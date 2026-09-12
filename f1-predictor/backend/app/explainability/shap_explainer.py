from typing import Dict, Any, List
import pandas as pd
import numpy as np

class SHAPExplainer:
    def __init__(self, qualifying_model=None, race_pace_model=None):
        self.q_model = qualifying_model
        self.r_model = race_pace_model

    def explain_driver(self, race_features: pd.DataFrame, driver_id: str) -> Dict[str, Any]:
        if self.q_model and hasattr(self.q_model, "get_shap_values"):
            all_shaps = self.q_model.get_shap_values(race_features)
            return all_shaps.get(driver_id, {})
        return {}
