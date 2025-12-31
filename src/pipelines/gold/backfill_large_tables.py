# Databricks notebook source
# MAGIC %md
# MAGIC # Historical Backfill for Large Gold Tables
# MAGIC 
# MAGIC Processes historical data in 1-week chunks to avoid memory issues and timeouts.
# MAGIC Works alongside the incremental job - backfills data BEFORE the current Gold min date.
# MAGIC 
# MAGIC **Tables supported:**
# MAGIC - fact_audit_logs (7B+ records)
# MAGIC - fact_usage (109M+ records)  
# MAGIC - fact_query_history (68M+ records)
# MAGIC 
# MAGIC **Strategy:**
# MAGIC - Get MIN/MAX date from Gold table (what's already been processed)
# MAGIC - Process data in 1-week chunks going backwards
# MAGIC - Uses MERGE to avoid duplicates if chunks overlap
# MAGIC - **RESUMABLE**: Queries Gold table to find what's already processed - if job times out, it resumes automatically
# MAGIC 
# MAGIC **No checkpoint table needed** - the Gold table itself is the source of truth!

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, lit, to_json, lower, current_timestamp,
    to_date, unix_timestamp, year, month
)
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from delta.tables import DeltaTable

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    gold_schema = dbutils.widgets.get("gold_schema")
    table_name = dbutils.widgets.get("table_name")  # fact_audit_logs, fact_usage, fact_query_history
    months_to_backfill = int(dbutils.widgets.get("months_to_backfill"))  # How many months back
    return catalog, bronze_schema, gold_schema, table_name, months_to_backfill

# COMMAND ----------

def get_gold_date_range(spark: SparkSession, gold_table: str, date_column: str):
    """Get the current date range in Gold table."""
    try:
        result = spark.sql(f"""
            SELECT 
                MIN({date_column}) as min_date,
                MAX({date_column}) as max_date,
                COUNT(*) as record_count
            FROM {gold_table}
        """).collect()[0]
        
        return result["min_date"], result["max_date"], result["record_count"]
    except Exception as e:
        print(f"  ⚠️ Could not get Gold date range: {str(e)[:100]}")
        return None, None, 0


# COMMAND ----------

def backfill_fact_audit_logs_chunk(
    spark: SparkSession,
    catalog: str,
    bronze_schema: str,
    gold_schema: str,
    start_date: str,
    end_date: str
) -> int:
    """
    Backfill a single 1-week chunk of fact_audit_logs.
    
    Returns number of records merged.
    """
    from merge_helpers import deduplicate_bronze, flatten_struct_fields, merge_fact_table
    
    bronze_table = f"{catalog}.{bronze_schema}.audit"
    
    print(f"\n  Processing: {start_date} to {end_date}")
    
    # Read Bronze for this date range
    bronze_raw = spark.table(bronze_table).filter(
        f"event_date >= '{start_date}' AND event_date < '{end_date}'"
    )
    
    record_count = bronze_raw.count()
    print(f"    Records in range: {record_count:,}")
    
    if record_count == 0:
        print(f"    ✓ No records in this range")
        return 0
    
    # Deduplicate
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["event_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Flatten nested structs
    user_identity_fields = {"email": "user_identity_email", "subject_name": "user_identity_subject_name"}
    response_fields = {"status_code": "response_status_code", "error_message": "response_error_message", "result": "response_result"}
    identity_metadata_fields = {"run_by": "identity_metadata_run_by", "run_as": "identity_metadata_run_as", "acting_resource": "identity_metadata_acting_resource"}
    
    bronze_df = flatten_struct_fields(bronze_df, "user_identity", user_identity_fields)
    bronze_df = flatten_struct_fields(bronze_df, "response", response_fields)
    bronze_df = flatten_struct_fields(bronze_df, "identity_metadata", identity_metadata_fields)
    
    # Add derived columns
    updates_df = (
        bronze_df
        .withColumn("is_sensitive_action",
                    when(
                        lower(col("action_name")).like("%grant%") |
                        lower(col("action_name")).like("%revoke%") |
                        lower(col("action_name")).like("%delete%") |
                        lower(col("action_name")).like("%secret%") |
                        lower(col("action_name")).like("%permission%") |
                        lower(col("action_name")).like("%token%") |
                        lower(col("action_name")).like("%password%") |
                        lower(col("action_name")).like("%credential%"),
                        lit(True)
                    ).otherwise(lit(False)))
        .withColumn("is_failed_action",
                    when(
                        (col("response_status_code") >= 400) |
                        col("response_error_message").isNotNull(),
                        lit(True)
                    ).otherwise(lit(False)))
        .select(
            "account_id", "workspace_id", "version", "event_time", "event_date",
            "source_ip_address", "user_agent", "session_id", "service_name",
            "action_name", "request_id", "audit_level", "event_id",
            "user_identity_email", "user_identity_subject_name", "request_params",
            "response_status_code", "response_error_message", "response_result",
            "identity_metadata_run_by", "identity_metadata_run_as", "identity_metadata_acting_resource",
            "is_sensitive_action", "is_failed_action"
        )
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_audit_logs",
        primary_keys=["event_id"],
        validate_schema=False  # Skip for performance
    )
    
    print(f"    ✓ Merged {merged_count:,} records")
    return merged_count

# COMMAND ----------

def backfill_fact_usage_chunk(
    spark: SparkSession,
    catalog: str,
    bronze_schema: str,
    gold_schema: str,
    start_date: str,
    end_date: str
) -> int:
    """
    Backfill a single 1-week chunk of fact_usage.
    """
    from merge_helpers import (
        deduplicate_bronze, flatten_usage_metadata, flatten_identity_metadata,
        flatten_product_features, add_tag_governance_columns,
        enrich_usage_with_list_prices, merge_fact_table
    )
    
    bronze_table = f"{catalog}.{bronze_schema}.usage"
    
    print(f"\n  Processing: {start_date} to {end_date}")
    
    # Read Bronze for this date range
    bronze_raw = spark.table(bronze_table).filter(
        f"usage_date >= '{start_date}' AND usage_date < '{end_date}'"
    )
    
    record_count = bronze_raw.count()
    print(f"    Records in range: {record_count:,}")
    
    if record_count == 0:
        print(f"    ✓ No records in this range")
        return 0
    
    # Deduplicate
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["record_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Flatten and enrich
    print("    Flattening nested structs...")
    bronze_df = flatten_usage_metadata(bronze_df)
    bronze_df = flatten_identity_metadata(bronze_df, prefix="identity_metadata")
    bronze_df = flatten_product_features(bronze_df)
    
    print("    Enriching with list prices...")
    bronze_df = enrich_usage_with_list_prices(spark, bronze_df)
    bronze_df = add_tag_governance_columns(bronze_df, tag_column="custom_tags")
    
    # Select columns matching Gold schema (synced with merge_billing.py)
    updates_df = bronze_df.select(
        # Core identifiers
        "account_id", "workspace_id", "record_id", "sku_name", "cloud",
        "usage_start_time", "usage_end_time", "usage_date", "custom_tags",
        "usage_unit", "usage_quantity",
        
        # All usage_metadata fields (flattened)
        "usage_metadata_cluster_id",
        "usage_metadata_job_id",
        "usage_metadata_warehouse_id",
        "usage_metadata_instance_pool_id",
        "usage_metadata_node_type",
        "usage_metadata_job_run_id",
        "usage_metadata_notebook_id",
        "usage_metadata_dlt_pipeline_id",
        "usage_metadata_endpoint_name",
        "usage_metadata_endpoint_id",
        "usage_metadata_dlt_update_id",
        "usage_metadata_dlt_maintenance_id",
        "usage_metadata_run_name",
        "usage_metadata_job_name",
        "usage_metadata_notebook_path",
        "usage_metadata_central_clean_room_id",
        "usage_metadata_source_region",
        "usage_metadata_destination_region",
        "usage_metadata_app_id",
        "usage_metadata_app_name",
        "usage_metadata_metastore_id",
        "usage_metadata_private_endpoint_name",
        "usage_metadata_storage_api_type",
        "usage_metadata_budget_policy_id",
        "usage_metadata_ai_runtime_pool_id",
        "usage_metadata_ai_runtime_workload_id",
        "usage_metadata_uc_table_catalog",
        "usage_metadata_uc_table_schema",
        "usage_metadata_uc_table_name",
        "usage_metadata_database_instance_id",
        "usage_metadata_sharing_materialization_id",
        "usage_metadata_schema_id",
        "usage_metadata_usage_policy_id",
        "usage_metadata_base_environment_id",
        "usage_metadata_agent_bricks_id",
        "usage_metadata_index_id",
        "usage_metadata_catalog_id",
        
        # Identity metadata
        "identity_metadata_run_as", "identity_metadata_created_by", "identity_metadata_owned_by",
        
        # Other fields
        "record_type", "ingestion_date", "billing_origin_product", "usage_type",
        
        # All product_features fields (flattened)
        "product_features_jobs_tier",
        "product_features_sql_tier",
        "product_features_dlt_tier",
        "product_features_is_serverless",
        "product_features_is_photon",
        "product_features_serving_type",
        "product_features_networking",
        "product_features_ai_runtime",
        "product_features_model_serving",
        "product_features_ai_gateway",
        "product_features_performance_target",
        "product_features_serverless_gpu",
        "product_features_agent_bricks",
        "product_features_ai_functions",
        "product_features_apps",
        "product_features_lakeflow_connect",
        
        # Enriched fields
        "list_price", "list_cost", "is_tagged", "tag_count"
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_usage",
        primary_keys=["record_id"],
        validate_schema=False
    )
    
    print(f"    ✓ Merged {merged_count:,} records")
    return merged_count

# COMMAND ----------

def backfill_fact_query_history_chunk(
    spark: SparkSession,
    catalog: str,
    bronze_schema: str,
    gold_schema: str,
    start_date: str,
    end_date: str
) -> int:
    """
    Backfill a single 1-week chunk of fact_query_history.
    
    Bronze columns (system.query.history):
      - account_id, workspace_id, statement_id, executed_by, session_id
      - execution_status, executed_by_user_id, statement_text, statement_type
      - error_message, client_application, client_driver
      - total_duration_ms, waiting_for_compute_duration_ms, waiting_at_capacity_duration_ms
      - execution_duration_ms, compilation_duration_ms, total_task_duration_ms
      - result_fetch_duration_ms, start_time, end_time, update_time
      - read_partitions, pruned_files, read_files, read_rows, produced_rows
      - read_bytes, read_io_cache_percent, from_result_cache
      - spilled_local_bytes, written_bytes, shuffle_read_bytes
      - executed_as_user_id, executed_as, written_rows, written_files
      - cache_origin_statement_id, compute (struct), query_source (struct)
      - query_parameters (struct), query_tags (map)
    """
    from merge_helpers import deduplicate_bronze, merge_fact_table
    
    bronze_table = f"{catalog}.{bronze_schema}.query_history"
    
    print(f"\n  Processing: {start_date} to {end_date}")
    
    # Read Bronze for this date range (use end_time for filtering)
    bronze_raw = spark.table(bronze_table).filter(
        f"DATE(end_time) >= '{start_date}' AND DATE(end_time) < '{end_date}'"
    )
    
    record_count = bronze_raw.count()
    print(f"    Records in range: {record_count:,}")
    
    if record_count == 0:
        print(f"    ✓ No records in this range")
        return 0
    
    # Deduplicate
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["statement_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Prepare updates - flatten structs and match Gold schema
    updates_df = (
        bronze_df
        # Flatten compute struct
        .withColumn("compute_type", col("compute").getField("type"))
        .withColumn("compute_cluster_id", col("compute").getField("cluster_id"))
        .withColumn("compute_warehouse_id", col("compute").getField("warehouse_id"))
        # Flatten query_source struct (JSON for complex nested fields)
        .withColumn("query_source_job_info",
                    when(col("query_source").getField("job_info").isNotNull(), 
                         to_json(col("query_source").getField("job_info")))
                    .otherwise(lit(None)))
        .withColumn("query_source_legacy_dashboard_id", col("query_source").getField("legacy_dashboard_id"))
        .withColumn("query_source_dashboard_id", col("query_source").getField("dashboard_id"))
        .withColumn("query_source_alert_id", col("query_source").getField("alert_id"))
        .withColumn("query_source_notebook_id", col("query_source").getField("notebook_id"))
        .withColumn("query_source_sql_query_id", col("query_source").getField("sql_query_id"))
        .withColumn("query_source_genie_space_id", col("query_source").getField("genie_space_id"))
        .withColumn("query_source_pipeline_info",
                    when(col("query_source").getField("pipeline_info").isNotNull(),
                         to_json(col("query_source").getField("pipeline_info")))
                    .otherwise(lit(None)))
        # Flatten query_parameters struct
        .withColumn("query_parameters_named_parameters",
                    when(col("query_parameters").getField("named_parameters").isNotNull(),
                         to_json(col("query_parameters").getField("named_parameters")))
                    .otherwise(lit(None)))
        .withColumn("query_parameters_pos_parameters",
                    when(col("query_parameters").getField("pos_parameters").isNotNull(),
                         to_json(col("query_parameters").getField("pos_parameters")))
                    .otherwise(lit(None)))
        .withColumn("query_parameters_truncated", col("query_parameters").getField("truncated"))
        # Cast read_io_cache_percent to STRING (Bronze has it as TINYINT)
        .withColumn("read_io_cache_percent", col("read_io_cache_percent").cast("string"))
        # Select columns matching Gold schema
        .select(
            # Core identifiers
            "account_id", "workspace_id", "statement_id",
            # User info (correct Bronze column names)
            "executed_by",           # Bronze: executed_by (not executed_as_user_name)
            "session_id",
            "execution_status",
            "executed_by_user_id",
            "statement_text",        # Bronze: statement_text (not query_text)
            "statement_type",
            "error_message",
            "client_application",
            "client_driver",
            # Duration metrics (correct Bronze column names)
            "total_duration_ms",     # Bronze: total_duration_ms (not total_time_ms)
            "waiting_for_compute_duration_ms",
            "waiting_at_capacity_duration_ms",
            "execution_duration_ms",
            "compilation_duration_ms",
            "total_task_duration_ms", # Bronze: total_task_duration_ms (not total_cpu_time_ms)
            "result_fetch_duration_ms",
            # Timestamps (correct Bronze column names)
            "start_time",            # Bronze: start_time (not query_start_time)
            "end_time",              # Bronze: end_time (not execution_end_time)
            "update_time",
            # IO metrics
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
            # Additional user info
            "executed_as_user_id",
            "executed_as",
            # Write metrics
            "written_rows",
            "written_files",
            "cache_origin_statement_id",
            # Flattened compute struct
            "compute_type",
            "compute_cluster_id",
            "compute_warehouse_id",
            # Flattened query_source struct
            "query_source_job_info",
            "query_source_legacy_dashboard_id",
            "query_source_dashboard_id",
            "query_source_alert_id",
            "query_source_notebook_id",
            "query_source_sql_query_id",
            "query_source_genie_space_id",
            "query_source_pipeline_info",
            # Flattened query_parameters struct
            "query_parameters_named_parameters",
            "query_parameters_pos_parameters",
            "query_parameters_truncated",
            # Native query_tags map (keep as-is for Gold)
            "query_tags"
        )
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_query_history",
        primary_keys=["statement_id"],
        validate_schema=False
    )
    
    print(f"    ✓ Merged {merged_count:,} records")
    return merged_count

# COMMAND ----------

def generate_weekly_chunks(end_date, months_back: int):
    """
    Generate list of (start_date, end_date) tuples for 1-week processing.
    Goes backwards from end_date.
    
    Args:
        end_date: End date to start from (typically today)
        months_back: Number of months to backfill (will be split into 1-week chunks)
    
    Returns:
        List of (start_date, end_date) tuples, each representing ~1 week (7 days)
    
    Note: Reduced from 2-week to 1-week chunks due to timeout issues with
    large tables (fact_audit_logs has 300M-763M records per 2-week period).
    """
    chunks = []
    
    # Calculate total days to backfill (months * ~30 days)
    total_days = months_back * 30
    current_end = end_date
    
    # Generate 1-week (7 day) chunks to avoid timeouts
    while total_days > 0:
        # Create 1-week chunk (or remaining days if less than 7)
        chunk_size = min(7, total_days)
        current_start = current_end - timedelta(days=chunk_size)
        
        chunks.append((
            current_start.strftime("%Y-%m-%d"),
            current_end.strftime("%Y-%m-%d")
        ))
        
        # Move to next chunk
        current_end = current_start
        total_days -= chunk_size
    
    return chunks

# COMMAND ----------

def main():
    """
    Main entry point for historical backfill.
    
    RESUMABLE: Queries the Gold table itself to find what's already been processed.
    If job times out, just rerun it - it will automatically skip already-processed date ranges.
    """
    
    catalog, bronze_schema, gold_schema, table_name, months_to_backfill = get_parameters()
    
    spark = SparkSession.builder.appName(f"Gold Backfill - {table_name}").getOrCreate()
    
    print("\n" + "=" * 80)
    print(f"HISTORICAL BACKFILL: {table_name} (RESUMABLE)")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Bronze Schema: {bronze_schema}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Months to backfill: {months_to_backfill}")
    print("=" * 80)
    
    # Table-specific configuration
    table_config = {
        "fact_audit_logs": {
            "date_column": "event_date",
            "backfill_func": backfill_fact_audit_logs_chunk
        },
        "fact_usage": {
            "date_column": "usage_date",
            "backfill_func": backfill_fact_usage_chunk
        },
        "fact_query_history": {
            "date_column": "DATE(end_time)",  # Gold uses end_time
            "backfill_func": backfill_fact_query_history_chunk
        }
    }
    
    if table_name not in table_config:
        raise ValueError(f"Unknown table: {table_name}. Supported: {list(table_config.keys())}")
    
    config = table_config[table_name]
    gold_table = f"{catalog}.{gold_schema}.{table_name}"
    
    # === QUERY GOLD TABLE TO FIND WHAT'S ALREADY PROCESSED ===
    print("\n📍 Checking Gold table for existing data (auto-resume)...")
    gold_min_date, gold_max_date, record_count = get_gold_date_range(spark, gold_table, config["date_column"])
    
    print(f"\nCurrent Gold table status:")
    print(f"  Records: {record_count:,}")
    print(f"  Min date: {gold_min_date}")
    print(f"  Max date: {gold_max_date}")
    
    # Calculate backfill date range
    today = datetime.now().date()
    backfill_end = today
    backfill_start = today - timedelta(days=months_to_backfill * 30)
    
    print(f"\n  → Requested backfill: {backfill_start} to {backfill_end} ({months_to_backfill} months)")
    
    # Generate 1-week chunks going backwards FROM TODAY
    all_chunks = generate_weekly_chunks(backfill_end, months_to_backfill)
    
    # === FILTER CHUNKS BASED ON WHAT'S ALREADY IN GOLD ===
    if gold_min_date and gold_max_date:
        # Gold has data - skip chunks that are already covered
        # A chunk is "done" if its date range falls within Gold's date range
        remaining_chunks = []
        skipped_chunks = []
        
        for start, end in all_chunks:
            chunk_start_date = datetime.strptime(start, "%Y-%m-%d").date()
            chunk_end_date = datetime.strptime(end, "%Y-%m-%d").date()
            
            # Convert gold dates to date objects for comparison
            gold_min = gold_min_date.date() if hasattr(gold_min_date, 'date') else gold_min_date
            gold_max = gold_max_date.date() if hasattr(gold_max_date, 'date') else gold_max_date
            
            # Skip chunks that are FULLY within Gold's existing date range
            # (Both start AND end are within gold_min to gold_max)
            if chunk_start_date >= gold_min and chunk_end_date <= gold_max:
                skipped_chunks.append((start, end))
            else:
                remaining_chunks.append((start, end))
        
        if skipped_chunks:
            print(f"\n📍 Auto-resume: Skipping {len(skipped_chunks)} chunks already in Gold table")
            print(f"   (Gold has data from {gold_min} to {gold_max})")
        
        chunks = remaining_chunks
    else:
        # Gold is empty - process all chunks
        print(f"\n📍 Gold table is empty - processing all {len(all_chunks)} chunks")
        chunks = all_chunks
    
    if not chunks:
        print(f"\n✓ All chunks already processed! Gold table has data for entire requested period.")
        print(f"  Gold: {gold_min_date} to {gold_max_date}")
        print(f"  Requested: {backfill_start} to {backfill_end}")
        return
    
    print(f"\nProcessing {len(chunks)} remaining 1-week chunks:")
    for start, end in chunks[:10]:  # Show first 10
        print(f"  • {start} to {end}")
    if len(chunks) > 10:
        print(f"  ... and {len(chunks) - 10} more")
    
    # Process each chunk
    total_merged = 0
    chunks_completed = 0
    
    try:
        for i, (start_date, end_date) in enumerate(chunks):
            print(f"\n[{i+1}/{len(chunks)}] Processing chunk...")
            merged = config["backfill_func"](
                spark, catalog, bronze_schema, gold_schema, start_date, end_date
            )
            total_merged += merged
            chunks_completed += 1
            print(f"    ✓ Progress: {chunks_completed}/{len(chunks)} chunks done")
            
    except Exception as e:
        print(f"\n❌ Error during backfill: {str(e)}")
        print(f"\n💾 Progress saved in Gold table! Completed {chunks_completed} of {len(chunks)} chunks")
        print(f"   Rerun the job to automatically resume from where it left off.")
        raise
    
    print("\n" + "=" * 80)
    print(f"✓ BACKFILL COMPLETED")
    print(f"  Total records merged: {total_merged:,}")
    print(f"  Chunks processed: {chunks_completed}")
    print("=" * 80)

# COMMAND ----------

if __name__ == "__main__":
    main()

