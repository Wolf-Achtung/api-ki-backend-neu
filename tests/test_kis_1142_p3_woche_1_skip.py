# -*- coding: utf-8 -*-
"""
KIS-1142 Punkt 3 — "Woche 1 überspringbar"-Widerspruch auflösen.

Der Report empfahl bisher *"Die 30-Tage-Challenge Woche 1 können Sie
überspringen"* (triggered by ``score_int >= 50`` in
``pdf_template_v7.html``), renderte die Challenge aber **weiter mit
vollständiger Woche 1**.  Kunden mit hohem Score sahen im selben
Dokument einen Hinweis ("skippable") und dazu die sieben Tage
Woche-1-Content, die laut Hinweis nicht für sie bestimmt sein sollen.

Fix (Variante B aus Briefing 9):
  * Die erste ``woche_*`` wird für ``expertise_level in
    {"intermediate", "expert"}`` im Generator tatsächlich aus
    ``challenge_data`` entfernt.
  * Restliche Wochen bekommen ``tage.tag`` neu ab 1 nummeriert.
  * Das Template-Banner triggert jetzt auf ``expertise_level`` (nicht
    auf ``score_int``) und beschreibt, dass die Woche *entfällt*
    — nicht mehr, dass sie *überspringbar* wäre.
"""

from __future__ import annotations

import pytest

from services.sofort_start_generator import (
    CHALLENGE_30_TAGE,
    CHALLENGE_30_TAGE_EXPERT,
    CHALLENGE_30_TAGE_INTERMEDIATE,
    _drop_first_week_and_renumber,
    generate_30_tage_challenge_html_v2,
)


# ---------------------------------------------------------------------------
# H1 — Helper: drop + renumber
# ---------------------------------------------------------------------------

class TestDropFirstWeekAndRenumber:
    def test_first_week_is_removed(self):
        result = _drop_first_week_and_renumber(CHALLENGE_30_TAGE)
        original_keys = list(CHALLENGE_30_TAGE.keys())
        result_keys = list(result.keys())
        assert original_keys[0] not in result_keys, (
            f"First week {original_keys[0]!r} must be dropped"
        )
        # Remaining keys stay in order.
        assert result_keys == original_keys[1:]

    def test_days_are_renumbered_from_one(self):
        result = _drop_first_week_and_renumber(CHALLENGE_30_TAGE)
        # First day of the first remaining week must be tag 1, not tag 8.
        first_week_key = next(iter(result))
        first_tag = result[first_week_key]["tage"][0]["tag"]
        assert first_tag == 1, (
            f"Expected first tag == 1 after renumber, got {first_tag!r}"
        )

    def test_days_stay_sequential_across_weeks(self):
        result = _drop_first_week_and_renumber(CHALLENGE_30_TAGE_EXPERT)
        seen = []
        for week in result.values():
            for tag in week["tage"]:
                seen.append(tag["tag"])
        assert seen == list(range(1, len(seen) + 1)), (
            f"Day numbers not sequential: {seen!r}"
        )

    def test_source_dict_not_mutated(self):
        # Guard against someone swapping dict() → .pop() and breaking the
        # shared module-level challenge dicts for every subsequent caller.
        snapshot = {
            k: {"tage": list(v["tage"])} for k, v in CHALLENGE_30_TAGE.items()
        }
        _ = _drop_first_week_and_renumber(CHALLENGE_30_TAGE)
        for week_key, week_data in CHALLENGE_30_TAGE.items():
            assert [t["tag"] for t in week_data["tage"]] == [
                t["tag"] for t in snapshot[week_key]["tage"]
            ]

    def test_empty_dict_returns_unchanged(self):
        assert _drop_first_week_and_renumber({}) == {}

    def test_abschluss_only_dict_returns_unchanged(self):
        # Pathological input: only "abschluss" key, no "woche_*".
        only_abschluss = {"abschluss": {"titel": "X", "tage": [{"tag": 1}]}}
        result = _drop_first_week_and_renumber(only_abschluss)
        assert result == only_abschluss

    def test_last_abschluss_kept(self):
        # The abschluss section must survive the drop.
        result = _drop_first_week_and_renumber(CHALLENGE_30_TAGE)
        assert "abschluss" in result


# ---------------------------------------------------------------------------
# H2 — Renderer: expertise_level gates the drop
# ---------------------------------------------------------------------------

class TestRendererDropsWocheOneForIntExpert:
    @pytest.mark.parametrize("level", ["intermediate", "expert"])
    def test_html_omits_woche_1_title(self, level):
        html = generate_30_tage_challenge_html_v2(
            company_size="team",
            zeitbudget="2_5",
            expertise_level=level,
        )
        # The expert/intermediate variants' woche_1 titles live in their
        # respective dicts; none must surface in the rendered HTML.
        for variant in (CHALLENGE_30_TAGE_EXPERT, CHALLENGE_30_TAGE_INTERMEDIATE):
            woche_1_title = variant["woche_1"]["titel"]
            if level == "expert" and variant is CHALLENGE_30_TAGE_EXPERT:
                assert woche_1_title not in html, (
                    f"Expert Woche 1 title {woche_1_title!r} leaked into "
                    "HTML after drop"
                )
            if level == "intermediate" and variant is CHALLENGE_30_TAGE_INTERMEDIATE:
                assert woche_1_title not in html

    def test_html_keeps_woche_1_for_beginner(self):
        html = generate_30_tage_challenge_html_v2(
            company_size="team",
            zeitbudget="2_5",
            expertise_level="beginner",
        )
        # Beginner must still see the original Woche 1 "Erste Schritte".
        assert CHALLENGE_30_TAGE["woche_1"]["titel"] in html

    def test_subtitle_announces_three_weeks_for_advanced(self):
        expert_html = generate_30_tage_challenge_html_v2(
            expertise_level="expert", zeitbudget="2_5",
        )
        inter_html = generate_30_tage_challenge_html_v2(
            expertise_level="intermediate", zeitbudget="2_5",
        )
        # The advanced subtitles previously claimed "in 4 Wochen" — now 3.
        assert "in 3 Wochen" in expert_html
        assert "in 3 Wochen" in inter_html
        assert "in 4 Wochen" not in expert_html
        assert "in 4 Wochen" not in inter_html

    def test_day_1_appears_only_once_in_advanced(self):
        # After renumber, the first visible day is Tag 1. Before the fix,
        # expert saw Tag 1 in (dropped) Woche 1 and again nowhere — but
        # after the drop + renumber, Tag 1 must be present exactly once
        # per HTML (no stale "Tag 8" rendering).
        html = generate_30_tage_challenge_html_v2(
            expertise_level="expert", zeitbudget="2_5",
        )
        # Count discrete "Tag 1<" occurrences (< terminates the number so
        # we don't count "Tag 10", "Tag 15" etc).
        count = html.count(">Tag 1<")
        assert count == 1, (
            f"Expected exactly one 'Tag 1' marker, got {count!r}"
        )


# ---------------------------------------------------------------------------
# H3 — Template skip-hint uses expertise_level, not score
# ---------------------------------------------------------------------------

class TestTemplateSkipHintUsesExpertiseLevel:
    """Source-level guard on templates/pdf_template_v7.html — rendering it
    standalone would need the full Jinja environment + all R1 template
    variables. An inspect-level check is cheaper and catches the three
    relevant regressions: score-based triggers returning, "überspringen"
    wording returning, or the expertise branches being dropped."""

    @pytest.fixture
    def template_src(self):
        with open("templates/pdf_template_v7.html", "r", encoding="utf-8") as f:
            return f.read()

    def test_score_based_skip_trigger_removed(self, template_src):
        # The old score-based conditions must be gone from the mgmt-summary
        # block. Allow the SKIP_HINT branch (custom hint injected by the
        # pipeline) and the "score_int >= 80" block to survive elsewhere
        # — we only guard the 30-day-challenge-specific phrasing.
        assert (
            "Die 30-Tage-Challenge Woche 1 können Sie überspringen"
            not in template_src
        ), (
            "Old score-based 'Woche 1 überspringen' wording still present; "
            "replace with an expertise_level-keyed banner that reflects "
            "the drop in the renderer."
        )

    def test_expertise_level_branches_present(self, template_src):
        assert 'expertise_level == "expert"' in template_src
        assert 'expertise_level == "intermediate"' in template_src

    def test_new_wording_matches_renderer_reality(self, template_src):
        # The new banner text describes the Woche as *entfällt* / starts
        # directly with a later topic — matching what the generator now
        # actually renders. Pin the exact substrings so a silent revert
        # to "überspringen" wording trips this test.
        assert "die Einstiegs-Woche entfällt" in template_src
        assert "überspringt die Grundlagen-Woche" in template_src
