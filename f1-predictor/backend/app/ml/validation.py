from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np
from scipy.stats import kendalltau, spearmanr


def chronological_split(
    X: pd.DataFrame,
    y: pd.Series,
    val_fraction: float = 0.15,
) -> Tuple[Tuple[pd.DataFrame, pd.Series], Tuple[pd.DataFrame, pd.Series]]:
    """Split by row order (assumes X/y are chronologically sorted)."""
    n = len(X)
    if n < 10:
        return (X, y), (X.iloc[:0], y.iloc[:0])
    split_idx = int(n * (1 - val_fraction))
    return (X.iloc[:split_idx], y.iloc[:split_idx]), (X.iloc[split_idx:], y.iloc[split_idx:])

class ChronologicalValidator:
    """Time-aware validation for F1 prediction to avoid data leakage."""

    def __init__(
        self,
        train_start_year: int = 2018,
        val_year: int = 2023,
        test_year: int = 2024
    ):
        self.train_start_year = train_start_year
        self.val_year = val_year
        self.test_year = test_year

    def get_train_val_test_split(
        self, df: pd.DataFrame, year_col: str = "season_year"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        train_df = df[(df[year_col] >= self.train_start_year) & (df[year_col] < self.val_year)]
        val_df = df[df[year_col] == self.val_year]
        test_df = df[df[year_col] == self.test_year]
        return train_df, val_df, test_df

def evaluate_ranking(y_true_positions: pd.Series, y_pred_values: pd.Series) -> Dict[str, float]:
    if len(y_true_positions) < 2:
        return {"kendall_tau": 0.0, "spearman_r": 0.0, "p1_accuracy": 0.0, "top3_accuracy": 0.0, "mae_position": 0.0}

    tau, _ = kendalltau(y_true_positions, y_pred_values)
    rho, _ = spearmanr(y_true_positions, y_pred_values)

    p1_acc = 1.0 if np.argmin(y_pred_values) == np.argmin(y_true_positions) else 0.0

    pred_ranks = np.argsort(np.argsort(y_pred_values)) + 1
    true_ranks = y_true_positions.values

    mae = float(np.mean(np.abs(pred_ranks - true_ranks)))

    top3_pred = set(np.argsort(y_pred_values)[:3])
    top3_true = set(np.argsort(true_ranks)[:3])
    top3_acc = len(top3_pred.intersection(top3_true)) / 3.0

    return {
        "kendall_tau": float(tau) if not np.isnan(tau) else 0.0,
        "spearman_r": float(rho) if not np.isnan(rho) else 0.0,
        "p1_accuracy": p1_acc,
        "top3_accuracy": top3_acc,
        "mae_position": mae,
    }
