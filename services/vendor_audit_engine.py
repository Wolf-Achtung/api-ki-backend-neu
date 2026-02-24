# -*- coding: utf-8 -*-
"""
Sprint G35: Vendor Audit Engine – KI-TUV for Tools & Models
============================================================

A comprehensive Vendor Audit Engine that evaluates tools and vendors
like a KI-TUV (German technical inspection):

- Generates audit profiles for each relevant tool/vendor
- Evaluates technical, organizational and legal criteria
- Provides scores and categories (Green / Yellow / Red)
- Marks critically conspicuous vendors
- Generates dedicated VENDOR_AUDIT_HTML report section
- Complements Risk Engine (G29/G33), Tools Engine (G25),
  Strategy (G28) and Recommendations (G32)

Version: 1.0.0 (Sprint G35)
Author: Claude + Wolf
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

log = logging.getLogger(__name__)

__all__ = [
    "VendorAuditEntry",
    "VendorAuditReport",
    "generate_vendor_audit_report",
    "vendor_audit_report_to_html",
    "VENDOR_AUDIT_ENGINE_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

VENDOR_AUDIT_ENGINE_ENABLED = True

# Vendor category thresholds
VENDOR_CATEGORY_RED_THRESHOLD = 4  # vendor_risk_score >= 4 = RED
VENDOR_CATEGORY_YELLOW_THRESHOLD = 3  # vendor_risk_score = 3 = YELLOW

# Jurisdiction classifications
JURISDICTIONS = ["EU", "US", "UK", "CH", "Other"]

# Data location classifications
DATA_LOCATIONS = ["EU-only", "EU+US", "Global", "Unknown"]

# Security posture levels
SECURITY_POSTURES = ["weak", "medium", "strong"]

# AI Act relevance levels
AI_ACT_RELEVANCE_LEVELS = ["none", "low", "medium", "high"]

# DSGVO risk levels
DSGVO_RISK_LEVELS = ["low", "medium", "high"]

# Overall category options
OVERALL_CATEGORIES = ["green", "yellow", "red"]

# Common certifications
COMMON_CERTIFICATIONS = [
    "ISO 27001",
    "SOC2",
    "SOC2 Type II",
    "ISO 27017",
    "ISO 27018",
    "C5",
    "BSI Grundschutz",
    "TISAX",
    "HIPAA",
    "PCI-DSS",
    "FedRAMP",
]

# Vendor heuristics for jurisdiction detection
VENDOR_JURISDICTION_HEURISTICS: Dict[str, str] = {
    # EU vendors
    "deepl": "EU",
    "aleph alpha": "EU",
    "mistral": "EU",
    "stability": "UK",
    "cohere": "US",
    # US vendors
    "openai": "US",
    "anthropic": "US",
    "microsoft": "US",
    "google": "US",
    "amazon": "US",
    "aws": "US",
    "meta": "US",
    "salesforce": "US",
    "hubspot": "US",
    "notion": "US",
    "slack": "US",
    "zoom": "US",
    "datadog": "US",
    "mongodb": "US",
    "snowflake": "US",
    "databricks": "US",
    # Other
    "tencent": "Other",
    "alibaba": "Other",
    "baidu": "Other",
}

# Size constraints for audit report
SIZE_AUDIT_LIMITS = {
    "solo": {"max_vendors": 5, "max_recommendations": 3},
    "team": {"max_vendors": 8, "max_recommendations": 5},
    "kmu": {"max_vendors": 12, "max_recommendations": 7},
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class VendorAuditEntry:
    """
    Audit entry for a single vendor/tool.

    Evaluates technical, organizational and legal criteria
    and provides a comprehensive risk assessment.
    """
    name: str
    category: str  # e.g. "LLM", "Analytics", "Automation"
    jurisdiction: str = "Unknown"  # e.g. "EU", "US", "UK", "Other"
    data_location: str = "Unknown"  # "EU-only", "EU+US", "Global", "Unknown"
    subprocessors: List[str] = field(default_factory=list)
    has_dpa: bool = False  # Data Processing Agreement in place?
    ai_act_relevance: str = "none"  # "none", "low", "medium", "high"
    dsgvo_risk_level: str = "medium"  # "low", "medium", "high"
    security_posture: str = "medium"  # "weak", "medium", "strong"
    certifications: List[str] = field(default_factory=list)
    vendor_risk_score: int = 3  # 1-5
    audit_flags: List[str] = field(default_factory=list)
    overall_category: str = "yellow"  # "green", "yellow", "red"
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Validate jurisdiction
        if self.jurisdiction not in JURISDICTIONS and self.jurisdiction != "Unknown":
            log.warning("[G35] Invalid jurisdiction: %s, defaulting to 'Unknown'", self.jurisdiction)
            self.jurisdiction = "Unknown"

        # Validate data_location
        if self.data_location not in DATA_LOCATIONS:
            log.warning("[G35] Invalid data_location: %s, defaulting to 'Unknown'", self.data_location)
            self.data_location = "Unknown"

        # Validate ai_act_relevance
        if self.ai_act_relevance not in AI_ACT_RELEVANCE_LEVELS:
            log.warning("[G35] Invalid ai_act_relevance: %s, defaulting to 'none'", self.ai_act_relevance)
            self.ai_act_relevance = "none"

        # Validate dsgvo_risk_level
        if self.dsgvo_risk_level not in DSGVO_RISK_LEVELS:
            log.warning("[G35] Invalid dsgvo_risk_level: %s, defaulting to 'medium'", self.dsgvo_risk_level)
            self.dsgvo_risk_level = "medium"

        # Validate security_posture
        if self.security_posture not in SECURITY_POSTURES:
            log.warning("[G35] Invalid security_posture: %s, defaulting to 'medium'", self.security_posture)
            self.security_posture = "medium"

        # Clamp vendor_risk_score
        self.vendor_risk_score = max(1, min(5, self.vendor_risk_score))

        # Validate overall_category
        if self.overall_category not in OVERALL_CATEGORIES:
            log.warning("[G35] Invalid overall_category: %s, defaulting to 'yellow'", self.overall_category)
            self.overall_category = "yellow"

        # Ensure lists
        if not isinstance(self.subprocessors, list):
            self.subprocessors = []
        if not isinstance(self.certifications, list):
            self.certifications = []
        if not isinstance(self.audit_flags, list):
            self.audit_flags = []

        # Recalculate category based on rules
        self._recalculate_category()

    def _recalculate_category(self) -> None:
        """
        Recalculate overall_category based on scoring rules.

        Rules:
        - US vendor without DPA -> at least yellow, possibly red
        - vendor_risk_score >= 4 or compliance_score >= 4 -> special flags + high category
        - EU vendor with EU hosting + DPA + certifications -> tends to green
        """
        # Rule: US vendor without DPA cannot be green
        if self.jurisdiction == "US" and not self.has_dpa:
            if self.overall_category == "green":
                self.overall_category = "yellow"
            if "US vendor without DPA" not in self.audit_flags:
                self.audit_flags.append("US vendor without DPA")

        # Rule: High vendor risk score
        if self.vendor_risk_score >= VENDOR_CATEGORY_RED_THRESHOLD:
            if self.overall_category != "red":
                self.overall_category = "red"
            if "High vendor risk score" not in self.audit_flags:
                self.audit_flags.append("High vendor risk score")

        # Rule: High DSGVO risk
        if self.dsgvo_risk_level == "high":
            if self.overall_category == "green":
                self.overall_category = "yellow"
            if "High DSGVO risk" not in self.audit_flags:
                self.audit_flags.append("High DSGVO risk")

        # Rule: High AI Act relevance without proper controls
        if self.ai_act_relevance == "high" and self.security_posture != "strong":
            if self.overall_category == "green":
                self.overall_category = "yellow"
            if "High AI Act relevance - review required" not in self.audit_flags:
                self.audit_flags.append("High AI Act relevance - review required")

        # Rule: Unknown data location
        if self.data_location == "Unknown":
            if self.overall_category == "green":
                self.overall_category = "yellow"
            if "Data location unknown" not in self.audit_flags:
                self.audit_flags.append("Data location unknown")

        # Rule: Weak security posture
        if self.security_posture == "weak":
            self.overall_category = "red"
            if "Weak security posture" not in self.audit_flags:
                self.audit_flags.append("Weak security posture")

        # Rule: EU vendor with EU hosting + DPA + certifications -> promote to green
        if (self.jurisdiction == "EU" and self.data_location == "EU-only" and
            self.has_dpa and len(self.certifications) >= 1 and
            self.dsgvo_risk_level != "high" and self.security_posture != "weak"):
            if self.overall_category == "yellow":
                self.overall_category = "green"
                # Remove any flags that were added during yellow checks
                self.audit_flags = [f for f in self.audit_flags if "Unknown" not in f]

    @property
    def is_eu_compliant(self) -> bool:
        """Check if vendor is EU-compliant (EU jurisdiction with DPA)."""
        return self.jurisdiction == "EU" and self.has_dpa

    @property
    def is_high_risk(self) -> bool:
        """Check if vendor is high-risk."""
        return self.overall_category == "red" or self.vendor_risk_score >= 4

    @property
    def has_certifications(self) -> bool:
        """Check if vendor has any certifications."""
        return len(self.certifications) > 0

    @property
    def certification_count(self) -> int:
        """Count of certifications."""
        return len(self.certifications)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "category": self.category,
            "jurisdiction": self.jurisdiction,
            "data_location": self.data_location,
            "subprocessors": self.subprocessors,
            "has_dpa": self.has_dpa,
            "ai_act_relevance": self.ai_act_relevance,
            "dsgvo_risk_level": self.dsgvo_risk_level,
            "security_posture": self.security_posture,
            "certifications": self.certifications,
            "vendor_risk_score": self.vendor_risk_score,
            "audit_flags": self.audit_flags,
            "overall_category": self.overall_category,
            "notes": self.notes,
            "is_eu_compliant": self.is_eu_compliant,
            "is_high_risk": self.is_high_risk,
            "has_certifications": self.has_certifications,
            "certification_count": self.certification_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VendorAuditEntry":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "Unknown"),
            category=data.get("category", "Unknown"),
            jurisdiction=data.get("jurisdiction", "Unknown"),
            data_location=data.get("data_location", "Unknown"),
            subprocessors=data.get("subprocessors", []),
            has_dpa=data.get("has_dpa", False),
            ai_act_relevance=data.get("ai_act_relevance", "none"),
            dsgvo_risk_level=data.get("dsgvo_risk_level", "medium"),
            security_posture=data.get("security_posture", "medium"),
            certifications=data.get("certifications", []),
            vendor_risk_score=int(data.get("vendor_risk_score", 3)),
            audit_flags=data.get("audit_flags", []),
            overall_category=data.get("overall_category", "yellow"),
            notes=data.get("notes", ""),
        )


@dataclass
class VendorAuditReport:
    """
    Complete Vendor Audit Report with all entries and summary.
    """
    entries: List[VendorAuditEntry] = field(default_factory=list)
    summary: str = ""
    high_risk_vendors: List[str] = field(default_factory=list)
    green_vendors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and calculate derived fields."""
        if not isinstance(self.entries, list):
            self.entries = []
        if not isinstance(self.high_risk_vendors, list):
            self.high_risk_vendors = []
        if not isinstance(self.green_vendors, list):
            self.green_vendors = []
        if not isinstance(self.recommendations, list):
            self.recommendations = []

        # Auto-calculate high_risk_vendors and green_vendors
        self._recalculate_vendor_lists()

    def _recalculate_vendor_lists(self) -> None:
        """Recalculate high_risk and green vendor lists from entries."""
        self.high_risk_vendors = [
            e.name for e in self.entries if e.overall_category == "red"
        ]
        self.green_vendors = [
            e.name for e in self.entries if e.overall_category == "green"
        ]

    @property
    def total_vendors(self) -> int:
        """Total number of vendors audited."""
        return len(self.entries)

    @property
    def red_count(self) -> int:
        """Count of red (high-risk) vendors."""
        return sum(1 for e in self.entries if e.overall_category == "red")

    @property
    def yellow_count(self) -> int:
        """Count of yellow (medium-risk) vendors."""
        return sum(1 for e in self.entries if e.overall_category == "yellow")

    @property
    def green_count(self) -> int:
        """Count of green (low-risk) vendors."""
        return sum(1 for e in self.entries if e.overall_category == "green")

    @property
    def average_risk_score(self) -> float:
        """Average vendor risk score."""
        if not self.entries:
            return 0.0
        return sum(e.vendor_risk_score for e in self.entries) / len(self.entries)

    @property
    def eu_compliant_count(self) -> int:
        """Count of EU-compliant vendors."""
        return sum(1 for e in self.entries if e.is_eu_compliant)

    @property
    def overall_audit_status(self) -> str:
        """
        Overall audit status: 'pass', 'warn', 'fail'.

        - fail: Any red vendors
        - warn: Any yellow vendors but no red
        - pass: All green vendors
        """
        if self.red_count > 0:
            return "fail"
        elif self.yellow_count > 0:
            return "warn"
        else:
            return "pass"

    @property
    def compliance_score(self) -> float:
        """
        Overall compliance score (0-100).

        Based on category distribution and EU compliance.
        """
        if not self.entries:
            return 100.0

        # Weight: green=100, yellow=50, red=0
        category_score = (
            self.green_count * 100 +
            self.yellow_count * 50 +
            self.red_count * 0
        ) / self.total_vendors

        # EU compliance bonus
        eu_bonus = (self.eu_compliant_count / self.total_vendors) * 20 if self.total_vendors > 0 else 0

        return min(100.0, category_score + eu_bonus)

    def get_entry(self, name: str) -> Optional[VendorAuditEntry]:
        """Get vendor entry by name."""
        for entry in self.entries:
            if entry.name.lower() == name.lower():
                return entry
        return None

    def get_entries_by_category(self, category: str) -> List[VendorAuditEntry]:
        """Get vendor entries by overall category."""
        return [e for e in self.entries if e.overall_category == category]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entries": [e.to_dict() for e in self.entries],
            "summary": self.summary,
            "high_risk_vendors": self.high_risk_vendors,
            "green_vendors": self.green_vendors,
            "recommendations": self.recommendations,
            "total_vendors": self.total_vendors,
            "red_count": self.red_count,
            "yellow_count": self.yellow_count,
            "green_count": self.green_count,
            "average_risk_score": round(self.average_risk_score, 2),
            "eu_compliant_count": self.eu_compliant_count,
            "overall_audit_status": self.overall_audit_status,
            "compliance_score": round(self.compliance_score, 1),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VendorAuditReport":
        """Create from dictionary."""
        entries_data = data.get("entries", [])
        entries = [
            VendorAuditEntry.from_dict(e) if isinstance(e, dict) else e
            for e in entries_data
        ]

        return cls(
            entries=entries,
            summary=data.get("summary", ""),
            high_risk_vendors=data.get("high_risk_vendors", []),
            green_vendors=data.get("green_vendors", []),
            recommendations=data.get("recommendations", []),
        )


# =============================================================================
# AUDIT DETERMINATION FUNCTIONS
# =============================================================================

def _determine_jurisdiction(
    vendor_name: str,
    host_info: str = "",
    gdpr_info: str = "",
) -> str:
    """
    Determine vendor jurisdiction from name and hosting info.

    Args:
        vendor_name: Name of the vendor/tool
        host_info: Hosting location info
        gdpr_info: GDPR/compliance info

    Returns:
        Jurisdiction string (EU, US, UK, CH, Other)
    """
    name_lower = vendor_name.lower()
    host_lower = host_info.lower() if host_info else ""
    gdpr_lower = gdpr_info.lower() if gdpr_info else ""

    # Check known vendors
    for pattern, jurisdiction in VENDOR_JURISDICTION_HEURISTICS.items():
        if pattern in name_lower:
            return jurisdiction

    # Check host info
    if "eu" in host_lower and "us" not in host_lower:
        return "EU"
    if "deutschland" in host_lower or "germany" in host_lower:
        return "EU"
    if "us" in host_lower or "united states" in host_lower:
        return "US"
    if "uk" in host_lower or "united kingdom" in host_lower:
        return "UK"
    if "schweiz" in host_lower or "switzerland" in host_lower:
        return "CH"

    # Check GDPR info
    if "eu-server" in gdpr_lower or "dsgvo-konform" in gdpr_lower:
        return "EU"
    if "us" in gdpr_lower and "eu" not in gdpr_lower:
        return "US"

    return "Unknown"


def _determine_data_location(
    host_info: str = "",
    gdpr_info: str = "",
    jurisdiction: str = "Unknown",
) -> str:
    """
    Determine data location from hosting and GDPR info.

    Args:
        host_info: Hosting location info
        gdpr_info: GDPR/compliance info
        jurisdiction: Already determined jurisdiction

    Returns:
        Data location string
    """
    host_lower = host_info.lower() if host_info else ""
    gdpr_lower = gdpr_info.lower() if gdpr_info else ""

    # Check for explicit EU-only
    if "eu-only" in host_lower or "eu-server" in gdpr_lower:
        return "EU-only"
    if "eu-option" in gdpr_lower or ("eu" in host_lower and "us" in host_lower):
        return "EU+US"
    if "global" in host_lower or "worldwide" in host_lower:
        return "Global"

    # Infer from jurisdiction
    if jurisdiction == "EU":
        return "EU-only"
    elif jurisdiction == "US":
        return "EU+US"  # Most US vendors offer EU hosting option

    return "Unknown"


def _determine_has_dpa(
    gdpr_info: str = "",
    vendor_name: str = "",
) -> bool:
    """
    Determine if DPA (Data Processing Agreement) is available.

    Args:
        gdpr_info: GDPR/compliance info
        vendor_name: Vendor name for known vendors

    Returns:
        True if DPA is available
    """
    gdpr_lower = gdpr_info.lower() if gdpr_info else ""

    # Check explicit DPA mentions
    dpa_indicators = [
        "dpa", "avv", "auftragsverarbeitung", "data processing agreement",
        "dsgvo-konform", "gdpr-compliant", "art. 28", "artikel 28",
    ]

    for indicator in dpa_indicators:
        if indicator in gdpr_lower:
            return True

    # Known vendors with DPA
    known_dpa_vendors = [
        "openai", "anthropic", "microsoft", "google", "aws", "amazon",
        "salesforce", "hubspot", "notion", "slack", "zoom", "datadog",
        "mongodb", "snowflake", "databricks", "deepl", "mistral",
    ]

    name_lower = vendor_name.lower()
    for vendor in known_dpa_vendors:
        if vendor in name_lower:
            return True

    return False


def _determine_security_posture(
    certifications: List[str],
    gdpr_info: str = "",
) -> str:
    """
    Determine security posture from certifications and info.

    Args:
        certifications: List of certifications
        gdpr_info: GDPR/compliance info

    Returns:
        Security posture string (weak, medium, strong)
    """
    cert_count = len(certifications)
    gdpr_lower = gdpr_info.lower() if gdpr_info else ""

    # Strong indicators
    strong_certs = ["iso 27001", "soc2 type ii", "c5", "bsi grundschutz", "tisax"]
    has_strong_cert = any(
        cert.lower() in " ".join(certifications).lower()
        for cert in strong_certs
    )

    if has_strong_cert and cert_count >= 2:
        return "strong"
    if cert_count >= 1 or "soc2" in gdpr_lower or "iso" in gdpr_lower:
        return "medium"
    if "unklar" in gdpr_lower or "unknown" in gdpr_lower:
        return "weak"

    return "medium"


def _determine_certifications(
    gdpr_info: str = "",
    vendor_name: str = "",
) -> List[str]:
    """
    Extract certifications from GDPR info.

    Args:
        gdpr_info: GDPR/compliance info
        vendor_name: Vendor name for inference

    Returns:
        List of certifications
    """
    gdpr_lower = gdpr_info.lower() if gdpr_info else ""
    certifications: List[str] = []

    # Check for each known certification
    cert_patterns = {
        "ISO 27001": ["iso 27001", "iso27001"],
        "SOC2": ["soc2", "soc 2"],
        "SOC2 Type II": ["soc2 type ii", "soc 2 type ii", "soc2 typ ii"],
        "ISO 27017": ["iso 27017", "iso27017"],
        "ISO 27018": ["iso 27018", "iso27018"],
        "C5": ["c5", "bsi c5"],
        "BSI Grundschutz": ["bsi grundschutz", "grundschutz"],
        "TISAX": ["tisax"],
        "HIPAA": ["hipaa"],
        "PCI-DSS": ["pci-dss", "pci dss"],
    }

    for cert_name, patterns in cert_patterns.items():
        for pattern in patterns:
            if pattern in gdpr_lower:
                certifications.append(cert_name)
                break

    return certifications


def _determine_ai_act_relevance(
    category: str,
    vendor_name: str = "",
    ai_act_class: str = "minimal",
) -> str:
    """
    Determine AI Act relevance based on vendor category.

    Args:
        category: Tool/vendor category
        vendor_name: Vendor name
        ai_act_class: AI Act classification from context

    Returns:
        AI Act relevance level
    """
    category_lower = category.lower()
    name_lower = vendor_name.lower()

    # High relevance: LLM providers, ML platforms
    high_relevance_patterns = [
        "llm", "large language", "gpt", "ai model", "ml platform",
        "machine learning", "deep learning", "neural", "foundation model",
    ]

    # Medium relevance: AI-assisted tools
    medium_relevance_patterns = [
        "ai-assist", "ki-assist", "automation", "bot", "chatbot",
        "analytics", "prediction", "recommendation",
    ]

    # Check patterns
    for pattern in high_relevance_patterns:
        if pattern in category_lower or pattern in name_lower:
            return "high"

    for pattern in medium_relevance_patterns:
        if pattern in category_lower or pattern in name_lower:
            return "medium"

    # Map from AI Act class
    if ai_act_class in ["high_risk", "unacceptable"]:
        return "high"
    elif ai_act_class in ["limited_risk"]:
        return "medium"

    return "low"


def _determine_dsgvo_risk(
    jurisdiction: str,
    data_location: str,
    has_dpa: bool,
    vendor_risk_score: int,
) -> str:
    """
    Determine DSGVO risk level.

    Args:
        jurisdiction: Vendor jurisdiction
        data_location: Data location
        has_dpa: Whether DPA is available
        vendor_risk_score: Vendor risk score

    Returns:
        DSGVO risk level
    """
    # High risk indicators
    if jurisdiction in ["US", "Other"] and not has_dpa:
        return "high"
    if data_location == "Unknown":
        return "high"
    if vendor_risk_score >= 4:
        return "high"

    # Low risk indicators
    if jurisdiction == "EU" and has_dpa and data_location == "EU-only":
        return "low"

    return "medium"


def _calculate_vendor_risk_score(
    jurisdiction: str,
    data_location: str,
    has_dpa: bool,
    security_posture: str,
    tools_vendor_risk: int = 3,
) -> int:
    """
    Calculate vendor risk score (1-5).

    Args:
        jurisdiction: Vendor jurisdiction
        data_location: Data location
        has_dpa: Whether DPA is available
        security_posture: Security posture
        tools_vendor_risk: Vendor risk from Tools Engine 4.0

    Returns:
        Vendor risk score (1-5)
    """
    # Start with tools engine score as baseline
    score = tools_vendor_risk

    # Adjust based on jurisdiction
    if jurisdiction == "EU":
        score = max(1, score - 1)
    elif jurisdiction in ["US", "Other"]:
        score = min(5, score + 1)

    # Adjust based on DPA
    if not has_dpa:
        score = min(5, score + 1)

    # Adjust based on data location
    if data_location == "Unknown":
        score = min(5, score + 1)
    elif data_location == "EU-only":
        score = max(1, score - 1)

    # Adjust based on security posture
    if security_posture == "weak":
        score = min(5, score + 1)
    elif security_posture == "strong":
        score = max(1, score - 1)

    return max(1, min(5, score))


def _determine_overall_category(
    vendor_risk_score: int,
    dsgvo_risk_level: str,
    ai_act_relevance: str,
    jurisdiction: str,
    has_dpa: bool,
    security_posture: str,
    certifications: List[str],
    data_location: str,
) -> Tuple[str, List[str]]:
    """
    Determine overall category (green/yellow/red) and audit flags.

    Args:
        vendor_risk_score: Calculated vendor risk score
        dsgvo_risk_level: DSGVO risk level
        ai_act_relevance: AI Act relevance
        jurisdiction: Vendor jurisdiction
        has_dpa: Whether DPA is available
        security_posture: Security posture
        certifications: List of certifications
        data_location: Data location

    Returns:
        Tuple of (overall_category, audit_flags)
    """
    audit_flags: List[str] = []

    # Start with base category from vendor_risk_score
    if vendor_risk_score >= 4:
        category = "red"
        audit_flags.append("High vendor risk score")
    elif vendor_risk_score == 3:
        category = "yellow"
    else:
        category = "green"

    # Rule: US vendor without DPA -> at least yellow
    if jurisdiction == "US" and not has_dpa:
        if category == "green":
            category = "yellow"
        audit_flags.append("US vendor without DPA")

    # Rule: High DSGVO risk -> at least yellow
    if dsgvo_risk_level == "high":
        if category == "green":
            category = "yellow"
        audit_flags.append("High DSGVO risk")

    # Rule: High AI Act relevance without strong security -> yellow
    if ai_act_relevance == "high" and security_posture != "strong":
        if category == "green":
            category = "yellow"
        audit_flags.append("High AI Act relevance - review required")

    # Rule: Unknown data location -> yellow
    if data_location == "Unknown":
        if category == "green":
            category = "yellow"
        audit_flags.append("Data location unknown")

    # Rule: Weak security posture -> red
    if security_posture == "weak":
        category = "red"
        audit_flags.append("Weak security posture")

    # Rule: EU vendor with EU hosting + DPA + certifications -> green
    if (jurisdiction == "EU" and data_location == "EU-only" and
        has_dpa and len(certifications) >= 1 and
        dsgvo_risk_level != "high" and security_posture != "weak"):
        if category == "yellow":
            category = "green"
        # Remove some flags if now green
        audit_flags = [f for f in audit_flags if "Unknown" not in f]

    return category, audit_flags


def _determine_size_label(briefing: Optional[Dict[str, Any]]) -> str:
    """Determine company size label from briefing."""
    if not briefing:
        return "team"

    size = str(briefing.get("unternehmensgroesse", "")).lower()

    if "solo" in size or "freiberuf" in size or "einzelunternehm" in size:
        return "solo"
    elif "kmu" in size or "mittel" in size or ">10" in size:
        return "kmu"
    else:
        return "team"




# FIX-C5: Known vendor metadata for questionnaire-based extraction
_KNOWN_VENDOR_META = {
    "chatgpt": {"name": "ChatGPT (OpenAI)", "category": "LLM", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "openai": {"name": "OpenAI", "category": "LLM API", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "claude": {"name": "Claude (Anthropic)", "category": "LLM", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "anthropic": {"name": "Anthropic", "category": "LLM API", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "perplexity": {"name": "Perplexity AI", "category": "Search AI", "host": "US", "gdpr": "Limited", "vendor_risk": 4, "eu_hosting": False},
    "tavily": {"name": "Tavily", "category": "Search API", "host": "US", "gdpr": "Limited", "vendor_risk": 4, "eu_hosting": False},
    "gemini": {"name": "Gemini (Google)", "category": "LLM", "host": "US/EU", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "copilot": {"name": "Microsoft Copilot", "category": "LLM", "host": "EU available", "gdpr": "DPA + EU Data Boundary", "vendor_risk": 2, "eu_hosting": True},
    "midjourney": {"name": "Midjourney", "category": "Image Gen", "host": "US", "gdpr": "Limited", "vendor_risk": 4, "eu_hosting": False},
    "deepl": {"name": "DeepL", "category": "Translation", "host": "DE", "gdpr": "Full DSGVO", "vendor_risk": 1, "eu_hosting": True},
    "notion": {"name": "Notion AI", "category": "Productivity", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "huggingface": {"name": "Hugging Face", "category": "ML Platform", "host": "US/EU", "gdpr": "Self-hosted option", "vendor_risk": 2, "eu_hosting": True},
}


def _extract_vendors_from_briefing(briefing: dict) -> list:
    """FIX-C5: Extract vendor info from questionnaire answers as fallback."""
    vendors = []
    seen = set()
    for source in [briefing.get("VORHANDENE_TOOLS_LABELS",""), briefing.get("vorhandene_tools",""), briefing.get("ki_projekte","")]:
        if not source: continue
        items = source if isinstance(source, list) else [s.strip() for s in str(source).replace(";",",").split(",")]
        for item in items:
            il = item.strip().lower()
            if not il: continue
            for key, meta in _KNOWN_VENDOR_META.items():
                if key in il and meta["name"] not in seen:
                    vendors.append(dict(meta)); seen.add(meta["name"])
    return vendors


def _extract_vendors_from_tools(
    tools_data: Any,
) -> List[Dict[str, Any]]:
    """
    Extract vendor information from Tools Engine 4.0 data.

    Args:
        tools_data: Tools Engine data (list of ToolProfile or dicts)

    Returns:
        List of vendor info dicts
    """
    vendors: List[Dict[str, Any]] = []

    if not tools_data:
        return vendors

    tools_list = tools_data if isinstance(tools_data, list) else []

    for tool in tools_list:
        if isinstance(tool, dict):
            vendor_info = {
                "name": tool.get("name", "Unknown"),
                "category": tool.get("category", "Unknown"),
                "vendor_risk": tool.get("vendor_risk", 3),
                "compliance_score": tool.get("compliance_score", 3),
                "eu_hosting": tool.get("eu_hosting"),
                "host": tool.get("host", ""),
                "gdpr": tool.get("gdpr", ""),
                "price": tool.get("price", ""),
            }
        else:
            # Handle ToolProfile objects
            vendor_info = {
                "name": getattr(tool, "name", "Unknown"),
                "category": getattr(tool, "category", "Unknown"),
                "vendor_risk": getattr(tool, "vendor_risk", 3),
                "compliance_score": getattr(tool, "compliance_score", 3),
                "eu_hosting": getattr(tool, "eu_hosting", None),
                "host": getattr(tool, "host", ""),
                "gdpr": getattr(tool, "gdpr", ""),
                "price": getattr(tool, "price", ""),
            }

        vendors.append(vendor_info)

    return vendors


def _generate_vendor_entry(
    vendor_info: Dict[str, Any],
    ai_act_class: str = "minimal",
) -> VendorAuditEntry:
    """
    Generate a VendorAuditEntry from vendor info.

    Args:
        vendor_info: Vendor information dict
        ai_act_class: AI Act classification from context

    Returns:
        VendorAuditEntry object
    """
    name = vendor_info.get("name", "Unknown")
    category = vendor_info.get("category", "Unknown")
    host = vendor_info.get("host", "")
    gdpr = vendor_info.get("gdpr", "")
    tools_vendor_risk = vendor_info.get("vendor_risk", 3)
    eu_hosting = vendor_info.get("eu_hosting")

    # Determine attributes
    jurisdiction = _determine_jurisdiction(name, host, gdpr)
    data_location = _determine_data_location(host, gdpr, jurisdiction)
    has_dpa = _determine_has_dpa(gdpr, name)
    certifications = _determine_certifications(gdpr, name)
    security_posture = _determine_security_posture(certifications, gdpr)
    ai_act_relevance = _determine_ai_act_relevance(category, name, ai_act_class)

    # Override data_location if eu_hosting is explicitly set
    if eu_hosting is True and data_location == "Unknown":
        data_location = "EU-only"
    elif eu_hosting is False and data_location == "Unknown":
        data_location = "Global"

    # Calculate risk scores
    vendor_risk_score = _calculate_vendor_risk_score(
        jurisdiction, data_location, has_dpa, security_posture, tools_vendor_risk
    )

    dsgvo_risk_level = _determine_dsgvo_risk(
        jurisdiction, data_location, has_dpa, vendor_risk_score
    )

    # Determine category
    overall_category, audit_flags = _determine_overall_category(
        vendor_risk_score, dsgvo_risk_level, ai_act_relevance,
        jurisdiction, has_dpa, security_posture, certifications, data_location
    )

    return VendorAuditEntry(
        name=name,
        category=category,
        jurisdiction=jurisdiction,
        data_location=data_location,
        subprocessors=[],  # Would need external data
        has_dpa=has_dpa,
        ai_act_relevance=ai_act_relevance,
        dsgvo_risk_level=dsgvo_risk_level,
        security_posture=security_posture,
        certifications=certifications,
        vendor_risk_score=vendor_risk_score,
        audit_flags=audit_flags,
        overall_category=overall_category,
        notes="",
    )


def _generate_recommendations(
    entries: List[VendorAuditEntry],
    size_label: str = "team",
) -> List[str]:
    """
    Generate recommendations based on audit entries.

    Args:
        entries: List of VendorAuditEntry objects
        size_label: Company size label

    Returns:
        List of recommendation strings
    """
    recommendations: List[str] = []
    constraints = SIZE_AUDIT_LIMITS.get(size_label, SIZE_AUDIT_LIMITS["team"])
    max_recommendations = constraints["max_recommendations"]

    # Check for US vendors without DPA
    us_no_dpa = [e for e in entries if e.jurisdiction == "US" and not e.has_dpa]
    if us_no_dpa:
        names = ", ".join([e.name for e in us_no_dpa[:2]])
        recommendations.append(
            f"DPA (Data Processing Agreement) mit US-Anbietern abschliessen: {names}"
        )

    # Check for red vendors
    red_vendors = [e for e in entries if e.overall_category == "red"]
    if red_vendors:
        names = ", ".join([e.name for e in red_vendors[:2]])
        recommendations.append(
            f"Hochrisiko-Anbieter prüfen, Risikominimierung durch AVV/DPA sicherstellen: {names}. Hinweis: Für LLM-Anbieter (OpenAI, Anthropic) existieren aktuell keine gleichwertigen EU-Alternativen — Fokus auf vertragliche Absicherung und Datenminimierung."
        )

    # Check for unknown data locations
    unknown_location = [e for e in entries if e.data_location == "Unknown"]
    if unknown_location:
        names = ", ".join([e.name for e in unknown_location[:2]])
        recommendations.append(
            f"Datenstandorte klären für: {names}"
        )

    # Check for weak security
    weak_security = [e for e in entries if e.security_posture == "weak"]
    if weak_security:
        names = ", ".join([e.name for e in weak_security[:2]])
        recommendations.append(
            f"Sicherheitsbewertung anfordern für: {names}"
        )

    # Check for high AI Act relevance
    high_ai_act = [e for e in entries if e.ai_act_relevance == "high"]
    if high_ai_act:
        names = ", ".join([e.name for e in high_ai_act[:2]])
        recommendations.append(
            f"AI Act Konformitätsprüfung durchführen für: {names}"
        )

    # Check for missing certifications
    no_certs = [e for e in entries if not e.has_certifications and e.overall_category != "green"]
    if no_certs:
        recommendations.append(
            "Zertifizierungsnachweise (ISO 27001, SOC2) von Anbietern anfordern"
        )

    # General recommendations
    if not any(e.overall_category == "green" for e in entries):
        recommendations.append(
            "Mindestens einen EU-konformen Anbieter als Alternative evaluieren"
        )

    return recommendations[:max_recommendations]


def _generate_summary(
    entries: List[VendorAuditEntry],
    lang: str = "de",
) -> str:
    """
    Generate summary text for the audit report.

    Args:
        entries: List of VendorAuditEntry objects
        lang: Language code

    Returns:
        Summary string
    """
    if not entries:
        return "Keine Anbieter zur Prüfung vorhanden." if lang == "de" else "No vendors to audit."

    total = len(entries)
    green = sum(1 for e in entries if e.overall_category == "green")
    yellow = sum(1 for e in entries if e.overall_category == "yellow")
    red = sum(1 for e in entries if e.overall_category == "red")
    eu_compliant = sum(1 for e in entries if e.is_eu_compliant)

    if lang == "en":
        return (
            f"Vendor audit completed for {total} tools/vendors. "
            f"Result: {green} green (low risk), {yellow} yellow (medium risk), {red} red (high risk). "
            f"{eu_compliant} vendors are EU-compliant. "
            f"{'Immediate action required for high-risk vendors.' if red > 0 else 'No critical findings.'}"
        )
    else:
        return (
            f"Vendor-Audit für {total} Tools/Anbieter abgeschlossen. "
            f"Ergebnis: {green} grün (niedriges Risiko), {yellow} gelb (mittleres Risiko), {red} rot (hohes Risiko). "
            f"{eu_compliant} Anbieter sind EU-konform. "
            f"{'Sofortiger Handlungsbedarf bei Hochrisiko-Anbietern.' if red > 0 else 'Keine kritischen Befunde.'}"
        )


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_vendor_audit_report(
    context: Optional[Any] = None,
    tools_data: Optional[Any] = None,
    risk_report_v2: Optional[Any] = None,
    risk_report_v3: Optional[Any] = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[Dict[str, Any]] = None,
) -> VendorAuditReport:
    """
    Generate comprehensive Vendor Audit Report.

    Uses data from Tools Engine 4.0 (G25), Risk Engine 2.0 (G29)
    and Risk Engine 3.0 (G33) to create audit profiles for all vendors.

    Args:
        context: ReportContext object (optional)
        tools_data: Tools Engine 4.0 output
        risk_report_v2: Risk Engine 2.0 report
        risk_report_v3: Risk Engine 3.0 report
        briefing: Original briefing/answers dict
        llm_response: Parsed JSON from LLM (if available)

    Returns:
        VendorAuditReport with complete vendor audit
    """
    log.info("[G35] Generating Vendor Audit Report...")

    briefing = briefing or {}
    size_label = _determine_size_label(briefing)
    constraints = SIZE_AUDIT_LIMITS.get(size_label, SIZE_AUDIT_LIMITS["team"])

    # If LLM response provided, use it directly
    if llm_response:
        return VendorAuditReport.from_dict(llm_response)

    # Extract AI Act class from risk reports
    ai_act_class = "minimal"
    if risk_report_v2:
        if hasattr(risk_report_v2, "ai_act_class"):
            ai_act_class = risk_report_v2.ai_act_class
        elif isinstance(risk_report_v2, dict):
            ai_act_class = risk_report_v2.get("ai_act_class", "minimal")

    # Extract vendors from tools data
    vendors = _extract_vendors_from_tools(tools_data)

    # FIX-C5: Fallback from questionnaire
    if not vendors and briefing:
        vendors = _extract_vendors_from_briefing(briefing)
        if vendors:
            log.info("[G35][FIX-C5] Extracted %d vendors from questionnaire", len(vendors))

    # Generate audit entries
    entries: List[VendorAuditEntry] = []
    for vendor_info in vendors[:constraints["max_vendors"]]:
        entry = _generate_vendor_entry(vendor_info, ai_act_class)
        entries.append(entry)

    # Generate recommendations
    recommendations = _generate_recommendations(entries, size_label)

    # Generate summary
    summary = _generate_summary(entries)

    report = VendorAuditReport(
        entries=entries,
        summary=summary,
        recommendations=recommendations,
    )

    log.info(
        "[G35] Vendor Audit Report generated: %d vendors, %d green, %d yellow, %d red",
        report.total_vendors,
        report.green_count,
        report.yellow_count,
        report.red_count,
    )

    return report


# =============================================================================
# HTML RENDERING
# =============================================================================

def vendor_audit_report_to_html(
    report: VendorAuditReport,
    lang: str = "de",
    max_html_chars: int = 0,
) -> str:
    """
    Generate HTML section for Vendor Audit Report.

    Renders a Vendor Audit chapter in HTML with:
    - Overview
    - Green / Yellow / Red Vendors
    - Audit Flags
    - Recommendations

    Uses Platin++ Cards + Badges styling.

    Args:
        report: VendorAuditReport object
        lang: Language code ("de" or "en")
        max_html_chars: If > 0, limit output to this many characters.
                        Omits vendor cards from lowest-risk first until under budget.

    Returns:
        HTML string for PDF template
    """
    # Labels
    if lang == "en":
        labels = {
            "title": "Vendor Audit – AI-TUV for Your Tools",
            "subtitle": "Comprehensive vendor risk assessment",
            "overview": "Overview",
            "total_vendors": "Total Vendors",
            "green_vendors": "Low Risk (Green)",
            "yellow_vendors": "Medium Risk (Yellow)",
            "red_vendors": "High Risk (Red)",
            "eu_compliant": "EU-Compliant",
            "compliance_score": "Compliance Score",
            "vendor_details": "Vendor Details",
            "jurisdiction": "Jurisdiction",
            "data_location": "Data Location",
            "dpa_status": "DPA Status",
            "security": "Security",
            "certifications": "Certifications",
            "audit_flags": "Audit Flags",
            "recommendations": "Recommendations",
            "no_flags": "No issues found",
            "dpa_yes": "DPA Available",
            "dpa_no": "No DPA",
            "notes": "Notes",
            "ai_act": "AI Act Relevance",
            "dsgvo_risk": "GDPR Risk",
        }
    else:
        labels = {
            "title": "Vendor Audit – KI-TÜV für Ihre Tools",
            "subtitle": "Umfassende Anbieter-Risikobewertung",
            "overview": "Übersicht",
            "total_vendors": "Geprüfte Anbieter",
            "green_vendors": "Niedriges Risiko (Grün)",
            "yellow_vendors": "Mittleres Risiko (Gelb)",
            "red_vendors": "Hohes Risiko (Rot)",
            "eu_compliant": "EU-Konform",
            "compliance_score": "Compliance-Score",
            "vendor_details": "Anbieter-Details",
            "jurisdiction": "Jurisdiktion",
            "data_location": "Datenstandort",
            "dpa_status": "AVV-Status",
            "security": "Sicherheit",
            "certifications": "Zertifizierungen",
            "audit_flags": "Audit-Hinweise",
            "recommendations": "Empfehlungen",
            "no_flags": "Keine Auffälligkeiten",
            "dpa_yes": "AVV vorhanden",
            "dpa_no": "Kein AVV",
            "notes": "Hinweise",
            "ai_act": "AI Act Relevanz",
            "dsgvo_risk": "DSGVO-Risiko",
        }

    # Colors
    category_colors = {
        "green": "#22c55e",
        "yellow": "#f59e0b",
        "red": "#dc2626",
    }
    category_bg = {
        "green": "#f0fdf4",
        "yellow": "#fffbeb",
        "red": "#fef2f2",
    }
    category_border = {
        "green": "#86efac",
        "yellow": "#fcd34d",
        "red": "#fca5a5",
    }

    status_colors = {
        "pass": "#22c55e",
        "warn": "#f59e0b",
        "fail": "#dc2626",
    }

    html_parts = [f'''
    <div class="vendor-audit-engine" style="font-size:11pt;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            <span style="font-size:20px;">🔍</span>
            <span style="font-size:11px;padding:2px 8px;background:#8b5cf6;color:#fff;border-radius:4px;font-weight:600;">G35</span>
        </div>
    ''']

    # Summary Block
    status_color = status_colors.get(report.overall_audit_status, "#f59e0b")
    html_parts.append(f'''
        <div class="vendor-audit-summary" style="padding:16px;background:linear-gradient(135deg,#f8fafc 0%,#fff 100%);border-radius:12px;border:2px solid {status_color};margin-bottom:20px;">
            <p style="margin:0 0 12px 0;color:#64748b;font-size:10pt;">{report.summary}</p>

            <div style="margin-bottom:12px;">
                <table data-preserve="true" style="width:100%;border-collapse:separate;border-spacing:8px;table-layout:fixed;">
                <tr>
                <td style="padding:12px;background:{category_bg["green"]};border-radius:8px;border:1px solid {category_border["green"]};text-align:center;width:33%;">
                    <span style="font-size:9px;color:#166534;font-weight:600;">{labels["green_vendors"]}</span>
                    <div style="font-size:24px;font-weight:700;color:{category_colors["green"]};">{report.green_count}</div>
                </td>
                <td style="padding:12px;background:{category_bg["yellow"]};border-radius:8px;border:1px solid {category_border["yellow"]};text-align:center;width:33%;">
                    <span style="font-size:9px;color:#92400e;font-weight:600;">{labels["yellow_vendors"]}</span>
                    <div style="font-size:24px;font-weight:700;color:{category_colors["yellow"]};">{report.yellow_count}</div>
                </td>
                <td style="padding:12px;background:{category_bg["red"]};border-radius:8px;border:1px solid {category_border["red"]};text-align:center;width:33%;">
                    <span style="font-size:9px;color:#991b1b;font-weight:600;">{labels["red_vendors"]}</span>
                    <div style="font-size:24px;font-weight:700;color:{category_colors["red"]};">{report.red_count}</div>
                </td>
                </tr>
                </table>
            </div>

            <table data-preserve="true" style="width:100%;border-collapse:separate;border-spacing:8px;table-layout:fixed;margin-top:12px;">
            <tr>
                <td style="padding:8px;background:#fff;border-radius:6px;border:1px solid #e2e8f0;width:50%;">
                    <span style="font-size:9px;color:#64748b;">{labels["eu_compliant"]}</span>
                    <div style="font-size:14px;font-weight:600;color:#1e293b;">{report.eu_compliant_count} / {report.total_vendors}</div>
                </td>
                <td style="padding:8px;background:#fff;border-radius:6px;border:1px solid #e2e8f0;width:50%;">
                    <span style="font-size:9px;color:#64748b;">{labels["compliance_score"]}</span>
                    <div style="font-size:14px;font-weight:600;color:#1e293b;">{report.compliance_score:.0f}%</div>
                </td>
            </tr>
            </table>
        </div>
    ''')

    # Vendor Details Section
    if report.entries:
        html_parts.append(f'''
            <div class="vendor-details-section" style="margin-bottom:20px;">
                <p style="font-weight:700;font-size:12pt;color:#1e293b;margin:0 0 12px 0;">📋 {labels["vendor_details"]}</p>
        ''')

        # Sort entries: red first, then yellow, then green
        sorted_entries = sorted(
            report.entries,
            key=lambda e: {"red": 0, "yellow": 1, "green": 2}.get(e.overall_category, 1)
        )

        for entry in sorted_entries:
            cat_color = category_colors.get(entry.overall_category, "#f59e0b")
            cat_bg = category_bg.get(entry.overall_category, "#fffbeb")
            cat_border = category_border.get(entry.overall_category, "#fcd34d")

            # Jurisdiction badge color
            juris_color = "#3b82f6" if entry.jurisdiction == "EU" else (
                "#f59e0b" if entry.jurisdiction == "US" else "#64748b"
            )

            html_parts.append(f'''
                <div class="vendor-card" style="padding:16px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;border-left:4px solid {cat_color};margin-bottom:12px;page-break-inside:avoid;word-break:normal;overflow-wrap:break-word;word-wrap:break-word;">
                    <div style="margin-bottom:8px;">
                        <div style="display:inline-block;vertical-align:top;">
                            <h4 style="margin:0;font-size:11pt;color:#1e293b;font-weight:600;">{entry.name}</h4>
                            <span style="font-size:9px;color:#64748b;">{entry.category}</span>
                        </div>
                        <div style="display:block;margin-top:4px;">
                            <span style="font-size:9px;padding:2px 8px;background:{juris_color}22;color:{juris_color};border-radius:4px;border:1px solid {juris_color}44;">{entry.jurisdiction}</span>
                            <span style="font-size:9px;padding:2px 8px;background:{cat_bg};color:{cat_color};border-radius:4px;border:1px solid {cat_border};font-weight:600;">{entry.overall_category.upper()}</span>
                        </div>
                        <div style="clear:both;"></div>
                    </div>

                    <div style="margin-bottom:8px;word-break:normal;overflow-wrap:break-word;hyphens:none;-webkit-hyphens:none;">
                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;display:inline-block;margin:2px;">📍 {entry.data_location}</span>
                        <span style="font-size:8px;padding:2px 6px;background:{"#dcfce7" if entry.has_dpa else "#fef2f2"};color:{"#166534" if entry.has_dpa else "#991b1b"};border-radius:3px;border:1px solid {"#86efac" if entry.has_dpa else "#fca5a5"};display:inline-block;margin:2px;">📄 {labels["dpa_yes"] if entry.has_dpa else labels["dpa_no"]}</span>
                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;display:inline-block;margin:2px;">🔒 {entry.security_posture.title()}</span>
                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;display:inline-block;margin:2px;">⚖️ {labels["ai_act"]}: {entry.ai_act_relevance}</span>
                    </div>
            ''')

            # Certifications
            if entry.certifications:
                certs_html = " ".join([
                    f'<span style="font-size:7px;padding:1px 4px;background:#3b82f622;color:#3b82f6;border-radius:2px;">{cert}</span>'
                    for cert in entry.certifications[:4]
                ])
                html_parts.append(f'''
                    <div style="margin-bottom:8px;">
                        <span style="font-size:8px;color:#64748b;">{labels["certifications"]}:</span>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px;">{certs_html}</div>
                    </div>
                ''')

            # Audit Flags
            if entry.audit_flags:
                flags_html = " ".join([
                    f'<span style="font-size:7px;padding:1px 4px;background:#dc262622;color:#dc2626;border-radius:2px;">⚠️ {flag}</span>'
                    for flag in entry.audit_flags[:3]
                ])
                html_parts.append(f'''
                    <div>
                        <span style="font-size:8px;color:#dc2626;">{labels["audit_flags"]}:</span>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px;">{flags_html}</div>
                    </div>
                ''')
            else:
                html_parts.append(f'''
                    <div>
                        <span style="font-size:8px;color:#22c55e;">✓ {labels["no_flags"]}</span>
                    </div>
                ''')

            html_parts.append('</div>')

        html_parts.append('</div>')

    # Recommendations Section
    if report.recommendations:
        html_parts.append(f'''
            <div class="vendor-recommendations-section" style="padding:16px;background:#f0fdf4;border-radius:12px;border:1px solid #22c55e44;">
                <p style="font-weight:700;font-size:12pt;color:#166534;margin:0 0 12px 0;">💡 {labels["recommendations"]}</p>
                <ul style="margin:0;padding:0 0 0 16px;font-size:10pt;color:#1e293b;">
        ''')
        for rec in report.recommendations:
            html_parts.append(f'<li style="margin-bottom:6px;">{rec}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div>')

    full_html = '\n'.join(html_parts)

    # FIX-WP4-VENDOR: Budget enforcement — if output exceeds max_html_chars,
    # use compact table format instead of full card layout.
    if max_html_chars > 0 and len(full_html) > max_html_chars and report.entries:
        log.info(
            "[G35] Budget enforcement: full=%d chars > %d limit, switching to compact mode",
            len(full_html), max_html_chars,
        )
        # Compact table format — fits any number of vendors in ~2000-3000 chars
        t = labels
        rows = ""
        sorted_entries = sorted(
            report.entries,
            key=lambda e: {"red": 0, "yellow": 1, "green": 2}.get(e.overall_category, 1)
        )
        for e in sorted_entries:
            cat_c = category_colors.get(e.overall_category, "#f59e0b")
            dpa_icon = "✓" if e.has_dpa else "✗"
            dpa_c = "#166534" if e.has_dpa else "#991b1b"
            flags_str = ", ".join(e.audit_flags[:2]) if e.audit_flags else "–"
            rows += (
                f'<tr><td style="padding:6px;border-bottom:1px solid #e2e8f0;">'
                f'<strong>{e.name}</strong><br><span style="font-size:8px;color:#64748b;">{e.category}</span></td>'
                f'<td style="padding:6px;border-bottom:1px solid #e2e8f0;text-align:center;">'
                f'<span style="color:{cat_c};font-weight:700;">{e.overall_category.upper()}</span></td>'
                f'<td style="padding:6px;border-bottom:1px solid #e2e8f0;">{e.jurisdiction} · {e.data_location}</td>'
                f'<td style="padding:6px;border-bottom:1px solid #e2e8f0;color:{dpa_c};">{dpa_icon}</td>'
                f'<td style="padding:6px;border-bottom:1px solid #e2e8f0;font-size:8px;">{flags_str}</td></tr>'
            )
        recs_html = ""
        if report.recommendations:
            recs_html = '<ul style="margin:8px 0 0 16px;font-size:9pt;">' + "".join(
                f'<li>{r}</li>' for r in report.recommendations[:3]
            ) + '</ul>'

        compact_html = f'''<div class="vendor-audit-engine" style="font-size:10pt;">
<p style="font-weight:700;margin:0 0 8px;">🔍 {t["title"]}</p>
<p style="font-size:9px;color:#64748b;margin:0 0 8px;">{t["green_vendors"]}: {report.green_count} · {t["yellow_vendors"]}: {report.yellow_count} · {t["red_vendors"]}: {report.red_count} · {t["compliance_score"]}: {report.compliance_score:.0f}%</p>
<table data-preserve="true" style="width:100%;border-collapse:collapse;font-size:9pt;">
<tr style="background:#f8fafc;"><th style="padding:6px;text-align:left;">Vendor</th><th style="padding:6px;">Status</th><th style="padding:6px;text-align:left;">{t["jurisdiction"]}</th><th style="padding:6px;">AVV</th><th style="padding:6px;text-align:left;">Flags</th></tr>
{rows}
</table>
{recs_html}
</div>'''
        log.info("[G35] Compact mode: %d chars (limit %d)", len(compact_html), max_html_chars)
        return compact_html

    return full_html


# =============================================================================
# VALIDATION HELPERS (for Consistency Engine)
# =============================================================================

def validate_vendor_risk_scores(
    report: VendorAuditReport,
    tools_data: Optional[Any] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate vendor risk scores are consistent with Tools Engine 4.0.

    VA_001: vendor_risk_score in VendorAuditEntry must not be lower
    than vendor_risk from Tools Engine 4.0.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    if not tools_data:
        return True, []

    vendors = _extract_vendors_from_tools(tools_data)
    tools_risk_map = {v["name"]: v.get("vendor_risk", 3) for v in vendors}

    for entry in report.entries:
        tools_risk = tools_risk_map.get(entry.name, 3)
        if entry.vendor_risk_score < tools_risk:
            errors.append(
                f"Vendor '{entry.name}' risk score ({entry.vendor_risk_score}) "
                f"is lower than Tools Engine risk ({tools_risk})"
            )

    return len(errors) == 0, errors


def validate_red_vendors_in_risk_report(
    report: VendorAuditReport,
    risk_report_v3: Optional[Any] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate red vendors appear in Risk Report or Mitigation Plan.

    VA_002: Vendors with overall_category='red' must appear in
    RiskReportV3 as risk or be addressed in Mitigation Plan.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    red_vendors = [e.name for e in report.entries if e.overall_category == "red"]

    if not red_vendors:
        return True, []

    if not risk_report_v3:
        errors.append(
            f"Red vendors ({', '.join(red_vendors[:3])}) exist but no Risk Report V3 available"
        )
        return False, errors

    # Check mitigation plan
    mitigation_plan = []
    if hasattr(risk_report_v3, "mitigation_plan"):
        mitigation_plan = risk_report_v3.mitigation_plan
    elif isinstance(risk_report_v3, dict):
        mitigation_plan = risk_report_v3.get("mitigation_plan", [])

    mitigation_text = " ".join(str(m) for m in mitigation_plan).lower()

    for vendor in red_vendors:
        if vendor.lower() not in mitigation_text:
            errors.append(
                f"Red vendor '{vendor}' not addressed in Risk Report mitigation plan"
            )

    return len(errors) == 0, errors


def validate_us_vendors_not_green(
    report: VendorAuditReport,
) -> Tuple[bool, List[str]]:
    """
    Validate US vendors without DPA are not classified as green.

    VA_003: Vendors with jurisdiction='US' and has_dpa=False
    must not have overall_category='green'.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    for entry in report.entries:
        if (entry.jurisdiction == "US" and
            not entry.has_dpa and
            entry.overall_category == "green"):
            errors.append(
                f"US vendor '{entry.name}' without DPA incorrectly classified as green"
            )

    return len(errors) == 0, errors


def validate_eu_hosting_not_red_without_flags(
    report: VendorAuditReport,
    tools_data: Optional[Any] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate EU-hosted tools with good compliance aren't red without reason.

    VA_004: Tools with eu_hosting=True and compliance_score <= 2
    must not be classified as red without audit_flags.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    if not tools_data:
        return True, []

    vendors = _extract_vendors_from_tools(tools_data)
    tools_info = {
        v["name"]: {
            "eu_hosting": v.get("eu_hosting"),
            "compliance_score": v.get("compliance_score", 3),
        }
        for v in vendors
    }

    for entry in report.entries:
        info = tools_info.get(entry.name, {})
        eu_hosting = info.get("eu_hosting")
        compliance_score = info.get("compliance_score", 3)

        if (eu_hosting is True and
            compliance_score <= 2 and
            entry.overall_category == "red" and
            not entry.audit_flags):
            errors.append(
                f"EU-hosted vendor '{entry.name}' with good compliance score "
                f"classified as red without audit flags"
            )

    return len(errors) == 0, errors


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G35] Vendor Audit Engine loaded")
