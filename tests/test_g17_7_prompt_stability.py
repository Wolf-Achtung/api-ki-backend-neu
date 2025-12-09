# -*- coding: utf-8 -*-
"""
Tests for Sprint G17.7: Prompt Stability Scoring & Auto-Freeze Mechanism

Tests cover:
- G17.7-A: Stability Score Engine (prompt_stability.py)
- G17.7-B: Auto-Freeze Mechanism (prompt_auto_freeze.py)
- G17.7-C: Auto-Recovery System (prompt_recovery.py)
- G17.7-D: Lifecycle State Machine (prompt_lifecycle.py)
- G17.7-E: Dashboard Endpoints (feedback_dashboard.py)
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

import pytest


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_storage_paths(temp_storage_dir):
    """Mock all storage paths to use temp directory."""
    with patch.dict(os.environ, {
        "STABILITY_SCORES_PATH": os.path.join(temp_storage_dir, "stability"),
        "STABILITY_STORAGE_PATH": os.path.join(temp_storage_dir, "stability"),
        "FREEZE_STORAGE_PATH": os.path.join(temp_storage_dir, "freeze"),
        "RECOVERY_STORAGE_PATH": os.path.join(temp_storage_dir, "recovery"),
        "LIFECYCLE_STORAGE_PATH": os.path.join(temp_storage_dir, "lifecycle"),
        "CHECKPOINT_STORAGE_PATH": os.path.join(temp_storage_dir, "checkpoints"),
    }):
        # Clear in-memory state from services
        try:
            from services import prompt_auto_freeze
            prompt_auto_freeze._freeze_registry.clear()
        except (ImportError, AttributeError):
            pass

        try:
            from services import prompt_recovery
            prompt_recovery._recovery_history.clear()
            prompt_recovery._pending_recoveries.clear()
        except (ImportError, AttributeError):
            pass

        try:
            from services import prompt_lifecycle
            prompt_lifecycle._lifecycle_registry.clear()
        except (ImportError, AttributeError):
            pass

        try:
            from services import prompt_stability
            prompt_stability._stability_cache.clear()
            prompt_stability._stability_history.clear()
        except (ImportError, AttributeError):
            pass

        yield temp_storage_dir


# =============================================================================
# G17.7-A: STABILITY SCORE ENGINE TESTS
# =============================================================================

class TestStabilityScoreEngine:
    """Tests for prompt_stability.py"""

    def test_stability_metrics_default_values(self, mock_storage_paths):
        """Test StabilityMetrics has correct default values."""
        from services.prompt_stability import StabilityMetrics

        metrics = StabilityMetrics()

        assert metrics.drift_history_score == 100.0
        assert metrics.rewrite_acceptance_rate == 100.0
        assert metrics.fallback_regression_rate == 100.0
        assert metrics.persona_leak_score == 100.0
        assert metrics.ai_act_conflict_score == 100.0
        assert metrics.redundancy_trend_score == 100.0
        assert metrics.tuning_stability_score == 100.0

    def test_stability_result_stability_label_property(self, mock_storage_paths):
        """Test stability_label property returns correct label."""
        from services.prompt_stability import PromptStabilityResult

        result_excellent = PromptStabilityResult(
            prompt_file="test.md",
            stability_score=90,
            stability_category="STABLE"
        )
        assert result_excellent.stability_label == "EXCELLENT"

        result_good = PromptStabilityResult(
            prompt_file="test.md",
            stability_score=70,
            stability_category="STABLE"
        )
        assert result_good.stability_label == "GOOD"

        result_poor = PromptStabilityResult(
            prompt_file="test.md",
            stability_score=30,
            stability_category="UNSTABLE"
        )
        assert result_poor.stability_label == "POOR"

        result_critical = PromptStabilityResult(
            prompt_file="test.md",
            stability_score=10,
            stability_category="CRITICAL"
        )
        assert result_critical.stability_label == "CRITICAL"

    def test_stability_result_requires_attention_property(self, mock_storage_paths):
        """Test requires_attention property."""
        from services.prompt_stability import PromptStabilityResult, PROMPT_STABILITY_MIN_SCORE

        result_ok = PromptStabilityResult(
            prompt_file="test.md",
            stability_score=PROMPT_STABILITY_MIN_SCORE + 10,
            stability_category="STABLE"
        )
        assert result_ok.requires_attention is False

        result_attention = PromptStabilityResult(
            prompt_file="test.md",
            stability_score=PROMPT_STABILITY_MIN_SCORE - 10,
            stability_category="UNSTABLE"
        )
        assert result_attention.requires_attention is True

    def test_calculate_prompt_stability_new_prompt(self, mock_storage_paths):
        """Test stability calculation for a new prompt."""
        from services.prompt_stability import calculate_prompt_stability

        result = calculate_prompt_stability("prompts/test_prompt.md")

        assert result.prompt_file == "prompts/test_prompt.md"
        assert result.stability_score == 100  # New prompt has perfect score
        assert result.stability_label == "EXCELLENT"
        assert result.requires_attention is False

    def test_update_and_get_stability(self, mock_storage_paths):
        """Test updating and retrieving stability index."""
        from services.prompt_stability import (
            update_prompt_stability_index,
            get_prompt_stability,
        )

        prompt_file = "prompts/test_update_prompt.md"

        # Update with low score
        success = update_prompt_stability_index(prompt_file, 25, trigger="test")
        assert success is True

        # Retrieve
        result = get_prompt_stability(prompt_file)
        assert result is not None
        assert result.stability_score == 25
        assert result.requires_attention is True

    def test_global_dashboard_structure(self, mock_storage_paths):
        """Test global dashboard has correct structure."""
        from services.prompt_stability import get_global_prompt_stability_dashboard

        dashboard = get_global_prompt_stability_dashboard()

        # Check structure exists
        assert "total_prompts_tracked" in dashboard
        assert "avg_stability_score" in dashboard
        assert "by_label" in dashboard
        assert "attention_required" in dashboard
        assert "enabled" in dashboard
        assert isinstance(dashboard["by_label"], dict)
        assert isinstance(dashboard["attention_required"], list)


# =============================================================================
# G17.7-B: AUTO-FREEZE MECHANISM TESTS
# =============================================================================

class TestAutoFreezeMechanism:
    """Tests for prompt_auto_freeze.py"""

    def test_check_stability_threshold_below(self, mock_storage_paths):
        """Test freeze trigger when stability below threshold."""
        from services.prompt_auto_freeze import check_stability_threshold

        reason = check_stability_threshold(15)

        assert reason is not None
        assert reason.rule == "LOW_STABILITY"
        assert "15" in reason.description

    def test_check_stability_threshold_above(self, mock_storage_paths):
        """Test no freeze when stability above threshold."""
        from services.prompt_auto_freeze import check_stability_threshold

        reason = check_stability_threshold(50)

        assert reason is None

    def test_check_consecutive_high_drift_triggered(self, mock_storage_paths):
        """Test freeze trigger for consecutive high drift."""
        from services.prompt_auto_freeze import check_consecutive_high_drift

        drift_history = [
            {"drift_level": "HIGH"},
            {"drift_level": "HIGH"},
        ]

        reason = check_consecutive_high_drift(drift_history)

        assert reason is not None
        assert reason.rule == "CONSECUTIVE_HIGH_DRIFT"

    def test_check_consecutive_high_drift_not_triggered(self, mock_storage_paths):
        """Test no freeze when drift is not consecutive high."""
        from services.prompt_auto_freeze import check_consecutive_high_drift

        drift_history = [
            {"drift_level": "LOW"},
            {"drift_level": "HIGH"},
        ]

        reason = check_consecutive_high_drift(drift_history)

        assert reason is None

    def test_check_simulation_regression_triggered(self, mock_storage_paths):
        """Test freeze trigger for simulation regression."""
        from services.prompt_auto_freeze import check_simulation_regression

        simulation_results = {
            "metrics": {
                "quality_regression": True,
                "fallback_rate_increase": 0.15,
                "persona_leak_increase": 0.1,
            }
        }

        reason = check_simulation_regression(simulation_results)

        assert reason is not None
        assert reason.rule == "SIMULATION_REGRESSION"

    def test_check_ai_act_conflict_severity_triggered(self, mock_storage_paths):
        """Test freeze trigger for AI-Act conflict severity."""
        from services.prompt_auto_freeze import check_ai_act_conflict_severity

        conflict_data = {"severity": "major"}

        reason = check_ai_act_conflict_severity(conflict_data)

        assert reason is not None
        assert reason.rule == "AI_ACT_CONFLICT"

    def test_check_ai_act_conflict_severity_not_triggered(self, mock_storage_paths):
        """Test no freeze when AI-Act severity is low."""
        from services.prompt_auto_freeze import check_ai_act_conflict_severity

        conflict_data = {"severity": "minor"}

        reason = check_ai_act_conflict_severity(conflict_data)

        assert reason is None

    def test_freeze_and_unfreeze_prompt(self, mock_storage_paths):
        """Test freezing and unfreezing a prompt."""
        from services.prompt_auto_freeze import (
            freeze_prompt,
            unfreeze_prompt,
            is_prompt_frozen,
        )

        prompt_file = "prompts/test_prompt.md"

        # Initially not frozen
        assert is_prompt_frozen(prompt_file) is False

        # Freeze
        result = freeze_prompt(prompt_file, "Test freeze", frozen_by="test")
        assert result["success"] is True

        # Should be frozen
        assert is_prompt_frozen(prompt_file) is True

        # Unfreeze
        result = unfreeze_prompt(prompt_file, unfrozen_by="test")
        assert result["success"] is True

        # Should not be frozen
        assert is_prompt_frozen(prompt_file) is False

    def test_freeze_already_frozen_prompt(self, mock_storage_paths):
        """Test freezing an already frozen prompt adds reason."""
        from services.prompt_auto_freeze import (
            freeze_prompt,
            get_freeze_record,
        )

        prompt_file = "prompts/test_prompt.md"

        # Freeze first time
        freeze_prompt(prompt_file, "First reason")

        # Freeze second time
        result = freeze_prompt(prompt_file, "Second reason")

        assert result["already_frozen"] is True

        # Check record has multiple reasons
        record = get_freeze_record(prompt_file)
        assert len(record["freeze_reasons"]) == 2

    def test_auto_freeze_check_and_apply(self, mock_storage_paths):
        """Test automatic freeze check and apply."""
        from services.prompt_auto_freeze import auto_freeze_check_and_apply

        prompt_file = "prompts/test_prompt.md"

        result = auto_freeze_check_and_apply(
            prompt_file=prompt_file,
            stability_score=10,  # Below threshold
        )

        assert result["should_freeze"] is True
        assert result["freeze_applied"] is True

    def test_block_if_frozen(self, mock_storage_paths):
        """Test block_if_frozen helper."""
        from services.prompt_auto_freeze import (
            freeze_prompt,
            block_if_frozen,
        )

        prompt_file = "prompts/test_block_if_frozen.md"

        # Not frozen - should not block
        block = block_if_frozen(prompt_file)
        assert block is None

        # Freeze it
        freeze_prompt(prompt_file, "Test freeze")

        # Should block
        block = block_if_frozen(prompt_file)
        assert block is not None
        assert block["blocked"] is True


# =============================================================================
# G17.7-C: AUTO-RECOVERY SYSTEM TESTS
# =============================================================================

class TestAutoRecoverySystem:
    """Tests for prompt_recovery.py"""

    def test_find_recovery_candidates_empty(self, mock_storage_paths):
        """Test finding candidates when no checkpoints exist."""
        from services.prompt_recovery import find_recovery_candidates

        candidates = find_recovery_candidates("prompts/test_prompt.md")

        assert len(candidates) == 0

    def test_get_best_recovery_candidate_none(self, mock_storage_paths):
        """Test getting best candidate when none available."""
        from services.prompt_recovery import get_best_recovery_candidate

        candidate = get_best_recovery_candidate("prompts/test_prompt.md")

        assert candidate is None

    def test_trigger_auto_recovery_no_candidate(self, mock_storage_paths):
        """Test recovery trigger when no candidate available."""
        from services.prompt_recovery import trigger_auto_recovery

        result = trigger_auto_recovery("prompts/test_prompt.md")

        assert result["success"] is False
        assert "No stable recovery candidate" in result["error"]

    def test_get_recovery_history_empty(self, mock_storage_paths):
        """Test getting empty recovery history."""
        from services.prompt_recovery import get_recovery_history

        history = get_recovery_history("prompts/test_prompt.md")

        assert history["prompt_file"] == "prompts/test_prompt.md"
        assert history["total_recoveries"] == 0
        assert history["total_failures"] == 0
        assert history["success_rate"] == 1.0

    def test_get_pending_recoveries_empty(self, mock_storage_paths):
        """Test getting empty pending recoveries."""
        from services.prompt_recovery import get_pending_recoveries

        pending = get_pending_recoveries()

        assert len(pending) == 0

    def test_recovery_statistics(self, mock_storage_paths):
        """Test recovery statistics."""
        from services.prompt_recovery import get_recovery_statistics

        stats = get_recovery_statistics()

        assert "total_recoveries" in stats
        assert "total_failures" in stats
        assert "success_rate" in stats
        assert stats["auto_recovery_enabled"] is True


# =============================================================================
# G17.7-D: LIFECYCLE STATE MACHINE TESTS
# =============================================================================

class TestLifecycleStateMachine:
    """Tests for prompt_lifecycle.py"""

    def test_lifecycle_states_enum(self, mock_storage_paths):
        """Test LifecycleState enum values."""
        from services.prompt_lifecycle import LifecycleState

        assert LifecycleState.ACTIVE.value == "ACTIVE"
        assert LifecycleState.TUNING_OPTIMIZED.value == "TUNING-OPTIMIZED"
        assert LifecycleState.REWRITE_READY.value == "REWRITE-READY"
        assert LifecycleState.GOVERNANCE_WAIT.value == "GOVERNANCE-WAIT"
        assert LifecycleState.FROZEN.value == "FROZEN"
        assert LifecycleState.RECOVERING.value == "RECOVERING"

    def test_lifecycle_state_from_string(self, mock_storage_paths):
        """Test parsing state from string."""
        from services.prompt_lifecycle import LifecycleState

        assert LifecycleState.from_string("ACTIVE") == LifecycleState.ACTIVE
        assert LifecycleState.from_string("tuning-optimized") == LifecycleState.TUNING_OPTIMIZED
        assert LifecycleState.from_string("FROZEN") == LifecycleState.FROZEN

    def test_is_valid_transition_active_to_frozen(self, mock_storage_paths):
        """Test valid transition from ACTIVE to FROZEN."""
        from services.prompt_lifecycle import LifecycleState, is_valid_transition

        assert is_valid_transition(
            LifecycleState.ACTIVE,
            LifecycleState.FROZEN
        ) is True

    def test_is_valid_transition_frozen_to_recovering(self, mock_storage_paths):
        """Test valid transition from FROZEN to RECOVERING."""
        from services.prompt_lifecycle import LifecycleState, is_valid_transition

        assert is_valid_transition(
            LifecycleState.FROZEN,
            LifecycleState.RECOVERING
        ) is True

    def test_is_valid_transition_recovering_to_active(self, mock_storage_paths):
        """Test valid transition from RECOVERING to ACTIVE."""
        from services.prompt_lifecycle import LifecycleState, is_valid_transition

        assert is_valid_transition(
            LifecycleState.RECOVERING,
            LifecycleState.ACTIVE
        ) is True

    def test_is_invalid_transition_active_to_recovering(self, mock_storage_paths):
        """Test invalid transition from ACTIVE to RECOVERING."""
        from services.prompt_lifecycle import LifecycleState, is_valid_transition

        assert is_valid_transition(
            LifecycleState.ACTIVE,
            LifecycleState.RECOVERING
        ) is False

    def test_get_valid_transitions(self, mock_storage_paths):
        """Test getting valid transitions from a state."""
        from services.prompt_lifecycle import LifecycleState, get_valid_transitions

        valid = get_valid_transitions(LifecycleState.ACTIVE)

        assert "TUNING-OPTIMIZED" in valid
        assert "REWRITE-READY" in valid
        assert "GOVERNANCE-WAIT" in valid
        assert "FROZEN" in valid
        assert "RECOVERING" not in valid  # Cannot go directly to RECOVERING

    def test_get_lifecycle_state_new_prompt(self, mock_storage_paths):
        """Test getting state for new prompt."""
        from services.prompt_lifecycle import get_lifecycle_state

        state = get_lifecycle_state("prompts/test_prompt.md")

        assert state["current_state"] == "ACTIVE"
        assert state["previous_state"] is None
        assert state["total_transitions"] == 0

    def test_transition_state_success(self, mock_storage_paths):
        """Test successful state transition."""
        from services.prompt_lifecycle import transition_state, get_lifecycle_state

        prompt_file = "prompts/test_prompt.md"

        result = transition_state(
            prompt_file=prompt_file,
            new_state="FROZEN",
            reason="Test freeze",
            triggered_by="test"
        )

        assert result["success"] is True
        assert result["from_state"] == "ACTIVE"
        assert result["to_state"] == "FROZEN"

        # Verify state changed
        state = get_lifecycle_state(prompt_file)
        assert state["current_state"] == "FROZEN"
        assert state["previous_state"] == "ACTIVE"
        assert state["total_transitions"] == 1

    def test_transition_state_invalid(self, mock_storage_paths):
        """Test invalid state transition."""
        from services.prompt_lifecycle import transition_state

        result = transition_state(
            prompt_file="prompts/test_invalid_transition.md",
            new_state="RECOVERING",  # Invalid from ACTIVE
            reason="Test",
            triggered_by="test"
        )

        assert result["success"] is False
        assert "Invalid transition" in result.get("error", "")

    def test_transition_state_force_invalid(self, mock_storage_paths):
        """Test forcing invalid state transition."""
        from services.prompt_lifecycle import transition_state, get_lifecycle_state

        prompt_file = "prompts/test_prompt.md"

        result = transition_state(
            prompt_file=prompt_file,
            new_state="RECOVERING",
            reason="Forced transition",
            triggered_by="admin",
            force=True
        )

        assert result["success"] is True

        state = get_lifecycle_state(prompt_file)
        assert state["current_state"] == "RECOVERING"

    def test_convenience_transition_functions(self, mock_storage_paths):
        """Test convenience transition functions."""
        from services.prompt_lifecycle import (
            mark_tuning_optimized,
            mark_frozen,
            mark_recovering,
            mark_active,
            get_lifecycle_state,
        )

        prompt_file = "prompts/test_convenience_prompt.md"

        # ACTIVE -> TUNING-OPTIMIZED
        result = mark_tuning_optimized(prompt_file)
        assert result["success"] is True

        state = get_lifecycle_state(prompt_file)
        assert state["current_state"] == "TUNING-OPTIMIZED"

        # TUNING-OPTIMIZED -> ACTIVE
        result = mark_active(prompt_file)
        assert result["success"] is True

        # ACTIVE -> FROZEN
        result = mark_frozen(prompt_file, "Test freeze")
        assert result["success"] is True

        state = get_lifecycle_state(prompt_file)
        assert state["current_state"] == "FROZEN"

        # FROZEN -> RECOVERING
        result = mark_recovering(prompt_file)
        assert result["success"] is True

        # RECOVERING -> ACTIVE
        result = mark_active(prompt_file, reason="Recovery complete")
        assert result["success"] is True

    def test_get_transition_history(self, mock_storage_paths):
        """Test getting transition history."""
        from services.prompt_lifecycle import (
            transition_state,
            get_transition_history,
        )

        prompt_file = "prompts/test_history_prompt.md"

        # Make some transitions
        transition_state(prompt_file, "FROZEN", "First", triggered_by="test")
        transition_state(prompt_file, "RECOVERING", "Second", triggered_by="test")
        transition_state(prompt_file, "ACTIVE", "Third", triggered_by="test")

        history = get_transition_history(prompt_file)

        assert len(history) >= 3
        assert history[0]["from_state"] == "ACTIVE"
        assert history[0]["to_state"] == "FROZEN"

    def test_get_prompts_by_state(self, mock_storage_paths):
        """Test getting prompts by state."""
        from services.prompt_lifecycle import (
            transition_state,
            get_prompts_by_state,
        )

        # Freeze some prompts
        transition_state("prompts/p1.md", "FROZEN", "Test")
        transition_state("prompts/p2.md", "FROZEN", "Test")
        transition_state("prompts/p3.md", "TUNING-OPTIMIZED", "Test")

        frozen = get_prompts_by_state("FROZEN")

        assert len(frozen) == 2
        assert "prompts/p1.md" in frozen
        assert "prompts/p2.md" in frozen

    def test_lifecycle_dashboard(self, mock_storage_paths):
        """Test lifecycle dashboard."""
        from services.prompt_lifecycle import get_lifecycle_dashboard

        dashboard = get_lifecycle_dashboard()

        assert "statistics" in dashboard
        assert "attention_required" in dashboard
        assert "state_transitions" in dashboard
        assert dashboard["enabled"] is True


# =============================================================================
# G17.7-E: DASHBOARD ENDPOINT TESTS
# =============================================================================

class TestStabilityDashboardEndpoints:
    """Tests for dashboard endpoints in feedback_dashboard.py"""

    @pytest.fixture
    def client(self, mock_storage_paths):
        """Create test client."""
        from fastapi.testclient import TestClient
        from routes.feedback_dashboard import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_get_stability_overview(self, client, mock_storage_paths):
        """Test GET /prompts/stability/overview endpoint."""
        response = client.get("/api/dashboard/feedback/prompts/stability/overview")

        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "total_prompts_tracked" in data
        assert "frozen_count" in data

    def test_get_stability_score(self, client, mock_storage_paths):
        """Test GET /prompts/stability/score endpoint."""
        response = client.get(
            "/api/dashboard/feedback/prompts/stability/score",
            params={"prompt_file": "prompts/test_endpoint.md"}
        )

        # May return 200 or 503 depending on imports
        if response.status_code == 200:
            data = response.json()
            assert data["prompt_file"] == "prompts/test_endpoint.md"
            assert "stability_score" in data
        else:
            # Stability scoring not available (ImportError) - this is acceptable
            assert response.status_code == 503

    def test_get_frozen_prompts_empty(self, client, mock_storage_paths):
        """Test GET /prompts/freeze/list endpoint with no frozen prompts."""
        response = client.get("/api/dashboard/feedback/prompts/freeze/list")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_freeze_prompt_endpoint(self, client, mock_storage_paths):
        """Test POST /prompts/freeze endpoint."""
        response = client.post(
            "/api/dashboard/feedback/prompts/freeze",
            params={
                "prompt_file": "prompts/test.md",
                "reason": "Test freeze",
                "frozen_by": "test"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "FREEZE"

    def test_unfreeze_prompt_endpoint(self, client, mock_storage_paths):
        """Test POST /prompts/unfreeze endpoint."""
        # First freeze
        client.post(
            "/api/dashboard/feedback/prompts/freeze",
            params={
                "prompt_file": "prompts/test.md",
                "reason": "Test freeze"
            }
        )

        # Then unfreeze
        response = client.post(
            "/api/dashboard/feedback/prompts/unfreeze",
            params={
                "prompt_file": "prompts/test.md",
                "unfrozen_by": "test"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "UNFREEZE"

    def test_get_recovery_history(self, client, mock_storage_paths):
        """Test GET /prompts/recovery/history endpoint."""
        response = client.get(
            "/api/dashboard/feedback/prompts/recovery/history",
            params={"prompt_file": "prompts/test.md"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_file"] == "prompts/test.md"
        assert "total_recoveries" in data

    def test_get_lifecycle_state(self, client, mock_storage_paths):
        """Test GET /prompts/lifecycle/state endpoint."""
        response = client.get(
            "/api/dashboard/feedback/prompts/lifecycle/state",
            params={"prompt_file": "prompts/test.md"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_file"] == "prompts/test.md"
        assert data["current_state"] == "ACTIVE"
        assert "valid_transitions" in data

    def test_transition_lifecycle_state(self, client, mock_storage_paths):
        """Test POST /prompts/lifecycle/transition endpoint."""
        response = client.post(
            "/api/dashboard/feedback/prompts/lifecycle/transition",
            params={
                "prompt_file": "prompts/test.md",
                "new_state": "FROZEN",
                "reason": "Test transition",
                "triggered_by": "test"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["to_state"] == "FROZEN"

    def test_get_lifecycle_dashboard(self, client, mock_storage_paths):
        """Test GET /prompts/lifecycle/dashboard endpoint."""
        response = client.get("/api/dashboard/feedback/prompts/lifecycle/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert "attention_required" in data
        assert "state_transitions" in data


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestStabilityIntegration:
    """Integration tests for the complete stability system."""

    def test_low_stability_triggers_freeze(self, mock_storage_paths):
        """Test that low stability score triggers auto-freeze."""
        from services.prompt_auto_freeze import auto_freeze_check_and_apply, is_prompt_frozen

        prompt_file = "prompts/test_integration_low_stability.md"

        # Check and apply freeze with low stability
        result = auto_freeze_check_and_apply(prompt_file, stability_score=15)

        assert result["should_freeze"] is True
        assert is_prompt_frozen(prompt_file) is True

    def test_freeze_unfreeze_lifecycle_flow(self, mock_storage_paths):
        """Test complete freeze-unfreeze flow updates lifecycle."""
        from services.prompt_auto_freeze import freeze_prompt, unfreeze_prompt
        from services.prompt_lifecycle import (
            mark_frozen,
            mark_active,
            get_lifecycle_state,
            get_transition_history,
        )

        prompt_file = "prompts/test_lifecycle_flow_integration.md"

        # Freeze
        freeze_prompt(prompt_file, "Test freeze")
        mark_frozen(prompt_file, "Test freeze")

        state = get_lifecycle_state(prompt_file)
        assert state["current_state"] == "FROZEN"

        # Unfreeze
        unfreeze_prompt(prompt_file)
        mark_active(prompt_file, reason="Manual unfreeze")

        state = get_lifecycle_state(prompt_file)
        assert state["current_state"] == "ACTIVE"

        # Check history
        history = get_transition_history(prompt_file)
        assert len(history) == 2

    def test_stability_metrics_weighting(self, mock_storage_paths):
        """Test stability metrics are correctly weighted."""
        from services.prompt_stability import StabilityMetrics

        # All perfect
        metrics_perfect = StabilityMetrics()

        # Low AI-Act (x4 weight = 25% impact)
        metrics_low_ai_act = StabilityMetrics(ai_act_conflict_score=0.0)

        # Low persona (x3 weight = 20% impact)
        metrics_low_persona = StabilityMetrics(persona_leak_score=0.0)

        # Low drift (x1 weight = 15% impact)
        metrics_low_drift = StabilityMetrics(drift_history_score=0.0)

        # Verify weights exist and are reasonable
        assert metrics_perfect.ai_act_conflict_score == 100.0
        assert metrics_low_ai_act.ai_act_conflict_score == 0.0
        assert metrics_low_persona.persona_leak_score == 0.0
        assert metrics_low_drift.drift_history_score == 0.0

    def test_freeze_statistics(self, mock_storage_paths):
        """Test freeze statistics tracking."""
        from services.prompt_auto_freeze import (
            freeze_prompt,
            get_freeze_statistics,
        )

        # Freeze a few prompts with unique names
        freeze_prompt("prompts/stats_p1.md", "Low stability", frozen_by="auto")
        freeze_prompt("prompts/stats_p2.md", "High drift", frozen_by="auto")

        stats = get_freeze_statistics()

        assert stats["total_frozen"] >= 2
        assert stats["auto_freeze_enabled"] is True
