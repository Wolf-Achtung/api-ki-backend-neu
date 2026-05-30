# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5-H2: vendor_audit_engine akzeptiert strategy_answers-Param.

KIS-1199 zeigte: Perplexity in Strategy s5_software, fehlt aber im R1
Vendor-Audit. Diagnose: briefing.answers enthält zu R1-Generation-Time
keine Strategy-Daten. Sprint-1027.4-2D fügte zwar s5_software als
source_key hinzu, hatte aber keinen Effekt, weil kein Caller die
Strategy-Daten in briefing merged.

Wolf-Decision (Sprint 1027.5-H2): Audit-Pfad strategy_answers
durchreichen. Defensive API-Erweiterung: Caller, die Briefing+Strategy
gemerged haben, können sie übergeben — generate_vendor_audit_report
und _extract_vendors_from_briefing nehmen optional strategy_answers
entgegen und mergen NICHT-zerstörend.

R1-Initialgeneration bleibt unverändert (kein Caller passiert
strategy_answers). Künftige Re-Render-Pfade (z. B. /api/strategy/admin/
r1-re-render nach Chat-Abschluss) können den Param setzen und damit
Perplexity & andere Strategy-only-Tools im Audit sehen.
"""
from __future__ import annotations

from services.vendor_audit_engine import (
    _extract_vendors_from_briefing,
    generate_vendor_audit_report,
)


def test_extract_vendors_without_strategy_baseline():
    """Baseline: Briefing allein, ohne strategy_answers — Perplexity nur via
    s5_software, das hier in briefing direkt steht."""
    briefing = {
        "vorhandene_tools": "ChatGPT, Notion AI, Claude",
    }
    vendors = _extract_vendors_from_briefing(briefing)
    names = sorted(v["name"] for v in vendors)
    assert "ChatGPT (OpenAI)" in names
    assert "Claude (Anthropic)" in names
    assert "Notion AI" in names
    # Perplexity nicht in briefing → fehlt erwartungsgemäß
    assert "Perplexity AI" not in names


def test_strategy_answers_merge_adds_perplexity():
    """Wenn strategy_answers Perplexity via s5_software liefert, taucht es
    in der Vendor-Liste auf."""
    briefing = {
        "vorhandene_tools": "ChatGPT, Notion AI, Claude",
    }
    strategy = {
        "s5_software": "ChatGPT, Claude, Perplexity, GitHub Copilot",
    }
    vendors = _extract_vendors_from_briefing(briefing, strategy_answers=strategy)
    names = sorted(v["name"] for v in vendors)
    assert "Perplexity AI" in names, f"Perplexity nicht gemerged: {names}"
    # Tools aus beiden Quellen vorhanden
    assert "ChatGPT (OpenAI)" in names
    assert "Claude (Anthropic)" in names
    assert "Notion AI" in names
    # GitHub Copilot (per "copilot"-Alias)
    assert "Microsoft Copilot" in names


def test_strategy_answers_does_not_overwrite_briefing():
    """Strategy-Werte dürfen Briefing-Werte NICHT überschreiben (nur leere
    Felder füllen). Sicherheit: caller-Briefing bleibt unverändert."""
    briefing = {
        "vorhandene_tools": "OnlyBriefingTool",
    }
    strategy = {
        "vorhandene_tools": "OnlyStrategyTool",  # darf nicht überschreiben
        "s5_software": "Perplexity",
    }
    vendors = _extract_vendors_from_briefing(briefing, strategy_answers=strategy)
    names = sorted(v["name"] for v in vendors)
    # Perplexity über s5_software (briefing hatte das Feld nicht)
    assert "Perplexity AI" in names
    # OnlyStrategyTool wurde nicht in vorhandene_tools gemerged (briefing
    # hatte schon "OnlyBriefingTool", non-empty)
    # Keine assert für unbekannte Tools, da sie ohnehin nicht in
    # _KNOWN_VENDOR_META sind. Indirekt: briefing-Dict ist nicht mutiert:
    assert briefing == {"vorhandene_tools": "OnlyBriefingTool"}


def test_generate_vendor_audit_report_accepts_strategy_answers_param():
    """API-Erweiterung: generate_vendor_audit_report akzeptiert den neuen
    Param ohne Fehler (defensive Caller-Sicherheit)."""
    briefing = {"vorhandene_tools": "ChatGPT", "unternehmensgroesse": "solo"}
    strategy = {"s5_software": "Perplexity"}
    report = generate_vendor_audit_report(
        briefing=briefing,
        strategy_answers=strategy,
    )
    # Report ist gerendert, hat Vendor-Einträge
    assert report is not None
    vendor_names = [e.name for e in report.entries]
    assert any("Perplexity" in n for n in vendor_names), (
        f"Perplexity nicht im Audit, vendors={vendor_names}"
    )
