# Databricks notebook source
# MAGIC %md
# MAGIC # System Lakeflow Tables - DLT Streaming Pipeline
# MAGIC
# MAGIC ## TRAINING MATERIAL: Job/Pipeline Monitoring Data Ingestion
# MAGIC
# MAGIC This notebook ingests Lakeflow (Jobs & Pipelines) system tables for
# MAGIC reliability and performance monitoring.
# MAGIC
# MAGIC ### Lakeflow Domain Tables
# MAGIC
# MAGIC | Table | Type | Content | Update Frequency |
# MAGIC |-------|------|---------|------------------|
# MAGIC | jobs | Dimension | Job definitions | On change |
# MAGIC | job_tasks | Dimension | Task configurations | On change |
# MAGIC | pipelines | Dimension | DLT pipeline configs | On change |
# MAGIC | job_run_timeline | Fact | Job execution history | Continuous |
# MAGIC | job_task_run_timeline | Fact | Task execution history | Continuous |
# MAGIC | pipeline_update_timeline | Fact | Pipeline run history | Continuous |
# MAGIC
# MAGIC ### Timeline Table Structure
# MAGIC
# MAGIC Timeline tables have a special structure for long-running operations:
# MAGIC - Jobs running >1 hour are split into hourly intervals
# MAGIC - Each interval has start_time and end_time
# MAGIC - Final interval has result_state and termination_code
# MAGIC
# MAGIC ```
# MAGIC Job Run (3 hours):
# MAGIC ├── Interval 1: [00:00, 01:00) - RUNNING
# MAGIC ├── Interval 2: [01:00, 02:00) - RUNNING
# MAGIC └── Interval 3: [02:00, 02:45] - SUCCESS (termination)
# MAGIC ```
# MAGIC
# MAGIC This enables accurate resource attribution per hour for cost analysis.
# MAGIC
# MAGIC **Tables ingested:**
# MAGIC - job_run_timeline (system.lakeflow.job_run_timeline)
# MAGIC - job_task_run_timeline (system.lakeflow.job_task_run_timeline)
# MAGIC - job_tasks (system.lakeflow.job_tasks)
# MAGIC - jobs (system.lakeflow.jobs)
# MAGIC - pipeline_update_timeline (system.lakeflow.pipeline_update_timeline)
# MAGIC - pipelines (system.lakeflow.pipelines)
# MAGIC
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

import dlt
from pyspark.sql.functions import current_timestamp

# COMMAND ----------

# MAGIC %md
# MAGIC ## Job Run Timeline Table

# COMMAND ----------

@dlt.table(
    name="job_run_timeline",
    comment="Bronze layer ingestion of system.lakeflow.job_run_timeline - tracks start and end times of job runs",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "lakeflow",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.lakeflow.job_run_timeline",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
# Temporarily disabled DQ rules
def job_run_timeline():
    """
    Streams job run timeline events from system.lakeflow.job_run_timeline.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks job execution timeline including:
    - Start and end times
    - Trigger type (manual, scheduled, etc.)
    - Run type (workflow, repair, etc.)
    - Result state and termination code
    
    Long-running jobs (>1 hour) are split into hourly intervals.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.lakeflow.job_run_timeline")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Job Task Run Timeline Table

# COMMAND ----------

@dlt.table(
    name="job_task_run_timeline",
    comment="Bronze layer ingestion of system.lakeflow.job_task_run_timeline - tracks start and end times and compute resources used for job task runs",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "lakeflow",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.lakeflow.job_task_run_timeline",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
# Temporarily disabled DQ rules
def job_task_run_timeline():
    """
    Streams job task run timeline events from system.lakeflow.job_task_run_timeline.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks individual task execution within job runs including:
    - Task-level start/end times
    - Compute resources (clusters, warehouses)
    - Result state and termination code
    - Parent run relationships
    
    Long-running tasks (>1 hour) are split into hourly intervals.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.lakeflow.job_task_run_timeline")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Job Tasks Table

# COMMAND ----------

@dlt.table(
    name="job_tasks",
    comment="Bronze layer ingestion of system.lakeflow.job_tasks - tracks all job tasks that run in the account",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "lakeflow",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.lakeflow.job_tasks",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
# Temporarily disabled DQ rules
def job_tasks():
    """
    Streams job task metadata from system.lakeflow.job_tasks.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    SCD Type 2 table tracking task definitions including:
    - Task keys and dependencies
    - Task configuration
    - Change history
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.lakeflow.job_tasks")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Jobs Table

# COMMAND ----------

@dlt.table(
    name="jobs",
    comment="Bronze layer ingestion of system.lakeflow.jobs - tracks all jobs created in the account",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "lakeflow",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.lakeflow.jobs",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
# Temporarily disabled DQ rules
def jobs():
    """
    Streams job metadata from system.lakeflow.jobs.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    SCD Type 2 table tracking job definitions including:
    - Job name and description
    - Creator and run_as identity
    - Tags
    - Change and delete history
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.lakeflow.jobs")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Update Timeline Table
# MAGIC 
# MAGIC **⚠️ TEMPORARILY DISABLED:** This table has Deletion Vectors enabled, which is incompatible with Delta Sharing streaming.
# MAGIC We will implement this table using a non-streaming MERGE approach instead.

# COMMAND ----------

# TEMPORARILY COMMENTED OUT DUE TO DELETION VECTORS INCOMPATIBILITY
# @dlt.table(
#     name="pipeline_update_timeline",
#     comment="Bronze layer ingestion of system.lakeflow.pipeline_update_timeline - tracks start and end times and compute resources used for pipeline updates",
#     table_properties={
#         "delta.enableChangeDataFeed": "true",
#         "delta.autoOptimize.optimizeWrite": "true",
#         "delta.autoOptimize.autoCompact": "true",
#         "layer": "bronze",
#         "source_system": "databricks_system_tables",
#         "domain": "lakeflow",
#         "entity_type": "fact",
#         "contains_pii": "false",
#         "data_classification": "internal",
#         "business_owner": "Platform Operations",
#         "technical_owner": "Data Engineering",
#         "source_table": "system.lakeflow.pipeline_update_timeline",
#         "retention_period": "365_days"
#     },
#     cluster_by_auto=True
# )
# def pipeline_update_timeline():
#     """
#     Streams DLT pipeline update timeline from system.lakeflow.pipeline_update_timeline.
#     
#     Data Quality Rules (loaded from dq_rules Delta table):
#     - Rules are user-configurable via frontend app
#     - Critical rules fail records, warnings log only
#     - Rules are queried at pipeline runtime (always latest)
#     
#     Tracks DLT pipeline update execution including:
#     - Update start/end times
#     - Update type (full refresh, incremental, etc.)
#     - Trigger type and details
#     - Compute resources used
#     - Result state
#     
#     Long-running updates (>1 hour) are split into hourly intervals.
#     """
#     return (
#         spark.readStream
#         .option("skipChangeCommits", "true")
#         .option("mergeSchema", "true")
#         .table("system.lakeflow.pipeline_update_timeline")
#         .withColumn("bronze_ingestion_timestamp", current_timestamp())
#     )

# COMMAND ----------

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipelines Table

# COMMAND ----------

@dlt.table(
    name="pipelines",
    comment="Bronze layer ingestion of system.lakeflow.pipelines - tracks all pipelines created in the account",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "lakeflow",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.lakeflow.pipelines",
        "retention_period": "365_days"
    },
    cluster_by_auto=True
)
# Temporarily disabled DQ rules
def pipelines():
    """
    Streams DLT pipeline metadata from system.lakeflow.pipelines.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    SCD Type 2 table tracking pipeline definitions including:
    - Pipeline name and type
    - Creator and run_as identity
    - Settings and configuration
    - Tags
    - Change and delete history
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.lakeflow.pipelines")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

