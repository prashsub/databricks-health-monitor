"""
Performance Worker Agent
========================

TRAINING MATERIAL: Performance Domain Worker Pattern
----------------------------------------------------

This module implements the Performance Worker Agent, specializing in
query optimization and compute resource efficiency analysis.

PERFORMANCE DOMAIN RESPONSIBILITIES:
------------------------------------
The Performance Agent handles queries related to:

1. QUERY ANALYSIS: Slow queries, full scans, missing indexes
2. WAREHOUSE SIZING: Right-sizing SQL warehouses
3. CLUSTER EFFICIENCY: Utilization, autoscaling, idle time
4. CACHE OPTIMIZATION: Hit rates, data locality
5. COST-PERFORMANCE: DBU efficiency, cost per query

PERFORMANCE DATA SOURCES:
-------------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  SYSTEM TABLES (Raw)             │  GOLD LAYER (Enriched)              │
├──────────────────────────────────┼─────────────────────────────────────┤
│  system.query.history           │  fact_query_performance              │
│  system.compute.clusters        │  fact_cluster_utilization            │
│  system.compute.warehouses      │  fact_warehouse_efficiency           │
│  system.billing.usage           │  fact_compute_cost                   │
└──────────────────────────────────┴─────────────────────────────────────┘

KEY TVFs FOR PERFORMANCE:
-------------------------
- get_slow_queries(days, threshold_seconds)
- get_warehouse_utilization(warehouse_id, days)
- get_cluster_rightsizing_recommendations()
- get_query_latency_percentiles(days)
- get_cache_hit_analysis(warehouse_id)

ML MODELS:
----------
- query_latency_predictor: Estimate query duration
- cache_benefit_predictor: Which queries benefit from caching
- cluster_rightsizer: Optimal cluster size recommendations

PERFORMANCE OPTIMIZATION HIERARCHY:
-----------------------------------
When users ask about performance, prioritize in this order:
1. QUERY OPTIMIZATION: Fix the query (free)
2. CACHING: Enable/configure caching (low cost)
3. WAREHOUSE SIZING: Right-size compute (medium cost)
4. CLUSTER CONFIG: Optimize cluster settings (medium cost)
5. MORE RESOURCES: Add compute (high cost)

Domain specialist for query and cluster performance optimization.
"""

# =============================================================================
# IMPORTS
# =============================================================================

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


# =============================================================================
# PERFORMANCE WORKER AGENT CLASS
# =============================================================================

class PerformanceWorkerAgent(GenieWorkerAgent):
    """
    Performance domain worker agent.
    
    TRAINING MATERIAL: Performance-Specific Enhancements
    =====================================================
    
    This agent specializes in performance queries with:
    
    1. THRESHOLD CONTEXT: User-defined latency thresholds
    2. RESOURCE FOCUS: Specific warehouse/cluster focus
    3. OPTIMIZATION HINTS: Caching, sizing recommendations
    
    PERFORMANCE ANALYSIS PATTERNS:
    ------------------------------
    - "What are the slowest queries?" → Sort by duration, group by user/warehouse
    - "Is my warehouse sized correctly?" → Utilization + queue time analysis
    - "Why is this query slow?" → Explain plan + resource metrics

    Handles queries related to:
    - Query performance and optimization
    - Cluster utilization metrics
    - Warehouse efficiency
    - Latency analysis
    - Cache hit rates
    - Resource right-sizing

    Genie Space: Performance Analyzer
    TVFs: 10 performance-related functions
    Metric Views: query_performance, cluster_utilization, cluster_efficiency
    ML Models: Query optimizer, cache predictor, latency forecaster
    """

    # TODO: Replace with actual Genie Space ID
    GENIE_SPACE_ID_PLACEHOLDER = "PERFORMANCE_GENIE_SPACE_ID"

    def __init__(self, genie_space_id: str = None):
        """
        Initialize Performance Worker Agent.
        
        TRAINING MATERIAL: Settings Delegation Pattern
        ===============================================
        
        The genie_space_id lookup chain:
        1. Explicit parameter (for testing)
        2. settings.performance_genie_space_id (which delegates to genie_spaces.py)
        3. Environment variable GENIE_SPACE_PERFORMANCE (checked by genie_spaces.py)
        
        This chain allows:
        - Testing with mock Space IDs
        - Dev/Prod with different Space IDs
        - Environment-based configuration
        """
        super().__init__(
            domain="performance",
            genie_space_id=genie_space_id or settings.performance_genie_space_id,
        )

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with performance-specific context.

        Adds:
        - Latency thresholds
        - Specific warehouse/cluster focus
        - Optimization hints
        """
        enhanced = query
        prefs = context.get("preferences", {})

        # Add latency threshold
        if prefs.get("latency_threshold_seconds"):
            threshold = prefs["latency_threshold_seconds"]
            enhanced += f" Flag queries exceeding {threshold} seconds."

        # Add warehouse focus
        if prefs.get("preferred_warehouse"):
            warehouse = prefs["preferred_warehouse"]
            enhanced += f" Focus on warehouse: {warehouse}."

        # Add cluster focus
        if prefs.get("preferred_cluster"):
            cluster = prefs["preferred_cluster"]
            enhanced += f" Focus on cluster: {cluster}."

        # Add workspace filter
        if prefs.get("preferred_workspace"):
            enhanced += f" Focus on workspace: {prefs['preferred_workspace']}."

        return enhanced

    def get_example_queries(self) -> list[str]:
        """Return example queries this agent handles."""
        return [
            "What are the slowest queries today?",
            "Show cluster CPU utilization trends",
            "Which warehouses have low cache hit rates?",
            "Recommend cluster right-sizing",
            "Show query latency percentiles",
            "What queries would benefit from caching?",
            "Compare warehouse performance week over week",
        ]
