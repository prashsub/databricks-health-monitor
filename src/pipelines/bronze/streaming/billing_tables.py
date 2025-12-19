# Databricks notebook source
# MAGIC %md
# MAGIC # System Billing Tables - DLT Streaming Pipeline
# MAGIC 
# MAGIC Bronze layer ingestion of system.billing.* tables with schema evolution.
# MAGIC 
# MAGIC **Tables ingested:**
# MAGIC - usage (system.billing.usage)
# MAGIC 
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

import dlt
from pyspark.sql.functions import current_timestamp
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

