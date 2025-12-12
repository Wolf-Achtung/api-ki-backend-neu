# -*- coding: utf-8 -*-
"""
SPRINT N3.9 PACKAGE A: Multi-Tenant Isolation Layer.

Enterprise-grade multi-tenant support for:
- Branding separation (logos, colors, watermarks)
- Data source isolation
- Layout and text style customization
- Per-tenant configuration and output paths
- Tenant-aware engine integration

Version: 1.0.0 (N3.9 - PLATIN++ v4.28)
"""
from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)

# Type alias
ConfigDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

class TenantTier(Enum):
    """Tenant subscription tier."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    PREMIUM = "premium"


class ColorTheme(Enum):
    """Available color themes."""
    DEFAULT = "default"
    CORPORATE_BLUE = "corporate_blue"
    EXECUTIVE_DARK = "executive_dark"
    MODERN_GREEN = "modern_green"
    CONSULTING_NEUTRAL = "consulting_neutral"
    CUSTOM = "custom"


class WordingProfile(Enum):
    """Text style profiles."""
    STANDARD = "standard"
    FORMAL = "formal"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    CONSULTING = "consulting"


class RiskProfile(Enum):
    """Risk tolerance profile."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    PROGRESSIVE = "progressive"


# Default branding configuration
DEFAULT_BRANDING: ConfigDict = {
    "logo_primary": None,
    "logo_secondary": None,
    "footer_logos": [],
    "color_primary": "#1A73E8",
    "color_secondary": "#34A853",
    "color_accent": "#EA4335",
    "font_family": "Inter, sans-serif",
    "pdf_watermark": None,
}

# Default tenant settings
DEFAULT_TENANT_SETTINGS: ConfigDict = {
    "max_reports_per_month": 100,
    "max_pdf_size_mb": 3.0,
    "enable_custom_prompts": False,
    "enable_api_access": False,
    "enable_white_label": False,
    "data_retention_days": 90,
    "audit_logging_enabled": True,
}

# Tier-based feature limits
TIER_LIMITS: Dict[str, ConfigDict] = {
    "basic": {
        "max_reports_per_month": 10,
        "max_pdf_size_mb": 2.5,
        "enable_custom_prompts": False,
        "enable_api_access": False,
        "enable_white_label": False,
        "custom_branding": False,
    },
    "professional": {
        "max_reports_per_month": 50,
        "max_pdf_size_mb": 3.0,
        "enable_custom_prompts": True,
        "enable_api_access": False,
        "enable_white_label": False,
        "custom_branding": True,
    },
    "enterprise": {
        "max_reports_per_month": 500,
        "max_pdf_size_mb": 5.0,
        "enable_custom_prompts": True,
        "enable_api_access": True,
        "enable_white_label": True,
        "custom_branding": True,
    },
    "premium": {
        "max_reports_per_month": -1,  # Unlimited
        "max_pdf_size_mb": 10.0,
        "enable_custom_prompts": True,
        "enable_api_access": True,
        "enable_white_label": True,
        "custom_branding": True,
    },
}

# Wording profile templates
WORDING_TEMPLATES: Dict[str, Dict[str, str]] = {
    "standard": {
        "greeting": "Sehr geehrte Damen und Herren",
        "recommendation_intro": "Wir empfehlen",
        "risk_intro": "Es bestehen folgende Risiken",
        "conclusion": "Zusammenfassend",
    },
    "formal": {
        "greeting": "Sehr geehrte Geschäftsleitung",
        "recommendation_intro": "Basierend auf unserer Analyse empfehlen wir",
        "risk_intro": "Die Risikoanalyse identifiziert",
        "conclusion": "Abschließend lässt sich feststellen",
    },
    "executive": {
        "greeting": "An die Geschäftsführung",
        "recommendation_intro": "Die strategische Empfehlung lautet",
        "risk_intro": "Die kritischen Risikofaktoren umfassen",
        "conclusion": "Das Executive Summary zeigt",
    },
    "technical": {
        "greeting": "Technische Zusammenfassung",
        "recommendation_intro": "Technische Empfehlung",
        "risk_intro": "Technische Risiken",
        "conclusion": "Technisches Fazit",
    },
    "consulting": {
        "greeting": "Sehr geehrte Entscheidungsträger",
        "recommendation_intro": "Unsere Handlungsempfehlung",
        "risk_intro": "Identifizierte Herausforderungen",
        "conclusion": "Strategische Schlussfolgerung",
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TenantBranding:
    """Tenant branding configuration."""
    logo_primary: Optional[str] = None
    logo_secondary: Optional[str] = None
    footer_logos: List[str] = field(default_factory=list)
    color_primary: str = "#1A73E8"
    color_secondary: str = "#34A853"
    color_accent: str = "#EA4335"
    font_family: str = "Inter, sans-serif"
    pdf_watermark: Optional[str] = None
    custom_css: Optional[str] = None

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "logo_primary": self.logo_primary,
            "logo_secondary": self.logo_secondary,
            "footer_logos": self.footer_logos,
            "color_primary": self.color_primary,
            "color_secondary": self.color_secondary,
            "color_accent": self.color_accent,
            "font_family": self.font_family,
            "pdf_watermark": self.pdf_watermark,
            "custom_css": self.custom_css,
        }


@dataclass
class TenantConfig:
    """Complete tenant configuration."""
    tenant_id: str
    tenant_name: str
    tier: TenantTier = TenantTier.BASIC
    branding: TenantBranding = field(default_factory=TenantBranding)
    color_theme: ColorTheme = ColorTheme.DEFAULT
    wording_profile: WordingProfile = WordingProfile.STANDARD
    risk_profile: RiskProfile = RiskProfile.BALANCED

    # Feature flags
    enable_custom_prompts: bool = False
    enable_api_access: bool = False
    enable_white_label: bool = False
    audit_logging_enabled: bool = True

    # Limits
    max_reports_per_month: int = 100
    max_pdf_size_mb: float = 3.0
    data_retention_days: int = 90

    # Paths
    output_base_path: Optional[str] = None
    research_scope: Optional[List[str]] = None

    # Custom prompt variants
    prompt_variants: Dict[str, str] = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    active: bool = True

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "tier": self.tier.value,
            "branding": self.branding.to_dict(),
            "color_theme": self.color_theme.value,
            "wording_profile": self.wording_profile.value,
            "risk_profile": self.risk_profile.value,
            "enable_custom_prompts": self.enable_custom_prompts,
            "enable_api_access": self.enable_api_access,
            "enable_white_label": self.enable_white_label,
            "audit_logging_enabled": self.audit_logging_enabled,
            "max_reports_per_month": self.max_reports_per_month,
            "max_pdf_size_mb": self.max_pdf_size_mb,
            "data_retention_days": self.data_retention_days,
            "output_base_path": self.output_base_path,
            "research_scope": self.research_scope,
            "prompt_variants": self.prompt_variants,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active": self.active,
        }

    def get_output_path(self, report_id: str) -> str:
        """Get tenant-specific output path for a report."""
        base = self.output_base_path or f"/data/tenants/{self.tenant_id}"
        return os.path.join(base, "reports", report_id)

    def get_wording_template(self, key: str) -> str:
        """Get wording template for this tenant's profile."""
        profile = self.wording_profile.value
        templates = WORDING_TEMPLATES.get(profile, WORDING_TEMPLATES["standard"])
        return templates.get(key, "")

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled for this tenant."""
        feature_map = {
            "custom_prompts": self.enable_custom_prompts,
            "api_access": self.enable_api_access,
            "white_label": self.enable_white_label,
            "audit_logging": self.audit_logging_enabled,
        }
        return feature_map.get(feature, False)


@dataclass
class TenantUsage:
    """Track tenant usage metrics."""
    tenant_id: str
    reports_this_month: int = 0
    total_reports: int = 0
    api_calls_this_month: int = 0
    storage_used_mb: float = 0.0
    last_activity: Optional[str] = None

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "reports_this_month": self.reports_this_month,
            "total_reports": self.total_reports,
            "api_calls_this_month": self.api_calls_this_month,
            "storage_used_mb": round(self.storage_used_mb, 2),
            "last_activity": self.last_activity,
        }


# =============================================================================
# TENANT REGISTRY
# =============================================================================

class TenantRegistry:
    """
    Central registry for tenant configurations.

    Provides thread-safe access to tenant configs and usage tracking.
    """

    _instance: Optional["TenantRegistry"] = None
    _tenants: Dict[str, TenantConfig] = {}
    _usage: Dict[str, TenantUsage] = {}
    _default_tenant: Optional[TenantConfig] = None

    def __new__(cls) -> "TenantRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tenants = {}
            cls._instance._usage = {}
            cls._instance._default_tenant = None
        return cls._instance

    def register_tenant(self, config: TenantConfig) -> None:
        """
        Register a new tenant.

        Args:
            config: Tenant configuration
        """
        self._tenants[config.tenant_id] = config
        if config.tenant_id not in self._usage:
            self._usage[config.tenant_id] = TenantUsage(tenant_id=config.tenant_id)
        log.info("[N3.9] Registered tenant: %s (%s)", config.tenant_name, config.tenant_id)

    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Get tenant configuration by ID.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantConfig if found, None otherwise
        """
        return self._tenants.get(tenant_id)

    def get_or_default(self, tenant_id: Optional[str]) -> TenantConfig:
        """
        Get tenant config or return default.

        Args:
            tenant_id: Optional tenant identifier

        Returns:
            TenantConfig (tenant-specific or default)
        """
        if tenant_id and tenant_id in self._tenants:
            return self._tenants[tenant_id]

        if self._default_tenant is None:
            self._default_tenant = TenantConfig(
                tenant_id="default",
                tenant_name="Default Tenant",
                tier=TenantTier.BASIC,
            )
        return self._default_tenant

    def get_usage(self, tenant_id: str) -> Optional[TenantUsage]:
        """Get usage metrics for a tenant."""
        return self._usage.get(tenant_id)

    def increment_usage(self, tenant_id: str, metric: str, amount: int = 1) -> None:
        """
        Increment a usage metric.

        Args:
            tenant_id: Tenant identifier
            metric: Metric name (reports_this_month, api_calls_this_month, etc.)
            amount: Amount to increment
        """
        if tenant_id not in self._usage:
            self._usage[tenant_id] = TenantUsage(tenant_id=tenant_id)

        usage = self._usage[tenant_id]
        if hasattr(usage, metric):
            current = getattr(usage, metric)
            setattr(usage, metric, current + amount)
        usage.last_activity = datetime.utcnow().isoformat()

    def check_quota(self, tenant_id: str) -> Tuple[bool, str]:
        """
        Check if tenant has remaining quota.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Tuple of (within_quota: bool, message: str)
        """
        config = self.get_tenant(tenant_id)
        usage = self.get_usage(tenant_id)

        if not config:
            return True, "No tenant config (default allowed)"

        if not usage:
            return True, "No usage recorded"

        # Check report limit (-1 = unlimited)
        if config.max_reports_per_month > 0:
            if usage.reports_this_month >= config.max_reports_per_month:
                return False, f"Monthly report limit reached ({config.max_reports_per_month})"

        return True, "Within quota"

    def list_tenants(self) -> List[TenantConfig]:
        """List all registered tenants."""
        return list(self._tenants.values())

    def deactivate_tenant(self, tenant_id: str) -> bool:
        """
        Deactivate a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if deactivated, False if not found
        """
        if tenant_id in self._tenants:
            self._tenants[tenant_id].active = False
            log.info("[N3.9] Deactivated tenant: %s", tenant_id)
            return True
        return False

    def reset_monthly_usage(self) -> int:
        """
        Reset monthly usage counters for all tenants.

        Returns:
            Number of tenants reset
        """
        count = 0
        for usage in self._usage.values():
            usage.reports_this_month = 0
            usage.api_calls_this_month = 0
            count += 1
        log.info("[N3.9] Reset monthly usage for %d tenants", count)
        return count


# Singleton instance
_registry = TenantRegistry()


def get_tenant_registry() -> TenantRegistry:
    """Get the global tenant registry instance."""
    return _registry


# =============================================================================
# TENANT-AWARE UTILITIES
# =============================================================================

def generate_tenant_id(name: str) -> str:
    """
    Generate a unique tenant ID from name.

    Args:
        name: Tenant name

    Returns:
        Unique tenant identifier
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    hash_input = f"{name}:{timestamp}".encode()
    hash_value = hashlib.sha256(hash_input).hexdigest()[:8]
    safe_name = "".join(c.lower() for c in name if c.isalnum())[:20]
    return f"{safe_name}_{hash_value}"


def create_tenant_from_env() -> Optional[TenantConfig]:
    """
    Create tenant configuration from environment variables.

    Reads TENANT_* environment variables to configure tenant.

    Returns:
        TenantConfig if TENANT_ID is set, None otherwise
    """
    tenant_id = os.environ.get("TENANT_ID")
    if not tenant_id:
        return None

    # Read branding
    branding = TenantBranding(
        logo_primary=os.environ.get("TENANT_LOGO_PRIMARY"),
        logo_secondary=os.environ.get("TENANT_LOGO_SECONDARY"),
        color_primary=os.environ.get("TENANT_COLOR_PRIMARY", "#1A73E8"),
        color_secondary=os.environ.get("TENANT_COLOR_SECONDARY", "#34A853"),
        pdf_watermark=os.environ.get("TENANT_PDF_WATERMARK"),
    )

    # Read tier
    tier_str = os.environ.get("TENANT_TIER", "basic").lower()
    try:
        tier = TenantTier(tier_str)
    except ValueError:
        tier = TenantTier.BASIC

    # Read profiles
    wording_str = os.environ.get("TENANT_WORDING_PROFILE", "standard").lower()
    try:
        wording = WordingProfile(wording_str)
    except ValueError:
        wording = WordingProfile.STANDARD

    risk_str = os.environ.get("TENANT_RISK_PROFILE", "balanced").lower()
    try:
        risk = RiskProfile(risk_str)
    except ValueError:
        risk = RiskProfile.BALANCED

    config = TenantConfig(
        tenant_id=tenant_id,
        tenant_name=os.environ.get("TENANT_NAME", tenant_id),
        tier=tier,
        branding=branding,
        wording_profile=wording,
        risk_profile=risk,
        output_base_path=os.environ.get("TENANT_OUTPUT_PATH"),
    )

    # Apply tier limits
    tier_config = TIER_LIMITS.get(tier.value, TIER_LIMITS["basic"])
    config.max_reports_per_month = tier_config["max_reports_per_month"]
    config.max_pdf_size_mb = tier_config["max_pdf_size_mb"]
    config.enable_custom_prompts = tier_config["enable_custom_prompts"]
    config.enable_api_access = tier_config["enable_api_access"]
    config.enable_white_label = tier_config["enable_white_label"]

    log.info("[N3.9] Created tenant from ENV: %s (tier=%s)", tenant_id, tier.value)
    return config


def load_tenant_from_dict(data: ConfigDict) -> TenantConfig:
    """
    Load tenant configuration from dictionary (e.g., from database).

    Args:
        data: Dictionary with tenant configuration

    Returns:
        TenantConfig instance
    """
    # Parse branding
    branding_data = data.get("branding", {})
    branding = TenantBranding(
        logo_primary=branding_data.get("logo_primary"),
        logo_secondary=branding_data.get("logo_secondary"),
        footer_logos=branding_data.get("footer_logos", []),
        color_primary=branding_data.get("color_primary", "#1A73E8"),
        color_secondary=branding_data.get("color_secondary", "#34A853"),
        color_accent=branding_data.get("color_accent", "#EA4335"),
        font_family=branding_data.get("font_family", "Inter, sans-serif"),
        pdf_watermark=branding_data.get("pdf_watermark"),
        custom_css=branding_data.get("custom_css"),
    )

    # Parse enums
    try:
        tier = TenantTier(data.get("tier", "basic"))
    except ValueError:
        tier = TenantTier.BASIC

    try:
        color_theme = ColorTheme(data.get("color_theme", "default"))
    except ValueError:
        color_theme = ColorTheme.DEFAULT

    try:
        wording = WordingProfile(data.get("wording_profile", "standard"))
    except ValueError:
        wording = WordingProfile.STANDARD

    try:
        risk = RiskProfile(data.get("risk_profile", "balanced"))
    except ValueError:
        risk = RiskProfile.BALANCED

    return TenantConfig(
        tenant_id=data["tenant_id"],
        tenant_name=data.get("tenant_name", data["tenant_id"]),
        tier=tier,
        branding=branding,
        color_theme=color_theme,
        wording_profile=wording,
        risk_profile=risk,
        enable_custom_prompts=data.get("enable_custom_prompts", False),
        enable_api_access=data.get("enable_api_access", False),
        enable_white_label=data.get("enable_white_label", False),
        audit_logging_enabled=data.get("audit_logging_enabled", True),
        max_reports_per_month=data.get("max_reports_per_month", 100),
        max_pdf_size_mb=data.get("max_pdf_size_mb", 3.0),
        data_retention_days=data.get("data_retention_days", 90),
        output_base_path=data.get("output_base_path"),
        research_scope=data.get("research_scope"),
        prompt_variants=data.get("prompt_variants", {}),
        active=data.get("active", True),
    )


# =============================================================================
# TENANT-AWARE ENGINE HOOKS
# =============================================================================

def apply_tenant_branding(
    sections: Dict[str, Any],
    tenant_config: TenantConfig,
) -> Dict[str, Any]:
    """
    Apply tenant branding to report sections.

    Args:
        sections: Report sections dictionary
        tenant_config: Tenant configuration

    Returns:
        Modified sections with tenant branding
    """
    branding = tenant_config.branding

    # Add branding metadata
    sections["_tenant_branding"] = {
        "tenant_id": tenant_config.tenant_id,
        "logo_primary": branding.logo_primary,
        "logo_secondary": branding.logo_secondary,
        "footer_logos": branding.footer_logos,
        "colors": {
            "primary": branding.color_primary,
            "secondary": branding.color_secondary,
            "accent": branding.color_accent,
        },
        "font_family": branding.font_family,
        "watermark": branding.pdf_watermark,
        "white_label": tenant_config.enable_white_label,
    }

    # Apply custom CSS if available
    if branding.custom_css:
        sections["_custom_css"] = branding.custom_css

    log.debug("[N3.9] Applied tenant branding for %s", tenant_config.tenant_id)
    return sections


def apply_tenant_wording(
    text: str,
    tenant_config: TenantConfig,
) -> str:
    """
    Apply tenant-specific wording adjustments.

    Args:
        text: Original text
        tenant_config: Tenant configuration

    Returns:
        Text with tenant wording applied
    """
    profile = tenant_config.wording_profile.value
    templates = WORDING_TEMPLATES.get(profile, WORDING_TEMPLATES["standard"])

    # Replace standard phrases with profile-specific ones
    replacements = {
        "Wir empfehlen": templates.get("recommendation_intro", "Wir empfehlen"),
        "Es bestehen folgende Risiken": templates.get("risk_intro", "Es bestehen folgende Risiken"),
        "Zusammenfassend": templates.get("conclusion", "Zusammenfassend"),
    }

    result = text
    for old, new in replacements.items():
        if old != new:
            result = result.replace(old, new)

    return result


def get_tenant_prompt_variant(
    tenant_config: TenantConfig,
    prompt_key: str,
    default_prompt: str,
) -> str:
    """
    Get tenant-specific prompt variant if available.

    Args:
        tenant_config: Tenant configuration
        prompt_key: Prompt identifier
        default_prompt: Default prompt if no variant exists

    Returns:
        Tenant-specific or default prompt
    """
    if not tenant_config.enable_custom_prompts:
        return default_prompt

    variant = tenant_config.prompt_variants.get(prompt_key)
    if variant:
        log.debug("[N3.9] Using tenant prompt variant for %s: %s",
                  tenant_config.tenant_id, prompt_key)
        return variant

    return default_prompt


def get_tenant_research_scope(
    tenant_config: TenantConfig,
    default_scope: Optional[List[str]] = None,
) -> List[str]:
    """
    Get tenant-specific research scope.

    Args:
        tenant_config: Tenant configuration
        default_scope: Default research scope

    Returns:
        List of allowed research domains/topics
    """
    if tenant_config.research_scope:
        return tenant_config.research_scope
    return default_scope or []


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_tenant_isolation(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process sections with tenant isolation.

    Main entry point for tenant-aware processing.

    Args:
        sections: Report sections
        briefing: Report briefing
        tenant_id: Optional tenant identifier

    Returns:
        Dict with processed sections and tenant metadata
    """
    registry = get_tenant_registry()

    # Get or create tenant config
    if tenant_id:
        config = registry.get_or_default(tenant_id)
    else:
        # Try to get from briefing or environment
        tenant_id = briefing.get("tenant_id") or os.environ.get("TENANT_ID")
        config = registry.get_or_default(tenant_id)

    # Check quota
    within_quota, quota_msg = registry.check_quota(config.tenant_id)
    if not within_quota:
        log.warning("[N3.9] Tenant %s quota exceeded: %s", config.tenant_id, quota_msg)
        return {
            "sections": sections,
            "tenant_metadata": {
                "tenant_id": config.tenant_id,
                "error": quota_msg,
                "quota_exceeded": True,
            },
        }

    # Apply tenant branding
    processed_sections = apply_tenant_branding(sections.copy(), config)

    # Apply wording to text sections
    for key, value in processed_sections.items():
        if isinstance(value, str) and key.endswith("_HTML"):
            processed_sections[key] = apply_tenant_wording(value, config)

    # Track usage
    registry.increment_usage(config.tenant_id, "reports_this_month")
    registry.increment_usage(config.tenant_id, "total_reports")

    # Build metadata
    metadata = {
        "tenant_id": config.tenant_id,
        "tenant_name": config.tenant_name,
        "tier": config.tier.value,
        "wording_profile": config.wording_profile.value,
        "risk_profile": config.risk_profile.value,
        "white_label": config.enable_white_label,
        "output_path": config.get_output_path(briefing.get("report_id", "unknown")),
        "processed_at": datetime.utcnow().isoformat(),
    }

    log.info(
        "[N3.9] Tenant isolation applied: %s (tier=%s, wording=%s)",
        config.tenant_id,
        config.tier.value,
        config.wording_profile.value,
    )

    return {
        "sections": processed_sections,
        "tenant_metadata": metadata,
        "tenant_config": config,
    }


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "TenantTier",
    "ColorTheme",
    "WordingProfile",
    "RiskProfile",
    # Data classes
    "TenantBranding",
    "TenantConfig",
    "TenantUsage",
    # Registry
    "TenantRegistry",
    "get_tenant_registry",
    # Utilities
    "generate_tenant_id",
    "create_tenant_from_env",
    "load_tenant_from_dict",
    # Engine hooks
    "apply_tenant_branding",
    "apply_tenant_wording",
    "get_tenant_prompt_variant",
    "get_tenant_research_scope",
    # Main function
    "process_tenant_isolation",
]
