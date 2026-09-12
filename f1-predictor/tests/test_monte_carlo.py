import numpy as np
import pytest

from app.simulation.monte_carlo import MonteCarloEngine
from app.simulation.race_simulator import DriverSimInput, RaceSimulator
from app.simulation.strategy_engine import StrategyEngine
from app.ml.tyre_model import TyreModel


def _make_inputs(n: int = 5) -> list[DriverSimInput]:
    tyre_m = TyreModel()
    strat_e = StrategyEngine(tyre_m)
    inputs = []
    for i in range(n):
        strats = strat_e.generate_candidate_strategies(58)
        inputs.append(
            DriverSimInput(
                driver_id=f"driver_{i}",
                team_id=f"team_{i}",
                base_pace_delta=float(i) * 0.1,
                dnf_probability=0.05,
                qualifying_position=i + 1,
                qualifying_pace_delta=float(i) * 0.05,
                wet_skill_delta=0.0,
                strategies=strats,
            )
        )
    return inputs


def test_monte_carlo_probability_sums():
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(5)
    result = mc.run(inputs, n_simulations=2000, seed=42)

    for d in range(5):
        dist_sum = result.position_distributions[d].sum()
        assert 0.99 <= dist_sum <= 1.01, f"Position distribution must sum to ~1, got {dist_sum}"


def test_monte_carlo_win_probabilities_valid():
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(8)
    result = mc.run(inputs, n_simulations=500, seed=7)

    assert result.expected_positions.shape == (8,)
    assert np.all(result.win_probabilities >= 0)
    assert np.all(result.win_probabilities <= 1)
    assert abs(result.win_probabilities.sum() - 1.0) < 0.05


def test_monte_carlo_reproducible_with_seed():
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(6)
    r1 = mc.run(inputs, n_simulations=1000, seed=99)
    r2 = mc.run(inputs, n_simulations=1000, seed=99)
    np.testing.assert_array_almost_equal(r1.win_probabilities, r2.win_probabilities)


def test_each_simulation_has_a_unique_complete_classification():
    """A race classification must be a permutation even when drivers retire."""
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(10)
    result = mc.run(inputs, n_simulations=500, seed=123)

    # Recover sampled classifications from the distribution invariant indirectly:
    # every driver's marginal distribution must include every simulated outcome.
    # RaceSimulator itself is vectorised, so its output is additionally checked
    # below with an intentionally high DNF scenario.
    from app.simulation.stochastic_model import StochasticFactors

    rng = np.random.default_rng(123)
    stochastic = StochasticFactors.sample(200, len(inputs), race_laps=58, rng=rng)
    positions, _, _ = mc.simulator.simulate(inputs, stochastic, rng=rng)
    expected = np.arange(1, len(inputs) + 1)
    assert all(np.array_equal(np.sort(row), expected) for row in positions)
    assert result.position_distributions.shape == (10, 20)


def test_pairwise_finish_matrix_properties():
    """D×D pairwise finishing matrix must satisfy reflexive, anti-symmetric, and
    probabilistic bounds (research §30: pairwise driver comparison models)."""
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(6)
    result = mc.run(inputs, n_simulations=1000, seed=42)

    pairwise = result.pairwise_finish_matrix
    n = len(inputs)
    assert pairwise.shape == (n, n)

    for i in range(n):
        # Reflexive: P(driver_i beats driver_i) = 0.5
        assert abs(pairwise[i][i] - 0.5) < 1e-10
        for j in range(n):
            # Probabilistic bounds
            assert 0.0 <= pairwise[i][j] <= 1.0
            if i != j:
                # Anti-symmetric: P(A beats B) + P(B beats A) = 1
                assert abs(pairwise[i][j] + pairwise[j][i] - 1.0) < 1e-10


def test_pairwise_matrix_consistent_with_win_probability():
    """A dominant driver's pairwise P(beat others) should correlate with win probability."""
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(5)
    # Make driver_0 dominant (much lower pace delta)
    inputs[0].base_pace_delta = 0.0
    inputs[1].base_pace_delta = 1.5
    result = mc.run(inputs, n_simulations=2000, seed=42)

    # Driver 0 should have highest pairwise win average
    avg_pairwise = result.pairwise_finish_matrix[0].mean()
    for i in range(1, 5):
        assert avg_pairwise > result.pairwise_finish_matrix[i].mean(), (
            f"Driver 0 pairwise mean {avg_pairwise:.3f} should exceed driver {i}'s "
            f"{result.pairwise_finish_matrix[i].mean():.3f}"
        )


def test_convergence_report_structure():
    """Convergence report must include required fields and be consistent."""
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(5)
    result = mc.run(inputs, n_simulations=2000, seed=42)

    report = result.convergence_report
    assert "win_probability_max_delta" in report
    assert "win_probability_mean_delta" in report
    assert "n_simulations" in report
    assert "converged" in report
    assert report["n_simulations"] == 2000
    assert 0.0 <= report["win_probability_max_delta"] <= 1.0
    assert 0.0 <= report["win_probability_mean_delta"] <= 1.0


def test_convergence_improves_with_more_simulations():
    """Higher simulation count should reduce max delta (all else equal)."""
    mc = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = _make_inputs(5)

    r1 = mc.run(inputs, n_simulations=500, seed=42)
    r2 = mc.run(inputs, n_simulations=5000, seed=42)

    assert r2.convergence_report["win_probability_max_delta"] <= (
        r1.convergence_report["win_probability_max_delta"] + 0.02  # tolerance
    )


def test_regulation_era_features():
    """Regulation-era indicator features must correctly classify F1 eras."""
    from app.features.driver_features import DriverFeatureExtractor

    era = DriverFeatureExtractor._regulation_era_features("2024_10")
    assert era["regulation_era_2022_plus"] == 1.0
    assert era["regulation_era_2017_plus"] == 1.0
    assert era["season_year"] == 2024.0

    era_old = DriverFeatureExtractor._regulation_era_features("2019_1")
    assert era_old["regulation_era_2022_plus"] == 0.0
    assert era_old["regulation_era_2017_plus"] == 1.0
    assert era_old["season_year"] == 2019.0


def test_recency_weighted_feature():
    """Recency-weighted average must weight recent races more than old ones."""
    from app.features.driver_features import DriverFeatureExtractor

    extractor = DriverFeatureExtractor.__new__(DriverFeatureExtractor)
    # Simulate finishes: [1st, 10th] — recent good, old bad
    weighted = extractor.recency_weighted([1.0, 10.0], half_life=5)
    simple_avg = (1.0 + 10.0) / 2
    # Recency weighting should be closer to 1.0 (recent good result)
    assert weighted < simple_avg
    assert 1.0 <= weighted <= 10.0
