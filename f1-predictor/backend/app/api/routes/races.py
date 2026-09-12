from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_settings
from app.models import Race, Prediction
from app.schemas.prediction import (
    RaceSchema,
    PredictionResponseSchema,
    SimulationRequest,
    WeatherSchema,
)
from app.services.prediction_service import PredictionService
from app.services.weather_client import OpenMeteoClient

router = APIRouter(prefix="/api/races", tags=["races"])


@router.get("/", response_model=List[RaceSchema])
async def list_races(season: Optional[int] = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(Race).options(selectinload(Race.circuit))
    if season:
        stmt = stmt.where(Race.season_year == season)
    stmt = stmt.order_by(Race.season_year.desc(), Race.round_number.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/next", response_model=RaceSchema)
async def get_next_race(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Race)
        .options(selectinload(Race.circuit))
        .where(Race.status == "scheduled")
        .order_by(Race.race_date.asc())
    )
    res = await db.execute(stmt)
    next_race = res.scalars().first()
    if not next_race:
        stmt_last = (
            select(Race)
            .options(selectinload(Race.circuit))
            .order_by(Race.season_year.desc(), Race.round_number.desc())
        )
        next_race = (await db.execute(stmt_last)).scalars().first()
    if not next_race:
        raise HTTPException(status_code=404, detail="No races found. Run data ingestion first.")
    return next_race


@router.get("/{race_id}", response_model=RaceSchema)
async def get_race(race_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Race).options(selectinload(Race.circuit)).where(Race.id == race_id)
    race = (await db.execute(stmt)).scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail=f"Race {race_id} not found")
    return race


@router.get("/{race_id}/weather", response_model=WeatherSchema)
async def get_race_weather(race_id: str, db: AsyncSession = Depends(get_db), settings=Depends(get_settings)):
    stmt = select(Race).options(selectinload(Race.circuit)).where(Race.id == race_id)
    race = (await db.execute(stmt)).scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail=f"Race {race_id} not found")

    svc = PredictionService(db, settings)
    weather = await svc._fetch_weather(race, None)
    return weather


@router.get("/{race_id}/prediction")
async def get_prediction(
    race_id: str,
    sim_count: int = Query(10000, ge=1000, le=500000),
    seed: int = Query(42),
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
):
    svc = PredictionService(db, settings)
    try:
        return await svc.generate_prediction(race_id, simulation_count=sim_count, seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{race_id}/predict")
async def trigger_prediction(
    race_id: str,
    sim_request: SimulationRequest = SimulationRequest(),
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
):
    svc = PredictionService(db, settings)
    try:
        return await svc.generate_prediction(
            race_id,
            simulation_count=sim_request.simulation_count,
            seed=sim_request.seed or 42,
            weather_override=sim_request.weather_override,
            safety_car_override=sim_request.safety_car_override,
            tyre_deg_override=sim_request.tyre_deg_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{race_id}/simulate")
async def simulate_scenario(
    race_id: str,
    sim_request: SimulationRequest = SimulationRequest(),
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
):
    """Run Monte Carlo with scenario overrides (weather, safety car, tyre deg)."""
    svc = PredictionService(db, settings)
    try:
        return await svc.generate_prediction(
            race_id,
            simulation_count=sim_request.simulation_count,
            seed=sim_request.seed or 42,
            weather_override=sim_request.weather_override,
            safety_car_override=sim_request.safety_car_override,
            tyre_deg_override=sim_request.tyre_deg_override,
            persist=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{race_id}/prediction/history")
async def get_prediction_history(race_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Prediction)
        .where(Prediction.race_id == race_id)
        .order_by(Prediction.created_at.desc())
        .limit(20)
    )
    preds = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": p.id,
            "race_id": p.race_id,
            "snapshot_type": p.snapshot_type,
            "model_version": p.model_version,
            "simulation_count": p.simulation_count,
            "simulation_seed": p.simulation_seed,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in preds
    ]
