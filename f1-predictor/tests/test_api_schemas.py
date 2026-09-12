from app.schemas.prediction import PredictionResponseSchema, SimulationRequest


def test_simulation_request_defaults():
    req = SimulationRequest()
    assert req.simulation_count == 10000
    assert req.seed == 42


def test_prediction_response_schema_optional_fields():
    schema = PredictionResponseSchema.model_json_schema()
    assert "data_status" in schema["properties"]
