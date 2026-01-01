# Databricks notebook source
# MAGIC %md
# MAGIC # Dashboard SQL Query Validator
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
        
        # Replace parameters with default values for validation
        # :param_name -> 'All' or default value
        query = re.sub(r':time_window', "'Last 30 Days'", query)
        query = re.sub(r':workspace_filter', "'All'", query)
        query = re.sub(r':sku_type', "'All'", query)
        query = re.sub(r':compute_type', "'All'", query)
        query = re.sub(r':job_status', "'All'", query)
        query = re.sub(r':annual_commit', "1000000", query)
        query = re.sub(r':time_key', "'Day'", query)
        query = re.sub(r':\w+', "'All'", query)  # Catch any remaining parameters
        
        queries.append({
            'dashboard': dashboard_name,
            'dataset': ds_name,
            'query': query,
            'original_query': dataset.get('query', '')
        })
    
    return queries

# COMMAND ----------

def validate_query(spark: SparkSession, query_info: Dict) -> Dict:
    """Validate a single SQL query by explaining it (doesn't execute)."""
    
    result = {
        'dashboard': query_info['dashboard'],
        'dataset': query_info['dataset'],
        'valid': False,
        'error': None,
        'error_type': None
    }
    
    try:
        # Use EXPLAIN to validate without executing
        # This catches syntax and column resolution errors
        spark.sql(f"EXPLAIN {query_info['query']}")
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
    
    print(f"\n🔍 Validating {len(all_queries)} queries...")
    print("-" * 80)
    
    # Validate each query
    results = []
    for i, query_info in enumerate(all_queries):
        result = validate_query(spark, query_info)
        results.append(result)
        
        status = "✓" if result['valid'] else "✗"
        print(f"  [{i+1}/{len(all_queries)}] {status} {query_info['dashboard']}.{query_info['dataset']}")
    
    # Generate report
    report = generate_validation_report(results)
    print("\n" + report)
    
    # Count failures
    invalid_count = sum(1 for r in results if not r['valid'])
    
    if invalid_count > 0:
        print(f"\n❌ VALIDATION FAILED: {invalid_count} queries have errors")
        print("Fix the errors above before deploying the dashboard.")
        
        # Create a summary file
        summary = {
            'total': len(results),
            'valid': len(results) - invalid_count,
            'invalid': invalid_count,
            'errors': [r for r in results if not r['valid']]
        }
        
        # Output summary as JSON for programmatic use
        print("\n=== ERROR SUMMARY JSON ===")
        print(json.dumps(summary, indent=2, default=str)[:5000])
        
        raise RuntimeError(f"Dashboard validation failed: {invalid_count} queries have errors")
    
    print("\n✅ VALIDATION PASSED: All queries are valid!")
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()

