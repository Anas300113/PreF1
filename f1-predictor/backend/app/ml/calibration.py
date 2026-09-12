from typing import Dict, Any
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, log_loss
import joblib

class ProbabilityCalibrator:
    """Isotonic regression probability calibrator."""

    def __init__(self):
        self.calibrators: Dict[str, IsotonicRegression] = {}

    def fit(self, y_prob: np.ndarray, y_true: np.ndarray, outcome_name: str) -> None:
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(y_prob, y_true)
        self.calibrators[outcome_name] = iso

    def calibrate(self, y_prob: np.ndarray, outcome_name: str) -> np.ndarray:
        if outcome_name not in self.calibrators:
            return np.clip(y_prob, 0.0, 1.0)
        return self.calibrators[outcome_name].predict(y_prob)

    def compute_metrics(self, y_prob: np.ndarray, y_true: np.ndarray) -> Dict[str, float]:
        brier = float(brier_score_loss(y_true, y_prob))
        ll = float(log_loss(y_true, y_prob, eps=1e-15))
        ece = float(np.mean(np.abs(y_prob - y_true)))
        return {"brier_score": brier, "log_loss": ll, "expected_calibration_error": ece}

    def save(self, path: str):
        joblib.dump(self.calibrators, path)

    @classmethod
    def load(cls, path: str) -> "ProbabilityCalibrator":
        inst = cls()
        inst.calibrators = joblib.load(path)
        return inst
