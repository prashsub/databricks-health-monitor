# Alert Configuration Guide

**Version:** 2.0  
**Last Updated:** December 30, 2025

---

## Overview

This guide explains how to configure alerts in the alerting framework. All configuration is done via the `alert_configurations` Delta table.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Alert Configuration Fields](#alert-configuration-fields)
3. [Notification Destinations](#notification-destinations)
4. [Query Templates](#query-templates)
5. [Threshold Configuration](#threshold-configuration)
6. [Schedule Configuration](#schedule-configuration)
7. [Custom Templates](#custom-templates)
8. [Examples by Domain](#examples-by-domain)

---

## Quick Start

### Option 1: Use Pre-Built Templates

```python
from alerting.alert_templates import create_alert_from_template

alert = create_alert_from_template(
    template_id="COST_SPIKE",
    alert_name="Daily Cost Alert",
    params={"threshold_usd": 5000},
    catalog="my_catalog",
    gold_schema="gold",
    sequence_number=1,
    owner="finops@company.com"
)

# Insert into config table
spark.sql(f"""
INSERT INTO my_catalog.gold.alert_configurations VALUES (...)
""")
```

### Option 2: Direct SQL Insert

```sql
INSERT INTO catalog.gold.alert_configurations (
    alert_id, alert_name, alert_description, agent_domain, severity,
    alert_query_template, threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    schedule_cron, schedule_timezone, notification_channels,
    owner, created_by, is_enabled
) VALUES (
    'COST-001',
    'Daily Cost Spike',
    'Alerts when daily cost exceeds $5000',
    'COST',
    'WARNING',
    'SELECT SUM(list_cost) as daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 HAVING SUM(list_cost) > 5000',
    'daily_cost',
    '>',
    'DOUBLE',
    5000.0,
    '0 0 6 * * ?',
    'America/Los_Angeles',
    array('default_email'),
    'finops@company.com',
    'system',
    TRUE
);
```

---

## Alert Configuration Fields

### Identity Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `alert_id` | ✅ | Unique identifier | `COST-001`, `RELI-042` |
| `alert_name` | ✅ | Display name | `Daily Cost Spike` |
| `alert_description` | ❌ | Detailed description | `Alerts when daily cost exceeds budget` |

**Alert ID Convention:** `<DOMAIN>-<NUMBER>`
- COST-001, COST-002, ...
- SECU-001, SECU-002, ...
- PERF-001, PERF-002, ...
- RELI-001, RELI-002, ...
- QUAL-001, QUAL-002, ...

### Classification Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `agent_domain` | ✅ | COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY | Business domain |
| `severity` | ✅ | CRITICAL, WARNING, INFO | Alert urgency |

### Query Fields

| Field | Required | Description |
|-------|----------|-------------|
| `alert_query_template` | ✅ | SQL query with placeholders |
| `query_source` | ❌ | Source type: CUSTOM, TVF, METRIC_VIEW |
| `source_artifact_name` | ❌ | Reference to source artifact |

### Threshold Fields

| Field | Required | Description |
|-------|----------|-------------|
| `threshold_column` | ✅ | Column name to evaluate |
| `threshold_operator` | ✅ | Comparison: >, <, >=, <=, =, != |
| `threshold_value_type` | ✅ | Type: DOUBLE, STRING, BOOLEAN |
| `threshold_value_double` | * | Numeric threshold |
| `threshold_value_string` | * | String threshold |
| `threshold_value_bool` | * | Boolean threshold |

*Required based on `threshold_value_type`

### Evaluation Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `empty_result_state` | ✅ | OK | State when no results: OK, TRIGGERED, ERROR |
| `aggregation_type` | ❌ | NONE | Aggregation: SUM, COUNT, AVG, MIN, MAX, FIRST |

### Schedule Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `schedule_cron` | ✅ | - | Quartz cron expression |
| `schedule_timezone` | ✅ | America/Los_Angeles | IANA timezone |
| `pause_status` | ✅ | UNPAUSED | UNPAUSED or PAUSED |
| `is_enabled` | ✅ | TRUE | Whether to deploy |

### Notification Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `notification_channels` | ✅ | - | Array of channel IDs or emails |
| `notify_on_ok` | ✅ | FALSE | Notify when alert clears |
| `retrigger_seconds` | ❌ | NULL | Cooldown before re-notify |

### Custom Template Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `use_custom_template` | ✅ | FALSE | Use custom notifications |
| `custom_subject_template` | ❌ | NULL | Custom email subject |
| `custom_body_template` | ❌ | NULL | Custom notification body |

### Ownership Fields

| Field | Required | Description |
|-------|----------|-------------|
| `owner` | ✅ | Alert owner email |
| `created_by` | ✅ | Creator identifier |
| `tags` | ❌ | Map of key-value tags |

---

## Notification Destinations

### Direct Email (Simplest)

Include email addresses directly in `notification_channels`:

```sql
notification_channels = array('alice@company.com', 'bob@company.com')
```

### Named Destinations (Recommended for Teams)

1. **Create destination in `notification_destinations` table:**

```sql
INSERT INTO catalog.gold.notification_destinations (
    destination_id,
    destination_name,
    destination_type,
    databricks_destination_id,  -- Get from Databricks UI or sync job
    config_json,
    owner,
    is_enabled,
    created_by
) VALUES (
    'finops_team',
    'FinOps Team Alerts',
    'EMAIL',
    'uuid-from-databricks-workspace',  -- Or NULL to auto-create
    NULL,
    'finops@company.com',
    TRUE,
    'system'
);
```

2. **Reference in alerts:**

```sql
notification_channels = array('finops_team')
```

### Destination Types

| Type | Config Required | Description |
|------|-----------------|-------------|
| `EMAIL` | Email list | Email notification |
| `SLACK` | Webhook URL | Slack channel |
| `WEBHOOK` | URL + optional auth | Custom HTTP endpoint |
| `TEAMS` | Connector URL | Microsoft Teams |
| `PAGERDUTY` | Integration key | PagerDuty incidents |

### Slack Destination Example

```sql
INSERT INTO catalog.gold.notification_destinations VALUES (
    'alerts_slack',
    '#alerts-channel',
    'SLACK',
    NULL,  -- Will be created by sync job
    '{"url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"}',
    'platform@company.com',
    TRUE,
    'system',
    CURRENT_TIMESTAMP(),
    NULL, NULL,
    map('team', 'platform')
);
```

---

## Query Templates

### Placeholder Syntax

Use these placeholders in `alert_query_template`:

| Placeholder | Replaced With |
|-------------|---------------|
| `${catalog}` | Target catalog name |
| `${gold_schema}` | Target schema name |

### Query Requirements

1. **Must return the threshold column**
2. **Use HAVING to filter results** (only return rows when condition met)
3. **Include `alert_message` column** for notification content
4. **Use NULLIF for division** to prevent divide-by-zero

### Query Pattern: Threshold

```sql
SELECT 
    SUM(list_cost) as daily_cost,
    'Daily cost $' || ROUND(SUM(list_cost), 2) || ' exceeds threshold' as alert_message
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date = CURRENT_DATE() - 1
HAVING SUM(list_cost) > 5000
```

### Query Pattern: Percentage Change

```sql
WITH current_week AS (
    SELECT SUM(cost) as weekly_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= DATE_TRUNC('week', CURRENT_DATE())
),
previous_week AS (
    SELECT SUM(cost) as weekly_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= DATE_TRUNC('week', CURRENT_DATE() - INTERVAL 7 DAYS)
      AND usage_date < DATE_TRUNC('week', CURRENT_DATE())
)
SELECT 
    ROUND((c.weekly_cost - p.weekly_cost) / NULLIF(p.weekly_cost, 0) * 100, 1) as pct_change,
    'Weekly cost increased by ' || 
        ROUND((c.weekly_cost - p.weekly_cost) / NULLIF(p.weekly_cost, 0) * 100, 1) || 
        '%' as alert_message
FROM current_week c, previous_week p
WHERE c.weekly_cost > p.weekly_cost * 1.25  -- >25% increase
```

### Query Pattern: Count-Based

```sql
SELECT 
    COUNT(*) as failed_jobs,
    'CRITICAL: ' || COUNT(*) || ' jobs failed in last 24 hours' as alert_message
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
  AND result_state = 'FAILED'
HAVING COUNT(*) > 0
```

### Query Pattern: Info Summary (Always Triggers)

```sql
SELECT 
    SUM(booking_count) as total_bookings,
    SUM(total_booking_value) as total_revenue,
    1 as always_trigger,  -- Forces trigger for INFO alerts
    'Daily Summary: ' || SUM(booking_count) || ' bookings, $' || 
        ROUND(SUM(total_booking_value), 2) || ' revenue' as alert_message
FROM ${catalog}.${gold_schema}.fact_booking_daily
WHERE check_in_date = CURRENT_DATE() - 1
```

---

## Threshold Configuration

### Operators

| Operator | Description | Use Case |
|----------|-------------|----------|
| `>` | Greater than | Cost exceeds budget |
| `>=` | Greater than or equal | Rate at or above limit |
| `<` | Less than | Coverage drops below threshold |
| `<=` | Less than or equal | Count at or below minimum |
| `=` | Equals | Status matches specific value |
| `!=` | Not equals | Status changed from expected |

### Value Types

| Type | Use Case | Example |
|------|----------|---------|
| `DOUBLE` | Numeric thresholds | Cost > 5000.0 |
| `STRING` | String comparisons | Status = 'FAILED' |
| `BOOLEAN` | Boolean checks | is_valid = false |

### Aggregation Types

| Type | Description |
|------|-------------|
| `SUM` | Sum of values |
| `COUNT` | Count of rows |
| `COUNT_DISTINCT` | Count distinct values |
| `AVG` | Average value |
| `MEDIAN` | Median value |
| `MIN` | Minimum value |
| `MAX` | Maximum value |
| `STDDEV` | Standard deviation |
| `FIRST` | First value in results |

---

## Schedule Configuration

### Cron Expression Format (Quartz)

```
┌───────────── second (0-59)
│ ┌───────────── minute (0-59)
│ │ ┌───────────── hour (0-23)
│ │ │ ┌───────────── day of month (1-31)
│ │ │ │ ┌───────────── month (1-12)
│ │ │ │ │ ┌───────────── day of week (0-7, SUN-SAT)
│ │ │ │ │ │
* * * * * *
```

### Common Schedules

| Schedule | Cron Expression |
|----------|-----------------|
| Every 5 minutes | `0 */5 * * * ?` |
| Every 15 minutes | `0 */15 * * * ?` |
| Every hour | `0 0 * * * ?` |
| Daily at 6 AM | `0 0 6 * * ?` |
| Daily at 8 AM | `0 0 8 * * ?` |
| Weekdays at 9 AM | `0 0 9 ? * MON-FRI` |
| Monday at 9 AM | `0 0 9 ? * MON` |
| First of month | `0 0 0 1 * ?` |

### Timezones

Use IANA timezone identifiers:
- `America/Los_Angeles` (Pacific)
- `America/New_York` (Eastern)
- `America/Chicago` (Central)
- `America/Denver` (Mountain)
- `UTC`
- `Europe/London`
- `Asia/Tokyo`

---

## Custom Templates

### Supported Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{{ALERT_ID}}` | Alert ID from config |
| `{{ALERT_NAME}}` | Alert display name |
| `{{SEVERITY}}` | Alert severity |
| `{{QUERY_RESULT_VALUE}}` | Value returned by query |
| `{{THRESHOLD_VALUE}}` | Configured threshold |
| `{{OPERATOR}}` | Comparison operator |
| `{{TIMESTAMP}}` | Alert trigger time |
| `{{ALERT_MESSAGE}}` | Message from query |
| `{{DOMAIN}}` | Agent domain |
| `{{OWNER}}` | Alert owner |

### Example Custom Subject

```
[{{SEVERITY}}] {{ALERT_NAME}} - {{QUERY_RESULT_VALUE}} {{OPERATOR}} {{THRESHOLD_VALUE}}
```

### Example Custom Body

```html
<h2>Alert: {{ALERT_NAME}}</h2>
<p><strong>Severity:</strong> {{SEVERITY}}</p>
<p><strong>Domain:</strong> {{DOMAIN}}</p>
<p><strong>Message:</strong> {{ALERT_MESSAGE}}</p>
<p><strong>Value:</strong> {{QUERY_RESULT_VALUE}}</p>
<p><strong>Threshold:</strong> {{OPERATOR}} {{THRESHOLD_VALUE}}</p>
<p><strong>Time:</strong> {{TIMESTAMP}}</p>
<hr>
<p><em>Owner: {{OWNER}}</em></p>
```

---

## Examples by Domain

### COST Domain

```sql
-- COST-001: Daily cost spike
INSERT INTO alert_configurations (
    alert_id, alert_name, agent_domain, severity,
    alert_query_template, threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    schedule_cron, schedule_timezone, notification_channels,
    owner, created_by, is_enabled
) VALUES (
    'COST-001', 'Daily Cost Spike', 'COST', 'WARNING',
    'SELECT SUM(list_cost) as daily_cost, ''Cost spike: $'' || ROUND(SUM(list_cost),2) as alert_message FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 HAVING SUM(list_cost) > 5000',
    'daily_cost', '>', 'DOUBLE', 5000.0,
    '0 0 6 * * ?', 'America/Los_Angeles', array('finops@company.com'),
    'finops@company.com', 'system', TRUE
);
```

### RELIABILITY Domain

```sql
-- RELI-001: Job failure rate
INSERT INTO alert_configurations (
    alert_id, alert_name, agent_domain, severity,
    alert_query_template, threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    schedule_cron, schedule_timezone, notification_channels,
    owner, created_by, is_enabled
) VALUES (
    'RELI-001', 'Job Failure Rate', 'RELIABILITY', 'CRITICAL',
    'SELECT ROUND(SUM(CASE WHEN result_state=''FAILED'' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) as failure_rate, ''Failure rate: '' || ROUND(SUM(CASE WHEN result_state=''FAILED'' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) || ''%'' as alert_message FROM ${catalog}.${gold_schema}.fact_job_run_timeline WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS HAVING SUM(CASE WHEN result_state=''FAILED'' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0) > 10',
    'failure_rate', '>', 'DOUBLE', 10.0,
    '0 */30 * * * ?', 'America/Los_Angeles', array('oncall@company.com'),
    'platform@company.com', 'system', TRUE
);
```

### SECURITY Domain

```sql
-- SECU-001: Failed access attempts
INSERT INTO alert_configurations (
    alert_id, alert_name, agent_domain, severity,
    alert_query_template, threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    schedule_cron, schedule_timezone, notification_channels,
    owner, created_by, is_enabled
) VALUES (
    'SECU-001', 'Failed Access Attempts', 'SECURITY', 'CRITICAL',
    'SELECT COUNT(*) as failed_attempts, ''CRITICAL: '' || COUNT(*) || '' failed access attempts'' as alert_message FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_date >= CURRENT_DATE() - 1 AND response_status_code >= 400 HAVING COUNT(*) > 50',
    'failed_attempts', '>', 'DOUBLE', 50.0,
    '0 0 * * * ?', 'America/Los_Angeles', array('security@company.com'),
    'security@company.com', 'system', TRUE
);
```

---

## Best Practices

1. **Start with PAUSED status** - Set `pause_status: PAUSED` initially, enable after testing
2. **Use descriptive alert_ids** - Follow the naming convention: `DOMAIN-NNN`
3. **Include alert_message in queries** - Makes notifications actionable
4. **Set appropriate retrigger_seconds** - Prevents notification spam
5. **Use tags for organization** - Filter and query alerts by team/project
6. **Test queries in SQL editor first** - Validate before adding to config
7. **Use templates for common patterns** - Reduces errors and ensures consistency

