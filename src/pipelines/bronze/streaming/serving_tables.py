# Databricks notebook source
# MAGIC %md
# MAGIC # System Serving Tables - DLT Streaming Pipeline
# MAGIC
# MAGIC ## TRAINING MATERIAL: Model Serving Observability Data
# MAGIC
# MAGIC This notebook ingests Model Serving system tables for
# MAGIC monitoring ML deployments and inference costs.
# MAGIC
# MAGIC ### Model Serving Architecture
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────────────┐
# MAGIC │                     Model Serving Endpoint                              │
# MAGIC │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
# MAGIC │  │ Served Entity 1 │ │ Served Entity 2 │ │ Served Entity 3 │          │
# MAGIC │  │ (model v1)      │ │ (model v2)      │ │ (model v3)      │          │
# MAGIC │  │ Traffic: 70%    │ │ Traffic: 20%    │ │ Traffic: 10%    │          │
# MAGIC │  └─────────────────┘ └─────────────────┘ └─────────────────┘          │
# MAGIC └─────────────────────────────────────────────────────────────────────────┘
# MAGIC                                    │
# MAGIC                 ┌──────────────────┴──────────────────┐
# MAGIC                 ▼                                      ▼
# MAGIC        served_entities                        endpoint_usage
# MAGIC        (SCD2 config history)                  (invocation metrics)
# MAGIC ```
# MAGIC
# MAGIC ### Key Metrics Available
# MAGIC
# MAGIC | Metric | Source | Use |
# MAGIC |--------|--------|-----|
# MAGIC | Request count | endpoint_usage | Traffic monitoring |
# MAGIC | Latency (p50/p99) | endpoint_usage | SLA compliance |
# MAGIC | Error rate | endpoint_usage | Health monitoring |
# MAGIC | Token usage | endpoint_usage | LLM cost tracking |
# MAGIC | Model version | served_entities | Deployment tracking |
# MAGIC
# MAGIC **Tables ingested:**
# MAGIC - served_entities (system.serving.served_entities)
# MAGIC - endpoint_usage (system.serving.endpoint_usage)
# MAGIC
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

import dlt
from pyspark.sql.functions import current_timestamp

# COMMAND ----------

# MAGIC %md
# MAGIC ## Served Entities Table

# COMMAND ----------

@dlt.table(
    name="served_entities",
    comment="Bronze layer ingestion of system.serving.served_entities - slow-changing dimension table storing metadata for each served foundation model in a model serving endpoint",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "serving",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.serving.served_entities",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
def served_entities():
    """
    Streams model serving entity metadata from system.serving.served_entities.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    SCD Type 2 table tracking served model configurations:
    - Endpoint name and ID
    - Served entity details
    - Model information
    - Configuration history
    
    Useful for model serving governance and version tracking.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.serving.served_entities")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Endpoint Usage Table

# COMMAND ----------

@dlt.table(
    name="endpoint_usage",
    comment="Bronze layer ingestion of system.serving.endpoint_usage - captures token counts for each request to a model serving endpoint and its responses",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "serving",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.serving.endpoint_usage",
        "retention_period": "90_days"
    },
    cluster_by_auto=True
)
def endpoint_usage():
    """
    Streams model serving endpoint usage from system.serving.endpoint_usage.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    High-frequency usage metrics for model serving endpoints:
    - Request and response token counts
    - Endpoint identification
    - Timestamp and request metadata
    
    Critical for:
    - Usage-based billing
    - Cost allocation
    - Token consumption tracking
    - Performance monitoring
    
    Note: Requires usage tracking enabled on serving endpoint.
    Shorter retention period (90 days) due to high volume.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.serving.endpoint_usage")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

