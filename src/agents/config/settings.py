"""
Agent Configuration Settings
============================

Centralized configuration for the Health Monitor Agent Framework.
All settings can be overridden via environment variables.

IMPORTANT: Genie Space configuration is defined in genie_spaces.py (single source of truth).
This file imports from there to avoid duplication.

Usage:
    from agents.config import settings

    llm_endpoint = settings.llm_endpoint
    cost_genie_id = settings.cost_genie_space_id  # Delegates to genie_spaces.py
"""

import os
from dataclasses import dataclass, field
from typing import Optional

# Import Genie Space configuration from single source of truth
from .genie_spaces import (
    GENIE_SPACE_REGISTRY,
    DOMAINS,
    get_genie_space_id as _get_genie_space_id,
    get_genie_space_config as _get_genie_space_config,
)


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
        default_factory=lambda: os.environ.get("LLM_ENDPOINT", "databricks-claude-sonnet-4-5")
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
    # Genie Space IDs (DELEGATED to genie_spaces.py - Single Source of Truth)
    # =========================================================================
    # DO NOT hardcode IDs here! They are managed in genie_spaces.py
    # These properties delegate to the central registry for consistency.
    # Environment variable overrides still work via genie_spaces.py
    # =========================================================================
    @property
    def cost_genie_space_id(self) -> str:
        """Cost Intelligence Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.COST) or ""
    
    @property
    def security_genie_space_id(self) -> str:
        """Security Auditor Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.SECURITY) or ""
    
    @property
    def performance_genie_space_id(self) -> str:
        """Performance Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.PERFORMANCE) or ""
    
    @property
    def reliability_genie_space_id(self) -> str:
        """Job Reliability Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.RELIABILITY) or ""
    
    @property
    def quality_genie_space_id(self) -> str:
        """Data Quality Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.QUALITY) or ""
    
    @property
    def unified_genie_space_id(self) -> str:
        """Overall Health Monitor Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.UNIFIED) or ""

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
    # MLflow Experiment Configuration (CONSOLIDATED)
    # =========================================================================
    # All agent-related MLflow runs go to a SINGLE experiment.
    # Use run tags to differentiate purpose (model_logging, evaluation, etc.)
    # This simplifies tracking and provides a single location for all agent runs.
    # =========================================================================
    mlflow_experiment_path: str = field(
        default_factory=lambda: os.environ.get(
            "MLFLOW_EXPERIMENT_PATH", 
            "/Shared/health_monitor/agent"
        )
    )

    # Run type tags for differentiation within the unified experiment
    # These are used as mlflow.set_tag("run_type", <value>)
    RUN_TYPE_MODEL_LOGGING: str = "model_logging"
    RUN_TYPE_EVALUATION: str = "evaluation"
    RUN_TYPE_DEPLOYMENT: str = "deployment"
    RUN_TYPE_PROMPTS: str = "prompt_registry"
    RUN_TYPE_TRACES: str = "traces"
    RUN_TYPE_MONITORING: str = "production_monitoring"

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
        """
        Get Genie Space ID for a domain.
        
        Delegates to genie_spaces.py (single source of truth).
        """
        return _get_genie_space_id(domain)
    
    def get_genie_space_config(self, domain: str):
        """
        Get full Genie Space configuration including agent instructions.
        
        Delegates to genie_spaces.py (single source of truth).
        
        Returns:
            GenieSpaceConfig with name, description, agent_instructions, etc.
        """
        return _get_genie_space_config(domain)

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
