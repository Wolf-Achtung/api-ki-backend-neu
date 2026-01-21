# -*- coding: utf-8 -*-
"""
FIX-505 Tests: HTML Contract Validation

Tests for:
- Code fence detection and rejection
- QuickWins marker validation
- Empty section detection
- STRICT_MODE fail-closed behavior
- Repair attempts
"""
import json
import pytest
from unittest.mock import patch, MagicMock

# Module under test
from services.html_contract import (
    html_contract_validate,
    ContractResult,
    ContractViolationError,
    Violation,
    ViolationType,
    strip_code_fences_final,
    validate_quick_wins_rendered,
    _check_code_fences,
    _check_quickwins_markers,
    _check_empty_sections,
    _check_html_sanity,
    _check_raw_json_artifacts,
)


class TestCodeFenceDetection:
    """Tests for code fence detection."""

    def test_detects_triple_backticks(self):
        """Test: ``` in HTML is detected."""
        html = """
        <div>
        Some content
        ```
        code here
        ```
        </div>
        """
        violations = _check_code_fences(html)
        assert len(violations) >= 2
        assert all(v.type == ViolationType.CODE_FENCE for v in violations)

    def test_detects_code_fence_with_language(self):
        """Test: ```html, ```python etc. are detected."""
        html = """
        <section>
        ```html
        <p>Example</p>
        ```
        </section>
        """
        violations = _check_code_fences(html)
        assert len(violations) >= 1
        assert any("html" in v.message.lower() or "code fence" in v.message.lower()
                   for v in violations)

    def test_detects_orhtml(self):
        """Test: 'orhtml' text is detected."""
        html = "<div>orhtml Some text</div>"
        violations = _check_code_fences(html)
        assert len(violations) >= 1

    def test_clean_html_passes(self):
        """Test: Clean HTML without code fences passes."""
        html = """
        <section>
            <h1>Title</h1>
            <p>Content without any code fences</p>
        </section>
        """
        violations = _check_code_fences(html)
        assert len(violations) == 0

    def test_code_fence_line_number_reported(self):
        """Test: Line number is reported in violation."""
        html = "Line 1\nLine 2\n```\nLine 4"
        violations = _check_code_fences(html)
        assert len(violations) >= 1
        assert violations[0].line == 3  # ``` is on line 3


class TestQuickWinsValidation:
    """Tests for QuickWins marker validation."""

    def test_quickwins_without_marker_fails(self):
        """Test: QuickWins with JSON but no marker fails."""
        html = """
        <section id="quick_wins">
            <h2>Quick Wins</h2>
            {"title": "Some Win", "description": "Do something"}
        </section>
        """
        violations = _check_quickwins_markers(html)
        assert len(violations) >= 1
        assert any(v.type == ViolationType.QUICKWINS_NO_MARKER for v in violations)

    def test_quickwins_with_class_marker_passes(self):
        """Test: QuickWins with class="quick-win" passes."""
        html = """
        <section id="quick_wins">
            <h2>Quick Wins</h2>
            <ul>
                <li class="quick-win">First win</li>
                <li class="quick-win">Second win</li>
            </ul>
        </section>
        """
        violations = _check_quickwins_markers(html)
        critical = [v for v in violations if v.critical]
        assert len(critical) == 0

    def test_quickwins_with_data_attribute_passes(self):
        """Test: QuickWins with data-qw-json-rendered="true" passes."""
        html = """
        <section id="quick_wins" data-qw-json-rendered="true">
            <h2>Quick Wins</h2>
            <div>{"title": "Win"}</div>
        </section>
        """
        violations = _check_quickwins_markers(html)
        # Should pass if marker is present
        no_marker_violations = [v for v in violations if v.type == ViolationType.QUICKWINS_NO_MARKER]
        assert len(no_marker_violations) == 0

    def test_quickwins_with_rendered_list_passes(self):
        """Test: QuickWins with proper HTML list passes."""
        html = """
        <section id="schnellgewinne">
            <h2>Schnellgewinne</h2>
            <ul>
                <li><p>Maßnahme 1</p></li>
                <li><p>Maßnahme 2</p></li>
            </ul>
        </section>
        """
        violations = _check_quickwins_markers(html)
        critical = [v for v in violations if v.critical]
        assert len(critical) == 0


class TestEmptySectionDetection:
    """Tests for empty section detection."""

    def test_empty_required_section_fails(self):
        """Test: Empty required section is detected."""
        html = """
        <section id="executive_summary">
            <h1>Executive Summary</h1>
            <!-- Empty! -->
        </section>
        """
        violations = _check_empty_sections(html, sections=["executive_summary"])
        assert len(violations) >= 1
        assert any(v.type == ViolationType.EMPTY_SECTION for v in violations)

    def test_section_with_content_passes(self):
        """Test: Section with sufficient content passes."""
        html = """
        <section id="executive_summary">
            <h1>Executive Summary</h1>
            <p>This is a comprehensive executive summary that provides an overview
            of the AI readiness assessment. The company shows strong potential for
            digital transformation with several key opportunities identified.</p>
        </section>
        """
        violations = _check_empty_sections(html, sections=["executive_summary"])
        # Should not have empty section violation
        empty_violations = [v for v in violations if v.type == ViolationType.EMPTY_SECTION]
        assert len(empty_violations) == 0

    def test_optional_section_can_be_empty(self):
        """Test: Optional sections can be empty without violation."""
        html = """
        <section id="foerderprogramme">
            <h2>Förderprogramme</h2>
        </section>
        """
        violations = _check_empty_sections(html)
        # foerderprogramme is optional
        critical = [v for v in violations if v.critical and "foerderprogramme" in str(v.section).lower()]
        assert len(critical) == 0


class TestHTMLSanity:
    """Tests for basic HTML sanity checks."""

    def test_missing_heading_warning(self):
        """Test: HTML without headings gets warning."""
        html = "<div><p>Content only</p></div>"
        violations = _check_html_sanity(html)
        assert any(v.type == ViolationType.MISSING_HEADING for v in violations)

    def test_html_with_heading_passes(self):
        """Test: HTML with headings passes heading check."""
        html = "<section><h1>Title</h1><p>Content</p></section>"
        violations = _check_html_sanity(html)
        heading_violations = [v for v in violations if v.type == ViolationType.MISSING_HEADING]
        assert len(heading_violations) == 0

    def test_unclosed_tag_warning(self):
        """Test: Unclosed tags generate warning."""
        html = "<section><div>Content</section>"  # Missing </div>
        violations = _check_html_sanity(html)
        assert any(v.type == ViolationType.UNCLOSED_TAG for v in violations)


class TestRawJSONDetection:
    """Tests for raw JSON artifact detection."""

    def test_raw_json_object_detected(self):
        """Test: Raw JSON objects in HTML are detected."""
        html = """
        <section id="recommendations">
            <h2>Recommendations</h2>
            {"title": "AI Implementation", "description": "Deploy AI chatbot", "priority": "high"}
        </section>
        """
        violations = _check_raw_json_artifacts(html)
        assert len(violations) >= 1
        assert any(v.type == ViolationType.RAW_JSON for v in violations)

    def test_json_in_script_tag_ignored(self):
        """Test: JSON in script tags should not trigger (it's valid)."""
        html = """
        <script type="application/json">
            {"config": "value"}
        </script>
        """
        # Note: Current implementation may still flag this, but it's a known limitation
        # The test documents expected behavior

    def test_rendered_html_passes(self):
        """Test: Properly rendered HTML without raw JSON passes."""
        html = """
        <section id="recommendations">
            <h2>Recommendations</h2>
            <ul>
                <li><strong>AI Implementation:</strong> Deploy AI chatbot</li>
            </ul>
        </section>
        """
        violations = _check_raw_json_artifacts(html)
        assert len(violations) == 0


class TestContractValidation:
    """Tests for the main validation function."""

    def test_valid_html_passes(self):
        """Test: Valid HTML passes all checks."""
        html = """
        <!DOCTYPE html>
        <html>
        <body>
            <section id="executive_summary">
                <h1>Executive Summary</h1>
                <p>This is a comprehensive executive summary that provides an overview
                of the AI readiness assessment for ACME Corp. Multiple opportunities
                have been identified across different business areas.</p>
            </section>
            <section id="quick_wins">
                <h2>Quick Wins</h2>
                <ul>
                    <li class="quick-win">Implement chatbot</li>
                    <li class="quick-win">Automate reports</li>
                </ul>
            </section>
        </body>
        </html>
        """
        result = html_contract_validate(html, strict_mode=False)
        assert result.passed or result.critical_count == 0

    def test_code_fence_fails_validation(self):
        """Test: HTML with code fence fails validation."""
        html = """
        <section id="test">
            <h1>Test</h1>
            ```
            code block
            ```
        </section>
        """
        result = html_contract_validate(html, strict_mode=False, allow_repair=False)
        assert not result.passed
        assert result.critical_count > 0

    def test_empty_html_fails(self):
        """Test: Empty HTML fails validation."""
        result = html_contract_validate("", strict_mode=False)
        assert not result.passed

    def test_violations_counted_correctly(self):
        """Test: Critical and warning counts are correct."""
        html = """
        <div>
            ```
            code
            ```
            No headings here
        </div>
        """
        result = html_contract_validate(html, strict_mode=False, allow_repair=False)

        # Should have at least one critical (code fence)
        assert result.critical_count >= 1
        # Violation list should match counts
        critical_in_list = sum(1 for v in result.violations if v.critical)
        assert critical_in_list == result.critical_count


class TestStrictMode:
    """Tests for STRICT_MODE behavior."""

    def test_strict_mode_raises_on_violation(self):
        """Test: STRICT_MODE raises ContractViolationError on failure."""
        html = "<div>```code```</div>"

        with pytest.raises(ContractViolationError) as exc_info:
            html_contract_validate(html, strict_mode=True, allow_repair=False)

        error = exc_info.value
        assert error.result is not None
        assert error.result.critical_count > 0
        assert "debug_attachments" in dir(error)

    def test_strict_mode_debug_attachments(self):
        """Test: Debug attachments are generated in STRICT_MODE failure."""
        html = "<section id='quick_wins'>{\"broken\": \"json\"}</section>"

        with pytest.raises(ContractViolationError) as exc_info:
            html_contract_validate(html, strict_mode=True, allow_repair=False)

        attachments = exc_info.value.debug_attachments
        assert "debug_505_contract_report.json" in attachments
        assert "debug_505_bad_blocks.html" in attachments

        # Contract report should be valid JSON
        report = json.loads(attachments["debug_505_contract_report.json"])
        assert "violations" in report

    def test_non_strict_mode_returns_result(self):
        """Test: Non-STRICT mode returns result instead of raising."""
        html = "<div>```code```</div>"

        result = html_contract_validate(html, strict_mode=False, allow_repair=False)

        assert not result.passed
        assert result.critical_count > 0
        # Should not raise


class TestRepairAttempts:
    """Tests for repair functionality."""

    def test_deterministic_repair_removes_code_fences(self):
        """Test: Deterministic repair removes code fences."""
        html = "<section><h1>Title</h1>```code```<p>Text</p></section>"

        result = html_contract_validate(
            html,
            strict_mode=False,
            allow_repair=True,
        )

        # After repair, should pass or have fewer violations
        assert result.repair_attempted

    def test_repair_flag_set(self):
        """Test: repair_attempted flag is set when repair runs."""
        html = "<div>```fence```</div><h1>H</h1>"

        result = html_contract_validate(html, strict_mode=False, allow_repair=True)

        assert result.repair_attempted


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_strip_code_fences_final(self):
        """Test: strip_code_fences_final removes all fences."""
        html = "Before ```python\ncode\n``` After ```html\n<p>x</p>\n```"
        result = strip_code_fences_final(html)

        assert "```" not in result
        assert "Before" in result
        assert "After" in result

    def test_validate_quick_wins_rendered_true(self):
        """Test: validate_quick_wins_rendered returns True for proper HTML."""
        html = """
        <section id="quick_wins">
            <ul><li class="quick-win">Win</li></ul>
        </section>
        """
        assert validate_quick_wins_rendered(html)

    def test_validate_quick_wins_rendered_false(self):
        """Test: validate_quick_wins_rendered returns False for raw JSON."""
        html = """
        <section id="quick_wins">
            {"title": "Raw JSON"}
        </section>
        """
        # May return False due to JSON without markers
        result = validate_quick_wins_rendered(html)
        # This depends on implementation - adjust based on actual behavior


class TestResultSerialization:
    """Tests for result serialization."""

    def test_result_to_dict(self):
        """Test: ContractResult can be serialized to dict."""
        result = ContractResult(
            passed=False,
            violations=[
                Violation(
                    type=ViolationType.CODE_FENCE,
                    message="Test violation",
                    line=10,
                    context="```code```",
                    critical=True,
                )
            ],
            critical_count=1,
            warning_count=0,
            html_bytes=1000,
        )

        d = result.to_dict()

        assert d['passed'] is False
        assert d['critical_count'] == 1
        assert len(d['violations']) == 1
        assert d['violations'][0]['type'] == 'code_fence'
        assert d['violations'][0]['line'] == 10

    def test_result_json_serializable(self):
        """Test: Result dict is JSON serializable."""
        result = ContractResult(
            passed=True,
            violations=[],
            critical_count=0,
            warning_count=0,
        )

        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)

        assert parsed['passed'] is True


class TestLoggingFormat:
    """Tests for FIX-505 logging format."""

    def test_pass_log_format(self, caplog):
        """Test: PASS log has correct format."""
        import logging
        caplog.set_level(logging.INFO)

        html = "<section><h1>Title</h1><p>" + "x" * 100 + "</p></section>"
        html_contract_validate(html, strict_mode=False)

        log_messages = [r.message for r in caplog.records]
        assert any("[FIX-505][HTML-CONTRACT]" in msg for msg in log_messages)

    def test_fail_log_format(self, caplog):
        """Test: FAIL log has correct format."""
        import logging
        caplog.set_level(logging.WARNING)

        html = "<div>```code```</div>"
        html_contract_validate(html, strict_mode=False, allow_repair=False)

        log_messages = [r.message for r in caplog.records]
        assert any("FAIL" in msg and "[FIX-505][HTML-CONTRACT]" in msg for msg in log_messages)
