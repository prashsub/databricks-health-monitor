"""
Worker Agents Module
====================

Domain-specific worker agents that wrap Genie Spaces.

Each worker agent:
1. Receives queries from the orchestrator
2. Enhances the query with domain context
3. Queries the corresponding Genie Space
4. Formats the response for synthesis

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
