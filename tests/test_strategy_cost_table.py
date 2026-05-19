# -*- coding: utf-8 -*-
"""
FIX-KIS-1188-ITEM1: Strategy Cost-Tabelle „Software jährlich" sanity tests.

Funnel KIS-1188 / DB-ID 1071 (Solo segment) showed „Software jährlich" =
12.000 € in the rendered PDF — duplicating the Gesamtinvestition Jahr 1
into the software-line. Correct value: 30 % of Gesamt = 3.600 €
(= 300 €/Monat × 12).

The cost-row values come deterministically from
services.strategy_budget.calculate_strategy_budget; the LLM is told via the
S5 prompt to use them verbatim. Both layers are exercised here.
"""
from __future__ import annotations

from services.strategy_budget import calculate_strategy_budget
from prompts.strategy_prompts import STRATEGY_PROMPTS as SECTION_PROMPTS


def _calc(size: str, s1_budget: str = "2000_10000"):
    return calculate_strategy_budget(
        briefing_data={"unternehmensgroesse": size},
        strategy_questions={"s1_budget": s1_budget, "s6_foerderinteresse": "Weiß nicht"},
        handlungsfelder=[],
        report1_values={},
    )


class TestSoftwareJaehrlichValue:
    """Canonical value: 30 % of gesamt_jahr1, equals 12 × software_monatlich."""

    def test_solo_software_jaehrlich_is_3600(self):
        b = _calc("1")
        assert b.budget_software_jaehrlich == 3_600
        assert b.budget_software_monatlich == 300

    def test_team_software_jaehrlich_is_7200(self):
        b = _calc("2–10")
        assert b.budget_software_jaehrlich == 7_200  # 30% of 24k
        assert b.budget_software_monatlich == 600

    def test_kmu_software_jaehrlich_is_14400(self):
        b = _calc("11–100")
        assert b.budget_software_jaehrlich == 14_400  # 30% of 48k
        assert b.budget_software_monatlich == 1_200

    def test_software_jaehrlich_is_not_gesamt(self):
        """The bug was that software_jaehrlich equalled gesamt — must NEVER happen."""
        for size in ("1", "2–10", "11–100"):
            b = _calc(size)
            assert b.budget_software_jaehrlich != b.budget_gesamt_jahr1, (
                f"Software jährlich ({b.budget_software_jaehrlich}) duplicates "
                f"Gesamtinvestition ({b.budget_gesamt_jahr1}) for size={size}"
            )

    def test_monthly_times_twelve_equals_yearly(self):
        for size in ("1", "2–10", "11–100"):
            b = _calc(size)
            assert b.budget_software_monatlich * 12 == b.budget_software_jaehrlich


class TestCostBlockSum:
    """Solo example from the audit: 3600 + 3000 + 1800 + 1200 + 2400 = 12000."""

    def test_solo_cost_breakdown_sums_to_gesamt(self):
        b = _calc("1")
        s = (
            b.budget_software_jaehrlich
            + b.budget_implementierung
            + b.budget_schulung_einmalig
            + b.budget_schulung_laufend
            + b.budget_personal
        )
        assert s == b.budget_gesamt_jahr1 == 12_000

    def test_audit_exact_split_solo(self):
        """Audit reference: 3600/3000/1800/1200/2400."""
        b = _calc("1")
        assert b.budget_software_jaehrlich == 3_600
        assert b.budget_implementierung == 3_000
        assert b.budget_schulung_einmalig == 1_800
        assert b.budget_schulung_laufend == 1_200
        assert b.budget_personal == 2_400


class TestS5PromptGuardsCostTable:
    """The prompt must reference budget_software_jaehrlich and forbid the
    LLM from duplicating budget_gesamt_jahr1 into the software line."""

    def test_s5_prompt_mentions_software_jaehrlich_variable(self):
        prompt = SECTION_PROMPTS["S5"]
        assert "{budget_software_jaehrlich}" in prompt

    def test_s5_prompt_warns_against_duplicating_gesamt(self):
        prompt = SECTION_PROMPTS["S5"]
        # The strengthened rule must explicitly forbid setting gesamt as software.
        assert "NIE die Gesamtinvestition" in prompt
        assert "Software-Jahreskosten" in prompt

    def test_s5_prompt_has_explicit_five_row_structure(self):
        """FIX-KIS-1188-ITEM1 hardening: the prompt enumerates the 5 cost
        rows explicitly so the LLM cannot invent a duplicate row."""
        prompt = SECTION_PROMPTS["S5"]
        assert "FIX-KIS-1188-ITEM1" in prompt
        # The 5 enumerated rows
        assert "Software-Lizenzen (Jahresbedarf)" in prompt
        assert "Implementierung (einmalig)" in prompt
        assert "Schulung (einmalig)" in prompt
        assert "Schulung (laufend/Jahr)" in prompt
        assert "Personal/Koordination" in prompt
