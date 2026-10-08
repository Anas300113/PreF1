"""Season-long championship Monte Carlo simulation.

Runs probabilistic simulations for each remaining race in the season,
accumulates **sampled** per-race points (not expected values), and produces
championship-position probability distributions for drivers and constructors.

Critical design: every simulation row i represents one coherent imagined
season.  Race k contributes the *sampled* points that driver d scored in
simulation row i, preserving within-race driver correlations and producing a
genuinely non-zero championship points variance.

Research references: XVX-016/F1-PREDICT, MRuhan17/f1-predictor,
siddhaarth555/ALL-SEASONS-GP-PREDICTOR.
"""

from dataclasses import dataclass, field
from typing import List
import numpy as np
from app.simulation.monte_carlo import MonteCarloEngine
from app.simulation.race_simulator import RaceSimulator, DriverSimInput
from app.simulation.strategy_engine import StrategyEngine
from app.ml.tyre_model import TyreModel

F1_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] + [0] * 10

# Season-aware sprint scoring (FIA Sporting Regulations).
# 2021: 3-2-1; 2022 onward: 8-7-6-5-4-3-2-1.
SPRINT_POINTS_2021 = [3.0, 2.0, 1.0] + [0.0] * 17
SPRINT_POINTS_MODERN = [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0] + [0.0] * 12


def sprint_points_table(season: int) -> np.ndarray:
    """Return the sprint scoring table for a given season (0 if no sprints)."""
    if season >= 2022:
        return np.asarray(SPRINT_POINTS_MODERN, dtype=float)
    if season == 2021:
        return np.asarray(SPRINT_POINTS_2021, dtype=float)
    return np.zeros(20, dtype=float)


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
    # Per-driver standard deviation of final championship points across
    # simulations — must be > 0 whenever races remain (regression guard
    # against expected-value collapse).
    championship_points_std: np.ndarray = field(default_factory=lambda: np.zeros(0))


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
        season: int = 2025,
    ) -> ChampionshipResult:
        """Monte Carlo simulate the remaining season.

        Each simulation row is one imagined season: for every remaining race
        the *sampled* finishing positions (and therefore sampled points) are
        added to that row's running championship total.  Expected-value
        collapsing is explicitly forbidden — it produces zero-variance
        championships that misrepresent uncertainty.
        """
        rng = np.random.default_rng(seed)
        n_drivers = len(drivers)

        cumulative_points = np.zeros((n_simulations, n_drivers), dtype=float)
        for d, driver in enumerate(drivers):
            cumulative_points[:, d] = driver.current_points

        for race in remaining_races:
            driver_inputs = self._build_race_inputs(drivers, race)
            if not driver_inputs:
                continue

            # --- Grand Prix: sampled race outcomes -----------------------
            gp_result = self.mc_engine.run(
                driver_inputs=driver_inputs,
                race_laps=race.total_laps,
                circuit_deg_index=race.circuit_deg_index,
                n_simulations=n_simulations,
                seed=int(rng.integers(0, 2**31)),
                safety_car_prob=race.safety_car_prob,
                retain_samples=True,
            )
            if gp_result.sampled_points is None:  # pragma: no cover - safety guard
                raise RuntimeError(
                    "Championship simulation requires sampled race outcomes; "
                    "MonteCarloEngine returned no sampled_points."
                )
            # Row-aligned accumulation preserves within-race correlations:
            # row i of gp_result corresponds to row i of cumulative_points.
            cumulative_points += gp_result.sampled_points.astype(float)

            # --- Sprint: independent sampled sprint outcomes -------------
            if race.is_sprint_weekend and season >= 2021:
                sprint_table = sprint_points_table(season)
                sprint_result = self.mc_engine.run(
                    driver_inputs=driver_inputs,
                    race_laps=max(10, race.total_laps // 3),
                    circuit_deg_index=race.circuit_deg_index,
                    n_simulations=n_simulations,
                    seed=int(rng.integers(0, 2**31)),
                    safety_car_prob=race.safety_car_prob,
                    points_table=sprint_table,
                    retain_samples=True,
                )
                if sprint_result.sampled_points is None:  # pragma: no cover
                    raise RuntimeError("Sprint simulation returned no sampled points.")
                cumulative_points += sprint_result.sampled_points.astype(float)

        rankings = np.zeros((n_simulations, n_drivers), dtype=int)
        for sim in range(n_simulations):
            # Stable tie-break on current points so equal-point seasons are
            # resolved deterministically rather than arbitrarily.
            order = np.lexsort((np.arange(n_drivers), -cumulative_points[sim]))
            for rank, driver_idx in enumerate(order, 1):
                rankings[sim, driver_idx] = rank

        pos_probs = np.zeros((n_drivers, n_drivers))
        for d in range(n_drivers):
            for pos in range(1, n_drivers + 1):
                pos_probs[d, pos - 1] = np.mean(rankings[:, d] == pos)

        win_probs = np.mean(rankings == 1, axis=0)
        exp_points = np.mean(cumulative_points, axis=0)
        exp_position = np.mean(rankings, axis=0)
        points_std = np.std(cumulative_points, axis=0)

        # dict.fromkeys preserves first-appearance order (set iteration order
        # for strings is hash-randomised across processes).
        team_ids = list(dict.fromkeys(d.team_id for d in drivers))
        team_idx_map = {t: i for i, t in enumerate(team_ids)}
        n_teams = len(team_ids)
        team_points = np.zeros((n_simulations, n_teams))
        for d, driver in enumerate(drivers):
            ti = team_idx_map[driver.team_id]
            team_points[:, ti] += cumulative_points[:, d]

        team_rankings = np.zeros((n_simulations, n_teams), dtype=int)
        for sim in range(n_simulations):
            order = np.lexsort((np.arange(n_teams), -team_points[sim]))
            for rank, ti in enumerate(order, 1):
                team_rankings[sim, ti] = rank

        constructor_win_probs = np.mean(team_rankings == 1, axis=0)
        constructor_exp_points = np.mean(team_points, axis=0)

        convergence = {
            "n_simulations": n_simulations,
            "n_races": len(remaining_races),
            "n_drivers": n_drivers,
            "sampled_outcomes": True,
            "min_championship_points_std": float(np.min(points_std)) if n_drivers else 0.0,
            "max_championship_points_std": float(np.max(points_std)) if n_drivers else 0.0,
        }

        return ChampionshipResult(
            n_simulations=n_simulations,
            season=season,
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
            championship_points_std=points_std,
        )

    def _build_race_inputs(
        self, drivers: List[ChampionshipDriver], race: ChampionshipRace
    ) -> List[DriverSimInput]:
        tyre_m = TyreModel()
        strat_e = StrategyEngine(tyre_m)
        strategies = strat_e.generate_candidate_strategies(race.total_laps)

        # Championship prior: a driver's points are evidence of underlying
        # pace.  Express this as a *relative* per-lap time delta centred on
        # the field mean so the leader is faster (negative delta), not slower.
        # Scale: the full points spread maps to ~±0.25 s/lap, which is a
        # deliberately weak prior — recent form should dominate once the
        # season's own data is available elsewhere.
        points = np.array([d.current_points for d in drivers], dtype=float)
        mean_points = float(np.mean(points)) if len(points) else 0.0
        spread = float(np.max(points) - np.min(points)) if len(points) else 0.0
        scale = 0.25 / spread if spread > 0 else 0.0

        # Grid: order by current championship points (best first).  This is a
        # prior for circuits where no qualifying data exists.
        grid_order = np.argsort([-d.current_points for d in drivers], kind="stable")
        grid_position = np.empty(len(drivers), dtype=int)
        for rank, idx in enumerate(grid_order, start=1):
            grid_position[idx] = rank

        inputs = []
        for i, d in enumerate(drivers):
            inputs.append(
                DriverSimInput(
                    driver_id=d.driver_id,
                    team_id=d.team_id,
                    base_pace_delta=(mean_points - d.current_points) * scale,
                    dnf_probability=0.05,
                    qualifying_position=int(grid_position[i]),
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
            "championship_points_std": round(float(result.championship_points_std[i]), 1)
            if result.championship_points_std.size else 0.0,
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
