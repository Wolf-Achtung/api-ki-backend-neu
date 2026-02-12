# -*- coding: utf-8 -*-
"""Tests for scripts/report_qa_scan.py."""
import os
import sys
import json
import tempfile
from pathlib import Path

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from report_qa_scan import (
    Rule,
    Finding,
    scan_content,
    build_rules,
    _extract_text_from_html,
    findings_to_json,
    main,
)


# ---------------------------------------------------------------------------
# Rule / scan_content unit tests
# ---------------------------------------------------------------------------

class TestCurrencyEuroDot:
    """CURRENCY_EURO_DOT: detect empty '€.' artifacts."""

    def test_detects_euro_dot(self):
        rules = [r for r in build_rules(None) if r.id == "CURRENCY_EURO_DOT"]
        findings = scan_content(
            file_path=Path("test.html"), file_type="html", raw="", text="Kosten: €.",
            rules=rules,
        )
        assert len(findings) >= 1

    def test_ignores_valid_euro(self):
        rules = [r for r in build_rules(None) if r.id == "CURRENCY_EURO_DOT"]
        findings = scan_content(
            file_path=Path("test.html"), file_type="html", raw="", text="Kosten: 6.000 €.",
            rules=rules,
        )
        # "6.000 €." has a digit before the space-euro, so our negative lookbehind fires
        # This is actually a sentence ending after a valid euro value — should NOT match
        assert len(findings) == 0


class TestPercentPlaceholder:
    """PERCENT_PLACEHOLDER_BEI: detect 'bei %' without a number."""

    def test_detects_bei_percent(self):
        rules = [r for r in build_rules(None) if r.id == "PERCENT_PLACEHOLDER_BEI"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="", text="Der ROI liegt bei %.",
            rules=rules,
        )
        assert len(findings) >= 1

    def test_ignores_valid_percent(self):
        rules = [r for r in build_rules(None) if r.id == "PERCENT_PLACEHOLDER_BEI"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="", text="ROI bei 200 %",
            rules=rules,
        )
        assert len(findings) == 0


class TestColonPercent:
    """COLON_PERCENT_EMPTY: detect ': %' without a number."""

    def test_detects_colon_percent(self):
        rules = [r for r in build_rules(None) if r.id == "COLON_PERCENT_EMPTY"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="", text="ROI: %.",
            rules=rules,
        )
        assert len(findings) >= 1


class TestDuForm:
    """DU_FORM_PRONOUNS: detect informal 'du' but not false positives."""

    def test_detects_standalone_du(self):
        rules = [r for r in build_rules(None) if r.id == "DU_FORM_PRONOUNS"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="Wenn du die Software einsetzt, steigt deine Effizienz.",
            rules=rules,
        )
        assert len(findings) >= 2  # "du" + "deine"

    def test_ignores_durch(self):
        """'durch' must NOT trigger Du-form detection."""
        rules = [r for r in build_rules(None) if r.id == "DU_FORM_PRONOUNS"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="durch Automatisierung steigt die Produktivitaet",
            rules=rules,
        )
        assert len(findings) == 0

    def test_ignores_produkt(self):
        """'Produkt' must NOT trigger Du-form detection."""
        rules = [r for r in build_rules(None) if r.id == "DU_FORM_PRONOUNS"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="Das Produkt wurde industriell gefertigt. Industrie 4.0 ist relevant.",
            rules=rules,
        )
        assert len(findings) == 0

    def test_ignores_uppercase_Du(self):
        """Uppercase 'Du' (polite form in some contexts) should NOT match (case-sensitive)."""
        rules = [r for r in build_rules(None) if r.id == "DU_FORM_PRONOUNS"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="Wenn Du das Tool nutzt",
            rules=rules,
        )
        # Our regex is case-sensitive (flags=0), so uppercase "Du" should not match
        assert len(findings) == 0


class TestLeakDetection:
    """Leak phrase detection rules."""

    def test_detects_platzhalter(self):
        rules = [r for r in build_rules(None) if r.id == "LEAK_PLATZHALTER"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="Dies ist ein Platzhalter fuer spaeteren Inhalt.",
            rules=rules,
        )
        assert len(findings) == 1

    def test_detects_assistant_de(self):
        rules = [r for r in build_rules(None) if r.id == "LEAK_ASSISTANT_DE"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="wie kann ich dir helfen bei der Implementierung?",
            rules=rules,
        )
        assert len(findings) == 1

    def test_detects_assistant_en(self):
        rules = [r for r in build_rules(None) if r.id == "LEAK_ASSISTANT_EN"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="As an AI assistant, I can help you.",
            rules=rules,
        )
        assert len(findings) >= 1


class TestJinjaPlaceholder:
    """PLACEHOLDER_JINJA: detect unrendered {{ }} in raw HTML."""

    def test_detects_jinja(self):
        rules = [r for r in build_rules(None) if r.id == "PLACEHOLDER_JINJA"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html",
            raw="<p>{{CAPEX_REALISTISCH_EUR}} Euro</p>",
            text="Euro",
            rules=rules,
        )
        assert len(findings) == 1

    def test_no_jinja_in_clean_html(self):
        rules = [r for r in build_rules(None) if r.id == "PLACEHOLDER_JINJA"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html",
            raw="<p>6.000 Euro</p>",
            text="6.000 Euro",
            rules=rules,
        )
        assert len(findings) == 0


class TestSoloSegmentRules:
    """Solo-specific rules."""

    def test_solo_governance_detected(self):
        rules = build_rules("solo")
        solo_rules = [r for r in rules if r.id == "SOLO_GOVERNANCE"]
        findings = scan_content(
            file_path=Path("t.html"), file_type="html", raw="",
            text="Die Governance-Struktur sollte etabliert werden.",
            rules=solo_rules,
        )
        assert len(findings) == 1

    def test_solo_governance_not_in_team(self):
        rules = build_rules("team")
        governance_rules = [r for r in rules if r.id == "SOLO_GOVERNANCE"]
        assert len(governance_rules) == 0  # Not a team rule


# ---------------------------------------------------------------------------
# HTML extraction tests
# ---------------------------------------------------------------------------

class TestHTMLExtraction:
    """HTML text extraction strips tags/styles correctly."""

    def test_strips_style_content(self):
        html = '<style>.foo { width: 100%; }</style><p>Visible text</p>'
        text = _extract_text_from_html(html)
        assert "100%" not in text
        assert "Visible text" in text

    def test_strips_script_content(self):
        html = '<script>var x = "100%";</script><p>Only this</p>'
        text = _extract_text_from_html(html)
        assert "Only this" in text
        assert "var x" not in text

    def test_unescapes_entities(self):
        html = '<p>6.000&nbsp;&euro;</p>'
        text = _extract_text_from_html(html)
        assert "\u20ac" in text  # euro sign


# ---------------------------------------------------------------------------
# JSON output tests
# ---------------------------------------------------------------------------

class TestJSONOutput:
    """JSON output format."""

    def test_empty_findings(self):
        result = findings_to_json([])
        assert result["passed"] is True
        assert result["summary"]["errors"] == 0

    def test_with_errors(self):
        f = Finding(
            file="test.html", file_type="html", rule_id="X",
            severity="error", description="d", match="m",
            snippet="s", position=0,
        )
        result = findings_to_json([f])
        assert result["passed"] is False
        assert result["summary"]["errors"] == 1


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

class TestCLI:
    """CLI main() integration."""

    def test_clean_file_exits_0(self, tmp_path: Path):
        f = tmp_path / "clean.html"
        f.write_text("<html><body><p>Sauberer Report mit 6.000 Euro.</p></body></html>")
        exit_code = main([str(f)])
        assert exit_code == 0

    def test_dirty_file_exits_2(self, tmp_path: Path):
        f = tmp_path / "dirty.html"
        f.write_text("<html><body><p>Kosten: €. Der ROI liegt bei %.</p></body></html>")
        exit_code = main([str(f)])
        assert exit_code == 2

    def test_json_output(self, tmp_path: Path, capsys):
        f = tmp_path / "test.html"
        f.write_text("<html><body><p>Sauberer Text</p></body></html>")
        exit_code = main([str(f), "--json"])
        assert exit_code == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["passed"] is True

    def test_junit_output(self, tmp_path: Path):
        f = tmp_path / "test.html"
        f.write_text("<html><body><p>Platzhalter im Text</p></body></html>")
        junit_path = tmp_path / "results.xml"
        exit_code = main([str(f), "--junit", str(junit_path)])
        assert exit_code == 2
        assert junit_path.exists()
        content = junit_path.read_text()
        assert "LEAK_PLATZHALTER" in content

    def test_segment_solo(self, tmp_path: Path):
        f = tmp_path / "solo.html"
        f.write_text("<html><body><p>Die Governance sollte geaendert werden.</p></body></html>")
        exit_code = main([str(f), "--segment", "solo"])
        assert exit_code == 2  # SOLO_GOVERNANCE triggers error

    def test_directory_scan(self, tmp_path: Path):
        (tmp_path / "a.html").write_text("<p>OK</p>")
        (tmp_path / "b.html").write_text("<p>TODO here</p>")
        exit_code = main([str(tmp_path)])
        assert exit_code == 2  # b.html has TODO

    def test_no_files_exits_1(self, tmp_path: Path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        exit_code = main([str(empty_dir)])
        assert exit_code == 1  # No scannable files
