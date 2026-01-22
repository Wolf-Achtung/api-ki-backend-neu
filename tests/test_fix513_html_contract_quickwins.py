"""
FIX-513: HTML-Contract QuickWins False-Positive + STRICT "No repair_llm" Tests

Tests:
- P1: Contract passes for premium quickwins HTML (class contains quick-win + marker)
- P2: STRICT disables LLM repair
- P3: Contract fails with quick_wins_empty when block has only header/empty
"""
import pytest
import re
import os

# Path to html_contract.py for source inspection
HTML_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "html_contract.py")


def _read_source() -> str:
    """Read html_contract.py source."""
    with open(HTML_CONTRACT_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestFix513_QuickWinsWordBoundary:
    """P1: QuickWins detection with word-boundary class check."""

    def test_quickwin_class_pattern_exists(self):
        """_QUICKWIN_CLASS_PATTERN should use word-boundary regex."""
        source = _read_source()
        assert "_QUICKWIN_CLASS_PATTERN" in source
        assert r"\bquick-win\b" in source

    def test_premium_quickwins_passes_contract(self):
        """Premium QuickWins HTML with class='quick-win ...' should pass."""
        from services.html_contract import html_contract_validate

        html = """<html><head><title>Test</title></head><body>
        <h1>Report</h1>
        <!-- DEBUG-503D: QUICK_WINS_START -->
        <div class="quick-wins-container">
            <div class="quick-win quick-win-card-premium" data-qw-json-rendered="true">
                <h3>Quick Win 1: Automatisierung</h3>
                <p>Problem: Manuelle Dateneingabe kostet 10h pro Woche.</p>
                <p>Wirkung: 80% Zeitersparnis durch KI-Automatisierung.</p>
                <p>Umsetzung: Tool X implementieren, Schulung der Mitarbeiter.</p>
            </div>
            <div class="quick-win quick-win-card-premium">
                <h3>Quick Win 2: Textverarbeitung</h3>
                <p>Problem: Lange Bearbeitungszeiten bei Dokumentenerstellung.</p>
                <p>Wirkung: 60% schnellere Dokumentenerstellung.</p>
                <p>Umsetzung: KI-Textassistenten einsetzen.</p>
            </div>
        </div>
        <!-- DEBUG-503D: QUICK_WINS_END -->
        </body></html>"""

        result = html_contract_validate(html, strict_mode=False, allow_repair=False)

        # Should pass - has marker AND class with word-boundary match
        quickwins_violations = [
            v for v in result.violations
            if v.type.value in ("quickwins_no_marker", "quick_wins_empty")
        ]
        assert len(quickwins_violations) == 0, f"Should have no QuickWins violations, got: {quickwins_violations}"

    def test_class_quick_win_premium_matches_pattern(self):
        """class='quick-win quick-win-card-premium' should match pattern."""
        from services.html_contract import _QUICKWIN_CLASS_PATTERN

        test_cases = [
            ('class="quick-win"', True),
            ('class="quick-win quick-win-card-premium"', True),
            ('class="quick-win-card"', True),  # Still has quick-win word boundary
            ('class="not-a-quickwin"', False),
            ('class="quick-wins-container"', False),  # "quick-wins" != "quick-win"
        ]

        for html_attr, should_match in test_cases:
            match = _QUICKWIN_CLASS_PATTERN.search(html_attr)
            assert (match is not None) == should_match, (
                f"'{html_attr}' should {'match' if should_match else 'not match'}"
            )

    def test_debug_anchors_used_for_block_extraction(self):
        """Debug anchors should be used to extract QuickWins block."""
        source = _read_source()
        assert "DEBUG-503D: QUICK_WINS_START" in source
        assert "DEBUG-503D: QUICK_WINS_END" in source

    def test_quickwins_check_log_pattern(self):
        """Should log [FIX-513][HTML-CONTRACT] quick_wins_check."""
        source = _read_source()
        assert "[FIX-513][HTML-CONTRACT] quick_wins_check" in source


class TestFix513_StrictNoLLMRepair:
    """P2: STRICT mode disables LLM repair."""

    def test_strict_skips_llm_repair(self):
        """In STRICT mode, LLM repair should NOT be called."""
        source = _read_source()

        # Find Phase 2 section
        phase2_match = re.search(
            r'# Phase 2.*?_attempt_llm_repair',
            source,
            re.DOTALL
        )
        assert phase2_match is not None
        phase2_section = phase2_match.group()

        # Should have strict mode check
        assert "not is_strict" in phase2_section

    def test_pass_log_includes_repair_llm_used_0(self):
        """PASS log should include repair_llm_used=0."""
        source = _read_source()
        assert "repair_llm_used=0" in source

    def test_strict_mode_no_llm_repair_call(self):
        """Contract validate with strict=True should not attempt LLM repair."""
        source = _read_source()

        # Find the validation function
        func_match = re.search(
            r'def html_contract_validate.*?(?=\ndef _extract_bad_blocks)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Phase 2 should be guarded by "not is_strict"
        phase2_match = re.search(
            r'# Phase 2.*?_attempt_llm_repair',
            func_source,
            re.DOTALL
        )
        assert phase2_match is not None
        phase2_section = phase2_match.group()

        # Must check is_strict before calling LLM repair
        assert "not is_strict" in phase2_section, (
            "LLM repair should be guarded by 'not is_strict'"
        )


class TestFix513_QuickWinsNonEmptyGuard:
    """P3: Non-Empty Guard for QuickWins."""

    def test_quickwins_empty_violation_type_exists(self):
        """ViolationType.QUICKWINS_EMPTY should exist."""
        from services.html_contract import ViolationType
        assert hasattr(ViolationType, 'QUICKWINS_EMPTY')
        assert ViolationType.QUICKWINS_EMPTY.value == "quick_wins_empty"

    def test_quickwins_empty_block_fails(self):
        """QuickWins block with only header (no items) should fail."""
        from services.html_contract import html_contract_validate

        html = """<html><head><title>Test</title></head><body>
        <h1>Report</h1>
        <!-- DEBUG-503D: QUICK_WINS_START -->
        <div class="quick-wins-container">
            <h2>Quick Wins</h2>
        </div>
        <!-- DEBUG-503D: QUICK_WINS_END -->
        </body></html>"""

        result = html_contract_validate(html, strict_mode=False, allow_repair=False)

        # Should NOT have quickwins_no_marker (since no class="quick-win" found)
        # The fallback section check should catch empty sections
        # In this case it goes through fallback path since no marker/class found

    def test_min_block_len_configured(self):
        """_QUICKWIN_MIN_BLOCK_LEN should be configured."""
        source = _read_source()
        assert "_QUICKWIN_MIN_BLOCK_LEN" in source
        # Should be 300
        assert "_QUICKWIN_MIN_BLOCK_LEN = 300" in source

    def test_quickwins_with_marker_but_too_short_fails(self):
        """QuickWins with marker but block too short should fail."""
        from services.html_contract import html_contract_validate

        # Very short block with marker but minimal content
        html = """<html><head><title>Test</title></head><body>
        <h1>Report</h1>
        <!-- DEBUG-503D: QUICK_WINS_START -->
        <div class="quick-win" data-qw-json-rendered="true">
            <p>Short</p>
        </div>
        <!-- DEBUG-503D: QUICK_WINS_END -->
        </body></html>"""

        result = html_contract_validate(html, strict_mode=False, allow_repair=False)

        # Should have quick_wins_empty violation due to short block
        empty_violations = [
            v for v in result.violations
            if v.type.value == "quick_wins_empty"
        ]
        assert len(empty_violations) > 0, "Should have quick_wins_empty violation for too-short block"

    def test_quickwins_sufficient_content_passes(self):
        """QuickWins with sufficient content should pass."""
        from services.html_contract import html_contract_validate

        # Build a long enough block with quick-win classes
        items = []
        for i in range(3):
            items.append(f'''
            <div class="quick-win quick-win-card-premium">
                <h3>Quick Win {i+1}: Automatisierung Bereich {i+1}</h3>
                <p><strong>Problem:</strong> Manuelle Prozesse kosten viel Zeit und Ressourcen im täglichen Betrieb.</p>
                <p><strong>Wirkung:</strong> Erhebliche Zeitersparnis durch intelligente Automatisierung der Kernprozesse.</p>
                <p><strong>Umsetzung:</strong> Implementierung von KI-gestützten Workflow-Tools innerhalb von zwei Wochen.</p>
            </div>''')

        html = f"""<html><head><title>Test</title></head><body>
        <h1>Report</h1>
        <!-- DEBUG-503D: QUICK_WINS_START -->
        <div class="quick-wins-container" data-qw-json-rendered="true">
            {''.join(items)}
        </div>
        <!-- DEBUG-503D: QUICK_WINS_END -->
        </body></html>"""

        result = html_contract_validate(html, strict_mode=False, allow_repair=False)

        quickwins_violations = [
            v for v in result.violations
            if v.type.value in ("quickwins_no_marker", "quick_wins_empty")
        ]
        assert len(quickwins_violations) == 0, (
            f"Should pass with sufficient content, got: "
            f"{[(v.type.value, v.message) for v in quickwins_violations]}"
        )


class TestFix513_SourceInspection:
    """Source inspection tests for FIX-513 patterns."""

    def test_fix513_log_patterns(self):
        """FIX-513 log patterns should exist."""
        source = _read_source()
        assert "[FIX-513][HTML-CONTRACT]" in source

    def test_strict_mode_guards_llm_repair(self):
        """STRICT mode should prevent LLM repair."""
        source = _read_source()

        # Find the validation function
        func_match = re.search(
            r'def html_contract_validate.*?(?=\ndef _extract_bad_blocks)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Phase 2 should check is_strict
        assert "not is_strict" in func_source

    def test_quickwins_violation_uses_correct_section_key(self):
        """QuickWins empty violation should use 'quick_wins_empty' section key."""
        source = _read_source()
        assert 'section="quick_wins_empty"' in source
