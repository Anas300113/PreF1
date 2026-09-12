from typing import Dict, Any, List

FEATURE_LABELS = {
    "driver_rolling_3_finish": "Strong recent 3-race finishing form",
    "driver_rolling_5_finish": "Solid rolling 5-race consistency",
    "driver_quali_vs_teammate_3": "Superior teammate qualifying pace delta",
    "driver_circuit_avg_finish": "Favorable historical performance at this circuit",
    "team_quali_pace_vs_field": "Strong constructor qualifying package",
    "weather_is_wet": "High rain/wet conditions uncertainty",
    "circuit_overtaking_difficulty": "Challenging overtaking characteristics on track",
    "fp2_pace_delta": "Fast FP2 long-run practice pace",
}

def generate_explanation(driver_id: str, shap_values: Dict[str, float]) -> Dict[str, Any]:
    pos_factors = []
    neg_factors = []

    sorted_shaps = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)

    for feature, val in sorted_shaps[:5]:
        label = FEATURE_LABELS.get(feature, feature.replace("_", " ").title())
        if val < 0:  # Negative delta = faster lap time / better finish
            pos_factors.append(label)
        else:
            neg_factors.append(label)

    if not pos_factors:
        pos_factors = ["Consistent baseline performance", "Strong team reliability"]
    if not neg_factors:
        neg_factors = ["High track evolution sensitivity"]

    return {
        "positive_factors": pos_factors,
        "negative_factors": neg_factors,
        "shap_values": shap_values,
    }
