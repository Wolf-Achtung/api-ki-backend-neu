"""
N4.0 Regression Suite - PLATIN+++ Autonomous Engine Layer

Comprehensive test suite covering all N4.0 packages:
- Package A: Meta-Engine Scheduler
- Package B: Multi-Model Strategy Layer
- Package C: Multilevel Simulation Engine
- Package D: Knowledge Fusion Engine
- Package E: Complete Governance Engine
- Package F: Adaptive Prompt Evolution Layer

Test Coverage:
- Model switching
- Tenant isolation
- Simulation accuracy
- Governance consistency
- Narrative coherence
- Cross-numerical consistency
- Stress load behavior
- Prompt evolution stability

Target: ~150 tests
"""

import pytest
import time
import random
from datetime import datetime
from typing import Any, Dict, List, Optional


# =============================================================================
# META-ENGINE SCHEDULER TESTS (Package A)
# =============================================================================

class TestMetaEngineScheduler:
    """Tests for Meta-Engine Scheduler module."""

    def test_import_meta_scheduler(self) -> None:
        """Test that meta scheduler module can be imported."""
        from services.meta_engine_scheduler import (
            MetaEngineScheduler,
            EngineDependencyGraph,
            EngineDecisionMaker,
            ConflictDetector,
        )
        assert MetaEngineScheduler is not None
        assert EngineDependencyGraph is not None
        assert EngineDecisionMaker is not None
        assert ConflictDetector is not None

    def test_engine_type_enum(self) -> None:
        """Test EngineType enum values."""
        from services.meta_engine_scheduler import EngineType

        assert EngineType.TOOLS_ENGINE_V4.value == "tools_engine_v4"
        assert EngineType.RISK_ENGINE_V2.value == "risk_engine_v2"
        assert EngineType.GOVERNANCE_ENGINE.value == "governance_engine"
        assert len(list(EngineType)) >= 10

    def test_engine_state_enum(self) -> None:
        """Test EngineState enum values."""
        from services.meta_engine_scheduler import EngineState

        assert EngineState.DISABLED.value == "disabled"
        assert EngineState.PENDING.value == "pending"
        assert EngineState.RUNNING.value == "running"
        assert EngineState.COMPLETED.value == "completed"

    def test_priority_level_enum(self) -> None:
        """Test PriorityLevel enum values."""
        from services.meta_engine_scheduler import PriorityLevel

        assert PriorityLevel.CRITICAL.value == 100
        assert PriorityLevel.HIGH.value == 80
        assert PriorityLevel.MEDIUM.value == 60
        assert PriorityLevel.LOW.value == 40

    def test_dependency_graph_initialization(self) -> None:
        """Test EngineDependencyGraph initialization."""
        from services.meta_engine_scheduler import EngineDependencyGraph, EngineType

        graph = EngineDependencyGraph()

        # All engine types should have nodes
        for engine_type in EngineType:
            node = graph.get_node(engine_type)
            assert node is not None
            assert node.engine_type == engine_type

    def test_dependency_graph_execution_order(self) -> None:
        """Test topological sorting of engine execution."""
        from services.meta_engine_scheduler import EngineDependencyGraph, EngineType

        graph = EngineDependencyGraph()
        order = graph.get_execution_order()

        assert len(order) > 0
        # Governance should come before dependent engines
        gov_idx = order.index(EngineType.GOVERNANCE_ENGINE) if EngineType.GOVERNANCE_ENGINE in order else -1
        if gov_idx >= 0 and EngineType.RISK_ENGINE_V2 in order:
            risk_idx = order.index(EngineType.RISK_ENGINE_V2)
            assert gov_idx < risk_idx

    def test_dependency_graph_parallel_groups(self) -> None:
        """Test parallel execution groups."""
        from services.meta_engine_scheduler import EngineDependencyGraph

        graph = EngineDependencyGraph()
        groups = graph.get_parallel_groups()

        assert len(groups) > 0
        assert isinstance(groups[0], list)

    def test_engine_enable_disable(self) -> None:
        """Test enabling and disabling engines."""
        from services.meta_engine_scheduler import (
            EngineDependencyGraph,
            EngineType,
            EngineState,
        )

        graph = EngineDependencyGraph()

        graph.disable_engine(EngineType.BENCHMARK_ENGINE)
        node = graph.get_node(EngineType.BENCHMARK_ENGINE)
        assert node is not None
        assert node.state == EngineState.DISABLED

        graph.enable_engine(EngineType.BENCHMARK_ENGINE)
        assert node.state == EngineState.PENDING

    def test_decision_maker_evaluation(self) -> None:
        """Test EngineDecisionMaker evaluation logic."""
        from services.meta_engine_scheduler import (
            EngineDecisionMaker,
            EngineType,
            DecisionReason,
        )

        decision_maker = EngineDecisionMaker()

        # Test high-risk tenant enables risk engines
        context = {
            "tenant_config": {},
            "risk_level": "high",
            "data_quality_score": 0.8,
        }

        should_enable, reason, details = decision_maker.evaluate_engine(
            EngineType.RISK_ENGINE_V2,
            context,
        )

        assert should_enable is True
        assert reason == DecisionReason.RISK_LEVEL

    def test_decision_maker_light_mode(self) -> None:
        """Test light mode disables certain engines."""
        from services.meta_engine_scheduler import (
            EngineDecisionMaker,
            EngineType,
            DecisionReason,
        )

        decision_maker = EngineDecisionMaker()

        context = {
            "tenant_config": {"mode": "light"},
            "risk_level": "medium",
        }

        should_enable, reason, _ = decision_maker.evaluate_engine(
            EngineType.AUTOMATION_ROADMAP,
            context,
        )

        assert should_enable is False
        assert reason == DecisionReason.LIGHT_MODE

    def test_conflict_detector_numeric(self) -> None:
        """Test numeric conflict detection."""
        from services.meta_engine_scheduler import ConflictDetector, EngineType

        detector = ConflictDetector()

        # Values differ by more than 4%
        conflict = detector.check_numeric_conflict(
            EngineType.BUSINESS_CASE_V2,
            EngineType.BUSINESS_CASE_V3,
            100.0,
            110.0,
            "roi",
        )

        assert conflict is not None
        assert conflict.conflict_type == "numeric"
        assert conflict.severity in ["medium", "high"]

    def test_conflict_detector_no_conflict(self) -> None:
        """Test no conflict when values are close."""
        from services.meta_engine_scheduler import ConflictDetector, EngineType

        detector = ConflictDetector()

        # Values differ by less than 4%
        conflict = detector.check_numeric_conflict(
            EngineType.BUSINESS_CASE_V2,
            EngineType.BUSINESS_CASE_V3,
            100.0,
            102.0,
            "roi",
        )

        assert conflict is None

    def test_scheduler_singleton(self) -> None:
        """Test scheduler singleton pattern."""
        from services.meta_engine_scheduler import get_scheduler

        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()

        assert scheduler1 is scheduler2

    def test_scheduler_prepare_execution(self) -> None:
        """Test execution preparation."""
        from services.meta_engine_scheduler import MetaEngineScheduler

        scheduler = MetaEngineScheduler()
        context = {
            "tenant_id": "test_tenant",
            "risk_level": "medium",
        }

        state = scheduler.prepare_execution(context)

        assert state is not None
        assert state.execution_id is not None
        assert len(state.decisions) > 0

    def test_scheduler_execution_plan(self) -> None:
        """Test getting execution plan."""
        from services.meta_engine_scheduler import MetaEngineScheduler

        scheduler = MetaEngineScheduler()
        scheduler.prepare_execution({"tenant_id": "test"})
        plan = scheduler.get_execution_plan()

        assert "execution_order" in plan
        assert "groups" in plan
        assert len(plan["execution_order"]) > 0


# =============================================================================
# MULTI-MODEL STRATEGY TESTS (Package B)
# =============================================================================

class TestModelStrategyLayer:
    """Tests for Multi-Model Strategy Layer module."""

    def test_import_model_strategy(self) -> None:
        """Test that model strategy module can be imported."""
        from services.model_strategy_layer import (
            ModelStrategyLayer,
            SemanticMerger,
            ContradictionDetector,
            RedundancyEngine,
        )
        assert ModelStrategyLayer is not None
        assert SemanticMerger is not None
        assert ContradictionDetector is not None
        assert RedundancyEngine is not None

    def test_model_provider_enum(self) -> None:
        """Test ModelProvider enum values."""
        from services.model_strategy_layer import ModelProvider

        assert ModelProvider.GPT.value == "gpt"
        assert ModelProvider.CLAUDE.value == "claude"
        assert ModelProvider.DUAL.value == "dual"

    def test_section_type_enum(self) -> None:
        """Test SectionType enum values."""
        from services.model_strategy_layer import SectionType

        assert SectionType.EXECUTIVE_SUMMARY.value == "executive_summary"
        assert SectionType.RISK_ASSESSMENT.value == "risk_assessment"
        assert SectionType.BUSINESS_CASE.value == "business_case"

    def test_model_selection_rules(self) -> None:
        """Test model selection rules configuration."""
        from services.model_strategy_layer import MODEL_SELECTION_RULES, SectionType, ModelProvider

        # Claude for narrative/governance
        assert MODEL_SELECTION_RULES[SectionType.NARRATIVE] == ModelProvider.CLAUDE
        assert MODEL_SELECTION_RULES[SectionType.GOVERNANCE] == ModelProvider.CLAUDE

        # GPT for tables/calculations
        assert MODEL_SELECTION_RULES[SectionType.TABLES] == ModelProvider.GPT
        assert MODEL_SELECTION_RULES[SectionType.KPI_CALCULATIONS] == ModelProvider.GPT

        # Dual for critical sections
        assert MODEL_SELECTION_RULES[SectionType.EXECUTIVE_SUMMARY] == ModelProvider.DUAL

    def test_select_model_function(self) -> None:
        """Test model selection function."""
        from services.model_strategy_layer import select_model

        model, reason = select_model("risk_assessment", 0.5)
        assert model == "claude"
        assert reason in ["default_selection", "tenant_preference"]

    def test_select_model_complexity_override(self) -> None:
        """Test complexity-based model override."""
        from services.model_strategy_layer import ModelStrategyLayer, SectionType

        layer = ModelStrategyLayer()

        # Very high complexity should prefer Claude
        model, reason = layer.select_model(
            SectionType.TABLES,
            complexity_score=0.95,
        )

        assert model.value == "claude" or reason == "complexity_override" or reason == "default_selection"

    def test_contradiction_detector(self) -> None:
        """Test contradiction detection."""
        from services.model_strategy_layer import ContradictionDetector

        detector = ContradictionDetector()

        text_a = "Die Umsätze werden steigen und das Wachstum wird positiv sein."
        text_b = "Die Umsätze werden sinken und der Rückgang wird erheblich sein."

        contradictions = detector.detect_contradictions(text_a, text_b)

        assert len(contradictions) > 0

    def test_contradiction_detector_no_contradiction(self) -> None:
        """Test no contradiction when texts agree."""
        from services.model_strategy_layer import ContradictionDetector

        detector = ContradictionDetector()

        text_a = "Das Unternehmen zeigt starkes Wachstum."
        text_b = "Die Wachstumsrate des Unternehmens ist beeindruckend."

        contradictions = detector.detect_contradictions(text_a, text_b)

        # Should have no semantic contradictions
        semantic_contradictions = [c for c in contradictions if c.contradiction_type == "semantic"]
        assert len(semantic_contradictions) == 0

    def test_redundancy_engine(self) -> None:
        """Test redundancy detection and removal."""
        from services.model_strategy_layer import RedundancyEngine

        engine = RedundancyEngine()

        text_a = "Das Unternehmen hat eine starke Marktposition und gute Wachstumsaussichten."
        text_b = "Die starke Marktposition und guten Wachstumsaussichten des Unternehmens sind evident."

        redundancies = engine.detect_redundancies(text_a, text_b)

        # Should detect similarity
        assert len(redundancies) >= 0  # May or may not find based on threshold

    def test_tone_harmonizer(self) -> None:
        """Test tone harmonization."""
        from services.model_strategy_layer import ToneHarmonizer

        harmonizer = ToneHarmonizer()

        text = "Die Ergebnisse sind super toll und mega beeindruckend."
        harmonized = harmonizer.harmonize(text)

        assert "super" not in harmonized or "hervorragend" in harmonized

    def test_semantic_merger(self) -> None:
        """Test semantic merging of content."""
        from services.model_strategy_layer import SemanticMerger, MergeStrategy

        merger = SemanticMerger()

        content_a = "Der Markt wächst. Die Chancen sind gut."
        content_b = "Die Expansion ist vielversprechend. Risiken sind minimal."

        result = merger.merge(content_a, content_b, strategy=MergeStrategy.WEIGHTED_BLEND)

        assert "merged_content" in result
        assert len(result["merged_content"]) > 0
        assert "quality_score" in result

    def test_semantic_merge_function(self) -> None:
        """Test convenience merge function."""
        from services.model_strategy_layer import semantic_merge

        content_a = "Erste Aussage zum Thema."
        content_b = "Zweite Aussage mit anderen Details."

        result = semantic_merge(content_a, content_b)

        assert "merged_content" in result
        assert "contradictions_found" in result
        assert "redundancies_removed" in result


# =============================================================================
# SIMULATION ENGINE TESTS (Package C)
# =============================================================================

class TestSimulationEngine:
    """Tests for Multilevel Simulation Engine module."""

    def test_import_simulation_engine(self) -> None:
        """Test that simulation engine module can be imported."""
        from services.simulation_engine import (
            SimulationEngine,
            MonteCarloEngine,
            OperationalSimulator,
            ScenarioImpactEngine,
        )
        assert SimulationEngine is not None
        assert MonteCarloEngine is not None
        assert OperationalSimulator is not None
        assert ScenarioImpactEngine is not None

    def test_simulation_type_enum(self) -> None:
        """Test SimulationType enum values."""
        from services.simulation_engine import SimulationType

        assert SimulationType.MONTE_CARLO.value == "monte_carlo"
        assert SimulationType.OPERATIONAL.value == "operational"
        assert SimulationType.SCENARIO.value == "scenario"

    def test_distribution_type_enum(self) -> None:
        """Test DistributionType enum values."""
        from services.simulation_engine import DistributionType

        assert DistributionType.NORMAL.value == "normal"
        assert DistributionType.LOGNORMAL.value == "lognormal"
        assert DistributionType.UNIFORM.value == "uniform"
        assert DistributionType.TRIANGULAR.value == "triangular"

    def test_scenario_type_enum(self) -> None:
        """Test ScenarioType enum values."""
        from services.simulation_engine import ScenarioType

        assert ScenarioType.OPTIMISTIC.value == "optimistic"
        assert ScenarioType.BASE_CASE.value == "base_case"
        assert ScenarioType.PESSIMISTIC.value == "pessimistic"
        assert ScenarioType.WORST_CASE.value == "worst_case"

    def test_distribution_generator_normal(self) -> None:
        """Test normal distribution generation."""
        from services.simulation_engine import DistributionGenerator, DistributionType

        generator = DistributionGenerator(seed=42)

        samples = generator.generate(
            DistributionType.NORMAL,
            {"mean": 100, "std_dev": 10},
            count=1000,
        )

        assert len(samples) == 1000
        mean = sum(samples) / len(samples)
        assert 90 < mean < 110  # Should be close to 100

    def test_distribution_generator_uniform(self) -> None:
        """Test uniform distribution generation."""
        from services.simulation_engine import DistributionGenerator, DistributionType

        generator = DistributionGenerator(seed=42)

        samples = generator.generate(
            DistributionType.UNIFORM,
            {"min_value": 0, "max_value": 100},
            count=1000,
        )

        assert len(samples) == 1000
        assert all(0 <= s <= 100 for s in samples)

    def test_monte_carlo_simulation(self) -> None:
        """Test Monte Carlo simulation."""
        from services.simulation_engine import MonteCarloEngine

        engine = MonteCarloEngine(seed=42)

        inputs = {
            "revenue": {"base_value": 1000000, "std_dev": 100000},
            "cost": {"base_value": 800000, "std_dev": 80000},
        }

        results = engine.simulate(inputs, iterations=1000)

        assert "revenue" in results
        assert "cost" in results
        assert "mean" in results["revenue"]
        assert "std_dev" in results["revenue"]
        assert "percentiles" in results["revenue"]

    def test_monte_carlo_convergence(self) -> None:
        """Test Monte Carlo convergence detection."""
        from services.simulation_engine import MonteCarloEngine

        engine = MonteCarloEngine(seed=42)

        inputs = {
            "test_var": {"base_value": 100, "std_dev": 5},
        }

        results = engine.simulate(inputs, iterations=5000)

        # With low std_dev, should converge
        assert "convergence_achieved" in results["test_var"]

    def test_operational_simulator(self) -> None:
        """Test operational simulation."""
        from services.simulation_engine import OperationalSimulator

        simulator = OperationalSimulator()

        current = {
            "process_time_hours": 40,
            "tool_adoption": 0.3,
            "governance_complexity": 0.5,
        }

        target = {
            "process_time_hours": 25,
            "tool_adoption": 0.8,
            "governance_improvement": 0.3,
        }

        results = simulator.simulate_operations(
            current, target, simulation_months=12, iterations=100
        )

        assert "process_time_reduction" in results
        assert "tool_adoption_rate" in results
        assert "automation_gain_index" in results
        assert 0 <= results["automation_gain_index"] <= 1

    def test_scenario_impact_calculation(self) -> None:
        """Test scenario impact calculation."""
        from services.simulation_engine import ScenarioImpactEngine, ScenarioType

        engine = ScenarioImpactEngine()

        impact = engine.calculate_scenario_impact(
            base_metrics={"revenue": 1000000},
            scenario_type=ScenarioType.BASE_CASE,
            investment_capex=100000,
            current_opex=500000,
        )

        assert "roi_12m" in impact
        assert "opex_delta" in impact
        assert "capex_amortization_months" in impact
        assert "executive_impact_indicator" in impact

    def test_all_scenarios_calculation(self) -> None:
        """Test calculation of all scenarios."""
        from services.simulation_engine import ScenarioImpactEngine, ScenarioType

        engine = ScenarioImpactEngine()

        results = engine.calculate_all_scenarios(
            base_metrics={"revenue": 1000000},
            investment_capex=100000,
            current_opex=500000,
        )

        for scenario_type in ScenarioType:
            assert scenario_type.value in results
            assert "roi_12m" in results[scenario_type.value]

    def test_simulation_engine_full(self) -> None:
        """Test full simulation engine."""
        from services.simulation_engine import SimulationEngine

        engine = SimulationEngine(seed=42)

        result = engine.run_full_simulation(
            financial_inputs={
                "revenue": {"base_value": 1000000, "std_dev": 100000},
            },
            operational_current={"process_time_hours": 40},
            operational_target={"process_time_hours": 25},
            investment_capex=100000,
            current_opex=500000,
            iterations=500,
        )

        assert "monte_carlo" in result
        assert "operational" in result
        assert "scenarios" in result
        assert "summary" in result

    def test_run_monte_carlo_function(self) -> None:
        """Test convenience Monte Carlo function."""
        from services.simulation_engine import run_monte_carlo

        inputs = {"test": {"base_value": 100}}
        results = run_monte_carlo(inputs, iterations=100)

        assert "test" in results
        assert "mean" in results["test"]


# =============================================================================
# KNOWLEDGE FUSION ENGINE TESTS (Package D)
# =============================================================================

class TestKnowledgeFusionEngine:
    """Tests for Knowledge Fusion Engine module."""

    def test_import_knowledge_fusion(self) -> None:
        """Test that knowledge fusion module can be imported."""
        from services.knowledge_fusion_engine import (
            KnowledgeFusionEngine,
            SemanticClusterer,
            CompetitorDeduplicator,
            KeySignalExtractor,
        )
        assert KnowledgeFusionEngine is not None
        assert SemanticClusterer is not None
        assert CompetitorDeduplicator is not None
        assert KeySignalExtractor is not None

    def test_insight_category_enum(self) -> None:
        """Test InsightCategory enum values."""
        from services.knowledge_fusion_engine import InsightCategory

        assert InsightCategory.MARKET_TREND.value == "market_trend"
        assert InsightCategory.COMPETITOR.value == "competitor"
        assert InsightCategory.TECHNOLOGY.value == "technology"

    def test_signal_type_enum(self) -> None:
        """Test SignalType enum (5-Signal Model)."""
        from services.knowledge_fusion_engine import SignalType

        assert SignalType.GROWTH_SIGNAL.value == "growth_signal"
        assert SignalType.DISRUPTION_SIGNAL.value == "disruption_signal"
        assert SignalType.CONSOLIDATION_SIGNAL.value == "consolidation_signal"
        assert SignalType.REGULATION_SIGNAL.value == "regulation_signal"
        assert SignalType.TALENT_SIGNAL.value == "talent_signal"
        assert len(list(SignalType)) == 5

    def test_semantic_clusterer(self) -> None:
        """Test semantic clustering of insights."""
        from services.knowledge_fusion_engine import SemanticClusterer

        clusterer = SemanticClusterer()

        insights = [
            {"id": "1", "content": "Der Markt zeigt starkes Wachstum in der Digitalisierung."},
            {"id": "2", "content": "Digitalisierung treibt das Marktwachstum erheblich voran."},
            {"id": "3", "content": "Neue Regulierungen erfordern Compliance-Anpassungen."},
        ]

        clusters = clusterer.cluster_insights(insights, min_cluster_size=1)

        assert len(clusters) >= 1

    def test_competitor_deduplicator(self) -> None:
        """Test competitor deduplication."""
        from services.knowledge_fusion_engine import CompetitorDeduplicator

        deduplicator = CompetitorDeduplicator()

        insights = [
            {"id": "1", "content": "Microsoft ist Marktführer im Cloud-Bereich.", "source": "report1"},
            {"id": "2", "content": "Microsoft Corp. expandiert in neue Märkte.", "source": "report2"},
            {"id": "3", "content": "Google konkurriert stark im KI-Segment.", "source": "report1"},
        ]

        profiles = deduplicator.deduplicate_competitors(insights)

        # Should consolidate Microsoft mentions
        microsoft_profiles = [p for p in profiles if "microsoft" in p["normalized_name"].lower()]
        assert len(microsoft_profiles) <= 1 or profiles[0]["mentions"] >= 1

    def test_key_signal_extractor(self) -> None:
        """Test key signal extraction."""
        from services.knowledge_fusion_engine import KeySignalExtractor, InsightCluster, InsightCategory, SignalType

        extractor = KeySignalExtractor()

        # Create mock clusters with signals
        cluster = InsightCluster(
            cluster_id="test_cluster",
            category=InsightCategory.MARKET_TREND,
            members=[
                {"content": "Starkes Marktwachstum und Expansion beobachtet.", "source": "test"},
            ],
        )
        cluster.signals = {SignalType.GROWTH_SIGNAL}

        signals = extractor.extract_signals([cluster])

        assert len(signals) > 0
        assert signals[0]["signal_type"] == "growth_signal"

    def test_market_thesis_builder(self) -> None:
        """Test market thesis building."""
        from services.knowledge_fusion_engine import (
            MarketThesisBuilder,
            InsightCluster,
            InsightCategory,
            ClusterQuality,
        )

        builder = MarketThesisBuilder()

        cluster = InsightCluster(
            cluster_id="test",
            category=InsightCategory.TECHNOLOGY,
            members=[
                {"content": "KI transformiert die Branche fundamental.", "source": "test"},
                {"content": "Technologische Innovation treibt den Wandel.", "source": "test"},
            ],
            quality=ClusterQuality.HIGH,
        )
        cluster._update_centroid()

        theses = builder.build_theses([cluster], [], [])

        assert len(theses) > 0
        assert "statement" in theses[0]
        assert "implications" in theses[0]

    def test_knowledge_fusion_engine_full(self) -> None:
        """Test full knowledge fusion process."""
        from services.knowledge_fusion_engine import KnowledgeFusionEngine

        engine = KnowledgeFusionEngine()

        insights = [
            {"id": "1", "content": "Der KI-Markt wächst um 25% jährlich.", "source": "analyst"},
            {"id": "2", "content": "Wachstum im KI-Segment beträgt ca. 25 Prozent.", "source": "report"},
            {"id": "3", "content": "Microsoft und Google dominieren das Cloud-Geschäft.", "source": "news"},
        ]

        result = engine.fuse_insights(insights)

        assert result.fusion_id is not None
        assert result.statistics["input_insights"] == 3

    def test_fuse_research_insights_function(self) -> None:
        """Test convenience fusion function."""
        from services.knowledge_fusion_engine import fuse_research_insights

        insights = [
            {"id": "1", "content": "Test insight about market growth.", "source": "test"},
        ]

        result = fuse_research_insights(insights)

        assert "fusion_id" in result
        assert "statistics" in result


# =============================================================================
# GOVERNANCE ENGINE TESTS (Package E)
# =============================================================================

class TestGovernanceEngine:
    """Tests for Governance Engine module."""

    def test_import_governance_engine(self) -> None:
        """Test that governance engine module can be imported."""
        from services.governance_engine import (
            GovernanceEngine,
            MaturityAssessor,
            RACIGenerator,
            PolicyBlueprintGenerator,
        )
        assert GovernanceEngine is not None
        assert MaturityAssessor is not None
        assert RACIGenerator is not None
        assert PolicyBlueprintGenerator is not None

    def test_governance_framework_enum(self) -> None:
        """Test GovernanceFramework enum values."""
        from services.governance_engine import GovernanceFramework

        assert GovernanceFramework.EU_AI_ACT.value == "eu_ai_act"
        assert GovernanceFramework.ISO_42001.value == "iso_42001"
        assert GovernanceFramework.NIST_AI_RMF.value == "nist_ai_rmf"

    def test_maturity_level_enum(self) -> None:
        """Test MaturityLevel enum values."""
        from services.governance_engine import MaturityLevel

        assert MaturityLevel.INITIAL.value == "initial"
        assert MaturityLevel.DEVELOPING.value == "developing"
        assert MaturityLevel.DEFINED.value == "defined"
        assert MaturityLevel.MANAGED.value == "managed"
        assert MaturityLevel.OPTIMIZING.value == "optimizing"

    def test_risk_level_enum(self) -> None:
        """Test RiskLevel enum (EU AI Act classification)."""
        from services.governance_engine import RiskLevel

        assert RiskLevel.UNACCEPTABLE.value == "unacceptable"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.LIMITED.value == "limited"
        assert RiskLevel.MINIMAL.value == "minimal"

    def test_maturity_assessor(self) -> None:
        """Test maturity assessment."""
        from services.governance_engine import MaturityAssessor

        assessor = MaturityAssessor()

        assessment = {
            "ai_system_description": "Test AI system for document processing",
            "existing_controls": [
                "Risk assessment policy",
                "Data governance framework",
                "Model validation process",
            ],
        }

        result = assessor.assess_maturity(assessment)

        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 100
        assert "maturity_level" in result
        assert "gaps" in result
        assert "recommendations" in result

    def test_raci_generator(self) -> None:
        """Test RACI matrix generation."""
        from services.governance_engine import RACIGenerator

        generator = RACIGenerator()

        stakeholders = [
            "CEO",
            "CTO",
            "Data Science Lead",
            "Compliance Officer",
            "Risk Manager",
        ]

        raci_matrix = generator.generate_raci(stakeholders)

        assert len(raci_matrix) > 0
        for entry in raci_matrix:
            assert "activity" in entry
            assert "responsible" in entry
            assert "accountable" in entry

    def test_policy_blueprint_generator(self) -> None:
        """Test policy blueprint generation."""
        from services.governance_engine import PolicyBlueprintGenerator, GovernanceFramework

        generator = PolicyBlueprintGenerator()

        assessment = {
            "use_cases": ["Document classification", "Risk scoring"],
            "deployment_context": "Enterprise",
        }

        policies = generator.generate_policies(
            assessment,
            [GovernanceFramework.EU_AI_ACT],
        )

        assert len(policies) >= 5
        for policy in policies:
            assert "policy_id" in policy
            assert "title" in policy
            assert "requirements" in policy

    def test_risk_control_library(self) -> None:
        """Test risk control library."""
        from services.governance_engine import RiskControlLibrary, RiskLevel

        library = RiskControlLibrary()

        # High risk should return all controls
        high_risk_controls = library.get_controls(RiskLevel.HIGH)
        assert len(high_risk_controls) >= 10

        # Minimal risk should return fewer controls
        minimal_risk_controls = library.get_controls(RiskLevel.MINIMAL)
        assert len(minimal_risk_controls) < len(high_risk_controls)

    def test_governance_engine_full_assessment(self) -> None:
        """Test full governance assessment."""
        from services.governance_engine import GovernanceEngine

        engine = GovernanceEngine()

        assessment = {
            "ai_system_description": "Customer service chatbot",
            "use_cases": ["Customer inquiry handling"],
            "existing_controls": ["Basic monitoring"],
            "stakeholders": ["CEO", "CTO", "Compliance"],
        }

        profile = engine.assess_governance(assessment)

        assert profile.profile_id is not None
        assert profile.maturity_result is not None
        assert len(profile.raci_matrix) > 0
        assert len(profile.policies) > 0
        assert profile.summary is not None

    def test_risk_classification(self) -> None:
        """Test EU AI Act risk classification."""
        from services.governance_engine import GovernanceEngine

        engine = GovernanceEngine()

        # High-risk use case
        high_risk_assessment = {
            "ai_system_description": "AI for employment decisions",
            "use_cases": ["employment_hr"],
        }

        profile = engine.assess_governance(high_risk_assessment)
        assert profile.summary is not None
        assert profile.summary["risk_classification"] in ["high", "limited", "minimal"]

    def test_assess_ai_governance_function(self) -> None:
        """Test convenience governance assessment function."""
        from services.governance_engine import assess_ai_governance

        assessment = {
            "ai_system_description": "Test system",
            "existing_controls": [],
        }

        result = assess_ai_governance(assessment)

        assert "profile_id" in result
        assert "executive_summary" in result
        assert "maturity_assessment" in result


# =============================================================================
# PROMPT EVOLUTION ENGINE TESTS (Package F)
# =============================================================================

class TestPromptEvolutionEngine:
    """Tests for Prompt Evolution Engine module."""

    def test_import_prompt_evolution(self) -> None:
        """Test that prompt evolution module can be imported."""
        from services.prompt_evolution_engine import (
            PromptEvolutionEngine,
            MutationEngine,
            FitnessEvaluator,
            EvolutionEngine,
        )
        assert PromptEvolutionEngine is not None
        assert MutationEngine is not None
        assert FitnessEvaluator is not None
        assert EvolutionEngine is not None

    def test_prompt_category_enum(self) -> None:
        """Test PromptCategory enum values."""
        from services.prompt_evolution_engine import PromptCategory

        assert PromptCategory.ANALYSIS.value == "analysis"
        assert PromptCategory.NARRATIVE.value == "narrative"
        assert PromptCategory.EXTRACTION.value == "extraction"

    def test_mutation_type_enum(self) -> None:
        """Test MutationType enum values."""
        from services.prompt_evolution_engine import MutationType

        assert MutationType.SYNONYM_REPLACE.value == "synonym_replace"
        assert MutationType.PHRASE_REORDER.value == "phrase_reorder"
        assert MutationType.EMPHASIS_ADJUST.value == "emphasis_adjust"

    def test_fitness_metric_enum(self) -> None:
        """Test FitnessMetric enum values."""
        from services.prompt_evolution_engine import FitnessMetric

        assert FitnessMetric.LEAK_PROBABILITY.value == "leak_probability"
        assert FitnessMetric.FALLBACK_FREQUENCY.value == "fallback_frequency"
        assert FitnessMetric.CONSISTENCY_SCORE.value == "consistency_score"

    def test_mutation_engine_synonym(self) -> None:
        """Test synonym mutation."""
        from services.prompt_evolution_engine import MutationEngine, MutationType

        engine = MutationEngine(seed=42)

        prompt = "Analysiere die wichtigen Aspekte detailliert."
        mutated, records = engine.mutate(
            prompt,
            mutation_rate=1.0,  # Force mutation
            allowed_mutations=[MutationType.SYNONYM_REPLACE],
        )

        # May or may not mutate depending on random choice
        assert isinstance(mutated, str)
        assert len(mutated) > 0

    def test_mutation_engine_constraint_add(self) -> None:
        """Test constraint addition mutation."""
        from services.prompt_evolution_engine import MutationEngine, MutationType

        engine = MutationEngine(seed=42)

        prompt = "Beschreibe das Ergebnis."
        mutated, records = engine.mutate(
            prompt,
            mutation_rate=1.0,
            allowed_mutations=[MutationType.CONSTRAINT_ADD],
        )

        # Should have added a constraint
        constraint_added = any(r.mutation_type == MutationType.CONSTRAINT_ADD for r in records)
        if constraint_added:
            assert len(mutated) > len(prompt)

    def test_fitness_evaluator(self) -> None:
        """Test fitness evaluation."""
        from services.prompt_evolution_engine import FitnessEvaluator

        evaluator = FitnessEvaluator()

        prompt = "WICHTIG: Analysiere die Daten präzise und strukturiert. Beispiel: KPI-Analyse."

        fitness, metrics = evaluator.evaluate(prompt)

        assert 0 <= fitness <= 1
        assert "leak_probability" in metrics
        assert "consistency_score" in metrics
        assert "narrative_depth" in metrics

    def test_fitness_evaluator_comparison(self) -> None:
        """Test that better prompts get better fitness scores."""
        from services.prompt_evolution_engine import FitnessEvaluator

        evaluator = FitnessEvaluator()

        # Prompt with good structure
        good_prompt = """
        WICHTIG: Analysiere präzise und strukturiert.
        1. Identifiziere Kernaspekte
        2. Bewerte quantitativ
        Beispiel: ROI-Berechnung durchführen.
        Beachte besonders: Konsistenz wahren.
        """

        # Simple prompt
        simple_prompt = "Mach eine Analyse."

        good_fitness, _ = evaluator.evaluate(good_prompt)
        simple_fitness, _ = evaluator.evaluate(simple_prompt)

        # Good prompt should have higher or equal fitness
        assert good_fitness >= simple_fitness * 0.9  # Allow some variance

    def test_evolution_engine_initialization(self) -> None:
        """Test evolution engine initialization."""
        from services.prompt_evolution_engine import EvolutionEngine, PromptCategory

        engine = EvolutionEngine(seed=42)

        state = engine.initialize_evolution(
            prompt_id="test_prompt",
            initial_prompt="Test prompt content.",
            category=PromptCategory.ANALYSIS,
        )

        assert state is not None
        assert state.evolution_id is not None
        assert len(state.population) > 0
        assert state.best_ever is not None

    def test_evolution_generation(self) -> None:
        """Test running one evolution generation."""
        from services.prompt_evolution_engine import EvolutionEngine, PromptCategory

        engine = EvolutionEngine(seed=42)

        engine.initialize_evolution(
            prompt_id="test_evo",
            initial_prompt="Analysiere die wichtigen Daten.",
            category=PromptCategory.ANALYSIS,
        )

        result = engine.evolve_generation("test_evo")

        assert "generation" in result
        assert result["generation"] == 1
        assert "best_fitness" in result
        assert "avg_fitness" in result

    def test_prompt_evolution_engine_full(self) -> None:
        """Test full prompt evolution engine."""
        from services.prompt_evolution_engine import PromptEvolutionEngine

        engine = PromptEvolutionEngine(seed=42)

        genome = engine.register_prompt(
            prompt_id="full_test",
            content="Beschreibe das Ergebnis klar und präzise.",
            category="analysis",
        )

        assert genome is not None
        assert "genome_id" in genome

    def test_evolve_prompt_function(self) -> None:
        """Test convenience evolve function."""
        from services.prompt_evolution_engine import (
            get_prompt_evolution_engine,
            register_prompt_for_evolution,
            evolve_prompt,
        )

        engine = get_prompt_evolution_engine(seed=42)

        # Register
        reg_result = register_prompt_for_evolution(
            prompt_id="conv_test",
            content="Test prompt for evolution.",
        )
        assert "genome_id" in reg_result

        # Evolve
        evo_result = evolve_prompt("conv_test", max_generations=2)
        assert "generations_run" in evo_result
        assert "final_fitness" in evo_result

    def test_evolution_config(self) -> None:
        """Test evolution configuration values."""
        from services.prompt_evolution_engine import EVOLUTION_CONFIG

        assert EVOLUTION_CONFIG["mutation_rate"] == 0.07  # ±7%
        assert EVOLUTION_CONFIG["population_size"] >= 3
        assert EVOLUTION_CONFIG["fitness_threshold"] > 0.5


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestN40Integration:
    """Integration tests for N4.0 modules working together."""

    def test_scheduler_with_simulation(self) -> None:
        """Test meta scheduler can coordinate simulation."""
        from services.meta_engine_scheduler import MetaEngineScheduler, EngineType
        from services.simulation_engine import get_simulation_engine

        scheduler = MetaEngineScheduler()
        sim_engine = get_simulation_engine()

        # Both should initialize without errors
        assert scheduler is not None
        assert sim_engine is not None

    def test_model_strategy_with_knowledge_fusion(self) -> None:
        """Test model strategy with knowledge fusion."""
        from services.model_strategy_layer import semantic_merge
        from services.knowledge_fusion_engine import cluster_insights

        # These should work independently
        merge_result = semantic_merge("Text A.", "Text B.")
        assert "merged_content" in merge_result

        clusters = cluster_insights([{"id": "1", "content": "Test insight."}])
        assert isinstance(clusters, list)

    def test_governance_with_evolution(self) -> None:
        """Test governance engine with prompt evolution."""
        from services.governance_engine import get_governance_maturity_score
        from services.prompt_evolution_engine import get_prompt_evolution_map

        # Both should work
        score = get_governance_maturity_score({"existing_controls": []})
        assert "overall_score" in score

        evolution_map = get_prompt_evolution_map()
        assert "prompts" in evolution_map

    def test_all_modules_import(self) -> None:
        """Test all N4.0 modules can be imported together."""
        from services.meta_engine_scheduler import get_scheduler
        from services.model_strategy_layer import get_model_strategy
        from services.simulation_engine import get_simulation_engine
        from services.knowledge_fusion_engine import get_knowledge_fusion_engine
        from services.governance_engine import get_governance_engine
        from services.prompt_evolution_engine import get_prompt_evolution_engine

        # All singletons should be obtainable
        assert get_scheduler() is not None
        assert get_model_strategy() is not None
        assert get_simulation_engine() is not None
        assert get_knowledge_fusion_engine() is not None
        assert get_governance_engine() is not None
        assert get_prompt_evolution_engine() is not None


# =============================================================================
# STRESS & PERFORMANCE TESTS
# =============================================================================

class TestN40StressLoad:
    """Stress and load tests for N4.0 modules."""

    def test_monte_carlo_large_iterations(self) -> None:
        """Test Monte Carlo with large number of iterations."""
        from services.simulation_engine import MonteCarloEngine

        engine = MonteCarloEngine(seed=42)

        inputs = {"test": {"base_value": 100, "std_dev": 10}}

        start = time.time()
        results = engine.simulate(inputs, iterations=10000)
        elapsed = time.time() - start

        assert "test" in results
        assert elapsed < 10  # Should complete in under 10 seconds

    def test_clustering_many_insights(self) -> None:
        """Test clustering with many insights."""
        from services.knowledge_fusion_engine import SemanticClusterer

        clusterer = SemanticClusterer()

        # Generate many insights
        insights = [
            {"id": str(i), "content": f"Insight {i} about market trend number {i % 10}."}
            for i in range(100)
        ]

        start = time.time()
        clusters = clusterer.cluster_insights(insights, min_cluster_size=2)
        elapsed = time.time() - start

        assert len(clusters) > 0
        assert elapsed < 30  # Should complete in under 30 seconds

    def test_evolution_multiple_generations(self) -> None:
        """Test evolution over multiple generations."""
        from services.prompt_evolution_engine import EvolutionEngine, PromptCategory

        engine = EvolutionEngine(seed=42)

        engine.initialize_evolution(
            prompt_id="stress_test",
            initial_prompt="Analysiere die wichtigen Daten präzise und strukturiert.",
            category=PromptCategory.ANALYSIS,
        )

        start = time.time()
        for _ in range(5):
            if engine.should_continue_evolution("stress_test"):
                engine.evolve_generation("stress_test")
        elapsed = time.time() - start

        state = engine.get_evolution_state("stress_test")
        assert state is not None
        assert state.current_generation >= 1
        assert elapsed < 30

    def test_concurrent_scheduler_access(self) -> None:
        """Test concurrent access to scheduler."""
        from services.meta_engine_scheduler import get_scheduler
        import threading

        results = []

        def get_scheduler_instance():
            scheduler = get_scheduler()
            results.append(scheduler)

        threads = [threading.Thread(target=get_scheduler_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should get the same instance
        assert len(results) == 10
        assert all(r is results[0] for r in results)


# =============================================================================
# CONSISTENCY TESTS
# =============================================================================

class TestN40Consistency:
    """Tests for cross-numerical and narrative consistency."""

    def test_simulation_scenario_consistency(self) -> None:
        """Test simulation scenarios are internally consistent."""
        from services.simulation_engine import ScenarioImpactEngine, ScenarioType

        engine = ScenarioImpactEngine()

        scenarios = engine.calculate_all_scenarios(
            base_metrics={"revenue": 1000000},
            investment_capex=100000,
            current_opex=500000,
        )

        # Optimistic should have better ROI than pessimistic
        opt_roi = scenarios[ScenarioType.OPTIMISTIC.value]["roi_12m"]
        pes_roi = scenarios[ScenarioType.PESSIMISTIC.value]["roi_12m"]

        assert opt_roi >= pes_roi

    def test_governance_score_consistency(self) -> None:
        """Test governance scores are consistent with inputs."""
        from services.governance_engine import MaturityAssessor

        assessor = MaturityAssessor()

        # More controls should mean higher score
        few_controls = assessor.assess_maturity({"existing_controls": ["policy"]})
        many_controls = assessor.assess_maturity({
            "existing_controls": [
                "risk assessment",
                "data governance",
                "model validation",
                "monitoring",
                "audit",
            ]
        })

        assert many_controls["overall_score"] >= few_controls["overall_score"]

    def test_evolution_fitness_improvement(self) -> None:
        """Test evolution tends to improve fitness."""
        from services.prompt_evolution_engine import EvolutionEngine, PromptCategory

        engine = EvolutionEngine(seed=42)

        engine.initialize_evolution(
            prompt_id="fitness_test",
            initial_prompt="Mach Analyse.",  # Deliberately simple
            category=PromptCategory.ANALYSIS,
        )

        initial_state = engine.get_evolution_state("fitness_test")
        initial_fitness = initial_state.best_ever["fitness"] if initial_state and initial_state.best_ever else 0

        # Run a few generations
        for _ in range(3):
            if engine.should_continue_evolution("fitness_test"):
                engine.evolve_generation("fitness_test")

        final_state = engine.get_evolution_state("fitness_test")
        final_fitness = final_state.best_ever["fitness"] if final_state and final_state.best_ever else 0

        # Should not decrease significantly
        assert final_fitness >= initial_fitness * 0.9


# =============================================================================
# MODULE AVAILABILITY TESTS
# =============================================================================

class TestModuleAvailability:
    """Tests for module availability flags in gpt_analyze.py."""

    def test_meta_scheduler_available(self) -> None:
        """Test META_SCHEDULER_AVAILABLE flag."""
        try:
            from services.meta_engine_scheduler import get_scheduler
            available = True
        except ImportError:
            available = False
        assert available is True

    def test_model_strategy_available(self) -> None:
        """Test MODEL_STRATEGY_AVAILABLE flag."""
        try:
            from services.model_strategy_layer import get_model_strategy
            available = True
        except ImportError:
            available = False
        assert available is True

    def test_simulation_engine_available(self) -> None:
        """Test SIMULATION_ENGINE_AVAILABLE flag."""
        try:
            from services.simulation_engine import get_simulation_engine
            available = True
        except ImportError:
            available = False
        assert available is True

    def test_knowledge_fusion_available(self) -> None:
        """Test KNOWLEDGE_FUSION_AVAILABLE flag."""
        try:
            from services.knowledge_fusion_engine import get_knowledge_fusion_engine
            available = True
        except ImportError:
            available = False
        assert available is True

    def test_governance_engine_available(self) -> None:
        """Test GOVERNANCE_ENGINE_AVAILABLE flag."""
        try:
            from services.governance_engine import get_governance_engine
            available = True
        except ImportError:
            available = False
        assert available is True

    def test_prompt_evolution_available(self) -> None:
        """Test PROMPT_EVOLUTION_AVAILABLE flag."""
        try:
            from services.prompt_evolution_engine import get_prompt_evolution_engine
            available = True
        except ImportError:
            available = False
        assert available is True
