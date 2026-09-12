from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib

class RacePaceModel:
    MODEL_FEATURES = [
        "driver_rolling_3_finish", "driver_rolling_5_finish",
        "driver_rolling_10_finish", "driver_circuit_avg_finish",
        "team_quali_pace_vs_field", "circuit_length_km",
        "circuit_overtaking_difficulty", "weather_is_wet",
        "weather_race_temp_c", "quali_gap_to_pole", "quali_position"
    ]

    DEFAULT_PARAMS = {
        "objective": "reg:squarederror",
        "max_depth": 4,
        "learning_rate": 0.05,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 5,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "n_jobs": -1,
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or self.DEFAULT_PARAMS
        self.model: Optional[xgb.XGBRegressor] = None
        self.is_trained: bool = False
        self.feature_names: List[str] = self.MODEL_FEATURES

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        X_tr = X_train[self.feature_names]
        self.model = xgb.XGBRegressor(**self.params)
        self.model.fit(X_tr, y_train)
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained or self.model is None:
            return np.zeros(len(X))
        X_test = X[self.feature_names]
        return self.model.predict(X_test)

    def save(self, path: str) -> None:
        joblib.dump({"model": self.model, "params": self.params, "features": self.feature_names}, path)

    @classmethod
    def load(cls, path: str) -> "RacePaceModel":
        data = joblib.load(path)
        inst = cls(data["params"])
        inst.model = data["model"]
        inst.feature_names = data["features"]
        inst.is_trained = True
        return inst
