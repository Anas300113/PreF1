import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.backtesting.baseline_comparator import BaselineComparator
from app.models import BacktestSeason, BacktestRace

router = APIRouter(prefix="/api/backtests", tags=["backtests"])


def _parse_json(raw: str | None) -> dict:
    try:
        return json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        return {}


@router.get("/")
async def list_backtests(db: AsyncSession = Depends(get_db)):
    """Season-level backtest summaries (real evaluation results from the DB).

    Returns an empty list if no backtest has been run yet — the API never
    fabricates performance metrics.
    """
    stmt = select(BacktestSeason).order_by(BacktestSeason.season.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "season": r.season,
            "n_races": r.n_races,
            "model_version": r.model_version,
            "training_cutoff": r.training_cutoff,
            "n_simulations": r.n_simulations,
            "simulation_seed": r.simulation_seed,
            **_parse_json(r.model_metrics),
            "baselines": _parse_json(r.baseline_metrics),
            "comparison": BaselineComparator.compare(
                _parse_json(r.model_metrics), _parse_json(r.baseline_metrics)
            ),
        }
        for r in rows
    ]


@router.get("/{season}")
async def get_season_backtest(season: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(BacktestSeason)
        .where(BacktestSeason.season == season)
        .order_by(BacktestSeason.created_at.desc())
    )
    season_row = (await db.execute(stmt)).scalars().first()
    if not season_row:
        raise HTTPException(
            status_code=404,
            detail=f"No backtest stored for season {season}. Run scripts/run_backtest.py first.",
        )

    races_stmt = (
        select(BacktestRace)
        .where(BacktestRace.backtest_season_id == season_row.id)
        .order_by(BacktestRace.race_date)
    )
    race_rows = (await db.execute(races_stmt)).scalars().all()

    return {
        "season": season_row.season,
        "n_races": season_row.n_races,
        "model_version": season_row.model_version,
        "training_cutoff": season_row.training_cutoff,
        "n_simulations": season_row.n_simulations,
        "simulation_seed": season_row.simulation_seed,
        **_parse_json(season_row.model_metrics),
        "baselines": _parse_json(season_row.baseline_metrics),
        "races": [
            {
                **_parse_json(r.model_metrics),
                "baselines": _parse_json(r.baselines),
            }
            for r in race_rows
        ],
    }
