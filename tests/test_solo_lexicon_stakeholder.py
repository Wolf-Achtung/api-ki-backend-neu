# -*- coding: utf-8 -*-
"""
FIX-KIS-1188-S4 (Sprint 1026.4): Solo-Lexicon Stakeholder coverage.

Pre-existing state had only `\\bStakeholdern\\b` and `\\bStakeholder\\b`
(both case-sensitive) in data/lexicon/solo_replacements.json. That left
gaps the in-file SOLO_TERM_REPLACEMENTS already covered:
- composite forms (Stakeholder-Analyse, -Management, -Mapping, …)
- English plural „Stakeholders"
- lowercase/ALLCAPS casing

Funnel KIS-1188 logs:
    [QUALITY-ENFORCER-RENDER] Failed: [FIX-52x][SOLO-LEAK] forbidden
    terms remain after rewrite: ['Stakeholder']

The lexicon now contains the full set; this test pins the coverage so
future edits can't silently regress.
"""
from __future__ import annotations

import pytest

from services.lexicon_loader import load_lexicon, apply_lexicon


@pytest.fixture(autouse=True)
def _fresh_lexicon_cache():
    """Each test runs against freshly compiled rules so a previous test
    that loaded a stale cached copy can't bleed in."""
    load_lexicon.cache_clear()
    yield
    load_lexicon.cache_clear()


class TestBasicStakeholderReplacement:

    def test_singular_replaced(self):
        out, n = apply_lexicon("Die Stakeholder müssen abstimmen.", "solo")
        assert n >= 1
        assert "Stakeholder" not in out
        assert "Beteiligte" in out

    def test_dativ_plural_replaced(self):
        out, n = apply_lexicon("Mit Stakeholdern sprechen.", "solo")
        assert n >= 1
        assert "Stakeholder" not in out
        assert "Beteiligten" in out

    def test_english_plural_replaced(self):
        """English-style plural „Stakeholders" was missing before S4."""
        out, n = apply_lexicon("List of all Stakeholders updated.", "solo")
        assert n >= 1
        assert "Stakeholders" not in out
        assert "Beteiligte" in out


class TestCasingVariants:
    """The leak-scanner runs case-insensitive (re.IGNORECASE), so the
    lexicon must too — otherwise lowercase/ALLCAPS leaks survive."""

    @pytest.mark.parametrize("text", [
        "Die stakeholder sind informiert.",
        "Die STAKEHOLDER sind informiert.",
        "Die StakeHolder sind informiert.",
    ])
    def test_casing_singular(self, text):
        out, n = apply_lexicon(text, "solo")
        assert n >= 1, f"no replacement for: {text!r}"
        assert "takeholder" not in out.lower()

    def test_casing_plural_dativ(self):
        out, n = apply_lexicon("mit stakeholdern abstimmen.", "solo")
        assert n >= 1
        assert "stakeholder" not in out.lower()

    def test_casing_english_plural_allcaps(self):
        out, n = apply_lexicon("Alle STAKEHOLDERS einbinden.", "solo")
        assert n >= 1
        assert "stakeholder" not in out.lower()


class TestCompositeForms:
    """`Stakeholder-XXX` compounds are common in enterprise prose and
    need explicit mappings BEFORE the bare-noun pattern (otherwise the
    bare-noun pattern eats the head and leaves the tail dangling)."""

    @pytest.mark.parametrize("composite,expected_fragment", [
        ("Stakeholder-Analyse", "Beteiligten-Analyse"),
        ("Stakeholder-Alignment", "Abstimmung der Beteiligten"),
        ("Stakeholder-Feedback", "Rückmeldung der Beteiligten"),
        ("Stakeholder-Management", "Beteiligten-Management"),
        ("Stakeholder-Kommunikation", "Kommunikation mit Beteiligten"),
        ("Stakeholder-Mapping", "Beteiligten-Übersicht"),
        ("Stakeholder-Engagement", "Einbindung der Beteiligten"),
    ])
    def test_known_compounds(self, composite, expected_fragment):
        out, n = apply_lexicon(f"Wir starten mit {composite}.", "solo")
        assert n >= 1
        assert "Stakeholder" not in out
        assert expected_fragment in out

    def test_unknown_compound_fallback(self):
        """A compound the table doesn't enumerate falls through the
        catch-all and still loses the „Stakeholder-" prefix."""
        out, n = apply_lexicon("Die Stakeholder-Liste sollte aktuell sein.", "solo")
        assert n >= 1
        assert "Stakeholder" not in out

    def test_compound_pattern_consumes_full_token(self):
        """The compound pattern must consume „Stakeholder-Liste" as one
        unit — the leftover bare „Stakeholder" must not remain."""
        out, _ = apply_lexicon("Stakeholder-Mapping zeigt die Verantwortlichen.", "solo")
        # No bare „Stakeholder" or „-Mapping" residue
        assert "Stakeholder" not in out
        assert "-Mapping" not in out


class TestNoBackwardsRegression:
    """The wider solo lexicon must still apply other rules unchanged."""

    def test_governance_still_replaced(self):
        out, n = apply_lexicon("Die Governance ist klar.", "solo")
        assert n >= 1
        assert "Governance" not in out

    def test_rule_count_grew_by_expected_amount(self):
        """Sprint 1026.4 added 9 Stakeholder rows (replaced 2 with 11).
        Net change: +9. Pin so future edits don't accidentally collapse."""
        lex = load_lexicon("solo")
        stakeholder_rules = [
            r for r in lex.rules
            if "Stakeholder" in r.pattern or "stakeholder" in r.pattern.lower()
        ]
        assert len(stakeholder_rules) == 11, (
            f"expected 11 Stakeholder rules, found {len(stakeholder_rules)}"
        )

    def test_solo_lexicon_total_rule_count(self):
        """Sanity: solo lexicon has 80 rules (76 nach Sprint 1026.4 + 4
        KIS-1230-Kompositum-Regeln: Governance-Rahmen/-Runde/-Struktur/-Regeln,
        damit die generische Governance→Steuerung-Regel keine Komposita mehr
        zu 'Steuerung-Rahmen' zerbricht)."""
        lex = load_lexicon("solo")
        assert lex.rule_count == 80


class TestTeamPersonaUnchanged:
    """The Stakeholder extension is solo-only; team-persona keeps its
    single Stakeholder-Management→Team-Koordination mapping."""

    def test_team_lexicon_unchanged(self):
        lex = load_lexicon("team")
        stakeholder_rules = [
            r for r in lex.rules
            if "Stakeholder" in r.pattern
        ]
        assert len(stakeholder_rules) == 1
        assert "Team-Koordination" in stakeholder_rules[0].replacement

    def test_team_apply_does_not_touch_bare_stakeholder(self):
        """Team-persona does NOT rewrite the bare noun (Team contexts
        legitimately have multiple stakeholders)."""
        out, n = apply_lexicon("Die Stakeholder treffen sich.", "team")
        # bare „Stakeholder" survives in team persona (intentional)
        assert "Stakeholder" in out
        assert n == 0
