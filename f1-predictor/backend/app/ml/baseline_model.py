from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

class BaselineModel:
    """Historical baseline using championship position or rolling average."""

    def predict_from_standings(self, standings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sorted_standings = sorted(standings, key=lambda x: int(x.get("position", 99)))
        results = []
        for idx, s in enumerate(sorted_standings):
            results.append({
                "driver_id": s["driver_id"],
                "predicted_position": idx + 1,
                "confidence": max(0.1, 1.0 - (idx * 0.04))
            })
        return results

    def predict_from_rolling(self, df_features: pd.DataFrame) -> pd.DataFrame:
        df = df_features.copy()
        if "driver_rolling_5_finish" in df.columns:
            df["predicted_score"] = df["driver_rolling_5_finish"].fillna(15.0)
        else:
            df["predicted_score"] = 10.0
        df["predicted_position"] = np.argsort(np.argsort(df["predicted_score"])) + 1
        return df.sort_values("predicted_position")
