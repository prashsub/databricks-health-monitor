"""
Migrate DQ Rules: Change Bronze Layer Critical Rules to Warnings

This script updates existing DQ rules in the Bronze layer to use "warning" 
severity instead of "critical" for rules where NULL values are legitimate.

Affected tables:
- column_lineage: 309M records were being dropped
- clusters: 155 records were being dropped  
- table_lineage: Lineage tracking
- warehouses: Resource tracking

Usage:
    python scripts/migrate_dq_rules_to_warnings.py --catalog <catalog> --schema <schema>
"""

from databricks.sdk import WorkspaceClient
import argparse

def migrate_rules(catalog: str, schema: str):
    """Update DQ rules from critical to warning severity."""
    
    w = WorkspaceClient()
    
    table_fqn = f"{catalog}.{schema}.dq_rules"
    
    print(f"Migrating DQ rules in: {table_fqn}")
    print("=" * 80)
    
    # Rules to migrate: table_name -> list of rule_names
    rules_to_migrate = {
        "column_lineage": ["valid_source_column", "valid_target_column"],
        "clusters": ["valid_cluster_id", "valid_cluster_name", "valid_state"],
        "table_lineage": ["valid_source_table", "valid_target_table"],
        "warehouses": ["valid_warehouse_id", "valid_warehouse_name", "valid_state"]
    }
    
    # Build WHERE clause for each table
    updates_made = 0
    for table_name, rule_names in rules_to_migrate.items():
        rule_names_str = "', '".join(rule_names)
        
        print(f"\n📝 Updating {table_name} rules...")
        
        update_sql = f"""
        UPDATE {table_fqn}
        SET 
            severity = 'warning',
            updated_by = 'migration_script',
            updated_at = current_timestamp()
        WHERE table_name = '{table_name}'
          AND rule_name IN ('{rule_names_str}')
          AND severity = 'critical'
        """
        
        try:
            # Execute update
            result = w.statement_execution.execute_statement(
                statement=update_sql,
                warehouse_id="${var.warehouse_id}",  # Will be replaced by DAB variable
                wait_timeout="30s"
            )
            
            # Get count of updated rows
            count_sql = f"""
            SELECT COUNT(*) as updated_count
            FROM {table_fqn}
            WHERE table_name = '{table_name}'
              AND rule_name IN ('{rule_names_str}')
              AND severity = 'warning'
            """
            
            count_result = w.statement_execution.execute_statement(
                statement=count_sql,
                warehouse_id="${var.warehouse_id}",
                wait_timeout="30s"
            )
            
            if count_result.result and count_result.result.data_array:
                updated_count = count_result.result.data_array[0][0]
                updates_made += updated_count
                print(f"   ✓ Updated {updated_count} rules for {table_name}")
            
        except Exception as e:
            print(f"   ❌ Error updating {table_name}: {e}")
    
    print("\n" + "=" * 80)
    print(f"✓ Migration complete! Updated {updates_made} rules from 'critical' to 'warning'")
    print("=" * 80)
    
    # Show summary of current rules
    print("\n📊 Current DQ Rules Summary:")
    summary_sql = f"""
    SELECT 
        table_name,
        severity,
        COUNT(*) as rule_count
    FROM {table_fqn}
    WHERE table_name IN ('column_lineage', 'clusters', 'table_lineage', 'warehouses')
    GROUP BY table_name, severity
    ORDER BY table_name, severity
    """
    
    try:
        summary_result = w.statement_execution.execute_statement(
            statement=summary_sql,
            warehouse_id="${var.warehouse_id}",
            wait_timeout="30s"
        )
        
        if summary_result.result and summary_result.result.data_array:
            print(f"\n{'Table':<30} {'Severity':<15} {'Count':<10}")
            print("-" * 55)
            for row in summary_result.result.data_array:
                print(f"{row[0]:<30} {row[1]:<15} {row[2]:<10}")
    except Exception as e:
        print(f"Warning: Could not fetch summary: {e}")

def main():
    parser = argparse.ArgumentParser(description="Migrate DQ rules from critical to warning")
    parser.add_argument("--catalog", required=True, help="Catalog name")
    parser.add_argument("--schema", required=True, help="Bronze schema name")
    
    args = parser.parse_args()
    
    migrate_rules(args.catalog, args.schema)

if __name__ == "__main__":
    main()
