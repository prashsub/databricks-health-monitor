# Databricks notebook source
# MAGIC %md
# MAGIC # System Compute Tables - DLT Streaming Pipeline
# MAGIC
# MAGIC ## TRAINING MATERIAL: DLT Streaming from System Tables
# MAGIC
# MAGIC This notebook demonstrates the standard pattern for ingesting Databricks
# MAGIC system tables into Bronze layer using DLT streaming.
# MAGIC
# MAGIC ### Key DLT Options for System Tables
# MAGIC
# MAGIC ```python
# MAGIC spark.readStream
# MAGIC     .option("skipChangeCommits", "true")   # Ignore CDC commits
# MAGIC     .option("mergeSchema", "true")         # Handle schema evolution
# MAGIC     .table("system.compute.clusters")
# MAGIC ```
# MAGIC
# MAGIC **skipChangeCommits**: System tables use Change Data Feed internally.
# MAGIC Without this option, DLT fails when it encounters CDC records.
# MAGIC
# MAGIC **mergeSchema**: Databricks adds columns to system tables over time.
# MAGIC This option automatically incorporates new columns.
# MAGIC
# MAGIC ### Table Properties Pattern
# MAGIC
# MAGIC Every Bronze table needs consistent properties for governance:
# MAGIC
# MAGIC ```python
# MAGIC table_properties={
# MAGIC     "delta.enableChangeDataFeed": "true",      # Enable downstream streaming
# MAGIC     "delta.autoOptimize.optimizeWrite": "true", # Auto-optimize writes
# MAGIC     "delta.autoOptimize.autoCompact": "true",   # Auto-compaction
# MAGIC     "layer": "bronze",                          # Medallion layer tag
# MAGIC     "source_system": "databricks_system_tables",
# MAGIC     "domain": "compute",                        # Domain tag
# MAGIC     "entity_type": "dimension",                 # dim vs fact
# MAGIC     "source_table": "system.compute.clusters",  # Lineage
# MAGIC }
# MAGIC ```
# MAGIC
# MAGIC **Tables ingested:**
# MAGIC - clusters (system.compute.clusters)
# MAGIC - node_timeline (system.compute.node_timeline)
# MAGIC - warehouse_events (system.compute.warehouse_events)
# MAGIC - warehouses (system.compute.warehouses)
# MAGIC
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

import dlt
from pyspark.sql.functions import current_timestamp
import sys

# Import DQ rules loader for centralized Delta Table pattern
sys.path.insert(0, '/Workspace/Users/prashanth.subrahmanyam@databricks.com/.bundle/databricks_health_monitor/dev/files/src/bronze/streaming')
from dq_rules_loader import get_critical_rules_for_table, get_warning_rules_for_table

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration - Get Catalog/Schema from Pipeline

# COMMAND ----------

# Get catalog and schema from pipeline configuration
catalog = spark.conf.get("catalog")
bronze_schema = spark.conf.get("bronze_schema")

print("=" * 80)
print("BRONZE PIPELINE CONFIGURATION - COMPUTE DOMAIN")
print("=" * 80)
print(f"Catalog: {catalog}")
print(f"Bronze Schema: {bronze_schema}")
print("=" * 80)

def get_bronze_table_fqn(table_name):
    """
    Returns fully qualified Bronze table name.
    
    CRITICAL: DLT requires fully qualified names when using expectations.
    Format: catalog.schema.table
    """
    fqn = f"{catalog}.{bronze_schema}.{table_name}"
    print(f"Creating Bronze table: {fqn}")
    return fqn

# COMMAND ----------

# MAGIC %md
# MAGIC ## Clusters Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("clusters"),
    comment="Bronze layer ingestion of system.compute.clusters - slow-changing dimension table containing full history of compute configurations over time for any cluster",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "compute",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.compute.clusters",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("clusters"))
@dlt.expect_all(get_warning_rules_for_table("clusters"))
def clusters():
    """
    Streams cluster configuration history from system.compute.clusters.
    
    SCD Type 2 table tracking all cluster configuration changes including:
    - Node types (driver and worker)
    - Autoscaling settings
    - Instance pools
    - DBR versions
    - Tags and policies
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.compute.clusters")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Node Timeline Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("node_timeline"),
    comment="Bronze layer ingestion of system.compute.node_timeline - captures utilization metrics of all-purpose and jobs compute resources",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "compute",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.compute.node_timeline",
        "retention_period": "90_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("node_timeline"))
@dlt.expect_all(get_warning_rules_for_table("node_timeline"))
def node_timeline():
    """
    Streams node utilization metrics from system.compute.node_timeline.
    
    High-frequency metrics for cluster node monitoring including:
    - CPU utilization
    - Memory usage
    - Disk I/O
    - Network traffic
    
    Shorter retention period (90 days) due to high volume.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.compute.node_timeline")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## SQL Warehouse Events Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("warehouse_events"),
    comment="Bronze layer ingestion of system.compute.warehouse_events - captures events related to SQL warehouses (starting, stopping, scaling, etc.)",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "compute",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.compute.warehouse_events",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("warehouse_events"))
@dlt.expect_all(get_warning_rules_for_table("warehouse_events"))
def warehouse_events():
    """
    Streams SQL warehouse lifecycle events from system.compute.warehouse_events.
    
    Tracks warehouse state changes:
    - STARTING / RUNNING / STOPPING / STOPPED
    - SCALED_UP / SCALED_DOWN
    - Cluster count changes
    
    Useful for SQL warehouse utilization analysis and cost optimization.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.compute.warehouse_events")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## SQL Warehouses Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("warehouses"),
    comment="Bronze layer ingestion of system.compute.warehouses - contains full history of configurations over time for any SQL warehouse",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "compute",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.compute.warehouses",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("warehouses"))
@dlt.expect_all(get_warning_rules_for_table("warehouses"))
def warehouses():
    """
    Streams SQL warehouse configuration history from system.compute.warehouses.
    
    SCD Type 2 table tracking all warehouse configuration changes including:
    - Warehouse type (CLASSIC, PRO, SERVERLESS)
    - Size (2X_SMALL to 4X_LARGE)
    - Cluster count (min/max)
    - Auto-stop settings
    - Tags
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.compute.warehouses")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

