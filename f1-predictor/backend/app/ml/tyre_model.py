from typing import Dict, Optional
import numpy as np

# Labelled fallback priors (§12: avoid hard-coded values unless data is
# insufficient).  Used only when stint data cannot be fitted — e.g. a circuit
# with no ingested race laps.  Values are documented assumptions, not fits.
FALLBACK_PARAMS = {
    "SOFT": {"base_delta": -1.2, "linear": 0.08, "quadratic": 0.0008, "sigma": 0.15},
    "MEDIUM": {"base_delta": -0.6, "linear": 0.05, "quadratic": 0.0004, "sigma": 0.12},
    "HARD": {"base_delta": 0.0, "linear": 0.03, "quadratic": 0.0002, "sigma": 0.10},
    "INTER": {"base_delta": 0.0, "linear": 0.04, "quadratic": 0.0003, "sigma": 0.20},
    "WET": {"base_delta": 0.0, "linear": 0.02, "quadratic": 0.0001, "sigma": 0.25},
}

VALID_COMPOUNDS = {"SOFT", "MEDIUM", "HARD", "INTER", "WET"}


class TyreModel:
    """Tyre degradation and compound performance model.

    lap_time_delta(compound, age) = base_delta + linear*age + quadratic*age^2

    Parameters may be fitted from real stint data via ``TyreDegradationFitter``
    (quadratic polynomial per compound, lap-1 and safety-car laps excluded).
    Falls back to labelled priors when fitting is impossible.
    """

    # Retained for backwards compatibility with earlier callers.
    COMPOUND_BASE_DELTAS = {k: v["base_delta"] for k, v in FALLBACK_PARAMS.items()}
    COMPOUND_DEG_SLOPES = {k: v["linear"] for k, v in FALLBACK_PARAMS.items()}

    def __init__(self, fitted_params: Optional[Dict[str, dict]] = None):
        self.params: Dict[str, dict] = {}
        for compound in VALID_COMPOUNDS:
            fitted = (fitted_params or {}).get(compound)
            if fitted and all(
                isinstance(fitted.get(k), (int, float))
                for k in ("base_delta", "linear", "quadratic", "sigma")
            ):
                self.params[compound] = {**fitted, "fitted": True}
            else:
                self.params[compound] = {**FALLBACK_PARAMS[compound], "fitted": False}

    def predict_lap_time_delta(
        self, compound: str, tyre_age: int, circuit_deg_index: float = 0.5
    ) -> float:
        compound_upper = (compound or "MEDIUM").upper()
        p = self.params.get(compound_upper, self.params["MEDIUM"])
        age = max(0, tyre_age)
        deg_scale = 0.5 + circuit_deg_index
        return p["base_delta"] + deg_scale * (p["linear"] * age + p["quadratic"] * age * age)

    def get_stint_total_time(
        self, compound: str, stint_laps: int, circuit_deg_index: float = 0.5
    ) -> float:
        """Closed-form cumulative tyre delta for a stint of ``stint_laps`` laps.

        Sum of (base + s*a + q*a^2) for a = 0 .. n-1:
            n*base + s*n(n-1)/2 + q*(n-1)n(2n-1)/6
        """
        compound_upper = (compound or "MEDIUM").upper()
        p = self.params.get(compound_upper, self.params["MEDIUM"])
        n = max(0, int(stint_laps))
        if n == 0:
            return 0.0
        deg_scale = 0.5 + circuit_deg_index
        linear_sum = p["linear"] * n * (n - 1) / 2.0
        quadratic_sum = p["quadratic"] * (n - 1) * n * (2 * n - 1) / 6.0
        return n * p["base_delta"] + deg_scale * (linear_sum + quadratic_sum)

    def sample_stint_noise(
        self, n_sims: int, race_laps: int, rng: np.random.Generator, circuit_deg_index: float = 0.5
    ) -> np.ndarray:
        """Per-race stochastic tyre noise for one driver, shape (n_sims,).

        Residual sigma is per-lap; total stint noise scales with sqrt(laps).
        """
        sigmas = np.array([self.params[c]["sigma"] for c in ("MEDIUM", "HARD", "SOFT")])
        sigma = float(np.mean(sigmas)) * (0.5 + circuit_deg_index)
        return rng.normal(0.0, sigma * np.sqrt(max(1, race_laps)), size=n_sims)

    def get_optimal_stint_length(self, compound: str, circuit_deg_index: float = 0.5) -> int:
        """Stint length at which marginal degradation cost crosses 0.25 s/lap."""
        compound_upper = (compound or "MEDIUM").upper()
        p = self.params.get(compound_upper, self.params["MEDIUM"])
        deg_scale = 0.5 + circuit_deg_index
        age = 0
        while deg_scale * (p["linear"] + 2 * p["quadratic"] * age) < 0.25 and age < 60:
            age += 1
        return max(1, age)

    @property
    def is_fitted(self) -> bool:
        return any(p["fitted"] for p in self.params.values())


class TyreDegradationFitter:
    """Fits per-compound quadratic degradation curves from race stint laps.

    Data-cleaning rules (from letix1/f1-strategy-optimizer and
    AryunGupta/Monte-Carlo-F1-Simulation research):
      * Exclude lap 1 of each stint — standing starts anchor the low end of
        the tyre-age fit at an artificially slow point.
      * Exclude safety-car / VSC / yellow-flag laps (track_status != '1').
      * Require a minimum number of observations per compound, otherwise the
        compound falls back to labelled priors.
    """

    MIN_OBSERVATIONS = 120

    def fit(self, laps_df) -> Dict[str, dict]:
        """``laps_df`` must contain: lap_time_s, compound, tyre_life,
        session_type, track_status, deleted (pandas DataFrame)."""
        params: Dict[str, dict] = {}
        if laps_df is None or len(laps_df) == 0:
            return params

        df = laps_df.copy()
        if "session_type" in df.columns:
            df = df[df["session_type"] == "race"]
        if "deleted" in df.columns:
            df = df[df["deleted"] == False]  # noqa: E712
        df = df[df["lap_time_s"].notna() & df["compound"].notna() & df["tyre_life"].notna()]
        df["compound"] = df["compound"].str.upper()
        df = df[df["compound"].isin(VALID_COMPOUNDS)]
        # Clean green-flag laps only; tyre_life > 1 drops stint lap 1 (§ lap-1
        # exclusion rule).
        df = df[df["tyre_life"] > 1]
        if "track_status" in df.columns:
            df = df[df["track_status"].astype(str).str.strip().str.startswith("1")]
        for compound, group in df.groupby("compound"):
            # Winsorise implausible lap times (> 2x compound median).
            median = group["lap_time_s"].median()
            group = group[group["lap_time_s"] < 2.0 * median]
            if len(group) < self.MIN_OBSERVATIONS:
                continue
            x = group["tyre_life"].to_numpy(dtype=float)
            y = group["lap_time_s"].to_numpy(dtype=float)
            quad = np.polyfit(x, y, 2)  # [quadratic, linear, intercept]
            residuals = y - np.polyval(quad, x)
            sigma = float(np.std(residuals))
            params[compound] = {
                # base_delta normalised to 0; compound pace offsets are applied
                # separately so fits are pace *deltas*, not absolute lap times.
                "base_delta": 0.0,
                "linear": float(quad[1]),
                "quadratic": float(quad[0]),
                "sigma": max(0.05, min(sigma, 1.5)),
            }
        return params

        return any(p["fitted"] for p in self.params.values())
