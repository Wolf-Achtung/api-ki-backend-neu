# -*- coding: utf-8 -*-
"""
Tests for DEBUG-503D artifact collection module.

Tests verify:
1. build_debug_503d_attachments returns 4 attachments with correct filenames
2. quick_wins_keys.json contains expected fields
3. payback_mentions.txt includes canonical line
"""
import json
import os
import pytest
from unittest.mock import patch


class TestDebug503DAttachments:
    """Tests for build_debug_503d_attachments function."""

    @pytest.fixture
    def sample_html_with_anchors(self):
        """Sample HTML with debug anchors."""
        return """
<!DOCTYPE html>
<html>
<head><title>Test Report</title></head>
<body>
    <!-- DEBUG-ANCHOR: QUICK_WINS_DETAIL_START -->
    <section class="section chapter">
        <div class="section-header">
            <h2>Quick Wins</h2>
        </div>
        <div class="section-body">
            <div class="quick-win" data-qw-json-rendered="true">
                <h3>Quick Win 1</h3>
                <p>Description with Payback: 6 Monate</p>
            </div>
        </div>
    </section>
    <!-- DEBUG-ANCHOR: QUICK_WINS_DETAIL_END -->

    <!-- DEBUG-ANCHOR: RISK_MATRIX_START -->
    <div class="risk-block matrix-block risk-matrix-section">
        <p>Risiko-Matrix</p>
        <table class="table-modern" style="table-layout:auto;">
            <tr><td>Risiko</td><td>L</td><td>I</td><td>Score</td></tr>
            <tr><td>Risk 1</td><td>3</td><td>4</td><td>12</td></tr>
        </table>
    </div>
    <!-- DEBUG-ANCHOR: RISK_MATRIX_END -->

    <p>Amortisation in 8 Monaten erwartet.</p>
    <p>Payback period is approximately 6-8 months.</p>
</body>
</html>
"""

    @pytest.fixture
    def sample_sections(self):
        """Sample sections dict."""
        return {
            "QUICK_WINS_HTML": '<div class="quick-win" data-qw-json-rendered="true">Content</div>',
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
            "quick_wins": "[{\"title\": \"Test\"}]",
            "PAYBACK_MONTHS": 6.5,
            "CAPEX_REALISTISCH_EUR": 15000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2500,
        }

    @pytest.fixture
    def sample_canonical_kpis(self):
        """Sample canonical KPIs dict."""
        return {
            "PAYBACK_MONTHS": 6.5,
            "CAPEX_REALISTISCH_EUR": 15000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2500,
        }

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_returns_4_attachments(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that build_debug_503d_attachments returns exactly 4 attachments."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        assert len(attachments) == 4, f"Expected 4 attachments, got {len(attachments)}"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_correct_filenames(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that attachments have correct filenames."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        expected_filenames = [
            "debug_503d_quick_wins_block.html",
            "debug_503d_risk_matrix_block.html",
            "debug_503d_payback_mentions.txt",
            "debug_503d_quick_wins_keys.json",
        ]

        actual_filenames = [att["filename"] for att in attachments]
        assert actual_filenames == expected_filenames, f"Filenames mismatch: {actual_filenames}"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_quick_wins_keys_json_fields(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that quick_wins_keys.json contains expected fields."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        # Find the JSON attachment
        json_att = next(a for a in attachments if a["filename"] == "debug_503d_quick_wins_keys.json")
        data = json.loads(json_att["content"].decode("utf-8"))

        # Check required keys exist
        expected_keys = [
            "QUICK_WINS_HTML",
            "QUICK_WINS_HTML_LEFT",
            "QUICK_WINS_HTML_RIGHT",
            "quick_wins",
            "template_mode",
            "captured_at",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

        # Check each QW key has required fields
        for qw_key in ["QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT", "quick_wins"]:
            assert "len" in data[qw_key], f"Missing 'len' in {qw_key}"
            assert "has_quick_win_class" in data[qw_key], f"Missing 'has_quick_win_class' in {qw_key}"
            assert "has_rendered_marker" in data[qw_key], f"Missing 'has_rendered_marker' in {qw_key}"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_quick_wins_keys_template_mode(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test template_mode detection in quick_wins_keys.json."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        json_att = next(a for a in attachments if a["filename"] == "debug_503d_quick_wins_keys.json")
        data = json.loads(json_att["content"].decode("utf-8"))

        # With QUICK_WINS_HTML set and LEFT/RIGHT empty, should be FULL
        assert data["template_mode"] == "FULL", f"Expected FULL, got {data['template_mode']}"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_payback_mentions_canonical_line(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that payback_mentions.txt includes canonical PAYBACK_MONTHS line."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        txt_att = next(a for a in attachments if a["filename"] == "debug_503d_payback_mentions.txt")
        content = txt_att["content"].decode("utf-8")

        # Check canonical line exists (German format: 6,5)
        assert "CANONICAL PAYBACK_MONTHS:" in content
        assert "6,5" in content, f"Expected German formatted '6,5' in content"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_payback_mentions_finds_occurrences(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that payback_mentions.txt finds Payback/Amortisation occurrences."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        txt_att = next(a for a in attachments if a["filename"] == "debug_503d_payback_mentions.txt")
        content = txt_att["content"].decode("utf-8")

        # Should find "Payback" and "Amortisation" occurrences
        # Check that markers >>> and <<< are present (they mark match positions)
        assert ">>>" in content and "<<<" in content
        assert "TOTAL MATCHES:" in content
        # Check that matches were actually found
        assert "TOTAL MATCHES: 0" not in content, "Should find at least one Payback/Amortisation occurrence"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_quick_wins_snippet_extraction(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that quick_wins_block.html extracts content via anchors."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        html_att = next(a for a in attachments if a["filename"] == "debug_503d_quick_wins_block.html")
        content = html_att["content"].decode("utf-8")

        # Should contain the Quick Wins section content
        assert "Quick Wins" in content or "quick-win" in content
        assert "anchors" in content.lower() or "section" in content.lower()

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_risk_matrix_snippet_has_css(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that risk_matrix_block.html includes CSS styles."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        html_att = next(a for a in attachments if a["filename"] == "debug_503d_risk_matrix_block.html")
        content = html_att["content"].decode("utf-8")

        # Should contain CSS styles
        assert "<style>" in content
        assert "table-layout" in content

    @patch.dict(os.environ, {"DEBUG_RENDER": "0"})
    def test_returns_empty_when_disabled(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that no attachments are returned when DEBUG_RENDER is not '1'."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        assert len(attachments) == 0, "Should return empty list when DEBUG_RENDER != 1"

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_empty_when_env_not_set(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that no attachments are returned when DEBUG_RENDER env var is not set."""
        # Ensure DEBUG_RENDER is not set
        if "DEBUG_RENDER" in os.environ:
            del os.environ["DEBUG_RENDER"]

        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        assert len(attachments) == 0, "Should return empty list when DEBUG_RENDER not set"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_attachments_have_mimetype(self, sample_html_with_anchors, sample_sections, sample_canonical_kpis):
        """Test that all attachments have mimetype field."""
        from services.debug_503d import build_debug_503d_attachments

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis=sample_canonical_kpis
        )

        for att in attachments:
            assert "mimetype" in att, f"Attachment {att['filename']} missing mimetype"
            assert att["mimetype"] is not None


class TestIsDebugRenderEnabled:
    """Tests for is_debug_render_enabled function."""

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_enabled_with_1(self):
        from services.debug_503d import is_debug_render_enabled
        assert is_debug_render_enabled() is True

    @patch.dict(os.environ, {"DEBUG_RENDER": "0"})
    def test_disabled_with_0(self):
        from services.debug_503d import is_debug_render_enabled
        assert is_debug_render_enabled() is False

    @patch.dict(os.environ, {"DEBUG_RENDER": "true"})
    def test_disabled_with_true_string(self):
        """DEBUG_RENDER only activates with '1', not 'true'."""
        from services.debug_503d import is_debug_render_enabled
        assert is_debug_render_enabled() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_disabled_when_not_set(self):
        if "DEBUG_RENDER" in os.environ:
            del os.environ["DEBUG_RENDER"]
        from services.debug_503d import is_debug_render_enabled
        assert is_debug_render_enabled() is False


class TestTemplateMode:
    """Tests for template_mode detection in quick_wins_keys.json."""

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_left_right_mode(self):
        """Test LEFT_RIGHT mode when QUICK_WINS_HTML_RIGHT has content."""
        from services.debug_503d import build_debug_503d_attachments

        sections = {
            "QUICK_WINS_HTML": "",
            "QUICK_WINS_HTML_LEFT": "left content",
            "QUICK_WINS_HTML_RIGHT": "right content",
            "quick_wins": "",
        }

        attachments = build_debug_503d_attachments(
            final_html="<html></html>",
            sections=sections,
            canonical_kpis={}
        )

        json_att = next(a for a in attachments if a["filename"] == "debug_503d_quick_wins_keys.json")
        data = json.loads(json_att["content"].decode("utf-8"))
        assert data["template_mode"] == "LEFT_RIGHT"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_left_only_mode(self):
        """Test LEFT_ONLY mode when only QUICK_WINS_HTML_LEFT has content."""
        from services.debug_503d import build_debug_503d_attachments

        sections = {
            "QUICK_WINS_HTML": "",
            "QUICK_WINS_HTML_LEFT": "left content",
            "QUICK_WINS_HTML_RIGHT": "",
            "quick_wins": "",
        }

        attachments = build_debug_503d_attachments(
            final_html="<html></html>",
            sections=sections,
            canonical_kpis={}
        )

        json_att = next(a for a in attachments if a["filename"] == "debug_503d_quick_wins_keys.json")
        data = json.loads(json_att["content"].decode("utf-8"))
        assert data["template_mode"] == "LEFT_ONLY"

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_none_mode(self):
        """Test NONE mode when no Quick Wins content."""
        from services.debug_503d import build_debug_503d_attachments

        sections = {
            "QUICK_WINS_HTML": "",
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
            "quick_wins": "",
        }

        attachments = build_debug_503d_attachments(
            final_html="<html></html>",
            sections=sections,
            canonical_kpis={}
        )

        json_att = next(a for a in attachments if a["filename"] == "debug_503d_quick_wins_keys.json")
        data = json.loads(json_att["content"].decode("utf-8"))
        assert data["template_mode"] == "NONE"


class TestDebug503DSummaryJsonSerializable:
    """Tests for DEBUG-503D JSON serialization safety (prevents bytes-in-JSONB crash)."""

    @pytest.fixture
    def sample_html_with_anchors(self):
        """Sample HTML with debug anchors."""
        return """
<!DOCTYPE html>
<html>
<body>
    <!-- DEBUG-ANCHOR: QUICK_WINS_DETAIL_START -->
    <div class="quick-win">Test Quick Win</div>
    <!-- DEBUG-ANCHOR: QUICK_WINS_DETAIL_END -->
    <!-- DEBUG-ANCHOR: RISK_MATRIX_START -->
    <table><tr><td>Risk</td></tr></table>
    <!-- DEBUG-ANCHOR: RISK_MATRIX_END -->
    <p>Payback: 6 Monate</p>
</body>
</html>
"""

    @pytest.fixture
    def sample_sections(self):
        """Sample sections dict."""
        return {
            "QUICK_WINS_HTML": '<div class="quick-win">Content</div>',
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
            "quick_wins": "[]",
            "PAYBACK_MONTHS": 6.5,
        }

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_debug_503d_summary_is_json_serializable(self, sample_html_with_anchors, sample_sections):
        """
        Test that build_debug_503d_summary returns JSON-serializable data.

        This is the CRITICAL test for DEBUG-503D Hotfix:
        - build_debug_503d_attachments returns bytes (for email)
        - build_debug_503d_summary returns JSON-safe metadata (for DB storage)
        - The summary must be serializable to prevent "bytes not JSON serializable" error
        """
        from services.debug_503d import build_debug_503d_attachments, build_debug_503d_summary

        # Build attachments (contains bytes)
        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis={"PAYBACK_MONTHS": 6.5}
        )

        assert len(attachments) == 4, "Should have 4 debug attachments"

        # Build summary (should be JSON-safe)
        summary = build_debug_503d_summary(attachments)

        # CRITICAL: This must not raise TypeError
        try:
            json_str = json.dumps(summary)
        except TypeError as e:
            pytest.fail(f"Summary is NOT JSON-serializable: {e}")

        # Verify summary structure
        assert "artifact_count" in summary
        assert summary["artifact_count"] == 4
        assert "artifacts" in summary
        assert len(summary["artifacts"]) == 4
        assert "total_bytes" in summary
        assert "captured_at" in summary

        # Verify each artifact has expected fields
        for artifact in summary["artifacts"]:
            assert "filename" in artifact
            assert "size_bytes" in artifact
            assert "sha256" in artifact
            assert "mimetype" in artifact
            # size_bytes should be an int
            assert isinstance(artifact["size_bytes"], int)
            # sha256 should be a string (hex)
            assert isinstance(artifact["sha256"], str)
            assert len(artifact["sha256"]) == 64  # SHA256 hex is 64 chars

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_meta_with_summary_is_json_serializable(self, sample_html_with_anchors, sample_sections):
        """
        Test that the meta dict containing debug_503d_summary is JSON-serializable.

        This simulates the actual flow where meta is stored in Analysis.meta (Postgres JSONB).
        """
        from services.debug_503d import build_debug_503d_attachments, build_debug_503d_summary

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis={"PAYBACK_MONTHS": 6.5}
        )

        # Simulate what report_renderer.py does
        meta = {
            "scores": {"overall": 75},
            "report_id": "test-123",
            "debug_503d_summary": build_debug_503d_summary(attachments)
        }

        # This is what would fail with the old code (debug_503d_attachments with bytes)
        # It must pass now (debug_503d_summary without bytes)
        try:
            json_str = json.dumps(meta)
            parsed = json.loads(json_str)
        except TypeError as e:
            pytest.fail(f"Meta dict is NOT JSON-serializable: {e}")

        # Verify round-trip
        assert parsed["debug_503d_summary"]["artifact_count"] == 4

    @patch.dict(os.environ, {"DEBUG_RENDER": "1"})
    def test_attachments_contain_bytes_but_summary_does_not(self, sample_html_with_anchors, sample_sections):
        """
        Test that attachments contain bytes (for email) but summary does not (for DB).

        This verifies the separation of concerns:
        - attachments: passed to email function, contain actual bytes
        - summary: stored in DB meta, contains only metadata strings/numbers
        """
        from services.debug_503d import build_debug_503d_attachments, build_debug_503d_summary

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis={"PAYBACK_MONTHS": 6.5}
        )

        # Attachments SHOULD contain bytes (this is for email)
        for att in attachments:
            assert "content" in att
            assert isinstance(att["content"], bytes), f"Attachment {att['filename']} content should be bytes"

        # Summary should NOT contain bytes
        summary = build_debug_503d_summary(attachments)

        def check_no_bytes(obj, path="root"):
            """Recursively check that no bytes objects exist in the structure."""
            if isinstance(obj, bytes):
                pytest.fail(f"Found bytes at {path}")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    check_no_bytes(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_no_bytes(v, f"{path}[{i}]")

        check_no_bytes(summary)

    @patch.dict(os.environ, {"DEBUG_RENDER": "0"})
    def test_summary_empty_when_disabled(self, sample_html_with_anchors, sample_sections):
        """Test that summary is empty when DEBUG_RENDER is disabled."""
        from services.debug_503d import build_debug_503d_attachments, build_debug_503d_summary

        attachments = build_debug_503d_attachments(
            final_html=sample_html_with_anchors,
            sections=sample_sections,
            canonical_kpis={}
        )

        assert len(attachments) == 0

        summary = build_debug_503d_summary(attachments)
        assert summary == {}
