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
) -> Tuple[int, int, List[str]]:
    """
    Deploy all TVFs from a single SQL file.

    Args:
        spark: SparkSession
        file_path: Path to SQL file
        variables: Variable substitutions

    Returns:
        Tuple of (success_count, error_count, error_messages)
    """
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print(f"{'='*60}")

    # Read file content from workspace
    try:
        sql_content = read_workspace_file(file_path)
    except Exception as e:
        return 0, 1, [f"Failed to read file: {e}"]

    # Substitute variables
    sql_content = substitute_variables(sql_content, variables)

    # Extract individual statements
    statements = extract_tvf_statements(sql_content)
    print(f"Found {len(statements)} TVF statements")

    success_count = 0
    error_count = 0
    errors = []

    for stmt in statements:
        func_name = extract_function_name(stmt)
        print(f"\n  Creating: {func_name}")

        try:
            spark.sql(stmt)
            print(f"  ✓ Success: {func_name}")
            success_count += 1
        except Exception as e:
            error_msg = f"{func_name}: {str(e)[:200]}"
            print(f"  ✗ Error: {error_msg}")
            errors.append(error_msg)
            error_count += 1

    return success_count, error_count, errors

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
    print(f"\n{'='*60}")
    print("Verifying Deployed TVFs")
    print(f"{'='*60}")

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

        print(f"\nFound {len(tvfs)} functions in {catalog}.{schema}:")
        for row in tvfs:
            print(f"  - {row['routine_name']}")

        return [row.asDict() for row in tvfs]

    except Exception as e:
        print(f"Warning: Could not verify TVFs: {e}")
        return []

# COMMAND ----------

def main():
    """Main entry point for TVF deployment."""
    print("\n" + "=" * 80)
    print("DEPLOYING TABLE-VALUED FUNCTIONS (TVFs)")
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
        print(f"Notebook path: {notebook_path}")
    except Exception as e:
        # Fall back to relative path for local testing
        print(f"Could not get notebook path: {e}")
        base_path = os.path.dirname(os.path.abspath(__file__))

    print(f"\nBase path: {base_path}")

    # List TVF files
    tvf_files = list_tvf_files(base_path)
    print(f"Found {len(tvf_files)} TVF files to process")

    # Deploy each file
    total_success = 0
    total_errors = 0
    all_errors = []

    for file_path in tvf_files:
        success, errors, error_msgs = deploy_tvf_file(spark, file_path, variables)
        total_success += success
        total_errors += errors
        all_errors.extend(error_msgs)

    # Summary
    print("\n" + "=" * 80)
    print("DEPLOYMENT SUMMARY")
    print("=" * 80)
    print(f"✓ Successful: {total_success}")
    print(f"✗ Failed: {total_errors}")

    if all_errors:
        print("\nErrors:")
        for err in all_errors:
            print(f"  - {err}")

    # Verify deployment
    verified = verify_tvfs(spark, catalog, gold_schema)

    print("\n" + "=" * 80)
    if total_errors == 0:
        print("✓ TVF DEPLOYMENT COMPLETE - ALL SUCCESSFUL")
        dbutils.notebook.exit("SUCCESS")
    else:
        print(f"⚠ TVF DEPLOYMENT COMPLETE WITH {total_errors} ERRORS")
        dbutils.notebook.exit(f"PARTIAL: {total_success} success, {total_errors} errors")
    print("=" * 80)

# COMMAND ----------

if __name__ == "__main__":
    main()
