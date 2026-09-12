#!/usr/bin/env python3
"""Benchmark the vectorised Monte Carlo engine at production-scale runs.

Reports wall-clock runtime and throughput for 10k / 50k / 100k / 500k
simulations over a realistic 20-driver field (spec §41).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.simulation.monte_carlo import MonteCarloEngine
from app.simulation.race_simulator import DriverSimInput, RaceSimulator
from app.simulation.strategy_engine import StrategyEngine
from app.ml.tyre_model import TyreModel


def make_inputs(n_drivers: int, n_strategies: int = 3) -> list[DriverSimInput]:
    tyre = TyreModel()
    engine = StrategyEngine(tyre)
    inputs = []
    for i in range(n_drivers):
        inputs.append(
            DriverSimInput(
                driver_id=f"driver_{i}",
                team_id=f"team_{i % 10}",
                base_pace_delta=-2.0 + 0.25 * i,  # spread of pace across field
                dnf_probability=0.05 + 0.002 * i,
                qualifying_position=i + 1,
                qualifying_pace_delta=0.05 * i,
                wet_skill_delta=-0.1 if i < 5 else 0.0,
                strategies=engine.generate_candidate_strategies(58, 0.5, False)[:n_strategies],
            )
        )
    return inputs


def main() -> None:
    print("PreF1 Monte Carlo performance benchmark (20 drivers, 58 laps)\n")
    engine = MonteCarloEngine(RaceSimulator(StrategyEngine(TyreModel())))
    inputs = make_inputs(20)

    results = []
    for n in (10_000, 50_000, 100_000, 500_000):
        t0 = time.perf_counter()
        res = engine.run(inputs, race_laps=58, is_wet=False, circuit_deg_index=0.5,
                         n_simulations=n, seed=42)
        dt = time.perf_counter() - t0
        results.append((n, dt))
        print(f"  {n:>8,} sims : {dt:8.2f}s  ({n / dt:>10,.0f} sims/s)")

    print("\nMonte Carlo benchmark complete.")


if __name__ == "__main__":
    main()