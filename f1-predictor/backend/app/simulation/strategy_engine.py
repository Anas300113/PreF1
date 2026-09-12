from dataclasses import dataclass
from typing import List
import numpy as np
from app.ml.tyre_model import TyreModel

@dataclass
class PitStrategy:
    stops: int
    compounds: List[str]
    pit_laps: List[int]
    expected_total_time: float
    probability: float

class StrategyEngine:
    """Evaluates and samples pit strategies for Monte Carlo simulations.

    Generates 1/2/3-stop candidates across compound sequences with optimised
    pit windows, and ranks them by a risk-adjusted score
    -(P50 + lambda * IQR) (AryunGupta research): a frontrunner may prefer a
    slightly slower strategy with far less spread.
    """

    # Compound sequences by stop count (dry).  Order = stint order.
    DRY_SEQUENCES = {
        0: [("HARD",)],
        1: [("MEDIUM", "HARD"), ("HARD", "MEDIUM")],
        2: [("MEDIUM", "HARD", "HARD"), ("SOFT", "MEDIUM", "HARD"), ("MEDIUM", "MEDIUM", "HARD")],
        3: [("SOFT", "MEDIUM", "HARD", "MEDIUM")],
    }

    def __init__(self, tyre_model: TyreModel):
        self.tyre_model = tyre_model

    def generate_candidate_strategies(
        self, race_laps: int, circuit_deg_index: float = 0.5, is_wet: bool = False
    ) -> List[PitStrategy]:
        if is_wet:
            return [
                PitStrategy(stops=1, compounds=["INTER", "INTER"], pit_laps=[int(race_laps * 0.5)], expected_total_time=0.0, probability=0.7),
                PitStrategy(stops=2, compounds=["INTER", "INTER", "WET"], pit_laps=[int(race_laps * 0.35), int(race_laps * 0.7)], expected_total_time=5.0, probability=0.3)
            ]

        candidates: List[PitStrategy] = []
        for stops, sequences in self.DRY_SEQUENCES.items():
            for compounds in sequences:
                # Optimal pit windows: equalise stint lengths, nudged earlier
                # for soft-opening sequences at high degradation.
                boundaries = [0]
                for i in range(stops):
                    frac = (i + 1) / (stops + 1)
                    if compounds[0] == "SOFT":
                        frac *= 1.0 - 0.08 * circuit_deg_index
                    boundaries.append(int(race_laps * frac))
                boundaries.append(race_laps)
                pit_laps = [b for b in boundaries[1:-1] if 0 < b < race_laps]
                stint_lengths = [
                    max(1, boundaries[i + 1] - boundaries[i]) for i in range(len(boundaries) - 1)
                ]
                # Cost = tyre time + pit loss.
                tyre_time = sum(
                    self.tyre_model.get_stint_total_time(c, n, circuit_deg_index)
                    for c, n in zip(compounds, stint_lengths)
                )
                expected = tyre_time + len(pit_laps) * 22.0
                candidates.append(PitStrategy(
                    stops=len(pit_laps),
                    compounds=list(compounds),
                    pit_laps=pit_laps,
                    expected_total_time=expected,
                    probability=0.0,
                ))
        # Soft prior toward extra stops at high degradation (retained from the
        # original engine); exact weights are refined by MC ranking.
        two_stop_probability = float(np.clip(0.18 + 0.44 * circuit_deg_index, 0.20, 0.65))
        base_weights = {0: 0.02, 1: 1.0 - two_stop_probability, 2: two_stop_probability, 3: 0.05}
        for cand in candidates:
            n_same = sum(1 for c in candidates if c.stops == cand.stops)
            cand.probability = base_weights.get(cand.stops, 0.02) / max(1, n_same)
        total = sum(c.probability for c in candidates) or 1.0
        for cand in candidates:
            cand.probability /= total
        return candidates

    def rank_strategies(
        self,
        candidates: List[PitStrategy],
        race_laps: int,
        circuit_deg_index: float = 0.5,
        n_simulations: int = 2000,
        risk_aversion: float = 0.5,
        pit_loss_seconds: float = 22.0,
        seed: int = 42,
    ) -> List[dict]:
        """Monte Carlo each candidate strategy; rank by risk-adjusted score
        -(P50 + lambda * IQR).  Returns ranked list with distributions."""
        rng = np.random.default_rng(seed)
        sigma = float(np.mean([self.tyre_model.params[c]["sigma"] for c in ("MEDIUM", "HARD", "SOFT")]))
        results = []
        for cand in candidates:
            base_tyre = self._strategy_tyre_time_static(cand, race_laps, circuit_deg_index)
            total_times = base_tyre + rng.normal(
                0.0, sigma * np.sqrt(race_laps), size=n_simulations
            )
            # Per-stop execution ~ Normal(circuit pit loss, 1.2s); discounted
            # 55% when the stop lands within 3 laps of a sampled safety car.
            sc_lap = rng.integers(5, max(6, race_laps - 10), size=n_simulations)
            sc_active = rng.random(n_simulations) < 0.5
            for pit_lap in cand.pit_laps:
                stop_loss = rng.normal(pit_loss_seconds, 1.2, size=n_simulations)
                stop_loss[sc_active & (np.abs(sc_lap - pit_lap) <= 3)] *= 0.45
                total_times += stop_loss
            p50, p25, p75 = np.percentile(total_times, [50, 25, 75])
            iqr = p75 - p25
            results.append({
                "stops": cand.stops,
                "compounds": cand.compounds,
                "pit_laps": cand.pit_laps,
                "expected_total_time_s": float(np.mean(total_times)),
                "p50_s": float(p50), "p25_s": float(p25), "p75_s": float(p75),
                "iqr_s": float(iqr),
                "stdev_s": float(np.std(total_times)),
                "risk_adjusted_score": float(-(p50 + risk_aversion * iqr)),
            })
        results.sort(key=lambda r: r["risk_adjusted_score"], reverse=True)
        for rank, r in enumerate(results, 1):
            r["rank"] = rank
        return results

    def _strategy_tyre_time_static(
        self, strategy: PitStrategy, race_laps: int, circuit_deg_index: float
    ) -> float:
        boundaries = [0, *strategy.pit_laps, race_laps]
        total = 0.0
        for i, compound in enumerate(strategy.compounds):
            if i + 1 >= len(boundaries):
                break
            stint = max(0, boundaries[i + 1] - boundaries[i])
            total += self.tyre_model.get_stint_total_time(compound, stint, circuit_deg_index)
        return total

    def sample_strategies(
        self, n_sims: int, n_drivers: int, strategies: List[PitStrategy], rng: np.random.Generator
    ) -> np.ndarray:
        probs = np.array([s.probability for s in strategies])
        probs = probs / np.sum(probs)
        return rng.choice(len(strategies), size=(n_sims, n_drivers), p=probs)

        return candidates
