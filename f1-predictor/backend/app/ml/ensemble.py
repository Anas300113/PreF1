from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from app.ml.qualifying_model import QualifyingModel
from app.ml.race_pace_model import RacePaceModel
from app.ml.dnf_model import DNFModel
from app.ml.baseline_model import BaselineModel

class ModelEnsemble:
    """Combines individual models into ensemble race pace & DNF estimates."""

    def __init__(
        self,
        qualifying_model: QualifyingModel,
        race_pace_model: RacePaceModel,
        dnf_model: DNFModel,
        weights: Optional[Dict[str, float]] = None
    ):
        self.q_model = qualifying_model
        self.r_model = race_pace_model
        self.dnf_model = dnf_model
        self.weights = weights or {"qualifying": 0.4, "race_pace": 0.6}

    def predict_race_pace_deltas(self, race_features: pd.DataFrame) -> Dict[str, float]:
        q_preds = self.q_model.predict(race_features)
        r_preds = self.r_model.predict(race_features)

        w_q = self.weights.get("qualifying", 0.4)
        w_r = self.weights.get("race_pace", 0.6)

        combined = w_q * q_preds + w_r * r_preds
        result = {}
        for idx, row in race_features.iterrows():
            d_id = str(row.get("driver_id", idx))
            result[d_id] = float(combined[idx])
        return result

    def predict_dnf_probabilities(self, race_features: pd.DataFrame) -> Dict[str, float]:
        probs = self.dnf_model.predict_proba(race_features)
        result = {}
        for idx, row in race_features.iterrows():
            d_id = str(row.get("driver_id", idx))
            result[d_id] = float(probs[idx])
        return result
