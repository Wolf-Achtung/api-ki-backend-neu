# -*- coding: utf-8 -*-
"""
Sprint G12: Business Case Reconciler

Post-AI-Act validation to ensure business case data is logically consistent:
- ROI cannot be negative with positive savings
- Payback period must be >= 0
- CAPEX/OPEX modifiers must be documented
- Consistent rounding across all values

Version: 1.0.0 (Sprint G12)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

BC_RECONCILE_ENABLED = os.getenv("BC_RECONCILE_ENABLED", "1").lower() in ("1", "true", "yes")
BC_ROUNDING_DECIMALS = int(os.getenv("BC_ROUNDING_DECIMALS", "1"))
BC_FAIL_ON_INCONSISTENCY = os.getenv("BC_FAIL_ON_INCONSISTENCY", "0").lower() in ("1", "true", "yes")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ReconcileIssue:
    """A single reconciliation issue."""
    code: str
    severity: str  # error, warning, info, auto_fixed
    message: str
    field: str = ""
    original_value: Any = None
    fixed_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.field:
            result["field"] = self.field
        if self.original_value is not None:
            result["original_value"] = self.original_value
        if self.fixed_value is not None:
            result["fixed_value"] = self.fixed_value
        return result


@dataclass
class ReconcileResult:
    """Result of reconciliation process."""
    success: bool = True
    issues: List[ReconcileIssue] = field(default_factory=list)
    fixes_applied: int = 0
    original_values: Dict[str, Any] = field(default_factory=dict)

    def add_issue(
        self,
        code: str,
        severity: str,
        message: str,
        field: str = "",
        original: Any = None,
        fixed: Any = None,
    ) -> None:
        issue = ReconcileIssue(
            code=code,
            severity=severity,
            message=message,
            field=field,
            original_value=original,
            fixed_value=fixed,
        )
        self.issues.append(issue)

        if severity == "error":
            self.success = False
        elif severity == "auto_fixed":
            self.fixes_applied += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "fixes_applied": self.fixes_applied,
            "error_count": len([i for i in self.issues if i.severity == "error"]),
            "warning_count": len([i for i in self.issues if i.severity == "warning"]),
            "issues": [i.to_dict() for i in self.issues],
        }


# =============================================================================
# RECONCILER IMPLEMENTATION
# =============================================================================

class BusinessCaseReconciler:
    """
    Validates and reconciles business case data post-AI-Act modifications.

    Rules:
    1. ROI cannot be negative when savings are positive
    2. Payback must be >= 0 (None allowed for invalid scenarios)
    3. CAPEX/OPEX modifiers must be present when AI Act applied
    4. All monetary values rounded consistently
    5. Savings must cover OPEX for positive ROI claim
    """

    def __init__(self, rounding_decimals: int = BC_ROUNDING_DECIMALS):
        self.rounding_decimals = rounding_decimals

    def reconcile(
        self,
        sections: Dict[str, Any],
        apply_fixes: bool = True,
    ) -> ReconcileResult:
        """
        Reconcile business case data.

        Args:
            sections: Report sections dict (modified in-place if apply_fixes=True)
            apply_fixes: Whether to apply automatic fixes

        Returns:
            ReconcileResult with issues and fixes
        """
        result = ReconcileResult()

        if not BC_RECONCILE_ENABLED:
            result.add_issue(
                "RECONCILE_DISABLED",
                "info",
                "BC reconciliation is disabled",
            )
            return result

        # Extract relevant values
        capex = self._get_float(sections, "CAPEX_REALISTISCH_EUR", 0)
        opex = self._get_float(sections, "OPEX_REALISTISCH_EUR", 0)
        einsparung = self._get_float(sections, "EINSPARUNG_MONAT_EUR", 0)
        roi = self._get_float(sections, "ROI_12M")
        payback = self._get_float(sections, "PAYBACK_MONTHS")

        # AI Act related
        ai_act_applied = sections.get("AI_ACT_BC_APPLIED", False)
        capex_factor = self._get_float(sections, "AI_ACT_BC_CAPEX_FACTOR", 1.0)
        opex_factor = self._get_float(sections, "AI_ACT_BC_OPEX_FACTOR", 1.0)
        original_capex = self._get_float(sections, "AI_ACT_BC_ORIGINAL_CAPEX")
        original_opex = self._get_float(sections, "AI_ACT_BC_ORIGINAL_OPEX")

        # Store original values for reference
        result.original_values = {
            "CAPEX_REALISTISCH_EUR": capex,
            "OPEX_REALISTISCH_EUR": opex,
            "ROI_12M": roi,
            "PAYBACK_MONTHS": payback,
        }

        # Rule 1: Validate ROI consistency
        self._validate_roi(result, sections, capex, opex, einsparung, roi, apply_fixes)

        # Rule 2: Validate payback period
        self._validate_payback(result, sections, payback, apply_fixes)

        # Rule 3: Validate AI Act modifier documentation
        self._validate_ai_act_modifiers(
            result, sections, ai_act_applied,
            capex_factor, opex_factor, original_capex, original_opex
        )

        # Rule 4: Apply consistent rounding
        self._apply_rounding(result, sections, apply_fixes)

        # Rule 5: Validate savings cover OPEX
        self._validate_savings_coverage(result, einsparung, opex)

        # Log result
        if not result.success:
            log.warning(
                "[G12-BCReconcile] Reconciliation issues: %d errors, %d warnings, %d fixes",
                len([i for i in result.issues if i.severity == "error"]),
                len([i for i in result.issues if i.severity == "warning"]),
                result.fixes_applied,
            )
        elif result.fixes_applied > 0:
            log.info("[G12-BCReconcile] Applied %d automatic fixes", result.fixes_applied)

        return result

    def _get_float(
        self,
        sections: Dict[str, Any],
        key: str,
        default: Optional[float] = None,
    ) -> Optional[float]:
        """Safely get float value from sections."""
        value = sections.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _validate_roi(
        self,
        result: ReconcileResult,
        sections: Dict[str, Any],
        capex: float,
        opex: float,
        einsparung: float,
        roi: Optional[float],
        apply_fixes: bool,
    ) -> None:
        """Validate ROI is logically consistent."""
        if roi is None:
            return

        # Calculate expected ROI
        yearly_savings = einsparung * 12
        yearly_opex = opex * 12
        net_benefit = yearly_savings - yearly_opex

        if capex > 0:
            expected_roi = round((net_benefit - capex) / capex * 100, self.rounding_decimals)
        else:
            expected_roi = 0.0

        # Check: Negative ROI with positive net benefit (after covering CAPEX eventually)
        if roi < 0 and einsparung > opex and einsparung > 0:
            # This might be valid if yearly benefit doesn't cover CAPEX in first year
            first_year_profit = net_benefit - capex
            if first_year_profit > 0:
                result.add_issue(
                    "ROI_SIGN_MISMATCH",
                    "warning",
                    f"ROI is negative ({roi}%) but first-year profit is positive",
                    field="ROI_12M",
                    original=roi,
                )

        # Check: ROI significantly different from calculation
        if abs(roi - expected_roi) > 5:  # More than 5% difference
            result.add_issue(
                "ROI_CALCULATION_MISMATCH",
                "warning",
                f"ROI ({roi}%) differs from calculated value ({expected_roi}%)",
                field="ROI_12M",
                original=roi,
                fixed=expected_roi,
            )

            if apply_fixes:
                sections["ROI_12M"] = expected_roi
                result.add_issue(
                    "ROI_AUTO_CORRECTED",
                    "auto_fixed",
                    f"ROI corrected from {roi}% to {expected_roi}%",
                    field="ROI_12M",
                    original=roi,
                    fixed=expected_roi,
                )

    def _validate_payback(
        self,
        result: ReconcileResult,
        sections: Dict[str, Any],
        payback: Optional[float],
        apply_fixes: bool,
    ) -> None:
        """Validate payback period is valid."""
        if payback is None:
            return

        if payback < 0:
            result.add_issue(
                "NEGATIVE_PAYBACK",
                "error",
                f"Payback period cannot be negative: {payback}",
                field="PAYBACK_MONTHS",
                original=payback,
            )

            if apply_fixes:
                # Set to None if negative (indicates invalid calculation)
                sections["PAYBACK_MONTHS"] = None
                result.add_issue(
                    "PAYBACK_NULLIFIED",
                    "auto_fixed",
                    "Negative payback set to None",
                    field="PAYBACK_MONTHS",
                    original=payback,
                    fixed=None,
                )

        # Sanity check: payback > 120 months (10 years) is unusual
        if payback is not None and payback > 120:
            result.add_issue(
                "UNUSUALLY_LONG_PAYBACK",
                "warning",
                f"Payback period unusually long: {payback} months",
                field="PAYBACK_MONTHS",
            )

    def _validate_ai_act_modifiers(
        self,
        result: ReconcileResult,
        sections: Dict[str, Any],
        ai_act_applied: bool,
        capex_factor: float,
        opex_factor: float,
        original_capex: Optional[float],
        original_opex: Optional[float],
    ) -> None:
        """Validate AI Act modifier documentation."""
        if not ai_act_applied:
            return

        # Check that modifiers are documented
        if capex_factor != 1.0 and original_capex is None:
            result.add_issue(
                "MISSING_ORIGINAL_CAPEX",
                "warning",
                "CAPEX modifier applied but original value not documented",
                field="AI_ACT_BC_ORIGINAL_CAPEX",
            )

        if opex_factor != 1.0 and original_opex is None:
            result.add_issue(
                "MISSING_ORIGINAL_OPEX",
                "warning",
                "OPEX modifier applied but original value not documented",
                field="AI_ACT_BC_ORIGINAL_OPEX",
            )

        # Check that factors are within reasonable range (0.8 to 2.0)
        if not (0.8 <= capex_factor <= 2.0):
            result.add_issue(
                "UNUSUAL_CAPEX_FACTOR",
                "warning",
                f"CAPEX factor outside normal range: {capex_factor}",
                field="AI_ACT_BC_CAPEX_FACTOR",
            )

        if not (0.8 <= opex_factor <= 2.0):
            result.add_issue(
                "UNUSUAL_OPEX_FACTOR",
                "warning",
                f"OPEX factor outside normal range: {opex_factor}",
                field="AI_ACT_BC_OPEX_FACTOR",
            )

    def _apply_rounding(
        self,
        result: ReconcileResult,
        sections: Dict[str, Any],
        apply_fixes: bool,
    ) -> None:
        """Apply consistent rounding to monetary values."""
        monetary_fields = [
            "CAPEX_REALISTISCH_EUR",
            "OPEX_REALISTISCH_EUR",
            "EINSPARUNG_MONAT_EUR",
            "AI_ACT_BC_ORIGINAL_CAPEX",
            "AI_ACT_BC_ORIGINAL_OPEX",
        ]

        percentage_fields = [
            "ROI_12M",
        ]

        for field in monetary_fields:
            value = sections.get(field)
            if value is not None:
                try:
                    float_val = float(value)
                    # Round monetary values to whole euros
                    rounded = round(float_val, 0)
                    if float_val != rounded and apply_fixes:
                        sections[field] = int(rounded)
                        result.add_issue(
                            "ROUNDING_APPLIED",
                            "auto_fixed",
                            f"{field} rounded to whole euros",
                            field=field,
                            original=float_val,
                            fixed=int(rounded),
                        )
                except (ValueError, TypeError):
                    pass

        for field in percentage_fields:
            value = sections.get(field)
            if value is not None:
                try:
                    float_val = float(value)
                    rounded = round(float_val, self.rounding_decimals)
                    if float_val != rounded and apply_fixes:
                        sections[field] = rounded
                        result.add_issue(
                            "ROUNDING_APPLIED",
                            "auto_fixed",
                            f"{field} rounded to {self.rounding_decimals} decimals",
                            field=field,
                            original=float_val,
                            fixed=rounded,
                        )
                except (ValueError, TypeError):
                    pass

    def _validate_savings_coverage(
        self,
        result: ReconcileResult,
        einsparung: float,
        opex: float,
    ) -> None:
        """Validate monthly savings cover monthly OPEX."""
        if opex > 0 and einsparung < opex:
            result.add_issue(
                "SAVINGS_BELOW_OPEX",
                "warning",
                f"Monthly savings ({einsparung}€) are less than monthly OPEX ({opex}€)",
                field="EINSPARUNG_MONAT_EUR",
            )


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_reconciler_instance: Optional[BusinessCaseReconciler] = None


def get_bc_reconciler() -> BusinessCaseReconciler:
    """Get singleton reconciler instance."""
    global _reconciler_instance
    if _reconciler_instance is None:
        _reconciler_instance = BusinessCaseReconciler()
    return _reconciler_instance


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def reconcile_business_case(
    sections: Dict[str, Any],
    apply_fixes: bool = True,
) -> ReconcileResult:
    """
    Convenience function to reconcile business case data.

    Args:
        sections: Report sections dict
        apply_fixes: Whether to apply automatic fixes

    Returns:
        ReconcileResult
    """
    return get_bc_reconciler().reconcile(sections, apply_fixes)


def validate_bc_consistency(sections: Dict[str, Any]) -> bool:
    """
    Quick check if business case is consistent.

    Returns True if valid, False if critical issues found.
    """
    result = reconcile_business_case(sections, apply_fixes=False)
    return result.success


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G12] BC Reconciler loaded - enabled=%s rounding=%d fail_on_error=%s",
    BC_RECONCILE_ENABLED,
    BC_ROUNDING_DECIMALS,
    BC_FAIL_ON_INCONSISTENCY,
)
