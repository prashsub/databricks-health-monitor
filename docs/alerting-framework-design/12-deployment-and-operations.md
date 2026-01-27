# 12 - Deployment and Operations

## Overview

This document covers production deployment and day-to-day operations of the alerting framework.

## Deployment Commands

### Initial Deployment

```bash
# 1. Validate bundle configuration
databricks bundle validate -t dev

# 2. Deploy all resources
databricks bundle deploy -t dev

# 3. Run complete alerting setup
databricks bundle run -t dev alerting_setup_orchestrator_job
```

### Individual Job Execution

```bash
# Setup tables only
databricks bundle run -t dev alerting_tables_job

# Seed alerts only
databricks bundle run -t dev alerting_seed_job

# Validate queries only
databricks bundle run -t dev alerting_validation_job

# Deploy alerts only
databricks bundle run -t dev alerting_deploy_job

# Sync notification destinations
databricks bundle run -t dev alerting_notifications_job
```

### Production Deployment

```bash
# Deploy to production
databricks bundle deploy -t prod

# Run setup
databricks bundle run -t prod alerting_setup_orchestrator_job
```

## Verification Queries

### Alert Sync Status

```sql
SELECT 
    alert_id,
    alert_name,
    severity,
    last_sync_status,
    last_synced_at,
    last_sync_error
FROM alert_configurations
WHERE is_enabled = TRUE
ORDER BY last_synced_at DESC;
```

### Validation Results

```sql
SELECT 
    alert_id,
    is_valid,
    error_message,
    validation_timestamp
FROM alert_validation_results
WHERE is_valid = FALSE
ORDER BY validation_timestamp DESC;
```

## Common Operations

### Adding New Alerts - Complete Workflow

#### Step 1: Insert Alert Configuration

```sql
-- Option A: Simple alert with direct SQL INSERT
INSERT INTO ${catalog}.${gold_schema}.alert_configurations (
    alert_id, alert_name, alert_description, agent_domain, severity,
    alert_query_template, query_source, threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double, empty_result_state,
    aggregation_type, schedule_cron, schedule_timezone, pause_status,
    is_enabled, notification_channels, notify_on_ok, owner,
    created_by, created_at
) VALUES (
    'COST-099',
    'Daily Workspace Cost Spike',
    'Alert when daily workspace cost exceeds $10,000',
    'COST',
    'WARNING',
    'SELECT SUM(list_cost) as total_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 AND workspace_name LIKE ''%prod%'' HAVING SUM(list_cost) > 10000',
    'CUSTOM',
    'total_cost',
    '>',
    'DOUBLE',
    10000.0,
    'OK',
    'FIRST',
    '0 0 7 * * ?',  -- Daily at 7am
    'America/Los_Angeles',
    'UNPAUSED',
    true,
    ARRAY('finops@company.com'),
    false,
    'finops@company.com',
    'prashanth.subrahmanyam@databricks.com',
    CURRENT_TIMESTAMP()
);
```

**⚠️ For queries with LIKE patterns**, use DataFrame insertion to avoid SQL escaping issues:

```python
# Option B: DataFrame insertion (handles SQL escaping correctly)
from pyspark.sql import SparkSession
from datetime import datetime

spark = SparkSession.builder.getOrCreate()

new_alerts = [{
    "alert_id": "COST-099",
    "alert_name": "Daily Workspace Cost Spike",
    "alert_query_template": "SELECT SUM(list_cost) as total_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 AND workspace_name LIKE '%prod%' HAVING SUM(list_cost) > 10000",
    # ... all other required fields
    "created_at": datetime.now(),
    "is_enabled": True,
}]

df = spark.createDataFrame(new_alerts, schema=ALERT_CONFIG_SCHEMA)
df.write.mode("append").saveAsTable(f"{catalog}.{gold_schema}.alert_configurations")
```

#### Step 2: Validate Query (Recommended)

```bash
# Run validation to catch syntax/column errors early
databricks bundle run -t dev alerting_validation_job
```

Check validation results:
```sql
SELECT alert_id, is_valid, error_message
FROM ${catalog}.${gold_schema}.alert_validation_results
WHERE alert_id = 'COST-099';
```

#### Step 3: Deploy to Databricks SQL Alerts

```bash
# Sync configuration to Databricks SQL Alerts
databricks bundle run -t dev alerting_deploy_job
```

#### Step 4: Verify Deployment

```sql
-- Check sync status
SELECT 
    alert_id,
    alert_name,
    databricks_alert_id,
    last_sync_status,
    last_synced_at,
    last_sync_error
FROM ${catalog}.${gold_schema}.alert_configurations
WHERE alert_id = 'COST-099';

-- Expected: last_sync_status = 'CREATED', databricks_alert_id populated
```

#### Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. Insert/Update Alert in Delta Table                  │
│    → SQL INSERT (simple queries)                       │
│    → DataFrame write (complex queries with LIKE)       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Validate Query (Recommended)                        │
│    → databricks bundle run alerting_validation_job     │
│    → Catches 100% of syntax/column errors              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Deploy to Databricks SQL Alerts                     │
│    → databricks bundle run alerting_deploy_job         │
│    → Creates/updates alert via SDK                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Verify Deployment                                   │
│    → Check last_sync_status in config table            │
│    → Verify alert appears in Databricks SQL UI         │
└─────────────────────────────────────────────────────────┘
```

### Modifying Existing Alerts

#### Update Alert Threshold

```sql
UPDATE ${catalog}.${gold_schema}.alert_configurations
SET 
    threshold_value_double = 15000.0,
    alert_description = 'Updated threshold from $10k to $15k',
    updated_by = 'prashanth.subrahmanyam@databricks.com',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-099';

-- Then re-sync (will UPDATE existing Databricks alert, not create duplicate)
-- databricks bundle run -t dev alerting_deploy_job
```

#### Update Alert Query

```sql
UPDATE ${catalog}.${gold_schema}.alert_configurations
SET 
    alert_query_template = 'SELECT SUM(list_cost) as total_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 AND workspace_name LIKE ''%prod%'' AND usage_metadata.workload_type = ''JOBS'' HAVING SUM(list_cost) > 15000',
    updated_by = 'prashanth.subrahmanyam@databricks.com',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-099';

-- IMPORTANT: Validate query after update!
-- databricks bundle run -t dev alerting_validation_job
-- databricks bundle run -t dev alerting_deploy_job
```

### Disabling/Enabling Alerts

#### Disable Alert (Removes from Databricks)

```sql
UPDATE ${catalog}.${gold_schema}.alert_configurations
SET 
    is_enabled = FALSE,
    updated_by = 'prashanth.subrahmanyam@databricks.com',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-099';

-- Sync will DELETE the alert from Databricks (if delete_disabled = true)
-- databricks bundle run -t dev alerting_deploy_job
```

#### Pause Alert (Keeps in Databricks, Stops Evaluation)

```sql
UPDATE ${catalog}.${gold_schema}.alert_configurations
SET 
    pause_status = 'PAUSED',
    updated_by = 'prashanth.subrahmanyam@databricks.com',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-099';

-- Sync will update pause status
-- databricks bundle run -t dev alerting_deploy_job
```

### Best Practices

#### ✅ DO:
1. **Always validate queries first** - Catches 100% of syntax/column errors before deployment
2. **Use fully qualified table names** - `${catalog}.${gold_schema}.table_name`
3. **Test threshold logic manually** - Run query to verify HAVING clause works
4. **Use DataFrame insert for LIKE patterns** - Avoids SQL escaping issues
5. **Check sync status after deployment** - Verify `last_sync_status = 'CREATED'` or `'UPDATED'`
6. **Document alert purpose** - Use descriptive `alert_description`

#### ❌ DON'T:
1. **Don't use SQL INSERT for LIKE patterns** - Use DataFrame insertion instead
2. **Don't skip query validation** - Prevents deployment failures
3. **Don't hardcode catalog/schema in queries** - Use `${catalog}.${gold_schema}` placeholders
4. **Don't forget notification_channels** - Alert won't notify anyone!
5. **Don't update queries without validation** - Always re-validate after changes

## Monitoring and Observability

### Alert Sync Metrics

```sql
-- Recent sync job performance
SELECT 
    sync_run_id,
    sync_started_at,
    total_alerts,
    success_count,
    error_count,
    ROUND(success_count * 100.0 / total_alerts, 2) as success_rate_pct,
    total_duration_seconds,
    error_summary
FROM ${catalog}.${gold_schema}.alert_sync_metrics
ORDER BY sync_started_at DESC
LIMIT 10;

-- Average sync performance (last 7 days)
SELECT 
    COUNT(*) as total_runs,
    AVG(total_duration_seconds) as avg_duration_sec,
    AVG(success_count * 100.0 / total_alerts) as avg_success_rate,
    MAX(total_duration_seconds) as max_duration_sec
FROM ${catalog}.${gold_schema}.alert_sync_metrics
WHERE sync_started_at >= CURRENT_DATE() - 7;
```

### Alert Health Check

```sql
-- Identify alerts that haven't synced recently (potential issues)
SELECT 
    alert_id,
    alert_name,
    last_sync_status,
    last_synced_at,
    DATEDIFF(CURRENT_TIMESTAMP(), last_synced_at) as days_since_sync,
    last_sync_error
FROM ${catalog}.${gold_schema}.alert_configurations
WHERE is_enabled = TRUE
  AND (last_synced_at IS NULL OR last_synced_at < CURRENT_TIMESTAMP() - INTERVAL 7 DAYS)
ORDER BY last_synced_at ASC NULLS FIRST;

-- Count alerts by status
SELECT 
    last_sync_status,
    COUNT(*) as alert_count
FROM ${catalog}.${gold_schema}.alert_configurations
WHERE is_enabled = TRUE
GROUP BY last_sync_status
ORDER BY alert_count DESC;
```

### Validation Health

```sql
-- Recent validation failures
SELECT 
    alert_id,
    error_message,
    validation_timestamp
FROM ${catalog}.${gold_schema}.alert_validation_results
WHERE is_valid = FALSE
  AND validation_timestamp >= CURRENT_DATE() - 1
ORDER BY validation_timestamp DESC;
```

## Quick Reference Commands

### Complete Setup (First Time)
```bash
# Deploy and run everything
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev alerting_setup_orchestrator_job
```

### Day 2: Add/Update Alerts
```bash
# After updating alert_configurations table:
databricks bundle run -t dev alerting_validation_job  # Recommended
databricks bundle run -t dev alerting_deploy_job      # Required
```

### Day 2: Troubleshooting
```bash
# Re-seed all alerts (force refresh)
databricks bundle run -t dev alerting_seed_job

# Validate all queries
databricks bundle run -t dev alerting_validation_job

# Re-sync configuration to Databricks
databricks bundle run -t dev alerting_deploy_job
```

### Individual Atomic Jobs
```bash
# Run specific steps independently
databricks bundle run -t dev alerting_tables_job
databricks bundle run -t dev alerting_seed_job
databricks bundle run -t dev alerting_validation_job
databricks bundle run -t dev alerting_notifications_job
databricks bundle run -t dev alerting_deploy_job
```

## Troubleshooting

See [Appendix D](appendices/D-troubleshooting.md) for detailed troubleshooting guide.

## Summary

**To add a new alert:**
1. ✅ INSERT into `alert_configurations` table (or use DataFrame)
2. ✅ Run `alerting_validation_job` (catches errors early)
3. ✅ Run `alerting_deploy_job` (deploys to Databricks)
4. ✅ Verify in config table and Databricks UI

**To update an alert:**
1. ✅ UPDATE `alert_configurations` table
2. ✅ Re-validate if query changed
3. ✅ Re-run sync job (updates existing alert)

**To disable an alert:**
1. ✅ SET `is_enabled = FALSE`
2. ✅ Run sync job (deletes from Databricks)

## Next Steps

- [Appendix A](appendices/A-code-examples.md): Complete code examples
- [Appendix D](appendices/D-troubleshooting.md): Troubleshooting guide


