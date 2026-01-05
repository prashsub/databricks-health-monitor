# Databricks notebook source
"""
Genie Space Benchmark SQL Validation Notebook

Validates SQL queries in Genie Space benchmark sections before deployment:
1. SQL syntax correctness
2. Column resolution (columns exist in tables/views)
3. Table/view existence
4. Function calls are valid (TVFs, MEASURE())
5. No ambiguous references

Uses EXPLAIN to validate without executing queries.
Fails the job if any validation errors are found.
"""

# COMMAND ----------

import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    # feature_schema is optional - defaults to gold_schema_ml in validation script
    try:
        feature_schema = dbutils.widgets.get("feature_schema")
    except Exception:
        feature_schema = f"{gold_schema}_ml"
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema

# COMMAND ----------

# Get the script directory (where markdown files are located)
try:
    # In Databricks workspace
    notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    
    # Convert to file system path for bundle deployments
    if ".bundle" in notebook_path:
        script_dir = os.path.dirname(notebook_path.replace("/Workspace", ""))
        if not script_dir.startswith("/Workspace"):
            script_dir = "/Workspace" + script_dir
    else:
        script_dir = os.path.dirname(notebook_path)
    
    # Add to sys.path for imports
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    genie_dir = Path(script_dir)
    print(f"Notebook path: {notebook_path}")
    print(f"Genie directory: {genie_dir}")
    
except Exception as e:
    print(f"Error getting paths: {e}")
    # Fallback
    script_dir = "/Workspace/Users/prashanth.subrahmanyam@databricks.com/.bundle/databricks_health_monitor/dev/files/src/genie"
    genie_dir = Path(script_dir)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    print(f"Using fallback: {genie_dir}")

# COMMAND ----------

from validate_genie_benchmark_sql import validate_all_genie_benchmarks

# COMMAND ----------

def main():
    """Main validation function."""
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    print("\n" + "=" * 80)
    print("GENIE SPACE BENCHMARK SQL VALIDATOR")
    print("=" * 80)
    print(f"📁 Genie Space directory: {genie_dir}")
    print(f"🗂️  Catalog: {catalog}")
    print(f"📊 Gold Schema: {gold_schema}")
    print(f"🤖 Feature/ML Schema: {feature_schema}")
    print("")
    
    # Validate all benchmark queries
    success, results = validate_all_genie_benchmarks(genie_dir, catalog, gold_schema, spark, feature_schema)
    
    if not success:
        invalid_count = sum(1 for r in results if not r['valid'])
        print(f"\n❌ VALIDATION FAILED: {invalid_count} benchmark queries have errors")
        print("Fix the errors above before deploying Genie Spaces.")
        
        # Build detailed error summary for exception message
        error_details = []
        for r in results:
            if not r['valid']:
                error_type = r.get('error_type', 'UNKNOWN')
                short_error = str(r.get('error', ''))[:200]
                error_details.append(f"  - {r['genie_space']} Q{r['question_num']}: {error_type} - {short_error}")
        
        error_summary = "\n".join(error_details[:10])  # First 10 errors
        if len(error_details) > 10:
            error_summary += f"\n  ... and {len(error_details) - 10} more errors"
        
        raise Exception(f"Genie Space benchmark validation failed: {invalid_count} queries with errors\n\nFirst errors:\n{error_summary}")
    
    print("\n✅ VALIDATION PASSED: All benchmark queries are valid!")
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()
