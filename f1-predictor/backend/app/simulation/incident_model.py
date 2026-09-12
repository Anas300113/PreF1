import numpy as np
from typing import Tuple

class IncidentModel:
    """Simulates DNFs and safety car occurrences across simulations."""

    def sample_dnf_laps(
        self,
        n_sims: int,
        dnf_probabilities: np.ndarray,
        race_laps: int,
        rng: np.random.Generator
    ) -> Tuple[np.ndarray, np.ndarray]:
        n_drivers = len(dnf_probabilities)
        rand = rng.random(size=(n_sims, n_drivers))
        dnf_mask = rand < dnf_probabilities

        dnf_laps = np.full((n_sims, n_drivers), -1, dtype=int)
        if np.any(dnf_mask):
            sampled_laps = rng.integers(1, race_laps + 1, size=(n_sims, n_drivers))
            dnf_laps[dnf_mask] = sampled_laps[dnf_mask]

        return dnf_mask, dnf_laps
