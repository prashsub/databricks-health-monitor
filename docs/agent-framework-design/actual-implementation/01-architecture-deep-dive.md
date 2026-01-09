# 01 - Architecture Deep Dive

## Overview

This document provides a detailed technical walkthrough of the Health Monitor Agent architecture, with exact file paths and code references.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Model Serving Endpoint                               │
│                    health_monitor_agent_dev                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    HealthMonitorAgent (ChatAgent)                     │  │
│  │                    src/agents/orchestrator/agent.py                   │  │
│  │                                                                       │  │
│  │  predict(messages, context)                                           │  │
│  │      │                                                                │  │
│  │      ▼                                                                │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │              LangGraph StateGraph                              │   │  │
│  │  │              src/agents/orchestrator/graph.py                  │   │  │
│  │  │                                                                │   │  │
│  │  │  START ──► load_context ──► classify_intent ──► route_to_agents│   │  │
│  │  │                                    │                           │   │  │
│  │  │                    ┌───────────────┼───────────────┐           │   │  │
│  │  │                    ▼               ▼               ▼           │   │  │
│  │  │            cost_agent     security_agent    reliability_agent  │   │  │
│  │  │            quality_agent  performance_agent                    │   │  │
│  │  │                    │               │               │           │   │  │
│  │  │                    └───────────────┼───────────────┘           │   │  │
│  │  │                                    ▼                           │   │  │
│  │  │                            synthesize_response ──► END         │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │  Short-Term Memory │  │  Long-Term Memory  │  │   Genie Spaces     │   │
│  │  CheckpointSaver   │  │  DatabricksStore   │  │   (Data Layer)     │   │
│  │  memory/short_term │  │  memory/long_term  │  │   tools/genie_tool │   │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Genie Spaces (6 domains)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Cost Space       │ Security Space   │ Performance Space                    │
│  01f0ea871ffe...  │ 01f0ea9367f2...  │ 01f0ea93671e...                      │
├───────────────────┼──────────────────┼──────────────────────────────────────┤
│  Reliability Space│ Quality Space    │ Unified Health Space                 │
│  01f0ea8724fd...  │ 01f0ea93616c...  │ 01f0ea9368801...                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Dependencies

### Import Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                        src/agents/__init__.py                         │
│  - Enables mlflow.langchain.autolog()                                 │
│  - Sets default MLflow experiment                                     │
│  - Exports settings and lazy agent import                             │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   config/    │ │ orchestrator/│ │   workers/   │
            │   settings   │ │   agent      │ │   base       │
            │   genie_     │ │   graph      │ │   cost_agent │
            │   spaces     │ │   state      │ │   etc.       │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │              │ │   memory/    │ │   tools/     │
            │ (env vars)   │ │ short_term   │ │ genie_tool   │
            │              │ │ long_term    │ │ web_search   │
            └──────────────┘ └──────────────┘ └──────────────┘
```

### Key Import Statements

**`src/agents/__init__.py`** (Lines 1-25)
```python
import mlflow

# CRITICAL: Enable autolog at module level
try:
    mlflow.langchain.autolog()
except Exception as e:
    print(f"⚠ MLflow autolog not available: {e}")

from .config.settings import settings

# Set default experiment for agent traces
mlflow.set_experiment(settings.mlflow_experiment_path)
```

**`src/agents/orchestrator/agent.py`** (Lines 10-48)
```python
from mlflow.pyfunc import ChatAgent
from mlflow.types.agent import ChatAgentMessage, ChatAgentResponse, ChatContext
from databricks.sdk import WorkspaceClient

# Import MLflow resources for automatic authentication passthrough
from mlflow.models.resources import (
    DatabricksServingEndpoint,
    DatabricksGenieSpace,
    DatabricksSQLWarehouse,
)

from .graph import create_orchestrator_graph
from .state import create_initial_state
from ..memory import get_checkpoint_saver, ShortTermMemory
from ..config import settings
```

---

## 🔄 Request Flow

### Step-by-Step Trace

```
1. HTTP Request arrives at Model Serving endpoint
   │
   ▼
2. HealthMonitorAgent.predict() called
   │  File: src/agents/orchestrator/agent.py:127
   │  - Resolves thread_id for conversation continuity
   │  - Resolves user_id from context
   │  - Creates initial state
   │
   ▼
3. LangGraph invoked with config
   │  File: src/agents/orchestrator/agent.py:170
   │  - config = {"configurable": {"thread_id": thread_id}}
   │  - result = self.graph.invoke(state, config)
   │
   ▼
4. load_context node executes
   │  File: src/agents/orchestrator/graph.py:31
   │  - Retrieves user preferences from long-term memory
   │  - Adds memory_context to state
   │
   ▼
5. classify_intent node executes
   │  File: src/agents/orchestrator/graph.py:68
   │  - LLM classifies query into domains
   │  - Returns {"intent": {"domains": [...], "confidence": 0.9}}
   │
   ▼
6. route_to_agents conditional edge
   │  File: src/agents/orchestrator/graph.py:87
   │  - Routes to single domain or parallel execution
   │
   ▼
7. Worker agent(s) execute
   │  File: src/agents/workers/{domain}_agent.py
   │  - Enhances query with domain context
   │  - Queries Genie Space via GenieAgent
   │  - Returns domain results
   │
   ▼
8. synthesize_response node executes
   │  File: src/agents/orchestrator/graph.py:175
   │  - Combines results from all workers
   │  - Generates coherent response
   │
   ▼
9. Response returned to user
   │  File: src/agents/orchestrator/agent.py:183
   │  - ChatAgentResponse with message and metadata
```

---

## 📊 State Management

### AgentState TypedDict

**File:** `src/agents/orchestrator/state.py`

```python
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    """
    State passed through the agent graph.
    
    Extends MessagesState to include conversation messages.
    """
    
    # Core identifiers
    user_id: str                       # User identifier
    thread_id: str                     # Conversation thread ID
    
    # Query processing
    query: str                         # Original user query
    intent: Dict[str, Any]            # Classification result
    
    # Memory context
    memory_context: Dict[str, Any]    # User preferences, role, history
    
    # Worker results
    worker_results: Dict[str, Any]    # Results from domain workers
    
    # Final output
    response: str                      # Synthesized response
    confidence: float                  # Overall confidence score
    sources: List[str]                # Data sources used
```

### State Flow Diagram

```
Initial State                After classify_intent
─────────────────           ─────────────────────
{                           {
  user_id: "user@...",        user_id: "user@...",
  thread_id: "abc123",        thread_id: "abc123",
  query: "Why cost?",         query: "Why cost?",
  intent: {},          ──►    intent: {
  memory_context: {},           "domains": ["COST"],
  worker_results: {},           "confidence": 0.95
  ...                         },
}                             memory_context: {...},
                              ...
                            }

After worker execution       Final State
──────────────────────      ───────────────────────
{                           {
  ...                         ...
  worker_results: {           worker_results: {...},
    "cost": {                 response: "Cost spiked
      "response": "...",       due to increased DBU
      "confidence": 0.9,       usage in workspace X",
      "sources": [...]        confidence: 0.92,
    }                         sources: ["fact_usage"]
  },                        }
  ...
}
```

---

## 🔌 External Integrations

### 1. Databricks Model Serving

**Entry Point:** `src/agents/orchestrator/agent.py`

```python
class HealthMonitorAgent(ChatAgent):
    """
    Implements MLflow ChatAgent for Model Serving deployment.
    """
    
    def predict(
        self,
        context: Optional[ChatContext] = None,
        messages: List[ChatAgentMessage] = None,
        custom_inputs: Optional[Dict] = None,
    ) -> ChatAgentResponse:
        # ... implementation
```

### 2. Genie Spaces (via GenieAgent)

**Integration Point:** `src/agents/tools/genie_tool.py`

```python
from databricks_langchain.genie import GenieAgent

class GenieTool(BaseTool):
    @property
    def genie_agent(self):
        if self._genie_agent is None:
            self._genie_agent = GenieAgent(
                genie_space_id=self.genie_space_id,
                genie_agent_name=f"{self.name}",
            )
        return self._genie_agent
```

### 3. Lakebase Memory

**Short-term:** `src/agents/memory/short_term.py`
```python
from databricks_langchain import CheckpointSaver

with CheckpointSaver(instance_name=instance_name) as saver:
    graph = workflow.compile(checkpointer=saver)
```

**Long-term:** `src/agents/memory/long_term.py`
```python
from databricks_langchain import DatabricksStore

store = DatabricksStore(
    instance_name=instance_name,
    embedding_endpoint=embedding_endpoint,
    embedding_dims=embedding_dims,
)
```

### 4. MLflow Tracking

**Experiment:** `/Shared/health_monitor/agent`

All MLflow operations are centralized:
- Model logging: `run_type=model_logging`
- Evaluation: `run_type=evaluation`
- Deployment: `run_type=deployment`
- Traces: `run_type=traces`

---

## 🗄️ Unity Catalog Resources

### Schema Structure

```
prashanth_subrahmanyam_catalog
└── dev_prashanth_subrahmanyam_system_gold_agent
    │
    ├── MODELS
    │   └── health_monitor_agent        # Registered model
    │
    ├── TABLES (Structured Data)
    │   ├── inference_request_logs      # Request logging
    │   ├── inference_response_logs     # Response logging
    │   ├── evaluation_results          # Evaluation metrics
    │   └── ab_test_assignments         # A/B testing data
    │
    └── VOLUMES (Unstructured Data)
        ├── runbooks/                   # RAG knowledge base
        ├── embeddings/                 # Vector embeddings
        └── artifacts/                  # Model artifacts
```

### MLflow Resources Declaration

**File:** `src/agents/orchestrator/agent.py` (Lines 250-290)

```python
def get_mlflow_resources() -> list:
    """
    Declare MLflow resources for automatic authentication passthrough.
    
    These resources are automatically authenticated when the model
    is deployed to Model Serving.
    """
    resources = []
    
    # Genie Spaces
    for domain in ["cost", "security", "performance", "reliability", "quality", "unified"]:
        space_id = settings.get_genie_space_id(domain)
        if space_id and DatabricksGenieSpace:
            resources.append(DatabricksGenieSpace(genie_space_id=space_id))
    
    # SQL Warehouse
    if settings.warehouse_id and DatabricksSQLWarehouse:
        resources.append(DatabricksSQLWarehouse(warehouse_id=settings.warehouse_id))
    
    # LLM Endpoint
    if DatabricksServingEndpoint:
        resources.append(DatabricksServingEndpoint(endpoint_name=settings.llm_endpoint))
    
    # Lakebase (if available)
    if _HAS_LAKEBASE_RESOURCE and settings.lakebase_instance_name:
        resources.append(DatabricksLakebase(instance_name=settings.lakebase_instance_name))
    
    return resources
```

---

## 🔐 Authentication Flow

### Automatic Authentication Passthrough

```
┌─────────────────────────────────────────────────────────────────┐
│                     Model Serving Container                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Model loaded with declared resources:                       │
│     - DatabricksGenieSpace (6 spaces)                           │
│     - DatabricksSQLWarehouse                                    │
│     - DatabricksServingEndpoint (LLM)                           │
│     - DatabricksLakebase                                        │
│                                                                 │
│  2. Databricks automatically provisions credentials:            │
│     - OAuth tokens for each resource                            │
│     - Automatic token refresh                                   │
│     - No manual credential management                           │
│                                                                 │
│  3. Runtime access:                                             │
│     - GenieAgent queries → auto-authenticated                   │
│     - DatabricksStore calls → auto-authenticated                │
│     - LLM endpoint calls → auto-authenticated                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Key Files Reference

| Component | File | Line Numbers |
|-----------|------|--------------|
| Main Agent Class | `src/agents/orchestrator/agent.py` | 50-210 |
| Graph Definition | `src/agents/orchestrator/graph.py` | 1-318 |
| State TypedDict | `src/agents/orchestrator/state.py` | 1-50 |
| Intent Classifier | `src/agents/orchestrator/intent_classifier.py` | 52-160 |
| Response Synthesizer | `src/agents/orchestrator/synthesizer.py` | 1-150 |
| Base Worker | `src/agents/workers/base.py` | 20-200 |
| Genie Tool | `src/agents/tools/genie_tool.py` | 36-200 |
| Short-term Memory | `src/agents/memory/short_term.py` | 40-187 |
| Long-term Memory | `src/agents/memory/long_term.py` | 65-441 |
| Settings | `src/agents/config/settings.py` | 21-318 |
| Genie Spaces Config | `src/agents/config/genie_spaces.py` | 48-350 |

---

**Next:** [02-core-agent-implementation.md](./02-core-agent-implementation.md)


