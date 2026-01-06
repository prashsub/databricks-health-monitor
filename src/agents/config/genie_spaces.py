"""
Genie Space Configuration
=========================

Centralized configuration for all Genie Space IDs used by the agent framework.
This file serves as the single source of truth for Genie Space mappings.

To update Genie Space IDs:
1. Update the DEFAULT_GENIE_SPACES dict below
2. Redeploy the agent
   
Environment variables override defaults (for per-environment config):
    export COST_GENIE_SPACE_ID="new-space-id"

Usage:
    from agents.config.genie_spaces import get_genie_space_id, GENIE_SPACES
    
    cost_space = get_genie_space_id("cost")
    all_spaces = GENIE_SPACES
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class GenieSpaceConfig:
    """Configuration for a single Genie Space."""
    space_id: str
    name: str
    domain: str
    description: str
    env_var: str
    
    def get_id(self) -> str:
        """Get space ID, with environment variable override."""
        return os.environ.get(self.env_var, self.space_id)


# =============================================================================
# GENIE SPACE CONFIGURATION
# =============================================================================
# Update these IDs when Genie Spaces are redeployed or migrated.
# Environment variables can override these defaults.
# =============================================================================

DEFAULT_GENIE_SPACES: Dict[str, GenieSpaceConfig] = {
    "cost": GenieSpaceConfig(
        space_id="01f0ea871ffe176fa6aee6f895f83d3b",
        name="Cost Intelligence Space",
        domain="cost",
        description="Billing, DBU usage, budgets, cost optimization, chargeback",
        env_var="COST_GENIE_SPACE_ID",
    ),
    "reliability": GenieSpaceConfig(
        space_id="01f0ea8724fd160e8e959b8a5af1a8c5",
        name="Job Reliability Space",
        domain="reliability",
        description="Job failures, SLA compliance, pipeline health, task success",
        env_var="RELIABILITY_GENIE_SPACE_ID",
    ),
    "quality": GenieSpaceConfig(
        space_id="01f0ea93616c1978a99a59d3f2e805bd",
        name="Data Quality Space",
        domain="quality",
        description="Data freshness, schema changes, lineage, governance",
        env_var="QUALITY_GENIE_SPACE_ID",
    ),
    "performance": GenieSpaceConfig(
        space_id="01f0ea93671e12d490224183f349dba0",
        name="Performance Space",
        domain="performance",
        description="Query speed, cluster utilization, warehouse efficiency",
        env_var="PERFORMANCE_GENIE_SPACE_ID",
    ),
    "security": GenieSpaceConfig(
        space_id="01f0ea9367f214d6a4821605432234c4",
        name="Security Auditor Space",
        domain="security",
        description="Access control, audit logs, permissions, compliance",
        env_var="SECURITY_GENIE_SPACE_ID",
    ),
    "unified": GenieSpaceConfig(
        space_id="01f0ea9368801e019e681aa3abaa0089",
        name="Overall Health Monitor Space",
        domain="unified",
        description="Cross-domain analytics, holistic platform health view",
        env_var="UNIFIED_GENIE_SPACE_ID",
    ),
}

# Convenience dict for quick access
GENIE_SPACES: Dict[str, str] = {
    domain: config.get_id() 
    for domain, config in DEFAULT_GENIE_SPACES.items()
}


def get_genie_space_id(domain: str) -> Optional[str]:
    """
    Get Genie Space ID for a domain.
    
    Args:
        domain: Domain name (cost, security, performance, reliability, quality, unified)
        
    Returns:
        Genie Space ID or None if domain not found.
        
    Example:
        cost_space_id = get_genie_space_id("cost")
    """
    domain_lower = domain.lower()
    if domain_lower in DEFAULT_GENIE_SPACES:
        return DEFAULT_GENIE_SPACES[domain_lower].get_id()
    return None


def get_genie_space_config(domain: str) -> Optional[GenieSpaceConfig]:
    """
    Get full Genie Space configuration for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        GenieSpaceConfig or None if domain not found.
    """
    return DEFAULT_GENIE_SPACES.get(domain.lower())


def get_all_configured_spaces() -> Dict[str, str]:
    """
    Get all Genie Spaces that have valid IDs configured.
    
    Returns:
        Dict of domain -> space_id for all configured spaces.
    """
    return {
        domain: config.get_id()
        for domain, config in DEFAULT_GENIE_SPACES.items()
        if config.get_id()
    }


def validate_genie_spaces() -> Dict[str, bool]:
    """
    Validate which Genie Spaces are properly configured.
    
    Returns:
        Dict of domain -> is_configured boolean.
    """
    return {
        domain: bool(config.get_id())
        for domain, config in DEFAULT_GENIE_SPACES.items()
    }


def print_genie_space_summary():
    """Print summary of Genie Space configuration."""
    print("=" * 70)
    print("GENIE SPACE CONFIGURATION")
    print("=" * 70)
    
    for domain, config in DEFAULT_GENIE_SPACES.items():
        space_id = config.get_id()
        override = os.environ.get(config.env_var)
        status = "✓ Configured" if space_id else "✗ Not configured"
        source = "(env)" if override else "(default)"
        
        print(f"\n{config.name}")
        print(f"  Domain: {domain}")
        print(f"  ID: {space_id or 'None'} {source}")
        print(f"  Status: {status}")
        print(f"  Env var: {config.env_var}")
    
    print("\n" + "=" * 70)


# Export for convenience
__all__ = [
    "GENIE_SPACES",
    "DEFAULT_GENIE_SPACES",
    "GenieSpaceConfig",
    "get_genie_space_id",
    "get_genie_space_config",
    "get_all_configured_spaces",
    "validate_genie_spaces",
    "print_genie_space_summary",
]

