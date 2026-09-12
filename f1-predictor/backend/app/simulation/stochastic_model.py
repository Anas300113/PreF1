from dataclasses import dataclass
import numpy as np

@dataclass
class StochasticFactors:
    """Correlated global & per-driver shocks for Monte Carlo simulations."""
    n_sims: int
    global_weather_shock: np.ndarray
    track_evolution_rate: np.ndarray
    safety_car_deployed: np.ndarray
    safety_car_lap: np.ndarray
    red_flag_deployed: np.ndarray
    driver_pace_noise: np.ndarray

    @classmethod
    def sample(
        cls,
        n_sims: int,
        n_drivers: int,
        safety_car_prob: float = 0.50,
        red_flag_prob: float = 0.10,
        race_laps: int = 58,
        rng: np.random.Generator = None
    ) -> "StochasticFactors":
        rng = rng or np.random.default_rng()

        weather_shock = rng.normal(0.0, 0.5, size=n_sims)
        track_evo = rng.uniform(0.01, 0.04, size=n_sims)

        sc_deployed = rng.random(size=n_sims) < safety_car_prob
        sc_lap = rng.integers(5, max(6, race_laps - 10), size=n_sims)

        rf_deployed = rng.random(size=n_sims) < red_flag_prob

        # Per-driver pace noise (N, D)
        pace_noise = rng.normal(0.0, 0.15, size=(n_sims, n_drivers))

        return cls(
            n_sims=n_sims,
            global_weather_shock=weather_shock,
            track_evolution_rate=track_evo,
            safety_car_deployed=sc_deployed,
            safety_car_lap=sc_lap,
            red_flag_deployed=rf_deployed,
            driver_pace_noise=pace_noise,
        )
