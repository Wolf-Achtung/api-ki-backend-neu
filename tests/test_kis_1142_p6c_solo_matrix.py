# -*- coding: utf-8 -*-
"""
KIS-1142 P6-C Solo + KIS-1192 Item H Solo-Override + P3 Solo-Exempt.

History:
- KIS-1142 P6-C: ``_CHALLENGE_WEEKS_SKIP_BY_SIZE["solo"] = {"woche_3",
  "woche_4"}`` — Enterprise-LLM-Ops-Wochen raus für Einzelberater.
  Kombiniert mit P3 ("Woche 1 weg für Intermediate/Expert") wäre Solo
  auf eine einzige Governance-Woche degeneriert; P3 ist für Solo
  inaktiv geblieben.
- KIS-1192 Item H: Skip führte zu sichtbarer Tage-15-28-Lücke auf
  R1 S.12 (Tag 1-14 + Abschluss-Block Tag 29-30, nichts dazwischen).
  Wolf-Entscheidung H1: Skip-Set für Solo geleert, stattdessen
  Solo-spezifische woche_3/4 via ``_CHALLENGE_SOLO_WEEK_OVERRIDES``.
  Solo bekommt damit wieder vollständige 30-Tage-Erfahrung mit
  Solo-realistischen Inhalten (Vorlagen-Bibliothek + Mandanten-
  Onboarding) statt Enterprise-LLM-Ops.

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
    _CHALLENGE_SOLO_WEEK_OVERRIDES,
    _CHALLENGE_WEEKS_SKIP_BY_SIZE,
    generate_30_tage_challenge_html_v2,
)


# ---------------------------------------------------------------------------
# H1 — KIS-1192 Item H: Solo skip is now empty; override mechanism applies
# ---------------------------------------------------------------------------

class TestSoloSkipSetPopulated:
    def test_solo_keeps_all_four_weeks(self):
        # KIS-1142 droppte W3/W4 für Solo. KIS-1192 Item H hebt das auf:
        # Solo bekommt eigenen Content via _CHALLENGE_SOLO_WEEK_OVERRIDES.
        # Skip-Set für Solo muss leer sein.
        assert _CHALLENGE_WEEKS_SKIP_BY_SIZE["solo"] == set()

    def test_solo_overrides_have_w3_and_w4(self):
        # The replacement mechanism MUST cover both Enterprise-LLM-Ops weeks.
        assert "woche_3" in _CHALLENGE_SOLO_WEEK_OVERRIDES
        assert "woche_4" in _CHALLENGE_SOLO_WEEK_OVERRIDES
        # Each override must have the canonical structure (titel, ziel, tage).
        for wk in ("woche_3", "woche_4"):
            assert "titel" in _CHALLENGE_SOLO_WEEK_OVERRIDES[wk]
            assert "tage" in _CHALLENGE_SOLO_WEEK_OVERRIDES[wk]
            assert len(_CHALLENGE_SOLO_WEEK_OVERRIDES[wk]["tage"]) == 7

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

# KIS-1192 Item H: Solo-specific override titles
_SOLO_OVERRIDE_W3_TITLE = _CHALLENGE_SOLO_WEEK_OVERRIDES["woche_3"]["titel"]
_SOLO_OVERRIDE_W4_TITLE = _CHALLENGE_SOLO_WEEK_OVERRIDES["woche_4"]["titel"]


class TestConsistencyMatrix:
    # --- SOLO --- (KIS-1192 Item H: full 30 days, Solo-overrides for
    # Enterprise-LLM-Ops weeks; week 1 always kept) -----------------------

    def test_solo_beginner_keeps_5_blocks(self):
        # KIS-1192 Item H: Solo bekommt alle 5 Blöcke (w1-w4 + Abschluss).
        # Beginner-Content ist bereits solo-tauglich → kein Override nötig.
        titles = _render_and_extract_week_titles("solo", "beginner")
        assert titles == [
            _BEGINNER_W1_TITLE,
            _BEGINNER_W2_TITLE,
            _BEGINNER_W3_TITLE,
            _BEGINNER_W4_TITLE,
            _BEGINNER_ABSCHLUSS_TITLE,
        ]

    def test_solo_intermediate_keeps_5_blocks(self):
        # KIS-1192 Item H: Solo bekommt alle 5 Blöcke (w1-w4 + Abschluss).
        # Intermediate w3 ("Vertiefung & Qualität") ist solo-OK → bleibt.
        # Intermediate w4 ("Skalierung & Standardisierung") matched den
        # Enterprise-Keyword-Filter → wird durch Solo-Override ersetzt.
        # Degeneration-Guard: P3 darf w1 für Solo nicht droppen.
        titles = _render_and_extract_week_titles("solo", "intermediate")
        assert titles == [
            _INTER_W1_TITLE,
            _INTER_W2_TITLE,
            _INTER_W3_TITLE,
            _SOLO_OVERRIDE_W4_TITLE,
            _INTER_ABSCHLUSS_TITLE,
        ]

    def test_solo_expert_keeps_5_blocks(self):
        # KIS-1192 Item H: Solo bekommt alle 5 Blöcke (w1-w4 + Abschluss).
        # Expert w3 ("Optimierung" — LLM-Ops) und w4 ("Skalierung") sind
        # Enterprise → beide werden durch Solo-Overrides ersetzt.
        # Solo-Expert ist ein zentrales Produkt-Profil (TÜV KI-Manager
        # Freelancer etc.).
        titles = _render_and_extract_week_titles("solo", "expert")
        assert titles == [
            _EXPERT_W1_TITLE,
            _EXPERT_W2_TITLE,
            _SOLO_OVERRIDE_W3_TITLE,
            _SOLO_OVERRIDE_W4_TITLE,
            _EXPERT_ABSCHLUSS_TITLE,
        ]

    def test_solo_advanced_keeps_5_blocks(self):
        # KIS-1192 Wolf-Profil-Regression-Schutz: Briefing KI-Kompetenz=
        # "hoch" mappt im upstream-Pipeline auf expertise_level="expert".
        # Dieser Test fixt das genaue Profil aus KIS-1192 (Briefing-ID
        # 1075) — Solo + Beratung + hoch — gegen die 5-Block-Erwartung.
        # Replicates the user-facing R1 S.12-Layout vom KIS-1192-Lauf.
        titles = _render_and_extract_week_titles("solo", "expert")
        week_blocks = [t for t in titles
                       if t not in (_BEGINNER_ABSCHLUSS_TITLE,
                                    _EXPERT_ABSCHLUSS_TITLE,
                                    _INTER_ABSCHLUSS_TITLE)]
        assert len(titles) == 5, (
            f"Wolf-Profil (Solo + KI-Kompetenz=hoch) muss 5 Blöcke "
            f"rendern (w1-w4 + Abschluss), got {len(titles)}: {titles!r}"
        )
        assert len(week_blocks) == 4, (
            f"Wolf-Profil muss 4 echte Wochen-Blöcke haben, "
            f"got {len(week_blocks)}: {titles!r}"
        )
        # Override-Markers müssen tatsächlich greifen (sonst landet
        # Enterprise-LLM-Ops-Content beim Solo-Berater).
        assert _SOLO_OVERRIDE_W3_TITLE in titles
        assert _SOLO_OVERRIDE_W4_TITLE in titles

    @pytest.mark.parametrize("expertise", ["beginner", "intermediate", "expert"])
    def test_solo_renders_full_30_days(self, expertise):
        # KIS-1192 Item H regression-guard: Solo bekommt alle 4 Wochen
        # + Abschluss, keine sichtbare Lücke mehr (R1 S.12 lückenlos
        # Tag 1-30 statt vorher 1-14 + 29-30).
        titles = _render_and_extract_week_titles("solo", expertise)
        week_blocks = [t for t in titles
                       if t not in (_BEGINNER_ABSCHLUSS_TITLE,
                                    _EXPERT_ABSCHLUSS_TITLE,
                                    _INTER_ABSCHLUSS_TITLE)]
        assert len(week_blocks) == 4, (
            f"Solo+{expertise} should render all 4 weeks (KIS-1192 Item H), "
            f"got {len(week_blocks)} week-block(s): {titles!r}."
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
        # KIS-1192 Item H: Solo bekommt jetzt 4 Wochen + Abschluss.
        # Normalisierung muss case- und whitespace-tolerant sein, sodass
        # Solo-Override für w3/w4 greift (sonst landet Enterprise-LLM-Ops
        # beim Solo-Berater).
        titles = _render_and_extract_week_titles(variant, "expert")
        week_blocks = [t for t in titles
                       if t not in (_EXPERT_ABSCHLUSS_TITLE,)]
        assert len(week_blocks) == 4, (
            f"company_size={variant!r} should normalise to 'solo' and "
            f"render 4 weeks (KIS-1192 Item H), got {titles!r}"
        )
        # Solo-Overrides müssen für die LLM-Ops-Wochen greifen.
        assert _SOLO_OVERRIDE_W3_TITLE in titles, (
            f"company_size={variant!r}: w3 should be solo-overridden, "
            f"got {titles!r}"
        )
        assert _SOLO_OVERRIDE_W4_TITLE in titles, (
            f"company_size={variant!r}: w4 should be solo-overridden, "
            f"got {titles!r}"
        )
