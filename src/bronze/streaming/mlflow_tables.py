# Databricks notebook source
# MAGIC %md
# MAGIC # System MLflow Tables - DLT Streaming Pipeline
# MAGIC 
# MAGIC Bronze layer ingestion of system.mlflow.* tables with schema evolution.
# MAGIC 
# MAGIC **Tables ingested:**
# MAGIC - experiments_latest (system.mlflow.experiments_latest)
# MAGIC - runs_latest (system.mlflow.runs_latest)
# MAGIC - run_metrics_history (system.mlflow.run_metrics_history)
# MAGIC 
# MAGIC **Pattern:** Stream from system tables with skipChangeCommits and schema evolution enabled

# COMMAND ----------

import dlt
from pyspark.sql.functions import current_timestamp

# COMMAND ----------

# MAGIC %md
# MAGIC ## MLflow Experiments Table

# COMMAND ----------

@dlt.table(
    name="experiments_latest",
    comment="Bronze layer ingestion of system.mlflow.experiments_latest - each row represents an experiment created in the Databricks-managed MLflow system",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "mlflow",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.mlflow.experiments_latest",
        "retention_period": "180_days"
    },
    cluster_by_auto=True
)
def experiments_latest():
    """
    Streams MLflow experiment metadata from system.mlflow.experiments_latest.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks experiment definitions including:
    - Experiment ID and name
    - Workspace location
    - Create and update times
    - Delete status
    
    Shorter retention period (180 days) for MLflow tracking data.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.mlflow.experiments_latest")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## MLflow Runs Table

# COMMAND ----------

@dlt.table(
    name="runs_latest",
    comment="Bronze layer ingestion of system.mlflow.runs_latest - each row represents a run created in the Databricks-managed MLflow system",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "mlflow",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.mlflow.runs_latest",
        "retention_period": "180_days"
    },
    cluster_by_auto=True
)
def runs_latest():
    """
    Streams MLflow run metadata from system.mlflow.runs_latest.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks model training runs including:
    - Run ID, name, and status
    - Experiment association
    - Creator identity
    - Start and end times
    - Parameters and tags
    - Aggregated metrics (min, max, latest)
    
    Critical for ML experiment tracking and model governance.
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.mlflow.runs_latest")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## MLflow Run Metrics History Table

# COMMAND ----------

@dlt.table(
    name="run_metrics_history",
    comment="Bronze layer ingestion of system.mlflow.run_metrics_history - holds timeseries metrics logged to MLflow for model training, evaluation, or agent development",
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "bronze",
        "source_system": "databricks_system_tables",
        "domain": "mlflow",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Platform Operations",
        "technical_owner": "Data Engineering",
        "source_table": "system.mlflow.run_metrics_history",
        "retention_period": "180_days"
    },
    cluster_by_auto=True
)
def run_metrics_history():
    """
    Streams MLflow run metrics timeseries from system.mlflow.run_metrics_history.
    
    Data Quality Rules (loaded from dq_rules Delta table):
    - Rules are user-configurable via frontend app
    - Critical rules fail records, warnings log only
    - Rules are queried at pipeline runtime (always latest)
    
    Tracks all metrics logged during model training:
    - Metric name and value
    - Metric timestamp and step
    - Run and experiment association
    
    High-volume table with detailed metric history for ML observability.
    Shorter retention period (180 days).
    """
    return (
        spark.readStream
        .option("skipChangeCommits", "true")
        .option("mergeSchema", "true")
        .table("system.mlflow.run_metrics_history")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )

