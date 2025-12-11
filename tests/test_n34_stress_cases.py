# -*- coding: utf-8 -*-
"""
SPRINT N3.4 TASK 6: Stress Test Cases.

Tests for the 9-combination stress test engine.
"""
import pytest


class TestStressTestConfiguration:
    """Test stress test configuration and constants."""

    def test_temperatures_defined(self):
        """Should have 3 temperature levels defined."""
        from services.stress_test_engine import STRESS_TEMPERATURES

        assert len(STRESS_TEMPERATURES) == 3
        assert 0.3 in STRESS_TEMPERATURES
        assert 0.7 in STRESS_TEMPERATURES
        assert 1.0 in STRESS_TEMPERATURES

    def test_truncation_levels_defined(self):
        """Should have 3 truncation levels defined."""
        from services.stress_test_engine import TruncationLevel

        assert len(TruncationLevel) == 3
        assert TruncationLevel.SHORT.value == "short"
        assert TruncationLevel.MEDIUM.value == "medium"
        assert TruncationLevel.FULL.value == "full"

    def test_truncation_multipliers_defined(self):
        """Should have multipliers for each truncation level."""
        from services.stress_test_engine import (
            TRUNCATION_MULTIPLIERS,
            TruncationLevel,
        )

        assert TRUNCATION_MULTIPLIERS[TruncationLevel.SHORT] == 0.3
        assert TRUNCATION_MULTIPLIERS[TruncationLevel.MEDIUM] == 0.6
        assert TRUNCATION_MULTIPLIERS[TruncationLevel.FULL] == 1.0


class TestStressTestConfig:
    """Test StressTestConfig data class."""

    def test_config_creation(self):
        """Should create config with temperature and truncation."""
        from services.stress_test_engine import StressTestConfig, TruncationLevel

        config = StressTestConfig(
            temperature=0.7,
            truncation=TruncationLevel.MEDIUM
        )

        assert config.temperature == 0.7
        assert config.truncation == TruncationLevel.MEDIUM

    def test_get_word_target(self):
        """Should calculate word target based on truncation."""
        from services.stress_test_engine import StressTestConfig, TruncationLevel

        config_full = StressTestConfig(
            temperature=0.7,
            truncation=TruncationLevel.FULL
        )
        config_short = StressTestConfig(
            temperature=0.7,
            truncation=TruncationLevel.SHORT
        )

        target_full = config_full.get_word_target("executive_summary")
        target_short = config_short.get_word_target("executive_summary")

        # Short should be 30% of full
        assert target_short == int(target_full * 0.3)

    def test_config_string_representation(self):
        """Should have readable string representation."""
        from services.stress_test_engine import StressTestConfig, TruncationLevel

        config = StressTestConfig(
            temperature=0.7,
            truncation=TruncationLevel.MEDIUM
        )

        assert "0.7" in str(config)
        assert "medium" in str(config)


class TestGetStressTestMatrix:
    """Test the matrix generation function."""

    def test_matrix_has_9_combinations(self):
        """Should generate exactly 9 combinations."""
        from services.stress_test_engine import get_stress_test_matrix

        matrix = get_stress_test_matrix()

        assert len(matrix) == 9

    def test_matrix_covers_all_temperatures(self):
        """Should cover all 3 temperatures."""
        from services.stress_test_engine import get_stress_test_matrix, STRESS_TEMPERATURES

        matrix = get_stress_test_matrix()
        temps = {config.temperature for config in matrix}

        assert temps == set(STRESS_TEMPERATURES)

    def test_matrix_covers_all_truncations(self):
        """Should cover all 3 truncation levels."""
        from services.stress_test_engine import get_stress_test_matrix, TruncationLevel

        matrix = get_stress_test_matrix()
        truncs = {config.truncation for config in matrix}

        assert truncs == set(TruncationLevel)

    def test_matrix_has_unique_run_ids(self):
        """Each config should have unique run_id."""
        from services.stress_test_engine import get_stress_test_matrix

        matrix = get_stress_test_matrix()
        run_ids = [config.run_id for config in matrix]

        assert len(run_ids) == len(set(run_ids))


class TestSimulateStressRun:
    """Test the simulate_stress_run function."""

    def test_function_exists(self):
        """simulate_stress_run should exist."""
        from services.stress_test_engine import simulate_stress_run

        assert callable(simulate_stress_run)

    def test_handles_empty_briefing(self):
        """Should handle empty briefing gracefully."""
        from services.stress_test_engine import simulate_stress_run, TruncationLevel

        result = simulate_stress_run(
            briefing={},
            temperature=0.7,
            truncation_level=TruncationLevel.FULL
        )

        assert result.success is False
        assert "Empty briefing" in result.error_message

    def test_generates_simulated_content(self):
        """Should generate simulated content for valid briefing."""
        from services.stress_test_engine import simulate_stress_run, TruncationLevel

        briefing = {"company": "Test GmbH", "branche": "IT"}

        result = simulate_stress_run(
            briefing=briefing,
            temperature=0.7,
            truncation_level=TruncationLevel.FULL
        )

        assert result.success is True
        assert result.total_words > 0
        assert len(result.sections_generated) > 0

    def test_uses_custom_generator(self):
        """Should use custom generator function if provided."""
        from services.stress_test_engine import simulate_stress_run, TruncationLevel

        def custom_gen(briefing, temp, trunc):
            return {"test_section": "This is test content with multiple words."}

        result = simulate_stress_run(
            briefing={"company": "Test"},
            temperature=0.7,
            truncation_level=TruncationLevel.FULL,
            generator_fn=custom_gen
        )

        assert result.success is True
        assert "test_section" in result.sections_generated


class TestStressTestResult:
    """Test StressTestResult data class."""

    def test_passed_property_true(self):
        """Should return True when no failures."""
        from services.stress_test_engine import (
            StressTestResult,
            StressTestConfig,
            TruncationLevel,
        )

        config = StressTestConfig(temperature=0.7, truncation=TruncationLevel.FULL)
        result = StressTestResult(config=config, success=True)

        assert result.passed is True

    def test_passed_property_false_on_failure(self):
        """Should return False when sections failed."""
        from services.stress_test_engine import (
            StressTestResult,
            StressTestConfig,
            TruncationLevel,
        )

        config = StressTestConfig(temperature=0.7, truncation=TruncationLevel.FULL)
        result = StressTestResult(
            config=config,
            success=True,
            sections_failed=["recommendations"]
        )

        assert result.passed is False


class TestRunStressTestMatrix:
    """Test the full matrix run function."""

    def test_function_exists(self):
        """run_stress_test_matrix should exist."""
        from services.stress_test_engine import run_stress_test_matrix

        assert callable(run_stress_test_matrix)

    def test_runs_all_9_combinations(self):
        """Should run all 9 combinations."""
        from services.stress_test_engine import run_stress_test_matrix

        briefing = {"company": "Test GmbH", "branche": "IT"}

        report = run_stress_test_matrix(briefing)

        assert len(report.results) == 9

    def test_calculates_pass_rate(self):
        """Should calculate overall pass rate."""
        from services.stress_test_engine import run_stress_test_matrix

        briefing = {"company": "Test GmbH", "branche": "IT"}

        report = run_stress_test_matrix(briefing)

        assert 0.0 <= report.overall_pass_rate <= 1.0

    def test_identifies_best_worst_combinations(self):
        """Should identify best and worst combinations."""
        from services.stress_test_engine import run_stress_test_matrix

        briefing = {"company": "Test GmbH", "branche": "IT"}

        report = run_stress_test_matrix(briefing)

        assert report.best_combination is not None
        assert report.worst_combination is not None


class TestValidateStressResult:
    """Test the validation function."""

    def test_function_exists(self):
        """validate_stress_result should exist."""
        from services.stress_test_engine import validate_stress_result

        assert callable(validate_stress_result)

    def test_validates_successful_result(self):
        """Should validate successful result."""
        from services.stress_test_engine import (
            validate_stress_result,
            StressTestResult,
            StressTestConfig,
            TruncationLevel,
        )

        config = StressTestConfig(temperature=0.7, truncation=TruncationLevel.FULL)
        result = StressTestResult(
            config=config,
            success=True,
            total_words=3000,
            sections_generated={"exec": 500, "reco": 800}
        )

        passed, issues = validate_stress_result(result)

        assert passed is True
        assert len(issues) == 0

    def test_detects_failed_run(self):
        """Should detect failed run."""
        from services.stress_test_engine import (
            validate_stress_result,
            StressTestResult,
            StressTestConfig,
            TruncationLevel,
        )

        config = StressTestConfig(temperature=0.7, truncation=TruncationLevel.FULL)
        result = StressTestResult(
            config=config,
            success=False,
            error_message="Test failure"
        )

        passed, issues = validate_stress_result(result)

        assert passed is False
        assert "Test failure" in str(issues)


class TestGetStressTestSummary:
    """Test the summary generation function."""

    def test_function_exists(self):
        """get_stress_test_summary should exist."""
        from services.stress_test_engine import get_stress_test_summary

        assert callable(get_stress_test_summary)

    def test_generates_summary(self):
        """Should generate summary dict."""
        from services.stress_test_engine import (
            get_stress_test_summary,
            run_stress_test_matrix,
        )

        briefing = {"company": "Test GmbH"}
        report = run_stress_test_matrix(briefing)

        summary = get_stress_test_summary(report)

        assert "total_runs" in summary
        assert "pass_rate" in summary
        assert "matrix" in summary
        assert summary["total_runs"] == 9
