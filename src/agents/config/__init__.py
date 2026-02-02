"""
TRAINING MATERIAL: Agent Configuration Module Architecture
===========================================================

This module provides centralized configuration for the agent framework.
It separates configuration from code for maintainability and flexibility.

CONFIGURATION ARCHITECTURE:
---------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION COMPONENTS                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  AgentSettings (settings.py)                                     │   │
│  │  ───────────────────────────────────────────────────────────────│   │
│  │  Environment-aware settings:                                     │   │
│  │  - catalog, gold_schema, feature_schema                          │   │
│  │  - llm_endpoint (Foundation Model endpoint)                      │   │
│  │  - workspace_url, warehouse_id                                   │   │
│  │  - memory_catalog, memory_schema (Lakebase)                      │   │
│  │  Uses Pydantic for validation and env var loading.               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  GENIE_SPACES (genie_spaces.py)                                  │   │
│  │  ───────────────────────────────────────────────────────────────│   │
│  │  Registry of Genie Space configurations:                         │   │
│  │  - Space IDs per domain (cost, security, etc.)                   │   │
│  │  - Space metadata (name, description)                            │   │
│  │  - Utility functions for lookup and validation                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

WHY CENTRALIZED CONFIGURATION:
------------------------------

1. SINGLE SOURCE OF TRUTH
   - All agents use the same settings
   - No hardcoded values scattered across codebase
   - Easy to update for different environments

2. ENVIRONMENT FLEXIBILITY
   - Development: Different catalog, test Genie spaces
   - Production: Production catalog, real Genie spaces
   - Configuration via environment variables

3. VALIDATION AT STARTUP
   - Pydantic validates all required settings
   - Fails fast if misconfigured
   - Clear error messages

USAGE PATTERN:
--------------

    from agents.config import settings, GENIE_SPACES
    
    # Access global settings
    print(settings.catalog)  # e.g., "health_monitor"
    print(settings.llm_endpoint)  # e.g., "databricks-meta-llama-3-1-70b-instruct"
    
    # Get Genie Space ID for a domain
    from agents.config import get_genie_space_id
    cost_space_id = get_genie_space_id("cost")

Agent configuration module.
"""

from .settings import settings, AgentSettings
from .genie_spaces import (
    GENIE_SPACES,
    get_genie_space_id,
    get_genie_space_config,
    get_all_configured_spaces,
    validate_genie_spaces,
)

__all__ = [
    "settings",
    "AgentSettings",
    "GENIE_SPACES",
    "get_genie_space_id",
    "get_genie_space_config",
    "get_all_configured_spaces",
    "validate_genie_spaces",
]
