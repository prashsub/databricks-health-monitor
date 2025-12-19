# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Query Performance Domain
# MAGIC
# MAGIC Merges Query Performance dimension and fact tables from Bronze to Gold.
# MAGIC
# MAGIC **Tables:**
# MAGIC - dim_warehouse (from compute.warehouses)
# MAGIC - fact_query_history (from query.history)
# MAGIC - fact_warehouse_events (from compute.warehouse_events)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, when, lit, to_json
)
from merge_helpers import (
    deduplicate_bronze,
    merge_dimension_table,
    merge_fact_table,
    flatten_struct_fields,
    print_merge_summary,
    get_incremental_filter
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

def merge_dim_warehouse(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_warehouse from Bronze to Gold (SCD Type 1).
    
    Bronze Source: system.compute.warehouses → Bronze: warehouses
    Gold Table: dim_warehouse
    Primary Key: workspace_id, warehouse_id (composite)
    Grain: One row per warehouse per workspace
    
    Column Mapping (Bronze → Gold):
    - Direct copy: warehouse_id, workspace_id, account_id, warehouse_name, warehouse_type,
                   warehouse_channel, warehouse_size, min_clusters, max_clusters,
                   auto_stop_minutes, change_time, delete_time, created_by
    - JSON serialization: tags → tags_json
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_warehouse")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.warehouses"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "warehouse_id"],
        order_by_column="change_time"
    )
    
    # Prepare updates
    updates_df = (
        bronze_df
        # Serialize tags to JSON string
        .withColumn("tags_json",
                    when(col("tags").isNotNull(), to_json(col("tags")))
                    .otherwise(lit(None)))
        .select(
            "warehouse_id",
            "workspace_id",
            "account_id",
            "warehouse_name",
            "warehouse_type",
            "warehouse_channel",
            "warehouse_size",
            "min_clusters",
            "max_clusters",
            "auto_stop_minutes",
            "change_time",
            "delete_time",
            "created_by",
            "tags_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (SCD Type 1)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_warehouse",
        business_keys=["workspace_id", "warehouse_id"],
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_warehouse", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_query_history(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_query_history from Bronze to Gold (TRUE INCREMENTAL).
    
    Bronze Source: system.query.history → Bronze: query_history
    Gold Table: fact_query_history
    Primary Key: statement_id (unique identifier)
    Grain: One row per query execution
    
    ⚠️ INCREMENTAL PATTERN:
    - First run: Gold is empty → process ALL historical data (500M+ records, will be slow)
    - Subsequent runs: Only process records NEWER than Gold's max(execution_end_time) → fast!
    
    Column Mapping (Bronze → Gold):
    - Direct copy: All top-level performance metrics
    - Flattened compute: type, cluster_id, warehouse_id
    - Flattened query_source: job_info, legacy_dashboard_id, dashboard_id, alert_id,
                               notebook_id, sql_query_id, genie_space_id, pipeline_info
    - Flattened query_parameters: named_parameters, pos_parameters, truncated
    - MAP type: query_tags (direct copy if MAP, already correct type)
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_query_history")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.query_history"
    gold_table = f"{catalog}.{gold_schema}.fact_query_history"
    
    # Get incremental filter from Gold table's high-water mark
    # Use end_time as watermark for query history (Bronze column name)
    # NOTE: 90-day limit on first run for this 68M+ record table
    incremental_filter = get_incremental_filter(
        spark, gold_table, "end_time",
        max_initial_days=90  # Limit first run to last 90 days
    )
    
    # Read Bronze source (with incremental filter if not first run)
    bronze_raw = spark.table(bronze_table)
    if incremental_filter:
        bronze_raw = bronze_raw.filter(incremental_filter)
    
    # Show record count
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No new records to process - Gold is up to date!")
        return 0
    
    # Deduplicate on statement_id (unique identifier)
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["statement_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Flatten simple nested fields (compute)
    compute_fields = {
        "type": "compute_type",
        "cluster_id": "compute_cluster_id",
        "warehouse_id": "compute_warehouse_id"
    }
    bronze_df = flatten_struct_fields(bronze_df, "compute", compute_fields)
    
    # For complex nested types, serialize to JSON strings
    # Gold DDL expects STRING for these columns
    updates_df = (
        bronze_df
        # Serialize query_tags MAP to JSON string
        .withColumn("query_tags_json",
                    when(col("query_tags").isNotNull(), to_json(col("query_tags")))
                    .otherwise(lit(None)))
        # Serialize query_source nested STRUCTs to JSON
        .withColumn("query_source_job_info",
                    when(col("query_source.job_info").isNotNull(), to_json(col("query_source.job_info")))
                    .otherwise(lit(None)))
        .withColumn("query_source_legacy_dashboard_id", col("query_source.legacy_dashboard_id"))
        .withColumn("query_source_dashboard_id", col("query_source.dashboard_id"))
        .withColumn("query_source_alert_id", col("query_source.alert_id"))
        .withColumn("query_source_notebook_id", col("query_source.notebook_id"))
        .withColumn("query_source_sql_query_id", col("query_source.sql_query_id"))
        .withColumn("query_source_genie_space_id", col("query_source.genie_space_id"))
        .withColumn("query_source_pipeline_info",
                    when(col("query_source.pipeline_info").isNotNull(), to_json(col("query_source.pipeline_info")))
                    .otherwise(lit(None)))
        # Serialize query_parameters complex nested types to JSON
        .withColumn("query_parameters_named_parameters",
                    when(col("query_parameters.named_parameters").isNotNull(), to_json(col("query_parameters.named_parameters")))
                    .otherwise(lit(None)))
        .withColumn("query_parameters_pos_parameters",
                    when(col("query_parameters.pos_parameters").isNotNull(), to_json(col("query_parameters.pos_parameters")))
                    .otherwise(lit(None)))
        .withColumn("query_parameters_truncated", col("query_parameters.truncated"))
        # Cast read_io_cache_percent from ByteType to STRING
        .withColumn("read_io_cache_percent", col("read_io_cache_percent").cast("string"))
        .select(
            # Core identifiers
            "account_id",
            "workspace_id",
            "statement_id",
            "executed_by",
            "session_id",
            "execution_status",
            "executed_by_user_id",
            "statement_text",
            "statement_type",
            "error_message",
            "client_application",
            "client_driver",
            
            # Performance metrics
            "total_duration_ms",
            "waiting_for_compute_duration_ms",
            "waiting_at_capacity_duration_ms",
            "execution_duration_ms",
            "compilation_duration_ms",
            "total_task_duration_ms",
            "result_fetch_duration_ms",
            
            # Timestamps
            "start_time",
            "end_time",
            "update_time",
            
            # I/O metrics
            "read_partitions",
            "pruned_files",
            "read_files",
            "read_rows",
            "produced_rows",
            "read_bytes",
            "read_io_cache_percent",
            "from_result_cache",
            "spilled_local_bytes",
            "written_bytes",
            "shuffle_read_bytes",
            "written_rows",
            "written_files",
            "cache_origin_statement_id",
            
            # Identity
            "executed_as_user_id",
            "executed_as",
            
            # Flattened compute (simple types)
            "compute_type",
            "compute_cluster_id",
            "compute_warehouse_id",
            
            # Query source (JSON serialized for complex types)
            "query_source_job_info",
            "query_source_legacy_dashboard_id",
            "query_source_dashboard_id",
            "query_source_alert_id",
            "query_source_notebook_id",
            "query_source_sql_query_id",
            "query_source_genie_space_id",
            "query_source_pipeline_info",
            
            # Query parameters (JSON serialized)
            "query_parameters_named_parameters",
            "query_parameters_pos_parameters",
            "query_parameters_truncated",
            
            # Query tags (JSON serialized)
            "query_tags_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (transaction grain)
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_query_history",
        primary_keys=["statement_id"],
        validate_schema=False  # Disabled for performance (500M+ records)
    )
    
    print_merge_summary("fact_query_history", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_warehouse_events(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_warehouse_events from Bronze to Gold.
    
    Bronze Source: system.compute.warehouse_events → Bronze: warehouse_events
    Gold Table: fact_warehouse_events
    Primary Key: workspace_id, warehouse_id, event_time (composite)
    Grain: One row per warehouse event (start, stop, scale)
    
    Column Mapping (Bronze → Gold):
    - Direct copy: All columns (no transformations needed)
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_warehouse_events")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.warehouse_events"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite PK
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "warehouse_id", "event_time"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Prepare updates (all direct copy)
    updates_df = bronze_df.select(
        "account_id",
        "workspace_id",
        "warehouse_id",
        "event_type",
        "cluster_count",
        "event_time"
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (event grain)
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_warehouse_events",
        primary_keys=["workspace_id", "warehouse_id", "event_time"],
        validate_schema=True
    )
    
    print_merge_summary("fact_warehouse_events", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Query Performance domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - QUERY PERFORMANCE DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Query Performance").getOrCreate()
    
    try:
        # Merge dimension first
        print("\nStep 1: Merging dim_warehouse...")
        merge_dim_warehouse(spark, catalog, bronze_schema, gold_schema)
        
        # Merge facts
        print("\nStep 2: Merging fact_query_history...")
        merge_fact_query_history(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 3: Merging fact_warehouse_events...")
        merge_fact_warehouse_events(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Query Performance domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Query Performance domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

