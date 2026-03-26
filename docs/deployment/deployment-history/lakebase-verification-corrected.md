# Lakebase Verification - Corrected Guide

## ⚠️ Important Correction

**Lakebase tables are NOT exposed as Delta tables in Unity Catalog.**

- ❌ **WRONG:** Query with `SELECT * FROM catalog.schema.checkpoints`
- ✅ **CORRECT:** Query via `databricks-langchain` API (CheckpointSaver, DatabricksStore)

## What is Lakebase?

**Lakebase** is a Databricks-managed Postgres-backed storage service specifically designed for:
- Short-term memory (conversation context)
- Long-term memory (user preferences, vector embeddings)
- Stateful agent applications

**Key Characteristics:**
- Storage: Managed Postgres (not Delta tables)
- Access: Only through `databricks-langchain` Python API
- Instance-based: Each project uses a named instance (e.g., `vibe-coding-workshop-lakebase`)
- Tables: `checkpoints` and `store` (in Postgres, not Unity Catalog)

## ✅ Correct Ways to Verify Lakebase

### Option 1: Python Script (Recommended)

Run the corrected verification script:

```bash
python src/agents/setup/verify_lakebase_tables.py
```

This script uses the `databricks-langchain` API to:
1. Connect to your Lakebase instance
2. Test CheckpointSaver (short-term memory)
3. Test DatabricksStore (long-term memory)
4. Attempt write/read operations
5. Report on table existence and accessibility

**Example Output:**

```
================================================================================
  LAKEBASE TABLES VERIFICATION (Direct API)
================================================================================
  • Timestamp: 2026-01-29T16:30:00
  
  • Note: Lakebase tables are stored in managed Postgres,
  • NOT as Delta tables in Unity Catalog.
  • We query them via databricks-langchain API.

  • Lakebase Instance: vibe-coding-workshop-lakebase

================================================================================
  1. SHORT-TERM MEMORY (checkpoints table)
================================================================================
  • Lakebase Instance: vibe-coding-workshop-lakebase
  • Table: checkpoints (in Lakebase Postgres)
  • Connecting to Lakebase via CheckpointSaver...
  ✅ Connected to Lakebase successfully
  • Checkpoint retrieval works (table exists)

  ✅ Short-term memory (CheckpointSaver) is operational

================================================================================
  2. LONG-TERM MEMORY (store table)
================================================================================
  • Lakebase Instance: vibe-coding-workshop-lakebase
  • Table: store (in Lakebase Postgres)
  • Connecting to Lakebase via DatabricksStore...
  ✅ Connected to Lakebase successfully
  • Store search works (table exists)

  ✅ Long-term memory (DatabricksStore) is operational

================================================================================
  3. WRITE TEST (Table Creation)
================================================================================
  • Testing if Lakebase tables can be created/written to...
  • Attempting to write a test checkpoint...
  ✅ Successfully wrote test checkpoint
  • Test thread_id: verification_test_20260129163000
  ✅ Successfully read back test checkpoint
  ✅ Lakebase tables are fully functional!

================================================================================
  4. SUMMARY & RECOMMENDATIONS
================================================================================

  • Lakebase Status:
    Short-term Memory (checkpoints): ✅ ACCESSIBLE
    Long-term Memory (store):        ✅ ACCESSIBLE
    Write Test:                      ✅ PASSED

  ✅ Lakebase is fully operational!

  • Next Steps:
    1. Send queries to your agent endpoint
    2. Re-run this script to see checkpoint/store entries grow
    3. Monitor memory usage in your agent logs

================================================================================
  ✅ VERIFICATION COMPLETE - LAKEBASE ACCESSIBLE
================================================================================
```

### Option 2: Databricks UI (Limited Visibility)

Lakebase instances may be visible in the Databricks workspace UI:

1. Go to **Workspace Settings** or **Admin Console**
2. Look for **"Lakebase"** or **"Data Services"** section
3. Check if `vibe-coding-workshop-lakebase` instance is listed

**Note:** UI visibility depends on workspace configuration. Not all workspaces expose Lakebase management UI.

### Option 3: Agent Logs (Indirect Verification)

Check your agent endpoint logs for memory operations:

```python
# In your agent logs, you should see:
✓ Short-term memory loaded: 3 messages
✓ Saved to short-term memory (thread: abc-123)
⚠ Short-term memory disabled (Lakebase tables not initialized)  # If not working
```

**How to view logs:**
1. Go to Databricks workspace
2. Navigate to **Machine Learning** → **Serving** → **Endpoints**
3. Click your endpoint: `dev_prashanth_subrahmanyam_health_monitor_agent_dev`
4. Click **"Logs"** tab
5. Look for memory-related messages

### Option 4: Test via Agent Queries

Send queries and check if memory persists:

```python
import requests
import os

endpoint_url = "https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/dev_prashanth_subrahmanyam_health_monitor_agent_dev/invocations"
token = os.environ.get("DATABRICKS_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Query 1: Initial query with thread_id
query1 = {
    "messages": [{"role": "user", "content": "What is my total cost?"}],
    "custom_inputs": {"thread_id": "test-memory-123"}
}
response1 = requests.post(endpoint_url, json=query1, headers=headers)
print(f"Query 1: {response1.status_code}")

# Query 2: Follow-up query with SAME thread_id
query2 = {
    "messages": [{"role": "user", "content": "Show me more details about that"}],
    "custom_inputs": {"thread_id": "test-memory-123"}  # Same thread_id
}
response2 = requests.post(endpoint_url, json=query2, headers=headers)
print(f"Query 2: {response2.status_code}")

# If memory works, Query 2 should reference context from Query 1
response_text = response2.json()['choices'][0]['message']['content']
print(f"Response: {response_text}")

# Check if response shows memory of previous query
if "cost" in response_text.lower():
    print("✅ Memory is working! Agent remembered the context.")
else:
    print("⚠️  Memory may not be working - agent didn't reference previous query")
```

## ❌ What DOESN'T Work

### These SQL Queries Will FAIL:

```sql
-- ❌ WRONG: Lakebase tables are not in Unity Catalog
SELECT * FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints;
-- Error: TABLE_OR_VIEW_NOT_FOUND

-- ❌ WRONG: Not Delta tables
DESCRIBE TABLE prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints;
-- Error: TABLE_OR_VIEW_NOT_FOUND

-- ❌ WRONG: Not queryable via system tables
SELECT * FROM system.information_schema.tables WHERE table_name = 'checkpoints';
-- Returns empty (Lakebase tables not in UC)
```

### Why SQL Doesn't Work:
- Lakebase is a **separate storage system** from Unity Catalog
- Tables are in **managed Postgres**, not Delta format
- Only accessible via **databricks-langchain API**, not SQL

## Configuration in Your Deployment

Your current configuration (from deployment output):

```
Lakebase Instance: vibe-coding-workshop-lakebase
Catalog: prashanth_subrahmanyam_catalog
Schema: dev_prashanth_subrahmanyam_system_gold_agent
Endpoint: dev_prashanth_subrahmanyam_health_monitor_agent_dev
```

**Important:** The catalog and schema are for your agent model and evaluation tables, NOT for Lakebase tables. Lakebase tables are stored separately in the Lakebase Postgres instance.

## How Auto-Creation Works

From your `log_agent_model.py`:

```python
# When agent handles a query...
from databricks_langchain import CheckpointSaver

with CheckpointSaver(instance_name="vibe-coding-workshop-lakebase") as checkpointer:
    # First call to put() auto-creates 'checkpoints' table in Lakebase Postgres
    checkpointer.put(config, checkpoint, metadata)
    
    # Tables are created in Lakebase, NOT in Unity Catalog
```

**Auto-creation happens:**
1. First agent query triggers memory operations
2. `CheckpointSaver().put()` is called
3. Lakebase Postgres automatically creates `checkpoints` table
4. Similarly for `DatabricksStore` and `store` table

**No Unity Catalog involvement** - these tables never appear in UC.

## Troubleshooting

### Issue: "Instance not found" error

**Cause:** Lakebase instance name is incorrect or doesn't exist

**Solution:**
```python
# Check configured instance name
from src.agents.config.settings import settings
print(f"Lakebase Instance: {settings.lakebase_instance_name}")

# Verify in workspace
# Contact workspace admin to confirm 'vibe-coding-workshop-lakebase' exists
```

### Issue: Import error for databricks-langchain

**Cause:** Package not installed in environment

**Solution:**
```bash
pip install databricks-langchain[memory]
```

### Issue: Permission denied

**Cause:** Service principal lacks Lakebase access

**Solution:**
- Contact workspace admin
- Ensure service principal has Lakebase usage permissions
- Check if Lakebase is enabled for your workspace

### Issue: Silent memory failures (no errors but no memory)

**Cause:** Tables don't exist yet or Lakebase not configured

**Check Agent Logs:**
```
⚠ Short-term memory disabled (Lakebase tables not initialized)
```

**Solution:**
1. Send 2-3 queries to trigger table creation
2. Re-run verification script
3. If still failing, check Lakebase instance configuration

## Summary

| Verification Method | Works? | How to Use |
|---------------------|--------|------------|
| **Python API (databricks-langchain)** | ✅ Yes | `python src/agents/setup/verify_lakebase_tables.py` |
| **SQL Queries to Unity Catalog** | ❌ No | Lakebase tables not in UC |
| **Databricks UI (Lakebase section)** | ⚠️ Maybe | Depends on workspace config |
| **Agent Logs** | ✅ Yes | Check serving endpoint logs |
| **Test Queries** | ✅ Yes | Send queries with same thread_id |

## Quick Verification Command

```bash
# Run corrected verification script
python src/agents/setup/verify_lakebase_tables.py

# Expected output if working:
# ✅ VERIFICATION COMPLETE - LAKEBASE ACCESSIBLE
```

## References

- **databricks-langchain Documentation:** [GitHub](https://github.com/databricks/databricks-langchain)
- **Lakebase (Internal Databricks feature):** Contact workspace admin for details
- **Agent Memory Docs:** [Stateful Agents](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/stateful-agents)
