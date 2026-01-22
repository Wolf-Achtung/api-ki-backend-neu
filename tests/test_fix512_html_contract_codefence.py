"""
FIX-512: HTML Contract CodeFence-Safe Tests

Tests for the code fence stripping after LLM repair and hardened prompts.

Key changes in FIX-512:
- CHANGE 1: Strip code fences AFTER html_repair output, before re-validation
- CHANGE 2: Hardened repair prompt with explicit NO markdown/code fences instruction
- CHANGE 3: Debug attachments stored in meta for admin email
"""
import pytest
import re
import os

# Path to files for source inspection
HTML_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "html_contract.py")
REPORT_RENDERER_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "report_renderer.py")


def _read_source(path: str) -> str:
    """Read source file for inspection tests."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class TestFix512_CodeFenceStripping:
    """Tests for CHANGE 1: Strip code fences after LLM repair."""

    def test_strip_code_fences_after_repair_log_pattern(self):
        """Should log [FIX-512][HTML-CONTRACT] stripped_code_fences_after_repair."""
        source = _read_source(HTML_CONTRACT_PATH)
        assert "[FIX-512][HTML-CONTRACT] stripped_code_fences_after_repair" in source

    def test_strip_code_fences_called_after_llm_repair(self):
        """strip_code_fences_final should be called after _attempt_llm_repair."""
        source = _read_source(HTML_CONTRACT_PATH)

        # Find the Phase 2 LLM repair section
        llm_repair_match = re.search(
            r'# Phase 2: LLM repair.*?repair successful \(LLM\)',
            source,
            re.DOTALL
        )
        assert llm_repair_match is not None
        llm_section = llm_repair_match.group()

        # Order check: _attempt_llm_repair before strip_code_fences_final
        llm_repair_pos = llm_section.find("_attempt_llm_repair")
        strip_pos = llm_section.find("strip_code_fences_final")

        assert llm_repair_pos != -1, "_attempt_llm_repair should be called"
        assert strip_pos != -1, "strip_code_fences_final should be called"
        assert llm_repair_pos < strip_pos, "strip_code_fences_final must be called AFTER _attempt_llm_repair"

    def test_strip_code_fences_before_revalidation(self):
        """strip_code_fences_final should be called BEFORE re-validation."""
        source = _read_source(HTML_CONTRACT_PATH)

        # Find the Phase 2 LLM repair section
        llm_repair_match = re.search(
            r'# Phase 2: LLM repair.*?repair successful \(LLM\)',
            source,
            re.DOTALL
        )
        assert llm_repair_match is not None
        llm_section = llm_repair_match.group()

        # Order check: strip_code_fences_final before recheck html_contract_validate
        strip_pos = llm_section.find("strip_code_fences_final")
        recheck_pos = llm_section.find("recheck = html_contract_validate")

        assert strip_pos != -1, "strip_code_fences_final should be called"
        assert recheck_pos != -1, "html_contract_validate should be called for recheck"
        assert strip_pos < recheck_pos, "strip_code_fences_final must be called BEFORE recheck"

    def test_counts_fences_removed(self):
        """Should count how many fences were removed and log it."""
        source = _read_source(HTML_CONTRACT_PATH)

        # Find the Phase 2 section
        llm_repair_match = re.search(
            r'# Phase 2: LLM repair.*?repair successful \(LLM\)',
            source,
            re.DOTALL
        )
        assert llm_repair_match is not None
        llm_section = llm_repair_match.group()

        assert "fences_removed" in llm_section
        assert "fence_count_before" in llm_section
        assert "fence_count_after" in llm_section


class TestFix512_HardenedPrompt:
    """Tests for CHANGE 2: Hardened repair prompt."""

    def test_prompt_has_no_markdown_instruction(self):
        """Repair prompt should explicitly say 'No markdown'."""
        source = _read_source(HTML_CONTRACT_PATH)

        # Find _attempt_llm_repair function (until next def or end of REPAIR FUNCTIONS section)
        func_match = re.search(
            r'def _attempt_llm_repair.*?(?=\n# =====|\ndef [a-z_]+\()',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "No markdown" in func_source or "no markdown" in func_source.lower()

    def test_prompt_has_no_code_fences_instruction(self):
        """Repair prompt should explicitly say 'No ``` fences'."""
        source = _read_source(HTML_CONTRACT_PATH)

        func_match = re.search(
            r'def _attempt_llm_repair.*?(?=\n# =====|\ndef [a-z_]+\()',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "No ```" in func_source or "no code fence" in func_source.lower()

    def test_prompt_has_only_raw_html_instruction(self):
        """Repair prompt should say 'Return ONLY raw HTML'."""
        source = _read_source(HTML_CONTRACT_PATH)

        func_match = re.search(
            r'def _attempt_llm_repair.*?(?=\n# =====|\ndef [a-z_]+\()',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "ONLY raw HTML" in func_source or "only raw html" in func_source.lower()

    def test_system_prompt_hardened(self):
        """System prompt should be hardened to prevent markdown output."""
        source = _read_source(HTML_CONTRACT_PATH)

        func_match = re.search(
            r'def _attempt_llm_repair.*?(?=\n# =====|\ndef [a-z_]+\()',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Check system_prompt
        assert "system_prompt=" in func_source
        # Should mention no markdown or only HTML
        assert "Never use markdown" in func_source or "clean HTML" in func_source


class TestFix512_DebugAttachments:
    """Tests for CHANGE 3: Debug attachments in report_renderer."""

    def test_debug_attachments_stored_in_meta(self):
        """Debug attachments should be stored in meta for admin email."""
        source = _read_source(REPORT_RENDERER_PATH)

        assert "html_contract_debug_attachments" in source

    def test_debug_attachments_log_pattern(self):
        """Should log [FIX-512][HTML-CONTRACT] debug_attachments stored."""
        source = _read_source(REPORT_RENDERER_PATH)

        assert "[FIX-512][HTML-CONTRACT] debug_attachments stored" in source

    def test_checks_exception_debug_attachments(self):
        """Should check e.debug_attachments from ContractViolationError."""
        source = _read_source(REPORT_RENDERER_PATH)

        # Find the ContractViolationError handling (greedy until next except or end of try block)
        exception_match = re.search(
            r'except ContractViolationError as e:.*?(?=\n    except|\n    #|\nif|\Z)',
            source,
            re.DOTALL
        )
        assert exception_match is not None
        exception_section = exception_match.group()

        assert "debug_attachments" in exception_section


class TestFix512_StripCodeFencesFunction:
    """Unit tests for strip_code_fences_final function."""

    def test_strip_code_fences_function_exists(self):
        """strip_code_fences_final function should exist."""
        source = _read_source(HTML_CONTRACT_PATH)
        assert "def strip_code_fences_final" in source

    def test_strip_code_fences_removes_backticks(self):
        """strip_code_fences_final should remove ``` markers."""
        from services.html_contract import strip_code_fences_final

        html = "```html\n<div>Test</div>\n```"
        result = strip_code_fences_final(html)

        assert "```" not in result
        assert "<div>Test</div>" in result

    def test_strip_code_fences_removes_orhtml(self):
        """strip_code_fences_final should remove 'orhtml' pattern."""
        from services.html_contract import strip_code_fences_final

        html = "<div>Test</div>orhtml"
        result = strip_code_fences_final(html)

        assert "orhtml" not in result.lower()
        assert "<div>Test</div>" in result

    def test_strip_code_fences_preserves_valid_html(self):
        """strip_code_fences_final should preserve valid HTML content."""
        from services.html_contract import strip_code_fences_final

        html = """<div class="test">
            <h1>Title</h1>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>"""

        result = strip_code_fences_final(html)

        assert '<div class="test">' in result
        assert "<h1>Title</h1>" in result
        assert "<li>Item 1</li>" in result


class TestFix512_CodeFencePatterns:
    """Unit tests for code fence pattern detection."""

    def test_code_fence_pattern_matches_backticks(self):
        """_CODE_FENCE_PATTERN should match ``` markers."""
        from services.html_contract import _CODE_FENCE_PATTERN

        test_cases = [
            ("```", True),
            ("```html", True),
            ("```python", True),
            ("````", True),
            ("<div>", False),
        ]

        for text, should_match in test_cases:
            match = _CODE_FENCE_PATTERN.search(text)
            assert (match is not None) == should_match, f"'{text}' should {'match' if should_match else 'not match'}"

    def test_orhtml_pattern_matches_variants(self):
        """_ORHTML_PATTERN should match 'orhtml' and '```html'."""
        from services.html_contract import _ORHTML_PATTERN

        test_cases = [
            ("orhtml", True),
            ("ORHTML", True),
            ("```html", True),
            ("```HTML", True),
            ("<html>", False),
        ]

        for text, should_match in test_cases:
            match = _ORHTML_PATTERN.search(text)
            assert (match is not None) == should_match, f"'{text}' should {'match' if should_match else 'not match'}"


class TestFix512_MustNotHappen:
    """Tests for patterns that must not happen after FIX-512."""

    def test_fail_log_still_exists_for_other_violations(self):
        """FAIL log should still exist for non-code-fence violations."""
        source = _read_source(HTML_CONTRACT_PATH)
        assert "[FIX-505][HTML-CONTRACT] FAIL" in source

    def test_contract_violation_error_still_raised(self):
        """ContractViolationError should still be raised in STRICT mode."""
        source = _read_source(HTML_CONTRACT_PATH)
        assert "raise ContractViolationError" in source

    def test_repair_still_attempted(self):
        """Repair should still be attempted before failing."""
        source = _read_source(HTML_CONTRACT_PATH)
        assert "repair_attempted = True" in source
        assert "_attempt_deterministic_repair" in source
        assert "_attempt_llm_repair" in source
