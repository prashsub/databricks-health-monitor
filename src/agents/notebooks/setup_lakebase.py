# Databricks notebook source
# MAGIC %md
# MAGIC # Lakebase Memory Setup
# MAGIC
# MAGIC This notebook initializes the Lakebase infrastructure for the Health Monitor agent:
# MAGIC 1. Creates CheckpointSaver tables for short-term memory (conversation context)
# MAGIC 2. Creates DatabricksStore tables for long-term memory (user preferences)
# MAGIC 3. Verifies connectivity and permissions
# MAGIC
# MAGIC **Run this once** before using memory features. Tables persist across agent versions.

# COMMAND ----------

# Parameters - passed from agent_setup_job.yml
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")
dbutils.widgets.text("lakebase_instance_name", "")  # Empty = skip Lakebase setup

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")
lakebase_instance = dbutils.widgets.get("lakebase_instance_name")

print("=" * 60)
print("LAKEBASE MEMORY SETUP")
print("=" * 60)
print(f"Catalog: {catalog}")
print(f"Schema: {agent_schema}")
print(f"Lakebase Instance: {lakebase_instance or '(not configured)'}")
print("=" * 60)

# Skip if Lakebase not configured
if not lakebase_instance:
    print("\n⚠ Lakebase instance not configured - skipping memory setup")
    print("  Memory features will be disabled in the agent.")
    print("  To enable, set 'lakebase_instance_name' in databricks.yml")
    dbutils.notebook.exit("SKIPPED - No Lakebase instance configured")

# COMMAND ----------

# MAGIC %pip install -q databricks-langchain[memory]

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# Re-read parameters after Python restart
lakebase_instance = dbutils.widgets.get("lakebase_instance_name")
catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")

print(f"\nInitializing Lakebase: {lakebase_instance}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup Short-Term Memory (CheckpointSaver)
# MAGIC 
# MAGIC CheckpointSaver stores conversation context between turns.
# MAGIC - Table: `checkpoints` in Lakebase
# MAGIC - Retention: Configurable (default 24h)

# COMMAND ----------

from databricks_langchain import CheckpointSaver

print("\n" + "─" * 60)
print("STEP 1: SHORT-TERM MEMORY (CheckpointSaver)")
print("─" * 60)

try:
    print(f"→ Connecting to Lakebase: {lakebase_instance}")
    with CheckpointSaver(instance_name=lakebase_instance) as saver:
        print("→ Creating/verifying checkpoints table...")
        saver.setup()
        print("✓ CheckpointSaver tables ready")
except Exception as e:
    print(f"✗ CheckpointSaver setup failed: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Setup Long-Term Memory (DatabricksStore)
# MAGIC 
# MAGIC DatabricksStore stores user preferences and insights with semantic search.
# MAGIC - Table: `store` in Lakebase
# MAGIC - Uses embeddings for semantic retrieval

# COMMAND ----------

from databricks_langchain import DatabricksStore

# Embedding configuration for semantic search
EMBEDDING_ENDPOINT = "databricks-gte-large-en"
EMBEDDING_DIMS = 1024

print("\n" + "─" * 60)
print("STEP 2: LONG-TERM MEMORY (DatabricksStore)")
print("─" * 60)

try:
    print(f"→ Connecting to Lakebase: {lakebase_instance}")
    print(f"→ Embedding model: {EMBEDDING_ENDPOINT}")
    
    store = DatabricksStore(
        instance_name=lakebase_instance,
        embedding_endpoint=EMBEDDING_ENDPOINT,
        embedding_dims=EMBEDDING_DIMS,
    )
    
    print("→ Creating/verifying store table...")
    store.setup()
    print("✓ DatabricksStore tables ready")
except Exception as e:
    print(f"✗ DatabricksStore setup failed: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Verify Setup

# COMMAND ----------

print("\n" + "─" * 60)
print("STEP 3: VERIFICATION")
print("─" * 60)

verification_passed = True

# Test short-term memory connection
print("\n→ Testing CheckpointSaver connection...")
try:
    with CheckpointSaver(instance_name=lakebase_instance) as saver:
        print("  ✓ CheckpointSaver: Connected")
except Exception as e:
    print(f"  ✗ CheckpointSaver: Failed - {e}")
    verification_passed = False

# Test long-term memory with write/read/delete cycle
print("\n→ Testing DatabricksStore operations...")
try:
    import datetime
    test_namespace = ("__test__", "setup_verification")
    test_key = f"test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_value = {"status": "verified", "timestamp": str(datetime.datetime.now())}
    
    # Write
    store.put(test_namespace, test_key, test_value)
    print("  ✓ Write: OK")
    
    # Read
    retrieved = store.get(test_namespace, test_key)
    if retrieved and retrieved.value == test_value:
        print("  ✓ Read: OK")
    else:
        print("  ✗ Read: Data mismatch")
        verification_passed = False
    
    # Delete (cleanup)
    store.delete(test_namespace, test_key)
    print("  ✓ Delete: OK")
    
except Exception as e:
    print(f"  ✗ DatabricksStore operations failed: {e}")
    verification_passed = False

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n")
print("╔" + "═" * 58 + "╗")
print("║" + " LAKEBASE MEMORY SETUP COMPLETE ".center(58) + "║")
print("╠" + "═" * 58 + "╣")
print(f"║  Lakebase Instance: {lakebase_instance:<36} ║")
print(f"║  Embedding Model:   {EMBEDDING_ENDPOINT:<36} ║")
print(f"║  Embedding Dims:    {EMBEDDING_DIMS:<36} ║")
print("╠" + "═" * 58 + "╣")
print("║  Tables Created:                                        ║")
print("║    • checkpoints (short-term memory)                    ║")
print("║    • store (long-term memory with embeddings)           ║")
print("╠" + "═" * 58 + "╣")

if verification_passed:
    print("║  Status: ✅ ALL TESTS PASSED                            ║")
    exit_status = "SUCCESS"
else:
    print("║  Status: ⚠️  SOME TESTS FAILED (check logs above)       ║")
    exit_status = "PARTIAL"

print("╚" + "═" * 58 + "╝")

dbutils.notebook.exit(exit_status)
