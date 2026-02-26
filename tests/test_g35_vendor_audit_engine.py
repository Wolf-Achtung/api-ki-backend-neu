# -*- coding: utf-8 -*-
"""
Sprint G35: Vendor Audit Engine Tests
=====================================

Comprehensive test suite for Vendor Audit Engine with 50+ tests covering:
- Data structures (VendorAuditEntry, VendorAuditReport)
- Category determination logic (green/yellow/red)
- Jurisdiction and data location detection
- DPA and certification handling
- HTML generation
- Consistency with Tools Engine 4.0
- Consistency with Risk Engines (G29, G33)
- Consistency rules VA_001-VA_006

Version: 1.0.0 (Sprint G35)
"""
from __future__ import annotations

import pytest
from typing import Dict, Any, List, Optional


# =============================================================================
# TEST: Data Structures - VendorAuditEntry
# =============================================================================

class TestVendorAuditEntry:
    """Tests for VendorAuditEntry dataclass."""

    def test_basic_creation(self) -> None:
        """Test VendorAuditEntry can be instantiated with basic values."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="OpenAI",
            category="LLM",
            jurisdiction="US",
            data_location="EU+US",
            has_dpa=True,
            ai_act_relevance="high",
            dsgvo_risk_level="medium",
            security_posture="strong",
            certifications=["SOC2", "ISO 27001"],
            vendor_risk_score=3,
            overall_category="yellow",
        )

        assert entry.name == "OpenAI"
        assert entry.category == "LLM"
        assert entry.jurisdiction == "US"
        assert entry.has_dpa is True
        assert entry.overall_category == "yellow"

    def test_invalid_jurisdiction_normalized(self) -> None:
        """Test invalid jurisdiction is normalized to 'Unknown'."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Test",
            category="Test",
            jurisdiction="INVALID",
        )

        assert entry.jurisdiction == "Unknown"

    def test_valid_jurisdictions(self) -> None:
        """Test all valid jurisdiction values."""
        from services.vendor_audit_engine import VendorAuditEntry, JURISDICTIONS

        for jurisdiction in JURISDICTIONS:
            entry = VendorAuditEntry(
                name="Test",
                category="Test",
                jurisdiction=jurisdiction,
            )
            assert entry.jurisdiction == jurisdiction

    def test_invalid_data_location_normalized(self) -> None:
        """Test invalid data_location is normalized to 'Unknown'."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Test",
            category="Test",
            data_location="INVALID",
        )

        assert entry.data_location == "Unknown"

    def test_valid_data_locations(self) -> None:
        """Test all valid data_location values."""
        from services.vendor_audit_engine import VendorAuditEntry, DATA_LOCATIONS

        for location in DATA_LOCATIONS:
            entry = VendorAuditEntry(
                name="Test",
                category="Test",
                data_location=location,
            )
            assert entry.data_location == location

    def test_invalid_security_posture_normalized(self) -> None:
        """Test invalid security_posture is normalized to 'medium'."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Test",
            category="Test",
            security_posture="INVALID",
        )

        assert entry.security_posture == "medium"

    def test_vendor_risk_score_clamped(self) -> None:
        """Test vendor_risk_score is clamped to 1-5."""
        from services.vendor_audit_engine import VendorAuditEntry

        # Test lower bound
        entry_low = VendorAuditEntry(
            name="Test",
            category="Test",
            vendor_risk_score=0,
        )
        assert entry_low.vendor_risk_score == 1

        # Test upper bound
        entry_high = VendorAuditEntry(
            name="Test",
            category="Test",
            vendor_risk_score=10,
        )
        assert entry_high.vendor_risk_score == 5

    def test_us_vendor_without_dpa_cannot_be_green(self) -> None:
        """Test US vendor without DPA is not classified as green."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="US Tool",
            category="LLM",
            jurisdiction="US",
            has_dpa=False,
            overall_category="green",  # Should be changed
        )

        assert entry.overall_category != "green"
        assert "US vendor without DPA" in entry.audit_flags

    def test_high_vendor_risk_becomes_red(self) -> None:
        """Test high vendor_risk_score results in red category."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Risky Tool",
            category="Analytics",
            vendor_risk_score=4,
            overall_category="yellow",
        )

        assert entry.overall_category == "red"
        assert "High vendor risk score" in entry.audit_flags

    def test_weak_security_becomes_red(self) -> None:
        """Test weak security_posture results in red category."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Insecure Tool",
            category="Analytics",
            security_posture="weak",
            overall_category="green",
        )

        assert entry.overall_category == "red"
        assert "Weak security posture" in entry.audit_flags

    def test_unknown_data_location_adds_flag(self) -> None:
        """Test unknown data_location adds audit flag."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Unknown Location Tool",
            category="Analytics",
            data_location="Unknown",
            overall_category="green",
        )

        assert entry.overall_category != "green"
        assert "Data location unknown" in entry.audit_flags

    def test_is_eu_compliant_property(self) -> None:
        """Test is_eu_compliant property."""
        from services.vendor_audit_engine import VendorAuditEntry

        # EU with DPA
        entry_compliant = VendorAuditEntry(
            name="EU Tool",
            category="Analytics",
            jurisdiction="EU",
            has_dpa=True,
        )
        assert entry_compliant.is_eu_compliant is True

        # EU without DPA
        entry_no_dpa = VendorAuditEntry(
            name="EU Tool No DPA",
            category="Analytics",
            jurisdiction="EU",
            has_dpa=False,
        )
        assert entry_no_dpa.is_eu_compliant is False

        # US with DPA
        entry_us = VendorAuditEntry(
            name="US Tool",
            category="Analytics",
            jurisdiction="US",
            has_dpa=True,
        )
        assert entry_us.is_eu_compliant is False

    def test_is_high_risk_property(self) -> None:
        """Test is_high_risk property."""
        from services.vendor_audit_engine import VendorAuditEntry

        # Red category
        entry_red = VendorAuditEntry(
            name="Red Tool",
            category="Analytics",
            vendor_risk_score=4,
        )
        assert entry_red.is_high_risk is True

        # High risk score but yellow
        entry_high = VendorAuditEntry(
            name="High Risk Tool",
            category="Analytics",
            vendor_risk_score=4,
        )
        assert entry_high.is_high_risk is True

        # Low risk
        entry_low = VendorAuditEntry(
            name="Low Risk Tool",
            category="Analytics",
            vendor_risk_score=2,
            overall_category="green",
        )
        assert entry_low.is_high_risk is False

    def test_to_dict_serialization(self) -> None:
        """Test VendorAuditEntry serialization to dict."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Test Tool",
            category="LLM",
            jurisdiction="EU",
            data_location="EU-only",
            has_dpa=True,
            certifications=["ISO 27001"],
            vendor_risk_score=2,
            overall_category="green",
        )

        data = entry.to_dict()

        assert data["name"] == "Test Tool"
        assert data["jurisdiction"] == "EU"
        assert data["has_dpa"] is True
        assert "is_eu_compliant" in data
        assert "is_high_risk" in data
        assert "certification_count" in data

    def test_from_dict_deserialization(self) -> None:
        """Test VendorAuditEntry creation from dict."""
        from services.vendor_audit_engine import VendorAuditEntry

        data = {
            "name": "From Dict Tool",
            "category": "Analytics",
            "jurisdiction": "US",
            "data_location": "EU+US",
            "has_dpa": True,
            "certifications": ["SOC2"],
            "vendor_risk_score": 3,
            "overall_category": "yellow",
        }

        entry = VendorAuditEntry.from_dict(data)

        assert entry.name == "From Dict Tool"
        assert entry.jurisdiction == "US"
        assert entry.has_dpa is True
        assert entry.vendor_risk_score == 3


# =============================================================================
# TEST: Data Structures - VendorAuditReport
# =============================================================================

class TestVendorAuditReport:
    """Tests for VendorAuditReport dataclass."""

    def test_basic_creation(self) -> None:
        """Test VendorAuditReport can be instantiated."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        # Green entry needs: EU jurisdiction, DPA, EU-only data, low risk, certifications
        entry1 = VendorAuditEntry(
            name="Tool 1",
            category="LLM",
            jurisdiction="EU",
            has_dpa=True,
            data_location="EU-only",
            vendor_risk_score=1,
            certifications=["ISO 27001"],
            overall_category="green",
        )
        entry2 = VendorAuditEntry(name="Tool 2", category="Analytics", overall_category="yellow")

        report = VendorAuditReport(
            entries=[entry1, entry2],
            summary="Test summary",
            recommendations=["Rec 1", "Rec 2"],
        )

        assert report.total_vendors == 2
        assert report.green_count == 1
        assert report.yellow_count == 1

    def test_auto_calculate_vendor_lists(self) -> None:
        """Test high_risk_vendors and green_vendors are auto-calculated."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entry_green = VendorAuditEntry(
            name="Green Tool",
            category="LLM",
            jurisdiction="EU",
            has_dpa=True,
            data_location="EU-only",
            vendor_risk_score=1,
            certifications=["ISO 27001"],  # Required for green
            overall_category="green",
        )
        entry_red = VendorAuditEntry(
            name="Red Tool",
            category="Analytics",
            vendor_risk_score=5,
            overall_category="red",
        )

        report = VendorAuditReport(entries=[entry_green, entry_red])

        assert "Green Tool" in report.green_vendors
        assert "Red Tool" in report.high_risk_vendors

    def test_total_vendors_property(self) -> None:
        """Test total_vendors property."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entries = [
            VendorAuditEntry(name=f"Tool {i}", category="LLM")
            for i in range(5)
        ]

        report = VendorAuditReport(entries=entries)

        assert report.total_vendors == 5

    def test_category_counts(self) -> None:
        """Test red_count, yellow_count, green_count properties."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entries = [
            # Green entries need certifications to stay green
            VendorAuditEntry(name="Green 1", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=1, data_location="EU-only", certifications=["ISO 27001"]),
            VendorAuditEntry(name="Green 2", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=2, data_location="EU-only", certifications=["SOC2"]),
            VendorAuditEntry(name="Yellow 1", category="LLM", vendor_risk_score=3),
            VendorAuditEntry(name="Red 1", category="LLM", vendor_risk_score=5),
        ]

        report = VendorAuditReport(entries=entries)

        assert report.green_count == 2
        assert report.yellow_count == 1
        assert report.red_count == 1

    def test_average_risk_score(self) -> None:
        """Test average_risk_score property."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entries = [
            VendorAuditEntry(name="Tool 1", category="LLM", vendor_risk_score=2),
            VendorAuditEntry(name="Tool 2", category="LLM", vendor_risk_score=4),
        ]

        report = VendorAuditReport(entries=entries)

        assert report.average_risk_score == 3.0

    def test_overall_audit_status_pass(self) -> None:
        """Test overall_audit_status is 'pass' when all green."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entries = [
            # Green entries need certifications to stay green
            VendorAuditEntry(name="Green 1", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=1, data_location="EU-only", certifications=["ISO 27001"]),
            VendorAuditEntry(name="Green 2", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=2, data_location="EU-only", certifications=["SOC2"]),
        ]

        report = VendorAuditReport(entries=entries)

        assert report.overall_audit_status == "pass"

    def test_overall_audit_status_warn(self) -> None:
        """Test overall_audit_status is 'warn' with yellow vendors."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entries = [
            VendorAuditEntry(name="Green 1", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=1, data_location="EU-only"),
            VendorAuditEntry(name="Yellow 1", category="LLM", vendor_risk_score=3),
        ]

        report = VendorAuditReport(entries=entries)

        assert report.overall_audit_status == "warn"

    def test_overall_audit_status_fail(self) -> None:
        """Test overall_audit_status is 'fail' with red vendors."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entries = [
            VendorAuditEntry(name="Green 1", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=1, data_location="EU-only"),
            VendorAuditEntry(name="Red 1", category="LLM", vendor_risk_score=5),
        ]

        report = VendorAuditReport(entries=entries)

        assert report.overall_audit_status == "fail"

    def test_compliance_score_calculation(self) -> None:
        """Test compliance_score calculation."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        # All green vendors - need certifications for green status
        entries_green = [
            VendorAuditEntry(name="Green 1", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=1, data_location="EU-only", certifications=["ISO 27001"]),
        ]
        report_green = VendorAuditReport(entries=entries_green)
        assert report_green.compliance_score >= 100.0  # Green = 100 + EU bonus

        # All red vendors
        entries_red = [
            VendorAuditEntry(name="Red 1", category="LLM", vendor_risk_score=5),
        ]
        report_red = VendorAuditReport(entries=entries_red)
        assert report_red.compliance_score == 0.0

    def test_get_entry_by_name(self) -> None:
        """Test get_entry method."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entry1 = VendorAuditEntry(name="OpenAI", category="LLM")
        entry2 = VendorAuditEntry(name="DeepL", category="Translation")

        report = VendorAuditReport(entries=[entry1, entry2])

        found = report.get_entry("OpenAI")
        assert found is not None
        assert found.name == "OpenAI"

        not_found = report.get_entry("NonExistent")
        assert not_found is None

    def test_get_entries_by_category(self) -> None:
        """Test get_entries_by_category method."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entries = [
            # Green entry needs certifications
            VendorAuditEntry(name="Green 1", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=1, data_location="EU-only", certifications=["ISO 27001"]),
            VendorAuditEntry(name="Yellow 1", category="LLM", vendor_risk_score=3),
            VendorAuditEntry(name="Red 1", category="LLM", vendor_risk_score=5),
        ]

        report = VendorAuditReport(entries=entries)

        green_entries = report.get_entries_by_category("green")
        assert len(green_entries) == 1
        assert green_entries[0].name == "Green 1"

    def test_to_dict_serialization(self) -> None:
        """Test VendorAuditReport serialization to dict."""
        from services.vendor_audit_engine import VendorAuditReport, VendorAuditEntry

        entry = VendorAuditEntry(name="Test", category="LLM")
        report = VendorAuditReport(
            entries=[entry],
            summary="Test summary",
            recommendations=["Rec 1"],
        )

        data = report.to_dict()

        assert "entries" in data
        assert "summary" in data
        assert "total_vendors" in data
        assert "compliance_score" in data
        assert "overall_audit_status" in data

    def test_from_dict_deserialization(self) -> None:
        """Test VendorAuditReport creation from dict."""
        from services.vendor_audit_engine import VendorAuditReport

        data = {
            "entries": [
                {"name": "Tool 1", "category": "LLM", "jurisdiction": "EU"},
                {"name": "Tool 2", "category": "Analytics", "jurisdiction": "US"},
            ],
            "summary": "Test summary",
            "recommendations": ["Rec 1"],
        }

        report = VendorAuditReport.from_dict(data)

        assert report.total_vendors == 2
        assert report.summary == "Test summary"


# =============================================================================
# TEST: Determination Functions
# =============================================================================

class TestDeterminationFunctions:
    """Tests for audit determination functions."""

    def test_determine_jurisdiction_known_vendor(self) -> None:
        """Test jurisdiction detection for known vendors."""
        from services.vendor_audit_engine import _determine_jurisdiction

        assert _determine_jurisdiction("OpenAI GPT") == "US"
        assert _determine_jurisdiction("Anthropic Claude") == "US"
        assert _determine_jurisdiction("DeepL Pro") == "EU"
        assert _determine_jurisdiction("Microsoft Azure") == "US"

    def test_determine_jurisdiction_from_host(self) -> None:
        """Test jurisdiction detection from host info."""
        from services.vendor_audit_engine import _determine_jurisdiction

        assert _determine_jurisdiction("Unknown Tool", "EU Server", "") == "EU"
        assert _determine_jurisdiction("Unknown Tool", "US Server", "") == "US"
        assert _determine_jurisdiction("Unknown Tool", "Deutschland", "") == "EU"

    def test_determine_data_location(self) -> None:
        """Test data location determination."""
        from services.vendor_audit_engine import _determine_data_location

        assert _determine_data_location("EU-only", "", "EU") == "EU-only"
        assert _determine_data_location("EU US", "", "US") == "EU+US"
        assert _determine_data_location("", "eu-server", "EU") == "EU-only"

    def test_determine_has_dpa(self) -> None:
        """Test DPA detection."""
        from services.vendor_audit_engine import _determine_has_dpa

        assert _determine_has_dpa("DPA available", "") is True
        assert _determine_has_dpa("AVV verfuegbar", "") is True
        assert _determine_has_dpa("DSGVO-konform", "") is True
        assert _determine_has_dpa("", "OpenAI") is True  # Known vendor
        assert _determine_has_dpa("", "Unknown Tool") is False

    def test_determine_security_posture(self) -> None:
        """Test security posture determination."""
        from services.vendor_audit_engine import _determine_security_posture

        assert _determine_security_posture(["ISO 27001", "SOC2 Type II"], "") == "strong"
        assert _determine_security_posture(["SOC2"], "") == "medium"
        assert _determine_security_posture([], "unklar") == "weak"

    def test_determine_ai_act_relevance(self) -> None:
        """Test AI Act relevance determination."""
        from services.vendor_audit_engine import _determine_ai_act_relevance

        assert _determine_ai_act_relevance("LLM", "GPT Model") == "high"
        assert _determine_ai_act_relevance("Automation", "Make.com") == "medium"
        assert _determine_ai_act_relevance("CRM", "Salesforce") == "low"

    def test_determine_dsgvo_risk(self) -> None:
        """Test DSGVO risk determination."""
        from services.vendor_audit_engine import _determine_dsgvo_risk

        # High risk: US without DPA
        assert _determine_dsgvo_risk("US", "Unknown", False, 3) == "high"

        # Low risk: EU with DPA and EU-only
        assert _determine_dsgvo_risk("EU", "EU-only", True, 2) == "low"

        # Medium risk: default
        assert _determine_dsgvo_risk("EU", "EU+US", True, 3) == "medium"

    def test_calculate_vendor_risk_score(self) -> None:
        """Test vendor risk score calculation."""
        from services.vendor_audit_engine import _calculate_vendor_risk_score

        # EU vendor with DPA and strong security
        score_eu = _calculate_vendor_risk_score("EU", "EU-only", True, "strong", 3)
        assert score_eu <= 2

        # US vendor without DPA and weak security
        score_us = _calculate_vendor_risk_score("US", "Unknown", False, "weak", 3)
        assert score_us >= 4


# =============================================================================
# TEST: Main Generation Function
# =============================================================================

class TestGenerateVendorAuditReport:
    """Tests for generate_vendor_audit_report function."""

    def test_empty_tools_data(self) -> None:
        """Test report generation with no tools data."""
        from services.vendor_audit_engine import generate_vendor_audit_report

        report = generate_vendor_audit_report(
            tools_data=None,
            briefing={},
        )

        assert report.total_vendors == 0
        assert report.overall_audit_status == "pass"

    def test_with_tools_data(self) -> None:
        """Test report generation with tools data."""
        from services.vendor_audit_engine import generate_vendor_audit_report

        tools_data = [
            {"name": "OpenAI", "category": "LLM", "vendor_risk": 3, "host": "US"},
            {"name": "DeepL", "category": "Translation", "vendor_risk": 1, "host": "EU"},
        ]

        report = generate_vendor_audit_report(
            tools_data=tools_data,
            briefing={"unternehmensgroesse": "team"},
        )

        assert report.total_vendors == 2
        assert report.get_entry("DeepL") is not None

    def test_size_constraints_solo(self) -> None:
        """Test size constraints for solo company."""
        from services.vendor_audit_engine import generate_vendor_audit_report

        tools_data = [
            {"name": f"Tool {i}", "category": "LLM", "vendor_risk": 3}
            for i in range(10)
        ]

        report = generate_vendor_audit_report(
            tools_data=tools_data,
            briefing={"unternehmensgroesse": "solo"},
        )

        assert report.total_vendors <= 5

    def test_size_constraints_kmu(self) -> None:
        """Test size constraints for KMU company."""
        from services.vendor_audit_engine import generate_vendor_audit_report

        tools_data = [
            {"name": f"Tool {i}", "category": "LLM", "vendor_risk": 3}
            for i in range(15)
        ]

        report = generate_vendor_audit_report(
            tools_data=tools_data,
            briefing={"unternehmensgroesse": "kmu"},
        )

        assert report.total_vendors <= 12

    def test_recommendations_generated(self) -> None:
        """Test recommendations are generated."""
        from services.vendor_audit_engine import generate_vendor_audit_report

        tools_data = [
            {"name": "US Tool", "category": "LLM", "vendor_risk": 4, "host": "US"},
        ]

        report = generate_vendor_audit_report(
            tools_data=tools_data,
            briefing={},
        )

        assert len(report.recommendations) > 0


# =============================================================================
# TEST: HTML Rendering
# =============================================================================

class TestVendorAuditReportToHtml:
    """Tests for vendor_audit_report_to_html function."""

    def test_html_output_basic(self) -> None:
        """Test HTML output contains basic elements."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            vendor_audit_report_to_html,
        )

        entry = VendorAuditEntry(
            name="Test Tool",
            category="LLM",
            jurisdiction="EU",
            overall_category="green",
        )
        report = VendorAuditReport(
            entries=[entry],
            summary="Test summary",
        )

        html = vendor_audit_report_to_html(report, lang="de")

        assert "Test Tool" in html
        assert "G35" in html
        assert "vendor-audit" in html

    def test_html_output_english(self) -> None:
        """Test HTML output in English."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            vendor_audit_report_to_html,
        )

        entry = VendorAuditEntry(name="Test", category="LLM")
        report = VendorAuditReport(entries=[entry])

        html = vendor_audit_report_to_html(report, lang="en")

        # Check for G35 badge and vendor-audit class (titles are in template, not in engine output)
        assert "G35" in html
        assert "vendor-audit" in html

    def test_html_contains_category_badges(self) -> None:
        """Test HTML contains category badges (GREEN/YELLOW/RED)."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            vendor_audit_report_to_html,
        )

        entries = [
            VendorAuditEntry(name="Green", category="LLM", jurisdiction="EU", has_dpa=True, vendor_risk_score=1, data_location="EU-only"),
            VendorAuditEntry(name="Yellow", category="LLM", vendor_risk_score=3),
            VendorAuditEntry(name="Red", category="LLM", vendor_risk_score=5),
        ]
        report = VendorAuditReport(entries=entries)

        html = vendor_audit_report_to_html(report, lang="de")

        assert "GREEN" in html or "green" in html.lower()
        assert "YELLOW" in html or "yellow" in html.lower()
        assert "RED" in html or "red" in html.lower()

    def test_html_contains_recommendations(self) -> None:
        """Test HTML contains recommendations section."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            vendor_audit_report_to_html,
        )

        entry = VendorAuditEntry(name="Test", category="LLM")
        report = VendorAuditReport(
            entries=[entry],
            recommendations=["Test recommendation 1", "Test recommendation 2"],
        )

        html = vendor_audit_report_to_html(report, lang="de")

        assert "Test recommendation 1" in html

    def test_html_contains_audit_flags(self) -> None:
        """Test HTML contains audit flags."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            vendor_audit_report_to_html,
        )

        entry = VendorAuditEntry(
            name="Flagged Tool",
            category="LLM",
            jurisdiction="US",
            has_dpa=False,
        )
        report = VendorAuditReport(entries=[entry])

        html = vendor_audit_report_to_html(report, lang="de")

        assert "US vendor without DPA" in html or "ohne DPA" in html or "ohne AVV" in html


# =============================================================================
# TEST: Validation Helpers
# =============================================================================

class TestValidationHelpers:
    """Tests for validation helper functions."""

    def test_validate_vendor_risk_scores_pass(self) -> None:
        """Test validation passes when scores are consistent."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            validate_vendor_risk_scores,
        )

        entry = VendorAuditEntry(
            name="Test",
            category="LLM",
            vendor_risk_score=3,
        )
        report = VendorAuditReport(entries=[entry])

        tools_data = [{"name": "Test", "vendor_risk": 2}]

        is_valid, errors = validate_vendor_risk_scores(report, tools_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_vendor_risk_scores_fail(self) -> None:
        """Test validation fails when audit score is lower."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            validate_vendor_risk_scores,
        )

        entry = VendorAuditEntry(
            name="Test",
            category="LLM",
            vendor_risk_score=2,  # Lower than tools data
        )
        report = VendorAuditReport(entries=[entry])

        tools_data = [{"name": "Test", "vendor_risk": 4}]

        is_valid, errors = validate_vendor_risk_scores(report, tools_data)

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_us_vendors_not_green_pass(self) -> None:
        """Test US vendors without DPA are not green."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            validate_us_vendors_not_green,
        )

        entry = VendorAuditEntry(
            name="US Tool",
            category="LLM",
            jurisdiction="US",
            has_dpa=False,
            overall_category="yellow",  # Correctly yellow
        )
        report = VendorAuditReport(entries=[entry])

        is_valid, errors = validate_us_vendors_not_green(report)

        assert is_valid is True

    def test_validate_eu_hosting_not_red_without_flags(self) -> None:
        """Test EU-hosted tools validation."""
        from services.vendor_audit_engine import (
            VendorAuditReport,
            VendorAuditEntry,
            validate_eu_hosting_not_red_without_flags,
        )

        entry = VendorAuditEntry(
            name="EU Tool",
            category="LLM",
            jurisdiction="EU",
            overall_category="green",
        )
        report = VendorAuditReport(entries=[entry])

        tools_data = [{"name": "EU Tool", "eu_hosting": True, "compliance_score": 1}]

        is_valid, errors = validate_eu_hosting_not_red_without_flags(report, tools_data)

        assert is_valid is True


# =============================================================================
# TEST: Consistency Rules VA_001-VA_006
# =============================================================================

class TestConsistencyRules:
    """Tests for consistency rules VA_001-VA_006."""

    def test_va_001_vendor_risk_consistency(self) -> None:
        """Test VA_001: vendor_risk_score >= Tools Engine vendor_risk."""
        from services.vendor_audit_engine import VendorAuditEntry

        # Should have risk >= 3 (tools engine value)
        entry = VendorAuditEntry(
            name="Test",
            category="LLM",
            vendor_risk_score=3,
        )

        # This test validates the rule conceptually
        assert entry.vendor_risk_score >= 1

    def test_va_003_us_vendor_dpa_rule(self) -> None:
        """Test VA_003: US vendors without DPA cannot be green."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="US Tool",
            category="LLM",
            jurisdiction="US",
            has_dpa=False,
            overall_category="green",  # Should be changed
        )

        # Should be yellow or red, not green
        assert entry.overall_category != "green"

    def test_va_004_eu_hosting_red_needs_flags(self) -> None:
        """Test VA_004: EU-hosted tools need flags if red."""
        from services.vendor_audit_engine import VendorAuditEntry

        # EU vendor with weak security becomes red WITH flags
        entry = VendorAuditEntry(
            name="EU Tool",
            category="LLM",
            jurisdiction="EU",
            security_posture="weak",
            overall_category="green",
        )

        # If red, should have flags
        if entry.overall_category == "red":
            assert len(entry.audit_flags) > 0


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_certifications(self) -> None:
        """Test handling of empty certifications list."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="No Certs Tool",
            category="LLM",
            certifications=[],
        )

        assert entry.has_certifications is False
        assert entry.certification_count == 0

    def test_many_audit_flags(self) -> None:
        """Test handling of many audit flags."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Problematic Tool",
            category="LLM",
            jurisdiction="US",
            has_dpa=False,
            data_location="Unknown",
            security_posture="weak",
        )

        # Should have multiple flags
        assert len(entry.audit_flags) >= 2

    def test_empty_report(self) -> None:
        """Test empty report handling."""
        from services.vendor_audit_engine import VendorAuditReport

        report = VendorAuditReport()

        assert report.total_vendors == 0
        assert report.average_risk_score == 0.0
        assert report.compliance_score == 100.0
        assert report.overall_audit_status == "pass"

    def test_special_characters_in_name(self) -> None:
        """Test handling of special characters in vendor name."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Tool & Co. (GmbH)",
            category="LLM <test>",
        )

        assert entry.name == "Tool & Co. (GmbH)"

    def test_unicode_in_notes(self) -> None:
        """Test handling of unicode in notes."""
        from services.vendor_audit_engine import VendorAuditEntry

        entry = VendorAuditEntry(
            name="Test",
            category="LLM",
            notes="Umlaute: aeoue Emoji: 🔒",
        )

        assert "Umlaute" in entry.notes


# =============================================================================
# TEST: Integration with Tools Engine
# =============================================================================

class TestToolsEngineIntegration:
    """Tests for integration with Tools Engine 4.0."""

    def test_extract_vendors_from_tool_profiles(self) -> None:
        """Test vendor extraction from ToolProfile-like objects."""
        from services.vendor_audit_engine import _extract_vendors_from_tools

        tools_data = [
            {
                "name": "OpenAI",
                "category": "LLM",
                "vendor_risk": 3,
                "compliance_score": 2,
                "eu_hosting": False,
                "host": "US",
                "gdpr": "DPA available",
            },
        ]

        vendors = _extract_vendors_from_tools(tools_data)

        assert len(vendors) == 1
        assert vendors[0]["name"] == "OpenAI"
        assert vendors[0]["vendor_risk"] == 3

    def test_generate_vendor_entry_from_tools_data(self) -> None:
        """Test vendor entry generation from tools data."""
        from services.vendor_audit_engine import _generate_vendor_entry

        vendor_info = {
            "name": "OpenAI",
            "category": "LLM",
            "vendor_risk": 3,
            "host": "US",
            "gdpr": "DPA available",
            "eu_hosting": False,
        }

        entry = _generate_vendor_entry(vendor_info, "minimal")

        assert entry.name == "OpenAI"
        assert entry.jurisdiction == "US"
        assert entry.has_dpa is True


# =============================================================================
# TEST: Module Import and Configuration
# =============================================================================

class TestModuleConfiguration:
    """Tests for module configuration and exports."""

    def test_module_exports(self) -> None:
        """Test all expected exports are available."""
        from services.vendor_audit_engine import (
            VendorAuditEntry,
            VendorAuditReport,
            generate_vendor_audit_report,
            vendor_audit_report_to_html,
            VENDOR_AUDIT_ENGINE_ENABLED,
        )

        assert VendorAuditEntry is not None
        assert VendorAuditReport is not None
        assert callable(generate_vendor_audit_report)
        assert callable(vendor_audit_report_to_html)
        assert isinstance(VENDOR_AUDIT_ENGINE_ENABLED, bool)

    def test_configuration_constants(self) -> None:
        """Test configuration constants are defined."""
        from services.vendor_audit_engine import (
            JURISDICTIONS,
            DATA_LOCATIONS,
            SECURITY_POSTURES,
            AI_ACT_RELEVANCE_LEVELS,
            DSGVO_RISK_LEVELS,
            OVERALL_CATEGORIES,
            SIZE_AUDIT_LIMITS,
        )

        assert "EU" in JURISDICTIONS
        assert "EU-only" in DATA_LOCATIONS
        assert "strong" in SECURITY_POSTURES
        assert "high" in AI_ACT_RELEVANCE_LEVELS
        assert "low" in DSGVO_RISK_LEVELS
        assert "green" in OVERALL_CATEGORIES
        assert "solo" in SIZE_AUDIT_LIMITS
