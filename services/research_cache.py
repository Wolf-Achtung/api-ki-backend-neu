# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, time, logging
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)
DEFAULT_CACHE_DIR = os.getenv("RESEARCH_CACHE_DIR", "data/cache")
DEFAULT_TTL_DAYS = int(os.getenv("RESEARCH_CACHE_TTL_DAYS", "14"))

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _path_for_key(key: str) -> str:
    _ensure_dir(DEFAULT_CACHE_DIR)
    safe = "".join(c for c in key if c.isalnum() or c in "-_.")
    return os.path.join(DEFAULT_CACHE_DIR, f"{safe}.json")

def cache_get(key: str, max_age_days: Optional[int] = None) -> Optional[Any]:
    ttl_days = DEFAULT_TTL_DAYS if max_age_days is None else max_age_days
    path = _path_for_key(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        ts = float(payload.get("_ts", 0))
        if time.time() - ts > ttl_days * 86400:
            return None
        return payload.get("data")
    except Exception as exc:
        LOGGER.warning("cache_get failed for %s: %s", key, exc)
        return None

def cache_set(key: str, data: Any) -> None:
    path = _path_for_key(key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"_ts": time.time(), "data": data}, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        LOGGER.warning("cache_set failed for %s: %s", key, exc)
