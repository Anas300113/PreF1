from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
import joblib

class QualifyingModel:
    MODEL_FEATURES = [
        "driver_rolling_3_finish", "driver_rolling_5_finish",
        "driver_quali_vs_teammate_3", "driver_circuit_avg_finish",
        "team_quali_pace_vs_field", "circuit_length_km",
        "circuit_overtaking_difficulty", "fp1_pace_delta",
        "fp2_pace_delta", "fp3_pace_delta", "weather_is_wet",
        "weather_race_temp_c"
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

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None
    ) -> None:
        X_tr = X_train[self.feature_names]
        self.model = xgb.XGBRegressor(**self.params)
        
        if X_val is not None and y_val is not None:
            X_v = X_val[self.feature_names]
            self.model.fit(X_tr, y_train, eval_set=[(X_v, y_val)], verbose=False)
        else:
            self.model.fit(X_tr, y_train)

        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained or self.model is None:
            # Fallback naive gap
            return np.zeros(len(X))
        X_test = X[self.feature_names]
        return self.model.predict(X_test)

    def predict_grid_order(self, race_features: pd.DataFrame) -> pd.DataFrame:
        preds = self.predict(race_features)
        df = race_features.copy()
        df["predicted_gap_to_pole"] = preds
        df["predicted_position"] = np.argsort(np.argsort(preds)) + 1
        return df.sort_values("predicted_position")

    def get_shap_values(self, X: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        if not self.is_trained or self.model is None:
            return {}
        X_sub = X[self.feature_names]
        explainer = shap.TreeExplainer(self.model)
        shap_vals = explainer.shap_values(X_sub)
        
        result = {}
        for idx, row in X.iterrows():
            driver_id = str(row.get("driver_id", idx))
            driver_shaps = {}
            for f_idx, f_name in enumerate(self.feature_names):
                driver_shaps[f_name] = float(shap_vals[idx, f_idx])
            result[driver_id] = driver_shaps
        return result

    def save(self, path: str) -> None:
        joblib.dump({"model": self.model, "params": self.params, "features": self.feature_names}, path)

    @classmethod
    def load(cls, path: str) -> "QualifyingModel":
        data = joblib.load(path)
        inst = cls(data["params"])
        inst.model = data["model"]
        inst.feature_names = data["features"]
        inst.is_trained = True
        return inst
