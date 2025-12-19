# Databricks notebook source
"""
Security Access Monitor Configuration
=====================================

Lakehouse Monitor for fact_audit_logs table.
Tracks user activity, permission changes, and security events.
"""

# COMMAND ----------

from monitor_utils import (
    check_monitoring_available,
    delete_monitor_if_exists,
    create_time_series_monitor,
    create_aggregate_metric,
    create_derived_metric,
    create_drift_metric,
    MONITORING_AVAILABLE
)

if MONITORING_AVAILABLE:
    from databricks.sdk import WorkspaceClient

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")

# COMMAND ----------

def get_security_custom_metrics():
    """Define custom metrics for security monitoring."""
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Event volume metrics
        create_aggregate_metric(
            "total_events",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_users",
            "COUNT(DISTINCT user_identity_email)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_services",
            "COUNT(DISTINCT service_name)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_actions",
            "COUNT(DISTINCT action_name)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_ips",
            "COUNT(DISTINCT source_ip_address)",
            "LONG"
        ),

        # Sensitive action metrics
        create_aggregate_metric(
            "sensitive_action_count",
            "SUM(CASE WHEN is_sensitive_action = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "failed_action_count",
            "SUM(CASE WHEN is_failed_action = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Permission change metrics
        create_aggregate_metric(
            "permission_change_count",
            "SUM(CASE WHEN action_name LIKE '%grant%' OR action_name LIKE '%revoke%' OR action_name LIKE '%Permission%' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "secret_access_count",
            "SUM(CASE WHEN action_name LIKE '%Secret%' OR action_name LIKE '%secret%' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Audit level breakdown
        create_aggregate_metric(
            "account_level_events",
            "SUM(CASE WHEN audit_level = 'ACCOUNT_LEVEL' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "workspace_level_events",
            "SUM(CASE WHEN audit_level = 'WORKSPACE_LEVEL' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Error tracking
        create_aggregate_metric(
            "client_error_count",
            "SUM(CASE WHEN response_status_code >= 400 AND response_status_code < 500 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "server_error_count",
            "SUM(CASE WHEN response_status_code >= 500 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "unauthorized_count",
            "SUM(CASE WHEN response_status_code = 401 OR response_status_code = 403 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Off-hours activity (security concern)
        create_aggregate_metric(
            "off_hours_events",
            "SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "weekend_events",
            "SUM(CASE WHEN DAYOFWEEK(event_date) IN (1, 7) THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # ==========================================
        # AUDIT LOGS REPO METRICS (NEW)
        # Source: system-tables-audit-logs GitHub repo - User type classification
        # ==========================================

        # Human user events (excludes system/service accounts)
        create_aggregate_metric(
            "human_user_events",
            """SUM(CASE
                WHEN user_identity_email LIKE '%@%'
                 AND user_identity_email NOT LIKE 'System-%'
                 AND user_identity_email NOT LIKE '%spn@%'
                 AND user_identity_email NOT LIKE '%iam.gserviceaccount.com'
                 AND user_identity_email NOT LIKE 'DBX_%'
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),
        # Service principal events
        create_aggregate_metric(
            "service_principal_events",
            """SUM(CASE
                WHEN user_identity_email LIKE '%spn@%'
                  OR user_identity_email LIKE '%iam.gserviceaccount.com'
                  OR (user_identity_email NOT LIKE '%@%'
                      AND user_identity_email NOT LIKE 'System-%'
                      AND user_identity_email NOT LIKE 'DBX_%')
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),
        # System account events
        create_aggregate_metric(
            "system_account_events",
            """SUM(CASE
                WHEN user_identity_email LIKE 'System-%'
                  OR user_identity_email LIKE 'DBX_%'
                  OR user_identity_email IN ('Unity Catalog', 'Delta Sharing', 'Catalog', 'Schema')
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),
        # Human user off-hours (more meaningful for security)
        create_aggregate_metric(
            "human_off_hours_events",
            """SUM(CASE
                WHEN (HOUR(event_time) < 7 OR HOUR(event_time) >= 19)
                 AND user_identity_email LIKE '%@%'
                 AND user_identity_email NOT LIKE 'System-%'
                 AND user_identity_email NOT LIKE '%spn@%'
                 AND user_identity_email NOT LIKE '%iam.gserviceaccount.com'
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),
        # Distinct human users
        create_aggregate_metric(
            "distinct_human_users",
            """COUNT(DISTINCT CASE
                WHEN user_identity_email LIKE '%@%'
                 AND user_identity_email NOT LIKE 'System-%'
                 AND user_identity_email NOT LIKE '%spn@%'
                 AND user_identity_email NOT LIKE '%iam.gserviceaccount.com'
                THEN user_identity_email
            END)""",
            "LONG"
        ),
        # Distinct service principals
        create_aggregate_metric(
            "distinct_service_principals",
            """COUNT(DISTINCT CASE
                WHEN user_identity_email LIKE '%spn@%'
                  OR user_identity_email LIKE '%iam.gserviceaccount.com'
                THEN user_identity_email
            END)""",
            "LONG"
        ),

        # Service breakdown (top services)
        create_aggregate_metric(
            "clusters_service_events",
            "SUM(CASE WHEN service_name = 'clusters' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "sql_service_events",
            "SUM(CASE WHEN service_name = 'databrickssql' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "workspace_service_events",
            "SUM(CASE WHEN service_name = 'workspace' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "unitycatalog_service_events",
            "SUM(CASE WHEN service_name = 'unityCatalog' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "sensitive_action_rate",
            "sensitive_action_count * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "failure_rate",
            "failed_action_count * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "off_hours_rate",
            "off_hours_events * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "weekend_rate",
            "weekend_events * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "unauthorized_rate",
            "unauthorized_count * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "avg_events_per_user",
            "total_events * 1.0 / NULLIF(distinct_users, 0)"
        ),
        create_derived_metric(
            "account_level_ratio",
            "account_level_events * 100.0 / NULLIF(total_events, 0)"
        ),

        # Audit Logs Repo derived metrics (NEW)
        create_derived_metric(
            "human_user_ratio",
            "human_user_events * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "service_principal_ratio",
            "service_principal_events * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "system_account_ratio",
            "system_account_events * 100.0 / NULLIF(total_events, 0)"
        ),
        create_derived_metric(
            "human_off_hours_rate",
            "human_off_hours_events * 100.0 / NULLIF(human_user_events, 0)"
        ),
        create_derived_metric(
            "avg_events_per_human",
            "human_user_events * 1.0 / NULLIF(distinct_human_users, 0)"
        ),
        create_derived_metric(
            "avg_events_per_sp",
            "service_principal_events * 1.0 / NULLIF(distinct_service_principals, 0)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "event_volume_drift_pct",
            "(({{current_df}}.total_events - {{base_df}}.total_events) / NULLIF({{base_df}}.total_events, 0)) * 100"
        ),
        create_drift_metric(
            "sensitive_action_drift",
            "{{current_df}}.sensitive_action_count - {{base_df}}.sensitive_action_count"
        ),
        create_drift_metric(
            "failure_rate_drift",
            "{{current_df}}.failure_rate - {{base_df}}.failure_rate"
        ),
        create_drift_metric(
            "off_hours_drift",
            "{{current_df}}.off_hours_rate - {{base_df}}.off_hours_rate"
        ),
        create_drift_metric(
            "user_count_drift",
            "{{current_df}}.distinct_users - {{base_df}}.distinct_users"
        ),

        # Audit Logs Repo drift metrics (NEW)
        create_drift_metric(
            "human_off_hours_drift",
            "{{current_df}}.human_off_hours_rate - {{base_df}}.human_off_hours_rate"
        ),
        create_drift_metric(
            "human_user_count_drift",
            "{{current_df}}.distinct_human_users - {{base_df}}.distinct_human_users"
        ),
        create_drift_metric(
            "service_principal_volume_drift_pct",
            "(({{current_df}}.service_principal_events - {{base_df}}.service_principal_events) / NULLIF({{base_df}}.service_principal_events, 0)) * 100"
        ),
    ]


def create_security_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """Create the security monitor for fact_audit_logs."""
    table_name = f"{catalog}.{gold_schema}.fact_audit_logs"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    # Create monitor
    monitor = create_time_series_monitor(
        workspace_client=workspace_client,
        table_name=table_name,
        timestamp_col="event_date",
        granularities=["1 day"],
        custom_metrics=get_security_custom_metrics(),
        slicing_exprs=["workspace_id", "service_name", "audit_level"],
        schedule_cron="0 0 6 * * ?",  # Daily at 6 AM UTC
    )

    return monitor

# COMMAND ----------

def main():
    """Main entry point."""
    if not check_monitoring_available():
        print("Lakehouse Monitoring not available - skipping")
        dbutils.notebook.exit("SKIPPED: SDK not available")
        return

    workspace_client = WorkspaceClient()

    try:
        monitor = create_security_monitor(workspace_client, catalog, gold_schema, spark)
        if monitor:
            dbutils.notebook.exit("SUCCESS: Security monitor created")
        else:
            dbutils.notebook.exit("SKIPPED: Monitor already exists")
    except Exception as e:
        dbutils.notebook.exit(f"FAILED: {str(e)}")

# COMMAND ----------

if __name__ == "__main__":
    main()
