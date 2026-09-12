from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np
import time
from app.simulation.stochastic_model import StochasticFactors
from app.simulation.race_simulator import RaceSimulator, DriverSimInput

@dataclass
class MonteCarloResult:
    n_simulations: int
    runtime_seconds: float
    seed: int
    driver_ids: List[str]
    win_probabilities: np.ndarray
    podium_probabilities: np.ndarray
    top5_probabilities: np.ndarray
    top10_probabilities: np.ndarray
    points_probabilities: np.ndarray
    dnf_probabilities: np.ndarray
    expected_positions: np.ndarray
    expected_points: np.ndarray
    median_positions: np.ndarray
    p10_positions: np.ndarray
    p25_positions: np.ndarray
    p75_positions: np.ndarray
    p90_positions: np.ndarray
    position_distributions: np.ndarray

class MonteCarloEngine:
    """High-performance Monte Carlo simulation engine."""

    def __init__(self, race_simulator: RaceSimulator):
        self.simulator = race_simulator

    def run(
        self,
        driver_inputs: List[DriverSimInput],
        race_laps: int = 58,
        is_wet: bool = False,
        circuit_deg_index: float = 0.5,
        n_simulations: int = 10000,
        seed: int = 42,
        safety_car_prob: float = 0.50,
    ) -> MonteCarloResult:
        start_time = time.perf_counter()
        rng = np.random.default_rng(seed)

        stochastic = StochasticFactors.sample(
            n_sims=n_simulations,
            n_drivers=len(driver_inputs),
            race_laps=race_laps,
            safety_car_prob=safety_car_prob,
            rng=rng
        )

        positions, points, dnfs = self.simulator.simulate(
            driver_inputs=driver_inputs,
            stochastic=stochastic,
            race_laps=race_laps,
            is_wet=is_wet,
            circuit_deg_index=circuit_deg_index,
            rng=rng
        )

        runtime = time.perf_counter() - start_time
        n_drivers = len(driver_inputs)

        win_p = np.mean(positions == 1, axis=0)
        podium_p = np.mean(positions <= 3, axis=0)
        top5_p = np.mean(positions <= 5, axis=0)
        top10_p = np.mean(positions <= 10, axis=0)
        points_p = np.mean((positions <= 10) & (~dnfs), axis=0)
        dnf_p = np.mean(dnfs, axis=0)

        exp_pos = np.mean(positions, axis=0)
        exp_pts = np.mean(points, axis=0)

        med_pos = np.median(positions, axis=0)
        p10 = np.percentile(positions, 10, axis=0)
        p25 = np.percentile(positions, 25, axis=0)
        p75 = np.percentile(positions, 75, axis=0)
        p90 = np.percentile(positions, 90, axis=0)

        pos_dist = np.zeros((n_drivers, 20))
        for d in range(n_drivers):
            for pos in range(1, 21):
                pos_dist[d, pos - 1] = np.mean(positions[:, d] == pos)

        return MonteCarloResult(
            n_simulations=n_simulations,
            runtime_seconds=runtime,
            seed=seed,
            driver_ids=[d.driver_id for d in driver_inputs],
            win_probabilities=win_p,
            podium_probabilities=podium_p,
            top5_probabilities=top5_p,
            top10_probabilities=top10_p,
            points_probabilities=points_p,
            dnf_probabilities=dnf_p,
            expected_positions=exp_pos,
            expected_points=exp_pts,
            median_positions=med_pos,
            p10_positions=p10,
            p25_positions=p25,
            p75_positions=p75,
            p90_positions=p90,
            position_distributions=pos_dist
        )
