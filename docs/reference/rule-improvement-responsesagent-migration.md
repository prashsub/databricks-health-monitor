# Rule Improvement Case Study: ResponsesAgent Migration for AI Playground Compatibility

**Date:** January 7, 2026
**Rule Updated:** `.cursor/rules/ml/28-mlflow-genai-patterns.mdc`
**Trigger:** Agent model would not load in Databricks AI Playground

---

## Problem Statement

The Health Monitor Agent was implemented using `mlflow.pyfunc.PythonModel` with a manually defined model signature. Despite the agent working correctly in notebooks and batch inference, it **failed to load in AI Playground**.

### Symptoms

1. AI Playground displayed "Unable to load model" error
2. Model signature mismatch warnings in deployment logs
3. Manual signature definition causing inference format issues

---

## Root Cause Analysis

### Official Documentation Discovery

From [Microsoft Docs - Create an AI Agent](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/create-agent#understand-model-signatures-to-ensure-compatibility-with-azure-databricks-features):

> "Azure Databricks uses **MLflow Model Signatures** to define agents' input and output schema. Product features like the **AI Playground assume that your agent has one of a set of supported model signatures**."

> "If you follow the **recommended approach to authoring agents**, MLflow will **automatically infer a signature** for your agent that is compatible with Azure Databricks product features, with **no additional work required** on your part."

### The Recommended Approach

From [Databricks Author Agent Docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent):

> "Databricks recommends the MLflow interface `ResponsesAgent` to create production-grade agents."

### What We Did Wrong

| Aspect | Wrong Approach | Correct Approach |
|---|---|---|
| **Base Class** | `mlflow.pyfunc.PythonModel` | `mlflow.pyfunc.ResponsesAgent` |
| **Method Signature** | `predict(self, context, model_input)` | `predict(self, request)` |
| **Input Format** | `{"messages": [...]}` | `{"input": [...]}` |
| **Output Format** | `{"messages": [...], "metadata": {...}}` | `ResponsesAgentResponse(output=[...])` |
| **Model Signature** | Manually defined `ModelSignature` | Auto-inferred (no parameter) |

---

## Implementation Changes

### Before (Broken)

```python
from mlflow.models.signature import ModelSignature
from mlflow.types.schema import Schema, ColSpec

class HealthMonitorAgent(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        # Parse messages
        messages = model_input.get("messages", [])
        query = messages[-1].get("content", "")
        
        response = self._process(query)
        
        return {
            "messages": [{"role": "assistant", "content": response}],
            "metadata": {"source": "agent"}
        }

# Manual signature (WRONG!)
input_schema = Schema([ColSpec("string", "messages")])
output_schema = Schema([
    ColSpec("string", "messages"),
    ColSpec("string", "metadata")
])
signature = ModelSignature(inputs=input_schema, outputs=output_schema)

mlflow.pyfunc.log_model(
    python_model=agent,
    signature=signature,  # ❌ This breaks AI Playground!
    ...
)
```

### After (Working)

```python
import uuid
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

class HealthMonitorAgent(ResponsesAgent):
    @mlflow.trace(name="health_monitor_agent", span_type="AGENT")
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        # Parse input (ResponsesAgent uses 'input', not 'messages')
        input_messages = [msg.model_dump() for msg in request.input]
        query = input_messages[-1].get("content", "")
        
        response = self._process(query)
        
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(
                text=response,
                id=str(uuid.uuid4())
            )],
            custom_outputs={"source": "agent"}
        )

# Input example in ResponsesAgent format
input_example = {
    "input": [{"role": "user", "content": "Why did costs spike?"}]
}

mlflow.pyfunc.log_model(
    python_model=agent,
    input_example=input_example,
    # NO signature parameter - auto-inferred!
    ...
)
```

---

## Key Technical Differences

### Input Format

| Format | Schema | Example |
|---|---|---|
| **ResponsesAgent** | `input` | `{"input": [{"role": "user", "content": "..."}]}` |
| **ChatAgent (Legacy)** | `messages` | `{"messages": [{"role": "user", "content": "..."}]}` |

### Output Format

| Format | Schema | Example |
|---|---|---|
| **ResponsesAgent** | `ResponsesAgentResponse.output` | `ResponsesAgentResponse(output=[...])` |
| **ChatAgent (Legacy)** | `messages` list | `{"messages": [{"role": "assistant", "content": "..."}]}` |

### Helper Methods (ResponsesAgent)

```python
# Text output
self.create_text_output_item(text="...", id="msg_1")

# Function call
self.create_function_call_item(id="fc_1", call_id="call_1", name="fn", arguments="{}")

# Function output
self.create_function_call_output_item(call_id="call_1", output="result")

# Streaming delta
self.create_text_delta(delta="chunk", item_id="msg_1")
```

---

## Files Modified

| File | Changes |
|---|---|
| `src/agents/setup/log_agent_model.py` | Migrated to ResponsesAgent, removed manual signature |
| `src/agents/setup/deployment_job.py` | Updated evaluation input format |
| `.cursor/rules/ml/28-mlflow-genai-patterns.mdc` | Added ResponsesAgent patterns and checklist |

---

## Impact Metrics

| Metric | Before | After |
|---|---|---|
| AI Playground Compatibility | ❌ Failed | ✅ Working |
| Signature Definition | ~20 lines manual | 0 lines (auto) |
| Input/Output Parsing | Complex | Standardized |
| Streaming Support | Manual | Built-in |
| Tool Calling Support | Manual | Built-in |

---

## Prevention: Future Checklist

Before logging any agent model:

1. [ ] Agent inherits from `mlflow.pyfunc.ResponsesAgent`
2. [ ] `predict` method signature: `predict(self, request)`
3. [ ] Returns `ResponsesAgentResponse` object
4. [ ] Input example uses `input` key (not `messages`)
5. [ ] **NO `signature` parameter** in `log_model()` call
6. [ ] Test in AI Playground before production deployment

---

## References

### Official Documentation
- [Model Signatures for Databricks Features](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/create-agent#understand-model-signatures-to-ensure-compatibility-with-azure-databricks-features)
- [Author AI Agents in Code](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent)
- [ResponsesAgent for Model Serving](https://mlflow.org/docs/latest/genai/serving/responses-agent)
- [MLflow Model Signatures](https://mlflow.org/docs/latest/ml/model/signatures/)
- [Legacy Agent Schema](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-legacy-schema)

### Key Quotes

> "Azure Databricks uses MLflow Model Signatures to define agents' input and output schema. Product features like the AI Playground assume that your agent has one of a set of supported model signatures."

> "If you follow the recommended approach to authoring agents, MLflow will automatically infer a signature for your agent that is compatible with Azure Databricks product features, with no additional work required on your part."

> "Databricks recommends the MLflow interface `ResponsesAgent` to create production-grade agents."

---

## Lessons Learned

1. **Always check official docs first** - The solution was clearly documented
2. **Auto-inference > manual definition** - Let MLflow handle signatures
3. **ResponsesAgent is the standard** - ChatAgent is legacy
4. **Test in AI Playground early** - Don't wait until production
5. **Input format matters** - `input` vs `messages` is a breaking difference




