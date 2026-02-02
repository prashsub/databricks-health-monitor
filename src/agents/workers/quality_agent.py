"""
Quality Worker Agent
====================

TRAINING MATERIAL: Quality Domain Worker Pattern
------------------------------------------------

This module implements the Quality Worker Agent, specializing in
data quality monitoring, lineage tracking, and governance compliance.

QUALITY DOMAIN RESPONSIBILITIES:
--------------------------------
The Quality Agent handles queries related to:

1. DATA FRESHNESS: Is data current? When was it last updated?
2. DATA QUALITY: Null rates, uniqueness, validity
3. SCHEMA DRIFT: Column changes, type changes
4. LINEAGE: Upstream/downstream dependencies
5. GOVERNANCE: Classification, ownership, documentation

DATA QUALITY DIMENSIONS (Industry Standard):
--------------------------------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  DIMENSION        │  DEFINITION                   │  METRICS           │
├───────────────────┼───────────────────────────────┼────────────────────┤
│  COMPLETENESS     │  Data exists (not null)       │  null_rate         │
│  UNIQUENESS       │  No duplicates                │  duplicate_rate    │
│  VALIDITY         │  Conforms to rules            │  invalid_rate      │
│  CONSISTENCY      │  Same across systems          │  mismatch_rate     │
│  TIMELINESS       │  Data is current              │  freshness_hours   │
│  ACCURACY         │  Reflects reality             │  error_rate        │
└───────────────────┴───────────────────────────────┴────────────────────┘

QUALITY DATA SOURCES:
---------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  LAKEHOUSE MONITORING            │  GOLD LAYER (Enriched)              │
├──────────────────────────────────┼─────────────────────────────────────┤
│  {table}_profile_metrics        │  fact_table_quality                  │
│  {table}_drift_metrics          │  fact_schema_changes                 │
│  system.information_schema.*    │  dim_table_metadata                  │
│  system.access.table_lineage    │  fact_lineage_graph                  │
└──────────────────────────────────┴─────────────────────────────────────┘

KEY TVFs FOR QUALITY:
---------------------
- get_table_freshness(schema_pattern) → Last update times
- get_quality_issues(days) → Tables with quality problems
- get_schema_changes(days) → Recent schema modifications
- get_table_lineage(table_name) → Upstream/downstream deps
- get_unclassified_tables() → Governance gaps

ML MODELS:
----------
- drift_detector: Detect statistical drift in columns
- freshness_predictor: Predict update delays
- schema_analyzer: Classify schema change impact

Domain specialist for data quality, lineage, and governance.
"""

# =============================================================================
# IMPORTS
# =============================================================================

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


# =============================================================================
# QUALITY WORKER AGENT CLASS
# =============================================================================

class QualityWorkerAgent(GenieWorkerAgent):
    """
    Quality domain worker agent.
    
    TRAINING MATERIAL: Quality-Specific Enhancements
    =================================================
    
    This agent specializes in quality queries with:
    
    1. FRESHNESS THRESHOLDS: User-defined staleness limits
    2. CRITICAL TABLES: Focus on high-priority tables
    3. LINEAGE CONTEXT: Include dependencies in analysis
    
    QUALITY INVESTIGATION FLOW:
    ---------------------------
    When a user asks "What's wrong with table X?":
    
    1. CHECK FRESHNESS: Is it stale?
    2. CHECK COMPLETENESS: Null rates, row counts
    3. CHECK DRIFT: Did the distribution change?
    4. CHECK SCHEMA: Were columns added/removed?
    5. CHECK UPSTREAM: Did source tables have issues?

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
        """
        Initialize Quality Worker Agent.
        
        TRAINING MATERIAL: Cross-Domain Awareness
        =========================================
        
        The Quality agent often needs to reference other domains:
        - RELIABILITY: Did job failures cause stale data?
        - COST: Is quality monitoring expensive?
        - SECURITY: Who modified the schema?
        
        This cross-domain awareness is handled by the orchestrator,
        not within this worker. The worker focuses on quality data only.
        """
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
