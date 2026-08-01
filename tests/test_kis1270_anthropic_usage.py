# -*- coding: utf-8 -*-
"""KIS-1270: Anthropic-Usage-Persistenz + cache-korrekte Kostenrechnung.

Vorfragen-Diagnose vom 01.08.2026: Es gab KEINE Kostenerfassung und keine
DB-Senke — die [CACHE-USAGE]-Logzeilen rollten mit der Railway-Retention
weg. Dieser Baustein persistiert jede Zeile und rechnet die Kosten von
Anfang an cache-korrekt (creative-radar-Lektion: input_tokens allein
untertreibt, sobald Caching greift):
  total_input = input*1,00 + cache_write*1,25 + cache_read*0,10  (x Basispreis)
"""
from __future__ import annotations

import pytest


# =========================================================================
# 1. Kostenrechnung — exakt die F1-Fehlerklasse aus creative-radar
# =========================================================================

class TestCostEstimate:

    def test_all_three_input_fields_priced(self):
        from services.anthropic_client import estimate_anthropic_cost_usd
        # Sonnet (3/15 je MTok): 1000 regulaer + 2000 write + 10000 read
        cost = estimate_anthropic_cost_usd("claude-sonnet-5", 1000, 2000, 10000, 500)
        expected = (1000*1.0 + 2000*1.25 + 10000*0.10) * 3.0/1e6 + 500 * 15.0/1e6
        assert cost == pytest.approx(expected, abs=1e-9)

    def test_input_tokens_alone_would_undercount(self):
        # Der creative-radar-Fehler haette hier 1000*3/1e6 gerechnet —
        # unsere Schaetzung MUSS darueberliegen, sobald Cache-Felder > 0.
        from services.anthropic_client import estimate_anthropic_cost_usd
        naive = 1000 * 3.0 / 1e6
        assert estimate_anthropic_cost_usd("claude-sonnet-5", 1000, 2000, 10000, 0) > naive

    def test_cache_read_is_cheaper_than_regular(self):
        from services.anthropic_client import estimate_anthropic_cost_usd
        regular = estimate_anthropic_cost_usd("claude-sonnet-5", 10000, 0, 0, 0)
        cached = estimate_anthropic_cost_usd("claude-sonnet-5", 0, 0, 10000, 0)
        assert cached == pytest.approx(regular * 0.10, rel=1e-6)

    def test_model_price_lookup(self):
        from services.anthropic_client import _price_for_model
        assert _price_for_model("claude-opus-4-8") == (5.0, 25.0)
        assert _price_for_model("claude-sonnet-5") == (3.0, 15.0)
        assert _price_for_model("claude-haiku-4-5-20251001") == (1.0, 5.0)
        # Unbekannt -> konservativ Sonnet
        assert _price_for_model("unbekannt") == (3.0, 15.0)

    def test_price_override_via_env(self, monkeypatch):
        from services.anthropic_client import _price_for_model
        monkeypatch.setenv("ANTHROPIC_PRICES_JSON", '{"opus": [15, 75]}')
        assert _price_for_model("claude-opus-4-8") == (15.0, 75.0)


# =========================================================================
# 2. Persistenz ueber log_anthropic_usage (fail-open, eigene Session)
# =========================================================================

class _FakeUsage:
    input_tokens = 111
    cache_creation_input_tokens = 222
    cache_read_input_tokens = 333
    output_tokens = 44

class _FakeMessage:
    usage = _FakeUsage()


@pytest.fixture()
def usage_db(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool, future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    import core.db
    monkeypatch.setattr(core.db, "SessionLocal", Session)
    from models import AnthropicUsage
    AnthropicUsage.__table__.create(bind=engine, checkfirst=True)
    return Session


class TestPersistence:

    def test_log_call_writes_row(self, usage_db):
        from services.anthropic_client import log_anthropic_usage
        from models import AnthropicUsage
        log_anthropic_usage(_FakeMessage(), call_site="call_anthropic:risks",
                            model="claude-opus-4-8")
        db = usage_db()
        row = db.query(AnthropicUsage).one()
        assert row.call_site == "call_anthropic:risks"
        assert (row.input_tokens, row.cache_creation_input_tokens,
                row.cache_read_input_tokens, row.output_tokens) == (111, 222, 333, 44)
        assert row.cost_usd > 0
        db.close()

    def test_flag_disables_persistence(self, usage_db, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_USAGE_DB", "0")
        from services.anthropic_client import log_anthropic_usage
        from models import AnthropicUsage
        log_anthropic_usage(_FakeMessage(), call_site="x", model="m")
        db = usage_db()
        assert db.query(AnthropicUsage).count() == 0
        db.close()

    def test_db_failure_never_breaks_call(self, monkeypatch):
        # SessionLocal wirft -> log_anthropic_usage darf NICHT raisen
        import core.db
        def _boom():
            raise RuntimeError("db down")
        monkeypatch.setattr(core.db, "SessionLocal", _boom)
        from services.anthropic_client import log_anthropic_usage
        log_anthropic_usage(_FakeMessage(), call_site="x", model="m")  # kein Raise


# =========================================================================
# 3. Admin-Endpoint
# =========================================================================

class TestUsageSummaryEndpoint:

    def test_requires_admin_key(self, monkeypatch):
        monkeypatch.setenv("STRATEGY_ADMIN_KEY", "k")
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import routes.metrics as m
        app = FastAPI()
        app.include_router(m.router, prefix="/api")
        c = TestClient(app)
        assert c.get("/api/metrics/anthropic-usage",
                     params={"admin_key": "falsch"}).status_code == 403

    def test_aggregates_by_call_site_and_model(self, usage_db, monkeypatch):
        monkeypatch.setenv("STRATEGY_ADMIN_KEY", "k")
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import routes.metrics as m
        monkeypatch.setattr(m, "SessionLocal", usage_db)
        from models import AnthropicUsage, Briefing
        Briefing.__table__.create(bind=usage_db().get_bind(), checkfirst=True)
        db = usage_db()
        for _ in range(3):
            db.add(AnthropicUsage(call_site="call_anthropic:risks",
                                  model="claude-opus-4-8", input_tokens=100,
                                  cache_creation_input_tokens=0,
                                  cache_read_input_tokens=2700,
                                  output_tokens=50, cost_usd=0.01))
        db.commit(); db.close()
        app = FastAPI()
        app.include_router(m.router, prefix="/api")
        c = TestClient(app)
        r = c.get("/api/metrics/anthropic-usage", params={"admin_key": "k", "days": 7})
        assert r.status_code == 200
        data = r.json()
        assert data["total_cost_usd"] == pytest.approx(0.03, abs=1e-6)
        g = data["groups"][0]
        assert g["calls"] == 3 and g["cache_read_input_tokens"] == 8100
        assert "briefings" in data
