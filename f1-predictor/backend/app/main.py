from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.utils.logging_config import setup_logging
from app.api.routes import health, races, drivers, teams, backtests, models_route, seasons, explain

settings = get_settings()
setup_logging(settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
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

@app.get("/")
async def root():
    return {"message": "PreF1 API is running", "docs": "/docs"}
