"""
Databricks Health Monitor Agent Framework
=========================================

Multi-agent system for Databricks platform observability using:
- LangGraph orchestrator for multi-agent coordination
- Genie Spaces as the sole data interface
- Lakebase for short-term and long-term memory
- MLflow 3.0 for tracing, evaluation, and prompt registry

Architecture:
    User Query -> Orchestrator -> Intent Classification -> Worker Agents -> Genie Spaces -> Response

Best Practices Implemented:
1. MLflow autolog enabled at module level
2. Span types for all traced operations
3. ChatAgent interface for model serving
4. Prompt registry with versioning
5. Lakebase memory with CheckpointSaver (short-term) and DatabricksStore (long-term)
"""

import mlflow

# CRITICAL: Enable autolog at module level per MLflow GenAI patterns
# This must be at the TOP of the module before any LangChain imports
# Note: Using minimal parameters for compatibility with current MLflow version
try:
    mlflow.langchain.autolog()
except Exception as e:
    print(f"⚠ MLflow autolog not available: {e}")

# Set default experiment for agent traces
EXPERIMENT_NAME = "/Shared/health_monitor/agent_traces"
try:
    mlflow.set_experiment(EXPERIMENT_NAME)
except Exception:
    # Experiment creation may fail in some contexts; proceed anyway
    pass

from .config.settings import settings

# Lazy imports to avoid cascading dependency issues
# Import HealthMonitorAgent only when needed
__all__ = [
    "settings",
    "EXPERIMENT_NAME",
]

def get_agent():
    """Get HealthMonitorAgent with lazy import to avoid dependency issues."""
    from .orchestrator.agent import HealthMonitorAgent
    return HealthMonitorAgent

__version__ = "1.0.0"
