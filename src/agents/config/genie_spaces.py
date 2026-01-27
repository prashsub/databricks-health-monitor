"""
Genie Space Configuration
==========================

Centralized configuration for all Genie Space IDs and metadata used by the agent framework.

CONFIGURATION HIERARCHY (in order of precedence):
1. **Environment Variables** (highest priority) - Set via databricks.yml or runtime
   - COST_GENIE_SPACE_ID
   - RELIABILITY_GENIE_SPACE_ID
   - QUALITY_GENIE_SPACE_ID
   - PERFORMANCE_GENIE_SPACE_ID
   - SECURITY_GENIE_SPACE_ID
   - UNIFIED_GENIE_SPACE_ID

2. **Default Values** (fallback) - Hardcoded in GENIE_SPACE_REGISTRY below

RECOMMENDED APPROACH:
- Define Genie Space IDs in databricks.yml as variables
- Pass them as environment variables to agent deployment jobs
- Keep defaults here as fallback for development

Example databricks.yml:
    variables:
      cost_genie_space_id:
        default: "01f0ea871ffe176fa6aee6f895f83d3b"
    
    targets:
      prod:
        variables:
          cost_genie_space_id: "prod-space-id"  # Override for prod

Usage:
    from agents.config.genie_spaces import (
        get_genie_space_id, 
        get_genie_space_config,
        GENIE_SPACE_REGISTRY,
        DOMAINS
    )
    
    cost_space = get_genie_space_id("cost")  # Returns env var or default
    cost_config = get_genie_space_config("cost")
    print(cost_config.agent_instructions)  # When to use this space
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# =============================================================================
# DOMAIN CONSTANTS
# =============================================================================
class DOMAINS:
    """Domain constants for type safety."""
    COST = "cost"
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    QUALITY = "quality"
    UNIFIED = "unified"
    
    ALL = [COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY, UNIFIED]
    SPECIALIZED = [COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY]  # Excludes unified


@dataclass
class GenieSpaceConfig:
    """
    Configuration for a single Genie Space.
    
    This dataclass contains all metadata needed for:
    1. Agent routing - deciding which Genie Space to query
    2. Tool creation - generating LangChain tools with proper descriptions
    3. Environment configuration - allowing per-environment overrides
    """
    # Core identifiers
    space_id: str
    domain: str
    env_var: str
    
    # Human-readable metadata
    name: str
    short_description: str
    
    # Agent routing instructions (CRITICAL for multi-agent orchestration)
    agent_instructions: str
    
    # Example queries this space handles well
    example_queries: List[str] = field(default_factory=list)
    
    # Keywords that indicate this domain (for intent classification)
    routing_keywords: List[str] = field(default_factory=list)
    
    # Data assets available in this space
    data_assets: List[str] = field(default_factory=list)
    
    def get_id(self) -> str:
        """Get space ID, with environment variable override."""
        return os.environ.get(self.env_var, self.space_id)
    
    def get_tool_description(self) -> str:
        """
        Generate a comprehensive tool description for LangChain.
        This description helps the LLM decide when to use this tool.
        """
        return f"""{self.short_description}

WHEN TO USE THIS TOOL:
{self.agent_instructions}

EXAMPLE QUERIES:
{chr(10).join(f'- {q}' for q in self.example_queries[:5])}

KEYWORDS: {', '.join(self.routing_keywords[:10])}"""


# =============================================================================
# GENIE SPACE REGISTRY (SINGLE SOURCE OF TRUTH)
# =============================================================================
# This is the ONLY place where Genie Space configuration should be defined.
# Do NOT duplicate these IDs or descriptions in settings.py or elsewhere.
# =============================================================================

GENIE_SPACE_REGISTRY: Dict[str, GenieSpaceConfig] = {
    
    DOMAINS.COST: GenieSpaceConfig(
        space_id="01f0f1a3c2dc1c8897de11d27ca2cb6f",
        domain=DOMAINS.COST,
        env_var="COST_GENIE_SPACE_ID",
        name="Cost Intelligence Space",
        short_description="Analyze Databricks billing, DBU consumption, cost allocation, and spending optimization.",
        agent_instructions="""Use this tool for ANY question about:
- Billing, spending, or costs (yesterday, last week, month, etc.)
- DBU (Databricks Unit) consumption by SKU, workspace, or cluster
- Cost spikes, anomalies, or unexpected charges
- Budget tracking and forecasting
- Chargeback and cost allocation to teams/projects
- Serverless vs classic compute cost comparison
- Photon and warehouse spending
- Reserved capacity and commitment utilization
- Cost optimization recommendations

DO NOT use for: Job failures (use reliability), slow queries (use performance), 
data quality issues (use quality), or access control (use security).""",
        example_queries=[
            "Why did costs spike yesterday?",
            "What are the top 10 most expensive jobs?",
            "Show DBU usage by workspace for last 30 days",
            "Which teams are over budget this month?",
            "Compare serverless vs classic compute costs",
            "What's our daily spend trend?",
            "Show cost breakdown by SKU",
            "Which clusters are wasting money?",
        ],
        routing_keywords=[
            "cost", "spend", "spending", "budget", "dbu", "billing", "charge",
            "expensive", "price", "money", "dollar", "waste", "optimize",
            "chargeback", "allocation", "forecast", "commitment", "reserved",
            "sku", "photon", "serverless"
        ],
        data_assets=[
            "fact_usage - Daily usage and cost records",
            "fact_list_prices - SKU pricing information",
            "dim_workspace - Workspace metadata",
            "dim_sku - SKU details and categories",
        ],
    ),
    
    DOMAINS.RELIABILITY: GenieSpaceConfig(
        space_id="01f0f1a3c33b19848c856518eac91dee",
        domain=DOMAINS.RELIABILITY,
        env_var="RELIABILITY_GENIE_SPACE_ID",
        name="Job Reliability Space",
        short_description="Monitor job execution, failures, SLA compliance, and pipeline health.",
        agent_instructions="""Use this tool for ANY question about:
- Job or workflow failures, errors, and exceptions
- Job success rates and failure trends
- Pipeline health and task completion
- SLA compliance and breach monitoring
- Job run duration and timeout issues
- Task retries and retry patterns
- Scheduled job reliability
- DLT pipeline failures and data quality expectations
- Workflow orchestration issues
- Job queue times and delays

DO NOT use for: Cost analysis (use cost), slow query performance (use performance),
data freshness issues (use quality), or permission errors (use security).""",
        example_queries=[
            "Which jobs failed today?",
            "What is the success rate for production jobs?",
            "Show me failing pipelines",
            "Are we meeting our SLAs?",
            "Which jobs have the most retries?",
            "What's causing job failures this week?",
            "List long-running jobs that might timeout",
            "Show DLT pipeline health status",
        ],
        routing_keywords=[
            "fail", "failure", "failed", "error", "success", "sla", "pipeline",
            "job", "workflow", "task", "retry", "timeout", "exception",
            "crash", "abort", "terminate", "health", "status", "running",
            "dlt", "schedule", "queue"
        ],
        data_assets=[
            "fact_job_run_timeline - Job execution history",
            "fact_task_run_timeline - Task-level execution",
            "dim_job - Job metadata and configuration",
            "dim_cluster - Cluster information",
        ],
    ),
    
    DOMAINS.QUALITY: GenieSpaceConfig(
        space_id="01f0f1a3c39517ffbe190f38956d8dd1",
        domain=DOMAINS.QUALITY,
        env_var="QUALITY_GENIE_SPACE_ID",
        name="Data Quality Space",
        short_description="Monitor data freshness, schema changes, lineage, and governance compliance.",
        agent_instructions="""Use this tool for ANY question about:
- Data freshness and staleness (when was table last updated?)
- Schema changes and column modifications
- Data lineage and dependencies
- Table metadata and documentation
- Data quality metrics and validation rules
- NULL rates, duplicate detection, constraint violations
- Catalog and schema organization
- Table ownership and governance
- Volume and growth trends
- Partition health and optimization

DO NOT use for: Job failures (use reliability), query speed (use performance),
spending analysis (use cost), or access permissions (use security).""",
        example_queries=[
            "Which tables haven't been updated in 24 hours?",
            "Show schema changes this week",
            "What is the lineage for this table?",
            "Which tables have high NULL rates?",
            "Are there any duplicate records?",
            "Show tables without owners",
            "What's the data freshness SLA status?",
            "List tables with schema drift",
        ],
        routing_keywords=[
            "quality", "freshness", "stale", "schema", "lineage", "null",
            "duplicate", "constraint", "governance", "catalog", "metadata",
            "owner", "documentation", "column", "partition", "drift",
            "validate", "integrity", "complete", "accurate"
        ],
        data_assets=[
            "fact_table_freshness - Table update timestamps",
            "fact_column_lineage - Column-level lineage",
            "dim_table - Table metadata",
            "dim_column - Column information",
        ],
    ),
    
    DOMAINS.PERFORMANCE: GenieSpaceConfig(
        space_id="01f0f1a3c3e31a8e8e6dee3eddf5d61f",
        domain=DOMAINS.PERFORMANCE,
        env_var="PERFORMANCE_GENIE_SPACE_ID",
        name="Performance Space",
        short_description="Analyze query performance, cluster utilization, and warehouse efficiency.",
        agent_instructions="""Use this tool for ANY question about:
- Slow queries and query optimization opportunities
- Query execution times and trends
- Cluster utilization and resource usage
- SQL warehouse efficiency and concurrency
- Autoscaling behavior and efficiency
- Spill to disk and memory issues
- Scan efficiency and partition pruning
- Cache hit rates and optimization
- Query queue times and delays
- Resource bottlenecks and hotspots

DO NOT use for: Job failures (use reliability), cost analysis (use cost),
data quality issues (use quality), or access control (use security).""",
        example_queries=[
            "What are the slowest queries?",
            "Show cluster utilization trends",
            "Which queries are spilling to disk?",
            "Are warehouses properly sized?",
            "What's the average query latency?",
            "Show queries with full table scans",
            "Which clusters are underutilized?",
            "List queries waiting in queue",
        ],
        routing_keywords=[
            "slow", "fast", "performance", "latency", "duration", "speed",
            "utilization", "cluster", "warehouse", "query", "optimize",
            "scan", "spill", "cache", "memory", "cpu", "autoscale",
            "bottleneck", "queue", "concurrent"
        ],
        data_assets=[
            "fact_query_history - Query execution metrics",
            "fact_cluster_utilization - Resource usage",
            "dim_warehouse - Warehouse configuration",
            "dim_cluster - Cluster metadata",
        ],
    ),
    
    DOMAINS.SECURITY: GenieSpaceConfig(
        space_id="01f0f1a3c44117acada010638189392f",
        domain=DOMAINS.SECURITY,
        env_var="SECURITY_GENIE_SPACE_ID",
        name="Security Auditor Space",
        short_description="Audit access control, permissions, authentication, and compliance events.",
        agent_instructions="""Use this tool for ANY question about:
- Access control and permission changes
- User authentication and login activity
- Audit logs and compliance events
- Data access patterns and who accessed what
- Permission grants and revocations
- Security incidents and anomalies
- Service principal activity
- Token usage and API access
- Sensitive data access monitoring
- Compliance reporting (SOC2, HIPAA, etc.)

DO NOT use for: Job failures (use reliability), cost analysis (use cost),
query performance (use performance), or data quality (use quality).""",
        example_queries=[
            "Who accessed this table?",
            "Show failed login attempts today",
            "What permissions changed this week?",
            "List users with admin access",
            "Show audit events for sensitive data",
            "Which service principals are active?",
            "Are there any suspicious access patterns?",
            "Generate compliance report for SOC2",
        ],
        routing_keywords=[
            "security", "access", "permission", "audit", "login", "auth",
            "user", "grant", "revoke", "compliance", "soc2", "hipaa",
            "sensitive", "pii", "token", "service principal", "admin",
            "privilege", "role", "acl"
        ],
        data_assets=[
            "fact_audit_logs - Security audit events",
            "fact_access_logs - Data access records",
            "dim_user - User information",
            "dim_permission - Permission definitions",
        ],
    ),
    
    DOMAINS.UNIFIED: GenieSpaceConfig(
        space_id="01f0f1a3c4981080b61e224ecd465817",
        domain=DOMAINS.UNIFIED,
        env_var="UNIFIED_GENIE_SPACE_ID",
        name="Overall Health Monitor Space",
        short_description="Holistic platform health view combining insights across all domains.",
        agent_instructions="""Use this tool for questions that:
- Span multiple domains (e.g., "What's the overall platform health?")
- Require cross-domain correlation (e.g., "Did the cost spike cause failures?")
- Need executive-level summaries across the platform
- Ask about general platform status without specific domain
- Request health scores or composite metrics

PREFER SPECIALIZED TOOLS when the question clearly fits one domain.
Use this tool only when multiple domains are needed or for general health overviews.""",
        example_queries=[
            "What's the overall platform health?",
            "Give me an executive summary of issues",
            "Correlate cost spikes with job failures",
            "Show me the top issues across all domains",
            "What should I prioritize fixing?",
        ],
        routing_keywords=[
            "overall", "health", "summary", "executive", "platform",
            "correlate", "across", "multiple", "holistic", "status",
            "dashboard", "overview"
        ],
        data_assets=[
            "Aggregated metrics from all domain spaces",
            "Cross-domain correlation tables",
            "Platform health scores",
        ],
    ),
}


# =============================================================================
# CONVENIENCE ACCESSORS
# =============================================================================

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
    if domain_lower in GENIE_SPACE_REGISTRY:
        return GENIE_SPACE_REGISTRY[domain_lower].get_id()
    return None


def get_genie_space_config(domain: str) -> Optional[GenieSpaceConfig]:
    """
    Get full Genie Space configuration for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        GenieSpaceConfig or None if domain not found.
    """
    return GENIE_SPACE_REGISTRY.get(domain.lower())


def get_all_space_ids() -> Dict[str, str]:
    """
    Get all Genie Space IDs as a simple dict.
    
    Returns:
        Dict of domain -> space_id
    """
    return {
        domain: config.get_id()
        for domain, config in GENIE_SPACE_REGISTRY.items()
    }


def get_configured_spaces() -> Dict[str, GenieSpaceConfig]:
    """
    Get all Genie Spaces that have valid IDs configured.
    
    Returns:
        Dict of domain -> GenieSpaceConfig for all configured spaces.
    """
    return {
        domain: config
        for domain, config in GENIE_SPACE_REGISTRY.items()
        if config.get_id()
    }


def get_routing_keywords_map() -> Dict[str, List[str]]:
    """
    Get keyword -> domain mapping for intent classification.
    
    Returns:
        Dict mapping each keyword to its domain.
    """
    keyword_map = {}
    for domain, config in GENIE_SPACE_REGISTRY.items():
        for keyword in config.routing_keywords:
            keyword_map[keyword.lower()] = domain
    return keyword_map


def validate_genie_spaces() -> Dict[str, bool]:
    """
    Validate which Genie Spaces are properly configured.
    
    Returns:
        Dict of domain -> is_configured boolean.
    """
    return {
        domain: bool(config.get_id())
        for domain, config in GENIE_SPACE_REGISTRY.items()
    }


def print_genie_space_summary():
    """Print summary of Genie Space configuration for debugging."""
    print("=" * 80)
    print("GENIE SPACE CONFIGURATION (Single Source of Truth)")
    print("=" * 80)
    
    for domain, config in GENIE_SPACE_REGISTRY.items():
        space_id = config.get_id()
        override = os.environ.get(config.env_var)
        status = "✓ Configured" if space_id else "✗ Not configured"
        source = "(env override)" if override else "(default)"
        
        print(f"\n{config.name}")
        print(f"  Domain: {domain}")
        print(f"  ID: {space_id or 'None'} {source}")
        print(f"  Status: {status}")
        print(f"  Env var: {config.env_var}")
        print(f"  Description: {config.short_description}")
        print(f"  Keywords: {', '.join(config.routing_keywords[:5])}...")
    
    print("\n" + "=" * 80)


# Legacy compatibility - simple dict for quick access
GENIE_SPACES: Dict[str, str] = get_all_space_ids()


# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    # Core types
    "GenieSpaceConfig",
    "DOMAINS",
    
    # Registry
    "GENIE_SPACE_REGISTRY",
    "GENIE_SPACES",  # Legacy compatibility
    
    # Accessors
    "get_genie_space_id",
    "get_genie_space_config",
    "get_all_space_ids",
    "get_configured_spaces",
    "get_routing_keywords_map",
    "validate_genie_spaces",
    "print_genie_space_summary",
]
