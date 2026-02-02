"""
Genie Tool for LangGraph
========================

TRAINING MATERIAL: Tool Pattern for LangGraph Agent Integration
----------------------------------------------------------------

This module implements a LangChain tool that wraps Genie Space interactions,
enabling natural language data queries within a LangGraph multi-agent system.

WHY TOOLS ARE CRITICAL FOR AGENTS:
-----------------------------------
In LangGraph, tools are the "hands" of an agent:

┌─────────────────────────────────────────────────────────────────────────┐
│                    AGENT TOOL INTERACTION                                │
│                                                                         │
│  User: "How much did we spend last month?"                              │
│                                                                         │
│  ┌─────────────┐    Tool Selection     ┌──────────────────────────────┐ │
│  │   Agent     │ ─────────────────────→│   cost_genie                  │ │
│  │   (Brain)   │                        │   (Hand for cost queries)    │ │
│  └─────────────┘                        └──────────────────────────────┘ │
│        ↓                                          ↓                      │
│  "This is a cost question"             "Execute: SELECT SUM(cost)..."    │
│                                                   ↓                      │
│                                         ┌──────────────────────────────┐ │
│                                         │   Genie Space (Data Source)  │ │
│                                         │   - Unity Catalog tables      │ │
│                                         │   - SQL generation           │ │
│                                         │   - Natural language → SQL   │ │
│                                         └──────────────────────────────┘ │
│                                                   ↓                      │
│                                         "Formatted response"             │
└─────────────────────────────────────────────────────────────────────────┘

GENIEAGENT VS DIRECT GENIE API:
-------------------------------
Two ways to call Genie from an agent:

1. Direct Genie API (Not Recommended for LangGraph)
   - databricks.sdk.service.dashboards.genie.GenieClient
   - Low-level API, manual SQL execution
   - More control but more complexity

2. GenieAgent (Recommended for LangGraph) ✓
   - databricks_langchain.genie.GenieAgent
   - LangGraph-native, proper state management
   - Handles conversation history
   - Works with checkpointers
   - Official Databricks pattern

TOOL DESCRIPTION BEST PRACTICES:
--------------------------------
The tool description is critical for agent routing:

GOOD (Specific, action-oriented):
    "Query cost and billing data. Use for questions about:
     spending, DBU usage, budgets, cost allocation, pricing."

BAD (Vague):
    "A tool for cost stuff."

Why it matters:
- LLM reads description to decide WHICH tool to use
- More specific = better routing
- Include example question types

LAZY INITIALIZATION PATTERN:
-----------------------------
GenieAgent is created lazily (on first use) for several reasons:
1. Import time: Don't slow down module loading
2. Resource efficiency: Only create agents that are actually used
3. Error isolation: One bad Genie Space doesn't break the whole tool set

```python
@property
def genie_agent(self):
    if self._genie_agent is None:  # First access
        self._genie_agent = GenieAgent(...)  # Create now
    return self._genie_agent
```

MLFLOW TRACING:
---------------
All tool invocations are traced for observability:

┌─────────────────────────────────────────────────────────────────────────┐
│  TRACE: genie_tool_query                                                 │
│  ├─ Input: {"query": "monthly spend", "domain": "cost"}                 │
│  ├─ Span: genie_cost                                                    │
│  │    ├─ GenieAgent.invoke()                                            │
│  │    └─ Response parsing                                               │
│  └─ Output: {"response_length": 256, "domain": "cost"}                  │
└─────────────────────────────────────────────────────────────────────────┘

Aligned with the official LangGraph Multi-Agent Genie pattern:
- https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie
- https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/multi-agent-genie
- https://docs.databricks.com/notebooks/source/generative-ai/langgraph-multiagent-genie.html

The GenieTool allows agents to query structured data through
natural language, with Genie handling the SQL generation.
Uses GenieAgent for proper LangGraph integration.
"""

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization for Tool Modules
#
# typing: For type hints (Dict, List, Optional, Any)
# mlflow: For tracing tool invocations
# BaseTool: LangChain's base class for tools (MUST inherit from this)
# BaseModel, Field: Pydantic for input schema validation

from typing import Dict, List, Optional, Any
import mlflow

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..config import settings


# =============================================================================
# INPUT SCHEMA
# =============================================================================
# TRAINING MATERIAL: Pydantic Input Schema Pattern
#
# LangChain tools can define structured input schemas using Pydantic.
# This enables:
# - Type validation at runtime
# - Better error messages
# - Schema documentation for the LLM

class GenieQueryInput(BaseModel):
    """Input schema for Genie query tool."""

    query: str = Field(description="Natural language question to ask Genie")
    workspace_filter: Optional[str] = Field(
        default=None,
        description="Optional workspace to filter results"
    )


class GenieTool(BaseTool):
    """
    LangChain tool for querying Genie Spaces using GenieAgent.

    This tool wraps a Genie Space using the official GenieAgent from
    databricks_langchain, providing proper LangGraph integration.

    Following the official pattern from:
    https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie

    Attributes:
        name: Tool name (e.g., "cost_genie")
        description: Tool description for agent routing
        genie_space_id: Genie Space identifier
        domain: Domain category (cost, security, etc.)
    """

    name: str
    description: str
    genie_space_id: str
    domain: str

    # Private attributes
    _genie_agent: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def genie_agent(self):
        """
        Lazily create GenieAgent.

        Uses databricks_langchain.genie.GenieAgent which is the official
        LangGraph-compatible wrapper for Genie Spaces.

        Reference:
        https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/multi-agent-genie
        """
        if self._genie_agent is None and self.genie_space_id:
            try:
                from databricks_langchain.genie import GenieAgent
                self._genie_agent = GenieAgent(
                    genie_space_id=self.genie_space_id,
                    genie_agent_name=f"{self.name}",
                )
            except ImportError as e:
                print(f"Warning: Could not import GenieAgent: {e}")
            except Exception as e:
                print(f"Warning: Could not initialize GenieAgent for {self.domain}: {e}")
        return self._genie_agent

    def _run(self, query: str, workspace_filter: str = None) -> str:
        """
        Execute Genie query synchronously using GenieAgent.

        Args:
            query: Natural language question
            workspace_filter: Optional workspace filter

        Returns:
            Genie response as string.
        """
        return self._query_genie(query, workspace_filter)

    async def _arun(self, query: str, workspace_filter: str = None) -> str:
        """
        Execute Genie query asynchronously.

        For now, delegates to sync implementation.
        TODO: Implement true async when GenieAgent supports it.
        """
        return self._run(query, workspace_filter)

    @mlflow.trace(name="genie_tool_query", span_type="TOOL")
    def _query_genie(self, query: str, workspace_filter: str = None) -> str:
        """
        Query the Genie Space using GenieAgent.

        This method follows the official LangGraph Multi-Agent Genie pattern:
        - Uses GenieAgent.invoke() for LangGraph compatibility
        - Proper MLflow tracing on all operations
        - Returns string response for tool interface

        Args:
            query: Natural language question
            workspace_filter: Optional workspace filter

        Returns:
            Formatted response string.
        """
        with mlflow.start_span(name=f"genie_{self.domain}") as span:
            span.set_inputs({
                "query": query,
                "domain": self.domain,
                "genie_space_id": self.genie_space_id,
            })

            # Check if Genie Space is configured
            if not self.genie_space_id:
                result = f"Error: Genie Space for {self.domain} is not configured."
                span.set_outputs({"error": "NOT_CONFIGURED"})
                return result

            # Enhance query with workspace filter
            enhanced_query = query
            if workspace_filter:
                enhanced_query += f" Filter by workspace: {workspace_filter}"

            # Check if GenieAgent is available
            genie = self.genie_agent
            if genie is None:
                result = f"Error: GenieAgent for {self.domain} is not available."
                span.set_outputs({"error": "AGENT_NOT_AVAILABLE"})
                return result

            try:
                # Use GenieAgent.invoke() - the official LangGraph pattern
                genie_result = genie.invoke({"input": enhanced_query})

                # Parse GenieAgent response
                result = self._format_response(genie_result)

                span.set_outputs({
                    "response_length": len(result),
                    "domain": self.domain,
                })

                return result

            except Exception as e:
                error_msg = f"Error querying {self.domain} Genie: {str(e)}"
                span.set_outputs({"error": str(e)})
                return error_msg

    def _format_response(self, genie_result: Any) -> str:
        """
        Format GenieAgent response for tool return.

        GenieAgent.invoke() returns a dict with 'output' key containing
        the natural language response.

        Args:
            genie_result: Result from GenieAgent.invoke()

        Returns:
            Formatted response string.
        """
        # Extract output from GenieAgent result
        if isinstance(genie_result, dict):
            content = genie_result.get("output", "")
            if not content:
                # Try other possible keys
                content = genie_result.get("response", "")
                if not content:
                    content = str(genie_result)
        else:
            content = str(genie_result)

        if content:
            return content.strip()

        return "Genie returned no content"


def create_genie_tools() -> List[GenieTool]:
    """
    Create Genie tools for all domains using GenieAgent.

    Each tool wraps a GenieAgent instance for proper LangGraph integration.

    Returns:
        List of GenieTool instances for each configured domain.
    """
    tools = []

    # Domain configurations
    domains = {
        "cost": {
            "name": "cost_genie",
            "description": (
                "Query cost and billing data. Use for questions about: "
                "spending, DBU usage, budgets, cost allocation, pricing, "
                "chargeback, most expensive jobs, cost trends, SKU analysis."
            ),
            "genie_space_id": settings.cost_genie_space_id,
        },
        "security": {
            "name": "security_genie",
            "description": (
                "Query security and audit data. Use for questions about: "
                "access control, permissions, audit logs, who accessed what, "
                "failed logins, compliance, threats, sensitive data access."
            ),
            "genie_space_id": settings.security_genie_space_id,
        },
        "performance": {
            "name": "performance_genie",
            "description": (
                "Query performance data. Use for questions about: "
                "slow queries, cluster utilization, warehouse efficiency, "
                "latency, cache hit rates, query optimization, resource sizing."
            ),
            "genie_space_id": settings.performance_genie_space_id,
        },
        "reliability": {
            "name": "reliability_genie",
            "description": (
                "Query reliability data. Use for questions about: "
                "job failures, SLA compliance, pipeline health, task success, "
                "incidents, job duration, failing jobs, success rates."
            ),
            "genie_space_id": settings.reliability_genie_space_id,
        },
        "quality": {
            "name": "quality_genie",
            "description": (
                "Query data quality data. Use for questions about: "
                "data freshness, schema changes, data lineage, null rates, "
                "table health, governance, data classification."
            ),
            "genie_space_id": settings.quality_genie_space_id,
        },
        "unified": {
            "name": "unified_genie",
            "description": (
                "Query cross-domain data. Use for complex questions spanning "
                "multiple domains, correlation analysis, or when you need "
                "a holistic view of platform health."
            ),
            "genie_space_id": settings.unified_genie_space_id,
        },
    }

    for domain, config in domains.items():
        # Only create tool if Genie Space ID is configured
        if config["genie_space_id"]:
            tools.append(GenieTool(
                name=config["name"],
                description=config["description"],
                genie_space_id=config["genie_space_id"],
                domain=domain,
            ))

    return tools


# Create tools lazily
_genie_tools: Optional[List[GenieTool]] = None


def get_genie_tools() -> List[GenieTool]:
    """Get all configured Genie tools."""
    global _genie_tools
    if _genie_tools is None:
        _genie_tools = create_genie_tools()
    return _genie_tools
