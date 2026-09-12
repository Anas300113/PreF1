"""Historical backtesting with leakage-safe predictions.

For every historical race the runner pretends to stand before the race:
features are built only from information available before the race date,
qualifying is *predicted* by the qualifying model (never actual results), and
the Monte Carlo engine produces probabilistic forecasts that are scored
against the actual result. Predictions are additionally compared against
simple, chronologically honest baselines so that ML performance claims are
only made when the model genuinely beats them.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.backtesting.metrics import (
    RaceBacktestResult,
    brier_score_win,
    expected_points_error,
    kendall_tau,
    log_loss_win,
    mean_abs_position_error,
    podium_accuracy,
    rmse_position_error,
    summarize_races,
    top5_accuracy,
    winner_accuracy,
)
from app.config import Settings
from app.backtesting.baseline_comparator import BaselineComparator
from app.models import BacktestRace, BacktestSeason, Race, RaceResult
from app.services.prediction_service import PredictionService
from app.utils.logging_config import get_logger

logger = get_logger("backtest_runner")


class BacktestRunner:
    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        n_simulations: int = 5000,
        seed: int = 42,
    ):
        self.db = db
        self.settings = settings
        self.n_simulations = n_simulations
        self.seed = seed
        self.service = PredictionService(db, settings)

    async def season_races(self, season: int) -> list[Race]:
        stmt = (
            select(Race)
            .options(selectinload(Race.circuit))
            .where(Race.season_year == season, Race.status == "completed")
            .order_by(Race.round_number)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def run_season(self, season: int) -> dict[str, Any] | None:
        """Backtest every completed race of a season; persist and return summary."""
        races = await self.season_races(season)
        if not races:
            logger.warning("No completed races found for season", season=season)
            return None

        results: list[RaceBacktestResult] = []
        per_race_baselines: list[dict[str, dict[str, float]]] = []
        skipped = 0

        for race in races:
            try:
                race_result, baselines = await self.run_single_race(race.id)
            except Exception as exc:
                skipped += 1
                logger.warning("Backtest race skipped", race=race.id, error=str(exc))
                continue
            results.append(race_result)
            per_race_baselines.append(baselines)

        if not results:
            logger.warning("All races failed backtest for season", season=season)
            return None

        summary = summarize_races(results)
        baseline_summaries = self._summarize_baselines(per_race_baselines)
        record = await self._persist(
            season, summary, baseline_summaries, results, per_race_baselines
        )
        logger.info(
            "Season backtest complete",
            season=season,
            races=summary["n_races"],
            skipped=skipped,
            winner_acc=summary["winner_accuracy"],
        )
        return record

    # ------------------------------------------------------------------
    # Single race
    # ------------------------------------------------------------------
    async def run_single_race(
        self, race_id: str
    ) -> tuple[RaceBacktestResult, dict[str, dict[str, float]]]:
        prediction = await self.service.generate_prediction(
            race_id,
            simulation_count=self.n_simulations,
            seed=self.seed,
            persist=False,
            use_live_weather=False,
        )
        if prediction.get("data_status") != "ok":
            raise ValueError(
                f"Prediction unavailable for {race_id}: {prediction.get('disclaimer')}"
            )

        drivers = prediction["drivers"]
        if len(drivers) < 10:
            raise ValueError(f"Too few drivers predicted for {race_id} ({len(drivers)})")

        ranked = sorted(drivers, key=lambda d: d["expected_position"])
        predictions = [
            {"driver_id": d["driver_id"], "predicted_position": i + 1}
            for i, d in enumerate(ranked)
        ]
        win_probs = {d["driver_id"]: d["win_probability"] for d in drivers}
        exp_points = {d["driver_id"]: d["expected_points"] for d in drivers}

        actuals_rows = (
            (await self.db.execute(select(RaceResult).where(RaceResult.race_id == race_id)))
            .scalars().all()
        )
        if len(actuals_rows) < 10:
            raise ValueError(f"Too few actual results stored for {race_id} ({len(actuals_rows)})")
        actuals = [
            {
                "driver_id": r.driver_id,
                "finish_position": r.finish_position if r.finish_position is not None else 99,
                "points": float(r.points or 0.0),
            }
            for r in actuals_rows
        ]
        actual_winner = min(actuals, key=lambda x: x["finish_position"])["driver_id"]
        actual_points = {a["driver_id"]: a["points"] for a in actuals}
        driver_ids = [p["driver_id"] for p in predictions]

        race = prediction["race"]
        baselines: dict[str, dict[str, float]] = {}

        standings_preds = await self._standings_baseline(race, driver_ids)
        if standings_preds:
            baselines["championship_standings"] = self._baseline_metrics(standings_preds, actuals)
        prev_preds = await self._previous_race_baseline(race, driver_ids)
        if prev_preds:
            baselines["previous_race_order"] = self._baseline_metrics(prev_preds, actuals)
        rolling_preds = await self._rolling_form_baseline(race_id, driver_ids)
        if rolling_preds:
            baselines["rolling_form"] = self._baseline_metrics(rolling_preds, actuals)

        model_winner_correct = winner_accuracy(predictions, actuals) == 1.0
        standings_winner_correct = baselines.get("championship_standings", {}).get(
            "winner_accuracy", 0.0
        ) == 1.0

        result = RaceBacktestResult(
            race_id=race_id,
            race_name=race.name,
            race_date=race.race_date or date(1970, 1, 1),
            winner_correct=model_winner_correct,
            podium_accuracy=podium_accuracy(predictions, actuals),
            top5_accuracy=top5_accuracy(predictions, actuals),
            mae_position=mean_abs_position_error(predictions, actuals),
            rmse_position=rmse_position_error(predictions, actuals),
            brier_score_win=brier_score_win(win_probs, actual_winner),
            log_loss_win=log_loss_win(win_probs, actual_winner),
            kendall_tau=kendall_tau(predictions, actuals),
            expected_points_error=expected_points_error(exp_points, actual_points),
            n_drivers=len(predictions),
            vs_baseline_winner=model_winner_correct and not standings_winner_correct,
        )
        return result, baselines

    # ------------------------------------------------------------------
    # Chronologically honest baselines
    # ------------------------------------------------------------------
    async def _standings_baseline(self, race: Race, driver_ids: list[str]) -> list[dict]:
        """Championship standings known before the race: points scored in
        earlier races of the same season (never the race being predicted)."""
        stmt = (
            select(RaceResult.driver_id, RaceResult.points)
            .join(Race, RaceResult.race_id == Race.id)
            .where(Race.season_year == race.season_year, Race.race_date < race.race_date)
        )
        points: dict[str, float] = {}
        for d_id, pts in (await self.db.execute(stmt)):
            points[d_id] = points.get(d_id, 0.0) + float(pts or 0.0)
        order = sorted(driver_ids, key=lambda d: (-points.get(d, 0.0), d))
        return [{"driver_id": d, "predicted_position": i + 1} for i, d in enumerate(order)]

    async def _previous_race_baseline(self, race: Race, driver_ids: list[str]) -> list[dict]:
        """Order drivers by the immediately preceding race's finishing order."""
        prev_stmt = (
            select(Race.id)
            .where(
                Race.season_year == race.season_year,
                Race.status == "completed",
                Race.race_date < race.race_date,
            )
            .order_by(Race.race_date.desc())
            .limit(1)
        )
        prev_id = (await self.db.execute(prev_stmt)).scalar_one_or_none()
        if prev_id is None:
            return []
        rows_stmt = (
            select(RaceResult.driver_id, RaceResult.finish_position)
            .where(RaceResult.race_id == prev_id)
            .order_by(RaceResult.finish_position.asc().nullslast())
        )
        prev_order = [d for d, _ in (await self.db.execute(rows_stmt)).all() if d]
        ordered = [d for d in prev_order if d in driver_ids]
        ordered += [d for d in driver_ids if d not in ordered]
        return [{"driver_id": d, "predicted_position": i + 1} for i, d in enumerate(ordered)]

    async def _rolling_form_baseline(self, race_id: str, driver_ids: list[str]) -> list[dict]:
        """Sort by rolling 5-race average finish (lower = better form)."""
        features, _ = await self.service.feature_builder.build_features(race_id)
        if features.empty:
            return []
        form = dict(zip(features["driver_id"], features["driver_rolling_5_finish"]))
        order = sorted(driver_ids, key=lambda d: (form.get(d, 25.0), d))
        return [{"driver_id": d, "predicted_position": i + 1} for i, d in enumerate(order)]

    @staticmethod
    def _baseline_metrics(predictions: list[dict], actuals: list[dict]) -> dict[str, float]:
        return {
            "winner_accuracy": winner_accuracy(predictions, actuals),
            "podium_accuracy": podium_accuracy(predictions, actuals),
            "top5_accuracy": top5_accuracy(predictions, actuals),
            "mae_position": mean_abs_position_error(predictions, actuals),
            "rmse_position": rmse_position_error(predictions, actuals),
            "kendall_tau": kendall_tau(predictions, actuals),
        }

    @staticmethod
    def _summarize_baselines(
        per_race_baselines: list[dict[str, dict[str, float]]]
    ) -> dict[str, dict[str, float]]:
        summaries: dict[str, dict[str, float]] = {}
        metric_keys = [
            "winner_accuracy", "podium_accuracy", "top5_accuracy",
            "mae_position", "rmse_position", "kendall_tau",
        ]
        for name in ("championship_standings", "previous_race_order", "rolling_form"):
            rows = [b[name] for b in per_race_baselines if name in b]
            if not rows:
                continue
            summaries[name] = {
                key: float(sum(r[key] for r in rows) / len(rows)) for key in metric_keys
            }
            summaries[name]["n_races"] = len(rows)
        return summaries

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @staticmethod
    def _race_metrics_dict(r: RaceBacktestResult) -> dict[str, Any]:
        return {
            "race_id": r.race_id,
            "race_name": r.race_name,
            "race_date": r.race_date.isoformat() if r.race_date else None,
            "winner_correct": bool(r.winner_correct),
            "podium_accuracy": r.podium_accuracy,
            "top5_accuracy": r.top5_accuracy,
            "mae_position": r.mae_position,
            "rmse_position": r.rmse_position,
            "brier_score_win": r.brier_score_win,
            "log_loss_win": r.log_loss_win,
            "kendall_tau": r.kendall_tau,
            "expected_points_error": r.expected_points_error,
            "n_drivers": r.n_drivers,
            "vs_baseline_winner": bool(r.vs_baseline_winner),
        }

    async def _persist(
        self,
        season: int,
        summary: dict[str, Any],
        baseline_summaries: dict[str, dict[str, float]],
        results: list[RaceBacktestResult],
        per_race_baselines: list[dict[str, dict[str, float]]],
    ) -> dict[str, Any]:
        training_cutoff = self.service._training_cutoff_metadata()
        season_rec = BacktestSeason(
            id=str(uuid.uuid4()),
            season=season,
            model_version=self.settings.model_version,
            training_cutoff=training_cutoff,
            n_races=summary["n_races"],
            n_simulations=self.n_simulations,
            simulation_seed=self.seed,
            model_metrics=json.dumps(summary),
            baseline_metrics=json.dumps(baseline_summaries),
        )
        self.db.add(season_rec)

        for race_result, baselines in zip(results, per_race_baselines):
            self.db.add(
                BacktestRace(
                    id=str(uuid.uuid4()),
                    backtest_season_id=season_rec.id,
                    race_id=race_result.race_id,
                    race_name=race_result.race_name,
                    race_date=datetime.combine(race_result.race_date, datetime.min.time()),
                    model_metrics=json.dumps(self._race_metrics_dict(race_result)),
                    baselines=json.dumps(baselines),
                )
            )
        try:
            await self.db.commit()
        except Exception as exc:
            await self.db.rollback()
            logger.warning("Failed to persist backtest results", error=str(exc))

        comparison = BaselineComparator.compare(summary, baseline_summaries)
        return {
            "season": season,
            "model_version": self.settings.model_version,
            "training_cutoff": training_cutoff,
            "n_simulations": self.n_simulations,
            "simulation_seed": self.seed,
            **summary,
            "baselines": baseline_summaries,
            "comparison": comparison,
        }



