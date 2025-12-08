# -*- coding: utf-8 -*-
"""
Sprint G15: Release R1 / Launch-Mode Tests
==========================================

Test coverage for:
- G15-A: Release configuration and ENV validation
- G15-B: E2E check script functionality
- G15-C: Release health endpoint
- G15-D: Documentation existence

Version: 1.0.0 (Release R1)
"""

import pytest
import os
from pathlib import Path


# =============================================================================
# G15-A: Release Configuration Tests
# =============================================================================

class TestG15A_ReleaseConfig:
    """Tests for release configuration module."""

    def test_config_release_imports(self):
        """Test that config_release module can be imported."""
        from services.config_release import (
            ReleaseConfig,
            REQUIRED_ENV_VARS,
            RECOMMENDED_ENV_VARS,
            FEATURE_FLAGS,
            RELEASE_HEALTH_THRESHOLDS,
        )
        assert ReleaseConfig is not None
        assert isinstance(REQUIRED_ENV_VARS, list)
        assert isinstance(RECOMMENDED_ENV_VARS, list)
        assert isinstance(FEATURE_FLAGS, dict)
        assert isinstance(RELEASE_HEALTH_THRESHOLDS, dict)

    def test_release_config_defaults(self):
        """Test ReleaseConfig has expected defaults."""
        from services.config_release import ReleaseConfig

        config = ReleaseConfig()

        # Check critical defaults
        assert config.AI_ACT_ENABLED is True
        assert config.RATE_LIMIT_ENABLED is True
        assert config.LLM_SHORT_RETRY_ENABLED is True
        assert config.PPLX_FAILURE_THRESHOLD == 2
        assert config.LLM_MAX_RETRIES == 2

    def test_required_env_vars_defined(self):
        """Test required ENV vars are defined."""
        from services.config_release import REQUIRED_ENV_VARS

        # These should be required
        assert "DATABASE_URL" in REQUIRED_ENV_VARS
        assert "JWT_SECRET" in REQUIRED_ENV_VARS
        assert "OPENAI_API_KEY" in REQUIRED_ENV_VARS
        assert "PDF_SERVICE_URL" in REQUIRED_ENV_VARS

    def test_feature_flags_have_sprint_info(self):
        """Test feature flags include sprint information."""
        from services.config_release import FEATURE_FLAGS

        for flag, info in FEATURE_FLAGS.items():
            assert "sprint" in info, f"Flag {flag} missing sprint info"
            assert "description" in info, f"Flag {flag} missing description"
            assert "production_default" in info, f"Flag {flag} missing production_default"

    def test_health_thresholds_have_warn_and_critical(self):
        """Test health thresholds have both levels."""
        from services.config_release import RELEASE_HEALTH_THRESHOLDS

        for metric, thresholds in RELEASE_HEALTH_THRESHOLDS.items():
            assert "warn" in thresholds, f"Metric {metric} missing warn threshold"
            assert "critical" in thresholds, f"Metric {metric} missing critical threshold"
            assert thresholds["warn"] < thresholds["critical"], \
                f"Metric {metric}: warn should be less than critical"

    def test_get_env_validation_summary(self):
        """Test ENV validation summary function."""
        from services.config_release import get_env_validation_summary

        summary = get_env_validation_summary()

        assert "missing_required" in summary
        assert "missing_recommended" in summary
        assert "invalid_values" in summary
        assert isinstance(summary["missing_required"], list)

    def test_get_current_feature_status(self):
        """Test feature status retrieval."""
        from services.config_release import get_current_feature_status

        status = get_current_feature_status()

        assert isinstance(status, dict)
        # Should return boolean values
        for flag, value in status.items():
            assert isinstance(value, bool), f"Flag {flag} should be boolean"


class TestG15A_ConfigValidation:
    """Tests for config_validation module extensions."""

    def test_release_validation_result_class(self):
        """Test ReleaseValidationResult class."""
        from services.config_validation import ReleaseValidationResult

        result = ReleaseValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

        result.add_error("Test error")
        assert result.is_valid is False
        assert len(result.errors) == 1

        result.add_warning("Test warning")
        assert len(result.warnings) == 1

    def test_validate_release_config_function(self):
        """Test validate_release_config function."""
        from services.config_validation import validate_release_config

        result = validate_release_config()

        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "to_dict")

    def test_validate_release_config_returns_dict(self):
        """Test validate_release_config.to_dict() returns expected structure."""
        from services.config_validation import validate_release_config

        result = validate_release_config()
        d = result.to_dict()

        assert "is_valid" in d
        assert "errors" in d
        assert "warnings" in d
        assert "error_count" in d
        assert "warning_count" in d


# =============================================================================
# G15-B: E2E Check Script Tests
# =============================================================================

class TestG15B_E2ECheckScript:
    """Tests for E2E release check script."""

    def test_e2e_script_exists(self):
        """Test E2E script file exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "run_release_e2e_check.py"
        assert script_path.exists(), f"E2E script not found at {script_path}"

    def test_e2e_script_imports(self):
        """Test E2E script can be imported."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        # Import the module components
        from run_release_e2e_check import (
            ProfileTestResult,
            E2ETestSuite,
            GOLD_PROFILES,
            get_mock_response,
            validate_profile,
        )

        assert ProfileTestResult is not None
        assert E2ETestSuite is not None
        assert len(GOLD_PROFILES) >= 3  # At least 3 gold profiles

    def test_gold_profiles_defined(self):
        """Test gold profiles are properly defined."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        from run_release_e2e_check import GOLD_PROFILES

        for profile in GOLD_PROFILES:
            assert "path" in profile
            assert "id" in profile
            assert "criteria" in profile

    def test_mock_responses_available(self):
        """Test mock responses are available for all gold profiles."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        from run_release_e2e_check import GOLD_PROFILES, get_mock_response

        for profile in GOLD_PROFILES:
            mock = get_mock_response(profile["id"])
            assert mock, f"No mock response for {profile['id']}"
            assert "ai_act" in mock or "error" not in mock

    def test_profile_test_result_methods(self):
        """Test ProfileTestResult methods work correctly."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        from run_release_e2e_check import ProfileTestResult

        result = ProfileTestResult(profile_id="test")
        assert result.status == "pending"

        result.add_pass("Test passed")
        assert result.checks_passed == 1

        result.add_warn("Test warning")
        assert result.checks_warned == 1

        result.finalize()
        assert result.status == "WARN"  # Has warnings

    def test_e2e_suite_tracks_results(self):
        """Test E2ETestSuite tracks results correctly."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        from run_release_e2e_check import ProfileTestResult, E2ETestSuite

        suite = E2ETestSuite()
        assert suite.profiles_tested == 0

        result1 = ProfileTestResult(profile_id="test1")
        result1.status = "OK"
        suite.add_result(result1)

        result2 = ProfileTestResult(profile_id="test2")
        result2.status = "WARN"
        suite.add_result(result2)

        assert suite.profiles_tested == 2
        assert suite.profiles_ok == 1
        assert suite.profiles_warn == 1
        assert suite.overall_status == "WARN"


# =============================================================================
# G15-C: Dashboard Release Health Tests
# =============================================================================

class TestG15C_DashboardEndpoints:
    """Tests for dashboard release health endpoints."""

    def test_dashboard_module_imports(self):
        """Test dashboard module can be imported."""
        pytest.importorskip("fastapi", reason="fastapi required for dashboard tests")
        from routes.dashboard import router
        assert router is not None

    def test_release_health_thresholds_used(self):
        """Test that release health uses config thresholds."""
        from services.config_release import RELEASE_HEALTH_THRESHOLDS

        # Check expected metrics have thresholds
        assert "fallback_rate_pct" in RELEASE_HEALTH_THRESHOLDS
        assert "pdf_error_rate_pct" in RELEASE_HEALTH_THRESHOLDS
        assert "ai_act_high_risk_share_pct" in RELEASE_HEALTH_THRESHOLDS


# =============================================================================
# G15-D: Documentation Tests
# =============================================================================

class TestG15D_Documentation:
    """Tests for documentation existence."""

    def test_operator_guide_exists(self):
        """Test OPERATOR_GUIDE.md exists."""
        doc_path = Path(__file__).parent.parent / "docs" / "OPERATOR_GUIDE.md"
        assert doc_path.exists(), f"Operator guide not found at {doc_path}"

    def test_operator_guide_content(self):
        """Test operator guide has expected sections."""
        doc_path = Path(__file__).parent.parent / "docs" / "OPERATOR_GUIDE.md"

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for expected sections
        assert "Quick Start" in content
        assert "Environment Configuration" in content
        assert "Health Monitoring" in content
        assert "Troubleshooting" in content

    def test_readme_exists(self):
        """Test README.md exists."""
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), f"README not found at {readme_path}"

    def test_readme_has_release_section(self):
        """Test README has Release R1 section."""
        readme_path = Path(__file__).parent.parent / "README.md"

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Release R1" in content
        assert "E2E" in content or "e2e" in content.lower()

    def test_env_example_exists(self):
        """Test .env.example exists."""
        env_path = Path(__file__).parent.parent / ".env.example"
        assert env_path.exists(), f".env.example not found at {env_path}"

    def test_env_example_has_g15_section(self):
        """Test .env.example has G15 section."""
        env_path = Path(__file__).parent.parent / ".env.example"

        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "G15" in content or "RELEASE" in content


# =============================================================================
# G15-E: Integration Tests
# =============================================================================

class TestG15E_Integration:
    """Integration tests for Release R1."""

    def test_all_g15_modules_import(self):
        """Test all G15-modified modules can be imported together."""
        from services.config_release import ReleaseConfig
        from services.config_validation import validate_release_config

        # Dashboard requires fastapi
        fastapi = pytest.importorskip("fastapi", reason="fastapi required")
        from routes.dashboard import router

        assert True  # All imports successful

    def test_gold_profile_files_exist(self):
        """Test gold profile JSON files exist."""
        profiles_dir = Path(__file__).parent.parent / "data" / "test_profiles_gold"

        expected_profiles = [
            "solo_beratung_ki_assessments.json",
            "team_finance_insurance_advisory.json",
            "kmu_france_eu_core_en_gold.json",
        ]

        for profile_name in expected_profiles:
            profile_path = profiles_dir / profile_name
            assert profile_path.exists(), f"Gold profile not found: {profile_name}"

    def test_release_validation_runs(self):
        """Test release validation can be executed."""
        from services.config_validation import validate_release_config

        result = validate_release_config()

        # Should at least return a result
        assert result is not None
        # In test environment, some vars will be missing - that's OK
        assert isinstance(result.is_valid, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
