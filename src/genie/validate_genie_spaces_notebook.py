# Databricks notebook source
"""
Genie Space Benchmark SQL Validation Notebook

Validates SQL queries in Genie Space benchmark sections before deployment by:
1. EXECUTING each query with LIMIT 1 (catches all errors)
2. Validating SQL syntax, column resolution, table existence
3. Checking function calls (TVFs, MEASURE())
4. Catching runtime errors (type mismatches, NULL handling, etc.)
5. Detecting ambiguous references and logic errors

Why EXECUTE instead of EXPLAIN:
- EXPLAIN may miss runtime errors (type mismatches, NULL handling)
- LIMIT 1 catches ALL errors while being fast (returns only 1 row)
- Full execution path ensures queries work identically in production

Output:
- Detailed error logs printed to stdout for troubleshooting
- Fails the job if any validation errors found
- NO TABLE STORAGE - All results printed to logs only

Typical runtime: ~2-3 minutes for 150+ queries
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
    """Main validation function with detailed error logging.
    
    Returns:
        tuple: (success: bool, results: list, stats: dict)
    """

    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()

    print("\n" + "=" * 80)
    print("GENIE SPACE BENCHMARK SQL VALIDATOR - EXECUTING QUERIES WITH LIMIT 1")
    print("=" * 80)
    print(f"Genie Space directory: {genie_dir}")
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature/ML Schema: {feature_schema}")
    print(f"\n🚀 Mode: EXECUTE queries with LIMIT 1 (full validation)")
    print(f"   This catches syntax, column, type, and runtime errors")
    print("")

    # Validate all benchmark queries
    success, results = validate_all_genie_benchmarks(genie_dir, catalog, gold_schema, spark, feature_schema)

    if not success:
        invalid_count = sum(1 for r in results if not r['valid'])
        valid_count = len(results) - invalid_count

        print("\n" + "=" * 80)
        print("❌ VALIDATION FAILED - DETAILED ERROR LOG")
        print("=" * 80)
        print(f"Total queries validated: {len(results)}")
        print(f"✅ Valid: {valid_count}")
        print(f"❌ Invalid: {invalid_count}")
        print("")

        # Group errors by Genie Space for easier fixing
        errors_by_space = {}
        for r in results:
            if not r['valid']:
                space = r['genie_space']
                if space not in errors_by_space:
                    errors_by_space[space] = []
                errors_by_space[space].append(r)

        # Print error summary by Genie Space
        print("=" * 80)
        print("ERROR SUMMARY BY GENIE SPACE")
        print("=" * 80)
        for space, errors in sorted(errors_by_space.items()):
            print(f"  {space}: {len(errors)} errors")
        print("")

        # Print error summary by error type
        error_type_counts = {}
        for r in results:
            if not r['valid']:
                et = r.get('error_type', 'UNKNOWN')
                error_type_counts[et] = error_type_counts.get(et, 0) + 1
        
        print("=" * 80)
        print("ERROR SUMMARY BY TYPE")
        print("=" * 80)
        for et, count in sorted(error_type_counts.items(), key=lambda x: -x[1]):
            print(f"  {et}: {count} queries")
        print("")

        # Print ALL errors with FULL details for troubleshooting
        print("=" * 80)
        print("DETAILED ERROR LOG - COPY THIS FOR DEBUGGING")
        print("=" * 80)
        
        for space, errors in sorted(errors_by_space.items()):
            print(f"\n{'▼' * 80}")
            print(f"GENIE SPACE: {space.upper()} ({len(errors)} errors)")
            print(f"{'▼' * 80}\n")

            for idx, err in enumerate(errors, 1):
                print(f"─── ERROR {idx}/{len(errors)} ───────────────────────────────────────────────")
                print(f"Question Number: {err['question_num']}")
                print(f"Question Text: {err.get('question_text', 'N/A')}")
                print(f"Error Type: {err.get('error_type', 'UNKNOWN')}")
                print("")

                # Print specific error details based on type
                if err.get('error_type') == 'COLUMN_NOT_FOUND':
                    print(f"🔍 MISSING COLUMN:")
                    print(f"   Column Name: {err.get('error_column', 'unknown')}")
                    if 'suggestions' in err:
                        print(f"   Did you mean: {err['suggestions']}")
                    print(f"\n💡 FIX: Add column to table or fix column name in JSON export")
                    
                elif err.get('error_type') == 'TABLE_NOT_FOUND':
                    print(f"🔍 MISSING TABLE/VIEW:")
                    print(f"   Table Name: {err.get('missing_table', 'unknown')}")
                    print(f"\n💡 FIX: Deploy missing table/view or fix table name in JSON export")
                    
                elif err.get('error_type') == 'FUNCTION_NOT_FOUND':
                    print(f"🔍 MISSING FUNCTION:")
                    print(f"   Function Name: {err.get('missing_function', 'unknown')}")
                    print(f"\n💡 FIX: Deploy missing TVF or fix function name/signature in JSON export")
                    
                elif err.get('error_type') == 'AMBIGUOUS_COLUMN':
                    print(f"🔍 AMBIGUOUS COLUMN:")
                    print(f"   Column Name: {err.get('error_column', 'unknown')}")
                    print(f"\n💡 FIX: Qualify column with table alias (e.g., table.column)")
                    
                elif err.get('error_type') == 'SYNTAX_ERROR':
                    print(f"🔍 SQL SYNTAX ERROR:")
                    print(f"   Error Near: {err.get('error_near', 'unknown')}")
                    print(f"\n💡 FIX: Check SQL syntax in JSON export")
                
                else:
                    print(f"🔍 OTHER ERROR:")
                    print(f"\n💡 FIX: Review full error message below")

                # Print FULL error message (not truncated)
                print(f"\n📄 FULL ERROR MESSAGE:")
                full_error = str(err.get('error', 'No error message'))
                print(f"{full_error}")
                print("")

        print("=" * 80)
        print("END OF DETAILED ERROR LOG")
        print("=" * 80)
        print(f"\n💡 TIP: Search for specific error types above to focus debugging")
        print(f"💡 TIP: Most errors are fixable by updating JSON export files")
        print(f"💡 TIP: COLUMN_NOT_FOUND: Check column names against deployed tables")
        print(f"💡 TIP: TABLE_NOT_FOUND: Deploy missing assets first")
        print(f"💡 TIP: FUNCTION_NOT_FOUND: Check TVF names and signatures")
        print("")

        # Build concise summary for exception message
        error_summary_lines = []
        for space, errors in sorted(errors_by_space.items()):
            for err in errors[:3]:  # First 3 errors per space
                error_type = err.get('error_type', 'UNKNOWN')
                if err.get('error_type') == 'COLUMN_NOT_FOUND':
                    detail = f"column={err.get('error_column', '?')}"
                elif err.get('error_type') == 'TABLE_NOT_FOUND':
                    detail = f"table={err.get('missing_table', '?')}"
                elif err.get('error_type') == 'FUNCTION_NOT_FOUND':
                    detail = f"function={err.get('missing_function', '?')}"
                else:
                    # Show full error message for OTHER types (was truncated to 50 chars)
                    detail = str(err.get('error', ''))[:200]  # Increased to 200 chars
                error_summary_lines.append(f"  • {space} Q{err['question_num']}: {error_type} ({detail})")
            
            if len(errors) > 3:
                error_summary_lines.append(f"  • ... and {len(errors) - 3} more in {space}")

        # Build stats for return
        stats = {
            'total': len(results),
            'valid': valid_count,
            'invalid': invalid_count,
            'errors_by_space': {space: len(errors) for space, errors in errors_by_space.items()},
            'errors_by_type': error_type_counts,
            'error_summary': error_summary_lines
        }
        
        return False, results, stats

    # All queries passed!
    print("\n" + "=" * 80)
    print("✅ VALIDATION PASSED - ALL QUERIES EXECUTED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\nTotal queries validated: {len(results)}")
    print(f"✅ All {len(results)} benchmark queries executed with LIMIT 1")
    print(f"\n🚀 Genie Spaces are ready for deployment!")
    print(f"   No errors found. All queries execute correctly.")
    print("=" * 80)
    print("")
    
    # Build success stats
    stats = {
        'total': len(results),
        'valid': len(results),
        'invalid': 0,
        'errors_by_space': {},
        'errors_by_type': {}
    }
    
    return True, results, stats

# COMMAND ----------

# Execute validation
validation_success, validation_results, validation_stats = main()

# COMMAND ----------

# Notebook Exit - Separate cell for debugging
print("\n" + "=" * 80)
print("VALIDATION COMPLETE - PREPARING NOTEBOOK EXIT")
print("=" * 80)
print(f"\n📊 Validation Summary:")
print(f"   Total queries: {validation_stats['total']}")
print(f"   Valid: {validation_stats['valid']}")
print(f"   Invalid: {validation_stats['invalid']}")

if validation_success:
    print(f"\n✅ STATUS: SUCCESS")
    print(f"   All {validation_stats['total']} queries executed without errors")
    print(f"   Ready for Genie Space deployment")
    print("")
    print("=" * 80)
    dbutils.notebook.exit("SUCCESS")
else:
    print(f"\n❌ STATUS: FAILED")
    print(f"   {validation_stats['invalid']} queries have errors")
    print(f"\n🔍 Error Breakdown by Genie Space:")
    for space, count in validation_stats['errors_by_space'].items():
        print(f"     • {space}: {count} errors")
    print(f"\n🔍 Error Breakdown by Type:")
    for error_type, count in validation_stats['errors_by_type'].items():
        print(f"     • {error_type}: {count} errors")
    print("")
    print(f"💡 Review detailed error log above for fixing guidance")
    print(f"💡 Most common fixes:")
    print(f"   - COLUMN_NOT_FOUND: Update column names in JSON exports")
    print(f"   - TABLE_NOT_FOUND: Deploy missing tables/views first")
    print(f"   - FUNCTION_NOT_FOUND: Check TVF names and signatures")
    print("")
    error_msg = (
        f"❌ VALIDATION FAILED: {validation_stats['invalid']} of {validation_stats['total']} queries have errors\n\n"
        f"First errors:\n" + "\n".join(validation_stats.get('error_summary', []))
    )
    print("=" * 80)
    raise Exception(error_msg)
