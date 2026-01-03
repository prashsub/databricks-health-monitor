"""
Prompt A/B Testing
==================

A/B testing framework for comparing prompt variants in production.

Reference:
    28-mlflow-genai-patterns.mdc cursor rule
    docs/agent-framework-design/10-prompt-registry.md

Usage:
    from agents.prompts import PromptABTest

    ab_test = PromptABTest(
        prompt_name="orchestrator",
        variants={"control": "v1", "treatment": "v2"},
        traffic_split={"control": 0.5, "treatment": 0.5}
    )

    # Select variant for user
    variant, prompt = ab_test.select_variant(user_id="user@example.com")

    # Log variant-specific metrics
    ab_test.log_variant_metrics(variant, {"latency_ms": 150, "quality_score": 0.92})
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
import hashlib
import random
import mlflow
import mlflow.genai

from ..config import settings


@dataclass
class ABTestMetrics:
    """Metrics for an A/B test variant."""

    variant_name: str
    impressions: int = 0
    total_latency_ms: float = 0.0
    total_quality_score: float = 0.0
    errors: int = 0

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        return self.total_latency_ms / self.impressions if self.impressions > 0 else 0.0

    @property
    def avg_quality_score(self) -> float:
        """Average quality score."""
        return self.total_quality_score / self.impressions if self.impressions > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Error rate as a fraction."""
        return self.errors / self.impressions if self.impressions > 0 else 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            "variant_name": self.variant_name,
            "impressions": self.impressions,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_quality_score": self.avg_quality_score,
            "error_rate": self.error_rate,
        }


class PromptABTest:
    """
    A/B testing framework for prompt variants.

    Enables controlled experiments comparing different prompt versions
    with consistent user assignment and metric tracking.

    Attributes:
        prompt_name: Base prompt name in registry
        variants: Dict of variant name to version/alias
        traffic_split: Dict of variant name to traffic percentage (0-1)
        metrics: Dict of variant metrics
    """

    def __init__(
        self,
        prompt_name: str,
        variants: Dict[str, str],
        traffic_split: Dict[str, float] = None,
        experiment_name: str = None,
    ):
        """
        Initialize A/B test for a prompt.

        Args:
            prompt_name: Prompt name in registry (e.g., "orchestrator")
            variants: Dict mapping variant names to version/alias
                      e.g., {"control": "production", "treatment": "v3"}
            traffic_split: Dict mapping variant names to traffic fraction
                          e.g., {"control": 0.5, "treatment": 0.5}
                          Must sum to 1.0
            experiment_name: MLflow experiment for logging

        Example:
            ab_test = PromptABTest(
                prompt_name="orchestrator",
                variants={"control": "production", "treatment": "v3"},
                traffic_split={"control": 0.5, "treatment": 0.5}
            )
        """
        self.prompt_name = prompt_name
        self.variants = variants
        self.experiment_name = experiment_name

        # Default to even split
        if traffic_split is None:
            equal_share = 1.0 / len(variants)
            traffic_split = {name: equal_share for name in variants}

        # Validate traffic split
        total = sum(traffic_split.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")

        self.traffic_split = traffic_split

        # Initialize metrics tracking
        self.metrics: Dict[str, ABTestMetrics] = {
            name: ABTestMetrics(variant_name=name)
            for name in variants
        }

        # Cache for loaded prompts
        self._prompt_cache: Dict[str, str] = {}

    def select_variant(
        self,
        user_id: str = None,
        deterministic: bool = True,
    ) -> Tuple[str, str]:
        """
        Select a variant for a user.

        Args:
            user_id: User identifier for consistent assignment
            deterministic: If True, same user always gets same variant

        Returns:
            Tuple of (variant_name, prompt_template)

        Example:
            variant, prompt = ab_test.select_variant("user@example.com")
            print(f"Assigned to: {variant}")
        """
        # Select variant
        if user_id and deterministic:
            variant = self._deterministic_select(user_id)
        else:
            variant = self._random_select()

        # Load prompt for variant
        prompt = self._load_variant_prompt(variant)

        # Track impression
        self.metrics[variant].impressions += 1

        # Log to MLflow
        self._log_assignment(user_id, variant)

        return variant, prompt

    def _deterministic_select(self, user_id: str) -> str:
        """
        Deterministically select variant based on user_id hash.

        This ensures the same user always gets the same variant.
        """
        # Create hash from user_id
        hash_input = f"{self.prompt_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Normalize to [0, 1)
        normalized = (hash_value % 10000) / 10000.0

        # Select based on cumulative traffic split
        cumulative = 0.0
        for variant, split in self.traffic_split.items():
            cumulative += split
            if normalized < cumulative:
                return variant

        # Fallback to last variant
        return list(self.traffic_split.keys())[-1]

    def _random_select(self) -> str:
        """Randomly select variant based on traffic split."""
        rand = random.random()
        cumulative = 0.0

        for variant, split in self.traffic_split.items():
            cumulative += split
            if rand < cumulative:
                return variant

        return list(self.traffic_split.keys())[-1]

    def _load_variant_prompt(self, variant: str) -> str:
        """Load prompt for a variant from registry."""
        if variant in self._prompt_cache:
            return self._prompt_cache[variant]

        version_or_alias = self.variants[variant]
        model_name = f"health_monitor_{self.prompt_name}_prompt"

        try:
            uri = f"prompts:/{model_name}/{version_or_alias}"
            prompt = mlflow.genai.load_prompt(uri)
            self._prompt_cache[variant] = prompt
            return prompt
        except Exception as e:
            # Return empty string on failure
            print(f"Failed to load prompt for variant {variant}: {e}")
            return ""

    def _log_assignment(self, user_id: str, variant: str) -> None:
        """Log variant assignment to MLflow trace."""
        try:
            mlflow.update_current_trace(tags={
                "ab_test": self.prompt_name,
                "ab_variant": variant,
                "ab_user_id": user_id or "anonymous",
            })
        except Exception:
            pass  # Don't fail on logging errors

    def log_variant_metrics(
        self,
        variant: str,
        metrics: Dict[str, float],
    ) -> None:
        """
        Log metrics for a variant.

        Args:
            variant: Variant name
            metrics: Dict of metric name to value
                     Expected keys: latency_ms, quality_score, error (bool)

        Example:
            ab_test.log_variant_metrics(
                "treatment",
                {"latency_ms": 150, "quality_score": 0.92, "error": False}
            )
        """
        if variant not in self.metrics:
            return

        variant_metrics = self.metrics[variant]

        if "latency_ms" in metrics:
            variant_metrics.total_latency_ms += metrics["latency_ms"]

        if "quality_score" in metrics:
            variant_metrics.total_quality_score += metrics["quality_score"]

        if metrics.get("error", False):
            variant_metrics.errors += 1

        # Log to MLflow
        try:
            for name, value in metrics.items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(f"ab_{variant}_{name}", value)
        except Exception:
            pass

    def get_results(self) -> Dict[str, Dict]:
        """
        Get A/B test results.

        Returns:
            Dict of variant name to metrics dict.
        """
        return {
            name: metrics.to_dict()
            for name, metrics in self.metrics.items()
        }

    def get_winner(self, metric: str = "quality_score") -> Optional[str]:
        """
        Determine the winning variant.

        Args:
            metric: Metric to compare ("quality_score" or "latency_ms")

        Returns:
            Name of winning variant, or None if insufficient data.
        """
        min_impressions = 10

        valid_variants = [
            (name, m) for name, m in self.metrics.items()
            if m.impressions >= min_impressions
        ]

        if len(valid_variants) < 2:
            return None

        if metric == "quality_score":
            return max(valid_variants, key=lambda x: x[1].avg_quality_score)[0]
        elif metric == "latency_ms":
            return min(valid_variants, key=lambda x: x[1].avg_latency_ms)[0]
        else:
            return None

    def reset_metrics(self) -> None:
        """Reset all metrics for a new test period."""
        for name in self.metrics:
            self.metrics[name] = ABTestMetrics(variant_name=name)

    def __repr__(self) -> str:
        return (
            f"PromptABTest(prompt='{self.prompt_name}', "
            f"variants={list(self.variants.keys())}, "
            f"split={self.traffic_split})"
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def create_ab_test(
    prompt_name: str,
    control_version: str = "production",
    treatment_version: str = "development",
    treatment_traffic: float = 0.1,
) -> PromptABTest:
    """
    Create a simple A/B test with control and treatment.

    Args:
        prompt_name: Prompt name in registry
        control_version: Control variant version/alias (default: production)
        treatment_version: Treatment variant version/alias
        treatment_traffic: Fraction of traffic for treatment (0-1)

    Returns:
        Configured PromptABTest instance.

    Example:
        # Test new orchestrator prompt with 10% of traffic
        ab_test = create_ab_test(
            "orchestrator",
            treatment_version="v3",
            treatment_traffic=0.1
        )
    """
    return PromptABTest(
        prompt_name=prompt_name,
        variants={
            "control": control_version,
            "treatment": treatment_version,
        },
        traffic_split={
            "control": 1.0 - treatment_traffic,
            "treatment": treatment_traffic,
        },
    )


def create_multi_variant_test(
    prompt_name: str,
    variants: Dict[str, str],
) -> PromptABTest:
    """
    Create a multi-variant test with even traffic split.

    Args:
        prompt_name: Prompt name in registry
        variants: Dict of variant name to version/alias

    Returns:
        Configured PromptABTest instance.

    Example:
        ab_test = create_multi_variant_test(
            "synthesizer",
            {
                "concise": "v1",
                "detailed": "v2",
                "technical": "v3"
            }
        )
    """
    return PromptABTest(
        prompt_name=prompt_name,
        variants=variants,
    )

