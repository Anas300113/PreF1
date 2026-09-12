"""Tests for backtesting metrics — pure functions, exact expected values."""
from datetime import date

import pytest

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


ACTUALS = [
    {"driver_id": "alice", "finish_position": 1, "points": 25.0},
    {"driver_id": "bob", "finish_position": 2, "points": 18.0},
    {"driver_id": "carol", "finish_position": 3, "points": 15.0},
    {"driver_id": "dave", "finish_position": 4, "points": 12.0},
    {"driver_id": "erin", "finish_position": 5, "points": 10.0},
]


def test_winner_accuracy_perfect_and_wrong():
    preds = [{"driver_id": "alice", "predicted_position": 1},
             {"driver_id": "bob", "predicted_position": 2}]
    assert winner_accuracy(preds, ACTUALS) == 1.0
    preds_wrong = [{"driver_id": "bob", "predicted_position": 1},
                   {"driver_id": "alice", "predicted_position": 2}]
    assert winner_accuracy(preds_wrong, ACTUALS) == 0.0


def test_podium_accuracy_counts_overlap():
    preds = [{"driver_id": "alice", "predicted_position": 1},
             {"driver_id": "bob", "predicted_position": 2},
             {"driver_id": "zed", "predicted_position": 3}]
    # alice & bob in actual podium, zed is not → 2/3
    assert podium_accuracy(preds, ACTUALS) == pytest.approx(2 / 3)


def test_top5_accuracy_counts_overlap():
    preds = [
        {"driver_id": "alice", "predicted_position": 1},
        {"driver_id": "bob", "predicted_position": 2},
        {"driver_id": "carol", "predicted_position": 3},
        {"driver_id": "dave", "predicted_position": 4},
        {"driver_id": "zed", "predicted_position": 5},
    ]
    assert top5_accuracy(preds, ACTUALS) == pytest.approx(4 / 5)


def test_mae_and_rmse():
    preds = [{"driver_id": "alice", "predicted_position": 1},
             {"driver_id": "bob", "predicted_position": 2},
             {"driver_id": "carol", "predicted_position": 5},
             {"driver_id": "dave", "predicted_position": 4},
             {"driver_id": "erin", "predicted_position": 8}]
    # |errors| = 0, 0, 2, 0, 3
    assert mean_abs_position_error(preds, ACTUALS) == pytest.approx(1.0)
    # mean squared errors = (0+0+4+0+9)/5 = 2.6
    assert rmse_position_error(preds, ACTUALS) == pytest.approx(2.6 ** 0.5)


def test_brier_score_win_bounds_and_values():
    # Perfect certainty on the winner → 0
    assert brier_score_win({"alice": 1.0, "bob": 0.0}, "alice") == 0.0
    # Uniform over 4 drivers, winner alice: mean((0.25-y)^2) over 4 drivers
    uniform = {"alice": 0.25, "bob": 0.25, "carol": 0.25, "dave": 0.25}
    expected = (3 * 0.0625 + 0.5625) / 4
    assert brier_score_win(uniform, "alice") == pytest.approx(expected)
    # Certain but wrong → penalised
    wrong = {"bob": 1.0, "alice": 0.0}
    assert brier_score_win(wrong, "alice") == pytest.approx(1.0)


def test_log_loss_win():
    probs = {"alice": 0.5, "bob": 0.5}
    import math
    assert log_loss_win(probs, "alice") == pytest.approx(-math.log(0.5))
    # Probability never exactly zero → epsilon-clamped
    assert log_loss_win({"alice": 0.0}, "alice") > 0


def test_kendall_tau_perfect_ordering():
    preds = [{"driver_id": d, "predicted_position": a["finish_position"]}
             for d, a in zip([x["driver_id"] for x in ACTUALS], ACTUALS)]
    assert kendall_tau(preds, ACTUALS) == pytest.approx(1.0)


def test_expected_points_error():
    pred_points = {"alice": 20.0, "bob": 10.0, "zed": 5.0}
    actual_points = {a["driver_id"]: a["points"] for a in ACTUALS}
    # Only common drivers alice & bob: |20-25| + |10-18| over 2 = 6.5
    assert expected_points_error(pred_points, actual_points) == pytest.approx(6.5)


def test_summarize_races_aggregation():
    results = [
        RaceBacktestResult(
            race_id="r1", race_name="R1", race_date=date(2025, 3, 1),
            winner_correct=True, podium_accuracy=1.0, top5_accuracy=0.8,
            mae_position=2.0, rmse_position=2.5, brier_score_win=0.10,
            log_loss_win=0.30, kendall_tau=0.7, expected_points_error=3.0,
        ),
        RaceBacktestResult(
            race_id="r2", race_name="R2", race_date=date(2025, 3, 8),
            winner_correct=False, podium_accuracy=0.6667, top5_accuracy=0.6,
            mae_position=4.0, rmse_position=5.0, brier_score_win=0.30,
            log_loss_win=1.10, kendall_tau=0.3, expected_points_error=5.0,
        ),
    ]
    summary = summarize_races(results)
    assert summary["n_races"] == 2
    assert summary["winner_accuracy"] == pytest.approx(0.5)
    assert summary["mean_abs_position_error"] == pytest.approx(3.0)
    assert summary["rmse_position_error"] == pytest.approx(3.75)
    assert summary["brier_score_win"] == pytest.approx(0.20)
    assert summary["top5_accuracy"] == pytest.approx(0.7)


def test_summarize_races_empty_is_zeroed_not_crash():
    summary = summarize_races([])
    assert summary["n_races"] == 0
    assert summary["winner_accuracy"] == 0.0