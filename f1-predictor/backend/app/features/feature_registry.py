from enum import Enum
from dataclasses import dataclass

class FeatureAvailability(Enum):
    HISTORICAL = "historical"
    WEDNESDAY = "wednesday"
    FP1_DONE = "fp1_done"
    FP2_DONE = "fp2_done"
    FP3_DONE = "fp3_done"
    QUALIFYING_DONE = "qualifying_done"

@dataclass
class FeatureDefinition:
    name: str
    description: str
    availability: FeatureAvailability
    models: list[str]
    dtype: str

FEATURE_REGISTRY: dict[str, FeatureDefinition] = {
    "driver_rolling_3_finish": FeatureDefinition(
        name="driver_rolling_3_finish",
        description="Driver rolling mean finish position (last 3 races)",
        availability=FeatureAvailability.HISTORICAL,
        models=["qualifying", "race_pace", "dnf"],
        dtype="float",
    ),
    "driver_rolling_5_finish": FeatureDefinition(
        name="driver_rolling_5_finish",
        description="Driver rolling mean finish position (last 5 races)",
        availability=FeatureAvailability.HISTORICAL,
        models=["qualifying", "race_pace", "dnf"],
        dtype="float",
    ),
    "driver_rolling_10_finish": FeatureDefinition(
        name="driver_rolling_10_finish",
        description="Driver rolling mean finish position (last 10 races)",
        availability=FeatureAvailability.HISTORICAL,
        models=["qualifying", "race_pace", "dnf"],
        dtype="float",
    ),
    "driver_quali_vs_teammate_3": FeatureDefinition(
        name="driver_quali_vs_teammate_3",
        description="Driver qualifying time delta vs teammate (last 3 races)",
        availability=FeatureAvailability.HISTORICAL,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "driver_dnf_rate_10": FeatureDefinition(
        name="driver_dnf_rate_10",
        description="Driver DNF rate in last 10 races",
        availability=FeatureAvailability.HISTORICAL,
        models=["dnf", "race_pace"],
        dtype="float",
    ),
    "team_quali_pace_vs_field": FeatureDefinition(
        name="team_quali_pace_vs_field",
        description="Team average qualifying pace gap to field median",
        availability=FeatureAvailability.HISTORICAL,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "team_dnf_rate_5": FeatureDefinition(
        name="team_dnf_rate_5",
        description="Team DNF rate in last 5 races",
        availability=FeatureAvailability.HISTORICAL,
        models=["dnf"],
        dtype="float",
    ),
    "circuit_length_km": FeatureDefinition(
        name="circuit_length_km",
        description="Circuit lap length in kilometers",
        availability=FeatureAvailability.HISTORICAL,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "circuit_overtaking_difficulty": FeatureDefinition(
        name="circuit_overtaking_difficulty",
        description="Overtaking difficulty index (0-1)",
        availability=FeatureAvailability.HISTORICAL,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "weather_is_wet": FeatureDefinition(
        name="weather_is_wet",
        description="Boolean indicating rain expected during session",
        availability=FeatureAvailability.WEDNESDAY,
        models=["qualifying", "race_pace"],
        dtype="bool",
    ),
    "weather_race_temp_c": FeatureDefinition(
        name="weather_race_temp_c",
        description="Forecast air temperature in Celsius",
        availability=FeatureAvailability.WEDNESDAY,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "fp1_pace_delta": FeatureDefinition(
        name="fp1_pace_delta",
        description="Driver FP1 best lap time delta vs field median",
        availability=FeatureAvailability.FP1_DONE,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "fp2_pace_delta": FeatureDefinition(
        name="fp2_pace_delta",
        description="Driver FP2 best lap time delta vs field median",
        availability=FeatureAvailability.FP2_DONE,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "fp3_pace_delta": FeatureDefinition(
        name="fp3_pace_delta",
        description="Driver FP3 best lap time delta vs field median",
        availability=FeatureAvailability.FP3_DONE,
        models=["qualifying", "race_pace"],
        dtype="float",
    ),
    "quali_gap_to_pole": FeatureDefinition(
        name="quali_gap_to_pole",
        description="Gap to pole in qualifying (seconds)",
        availability=FeatureAvailability.QUALIFYING_DONE,
        models=["race_pace"],
        dtype="float",
    ),
}
