#!/usr/bin/env python3
"""
Test if TVFs exist and are callable in the catalog.
This helps diagnose NOT_A_SCALAR_FUNCTION errors.
"""

import subprocess
import json

def main():
    catalog = "prashanth_subrahmanyam_catalog"
    gold_schema = "dev_prashanth_subrahmanyam_system_gold"
    
    # Test query: Try to call get_slow_queries with TABLE() wrapper
    test_sql = f"""
    SELECT * FROM TABLE({catalog}.{gold_schema}.get_slow_queries(
        '2026-01-01',
        '2026-01-07',
        30,
        10
    ))
    LIMIT 1
    """
    
    print("=" * 80)
    print("Testing TVF Existence")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Schema: {gold_schema}")
    print(f"TVF: get_slow_queries")
    print("\nTest SQL:")
    print(test_sql)
    print("=" * 80)
    
    # First, check if function exists using DESCRIBE FUNCTION
    describe_sql = f"DESCRIBE FUNCTION {catalog}.{gold_schema}.get_slow_queries"
    
    print("\n--- Step 1: Check if function exists ---")
    print(f"SQL: {describe_sql}")
    
    # Create a simple SQL file
    with open("/tmp/test_tvf.sql", "w") as f:
        f.write(describe_sql)
    
    # Use workspace-cli or check via API
    # Simpler approach: use Python Databricks SDK
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.sql import StatementState
        
        w = WorkspaceClient(profile="health_monitor")
        
        # Execute DESCRIBE FUNCTION
        print("Executing via Databricks SDK...")
        result = w.statement_execution.execute_statement(
            warehouse_id="4b9b953939869799",
            statement=describe_sql,
            wait_timeout="30s"
        )
        
        print("\n=== RESULT ===")
        if result.status.state == StatementState.SUCCEEDED:
            print("✅ SUCCESS: Function exists!")
            if result.result:
                print("\nFunction Details:")
                print(result.result.data_array)
        else:
            print(f"❌ FAILED: {result.status.state}")
            if result.status.error:
                print(f"Error: {result.status.error.message}")
        
        # Now try to call it with TABLE() wrapper
        print("\n--- Step 2: Test TVF call with TABLE() wrapper ---")
        result2 = w.statement_execution.execute_statement(
            warehouse_id="4b9b953939869799",
            statement=test_sql,
            wait_timeout="30s"
        )
        
        if result2.status.state == StatementState.SUCCEEDED:
            print("✅ SUCCESS: TVF call works!")
        else:
            print(f"❌ FAILED: TVF call failed")
            if result2.status.error:
                error_msg = result2.status.error.message
                print(f"Error: {error_msg}")
                
                # Check error type
                if "NOT_A_SCALAR_FUNCTION" in error_msg:
                    print("\n💡 Issue: TVF exists but Spark doesn't recognize TABLE() wrapper")
                    print("   This is the root cause of validation failures")
                elif "FUNCTION_NOT_FOUND" in error_msg:
                    print("\n💡 Issue: TVF doesn't exist in catalog")
                elif "TABLE_OR_VIEW_NOT_FOUND" in error_msg:
                    print("\n💡 Issue: Underlying table doesn't exist")
    
    except ImportError:
        print("❌ ERROR: databricks-sdk not installed")
        print("Install with: pip install databricks-sdk")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()

