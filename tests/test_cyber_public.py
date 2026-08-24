# -*- coding: utf-8 -*-
"""KIS-1263: oeffentlicher Cyberangriffs-Check ohne Login.

Der Endpunkt ist von aussen erreichbar — die Tests decken deshalb nicht
nur den Normalfall ab, sondern auch die Missbrauchswege: fremde Adressen,
Skript-Einsendungen, geraten Tokens, doppelte Klicks.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")

_LANGSAM_GENUG = 60_000  # ms; ueber der Mindest-Ausfuellzeit


def _alle_antworten(default=2, **overrides):
    from services.resilienz_score import all_question_ids
    a = {qid: default for qid in all_question_ids("de")}
    a.update(overrides)
    return a


def _treiber(default=2, **overrides):
    from services.resilienz_score import REAKTIONSLUECKE_FIELDS
    a = {f: default for f in REAKTIONSLUECKE_FIELDS}
    a.update(overrides)
    return a


@pytest.fixture
def client(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    import sys

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    import core.db
    original_session, original_engine = core.db.SessionLocal, core.db.engine
    core.db.SessionLocal = TestSessionLocal
    core.db.engine = test_engine

    from core.db import Base
    from models import Analysis, Briefing, User  # noqa: F401

    Base.metadata.create_all(bind=test_engine)

    for key in list(sys.modules.keys()):
        if key.startswith("routes") or key == "main":
            del sys.modules[key]
    from main import app
    from routes._bootstrap import get_db

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Keine echten Mails, keine echte Generierung im Test.
    versendet = []
    import routes.cyber_public as cyber
    monkeypatch.setattr(cyber, "_sende_bestaetigungsmail",
                        lambda email, bid: versendet.append((email, bid)))
    import services.resilienz_pipeline as pipeline
    monkeypatch.setattr(pipeline, "generate_resilienz_report", lambda bid: None)

    test_client = TestClient(app)
    test_client._sessionmaker = TestSessionLocal
    test_client._versendet = versendet
    try:
        yield test_client
    finally:
        core.db.SessionLocal = original_session
        core.db.engine = original_engine
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
        for key in list(sys.modules.keys()):
            if key.startswith("routes") or key == "main":
                sys.modules.pop(key, None)


class TestKurzcheck:
    """Fuenf Fragen, sofortiges Ergebnis, ohne Login und ohne Speichern."""

    def test_fragen_ohne_login_abrufbar(self, client):
        r = client.get("/api/cyber/kurzfragen")
        assert r.status_code == 200
        data = r.json()
        assert [q["id"] for q in data["questions"]] == ["B2", "C1", "C2", "C3", "C4"]
        assert data["benchmark_minuten"] == 15

    def test_min_regel_bestimmt_das_band(self, client):
        # Vier Antworten auf Stufe 4, eine auf Stufe 1 -> schlechtestes Band.
        r = client.post("/api/cyber/kurzcheck",
                        json={"answers": _treiber(4, C3=1), "ms": _LANGSAM_GENUG})
        assert r.status_code == 200
        data = r.json()
        assert data["label"] == "mehr als 8 Stunden"
        assert data["min_stufe"] == 1
        assert [t["id"] for t in data["treiber"]] == ["C3"]

    def test_bestwert_ergibt_bestes_band(self, client):
        r = client.post("/api/cyber/kurzcheck",
                        json={"answers": _treiber(4), "ms": _LANGSAM_GENUG})
        assert r.json()["label"] == "unter 15 Minuten"

    def test_kurzcheck_speichert_nichts(self, client):
        client.post("/api/cyber/kurzcheck",
                    json={"answers": _treiber(3), "ms": _LANGSAM_GENUG})
        from models import Briefing
        db = client._sessionmaker()
        try:
            assert db.query(Briefing).count() == 0
        finally:
            db.close()

    def test_fremde_felder_abgelehnt(self, client):
        a = _treiber(3)
        a["A1"] = 2
        r = client.post("/api/cyber/kurzcheck", json={"answers": a, "ms": _LANGSAM_GENUG})
        assert r.status_code == 422


class TestBotschutz:

    def test_honigtopf_gefuellt_wird_abgewiesen(self, client):
        r = client.post("/api/cyber/kurzcheck",
                        json={"answers": _treiber(3), "hp": "spam", "ms": _LANGSAM_GENUG})
        assert r.status_code == 422

    def test_zu_schnell_ausgefuellt_wird_abgewiesen(self, client):
        r = client.post("/api/cyber/kurzcheck", json={"answers": _treiber(3), "ms": 40})
        assert r.status_code == 422

    def test_vollreport_verlangt_laengere_zeit(self, client):
        r = client.post("/api/cyber/anfordern", json={
            "answers": _alle_antworten(), "email": "bot@example.com",
            "einwilligung": True, "ms": 4_000,
        })
        assert r.status_code == 422


class TestAnforderung:

    def _anfordern(self, client, email="kunde@example.com", **extra):
        payload = {
            "answers": _alle_antworten(), "email": email,
            "einwilligung": True, "ms": _LANGSAM_GENUG,
        }
        payload.update(extra)
        return client.post("/api/cyber/anfordern", json=payload)

    def test_erzeugt_unbestaetigten_vorgang_ohne_report(self, client):
        r = self._anfordern(client)
        assert r.status_code == 202
        from models import Briefing
        db = client._sessionmaker()
        try:
            row = db.query(Briefing).first()
            assert row.status == "unconfirmed"
            assert row.report_type == "resilienz"
            assert row.source == "cyber_public"
        finally:
            db.close()
        assert client._versendet, "Bestätigungsmail wurde nicht ausgelöst"

    def test_ohne_einwilligung_422(self, client):
        assert self._anfordern(client, einwilligung=False).status_code == 422

    def test_unvollstaendige_antworten_422(self, client):
        a = _alle_antworten()
        del a["F1"]
        assert self._anfordern(client, answers=a).status_code == 422

    def test_kein_login_durch_oeffentliche_anfrage(self, client):
        # Ein User-Datensatz entsteht, aber der Zugang haengt an der
        # Whitelist — die oeffentliche Anfrage darf sie nicht aufweichen.
        self._anfordern(client, email="fremder@example.com")
        from core.whitelist import is_whitelisted
        assert not is_whitelisted("fremder@example.com")


class TestBestaetigung:

    def _anfordern_und_id(self, client):
        client.post("/api/cyber/anfordern", json={
            "answers": _alle_antworten(), "email": "kunde@example.com",
            "einwilligung": True, "ms": _LANGSAM_GENUG,
        })
        return client._versendet[-1][1]

    def test_gueltiger_link_startet_generierung(self, client):
        from routes.cyber_public import _token_fuer
        bid = self._anfordern_und_id(client)
        r = client.get(f"/api/cyber/bestaetigen?b={bid}&t={_token_fuer(bid)}")
        assert r.status_code == 200
        assert "wird erstellt" in r.text

        from models import Briefing
        db = client._sessionmaker()
        try:
            assert db.query(Briefing).filter(Briefing.id == bid).first().status == "accepted"
        finally:
            db.close()

    def test_falscher_token_wird_abgewiesen(self, client):
        bid = self._anfordern_und_id(client)
        r = client.get(f"/api/cyber/bestaetigen?b={bid}&t={'a' * 32}")
        assert r.status_code == 403

        from models import Briefing
        db = client._sessionmaker()
        try:
            assert db.query(Briefing).filter(Briefing.id == bid).first().status == "unconfirmed"
        finally:
            db.close()

    def test_token_gilt_nicht_fuer_fremden_vorgang(self, client):
        from routes.cyber_public import _token_fuer
        bid = self._anfordern_und_id(client)
        assert client.get(
            f"/api/cyber/bestaetigen?b={bid + 1}&t={_token_fuer(bid)}"
        ).status_code == 403

    def test_zweiter_klick_erzeugt_keinen_zweiten_report(self, client):
        from routes.cyber_public import _token_fuer
        bid = self._anfordern_und_id(client)
        url = f"/api/cyber/bestaetigen?b={bid}&t={_token_fuer(bid)}"
        assert client.get(url).status_code == 200
        zweiter = client.get(url)
        assert zweiter.status_code == 200
        assert "schon benutzt" in zweiter.text


class TestWorkerBleibtUnberuehrt:

    def test_unbestaetigte_vorgaenge_werden_nie_geclaimt(self, client):
        # Der Worker holt nur report_type='r1' — ein unbestaetigter
        # Cyber-Vorgang darf nie in die r1-Pipeline laufen.
        client.post("/api/cyber/anfordern", json={
            "answers": _alle_antworten(), "email": "kunde@example.com",
            "einwilligung": True, "ms": _LANGSAM_GENUG,
        })
        from workers.briefings_worker import claim_next_briefing
        db = client._sessionmaker()
        try:
            assert claim_next_briefing(db) is None
        finally:
            db.close()
