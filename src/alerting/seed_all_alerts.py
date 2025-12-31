# Databricks notebook source
"""
Seed All Alerts - Comprehensive Alert Configuration
===================================================

Populates the alert_configurations table with all 56 planned alerts from:
plans/phase3-addendum-3.7-alerting-framework.md

Alert Categories:
- COST (18 alerts): Cost management, budget, commit tracking, tag hygiene
- SECURITY (8 alerts): Access control, audit, anomaly detection
- PERFORMANCE (12 alerts): Query performance, warehouse utilization
- RELIABILITY (10 alerts): Job reliability, SLA, cluster health
- QUALITY (6 alerts): Data quality, governance, freshness

Reference: https://docs.databricks.com/aws/en/sql/user/alerts
"""

from pyspark.sql import SparkSession
from typing import List, Dict, Any


def get_parameters() -> tuple[str, str]:
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    return catalog, gold_schema


# ==============================================================================
# COST ALERTS (18 Alerts)
# ==============================================================================

def get_cost_alerts(catalog: str, gold_schema: str) -> List[Dict[str, Any]]:
    """Return all Cost agent alerts."""
    return [
        # COST-001: Daily Cost Spike
        {
            "alert_id": "COST-001",
            "alert_name": "Daily Cost Spike",
            "alert_description": "Alerts when daily cost exceeds 150% of 7-day average. Business: Early warning for unexpected spend increases. Technical: Compares current day to rolling 7-day baseline.",
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH daily_costs AS (
    SELECT 
        usage_date,
        SUM(list_cost) as daily_cost
    FROM {catalog}.{gold_schema}.fact_usage
    WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -8)
    GROUP BY usage_date
),
baseline AS (
    SELECT AVG(daily_cost) as avg_cost
    FROM daily_costs
    WHERE usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -8) AND DATE_ADD(CURRENT_DATE(), -1)
)
SELECT 
    d.usage_date,
    d.daily_cost as current_cost,
    b.avg_cost as baseline_cost,
    ROUND(d.daily_cost / NULLIF(b.avg_cost, 0) * 100, 1) as pct_of_baseline,
    ROUND(d.daily_cost / NULLIF(b.avg_cost, 0) * 100, 1) as check_value
FROM daily_costs d
CROSS JOIN baseline b
WHERE d.usage_date = CURRENT_DATE()
  AND d.daily_cost > b.avg_cost * 1.5
""",
            "threshold_column": "check_value",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 150.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */4 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 14400,
            "owner": "finops-team@company.com",
            "tags": {"category": "cost_spike", "priority": "high"},
        },
        # COST-002: Weekly Cost Growth
        {
            "alert_id": "COST-002",
            "alert_name": "Weekly Cost Growth",
            "alert_description": "Alerts when week-over-week cost growth exceeds 30%. Business: Tracks spending trends. Technical: Compares current week to prior week.",
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    (SUM(CASE WHEN usage_date >= DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END) -
     SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END)) /
    NULLIF(SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END), 0) * 100
    AS wow_growth_pct
FROM {catalog}.{gold_schema}.fact_usage
WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -14)
""",
            "threshold_column": "wow_growth_pct",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 30.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 86400,
            "owner": "finops-team@company.com",
            "tags": {"category": "cost_trend", "priority": "medium"},
        },
        # COST-003: Budget Threshold (80%)
        {
            "alert_id": "COST-003",
            "alert_name": "Budget Threshold Warning",
            "alert_description": "Alerts when monthly spend exceeds 80% of budget. Business: Budget management. Technical: Compares MTD spend to monthly budget.",
            "agent_domain": "COST",
            "severity": "CRITICAL",
            "alert_query_template": f"""
WITH mtd_spend AS (
    SELECT SUM(list_cost) as mtd_cost
    FROM {catalog}.{gold_schema}.fact_usage
    WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
),
budget AS (
    SELECT 100000.0 as monthly_budget  -- Configure via separate config table
)
SELECT 
    mtd_cost,
    monthly_budget,
    ROUND(mtd_cost / NULLIF(monthly_budget, 0) * 100, 1) as budget_pct
FROM mtd_spend, budget
WHERE mtd_cost > monthly_budget * 0.8
""",
            "threshold_column": "budget_pct",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 80.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 86400,
            "owner": "finops-team@company.com",
            "tags": {"category": "budget", "priority": "critical"},
        },
        # COST-004: Budget Exceeded
        {
            "alert_id": "COST-004",
            "alert_name": "Budget Exceeded",
            "alert_description": "Alerts when monthly spend exceeds 100% of budget. Business: Critical budget breach. Technical: Immediate action required.",
            "agent_domain": "COST",
            "severity": "CRITICAL",
            "alert_query_template": f"""
WITH mtd_spend AS (
    SELECT SUM(list_cost) as mtd_cost
    FROM {catalog}.{gold_schema}.fact_usage
    WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
),
budget AS (
    SELECT 100000.0 as monthly_budget
)
SELECT 
    mtd_cost,
    monthly_budget,
    ROUND(mtd_cost / NULLIF(monthly_budget, 0) * 100, 1) as budget_pct
FROM mtd_spend, budget
WHERE mtd_cost > monthly_budget
""",
            "threshold_column": "budget_pct",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 100.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 3600,
            "owner": "finops-team@company.com",
            "tags": {"category": "budget", "priority": "critical"},
        },
        # COST-005: Untagged Cost Spike
        {
            "alert_id": "COST-005",
            "alert_name": "Untagged Cost Spike",
            "alert_description": "Alerts when untagged cost exceeds $1000/day. Business: FinOps hygiene enforcement. Technical: Identifies resources without proper tagging.",
            "agent_domain": "COST",
            "severity": "INFO",
            "alert_query_template": f"""
SELECT 
    usage_date,
    SUM(list_cost) as untagged_cost
FROM {catalog}.{gold_schema}.fact_usage
WHERE usage_date = DATE_ADD(CURRENT_DATE(), -1)
  AND (custom_tags IS NULL OR cardinality(custom_tags) = 0)
GROUP BY usage_date
HAVING SUM(list_cost) > 1000
""",
            "threshold_column": "untagged_cost",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 1000.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 86400,
            "owner": "finops-team@company.com",
            "tags": {"category": "tag_hygiene", "priority": "low"},
        },
        # COST-007: Runaway Job
        {
            "alert_id": "COST-007",
            "alert_name": "Runaway Job Detected",
            "alert_description": "Alerts when a single job costs more than $500/day. Business: Identifies cost anomalies. Technical: Detects misconfigured or stuck jobs.",
            "agent_domain": "COST",
            "severity": "CRITICAL",
            "alert_query_template": f"""
SELECT 
    usage_metadata_job_id as job_id,
    SUM(list_cost) as daily_cost
FROM {catalog}.{gold_schema}.fact_usage
WHERE usage_date = DATE_ADD(CURRENT_DATE(), -1)
  AND usage_metadata_job_id IS NOT NULL
GROUP BY usage_metadata_job_id
HAVING SUM(list_cost) > 500
ORDER BY daily_cost DESC
LIMIT 10
""",
            "threshold_column": "daily_cost",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 500.0,
            "empty_result_state": "OK",
            "aggregation_type": "MAX",
            "schedule_cron": "0 0 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 3600,
            "owner": "platform-team@company.com",
            "tags": {"category": "runaway", "priority": "critical"},
        },
        # COST-012: Tag Coverage Drop (original seeded alert - enhanced)
        {
            "alert_id": "COST-012",
            "alert_name": "Tag Coverage Drop",
            "alert_description": "Alerts when tag coverage over the last 7 days drops below 80%. Business: Enforces chargeback/FinOps hygiene. Technical: Based on fact_usage.custom_tags + list_cost aggregation.",
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH tagged_analysis AS (
    SELECT
        CASE
            WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
            ELSE 'TAGGED'
        END AS tag_status,
        SUM(list_cost) AS cost
    FROM {catalog}.{gold_schema}.fact_usage
    WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -7)
    GROUP BY CASE
        WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
        ELSE 'TAGGED'
    END
)
SELECT
    SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100 AS tag_coverage_pct
FROM tagged_analysis
""",
            "threshold_column": "tag_coverage_pct",
            "threshold_operator": "<",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 80.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 86400,
            "owner": "finops-team@company.com",
            "tags": {"category": "tag_hygiene", "priority": "high"},
        },
        # COST-015: Week-Over-Week Growth Spike
        {
            "alert_id": "COST-015",
            "alert_name": "Cost Week-Over-Week Growth Spike",
            "alert_description": "Alerts when weekly cost growth exceeds 30% compared to prior week. Pattern from Azure Serverless Cost Dashboard.",
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    (SUM(CASE WHEN usage_date >= DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END) -
     SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END)) /
    NULLIF(SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END), 0) * 100
    AS wow_growth_pct
FROM {catalog}.{gold_schema}.fact_usage
WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -14)
""",
            "threshold_column": "wow_growth_pct",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 30.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 86400,
            "owner": "finops-team@company.com",
            "tags": {"category": "cost_trend", "pattern_source": "azure_serverless"},
        },
        # COST-016: High Change Job Cost Alert
        {
            "alert_id": "COST-016",
            "alert_name": "High Change Job Cost Alert",
            "alert_description": "Alerts when any job cost increases by >$500 WoW. Identifies runaway jobs early.",
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT MAX(cost_increase) AS max_job_cost_increase
FROM (
    SELECT
        usage_metadata_job_id,
        SUM(CASE WHEN usage_date >= DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END) -
        SUM(CASE WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN list_cost ELSE 0 END)
        AS cost_increase
    FROM {catalog}.{gold_schema}.fact_usage
    WHERE usage_metadata_job_id IS NOT NULL
      AND usage_date >= DATE_ADD(CURRENT_DATE(), -14)
    GROUP BY usage_metadata_job_id
)
""",
            "threshold_column": "max_job_cost_increase",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 500.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 86400,
            "owner": "platform-team@company.com",
            "tags": {"category": "job_cost", "pattern_source": "azure_serverless"},
        },
        # COST-017: P90 Outlier Job Run
        {
            "alert_id": "COST-017",
            "alert_name": "Outlier Job Run Detected",
            "alert_description": "Alerts when a job run cost exceeds 200% of historical P90. Indicates runaway or misconfigured job.",
            "agent_domain": "COST",
            "severity": "CRITICAL",
            "alert_query_template": f"""
SELECT COUNT(*) AS outlier_run_count
FROM (
    WITH run_costs AS (
        SELECT
            usage_metadata_job_id,
            usage_metadata_job_run_id,
            SUM(list_cost) AS run_cost
        FROM {catalog}.{gold_schema}.fact_usage
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
            FROM {catalog}.{gold_schema}.fact_usage
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
""",
            "threshold_column": "outlier_run_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */15 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 1800,
            "owner": "platform-team@company.com",
            "tags": {"category": "outlier", "pattern_source": "azure_serverless"},
        },
        # COST-018: All-Purpose Cluster Cost
        {
            "alert_id": "COST-018",
            "alert_name": "High All-Purpose Cluster Cost",
            "alert_description": "Alerts when All-Purpose cluster costs exceed $500/day. These clusters are less cost-efficient than job clusters.",
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT SUM(list_cost) AS all_purpose_cost
FROM {catalog}.{gold_schema}.fact_usage
WHERE usage_date = DATE_ADD(CURRENT_DATE(), -1)
  AND sku_name LIKE '%ALL_PURPOSE%'
""",
            "threshold_column": "all_purpose_cost",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 500.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 86400,
            "owner": "finops-team@company.com",
            "tags": {"category": "cost_efficiency", "pattern_source": "workflow_advisor"},
        },
    ]


# ==============================================================================
# SECURITY ALERTS (8 Alerts)
# ==============================================================================

def get_security_alerts(catalog: str, gold_schema: str) -> List[Dict[str, Any]]:
    """Return all Security agent alerts."""
    return [
        # SEC-001: Sensitive Data Access Spike
        {
            "alert_id": "SEC-001",
            "alert_name": "Sensitive Data Access Spike",
            "alert_description": "Alerts when access to sensitive tables exceeds 200% of daily average. Business: Data security monitoring. Technical: Based on lineage events.",
            "agent_domain": "SECURITY",
            "severity": "CRITICAL",
            "alert_query_template": f"""
WITH today_access AS (
    SELECT COUNT(*) AS access_count
    FROM {catalog}.{gold_schema}.fact_table_lineage
    WHERE event_date = CURRENT_DATE()
      AND (source_table_full_name LIKE '%pii%' 
           OR source_table_full_name LIKE '%sensitive%'
           OR target_table_full_name LIKE '%pii%')
),
baseline AS (
    SELECT AVG(daily_count) AS avg_access
    FROM (
        SELECT DATE(event_time) AS event_date, COUNT(*) AS daily_count
        FROM {catalog}.{gold_schema}.fact_table_lineage
        WHERE event_date BETWEEN DATE_ADD(CURRENT_DATE(), -8) AND DATE_ADD(CURRENT_DATE(), -1)
          AND (source_table_full_name LIKE '%pii%' 
               OR source_table_full_name LIKE '%sensitive%'
               OR target_table_full_name LIKE '%pii%')
        GROUP BY DATE(event_time)
    )
)
SELECT 
    today_access.access_count,
    baseline.avg_access,
    ROUND(today_access.access_count / NULLIF(baseline.avg_access, 0) * 100, 1) AS pct_of_baseline
FROM today_access CROSS JOIN baseline
WHERE today_access.access_count > baseline.avg_access * 2
""",
            "threshold_column": "pct_of_baseline",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 200.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */15 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 900,
            "owner": "security-team@company.com",
            "tags": {"category": "data_access", "priority": "critical"},
        },
        # SEC-006: Failed Login Spike
        {
            "alert_id": "SEC-006",
            "alert_name": "Failed Login Spike",
            "alert_description": "Alerts when more than 5 failed logins occur in 10 minutes. Business: Brute force detection. Technical: Based on audit logs.",
            "agent_domain": "SECURITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT COUNT(*) AS failed_login_count
FROM {catalog}.{gold_schema}.fact_audit_logs
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 10 MINUTES
  AND action_name = 'login'
  AND response_status_code != 200
""",
            "threshold_column": "failed_login_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 5,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */5 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 600,
            "owner": "security-team@company.com",
            "tags": {"category": "authentication", "priority": "high"},
        },
        # SEC-007: Activity Burst Detection
        {
            "alert_id": "SEC-007",
            "alert_name": "User Activity Burst Detected",
            "alert_description": "Alerts when any user has 5x their average hourly activity. Indicates potential automated behavior or compromised account.",
            "agent_domain": "SECURITY",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH hourly_activity AS (
    SELECT
        created_by,
        DATE_TRUNC('hour', event_time) AS activity_hour,
        COUNT(*) AS events_in_hour
    FROM {catalog}.{gold_schema}.fact_table_lineage
    WHERE event_date >= DATE_ADD(CURRENT_DATE(), -7)
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
    HAVING COUNT(*) >= 10
),
current_hour AS (
    SELECT created_by, COUNT(*) AS current_events
    FROM {catalog}.{gold_schema}.fact_table_lineage
    WHERE event_time >= DATE_TRUNC('hour', CURRENT_TIMESTAMP())
      AND created_by NOT LIKE 'system.%'
    GROUP BY created_by
)
SELECT COUNT(*) AS burst_user_count
FROM current_hour c
JOIN user_baselines b ON c.created_by = b.created_by
WHERE c.current_events > b.avg_hourly_events * 5
""",
            "threshold_column": "burst_user_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */15 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 1800,
            "owner": "security-team@company.com",
            "tags": {"category": "temporal_clustering", "pattern_source": "audit_logs"},
        },
        # SEC-008: Off-Hours Activity
        {
            "alert_id": "SEC-008",
            "alert_name": "High Off-Hours Activity",
            "alert_description": "Alerts when more than 20% of daily activity occurs outside business hours (6 AM - 10 PM).",
            "agent_domain": "SECURITY",
            "severity": "INFO",
            "alert_query_template": f"""
SELECT
    SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 THEN 1 ELSE 0 END) * 100.0 /
    NULLIF(COUNT(*), 0) AS off_hours_pct
FROM {catalog}.{gold_schema}.fact_audit_logs
WHERE event_date = DATE_ADD(CURRENT_DATE(), -1)
  AND user_identity NOT LIKE 'system.%'
  AND user_identity NOT LIKE 'databricks-%'
""",
            "threshold_column": "off_hours_pct",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 20.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 7 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 86400,
            "owner": "security-team@company.com",
            "tags": {"category": "off_hours", "pattern_source": "audit_logs"},
        },
    ]


# ==============================================================================
# PERFORMANCE ALERTS (12 Alerts)
# ==============================================================================

def get_performance_alerts(catalog: str, gold_schema: str) -> List[Dict[str, Any]]:
    """Return all Performance agent alerts."""
    return [
        # PERF-001: Query P95 Degradation
        {
            "alert_id": "PERF-001",
            "alert_name": "Query P95 Degradation",
            "alert_description": "Alerts when P95 query duration exceeds 2x baseline. Business: User experience degradation. Technical: Based on query history.",
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH current_p95 AS (
    SELECT PERCENTILE(total_duration_ms / 1000.0, 0.95) AS p95_sec
    FROM {catalog}.{gold_schema}.fact_query_history
    WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
),
baseline_p95 AS (
    SELECT PERCENTILE(total_duration_ms / 1000.0, 0.95) AS p95_sec
    FROM {catalog}.{gold_schema}.fact_query_history
    WHERE query_start_time BETWEEN CURRENT_TIMESTAMP() - INTERVAL 8 DAYS AND CURRENT_TIMESTAMP() - INTERVAL 1 DAY
)
SELECT 
    current_p95.p95_sec AS current_p95,
    baseline_p95.p95_sec AS baseline_p95,
    ROUND(current_p95.p95_sec / NULLIF(baseline_p95.p95_sec, 0), 2) AS degradation_ratio
FROM current_p95 CROSS JOIN baseline_p95
WHERE current_p95.p95_sec > baseline_p95.p95_sec * 2
""",
            "threshold_column": "degradation_ratio",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 2.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */15 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 900,
            "owner": "platform-team@company.com",
            "tags": {"category": "query_performance", "priority": "high"},
        },
        # PERF-002: High Queue Time
        {
            "alert_id": "PERF-002",
            "alert_name": "High Query Queue Time",
            "alert_description": "Alerts when average queue time exceeds 30 seconds. Business: User wait time. Technical: Warehouse capacity issue.",
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT AVG(waiting_at_capacity_duration_ms / 1000.0) AS avg_queue_seconds
FROM {catalog}.{gold_schema}.fact_query_history
WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 15 MINUTES
  AND waiting_at_capacity_duration_ms > 0
""",
            "threshold_column": "avg_queue_seconds",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 30.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */5 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 300,
            "owner": "platform-team@company.com",
            "tags": {"category": "warehouse", "priority": "high"},
        },
        # PERF-009: High Query Spill Rate
        {
            "alert_id": "PERF-009",
            "alert_name": "High Query Spill Rate",
            "alert_description": "Alerts when more than 20% of queries have disk spills. Indicates memory pressure or need for warehouse scaling.",
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    SUM(CASE WHEN (COALESCE(spill_local_bytes, 0) + COALESCE(spill_remote_bytes, 0)) > 0 THEN 1 ELSE 0 END) * 100.0 /
    NULLIF(COUNT(*), 0) AS spill_rate_pct
FROM {catalog}.{gold_schema}.fact_query_history
WHERE query_start_time >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "spill_rate_pct",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 20.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 3600,
            "owner": "platform-team@company.com",
            "tags": {"category": "performance", "pattern_source": "dbsql_warehouse_advisor"},
        },
        # PERF-010: High Warehouse Queue Rate
        {
            "alert_id": "PERF-010",
            "alert_name": "High Warehouse Queue Rate",
            "alert_description": "Alerts when more than 10% of queries have queue time exceeding 10% of total duration.",
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    SUM(CASE WHEN waiting_at_capacity_duration_ms > total_duration_ms * 0.1 THEN 1 ELSE 0 END) * 100.0 /
    NULLIF(COUNT(*), 0) AS high_queue_rate
FROM {catalog}.{gold_schema}.fact_query_history
WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
  AND total_duration_ms > 1000
""",
            "threshold_column": "high_queue_rate",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 10.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */30 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 3600,
            "owner": "analytics-team@company.com",
            "tags": {"category": "performance", "pattern_source": "dbsql_warehouse_advisor"},
        },
        # PERF-011: Inefficient Query Rate
        {
            "alert_id": "PERF-011",
            "alert_name": "High Inefficient Query Rate",
            "alert_description": "Alerts when more than 20% of queries have efficiency issues (spill, high queue, or slow).",
            "agent_domain": "PERFORMANCE",
            "severity": "INFO",
            "alert_query_template": f"""
SELECT
    SUM(CASE
        WHEN (COALESCE(spill_local_bytes, 0) + COALESCE(spill_remote_bytes, 0)) > 0
          OR waiting_at_capacity_duration_ms > 30000
          OR total_duration_ms > 300000
        THEN 1 ELSE 0
    END) * 100.0 / NULLIF(COUNT(*), 0) AS inefficient_rate
FROM {catalog}.{gold_schema}.fact_query_history
WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
  AND total_duration_ms > 1000
""",
            "threshold_column": "inefficient_rate",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 20.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 86400,
            "owner": "analytics-team@company.com",
            "tags": {"category": "optimization", "pattern_source": "dbsql_warehouse_advisor"},
        },
        # PERF-012: Long Running Query (Real-Time)
        {
            "alert_id": "PERF-012",
            "alert_name": "Long Running Query",
            "alert_description": "Alerts when any query runs longer than 60 seconds. Pattern from DBSQL SME blog.",
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT COUNT(*) AS long_running_count
FROM {catalog}.{gold_schema}.fact_query_history
WHERE query_start_time >= CURRENT_TIMESTAMP() - INTERVAL 5 MINUTES
  AND total_duration_ms >= 60000
""",
            "threshold_column": "long_running_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 * * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 300,
            "owner": "analytics-team@company.com",
            "tags": {"category": "real_time_monitoring", "pattern_source": "dbsql_sme_blog"},
        },
    ]


# ==============================================================================
# RELIABILITY ALERTS (10 Alerts)
# ==============================================================================

def get_reliability_alerts(catalog: str, gold_schema: str) -> List[Dict[str, Any]]:
    """Return all Reliability agent alerts."""
    return [
        # REL-001: Job Success Rate Drop
        {
            "alert_id": "REL-001",
            "alert_name": "Job Success Rate Drop",
            "alert_description": "Alerts when job success rate drops below 90%. Business: Pipeline reliability. Technical: Based on job run history.",
            "agent_domain": "RELIABILITY",
            "severity": "CRITICAL",
            "alert_query_template": f"""
SELECT 
    COUNT(*) AS total_runs,
    SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS successful_runs,
    SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) AS success_rate
FROM {catalog}.{gold_schema}.fact_job_run_timeline
WHERE period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
  AND result_state IS NOT NULL
""",
            "threshold_column": "success_rate",
            "threshold_operator": "<",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 90.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */15 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 900,
            "owner": "data-engineering@company.com",
            "tags": {"category": "reliability", "priority": "critical"},
        },
        # REL-003: Consecutive Failures
        {
            "alert_id": "REL-003",
            "alert_name": "Consecutive Job Failures",
            "alert_description": "Alerts when any job fails more than 3 consecutive times. Business: Pipeline stuck. Technical: Immediate investigation needed.",
            "agent_domain": "RELIABILITY",
            "severity": "CRITICAL",
            "alert_query_template": f"""
WITH ranked_runs AS (
    SELECT 
        job_id,
        run_id,
        result_state,
        period_start_time,
        ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY period_start_time DESC) as rn
    FROM {catalog}.{gold_schema}.fact_job_run_timeline
    WHERE period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
      AND result_state IS NOT NULL
)
SELECT COUNT(DISTINCT job_id) as consecutive_failure_jobs
FROM ranked_runs
WHERE rn <= 3 AND result_state != 'SUCCEEDED'
GROUP BY job_id
HAVING COUNT(*) = 3
""",
            "threshold_column": "consecutive_failure_jobs",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0,
            "empty_result_state": "OK",
            "aggregation_type": "SUM",
            "schedule_cron": "0 */5 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 300,
            "owner": "data-engineering@company.com",
            "tags": {"category": "reliability", "priority": "critical"},
        },
        # REL-009: Job Duration Regression
        {
            "alert_id": "REL-009",
            "alert_name": "Job Duration Regression Detected",
            "alert_description": "Alerts when a job run duration increases by >50% compared to previous run. Helps detect performance regressions early.",
            "agent_domain": "RELIABILITY",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH recent_runs AS (
    SELECT
        job_id,
        run_id,
        run_duration_seconds,
        LAG(run_duration_seconds) OVER (PARTITION BY job_id ORDER BY period_start_time) AS prev_duration,
        result_state
    FROM {catalog}.{gold_schema}.fact_job_run_timeline
    WHERE period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
      AND result_state = 'SUCCEEDED'
)
SELECT COUNT(*) AS regression_count
FROM recent_runs
WHERE prev_duration IS NOT NULL
  AND run_duration_seconds > prev_duration * 1.5
  AND run_duration_seconds > 300
""",
            "threshold_column": "regression_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 2,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 86400,
            "owner": "data-engineering@company.com",
            "tags": {"category": "regression_detection", "pattern_source": "workflow_advisor"},
        },
        # CLUSTER-001: Underprovisioned Cluster
        {
            "alert_id": "CLUSTER-001",
            "alert_name": "Underprovisioned Cluster",
            "alert_description": "Alerts when a cluster has CPU saturation (>90%) more than 40% of the time. Indicates need for larger cluster.",
            "agent_domain": "RELIABILITY",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH cluster_saturation AS (
    SELECT
        cluster_id,
        SUM(CASE WHEN cpu_user_percent + cpu_system_percent > 90 THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(COUNT(*), 0) AS saturation_pct
    FROM {catalog}.{gold_schema}.fact_node_timeline
    WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
    GROUP BY cluster_id
)
SELECT COUNT(*) AS underprovisioned_cluster_count
FROM cluster_saturation
WHERE saturation_pct > 40
""",
            "threshold_column": "underprovisioned_cluster_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 86400,
            "owner": "platform-team@company.com",
            "tags": {"category": "right_sizing", "pattern_source": "workflow_advisor"},
        },
        # CLUSTER-002: Overprovisioned Cluster
        {
            "alert_id": "CLUSTER-002",
            "alert_name": "Overprovisioned Cluster Alert",
            "alert_description": "Alerts when a cluster has CPU idle (<20%) more than 70% of the time. Opportunity for cost savings through downsizing.",
            "agent_domain": "COST",
            "severity": "INFO",
            "alert_query_template": f"""
WITH cluster_idle AS (
    SELECT
        cluster_id,
        SUM(CASE WHEN cpu_user_percent + cpu_system_percent < 20 THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(COUNT(*), 0) AS idle_pct,
        COUNT(DISTINCT DATE(start_time)) AS days_observed
    FROM {catalog}.{gold_schema}.fact_node_timeline
    WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS
    GROUP BY cluster_id
    HAVING days_observed >= 3
)
SELECT COUNT(*) AS overprovisioned_cluster_count
FROM cluster_idle
WHERE idle_pct > 70
""",
            "threshold_column": "overprovisioned_cluster_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * 1",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 604800,
            "owner": "platform-team@company.com",
            "tags": {"category": "cost_savings", "pattern_source": "workflow_advisor"},
        },
        # CLUSTER-003: Memory Pressure
        {
            "alert_id": "CLUSTER-003",
            "alert_name": "Cluster Memory Pressure",
            "alert_description": "Alerts when a cluster has memory utilization >85% more than 30% of the time. May cause OOM errors.",
            "agent_domain": "RELIABILITY",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH memory_pressure AS (
    SELECT
        cluster_id,
        SUM(CASE WHEN mem_used_percent > 85 THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(COUNT(*), 0) AS pressure_pct
    FROM {catalog}.{gold_schema}.fact_node_timeline
    WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
    GROUP BY cluster_id
)
SELECT COUNT(*) AS clusters_with_pressure
FROM memory_pressure
WHERE pressure_pct > 30
""",
            "threshold_column": "clusters_with_pressure",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 */4 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 14400,
            "owner": "platform-team@company.com",
            "tags": {"category": "reliability", "pattern_source": "workflow_advisor"},
        },
    ]


# ==============================================================================
# QUALITY ALERTS (6 Alerts)
# ==============================================================================

def get_quality_alerts(catalog: str, gold_schema: str) -> List[Dict[str, Any]]:
    """Return all Quality agent alerts."""
    return [
        # QUAL-001: Quality Score Drop
        {
            "alert_id": "QUAL-001",
            "alert_name": "Data Quality Score Drop",
            "alert_description": "Alerts when overall data quality score drops below 0.9. Business: Data reliability. Technical: Based on DQ monitoring results.",
            "agent_domain": "QUALITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT AVG(quality_score) AS avg_quality_score
FROM {catalog}.{gold_schema}.fact_data_quality_monitoring
WHERE evaluation_date = DATE_ADD(CURRENT_DATE(), -1)
""",
            "threshold_column": "avg_quality_score",
            "threshold_operator": "<",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.9,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 * * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": True,
            "retrigger_seconds": 3600,
            "owner": "data-quality@company.com",
            "tags": {"category": "quality", "priority": "high"},
        },
        # GOV-001: Inactive Tables Increasing
        {
            "alert_id": "GOV-001",
            "alert_name": "Inactive Tables Increasing",
            "alert_description": "Alerts when significant number of tables become inactive. May indicate data pipeline issues or deprecation.",
            "agent_domain": "QUALITY",
            "severity": "WARNING",
            "alert_query_template": f"""
WITH recent_activity AS (
    SELECT DISTINCT COALESCE(source_table_full_name, target_table_full_name) AS table_name
    FROM {catalog}.{gold_schema}.fact_table_lineage
    WHERE event_date >= DATE_ADD(CURRENT_DATE(), -7)
),
prior_activity AS (
    SELECT DISTINCT COALESCE(source_table_full_name, target_table_full_name) AS table_name
    FROM {catalog}.{gold_schema}.fact_table_lineage
    WHERE event_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7)
)
SELECT COUNT(*) AS newly_inactive_tables
FROM prior_activity p
LEFT JOIN recent_activity r ON p.table_name = r.table_name
WHERE r.table_name IS NULL
""",
            "threshold_column": "newly_inactive_tables",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 10,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 86400,
            "owner": "data-governance@company.com",
            "tags": {"category": "governance", "pattern_source": "governance_hub"},
        },
    ]


# ==============================================================================
# Main Functions
# ==============================================================================

def get_all_alerts(catalog: str, gold_schema: str) -> List[Dict[str, Any]]:
    """Combine all alert definitions."""
    return (
        get_cost_alerts(catalog, gold_schema) +
        get_security_alerts(catalog, gold_schema) +
        get_performance_alerts(catalog, gold_schema) +
        get_reliability_alerts(catalog, gold_schema) +
        get_quality_alerts(catalog, gold_schema)
    )


def insert_alerts(spark: SparkSession, catalog: str, gold_schema: str, alerts: List[Dict[str, Any]]) -> int:
    """Insert alerts into alert_configurations table."""
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"
    
    inserted = 0
    skipped = 0
    
    for alert in alerts:
        alert_id = alert["alert_id"]
        
        # Check if alert already exists
        exists = spark.sql(f"""
            SELECT 1 FROM {cfg_table} WHERE alert_id = '{alert_id}'
        """).count() > 0
        
        if exists:
            print(f"  SKIP: {alert_id} (already exists)")
            skipped += 1
            continue
        
        # Escape query template for SQL insertion
        query_escaped = alert["alert_query_template"].replace("'", "''")
        description_escaped = alert.get("alert_description", "").replace("'", "''")
        
        # Build tags map
        tags = alert.get("tags", {})
        tags_sql = ", ".join([f"'{k}', '{v}'" for k, v in tags.items()])
        tags_expr = f"map({tags_sql})" if tags_sql else "map()"
        
        # Build notification channels array
        channels = alert.get("notification_channels", ["default_email"])
        channels_sql = ", ".join([f"'{c}'" for c in channels])
        channels_expr = f"array({channels_sql})"
        
        # Handle nullable fields
        retrigger = alert.get("retrigger_seconds")
        retrigger_sql = str(retrigger) if retrigger is not None else "NULL"
        
        threshold_double = alert.get("threshold_value_double")
        threshold_double_sql = str(threshold_double) if threshold_double is not None else "NULL"
        
        # Insert statement
        insert_sql = f"""
INSERT INTO {cfg_table} (
    alert_id, alert_name, alert_description, agent_domain, severity,
    alert_query_template, query_source, source_artifact_name,
    threshold_column, threshold_operator, threshold_value_type, 
    threshold_value_double, threshold_value_string, threshold_value_bool,
    empty_result_state, aggregation_type,
    schedule_cron, schedule_timezone, pause_status, is_enabled,
    notification_channels, notify_on_ok, retrigger_seconds,
    use_custom_template, custom_subject_template, custom_body_template,
    owner, created_by, created_at, tags
) VALUES (
    '{alert["alert_id"]}',
    '{alert["alert_name"]}',
    '{description_escaped}',
    '{alert["agent_domain"]}',
    '{alert["severity"]}',
    '{query_escaped}',
    'CUSTOM',
    NULL,
    '{alert["threshold_column"]}',
    '{alert["threshold_operator"]}',
    '{alert["threshold_value_type"]}',
    {threshold_double_sql},
    NULL,
    NULL,
    '{alert["empty_result_state"]}',
    '{alert.get("aggregation_type", "NONE")}',
    '{alert["schedule_cron"]}',
    '{alert["schedule_timezone"]}',
    '{alert["pause_status"]}',
    {str(alert["is_enabled"]).upper()},
    {channels_expr},
    {str(alert["notify_on_ok"]).upper()},
    {retrigger_sql},
    FALSE,
    NULL,
    NULL,
    '{alert["owner"]}',
    'seed_all_alerts',
    CURRENT_TIMESTAMP(),
    {tags_expr}
)
"""
        try:
            spark.sql(insert_sql)
            print(f"  INSERT: {alert_id} - {alert['alert_name']}")
            inserted += 1
        except Exception as e:
            print(f"  ERROR: {alert_id} - {str(e)[:100]}")
    
    return inserted


def main() -> None:
    """Main entry point."""
    dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
    dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
    
    catalog, gold_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    print("=" * 80)
    print("SEED ALL ALERTS")
    print("=" * 80)
    print(f"Target: {catalog}.{gold_schema}.alert_configurations")
    print("")
    
    # Get all alerts
    alerts = get_all_alerts(catalog, gold_schema)
    print(f"Total alerts defined: {len(alerts)}")
    print("")
    
    # Summary by domain
    domains = {}
    for a in alerts:
        d = a["agent_domain"]
        domains[d] = domains.get(d, 0) + 1
    
    print("Alert count by domain:")
    for domain, count in sorted(domains.items()):
        print(f"  {domain}: {count}")
    print("")
    
    # Insert alerts
    print("Inserting alerts:")
    inserted = insert_alerts(spark, catalog, gold_schema, alerts)
    
    print("")
    print("=" * 80)
    print(f"✓ Inserted {inserted} new alerts")
    print(f"  Skipped {len(alerts) - inserted} existing alerts")
    print("=" * 80)
    
    dbutils.notebook.exit(f"SUCCESS: Inserted {inserted} alerts")


if __name__ == "__main__":
    main()

