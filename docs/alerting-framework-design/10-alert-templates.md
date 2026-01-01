# 10 - Alert Templates

## Overview

The alerting framework includes **29 pre-built alert templates** across 5 domains. These templates provide validated queries, appropriate thresholds, and consistent structure.

## Template Categories

| Domain | Count | Purpose |
|--------|-------|---------|
| **COST** | 6 | Budget, spend, tag coverage |
| **SECURITY** | 8 | Access, audit, compliance |
| **PERFORMANCE** | 5 | Latency, utilization, queues |
| **RELIABILITY** | 5 | Job failures, SLA, availability |
| **QUALITY** | 5 | Freshness, completeness, accuracy |

## Pre-Built Alerts by Domain

### COST Domain (6 alerts)

| Alert ID | Name | Severity | Trigger Condition |
|----------|------|----------|-------------------|
| COST-001 | Daily Cost Spike | WARNING | Daily spend > $5,000 |
| COST-002 | Weekly Cost Change | WARNING | Week-over-week increase > 25% |
| COST-003 | Tag Coverage Alert | WARNING | Tagged spend < 80% |
| COST-004 | Budget Threshold Warning | WARNING | Monthly spend > 90% of budget |
| COST-005 | SKU Cost Spike | WARNING | Single SKU cost > 50% increase |
| COST-006 | Untagged Spend Alert | INFO | Untagged spend summary |

### SECURITY Domain (8 alerts)

| Alert ID | Name | Severity | Trigger Condition |
|----------|------|----------|-------------------|
| SEC-001 | Failed Access Attempts | CRITICAL | Failed access > 50/hour |
| SEC-002 | Admin Action Spike | WARNING | Admin actions > 10/hour |
| SEC-003 | Permission Changes | WARNING | Permission grants > 5/day |
| SEC-004 | Secrets Access | CRITICAL | Secret access > 20/hour |
| SEC-005 | IP Anomaly | WARNING | New IP addresses detected |
| SEC-006 | After-Hours Access | WARNING | Access outside business hours |
| SEC-007 | Sensitive Table Access | CRITICAL | PII table access spike |
| SEC-008 | Service Account Activity | INFO | Service account usage summary |

### PERFORMANCE Domain (5 alerts)

| Alert ID | Name | Severity | Trigger Condition |
|----------|------|----------|-------------------|
| PERF-001 | Query Latency Alert | WARNING | P95 latency > 300s |
| PERF-002 | Warehouse Queue Alert | WARNING | Queue depth > 10 |
| PERF-003 | Large Table Scan | WARNING | Full scan > 1B rows |
| PERF-004 | Cluster Memory Pressure | CRITICAL | Memory usage > 90% |
| PERF-005 | Spill to Disk | WARNING | Disk spill > 10GB |

### RELIABILITY Domain (5 alerts)

| Alert ID | Name | Severity | Trigger Condition |
|----------|------|----------|-------------------|
| RELI-001 | Job Failure Rate | CRITICAL | Failure rate > 10% |
| RELI-002 | Job Failure Count | WARNING | Failed jobs > 5/day |
| RELI-003 | Pipeline SLA Breach | CRITICAL | Pipeline duration > SLA |
| RELI-004 | Cluster Underutilization | INFO | Utilization < 20% |
| RELI-005 | Streaming Lag | WARNING | Processing lag > 1 hour |

### QUALITY Domain (5 alerts)

| Alert ID | Name | Severity | Trigger Condition |
|----------|------|----------|-------------------|
| QUAL-001 | Data Freshness | WARNING | Data age > 24 hours |
| QUAL-002 | NULL Rate Alert | WARNING | NULL rate > 10% |
| QUAL-003 | Duplicate Rate | WARNING | Duplicate rate > 1% |
| QUAL-004 | Schema Drift | WARNING | Schema change detected |
| QUAL-005 | Volume Anomaly | WARNING | Row count deviation > 50% |

## Template Query Examples

### COST-001: Daily Cost Spike

```sql
SELECT 
    SUM(list_cost) as daily_cost,
    'Daily cost $' || ROUND(SUM(list_cost), 2) || 
        ' exceeds $5000 threshold' as alert_message
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date = CURRENT_DATE() - 1
HAVING SUM(list_cost) > 5000
```

**Configuration:**
```yaml
threshold_column: daily_cost
threshold_operator: ">"
threshold_value_type: DOUBLE
threshold_value_double: 5000.0
schedule_cron: "0 0 6 * * ?"  # Daily 6 AM
empty_result_state: OK
```

### RELI-001: Job Failure Rate

```sql
SELECT 
    ROUND(
        SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        1
    ) as failure_rate,
    'Job failure rate ' || 
        ROUND(
            SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
            NULLIF(COUNT(*), 0), 
            1
        ) || '% exceeds 10% threshold' as alert_message
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
HAVING SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
       NULLIF(COUNT(*), 0) > 10
```

**Configuration:**
```yaml
threshold_column: failure_rate
threshold_operator: ">"
threshold_value_type: DOUBLE
threshold_value_double: 10.0
schedule_cron: "0 */30 * * * ?"  # Every 30 minutes
empty_result_state: OK
```

### SEC-001: Failed Access Attempts

```sql
SELECT 
    COUNT(*) as failed_attempts,
    'CRITICAL: ' || COUNT(*) || 
        ' failed access attempts in last hour' as alert_message
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - 1
  AND response_status_code >= 400
HAVING COUNT(*) > 50
```

**Configuration:**
```yaml
threshold_column: failed_attempts
threshold_operator: ">"
threshold_value_type: DOUBLE
threshold_value_double: 50.0
schedule_cron: "0 0 * * * ?"  # Hourly
empty_result_state: OK
severity: CRITICAL
```

## Seeding Alerts

### seed_all_alerts.py Structure

The seeding script uses **PySpark DataFrames** (not SQL INSERT) to avoid escaping issues:

```python
from datetime import datetime
from typing import Any, Dict, List
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, BooleanType, 
    IntegerType, DoubleType, TimestampType, ArrayType, MapType
)

# Define schema explicitly
ALERT_CONFIG_SCHEMA = StructType([
    StructField("alert_id", StringType(), False),
    StructField("alert_name", StringType(), False),
    StructField("alert_description", StringType(), True),
    StructField("agent_domain", StringType(), False),
    StructField("severity", StringType(), False),
    StructField("alert_query_template", StringType(), False),
    # ... all other fields
])

# Alert definitions
COST_ALERTS = [
    {
        "alert_id": "COST-001",
        "alert_name": "Daily Cost Spike Alert",
        "alert_description": "Alerts when daily spend exceeds threshold",
        "agent_domain": "COST",
        "severity": "WARNING",
        "alert_query_template": """
            SELECT SUM(list_cost) as daily_cost
            FROM ${catalog}.${gold_schema}.fact_usage
            WHERE usage_date = CURRENT_DATE() - 1
            HAVING SUM(list_cost) > 5000
        """,
        "threshold_column": "daily_cost",
        "threshold_operator": ">",
        "threshold_value_type": "DOUBLE",
        "threshold_value_double": 5000.0,
        "schedule_cron": "0 0 6 * * ?",
        "schedule_timezone": "America/Los_Angeles",
        "pause_status": "UNPAUSED",
        "is_enabled": True,
        "notification_channels": ["finops@company.com"],
        "notify_on_ok": False,
        "use_custom_template": False,
        "empty_result_state": "OK",
        "owner": "finops@company.com",
    },
    # ... more cost alerts
]

def insert_alerts(spark: SparkSession, catalog: str, gold_schema: str, alerts: List[Dict]) -> int:
    """Insert alerts using DataFrame (handles escaping correctly)."""
    
    rows = []
    for alert in alerts:
        rows.append({
            **alert,
            "created_by": "seed_all_alerts",
            "created_at": datetime.now(),
            # Set NULL for sync metadata
            "databricks_alert_id": None,
            "last_synced_at": None,
            "last_sync_status": None,
            "last_sync_error": None,
        })
    
    df = spark.createDataFrame(rows, schema=ALERT_CONFIG_SCHEMA)
    df.write.format("delta").mode("append").saveAsTable(
        f"{catalog}.{gold_schema}.alert_configurations"
    )
    
    return len(rows)
```

### Why DataFrame Over SQL INSERT?

```sql
-- ❌ SQL INSERT: Escaping issues with LIKE patterns
INSERT INTO alert_configurations (alert_query_template)
VALUES ('SELECT * FROM t WHERE col LIKE ''%pattern%''');
-- Result: LIKE %pattern% (quotes stripped!)
```

```python
# ✅ DataFrame: Handles escaping correctly
df = spark.createDataFrame([{
    "alert_query_template": "SELECT * FROM t WHERE col LIKE '%pattern%'"
}], schema=ALERT_CONFIG_SCHEMA)
df.write.saveAsTable("alert_configurations")
# Result: LIKE '%pattern%' (correct!)
```

## Customizing Templates

### Override Threshold

```sql
-- Change threshold for existing alert
UPDATE alert_configurations
SET threshold_value_double = 10000.0,
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

### Override Schedule

```sql
-- Change from 6 AM to 8 AM
UPDATE alert_configurations
SET schedule_cron = '0 0 8 * * ?',
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

### Override Notification Channels

```sql
-- Add additional recipients
UPDATE alert_configurations
SET notification_channels = array(
    'finops@company.com', 
    'cfo@company.com',
    'finops_slack'
),
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'COST-001';
```

## Creating Custom Alerts

### Pattern for New Alert

```sql
INSERT INTO alert_configurations (
    alert_id, alert_name, alert_description,
    agent_domain, severity,
    alert_query_template,
    threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    empty_result_state,
    schedule_cron, schedule_timezone, pause_status, is_enabled,
    notification_channels, notify_on_ok, use_custom_template,
    owner, created_by, created_at
) VALUES (
    'CUSTOM-001',                    -- Unique ID
    'My Custom Alert',               -- Display name
    'Description of what this alerts on',
    'COST',                          -- Domain
    'WARNING',                       -- Severity
    'SELECT metric as value FROM ${catalog}.${gold_schema}.my_table HAVING metric > 100',
    'value',                         -- Column to evaluate
    '>',                             -- Operator
    'DOUBLE',                        -- Value type
    100.0,                           -- Threshold
    'OK',                            -- Empty result state
    '0 0 6 * * ?',                   -- Schedule (daily 6 AM)
    'America/Los_Angeles',           -- Timezone
    'PAUSED',                        -- Start paused for testing
    TRUE,                            -- Enabled for sync
    array('my-team@company.com'),    -- Notifications
    FALSE,                           -- Don't notify on OK
    FALSE,                           -- No custom template
    'my-team@company.com',           -- Owner
    'admin',                         -- Created by
    CURRENT_TIMESTAMP()              -- Created at
);
```

### Validation Before Enabling

```bash
# 1. Add alert with PAUSED status
# 2. Run validation
databricks bundle run -t dev alert_query_validation_job

# 3. Check validation results
# 4. If valid, unpause
UPDATE alert_configurations
SET pause_status = 'UNPAUSED'
WHERE alert_id = 'CUSTOM-001';

# 5. Sync to Databricks
databricks bundle run -t dev sql_alert_deployment_job
```

## Template Best Practices

### 1. Always Include alert_message

```sql
SELECT 
    metric as value,
    'Metric is ' || metric || ' (threshold: 100)' as alert_message
FROM table
```

### 2. Use HAVING for Filtering

```sql
-- ✅ HAVING filters results
SELECT SUM(cost) as total HAVING SUM(cost) > 5000

-- ❌ WHERE doesn't aggregate
SELECT SUM(cost) as total WHERE SUM(cost) > 5000  -- Invalid!
```

### 3. Handle Division by Zero

```sql
SELECT failed / NULLIF(total, 0) * 100 as rate
```

### 4. Start with PAUSED Status

```sql
pause_status = 'PAUSED'  -- Test before enabling
```

### 5. Use Appropriate Schedules

| Alert Type | Recommended Schedule |
|------------|----------------------|
| Security (critical) | Every 5-15 minutes |
| Performance | Every 15-30 minutes |
| Cost | Daily (morning) |
| Quality | Hourly or daily |
| Summary/Info | Daily or weekly |

## Next Steps

- **[11-Implementation Guide](11-implementation-guide.md)**: Step-by-step setup
- **[12-Deployment and Operations](12-deployment-and-operations.md)**: Production deployment
- **[04-Alert Query Patterns](04-alert-query-patterns.md)**: Query best practices


