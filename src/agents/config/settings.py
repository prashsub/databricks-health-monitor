"""
Agent Configuration Settings
============================

Centralized configuration for the Health Monitor Agent Framework.
All settings can be overridden via environment variables.

Usage:
    from agents.config import settings

    llm_endpoint = settings.llm_endpoint
    cost_genie_id = settings.cost_genie_space_id
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentSettings:
    """Configuration settings for the agent framework."""

    # =========================================================================
    # Databricks Connection
    # =========================================================================
    databricks_host: str = field(
        default_factory=lambda: os.environ.get("DATABRICKS_HOST", "")
    )

    # =========================================================================
    # LLM Configuration
    # =========================================================================
    llm_endpoint: str = field(
        default_factory=lambda: os.environ.get("LLM_ENDPOINT", "databricks-claude-3-7-sonnet")
    )
    llm_temperature: float = field(
        default_factory=lambda: float(os.environ.get("LLM_TEMPERATURE", "0.3"))
    )

    # Embedding model for long-term memory vector search
    embedding_endpoint: str = field(
        default_factory=lambda: os.environ.get("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
    )
    embedding_dims: int = field(
        default_factory=lambda: int(os.environ.get("EMBEDDING_DIMS", "1024"))
    )

    # =========================================================================
    # Genie Space IDs (from Phase 3.6 deployment)
    # =========================================================================
    cost_genie_space_id: str = field(
        default_factory=lambda: os.environ.get("COST_GENIE_SPACE_ID", "")
    )
    security_genie_space_id: str = field(
        default_factory=lambda: os.environ.get("SECURITY_GENIE_SPACE_ID", "")
    )
    performance_genie_space_id: str = field(
        default_factory=lambda: os.environ.get("PERFORMANCE_GENIE_SPACE_ID", "")
    )
    reliability_genie_space_id: str = field(
        default_factory=lambda: os.environ.get("RELIABILITY_GENIE_SPACE_ID", "")
    )
    quality_genie_space_id: str = field(
        default_factory=lambda: os.environ.get("QUALITY_GENIE_SPACE_ID", "")
    )
    unified_genie_space_id: str = field(
        default_factory=lambda: os.environ.get("UNIFIED_GENIE_SPACE_ID", "")
    )

    # =========================================================================
    # Lakebase Memory Configuration
    # =========================================================================
    lakebase_instance_name: str = field(
        default_factory=lambda: os.environ.get("LAKEBASE_INSTANCE_NAME", "health_monitor_memory")
    )

    # Short-term memory (conversation context)
    short_term_memory_ttl_hours: int = field(
        default_factory=lambda: int(os.environ.get("SHORT_TERM_MEMORY_TTL_HOURS", "24"))
    )

    # Long-term memory (user preferences, insights)
    long_term_memory_ttl_days: int = field(
        default_factory=lambda: int(os.environ.get("LONG_TERM_MEMORY_TTL_DAYS", "365"))
    )

    # =========================================================================
    # Unity Catalog Configuration
    # =========================================================================
    catalog: str = field(
        default_factory=lambda: os.environ.get("CATALOG", "health_monitor")
    )
    schema: str = field(
        default_factory=lambda: os.environ.get("SCHEMA", "agents")
    )

    # =========================================================================
    # Timeouts
    # =========================================================================
    genie_timeout_seconds: int = field(
        default_factory=lambda: int(os.environ.get("GENIE_TIMEOUT_SECONDS", "45"))
    )
    agent_timeout_seconds: int = field(
        default_factory=lambda: int(os.environ.get("AGENT_TIMEOUT_SECONDS", "30"))
    )

    # =========================================================================
    # Utility Tools Configuration
    # =========================================================================
    tavily_api_key: str = field(
        default_factory=lambda: os.environ.get("TAVILY_API_KEY", "")
    )
    vector_search_endpoint: str = field(
        default_factory=lambda: os.environ.get("VECTOR_SEARCH_ENDPOINT", "")
    )

    # =========================================================================
    # Model Serving Configuration
    # =========================================================================
    model_serving_endpoint_name: str = field(
        default_factory=lambda: os.environ.get(
            "MODEL_SERVING_ENDPOINT_NAME",
            "health_monitor_orchestrator"
        )
    )

    # =========================================================================
    # Feature Flags
    # =========================================================================
    enable_long_term_memory: bool = field(
        default_factory=lambda: os.environ.get("ENABLE_LONG_TERM_MEMORY", "true").lower() == "true"
    )
    enable_web_search: bool = field(
        default_factory=lambda: os.environ.get("ENABLE_WEB_SEARCH", "true").lower() == "true"
    )
    enable_mlflow_tracing: bool = field(
        default_factory=lambda: os.environ.get("ENABLE_MLFLOW_TRACING", "true").lower() == "true"
    )

    def get_genie_space_id(self, domain: str) -> Optional[str]:
        """Get Genie Space ID for a domain."""
        mapping = {
            "cost": self.cost_genie_space_id,
            "security": self.security_genie_space_id,
            "performance": self.performance_genie_space_id,
            "reliability": self.reliability_genie_space_id,
            "quality": self.quality_genie_space_id,
            "unified": self.unified_genie_space_id,
        }
        return mapping.get(domain.lower())

    def validate(self) -> list[str]:
        """Validate required settings are configured."""
        errors = []

        if not self.databricks_host:
            errors.append("DATABRICKS_HOST is not set")

        if not self.lakebase_instance_name:
            errors.append("LAKEBASE_INSTANCE_NAME is not set")

        # Check at least one Genie Space is configured
        genie_spaces = [
            self.cost_genie_space_id,
            self.security_genie_space_id,
            self.performance_genie_space_id,
            self.reliability_genie_space_id,
            self.quality_genie_space_id,
        ]
        if not any(genie_spaces):
            errors.append("At least one GENIE_SPACE_ID must be configured")

        return errors


# Global settings instance
settings = AgentSettings()
