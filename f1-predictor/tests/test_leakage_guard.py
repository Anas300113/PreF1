from datetime import datetime, timedelta, timezone

import pytest

from app.features.leakage_guard import Feature, FeatureSet, LeakageError, validate_no_leakage


def test_no_leakage_when_cutoff_respected():
    cutoff = datetime(2024, 6, 1, tzinfo=timezone.utc)
    fs = FeatureSet(information_cutoff=cutoff)
    fs.add(Feature("driver_rolling_3_finish", 3.5, "db", cutoff, cutoff))
    fs.add(Feature("team_quali_pace", -0.2, "db", cutoff, cutoff))
    assert fs.to_dict()["driver_rolling_3_finish"] == 3.5


def test_leakage_detected_when_feature_is_not_yet_available():
    cutoff = datetime(2024, 6, 1, tzinfo=timezone.utc)
    future = datetime(2024, 6, 2, tzinfo=timezone.utc)
    fs = FeatureSet(information_cutoff=cutoff)
    with pytest.raises(LeakageError):
        fs.add(Feature("future_result", 1.0, "db", future, future))


def test_no_leakage_at_boundary_when_availability_equals_cutoff():
    cutoff = datetime(2024, 6, 1, tzinfo=timezone.utc)
    fs = FeatureSet(information_cutoff=cutoff)
    # availability_timestamp <= cutoff is permitted (boundary inclusive).
    fs.add(Feature("qualifier", 2.0, "db", cutoff, cutoff))
    assert fs.to_dict()["qualifier"] == 2.0


def test_leakage_detected_when_availability_after_cutoff_even_if_observation_before():
    cutoff = datetime(2024, 6, 1, tzinfo=timezone.utc)
    # The observation timestamp is before the cutoff, but the feature only
    # becomes available on race day (2024-06-02) - still future information
    # relative to the cutoff, so it must be rejected.
    observed = datetime(2024, 5, 31, tzinfo=timezone.utc)
    fs = FeatureSet(information_cutoff=cutoff)
    with pytest.raises(LeakageError):
        fs.add(Feature("race_day_obs", 1.0, "db", observed, cutoff + timedelta(days=1)))


def test_validate_no_leakage_rejects_future_timestamps():
    import pandas as pd

    # Happy path: every timestamp column is <= its row's cutoff.
    df_clean = pd.DataFrame(
        [
            {"race_date": datetime(2024, 6, 1, tzinfo=timezone.utc),
             "qualifier": datetime(2024, 6, 1, tzinfo=timezone.utc)},
            {"race_date": datetime(2024, 6, 2, tzinfo=timezone.utc),
             "qualifier": datetime(2024, 6, 2, tzinfo=timezone.utc)},
        ]
    )
    validate_no_leakage(df_clean, "race_date", ["qualifier"])

    # A row whose timestamp column exceeds its cutoff must raise.
    df_leak = pd.DataFrame(
        [
            {"race_date": datetime(2024, 6, 1, tzinfo=timezone.utc),
             "qualifier": datetime(2024, 6, 1, tzinfo=timezone.utc)},
            {"race_date": datetime(2024, 6, 3, tzinfo=timezone.utc),
             "qualifier": datetime(2024, 6, 4, tzinfo=timezone.utc)},
        ]
    )
    with pytest.raises(LeakageError):
        validate_no_leakage(df_leak, "race_date", ["qualifier"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
