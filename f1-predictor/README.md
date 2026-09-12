# PreF1 — Formula 1 Race Prediction & Simulation Platform

Production-grade probabilistic F1 forecasting using a modular ML pipeline and vectorised Monte Carlo race simulation.

## Architecture

```
Jolpica / Open-Meteo / FastF1
        ↓
   Ingestion Layer → SQLite (PostgreSQL-ready)
        ↓
   Feature Engineering (leakage-safe, chronological)
        ↓
   Qualifying Model (XGBoost) → Race Pace Model → DNF Model → Tyre Model
        ↓
   Strategy Engine → Monte Carlo Simulator (10k–500k sims)
        ↓
   FastAPI → React Dashboard
```

**Important:** Predictions are probabilistic forecasts, not deterministic claims.

## Quick Start

### 1. Backend

```bash
cd f1-predictor
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Ingest historical data (2018–2026, ~15 min first run; Jolpica rate limits apply)
python scripts/ingest_historical.py --start 2018 --end 2026

# Ingest leakage-safe pre-race weather (Fri/Sat archive, never race-day obs)
python scripts/ingest_weather.py --start 2018 --end 2026

# Train XGBoost models from ingested data
python scripts/train_models.py

# Run the historical backtest (real leakage-safe predictions + honest baselines)
python scripts/run_backtest.py --season 2025

# Benchmark the Monte Carlo engine (10k–500k sims)
python scripts/benchmark_simulation.py

# Start API
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — the Vite dev server proxies `/api` to port 8000.

### 3. Docker (optional)

```bash
docker compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/seasons` | List seasons |
| GET | `/api/races` | List races |
| GET | `/api/races/next` | Next scheduled race |
| GET | `/api/races/{id}/prediction` | Run prediction |
| POST | `/api/races/{id}/simulate` | Scenario simulation |
| GET | `/api/races/{id}/weather` | Race weather forecast |
| GET | `/api/explain/{race_id}/{driver_id}` | SHAP explanations |
| GET | `/api/backtests` | Backtest summaries |
| GET | `/api/models` | Model metadata |

## Data Sources

- **Jolpica F1 API** — results, qualifying, standings, pit stops
- **Open-Meteo** — historical archive + live forecast weather
- **FastF1** — practice/qualifying session timing (optional enrichment)

## Modelling Principles

1. **Modular pipeline** — separate qualifying, race pace, tyre, strategy, incident models
2. **No direct position prediction** — model pace deltas, simulate mechanically
3. **Chronological validation** — never random train/test splits; models train 2018–2024, evaluate out-of-sample
4. **Information cutoff** — features only use data strictly before the race's calendar date
5. **Weather leakage guard** — only pre-race (Fri/Sat) weather may enter features; observed race-day weather never does
6. **Honest backtesting** — `/api/backtests` serves only persisted, reproducible evaluations; if none exist it returns an empty list, never fabricated metrics
7. **Reproducibility** — every prediction stores model version, seed, simulation count

## Project Structure

```
f1-predictor/
├── backend/app/
│   ├── api/routes/       # FastAPI endpoints
│   ├── features/         # Feature engineering
│   ├── ml/               # XGBoost models + training
│   ├── simulation/       # Monte Carlo engine
│   ├── services/         # Jolpica, weather, prediction orchestration
│   └── backtesting/      # Historical evaluation
├── frontend/             # React + Tailwind dashboard
├── scripts/              # Ingestion & training CLIs
├── tests/                # Unit & integration tests
└── data/                 # SQLite DB, caches, raw data
```

## Running Tests

```bash
cd f1-predictor
pytest tests/ -v
```

## Configuration

Environment variables (`.env`):

```
DATABASE_URL=sqlite+aiosqlite:///./data/db/f1_predictor.db
MODEL_VERSION=xgb-mc-v1
SIMULATION_DEFAULT_COUNT=10000
LOG_LEVEL=INFO
```

SQLite is the default; swap `DATABASE_URL` for PostgreSQL when scaling.
