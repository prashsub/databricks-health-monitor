# Alerting Framework Deployment Guide

**Version:** 2.0  
**Last Updated:** December 30, 2025

---

## Overview

This guide covers deploying the alerting framework from development through production.

---

## Prerequisites

1. **Databricks Workspace** with SQL warehouse
2. **Unity Catalog** enabled
3. **Databricks CLI** configured with authentication
4. **Gold layer tables** deployed (fact_usage, etc.)

---

## Deployment Steps

### Step 1: Deploy Asset Bundle Resources

```bash
# From project root
cd DatabricksHealthMonitor

# Validate bundle configuration
databricks bundle validate -t dev

# Deploy to development
databricks bundle deploy -t dev
```

**Expected Output:**
```
Uploading bundle files to /Workspace/Users/.../DatabricksHealthMonitor/files
Starting resource deployment
Deploying alerting_tables_setup_job...
Deploying alert_query_validation_job...
Deploying sql_alert_deployment_job...
Deploying alerting_layer_setup_job...
Deployment complete!
```

### Step 2: Run Setup Job

```bash
# Run the complete alerting setup
databricks bundle run -t dev alerting_layer_setup_job
```

This orchestrator job will:
1. Create/update configuration tables
2. Seed minimal default alerts
3. Sync notification destinations
4. Validate all alert queries
5. Deploy alerts (in dry-run mode initially)

**Expected Output:**
```
Run URL: https://workspace.cloud.databricks.com/jobs/...
Run completed successfully
```

### Step 3: Verify Table Creation

```sql
-- In Databricks SQL
SHOW TABLES IN catalog.gold LIKE 'alert*';

-- Check tables were created
SELECT COUNT(*) FROM catalog.gold.alert_configurations;
SELECT COUNT(*) FROM catalog.gold.notification_destinations;
```

### Step 4: Add Alert Configurations

Add your specific alerts to the configuration table:

```sql
-- Example: Add a cost alert
INSERT INTO catalog.gold.alert_configurations (
    alert_id, alert_name, alert_description, agent_domain, severity,
    alert_query_template, threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    empty_result_state, schedule_cron, schedule_timezone,
    pause_status, is_enabled, notification_channels,
    notify_on_ok, use_custom_template,
    owner, created_by, created_at
) VALUES (
    'COST-002',
    'Weekly Cost Trend',
    'Alerts on weekly cost increases over 25%',
    'COST',
    'WARNING',
    'WITH w1 AS (SELECT SUM(list_cost) c FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= DATE_TRUNC(''week'', CURRENT_DATE())), w2 AS (SELECT SUM(list_cost) c FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= DATE_TRUNC(''week'', CURRENT_DATE() - 7) AND usage_date < DATE_TRUNC(''week'', CURRENT_DATE())) SELECT ROUND((w1.c - w2.c) / NULLIF(w2.c, 0) * 100, 1) as pct_change, ''Weekly cost changed by '' || ROUND((w1.c - w2.c) / NULLIF(w2.c, 0) * 100, 1) || ''%'' as alert_message FROM w1, w2 WHERE (w1.c - w2.c) / NULLIF(w2.c, 0) > 0.25',
    'pct_change',
    '>',
    'DOUBLE',
    25.0,
    'OK',
    '0 0 8 ? * MON',
    'America/Los_Angeles',
    'UNPAUSED',
    TRUE,
    array('finops@company.com'),
    FALSE,
    FALSE,
    'finops@company.com',
    'admin',
    CURRENT_TIMESTAMP()
);
```

### Step 5: Validate Queries

Run query validation to ensure all queries are valid:

```bash
databricks bundle run -t dev alert_query_validation_job
```

**Expected Output:**
```
Validating 3 enabled alerts...
✓ COST-001: Valid
✓ COST-002: Valid
✓ COST-012: Valid
All 3 alert queries are valid!
```

### Step 6: Enable Alert Deployment

Edit the job YAML to disable dry-run:

```yaml
# resources/alerting/sql_alert_deployment_job.yml
base_parameters:
  dry_run: "false"  # Change from "true" to "false"
```

Redeploy and run:

```bash
databricks bundle deploy -t dev
databricks bundle run -t dev sql_alert_deployment_job
```

**Expected Output:**
```
Processing 3 enabled alerts...

[1/3] COST-001: Daily Cost Spike
  Action: CREATE
  ✓ OK (0.85s)

[2/3] COST-002: Weekly Cost Trend
  Action: CREATE
  ✓ OK (0.72s)

[3/3] COST-012: Tag Coverage Alert
  Action: CREATE
  ✓ OK (0.68s)

================================================================================
SYNC SUMMARY
================================================================================
Total: 3 | Success: 3 | Errors: 0
Deleted: 0
```

### Step 7: Verify Deployment

1. **Check Databricks UI:**
   - Navigate to SQL → Alerts
   - Verify alerts appear with correct names

2. **Check Configuration Table:**
   ```sql
   SELECT 
       alert_id,
       alert_name,
       databricks_alert_id,
       last_sync_status,
       last_synced_at
   FROM catalog.gold.alert_configurations
   WHERE is_enabled = TRUE;
   ```

---

## Production Deployment

### Step 1: Update Target Variables

Edit `databricks.yml` for production:

```yaml
targets:
  prod:
    mode: production
    variables:
      catalog: prod_catalog
      gold_schema: gold
      warehouse_id: "your-prod-warehouse-id"
```

### Step 2: Deploy to Production

```bash
# Validate first
databricks bundle validate -t prod

# Deploy
databricks bundle deploy -t prod

# Run setup
databricks bundle run -t prod alerting_layer_setup_job
```

### Step 3: Configure Production Schedules

Ensure all alerts have appropriate production schedules:

```sql
UPDATE catalog.gold.alert_configurations
SET 
    pause_status = 'UNPAUSED',
    updated_at = CURRENT_TIMESTAMP(),
    updated_by = 'admin'
WHERE is_enabled = TRUE;
```

### Step 4: Configure Notification Destinations

Add production notification destinations:

```sql
INSERT INTO catalog.gold.notification_destinations VALUES (
    'prod_oncall',
    'Production On-Call',
    'PAGERDUTY',
    NULL,  -- Will be created by sync
    '{"routing_key": "your-pagerduty-key"}',
    'platform@company.com',
    TRUE,
    'admin',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    map('environment', 'production')
);
```

### Step 5: Run Final Deployment

```bash
# Ensure dry_run is false in prod YAML
databricks bundle run -t prod sql_alert_deployment_job
```

---

## Job Reference

### alerting_layer_setup_job (Orchestrator)

**Purpose:** Complete alerting framework setup

**Tasks:**
1. `setup_alerting_tables` - Create/update tables
2. `validate_alert_queries` - Validate all queries
3. `sync_notification_destinations` - Sync destinations
4. `deploy_sql_alerts` - Deploy to Databricks

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| catalog | Unity Catalog name | From variable |
| gold_schema | Schema name | From variable |
| warehouse_id | SQL Warehouse ID | From variable |

### alert_query_validation_job (Atomic)

**Purpose:** Validate alert queries before deployment

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| catalog | Unity Catalog name | From variable |
| gold_schema | Schema name | From variable |

### sql_alert_deployment_job (Atomic)

**Purpose:** Sync alerts to Databricks SQL

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| catalog | Unity Catalog name | From variable |
| gold_schema | Schema name | From variable |
| warehouse_id | SQL Warehouse ID | From variable |
| dry_run | Skip API calls | "true" |
| api_base | API endpoint | "/api/2.0/alerts" |
| delete_disabled | Delete disabled alerts | "true" |

---

## Dry Run Mode

When `dry_run: "true"`:
- All validation is performed
- Config table is NOT updated
- SQL Alerts API is NOT called
- Summary shows what WOULD happen

**Use dry run to:**
- Validate new alerts before deployment
- Test configuration changes
- Audit existing setup

---

## Rollback Procedures

### Rollback Single Alert

```sql
-- Disable alert (stops evaluation)
UPDATE catalog.gold.alert_configurations
SET 
    is_enabled = FALSE,
    pause_status = 'PAUSED',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-002';

-- Re-run sync to delete from Databricks
-- databricks bundle run -t prod sql_alert_deployment_job
```

### Rollback All Alerts

```sql
-- Disable all alerts
UPDATE catalog.gold.alert_configurations
SET 
    is_enabled = FALSE,
    pause_status = 'PAUSED',
    updated_at = CURRENT_TIMESTAMP();

-- Re-run sync to delete all from Databricks
-- databricks bundle run -t prod sql_alert_deployment_job
```

### Restore from Time Travel

```sql
-- Find previous version
DESCRIBE HISTORY catalog.gold.alert_configurations;

-- Restore to previous version
RESTORE TABLE catalog.gold.alert_configurations TO VERSION AS OF 5;

-- Re-run sync
-- databricks bundle run -t prod sql_alert_deployment_job
```

---

## Troubleshooting

### Alert Not Creating

**Symptom:** Alert not appearing in Databricks UI

**Check:**
1. Is `is_enabled = TRUE`?
2. Is `dry_run = false`?
3. Check `last_sync_status` and `last_sync_error`

```sql
SELECT alert_id, last_sync_status, last_sync_error
FROM catalog.gold.alert_configurations
WHERE alert_id = 'COST-002';
```

### Query Validation Failed

**Symptom:** Validation job fails

**Check:**
1. Run query manually in SQL editor
2. Check for missing tables/columns
3. Verify ${catalog} and ${gold_schema} placeholders

### API Errors

**Symptom:** Sync job shows API errors

**Common Errors:**
- `403 Forbidden` - Check token/permissions
- `400 Bad Request` - Check payload format
- `404 Not Found` - Alert ID incorrect

**Resolution:**
```sql
-- Clear stale alert ID to force recreation
UPDATE catalog.gold.alert_configurations
SET databricks_alert_id = NULL
WHERE alert_id = 'COST-002';
```

### Notification Not Received

**Symptom:** Alert triggered but no notification

**Check:**
1. Notification destination configured correctly
2. Destination mapping exists
3. Email/Slack channel accessible

```sql
SELECT * FROM catalog.gold.notification_destinations
WHERE destination_id = 'my_channel';
```

---

## Best Practices

1. **Always validate before deploying** - Run validation job first
2. **Use dry-run for testing** - Verify changes without side effects
3. **Start with PAUSED alerts** - Enable after verification
4. **Monitor sync metrics** - Check `alert_sync_metrics` table
5. **Use tags for organization** - Filter alerts by team/domain
6. **Document alert owners** - Ensure accountability
7. **Test notifications** - Verify delivery before relying on them

