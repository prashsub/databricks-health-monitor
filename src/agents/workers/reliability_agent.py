"""
Reliability Worker Agent
========================

Domain specialist for job health, SLAs, and operational reliability.
"""

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


class ReliabilityWorkerAgent(GenieWorkerAgent):
    """
    Reliability domain worker agent.

    Handles queries related to:
    - Job failures and success rates
    - SLA compliance and breaches
    - Pipeline health monitoring
    - Task execution analysis
    - Incident investigation
    - Job duration trends

    Genie Space: Job Health Monitor
    TVFs: 12 reliability-related functions
    Metric Views: job_performance
    ML Models: Failure predictor, duration estimator, SLA breach detector
    """

    # TODO: Replace with actual Genie Space ID
    GENIE_SPACE_ID_PLACEHOLDER = "RELIABILITY_GENIE_SPACE_ID"

    def __init__(self, genie_space_id: str = None):
        """Initialize Reliability Worker Agent."""
        super().__init__(
            domain="reliability",
            genie_space_id=genie_space_id or settings.reliability_genie_space_id,
        )

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with reliability-specific context.

        Adds:
        - SLA threshold context
        - Critical job focus
        - Time window defaults
        """
        enhanced = query
        prefs = context.get("preferences", {})

        # Add SLA context
        if prefs.get("sla_threshold_percent"):
            sla = prefs["sla_threshold_percent"]
            enhanced += f" Flag jobs below {sla}% success rate."

        # Add critical job focus
        if prefs.get("critical_jobs"):
            jobs = ", ".join(prefs["critical_jobs"])
            enhanced += f" Prioritize these critical jobs: {jobs}."

        # Add workspace filter
        if prefs.get("preferred_workspace"):
            enhanced += f" Focus on workspace: {prefs['preferred_workspace']}."

        # Add pipeline focus
        if "pipeline" in query.lower() or "dlt" in query.lower():
            enhanced += " Include DLT pipeline health metrics."

        return enhanced

    def get_example_queries(self) -> list[str]:
        """Return example queries this agent handles."""
        return [
            "Which jobs failed today?",
            "What is our SLA compliance this week?",
            "Show long-running jobs exceeding baseline",
            "Which pipelines have the most failures?",
            "Predict which jobs are likely to fail tomorrow",
            "Show job success rate trends",
            "What caused job X to fail?",
        ]
