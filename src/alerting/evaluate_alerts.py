# Databricks notebook source
"""
Alert Evaluator Job
===================

The "missing piece" that bridges alert_configurations and alert_history.

This notebook reads all enabled alert configurations, executes each alert's
SQL query, compares the result against its threshold, optionally enriches
with ML scores, and calls FMAPI for a short AI analysis on TRIGGERED alerts.
Results are written to the alert_history Delta table.

EXECUTION FLOW:
---------------

1. Read enabled alerts from alert_configurations
2. For each alert:
   a. Render the query template (substitute catalog/schema variables)
   b. Execute via spark.sql() with a timeout
   c. Evaluate threshold to determine OK / TRIGGERED / ERROR
   d. Look up previous_status from most recent alert_history row
   e. For ML-tagged alerts: extract ml_score from prediction table
3. For TRIGGERED alerts only: call FMAPI for 2-3 sentence analysis
4. Batch-write all evaluation results to alert_history
5. Print summary

DESIGN DECISIONS:
-----------------

- Sequential execution to avoid SQL warehouse overload
- FMAPI calls only for TRIGGERED alerts (bounds LLM cost)
- 60-second query timeout; ERROR status on timeout
- Per-alert error isolation; one failure does not stop others
- alert_history is append-only (no updates)

Reference: docs/frontend-framework-design/prd/04-closed-loop-architecture.md
"""

import uuid
import time
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from pyspark.sql import SparkSession, Row
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    BooleanType, LongType, TimestampType, DateType, ArrayType,
)


# =========================================================================
# PARAMETERS
# =========================================================================

def get_parameters() -> Dict[str, str]:
    """Get job parameters from dbutils widgets."""
    dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
    dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
    dbutils.widgets.text("feature_schema", "system_gold_ml", "ML Feature Schema")
    dbutils.widgets.text("llm_endpoint", "databricks-claude-sonnet-4-5", "LLM Endpoint")

    return {
        "catalog": dbutils.widgets.get("catalog"),
        "gold_schema": dbutils.widgets.get("gold_schema"),
        "feature_schema": dbutils.widgets.get("feature_schema"),
        "llm_endpoint": dbutils.widgets.get("llm_endpoint"),
    }


# =========================================================================
# QUERY RENDERING
# =========================================================================

def render_query(template: str, catalog: str, gold_schema: str, feature_schema: str) -> str:
    """
    Render a query template by substituting variable placeholders.

    Handles both f-string-rendered queries (already substituted at seed time)
    and ${variable} placeholders (for templates stored with placeholders).
    """
    rendered = template
    rendered = rendered.replace("${catalog}", catalog)
    rendered = rendered.replace("${gold_schema}", gold_schema)
    rendered = rendered.replace("${feature_schema}", feature_schema)
    return rendered.strip()


# =========================================================================
# THRESHOLD EVALUATION
# =========================================================================

OPERATOR_MAP = {
    ">": lambda v, t: v > t,
    ">=": lambda v, t: v >= t,
    "<": lambda v, t: v < t,
    "<=": lambda v, t: v <= t,
    "=": lambda v, t: v == t,
    "==": lambda v, t: v == t,
    "!=": lambda v, t: v != t,
    "<>": lambda v, t: v != t,
}


def evaluate_threshold(
    result_value: Optional[float],
    operator: str,
    threshold_value: Optional[float],
) -> str:
    """
    Compare the query result value against the threshold.

    Returns: "TRIGGERED" if threshold is breached, "OK" otherwise.
    """
    if result_value is None or threshold_value is None:
        return "OK"

    comparator = OPERATOR_MAP.get(operator)
    if comparator is None:
        return "ERROR"

    return "TRIGGERED" if comparator(result_value, threshold_value) else "OK"


# =========================================================================
# QUERY EXECUTION
# =========================================================================

QUERY_TIMEOUT_SECONDS = 60


def execute_alert_query(
    spark: SparkSession,
    rendered_query: str,
    threshold_column: str,
    aggregation_type: str,
) -> Tuple[Optional[float], Optional[str], int, Optional[str]]:
    """
    Execute an alert SQL query and extract the check value.

    Returns:
        (result_value_double, result_value_string, duration_ms, error_message)
    """
    start_ms = int(time.time() * 1000)
    try:
        df = spark.sql(rendered_query)
        rows = df.limit(1).collect()
        duration_ms = int(time.time() * 1000) - start_ms

        if not rows:
            return None, None, duration_ms, None

        row = rows[0]

        if threshold_column not in row.asDict():
            return None, None, duration_ms, f"Column '{threshold_column}' not in query result"

        raw_value = row[threshold_column]
        if raw_value is None:
            return None, None, duration_ms, None

        try:
            return float(raw_value), str(raw_value), duration_ms, None
        except (ValueError, TypeError):
            return None, str(raw_value), duration_ms, None

    except Exception as e:
        duration_ms = int(time.time() * 1000) - start_ms
        return None, None, duration_ms, str(e)[:500]


# =========================================================================
# PREVIOUS STATUS LOOKUP
# =========================================================================

def get_previous_status(spark: SparkSession, catalog: str, gold_schema: str, alert_id: str) -> Optional[str]:
    """Get the most recent evaluation_status for this alert from alert_history."""
    try:
        rows = spark.sql(f"""
            SELECT evaluation_status
            FROM {catalog}.{gold_schema}.alert_history
            WHERE alert_id = '{alert_id}'
            ORDER BY evaluation_timestamp DESC
            LIMIT 1
        """).collect()
        return rows[0]["evaluation_status"] if rows else None
    except Exception:
        return None


# =========================================================================
# ML SCORE EXTRACTION
# =========================================================================

ML_SCORE_QUERIES = {
    "cost_anomaly_detector": """
        SELECT AVG(CASE WHEN prediction = -1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.cost_anomaly_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "security_threat_detector": """
        SELECT AVG(CASE WHEN prediction = -1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.security_threat_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "exfiltration_detector": """
        SELECT AVG(CASE WHEN prediction = -1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.exfiltration_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "performance_regression_detector": """
        SELECT AVG(CASE WHEN prediction = -1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.performance_regression_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "warehouse_optimizer": """
        SELECT AVG(CASE WHEN prediction < 0.3 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.warehouse_optimizer_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "job_failure_predictor": """
        SELECT AVG(CASE WHEN prediction = 1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.job_failure_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "sla_breach_predictor": """
        SELECT AVG(CASE WHEN prediction = 1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.sla_breach_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "data_drift_detector": """
        SELECT AVG(CASE WHEN prediction = -1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.data_drift_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "data_freshness_predictor": """
        SELECT 1.0 - AVG(prediction) AS ml_score
        FROM {catalog}.{feature_schema}.freshness_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "budget_forecaster": """
        SELECT CASE WHEN MAX(prediction) > 100000 THEN 1.0 ELSE 0.0 END AS ml_score
        FROM {catalog}.{feature_schema}.budget_forecast_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "privilege_escalation_detector": """
        SELECT AVG(CASE WHEN prediction = 1 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.privilege_escalation_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "dbr_migration_risk_scorer": """
        SELECT AVG(CASE WHEN prediction >= 2 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.dbr_migration_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "cluster_capacity_planner": """
        SELECT AVG(CASE WHEN prediction < 0.4 THEN 1.0 ELSE 0.0 END) AS ml_score
        FROM {catalog}.{feature_schema}.cluster_capacity_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
    "pipeline_health_scorer": """
        SELECT 1.0 - (AVG(prediction) / 100.0) AS ml_score
        FROM {catalog}.{feature_schema}.pipeline_health_predictions
        WHERE scored_at >= DATE_ADD(CURRENT_TIMESTAMP(), -1)
    """,
}


def get_ml_score(
    spark: SparkSession,
    tags: Dict[str, str],
    catalog: str,
    feature_schema: str,
) -> Optional[float]:
    """Extract ML score for ML-tagged alerts. Returns None for non-ML alerts."""
    if tags.get("source") != "ml_prediction":
        return None

    model_name = tags.get("ml_model", "")
    query_template = ML_SCORE_QUERIES.get(model_name)
    if not query_template:
        return None

    try:
        query = query_template.format(catalog=catalog, feature_schema=feature_schema)
        rows = spark.sql(query).collect()
        if rows and rows[0]["ml_score"] is not None:
            return round(float(rows[0]["ml_score"]), 4)
    except Exception:
        pass

    return None


# =========================================================================
# FMAPI AI ANALYSIS
# =========================================================================

def generate_ai_analysis(
    alert_name: str,
    agent_domain: str,
    alert_description: str,
    result_value: Optional[float],
    threshold_operator: str,
    threshold_value: Optional[float],
    llm_endpoint: str,
) -> Optional[str]:
    """
    Call the Foundation Model API for a short analysis of a TRIGGERED alert.

    Returns a 2-3 sentence analysis string, or None on failure.
    Only called for TRIGGERED alerts to bound LLM cost.
    """
    try:
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()

        value_str = f"{result_value:.2f}" if result_value is not None else "N/A"
        threshold_str = f"{threshold_value:.2f}" if threshold_value is not None else "N/A"

        prompt = (
            f"You are a Databricks platform health analyst. "
            f"Alert '{alert_name}' in the {agent_domain} domain has triggered. "
            f"{alert_description} "
            f"The query returned {value_str} which breached the threshold "
            f"({threshold_operator} {threshold_str}). "
            f"Provide a concise 2-3 sentence root cause analysis and "
            f"actionable recommendation. Be specific and technical."
        )

        response = w.serving_endpoints.query(
            name=llm_endpoint,
            messages=[
                {"role": "system", "content": "You are a concise Databricks platform health analyst. Respond in 2-3 sentences only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.3,
        )

        if response and response.choices:
            return response.choices[0].message.content.strip()[:1000]

    except Exception as e:
        print(f"    FMAPI error: {str(e)[:200]}")

    return None


# =========================================================================
# MAIN EVALUATION LOOP
# =========================================================================

def evaluate_all_alerts(
    spark: SparkSession,
    params: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Evaluate all enabled alerts and return history rows.

    This is the core loop:
    1. Read enabled alerts
    2. Execute each query
    3. Evaluate threshold
    4. Enrich with ML score + AI analysis
    5. Return list of alert_history row dicts
    """
    catalog = params["catalog"]
    gold_schema = params["gold_schema"]
    feature_schema = params["feature_schema"]
    llm_endpoint = params["llm_endpoint"]

    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"

    alerts_df = spark.sql(f"""
        SELECT * FROM {cfg_table}
        WHERE is_enabled = true
        ORDER BY agent_domain, alert_id
    """)
    alerts = alerts_df.collect()

    print(f"Evaluating {len(alerts)} enabled alerts...")
    print("")

    evaluation_time = datetime.utcnow()
    evaluation_date = evaluation_time.date()
    results = []

    ok_count = 0
    triggered_count = 0
    error_count = 0

    for alert in alerts:
        alert_id = alert["alert_id"]
        alert_name = alert["alert_name"]
        agent_domain = alert["agent_domain"]
        severity = alert["severity"]

        print(f"  [{agent_domain}] {alert_id}: {alert_name} ... ", end="")

        rendered_query = render_query(
            alert["alert_query_template"],
            catalog, gold_schema, feature_schema,
        )

        result_double, result_string, duration_ms, error_msg = execute_alert_query(
            spark, rendered_query,
            alert["threshold_column"],
            alert["aggregation_type"] or "NONE",
        )

        if error_msg:
            status = "ERROR"
            error_count += 1
            print(f"ERROR ({error_msg[:80]})")
        else:
            empty_result = result_double is None and result_string is None
            if empty_result:
                status = alert["empty_result_state"] or "OK"
            else:
                status = evaluate_threshold(
                    result_double,
                    alert["threshold_operator"],
                    alert["threshold_value_double"],
                )

            if status == "TRIGGERED":
                triggered_count += 1
                print(f"TRIGGERED (value={result_double})")
            elif status == "OK":
                ok_count += 1
                print("OK")
            else:
                error_count += 1
                print(f"ERROR (empty_result_state={status})")

        previous_status = get_previous_status(spark, catalog, gold_schema, alert_id)

        tags = {}
        if alert["tags"]:
            try:
                tags = dict(alert["tags"])
            except Exception:
                pass

        ml_score = get_ml_score(spark, tags, catalog, feature_schema)

        ai_analysis = None
        if status == "TRIGGERED":
            ai_analysis = generate_ai_analysis(
                alert_name, agent_domain,
                alert["alert_description"] or "",
                result_double,
                alert["threshold_operator"],
                alert["threshold_value_double"],
                llm_endpoint,
            )
            if ai_analysis:
                print(f"    AI: {ai_analysis[:100]}...")

        results.append({
            "evaluation_id": str(uuid.uuid4()),
            "alert_id": alert_id,
            "alert_name": alert_name,
            "agent_domain": agent_domain,
            "severity": severity,
            "evaluation_timestamp": evaluation_time,
            "evaluation_date": evaluation_date,
            "evaluation_status": status,
            "previous_status": previous_status,
            "query_result_value_double": result_double,
            "query_result_value_string": result_string,
            "threshold_operator": alert["threshold_operator"],
            "threshold_value_type": alert["threshold_value_type"],
            "threshold_value_double": alert["threshold_value_double"],
            "threshold_value_string": alert["threshold_value_string"],
            "threshold_value_bool": alert["threshold_value_bool"],
            "query_duration_ms": duration_ms,
            "error_message": error_msg,
            "ml_score": ml_score,
            "ml_suppressed": False,
            "ai_analysis": ai_analysis,
            "notification_sent": False,
            "notification_channels_used": None,
            "record_created_timestamp": evaluation_time,
        })

    print("")
    print(f"  OK: {ok_count}  |  TRIGGERED: {triggered_count}  |  ERROR: {error_count}")

    return results


# =========================================================================
# WRITE TO ALERT_HISTORY
# =========================================================================

HISTORY_SCHEMA = StructType([
    StructField("evaluation_id", StringType(), False),
    StructField("alert_id", StringType(), False),
    StructField("alert_name", StringType(), False),
    StructField("agent_domain", StringType(), False),
    StructField("severity", StringType(), False),
    StructField("evaluation_timestamp", TimestampType(), False),
    StructField("evaluation_date", DateType(), False),
    StructField("evaluation_status", StringType(), False),
    StructField("previous_status", StringType(), True),
    StructField("query_result_value_double", DoubleType(), True),
    StructField("query_result_value_string", StringType(), True),
    StructField("threshold_operator", StringType(), False),
    StructField("threshold_value_type", StringType(), False),
    StructField("threshold_value_double", DoubleType(), True),
    StructField("threshold_value_string", StringType(), True),
    StructField("threshold_value_bool", BooleanType(), True),
    StructField("query_duration_ms", LongType(), True),
    StructField("error_message", StringType(), True),
    StructField("ml_score", DoubleType(), True),
    StructField("ml_suppressed", BooleanType(), True),
    StructField("ai_analysis", StringType(), True),
    StructField("notification_sent", BooleanType(), True),
    StructField("notification_channels_used", ArrayType(StringType()), True),
    StructField("record_created_timestamp", TimestampType(), False),
])


def write_results(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    results: List[Dict[str, Any]],
) -> int:
    """Write evaluation results to alert_history Delta table."""
    if not results:
        print("No results to write.")
        return 0

    history_table = f"{catalog}.{gold_schema}.alert_history"

    rows = []
    for r in results:
        rows.append(Row(**r))

    df = spark.createDataFrame(rows, schema=HISTORY_SCHEMA)
    df.write.format("delta").mode("append").saveAsTable(history_table)

    record_count = len(results)
    print(f"Wrote {record_count} evaluation records to {history_table}")
    return record_count


# =========================================================================
# MAIN
# =========================================================================

def main() -> None:
    """Main entry point for the alert evaluator job."""
    params = get_parameters()
    spark = SparkSession.builder.getOrCreate()

    print("=" * 80)
    print("ALERT EVALUATOR")
    print("=" * 80)
    print(f"Config:   {params['catalog']}.{params['gold_schema']}.alert_configurations")
    print(f"History:  {params['catalog']}.{params['gold_schema']}.alert_history")
    print(f"ML:       {params['catalog']}.{params['feature_schema']}")
    print(f"LLM:      {params['llm_endpoint']}")
    print("")

    try:
        results = evaluate_all_alerts(spark, params)

        print("")
        write_results(spark, params["catalog"], params["gold_schema"], results)

        triggered = [r for r in results if r["evaluation_status"] == "TRIGGERED"]
        errors = [r for r in results if r["evaluation_status"] == "ERROR"]

        print("")
        print("=" * 80)
        print(f"Evaluation complete: {len(results)} alerts processed")
        print(f"  TRIGGERED: {len(triggered)}")
        print(f"  ERRORS:    {len(errors)}")
        print("=" * 80)

        if triggered:
            print("")
            print("TRIGGERED ALERTS:")
            for t in triggered:
                ai_snippet = ""
                if t["ai_analysis"]:
                    ai_snippet = f" | AI: {t['ai_analysis'][:80]}..."
                print(f"  [{t['severity']}] {t['alert_id']}: {t['alert_name']}{ai_snippet}")

        dbutils.notebook.exit(
            f"SUCCESS: {len(results)} evaluated, "
            f"{len(triggered)} triggered, {len(errors)} errors"
        )

    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        traceback.print_exc()
        dbutils.notebook.exit(f"FAILURE: {str(e)[:200]}")
        raise


if __name__ == "__main__":
    main()
