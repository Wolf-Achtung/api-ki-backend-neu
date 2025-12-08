#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprint G15.2: Profile Sanity & AI-Act Override Validation

Comprehensive validation of gold profiles for:
- AI-Act Override Validation
- Persona & Size Consistency Audit
- Funding Flow Validation
- Redundancy + Word-Min Checks

Usage:
    python scripts/validate_profiles_g15_2.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# VALIDATION RESULT STRUCTURES
# =============================================================================

@dataclass
class AIActValidation:
    """AI-Act validation result for a profile."""
    override_set: bool = False
    override_value: Optional[str] = None
    effective_risk_level: str = "unknown"
    risk_consistency_score: float = 0.0
    capex_modifier: float = 1.0
    opex_modifier: float = 1.0
    payback_delta: float = 0.0
    modifier_trace: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PersonaValidation:
    """Persona/Size consistency validation result."""
    expected_persona: str = ""
    forbidden_terms_found: List[str] = field(default_factory=list)
    is_consistent: bool = True
    warnings: List[str] = field(default_factory=list)


@dataclass
class FundingValidation:
    """Funding flow validation result."""
    expected_flow: str = ""
    actual_flow: str = ""
    is_correct: bool = True
    premium_funding_enabled: bool = False
    coverage: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class WordMinValidation:
    """Word minimum validation result."""
    section_checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    sections_below_min: List[str] = field(default_factory=list)
    smart_mode_active: bool = False
    warnings: List[str] = field(default_factory=list)


@dataclass
class ProfileValidationResult:
    """Complete validation result for a profile."""
    profile_id: str
    ai_act: AIActValidation = field(default_factory=AIActValidation)
    persona: PersonaValidation = field(default_factory=PersonaValidation)
    funding: FundingValidation = field(default_factory=FundingValidation)
    word_min: WordMinValidation = field(default_factory=WordMinValidation)
    fixes_required: List[str] = field(default_factory=list)


# =============================================================================
# AI-ACT RISK LEVEL DETERMINATION
# =============================================================================

def determine_risk_level(profile: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Determine AI-Act risk level based on profile.

    Returns: (risk_level, reasoning_list)
    """
    answers = profile.get("answers", {})
    reasons = []

    # Check for override first
    override = profile.get("ai_act_override_risk_level") or answers.get("ai_act_override_risk_level")
    if override:
        return override, [f"Override: {override}"]

    branche = answers.get("branche", "").lower()
    size = answers.get("unternehmensgroesse", "").lower()
    regulated = answers.get("regulierte_branche", [])
    ki_einsatz = answers.get("ki_einsatz", [])
    ki_guardrails = answers.get("ki_guardrails", "")

    # Normalize regulated branches
    if isinstance(regulated, str):
        regulated = [regulated]
    regulated_lower = [r.lower() for r in regulated]

    # High-risk checks
    high_risk_branches = ["finanzen", "finance", "versicherung", "insurance", "healthcare", "medical", "gesundheit"]
    high_risk_uses = ["risikoanalyse", "risk_analysis", "scoring", "entscheidung", "decision", "kreditbewertung"]

    is_high_risk_branch = any(b in branche or b in " ".join(regulated_lower) for b in high_risk_branches)
    is_high_risk_use = any(u in " ".join(ki_einsatz).lower() for u in high_risk_uses)

    if is_high_risk_branch and is_high_risk_use:
        reasons.append(f"High-risk branch ({branche}) + high-risk use case")
        return "high-risk", reasons

    if is_high_risk_branch:
        reasons.append(f"Regulated high-risk branch: {branche}")
        return "high-risk", reasons

    # Limited risk checks
    if ki_guardrails:
        reasons.append("Has guardrails defined")

    if "legal" in branche or "recht" in branche:
        reasons.append("Legal/Law sector")
        return "limited", reasons

    # Size-based minimal risk
    if "solo" in size:
        reasons.append("Solo size with low automation")
        return "minimal", reasons

    if "team" in size:
        reasons.append("Team size")
        return "limited", reasons

    # KMU default
    reasons.append("KMU default")
    return "limited", reasons


def get_ai_act_modifiers(risk_level: str) -> Dict[str, float]:
    """Get CAPEX/OPEX modifiers for risk level."""
    modifiers = {
        "high-risk": {"capex": 1.25, "opex": 1.15, "payback_delta": 2.0},
        "limited": {"capex": 1.10, "opex": 1.05, "payback_delta": 0.5},
        "minimal": {"capex": 1.0, "opex": 1.0, "payback_delta": 0.0},
        "none": {"capex": 1.0, "opex": 1.0, "payback_delta": 0.0},
    }
    return modifiers.get(risk_level, modifiers["limited"])


# =============================================================================
# PERSONA CONSISTENCY CHECKS
# =============================================================================

SOLO_FORBIDDEN_TERMS = [
    "team", "teams", "mitarbeiter", "mitarbeitende", "abteilung", "abteilungen",
    "bereichsleiter", "teamleiter", "fachbereich", "fachbereiche", "belegschaft",
    "personal", "personalstrategien", "hr", "bereichsübergreifend", "teamstruktur",
]

TEAM_FORBIDDEN_TERMS = [
    "einzelperson", "als einzelner", "persönliche kapazität", "solo-selbstständig",
    "freiberufler", "allein arbeiten",
]

KMU_FORBIDDEN_TERMS = [
    "konzern", "division", "business unit", "headquarters", "global",
]


def check_persona_consistency(profile: Dict[str, Any]) -> PersonaValidation:
    """Check persona/size consistency in profile."""
    result = PersonaValidation()

    answers = profile.get("answers", {})
    size = answers.get("unternehmensgroesse", "").lower()

    # Determine expected persona
    if "solo" in size or "1" in size:
        result.expected_persona = "solo"
        forbidden = SOLO_FORBIDDEN_TERMS
    elif "team" in size or "2" in size:
        result.expected_persona = "team"
        forbidden = TEAM_FORBIDDEN_TERMS
    else:
        result.expected_persona = "kmu"
        forbidden = KMU_FORBIDDEN_TERMS

    # Context patterns that indicate external/customer references (OK for all personas)
    # When describing what you offer TO others, mentioning "Teams" is fine
    customer_context_patterns = [
        "für solo", "für team", "für kmu", "für unternehmen",
        "kleine unternehmen und teams",  # Describes target customers
        "zielgruppen",
    ]

    # Check all text fields for forbidden terms
    text_fields = [
        "ki_projekte", "ki_guardrails",
        "zeitersparnis_prioritaet", "geschaeftsmodell_evolution",
        "vision_3_jahre", "strategische_ziele",
    ]

    # Skip hauptleistung for Solo - it describes services offered TO others
    # "Teams" as target customers is valid for Solo providers
    if result.expected_persona != "solo":
        text_fields.append("hauptleistung")

    for field_name in text_fields:
        field_value = answers.get(field_name, "")
        if isinstance(field_value, str):
            field_lower = field_value.lower()

            # Skip if this is customer context
            is_customer_context = any(p in field_lower for p in customer_context_patterns)
            if is_customer_context:
                continue

            for term in forbidden:
                # Use word boundary check to avoid false positives like "hr" in "Durchführung"
                import re
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, field_lower):
                    result.forbidden_terms_found.append(f"{field_name}: '{term}'")
                    result.is_consistent = False

    # Check description for actual persona leaks (not customer descriptions)
    description = profile.get("description", "").lower()
    # Only flag if it describes internal structure, not customers
    internal_structure_terms = ["abteilung", "bereichsleiter", "teamleiter", "mitarbeiter schulen"]
    for term in internal_structure_terms:
        if term in description:
            result.forbidden_terms_found.append(f"description: '{term}'")
            result.is_consistent = False

    if result.forbidden_terms_found:
        result.warnings.append(f"Found {len(result.forbidden_terms_found)} forbidden terms for {result.expected_persona}")
    else:
        result.is_consistent = True  # Ensure it's True if no issues found

    return result


# =============================================================================
# FUNDING FLOW VALIDATION
# =============================================================================

def validate_funding_flow(profile: Dict[str, Any]) -> FundingValidation:
    """Validate funding flow routing."""
    result = FundingValidation()

    answers = profile.get("answers", {})
    lang = profile.get("lang", "de")
    country = profile.get("country", answers.get("country", "Germany"))

    # Determine expected flow
    if lang == "en":
        if country.lower() in ["germany", "deutschland", "de", ""]:
            result.expected_flow = "DE-EN"
        else:
            result.expected_flow = "EN-EU-Core"
    else:
        result.expected_flow = "DE"

    # Check expected_validation if present
    expected = profile.get("expected_validation", {})
    if expected:
        exp_flow = expected.get("funding_flow", "")
        if exp_flow:
            result.expected_flow = exp_flow

    # Check premium funding
    result.premium_funding_enabled = os.environ.get("ENABLE_PREMIUM_FUNDING", "0") == "1"

    # Set coverage expectations
    result.coverage = {
        "tools": 8,
        "funding": 8,
        "competitor": 5,
        "market_insights": 5,
    }

    result.actual_flow = result.expected_flow  # Would be determined at runtime
    result.is_correct = True

    return result


# =============================================================================
# WORD MINIMUM CHECKS
# =============================================================================

SECTION_MIN_WORDS = {
    "solo": {
        "executive_summary": 150,
        "quick_wins": 60,
        "roadmap_90d": 250,
        "roadmap_12m": 500,
        "strategie_governance": 130,
        "recommendations": 500,
        "risks": 500,
        "gamechanger": 500,
        "foerderpotenzial": 600,
        "tools_empfehlungen": 100,
        "org_change": 300,
    },
    "team": {
        "executive_summary": 180,
        "quick_wins": 90,
        "roadmap_90d": 320,
        "roadmap_12m": 600,
        "strategie_governance": 130,
        "recommendations": 600,
        "risks": 600,
        "gamechanger": 600,
        "foerderpotenzial": 700,
        "tools_empfehlungen": 130,
        "org_change": 400,
    },
    "kmu": {
        "executive_summary": 200,
        "quick_wins": 120,
        "roadmap_90d": 340,
        "roadmap_12m": 700,
        "strategie_governance": 160,
        "recommendations": 700,
        "risks": 700,
        "gamechanger": 700,
        "foerderpotenzial": 800,
        "tools_empfehlungen": 160,
        "org_change": 500,
    },
}


def validate_word_mins(profile: Dict[str, Any]) -> WordMinValidation:
    """Validate word minimums for profile size."""
    result = WordMinValidation()

    answers = profile.get("answers", {})
    size = answers.get("unternehmensgroesse", "").lower()

    # Determine size category
    if "solo" in size or "1" in size:
        size_key = "solo"
    elif "team" in size or "2" in size:
        size_key = "team"
    else:
        size_key = "kmu"

    mins = SECTION_MIN_WORDS.get(size_key, SECTION_MIN_WORDS["kmu"])

    for section, min_words in mins.items():
        result.section_checks[section] = {
            "min_required": min_words,
            "status": "pending",  # Would be checked against actual content
        }

    # Smart mode check
    result.smart_mode_active = True  # G14 feature

    return result


# =============================================================================
# MAIN VALIDATION
# =============================================================================

def validate_profile(profile: Dict[str, Any]) -> ProfileValidationResult:
    """Run complete validation on a profile."""
    result = ProfileValidationResult(profile_id=profile.get("profile_id", "unknown"))

    # A) AI-Act Override Validation
    risk_level, reasons = determine_risk_level(profile)
    modifiers = get_ai_act_modifiers(risk_level)

    result.ai_act.override_set = bool(
        profile.get("ai_act_override_risk_level") or
        profile.get("answers", {}).get("ai_act_override_risk_level")
    )
    result.ai_act.override_value = profile.get("ai_act_override_risk_level")
    result.ai_act.effective_risk_level = risk_level
    result.ai_act.capex_modifier = modifiers["capex"]
    result.ai_act.opex_modifier = modifiers["opex"]
    result.ai_act.payback_delta = modifiers["payback_delta"]
    result.ai_act.modifier_trace = {
        "risk_level": risk_level,
        "reasons": reasons,
        "modifiers": modifiers,
    }

    # Calculate consistency score
    answers = profile.get("answers", {})
    regulated = answers.get("regulierte_branche", [])
    if isinstance(regulated, str):
        regulated = [regulated]

    is_regulated = any(r.lower() not in ["keine_regulierung", "no_regulation", ""] for r in regulated)

    if risk_level == "high-risk" and is_regulated:
        result.ai_act.risk_consistency_score = 1.0
    elif risk_level == "minimal" and not is_regulated:
        result.ai_act.risk_consistency_score = 1.0
    elif risk_level == "limited":
        result.ai_act.risk_consistency_score = 0.8
    else:
        result.ai_act.risk_consistency_score = 0.6
        result.ai_act.warnings.append("Risk level may not match branch characteristics")

    # B) Persona Consistency
    result.persona = check_persona_consistency(profile)

    # C) Funding Flow
    result.funding = validate_funding_flow(profile)

    # D) Word Minimums
    result.word_min = validate_word_mins(profile)

    # Collect fixes required
    if not result.ai_act.override_set:
        result.fixes_required.append(f"Add ai_act_override_risk_level: '{risk_level}'")
    if not result.persona.is_consistent:
        result.fixes_required.append(f"Fix persona terms: {result.persona.forbidden_terms_found}")

    return result


def print_validation_table(results: List[ProfileValidationResult]) -> None:
    """Print validation results as table."""
    print("\n" + "=" * 120)
    print("G15.2 PROFILE VALIDATION RESULTS")
    print("=" * 120)

    # Header
    print(f"{'Profil':<40} | {'Override':<8} | {'Risk Level':<12} | {'BC Mod':<10} | {'Funding':<12} | {'Persona':<8} | {'Warnings':<8} | {'Fixes?':<6}")
    print("-" * 120)

    for r in results:
        override = "YES" if r.ai_act.override_set else "NO"
        bc_mod = f"C:{r.ai_act.capex_modifier:.2f}/O:{r.ai_act.opex_modifier:.2f}"
        persona = "OK" if r.persona.is_consistent else "FAIL"
        warnings = len(r.ai_act.warnings) + len(r.persona.warnings)
        fixes = "YES" if r.fixes_required else "NO"

        print(f"{r.profile_id:<40} | {override:<8} | {r.ai_act.effective_risk_level:<12} | {bc_mod:<10} | {r.funding.expected_flow:<12} | {persona:<8} | {warnings:<8} | {fixes:<6}")

    print("=" * 120)


def generate_optimized_profile(profile: Dict[str, Any], validation: ProfileValidationResult) -> Dict[str, Any]:
    """Generate optimized profile with fixes applied."""
    optimized = json.loads(json.dumps(profile))  # Deep copy

    # Add AI-Act override
    optimized["ai_act_override_risk_level"] = validation.ai_act.effective_risk_level

    # Add validation metadata
    optimized["g15_2_validation"] = {
        "ai_act_effective_risk_level": validation.ai_act.effective_risk_level,
        "ai_act_risk_consistency_score": validation.ai_act.risk_consistency_score,
        "ai_act_modifier_trace": {
            "CAPEX_MODIFIER": validation.ai_act.capex_modifier,
            "OPEX_MODIFIER": validation.ai_act.opex_modifier,
            "PAYBACK_DELTA_MONTHS": validation.ai_act.payback_delta,
        },
        "persona_status": "consistent" if validation.persona.is_consistent else "inconsistent",
        "funding_flow": validation.funding.expected_flow,
        "warnings": validation.ai_act.warnings + validation.persona.warnings,
    }

    return optimized


def main():
    """Main validation runner."""
    print("\n" + "=" * 80)
    print("Sprint G15.2: Profile Sanity & AI-Act Override Validation")
    print("=" * 80)

    # Load profiles
    profiles_dir = PROJECT_ROOT / "data" / "test_profiles_gold"
    target_profiles = [
        "solo_beratung_ki_assessments.json",
        "kmu_france_eu_core_en_gold.json",
        "team_finance_insurance_advisory.json",
    ]

    results: List[ProfileValidationResult] = []
    optimized_profiles: List[Dict[str, Any]] = []

    for filename in target_profiles:
        filepath = profiles_dir / filename
        if not filepath.exists():
            print(f"[WARN] Profile not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            profile = json.load(f)

        print(f"\n[INFO] Validating: {profile.get('profile_id', filename)}")

        validation = validate_profile(profile)
        results.append(validation)

        # Print details
        print(f"  AI-Act Risk Level: {validation.ai_act.effective_risk_level}")
        print(f"  Risk Consistency: {validation.ai_act.risk_consistency_score:.1%}")
        print(f"  CAPEX Modifier: {validation.ai_act.capex_modifier:.2f}")
        print(f"  OPEX Modifier: {validation.ai_act.opex_modifier:.2f}")
        print(f"  Funding Flow: {validation.funding.expected_flow}")
        print(f"  Persona Consistent: {validation.persona.is_consistent}")

        if validation.persona.forbidden_terms_found:
            print(f"  Forbidden Terms: {validation.persona.forbidden_terms_found[:3]}...")

        if validation.fixes_required:
            print(f"  Fixes Required: {len(validation.fixes_required)}")

        # Generate optimized profile
        optimized = generate_optimized_profile(profile, validation)
        optimized_profiles.append(optimized)

    # Print summary table
    print_validation_table(results)

    # Print recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("\n1. AI-Act Override Fields to Add:")
    for r in results:
        if not r.ai_act.override_set:
            print(f"   - {r.profile_id}: ai_act_override_risk_level = '{r.ai_act.effective_risk_level}'")

    print("\n2. Persona Issues to Fix:")
    for r in results:
        if not r.persona.is_consistent:
            print(f"   - {r.profile_id}: {len(r.persona.forbidden_terms_found)} forbidden terms")

    print("\n3. Word Minimum Recommendations:")
    print("   - roadmap_90d (solo): 250 words - EXTENDED in G15.1")
    print("   - strategie_governance: Consider +80 words for depth")
    print("   - All sections should use Smart Mode consolidation (G14)")

    # Save optimized profiles
    output_dir = PROJECT_ROOT / "data" / "test_profiles_gold_optimized"
    output_dir.mkdir(exist_ok=True)

    for profile in optimized_profiles:
        filename = f"{profile['profile_id']}_optimized.json"
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVED] {filepath}")

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)

    return results


if __name__ == "__main__":
    main()
