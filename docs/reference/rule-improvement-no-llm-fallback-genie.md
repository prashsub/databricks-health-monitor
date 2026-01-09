# Rule Improvement: No LLM Fallback for Genie/Tool Calls

**Date:** January 7, 2026  
**Rule Updated:** `.cursor/rules/ml/28-mlflow-genai-patterns.mdc`  
**Severity:** 🔴 CRITICAL - Data Integrity Issue

## Problem Statement

When the Health Monitor Agent's Genie Space failed to initialize, the agent fell back to an LLM to generate a response. This caused **hallucination of completely fabricated data** that appeared authentic.

## The Incident

### User Query
```
"Which jobs failed today?"
```

### Expected Behavior
- Agent queries Genie Space for reliability domain
- Genie returns real job failure data from `system.lakeflow.job_run_timeline`
- User sees actual failed jobs

### Actual Behavior
- Genie failed to initialize (`databricks-agents` not available in serving environment)
- Agent fell back to LLM with `reliability_analyst` prompt
- LLM generated a professional-looking table with **completely fake data**:

```markdown
## Job Failures Analysis - Today

| Job Name                      | Owner       | Failure Time | Error Type          | Impact                          |
|-------------------------------|-------------|--------------|---------------------|---------------------------------|
| daily_customer_metrics        | data_team   | 07:15 AM     | Timeout Error       | High - Blocks downstream        |
| inventory_refresh             | operations  | 09:42 AM     | Resource Constraint | Medium - Delayed inventory      |
| marketing_campaign_analysis   | marketing   | 11:30 AM     | Data Quality Issue  | Medium - Campaign reporting     |
```

**None of these jobs exist.** The LLM hallucinated plausible-sounding job names, owners, and error types.

## Root Cause

The agent code had an **LLM fallback pattern**:

```python
# Try Genie
if genie:
    try:
        result = genie.invoke(query)
        return result
    except Exception:
        pass  # Continue to fallback

# ❌ FATAL: LLM fallback
response = self._call_llm(query, system_prompt=domain_prompt)
return response  # HALLUCINATED DATA
```

## The Fix

Removed LLM fallback entirely. Agent now returns **explicit error messages** when Genie fails:

```python
# Try Genie - NO LLM FALLBACK
if genie:
    try:
        result = genie.invoke(query)
        return ResponsesAgentResponse(output=[...], custom_outputs={"source": "genie"})
    except Exception as e:
        # ✅ Return error, NOT hallucinated data
        error_msg = f"""## Genie Query Failed
        
**Domain:** {domain}
**Error:** {str(e)}

I will NOT generate fake data. All responses must come from real system tables via Genie."""
        
        return ResponsesAgentResponse(output=[...], custom_outputs={"source": "error"})
else:
    # ✅ Genie not available - explicit error
    error_msg = """## Genie Space Not Available
    
**Note:** I will NOT generate fake data."""
    
    return ResponsesAgentResponse(output=[...], custom_outputs={"source": "error"})
```

## Key Learning

### The Golden Rule

> **If your agent uses Genie or any data retrieval tool, NEVER fall back to LLM for data responses. Return an explicit error instead.**

### When LLM Fallback IS Acceptable

| Scenario | LLM Fallback OK? | Reason |
|---|---|---|
| **Data queries** (jobs, costs, metrics) | ❌ **NEVER** | LLM will hallucinate fake data |
| **Explanation/interpretation** of real data | ✅ Yes | LLM explains, doesn't invent |
| **General questions** (not data-dependent) | ✅ Yes | No risk of fake data |
| **Classification/routing** | ✅ Yes | No data fabrication |

## Files Modified

- `src/agents/setup/log_agent_model.py` - Removed LLM fallback, added error handling
- `.cursor/rules/ml/28-mlflow-genai-patterns.mdc` - Added NO LLM FALLBACK section

## Impact

| Metric | Before | After |
|---|---|---|
| Risk of hallucinated data | 100% when Genie fails | 0% |
| Error visibility | Hidden (looked like success) | Explicit error message |
| User trust | Undermined by fake data | Preserved by honest errors |

## Trace Visibility

The trace now clearly shows when errors occur:

```
health_monitor_agent
├── classify_domain → reliability
└── genie_reliability → ERROR: genie_not_available
                        fallback: none (NOT "llm")
                        source: error
```

## Prevention Checklist

Before deploying any agent with tool/Genie integration:

- [ ] **NO LLM fallback** for data queries
- [ ] Clear error messages when tools fail
- [ ] "I will NOT generate fake data" statement in errors
- [ ] Errors logged to trace spans with `fallback: none`
- [ ] `custom_outputs.source` indicates "genie" or "error" (never "llm" for data)
- [ ] Test agent behavior when Genie is unavailable

## References

- [MLflow GenAI Patterns Rule](../../.cursor/rules/ml/28-mlflow-genai-patterns.mdc)
- [Databricks Genie Spaces](https://docs.databricks.com/aws/en/genie/)
- [Agent Tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/)

---

**Lesson:** A professional-looking hallucinated response is worse than an honest error. Users will take action on fake data if it looks real.




