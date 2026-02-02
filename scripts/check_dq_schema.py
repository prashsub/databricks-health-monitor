#!/usr/bin/env python3
"""Check DQ rules table schema and sample data"""

from databricks.sdk import WorkspaceClient
import os

os.environ['DATABRICKS_CONFIG_PROFILE'] = 'e2-demo'
w = WorkspaceClient()

warehouse_id = '4b9b953939869799'
catalog = "prashanth_subrahmanyam_catalog"
schema = "dev_prashanth_subrahmanyam_system_bronze"

# Describe table
print("Table Schema:")
print("=" * 80)
describe_sql = f"DESCRIBE {catalog}.{schema}.dq_rules"

result = w.statement_execution.execute_statement(
    statement=describe_sql,
    warehouse_id=warehouse_id,
    wait_timeout="30s"
)

if result.result and result.result.data_array:
    print(f"{'Column':<30} {'Type':<20} {'Comment'}")
    print("-" * 80)
    for row in result.result.data_array:
        print(f"{row[0]:<30} {row[1]:<20} {row[2] if len(row) > 2 else ''}")

# Get sample row
print("\n\nSample Row:")
print("=" * 80)
sample_sql = f"""
SELECT *
FROM {catalog}.{schema}.dq_rules
WHERE table_name = 'column_lineage'
LIMIT 1
"""

result2 = w.statement_execution.execute_statement(
    statement=sample_sql,
    warehouse_id=warehouse_id,
    wait_timeout="30s"
)

if result2.result:
    if result2.result.data_array:
        print(f"Data: {result2.result.data_array[0]}")
    if result2.result.column_names:
        print(f"\nColumns: {result2.result.column_names}")
