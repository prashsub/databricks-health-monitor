# Databricks notebook source
# MAGIC %md
# MAGIC # System Billing Tables - DLT Streaming Pipeline
# MAGIC 
# MAGIC TRAINING MATERIAL: DLT Bronze Layer Streaming Pattern
# MAGIC =======================================================
# MAGIC 
# MAGIC This notebook demonstrates the **recommended Bronze layer pattern** for ingesting 
# MAGIC Databricks system tables using Delta Live Tables (DLT).
# MAGIC 
# MAGIC ## Why DLT for Bronze Layer?
# MAGIC 
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────────────┐
# MAGIC │                    DLT BENEFITS FOR BRONZE LAYER                         │
# MAGIC │                                                                         │
# MAGIC │  TRADITIONAL ETL:                 DLT STREAMING:                        │
# MAGIC │  ────────────────                 ─────────────                         │
# MAGIC │  - Manual scheduling              - Continuous/triggered execution       │
# MAGIC │  - DIY checkpointing              - Auto checkpointing                  │
# MAGIC │  - DIY schema evolution           - mergeSchema built-in                │
# MAGIC │  - Manual error handling          - Expectation-based quality           │
# MAGIC │  - Explicit CDC handling          - skipChangeCommits option            │
# MAGIC └─────────────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC 
# MAGIC ## Key Patterns Demonstrated
# MAGIC 
# MAGIC 1. **skipChangeCommits**: Skips transaction logs, reads committed data only
# MAGIC 2. **mergeSchema**: Handles schema evolution when source adds columns  
# MAGIC 3. **@dlt.expect_all_or_drop**: Critical rules (bad data is quarantined)
# MAGIC 4. **@dlt.expect_all**: Warning rules (data flows through, metrics logged)
# MAGIC 5. **Table properties**: Full metadata for governance and optimization
# MAGIC 6. **cluster_by_auto**: Automatic liquid clustering for performance
# MAGIC 
# MAGIC ## Data Flow
# MAGIC 
# MAGIC ```
# MAGIC system.billing.usage ──► DLT Bronze (usage) ──► DLT Silver ──► Gold Layer
# MAGIC         │                        │
# MAGIC         │                        ├── Critical rules: DROP failures
# MAGIC         │                        ├── Warning rules: LOG metrics
# MAGIC         │                        └── bronze_ingestion_timestamp added
# MAGIC         │
# MAGIC         └── Source: Databricks system table (billing data)
# MAGIC ```
# MAGIC 
# MAGIC **Tables ingested:**
# MAGIC - usage (system.billing.usage)
# MAGIC 
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: DLT Import Pattern
#
# dlt: Delta Live Tables API for defining tables and expectations
# current_timestamp: For adding ingestion tracking columns
# dq_rules_loader: Custom module for dynamic data quality rules (see below)

import dlt
from pyspark.sql.functions import current_timestamp

# TRAINING MATERIAL: Dynamic Data Quality Rules
# ---------------------------------------------
# Instead of hardcoding rules in code, rules are loaded from a Delta table.
# This enables:
# - User-configurable rules via frontend app
# - Rules can be updated WITHOUT redeploying the pipeline
# - Rules are version-controlled in Delta
# 
# Example rule in Delta table:
#   table_name="usage", rule_name="valid_dbus", rule_expr="dbus >= 0"
#
# get_critical_rules_for_table returns dict: {"valid_dbus": "dbus >= 0", ...}
from dq_rules_loader import get_critical_rules_for_table, get_warning_rules_for_table

# COMMAND ----------

# MAGIC %md
# MAGIC ## Billable Usage Table

# COMMAND ----------

@dlt.table(
    name="usage",
    comment="Bronze layer ingestion of system.billing.usage - includes records for all billable usage across the account",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "billing",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "confidential",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.billing.usage",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("usage"))
@dlt.expect_all(get_warning_rules_for_table("usage"))
def usage():
    """
    Streams billable usage records from system.billing.usage.
    
    Contains all billable usage across the account including:
    - Compute usage (DBUs)
    - Storage usage
    - Network usage
    - Model serving usage
    
    Critical for cost analysis, chargeback, and budget monitoring.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.billing.usage")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

