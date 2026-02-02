"""
Reliability Worker Agent
========================

TRAINING MATERIAL: Reliability Domain Worker Pattern
----------------------------------------------------

This module implements the Reliability Worker Agent, specializing in
job health monitoring, SLA compliance, and incident investigation.

RELIABILITY DOMAIN RESPONSIBILITIES:
------------------------------------
The Reliability Agent handles queries related to:

1. JOB FAILURES: What failed, why, and how often
2. SLA COMPLIANCE: Are jobs meeting their targets
3. PIPELINE HEALTH: DLT pipeline status and errors
4. INCIDENT INVESTIGATION: Root cause analysis
5. CAPACITY PLANNING: Duration trends, resource needs

RELIABILITY DATA SOURCES:
-------------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  SYSTEM TABLES (Raw)             │  GOLD LAYER (Enriched)              │
├──────────────────────────────────┼─────────────────────────────────────┤
│  system.lakeflow.job_run_timeline│  fact_job_runs                      │
│  system.lakeflow.job_tasks       │  fact_job_tasks                     │
│  system.workflow.job_run_timeline│  fact_pipeline_runs                 │
│  system.billing.usage            │  fact_job_cost                      │
└──────────────────────────────────┴─────────────────────────────────────┘

KEY TVFs FOR RELIABILITY:
-------------------------
- get_failed_jobs(days) → Recent job failures with error details
- get_job_success_rate(days) → Success/failure metrics by job
- get_sla_compliance(days) → Jobs vs SLA targets
- get_long_running_jobs(threshold_minutes) → Duration outliers
- get_job_failure_root_cause(job_id, run_id) → Error analysis

ML MODELS:
----------
- job_failure_predictor: Predict which jobs will fail
- duration_estimator: Forecast job completion time
- sla_breach_detector: Alert on likely SLA violations

SLA METRICS EXPLAINED:
----------------------
Common SLA metrics this agent reports on:

1. SUCCESS RATE: (successful_runs / total_runs) * 100
   - Critical jobs typically target 99.9%+
   - Standard jobs target 99%+

2. DURATION SLA: (runs_within_target / total_runs) * 100
   - "Job X should complete in < 30 minutes"

3. DATA FRESHNESS: How recent is the latest data
   - "Table should be updated within 2 hours"

Domain specialist for job health, SLAs, and operational reliability.
"""

# =============================================================================
# IMPORTS
# =============================================================================

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


# =============================================================================
# RELIABILITY WORKER AGENT CLASS
# =============================================================================

class ReliabilityWorkerAgent(GenieWorkerAgent):
    """
    Reliability domain worker agent.
    
    TRAINING MATERIAL: Reliability-Specific Enhancements
    =====================================================
    
    This agent specializes in reliability queries with:
    
    1. SLA CONTEXT: User-defined success rate thresholds
    2. CRITICAL JOBS: Focus on high-priority jobs
    3. PIPELINE AWARENESS: DLT-specific metrics
    
    INCIDENT INVESTIGATION FLOW:
    ----------------------------
    When a user asks "Why did job X fail?":
    
    1. GET RECENT RUNS: Find the specific failure
    2. GET ERROR DETAILS: Extract error message/code
    3. CHECK PATTERNS: Is this a recurring failure?
    4. ANALYZE RESOURCES: Did it run out of memory/time?
    5. CHECK DEPENDENCIES: Did upstream jobs fail?

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
        """
        Initialize Reliability Worker Agent.
        
        TRAINING MATERIAL: Domain Identification
        ========================================
        
        The domain="reliability" string is used for:
        1. MLflow tracing span names (reliability_query, etc.)
        2. Genie Space lookup (genie_spaces.py key)
        3. Logging and error messages
        4. Intent classification routing
        """
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
