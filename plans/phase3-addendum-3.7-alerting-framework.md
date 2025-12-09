# Phase 3 Addendum 3.7: Alerting Framework for Databricks Health Monitor

## Overview

**Status:** 📋 Planned  
**Dependencies:** Gold Layer (Phase 2), TVFs (Phase 3.2), Metric Views (Phase 3.3), Lakehouse Monitoring (Phase 3.4)  
**Estimated Effort:** 2-3 weeks  
**Reference:** [Databricks SQL Alerts Documentation](https://docs.databricks.com/aws/en/sql/user/alerts/)

---

## Purpose

Create a centralized, config-driven alerting framework that:
- **Unified Alert Management** - All alerts defined in a central Delta table in Unity Catalog
- **Frontend Configurable** - Enable/disable/configure alerts from the UI
- **Agent-Domain Organized** - Alerts mapped to Cost, Security, Performance, Reliability, Quality agents
- **Multi-Channel Notifications** - Email, Slack, PagerDuty, webhooks
- **Self-Healing** - Integrate with ML models for intelligent alert suppression

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend Application                             │
│                  (Alert Configuration & Management UI)                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ REST API
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Alert Configuration Layer                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │         ${catalog}.${gold_schema}.alert_configurations          │   │
│  │                     (Central Delta Table)                        │   │
│  │                                                                   │   │
│  │  • Alert definitions (query, thresholds, schedule)              │   │
│  │  • Agent domain mapping                                          │   │
│  │  • Notification channels                                         │   │
│  │  • Enable/disable flags                                          │   │
│  │  • Custom templates                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Alert Execution Engine                              │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Databricks SQL  │  │ Databricks Jobs │  │ Lakehouse       │         │
│  │ Alerts (Native) │  │ (Workflow)      │  │ Monitoring      │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│              ↓                    ↓                    ↓                 │
│         Real-time           Scheduled           Drift-based             │
│         Threshold            Batch               Anomaly                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Notification Hub                                    │
│                                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │  Email  │  │  Slack  │  │PagerDuty│  │ Webhook │  │  Teams  │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Alert History & Analytics                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │            ${catalog}.${gold_schema}.alert_history               │   │
│  │                                                                   │   │
│  │  • Evaluation results                                            │   │
│  │  • Trigger timestamps                                            │   │
│  │  • Resolution times                                              │   │
│  │  • False positive tracking                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Alert Configuration Schema

### Table: `alert_configurations`

**Purpose:** Central configuration table for all alerts, stored in Unity Catalog

```sql
CREATE TABLE IF NOT EXISTS ${catalog}.${gold_schema}.alert_configurations (
    -- Primary Key
    alert_id STRING NOT NULL 
        COMMENT 'Unique alert identifier (UUID). Business: Used to track and manage alerts. Technical: Primary key, auto-generated on creation.',
    
    -- Alert Identity
    alert_name STRING NOT NULL 
        COMMENT 'Human-readable alert name. Business: Displayed in notifications and UI. Technical: Must be unique within agent domain.',
    alert_description STRING 
        COMMENT 'Detailed description of what this alert monitors. Business: Helps users understand alert purpose. Technical: Shown in notification body.',
    
    -- Agent Domain Classification
    agent_domain STRING NOT NULL 
        COMMENT 'Agent domain: COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY. Business: Routes alerts to appropriate agent. Technical: Used for filtering and dashboard grouping.',
    severity STRING NOT NULL DEFAULT 'WARNING' 
        COMMENT 'Alert severity: CRITICAL, WARNING, INFO. Business: Determines notification urgency. Technical: Used for priority routing.',
    
    -- Alert Query Configuration
    alert_query STRING NOT NULL 
        COMMENT 'SQL query that returns the value to check. Business: The metric being monitored. Technical: Must return single numeric value for threshold comparison.',
    query_source STRING DEFAULT 'CUSTOM' 
        COMMENT 'Query source: CUSTOM, TVF, METRIC_VIEW, MONITORING. Business: Indicates where query logic comes from. Technical: Used for maintenance tracking.',
    source_artifact_name STRING 
        COMMENT 'Name of TVF, Metric View, or Monitor if not custom. Business: Links alert to existing artifact. Technical: Used for dependency tracking.',
    
    -- Threshold Configuration
    threshold_column STRING NOT NULL 
        COMMENT 'Column name in query result to check. Business: The specific value being compared. Technical: Must exist in query result.',
    threshold_operator STRING NOT NULL 
        COMMENT 'Comparison operator: >, <, >=, <=, ==, !=. Business: How to compare against threshold. Technical: Standard SQL operators.',
    threshold_value DOUBLE NOT NULL 
        COMMENT 'Static threshold value to compare against. Business: The boundary that triggers alert. Technical: Numeric value for comparison.',
    threshold_type STRING DEFAULT 'STATIC' 
        COMMENT 'Threshold type: STATIC, BASELINE_PERCENT, ROLLING_AVG. Business: How threshold is calculated. Technical: STATIC = fixed, BASELINE_PERCENT = % deviation from baseline.',
    baseline_window_days INT DEFAULT 7 
        COMMENT 'Days of history for baseline calculation. Business: How much history to use for dynamic thresholds. Technical: Only used when threshold_type != STATIC.',
    
    -- Aggregation (for Databricks SQL Alerts)
    aggregation_type STRING DEFAULT 'NONE' 
        COMMENT 'Aggregation: NONE, SUM, AVG, MIN, MAX, COUNT. Business: How to aggregate multi-row results. Technical: Applied before threshold comparison.',
    
    -- Schedule Configuration
    schedule_cron STRING NOT NULL DEFAULT '0 */5 * * * ?' 
        COMMENT 'Quartz cron expression for alert schedule. Business: How often alert runs. Technical: Default = every 5 minutes.',
    schedule_timezone STRING DEFAULT 'America/New_York' 
        COMMENT 'Timezone for schedule interpretation. Business: Ensures alerts run at expected times. Technical: IANA timezone name.',
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE 
        COMMENT 'Whether alert is active. Business: Toggle to enable/disable without deleting. Technical: FALSE = alert will not run.',
    
    -- Notification Configuration
    notification_channels ARRAY<STRING> NOT NULL 
        COMMENT 'List of notification channel IDs. Business: Where to send alerts. Technical: References notification_destinations table.',
    notify_on_ok BOOLEAN DEFAULT FALSE 
        COMMENT 'Send notification when alert resolves to OK. Business: Useful for tracking resolution. Technical: Additional notification on state change to OK.',
    notification_frequency_minutes INT DEFAULT 60 
        COMMENT 'Re-notify frequency if alert stays triggered. Business: Prevent alert fatigue vs ensuring visibility. Technical: 0 = only once until OK.',
    
    -- Custom Template
    use_custom_template BOOLEAN DEFAULT FALSE 
        COMMENT 'Whether to use custom notification template. Business: Customize alert message content. Technical: If FALSE, use default template.',
    custom_subject_template STRING 
        COMMENT 'Custom subject template with variables. Business: Customized notification subject. Technical: Supports {{ALERT_STATUS}}, {{ALERT_NAME}}, etc.',
    custom_body_template STRING 
        COMMENT 'Custom body template with variables. Business: Customized notification content. Technical: Supports HTML for email destinations.',
    
    -- Empty Result Handling
    empty_result_state STRING DEFAULT 'OK' 
        COMMENT 'State when query returns no results: OK, TRIGGERED, ERROR. Business: Define behavior for missing data. Technical: Default = OK (no alert).',
    
    -- ML Integration
    ml_model_enabled BOOLEAN DEFAULT FALSE 
        COMMENT 'Use ML model for intelligent suppression. Business: Reduce false positives. Technical: Uses prediction from ML inference table.',
    ml_model_name STRING 
        COMMENT 'Name of ML model for anomaly scoring. Business: Which model to consult. Technical: Must exist in Unity Catalog Model Registry.',
    ml_threshold DOUBLE DEFAULT 0.8 
        COMMENT 'ML confidence threshold to suppress alert. Business: If ML says not anomaly with >80% confidence, suppress. Technical: Range 0-1.',
    
    -- Ownership & Audit
    owner STRING NOT NULL 
        COMMENT 'Alert owner (user or group). Business: Who is responsible for this alert. Technical: Used for access control.',
    created_by STRING NOT NULL 
        COMMENT 'User who created the alert. Business: Audit trail. Technical: Set automatically on creation.',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() 
        COMMENT 'When alert was created. Business: Audit trail. Technical: Immutable after creation.',
    updated_by STRING 
        COMMENT 'User who last updated the alert. Business: Audit trail. Technical: Set automatically on update.',
    updated_at TIMESTAMP 
        COMMENT 'When alert was last updated. Business: Audit trail. Technical: Set automatically on update.',
    
    -- Tags for Organization
    tags MAP<STRING, STRING> 
        COMMENT 'Key-value tags for organization. Business: Custom metadata for filtering. Technical: Queryable for alert discovery.',
    
    -- Constraints
    CONSTRAINT pk_alert_configurations PRIMARY KEY (alert_id) NOT ENFORCED,
    CONSTRAINT chk_agent_domain CHECK (agent_domain IN ('COST', 'SECURITY', 'PERFORMANCE', 'RELIABILITY', 'QUALITY')),
    CONSTRAINT chk_severity CHECK (severity IN ('CRITICAL', 'WARNING', 'INFO')),
    CONSTRAINT chk_operator CHECK (threshold_operator IN ('>', '<', '>=', '<=', '==', '!=')),
    CONSTRAINT chk_threshold_type CHECK (threshold_type IN ('STATIC', 'BASELINE_PERCENT', 'ROLLING_AVG')),
    CONSTRAINT chk_aggregation CHECK (aggregation_type IN ('NONE', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT')),
    CONSTRAINT chk_empty_result CHECK (empty_result_state IN ('OK', 'TRIGGERED', 'ERROR'))
)
USING DELTA
CLUSTER BY AUTO
COMMENT 'Central alert configuration table for Databricks Health Monitor. All alerts are defined here and synced to Databricks SQL Alerts or Job-based alerting. Enables config-driven alert management from frontend.'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'layer' = 'gold',
    'domain' = 'alerting',
    'entity_type' = 'configuration'
);
```

### Table: `alert_history`

**Purpose:** Track all alert evaluations, triggers, and resolutions

```sql
CREATE TABLE IF NOT EXISTS ${catalog}.${gold_schema}.alert_history (
    -- Primary Key
    evaluation_id STRING NOT NULL 
        COMMENT 'Unique evaluation identifier (UUID). Technical: Primary key for this table.',
    
    -- Alert Reference
    alert_id STRING NOT NULL 
        COMMENT 'Reference to alert_configurations.alert_id. Technical: Foreign key.',
    alert_name STRING NOT NULL 
        COMMENT 'Alert name at time of evaluation (denormalized). Technical: For historical accuracy.',
    
    -- Evaluation Details
    evaluation_timestamp TIMESTAMP NOT NULL 
        COMMENT 'When the alert was evaluated. Technical: Event time.',
    evaluation_status STRING NOT NULL 
        COMMENT 'Result: OK, TRIGGERED, ERROR. Technical: Post-evaluation state.',
    previous_status STRING 
        COMMENT 'Status before this evaluation. Technical: For state change detection.',
    
    -- Query Results
    query_result_value DOUBLE 
        COMMENT 'The value returned by the alert query. Technical: NULL if ERROR.',
    threshold_value DOUBLE NOT NULL 
        COMMENT 'The threshold that was compared against. Technical: Snapshot at evaluation time.',
    threshold_operator STRING NOT NULL 
        COMMENT 'The operator used for comparison. Technical: Snapshot at evaluation time.',
    
    -- Timing Metrics
    query_duration_ms BIGINT 
        COMMENT 'How long the query took to execute. Technical: For performance monitoring.',
    
    -- ML Integration Results
    ml_score DOUBLE 
        COMMENT 'ML model anomaly score (if enabled). Technical: 0-1, higher = more anomalous.',
    ml_suppressed BOOLEAN DEFAULT FALSE 
        COMMENT 'Whether ML suppressed this alert. Technical: TRUE if triggered but ML said not anomaly.',
    
    -- Notification Tracking
    notification_sent BOOLEAN DEFAULT FALSE 
        COMMENT 'Whether notification was dispatched. Technical: FALSE if suppressed or already notified.',
    notification_channels_used ARRAY<STRING> 
        COMMENT 'Channels that received notification. Technical: For audit trail.',
    
    -- Error Details
    error_message STRING 
        COMMENT 'Error details if evaluation_status = ERROR. Technical: For debugging.',
    
    -- Metadata
    agent_domain STRING NOT NULL 
        COMMENT 'Agent domain at evaluation time. Technical: Denormalized for analytics.',
    
    CONSTRAINT pk_alert_history PRIMARY KEY (evaluation_id) NOT ENFORCED,
    CONSTRAINT fk_alert_history_alert FOREIGN KEY (alert_id) 
        REFERENCES alert_configurations(alert_id) NOT ENFORCED
)
USING DELTA
CLUSTER BY AUTO
PARTITIONED BY (DATE(evaluation_timestamp))
COMMENT 'Historical record of all alert evaluations. Used for alert analytics, false positive analysis, and audit compliance.'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'layer' = 'gold',
    'domain' = 'alerting',
    'entity_type' = 'fact'
);
```

### Table: `notification_destinations`

**Purpose:** Configure notification channels

```sql
CREATE TABLE IF NOT EXISTS ${catalog}.${gold_schema}.notification_destinations (
    destination_id STRING NOT NULL COMMENT 'Unique destination identifier',
    destination_name STRING NOT NULL COMMENT 'Human-readable name',
    destination_type STRING NOT NULL COMMENT 'Type: EMAIL, SLACK, PAGERDUTY, WEBHOOK, TEAMS',
    
    -- Type-specific configuration (stored as JSON)
    config_json STRING NOT NULL COMMENT 'JSON configuration for the destination type',
    
    -- Ownership
    owner STRING NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP,
    
    CONSTRAINT pk_notification_destinations PRIMARY KEY (destination_id) NOT ENFORCED
)
USING DELTA
CLUSTER BY AUTO
COMMENT 'Notification destination configurations for alert delivery.';
```

---

## Pre-Configured Alerts by Agent Domain

### 💰 Cost Agent Alerts (14 Alerts)

| Alert ID | Alert Name | Query Source | Threshold | Schedule | Severity |
|----------|------------|--------------|-----------|----------|----------|
| COST-001 | Daily Cost Spike | fact_usage | > 150% of 7-day avg | Every 4 hours | WARNING |
| COST-002 | Weekly Cost Growth | cost_analytics_metrics | > 30% WoW growth | Daily 8 AM | WARNING |
| COST-003 | Budget Threshold | fact_usage | > 80% of monthly budget | Daily 6 AM | CRITICAL |
| COST-004 | Budget Exceeded | fact_usage | > 100% of monthly budget | Every hour | CRITICAL |
| COST-005 | Untagged Cost Spike | fact_usage | > $1000 untagged | Daily | INFO |
| COST-006 | Job Cost Anomaly | ML: cost_anomaly_detector | anomaly_score > 0.9 | Every 15 min | WARNING |
| COST-007 | Runaway Job | fact_usage | Single job > $500/day | Every hour | CRITICAL |
| COST-008 | Cost Allocation Drift | fact_usage | Team cost > 120% of budget | Weekly | WARNING |
| **COST-009** | **Commit Undershoot Risk** | commit_configurations | Projected < 95% of commit | Daily 8 AM | **WARNING** |
| **COST-010** | **Commit Overshoot Risk** | commit_configurations | Projected > 105% of commit | Daily 8 AM | **WARNING** |
| **COST-011** | **Commit Variance Critical** | commit_configurations | Projected < 85% OR > 115% | Daily 8 AM | **CRITICAL** |
| **COST-012** | **Tag Coverage Drop** | fact_usage | Tag coverage < 80% | Daily | **WARNING** |
| **COST-013** | **Untagged High-Cost Job** | fact_usage | Untagged job > $100/day | Daily | **WARNING** |
| **COST-014** | **New Untagged Resources** | dim_job, dim_cluster | New resources without tags | Daily | **INFO** |

#### Alert Definition: COST-001 (Daily Cost Spike)

```sql
-- Alert Query for COST-001
SELECT 
    SUM(usage_quantity * list_price) AS current_cost,
    AVG(baseline.daily_cost) AS baseline_cost,
    (SUM(usage_quantity * list_price) / NULLIF(AVG(baseline.daily_cost), 0) - 1) * 100 AS deviation_pct
FROM ${catalog}.${gold_schema}.fact_usage current
CROSS JOIN (
    SELECT SUM(usage_quantity * list_price) / 7 AS daily_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date BETWEEN CURRENT_DATE() - INTERVAL 8 DAYS AND CURRENT_DATE() - INTERVAL 1 DAY
) baseline
WHERE current.usage_date = CURRENT_DATE()
HAVING deviation_pct > 50  -- 50% above baseline triggers alert
```

#### Alert Definition: COST-009/010/011 (Commit Tracking Alerts)

These alerts help proactively manage Databricks commit amounts by tracking actual vs required run rate.

```sql
-- Alert Query for COST-009: Commit Undershoot Risk
-- Alert Query for COST-010: Commit Overshoot Risk  
-- Alert Query for COST-011: Commit Variance Critical
WITH commit_config AS (
    SELECT 
        annual_commit_amount,
        undershoot_alert_pct,
        overshoot_alert_pct
    FROM ${catalog}.${gold_schema}.commit_configurations
    WHERE commit_year = YEAR(CURRENT_DATE())
),
monthly_spend AS (
    SELECT SUM(usage_quantity * list_price) AS monthly_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())
    GROUP BY DATE_TRUNC('month', usage_date)
),
projection AS (
    SELECT 
        AVG(monthly_cost) * 12 AS projected_annual,
        cc.annual_commit_amount,
        cc.undershoot_alert_pct,
        cc.overshoot_alert_pct
    FROM monthly_spend
    CROSS JOIN commit_config cc
)
SELECT 
    projected_annual,
    annual_commit_amount,
    projected_annual / NULLIF(annual_commit_amount, 0) * 100 AS pct_of_commit,
    CASE 
        WHEN projected_annual < annual_commit_amount * undershoot_alert_pct THEN 'UNDERSHOOT_RISK'
        WHEN projected_annual > annual_commit_amount * overshoot_alert_pct THEN 'OVERSHOOT_RISK'
        ELSE 'ON_TRACK'
    END AS commit_status,
    -- For threshold comparison
    ABS(projected_annual / NULLIF(annual_commit_amount, 0) - 1) * 100 AS variance_pct
FROM projection
```

**Alert Thresholds:**
- **COST-009 (Undershoot):** `commit_status = 'UNDERSHOOT_RISK'`
- **COST-010 (Overshoot):** `commit_status = 'OVERSHOOT_RISK'`
- **COST-011 (Critical):** `variance_pct > 15`

#### Alert Definition: COST-012/013/014 (Tag Hygiene Alerts)

These alerts ensure proper tagging for cost attribution per [billing table custom_tags](https://docs.databricks.com/aws/en/admin/system-tables/billing).

```sql
-- Alert Query for COST-012: Tag Coverage Drop
-- Triggers when less than 80% of cost is properly tagged
WITH tagged_analysis AS (
    SELECT 
        CASE 
            WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
            ELSE 'TAGGED'
        END AS tag_status,
        SUM(usage_quantity * list_price) AS cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    GROUP BY CASE 
        WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
        ELSE 'TAGGED'
    END
)
SELECT 
    SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100 AS tag_coverage_pct
FROM tagged_analysis
-- Alert triggers when tag_coverage_pct < 80
```

```sql
-- Alert Query for COST-013: Untagged High-Cost Job
-- Identifies jobs spending > $100/day without tags
SELECT 
    j.job_id,
    j.name AS job_name,
    w.workspace_name,
    SUM(f.usage_quantity * f.list_price) AS daily_cost
FROM ${catalog}.${gold_schema}.fact_usage f
INNER JOIN ${catalog}.${gold_schema}.dim_job j 
    ON f.usage_metadata.job_id = j.job_id AND j.is_current = TRUE
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
    ON j.workspace_id = w.workspace_id AND w.is_current = TRUE
WHERE f.usage_date = CURRENT_DATE() - INTERVAL 1 DAY
    AND (f.custom_tags IS NULL OR cardinality(f.custom_tags) = 0)
    AND f.usage_metadata.job_id IS NOT NULL
GROUP BY j.job_id, j.name, w.workspace_name
HAVING SUM(f.usage_quantity * f.list_price) > 100  -- $100 threshold
ORDER BY daily_cost DESC
```

```sql
-- Alert Query for COST-014: New Untagged Resources
-- Identifies resources created in last 24 hours without tags
SELECT 
    'JOB' AS resource_type,
    job_id AS resource_id,
    name AS resource_name,
    workspace_id,
    create_time
FROM ${catalog}.${gold_schema}.dim_job
WHERE is_current = TRUE
    AND create_time >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY
    AND (tags IS NULL OR cardinality(tags) = 0)
UNION ALL
SELECT 
    'CLUSTER' AS resource_type,
    cluster_id AS resource_id,
    cluster_name AS resource_name,
    workspace_id,
    create_time
FROM ${catalog}.${gold_schema}.dim_cluster
WHERE is_current = TRUE
    AND create_time >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY
    AND (custom_tags IS NULL OR cardinality(custom_tags) = 0)
```

---

### 🔒 Security Agent Alerts (6 Alerts)

| Alert ID | Alert Name | Query Source | Threshold | Schedule | Severity |
|----------|------------|--------------|-----------|----------|----------|
| SEC-001 | Sensitive Data Access Spike | fact_table_lineage | > 200% of daily avg | Every 15 min | CRITICAL |
| SEC-002 | Off-Hours Access | fact_table_lineage | Any sensitive table access 10PM-6AM | Real-time | WARNING |
| SEC-003 | Unusual Data Export | fact_query_history | > 10GB read by single user/hour | Every 15 min | CRITICAL |
| SEC-004 | Permission Escalation | fact_audit_events | Any GRANT with ADMIN | Real-time | CRITICAL |
| SEC-005 | New IP Access | fact_audit_events | Login from unknown IP | Real-time | WARNING |
| SEC-006 | Failed Login Spike | fact_audit_events | > 5 failed logins in 10 min | Every 5 min | WARNING |

#### Alert Definition: SEC-001 (Sensitive Data Access Spike)

```sql
-- Alert Query for SEC-001
WITH today_access AS (
    SELECT COUNT(*) AS access_count
    FROM ${catalog}.${gold_schema}.fact_table_lineage
    WHERE event_date = CURRENT_DATE()
      AND (source_table_full_name LIKE '%pii%' 
           OR source_table_full_name LIKE '%sensitive%'
           OR target_table_full_name LIKE '%pii%')
),
baseline AS (
    SELECT AVG(daily_count) AS avg_access
    FROM (
        SELECT DATE(event_time) AS event_date, COUNT(*) AS daily_count
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date BETWEEN CURRENT_DATE() - INTERVAL 8 DAYS AND CURRENT_DATE() - INTERVAL 1 DAY
          AND (source_table_full_name LIKE '%pii%' 
               OR source_table_full_name LIKE '%sensitive%'
               OR target_table_full_name LIKE '%pii%')
        GROUP BY DATE(event_time)
    )
)
SELECT 
    today_access.access_count,
    baseline.avg_access,
    (today_access.access_count / NULLIF(baseline.avg_access, 0)) * 100 AS pct_of_baseline
FROM today_access CROSS JOIN baseline
```

---

### ⚡ Performance Agent Alerts (8 Alerts)

| Alert ID | Alert Name | Query Source | Threshold | Schedule | Severity |
|----------|------------|--------------|-----------|----------|----------|
| PERF-001 | Query P95 Degradation | fact_query_history | P95 > 2x baseline | Every 15 min | WARNING |
| PERF-002 | High Queue Time | fact_query_history | Avg queue > 30 sec | Every 5 min | WARNING |
| PERF-003 | Warehouse Saturation | fact_query_history | Queue rate > 20% | Every 5 min | WARNING |
| PERF-004 | Slow Query Spike | fact_query_history | > 10 queries > 5 min | Every 15 min | INFO |
| PERF-005 | High Spill Rate | fact_query_history | > 10% queries spilling | Every hour | INFO |
| PERF-006 | Cluster Underutilization | fact_node_timeline | Avg CPU < 20% for 2 hours | Every 2 hours | INFO |
| PERF-007 | Cluster Overutilization | fact_node_timeline | Avg CPU > 90% for 1 hour | Every 30 min | WARNING |
| PERF-008 | Legacy DBR Usage | fact_job_run_timeline | Jobs on DBR < 13.x | Daily | INFO |

#### Alert Definition: PERF-001 (Query P95 Degradation)

```sql
-- Alert Query for PERF-001 (inspired by DBSQL Warehouse Advisor patterns)
WITH current_p95 AS (
    SELECT PERCENTILE(total_duration_ms / 1000, 0.95) AS p95_sec
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
),
baseline_p95 AS (
    SELECT PERCENTILE(total_duration_ms / 1000, 0.95) AS p95_sec
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE start_time BETWEEN CURRENT_TIMESTAMP() - INTERVAL 8 DAYS AND CURRENT_TIMESTAMP() - INTERVAL 1 DAY
)
SELECT 
    current_p95.p95_sec AS current_p95,
    baseline_p95.p95_sec AS baseline_p95,
    current_p95.p95_sec / NULLIF(baseline_p95.p95_sec, 0) AS degradation_ratio
FROM current_p95 CROSS JOIN baseline_p95
```

---

### 🔄 Reliability Agent Alerts (8 Alerts)

| Alert ID | Alert Name | Query Source | Threshold | Schedule | Severity |
|----------|------------|--------------|-----------|----------|----------|
| REL-001 | Job Success Rate Drop | fact_job_run_timeline | < 90% success rate | Every 15 min | CRITICAL |
| REL-002 | Critical Job Failed | fact_job_run_timeline | Tagged critical job fails | Real-time | CRITICAL |
| REL-003 | Consecutive Failures | fact_job_run_timeline | > 3 consecutive failures | Every 5 min | CRITICAL |
| REL-004 | Job Duration Anomaly | fact_job_run_timeline | > 2x historical P95 | Every 15 min | WARNING |
| REL-005 | SLA Breach Imminent | ML: sla_breach_predictor | Breach probability > 80% | Every 5 min | CRITICAL |
| REL-006 | High Retry Rate | fact_job_run_timeline | Retry rate > 20% | Every hour | WARNING |
| REL-007 | Timeout Rate Spike | fact_job_run_timeline | Timeout rate > 5% | Every 30 min | WARNING |
| REL-008 | Pipeline Failure | fact_job_run_timeline | DLT pipeline fails | Real-time | CRITICAL |

#### Alert Definition: REL-001 (Job Success Rate Drop)

```sql
-- Alert Query for REL-001
SELECT 
    COUNT(*) AS total_runs,
    SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS successful_runs,
    SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
  AND result_state IS NOT NULL
```

---

### ✅ Quality Agent Alerts (5 Alerts)

| Alert ID | Alert Name | Query Source | Threshold | Schedule | Severity |
|----------|------------|--------------|-----------|----------|----------|
| QUAL-001 | Quality Score Drop | fact_data_quality_monitoring | Score < 0.9 | Every hour | WARNING |
| QUAL-002 | Critical DQ Violation | fact_data_quality_monitoring | Any critical violation | Every 15 min | CRITICAL |
| QUAL-003 | Data Freshness SLA | fact_table_lineage | Table not updated in SLA | Every 15 min | WARNING |
| QUAL-004 | Schema Drift Detected | ML: schema_drift_detector | Breaking change detected | On schema change | CRITICAL |
| QUAL-005 | Null Rate Spike | Lakehouse Monitoring | Null rate > 10% | Every hour | WARNING |

---

## Alert Sync Engine

### Databricks SQL Alert Sync

The Alert Sync Engine reads from `alert_configurations` and creates/updates native Databricks SQL Alerts.

```python
# src/alerting/sync_alerts.py
"""
Alert Sync Engine - Syncs alert_configurations to Databricks SQL Alerts

This script reads from the central alert_configurations Delta table and 
creates/updates corresponding Databricks SQL Alerts via the API.
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    CreateAlertRequest,
    AlertCondition,
    AlertConditionOperand,
    AlertOperandColumn,
    AlertConditionOperator,
    AlertState
)
from pyspark.sql import SparkSession


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    return catalog, gold_schema


def load_alert_configs(spark: SparkSession, catalog: str, gold_schema: str):
    """Load enabled alert configurations from Delta table."""
    return spark.sql(f"""
        SELECT *
        FROM {catalog}.{gold_schema}.alert_configurations
        WHERE is_enabled = TRUE
        ORDER BY agent_domain, severity DESC
    """).collect()


def map_operator(operator_str: str) -> AlertConditionOperator:
    """Map string operator to SDK enum."""
    mapping = {
        '>': AlertConditionOperator.GREATER_THAN,
        '<': AlertConditionOperator.LESS_THAN,
        '>=': AlertConditionOperator.GREATER_THAN_OR_EQUAL,
        '<=': AlertConditionOperator.LESS_THAN_OR_EQUAL,
        '==': AlertConditionOperator.EQUAL,
        '!=': AlertConditionOperator.NOT_EQUAL
    }
    return mapping.get(operator_str, AlertConditionOperator.GREATER_THAN)


def create_or_update_alert(
    workspace_client: WorkspaceClient,
    alert_config: dict,
    existing_alerts: dict
):
    """Create or update a Databricks SQL Alert from configuration."""
    
    alert_name = alert_config['alert_name']
    
    # Build alert condition
    condition = AlertCondition(
        operand=AlertConditionOperand(
            column=AlertOperandColumn(name=alert_config['threshold_column'])
        ),
        op=map_operator(alert_config['threshold_operator']),
        threshold=AlertConditionOperand(
            column=AlertOperandColumn(name="threshold_value")
        )
    )
    
    if alert_name in existing_alerts:
        # Update existing alert
        print(f"  Updating alert: {alert_name}")
        # Update logic here
    else:
        # Create new alert
        print(f"  Creating alert: {alert_name}")
        # Create logic here
    
    return True


def sync_alerts(spark: SparkSession, catalog: str, gold_schema: str):
    """Main sync function."""
    
    workspace_client = WorkspaceClient()
    
    # Load configurations
    alert_configs = load_alert_configs(spark, catalog, gold_schema)
    print(f"Loaded {len(alert_configs)} alert configurations")
    
    # Get existing alerts for comparison
    existing_alerts = {}  # Load from Databricks SQL Alerts API
    
    # Sync each alert
    synced = 0
    for config in alert_configs:
        try:
            create_or_update_alert(workspace_client, config, existing_alerts)
            synced += 1
        except Exception as e:
            print(f"  ❌ Failed to sync {config['alert_name']}: {e}")
    
    print(f"\n✓ Synced {synced}/{len(alert_configs)} alerts")


def main():
    catalog, gold_schema = get_parameters()
    spark = SparkSession.getActiveSession()
    
    print("=" * 80)
    print("ALERT SYNC ENGINE")
    print("=" * 80)
    
    sync_alerts(spark, catalog, gold_schema)
    
    print("\n✅ Alert sync completed!")


if __name__ == "__main__":
    main()
```

---

## Frontend API Endpoints

### Alert Configuration CRUD

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/alerts` | GET | List all alerts with filtering by domain, severity, status |
| `/api/alerts/{id}` | GET | Get single alert configuration |
| `/api/alerts` | POST | Create new alert configuration |
| `/api/alerts/{id}` | PUT | Update alert configuration |
| `/api/alerts/{id}` | DELETE | Delete alert configuration |
| `/api/alerts/{id}/enable` | POST | Enable alert |
| `/api/alerts/{id}/disable` | POST | Disable alert |
| `/api/alerts/{id}/test` | POST | Test alert query without triggering notification |

### Alert History & Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/alerts/history` | GET | Get alert evaluation history |
| `/api/alerts/{id}/history` | GET | Get history for specific alert |
| `/api/alerts/analytics/by-domain` | GET | Alert counts by agent domain |
| `/api/alerts/analytics/false-positives` | GET | False positive analysis |
| `/api/alerts/analytics/mttr` | GET | Mean time to resolution |

### Notification Destinations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications/destinations` | GET | List notification destinations |
| `/api/notifications/destinations` | POST | Create notification destination |
| `/api/notifications/destinations/{id}` | PUT | Update notification destination |
| `/api/notifications/destinations/{id}/test` | POST | Test notification delivery |

---

## Custom Alert Template Variables

The following variables are available in custom alert templates (per [Databricks SQL Alerts](https://docs.databricks.com/aws/en/sql/user/alerts/)):

| Variable | Description | Type |
|----------|-------------|------|
| `{{ALERT_STATUS}}` | Evaluated status (OK, TRIGGERED, ERROR) | string |
| `{{ALERT_NAME}}` | Alert name | string |
| `{{ALERT_CONDITION}}` | Condition operator | string |
| `{{ALERT_THRESHOLD}}` | Threshold value | number |
| `{{ALERT_COLUMN}}` | Column being checked | string |
| `{{ALERT_URL}}` | Link to alert page | string |
| `{{QUERY_NAME}}` | Associated query name | string |
| `{{QUERY_URL}}` | Link to query | string |
| `{{QUERY_RESULT_VALUE}}` | Query result value | number |
| `{{QUERY_RESULT_TABLE}}` | HTML table of results (email only) | HTML |
| `{{QUERY_RESULT_ROWS}}` | Result rows array | array |
| `{{QUERY_RESULT_COLS}}` | Result column names | array |

### Custom Template Example

```html
<h2>🚨 {{ALERT_NAME}} - {{ALERT_STATUS}}</h2>

<p><strong>Agent Domain:</strong> {{AGENT_DOMAIN}}</p>
<p><strong>Severity:</strong> {{SEVERITY}}</p>

<h3>Alert Details</h3>
<p>The value <strong>{{QUERY_RESULT_VALUE}}</strong> is {{ALERT_CONDITION}} the threshold of <strong>{{ALERT_THRESHOLD}}</strong>.</p>

<h3>Query Results</h3>
{{QUERY_RESULT_TABLE}}

<h3>Actions</h3>
<ul>
    <li><a href="{{ALERT_URL}}">View Alert Configuration</a></li>
    <li><a href="{{QUERY_URL}}">View Query</a></li>
</ul>

<p><em>This alert is managed by Databricks Health Monitor.</em></p>
```

---

## Asset Bundle Configuration

```yaml
# resources/alerting/alerting_jobs.yml
resources:
  jobs:
    alert_sync_job:
      name: "[${bundle.target}] Health Monitor - Alert Sync"
      description: "Syncs alert configurations from Delta table to Databricks SQL Alerts"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - databricks-sdk>=0.20.0
      
      tasks:
        - task_key: sync_alerts
          environment_key: default
          notebook_task:
            notebook_path: ../src/alerting/sync_alerts.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
      
      schedule:
        quartz_cron_expression: "0 */5 * * * ?"  # Every 5 minutes
        pause_status: UNPAUSED
      
      tags:
        project: health_monitor
        layer: alerting
        job_type: sync

    alert_history_cleanup_job:
      name: "[${bundle.target}] Health Monitor - Alert History Cleanup"
      description: "Removes alert history older than retention period"
      
      tasks:
        - task_key: cleanup_history
          notebook_task:
            notebook_path: ../src/alerting/cleanup_history.py
            base_parameters:
              retention_days: "90"
      
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"  # Daily at 2 AM
        pause_status: PAUSED
```

---

## Alert Analytics Dashboard

### Key Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| **Total Alerts** | Count of configured alerts | 35+ |
| **Triggered Rate** | % of evaluations that trigger | < 5% |
| **False Positive Rate** | Alerts marked as false positive | < 10% |
| **MTTR** | Mean time to resolution | < 30 min |
| **Coverage by Domain** | Alerts per agent domain | Balanced |
| **ML Suppression Rate** | % suppressed by ML models | 10-20% |

---

## Alert Summary by Agent Domain

| Agent | Alert Count | Critical | Warning | Info |
|-------|-------------|----------|---------|------|
| 💰 **Cost** | **14** | 4 | 7 | 3 |
| 🔒 **Security** | 6 | 3 | 3 | 0 |
| ⚡ **Performance** | 8 | 0 | 4 | 4 |
| 🔄 **Reliability** | 8 | 5 | 3 | 0 |
| ✅ **Quality** | 5 | 2 | 2 | 1 |
| **Total** | **41** | **14** | **19** | **8** |

### Cost Agent Alert Breakdown

| Alert ID | Name | Type | Severity |
|----------|------|------|----------|
| COST-001 to COST-008 | Standard Cost Alerts | Threshold | Mixed |
| **COST-009** | Commit Undershoot Risk | Commit Tracking | WARNING |
| **COST-010** | Commit Overshoot Risk | Commit Tracking | WARNING |
| **COST-011** | Commit Variance Critical | Commit Tracking | CRITICAL |
| **COST-012** | Tag Coverage Drop | Tag Hygiene | WARNING |
| **COST-013** | Untagged High-Cost Job | Tag Hygiene | WARNING |
| **COST-014** | New Untagged Resources | Tag Hygiene | INFO |

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Pre-configured alerts | 35 alerts |
| Alert coverage | 100% of agent domains |
| Sync latency | < 5 minutes |
| False positive rate | < 10% |
| MTTR | < 30 minutes |
| Frontend CRUD | All operations functional |
| Custom templates | Working for all channels |

---

## References

### Official Databricks Documentation
- [Databricks SQL Alerts](https://docs.databricks.com/aws/en/sql/user/alerts/)
- [Alert API Reference](https://docs.databricks.com/api/workspace/alerts)
- [Notification Destinations](https://docs.databricks.com/sql/admin/notification-destinations.html)
- [Alert on Metric Views](https://docs.databricks.com/aws/en/sql/user/alerts/#alert-on-metric-views)

### Cursor Rules Reference
- [Cursor Rule 17 - Lakehouse Monitoring](mdc:.cursor/rules/17-lakehouse-monitoring-comprehensive.mdc)
- [Cursor Rule 14 - Metric Views Patterns](mdc:.cursor/rules/14-metric-views-patterns.mdc)

