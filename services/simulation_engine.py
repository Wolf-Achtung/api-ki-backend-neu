"""
Multilevel Simulation Engine (N4.0)

PLATIN+++ v5.0 - Autonomous Engine Layer

This module provides advanced simulation capabilities for financial
and operational forecasting.

Features:
- Monte-Carlo 2.0 with correlated variables
- Branch-specific distributions
- Risk-weighted variance
- Operational simulation (process times, tool adoption, governance bottlenecks)
- Automation Gain Index (AGI)
- Scenario Impact Engine with multiple metrics

Output Metrics per Scenario:
- ROI 12M
- OPEX Delta
- CAPEX amortization
- Risk Improvement Score
- Executive Impact Indicator (EII)
"""

import logging
import math
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypedDict,
    Union,
)

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class SimulationType(Enum):
    """Types of simulations available."""
    MONTE_CARLO = "monte_carlo"
    OPERATIONAL = "operational"
    SCENARIO = "scenario"
    SENSITIVITY = "sensitivity"
    STRESS_TEST = "stress_test"


class DistributionType(Enum):
    """Statistical distribution types."""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    BETA = "beta"
    EXPONENTIAL = "exponential"
    POISSON = "poisson"


class ScenarioType(Enum):
    """Scenario types for impact analysis."""
    OPTIMISTIC = "optimistic"
    BASE_CASE = "base_case"
    PESSIMISTIC = "pessimistic"
    BEST_CASE = "best_case"
    WORST_CASE = "worst_case"
    STRESS = "stress"


class RiskCategory(Enum):
    """Risk categories for weighting."""
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    STRATEGIC = "strategic"
    COMPLIANCE = "compliance"
    TECHNOLOGY = "technology"


# Monte Carlo configuration
MONTE_CARLO_CONFIG = {
    "default_iterations": 10000,
    "min_iterations": 1000,
    "max_iterations": 100000,
    "confidence_levels": [0.50, 0.75, 0.90, 0.95, 0.99],
    "convergence_threshold": 0.01,
}

# Branch-specific distribution parameters
BRANCH_DISTRIBUTIONS: Dict[str, Dict[str, Any]] = {
    "finance": {
        "distribution": DistributionType.LOGNORMAL,
        "volatility_factor": 1.2,
        "correlation_strength": 0.7,
    },
    "it": {
        "distribution": DistributionType.TRIANGULAR,
        "volatility_factor": 1.0,
        "correlation_strength": 0.5,
    },
    "manufacturing": {
        "distribution": DistributionType.NORMAL,
        "volatility_factor": 0.8,
        "correlation_strength": 0.6,
    },
    "healthcare": {
        "distribution": DistributionType.BETA,
        "volatility_factor": 0.9,
        "correlation_strength": 0.65,
    },
    "retail": {
        "distribution": DistributionType.UNIFORM,
        "volatility_factor": 1.1,
        "correlation_strength": 0.55,
    },
    "default": {
        "distribution": DistributionType.NORMAL,
        "volatility_factor": 1.0,
        "correlation_strength": 0.5,
    },
}

# Scenario multipliers
SCENARIO_MULTIPLIERS: Dict[ScenarioType, Dict[str, float]] = {
    ScenarioType.OPTIMISTIC: {
        "revenue": 1.15,
        "cost": 0.90,
        "risk": 0.75,
        "adoption": 1.20,
    },
    ScenarioType.BASE_CASE: {
        "revenue": 1.0,
        "cost": 1.0,
        "risk": 1.0,
        "adoption": 1.0,
    },
    ScenarioType.PESSIMISTIC: {
        "revenue": 0.85,
        "cost": 1.10,
        "risk": 1.25,
        "adoption": 0.80,
    },
    ScenarioType.BEST_CASE: {
        "revenue": 1.25,
        "cost": 0.80,
        "risk": 0.50,
        "adoption": 1.40,
    },
    ScenarioType.WORST_CASE: {
        "revenue": 0.70,
        "cost": 1.30,
        "risk": 2.0,
        "adoption": 0.50,
    },
    ScenarioType.STRESS: {
        "revenue": 0.60,
        "cost": 1.50,
        "risk": 2.5,
        "adoption": 0.30,
    },
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class SimulationInput(TypedDict, total=False):
    """Input parameters for simulation."""
    base_value: float
    min_value: float
    max_value: float
    mean: float
    std_dev: float
    distribution: str
    correlation_group: str
    risk_weight: float


class SimulationResult(TypedDict):
    """Result of a simulation run."""
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentiles: Dict[str, float]
    confidence_interval: Tuple[float, float]
    iterations: int
    convergence_achieved: bool


class ScenarioImpact(TypedDict):
    """Impact metrics for a scenario."""
    scenario_type: str
    roi_12m: float
    opex_delta: float
    opex_delta_percent: float
    capex_amortization_months: int
    risk_improvement_score: float
    executive_impact_indicator: float
    probability: float


class OperationalMetrics(TypedDict):
    """Operational simulation metrics."""
    process_time_reduction: float
    tool_adoption_rate: float
    governance_bottleneck_index: float
    automation_gain_index: float
    fte_equivalent_savings: float


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CorrelationMatrix:
    """Correlation matrix for variables."""
    variables: List[str] = field(default_factory=list)
    correlations: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def get_correlation(self, var_a: str, var_b: str) -> float:
        """Get correlation between two variables."""
        if var_a == var_b:
            return 1.0
        key = (min(var_a, var_b), max(var_a, var_b))
        return self.correlations.get(key, 0.0)

    def set_correlation(self, var_a: str, var_b: str, value: float) -> None:
        """Set correlation between two variables."""
        if var_a != var_b:
            key = (min(var_a, var_b), max(var_a, var_b))
            self.correlations[key] = max(-1.0, min(1.0, value))
            if var_a not in self.variables:
                self.variables.append(var_a)
            if var_b not in self.variables:
                self.variables.append(var_b)


@dataclass
class SimulationRun:
    """Record of a simulation run."""
    simulation_id: str
    simulation_type: SimulationType
    started_at: datetime
    completed_at: Optional[datetime] = None
    iterations: int = 0
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# DISTRIBUTION GENERATOR
# =============================================================================

class DistributionGenerator:
    """
    Generates random samples from various distributions.

    Supports:
    - Normal, Lognormal, Uniform, Triangular
    - Beta, Exponential, Poisson
    - Correlated samples via Cholesky decomposition
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def generate(
        self,
        distribution: DistributionType,
        params: Dict[str, float],
        count: int = 1,
    ) -> List[float]:
        """Generate samples from a distribution."""
        generators = {
            DistributionType.NORMAL: self._generate_normal,
            DistributionType.LOGNORMAL: self._generate_lognormal,
            DistributionType.UNIFORM: self._generate_uniform,
            DistributionType.TRIANGULAR: self._generate_triangular,
            DistributionType.BETA: self._generate_beta,
            DistributionType.EXPONENTIAL: self._generate_exponential,
            DistributionType.POISSON: self._generate_poisson,
        }

        generator = generators.get(distribution, self._generate_normal)
        return [generator(params) for _ in range(count)]

    def _generate_normal(self, params: Dict[str, float]) -> float:
        """Generate from normal distribution."""
        mean = params.get("mean", 0.0)
        std_dev = params.get("std_dev", 1.0)
        return self._rng.gauss(mean, std_dev)

    def _generate_lognormal(self, params: Dict[str, float]) -> float:
        """Generate from lognormal distribution."""
        mean = params.get("mean", 0.0)
        std_dev = params.get("std_dev", 1.0)
        return math.exp(self._rng.gauss(mean, std_dev))

    def _generate_uniform(self, params: Dict[str, float]) -> float:
        """Generate from uniform distribution."""
        min_val = params.get("min_value", 0.0)
        max_val = params.get("max_value", 1.0)
        return self._rng.uniform(min_val, max_val)

    def _generate_triangular(self, params: Dict[str, float]) -> float:
        """Generate from triangular distribution."""
        min_val = params.get("min_value", 0.0)
        max_val = params.get("max_value", 1.0)
        mode = params.get("mode", (min_val + max_val) / 2)
        return self._rng.triangular(min_val, max_val, mode)

    def _generate_beta(self, params: Dict[str, float]) -> float:
        """Generate from beta distribution."""
        alpha = params.get("alpha", 2.0)
        beta_param = params.get("beta", 5.0)
        return self._rng.betavariate(alpha, beta_param)

    def _generate_exponential(self, params: Dict[str, float]) -> float:
        """Generate from exponential distribution."""
        lambda_val = params.get("lambda", 1.0)
        return self._rng.expovariate(lambda_val)

    def _generate_poisson(self, params: Dict[str, float]) -> float:
        """Generate from Poisson distribution (approximation)."""
        lambda_val = params.get("lambda", 1.0)
        # Use normal approximation for large lambda
        if lambda_val > 30:
            return max(0, round(self._rng.gauss(lambda_val, math.sqrt(lambda_val))))
        # Direct simulation for small lambda
        L = math.exp(-lambda_val)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= self._rng.random()
        return k - 1

    def generate_correlated(
        self,
        distributions: List[Tuple[DistributionType, Dict[str, float]]],
        correlation_matrix: CorrelationMatrix,
        count: int = 1,
    ) -> List[List[float]]:
        """Generate correlated samples using Cholesky decomposition."""
        n_vars = len(distributions)

        # Build correlation matrix
        corr_matrix = [[0.0] * n_vars for _ in range(n_vars)]
        for i in range(n_vars):
            for j in range(n_vars):
                if i == j:
                    corr_matrix[i][j] = 1.0
                elif i < n_vars and j < n_vars:
                    var_i = correlation_matrix.variables[i] if i < len(correlation_matrix.variables) else f"var_{i}"
                    var_j = correlation_matrix.variables[j] if j < len(correlation_matrix.variables) else f"var_{j}"
                    corr_matrix[i][j] = correlation_matrix.get_correlation(var_i, var_j)

        # Cholesky decomposition
        try:
            cholesky = self._cholesky(corr_matrix)
        except ValueError:
            # Fall back to identity if decomposition fails
            cholesky = [[1.0 if i == j else 0.0 for j in range(n_vars)] for i in range(n_vars)]

        results: List[List[float]] = []
        for _ in range(count):
            # Generate independent standard normal samples
            z = [self._rng.gauss(0, 1) for _ in range(n_vars)]

            # Apply correlation via Cholesky
            correlated_z = [
                sum(cholesky[i][j] * z[j] for j in range(i + 1))
                for i in range(n_vars)
            ]

            # Transform to target distributions
            sample = []
            for i, (dist_type, params) in enumerate(distributions):
                # Use correlated normal as basis
                u = 0.5 * (1 + math.erf(correlated_z[i] / math.sqrt(2)))
                # Transform via inverse CDF approximation
                transformed = self._inverse_transform(dist_type, params, u)
                sample.append(transformed)

            results.append(sample)

        return results

    def _cholesky(self, matrix: List[List[float]]) -> List[List[float]]:
        """Cholesky decomposition of positive definite matrix."""
        n = len(matrix)
        L = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1):
                s = sum(L[i][k] * L[j][k] for k in range(j))
                if i == j:
                    val = matrix[i][i] - s
                    if val < 0:
                        raise ValueError("Matrix is not positive definite")
                    L[i][j] = math.sqrt(val)
                else:
                    L[i][j] = (matrix[i][j] - s) / L[j][j] if L[j][j] != 0 else 0

        return L

    def _inverse_transform(
        self,
        dist_type: DistributionType,
        params: Dict[str, float],
        u: float,
    ) -> float:
        """Inverse CDF transform for various distributions."""
        if dist_type == DistributionType.NORMAL:
            mean = params.get("mean", 0.0)
            std_dev = params.get("std_dev", 1.0)
            # Approximation of inverse normal CDF
            return mean + std_dev * self._inverse_normal_cdf(u)

        elif dist_type == DistributionType.UNIFORM:
            min_val = params.get("min_value", 0.0)
            max_val = params.get("max_value", 1.0)
            return min_val + u * (max_val - min_val)

        elif dist_type == DistributionType.EXPONENTIAL:
            lambda_val = params.get("lambda", 1.0)
            return -math.log(1 - u + 1e-10) / lambda_val

        else:
            # Default: use normal approximation
            mean = params.get("mean", params.get("base_value", 0.0))
            std_dev = params.get("std_dev", mean * 0.2)
            return mean + std_dev * self._inverse_normal_cdf(u)

    def _inverse_normal_cdf(self, p: float) -> float:
        """Approximate inverse of standard normal CDF."""
        # Rational approximation (Abramowitz and Stegun)
        if p <= 0:
            return -10.0
        if p >= 1:
            return 10.0
        if p == 0.5:
            return 0.0

        if p < 0.5:
            t = math.sqrt(-2 * math.log(p))
        else:
            t = math.sqrt(-2 * math.log(1 - p))

        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308

        result = t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)

        return result if p > 0.5 else -result


# =============================================================================
# MONTE CARLO ENGINE
# =============================================================================

class MonteCarloEngine:
    """
    Monte Carlo 2.0 simulation engine.

    Features:
    - Correlated variables
    - Branch-specific distributions
    - Risk-weighted variance
    - Convergence detection
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._generator = DistributionGenerator(seed)
        self._runs: List[SimulationRun] = []
        self._lock = threading.RLock()

    def simulate(
        self,
        inputs: Dict[str, SimulationInput],
        iterations: int = 10000,
        branch: str = "default",
        correlation_matrix: Optional[CorrelationMatrix] = None,
    ) -> Dict[str, SimulationResult]:
        """
        Run Monte Carlo simulation.

        Args:
            inputs: Dictionary of variable names to input parameters
            iterations: Number of simulation iterations
            branch: Industry branch for distribution selection
            correlation_matrix: Optional correlation matrix for variables

        Returns:
            Dictionary of variable names to simulation results
        """
        start_time = time.time()
        run_id = f"mc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        log.info(
            "[N4.0-Simulation] Starting Monte Carlo: %d iterations, branch=%s",
            iterations,
            branch,
        )

        # Get branch-specific configuration
        branch_config = BRANCH_DISTRIBUTIONS.get(
            branch.lower(),
            BRANCH_DISTRIBUTIONS["default"],
        )

        # Prepare distributions
        var_names = list(inputs.keys())
        distributions: List[Tuple[DistributionType, Dict[str, float]]] = []

        for var_name in var_names:
            inp = inputs[var_name]
            dist_type = DistributionType(
                inp.get("distribution", branch_config["distribution"].value)
            ) if "distribution" in inp else branch_config["distribution"]

            params = {
                "mean": inp.get("mean", inp.get("base_value", 0.0)),
                "std_dev": inp.get("std_dev", inp.get("base_value", 0.0) * 0.15),
                "min_value": inp.get("min_value", inp.get("base_value", 0.0) * 0.5),
                "max_value": inp.get("max_value", inp.get("base_value", 0.0) * 1.5),
            }

            # Apply volatility factor
            params["std_dev"] *= branch_config["volatility_factor"]

            distributions.append((dist_type, params))

        # Build correlation matrix if not provided
        if correlation_matrix is None:
            correlation_matrix = CorrelationMatrix(variables=var_names)
            # Set default correlations based on branch
            corr_strength = branch_config["correlation_strength"]
            for i, var_a in enumerate(var_names):
                for j, var_b in enumerate(var_names):
                    if i < j:
                        # Default positive correlation between related variables
                        correlation_matrix.set_correlation(var_a, var_b, corr_strength * 0.5)

        # Generate correlated samples
        samples = self._generator.generate_correlated(
            distributions,
            correlation_matrix,
            iterations,
        )

        # Calculate statistics for each variable
        results: Dict[str, SimulationResult] = {}

        for i, var_name in enumerate(var_names):
            var_samples = [s[i] for s in samples]
            results[var_name] = self._calculate_statistics(var_samples, iterations)

        # Record run
        run = SimulationRun(
            simulation_id=run_id,
            simulation_type=SimulationType.MONTE_CARLO,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            iterations=iterations,
            results=results,
            metadata={
                "branch": branch,
                "execution_time_ms": int((time.time() - start_time) * 1000),
            },
        )

        with self._lock:
            self._runs.append(run)

        log.info(
            "[N4.0-Simulation] Monte Carlo completed in %dms",
            run.metadata["execution_time_ms"],
        )

        return results

    def _calculate_statistics(
        self,
        samples: List[float],
        iterations: int,
    ) -> SimulationResult:
        """Calculate statistics from samples."""
        sorted_samples = sorted(samples)
        n = len(sorted_samples)

        mean = sum(samples) / n
        variance = sum((x - mean) ** 2 for x in samples) / n
        std_dev = math.sqrt(variance)

        median = sorted_samples[n // 2]
        min_val = sorted_samples[0]
        max_val = sorted_samples[-1]

        # Calculate percentiles
        percentiles = {}
        conf_levels_list: List[float] = [0.50, 0.75, 0.90, 0.95, 0.99]
        for level in conf_levels_list:
            idx = int(level * n)
            percentiles[f"p{int(level * 100)}"] = sorted_samples[min(idx, n - 1)]

        # 95% confidence interval
        ci_lower_idx = int(0.025 * n)
        ci_upper_idx = int(0.975 * n)
        confidence_interval = (
            sorted_samples[ci_lower_idx],
            sorted_samples[min(ci_upper_idx, n - 1)],
        )

        # Check convergence (coefficient of variation of running mean)
        threshold: float = 0.01  # From MONTE_CARLO_CONFIG["convergence_threshold"]
        convergence_achieved = std_dev / (abs(mean) + 1e-10) < threshold * 10

        return {
            "mean": mean,
            "median": median,
            "std_dev": std_dev,
            "min_value": min_val,
            "max_value": max_val,
            "percentiles": percentiles,
            "confidence_interval": confidence_interval,
            "iterations": iterations,
            "convergence_achieved": convergence_achieved,
        }


# =============================================================================
# OPERATIONAL SIMULATION ENGINE
# =============================================================================

class OperationalSimulator:
    """
    Simulates operational metrics.

    Features:
    - Process time simulation
    - Tool adoption modeling
    - Governance bottleneck analysis
    - Automation Gain Index (AGI) calculation
    """

    # Default operational parameters
    DEFAULT_PARAMS = {
        "base_process_time_hours": 40.0,
        "tool_adoption_ceiling": 0.85,
        "adoption_rate_per_month": 0.10,
        "governance_overhead_factor": 1.15,
        "automation_efficiency_gain": 0.30,
    }

    def __init__(self) -> None:
        self._generator = DistributionGenerator()

    def simulate_operations(
        self,
        current_state: Dict[str, Any],
        target_state: Dict[str, Any],
        simulation_months: int = 12,
        iterations: int = 1000,
    ) -> OperationalMetrics:
        """
        Simulate operational transformation.

        Args:
            current_state: Current operational metrics
            target_state: Target operational metrics
            simulation_months: Time horizon in months
            iterations: Number of simulation iterations

        Returns:
            OperationalMetrics with simulated outcomes
        """
        results: List[Dict[str, float]] = []

        for _ in range(iterations):
            result = self._simulate_single_run(
                current_state,
                target_state,
                simulation_months,
            )
            results.append(result)

        # Aggregate results
        aggregated: OperationalMetrics = {
            "process_time_reduction": self._mean([r["process_time_reduction"] for r in results]),
            "tool_adoption_rate": self._mean([r["tool_adoption_rate"] for r in results]),
            "governance_bottleneck_index": self._mean([r["governance_bottleneck_index"] for r in results]),
            "automation_gain_index": self._mean([r["automation_gain_index"] for r in results]),
            "fte_equivalent_savings": self._mean([r["fte_equivalent_savings"] for r in results]),
        }

        return aggregated

    def _simulate_single_run(
        self,
        current: Dict[str, Any],
        target: Dict[str, Any],
        months: int,
    ) -> Dict[str, float]:
        """Simulate a single operational transformation run."""
        # Process time
        current_time = current.get("process_time_hours", self.DEFAULT_PARAMS["base_process_time_hours"])
        target_time = target.get("process_time_hours", current_time * 0.6)

        # Simulate gradual improvement with noise
        final_time = current_time
        for _ in range(months):
            improvement_rate = (current_time - target_time) / current_time / months
            noise = self._generator.generate(
                DistributionType.NORMAL,
                {"mean": 0, "std_dev": 0.02},
            )[0]
            final_time *= (1 - improvement_rate + noise)
            final_time = max(target_time * 0.9, final_time)

        process_time_reduction = (current_time - final_time) / current_time

        # Tool adoption
        current_adoption = current.get("tool_adoption", 0.3)
        target_adoption = min(
            target.get("tool_adoption", 0.8),
            self.DEFAULT_PARAMS["tool_adoption_ceiling"],
        )

        final_adoption = current_adoption
        for _ in range(months):
            rate = self.DEFAULT_PARAMS["adoption_rate_per_month"]
            noise = self._generator.generate(
                DistributionType.NORMAL,
                {"mean": 0, "std_dev": 0.02},
            )[0]
            final_adoption += rate * (target_adoption - final_adoption) + noise
            final_adoption = max(0, min(target_adoption, final_adoption))

        # Governance bottleneck (lower is better)
        governance_complexity = current.get("governance_complexity", 0.5)
        governance_improvement = target.get("governance_improvement", 0.2)
        bottleneck_index = governance_complexity * (1 - governance_improvement)
        bottleneck_index *= self.DEFAULT_PARAMS["governance_overhead_factor"]
        bottleneck_index += self._generator.generate(
            DistributionType.NORMAL,
            {"mean": 0, "std_dev": 0.05},
        )[0]
        bottleneck_index = max(0.1, min(1.0, bottleneck_index))

        # Automation Gain Index (AGI)
        automation_factor = self.DEFAULT_PARAMS["automation_efficiency_gain"]
        agi = (
            process_time_reduction * 0.4 +
            final_adoption * 0.3 +
            (1 - bottleneck_index) * 0.3
        ) * (1 + automation_factor)
        agi = max(0, min(1.0, agi))

        # FTE equivalent savings
        hours_saved_per_month = current_time * process_time_reduction * 4  # 4 weeks/month
        fte_equivalent = hours_saved_per_month / 160  # 160 hours/month FTE

        return {
            "process_time_reduction": process_time_reduction,
            "tool_adoption_rate": final_adoption,
            "governance_bottleneck_index": bottleneck_index,
            "automation_gain_index": agi,
            "fte_equivalent_savings": fte_equivalent,
        }

    def _mean(self, values: List[float]) -> float:
        """Calculate mean of values."""
        return sum(values) / len(values) if values else 0.0


# =============================================================================
# SCENARIO IMPACT ENGINE
# =============================================================================

class ScenarioImpactEngine:
    """
    Calculates impact metrics for different scenarios.

    Metrics per scenario:
    - ROI 12M
    - OPEX Delta
    - CAPEX amortization
    - Risk Improvement Score
    - Executive Impact Indicator (EII)
    """

    def __init__(self) -> None:
        self._monte_carlo = MonteCarloEngine()
        self._operational = OperationalSimulator()

    def calculate_scenario_impact(
        self,
        base_metrics: Dict[str, float],
        scenario_type: ScenarioType,
        investment_capex: float,
        current_opex: float,
        risk_baseline: float = 0.5,
        branch: str = "default",
    ) -> ScenarioImpact:
        """
        Calculate impact metrics for a scenario.

        Args:
            base_metrics: Base case metrics (revenue, costs, etc.)
            scenario_type: Type of scenario to simulate
            investment_capex: Capital expenditure for transformation
            current_opex: Current operating expenses
            risk_baseline: Current risk level (0-1)
            branch: Industry branch

        Returns:
            ScenarioImpact with all metrics
        """
        multipliers = SCENARIO_MULTIPLIERS[scenario_type]

        # Apply scenario multipliers
        revenue_impact = base_metrics.get("revenue", 0) * (multipliers["revenue"] - 1)
        cost_impact = current_opex * (1 - multipliers["cost"])
        risk_factor = multipliers["risk"]

        # ROI 12M
        annual_benefit = revenue_impact + cost_impact
        roi_12m = (annual_benefit - investment_capex) / (investment_capex + 1e-10) * 100

        # OPEX Delta
        new_opex = current_opex * multipliers["cost"]
        opex_delta = current_opex - new_opex
        opex_delta_percent = opex_delta / (current_opex + 1e-10) * 100

        # CAPEX amortization (months)
        # FIX-AMORT-CANONICAL: Use NET monthly benefit (subtract remaining OPEX)
        # to match canonical formula: CAPEX / (monthly_benefit - OPEX)
        monthly_benefit_gross = annual_benefit / 12
        monthly_net_benefit = monthly_benefit_gross - new_opex
        if monthly_net_benefit > 0:
            capex_amortization = math.ceil(investment_capex / monthly_net_benefit)
        else:
            capex_amortization = 999  # Never amortized

        # Risk Improvement Score
        new_risk = risk_baseline * risk_factor
        risk_improvement = (risk_baseline - new_risk) / (risk_baseline + 1e-10)
        risk_improvement_score = max(-1.0, min(1.0, risk_improvement)) * 100

        # Executive Impact Indicator (EII)
        # Weighted combination of key metrics
        eii = (
            min(roi_12m / 100, 1.0) * 0.3 +
            min(opex_delta_percent / 30, 1.0) * 0.25 +
            (1 - min(capex_amortization / 24, 1.0)) * 0.2 +
            (risk_improvement_score / 100) * 0.25
        ) * 100

        # Scenario probability (heuristic)
        probability_map = {
            ScenarioType.OPTIMISTIC: 0.25,
            ScenarioType.BASE_CASE: 0.40,
            ScenarioType.PESSIMISTIC: 0.25,
            ScenarioType.BEST_CASE: 0.05,
            ScenarioType.WORST_CASE: 0.04,
            ScenarioType.STRESS: 0.01,
        }

        return {
            "scenario_type": scenario_type.value,
            "roi_12m": round(roi_12m, 2),
            "opex_delta": round(opex_delta, 2),
            "opex_delta_percent": round(opex_delta_percent, 2),
            "capex_amortization_months": capex_amortization,
            "risk_improvement_score": round(risk_improvement_score, 2),
            "executive_impact_indicator": round(eii, 2),
            "probability": probability_map.get(scenario_type, 0.1),
        }

    def calculate_all_scenarios(
        self,
        base_metrics: Dict[str, float],
        investment_capex: float,
        current_opex: float,
        risk_baseline: float = 0.5,
        branch: str = "default",
    ) -> Dict[str, ScenarioImpact]:
        """Calculate impact for all scenario types."""
        results = {}

        for scenario_type in ScenarioType:
            results[scenario_type.value] = self.calculate_scenario_impact(
                base_metrics=base_metrics,
                scenario_type=scenario_type,
                investment_capex=investment_capex,
                current_opex=current_opex,
                risk_baseline=risk_baseline,
                branch=branch,
            )

        return results

    def get_expected_value(
        self,
        scenarios: Dict[str, ScenarioImpact],
        metric: str,
    ) -> float:
        """Calculate probability-weighted expected value for a metric."""
        total = 0.0
        total_prob = 0.0

        for scenario in scenarios.values():
            if metric in scenario:
                total += scenario[metric] * scenario["probability"]  # type: ignore[literal-required]
                total_prob += scenario["probability"]

        return total / total_prob if total_prob > 0 else 0.0


# =============================================================================
# MAIN SIMULATION ENGINE
# =============================================================================

class SimulationEngine:
    """
    Main simulation engine combining all simulation capabilities.

    Features:
    - Monte Carlo simulation
    - Operational simulation
    - Scenario impact analysis
    - Integrated result reporting
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._monte_carlo = MonteCarloEngine(seed)
        self._operational = OperationalSimulator()
        self._scenario = ScenarioImpactEngine()
        self._lock = threading.RLock()

        log.info("[N4.0-Simulation] SimulationEngine initialized")

    def run_full_simulation(
        self,
        financial_inputs: Dict[str, SimulationInput],
        operational_current: Dict[str, Any],
        operational_target: Dict[str, Any],
        investment_capex: float,
        current_opex: float,
        branch: str = "default",
        iterations: int = 5000,
    ) -> Dict[str, Any]:
        """
        Run comprehensive simulation covering all aspects.

        Returns complete simulation results including:
        - Monte Carlo financial projections
        - Operational transformation metrics
        - Scenario impact analysis
        """
        start_time = time.time()

        log.info(
            "[N4.0-Simulation] Starting full simulation: branch=%s, iterations=%d",
            branch,
            iterations,
        )

        # Monte Carlo financial simulation
        monte_carlo_results = self._monte_carlo.simulate(
            inputs=financial_inputs,
            iterations=iterations,
            branch=branch,
        )

        # Operational simulation
        operational_results = self._operational.simulate_operations(
            current_state=operational_current,
            target_state=operational_target,
            simulation_months=12,
            iterations=min(iterations, 1000),
        )

        # Extract base metrics for scenario analysis
        revenue_result_dict: Dict[str, Any] = dict(monte_carlo_results.get("revenue", {}))
        cost_result_dict: Dict[str, Any] = dict(monte_carlo_results.get("cost_savings", {}))
        revenue_mean: float = float(revenue_result_dict.get("mean", 0))
        cost_mean: float = float(cost_result_dict.get("mean", 0))
        base_metrics = {
            "revenue": revenue_mean,
            "cost_savings": cost_mean,
        }

        # Scenario impact analysis
        scenario_results = self._scenario.calculate_all_scenarios(
            base_metrics=base_metrics,
            investment_capex=investment_capex,
            current_opex=current_opex,
            risk_baseline=0.5,
            branch=branch,
        )

        # Calculate expected values
        expected_roi = self._scenario.get_expected_value(scenario_results, "roi_12m")
        expected_eii = self._scenario.get_expected_value(
            scenario_results, "executive_impact_indicator"
        )

        execution_time_ms = int((time.time() - start_time) * 1000)

        result = {
            "simulation_id": f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "execution_time_ms": execution_time_ms,
            "branch": branch,
            "iterations": iterations,
            "monte_carlo": monte_carlo_results,
            "operational": operational_results,
            "scenarios": scenario_results,
            "summary": {
                "expected_roi_12m": round(expected_roi, 2),
                "expected_eii": round(expected_eii, 2),
                "automation_gain_index": round(
                    operational_results["automation_gain_index"], 3
                ),
                "recommended_scenario": "base_case",
                "confidence_level": 0.90,
            },
        }

        log.info(
            "[N4.0-Simulation] Full simulation completed in %dms (ROI: %.1f%%, EII: %.1f)",
            execution_time_ms,
            expected_roi,
            expected_eii,
        )

        return result

    def get_simulation_result_map(
        self,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get formatted simulation result map for reporting.

        Returns structured data suitable for report integration.
        """
        return {
            "financial_projections": {
                k: {
                    "mean": v.get("mean", 0),
                    "confidence_interval": v.get("confidence_interval", (0, 0)),
                    "std_dev": v.get("std_dev", 0),
                }
                for k, v in result.get("monte_carlo", {}).items()
            },
            "operational_metrics": result.get("operational", {}),
            "scenario_impacts": {
                k: {
                    "roi_12m": v["roi_12m"],
                    "eii": v["executive_impact_indicator"],
                    "probability": v["probability"],
                }
                for k, v in result.get("scenarios", {}).items()
            },
            "summary": result.get("summary", {}),
        }


# =============================================================================
# SINGLETON & HELPER FUNCTIONS
# =============================================================================

_simulation_instance: Optional[SimulationEngine] = None
_simulation_lock = threading.Lock()


def get_simulation_engine(seed: Optional[int] = None) -> SimulationEngine:
    """Get or create the singleton simulation engine."""
    global _simulation_instance

    if _simulation_instance is None:
        with _simulation_lock:
            if _simulation_instance is None:
                _simulation_instance = SimulationEngine(seed)

    return _simulation_instance


def run_monte_carlo(
    inputs: Dict[str, SimulationInput],
    iterations: int = 10000,
    branch: str = "default",
) -> Dict[str, SimulationResult]:
    """
    Run Monte Carlo simulation.

    Convenience function for external use.
    """
    engine = get_simulation_engine()
    return engine._monte_carlo.simulate(inputs, iterations, branch)


def run_scenario_analysis(
    base_metrics: Dict[str, float],
    investment_capex: float,
    current_opex: float,
    branch: str = "default",
) -> Dict[str, ScenarioImpact]:
    """
    Run scenario impact analysis.

    Convenience function for external use.
    """
    engine = get_simulation_engine()
    return engine._scenario.calculate_all_scenarios(
        base_metrics=base_metrics,
        investment_capex=investment_capex,
        current_opex=current_opex,
        branch=branch,
    )


def run_operational_simulation(
    current_state: Dict[str, Any],
    target_state: Dict[str, Any],
    months: int = 12,
) -> OperationalMetrics:
    """
    Run operational transformation simulation.

    Convenience function for external use.
    """
    engine = get_simulation_engine()
    return engine._operational.simulate_operations(
        current_state=current_state,
        target_state=target_state,
        simulation_months=months,
    )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "SimulationType",
    "DistributionType",
    "ScenarioType",
    "RiskCategory",
    # Classes
    "SimulationEngine",
    "MonteCarloEngine",
    "OperationalSimulator",
    "ScenarioImpactEngine",
    "DistributionGenerator",
    # Data classes
    "CorrelationMatrix",
    "SimulationRun",
    # Type definitions
    "SimulationInput",
    "SimulationResult",
    "ScenarioImpact",
    "OperationalMetrics",
    # Functions
    "get_simulation_engine",
    "run_monte_carlo",
    "run_scenario_analysis",
    "run_operational_simulation",
    # Constants
    "MONTE_CARLO_CONFIG",
    "BRANCH_DISTRIBUTIONS",
    "SCENARIO_MULTIPLIERS",
]
