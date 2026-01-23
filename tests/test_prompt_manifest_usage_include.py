# -*- coding: utf-8 -*-
"""
Tests for PROMPT-MANIFEST / USAGE / INCLUDE-ONLY-HARDEN-A

Covers:
- TASK 1: Manifest enforcement (PromptManifest resolve, STRICT fail-closed)
- TASK 2: Usage tracking (record, flush, audit script)
- TASK 3: Jinja include-only + path sandbox
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch


class TestPromptManifest:
    """TASK 1: Manifest as Single Source of Truth."""

    def setup_method(self):
        from services.prompt_loader import PromptManifest
        PromptManifest.reset()

    def test_manifest_loads_singleton(self):
        """PromptManifest.load() returns cached singleton."""
        from services.prompt_loader import PromptManifest
        m1 = PromptManifest.load()
        m2 = PromptManifest.load()
        assert m1 is m2

    def test_manifest_resolve_known_section(self):
        """Known section resolves to path from manifest."""
        from services.prompt_loader import PromptManifest
        m = PromptManifest.load()
        path = m.resolve("executive_summary", "de")
        assert path == "executive_summary.md"

    def test_manifest_resolve_unknown_section(self):
        """Unknown section returns None."""
        from services.prompt_loader import PromptManifest
        m = PromptManifest.load()
        path = m.resolve("nonexistent_section_xyz", "de")
        assert path is None

    def test_manifest_has_section(self):
        """has_section returns True for known, False for unknown."""
        from services.prompt_loader import PromptManifest
        m = PromptManifest.load()
        assert m.has_section("quick_wins", "de") is True
        assert m.has_section("nonexistent_xyz", "de") is False

    def test_manifest_resolve_en_section(self):
        """EN sections also resolve from manifest."""
        from services.prompt_loader import PromptManifest
        m = PromptManifest.load()
        path = m.resolve("executive_summary", "en")
        assert path == "executive_summary.md"

    def test_strict_mode_unknown_section_raises(self):
        """In STRICT mode, unknown section raises RuntimeError."""
        from services.prompt_loader import _resolve_section_path, PromptManifest
        PromptManifest.reset()
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-MANIFEST.*unknown section"):
                _resolve_section_path("totally_fake_section_999", "de")

    def test_non_strict_unknown_section_returns_none(self):
        """In non-STRICT mode, unknown section falls through to None."""
        from services.prompt_loader import _resolve_section_path, PromptManifest
        PromptManifest.reset()
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", False):
            path, lang = _resolve_section_path("totally_fake_section_999", "de")
            assert path is None

    def test_manifest_log_present_in_source(self):
        """prompt_loader.py must contain [PROMPT-MANIFEST] ok log."""
        source = Path("services/prompt_loader.py").read_text()
        assert "[PROMPT-MANIFEST] ok section=" in source

    def test_manifest_error_log_present(self):
        """prompt_loader.py must contain [PROMPT-MANIFEST][ERROR] log."""
        source = Path("services/prompt_loader.py").read_text()
        assert "[PROMPT-MANIFEST][ERROR]" in source


class TestPromptUsageTracking:
    """TASK 2: Usage tracking."""

    def setup_method(self):
        from services.prompt_loader import clear_used_prompts
        clear_used_prompts()

    def test_record_usage_appends(self):
        """_record_usage adds entries to used_prompts."""
        from services.prompt_loader import _record_usage, get_used_prompts
        _record_usage("test_section", "de", "de/test.md", 100, "hello", [])
        entries = get_used_prompts()
        assert len(entries) == 1
        assert entries[0]["section"] == "test_section"
        assert entries[0]["lang"] == "de"
        assert entries[0]["bytes"] == 100
        assert "sha256" in entries[0]

    def test_record_usage_includes_sha256(self):
        """Usage entry must have sha256 hash."""
        from services.prompt_loader import _record_usage, get_used_prompts
        _record_usage("s", "de", "p", 5, "test content", ["inc.md"])
        entry = get_used_prompts()[0]
        assert len(entry["sha256"]) == 16  # truncated sha256
        assert entry["includes"] == ["inc.md"]

    def test_flush_creates_artifact(self):
        """flush_usage_to_artifact writes JSON file."""
        from services.prompt_loader import (
            _record_usage, flush_usage_to_artifact, clear_used_prompts
        )
        _record_usage("executive_summary", "de", "de/executive_summary.md", 200, "content", [])

        result = flush_usage_to_artifact()

        # It should have written to artifacts/prompt_usage_last.json
        assert result is not None
        assert Path(result).exists()
        data = json.loads(Path(result).read_text())
        assert len(data) >= 1
        assert data[-1]["section"] == "executive_summary"

        # Clean up so audit script test passes
        Path(result).unlink(missing_ok=True)

    def test_clear_used_prompts(self):
        """clear_used_prompts empties the list."""
        from services.prompt_loader import _record_usage, get_used_prompts, clear_used_prompts
        _record_usage("s", "de", "p", 10, "x", [])
        assert len(get_used_prompts()) == 1
        clear_used_prompts()
        assert len(get_used_prompts()) == 0

    def test_audit_script_exits_zero(self):
        """scripts/prompt_usage_audit.py must exit 0."""
        import subprocess
        result = subprocess.run(
            ["python", "scripts/prompt_usage_audit.py"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, f"Audit failed:\n{result.stdout}\n{result.stderr}"


class TestJinjaIncludeOnly:
    """TASK 3: Jinja include-only enforcement + path sandbox."""

    def test_forbidden_extends_blocked(self):
        """{% extends %} must be blocked."""
        from services.prompt_loader import _prescan_jinja_tags
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-JINJA.*forbidden tag.*extends"):
                _prescan_jinja_tags('{% extends "base.html" %}', "test")

    def test_forbidden_import_blocked(self):
        """{% import %} must be blocked."""
        from services.prompt_loader import _prescan_jinja_tags
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-JINJA.*forbidden tag.*import"):
                _prescan_jinja_tags('{% import "macros.html" as m %}', "test")

    def test_forbidden_from_blocked(self):
        """{% from %} must be blocked."""
        from services.prompt_loader import _prescan_jinja_tags
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-JINJA.*forbidden tag.*from"):
                _prescan_jinja_tags('{% from "x.html" import y %}', "test")

    def test_forbidden_macro_blocked(self):
        """{% macro %} must be blocked."""
        from services.prompt_loader import _prescan_jinja_tags
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-JINJA.*forbidden tag.*macro"):
                _prescan_jinja_tags('{% macro input(name) %}...{% endmacro %}', "test")

    def test_include_allowed(self):
        """{% include %} must NOT be blocked."""
        from services.prompt_loader import _prescan_jinja_tags
        # Should not raise
        _prescan_jinja_tags('{% include "fragment.md" %}', "test")

    def test_raw_allowed(self):
        """{% raw %} must NOT be blocked."""
        from services.prompt_loader import _prescan_jinja_tags
        _prescan_jinja_tags('{% raw %}...{% endraw %}', "test")

    def test_include_path_traversal_blocked(self):
        """Include with '..' must be blocked."""
        from services.prompt_loader import _validate_include_path
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-INCLUDE.*BLOCK.*path_traversal"):
                _validate_include_path("../etc/passwd", "de", "test")

    def test_include_absolute_path_blocked(self):
        """Include with absolute path must be blocked."""
        from services.prompt_loader import _validate_include_path
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-INCLUDE.*BLOCK.*absolute_path"):
                _validate_include_path("/etc/passwd", "de", "test")

    def test_include_backslash_blocked(self):
        """Include with backslash must be blocked."""
        from services.prompt_loader import _validate_include_path
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
            with pytest.raises(RuntimeError, match="PROMPT-INCLUDE.*BLOCK.*backslash"):
                _validate_include_path("foo\\bar.md", "de", "test")

    def test_include_normal_path_allowed(self):
        """Normal include path (e.g. 'prompt_framework.md') is allowed."""
        from services.prompt_loader import _validate_include_path, PromptManifest
        PromptManifest.reset()
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", False):
            result = _validate_include_path("prompt_framework.md", "de", "test")
            assert result is True

    def test_prescan_includes_returns_list(self):
        """_prescan_includes returns list of include targets."""
        from services.prompt_loader import _prescan_includes, PromptManifest
        PromptManifest.reset()
        with patch("services.prompt_loader.RELEASE_STRICT_MODE", False):
            text = '{% include "a.md" %}\n{% include "b.md" %}'
            result = _prescan_includes(text, "de", "test")
            assert result == ["a.md", "b.md"]

    def test_source_has_prompt_include_log(self):
        """prompt_loader.py must contain [PROMPT-INCLUDE] allow log."""
        source = Path("services/prompt_loader.py").read_text()
        assert "[PROMPT-INCLUDE] allow" in source

    def test_source_has_prompt_jinja_block_log(self):
        """prompt_loader.py must contain [PROMPT-JINJA][BLOCK] log."""
        source = Path("services/prompt_loader.py").read_text()
        assert "[PROMPT-JINJA][BLOCK]" in source
