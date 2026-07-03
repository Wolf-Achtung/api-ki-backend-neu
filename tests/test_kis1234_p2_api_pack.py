# -*- coding: utf-8 -*-
"""KIS-1234-P2: API-Nutzungspaket.

Deckt die vier P2-Bausteine ab:
1. briefing_contradictions — deterministische Widerspruchs-Erkennung
   (4 Regeln aus dem KIS-1234-Lauf) + Prompt-Block-Bau.
2. Prompt-Caching — _build_user_content mit/ohne Flag und Prefix.
3. Extended Thinking — _maybe_add_thinking (Default aus, Opt-in per Env).
4. Structured Output — call_anthropic_structured (Fake-Client) und der
   Structured-Quick-Wins-Zweig in _call_llm_for_section inkl. Fallback.
"""
from __future__ import annotations

import json

import pytest

from services.briefing_contradictions import (
    build_contradictions_block,
    detect_contradictions,
)
from services.anthropic_client import (
    _build_user_content,
    _maybe_add_thinking,
    _prompt_caching_enabled,
)


# =========================================================================
# 1. Widerspruchs-Erkennung
# =========================================================================

class TestDetectContradictions:

    def test_tools_keine_vs_fb2_software(self):
        findings = detect_contradictions(
            {"vorhandene_tools": "keine"},
            {"s5_software": "ChatGPT, Claude, Notion AI"},
        )
        assert len(findings) == 1
        assert "ChatGPT" in findings[0]

    def test_tools_keine_vs_api_in_ki_projekten(self):
        findings = detect_contradictions(
            {"vorhandene_tools": "keine",
             "ki_projekte": "Geplante API-Integration in den Redaktionsworkflow"},
        )
        assert len(findings) == 1

    def test_interne_kompetenz_nein_vs_hohe_kompetenz(self):
        findings = detect_contradictions(
            {"interne_ki_kompetenzen": "Nein", "ki_kompetenz": "hoch"},
        )
        assert len(findings) == 1
        assert "doppeldeutig" in findings[0]

    def test_datenreife_keine_vs_digitalisierung_9(self):
        findings = detect_contradictions(
            {"datenreife": "keine", "digitalisierungsgrad": "9"},
        )
        assert len(findings) == 1
        assert "9/10" in findings[0]

    def test_datenreife_keine_bei_niedriger_digitalisierung_ok(self):
        findings = detect_contradictions(
            {"datenreife": "keine", "digitalisierungsgrad": "3"},
        )
        assert findings == []

    def test_engpass_budget_vs_konkretes_budget(self):
        findings = detect_contradictions(
            {"groesster_engpass": "Kein Budget", "investitionsbudget": "bis 10.000 €"},
        )
        assert len(findings) == 1
        assert "10.000" in findings[0]

    def test_engpass_budget_ohne_budgetangabe_ok(self):
        findings = detect_contradictions(
            {"groesster_engpass": "Kein Budget", "investitionsbudget": "keine"},
        )
        assert findings == []

    def test_strategy_answers_via_underscore_key(self):
        """Early-Load legt FB2-Antworten unter briefing['_strategy_answers'] ab."""
        findings = detect_contradictions(
            {"vorhandene_tools": "keine",
             "_strategy_answers": {"s5_software": "Midjourney, ChatGPT"}},
        )
        assert len(findings) == 1

    def test_clean_briefing_has_no_findings(self):
        findings = detect_contradictions(
            {"vorhandene_tools": "ChatGPT", "interne_ki_kompetenzen": "Ja",
             "datenreife": "strukturiert", "digitalisierungsgrad": "8",
             "groesster_engpass": "Zeit", "investitionsbudget": "5.000 €"},
        )
        assert findings == []

    def test_kis1234_case_finds_all_four(self):
        """Der reale KIS-1234-Lauf: alle vier Spannungen gleichzeitig."""
        briefing = {
            "vorhandene_tools": "keine",
            "interne_ki_kompetenzen": "Nein",
            "ki_kompetenz": "hoch",
            "datenreife": "keine",
            "digitalisierungsgrad": "9",
            "groesster_engpass": "Kein Budget",
            "investitionsbudget": "2.000–10.000 €",
            "_strategy_answers": {"s5_software": "ChatGPT, Claude, Perplexity"},
        }
        assert len(detect_contradictions(briefing)) == 4


class TestContradictionsBlock:

    def test_empty_when_clean(self):
        assert build_contradictions_block({}) == ""

    def test_block_contains_findings_and_directive(self):
        block = build_contradictions_block(
            {"datenreife": "keine", "digitalisierungsgrad": "9"},
        )
        assert "BEKANNTE SPANNUNGEN" in block
        assert block.count("\n- ") == 1
        assert "NICHT stillschweigend" in block
        assert "Keine\nMeta-Kommentare" in block or "Meta-Kommentare" in block


# =========================================================================
# 2. Prompt-Caching
# =========================================================================

class TestPromptCaching:

    def test_enabled_by_default(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_PROMPT_CACHING", raising=False)
        assert _prompt_caching_enabled() is True

    @pytest.mark.parametrize("off", ["0", "false", "no", "off"])
    def test_disabled_via_env(self, monkeypatch, off):
        monkeypatch.setenv("ANTHROPIC_PROMPT_CACHING", off)
        assert _prompt_caching_enabled() is False

    def test_prefix_becomes_cached_block(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_PROMPT_CACHING", raising=False)
        content = _build_user_content("AUFGABE", "KONTEXT")
        assert len(content) == 2
        assert content[0]["text"] == "KONTEXT"
        assert content[0]["cache_control"] == {"type": "ephemeral"}
        assert content[1] == {"type": "text", "text": "AUFGABE"}

    def test_prefix_merged_when_caching_off(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_PROMPT_CACHING", "0")
        content = _build_user_content("AUFGABE", "KONTEXT")
        assert len(content) == 1
        assert "cache_control" not in content[0]
        assert "KONTEXT" in content[0]["text"] and "AUFGABE" in content[0]["text"]

    def test_no_prefix_single_block(self):
        content = _build_user_content("AUFGABE", None)
        assert content == [{"type": "text", "text": "AUFGABE"}]


# =========================================================================
# 3. Extended Thinking (Default: aus)
# =========================================================================

class TestMaybeAddThinking:

    def test_off_by_default(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_THINKING_BUDGET", raising=False)
        kwargs = {"max_tokens": 4000, "temperature": 0.6}
        assert _maybe_add_thinking(dict(kwargs), "gamechanger", 4000) == kwargs

    def test_section_not_listed_stays_off(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_THINKING_BUDGET", "3000")
        monkeypatch.setenv("ANTHROPIC_THINKING_SECTIONS", "gamechanger")
        out = _maybe_add_thinking({"max_tokens": 4000}, "quick_wins", 4000)
        assert "thinking" not in out

    def test_enabled_for_listed_section(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_THINKING_BUDGET", "3000")
        monkeypatch.setenv("ANTHROPIC_THINKING_SECTIONS", "gamechanger, executive_summary")
        out = _maybe_add_thinking(
            {"max_tokens": 4000, "temperature": 0.6, "output_config": {"effort": "high"}},
            "gamechanger", 4000,
        )
        assert out["thinking"] == {"type": "enabled", "budget_tokens": 3000}
        # thinking ist mit temperature/output_config unvereinbar
        assert "temperature" not in out and "output_config" not in out
        # API-Anforderung: max_tokens > budget_tokens
        assert out["max_tokens"] >= 5000

    def test_invalid_budget_ignored(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_THINKING_BUDGET", "viel")
        out = _maybe_add_thinking({"max_tokens": 4000}, "gamechanger", 4000)
        assert "thinking" not in out


# =========================================================================
# 4. Structured Output (Tool-Use)
# =========================================================================

class _FakeBlock:
    def __init__(self, type_, name="", input_=None):
        self.type = type_
        self.name = name
        self.input = input_


class _FakeMessage:
    def __init__(self, blocks):
        self.content = blocks
        self.stop_reason = "tool_use"


class _FakeMessages:
    def __init__(self, message):
        self._message = message
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._message


class _FakeClient:
    def __init__(self, message):
        self.messages = _FakeMessages(message)


class TestCallAnthropicStructured:

    SCHEMA = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}

    def _call(self, monkeypatch, message):
        import services.anthropic_client as ac
        client = _FakeClient(message)
        monkeypatch.setattr(ac, "get_anthropic_client", lambda: client)
        result = ac.call_anthropic_structured(
            "Prompt", section="quick_wins", schema=self.SCHEMA,
            tool_name="emit_result", max_tokens=500,
        )
        return result, client.messages.last_kwargs

    def test_tool_use_input_returned(self, monkeypatch):
        message = _FakeMessage([_FakeBlock("tool_use", "emit_result", {"x": "ok"})])
        result, kwargs = self._call(monkeypatch, message)
        assert result == {"x": "ok"}
        assert kwargs["tool_choice"] == {"type": "tool", "name": "emit_result"}
        assert kwargs["tools"][0]["input_schema"] == self.SCHEMA

    def test_no_tool_use_block_returns_none(self, monkeypatch):
        message = _FakeMessage([_FakeBlock("text")])
        result, _ = self._call(monkeypatch, message)
        assert result is None

    def test_none_client_returns_none(self, monkeypatch):
        import services.anthropic_client as ac
        monkeypatch.setattr(ac, "get_anthropic_client", lambda: None)
        assert ac.call_anthropic_structured(
            "Prompt", section="quick_wins", schema=self.SCHEMA,
        ) is None


class TestStructuredQuickWinsBranch:
    """Der quick_wins-Zweig in _call_llm_for_section."""

    QW = {"title": "T", "icon": "⚡", "problem": "P", "wirkung": "W",
          "umsetzung": "U", "hinweis": "H"}

    def test_structured_result_serialized_as_json_list(self, monkeypatch):
        import gpt_analyze
        import services.anthropic_client as ac
        monkeypatch.setattr(gpt_analyze, "should_use_anthropic", lambda s: True)
        monkeypatch.setattr(
            ac, "call_anthropic_structured",
            lambda *a, **k: {"quick_wins": [self.QW, self.QW, self.QW]},
        )
        out = gpt_analyze._call_llm_for_section("quick_wins", "Prompt")
        data = json.loads(out)
        assert isinstance(data, list) and len(data) == 3
        assert data[0]["title"] == "T"

    def test_fallback_to_freetext_on_empty_structured(self, monkeypatch):
        import gpt_analyze
        import services.anthropic_client as ac
        monkeypatch.setattr(gpt_analyze, "should_use_anthropic", lambda s: True)
        monkeypatch.setattr(ac, "call_anthropic_structured", lambda *a, **k: None)
        monkeypatch.setattr(gpt_analyze, "call_anthropic",
                            lambda *a, **k: "FREITEXT-FALLBACK")
        assert gpt_analyze._call_llm_for_section("quick_wins", "Prompt") == "FREITEXT-FALLBACK"

    def test_flag_off_skips_structured_path(self, monkeypatch):
        import gpt_analyze
        import services.anthropic_client as ac
        monkeypatch.setenv("QUICK_WINS_STRUCTURED", "0")
        monkeypatch.setattr(gpt_analyze, "should_use_anthropic", lambda s: True)

        def _boom(*a, **k):
            raise AssertionError("structured darf bei Flag=0 nicht aufgerufen werden")

        monkeypatch.setattr(ac, "call_anthropic_structured", _boom)
        monkeypatch.setattr(gpt_analyze, "call_anthropic", lambda *a, **k: "OK")
        assert gpt_analyze._call_llm_for_section("quick_wins", "Prompt") == "OK"

    def test_schema_pins_exactly_three_items(self):
        import gpt_analyze
        qw = gpt_analyze._QUICK_WINS_TOOL_SCHEMA["properties"]["quick_wins"]
        assert qw["minItems"] == 3 and qw["maxItems"] == 3
        assert set(qw["items"]["required"]) == {
            "title", "icon", "problem", "wirkung", "umsetzung", "hinweis",
        }
