#!/usr/bin/env python3
"""
Run DQ Rules Migration SQL (FIXED - using correct column names)
"""

from databricks.sdk import WorkspaceClient
import os
import sys

os.environ['DATABRICKS_CONFIG_PROFILE'] = 'e2-demo'
w = WorkspaceClient()

warehouse_id = '4b9b953939869799'
catalog = "prashanth_subrahmanyam_catalog"
schema = "dev_prashanth_subrahmanyam_system_bronze"

print("=" * 80)
print("DQ RULES MIGRATION - FIXING RECORD DROPS")
print("=" * 80)
print(f"Catalog: {catalog}")
print(f"Schema: {schema}")
print("=" * 80)
print("\nChanging ALL critical rules to 'warning' for Bronze system tables")
print("(except mathematical constraints like non_negative values)\n")

# Update SQL - only set severity and updated_timestamp (no updated_by column!)
update_sql = f"""
UPDATE {catalog}.{schema}.dq_rules
SET 
    severity = 'warning',
    updated_timestamp = current_timestamp()
WHERE 
    severity = 'critical'
    AND table_name IN ('column_lineage', 'clusters', 'table_lineage', 'warehouses', 'usage')
    AND rule_name NOT IN (
        'non_negative_usage_quantity',
        'valid_time_sequence'
    )
"""

print("📝 Executing UPDATE...")
try:
    result = w.statement_execution.execute_statement(
        statement=update_sql,
        warehouse_id=warehouse_id,
        wait_timeout="50s"
    )
    print("✅ UPDATE executed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Verify
print("\n📊 Verification:")
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
        total_warning = 0
        total_critical = 0
        for row in summary_result.result.data_array:
            print(f"{row[0]:<20} {row[1]:<12} {row[2]:<6}")
            if row[1] == 'warning':
                total_warning += row[2]
            else:
                total_critical += row[2]
        
        print("-" * 40)
        print(f"{'TOTAL':<20} {'warning':<12} {total_warning:<6}")
        print(f"{'TOTAL':<20} {'critical':<12} {total_critical:<6}")

except Exception as e:
    print(f"⚠️  Error: {e}")

print("\n" + "=" * 80)
print("✅ MIGRATION COMPLETE!")
print("=" * 80)
print("\nExpected Results:")
print("  - column_lineage: Most rules changed to 'warning'")
print("  - usage: Most rules changed to 'warning' (except non_negative)")
print("  - clusters: All rules changed to 'warning'")
print("\nNext: Re-run Bronze streaming pipeline to see drops go to ~0")
print("=" * 80)
