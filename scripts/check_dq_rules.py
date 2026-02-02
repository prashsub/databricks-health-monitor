#!/usr/bin/env python3
"""Check current DQ rules state"""

from databricks.sdk import WorkspaceClient
import os

os.environ['DATABRICKS_CONFIG_PROFILE'] = 'e2-demo'
w = WorkspaceClient()

warehouse_id = '4b9b953939869799'
catalog = "prashanth_subrahmanyam_catalog"
schema = "dev_prashanth_subrahmanyam_system_bronze"

# Check specific rules
check_sql = f"""
SELECT 
    table_name,
    rule_name,
    severity,
    enabled
FROM {catalog}.{schema}.dq_rules
WHERE table_name IN ('column_lineage', 'usage', 'clusters')
ORDER BY table_name, rule_name
"""

print("Current DQ rules state:")
print("=" * 80)

result = w.statement_execution.execute_statement(
    statement=check_sql,
    warehouse_id=warehouse_id,
    wait_timeout="30s"
)

if result.result and result.result.data_array:
    print(f"{'Table':<20} {'Rule':<30} {'Severity':<12} {'Enabled'}")
    print("-" * 80)
    for row in result.result.data_array:
        print(f"{row[0]:<20} {row[1]:<30} {row[2]:<12} {row[3]}")
