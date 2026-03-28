# Databricks notebook source
"""
ML-Driven Alert Seeding
=======================

Seeds conservative ML-driven alerts into alert_configurations.
These alerts query ML prediction tables in the feature_schema
and fire only when models have flagged anomalies or high-risk items.

ALERT PHILOSOPHY:
-----------------
- Conservative: only anomaly-detection, high-signal classifiers,
  and predictive leading-indicators with clear actionability.
- All alerts start PAUSED (enable selectively after validation).
- Each query checks for recent predictions (last 24h) to avoid
  stale detections.
- Tagged with source=ml_prediction for easy filtering.
- Signals that are purely advisory or lack urgency are kept
  out of alerting and surfaced via dashboards/Genie instead.

ML ALERT INVENTORY (14 alerts):
-------------------------------
    COST (2):        ML-COST-001 (anomaly), ML-COST-002 (budget forecast)
    SECURITY (3):    ML-SEC-001 (threat), ML-SEC-002 (exfiltration),
                     ML-SEC-003 (privilege escalation)
    PERFORMANCE (4): ML-PERF-001 (regression), ML-PERF-002 (warehouse opt),
                     ML-PERF-003 (DBR migration), ML-PERF-004 (capacity)
    RELIABILITY (3): ML-REL-001 (job failure), ML-REL-002 (SLA breach),
                     ML-REL-003 (pipeline health)
    QUALITY (2):     ML-QUAL-001 (drift), ML-QUAL-002 (freshness)

Reference: src/ml/utils/prediction_metadata.py for table schemas
"""

from pyspark.sql import SparkSession
from typing import List, Dict, Any


def get_parameters() -> tuple[str, str, str]:
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema


def get_ml_alerts(catalog: str, gold_schema: str, feature_schema: str) -> List[Dict[str, Any]]:
    """
    Return all ML-driven alert definitions.

    Each alert queries a prediction table in {catalog}.{feature_schema}
    and checks for recent anomaly/risk detections.
    """
    return [
        # ==================================================================
        # COST DOMAIN (2 alerts)
        # ==================================================================
        {
            "alert_id": "ML-COST-001",
            "alert_name": "ML Cost Anomaly Detected",
            "alert_description": (
                "Fires when the cost_anomaly_detector IsolationForest model "
                "flags any workspace-day as anomalous (prediction=-1) in the "
                "last 24 hours. Business: early ML-driven warning for unusual "
                "spend. Technical: queries cost_anomaly_predictions."
            ),
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS anomaly_count,
    MIN(scored_at) AS earliest_anomaly,
    MAX(scored_at) AS latest_anomaly
FROM {catalog}.{feature_schema}.cost_anomaly_predictions
WHERE prediction = -1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "anomaly_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 21600,
            "owner": "finops-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "cost_anomaly_detector",
                "ml_type": "isolation_forest",
                "priority": "medium",
            },
        },

        # ML-COST-002: Projected Budget Overspend
        {
            "alert_id": "ML-COST-002",
            "alert_name": "ML Projected Budget Overspend",
            "alert_description": (
                "Fires when the budget_forecaster Prophet model projects that "
                "spending will exceed the budget threshold within 7 days. "
                "Business: forward-looking budget breach warning unlike MTD "
                "checks (COST-003/004); gives time to throttle workloads or "
                "request budget increase. Technical: queries "
                "budget_forecast_predictions for forecasted spend vs budget."
            ),
            "agent_domain": "COST",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS overspend_forecast_count,
    ROUND(MAX(prediction), 2) AS max_forecasted_cost,
    MAX(scored_at) AS latest_forecast
FROM {catalog}.{feature_schema}.budget_forecast_predictions
WHERE prediction > 100000
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "overspend_forecast_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
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
            "tags": {
                "source": "ml_prediction",
                "ml_model": "budget_forecaster",
                "ml_type": "prophet",
                "priority": "medium",
            },
        },

        # ==================================================================
        # SECURITY DOMAIN (3 alerts)
        # ==================================================================
        {
            "alert_id": "ML-SEC-001",
            "alert_name": "ML Security Threat Detected",
            "alert_description": (
                "Fires when the security_threat_detector IsolationForest model "
                "flags any user-day as a potential threat (prediction=-1) in the "
                "last 24 hours. Business: ML-driven insider-threat early warning. "
                "Technical: queries security_threat_predictions."
            ),
            "agent_domain": "SECURITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS threat_count,
    COUNT(DISTINCT user_id) AS affected_users,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.security_threat_predictions
WHERE prediction = -1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "threat_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */4 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 14400,
            "owner": "security-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "security_threat_detector",
                "ml_type": "isolation_forest",
                "priority": "high",
            },
        },
        {
            "alert_id": "ML-SEC-002",
            "alert_name": "ML Data Exfiltration Risk",
            "alert_description": (
                "Fires when the exfiltration_detector IsolationForest model "
                "flags any user-day as a potential data exfiltration risk "
                "(prediction=-1) in the last 24 hours. Business: data loss "
                "prevention via ML. Technical: queries exfiltration_predictions."
            ),
            "agent_domain": "SECURITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS exfiltration_count,
    COUNT(DISTINCT user_id) AS affected_users,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.exfiltration_predictions
WHERE prediction = -1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "exfiltration_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */4 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 14400,
            "owner": "security-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "exfiltration_detector",
                "ml_type": "isolation_forest",
                "priority": "high",
            },
        },

        # ML-SEC-003: Privilege Escalation Risk
        {
            "alert_id": "ML-SEC-003",
            "alert_name": "ML Privilege Escalation Risk",
            "alert_description": (
                "Fires when the privilege_escalation_detector model flags "
                "unexpected permission changes (prediction=1) in the last "
                "24 hours. Business: unauthorized privilege escalation is a "
                "critical security incident; every minute of elevated access "
                "increases blast radius. Technical: queries "
                "privilege_escalation_predictions."
            ),
            "agent_domain": "SECURITY",
            "severity": "CRITICAL",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS escalation_count,
    COUNT(DISTINCT user_id) AS affected_users,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.privilege_escalation_predictions
WHERE prediction = 1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "escalation_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */4 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 14400,
            "owner": "security-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "privilege_escalation_detector",
                "ml_type": "classifier",
                "priority": "critical",
            },
        },

        # ==================================================================
        # PERFORMANCE DOMAIN (4 alerts)
        # ==================================================================
        {
            "alert_id": "ML-PERF-001",
            "alert_name": "ML Performance Regression Detected",
            "alert_description": (
                "Fires when the performance_regression_detector IsolationForest "
                "model flags any warehouse-day as degraded (prediction=-1) in "
                "the last 24 hours. Business: ML-driven performance regression "
                "early warning. Technical: queries performance_regression_predictions."
            ),
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS regression_count,
    COUNT(DISTINCT warehouse_id) AS affected_warehouses,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.performance_regression_predictions
WHERE prediction = -1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "regression_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 21600,
            "owner": "platform-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "performance_regression_detector",
                "ml_type": "isolation_forest",
                "priority": "medium",
            },
        },

        # ML-PERF-002: Warehouse Optimization Needed
        {
            "alert_id": "ML-PERF-002",
            "alert_name": "ML Warehouse Optimization Needed",
            "alert_description": (
                "Fires when the warehouse_optimizer model scores any warehouse "
                "below 0.3 (poorly optimized) in the last 24 hours. Business: "
                "identifies warehouses with suboptimal configuration that may "
                "cause degraded query performance. Technical: queries "
                "warehouse_optimizer_predictions, low score = poor optimization."
            ),
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS poorly_optimized_count,
    COUNT(DISTINCT warehouse_id) AS affected_warehouses,
    ROUND(MIN(prediction), 3) AS lowest_optimization_score
FROM {catalog}.{feature_schema}.warehouse_optimizer_predictions
WHERE prediction < 0.3
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "poorly_optimized_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 21600,
            "owner": "platform-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "warehouse_optimizer",
                "ml_type": "regression",
                "priority": "medium",
            },
        },

        # ML-PERF-003: DBR Migration Risk
        {
            "alert_id": "ML-PERF-003",
            "alert_name": "ML DBR Migration Risk",
            "alert_description": (
                "Fires when the dbr_migration_risk_scorer model flags any "
                "cluster with HIGH or CRITICAL migration risk (prediction>=2) "
                "in the last 24 hours. Business: clusters on deprecated or "
                "EOL Databricks Runtime versions will eventually stop working; "
                "this alert gives lead time to plan migration. Technical: "
                "queries dbr_migration_predictions, risk levels 0-3."
            ),
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS high_risk_count,
    COUNT(DISTINCT cluster_id) AS affected_clusters,
    MAX(prediction) AS highest_risk_level,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.dbr_migration_predictions
WHERE prediction >= 2
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "high_risk_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * 1",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 604800,
            "owner": "platform-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "dbr_migration_risk_scorer",
                "ml_type": "lightgbm_classifier",
                "priority": "medium",
            },
        },

        # ML-PERF-004: Cluster Capacity Warning
        {
            "alert_id": "ML-PERF-004",
            "alert_name": "ML Cluster Capacity Warning",
            "alert_description": (
                "Fires when the cluster_capacity_planner model predicts "
                "insufficient capacity (prediction < 0.4, indicating high "
                "under-provisioning risk) for any cluster in the last 24 "
                "hours. Business: pre-scale before jobs fail due to resource "
                "starvation. Technical: queries cluster_capacity_predictions, "
                "low score = likely capacity shortfall."
            ),
            "agent_domain": "PERFORMANCE",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS capacity_warning_count,
    COUNT(DISTINCT cluster_id) AS affected_clusters,
    ROUND(MIN(prediction), 3) AS lowest_capacity_score,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.cluster_capacity_predictions
WHERE prediction < 0.4
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "capacity_warning_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 21600,
            "owner": "platform-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "cluster_capacity_planner",
                "ml_type": "gradient_boosting",
                "priority": "medium",
            },
        },

        # ==================================================================
        # RELIABILITY DOMAIN (3 alerts)
        # ==================================================================
        {
            "alert_id": "ML-REL-001",
            "alert_name": "ML Job Failure Risk",
            "alert_description": (
                "Fires when the job_failure_predictor XGBClassifier predicts "
                "high failure risk (prediction=1) for any job in the last 24 "
                "hours. Business: proactive failure prevention via ML. "
                "Technical: queries job_failure_predictions."
            ),
            "agent_domain": "RELIABILITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS at_risk_count,
    COUNT(DISTINCT job_id) AS affected_jobs,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.job_failure_predictions
WHERE prediction = 1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "at_risk_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 21600,
            "owner": "sre-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "job_failure_predictor",
                "ml_type": "xgb_classifier",
                "priority": "medium",
            },
        },
        {
            "alert_id": "ML-REL-002",
            "alert_name": "ML SLA Breach Risk",
            "alert_description": (
                "Fires when the sla_breach_predictor XGBClassifier predicts "
                "SLA breach risk (prediction=1) for any job in the last 24 "
                "hours. Business: proactive SLA protection via ML. "
                "Technical: queries sla_breach_predictions."
            ),
            "agent_domain": "RELIABILITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS breach_risk_count,
    COUNT(DISTINCT job_id) AS affected_jobs,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.sla_breach_predictions
WHERE prediction = 1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "breach_risk_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 21600,
            "owner": "sre-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "sla_breach_predictor",
                "ml_type": "xgb_classifier",
                "priority": "medium",
            },
        },

        # ML-REL-003: Pipeline Health Degradation
        {
            "alert_id": "ML-REL-003",
            "alert_name": "ML Pipeline Health Degradation",
            "alert_description": (
                "Fires when the pipeline_health_scorer model scores any "
                "job/pipeline below 50 (Poor or Critical health) in the "
                "last 24 hours. Business: leading indicator that fires "
                "before cascading job failures; provides a holistic "
                "pipeline view unlike per-job failure alerts. Technical: "
                "queries pipeline_health_predictions, score 0-100."
            ),
            "agent_domain": "RELIABILITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS unhealthy_pipeline_count,
    COUNT(DISTINCT job_id) AS affected_jobs,
    ROUND(MIN(prediction), 1) AS lowest_health_score,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.pipeline_health_predictions
WHERE prediction < 50
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "unhealthy_pipeline_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 */6 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 21600,
            "owner": "sre-team@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "pipeline_health_scorer",
                "ml_type": "gradient_boosting",
                "priority": "high",
            },
        },

        # ==================================================================
        # QUALITY DOMAIN (2 alerts)
        # ==================================================================
        {
            "alert_id": "ML-QUAL-001",
            "alert_name": "ML Data Drift Detected",
            "alert_description": (
                "Fires when the data_drift_detector IsolationForest model "
                "flags any catalog-snapshot as drifted (prediction=-1) in the "
                "last 24 hours. Business: data quality governance via ML. "
                "Technical: queries data_drift_predictions."
            ),
            "agent_domain": "QUALITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS drift_count,
    COUNT(DISTINCT catalog_name) AS affected_catalogs,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.data_drift_predictions
WHERE prediction = -1
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "drift_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 43200,
            "owner": "data-engineering@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "data_drift_detector",
                "ml_type": "isolation_forest",
                "priority": "medium",
            },
        },
        {
            "alert_id": "ML-QUAL-002",
            "alert_name": "ML Data Freshness Degradation",
            "alert_description": (
                "Fires when the data_freshness_predictor scores any "
                "catalog-snapshot below 0.5 (stale) in the last 24 hours. "
                "Business: ETL health monitoring via ML. "
                "Technical: queries freshness_predictions, score < 0.5 = stale."
            ),
            "agent_domain": "QUALITY",
            "severity": "WARNING",
            "alert_query_template": f"""
SELECT
    COUNT(*) AS stale_count,
    COUNT(DISTINCT catalog_name) AS affected_catalogs,
    ROUND(MIN(prediction), 3) AS lowest_freshness_score,
    MAX(scored_at) AS latest_detection
FROM {catalog}.{feature_schema}.freshness_predictions
WHERE prediction < 0.5
  AND scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
""",
            "threshold_column": "stale_count",
            "threshold_operator": ">",
            "threshold_value_type": "DOUBLE",
            "threshold_value_double": 0.0,
            "empty_result_state": "OK",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",
            "schedule_timezone": "America/Los_Angeles",
            "pause_status": "PAUSED",
            "is_enabled": True,
            "notification_channels": ["default_email"],
            "notify_on_ok": False,
            "retrigger_seconds": 43200,
            "owner": "data-engineering@company.com",
            "tags": {
                "source": "ml_prediction",
                "ml_model": "data_freshness_predictor",
                "ml_type": "gradient_boosting",
                "priority": "medium",
            },
        },
    ]


def upsert_alerts(spark: SparkSession, catalog: str, gold_schema: str, alerts: List[Dict[str, Any]]) -> tuple:
    """Upsert ML alerts into alert_configurations table.

    Uses MERGE to insert new alerts and update existing ones so that
    re-running the seed fixes broken queries from prior deployments.
    """
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"

    inserted = 0
    updated = 0
    errors = 0

    for alert in alerts:
        alert_id = alert["alert_id"]

        query_escaped = alert["alert_query_template"].replace("'", "''")
        description_escaped = alert.get("alert_description", "").replace("'", "''")
        name_escaped = alert["alert_name"].replace("'", "''")

        tags = alert.get("tags", {})
        tags_sql = ", ".join([f"'{k}', '{v}'" for k, v in tags.items()])
        tags_expr = f"map({tags_sql})" if tags_sql else "map()"

        channels = alert.get("notification_channels", ["default_email"])
        channels_sql = ", ".join([f"'{c}'" for c in channels])
        channels_expr = f"array({channels_sql})"

        retrigger = alert.get("retrigger_seconds")
        retrigger_sql = str(retrigger) if retrigger is not None else "NULL"

        threshold_double = alert.get("threshold_value_double")
        threshold_double_sql = str(threshold_double) if threshold_double is not None else "NULL"

        merge_sql = f"""
MERGE INTO {cfg_table} AS target
USING (SELECT '{alert_id}' AS alert_id) AS source
ON target.alert_id = source.alert_id
WHEN MATCHED THEN UPDATE SET
    alert_name = '{name_escaped}',
    alert_description = '{description_escaped}',
    agent_domain = '{alert["agent_domain"]}',
    severity = '{alert["severity"]}',
    alert_query_template = '{query_escaped}',
    threshold_column = '{alert["threshold_column"]}',
    threshold_operator = '{alert["threshold_operator"]}',
    threshold_value_type = '{alert["threshold_value_type"]}',
    threshold_value_double = {threshold_double_sql},
    empty_result_state = '{alert["empty_result_state"]}',
    aggregation_type = '{alert.get("aggregation_type", "NONE")}',
    schedule_cron = '{alert["schedule_cron"]}',
    schedule_timezone = '{alert["schedule_timezone"]}',
    owner = '{alert["owner"]}',
    tags = {tags_expr}
WHEN NOT MATCHED THEN INSERT (
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
    '{alert_id}',
    '{name_escaped}',
    '{description_escaped}',
    '{alert["agent_domain"]}',
    '{alert["severity"]}',
    '{query_escaped}',
    'ML_PREDICTION',
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
    'seed_ml_alerts',
    CURRENT_TIMESTAMP(),
    {tags_expr}
)
"""
        try:
            result = spark.sql(merge_sql)
            metrics = result.first()
            if metrics and metrics["num_inserted_rows"] > 0:
                print(f"  INSERT: {alert_id} - {alert['alert_name']}")
                inserted += 1
            else:
                print(f"  UPDATE: {alert_id} - {alert['alert_name']}")
                updated += 1
        except Exception as e:
            print(f"  ERROR: {alert_id} - {str(e)[:200]}")
            errors += 1

    return inserted, updated, errors


def main() -> None:
    """Main entry point."""
    dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
    dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
    dbutils.widgets.text("feature_schema", "system_gold_ml", "ML Feature Schema")

    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()

    print("=" * 80)
    print("SEED ML-DRIVEN ALERTS")
    print("=" * 80)
    print(f"Config table: {catalog}.{gold_schema}.alert_configurations")
    print(f"Prediction tables in: {catalog}.{feature_schema}")
    print("")

    alerts = get_ml_alerts(catalog, gold_schema, feature_schema)
    print(f"Total ML alerts defined: {len(alerts)}")
    print("")

    domains = {}
    for a in alerts:
        d = a["agent_domain"]
        domains[d] = domains.get(d, 0) + 1

    print("ML alert count by domain:")
    for domain, domain_count in sorted(domains.items()):
        print(f"  {domain}: {domain_count}")
    print("")

    print("Upserting ML alerts:")
    inserted, updated, errors = upsert_alerts(spark, catalog, gold_schema, alerts)

    print("")
    print("=" * 80)
    print(f"✓ Inserted {inserted} new ML alerts")
    print(f"  Updated {updated} existing ML alerts")
    if errors:
        print(f"  ❌ {errors} errors")
    print("=" * 80)

    if errors:
        raise RuntimeError(f"Failed to upsert {errors} ML alert(s)")

    dbutils.notebook.exit(f"SUCCESS: {inserted} inserted, {updated} updated")


if __name__ == "__main__":
    main()
