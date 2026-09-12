from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_settings
from app.explainability.factor_summary import generate_explanation
from app.features.race_feature_builder import RaceFeatureBuilder
from app.ml.qualifying_model import QualifyingModel
from pathlib import Path

router = APIRouter(prefix="/api/explain", tags=["explain"])


@router.get("/{race_id}/{driver_id}")
async def explain_driver_prediction(
    race_id: str,
    driver_id: str,
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
):
    builder = RaceFeatureBuilder(db)
    features, race = await builder.build_features(race_id)
    if race is None:
        raise HTTPException(status_code=404, detail=f"Race {race_id} not found")

    driver_feats = features[features["driver_id"] == driver_id]
    if driver_feats.empty:
        raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found for race")

    row = driver_feats.iloc[0]
    shap_vals = {
        "driver_rolling_3_finish": float(row.get("driver_rolling_3_finish", 10)),
        "driver_quali_vs_teammate_3": float(row.get("driver_quali_vs_teammate_3", 0)),
        "team_quali_pace_vs_field": float(row.get("team_quali_pace_vs_field", 0.5)),
        "circuit_overtaking_difficulty": float(row.get("circuit_overtaking_difficulty", 0.5)),
        "weather_is_wet": float(1.0 if row.get("weather_is_wet") else 0.0),
    }

    model_path = Path(settings.models_dir) / "qualifying_v1.0.joblib"
    if model_path.exists():
        try:
            model = QualifyingModel.load(str(model_path))
            if model.is_trained:
                shap_map = model.get_shap_values(driver_feats)
                if driver_id in shap_map:
                    shap_vals = shap_map[driver_id]
        except Exception:
            pass

    return {
        "race_id": race_id,
        "driver_id": driver_id,
        "explanation": generate_explanation(driver_id, shap_vals),
        "features": row.to_dict(),
        "disclaimer": "Factors reflect statistical associations, not proven causal relationships.",
    }
