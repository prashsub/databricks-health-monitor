# Alerting Framework Operations Guide

**Version:** 2.0  
**Last Updated:** December 30, 2025

---

## Overview

This guide covers day-to-day operations, monitoring, and troubleshooting of the alerting framework.

---

## Monitoring

### Sync Job Health

Monitor sync job runs in the Databricks UI:
1. Navigate to Workflows → Jobs
2. Find `sql_alert_deployment_job`
3. Review run history and durations

### Sync Metrics Table

Query the metrics table for operational insights:

```sql
-- Recent sync runs
SELECT 
    sync_run_id,
    sync_started_at,
    total_duration_seconds,
    total_alerts,
    success_count,
    error_count,
    deleted_count
FROM catalog.gold.alert_sync_metrics
ORDER BY sync_started_at DESC
LIMIT 10;

-- Average sync performance
SELECT 
    AVG(total_duration_seconds) as avg_duration,
    AVG(avg_api_latency_ms) as avg_latency,
    SUM(error_count) as total_errors,
    COUNT(*) as total_runs
FROM catalog.gold.alert_sync_metrics
WHERE sync_started_at >= CURRENT_DATE() - 7;
```

### Alert Status Dashboard

```sql
-- Alert health summary
SELECT 
    agent_domain,
    severity,
    COUNT(*) as total,
    SUM(CASE WHEN is_enabled THEN 1 ELSE 0 END) as enabled,
    SUM(CASE WHEN last_sync_status = 'CREATED' OR last_sync_status = 'UPDATED' THEN 1 ELSE 0 END) as synced,
    SUM(CASE WHEN last_sync_status = 'ERROR' THEN 1 ELSE 0 END) as errors
FROM catalog.gold.alert_configurations
GROUP BY agent_domain, severity
ORDER BY agent_domain, severity;
```

---

## Common Operations

### Add New Alert

```sql
INSERT INTO catalog.gold.alert_configurations (
    alert_id,
    alert_name,
    alert_description,
    agent_domain,
    severity,
    alert_query_template,
    threshold_column,
    threshold_operator,
    threshold_value_type,
    threshold_value_double,
    empty_result_state,
    schedule_cron,
    schedule_timezone,
    pause_status,
    is_enabled,
    notification_channels,
    notify_on_ok,
    use_custom_template,
    owner,
    created_by,
    created_at
) VALUES (
    'COST-003',
    'Monthly Budget Check',
    'Alert when monthly spend approaches budget',
    'COST',
    'WARNING',
    'SELECT SUM(list_cost) as mtd_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= DATE_TRUNC(''month'', CURRENT_DATE()) HAVING SUM(list_cost) > 10000',
    'mtd_cost',
    '>',
    'DOUBLE',
    10000.0,
    'OK',
    '0 0 8 * * ?',
    'America/Los_Angeles',
    'PAUSED',  -- Start paused
    TRUE,
    array('finops@company.com'),
    FALSE,
    FALSE,
    'finops@company.com',
    'admin',
    CURRENT_TIMESTAMP()
);
```

Then deploy:
```bash
databricks bundle run -t dev sql_alert_deployment_job
```

### Update Alert Threshold

```sql
UPDATE catalog.gold.alert_configurations
SET 
    threshold_value_double = 7500.0,
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

Re-sync:
```bash
databricks bundle run -t dev sql_alert_deployment_job
```

### Disable Alert

```sql
-- Disable in config (keeps in Databricks but paused)
UPDATE catalog.gold.alert_configurations
SET 
    is_enabled = FALSE,
    pause_status = 'PAUSED',
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-003';
```

### Delete Alert

```sql
-- Option 1: Disable and let sync job delete from Databricks
UPDATE catalog.gold.alert_configurations
SET is_enabled = FALSE
WHERE alert_id = 'COST-003';
-- Run sync with delete_disabled=true

-- Option 2: Hard delete from config (requires manual Databricks cleanup)
DELETE FROM catalog.gold.alert_configurations
WHERE alert_id = 'COST-003';
```

### Pause/Unpause Alert

```sql
-- Pause (stops evaluation)
UPDATE catalog.gold.alert_configurations
SET 
    pause_status = 'PAUSED',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';

-- Unpause (resumes evaluation)
UPDATE catalog.gold.alert_configurations
SET 
    pause_status = 'UNPAUSED',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

### Update Schedule

```sql
UPDATE catalog.gold.alert_configurations
SET 
    schedule_cron = '0 0 9 * * ?',  -- Change to 9 AM
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

### Update Notification Channels

```sql
-- Add additional recipient
UPDATE catalog.gold.alert_configurations
SET 
    notification_channels = array('finops@company.com', 'manager@company.com'),
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

---

## Bulk Operations

### Enable All Alerts for Domain

```sql
UPDATE catalog.gold.alert_configurations
SET 
    is_enabled = TRUE,
    pause_status = 'UNPAUSED',
    updated_at = CURRENT_TIMESTAMP()
WHERE agent_domain = 'COST';
```

### Pause All Critical Alerts

```sql
UPDATE catalog.gold.alert_configurations
SET 
    pause_status = 'PAUSED',
    updated_at = CURRENT_TIMESTAMP()
WHERE severity = 'CRITICAL';
```

### Update Owner for Team

```sql
UPDATE catalog.gold.alert_configurations
SET 
    owner = 'newteam@company.com',
    updated_at = CURRENT_TIMESTAMP()
WHERE tags['team'] = 'finops';
```

---

## Troubleshooting

### Alert Not Triggering

**Possible Causes:**
1. Alert is paused
2. Query returns no results
3. Threshold not met
4. Schedule not reached

**Diagnosis:**
```sql
-- Check alert status
SELECT 
    alert_id,
    is_enabled,
    pause_status,
    schedule_cron,
    last_synced_at
FROM catalog.gold.alert_configurations
WHERE alert_id = 'COST-001';

-- Test query manually
SELECT SUM(list_cost) as daily_cost
FROM catalog.gold.fact_usage
WHERE usage_date = CURRENT_DATE() - 1;
```

### Sync Job Failing

**Possible Causes:**
1. Authentication expired
2. API rate limit
3. Invalid query syntax
4. Missing tables

**Diagnosis:**
```sql
-- Check recent errors
SELECT 
    alert_id,
    last_sync_status,
    last_sync_error,
    last_synced_at
FROM catalog.gold.alert_configurations
WHERE last_sync_status = 'ERROR'
ORDER BY last_synced_at DESC;
```

**Resolution:**
```bash
# Re-authenticate
databricks auth login --host https://workspace.cloud.databricks.com --profile dev

# Re-run sync
databricks bundle run -t dev sql_alert_deployment_job
```

### Duplicate Alerts in UI

**Cause:** Alert ID changed but old alert not deleted

**Resolution:**
```sql
-- Clear stale Databricks ID
UPDATE catalog.gold.alert_configurations
SET databricks_alert_id = NULL
WHERE alert_id = 'COST-001';

-- Run sync to recreate
-- Manual cleanup: Delete old alert in Databricks UI
```

### Notification Not Delivered

**Possible Causes:**
1. Destination not configured
2. Email/webhook unreachable
3. Destination mapping missing

**Diagnosis:**
```sql
-- Check destination mapping
SELECT 
    destination_id,
    destination_name,
    destination_type,
    databricks_destination_id,
    is_enabled
FROM catalog.gold.notification_destinations
WHERE destination_id IN (
    SELECT EXPLODE(notification_channels)
    FROM catalog.gold.alert_configurations
    WHERE alert_id = 'COST-001'
);
```

### Query Timeout

**Cause:** Alert query takes too long

**Resolution:**
1. Optimize query (add filters, indices)
2. Reduce data volume (shorter lookback)
3. Pre-aggregate in separate table

```sql
-- Before: Full scan
SELECT COUNT(*) FROM fact_usage WHERE ...

-- After: Filtered scan
SELECT COUNT(*) 
FROM fact_usage 
WHERE usage_date >= CURRENT_DATE() - 7  -- Limit lookback
```

---

## Health Checks

### Daily Health Check Script

```python
# Run as scheduled job
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Check 1: Any sync errors in last 24h?
errors = spark.sql("""
    SELECT COUNT(*) as error_count
    FROM catalog.gold.alert_configurations
    WHERE last_sync_status = 'ERROR'
      AND last_synced_at >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
""").collect()[0]['error_count']

if errors > 0:
    print(f"WARNING: {errors} alerts with sync errors")

# Check 2: Any stale syncs (not synced in >24h)?
stale = spark.sql("""
    SELECT COUNT(*) as stale_count
    FROM catalog.gold.alert_configurations
    WHERE is_enabled = TRUE
      AND (last_synced_at IS NULL OR last_synced_at < CURRENT_TIMESTAMP() - INTERVAL 24 HOURS)
""").collect()[0]['stale_count']

if stale > 0:
    print(f"WARNING: {stale} alerts not synced recently")

# Check 3: Config table accessible?
try:
    count = spark.sql("SELECT COUNT(*) FROM catalog.gold.alert_configurations").collect()[0][0]
    print(f"OK: {count} alerts configured")
except Exception as e:
    print(f"ERROR: Cannot access config table: {e}")
```

### Weekly Audit Report

```sql
-- Generate weekly audit report
SELECT 
    agent_domain,
    COUNT(*) as total_alerts,
    SUM(CASE WHEN is_enabled THEN 1 ELSE 0 END) as enabled,
    SUM(CASE WHEN pause_status = 'PAUSED' THEN 1 ELSE 0 END) as paused,
    SUM(CASE WHEN last_sync_status = 'ERROR' THEN 1 ELSE 0 END) as sync_errors,
    SUM(CASE WHEN last_synced_at < CURRENT_TIMESTAMP() - INTERVAL 24 HOURS THEN 1 ELSE 0 END) as stale,
    MIN(last_synced_at) as oldest_sync,
    MAX(last_synced_at) as newest_sync
FROM catalog.gold.alert_configurations
GROUP BY agent_domain
ORDER BY agent_domain;
```

---

## Performance Tuning

### Query Optimization

```sql
-- Use aggregation at source when possible
-- Before: Complex join
SELECT ... FROM fact_a JOIN fact_b ...

-- After: Pre-aggregated
SELECT ... FROM fact_summary WHERE ...
```

### Sync Parallelization

For large alert counts, enable parallel sync:

```python
# In sync_sql_alerts.py
sync_alerts(
    spark=spark,
    catalog=catalog,
    gold_schema=gold_schema,
    warehouse_id=warehouse_id,
    dry_run=False,
    api_base="/api/2.0/alerts",
    delete_disabled=True,
    parallel=True,        # Enable parallel
    max_workers=10        # Increase workers
)
```

### Schedule Staggering

Avoid all alerts running at same time:

```sql
-- Stagger schedules
UPDATE alert_configurations SET schedule_cron = '0 0 6 * * ?' WHERE alert_id = 'COST-001';
UPDATE alert_configurations SET schedule_cron = '0 5 6 * * ?' WHERE alert_id = 'COST-002';
UPDATE alert_configurations SET schedule_cron = '0 10 6 * * ?' WHERE alert_id = 'COST-003';
```

---

## Incident Response

### Alert Storm (Too Many Notifications)

1. **Immediate:** Pause all alerts
   ```sql
   UPDATE alert_configurations SET pause_status = 'PAUSED';
   ```

2. **Investigate:** Check what triggered mass alerts

3. **Resolve:** Fix root cause, adjust thresholds

4. **Resume:** Re-enable alerts with staggered schedule

### Sync Job Down

1. **Check logs:** Review job run output
2. **Re-authenticate:** Refresh Databricks token
3. **Manual sync:** Run sync job manually
4. **Alert owner:** Notify platform team

### Data Quality Issue Affecting Alerts

1. **Pause affected alerts**
2. **Fix source data**
3. **Validate queries**
4. **Re-enable alerts**

---

## Maintenance

### Weekly Tasks

- [ ] Review sync error log
- [ ] Check stale alerts
- [ ] Verify notification delivery
- [ ] Review alert trigger frequency

### Monthly Tasks

- [ ] Audit alert ownership
- [ ] Review and update thresholds
- [ ] Clean up disabled alerts
- [ ] Update notification destinations

### Quarterly Tasks

- [ ] Review alert coverage by domain
- [ ] Assess new alert requirements
- [ ] Archive historical data
- [ ] Performance optimization review

