# -*- coding: utf-8 -*-
"""Resilienz V1: API- und Pipeline-Tests (Route, Auth, Rendering, Sprachregeln)."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")


def _valid_answers(default=3, **overrides):
    from services.resilienz_score import all_question_ids
    a = {qid: default for qid in all_question_ids("de")}
    a.update(overrides)
    return a


@pytest.fixture
def client():
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
    original_session = core.db.SessionLocal
    original_engine = core.db.engine
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
    test_client = TestClient(app)
    test_client._sessionmaker = TestSessionLocal  # fuer Tests
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
                if key in sys.modules:
                    del sys.modules[key]


@pytest.fixture
def auth_headers():
    from core.security import create_access_token
    token = create_access_token("wolf@test.de")
    return {"Authorization": f"Bearer {token}"}


class TestSubmitValidation:

    def test_ohne_login_401(self, client):
        r = client.post("/api/resilienz/submit", json={"answers": _valid_answers()})
        assert r.status_code == 401

    def test_unvollstaendig_422(self, client, auth_headers):
        a = _valid_answers()
        del a["C2"]
        r = client.post("/api/resilienz/submit", json={"answers": a}, headers=auth_headers)
        assert r.status_code == 422
        assert "C2" in r.text

    def test_unbekanntes_feld_422(self, client, auth_headers):
        a = _valid_answers()
        a["firma"] = 2
        r = client.post("/api/resilienz/submit", json={"answers": a}, headers=auth_headers)
        assert r.status_code == 422

    def test_stufe_ausserhalb_422(self, client, auth_headers):
        r = client.post(
            "/api/resilienz/submit",
            json={"answers": _valid_answers(B2=7)},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_nur_de_422(self, client, auth_headers):
        r = client.post(
            "/api/resilienz/submit",
            json={"lang": "en", "answers": _valid_answers()},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_submit_erzeugt_typisiertes_briefing(self, client, auth_headers, monkeypatch):
        import services.resilienz_pipeline as pipeline
        monkeypatch.setattr(pipeline, "generate_resilienz_report", lambda bid: None)
        r = client.post(
            "/api/resilienz/submit", json={"answers": _valid_answers()}, headers=auth_headers,
        )
        assert r.status_code == 202
        bid = r.json()["briefing_id"]

        from models import Briefing
        db = client._sessionmaker()
        try:
            row = db.query(Briefing).filter(Briefing.id == bid).first()
            assert row.report_type == "resilienz"
            assert row.status in ("accepted", "processing", "done")
            assert set(row.answers.keys()) == set(_valid_answers().keys())
        finally:
            db.close()


class TestKatalogEndpoint:

    def test_katalog_braucht_login(self, client):
        assert client.get("/api/resilienz/katalog").status_code == 401

    def test_katalog_liefert_22_fragen_ohne_gewichte(self, client, auth_headers):
        r = client.get("/api/resilienz/katalog", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data["blocks"]) == 6
        assert sum(len(b["questions"]) for b in data["blocks"]) == 22
        # Gewichte/Scoring-Interna bleiben serverseitig
        assert "weight" not in str(data)


class TestOwnership:

    def test_fremder_check_403(self, client, auth_headers, monkeypatch):
        import services.resilienz_pipeline as pipeline
        monkeypatch.setattr(pipeline, "generate_resilienz_report", lambda bid: None)
        r = client.post(
            "/api/resilienz/submit", json={"answers": _valid_answers()}, headers=auth_headers,
        )
        bid = r.json()["briefing_id"]

        from core.security import create_access_token
        other = {"Authorization": f"Bearer {create_access_token('angreifer@test.de')}"}
        assert client.get(f"/api/resilienz/status/{bid}", headers=other).status_code == 403
        assert client.get(f"/api/resilienz/html/{bid}", headers=other).status_code == 403


class TestPipelineRendering:
    """render_resilienz_html ohne LLM (fail-open) und ohne DB."""

    def _render(self, monkeypatch, answers):
        import services.resilienz_pipeline as pipeline
        monkeypatch.setattr(pipeline, "_llm_section", lambda *a, **k: None)

        class _B:
            id = 4711
            lang = "de"
        _B.answers = answers
        return pipeline.render_resilienz_html(_B())

    def test_html_enthaelt_kernbausteine(self, monkeypatch):
        out = self._render(monkeypatch, _valid_answers(4, B2=1))
        html = out["html"]
        assert "geschätzte Reaktionslücke auf Basis Ihrer Angaben" in html
        assert "mehr als 8 Stunden" in html
        assert "<svg" in html  # Zeitstrahl + Radar
        assert "Selbstauskunft" in html
        assert "Cyberangriffs-Check" in html  # Produktname (Wolfs Wahl, 2026-08-23)
        assert "KI-Resilienz-Check" not in html
        assert out["meta"]["scores"]["reaktionsluecke"]["min_stufe"] == 1

    def test_deckelregel_sichtbar(self, monkeypatch):
        out = self._render(monkeypatch, _valid_answers(4, C1=1, C2=1, C3=1, C4=1, C5=1))
        assert "organisatorische Obergrenze" in out["html"]
        assert out["meta"]["scores"]["gedeckelt"] is True

    def test_keine_verbotenen_zusicherungen(self, monkeypatch):
        from services.resilienz_pipeline import FORBIDDEN_ASSURANCES
        out = self._render(monkeypatch, _valid_answers(2))
        lowered = out["html"].lower()
        for phrase in FORBIDDEN_ASSURANCES:
            assert phrase.lower() not in lowered

    def test_en_wird_abgelehnt_kein_stilles_downgrade(self, monkeypatch):
        import services.resilienz_pipeline as pipeline

        class _B:
            id = 4712
            lang = "en"
            answers = _valid_answers()

        with pytest.raises(ValueError, match="nur DE"):
            pipeline.render_resilienz_html(_B())

    def test_fallback_befunde_nicht_repetitiv(self, monkeypatch):
        # KIS-1259: 6x derselbe Satz -> jetzt schwaechste Angabe je Block
        out = self._render(monkeypatch, _valid_answers(2, F1=1, F2=1, F3=1))
        html = out["html"]
        assert html.count("den größten Abstand") <= 1
        assert "NIS2 sagt mir nichts" in html  # schwaechste Angabe Block F

    def test_footer_und_zeitstrahl_kis1259(self, monkeypatch):
        # Zeitstrahl-Label liegt im viewBox (Balken 400, Text ab 410)
        out = self._render(monkeypatch, _valid_answers(4, B2=1))
        assert 'x="410"' in out["html"]
        assert 'x="530"' not in out["html"]

    def test_betriebskontext_auf_seite_1(self, monkeypatch):
        # KIS-1260: r1-Kontext personalisiert Kopfzeile und LLM-Vars
        import services.resilienz_pipeline as pipeline
        captured = {}

        def fake_llm(section, vars_dict, lang, max_tokens=900):
            captured[section] = dict(vars_dict)
            return None

        monkeypatch.setattr(pipeline, "_llm_section", fake_llm)

        class _B:
            id = 4713
            lang = "de"
            answers = _valid_answers()

        out = pipeline.render_resilienz_html(
            _B(), r1_kontext={"branche": "Medien & Kreativwirtschaft",
                              "sparte": "Postproduktion/VFX/Animation",
                              "hauptleistung": "Postproduktion für Werbefilme"},
        )
        assert "Medien &amp; Kreativwirtschaft (Postproduktion/VFX/Animation)" in out["html"]
        assert "Postproduktion für Werbefilme" in captured["resilienz_kernaussage"]["betriebskontext"]

    def test_ohne_kontext_unveraendert(self, monkeypatch):
        out = self._render(monkeypatch, _valid_answers(3))
        assert "aus dem KI-Status-Check" not in out["html"]

    def test_kein_firmenname_im_report(self, monkeypatch):
        # Invariante: Der Check erhebt keinen Firmennamen — im HTML darf
        # kein Feld/Label danach fragen.
        out = self._render(monkeypatch, _valid_answers(3))
        assert "Firmenname" not in out["html"]
        assert "firma" not in out["html"].lower()
