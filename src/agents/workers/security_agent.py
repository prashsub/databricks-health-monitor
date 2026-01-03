"""
Security Worker Agent
=====================

Domain specialist for security, audit, and compliance queries.
"""

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


class SecurityWorkerAgent(GenieWorkerAgent):
    """
    Security domain worker agent.

    Handles queries related to:
    - Access control and permissions
    - Audit log analysis
    - Threat detection
    - Compliance monitoring
    - User activity tracking
    - Sensitive data access

    Genie Space: Security Auditor
    TVFs: 10 security-related functions
    Metric Views: security_events, governance_analytics
    ML Models: Threat detector, compliance scorer, access analyzer
    """

    # TODO: Replace with actual Genie Space ID
    GENIE_SPACE_ID_PLACEHOLDER = "SECURITY_GENIE_SPACE_ID"

    def __init__(self, genie_space_id: str = None):
        """Initialize Security Worker Agent."""
        super().__init__(
            domain="security",
            genie_space_id=genie_space_id or settings.security_genie_space_id,
        )

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with security-specific context.

        Adds:
        - Sensitive data handling hints
        - Compliance framework context
        - Time range for audit queries
        """
        enhanced = query
        prefs = context.get("preferences", {})

        # Add sensitive data context
        if "sensitive" in query.lower() or "pii" in query.lower():
            enhanced += " Include data classification tags and access patterns."

        # Add compliance context
        if prefs.get("compliance_framework"):
            framework = prefs["compliance_framework"]
            enhanced += f" Consider {framework} compliance requirements."

        # Add workspace filter
        if prefs.get("preferred_workspace"):
            enhanced += f" Focus on workspace: {prefs['preferred_workspace']}."

        return enhanced

    def get_example_queries(self) -> list[str]:
        """Return example queries this agent handles."""
        return [
            "Who accessed sensitive data last week?",
            "Show failed login attempts today",
            "What permissions changed recently?",
            "Are there any unusual access patterns?",
            "List users with admin privileges",
            "Show audit logs for table: customer_data",
            "Check compliance status for SOC2",
        ]
