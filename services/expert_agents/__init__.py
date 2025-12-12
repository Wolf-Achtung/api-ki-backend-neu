"""
N4.5 Autonomous Expert Agent Layer - PLATIN+++ v5.5

Expert agents that act as mini-consultants, interpreting research signals,
analyzing numerical relationships, checking risks, writing governance
interpretations, and creating strategic conclusions.

Modules:
- expert_orchestrator: Expert agent registration and dependency management
- risk_specialist_agent: Risk analysis and gap identification
- roi_specialist_agent: ROI interpretation and financial analysis
- benchmark_specialist_agent: Competitive positioning and market analysis
- governance_advisor_agent: Compliance mapping and governance mandates
- transformation_analyst_agent: Transformation scenarios and roadmaps
- knowledge_fusion_engine_v3: Fusion of research and expert findings
- n45_integration: Integration with gpt_analyze.py
"""

from services.expert_agents.expert_orchestrator import (
    # Enums
    ExpertType,
    ExpertStatus,
    DependencyType,
    FindingPriority,
    # Data structures
    ExpertDependency,
    ExpertConfig,
    ExpertFinding,
    ExpertResult,
    ExpertManifest,
    # Classes
    ExpertRegistry,
    DependencyGraph,
    ExpertOrchestrator,
    # Functions
    create_expert_manifest,
    schedule_experts,
    get_expert_status,
)

from services.expert_agents.risk_specialist_agent import (
    # Enums
    RiskGrade,
    GapSeverity,
    ControlCategory,
    # Data structures
    CriticalGap,
    VendorRiskHotspot,
    AIActControl,
    RiskSpecialistFinding,
    # Classes
    RiskSpecialistAgent,
    # Functions
    run_risk_analysis,
    assess_risk_grade,
    identify_control_gaps,
    MOCK_RISK_DATA,
)

from services.expert_agents.roi_specialist_agent import (
    # Enums
    InvestmentRecommendation,
    SimulationScenario,
    MisalignmentType,
    # Data structures
    ROIMetrics,
    SimulationResult,
    MisalignmentFinding,
    ROISpecialistFinding,
    # Classes
    ROISpecialistAgent,
    # Functions
    run_roi_analysis,
    detect_misalignment,
    apply_financial_truth_filter,
    MOCK_ROI_DATA,
)

from services.expert_agents.benchmark_specialist_agent import (
    # Enums
    CompetitivePosition,
    MarketSegment,
    AdvantageType,
    # Data structures
    CompetitorPosition,
    PositionMatrix,
    MarketAdvantageThesis,
    BenchmarkSpecialistFinding,
    # Classes
    BenchmarkSpecialistAgent,
    # Functions
    run_benchmark_analysis,
    build_position_matrix,
    derive_advantage_thesis,
    MOCK_BENCHMARK_DATA,
)

from services.expert_agents.governance_advisor_agent import (
    # Enums
    ComplianceFramework,
    MaturityLevel,
    MandateTimeframe,
    # Data structures
    ComplianceMapping,
    MaturityGap,
    GovernanceMandate,
    GovernanceAdvisorFinding,
    # Classes
    GovernanceAdvisorAgent,
    # Functions
    run_governance_analysis,
    map_compliance_requirements,
    identify_maturity_gaps,
    MOCK_GOVERNANCE_DATA,
)

from services.expert_agents.transformation_analyst_agent import (
    # Enums
    TransformationTrack,
    ScenarioType,
    ChangeReadiness,
    # Data structures
    TransformationScenario,
    OrgChangeSignal,
    TransformationAnalystFinding,
    # Classes
    TransformationAnalystAgent,
    # Functions
    run_transformation_analysis,
    generate_scenarios,
    assess_change_readiness,
    MOCK_TRANSFORMATION_DATA,
)

from services.expert_agents.knowledge_fusion_engine_v3 import (
    # Enums
    ContradictionSeverity,
    ImpactCategory,
    FusionStrategy as FusionStrategyV3,
    # Data structures
    ExpertContradiction,
    ImpactPoint,
    ExecutiveImpactSummary,
    FusedExpertInsight,
    # Classes
    KnowledgeFusionEngineV3,
    ContradictionMiner,
    # Functions
    fuse_expert_findings,
    mine_contradictions,
    generate_impact_summary,
)

from services.expert_agents.n45_integration import (
    # Main functions
    process_n45_experts,
    inject_expert_findings,
    validate_n45_dod,
    # Constants
    N45_VERSION,
)

__version__ = "5.5.0"
__all__ = [
    # Orchestrator
    "ExpertType",
    "ExpertStatus",
    "DependencyType",
    "FindingPriority",
    "ExpertDependency",
    "ExpertConfig",
    "ExpertFinding",
    "ExpertResult",
    "ExpertManifest",
    "ExpertRegistry",
    "DependencyGraph",
    "ExpertOrchestrator",
    "create_expert_manifest",
    "schedule_experts",
    "get_expert_status",
    # Risk Specialist
    "RiskGrade",
    "GapSeverity",
    "ControlCategory",
    "CriticalGap",
    "VendorRiskHotspot",
    "AIActControl",
    "RiskSpecialistFinding",
    "RiskSpecialistAgent",
    "run_risk_analysis",
    "assess_risk_grade",
    "identify_control_gaps",
    "MOCK_RISK_DATA",
    # ROI Specialist
    "InvestmentRecommendation",
    "SimulationScenario",
    "MisalignmentType",
    "ROIMetrics",
    "SimulationResult",
    "MisalignmentFinding",
    "ROISpecialistFinding",
    "ROISpecialistAgent",
    "run_roi_analysis",
    "detect_misalignment",
    "apply_financial_truth_filter",
    "MOCK_ROI_DATA",
    # Benchmark Specialist
    "CompetitivePosition",
    "MarketSegment",
    "AdvantageType",
    "CompetitorPosition",
    "PositionMatrix",
    "MarketAdvantageThesis",
    "BenchmarkSpecialistFinding",
    "BenchmarkSpecialistAgent",
    "run_benchmark_analysis",
    "build_position_matrix",
    "derive_advantage_thesis",
    "MOCK_BENCHMARK_DATA",
    # Governance Advisor
    "ComplianceFramework",
    "MaturityLevel",
    "MandateTimeframe",
    "ComplianceMapping",
    "MaturityGap",
    "GovernanceMandate",
    "GovernanceAdvisorFinding",
    "GovernanceAdvisorAgent",
    "run_governance_analysis",
    "map_compliance_requirements",
    "identify_maturity_gaps",
    "MOCK_GOVERNANCE_DATA",
    # Transformation Analyst
    "TransformationTrack",
    "ScenarioType",
    "ChangeReadiness",
    "TransformationScenario",
    "OrgChangeSignal",
    "TransformationAnalystFinding",
    "TransformationAnalystAgent",
    "run_transformation_analysis",
    "generate_scenarios",
    "assess_change_readiness",
    "MOCK_TRANSFORMATION_DATA",
    # Knowledge Fusion v3
    "ContradictionSeverity",
    "ImpactCategory",
    "FusionStrategyV3",
    "ExpertContradiction",
    "ImpactPoint",
    "ExecutiveImpactSummary",
    "FusedExpertInsight",
    "KnowledgeFusionEngineV3",
    "ContradictionMiner",
    "fuse_expert_findings",
    "mine_contradictions",
    "generate_impact_summary",
    # Integration
    "process_n45_experts",
    "inject_expert_findings",
    "validate_n45_dod",
    "N45_VERSION",
]
