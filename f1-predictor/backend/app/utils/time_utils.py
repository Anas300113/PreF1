from datetime import datetime, timezone, date
from typing import Optional

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def to_seconds(time_str: Optional[str]) -> Optional[float]:
    if not time_str or not isinstance(time_str, str):
        return None
    try:
        time_str = time_str.strip()
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60.0 + float(seconds)
            elif len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600.0 + float(minutes) * 60.0 + float(seconds)
        return float(time_str)
    except (ValueError, TypeError):
        return None

def from_seconds(seconds: Optional[float]) -> str:
    if seconds is None or seconds <= 0:
        return "N/A"
    mins = int(seconds // 60)
    secs = seconds % 60
    if mins > 0:
        return f"{mins}:{secs:06.3f}"
    return f"{secs:.3f}"

def parse_jolpica_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def regulation_era(year: int) -> str:
    if year < 2022:
        return "pre2022"
    elif year < 2026:
        return "2022+"
    return "2026+"
