# -*- coding: utf-8 -*-
"""KIS-1269: Cookiefreie First-Party-Reichweitenmessung.

Das UX-Audit fand keinerlei Analytics — Absprung-/Abbruchpunkte unbekannt.
Design: keine Cookies, keine IP-Speicherung, keine User-IDs; nur anonyme
Zähl-Events aus einer festen Allowlist; Auswertung nur mit Admin-Key.
"""
from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("STRATEGY_ADMIN_KEY", "test-admin-key")
    # StaticPool-Engine, damit alle Connections dieselbe :memory:-DB sehen
    # (Muster aus test_report_workflow.py)
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool, future=True)
    TestSession = sessionmaker(bind=test_engine, autoflush=False,
                               autocommit=False, future=True)
    import core.db
    import routes.metrics as m
    monkeypatch.setattr(core.db, "engine", test_engine)
    monkeypatch.setattr(core.db, "SessionLocal", TestSession)
    monkeypatch.setattr(m, "SessionLocal", TestSession)
    from models import MetricsEvent
    MetricsEvent.__table__.create(bind=test_engine, checkfirst=True)
    app = FastAPI()
    app.include_router(m.router, prefix="/api")
    return TestClient(app)


class TestTrackEvent:

    def test_allowed_event_stored(self, client):
        r = client.post("/api/metrics/event",
                        content='{"event":"pageview","page":"/","lang":"de","ref":"google.com"}',
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 204
        s = client.get("/api/metrics/summary",
                       params={"admin_key": "test-admin-key", "days": 1})
        assert s.status_code == 200
        counts = s.json()["counts"]
        assert any("pageview" in day for day in counts.values())

    def test_unknown_event_rejected(self, client):
        r = client.post("/api/metrics/event",
                        content='{"event":"steal_pii","page":"/"}',
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 400

    def test_no_pii_fields_stored(self, client):
        # Fremdfelder (z. B. E-Mail) werden schlicht ignoriert — das Modell
        # kennt nur event/page/lang/ref.
        r = client.post("/api/metrics/event",
                        content='{"event":"cta_click","email":"x@y.de","ip":"1.2.3.4"}',
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 204
        from models import MetricsEvent
        cols = {c.name for c in MetricsEvent.__table__.columns}
        assert cols == {"id", "event", "page", "lang", "ref", "created_at"}

    def test_oversized_payload_rejected(self, client):
        r = client.post("/api/metrics/event", content="x" * 3000,
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 413


class TestSummaryAuth:

    def test_summary_requires_admin_key(self, client):
        assert client.get("/api/metrics/summary",
                          params={"admin_key": "falsch"}).status_code == 403

    def test_event_allowlist_is_funnel_only(self):
        from routes.metrics import ALLOWED_EVENTS
        assert "pageview" in ALLOWED_EVENTS
        assert len(ALLOWED_EVENTS) <= 12  # bewusst klein halten
