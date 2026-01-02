# Appendix B - Troubleshooting Guide

## Error Reference

### Error Categories

| Category | Description | Common Causes |
|----------|-------------|---------------|
| **SDK Errors** | Databricks SDK import failures | Wrong SDK version, missing package |
| **API Errors** | Monitor creation/update failures | Permissions, table not found |
| **Schema Errors** | Output table issues | Schema doesn't exist, permissions |
| **Metric Errors** | Custom metric computation fails | Invalid SQL, missing columns |

### Error-Solution Matrix

| Error Message | Root Cause | Solution |
|---------------|------------|----------|
| `ModuleNotFoundError: databricks.sdk` | SDK not installed | Add `databricks-sdk>=0.28.0` to dependencies |
| `ResourceAlreadyExists` | Monitor exists | Delete and recreate, or use update |
| `ResourceDoesNotExist` | Table not found | Verify table name, check permissions |
| `SCHEMA_NOT_FOUND` | Monitoring schema missing | Create schema first |
| `PERMISSION_DENIED` | Insufficient permissions | Grant MANAGE on table |
| `Column 'X' does not exist` | Wrong column name in metric | Fix column name in definition |
| `Division by zero` | Missing NULLIF in derived metric | Add `NULLIF(denominator, 0)` |

## Diagnostic Procedures

### Quick Diagnostics

```sql
-- Check if monitors exist
SELECT * FROM system.information_schema.lakehouse_monitors
WHERE table_catalog = 'your_catalog';

-- Check monitoring schema
SHOW SCHEMAS IN your_catalog LIKE '%monitoring%';

-- Check output tables
SHOW TABLES IN your_catalog.gold_monitoring;

-- Check table permissions
SHOW GRANTS ON TABLE your_catalog.gold.fact_usage;
```

### Detailed Investigation

#### Step 1: Verify SDK Availability

```python
# In Databricks notebook
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.catalog import MonitorMetric
    print("✓ SDK available")
except ImportError as e:
    print(f"✗ SDK not available: {e}")
```

#### Step 2: Check Monitor Status

```python
from databricks.sdk import WorkspaceClient

workspace_client = WorkspaceClient()
table_name = "catalog.schema.table"

try:
    monitor = workspace_client.quality_monitors.get(table_name=table_name)
    print(f"Monitor status: {monitor.status}")
    print(f"Last refresh: {monitor.last_refresh_time}")
except Exception as e:
    print(f"Monitor not found: {e}")
```

#### Step 3: Verify Output Tables

```sql
-- Check profile_metrics exists and has data
SELECT COUNT(*) as row_count
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics;

-- Check custom metrics are populated
SELECT column_name, COUNT(*) 
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
GROUP BY column_name;
```

## Common Issues by Component

### Monitor Creation

#### Issue: "ResourceAlreadyExists" when creating monitor

**Symptoms:**
- Setup job fails with "ResourceAlreadyExists"
- Monitor shows in UI but may have wrong configuration

**Diagnosis:**
```python
# Check existing monitor
monitor = workspace_client.quality_monitors.get(table_name=table_name)
print(f"Existing metrics: {len(monitor.custom_metrics)}")
```

**Solution:**
```python
# Delete and recreate
workspace_client.quality_monitors.delete(table_name=table_name)
# Drop output tables
spark.sql(f"DROP TABLE IF EXISTS {profile_table}")
spark.sql(f"DROP TABLE IF EXISTS {drift_table}")
# Recreate (run setup job)
```

#### Issue: Monitor creation timeout

**Symptoms:**
- Job runs for >30 minutes
- Eventually times out

**Diagnosis:**
```sql
-- Check source table size
SELECT COUNT(*) as rows, SUM(size_in_bytes)/1e9 as gb
FROM system.information_schema.table_storage_metrics
WHERE table_name = 'your_table';
```

**Solution:**
1. Increase job timeout in YAML
2. Ensure source table has proper clustering
3. Consider reducing slicing dimensions

### Metric Computation

#### Issue: Custom metrics return NULL

**Symptoms:**
- Profile metrics table has rows
- Custom metric columns are all NULL

**Diagnosis:**
```sql
-- Check if source table has data in time window
SELECT COUNT(*), MIN(timestamp_col), MAX(timestamp_col)
FROM your_catalog.gold.fact_usage;

-- Check metric definition
SELECT definition 
FROM system.information_schema.lakehouse_monitor_metrics
WHERE table_name = 'fact_usage'
  AND metric_name = 'total_daily_cost';
```

**Solution:**
1. Verify source table has data in expected time range
2. Check column names in metric definitions
3. Verify SQL syntax is valid

#### Issue: DERIVED metrics not computed

**Symptoms:**
- AGGREGATE metrics have values
- DERIVED metrics are NULL

**Diagnosis:**
```sql
-- Check AGGREGATE metrics exist
SELECT total_daily_cost, record_count
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
LIMIT 5;
```

**Solution:**
- DERIVED metrics reference AGGREGATE metrics by exact name
- Verify referenced metrics exist and have non-NULL values

### Output Tables

#### Issue: "SCHEMA_NOT_FOUND" when creating monitor

**Symptoms:**
- Monitor creation fails
- Error mentions monitoring schema

**Solution:**
```sql
-- Create monitoring schema manually
CREATE SCHEMA IF NOT EXISTS your_catalog.gold_monitoring;
```

Or ensure `spark` is passed to `create_time_series_monitor()`:
```python
monitor = create_time_series_monitor(..., spark=spark)
```

#### Issue: Output tables don't appear

**Symptoms:**
- Monitor created successfully
- Tables not visible after 30+ minutes

**Diagnosis:**
```sql
-- Check monitor status
SELECT status, last_refresh_time
FROM system.information_schema.lakehouse_monitors
WHERE table_name = 'fact_usage';
```

**Solution:**
1. Verify source table has data
2. Trigger manual refresh
3. Check for errors in monitor UI

### Documentation

#### Issue: Column comments not applied

**Symptoms:**
- Documentation job succeeds
- Columns still have no comments

**Diagnosis:**
```sql
-- Check column metadata
DESCRIBE TABLE your_catalog.gold_monitoring.fact_usage_profile_metrics;
```

**Solution:**
1. Verify metric names in `METRIC_DESCRIPTIONS` match actual column names
2. Check for case sensitivity issues
3. Re-run documentation job

### Query Issues

#### Issue: Query returns empty results when data exists

**Symptoms:**
- Profile metrics table has rows
- Query returns 0 rows
- Dashboard shows no data

**Common Causes:**
1. Missing `column_name = ':table'` filter
2. Missing `log_type = 'INPUT'` filter
3. Wrong `slice_key` value

**Diagnosis:**
```sql
-- Check what column_name values exist
SELECT DISTINCT column_name, COUNT(*) 
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
GROUP BY column_name;

-- Check what slice_key values exist
SELECT DISTINCT slice_key, COUNT(*) 
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
GROUP BY slice_key;
```

**Solution:**
```sql
-- CORRECT query pattern
SELECT *
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'      -- REQUIRED for custom metrics
  AND log_type = 'INPUT'          -- REQUIRED for source data
  AND slice_key IS NULL;          -- For overall (non-sliced) metrics
```

#### Issue: Sliced queries return duplicates

**Symptoms:**
- Query returns more rows than expected
- Same metric appears multiple times

**Diagnosis:**
```sql
-- Check for multiple slice_key values in same window
SELECT window.start, slice_key, slice_value, COUNT(*)
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
GROUP BY window.start, slice_key, slice_value
HAVING COUNT(*) > 1;
```

**Solution:**
- Add specific `slice_key` filter to avoid mixing sliced and non-sliced results:
```sql
-- Get only workspace-sliced data
WHERE slice_key = 'workspace_id'  -- Be explicit about which slice
```

#### Issue: Drift metrics all NULL

**Symptoms:**
- Drift table has rows
- Drift metric columns are NULL

**Diagnosis:**
```sql
-- Check if CONSECUTIVE drift exists
SELECT DISTINCT drift_type
FROM your_catalog.gold_monitoring.fact_usage_drift_metrics;

-- Need at least 2 periods
SELECT COUNT(DISTINCT window.start) as periods
FROM your_catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table';
```

**Solution:**
- Drift requires 2+ periods of data
- Wait for second refresh cycle
- Query with correct filter:
```sql
WHERE drift_type = 'CONSECUTIVE'  -- REQUIRED for period-over-period
  AND column_name = ':table'
```

## FAQ

### Q: How long does monitor creation take?

A: Typically 2-10 minutes, depending on source table size. Initial profile/drift tables may take additional 10-15 minutes to populate.

### Q: Why are drift metrics empty?

A: Drift metrics require 2+ periods of data. If your monitor uses daily granularity, you need at least 2 days of data.

### Q: Can I update metrics without recreating the monitor?

A: Yes, use `workspace_client.quality_monitors.update()`, but you MUST include all `custom_metrics` - omitting it deletes all metrics.

### Q: Why does refresh take so long?

A: Refresh scans the entire source table. Ensure tables are properly clustered on the timestamp column.

### Q: How do I monitor multiple tables?

A: Create separate monitors for each table. Our implementation has 8 separate monitor notebooks.

### Q: Why must I use `column_name = ':table'`?

A: Lakehouse Monitoring stores both column-level statistics (one row per column) and table-level custom metrics (stored with `column_name = ':table'`). Without this filter, you'll get column-level statistics mixed with your custom business KPIs.

### Q: What's the difference between `slice_key` and `column_name`?

A: 
- `column_name`: Determines if the metric is table-level (`:table`) or column-level (actual column name)
- `slice_key`: Determines if the metric is overall (`NULL`) or broken down by a dimension (e.g., `workspace_id`)

### Q: Why do I need `log_type = 'INPUT'`?

A: Profile metrics can track both input data (`INPUT`) and output data after transformations. For monitoring source Gold tables, always use `INPUT`.

## Support Contacts

| Issue Type | Contact | Method |
|------------|---------|--------|
| SDK/API issues | Databricks Support | Support ticket |
| Job failures | Platform Team | Slack #platform |
| Metric questions | Data Engineering | Slack #data-eng |

---

**Version:** 1.0  
**Last Updated:** January 2026

