"""Versioned model registry with integrity verification.

Every model artifact is stored with metadata identifying what produced it
(model_id, version, training cutoff, feature schema version, metrics) and a
SHA-256 checksum of the artifact bytes.  Production startup calls
``verify()`` — if a required model is missing or corrupt the caller decides
whether to FAIL CLOSED (settings.require_trained_models) or to explicitly
surface "MODEL UNAVAILABLE" to users.  Silent heuristic fallback is
forbidden: ``load_status()`` must be reported alongside any prediction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ModelStatus:
    """Verification status for one registered model artifact."""

    model_type: str
    version: str
    artifact_path: str
    artifact_exists: bool
    metadata_exists: bool
    checksum_ok: Optional[bool] = None  # None when artifact missing
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def available(self) -> bool:
        # A checksum *mismatch* (checksum_ok is False) is the only integrity
        # failure; legacy metadata without a recorded checksum still loads.
        return (
            self.artifact_exists
            and self.metadata_exists
            and self.checksum_ok is not False
        )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ModelRegistry:
    """Filesystem-backed registry for trained model artifacts."""

    # Metadata keys every production registration should carry.
    REQUIRED_METADATA = (
        "model_id",
        "model_version",
        "training_date",
        "training_data_cutoff",
        "feature_schema_version",
    )

    def __init__(self, models_dir: str = "./models/trained"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = self.models_dir / "metadata"
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    def artifact_path(self, model_type: str, version: str) -> Path:
        return self.models_dir / f"{model_type}_{version}.joblib"

    def metadata_path(self, model_type: str, version: str) -> Path:
        return self.meta_dir / f"{model_type}_{version}.json"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def save_model(
        self,
        model_obj: Any,
        model_type: str,
        version: str,
        metadata: Dict[str, Any],
    ) -> str:
        model_path = self.artifact_path(model_type, version)
        meta_path = self.metadata_path(model_type, version)

        if hasattr(model_obj, "save"):
            model_obj.save(str(model_path))
        else:  # pragma: no cover - pass-through for raw estimators
            import joblib

            joblib.dump(model_obj, str(model_path))

        record = {
            "model_id": model_type,
            "model_version": version,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "artifact_checksum_sha256": sha256_file(model_path),
            **metadata,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        return str(model_path)

    # ------------------------------------------------------------------
    # Read / verify
    # ------------------------------------------------------------------
    def get_metadata(self, model_type: str, version: str) -> Optional[Dict[str, Any]]:
        meta_path = self.metadata_path(model_type, version)
        if not meta_path.exists():
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def verify(self, model_type: str, version: str) -> ModelStatus:
        """Verify one artifact: exists, metadata present, checksum matches."""
        artifact = self.artifact_path(model_type, version)
        meta = self.get_metadata(model_type, version)

        status = ModelStatus(
            model_type=model_type,
            version=version,
            artifact_path=str(artifact),
            artifact_exists=artifact.exists(),
            metadata_exists=meta is not None,
            metadata=meta or {},
        )
        if not status.artifact_exists:
            status.error = "artifact_missing"
            return status
        if meta is None:
            status.error = "metadata_missing"
            return status

        recorded = meta.get("artifact_checksum_sha256")
        if recorded:
            try:
                status.checksum_ok = sha256_file(artifact) == recorded
            except OSError as exc:
                status.error = f"checksum_unreadable: {exc}"
                return status
            if not status.checksum_ok:
                status.error = "checksum_mismatch"
        else:
            # Legacy metadata written before checksums — flag but do not
            # fail: the artifact loads, it just cannot be integrity-checked.
            status.checksum_ok = None
            status.error = "checksum_unrecorded"
        return status

    def verify_required(self, required: List[Dict[str, str]]) -> Dict[str, ModelStatus]:
        """Verify a list of {"model_type": ..., "version": ...} requirements.

        Returns {f"{type}_{version}": ModelStatus}.
        """
        out: Dict[str, ModelStatus] = {}
        for req in required:
            mt, ver = req["model_type"], req["version"]
            out[f"{mt}_{ver}"] = self.verify(mt, ver)
        return out

    def load_status(self, required: List[Dict[str, str]]) -> Dict[str, Any]:
        """Summary suitable for API/health responses."""
        verified = self.verify_required(required)
        return {
            "all_available": all(s.available for s in verified.values()),
            "models": {
                key: {
                    "available": s.available,
                    "artifact_exists": s.artifact_exists,
                    "metadata_exists": s.metadata_exists,
                    "checksum_ok": s.checksum_ok,
                    "training_data_cutoff": s.metadata.get("training_data_cutoff"),
                    "feature_schema_version": s.metadata.get("feature_schema_version"),
                    "error": s.error,
                }
                for key, s in verified.items()
            },
        }

    def list_models(self) -> Dict[str, list]:
        models: Dict[str, list] = {}
        for f in sorted(self.meta_dir.glob("*.json")):
            m_type = f.stem.rsplit("_", 1)[0]
            models.setdefault(m_type, []).append(f.name)
        return models

