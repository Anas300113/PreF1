from dataclasses import dataclass
import numpy as np

@dataclass
class StochasticFactors:
    """Correlated global & per-driver shocks for Monte Carlo simulations.

    Safety-car events are sampled from a non-homogeneous Poisson process
    (NHPP): the per-lap hazard is elevated on lap 1 (first-lap incidents are
    ~4x more likely, calibrated from 2019-2024 race data — see
    AryunGupta/Monte-Carlo-F1-Simulation research) and otherwise flat at the
    circuit's historical SC rate.  Multiple events per race are possible.
    """
    n_sims: int
    global_weather_shock: np.ndarray
    track_evolution_rate: np.ndarray
    safety_car_deployed: np.ndarray       # any SC/VSC event occurred
    safety_car_lap: np.ndarray            # lap of first event (for pit discount)
    safety_car_events: np.ndarray         # total SC+VSC event count per sim
    red_flag_deployed: np.ndarray
    driver_pace_noise: np.ndarray

    LAP1_HAZARD_MULTIPLIER = 4.0
    VSC_SHARE = 0.35  # fraction of caution events that are VSC (weaker)

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

        # --- NHPP safety-car sampling -------------------------------------
        # safety_car_prob is the historical probability of >= 1 caution at this
        # circuit.  Convert to a per-lap hazard rate: P(0 events) = exp(-Λ).
        clamped_prob = float(np.clip(safety_car_prob, 0.01, 0.99))
        total_intensity = -np.log(1.0 - clamped_prob)
        per_lap_hazard = total_intensity / max(1, race_laps)
        hazard = np.full(race_laps, per_lap_hazard)
        hazard[0] *= cls.LAP1_HAZARD_MULTIPLIER
        cumulative = np.cumsum(hazard)

        # For each sim, draw event count from Poisson(total intensity) and
        # place events via inverse-CDF over the cumulative hazard.
        n_events = rng.poisson(total_intensity, size=n_sims)
        max_events = int(n_events.max()) if n_events.size else 0
        safety_car_events = np.zeros(n_sims, dtype=int)
        safety_car_deployed = np.zeros(n_sims, dtype=bool)
        first_lap = np.full(n_sims, race_laps, dtype=int)
        if max_events > 0:
            u = rng.random(size=(n_sims, max_events)) * cumulative[-1]
            event_laps = np.searchsorted(cumulative, u, side="right") + 1
            valid = np.arange(max_events)[None, :] < n_events[:, None]
            counts = valid.sum(axis=1)
            safety_car_events = counts.astype(int)
            safety_car_deployed = counts > 0
            any_valid = valid.any(axis=1)
            first_lap = np.where(
                any_valid, event_laps[np.arange(n_sims), np.argmax(valid, axis=1)], race_laps
            )

        rf_deployed = rng.random(size=n_sims) < red_flag_prob

        # Per-driver pace noise (N, D)
        pace_noise = rng.normal(0.0, 0.15, size=(n_sims, n_drivers))

        return cls(
            n_sims=n_sims,
            global_weather_shock=weather_shock,
            track_evolution_rate=track_evo,
            safety_car_deployed=safety_car_deployed,
            safety_car_lap=first_lap,
            safety_car_events=safety_car_events,
            red_flag_deployed=rf_deployed,
            driver_pace_noise=pace_noise,
        )
