# -*- coding: utf-8 -*-
"""
services/research_cache.py
--------------------------
Simple JSON-based cache for research results.

Usage:
    from services.research_cache import cache_get, cache_set
    
    # Try to get cached
    cached = cache_get("tools_maschinenbau_30d")
    if cached:
        return cached
    
    # Fetch fresh data
    results = fetch_from_api()
    
    # Cache for 14 days
    cache_set("tools_maschinenbau_30d", results)
"""
from __future__ import annotations
import os
import json
import time
import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = os.getenv("RESEARCH_CACHE_DIR", "data/cache")
DEFAULT_TTL_DAYS = int(os.getenv("RESEARCH_CACHE_TTL_DAYS", "14"))


def _ensure_dir(path: str) -> None:
    """Erstellt Verzeichnis falls nicht vorhanden."""
    os.makedirs(path, exist_ok=True)


def _path_for_key(key: str) -> str:
    """Generiert Dateipfad für Cache-Key."""
    _ensure_dir(DEFAULT_CACHE_DIR)
    # Sanitize key für Dateisystem
    safe = "".join(c for c in key if c.isalnum() or c in "-_.")
    return os.path.join(DEFAULT_CACHE_DIR, f"{safe}.json")


def cache_get(key: str, max_age_days: Optional[int] = None) -> Optional[Any]:
    """
    Lädt gecachten Wert.
    
    Args:
        key: Cache-Key
        max_age_days: Max. Alter in Tagen (default: 14)
        
    Returns:
        Gecachter Wert oder None wenn nicht gefunden/abgelaufen
    """
    ttl_days = DEFAULT_TTL_DAYS if max_age_days is None else max_age_days
    path = _path_for_key(key)
    
    if not os.path.exists(path):
        log.debug("Cache miss: %s", key)
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        
        ts = float(payload.get("_ts", 0))
        age_seconds = time.time() - ts
        age_days = age_seconds / 86400
        
        if age_days > ttl_days:
            log.debug("Cache expired: %s (%.1f days old)", key, age_days)
            return None
        
        log.debug("Cache hit: %s (%.1f days old)", key, age_days)
        return payload.get("data")
        
    except Exception as exc:
        log.warning("Cache read error for %s: %s", key, exc)
        return None


def cache_set(key: str, data: Any) -> None:
    """
    Speichert Wert im Cache.
    
    Args:
        key: Cache-Key
        data: Zu cachende Daten (muss JSON-serialisierbar sein)
    """
    path = _path_for_key(key)
    
    try:
        payload = {
            "_ts": time.time(),
            "data": data
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        log.debug("Cache saved: %s", key)
        
    except Exception as exc:
        log.warning("Cache write error for %s: %s", key, exc)


def cache_clear(key: Optional[str] = None) -> None:
    """
    Löscht Cache-Einträge.
    
    Args:
        key: Spezifischer Key zum Löschen, oder None für alle
    """
    if key:
        # Lösche spezifischen Key
        path = _path_for_key(key)
        try:
            if os.path.exists(path):
                os.remove(path)
                log.info("Cache cleared: %s", key)
        except Exception as exc:
            log.warning("Cache clear error for %s: %s", key, exc)
    else:
        # Lösche alle Cache-Dateien
        try:
            if os.path.exists(DEFAULT_CACHE_DIR):
                for filename in os.listdir(DEFAULT_CACHE_DIR):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(DEFAULT_CACHE_DIR, filename))
                log.info("All cache cleared")
        except Exception as exc:
            log.warning("Cache clear all error: %s", exc)


def cache_stats() -> dict:
    """
    Gibt Cache-Statistiken zurück.
    
    Returns:
        Dict mit: total_files, total_size_bytes, oldest_entry_days
    """
    stats = {
        "total_files": 0,
        "total_size_bytes": 0,
        "oldest_entry_days": 0.0
    }
    
    try:
        if not os.path.exists(DEFAULT_CACHE_DIR):
            return stats
        
        oldest_ts = time.time()
        
        for filename in os.listdir(DEFAULT_CACHE_DIR):
            if not filename.endswith('.json'):
                continue
            
            path = os.path.join(DEFAULT_CACHE_DIR, filename)
            stats["total_files"] += 1
            stats["total_size_bytes"] += os.path.getsize(path)
            
            # Check oldest
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                    ts = float(payload.get("_ts", time.time()))
                    oldest_ts = min(oldest_ts, ts)
            except Exception:
                pass
        
        stats["oldest_entry_days"] = (time.time() - oldest_ts) / 86400
        
    except Exception as exc:
        log.warning("Cache stats error: %s", exc)
    
    return stats
