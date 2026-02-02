"""
TRAINING MATERIAL: Domain Worker Agent Architecture
===================================================

This module implements the domain-specific worker agents that serve
as the interface between the orchestrator and Genie Spaces.

WORKER AGENT DATA FLOW:
-----------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR                                                            │
│      │                                                                   │
│      │ "What's our daily DBU spend?"                                    │
│      │ → Classified as COST domain                                      │
│      ▼                                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  CostWorkerAgent                                                   │  │
│  │  ─────────────────                                                 │  │
│  │  1. Enhance query with domain context                              │  │
│  │     "For the Cost Genie Space: What's our daily DBU spend?"       │  │
│  │                                                                    │  │
│  │  2. Query Genie Space via GenieAgent                               │  │
│  │     genie_agent.query(enhanced_query)                              │  │
│  │                                                                    │  │
│  │  3. Format response for synthesis                                  │  │
│  │     {"domain": "cost", "findings": [...], "confidence": 0.9}      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│      │                                                                   │
│      ▼                                                                   │
│  COST GENIE SPACE                                                        │
│  (TVFs, Metric Views, ML Predictions)                                   │
└─────────────────────────────────────────────────────────────────────────┘

GENIE-ONLY DATA ACCESS:
-----------------------

CRITICAL DESIGN DECISION: Workers NEVER query data directly!

    ❌ WRONG: spark.sql("SELECT * FROM fact_usage")
    ❌ WRONG: call_tvf("get_daily_cost_summary", params)
    ❌ WRONG: query_metric_view("cost_analytics_metrics")
    
    ✅ RIGHT: genie_agent.query("What's our daily DBU spend?")

Why?
1. Genie has semantic understanding of natural language
2. Genie knows which TVF/MV/table to use
3. Genie handles SQL generation and execution
4. Single interface for all data access

LAZY INITIALIZATION:
--------------------

Workers are lazily initialized to avoid import overhead:

    def get_worker_agent(domain: str) -> BaseWorkerAgent:
        if domain not in _WORKER_AGENTS:
            _WORKER_AGENTS[domain] = agent_classes[domain]()
        return _WORKER_AGENTS.get(domain)

First call creates the agent; subsequent calls return cached instance.

The agents NEVER query TVFs, Metric Views, or ML tables directly.
All data access flows through Genie Spaces.
"""

from typing import Optional, Dict

from .base import BaseWorkerAgent, GenieWorkerAgent
from .cost_agent import CostWorkerAgent
from .security_agent import SecurityWorkerAgent
from .performance_agent import PerformanceWorkerAgent
from .reliability_agent import ReliabilityWorkerAgent
from .quality_agent import QualityWorkerAgent


# Worker agent registry
_WORKER_AGENTS: Dict[str, BaseWorkerAgent] = {}


def get_worker_agent(domain: str) -> Optional[BaseWorkerAgent]:
    """
    Get a worker agent by domain name.

    Args:
        domain: Domain name (cost, security, performance, reliability, quality)

    Returns:
        Worker agent instance or None if not configured.
    """
    domain_lower = domain.lower()

    # Lazy initialization
    if domain_lower not in _WORKER_AGENTS:
        agent_classes = {
            "cost": CostWorkerAgent,
            "security": SecurityWorkerAgent,
            "performance": PerformanceWorkerAgent,
            "reliability": ReliabilityWorkerAgent,
            "quality": QualityWorkerAgent,
        }

        if domain_lower in agent_classes:
            _WORKER_AGENTS[domain_lower] = agent_classes[domain_lower]()

    return _WORKER_AGENTS.get(domain_lower)


def list_available_workers() -> list[str]:
    """List all available worker domains."""
    return ["cost", "security", "performance", "reliability", "quality"]


__all__ = [
    "BaseWorkerAgent",
    "GenieWorkerAgent",
    "CostWorkerAgent",
    "SecurityWorkerAgent",
    "PerformanceWorkerAgent",
    "ReliabilityWorkerAgent",
    "QualityWorkerAgent",
    "get_worker_agent",
    "list_available_workers",
]
