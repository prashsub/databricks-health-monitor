"""
Cost Worker Agent
=================

Domain specialist for cost analysis, billing, and FinOps queries.
"""

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


class CostWorkerAgent(GenieWorkerAgent):
    """
    Cost domain worker agent.

    Handles queries related to:
    - Billing and spending analysis
    - DBU usage and allocation
    - Budget tracking and forecasting
    - Cost anomaly detection
    - Chargeback and showback
    - SKU analysis

    Genie Space: Cost Intelligence
    TVFs: 15 cost-related functions
    Metric Views: cost_analytics, commit_tracking
    ML Models: Cost anomaly, forecast, budget alerts
    """

    # TODO: Replace with actual Genie Space ID
    GENIE_SPACE_ID_PLACEHOLDER = "COST_GENIE_SPACE_ID"

    def __init__(self, genie_space_id: str = None):
        """Initialize Cost Worker Agent."""
        super().__init__(
            domain="cost",
            genie_space_id=genie_space_id or settings.cost_genie_space_id,
        )

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with cost-specific context.

        Adds:
        - Cost threshold preferences
        - Workspace focus
        - Time range defaults
        """
        enhanced = query
        prefs = context.get("preferences", {})

        # Add cost threshold if available
        if prefs.get("cost_threshold"):
            threshold = prefs["cost_threshold"]
            enhanced += f" Flag any costs exceeding ${threshold}."

        # Add workspace filter
        if prefs.get("preferred_workspace"):
            enhanced += f" Focus on workspace: {prefs['preferred_workspace']}."

        # Add user role context for response formatting
        role = context.get("user_role")
        if role == "manager":
            enhanced += " Provide executive summary with key metrics."
        elif role == "analyst":
            enhanced += " Include detailed breakdowns and trends."

        return enhanced

    def get_example_queries(self) -> list[str]:
        """Return example queries this agent handles."""
        return [
            "Why did costs spike yesterday?",
            "What are the top 10 most expensive jobs?",
            "Show DBU usage by workspace for last month",
            "Which teams are over budget?",
            "Forecast next month's spending",
            "What SKUs are driving cost increases?",
            "Show untagged resource costs",
        ]
