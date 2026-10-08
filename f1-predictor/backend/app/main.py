from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.ml.model_registry import ModelRegistry
from app.utils.logging_config import setup_logging
from app.api.routes import health, races, drivers, teams, backtests, models_route, seasons, explain, championship, openf1

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger("pref1.startup")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()

    # Verify model artifacts.  Missing/corrupt artifacts must never silently
    # downgrade predictions to heuristics: fail closed when configured, and
    # otherwise attach the verification status to app.state so /api/health
    # and prediction responses can surface "MODEL UNAVAILABLE".
    registry = ModelRegistry(settings.models_dir)
    model_status = registry.load_status(settings.required_model_list())
    app.state.model_status = model_status
    if not model_status["all_available"]:
        missing = [
            key for key, info in model_status["models"].items()
            if not info["available"]
        ]
        if settings.require_trained_models:
            raise RuntimeError(
                "MODEL UNAVAILABLE — required model artifacts failed verification: "
                f"{missing}. Run scripts/train_models.py or set "
                "REQUIRE_TRAINED_MODELS=false to start in degraded mode."
            )
        logger.error(
            "Model artifacts unavailable (degraded mode — predictions will be "
            "explicitly labelled heuristic): %s",
            missing,
        )
    else:
        logger.info("All required model artifacts verified")
    yield

app = FastAPI(
    title="PreF1 - Formula 1 Race Prediction & Simulation API",
    description="Production-grade probabilistic Formula 1 predictions powered by XGBoost and Monte Carlo simulation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(races.router)
app.include_router(drivers.router)
app.include_router(teams.router)
app.include_router(backtests.router)
app.include_router(models_route.router)
app.include_router(seasons.router)
app.include_router(explain.router)
app.include_router(championship.router)
app.include_router(openf1.router)

@app.get("/")
async def root():
    return {"message": "PreF1 API is running", "docs": "/docs"}
