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
    # These IDs are configurable via environment variables for flexibility.
    # Default values are the deployed Genie Space IDs from the project.
    # To override: export COST_GENIE_SPACE_ID="your-space-id"
    # =========================================================================
    cost_genie_space_id: str = field(
        default_factory=lambda: os.environ.get(
            "COST_GENIE_SPACE_ID", 
            "01f0ea871ffe176fa6aee6f895f83d3b"  # Cost Intelligence Space
        )
    )
    security_genie_space_id: str = field(
        default_factory=lambda: os.environ.get(
            "SECURITY_GENIE_SPACE_ID", 
            "01f0ea9367f214d6a4821605432234c4"  # Security Auditor Space
        )
    )
    performance_genie_space_id: str = field(
        default_factory=lambda: os.environ.get(
            "PERFORMANCE_GENIE_SPACE_ID", 
            "01f0ea93671e12d490224183f349dba0"  # Performance Space
        )
    )
    reliability_genie_space_id: str = field(
        default_factory=lambda: os.environ.get(
            "RELIABILITY_GENIE_SPACE_ID", 
            "01f0ea8724fd160e8e959b8a5af1a8c5"  # Job Reliability Space
        )
    )
    quality_genie_space_id: str = field(
        default_factory=lambda: os.environ.get(
            "QUALITY_GENIE_SPACE_ID", 
            "01f0ea93616c1978a99a59d3f2e805bd"  # Data Quality Space
        )
    )
    unified_genie_space_id: str = field(
        default_factory=lambda: os.environ.get(
            "UNIFIED_GENIE_SPACE_ID", 
            "01f0ea9368801e019e681aa3abaa0089"  # Overall Health Monitor Space
        )
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
    # Follows project convention: catalog.schema pattern
    # Dev: prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent
    # Prod: main.system_gold_agent
    #
    # CONSOLIDATED STORAGE (single schema to avoid sprawl):
    #   - MODELS: health_monitor_agent
    #   - TABLES (Structured):
    #       - Config: agent_config
    #       - Evaluation: evaluation_datasets, evaluation_results
    #       - Experimentation: ab_test_assignments
    #       - Inference: inference_request_logs, inference_response_logs
    #       - Memory: memory_short_term, memory_long_term
    #   - VOLUMES (Unstructured):
    #       - runbooks/ (RAG knowledge base)
    #       - embeddings/ (vector embeddings)
    #       - artifacts/ (model checkpoints)
    # =========================================================================
    
    catalog: str = field(
        default_factory=lambda: os.environ.get("CATALOG", "prashanth_subrahmanyam_catalog")
    )
    
    # Single consolidated agent schema for all agent-related data
    agent_schema: str = field(
        default_factory=lambda: os.environ.get("AGENT_SCHEMA", "dev_prashanth_subrahmanyam_system_gold_agent")
    )
    
    # Deprecated: Now consolidated into agent_schema
    # Kept for backwards compatibility - maps to agent_schema
    @property
    def inference_schema(self) -> str:
        """Inference logs schema (now same as agent_schema)."""
        return self.agent_schema
    
    @property
    def memory_schema(self) -> str:
        """Memory tables schema (now same as agent_schema)."""
        return self.agent_schema
    
    # Legacy alias
    schema: str = field(
        default_factory=lambda: os.environ.get("SCHEMA", "dev_prashanth_subrahmanyam_system_gold_agent")
    )
    
    # =========================================================================
    # Helper Properties for Full Paths
    # =========================================================================
    @property
    def model_full_name(self) -> str:
        """Full UC path for the agent model."""
        return f"{self.catalog}.{self.agent_schema}.health_monitor_agent"
    
    @property
    def runbooks_volume_path(self) -> str:
        """Full UC path for the runbooks volume."""
        return f"/Volumes/{self.catalog}/{self.agent_schema}/runbooks"
    
    @property
    def embeddings_volume_path(self) -> str:
        """Full UC path for the embeddings volume."""
        return f"/Volumes/{self.catalog}/{self.agent_schema}/embeddings"
    
    # Table name helpers (with prefixes for organization within single schema)
    @property
    def inference_request_table(self) -> str:
        """Full path to inference request logs table."""
        return f"{self.catalog}.{self.agent_schema}.inference_request_logs"
    
    @property
    def inference_response_table(self) -> str:
        """Full path to inference response logs table."""
        return f"{self.catalog}.{self.agent_schema}.inference_response_logs"
    
    @property
    def memory_short_term_table(self) -> str:
        """Full path to short-term memory table."""
        return f"{self.catalog}.{self.agent_schema}.memory_short_term"
    
    @property
    def memory_long_term_table(self) -> str:
        """Full path to long-term memory table."""
        return f"{self.catalog}.{self.agent_schema}.memory_long_term"

    # =========================================================================
    # SQL Warehouse Configuration
    # =========================================================================
    warehouse_id: str = field(
        default_factory=lambda: os.environ.get("WAREHOUSE_ID", "4b9b953939869799")
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
