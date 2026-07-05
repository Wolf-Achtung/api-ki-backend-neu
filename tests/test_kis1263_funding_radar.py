# -*- coding: utf-8 -*-
"""KIS-1263: Förder-Radar — automatisierte Pflege-Überwachung der
Förderprogramm-Daten.

Tools aktualisieren sich bei jeder Report-Generierung live (Tavily/
Perplexity) — ein veralteter Tool-Preis ist harmlos. Förderquoten und
Fristen sind Zusagen mit finanzieller Tragweite; Web-Recherche ist dort
nicht richtliniensicher. Deshalb: Daten bleiben kuratiert, aber die
ÜBERWACHUNG läuft maschinell — wöchentlicher CI-Job prüft tote Links,
abgelaufene Fristen, Blacklist-Treffer und veraltete verified_at-Stempel
und öffnet bei Befunden automatisch ein Issue.
"""
from __future__ import annotations

import json
from datetime import date

TODAY = date(2026, 7, 5)


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Deterministische Programm-Checks
# =========================================================================

class TestCheckProgram:

    def test_healthy_program_no_findings(self):
        from scripts.funding_radar import check_program
        p = {"title": "Invest BW", "status": "active", "deadline": None,
             "verified_at": "2026-07-01", "url": "https://example.org"}
        assert check_program(p, TODAY, blacklist=["go-digital"]) == []

    def test_expired_deadline_flagged(self):
        from scripts.funding_radar import check_program
        p = {"title": "Altes Programm", "status": "active",
             "deadline": "31.12.2025", "verified_at": "2026-07-01"}
        fs = check_program(p, TODAY, blacklist=[])
        assert any(f["type"] == "expired" for f in fs)

    def test_abgelaufen_marker_flagged(self):
        from scripts.funding_radar import check_program
        p = {"title": "X", "status": "active", "deadline": "ABGELAUFEN",
             "verified_at": "2026-07-01"}
        assert any(f["type"] == "expired" for f in check_program(p, TODAY, blacklist=[]))

    def test_archived_status_is_documented_state(self):
        # status=expired ist ERLEDIGTE Pflege (kuratierte Historie) —
        # der Radar nörgelt nicht dauerhaft über archivierte Einträge.
        from scripts.funding_radar import check_program
        p = {"title": "X", "status": "expired"}
        assert check_program(p, TODAY, blacklist=[]) == []

    def test_unknown_inactive_status_flagged(self):
        from scripts.funding_radar import check_program
        p = {"title": "X", "status": "pausiert", "verified_at": "2026-07-01"}
        assert any(f["type"] == "expired" for f in check_program(p, TODAY, blacklist=[]))

    def test_future_deadline_ok(self):
        from scripts.funding_radar import check_program
        p = {"title": "X", "status": "active", "deadline": "31.12.2026",
             "verified_at": "2026-07-01"}
        assert not any(f["type"] == "expired" for f in check_program(p, TODAY, blacklist=[]))

    def test_blacklisted_program_flagged(self):
        from scripts.funding_radar import check_program
        p = {"name": "go-digital (BMWK)", "status": "active",
             "verified_at": "2026-07-01"}
        fs = check_program(p, TODAY, blacklist=["go-digital"])
        assert any(f["type"] == "blacklisted" for f in fs)

    def test_missing_verified_at_is_stale(self):
        from scripts.funding_radar import check_program
        p = {"title": "X", "status": "active"}
        assert any(f["type"] == "stale" for f in check_program(p, TODAY, blacklist=[]))

    def test_old_verified_at_is_stale(self):
        from scripts.funding_radar import check_program
        p = {"title": "X", "status": "active", "verified_at": "2026-01-01"}
        fs = check_program(p, TODAY, max_age_days=120, blacklist=[])
        assert any(f["type"] == "stale" for f in fs)

    def test_report_renders_findings_table(self):
        from scripts.funding_radar import render_report
        out = render_report([{"type": "expired", "program": "X",
                              "source": "core_2025", "detail": "deadline=alt"}], TODAY)
        assert "1 Befund" in out and "| expired | X |" in out
        # Der Kern der Design-Entscheidung steht im Report
        assert "nicht richtliniensicher" in out.lower() or "NICHT" in out

    def test_report_clean_state(self):
        from scripts.funding_radar import render_report
        assert "Keine Befunde" in render_report([], TODAY)


# =========================================================================
# 2. Datenbestand: Stempel gesetzt, keine Blacklist-Leichen
# =========================================================================

class TestFundingDataHygiene:

    def test_all_core_programs_have_verified_at(self):
        progs = json.load(open("data/funding_programmes_core_2025.json", encoding="utf-8"))
        missing = [p.get("title") for p in progs if not p.get("verified_at")]
        assert missing == [], f"ohne verified_at: {missing}"

    def test_fallback_contains_no_blacklisted_program(self):
        from b25_enforcer import FUNDING_BLACKLIST
        progs = json.load(open("data/funding_programs.json", encoding="utf-8"))
        bl = [t.lower() for t in FUNDING_BLACKLIST]
        offenders = [p["name"] for p in progs
                     if any(t in str(p.get("name", "")).lower() for t in bl)]
        assert offenders == [], f"Blacklist-Programme im Datenbestand: {offenders}"

    def test_radar_runs_clean_on_current_data(self):
        # Der Radar (ohne Netz-Checks) muss auf dem frisch gestempelten
        # Bestand 0 Befunde melden — sonst wäre das Issue-Grundrauschen da.
        from scripts.funding_radar import run_radar
        findings = run_radar(TODAY, check_urls=False, max_age_days=120)
        assert findings == [], findings


# =========================================================================
# 3. CI-Verdrahtung
# =========================================================================

class TestRadarWorkflow:

    def test_workflow_exists_with_cron_and_issue_step(self):
        src = _read(".github/workflows/funding-radar.yml")
        assert "cron:" in src
        assert "workflow_dispatch" in src
        assert "funding_radar.py --check-urls" in src
        assert "gh issue" in src
        assert "issues: write" in src
