# -*- coding: utf-8 -*-
"""
Tests for Tool Whitelist Service

FIX-TOOL-WHITELIST: Tests for tool whitelist configuration, validation,
and vorhandene_tools integration.
"""
import pytest
from typing import Any, Dict, List


class TestToolWhitelistBasic:
    """Basic tests for tool whitelist functions."""

    def test_import_tool_whitelist(self):
        """Verify tool_whitelist can be imported."""
        from services.tool_whitelist import (
            get_categories,
            get_size_profile,
            get_recommended_tools,
            get_blacklist,
            is_tool_allowed,
        )
        assert callable(get_categories)
        assert callable(get_size_profile)
        assert callable(get_recommended_tools)

    def test_get_categories_not_empty(self):
        """Verify categories are loaded."""
        from services.tool_whitelist import get_categories
        categories = get_categories()
        assert isinstance(categories, dict)
        assert len(categories) > 0

    def test_get_size_profiles_exist(self):
        """Verify size profiles exist for all sizes."""
        from services.tool_whitelist import get_size_profile

        for size in ["solo", "team", "kmu"]:
            profile = get_size_profile(size)
            assert isinstance(profile, dict)
            assert "max_tools" in profile or "required" in profile


class TestVorhandendeToolsParsing:
    """Tests for vorhandene_tools parsing."""

    def test_parse_comma_separated(self):
        """Parse comma-separated tools."""
        from services.tool_whitelist import parse_vorhandene_tools

        result = parse_vorhandene_tools("ChatGPT, Notion, Slack")
        assert "chatgpt" in result
        assert "notion" in result
        assert "slack" in result
        assert len(result) == 3

    def test_parse_semicolon_separated(self):
        """Parse semicolon-separated tools."""
        from services.tool_whitelist import parse_vorhandene_tools

        result = parse_vorhandene_tools("ChatGPT; Notion; Slack")
        assert len(result) == 3

    def test_parse_mixed_separators(self):
        """Parse mixed separators (comma, semicolon, newline, pipe)."""
        from services.tool_whitelist import parse_vorhandene_tools

        result = parse_vorhandene_tools("ChatGPT, Notion; Slack|Asana\nMonday")
        assert len(result) == 5

    def test_parse_empty_string(self):
        """Empty string returns empty list."""
        from services.tool_whitelist import parse_vorhandene_tools

        assert parse_vorhandene_tools("") == []
        assert parse_vorhandene_tools(None) == []

    def test_parse_whitespace_handling(self):
        """Whitespace is stripped from tools."""
        from services.tool_whitelist import parse_vorhandene_tools

        result = parse_vorhandene_tools("  ChatGPT  ,  Notion  ")
        assert "chatgpt" in result
        assert "notion" in result


class TestToolsContextForPrompt:
    """Tests for get_tools_context_for_prompt function."""

    def test_context_includes_whitelist(self):
        """Context includes tool whitelist categories."""
        from services.tool_whitelist import get_tools_context_for_prompt

        context = get_tools_context_for_prompt("solo", "beratung")
        assert "Erlaubte Tool-Kategorien" in context or "## " in context

    def test_context_includes_existing_tools(self):
        """Context includes user's existing tools."""
        from services.tool_whitelist import get_tools_context_for_prompt

        context = get_tools_context_for_prompt(
            "team",
            "it",
            vorhandene_tools="ChatGPT, Notion"
        )
        assert "chatgpt" in context.lower() or "Bereits vorhandene" in context

    def test_context_for_english(self):
        """English context has English headers."""
        from services.tool_whitelist import get_tools_context_for_prompt

        context = get_tools_context_for_prompt("solo", "beratung", lang="en")
        assert "Allowed Tool Categories" in context or "User's Existing Tools" in context


class TestPostprocessToolsEmpfehlungen:
    """Tests for post-processor function."""

    def test_postprocess_detects_existing_tools(self):
        """Post-processor detects when user already has a tool."""
        from services.tool_whitelist import postprocess_tools_empfehlungen

        html = "<p>Wir empfehlen ChatGPT für Ihre Textarbeit.</p>"
        result = postprocess_tools_empfehlungen(
            html,
            "solo",
            vorhandene_tools="ChatGPT"
        )

        assert len(result["already_has"]) > 0
        assert any("chatgpt" in h["tool"].lower() for h in result["already_has"])

    def test_postprocess_returns_metadata(self):
        """Post-processor returns complete metadata."""
        from services.tool_whitelist import postprocess_tools_empfehlungen

        html = "<p>Test content</p>"
        result = postprocess_tools_empfehlungen(html, "team")

        assert "processed_html" in result
        assert "validation_issues" in result
        assert "already_has" in result
        assert "recommended_categories" in result
        assert "meta" in result

    def test_postprocess_empty_content(self):
        """Post-processor handles empty content."""
        from services.tool_whitelist import postprocess_tools_empfehlungen

        result = postprocess_tools_empfehlungen("", "solo")

        assert len(result["validation_issues"]) > 0
        assert any(i["type"] == "empty_content" for i in result["validation_issues"])


class TestValidateToolsSection:
    """Tests for section validation."""

    def test_validate_empty_returns_invalid(self):
        """Empty section is invalid."""
        from services.tool_whitelist import validate_tools_section

        is_valid, issues = validate_tools_section("", "solo")
        assert is_valid is False
        assert any(i["type"] == "empty" for i in issues)

    def test_validate_short_content_warning(self):
        """Short content triggers warning."""
        from services.tool_whitelist import validate_tools_section

        html = "<p>Short</p>"
        is_valid, issues = validate_tools_section(html, "team")

        # Should still be valid but with warning
        assert any(i["type"] == "too_short" for i in issues)

    def test_validate_good_content(self):
        """Good content with tool mentions validates."""
        from services.tool_whitelist import validate_tools_section

        html = """
        <p>Für Ihre Anforderungen empfehlen wir folgende Tools:</p>
        <ul>
            <li><strong>ChatGPT</strong>: Für Textarbeiten und Brainstorming.
            Dieser KI-Assistent hilft bei E-Mails und Content-Erstellung.</li>
            <li><strong>Notion</strong>: Für Dokumentation und Wissensmanagement.</li>
            <li><strong>Make.com</strong>: Für Automatisierung von Workflows.</li>
        </ul>
        <p>Diese Tools sind einfach zu bedienen und passen zu Ihrer Unternehmensgröße.</p>
        """
        is_valid, issues = validate_tools_section(html, "solo")

        # Should be valid
        assert is_valid is True


class TestPromptEnhancerIntegration:
    """Tests for prompt enhancer integration."""

    def test_enhancer_has_tools_whitelist_method(self):
        """PromptEnhancer has _build_tools_whitelist_context method."""
        from services.prompt_enhancer import PromptEnhancer

        enhancer = PromptEnhancer()
        assert hasattr(enhancer, "_build_tools_whitelist_context")

    def test_enhancer_injects_tools_context(self):
        """PromptEnhancer injects tools context for tools_empfehlungen."""
        from services.prompt_enhancer import PromptEnhancer

        enhancer = PromptEnhancer()
        briefing = {
            "unternehmensgroesse": "solo",
            "branche": "beratung",
            "vorhandene_tools": "ChatGPT",
        }

        context = enhancer._build_tools_whitelist_context(briefing)
        # Should return some context (not empty if whitelist is loaded)
        assert isinstance(context, str)
