# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - MLflow Domain
# MAGIC
# MAGIC ## TRAINING MATERIAL: Graceful Handling of Missing Tables
# MAGIC
# MAGIC This notebook demonstrates defensive coding for optional source tables.
# MAGIC MLflow system tables may not exist if MLflow is not used in all workspaces.
# MAGIC
# MAGIC ### The Problem
# MAGIC
# MAGIC ```python
# MAGIC # This will FAIL if table doesn't exist
# MAGIC bronze_df = spark.table(bronze_table)  # AnalysisException!
# MAGIC ```
# MAGIC
# MAGIC ### The Solution: Try/Except Pattern
# MAGIC
# MAGIC ```python
# MAGIC def merge_dim_experiment(...):
# MAGIC     bronze_table = f"{catalog}.{bronze_schema}.experiments_latest"
# MAGIC     
# MAGIC     # Graceful handling of missing source
# MAGIC     try:
# MAGIC         bronze_raw = spark.table(bronze_table)
# MAGIC     except Exception as e:
# MAGIC         print(f"  ⚠️ Bronze table not found: {bronze_table}")
# MAGIC         print(f"  Skipping dim_experiment")
# MAGIC         return 0  # Return 0 records merged
# MAGIC     
# MAGIC     # Continue with normal processing...
# MAGIC ```
# MAGIC
# MAGIC ### When to Use This Pattern
# MAGIC
# MAGIC | Table Type | Use Pattern? | Reason |
# MAGIC |------------|--------------|--------|
# MAGIC | Core system tables | No | Always exist |
# MAGIC | MLflow tables | Yes | MLflow may not be enabled |
# MAGIC | Marketplace tables | Yes | Marketplace optional |
# MAGIC | Model Serving tables | Yes | Serving may not be used |
# MAGIC
# MAGIC **Tables:**
# MAGIC - dim_experiment (from mlflow.experiments_latest)
# MAGIC - fact_mlflow_runs (from mlflow.runs_latest)
# MAGIC - fact_mlflow_run_metrics_history (from mlflow.run_metrics_history)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, lit, to_json
)
from merge_helpers import (
    deduplicate_bronze,
    merge_dimension_table,
    merge_fact_table,
    print_merge_summary
)

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Bronze Schema: {bronze_schema}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, bronze_schema, gold_schema

# COMMAND ----------

def merge_dim_experiment(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_experiment from Bronze to Gold (SCD Type 1).
    
    Bronze Source: system.mlflow.experiments_latest
    Gold Table: dim_experiment
    Primary Key: workspace_id, experiment_id (composite)
    Grain: One row per experiment per workspace
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_experiment")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.experiments_latest"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping dim_experiment")
        return 0
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "experiment_id"],
        order_by_column="update_time"
    )
    
    # Select columns matching Gold schema
    updates_df = bronze_df.select(
        "account_id",
        "update_time",
        "delete_time",
        "workspace_id",
        "experiment_id",
        "name",
        "create_time"
    )
    
    # MERGE to Gold (SCD Type 1)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_experiment",
        business_keys=["workspace_id", "experiment_id"],
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_experiment", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def merge_fact_mlflow_runs(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_mlflow_runs from Bronze to Gold.
    
    Bronze Source: system.mlflow.runs_latest
    Gold Table: fact_mlflow_runs
    Primary Key: workspace_id, run_id (composite)
    Grain: One row per training run per workspace
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_mlflow_runs")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.runs_latest"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_mlflow_runs")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "run_id"],
        order_by_column="update_time"
    )
    
    # Serialize nested fields to JSON
    updates_df = (
        bronze_df
        .withColumn("params_json",
                    when(col("params").isNotNull(), to_json(col("params")))
                    .otherwise(lit(None)))
        .withColumn("tags_json",
                    when(col("tags").isNotNull(), to_json(col("tags")))
                    .otherwise(lit(None)))
        .withColumn("aggregated_metrics_json",
                    when(col("aggregated_metrics").isNotNull(), to_json(col("aggregated_metrics")))
                    .otherwise(lit(None)))
        .select(
            "account_id",
            "update_time",
            "delete_time",
            "workspace_id",
            "run_id",
            "experiment_id",
            "created_by",
            "start_time",
            "end_time",
            "run_name",
            "status",
            "params_json",
            "tags_json",
            "aggregated_metrics_json"
        )
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_mlflow_runs",
        primary_keys=["workspace_id", "run_id"],
        validate_schema=True
    )
    
    print_merge_summary("fact_mlflow_runs", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def merge_fact_mlflow_run_metrics_history(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_mlflow_run_metrics_history from Bronze to Gold.
    
    Bronze Source: system.mlflow.run_metrics_history
    Gold Table: fact_mlflow_run_metrics_history
    Primary Key: workspace_id, run_id, metric_name, metric_time (composite)
    Grain: One row per metric per time point per run
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_mlflow_run_metrics_history")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.run_metrics_history"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_mlflow_run_metrics_history")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "run_id", "metric_name", "metric_time"],
        order_by_column="insert_time"
    )
    
    # Select columns matching Gold schema
    updates_df = bronze_df.select(
        "account_id",
        "insert_time",
        "record_id",
        "workspace_id",
        "experiment_id",
        "run_id",
        "metric_name",
        "metric_time",
        "metric_step",
        "metric_value"
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_mlflow_run_metrics_history",
        primary_keys=["workspace_id", "run_id", "metric_name", "metric_time"],
        validate_schema=True
    )
    
    print_merge_summary("fact_mlflow_run_metrics_history", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for MLflow domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - MLFLOW DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - MLflow").getOrCreate()
    
    try:
        # Merge dimension first
        print("\nStep 1: Merging dim_experiment...")
        merge_dim_experiment(spark, catalog, bronze_schema, gold_schema)
        
        # Merge facts (in dependency order)
        print("\nStep 2: Merging fact_mlflow_runs...")
        merge_fact_mlflow_runs(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 3: Merging fact_mlflow_run_metrics_history...")
        merge_fact_mlflow_run_metrics_history(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ MLflow domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during MLflow domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()




