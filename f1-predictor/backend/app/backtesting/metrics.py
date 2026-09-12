"""Backtesting metrics.

All functions are pure and unit-testable. Predictions are expressed either as
deterministic rankings (``predicted_position``) or as probabilistic forecasts
(``win_probability`` etc. produced by the Monte Carlo engine).
"""
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any
import math
import numpy as np

LOG_LOSS_EPSILON = 1e-6


@dataclass
class RaceBacktestResult:
    race_id: str
    race_name: str
    race_date: date
    winner_correct: bool
    podium_accuracy: float
    top5_accuracy: float
    mae_position: float
    rmse_position: float
    brier_score_win: float
    log_loss_win: float
    kendall_tau: float
    expected_points_error: float
    n_drivers: int = 0
    vs_baseline_winner: bool = False


def _sorted_by_pred(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(predictions, key=lambda x: x.get("predicted_position", 99))


def winner_accuracy(predictions: List[Dict[str, Any]], actuals: List[Dict[str, Any]]) -> float:
    if not predictions or not actuals:
        return 0.0
    pred_p1 = min(predictions, key=lambda x: x.get("predicted_position", 99))
    act_p1 = min(actuals, key=lambda x: x.get("finish_position", 99))
    return 1.0 if pred_p1["driver_id"] == act_p1["driver_id"] else 0.0


def podium_accuracy(predictions: List[Dict[str, Any]], actuals: List[Dict[str, Any]]) -> float:
    if not predictions or not actuals:
        return 0.0
    pred_top3 = {x["driver_id"] for x in _sorted_by_pred(predictions)[:3]}
    act_top3 = {x["driver_id"] for x in sorted(actuals, key=lambda x: x.get("finish_position", 99))[:3]}
    return len(pred_top3.intersection(act_top3)) / 3.0


def top5_accuracy(predictions: List[Dict[str, Any]], actuals: List[Dict[str, Any]]) -> float:
    if not predictions or not actuals:
        return 0.0
    pred_top5 = {x["driver_id"] for x in _sorted_by_pred(predictions)[:5]}
    act_top5 = {x["driver_id"] for x in sorted(actuals, key=lambda x: x.get("finish_position", 99))[:5]}
    return len(pred_top5.intersection(act_top5)) / 5.0


def _position_errors(predictions: List[Dict[str, Any]], actuals: List[Dict[str, Any]]) -> List[float]:
    if not predictions or not actuals:
        return []
    act_map = {x["driver_id"]: x.get("finish_position", 20) for x in actuals}
    errors = []
    for p in predictions:
        d_id = p["driver_id"]
        if d_id in act_map:
            errors.append(abs(p.get("predicted_position", 10) - act_map[d_id]))
    return errors


def mean_abs_position_error(predictions: List[Dict[str, Any]], actuals: List[Dict[str, Any]]) -> float:
    errors = _position_errors(predictions, actuals)
    return float(np.mean(errors)) if errors else 0.0


def rmse_position_error(predictions: List[Dict[str, Any]], actuals: List[Dict[str, Any]]) -> float:
    errors = _position_errors(predictions, actuals)
    return float(np.sqrt(np.mean(np.square(errors)))) if errors else 0.0


def kendall_tau(predictions: List[Dict[str, Any]], actuals: List[Dict[str, Any]]) -> float:
    """Kendall rank correlation between predicted and actual ordering."""
    from scipy.stats import kendalltau

    act_map = {x["driver_id"]: x.get("finish_position") for x in actuals}
    pairs = [
        (p.get("predicted_position", 99), act_map[p["driver_id"]])
        for p in predictions
        if p["driver_id"] in act_map and act_map[p["driver_id"]] is not None
    ]
    if len(pairs) < 2:
        return 0.0
    pred_rank, act_rank = zip(*pairs)
    tau, _ = kendalltau(pred_rank, act_rank)
    return float(tau) if tau is not None and not math.isnan(tau) else 0.0


def brier_score_win(win_probabilities: Dict[str, float], actual_winner_id: str) -> float:
    """Multi-class Brier score for the win event.

    Mean over drivers of (p_win(driver) - 1{driver won})^2. Ranges 0..2 for
    multi-class events; lower is better, 1/D for a uniform guess.
    """
    if not win_probabilities:
        return 1.0
    terms = [
        (float(p) - (1.0 if d == actual_winner_id else 0.0)) ** 2
        for d, p in win_probabilities.items()
    ]
    return float(np.mean(terms))


def log_loss_win(win_probabilities: Dict[str, float], actual_winner_id: str) -> float:
    """Cross-entropy loss of the actual winner's predicted win probability."""
    p = float(win_probabilities.get(actual_winner_id, 0.0))
    p = min(max(p, LOG_LOSS_EPSILON), 1.0)
    return float(-math.log(p))


def expected_points_error(
    predicted_points: Dict[str, float], actual_points: Dict[str, float]
) -> float:
    """Mean absolute error between predicted expected points and actual points."""
    common = [d for d in predicted_points if d in actual_points]
    if not common:
        return 0.0
    errors = [abs(float(predicted_points[d]) - float(actual_points[d])) for d in common]
    return float(np.mean(errors))


def summarize_races(results: List[RaceBacktestResult]) -> Dict[str, Any]:
    """Aggregate per-race backtest results into season-level metrics."""
    n = len(results)
    if n == 0:
        return {
            "n_races": 0, "winner_accuracy": 0.0, "podium_accuracy": 0.0,
            "top5_accuracy": 0.0, "mean_abs_position_error": 0.0,
            "rmse_position_error": 0.0, "brier_score_win": 0.0,
            "log_loss_win": 0.0, "kendall_tau": 0.0, "expected_points_error": 0.0,
        }
    return {
        "n_races": n,
        "winner_accuracy": float(np.mean([r.winner_correct for r in results])),
        "podium_accuracy": float(np.mean([r.podium_accuracy for r in results])),
        "top5_accuracy": float(np.mean([r.top5_accuracy for r in results])),
        "mean_abs_position_error": float(np.mean([r.mae_position for r in results])),
        "rmse_position_error": float(np.mean([r.rmse_position for r in results])),
        "brier_score_win": float(np.mean([r.brier_score_win for r in results])),
        "log_loss_win": float(np.mean([r.log_loss_win for r in results])),
        "kendall_tau": float(np.mean([r.kendall_tau for r in results])),
        "expected_points_error": float(np.mean([r.expected_points_error for r in results])),
    }
