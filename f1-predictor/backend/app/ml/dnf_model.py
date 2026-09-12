from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib

class DNFModel:
    MODEL_FEATURES = [
        "driver_dnf_rate_10", "team_dnf_rate_5",
        "driver_rolling_5_finish", "circuit_overtaking_difficulty"
    ]

    DEFAULT_PARAMS = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "max_depth": 3,
        "learning_rate": 0.05,
        "n_estimators": 150,
        "subsample": 0.8,
        "scale_pos_weight": 5,
        "random_state": 42,
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or self.DEFAULT_PARAMS
        self.model: Optional[xgb.XGBClassifier] = None
        self.is_trained: bool = False
        self.feature_names: List[str] = self.MODEL_FEATURES

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        X_tr = X_train[self.feature_names]
        self.model = xgb.XGBClassifier(**self.params)
        self.model.fit(X_tr, y_train)
        self.is_trained = True

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained or self.model is None:
            # Fallback 10% DNF
            return np.full(len(X), 0.10)
        X_test = X[self.feature_names]
        probs = self.model.predict_proba(X_test)
        return probs[:, 1]

    def save(self, path: str) -> None:
        joblib.dump({"model": self.model, "params": self.params, "features": self.feature_names}, path)

    @classmethod
    def load(cls, path: str) -> "DNFModel":
        data = joblib.load(path)
        inst = cls(data["params"])
        inst.model = data["model"]
        inst.feature_names = data["features"]
        inst.is_trained = True
        return inst
