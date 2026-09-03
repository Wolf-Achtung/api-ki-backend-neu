# -*- coding: utf-8 -*-
"""KIS-1265: Wächter-Jobs außerhalb der Pipeline.

Drei Dinge müssen hier fest bleiben:
1. Die Radare ändern nie Daten und laufen ohne Schlüssel unverändert
   weiter (Tavily ist Zusatz, kein Muss).
2. Recherche-Kandidaten sind als ungeprüft gekennzeichnet und kosten
   höchstens eine Suche je betroffenem Eintrag.
3. Der Mail-Helfer schweigt ohne Secrets, statt den Job rot zu färben.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TODAY = date(2026, 9, 3)


# =========================================================================
# 1. Förder-Radar: Tavily-Kandidaten
# =========================================================================

class TestFundingRadarKandidaten:

    def test_ohne_schluessel_keine_kandidaten_und_kein_netz(self):
        from scripts.funding_radar import collect_candidates
        aufrufe = []
        out = collect_candidates(
            [{"title": "Invest BW", "status": "active"}],
            [{"type": "dead_url", "program": "Invest BW", "detail": "x"}],
            api_key="", year=2026, search=lambda *a, **k: aufrufe.append(a) or [],
        )
        assert out == {}
        assert aufrufe == []

    def test_nur_programme_mit_befund_werden_gesucht(self):
        from scripts.funding_radar import collect_candidates
        gesucht = []

        def fake(name, year, key):
            gesucht.append(name)
            return [{"title": f"Neu zu {name}", "url": "https://example.org/a"}]

        programme = [
            {"title": "Invest BW", "status": "active"},
            {"title": "ZIM", "status": "active"},
            {"title": "Digitalbonus Bayern", "status": "expired"},
        ]
        befunde = [{"type": "stale", "program": "Invest BW", "detail": "x"},
                   {"type": "dead_url", "program": "Digitalbonus Bayern", "detail": "y"}]
        out = collect_candidates(programme, befunde, api_key="k", year=2026, search=fake)
        assert gesucht == ["Invest BW"]          # ZIM ohne Befund, Digitalbonus archiviert
        assert list(out) == ["Invest BW"]

    def test_scan_all_nimmt_alle_aktiven(self):
        from scripts.funding_radar import collect_candidates
        gesucht = []
        programme = [{"title": "A", "status": "active"}, {"title": "B", "status": "active"},
                     {"title": "C", "status": "discontinued"}]
        collect_candidates(programme, [], api_key="k", year=2026, scan_all=True,
                           search=lambda n, y, k: gesucht.append(n) or [])
        assert gesucht == ["A", "B"]

    def test_suchanfrage_nennt_programm_jahr_und_frist(self):
        from scripts.funding_radar import build_candidate_query
        q = build_candidate_query("Invest BW – Digitalisierung & KI", 2026)
        assert "Invest BW" in q and "2026" in q and "Frist" in q
        assert "–" not in q  # Gedankenstriche bereinigt

    def test_tavily_fail_open_bei_netzfehler(self, monkeypatch):
        import scripts.funding_radar as fr

        class _Boom:
            def post(self, *a, **k):
                raise RuntimeError("netz weg")

        monkeypatch.setitem(sys.modules, "requests", _Boom())
        assert fr.tavily_candidates("Invest BW", 2026, "key") == []

    def test_report_kennzeichnet_kandidaten_als_ungeprueft(self):
        from scripts.funding_radar import render_report
        befunde = [{"type": "stale", "program": "Invest BW", "source": "core_2025",
                    "detail": "verified_at=2026-01-01 (> 120 Tage)"}]
        kandidaten = {"Invest BW": [{"title": "Neue Runde 2026", "url": "https://example.org/x"}]}
        md = render_report(befunde, TODAY, kandidaten)
        assert "Recherche-Kandidaten (Tavily, ungeprüft)" in md
        assert "**1 Kandidat(en)**" in md
        assert "[Neue Runde 2026](https://example.org/x)" in md
        # Der bisherige Befund-Teil bleibt unverändert
        assert "**1 Befund(e)**" in md

    def test_report_ohne_kandidaten_unveraendert(self):
        from scripts.funding_radar import render_report
        befunde = [{"type": "stale", "program": "X", "source": "core_2025", "detail": "d"}]
        assert render_report(befunde, TODAY) == render_report(befunde, TODAY, {})


# =========================================================================
# 2. Tool-Radar
# =========================================================================

class TestToolsRadar:

    def test_nie_verifiziert_ist_befund(self):
        from scripts.tools_radar import check_tool
        f = check_tool({"name": "Tally.so", "price": "0–29 €/Monat"}, TODAY)
        assert len(f) == 1 and f[0]["type"] == "stale"
        assert "nie verifiziert" in f[0]["detail"]

    def test_frisch_verifiziert_kein_befund(self):
        from scripts.tools_radar import check_tool
        assert check_tool({"name": "X", "verified_at": "2026-08-20"}, TODAY) == []

    def test_alt_verifiziert_ist_befund(self):
        from scripts.tools_radar import check_tool
        f = check_tool({"name": "X", "verified_at": "2026-01-01"}, TODAY, max_age_days=120)
        assert f and f[0]["type"] == "stale"

    def test_kandidaten_begrenzt_und_nur_bei_befund(self):
        from scripts.tools_radar import collect_candidates
        gesucht = []
        befunde = [{"type": "stale", "tool": f"T{i}", "detail": "d"} for i in range(20)]
        befunde.append({"type": "dead_url", "tool": "T0", "detail": "doppelt"})
        collect_candidates([], befunde, api_key="k", year=2026, limit=12,
                           search=lambda n, y, k: gesucht.append(n) or [])
        assert len(gesucht) == 12
        assert gesucht.count("T0") == 1

    def test_echte_seed_datei_laesst_sich_pruefen(self):
        from scripts.tools_radar import load_tools, run_radar
        tools = load_tools()
        assert len(tools) >= 20
        befunde = run_radar(TODAY)  # ohne Netz
        assert all(f["type"] == "stale" for f in befunde)

    def test_report_form(self):
        from scripts.tools_radar import render_report
        md = render_report([{"type": "stale", "tool": "Notion", "detail": "d"}], TODAY)
        assert md.startswith("# 🧰 Tool-Radar — 2026-09-03")
        assert "**1 Befund(e)**" in md
        assert "| stale | Notion | d |" in md


# =========================================================================
# 3. Mail-Helfer
# =========================================================================

class TestNotifyMail:

    def test_markdown_tabelle_wird_html(self):
        from scripts.notify_mail import markdown_to_html
        md = "# Titel\n\n**2 Befund(e)**\n\n| Typ | Tool |\n|---|---|\n| stale | Notion |\n"
        out = markdown_to_html(md)
        assert "<h2>Titel</h2>" in out
        assert "<strong>2 Befund(e)</strong>" in out
        assert "<th" in out and "<td" in out and "Notion" in out

    def test_links_werden_klickbar_und_html_entkommen(self):
        from scripts.notify_mail import markdown_to_html
        out = markdown_to_html("- <b>x</b> https://example.org/a")
        assert "&lt;b&gt;" in out
        assert '<a href="https://example.org/a">' in out

    def test_has_findings(self):
        from scripts.notify_mail import has_findings
        assert has_findings("**3 Befund(e)** — bitte prüfen")
        assert has_findings("**2 Kandidat(en)**")
        assert not has_findings("✅ Keine Befunde")

    def test_ohne_secrets_exit_0_ohne_netz(self, tmp_path, monkeypatch):
        for var in ("RESEND_API_KEY", "RESEND_FROM", "ADMIN_NOTIFY_EMAIL"):
            monkeypatch.delenv(var, raising=False)
        f = tmp_path / "r.md"
        f.write_text("**1 Befund(e)**", encoding="utf-8")
        r = subprocess.run([sys.executable, str(REPO / "scripts" / "notify_mail.py"),
                            "--subject", "t", "--file", str(f)],
                           capture_output=True, text=True, cwd=REPO)
        assert r.returncode == 0
        assert "übersprungen" in r.stdout


# =========================================================================
# 4. News-Entwurf: ohne Schlüssel grün, nie rot
# =========================================================================

class TestNewsDraftSkript:

    def test_ohne_tavily_key_exit_0(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        r = subprocess.run([sys.executable, str(REPO / "scripts" / "news_draft.py"),
                            "--out", str(tmp_path / "d.html")],
                           capture_output=True, text=True, cwd=REPO,
                           env={"PATH": "/usr/bin:/bin:/usr/local/bin"})
        assert r.returncode == 0, r.stderr[-500:]
        assert "TAVILY_API_KEY fehlt" in r.stdout
        assert not (tmp_path / "d.html").exists()


# =========================================================================
# 5. Workflows: gültiges YAML, richtige Skripte, keine Railway-Berührung
# =========================================================================

class TestWorkflows:

    @pytest.mark.parametrize("name,script", [
        ("news-draft.yml", "scripts/news_draft.py"),
        ("funding-radar.yml", "scripts/funding_radar.py"),
        ("tools-radar.yml", "scripts/tools_radar.py"),
    ])
    def test_workflow_ruft_skript_und_hat_cron(self, name, script):
        import yaml
        text = (REPO / ".github" / "workflows" / name).read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        # PyYAML liest den Schlüssel `on` als True
        on = data.get("on") or data.get(True)
        assert "schedule" in on and "workflow_dispatch" in on
        assert script in text
        # Keine Produktions-URL, kein Aufruf des blockierenden Endpunkts —
        # Kommentare erklären das, zählen aber nicht.
        code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
        assert "railway.app" not in code
        assert "/api/content/research-news" not in code
        assert "curl" not in code

    def test_radare_weisen_dem_inhaber_zu_und_mailen(self):
        for name in ("funding-radar.yml", "tools-radar.yml"):
            text = (REPO / ".github" / "workflows" / name).read_text(encoding="utf-8")
            assert "--assignee" in text or "--add-assignee" in text
            assert "scripts/notify_mail.py" in text
