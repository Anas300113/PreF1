#!/usr/bin/env python3
"""CLI script to run historical backtests against real ingested data.

Example:
    python scripts/run_backtest.py --season 2025
    python scripts/run_backtest.py --start 2023 --end 2025 --sims 5000
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.backtesting.backtest_runner import BacktestRunner
from app.utils.logging_config import setup_logging


def print_season_summary(record: dict) -> None:
    m = record
    print(f"\n=== Season {m['season']} ({m['n_races']} races, {m['n_simulations']} sims/race) ===")
    print(
        f"  Winner acc      : {m['winner_accuracy']:.1%}"
        f"   (model vs standings baseline below)"
    )
    print(f"  Podium acc (Jaccard/3): {m['podium_accuracy']:.1%}")
    print(f"  Top-5 acc       : {m['top5_accuracy']:.1%}")
    print(f"  MAE position    : {m['mean_abs_position_error']:.2f}")
    print(f"  RMSE position   : {m['rmse_position_error']:.2f}")
    print(f"  Brier (win)     : {m['brier_score_win']:.3f}")
    print(f"  Log loss (win)  : {m['log_loss_win']:.3f}")
    print(f"  Kendall tau     : {m['kendall_tau']:.3f}")
    print(f"  E[points] MAE   : {m['expected_points_error']:.2f}")

    for name, base in (m.get("baselines") or {}).items():
        comp = (m.get("comparison") or {}).get(name, {})
        print(
            f"  vs {name:<24}: winner {base.get('winner_accuracy', 0):.1%} "
            f"MAE {base.get('mae_position', 0):.2f} "
            f"| model delta winner {comp.get('winner_accuracy_delta', 0):+.1%}, "
            f"MAE {comp.get('mae_delta', 0):+.2f} "
            f"({'BEATS' if comp.get('beats_on_winner') or comp.get('beats_on_mae') else 'does not beat'})"
        )


async def main(args: argparse.Namespace) -> None:
    print("Running PreF1 Historical Backtesting Suite (real predictions, leakage-safe)...")
    await init_db()

    seasons = (
        list(range(args.start, args.end + 1)) if args.start else [args.season]
    )
    ran_any = False

    for season in seasons:
        async with AsyncSessionLocal() as session:
            runner = BacktestRunner(
                session,
                get_settings(),
                n_simulations=args.sims,
                seed=args.seed,
            )
            record = await runner.run_season(season)
        if record:
            ran_any = True
            print_season_summary(record)
        else:
            print(
                f"Season {season}: no completed races with sufficient data — "
                "run scripts/ingest_historical.py first."
            )

    if not ran_any:
        print("\nNo seasons could be evaluated. The API will report no backtests.")
        sys.exit(1)

    print("\nBacktesting suite complete. Results persisted to the database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PreF1 historical backtests")
    parser.add_argument("--season", type=int, default=None, help="Single season to evaluate")
    parser.add_argument("--start", type=int, default=None, help="First season (inclusive)")
    parser.add_argument("--end", type=int, default=None, help="Last season (inclusive)")
    parser.add_argument("--sims", type=int, default=5000, help="Monte Carlo sims per race")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic RNG seed")
    args = parser.parse_args()
    if args.season is None and args.start is None:
        parser.error("Provide --season or --start/--end")
    asyncio.run(main(args))
