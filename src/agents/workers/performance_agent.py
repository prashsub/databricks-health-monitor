"""
Performance Worker Agent
========================

Domain specialist for query and cluster performance optimization.
"""

from typing import Dict

from .base import GenieWorkerAgent
from ..config import settings


class PerformanceWorkerAgent(GenieWorkerAgent):
    """
    Performance domain worker agent.

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
        """Initialize Performance Worker Agent."""
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
