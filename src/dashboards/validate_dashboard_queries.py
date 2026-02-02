# Databricks notebook source
# MAGIC %md
# MAGIC # Dashboard SQL Query Validator
# MAGIC
# MAGIC ## TRAINING MATERIAL: SELECT LIMIT 1 Validation Strategy
# MAGIC
# MAGIC This script validates dashboard queries BEFORE deployment by executing
# MAGIC them with LIMIT 1. This catches 90%+ of errors in seconds, not minutes.
# MAGIC
# MAGIC ### WHY NOT EXPLAIN?
# MAGIC
# MAGIC | Validation | Catches | Misses |
# MAGIC |---|---|---|
# MAGIC | EXPLAIN ONLY | Syntax errors | Runtime type errors |
# MAGIC | SELECT LIMIT 1 ✅ | All of the above + column resolution, ambiguous refs | Full data errors |
# MAGIC | Full Query | Everything | Takes 20-50 minutes |
# MAGIC
# MAGIC ### Common Errors Caught
# MAGIC
# MAGIC 1. **Column Resolution**: `workspace_owner not found` → Need to check schema
# MAGIC 2. **Ambiguous Reference**: `ambiguous column owner` → Need table alias
# MAGIC 3. **Type Mismatch**: `cannot cast STRING to TIMESTAMP` → Need explicit cast
# MAGIC 4. **Missing Table**: `Table not found` → Wrong schema or table name
# MAGIC
# MAGIC ### Root Cause Analysis Pattern
# MAGIC
# MAGIC When a query fails, don't blind fix - investigate:
# MAGIC
# MAGIC ```
# MAGIC Error: workspace_owner cannot be resolved
# MAGIC
# MAGIC Step 1: Check dim_workspace schema
# MAGIC    DESCRIBE catalog.gold.dim_workspace
# MAGIC
# MAGIC Step 2: Find actual column name
# MAGIC    → "workspace_owner" not in columns, but "owner" exists
# MAGIC
# MAGIC Step 3: Fix dashboard JSON
# MAGIC    → Change "workspace_owner" to "owner"
# MAGIC ```
# MAGIC
# MAGIC Pre-deployment validation of all dashboard SQL queries.
# MAGIC Catches column resolution, syntax, and ambiguous reference errors before deployment.

# COMMAND ----------

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from pyspark.sql import SparkSession

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, gold_schema

# COMMAND ----------

def find_dashboard_dir() -> Path:
    """Find the dashboards directory."""
    # Try relative paths from different locations
    possible_paths = [
        Path("/Workspace/Users/prashanth.subrahmanyam@databricks.com/.bundle/databricks_health_monitor/dev/files/src/dashboards"),
        Path("./src/dashboards"),
        Path("../src/dashboards"),
        Path("/Workspace/Repos/prashanth.subrahmanyam@databricks.com/DatabricksHealthMonitor/src/dashboards"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Try to find using dbutils
    try:
        workspace_path = "/Workspace/Users/prashanth.subrahmanyam@databricks.com/.bundle/databricks_health_monitor/dev/files"
        dashboard_path = Path(f"{workspace_path}/src/dashboards")
        if dashboard_path.exists():
            return dashboard_path
    except:
        pass
    
    raise FileNotFoundError("Could not find dashboards directory")

# COMMAND ----------

def extract_queries_from_dashboard(dashboard_path: Path, catalog: str, gold_schema: str) -> List[Dict]:
    """Extract all SQL queries from a dashboard JSON file."""
    
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    
    queries = []
    dashboard_name = dashboard_path.stem
    
    for dataset in dashboard.get('datasets', []):
        ds_name = dataset.get('name', 'unknown')
        query = dataset.get('query', '')
        
        if not query:
            continue
        
        # Substitute variables
        query = query.replace('${catalog}', catalog)
        query = query.replace('${gold_schema}', gold_schema)
        
        # ML/Feature schema substitution (from Asset Bundle feature_schema variable)
        feature_schema = gold_schema.replace('_system_gold', '_system_gold_ml')
        query = query.replace('${feature_schema}', feature_schema)
        query = query.replace('${ml_schema}', feature_schema)
        
        # Replace parameters with default values for validation
        # :param_name -> 'All' or default value
        # IMPORTANT: Do NOT replace :table - it's a literal value in Lakehouse Monitoring, not a parameter
        # Parameters are typically preceded by = or space (e.g., WHERE x = :param or AND :param)
        
        # Date range parameters (Account Usage Dashboard v2 style)
        # :time_range.min and :time_range.max -> actual date values
        query = re.sub(r':time_range\.min\b', "CURRENT_DATE() - INTERVAL 30 DAYS", query)
        query = re.sub(r':time_range\.max\b', "CURRENT_DATE()", query)
        
        # Handle window_start from Lakehouse Monitoring tables
        # This is the actual column name in monitoring tables
        # For validation, just ensure queries referencing it are syntactically valid
        # No substitution needed - window_start is an actual column
        
        # Time and date parameters (legacy style)
        query = re.sub(r':time_window\b', "'Last 30 Days'", query)
        query = re.sub(r':time_key\b', "'Day'", query)
        query = re.sub(r':date_range\b', "'Last 30 Days'", query)
        
        # Workspace and environment parameters
        # Use ARRAY('All') for workspace params since they're used in EXPLODE()
        query = re.sub(r':workspace_filter\b', "ARRAY('All')", query)
        query = re.sub(r':workspace_name\b', "'All'", query)
        query = re.sub(r':param_workspace\b', "ARRAY('All')", query)
        
        # SKU and product parameters
        query = re.sub(r':sku_type\b', "'All'", query)
        query = re.sub(r':sku_category\b', "'All'", query)
        query = re.sub(r':product_category\b', "'All'", query)
        query = re.sub(r':billing_origin_product\b', "'All'", query)
        
        # Other filter parameters
        query = re.sub(r':compute_type\b', "'All'", query)
        query = re.sub(r':job_status\b', "'All'", query)
        query = re.sub(r':job_name\b', "'All'", query)
        query = re.sub(r':owner\b', "'All'", query)
        query = re.sub(r':service_name\b', "'All'", query)
        
        # Numeric parameters
        query = re.sub(r':annual_commit\b', "1000000", query)
        query = re.sub(r':top_n\b', "10", query)
        query = re.sub(r':limit\b', "100", query)
        
        # Lakehouse Monitoring parameters (slice filters)
        query = re.sub(r':monitor_time_start\b', "CURRENT_DATE() - INTERVAL 12 MONTHS", query)
        query = re.sub(r':monitor_time_end\b', "CURRENT_DATE()", query)
        query = re.sub(r':monitor_slice_key\b', "'No Slice'", query)
        query = re.sub(r':monitor_slice_value\b', "'No Slice'", query)
        query = re.sub(r':slice_key\b', "'No Slice'", query)
        query = re.sub(r':slice_value\b', "'No Slice'", query)
        
        # Catch remaining parameters - replace with string 'All' for validation
        # Skip :table (Lakehouse Monitoring literal) and patterns inside quoted strings
        query = re.sub(r'(?<=[=\s]):(?!table\b)([a-z_]+)\b', "'All'", query, flags=re.IGNORECASE)
        
        # Also replace CASE :param patterns that start the expression
        query = re.sub(r'CASE\s+:([a-z_]+)', r"CASE 'All'", query, flags=re.IGNORECASE)
        
        queries.append({
            'dashboard': dashboard_name,
            'dataset': ds_name,
            'query': query,
            'original_query': dataset.get('query', '')
        })
    
    return queries

# COMMAND ----------

def validate_query(spark: SparkSession, query_info: Dict) -> Dict:
    """Validate a single SQL query by executing it with LIMIT 1.
    
    Using SELECT LIMIT 1 instead of EXPLAIN because:
    - EXPLAIN may not catch all column resolution errors
    - EXPLAIN may not catch type mismatches
    - SELECT LIMIT 1 validates the full execution path
    - Only returns 1 row, so it's still fast
    """
    
    result = {
        'dashboard': query_info['dashboard'],
        'dataset': query_info['dataset'],
        'valid': False,
        'error': None,
        'error_type': None
    }
    
    try:
        # Wrap query with LIMIT 1 for fast validation
        # This catches ALL errors - syntax, columns, types, runtime
        original_query = query_info['query'].strip().rstrip(';')
        
        # Handle queries that already have LIMIT - wrap in subquery
        if 'LIMIT' in original_query.upper():
            validation_query = f"SELECT * FROM ({original_query}) AS validation_subquery LIMIT 1"
        else:
            validation_query = f"{original_query} LIMIT 1"
        
        # Actually execute the query
        spark.sql(validation_query).collect()
        result['valid'] = True
        
    except Exception as e:
        error_str = str(e)
        result['error'] = error_str
        
        # Categorize the error
        if 'UNRESOLVED_COLUMN' in error_str:
            result['error_type'] = 'COLUMN_NOT_FOUND'
            # Extract column name
            match = re.search(r"name `([^`]+)`", error_str)
            if match:
                result['error_column'] = match.group(1)
            # Extract suggestions
            match = re.search(r"Did you mean one of the following\? \[([^\]]+)\]", error_str)
            if match:
                result['suggestions'] = match.group(1)
                
        elif 'AMBIGUOUS_REFERENCE' in error_str:
            result['error_type'] = 'AMBIGUOUS_COLUMN'
            match = re.search(r"Reference `([^`]+)`", error_str)
            if match:
                result['error_column'] = match.group(1)
                
        elif 'PARSE_SYNTAX_ERROR' in error_str:
            result['error_type'] = 'SYNTAX_ERROR'
            match = re.search(r"at or near '([^']+)'", error_str)
            if match:
                result['error_near'] = match.group(1)
                
        elif 'TABLE_OR_VIEW_NOT_FOUND' in error_str:
            result['error_type'] = 'TABLE_NOT_FOUND'
            match = re.search(r"table or view `([^`]+)`", error_str)
            if match:
                result['missing_table'] = match.group(1)
        else:
            result['error_type'] = 'OTHER'
    
    return result

# COMMAND ----------

def generate_validation_report(results: List[Dict]) -> str:
    """Generate a detailed validation report."""
    
    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = len(results) - valid_count
    
    report = []
    report.append("=" * 80)
    report.append("DASHBOARD SQL VALIDATION REPORT")
    report.append("=" * 80)
    report.append(f"\nTotal queries validated: {len(results)}")
    report.append(f"✓ Valid: {valid_count}")
    report.append(f"✗ Invalid: {invalid_count}")
    report.append("")
    
    if invalid_count == 0:
        report.append("🎉 All queries passed validation!")
        return "\n".join(report)
    
    # Group errors by type
    errors_by_type = {}
    for r in results:
        if not r['valid']:
            error_type = r.get('error_type', 'OTHER')
            if error_type not in errors_by_type:
                errors_by_type[error_type] = []
            errors_by_type[error_type].append(r)
    
    # Report errors by type
    report.append("\n" + "-" * 80)
    report.append("ERRORS BY TYPE")
    report.append("-" * 80)
    
    for error_type, errors in sorted(errors_by_type.items()):
        report.append(f"\n### {error_type} ({len(errors)} errors)")
        report.append("")
        
        for err in errors:
            report.append(f"  📋 {err['dashboard']} -> {err['dataset']}")
            
            if error_type == 'COLUMN_NOT_FOUND':
                report.append(f"     Column: `{err.get('error_column', 'unknown')}`")
                if 'suggestions' in err:
                    report.append(f"     Suggestions: {err['suggestions']}")
                    
            elif error_type == 'AMBIGUOUS_COLUMN':
                report.append(f"     Column: `{err.get('error_column', 'unknown')}`")
                report.append(f"     Qualify with table alias (e.g., f.{err.get('error_column', 'column')})")
                
            elif error_type == 'SYNTAX_ERROR':
                report.append(f"     Error near: '{err.get('error_near', 'unknown')}'")
                
            elif error_type == 'TABLE_NOT_FOUND':
                report.append(f"     Missing table: {err.get('missing_table', 'unknown')}")
            
            report.append("")
    
    # Detailed error list
    report.append("\n" + "-" * 80)
    report.append("DETAILED ERRORS (for debugging)")
    report.append("-" * 80)
    
    for r in results:
        if not r['valid']:
            report.append(f"\n❌ {r['dashboard']} -> {r['dataset']}")
            report.append(f"   Error: {r['error'][:500]}...")
            report.append("")
    
    return "\n".join(report)

# COMMAND ----------

def main():
    """Main validation function."""
    
    catalog, gold_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    print("\n" + "=" * 80)
    print("DASHBOARD SQL QUERY VALIDATOR")
    print("=" * 80)
    
    # Find dashboards
    try:
        dashboard_dir = find_dashboard_dir()
        print(f"\n📁 Dashboard directory: {dashboard_dir}")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        raise
    
    # Get all dashboard JSON files
    dashboard_files = list(dashboard_dir.glob("*.lvdash.json"))
    print(f"📊 Found {len(dashboard_files)} dashboard files")
    
    # Extract all queries
    all_queries = []
    for dash_file in dashboard_files:
        queries = extract_queries_from_dashboard(dash_file, catalog, gold_schema)
        all_queries.extend(queries)
        print(f"   {dash_file.name}: {len(queries)} datasets")
    
    print(f"\n🔍 Validating {len(all_queries)} queries using SELECT LIMIT 1...")
    print("   (This executes each query to catch ALL errors)")
    print("-" * 80)
    
    import time
    start_time = time.time()
    
    # Validate each query
    results = []
    failed_queries = []
    
    for i, query_info in enumerate(all_queries):
        query_start = time.time()
        result = validate_query(spark, query_info)
        query_duration = time.time() - query_start
        result['duration_sec'] = round(query_duration, 2)
        results.append(result)
        
        status = "✓" if result['valid'] else "✗"
        duration_str = f"({query_duration:.1f}s)" if query_duration > 1 else ""
        print(f"  [{i+1}/{len(all_queries)}] {status} {query_info['dashboard']}.{query_info['dataset']} {duration_str}")
        
        if not result['valid']:
            failed_queries.append(result)
    
    total_duration = time.time() - start_time
    print(f"\n⏱️ Total validation time: {total_duration:.1f} seconds")
    
    # Generate report
    report = generate_validation_report(results)
    print("\n" + report)
    
    # Count failures
    invalid_count = sum(1 for r in results if not r['valid'])
    
    if invalid_count > 0:
        print(f"\n❌ VALIDATION FAILED: {invalid_count} queries have errors")
        print("Fix the errors above before deploying the dashboard.")
        
        # Print detailed errors for each failed query
        print("\n" + "=" * 80)
        print("DETAILED ERROR LIST (for easy debugging)")
        print("=" * 80)
        
        for r in results:
            if not r['valid']:
                print(f"\n🔴 FAILED: {r['dashboard']}.lvdash.json -> {r['dataset']}")
                print(f"   Error Type: {r.get('error_type', 'UNKNOWN')}")
                if 'error_column' in r:
                    print(f"   Column: {r['error_column']}")
                if 'suggestions' in r:
                    print(f"   Suggestions: {r['suggestions']}")
                if 'missing_table' in r:
                    print(f"   Missing Table: {r['missing_table']}")
                if 'error_near' in r:
                    print(f"   Error Near: {r['error_near']}")
                print(f"   Full Error: {str(r.get('error', ''))[:500]}")
        
        print("\n" + "=" * 80)
        
        # Create a summary file
        summary = {
            'total': len(results),
            'valid': len(results) - invalid_count,
            'invalid': invalid_count,
            'errors': [r for r in results if not r['valid']]
        }
        
        # Output summary as JSON for programmatic use
        print("\n=== ERROR SUMMARY JSON ===")
        error_json = json.dumps(summary, indent=2, default=str)
        print(error_json[:10000])  # Print more for debugging
        
        # Save errors to a file for easier retrieval
        error_file_path = "/Workspace/Users/prashanth.subrahmanyam@databricks.com/.bundle/databricks_health_monitor/dev/files/validation_errors.json"
        try:
            with open(error_file_path, 'w') as f:
                f.write(error_json)
            print(f"\n📁 Errors saved to: {error_file_path}")
        except Exception as e:
            print(f"Could not save errors to file: {e}")
        
        # Exit with error summary so it's captured in API response
        dbutils.notebook.exit(json.dumps({
            "status": "FAILED",
            "invalid_count": invalid_count,
            "errors": [
                {
                    "dashboard": r['dashboard'],
                    "dataset": r['dataset'],
                    "error_type": r.get('error_type'),
                    "error_column": r.get('error_column'),
                    "suggestions": r.get('suggestions'),
                    "missing_table": r.get('missing_table'),
                    "error_near": r.get('error_near'),
                    "error": str(r.get('error', ''))[:300]
                }
                for r in results if not r['valid']
            ]
        }, default=str)[:30000])
    
    print("\n✅ VALIDATION PASSED: All queries are valid!")
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()

