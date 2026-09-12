from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root (f1-predictor/): this file lives at backend/app/config.py,
# so parents[2] is the project root. Relative data/model paths are anchored
# there so the API works regardless of the working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _anchor_path(raw: str) -> str:
    """Rewrite relative sqlite/paths to be anchored at the project root."""
    if ":///" in raw and raw.split("://")[0].startswith("sqlite"):
        scheme, _, rel = raw.partition(":///")
        p = Path(rel)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        return f"{scheme}:///{p.as_posix()}"
    if raw.startswith("./"):
        p = Path(raw)
        if not p.is_absolute():
            return str(PROJECT_ROOT / p)
    return raw


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/db/f1_predictor.db"
    fastf1_cache_dir: str = "./data/cache/fastf1"
    data_raw_dir: str = "./data/raw"
    models_dir: str = "./models/trained"
    log_level: str = "INFO"
    api_rate_limit_jolpica: int = 4
    jolpica_base_url: str = "https://api.jolpi.ca/ergast/f1"
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    model_version: str = "xgb-mc-v1"
    feature_version: str = "v1.0"
    simulation_default_count: int = 10000
    simulation_max_count: int = 500000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    def model_post_init(self, __context) -> None:
        self.database_url = _anchor_path(self.database_url)
        self.models_dir = _anchor_path(self.models_dir)
        self.data_raw_dir = _anchor_path(self.data_raw_dir)
        self.fastf1_cache_dir = _anchor_path(self.fastf1_cache_dir)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
