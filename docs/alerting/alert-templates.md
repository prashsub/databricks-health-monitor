# Pre-Built Alert Templates

**Version:** 2.0  
**Last Updated:** December 30, 2025

---

## Overview

The alerting framework includes pre-built templates for common alerting scenarios. These templates provide:

- ✅ Validated SQL queries
- ✅ Appropriate thresholds
- ✅ Proper severity levels
- ✅ Schedule recommendations
- ✅ Consistent naming

---

## Available Templates

### Cost Domain Templates

| Template ID | Name | Description | Default Threshold |
|-------------|------|-------------|-------------------|
| `COST_DAILY_SPIKE` | Daily Cost Spike | Daily spend exceeds threshold | $5,000 |
| `COST_WEEKLY_CHANGE` | Weekly Cost Change | Week-over-week increase | 25% |
| `COST_TAG_COVERAGE` | Tag Coverage Alert | Untagged spend above threshold | 20% |
| `COST_BUDGET_EXHAUSTION` | Budget Exhaustion Warning | Projected to exceed budget | 90% |
| `COST_SKU_SPIKE` | SKU Cost Spike | Individual SKU cost spike | 50% |

### Reliability Domain Templates

| Template ID | Name | Description | Default Threshold |
|-------------|------|-------------|-------------------|
| `RELI_JOB_FAILURE_RATE` | Job Failure Rate | Overall failure rate | 10% |
| `RELI_JOB_FAILURE_COUNT` | Job Failure Count | Absolute failure count | 5 jobs |
| `RELI_PIPELINE_SLA` | Pipeline SLA Breach | Pipeline exceeds SLA | 4 hours |
| `RELI_CLUSTER_UTILIZATION` | Cluster Underutilization | Low resource utilization | 20% |
| `RELI_STREAMING_LAG` | Streaming Lag | Processing lag exceeds threshold | 1 hour |

### Security Domain Templates

| Template ID | Name | Description | Default Threshold |
|-------------|------|-------------|-------------------|
| `SECU_FAILED_ACCESS` | Failed Access Attempts | High failed access rate | 50 attempts |
| `SECU_ADMIN_ACTIONS` | Admin Action Spike | Unusual admin activity | 10 actions |
| `SECU_PERMISSION_CHANGES` | Permission Changes | Permission grants/revokes | 5 changes |
| `SECU_SECRETS_ACCESS` | Secrets Access Alert | Secret access anomaly | 20 accesses |
| `SECU_IP_ANOMALY` | IP Anomaly Alert | Access from unusual IPs | 1 new IP |

### Performance Domain Templates

| Template ID | Name | Description | Default Threshold |
|-------------|------|-------------|-------------------|
| `PERF_QUERY_LATENCY` | Query Latency Alert | P95 query latency high | 300 seconds |
| `PERF_WAREHOUSE_QUEUE` | Warehouse Queue Alert | Query queue building | 10 queries |
| `PERF_TABLE_SCAN` | Large Table Scan | Full table scans detected | 1 billion rows |
| `PERF_CLUSTER_MEMORY` | Cluster Memory Pressure | OOM risk | 90% |
| `PERF_SPILL_TO_DISK` | Spill to Disk Alert | Excessive disk spills | 10 GB |

### Quality Domain Templates

| Template ID | Name | Description | Default Threshold |
|-------------|------|-------------|-------------------|
| `QUAL_DATA_FRESHNESS` | Data Freshness Alert | Stale data detected | 24 hours |
| `QUAL_NULL_RATE` | Null Rate Alert | High null rate in column | 10% |
| `QUAL_DUPLICATE_RATE` | Duplicate Rate Alert | Duplicate records found | 1% |
| `QUAL_SCHEMA_DRIFT` | Schema Drift Alert | Schema change detected | 1 change |
| `QUAL_VOLUME_ANOMALY` | Volume Anomaly | Row count deviation | 50% |

---

## Template Definitions

### COST_DAILY_SPIKE

**Purpose:** Alert when daily spending exceeds a threshold.

```yaml
template_id: COST_DAILY_SPIKE
domain: COST
default_severity: WARNING
default_threshold: 5000.0

parameters:
  - name: threshold_usd
    type: DOUBLE
    description: Daily cost threshold in USD
    default: 5000.0

query_template: |
  SELECT 
    SUM(list_cost) as daily_cost,
    'Daily cost $' || ROUND(SUM(list_cost), 2) || ' exceeds threshold (${{threshold_usd}})' as alert_message
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date = CURRENT_DATE() - 1
  HAVING SUM(list_cost) > {{threshold_usd}}

threshold_column: daily_cost
threshold_operator: ">"
recommended_schedule: "0 0 6 * * ?"  # Daily at 6 AM
recommended_timezone: America/Los_Angeles
```

### COST_TAG_COVERAGE

**Purpose:** Alert when untagged resource usage is high.

```yaml
template_id: COST_TAG_COVERAGE
domain: COST
default_severity: WARNING
default_threshold: 80.0

parameters:
  - name: min_coverage_pct
    type: DOUBLE
    description: Minimum tag coverage percentage
    default: 80.0

query_template: |
  WITH tagged_analysis AS (
    SELECT
      CASE
        WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
        ELSE 'TAGGED'
      END AS tag_status,
      SUM(list_cost) AS cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    GROUP BY CASE
      WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
      ELSE 'TAGGED'
    END
  )
  SELECT
    SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100 AS tag_coverage_pct,
    'Tag coverage ' || ROUND(SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100, 1)
      || '% is below threshold ({{min_coverage_pct}}%)' AS alert_message
  FROM tagged_analysis
  HAVING SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100 < {{min_coverage_pct}}

threshold_column: tag_coverage_pct
threshold_operator: "<"
recommended_schedule: "0 0 8 ? * MON"  # Weekly Monday 8 AM
recommended_timezone: America/Los_Angeles
```

### RELI_JOB_FAILURE_RATE

**Purpose:** Alert when job failure rate exceeds threshold.

```yaml
template_id: RELI_JOB_FAILURE_RATE
domain: RELIABILITY
default_severity: CRITICAL
default_threshold: 10.0

parameters:
  - name: failure_rate_pct
    type: DOUBLE
    description: Maximum acceptable failure rate percentage
    default: 10.0
  - name: lookback_hours
    type: INT
    description: Hours to look back
    default: 24

query_template: |
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
      ) || '% exceeds threshold ({{failure_rate_pct}}%)' as alert_message
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL {{lookback_hours}} HOURS
  HAVING SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) > {{failure_rate_pct}}

threshold_column: failure_rate
threshold_operator: ">"
recommended_schedule: "0 */30 * * * ?"  # Every 30 minutes
recommended_timezone: America/Los_Angeles
```

### SECU_FAILED_ACCESS

**Purpose:** Alert on high failed access attempts.

```yaml
template_id: SECU_FAILED_ACCESS
domain: SECURITY
default_severity: CRITICAL
default_threshold: 50.0

parameters:
  - name: max_failed_attempts
    type: DOUBLE
    description: Maximum allowed failed attempts
    default: 50.0
  - name: lookback_hours
    type: INT
    description: Hours to look back
    default: 1

query_template: |
  SELECT 
    COUNT(*) as failed_attempts,
    'CRITICAL: ' || COUNT(*) || ' failed access attempts in last {{lookback_hours}} hour(s)' as alert_message
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL {{lookback_hours}} HOURS
    AND response_status_code >= 400
  HAVING COUNT(*) > {{max_failed_attempts}}

threshold_column: failed_attempts
threshold_operator: ">"
recommended_schedule: "0 0 * * * ?"  # Hourly
recommended_timezone: America/Los_Angeles
```

### QUAL_DATA_FRESHNESS

**Purpose:** Alert when data is stale.

```yaml
template_id: QUAL_DATA_FRESHNESS
domain: QUALITY
default_severity: WARNING
default_threshold: 24.0

parameters:
  - name: max_age_hours
    type: DOUBLE
    description: Maximum acceptable data age in hours
    default: 24.0
  - name: table_name
    type: STRING
    description: Table to check
    default: fact_usage

query_template: |
  SELECT 
    TIMESTAMPDIFF(HOUR, MAX(processed_at), CURRENT_TIMESTAMP()) as hours_since_update,
    'Data in {{table_name}} is ' || TIMESTAMPDIFF(HOUR, MAX(processed_at), CURRENT_TIMESTAMP()) || 
      ' hours old (threshold: {{max_age_hours}} hours)' as alert_message
  FROM ${catalog}.${gold_schema}.{{table_name}}
  HAVING TIMESTAMPDIFF(HOUR, MAX(processed_at), CURRENT_TIMESTAMP()) > {{max_age_hours}}

threshold_column: hours_since_update
threshold_operator: ">"
recommended_schedule: "0 0 * * * ?"  # Hourly
recommended_timezone: America/Los_Angeles
```

---

## Using Templates

### Python API

```python
from alerting.alert_templates import (
    AlertTemplateLibrary,
    get_template,
    create_alert_from_template,
    list_templates
)

# List all available templates
templates = list_templates()
for t in templates:
    print(f"{t.template_id}: {t.name}")

# Get a specific template
template = get_template("COST_DAILY_SPIKE")
print(template.query_template)

# Create alert from template
alert_config = create_alert_from_template(
    template_id="COST_DAILY_SPIKE",
    alert_name="My Daily Cost Alert",
    params={
        "threshold_usd": 3000.0
    },
    catalog="my_catalog",
    gold_schema="gold",
    sequence_number=1,
    owner="finops@company.com",
    notification_channels=["finops@company.com"]
)

# Insert into config table
spark.sql(f"""
    INSERT INTO my_catalog.gold.alert_configurations 
    SELECT * FROM json_to_table('{alert_config.to_json()}')
""")
```

### SQL API (via Stored Procedure)

```sql
-- Future: SQL procedure for template instantiation
CALL create_alert_from_template(
    template_id => 'COST_DAILY_SPIKE',
    alert_name => 'My Daily Cost Alert',
    params => map('threshold_usd', '3000.0'),
    owner => 'finops@company.com',
    notification_channels => array('finops@company.com')
);
```

---

## Customizing Templates

### Override Threshold

```python
alert_config = create_alert_from_template(
    template_id="COST_DAILY_SPIKE",
    params={"threshold_usd": 10000.0},  # Override default $5000
    ...
)
```

### Override Schedule

```python
alert_config = create_alert_from_template(
    template_id="COST_DAILY_SPIKE",
    schedule_cron="0 0 8 * * ?",  # Override to 8 AM
    ...
)
```

### Override Severity

```python
alert_config = create_alert_from_template(
    template_id="COST_DAILY_SPIKE",
    severity="CRITICAL",  # Override from WARNING
    ...
)
```

### Add Custom Tags

```python
alert_config = create_alert_from_template(
    template_id="COST_DAILY_SPIKE",
    tags={
        "team": "finops",
        "project": "cost-monitoring",
        "environment": "production"
    },
    ...
)
```

---

## Creating Custom Templates

### Template Structure

```python
from alerting.alert_templates import AlertTemplate, TemplateParameter

my_template = AlertTemplate(
    template_id="CUSTOM_001",
    name="My Custom Alert",
    description="Description of what this alert does",
    domain="COST",
    default_severity="WARNING",
    
    parameters=[
        TemplateParameter(
            name="my_param",
            param_type="DOUBLE",
            description="Description of parameter",
            default_value=100.0,
            required=True
        )
    ],
    
    query_template="""
        SELECT 
            my_column as threshold_value,
            'Alert message' as alert_message
        FROM ${catalog}.${gold_schema}.my_table
        WHERE condition = true
        HAVING my_column > {{my_param}}
    """,
    
    threshold_column="threshold_value",
    threshold_operator=">",
    threshold_value_type="DOUBLE",
    
    recommended_schedule="0 0 6 * * ?",
    recommended_timezone="America/Los_Angeles"
)
```

### Register Custom Template

```python
from alerting.alert_templates import AlertTemplateLibrary

# Add to library
library = AlertTemplateLibrary()
library.register_template(my_template)

# Persist to Delta table (optional)
library.save_to_delta(spark, "my_catalog.gold.alert_templates")
```

---

## Template Validation

All templates are validated for:

1. **SQL Syntax** - Query must parse without errors
2. **Placeholder Consistency** - All `{{param}}` must be defined
3. **Threshold Column** - Must appear in SELECT clause
4. **Alert Message** - Recommended to include `alert_message` column
5. **Aggregation** - HAVING clause should limit results

### Validate Template

```python
from alerting.alert_templates import validate_template

result = validate_template(
    template=my_template,
    catalog="my_catalog",
    gold_schema="gold",
    spark=spark
)

if result.is_valid:
    print("Template is valid")
else:
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
```

---

## Best Practices

1. **Start with templates** - Modify rather than build from scratch
2. **Test threshold values** - Run queries manually before deploying
3. **Use appropriate severity** - CRITICAL for immediate action, WARNING for investigation
4. **Set reasonable schedules** - Don't over-alert (alert fatigue)
5. **Include actionable messages** - Tell users what to do
6. **Tag consistently** - Enable filtering and reporting

