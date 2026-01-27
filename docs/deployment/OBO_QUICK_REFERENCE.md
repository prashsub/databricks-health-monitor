# OBO Auth Fix - Quick Reference

## 🔧 What Changed

One method in one file:
- **File**: `src/agents/setup/log_agent_model.py`
- **Method**: `_get_genie_client()`
- **Change**: Added Model Serving environment detection before attempting OBO

## 🎯 The Fix (30 Second Version)

**Before**: Agent always tried OBO → Failed outside Model Serving → Permission errors

**After**: Agent checks environment → Uses OBO in Model Serving, default auth elsewhere → Works everywhere

## ✅ Quick Verification

```python
# Run this in a notebook
from src.agents.setup.log_agent_model import HealthMonitorAgent

agent = HealthMonitorAgent()
response, _ = agent._query_genie("cost", "Show top 5 expensive jobs")

# Should see:
# → Using default workspace auth for cost Genie (evaluation/notebook mode)
# ✓ Genie response for cost (1234 chars)

print(response[:200])  # Should show actual data
```

## 📊 Expected Logs

### Evaluation/Notebook (You)
```
→ Using default workspace auth for cost Genie (evaluation/notebook mode)
```

### Model Serving (Production)
```
✓ Using on-behalf-of-user auth for cost Genie (Model Serving)
```

## 🚨 If It Still Fails

### Permission Error?
Run this to check your access:
```python
from databricks.sdk import WorkspaceClient
WorkspaceClient().genie.list_conversations(space_id="01f0ea87...")
```

If error → You need permissions:
```sql
GRANT USE ON GENIE SPACE <space_id> TO `<your_email>`;
GRANT USAGE ON WAREHOUSE <warehouse_id> TO `<your_email>`;
```

### Wrong Auth Mode?
Check environment:
```python
import os
print(f"Model Serving: {os.environ.get('IS_IN_DB_MODEL_SERVING_ENV')}")
# Should be: None or not 'true'
```

## 📖 Full Documentation

- [Complete Fix Details](./OBO_AUTH_FIX.md)
- [Summary & Next Steps](./OBO_FIX_SUMMARY.md)
- [Verification Tests](../../tests/test_obo_auth_fix.py)

## ✨ Bottom Line

**You can now run agent evaluation without permission errors!**

Just run your evaluation as normal:
```python
%run /Workspace/.../deployment_job.py
```

The agent will automatically:
- ✅ Use your credentials in evaluation
- ✅ Use end-user credentials in Model Serving
- ✅ Handle both contexts seamlessly
