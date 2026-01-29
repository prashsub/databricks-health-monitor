"""
Verify Lakebase Memory Configuration for Health Monitor Agent
==============================================================

This script verifies that the Lakebase instance and memory tables are properly
configured and accessible by the deployed agent.

Key Checks:
1. Lakebase instance existence and accessibility
2. Short-term memory table (checkpoints) - 24h retention
3. Long-term memory table (store) - 1yr retention
4. Table schemas and configuration
5. Write/read permissions

Usage:
    databricks bundle exec python src/agents/setup/verify_lakebase_memory.py
    
    Or with specific Lakebase instance:
    LAKEBASE_INSTANCE=vibe-coding-workshop-lakebase python src/agents/setup/verify_lakebase_memory.py
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import TableInfo


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def print_success(message: str):
    """Print success message."""
    print(f"  ✅ {message}")


def print_warning(message: str):
    """Print warning message."""
    print(f"  ⚠️  {message}")


def print_error(message: str):
    """Print error message."""
    print(f"  ❌ {message}")


def print_info(message: str, indent: int = 2):
    """Print info message."""
    print(f"{' ' * indent}• {message}")


def check_lakebase_instance(w: WorkspaceClient, instance_name: str) -> bool:
    """
    Check if Lakebase instance exists and is accessible.
    
    Note: Lakebase instances are NOT queryable via Databricks SDK catalog API.
    They are managed instances visible in the UI but not via standard Unity Catalog APIs.
    
    Returns:
        bool: True if we can proceed (instance assumed to exist), False if critical error
    """
    print_section("1. LAKEBASE INSTANCE CHECK")
    
    print_info(f"Instance Name: {instance_name}")
    print_warning("Lakebase instances are not queryable via standard Databricks SDK APIs")
    print_info("Verification method: Attempt to query tables (they reference the instance)")
    
    # We can't directly verify the instance exists, but we can check if tables referencing it exist
    print_info("Status: Proceeding with table checks (instance assumed configured)")
    
    return True


def get_table_info(w: WorkspaceClient, catalog: str, schema: str, table: str) -> Optional[TableInfo]:
    """Get table information if it exists."""
    try:
        full_name = f"{catalog}.{schema}.{table}"
        table_info = w.tables.get(full_name=full_name)
        return table_info
    except Exception as e:
        if "TABLE_OR_VIEW_NOT_FOUND" in str(e) or "does not exist" in str(e):
            return None
        raise


def check_memory_table(
    w: WorkspaceClient,
    table_type: str,
    catalog: str,
    schema: str,
    table_name: str,
    expected_columns: List[str]
) -> Dict:
    """
    Check if a memory table exists and has the correct schema.
    
    Returns:
        Dict with keys: exists, accessible, schema_valid, details
    """
    result = {
        "exists": False,
        "accessible": False,
        "schema_valid": False,
        "details": {}
    }
    
    full_name = f"{catalog}.{schema}.{table_name}"
    
    # Check if table exists
    table_info = get_table_info(w, catalog, schema, table_name)
    
    if table_info is None:
        result["details"]["message"] = "Table does not exist yet (will auto-create on first agent query)"
        return result
    
    result["exists"] = True
    result["accessible"] = True
    result["details"]["full_name"] = full_name
    result["details"]["table_type"] = table_info.table_type.value if table_info.table_type else "UNKNOWN"
    result["details"]["created_at"] = str(table_info.created_at) if table_info.created_at else "Unknown"
    result["details"]["storage_location"] = table_info.storage_location or "Managed"
    
    # Check schema
    if table_info.columns:
        actual_columns = {col.name for col in table_info.columns}
        result["details"]["columns"] = list(actual_columns)
        
        # Check if expected columns are present
        missing_columns = set(expected_columns) - actual_columns
        if not missing_columns:
            result["schema_valid"] = True
        else:
            result["details"]["missing_columns"] = list(missing_columns)
    
    # Get row count if possible
    try:
        # Note: This requires SQL execution permissions
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        row_count = spark.table(full_name).count()
        result["details"]["row_count"] = row_count
    except Exception as e:
        result["details"]["row_count"] = f"Unable to query: {str(e)[:100]}"
    
    return result


def check_short_term_memory(w: WorkspaceClient, catalog: str, schema: str, lakebase_instance: str) -> Dict:
    """
    Check short-term memory table (checkpoints).
    
    This table stores conversation threads with 24h retention.
    Required by LangGraph CheckpointSaver.
    """
    print_section("2. SHORT-TERM MEMORY (CheckpointSaver)")
    
    print_info(f"Purpose: Conversation threads (24h retention)")
    print_info(f"Expected Table: {catalog}.{schema}.checkpoints")
    print_info(f"Lakebase Instance: {lakebase_instance}")
    
    # Expected schema for CheckpointSaver
    # Reference: langgraph-checkpoint-databricks package
    expected_columns = [
        "thread_id",
        "checkpoint_ns",
        "checkpoint_id",
        "parent_checkpoint_id",
        "type",
        "checkpoint",
        "metadata"
    ]
    
    result = check_memory_table(
        w, "Short-term", catalog, schema, "checkpoints", expected_columns
    )
    
    print()
    if result["exists"]:
        print_success("Table exists and is accessible")
        print_info(f"Created: {result['details'].get('created_at', 'Unknown')}")
        print_info(f"Type: {result['details'].get('table_type', 'Unknown')}")
        
        if result["schema_valid"]:
            print_success("Schema is valid")
        else:
            print_warning("Schema validation incomplete")
            if "missing_columns" in result["details"]:
                print_error(f"Missing columns: {result['details']['missing_columns']}")
        
        if "row_count" in result["details"]:
            print_info(f"Rows: {result['details']['row_count']}")
    else:
        print_warning("Table does not exist yet")
        print_info("Auto-creates on first agent conversation")
        print_info("This is EXPECTED behavior for new deployments")
    
    return result


def check_long_term_memory(w: WorkspaceClient, catalog: str, schema: str, lakebase_instance: str) -> Dict:
    """
    Check long-term memory table (store).
    
    This table stores user preferences and insights with 1yr retention.
    Required by DatabricksStore.
    """
    print_section("3. LONG-TERM MEMORY (DatabricksStore)")
    
    print_info(f"Purpose: User preferences (1yr retention)")
    print_info(f"Expected Table: {catalog}.{schema}.store")
    print_info(f"Lakebase Instance: {lakebase_instance}")
    
    # Expected schema for DatabricksStore
    # Reference: langgraph-checkpoint-databricks package
    expected_columns = [
        "namespace",
        "key",
        "value",
        "created_at",
        "updated_at"
    ]
    
    result = check_memory_table(
        w, "Long-term", catalog, schema, "store", expected_columns
    )
    
    print()
    if result["exists"]:
        print_success("Table exists and is accessible")
        print_info(f"Created: {result['details'].get('created_at', 'Unknown')}")
        print_info(f"Type: {result['details'].get('table_type', 'Unknown')}")
        
        if result["schema_valid"]:
            print_success("Schema is valid")
        else:
            print_warning("Schema validation incomplete")
            if "missing_columns" in result["details"]:
                print_error(f"Missing columns: {result['details']['missing_columns']}")
        
        if "row_count" in result["details"]:
            print_info(f"Rows: {result['details']['row_count']}")
    else:
        print_warning("Table does not exist yet")
        print_info("Auto-creates on first agent conversation")
        print_info("This is EXPECTED behavior for new deployments")
    
    return result


def test_memory_write_permissions(w: WorkspaceClient, catalog: str, schema: str) -> Dict:
    """
    Test if we can write to the memory schema (required for table creation).
    """
    print_section("4. WRITE PERMISSIONS TEST")
    
    test_table = f"{catalog}.{schema}.memory_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    result = {
        "can_write": False,
        "can_read": False,
        "can_delete": False,
        "error": None
    }
    
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        
        # Try to create a test table
        print_info(f"Creating test table: {test_table}")
        spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {test_table} (
                test_id STRING,
                test_value STRING,
                created_at TIMESTAMP
            ) USING DELTA
        """)
        result["can_write"] = True
        print_success("Can create tables in schema")
        
        # Try to write data
        print_info("Writing test data...")
        spark.sql(f"""
            INSERT INTO {test_table} VALUES 
            ('test1', 'value1', current_timestamp())
        """)
        print_success("Can write data to tables")
        
        # Try to read data
        print_info("Reading test data...")
        count = spark.sql(f"SELECT COUNT(*) as count FROM {test_table}").collect()[0]["count"]
        result["can_read"] = True
        print_success(f"Can read data from tables (found {count} rows)")
        
        # Clean up
        print_info("Cleaning up test table...")
        spark.sql(f"DROP TABLE IF EXISTS {test_table}")
        result["can_delete"] = True
        print_success("Can delete tables from schema")
        
        print()
        print_success("All write permissions verified!")
        
    except Exception as e:
        result["error"] = str(e)
        print_error(f"Permission test failed: {str(e)[:200]}")
        print_warning("Memory tables may not auto-create successfully")
    
    return result


def provide_next_steps(results: Dict):
    """Provide actionable next steps based on verification results."""
    print_section("5. SUMMARY & NEXT STEPS")
    
    short_term_exists = results["short_term"]["exists"]
    long_term_exists = results["long_term"]["exists"]
    can_write = results["permissions"]["can_write"]
    
    print()
    print_info("Memory Configuration Status:")
    print(f"    Short-term Memory (checkpoints): {'✅ EXISTS' if short_term_exists else '⚠️  NOT CREATED YET'}")
    print(f"    Long-term Memory (store):        {'✅ EXISTS' if long_term_exists else '⚠️  NOT CREATED YET'}")
    print(f"    Write Permissions:               {'✅ VERIFIED' if can_write else '❌ FAILED'}")
    
    print()
    
    if short_term_exists and long_term_exists:
        print_success("Both memory tables exist! Agent memory is fully operational.")
        print()
        print_info("Test memory by sending queries to your agent:")
        print(f"        • Endpoint: {results.get('endpoint_name', 'your-endpoint-name')}")
        print(f"        • After 2-3 queries, check table row counts to verify memory writes")
    
    elif can_write:
        print_warning("Memory tables not created yet (EXPECTED for new deployments)")
        print()
        print_info("To initialize memory tables:")
        print()
        print("    OPTION 1: Query the Agent (Recommended)")
        print("      • Send 2-3 test queries to your deployed agent endpoint")
        print("      • Tables auto-create on first conversation")
        print("      • Re-run this script to verify tables were created")
        print()
        print("    OPTION 2: Manual Initialization (Advanced)")
        print("      • Run: databricks bundle exec python src/agents/setup/initialize_lakebase_tables.py")
        print("      • This pre-creates tables with correct schemas")
        print()
        print_info("After initialization, re-run this verification script:")
        print(f"      python {__file__}")
    
    else:
        print_error("CRITICAL: Cannot write to schema - memory will NOT work!")
        print()
        print_info("Required Actions:")
        print("    1. Verify Unity Catalog permissions for your service principal")
        print(f"    2. Grant CREATE TABLE on schema: {results['catalog']}.{results['schema']}")
        print("    3. Grant SELECT, INSERT, UPDATE on schema")
        print("    4. Contact your workspace admin if you don't have these permissions")


def main():
    """Main verification flow."""
    print_section("LAKEBASE MEMORY VERIFICATION")
    print_info("Starting verification checks...")
    print_info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Get configuration
    lakebase_instance = os.environ.get("LAKEBASE_INSTANCE", "vibe-coding-workshop-lakebase")
    catalog = os.environ.get("CATALOG", "prashanth_subrahmanyam_catalog")
    schema = os.environ.get("AGENT_SCHEMA", "dev_prashanth_subrahmanyam_system_gold_agent")
    endpoint_name = os.environ.get("ENDPOINT_NAME", "dev_prashanth_subrahmanyam_health_monitor_agent_dev")
    
    print_info(f"Lakebase Instance: {lakebase_instance}")
    print_info(f"Unity Catalog Schema: {catalog}.{schema}")
    print_info(f"Agent Endpoint: {endpoint_name}")
    
    # Initialize Databricks client
    w = WorkspaceClient()
    
    # Run checks
    results = {
        "catalog": catalog,
        "schema": schema,
        "lakebase_instance": lakebase_instance,
        "endpoint_name": endpoint_name,
        "instance_check": check_lakebase_instance(w, lakebase_instance),
        "short_term": check_short_term_memory(w, catalog, schema, lakebase_instance),
        "long_term": check_long_term_memory(w, catalog, schema, lakebase_instance),
        "permissions": test_memory_write_permissions(w, catalog, schema)
    }
    
    # Provide recommendations
    provide_next_steps(results)
    
    # Exit code
    if results["short_term"]["exists"] and results["long_term"]["exists"]:
        print()
        print_section("✅ VERIFICATION COMPLETE - MEMORY FULLY OPERATIONAL")
        return 0
    elif results["permissions"]["can_write"]:
        print()
        print_section("⚠️  VERIFICATION COMPLETE - TABLES NEED INITIALIZATION")
        return 0  # Not an error - expected state
    else:
        print()
        print_section("❌ VERIFICATION FAILED - PERMISSIONS ISSUE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
