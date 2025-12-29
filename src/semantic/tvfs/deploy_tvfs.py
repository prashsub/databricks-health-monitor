# Databricks notebook source
"""
Deploy Table-Valued Functions (TVFs)
=====================================

Deploys all TVFs to the specified catalog and schema organized by Agent Domain.

Agent Domain Organization:
--------------------------
| Domain      | File                    | TVFs | Primary Use Cases                    |
|-------------|-------------------------|------|--------------------------------------|
| 💰 Cost     | cost_tvfs.sql           | 15   | FinOps, chargeback, tag governance   |
| 🔄 Reliability | reliability_tvfs.sql  | 12   | Job failures, SLA, retries, costs    |
| ⚡ Performance | performance_tvfs.sql  | 10   | Query analysis, warehouse sizing     |
| ⚡ Performance | compute_tvfs.sql      | 6    | Cluster utilization, right-sizing    |
| 🔒 Security | security_tvfs.sql       | 10   | Audit, access patterns, compliance   |
| ✅ Quality  | quality_tvfs.sql        | 7    | Freshness, lineage, data governance  |

Usage:
    Run this notebook with parameters:
    - catalog: Target catalog name
    - gold_schema: Target schema name for TVFs

The script will:
1. Read all *_tvfs.sql files from the same directory
2. Substitute ${catalog} and ${gold_schema} variables
3. Execute each CREATE OR REPLACE FUNCTION statement
4. Report success/failure for each TVF

Total TVFs: 60 (aligned with 5 Agent Domains)
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")

    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")

    return catalog, gold_schema

# COMMAND ----------

def substitute_variables(sql_content: str, variables: Dict[str, str]) -> str:
    """
    Substitute ${variable} placeholders in SQL content.

    Args:
        sql_content: SQL string with ${variable} placeholders
        variables: Dictionary of variable name -> value

    Returns:
        SQL string with variables substituted
    """
    result = sql_content
    for var_name, var_value in variables.items():
        result = result.replace(f"${{{var_name}}}", var_value)
    return result


def extract_tvf_statements(sql_content: str) -> List[str]:
    """
    Extract individual CREATE OR REPLACE FUNCTION statements from SQL content.

    Args:
        sql_content: Full SQL file content

    Returns:
        List of individual CREATE statements
    """
    # Split on CREATE OR REPLACE FUNCTION, keeping the delimiter
    pattern = r'(CREATE\s+OR\s+REPLACE\s+FUNCTION)'
    parts = re.split(pattern, sql_content, flags=re.IGNORECASE)

    statements = []
    for i in range(1, len(parts), 2):
        # Combine the CREATE keyword with the following content
        if i + 1 < len(parts):
            stmt = parts[i] + parts[i + 1]
            # Clean up the statement
            stmt = stmt.strip()
            # Remove trailing comments and whitespace
            stmt = re.sub(r'\s*--.*$', '', stmt, flags=re.MULTILINE)
            if stmt:
                statements.append(stmt)

    return statements


def extract_function_name(statement: str) -> str:
    """Extract function name from CREATE FUNCTION statement."""
    match = re.search(
        r'CREATE\s+OR\s+REPLACE\s+FUNCTION\s+([^\s(]+)',
        statement,
        re.IGNORECASE
    )
    if match:
        return match.group(1)
    return "unknown"

# COMMAND ----------

def read_workspace_file(file_path: str) -> str:
    """
    Read file from Databricks workspace or local filesystem.
    
    In serverless notebooks, /Workspace paths are accessible via standard file I/O.
    
    Args:
        file_path: Path to file (e.g., /Workspace/... or local path)
        
    Returns:
        File content as string
    """
    # Method 1: Direct file read (works for /Workspace paths in serverless)
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e1:
        print(f"  Direct file read failed: {e1}")
    
    # Method 2: Try with dbutils.fs (DBFS paths)
    try:
        # For DBFS paths (dbfs:/ or /dbfs/)
        if 'dbfs' in file_path.lower():
            content = dbutils.fs.head(file_path, 1024 * 1024)  # Max 1MB
            return content
    except Exception as e2:
        print(f"  DBFS read failed: {e2}")
    
    # Method 3: Try Workspace API as last resort
    try:
        import base64
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        response = w.workspace.export(file_path, format="SOURCE")
        content = base64.b64decode(response.content).decode('utf-8')
        return content
    except Exception as e3:
        print(f"  Workspace API failed: {e3}")
    
    raise Exception(f"Cannot read file from any method: {file_path}")


def deploy_tvf_file(
    spark: SparkSession,
    file_path: str,
    variables: Dict[str, str]
) -> Tuple[int, int, List[Dict[str, str]]]:
    """
    Deploy all TVFs from a single SQL file.

    Args:
        spark: SparkSession
        file_path: Path to SQL file
        variables: Variable substitutions

    Returns:
        Tuple of (success_count, error_count, error_details_list)
    """
    file_name = os.path.basename(file_path)
    
    print(f"\n{'='*80}")
    print(f"📁 Processing File: {file_name}")
    print(f"   Full Path: {file_path}")
    print(f"{'='*80}")

    # Read file content from workspace
    try:
        sql_content = read_workspace_file(file_path)
        print(f"✓ Successfully read file ({len(sql_content)} bytes)")
    except Exception as e:
        error_detail = {
            'file': file_name,
            'tvf_name': 'FILE_READ_ERROR',
            'error': str(e),
            'category': 'FILE_ACCESS'
        }
        print(f"✗ CRITICAL: Failed to read file!")
        print(f"   Error: {str(e)}")
        return 0, 1, [error_detail]

    # Substitute variables
    sql_content = substitute_variables(sql_content, variables)
    print(f"✓ Variables substituted: catalog={variables['catalog']}, schema={variables['gold_schema']}")

    # Extract individual statements
    statements = extract_tvf_statements(sql_content)
    print(f"✓ Found {len(statements)} TVF CREATE statements in {file_name}")

    success_count = 0
    error_count = 0
    error_details = []

    print(f"\n{'─'*80}")
    print(f"Deploying TVFs from {file_name}...")
    print(f"{'─'*80}")

    for idx, stmt in enumerate(statements, 1):
        func_name = extract_function_name(stmt)
        print(f"\n[{idx}/{len(statements)}] Creating TVF: {func_name}")

        try:
            # Execute the CREATE statement
            spark.sql(stmt)
            print(f"      ✓ SUCCESS: {func_name} deployed")
            success_count += 1
            
        except Exception as e:
            error_str = str(e)
            error_count += 1
            
            # Categorize error
            if "already exists" in error_str.lower():
                error_category = "ALREADY_EXISTS"
            elif "syntax" in error_str.lower() or "parse" in error_str.lower():
                error_category = "SQL_SYNTAX"
            elif "table" in error_str.lower() or "column" in error_str.lower():
                error_category = "SCHEMA_MISMATCH"
            elif "permission" in error_str.lower() or "denied" in error_str.lower():
                error_category = "PERMISSION"
            else:
                error_category = "EXECUTION_ERROR"
            
            error_details.append({
                'file': file_name,
                'tvf_name': func_name,
                'error': error_str,
                'category': error_category
            })
            
            # Print detailed error
            print(f"      ✗ FAILED: {func_name}")
            print(f"         Category: {error_category}")
            print(f"         Error: {error_str[:500]}")  # Show first 500 chars
            
            # For schema mismatch, show the likely problematic line
            if error_category == "SCHEMA_MISMATCH":
                print(f"         Tip: Check if referenced table/column exists in Gold layer")
                # Extract table references from error
                table_match = re.search(r'(fact_|dim_)\w+', error_str)
                if table_match:
                    print(f"         Referenced table: {table_match.group()}")
            
            # For syntax errors, show snippet of problematic SQL
            if error_category == "SQL_SYNTAX":
                print(f"         SQL Preview: {stmt[:300]}...")

    print(f"\n{'─'*80}")
    print(f"File Summary: {file_name}")
    print(f"   ✓ Success: {success_count}")
    print(f"   ✗ Failed: {error_count}")
    print(f"{'─'*80}")

    return success_count, error_count, error_details

# COMMAND ----------

def list_tvf_files(base_path: str) -> List[str]:
    """
    List all TVF SQL files in the directory.

    Looks for files matching *_tvfs.sql pattern.
    """
    tvf_files = []

    # In Databricks, use dbutils.fs.ls for workspace files
    try:
        # Try local filesystem first (for testing)
        for f in os.listdir(base_path):
            if f.endswith('_tvfs.sql'):
                tvf_files.append(os.path.join(base_path, f))
    except Exception:
        # Fall back to hardcoded list for Databricks
        # Organized by Agent Domain for clear ownership
        tvf_files = [
            # 💰 COST AGENT (15 TVFs)
            # FinOps, chargeback, tag governance, commit tracking
            f"{base_path}/cost_tvfs.sql",
            
            # 🔄 RELIABILITY AGENT (12 TVFs)
            # Job failures, success rates, SLA compliance, retry costs
            f"{base_path}/reliability_tvfs.sql",
            
            # ⚡ PERFORMANCE AGENT - Queries (10 TVFs)
            # Query analysis, warehouse utilization, latency percentiles
            f"{base_path}/performance_tvfs.sql",
            
            # ⚡ PERFORMANCE AGENT - Compute (6 TVFs)
            # Cluster utilization, right-sizing, autoscaling, DBR versions
            f"{base_path}/compute_tvfs.sql",
            
            # 🔒 SECURITY AGENT (10 TVFs)
            # Audit trails, access patterns, compliance, anomaly detection
            f"{base_path}/security_tvfs.sql",
            
            # ✅ QUALITY AGENT (7 TVFs)
            # Data freshness, lineage, governance, orphaned tables
            f"{base_path}/quality_tvfs.sql",
        ]

    return tvf_files

# COMMAND ----------

def verify_tvfs(spark: SparkSession, catalog: str, schema: str) -> List[Dict]:
    """
    Verify deployed TVFs by querying information_schema.

    Returns list of TVF details.
    """
    print(f"\n{'='*80}")
    print("🔍 Verifying Deployed TVFs")
    print(f"{'='*80}")

    try:
        # Query information_schema.routines for functions
        result = spark.sql(f"""
            SELECT
                routine_name,
                routine_type,
                created,
                last_altered
            FROM {catalog}.information_schema.routines
            WHERE routine_schema = '{schema}'
                AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """)

        tvfs = result.collect()

        if tvfs:
            print(f"✓ Found {len(tvfs)} functions in {catalog}.{schema}")
            print(f"\n{'Function Name':<50} {'Created':<25} {'Last Modified':<25}")
            print("─" * 100)
            
            # Group by prefix for better organization
            tvf_by_prefix = {}
            for row in tvfs:
                name = row['routine_name']
                prefix = name.split('_')[0] if '_' in name else 'other'
                if prefix not in tvf_by_prefix:
                    tvf_by_prefix[prefix] = []
                tvf_by_prefix[prefix].append(row)
            
            # Print by prefix group
            for prefix in sorted(tvf_by_prefix.keys()):
                print(f"\n📁 {prefix.upper()} functions:")
                for row in tvf_by_prefix[prefix]:
                    created = str(row['created'])[:19] if row['created'] else 'N/A'
                    modified = str(row['last_altered'])[:19] if row['last_altered'] else 'N/A'
                    print(f"   {row['routine_name']:<47} {created:<25} {modified:<25}")
        else:
            print(f"⚠ No functions found in {catalog}.{schema}")
            print(f"   This could indicate:")
            print(f"   1. All TVF creations failed")
            print(f"   2. Schema doesn't exist")
            print(f"   3. Permission issues")

        return [row.asDict() for row in tvfs]

    except Exception as e:
        print(f"⚠ Warning: Could not verify TVFs")
        print(f"   Error: {str(e)}")
        print(f"   This is not critical, but manual verification recommended:")
        print(f"   SHOW FUNCTIONS IN {catalog}.{schema};")
        return []

# COMMAND ----------

def main():
    """Main entry point for TVF deployment."""
    print("\n" + "=" * 80)
    print("🚀 DEPLOYING TABLE-VALUED FUNCTIONS (TVFs)")
    print("=" * 80)

    # Get parameters
    catalog, gold_schema = get_parameters()

    # Set up variable substitutions
    variables = {
        "catalog": catalog,
        "gold_schema": gold_schema
    }

    # Get Spark session
    spark = SparkSession.builder.getOrCreate()

    # Determine base path (same directory as this script)
    # In Databricks serverless, workspace files are accessible at /Workspace/...
    try:
        # Get current notebook path and add /Workspace prefix
        notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        base_path = "/Workspace" + "/".join(notebook_path.split("/")[:-1])
        print(f"📍 Notebook path: {notebook_path}")
    except Exception as e:
        # Fall back to relative path for local testing
        print(f"⚠ Could not get notebook path: {e}")
        base_path = os.path.dirname(os.path.abspath(__file__))

    print(f"📁 Base path: {base_path}")
    print(f"🎯 Target: {catalog}.{gold_schema}")

    # List TVF files
    tvf_files = list_tvf_files(base_path)
    print(f"\n📋 Found {len(tvf_files)} TVF files to process:")
    for f in tvf_files:
        print(f"   - {os.path.basename(f)}")

    # Deploy each file
    total_success = 0
    total_errors = 0
    all_error_details = []
    file_results = []

    for file_path in tvf_files:
        success, errors, error_details = deploy_tvf_file(spark, file_path, variables)
        total_success += success
        total_errors += errors
        all_error_details.extend(error_details)
        
        file_results.append({
            'file': os.path.basename(file_path),
            'success': success,
            'errors': errors,
            'total': success + errors
        })

    # ========================================================================
    # DETAILED SUMMARY
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 80)
    
    # Per-file summary table
    print("\n📁 Results by File:")
    print(f"{'File':<30} {'Success':>10} {'Failed':>10} {'Total':>10} {'Status':>15}")
    print("─" * 80)
    
    for result in file_results:
        status = "✓ OK" if result['errors'] == 0 else f"✗ {result['errors']} ERRORS"
        print(f"{result['file']:<30} {result['success']:>10} {result['errors']:>10} {result['total']:>10} {status:>15}")
    
    print("─" * 80)
    print(f"{'TOTAL':<30} {total_success:>10} {total_errors:>10} {total_success + total_errors:>10}")
    print("=" * 80)

    # Error categorization
    if all_error_details:
        print("\n" + "=" * 80)
        print("❌ ERROR DETAILS")
        print("=" * 80)
        
        # Group by category
        errors_by_category = {}
        for err in all_error_details:
            category = err['category']
            if category not in errors_by_category:
                errors_by_category[category] = []
            errors_by_category[category].append(err)
        
        # Print by category
        for category, errors in sorted(errors_by_category.items()):
            print(f"\n📌 {category} ({len(errors)} errors):")
            print("─" * 80)
            for err in errors:
                print(f"   File: {err['file']}")
                print(f"   TVF:  {err['tvf_name']}")
                print(f"   Error: {err['error'][:500]}")
                print("   " + "─" * 76)
        
        # Failed TVF list
        print("\n" + "=" * 80)
        print("📝 FAILED TVF LIST")
        print("=" * 80)
        failed_tvfs = [err['tvf_name'] for err in all_error_details if err['tvf_name'] != 'FILE_READ_ERROR']
        for i, tvf in enumerate(failed_tvfs, 1):
            print(f"  {i:2d}. {tvf}")
        print("=" * 80)

    # Verify deployment
    verified_tvfs = verify_tvfs(spark, catalog, gold_schema)
    
    # Comparison: Expected vs Deployed
    expected_count = total_success + total_errors
    actual_count = len(verified_tvfs)
    
    print("\n" + "=" * 80)
    print("🔍 VERIFICATION")
    print("=" * 80)
    print(f"Expected TVFs:  {expected_count}")
    print(f"Deployed TVFs:  {actual_count}")
    print(f"Success Rate:   {(total_success / expected_count * 100):.1f}%" if expected_count > 0 else "N/A")
    
    # Final status
    print("\n" + "=" * 80)
    if total_errors == 0:
        print("✅ TVF DEPLOYMENT COMPLETE - ALL SUCCESSFUL")
        print("=" * 80)
        dbutils.notebook.exit("SUCCESS")
    else:
        print(f"⚠️  TVF DEPLOYMENT COMPLETED WITH ERRORS")
        print(f"   ✓ Successful: {total_success}")
        print(f"   ✗ Failed: {total_errors}")
        print(f"   Success Rate: {(total_success / (total_success + total_errors) * 100):.1f}%")
        print("=" * 80)
        print("\n⚠️  JOB WILL FAIL - Review errors above and fix the TVF SQL files")
        print("=" * 80)
        
        # Exit with error to fail the job
        raise Exception(
            f"TVF deployment failed: {total_errors} errors out of {total_success + total_errors} TVFs. "
            f"See detailed error log above. Failed TVFs: {', '.join(failed_tvfs[:10])}..."
        )

# COMMAND ----------

if __name__ == "__main__":
    main()
