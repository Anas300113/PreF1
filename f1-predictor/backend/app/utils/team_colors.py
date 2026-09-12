"""2025 F1 team colour mapping for UI display."""

TEAM_COLORS: dict[str, str] = {
    "mclaren": "#FF8000",
    "ferrari": "#E8002D",
    "red_bull": "#3671C6",
    "mercedes": "#27F4D2",
    "aston_martin": "#229971",
    "alpine": "#FF87BC",
    "williams": "#64C4FF",
    "rb": "#6692FF",
    "sauber": "#52E252",
    "haas": "#B6BABD",
    "cadillac": "#004785",
}


def team_color(team_id: str, team_name: str | None = None) -> str:
    key = team_id.lower().replace("-", "_")
    if key in TEAM_COLORS:
        return TEAM_COLORS[key]
    if team_name:
        name_key = team_name.lower().replace(" ", "_")
        for token in (name_key, name_key.split("_")[0]):
            if token in TEAM_COLORS:
                return TEAM_COLORS[token]
    return "#888888"
