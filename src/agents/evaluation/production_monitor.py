"""
Production Monitoring with MLflow GenAI
=======================================

Real-time response quality assessment using mlflow.genai.assess().
Monitors agent responses in production and logs quality metrics.

Reference:
    28-mlflow-genai-patterns.mdc cursor rule
    https://docs.databricks.com/en/mlflow/mlflow-genai.html

Usage:
    from agents.evaluation import ProductionMonitor

    monitor = ProductionMonitor()

    # Assess response quality in real-time
    assessment = monitor.assess_response(
        query="Why did costs spike?",
        response="Costs increased by 25% due to...",
        domains=["COST"]
    )

    # Check if response needs review
    if assessment.needs_review:
        alert_team(assessment)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import mlflow
import mlflow.genai
from mlflow.genai import assess, Score

from .judges import (
    domain_accuracy_judge,
    response_relevance_judge,
    actionability_judge,
    source_citation_judge,
    cost_accuracy_judge,
    security_compliance_judge,
    performance_accuracy_judge,
    reliability_accuracy_judge,
    quality_accuracy_judge,
)
from ..config import settings


@dataclass
class AssessmentResult:
    """Result of a production quality assessment."""

    timestamp: datetime
    query: str
    response: str
    domains: List[str]
    scores: Dict[str, Score]
    overall_score: float
    needs_review: bool
    alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "response": self.response[:500] + "..." if len(self.response) > 500 else self.response,
            "domains": self.domains,
            "scores": {k: {"value": v.value, "rationale": v.rationale} for k, v in self.scores.items()},
            "overall_score": self.overall_score,
            "needs_review": self.needs_review,
            "alerts": self.alerts,
        }


class ProductionMonitor:
    """
    Production monitoring for agent response quality.

    Uses mlflow.genai.assess() for real-time evaluation and
    logs results to MLflow for dashboarding and alerting.

    Attributes:
        review_threshold: Score below which responses need review
        alert_threshold: Score below which alerts are triggered
        enabled: Whether monitoring is active
    """

    def __init__(
        self,
        review_threshold: float = 0.7,
        alert_threshold: float = 0.4,
        enabled: bool = True,
    ):
        """
        Initialize production monitor.

        Args:
            review_threshold: Score threshold for flagging review
            alert_threshold: Score threshold for triggering alerts
            enabled: Whether to enable monitoring
        """
        self.review_threshold = review_threshold
        self.alert_threshold = alert_threshold
        self.enabled = enabled

        # Domain-specific judges
        self._domain_judges = {
            "cost": cost_accuracy_judge,
            "security": security_compliance_judge,
            "performance": performance_accuracy_judge,
            "reliability": reliability_accuracy_judge,
            "quality": quality_accuracy_judge,
        }

        # Default scorers for all assessments
        self._default_scorers = [
            domain_accuracy_judge,
            response_relevance_judge,
        ]

    @mlflow.trace(name="assess_response", span_type="AGENT")
    def assess_response(
        self,
        query: str,
        response: str,
        domains: List[str] = None,
        user_id: str = None,
        session_id: str = None,
        additional_context: Dict = None,
    ) -> AssessmentResult:
        """
        Assess a single response in production.

        Args:
            query: User query
            response: Agent response
            domains: Domains involved in the response
            user_id: Optional user identifier
            session_id: Optional session identifier
            additional_context: Optional additional context

        Returns:
            AssessmentResult with scores and review flags.
        """
        if not self.enabled:
            return self._create_disabled_result(query, response, domains or [])

        with mlflow.start_span(name="production_assess") as span:
            span.set_inputs({
                "query": query,
                "domains": domains,
                "user_id": user_id,
            })

            # Prepare inputs and outputs for assess()
            inputs = {"query": query}
            outputs = {"response": response}

            if additional_context:
                inputs["context"] = additional_context

            # Select scorers based on domains
            scorers = self._select_scorers(domains or [])

            # Run assessment using mlflow.genai.assess()
            try:
                assessment = assess(
                    inputs=inputs,
                    outputs=outputs,
                    scorers=scorers,
                )

                # Parse assessment results
                scores = self._parse_assessment(assessment)

            except Exception as e:
                # Fallback to manual scoring if assess() fails
                scores = self._manual_assess(inputs, outputs, scorers)

            # Calculate overall score
            overall_score = self._calculate_overall_score(scores)

            # Determine review needs and alerts
            needs_review = overall_score < self.review_threshold
            alerts = self._generate_alerts(scores, overall_score, domains or [])

            result = AssessmentResult(
                timestamp=datetime.utcnow(),
                query=query,
                response=response,
                domains=domains or [],
                scores=scores,
                overall_score=overall_score,
                needs_review=needs_review,
                alerts=alerts,
            )

            # Log to MLflow
            self._log_assessment(result, user_id, session_id)

            span.set_outputs({
                "overall_score": overall_score,
                "needs_review": needs_review,
                "alert_count": len(alerts),
            })

            return result

    def _select_scorers(self, domains: List[str]) -> List:
        """Select appropriate scorers based on domains."""
        scorers = list(self._default_scorers)

        for domain in domains:
            domain_lower = domain.lower()
            if domain_lower in self._domain_judges:
                scorers.append(self._domain_judges[domain_lower])

        return scorers

    def _parse_assessment(self, assessment) -> Dict[str, Score]:
        """Parse mlflow.genai.assess() result into Score dict."""
        scores = {}

        if hasattr(assessment, "results"):
            for result in assessment.results:
                name = getattr(result, "name", "unknown")
                value = getattr(result, "value", 0.5)
                rationale = getattr(result, "rationale", "")
                scores[name] = Score(value=value, rationale=rationale)

        elif isinstance(assessment, dict):
            for name, result in assessment.items():
                if isinstance(result, Score):
                    scores[name] = result
                elif isinstance(result, dict):
                    scores[name] = Score(
                        value=result.get("value", 0.5),
                        rationale=result.get("rationale", ""),
                    )

        return scores

    def _manual_assess(
        self,
        inputs: Dict,
        outputs: Dict,
        scorers: List,
    ) -> Dict[str, Score]:
        """Manually run scorers if assess() fails."""
        scores = {}

        for scorer_func in scorers:
            try:
                name = getattr(scorer_func, "__name__", str(scorer_func))
                score = scorer_func(inputs, outputs, None)
                scores[name] = score
            except Exception as e:
                scores[name] = Score(value=0.5, rationale=f"Error: {str(e)}")

        return scores

    def _calculate_overall_score(self, scores: Dict[str, Score]) -> float:
        """Calculate weighted overall score."""
        if not scores:
            return 0.5

        # Weight configuration (can be customized)
        weights = {
            "domain_accuracy_judge": 1.5,
            "response_relevance_judge": 1.5,
            "cost_accuracy_judge": 1.0,
            "security_compliance_judge": 1.0,
            "performance_accuracy_judge": 1.0,
            "reliability_accuracy_judge": 1.0,
            "quality_accuracy_judge": 1.0,
        }

        total_weight = 0
        weighted_sum = 0

        for name, score in scores.items():
            weight = weights.get(name, 1.0)
            weighted_sum += score.value * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _generate_alerts(
        self,
        scores: Dict[str, Score],
        overall_score: float,
        domains: List[str],
    ) -> List[str]:
        """Generate alerts for low-quality responses."""
        alerts = []

        # Overall score alert
        if overall_score < self.alert_threshold:
            alerts.append(f"CRITICAL: Overall quality score {overall_score:.2f} below threshold {self.alert_threshold}")

        # Individual score alerts
        for name, score in scores.items():
            if score.value < 0.3:
                alerts.append(f"LOW: {name} scored {score.value:.2f} - {score.rationale}")

        # Security-specific alerts
        if "security" in [d.lower() for d in domains]:
            security_score = scores.get("security_compliance_judge")
            if security_score and security_score.value < 0.5:
                alerts.append(f"SECURITY: Response may have security issues - {security_score.rationale}")

        return alerts

    def _log_assessment(
        self,
        result: AssessmentResult,
        user_id: str = None,
        session_id: str = None,
    ) -> None:
        """Log assessment results to MLflow."""
        try:
            # Log metrics
            mlflow.log_metric("production_overall_score", result.overall_score)

            for name, score in result.scores.items():
                metric_name = f"production_{name}"
                mlflow.log_metric(metric_name, score.value)

            if result.needs_review:
                mlflow.log_metric("production_needs_review", 1)

            mlflow.log_metric("production_alert_count", len(result.alerts))

            # Update trace tags
            mlflow.update_current_trace(tags={
                "production_overall_score": str(result.overall_score),
                "production_needs_review": str(result.needs_review),
                "user_id": user_id or "unknown",
                "session_id": session_id or "unknown",
            })

        except Exception:
            # Don't fail the response for logging errors
            pass

    def _create_disabled_result(
        self,
        query: str,
        response: str,
        domains: List[str],
    ) -> AssessmentResult:
        """Create a placeholder result when monitoring is disabled."""
        return AssessmentResult(
            timestamp=datetime.utcnow(),
            query=query,
            response=response,
            domains=domains,
            scores={},
            overall_score=1.0,
            needs_review=False,
            alerts=[],
        )

    def assess_batch(
        self,
        interactions: List[Dict],
    ) -> List[AssessmentResult]:
        """
        Assess a batch of interactions.

        Args:
            interactions: List of dicts with 'query', 'response', 'domains' keys

        Returns:
            List of AssessmentResult objects.
        """
        results = []

        for interaction in interactions:
            result = self.assess_response(
                query=interaction.get("query", ""),
                response=interaction.get("response", ""),
                domains=interaction.get("domains", []),
                user_id=interaction.get("user_id"),
                session_id=interaction.get("session_id"),
            )
            results.append(result)

        return results

    def get_alert_summary(
        self,
        results: List[AssessmentResult],
    ) -> Dict:
        """
        Generate summary of alerts from assessment results.

        Args:
            results: List of AssessmentResult objects

        Returns:
            Summary dict with alert statistics.
        """
        total = len(results)
        needs_review = sum(1 for r in results if r.needs_review)
        with_alerts = sum(1 for r in results if r.alerts)
        avg_score = sum(r.overall_score for r in results) / total if total > 0 else 0

        all_alerts = []
        for r in results:
            all_alerts.extend(r.alerts)

        return {
            "total_assessments": total,
            "needs_review_count": needs_review,
            "needs_review_pct": needs_review / total * 100 if total > 0 else 0,
            "with_alerts_count": with_alerts,
            "average_score": avg_score,
            "total_alerts": len(all_alerts),
            "critical_alerts": sum(1 for a in all_alerts if "CRITICAL" in a),
            "security_alerts": sum(1 for a in all_alerts if "SECURITY" in a),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

# Global monitor instance
_production_monitor: Optional[ProductionMonitor] = None


def get_production_monitor() -> ProductionMonitor:
    """Get the singleton ProductionMonitor instance."""
    global _production_monitor
    if _production_monitor is None:
        _production_monitor = ProductionMonitor()
    return _production_monitor


def monitor_response_quality(
    inputs: Dict,
    outputs: Dict,
    scorers: List = None,
) -> Dict[str, Score]:
    """
    Quick function to monitor response quality.

    This is a simplified interface for production monitoring
    as specified in the cursor rule.

    Args:
        inputs: Dict with 'query' key
        outputs: Dict with 'response' key
        scorers: Optional list of scorers to use

    Returns:
        Dict of scorer name to Score object.

    Example:
        from agents.evaluation import monitor_response_quality

        assessment = monitor_response_quality(
            inputs={"query": "Why did costs spike?"},
            outputs={"response": "Costs increased due to..."}
        )
    """
    scorers = scorers or [domain_accuracy_judge, response_relevance_judge]

    try:
        assessment = assess(
            inputs=inputs,
            outputs=outputs,
            scorers=scorers,
        )

        # Parse results
        scores = {}
        if hasattr(assessment, "results"):
            for result in assessment.results:
                name = getattr(result, "name", "unknown")
                scores[name] = Score(
                    value=getattr(result, "value", 0.5),
                    rationale=getattr(result, "rationale", ""),
                )
        return scores

    except Exception as e:
        # Fallback to manual execution
        scores = {}
        for scorer_func in scorers:
            name = getattr(scorer_func, "__name__", str(scorer_func))
            try:
                scores[name] = scorer_func(inputs, outputs, None)
            except Exception as inner_e:
                scores[name] = Score(value=0.5, rationale=f"Error: {str(inner_e)}")
        return scores


def assess_and_alert(
    query: str,
    response: str,
    domains: List[str] = None,
    alert_callback: callable = None,
) -> AssessmentResult:
    """
    Assess response and trigger alerts if needed.

    Args:
        query: User query
        response: Agent response
        domains: Domains involved
        alert_callback: Optional callback for alerts

    Returns:
        AssessmentResult with scores and alerts.
    """
    monitor = get_production_monitor()

    result = monitor.assess_response(
        query=query,
        response=response,
        domains=domains,
    )

    if result.alerts and alert_callback:
        alert_callback(result.alerts)

    return result

