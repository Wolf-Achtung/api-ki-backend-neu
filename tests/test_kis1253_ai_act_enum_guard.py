# -*- coding: utf-8 -*-
"""KIS-1253: Machine-Enum-Schutz für die Badge-Eindeutschung.

Lauf 1123 (Gastronomie/KMU/BW) starb hart am Quality-Gate:
'[AI_ACT_INVALID_RISK] Ungültiges AI Act Risk Level: begrenzt'.
Ursache: apply_badge_localization übersetzte mit der \\blimited\\b-Regel
auch das kanonische Machine-Feld AI_ACT_RISK_LEVEL ('limited' → 'begrenzt'),
und der Report-Validator lehnt alles außerhalb des Enums ab.

Zwei Schichten: (1) Die Lokalisierung überspringt Machine-Keys und
Kurzwerte; (2) der Validator normalisiert bekannte Eindeutschungs-Reste
zurück, statt den Report zu killen.
"""
from __future__ import annotations


class TestLocalizationSkipsMachineFields:

    def test_ai_act_risk_level_untouched(self):
        # Exakte Reproduktion von Lauf 1123
        from services.content_quality_enforcer import apply_badge_localization
        s = {"AI_ACT_RISK_LEVEL": "limited"}
        assert apply_badge_localization(s)["AI_ACT_RISK_LEVEL"] == "limited"

    def test_known_machine_keys_untouched(self):
        from services.content_quality_enforcer import apply_badge_localization
        s = {
            "RISK_AI_ACT_CLASS": "high_risk",
            "COMPLIANCE_STATUS": "non_compliant",
            "VENDOR_AUDIT_STATUS": "limited",
            "expertise_level": "beginner",
        }
        out = apply_badge_localization(dict(s))
        assert out == s

    def test_short_values_untouched(self):
        # Kurze Strings sind kanonische Einzelwerte, keine Anzeigetexte
        from services.content_quality_enforcer import apply_badge_localization
        s = {"IRGENDEIN_FELD": "limited"}
        assert apply_badge_localization(s)["IRGENDEIN_FELD"] == "limited"

    def test_long_display_html_still_localized(self):
        from services.content_quality_enforcer import apply_badge_localization
        s = {"VENDOR_AUDIT_HTML":
             "<p>Badge: ESSENTIAL — AI-ACT RISIKO limited — Komplexität: low</p>"}
        out = apply_badge_localization(s)["VENDOR_AUDIT_HTML"]
        assert "UNVERZICHTBAR" in out
        assert "RISIKO begrenzt" in out
        assert "Komplexität: niedrig" in out

    def test_cover_slug_still_localized(self):
        # 19 Zeichen — muss über der Kurzwert-Schwelle liegen
        from services.content_quality_enforcer import apply_badge_localization
        s = {"PROFILE_SLUG": "KMU/Bau/KI-Anwender"}
        assert apply_badge_localization(s)["PROFILE_SLUG"] == "KMU · Bau · KI-Anwender"


class TestValidatorHealsAliases:

    def _validator(self, risk_level):
        from services.report_validator import ReportValidator
        sections = {
            "AI_ACT_RISK_LEVEL": risk_level,
            "AI_ACT_RISK_REASONING": "<p>" + "Begründung mit Substanz. " * 40 + "</p>",
        }
        return ReportValidator(sections, {"unternehmensgroesse": "kmu"})

    def test_begrenzt_healed_no_critical(self):
        v = self._validator("begrenzt")
        v._check_ai_act_sections()
        assert v.sections["AI_ACT_RISK_LEVEL"] == "limited"
        assert not [e for e in v.errors if e.category == "AI_ACT_INVALID_RISK"]

    def test_high_risk_alias_healed(self):
        v = self._validator("high_risk")
        v._check_ai_act_sections()
        assert v.sections["AI_ACT_RISK_LEVEL"] == "high-risk"
        assert not [e for e in v.errors if e.category == "AI_ACT_INVALID_RISK"]

    def test_valid_enum_passes_unchanged(self):
        v = self._validator("limited")
        v._check_ai_act_sections()
        assert v.sections["AI_ACT_RISK_LEVEL"] == "limited"
        assert not [e for e in v.errors if e.category == "AI_ACT_INVALID_RISK"]

    def test_truly_invalid_value_still_critical(self):
        v = self._validator("banane")
        v._check_ai_act_sections()
        assert [e for e in v.errors if e.category == "AI_ACT_INVALID_RISK"]
