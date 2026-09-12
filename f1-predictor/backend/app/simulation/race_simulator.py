from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from app.simulation.stochastic_model import StochasticFactors
from app.simulation.incident_model import IncidentModel
from app.simulation.strategy_engine import StrategyEngine, PitStrategy

@dataclass
class DriverSimInput:
    driver_id: str
    team_id: str
    base_pace_delta: float
    dnf_probability: float
    qualifying_position: int
    qualifying_pace_delta: float
    wet_skill_delta: float
    strategies: List[PitStrategy]

class RaceSimulator:
    POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] + [0] * 10

    def __init__(self, strategy_engine: StrategyEngine, pit_loss_seconds: float = 22.0):
        self.strategy_engine = strategy_engine
        self.incident_model = IncidentModel()
        self.pit_loss_seconds = pit_loss_seconds

    def simulate(
        self,
        driver_inputs: List[DriverSimInput],
        stochastic: StochasticFactors,
        race_laps: int = 58,
        is_wet: bool = False,
        circuit_deg_index: float = 0.5,
        rng: np.random.Generator = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Vectorised simulation over N simulations and D drivers.
        Returns: (positions, points, dnfs) of shape (N, D)
        """
        rng = rng or np.random.default_rng()
        n_sims = stochastic.n_sims
        n_drivers = len(driver_inputs)

        base_paces = np.array([d.base_pace_delta for d in driver_inputs])
        grid_positions = np.array([d.qualifying_position for d in driver_inputs])
        dnf_probs = np.array([d.dnf_probability for d in driver_inputs])

        if not driver_inputs:
            raise ValueError("At least one driver is required to simulate a race")

        # The grid affects the opening phase and the amount of traffic a car must
        # negotiate.  It is deliberately a small time effect rather than a direct
        # position adjustment: final classification is always derived from race time.
        grid_noise = rng.normal(0.0, 0.05, size=(n_sims, n_drivers))
        effective_grid_time = (grid_positions - 1) * 0.1 + grid_noise

        # Base race time over laps (N, D)
        laps_factor = float(race_laps)
        race_times = np.tile(base_paces * laps_factor, (n_sims, 1)) + effective_grid_time

        # Correlated randomness is sampled once per race.  The weather shock and
        # track evolution are shared by the field; individual pace noise remains
        # independent, preventing implausible all-driver-independent races.
        # σ = 0.15 * laps * 0.5 ≈ 4.4 s over a race (≈0.075 s/lap of
        # driver-specific form variance) — enough for strategy and incidents to
        # genuinely reorder the field.
        race_times += stochastic.driver_pace_noise * laps_factor * 0.5
        wet_skill = np.array([d.wet_skill_delta for d in driver_inputs])
        if is_wet:
            race_times += wet_skill[None, :] * laps_factor
            race_times += stochastic.global_weather_shock[:, None] * wet_skill[None, :] * 0.35

        # Sample a strategy for every car and simulation, then add the cumulative
        # compound/degradation cost and pit-lane loss.  This is aggregated by stint
        # (rather than a Python loop over every lap) and is therefore suitable for
        # 10k+ simulation runs.
        for driver_index, driver in enumerate(driver_inputs):
            strategies = driver.strategies
            if not strategies:
                raise ValueError(f"Driver {driver.driver_id} has no candidate strategies")
            selected = self.strategy_engine.sample_strategies(
                n_sims, 1, strategies, rng
            ).reshape(-1)
            strategy_times = np.zeros(n_sims, dtype=float)
            for strategy_index, strategy in enumerate(strategies):
                mask = selected == strategy_index
                if not np.any(mask):
                    continue
                tyre_time = self._strategy_tyre_time(
                    strategy, race_laps, circuit_deg_index
                )
                # A safety car reduces pit loss only for stops occurring in its
                # deployment window.  This is a common shock shared by all cars.
                pit_loss = self._pit_loss_for_strategy(strategy, stochastic, mask)
                strategy_times[mask] = tyre_time + pit_loss
            race_times[:, driver_index] += strategy_times

        # Track evolution is common but different drivers realise it differently
        # through their selected stint plans; retain a modest residual here.
        race_times -= stochastic.track_evolution_rate[:, None] * laps_factor * 0.15

        # Incident DNF check
        dnf_mask, dnf_laps = self.incident_model.sample_dnf_laps(n_sims, dnf_probs, race_laps, rng)
        
        # Finishers are always classified ahead of DNFs.  Among DNFs, a later
        # retirement is classified ahead of an earlier retirement, matching the
        # distance-based convention more closely than assigning all DNFs arbitrary
        # last-place times.
        race_times[dnf_mask] = 1e6 - dnf_laps[dnf_mask] + rng.uniform(
            0.0, 0.01, size=int(dnf_mask.sum())
        )

        # Ranking per simulation
        order = np.argsort(race_times, axis=1)
        positions = np.argsort(order, axis=1) + 1
        points_table = np.asarray(self.POINTS, dtype=float)
        points = points_table[np.minimum(positions, len(points_table)) - 1]
        points[(positions > 10) | dnf_mask] = 0.0

        return positions, points, dnf_mask

    def _strategy_tyre_time(
        self,
        strategy: PitStrategy,
        race_laps: int,
        circuit_deg_index: float,
    ) -> float:
        """Return cumulative tyre delta over a complete candidate strategy."""
        boundaries = [0, *strategy.pit_laps, race_laps]
        total = 0.0
        for stint_index, compound in enumerate(strategy.compounds):
            if stint_index + 1 >= len(boundaries):
                break
            stint_laps = max(0, boundaries[stint_index + 1] - boundaries[stint_index])
            if stint_laps == 0:
                continue
            # Sum base pace + linear age degradation for ages 0..n-1.
            base = self.strategy_engine.tyre_model.predict_lap_time_delta(
                compound, 0, circuit_deg_index
            )
            age_one = self.strategy_engine.tyre_model.predict_lap_time_delta(
                compound, 1, circuit_deg_index
            )
            slope = age_one - base
            total += stint_laps * base + slope * stint_laps * (stint_laps - 1) / 2
        return total + strategy.expected_total_time

    def _pit_loss_for_strategy(
        self,
        strategy: PitStrategy,
        stochastic: StochasticFactors,
        mask: np.ndarray,
    ) -> np.ndarray:
        """Calculate pit loss, discounting a stop made close to a safety car."""
        indices = np.flatnonzero(mask)
        losses = np.full(len(indices), strategy.stops * self.pit_loss_seconds, dtype=float)
        if strategy.stops == 0 or not len(indices):
            return losses
        sc_laps = stochastic.safety_car_lap[indices]
        sc_active = stochastic.safety_car_deployed[indices]
        for pit_lap in strategy.pit_laps:
            under_sc = sc_active & (np.abs(sc_laps - pit_lap) <= 3)
            losses[under_sc] -= self.pit_loss_seconds * 0.55
        return losses
