# OBO Authentication Fix for Evaluation

## Problem

Agent evaluation was failing with permission errors:
```
✗ Genie query failed for cost: You need "Can View" permission to perform this action.
```

Even though the user running the evaluation had proper permissions, all Genie queries were failing.

## Root Cause

The agent code was attempting to use **On-Behalf-Of-User (OBO) authentication** in all contexts, including evaluation runs. However, **OBO only works in Model Serving environments**, not in notebooks or jobs.

### What Was Happening

1. ✅ Code detected `databricks-ai-bridge` package is installed
2. ✅ Code created `WorkspaceClient(credentials_strategy=ModelServingUserCredentials())`
3. ❌ Outside Model Serving, `ModelServingUserCredentials()` produces invalid/empty credentials
4. ❌ Result: Permission denied errors, even though user has permissions

### Code Before Fix

```python
def _get_genie_client(self, domain: str):
    try:
        from databricks_ai_bridge import ModelServingUserCredentials
        # ❌ This only works in Model Serving!
        client = WorkspaceClient(credentials_strategy=ModelServingUserCredentials())
        return client
    except ImportError:
        return WorkspaceClient()  # Fallback
```

**Issue**: No check for whether we're actually in Model Serving context.

## Solution

Added Model Serving environment detection before attempting OBO:

```python
def _get_genie_client(self, domain: str):
    import os
    
    # Detect if we're in Model Serving
    is_model_serving = (
        os.environ.get("IS_IN_DB_MODEL_SERVING_ENV") == "true" or
        os.environ.get("DATABRICKS_SERVING_ENDPOINT") is not None or
        os.environ.get("MLFLOW_DEPLOYMENT_FLAVOR_NAME") == "databricks"
    )
    
    if is_model_serving:
        # Use OBO in Model Serving
        try:
            from databricks_ai_bridge import ModelServingUserCredentials
            client = WorkspaceClient(credentials_strategy=ModelServingUserCredentials())
            print(f"✓ Using on-behalf-of-user auth for {domain} Genie (Model Serving)")
            return client
        except Exception as e:
            print(f"⚠ OBO auth failed, falling back to default")
            return WorkspaceClient()
    else:
        # Use default auth in notebooks/jobs/evaluation
        print(f"→ Using default workspace auth for {domain} Genie (evaluation/notebook mode)")
        return WorkspaceClient()
```

## Environment Variables Checked

| Variable | Set In | Purpose |
|----------|--------|---------|
| `IS_IN_DB_MODEL_SERVING_ENV` | Model Serving | Primary indicator (set to "true") |
| `DATABRICKS_SERVING_ENDPOINT` | Model Serving | Contains endpoint name |
| `MLFLOW_DEPLOYMENT_FLAVOR_NAME` | MLflow deployments | Set to "databricks" |

## Behavior After Fix

### During Evaluation (Notebook/Job)
```
→ Using default workspace auth for cost Genie (evaluation/notebook mode)
→ Using default workspace auth for security Genie (evaluation/notebook mode)
...
```
- ✅ Uses your user credentials or service principal
- ✅ Queries succeed if you have permissions
- ✅ No "Can View" permission errors

### In Production Model Serving
```
✓ Using on-behalf-of-user auth for cost Genie (Model Serving)
✓ Using on-behalf-of-user auth for security Genie (Model Serving)
...
```
- ✅ Uses end-user credentials via OBO
- ✅ Respects per-user permissions
- ✅ Proper security isolation

## Verification

### Test 1: Run Evaluation

```python
# In a notebook
from src.agents.setup.deployment_job import run_evaluation
import pandas as pd

# Create test data
eval_data = pd.DataFrame({
    "query": ["What are the top 10 expensive jobs?"],
    "category": ["cost"],
    "difficulty": ["moderate"]
})

# Run evaluation - should now work without permission errors
results = run_evaluation(model, eval_data)
print(f"Success rate: {results['passed_count']} / {results['total_count']}")
```

**Expected output**:
```
→ Using default workspace auth for cost Genie (evaluation/notebook mode)
✓ Genie response for cost (1234 chars)
```

### Test 2: Test in Model Serving (After Deployment)

```python
# Query deployed endpoint
import mlflow.deployments

client = mlflow.deployments.get_deploy_client("databricks")
response = client.predict(
    endpoint="health_monitor_agent",
    inputs={
        "messages": [{"role": "user", "content": "Show cost trends"}],
        "custom_inputs": {"user_id": "test@company.com"}
    }
)
```

**Expected in endpoint logs**:
```
✓ Using on-behalf-of-user auth for cost Genie (Model Serving)
```

### Test 3: Check Environment Detection

```python
# Run in notebook to verify detection
import os

is_model_serving = (
    os.environ.get("IS_IN_DB_MODEL_SERVING_ENV") == "true" or
    os.environ.get("DATABRICKS_SERVING_ENDPOINT") is not None or
    os.environ.get("MLFLOW_DEPLOYMENT_FLAVOR_NAME") == "databricks"
)

print(f"Model Serving detected: {is_model_serving}")
# Should print: Model Serving detected: False (in notebook)
```

## Files Changed

- `src/agents/setup/log_agent_model.py` - Updated `_get_genie_client()` method

## Related Documentation

- [Databricks Agent Authentication](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication)
- [On-Behalf-Of-User Authentication](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#on-behalf-of-user-authentication)
- [OBO Authentication Guide](../agent-framework-design/obo-authentication-guide.md)

## Troubleshooting

### Still Getting Permission Errors?

**Check 1: Verify you have Genie Space permissions**
```python
from databricks.sdk import WorkspaceClient
client = WorkspaceClient()

space_id = "01f0ea87..."  # Your Genie Space ID
try:
    conversations = client.genie.list_conversations(space_id=space_id)
    print("✓ You have access to Genie Space")
except Exception as e:
    print(f"✗ No access: {e}")
```

**Check 2: Verify SQL Warehouse permissions**
```python
warehouse_id = "<your_warehouse_id>"
try:
    warehouse = client.warehouses.get(warehouse_id)
    print(f"✓ Can view warehouse: {warehouse.name}")
except Exception as e:
    print(f"✗ Cannot view warehouse: {e}")
```

**Check 3: Test Genie query directly**
```python
response = client.genie.start_conversation_and_wait(
    space_id=space_id,
    content="Show me cost trends"
)
print(f"Response: {response}")
```

### Environment Variable Not Set in Model Serving?

If OBO isn't being detected in Model Serving, check:

1. **Databricks runtime version** - OBO requires runtime 14.3+
2. **Model Serving type** - Must be "Serverless" or "GPU" (not "Classic")
3. **Auth configuration** - Endpoint must have OBO enabled in settings

### databricks-ai-bridge Not Found?

Install it in your cluster/environment:
```bash
%pip install databricks-ai-bridge
dbutils.library.restartPython()
```

## Success Metrics

After this fix, you should see:

- ✅ **Evaluation runs** complete without permission errors
- ✅ **Genie queries** return actual data and analysis
- ✅ **Scorers** can evaluate responses properly
- ✅ **Model Serving** continues to use OBO for user-specific permissions

---

**Fix Applied**: January 27, 2026  
**Files Modified**: `src/agents/setup/log_agent_model.py`  
**Issue**: OBO attempted outside Model Serving context  
**Resolution**: Added environment detection before OBO authentication
