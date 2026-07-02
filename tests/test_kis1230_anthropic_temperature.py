# -*- coding: utf-8 -*-
"""KIS-1230-HOTFIX: claude-sonnet-5 lehnte `temperature` mit 400 ab →
alle Sonnet-Sektionen fielen in die Fallback-Kette (Decision-Boxen wurden
Boilerplate). Diese Tests sichern die Parameter-Wahl je Modellfamilie."""
from __future__ import annotations

from services.anthropic_client import build_anthropic_create_kwargs


def _kwargs(model: str) -> dict:
    return build_anthropic_create_kwargs(
        model=model,
        max_tokens=1000,
        temperature=0.3,
        system="sys",
        messages=[{"role": "user", "content": [{"type": "text", "text": "hi"}]}],
    )


def test_sonnet_5_gets_no_temperature_and_no_effort():
    kw = _kwargs("claude-sonnet-5")
    assert "temperature" not in kw
    assert "output_config" not in kw


def test_claude_5_family_gets_no_temperature():
    for model in ("claude-opus-5", "claude-haiku-5", "claude-fable-5", "claude-mythos-5"):
        assert "temperature" not in _kwargs(model), model


def test_opus_4_8_gets_no_temperature():
    # KIS-1231: Der KMU-Lauf 1114 belegte, dass opus-4-8 temperature
    # inzwischen ebenfalls mit 400 ablehnt (jede Opus-Sektion lief über
    # den reaktiven Retry) — jetzt proaktiv weglassen.
    kw = _kwargs("claude-opus-4-8")
    assert "temperature" not in kw
    assert "output_config" not in kw


def test_effort_models_get_output_config_not_temperature():
    kw = _kwargs("claude-sonnet-4-6")
    assert "temperature" not in kw
    assert kw.get("output_config", {}).get("effort")


def test_haiku_4_5_keeps_temperature():
    kw = _kwargs("claude-haiku-4-5-20251001")
    assert kw.get("temperature") == 0.3
