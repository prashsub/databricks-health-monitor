# Databricks notebook source
"""
Setup All Lakehouse Monitors
============================

TRAINING MATERIAL: Lakehouse Monitoring Orchestration
------------------------------------------------------

This notebook demonstrates how to orchestrate the creation of multiple
Databricks Lakehouse Monitors across all domain tables.

WHAT IS LAKEHOUSE MONITORING:
-----------------------------
Databricks Lakehouse Monitoring automatically tracks data quality metrics
for Delta tables. It provides:
- Profile metrics (null counts, distinct counts, distributions)
- Drift detection (statistical changes over time)
- Custom metrics (domain-specific KPIs)

ARCHITECTURE:
-------------
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAKEHOUSE MONITORING SETUP                            │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Gold Tables (source)                                            │   │
│  │  ├── fact_usage (Cost)                                          │   │
│  │  ├── fact_job_run_timeline (Reliability)                        │   │
│  │  ├── fact_query_history (Performance)                           │   │
│  │  ├── fact_cluster_usage (Performance)                           │   │
│  │  ├── fact_audit_logs (Security)                                 │   │
│  │  └── ... more tables                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Lakehouse Monitors (created by this notebook)                   │   │
│  │  ├── cost_usage_monitor                                         │   │
│  │  ├── job_reliability_monitor                                    │   │
│  │  ├── query_performance_monitor                                  │   │
│  │  └── ... more monitors                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Output Tables (auto-generated)                                  │   │
│  │  ├── {table}_profile_metrics (statistics)                       │   │
│  │  └── {table}_drift_metrics (change detection)                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

WHY LAKEHOUSE MONITORING:
-------------------------
1. AUTOMATED: No manual data quality checks
2. STATISTICAL: Uses proper statistical methods
3. HISTORICAL: Tracks metrics over time
4. ALERTABLE: Can trigger alerts on drift
5. INTEGRATED: Works with Unity Catalog governance

MONITOR TYPES:
--------------
1. SNAPSHOT: For dimension tables (point-in-time)
2. TIME_SERIES: For fact tables (time-partitioned)
3. INFERENCE: For ML model inputs/outputs

CUSTOM METRICS:
---------------
Each domain monitor defines custom metrics specific to that domain:
- Cost: budget_variance, cost_per_dbu, tag_coverage
- Reliability: job_success_rate, avg_duration_hours
- Performance: query_failure_rate, avg_duration_seconds

ASYNC TABLE CREATION:
---------------------
CRITICAL: Lakehouse Monitoring creates tables ASYNCHRONOUSLY.
After creating a monitor, _profile_metrics and _drift_metrics
tables may take 10-15 minutes to appear.
Always call wait_for_monitor_tables() after creation.

Creates all Lakehouse Monitors for Health Monitor Gold tables.
Orchestrates monitor creation across all domains.
"""

# COMMAND ----------

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Conditional Imports Pattern
#
# Some Databricks SDK features may not be available in all environments.
# We use conditional imports to gracefully handle this.

from monitor_utils import (
    check_monitoring_available,  # Check if SDK supports monitoring
    wait_for_monitor_tables,     # Wait for async table creation
    document_all_monitor_tables, # Add descriptions for Genie
    MONITORING_AVAILABLE         # Boolean flag
)

# Conditional import: Only import WorkspaceClient if monitoring is available
if MONITORING_AVAILABLE:
    from databricks.sdk import WorkspaceClient

# Import domain-specific monitor creators
# Each module defines custom metrics for its domain
from cost_monitor import create_cost_monitor
from job_monitor import create_job_monitor
from query_monitor import create_query_monitor
from cluster_monitor import create_cluster_monitor
from security_monitor import create_security_monitor
from quality_monitor import create_quality_monitor
from governance_monitor import create_governance_monitor
from inference_monitor import create_inference_monitor

# COMMAND ----------

# =============================================================================
# WIDGET PARAMETERS
# =============================================================================
# TRAINING MATERIAL: Widget Patterns for Configurable Notebooks
#
# Widgets provide a UI for notebook parameters in Databricks.
# When run as a job, values come from base_parameters in YAML.
# When run interactively, user can modify values in UI.
#
# WIDGET TYPES:
# - text(): Free-form text input
# - dropdown(): Single selection from list
# - multiselect(): Multiple selections from list
# - combobox(): Dropdown with free-form option

dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
dbutils.widgets.dropdown("skip_wait", "false", ["true", "false"], "Skip Wait")

# Retrieve parameter values
catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
skip_wait = dbutils.widgets.get("skip_wait") == "true"

# Log configuration (visible in job logs)
print(f"Setting up Lakehouse Monitors for: {catalog}.{gold_schema}")
if skip_wait:
    print("(Wait for table creation will be skipped)")

# COMMAND ----------

# =============================================================================
# MONITOR ORCHESTRATION
# =============================================================================
# TRAINING MATERIAL: Factory Pattern for Monitor Creation

def setup_all_monitors(workspace_client, catalog: str, gold_schema: str, spark):
    """
    Create all domain monitors.
    
    TRAINING MATERIAL: Orchestrator Pattern
    ========================================
    
    This function orchestrates creation of ALL monitors across domains.
    Each domain has its own create_xxx_monitor() function that:
    - Defines custom metrics specific to that domain
    - Configures time/granularity columns
    - Sets slicing dimensions
    
    DOMAIN → MONITOR MAPPING:
    -------------------------
    ┌─────────────┬─────────────────────┬───────────────────────────┐
    │   Domain    │    Monitor Name     │     Primary Table         │
    ├─────────────┼─────────────────────┼───────────────────────────┤
    │   Cost      │   Cost Monitor      │   fact_usage             │
    │   Perf      │   Query Monitor     │   fact_query_history     │
    │   Perf      │   Cluster Monitor   │   fact_cluster_usage     │
    │   Reliab    │   Job Monitor       │   fact_job_run_timeline  │
    │   Security  │   Security Monitor  │   fact_audit_logs        │
    │   Quality   │   Quality Monitor   │   fact_data_quality      │
    │   Governance│   Governance Monitor│   fact_lineage_events    │
    │   ML        │   Inference Monitor │   fact_model_inference   │
    └─────────────┴─────────────────────┴───────────────────────────┘
    
    ERROR HANDLING:
    ---------------
    Each monitor creation is wrapped in try/except.
    Failure of one monitor doesn't stop others.
    Results dict tracks success/failure for each.
    
    WHY FACTORY FUNCTIONS:
    ----------------------
    Each domain has different:
    - Custom metrics (business KPIs)
    - Time columns (usage_date vs created_at)
    - Slicing dimensions (workspace_id vs job_id)
    
    Args:
        workspace_client: Databricks SDK WorkspaceClient
        catalog: Unity Catalog name
        gold_schema: Gold layer schema name
        spark: SparkSession (for table operations)
    
    Returns:
        Dict mapping monitor name to status (SUCCESS/SKIPPED/FAILED)
    """
    results = {}

    # Monitor configurations by Agent Domain
    # Each tuple: (display_name, create_function)
    monitors = [
        # Cost Domain - tracks billing and spend
        ("Cost", create_cost_monitor),
        # Performance Domain - query and cluster metrics
        ("Query", create_query_monitor),
        ("Cluster", create_cluster_monitor),
        # Reliability Domain - job execution health
        ("Job", create_job_monitor),
        # Security Domain - audit and access patterns
        ("Security", create_security_monitor),
        # Quality Domain - data quality metrics
        ("Quality", create_quality_monitor),
        # Governance Domain - lineage and catalog events
        ("Governance", create_governance_monitor),
        # ML Inference Domain - model serving metrics
        ("Inference", create_inference_monitor),
    ]

    print("=" * 60)
    print("Creating Lakehouse Monitors")
    print("=" * 60)

    # Create each monitor (fail-safe: errors don't stop loop)
    for name, create_func in monitors:
        print(f"\n--- {name} Monitor ---")
        try:
            monitor = create_func(workspace_client, catalog, gold_schema, spark)
            results[name] = "SUCCESS" if monitor else "SKIPPED"
        except Exception as e:
            # Log error but continue with other monitors
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
        
        # Document monitoring tables for Genie after tables are ready
        print("\n" + "=" * 60)
        print("Documenting Monitor Tables for Genie")
        print("=" * 60)
        doc_results = document_all_monitor_tables(spark, catalog, gold_schema)
        
        # Count documented tables
        doc_success = sum(
            1 for table_results in doc_results.values()
            for status in table_results.values()
            if "SUCCESS" in status
        )
        print(f"\n  Documented {doc_success} monitoring tables for Genie")

    # Create monitoring schema (if not already exists)
    monitoring_schema = f"{gold_schema}_monitoring"
    print(f"\nMonitoring output schema: {catalog}.{monitoring_schema}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{monitoring_schema}")

    # Exit with appropriate status
    if failed_count > 0:
        dbutils.notebook.exit(f"PARTIAL: {failed_count} monitors failed")
    else:
        dbutils.notebook.exit(f"SUCCESS: {len(results)} monitors configured")

# COMMAND ----------

# Call main() directly - __name__ check doesn't work in Databricks job notebooks
main()
