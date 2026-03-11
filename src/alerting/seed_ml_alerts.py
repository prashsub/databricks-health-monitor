# Databricks notebook source
"""
ML-Driven Alert Seeding
=======================

Seeds conservative ML-driven alerts into alert_configurations.
These alerts query ML prediction tables in the feature_schema
and fire only when models have flagged anomalies or high-risk items.

ALERT PHILOSOPHY:
-----------------
- Conservative: only anomaly-detection (IsolationForest) and
  high-signal classifiers are included.
- All alerts start PAUSED and at WARNING severity.
- Each query checks for recent predictions (last 24h) to avoid
  stale detections.
- Tagged with source=ml_prediction for easy filtering.

ML ALERT ID CONVENTION:
-----------------------
    ML-{DOMAIN}-NNN

    Examples:
    - ML-COST-001: Cost Anomaly (IsolationForest)
    - ML-SEC-001: Security Threat (IsolationForest)
    - ML-REL-001: Job Failure Risk (XGBClassifier)

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
        # COST DOMAIN (1 alert)
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

        # ==================================================================
        # SECURITY DOMAIN (2 alerts)
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

        # ==================================================================
        # PERFORMANCE DOMAIN (2 alerts)
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

        # ==================================================================
        # RELIABILITY DOMAIN (2 alerts)
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


def insert_alerts(spark: SparkSession, catalog: str, gold_schema: str, alerts: List[Dict[str, Any]]) -> int:
    """Insert alerts into alert_configurations table (skip if exists)."""
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"

    inserted = 0
    skipped = 0

    for alert in alerts:
        alert_id = alert["alert_id"]

        exists = spark.sql(f"""
            SELECT 1 FROM {cfg_table} WHERE alert_id = '{alert_id}'
        """).count() > 0

        if exists:
            print(f"  SKIP: {alert_id} (already exists)")
            skipped += 1
            continue

        query_escaped = alert["alert_query_template"].replace("'", "''")
        description_escaped = alert.get("alert_description", "").replace("'", "''")

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
            spark.sql(insert_sql)
            print(f"  INSERT: {alert_id} - {alert['alert_name']}")
            inserted += 1
        except Exception as e:
            print(f"  ERROR: {alert_id} - {str(e)[:200]}")

    return inserted


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

    print("Inserting ML alerts:")
    inserted = insert_alerts(spark, catalog, gold_schema, alerts)

    print("")
    print("=" * 80)
    print(f"Inserted {inserted} new ML alerts")
    print(f"  Skipped {len(alerts) - inserted} existing alerts")
    print("=" * 80)

    dbutils.notebook.exit(f"SUCCESS: Inserted {inserted} ML alerts")


if __name__ == "__main__":
    main()
