# -*- coding: utf-8 -*-
"""KIS-1236: Quick-Wins-Absturz aus Lauf 1119 (Briefing Bildung/KMU/Bayern).

Zwei Ursachen, zwei Fixes:
1. _QUICK_WINS_TOOL_SCHEMA pinnte exakt 3 Items, der KMU-Prompt fordert
   aber 4–5 — der Konflikt lieferte einen leeren tool_use-Input und warf
   die Pipeline in den Freitext-Fallback. → Schema erlaubt jetzt 3–5.
2. Das Freitext-Fallback-JSON enthielt ein literales Steuerzeichen
   (Newline) in einem String ("Invalid control character at char 2616"),
   json.loads(strict=True) lehnte ab, FIX-499-STRICT blockte den ganzen
   Lauf. → strict=False-Retry heilt exakt diese Klasse; echt kaputtes
   JSON blockt weiterhin.
"""
from __future__ import annotations

import json

import gpt_analyze
from services.quickwins_renderer import render_quickwins_premium_json


def _qw_item(title: str = "Titel", body: str = "Text") -> dict:
    return {
        "title": title, "icon": "⚡", "problem": body,
        "wirkung": body, "umsetzung": body, "hinweis": "siehe Business Case",
    }


def _json_with_literal_newline(n_items: int = 3) -> str:
    """Gültiges QW-JSON, aber mit literalem \\n INNERHALB eines Strings —
    exakt die Fehlerklasse aus Lauf 1119."""
    items = [_qw_item(f"QW {i+1}") for i in range(n_items)]
    raw = json.dumps(items, ensure_ascii=False)
    return raw.replace("Text", "Zeile 1\nZeile 2", 1)


class TestParserStrictHeal:

    def test_literal_newline_in_string_is_healed(self):
        raw = _json_with_literal_newline()
        # Vorbedingung: strict=True lehnt genau dieses JSON ab
        try:
            json.loads(raw)
            raise AssertionError("Testdaten enthalten kein Steuerzeichen")
        except json.JSONDecodeError as e:
            assert "control character" in str(e).lower()
        parsed = gpt_analyze._parse_quick_wins_json(raw)
        assert parsed is not None and len(parsed) == 3
        assert "Zeile 1\nZeile 2" in parsed[0]["problem"] + parsed[0]["wirkung"]

    def test_truly_broken_json_still_returns_none(self):
        assert gpt_analyze._parse_quick_wins_json('[{"title": "abbruch mitten') is None

    def test_clean_json_unaffected(self):
        raw = json.dumps([_qw_item() for _ in range(4)], ensure_ascii=False)
        parsed = gpt_analyze._parse_quick_wins_json(raw)
        assert parsed is not None and len(parsed) == 4


class TestPremiumRendererStrictHeal:

    def test_premium_renderer_heals_control_char(self):
        raw = _json_with_literal_newline()
        html = render_quickwins_premium_json(raw, template_mode="FULL", run_id="t1236")
        assert html is not None and "QW 1" in html

    def test_premium_renderer_broken_json_returns_none(self):
        assert render_quickwins_premium_json(
            '[{"title": "abbruch', template_mode="FULL", run_id="t1236",
        ) is None


class TestStructuredSchemaAndDiagnostics:

    def test_schema_range_matches_prompt_contract(self):
        # Prompt: solo=3, team=4, KMU=4–5 → Schema muss 3–5 zulassen.
        qw = gpt_analyze._QUICK_WINS_TOOL_SCHEMA["properties"]["quick_wins"]
        assert qw["minItems"] == 3
        assert qw["maxItems"] == 5

    def test_five_item_structured_result_serialized(self, monkeypatch):
        import services.anthropic_client as ac
        monkeypatch.setattr(gpt_analyze, "should_use_anthropic", lambda s: True)
        monkeypatch.setattr(
            ac, "call_anthropic_structured",
            lambda *a, **k: {"quick_wins": [_qw_item(f"QW {i}") for i in range(5)]},
        )
        out = gpt_analyze._call_llm_for_section("quick_wins", "Prompt")
        assert len(json.loads(out)) == 5

    def test_empty_structured_logs_diagnostics(self, monkeypatch, caplog):
        import services.anthropic_client as ac
        monkeypatch.setattr(gpt_analyze, "should_use_anthropic", lambda s: True)
        monkeypatch.setattr(
            ac, "call_anthropic_structured", lambda *a, **k: {"quick_wins": []},
        )
        monkeypatch.setattr(gpt_analyze, "call_anthropic", lambda *a, **k: "FALLBACK")
        with caplog.at_level("WARNING"):
            out = gpt_analyze._call_llm_for_section("quick_wins", "Prompt")
        assert out == "FALLBACK"
        diag = [r.message for r in caplog.records if "Structured quick_wins leer" in r.message]
        assert diag and "quick_wins_type=list" in diag[0] and "len=0" in diag[0]
