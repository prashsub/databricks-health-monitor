"""
TRAINING MATERIAL: Agent Framework Package Architecture
=======================================================

This is the root package for the Databricks Health Monitor Agent,
implementing a multi-agent system with production best practices.

AGENT ARCHITECTURE OVERVIEW:
----------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                        │
│                            │                                            │
│                            ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     ORCHESTRATOR (LangGraph)                      │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │  Intent Classification → Route to Domain                    │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                            │                                            │
│       ┌────────────────────┼────────────────────┐                      │
│       ▼                    ▼                    ▼                      │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐                  │
│  │  Cost   │         │Security │         │Perform  │  ... 5 domains   │
│  │  Agent  │         │ Agent   │         │ Agent   │                  │
│  └────┬────┘         └────┬────┘         └────┬────┘                  │
│       │                   │                   │                        │
│       └───────────────────┴───────────────────┘                        │
│                            │                                            │
│                            ▼                                            │
│                    GENIE SPACES (Data)                                  │
│                            │                                            │
│                            ▼                                            │
│               RESPONSE SYNTHESIS + MEMORY                               │
└─────────────────────────────────────────────────────────────────────────┘

KEY PRODUCTION PATTERNS:
------------------------

1. MLflow autolog at module level (not function level)
2. ChatAgent interface for Model Serving compatibility
3. Lakebase memory (short-term + long-term)
4. Span types for tracing (AGENT, CHAIN, TOOL, RETRIEVER)
5. Prompt registry with versioning

MODULE-LEVEL AUTOLOG:
---------------------

    import mlflow
    mlflow.langchain.autolog()  # BEFORE any LangChain imports!

This must be at the TOP of the module, before any LangChain imports,
to ensure all LangChain operations are automatically traced.

EXPERIMENT ORGANIZATION:
------------------------

Three experiments for clean separation:
- /Shared/health_monitor_agent_development - Dev/iteration runs
- /Shared/health_monitor_agent_evaluation - Formal evaluation
- /Shared/health_monitor_agent_deployment - Production deployment logs

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

# Import settings first to get consolidated experiment path
from .config.settings import settings

# CRITICAL: Enable autolog at module level per MLflow GenAI patterns
# This must be at the TOP of the module before any LangChain imports
# Note: Using minimal parameters for compatibility with current MLflow version
try:
    mlflow.langchain.autolog()
except Exception as e:
    print(f"⚠ MLflow autolog not available: {e}")

# MLflow Experiment Structure (Organized by Purpose)
# Three separate experiments for clean organization:
EXPERIMENT_DEVELOPMENT = "/Shared/health_monitor_agent_development"
EXPERIMENT_EVALUATION = "/Shared/health_monitor_agent_evaluation"
EXPERIMENT_DEPLOYMENT = "/Shared/health_monitor_agent_deployment"

# Default to evaluation (most common use case for imports)
EXPERIMENT_NAME = EXPERIMENT_EVALUATION
try:
    mlflow.set_experiment(EXPERIMENT_NAME)
except Exception:
    # Experiment creation may fail in some contexts; proceed anyway
    pass

# Lazy imports to avoid cascading dependency issues
# Import HealthMonitorAgent only when needed
__all__ = [
    "settings",
    "EXPERIMENT_NAME",
    "EXPERIMENT_DEVELOPMENT",
    "EXPERIMENT_EVALUATION",
    "EXPERIMENT_DEPLOYMENT",
]

def get_agent():
    """Get HealthMonitorAgent with lazy import to avoid dependency issues."""
    from .orchestrator.agent import HealthMonitorAgent
    return HealthMonitorAgent

__version__ = "1.0.0"
