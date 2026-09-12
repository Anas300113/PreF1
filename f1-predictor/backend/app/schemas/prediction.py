from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class CircuitSchema(BaseModel):
    id: str
    name: str
    country: Optional[str] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    circuit_type: Optional[str] = None
    overtaking_difficulty: Optional[float] = None
    tyre_degradation_index: Optional[float] = None
    safety_car_rate: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class RaceSchema(BaseModel):
    id: str
    season_year: int
    round_number: int
    name: str
    race_date: Optional[date] = None
    circuit: Optional[CircuitSchema] = None
    is_sprint_weekend: bool = False
    status: str = "scheduled"

    model_config = ConfigDict(from_attributes=True)

class DriverPredictionSchema(BaseModel):
    driver_id: str
    code: str
    full_name: str
    team: str
    team_color: str
    win_probability: float
    podium_probability: float
    top5_probability: float
    top10_probability: float
    points_probability: float
    dnf_probability: float
    expected_position: float
    median_position: float
    p10_position: float
    p25_position: float
    p75_position: float
    p90_position: float
    expected_points: float
    position_distribution: Dict[str, float]

    model_config = ConfigDict(from_attributes=True)

class WeatherSchema(BaseModel):
    source: str
    retrieved_at: str
    temperature_c: Optional[float] = 22.0
    precipitation_probability: Optional[float] = 0.0
    precipitation_mm: Optional[float] = 0.0
    wind_speed_ms: Optional[float] = 5.0
    cloud_cover_pct: Optional[float] = 20.0
    humidity_pct: Optional[float] = 50.0
    is_wet: bool = False
    weather_code: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class ModelMetadataSchema(BaseModel):
    version: str
    training_cutoff: str
    simulation_count: int
    simulation_seed: int
    feature_version: str
    created_at: str
    runtime_seconds: Optional[float] = None

class PredictionResponseSchema(BaseModel):
    race: RaceSchema
    model: ModelMetadataSchema
    drivers: List[DriverPredictionSchema]
    qualifying_prediction: List[Dict[str, Any]]
    weather: WeatherSchema
    explanations: Dict[str, Any]
    disclaimer: str
    data_status: Optional[str] = "ok"
    scenarios: Optional[Dict[str, Any]] = None

class SimulationRequest(BaseModel):
    simulation_count: int = 10000
    seed: Optional[int] = 42
    weather_override: Optional[str] = None  # 'dry', 'wet', 'mixed'
    safety_car_override: Optional[str] = None  # 'low', 'normal', 'high'
    tyre_deg_override: Optional[str] = None  # 'low', 'normal', 'high'

class ScenarioRequest(BaseModel):
    weather: str = "dry"
    safety_car: str = "normal"
    tyre_deg: str = "normal"
    simulation_count: int = 10000

class HealthResponse(BaseModel):
    status: str
    version: str
    model_version: str
    db_status: str
    timestamp: str
