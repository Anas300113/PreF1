from fastapi import APIRouter, Depends
from app.api.deps import get_settings

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/")
async def get_models_info(settings = Depends(get_settings)):
    return {
        "active_model_version": settings.model_version,
        "feature_version": settings.feature_version,
        "architecture": "Modular XGBoost + Vectorised Monte Carlo Simulation",
        "components": [
            {"name": "Qualifying Model", "type": "XGBRegressor", "target": "gap_to_pole_s"},
            {"name": "Race Pace Model", "type": "XGBRegressor", "target": "normalized_race_pace"},
            {"name": "Incident / DNF Model", "type": "XGBClassifier", "target": "binary_dnf"},
            {"name": "Tyre Degradation Model", "type": "Regression Slope Estimator", "target": "seconds_per_lap_deg"},
            {"name": "Monte Carlo Engine", "type": "NumPy Vectorised Engine", "simulations": settings.simulation_default_count},
            {"name": "Calibration", "type": "Isotonic Regression", "metric": "Brier Score"},
        ]
    }
