# Databricks notebook source
# MAGIC %md
# MAGIC # System Access Tables - DLT Streaming Pipeline
# MAGIC 
# MAGIC Bronze layer ingestion of system.access.* tables with schema evolution.
# MAGIC 
# MAGIC **Tables ingested:**
# MAGIC - audit (system.access.audit)
# MAGIC - clean_room_events (system.access.clean_room_events)
# MAGIC - column_lineage (system.access.column_lineage)
# MAGIC - outbound_network (system.access.outbound_network) - **✅ HAS DQ RULES (Centralized Delta Table Pattern)**
# MAGIC - table_lineage (system.access.table_lineage)
# MAGIC 
# MAGIC **DQ Pattern:** Centralized Delta Table
# MAGIC - Rules stored in: catalog.schema.dq_rules (Delta table)
# MAGIC - Loaded via: dq_rules_loader module
# MAGIC - Applied with: @dlt.expect_all_or_drop()
# MAGIC - Reference: https://docs.databricks.com/aws/en/ldp/expectation-patterns?language=Delta%C2%A0Table

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
print("BRONZE PIPELINE CONFIGURATION")
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
# MAGIC ## Audit Logs Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("audit"),  # ✅ Fully qualified name
    comment="Bronze layer ingestion of system.access.audit - includes records for all audit events from workspaces in the region",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.access.audit",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("audit"))
@dlt.expect_all(get_warning_rules_for_table("audit"))
def audit():
    """
    Streams audit log events from system.access.audit.
    
    Contains all audit events for workspace and account-level actions.
    Includes user identity, service name, action name, and request/response details.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.access.audit")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Clean Room Events Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("clean_room_events"),  # ✅ Fully qualified name
    comment="Bronze layer ingestion of system.access.clean_room_events - captures events related to clean rooms",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.access.clean_room_events",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("clean_room_events"))
@dlt.expect_all(get_warning_rules_for_table("clean_room_events"))
def clean_room_events():
    """
    Streams clean room events from system.access.clean_room_events.
    
    Tracks clean room creation, deletion, asset updates, and notebook execution events.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.access.clean_room_events")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Column Lineage Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("column_lineage"),  # ✅ Fully qualified name
    comment="Bronze layer ingestion of system.access.column_lineage - includes a record for each read or write event on a Unity Catalog column",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.access.column_lineage",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("column_lineage"))
@dlt.expect_all(get_warning_rules_for_table("column_lineage"))
def column_lineage():
    """
    Streams column-level lineage events from system.access.column_lineage.
    
    Tracks data lineage at the column level for Unity Catalog tables.
    Does not include events without a source.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.access.column_lineage")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚠️ DISABLED: Inbound Network Access Events Table
# MAGIC **Reason:** Delta Sharing incompatibility - table has Deletion Vectors enabled
# MAGIC **Error:** `DS_UNSUPPORTED_DELTA_TABLE_FEATURES: Table features delta.enableDeletionVectors are found`
# MAGIC **Solution:** This table should be ingested via non-streaming MERGE instead

# COMMAND ----------

# @dlt.table(
#     name=get_bronze_table_fqn("inbound_network"),  # ✅ Fully qualified name
#     comment="Bronze layer ingestion of system.access.inbound_network - records events for denied inbound access to workspace by ingress policy",
#     table_properties={
#         "delta.enableChangeDataFeed": "true",
#         "delta.autoOptimize.optimizeWrite": "true",
#         "delta.autoOptimize.autoCompact": "true",
#         "layer": "bronze",
#         "source_system": "databricks_system_tables",
#         "domain": "access",
#         "entity_type": "fact",
#         "contains_pii": "true",
#         "data_classification": "confidential",
#         "business_owner": "Platform Operations",
#         "technical_owner": "Data Engineering",
#         "source_table": "system.access.inbound_network",
#         "retention_period": "30_days"
#     },
#     cluster_by_auto=True
# )
# def inbound_network():
#     """
#     Streams inbound network access denial events from system.access.inbound_network.
#     
#     Records denied inbound access attempts, useful for security monitoring.
#     Shorter retention period (30 days).
#     """
#     return (
#         spark.readStream
#         .option("skipChangeCommits", "true")
#         .option("mergeSchema", "true")
#         .table("system.access.inbound_network")
#         .withColumn("bronze_ingestion_timestamp", current_timestamp())
#     )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Outbound Network Access Events Table - TESTING DQ RULES

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("outbound_network"),  # ✅ Fully qualified name
    comment="Bronze layer ingestion of system.access.outbound_network - records events for denied outbound internet access from account",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.access.outbound_network",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("outbound_network"))
def outbound_network():
    """
    Streams outbound network access denial events from system.access.outbound_network.
    
    Records denied outbound access attempts (DNS, IP, storage).
    Useful for compliance and security monitoring.
    
    🎯 Data Quality Pattern: Centralized Delta Table
    - Rules loaded from: dq_rules Delta table
    - Via: dq_rules_loader.get_critical_rules_for_table()
    - Current rules: workspace_id and event_time NOT NULL checks
    
    ✅ CRITICAL LEARNINGS:
    1. Fully qualified table names REQUIRED: name=get_bronze_table_fqn("table_name")
    2. Column names MUST match source table EXACTLY (event_time, NOT timestamp!)
    3. Rules centralized in Delta table for easy maintenance across 20+ tables
    4. "key not found" error = INVALID COLUMN NAMES in expectations!
    
    References:
    - https://docs.databricks.com/aws/en/ldp/expectation-patterns?language=Delta%C2%A0Table
    - @07-dlt-expectations-patterns.mdc
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.access.outbound_network")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table Lineage Table

# COMMAND ----------

@dlt.table(
    name=get_bronze_table_fqn("table_lineage"),  # ✅ Fully qualified name
    comment="Bronze layer ingestion of system.access.table_lineage - includes a record for each read or write event on a Unity Catalog table or path",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.access.table_lineage",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
def table_lineage():
    """
    Streams table-level lineage events from system.access.table_lineage.
    
    Tracks data lineage at the table level for Unity Catalog tables and paths.
    Includes entity metadata for jobs, notebooks, dashboards, pipelines, and queries.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.access.table_lineage")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
