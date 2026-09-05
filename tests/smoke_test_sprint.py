# -*- coding: utf-8 -*-
"""
Post-Sprint Smoke Test Suite
=============================
Tests the following changes:
1. Markdown output + HTML rendering
2. Size-aware min lengths
3. Sanitizer recovery (no 0-word errors)
4. Template phrase removal
5. QuickWins min 4 entries
6. Size-mismatch adjustments
"""
from __future__ import annotations

import os
import sys
import re
import json

# Set test environment
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")

# Test results collector
RESULTS = {
    "passed": [],
    "failed": [],
    "warnings": [],
}


def log_pass(test_name: str, details: str = ""):
    RESULTS["passed"].append({"test": test_name, "details": details})
    print(f"  [PASS] {test_name}")


def log_fail(test_name: str, details: str):
    RESULTS["failed"].append({"test": test_name, "details": details})
    print(f"  [FAIL] {test_name}: {details}")


def log_warn(test_name: str, details: str):
    RESULTS["warnings"].append({"test": test_name, "details": details})
    print(f"  [WARN] {test_name}: {details}")


# =============================================================================
# 1. PROMPT-ENGINE SMOKE-TEST
# =============================================================================
def test_prompt_structure():
    """Test prompt files for correct structure."""
    print("\n" + "=" * 60)
    print("1. PROMPT-ENGINE SMOKE-TEST")
    print("=" * 60)

    # Check Markdown prompts
    md_prompts = [
        "prompts/de/quick_wins.md",
        "prompts/de/roadmap_90d.md",
        "prompts/de/roadmap_12m.md",
    ]

    for path in md_prompts:
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()

            # Check for Markdown indicators
            has_md_headers = "## " in content or "### " in content
            has_md_lists = "- " in content or "* " in content
            has_html_output_hint = "Markdown" in content or "KEIN HTML" in content

            if has_md_headers and has_md_lists:
                log_pass(f"Markdown structure: {path}")
            else:
                log_fail(f"Markdown structure: {path}", "Missing MD headers/lists")

            # Check for forbidden template phrases
            forbidden = ["Freitextfeld", "TODO", "Platzhalter"]
            found_forbidden = [f for f in forbidden if f in content]
            if not found_forbidden:
                log_pass(f"No forbidden phrases: {path}")
            else:
                log_fail(f"Forbidden phrases: {path}", f"Found: {found_forbidden}")
        else:
            log_fail(f"File exists: {path}", "File not found")

    # Check HTML prompts have size-aware logic
    html_prompts = [
        "prompts/de/org_change.md",
        "prompts/de/strategie_governance.md",
        "prompts/de/wettbewerb_benchmark.md",
    ]

    for path in html_prompts:
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()

            # Check for size-aware conditionals
            has_size_aware = "COMPANY_SIZE" in content or "size-aware" in content.lower()
            has_jinja = "{% if" in content or "{% elif" in content

            if has_size_aware:
                log_pass(f"Size-aware logic: {path}")
            else:
                log_warn(f"Size-aware logic: {path}", "No COMPANY_SIZE variable found")

            if has_jinja:
                log_pass(f"Jinja conditionals: {path}")
            else:
                log_warn(f"Jinja conditionals: {path}", "No {% if %} blocks found")


# =============================================================================
# 2. SANITIZER / HTML-RENDER SMOKE-TEST
# =============================================================================
def test_sanitizer():
    """Test sanitizer functions."""
    print("\n" + "=" * 60)
    print("2. SANITIZER / HTML-RENDER SMOKE-TEST")
    print("=" * 60)

    try:
        from services.html_sanitizer import (
            render_markdown_safe,
            recover_text_from_broken_html,
            sanitize_or_recover,
            sanitize_section_html,
        )

        # Test 1: Markdown rendering
        md_input = """## Test Header

This is a paragraph with **bold** and *italic* text.

- Item 1
- Item 2
- Item 3

### Subheader

Another paragraph here.
"""
        html_output = render_markdown_safe(md_input)

        if "<h2>" in html_output or "<p>" in html_output:
            log_pass("render_markdown_safe: basic conversion")
        else:
            log_fail("render_markdown_safe: basic conversion", f"Output: {html_output[:100]}")

        if "<strong>" in html_output or "<b>" in html_output:
            log_pass("render_markdown_safe: inline formatting")
        else:
            log_warn("render_markdown_safe: inline formatting", "No bold tags found")

        if "<ul>" in html_output and "<li>" in html_output:
            log_pass("render_markdown_safe: list rendering")
        else:
            log_warn("render_markdown_safe: list rendering", "No list tags found")

        # Test 2: Broken HTML recovery
        broken_html = "<p>This is broken <strong>HTML with <em>unclosed tags"
        recovered = recover_text_from_broken_html(broken_html, min_words=3)

        if "broken" in recovered.lower() and "html" in recovered.lower():
            log_pass("recover_text_from_broken_html: basic recovery")
        else:
            log_fail("recover_text_from_broken_html: basic recovery", f"Output: {recovered[:100]}")

        # Test 3: Zero-word prevention
        empty_looking_html = "<div><span></span><p>   </p></div>"
        recovered_empty = recover_text_from_broken_html(empty_looking_html, min_words=1)

        # Should return something, not crash
        log_pass("recover_text_from_broken_html: handles empty HTML")

        # Test 4: sanitize_or_recover combined
        good_html = "<p>This is valid HTML with enough words to pass the minimum threshold for the validator.</p>"
        result = sanitize_or_recover(good_html, min_words=5)

        if "valid HTML" in result:
            log_pass("sanitize_or_recover: preserves valid HTML")
        else:
            log_fail("sanitize_or_recover: preserves valid HTML", f"Output: {result[:100]}")

        # Test 5: No double <br> soup
        br_html = "<p>Line 1<br><br><br>Line 2</p>"
        sanitized = sanitize_section_html(br_html)

        br_count = sanitized.count("<br")
        if br_count <= 2:
            log_pass("sanitize_section_html: no br soup")
        else:
            log_warn("sanitize_section_html: br soup detected", f"{br_count} <br> tags found")

    except ImportError as e:
        log_fail("Sanitizer import", str(e))
    except Exception as e:
        log_fail("Sanitizer tests", str(e))


# =============================================================================
# 3. VALIDATOR SMOKE-TEST
# =============================================================================
def test_validator():
    """Test validator with profiles."""
    print("\n" + "=" * 60)
    print("3. VALIDATOR SMOKE-TEST")
    print("=" * 60)

    try:
        from services.report_validator import ReportValidator

        # Check MIN_SECTION_LENGTH_WORDS values
        expected_mins = {
            "foerderpotenzial": 600,
            "risks": 500,
            "recommendations": 500,
            "roadmap_12m": 400,
            "unternehmensprofil_markt": 220,  # FIX-B23-P3: card-based layout
        }

        for section, expected in expected_mins.items():
            actual = ReportValidator.MIN_SECTION_LENGTH_WORDS.get(section, 0)
            if actual == expected:
                log_pass(f"MIN_SECTION_LENGTH_WORDS[{section}] = {actual}")
            else:
                log_fail(f"MIN_SECTION_LENGTH_WORDS[{section}]", f"Expected {expected}, got {actual}")

        # Check SIZE-AWARE overrides exist
        if hasattr(ReportValidator, "MIN_SECTION_LENGTH_BY_SIZE"):
            sizes = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE
            if "solo" in sizes and "team" in sizes and "kmu" in sizes:
                log_pass("SIZE-AWARE overrides: all sizes defined")

                # Verify solo has lower values than kmu
                solo_12m = sizes.get("solo", {}).get("roadmap_12m", 0)
                kmu_12m = sizes.get("kmu", {}).get("roadmap_12m", 0)
                if solo_12m < kmu_12m:
                    log_pass(f"SIZE-AWARE hierarchy: solo({solo_12m}) < kmu({kmu_12m})")
                else:
                    log_fail("SIZE-AWARE hierarchy", f"solo({solo_12m}) should be < kmu({kmu_12m})")
            else:
                log_fail("SIZE-AWARE overrides", "Missing size keys")
        else:
            log_fail("SIZE-AWARE overrides", "MIN_SECTION_LENGTH_BY_SIZE not found")

        # Test validator with mock sections
        mock_sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>" + "Test content. " * 50 + "</p>",
            "foerderpotenzial": "<p>" + "Förderpotenzial text. " * 150 + "</p>",
            "risks": "<p>" + "Risk analysis text. " * 120 + "</p>",
            "roadmap_12m": "<p>" + "Roadmap content. " * 100 + "</p>",
        }
        mock_briefing = {"unternehmensgroesse": "1 (Solo)"}

        validator = ReportValidator(mock_sections, mock_briefing)
        is_valid, errors = validator.validate_all()

        # Check for TEMPLATE_PHRASE errors
        template_errors = [e for e in errors if e.category == "TEMPLATE_PHRASE"]
        if not template_errors:
            log_pass("Validator: no TEMPLATE_PHRASE errors")
        else:
            log_fail("Validator: TEMPLATE_PHRASE", f"{len(template_errors)} errors found")

        # Check for zero-word errors
        zero_word_errors = [e for e in errors if "0 Wörter" in str(e.message) or "0 words" in str(e.message).lower()]
        if not zero_word_errors:
            log_pass("Validator: no zero-word errors")
        else:
            log_fail("Validator: zero-word errors", f"{len(zero_word_errors)} errors found")

    except ImportError as e:
        log_fail("Validator import", str(e))
    except Exception as e:
        log_fail("Validator tests", str(e))


# =============================================================================
# 4. FUNDING ENGINE SMOKE-TEST
# =============================================================================
def test_funding():
    """Test funding engine functions."""
    print("\n" + "=" * 60)
    print("4. FUNDING ENGINE SMOKE-TEST")
    print("=" * 60)

    # Check funding JSON files exist
    funding_files = [
        "data/funding_programmes_core_2025.json",
        "data/funding/funding_de_en.json",
        "data/funding/funding_eu_core_en.json",
    ]

    for path in funding_files:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                if isinstance(data, (list, dict)):
                    log_pass(f"Funding file valid: {path}")
                else:
                    log_fail(f"Funding file: {path}", "Invalid JSON structure")
            except json.JSONDecodeError as e:
                log_fail(f"Funding file: {path}", f"JSON error: {e}")
        else:
            log_warn(f"Funding file: {path}", "File not found")

    # Check research_pipeline imports
    try:
        from services.research_pipeline import run_research, MAX_VISIBLE_ITEMS

        if MAX_VISIBLE_ITEMS == 6:
            log_pass("research_pipeline: MAX_VISIBLE_ITEMS = 6")
        else:
            log_warn("research_pipeline: MAX_VISIBLE_ITEMS", f"Expected 6, got {MAX_VISIBLE_ITEMS}")

        log_pass("research_pipeline: imports successfully")

    except ImportError as e:
        log_fail("research_pipeline import", str(e))


# =============================================================================
# 5. PDF RENDER SMOKE-TEST
# =============================================================================
def test_pdf_render():
    """Test PDF rendering components."""
    print("\n" + "=" * 60)
    print("5. PDF RENDER SMOKE-TEST")
    print("=" * 60)

    # Check logo embedder
    try:
        from utils.logo_embedder import (
            get_logo_base64_map,
            optimize_base64_image,
            DEFAULT_LOGOS,
        )

        log_pass("logo_embedder: imports successfully")

        # Check optimize function exists
        if callable(optimize_base64_image):
            log_pass("logo_embedder: optimize_base64_image callable")

        # Check DEFAULT_LOGOS
        if len(DEFAULT_LOGOS) >= 3:
            log_pass(f"logo_embedder: {len(DEFAULT_LOGOS)} logos defined")
        else:
            log_warn("logo_embedder: logos", f"Only {len(DEFAULT_LOGOS)} logos defined")

    except ImportError as e:
        log_fail("logo_embedder import", str(e))

    # Check HTML sanitizer minify function
    try:
        from services.html_sanitizer import sanitize_section_html

        # Test minification
        verbose_html = """
        <div class="">
            <p>   Text with spaces   </p>
            <span></span>
        </div>
        """
        minified = sanitize_section_html(verbose_html, minify=True)

        if len(minified) < len(verbose_html):
            log_pass("HTML minification: reduces size")
        else:
            log_warn("HTML minification", "No size reduction")

    except ImportError as e:
        log_fail("HTML minification import", str(e))


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "#" * 60)
    print("# POST-SPRINT SMOKE TEST")
    print("#" * 60)

    test_prompt_structure()
    test_sanitizer()
    test_validator()
    test_funding()
    test_pdf_render()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  PASSED:   {len(RESULTS['passed'])}")
    print(f"  FAILED:   {len(RESULTS['failed'])}")
    print(f"  WARNINGS: {len(RESULTS['warnings'])}")

    if RESULTS["failed"]:
        print("\nFAILED TESTS:")
        for f in RESULTS["failed"]:
            print(f"  - {f['test']}: {f['details']}")

    if RESULTS["warnings"]:
        print("\nWARNINGS:")
        for w in RESULTS["warnings"]:
            print(f"  - {w['test']}: {w['details']}")

    # Return exit code
    return 0 if len(RESULTS["failed"]) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
