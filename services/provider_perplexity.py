# -*- coding: utf-8 -*-
"""
provider_perplexity.py
----------------------
Perplexity API client with Sprint G14-B circuit breaker.

Circuit breaker pattern: After PPLX_FAILURE_THRESHOLD consecutive failures,
the circuit "opens" and returns empty results immediately without making
API calls, reducing latency and avoiding cascading failures.
"""
from __future__ import annotations
import os, json, logging, requests, threading, time
from typing import List, Dict, Any

LOGGER = logging.getLogger(__name__)
PPLX_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PPLX_ENDPOINT = os.getenv("PPLX_ENDPOINT", "https://api.perplexity.ai/chat/completions")
PPLX_MODEL = os.getenv("PERPLEXITY_MODEL") or os.getenv("PPLX_MODEL", "sonar-pro")

# SPRINT G14-B: Circuit breaker configuration
PPLX_FAILURE_THRESHOLD = int(os.getenv("PPLX_FAILURE_THRESHOLD", "2"))
PPLX_CIRCUIT_RESET_SEC = int(os.getenv("PPLX_CIRCUIT_RESET_SEC", "120"))  # 2 minutes
PPLX_TIMEOUT = int(os.getenv("PPLX_TIMEOUT", "30"))  # reduced from 45s

SYSTEM = "You are a research assistant. Return concise JSON with a list of items [{title, url, summary}]. No markdown."
USER_TMPL = "Find the most recent (last {days} days) {topic}. Return JSON only."


# =============================================================================
# SPRINT G14-B: Circuit Breaker State
# =============================================================================

class _CircuitBreaker:
    """Thread-safe circuit breaker for Perplexity API."""

    def __init__(self, threshold: int, reset_sec: int):
        self._threshold = threshold
        self._reset_sec = reset_sec
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self._threshold:
                LOGGER.warning(
                    "[PPLX-CIRCUIT] Circuit OPEN after %d failures (reset in %ds)",
                    self._failure_count, self._reset_sec
                )

    def record_success(self) -> None:
        """Record a success and reset the circuit."""
        with self._lock:
            if self._failure_count > 0:
                LOGGER.info("[PPLX-CIRCUIT] Circuit reset after successful call")
            self._failure_count = 0

    def is_open(self) -> bool:
        """Check if circuit is open (should skip API calls)."""
        with self._lock:
            if self._failure_count < self._threshold:
                return False
            # Check if reset time has passed
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self._reset_sec:
                LOGGER.info("[PPLX-CIRCUIT] Circuit HALF-OPEN, allowing test request")
                self._failure_count = self._threshold - 1  # Allow one test
                return False
            return True

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        with self._lock:
            return {
                "failures": self._failure_count,
                "threshold": self._threshold,
                "is_open": self._failure_count >= self._threshold,
                "reset_sec": self._reset_sec,
            }


# Global circuit breaker instance
_circuit = _CircuitBreaker(PPLX_FAILURE_THRESHOLD, PPLX_CIRCUIT_RESET_SEC)


def get_circuit_status() -> Dict[str, Any]:
    """Get current circuit breaker status (for monitoring/debugging)."""
    return _circuit.get_status()


def _post_json(url: str, payload: dict, timeout: int = PPLX_TIMEOUT) -> dict[Any, Any]:
    headers = {"Content-Type":"application/json","Accept":"application/json","Authorization": f"Bearer {PPLX_API_KEY}" if PPLX_API_KEY else ""}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else {}

def search(topic: str, days: int = 30, max_items: int = 8) -> List[Dict]:
    """
    Search via Perplexity API with circuit breaker protection.

    SPRINT G14-B: Circuit breaker pattern prevents cascading failures.
    After PPLX_FAILURE_THRESHOLD consecutive errors, returns empty immediately.
    """
    if not PPLX_API_KEY:
        LOGGER.warning("PERPLEXITY_API_KEY not set")
        return []

    # SPRINT G14-B: Check circuit breaker before making request
    if _circuit.is_open():
        LOGGER.warning("[PPLX-CIRCUIT] Circuit is OPEN, skipping API call for: %s", topic[:50])
        return []

    messages = [{"role":"system","content":SYSTEM},{"role":"user","content":USER_TMPL.format(days=max(1,days), topic=topic)}]
    payload = {"model": PPLX_MODEL, "messages": messages, "temperature": 0.1}
    try:
        data = _post_json(PPLX_ENDPOINT, payload)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            obj = json.loads(content)
            items = obj if isinstance(obj, list) else obj.get("items", [])
        except Exception:
            start, end = content.find("["), content.rfind("]")
            items = json.loads(content[start:end+1]) if start != -1 and end != -1 else []
        out = []
        for it in items[:max_items]:
            out.append({"title": it.get("title",""), "url": it.get("url",""), "content": it.get("summary",""), "source":"perplexity"})

        # SPRINT G14-B: Record success, reset circuit
        _circuit.record_success()
        return out
    except Exception as exc:
        # SPRINT G14-B: Record failure, may open circuit
        _circuit.record_failure()
        LOGGER.error("Perplexity search failed: %s", exc)
        return []
