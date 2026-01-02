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

CRITICAL QUERY PATTERNS FOR GENIE:
==================================

1. PROFILE_METRICS - Business KPIs:
   WHERE column_name = ':table' AND log_type = 'INPUT'
   - Overall: WHERE slice_key IS NULL
   - By dimension: WHERE slice_key = 'workspace_id' AND slice_value = 'value'

2. DRIFT_METRICS - Period Comparisons:
   WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'
   - Overall: WHERE slice_key IS NULL
   - By dimension: WHERE slice_key = 'workspace_id' AND slice_value = 'value'

3. TIME FILTERING:
   WHERE window.start >= 'date' AND window.end <= 'date'

4. NO SLICING (Overall Metrics):
   COALESCE(slice_key, 'No Slice') = 'No Slice'
   COALESCE(slice_value, 'No Slice') = 'No Slice'

Genie Integration:
- Table comments explain query patterns and available metrics
- Column comments describe business meaning and technical calculation
- Slicing dimensions enable "show by workspace", "show by SKU" type queries
"""

# COMMAND ----------

from monitor_utils import (
    document_all_monitor_tables,
    document_monitor_output_tables,
    METRIC_DESCRIPTIONS,
    MONITOR_TABLE_DESCRIPTIONS,
    MONITORING_QUERY_GUIDE,
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
        print("\n📋 QUERY PATTERNS FOR GENIE:")
        print("-" * 40)
        print("  PROFILE_METRICS (business KPIs):")
        print("    WHERE column_name = ':table'")
        print("    AND log_type = 'INPUT'")
        print("    AND slice_key IS NULL  -- for overall metrics")
        print()
        print("  DRIFT_METRICS (period comparisons):")
        print("    WHERE drift_type = 'CONSECUTIVE'")
        print("    AND column_name = ':table'")
        print()
        print("  SLICING (dimensional analysis):")
        print("    WHERE slice_key = 'workspace_id'")
        print("    AND slice_value = 'your_value'")
        print()
        
        print("📊 Tables to Document:")
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
    
    # Print query guide summary
    print("\n📖 GENIE QUERY GUIDE SUMMARY:")
    print("-" * 50)
    print("  Example queries Genie can now understand:")
    print()
    print("  'What is the total cost this month?'")
    print("  → Query fact_usage_profile_metrics")
    print("    WHERE column_name=':table' AND log_type='INPUT'")
    print()
    print("  'Show cost breakdown by workspace'")
    print("  → Query fact_usage_profile_metrics")
    print("    WHERE slice_key='workspace_id'")
    print()
    print("  'Which jobs failed yesterday?'")
    print("  → Query fact_job_run_timeline_profile_metrics")
    print("    WHERE slice_key='result_state' AND slice_value='FAILED'")
    print()
    print("  'How has cost changed compared to last period?'")
    print("  → Query fact_usage_drift_metrics")
    print("    WHERE drift_type='CONSECUTIVE'")
    
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
        print("    Query patterns documented in table comments for LLM understanding.")
        dbutils.notebook.exit(f"SUCCESS: {success_count} tables documented for Genie")

# COMMAND ----------

# Call main() directly - __name__ check doesn't work in Databricks job notebooks
main()

