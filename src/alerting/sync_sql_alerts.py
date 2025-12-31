# Databricks notebook source
# MAGIC %pip install --upgrade databricks-sdk>=0.40.0 --quiet

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

"""
SQL Alert Sync Engine (Databricks SQL Alerts V2)
=================================================

Reads {catalog}.{gold_schema}.alert_configurations and syncs enabled rows into
Databricks SQL Alerts using the Databricks SDK.

SDK Reference: https://databricks-sdk-py.readthedocs.io/en/latest/workspace/sql/alerts_v2.html

Features:
- Creates new alerts for enabled configs without a deployed alert
- Updates existing alerts when config changes (uses update_mask for PATCH)
- Deletes alerts that are disabled in config (optional, controlled by delete_disabled)
- Tracks sync status back to the config table
- Dry-run mode for validation
- Handles ResourceAlreadyExists by refreshing and updating existing alerts
- Metrics collection for observability

Note:
- SQL alerts do NOT support query parameters, so queries must be fully qualified.
  We render ${catalog} and ${gold_schema} placeholders before deploying.
- Requires databricks-sdk>=0.40.0 for AlertV2 types (installed via %pip at runtime)
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import AlertV2

from pyspark.sql import SparkSession  # type: ignore[import]
from pyspark.sql.functions import col  # type: ignore[import]

# Import from sibling modules (pure Python, no dbutils)
from alerting_config import (
    AlertConfigRow,
    build_subscriptions,
    build_threshold_value,
    map_operator_to_comparison_operator,
    normalize_aggregation,
    render_query_template,
)
from alerting_metrics import (
    AlertSyncMetrics,
    log_sync_metrics_spark,
    print_metrics_summary,
)


# ==============================================================================
# Constants
# ==============================================================================

DEFAULT_PARALLEL_WORKERS = 5


# ==============================================================================
# Parameter Handling
# ==============================================================================


def get_parameters() -> Tuple[str, str, str, bool, bool, bool, int]:
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")  # type: ignore[name-defined]
    gold_schema = dbutils.widgets.get("gold_schema")  # type: ignore[name-defined]
    warehouse_id = dbutils.widgets.get("warehouse_id")  # type: ignore[name-defined]
    dry_run = dbutils.widgets.get("dry_run").lower() == "true"  # type: ignore[name-defined]
    delete_disabled = dbutils.widgets.get("delete_disabled").lower() == "true"  # type: ignore[name-defined]
    enable_parallel = dbutils.widgets.get("enable_parallel").lower() == "true"  # type: ignore[name-defined]
    parallel_workers = int(dbutils.widgets.get("parallel_workers") or DEFAULT_PARALLEL_WORKERS)  # type: ignore[name-defined]
    return catalog, gold_schema, warehouse_id, dry_run, delete_disabled, enable_parallel, parallel_workers


# ==============================================================================
# SDK Helpers
# ==============================================================================


def list_existing_alerts(ws: WorkspaceClient) -> Dict[str, AlertV2]:
    """
    List existing alerts and return dict keyed by display_name.
    
    SDK handles pagination automatically via iterator.
    """
    existing: Dict[str, AlertV2] = {}
    
    try:
        for alert in ws.alerts_v2.list_alerts():
            if alert.display_name:
                existing[alert.display_name] = alert
    except Exception as e:
        print(f"Warning: Could not list existing alerts: {e}")
    
    return existing


def build_alert_v2(
    cfg: AlertConfigRow,
    *,
    catalog: str,
    gold_schema: str,
    warehouse_id: str,
    subscriptions: List[Dict[str, str]],
) -> AlertV2:
    """Build an AlertV2 object from an AlertConfigRow."""
    display_name = f"[{cfg.severity}] {cfg.alert_name}"
    query_text = render_query_template(
        cfg.alert_query_template, catalog=catalog, gold_schema=gold_schema
    )

    comparison_operator = map_operator_to_comparison_operator(cfg.threshold_operator)
    aggregation = normalize_aggregation(cfg.aggregation_type)
    threshold_value = build_threshold_value(
        cfg.threshold_value_type,
        cfg.threshold_value_double,
        cfg.threshold_value_string,
        cfg.threshold_value_bool,
    )

    # Build source/operand dict
    source: Dict[str, Any] = {"name": cfg.threshold_column}
    if aggregation:
        source["aggregation"] = aggregation

    # Build notification subscriptions
    notification_subscriptions = []
    for sub in subscriptions:
        if "user_email" in sub:
            notification_subscriptions.append({"user_email": sub["user_email"]})
        elif "destination_id" in sub:
            notification_subscriptions.append({"destination_id": sub["destination_id"]})

    # Build notification block
    notification: Dict[str, Any] = {
        "notify_on_ok": cfg.notify_on_ok,
    }
    if notification_subscriptions:
        notification["subscriptions"] = notification_subscriptions
    if cfg.retrigger_seconds is not None:
        notification["retrigger_seconds"] = int(cfg.retrigger_seconds)

    # Build evaluation/condition block
    evaluation = {
        "source": source,
        "comparison_operator": comparison_operator,
        "threshold": {"value": threshold_value},
        "empty_result_state": cfg.empty_result_state,
        "notification": notification,
    }

    # Build schedule block
    schedule = {
        "quartz_cron_schedule": cfg.schedule_cron,
        "timezone_id": cfg.schedule_timezone,
        "pause_status": cfg.pause_status,
    }

    # Build AlertV2 object using from_dict pattern
    alert_dict = {
        "display_name": display_name,
        "warehouse_id": warehouse_id,
        "query_text": query_text,
        "schedule": schedule,
        "evaluation": evaluation,
    }

    # Add custom templates if enabled
    if cfg.use_custom_template:
        if cfg.custom_subject_template:
            alert_dict["custom_summary"] = cfg.custom_subject_template
        if cfg.custom_body_template:
            alert_dict["custom_description"] = cfg.custom_body_template

    return AlertV2.from_dict(alert_dict)


# ==============================================================================
# Sync Status Tracking
# ==============================================================================


def update_sync_status(
    spark: SparkSession,
    cfg_table: str,
    alert_id: str,
    databricks_alert_id: Optional[str],
    display_name: str,
    status: str,
    error: Optional[str] = None,
) -> None:
    """
    Update sync status in the config table.
    
    Uses proper escaping to avoid SQL injection.
    """
    # Escape values for SQL
    safe_display_name = display_name.replace("'", "''") if display_name else ""
    safe_error = error.replace("'", "''")[:1900] if error else None
    safe_alert_id = alert_id.replace("'", "''")
    
    update_sql = f"""
UPDATE {cfg_table}
SET
  databricks_alert_id = {f"'{databricks_alert_id}'" if databricks_alert_id else "databricks_alert_id"},
  databricks_display_name = '{safe_display_name}',
  last_synced_at = CURRENT_TIMESTAMP(),
  last_sync_status = '{status}',
  last_sync_error = {f"'{safe_error}'" if safe_error else "NULL"}
WHERE alert_id = '{safe_alert_id}'
"""
    spark.sql(update_sql)


# ==============================================================================
# Main Sync Logic
# ==============================================================================


def sync_alerts(
    spark: SparkSession,
    *,
    catalog: str,
    gold_schema: str,
    warehouse_id: str,
    dry_run: bool,
    delete_disabled: bool,
    enable_parallel: bool = False,
    parallel_workers: int = DEFAULT_PARALLEL_WORKERS,
) -> None:
    """
    Main sync function: reads config table, creates/updates/deletes alerts.
    
    Uses Databricks SDK for automatic authentication and typed API.
    
    Args:
        spark: SparkSession
        catalog: Target catalog
        gold_schema: Target schema
        warehouse_id: SQL warehouse for alert execution
        dry_run: If True, don't make API calls
        delete_disabled: If True, delete disabled alerts
        enable_parallel: (reserved for future use)
        parallel_workers: (reserved for future use)
    """
    # Start metrics collection
    metrics = AlertSyncMetrics.start(catalog, gold_schema, dry_run)
    
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"
    dest_table = f"{catalog}.{gold_schema}.notification_destinations"

    # Load destination mapping
    destination_map_rows = (
        spark.table(dest_table)
        .where(col("is_enabled") == True)  # noqa: E712
        .select("destination_id", "databricks_destination_id")
        .collect()
    )
    destination_id_by_channel_id = {
        r["destination_id"]: r["databricks_destination_id"]
        for r in destination_map_rows
        if r["databricks_destination_id"]
    }

    # Load enabled configs
    enabled_configs = (
        spark.table(cfg_table)
        .where(col("is_enabled") == True)  # noqa: E712
        .orderBy(col("agent_domain"), col("severity").desc(), col("alert_id"))
        .collect()
    )
    metrics.total_alerts = len(enabled_configs)

    # Load disabled configs (for delete sync)
    disabled_configs = []
    if delete_disabled:
        disabled_configs = (
            spark.table(cfg_table)
            .where(col("is_enabled") == False)  # noqa: E712
            .where(col("databricks_alert_id").isNotNull())
            .select("alert_id", "databricks_alert_id", "databricks_display_name")
            .collect()
        )

    # Initialize SDK client (auto-authentication in Databricks notebook)
    ws = WorkspaceClient()
    
    # List existing alerts
    existing = list_existing_alerts(ws)

    # Print summary
    print("=" * 80)
    print("SQL ALERT SYNC ENGINE (SDK)")
    print("=" * 80)
    print(f"Catalog:          {catalog}")
    print(f"Gold schema:      {gold_schema}")
    print(f"Warehouse:        {warehouse_id}")
    print(f"Dry run:          {dry_run}")
    print(f"Delete disabled:  {delete_disabled}")
    print(f"SDK:              databricks-sdk (WorkspaceClient.alerts_v2)")
    print(f"Existing alerts:  {len(existing)}")
    print(f"Enabled configs:  {len(enabled_configs)}")
    print(f"Disabled configs: {len(disabled_configs)}")
    print("-" * 80)

    errors: List[Tuple[str, str]] = []

    # =====================================================================
    # Phase 1: Sync enabled alerts (create/update)
    # =====================================================================
    print("\n[PHASE 1] Syncing enabled alerts...")
    
    for i, row in enumerate(enabled_configs, 1):
        cfg = AlertConfigRow.from_spark_row(row)
        display_name = f"[{cfg.severity}] {cfg.alert_name}"

        subscriptions = build_subscriptions(
            channel_ids=cfg.notification_channels,
            destination_id_by_channel_id=destination_id_by_channel_id,
        )

        alert_v2 = build_alert_v2(
            cfg,
            catalog=catalog,
            gold_schema=gold_schema,
            warehouse_id=warehouse_id,
            subscriptions=subscriptions,
        )

        existing_alert = existing.get(display_name)
        action = "CREATE" if not existing_alert else "UPDATE"

        print(f"[{i}/{len(enabled_configs)}] {action}: {cfg.alert_id} -> {display_name}")

        if dry_run:
            print("  [DRY RUN] Skipping API call")
            metrics.record_skip()
            continue

        started = time.time()
        try:
            if not existing_alert:
                # Create new alert
                try:
                    created = ws.alerts_v2.create_alert(alert_v2)
                    deployed_id = created.id
                    update_sync_status(
                        spark, cfg_table, cfg.alert_id, deployed_id, display_name, "CREATED"
                    )
                    elapsed = time.time() - started
                    metrics.record_create(elapsed)
                    print(f"  ✓ CREATED ({elapsed:.2f}s)")
                    
                except Exception as e:
                    # Handle ResourceAlreadyExists - refresh and update
                    if "RESOURCE_ALREADY_EXISTS" in str(e):
                        print(f"  Alert already exists, refreshing and updating...")
                        existing = list_existing_alerts(ws)
                        existing_alert = existing.get(display_name)
                        if existing_alert:
                            ws.alerts_v2.update_alert(
                                id=existing_alert.id,
                                alert=alert_v2,
                                update_mask="display_name,query_text,warehouse_id,schedule,evaluation,custom_summary,custom_description"
                            )
                            update_sync_status(
                                spark, cfg_table, cfg.alert_id, existing_alert.id, display_name, "UPDATED"
                            )
                            elapsed = time.time() - started
                            metrics.record_update(elapsed)
                            print(f"  ✓ UPDATED (found existing, {elapsed:.2f}s)")
                        else:
                            raise RuntimeError("Alert exists but could not be found after refresh")
                    else:
                        raise
            else:
                # Update existing alert
                ws.alerts_v2.update_alert(
                    id=existing_alert.id,
                    alert=alert_v2,
                    update_mask="display_name,query_text,warehouse_id,schedule,evaluation,custom_summary,custom_description"
                )
                update_sync_status(
                    spark, cfg_table, cfg.alert_id, existing_alert.id, display_name, "UPDATED"
                )
                elapsed = time.time() - started
                metrics.record_update(elapsed)
                print(f"  ✓ UPDATED ({elapsed:.2f}s)")

        except Exception as e:
            err = str(e)
            print(f"  ✗ ERROR: {err[:400]}")
            errors.append((cfg.alert_id, err))
            metrics.record_error(cfg.alert_id, err)
            update_sync_status(
                spark, cfg_table, cfg.alert_id, None, display_name, "ERROR", err
            )

    # =====================================================================
    # Phase 2: Delete disabled alerts (if enabled)
    # =====================================================================
    if delete_disabled and disabled_configs:
        print(f"\n[PHASE 2] Deleting {len(disabled_configs)} disabled alert(s)...")
        
        for i, row in enumerate(disabled_configs, 1):
            alert_id = row["alert_id"]
            databricks_alert_id = row["databricks_alert_id"]
            display_name = row["databricks_display_name"] or alert_id

            print(f"[{i}/{len(disabled_configs)}] DELETE: {alert_id} ({databricks_alert_id})")

            if dry_run:
                print("  [DRY RUN] Skipping API call")
                metrics.record_skip()
                continue

            started = time.time()
            try:
                ws.alerts_v2.trash_alert(databricks_alert_id)
                
                # Clear the deployed ID in config
                update_sync_status(
                    spark, cfg_table, alert_id, None, display_name, "DELETED"
                )
                
                elapsed = time.time() - started
                print(f"  ✓ Trashed ({elapsed:.2f}s)")
                metrics.record_delete(elapsed)

            except Exception as e:
                err = str(e)
                print(f"  ✗ DELETE ERROR: {err[:400]}")
                errors.append((alert_id, f"DELETE: {err}"))
                metrics.record_error(alert_id, err)

    # =====================================================================
    # Finish metrics and log
    # =====================================================================
    metrics.finish()
    print_metrics_summary(metrics)
    
    # Log metrics to table (skip if dry run)
    if not dry_run:
        try:
            log_sync_metrics_spark(spark, metrics)
        except Exception as e:
            print(f"⚠️ Could not log metrics: {e}")

    # =====================================================================
    # Summary
    # =====================================================================
    print("-" * 80)
    print(f"Synced OK:  {metrics.success_count}/{len(enabled_configs)}")
    if delete_disabled:
        print(f"Deleted:    {metrics.deleted_count}/{len(disabled_configs)}")
    
    if errors:
        print(f"\nFailed operations ({len(errors)}):")
        for aid, msg in errors[:25]:
            print(f"  - {aid}: {msg[:200]}")
        raise RuntimeError(f"SQL Alert sync failed for {len(errors)} operation(s)")

    print("\n✅ Alert sync completed successfully!")


# ==============================================================================
# Entry Point
# ==============================================================================

# COMMAND ----------

def main() -> None:
    """Main entry point with widget initialization."""
    # Define widgets with defaults
    dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")  # type: ignore[name-defined]
    dbutils.widgets.text("gold_schema", "gold", "Gold Schema")  # type: ignore[name-defined]
    dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")  # type: ignore[name-defined]
    dbutils.widgets.text("dry_run", "true", "Dry run (true/false)")  # type: ignore[name-defined]
    dbutils.widgets.text("delete_disabled", "false", "Delete disabled alerts (true/false)")  # type: ignore[name-defined]
    dbutils.widgets.text("enable_parallel", "false", "Enable parallel sync (true/false)")  # type: ignore[name-defined]
    dbutils.widgets.text("parallel_workers", str(DEFAULT_PARALLEL_WORKERS), "Parallel worker count")  # type: ignore[name-defined]

    (
        catalog,
        gold_schema,
        warehouse_id,
        dry_run,
        delete_disabled,
        enable_parallel,
        parallel_workers,
    ) = get_parameters()

    if not warehouse_id:
        raise ValueError("warehouse_id widget is required")

    spark = SparkSession.builder.getOrCreate()
    
    sync_alerts(
        spark,
        catalog=catalog,
        gold_schema=gold_schema,
        warehouse_id=warehouse_id,
        dry_run=dry_run,
        delete_disabled=delete_disabled,
        enable_parallel=enable_parallel,
        parallel_workers=parallel_workers,
    )
    
    dbutils.notebook.exit("SUCCESS: SQL alerts synced")  # type: ignore[name-defined]


if __name__ == "__main__":
    main()
