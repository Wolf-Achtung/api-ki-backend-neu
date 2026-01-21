# -*- coding: utf-8 -*-
"""
FIX-505 Tests: PromptLoader Cycle Detection

Tests for:
- Cycle detection in Jinja2 includes
- STRICT_MODE behavior (no fallback)
- Non-strict fallback with logging
- Normal includes work without warnings
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Module under test
from services.prompt_loader import (
    load_prompt,
    check_prompt_cycles,
    PromptIncludeCycleError,
    _interpolate_text,
    CycleDetectingLoader,
)


class TestCycleDetection:
    """Tests for cycle detection in prompt includes."""

    def test_direct_cycle_detected(self, tmp_path):
        """Test: a includes b, b includes a → raises PromptIncludeCycleError."""
        # Create prompt files with cycle
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        (prompts_dir / "a.md").write_text("{% include 'b.md' %}")
        (prompts_dir / "b.md").write_text("{% include 'a.md' %}")

        # Patch BASE_DIR
        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            with pytest.raises((PromptIncludeCycleError, RuntimeError)) as exc_info:
                load_prompt("a", lang="de", vars_dict={"test": "value"})

            # Check error mentions cycle
            assert "cycle" in str(exc_info.value).lower() or "recursion" in str(exc_info.value).lower()

    def test_three_way_cycle_detected(self, tmp_path):
        """Test: a → b → c → a cycle detected."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        (prompts_dir / "a.md").write_text("Start {% include 'b.md' %} End")
        (prompts_dir / "b.md").write_text("Middle {% include 'c.md' %}")
        (prompts_dir / "c.md").write_text("{% include 'a.md' %}")

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            with pytest.raises((PromptIncludeCycleError, RuntimeError)):
                load_prompt("a", lang="de", vars_dict={"x": "y"})

    def test_no_cycle_normal_include(self, tmp_path):
        """Test: Normal includes without cycles work fine."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        (prompts_dir / "main.md").write_text("Main: {% include 'helper.md' %}")
        (prompts_dir / "helper.md").write_text("Helper content with {{ name }}")

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            result = load_prompt("main", lang="de", vars_dict={"name": "Test"})

            assert "Main:" in result
            assert "Helper content with Test" in result

    def test_diamond_dependency_no_cycle(self, tmp_path):
        """Test: Diamond dependencies (a→b, a→c, b→d, c→d) are NOT cycles."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        (prompts_dir / "a.md").write_text("{% include 'b.md' %}\n{% include 'c.md' %}")
        (prompts_dir / "b.md").write_text("B: {% include 'd.md' %}")
        (prompts_dir / "c.md").write_text("C: {% include 'd.md' %}")
        (prompts_dir / "d.md").write_text("D: {{ value }}")

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            result = load_prompt("a", lang="de", vars_dict={"value": "OK"})

            assert "B:" in result
            assert "C:" in result
            assert "D: OK" in result


class TestStrictMode:
    """Tests for STRICT_MODE behavior."""

    def test_strict_mode_no_fallback_on_jinja_error(self, tmp_path):
        """Test: In STRICT_MODE, Jinja2 errors raise RuntimeError (no fallback)."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        # Invalid Jinja2 syntax
        (prompts_dir / "broken.md").write_text("{% if broken %} unclosed")

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
                with pytest.raises(RuntimeError) as exc_info:
                    load_prompt("broken", lang="de", vars_dict={"test": "1"})

                assert "STRICT_MODE" in str(exc_info.value)

    def test_non_strict_mode_allows_fallback(self, tmp_path, caplog):
        """Test: In non-STRICT mode, Jinja2 errors fallback with logging."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        # Invalid Jinja2 that will fail
        (prompts_dir / "broken.md").write_text("{% if broken %} unclosed")

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            with patch("services.prompt_loader.RELEASE_STRICT_MODE", False):
                # Should not raise, should fallback
                import logging
                caplog.set_level(logging.WARNING)

                result = load_prompt("broken", lang="de", vars_dict={"test": "1"})

                # Should have fallback log
                assert any("FALLBACK" in record.message for record in caplog.records)

    def test_strict_mode_cycle_raises_immediately(self, tmp_path):
        """Test: Cycles in STRICT_MODE raise an error (either PromptIncludeCycleError or RuntimeError)."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        # Create a cycle: a includes b, b includes a
        (prompts_dir / "a.md").write_text("A: {% include 'b.md' %}")
        (prompts_dir / "b.md").write_text("B: {% include 'a.md' %}")

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
                with pytest.raises((PromptIncludeCycleError, RuntimeError)) as exc_info:
                    load_prompt("a", lang="de", vars_dict={})

                # Error should mention cycle or recursion
                error_msg = str(exc_info.value).lower()
                assert "cycle" in error_msg or "recursion" in error_msg


class TestCycleChecker:
    """Tests for the preflight cycle checker."""

    def test_check_prompt_cycles_finds_cycle(self, tmp_path):
        """Test: check_prompt_cycles detects cycles."""
        prompts_dir = tmp_path / "prompts"
        de_dir = prompts_dir / "de"
        de_dir.mkdir(parents=True)

        (de_dir / "x.md").write_text("{% include 'y.md' %}")
        (de_dir / "y.md").write_text("{% include 'x.md' %}")

        result = check_prompt_cycles(base_dir=prompts_dir, langs=["de"])

        assert len(result["cycles"]) > 0
        # Cycle should mention x and y
        cycle_str = str(result["cycles"])
        assert "x.md" in cycle_str or "y.md" in cycle_str

    def test_check_prompt_cycles_no_cycles(self, tmp_path):
        """Test: check_prompt_cycles returns empty when no cycles."""
        prompts_dir = tmp_path / "prompts"
        de_dir = prompts_dir / "de"
        de_dir.mkdir(parents=True)

        (de_dir / "base.md").write_text("Base content")
        (de_dir / "child.md").write_text("{% include 'base.md' %}")

        result = check_prompt_cycles(base_dir=prompts_dir, langs=["de"])

        assert len(result["cycles"]) == 0
        assert result["checked_files"] == 2


class TestLogging:
    """Tests for FIX-505 logging format."""

    def test_render_start_log(self, tmp_path, caplog):
        """Test: Render start logs [FIX-505][PROMPT] prefix."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        (prompts_dir / "test.md").write_text("{% if true %}OK{% endif %}")

        import logging
        caplog.set_level(logging.DEBUG)

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            load_prompt("test", lang="de", vars_dict={"x": "1"})

        # Should have render start or render ok log
        log_messages = [r.message for r in caplog.records]
        assert any("[FIX-505][PROMPT]" in msg for msg in log_messages)

    def test_cycle_log_format(self, tmp_path, caplog):
        """Test: Cycle detection logs have [FIX-505][PROMPT] prefix with CYCLE mention."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        # Create a cycle: a includes b, b includes a
        (prompts_dir / "a.md").write_text("A: {% include 'b.md' %}")
        (prompts_dir / "b.md").write_text("B: {% include 'a.md' %}")

        import logging
        caplog.set_level(logging.ERROR)

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            with patch("services.prompt_loader.RELEASE_STRICT_MODE", True):
                try:
                    load_prompt("a", lang="de", vars_dict={})
                except (PromptIncludeCycleError, RuntimeError):
                    pass

        log_messages = [r.message for r in caplog.records]
        # Should have cycle-related log
        assert any("CYCLE" in msg or "recursion" in msg.lower() for msg in log_messages)


class TestRegression:
    """Regression tests - normal operation should not be affected."""

    def test_simple_prompt_no_jinja(self, tmp_path):
        """Test: Simple prompts without Jinja2 work normally."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        (prompts_dir / "simple.md").write_text("Hello {{ name }}, welcome to ${company}!")

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            result = load_prompt("simple", lang="de", vars_dict={"name": "User", "company": "ACME"})

            assert result == "Hello User, welcome to ACME!"

    def test_json_prompt(self, tmp_path):
        """Test: JSON prompts still work."""
        prompts_dir = tmp_path / "prompts" / "de"
        prompts_dir.mkdir(parents=True)

        (prompts_dir / "config.json").write_text('{"system": "{{ sys }}", "user": "{{ usr }}"}')

        with patch("services.prompt_loader.BASE_DIR", tmp_path / "prompts"):
            result = load_prompt("config", lang="de", vars_dict={"sys": "A", "usr": "B"})

            assert result["system"] == "A"
            assert result["user"] == "B"

    def test_multilingual_en_prompts(self, tmp_path):
        """Test: EN prompts work with cycle detection."""
        prompts_dir = tmp_path / "prompts"
        en_dir = prompts_dir / "en"
        en_dir.mkdir(parents=True)

        (en_dir / "greeting.md").write_text("Hello {% if formal %}Sir{% else %}friend{% endif %}!")

        with patch("services.prompt_loader.BASE_DIR", prompts_dir):
            result = load_prompt("greeting", lang="en", vars_dict={"formal": True})

            assert "Hello Sir!" in result
