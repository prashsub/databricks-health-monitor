# 02 - Core Agent Implementation

## Overview

This document details the `HealthMonitorAgent` class - the main entry point for the multi-agent system. It implements MLflow's `ChatAgent` interface for seamless deployment to Databricks Model Serving.

---

## 📍 File Location

```
src/agents/orchestrator/agent.py
```

---

## 🎯 Key Class: HealthMonitorAgent

### Class Definition

```python
# File: src/agents/orchestrator/agent.py
# Lines: 50-210

class HealthMonitorAgent(ChatAgent):
    """
    Databricks Health Monitor Multi-Agent System.

    Implements the MLflow ChatAgent interface for deployment
    to Databricks Model Serving.

    Features:
        - Multi-agent orchestration via LangGraph
        - Short-term memory via Lakebase CheckpointSaver
        - Long-term memory via Lakebase DatabricksStore
        - MLflow tracing for all operations
        - Genie Spaces as data interface
    """
```

### Why ChatAgent?

The `ChatAgent` interface is MLflow's recommended approach for deploying conversational agents:

| Feature | Benefit |
|---------|---------|
| Streaming support | `predict_stream()` for progressive responses |
| Context handling | Built-in conversation management |
| Message format | Standardized `ChatAgentMessage` format |
| Model Serving compatible | Direct deployment without wrappers |

---

## 🔧 Initialization

### Constructor

```python
# File: src/agents/orchestrator/agent.py
# Lines: 72-76

def __init__(self):
    """Initialize the Health Monitor Agent."""
    self.workspace_client = WorkspaceClient()
    self._graph = None
    self._checkpointer = None
```

**Key Points:**
- `WorkspaceClient` is initialized for Databricks SDK access
- Graph and checkpointer use lazy initialization (created on first use)
- No heavy resources loaded at construction time

### Lazy Graph Initialization

```python
# File: src/agents/orchestrator/agent.py
# Lines: 78-86

@property
def graph(self):
    """Lazily create the orchestrator graph."""
    if self._graph is None:
        workflow = create_orchestrator_graph()
        # Compile with checkpointer for state persistence
        with get_checkpoint_saver() as checkpointer:
            self._graph = workflow.compile(checkpointer=checkpointer)
    return self._graph
```

**Why Lazy?**
1. **Faster startup** - Model Serving containers start quickly
2. **Memory efficient** - Resources only allocated when needed
3. **Testability** - Can test without full graph initialization

---

## 🔮 The predict() Method

### Method Signature

```python
# File: src/agents/orchestrator/agent.py
# Lines: 127-195

@mlflow.trace(name="health_monitor_predict", span_type="AGENT")
def predict(
    self,
    context: Optional[ChatContext] = None,
    messages: List[ChatAgentMessage] = None,
    custom_inputs: Optional[Dict] = None,
) -> ChatAgentResponse:
    """
    Process a user message and return the agent's response.
    
    Args:
        context: Conversation context (includes conversation_id)
        messages: List of conversation messages
        custom_inputs: Optional custom parameters (thread_id, user_id)
    
    Returns:
        ChatAgentResponse with assistant message and metadata.
    """
```

### Implementation Flow

```python
# Step 1: Resolve identifiers
thread_id = self._resolve_thread_id(custom_inputs, context)
user_id = self._resolve_user_id(custom_inputs, context)

# Step 2: Extract the latest user query
query = messages[-1].content if messages else ""

# Step 3: Create initial state for the graph
initial_state = create_initial_state(
    query=query,
    user_id=user_id,
    thread_id=thread_id,
)

# Step 4: Configure LangGraph with thread_id for memory
config = {"configurable": {"thread_id": thread_id}}

# Step 5: Invoke the orchestrator graph
try:
    result = self.graph.invoke(initial_state, config)
    response_text = result.get("response", "I couldn't generate a response.")
    confidence = result.get("confidence", 0.0)
    sources = result.get("sources", [])
except Exception as e:
    response_text = f"Error processing request: {str(e)}"
    confidence = 0.0
    sources = []

# Step 6: Build and return response
return ChatAgentResponse(
    messages=[
        ChatAgentMessage(
            role="assistant",
            content=response_text,
        )
    ],
    custom_outputs={
        "confidence": confidence,
        "sources": sources,
        "thread_id": thread_id,
        "domains": result.get("intent", {}).get("domains", []),
    },
)
```

---

## 🆔 Thread and User Resolution

### Thread ID Resolution

```python
# File: src/agents/orchestrator/agent.py
# Lines: 88-112

def _resolve_thread_id(
    self,
    custom_inputs: Optional[Dict] = None,
    context: Optional[ChatContext] = None,
) -> str:
    """
    Resolve thread ID for conversation continuity.

    Priority:
        1. custom_inputs["thread_id"]
        2. context.conversation_id
        3. New UUID
    """
    # Priority 1: Explicit thread_id in custom_inputs
    if custom_inputs and "thread_id" in custom_inputs:
        return custom_inputs["thread_id"]
    
    # Priority 2: conversation_id from context
    if context and hasattr(context, "conversation_id") and context.conversation_id:
        return context.conversation_id
    
    # Priority 3: Generate new UUID
    return str(uuid.uuid4())
```

### User ID Resolution

```python
# File: src/agents/orchestrator/agent.py
# Lines: 114-125

def _resolve_user_id(
    self,
    custom_inputs: Optional[Dict] = None,
    context: Optional[ChatContext] = None,
) -> str:
    """
    Resolve user ID for personalization.

    Priority:
        1. custom_inputs["user_id"]
        2. context.user_id (if available)
        3. "anonymous"
    """
    if custom_inputs and "user_id" in custom_inputs:
        return custom_inputs["user_id"]
    
    if context and hasattr(context, "user_id") and context.user_id:
        return context.user_id
    
    return "anonymous"
```

---

## 🌊 Streaming Support

### predict_stream() Method

```python
# File: src/agents/orchestrator/agent.py
# Lines: 197-245

@mlflow.trace(name="health_monitor_predict_stream", span_type="AGENT")
def predict_stream(
    self,
    context: Optional[ChatContext] = None,
    messages: List[ChatAgentMessage] = None,
    custom_inputs: Optional[Dict] = None,
):
    """
    Stream the agent's response progressively.
    
    Yields:
        ChatAgentResponse chunks as they're generated.
    """
    # Resolve identifiers (same as predict)
    thread_id = self._resolve_thread_id(custom_inputs, context)
    user_id = self._resolve_user_id(custom_inputs, context)
    query = messages[-1].content if messages else ""
    
    initial_state = create_initial_state(
        query=query,
        user_id=user_id,
        thread_id=thread_id,
    )
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Use stream() for progressive output
        for event in self.graph.stream(initial_state, config):
            # Yield intermediate results
            if "response" in event:
                yield ChatAgentResponse(
                    messages=[
                        ChatAgentMessage(
                            role="assistant",
                            content=event.get("response", ""),
                        )
                    ],
                    custom_outputs={
                        "streaming": True,
                        "thread_id": thread_id,
                    },
                )
    except Exception as e:
        yield ChatAgentResponse(
            messages=[
                ChatAgentMessage(
                    role="assistant",
                    content=f"Streaming error: {str(e)}",
                )
            ],
        )
```

**When to Use Streaming:**
- Long responses (complex multi-domain queries)
- Interactive chat interfaces
- Real-time feedback to users

---

## 🔐 MLflow Resource Declaration

### Purpose

When deployed to Model Serving, the agent needs access to various Databricks resources. Declaring these resources enables **automatic authentication passthrough**.

### Implementation

```python
# File: src/agents/orchestrator/agent.py
# Lines: 250-295

def get_mlflow_resources() -> list:
    """
    Declare MLflow resources for automatic authentication passthrough.
    
    These resources are automatically authenticated when the model
    is deployed to Model Serving.
    
    Returns:
        List of MLflow resource declarations.
    """
    resources = []
    
    # Genie Spaces - one for each domain
    for domain in ["cost", "security", "performance", "reliability", "quality", "unified"]:
        space_id = settings.get_genie_space_id(domain)
        if space_id and DatabricksGenieSpace:
            resources.append(
                DatabricksGenieSpace(genie_space_id=space_id)
            )
    
    # SQL Warehouse for Genie
    if settings.warehouse_id and DatabricksSQLWarehouse:
        resources.append(
            DatabricksSQLWarehouse(warehouse_id=settings.warehouse_id)
        )
    
    # LLM Serving Endpoint
    if DatabricksServingEndpoint:
        resources.append(
            DatabricksServingEndpoint(endpoint_name=settings.llm_endpoint)
        )
    
    # Lakebase for memory (if available in MLflow version)
    if _HAS_LAKEBASE_RESOURCE and settings.lakebase_instance_name:
        resources.append(
            DatabricksLakebase(instance_name=settings.lakebase_instance_name)
        )
    
    return resources
```

### Resource Types

| Resource Type | Purpose | Configuration Source |
|---------------|---------|---------------------|
| `DatabricksGenieSpace` | Query structured data | `settings.get_genie_space_id(domain)` |
| `DatabricksSQLWarehouse` | SQL execution | `settings.warehouse_id` |
| `DatabricksServingEndpoint` | LLM calls | `settings.llm_endpoint` |
| `DatabricksLakebase` | Memory storage | `settings.lakebase_instance_name` |

---

## 📦 Model Logging

### log_agent_to_mlflow Function

```python
# File: src/agents/orchestrator/agent.py
# Lines: 300-370

def log_agent_to_mlflow(
    registered_model_name: Optional[str] = None,
    experiment_name: Optional[str] = None,
) -> str:
    """
    Log the HealthMonitorAgent to MLflow Model Registry.
    
    Args:
        registered_model_name: Full UC path for model registration
        experiment_name: MLflow experiment path
    
    Returns:
        Registered model version.
    """
    model_name = registered_model_name or settings.model_full_name
    exp_name = experiment_name or settings.mlflow_experiment_path
    
    mlflow.set_experiment(exp_name)
    
    agent = HealthMonitorAgent()
    mlflow.models.set_model(agent)
    
    with mlflow.start_run(run_name="health_monitor_agent_registration") as run:
        mlflow.set_tag("run_type", settings.RUN_TYPE_MODEL_LOGGING)
        
        # Log the agent with resources
        model_info = mlflow.langchain.log_model(
            lc_model=agent.graph,
            artifact_path="agent",
            registered_model_name=model_name,
            pip_requirements=[
                "mlflow>=3.3.2",
                "langchain>=0.3.0",
                "langgraph>=0.2.0",
                "databricks-langchain",
                "databricks-agents>=0.16.0",
            ],
            resources=get_mlflow_resources(),
        )
        
        # Log metadata
        mlflow.log_params({
            "llm_endpoint": settings.llm_endpoint,
            "lakebase_instance": settings.lakebase_instance_name,
            "genie_spaces": list(GENIE_SPACE_REGISTRY.keys()),
        })
        
        return model_info.registered_model_version
```

---

## ⚠️ Error Handling

### Response Error Handling

```python
# In predict() method
try:
    result = self.graph.invoke(initial_state, config)
    response_text = result.get("response", "I couldn't generate a response.")
except Exception as e:
    # Log error to MLflow
    mlflow.log_metric("prediction_error", 1)
    
    # Return graceful error response
    response_text = f"I encountered an error processing your request. Please try again."
    confidence = 0.0
    sources = []
```

### Common Error Scenarios

| Error Type | Cause | Handling |
|------------|-------|----------|
| `GenieTimeoutError` | Genie Space slow | Return partial results |
| `LLMError` | LLM endpoint issue | Retry with backoff |
| `MemoryError` | Lakebase unavailable | Proceed without memory |
| `ClassificationError` | Intent unclear | Default to unified space |

---

## 🧪 Testing the Agent

### Unit Testing

```python
# Test predict method
def test_predict_basic():
    agent = HealthMonitorAgent()
    
    response = agent.predict(
        messages=[
            ChatAgentMessage(role="user", content="Why did costs spike?")
        ],
        custom_inputs={"thread_id": "test-123"},
    )
    
    assert response.messages[0].role == "assistant"
    assert len(response.messages[0].content) > 0
```

### Interactive Testing

```python
# In Databricks notebook
from src.agents.orchestrator.agent import HealthMonitorAgent
from mlflow.types.agent import ChatAgentMessage

agent = HealthMonitorAgent()

# Single query
response = agent.predict(
    messages=[
        ChatAgentMessage(role="user", content="What's our spending trend?")
    ]
)

print(response.messages[0].content)
```

---

## 📊 Key Metrics Logged

| Metric | Type | Purpose |
|--------|------|---------|
| `prediction_latency_ms` | Gauge | End-to-end response time |
| `prediction_error` | Counter | Error rate tracking |
| `domains_queried` | Counter | Which domains are used most |
| `memory_load_error` | Counter | Memory system health |
| `confidence_score` | Gauge | Response quality indicator |

---

## 🔗 Related Files

| File | Relationship |
|------|-------------|
| `orchestrator/graph.py` | LangGraph definition used by `self.graph` |
| `orchestrator/state.py` | AgentState definition |
| `memory/short_term.py` | CheckpointSaver for conversation state |
| `config/settings.py` | Configuration values |

---

**Next:** [03-langgraph-orchestration.md](./03-langgraph-orchestration.md)

