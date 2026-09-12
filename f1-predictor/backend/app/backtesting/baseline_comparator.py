"""Compares model season metrics against chronologically honest baselines."""
from typing import Any


class BaselineComparator:
    @staticmethod
    def compare(
        model_summary: dict[str, Any],
        baseline_summaries: dict[str, dict[str, float]],
    ) -> dict[str, Any]:
        """Per-baseline deltas: positive winner delta / negative MAE delta = model better."""
        comparison: dict[str, Any] = {}
        for name, base in baseline_summaries.items():
            comparison[name] = {
                "winner_accuracy_delta": round(
                    model_summary.get("winner_accuracy", 0.0)
                    - base.get("winner_accuracy", 0.0), 4
                ),
                "podium_accuracy_delta": round(
                    model_summary.get("podium_accuracy", 0.0)
                    - base.get("podium_accuracy", 0.0), 4
                ),
                "mae_delta": round(
                    model_summary.get("mean_abs_position_error", 0.0)
                    - base.get("mae_position", 0.0), 4
                ),
                "beats_on_winner": model_summary.get("winner_accuracy", 0.0)
                > base.get("winner_accuracy", 0.0),
                "beats_on_mae": model_summary.get("mean_abs_position_error", 0.0)
                < base.get("mae_position", 0.0),
            }
        return comparison
