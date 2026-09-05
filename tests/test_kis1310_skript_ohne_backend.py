# -*- coding: utf-8 -*-
"""KIS-1310 — Das Testlauf-Skript läuft ohne Backend-Abhängigkeiten.

Erster Lauf auf Wolfs Mac (05.09.2026): ``ModuleNotFoundError: No module
named 'fastapi'`` — das Skript importierte ``routes.admin_testrun`` und damit
die ganze App. Jetzt liegt die Prüfung in ``services/profil_pruefung.py``
(nur Standardbibliothek plus ``services.chat_normalizer``); der Endpunkt
re-exportiert sie. Der Test sperrt FastAPI, Pydantic, SQLAlchemy und die
App-Settings beim Import und erwartet trotzdem eine saubere Prüfung.
"""
from __future__ import annotations

import builtins
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFILE = sorted((ROOT / "data" / "test_profiles_gold").glob("*_testlauf.json"))
GESPERRT = ("fastapi", "pydantic", "sqlalchemy", "starlette", "httpx", "requests",
            "anthropic", "openai", "settings", "config", "models", "db", "routes")


@pytest.fixture
def ohne_backend(monkeypatch):
    """Importe der Backend-Abhängigkeiten schlagen fehl wie auf einem Rechner ohne venv."""
    echt = builtins.__import__

    def gesperrt(name, *a, **k):
        if name.split(".")[0] in GESPERRT:
            raise ModuleNotFoundError(f"No module named {name!r}")
        return echt(name, *a, **k)

    for mod in list(sys.modules):
        if mod.split(".")[0] in ("services.profil_pruefung",):
            monkeypatch.delitem(sys.modules, mod)
    monkeypatch.setattr(builtins, "__import__", gesperrt)
    yield


@pytest.mark.parametrize("pfad", PROFILE, ids=[p.stem for p in PROFILE])
def test_pruefung_ohne_fastapi(ohne_backend, pfad):
    from services.profil_pruefung import profil_pruefen
    d = json.loads(pfad.read_text(encoding="utf-8"))
    assert profil_pruefen(d["answers"], d["strategy_answers"]) == []


def test_pruefung_findet_fehler_ohne_fastapi(ohne_backend):
    from services.profil_pruefung import profil_pruefen
    d = json.loads(PROFILE[0].read_text(encoding="utf-8"))
    a = dict(d["answers"])
    a["bundesland"] = "bayern"
    a.pop("hauptleistung")
    fehler = profil_pruefen(a, None)
    assert any("bundesland" in f for f in fehler)
    assert any("hauptleistung" in f for f in fehler)


def test_modul_importiert_kein_fastapi():
    src = (ROOT / "services" / "profil_pruefung.py").read_text(encoding="utf-8")
    importe = [z.strip() for z in src.splitlines() if z.strip().startswith(("import ", "from "))]
    for verboten in ("fastapi", "pydantic", "sqlalchemy", "settings", "models"):
        assert not any(verboten in z for z in importe), verboten
    # routes.strategy nur im try-Block (FB2), nie auf Modulebene
    assert "from routes.strategy import" in src and src.index("try:") < src.index("from routes.strategy import")


def test_endpunkt_reexportiert():
    from routes import admin_testrun
    from services import profil_pruefung
    assert admin_testrun.profil_pruefen is profil_pruefung.profil_pruefen
    assert admin_testrun._FB2_FELDER == profil_pruefung.FB2_FELDER


def test_skript_check_laeuft_mit_nackter_standardbibliothek():
    """Startet das Skript in einem Python ohne site-packages (-S, -I): nur
    Standardbibliothek. ``--check`` muss durchlaufen und den FB2-Hinweis zeigen."""
    p = subprocess.run(
        [sys.executable, "-I", "-S", "scripts/testlauf_profil.py",
         str(PROFILE[0].relative_to(ROOT)), "--check"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    assert "Profil geprüft" in p.stdout
    assert "FastAPI fehlt lokal" in p.stdout
    assert "Traceback" not in p.stderr
