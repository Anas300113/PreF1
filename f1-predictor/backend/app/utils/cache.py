import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional

from app.utils.logging_config import get_logger

logger = get_logger("disk_cache")

class DiskCache:
    def __init__(self, cache_dir: str = "./data/cache", default_ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir)
        # On serverless platforms (e.g. Vercel Functions) the bundle filesystem
        # is read-only at request time. Creating the cache directory must not
        # abort startup there: set() already swallows write failures, so a
        # cache that cannot be materialised degrades to a pure cache miss
        # (every request goes upstream) rather than an error.
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.debug(
                "Cache directory %s is not writable; running without a disk cache",
                self.cache_dir,
            )
        self.default_ttl = default_ttl_seconds

    def _get_path(self, key: str) -> Path:
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                item = json.load(f)
            if item.get("expires_at") and time.time() > item["expires_at"]:
                path.unlink(missing_ok=True)
                return None
            return item.get("data")
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        path = self._get_path(key)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        item = {
            "key": key,
            "data": value,
            "created_at": time.time(),
            "expires_at": expires_at,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(item, f)
        except Exception:
            pass

    def invalidate(self, key: str) -> None:
        path = self._get_path(key)
        path.unlink(missing_ok=True)
