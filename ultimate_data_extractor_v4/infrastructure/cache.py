import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0


class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_stats = CacheStats()

    def get_cache_key(self, url: str, query: str) -> str:
        return str(abs(hash(f"{url}|{query}")))

    def get(self, cache_key: str, ttl_hours: int = 24) -> Optional[Any]:
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                ts = datetime.fromisoformat(data["timestamp"])  # type: ignore
                if datetime.now() - ts < timedelta(hours=ttl_hours):
                    self.cache_stats.hits += 1
                    return data.get("data")
            except Exception:
                pass
        self.cache_stats.misses += 1
        return None

    def set(self, cache_key: str, data: Any) -> None:
        try:
            with open(self.cache_dir / f"{cache_key}.json", "w", encoding="utf-8") as f:
                json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f, default=str)
        except Exception:
            # best-effort cache
            pass

