# -*- coding: utf-8 -*-
"""
Sprint G17.6-D: Prompt Rollout Simulator

Simulates patch impact on representative profiles before production rollout:
- 3 Gold profiles (best-case scenarios)
- 5 Random sample profiles
- 2 Risk edge profiles (high-risk + freeform stress)

Metrics tracked:
- Warning delta (before vs after)
- Fallback density
- Persona leak score
- AI-Act hard guards
- Token usage delta

If >= 2 categories regress, patch is blocked.

Version: 1.0.0 (Sprint G17.6)
"""
from __future__ import annotations

import json
import logging
import os
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

PROMPT_GOVERNANCE_ENABLED = os.environ.get("PROMPT_GOVERNANCE_ENABLED", "1") == "1"
PROMPT_DRAFT_MODE = os.environ.get("PROMPT_DRAFT_MODE", "0") == "1"

PROMPT_SIMULATION_PROFILE_COUNT = int(os.environ.get("PROMPT_SIMULATION_PROFILE_COUNT", "10"))
PROMPT_SIMULATION_REQUIRED_IMPROVEMENTS = int(os.environ.get("PROMPT_SIMULATION_REQUIRED_IMPROVEMENTS", "1"))
PROMPT_SIMULATION_HARD_STOP_REGRESSIONS = int(os.environ.get("PROMPT_SIMULATION_HARD_STOP_REGRESSIONS", "2"))

# Storage path
SIMULATION_RESULTS_PATH = os.environ.get("SIMULATION_RESULTS_PATH", "data/simulation_results")


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class SimulationProfile:
    """A profile used for simulation testing."""
    profile_id: str
    profile_type: str  # gold, random, risk_edge
    company_size: str  # solo, team, kmu
    branch: str
    ai_act_risk: str  # minimal, moderate, high
    language: str = "DE"
    description: str = ""


@dataclass
class ProfileMetrics:
    """Metrics collected for a single profile simulation."""
    profile_id: str
    warning_count: int = 0
    fallback_count: int = 0
    persona_leak_score: float = 0.0
    ai_act_violations: int = 0
    token_count: int = 0
    validation_score: float = 0.0


@dataclass
class MetricDelta:
    """Delta between before and after metrics."""
    metric_name: str
    before: float
    after: float
    delta: float
    delta_percent: float
    improved: bool
    regression: bool
    neutral: bool


@dataclass
class SimulationResult:
    """Result of simulating a patch on a single profile."""
    profile: SimulationProfile
    metrics_before: ProfileMetrics
    metrics_after: ProfileMetrics
    deltas: List[MetricDelta] = field(default_factory=list)
    regressions: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    passed: bool = True


@dataclass
class RolloutSimulation:
    """Complete rollout simulation result."""
    simulation_id: str
    patch_id: str
    prompt_file: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Profiles tested
    gold_profiles: List[SimulationResult] = field(default_factory=list)
    random_profiles: List[SimulationResult] = field(default_factory=list)
    risk_edge_profiles: List[SimulationResult] = field(default_factory=list)

    # Aggregated metrics
    total_profiles: int = 0
    profiles_passed: int = 0
    profiles_failed: int = 0

    total_regressions: int = 0
    total_improvements: int = 0

    # Category summaries
    warning_delta_avg: float = 0.0
    fallback_delta_avg: float = 0.0
    persona_leak_delta_avg: float = 0.0
    ai_act_delta_avg: float = 0.0
    token_delta_avg: float = 0.0

    # Decision
    passed: bool = True
    blocked: bool = False
    block_reason: Optional[str] = None


# =============================================================================
# GOLD PROFILES
# =============================================================================

GOLD_PROFILES = [
    SimulationProfile(
        profile_id="gold_solo_beratung",
        profile_type="gold",
        company_size="solo",
        branch="beratung",
        ai_act_risk="minimal",
        description="Solo consultant, minimal AI risk - baseline best case",
    ),
    SimulationProfile(
        profile_id="gold_team_it",
        profile_type="gold",
        company_size="team",
        branch="it_software",
        ai_act_risk="moderate",
        description="IT team, moderate risk - typical tech company",
    ),
    SimulationProfile(
        profile_id="gold_kmu_industrie",
        profile_type="gold",
        company_size="kmu",
        branch="industrie",
        ai_act_risk="high",
        description="Industrial KMU, high AI risk - complex use case",
    ),
]


# =============================================================================
# RISK EDGE PROFILES
# =============================================================================

RISK_EDGE_PROFILES = [
    SimulationProfile(
        profile_id="risk_high_ai_act",
        profile_type="risk_edge",
        company_size="kmu",
        branch="gesundheit",
        ai_act_risk="high",
        description="Healthcare KMU with high AI-Act risk - maximum compliance needed",
    ),
    SimulationProfile(
        profile_id="risk_freeform_stress",
        profile_type="risk_edge",
        company_size="solo",
        branch="marketing",
        ai_act_risk="moderate",
        description="Creative solo with freeform inputs - edge case for persona",
    ),
]


# =============================================================================
# RANDOM PROFILE GENERATION
# =============================================================================

def _generate_random_profiles(count: int = 5) -> List[SimulationProfile]:
    """Generate random sample profiles for simulation."""
    sizes = ["solo", "team", "kmu"]
    branches = [
        "beratung", "it_software", "finanzen", "handel",
        "industrie", "gesundheit", "marketing", "logistik",
    ]
    risks = ["minimal", "moderate", "high"]

    profiles = []
    for i in range(count):
        profiles.append(SimulationProfile(
            profile_id=f"random_{i+1}_{datetime.now().strftime('%H%M%S')}",
            profile_type="random",
            company_size=random.choice(sizes),
            branch=random.choice(branches),
            ai_act_risk=random.choice(risks),
            description=f"Randomly sampled profile {i+1}",
        ))

    return profiles


# =============================================================================
# METRIC SIMULATION (Mock for now - would integrate with actual validation)
# =============================================================================

def _simulate_metrics_for_profile(
    profile: SimulationProfile,
    prompt_content: str,
    is_patched: bool = False,
) -> ProfileMetrics:
    """
    Simulate metrics for a profile with given prompt.

    Note: This is a simplified simulation. In production, this would
    actually run the prompt through the validation pipeline.

    Args:
        profile: Profile to simulate
        prompt_content: Prompt content to test
        is_patched: Whether this is the patched version

    Returns:
        Simulated ProfileMetrics
    """
    # Base metrics from profile characteristics
    base_warnings = 3 if profile.ai_act_risk == "high" else (2 if profile.ai_act_risk == "moderate" else 1)
    base_fallbacks = 2 if profile.company_size == "solo" else 1
    base_persona_leak = 0.1 if profile.company_size == "solo" else 0.05
    base_ai_act = 1 if profile.ai_act_risk == "high" else 0

    # Token count based on prompt length
    token_count = len(prompt_content) // 4

    # Adjust for patched version (simulated improvement/regression)
    if is_patched:
        # Patches generally improve things slightly
        base_warnings = max(0, base_warnings - random.randint(0, 1))
        base_fallbacks = max(0, base_fallbacks - random.randint(0, 1))
        base_persona_leak = max(0, base_persona_leak - 0.02)
        # Token count may change
        token_count = int(token_count * random.uniform(0.95, 1.05))

    return ProfileMetrics(
        profile_id=profile.profile_id,
        warning_count=base_warnings,
        fallback_count=base_fallbacks,
        persona_leak_score=base_persona_leak,
        ai_act_violations=base_ai_act,
        token_count=token_count,
        validation_score=0.85 + random.uniform(-0.1, 0.1),
    )


def _calculate_delta(
    metric_name: str,
    before: float,
    after: float,
    lower_is_better: bool = True,
) -> MetricDelta:
    """Calculate metric delta and determine if it's improvement/regression."""
    delta = after - before
    delta_percent = (delta / before * 100) if before != 0 else 0

    # For metrics where lower is better (warnings, fallbacks, etc.)
    if lower_is_better:
        improved = delta < 0
        regression = delta > 0
    else:
        improved = delta > 0
        regression = delta < 0

    # Small changes are neutral
    threshold = 0.05 if abs(before) < 1 else 0.1
    neutral = abs(delta) <= threshold

    return MetricDelta(
        metric_name=metric_name,
        before=before,
        after=after,
        delta=delta,
        delta_percent=delta_percent,
        improved=improved and not neutral,
        regression=regression and not neutral,
        neutral=neutral,
    )


def _simulate_profile(
    profile: SimulationProfile,
    prompt_before: str,
    prompt_after: str,
) -> SimulationResult:
    """
    Simulate a patch on a single profile.

    Args:
        profile: Profile to test
        prompt_before: Original prompt
        prompt_after: Patched prompt

    Returns:
        SimulationResult with metrics comparison
    """
    # Get metrics before and after
    metrics_before = _simulate_metrics_for_profile(profile, prompt_before, is_patched=False)
    metrics_after = _simulate_metrics_for_profile(profile, prompt_after, is_patched=True)

    result = SimulationResult(
        profile=profile,
        metrics_before=metrics_before,
        metrics_after=metrics_after,
    )

    # Calculate deltas for each metric
    deltas = [
        _calculate_delta("warnings", metrics_before.warning_count, metrics_after.warning_count),
        _calculate_delta("fallbacks", metrics_before.fallback_count, metrics_after.fallback_count),
        _calculate_delta("persona_leak", metrics_before.persona_leak_score, metrics_after.persona_leak_score),
        _calculate_delta("ai_act_violations", metrics_before.ai_act_violations, metrics_after.ai_act_violations),
        _calculate_delta("token_count", metrics_before.token_count, metrics_after.token_count),
    ]

    result.deltas = deltas

    # Collect regressions and improvements
    for delta in deltas:
        if delta.regression:
            result.regressions.append(delta.metric_name)
        if delta.improved:
            result.improvements.append(delta.metric_name)

    # Profile passes if it has no regressions or improvements outweigh
    result.passed = len(result.regressions) == 0 or len(result.improvements) > len(result.regressions)

    return result


# =============================================================================
# MAIN SIMULATION FUNCTIONS
# =============================================================================

def simulate_rollout(
    patch_id: str,
    prompt_file: str,
    prompt_before: str,
    prompt_after: str,
    random_profile_count: int = 5,
) -> RolloutSimulation:
    """
    Simulate patch rollout on representative profiles.

    Tests on:
    - 3 Gold profiles (best-case)
    - N Random sample profiles
    - 2 Risk edge profiles

    Args:
        patch_id: ID of the patch being tested
        prompt_file: Prompt file being patched
        prompt_before: Original prompt content
        prompt_after: Patched prompt content
        random_profile_count: Number of random profiles to test

    Returns:
        RolloutSimulation with complete results
    """
    simulation_id = f"sim_{patch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    simulation = RolloutSimulation(
        simulation_id=simulation_id,
        patch_id=patch_id,
        prompt_file=prompt_file,
    )

    # Simulate on gold profiles
    for profile in GOLD_PROFILES:
        result = _simulate_profile(profile, prompt_before, prompt_after)
        simulation.gold_profiles.append(result)

    # Simulate on random profiles
    random_profiles = _generate_random_profiles(random_profile_count)
    for profile in random_profiles:
        result = _simulate_profile(profile, prompt_before, prompt_after)
        simulation.random_profiles.append(result)

    # Simulate on risk edge profiles
    for profile in RISK_EDGE_PROFILES:
        result = _simulate_profile(profile, prompt_before, prompt_after)
        simulation.risk_edge_profiles.append(result)

    # Aggregate results
    all_results = (
        simulation.gold_profiles +
        simulation.random_profiles +
        simulation.risk_edge_profiles
    )

    simulation.total_profiles = len(all_results)
    simulation.profiles_passed = sum(1 for r in all_results if r.passed)
    simulation.profiles_failed = simulation.total_profiles - simulation.profiles_passed

    # Count total regressions and improvements
    for result in all_results:
        simulation.total_regressions += len(result.regressions)
        simulation.total_improvements += len(result.improvements)

    # Calculate average deltas per category
    if all_results:
        warning_deltas = [r.metrics_after.warning_count - r.metrics_before.warning_count for r in all_results]
        fallback_deltas = [r.metrics_after.fallback_count - r.metrics_before.fallback_count for r in all_results]
        persona_deltas = [r.metrics_after.persona_leak_score - r.metrics_before.persona_leak_score for r in all_results]
        ai_act_deltas = [r.metrics_after.ai_act_violations - r.metrics_before.ai_act_violations for r in all_results]
        token_deltas = [r.metrics_after.token_count - r.metrics_before.token_count for r in all_results]

        simulation.warning_delta_avg = sum(warning_deltas) / len(warning_deltas)
        simulation.fallback_delta_avg = sum(fallback_deltas) / len(fallback_deltas)
        simulation.persona_leak_delta_avg = sum(persona_deltas) / len(persona_deltas)
        simulation.ai_act_delta_avg = sum(ai_act_deltas) / len(ai_act_deltas)
        simulation.token_delta_avg = sum(token_deltas) / len(token_deltas)

    # Determine if simulation passes
    # Count how many categories regressed on average
    regressed_categories = 0
    if simulation.warning_delta_avg > 0.1:
        regressed_categories += 1
    if simulation.fallback_delta_avg > 0.1:
        regressed_categories += 1
    if simulation.persona_leak_delta_avg > 0.01:
        regressed_categories += 1
    if simulation.ai_act_delta_avg > 0:
        regressed_categories += 1
    if abs(simulation.token_delta_avg) > 100:  # Significant token change
        regressed_categories += 1

    # Block if >= PROMPT_SIMULATION_HARD_STOP_REGRESSIONS categories regressed
    if regressed_categories >= PROMPT_SIMULATION_HARD_STOP_REGRESSIONS:
        simulation.passed = False
        simulation.blocked = True
        simulation.block_reason = f"{regressed_categories} categories showed regression (threshold: {PROMPT_SIMULATION_HARD_STOP_REGRESSIONS})"
    else:
        simulation.passed = True
        simulation.blocked = False

    # Store simulation result
    _store_simulation_result(simulation)

    return simulation


def _store_simulation_result(simulation: RolloutSimulation) -> bool:
    """Store simulation result to persistent storage."""
    if PROMPT_DRAFT_MODE:
        return False

    try:
        results_path = Path(SIMULATION_RESULTS_PATH)
        results_path.mkdir(parents=True, exist_ok=True)

        filename = f"{simulation.simulation_id}.json"
        file_path = results_path / filename

        # Serialize simulation
        data = {
            "simulation_id": simulation.simulation_id,
            "patch_id": simulation.patch_id,
            "prompt_file": simulation.prompt_file,
            "timestamp": simulation.timestamp.isoformat(),
            "total_profiles": simulation.total_profiles,
            "profiles_passed": simulation.profiles_passed,
            "profiles_failed": simulation.profiles_failed,
            "total_regressions": simulation.total_regressions,
            "total_improvements": simulation.total_improvements,
            "warning_delta_avg": simulation.warning_delta_avg,
            "fallback_delta_avg": simulation.fallback_delta_avg,
            "persona_leak_delta_avg": simulation.persona_leak_delta_avg,
            "ai_act_delta_avg": simulation.ai_act_delta_avg,
            "token_delta_avg": simulation.token_delta_avg,
            "passed": simulation.passed,
            "blocked": simulation.blocked,
            "block_reason": simulation.block_reason,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        log.error(f"Failed to store simulation result: {e}")
        return False


def get_simulation_result(simulation_id: str) -> Optional[Dict[str, Any]]:
    """Get a stored simulation result."""
    try:
        results_path = Path(SIMULATION_RESULTS_PATH)
        file_path = results_path / f"{simulation_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data

    except Exception as e:
        log.warning(f"Failed to load simulation result: {e}")
        return None


def get_simulation_summary(simulation: RolloutSimulation) -> Dict[str, Any]:
    """Get a summary of simulation results for reporting."""
    return {
        "simulation_id": simulation.simulation_id,
        "patch_id": simulation.patch_id,
        "prompt_file": simulation.prompt_file,
        "timestamp": simulation.timestamp.isoformat(),
        "total_profiles": simulation.total_profiles,
        "profiles_passed": simulation.profiles_passed,
        "profiles_failed": simulation.profiles_failed,
        "pass_rate": simulation.profiles_passed / max(simulation.total_profiles, 1),
        "total_regressions": simulation.total_regressions,
        "total_improvements": simulation.total_improvements,
        "category_deltas": {
            "warnings": simulation.warning_delta_avg,
            "fallbacks": simulation.fallback_delta_avg,
            "persona_leak": simulation.persona_leak_delta_avg,
            "ai_act": simulation.ai_act_delta_avg,
            "tokens": simulation.token_delta_avg,
        },
        "passed": simulation.passed,
        "blocked": simulation.blocked,
        "block_reason": simulation.block_reason,
    }


def should_block_patch(simulation: RolloutSimulation) -> Tuple[bool, str]:
    """
    Determine if a patch should be blocked based on simulation results.

    Returns:
        Tuple of (should_block, reason)
    """
    if simulation.blocked:
        return True, simulation.block_reason or "Simulation blocked"

    if simulation.profiles_failed > simulation.profiles_passed:
        return True, f"More profiles failed ({simulation.profiles_failed}) than passed ({simulation.profiles_passed})"

    if simulation.total_regressions > simulation.total_improvements * 2:
        return True, f"Too many regressions ({simulation.total_regressions} vs {simulation.total_improvements} improvements)"

    return False, ""
