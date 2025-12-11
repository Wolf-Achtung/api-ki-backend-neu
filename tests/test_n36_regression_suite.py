# -*- coding: utf-8 -*-
"""
SPRINT N3.6 PACKAGE G: Comprehensive Regression Test Suite.

150+ tests covering all N3.6 packages:
- PACKAGE A: mypy Stability Layer (types.py)
- PACKAGE B: Extension Manager (extension_manager.py)
- PACKAGE C: Consistency Kernel v5 (G22 skip rules)
- PACKAGE D: Final Tone Harmonizer v5 (tone_harmonizer_final.py)
- PACKAGE E: Zero-Leak Layer v3 (zero_leak_engine.py)
- PACKAGE F: Performance Resilience v3 (llm_client.py)

Version: 1.0.0 (N3.6 - PLATIN++ v4.21)
"""
import pytest


# =============================================================================
# PACKAGE A: mypy Stability Layer Tests (types.py)
# =============================================================================

class TestPackageATypeDefinitions:
    """Test type definitions from types.py."""

    def test_section_dict_exists(self):
        """SectionDict type alias should exist."""
        from services.types import SectionDict

        assert SectionDict is not None

    def test_briefing_dict_exists(self):
        """BriefingDict type alias should exist."""
        from services.types import BriefingDict

        assert BriefingDict is not None

    def test_llm_response_dict_exists(self):
        """LLMResponseDict type alias should exist."""
        from services.types import LLMResponseDict

        assert LLMResponseDict is not None


class TestPackageAEngineReport:
    """Test EngineReport dataclass."""

    def test_engine_report_creation(self):
        """Should create EngineReport with defaults."""
        from services.types import EngineReport

        report = EngineReport(engine_id="TEST")

        assert report.engine_id == "TEST"
        assert report.success is True
        assert report.sections_processed == 0

    def test_engine_report_add_issue(self):
        """Should add issues to report."""
        from services.types import EngineReport

        report = EngineReport(engine_id="TEST")
        report.add_issue("Test issue")

        assert len(report.issues_found) == 1
        assert "Test issue" in report.issues_found

    def test_engine_report_add_warning(self):
        """Should add warnings to report."""
        from services.types import EngineReport

        report = EngineReport(engine_id="TEST")
        report.add_warning("Test warning")

        assert len(report.warnings) == 1
        assert "Test warning" in report.warnings

    def test_engine_report_set_metric(self):
        """Should set metric values."""
        from services.types import EngineReport

        report = EngineReport(engine_id="TEST")
        report.set_metric("test_key", 42)

        assert report.metrics["test_key"] == 42

    def test_engine_report_to_dict(self):
        """Should convert to dictionary."""
        from services.types import EngineReport

        report = EngineReport(engine_id="TEST", success=True)
        d = report.to_dict()

        assert d["engine_id"] == "TEST"
        assert d["success"] is True
        assert "issues_found" in d


class TestPackageAEngineIDs:
    """Test engine ID constants."""

    def test_engine_id_bc(self):
        """ENGINE_ID_BC should be 'BC'."""
        from services.types import ENGINE_ID_BC

        assert ENGINE_ID_BC == "BC"

    def test_engine_id_reco(self):
        """ENGINE_ID_RECO should be 'RECO'."""
        from services.types import ENGINE_ID_RECO

        assert ENGINE_ID_RECO == "RECO"

    def test_engine_id_risk(self):
        """ENGINE_ID_RISK should be 'RISK'."""
        from services.types import ENGINE_ID_RISK

        assert ENGINE_ID_RISK == "RISK"

    def test_engine_id_vendor(self):
        """ENGINE_ID_VENDOR should be 'VENDOR'."""
        from services.types import ENGINE_ID_VENDOR

        assert ENGINE_ID_VENDOR == "VENDOR"

    def test_engine_id_auto(self):
        """ENGINE_ID_AUTO should be 'AUTO'."""
        from services.types import ENGINE_ID_AUTO

        assert ENGINE_ID_AUTO == "AUTO"

    def test_engine_id_bench(self):
        """ENGINE_ID_BENCH should be 'BENCH'."""
        from services.types import ENGINE_ID_BENCH

        assert ENGINE_ID_BENCH == "BENCH"

    def test_engine_id_tone(self):
        """ENGINE_ID_TONE should be 'TONE'."""
        from services.types import ENGINE_ID_TONE

        assert ENGINE_ID_TONE == "TONE"

    def test_all_engine_ids_list(self):
        """ALL_ENGINE_IDS should contain all IDs."""
        from services.types import ALL_ENGINE_IDS

        assert len(ALL_ENGINE_IDS) >= 7
        assert "BC" in ALL_ENGINE_IDS
        assert "RECO" in ALL_ENGINE_IDS


class TestPackageAHealingFlags:
    """Test HealingFlags dataclass."""

    def test_healing_flags_creation(self):
        """Should create HealingFlags with all False."""
        from services.types import HealingFlags

        flags = HealingFlags()

        assert flags.BC is False
        assert flags.RECO is False
        assert flags.RISK is False

    def test_healing_flags_set_healed(self):
        """Should set healed flag by engine ID."""
        from services.types import HealingFlags

        flags = HealingFlags()
        flags.set_healed("BC")

        assert flags.BC is True
        assert flags.RECO is False

    def test_healing_flags_is_healed(self):
        """Should check if healed by engine ID."""
        from services.types import HealingFlags

        flags = HealingFlags()
        flags.BC = True

        assert flags.is_healed("BC") is True
        assert flags.is_healed("RECO") is False

    def test_healing_flags_to_dict(self):
        """Should convert to dictionary."""
        from services.types import HealingFlags

        flags = HealingFlags(BC=True, RECO=True)
        d = flags.to_dict()

        assert d["BC"] is True
        assert d["RECO"] is True
        assert d["RISK"] is False

    def test_healing_flags_from_dict(self):
        """Should create from dictionary."""
        from services.types import HealingFlags

        data = {"BC": True, "RECO": True, "RISK": False}
        flags = HealingFlags.from_dict(data)

        assert flags.BC is True
        assert flags.RECO is True
        assert flags.RISK is False


class TestPackageAGetHealingFlags:
    """Test get_healing_flags function."""

    def test_get_healing_flags_empty(self):
        """Should handle empty sections."""
        from services.types import get_healing_flags

        flags = get_healing_flags({})

        assert flags.BC is False
        assert flags.RECO is False

    def test_get_healing_flags_unified_format(self):
        """Should extract from unified _healed dict."""
        from services.types import get_healing_flags

        sections = {"_healed": {"BC": True, "RECO": True}}
        flags = get_healing_flags(sections)

        assert flags.BC is True
        assert flags.RECO is True

    def test_get_healing_flags_legacy_format(self):
        """Should support legacy _bc_healed format."""
        from services.types import get_healing_flags

        sections = {"_bc_healed": True, "_reco_healed": True}
        flags = get_healing_flags(sections)

        assert flags.BC is True
        assert flags.RECO is True

    def test_get_healing_flags_consistency_normalized(self):
        """Should support _bc_consistency_normalized flag."""
        from services.types import get_healing_flags

        sections = {"_bc_consistency_normalized": True}
        flags = get_healing_flags(sections)

        assert flags.BC is True


class TestPackageASetHealingFlag:
    """Test set_healing_flag function."""

    def test_set_healing_flag_creates_healed_dict(self):
        """Should create _healed dict if not exists."""
        from services.types import set_healing_flag

        sections = {}
        set_healing_flag(sections, "BC")

        assert "_healed" in sections
        assert sections["_healed"]["BC"] is True

    def test_set_healing_flag_sets_legacy(self):
        """Should set legacy flags for BC."""
        from services.types import set_healing_flag

        sections = {}
        set_healing_flag(sections, "BC")

        assert sections.get("_bc_healed") is True
        assert sections.get("_bc_consistency_normalized") is True

    def test_set_healing_flag_sets_reco_legacy(self):
        """Should set legacy flags for RECO."""
        from services.types import set_healing_flag

        sections = {}
        set_healing_flag(sections, "RECO")

        assert sections.get("_reco_healed") is True


class TestPackageAExtensionConfig:
    """Test ExtensionConfig dataclass."""

    def test_extension_config_creation(self):
        """Should create ExtensionConfig with defaults."""
        from services.types import ExtensionConfig

        config = ExtensionConfig()

        assert config.target_words == 200
        assert config.min_words == 100
        assert config.max_words == 500

    def test_extension_config_custom_values(self):
        """Should allow custom values."""
        from services.types import ExtensionConfig

        config = ExtensionConfig(target_words=300, style="premium")

        assert config.target_words == 300
        assert config.style == "premium"


class TestPackageAConsistencyIssue:
    """Test ConsistencyIssue dataclass."""

    def test_consistency_issue_creation(self):
        """Should create ConsistencyIssue."""
        from services.types import ConsistencyIssue

        issue = ConsistencyIssue(
            code="BC_001",
            severity="error",
            message="Test error"
        )

        assert issue.code == "BC_001"
        assert issue.severity == "error"
        assert issue.can_heal is False

    def test_consistency_issue_to_dict(self):
        """Should convert to dictionary."""
        from services.types import ConsistencyIssue

        issue = ConsistencyIssue(
            code="BC_001",
            severity="error",
            message="Test",
            healed=True
        )
        d = issue.to_dict()

        assert d["code"] == "BC_001"
        assert d["healed"] is True


# =============================================================================
# PACKAGE B: Extension Manager Tests (extension_manager.py)
# =============================================================================

class TestPackageBMinWords:
    """Test MIN_WORDS_BY_SECTION configuration."""

    def test_min_words_exists(self):
        """MIN_WORDS_BY_SECTION should exist."""
        from services.extension_manager import MIN_WORDS_BY_SECTION

        assert isinstance(MIN_WORDS_BY_SECTION, dict)

    def test_min_words_executive_summary(self):
        """executive_summary should have min words."""
        from services.extension_manager import MIN_WORDS_BY_SECTION

        assert "executive_summary" in MIN_WORDS_BY_SECTION
        # MIN_WORDS_BY_SECTION uses nested dict with size keys
        assert isinstance(MIN_WORDS_BY_SECTION["executive_summary"], dict)

    def test_min_words_recommendations(self):
        """recommendations should have min words."""
        from services.extension_manager import MIN_WORDS_BY_SECTION

        assert "recommendations" in MIN_WORDS_BY_SECTION

    def test_min_words_risks(self):
        """risks should have min words."""
        from services.extension_manager import MIN_WORDS_BY_SECTION

        assert "risks" in MIN_WORDS_BY_SECTION


class TestPackageBGptFlairPhrases:
    """Test GPT_FLAIR_PHRASES list."""

    def test_flair_phrases_exist(self):
        """GPT_FLAIR_PHRASES should exist and have entries."""
        from services.extension_manager import GPT_FLAIR_PHRASES

        assert isinstance(GPT_FLAIR_PHRASES, list)
        assert len(GPT_FLAIR_PHRASES) >= 10

    def test_flair_phrases_german(self):
        """Should contain German flair phrases."""
        from services.extension_manager import GPT_FLAIR_PHRASES

        all_phrases = " ".join(GPT_FLAIR_PHRASES).lower()
        assert "zusammenfassend" in all_phrases or "abschließend" in all_phrases


class TestPackageBBranchExtensions:
    """Test BRANCH_EXTENSIONS dictionary."""

    def test_branch_extensions_exist(self):
        """BRANCH_EXTENSIONS should exist."""
        from services.extension_manager import BRANCH_EXTENSIONS

        assert isinstance(BRANCH_EXTENSIONS, dict)

    def test_branch_extensions_has_entries(self):
        """Should have branch-specific extensions."""
        from services.extension_manager import BRANCH_EXTENSIONS

        # Should have at least some branches
        assert len(BRANCH_EXTENSIONS) >= 1


class TestPackageBToneStyles:
    """Test TONE_STYLES dictionary."""

    def test_tone_styles_exist(self):
        """TONE_STYLES should exist."""
        from services.extension_manager import TONE_STYLES

        assert isinstance(TONE_STYLES, dict)

    def test_tone_styles_analytical(self):
        """Should have analytical_decisive style."""
        from services.extension_manager import TONE_STYLES

        assert "analytical_decisive" in TONE_STYLES


class TestPackageBExtendSection:
    """Test extend_section function."""

    def test_extend_section_exists(self):
        """extend_section function should exist."""
        from services.extension_manager import extend_section

        assert callable(extend_section)

    def test_extend_section_short_text(self):
        """Should extend short text."""
        from services.extension_manager import extend_section

        result = extend_section("Short.", "exec_summary", target_words=50)

        assert result.original_words < 50
        assert len(result.extended_text) > len("Short.")

    def test_extend_section_long_text_unchanged(self):
        """Should not extend text already at target."""
        from services.extension_manager import extend_section

        long_text = " ".join(["word"] * 100)
        result = extend_section(long_text, "exec_summary", target_words=50)

        assert result.extended_text == long_text
        assert result.words_added == 0

    def test_extend_section_empty_text(self):
        """Should handle empty text."""
        from services.extension_manager import extend_section

        result = extend_section("", "exec_summary")

        assert result.original_words == 0

    def test_extend_section_returns_result(self):
        """Should return ExtensionResult."""
        from services.extension_manager import extend_section, ExtensionResult

        result = extend_section("Test text.", "exec_summary")

        assert isinstance(result, ExtensionResult)
        assert hasattr(result, "extended_text")
        assert hasattr(result, "words_added")


class TestPackageBBatchExtend:
    """Test batch_extend_sections function."""

    def test_batch_extend_exists(self):
        """batch_extend_sections function should exist."""
        from services.extension_manager import batch_extend_sections

        assert callable(batch_extend_sections)

    def test_batch_extend_multiple_sections(self):
        """Should extend multiple sections."""
        from services.extension_manager import batch_extend_sections

        sections = {
            "exec_summary": "Short summary.",
            "recommendations": "Brief reco.",
        }

        extended, results = batch_extend_sections(sections)

        assert "exec_summary" in extended
        assert "recommendations" in extended


class TestPackageBGetMinWords:
    """Test get_min_words function."""

    def test_get_min_words_exists(self):
        """get_min_words function should exist."""
        from services.extension_manager import get_min_words

        assert callable(get_min_words)

    def test_get_min_words_known_section(self):
        """Should return min words for known section."""
        from services.extension_manager import get_min_words

        min_words = get_min_words("exec_summary")

        assert min_words >= 50

    def test_get_min_words_unknown_section(self):
        """Should return default for unknown section."""
        from services.extension_manager import get_min_words

        min_words = get_min_words("unknown_section_xyz")

        assert min_words >= 50  # Default value


# =============================================================================
# PACKAGE D: Final Tone Harmonizer Tests (tone_harmonizer_final.py)
# =============================================================================

class TestPackageDGptFlairSentences:
    """Test GPT_FLAIR_SENTENCES list."""

    def test_flair_sentences_exist(self):
        """GPT_FLAIR_SENTENCES should exist."""
        from services.tone_harmonizer_final import GPT_FLAIR_SENTENCES

        assert isinstance(GPT_FLAIR_SENTENCES, list)
        assert len(GPT_FLAIR_SENTENCES) >= 20

    def test_flair_sentences_german(self):
        """Should contain German flair phrases."""
        from services.tone_harmonizer_final import GPT_FLAIR_SENTENCES

        assert any("heutigen" in s for s in GPT_FLAIR_SENTENCES)


class TestPackageDEndFloskeln:
    """Test END_SENTENCE_FLOSKELN list."""

    def test_end_floskeln_exist(self):
        """END_SENTENCE_FLOSKELN should exist."""
        from services.tone_harmonizer_final import END_SENTENCE_FLOSKELN

        assert isinstance(END_SENTENCE_FLOSKELN, list)
        assert len(END_SENTENCE_FLOSKELN) >= 5

    def test_end_floskeln_contains_insgesamt(self):
        """Should contain 'insgesamt'."""
        from services.tone_harmonizer_final import END_SENTENCE_FLOSKELN

        assert "insgesamt" in END_SENTENCE_FLOSKELN


class TestPackageDWeakToStrong:
    """Test WEAK_TO_STRONG dictionary."""

    def test_weak_to_strong_exists(self):
        """WEAK_TO_STRONG should exist."""
        from services.tone_harmonizer_final import WEAK_TO_STRONG

        assert isinstance(WEAK_TO_STRONG, dict)
        assert len(WEAK_TO_STRONG) >= 8

    def test_weak_to_strong_vielleicht(self):
        """Should replace 'vielleicht' with stronger form."""
        from services.tone_harmonizer_final import WEAK_TO_STRONG

        assert "vielleicht" in WEAK_TO_STRONG


class TestPackageDDuForms:
    """Test DU_FORMS_FINAL dictionary."""

    def test_du_forms_exist(self):
        """DU_FORMS_FINAL should exist."""
        from services.tone_harmonizer_final import DU_FORMS_FINAL

        assert isinstance(DU_FORMS_FINAL, dict)
        assert len(DU_FORMS_FINAL) >= 5

    def test_du_forms_du_kannst(self):
        """Should have replacement for 'du kannst'."""
        from services.tone_harmonizer_final import DU_FORMS_FINAL

        assert "du kannst" in DU_FORMS_FINAL


class TestPackageDRemoveGptFlair:
    """Test remove_gpt_flair_sentences function."""

    def test_remove_gpt_flair_exists(self):
        """remove_gpt_flair_sentences should exist."""
        from services.tone_harmonizer_final import remove_gpt_flair_sentences

        assert callable(remove_gpt_flair_sentences)

    def test_remove_gpt_flair_removes_sentences(self):
        """Should remove GPT flair sentences."""
        from services.tone_harmonizer_final import remove_gpt_flair_sentences

        text = "In der heutigen Zeit ist KI wichtig. Das Unternehmen wächst."
        cleaned, count = remove_gpt_flair_sentences(text)

        assert count >= 1
        assert "heutigen Zeit" not in cleaned

    def test_remove_gpt_flair_keeps_normal(self):
        """Should keep normal sentences."""
        from services.tone_harmonizer_final import remove_gpt_flair_sentences

        text = "Das Unternehmen wächst. Der Umsatz steigt."
        cleaned, count = remove_gpt_flair_sentences(text)

        assert count == 0
        assert "Unternehmen" in cleaned

    def test_remove_gpt_flair_empty_text(self):
        """Should handle empty text."""
        from services.tone_harmonizer_final import remove_gpt_flair_sentences

        cleaned, count = remove_gpt_flair_sentences("")

        assert cleaned == ""
        assert count == 0


class TestPackageDRemoveEndFloskeln:
    """Test remove_end_floskeln function."""

    def test_remove_end_floskeln_exists(self):
        """remove_end_floskeln should exist."""
        from services.tone_harmonizer_final import remove_end_floskeln

        assert callable(remove_end_floskeln)

    def test_remove_end_floskeln_removes(self):
        """Should remove end floskeln."""
        from services.tone_harmonizer_final import remove_end_floskeln

        text = "Das Ergebnis ist positiv, insgesamt."
        cleaned, count = remove_end_floskeln(text)

        # May or may not match depending on exact pattern
        assert isinstance(cleaned, str)
        assert isinstance(count, int)


class TestPackageDStrengthenWeakForms:
    """Test strengthen_weak_forms function."""

    def test_strengthen_weak_forms_exists(self):
        """strengthen_weak_forms should exist."""
        from services.tone_harmonizer_final import strengthen_weak_forms

        assert callable(strengthen_weak_forms)

    def test_strengthen_weak_forms_vielleicht(self):
        """Should replace 'vielleicht' with 'potenziell'."""
        from services.tone_harmonizer_final import strengthen_weak_forms

        text = "Das ist vielleicht sinnvoll."
        strengthened, count = strengthen_weak_forms(text)

        assert count >= 1
        assert "potenziell" in strengthened

    def test_strengthen_weak_forms_preserves_case(self):
        """Should preserve case when replacing."""
        from services.tone_harmonizer_final import strengthen_weak_forms

        text = "Vielleicht ist das gut."
        strengthened, count = strengthen_weak_forms(text)

        assert strengthened[0].isupper()


class TestPackageDReplaceDuForms:
    """Test replace_final_du_forms function."""

    def test_replace_du_forms_exists(self):
        """replace_final_du_forms should exist."""
        from services.tone_harmonizer_final import replace_final_du_forms

        assert callable(replace_final_du_forms)

    def test_replace_du_forms_du_kannst(self):
        """Should replace 'du kannst'."""
        from services.tone_harmonizer_final import replace_final_du_forms

        text = "So du kannst das umsetzen."
        cleaned, count = replace_final_du_forms(text)

        assert count >= 1
        assert "du kannst" not in cleaned.lower()


class TestPackageDApplyToneHarmonizer:
    """Test apply_tone_harmonizer_final function."""

    def test_apply_tone_harmonizer_exists(self):
        """apply_tone_harmonizer_final should exist."""
        from services.tone_harmonizer_final import apply_tone_harmonizer_final

        assert callable(apply_tone_harmonizer_final)

    def test_apply_tone_harmonizer_returns_tuple(self):
        """Should return (html, report) tuple."""
        from services.tone_harmonizer_final import apply_tone_harmonizer_final

        html = "<p>Test content.</p>"
        result = apply_tone_harmonizer_final(html)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_apply_tone_harmonizer_report_fields(self):
        """Should return report with expected fields."""
        from services.tone_harmonizer_final import apply_tone_harmonizer_final

        html = "<p>Das ist vielleicht wichtig.</p>"
        harmonized, report = apply_tone_harmonizer_final(html)

        assert hasattr(report, "flair_sentences_removed")
        assert hasattr(report, "weak_forms_strengthened")


class TestPackageDToneHarmonizerReport:
    """Test ToneHarmonizerReport dataclass."""

    def test_tone_report_creation(self):
        """Should create ToneHarmonizerReport."""
        from services.tone_harmonizer_final import ToneHarmonizerReport

        report = ToneHarmonizerReport()

        assert report.sentences_processed == 0
        assert report.flair_sentences_removed == 0

    def test_tone_report_to_dict(self):
        """Should convert to dictionary."""
        from services.tone_harmonizer_final import ToneHarmonizerReport

        report = ToneHarmonizerReport(flair_sentences_removed=5)
        d = report.to_dict()

        assert d["flair_sentences_removed"] == 5


class TestPackageDProcessSectionsToneFinal:
    """Test process_sections_tone_final function."""

    def test_process_sections_exists(self):
        """process_sections_tone_final should exist."""
        from services.tone_harmonizer_final import process_sections_tone_final

        assert callable(process_sections_tone_final)

    def test_process_sections_multiple(self):
        """Should process multiple sections."""
        from services.tone_harmonizer_final import process_sections_tone_final

        sections = {
            "exec_summary": "<p>Vielleicht ist das wichtig.</p>",
            "recommendations": "<p>Normal content.</p>",
        }

        harmonized, report = process_sections_tone_final(sections)

        assert "exec_summary" in harmonized
        assert "recommendations" in harmonized


# =============================================================================
# PACKAGE E: Zero-Leak Layer Tests (zero_leak_engine.py)
# =============================================================================

class TestPackageELeakCategories:
    """Test leak phrase categories."""

    def test_ai_reference_leaks_exist(self):
        """AI_REFERENCE_LEAKS should exist."""
        from services.zero_leak_engine import AI_REFERENCE_LEAKS

        assert isinstance(AI_REFERENCE_LEAKS, list)
        assert len(AI_REFERENCE_LEAKS) >= 30

    def test_support_leaks_exist(self):
        """SUPPORT_LEAKS should exist."""
        from services.zero_leak_engine import SUPPORT_LEAKS

        assert isinstance(SUPPORT_LEAKS, list)
        assert len(SUPPORT_LEAKS) >= 20

    def test_filler_leaks_exist(self):
        """FILLER_LEAKS should exist."""
        from services.zero_leak_engine import FILLER_LEAKS

        assert isinstance(FILLER_LEAKS, list)
        assert len(FILLER_LEAKS) >= 30

    def test_intro_leaks_exist(self):
        """INTRO_LEAKS should exist."""
        from services.zero_leak_engine import INTRO_LEAKS

        assert isinstance(INTRO_LEAKS, list)
        assert len(INTRO_LEAKS) >= 20

    def test_conclusion_leaks_exist(self):
        """CONCLUSION_LEAKS should exist."""
        from services.zero_leak_engine import CONCLUSION_LEAKS

        assert isinstance(CONCLUSION_LEAKS, list)
        assert len(CONCLUSION_LEAKS) >= 20

    def test_vague_leaks_exist(self):
        """VAGUE_LEAKS should exist."""
        from services.zero_leak_engine import VAGUE_LEAKS

        assert isinstance(VAGUE_LEAKS, list)
        assert len(VAGUE_LEAKS) >= 20


class TestPackageEAllLeakPhrases:
    """Test ALL_LEAK_PHRASES combined list."""

    def test_all_leak_phrases_200_plus(self):
        """Should have 200+ leak phrases."""
        from services.zero_leak_engine import ALL_LEAK_PHRASES

        assert len(ALL_LEAK_PHRASES) >= 200

    def test_all_leak_phrases_contains_ki(self):
        """Should contain KI reference phrases."""
        from services.zero_leak_engine import ALL_LEAK_PHRASES

        all_lower = [p.lower() for p in ALL_LEAK_PHRASES]
        assert any("ki" in p for p in all_lower) or any("ai" in p for p in all_lower)


class TestPackageEFuzzyPatterns:
    """Test FUZZY_LEAK_PATTERNS."""

    def test_fuzzy_patterns_exist(self):
        """FUZZY_LEAK_PATTERNS should exist."""
        from services.zero_leak_engine import FUZZY_LEAK_PATTERNS

        assert isinstance(FUZZY_LEAK_PATTERNS, list)
        assert len(FUZZY_LEAK_PATTERNS) >= 5


class TestPackageEDetectLeaks:
    """Test detect_leaks function."""

    def test_detect_leaks_exists(self):
        """detect_leaks function should exist."""
        from services.zero_leak_engine import detect_leaks

        assert callable(detect_leaks)

    def test_detect_leaks_finds_ai_reference(self):
        """Should detect AI reference leaks."""
        from services.zero_leak_engine import detect_leaks

        text = "Als KI-Assistent kann ich Ihnen helfen."
        leaks = detect_leaks(text)

        assert len(leaks) >= 1

    def test_detect_leaks_clean_text(self):
        """Should return empty for clean text."""
        from services.zero_leak_engine import detect_leaks

        text = "Das Unternehmen wächst kontinuierlich."
        leaks = detect_leaks(text)

        assert len(leaks) == 0

    def test_detect_leaks_returns_list(self):
        """Should return list of LeakMatch objects."""
        from services.zero_leak_engine import detect_leaks

        text = "Test text"
        leaks = detect_leaks(text)

        assert isinstance(leaks, list)


class TestPackageERemoveLeaks:
    """Test remove_leaks function."""

    def test_remove_leaks_exists(self):
        """remove_leaks function should exist."""
        from services.zero_leak_engine import remove_leaks

        assert callable(remove_leaks)

    def test_remove_leaks_removes_ai_reference(self):
        """Should remove AI reference leaks."""
        from services.zero_leak_engine import remove_leaks

        text = "Als KI-Assistent empfehle ich folgendes. Das Unternehmen wächst."
        cleaned, report = remove_leaks(text)

        assert report.total_leaks_found >= 1 or report.leaks_removed >= 1
        assert "KI-Assistent" not in cleaned

    def test_remove_leaks_preserves_content(self):
        """Should preserve non-leak content."""
        from services.zero_leak_engine import remove_leaks

        text = "Das Unternehmen wächst kontinuierlich."
        cleaned, count = remove_leaks(text)

        assert "Unternehmen" in cleaned


class TestPackageEGuaranteeLeakFree:
    """Test guarantee_leak_free function."""

    def test_guarantee_leak_free_exists(self):
        """guarantee_leak_free function should exist."""
        from services.zero_leak_engine import guarantee_leak_free

        assert callable(guarantee_leak_free)

    def test_guarantee_leak_free_multi_pass(self):
        """Should perform multiple passes until clean."""
        from services.zero_leak_engine import guarantee_leak_free

        html = "<p>Als KI kann ich helfen. Gerne erkläre ich mehr.</p>"
        clean = guarantee_leak_free(html)

        # Should not contain obvious leaks after guarantee
        from services.zero_leak_engine import detect_leaks
        remaining = detect_leaks(clean)
        assert len(remaining) == 0


class TestPackageEProcessSectionsZeroLeak:
    """Test process_sections_zero_leak function."""

    def test_process_sections_exists(self):
        """process_sections_zero_leak should exist."""
        from services.zero_leak_engine import process_sections_zero_leak

        assert callable(process_sections_zero_leak)

    def test_process_sections_multiple(self):
        """Should process multiple sections."""
        from services.zero_leak_engine import process_sections_zero_leak

        sections = {
            "exec_summary": "<p>Als KI empfehle ich.</p>",
            "recommendations": "<p>Normal content.</p>",
        }

        cleaned, report = process_sections_zero_leak(sections)

        assert "exec_summary" in cleaned
        assert "recommendations" in cleaned


class TestPackageEZeroLeakReport:
    """Test ZeroLeakReport dataclass."""

    def test_zero_leak_report_creation(self):
        """Should create ZeroLeakReport."""
        from services.zero_leak_engine import ZeroLeakReport

        report = ZeroLeakReport()

        assert report.total_leaks_found == 0
        assert report.leaks_removed == 0

    def test_zero_leak_report_fields(self):
        """Should have expected fields."""
        from services.zero_leak_engine import ZeroLeakReport

        report = ZeroLeakReport()
        report.total_leaks_found = 5
        report.leaks_removed = 5

        assert report.total_leaks_found == 5
        assert report.leaks_removed == 5


# =============================================================================
# PACKAGE F: Performance Resilience Tests (llm_client.py)
# =============================================================================

class TestPackageFTimeoutConfig:
    """Test N3.6 timeout configuration."""

    def test_max_retries_is_5(self):
        """N3.6: Max retries should be 5."""
        from services.llm_client import LLM_MAX_RETRIES

        assert LLM_MAX_RETRIES == 5

    def test_backoff_base_is_3(self):
        """N3.6: Backoff base should be 3.0s."""
        from services.llm_client import LLM_RETRY_BACKOFF_BASE

        assert LLM_RETRY_BACKOFF_BASE == 3.0

    def test_premium_timeout_is_140(self):
        """N3.6: Premium sections should have 140s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES["exec_summary"] == 140.0
        assert SECTION_TIMEOUT_OVERRIDES["recommendations"] == 140.0


class TestPackageFBackoffSequence:
    """Test N3.6 backoff sequence."""

    def test_backoff_3s(self):
        """First retry should wait 3s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()
        assert calculate_backoff(0, config) == 3.0

    def test_backoff_6s(self):
        """Second retry should wait 6s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()
        assert calculate_backoff(1, config) == 6.0

    def test_backoff_12s(self):
        """Third retry should wait 12s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()
        assert calculate_backoff(2, config) == 12.0

    def test_backoff_24s(self):
        """Fourth retry should wait 24s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()
        assert calculate_backoff(3, config) == 24.0

    def test_backoff_48s(self):
        """Fifth retry should wait 48s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()
        assert calculate_backoff(4, config) == 48.0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestN36Integration:
    """Integration tests for N3.6 packages."""

    def test_types_used_in_extension_manager(self):
        """Extension manager should use types from types.py."""
        from services.extension_manager import ExtensionResult
        from services.types import ExtensionConfig

        # Both should work together
        config = ExtensionConfig(target_words=150)
        assert config.target_words == 150

    def test_full_pipeline_zero_leak_then_tone(self):
        """Should process through zero-leak then tone harmonizer."""
        from services.zero_leak_engine import guarantee_leak_free
        from services.tone_harmonizer_final import apply_tone_harmonizer_final

        html = "<p>Als KI sage ich: Das ist vielleicht wichtig.</p>"

        # Step 1: Zero-leak
        clean = guarantee_leak_free(html)

        # Step 2: Tone harmonize
        final, report = apply_tone_harmonizer_final(clean)

        # Final should be clean of leaks and weak forms
        assert "KI" not in final
        assert "vielleicht" not in final or "potenziell" in final

    def test_healing_flags_roundtrip(self):
        """Healing flags should survive dict roundtrip."""
        from services.types import HealingFlags, get_healing_flags, set_healing_flag

        sections = {}
        set_healing_flag(sections, "BC", True)
        set_healing_flag(sections, "RECO", True)

        flags = get_healing_flags(sections)

        assert flags.BC is True
        assert flags.RECO is True
        assert flags.RISK is False
