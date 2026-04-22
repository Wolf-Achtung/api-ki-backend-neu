# -*- coding: utf-8 -*-
"""
KIS-1142 Punkt 5 — Persönliche Einschätzung im Strategy-Report.

Strategy-Äquivalent zum R1-advisor_note. Regression cover for:

  1. STRATEGY_PROMPTS["advisor_note"] exists and references the expected
     context variables (R1 dim scores + Strategy questions + budget).
  2. services.strategy_pipeline exposes R1 dimension scores in base_context
     under the r1_score_* keys the prompt relies on.
  3. The Strategy renderer wires `sections["advisor_note"]` into the
     Jinja context as `section_advisor_note`.
  4. The Strategy HTML template renders the advisor note between S-Moat
     and "Nächste Schritte", gated by a non-empty value.
"""

from __future__ import annotations

import inspect
import re

import pytest

from prompts.strategy_prompts import STRATEGY_PROMPTS
from services import strategy_pipeline


# ---------------------------------------------------------------------------
# H1 — Prompt is present and wired to the right context keys
# ---------------------------------------------------------------------------

class TestAdvisorNotePrompt:
    def test_prompt_exists_in_strategy_prompts(self):
        assert "advisor_note" in STRATEGY_PROMPTS, (
            "STRATEGY_PROMPTS['advisor_note'] missing — Strategy-Report "
            "would render no Persönliche Einschätzung."
        )
        assert STRATEGY_PROMPTS["advisor_note"].strip(), (
            "advisor_note prompt must not be empty."
        )

    @pytest.mark.parametrize("placeholder", [
        # R1 dimension scores — must be populated by strategy_pipeline.
        "r1_score_governance",
        "r1_score_sicherheit",
        "r1_score_nutzen",
        "r1_score_befaehigung",
        # Strategy context — already in base_context.
        "firmenname", "branche", "hauptleistung", "segment",
        "readiness_score", "reifegrad_label",
        "s1_budget", "s2_zeitrahmen", "s3_prioritaeten", "s4_engpass",
        "s6_foerderinteresse",
        "budget_gesamt_jahr1", "roi_realistisch", "breakeven_realistisch",
    ])
    def test_placeholder_referenced(self, placeholder):
        assert "{" + placeholder + "}" in STRATEGY_PROMPTS["advisor_note"], (
            f"advisor_note prompt does not reference {{{placeholder}}} — "
            "either the prompt lost a key or the variable was renamed."
        )

    def test_prompt_enforces_plain_text_contract(self):
        # The prompt must mirror the R1 advisor_note plain-text rule so the
        # Strategy renderer can safely wrap the output in its own HTML chrome
        # without double-styled <p>/<ul> leaking in.
        src = STRATEGY_PROMPTS["advisor_note"]
        assert "PLAIN TEXT" in src
        assert "kein HTML" in src
        assert "kein Markdown" in src

    def test_prompt_does_not_leak_r1_only_keys(self):
        # score_gesamt_display and COMPANY_SIZE are R1-specific names that
        # don't exist in Strategy's base_context. Accidentally using them
        # would KeyError at format time.
        src = STRATEGY_PROMPTS["advisor_note"]
        assert "{score_gesamt_display}" not in src
        assert "{COMPANY_SIZE}" not in src
        assert "{BRANCHE_LABEL}" not in src


# ---------------------------------------------------------------------------
# H2 — Pipeline passes the R1 dimension scores into base_context
# ---------------------------------------------------------------------------

class TestPipelineBaseContextWiring:
    """Source-level guard — the full pipeline is async/DB-backed and
    expensive to spin up for a unit check. Inspecting the source of
    generate_strategy_report catches the three common regressions:
    dropping a key, renaming it, or accidentally setting str/None to
    the wrong value."""

    def test_source_defines_r1_score_keys(self):
        src = inspect.getsource(strategy_pipeline.generate_strategy_report)
        for key in ("r1_score_governance", "r1_score_sicherheit",
                    "r1_score_nutzen", "r1_score_befaehigung"):
            assert f'"{key}"' in src, (
                f"{key!r} missing from base_context — advisor_note prompt "
                "would KeyError/format-miss."
            )

    def test_source_schedules_advisor_note_in_parallel(self):
        src = inspect.getsource(strategy_pipeline.generate_strategy_report)
        # The advisor_note generation and the exec_summary generation must
        # be gathered together so advisor_note always runs (regression
        # guard against someone removing the gather and leaving only exec).
        normalized = " ".join(src.split())
        assert '_generate_section("advisor_note"' in normalized, (
            "advisor_note section call is missing from the pipeline."
        )
        assert 'sections["advisor_note"]' in normalized, (
            "Pipeline must assign sections['advisor_note'] so the renderer "
            "can pick it up."
        )

    def test_advisor_note_extra_context_is_empty(self):
        # The prompt relies entirely on base_context. Passing extras risks
        # accidentally overriding a base_context key or masking a missing
        # base_context key at review time — this guard pins the contract.
        src = inspect.getsource(strategy_pipeline.generate_strategy_report)
        normalized = " ".join(src.split())
        assert '_generate_section("advisor_note", base_context, {},' in normalized, (
            "advisor_note should be generated with an empty extra_context "
            "dict — all data flows through base_context."
        )


# ---------------------------------------------------------------------------
# H3 — Renderer surfaces the section and template renders it
# ---------------------------------------------------------------------------

class TestRendererAndTemplateWiring:
    def test_renderer_exposes_section_advisor_note(self):
        from services import strategy_renderer
        src = inspect.getsource(strategy_renderer)
        assert '"section_advisor_note"' in src, (
            "strategy_renderer must add section_advisor_note to the "
            "template context."
        )
        assert 'sections.get("advisor_note"' in src, (
            "strategy_renderer should read sections['advisor_note'] "
            "(matching the key produced by the pipeline)."
        )

    def test_template_renders_advisor_note_block(self):
        with open("templates/strategy_report.html", "r", encoding="utf-8") as f:
            tpl = f.read()

        # The block must be gated — empty strings should not render.
        assert "{% if section_advisor_note" in tpl, (
            "Template must conditionally render the advisor note so it "
            "stays invisible if the section is empty."
        )
        # Signature and title strings follow the R1 advisor_note pattern.
        assert "Meine Einschätzung für Ihr Unternehmen" in tpl
        assert "Wolf Hohl" in tpl

    def test_template_places_advisor_note_between_s_moat_and_next_steps(self):
        with open("templates/strategy_report.html", "r", encoding="utf-8") as f:
            tpl = f.read()

        # Positional regression guard — moving the block up (before exec
        # summary) or down (after impressum) would break the intended UX.
        smoat_pos = tpl.find("section_s_moat")
        advisor_pos = tpl.find("section_advisor_note")
        next_steps_pos = tpl.find("naechste_schritte")

        assert smoat_pos > 0
        assert advisor_pos > 0
        assert next_steps_pos > 0
        assert smoat_pos < advisor_pos < next_steps_pos, (
            "advisor_note block must sit between s_moat and "
            "nächste Schritte in the Strategy template."
        )
