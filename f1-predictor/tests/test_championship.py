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


def _make_races(n: int = 3) -> list:
    return [
        ChampionshipRace(
            race_id=f"2025_{i}",
            name=f"Race {i}",
            round_number=i,
            total_laps=58,
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
