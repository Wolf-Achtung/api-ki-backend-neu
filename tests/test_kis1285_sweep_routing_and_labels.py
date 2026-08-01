# -*- coding: utf-8 -*-
"""KIS-1285: Sprachgate-Feinschliff aus dem Medien-Testlauf (Briefing 1141).

Zwei Restbefunde des ansonsten sauberen Laufs:

1. Die Sweep-Übersetzung der Sektion "quick_wins" landete im Structured-
   Tool-Use-Zweig von _call_llm_for_section (der auf den Sektionsnamen
   matcht) und bekam JSON statt Marker-Text zurück — Marker-Mismatch
   deterministisch, auch im KIS-1281-Retry. Der Sweep präfixt seine Calls
   jetzt mit "lang_sweep_", damit KEIN sektionsname-basierter Sonderpfad
   greift.

2. Deutsche Überschriften-Fragmente unter der 25-Zeichen-Blockschwelle
   des Sprachgates ("Grundlage", "Pilotierung", "Konsequenz für Sie", …)
   blieben im EN-PDF stehen — jetzt Teil der deterministischen
   EN-Token-Map.
"""


class TestSweepRoutingFix:

    def test_translate_call_uses_neutral_section_key(self, monkeypatch):
        import gpt_analyze as g

        captured = {}

        def fake_llm(section_key, prompt, **kw):
            captured["section_key"] = section_key
            return None  # fail-open reicht — uns interessiert nur das Routing

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        g._translate_de_blocks_to_en(
            "quick_wins",
            ["<p>Die Angebotserstellung bindet die meisten Stunden im Team.</p>"],
        )
        assert captured["section_key"] == "lang_sweep_quick_wins"

    def test_no_section_name_special_path_matches_prefixed_key(self):
        """Der Structured-Zweig matcht exakt auf 'quick_wins' — der Präfix
        macht die Kollision unmöglich."""
        assert "lang_sweep_quick_wins" != "quick_wins"
        with open("gpt_analyze.py", encoding="utf-8") as fh:
            src = fh.read()
        assert 'section_key=f"lang_sweep_{section_key}"' in src


class TestHeadingTokenMap:

    def _san(self, html):
        from services.html_sanitizer import sanitize_en_locale_tokens
        return sanitize_en_locale_tokens(html, "en")

    def test_phase_labels_translated(self):
        assert "Foundation" in self._san("<h4>Phase 1 (0–30 Days): Grundlage</h4>")
        assert "Piloting" in self._san("<h4>Phase 2 (31–60 Days): Pilotierung</h4>")

    def test_decision_headings_translated(self):
        assert "Decision Version" in self._san("<h3>90 Days-Roadmap – Entscheidungsversion</h3>")
        assert "Decision Summary" in self._san("<h3>Gamechanger – Entscheidungszusammenfassung</h3>")

    def test_consequence_and_focus_translated(self):
        assert "What this means for you" in self._san("<h4>Konsequenz für Sie</h4>")
        out = self._san("<strong>Fokus:</strong> NDA-covered material")
        assert "Focus:" in out and "Fokus" not in out

    def test_german_report_untouched(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        html = "<h4>Phase 2: Pilotierung</h4>"
        assert sanitize_en_locale_tokens(html, "de") == html
