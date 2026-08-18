# -*- coding: utf-8 -*-
"""KIS-1288: Zwei Fixes aus dem Thinking-Audit.

1. Der Thinking-Opt-in (ANTHROPIC_THINKING_BUDGET/-SECTIONS) sendete das
   alte Format {"type": "enabled", "budget_tokens": N}. Die aktuellen
   Modelle (Sonnet 5, Opus 4.7/4.8, Claude-5-Familie) lehnen es mit 400
   ab — der Schalter hätte jede betroffene Sektion in die Fallback-Kette
   geschickt. Jetzt: {"type": "adaptive"} für 4.6+/Claude-5-Modelle,
   budget_tokens nur noch für ältere Modelle.

2. call_anthropic_structured (quick_wins u. a.) hatte kein Netz gegen
   stop_reason=max_tokens: Der tool_use-Input war dann unvollständig oder
   fehlte, die Sektion fiel auf die Fallback-Kette. Jetzt: einmaliger
   Retry mit erhöhtem Budget — dasselbe Muster wie KIS-1231 in
   call_anthropic.
"""

from services.anthropic_client import _maybe_add_thinking


# =========================================================================
# 1. Thinking-Format je Modell
# =========================================================================

class TestAdaptiveThinkingFormat:

    def _on(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_THINKING_BUDGET", "3000")
        monkeypatch.setenv("ANTHROPIC_THINKING_SECTIONS", "gamechanger")

    def test_sonnet_5_gets_adaptive(self, monkeypatch):
        self._on(monkeypatch)
        out = _maybe_add_thinking(
            {"model": "claude-sonnet-5", "max_tokens": 4000, "temperature": 0.6},
            "gamechanger", 4000,
        )
        assert out["thinking"] == {"type": "adaptive"}
        assert "budget_tokens" not in str(out["thinking"])
        assert "temperature" not in out
        assert out["max_tokens"] >= 5000

    def test_opus_4_8_gets_adaptive(self, monkeypatch):
        self._on(monkeypatch)
        out = _maybe_add_thinking(
            {"model": "claude-opus-4-8", "max_tokens": 4000}, "gamechanger", 4000,
        )
        assert out["thinking"] == {"type": "adaptive"}

    def test_sonnet_4_6_gets_adaptive_and_keeps_effort(self, monkeypatch):
        self._on(monkeypatch)
        out = _maybe_add_thinking(
            {"model": "claude-sonnet-4-6", "max_tokens": 4000,
             "output_config": {"effort": "high"}},
            "gamechanger", 4000,
        )
        assert out["thinking"] == {"type": "adaptive"}
        # effort steuert bei adaptive die Denktiefe — bleibt erhalten
        assert out["output_config"] == {"effort": "high"}

    def test_legacy_model_keeps_budget_tokens(self, monkeypatch):
        self._on(monkeypatch)
        out = _maybe_add_thinking(
            {"model": "claude-sonnet-4-5-20250929", "max_tokens": 4000,
             "temperature": 0.6, "output_config": {"effort": "high"}},
            "gamechanger", 4000,
        )
        assert out["thinking"] == {"type": "enabled", "budget_tokens": 3000}
        assert "temperature" not in out and "output_config" not in out
        assert out["max_tokens"] >= 5000

    def test_default_stays_off(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_THINKING_BUDGET", raising=False)
        out = _maybe_add_thinking(
            {"model": "claude-sonnet-5", "max_tokens": 4000}, "gamechanger", 4000,
        )
        assert "thinking" not in out


# =========================================================================
# 2. Truncation-Retry im Structured-Pfad
# =========================================================================

class _Block:
    def __init__(self, type_, name="", input_=None):
        self.type = type_
        self.name = name
        self.input = input_


class _Msg:
    def __init__(self, blocks, stop_reason="tool_use"):
        self.content = blocks
        self.stop_reason = stop_reason


class _SeqMessages:
    """Liefert vorbereitete Messages in Reihenfolge, protokolliert kwargs."""

    def __init__(self, messages):
        self._messages = list(messages)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._messages.pop(0)


class _SeqClient:
    def __init__(self, messages):
        self.messages = _SeqMessages(messages)


SCHEMA = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}


def _call_structured(monkeypatch, messages, **env):
    import services.anthropic_client as ac
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    client = _SeqClient(messages)
    monkeypatch.setattr(ac, "get_anthropic_client", lambda: client)
    result = ac.call_anthropic_structured(
        "Prompt", section="quick_wins", schema=SCHEMA,
        tool_name="emit_result", max_tokens=500,
    )
    return result, client.messages.calls


class TestStructuredTruncationRetry:

    def test_max_tokens_triggers_retry_with_raised_budget(self, monkeypatch):
        first = _Msg([_Block("tool_use", "emit_result", {})], stop_reason="max_tokens")
        second = _Msg([_Block("tool_use", "emit_result", {"x": "voll"})])
        result, calls = _call_structured(monkeypatch, [first, second])
        assert result == {"x": "voll"}
        assert len(calls) == 2
        assert calls[0]["max_tokens"] == 500
        assert calls[1]["max_tokens"] > 500

    def test_no_retry_when_stop_is_tool_use(self, monkeypatch):
        only = _Msg([_Block("tool_use", "emit_result", {"x": "ok"})])
        result, calls = _call_structured(monkeypatch, [only])
        assert result == {"x": "ok"}
        assert len(calls) == 1

    def test_retry_disabled_via_env(self, monkeypatch):
        first = _Msg([_Block("tool_use", "emit_result", {"x": "kurz"})],
                     stop_reason="max_tokens")
        result, calls = _call_structured(
            monkeypatch, [first], ANTHROPIC_TRUNCATION_RETRY="0",
        )
        # Kein Retry — die (möglicherweise unvollständige) Erst-Antwort zählt
        assert result == {"x": "kurz"}
        assert len(calls) == 1

    def test_retry_also_truncated_keeps_first_answer(self, monkeypatch):
        first = _Msg([_Block("tool_use", "emit_result", {"x": "erst"})],
                     stop_reason="max_tokens")
        second = _Msg([_Block("tool_use", "emit_result", {"x": "zweit"})],
                      stop_reason="max_tokens")
        result, calls = _call_structured(monkeypatch, [first, second])
        assert result == {"x": "erst"}
        assert len(calls) == 2

    def test_retry_exception_keeps_first_answer(self, monkeypatch):
        import services.anthropic_client as ac

        first = _Msg([_Block("tool_use", "emit_result", {"x": "erst"})],
                     stop_reason="max_tokens")

        class _FailSecond:
            def __init__(self):
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                if len(self.calls) == 1:
                    return first
                raise RuntimeError("boom")

        client = type("C", (), {})()
        client.messages = _FailSecond()
        monkeypatch.setattr(ac, "get_anthropic_client", lambda: client)
        result = ac.call_anthropic_structured(
            "Prompt", section="quick_wins", schema=SCHEMA,
            tool_name="emit_result", max_tokens=500,
        )
        assert result == {"x": "erst"}
        assert len(client.messages.calls) == 2
