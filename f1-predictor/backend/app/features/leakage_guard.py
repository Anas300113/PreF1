from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import pandas as pd

class LeakageError(Exception):
    pass

@dataclass
class Feature:
    name: str
    value: Any
    source: str
    observation_timestamp: datetime
    availability_timestamp: datetime

    def is_available_at(self, cutoff: datetime) -> bool:
        return self.availability_timestamp <= cutoff

@dataclass
class FeatureSet:
    features: dict[str, Feature] = field(default_factory=dict)
    information_cutoff: Optional[datetime] = None

    def add(self, feature: Feature) -> None:
        if self.information_cutoff and not feature.is_available_at(self.information_cutoff):
            raise LeakageError(
                f"Feature '{feature.name}' with timestamp {feature.availability_timestamp} "
                f"violates cutoff {self.information_cutoff}"
            )
        self.features[feature.name] = feature

    def to_dict(self) -> dict[str, Any]:
        return {name: f.value for name, f in self.features.items()}

def validate_no_leakage(df: pd.DataFrame, cutoff_col: str, timestamp_cols: list[str]) -> None:
    for _, row in df.iterrows():
        cutoff = row[cutoff_col]
        for col in timestamp_cols:
            if pd.notna(row[col]) and row[col] > cutoff:
                raise LeakageError(f"Timestamp in column '{col}' ({row[col]}) is greater than cutoff ({cutoff})")
