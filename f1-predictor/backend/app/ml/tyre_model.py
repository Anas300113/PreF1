from typing import Dict, Any

class TyreModel:
    """Tyre degradation and compound performance model."""

    COMPOUND_BASE_DELTAS = {
        "SOFT": -1.2,
        "MEDIUM": -0.6,
        "HARD": 0.0,
        "INTER": 0.0,
        "WET": 0.0,
    }

    COMPOUND_DEG_SLOPES = {
        "SOFT": 0.08,
        "MEDIUM": 0.05,
        "HARD": 0.03,
        "INTER": 0.04,
        "WET": 0.02,
    }

    def predict_lap_time_delta(
        self, compound: str, tyre_age: int, circuit_deg_index: float = 0.5
    ) -> float:
        compound_upper = compound.upper() if compound else "MEDIUM"
        base_delta = self.COMPOUND_BASE_DELTAS.get(compound_upper, 0.0)
        base_slope = self.COMPOUND_DEG_SLOPES.get(compound_upper, 0.05)

        # Scale by circuit degradation index
        effective_slope = base_slope * (0.5 + circuit_deg_index)
        deg_penalty = effective_slope * max(0, tyre_age)

        return base_delta + deg_penalty

    def get_optimal_stint_length(self, compound: str, circuit_deg_index: float = 0.5) -> int:
        compound_upper = compound.upper() if compound else "MEDIUM"
        limits = {"SOFT": 18, "MEDIUM": 28, "HARD": 40, "INTER": 30, "WET": 35}
        base_limit = limits.get(compound_upper, 25)
        return int(base_limit / (0.5 + circuit_deg_index))
