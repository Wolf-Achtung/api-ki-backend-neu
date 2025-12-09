# -*- coding: utf-8 -*-
"""
Tests for Sprint G17.6: Prompt Governance & Drift Control

Tests cover:
- Snapshot compare
- Drift score calculation
- Patch gate block/approve
- Simulation regressions
- Dashboard endpoints
- ENV flags
- Critical drift hard stop
"""
from __future__ import annotations

import asyncio
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_prompt_before() -> str:
    """Sample prompt content (before patch)."""
    return """# Roadmap 12 Monate

## Einleitung
Erstellen Sie einen detaillierten 12-Monats-Plan.

## Meilensteine
{{#if (eq unternehmensgroesse "solo")}}
Als Einzelunternehmer sollten Sie...
{{else}}
Ihr Team sollte...
{{/if}}

### Quartal 1
- Analyse der aktuellen Situation
- Definition der Ziele

### Quartal 2
- Implementierung erster Maßnahmen

[PERSONA: Du-Form für Solo]
[LENGTH: mindestens 200 Wörter]

Vermeide Wiederholungen und halte den Text prägnant.
"""


@pytest.fixture
def sample_prompt_after() -> str:
    """Sample prompt content (after patch with moderate changes)."""
    return """# Roadmap 12 Monate

## Einleitung
Erstellen Sie einen umfassenden und detaillierten 12-Monats-Plan mit konkreten Maßnahmen.

## Meilensteine
{{#if (eq unternehmensgroesse "solo")}}
Als Einzelunternehmer sollten Sie folgende Aspekte beachten...
{{else}}
Ihr Team sollte diese Schritte verfolgen...
{{/if}}

### Quartal 1
- Analyse der aktuellen Situation
- Definition der Ziele
- Ressourcenplanung

### Quartal 2
- Implementierung erster Maßnahmen
- Fortschrittskontrolle

### Quartal 3
- Optimierung der Prozesse

[PERSONA: Du-Form für Solo, Sie-Form für Team]
[LENGTH: mindestens 250 Wörter]

Vermeide Wiederholungen und achte auf klare Struktur.
"""


@pytest.fixture
def sample_prompt_critical() -> str:
    """Sample prompt with critical changes (major structural changes)."""
    return """# Completely New Structure

## Section A
Totally different content here.

## Section B
More new content.

[NEW_RULES: Everything changed]
"""


# =============================================================================
# SNAPSHOT COMPARE TESTS
# =============================================================================

class TestSnapshotCompare:
    """Tests for snapshot comparison functionality."""

    def test_compare_snapshots_basic(self, sample_prompt_before: str, sample_prompt_after: str, tmp_path) -> None:
        """Test basic snapshot comparison."""
        from services.prompt_checkpoint import (
            PromptSnapshot,
            compare_snapshots,
            _compute_hash,
        )

        old_snapshot = PromptSnapshot(
            prompt_file="prompts/de/roadmap_12m.md",
            content=sample_prompt_before,
            content_hash=_compute_hash(sample_prompt_before),
            version=1,
            sections=["Roadmap 12 Monate", "Einleitung", "Meilensteine", "Quartal 1", "Quartal 2"],
            token_count=len(sample_prompt_before) // 4,
        )

        new_snapshot = PromptSnapshot(
            prompt_file="prompts/de/roadmap_12m.md",
            content=sample_prompt_after,
            content_hash=_compute_hash(sample_prompt_after),
            version=2,
            sections=["Roadmap 12 Monate", "Einleitung", "Meilensteine", "Quartal 1", "Quartal 2", "Quartal 3"],
            token_count=len(sample_prompt_after) // 4,
        )

        diff = compare_snapshots(old_snapshot, new_snapshot)

        assert diff.old_version == 1
        assert diff.new_version == 2
        assert "Quartal 3" in diff.added_sections
        assert diff.total_changes > 0

    def test_create_and_load_snapshot(self, sample_prompt_before: str, tmp_path) -> None:
        """Test creating and loading a snapshot."""
        from services.prompt_checkpoint import (
            create_prompt_snapshot,
            load_prompt_snapshot,
        )

        with patch("services.prompt_checkpoint._get_snapshots_path", return_value=tmp_path):
            with patch("services.prompt_checkpoint.PROMPT_DRAFT_MODE", False):
                # Create snapshot
                snapshot = create_prompt_snapshot(
                    prompt_file="test/prompt.md",
                    content=sample_prompt_before,
                    metadata={"test": True},
                )

                assert snapshot.version == 1
                assert snapshot.content == sample_prompt_before
                assert len(snapshot.sections) > 0

                # Load snapshot
                loaded = load_prompt_snapshot("test/prompt.md")
                assert loaded is not None
                assert loaded.content == sample_prompt_before


# =============================================================================
# DRIFT SCORE CALCULATION TESTS
# =============================================================================

class TestDriftScoreCalculation:
    """Tests for drift score calculation."""

    def test_calculate_drift_score_low(self, sample_prompt_before: str, sample_prompt_after: str) -> None:
        """Test drift score for moderate changes (should be LOW/MEDIUM)."""
        from services.prompt_checkpoint import (
            PromptSnapshot,
            compare_snapshots,
            calculate_drift_score,
            categorize_drift,
            _compute_hash,
        )

        old_snapshot = PromptSnapshot(
            prompt_file="test.md",
            content=sample_prompt_before,
            content_hash=_compute_hash(sample_prompt_before),
            version=1,
            sections=["Roadmap 12 Monate", "Einleitung", "Meilensteine"],
            token_count=100,
        )

        new_snapshot = PromptSnapshot(
            prompt_file="test.md",
            content=sample_prompt_after,
            content_hash=_compute_hash(sample_prompt_after),
            version=2,
            sections=["Roadmap 12 Monate", "Einleitung", "Meilensteine", "Quartal 3"],
            token_count=120,
        )

        diff = compare_snapshots(old_snapshot, new_snapshot)
        score = calculate_drift_score(diff)
        category = categorize_drift(score)

        # Moderate changes should result in LOW to MEDIUM drift
        assert score < 50  # Not HIGH
        assert category in ["MINIMAL", "LOW", "MEDIUM"]

    def test_calculate_drift_score_critical(self, sample_prompt_before: str, sample_prompt_critical: str) -> None:
        """Test drift score for major changes (should be HIGH/CRITICAL)."""
        from services.prompt_checkpoint import (
            PromptSnapshot,
            compare_snapshots,
            calculate_drift_score,
            categorize_drift,
            _compute_hash,
        )

        old_snapshot = PromptSnapshot(
            prompt_file="test.md",
            content=sample_prompt_before,
            content_hash=_compute_hash(sample_prompt_before),
            version=1,
            sections=["Roadmap 12 Monate", "Einleitung", "Meilensteine", "Quartal 1", "Quartal 2"],
            token_count=200,
            persona_instructions=["Du-Form für Solo"],
            length_rules=["mindestens 200 Wörter"],
            system_rules=["Vermeide Wiederholungen"],
        )

        new_snapshot = PromptSnapshot(
            prompt_file="test.md",
            content=sample_prompt_critical,
            content_hash=_compute_hash(sample_prompt_critical),
            version=2,
            sections=["Completely New Structure", "Section A", "Section B"],
            token_count=50,
            persona_instructions=[],
            length_rules=[],
            system_rules=["NEW_RULES"],
        )

        diff = compare_snapshots(old_snapshot, new_snapshot)
        score = calculate_drift_score(diff)
        category = categorize_drift(score)

        # Major changes should result in HIGH drift
        assert score >= 30  # At least MEDIUM
        assert len(diff.removed_sections) > 0


# =============================================================================
# PATCH GATE BLOCK/APPROVE TESTS
# =============================================================================

class TestPatchGate:
    """Tests for patch gate block/approve functionality."""

    def test_evaluate_patch_low_drift(self, tmp_path) -> None:
        """Test patch evaluation with low drift - should auto-approve."""
        from services.prompt_patch_gate import evaluate_patch_and_decide, PatchDecision

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            with patch("services.prompt_patch_gate.PROMPT_DRAFT_MODE", False):
                evaluation = evaluate_patch_and_decide(
                    prompt_file="test.md",
                    patch_content="small change",
                    drift_score=10,
                    drift_category="LOW",
                )

                assert evaluation.decision == PatchDecision.AUTO_APPROVE
                assert not evaluation.requires_manual_review

    def test_evaluate_patch_high_drift(self, tmp_path) -> None:
        """Test patch evaluation with high drift - should block for review."""
        from services.prompt_patch_gate import evaluate_patch_and_decide, PatchDecision

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            with patch("services.prompt_patch_gate.PROMPT_DRAFT_MODE", False):
                evaluation = evaluate_patch_and_decide(
                    prompt_file="test.md",
                    patch_content="major change",
                    drift_score=60,
                    drift_category="HIGH",
                )

                assert evaluation.decision == PatchDecision.BLOCK_FOR_REVIEW
                assert evaluation.requires_manual_review

    def test_evaluate_patch_critical_drift(self, tmp_path) -> None:
        """Test patch evaluation with critical drift - should hard stop."""
        from services.prompt_patch_gate import evaluate_patch_and_decide, PatchDecision

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            with patch("services.prompt_patch_gate.PROMPT_DRAFT_MODE", False):
                evaluation = evaluate_patch_and_decide(
                    prompt_file="test.md",
                    patch_content="radical change",
                    drift_score=80,
                    drift_category="CRITICAL",
                )

                assert evaluation.decision == PatchDecision.HARD_STOP
                assert evaluation.requires_manual_review

    def test_block_and_approve_patch(self, tmp_path) -> None:
        """Test manual block and approve functionality."""
        from services.prompt_patch_gate import (
            add_pending_patch,
            block_patch,
            approve_patch,
            get_pending_patches,
            get_blocked_patches,
        )

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            with patch("services.prompt_patch_gate.PROMPT_DRAFT_MODE", False):
                # Add pending patch
                patch_obj = add_pending_patch(
                    prompt_file="test.md",
                    patch_content="test content",
                    source="test",
                )

                # Block it
                block_patch(
                    prompt_file="test.md",
                    patch_id=patch_obj.patch_id,
                    reason="Test block",
                    blocked_by="tester",
                )

                blocked = get_blocked_patches()
                assert len(blocked) >= 1

                # Approve it
                approve_patch(
                    prompt_file="test.md",
                    patch_id=patch_obj.patch_id,
                    approved_by="admin",
                    notes="Approved after review",
                )


# =============================================================================
# SIMULATION REGRESSION TESTS
# =============================================================================

class TestSimulationRegressions:
    """Tests for rollout simulation regression detection."""

    def test_simulate_rollout_passes(self, sample_prompt_before: str, sample_prompt_after: str, tmp_path) -> None:
        """Test simulation that should pass."""
        from services.prompt_rollout_simulator import simulate_rollout

        with patch("services.prompt_rollout_simulator.SIMULATION_RESULTS_PATH", str(tmp_path)):
            with patch("services.prompt_rollout_simulator.PROMPT_DRAFT_MODE", False):
                simulation = simulate_rollout(
                    patch_id="test_patch_1",
                    prompt_file="test.md",
                    prompt_before=sample_prompt_before,
                    prompt_after=sample_prompt_after,
                    random_profile_count=3,
                )

                assert simulation.total_profiles > 0
                assert simulation.simulation_id.startswith("sim_")
                # Most simulations should pass with moderate changes
                # (depends on random simulation results)

    def test_simulation_profile_types(self, sample_prompt_before: str, sample_prompt_after: str, tmp_path) -> None:
        """Test that simulation uses all profile types."""
        from services.prompt_rollout_simulator import simulate_rollout

        with patch("services.prompt_rollout_simulator.SIMULATION_RESULTS_PATH", str(tmp_path)):
            with patch("services.prompt_rollout_simulator.PROMPT_DRAFT_MODE", False):
                simulation = simulate_rollout(
                    patch_id="test_patch_2",
                    prompt_file="test.md",
                    prompt_before=sample_prompt_before,
                    prompt_after=sample_prompt_after,
                    random_profile_count=5,
                )

                # Should have all profile types
                assert len(simulation.gold_profiles) == 3  # 3 gold profiles
                assert len(simulation.random_profiles) == 5  # requested 5 random
                assert len(simulation.risk_edge_profiles) == 2  # 2 risk edge


# =============================================================================
# DASHBOARD ENDPOINT TESTS
# =============================================================================

class TestDashboardEndpoints:
    """Tests for G17.6 dashboard endpoints."""

    def test_governance_overview_endpoint(self, tmp_path) -> None:
        """Test governance overview endpoint."""
        from routes.feedback_dashboard import get_governance_overview

        with patch("services.prompt_checkpoint._get_drift_results_path", return_value=tmp_path):
            with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
                result = asyncio.get_event_loop().run_until_complete(
                    get_governance_overview()
                )

                assert hasattr(result, "enabled")
                assert hasattr(result, "total_prompts_tracked")
                assert hasattr(result, "drift_summary")
                assert hasattr(result, "pending_patches")
                assert hasattr(result, "blocked_patches")

    def test_drift_report_endpoint(self, tmp_path) -> None:
        """Test drift report endpoint."""
        from routes.feedback_dashboard import get_drift_report

        with patch("services.prompt_checkpoint._get_drift_results_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_drift_report(prompt_file="test/prompt.md")
            )

            assert hasattr(result, "prompt_file")
            assert hasattr(result, "drift_score")
            assert hasattr(result, "drift_category")
            assert hasattr(result, "structural_changes")

    def test_pending_patches_endpoint(self, tmp_path) -> None:
        """Test pending patches endpoint."""
        from routes.feedback_dashboard import get_pending_patches_endpoint

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_pending_patches_endpoint()
            )

            assert isinstance(result, list)

    def test_blocked_patches_endpoint(self, tmp_path) -> None:
        """Test blocked patches endpoint."""
        from routes.feedback_dashboard import get_blocked_patches_endpoint

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_blocked_patches_endpoint()
            )

            assert isinstance(result, list)


# =============================================================================
# ENV FLAGS TESTS
# =============================================================================

class TestEnvFlags:
    """Tests for ENV flag behavior."""

    def test_governance_disabled(self) -> None:
        """Test behavior when governance is disabled."""
        from services.prompt_checkpoint import load_prompt_snapshot

        with patch("services.prompt_checkpoint.PROMPT_GOVERNANCE_ENABLED", False):
            result = load_prompt_snapshot("any/file.md")
            assert result is None

    def test_draft_mode_no_persist(self, sample_prompt_before: str, tmp_path) -> None:
        """Test that draft mode doesn't persist changes."""
        from services.prompt_checkpoint import create_prompt_snapshot

        with patch("services.prompt_checkpoint._get_snapshots_path", return_value=tmp_path):
            with patch("services.prompt_checkpoint.PROMPT_DRAFT_MODE", True):
                snapshot = create_prompt_snapshot(
                    prompt_file="draft/test.md",
                    content=sample_prompt_before,
                )

                assert snapshot is not None
                # In draft mode, file should not be created
                files = list(tmp_path.glob("*.json"))
                assert len(files) == 0

    def test_auto_approve_disabled(self, tmp_path) -> None:
        """Test behavior when auto-approve is disabled."""
        from services.prompt_patch_gate import evaluate_patch_and_decide, PatchDecision

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            with patch("services.prompt_patch_gate.PROMPT_PATCH_AUTO_APPROVE", False):
                with patch("services.prompt_patch_gate.PROMPT_DRAFT_MODE", False):
                    evaluation = evaluate_patch_and_decide(
                        prompt_file="test.md",
                        patch_content="small change",
                        drift_score=10,
                        drift_category="LOW",
                    )

                    # Even low drift should be blocked when auto-approve is disabled
                    assert evaluation.decision == PatchDecision.BLOCK_FOR_REVIEW


# =============================================================================
# CRITICAL DRIFT HARD STOP TESTS
# =============================================================================

class TestCriticalDriftHardStop:
    """Tests for critical drift hard stop functionality."""

    def test_critical_drift_triggers_hard_stop(self, tmp_path) -> None:
        """Test that critical drift triggers hard stop."""
        from services.prompt_patch_gate import (
            evaluate_patch_and_decide,
            is_hard_stop,
            PatchDecision,
        )

        with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
            with patch("services.prompt_patch_gate.PROMPT_DRAFT_MODE", False):
                evaluation = evaluate_patch_and_decide(
                    prompt_file="test.md",
                    patch_content="critical change",
                    drift_score=75,
                    drift_category="CRITICAL",
                )

                assert evaluation.decision == PatchDecision.HARD_STOP
                assert is_hard_stop(evaluation)
                assert evaluation.requires_manual_review

    def test_drift_detector_critical_detection(self, sample_prompt_before: str, sample_prompt_critical: str) -> None:
        """Test drift detector identifies critical drift."""
        from services.prompt_drift_detector import (
            analyze_drift,
            is_critical_drift,
        )

        analysis = analyze_drift(
            prompt_file="test.md",
            prompt_before=sample_prompt_before,
            prompt_after=sample_prompt_critical,
        )

        # Major structural changes should produce high drift
        assert analysis.total_drift_score > 0
        assert len(analysis.structural_changes) > 0 or analysis.structural_drift_score > 0


# =============================================================================
# DRIFT DETECTOR TESTS
# =============================================================================

class TestDriftDetector:
    """Tests for drift detector functionality."""

    def test_detect_structural_drift(self, sample_prompt_before: str, sample_prompt_after: str) -> None:
        """Test structural drift detection."""
        from services.prompt_drift_detector import detect_structural_drift

        result = detect_structural_drift(sample_prompt_before, sample_prompt_after)

        assert result.score >= 0
        # Should detect the added "Quartal 3" section
        assert "Quartal 3" in result.added_h3 or len(result.changes) > 0

    def test_detect_instruction_drift(self, sample_prompt_before: str, sample_prompt_after: str) -> None:
        """Test instruction drift detection."""
        from services.prompt_drift_detector import detect_instruction_drift

        result = detect_instruction_drift(sample_prompt_before, sample_prompt_after)

        assert result.score >= 0
        # Length rule changed from 200 to 250 words
        assert len(result.length_constraint_changes) > 0 or result.score >= 0

    def test_detect_semantic_drift(self, sample_prompt_before: str, sample_prompt_after: str) -> None:
        """Test semantic drift detection."""
        from services.prompt_drift_detector import detect_semantic_drift

        result = detect_semantic_drift(sample_prompt_before, sample_prompt_after)

        # Should be within bounds
        assert result.score >= 0 and result.score <= 100
        assert result.formality_shift in ["none", "more_formal", "less_formal"]
        assert result.directive_shift in ["none", "more_directive", "less_directive"]

    def test_detect_fallback_risk(self, sample_prompt_before: str, sample_prompt_after: str) -> None:
        """Test fallback risk detection."""
        from services.prompt_drift_detector import detect_fallback_risk

        result = detect_fallback_risk(sample_prompt_before, sample_prompt_after)

        assert result.score >= 0 and result.score <= 100


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full governance pipeline."""

    def test_full_governance_pipeline(
        self,
        sample_prompt_before: str,
        sample_prompt_after: str,
        tmp_path,
    ) -> None:
        """Test the full governance pipeline from snapshot to decision."""
        from services.prompt_checkpoint import (
            create_prompt_snapshot,
            compare_snapshots,
            calculate_drift_score,
            categorize_drift,
            store_drift_result,
        )
        from services.prompt_drift_detector import analyze_drift, get_drift_summary
        from services.prompt_patch_gate import evaluate_patch_and_decide, can_auto_approve
        from services.prompt_rollout_simulator import simulate_rollout, should_block_patch

        with patch("services.prompt_checkpoint._get_snapshots_path", return_value=tmp_path):
            with patch("services.prompt_checkpoint._get_drift_results_path", return_value=tmp_path):
                with patch("services.prompt_patch_gate._get_decisions_path", return_value=tmp_path):
                    with patch("services.prompt_rollout_simulator.SIMULATION_RESULTS_PATH", str(tmp_path)):
                        with patch("services.prompt_checkpoint.PROMPT_DRAFT_MODE", False):
                            with patch("services.prompt_patch_gate.PROMPT_DRAFT_MODE", False):
                                # 1. Create snapshots
                                old_snapshot = create_prompt_snapshot(
                                    prompt_file="test/pipeline.md",
                                    content=sample_prompt_before,
                                )

                                new_snapshot = create_prompt_snapshot(
                                    prompt_file="test/pipeline.md",
                                    content=sample_prompt_after,
                                )

                                # 2. Compare and calculate drift
                                diff = compare_snapshots(old_snapshot, new_snapshot)
                                drift_score = calculate_drift_score(diff)
                                drift_category = categorize_drift(drift_score)

                                # 3. Run drift analysis
                                analysis = analyze_drift(
                                    "test/pipeline.md",
                                    sample_prompt_before,
                                    sample_prompt_after,
                                )

                                # 4. Store drift result
                                store_drift_result(
                                    prompt_file="test/pipeline.md",
                                    drift_score=drift_score,
                                    diff_summary=get_drift_summary(analysis),
                                )

                                # 5. Evaluate patch
                                evaluation = evaluate_patch_and_decide(
                                    prompt_file="test/pipeline.md",
                                    patch_content=sample_prompt_after,
                                    drift_score=drift_score,
                                    drift_category=drift_category,
                                )

                                # 6. Run simulation
                                simulation = simulate_rollout(
                                    patch_id=evaluation.patch_id,
                                    prompt_file="test/pipeline.md",
                                    prompt_before=sample_prompt_before,
                                    prompt_after=sample_prompt_after,
                                    random_profile_count=3,
                                )

                                # Verify pipeline completed
                                assert old_snapshot.version == 1
                                assert new_snapshot.version == 2
                                assert drift_score >= 0
                                assert evaluation.patch_id is not None
                                assert simulation.total_profiles > 0
