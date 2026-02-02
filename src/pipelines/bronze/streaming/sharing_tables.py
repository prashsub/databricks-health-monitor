# Databricks notebook source
# MAGIC %md
# MAGIC # System Sharing Tables - DLT Streaming Pipeline
# MAGIC
# MAGIC ## TRAINING MATERIAL: Delta Sharing Governance Data
# MAGIC
# MAGIC This notebook ingests Delta Sharing system tables for
# MAGIC tracking data exchange and materialization events.
# MAGIC
# MAGIC ### Delta Sharing Architecture
# MAGIC
# MAGIC ```
# MAGIC Provider Workspace                    Recipient Workspace
# MAGIC ─────────────────                     ───────────────────
# MAGIC ┌─────────────────┐                   ┌─────────────────┐
# MAGIC │  Source Table   │                   │ Materialized    │
# MAGIC │  (Gold layer)   │═══════════════════│ View/Table      │
# MAGIC └─────────────────┘   Delta Sharing   └─────────────────┘
# MAGIC                              │
# MAGIC                              ▼
# MAGIC                   materialization_history
# MAGIC                   (tracks all exchanges)
# MAGIC ```
# MAGIC
# MAGIC ### What is Materialization?
# MAGIC
# MAGIC When a recipient accesses shared data that requires computation
# MAGIC (views, streaming tables), Delta Sharing creates a **materialization**:
# MAGIC
# MAGIC 1. **Views** - Computed on-demand at recipient
# MAGIC 2. **Materialized Views** - Pre-computed and refreshed
# MAGIC 3. **Streaming Tables** - Continuous replication
# MAGIC
# MAGIC ### Governance Use Cases
# MAGIC
# MAGIC 1. **Data lineage** - Track where data flows across organizations
# MAGIC 2. **Cost attribution** - Bill back materialization costs
# MAGIC 3. **Compliance audit** - Document data sharing activities
# MAGIC 4. **Usage analytics** - Understand data product consumption
# MAGIC
# MAGIC **Tables ingested:**
# MAGIC - materialization_history (system.sharing.materialization_history)
# MAGIC
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

import dlt
from pyspark.sql.functions import current_timestamp
from dq_rules_loader import get_critical_rules_for_table, get_warning_rules_for_table

# COMMAND ----------

# MAGIC %md
# MAGIC ## Delta Sharing Materialization History Table

# COMMAND ----------

@dlt.table(
    name="materialization_history",
    comment="Bronze layer ingestion of system.sharing.materialization_history - captures data materialization events created from view, materialized view, and streaming table sharing",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "sharing",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.sharing.materialization_history",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_fail(get_critical_rules_for_table("materialization_history"))
@dlt.expect_all(get_warning_rules_for_table("materialization_history"))
def materialization_history():
    """
    Streams Delta Sharing materialization events from system.sharing.materialization_history.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks data materialization events for Delta Sharing:
    - Materialization ID and creation timestamp
    - Recipient and provider information
    - Share, schema, and table names
    - Workspace association
    
    Critical for:
    - Delta Sharing usage tracking
    - Data product consumption monitoring
    - Cross-organization data sharing analytics
    
    Covers materialization from:
    - Views
    - Materialized views
    - Streaming tables
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.sharing.materialization_history")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

