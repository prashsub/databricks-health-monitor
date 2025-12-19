# Databricks notebook source
"""
Setup All Lakehouse Monitors
============================

Creates all Lakehouse Monitors for Health Monitor Gold tables.
Orchestrates monitor creation across all domains.
"""

# COMMAND ----------

from monitor_utils import (
    check_monitoring_available,
    wait_for_monitor_tables,
    MONITORING_AVAILABLE
)

if MONITORING_AVAILABLE:
    from databricks.sdk import WorkspaceClient

# Import domain monitors
from cost_monitor import create_cost_monitor
from job_monitor import create_job_monitor
from query_monitor import create_query_monitor
from cluster_monitor import create_cluster_monitor
from security_monitor import create_security_monitor

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
dbutils.widgets.dropdown("skip_wait", "false", ["true", "false"], "Skip Wait")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
skip_wait = dbutils.widgets.get("skip_wait") == "true"

print(f"Setting up Lakehouse Monitors for: {catalog}.{gold_schema}")
if skip_wait:
    print("(Wait for table creation will be skipped)")

# COMMAND ----------

def setup_all_monitors(workspace_client, catalog: str, gold_schema: str, spark):
    """Create all domain monitors."""
    results = {}

    # Monitor configurations
    monitors = [
        ("Cost", create_cost_monitor),
        ("Job", create_job_monitor),
        ("Query", create_query_monitor),
        ("Cluster", create_cluster_monitor),
        ("Security", create_security_monitor),
    ]

    print("=" * 60)
    print("Creating Lakehouse Monitors")
    print("=" * 60)

    for name, create_func in monitors:
        print(f"\n--- {name} Monitor ---")
        try:
            monitor = create_func(workspace_client, catalog, gold_schema, spark)
            results[name] = "SUCCESS" if monitor else "SKIPPED"
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results[name] = f"FAILED: {str(e)}"

    return results


def print_summary(results: dict):
    """Print monitor creation summary."""
    print("\n" + "=" * 60)
    print("Monitor Creation Summary")
    print("=" * 60)

    success_count = sum(1 for v in results.values() if v == "SUCCESS")
    skipped_count = sum(1 for v in results.values() if v == "SKIPPED")
    failed_count = sum(1 for v in results.values() if v.startswith("FAILED"))

    print(f"\nTotal: {len(results)}")
    print(f"  Created: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Failed: {failed_count}")

    print("\nDetails:")
    for name, status in results.items():
        icon = "OK" if status == "SUCCESS" else "SKIP" if status == "SKIPPED" else "ERR"
        print(f"  [{icon}] {name}: {status}")

    return failed_count

# COMMAND ----------

def main():
    """Main entry point."""
    if not check_monitoring_available():
        print("Lakehouse Monitoring not available - skipping")
        dbutils.notebook.exit("SKIPPED: SDK not available")
        return

    workspace_client = WorkspaceClient()

    # Create all monitors
    results = setup_all_monitors(workspace_client, catalog, gold_schema, spark)

    # Print summary
    failed_count = print_summary(results)

    # Wait for tables (optional)
    if not skip_wait and failed_count == 0:
        print("\n" + "=" * 60)
        print("Waiting for Monitor Tables")
        print("=" * 60)
        wait_for_monitor_tables(minutes=15)

    # Create monitoring schema
    monitoring_schema = f"{gold_schema}_monitoring"
    print(f"\nMonitoring output schema: {catalog}.{monitoring_schema}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{monitoring_schema}")

    # Exit with appropriate status
    if failed_count > 0:
        dbutils.notebook.exit(f"PARTIAL: {failed_count} monitors failed")
    else:
        dbutils.notebook.exit(f"SUCCESS: {len(results)} monitors configured")

# COMMAND ----------

if __name__ == "__main__":
    main()
