# Databricks notebook source
# MAGIC %md
# MAGIC # Historical Backfill for Large Gold Tables
# MAGIC 
# MAGIC Processes historical data in monthly chunks to avoid memory issues.
# MAGIC Works alongside the incremental job - backfills data BEFORE the current Gold min date.
# MAGIC 
# MAGIC **Tables supported:**
# MAGIC - fact_audit_logs (7B+ records)
# MAGIC - fact_usage (109M+ records)  
# MAGIC - fact_query_history (68M+ records)
# MAGIC 
# MAGIC **Strategy:**
# MAGIC - Get MIN date from Gold (earliest data we have)
# MAGIC - Process data in monthly chunks going backwards
# MAGIC - Uses MERGE to avoid duplicates if chunks overlap

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
    Backfill a single month chunk of fact_audit_logs.
    
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
    Backfill a single month chunk of fact_usage.
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
    Backfill a single month chunk of fact_query_history.
    """
    from merge_helpers import deduplicate_bronze, flatten_struct_fields, merge_fact_table
    
    bronze_table = f"{catalog}.{bronze_schema}.query_history"
    
    print(f"\n  Processing: {start_date} to {end_date}")
    
    # Read Bronze for this date range (use end_time for filtering - Bronze column name)
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
    
    # Prepare updates (simplified - match Gold schema)
    updates_df = (
        bronze_df
        .withColumn("query_tags_json",
                    when(col("query_tags").isNotNull(), to_json(col("query_tags")))
                    .otherwise(lit(None)))
        .withColumn("query_source_job_info",
                    when(col("query_source").getField("job_info").isNotNull(), 
                         to_json(col("query_source").getField("job_info")))
                    .otherwise(lit(None)))
        .withColumn("query_source_pipeline_info",
                    when(col("query_source").getField("pipeline_info").isNotNull(),
                         to_json(col("query_source").getField("pipeline_info")))
                    .otherwise(lit(None)))
        .withColumn("query_parameters_named_parameters",
                    when(col("query_parameters").getField("named_parameters").isNotNull(),
                         to_json(col("query_parameters").getField("named_parameters")))
                    .otherwise(lit(None)))
        .withColumn("query_parameters_pos_parameters",
                    when(col("query_parameters").getField("pos_parameters").isNotNull(),
                         to_json(col("query_parameters").getField("pos_parameters")))
                    .otherwise(lit(None)))
        .withColumn("read_io_cache_percent", col("read_io_cache_percent").cast("string"))
        .select(
            "account_id", "workspace_id", "statement_id", "executed_as_user_id",
            "executed_as_user_name", "execution_status", "query_text",
            "query_start_time", "execution_end_time", "compute_time",
            "total_cpu_time_ms", "total_time_ms", "read_bytes", "produced_rows",
            "read_io_cache_percent", "spilled_local_bytes", "written_bytes",
            "warehouse_id", "statement_type",
            "query_tags_json", "query_source_job_info", "query_source_pipeline_info",
            "query_parameters_named_parameters", "query_parameters_pos_parameters"
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

def generate_monthly_chunks(end_date, months_back: int):
    """
    Generate list of (start_date, end_date) tuples for monthly processing.
    Goes backwards from end_date.
    """
    chunks = []
    current_end = end_date
    
    for i in range(months_back):
        # Start of this month
        current_start = current_end.replace(day=1)
        chunks.append((
            current_start.strftime("%Y-%m-%d"),
            current_end.strftime("%Y-%m-%d")
        ))
        # Move to previous month
        current_end = current_start - timedelta(days=1)
    
    return chunks

# COMMAND ----------

def main():
    """Main entry point for historical backfill."""
    
    catalog, bronze_schema, gold_schema, table_name, months_to_backfill = get_parameters()
    
    spark = SparkSession.builder.appName(f"Gold Backfill - {table_name}").getOrCreate()
    
    print("\n" + "=" * 80)
    print(f"HISTORICAL BACKFILL: {table_name}")
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
            "date_column": "DATE(end_time)",  # Bronze column name is end_time
            "backfill_func": backfill_fact_query_history_chunk
        }
    }
    
    if table_name not in table_config:
        raise ValueError(f"Unknown table: {table_name}. Supported: {list(table_config.keys())}")
    
    config = table_config[table_name]
    gold_table = f"{catalog}.{gold_schema}.{table_name}"
    
    # Get current Gold date range (for informational purposes)
    min_date, max_date, record_count = get_gold_date_range(spark, gold_table, config["date_column"])
    
    print(f"\nCurrent Gold table status:")
    print(f"  Records: {record_count:,}")
    print(f"  Min date: {min_date}")
    print(f"  Max date: {max_date}")
    
    # CORRECT: Start from TODAY and go back X months
    # This ensures we backfill the last N months of data
    today = datetime.now().date()
    backfill_end = today
    
    print(f"\n  → Backfilling last {months_to_backfill} months (from {backfill_end} going back)")
    print(f"     Note: MERGE ensures no duplicates with existing data")
    
    # Generate monthly chunks going backwards FROM TODAY
    chunks = generate_monthly_chunks(backfill_end, months_to_backfill)
    
    print(f"\nProcessing {len(chunks)} monthly chunks:")
    for start, end in chunks:
        print(f"  • {start} to {end}")
    
    # Process each chunk
    total_merged = 0
    try:
        for i, (start_date, end_date) in enumerate(chunks):
            print(f"\n[{i+1}/{len(chunks)}] Processing chunk...")
            merged = config["backfill_func"](
                spark, catalog, bronze_schema, gold_schema, start_date, end_date
            )
            total_merged += merged
            
    except Exception as e:
        print(f"\n❌ Error during backfill: {str(e)}")
        raise
    
    print("\n" + "=" * 80)
    print(f"✓ BACKFILL COMPLETED")
    print(f"  Total records merged: {total_merged:,}")
    print(f"  Chunks processed: {len(chunks)}")
    print("=" * 80)

# COMMAND ----------

if __name__ == "__main__":
    main()

