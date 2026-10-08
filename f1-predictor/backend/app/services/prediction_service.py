"""Orchestrates feature building, ML models, weather, and Monte Carlo simulation."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.explainability.factor_summary import generate_explanation
from app.features.race_feature_builder import RaceFeatureBuilder
from app.ml.baseline_model import BaselineModel
from app.ml.dnf_model import DNFModel
from app.ml.model_registry import ModelRegistry
from app.ml.qualifying_model import QualifyingModel
from app.ml.race_pace_model import RacePaceModel
from app.models import Prediction
from app.services.weather_client import OpenMeteoClient
from app.simulation.monte_carlo import MonteCarloEngine
from app.simulation.race_simulator import DriverSimInput, RaceSimulator
from app.simulation.strategy_engine import StrategyEngine
from app.ml.tyre_model import TyreModel
from app.utils.circuit_profiles import get_circuit_profile
from app.utils.logging_config import get_logger
from app.utils.team_colors import team_color

logger = get_logger("prediction_service")

SCENARIO_SAFETY_CAR = {"low": 0.20, "normal": 0.50, "high": 0.75}
SCENARIO_TYRE_DEG = {"low": 0.3, "normal": 0.5, "high": 0.8}


class PredictionService:
    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self.feature_builder = RaceFeatureBuilder(db)
        self.registry = ModelRegistry(settings.models_dir)
        self.baseline = BaselineModel()

    async def generate_prediction(
        self,
        race_id: str,
        simulation_count: int = 10000,
        seed: int = 42,
        weather_override: str | None = None,
        safety_car_override: str | None = None,
        tyre_deg_override: str | None = None,
        persist: bool = True,
        use_live_weather: bool = True,
    ) -> dict[str, Any]:
        simulation_count = min(simulation_count, self.settings.simulation_max_count)

        weather_feats_override = self._weather_override_features(weather_override)
        features, race = await self.feature_builder.build_features(
            race_id, weather_override=weather_feats_override
        )

        if race is None:
            raise ValueError(f"Race {race_id} not found")

        if features.empty:
            return self._unavailable_response(race, "No driver entries found. Run data ingestion first.")

        if use_live_weather:
            weather = await self._fetch_weather(race, weather_override)
        else:
            # Backtesting mode: never consult live forecast services for a
            # historical race (and observed race-day weather would leak future
            # information anyway). Weather is treated as neutral/dry.
            weather = {
                "source": "not_used_in_backtest",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "temperature_c": None,
                "precipitation_probability": None,
                "precipitation_mm": None,
                "wind_speed_ms": None,
                "cloud_cover_pct": None,
                "humidity_pct": None,
                "is_wet": False,
                "weather_code": None,
            }
        is_wet = weather.get("is_wet", False)

        quali_model, pace_model, dnf_model, model_provenance = self._load_models()
        quali_preds = self._predict_qualifying(features, quali_model)
        pace_preds = self._predict_race_pace(features, pace_model, quali_preds)
        dnf_probs = self._predict_dnf(features, dnf_model)

        circuit_profile = get_circuit_profile(race.circuit_id)
        deg_index = circuit_profile.get("tyre_degradation_index", 0.5)
        if tyre_deg_override:
            deg_index = SCENARIO_TYRE_DEG.get(tyre_deg_override, deg_index)

        sc_prob = SCENARIO_SAFETY_CAR.get(safety_car_override or "normal", 0.50)

        tyre_m = TyreModel()
        strat_e = StrategyEngine(tyre_m)
        sim_engine = RaceSimulator(strat_e, pit_loss_seconds=circuit_profile.get("pit_loss_seconds", 22.0))
        mc = MonteCarloEngine(sim_engine)

        race_laps = race.total_laps or 58
        driver_inputs = self._build_sim_inputs(
            features, quali_preds, pace_preds, dnf_probs, strat_e, race_laps,
            is_wet, deg_index
        )

        mc_result = mc.run(
            driver_inputs,
            race_laps=race_laps,
            is_wet=is_wet,
            circuit_deg_index=deg_index,
            n_simulations=simulation_count,
            seed=seed,
            safety_car_prob=sc_prob,
        )

        # Pairwise finishing probability matrix (D×D)
        pairwise_matrix: dict[str, dict[str, float]] = {}
        for i, di in enumerate(driver_inputs):
            pairwise_matrix[di.driver_id] = {}
            for j, dj in enumerate(driver_inputs):
                pairwise_matrix[di.driver_id][dj.driver_id] = round(
                    float(mc_result.pairwise_finish_matrix[i][j]), 4
                )

        shap_map = {}
        if quali_model.is_trained:
            try:
                shap_map = quali_model.get_shap_values(features)
            except Exception as exc:
                logger.warning("SHAP computation failed", error=str(exc))

        driver_preds, quali_grid, explanations = self._format_results(
            features, quali_preds, mc_result, shap_map
        )

        training_cutoff = self._training_cutoff_metadata()
        created_at = datetime.now(timezone.utc)

        # Honest model provenance: users must be able to tell an ML forecast
        # from a heuristic one (Principle: never claim ML when heuristic).
        ml_backends = [p["backend"] for p in model_provenance.values()]
        if all(b == "xgboost" for b in ml_backends):
            inference_backend = "xgboost"
        elif any(b == "xgboost" for b in ml_backends):
            inference_backend = "mixed"
        else:
            inference_backend = "heuristic"

        # Prediction cutoff: no feature used by this prediction may originate
        # after the race's own date (feature builder enforces race_date <
        # cutoff for historical features; weekend features are pre-race).
        data_cutoff = (
            race.race_date.isoformat() if race.race_date else created_at.date().isoformat()
        )

        response = {
            "race": race,
            "model": {
                "version": self.settings.model_version,
                "training_cutoff": training_cutoff,
                "simulation_count": simulation_count,
                "simulation_seed": seed,
                "feature_version": self.settings.feature_version,
                "created_at": created_at.isoformat(),
                "prediction_cutoff_timestamp": data_cutoff,
                "runtime_seconds": mc_result.runtime_seconds,
                "inference_backend": inference_backend,
                "components": model_provenance,
                "model_unavailable": inference_backend == "heuristic",
            },
            "drivers": driver_preds,
            "qualifying_prediction": quali_grid,
            "weather": weather,
            "explanations": explanations,
            "scenarios": {
                "weather": weather_override or "forecast",
                "safety_car": safety_car_override or "normal",
                "tyre_deg": tyre_deg_override or "normal",
            },
            "disclaimer": (
                "These are probabilistic forecasts, not deterministic claims. "
                "Actual race outcomes depend on unpredictable factors."
            ),
            "data_status": "ok",
            "pairwise_finish_matrix": pairwise_matrix,
            "convergence_report": mc_result.convergence_report,
        }

        if persist:
            await self._persist_prediction(race_id, response, seed, simulation_count, created_at)

        return response

    def _load_models(
        self,
    ) -> tuple[QualifyingModel, RacePaceModel, DNFModel, dict[str, Any]]:
        """Load registered model artifacts and report provenance per model.

        Returns (quali, pace, dnf, provenance) where provenance maps each
        model type to {"backend": "xgboost"|"heuristic", "version": ...}.
        Heuristic fallback is NEVER silent — the caller must surface it.
        """
        quali = QualifyingModel()
        pace = RacePaceModel()
        dnf = DNFModel()
        provenance: dict[str, Any] = {}

        registry_models = {
            "qualifying": quali,
            "race_pace": pace,
            "dnf": dnf,
        }
        required = {
            entry["model_type"]: entry["version"]
            for entry in self.settings.required_model_list()
            if entry["model_type"] in registry_models
        }

        for model_type, target in registry_models.items():
            version = required.get(model_type, "v1.0")
            status = self.registry.verify(model_type, version)
            provenance[model_type] = {
                "version": version,
                "backend": "heuristic",
                "artifact_available": status.available,
                "checksum_ok": status.checksum_ok,
                "training_data_cutoff": status.metadata.get("training_data_cutoff"),
                "error": status.error,
            }
            if not status.available:
                logger.warning(
                    "Model artifact unavailable — heuristic fallback in use",
                    model=model_type,
                    version=version,
                    error=status.error,
                )
                continue
            try:
                loaded = type(target).load(str(self.registry.artifact_path(model_type, version)))
            except Exception as exc:
                logger.warning("Failed to load model", model=model_type, error=str(exc))
                provenance[model_type][
                    "error"
                ] = f"load_failed: {exc}"
                continue
            # Refuse to treat a load as "trained" unless the estimator actually
            # carries a fitted booster.  load() historically forced
            # is_trained=True, which would otherwise silently present a
            # never-trained artefact as an ML prediction.
            if not (loaded.is_trained and getattr(loaded, "model", None) is not None):
                logger.warning(
                    "Loaded model has no fitted booster — heuristic fallback in use",
                    model=model_type,
                    error="unfitted_artifact",
                )
                provenance[model_type][
                    "error"
                ] = "unfitted_artifact"
                continue
            if model_type == "qualifying":
                quali = loaded
            elif model_type == "race_pace":
                pace = loaded
            else:
                dnf = loaded
            provenance[model_type][
                "backend"
            ] = "xgboost"
        return quali, pace, dnf, provenance

    def _predict_qualifying(self, features: pd.DataFrame, model: QualifyingModel) -> pd.DataFrame:
        if model.is_trained:
            gaps = model.predict(features)
        else:
            gaps = features["driver_rolling_5_finish"].values * 0.05 + features["team_quali_pace_vs_field"].values
        df = features.copy()
        df["predicted_gap_to_pole"] = gaps
        df["predicted_quali_position"] = np.argsort(np.argsort(gaps)) + 1
        return df.sort_values("predicted_quali_position")

    def _predict_race_pace(self, features: pd.DataFrame, model: RacePaceModel, quali: pd.DataFrame) -> pd.DataFrame:
        """Predict race pace with train/serve-consistent qualifying inputs.

        The race-pace model was trained with OBSERVED qualifying values
        (training_data_builder injects actual quali gap/position).  At serve
        time we therefore keep observed qualifying wherever it exists and
        only substitute the qualifying model's prediction before qualifying
        has been held ('pre-qualifying' prediction mode).
        """
        merged = features.merge(
            quali[["driver_id", "predicted_gap_to_pole", "predicted_quali_position"]],
            on="driver_id",
            how="left",
        )
        observed = merged.get("quali_observed", pd.Series(0.0, index=merged.index)).fillna(0.0) == 1.0
        # Observed where available; predicted only for pre-qualifying rows.
        merged["quali_gap_to_pole"] = np.where(
            observed, merged["quali_gap_to_pole"], merged["predicted_gap_to_pole"]
        )
        merged["quali_position"] = np.where(
            observed, merged["quali_position"], merged["predicted_quali_position"]
        )
        merged["qualifying_mode"] = np.where(observed, "post_qualifying", "pre_qualifying")

        if model.is_trained:
            pace = model.predict(merged)
        else:
            pace = merged["driver_rolling_5_finish"].values * 0.08 + merged["predicted_gap_to_pole"].values * 0.5

        merged["predicted_race_pace_delta"] = pace
        return merged

    def _predict_dnf(self, features: pd.DataFrame, model: DNFModel) -> np.ndarray:
        if model.is_trained:
            return np.clip(model.predict_proba(features), 0.02, 0.35)
        return np.clip(features["driver_dnf_rate_10"].values, 0.05, 0.25)

    def _build_sim_inputs(
        self,
        features: pd.DataFrame,
        quali: pd.DataFrame,
        pace: pd.DataFrame,
        dnf_probs: np.ndarray,
        strat_e: StrategyEngine,
        race_laps: int,
        is_wet: bool,
        circuit_deg_index: float,
    ) -> list[DriverSimInput]:
        quali_map = quali.set_index("driver_id")
        pace_map = pace.set_index("driver_id")
        inputs: list[DriverSimInput] = []

        driver_ids = list(features["driver_id"])
        for i, (_, row) in enumerate(features.iterrows()):
            d_id = row["driver_id"]
            q_row = quali_map.loc[d_id]
            p_row = pace_map.loc[d_id]

            # The pace model outputs a position-scale score (lower = better).
            # The simulator expects a per-lap TIME delta in seconds: convert
            # relative to the field median using an empirically calibrated
            # ~0.12 s/lap per pace position (F1 field spread ≈ 2.5 s/lap).
            pace_score = float(p_row["predicted_race_pace_delta"])
            field_median = float(np.nanmedian(pace["predicted_race_pace_delta"].values))
            base_pace = (pace_score - field_median) * 0.12

            # Prefer the OBSERVED qualifying position (official grid prior)
            # when qualifying has been held; otherwise the model's prediction.
            if q_row.get("quali_observed", 0.0) == 1.0 and not pd.isna(q_row.get("quali_position")):
                quali_pos = int(q_row["quali_position"])
                quali_pace = float(q_row.get("quali_gap_to_pole", 0.0) or 0.0)
            else:
                quali_pos = int(q_row["predicted_quali_position"])
                quali_pace = float(q_row["predicted_gap_to_pole"])
            wet_skill = -0.15 if row.get("driver_circuit_avg_finish", 10) < 5 else 0.0

            strats = strat_e.generate_candidate_strategies(
                race_laps, circuit_deg_index=circuit_deg_index, is_wet=is_wet
            )
            inputs.append(
                DriverSimInput(
                    driver_id=d_id,
                    team_id=row["team_id"],
                    base_pace_delta=base_pace,
                    dnf_probability=float(dnf_probs[i]),
                    qualifying_position=quali_pos,
                    qualifying_pace_delta=quali_pace,
                    wet_skill_delta=wet_skill if is_wet else 0.0,
                    strategies=strats,
                )
            )
        return inputs

    def _format_results(
        self,
        features: pd.DataFrame,
        quali: pd.DataFrame,
        mc_result,
        shap_map: dict,
    ) -> tuple[list[dict], list[dict], dict]:
        driver_preds = []
        quali_grid = []
        explanations = {}

        id_to_idx = {d: i for i, d in enumerate(mc_result.driver_ids)}

        for _, row in quali.iterrows():
            d_id = row["driver_id"]
            idx = id_to_idx[d_id]
            pos_dist = {
                str(p + 1): float(mc_result.position_distributions[idx, p])
                for p in range(min(20, mc_result.position_distributions.shape[1]))
            }

            driver_preds.append({
                "driver_id": d_id,
                "code": row["code"],
                "full_name": row["full_name"],
                "team": row["team_name"],
                "team_color": team_color(row["team_id"], row["team_name"]),
                "win_probability": float(mc_result.win_probabilities[idx]),
                "podium_probability": float(mc_result.podium_probabilities[idx]),
                "top5_probability": float(mc_result.top5_probabilities[idx]),
                "top10_probability": float(mc_result.top10_probabilities[idx]),
                "points_probability": float(mc_result.points_probabilities[idx]),
                "dnf_probability": float(mc_result.dnf_probabilities[idx]),
                "expected_position": float(mc_result.expected_positions[idx]),
                "median_position": float(mc_result.median_positions[idx]),
                "p10_position": float(mc_result.p10_positions[idx]),
                "p25_position": float(mc_result.p25_positions[idx]),
                "p75_position": float(mc_result.p75_positions[idx]),
                "p90_position": float(mc_result.p90_positions[idx]),
                "expected_points": float(mc_result.expected_points[idx]),
                "position_distribution": pos_dist,
            })

            quali_grid.append({
                "driver_id": d_id,
                "code": row["code"],
                "expected_position": int(row["predicted_quali_position"]),
            })

            shap_vals = shap_map.get(d_id, {
                "driver_rolling_3_finish": float(row.get("driver_rolling_3_finish", 10)),
                "driver_quali_vs_teammate_3": float(row.get("driver_quali_vs_teammate_3", 0)),
                "team_quali_pace_vs_field": float(row.get("team_quali_pace_vs_field", 0.5)),
            })
            explanations[d_id] = generate_explanation(d_id, shap_vals)

        return driver_preds, quali_grid, explanations

    async def _fetch_weather(self, race, weather_override: str | None) -> dict[str, Any]:
        circuit = race.circuit
        now = datetime.now(timezone.utc)

        if weather_override == "wet":
            return {
                "source": "scenario_override",
                "retrieved_at": now.isoformat(),
                "temperature_c": 18.0,
                "precipitation_probability": 85.0,
                "precipitation_mm": 2.5,
                "wind_speed_ms": 6.0,
                "cloud_cover_pct": 90.0,
                "humidity_pct": 80.0,
                "is_wet": True,
                "weather_code": 61,
            }
        if weather_override == "mixed":
            return {
                "source": "scenario_override",
                "retrieved_at": now.isoformat(),
                "temperature_c": 20.0,
                "precipitation_probability": 45.0,
                "precipitation_mm": 0.2,
                "wind_speed_ms": 5.0,
                "cloud_cover_pct": 60.0,
                "humidity_pct": 65.0,
                "is_wet": False,
                "weather_code": 3,
            }
        if weather_override == "dry":
            return {
                "source": "scenario_override",
                "retrieved_at": now.isoformat(),
                "temperature_c": 24.0,
                "precipitation_probability": 5.0,
                "precipitation_mm": 0.0,
                "wind_speed_ms": 4.0,
                "cloud_cover_pct": 15.0,
                "humidity_pct": 50.0,
                "is_wet": False,
                "weather_code": 1,
            }

        if not circuit or circuit.latitude is None or circuit.longitude is None:
            return {
                "source": "unavailable",
                "retrieved_at": now.isoformat(),
                "temperature_c": None,
                "precipitation_probability": None,
                "precipitation_mm": None,
                "wind_speed_ms": None,
                "cloud_cover_pct": None,
                "humidity_pct": None,
                "is_wet": False,
                "weather_code": None,
            }

        race_date = race.race_date or now.date()
        client = OpenMeteoClient()
        try:
            obs_list = await client.get_forecast(
                circuit.latitude, circuit.longitude, race_date, race_date
            )
            if obs_list:
                # Use midday-ish observation or first available
                obs = obs_list[len(obs_list) // 2] if len(obs_list) > 1 else obs_list[0]
                return {
                    "source": obs.get("source", "open_meteo_forecast"),
                    "retrieved_at": obs.get("source_retrieved_at", now.isoformat()),
                    "temperature_c": obs.get("temperature_c"),
                    "precipitation_probability": obs.get("precipitation_probability"),
                    "precipitation_mm": obs.get("precipitation_mm"),
                    "wind_speed_ms": obs.get("wind_speed_ms"),
                    "cloud_cover_pct": obs.get("cloud_cover_pct"),
                    "humidity_pct": obs.get("humidity_pct"),
                    "is_wet": bool(obs.get("is_wet", False)),
                    "weather_code": obs.get("weather_code"),
                }
        finally:
            await client.close()

        # No forecast data available.  NEVER fabricate plausible-looking
        # weather — return nulls explicitly labelled as an assumption so the
        # UI can distinguish missing data from observed/forecast data.
        return {
            "source": "assumed_dry_no_forecast",
            "retrieved_at": now.isoformat(),
            "temperature_c": None,
            "precipitation_probability": None,
            "precipitation_mm": None,
            "wind_speed_ms": None,
            "cloud_cover_pct": None,
            "humidity_pct": None,
            "is_wet": False,
            "weather_code": None,
            "note": "ASSUMED: no forecast available; simulation assumes dry conditions.",
        }

    @staticmethod
    def _weather_override_features(override: str | None) -> dict[str, Any] | None:
        if override == "wet":
            return {"weather_is_wet": True, "weather_race_temp_c": 18.0}
        if override == "mixed":
            return {"weather_is_wet": False, "weather_race_temp_c": 20.0}
        if override == "dry":
            return {"weather_is_wet": False, "weather_race_temp_c": 24.0}
        return None

    def _training_cutoff_metadata(self) -> str:
        meta = self.registry.get_metadata("qualifying", "v1.0")
        if meta and "training_cutoff" in meta:
            return meta["training_cutoff"]
        return "2024-12-01T00:00:00Z"

    async def _persist_prediction(
        self, race_id: str, response: dict, seed: int, sim_count: int, created_at: datetime
    ) -> None:
        pred = Prediction(
            id=str(uuid.uuid4()),
            race_id=race_id,
            snapshot_type="pre_race",
            model_version=self.settings.model_version,
            feature_version=self.settings.feature_version,
            training_cutoff=response["model"]["training_cutoff"],
            simulation_seed=seed,
            simulation_count=sim_count,
            created_at=created_at,
            payload=json.dumps({"model": response["model"], "scenarios": response.get("scenarios")}),
        )
        self.db.add(pred)
        try:
            await self.db.commit()
        except Exception as exc:
            logger.warning("Failed to persist prediction", error=str(exc))
            await self.db.rollback()

    @staticmethod
    def _unavailable_response(race, reason: str) -> dict[str, Any]:
        return {
            "race": race,
            "model": {
                "version": "unavailable",
                "training_cutoff": "",
                "simulation_count": 0,
                "simulation_seed": 0,
                "feature_version": "",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "drivers": [],
            "qualifying_prediction": [],
            "weather": {"source": "unavailable", "retrieved_at": datetime.now(timezone.utc).isoformat()},
            "explanations": {},
            "disclaimer": reason,
            "data_status": "unavailable",
        }
