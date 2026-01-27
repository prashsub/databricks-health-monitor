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

# Global variable to store results for exit cell
_doc_results = None

def main():
    """Document all Lakehouse Monitoring output tables."""
    global _doc_results
    
    print("=" * 70)
    print("LAKEHOUSE MONITOR DOCUMENTATION")
    print("=" * 70)
    print(f"  Catalog:           {catalog}")
    print(f"  Gold Schema:       {gold_schema}")
    print(f"  Monitoring Schema: {gold_schema}_monitoring")
    print(f"  Metrics Registry:  {len(METRIC_DESCRIPTIONS)} descriptions loaded")
    print(f"  Verbose Mode:      {verbose}")
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
    
    print("\n📊 DISCOVERING MONITORING TABLES...")
    print("-" * 40)
    
    # List actual tables in monitoring schema
    monitoring_schema = f"{gold_schema}_monitoring"
    try:
        existing_tables = spark.sql(f"SHOW TABLES IN {catalog}.{monitoring_schema}").collect()
        existing_table_names = [row.tableName for row in existing_tables]
        print(f"  Found {len(existing_table_names)} tables in {catalog}.{monitoring_schema}:")
        for t in sorted(existing_table_names):
            print(f"    • {t}")
        print()
    except Exception as e:
        print(f"  ⚠ Could not list tables: {str(e)[:60]}")
        print(f"  Will attempt to document known monitor tables anyway.\n")
    
    # Document all monitoring tables (pass verbose flag)
    results = document_all_monitor_tables(spark, catalog, gold_schema, verbose=verbose)
    
    # Count results by status
    success_count = 0
    not_ready_count = 0
    error_count = 0
    total_cols_documented = 0
    total_cols_in_tables = 0
    
    for table_name, table_results in results.items():
        # Count profile/drift table statuses
        profile_status = table_results.get("profile_metrics", "")
        drift_status = table_results.get("drift_metrics", "")
        
        # Profile metrics
        if "SUCCESS" in str(profile_status):
            success_count += 1
            total_cols_documented += table_results.get("profile_columns_documented", 0)
            total_cols_in_tables += table_results.get("profile_columns_total", 0)
        elif profile_status == "NOT_READY":
            not_ready_count += 1
        elif profile_status != "NOT_FOUND":
            error_count += 1
            
        # Drift metrics
        if "SUCCESS" in str(drift_status):
            success_count += 1
            total_cols_documented += table_results.get("drift_columns_documented", 0)
            total_cols_in_tables += table_results.get("drift_columns_total", 0)
        elif drift_status == "NOT_READY":
            not_ready_count += 1
        elif drift_status != "NOT_FOUND":
            error_count += 1
    
    print("\n" + "=" * 70)
    print("DOCUMENTATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"  ✓ Tables documented:      {success_count}")
    print(f"  ⏳ Tables not ready:       {not_ready_count}")
    print(f"  ✗ Tables with errors:     {error_count}")
    print(f"  📊 Columns documented:     {total_cols_documented}/{total_cols_in_tables}")
    print("-" * 70)
    
    # Print query guide summary
    print("\n📖 GENIE QUERY EXAMPLES:")
    print("-" * 50)
    print("  'What is the total cost this month?'")
    print("  → SELECT total_daily_cost FROM fact_usage_profile_metrics")
    print("    WHERE column_name=':table' AND log_type='INPUT'")
    print()
    print("  'Show cost breakdown by workspace'")
    print("  → SELECT slice_value as workspace, total_daily_cost")
    print("    FROM fact_usage_profile_metrics")
    print("    WHERE slice_key='workspace_id'")
    print()
    print("  'Which jobs failed yesterday?'")
    print("  → SELECT failure_count FROM fact_job_run_timeline_profile_metrics")
    print("    WHERE slice_key='result_state' AND slice_value='FAILED'")
    print()
    print("  'How has cost changed compared to last period?'")
    print("  → SELECT cost_drift_pct FROM fact_usage_drift_metrics")
    print("    WHERE drift_type='CONSECUTIVE'")
    
    # Store results for exit cell
    _doc_results = {
        "success_count": success_count,
        "not_ready_count": not_ready_count,
        "error_count": error_count,
        "total_cols_documented": total_cols_documented,
        "total_cols_in_tables": total_cols_in_tables,
        "detailed_results": results
    }
    
    return _doc_results

# COMMAND ----------

# Call main() directly - __name__ check doesn't work in Databricks job notebooks
results = main()

# COMMAND ----------

# NOTEBOOK EXIT (separate cell for job status)
# This cell provides the final exit status for the DAB job

if _doc_results is None:
    dbutils.notebook.exit("ERROR: main() did not complete")

success_count = _doc_results["success_count"]
not_ready_count = _doc_results["not_ready_count"]
error_count = _doc_results["error_count"]
total_cols = _doc_results["total_cols_documented"]

# Determine exit status
if not_ready_count > 0 and success_count == 0:
    print(f"\n[⏳ NOT READY] Monitoring tables not yet created.")
    print("    Run this notebook again after monitors initialize (~15 min).")
    dbutils.notebook.exit(f"NOT_READY: {not_ready_count} tables still initializing")
elif error_count > 0:
    print(f"\n[⚠ PARTIAL] {success_count} tables documented, {error_count} had errors.")
    dbutils.notebook.exit(f"PARTIAL: {success_count} tables, {total_cols} columns documented")
else:
    print(f"\n[✓ SUCCESS] All {success_count} monitoring tables documented!")
    print(f"    {total_cols} custom metric columns documented for Genie.")
    print("    Query patterns documented in table comments for LLM understanding.")
    dbutils.notebook.exit(f"SUCCESS: {success_count} tables, {total_cols} columns documented")

