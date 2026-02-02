"""
Configuration helpers for the Genie Space Optimizer.

Provides:
- Genie Space IDs mapping
- Environment variable loading
- Configuration validation
- Default settings
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Genie Space IDs (from databricks.yml)
GENIE_SPACES = {
    "cost": {
        "id": "01f0f1a3c2dc1c8897de11d27ca2cb6f",
        "name": "Health Monitor Cost Intelligence Space",
        "description": "Cost analytics and FinOps",
        "emoji": "💰",
    },
    "reliability": {
        "id": "01f0f1a3c33b19848c856518eac91dee",
        "name": "Health Monitor Job Reliability Space",
        "description": "Job reliability tracking",
        "emoji": "🔄",
    },
    "quality": {
        "id": "01f0f1a3c39517ffbe190f38956d8dd1",
        "name": "Health Monitor Data Quality Space",
        "description": "Data freshness and lineage",
        "emoji": "✅",
    },
    "performance": {
        "id": "01f0f1a3c3e31a8e8e6dee3eddf5d61f",
        "name": "Health Monitor Performance Space",
        "description": "Query and cluster performance",
        "emoji": "⚡",
    },
    "security": {
        "id": "01f0f1a3c44117acada010638189392f",
        "name": "Health Monitor Security Auditor Space",
        "description": "Security audit and compliance",
        "emoji": "🔒",
    },
    "unified": {
        "id": "01f0f1a3c4981080b61e224ecd465817",
        "name": "Databricks Health Monitor Space",
        "description": "All domains combined",
        "emoji": "🌐",
    },
}


@dataclass
class OptimizerConfig:
    """
    Configuration for the Genie Space Optimizer.
    
    Attributes:
        workspace_url: Databricks workspace URL
        token: Databricks API token
        catalog: Unity Catalog name
        gold_schema: Gold layer schema name
        rate_limit_seconds: Minimum seconds between API calls
        timeout_seconds: API request timeout
        max_retries: Maximum retries for failed requests
        test_cases_path: Path to golden queries YAML
        scratchpad_path: Path to scratchpad directory
    """
    workspace_url: str
    token: str
    catalog: str = "prashanth_subrahmanyam_catalog"
    gold_schema: str = "system_gold"
    rate_limit_seconds: float = 12.0  # 5 POST/min = 12 seconds between calls
    timeout_seconds: int = 300  # 5 minutes for long queries
    max_retries: int = 3
    poll_interval_seconds: float = 2.0  # Poll for completion every 2 seconds
    test_cases_path: Path = field(default_factory=lambda: Path("tests/optimizer/genie_golden_queries.yml"))
    scratchpad_path: Path = field(default_factory=lambda: Path("scratchpad"))
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.workspace_url:
            raise ValueError("workspace_url is required")
        if not self.token:
            raise ValueError("token is required")
        
        # Ensure workspace URL doesn't have trailing slash
        self.workspace_url = self.workspace_url.rstrip("/")
        
        # Convert string paths to Path objects
        if isinstance(self.test_cases_path, str):
            self.test_cases_path = Path(self.test_cases_path)
        if isinstance(self.scratchpad_path, str):
            self.scratchpad_path = Path(self.scratchpad_path)
    
    @property
    def state_file(self) -> Path:
        """Path to optimizer state file."""
        return self.scratchpad_path / "optimizer_state.json"
    
    @property
    def change_log_file(self) -> Path:
        """Path to change log file."""
        return self.scratchpad_path / "change_log.md"


def load_config(
    workspace_url: Optional[str] = None,
    token: Optional[str] = None,
    catalog: Optional[str] = None,
    gold_schema: Optional[str] = None,
) -> OptimizerConfig:
    """
    Load optimizer configuration from environment or provided values.
    
    Environment variables:
    - DATABRICKS_HOST: Workspace URL
    - DATABRICKS_TOKEN: API token
    - DATABRICKS_CATALOG: Unity Catalog name
    - DATABRICKS_GOLD_SCHEMA: Gold schema name
    
    Args:
        workspace_url: Override workspace URL
        token: Override API token
        catalog: Override catalog name
        gold_schema: Override gold schema name
        
    Returns:
        OptimizerConfig with loaded values
        
    Raises:
        ValueError: If required values are missing
    """
    config = OptimizerConfig(
        workspace_url=workspace_url or os.environ.get("DATABRICKS_HOST", ""),
        token=token or os.environ.get("DATABRICKS_TOKEN", ""),
        catalog=catalog or os.environ.get("DATABRICKS_CATALOG", "prashanth_subrahmanyam_catalog"),
        gold_schema=gold_schema or os.environ.get("DATABRICKS_GOLD_SCHEMA", "system_gold"),
    )
    
    return config


def get_space_id(domain: str) -> str:
    """
    Get Genie Space ID for a domain.
    
    Args:
        domain: Domain name (cost, reliability, etc.)
        
    Returns:
        Genie Space ID
        
    Raises:
        KeyError: If domain not found
    """
    if domain not in GENIE_SPACES:
        valid_domains = list(GENIE_SPACES.keys())
        raise KeyError(f"Unknown domain '{domain}'. Valid domains: {valid_domains}")
    return GENIE_SPACES[domain]["id"]


def get_space_info(domain: str) -> dict:
    """
    Get full Genie Space info for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        Dictionary with id, name, description, emoji
    """
    if domain not in GENIE_SPACES:
        valid_domains = list(GENIE_SPACES.keys())
        raise KeyError(f"Unknown domain '{domain}'. Valid domains: {valid_domains}")
    return GENIE_SPACES[domain]


def list_domains() -> list[str]:
    """List all available domains."""
    return list(GENIE_SPACES.keys())


def print_spaces_summary():
    """Print a formatted summary of all Genie Spaces."""
    print("\n" + "=" * 70)
    print("GENIE SPACES SUMMARY")
    print("=" * 70)
    
    for domain, info in GENIE_SPACES.items():
        print(f"\n{info['emoji']} {domain.upper()}")
        print(f"   Name: {info['name']}")
        print(f"   ID:   {info['id']}")
        print(f"   Desc: {info['description']}")
    
    print("\n" + "=" * 70)
