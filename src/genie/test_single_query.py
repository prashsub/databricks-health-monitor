# Databricks notebook source
"""
Test Single Query Execution
===========================
This notebook tests a single benchmark query to debug NOT_A_SCALAR_FUNCTION errors.
"""

# COMMAND ----------

import json
from pathlib import Path

# Get parameters
catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")

print(f"Catalog: {catalog}")
print(f"Gold Schema: {gold_schema}")

# COMMAND ----------

# Get notebook directory
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
genie_dir = Path("/Workspace" + "/".join(notebook_path.split("/")[:-1]))
print(f"Genie dir: {genie_dir}")

# Read performance JSON
json_path = genie_dir / "performance_genie_export.json"
print(f"JSON path: {json_path}")

with open(json_path, 'r') as f:
    data = json.load(f)

print(f"Successfully loaded JSON")

# COMMAND ----------

# Get Q5
curated = data.get('curated_questions', [])
print(f"Total curated questions: {len(curated)}")

q5 = curated[4]  # Q5 is index 4
print(f"\nQ5 question: {q5.get('question')}")

query = q5.get('query')
print(f"\nQ5 query type: {type(query)}")
print(f"\nQ5 query raw content:")
print(repr(query))

# COMMAND ----------

# Substitute variables
sql = query.replace('${catalog}', catalog)
sql = sql.replace('${gold_schema}', gold_schema)

print("Substituted SQL:")
print(sql)
print(f"\nHas TABLE(: {'TABLE(' in sql}")

# COMMAND ----------

# Try to execute
print("Executing SQL...")
try:
    result = spark.sql(sql)
    print("SUCCESS!")
    display(result)
except Exception as e:
    print(f"ERROR: {e}")

# COMMAND ----------

# Also test without LIMIT to see if that matters
sql_no_limit = sql.replace("LIMIT 20", "LIMIT 1")
print("SQL with LIMIT 1:")
print(sql_no_limit)

try:
    result = spark.sql(sql_no_limit)
    print("SUCCESS with LIMIT 1!")
    display(result)
except Exception as e:
    print(f"ERROR with LIMIT 1: {e}")
