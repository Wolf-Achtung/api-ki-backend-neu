# -*- coding: utf-8 -*-
"""KIS-1269: Cookiefreie First-Party-Reichweitenmessung.

Das UX-Audit fand: keinerlei Analytics — Absprung-/Abbruchpunkte sind
unbekannt. Design-Entscheidung (Datensparsamkeit wie beim Firmennamen):

  - KEINE Cookies, KEINE IP-Speicherung, KEINE User-IDs, KEIN Fingerprinting
  - nur anonyme Zähl-Events aus einer festen Allowlist (Funnel-Schritte)
  - Beacon sendet text/plain (kein CORS-Preflight, sendBeacon-kompatibel)
  - Auswertung nur mit Admin-Key (STRATEGY_ADMIN_KEY, timing-safe)

Damit ist die Messung nach Art. 6 Abs. 1 lit. f DSGVO ohne Consent-Banner
vertretbar (keine personenbezogenen Daten); die Datenschutzerklärung
erwähnt sie transparent.
"""
from __future__ import annotations

import hmac
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request, Response
from sqlalchemy import func

from core.db import SessionLocal
from models import MetricsEvent
from services.rate_limit import RateLimiter

log = logging.getLogger(__name__)
router = APIRouter(tags=["metrics"])

# Feste Allowlist — alles andere wird verworfen (kein freies Event-Feld,
# damit niemand PII in die Tabelle schreiben kann).
ALLOWED_EVENTS = frozenset({
    "pageview",
    "cta_click",
    "login_success",
    "mode_chat",
    "mode_form",
    "q1_started",
    "q1_completed",
    "strategy_submitted",
    "feedback_submitted",
    "resilienz_started",
    "resilienz_completed",
})

_MAX_FIELD = 120
_limiter = RateLimiter(namespace="metrics", limit=60, window_sec=60)


def _clean(value: object) -> str:
    return str(value or "")[:_MAX_FIELD]


@router.post("/metrics/event", status_code=204)
async def track_event(request: Request) -> Response:
    """Anonymer Zähl-Beacon. Nimmt text/plain-JSON (sendBeacon/keepalive)."""
    # Rate-Limit pro Client-IP (IP wird NUR für das Limit-Fenster im
    # Speicher gehalten, nie persistiert).
    client_ip = request.client.host if request.client else "unknown"
    _limiter.hit(key=client_ip)

    raw = await request.body()
    if len(raw) > 2048:
        raise HTTPException(status_code=413, detail="payload too large")
    try:
        data = json.loads(raw.decode("utf-8", errors="replace") or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json")

    event = _clean(data.get("event"))
    if event not in ALLOWED_EVENTS:
        raise HTTPException(status_code=400, detail="unknown event")

    db = SessionLocal()
    try:
        db.add(MetricsEvent(
            event=event,
            page=_clean(data.get("page")),
            lang=_clean(data.get("lang"))[:8],
            ref=_clean(data.get("ref")),
        ))
        db.commit()
    finally:
        db.close()
    return Response(status_code=204)


@router.get("/metrics/summary")
def metrics_summary(admin_key: str = Query(...), days: int = Query(30, ge=1, le=365)) -> dict:
    """Tages-Zählstände je Event (nur Admin)."""
    expected = os.getenv("STRATEGY_ADMIN_KEY", "")
    if not expected:
        raise HTTPException(status_code=500, detail="STRATEGY_ADMIN_KEY nicht konfiguriert")
    if not hmac.compare_digest(admin_key, expected):
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    db = SessionLocal()
    try:
        rows = (
            db.query(
                func.date(MetricsEvent.created_at).label("day"),
                MetricsEvent.event,
                func.count().label("n"),
            )
            .filter(MetricsEvent.created_at >= since)
            .group_by("day", MetricsEvent.event)
            .order_by("day")
            .all()
        )
    finally:
        db.close()
    out: dict = {}
    for day, event, n in rows:
        out.setdefault(str(day), {})[event] = n
    return {"days": days, "counts": out}


@router.get("/metrics/anthropic-usage")
def anthropic_usage_summary(admin_key: str = Query(...),
                            days: int = Query(30, ge=1, le=365)) -> dict:
    """KIS-1270: Aggregation der persistierten Usage nach call_site x model.

    Liefert je Gruppe: Calls, Tokensummen (alle drei Input-Felder getrennt),
    Output-Token, cache-korrekte Kosten. Dazu Gesamtkosten und die Zahl der
    Briefings im Zeitraum als Mengengeruest."""
    expected = os.getenv("STRATEGY_ADMIN_KEY", "")
    if not expected:
        raise HTTPException(status_code=500, detail="STRATEGY_ADMIN_KEY nicht konfiguriert")
    if not hmac.compare_digest(admin_key, expected):
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")

    from models import AnthropicUsage, Briefing
    since = datetime.now(timezone.utc) - timedelta(days=days)
    db = SessionLocal()
    try:
        rows = (
            db.query(
                AnthropicUsage.call_site,
                AnthropicUsage.model,
                func.count().label("calls"),
                func.sum(AnthropicUsage.input_tokens),
                func.sum(AnthropicUsage.cache_creation_input_tokens),
                func.sum(AnthropicUsage.cache_read_input_tokens),
                func.sum(AnthropicUsage.output_tokens),
                func.sum(AnthropicUsage.cost_usd),
            )
            .filter(AnthropicUsage.created_at >= since)
            .group_by(AnthropicUsage.call_site, AnthropicUsage.model)
            .order_by(func.sum(AnthropicUsage.cost_usd).desc())
            .all()
        )
        briefings = (db.query(func.count(Briefing.id))
                     .filter(Briefing.created_at >= since).scalar()) or 0
    finally:
        db.close()

    groups = []
    total_cost = 0.0
    for cs, model, calls, inp, created, read, out, cost in rows:
        cost = round(float(cost or 0.0), 4)
        total_cost += cost
        groups.append({
            "call_site": cs, "model": model, "calls": int(calls or 0),
            "input_tokens": int(inp or 0),
            "cache_creation_input_tokens": int(created or 0),
            "cache_read_input_tokens": int(read or 0),
            "output_tokens": int(out or 0),
            "cost_usd": cost,
        })
    return {"days": days, "briefings": int(briefings),
            "total_cost_usd": round(total_cost, 4), "groups": groups}
