# Databricks notebook source
# MAGIC %md
# MAGIC # System Marketplace Tables - DLT Streaming Pipeline
# MAGIC 
# MAGIC Bronze layer ingestion of system.marketplace.* tables with schema evolution.
# MAGIC 
# MAGIC **Tables ingested:**
# MAGIC - listing_funnel_events (system.marketplace.listing_funnel_events)
# MAGIC - listing_access_events (system.marketplace.listing_access_events)
# MAGIC 
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

import dlt
from pyspark.sql.functions import current_timestamp

# COMMAND ----------

# MAGIC %md
# MAGIC ## Listing Funnel Events Table

# COMMAND ----------

@dlt.table(
    name="listing_funnel_events",
    comment="Bronze layer ingestion of system.marketplace.listing_funnel_events - includes consumer impression and funnel data for listings",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "marketplace",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.marketplace.listing_funnel_events",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
def listing_funnel_events():
    """
    Streams marketplace listing funnel events from system.marketplace.listing_funnel_events.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks consumer interactions with Databricks Marketplace listings:
    - Impressions
    - Views
    - Clicks
    - Conversions
    
    Useful for marketplace analytics and listing performance tracking.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.marketplace.listing_funnel_events")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Listing Access Events Table

# COMMAND ----------

@dlt.table(
    name="listing_access_events",
    comment="Bronze layer ingestion of system.marketplace.listing_access_events - includes consumer info for completed request data or get data events on listings",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "marketplace",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.marketplace.listing_access_events",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
def listing_access_events():
    """
    Streams marketplace listing access events from system.marketplace.listing_access_events.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks consumer data access events:
    - REQUEST_DATA events (consumer requests access)
    - GET_DATA events (consumer receives data)
    
    Contains consumer information:
    - Email, name, company
    - Cloud and region
    - Intended use and comments
    
    Critical for marketplace provider tracking and analytics.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.marketplace.listing_access_events")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

