import subprocess
import sys
from pathlib import Path

from app.schemas.prediction import (
    PredictionResponseSchema,
    SimulationRequest,
    ModelMetadataSchema,
    HealthResponse,
)

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"

# pydantic validates field names against the reserved "model_" namespace when the
# class is *defined*, so the warning fires at import time. It must therefore be
# probed in a fresh interpreter rather than in-process.
_IMPORT_PROBE = (
    "import warnings, sys\n"
    "with warnings.catch_warnings(record=True) as caught:\n"
    "    warnings.simplefilter('always')\n"
    "    import app.schemas.prediction\n"
    "hits = [str(w.message) for w in caught if 'protected namespace' in str(w.message)]\n"
    "print(chr(10).join(hits))\n"
    "sys.exit(1 if hits else 0)\n"
)


def test_simulation_request_defaults():
    req = SimulationRequest()
    assert req.simulation_count == 10000
    assert req.seed == 42


def test_prediction_response_schema_optional_fields():
    schema = PredictionResponseSchema.model_json_schema()
    assert "data_status" in schema["properties"]


def test_model_prefixed_fields_do_not_conflict_with_protected_namespace():
    """`model_*` fields are part of the API contract.

    pydantic reserves the `model_` namespace, so these schemas must set
    `protected_namespaces=()`. Without it, importing the module emits a
    UserWarning for every `model_*` field.
    """
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_PROBE],
        cwd=_BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"import emitted a protected-namespace warning:\n{result.stdout}{result.stderr}"
    )


def test_model_prefixed_fields_survive_serialisation():
    """Round-trip proves the `model_*` fields are not shadowed by pydantic."""
    meta = ModelMetadataSchema(
        version="v1.0",
        training_cutoff="2024-01-01",
        simulation_count=1000,
        simulation_seed=42,
        feature_version="fv1",
        created_at="2024-01-01",
        model_unavailable=True,
    )
    health = HealthResponse(
        status="ok",
        version="1.0",
        model_version="v1.0",
        db_status="ok",
        timestamp="2024-01-01",
    )

    assert meta.model_unavailable is True
    assert health.model_version == "v1.0"
    assert "model_unavailable" in meta.model_dump()
    assert "model_version" in health.model_dump()
