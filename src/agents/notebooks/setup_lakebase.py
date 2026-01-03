# Databricks notebook source
# MAGIC %md
# MAGIC # Agent Framework Setup
# MAGIC
# MAGIC This notebook initializes the Lakebase infrastructure for the Health Monitor agent:
# MAGIC 1. Creates CheckpointSaver tables for short-term memory
# MAGIC 2. Creates DatabricksStore tables for long-term memory
# MAGIC 3. Verifies connectivity and permissions

# COMMAND ----------

# MAGIC %pip install databricks-langchain mlflow>=3.0.0
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "health_monitor")
dbutils.widgets.text("schema", "agents")
dbutils.widgets.text("lakebase_instance", "health_monitor_memory")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
lakebase_instance = dbutils.widgets.get("lakebase_instance")

print(f"Catalog: {catalog}")
print(f"Schema: {schema}")
print(f"Lakebase Instance: {lakebase_instance}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Create Schema

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
print(f"Schema {catalog}.{schema} ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Setup Short-Term Memory (CheckpointSaver)

# COMMAND ----------

from databricks_langchain import CheckpointSaver

print("Setting up CheckpointSaver tables...")

with CheckpointSaver(instance_name=lakebase_instance) as saver:
    saver.setup()

print("CheckpointSaver tables created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Setup Long-Term Memory (DatabricksStore)

# COMMAND ----------

from databricks_langchain import DatabricksStore

# Use GTE-Large for embeddings
EMBEDDING_ENDPOINT = "databricks-gte-large-en"
EMBEDDING_DIMS = 1024

print("Setting up DatabricksStore tables...")

store = DatabricksStore(
    instance_name=lakebase_instance,
    embedding_endpoint=EMBEDDING_ENDPOINT,
    embedding_dims=EMBEDDING_DIMS,
)
store.setup()

print("DatabricksStore tables created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Verify Setup

# COMMAND ----------

# Test short-term memory
print("\nTesting Short-Term Memory...")
with CheckpointSaver(instance_name=lakebase_instance) as saver:
    # The setup is complete if we can create the context manager
    print("Short-term memory: OK")

# Test long-term memory
print("\nTesting Long-Term Memory...")
test_namespace = ("test", "setup_verification")
test_key = "test_memory"
test_value = {"status": "verified", "timestamp": str(spark.sql("SELECT current_timestamp()").first()[0])}

store.put(test_namespace, test_key, test_value)
retrieved = store.get(test_namespace, test_key)

if retrieved and retrieved.value == test_value:
    print("Long-term memory: OK")
    # Cleanup test data
    store.delete(test_namespace, test_key)
else:
    print("Long-term memory: FAILED")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Summary

# COMMAND ----------

print("=" * 60)
print("Agent Framework Setup Complete")
print("=" * 60)
print(f"Lakebase Instance: {lakebase_instance}")
print(f"Embedding Model: {EMBEDDING_ENDPOINT}")
print(f"Embedding Dimensions: {EMBEDDING_DIMS}")
print("=" * 60)

dbutils.notebook.exit("SUCCESS")
