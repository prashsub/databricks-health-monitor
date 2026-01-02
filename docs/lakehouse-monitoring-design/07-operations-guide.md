# 07 - Operations Guide

## Overview

This guide covers day-to-day operations, maintenance, and troubleshooting for the Lakehouse Monitoring system.

## Daily Operations

### Health Checks

| Check | Frequency | Command | Expected Result |
|-------|-----------|---------|-----------------|
| Monitor status | Daily | See SQL below | All ACTIVE |
| Refresh success | Daily | Check Workflows UI | Last run SUCCESS |
| Metric freshness | Daily | See SQL below | Recent windows |
| Error alerts | Daily | Check email | No failures |

#### SQL Health Checks

```sql
-- Check 1: All monitors active
SELECT 
    table_name,
    status,
    DATEDIFF(CURRENT_DATE, last_refresh_time) as days_since_refresh
FROM system.information_schema.lakehouse_monitors
WHERE table_catalog = 'your_catalog'
  AND table_schema = 'your_gold_schema';
-- Expected: All status = 'ACTIVE', days_since_refresh <= 1

-- Check 2: Recent metrics computed (CRITICAL: use correct filters)
SELECT 
    MAX(window.end) as latest_window,
    DATEDIFF(CURRENT_TIMESTAMP, MAX(window.end)) as hours_behind
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'      -- REQUIRED: table-level custom metrics
  AND log_type = 'INPUT'          -- REQUIRED: source data statistics
  AND slice_key IS NULL;          -- Overall (non-sliced) metrics
-- Expected: hours_behind < 24

-- Check 3: No NULL metrics (verify custom metrics are populated)
SELECT 
    COUNT(*) as total_rows,
    COUNT(total_daily_cost) as non_null_cost,
    COUNT(tag_coverage_pct) as non_null_tag_coverage
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.end > CURRENT_DATE - INTERVAL 7 DAYS;
-- Expected: non_null_* = total_rows

-- Check 4: Sliced metrics are populated
SELECT 
    slice_key,
    COUNT(DISTINCT slice_value) as unique_values,
    COUNT(*) as metric_rows
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NOT NULL
GROUP BY slice_key;
-- Expected: Rows for each slicing dimension (workspace_id, sku_name, etc.)

-- Check 5: Drift metrics computed
SELECT 
    COUNT(*) as drift_rows
FROM your_catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table';
-- Expected: > 0 (after 2+ periods)
```

### Critical Query Patterns

When querying monitoring tables, **always use these filters**:

| Filter | Profile Metrics | Drift Metrics |
|--------|----------------|---------------|
| `column_name = ':table'` | ✅ Required | ✅ Required |
| `log_type = 'INPUT'` | ✅ Required | Not applicable |
| `drift_type = 'CONSECUTIVE'` | Not applicable | ✅ Required |
| `slice_key IS NULL` | Optional (overall) | Optional (overall) |
| `slice_key = 'dimension'` | Optional (sliced) | Optional (sliced) |

### Monitoring Dashboards

| Dashboard | Purpose | URL |
|-----------|---------|-----|
| Lakehouse Monitoring | Monitor health | `/lakehouse-monitoring` |
| Workflows | Job status | `/workflows` |
| Gold Monitoring Schema | Output tables | `/data/{catalog}/gold_monitoring` |

## Refresh Operations

### Scheduled Refresh

The refresh job runs daily at 6 AM (when enabled).

**Schedule Configuration**:
```yaml
schedule:
  quartz_cron_expression: "0 0 6 * * ?"
  timezone_id: "America/Los_Angeles"
  pause_status: PAUSED  # Enable in prod
```

### Manual Refresh

Trigger immediate refresh:

```bash
# Via CLI
DATABRICKS_CONFIG_PROFILE=your-profile \
  databricks bundle run -t dev lakehouse_monitoring_refresh_job

# Via UI
# Workflows → Find job → Run Now
```

### Refresh Notebook

The refresh notebook triggers all monitors:

```python
# refresh_monitors.py (simplified)
def main():
    workspace_client = WorkspaceClient()
    
    tables = [
        f"{catalog}.{gold_schema}.fact_usage",
        f"{catalog}.{gold_schema}.fact_job_run_timeline",
        # ... 8 tables total
    ]
    
    for table_name in tables:
        workspace_client.quality_monitors.run_refresh(table_name=table_name)
        print(f"Triggered refresh for {table_name}")
```

## Update Operations

### ⚠️ Critical: Update Behavior

**Never omit `custom_metrics` when updating a monitor!**

| What You Pass | What Happens |
|---------------|--------------|
| `custom_metrics=None` | ❌ Deletes all custom metrics |
| `custom_metrics=[]` | ❌ Deletes all custom metrics |
| Omit `custom_metrics` | ❌ Deletes all custom metrics |
| `custom_metrics=[...]` | ✅ Replaces with provided list |

### Safe Update Pattern

```python
def update_monitor_safely(workspace_client, table_name: str, new_metrics: List):
    """Update monitor with full configuration."""
    
    # Get existing config
    existing = workspace_client.quality_monitors.get(table_name=table_name)
    
    # Build update with ALL fields
    workspace_client.quality_monitors.update(
        table_name=table_name,
        custom_metrics=new_metrics,  # ✅ Always include
        slicing_exprs=existing.slicing_exprs,  # Preserve
        schedule=existing.schedule,  # Preserve
    )
```

### Add Metric Workflow

1. Define new metric in monitor notebook
2. Run setup job (will recreate monitor)
3. Wait 15 min for tables
4. Run documentation job

```bash
# After updating code
databricks bundle deploy -t dev
databricks bundle run -t dev lakehouse_monitoring_setup_job
sleep 900
databricks bundle run -t dev lakehouse_monitoring_document_job
```

## Maintenance Procedures

### Scheduled Maintenance

| Task | Frequency | Steps | Owner |
|------|-----------|-------|-------|
| Verify metrics | Weekly | Run health check SQL | Data Engineer |
| Check drift tables | Weekly | Query drift metrics | Data Analyst |
| Review job runs | Weekly | Check Workflows history | Platform Team |
| Update descriptions | Monthly | Run documentation job | Data Engineer |

### Ad-hoc Maintenance

#### Recreate Single Monitor

```python
# 1. Delete existing
workspace_client.quality_monitors.delete(table_name="catalog.schema.table")

# 2. Drop output tables
spark.sql("DROP TABLE IF EXISTS catalog.gold_monitoring.table_profile_metrics")
spark.sql("DROP TABLE IF EXISTS catalog.gold_monitoring.table_drift_metrics")

# 3. Recreate (run specific task or full setup job)
```

#### Clear and Rebuild All

```bash
# Run full cleanup and rebuild
databricks bundle run -t dev lakehouse_monitoring_setup_job
sleep 900
databricks bundle run -t dev lakehouse_monitoring_document_job
```

## Incident Response

### Incident Classification

| Level | Description | Examples |
|-------|-------------|----------|
| P1 | All monitors down | API unavailable, workspace issues |
| P2 | Multiple monitors failing | Schema deleted, permission issues |
| P3 | Single monitor failing | Source table issue |
| P4 | Delayed refresh | Network timeout, transient error |

### Response Procedures

#### P1 Response (All Monitors Down)

1. Check Databricks status page
2. Verify workspace connectivity
3. Check system.information_schema.lakehouse_monitors
4. Escalate to Databricks support if API issue

#### P2 Response (Multiple Failures)

1. Check monitoring schema exists
2. Verify permissions on Gold tables
3. Review job logs for common errors
4. Recreate affected monitors if needed

#### P3 Response (Single Monitor)

1. Check source table has data
2. Verify table schema unchanged
3. Check monitor status in UI
4. Delete and recreate monitor

#### P4 Response (Delayed Refresh)

1. Check job run history
2. Trigger manual refresh
3. Monitor next scheduled run
4. No action if transient

## Backup and Recovery

### What's Backed Up

| Component | Backup Method | Retention |
|-----------|---------------|-----------|
| Monitor definitions | Code in Git | Unlimited |
| Metric configurations | Code in Git | Unlimited |
| Output tables | Delta Lake history | 30 days |
| Documentation | Code in Git | Unlimited |

### Recovery Procedures

#### Recover Monitor Definitions

```bash
# Monitors are defined in code - redeploy
git checkout main
databricks bundle deploy -t dev
databricks bundle run -t dev lakehouse_monitoring_setup_job
```

#### Recover Output Tables (Time Travel)

```sql
-- Restore profile_metrics to previous version
RESTORE TABLE catalog.gold_monitoring.fact_usage_profile_metrics
TO VERSION AS OF 5;

-- Or to timestamp
RESTORE TABLE catalog.gold_monitoring.fact_usage_profile_metrics
TO TIMESTAMP AS OF '2024-01-01 00:00:00';
```

## Performance Tuning

### Key Metrics

| Metric | Target | Current | Action if Exceeded |
|--------|--------|---------|-------------------|
| Monitor creation time | <5 min | Monitor | Reduce source table size |
| Refresh time | <30 min | Monitor | Optimize source tables |
| Output table size | <10GB | Monitor | Archive old windows |

### Optimization Procedures

#### Large Source Tables

If source tables are very large:

1. Ensure clustering on timestamp column
2. Consider reducing granularities
3. Limit slicing expression cardinality

#### Output Table Growth

```sql
-- Check output table sizes
SELECT 
    table_name,
    SUM(size_in_bytes) / (1024*1024*1024) as size_gb
FROM system.information_schema.table_storage_metrics
WHERE table_schema = 'gold_monitoring'
GROUP BY table_name
ORDER BY size_gb DESC;
```

If too large:
```sql
-- Delete old data (keep last 90 days)
DELETE FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE window_end < CURRENT_DATE - INTERVAL 90 DAYS;

OPTIMIZE catalog.gold_monitoring.fact_usage_profile_metrics;
VACUUM catalog.gold_monitoring.fact_usage_profile_metrics;
```

## Access Control

### Service Accounts

| Account | Purpose | Permissions | Owner |
|---------|---------|-------------|-------|
| `monitoring-service` | Job execution | MANAGE on Gold tables | Platform Team |

### Permission Changes

To grant access to monitoring output:

```sql
-- Grant read access
GRANT SELECT ON SCHEMA catalog.gold_monitoring TO `data_analysts`;

-- Grant to specific table
GRANT SELECT ON TABLE catalog.gold_monitoring.fact_usage_profile_metrics TO `analyst@company.com`;
```

## Common Issues and Solutions

### Issue: Monitor Returns NULL Metrics

**Symptom**: Custom metrics are all NULL

**Causes**:
1. Source table is empty
2. Timestamp column has no recent data
3. Metric definition has SQL error

**Solution**:
```sql
-- Check source table
SELECT COUNT(*), MAX(timestamp_col) FROM catalog.schema.source_table;

-- If empty, wait for data then refresh
```

### Issue: Drift Metrics Empty

**Symptom**: Drift table exists but has no rows

**Causes**:
1. Need 2+ periods of data for comparison
2. Missing required query filters

**Solution**:
```sql
-- Check drift data with correct filters
SELECT COUNT(*) 
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'  -- REQUIRED
  AND column_name = ':table';     -- REQUIRED

-- If 0 rows, wait for next refresh cycle after initial data
-- Drift requires 2+ periods to compare
```

### Issue: Query Returns No Data When Data Exists

**Symptom**: Output table has rows, but query returns empty

**Causes**:
1. Missing `column_name = ':table'` filter
2. Missing `log_type = 'INPUT'` filter
3. Wrong `slice_key` value

**Solution**:
```sql
-- Correct profile metrics query pattern
SELECT total_daily_cost, tag_coverage_pct
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'     -- REQUIRED for custom metrics
  AND log_type = 'INPUT'         -- REQUIRED for source data
  AND slice_key IS NULL;         -- For overall (non-sliced) metrics

-- Check available slice_key values
SELECT DISTINCT slice_key FROM catalog.gold_monitoring.fact_usage_profile_metrics;
```

### Issue: Documentation Not Applied

**Symptom**: Columns have no comments after running job

**Causes**:
1. Tables not yet created
2. Permission issue
3. Column name mismatch

**Solution**:
```sql
-- Check if tables exist
SHOW TABLES IN catalog.gold_monitoring;

-- Check permissions
SHOW GRANTS ON TABLE catalog.gold_monitoring.fact_usage_profile_metrics;

-- Re-run documentation
databricks bundle run -t dev lakehouse_monitoring_document_job
```

### Issue: Job Timeout

**Symptom**: Setup job times out

**Cause**: Very large source tables

**Solution**:
1. Increase job timeout in YAML
2. Optimize source tables
3. Run monitors sequentially

## Monitoring the Monitors

### Meta-Monitoring Query

```sql
-- Dashboard query: Monitor health overview
SELECT 
    SPLIT_PART(table_name, '.', 3) as table_short_name,
    status,
    last_refresh_time,
    CASE 
        WHEN status = 'ACTIVE' AND last_refresh_time > CURRENT_TIMESTAMP - INTERVAL 1 DAY THEN '🟢 Healthy'
        WHEN status = 'ACTIVE' AND last_refresh_time > CURRENT_TIMESTAMP - INTERVAL 2 DAYS THEN '🟡 Stale'
        ELSE '🔴 Issue'
    END as health_status
FROM system.information_schema.lakehouse_monitors
WHERE table_catalog = 'your_catalog'
  AND table_schema = 'your_gold_schema';
```

## Support Contacts

| Issue Type | Contact | Method |
|------------|---------|--------|
| Monitor API issues | Databricks Support | Support ticket |
| Job failures | Platform Team | Slack #platform |
| Metric questions | Data Engineering | Slack #data-eng |
| Access requests | Security Team | Jira ticket |

---

**Version:** 1.0  
**Last Updated:** January 2026

