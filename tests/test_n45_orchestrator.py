"""
Tests for N4.5 Expert Agent Orchestrator.

Tests cover:
- Expert type enums
- Expert status enums
- Data structures (ExpertConfig, ExpertFinding, ExpertResult)
- ExpertRegistry functionality
- DependencyGraph operations
- ExpertOrchestrator behavior
- Module functions
"""

import pytest
from typing import Dict, Any

from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertStatus,
    DependencyType,
    FindingPriority,
    ExpertDependency,
    ExpertConfig,
    ExpertFinding,
    ExpertResult,
    ExpertManifest,
    ExpertRegistry,
    DependencyGraph,
    ExpertOrchestrator,
    create_expert_manifest,
    schedule_experts,
    get_expert_status,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample company briefing."""
    return {
        "company_name": "Test GmbH",
        "industry": "Technology",
        "employees": 500,
    }


@pytest.fixture
def sample_dependency() -> ExpertDependency:
    """Sample expert dependency."""
    return ExpertDependency(
        dependency_id="risk_engine_v3",
        dependency_type=DependencyType.ENGINE_OUTPUT,
        source="risk_engine_v3",
        required=True,
        description="Risk Engine V3 output",
    )


@pytest.fixture
def sample_config(sample_dependency) -> ExpertConfig:
    """Sample expert configuration."""
    return ExpertConfig(
        expert_id="risk_specialist",
        expert_type=ExpertType.RISK_SPECIALIST,
        name="Risk Specialist",
        description="Analyzes risk factors",
        dependencies=[sample_dependency],
        priority=10,
        enabled=True,
    )


@pytest.fixture
def sample_finding() -> ExpertFinding:
    """Sample expert finding."""
    return ExpertFinding(
        finding_id="RISK-001",
        expert_type=ExpertType.RISK_SPECIALIST,
        title="Critical Risk Identified",
        content="AI implementation risk detected",
        priority=FindingPriority.HIGH,
        confidence=0.85,
        evidence=["Risk score exceeded threshold"],
        recommendations=["Implement mitigation"],
    )


@pytest.fixture
def sample_result(sample_finding) -> ExpertResult:
    """Sample expert result."""
    return ExpertResult(
        expert_id="risk_specialist",
        expert_type=ExpertType.RISK_SPECIALIST,
        status=ExpertStatus.COMPLETED,
        findings=[sample_finding],
        summary="Risk analysis complete",
        confidence=0.85,
    )


# =============================================================================
# Test Expert Type Enum
# =============================================================================


class TestExpertType:
    """Tests for ExpertType enum."""

    def test_risk_specialist_value(self):
        assert ExpertType.RISK_SPECIALIST.value == "risk_specialist"

    def test_roi_specialist_value(self):
        assert ExpertType.ROI_SPECIALIST.value == "roi_specialist"

    def test_benchmark_specialist_value(self):
        assert ExpertType.BENCHMARK_SPECIALIST.value == "benchmark_specialist"

    def test_governance_advisor_value(self):
        assert ExpertType.GOVERNANCE_ADVISOR.value == "governance_advisor"

    def test_transformation_analyst_value(self):
        assert ExpertType.TRANSFORMATION_ANALYST.value == "transformation_analyst"

    def test_expert_type_count(self):
        assert len(ExpertType) == 5


# =============================================================================
# Test Expert Status Enum
# =============================================================================


class TestExpertStatus:
    """Tests for ExpertStatus enum."""

    def test_pending_value(self):
        assert ExpertStatus.PENDING.value == "pending"

    def test_running_value(self):
        assert ExpertStatus.RUNNING.value == "running"

    def test_completed_value(self):
        assert ExpertStatus.COMPLETED.value == "completed"

    def test_failed_value(self):
        assert ExpertStatus.FAILED.value == "failed"

    def test_status_count(self):
        assert len(ExpertStatus) == 6


# =============================================================================
# Test Dependency Type Enum
# =============================================================================


class TestDependencyType:
    """Tests for DependencyType enum."""

    def test_research_signal(self):
        assert DependencyType.RESEARCH_SIGNAL.value == "research_signal"

    def test_engine_output(self):
        assert DependencyType.ENGINE_OUTPUT.value == "engine_output"

    def test_expert_finding(self):
        assert DependencyType.EXPERT_FINDING.value == "expert_finding"

    def test_data_source(self):
        assert DependencyType.DATA_SOURCE.value == "data_source"


# =============================================================================
# Test Finding Priority Enum
# =============================================================================


class TestFindingPriority:
    """Tests for FindingPriority enum."""

    def test_critical_value(self):
        assert FindingPriority.CRITICAL.value == "critical"

    def test_high_value(self):
        assert FindingPriority.HIGH.value == "high"

    def test_medium_value(self):
        assert FindingPriority.MEDIUM.value == "medium"

    def test_low_value(self):
        assert FindingPriority.LOW.value == "low"

    def test_informational_value(self):
        assert FindingPriority.INFORMATIONAL.value == "informational"


# =============================================================================
# Test Data Structures
# =============================================================================


class TestExpertDependency:
    """Tests for ExpertDependency dataclass."""

    def test_dependency_creation(self, sample_dependency):
        assert sample_dependency.dependency_id == "risk_engine_v3"
        assert sample_dependency.dependency_type == DependencyType.ENGINE_OUTPUT
        assert sample_dependency.required is True

    def test_dependency_to_dict(self, sample_dependency):
        result = sample_dependency.to_dict()
        assert result["dependency_id"] == "risk_engine_v3"
        assert result["dependency_type"] == "engine_output"


class TestExpertConfig:
    """Tests for ExpertConfig dataclass."""

    def test_config_creation(self, sample_config):
        assert sample_config.expert_id == "risk_specialist"
        assert sample_config.expert_type == ExpertType.RISK_SPECIALIST
        assert sample_config.priority == 10

    def test_config_to_dict(self, sample_config):
        result = sample_config.to_dict()
        assert result["expert_id"] == "risk_specialist"
        assert result["expert_type"] == "risk_specialist"
        assert len(result["dependencies"]) == 1


class TestExpertFinding:
    """Tests for ExpertFinding dataclass."""

    def test_finding_creation(self, sample_finding):
        assert sample_finding.finding_id == "RISK-001"
        assert sample_finding.priority == FindingPriority.HIGH
        assert sample_finding.confidence == 0.85

    def test_finding_confidence_clamp(self):
        finding = ExpertFinding(
            finding_id="TEST",
            expert_type=ExpertType.RISK_SPECIALIST,
            title="Test",
            content="Test content",
            priority=FindingPriority.MEDIUM,
            confidence=1.5,
        )
        assert finding.confidence == 1.0

    def test_finding_to_dict(self, sample_finding):
        result = sample_finding.to_dict()
        assert result["finding_id"] == "RISK-001"
        assert result["priority"] == "high"


class TestExpertResult:
    """Tests for ExpertResult dataclass."""

    def test_result_creation(self, sample_result):
        assert sample_result.expert_id == "risk_specialist"
        assert sample_result.status == ExpertStatus.COMPLETED
        assert len(sample_result.findings) == 1

    def test_result_compute_hash(self, sample_result):
        hash_value = sample_result.compute_hash()
        assert len(hash_value) == 16
        assert isinstance(hash_value, str)

    def test_result_to_dict(self, sample_result):
        result = sample_result.to_dict()
        assert result["expert_id"] == "risk_specialist"
        assert result["status"] == "completed"


class TestExpertManifest:
    """Tests for ExpertManifest dataclass."""

    def test_manifest_creation(self, sample_config):
        manifest = ExpertManifest(
            version="5.5.0",
            experts=[sample_config],
            description="Test manifest",
        )
        assert manifest.version == "5.5.0"
        assert len(manifest.experts) == 1

    def test_manifest_to_dict(self, sample_config):
        manifest = ExpertManifest(
            version="5.5.0",
            experts=[sample_config],
        )
        result = manifest.to_dict()
        assert result["version"] == "5.5.0"


# =============================================================================
# Test Expert Registry
# =============================================================================


class TestExpertRegistry:
    """Tests for ExpertRegistry class."""

    def test_registry_init(self):
        registry = ExpertRegistry()
        assert len(registry.get_all_experts()) == 0

    def test_registry_register(self, sample_config):
        registry = ExpertRegistry()

        class MockAgent:
            pass

        registry.register(sample_config, MockAgent)
        assert len(registry.get_all_experts()) == 1

    def test_registry_get_config(self, sample_config):
        registry = ExpertRegistry()

        class MockAgent:
            pass

        registry.register(sample_config, MockAgent)
        config = registry.get_config("risk_specialist")
        assert config is not None
        assert config.expert_id == "risk_specialist"

    def test_registry_get_status(self, sample_config):
        registry = ExpertRegistry()

        class MockAgent:
            pass

        registry.register(sample_config, MockAgent)
        status = registry.get_status("risk_specialist")
        assert status == ExpertStatus.PENDING

    def test_registry_set_status(self, sample_config):
        registry = ExpertRegistry()

        class MockAgent:
            pass

        registry.register(sample_config, MockAgent)
        registry.set_status("risk_specialist", ExpertStatus.RUNNING)
        assert registry.get_status("risk_specialist") == ExpertStatus.RUNNING

    def test_registry_get_enabled_experts(self, sample_config):
        registry = ExpertRegistry()

        class MockAgent:
            pass

        registry.register(sample_config, MockAgent)
        enabled = registry.get_enabled_experts()
        assert len(enabled) == 1


# =============================================================================
# Test Dependency Graph
# =============================================================================


class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    def test_graph_init(self):
        graph = DependencyGraph()
        assert not graph.has_cycle()

    def test_graph_add_expert(self):
        graph = DependencyGraph()
        graph.add_expert("expert_a")
        assert "expert_a" in graph._graph

    def test_graph_add_dependency(self):
        graph = DependencyGraph()
        graph.add_dependency("expert_b", "expert_a")
        deps = graph.get_dependencies("expert_b")
        assert "expert_a" in deps

    def test_graph_topological_sort(self):
        graph = DependencyGraph()
        graph.add_dependency("expert_c", "expert_b")
        graph.add_dependency("expert_b", "expert_a")
        order = graph.topological_sort()
        assert order.index("expert_a") < order.index("expert_b")

    def test_graph_no_cycle(self):
        graph = DependencyGraph()
        graph.add_dependency("b", "a")
        graph.add_dependency("c", "b")
        assert not graph.has_cycle()

    def test_graph_to_dict(self):
        graph = DependencyGraph()
        graph.add_expert("expert_a")
        result = graph.to_dict()
        assert "nodes" in result
        assert "edges" in result


# =============================================================================
# Test Expert Orchestrator
# =============================================================================


class TestExpertOrchestrator:
    """Tests for ExpertOrchestrator class."""

    def test_orchestrator_init(self, sample_briefing):
        orchestrator = ExpertOrchestrator(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert orchestrator.language == "de"
        assert orchestrator.mock_mode is True

    def test_orchestrator_register_defaults(self, sample_briefing):
        orchestrator = ExpertOrchestrator(
            briefing=sample_briefing,
            mock_mode=True,
        )
        orchestrator.register_defaults()
        experts = orchestrator._registry.get_all_experts()
        assert len(experts) == 5

    def test_orchestrator_run_all(self, sample_briefing):
        orchestrator = ExpertOrchestrator(
            briefing=sample_briefing,
            mock_mode=True,
        )
        orchestrator.register_defaults()
        results = orchestrator.run_all()
        assert len(results) == 5

    def test_orchestrator_get_results(self, sample_briefing):
        orchestrator = ExpertOrchestrator(
            briefing=sample_briefing,
            mock_mode=True,
        )
        orchestrator.register_defaults()
        orchestrator.run_all()
        results = orchestrator.get_results()
        assert "risk_specialist" in results

    def test_orchestrator_execution_summary(self, sample_briefing):
        orchestrator = ExpertOrchestrator(
            briefing=sample_briefing,
            mock_mode=True,
        )
        orchestrator.register_defaults()
        orchestrator.run_all()
        summary = orchestrator.get_execution_summary()
        assert summary["total_experts"] == 5
        assert summary["completed"] == 5


# =============================================================================
# Test Module Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_create_expert_manifest(self, sample_config):
        manifest = create_expert_manifest([sample_config])
        assert manifest.version == "5.5.0"
        assert len(manifest.experts) == 1

    def test_schedule_experts(self, sample_config):
        registry = ExpertRegistry()
        graph = DependencyGraph()

        class MockAgent:
            pass

        registry.register(sample_config, MockAgent)
        graph.add_expert(sample_config.expert_id)

        scheduled = schedule_experts(registry, graph)
        assert len(scheduled) == 1

    def test_get_expert_status(self, sample_config):
        registry = ExpertRegistry()

        class MockAgent:
            pass

        registry.register(sample_config, MockAgent)
        status = get_expert_status(registry, "risk_specialist")
        assert status["expert_id"] == "risk_specialist"
        assert status["status"] == "pending"
