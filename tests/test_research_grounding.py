# -*- coding: utf-8 -*-
"""Tests für services.research_grounding (KIS-PROMPT P1)."""
from __future__ import annotations

from services import research_grounding as rg


def _fake_blocks() -> dict:
    return {
        "TOOLS_TABLE_HTML": (
            "<table><tr><th>Tool</th><th>Preis</th></tr>"
            "<tr><td>Beispiel-Assistent Pro</td><td>20 €/Monat</td></tr>"
            "<tr><td>DACH-Suite</td><td>49 €/Monat</td></tr></table>"
        ),
        "FUNDING_TABLE_HTML": "<ul><li>Digital-Zuschuss Berlin: bis 50%</li></ul>",
        "MARKET_INSIGHTS_HTML": "<p>KI-Adoption im Beratungsmarkt steigt.</p>",
        "NEWS_BOX_HTML": "",
        "last_updated": "2026-07-01",
    }


def test_grounding_built_for_expected_sections(monkeypatch):
    monkeypatch.setattr(
        "services.research_pipeline.run_research", lambda answers: _fake_blocks()
    )
    out = rg.build_research_grounding({"branche": "beratung"})
    assert set(out) == {
        "tools_empfehlungen", "foerderpotenzial",
        "wettbewerb_benchmark", "unternehmensprofil_markt",
    }
    tools = out["tools_empfehlungen"]
    assert "LIVE-RECHERCHE-KONTEXT" in tools
    assert "Beispiel-Assistent Pro" in tools and "20 €/Monat" in tools
    assert "Stand: 2026-07-01" in tools
    # HTML wurde zu Klartext
    assert "<table>" not in tools and "<td>" not in tools


def test_grounding_fail_open_on_research_error(monkeypatch):
    def _boom(answers):
        raise RuntimeError("provider down")
    monkeypatch.setattr("services.research_pipeline.run_research", _boom)
    assert rg.build_research_grounding({}) == {}


def test_grounding_disabled_via_env(monkeypatch):
    monkeypatch.setenv("RESEARCH_GROUNDING_ENABLED", "0")
    called = {"n": 0}
    def _count(answers):
        called["n"] += 1
        return _fake_blocks()
    monkeypatch.setattr("services.research_pipeline.run_research", _count)
    assert rg.build_research_grounding({}) == {}
    assert called["n"] == 0


def test_grounding_caps_length(monkeypatch):
    big = "<ul>" + "".join(
        f"<li>Programm {i}: Beschreibung mit einigen Wörtern</li>" for i in range(500)
    ) + "</ul>"
    blocks = _fake_blocks()
    blocks["FUNDING_TABLE_HTML"] = big
    monkeypatch.setattr(
        "services.research_pipeline.run_research", lambda answers: blocks
    )
    monkeypatch.setenv("RESEARCH_GROUNDING_MAX_CHARS", "1500")
    out = rg.build_research_grounding({})
    funding = out["foerderpotenzial"]
    assert len(funding) < 2600  # 1500 Inhalt + Rahmen/Anweisungen
    assert "gekürzt" in funding


def test_empty_research_yields_no_grounding(monkeypatch):
    monkeypatch.setattr(
        "services.research_pipeline.run_research",
        lambda answers: {"TOOLS_TABLE_HTML": "", "last_updated": ""},
    )
    assert rg.build_research_grounding({}) == {}
