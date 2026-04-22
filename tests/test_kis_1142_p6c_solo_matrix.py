# -*- coding: utf-8 -*-
"""
KIS-1142 P6-C Solo-Populate + P3 Solo-Exempt.

Wolf populates ``_CHALLENGE_WEEKS_SKIP_BY_SIZE["solo"] = {"woche_3",
"woche_4"}`` (Enterprise-LLM-Ops-Wochen raus für Einzelberater).
Kombiniert mit dem bestehenden P3-Drop ("Woche 1 weg für
Intermediate/Expert") würde Solo+Intermediate/Expert aber auf eine
einzige Governance-Woche degenerieren.

Wolf-Entscheidung: P3 bleibt für Solo inaktiv, damit Solo immer mit
mindestens ``{w1, w2, abschluss}`` aus der Challenge kommt. P3 greift
weiter für Team/KMU+Intermediate/Expert.

Regression-Cover: die vollständige 3×3-Konsistenz-Matrix (company_size
× expertise_level) wird hier gegen die erwartete Wochen-Konfiguration
geprüft. Jede Zelle ist ein Test, damit eine spätere Änderung an P3
oder P6-C sofort sichtbar macht, welche Segmente sie betrifft.
"""

from __future__ import annotations

import re

import pytest

from services.sofort_start_generator import (
    CHALLENGE_30_TAGE,
    CHALLENGE_30_TAGE_EXPERT,
    CHALLENGE_30_TAGE_INTERMEDIATE,
    _CHALLENGE_WEEKS_SKIP_BY_SIZE,
    generate_30_tage_challenge_html_v2,
)


# ---------------------------------------------------------------------------
# H1 — The dict is populated for Solo as Wolf specified
# ---------------------------------------------------------------------------

class TestSoloSkipSetPopulated:
    def test_solo_drops_weeks_3_and_4(self):
        assert _CHALLENGE_WEEKS_SKIP_BY_SIZE["solo"] == {"woche_3", "woche_4"}

    def test_team_and_kmu_still_empty(self):
        # Wolf: "Team/KMU nach Prüfung in separatem PR". Must stay empty
        # here so this PR doesn't silently introduce team/kmu-defaults.
        assert _CHALLENGE_WEEKS_SKIP_BY_SIZE["team"] == set()
        assert _CHALLENGE_WEEKS_SKIP_BY_SIZE["kmu"] == set()


# ---------------------------------------------------------------------------
# H2 — Full consistency matrix: company_size × expertise_level
# ---------------------------------------------------------------------------

def _render_and_extract_week_titles(
    company_size: str, expertise_level: str,
) -> list[str]:
    """Render the challenge and return the ordered week titles as they
    appear in the HTML (including "Abschluss" if present)."""
    html = generate_30_tage_challenge_html_v2(
        company_size=company_size,
        zeitbudget="2_5",
        expertise_level=expertise_level,
    )
    # The renderer emits each week as `<h3 …>{Label}: {titel}</h3>`.
    # Capture the titles in order.
    titles = re.findall(
        r'<h3[^>]*>\s*(?:Woche \d+|Abschluss)\s*:\s*([^<]+?)</h3>',
        html,
    )
    return [t.strip() for t in titles]


# Expected titles per variant, for the weeks that should survive each
# (company_size, expertise_level) combination.  Beginner = CHALLENGE_30_TAGE,
# intermediate = CHALLENGE_30_TAGE_INTERMEDIATE, expert = CHALLENGE_30_TAGE_EXPERT.
_BEGINNER_W1_TITLE = CHALLENGE_30_TAGE["woche_1"]["titel"]
_BEGINNER_W2_TITLE = CHALLENGE_30_TAGE["woche_2"]["titel"]
_BEGINNER_W3_TITLE = CHALLENGE_30_TAGE["woche_3"]["titel"]
_BEGINNER_W4_TITLE = CHALLENGE_30_TAGE["woche_4"]["titel"]
_BEGINNER_ABSCHLUSS_TITLE = CHALLENGE_30_TAGE["abschluss"]["titel"]

_EXPERT_W1_TITLE = CHALLENGE_30_TAGE_EXPERT["woche_1"]["titel"]
_EXPERT_W2_TITLE = CHALLENGE_30_TAGE_EXPERT["woche_2"]["titel"]
_EXPERT_W3_TITLE = CHALLENGE_30_TAGE_EXPERT["woche_3"]["titel"]
_EXPERT_W4_TITLE = CHALLENGE_30_TAGE_EXPERT["woche_4"]["titel"]
_EXPERT_ABSCHLUSS_TITLE = CHALLENGE_30_TAGE_EXPERT["abschluss"]["titel"]

_INTER_W1_TITLE = CHALLENGE_30_TAGE_INTERMEDIATE["woche_1"]["titel"]
_INTER_W2_TITLE = CHALLENGE_30_TAGE_INTERMEDIATE["woche_2"]["titel"]
_INTER_W3_TITLE = CHALLENGE_30_TAGE_INTERMEDIATE["woche_3"]["titel"]
_INTER_W4_TITLE = CHALLENGE_30_TAGE_INTERMEDIATE["woche_4"]["titel"]
_INTER_ABSCHLUSS_TITLE = CHALLENGE_30_TAGE_INTERMEDIATE["abschluss"]["titel"]


class TestConsistencyMatrix:
    # --- SOLO --- (weeks 3 + 4 always dropped, week 1 always kept) ------

    def test_solo_beginner_keeps_w1_w2_abschluss(self):
        titles = _render_and_extract_week_titles("solo", "beginner")
        assert titles == [
            _BEGINNER_W1_TITLE,
            _BEGINNER_W2_TITLE,
            _BEGINNER_ABSCHLUSS_TITLE,
        ]

    def test_solo_intermediate_keeps_w1_w2_abschluss(self):
        # Key degeneration guard: P3 must NOT drop w1 for Solo.
        titles = _render_and_extract_week_titles("solo", "intermediate")
        assert titles == [
            _INTER_W1_TITLE,
            _INTER_W2_TITLE,
            _INTER_ABSCHLUSS_TITLE,
        ]

    def test_solo_expert_keeps_w1_w2_abschluss(self):
        # Same degeneration guard for expert — Solo-Expert is a central
        # product profile (TÜV KI-Manager freelancer etc.).
        titles = _render_and_extract_week_titles("solo", "expert")
        assert titles == [
            _EXPERT_W1_TITLE,
            _EXPERT_W2_TITLE,
            _EXPERT_ABSCHLUSS_TITLE,
        ]

    @pytest.mark.parametrize("expertise", ["beginner", "intermediate", "expert"])
    def test_solo_never_degenerates_below_two_weeks(self, expertise):
        titles = _render_and_extract_week_titles("solo", expertise)
        # "Abschluss" counts separately — we want at least two actual
        # Wochen-Blöcke, so the Challenge reads as a challenge.
        week_blocks = [t for t in titles
                       if t not in (_BEGINNER_ABSCHLUSS_TITLE,
                                    _EXPERT_ABSCHLUSS_TITLE,
                                    _INTER_ABSCHLUSS_TITLE)]
        assert len(week_blocks) >= 2, (
            f"Solo+{expertise} degenerated to {len(week_blocks)} "
            f"week-block(s): {titles!r}. Expected ≥ 2."
        )

    # --- TEAM --- (P6-C no-op, P3 drops w1 for Int/Expert) --------------

    def test_team_beginner_keeps_all_four_weeks(self):
        titles = _render_and_extract_week_titles("team", "beginner")
        assert titles == [
            _BEGINNER_W1_TITLE,
            _BEGINNER_W2_TITLE,
            _BEGINNER_W3_TITLE,
            _BEGINNER_W4_TITLE,
            _BEGINNER_ABSCHLUSS_TITLE,
        ]

    def test_team_intermediate_drops_w1_keeps_w2_w3_w4(self):
        titles = _render_and_extract_week_titles("team", "intermediate")
        assert titles == [
            _INTER_W2_TITLE,
            _INTER_W3_TITLE,
            _INTER_W4_TITLE,
            _INTER_ABSCHLUSS_TITLE,
        ]

    def test_team_expert_drops_w1_keeps_w2_w3_w4(self):
        titles = _render_and_extract_week_titles("team", "expert")
        assert titles == [
            _EXPERT_W2_TITLE,
            _EXPERT_W3_TITLE,
            _EXPERT_W4_TITLE,
            _EXPERT_ABSCHLUSS_TITLE,
        ]

    # --- KMU --- (same as Team: P6-C no-op, P3 drops w1 for Int/Expert) -

    def test_kmu_beginner_keeps_all_four_weeks(self):
        titles = _render_and_extract_week_titles("kmu", "beginner")
        assert titles == [
            _BEGINNER_W1_TITLE,
            _BEGINNER_W2_TITLE,
            _BEGINNER_W3_TITLE,
            _BEGINNER_W4_TITLE,
            _BEGINNER_ABSCHLUSS_TITLE,
        ]

    def test_kmu_expert_drops_w1_keeps_w2_w3_w4(self):
        titles = _render_and_extract_week_titles("kmu", "expert")
        assert titles == [
            _EXPERT_W2_TITLE,
            _EXPERT_W3_TITLE,
            _EXPERT_W4_TITLE,
            _EXPERT_ABSCHLUSS_TITLE,
        ]


# ---------------------------------------------------------------------------
# H3 — Solo-exempt guard in source (regression-proof the condition)
# ---------------------------------------------------------------------------

class TestSoloExemptGuard:
    def test_p3_branch_checks_company_size(self):
        import inspect

        from services import sofort_start_generator

        src = inspect.getsource(
            sofort_start_generator.generate_30_tage_challenge_html_v2,
        )
        normalized = " ".join(src.split())
        # The P3 drop must be gated on company_size != "solo". If a future
        # edit reverts the guard or renames the variable, this assertion
        # fails immediately.
        assert '_company_size_norm != "solo"' in normalized, (
            "P3 drop must stay gated on company_size != 'solo' so Solo "
            "users keep week 1 (avoids the 1-week-degenerate case)."
        )

    @pytest.mark.parametrize("variant", ["Solo", "SOLO", " solo ", "solo"])
    def test_company_size_normalisation_survives_whitespace_and_case(self, variant):
        # The normalised comparison must handle upstream inputs that
        # preserve original casing/spacing (legacy briefings).
        titles = _render_and_extract_week_titles(variant, "expert")
        # Still the Solo shape (w1 + w2 + abschluss), not the degenerate
        # 1-week shape.
        week_blocks = [t for t in titles
                       if t not in (_EXPERT_ABSCHLUSS_TITLE,)]
        assert len(week_blocks) == 2, (
            f"company_size={variant!r} should normalise to 'solo' and "
            f"keep w1+w2, got {titles!r}"
        )
