# Lakebase Memory - Quick Check

## TL;DR - How to Verify Memory is Working

### 1️⃣ Run the Verification Script (2 minutes)

```bash
cd /Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My\ Drive/DSA/DatabricksHealthMonitor

databricks bundle exec python src/agents/setup/verify_lakebase_memory.py
```

### 2️⃣ Interpret Results

#### ✅ **GOOD** - Tables Exist
```
Short-term Memory (checkpoints): ✅ EXISTS
Long-term Memory (store):        ✅ EXISTS
Write Permissions:               ✅ VERIFIED

✅ VERIFICATION COMPLETE - MEMORY FULLY OPERATIONAL
```

**Action:** Memory is working! No action needed.

---

#### ⚠️ **EXPECTED** - Tables Don't Exist Yet (New Deployment)
```
Short-term Memory (checkpoints): ⚠️  NOT CREATED YET
Long-term Memory (store):        ⚠️  NOT CREATED YET
Write Permissions:               ✅ VERIFIED

⚠️  VERIFICATION COMPLETE - TABLES NEED INITIALIZATION
```

**Action:** Send 2-3 test queries to your agent endpoint, then re-run verification.

**Test Query Example:**
```bash
# Use AI Playground at:
# https://e2-demo-field-eng.cloud.databricks.com/ml/playground?endpointName=dev_prashanth_subrahmanyam_health_monitor_agent_dev

# Or via API:
curl -X POST \
  "https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/dev_prashanth_subrahmanyam_health_monitor_agent_dev/invocations" \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is my total Databricks cost this month?"}
    ]
  }'
```

---

#### ❌ **BAD** - Permission Issue
```
Short-term Memory (checkpoints): ⚠️  NOT CREATED YET
Long-term Memory (store):        ⚠️  NOT CREATED YET
Write Permissions:               ❌ FAILED

❌ VERIFICATION FAILED - PERMISSIONS ISSUE
```

**Action:** Grant permissions to your service principal:

```sql
GRANT CREATE TABLE ON SCHEMA prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent 
TO `your-service-principal@company.com`;

GRANT SELECT, INSERT, UPDATE ON SCHEMA prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent 
TO `your-service-principal@company.com`;
```

Then re-run verification.

---

## Quick SQL Checks (Optional)

### Check if Tables Exist
```sql
-- This should return table schema (not error)
DESCRIBE TABLE prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints;
```

### Check Row Counts
```sql
SELECT COUNT(*) FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.checkpoints;
SELECT COUNT(*) FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.store;
```

**Expected:**
- **Before first query:** `TABLE_OR_VIEW_NOT_FOUND` (NORMAL!)
- **After 2-3 queries:** `checkpoints` has 2+ rows, `store` has 0+ rows

---

## When to Worry

### ❌ **Problem:** Tables still don't exist after 10+ queries

**Solution:** Manual initialization
```bash
databricks bundle exec python src/agents/setup/initialize_lakebase_tables.py
```

### ❌ **Problem:** Tables exist but row count always 0

**Solution:** Check agent logs for memory write errors
```bash
# View endpoint logs
databricks serving-endpoints logs \
  --name dev_prashanth_subrahmanyam_health_monitor_agent_dev
```

---

## Your Configuration

From deployment output:

| Setting | Value |
|---|---|
| **Lakebase Instance** | `vibe-coding-workshop-lakebase` |
| **Catalog** | `prashanth_subrahmanyam_catalog` |
| **Schema** | `dev_prashanth_subrahmanyam_system_gold_agent` |
| **Endpoint** | `dev_prashanth_subrahmanyam_health_monitor_agent_dev` |
| **Short-term Retention** | 24 hours |
| **Long-term Retention** | 1 year |

---

## Full Documentation

For detailed troubleshooting and testing: `docs/deployment/LAKEBASE_MEMORY_VERIFICATION.md`
