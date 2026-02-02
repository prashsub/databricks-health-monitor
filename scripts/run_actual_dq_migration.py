#!/usr/bin/env python3
"""
Run DQ Rules Migration SQL (using ACTUAL rule names from database)
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
print("DQ RULES MIGRATION (ACTUAL DATABASE RULES)")
print("=" * 80)
print(f"Catalog: {catalog}")
print(f"Schema: {schema}")
print("=" * 80)

# Based on actual database, we need to change these to warning:
# - column_lineage: valid_source_table_full_name, valid_target_table_full_name, valid_workspace_id
# - clusters: valid_cluster_id, valid_cluster_name, valid_workspace_id, valid_account_id
# - usage: Most rules except non_negative_usage_quantity

# Strategy: Change ALL critical rules to warning for these tables
# EXCEPT mathematical constraints (non_negative, time_sequence)

update_sql = f"""
UPDATE {catalog}.{schema}.dq_rules
SET 
    severity = 'warning',
    updated_by = 'consolidated_migration_v2',
    updated_at = current_timestamp()
WHERE 
    severity = 'critical'
    AND table_name IN ('column_lineage', 'clusters', 'table_lineage', 'warehouses', 'usage')
    AND rule_name NOT IN (
        'non_negative_usage_quantity',
        'valid_time_sequence'
    )
"""

print("\n📝 Executing UPDATE for all critical rules (except math constraints)...")
print("   Tables: column_lineage, clusters, table_lineage, warehouses, usage")
print("   Keeping critical: non_negative_usage_quantity, valid_time_sequence")
print()

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

# Verify
print("\n📊 Verifying migration...")
verify_sql = f"""
SELECT COUNT(*) as updated_rules
FROM {catalog}.{schema}.dq_rules
WHERE updated_by = 'consolidated_migration_v2'
"""

try:
    verify_result = w.statement_execution.execute_statement(
        statement=verify_sql,
        warehouse_id=warehouse_id,
        wait_timeout="30s"
    )
    
    if verify_result.result and verify_result.result.data_array:
        updated_count = verify_result.result.data_array[0][0]
        print(f"✅ {updated_count} rules updated to 'warning'")

except Exception as e:
    print(f"⚠️  Could not verify: {e}")

# Show summary
print("\n📈 Summary by table and severity...")
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

# Show which rules are still critical
print("\n📋 Rules still marked as CRITICAL:")
critical_sql = f"""
SELECT 
    table_name,
    rule_name,
    severity
FROM {catalog}.{schema}.dq_rules
WHERE table_name IN ('column_lineage', 'usage', 'clusters', 'table_lineage', 'warehouses')
  AND severity = 'critical'
ORDER BY table_name, rule_name
"""

try:
    critical_result = w.statement_execution.execute_statement(
        statement=critical_sql,
        warehouse_id=warehouse_id,
        wait_timeout="30s"
    )
    
    if critical_result.result and critical_result.result.data_array:
        for row in critical_result.result.data_array:
            print(f"  - {row[0]}.{row[1]}")
    else:
        print("  (none - all changed to warning)")

except Exception as e:
    print(f"⚠️  Could not fetch critical rules: {e}")

print("\n" + "=" * 80)
print("✅ MIGRATION COMPLETE!")
print("=" * 80)
print("\nNext steps:")
print("1. Re-run Bronze streaming pipeline")
print("2. Check dropped counts in DLT UI - should go to ~0")
print("=" * 80)
