# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Lakeflow Domain
# MAGIC
# MAGIC ## TRAINING MATERIAL: Complex Type Serialization Pattern
# MAGIC
# MAGIC This notebook demonstrates handling complex types (arrays, maps, structs)
# MAGIC when moving from Bronze to Gold layer.
# MAGIC
# MAGIC ### The Problem: Complex Types in Gold
# MAGIC
# MAGIC Bronze tables preserve source schema including complex types:
# MAGIC - `tags` MAP<STRING, STRING>
# MAGIC - `parameters` ARRAY<STRUCT>
# MAGIC - `settings` STRUCT<...>
# MAGIC
# MAGIC Gold tables often need simpler types for:
# MAGIC - BI tool compatibility (many don't handle complex types)
# MAGIC - Metric View queries (simpler predicates)
# MAGIC - Genie natural language (easier to interpret)
# MAGIC
# MAGIC ### Serialization Pattern
# MAGIC
# MAGIC ```python
# MAGIC # Serialize complex type to JSON string
# MAGIC updates_df = (
# MAGIC     bronze_df
# MAGIC     .withColumn("tags_json",
# MAGIC                 when(col("tags").isNotNull(), to_json(col("tags")))
# MAGIC                 .otherwise(lit(None)))
# MAGIC     .withColumn("parameters_json",
# MAGIC                 when(col("parameters").isNotNull(), to_json(col("parameters")))
# MAGIC                 .otherwise(lit(None)))
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC ### When to Serialize vs Keep Complex
# MAGIC
# MAGIC | Keep Complex | Serialize to JSON |
# MAGIC |--------------|-------------------|
# MAGIC | Need array functions | BI tool queries |
# MAGIC | Explode operations | Metric Views |
# MAGIC | Nested analytics | Genie queries |
# MAGIC | Internal pipelines | Reporting/dashboards |
# MAGIC
# MAGIC **Tables:**
# MAGIC - dim_job (from lakeflow.jobs)
# MAGIC - dim_job_task (from lakeflow.job_tasks)
# MAGIC - dim_pipeline (from lakeflow.pipelines)
# MAGIC - fact_job_run_timeline (from lakeflow.job_run_timeline)
# MAGIC - fact_job_task_run_timeline (from lakeflow.job_task_run_timeline)
# MAGIC - fact_pipeline_update_timeline (from lakeflow.pipeline_update_timeline)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, when, lit, to_json,
    to_date, unix_timestamp, lower, size
)
from merge_helpers import (
    deduplicate_bronze,
    merge_dimension_table,
    merge_fact_table,
    flatten_struct_fields,
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

def merge_dim_job(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_job from Bronze to Gold (SCD Type 2).
    
    Bronze Source: system.lakeflow.jobs → Bronze: jobs
    Gold Table: dim_job
    Primary Key: workspace_id, job_id (composite)
    Grain: One row per job per workspace (tracks changes over time)
    
    Column Mapping (Bronze → Gold):
    - Direct copy: account_id, workspace_id, job_id, name, creator_id, run_as, change_time, delete_time, description
    - JSON serialization: tags → tags_json (to_json(tags))
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_job")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.jobs"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "job_id"],
        order_by_column="change_time"  # Use change_time for latest version
    )
    
    # Prepare updates
    updates_df = (
        bronze_df
        # Serialize tags to JSON string
        .withColumn("tags_json",
                    when(col("tags").isNotNull(), to_json(col("tags")))
                    .otherwise(lit(None)))
        .select(
            "account_id",
            "workspace_id",
            "job_id",
            "name",
            "creator_id",
            "run_as",
            "change_time",
            "delete_time",
            "description",
            "tags_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (SCD Type 2)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_job",
        business_keys=["workspace_id", "job_id"],
        scd_type=1,  # SCD Type 1 - overwrite (no is_current column in Gold)
        validate_schema=True
    )
    
    print_merge_summary("dim_job", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_dim_job_task(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_job_task from Bronze to Gold.
    
    Bronze Source: system.lakeflow.job_tasks → Bronze: job_tasks
    Gold Table: dim_job_task
    Primary Key: workspace_id, job_id, task_key (composite)
    Grain: One row per task per job
    
    Column Mapping (Bronze → Gold):
    - Direct copy: account_id, workspace_id, job_id, task_key, change_time, delete_time
    - JSON serialization: depends_on_keys → depends_on_keys_json
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_job_task")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.job_tasks"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "job_id", "task_key"],
        order_by_column="change_time"
    )
    
    # Prepare updates
    updates_df = (
        bronze_df
        # Serialize depends_on_keys array to JSON string (Bronze column name is depends_on_keys)
        .withColumn("depends_on_keys_json",
                    when(col("depends_on_keys").isNotNull(), to_json(col("depends_on_keys")))
                    .otherwise(lit(None)))
        .select(
            "account_id",
            "workspace_id",
            "job_id",
            "task_key",
            "change_time",
            "delete_time",
            "depends_on_keys_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_job_task",
        business_keys=["workspace_id", "job_id", "task_key"],
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_job_task", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_dim_pipeline(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_pipeline from Bronze to Gold.
    
    Bronze Source: system.lakeflow.pipelines → Bronze: pipelines
    Gold Table: dim_pipeline
    Primary Key: workspace_id, pipeline_id (composite)
    Grain: One row per pipeline per workspace
    
    ⚠️ CRITICAL COLUMN RENAME:
    - Bronze: pipeline_id
    - Gold: pipeline_id (same name, no change needed)
    
    Column Mapping (Bronze → Gold):
    - Direct copy: workspace_id, pipeline_id, pipeline_type, name, created_by, run_as, change_time, delete_time, account_id
    - Flattened: settings.photon → settings_photon
    - Flattened: settings.development → settings_development
    - Flattened: settings.continuous → settings_continuous
    - Flattened: settings.serverless → settings_serverless
    - Flattened: settings.edition → settings_edition
    - Flattened: settings.channel → settings_channel
    - JSON serialization: tags → tags_json
    - JSON serialization: configuration → configuration_json
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_pipeline")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.pipelines"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "pipeline_id"],
        order_by_column="change_time"
    )
    
    # Flatten settings struct
    settings_fields = {
        "photon": "settings_photon",
        "development": "settings_development",
        "continuous": "settings_continuous",
        "serverless": "settings_serverless",
        "edition": "settings_edition",
        "channel": "settings_channel"
    }
    bronze_df = flatten_struct_fields(bronze_df, "settings", settings_fields)
    
    # Prepare updates
    updates_df = (
        bronze_df
        # Serialize complex types to JSON
        .withColumn("tags_json",
                    when(col("tags").isNotNull(), to_json(col("tags")))
                    .otherwise(lit(None)))
        .withColumn("configuration_json",
                    when(col("configuration").isNotNull(), to_json(col("configuration")))
                    .otherwise(lit(None)))
        .select(
            "workspace_id",
            "pipeline_id",
            "pipeline_type",
            "name",
            "created_by",
            "run_as",
            "change_time",
            "delete_time",
            "account_id",
            "tags_json",
            "settings_photon",
            "settings_development",
            "settings_continuous",
            "settings_serverless",
            "settings_edition",
            "settings_channel",
            "configuration_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_pipeline",
        business_keys=["workspace_id", "pipeline_id"],
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_pipeline", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_job_run_timeline(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_job_run_timeline from Bronze to Gold.
    
    Bronze Source: system.lakeflow.job_run_timeline → Bronze: job_run_timeline
    Gold Table: fact_job_run_timeline
    Primary Key: workspace_id, run_id (transaction grain)
    Grain: One row per job run (hourly slicing for long runs)
    
    Column Mapping (Bronze → Gold):
    - Direct copy: All top-level columns
    - MAP/ARRAY types: compute_ids (ARRAY), job_parameters (MAP) - already correct type in Bronze
    - Derived: run_date, run_duration_seconds, run_duration_minutes, is_success
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_job_run_timeline")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.job_run_timeline"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite PK
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "run_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Prepare updates - Gold DDL has native ARRAY + JSON for nested MAP + derived columns
    # Note: Bronze job_parameters is MAP<STRING, MAP<STRING, STRING>> but Gold expects MAP<STRING, STRING>
    # Since it's nested, we serialize to JSON string and store in a STRING column
    updates_df = (
        bronze_df
        # Serialize nested job_parameters to JSON (Bronze has nested MAP, not compatible with Gold)
        .withColumn("job_parameters",
                    when(col("job_parameters").isNotNull(), to_json(col("job_parameters")))
                    .otherwise(lit(None)))
        # Derived columns per Gold YAML spec
        .withColumn("run_date", to_date(col("period_start_time")))
        .withColumn("run_duration_seconds",
                    when(col("period_end_time").isNotNull() & col("period_start_time").isNotNull(),
                         unix_timestamp(col("period_end_time")) - unix_timestamp(col("period_start_time")))
                    .otherwise(lit(None)).cast("bigint"))
        .withColumn("run_duration_minutes",
                    when(col("run_duration_seconds").isNotNull(),
                         col("run_duration_seconds") / 60.0)
                    .otherwise(lit(None)))
        .withColumn("is_success",
                    when(col("result_state") == "SUCCESS", lit(True))
                    .otherwise(lit(False)))
        .select(
            # Core columns
            "account_id",
            "workspace_id",
            "job_id",
            "run_id",
            "period_start_time",
            "period_end_time",
            "trigger_type",
            "result_state",
            "run_type",
            "run_name",
            "termination_code",
            
            # Native ARRAY type (Gold DDL has native ARRAY<STRING>)
            "compute_ids",
            # JSON serialized (Bronze nested MAP incompatible with Gold simple MAP)
            "job_parameters",
            
            # Derived columns
            "run_date",
            "run_duration_seconds",
            "run_duration_minutes",
            "is_success"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (transaction grain)
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_job_run_timeline",
        primary_keys=["workspace_id", "run_id"],
        validate_schema=True
    )
    
    print_merge_summary("fact_job_run_timeline", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_job_task_run_timeline(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_job_task_run_timeline from Bronze to Gold.
    
    Bronze Source: system.lakeflow.job_task_run_timeline → Bronze: job_task_run_timeline
    Gold Table: fact_job_task_run_timeline
    Primary Key: workspace_id, run_id (composite)
    Grain: One row per task run
    
    Column Mapping (Bronze → Gold):
    - Direct copy: All top-level columns
    - JSON serialization: compute_ids → compute_ids_json (to_json())
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_job_task_run_timeline")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.job_task_run_timeline"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite PK
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "run_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Prepare updates
    # NOTE: Bronze column is compute_ids (not compute)
    updates_df = (
        bronze_df
        # Serialize compute_ids array to JSON string
        .withColumn("compute_ids_json",
                    when(col("compute_ids").isNotNull(), to_json(col("compute_ids")))
                    .otherwise(lit(None)))
        .select(
            "account_id",
            "workspace_id",
            "job_id",
            "run_id",
            "period_start_time",
            "period_end_time",
            "task_key",
            "result_state",
            "job_run_id",
            "parent_run_id",
            "termination_code",
            "compute_ids_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_job_task_run_timeline",
        primary_keys=["workspace_id", "run_id"],
        validate_schema=True
    )
    
    print_merge_summary("fact_job_task_run_timeline", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_pipeline_update_timeline(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_pipeline_update_timeline from Bronze to Gold.
    
    Bronze Source: system.lakeflow.pipeline_update_timeline → Bronze: pipeline_update_timeline (non-streaming)
    Gold Table: fact_pipeline_update_timeline
    Primary Key: workspace_id, update_id (composite)
    Grain: One row per pipeline update
    
    Column Mapping (Bronze → Gold):
    - Direct copy: workspace_id, update_id, pipeline_id, update_type, request_id, run_as_user_name,
                   trigger_type, result_state, period_start_time, period_end_time, account_id
    - Flattened: trigger_details.job_task → trigger_details_job_task
    - Flattened: compute.type → compute_type
    - Flattened: compute.cluster_id → compute_cluster_id
    - JSON serialization: refresh_selection → refresh_selection_json
    - JSON serialization: full_refresh_selection → full_refresh_selection_json
    - JSON serialization: reset_checkpoint_selection → reset_checkpoint_selection_json
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_pipeline_update_timeline")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.pipeline_update_timeline"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite PK
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "update_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Flatten nested structs
    trigger_details_fields = {"job_task": "trigger_details_job_task"}
    compute_fields = {"type": "compute_type", "cluster_id": "compute_cluster_id"}
    
    bronze_df = flatten_struct_fields(bronze_df, "trigger_details", trigger_details_fields)
    bronze_df = flatten_struct_fields(bronze_df, "compute", compute_fields)
    
    # Prepare updates
    updates_df = (
        bronze_df
        # Serialize structs/arrays to JSON strings
        .withColumn("trigger_details_job_task",
                    when(col("trigger_details_job_task").isNotNull(), to_json(col("trigger_details_job_task")))
                    .otherwise(lit(None)))
        .withColumn("refresh_selection_json",
                    when(col("refresh_selection").isNotNull(), to_json(col("refresh_selection")))
                    .otherwise(lit(None)))
        .withColumn("full_refresh_selection_json",
                    when(col("full_refresh_selection").isNotNull(), to_json(col("full_refresh_selection")))
                    .otherwise(lit(None)))
        .withColumn("reset_checkpoint_selection_json",
                    when(col("reset_checkpoint_selection").isNotNull(), to_json(col("reset_checkpoint_selection")))
                    .otherwise(lit(None)))
        .select(
            "workspace_id",
            "pipeline_id",
            "update_id",
            "update_type",
            "request_id",
            "run_as_user_name",
            "trigger_type",
            "result_state",
            "period_start_time",
            "period_end_time",
            "account_id",
            "trigger_details_job_task",
            "compute_type",
            "compute_cluster_id",
            "refresh_selection_json",
            "full_refresh_selection_json",
            "reset_checkpoint_selection_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_pipeline_update_timeline",
        primary_keys=["workspace_id", "update_id"],
        validate_schema=True
    )
    
    print_merge_summary("fact_pipeline_update_timeline", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Lakeflow domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - LAKEFLOW DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Lakeflow").getOrCreate()
    
    try:
        # Merge dimensions first (dependencies)
        print("\nStep 1: Merging dim_job...")
        merge_dim_job(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 2: Merging dim_job_task (depends on dim_job)...")
        merge_dim_job_task(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 3: Merging dim_pipeline...")
        merge_dim_pipeline(spark, catalog, bronze_schema, gold_schema)
        
        # Merge facts
        print("\nStep 4: Merging fact_job_run_timeline...")
        merge_fact_job_run_timeline(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 5: Merging fact_job_task_run_timeline...")
        merge_fact_job_task_run_timeline(spark, catalog, bronze_schema, gold_schema)
        
        # NOTE: pipeline_update_timeline is ingested via non-streaming MERGE (not DLT)
        # due to Deletion Vectors incompatibility. Bronze table is populated by nonstreaming/merge.py
        print("\nStep 6: Merging fact_pipeline_update_timeline...")
        merge_fact_pipeline_update_timeline(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Lakeflow domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Lakeflow domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()





