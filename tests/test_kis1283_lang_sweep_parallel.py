# -*- coding: utf-8 -*-
"""KIS-1283: Paralleles Sprachgate (EN-Lauf 1140).

Repro: Der Sweep übersetzte ~60 Sektionen sequenziell (~8 s/Call) und
machte damit 8,6 der 19 Minuten Gesamtlaufzeit des EN-Status-Reports aus.
Die Übersetzungs-Calls sind unabhängig und laufen jetzt mit N Threads
(ENV LANG_SWEEP_PARALLELISM, Default 4); das Budget bleibt über einen
Lock global exakt gedeckelt. Parallelität 1 == altes Verhalten.
"""

import threading
import time


def _de(i):
    return (
        "<p>Die Angebotserstellung Variante %d bindet erfahrungsgemäß die "
        "meisten Stunden im Team und verzögert dadurch die Vertriebszyklen.</p>" % i
    )


class TestParallelismConfig:

    def test_default_is_4(self, monkeypatch):
        import gpt_analyze
        monkeypatch.delenv("LANG_SWEEP_PARALLELISM", raising=False)
        assert gpt_analyze._lang_sweep_parallelism() == 4

    def test_env_override(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "8")
        assert gpt_analyze._lang_sweep_parallelism() == 8

    def test_invalid_falls_back(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "schnell")
        assert gpt_analyze._lang_sweep_parallelism() == 4

    def test_minimum_is_1(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "0")
        assert gpt_analyze._lang_sweep_parallelism() == 1


class TestParallelSweep:

    def test_all_sections_translated_under_parallelism(self, monkeypatch):
        """6 distinkte Sektionen, 4 Threads: alle übersetzt, kein fail-open."""
        import gpt_analyze as g

        def ok(section_key, blocks):
            return ["<p>Proposal creation ties up hours (%s).</p>" % section_key
                    for _ in blocks]

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", ok)
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "4")
        sections = {f"SEC_{i}_HTML": _de(i) for i in range(6)}
        out = g._en_language_sweep_sections(sections, {"lang": "en"})
        for i in range(6):
            assert "Proposal creation" in out[f"SEC_{i}_HTML"]
            assert g._LANG_SWEEP_FAILOPEN_MARKER not in out[f"SEC_{i}_HTML"]

    def test_calls_actually_run_concurrently(self, monkeypatch):
        """Mit 4 Threads und 6 Jobs à 50 ms überlappen sich Calls messbar."""
        import gpt_analyze as g

        lock = threading.Lock()
        state = {"active": 0, "peak": 0}

        def slow_ok(section_key, blocks):
            with lock:
                state["active"] += 1
                state["peak"] = max(state["peak"], state["active"])
            time.sleep(0.05)
            with lock:
                state["active"] -= 1
            return ["<p>Translated block.</p>" for _ in blocks]

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", slow_ok)
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "4")
        sections = {f"SEC_{i}_HTML": _de(i) for i in range(6)}
        g._en_language_sweep_sections(sections, {"lang": "en"})
        assert state["peak"] > 1

    def test_budget_cap_is_exact_under_parallelism(self, monkeypatch):
        """Budget 5, 12 fehlschlagende Jobs, 4 Threads: exakt 5 Calls."""
        import gpt_analyze as g

        lock = threading.Lock()
        calls = []

        def always_none(section_key, blocks):
            with lock:
                calls.append(section_key)
            return None

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", always_none)
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "5")
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "4")
        sections = {f"SEC_{i:02d}_HTML": _de(i) for i in range(12)}
        out = g._en_language_sweep_sections(sections, {"lang": "en"})
        assert len(calls) == 5
        # Alle Sektionen fail-open (übersetzt wurde nichts erfolgreich)
        for key in sections:
            assert out[key].startswith(g._LANG_SWEEP_FAILOPEN_MARKER)

    def test_twins_still_inherit_under_parallelism(self, monkeypatch):
        """Inhaltsgleiche Twins erben Übersetzung ohne eigenen Call."""
        import gpt_analyze as g

        lock = threading.Lock()
        calls = []

        def ok(section_key, blocks):
            with lock:
                calls.append(section_key)
            return ["<p>Translated once.</p>" for _ in blocks]

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", ok)
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "4")
        same = _de(1)
        sections = {"EXEC_HTML": same, "exec": same, "OTHER_HTML": _de(2)}
        out = g._en_language_sweep_sections(sections, {"lang": "en"})
        assert len(calls) == 2  # EXEC_HTML + OTHER_HTML, Twin kopiert
        assert out["exec"] == out["EXEC_HTML"]

    def test_sequential_mode_unchanged(self, monkeypatch):
        """Parallelität 1: exakt ein Call pro distinkter Sektion, in
        Prioritätsreihenfolge (_HTML vor plain)."""
        import gpt_analyze as g

        calls = []

        def ok(section_key, blocks):
            calls.append(section_key)
            return ["<p>Translated.</p>" for _ in blocks]

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", ok)
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "1")
        sections = {"notes": _de(1), "RISK_HTML": _de(2)}
        g._en_language_sweep_sections(sections, {"lang": "en"})
        assert calls == ["RISK_HTML", "notes"]
