# -*- coding: utf-8 -*-
"""KIS-1281: Sprachgate-Retry bei Übersetzungs-Fehlschlag (EN-Lauf 1139).

Repro: quick_wins scheiterte einmalig am Marker-Protokoll ("expected 11
blocks, got []") und blieb ohne zweiten Versuch deutsch — sichtbar auf den
PDF-Seiten 9–11 des ansonsten englischen Status-Reports. Der Sweep versucht
fehlgeschlagene Sektionen jetzt genau EINMAL erneut (zählt gegen das
Budget); erst danach greift fail-open.
"""

_DE_BLOCK = (
    "<p>Die Angebotserstellung bindet erfahrungsgemäß die meisten Stunden "
    "im Team und verzögert dadurch die Vertriebszyklen erheblich.</p>"
)
_EN_BLOCK = (
    "<p>Proposal creation ties up the most hours in the team and thereby "
    "significantly delays sales cycles.</p>"
)


def _briefing_en():
    return {"lang": "en"}


class TestLangSweepRetry:

    def test_retry_after_single_failure_translates_section(self, monkeypatch):
        import gpt_analyze as g

        attempts = []

        def flaky(section_key, blocks):
            attempts.append(section_key)
            if len(attempts) == 1:
                return None  # Marker-Mismatch / leere Antwort / Exception
            return [_EN_BLOCK for _ in blocks]

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", flaky)
        sections = {"QUICK_WINS_HTML": _DE_BLOCK}
        out = g._en_language_sweep_sections(sections, _briefing_en())
        assert attempts == ["QUICK_WINS_HTML", "QUICK_WINS_HTML"]
        assert "Proposal creation" in out["QUICK_WINS_HTML"]
        assert g._LANG_SWEEP_FAILOPEN_MARKER not in out["QUICK_WINS_HTML"]

    def test_two_failures_stay_fail_open(self, monkeypatch):
        import gpt_analyze as g

        attempts = []

        def always_none(section_key, blocks):
            attempts.append(section_key)
            return None

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", always_none)
        sections = {"QUICK_WINS_HTML": _DE_BLOCK}
        out = g._en_language_sweep_sections(sections, _briefing_en())
        assert len(attempts) == 2  # genau ein Retry, keine Endlosschleife
        assert out["QUICK_WINS_HTML"].startswith(g._LANG_SWEEP_FAILOPEN_MARKER)
        assert _DE_BLOCK in out["QUICK_WINS_HTML"]

    def test_retry_respects_budget(self, monkeypatch):
        """Budget 1: Erst-Call verbraucht das Budget → kein Retry."""
        import gpt_analyze as g

        attempts = []

        def always_none(section_key, blocks):
            attempts.append(section_key)
            return None

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", always_none)
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "1")
        sections = {"QUICK_WINS_HTML": _DE_BLOCK}
        g._en_language_sweep_sections(sections, _briefing_en())
        assert len(attempts) == 1

    def test_retry_counts_against_budget_for_later_sections(self, monkeypatch):
        """Budget 2, Sektion A braucht 2 Versuche → Sektion B geht leer aus
        (fail-open) statt das Budget zu überziehen."""
        import gpt_analyze as g

        attempts = []

        def fail_first_only(section_key, blocks):
            attempts.append(section_key)
            if len(attempts) == 1:
                return None
            return [_EN_BLOCK for _ in blocks]

        monkeypatch.setattr(g, "_translate_de_blocks_to_en", fail_first_only)
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "2")
        # KIS-1283: Budget-Vergabe-Reihenfolge nur bei Parallelität 1 strikt.
        monkeypatch.setenv("LANG_SWEEP_PARALLELISM", "1")
        sections = {
            "EXEC_HTML": _DE_BLOCK,
            "RISKS_HTML": _DE_BLOCK.replace("Angebotserstellung", "Risikoanalyse"),
        }
        out = g._en_language_sweep_sections(sections, _briefing_en())
        # EXEC (Priorität 0) verbraucht beide Calls, RISKS bleibt fail-open
        assert attempts == ["EXEC_HTML", "EXEC_HTML"]
        assert "Proposal creation" in out["EXEC_HTML"]
        assert out["RISKS_HTML"].startswith(g._LANG_SWEEP_FAILOPEN_MARKER)
