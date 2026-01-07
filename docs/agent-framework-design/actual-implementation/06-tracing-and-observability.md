# 06 - Tracing and Observability

## Overview

This document details MLflow tracing implementation throughout the agent, enabling comprehensive observability of agent operations, latency tracking, and debugging capabilities.

---

## 📍 Key Files

| File | Purpose |
|------|---------|
| `src/agents/__init__.py` | Module-level autolog enablement |
| `src/agents/orchestrator/agent.py` | Agent-level tracing |
| `src/agents/orchestrator/graph.py` | Node-level tracing |
| `src/agents/workers/base.py` | Worker tracing |
| `src/agents/memory/short_term.py` | Memory operation tracing |
| `src/agents/memory/long_term.py` | Memory operation tracing |

---

## 🔧 Autolog Configuration

### Module-Level Enablement

```python
# File: src/agents/__init__.py
# Lines: 1-25

import mlflow

# CRITICAL: Enable autolog at module level per MLflow GenAI patterns
# This must be at the TOP of the module before any LangChain imports
# Note: Using minimal parameters for compatibility with current MLflow version
try:
    mlflow.langchain.autolog()
except Exception as e:
    print(f"⚠ MLflow autolog not available: {e}")

from .config.settings import settings

# Set default experiment for agent traces
try:
    mlflow.set_experiment(settings.mlflow_experiment_path)
    mlflow.set_tag("run_type", settings.RUN_TYPE_TRACES)
except Exception:
    # Experiment creation may fail in some contexts; proceed anyway
    pass
```

**Why Module Level?**

1. **Captures all LangChain operations** - Any LLM call is automatically traced
2. **Consistent tracing** - All code paths instrumented
3. **Zero manual instrumentation** - Chains, agents, retrievers all traced

---

## 📊 Span Types

### MLflow Span Type Reference

| Span Type | Usage | Example Operations |
|-----------|-------|-------------------|
| `AGENT` | Top-level agent operations | `predict()`, `predict_stream()` |
| `CLASSIFIER` | Classification operations | Intent classification |
| `TOOL` | Tool/function calls | Genie queries, worker execution |
| `LLM` | LLM invocations | Response synthesis |
| `MEMORY` | Memory operations | Load context, save preferences |
| `RETRIEVER` | Search/retrieval | Memory search, vector search |

---

## 🏷️ Tracing Decorators

### @mlflow.trace Decorator

```python
# Basic usage
@mlflow.trace(name="my_function", span_type="TOOL")
def my_function(arg1, arg2):
    """Function is automatically traced."""
    result = process(arg1, arg2)
    return result
```

### Traced Functions in the Codebase

#### Agent Level

```python
# File: src/agents/orchestrator/agent.py
# Lines: 127, 197

@mlflow.trace(name="health_monitor_predict", span_type="AGENT")
def predict(self, context, messages, custom_inputs):
    """Main prediction endpoint."""
    ...

@mlflow.trace(name="health_monitor_predict_stream", span_type="AGENT")
def predict_stream(self, context, messages, custom_inputs):
    """Streaming prediction endpoint."""
    ...
```

#### Graph Nodes

```python
# File: src/agents/orchestrator/graph.py

@mlflow.trace(name="load_context", span_type="MEMORY")
def load_context(state: AgentState) -> Dict:
    """Load user memory context."""
    ...

@mlflow.trace(name="classify_intent_node", span_type="CLASSIFIER")
def classify_intent(state: AgentState) -> Dict:
    """Classify user intent."""
    ...

@mlflow.trace(name="cost_agent_node", span_type="TOOL")
def cost_agent_node(state: AgentState) -> Dict:
    """Execute cost domain worker."""
    ...

@mlflow.trace(name="synthesize_response", span_type="LLM")
def synthesize_response(state: AgentState) -> Dict:
    """Synthesize final response."""
    ...
```

#### Workers

```python
# File: src/agents/workers/base.py

@mlflow.trace(name="genie_worker_query", span_type="TOOL")
def query(self, question: str, context: Dict = None) -> Dict:
    """Query Genie Space."""
    ...
```

#### Memory Operations

```python
# File: src/agents/memory/long_term.py

@mlflow.trace(name="save_memory", span_type="MEMORY")
def save_memory(self, user_id, memory_key, memory_data, namespace):
    """Save to long-term memory."""
    ...

@mlflow.trace(name="search_memories", span_type="RETRIEVER")
def search_memories(self, user_id, query, limit, namespace):
    """Search memories semantically."""
    ...
```

---

## 📐 Span Hierarchy

### Complete Trace Structure

```
health_monitor_predict (AGENT)
│
├── load_context (MEMORY)
│   └── search_memories (RETRIEVER)
│       └── databricks_store_search (auto-logged)
│
├── classify_intent_node (CLASSIFIER)
│   └── classify_intent (CLASSIFIER)
│       └── langchain_llm_invoke (LLM, auto-logged)
│           └── chat_databricks (LLM, auto-logged)
│
├── cost_agent_node (TOOL)
│   └── genie_worker_query (TOOL)
│       └── genie_cost (TOOL)
│           └── genie_agent_invoke (auto-logged)
│
└── synthesize_response (LLM)
    └── synthesize (LLM)
        └── langchain_llm_invoke (LLM, auto-logged)
            └── chat_databricks (LLM, auto-logged)
```

### Multi-Domain Query Trace

```
health_monitor_predict (AGENT)
│
├── load_context (MEMORY)
├── classify_intent_node (CLASSIFIER)
│
├── parallel_agents_node (TOOL)
│   │
│   ├── [Thread 1] cost_agent_node (TOOL)
│   │   └── genie_worker_query (TOOL)
│   │
│   ├── [Thread 2] reliability_agent_node (TOOL)
│   │   └── genie_worker_query (TOOL)
│   │
│   └── [Thread 3] performance_agent_node (TOOL)
│       └── genie_worker_query (TOOL)
│
└── synthesize_response (LLM)
```

---

## 🔍 Manual Span Creation

### Using start_span Context Manager

```python
# File: src/agents/workers/base.py
# Lines: 130-155

def query(self, question: str, context: Dict = None) -> Dict:
    """Query with detailed span instrumentation."""
    context = context or {}
    enhanced_query = self.enhance_query(question, context)
    
    try:
        if self.genie_agent is None:
            return self._fallback_response(enhanced_query)
        
        # Create span with inputs/outputs
        with mlflow.start_span(name=f"genie_{self.domain}", span_type="TOOL") as span:
            span.set_inputs({
                "query": enhanced_query,
                "domain": self.domain,
                "space_id": self.get_genie_space_id(),
            })
            
            result = self.genie_agent.invoke(enhanced_query)
            
            # Extract response
            response_text = self._extract_response(result)
            
            span.set_outputs({
                "response_length": len(response_text),
                "has_content": bool(response_text),
            })
            
            span.set_attributes({
                "domain": self.domain,
                "query_enhanced": True,
            })
            
            return {
                "response": response_text,
                "confidence": 0.85,
                "sources": [f"genie_{self.domain}"],
                "domain": self.domain,
            }
            
    except Exception as e:
        mlflow.log_metric(f"genie_{self.domain}_error", 1)
        return self._error_response(str(e))
```

### Setting Span Attributes

```python
# Available span methods
span.set_inputs({"key": "value"})       # Input data
span.set_outputs({"key": "value"})      # Output data
span.set_attributes({"custom": "attr"}) # Custom attributes
```

---

## 🏷️ Trace Tagging

### Adding Tags to Traces

```python
# File: src/agents/orchestrator/agent.py
# Lines: 180-190

# Update trace with metadata
mlflow.update_current_trace(tags={
    "user_id": user_id,
    "thread_id": thread_id,
    "environment": os.environ.get("ENVIRONMENT", "dev"),
    "domains": ",".join(result.get("intent", {}).get("domains", [])),
    "confidence": str(result.get("confidence", 0.0)),
})
```

### Standard Tags

| Tag | Purpose | Example |
|-----|---------|---------|
| `user_id` | User identification | `user@company.com` |
| `thread_id` | Conversation tracking | `conv_abc123` |
| `environment` | Deployment environment | `dev`, `prod` |
| `domains` | Domains queried | `cost,reliability` |
| `confidence` | Response confidence | `0.92` |
| `run_type` | Type of MLflow run | `traces`, `evaluation` |

---

## 🔗 Linking Prompts to Traces

### Overview

MLflow 3.0 supports linking registered prompts to traces. By loading prompts using `mlflow.genai.load_prompt()` **inside a traced function**, the prompt version is automatically linked to the trace in the MLflow UI.

Reference: [Link prompts to traces](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/)

### Implementation Pattern

```python
# File: src/agents/setup/log_agent_model.py
# Inside HealthMonitorAgent.predict()

def predict(self, context, model_input):
    """
    IMPORTANT: Prompts are loaded inside this traced function to link
    them to traces in MLflow UI.
    """
    import mlflow
    import os
    
    # ==================================================================
    # LOAD PROMPTS FROM MLFLOW PROMPT REGISTRY (Links to Traces!)
    # ==================================================================
    # Loading prompts inside the traced function automatically links
    # the prompt version to this trace in the MLflow UI.
    # ==================================================================
    def _load_prompt_safe(prompt_uri: str, default: str = "") -> str:
        """Safely load a prompt, returning default if not found."""
        try:
            return mlflow.genai.load_prompt(prompt_uri).template
        except Exception:
            return default
    
    # Get catalog/schema from environment
    _catalog = os.environ.get("AGENT_CATALOG", "...")
    _schema = os.environ.get("AGENT_SCHEMA", "...")
    
    # Load prompts - this links them to the current trace!
    prompts = {}
    prompt_names = ["orchestrator", "intent_classifier", "cost_analyst", ...]
    
    for prompt_name in prompt_names:
        prompt_uri = f"prompts:/{_catalog}.{_schema}.prompt_{prompt_name}@production"
        prompts[prompt_name] = _load_prompt_safe(prompt_uri, f"Default {prompt_name}")
    
    # Start trace span
    with mlflow.start_span(name="agent_predict", span_type="AGENT") as span:
        # Tag trace with prompts loaded
        mlflow.update_current_trace(tags={
            "prompts_loaded": ",".join(prompt_names),
            "prompt_catalog": _catalog,
            "prompt_schema": _schema,
        })
        
        # ... rest of prediction logic ...
```

### Key Points

1. **Load INSIDE traced function** - Prompts must be loaded within the traced scope
2. **Use `mlflow.genai.load_prompt()`** - This creates the link to the trace
3. **Use URI format** - `prompts:/{catalog}.{schema}.{prompt_name}@{alias}`
4. **Safe loading** - Handle missing prompts gracefully
5. **Tag the trace** - Record which prompts were loaded for debugging

### Environment Variables

The agent uses environment variables to locate prompts:

| Variable | Purpose | Default |
|----------|---------|---------|
| `AGENT_CATALOG` | Unity Catalog name | `prashanth_subrahmanyam_catalog` |
| `AGENT_SCHEMA` | Schema containing prompts | `dev_*_system_gold_agent` |

These are set in the Model Serving endpoint configuration.

### MLflow UI Integration

After loading prompts inside traces:

1. **View in MLflow UI**: Go to Experiment → Traces
2. **Linked Prompts**: Traces show linked prompt versions
3. **Click through**: Navigate from trace to prompt registry
4. **Version tracking**: See which prompt version was used

---

## 👤 User & Session Tracking

### Overview

MLflow 3 provides **standard metadata fields** for tracking users and sessions:

- `mlflow.trace.user` - Associates traces with specific users
- `mlflow.trace.session` - Groups traces belonging to multi-turn conversations

Reference: [Track Users & Sessions](https://mlflow.org/docs/latest/genai/tracing/track-users-sessions/)

### Implementation

```python
# File: src/agents/setup/log_agent_model.py
# Inside HealthMonitorAgent.predict()

# Extract user_id and session_id from input if provided
user_id = model_input.get("user_id") or \
         model_input.get("custom_inputs", {}).get("user_id") or \
         os.environ.get("USER_ID", "unknown")

session_id = model_input.get("session_id") or \
            model_input.get("custom_inputs", {}).get("session_id") or \
            model_input.get("thread_id") or \
            os.environ.get("SESSION_ID", "unknown")

# Update trace with standard MLflow metadata
mlflow.update_current_trace(
    metadata={
        "mlflow.trace.user": user_id,      # Links trace to specific user
        "mlflow.trace.session": session_id, # Groups traces in conversation
    },
    tags={
        "user_id": user_id,       # Also in tags for legacy compatibility
        "session_id": session_id, # Also in tags for legacy compatibility
    }
)
```

### Querying in MLflow UI

Filter traces using these search queries:

```
# Find all traces for a specific user
metadata.`mlflow.trace.user` = 'user-123'

# Find all traces in a session
metadata.`mlflow.trace.session` = 'session-abc-456'

# Find traces for a user within a specific session
metadata.`mlflow.trace.user` = 'user-123' AND metadata.`mlflow.trace.session` = 'session-abc-456'
```

### Benefits

1. **Multi-turn analysis**: Group all messages in a conversation
2. **User behavior analysis**: Track all interactions from a specific user
3. **Debugging**: Filter to specific user/session when issues are reported
4. **Metrics**: Calculate per-user or per-session statistics

---

## 📈 Metrics Logging

### Error Metrics

```python
# File: src/agents/orchestrator/graph.py

# Memory load error
except Exception as e:
    mlflow.log_metric("memory_load_error", 1)

# File: src/agents/workers/base.py

# Genie query error
except Exception as e:
    mlflow.log_metric(f"genie_{self.domain}_error", 1)
```

### Performance Metrics

```python
# Latency tracking
import time

start_time = time.time()
result = self.graph.invoke(state, config)
latency_ms = (time.time() - start_time) * 1000

mlflow.log_metric("prediction_latency_ms", latency_ms)
```

### Standard Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| `prediction_latency_ms` | Gauge | End-to-end latency |
| `memory_load_error` | Counter | Memory system health |
| `genie_{domain}_error` | Counter | Per-domain error rate |
| `classification_confidence` | Gauge | Intent clarity |
| `response_confidence` | Gauge | Answer quality |

---

## 🔬 Viewing Traces

### In Databricks UI

1. Navigate to **Experiments** → `/Shared/health_monitor/agent`
2. Click on a **Run** with traces
3. Expand the **Traces** tab
4. Click on individual spans to see details

### Programmatic Access

```python
import mlflow

# Get traces for an experiment
client = mlflow.MlflowClient()

# Search for runs with traces
runs = client.search_runs(
    experiment_ids=["<experiment_id>"],
    filter_string="tags.run_type = 'traces'",
    order_by=["start_time DESC"],
)

# Get trace details
for run in runs:
    trace = mlflow.get_trace(run_id=run.info.run_id)
    print(f"Trace: {trace.trace_id}")
    for span in trace.spans:
        print(f"  - {span.name}: {span.latency_ms}ms")
```

---

## 🧪 Testing Traces

### Verify Tracing Works

```python
# In a notebook
import mlflow
from src.agents.orchestrator.agent import HealthMonitorAgent
from mlflow.types.agent import ChatAgentMessage

# Ensure experiment is set
mlflow.set_experiment("/Shared/health_monitor/agent")

# Create agent
agent = HealthMonitorAgent()

# Make a prediction (will be traced)
with mlflow.start_run(run_name="trace_test") as run:
    response = agent.predict(
        messages=[
            ChatAgentMessage(role="user", content="What are the top 5 cost drivers?")
        ],
        custom_inputs={"thread_id": "test-trace"},
    )
    
    print(f"Run ID: {run.info.run_id}")
    print(f"Response: {response.messages[0].content}")

# View traces in UI at the run page
```

---

## ⚙️ Configuration

### Feature Flag

```python
# File: src/agents/config/settings.py
# Lines: 265-267

enable_mlflow_tracing: bool = field(
    default_factory=lambda: os.environ.get("ENABLE_MLFLOW_TRACING", "true").lower() == "true"
)
```

### Conditional Tracing

```python
if settings.enable_mlflow_tracing:
    @mlflow.trace(name="my_function", span_type="TOOL")
    def my_function():
        ...
else:
    def my_function():
        ...
```

---

## 🔧 Best Practices

### 1. Always Use Span Types

```python
# Good ✅
@mlflow.trace(name="classify", span_type="CLASSIFIER")

# Bad ❌
@mlflow.trace(name="classify")  # Missing span_type
```

### 2. Set Inputs and Outputs

```python
# Good ✅
with mlflow.start_span(name="process", span_type="TOOL") as span:
    span.set_inputs({"data": data})
    result = process(data)
    span.set_outputs({"result": result})

# Bad ❌
with mlflow.start_span(name="process"):
    result = process(data)  # No inputs/outputs captured
```

### 3. Use Consistent Naming

```python
# Good ✅ - Domain prefix, action suffix
"cost_agent_node"
"genie_cost_query"
"memory_search"

# Bad ❌ - Inconsistent
"costAgent"
"do_query"
"mem_srch"
```

### 4. Tag Traces with Context

```python
# Always tag with user and conversation context
mlflow.update_current_trace(tags={
    "user_id": user_id,
    "thread_id": thread_id,
})
```

---

**Next:** [07-configuration-management.md](./07-configuration-management.md)

