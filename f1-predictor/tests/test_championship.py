"""Championship + Monte Carlo P0 regression tests.

Includes guards for the P0.1 defect: the championship simulator must
propagate SAMPLED race outcomes (non-zero variance), not expected values.
"""
import numpy as np
import pytest
from app.simulation.race_simulator import RaceSimulator
from app.simulation.strategy_engine import StrategyEngine
from app.ml.tyre_model import TyreModel
from app.simulation.championship_simulator import (
    ChampionshipDriver,
    ChampionshipRace,
    ChampionshipSimulator,
    format_championship_response,
    sprint_points_table,
)


def _make_drivers(n: int = 4) -> list:
    return [
        ChampionshipDriver(
            driver_id=f"driver_{i}",
            code=f"D{i}",
            full_name=f"Driver {i}",
            team_id=f"team_{i // 2}",
            team_name=f"Team {i // 2}",
            current_points=float(i * 10),
        )
        for i in range(n)
    ]


def _make_races(n: int = 3, sprint: bool = False) -> list:
    return [
        ChampionshipRace(
            race_id=f"2025_{i}",
            name=f"Race {i}",
            round_number=i,
            total_laps=58,
            is_sprint_weekend=sprint,
        )
        for i in range(n)
    ]


def test_championship_runs():
    """Championship simulation must run without error."""
    tyre_m = TyreModel()
    sim = RaceSimulator(StrategyEngine(tyre_m))
    champ_sim = ChampionshipSimulator(sim)

    drivers = _make_drivers(4)
    races = _make_races(2)
    result = champ_sim.simulate(drivers, races, n_simulations=500, seed=42)

    assert result.n_simulations == 500
    assert result.races_remaining == 2
    assert len(result.driver_ids) == 4


def test_championship_win_probabilities_sum_to_one():
    """Exactly one driver must win the championship in each simulation."""
    tyre_m = TyreModel()
    sim = RaceSimulator(StrategyEngine(tyre_m))
    champ_sim = ChampionshipSimulator(sim)

    drivers = _make_drivers(4)
    races = _make_races(2)
    result = champ_sim.simulate(drivers, races, n_simulations=500, seed=42)

    assert abs(result.championship_win_probabilities.sum() - 1.0) < 0.05


def test_championship_position_probabilities_sum_to_one():
    """Each driver's championship position distribution must sum to ~1."""
    tyre_m = TyreModel()
    sim = RaceSimulator(StrategyEngine(tyre_m))
    champ_sim = ChampionshipSimulator(sim)

    drivers = _make_drivers(4)
    races = _make_races(2)
    result = champ_sim.simulate(drivers, races, n_simulations=500, seed=42)

    for d in range(4):
        assert abs(result.championship_position_probabilities[d].sum() - 1.0) < 0.05


def test_championship_leader_has_highest_win_probability():
    """The driver with the most current points should have the highest championship win probability."""
    tyre_m = TyreModel()
    sim = RaceSimulator(StrategyEngine(tyre_m))
    champ_sim = ChampionshipSimulator(sim)

    drivers = _make_drivers(4)
    # driver_3 has most current points (30)
    races = _make_races(2)
    result = champ_sim.simulate(drivers, races, n_simulations=500, seed=42)

    assert result.championship_win_probabilities[3] == max(result.championship_win_probabilities)


def test_championship_constructor_win_probabilities_sum_to_one():
    """Constructor championship win probabilities must sum to ~1."""
    tyre_m = TyreModel()
    sim = RaceSimulator(StrategyEngine(tyre_m))
    champ_sim = ChampionshipSimulator(sim)

    drivers = _make_drivers(4)  # 2 teams
    races = _make_races(2)
    result = champ_sim.simulate(drivers, races, n_simulations=500, seed=42)

    assert abs(result.constructor_win_probabilities.sum() - 1.0) < 0.05


def test_championship_response_format():
    """format_championship_response must produce valid structure."""
    tyre_m = TyreModel()
    sim = RaceSimulator(StrategyEngine(tyre_m))
    champ_sim = ChampionshipSimulator(sim)

    drivers = _make_drivers(4)
    races = _make_races(2)
    result = champ_sim.simulate(drivers, races, n_simulations=500, seed=42)
    response = format_championship_response(result)

    assert "driver_standings" in response
    assert "constructor_standings" in response
    assert "convergence_report" in response
    assert len(response["driver_standings"]) == 4
    assert len(response["constructor_standings"]) == 2
    for ds in response["driver_standings"]:
        assert "championship_win_probability" in ds
        assert "position_distribution" in ds
        assert "expected_championship_points" in ds


# ---------------------------------------------------------------------------
# P0.1 regression guards — sampled outcomes, not expected values
# ---------------------------------------------------------------------------
def _sim() -> ChampionshipSimulator:
    return ChampionshipSimulator(RaceSimulator(StrategyEngine(TyreModel())))


def test_championship_points_have_non_zero_variance():
    """Sampled outcomes must produce non-zero championship points variance.

    The old expected-value implementation gave every simulation row the
    identical increment, so std(points) was exactly 0 — proof that no race
    uncertainty was propagated.
    """
    result = _sim().simulate(_make_drivers(4), _make_races(2), n_simulations=2000, seed=42)

    assert result.championship_points_std.size == 4
    for i, std in enumerate(result.championship_points_std):
        assert std > 0.0, (
            f"driver_{i} championship points std is {std} — expected-value "
            "collapse detected (sampled outcomes not propagated)"
        )


def test_championship_win_probabilities_are_not_degenerate():
    """With 4 competitive drivers over 2 races, no driver should be certain."""
    result = _sim().simulate(_make_drivers(4), _make_races(2), n_simulations=2000, seed=42)
    # Old bug: the leader always won (p=1.0) because every row received
    # identical expected increments; sampled outcomes spread the mass.
    assert result.championship_win_probabilities.max() < 0.999


def test_convergence_report_declares_sampled_outcomes():
    result = _sim().simulate(_make_drivers(4), _make_races(1), n_simulations=500, seed=1)
    assert result.convergence_report["sampled_outcomes"] is True
    assert result.convergence_report["max_championship_points_std"] > 0.0


def test_more_races_increase_points_uncertainty():
    r1 = _sim().simulate(_make_drivers(4), _make_races(1), n_simulations=2000, seed=7)
    r3 = _sim().simulate(_make_drivers(4), _make_races(3), n_simulations=2000, seed=7)
    assert r3.championship_points_std.mean() > r1.championship_points_std.mean()


def test_monte_carlo_sampled_points_shape_and_consistency():
    from app.simulation.monte_carlo import MonteCarloEngine
    from app.simulation.race_simulator import DriverSimInput

    tyre = TyreModel()
    strat = StrategyEngine(tyre)
    engine = MonteCarloEngine(RaceSimulator(strat))
    inputs = [
        DriverSimInput(
            driver_id=f"d{i}", team_id=f"t{i // 2}", base_pace_delta=0.05 * i,
            dnf_probability=0.05, qualifying_position=i + 1, qualifying_pace_delta=0.1 * i,
            wet_skill_delta=0.0, strategies=strat.generate_candidate_strategies(58),
        )
        for i in range(5)
    ]
    r_no = engine.run(inputs, n_simulations=200, seed=3)
    assert r_no.sampled_points is None and r_no.sampled_positions is None

    r_yes = engine.run(inputs, n_simulations=200, seed=3, retain_samples=True)
    assert r_yes.sampled_points is not None
    assert r_yes.sampled_points.shape == (200, 5)
    assert r_yes.sampled_positions.shape == (200, 5)
    # Sample means must reproduce the reported expectations.
    np.testing.assert_allclose(
        r_yes.sampled_points.astype(float).mean(axis=0),
        r_yes.expected_points,
        atol=1e-4,
    )
    # Each row is a complete classification.
    for row in r_yes.sampled_positions:
        assert sorted(int(p) for p in row) == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# Sprint scoring — season-aware and sampled
# ---------------------------------------------------------------------------
def test_sprint_points_table_is_season_aware():
    modern = sprint_points_table(2025)
    assert modern[:8].tolist() == [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    assert modern[8] == 0.0

    y2021 = sprint_points_table(2021)
    assert y2021[:3].tolist() == [3.0, 2.0, 1.0]
    assert y2021[3] == 0.0

    assert sprint_points_table(2020).sum() == 0.0


def test_sprint_weekend_adds_expected_points():
    """A sprint weekend must yield strictly higher expected championship points."""
    drivers = _make_drivers(4)
    plain = _sim().simulate(drivers, _make_races(2, sprint=False), n_simulations=1500, seed=11)
    sprint = _sim().simulate(
        drivers, _make_races(2, sprint=True), n_simulations=1500, seed=11, season=2025
    )
    # Old bug: [8, 1, 0] expected-value hack.  Modern sprints award 36 points
    # across the field, so total expected points must rise (MC noise allowed).
    assert sprint.expected_championship_points.sum() > plain.expected_championship_points.sum() + 20.0


def test_championship_leader_is_not_paced_slower():
    """Old bug: base_pace_delta = +points*0.001 made the leader the slowest."""
    sim = _sim()
    drivers = _make_drivers(4)
    inputs = sim._build_race_inputs(drivers, _make_races(1)[0])
    by_id = {i.driver_id: i for i in inputs}
    deltas = [by_id[f"driver_{i}"].base_pace_delta for i in range(4)]
    assert deltas == sorted(deltas, reverse=True), (
        "points leader must be modelled as faster (lower race-time delta)"
    )
    # Grid prior: leader starts first.
    assert by_id["driver_3"].qualifying_position == 1
    assert by_id["driver_0"].qualifying_position == 4


def test_response_format_includes_points_std():
    result = _sim().simulate(_make_drivers(4), _make_races(1), n_simulations=500, seed=9)
    resp = format_championship_response(result)
    for ds in resp["driver_standings"]:
        assert "championship_points_std" in ds
        assert ds["championship_points_std"] >= 0.0


def test_season_is_threaded_through():
    result = _sim().simulate(
        _make_drivers(3), _make_races(1), n_simulations=200, seed=2, season=2026
    )
    assert result.season == 2026
