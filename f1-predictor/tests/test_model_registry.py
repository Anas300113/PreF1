"""P0.3 regression tests: model registry integrity + explicit fallback status.

Guards against silent downgrade to heuristics: artifacts must carry
checksummed metadata, verification must detect corruption/removal, and the
prediction service must report which backend produced each forecast.
"""
import json

import pytest

from app.ml.model_registry import ModelRegistry, sha256_file
from app.ml.qualifying_model import QualifyingModel


class _FakeModel:
    """Minimal saveable object for registry tests."""

    def __init__(self):
        self.is_trained = False

    def save(self, path: str):
        with open(path, "wb") as f:
            f.write(b"fake-model-bytes")


def test_save_writes_checksummed_metadata(tmp_path):
    registry = ModelRegistry(str(tmp_path / "models"))
    registry.save_model(_FakeModel(), "qualifying", "v1.0", {
        "training_data_cutoff": "2024-12-01T00:00:00+00:00",
        "feature_schema_version": "v1.0",
    })

    meta = registry.get_metadata("qualifying", "v1.0")
    assert meta is not None
    assert meta["model_id"] == "qualifying"
    assert meta["model_version"] == "v1.0"
    assert meta["training_date"]
    assert meta["training_data_cutoff"] == "2024-12-01T00:00:00+00:00"
    assert meta["feature_schema_version"] == "v1.0"
    # Checksum must match the actual artifact bytes.
    artifact = registry.artifact_path("qualifying", "v1.0")
    assert meta["artifact_checksum_sha256"] == sha256_file(artifact)


def test_verify_passes_for_intact_artifact(tmp_path):
    registry = ModelRegistry(str(tmp_path / "models"))
    registry.save_model(_FakeModel(), "race_pace", "v1.0", {
        "training_data_cutoff": "2024-12-01T00:00:00+00:00",
        "feature_schema_version": "v1.0",
    })
    status = registry.verify("race_pace", "v1.0")
    assert status.available
    assert status.checksum_ok is True
    assert status.error is None


def test_verify_detects_missing_artifact(tmp_path):
    """A clean clone without .joblib files must be detected, not ignored."""
    registry = ModelRegistry(str(tmp_path / "models"))
    # Metadata exists but artifact does not (gitignored artifacts case).
    registry.meta_dir.mkdir(parents=True, exist_ok=True)
    registry.metadata_path("qualifying", "v1.0").write_text(
        json.dumps({"model_id": "qualifying", "model_version": "v1.0"}), encoding="utf-8"
    )
    status = registry.verify("qualifying", "v1.0")
    assert not status.available
    assert status.error == "artifact_missing"


def test_verify_detects_corrupted_artifact(tmp_path):
    registry = ModelRegistry(str(tmp_path / "models"))
    registry.save_model(_FakeModel(), "dnf", "v1.0", {
        "training_data_cutoff": "2024-12-01T00:00:00+00:00",
        "feature_schema_version": "v1.0",
    })
    # Corrupt the artifact after registration.
    with open(registry.artifact_path("dnf", "v1.0"), "wb") as f:
        f.write(b"tampered-bytes")
    status = registry.verify("dnf", "v1.0")
    assert not status.available
    assert status.checksum_ok is False
    assert status.error == "checksum_mismatch"


def test_verify_detects_missing_metadata(tmp_path):
    registry = ModelRegistry(str(tmp_path / "models"))
    # Artifact without metadata must not verify as available.
    registry.models_dir.mkdir(parents=True, exist_ok=True)
    registry.artifact_path("qualifying", "v1.0").write_bytes(b"bytes")
    status = registry.verify("qualifying", "v1.0")
    assert not status.available
def test_load_status_summary_shape(tmp_path):
    registry = ModelRegistry(str(tmp_path / "models"))
    registry.save_model(_FakeModel(), "qualifying", "v1.0", {"training_data_cutoff": "x"})
    summary = registry.load_status([
        {"model_type": "qualifying", "version": "v1.0"},
        {"model_type": "race_pace", "version": "v1.0"},
    ])
    assert summary["all_available"] is False  # race_pace missing
    assert summary["models"]["qualifying_v1.0"]["available"] is True
    assert summary["models"]["race_pace_v1.0"]["available"] is False
    assert summary["models"]["race_pace_v1.0"]["error"] == "artifact_missing"


def test_required_model_list_parsing():
    from app.config import Settings

    settings = Settings(required_models="qualifying:v1.2, race_pace:v1.0 ,dnf:v1.0")
    parsed = settings.required_model_list()
    assert parsed == [
        {"model_type": "qualifying", "version": "v1.2"},
        {"model_type": "race_pace", "version": "v1.0"},
        {"model_type": "dnf", "version": "v1.0"},
    ]


def test_prediction_service_reports_model_provenance(tmp_path):
    """_load_models must return per-model backend provenance — never a
    silent heuristic fallback."""
    from app.config import Settings
    from app.services.prediction_service import PredictionService

    settings = Settings(models_dir=str(tmp_path / "missing_models"))
    service = PredictionService(db=None, settings=settings)
    quali, pace, dnf, provenance = service._load_models()

    # No artifacts in tmp dir → every model explicitly heuristic.
    assert set(provenance) == {"qualifying", "race_pace", "dnf"}
    for info in provenance.values():
        assert info["backend"] == "heuristic"
        assert info["artifact_available"] is False
        assert info["error"] == "artifact_missing"
    assert quali.is_trained is False
    assert pace.is_trained is False
    assert dnf.is_trained is False


def test_prediction_service_loads_real_artifacts(tmp_path):
    """With valid registered artifacts the service loads them and reports the
    launcher's checksum; a corrupt artifact is surfaced as unavailable, never
    served as an ML prediction."""
    import xgboost as xgb
    import numpy as np
    from app.config import Settings
    from app.services.prediction_service import PredictionService

    models_dir = tmp_path / "models"
    registry = ModelRegistry(str(models_dir))
    rng = np.random.default_rng(0)
    stub = _StubTrainedModel(rng)
    for model_type in ("qualifying", "race_pace", "dnf"):
        registry.save_model(
            stub, model_type, "v1.0", {
                "training_data_cutoff": "2024-12-01T00:00:00+00:00",
                "feature_schema_version": "v1.0",
            },
        )
    # Corrupt one artifact (race_pace): the service must refuse it.
    registry.artifact_path("race_pace", "v1.0").write_bytes(b"tampered")

    settings = Settings(models_dir=str(models_dir))
    service = PredictionService(db=None, settings=settings)
    _, _, _, provenance = service._load_models()

    assert provenance["qualifying"]["backend"] == "xgboost"
    assert provenance["qualifying"]["artifact_available"] is True
    assert provenance["race_pace"]["backend"] == "heuristic"
    assert provenance["race_pace"]["artifact_available"] is False
    assert provenance["dnf"]["backend"] == "xgboost"


def test_verify_detects_missing_metadata(tmp_path):
    registry = ModelRegistry(str(tmp_path / "models"))
    # Artifact without metadata must not verify as available.
    registry.models_dir.mkdir(parents=True, exist_ok=True)
    registry.artifact_path("qualifying", "v1.0").write_bytes(b"bytes")
    status = registry.verify("qualifying", "v1.0")
    assert status.error == "metadata_missing"


class _StubTrainedModel:
    """Model with a fitted booster so the service's fit-check passes."""

    def __init__(self, rng):
        import xgboost as xgb

        self.is_trained = True
        self.model = xgb.XGBRegressor(max_depth=2, n_estimators=5, random_state=0)
        self.model.fit(rng.standard_normal((50, 5)), rng.integers(0, 2, 50), verbose=False)
        self.feature_names = [f"f{i}" for i in range(5)]

    def save(self, path: str):
        import joblib

        joblib.dump(
            {
                "params": {},
                "model": self.model,
                "features": self.feature_names,
            },
            path,
        )

