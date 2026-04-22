# -*- coding: utf-8 -*-
"""
KIS-1142 Punkt 6 — Enterprise-Content-Bias mitigations (Varianten B + C).

Wolf pre-decided B+C (vs Variante A, a full content-matrix rewrite).

**Variante B — Tool-Budget-Filter**
Pre-filter the tool-recommender's seed list by the user's
`investitionsbudget` band so enterprise-priced tools (e.g.
"ab 500 €/Monat") never reach the scorer when a solo freelancer has
stated "unter_2000" as their budget cap. Tools with unparseable prices
("Usage-basiert") are always kept — we'd rather show an unknown-cost
tool than silently drop a potentially critical recommendation.

**Variante C — Challenge-Wochen-Opt-in**
Add an infrastructure hook so specific weeks of the 30-day challenge
can be dropped based on `company_size`. Populates empty by default;
once Wolf calls out which week-arcs feel too enterprise-heavy for solo
(governance-heavy content, team-scaling exercises), those keys drop
into `_CHALLENGE_WEEKS_SKIP_BY_SIZE`.

Both variants ship as **additive, non-breaking changes** — the default
(empty skip-set / unknown budget band) reproduces today's behavior.
"""

from __future__ import annotations

import inspect

import pytest

from services.sofort_start_generator import (
    CHALLENGE_30_TAGE,
    CHALLENGE_30_TAGE_EXPERT,
    _CHALLENGE_WEEKS_SKIP_BY_SIZE,
    _filter_challenge_weeks_by_size,
)
from services.tools_recommender import (
    _BUDGET_BAND_MAX_MONTHLY,
    _fits_budget,
    _parse_price_min_monthly,
    recommend_tools,
)


# ---------------------------------------------------------------------------
# Variante B — price parsing
# ---------------------------------------------------------------------------

class TestParsePriceMinMonthly:
    @pytest.mark.parametrize("price, expected", [
        ("0–29 €/Monat",         0),
        ("0-29 €/Monat",         0),
        ("0–10 €/Monat",         0),
        ("Free / ab 18 €/Monat", 0),
        ("Kostenlos",            0),
        ("ab 9 €/Monat",         9),
        ("ab ~5 € (Nutzung)",    5),
    ])
    def test_parses_known_seed_formats(self, price, expected):
        assert _parse_price_min_monthly(price) == expected

    @pytest.mark.parametrize("price", [
        "Usage-basiert", "Usage", "Usage/Pro", "",
    ])
    def test_unparseable_returns_none(self, price):
        assert _parse_price_min_monthly(price) is None

    def test_none_input_is_none(self):
        assert _parse_price_min_monthly(None) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Variante B — budget gate
# ---------------------------------------------------------------------------

class TestFitsBudget:
    def test_unter_2000_drops_expensive_tool(self):
        tool = {"name": "Expensive SaaS", "price": "ab 100 €/Monat"}
        assert _fits_budget(tool, "unter_2000") is False

    def test_unter_2000_keeps_cheap_tool(self):
        tool = {"name": "Tally.so", "price": "0–29 €/Monat"}
        assert _fits_budget(tool, "unter_2000") is True

    def test_2000_10000_keeps_mid_tier(self):
        tool = {"name": "HubSpot", "price": "Free / ab 18 €/Monat"}
        assert _fits_budget(tool, "2000_10000") is True

    def test_ueber_50000_bypass_filter(self):
        # Enterprise buyers should not be filtered — cap is None.
        tool = {"name": "Expensive", "price": "ab 9999 €/Monat"}
        assert _fits_budget(tool, "ueber_50000") is True

    def test_unklar_bypass_filter(self):
        # Missing data → never penalise.
        tool = {"name": "Expensive", "price": "ab 9999 €/Monat"}
        assert _fits_budget(tool, "unklar") is True

    def test_unknown_budget_band_bypasses(self):
        tool = {"name": "Expensive", "price": "ab 9999 €/Monat"}
        assert _fits_budget(tool, "some_new_band") is True

    def test_usage_based_tool_always_kept(self):
        # "Usage-basiert" → unparseable → keep as conservative default.
        tool = {"name": "OpenAI API", "price": "Usage-basiert"}
        for band in _BUDGET_BAND_MAX_MONTHLY:
            assert _fits_budget(tool, band) is True, (
                f"Usage-based tool was dropped under budget band {band!r}"
            )


# ---------------------------------------------------------------------------
# Variante B — end-to-end recommender
# ---------------------------------------------------------------------------

class TestRecommendToolsBudgetFilter:
    def test_no_budget_returns_baseline_count(self):
        # Empty briefing → filter skipped, we still get some recommendations.
        result = recommend_tools({})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_unter_2000_drops_fewer_or_equal_than_baseline(self):
        # The filter can only drop, never add.
        baseline = recommend_tools({})
        filtered = recommend_tools({
            "investitionsbudget": "unter_2000",
            "unternehmensgroesse": "solo",
        })
        assert len(filtered) <= len(baseline)
        # Every remaining tool must pass the budget gate.
        for tool in filtered:
            assert _fits_budget(tool, "unter_2000")

    def test_ueber_50000_matches_baseline_length(self):
        baseline = recommend_tools({})
        unfiltered = recommend_tools({
            "investitionsbudget": "ueber_50000",
        })
        # ueber_50000 bypasses the filter, so length should match.
        assert len(unfiltered) == len(baseline)


# ---------------------------------------------------------------------------
# Variante C — challenge filter
# ---------------------------------------------------------------------------

class TestChallengeWeekFilter:
    def test_default_config_is_empty_noop(self):
        # Ship with empty sets so the default behaviour matches today's
        # rendering. Wolf populates them once he picks the week-arcs.
        for size, skip in _CHALLENGE_WEEKS_SKIP_BY_SIZE.items():
            assert skip == set(), (
                f"_CHALLENGE_WEEKS_SKIP_BY_SIZE[{size!r}] must default to "
                "an empty set so the hook stays additive until populated."
            )

    def test_empty_skip_returns_input_unchanged(self):
        result = _filter_challenge_weeks_by_size(CHALLENGE_30_TAGE, "solo")
        assert result == CHALLENGE_30_TAGE

    def test_unknown_size_is_noop(self):
        result = _filter_challenge_weeks_by_size(CHALLENGE_30_TAGE, "unknown_size")
        assert result == CHALLENGE_30_TAGE

    def test_missing_size_is_noop(self):
        result = _filter_challenge_weeks_by_size(CHALLENGE_30_TAGE, "")
        assert result == CHALLENGE_30_TAGE

    def test_populated_skip_drops_matching_keys(self, monkeypatch):
        # Simulate Wolf adding "woche_1" to solo's skip-set.
        monkeypatch.setitem(
            _CHALLENGE_WEEKS_SKIP_BY_SIZE, "solo", {"woche_1"},
        )
        result = _filter_challenge_weeks_by_size(CHALLENGE_30_TAGE, "solo")
        assert "woche_1" not in result
        # Other weeks survive.
        assert "woche_2" in result
        assert "abschluss" in result

    def test_filter_does_not_mutate_source(self, monkeypatch):
        monkeypatch.setitem(
            _CHALLENGE_WEEKS_SKIP_BY_SIZE, "solo", {"woche_1"},
        )
        _filter_challenge_weeks_by_size(CHALLENGE_30_TAGE, "solo")
        # Guard against someone swapping to pop() and breaking the shared
        # module-level dict for every subsequent caller.
        assert "woche_1" in CHALLENGE_30_TAGE


# ---------------------------------------------------------------------------
# Variante C — wiring into the renderer
# ---------------------------------------------------------------------------

class TestChallengeFilterWiredIntoRenderer:
    def test_renderer_calls_filter_after_variant_selection(self):
        from services import sofort_start_generator
        src = inspect.getsource(
            sofort_start_generator.generate_30_tage_challenge_html_v2
        )
        # The call must appear in the renderer so the hook is live.
        assert "_filter_challenge_weeks_by_size(" in src, (
            "generate_30_tage_challenge_html_v2 must invoke "
            "_filter_challenge_weeks_by_size — otherwise Variante C is a "
            "dead config."
        )
