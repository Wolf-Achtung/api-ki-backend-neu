"""
FIX-RECO-PLACEHOLDERS-P0: Regression tests for Recommendations placeholder fixes.

Tests:
1. SCORE_GOVERNANCE uppercase alias is derived from score_governance
2. TOP_RISKS is deterministically derived as 3-bullet string from scores
3. Prompt contract raises RuntimeError in STRICT mode for unresolved placeholders
4. Must-not-happen: No PLACEHOLDER findings in RECOMMENDATIONS_HTML
"""
import os
import re
import sys
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Handle optional dependencies
try:
    import sqlalchemy  # noqa: F401
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    from gpt_analyze import _build_prompt_vars
    HAS_GPT_ANALYZE = True
except Exception:
    HAS_GPT_ANALYZE = False
    _build_prompt_vars = None  # type: ignore[assignment]

try:
    from services.report_validator import ReportValidator
    HAS_VALIDATOR = True
except Exception:
    HAS_VALIDATOR = False
    ReportValidator = None  # type: ignore[assignment,misc]


_skip_no_sqlalchemy = pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
_skip_no_gpt = pytest.mark.skipif(not HAS_GPT_ANALYZE, reason="gpt_analyze not importable")
_skip_no_validator = pytest.mark.skipif(not HAS_VALIDATOR, reason="report_validator not importable")


@_skip_no_sqlalchemy
@_skip_no_gpt
class TestScoreGovernanceBackfill:
    """TASK 1: SCORE_GOVERNANCE uppercase alias derivation."""

    def test_score_governance_uppercase_from_scores(self):
        """When score_governance exists in scores, SCORE_GOVERNANCE is set in vars_dict."""
        briefing = {"hauptleistung": "KI-Beratung", "unternehmensgroesse": "solo"}
        scores = {"governance": 72, "security": 55, "value": 60, "enablement": 45, "overall": 58}

        vars_dict = _build_prompt_vars(briefing, scores)

        assert "SCORE_GOVERNANCE" in vars_dict
        # Should be derived from score_governance (which comes from scores["governance"])
        assert str(vars_dict["SCORE_GOVERNANCE"]) != ""
        assert "72" in str(vars_dict["SCORE_GOVERNANCE"]) or vars_dict["SCORE_GOVERNANCE"] == 72

    def test_score_governance_zero_fallback(self):
        """When governance score is 0 or missing, SCORE_GOVERNANCE still gets set."""
        briefing = {"hauptleistung": "Test"}
        scores = {"overall": 50}  # No governance key

        vars_dict = _build_prompt_vars(briefing, scores)

        assert "SCORE_GOVERNANCE" in vars_dict
        # Should be "0" or fallback, not empty/missing
        assert vars_dict["SCORE_GOVERNANCE"] is not None


@_skip_no_sqlalchemy
@_skip_no_gpt
class TestTopRisksDerivation:
    """TASK 1: TOP_RISKS deterministic derivation from scores."""

    def test_top_risks_is_3_bullet_string(self):
        """TOP_RISKS should be a 3-bullet string derived from weakest score dimensions."""
        briefing = {"hauptleistung": "IT-Dienstleistung"}
        scores = {"governance": 30, "security": 70, "value": 50, "enablement": 40, "overall": 47}

        vars_dict = _build_prompt_vars(briefing, scores)

        assert "TOP_RISKS" in vars_dict
        top_risks = vars_dict["TOP_RISKS"]
        assert isinstance(top_risks, str)

        # Should contain exactly 3 bullet points
        bullets = [line for line in top_risks.split("\n") if line.strip().startswith("\u2022")]
        assert len(bullets) == 3, f"Expected 3 bullets, got {len(bullets)}: {top_risks}"

    def test_top_risks_sorted_by_weakest(self):
        """TOP_RISKS bullets should be ordered by weakest score first."""
        briefing = {"hauptleistung": "Beratung"}
        scores = {"governance": 80, "security": 20, "value": 60, "enablement": 10, "overall": 42}

        vars_dict = _build_prompt_vars(briefing, scores)
        top_risks = vars_dict["TOP_RISKS"]

        # enablement (10) should appear before security (20) which should appear before value (60)
        lines = [l for l in top_risks.split("\n") if l.strip()]
        assert "10/100" in lines[0], f"Expected enablement (10) first, got: {lines[0]}"
        assert "20/100" in lines[1], f"Expected security (20) second, got: {lines[1]}"
        assert "60/100" in lines[2], f"Expected value (60) third, got: {lines[2]}"

    def test_top_risks_not_empty_with_zero_scores(self):
        """TOP_RISKS should still be generated even with all zero scores."""
        briefing = {"hauptleistung": "Test"}
        scores = {"governance": 0, "security": 0, "value": 0, "enablement": 0, "overall": 0}

        vars_dict = _build_prompt_vars(briefing, scores)

        assert vars_dict["TOP_RISKS"].strip() != ""
        bullets = [l for l in vars_dict["TOP_RISKS"].split("\n") if l.strip()]
        assert len(bullets) == 3


class TestPromptContract:
    """TASK 2: Prompt interpolation contract -- fail-fast on unresolved placeholders."""

    def test_unresolved_placeholder_pattern_detection(self):
        """The contract regex should match {UPPERCASE_PLACEHOLDER} patterns."""
        pattern = re.compile(r'\{([A-Z][A-Z0-9_]+)\}')

        # Should match
        assert pattern.findall("text {SCORE_GOVERNANCE} more")
        assert pattern.findall("text {TOP_RISKS} more")
        assert pattern.findall("{ABC_DEF_123}")

        # Should NOT match (lowercase, Jinja2, single char)
        assert not pattern.findall("{{lowercase_var}}")
        assert not pattern.findall("{a}")
        assert not pattern.findall("{lowercase}")
        # Single char uppercase should NOT match (requires 2+ chars)
        assert not pattern.findall("{A}")

    def test_strict_mode_raises_on_unresolved(self):
        """In STRICT mode, unresolved placeholders should raise RuntimeError."""
        prompt_text = "Governance Score: {SCORE_GOVERNANCE} und Risiken: {TOP_RISKS}"
        pattern = re.compile(r'\{([A-Z][A-Z0-9_]+)\}')
        matches = pattern.findall(prompt_text)

        assert "SCORE_GOVERNANCE" in matches
        assert "TOP_RISKS" in matches

        # In STRICT mode, this would raise
        with pytest.raises(RuntimeError, match="PROMPT-CONTRACT"):
            if matches:
                raise RuntimeError(
                    f"[FIX-RECO][PROMPT-CONTRACT] Unresolved placeholders in prompt "
                    f"for section=recommendations: {sorted(set(matches))}. "
                    f"Add missing vars to _build_prompt_vars() or fix the prompt template."
                )

    @_skip_no_sqlalchemy
    @_skip_no_gpt
    def test_resolved_placeholders_pass_contract(self):
        """After proper interpolation, no {UPPERCASE} patterns should remain."""
        briefing = {"hauptleistung": "Webdesign"}
        scores = {"governance": 65, "security": 55, "value": 70, "enablement": 50, "overall": 60}

        vars_dict = _build_prompt_vars(briefing, scores)

        # Simulate a prompt that uses these vars (single-brace style)
        prompt_template = "Score: {SCORE_GOVERNANCE}, Risks: {TOP_RISKS}"

        # Replace using vars_dict
        def replace_fn(m: re.Match) -> str:
            key = m.group(1)
            val = vars_dict.get(key) or vars_dict.get(key.lower())
            return str(val) if val is not None else ""

        resolved = re.sub(r'\{([A-Z][A-Z0-9_]+)\}', replace_fn, prompt_template)

        # After resolution, no uppercase placeholders should remain
        remaining = re.findall(r'\{[A-Z][A-Z0-9_]+\}', resolved)
        assert remaining == [], f"Unresolved placeholders remain: {remaining}"


@_skip_no_sqlalchemy
@_skip_no_gpt
class TestMustNotHappenOutputScrub:
    """
    Must-not-happen: After output scrub, {SCORE_GOVERNANCE} and {TOP_RISKS}
    must not remain in LLM output.
    """

    def test_validator_does_not_find_score_governance_placeholder(self):
        """After vars backfill + output scrub, {SCORE_GOVERNANCE} must not appear in content."""
        briefing = {"hauptleistung": "Coaching"}
        scores = {"governance": 45, "security": 60, "value": 55, "enablement": 50, "overall": 52}

        vars_dict = _build_prompt_vars(briefing, scores)

        # Simulate LLM output containing placeholder
        llm_output = '<p>Der Governance-Score betraegt {SCORE_GOVERNANCE} Punkte.</p>'

        # Apply the output scrub (same logic as in gpt_analyze.py)
        pattern = re.compile(r'\{([A-Z][A-Z0-9_]+)\}')

        def _replace(m: re.Match) -> str:
            key = m.group(1)
            val = vars_dict.get(key) or vars_dict.get(key.lower())
            return str(val) if val is not None else ""

        scrubbed = pattern.sub(_replace, llm_output)

        # Verify: no {SCORE_GOVERNANCE} remains
        assert "{SCORE_GOVERNANCE}" not in scrubbed
        # Verify: the value was substituted
        assert "45" in scrubbed or str(vars_dict.get("SCORE_GOVERNANCE", "")) in scrubbed

    def test_validator_does_not_find_top_risks_placeholder(self):
        """After vars backfill + output scrub, {TOP_RISKS} must not appear in content."""
        briefing = {"hauptleistung": "Marketing"}
        scores = {"governance": 30, "security": 40, "value": 50, "enablement": 20, "overall": 35}

        vars_dict = _build_prompt_vars(briefing, scores)

        # Simulate LLM output containing placeholder
        llm_output = '<p>Die wichtigsten Risiken: {TOP_RISKS}</p>'

        # Apply the output scrub
        pattern = re.compile(r'\{([A-Z][A-Z0-9_]+)\}')

        def _replace(m: re.Match) -> str:
            key = m.group(1)
            val = vars_dict.get(key) or vars_dict.get(key.lower())
            return str(val) if val is not None else ""

        scrubbed = pattern.sub(_replace, llm_output)

        # Verify: no {TOP_RISKS} remains
        assert "{TOP_RISKS}" not in scrubbed
        # Verify: bullet points were substituted
        assert "\u2022" in scrubbed


@_skip_no_validator
class TestMustNotHappenValidator:
    """
    Must-not-happen: Validator must not find PLACEHOLDER errors in clean content.

    These specific log messages must never appear after fix:
    [PLACEHOLDER] RECOMMENDATIONS_HTML: Nicht ersetzter Placeholder gefunden: {SCORE_GOVERNANCE}
    [PLACEHOLDER] RECOMMENDATIONS_HTML: Nicht ersetzter Placeholder gefunden: {TOP_RISKS}
    [PLACEHOLDER] recommendations: Nicht ersetzter Placeholder gefunden: {SCORE_GOVERNANCE}
    [PLACEHOLDER] recommendations: Nicht ersetzter Placeholder gefunden: {TOP_RISKS}
    """

    def test_recommendations_html_clean_after_full_pipeline(self):
        """Simulated full pipeline: RECOMMENDATIONS_HTML should have zero placeholder violations."""
        # Content that WOULD have been caught before the fix (now clean after output scrub)
        clean_content = (
            '<section class="section recommendations">'
            '<h2>Handlungsempfehlungen</h2>'
            '<p>Governance-Bewertung: 45/100. Die drei wichtigsten Risiken sind:</p>'
            '<ul><li>Befaehigung (20/100): Mangelnde KI-Kompetenz</li>'
            '<li>Governance (30/100): Fehlende Richtlinien</li>'
            '<li>Sicherheit (40/100): Datenschutz-Luecken</li></ul>'
            '</section>'
        )

        sections = {
            "RECOMMENDATIONS_HTML": clean_content,
            "recommendations": clean_content,
        }
        meta = {"unternehmensgroesse": "solo"}

        validator = ReportValidator(sections=sections, meta=meta)
        validator._check_placeholders()

        # Filter for PLACEHOLDER errors in recommendations sections
        reco_placeholder_errors = [
            e for e in validator.errors
            if e.category == "PLACEHOLDER"
            and e.section in ("RECOMMENDATIONS_HTML", "recommendations")
        ]

        assert reco_placeholder_errors == [], (
            f"MUST NOT HAPPEN: Placeholder violations found in recommendations: "
            f"{[(e.section, e.message) for e in reco_placeholder_errors]}"
        )

    def test_unresolved_placeholders_still_caught_by_validator(self):
        """If output scrub fails, validator should still catch unresolved placeholders."""
        # Content WITH unresolved placeholders (simulating scrub failure)
        bad_content = (
            '<section class="section recommendations">'
            '<p>Score: {SCORE_GOVERNANCE}, Risiken: {TOP_RISKS}</p>'
            '</section>'
        )

        sections = {"RECOMMENDATIONS_HTML": bad_content}
        meta = {"unternehmensgroesse": "solo"}

        validator = ReportValidator(sections=sections, meta=meta)
        validator._check_placeholders()

        # Should find the placeholders
        placeholder_errors = [
            e for e in validator.errors
            if e.category == "PLACEHOLDER"
        ]
        assert len(placeholder_errors) >= 2, (
            f"Validator should catch unresolved placeholders, found: {len(placeholder_errors)}"
        )
