# 04 - Worker Agents and Genie Integration

## Overview

This document details the domain-specific worker agents and their integration with Databricks Genie Spaces. Workers are the "specialists" that query structured data through natural language.

---

## 📍 File Locations

| File | Purpose |
|------|---------|
| `src/agents/workers/base.py` | Base classes and GenieWorkerAgent |
| `src/agents/workers/cost_agent.py` | Cost domain worker |
| `src/agents/workers/security_agent.py` | Security domain worker |
| `src/agents/workers/performance_agent.py` | Performance domain worker |
| `src/agents/workers/reliability_agent.py` | Reliability domain worker |
| `src/agents/workers/quality_agent.py` | Quality domain worker |
| `src/agents/tools/genie_tool.py` | GenieTool LangChain wrapper |
| `src/agents/config/genie_spaces.py` | Genie Space configuration |

---

## 🏭 Worker Architecture

```
                     ┌────────────────────────────┐
                     │    BaseWorkerAgent (ABC)   │
                     │                            │
                     │  + domain: str             │
                     │  + enhance_query()         │
                     │  + get_genie_space_id()    │
                     │  + query()                 │
                     └────────────┬───────────────┘
                                  │
                     ┌────────────┴───────────────┐
                     │                            │
                     ▼                            ▼
        ┌────────────────────────┐    ┌────────────────────────┐
        │   GenieWorkerAgent     │    │   (Custom workers)     │
        │                        │    │                        │
        │  + _genie_agent        │    │  Custom implementations│
        │  + query() → GenieAgent│    │  for special logic     │
        └────────────┬───────────┘    └────────────────────────┘
                     │
     ┌───────────────┼───────────────┬───────────────┐
     │               │               │               │
     ▼               ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│CostAgent│   │Security │   │Perform- │   │ Quality │
│         │   │ Agent   │   │ance     │   │  Agent  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
```

---

## 🔧 Base Worker Classes

### BaseWorkerAgent (Abstract)

```python
# File: src/agents/workers/base.py
# Lines: 20-74

class BaseWorkerAgent(ABC):
    """
    Abstract base class for domain worker agents.

    All worker agents must implement:
    - enhance_query(): Add domain-specific context to the query
    - get_genie_space_id(): Return the Genie Space ID for this domain
    """

    def __init__(self, domain: str):
        """
        Initialize the worker agent.

        Args:
            domain: Domain name (cost, security, etc.)
        """
        self.domain = domain

    @abstractmethod
    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance the query with domain-specific context.

        Args:
            query: Original user query
            context: User context (preferences, role, etc.)

        Returns:
            Enhanced query string.
        """
        pass

    @abstractmethod
    def get_genie_space_id(self) -> str:
        """
        Get the Genie Space ID for this domain.

        Returns:
            Genie Space ID string.
        """
        pass

    @abstractmethod
    def query(self, question: str, context: Dict = None) -> Dict:
        """
        Query the domain for information.

        Args:
            question: User question
            context: Optional user context

        Returns:
            Response dict with keys: response, sources, confidence, domain
        """
        pass
```

---

### GenieWorkerAgent

The concrete base class that integrates with Databricks GenieAgent.

```python
# File: src/agents/workers/base.py
# Lines: 77-200

class GenieWorkerAgent(BaseWorkerAgent):
    """
    Worker agent that queries a Genie Space using GenieAgent.

    Aligned with official Databricks LangGraph Multi-Agent Genie pattern:
    https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie
    """

    def __init__(self, domain: str, genie_space_id: str = None):
        """
        Initialize the Genie worker agent.

        Args:
            domain: Domain name
            genie_space_id: Optional override for Genie Space ID
        """
        super().__init__(domain)
        self._genie_space_id = genie_space_id
        self._genie_agent = None

    def get_genie_space_id(self) -> str:
        """Get Genie Space ID from config or override."""
        if self._genie_space_id:
            return self._genie_space_id
        return settings.get_genie_space_id(self.domain)

    @property
    def genie_agent(self):
        """
        Lazily create GenieAgent instance.

        Uses GenieAgent from the databricks-agents package, which is the official
        LangGraph-compatible wrapper for Genie Spaces.
        
        Import priority (for compatibility):
        1. databricks.agents.genie (databricks-agents >= 0.16.0)
        2. databricks_langchain.genie (fallback for older environments)
        """
        if self._genie_agent is None:
            try:
                # Primary: databricks-agents package (recommended)
                from databricks.agents.genie import GenieAgent
                
                self._genie_agent = GenieAgent(
                    genie_space_id=self.get_genie_space_id(),
                    genie_agent_name=f"{self.domain}_genie",
                )
            except ImportError:
                # Fallback: databricks_langchain package
                try:
                    from databricks_langchain.genie import GenieAgent
                    self._genie_agent = GenieAgent(
                        genie_space_id=self.get_genie_space_id(),
                        genie_agent_name=f"{self.domain}_genie",
                    )
                except ImportError as e:
                    print(f"Warning: Could not import GenieAgent: {e}")
        return self._genie_agent

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with domain context.

        Override in subclasses for domain-specific enhancement.
        """
        # Default: no enhancement
        return query

    @mlflow.trace(name="genie_worker_query", span_type="TOOL")
    def query(self, question: str, context: Dict = None) -> Dict:
        """
        Query the Genie Space using GenieAgent.

        Args:
            question: User question
            context: Optional user context

        Returns:
            Dict with response, confidence, sources, domain
        """
        context = context or {}
        
        # Enhance query with domain context
        enhanced_query = self.enhance_query(question, context)
        
        try:
            if self.genie_agent is None:
                return self._fallback_response(enhanced_query)
            
            # Invoke GenieAgent
            with mlflow.start_span(name=f"genie_{self.domain}", span_type="TOOL") as span:
                span.set_inputs({"query": enhanced_query, "domain": self.domain})
                
                result = self.genie_agent.invoke(enhanced_query)
                
                # Extract response content
                if hasattr(result, 'content'):
                    response_text = result.content
                elif isinstance(result, dict):
                    response_text = result.get('content', str(result))
                else:
                    response_text = str(result)
                
                span.set_outputs({"response_length": len(response_text)})
                
                return {
                    "response": response_text,
                    "confidence": 0.85,
                    "sources": [f"genie_{self.domain}"],
                    "domain": self.domain,
                }
                
        except Exception as e:
            mlflow.log_metric(f"genie_{self.domain}_error", 1)
            return {
                "response": f"Error querying {self.domain}: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "domain": self.domain,
            }

    def _fallback_response(self, query: str) -> Dict:
        """Fallback when GenieAgent unavailable."""
        return {
            "response": f"The {self.domain} system is currently unavailable.",
            "confidence": 0.0,
            "sources": [],
            "domain": self.domain,
        }
```

---

## 👷 Domain Worker Implementations

### Cost Agent

```python
# File: src/agents/workers/cost_agent.py
# Lines: 1-80

"""
Cost Domain Worker Agent
========================

Specializes in:
- DBU usage and billing analysis
- Cost spikes and anomalies
- Budget tracking and forecasting
- Chargeback and allocation
"""

from typing import Dict
import mlflow

from .base import GenieWorkerAgent
from ..config import settings
from ..config.genie_spaces import get_genie_space_config, DOMAINS


class CostWorkerAgent(GenieWorkerAgent):
    """
    Worker agent for cost and billing queries.
    """

    def __init__(self):
        super().__init__(domain=DOMAINS.COST)
        self._config = get_genie_space_config(DOMAINS.COST)

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with cost-specific context.

        Adds:
        - Preferred cost thresholds
        - Default workspace focus
        - Time range clarifications
        """
        enhancements = []

        # Add cost threshold if user has preference
        if context.get("preferences", {}).get("cost_threshold"):
            threshold = context["preferences"]["cost_threshold"]
            enhancements.append(f"Consider costs above ${threshold} as significant.")

        # Add workspace focus if specified
        if context.get("preferences", {}).get("workspace"):
            workspace = context["preferences"]["workspace"]
            enhancements.append(f"Focus on workspace: {workspace}")

        # Build enhanced query
        if enhancements:
            context_str = " ".join(enhancements)
            return f"{query}\n\nContext: {context_str}"

        return query

    def get_tool_description(self) -> str:
        """Get tool description for LangGraph routing."""
        if self._config:
            return self._config.get_tool_description()
        return "Query cost and billing data from Databricks."


# Factory function
def get_cost_agent() -> CostWorkerAgent:
    """Get Cost Worker Agent instance."""
    return CostWorkerAgent()
```

### Security Agent

```python
# File: src/agents/workers/security_agent.py
# Lines: 1-70

"""
Security Domain Worker Agent
============================

Specializes in:
- Audit log analysis
- Access control monitoring
- Permission changes
- Compliance reporting
"""

from typing import Dict

from .base import GenieWorkerAgent
from ..config.genie_spaces import get_genie_space_config, DOMAINS


class SecurityWorkerAgent(GenieWorkerAgent):
    """
    Worker agent for security and audit queries.
    """

    def __init__(self):
        super().__init__(domain=DOMAINS.SECURITY)
        self._config = get_genie_space_config(DOMAINS.SECURITY)

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with security-specific context.

        Adds:
        - Compliance focus areas
        - Sensitive data indicators
        - Audit time ranges
        """
        enhancements = []

        # Check for compliance role
        if context.get("role") in ["compliance_officer", "security_admin"]:
            enhancements.append("Include compliance-relevant details.")

        # Add time constraints for audit queries
        if "audit" in query.lower() or "who accessed" in query.lower():
            enhancements.append("Include timestamps and user identities.")

        if enhancements:
            context_str = " ".join(enhancements)
            return f"{query}\n\nContext: {context_str}"

        return query


def get_security_agent() -> SecurityWorkerAgent:
    """Get Security Worker Agent instance."""
    return SecurityWorkerAgent()
```

### Similar patterns for:
- `performance_agent.py` - Query latency, cluster utilization
- `reliability_agent.py` - Job failures, SLA compliance
- `quality_agent.py` - Data freshness, lineage

---

## 🔌 Genie Space Configuration

### Single Source of Truth

```python
# File: src/agents/config/genie_spaces.py
# Lines: 48-180

GENIE_SPACE_REGISTRY: Dict[str, GenieSpaceConfig] = {
    
    DOMAINS.COST: GenieSpaceConfig(
        space_id="01f0ea871ffe176fa6aee6f895f83d3b",
        domain=DOMAINS.COST,
        env_var="COST_GENIE_SPACE_ID",
        name="Cost Intelligence Space",
        short_description="Analyze Databricks billing, DBU consumption...",
        
        agent_instructions="""Use this tool for ANY question about:
- Billing, spending, or costs (yesterday, last week, month, etc.)
- DBU (Databricks Unit) consumption by SKU, workspace, or cluster
- Cost spikes, anomalies, or unexpected charges
- Budget tracking and forecasting
- Chargeback and cost allocation to teams/projects
...

DO NOT use for: Job failures (use reliability), slow queries (use performance)...""",
        
        example_queries=[
            "Why did costs spike yesterday?",
            "What are the top 10 most expensive jobs?",
            "Show DBU usage by workspace for last 30 days",
            ...
        ],
        
        routing_keywords=[
            "cost", "spend", "spending", "budget", "dbu", "billing",
            "expensive", "price", "money", "waste", "optimize",
            ...
        ],
        
        data_assets=[
            "fact_usage - Daily usage and cost records",
            "fact_list_prices - SKU pricing information",
            ...
        ],
    ),
    
    # Similar configurations for other domains...
}
```

### Using Configuration

```python
# Get Genie Space ID
from agents.config.genie_spaces import get_genie_space_id
cost_space = get_genie_space_id("cost")
# Returns: "01f0ea871ffe176fa6aee6f895f83d3b"

# Get full configuration
from agents.config.genie_spaces import get_genie_space_config
config = get_genie_space_config("cost")
print(config.agent_instructions)  # Detailed routing instructions
print(config.example_queries)      # Sample questions
```

---

## 🔧 GenieTool (LangChain Integration)

### Tool Definition

```python
# File: src/agents/tools/genie_tool.py
# Lines: 36-100

class GenieTool(BaseTool):
    """
    LangChain tool for querying Genie Spaces using GenieAgent.

    This tool wraps a Genie Space using the official GenieAgent from
    databricks_langchain, providing proper LangGraph integration.
    """

    name: str
    description: str
    genie_space_id: str
    domain: str
    _genie_agent: Optional[Any] = None

    @property
    def genie_agent(self):
        """Lazily create GenieAgent."""
        if self._genie_agent is None and self.genie_space_id:
            from databricks_langchain.genie import GenieAgent
            self._genie_agent = GenieAgent(
                genie_space_id=self.genie_space_id,
                genie_agent_name=f"{self.name}",
            )
        return self._genie_agent

    def _run(self, query: str, workspace_filter: str = None) -> str:
        """Execute Genie query synchronously."""
        return self._query_genie(query, workspace_filter)

    @mlflow.trace(name="genie_tool_query", span_type="TOOL")
    def _query_genie(self, query: str, workspace_filter: str = None) -> str:
        """
        Query Genie Space using GenieAgent.
        """
        try:
            if self.genie_agent is None:
                return f"Genie Space {self.domain} is not available."

            # Build enhanced query
            full_query = query
            if workspace_filter:
                full_query = f"{query} (filter: workspace = {workspace_filter})"

            # Invoke GenieAgent
            result = self.genie_agent.invoke(full_query)

            # Extract content
            if hasattr(result, 'content'):
                return result.content
            elif isinstance(result, dict):
                return result.get('content', str(result))
            else:
                return str(result)

        except Exception as e:
            return f"Error querying {self.domain} Genie: {str(e)}"

    async def _arun(self, query: str, workspace_filter: str = None) -> str:
        """Execute Genie query asynchronously."""
        # GenieAgent doesn't support async yet, use sync
        return self._run(query, workspace_filter)
```

### Creating Tools from Configuration

```python
# File: src/agents/tools/genie_tool.py
# Lines: 150-200

def create_genie_tools() -> List[GenieTool]:
    """
    Create GenieTool instances for all configured Genie Spaces.

    Uses the genie_spaces.py configuration to create properly
    documented tools with comprehensive descriptions.

    Returns:
        List of GenieTool instances.
    """
    from ..config.genie_spaces import GENIE_SPACE_REGISTRY

    tools = []

    for domain, config in GENIE_SPACE_REGISTRY.items():
        space_id = config.get_id()
        if not space_id:
            continue

        tool = GenieTool(
            name=f"{domain}_genie",
            description=config.get_tool_description(),
            genie_space_id=space_id,
            domain=domain,
        )
        tools.append(tool)

    return tools
```

---

## 🏭 Worker Factory

### get_worker_agent()

```python
# File: src/agents/workers/__init__.py
# Lines: 15-50

def get_worker_agent(domain: str) -> BaseWorkerAgent:
    """
    Factory function to get a worker agent by domain.

    Args:
        domain: Domain name (cost, security, performance, reliability, quality)

    Returns:
        Appropriate worker agent instance.

    Raises:
        ValueError: If domain is not recognized.
    """
    domain = domain.lower()

    if domain == "cost":
        from .cost_agent import get_cost_agent
        return get_cost_agent()

    elif domain == "security":
        from .security_agent import get_security_agent
        return get_security_agent()

    elif domain == "performance":
        from .performance_agent import get_performance_agent
        return get_performance_agent()

    elif domain == "reliability":
        from .reliability_agent import get_reliability_agent
        return get_reliability_agent()

    elif domain == "quality":
        from .quality_agent import get_quality_agent
        return get_quality_agent()

    else:
        raise ValueError(f"Unknown domain: {domain}")
```

---

## 📊 Query Flow Diagram

```
User Query: "Why did costs spike yesterday?"
                    │
                    ▼
         ┌─────────────────────┐
         │  Intent Classifier  │
         │  domains: ["COST"]  │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   CostWorkerAgent   │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
         │   enhance_query()   │
         │   Add preferences   │
         └──────────┬──────────┘
                    │
         Enhanced: "Why did costs spike yesterday?
                    Context: Focus on workspace: prod.
                    Consider costs above $1000 as significant."
                    │
                    ▼
         ┌─────────────────────┐
         │     GenieAgent      │
         │  Cost Intelligence  │
         │      Space          │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   Genie Response    │
         │   SQL Generated     │
         │   Results Returned  │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Worker Response    │
         │  {                  │
         │    response: "...", │
         │    confidence: 0.9, │
         │    sources: [...],  │
         │    domain: "cost"   │
         │  }                  │
         └─────────────────────┘
```

---

## 🔍 Adding a New Domain Worker

### Step 1: Add Genie Space Configuration

```python
# In src/agents/config/genie_spaces.py

GENIE_SPACE_REGISTRY["governance"] = GenieSpaceConfig(
    space_id="your-genie-space-id",
    domain="governance",
    env_var="GOVERNANCE_GENIE_SPACE_ID",
    name="Data Governance Space",
    short_description="Analyze data governance and compliance...",
    agent_instructions="""Use for governance queries...""",
    example_queries=["Which tables lack owners?", ...],
    routing_keywords=["governance", "owner", "compliance", ...],
    data_assets=["dim_table", "fact_governance_events", ...],
)
```

### Step 2: Create Worker Agent

```python
# Create src/agents/workers/governance_agent.py

from .base import GenieWorkerAgent
from ..config.genie_spaces import get_genie_space_config

class GovernanceWorkerAgent(GenieWorkerAgent):
    def __init__(self):
        super().__init__(domain="governance")
        self._config = get_genie_space_config("governance")

    def enhance_query(self, query: str, context: Dict) -> str:
        # Add governance-specific enhancements
        return query

def get_governance_agent() -> GovernanceWorkerAgent:
    return GovernanceWorkerAgent()
```

### Step 3: Register in Factory

```python
# In src/agents/workers/__init__.py

def get_worker_agent(domain: str) -> BaseWorkerAgent:
    # ... existing code ...
    elif domain == "governance":
        from .governance_agent import get_governance_agent
        return get_governance_agent()
```

### Step 4: Add Graph Node

```python
# In src/agents/orchestrator/graph.py

@mlflow.trace(name="governance_agent_node", span_type="TOOL")
def governance_agent_node(state: AgentState) -> Dict:
    worker = get_worker_agent("governance")
    result = worker.query(state["query"], state.get("memory_context", {}))
    return {"worker_results": {"governance": result}}

# Add to graph
workflow.add_node("governance_agent", governance_agent_node)
workflow.add_edge("governance_agent", "synthesize_response")
```

### Step 5: Update Intent Classifier

Add "GOVERNANCE" to the classifier prompt and routing logic.

---

**Next:** [05-memory-system.md](./05-memory-system.md)

