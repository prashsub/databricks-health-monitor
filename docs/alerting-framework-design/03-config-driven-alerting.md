# 03 - Config-Driven Alerting

## Design Philosophy

**Core Principle**: Alert rules should be data, not code.

Traditional approach (❌):
```python
# Hardcoded in Python
if daily_cost > 5000:
    send_alert("Cost exceeded $5000")
```

Config-driven approach (✅):
```sql
-- Stored in Delta table
INSERT INTO alert_configurations (
    alert_id, alert_name, threshold_value_double, ...
) VALUES ('COST-001', 'Daily Cost Spike', 5000.0, ...);
```

## Benefits of Config-Driven Alerting

| Benefit | Description |
|---------|-------------|
| **Runtime Updates** | Change thresholds without code deployment |
| **Version History** | Delta time travel for audit trail |
| **Centralized View** | Query all alerts with SQL |
| **Separation of Concerns** | Alert logic vs. deployment logic |
| **Self-Service** | Analysts can add alerts via SQL |
| **Testing** | Validate queries before deployment |

## Configuration Tables

### alert_configurations (Primary)

The central table storing all alert rules.

```sql
CREATE TABLE ${catalog}.${gold_schema}.alert_configurations (
    -- ═══════════════════════════════════════════════════════════════════
    -- IDENTITY FIELDS
    -- ═══════════════════════════════════════════════════════════════════
    alert_id STRING NOT NULL,
    -- Primary key. Convention: <DOMAIN>-<NUMBER>
    -- Examples: COST-001, SEC-003, PERF-012
    
    alert_name STRING NOT NULL,
    -- Human-readable display name
    -- Example: "Daily Cost Spike Alert"
    
    alert_description STRING,
    -- Detailed description for documentation
    -- Example: "Alerts when daily spend exceeds budget threshold"
    
    -- ═══════════════════════════════════════════════════════════════════
    -- CLASSIFICATION FIELDS
    -- ═══════════════════════════════════════════════════════════════════
    agent_domain STRING NOT NULL,
    -- Business domain for routing and organization
    -- Values: COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY
    
    severity STRING NOT NULL,
    -- Alert urgency level
    -- Values: CRITICAL (page immediately), WARNING (investigate), INFO (FYI)
    
    -- ═══════════════════════════════════════════════════════════════════
    -- QUERY CONFIGURATION
    -- ═══════════════════════════════════════════════════════════════════
    alert_query_template STRING NOT NULL,
    -- SQL query with ${catalog} and ${gold_schema} placeholders
    -- Must return the threshold_column
    -- Should include alert_message column for notifications
    
    query_source STRING,
    -- Origin of the query for documentation
    -- Values: CUSTOM, TVF, METRIC_VIEW, MONITORING
    
    source_artifact_name STRING,
    -- Reference to source artifact (e.g., TVF name)
    -- Example: "get_daily_cost_summary"
    
    -- ═══════════════════════════════════════════════════════════════════
    -- THRESHOLD CONFIGURATION
    -- ═══════════════════════════════════════════════════════════════════
    threshold_column STRING NOT NULL,
    -- Column name in query result to evaluate
    -- Example: "daily_cost", "failure_rate"
    
    threshold_operator STRING NOT NULL,
    -- Comparison operator
    -- Values: >, <, >=, <=, =, !=
    
    threshold_value_type STRING NOT NULL,
    -- Data type of threshold
    -- Values: DOUBLE, STRING, BOOLEAN
    
    threshold_value_double DOUBLE,
    -- Numeric threshold (when type = DOUBLE)
    
    threshold_value_string STRING,
    -- String threshold (when type = STRING)
    
    threshold_value_bool BOOLEAN,
    -- Boolean threshold (when type = BOOLEAN)
    
    -- ═══════════════════════════════════════════════════════════════════
    -- EVALUATION CONFIGURATION
    -- ═══════════════════════════════════════════════════════════════════
    empty_result_state STRING NOT NULL,
    -- State when query returns no rows
    -- Values: OK (no alert), TRIGGERED (alert), ERROR (failure)
    
    aggregation_type STRING,
    -- How to aggregate multiple result rows
    -- Values: SUM, COUNT, COUNT_DISTINCT, AVG, MEDIAN, MIN, MAX, STDDEV, FIRST
    -- NULL/NONE means no aggregation (use first row)
    
    -- ═══════════════════════════════════════════════════════════════════
    -- SCHEDULE CONFIGURATION
    -- ═══════════════════════════════════════════════════════════════════
    schedule_cron STRING NOT NULL,
    -- Quartz cron expression
    -- Example: "0 0 6 * * ?" (daily at 6 AM)
    
    schedule_timezone STRING NOT NULL,
    -- IANA timezone identifier
    -- Example: "America/Los_Angeles"
    
    pause_status STRING NOT NULL,
    -- Whether alert schedule is paused
    -- Values: UNPAUSED (active), PAUSED (suspended)
    
    is_enabled BOOLEAN NOT NULL,
    -- Whether to deploy this alert
    -- FALSE = skip during sync (for draft alerts)
    
    -- ═══════════════════════════════════════════════════════════════════
    -- NOTIFICATION CONFIGURATION
    -- ═══════════════════════════════════════════════════════════════════
    notification_channels ARRAY<STRING>,
    -- List of channel IDs or direct email addresses
    -- Example: array('finops_team', 'oncall@company.com')
    
    notify_on_ok BOOLEAN NOT NULL,
    -- Send notification when alert clears
    
    retrigger_seconds INT,
    -- Cooldown before re-triggering (prevents spam)
    -- NULL = use default
    
    -- ═══════════════════════════════════════════════════════════════════
    -- CUSTOM TEMPLATE CONFIGURATION
    -- ═══════════════════════════════════════════════════════════════════
    use_custom_template BOOLEAN NOT NULL,
    -- Whether to use custom notification templates
    
    custom_subject_template STRING,
    -- Custom email subject with {{PLACEHOLDERS}}
    
    custom_body_template STRING,
    -- Custom notification body with {{PLACEHOLDERS}}
    
    -- ═══════════════════════════════════════════════════════════════════
    -- OWNERSHIP & AUDIT
    -- ═══════════════════════════════════════════════════════════════════
    owner STRING NOT NULL,
    -- Alert owner (email or team)
    
    created_by STRING NOT NULL,
    -- Who created this config
    
    created_at TIMESTAMP NOT NULL,
    -- When config was created
    
    updated_by STRING,
    -- Who last updated
    
    updated_at TIMESTAMP,
    -- When last updated
    
    tags MAP<STRING, STRING>,
    -- Key-value tags for filtering
    -- Example: map('team', 'finops', 'project', 'cost-monitoring')
    
    -- ═══════════════════════════════════════════════════════════════════
    -- SYNC METADATA (populated by sync engine)
    -- ═══════════════════════════════════════════════════════════════════
    databricks_alert_id STRING,
    -- UUID of deployed alert (populated after sync)
    
    databricks_display_name STRING,
    -- Actual display name in Databricks (may differ)
    
    last_synced_at TIMESTAMP,
    -- When last synced to Databricks
    
    last_sync_status STRING,
    -- Result of last sync: SUCCESS, ERROR, SKIPPED
    
    last_sync_error STRING,
    -- Error message if sync failed
    
    -- ═══════════════════════════════════════════════════════════════════
    -- CONSTRAINTS
    -- ═══════════════════════════════════════════════════════════════════
    CONSTRAINT pk_alert_configurations PRIMARY KEY (alert_id) NOT ENFORCED
)
USING DELTA
COMMENT 'Config-driven alert rules for Databricks SQL Alerts'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);
```

### notification_destinations

Maps internal channel IDs to Databricks workspace destination UUIDs.

```sql
CREATE TABLE ${catalog}.${gold_schema}.notification_destinations (
    destination_id STRING NOT NULL,
    -- Internal ID (e.g., 'finops_team', 'oncall_channel')
    
    destination_name STRING NOT NULL,
    -- Display name
    
    destination_type STRING NOT NULL,
    -- Type: EMAIL, SLACK, WEBHOOK, TEAMS, PAGERDUTY
    
    databricks_destination_id STRING,
    -- Workspace destination UUID (from Databricks)
    -- NULL if not yet created
    
    config_json STRING,
    -- Type-specific configuration
    -- For Slack: {"url": "https://hooks.slack.com/..."}
    -- For Email: {"addresses": ["a@co.com", "b@co.com"]}
    
    owner STRING NOT NULL,
    is_enabled BOOLEAN NOT NULL,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING,
    updated_at TIMESTAMP,
    tags MAP<STRING, STRING>,
    
    CONSTRAINT pk_notification_destinations PRIMARY KEY (destination_id) NOT ENFORCED
)
USING DELTA;
```

### alert_validation_results

Stores query validation results for debugging.

```sql
CREATE TABLE ${catalog}.${gold_schema}.alert_validation_results (
    alert_id STRING NOT NULL,
    is_valid BOOLEAN NOT NULL,
    error_message STRING,
    validation_timestamp TIMESTAMP NOT NULL
)
USING DELTA;
```

### alert_sync_metrics

Observability table for sync operations.

```sql
CREATE TABLE ${catalog}.${gold_schema}.alert_sync_metrics (
    sync_run_id STRING NOT NULL,
    -- UUID for each sync run
    
    sync_started_at TIMESTAMP NOT NULL,
    sync_ended_at TIMESTAMP NOT NULL,
    
    -- Counts
    total_alerts INT NOT NULL,
    success_count INT NOT NULL,
    error_count INT NOT NULL,
    created_count INT NOT NULL,
    updated_count INT NOT NULL,
    deleted_count INT NOT NULL,
    skipped_count INT NOT NULL,
    
    -- Latency metrics
    avg_api_latency_ms DOUBLE NOT NULL,
    max_api_latency_ms DOUBLE NOT NULL,
    min_api_latency_ms DOUBLE NOT NULL,
    p95_api_latency_ms DOUBLE NOT NULL,
    total_duration_seconds DOUBLE NOT NULL,
    
    -- Context
    dry_run BOOLEAN NOT NULL,
    catalog STRING NOT NULL,
    gold_schema STRING NOT NULL,
    error_summary STRING,
    
    CONSTRAINT pk_alert_sync_metrics PRIMARY KEY (sync_run_id) NOT ENFORCED
)
USING DELTA;
```

## Alert ID Convention

### Format

```
<DOMAIN>-<NUMBER>

Where:
- DOMAIN: 4-letter prefix (COST, SECU, PERF, RELI, QUAL)
- NUMBER: 3-digit zero-padded sequence (001, 002, ...)
```

### Examples by Domain

| Domain | Prefix | Examples |
|--------|--------|----------|
| Cost | COST | COST-001, COST-002, COST-003 |
| Security | SEC | SEC-001, SEC-002, SEC-003 |
| Performance | PERF | PERF-001, PERF-002, PERF-003 |
| Reliability | RELI | RELI-001, RELI-002, RELI-003 |
| Quality | QUAL | QUAL-001, QUAL-002, QUAL-003 |

### Query by Domain

```sql
-- All cost alerts
SELECT * FROM alert_configurations WHERE agent_domain = 'COST';

-- All critical alerts
SELECT * FROM alert_configurations WHERE severity = 'CRITICAL';

-- All enabled alerts by domain
SELECT agent_domain, COUNT(*) as count
FROM alert_configurations
WHERE is_enabled = TRUE
GROUP BY agent_domain;
```

## Severity Levels

### Definitions

| Severity | Meaning | Response Time | Typical Notification |
|----------|---------|---------------|----------------------|
| **CRITICAL** | Immediate action required | < 15 minutes | PagerDuty page, SMS |
| **WARNING** | Investigate soon | < 4 hours | Slack, email |
| **INFO** | Informational | Daily review | Email digest |

### Guidelines by Domain

| Domain | CRITICAL | WARNING | INFO |
|--------|----------|---------|------|
| **COST** | Budget exhaustion | Daily spike > 50% | Weekly summary |
| **SECURITY** | Unauthorized access | Failed access > 100 | Daily audit summary |
| **PERFORMANCE** | P95 > 5 minutes | P95 > 1 minute | Slow query summary |
| **RELIABILITY** | Failure rate > 50% | Failure rate > 10% | Daily job summary |
| **QUALITY** | Data loss detected | Freshness > 24h | Weekly quality report |

## Configuration Patterns

### Pattern 1: Simple Threshold Alert

```sql
INSERT INTO alert_configurations (
    alert_id, alert_name, alert_description,
    agent_domain, severity,
    alert_query_template,
    threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    empty_result_state, aggregation_type,
    schedule_cron, schedule_timezone, pause_status, is_enabled,
    notification_channels, notify_on_ok, use_custom_template,
    owner, created_by, created_at
) VALUES (
    'COST-001',
    'Daily Cost Spike',
    'Alerts when daily spend exceeds $5000',
    'COST',
    'WARNING',
    'SELECT SUM(list_cost) as daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 HAVING SUM(list_cost) > 5000',
    'daily_cost',
    '>',
    'DOUBLE',
    5000.0,
    'OK',
    'SUM',
    '0 0 6 * * ?',
    'America/Los_Angeles',
    'UNPAUSED',
    TRUE,
    array('finops@company.com'),
    FALSE,
    FALSE,
    'finops@company.com',
    'system',
    CURRENT_TIMESTAMP()
);
```

### Pattern 2: Percentage-Based Alert

```sql
INSERT INTO alert_configurations (...) VALUES (
    'RELI-001',
    'Job Failure Rate',
    'Alerts when job failure rate exceeds 10%',
    'RELIABILITY',
    'CRITICAL',
    'SELECT ROUND(SUM(CASE WHEN result_state = ''FAILED'' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as failure_rate FROM ${catalog}.${gold_schema}.fact_job_run_timeline WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS HAVING failure_rate > 10',
    'failure_rate',
    '>',
    'DOUBLE',
    10.0,
    ...
);
```

### Pattern 3: Count-Based Alert

```sql
INSERT INTO alert_configurations (...) VALUES (
    'SEC-001',
    'Failed Access Attempts',
    'Alerts when failed access attempts exceed 50 in 1 hour',
    'SECURITY',
    'CRITICAL',
    'SELECT COUNT(*) as failed_attempts FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR AND response_status_code >= 400 HAVING COUNT(*) > 50',
    'failed_attempts',
    '>',
    'DOUBLE',
    50.0,
    ...
);
```

### Pattern 4: Alert with Custom Template

```sql
INSERT INTO alert_configurations (
    ...,
    use_custom_template,
    custom_subject_template,
    custom_body_template,
    ...
) VALUES (
    ...,
    TRUE,
    '[{{SEVERITY}}] {{ALERT_NAME}} - Daily Cost ${{QUERY_RESULT_VALUE}}',
    '<h2>Cost Alert</h2><p>Daily cost {{QUERY_RESULT_VALUE}} exceeded threshold {{THRESHOLD_VALUE}}</p><p>Owner: {{OWNER}}</p>',
    ...
);
```

## Updating Configurations

### Enable/Disable Alert

```sql
-- Disable without deleting
UPDATE alert_configurations
SET is_enabled = FALSE, updated_by = 'admin', updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';

-- Re-enable
UPDATE alert_configurations
SET is_enabled = TRUE, updated_by = 'admin', updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

### Change Threshold

```sql
UPDATE alert_configurations
SET threshold_value_double = 10000.0,
    updated_by = 'finops_admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

### Change Schedule

```sql
UPDATE alert_configurations
SET schedule_cron = '0 0 8 * * ?',  -- Change from 6 AM to 8 AM
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

### Pause Alert

```sql
UPDATE alert_configurations
SET pause_status = 'PAUSED',
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

## Version History via Delta Time Travel

### View Alert Configuration History

```sql
-- All versions of a specific alert
SELECT * FROM alert_configurations VERSION AS OF 1
WHERE alert_id = 'COST-001';

-- Changes in last 7 days
SELECT * FROM alert_configurations TIMESTAMP AS OF '2025-12-24'
WHERE alert_id = 'COST-001';

-- Describe history
DESCRIBE HISTORY alert_configurations;
```

### Restore Previous Configuration

```sql
-- Restore specific alert to previous version
MERGE INTO alert_configurations AS target
USING (
    SELECT * FROM alert_configurations VERSION AS OF 5
    WHERE alert_id = 'COST-001'
) AS source
ON target.alert_id = source.alert_id
WHEN MATCHED THEN UPDATE SET *;
```

## Unity Catalog Considerations

### Table Creation Limitations

Unity Catalog has limitations on DDL:

| Feature | Support | Alternative |
|---------|---------|-------------|
| CHECK constraints | ❌ | Validate in application |
| DEFAULT values | ❌ | Provide in INSERT |
| PARTITIONED BY + CLUSTER BY AUTO | ❌ | Choose one |

### Why No CHECK Constraints?

```sql
-- ❌ This will fail in Unity Catalog
CREATE TABLE alert_configurations (
    severity STRING NOT NULL
        CONSTRAINT chk_severity CHECK (severity IN ('CRITICAL', 'WARNING', 'INFO'))
);

-- ✅ Validate in application code instead
if severity not in ['CRITICAL', 'WARNING', 'INFO']:
    raise ValueError(f"Invalid severity: {severity}")
```

## Next Steps

- **[04-Alert Query Patterns](04-alert-query-patterns.md)**: SQL query best practices
- **[05-Databricks SDK Integration](05-databricks-sdk-integration.md)**: SDK types and methods
- **[06-Notification Destinations](06-notification-destinations.md)**: Channel configuration


