# -*- coding: utf-8 -*-
"""KIS-1276: Phase-1 Medien-Fokus im CHAT-Modus (ENV VISIBLE_BRANCHES).

Deckt ab (ohne starlette TestClient — httpx fehlt lokal; die Helper werden
direkt getestet):

1. Branchen-Chips werden zur Laufzeit über VISIBLE_BRANCHES gefiltert
   (_visible_branche_qr_options, Single Source of Truth:
   services.branch_mapping.get_frontend_branch_options — fail-open).
2. Single-Branch-Modus (VISIBLE_BRANCHES=medien): branche-Autofill,
   erste Frage = medien_sparte, Welcome-Variante DE/EN.
3. medien_sparte-QR-Optionen (7 Sparten, DE-Labels wie im Formbuilder,
   EN-Labels aus services.answers_normalizer.MEDIEN_SPARTEN_LABELS_EN).
4. Freitext-Zuordnung (_normalize_medien_sparte) inkl. Skip-Semantik.
5. Keine Verhaltensänderung ohne ENV (Default = heutiges Verhalten).
"""

import pytest

import routes.chat as chat
from routes.chat import (
    MEDIEN_SPARTE_FIELD,
    PHASE_1A_QR_FIELDS,
    R1_WELCOME,
    R1_WELCOME_EN,
    STRATEGY_WELCOME,
    STRATEGY_WELCOME_EN,
    _apply_single_branch_autofill,
    _branche_value_allowed,
    _build_quick_replies,
    _get_first_qr_fields,
    _get_next_phase_1a_field,
    _get_welcome,
    _is_medien_sparte_other,
    _normalize_medien_sparte,
    _phase_1a_qr_fields,
    _should_skip_qr_field,
    _single_visible_branche,
    _visible_branche_qr_options,
    _QR_OPTIONS,
)
from services.answers_normalizer import MEDIEN_SPARTEN_LABELS_EN

ALL_13 = [
    "marketing", "beratung", "it", "finanzen", "handel", "bildung",
    "verwaltung", "gesundheit", "bau", "medien", "industrie",
    "logistik", "gastronomie",
]

SPARTEN_7 = [
    "produktion", "post_vfx", "games", "verlag_publishing",
    "musik_audio", "agentur_design", "content_creation",
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Default: kein Filter aktiv (wie in allen bestehenden Tests)."""
    monkeypatch.delenv("VISIBLE_BRANCHES", raising=False)
    yield


# ===========================================================================
# 1) Branchen-Chips-Filter
# ===========================================================================

class TestVisibleBrancheQrOptions:
    def test_default_all_13(self):
        options = _visible_branche_qr_options()
        assert [o["value"] for o in options] == ALL_13

    def test_default_identical_to_qr_options(self):
        assert _visible_branche_qr_options() == _QR_OPTIONS["branche"]

    def test_medien_only(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        options = _visible_branche_qr_options()
        assert [o["value"] for o in options] == ["medien"]
        assert options[0]["label"] == "Medien & Kreativwirtschaft"
        # EN-Label (label_en) bleibt am Options-Dict erhalten
        assert options[0]["label_en"] == "Media & Creative Industries"

    def test_subset(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien,it")
        values = [o["value"] for o in _visible_branche_qr_options()]
        assert sorted(values) == ["it", "medien"]

    def test_fail_open_invalid(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "gibtsnicht")
        assert len(_visible_branche_qr_options()) == 13

    def test_fail_open_empty(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "   ")
        assert len(_visible_branche_qr_options()) == 13

    def test_build_quick_replies_branche_filtered(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        qrs = _build_quick_replies(["branche"], "r1", {})
        assert len(qrs) == 1
        assert [o.value for o in qrs[0].options] == ["medien"]

    def test_build_quick_replies_branche_default_13(self):
        qrs = _build_quick_replies(["branche"], "r1", {})
        assert [o.value for o in qrs[0].options] == ALL_13

    def test_branche_value_allowed(self, monkeypatch):
        # Default: fail-open, alles erlaubt
        assert _branche_value_allowed("it")
        assert _branche_value_allowed("medien")
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        assert _branche_value_allowed("medien")
        assert not _branche_value_allowed("it")


# ===========================================================================
# 2) Single-Branch-Modus: Autofill, erste Frage, Welcome
# ===========================================================================

class TestSingleBranchMode:
    def test_single_visible_branche(self, monkeypatch):
        assert _single_visible_branche() is None
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        assert _single_visible_branche() == "medien"
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien,it")
        assert _single_visible_branche() is None

    def test_autofill_sets_branche(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        collected = {}
        assert _apply_single_branch_autofill(collected) == "medien"
        assert collected["branche"] == "medien"

    def test_autofill_noop_without_env(self):
        collected = {}
        assert _apply_single_branch_autofill(collected) is None
        assert collected == {}

    def test_autofill_respects_prefill(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        collected = {"branche": "it"}  # explizites Prefill hat Vorrang
        assert _apply_single_branch_autofill(collected) is None
        assert collected["branche"] == "it"

    def test_first_qr_fields_default(self):
        assert _get_first_qr_fields("r1") == ["branche"]

    def test_first_qr_fields_medien(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        assert _get_first_qr_fields("r1") == [MEDIEN_SPARTE_FIELD]

    def test_first_qr_fields_single_non_medien(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "it")
        assert _get_first_qr_fields("r1") == ["unternehmensgroesse"]

    def test_strategy_flow_untouched(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        assert _get_first_qr_fields("strategy") == ["s1_budget"]
        assert _get_welcome("strategy") == STRATEGY_WELCOME
        assert _get_welcome("strategy", "en") == STRATEGY_WELCOME_EN

    def test_welcome_default_unchanged(self):
        assert _get_welcome("r1") == R1_WELCOME
        assert _get_welcome("r1", "en") == R1_WELCOME_EN
        assert "In welcher Branche" in _get_welcome("r1")

    def test_welcome_medien_de(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        welcome = _get_welcome("r1")
        assert "In welcher Sparte der Medien- & Kreativbranche" in welcome
        assert "In welcher Branche" not in welcome
        # Intro bleibt inhaltlich identisch zum Standard-Welcome
        assert welcome.split("\n\n")[0] == R1_WELCOME.split("\n\n")[0]

    def test_welcome_medien_en(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        welcome = _get_welcome("r1", "en")
        assert "Which sector of the media & creative industries" in welcome
        assert "What industry" not in welcome
        assert welcome.split("\n\n")[0] == R1_WELCOME_EN.split("\n\n")[0]

    def test_welcome_single_non_medien(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "it")
        assert "Wie groß ist Ihr Unternehmen" in _get_welcome("r1")
        assert "How large is your company" in _get_welcome("r1", "en")


# ===========================================================================
# 3) Phase-1a-Sequenz + Skip-Logik
# ===========================================================================

class TestPhase1aSequence:
    def test_default_sequence_unchanged(self):
        assert _phase_1a_qr_fields() == PHASE_1A_QR_FIELDS
        assert MEDIEN_SPARTE_FIELD not in _phase_1a_qr_fields()

    def test_medien_sequence_inserts_sparte_after_branche(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        fields = _phase_1a_qr_fields()
        assert fields.index(MEDIEN_SPARTE_FIELD) == fields.index("branche") + 1
        # Restsequenz unverändert
        assert [f for f in fields if f != MEDIEN_SPARTE_FIELD] == PHASE_1A_QR_FIELDS

    def test_next_field_is_sparte_after_autofill(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        assert _get_next_phase_1a_field({"branche": "medien"}) == MEDIEN_SPARTE_FIELD

    def test_next_field_after_sparte_collected(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        collected = {"branche": "medien", MEDIEN_SPARTE_FIELD: "games"}
        assert _get_next_phase_1a_field(collected) == "unternehmensgroesse"

    def test_next_field_after_sparte_skipped(self, monkeypatch):
        # Übersprungene Sparte ("" = weiter ohne Sparte) blockiert nicht
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        collected = {"branche": "medien", MEDIEN_SPARTE_FIELD: ""}
        assert _get_next_phase_1a_field(collected) == "unternehmensgroesse"

    def test_should_skip_sparte_for_non_medien_branche(self):
        assert _should_skip_qr_field(MEDIEN_SPARTE_FIELD, {"branche": "it"})
        assert _should_skip_qr_field(MEDIEN_SPARTE_FIELD, {})
        assert not _should_skip_qr_field(MEDIEN_SPARTE_FIELD, {"branche": "medien"})

    def test_existing_skip_rules_unchanged(self):
        assert _should_skip_qr_field("bundesland", {"country": "CH"})
        assert not _should_skip_qr_field("bundesland", {"country": "DE"})
        assert _should_skip_qr_field("selbststaendig", {"unternehmensgroesse": "2–10"})


# ===========================================================================
# 4) medien_sparte QR-Optionen (DE/EN)
# ===========================================================================

class TestMedienSparteQrOptions:
    def test_seven_options_with_formbuilder_values(self):
        options = _QR_OPTIONS[MEDIEN_SPARTE_FIELD]
        assert [o["value"] for o in options] == SPARTEN_7

    def test_de_labels_match_formbuilder(self):
        labels = {o["value"]: o["label"] for o in _QR_OPTIONS[MEDIEN_SPARTE_FIELD]}
        assert labels["produktion"] == "Film-/TV-Produktion"
        assert labels["post_vfx"] == "Postproduktion / VFX / Animation"
        assert labels["games"] == "Games / Interactive"
        assert labels["verlag_publishing"] == "Verlag / Publishing / Redaktion"
        assert labels["musik_audio"] == "Musik / Audio / Tonstudio / Podcast"
        assert labels["agentur_design"] == "Agentur / Werbung / PR / Webdesign"
        assert labels["content_creation"] == "Content Creation / Social Media"

    def test_en_labels_from_answers_normalizer(self):
        for o in _QR_OPTIONS[MEDIEN_SPARTE_FIELD]:
            assert o["label_en"] == MEDIEN_SPARTEN_LABELS_EN[o["value"]]

    def test_build_quick_replies_de(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        qrs = _build_quick_replies([MEDIEN_SPARTE_FIELD], "r1", {"branche": "medien"})
        assert len(qrs) == 1
        qr = qrs[0]
        assert qr.field == MEDIEN_SPARTE_FIELD
        assert qr.optional is True          # OPTIONAL_FIELDS im Formbuilder
        assert qr.multi_select is False
        assert [o.value for o in qr.options] == SPARTEN_7
        assert qr.options[4].label == "Musik / Audio / Tonstudio / Podcast"
        assert qr.label == "Sparte (Medien & Kreativwirtschaft)"

    def test_build_quick_replies_en(self, monkeypatch):
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        qrs = _build_quick_replies(
            [MEDIEN_SPARTE_FIELD], "r1", {"branche": "medien"}, lang="en",
        )
        labels = [o.label for o in qrs[0].options]
        assert labels == [MEDIEN_SPARTEN_LABELS_EN[v] for v in SPARTEN_7]
        assert qrs[0].label == "Sector (media & creative industries)"

    def test_welcome_qr_without_collected(self, monkeypatch):
        # Beim /start gibt es noch keine collected_fields — Chips müssen
        # trotzdem gebaut werden (Registry-Fallback _EXTRA_QR_FIELD_REGISTRY).
        monkeypatch.setenv("VISIBLE_BRANCHES", "medien")
        qrs = _build_quick_replies(_get_first_qr_fields("r1"), "r1")
        assert len(qrs) == 1 and len(qrs[0].options) == 7


# ===========================================================================
# 5) Freitext-Zuordnung / Skip-Semantik
# ===========================================================================

class TestNormalizeMedienSparte:
    @pytest.mark.parametrize("text,expected", [
        ("wir machen Tonstudio-Arbeit", "musik_audio"),
        ("Ich produziere Podcasts", "musik_audio"),
        ("Filmproduktion für Werbekunden", "produktion"),  # film vor werbung
        ("Wir sind ein TV-Sender", "produktion"),
        ("Postproduktion und Color Grading", "post_vfx"),
        ("Motion Design Studio", "post_vfx"),
        ("Indie-Games-Studio mit Unity", "games"),
        ("Wir sind ein Buchverlag", "verlag_publishing"),
        ("Redaktion einer Fachzeitschrift", "verlag_publishing"),
        ("Werbeagentur mit Fokus Branding", "agentur_design"),
        ("Webdesign und Grafik", "agentur_design"),
        ("Social-Media-Content für Marken", "content_creation"),
        ("Influencer-Marketing auf TikTok", "content_creation"),
    ])
    def test_keyword_mapping(self, text, expected):
        assert _normalize_medien_sparte(text) == expected

    def test_exact_slug_and_labels(self):
        assert _normalize_medien_sparte("games") == "games"
        assert _normalize_medien_sparte("Musik / Audio / Tonstudio / Podcast") == "musik_audio"
        assert _normalize_medien_sparte("Film/TV production") == "produktion"

    def test_unmappable_returns_none(self):
        assert _normalize_medien_sparte("wir bauen Häuser") is None
        assert _normalize_medien_sparte("") is None
        assert _normalize_medien_sparte(None) is None

    def test_sonstiges_is_skip_not_match(self):
        assert _normalize_medien_sparte("sonstiges") is None
        assert _is_medien_sparte_other("Sonstiges")
        assert _is_medien_sparte_other("keine Angabe")
        assert _is_medien_sparte_other("other")
        assert not _is_medien_sparte_other("Tonstudio")


# ===========================================================================
# 6) Default-Schutz: ohne ENV keinerlei medien_sparte im Flow
# ===========================================================================

class TestNoBehaviorChangeWithoutEnv:
    def test_module_constants_untouched(self):
        # Die Mehr-Branchen-Konstanten sind wortidentisch geblieben
        assert "In welcher Branche ist Ihr Unternehmen tätig?" in R1_WELCOME
        assert "What industry is your company in?" in R1_WELCOME_EN
        assert PHASE_1A_QR_FIELDS == [
            "branche", "unternehmensgroesse", "selbststaendig",
            "country", "bundesland", "investitionsbudget",
        ]

    def test_no_sparte_question_by_default(self):
        assert _get_next_phase_1a_field({"branche": "medien"}) == "unternehmensgroesse"

    def test_chat_registry_not_polluted(self):
        # medien_sparte darf NICHT in der chat_normalizer-Registry landen
        # (würde Sections/Progress aller Sessions ändern).
        from services.chat_normalizer import FIELD_REGISTRY
        assert MEDIEN_SPARTE_FIELD not in FIELD_REGISTRY
        assert chat._EXTRA_QR_FIELD_REGISTRY[MEDIEN_SPARTE_FIELD]["required"] is False
