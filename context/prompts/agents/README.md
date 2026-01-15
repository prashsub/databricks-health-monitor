# Agent Framework Context Prompts

Comprehensive context prompts for LLM-based code generation of Databricks GenAI agents.

## Purpose

These prompts capture production-proven patterns from the Databricks Health Monitor Agent implementation. Use them to:
- Generate similar agent implementations
- Guide LLMs in creating production-grade agents
- Ensure best practices are followed
- Avoid common mistakes and anti-patterns

## Prompt Index

| Prompt | File | Purpose | Use When |
|---|---|---|---|
| **01** | [agent-framework-overview.md](01-agent-framework-overview.md) | Complete agent implementation guidance | Generating new agent classes |
| **02** | [evaluation-and-judging.md](02-evaluation-and-judging.md) | Evaluation system with LLM judges | Setting up agent evaluation |

## Quick Reference: Critical Requirements

### For ANY Agent Implementation

1. **MANDATORY: ResponsesAgent**
   - ALL agents must inherit from `mlflow.pyfunc.ResponsesAgent`
   - NO manual `signature` parameter in `log_model()`
   - Use `request.input` (not `messages`)
   - Return `ResponsesAgentResponse` (not dict)

2. **MANDATORY: No LLM Fallback for Data**
   - When Genie/API fails, return explicit error
   - NEVER fall back to LLM for data responses
   - Prevents hallucination of fake data

3. **MANDATORY: MLflow Tracing**
   - Add `@mlflow.trace` to all key functions
   - Specify appropriate `span_type`
   - Enable tracing visibility in MLflow UI

4. **MANDATORY: Streaming Support**
   - Implement `predict_stream()` yielding events
   - Send final `output_item.done` event
   - `predict()` can delegate to `predict_stream()`

### For Evaluation Systems

1. **Guidelines: 4-6 Sections (Not 8+)**
   - Production learning: 8 sections → 0.20 score
   - Solution: 4 focused sections → 0.5+ score

2. **Custom Judges: Foundation Models**
   - Use `endpoints:/databricks-claude-sonnet-4-5`
   - NOT pay-per-token endpoints
   - Temperature = 0.0 for consistency

3. **Deployment Thresholds**
   - Define thresholds per judge
   - Check before deployment
   - Block if not met

## How to Use These Prompts

### 1. Feed to LLM as System Context

```python
# Example: Using with Claude/GPT
with open("context/prompts/agents/01-agent-framework-overview.md") as f:
    agent_prompt = f.read()

response = llm.invoke([
    {"role": "system", "content": agent_prompt},
    {"role": "user", "content": "Generate an agent that monitors security events"}
])
```

### 2. Reference During Code Review

- Check generated code against patterns in prompts
- Verify no anti-patterns present
- Ensure all critical requirements met

### 3. Onboarding New Team Members

- Share prompts as implementation guide
- Use as reference for best practices
- Point to specific sections for questions

## Generated Code Quality Checklist

Use this to validate LLM-generated agent code:

### Core Agent Class
- [ ] Inherits from `ResponsesAgent`
- [ ] Implements `predict(request: ResponsesAgentRequest)`
- [ ] Returns `ResponsesAgentResponse`
- [ ] Input example uses `input` key
- [ ] Has `@mlflow.trace` decorator

### Streaming
- [ ] Implements `predict_stream()`
- [ ] Yields `ResponsesAgentStreamEvent` objects
- [ ] Sends final `output_item.done` event

### Data Integration
- [ ] Uses Genie/API for real data
- [ ] NO LLM fallback for data queries
- [ ] Returns explicit errors on failure
- [ ] Has `@mlflow.trace(span_type="TOOL")`

### Evaluation
- [ ] 4-6 focused guidelines
- [ ] Custom judges use `@scorer` decorator
- [ ] Foundation model endpoints
- [ ] Thresholds defined
- [ ] Consistent run naming

### Logging
- [ ] Calls `mlflow.models.set_model()`
- [ ] NO `signature` parameter
- [ ] Includes input_example
- [ ] Specifies pip_requirements

## Anti-Patterns to Watch For

If LLM generates any of these, STOP and fix:

### ❌ Manual Signatures
```python
mlflow.pyfunc.log_model(signature=...)  # NEVER!
```

### ❌ LLM Fallback for Data
```python
try:
    data = genie.query()
except:
    data = llm.generate()  # NEVER!
```

### ❌ Dict Return
```python
return {"messages": [...]}  # NEVER!
```

### ❌ Wrong Input Format
```python
input_example = {"messages": [...]}  # Should be 'input'!
```

### ❌ 8+ Guidelines
```python
guidelines = [s1, s2, s3, s4, s5, s6, s7, s8]  # Too many!
```

## Success Metrics

Your agent implementation is production-ready when:

1. **Functionality**
   - ✅ Agent loads in AI Playground
   - ✅ Streaming works
   - ✅ Tracing appears in MLflow UI
   - ✅ Returns accurate data (no hallucination)

2. **Evaluation**
   - ✅ All judges pass thresholds
   - ✅ Guidelines score ≥ 0.5
   - ✅ Custom judges provide useful feedback

3. **Deployment**
   - ✅ Registers to Unity Catalog
   - ✅ On-behalf-of auth works (if configured)
   - ✅ Memory gracefully degrades if unavailable

4. **Observability**
   - ✅ Traces show detailed execution flow
   - ✅ Judge reasoning visible in MLflow
   - ✅ Errors logged with context

## Related Documentation

### Cursor Rules
- [30-mlflow-genai-evaluation.mdc](../../.cursor/rules/genai-agents/30-mlflow-genai-evaluation.mdc)
- [31-lakebase-memory-patterns.mdc](../../.cursor/rules/genai-agents/31-lakebase-memory-patterns.mdc)
- [32-prompt-registry-patterns.mdc](../../.cursor/rules/genai-agents/32-prompt-registry-patterns.mdc)
- [33-mlflow-tracing-agent-patterns.mdc](../../.cursor/rules/genai-agents/33-mlflow-tracing-agent-patterns.mdc)

### Official Docs
- [ResponsesAgent](https://mlflow.org/docs/latest/genai/serving/responses-agent)
- [Databricks Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/)
- [MLflow Evaluation](https://mlflow.org/docs/latest/llms/llm-evaluate/)
- [MLflow Tracing](https://mlflow.org/docs/latest/llms/tracing/index.html)

## Version History

- **v1.0** (Jan 14, 2026) - Initial prompts from Health Monitor Agent
  - Agent framework overview
  - Evaluation and judging patterns
  - Key learnings: Guidelines simplification, no LLM fallback, graceful degradation

---

**Use these prompts to generate production-grade agent implementations with LLM assistance.**
