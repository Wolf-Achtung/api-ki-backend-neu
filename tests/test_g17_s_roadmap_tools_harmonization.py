# -*- coding: utf-8 -*-
"""
Tests für Sprint G17.S – Roadmap- & Tools-Harmonisierung.

Prüft:
1. Neue Min-Words-Limits für roadmap_90d sind korrekt
2. Tools-Empfehlungen Team ≥ 180 Wörter (Finance-Erweiterung)
3. Solo/KMU Tools erweitert (Responsible AI)
4. BRANCH_SHORT_LABEL ersetzt lange Branchensätze
5. Redundanz-Warnings für DATA/BUSINESS_CASE reduziert
6. strategie_governance Solo ≥ 130 Wörter (Mini-Governance-Booster)

Version: 1.0.0 (Sprint G17.S)
"""
import os
import sys
import pytest
import re

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestG17SRoadmapMinWords:
    """Test TASK 1: New roadmap_90d min_words limits."""

    def test_report_validator_solo_roadmap_limit(self):
        """Solo roadmap_90d should have min 150 words (not 250)."""
        from services.report_validator import ReportValidator

        # Access class-level constant directly (no instance needed)
        limits = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE.get("solo", {})

        assert "roadmap_90d" in limits, "roadmap_90d not in solo limits"
        assert limits["roadmap_90d"] == 150, \
            f"Solo roadmap_90d should be 150, got {limits['roadmap_90d']}"

    def test_report_validator_team_roadmap_limit(self):
        """Team roadmap_90d should have min 200 words (not 300)."""
        from services.report_validator import ReportValidator

        # Access class-level constant directly (no instance needed)
        limits = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE.get("team", {})

        assert "roadmap_90d" in limits, "roadmap_90d not in team limits"
        assert limits["roadmap_90d"] == 200, \
            f"Team roadmap_90d should be 200, got {limits['roadmap_90d']}"

    def test_report_validator_kmu_roadmap_limit(self):
        """KMU roadmap_90d should have min 220 words (not 350)."""
        from services.report_validator import ReportValidator

        # Access class-level constant directly (no instance needed)
        limits = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE.get("kmu", {})

        assert "roadmap_90d" in limits, "roadmap_90d not in kmu limits"
        assert limits["roadmap_90d"] == 220, \
            f"KMU roadmap_90d should be 220, got {limits['roadmap_90d']}"

    def test_config_validation_roadmap_limits(self):
        """config_validation.py should have roadmap_90d entries."""
        from services.config_validation import SECTION_MIN_WORDS

        assert ("solo", "roadmap_90d") in SECTION_MIN_WORDS
        assert ("team", "roadmap_90d") in SECTION_MIN_WORDS
        assert ("kmu", "roadmap_90d") in SECTION_MIN_WORDS

        # SPRINT N2: Reduced min-words thresholds
        assert SECTION_MIN_WORDS[("solo", "roadmap_90d")] == 130
        assert SECTION_MIN_WORDS[("team", "roadmap_90d")] == 170
        assert SECTION_MIN_WORDS[("kmu", "roadmap_90d")] == 190


class TestG17SToolsEmpfehlungenExtension:
    """Test TASK 2 & 5: Tools-Empfehlungen extensions."""

    def test_tools_prompt_has_responsible_ai_section(self):
        """tools_empfehlungen.md should have Responsible AI section."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "tools_empfehlungen.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should mention Responsible AI
        assert "Responsible AI" in content, \
            "tools_empfehlungen.md missing Responsible AI section"

        # Should have audit trails
        assert "Audit" in content or "audit" in content, \
            "tools_empfehlungen.md missing audit trails content"

        # Should have versioning
        assert "Versionierung" in content or "Version" in content, \
            "tools_empfehlungen.md missing versioning content"

    def test_tools_prompt_has_team_finance_section(self):
        """tools_empfehlungen.md should have Team Finance extension (BAIT/VAIT/MaRisk)."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "tools_empfehlungen.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should mention regulated branches content
        assert "regulierte Branchen" in content or "BAIT" in content or "VAIT" in content, \
            "tools_empfehlungen.md missing Team Finance / regulated branches content"

        # Should have compliance tools section
        assert "Compliance" in content, \
            "tools_empfehlungen.md missing Compliance content"

    def test_tools_prompt_anti_redundancy_rules(self):
        """tools_empfehlungen.md should have anti-redundancy rules."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "tools_empfehlungen.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should mention Tools-Engine anti-redundancy
        assert "KEINE Dopplung" in content or "Tools-Engine" in content, \
            "tools_empfehlungen.md missing anti-redundancy rules"

    def test_tools_prompt_version_updated(self):
        """tools_empfehlungen.md should have G17.S version."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "tools_empfehlungen.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "G17.S" in content or "v5.5" in content, \
            "tools_empfehlungen.md version should be updated for G17.S"


class TestG17SStrategieGovernanceSolo:
    """Test TASK 4: Mini-Governance for Solo."""

    def test_strategie_governance_has_mini_governance(self):
        """strategie_governance.md should have Mini-Governance für Solo section."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "strategie_governance.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should have Mini-Governance section
        assert "Mini-Governance" in content, \
            "strategie_governance.md missing Mini-Governance section"

        # Should mention versioning
        assert "Versionsführung" in content or "Version" in content, \
            "strategie_governance.md Mini-Governance missing versioning"

        # Should mention transparency
        assert "Transparenz" in content, \
            "strategie_governance.md Mini-Governance missing transparency"

        # Should mention approval/delivery check
        assert "Abnahme" in content or "Prüfung" in content, \
            "strategie_governance.md Mini-Governance missing approval check"

    def test_strategie_governance_solo_conditional(self):
        """Mini-Governance should be Solo-only (Jinja conditional)."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "strategie_governance.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should have Jinja conditional for solo
        assert "{% if COMPANY_SIZE ==" in content and "solo" in content, \
            "strategie_governance.md Mini-Governance should be Solo-conditional"

    def test_strategie_governance_no_team_terms_in_mini_governance(self):
        """Mini-Governance HTML content should not contain team-specific terms."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "strategie_governance.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract only the HTML Mini-Governance section (not the developer instructions)
        # Look for the <h3>Mini-Governance section in the HTML
        match = re.search(
            r'<h3>Mini-Governance\s+für\s+Solo</h3>.*?{% endif %}',
            content, re.DOTALL | re.IGNORECASE
        )

        if match:
            mini_gov_html = match.group(0)

            # Should not contain forbidden team terms in actual HTML content
            # Note: "Team" in "Teamkontexte" is allowed (it's about future scaling)
            forbidden = ["Mitarbeiter", "Abteilung", "Governance Board"]
            for term in forbidden:
                assert term not in mini_gov_html, \
                    f"Mini-Governance HTML contains forbidden term: {term}"


class TestG17SBranchShortLabel:
    """Test TASK 3: BRANCH_SHORT_LABEL mapping."""

    def test_branch_short_labels_de_defined(self):
        """BRANCH_SHORT_LABELS_DE should be defined with all sizes."""
        from services.prompt_enhancer import BRANCH_SHORT_LABELS_DE

        assert "solo_beratung" in BRANCH_SHORT_LABELS_DE
        assert "team_finanzen" in BRANCH_SHORT_LABELS_DE
        assert "kmu_beratung" in BRANCH_SHORT_LABELS_DE

        # Check specific expected values
        assert "Beratungsangebot" in BRANCH_SHORT_LABELS_DE["solo_beratung"]
        assert "Finanzteam" in BRANCH_SHORT_LABELS_DE["team_finanzen"]

    def test_branch_short_labels_en_defined(self):
        """BRANCH_SHORT_LABELS_EN should be defined with all sizes."""
        from services.prompt_enhancer import BRANCH_SHORT_LABELS_EN

        assert "solo_beratung" in BRANCH_SHORT_LABELS_EN
        assert "team_finanzen" in BRANCH_SHORT_LABELS_EN
        assert "kmu_beratung" in BRANCH_SHORT_LABELS_EN

    def test_generate_short_labels_includes_branch_short(self):
        """generate_short_labels should return BRANCH_SHORT_LABEL."""
        from services.prompt_enhancer import generate_short_labels

        briefing = {
            "branche": "finanzen",
            "company_size": "team",
        }

        labels = generate_short_labels(briefing, lang="de")

        assert "BRANCH_SHORT_LABEL" in labels
        assert "Finanzteam" in labels["BRANCH_SHORT_LABEL"]

    def test_generate_short_labels_solo_beratung(self):
        """Solo/Beratung should get correct short label."""
        from services.prompt_enhancer import generate_short_labels

        briefing = {
            "branche": "beratung",
            "company_size": "solo",
        }

        labels = generate_short_labels(briefing, lang="de")

        assert "BRANCH_SHORT_LABEL" in labels
        assert "KI-Readiness" in labels["BRANCH_SHORT_LABEL"]


class TestG17SRewriteEnginePatterns:
    """Test TASK 3: Redundancy patterns in rewrite engine."""

    def test_branch_context_redundancy_patterns_defined(self):
        """TEMPLATE_PHRASES should have branch_context_redundancy patterns."""
        from services.prompt_rewrite_engine import TEMPLATE_PHRASES

        assert "branch_context_redundancy" in TEMPLATE_PHRASES
        assert len(TEMPLATE_PHRASES["branch_context_redundancy"]) >= 3

    def test_cost_block_redundancy_patterns_defined(self):
        """TEMPLATE_PHRASES should have cost_block_redundancy patterns."""
        from services.prompt_rewrite_engine import TEMPLATE_PHRASES

        assert "cost_block_redundancy" in TEMPLATE_PHRASES
        assert len(TEMPLATE_PHRASES["cost_block_redundancy"]) >= 3

    def test_issue_types_include_g17s(self):
        """ISSUE_TYPES should include G17.S issue types."""
        from services.prompt_rewrite_engine import ISSUE_TYPES

        assert "branch_context_redundancy" in ISSUE_TYPES
        assert "cost_block_redundancy" in ISSUE_TYPES

    def test_detect_branch_context_redundancy(self):
        """Should detect overly long branch descriptions."""
        from services.prompt_rewrite_engine import TEMPLATE_PHRASES
        import re

        test_text = "Beratung, Durchführung und Operationalisierung von KI-Readiness-Analysen"

        matches_found = False
        for pattern in TEMPLATE_PHRASES["branch_context_redundancy"]:
            if re.search(pattern, test_text, re.IGNORECASE):
                matches_found = True
                break

        assert matches_found, "Should detect long branch description pattern"


class TestG17SPromptVersions:
    """Test that prompt versions are updated correctly."""

    def test_tools_empfehlungen_version(self):
        """tools_empfehlungen.md should have v5.5."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "tools_empfehlungen.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            first_lines = f.read(500)

        assert "v5.5" in first_lines or "G17.S" in first_lines

    def test_strategie_governance_version(self):
        """strategie_governance.md should have v5.3 or G17.S."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "strategie_governance.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            first_lines = f.read(500)

        assert "v5.3" in first_lines or "G17.S" in first_lines


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
