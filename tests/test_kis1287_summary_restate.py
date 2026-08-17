# -*- coding: utf-8 -*-
"""KIS-1287: Restate-Block in der Chat-Schlusszusammenfassung.

Die Schlusszusammenfassung spiegelt Ziel, Budget/Zeitrahmen und
Schmerzpunkte kompakt über der Feldliste — genau dort, wo der Flow
"Sind alle Angaben korrekt?" fragt. Der Nutzer prüft so die drei
Angaben, die den Report am stärksten formen, ohne die Detailliste
durchzugehen.

Regeln:
- Rein deterministisch, kein LLM-Call.
- Freitext im vollen Wortlaut (nie paraphrasiert).
- Block erscheint nur bei mindestens zwei belegten Zeilen.
- Der Summary-Marker bleibt die erste Zeile (Frontend-Erkennung).
- Kein Firmenname — der Block nutzt nur bestehende Felder.
"""

from services.chat_conversation import build_summary, _build_restate_lines


_R1_FULL = {
    "branche": "medien",
    "unternehmensgroesse": "2-10",
    "strategische_ziele": "Renderzeiten senken und Angebote schneller erstellen.",
    "investitionsbudget": "2000_10000",
    "zeitbudget": "2-5",
    "top_zeitfresser": "Rotoscoping, Angebotserstellung, Versionsabstimmung mit Kunden.",
}

_STRATEGY_FULL = {
    "s5_vision": "In zwei Jahren läuft die Rohschnitt-Sichtung KI-gestützt.",
    "s1_budget": "10000_50000",
    "s2_zeitrahmen": "1-3_monate",
    "s4_engpass": "Zu wenig Zeit neben dem Tagesgeschäft.",
}


class TestRestateBlockDE:

    def test_block_appears_after_marker(self):
        out = build_summary(_R1_FULL, "r1", lang="de")
        assert out.startswith("**Zusammenfassung Ihrer Angaben:**")
        assert "Das habe ich verstanden:" in out
        # Block steht vor der ersten Sektionsüberschrift
        assert out.index("Das habe ich verstanden:") < out.index("**Ihr Unternehmen**")

    def test_goal_and_pain_points_verbatim(self):
        out = build_summary(_R1_FULL, "r1", lang="de")
        assert "- Ihr Ziel: Renderzeiten senken und Angebote schneller erstellen." in out
        assert ("- Ihre größten Zeitfresser: Rotoscoping, Angebotserstellung, "
                "Versionsabstimmung mit Kunden.") in out

    def test_budget_line_joins_both_fields(self):
        lines = _build_restate_lines(_R1_FULL, "r1", "de")
        budget = [l for l in lines if l.startswith("- Ihr Budget und Zeitrahmen:")]
        assert len(budget) == 1
        # Beide Feldwerte in einer Zeile (Enum-Labels oder Rohwerte)
        assert budget[0].count(",") >= 1

    def test_goal_fallback_chain(self):
        data = dict(_R1_FULL)
        del data["strategische_ziele"]
        data["ki_ziele"] = ["zeitersparnis", "qualitaet"]
        lines = _build_restate_lines(data, "r1", "de")
        assert any(l.startswith("- Ihr Ziel:") for l in lines)


class TestRestateBlockEN:

    def test_english_labels_and_header(self):
        out = build_summary(_R1_FULL, "r1", lang="en")
        assert out.startswith("**Summary of your details:**")
        assert "This is what I understood:" in out
        assert "- Your goal: Renderzeiten senken" in out  # Freitext bleibt wörtlich
        assert "- Your biggest time sinks:" in out

    def test_strategy_bottleneck_en(self):
        lines = _build_restate_lines(_STRATEGY_FULL, "strategy", "en")
        assert any(l.startswith("- Your biggest bottleneck:") for l in lines)


class TestRestateBlockGuards:

    def test_hidden_below_two_rows(self):
        # Nur eine belegte Zeile → kein Block
        data = {"top_zeitfresser": "Rotoscoping."}
        assert _build_restate_lines(data, "r1", "de") == []
        out = build_summary(data, "r1", lang="de")
        assert "Das habe ich verstanden:" not in out

    def test_keine_angabe_values_skipped(self):
        data = dict(_R1_FULL)
        data["investitionsbudget"] = "keine_angabe"
        data["zeitbudget"] = "keine_angabe"
        lines = _build_restate_lines(data, "r1", "de")
        assert not any("Budget" in l for l in lines)
        # Ziel + Zeitfresser bleiben → Block erscheint trotzdem
        assert len(lines) == 3

    def test_empty_collected_fields_no_block(self):
        assert _build_restate_lines({}, "r1", "de") == []
        out = build_summary({}, "r1", lang="de")
        assert out.startswith("**Zusammenfassung Ihrer Angaben:**")

    def test_unknown_report_type_falls_back_silently(self):
        assert _build_restate_lines(_R1_FULL, "unknown_type", "de") == []

    def test_strategy_block_de(self):
        lines = _build_restate_lines(_STRATEGY_FULL, "strategy", "de")
        assert lines[0] == "Das habe ich verstanden:"
        assert any(l.startswith("- Ihr größter Engpass: Zu wenig Zeit") for l in lines)

    def test_no_company_name_key_involved(self):
        # Sicherheits-Invariante: Der Block fragt keinen Firmennamen ab
        # und referenziert kein firmen-/namensartiges Feld.
        from services.chat_conversation import _RESTATE_SOURCES
        for spec in _RESTATE_SOURCES.values():
            for _, _, fields, _ in spec:
                for f in fields:
                    assert "firma" not in f.lower()
                    assert "company" not in f.lower()
                    assert "name" not in f.lower()
