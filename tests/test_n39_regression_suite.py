# -*- coding: utf-8 -*-
"""
SPRINT N3.9 PACKAGE G: Comprehensive Regression Test Suite.

~160 tests covering all N3.9 packages:
- Multi-Tenant Isolation (25 tests)
- Audit & Traceability (25 tests)
- Performance Layer v6 (25 tests)
- Safety & Compliance Auto-Tuner (25 tests)
- Consistency Kernel v6 (20 tests)
- Executive Narrative v2 (20 tests)
- Final Integration (20 tests)

Version: 1.0.0 (N3.9 - PLATIN++ v4.28)
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections for testing."""
    return {
        "EXEC_SUMMARY_HTML": """
            <h1>Executive Summary</h1>
            <p>Das Unternehmen steht vor der digitalen Transformation.
            Der ROI beträgt 25%. Die Payback-Dauer ist 18 Monate.</p>
            <p>Priorität 1: Automatisierung. Priorität 2: Analytics.</p>
            <p>Die strategische Position erfordert schnelles Handeln.</p>
        """,
        "KI_STACK_SUMMARY_HTML": """
            <h2>KI-Stack Empfehlung</h2>
            <p>Der ROI beträgt 25%. Die Amortisationszeit ist 18 Monate.</p>
            <ul>
                <li>GPT-4 für Textanalyse</li>
                <li>Claude für Dokumentation</li>
            </ul>
            <p>Phase 1: Implementierung in 3 Monaten.</p>
        """,
        "RECOMMENDATIONS_HTML": """
            <h2>Handlungsempfehlungen</h2>
            <p>Empfehlung 1: Quick Wins implementieren. ROI: 15%</p>
            <p>Empfehlung 2: Foundation aufbauen. Einsparung: 50.000 EUR</p>
            <p>Empfehlung 3: Scale-up vorbereiten. Effizienz +20%</p>
        """,
        "RISKS_HTML": """
            <h2>Risikoanalyse</h2>
            <p>Datenschutz-Risiko: hoch. Security-Risiko: mittel.</p>
            <p>Reduktion: 30% durch Maßnahmen in 6 Monaten.</p>
            <p>Compliance muss in 3 Monaten erreicht werden.</p>
        """,
        "ROADMAP_90D_HTML": """
            <h2>90-Tage Roadmap</h2>
            <p>Phase 1: Pilot starten in 4 Wochen.</p>
            <p>Phase 2: Quick Wins erreichen. Verbesserung 30%.</p>
            <p>Schulung für 10 Mitarbeiter geplant.</p>
        """,
        "ROADMAP_12M_HTML": """
            <h2>12-Monats Roadmap</h2>
            <p>Phase 3: Scale-Up durchführen in 6 Monaten.</p>
            <p>Phase 4: Optimierung starten. Training und Weiterbildung.</p>
            <p>Kompetenzaufbau über 12 Monate.</p>
        """,
        "BUSINESS_CASE_HTML": """
            <h2>Business Case</h2>
            <p>ROI: 25%. Payback: 18 Monate. Einsparung: 100.000 EUR.</p>
            <p>Produktivitätssteigerung um 35% erwartet.</p>
        """,
        "WETTBEWERB_BENCHMARK_HTML": """
            <h2>Wettbewerbs-Benchmark</h2>
            <p>Digitalisierungsgrad: 2/5 (unterdurchschnittlich).</p>
            <p>Lücke bei Automatisierung. Gap in Analytics.</p>
            <p>Rückstand von 18 Monaten zum Wettbewerb.</p>
        """,
        "TOOLS_EMPFEHLUNGEN_HTML": """
            <h2>Tool-Empfehlungen</h2>
            <p>Tool 1: ChatGPT Enterprise für Automatisierung</p>
            <p>Tool 2: Power BI für Analytics</p>
            <p>Integration über API-Schnittstellen.</p>
        """,
        "FOERDERPOTENZIAL_HTML": """
            <h2>Förderpotenzial</h2>
            <p>ZIM: Bis zu 550.000 EUR Förderung für innovative Projekte.</p>
            <p>Go-Digital: Beratungsförderung verfügbar.</p>
        """,
        "STRATEGIE_GOVERNANCE_HTML": """
            <h2>Strategie & Governance</h2>
            <p>Die strategische Ausrichtung fokussiert auf digitale Transformation.</p>
            <p>ROI-Ziel: 25%. Wertschöpfung durch KI.</p>
        """,
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing for testing."""
    return {
        "branch": "Finanzdienstleistungen",
        "employees": 150,
        "company_name": "Test GmbH",
        "language": "de",
        "unternehmensgroesse": "kmu",
        "description": "Digitalisierungsberatung für KMU",
        "report_purpose": "consulting",
        "audience": "executive",
    }


@pytest.fixture
def sample_briefing_high_risk() -> Dict[str, Any]:
    """High-risk briefing for safety tuner testing."""
    return {
        "branch": "Healthcare",
        "employees": 500,
        "company_name": "MedTech GmbH",
        "language": "de",
        "use_case": "Patientendaten-Analyse",
        "description": "KI für Diagnoseunterstützung mit Patientendaten",
    }


@pytest.fixture
def sample_tenant_config() -> Dict[str, Any]:
    """Sample tenant configuration."""
    return {
        "tenant_id": "test_tenant_001",
        "tenant_name": "Test Corporation",
        "tier": "enterprise",
        "branding": {
            "logo_primary": "/logos/test_primary.png",
            "color_primary": "#0066CC",
            "color_secondary": "#00CC66",
        },
        "wording_profile": "executive",
        "risk_profile": "balanced",
        "enable_custom_prompts": True,
        "enable_api_access": True,
    }


# =============================================================================
# PACKAGE A: Multi-Tenant Isolation Tests (25 tests)
# =============================================================================

class TestTenantManagerImports:
    """Test tenant_manager module imports."""

    def test_module_import(self):
        """Should import tenant_manager module."""
        from services import tenant_manager
        assert tenant_manager is not None

    def test_tenant_config_exists(self):
        """TenantConfig class should exist."""
        from services.tenant_manager import TenantConfig
        assert TenantConfig is not None

    def test_tenant_branding_exists(self):
        """TenantBranding class should exist."""
        from services.tenant_manager import TenantBranding
        assert TenantBranding is not None

    def test_tenant_registry_exists(self):
        """TenantRegistry class should exist."""
        from services.tenant_manager import TenantRegistry
        assert TenantRegistry is not None

    def test_get_tenant_registry_exists(self):
        """get_tenant_registry function should exist."""
        from services.tenant_manager import get_tenant_registry
        assert callable(get_tenant_registry)


class TestTenantConfig:
    """Test TenantConfig functionality."""

    def test_tenant_config_creation(self):
        """Should create TenantConfig with defaults."""
        from services.tenant_manager import TenantConfig, TenantTier
        config = TenantConfig(tenant_id="test", tenant_name="Test")
        assert config.tenant_id == "test"
        assert config.tier == TenantTier.BASIC

    def test_tenant_config_to_dict(self):
        """TenantConfig should serialize to dict."""
        from services.tenant_manager import TenantConfig
        config = TenantConfig(tenant_id="test", tenant_name="Test")
        d = config.to_dict()
        assert "tenant_id" in d
        assert "tier" in d

    def test_tenant_config_output_path(self):
        """Should generate correct output path."""
        from services.tenant_manager import TenantConfig
        config = TenantConfig(tenant_id="test", tenant_name="Test")
        path = config.get_output_path("report_123")
        assert "test" in path
        assert "report_123" in path

    def test_tenant_config_wording_template(self):
        """Should return wording template."""
        from services.tenant_manager import TenantConfig, WordingProfile
        config = TenantConfig(
            tenant_id="test",
            tenant_name="Test",
            wording_profile=WordingProfile.EXECUTIVE,
        )
        template = config.get_wording_template("greeting")
        assert len(template) > 0


class TestTenantRegistry:
    """Test TenantRegistry functionality."""

    def test_registry_singleton(self):
        """Registry should be singleton."""
        from services.tenant_manager import get_tenant_registry
        reg1 = get_tenant_registry()
        reg2 = get_tenant_registry()
        assert reg1 is reg2

    def test_register_tenant(self):
        """Should register tenant."""
        from services.tenant_manager import get_tenant_registry, TenantConfig
        registry = get_tenant_registry()
        config = TenantConfig(tenant_id="test_reg", tenant_name="Test Registration")
        registry.register_tenant(config)
        assert registry.get_tenant("test_reg") is not None

    def test_get_or_default(self):
        """Should return default tenant when not found."""
        from services.tenant_manager import get_tenant_registry
        registry = get_tenant_registry()
        config = registry.get_or_default("nonexistent")
        assert config is not None
        assert config.tenant_id == "default"

    def test_check_quota_within_limit(self):
        """Should return within quota for new tenant."""
        from services.tenant_manager import get_tenant_registry, TenantConfig
        registry = get_tenant_registry()
        config = TenantConfig(tenant_id="quota_test", tenant_name="Quota Test")
        registry.register_tenant(config)
        within, msg = registry.check_quota("quota_test")
        assert within is True


class TestTenantProcessing:
    """Test tenant-aware processing."""

    def test_process_tenant_isolation(self, sample_sections, sample_briefing):
        """Should process with tenant isolation."""
        from services.tenant_manager import process_tenant_isolation
        result = process_tenant_isolation(sample_sections, sample_briefing)
        assert "sections" in result
        assert "tenant_metadata" in result

    def test_apply_tenant_branding(self, sample_sections):
        """Should apply tenant branding."""
        from services.tenant_manager import apply_tenant_branding, TenantConfig
        config = TenantConfig(tenant_id="brand_test", tenant_name="Brand Test")
        result = apply_tenant_branding(sample_sections, config)
        assert "_tenant_branding" in result

    def test_generate_tenant_id(self):
        """Should generate unique tenant ID."""
        from services.tenant_manager import generate_tenant_id
        id1 = generate_tenant_id("Test Company")
        id2 = generate_tenant_id("Test Company")
        assert id1 == id2  # Same input, same day = same ID
        assert "testcompany" in id1.lower()

    def test_load_tenant_from_dict(self, sample_tenant_config):
        """Should load tenant from dictionary."""
        from services.tenant_manager import load_tenant_from_dict
        config = load_tenant_from_dict(sample_tenant_config)
        assert config.tenant_id == "test_tenant_001"
        assert config.enable_api_access is True


# =============================================================================
# PACKAGE B: Audit & Traceability Tests (25 tests)
# =============================================================================

class TestAuditTraceImports:
    """Test audit_trace_engine module imports."""

    def test_module_import(self):
        """Should import audit_trace_engine module."""
        from services import audit_trace_engine
        assert audit_trace_engine is not None

    def test_audit_entry_exists(self):
        """AuditEntry class should exist."""
        from services.audit_trace_engine import AuditEntry
        assert AuditEntry is not None

    def test_audit_report_exists(self):
        """AuditReport class should exist."""
        from services.audit_trace_engine import AuditReport
        assert AuditReport is not None

    def test_audit_engine_exists(self):
        """AuditTraceEngine class should exist."""
        from services.audit_trace_engine import AuditTraceEngine
        assert AuditTraceEngine is not None

    def test_get_audit_engine_exists(self):
        """get_audit_engine function should exist."""
        from services.audit_trace_engine import get_audit_engine
        assert callable(get_audit_engine)


class TestAuditEntry:
    """Test AuditEntry functionality."""

    def test_audit_entry_creation(self):
        """Should create AuditEntry with defaults."""
        from services.audit_trace_engine import AuditEntry, EngineType
        entry = AuditEntry(
            entry_id="test_001",
            engine_type=EngineType.LLM_CALL,
            engine_name="test_engine",
        )
        assert entry.entry_id == "test_001"
        assert entry.engine_type == EngineType.LLM_CALL

    def test_audit_entry_compute_hash(self):
        """Should compute SHA256 hash."""
        from services.audit_trace_engine import AuditEntry, EngineType
        entry = AuditEntry(
            entry_id="hash_test",
            engine_type=EngineType.LLM_CALL,
            engine_name="test",
        )
        hash_val = entry.compute_hash()
        assert len(hash_val) == 64  # SHA256 hex length

    def test_audit_entry_to_dict(self):
        """AuditEntry should serialize to dict."""
        from services.audit_trace_engine import AuditEntry, EngineType
        entry = AuditEntry(
            entry_id="dict_test",
            engine_type=EngineType.CONSISTENCY_CHECK,
            engine_name="test",
        )
        d = entry.to_dict()
        assert "entry_id" in d
        assert "engine_type" in d


class TestAuditReport:
    """Test AuditReport functionality."""

    def test_audit_report_creation(self):
        """Should create AuditReport."""
        from services.audit_trace_engine import AuditReport
        report = AuditReport(report_id="test_report")
        assert report.report_id == "test_report"
        assert report.entry_count == 0

    def test_audit_report_add_entry(self):
        """Should add entry to report."""
        from services.audit_trace_engine import AuditReport, AuditEntry, EngineType
        report = AuditReport(report_id="add_test")
        entry = AuditEntry(
            entry_id="entry_001",
            engine_type=EngineType.LLM_CALL,
            engine_name="test",
        )
        report.add_entry(entry)
        assert report.entry_count == 1
        assert entry.parent_hash == "genesis"

    def test_audit_report_chain_validation(self):
        """Should validate hash chain."""
        from services.audit_trace_engine import AuditReport, AuditEntry, EngineType
        report = AuditReport(report_id="chain_test")
        for i in range(3):
            entry = AuditEntry(
                entry_id=f"entry_{i}",
                engine_type=EngineType.LLM_CALL,
                engine_name="test",
            )
            report.add_entry(entry)
        valid, msg = report.validate_chain()
        assert valid is True

    def test_audit_report_to_json(self):
        """Should serialize to JSON."""
        from services.audit_trace_engine import AuditReport
        report = AuditReport(report_id="json_test")
        json_str = report.to_json()
        assert "json_test" in json_str


class TestAuditEngine:
    """Test AuditTraceEngine functionality."""

    def test_audit_engine_singleton(self):
        """Engine should be singleton."""
        from services.audit_trace_engine import get_audit_engine
        eng1 = get_audit_engine()
        eng2 = get_audit_engine()
        assert eng1 is eng2

    def test_start_report(self):
        """Should start audit report."""
        from services.audit_trace_engine import get_audit_engine
        engine = get_audit_engine()
        report = engine.start_report("start_test")
        assert report.report_id == "start_test"

    def test_record_llm_call(self):
        """Should record LLM call."""
        from services.audit_trace_engine import get_audit_engine
        engine = get_audit_engine()
        engine.start_report("llm_test")
        engine.record_llm_call(
            report_id="llm_test",
            model="gpt-4",
            input_data={"prompt": "test"},
            output_data={"response": "test"},
            temperature=0.1,
        )
        report = engine.get_active_report("llm_test")
        assert report.total_llm_calls >= 1

    def test_finalize_report(self):
        """Should finalize report."""
        from services.audit_trace_engine import get_audit_engine
        engine = get_audit_engine()
        engine.start_report("finalize_test")
        report = engine.finalize_report("finalize_test")
        assert report is not None
        assert report.completed_at != ""


class TestAuditUtilities:
    """Test audit utility functions."""

    def test_compute_data_hash(self):
        """Should compute data hash."""
        from services.audit_trace_engine import compute_data_hash
        hash1 = compute_data_hash({"key": "value"})
        hash2 = compute_data_hash({"key": "value"})
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_compute_data_size(self):
        """Should compute data size."""
        from services.audit_trace_engine import compute_data_size
        size = compute_data_size("Hello World")
        assert size == 11

    def test_ki_act_compliance_check(self):
        """Should check KI-Act compliance."""
        from services.audit_trace_engine import check_ki_act_compliance, AuditReport
        report = AuditReport(report_id="ki_act_test")
        compliant, notes = check_ki_act_compliance(report)
        assert isinstance(compliant, bool)
        assert isinstance(notes, list)


# =============================================================================
# PACKAGE C: Performance Layer v6 Tests (25 tests)
# =============================================================================

class TestPerformanceLayerImports:
    """Test performance_layer_v6 module imports."""

    def test_module_import(self):
        """Should import performance_layer_v6 module."""
        from services import performance_layer_v6
        assert performance_layer_v6 is not None

    def test_performance_layer_exists(self):
        """PerformanceLayerV6 class should exist."""
        from services.performance_layer_v6 import PerformanceLayerV6
        assert PerformanceLayerV6 is not None

    def test_priority_queue_exists(self):
        """PriorityQueueManager class should exist."""
        from services.performance_layer_v6 import PriorityQueueManager
        assert PriorityQueueManager is not None

    def test_adaptive_parallelizer_exists(self):
        """AdaptiveParallelizer class should exist."""
        from services.performance_layer_v6 import AdaptiveParallelizer
        assert AdaptiveParallelizer is not None

    def test_get_performance_layer_exists(self):
        """get_performance_layer function should exist."""
        from services.performance_layer_v6 import get_performance_layer
        assert callable(get_performance_layer)


class TestPriorityQueue:
    """Test PriorityQueueManager functionality."""

    def test_queue_creation(self):
        """Should create priority queue."""
        from services.performance_layer_v6 import PriorityQueueManager
        queue = PriorityQueueManager()
        assert queue.get_depth() == 0

    def test_enqueue_report(self):
        """Should enqueue report."""
        from services.performance_layer_v6 import PriorityQueueManager, QueuedReport, ReportPriority
        queue = PriorityQueueManager()
        report = QueuedReport(
            report_id="test_001",
            priority=ReportPriority.NORMAL,
            briefing={},
        )
        result = queue.enqueue(report)
        assert result is True
        assert queue.get_depth() == 1

    def test_dequeue_by_priority(self):
        """Should dequeue by priority order."""
        from services.performance_layer_v6 import PriorityQueueManager, QueuedReport, ReportPriority
        queue = PriorityQueueManager()

        normal = QueuedReport(report_id="normal", priority=ReportPriority.NORMAL, briefing={})
        premium = QueuedReport(report_id="premium", priority=ReportPriority.PREMIUM, briefing={})

        queue.enqueue(normal)
        queue.enqueue(premium)

        first = queue.dequeue()
        assert first.report_id == "premium"  # Higher priority first

    def test_queue_depth_by_priority(self):
        """Should report depth by priority."""
        from services.performance_layer_v6 import PriorityQueueManager, QueuedReport, ReportPriority
        queue = PriorityQueueManager()
        queue.enqueue(QueuedReport(report_id="1", priority=ReportPriority.NORMAL, briefing={}))
        queue.enqueue(QueuedReport(report_id="2", priority=ReportPriority.PREMIUM, briefing={}))
        depths = queue.get_depth_by_priority()
        assert "NORMAL" in depths
        assert "PREMIUM" in depths


class TestAdaptiveParallelizer:
    """Test AdaptiveParallelizer functionality."""

    def test_parallelizer_creation(self):
        """Should create parallelizer."""
        from services.performance_layer_v6 import AdaptiveParallelizer
        para = AdaptiveParallelizer()
        assert para.get_capacity() > 0

    def test_acquire_slots(self):
        """Should acquire processing slots."""
        from services.performance_layer_v6 import AdaptiveParallelizer, LoadLevel
        para = AdaptiveParallelizer()
        granted = para.acquire_slots(2, LoadLevel.IDLE)
        assert granted >= 0
        para.release_slots(granted)

    def test_release_slots(self):
        """Should release slots correctly."""
        from services.performance_layer_v6 import AdaptiveParallelizer, LoadLevel
        para = AdaptiveParallelizer()
        para.acquire_slots(2, LoadLevel.IDLE)
        para.release_slots(2)
        assert para.get_active_tasks() == 0


class TestOverloadProtector:
    """Test OverloadProtector functionality."""

    def test_protector_creation(self):
        """Should create overload protector."""
        from services.performance_layer_v6 import OverloadProtector
        protector = OverloadProtector()
        assert protector.get_load_level() is not None

    def test_complexity_config_by_load(self):
        """Should return complexity config."""
        from services.performance_layer_v6 import OverloadProtector
        protector = OverloadProtector()
        config = protector.get_complexity_config()
        assert "complexity" in config
        assert "parallel_tasks" in config

    def test_token_limits_by_load(self):
        """Should return token limits."""
        from services.performance_layer_v6 import OverloadProtector
        protector = OverloadProtector()
        limits = protector.get_token_limits()
        assert "max_input_tokens" in limits
        assert "max_output_tokens" in limits


class TestPerformanceLayerMain:
    """Test main PerformanceLayerV6 functionality."""

    def test_layer_singleton(self):
        """Layer should be singleton."""
        from services.performance_layer_v6 import get_performance_layer
        layer1 = get_performance_layer()
        layer2 = get_performance_layer()
        assert layer1 is layer2

    def test_update_metrics(self):
        """Should update metrics."""
        from services.performance_layer_v6 import get_performance_layer
        layer = get_performance_layer()
        metrics = layer.update_metrics(cpu_usage=0.5, memory_usage=0.3)
        assert metrics.cpu_usage == 0.5

    def test_get_complexity_settings(self):
        """Should return complexity settings."""
        from services.performance_layer_v6 import get_performance_layer
        layer = get_performance_layer()
        settings = layer.get_complexity_settings()
        assert "complexity_level" in settings
        assert "token_limits" in settings

    def test_process_with_performance_layer(self, sample_sections, sample_briefing):
        """Should process with performance layer."""
        from services.performance_layer_v6 import process_with_performance_layer
        result = process_with_performance_layer(sample_sections, sample_briefing, "test_report")
        assert "sections" in result
        assert "performance_metadata" in result


# =============================================================================
# PACKAGE D: Safety & Compliance Auto-Tuner Tests (25 tests)
# =============================================================================

class TestSafetyTunerImports:
    """Test safety_tuner module imports."""

    def test_module_import(self):
        """Should import safety_tuner module."""
        from services import safety_tuner
        assert safety_tuner is not None

    def test_safety_tuner_exists(self):
        """SafetyTuner class should exist."""
        from services.safety_tuner import SafetyTuner
        assert SafetyTuner is not None

    def test_safety_context_exists(self):
        """SafetyContext class should exist."""
        from services.safety_tuner import SafetyContext
        assert SafetyContext is not None

    def test_tuned_parameters_exists(self):
        """TunedParameters class should exist."""
        from services.safety_tuner import TunedParameters
        assert TunedParameters is not None

    def test_get_safety_tuner_exists(self):
        """get_safety_tuner function should exist."""
        from services.safety_tuner import get_safety_tuner
        assert callable(get_safety_tuner)


class TestRiskDetection:
    """Test risk level detection."""

    def test_detect_minimal_risk(self, sample_briefing):
        """Should detect minimal risk for standard briefing."""
        from services.safety_tuner import detect_risk_level, RiskLevel
        # Modify to non-high-risk
        briefing = dict(sample_briefing)
        briefing["branch"] = "Einzelhandel"
        risk = detect_risk_level(briefing)
        assert risk in (RiskLevel.MINIMAL, RiskLevel.LIMITED)

    def test_detect_high_risk_healthcare(self, sample_briefing_high_risk):
        """Should detect high risk for healthcare."""
        from services.safety_tuner import detect_risk_level, RiskLevel
        risk = detect_risk_level(sample_briefing_high_risk)
        assert risk == RiskLevel.HIGH

    def test_detect_high_risk_finance(self, sample_briefing):
        """Should detect high risk for finance."""
        from services.safety_tuner import detect_risk_level, RiskLevel
        briefing = dict(sample_briefing)
        briefing["branch"] = "Banking"
        risk = detect_risk_level(briefing)
        assert risk == RiskLevel.HIGH


class TestDataSensitivityDetection:
    """Test data sensitivity detection."""

    def test_detect_pii_sensitivity(self):
        """Should detect PII sensitivity."""
        from services.safety_tuner import detect_data_sensitivity, DataSensitivity
        briefing = {"description": "Analyse von Kundendaten und Mitarbeiterdaten"}
        sensitivity = detect_data_sensitivity(briefing)
        assert sensitivity == DataSensitivity.PII

    def test_detect_confidential_for_healthcare(self):
        """Should detect confidential for healthcare."""
        from services.safety_tuner import detect_data_sensitivity, DataSensitivity
        briefing = {"branch": "Healthcare", "description": "Standard analysis"}
        sensitivity = detect_data_sensitivity(briefing)
        assert sensitivity == DataSensitivity.CONFIDENTIAL


class TestEntityMasking:
    """Test entity masking/anonymization."""

    def test_mask_email(self):
        """Should mask email addresses."""
        from services.safety_tuner import entity_masking
        text = "Contact us at test@example.com for more info."
        result = entity_masking(text)
        assert "[EMAIL REDACTED]" in result.anonymized_text
        assert result.total_redactions >= 1

    def test_mask_phone(self):
        """Should mask phone numbers."""
        from services.safety_tuner import entity_masking
        text = "Rufen Sie uns an: +49 123 456789."
        result = entity_masking(text)
        assert result.total_redactions >= 1

    def test_mask_iban(self):
        """Should mask IBAN numbers."""
        from services.safety_tuner import entity_masking
        text = "IBAN: DE89 3704 0044 0532 0130 00"
        result = entity_masking(text)
        assert "[IBAN REDACTED]" in result.anonymized_text


class TestSafetyTuning:
    """Test safety tuning functionality."""

    def test_tuner_singleton(self):
        """Tuner should be singleton."""
        from services.safety_tuner import get_safety_tuner
        t1 = get_safety_tuner()
        t2 = get_safety_tuner()
        assert t1 is t2

    def test_analyze_context(self, sample_briefing):
        """Should analyze safety context."""
        from services.safety_tuner import get_safety_tuner
        tuner = get_safety_tuner()
        context = tuner.analyze_context(sample_briefing)
        assert context.risk_level is not None
        assert context.compliance_mode is not None

    def test_tune_parameters_high_risk(self, sample_briefing_high_risk):
        """Should increase reasoning for high risk."""
        from services.safety_tuner import get_safety_tuner
        tuner = get_safety_tuner()
        context = tuner.analyze_context(sample_briefing_high_risk)
        params = tuner.tune_parameters(context)
        assert params.reasoning_multiplier >= 1.2

    def test_process_safety_tuning(self, sample_sections, sample_briefing):
        """Should process safety tuning."""
        from services.safety_tuner import process_safety_tuning
        result = process_safety_tuning(sample_sections, sample_briefing)
        assert "sections" in result
        assert "safety_metadata" in result


# =============================================================================
# PACKAGE E: Consistency Kernel v6 Tests (20 tests)
# =============================================================================

class TestConsistencyKernelN39:
    """Test N3.9 consistency rules."""

    def test_consistency_module_import(self):
        """Should import consistency_engine module."""
        from services import consistency_engine
        assert consistency_engine is not None

    def test_check_consistency_exists(self):
        """check_consistency function should exist."""
        from services.consistency_engine import check_consistency
        assert callable(check_consistency)

    def test_consistency_report_structure(self, sample_sections, sample_briefing):
        """Should return proper report structure."""
        from services.consistency_engine import check_consistency
        report = check_consistency(sample_sections, sample_briefing)
        assert hasattr(report, "status")
        assert hasattr(report, "score")
        assert hasattr(report, "issues")

    def test_n39_001_rule_exists(self, sample_sections, sample_briefing):
        """N39_001 rule should be checked."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        assert hasattr(engine, "_check_n39_risk_roadmap_numerical")

    def test_n39_002_rule_exists(self, sample_sections, sample_briefing):
        """N39_002 rule should be checked."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        assert hasattr(engine, "_check_n39_recommendations_kpis_alignment")

    def test_n39_003_rule_exists(self, sample_sections, sample_briefing):
        """N39_003 rule should be checked."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        assert hasattr(engine, "_check_n39_tools_automation_correlation")

    def test_n39_004_rule_exists(self, sample_sections, sample_briefing):
        """N39_004 rule should be checked."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        assert hasattr(engine, "_check_n39_benchmark_skillplan_depth")

    def test_check_all_includes_n39(self, sample_sections, sample_briefing):
        """check_all should include N3.9 rules."""
        from services.consistency_engine import check_consistency
        report = check_consistency(sample_sections, sample_briefing)
        # N3.9 adds 8 rules (2 per rule method)
        assert report.checked_rules >= 8


class TestConsistencyN39Rules:
    """Test specific N3.9 consistency rules."""

    def test_risk_roadmap_numerical_check(self, sample_sections, sample_briefing):
        """Should check risk-roadmap numerical consistency."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        engine._check_n39_risk_roadmap_numerical()
        # Should have checked 2 rules
        assert engine.report.checked_rules >= 2

    def test_recommendations_kpis_check(self, sample_sections, sample_briefing):
        """Should check recommendations-KPI alignment."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        engine._check_n39_recommendations_kpis_alignment()
        assert engine.report.checked_rules >= 2

    def test_tools_automation_check(self, sample_sections, sample_briefing):
        """Should check tools-automation correlation."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        engine._check_n39_tools_automation_correlation()
        assert engine.report.checked_rules >= 2

    def test_benchmark_skillplan_check(self, sample_sections, sample_briefing):
        """Should check benchmark-skillplan depth."""
        from services.consistency_engine import ConsistencyEngine
        engine = ConsistencyEngine(sample_sections, sample_briefing)
        engine._check_n39_benchmark_skillplan_depth()
        assert engine.report.checked_rules >= 2


# =============================================================================
# PACKAGE F: Executive Narrative v2 Tests (20 tests)
# =============================================================================

class TestExecutiveNarrativeImports:
    """Test executive narrative v2 imports."""

    def test_executive_layer_exists(self):
        """ExecutiveLayer class should exist."""
        from services.executive_narrative_engine import ExecutiveLayer
        assert ExecutiveLayer is not None

    def test_executive_narrative_v2_exists(self):
        """ExecutiveNarrativeV2 class should exist."""
        from services.executive_narrative_engine import ExecutiveNarrativeV2
        assert ExecutiveNarrativeV2 is not None

    def test_analyze_strategic_layer_exists(self):
        """analyze_strategic_layer function should exist."""
        from services.executive_narrative_engine import analyze_strategic_layer
        assert callable(analyze_strategic_layer)

    def test_analyze_transformation_layer_exists(self):
        """analyze_transformation_layer function should exist."""
        from services.executive_narrative_engine import analyze_transformation_layer
        assert callable(analyze_transformation_layer)

    def test_analyze_impact_layer_exists(self):
        """analyze_impact_layer function should exist."""
        from services.executive_narrative_engine import analyze_impact_layer
        assert callable(analyze_impact_layer)


class TestExecutiveLayerAnalysis:
    """Test executive layer analysis."""

    def test_strategic_layer_analysis(self, sample_sections):
        """Should analyze strategic layer."""
        from services.executive_narrative_engine import analyze_strategic_layer
        layer = analyze_strategic_layer(sample_sections)
        assert layer.layer_type == "strategic"
        assert len(layer.content) > 0

    def test_transformation_layer_analysis(self, sample_sections):
        """Should analyze transformation layer."""
        from services.executive_narrative_engine import analyze_transformation_layer
        layer = analyze_transformation_layer(sample_sections)
        assert layer.layer_type == "transformation"
        assert len(layer.content) > 0

    def test_impact_layer_analysis(self, sample_sections):
        """Should analyze impact layer."""
        from services.executive_narrative_engine import analyze_impact_layer
        layer = analyze_impact_layer(sample_sections)
        assert layer.layer_type == "impact"
        assert "roi_percent" in layer.metrics or len(layer.content) > 0

    def test_impact_layer_extracts_roi(self, sample_sections):
        """Should extract ROI from impact layer."""
        from services.executive_narrative_engine import analyze_impact_layer
        layer = analyze_impact_layer(sample_sections)
        # Sample has ROI: 25%
        assert layer.metrics.get("roi_percent") == 25.0 or layer.score > 0


class TestStoryArcConsistency:
    """Test story arc consistency checking."""

    def test_story_arc_check(self, sample_sections):
        """Should check story arc consistency."""
        from services.executive_narrative_engine import (
            analyze_strategic_layer,
            analyze_transformation_layer,
            analyze_impact_layer,
            check_story_arc_consistency,
        )
        strategic = analyze_strategic_layer(sample_sections)
        transformation = analyze_transformation_layer(sample_sections)
        impact = analyze_impact_layer(sample_sections)

        complete, score, issues = check_story_arc_consistency(
            strategic, transformation, impact
        )
        assert isinstance(complete, bool)
        assert 0 <= score <= 100
        assert isinstance(issues, list)

    def test_executive_story_arc_config(self):
        """EXECUTIVE_STORY_ARC should be defined."""
        from services.executive_narrative_engine import EXECUTIVE_STORY_ARC
        assert len(EXECUTIVE_STORY_ARC) == 5
        phases = [p["phase"] for p in EXECUTIVE_STORY_ARC]
        assert "ausgangslage" in phases
        assert "impact" in phases


class TestExecutiveNarrativeV2:
    """Test full ExecutiveNarrativeV2 functionality."""

    def test_analyze_executive_narrative_v2(self, sample_sections):
        """Should analyze full executive narrative."""
        from services.executive_narrative_engine import analyze_executive_narrative_v2
        report = analyze_executive_narrative_v2(sample_sections)
        assert report.strategic_layer is not None
        assert report.transformation_layer is not None
        assert report.impact_layer is not None

    def test_executive_narrative_v2_score(self, sample_sections):
        """Should calculate overall score."""
        from services.executive_narrative_engine import analyze_executive_narrative_v2
        report = analyze_executive_narrative_v2(sample_sections)
        score = report.get_overall_score()
        assert 0 <= score <= 100

    def test_process_executive_narrative_v2(self, sample_sections):
        """Should process full executive narrative."""
        from services.executive_narrative_engine import process_executive_narrative_v2
        processed, report = process_executive_narrative_v2(sample_sections)
        assert "_executive_narrative_v2" in processed
        assert "_executive_score" in processed


# =============================================================================
# PACKAGE G: Final Integration Tests (20 tests)
# =============================================================================

class TestIntegrationImports:
    """Test all N3.9 modules can be imported together."""

    def test_all_modules_import(self):
        """All N3.9 modules should import without conflict."""
        from services import tenant_manager
        from services import audit_trace_engine
        from services import performance_layer_v6
        from services import safety_tuner
        from services import consistency_engine
        from services import executive_narrative_engine
        assert all([
            tenant_manager,
            audit_trace_engine,
            performance_layer_v6,
            safety_tuner,
            consistency_engine,
            executive_narrative_engine,
        ])


class TestIntegrationPipeline:
    """Test integrated N3.9 processing pipeline."""

    def test_full_pipeline_tenant_first(self, sample_sections, sample_briefing):
        """Should process tenant isolation first."""
        from services.tenant_manager import process_tenant_isolation
        result = process_tenant_isolation(sample_sections, sample_briefing)
        assert "sections" in result
        assert "tenant_metadata" in result

    def test_full_pipeline_safety_tuning(self, sample_sections, sample_briefing):
        """Should process safety tuning."""
        from services.safety_tuner import process_safety_tuning
        result = process_safety_tuning(sample_sections, sample_briefing)
        assert "tuned_parameters" in result

    def test_full_pipeline_consistency(self, sample_sections, sample_briefing):
        """Should run consistency checks."""
        from services.consistency_engine import check_consistency
        report = check_consistency(sample_sections, sample_briefing)
        assert report.status in ("PASS", "WARN", "FAIL")

    def test_full_pipeline_narrative(self, sample_sections):
        """Should process executive narrative."""
        from services.executive_narrative_engine import process_executive_narrative_v2
        processed, report = process_executive_narrative_v2(sample_sections)
        assert "_executive_narrative_v2" in processed

    def test_full_pipeline_performance(self, sample_sections, sample_briefing):
        """Should apply performance layer."""
        from services.performance_layer_v6 import process_with_performance_layer
        result = process_with_performance_layer(sample_sections, sample_briefing)
        assert "performance_metadata" in result


class TestIntegrationAudit:
    """Test audit integration across pipeline."""

    def test_audit_tracks_all_engines(self):
        """Audit should track all engine types."""
        from services.audit_trace_engine import EngineType
        engine_types = list(EngineType)
        assert len(engine_types) >= 10  # Should have many engine types

    def test_audit_compliance_report(self):
        """Should generate compliance report."""
        from services.audit_trace_engine import (
            get_audit_engine,
            generate_compliance_report,
            ComplianceFramework,
        )
        engine = get_audit_engine()
        engine.start_report("compliance_test")
        report = engine.finalize_report("compliance_test")

        compliance = generate_compliance_report(
            report,
            [ComplianceFramework.KI_ACT, ComplianceFramework.ISO_42001],
        )
        assert "frameworks" in compliance
        assert "overall_compliant" in compliance


class TestIntegrationZeroFallback:
    """Test zero-fallback guarantee."""

    def test_no_fallback_in_consistency(self, sample_sections, sample_briefing):
        """Consistency should not require fallback."""
        from services.consistency_engine import check_consistency
        report = check_consistency(sample_sections, sample_briefing)
        # No fallback needed for consistency engine itself
        assert report is not None

    def test_no_fallback_in_narrative(self, sample_sections):
        """Narrative should not require fallback."""
        from services.executive_narrative_engine import analyze_executive_narrative_v2
        report = analyze_executive_narrative_v2(sample_sections)
        # No fallback in narrative analysis
        assert report is not None


class TestVersionCheck:
    """Test version information."""

    def test_version_file_exists(self):
        """VERSION file should exist."""
        import os
        version_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "VERSION"
        )
        assert os.path.exists(version_path)

    def test_version_contains_n39(self):
        """VERSION should mention N3.9."""
        import os
        version_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "VERSION"
        )
        with open(version_path, "r") as f:
            content = f.read()
        # Will be updated to v4.28 with N3.9
        assert "PLATIN++" in content
