"""
Security Worker Agent
=====================

TRAINING MATERIAL: Security Domain Worker Pattern
-------------------------------------------------

This module implements the Security Worker Agent, demonstrating how to
specialize the base worker pattern for a specific domain (security/audit).

SECURITY DOMAIN RESPONSIBILITIES:
---------------------------------
The Security Agent handles all queries related to:

1. ACCESS CONTROL: Who can access what resources
2. AUDIT LOGS: What actions were taken and by whom
3. THREAT DETECTION: Identify anomalous access patterns
4. COMPLIANCE: SOC2, HIPAA, PCI-DSS monitoring
5. DATA CLASSIFICATION: PII and sensitive data tracking

SECURITY DATA SOURCES:
----------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  SYSTEM TABLES (Audit)           │  GOLD LAYER (Enriched)              │
├──────────────────────────────────┼─────────────────────────────────────┤
│  system.access.audit            │  fact_audit_events                   │
│  system.access.table_lineage    │  dim_user_permissions                │
│  system.access.column_lineage   │  fact_access_patterns                │
│  system.information_schema.*    │  fact_data_classification            │
└──────────────────────────────────┴─────────────────────────────────────┘

KEY TVFs FOR SECURITY:
----------------------
- get_audit_events(start_date, end_date, action_type)
- get_failed_access_attempts(days)
- get_permission_changes(days)
- get_sensitive_data_access(days)
- get_user_access_summary(user_identity, days)

ML MODELS:
----------
- security_threat_detector: Anomaly detection on access patterns
- compliance_scorer: Predict compliance risk by workspace
- access_analyzer: Identify over-permissioned users

WHY SECURITY NEEDS SPECIAL HANDLING:
------------------------------------
1. SENSITIVE QUERIES: Audit trails contain user identities
2. COMPLIANCE CONTEXT: Different rules for SOC2 vs HIPAA
3. TIME-CRITICAL: Security events need recent data focus
4. ANOMALY FOCUS: Looking for "unusual" vs "normal"

Domain specialist for security, audit, and compliance queries.
"""

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Minimal Import Pattern
#
# Domain workers have minimal imports - they inherit most functionality
# from GenieWorkerAgent. Only import what's needed for this domain.

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


# =============================================================================
# SECURITY WORKER AGENT CLASS
# =============================================================================

class SecurityWorkerAgent(GenieWorkerAgent):
    """
    Security domain worker agent.
    
    TRAINING MATERIAL: Domain Worker Specialization
    ================================================
    
    This class extends GenieWorkerAgent with security-specific logic:
    
    1. GENIE SPACE: Points to Security Auditor Space
    2. QUERY ENHANCEMENT: Adds compliance and data classification context
    3. EXAMPLE QUERIES: Security-specific examples for testing/docs
    
    The inheritance chain is:
        SecurityWorkerAgent → GenieWorkerAgent → BaseWorkerAgent
    
    WHAT THIS AGENT DOES NOT DO:
    ----------------------------
    - Does NOT implement query() - inherited from GenieWorkerAgent
    - Does NOT manage Genie connection - inherited
    - Does NOT handle errors - inherited
    
    WHAT THIS AGENT SPECIALIZES:
    ----------------------------
    - enhance_query(): Adds security-specific context
    - get_example_queries(): Security-specific examples
    - Uses security Genie Space ID

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
        """
        Initialize Security Worker Agent.
        
        TRAINING MATERIAL: Domain Worker Initialization
        ================================================
        
        Simple initialization pattern:
        1. Call super().__init__() with domain name
        2. Pass domain-specific Genie Space ID
        3. No other state needed - base class handles everything
        
        The settings.security_genie_space_id is loaded from:
        1. Environment variable GENIE_SPACE_SECURITY (if set)
        2. genie_spaces.py GENIE_SPACE_REGISTRY (fallback)
        """
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
