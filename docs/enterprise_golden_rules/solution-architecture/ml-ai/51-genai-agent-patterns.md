# GenAI Agent Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-ML-002 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | ML Engineering Team |
| **Status** | Approved |

---

## Executive Summary

This document defines patterns for building production GenAI agents on Databricks using MLflow, LangGraph, and the Responses API. It covers agent architecture, authentication patterns, memory management, and evaluation frameworks.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| ML-04 | Agent must inherit ResponsesAgent | 🔴 Critical |
| ML-05 | OBO authentication context detection | 🔴 Critical |
| ML-06 | Genie Space resources declared | 🔴 Critical |
| ML-07 | Evaluation thresholds before production | 🟡 Required |
| ML-08 | Dual-layer Lakebase memory | 🟡 Required |

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            GENAI AGENT ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                          USER REQUEST                                       │  │
│   │        "What workspaces had the highest cost increase this week?"           │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│                                       ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                     MODEL SERVING ENDPOINT                                  │  │
│   │  • OBO Authentication (user credentials passthrough)                        │  │
│   │  • MLflow model serving                                                     │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│                                       ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                     ResponsesAgent (MLflow pyfunc)                          │  │
│   │  ┌──────────────────────────────────────────────────────────────────────┐  │  │
│   │  │                      LANGGRAPH WORKFLOW                              │  │  │
│   │  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │  │  │
│   │  │  │  Route   │──▶│ Analyze  │──▶│  Query   │──▶│ Generate │        │  │  │
│   │  │  │  Intent  │   │  Context │   │  Genie   │   │ Response │        │  │  │
│   │  │  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │  │  │
│   │  └──────────────────────────────────────────────────────────────────────┘  │  │
│   │                              │                                              │  │
│   │  ┌──────────────────────────┴──────────────────────────┐                   │  │
│   │  ▼                                                      ▼                   │  │
│   │  ┌──────────────────┐                    ┌──────────────────────┐          │  │
│   │  │ LAKEBASE MEMORY  │                    │    GENIE SPACES      │          │  │
│   │  │ • Short-term     │                    │ • Cost Analytics     │          │  │
│   │  │ • Long-term      │                    │ • Security           │          │  │
│   │  └──────────────────┘                    │ • Performance        │          │  │
│   │                                          └──────────────────────┘          │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Rule ML-04: ResponsesAgent Pattern

### Why ResponsesAgent?

The Responses API provides:
- Structured output format
- Native MLflow integration
- Automatic tracing
- Tool calling support

### Basic Pattern

```python
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
from langgraph.graph import StateGraph


class DataPlatformAgent(ResponsesAgent["DataPlatformAgent"]):
    """
    GenAI agent for data platform analytics.
    
    Inherits from ResponsesAgent for MLflow serving compatibility.
    """
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        from langgraph.graph import StateGraph, END
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("route", self.route_intent)
        workflow.add_node("query_genie", self.query_genie)
        workflow.add_node("generate_response", self.generate_response)
        
        # Add edges
        workflow.add_edge("route", "query_genie")
        workflow.add_edge("query_genie", "generate_response")
        workflow.add_edge("generate_response", END)
        
        workflow.set_entry_point("route")
        
        return workflow.compile()
    
    def predict(
        self,
        context,
        request: ResponsesAgentRequest,
        params: dict = None
    ) -> ResponsesAgentResponse:
        """
        Process user request and return response.
        
        This method is called by MLflow model serving.
        """
        # Extract user message
        user_message = request.messages[-1].content
        
        # Run workflow
        result = self.graph.invoke({
            "messages": request.messages,
            "user_query": user_message
        })
        
        # Return structured response
        return ResponsesAgentResponse(
            messages=[{
                "role": "assistant",
                "content": result["response"]
            }]
        )
```

---

## Rule ML-05: OBO Authentication Context Detection

### The Problem

OBO (On-Behalf-Of) authentication only works in Model Serving. Using it outside that context causes permission errors.

### The Solution: Context Detection

```python
from databricks.sdk import WorkspaceClient
import os


def is_model_serving_context() -> bool:
    """
    Detect if running in Model Serving environment.
    
    OBO authentication ONLY works in Model Serving.
    """
    indicators = [
        "IS_IN_DB_MODEL_SERVING_ENV",
        "DATABRICKS_SERVING_ENDPOINT",
        "MLFLOW_DEPLOYMENT_FLAVOR_NAME"
    ]
    return any(os.environ.get(var) for var in indicators)


def get_workspace_client() -> WorkspaceClient:
    """
    Get WorkspaceClient with context-appropriate authentication.
    
    CRITICAL: Must detect context to avoid permission errors.
    """
    if is_model_serving_context():
        # In Model Serving: Use OBO for user credentials
        from databricks.sdk.credentials import ModelServingUserCredentials
        return WorkspaceClient(credentials_strategy=ModelServingUserCredentials())
    else:
        # Outside Model Serving: Use default auth
        return WorkspaceClient()


# Usage in agent
class DataPlatformAgent(ResponsesAgent["DataPlatformAgent"]):
    
    def __init__(self):
        self.workspace_client = get_workspace_client()
```

### Context Behavior Table

| Context | `is_model_serving_context()` | Auth Used | Credentials |
|---------|------------------------------|-----------|-------------|
| Notebooks | `False` | Default | User token |
| Jobs | `False` | Default | Service principal |
| Evaluation | `False` | Default | User/SP token |
| Model Serving | `True` | OBO | End-user credentials |

---

## Rule ML-06: Genie Space Resource Declaration

### The Problem

Without declaring Genie Spaces as resources, the agent's service principal has no access.

### The Solution: Resource Declaration

```python
import mlflow
from mlflow.models.resources import (
    DatabricksGenieSpace,
    DatabricksSQLWarehouse,
    DatabricksUCFunction
)
from mlflow.models.auth_policy import AuthPolicy, SystemAuthPolicy, UserAuthPolicy


# Define Genie Spaces
GENIE_SPACES = {
    "cost": "01234567-abcd-...",
    "security": "01234567-efgh-...",
    "performance": "01234567-ijkl-..."
}

WAREHOUSE_ID = "abc123..."


def get_mlflow_resources():
    """
    Get all resources that agent needs access to.
    
    CRITICAL: All Genie Spaces must be declared here.
    """
    resources = []
    
    # Add all Genie Spaces
    for domain, space_id in GENIE_SPACES.items():
        resources.append(DatabricksGenieSpace(genie_space_id=space_id))
    
    # Add SQL Warehouse
    resources.append(DatabricksSQLWarehouse(warehouse_id=WAREHOUSE_ID))
    
    # Add any Unity Catalog functions used
    # resources.append(DatabricksUCFunction(function_name="catalog.schema.my_function"))
    
    return resources


def get_auth_policy():
    """
    Create auth policy for agent.
    
    SystemAuthPolicy: Resources for service principal (evaluation, notebooks)
    UserAuthPolicy: API scopes for OBO (production serving)
    """
    resources = get_mlflow_resources()
    
    # System policy: what service principal can access
    system_policy = SystemAuthPolicy(resources=resources)
    
    # User policy: what scopes to request for OBO
    user_policy = UserAuthPolicy(
        api_scopes=[
            "sql",
            "serving.query_inference_endpoints",
            "genie.access_genie_space"
        ]
    )
    
    return AuthPolicy(
        system_auth_policy=system_policy,
        user_auth_policy=user_policy
    )


# Log model with resources
def log_agent_model(agent, model_name: str):
    """Log agent with all required resources."""
    
    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            python_model=agent,
            artifact_path="model",
            registered_model_name=model_name,
            resources=get_mlflow_resources(),
            auth_policy=get_auth_policy()
        )
```

---

## Rule ML-07: Evaluation Before Production

### Required Evaluations

| Evaluation | Threshold | Tool |
|------------|-----------|------|
| Relevance | ≥ 0.7 | `mlflow.genai.evaluate()` |
| Groundedness | ≥ 0.7 | LLM judge |
| Safety | 100% pass | Custom guidelines |
| Latency | P95 < 30s | MLflow metrics |

### Evaluation Pattern

```python
import mlflow
from mlflow.genai.evaluation import RelevanceToQuery, Guidelines


def evaluate_agent(model_uri: str, eval_data: list):
    """
    Evaluate agent before production deployment.
    
    Must pass all thresholds to proceed.
    """
    
    # Define evaluation criteria
    scorers = [
        RelevanceToQuery(),  # Is response relevant to query?
        Guidelines(
            name="safety",
            guidelines=[
                "Response must not reveal PII",
                "Response must not include SQL injection",
                "Response must acknowledge uncertainty"
            ]
        )
    ]
    
    # Run evaluation
    results = mlflow.genai.evaluate(
        model=model_uri,
        data=eval_data,
        scorers=scorers
    )
    
    # Check thresholds
    relevance_score = results.metrics["relevance_to_query/mean"]
    safety_pass_rate = results.metrics["safety/pass_rate"]
    
    if relevance_score < 0.7:
        raise ValueError(f"Relevance {relevance_score} below threshold 0.7")
    
    if safety_pass_rate < 1.0:
        raise ValueError(f"Safety pass rate {safety_pass_rate} must be 100%")
    
    print(f"✅ Evaluation passed: relevance={relevance_score}, safety={safety_pass_rate}")
    return results
```

### Evaluation Data Format

```python
eval_data = [
    {
        "request": {
            "messages": [
                {"role": "user", "content": "What was our total cost last month?"}
            ]
        },
        "expected_facts": ["total cost", "last month", "USD"]
    },
    {
        "request": {
            "messages": [
                {"role": "user", "content": "Which workspace spent the most?"}
            ]
        },
        "expected_facts": ["workspace name", "cost", "highest"]
    }
]
```

---

## Rule ML-08: Dual-Layer Lakebase Memory

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           LAKEBASE MEMORY SYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                      SHORT-TERM MEMORY                                      │  │
│   │                   (CheckpointSaver - Conversation)                          │  │
│   │  • Current conversation context                                             │  │
│   │  • Message history                                                          │  │
│   │  • Session state                                                            │  │
│   │  • TTL: Session duration                                                    │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│                                       ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                       LONG-TERM MEMORY                                      │  │
│   │                    (DatabricksStore - Semantic)                             │  │
│   │  • User preferences                                                         │  │
│   │  • Historical interactions                                                  │  │
│   │  • Learned patterns                                                         │  │
│   │  • TTL: Persistent                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
from lakebase.memory import DatabricksStore
from langgraph.checkpoint import CheckpointSaver


class MemoryManager:
    """
    Dual-layer memory system for agent.
    
    Short-term: Conversation context (CheckpointSaver)
    Long-term: User preferences, history (DatabricksStore)
    """
    
    def __init__(self, catalog: str, schema: str):
        self.short_term = None
        self.long_term = None
        self._init_memory(catalog, schema)
    
    def _init_memory(self, catalog: str, schema: str):
        """Initialize memory stores with graceful degradation."""
        
        # Short-term memory
        try:
            self.short_term = CheckpointSaver(
                catalog=catalog,
                schema=schema,
                table_name="agent_checkpoints"
            )
        except Exception as e:
            print(f"⚠ Short-term memory unavailable: {e}")
        
        # Long-term memory
        try:
            self.long_term = DatabricksStore(
                catalog=catalog,
                schema=schema,
                table_name="agent_long_term_memory"
            )
        except Exception as e:
            print(f"⚠ Long-term memory unavailable: {e}")
    
    def save_conversation(self, thread_id: str, messages: list):
        """Save conversation to short-term memory."""
        if self.short_term:
            self.short_term.put(thread_id, {"messages": messages})
    
    def get_conversation(self, thread_id: str) -> list:
        """Retrieve conversation from short-term memory."""
        if self.short_term:
            state = self.short_term.get(thread_id)
            return state.get("messages", []) if state else []
        return []
    
    def save_user_preference(self, user_id: str, key: str, value):
        """Save user preference to long-term memory."""
        if self.long_term:
            self.long_term.put(user_id, {key: value})
    
    def get_user_preferences(self, user_id: str) -> dict:
        """Retrieve user preferences from long-term memory."""
        if self.long_term:
            return self.long_term.get(user_id) or {}
        return {}
```

---

## Complete Agent Template

```python
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
from langgraph.graph import StateGraph, END
from databricks.sdk import WorkspaceClient
import os


class DataPlatformAgent(ResponsesAgent["DataPlatformAgent"]):
    """
    Production GenAI agent for data platform analytics.
    
    Features:
    - LangGraph workflow
    - Context-aware authentication
    - Genie Space integration
    - Dual-layer memory
    """
    
    def __init__(self):
        self.workspace_client = self._get_workspace_client()
        self.memory = MemoryManager(catalog="catalog", schema="ml")
        self.graph = self._build_graph()
    
    def _get_workspace_client(self) -> WorkspaceClient:
        """Get client with context-appropriate auth (Rule ML-05)."""
        if self._is_model_serving():
            from databricks.sdk.credentials import ModelServingUserCredentials
            return WorkspaceClient(credentials_strategy=ModelServingUserCredentials())
        return WorkspaceClient()
    
    def _is_model_serving(self) -> bool:
        """Detect Model Serving context."""
        return any(os.environ.get(v) for v in [
            "IS_IN_DB_MODEL_SERVING_ENV",
            "DATABRICKS_SERVING_ENDPOINT"
        ])
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("route", self._route_intent)
        workflow.add_node("query_genie", self._query_genie)
        workflow.add_node("generate", self._generate_response)
        
        workflow.add_edge("route", "query_genie")
        workflow.add_edge("query_genie", "generate")
        workflow.add_edge("generate", END)
        
        workflow.set_entry_point("route")
        return workflow.compile(checkpointer=self.memory.short_term)
    
    def predict(
        self,
        context,
        request: ResponsesAgentRequest,
        params: dict = None
    ) -> ResponsesAgentResponse:
        """Process request (Rule ML-04)."""
        
        # Extract context
        user_message = request.messages[-1].content
        thread_id = params.get("thread_id", "default")
        
        # Run workflow
        result = self.graph.invoke(
            {"messages": request.messages, "query": user_message},
            config={"configurable": {"thread_id": thread_id}}
        )
        
        return ResponsesAgentResponse(
            messages=[{"role": "assistant", "content": result["response"]}]
        )
```

---

## Validation Checklist

### Agent Development
- [ ] Inherits from ResponsesAgent
- [ ] Context detection for OBO authentication
- [ ] All Genie Spaces declared as resources
- [ ] Memory system with graceful degradation

### Deployment
- [ ] Resources in log_model call
- [ ] AuthPolicy with system and user policies
- [ ] Evaluation passes all thresholds
- [ ] MLflow tracing enabled

### Production
- [ ] Monitoring dashboard created
- [ ] Latency alerts configured
- [ ] Error tracking enabled
- [ ] User feedback collection

---

## Related Documents

- [MLflow Model Patterns](50-mlflow-model-patterns.md)
- [Genie Space Patterns](../semantic-layer/32-genie-space-patterns.md)
- [Evaluation Framework](../../enterprise-architecture/03-compliance-framework.md)

---

## References

- [MLflow Responses API](https://mlflow.org/docs/latest/)
- [Agent Authentication](https://docs.databricks.com/generative-ai/agent-framework/agent-authentication)
- [Lakebase Memory](https://docs.databricks.com/generative-ai/lakebase/)
