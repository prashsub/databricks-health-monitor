# Databricks notebook source
"""
Document Lakehouse Monitor Output Tables
========================================

Adds detailed table and column descriptions to Lakehouse Monitoring output tables
to enable Genie and LLMs to understand the metrics for natural language queries.

Run this notebook AFTER monitors have initialized (typically 15+ minutes after creation).
Can be run independently or as part of the monitoring setup workflow.

Output Tables Documented:
- {table}_profile_metrics: Contains AGGREGATE and DERIVED custom metrics as columns
- {table}_drift_metrics: Contains DRIFT metrics comparing periods

Genie Integration:
- Table comments explain overall purpose and usage
- Column comments describe business meaning and technical calculation
- Use column_name=':table' filter for table-level business KPIs
"""

# COMMAND ----------

from monitor_utils import (
    document_all_monitor_tables,
    document_monitor_output_tables,
    METRIC_DESCRIPTIONS,
    MONITOR_TABLE_DESCRIPTIONS,
)

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
dbutils.widgets.dropdown("verbose", "true", ["true", "false"], "Verbose Output")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
verbose = dbutils.widgets.get("verbose") == "true"

# COMMAND ----------

def main():
    """Document all Lakehouse Monitoring output tables."""
    
    print("=" * 70)
    print("LAKEHOUSE MONITOR DOCUMENTATION")
    print("=" * 70)
    print(f"  Catalog:          {catalog}")
    print(f"  Gold Schema:      {gold_schema}")
    print(f"  Monitoring Schema: {gold_schema}_monitoring")
    print(f"  Metrics Registry: {len(METRIC_DESCRIPTIONS)} descriptions loaded")
    print("-" * 70)
    
    if verbose:
        print("\n📊 Tables to Document:")
        for table_name in MONITOR_TABLE_DESCRIPTIONS.keys():
            print(f"    • {table_name}_profile_metrics")
            print(f"    • {table_name}_drift_metrics")
        print()
    
    # Document all monitoring tables
    results = document_all_monitor_tables(spark, catalog, gold_schema)
    
    # Count results
    success_count = 0
    not_ready_count = 0
    error_count = 0
    
    for table_name, table_results in results.items():
        for table_type, status in table_results.items():
            if "SUCCESS" in status:
                success_count += 1
            elif status == "NOT_READY":
                not_ready_count += 1
            else:
                error_count += 1
    
    print("\n" + "-" * 70)
    
    if verbose:
        print("\nDetailed Results:")
        for table_name, table_results in results.items():
            print(f"\n  {table_name}:")
            for table_type, status in table_results.items():
                icon = "✓" if "SUCCESS" in status else "⚠" if status == "NOT_READY" else "✗"
                print(f"    [{icon}] {table_type}: {status}")
    
    # Exit with appropriate status
    if not_ready_count > 0 and success_count == 0:
        print(f"\n[⚠ NOT READY] Monitoring tables not yet created.")
        print("    Run this notebook again after monitors initialize (~15 min).")
        dbutils.notebook.exit(f"NOT_READY: {not_ready_count} tables still initializing")
    elif error_count > 0:
        print(f"\n[⚠ PARTIAL] Some tables had errors.")
        dbutils.notebook.exit(f"PARTIAL: {success_count} success, {error_count} errors")
    else:
        print(f"\n[✓ SUCCESS] All {success_count} monitoring tables documented!")
        print("    Genie can now understand custom metrics for natural language queries.")
        dbutils.notebook.exit(f"SUCCESS: {success_count} tables documented for Genie")

# COMMAND ----------

# Call main() directly - __name__ check doesn't work in Databricks job notebooks
main()

