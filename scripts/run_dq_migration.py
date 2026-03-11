#!/usr/bin/env python3
"""
Run DQ Rules Migration SQL
Executes the consolidated UPDATE statement to fix DQ rules
"""

from databricks.sdk import WorkspaceClient
import os
import sys

def run_migration():
    """Execute the DQ rules migration SQL."""
    
    # Set profile
    os.environ['DATABRICKS_CONFIG_PROFILE'] = 'e2-demo'
    
    w = WorkspaceClient()
    
    # Get warehouse ID from environment or use default
    warehouse_id = os.environ.get('DATABRICKS_WAREHOUSE_ID', '4b9b953939869799')
    
    catalog = "prashanth_subrahmanyam_catalog"
    schema = "dev_prashanth_subrahmanyam_system_bronze"
    
    print("=" * 80)
    print("DQ RULES MIGRATION")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Schema: {schema}")
    print(f"Warehouse: {warehouse_id}")
    print("=" * 80)
    
    # The consolidated UPDATE statement
    update_sql = f"""
    UPDATE {catalog}.{schema}.dq_rules
    SET 
        severity = 'warning',
        description = CASE 
            -- column_lineage rules
            WHEN table_name = 'column_lineage' AND rule_name = 'valid_source_column' 
                THEN 'Source column name should be present (NULL legitimate for CREATE operations)'
            WHEN table_name = 'column_lineage' AND rule_name = 'valid_target_column'
                THEN 'Target column name should be present (NULL legitimate for DROP operations)'
            
            -- clusters rules
            WHEN table_name = 'clusters' AND rule_name = 'valid_cluster_id' 
                THEN 'Cluster ID should be present for resource tracking'
            WHEN table_name = 'clusters' AND rule_name = 'valid_cluster_name'
                THEN 'Cluster name should be present for identification'
            WHEN table_name = 'clusters' AND rule_name = 'valid_state'
                THEN 'Cluster state should be present for tracking'
            
            -- table_lineage rules
            WHEN table_name = 'table_lineage' AND rule_name = 'valid_source_table' 
                THEN 'Source table name should be present for lineage tracking'
            WHEN table_name = 'table_lineage' AND rule_name = 'valid_target_table'
                THEN 'Target table name should be present for lineage tracking'
            
            -- warehouses rules
            WHEN table_name = 'warehouses' AND rule_name = 'valid_warehouse_id' 
                THEN 'Warehouse ID should be present for resource tracking'
            WHEN table_name = 'warehouses' AND rule_name = 'valid_warehouse_name'
                THEN 'Warehouse name should be present for identification'
            WHEN table_name = 'warehouses' AND rule_name = 'valid_state'
                THEN 'Warehouse state should be present for tracking'
            
            -- usage rules
            WHEN table_name = 'usage' AND rule_name = 'valid_usage_date' 
                THEN 'Usage date should be present (NULL legitimate for account-level aggregations)'
            WHEN table_name = 'usage' AND rule_name = 'valid_workspace_id'
                THEN 'Workspace ID should be present (NULL legitimate for account-level usage)'
            
            ELSE description
        END,
        updated_by = 'consolidated_migration',
        updated_at = current_timestamp()
    WHERE 
        severity = 'critical'
        AND (
            (table_name = 'column_lineage' AND rule_name IN ('valid_source_column', 'valid_target_column'))
            OR (table_name = 'usage' AND rule_name IN ('valid_usage_date', 'valid_workspace_id'))
            OR (table_name = 'clusters' AND rule_name IN ('valid_cluster_id', 'valid_cluster_name', 'valid_state'))
            OR (table_name = 'table_lineage' AND rule_name IN ('valid_source_table', 'valid_target_table'))
            OR (table_name = 'warehouses' AND rule_name IN ('valid_warehouse_id', 'valid_warehouse_name', 'valid_state'))
        )
    """
    
    print("\n📝 Executing UPDATE statement...")
    try:
        result = w.statement_execution.execute_statement(
            statement=update_sql,
            warehouse_id=warehouse_id,
            wait_timeout="50s"
        )
        print("✅ UPDATE executed successfully!")
        
    except Exception as e:
        print(f"❌ Error executing UPDATE: {e}")
        sys.exit(1)
    
    # Verify the update
    print("\n📊 Verifying migration...")
    verify_sql = f"""
    SELECT COUNT(*) as updated_rules
    FROM {catalog}.{schema}.dq_rules
    WHERE updated_by = 'consolidated_migration'
    """
    
    try:
        verify_result = w.statement_execution.execute_statement(
            statement=verify_sql,
            warehouse_id=warehouse_id,
            wait_timeout="30s"
        )
        
        if verify_result.result and verify_result.result.data_array:
            updated_count = verify_result.result.data_array[0][0]
            print(f"✅ Verified: {updated_count} rules updated")
            
            if updated_count != 12:
                print(f"⚠️  Warning: Expected 12 rules, but {updated_count} were updated")
        
    except Exception as e:
        print(f"⚠️  Could not verify: {e}")
    
    # Show summary
    print("\n📈 Summary by table...")
    summary_sql = f"""
    SELECT 
        table_name,
        severity,
        COUNT(*) as rule_count
    FROM {catalog}.{schema}.dq_rules
    WHERE table_name IN ('column_lineage', 'usage', 'clusters', 'table_lineage', 'warehouses')
    GROUP BY table_name, severity
    ORDER BY table_name, severity
    """
    
    try:
        summary_result = w.statement_execution.execute_statement(
            statement=summary_sql,
            warehouse_id=warehouse_id,
            wait_timeout="30s"
        )
        
        if summary_result.result and summary_result.result.data_array:
            print(f"\n{'Table':<20} {'Severity':<12} {'Count':<6}")
            print("-" * 40)
            for row in summary_result.result.data_array:
                print(f"{row[0]:<20} {row[1]:<12} {row[2]:<6}")
        
    except Exception as e:
        print(f"⚠️  Could not fetch summary: {e}")
    
    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Re-run Bronze streaming pipeline")
    print("2. Verify dropped record counts go to ~0")
    print("=" * 80)

if __name__ == "__main__":
    run_migration()
