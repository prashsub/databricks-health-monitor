# Databricks Agent Framework Implementation Prompt

## Purpose
This prompt provides comprehensive guidance for implementing production-grade GenAI agents using the Databricks Agent Framework, MLflow 3.0+, and LangGraph. Use this to generate similar agent implementations.

## Architecture Overview

You are implementing a **multi-agent system** with the following architecture:

```
User Query
    ↓
Orchestrator (ResponsesAgent)
    ├─> Intent Classification
    ├─> Domain Routing
    ├─> Multi-Agent Execution (parallel)
    │   ├─> Domain Agent 1 (queries Genie)
    │   ├─> Domain Agent 2 (queries Genie)
    │   └─> Domain Agent N (queries Genie)
    └─> Response Synthesis
    ↓
Streamed Response
```

## Critical Requirements

### 1. MANDATORY: ResponsesAgent Interface

**ALL agents MUST inherit from `mlflow.pyfunc.ResponsesAgent`** for AI Playground compatibility.

```python
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

class MyAgent(ResponsesAgent):
    @mlflow.trace(name="agent_predict", span_type="AGENT")
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        # Extract query from request.input (NOT messages!)
        query = request.input[-1].get("content", "")
        
        # Process
        response_text = self._process(query)
        
        # Return ResponsesAgentResponse
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(
                text=response_text,
                id=str(uuid.uuid4())
            )]
        )
```

**Key Points:**
- Use `request.input` NOT `messages`
- Return `ResponsesAgentResponse` NOT dict
- NO `signature` parameter in `mlflow.pyfunc.log_model()`

### 2. MANDATORY: No LLM Fallback for Data Queries

**When data retrieval fails (Genie, API, etc.), return explicit error - NEVER fallback to LLM.**

```python
try:
    result = genie.invoke(query)
    return result
except Exception as e:
    # ✅ CORRECT: Return explicit error
    return f"""## Data Query Failed
**Error:** {e}
I will NOT generate fake data."""
    
    # ❌ WRONG: LLM fallback would hallucinate fake data
    # return llm.invoke(query)
```

### 3. Streaming Support

```python
def predict_stream(self, request):
    """Stream response chunks."""
    item_id = str(uuid.uuid4())
    
    for chunk in self._process_streaming(query):
        yield ResponsesAgentStreamEvent(
            type="output_item.delta",
            delta=ResponsesAgentStreamEventDelta(
                type="message_delta",
                delta=ResponsesAgentMessageContentDelta(type="text", text=chunk)
            ),
            item_id=item_id
        )
    
    yield ResponsesAgentStreamEvent(type="output_item.done", item_id=item_id)
```

### 4. MLflow Tracing

```python
@mlflow.trace(name="function_name", span_type="AGENT|TOOL|LLM|RETRIEVER|CLASSIFIER")
def traced_function(params):
    """All key functions must be traced."""
    pass
```

**Span Types:**
- `AGENT`: Agent-level operations
- `TOOL`: External tool/API calls
- `LLM`: Foundation model calls
- `RETRIEVER`: RAG/search/memory retrieval
- `CLASSIFIER`: Classification operations

### 5. Memory Pattern (Optional but Recommended)

```python
def _load_memory(self):
    """Lazy-load with graceful degradation."""
    try:
        self._short_term_memory = ShortTermMemory()
        with self._short_term_memory.get_checkpointer():
            pass  # Test if tables exist
    except:
        print("⚠ Memory unavailable, using stateless mode")
        self._short_term_memory = None
```

## Implementation Checklist

### Core Agent Class
- [ ] Inherit from `mlflow.pyfunc.ResponsesAgent`
- [ ] Implement `predict(request: ResponsesAgentRequest)`
- [ ] Return `ResponsesAgentResponse` with `create_text_output_item()`
- [ ] Input example uses `input` key (not `messages`)
- [ ] Add `@mlflow.trace` decorator

### Streaming
- [ ] Implement `predict_stream()` yielding `ResponsesAgentStreamEvent`
- [ ] Send delta events for chunks
- [ ] Send final `output_item.done` event
- [ ] `predict()` can delegate to `predict_stream()`

### Data Integration
- [ ] Integrate Genie/tool for real data access
- [ ] NO LLM fallback for data queries
- [ ] Return explicit errors when tools fail
- [ ] Add `@mlflow.trace(span_type="TOOL")` to data retrieval functions

### Multi-Agent Orchestration (if applicable)
- [ ] Define LangGraph workflow with StateGraph
- [ ] Add nodes for orchestrator, workers, synthesizer
- [ ] Implement conditional routing based on intent
- [ ] Workers execute in parallel
- [ ] Each node has `@mlflow.trace` decorator

### Evaluation
- [ ] Create evaluation dataset (JSON/CSV with queries)
- [ ] Define 4-6 focused guidelines (not 8+)
- [ ] Register custom judges with `@scorer` decorator
- [ ] Set deployment thresholds per judge
- [ ] Use consistent run naming: `eval_pre_deploy_YYYYMMDD_HHMMSS`

### Logging
- [ ] Call `mlflow.models.set_model(agent)` before logging
- [ ] NO `signature` parameter in `log_model()`
- [ ] Include input_example in ResponsesAgent format
- [ ] Specify pip_requirements with `mlflow>=3.0.0`

### Memory (optional)
- [ ] Lazy-load memory with try/except
- [ ] Graceful fallback if tables don't exist
- [ ] Return `thread_id` in `custom_outputs`
- [ ] Short-term: CheckpointSaver
- [ ] Long-term: DatabricksStore with embeddings

### Prompts
- [ ] Store in Unity Catalog `agent_config` table
- [ ] Version in MLflow as artifacts
- [ ] Load at runtime (not hardcoded)
- [ ] Support AB testing with aliases

## Code Generation Template

When generating agent code, follow this structure:

```python
# Databricks notebook source
"""
[Agent Name] - [Description]
"""

import mlflow
import uuid
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    ResponsesAgentStreamEventDelta,
    ResponsesAgentMessageContentDelta
)

# Enable autolog
mlflow.langchain.autolog()


class MyAgent(ResponsesAgent):
    """
    [Description of agent purpose and capabilities]
    
    Reference: https://mlflow.org/docs/latest/genai/serving/responses-agent
    """
    
    def __init__(self):
        super().__init__()
        # Initialize components
        self.llm_endpoint = "databricks-claude-sonnet-4-5"
        self._memory = None
        self._memory_available = True
    
    @mlflow.trace(name="predict", span_type="AGENT")
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """Non-streaming prediction."""
        # Extract query
        query = request.input[-1].get("content", "")
        custom_inputs = request.custom_inputs or {}
        
        # Process
        response_text = self._process(query, custom_inputs)
        
        # Return response
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(
                text=response_text,
                id=str(uuid.uuid4())
            )],
            custom_outputs={
                "source": "agent",
                "custom_metadata": "value"
            }
        )
    
    def predict_stream(self, request: ResponsesAgentRequest):
        """Streaming prediction."""
        query = request.input[-1].get("content", "")
        item_id = str(uuid.uuid4())
        
        for chunk in self._process_streaming(query):
            yield ResponsesAgentStreamEvent(
                type="output_item.delta",
                delta=ResponsesAgentStreamEventDelta(
                    type="message_delta",
                    delta=ResponsesAgentMessageContentDelta(type="text", text=chunk)
                ),
                item_id=item_id
            )
        
        yield ResponsesAgentStreamEvent(type="output_item.done", item_id=item_id)
    
    @mlflow.trace(name="process", span_type="AGENT")
    def _process(self, query: str, custom_inputs: dict) -> str:
        """Core processing logic."""
        # Your implementation here
        return f"Processed: {query}"
    
    def _process_streaming(self, query: str):
        """Streaming processing."""
        # Your streaming implementation
        yield "Response chunk 1"
        yield "Response chunk 2"


# ============================================================================
# LOGGING
# ============================================================================

def log_agent():
    """Log agent to MLflow."""
    agent = MyAgent()
    mlflow.models.set_model(agent)
    
    input_example = {
        "input": [{"role": "user", "content": "Test query"}],
        "custom_inputs": {"user_id": "test"}
    }
    
    with mlflow.start_run(run_name="log_agent"):
        mlflow.pyfunc.log_model(
            artifact_path="agent",
            python_model=agent,
            input_example=input_example,
            # NO signature parameter!
            registered_model_name="my_agent",
            pip_requirements=[
                "mlflow>=3.0.0",
                "databricks-sdk>=0.28.0",
            ]
        )
```

## Anti-Patterns to Avoid

### ❌ NEVER: Manual Signatures
```python
mlflow.pyfunc.log_model(signature=custom_signature)  # Breaks AI Playground!
```

### ❌ NEVER: LLM Fallback for Data
```python
try:
    data = tool.get_data()
except:
    data = llm.generate_data()  # Hallucination!
```

### ❌ NEVER: Dict Return from predict()
```python
return {"messages": [...]}  # Wrong format!
```

### ❌ NEVER: Use `messages` Key in Input
```python
input_example = {"messages": [...]}  # Should be 'input'!
```

### ❌ NEVER: Assume Memory Tables Exist
```python
memory = ShortTermMemory()  # May crash!
```

## Success Criteria

Your agent implementation is complete when:
- ✅ Agent loads in AI Playground without errors
- ✅ Streaming works in AI Playground
- ✅ Tracing appears in MLflow Experiment UI
- ✅ Evaluation runs with all judges passing thresholds
- ✅ Memory works with graceful degradation
- ✅ Data queries fail explicitly (no hallucination)
- ✅ Model registers to Unity Catalog successfully
- ✅ On-behalf-of authentication works (if configured)

## References

- [ResponsesAgent Docs](https://mlflow.org/docs/latest/genai/serving/responses-agent)
- [Databricks Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/)
- [MLflow Tracing](https://mlflow.org/docs/latest/llms/tracing/index.html)
- [LangGraph](https://langchain-ai.github.io/langgraph/)

---

**Use this prompt to generate production-grade agent implementations following Databricks best practices.**
