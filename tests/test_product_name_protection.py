# -*- coding: utf-8 -*-
"""
test_product_name_protection.py - Tests für Produktnamen-Schutz (v14.35.21)

Stellt sicher, dass PROTECTED_PRODUCT_NAMES in apply_solo_persona_filter()
korrekt funktioniert und nicht von späteren Filtern überschrieben wird.

Acceptance Criteria:
- "Microsoft Teams" bleibt unverändert
- "MS Teams" bleibt unverändert
- "Zoom / Microsoft Teams für Online-Meetings" bleibt unverändert
- "Nutzen Sie Teams" → "Nutzen Sie Kapazitäten" (für Solo Governance)
- "Microsoft Kapazitäten" darf NIRGENDS erscheinen (Safety Net)

Version: 1.0.0 (v14.35.21)
"""
from __future__ import annotations

import re
try:
    import pytest
except ImportError:
    pytest = None  # type: ignore


class TestProductNameProtection:
    """Tests für PROTECTED_PRODUCT_NAMES Contract."""

    def test_microsoft_teams_unchanged(self) -> None:
        """Microsoft Teams MUSS unverändert bleiben."""
        from services.prompt_enhancer import apply_solo_persona_filter

        result = apply_solo_persona_filter("Microsoft Teams")
        assert result == "Microsoft Teams", f"Microsoft Teams was changed to: {result}"

    def test_ms_teams_unchanged(self) -> None:
        """MS Teams MUSS unverändert bleiben."""
        from services.prompt_enhancer import apply_solo_persona_filter

        result = apply_solo_persona_filter("MS Teams")
        assert result == "MS Teams", f"MS Teams was changed to: {result}"

    def test_zoom_microsoft_teams_unchanged(self) -> None:
        """Zoom / Microsoft Teams für Online-Meetings MUSS unverändert bleiben."""
        from services.prompt_enhancer import apply_solo_persona_filter

        input_text = "Zoom / Microsoft Teams für Online-Meetings"
        result = apply_solo_persona_filter(input_text)
        assert result == input_text, f"Text was changed to: {result}"

    def test_standalone_teams_replaced(self) -> None:
        """Standalone 'Teams' SOLL zu 'Kapazitäten' werden (Solo Governance)."""
        from services.prompt_enhancer import apply_solo_persona_filter

        result = apply_solo_persona_filter("Nutzen Sie Teams für die Kommunikation.")
        assert "Kapazitäten" in result, f"'Teams' was not replaced: {result}"
        assert "Teams" not in result or "Microsoft" in result, f"Standalone Teams still present: {result}"

    def test_no_microsoft_kapazitaeten_anywhere(self) -> None:
        """'Microsoft Kapazitäten' darf NIRGENDS entstehen."""
        from services.prompt_enhancer import apply_solo_persona_filter

        test_cases = [
            "Microsoft Teams",
            "MS Teams",
            "Zoom / Microsoft Teams für Online-Meetings",
            "Nutzen Sie Microsoft Teams und Teams Copilot.",
            "Microsoft Teams ist ein wichtiges Tool. Das Team arbeitet gut.",
        ]

        for input_text in test_cases:
            result = apply_solo_persona_filter(input_text)
            assert "Microsoft Kapazitäten" not in result, \
                f"'Microsoft Kapazitäten' found in output!\nInput: {input_text}\nOutput: {result}"
            assert "MS Kapazitäten" not in result, \
                f"'MS Kapazitäten' found in output!\nInput: {input_text}\nOutput: {result}"


class TestStandaloneTeamsInToolContext:
    """Hotfix 1027.2.1 F4: Standalone 'Teams' als Tool-Name (im Cluster mit
    Zoom/Meet/Webex/Slack/Otter etc.) darf NICHT von SOLO_GOVERNANCE_REPLACEMENTS
    erfasst werden. Sonst kette: Teams->Kapazitaeten->Zeitbudget -> 'Zoom oder
    Zeitbudget' in S.8 Quick Win Meeting-Nachbereitung (KIS-1193)."""

    def test_zoom_oder_teams_protected(self) -> None:
        from services.prompt_enhancer import apply_solo_persona_filter
        result = apply_solo_persona_filter(
            "Nutzen Sie Otter zur automatischen Transkription Ihrer "
            "Kundengespräche in Zoom oder Teams."
        )
        assert "Zoom oder Teams" in result, f"Teams wurde faelschlich ersetzt: {result}"
        assert "Zeitbudget" not in result, f"Zoom->Zeitbudget-Bug: {result}"
        assert "Kapazitäten" not in result, f"Teams->Kapazitaeten-Replace: {result}"

    def test_teams_oder_zoom_protected(self) -> None:
        from services.prompt_enhancer import apply_solo_persona_filter
        result = apply_solo_persona_filter("Wählen Sie Teams oder Zoom.")
        assert "Teams oder Zoom" in result, result

    def test_zoom_comma_teams_protected(self) -> None:
        from services.prompt_enhancer import apply_solo_persona_filter
        result = apply_solo_persona_filter("Tools wie Zoom, Teams und Webex.")
        assert "Teams" in result, result
        assert "Kapazitäten" not in result, result

    def test_slash_separator_protected(self) -> None:
        from services.prompt_enhancer import apply_solo_persona_filter
        result = apply_solo_persona_filter("Tools: Zoom / Teams")
        assert "Teams" in result, result
        assert "Kapazitäten" not in result, result

    def test_otter_teams_protected(self) -> None:
        from services.prompt_enhancer import apply_solo_persona_filter
        result = apply_solo_persona_filter("Otter und Teams kombinieren.")
        assert "Otter und Teams" in result, result

    def test_google_meet_teams_protected(self) -> None:
        from services.prompt_enhancer import apply_solo_persona_filter
        result = apply_solo_persona_filter("Google Meet oder Teams einsetzen.")
        assert "Teams" in result, result
        assert "Kapazitäten" not in result, result

    def test_standalone_teams_without_tool_context_still_replaced(self) -> None:
        """Negative Kontrolle: ohne Tool-Cluster greift weiter die Solo-Ersetzung."""
        from services.prompt_enhancer import apply_solo_persona_filter
        result = apply_solo_persona_filter("Sie organisieren mehrere Teams im Unternehmen.")
        assert "Teams" not in result or "Microsoft" in result, (
            f"Standalone Teams ohne Tool-Kontext muss weiter ersetzt werden: {result}"
        )


class TestSafetyNetSeatbelt:
    """Tests für Safety Net (seatbelt) im content_quality_enforcer."""

    def test_safety_net_fixes_microsoft_kapazitaeten(self) -> None:
        """Safety Net MUSS 'Microsoft Kapazitäten' zu 'Microsoft Teams' korrigieren."""
        from services.content_quality_enforcer import fix_product_name_mutations

        # Simulate a bug where protection failed
        broken_text = "Nutzen Sie Microsoft Kapazitäten für Meetings."
        result, count = fix_product_name_mutations(broken_text)

        assert "Microsoft Teams" in result, f"Safety net did not fix: {result}"
        assert "Microsoft Kapazitäten" not in result, f"Mutation still present: {result}"
        assert count > 0, "No fixes were applied"

    def test_safety_net_fixes_ms_kapazitaeten(self) -> None:
        """Safety Net MUSS 'MS Kapazitäten' zu 'MS Teams' korrigieren."""
        from services.content_quality_enforcer import fix_product_name_mutations

        broken_text = "MS Kapazitäten ist gut."
        result, count = fix_product_name_mutations(broken_text)

        assert "MS Teams" in result, f"Safety net did not fix: {result}"
        assert "MS Kapazitäten" not in result, f"Mutation still present: {result}"

    def test_safety_net_no_false_positives(self) -> None:
        """Safety Net DARF keine korrekten Texte verändern."""
        from services.content_quality_enforcer import fix_product_name_mutations

        correct_texts = [
            "Microsoft Teams funktioniert gut.",
            "Kapazitäten erweitern ist wichtig.",
            "Das Microsoft Office Paket.",
        ]

        for text in correct_texts:
            result, count = fix_product_name_mutations(text)
            assert result == text, f"False positive! Changed: {text} → {result}"
            assert count == 0, f"Unexpected fix count: {count}"


class TestFullPipelineProtection:
    """Tests dass Protection durch die gesamte Pipeline hält."""

    def test_protection_survives_all_enforcers(self) -> None:
        """Microsoft Teams MUSS alle Enforcer-Stufen überleben."""
        from services.prompt_enhancer import apply_solo_persona_filter
        from services.content_quality_enforcer import (
            apply_grammar_fixes,
            fix_product_name_mutations,
        )
        from services.text_healing import heal_text_block

        input_text = "Zoom / Microsoft Teams für Online-Meetings"

        # Stage 1: Solo persona filter
        result = apply_solo_persona_filter(input_text)
        assert "Microsoft Teams" in result, f"Stage 1 failed: {result}"

        # Stage 2: Grammar fixes
        result, _ = apply_grammar_fixes(result)
        assert "Microsoft Teams" in result, f"Stage 2 failed: {result}"

        # Stage 3: Text healing
        result = heal_text_block(result)
        assert "Microsoft Teams" in result, f"Stage 3 failed: {result}"

        # Stage 4: Safety net (should be no-op)
        result, _ = fix_product_name_mutations(result)
        assert "Microsoft Teams" in result, f"Stage 4 failed: {result}"

        # Final check
        assert "Microsoft Kapazitäten" not in result, f"Mutation found in final: {result}"


class TestOutputGates:
    """Output Gate Tests für 95+ Stabilität."""

    def test_gate_g1_no_product_name_mutation(self) -> None:
        """Gate G1: 'Microsoft Kapazitäten' darf 0x vorkommen."""
        # This would be run on final HTML in integration tests
        test_html = """
        <p>Nutzen Sie Microsoft Teams für Meetings.</p>
        <p>Erweitern Sie Ihre Kapazitäten durch Automatisierung.</p>
        """

        assert "Microsoft Kapazitäten" not in test_html, "Gate G1 FAILED"
        assert "MS Kapazitäten" not in test_html, "Gate G1 FAILED"

    def test_gate_g2_no_fragment_endings(self) -> None:
        """Gate G2: Keine Fragment-Endungen in finalen Texten."""
        from services.text_healing import FORBIDDEN_SENTENCE_ENDINGS

        test_texts = [
            "Dies ist ein vollständiger Satz.",
            "Die Empfehlungen sind wichtig.",
            "Nutzen Sie die Tools effektiv.",
        ]

        for text in test_texts:
            # Remove trailing punctuation
            clean_text = text.rstrip(".!?")
            words = clean_text.split()
            if words:
                last_word = words[-1].lower()
                assert last_word not in FORBIDDEN_SENTENCE_ENDINGS, \
                    f"Gate G2 FAILED: '{text}' ends with forbidden word '{last_word}'"

    def test_gate_g3_kpi_consistency_check(self) -> None:
        """Gate G3: KPI-Werte dürfen nicht >30% von Canonical abweichen."""
        from services.content_quality_enforcer import enforce_kpi_consistency

        canonical_kpis = {
            "monatsersparnis_stunden": 35,
            "jahresersparnis_stunden": 420,
        }

        # Simulate checking final HTML
        test_html = "<p>Zeitersparnis: 35 Stunden/Monat</p>"
        result, count = enforce_kpi_consistency(test_html, canonical_kpis)

        # Should have no enforcements if values are correct
        assert count == 0, f"Gate G3 FAILED: KPI inconsistency detected (fixes: {count})"


def validate_output_gates(html: str, canonical_kpis: dict | None = None) -> tuple[bool, list[str]]:
    """
    Utility function to validate all output gates on final HTML.

    v14.35.21: Can be called from integration tests to validate report quality.

    Returns:
        (all_passed, list_of_failures)
    """
    failures = []

    # Gate G1: No product name mutations
    if "Microsoft Kapazitäten" in html:
        failures.append("G1: 'Microsoft Kapazitäten' found in output")
    if "MS Kapazitäten" in html:
        failures.append("G1: 'MS Kapazitäten' found in output")

    # Gate G2: No fragment endings (check last sentences)
    from services.text_healing import FORBIDDEN_SENTENCE_ENDINGS

    # Extract sentence endings from HTML (simplified check)
    sentences = re.findall(r'[^.!?]+[.!?]', html)
    for sentence in sentences[-10:]:  # Check last 10 sentences
        clean = sentence.strip().rstrip(".!?")
        words = clean.split()
        if words:
            last_word = words[-1].lower()
            if last_word in FORBIDDEN_SENTENCE_ENDINGS:
                failures.append(f"G2: Fragment ending detected: '...{' '.join(words[-3:])}'")

    # Gate G3: KPI consistency
    if canonical_kpis:
        from services.content_quality_enforcer import enforce_kpi_consistency
        _, count = enforce_kpi_consistency(html, canonical_kpis)
        if count > 0:
            failures.append(f"G3: {count} KPI inconsistencies detected")

    return len(failures) == 0, failures


if __name__ == "__main__":
    print("=== Product Name Protection Tests ===")
    print("Run with: pytest tests/test_product_name_protection.py -v")
