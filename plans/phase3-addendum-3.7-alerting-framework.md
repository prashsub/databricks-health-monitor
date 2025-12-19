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

## 🆕 Dashboard Pattern-Derived Alerts

Based on analysis of real-world Databricks dashboards (see [phase3-use-cases.md SQL Patterns Catalog](./phase3-use-cases.md#-sql-query-patterns-catalog-from-dashboard-analysis)), the following new alert definitions should be added:

### New Cost Alerts (from Dashboard Patterns)

#### COST-015: Week-Over-Week Growth Spike (Pattern 1)
**Source:** Azure Serverless Cost Dashboard

```sql
-- Alert: WoW growth exceeds 30% threshold
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'COST-015',
    'Cost Week-Over-Week Growth Spike',
    'Alerts when weekly cost growth exceeds 30% compared to prior week. Pattern from Azure Serverless Cost Dashboard.',
    'COST',
    'WARNING',
    $$
    SELECT
        (SUM(CASE WHEN usage_date >= DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END) -
         SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END)) /
        NULLIF(SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END), 0) * 100
        AS wow_growth_pct
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -14)
    $$,
    'CUSTOM',
    NULL,
    'wow_growth_pct',
    '>',
    30.0,
    'STATIC',
    7,
    'NONE',
    '0 0 8 * * ?',  -- Daily at 8 AM
    'America/New_York',
    TRUE,
    ARRAY['default_slack', 'default_email'],
    TRUE,
    60,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'platform-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'azure_serverless', 'category', 'growth')
);
```

#### COST-016: High Change Entity Alert (Pattern 1)
**Source:** Azure Serverless Cost Dashboard - highest_change_jobs

```sql
-- Alert: Any single job's 7-day cost increased by more than $500
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'COST-016',
    'High Change Job Cost Alert',
    'Alerts when any job cost increases by >$500 WoW. Identifies runaway jobs early.',
    'COST',
    'WARNING',
    $$
    SELECT MAX(cost_increase) AS max_job_cost_increase
    FROM (
        SELECT
            usage_metadata_job_id,
            SUM(CASE WHEN usage_date >= DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END) -
            SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END)
            AS cost_increase
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_metadata_job_id IS NOT NULL
          AND usage_date >= DATE_ADD(CURRENT_DATE(), -14)
        GROUP BY usage_metadata_job_id
    )
    $$,
    'CUSTOM',
    NULL,
    'max_job_cost_increase',
    '>',
    500.0,
    'STATIC',
    7,
    'NONE',
    '0 0 8 * * ?',
    'America/New_York',
    TRUE,
    ARRAY['default_slack'],
    FALSE,
    120,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'platform-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'azure_serverless', 'category', 'entity_growth')
);
```

#### COST-017: P90 Outlier Job Run (Pattern 3)
**Source:** Azure Serverless Cost Dashboard - outlier detection

```sql
-- Alert: Job run cost exceeds 200% of job's P90
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'COST-017',
    'Outlier Job Run Detected',
    'Alerts when a job run cost exceeds 200% of historical P90. Indicates runaway or misconfigured job.',
    'COST',
    'CRITICAL',
    $$
    SELECT COUNT(*) AS outlier_run_count
    FROM (
        WITH run_costs AS (
            SELECT
                usage_metadata_job_id,
                usage_metadata_job_run_id,
                SUM(list_cost) AS run_cost
            FROM ${catalog}.${gold_schema}.fact_usage
            WHERE usage_metadata_job_id IS NOT NULL
              AND usage_date = CURRENT_DATE()
            GROUP BY usage_metadata_job_id, usage_metadata_job_run_id
        ),
        job_baselines AS (
            SELECT
                usage_metadata_job_id,
                PERCENTILE(run_cost, 0.9) AS p90_cost
            FROM (
                SELECT usage_metadata_job_id, usage_metadata_job_run_id, SUM(list_cost) AS run_cost
                FROM ${catalog}.${gold_schema}.fact_usage
                WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -30)
                  AND usage_date < CURRENT_DATE()
                GROUP BY usage_metadata_job_id, usage_metadata_job_run_id
            )
            GROUP BY usage_metadata_job_id
        )
        SELECT r.*
        FROM run_costs r
        JOIN job_baselines b ON r.usage_metadata_job_id = b.usage_metadata_job_id
        WHERE r.run_cost > b.p90_cost * 2
    )
    $$,
    'CUSTOM',
    NULL,
    'outlier_run_count',
    '>',
    0,
    'STATIC',
    30,
    'NONE',
    '0 */15 * * * ?',  -- Every 15 minutes
    'America/New_York',
    TRUE,
    ARRAY['default_pagerduty'],
    FALSE,
    30,
    FALSE,
    NULL,
    NULL,
    'OK',
    TRUE,  -- ML enabled for suppression
    'cost_anomaly_detector',
    0.9,
    'platform-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'azure_serverless', 'category', 'outlier')
);
```

### New Governance Alerts (from Dashboard Patterns)

#### GOV-001: Inactive Table Count Increase (Pattern 7)
**Source:** Governance Hub Dashboard

```sql
-- Alert: More than 10 tables became inactive in last 7 days
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'GOV-001',
    'Inactive Tables Increasing',
    'Alerts when significant number of tables become inactive. May indicate data pipeline issues or deprecation.',
    'QUALITY',
    'WARNING',
    $$
    WITH recent_activity AS (
        SELECT DISTINCT COALESCE(source_table_full_name, target_table_full_name) AS table_name
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date >= DATE_ADD(CURRENT_DATE(), -7)
    ),
    prior_activity AS (
        SELECT DISTINCT COALESCE(source_table_full_name, target_table_full_name) AS table_name
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7)
    )
    SELECT COUNT(*) AS newly_inactive_tables
    FROM prior_activity p
    LEFT JOIN recent_activity r ON p.table_name = r.table_name
    WHERE r.table_name IS NULL
    $$,
    'CUSTOM',
    NULL,
    'newly_inactive_tables',
    '>',
    10,
    'STATIC',
    7,
    'NONE',
    '0 0 6 * * ?',  -- Daily at 6 AM
    'America/New_York',
    TRUE,
    ARRAY['default_email'],
    FALSE,
    1440,  -- Daily
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'data-governance@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'governance_hub', 'category', 'governance')
);
```

### New Performance Alerts (from Dashboard Patterns)

#### PERF-009: Query Spill Rate Spike
**Source:** DBSQL Warehouse Advisor Dashboard

```sql
-- Alert: Query spill rate exceeds 20%
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'PERF-009',
    'High Query Spill Rate',
    'Alerts when more than 20% of queries have disk spills. Indicates memory pressure or need for warehouse scaling.',
    'PERFORMANCE',
    'WARNING',
    $$
    SELECT
        SUM(CASE WHEN (COALESCE(spill_local_bytes, 0) + COALESCE(spill_remote_bytes, 0)) > 0 THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(COUNT(*), 0) AS spill_rate_pct
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE query_start_time >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    $$,
    'CUSTOM',
    NULL,
    'spill_rate_pct',
    '>',
    20.0,
    'STATIC',
    1,
    'NONE',
    '0 0 * * * ?',  -- Hourly
    'America/New_York',
    TRUE,
    ARRAY['default_slack'],
    TRUE,
    60,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'platform-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'dbsql_warehouse_advisor', 'category', 'performance')
);
```

### Alert Summary by Pattern Source

| Pattern Source | New Alerts | Alert IDs |
|----------------|------------|-----------|
| **Azure Serverless Cost** | 3 | COST-015, COST-016, COST-017 |
| **Governance Hub** | 1 | GOV-001 |
| **DBSQL Warehouse Advisor** | 1 | PERF-009 |
| **Total New** | **5** | |

### Alert Threshold Recommendations from Dashboards

| Metric | Recommended Threshold | Severity | Source |
|--------|----------------------|----------|--------|
| WoW Cost Growth | 30% WARNING, 50% CRITICAL | Mixed | Azure Serverless |
| MoM Cost Growth | 20% WARNING, 40% CRITICAL | Mixed | Azure Serverless |
| P90 Cost Deviation | 150% WARNING, 200% CRITICAL | Mixed | Serverless Cost |
| Tag Coverage Drop | 10% drop WARNING | WARNING | Jobs System Tables |
| Inactive Tables | >10 in 7 days | WARNING | Governance Hub |
| Spill Rate | >20% | WARNING | DBSQL Warehouse Advisor |
| Queue Rate | >10% | WARNING | DBSQL Warehouse Advisor |

---

---

## 🆕 GitHub Repository Pattern Enhancements for Alerting Framework

Based on analysis of open-source Databricks repositories, the following alert enhancements should be incorporated:

### From system-tables-audit-logs Repository

#### Time-Windowed Anomaly Alerts
**Pattern:** 24-hour and 90-day rolling baselines for dynamic thresholds

#### SEC-007: Activity Burst Detection (🆕)
**Source:** Temporal clustering pattern from audit logs repo

```sql
-- Alert: User activity burst (5x normal in single hour)
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'SEC-007',
    'User Activity Burst Detected',
    'Alerts when any user has 5x their average hourly activity. Indicates potential automated behavior or compromised account. Pattern from system-tables-audit-logs repo.',
    'SECURITY',
    'WARNING',
    $$
    WITH hourly_activity AS (
        SELECT
            created_by,
            DATE_TRUNC('hour', event_time) AS activity_hour,
            COUNT(*) AS events_in_hour
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
          -- Exclude system accounts (from audit logs repo pattern)
          AND created_by NOT LIKE 'system.%'
          AND created_by NOT LIKE 'databricks-%'
        GROUP BY created_by, DATE_TRUNC('hour', event_time)
    ),
    user_baselines AS (
        SELECT
            created_by,
            AVG(events_in_hour) AS avg_hourly_events
        FROM hourly_activity
        GROUP BY created_by
        HAVING COUNT(*) >= 10  -- Require 10+ active hours for baseline
    ),
    current_hour AS (
        SELECT created_by, COUNT(*) AS current_events
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_time >= DATE_TRUNC('hour', CURRENT_TIMESTAMP())
          AND created_by NOT LIKE 'system.%'
        GROUP BY created_by
    )
    SELECT COUNT(*) AS burst_user_count
    FROM current_hour c
    JOIN user_baselines b ON c.created_by = b.created_by
    WHERE c.current_events > b.avg_hourly_events * 5
    $$,
    'CUSTOM',
    NULL,
    'burst_user_count',
    '>',
    0,
    'STATIC',
    7,
    'NONE',
    '0 */15 * * * ?',  -- Every 15 minutes
    'America/New_York',
    TRUE,
    ARRAY['default_slack', 'security_team'],
    FALSE,
    30,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'security-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'system-tables-audit-logs', 'category', 'temporal_clustering')
);
```

#### SEC-008: Off-Hours Activity Alert (🆕)
**Source:** Temporal analysis pattern from audit logs repo

```sql
-- Alert: Significant off-hours activity (>20% of daily activity outside business hours)
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'SEC-008',
    'High Off-Hours Activity',
    'Alerts when more than 20% of daily activity occurs outside business hours (6 AM - 10 PM). Pattern from system-tables-audit-logs repo.',
    'SECURITY',
    'INFO',
    $$
    SELECT
        SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(COUNT(*), 0) AS off_hours_pct
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date = CURRENT_DATE() - INTERVAL 1 DAY
      AND user_identity NOT LIKE 'system.%'
      AND user_identity NOT LIKE 'databricks-%'
    $$,
    'CUSTOM',
    NULL,
    'off_hours_pct',
    '>',
    20.0,
    'STATIC',
    7,
    'NONE',
    '0 0 7 * * ?',  -- Daily at 7 AM
    'America/New_York',
    TRUE,
    ARRAY['default_email'],
    FALSE,
    1440,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'security-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'system-tables-audit-logs', 'category', 'off_hours')
);
```

### From Workflow Advisor Repository

#### CLUSTER-001: Underprovisioned Cluster Alert (🆕)
**Source:** Right-sizing pattern from Workflow Advisor repo

```sql
-- Alert: Cluster is underprovisioned (CPU saturation > 40% of time)
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'CLUSTER-001',
    'Underprovisioned Cluster',
    'Alerts when a cluster has CPU saturation (>90%) more than 40% of the time. Indicates need for larger cluster or more workers. Pattern from Workflow Advisor repo.',
    'PERFORMANCE',
    'WARNING',
    $$
    WITH cluster_saturation AS (
        SELECT
            cluster_id,
            SUM(CASE WHEN cpu_user_percent + cpu_system_percent > 90 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0) AS saturation_pct
        FROM ${catalog}.${gold_schema}.fact_node_timeline
        WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
        GROUP BY cluster_id
    )
    SELECT COUNT(*) AS underprovisioned_cluster_count
    FROM cluster_saturation
    WHERE saturation_pct > 40
    $$,
    'CUSTOM',
    NULL,
    'underprovisioned_cluster_count',
    '>',
    0,
    'STATIC',
    1,
    'NONE',
    '0 0 8 * * ?',  -- Daily at 8 AM
    'America/New_York',
    TRUE,
    ARRAY['default_slack'],
    TRUE,
    1440,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'platform-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'workflow-advisor', 'category', 'right_sizing')
);
```

#### CLUSTER-002: Overprovisioned Cluster Alert (🆕)
**Source:** Right-sizing pattern from Workflow Advisor repo

```sql
-- Alert: Cluster is overprovisioned (CPU idle > 70% of time)
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'CLUSTER-002',
    'Overprovisioned Cluster - Cost Savings Opportunity',
    'Alerts when a cluster has CPU idle (<20%) more than 70% of the time. Indicates opportunity for cost savings through downsizing. Pattern from Workflow Advisor repo.',
    'COST',
    'INFO',
    $$
    WITH cluster_idle AS (
        SELECT
            cluster_id,
            SUM(CASE WHEN cpu_user_percent + cpu_system_percent < 20 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0) AS idle_pct,
            COUNT(DISTINCT DATE(start_time)) AS days_observed
        FROM ${catalog}.${gold_schema}.fact_node_timeline
        WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS
        GROUP BY cluster_id
        HAVING days_observed >= 3  -- At least 3 days of data
    )
    SELECT COUNT(*) AS overprovisioned_cluster_count
    FROM cluster_idle
    WHERE idle_pct > 70
    $$,
    'CUSTOM',
    NULL,
    'overprovisioned_cluster_count',
    '>',
    0,
    'STATIC',
    7,
    'NONE',
    '0 0 8 * * 1',  -- Weekly on Monday at 8 AM
    'America/New_York',
    TRUE,
    ARRAY['default_email'],
    TRUE,
    10080,  -- Weekly
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'platform-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'workflow-advisor', 'category', 'cost_savings')
);
```

#### CLUSTER-003: Memory Pressure Alert (🆕)
**Source:** Resource utilization pattern from Workflow Advisor repo

```sql
-- Alert: Cluster experiencing memory pressure
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'CLUSTER-003',
    'Cluster Memory Pressure',
    'Alerts when a cluster has memory utilization >85% more than 30% of the time. May cause OOM errors. Pattern from Workflow Advisor repo.',
    'RELIABILITY',
    'WARNING',
    $$
    WITH memory_pressure AS (
        SELECT
            cluster_id,
            SUM(CASE WHEN mem_used_percent > 85 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0) AS pressure_pct
        FROM ${catalog}.${gold_schema}.fact_node_timeline
        WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
        GROUP BY cluster_id
    )
    SELECT COUNT(*) AS clusters_with_pressure
    FROM memory_pressure
    WHERE pressure_pct > 30
    $$,
    'CUSTOM',
    NULL,
    'clusters_with_pressure',
    '>',
    0,
    'STATIC',
    1,
    'NONE',
    '0 */4 * * * ?',  -- Every 4 hours
    'America/New_York',
    TRUE,
    ARRAY['default_slack'],
    FALSE,
    240,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'platform-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'workflow-advisor', 'category', 'reliability')
);
```

### From DBSQL Warehouse Advisor Repository

#### PERF-010: High Queue Rate Alert (🆕)
**Source:** Query efficiency pattern from DBSQL Warehouse Advisor repo

```sql
-- Alert: Warehouse has high query queue rate
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'PERF-010',
    'High Warehouse Queue Rate',
    'Alerts when more than 10% of queries have queue time exceeding 10% of total duration. Indicates warehouse capacity issue. Pattern from DBSQL Warehouse Advisor repo.',
    'PERFORMANCE',
    'WARNING',
    $$
    SELECT
        SUM(CASE WHEN waiting_at_capacity_duration_ms > total_duration_ms * 0.1 THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(COUNT(*), 0) AS high_queue_rate
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
      AND total_duration_ms > 1000  -- Ignore trivial queries
    $$,
    'CUSTOM',
    NULL,
    'high_queue_rate',
    '>',
    10.0,
    'STATIC',
    1,
    'NONE',
    '0 */30 * * * ?',  -- Every 30 minutes
    'America/New_York',
    TRUE,
    ARRAY['default_slack'],
    TRUE,
    60,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'analytics-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'dbsql-warehouse-advisor', 'category', 'performance')
);
```

#### PERF-011: Inefficient Query Rate Alert (🆕)
**Source:** Query efficiency pattern from DBSQL Warehouse Advisor repo

```sql
-- Alert: High rate of inefficient queries
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'PERF-011',
    'High Inefficient Query Rate',
    'Alerts when more than 20% of queries have efficiency issues (spill, high queue, or slow). Pattern from DBSQL Warehouse Advisor repo.',
    'PERFORMANCE',
    'INFO',
    $$
    SELECT
        SUM(CASE
            WHEN (COALESCE(spill_local_bytes, 0) + COALESCE(spill_remote_bytes, 0)) > 0
              OR waiting_at_capacity_duration_ms > 30000
              OR total_duration_ms > 300000
            THEN 1 ELSE 0
        END) * 100.0 / NULLIF(COUNT(*), 0) AS inefficient_rate
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
      AND total_duration_ms > 1000
    $$,
    'CUSTOM',
    NULL,
    'inefficient_rate',
    '>',
    20.0,
    'STATIC',
    1,
    'NONE',
    '0 0 8 * * ?',  -- Daily at 8 AM
    'America/New_York',
    TRUE,
    ARRAY['default_email'],
    TRUE,
    1440,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'analytics-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'dbsql-warehouse-advisor', 'category', 'optimization')
);
```

### GitHub Repo Alert Summary

| Alert ID | Name | Source Repo | Category |
|----------|------|-------------|----------|
| SEC-007 | Activity Burst Detection | system-tables-audit-logs | Temporal Clustering |
| SEC-008 | Off-Hours Activity | system-tables-audit-logs | Temporal Analysis |
| CLUSTER-001 | Underprovisioned Cluster | Workflow Advisor | Right-Sizing |
| CLUSTER-002 | Overprovisioned Cluster | Workflow Advisor | Cost Savings |
| CLUSTER-003 | Memory Pressure | Workflow Advisor | Reliability |
| PERF-010 | High Queue Rate | DBSQL Warehouse Advisor | Performance |
| PERF-011 | Inefficient Query Rate | DBSQL Warehouse Advisor | Optimization |

**Total New Alerts from GitHub Repos: 7**

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Pre-configured alerts | 53 alerts (46 + 7 GitHub repo-derived) |
| Alert coverage | 100% of agent domains |
| Sync latency | < 5 minutes |
| False positive rate | < 10% |
| MTTR | < 30 minutes |
| Frontend CRUD | All operations functional |
| Custom templates | Working for all channels |
| Right-sizing alerts | Identify 100% of misprovisioned clusters |

---

## References

### Official Databricks Documentation
- [Databricks SQL Alerts](https://docs.databricks.com/aws/en/sql/user/alerts/)
- [Alert API Reference](https://docs.databricks.com/api/workspace/alerts)
- [Notification Destinations](https://docs.databricks.com/sql/admin/notification-destinations.html)
- [Alert on Metric Views](https://docs.databricks.com/aws/en/sql/user/alerts/#alert-on-metric-views)

### GitHub Repository References (🆕)
- [system-tables-audit-logs](https://github.com/andyweaves/system-tables-audit-logs) - Temporal clustering, off-hours detection, system account filtering
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme) - Query efficiency alerts, warehouse sizing
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor) - Under/over-provisioning alerts, memory pressure detection

### Blog Post References (🆕)
- [Real-Time Query Monitoring on DBSQL with Alerts](https://medium.com/dbsql-sme-engineering/real-time-query-monitoring-on-dbsql-with-alerts-24e4e7e4a904) - 60-second SLA threshold, 1-minute alerting cadence, UC connections for API access

### Cursor Rules Reference
- [Cursor Rule 17 - Lakehouse Monitoring](mdc:.cursor/rules/17-lakehouse-monitoring-comprehensive.mdc)
- [Cursor Rule 14 - Metric Views Patterns](mdc:.cursor/rules/14-metric-views-patterns.mdc)

---

## 🆕 Blog Post Pattern Enhancements for Alerting Framework

Based on analysis of Databricks engineering blog posts, the following alert enhancements should be incorporated:

### From "Real-Time Query Monitoring on DBSQL with Alerts" Blog

#### Recommended Alert Thresholds (Validated by SME Team)
| Metric | Threshold | Severity | Notes |
|--------|-----------|----------|-------|
| Long-running query | 60 seconds | WARNING | Recommended SLA trigger point |
| Alert polling interval | 1 minute | - | Balances responsiveness with resource usage |
| Queue time ratio | >10% of runtime | WARNING | From Warehouse Advisor |

#### Real-Time Alerting via Query History API (🆕)
**Use Case:** Near real-time alerts faster than system table updates

```sql
-- Pattern: Three-stage query architecture for real-time monitoring
-- Stage 1: Raw API call via UC Connection
-- Stage 2: JSON parsing into structured columns
-- Stage 3: Business logic filtering

-- Alert Query for PERF-012: Real-Time Long Running Query
-- Uses Query History API for faster alerting than system tables
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'PERF-012',
    'Long Running Query (Real-Time)',
    'Alerts when any query runs longer than 60 seconds. Uses Query History API for near real-time alerting. Pattern from DBSQL SME blog.',
    'PERFORMANCE',
    'WARNING',
    $$
    -- Note: This query assumes a UC Function wrapping the Query History API
    -- See blog for setup: Real-Time Query Monitoring on DBSQL with Alerts
    SELECT COUNT(*) AS long_running_count
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 5 MINUTES
      AND total_duration_ms >= 60000  -- 60-second threshold from blog
      AND execution_status = 'RUNNING'
    $$,
    'CUSTOM',
    NULL,
    'long_running_count',
    '>',
    0,
    'STATIC',
    1,
    'NONE',
    '0 * * * * ?',  -- Every minute (1-minute cadence from blog)
    'America/New_York',
    TRUE,
    ARRAY['default_slack'],
    FALSE,
    5,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'analytics-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'dbsql-sme-blog', 'category', 'real_time_monitoring')
);
```

### From "Workflow Advisor Dashboard" Blog

#### Job State Classification for Alerts
The blog recommends tracking 5 distinct job outcome states:
1. **SUCCEEDED** - Normal completion
2. **ERRORED** - Runtime error
3. **FAILED** - Job failure
4. **TIMED_OUT** - Duration exceeded limit
5. **CANCELLED** - Manual or system cancellation

#### Run Duration Regression Alert (🆕)
**Pattern:** "% Change in duration of last job from its previous run" for detecting performance regressions

```sql
-- Alert Query for REL-009: Job Duration Regression
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'REL-009',
    'Job Duration Regression Detected',
    'Alerts when a job run duration increases by >50% compared to previous run. Helps detect performance regressions early. Pattern from Workflow Advisor blog.',
    'RELIABILITY',
    'WARNING',
    $$
    WITH recent_runs AS (
        SELECT
            job_id,
            run_id,
            run_duration_seconds,
            LAG(run_duration_seconds) OVER (PARTITION BY job_id ORDER BY period_start_time) AS prev_duration,
            result_state
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline
        WHERE period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
          AND result_state = 'SUCCEEDED'
    )
    SELECT COUNT(*) AS regression_count
    FROM recent_runs
    WHERE prev_duration IS NOT NULL
      AND run_duration_seconds > prev_duration * 1.5  -- 50% increase threshold
      AND run_duration_seconds > 300  -- Only jobs > 5 minutes
    $$,
    'CUSTOM',
    NULL,
    'regression_count',
    '>',
    2,
    'STATIC',
    1,
    'NONE',
    '0 0 8 * * ?',
    'America/New_York',
    TRUE,
    ARRAY['default_email'],
    FALSE,
    1440,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'data-engineering@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'workflow-advisor-blog', 'category', 'regression_detection')
);
```

#### All-Purpose Cluster Cost Alert (🆕)
**Pattern:** Blog highlights "ALL PURPOSE CLUSTERS warrant scrutiny due to cost inefficiency"

```sql
-- Alert Query for COST-018: All-Purpose Cluster Cost
INSERT INTO ${catalog}.${gold_schema}.alert_configurations VALUES (
    'COST-018',
    'High All-Purpose Cluster Cost',
    'Alerts when All-Purpose cluster costs exceed $500/day. These clusters are less cost-efficient than job clusters. Pattern from Workflow Advisor blog.',
    'COST',
    'WARNING',
    $$
    SELECT SUM(list_cost) AS all_purpose_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date = CURRENT_DATE() - INTERVAL 1 DAY
      AND sku_name LIKE '%ALL_PURPOSE%'
    $$,
    'CUSTOM',
    NULL,
    'all_purpose_cost',
    '>',
    500.0,
    'STATIC',
    1,
    'NONE',
    '0 0 8 * * ?',
    'America/New_York',
    TRUE,
    ARRAY['default_email'],
    TRUE,
    1440,
    FALSE,
    NULL,
    NULL,
    'OK',
    FALSE,
    NULL,
    0.8,
    'finops-team@company.com',
    'system',
    CURRENT_TIMESTAMP(),
    NULL,
    NULL,
    MAP('pattern_source', 'workflow-advisor-blog', 'category', 'cost_efficiency')
);
```

### Blog Post Alert Summary

| Alert ID | Name | Source Blog | Category |
|----------|------|-------------|----------|
| PERF-012 | Long Running Query (Real-Time) | Real-Time Query Monitoring | Performance |
| REL-009 | Job Duration Regression | Workflow Advisor | Reliability |
| COST-018 | All-Purpose Cluster Cost | Workflow Advisor | Cost |

**Total New Alerts from Blog Posts: 3**
**Updated Total Alert Count: 53 → 56**

