from dataclasses import dataclass
from typing import List
import numpy as np
from app.ml.tyre_model import TyreModel

@dataclass
class PitStrategy:
    stops: int
    compounds: List[str]
    pit_laps: List[int]
    expected_total_time: float
    probability: float

class StrategyEngine:
    """Evaluates and samples pit strategies for Monte Carlo simulations."""

    def __init__(self, tyre_model: TyreModel):
        self.tyre_model = tyre_model

    def generate_candidate_strategies(
        self, race_laps: int, circuit_deg_index: float = 0.5, is_wet: bool = False
    ) -> List[PitStrategy]:
        if is_wet:
            return [
                PitStrategy(stops=1, compounds=["INTER", "INTER"], pit_laps=[int(race_laps * 0.5)], expected_total_time=0.0, probability=0.7),
                PitStrategy(stops=2, compounds=["INTER", "INTER", "WET"], pit_laps=[int(race_laps * 0.35), int(race_laps * 0.7)], expected_total_time=5.0, probability=0.3)
            ]

        # Shift the prior toward extra stops at high-degradation circuits.  The
        # simulator still samples alternatives, retaining strategic uncertainty.
        two_stop_probability = float(np.clip(0.18 + 0.44 * circuit_deg_index, 0.20, 0.65))
        one_stop_probability = 1.0 - two_stop_probability

        # 1-stop M-H
        s1 = PitStrategy(
            stops=1,
            compounds=["MEDIUM", "HARD"],
            pit_laps=[int(race_laps * 0.4)],
            expected_total_time=0.0,
            probability=one_stop_probability
        )
        # 2-stop S-M-H
        s2 = PitStrategy(
            stops=2,
            compounds=["SOFT", "MEDIUM", "HARD"],
            pit_laps=[int(race_laps * 0.25), int(race_laps * 0.6)],
            expected_total_time=3.0,
            probability=two_stop_probability
        )
        return [s1, s2]

    def sample_strategies(
        self, n_sims: int, n_drivers: int, strategies: List[PitStrategy], rng: np.random.Generator
    ) -> np.ndarray:
        probs = np.array([s.probability for s in strategies])
        probs = probs / np.sum(probs)
        return rng.choice(len(strategies), size=(n_sims, n_drivers), p=probs)
