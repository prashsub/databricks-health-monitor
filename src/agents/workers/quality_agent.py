"""
Quality Worker Agent
====================

Domain specialist for data quality, lineage, and governance.
"""

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


class QualityWorkerAgent(GenieWorkerAgent):
    """
    Quality domain worker agent.

    Handles queries related to:
    - Data quality metrics
    - Data freshness and staleness
    - Schema changes and drift
    - Data lineage tracking
    - Governance compliance
    - Table health and optimization

    Genie Space: Data Quality Monitor
    TVFs: 7 quality-related functions
    Metric Views: data_quality, governance_analytics
    ML Models: Drift detector, freshness predictor, schema analyzer
    """

    # TODO: Replace with actual Genie Space ID
    GENIE_SPACE_ID_PLACEHOLDER = "QUALITY_GENIE_SPACE_ID"

    def __init__(self, genie_space_id: str = None):
        """Initialize Quality Worker Agent."""
        super().__init__(
            domain="quality",
            genie_space_id=genie_space_id or settings.quality_genie_space_id,
        )

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with quality-specific context.

        Adds:
        - Freshness threshold context
        - Critical table focus
        - Governance framework hints
        """
        enhanced = query
        prefs = context.get("preferences", {})

        # Add freshness threshold
        if prefs.get("freshness_threshold_hours"):
            hours = prefs["freshness_threshold_hours"]
            enhanced += f" Flag tables not updated in {hours} hours."

        # Add critical table focus
        if prefs.get("critical_tables"):
            tables = ", ".join(prefs["critical_tables"])
            enhanced += f" Prioritize these critical tables: {tables}."

        # Add workspace filter
        if prefs.get("preferred_workspace"):
            enhanced += f" Focus on workspace: {prefs['preferred_workspace']}."

        # Add lineage context
        if "lineage" in query.lower():
            enhanced += " Include upstream and downstream dependencies."

        return enhanced

    def get_example_queries(self) -> list[str]:
        """Return example queries this agent handles."""
        return [
            "Which tables have quality issues?",
            "Show data freshness by schema",
            "What schema changes happened this week?",
            "Trace lineage for table: sales_facts",
            "Which tables need optimization?",
            "Show tables with high null rates",
            "List tables without data classification",
        ]
