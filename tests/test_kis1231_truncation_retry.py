# -*- coding: utf-8 -*-
"""KIS-1231: max_tokens-Truncation-Härtung.

KMU-Lauf 1114: quick_wins (claude-sonnet-5) endete mit stop_reason=
max_tokens, das JSON brach mitten im String ab und FIX-499-QW warf im
STRICT-Modus einen RuntimeError — der GESAMTE Report brach ab. Weitere
7 Sektionen trafen ebenfalls ihr Token-Limit und degradierten zu
Fallback/Expand.

Zwei Verteidigungslinien, beide hier getestet:
1. anthropic_client: einmaliger Retry mit erhöhtem Budget bei
   stop_reason=max_tokens (Faktor/Cap/Off-Schalter per ENV).
2. gpt_analyze._salvage_truncated_json_array: abgeschnittenes
   Quick-Wins-JSON auf das letzte vollständige Objekt zurückschneiden,
   statt den Report abzubrechen.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import services.anthropic_client as ac


# =========================================================================
# 1. Budget-Helfer
# =========================================================================

class TestRetryBudget:

    def test_default_doubles(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_TRUNCATION_RETRY_FACTOR", raising=False)
        monkeypatch.delenv("ANTHROPIC_TRUNCATION_RETRY_CAP", raising=False)
        assert ac._truncation_retry_max_tokens(5000) == 10000

    def test_cap_applies(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_TRUNCATION_RETRY_FACTOR", raising=False)
        monkeypatch.setenv("ANTHROPIC_TRUNCATION_RETRY_CAP", "12000")
        assert ac._truncation_retry_max_tokens(7000) == 12000

    def test_never_below_current(self, monkeypatch):
        # Budget bereits über dem Cap → kein sinnvoller Retry (current zurück)
        monkeypatch.setenv("ANTHROPIC_TRUNCATION_RETRY_CAP", "4000")
        assert ac._truncation_retry_max_tokens(5000) == 5000

    def test_invalid_env_falls_back(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_TRUNCATION_RETRY_FACTOR", "kaputt")
        monkeypatch.setenv("ANTHROPIC_TRUNCATION_RETRY_CAP", "auch kaputt")
        assert ac._truncation_retry_max_tokens(5000) == 10000

    def test_enabled_by_default(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_TRUNCATION_RETRY", raising=False)
        assert ac._truncation_retry_enabled() is True

    @pytest.mark.parametrize("val", ["0", "false", "off", "no"])
    def test_can_be_disabled(self, monkeypatch, val):
        monkeypatch.setenv("ANTHROPIC_TRUNCATION_RETRY", val)
        assert ac._truncation_retry_enabled() is False


# =========================================================================
# 2. call_anthropic: Retry-Verhalten (mit Fake-Client)
# =========================================================================

def _msg(text: str, stop_reason: str, tokens: int = 100):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        usage=SimpleNamespace(output_tokens=tokens),
    )


class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses):
        self.messages = _FakeMessages(responses)


@pytest.fixture()
def _clean_env(monkeypatch):
    for var in ("ANTHROPIC_TRUNCATION_RETRY", "ANTHROPIC_TRUNCATION_RETRY_FACTOR",
                "ANTHROPIC_TRUNCATION_RETRY_CAP"):
        monkeypatch.delenv(var, raising=False)
    yield monkeypatch


def test_truncated_response_triggers_retry_with_doubled_budget(_clean_env):
    fake = _FakeClient([
        _msg("abgeschnitten", "max_tokens"),
        _msg("vollständige Antwort", "end_turn"),
    ])
    _clean_env.setattr(ac, "get_anthropic_client", lambda: fake)

    out = ac.call_anthropic(
        "Prompt", section="quick_wins", max_tokens=5000,
        model="claude-sonnet-5",
    )

    assert out == "vollständige Antwort"
    assert len(fake.messages.calls) == 2
    assert fake.messages.calls[0]["max_tokens"] == 5000
    assert fake.messages.calls[1]["max_tokens"] == 10000


def test_retry_disabled_keeps_truncated_text(_clean_env):
    _clean_env.setenv("ANTHROPIC_TRUNCATION_RETRY", "0")
    fake = _FakeClient([_msg("abgeschnitten", "max_tokens")])
    _clean_env.setattr(ac, "get_anthropic_client", lambda: fake)

    out = ac.call_anthropic(
        "Prompt", section="quick_wins", max_tokens=5000,
        model="claude-sonnet-5",
    )

    assert out == "abgeschnitten"
    assert len(fake.messages.calls) == 1


def test_retry_also_truncated_keeps_longer_text(_clean_env):
    fake = _FakeClient([
        _msg("kurz", "max_tokens"),
        _msg("etwas längerer, aber wieder abgeschnittener Text", "max_tokens"),
    ])
    _clean_env.setattr(ac, "get_anthropic_client", lambda: fake)

    out = ac.call_anthropic(
        "Prompt", section="risks", max_tokens=4000,
        model="claude-sonnet-5",
    )

    # Retry lief erneut ins Limit, hat aber mehr geliefert → nimm den Retry
    assert out == "etwas längerer, aber wieder abgeschnittener Text"
    assert len(fake.messages.calls) == 2


def test_retry_failure_keeps_first_answer(_clean_env):
    class _ExplodingMessages(_FakeMessages):
        def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return _msg("erste Antwort", "max_tokens")
            raise RuntimeError("API down")

    fake = _FakeClient([])
    fake.messages = _ExplodingMessages([])
    _clean_env.setattr(ac, "get_anthropic_client", lambda: fake)

    out = ac.call_anthropic(
        "Prompt", section="roadmap", max_tokens=5000,
        model="claude-sonnet-5",
    )

    assert out == "erste Antwort"


def test_clean_finish_does_not_retry(_clean_env):
    fake = _FakeClient([_msg("fertig", "end_turn")])
    _clean_env.setattr(ac, "get_anthropic_client", lambda: fake)

    out = ac.call_anthropic(
        "Prompt", section="quick_wins", max_tokens=5000,
        model="claude-sonnet-5",
    )

    assert out == "fertig"
    assert len(fake.messages.calls) == 1


# =========================================================================
# 3. Truncated-JSON-Salvage (gpt_analyze)
# =========================================================================

@pytest.fixture(scope="module")
def salvage():
    from gpt_analyze import _salvage_truncated_json_array
    return _salvage_truncated_json_array


_QW = {
    "title": "Posteingang automatisch sortieren",
    "icon": "📥",
    "problem": "Manuelle Sichtung kostet täglich Zeit",
    "wirkung": "Spart wöchentlich mehrere Stunden",
    "umsetzung": "Regelbasierte Zuordnung mit KI-Klassifikator",
    "hinweis": "siehe Business Case",
}


class TestSalvageTruncatedJson:

    def test_unterminated_string_is_salvaged(self, salvage):
        """Exakt der KMU-1114-Fall: Abbruch mitten in einem String-Wert."""
        full = json.dumps([_QW, _QW, _QW], ensure_ascii=False)
        truncated = full[: full.rfind('"umsetzung"') + 30]  # bricht im 3. Objekt ab
        out = salvage(truncated)
        assert out is not None
        parsed = json.loads(out)
        assert len(parsed) == 2
        assert parsed[0]["title"] == _QW["title"]

    def test_truncation_between_objects(self, salvage):
        full = json.dumps([_QW, _QW], ensure_ascii=False)
        # Abbruch direkt nach dem Komma zwischen den Objekten
        first_end = full.find("},") + 2
        out = salvage(full[:first_end])
        assert out is not None
        assert len(json.loads(out)) == 1

    def test_complete_array_passes_through(self, salvage):
        full = json.dumps([_QW], ensure_ascii=False)
        out = salvage(full)
        assert out is not None
        assert json.loads(out) == [_QW]

    def test_no_complete_object_returns_none(self, salvage):
        assert salvage('[{"title": "abgeschni') is None

    def test_garbage_returns_none(self, salvage):
        assert salvage("kein json hier") is None
        assert salvage("") is None
        assert salvage(None) is None

    def test_nested_structures_survive(self, salvage):
        qw = dict(_QW, schritte=["a", "b", {"c": "d"}])
        full = json.dumps([qw, qw], ensure_ascii=False)
        truncated = full[: len(full) - 40]  # bricht im 2. Objekt ab
        out = salvage(truncated)
        assert out is not None
        parsed = json.loads(out)
        assert parsed[0]["schritte"][2] == {"c": "d"}

    def test_escaped_quotes_do_not_confuse_parser(self, salvage):
        qw = dict(_QW, problem='Er sagte \\"Stopp\\" und ging')
        full = json.dumps([qw, _QW], ensure_ascii=False)
        truncated = full[: len(full) - 25]
        out = salvage(truncated)
        assert out is not None
        assert len(json.loads(out)) == 1
