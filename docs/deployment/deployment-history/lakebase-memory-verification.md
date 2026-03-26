# Lakebase Memory Verification Guide

## Overview

The Health Monitor Agent uses **Lakebase** for stateful memory storage. Lakebase provides two types of memory:

1. **Short-term Memory (checkpoints table)** - Conversation context (24h retention)
2. **Long-term Memory (store table)** - User preferences and insights (1yr retention)

## Key Behavior: Auto-Initialization

**IMPORTANT:** Lakebase memory tables **auto-create on first agent query**. This means:

✅ **Expected Behavior:**
- After deployment, tables DON'T exist yet
- First agent conversation triggers table creation
- Tables initialize with correct schemas automatically
- Memory ops silently skip until tables exist (no errors logged)

❌ **Common Misconception:**
- Tables should exist immediately after deployment (FALSE)
- Missing tables indicate a problem (FALSE - expected!)
- Need manual table creation (FALSE - optional only)

## Your Deployment Status

Based on your deployment output:

```
Lakebase Instance: vibe-coding-workshop-lakebase
Schema: dev_prashanth_subrahmanyam_system_gold_agent
Endpoint: dev_prashanth_subrahmanyam_health_monitor_agent_dev

Memory Status: ✅ ENABLED (tables auto-initialize on first use)

⚠️  If tables don't exist: Memory ops silently skipped until
   first conversation creates them (no errors logged)
```

## Verification Steps

### Option 1: Automated Verification Script (Recommended)

Run the comprehensive verification script:

```bash
cd /Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My\ Drive/DSA/DatabricksHealthMonitor

databricks bundle exec python src/agents/setup/verify_lakebase_memory.py
```

**What it checks:**
1. ✅ Lakebase instance accessibility
2. ✅ Short-term memory table (checkpoints) existence and schema
3. ✅ Long-term memory table (store) existence and schema
4. ✅ Write permissions to schema
5. ✅ Provides actionable next steps

**Expected Output (New Deployment):**

```
════════════════════════════════════════════════════════════════════════════════
  LAKEBASE MEMORY VERIFICATION
════════════════════════════════════════════════════════════════════════════════
  • Starting verification checks...
  • Timestamp: 2026-01-29T10:30:00
  • Lakebase Instance: vibe-coding-workshop-lakebase
  • Unity Catalog Schema: prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent
  • Agent Endpoint: dev_prashanth_subrahmanyam_health_monitor_agent_dev

════════════════════════════════════════════════════════════════════════════════
  2. SHORT-TERM MEMORY (CheckpointSaver)
════════════════════════════════════════════════════════════════════════════════
  • Purpose: Conversation threads (24h retention)
  • Expected Table: prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints
  • Lakebase Instance: vibe-coding-workshop-lakebase

  ⚠️  Table does not exist yet
  • Auto-creates on first agent conversation
  • This is EXPECTED behavior for new deployments

════════════════════════════════════════════════════════════════════════════════
  3. LONG-TERM MEMORY (DatabricksStore)
════════════════════════════════════════════════════════════════════════════════
  • Purpose: User preferences (1yr retention)
  • Expected Table: prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.store
  • Lakebase Instance: vibe-coding-workshop-lakebase

  ⚠️  Table does not exist yet
  • Auto-creates on first agent conversation
  • This is EXPECTED behavior for new deployments

════════════════════════════════════════════════════════════════════════════════
  4. WRITE PERMISSIONS TEST
════════════════════════════════════════════════════════════════════════════════
  • Creating test table: prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.memory_test_20260129103000
  ✅ Can create tables in schema
  • Writing test data...
  ✅ Can write data to tables
  • Reading test data...
  ✅ Can read data from tables (found 1 rows)
  • Cleaning up test table...
  ✅ Can delete tables from schema

  ✅ All write permissions verified!

════════════════════════════════════════════════════════════════════════════════
  5. SUMMARY & NEXT STEPS
════════════════════════════════════════════════════════════════════════════════

  • Memory Configuration Status:
    Short-term Memory (checkpoints): ⚠️  NOT CREATED YET
    Long-term Memory (store):        ⚠️  NOT CREATED YET
    Write Permissions:               ✅ VERIFIED

  ⚠️  Memory tables not created yet (EXPECTED for new deployments)

  • To initialize memory tables:

    OPTION 1: Query the Agent (Recommended)
      • Send 2-3 test queries to your deployed agent endpoint
      • Tables auto-create on first conversation
      • Re-run this script to verify tables were created

    OPTION 2: Manual Initialization (Advanced)
      • Run: databricks bundle exec python src/agents/setup/initialize_lakebase_tables.py
      • This pre-creates tables with correct schemas

  • After initialization, re-run this verification script:
      python src/agents/setup/verify_lakebase_memory.py

════════════════════════════════════════════════════════════════════════════════
  ⚠️  VERIFICATION COMPLETE - TABLES NEED INITIALIZATION
════════════════════════════════════════════════════════════════════════════════
```

### Option 2: Manual SQL Verification

If you prefer to check manually using SQL:

```sql
-- 1. Check if checkpoints table exists
DESCRIBE TABLE prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints;

-- 2. Check if store table exists
DESCRIBE TABLE prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.store;

-- 3. Check row counts (if tables exist)
SELECT 'checkpoints' as table_name, COUNT(*) as row_count 
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints
UNION ALL
SELECT 'store' as table_name, COUNT(*) as row_count 
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.store;

-- 4. View recent checkpoints (conversation threads)
SELECT 
    thread_id,
    checkpoint_id,
    created_at,
    type
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints
ORDER BY created_at DESC
LIMIT 10;

-- 5. View long-term memory entries (user preferences)
SELECT 
    namespace,
    key,
    updated_at
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.store
ORDER BY updated_at DESC
LIMIT 10;
```

**Expected Results:**
- **Before first query:** `TABLE_OR_VIEW_NOT_FOUND` error (EXPECTED!)
- **After first query:** Tables exist with 0+ rows

### Option 3: Manual Table Initialization (Advanced)

If you want to pre-create tables before testing:

```bash
databricks bundle exec python src/agents/setup/initialize_lakebase_tables.py
```

This script:
1. ✅ Verifies schema permissions
2. ✅ Creates `checkpoints` table with correct schema
3. ✅ Creates `store` table with correct schema
4. ✅ Sets proper retention policies
5. ✅ Adds table properties for Lakebase integration

**When to use manual initialization:**
- Testing memory functionality before production deployment
- Troubleshooting auto-creation issues
- Pre-validating table schemas

## Testing Memory Functionality

After tables are created (auto or manual), test that memory is working:

### Step 1: Send Test Queries to Agent

Use AI Playground or API:

```python
import requests
import os

# Your endpoint URL from deployment
endpoint_url = "https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/dev_prashanth_subrahmanyam_health_monitor_agent_dev/invocations"

# Get token
token = os.environ.get("DATABRICKS_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Test conversation with multiple turns
queries = [
    {"messages": [{"role": "user", "content": "What is my total Databricks cost this month?"}]},
    {"messages": [{"role": "user", "content": "Which workspace is spending the most?"}]},
    {"messages": [{"role": "user", "content": "Show me failed jobs in the last 24 hours"}]}
]

for i, query in enumerate(queries, 1):
    print(f"\n🔹 Query {i}...")
    response = requests.post(endpoint_url, json=query, headers=headers)
    print(f"Status: {response.status_code}")
    if response.ok:
        print(f"Response: {response.json()['choices'][0]['message']['content'][:200]}...")
```

### Step 2: Verify Memory Writes

After sending 2-3 queries, check that data was written:

```sql
-- Check short-term memory (conversation context)
SELECT 
    COUNT(*) as conversation_count,
    COUNT(DISTINCT thread_id) as unique_threads
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints;

-- Check long-term memory (user preferences)
SELECT 
    COUNT(*) as preference_count,
    COUNT(DISTINCT namespace) as unique_namespaces
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.store;
```

**Expected Results:**
- `checkpoints` table: 1+ rows per conversation turn
- `store` table: 0+ rows (grows as agent learns preferences)

### Step 3: Test Memory Recall

Send a follow-up query that references earlier conversation:

```python
# This should show memory is working
query = {
    "messages": [
        {"role": "user", "content": "Remind me what we discussed about costs earlier"}
    ]
}

response = requests.post(endpoint_url, json=query, headers=headers)
print(response.json()['choices'][0]['message']['content'])
```

**Success Criteria:**
- Agent references previous cost discussion
- Agent maintains conversation context across turns
- Short-term memory table shows new checkpoints

## Troubleshooting

### Issue 1: Tables Not Auto-Creating

**Symptoms:**
- Sent multiple queries to agent
- Tables still don't exist after 5+ minutes

**Possible Causes:**
1. Permission issue (agent service principal lacks CREATE TABLE)
2. Lakebase instance misconfiguration
3. Schema doesn't exist

**Solution:**
```bash
# 1. Run verification script to check permissions
databricks bundle exec python src/agents/setup/verify_lakebase_memory.py

# 2. Check write permissions test output
# If FAILED, grant permissions:
# - CREATE TABLE on schema
# - INSERT, SELECT on schema

# 3. Try manual initialization
databricks bundle exec python src/agents/setup/initialize_lakebase_tables.py

# 4. Verify tables were created
databricks bundle exec python src/agents/setup/verify_lakebase_memory.py
```

### Issue 2: Tables Exist But No Data Written

**Symptoms:**
- Tables exist (DESCRIBE TABLE succeeds)
- Row count is 0 after multiple queries
- Agent responds but doesn't remember context

**Possible Causes:**
1. Agent code not configured to use Lakebase
2. Lakebase instance name mismatch
3. Memory ops failing silently

**Solution:**
```bash
# 1. Check agent configuration
python -c "
from src.agents.config.settings import settings
print(f'Lakebase Instance: {settings.lakebase_instance_name}')
print(f'Memory Schema: {settings.memory_schema}')
print(f'Short-term TTL: {settings.short_term_memory_ttl_hours}h')
print(f'Long-term TTL: {settings.long_term_memory_ttl_days}d')
"

# 2. Check deployment used correct settings
# Look for "Memory Configuration" section in deployment logs

# 3. Test with verbose logging
# Add DEBUG logging to agent and re-deploy
```

### Issue 3: Permission Denied Errors

**Symptoms:**
- `PermissionDenied` or `PERMISSION_DENIED` in logs
- Tables exist but cannot write

**Solution:**
```sql
-- Grant permissions to agent service principal
GRANT CREATE TABLE ON SCHEMA prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent 
TO `your-service-principal@company.com`;

GRANT SELECT, INSERT, UPDATE ON SCHEMA prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent 
TO `your-service-principal@company.com`;

-- Verify grants
SHOW GRANTS ON SCHEMA prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent;
```

## Memory Table Schemas

### Short-Term Memory (checkpoints)

```sql
CREATE TABLE checkpoints (
    thread_id STRING NOT NULL,           -- Conversation thread identifier
    checkpoint_ns STRING NOT NULL,       -- Checkpoint namespace (agent name)
    checkpoint_id STRING NOT NULL,       -- Unique checkpoint ID (timestamp-based)
    parent_checkpoint_id STRING,         -- Previous checkpoint in thread
    type STRING,                         -- Checkpoint type (langgraph metadata)
    checkpoint STRING,                   -- Serialized conversation state (JSON)
    metadata STRING,                     -- Additional metadata (JSON)
    created_at TIMESTAMP,                -- When checkpoint was created
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id) NOT ENFORCED
);
```

**Retention:** 24 hours (automatic cleanup via Delta properties)

### Long-Term Memory (store)

```sql
CREATE TABLE store (
    namespace STRING NOT NULL,           -- Namespace (user ID or domain)
    key STRING NOT NULL,                 -- Preference key (e.g., "favorite_workspace")
    value STRING,                        -- Preference value (JSON serialized)
    created_at TIMESTAMP,                -- When preference was first stored
    updated_at TIMESTAMP,                -- Last update timestamp
    PRIMARY KEY (namespace, key) NOT ENFORCED
);
```

**Retention:** 1 year (automatic cleanup via Delta properties)

## Monitoring Memory Health

### Daily Health Check Queries

```sql
-- 1. Check table sizes
SELECT 
    'checkpoints' as table_name,
    COUNT(*) as rows,
    COUNT(DISTINCT thread_id) as unique_threads,
    MAX(created_at) as latest_activity
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints
UNION ALL
SELECT 
    'store' as table_name,
    COUNT(*) as rows,
    COUNT(DISTINCT namespace) as unique_namespaces,
    MAX(updated_at) as latest_activity
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.store;

-- 2. Check retention is working (should only see recent data)
SELECT 
    DATE(created_at) as date,
    COUNT(*) as checkpoint_count
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 3. Check for orphaned threads (no recent activity)
SELECT 
    thread_id,
    COUNT(*) as checkpoint_count,
    MAX(created_at) as last_activity,
    DATEDIFF(HOUR, MAX(created_at), CURRENT_TIMESTAMP()) as hours_since_last_activity
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints
GROUP BY thread_id
HAVING hours_since_last_activity > 24
ORDER BY hours_since_last_activity DESC;
```

## References

- **Lakebase Documentation:** Internal Databricks feature (check workspace docs)
- **LangGraph Checkpointing:** [Official Docs](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- **Agent Framework Memory:** [Databricks Agent Docs](https://docs.databricks.com/aws/en/generative-ai/agent-framework/)
- **Deployment Job Code:** `src/agents/setup/deployment_job.py`
- **Agent Configuration:** `src/agents/config/settings.py`

## Quick Reference

| Task | Command |
|---|---|
| **Verify memory setup** | `databricks bundle exec python src/agents/setup/verify_lakebase_memory.py` |
| **Initialize tables manually** | `databricks bundle exec python src/agents/setup/initialize_lakebase_tables.py` |
| **Check if tables exist** | `DESCRIBE TABLE <catalog>.<schema>.checkpoints` |
| **View conversation history** | `SELECT * FROM <catalog>.<schema>.checkpoints ORDER BY created_at DESC LIMIT 10` |
| **View user preferences** | `SELECT * FROM <catalog>.<schema>.store ORDER BY updated_at DESC LIMIT 10` |
| **Check row counts** | `SELECT COUNT(*) FROM <catalog>.<schema>.checkpoints` |

## Next Steps

1. ✅ **Run Verification Script**
   ```bash
   databricks bundle exec python src/agents/setup/verify_lakebase_memory.py
   ```

2. ✅ **Send Test Queries** (if tables don't exist)
   - Use AI Playground or API to send 2-3 test queries
   - This triggers auto-creation of memory tables

3. ✅ **Re-run Verification** (after test queries)
   ```bash
   databricks bundle exec python src/agents/setup/verify_lakebase_memory.py
   ```

4. ✅ **Monitor Memory Health**
   - Add SQL queries to your monitoring dashboard
   - Set up alerts for stale data or permission issues

---

**Need Help?**
- Check deployment logs for memory configuration errors
- Review agent service principal permissions
- Contact Databricks support if Lakebase instance issues persist
