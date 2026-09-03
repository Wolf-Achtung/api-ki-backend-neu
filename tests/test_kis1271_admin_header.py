# -*- coding: utf-8 -*-
"""KIS-1271: Admin-Key per Header X-Admin-Key statt nur im Query-String.

Am 03.09.2026 scheiterte ein Aufruf mit einem GUELTIGEN Schluessel:
Er enthielt ein "+", und im Query-String wird "+" beim Dekodieren zu
einem Leerzeichen. Der Nutzer sah nur "Ungültiger Admin-Key".

Dazu Issue #984: Query-Parameter landen in Server-Logs, Proxy-Logs,
Browser-Verlauf und Shell-History. Ein Header tut das nicht.

Der Query-Parameter bleibt gueltig — bestehende Aufrufe brechen nicht.
"""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.admin_auth import ADMIN_KEY_ENV, require_admin_key, verify_admin_key

# Ein Schluessel wie der echte: enthaelt genau das Zeichen, das den
# Fehler ausgeloest hat.
KEY_MIT_PLUS = "aB3+xY7/zQ1=kL9mN2pR5sT8vW0dF4gH6jK1lM3nO5pQ7rS9tU"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv(ADMIN_KEY_ENV, KEY_MIT_PLUS)
    app = FastAPI()

    @app.get("/geschuetzt")
    def geschuetzt(_admin: None = Depends(require_admin_key)) -> dict:
        return {"ok": True}

    return TestClient(app)


class TestHeaderWeg:

    def test_header_mit_plus_wird_akzeptiert(self, client):
        """Der Fall, der ueber den Query-String scheiterte."""
        r = client.get("/geschuetzt", headers={"X-Admin-Key": KEY_MIT_PLUS})
        assert r.status_code == 200, r.text

    def test_falscher_header_wird_abgelehnt(self, client):
        r = client.get("/geschuetzt", headers={"X-Admin-Key": "falsch"})
        assert r.status_code == 403

    def test_ohne_alles_abgelehnt(self, client):
        assert client.get("/geschuetzt").status_code == 403


class TestQueryWegBleibtGueltig:
    """Rueckwaertskompatibilitaet: bestehende Aufrufe und Lesezeichen."""

    def test_korrekt_kodierter_query_parameter(self, client):
        r = client.get("/geschuetzt", params={"admin_key": KEY_MIT_PLUS})
        assert r.status_code == 200, r.text

    def test_falscher_query_parameter_abgelehnt(self, client):
        r = client.get("/geschuetzt", params={"admin_key": "falsch"})
        assert r.status_code == 403

    def test_header_gewinnt_gegen_query(self, client):
        r = client.get("/geschuetzt", params={"admin_key": "falsch"},
                       headers={"X-Admin-Key": KEY_MIT_PLUS})
        assert r.status_code == 200

    def test_unkodiertes_plus_im_query_scheitert_weiterhin(self, client):
        """Das ist keine Regression, sondern die Natur des Query-Strings —
        und genau der Grund fuer den Header."""
        r = client.get(f"/geschuetzt?admin_key={KEY_MIT_PLUS}")
        assert r.status_code == 403


class TestFehlendeKonfiguration:

    def test_ohne_env_kommt_500_nicht_403(self, monkeypatch):
        """500 sagt 'Server falsch konfiguriert', 403 'du darfst nicht' —
        die Unterscheidung hat die Diagnose am 03.09. erst ermoeglicht."""
        monkeypatch.delenv(ADMIN_KEY_ENV, raising=False)
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            verify_admin_key("egal")
        assert exc.value.status_code == 500

    def test_leerer_schluessel_wird_abgelehnt(self, monkeypatch):
        monkeypatch.setenv(ADMIN_KEY_ENV, KEY_MIT_PLUS)
        from fastapi import HTTPException

        for wert in ("", None):
            with pytest.raises(HTTPException) as exc:
                verify_admin_key(wert)
            assert exc.value.status_code == 403


class TestKeineZweiteKopieDerPruefung:
    """Vier eigene Kopien waren der Ausgangszustand — jede haette beim
    naechsten Mal anders driften koennen."""

    def test_routes_pruefen_nicht_mehr_selbst(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        eigenbau = []
        for pfad in (repo / "routes").glob("*.py"):
            text = pfad.read_text(encoding="utf-8")
            if 'os.getenv("STRATEGY_ADMIN_KEY"' in text:
                eigenbau.append(pfad.name)
        assert not eigenbau, f"Eigene Admin-Key-Prüfung in: {eigenbau}"

    def test_kein_endpunkt_fordert_den_query_parameter_zwingend(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        pflicht = []
        for pfad in (repo / "routes").glob("*.py"):
            if "admin_key: str = Query(..." in pfad.read_text(encoding="utf-8"):
                pflicht.append(pfad.name)
        assert not pflicht, f"Query-Pflichtparameter noch in: {pflicht}"
