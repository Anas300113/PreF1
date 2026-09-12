"""Season-long championship Monte Carlo simulation.

Runs probabilistic simulations for each remaining race in the season,
accumulates points, and produces championship-position probability
distributions for drivers and constructors.

Research references: XVX-016/F1-PREDICT, MRuhan17/f1-predictor,
siddhaarth555/ALL-SEASONS-GP-PREDICTOR.
"""

from dataclasses import dataclass
from typing import List
import numpy as np
from app.simulation.monte_carlo import MonteCarloEngine
from app.simulation.race_simulator import RaceSimulator, DriverSimInput
from app.simulation.strategy_engine import StrategyEngine
from app.ml.tyre_model import TyreModel

F1_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] + [0] * 10


@dataclass
class ChampionshipDriver:
    driver_id: str
    code: str
    full_name: str
    team_id: str
    team_name: str
    current_points: float = 0.0


@dataclass
class ChampionshipRace:
    race_id: str
    name: str
    round_number: int
    total_laps: int = 58
    is_sprint_weekend: bool = False
    circuit_deg_index: float = 0.5
    safety_car_prob: float = 0.50


@dataclass
class ChampionshipResult:
    n_simulations: int
    season: int
    races_remaining: int
    driver_ids: List[str]
    driver_codes: List[str]
    team_ids: List[str]
    championship_position_probabilities: np.ndarray
    championship_win_probabilities: np.ndarray
    expected_championship_points: np.ndarray
    expected_championship_position: np.ndarray
    constructor_win_probabilities: np.ndarray
    constructor_expected_points: np.ndarray
    convergence_report: dict


class ChampionshipSimulator:
    """Simulates the remainder of a championship season."""

    def __init__(self, race_simulator: RaceSimulator):
        self.race_simulator = race_simulator
        self.mc_engine = MonteCarloEngine(race_simulator)

    def simulate(
        self,
        drivers: List[ChampionshipDriver],
        remaining_races: List[ChampionshipRace],
        n_simulations: int = 10000,
        seed: int = 42,
    ) -> ChampionshipResult:
        """Monte Carlo simulate the remaining season."""
        rng = np.random.default_rng(seed)
        n_drivers = len(drivers)

        cumulative_points = np.zeros((n_simulations, n_drivers), dtype=float)
        for d, driver in enumerate(drivers):
            cumulative_points[:, d] = driver.current_points

        for race in remaining_races:
            driver_inputs = self._build_race_inputs(drivers, race)
            if not driver_inputs:
                continue

            mc_result = self.mc_engine.run(
                driver_inputs=driver_inputs,
                race_laps=race.total_laps,
                circuit_deg_index=race.circuit_deg_index,
                n_simulations=n_simulations,
                seed=rng.integers(0, 2**31),
                safety_car_prob=race.safety_car_prob,
            )

            for d in range(n_drivers):
                for pos_idx, points in enumerate(F1_POINTS):
                    cumulative_points[:, d] += (
                        mc_result.position_distributions[d, pos_idx] * points
                    )

            if race.is_sprint_weekend:
                sprint_extra = [8.0, 1.0, 0.0]
                for d in range(n_drivers):
                    for pos_idx, extra in enumerate(sprint_extra):
                        cumulative_points[:, d] += (
                            mc_result.position_distributions[d, pos_idx] * extra
                        )

        rankings = np.zeros((n_simulations, n_drivers), dtype=int)
        for sim in range(n_simulations):
            order = np.argsort(-cumulative_points[sim])
            for rank, driver_idx in enumerate(order, 1):
                rankings[sim, driver_idx] = rank

        pos_probs = np.zeros((n_drivers, n_drivers))
        for d in range(n_drivers):
            for pos in range(1, n_drivers + 1):
                pos_probs[d, pos - 1] = np.mean(rankings[:, d] == pos)

        win_probs = np.mean(rankings == 1, axis=0)
        exp_points = np.mean(cumulative_points, axis=0)
        exp_position = np.mean(rankings, axis=0)

        team_ids = list({d.team_id for d in drivers})
        team_idx_map = {t: i for i, t in enumerate(team_ids)}
        n_teams = len(team_ids)
        team_points = np.zeros((n_simulations, n_teams))
        for d, driver in enumerate(drivers):
            ti = team_idx_map[driver.team_id]
            team_points[:, ti] += cumulative_points[:, d]

        team_rankings = np.zeros((n_simulations, n_teams), dtype=int)
        for sim in range(n_simulations):
            order = np.argsort(-team_points[sim])
            for rank, ti in enumerate(order, 1):
                team_rankings[sim, ti] = rank

        constructor_win_probs = np.mean(team_rankings == 1, axis=0)
        constructor_exp_points = np.mean(team_points, axis=0)

        convergence = {
            "n_simulations": n_simulations,
            "n_races": len(remaining_races),
            "n_drivers": n_drivers,
        }

        return ChampionshipResult(
            n_simulations=n_simulations,
            season=2025,
            races_remaining=len(remaining_races),
            driver_ids=[d.driver_id for d in drivers],
            driver_codes=[d.code for d in drivers],
            team_ids=[d.team_id for d in drivers],
            championship_position_probabilities=pos_probs,
            championship_win_probabilities=win_probs,
            expected_championship_points=exp_points,
            expected_championship_position=exp_position,
            constructor_win_probabilities=constructor_win_probs,
            constructor_expected_points=constructor_exp_points,
            convergence_report=convergence,
        )

    def _build_race_inputs(
        self, drivers: List[ChampionshipDriver], race: ChampionshipRace
    ) -> List[DriverSimInput]:
        tyre_m = TyreModel()
        strat_e = StrategyEngine(tyre_m)
        strategies = strat_e.generate_candidate_strategies(race.total_laps)

        inputs = []
        for d in drivers:
            inputs.append(
                DriverSimInput(
                    driver_id=d.driver_id,
                    team_id=d.team_id,
                    base_pace_delta=float(d.current_points) * 0.001,
                    dnf_probability=0.05,
                    qualifying_position=1,
                    qualifying_pace_delta=0.0,
                    wet_skill_delta=0.0,
                    strategies=strategies,
                )
            )
        return inputs


def format_championship_response(result: ChampionshipResult) -> dict:
    """Format ChampionshipResult as API response dict."""
    driver_standings = []
    n_drivers = len(result.driver_ids)
    for i in range(n_drivers):
        position_dist = {
            str(pos + 1): round(float(result.championship_position_probabilities[i, pos]), 4)
            for pos in range(n_drivers)
        }
        driver_standings.append({
            "driver_id": result.driver_ids[i],
            "code": result.driver_codes[i],
            "team_id": result.team_ids[i],
            "championship_win_probability": round(float(result.championship_win_probabilities[i]), 4),
            "expected_championship_points": round(float(result.expected_championship_points[i]), 1),
            "expected_championship_position": round(float(result.expected_championship_position[i]), 2),
            "position_distribution": position_dist,
        })

    unique_teams = list(dict.fromkeys(result.team_ids))
    constructor_idx_map = {tid: i for i, tid in enumerate(unique_teams)}
    constructor_standings = []
    for tid in unique_teams:
        ci = constructor_idx_map[tid]
        constructor_standings.append({
            "team_id": tid,
            "championship_win_probability": round(float(result.constructor_win_probabilities[ci]), 4),
            "expected_championship_points": round(float(result.constructor_expected_points[ci]), 1),
        })

    return {
        "season": result.season,
        "races_remaining": result.races_remaining,
        "n_simulations": result.n_simulations,
        "driver_standings": driver_standings,
        "constructor_standings": constructor_standings,
        "convergence_report": result.convergence_report,
    }
