"""
FIX-QW-PROMPT-STABILIZE: Quick Wins Prompt Hardening + SAFE Context + Contract Telemetry

Tests:
- CHANGE 1: Prompt v8.3 structure (no blacklist, no examples, no prices, SAFE refs)
- CHANGE 2: sanitize_for_prompt() deterministic sanitizer + SAFE context fields
- CHANGE 3: ContractResult.repair_llm_used + PASS log telemetry + fail-closed gate
"""
import pytest
import re
import os

# Paths for source inspection
QUICK_WINS_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "de", "quick_wins.md")
HTML_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "html_contract.py")
PROMPT_ENHANCER_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "prompt_enhancer.py")
GPT_ANALYZE_PATH = os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py")


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# =============================================================================
# CHANGE 1: Prompt v8.3 Structure Tests
# =============================================================================

class TestChange1_PromptV83Structure:
    """Prompt v8.3 should have clean structure, no blacklist, no prices."""

    def test_prompt_version_is_v83(self):
        """Prompt should declare v8.3."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "v8.3" in content

    def test_no_hard_blacklist_block(self):
        """No HARD BLACKLIST block should be present."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "HARD BLACKLIST" not in content
        assert "HARD-BLACKLIST" not in content

    def test_no_price_examples(self):
        """No price lists (€/Monat patterns) should be present."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        # Should not have price patterns like "20€/Monat" or "19€/Monat"
        price_pattern = re.compile(r'\d+€/(?:Monat|Nutzer)')
        matches = price_pattern.findall(content)
        assert len(matches) == 0, f"Found price patterns: {matches}"

    def test_no_transformation_examples(self):
        """No transformation examples with time values should be present."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        # Should not have "3h/Woche" or similar time patterns in examples
        assert "spart 3h/Woche" not in content
        assert "6-10 h/Monat" not in content
        assert "6–10 h/Monat" not in content

    def test_no_json_example_block(self):
        """Should not have the long JSON example block from v8.2."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        # The v8.2 had a full example with "Ablauf-Blueprint für Ihre KI-Beratungsprojekte"
        assert "Ablauf-Blueprint" not in content
        assert "Testphase Ihres KI-Fragebogens" not in content

    def test_has_output_vertrag(self):
        """Should have OUTPUT-VERTRAG section."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "## OUTPUT-VERTRAG" in content
        assert "validen JSON-Array" in content

    def test_has_inhalts_vertrag(self):
        """Should have INHALTS-VERTRAG section."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "## INHALTS-VERTRAG" in content
        assert "mindestens vier volle Sätze" in content

    def test_has_zahlen_zeiten_strikt(self):
        """Should have Zahlen & Zeiten (STRIKT) section."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "### Zahlen & Zeiten (STRIKT)" in content
        assert "Keine Ziffern" in content

    def test_has_safe_context_refs(self):
        """Should reference SAFE context variables."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "ZEITERSPARNIS_PRIORITAET_SAFE" in content
        assert "KI_PROJEKTE_SAFE" in content
        assert "VISION_3_JAHRE_SAFE" in content

    def test_has_final_check(self):
        """Should have FINAL CHECK section."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "## FINAL CHECK" in content

    def test_no_hauptleistung_examples(self):
        """Should not have the long HAUPTLEISTUNG examples from v8.2."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "Online-Shop für Büromöbel" not in content
        assert "Steuerberatung für KMU" not in content
        assert "Content-Erstellung und Social Media" not in content

    def test_tool_hinweise_ohne_preise(self):
        """TOOL-HINWEISE should exist but without prices."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "## TOOL-HINWEISE (ohne Preise)" in content
        assert "Perplexity" in content
        assert "ChatGPT" in content
        # No price patterns
        assert "€" not in content

    def test_pflicht_regeln_strikt(self):
        """PFLICHT-REGELN (STRIKT) section should exist."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "## PFLICHT-REGELN (STRIKT)" in content

    def test_sprache_ton_formell(self):
        """Should enforce formal address (Sie)."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "Formelle Anrede" in content
        assert "keine Du-Form" in content

    def test_no_canonical_contract_block(self):
        """The old STRICT CANONICAL CONTRACT comment block should be removed."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert "STRICT CANONICAL CONTRACT" not in content

    def test_jinja2_conditionals_present(self):
        """Should have Jinja2 conditionals for COMPANY_SIZE."""
        content = _read_file(QUICK_WINS_PROMPT_PATH)
        assert '{% if COMPANY_SIZE == "solo" %}' in content
        assert '{% elif COMPANY_SIZE == "team" %}' in content
        assert "{% if ki_projekte %}" in content


# =============================================================================
# CHANGE 2: sanitize_for_prompt() Unit Tests
# =============================================================================

class TestChange2_SanitizeForPrompt:
    """Tests for the sanitize_for_prompt() function."""

    def test_function_exists(self):
        """sanitize_for_prompt should be importable."""
        from services.prompt_enhancer import sanitize_for_prompt
        assert callable(sanitize_for_prompt)

    def test_removes_digits(self):
        """Should remove standalone digits."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Wir sparen 10 Stunden pro Woche")
        assert "10" not in result
        assert "Stunden" not in result  # unit removed with digit

    def test_removes_euro_amounts(self):
        """Should remove Euro amounts."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Budget: 500€ pro Monat")
        assert "500" not in result
        assert "€" not in result

    def test_removes_time_ranges(self):
        """Should remove time ranges."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Zeitersparnis: 6-10 h/Monat durch Automatisierung")
        assert "6" not in result
        assert "10" not in result

    def test_removes_code_fences(self):
        """Should remove code fence markers."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("```json\nsome content\n```")
        assert "```" not in result
        assert "some content" in result

    def test_replaces_rollout(self):
        """Should replace 'Rollout' with 'Einführung'."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Der Rollout startet bald")
        assert "Rollout" not in result
        assert "Einführung" in result

    def test_replaces_skalierung(self):
        """Should replace 'Skalierung' with 'Ausbau'."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Die Skalierung ist geplant")
        assert "Skalierung" not in result
        assert "Ausbau" in result

    def test_replaces_modul(self):
        """Should replace 'Modul' with 'Baustein'."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Das Modul wird integriert")
        assert "Modul" not in result
        assert "Baustein" in result

    def test_replaces_stack(self):
        """Should replace 'Stack' with 'Tool-Set'."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Der Stack umfasst drei Tools")
        assert "Stack" not in result
        assert "Tool-Set" in result

    def test_replaces_zb(self):
        """Should replace 'z. B.' with 'optional'."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("z. B. ChatGPT oder Claude")
        assert "z. B." not in result
        assert "optional" in result

    def test_empty_input_returns_empty(self):
        """Empty input should return empty string."""
        from services.prompt_enhancer import sanitize_for_prompt
        assert sanitize_for_prompt("") == ""
        assert sanitize_for_prompt(None) == ""
        assert sanitize_for_prompt("   ") == ""

    def test_preserves_meaningful_text(self):
        """Should preserve meaningful text without numbers."""
        from services.prompt_enhancer import sanitize_for_prompt
        text = "Automatisierung der Dokumentenerstellung für Beratungsprojekte"
        result = sanitize_for_prompt(text)
        assert "Automatisierung" in result
        assert "Dokumentenerstellung" in result
        assert "Beratungsprojekte" in result

    def test_cleans_double_spaces(self):
        """Should not leave double spaces."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Wir sparen 10 Stunden bei der Arbeit")
        assert "  " not in result

    def test_percentage_removed(self):
        """Should remove percentage patterns."""
        from services.prompt_enhancer import sanitize_for_prompt
        result = sanitize_for_prompt("Effizienzsteigerung um 30% möglich")
        assert "30" not in result


class TestChange2_SafeContextFields:
    """Tests for SAFE context field generation in _build_prompt_vars."""

    def test_safe_fields_in_build_prompt_vars(self):
        """_build_prompt_vars should generate SAFE fields."""
        source = _read_file(GPT_ANALYZE_PATH)
        assert "ZEITERSPARNIS_PRIORITAET_SAFE" in source
        assert "KI_PROJEKTE_SAFE" in source
        assert "VISION_3_JAHRE_SAFE" in source

    def test_safe_log_pattern(self):
        """Should log [FIX-QW-PROMPT][SAFE] with lengths."""
        source = _read_file(GPT_ANALYZE_PATH)
        assert "[FIX-QW-PROMPT][SAFE]" in source
        assert "zeitersparnis_len=" in source
        assert "ki_projekte_len=" in source
        assert "vision_len=" in source

    def test_safe_uses_sanitize_for_prompt(self):
        """SAFE fields should be generated via sanitize_for_prompt."""
        source = _read_file(GPT_ANALYZE_PATH)
        assert "sanitize_for_prompt" in source

    def test_safe_handles_empty_fields(self):
        """SAFE fields should be empty string when original is empty."""
        source = _read_file(GPT_ANALYZE_PATH)
        # Should check if field is truthy before sanitizing
        assert 'if zeitersparnis_prioritaet' in source
        assert 'if ki_projekte' in source
        assert 'if vision_3_jahre' in source


class TestChange2_SanitizerSourcePatterns:
    """Source inspection for sanitizer patterns."""

    def test_sanitizer_function_defined(self):
        """sanitize_for_prompt should be defined in prompt_enhancer.py."""
        source = _read_file(PROMPT_ENHANCER_PATH)
        assert "def sanitize_for_prompt" in source

    def test_sanitizer_removes_backticks(self):
        """Sanitizer should handle backtick/code-fence removal."""
        source = _read_file(PROMPT_ENHANCER_PATH)
        assert "_CODE_FENCE_RE" in source

    def test_sanitizer_removes_digits(self):
        """Sanitizer should remove digits."""
        source = _read_file(PROMPT_ENHANCER_PATH)
        assert "_BARE_DIGITS_RE" in source
        assert "_DIGIT_FRAGMENT_RE" in source

    def test_sanitizer_has_corporate_replacements(self):
        """Sanitizer should have corporate wording replacements."""
        source = _read_file(PROMPT_ENHANCER_PATH)
        assert "_CORPORATE_WORDING_REPLACEMENTS" in source
        assert "Rollout" in source
        assert "Einführung" in source


# =============================================================================
# CHANGE 3: Contract Telemetry + Fail-Closed Gate
# =============================================================================

class TestChange3_ContractResultFields:
    """ContractResult should have repair_llm_used and deterministic_repairs fields."""

    def test_repair_llm_used_field_exists(self):
        """ContractResult should have repair_llm_used field."""
        from services.html_contract import ContractResult
        result = ContractResult(passed=True)
        assert hasattr(result, 'repair_llm_used')
        assert result.repair_llm_used is False

    def test_deterministic_repairs_field_exists(self):
        """ContractResult should have deterministic_repairs field."""
        from services.html_contract import ContractResult
        result = ContractResult(passed=True)
        assert hasattr(result, 'deterministic_repairs')
        assert result.deterministic_repairs == 0

    def test_to_dict_includes_fields(self):
        """to_dict() should include repair_llm_used and deterministic_repairs."""
        from services.html_contract import ContractResult
        result = ContractResult(passed=True, repair_llm_used=True, deterministic_repairs=3)
        d = result.to_dict()
        assert "repair_llm_used" in d
        assert d["repair_llm_used"] is True
        assert "deterministic_repairs" in d
        assert d["deterministic_repairs"] == 3


class TestChange3_PassLogTelemetry:
    """PASS log should include repair_llm_used and deterministic_repairs."""

    def test_pass_log_format(self):
        """PASS log should use [HTML-CONTRACT] PASS repair_llm_used=... format."""
        source = _read_file(HTML_CONTRACT_PATH)
        assert "[HTML-CONTRACT] PASS repair_llm_used=" in source
        assert "deterministic_repairs=" in source

    def test_pass_without_repair(self):
        """Contract pass without repair should log repair_llm_used=false."""
        from services.html_contract import html_contract_validate

        html = """<html><head><title>Test</title></head><body>
        <h1>Report</h1>
        <!-- DEBUG-503D: QUICK_WINS_START -->
        <div class="quick-wins-container" data-qw-json-rendered="true">
            <div class="quick-win quick-win-card-premium">
                <h3>Quick Win 1: Automatisierung der Dokumentenerstellung</h3>
                <p><strong>Problem:</strong> Manuelle Prozesse kosten viel Zeit und Ressourcen im täglichen Betrieb der Beratung.</p>
                <p><strong>Wirkung:</strong> Erhebliche Zeitersparnis durch intelligente Automatisierung der Kernprozesse und Dokumente.</p>
                <p><strong>Umsetzung:</strong> Implementierung von KI-gestützten Workflow-Tools innerhalb kurzer Zeit nach Projektstart.</p>
            </div>
            <div class="quick-win quick-win-card-premium">
                <h3>Quick Win 2: Textverarbeitung und Qualitätssicherung automatisieren</h3>
                <p><strong>Problem:</strong> Lange Bearbeitungszeiten bei der Erstellung von Beratungsdokumenten und Reports.</p>
                <p><strong>Wirkung:</strong> Deutlich schnellere Dokumentenerstellung bei gleichbleibend hoher Qualität und Konsistenz.</p>
                <p><strong>Umsetzung:</strong> Einsatz von KI-Textassistenten für Entwürfe, Reviews und Qualitätsprüfungen im Team.</p>
            </div>
            <div class="quick-win quick-win-card-premium">
                <h3>Quick Win 3: Wissensmanagement und Recherche beschleunigen</h3>
                <p><strong>Problem:</strong> Zeitaufwändige manuelle Recherche und fehlende zentrale Wissensbasis für Projekte.</p>
                <p><strong>Wirkung:</strong> Schnellerer Zugriff auf relevantes Wissen und konsistente Informationsgrundlage.</p>
                <p><strong>Umsetzung:</strong> Aufbau einer KI-gestützten Wissensdatenbank mit automatischer Indexierung und Suche.</p>
            </div>
        </div>
        <!-- DEBUG-503D: QUICK_WINS_END -->
        </body></html>"""

        result = html_contract_validate(html, strict_mode=False, allow_repair=False)
        assert result.passed is True
        assert result.repair_llm_used is False
        assert result.deterministic_repairs == 0


class TestChange3_FailClosedGate:
    """Fail-closed gate: repair_llm_used=true in STRICT should raise."""

    def test_fail_closed_gate_source_pattern(self):
        """Should have fail-closed gate for repair_llm_used in STRICT."""
        source = _read_file(HTML_CONTRACT_PATH)
        assert "FIX-QW-PROMPT-STABILIZE" in source
        assert "repair_llm_used" in source
        assert "strict_no_repair_llm" in source or "FAIL-CLOSED repair_llm_used=true" in source

    def test_strict_prevents_llm_repair(self):
        """In STRICT mode, LLM repair should not be attempted."""
        source = _read_file(HTML_CONTRACT_PATH)
        # Phase 2 should be guarded by not is_strict
        phase2_match = re.search(
            r'# Phase 2.*?_attempt_llm_repair',
            source,
            re.DOTALL
        )
        assert phase2_match is not None
        phase2_section = phase2_match.group()
        assert "not is_strict" in phase2_section

    def test_deterministic_repair_tracked(self):
        """Deterministic repairs should be counted."""
        source = _read_file(HTML_CONTRACT_PATH)

        # Find the Phase 1 section
        phase1_match = re.search(
            r'# Phase 1: Deterministic repair.*?# Phase 2',
            source,
            re.DOTALL
        )
        assert phase1_match is not None
        phase1_section = phase1_match.group()

        assert "deterministic_repairs" in phase1_section

    def test_llm_repair_sets_flag(self):
        """LLM repair should set repair_llm_used = True."""
        source = _read_file(HTML_CONTRACT_PATH)

        # Find Phase 2 section
        phase2_match = re.search(
            r'# Phase 2.*?# FIX-QW-PROMPT-STABILIZE',
            source,
            re.DOTALL
        )
        assert phase2_match is not None
        phase2_section = phase2_match.group()

        assert "repair_llm_used = True" in phase2_section


class TestChange3_DeterministicRepairPass:
    """Deterministic repair should produce correct telemetry."""

    def test_code_fence_deterministic_repair_pass(self):
        """Code fences fixed by deterministic repair should show repair_llm_used=false."""
        from services.html_contract import html_contract_validate

        # HTML with code fences that deterministic repair can fix
        html = """```html
<html><head><title>Test</title></head><body>
<h1>Report</h1>
<!-- DEBUG-503D: QUICK_WINS_START -->
<div class="quick-wins-container" data-qw-json-rendered="true">
    <div class="quick-win quick-win-card-premium">
        <h3>Quick Win 1: Prozessautomatisierung für Beratungsunternehmen</h3>
        <p><strong>Problem:</strong> Manuelle Erstellung von Beratungsdokumenten und Analyseberichten ist zeitaufwändig und fehleranfällig. Die Qualität variiert je nach Bearbeiter und Tagesform. Kunden erwarten konsistente, professionelle Ergebnisse in kurzer Zeit.</p>
        <p><strong>Wirkung:</strong> Deutliche Zeitersparnis bei der Dokumentenerstellung durch automatisierte Vorlagen und KI-Unterstützung. Konsistente Qualität über alle Projekte hinweg. Mehr Zeit für wertschöpfende Beratungstätigkeit.</p>
        <p><strong>Umsetzung:</strong> Starten Sie mit einem KI-Textassistenten wie Claude oder ChatGPT für erste Entwürfe. Erstellen Sie Vorlagen für wiederkehrende Dokumenttypen. Definieren Sie Qualitätsstandards und prüfen Sie Ergebnisse systematisch.</p>
    </div>
    <div class="quick-win quick-win-card-premium">
        <h3>Quick Win 2: Wissensmanagement und Recherche optimieren</h3>
        <p><strong>Problem:</strong> Projektrelevantes Wissen ist verstreut gespeichert und schwer auffindbar. Neue Mitarbeiter brauchen lange Einarbeitungszeit. Best Practices gehen zwischen Projekten verloren und werden nicht systematisch weitergegeben.</p>
        <p><strong>Wirkung:</strong> Schneller Zugriff auf gesammeltes Projektwissen und bewährte Methoden. Kürzere Einarbeitungszeiten für neue Teammitglieder. Konsistentere Beratungsqualität durch geteiltes Wissen.</p>
        <p><strong>Umsetzung:</strong> Richten Sie eine zentrale Wissensdatenbank ein, etwa mit Notion oder Obsidian. Nutzen Sie KI-Suche für schnelles Retrieval. Etablieren Sie einen Prozess zur Wissensdokumentation nach Projektabschluss.</p>
    </div>
    <div class="quick-win quick-win-card-premium">
        <h3>Quick Win 3: Kundenkommunikation und Follow-up strukturieren</h3>
        <p><strong>Problem:</strong> Follow-up-Termine und Kundenkommunikation werden manuell nachverfolgt. Wichtige Kontaktpunkte gehen verloren. Die Reaktionszeit auf Kundenanfragen ist inkonsistent und manchmal zu lang.</p>
        <p><strong>Wirkung:</strong> Systematische Kundennachverfolgung ohne manuelle Erinnerungen. Professionellere Kommunikation durch Vorlagen und Automatisierung. Bessere Kundenbindung durch zeitnahe Reaktionen.</p>
        <p><strong>Umsetzung:</strong> Implementieren Sie automatische Erinnerungen für Follow-ups in Ihrem CRM oder Kalender. Erstellen Sie E-Mail-Vorlagen für häufige Kommunikationsanlässe. Nutzen Sie KI für die Zusammenfassung von Gesprächsnotizen.</p>
    </div>
</div>
<!-- DEBUG-503D: QUICK_WINS_END -->
</body></html>
```"""

        result = html_contract_validate(html, strict_mode=False, allow_repair=True)

        # Deterministic repair should fix code fences
        assert result.passed is True
        assert result.repair_llm_used is False
        assert result.deterministic_repairs > 0
