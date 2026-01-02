# 06 - Implementation Guide

## Overview

This guide provides step-by-step instructions for deploying the Lakehouse Monitoring system. Follow these phases in order for a successful deployment.

## Prerequisites

Before starting, ensure:

- [ ] Gold layer tables exist and have data
- [ ] Unity Catalog access configured
- [ ] Databricks CLI installed and authenticated
- [ ] Asset Bundle deployed at least once

```bash
# Verify CLI authentication
databricks auth profiles
databricks current-user me
```

## Phase 1: Deploy Asset Bundle

### Step 1.1: Validate Bundle Configuration

```bash
cd /path/to/DatabricksHealthMonitor

# Validate bundle
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle validate -t dev
```

**Expected Result**: No errors, warnings acceptable

### Step 1.2: Deploy Bundle

```bash
# Deploy to dev target
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle deploy -t dev
```

**Expected Result**:
```
Deploying resources...
Deploy complete!
```

### Validation

```bash
# List deployed jobs
databricks jobs list --name "Health Monitor"
```

Should show:
- `[dev] Health Monitor - Lakehouse Monitoring Setup`
- `[dev] Health Monitor - Lakehouse Monitoring Refresh`
- `[dev] Health Monitor - Document Monitoring Tables`

## Phase 2: Create Monitors

### Step 2.1: Run Setup Job

```bash
# Run the setup job
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle run -t dev lakehouse_monitoring_setup_job
```

### Step 2.2: Monitor Progress

The job will execute 8 tasks sequentially:

```
Task                    | Status    | Output
------------------------|-----------|----------------------------------------
create_cost_monitor     | SUCCESS   | Cost monitor created with 35 metrics
create_job_monitor      | SUCCESS   | Job monitor created with 50 metrics
create_query_monitor    | SUCCESS   | Query monitor created with 40 metrics
create_cluster_monitor  | SUCCESS   | Cluster monitor created with 40 metrics
create_security_monitor | SUCCESS   | Security monitor created with 15 metrics
create_quality_monitor  | SUCCESS   | Quality monitor created with 15 metrics
create_governance_monitor| SUCCESS  | Governance monitor created with 15 metrics
create_inference_monitor | SUCCESS  | Inference monitor created with 15 metrics
```

**Expected Duration**: 5-15 minutes (depending on table sizes)

### Step 2.3: Verify Monitors Created

```sql
-- In Databricks SQL or notebook
SELECT 
    table_name,
    status,
    create_time,
    dashboard_id
FROM system.information_schema.lakehouse_monitors
WHERE table_catalog = 'your_catalog'
  AND table_schema = 'your_gold_schema';
```

**Expected Result**: 8 rows, all with status = 'ACTIVE'

## Phase 3: Wait for Table Creation

### Step 3.1: Monitor Asynchronous Creation

Lakehouse Monitoring creates output tables asynchronously. Wait ~15 minutes.

```bash
# Option 1: Use wait job (if implemented)
databricks bundle run -t dev wait_for_monitors

# Option 2: Manual wait
sleep 900  # 15 minutes
```

### Step 3.2: Verify Tables Exist

```sql
-- Check profile_metrics tables
SELECT table_name, row_count
FROM system.information_schema.tables
WHERE table_schema = 'your_gold_schema_monitoring'
  AND table_name LIKE '%_profile_metrics';

-- Check drift_metrics tables
SELECT table_name, row_count
FROM system.information_schema.tables
WHERE table_schema = 'your_gold_schema_monitoring'
  AND table_name LIKE '%_drift_metrics';
```

**Expected Result**: 16 tables (8 profile + 8 drift)

## Phase 4: Document for Genie

### Step 4.1: Run Documentation Job

```bash
# Run documentation job
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle run -t dev lakehouse_monitoring_document_job
```

### Step 4.2: Verify Documentation

**Expected Output**:
```
======================================================================
Documenting Lakehouse Monitoring Tables for Genie
======================================================================
  Tables documented: 8
  Tables not ready:  0
  Tables with errors: 0
```

### Step 4.3: Verify in SQL

```sql
-- Check table comments
SELECT 
    table_name,
    LEFT(comment, 100) as comment_preview
FROM system.information_schema.tables
WHERE table_schema = 'your_gold_schema_monitoring'
  AND table_name LIKE '%_profile_metrics';

-- Check column comments (sample)
DESCRIBE TABLE your_catalog.your_gold_schema_monitoring.fact_usage_profile_metrics;
```

## Phase 5: Enable Scheduled Refresh (Optional)

### Step 5.1: Unpause Refresh Job

In Databricks UI:
1. Navigate to Workflows
2. Find `[dev] Health Monitor - Lakehouse Monitoring Refresh`
3. Click "Edit"
4. Set Schedule to "Enabled"
5. Save

Or via CLI:

```bash
# Get job ID
JOB_ID=$(databricks jobs list --name "[dev] Health Monitor - Lakehouse Monitoring Refresh" --output json | jq '.[0].job_id')

# Note: Schedule management typically done via UI
# Job is deployed PAUSED by default for safety
```

### Step 5.2: Test Manual Refresh

```bash
# Trigger manual refresh
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle run -t dev lakehouse_monitoring_refresh_job
```

## Deployment Commands Summary

```bash
# ===== COMPLETE DEPLOYMENT SEQUENCE =====

# 1. Deploy bundle
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle deploy -t dev

# 2. Create monitors (one-time)
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle run -t dev lakehouse_monitoring_setup_job

# 3. Wait for tables (~15 min)
sleep 900

# 4. Document for Genie
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle run -t dev lakehouse_monitoring_document_job

# 5. (Optional) Test refresh
DATABRICKS_CONFIG_PROFILE=your-profile databricks bundle run -t dev lakehouse_monitoring_refresh_job
```

## Post-Deployment Validation

### Validation Checklist

- [ ] 8 monitors created (query system.information_schema.lakehouse_monitors)
- [ ] 16 output tables created (8 profile + 8 drift)
- [ ] Table comments added (DESCRIBE TABLE shows comments)
- [ ] Column comments added (custom metric columns have descriptions)
- [ ] Manual refresh succeeds
- [ ] Sample Genie query works

### Smoke Tests

```sql
-- Test 1: Profile metrics populated
SELECT COUNT(*) FROM catalog.gold_monitoring.fact_usage_profile_metrics;
-- Expected: > 0

-- Test 2: Custom metrics computed (CRITICAL: use column_name=':table' and log_type='INPUT')
SELECT 
    window.start AS window_start,
    window.end AS window_end,
    total_daily_cost,
    tag_coverage_pct
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'         -- REQUIRED: table-level custom metrics
  AND log_type = 'INPUT'             -- REQUIRED: source data statistics
  AND slice_key IS NULL              -- Overall (non-sliced) metrics
ORDER BY window.start DESC
LIMIT 5;
-- Expected: Recent data with non-null custom metrics

-- Test 3: Sliced metrics work
SELECT 
    slice_value AS workspace_id,
    total_daily_cost
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'workspace_id'     -- Sliced by workspace
ORDER BY total_daily_cost DESC
LIMIT 5;
-- Expected: Cost breakdown by workspace

-- Test 4: Drift metrics computed
SELECT COUNT(*) 
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'     -- Period-over-period comparison
  AND column_name = ':table';
-- Expected: > 0 (after 2+ periods)

-- Test 5: Drift values exist
SELECT 
    window.start AS window_start,
    cost_drift_pct,
    dbu_drift_pct
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
  AND slice_key IS NULL
ORDER BY window.start DESC
LIMIT 5;
-- Expected: Drift percentages (may be NULL for first period)

-- Test 6: Documentation present
SELECT comment 
FROM system.information_schema.tables
WHERE table_name = 'fact_usage_profile_metrics'
  AND table_schema LIKE '%monitoring';
-- Expected: Non-empty comment
```

### Query Pattern Reference

For all monitoring table queries, remember these **REQUIRED** filters:

| Table Type | Required Filters |
|------------|-----------------|
| **Profile Metrics** | `column_name = ':table'` AND `log_type = 'INPUT'` |
| **Drift Metrics** | `drift_type = 'CONSECUTIVE'` AND `column_name = ':table'` |
| **Sliced Data** | Add `slice_key = '<dimension>'` |
| **Overall Data** | Add `slice_key IS NULL` (or `COALESCE(slice_key, 'No Slice') = 'No Slice'`) |

See [05-Genie Integration](05-genie-integration.md#critical-query-patterns-for-genie) for comprehensive patterns.

## Cleanup and Restart

### Delete All Monitors

If you need to recreate monitors:

```python
# In a Databricks notebook
from databricks.sdk import WorkspaceClient

workspace_client = WorkspaceClient()
catalog = "your_catalog"
gold_schema = "your_gold_schema"

tables = [
    "fact_usage",
    "fact_job_run_timeline",
    "fact_query_history",
    "fact_node_timeline",
    "fact_audit_logs",
    "fact_table_quality",
    "fact_governance_metrics",
    "fact_model_serving",
]

for table in tables:
    table_name = f"{catalog}.{gold_schema}.{table}"
    try:
        workspace_client.quality_monitors.delete(table_name=table_name)
        print(f"Deleted monitor for {table}")
    except Exception as e:
        print(f"No monitor for {table}: {e}")
```

### Drop Output Tables

```sql
-- Drop all monitoring tables
DROP SCHEMA IF EXISTS your_catalog.your_gold_schema_monitoring CASCADE;
```

### Full Restart Sequence

```bash
# 1. Delete monitors (use notebook above)

# 2. Drop output tables (SQL above)

# 3. Redeploy
databricks bundle deploy -t dev

# 4. Recreate monitors
databricks bundle run -t dev lakehouse_monitoring_setup_job

# 5. Wait and document
sleep 900
databricks bundle run -t dev lakehouse_monitoring_document_job
```

## Rollback Procedures

### Quick Rollback (Pause Refresh)

If monitors are causing issues:

1. Navigate to Workflows in Databricks UI
2. Find refresh job
3. Pause schedule

### Full Rollback (Delete Monitors)

1. Run cleanup notebook (above)
2. Drop monitoring schema
3. Monitors can be recreated later

## Time Estimates

| Phase | Duration |
|-------|----------|
| Phase 1: Deploy Bundle | 2 minutes |
| Phase 2: Create Monitors | 5-15 minutes |
| Phase 3: Wait for Tables | 15 minutes |
| Phase 4: Document for Genie | 2-5 minutes |
| Phase 5: Enable Refresh | 1 minute |
| **Total** | **~30-40 minutes** |

## Troubleshooting

### Monitor Creation Fails

**Symptom**: Setup job fails with "ResourceAlreadyExists"

**Solution**: Delete existing monitor and retry:

```python
workspace_client.quality_monitors.delete(table_name="catalog.schema.table")
```

### Tables Not Created

**Symptom**: No output tables after 30 minutes

**Cause**: Source table may be empty or have issues

**Solution**: 
1. Verify source table has data
2. Check monitor status in system tables
3. Check Databricks UI for monitor errors

### Documentation Fails

**Symptom**: "NOT_READY" after 30+ minutes

**Solution**: 
1. Verify tables exist in catalog
2. Check for permission issues
3. Try running documentation again

---

**Version:** 1.0  
**Last Updated:** January 2026

