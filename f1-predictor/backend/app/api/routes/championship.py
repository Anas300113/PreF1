from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.simulation.race_simulator import RaceSimulator
from app.simulation.strategy_engine import StrategyEngine
from app.ml.tyre_model import TyreModel
from app.simulation.championship_simulator import (
    ChampionshipDriver,
    ChampionshipRace,
    ChampionshipSimulator,
    format_championship_response,
)

router = APIRouter(prefix="/api/championship", tags=["championship"])


class ChampionshipDriverInput(BaseModel):
    driver_id: str
    code: str
    full_name: str
    team_id: str
    team_name: str
    current_points: float = 0.0


class ChampionshipRaceInput(BaseModel):
    race_id: str
    name: str
    round_number: int
    total_laps: int = 58
    is_sprint_weekend: bool = False
    circuit_deg_index: float = 0.5
    safety_car_prob: float = 0.50


class ChampionshipRequest(BaseModel):
    season: int = 2025
    drivers: List[ChampionshipDriverInput]
    remaining_races: List[ChampionshipRaceInput]
    n_simulations: int = 5000
    seed: int = 42


@router.post("/simulate")
async def simulate_championship(request: ChampionshipRequest):
    """Simulate the remainder of a championship season."""
    tyre_m = TyreModel()
    strat_e = StrategyEngine(tyre_m)
    sim = RaceSimulator(strat_e)
    champ_sim = ChampionshipSimulator(sim)

    drivers = [
        ChampionshipDriver(
            driver_id=d.driver_id,
            code=d.code,
            full_name=d.full_name,
            team_id=d.team_id,
            team_name=d.team_name,
            current_points=d.current_points,
        )
        for d in request.drivers
    ]

    races = [
        ChampionshipRace(
            race_id=r.race_id,
            name=r.name,
            round_number=r.round_number,
            total_laps=r.total_laps,
            is_sprint_weekend=r.is_sprint_weekend,
            circuit_deg_index=r.circuit_deg_index,
            safety_car_prob=r.safety_car_prob,
        )
        for r in request.remaining_races
    ]

    if not drivers:
        raise HTTPException(status_code=400, detail="At least one driver required")
    if not races:
        raise HTTPException(status_code=400, detail="At least one remaining race required")

    result = champ_sim.simulate(
        drivers=drivers,
        remaining_races=races,
        n_simulations=min(request.n_simulations, 50000),
        seed=request.seed,
    )

    response = format_championship_response(result)
    response["season"] = request.season
    return response
