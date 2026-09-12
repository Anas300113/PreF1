from datetime import datetime, timezone

import pytest

from app.features.leakage_guard import Feature, FeatureSet, LeakageError


def test_no_leakage_when_cutoff_respected():
    cutoff = datetime(2024, 6, 1, tzinfo=timezone.utc)
    fs = FeatureSet(information_cutoff=cutoff)
    fs.add(Feature("driver_rolling_3_finish", 3.5, "db", cutoff, cutoff))
    fs.add(Feature("team_quali_pace", -0.2, "db", cutoff, cutoff))
    assert fs.to_dict()["driver_rolling_3_finish"] == 3.5


def test_leakage_detected_when_feature_after_cutoff():
    cutoff = datetime(2024, 6, 1, tzinfo=timezone.utc)
    future = datetime(2024, 6, 2, tzinfo=timezone.utc)
    fs = FeatureSet(information_cutoff=cutoff)
    with pytest.raises(LeakageError):
        fs.add(Feature("future_result", 1.0, "db", future, future))
