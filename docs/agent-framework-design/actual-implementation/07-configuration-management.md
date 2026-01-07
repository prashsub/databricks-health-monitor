# 07 - Configuration Management

## Overview

This document details the configuration architecture, including Genie Space configuration (single source of truth), settings management, and environment variable overrides.

---

## 📍 File Locations

| File | Purpose |
|------|---------|
| `src/agents/config/genie_spaces.py` | Genie Space configuration (SINGLE SOURCE OF TRUTH) |
| `src/agents/config/settings.py` | Agent settings and environment variables |
| `src/agents/config/__init__.py` | Module exports |

---

## 🏛️ Configuration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Configuration Hierarchy                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              Environment Variables                         │      │
│  │     COST_GENIE_SPACE_ID, LLM_ENDPOINT, CATALOG, etc.      │      │
│  └────────────────────────────┬─────────────────────────────┘      │
│                               │ (override)                          │
│                               ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              genie_spaces.py (Genie Config)               │      │
│  │     - Space IDs, routing instructions, keywords           │      │
│  │     - SINGLE SOURCE OF TRUTH for Genie configuration      │      │
│  └────────────────────────────┬─────────────────────────────┘      │
│                               │ (imports)                           │
│                               ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              settings.py (Agent Settings)                 │      │
│  │     - Delegates Genie to genie_spaces.py                  │      │
│  │     - LLM, Memory, UC, Timeouts, Features                 │      │
│  └────────────────────────────┬─────────────────────────────┘      │
│                               │ (used by)                           │
│                               ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              All Other Modules                            │      │
│  │     from agents.config import settings                    │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Genie Space Configuration

### Single Source of Truth

All Genie Space configuration lives in **one file only**: `src/agents/config/genie_spaces.py`

```python
# File: src/agents/config/genie_spaces.py
# Lines: 1-28

"""
Genie Space Configuration (SINGLE SOURCE OF TRUTH)
===================================================

Centralized configuration for all Genie Space IDs and metadata.
This is the ONLY place where Genie Space configuration should be defined.

IMPORTANT: Do NOT duplicate this configuration elsewhere.

To update Genie Space IDs:
1. Update the GENIE_SPACE_REGISTRY dict below
2. Redeploy the agent
   
Environment variables override defaults (for per-environment config):
    export COST_GENIE_SPACE_ID="new-space-id"
"""
```

### GenieSpaceConfig Dataclass

```python
# File: src/agents/config/genie_spaces.py
# Lines: 51-100

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
    space_id: str          # Default Genie Space ID
    domain: str            # Domain name (cost, security, etc.)
    env_var: str           # Environment variable for override
    
    # Human-readable metadata
    name: str              # Display name (e.g., "Cost Intelligence Space")
    short_description: str # Brief description
    
    # Agent routing instructions (CRITICAL for multi-agent orchestration)
    agent_instructions: str  # Detailed instructions for when to use
    
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
        """Generate comprehensive tool description for LangChain."""
        return f"""{self.short_description}

WHEN TO USE THIS TOOL:
{self.agent_instructions}

EXAMPLE QUERIES:
{chr(10).join(f'- {q}' for q in self.example_queries[:5])}

KEYWORDS: {', '.join(self.routing_keywords[:10])}"""
```

### Genie Space Registry

```python
# File: src/agents/config/genie_spaces.py
# Lines: 109-363

GENIE_SPACE_REGISTRY: Dict[str, GenieSpaceConfig] = {
    
    DOMAINS.COST: GenieSpaceConfig(
        space_id="01f0ea871ffe176fa6aee6f895f83d3b",
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

DO NOT use for: Job failures (use reliability), slow queries (use performance)...""",
        
        example_queries=[
            "Why did costs spike yesterday?",
            "What are the top 10 most expensive jobs?",
            "Show DBU usage by workspace for last 30 days",
            "Which teams are over budget this month?",
        ],
        
        routing_keywords=[
            "cost", "spend", "spending", "budget", "dbu", "billing",
            "expensive", "price", "money", "waste", "optimize",
        ],
        
        data_assets=[
            "fact_usage - Daily usage and cost records",
            "fact_list_prices - SKU pricing information",
        ],
    ),
    
    # Similar configurations for: SECURITY, PERFORMANCE, RELIABILITY, QUALITY, UNIFIED
    ...
}
```

### Accessor Functions

```python
# File: src/agents/config/genie_spaces.py
# Lines: 370-477

def get_genie_space_id(domain: str) -> Optional[str]:
    """Get Genie Space ID for a domain."""
    domain_lower = domain.lower()
    if domain_lower in GENIE_SPACE_REGISTRY:
        return GENIE_SPACE_REGISTRY[domain_lower].get_id()
    return None


def get_genie_space_config(domain: str) -> Optional[GenieSpaceConfig]:
    """Get full Genie Space configuration for a domain."""
    return GENIE_SPACE_REGISTRY.get(domain.lower())


def get_all_space_ids() -> Dict[str, str]:
    """Get all Genie Space IDs as a simple dict."""
    return {
        domain: config.get_id()
        for domain, config in GENIE_SPACE_REGISTRY.items()
    }


def get_routing_keywords_map() -> Dict[str, List[str]]:
    """Get keyword -> domain mapping for intent classification."""
    keyword_map = {}
    for domain, config in GENIE_SPACE_REGISTRY.items():
        for keyword in config.routing_keywords:
            keyword_map[keyword.lower()] = domain
    return keyword_map


def validate_genie_spaces() -> Dict[str, bool]:
    """Validate which Genie Spaces are properly configured."""
    return {
        domain: bool(config.get_id())
        for domain, config in GENIE_SPACE_REGISTRY.items()
    }
```

---

## ⚙️ Agent Settings

### AgentSettings Dataclass

```python
# File: src/agents/config/settings.py
# Lines: 31-270

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

    # =========================================================================
    # Genie Space IDs (DELEGATED to genie_spaces.py)
    # =========================================================================
    @property
    def cost_genie_space_id(self) -> str:
        """Cost Intelligence Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.COST) or ""
    
    @property
    def security_genie_space_id(self) -> str:
        """Security Auditor Space ID (from genie_spaces.py)."""
        return _get_genie_space_id(DOMAINS.SECURITY) or ""
    
    # Similar properties for performance, reliability, quality, unified...

    # =========================================================================
    # Memory Configuration
    # =========================================================================
    lakebase_instance_name: str = field(
        default_factory=lambda: os.environ.get("LAKEBASE_INSTANCE_NAME", "health_monitor_memory")
    )
    short_term_memory_ttl_hours: int = field(
        default_factory=lambda: int(os.environ.get("SHORT_TERM_MEMORY_TTL_HOURS", "24"))
    )
    long_term_memory_ttl_days: int = field(
        default_factory=lambda: int(os.environ.get("LONG_TERM_MEMORY_TTL_DAYS", "365"))
    )

    # =========================================================================
    # Unity Catalog Configuration
    # =========================================================================
    catalog: str = field(
        default_factory=lambda: os.environ.get("CATALOG", "prashanth_subrahmanyam_catalog")
    )
    agent_schema: str = field(
        default_factory=lambda: os.environ.get("AGENT_SCHEMA", "dev_prashanth_subrahmanyam_system_gold_agent")
    )
    
    @property
    def model_full_name(self) -> str:
        """Full UC path for the agent model."""
        return f"{self.catalog}.{self.agent_schema}.health_monitor_agent"

    # =========================================================================
    # MLflow Experiment Configuration
    # =========================================================================
    mlflow_experiment_path: str = field(
        default_factory=lambda: os.environ.get(
            "MLFLOW_EXPERIMENT_PATH", 
            "/Shared/health_monitor/agent"
        )
    )
    
    # Run type tags for differentiation
    RUN_TYPE_MODEL_LOGGING: str = "model_logging"
    RUN_TYPE_EVALUATION: str = "evaluation"
    RUN_TYPE_DEPLOYMENT: str = "deployment"
    RUN_TYPE_PROMPTS: str = "prompt_registry"
    RUN_TYPE_TRACES: str = "traces"
    RUN_TYPE_MONITORING: str = "production_monitoring"

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
```

### Settings Validation

```python
# File: src/agents/config/settings.py
# Lines: 292-313

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
```

---

## 🌍 Environment Variables

### Complete Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| **Databricks** |||
| `DATABRICKS_HOST` | `` | Workspace URL |
| **LLM** |||
| `LLM_ENDPOINT` | `databricks-claude-3-7-sonnet` | LLM serving endpoint |
| `LLM_TEMPERATURE` | `0.3` | Response randomness |
| `EMBEDDING_ENDPOINT` | `databricks-gte-large-en` | Embedding model |
| `EMBEDDING_DIMS` | `1024` | Vector dimensions |
| **Genie Spaces** |||
| `COST_GENIE_SPACE_ID` | `01f0ea871ffe...` | Cost domain |
| `SECURITY_GENIE_SPACE_ID` | `01f0ea9367f2...` | Security domain |
| `PERFORMANCE_GENIE_SPACE_ID` | `01f0ea93671e...` | Performance domain |
| `RELIABILITY_GENIE_SPACE_ID` | `01f0ea8724fd...` | Reliability domain |
| `QUALITY_GENIE_SPACE_ID` | `01f0ea93616c...` | Quality domain |
| `UNIFIED_GENIE_SPACE_ID` | `01f0ea936880...` | Unified health |
| **Memory** |||
| `LAKEBASE_INSTANCE_NAME` | `health_monitor_memory` | Lakebase instance |
| `SHORT_TERM_MEMORY_TTL_HOURS` | `24` | Conversation expiry |
| `LONG_TERM_MEMORY_TTL_DAYS` | `365` | User data expiry |
| **Unity Catalog** |||
| `CATALOG` | `prashanth_subrahmanyam_catalog` | UC catalog |
| `AGENT_SCHEMA` | `dev_..._agent` | UC schema |
| `WAREHOUSE_ID` | `4b9b953939869799` | SQL warehouse |
| **MLflow** |||
| `MLFLOW_EXPERIMENT_PATH` | `/Shared/health_monitor/agent` | Experiment location |
| **Timeouts** |||
| `GENIE_TIMEOUT_SECONDS` | `45` | Genie query timeout |
| `AGENT_TIMEOUT_SECONDS` | `30` | Worker timeout |
| **Feature Flags** |||
| `ENABLE_LONG_TERM_MEMORY` | `true` | Long-term memory |
| `ENABLE_WEB_SEARCH` | `true` | Web search tool |
| `ENABLE_MLFLOW_TRACING` | `true` | MLflow tracing |

---

## 🔧 Usage Examples

### Importing Settings

```python
# Recommended
from agents.config import settings

# Access values
llm = settings.llm_endpoint
cost_space = settings.cost_genie_space_id
```

### Using Genie Config

```python
from agents.config.genie_spaces import (
    get_genie_space_id,
    get_genie_space_config,
    GENIE_SPACE_REGISTRY,
    DOMAINS,
)

# Get space ID
cost_id = get_genie_space_id("cost")

# Get full config
config = get_genie_space_config("cost")
print(config.name)                # "Cost Intelligence Space"
print(config.agent_instructions)  # Detailed routing instructions
print(config.example_queries)     # Sample questions

# Iterate all spaces
for domain, config in GENIE_SPACE_REGISTRY.items():
    print(f"{domain}: {config.get_id()}")
```

### Overriding with Environment Variables

```bash
# Override Genie Space ID
export COST_GENIE_SPACE_ID="new-space-id"

# Override LLM endpoint
export LLM_ENDPOINT="databricks-gpt-4"

# Disable long-term memory
export ENABLE_LONG_TERM_MEMORY="false"
```

---

## 📦 Deployment Configuration

### Model Serving Environment

```python
# File: src/agents/setup/create_serving_endpoint.py
# Lines: 30-55

# Environment variables passed to serving container
ENVIRONMENT_VARS = {
    # NOTE: Genie Space IDs from genie_spaces.py (single source of truth)
    # These are loaded dynamically at runtime via os.environ.get()
    
    # LLM Configuration
    "LLM_ENDPOINT": settings.llm_endpoint,
    "LLM_TEMPERATURE": str(settings.llm_temperature),
    
    # Memory Configuration
    "LAKEBASE_INSTANCE_NAME": settings.lakebase_instance_name,
    
    # Unity Catalog
    "CATALOG": settings.catalog,
    "AGENT_SCHEMA": settings.agent_schema,
    
    # MLflow
    "MLFLOW_EXPERIMENT_PATH": settings.mlflow_experiment_path,
}

# Add Genie Space IDs from registry
for domain, config in GENIE_SPACE_REGISTRY.items():
    ENVIRONMENT_VARS[config.env_var] = config.space_id
```

---

## ✅ Configuration Checklist

### Before Deployment

- [ ] All Genie Space IDs are correct in `genie_spaces.py`
- [ ] Agent routing instructions are comprehensive
- [ ] Example queries cover common use cases
- [ ] LLM endpoint exists in workspace
- [ ] Embedding endpoint exists in workspace
- [ ] Lakebase instance is set up
- [ ] Unity Catalog schema exists
- [ ] MLflow experiment path is valid

### Validation Script

```python
# Validate configuration
from agents.config import settings
from agents.config.genie_spaces import validate_genie_spaces

# Check settings
errors = settings.validate()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")

# Check Genie Spaces
genie_status = validate_genie_spaces()
for domain, configured in genie_status.items():
    status = "✓" if configured else "✗"
    print(f"{status} {domain}: {'Configured' if configured else 'Missing'}")
```

---

**Next:** [08-evaluation-and-quality.md](./08-evaluation-and-quality.md)

