# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Security Domain
# MAGIC
# MAGIC Merges Security audit tables from Bronze to Gold.
# MAGIC
# MAGIC **Tables:**
# MAGIC - fact_audit_logs (from access.audit)
# MAGIC
# MAGIC **Chunking Strategy:**
# MAGIC - Processes data in weekly chunks to handle billions of records
# MAGIC - First run: Last 90 days in weekly chunks
# MAGIC - Subsequent runs: New data since last run in weekly chunks

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, lit, to_json, lower
)
from datetime import datetime, timedelta
from merge_helpers import (
    deduplicate_bronze,
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
    
    # Optional: days_lookback for initial run (default: 7 days for fast startup)
    # Use gold_backfill_job for historical data beyond this window
    try:
        days_lookback = int(dbutils.widgets.get("days_lookback"))
    except Exception:
        days_lookback = 7  # Default to 7 days for fast pipeline startup
    
    print(f"Catalog: {catalog}")
    print(f"Bronze Schema: {bronze_schema}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Days Lookback (initial run): {days_lookback}")
    
    return catalog, bronze_schema, gold_schema, days_lookback

# COMMAND ----------

def generate_weekly_chunks(start_date, end_date):
    """Generate list of (start_date, end_date) tuples for weekly processing."""
    chunks = []
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=7), end_date)
        chunks.append((current.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
        current = chunk_end
    return chunks


def get_gold_max_date(spark: SparkSession, gold_table: str, date_column: str):
    """Get the maximum date from Gold table, or None if empty."""
    try:
        result = spark.sql(f"SELECT MAX({date_column}) as max_date FROM {gold_table}").collect()[0]
        return result["max_date"]
    except Exception as e:
        print(f"  ⚠️ Could not get Gold max date: {str(e)[:100]}")
        return None


def merge_audit_logs_chunk(
    spark: SparkSession,
    catalog: str,
    bronze_schema: str,
    gold_schema: str,
    start_date: str,
    end_date: str
) -> int:
    """Merge a single chunk of audit logs."""
    bronze_table = f"{catalog}.{bronze_schema}.audit"
    
    # Read Bronze for this date range
    bronze_raw = spark.table(bronze_table).filter(
        f"event_date >= '{start_date}' AND event_date < '{end_date}'"
    )
    
    record_count = bronze_raw.count()
    print(f"    Records in range: {record_count:,}")
    
    if record_count == 0:
        return 0
    
    # Deduplicate on event_id
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
    
    # Add derived columns and select
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
        validate_schema=False
    )
    
    return merged_count


def merge_fact_audit_logs(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str, days_lookback: int = 7):
    """
    Merge fact_audit_logs from Bronze to Gold using WEEKLY CHUNKS.
    
    Chunking Strategy:
    - First run: Process last `days_lookback` days (default: 7 days for fast startup)
    - Subsequent runs: Process new data since max(event_date) in weekly chunks
    - For historical data beyond days_lookback, use the gold_backfill_job
    
    This prevents memory issues with 7B+ record table.
    
    Args:
        days_lookback: Number of days to look back on first run (default: 7)
                      Use gold_backfill_job for historical data beyond this window
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_audit_logs (CHUNKED)")
    print("=" * 80)
    
    gold_table = f"{catalog}.{gold_schema}.fact_audit_logs"
    
    # Determine date range
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)  # Include today's data
    max_gold_date = get_gold_max_date(spark, gold_table, "event_date")
    
    if max_gold_date:
        # Incremental: from day after Gold max to tomorrow (to include today)
        start_date = max_gold_date + timedelta(days=1)
        print(f"  ℹ️ Incremental mode: Processing from {start_date} to {today} (inclusive)")
    else:
        # First run: last N days (configurable, default 7 for fast startup)
        start_date = today - timedelta(days=days_lookback)
        print(f"  ℹ️ First run: Processing last {days_lookback} days ({start_date} to {today})")
        print(f"  💡 Tip: Use gold_backfill_job for historical data beyond {days_lookback} days")
    
    if start_date > today:  # Changed from >= to > (process today's data)
        print("  ✓ No new records to process - Gold is up to date!")
        return 0
    
    # Generate weekly chunks (up to tomorrow to include today's data)
    chunks = generate_weekly_chunks(start_date, tomorrow)
    print(f"  📦 Processing {len(chunks)} weekly chunks")
    
    total_merged = 0
    for i, (chunk_start, chunk_end) in enumerate(chunks):
        print(f"\n  [{i+1}/{len(chunks)}] Chunk: {chunk_start} to {chunk_end}")
        merged = merge_audit_logs_chunk(spark, catalog, bronze_schema, gold_schema, chunk_start, chunk_end)
        total_merged += merged
        print(f"    ✓ Merged {merged:,} records (running total: {total_merged:,})")
    
    print(f"\n  ✓ Total merged: {total_merged:,} records across {len(chunks)} chunks")
    return total_merged

# COMMAND ----------

# COMMAND ----------
# Additional Security Tables
# COMMAND ----------

def merge_fact_assistant_events(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_assistant_events from Bronze to Gold.
    
    Bronze Source: system.access.assistant_events
    Gold Table: fact_assistant_events
    Primary Key: event_id
    Grain: One row per AI assistant interaction
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_assistant_events")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.assistant_events"
    gold_table = f"{catalog}.{gold_schema}.fact_assistant_events"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_assistant_events")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate on event_id
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["event_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Select columns matching Gold schema
    updates_df = bronze_df.select(
        "account_id", "workspace_id", "event_id", "event_time", "event_date",
        "user_agent", "initiated_by"
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_assistant_events",
        primary_keys=["event_id"],
        validate_schema=False
    )
    
    print_merge_summary("fact_assistant_events", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def merge_fact_clean_room_events(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_clean_room_events from Bronze to Gold.
    
    Bronze Source: system.access.clean_room_events
    Gold Table: fact_clean_room_events
    Primary Key: event_id
    Grain: One row per clean room event
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_clean_room_events")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.clean_room_events"
    gold_table = f"{catalog}.{gold_schema}.fact_clean_room_events"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_clean_room_events")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate on event_id
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["event_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Flatten nested fields - serialize complex nested structures to JSON
    updates_df = (
        bronze_df
        # Flatten clean_room_created_metadata
        .withColumn("clean_room_created_metadata_collaborators",
                    when(col("clean_room_created_metadata.collaborators").isNotNull(),
                         to_json(col("clean_room_created_metadata.collaborators")))
                    .otherwise(lit(None)))
        .withColumn("clean_room_created_metadata_egress_network_policy",
                    when(col("clean_room_created_metadata.egress_network_policy").isNotNull(),
                         to_json(col("clean_room_created_metadata.egress_network_policy")))
                    .otherwise(lit(None)))
        .withColumn("clean_room_created_metadata_compliance_profile",
                    col("clean_room_created_metadata.compliance_profile"))
        # Flatten clean_room_deleted_metadata
        .withColumn("clean_room_deleted_metadata_central_clean_room_id",
                    col("clean_room_deleted_metadata.central_clean_room_id"))
        # Flatten run_notebook_started_metadata
        .withColumn("run_notebook_started_metadata_notebook_name",
                    col("run_notebook_started_metadata.notebook_name"))
        .withColumn("run_notebook_started_metadata_notebook_checksum",
                    col("run_notebook_started_metadata.notebook_checksum"))
        .withColumn("run_notebook_started_metadata_run_id",
                    col("run_notebook_started_metadata.run_id"))
        .withColumn("run_notebook_started_metadata_notebook_etag",
                    col("run_notebook_started_metadata.notebook_etag"))
        .withColumn("run_notebook_started_metadata_notebook_update_time",
                    col("run_notebook_started_metadata.notebook_update_time"))
        # Flatten run_notebook_completed_metadata
        .withColumn("run_notebook_completed_metadata_notebook_name",
                    col("run_notebook_completed_metadata.notebook_name"))
        .withColumn("run_notebook_completed_metadata_run_id",
                    col("run_notebook_completed_metadata.run_id"))
        .withColumn("run_notebook_completed_metadata_state",
                    col("run_notebook_completed_metadata.state"))
        .withColumn("run_notebook_completed_metadata_duration_in_seconds",
                    col("run_notebook_completed_metadata.duration_in_seconds"))
        .withColumn("run_notebook_completed_metadata_output_schema",
                    when(col("run_notebook_completed_metadata.output_schema").isNotNull(),
                         to_json(col("run_notebook_completed_metadata.output_schema")))
                    .otherwise(lit(None)))
        # Flatten clean_room_assets_updated_metadata
        .withColumn("clean_room_assets_updated_metadata_added_assets",
                    when(col("clean_room_assets_updated_metadata.added_assets").isNotNull(),
                         to_json(col("clean_room_assets_updated_metadata.added_assets")))
                    .otherwise(lit(None)))
        .withColumn("clean_room_assets_updated_metadata_updated_assets",
                    when(col("clean_room_assets_updated_metadata.updated_assets").isNotNull(),
                         to_json(col("clean_room_assets_updated_metadata.updated_assets")))
                    .otherwise(lit(None)))
        .withColumn("clean_room_assets_updated_metadata_removed_assets",
                    when(col("clean_room_assets_updated_metadata.removed_assets").isNotNull(),
                         to_json(col("clean_room_assets_updated_metadata.removed_assets")))
                    .otherwise(lit(None)))
        # Flatten output_schema_deleted_metadata
        .withColumn("output_schema_deleted_metadata_name",
                    col("output_schema_deleted_metadata.name"))
        .withColumn("output_schema_deleted_metadata_owner_global_metastore_id",
                    col("output_schema_deleted_metadata.owner_global_metastore_id"))
        .withColumn("output_schema_deleted_metadata_action",
                    col("output_schema_deleted_metadata.action"))
        .withColumn("output_schema_deleted_metadata_expire_time",
                    col("output_schema_deleted_metadata.expire_time"))
        # Flatten asset_review_created_metadata
        .withColumn("asset_review_created_metadata_asset_name",
                    col("asset_review_created_metadata.asset_name"))
        .withColumn("asset_review_created_metadata_data_object_type",
                    col("asset_review_created_metadata.data_object_type"))
        .withColumn("asset_review_created_metadata_review_state",
                    col("asset_review_created_metadata.review_state"))
        .withColumn("asset_review_created_metadata_review_sub_reason",
                    col("asset_review_created_metadata.review_sub_reason"))
        .withColumn("asset_review_created_metadata_auto_approval_rule_id",
                    col("asset_review_created_metadata.auto_approval_rule_id"))
        .withColumn("asset_review_created_metadata_notebook_metadata",
                    when(col("asset_review_created_metadata.notebook_metadata").isNotNull(),
                         to_json(col("asset_review_created_metadata.notebook_metadata")))
                    .otherwise(lit(None)))
        .select(
            "account_id", "metastore_id", "event_id", "clean_room_name",
            "central_clean_room_id", "initiator_global_metastore_id", "event_type",
            "event_time", "initiator_collaborator_alias",
            "clean_room_created_metadata_collaborators",
            "clean_room_created_metadata_egress_network_policy",
            "clean_room_created_metadata_compliance_profile",
            "clean_room_deleted_metadata_central_clean_room_id",
            "run_notebook_started_metadata_notebook_name",
            "run_notebook_started_metadata_notebook_checksum",
            "run_notebook_started_metadata_run_id",
            "run_notebook_started_metadata_notebook_etag",
            "run_notebook_started_metadata_notebook_update_time",
            "run_notebook_completed_metadata_notebook_name",
            "run_notebook_completed_metadata_run_id",
            "run_notebook_completed_metadata_state",
            "run_notebook_completed_metadata_duration_in_seconds",
            "run_notebook_completed_metadata_output_schema",
            "clean_room_assets_updated_metadata_added_assets",
            "clean_room_assets_updated_metadata_updated_assets",
            "clean_room_assets_updated_metadata_removed_assets",
            "output_schema_deleted_metadata_name",
            "output_schema_deleted_metadata_owner_global_metastore_id",
            "output_schema_deleted_metadata_action",
            "output_schema_deleted_metadata_expire_time",
            "asset_review_created_metadata_asset_name",
            "asset_review_created_metadata_data_object_type",
            "asset_review_created_metadata_review_state",
            "asset_review_created_metadata_review_sub_reason",
            "asset_review_created_metadata_auto_approval_rule_id",
            "asset_review_created_metadata_notebook_metadata"
        )
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_clean_room_events",
        primary_keys=["event_id"],
        validate_schema=False
    )
    
    print_merge_summary("fact_clean_room_events", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def merge_fact_outbound_network(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_outbound_network from Bronze to Gold.
    
    Bronze Source: system.access.outbound_network
    Gold Table: fact_outbound_network
    Primary Key: event_id
    Grain: One row per blocked outbound network event
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_outbound_network")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.outbound_network"
    gold_table = f"{catalog}.{gold_schema}.fact_outbound_network"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_outbound_network")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate on event_id
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["event_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Flatten nested fields
    updates_df = (
        bronze_df
        # Flatten dns_event
        .withColumn("dns_event_domain_name", col("dns_event.domain_name"))
        .withColumn("dns_event_rcode", col("dns_event.rcode"))
        # Flatten storage_event
        .withColumn("storage_event_hostname", col("storage_event.hostname"))
        .withColumn("storage_event_path", col("storage_event.path"))
        .withColumn("storage_event_rejection_reason", col("storage_event.rejection_reason"))
        .select(
            "account_id", "workspace_id", "destination_type", "destination",
            "event_time", "access_type", "event_id", "network_source_type",
            "dns_event_domain_name", "dns_event_rcode",
            "storage_event_hostname", "storage_event_path", "storage_event_rejection_reason"
        )
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_outbound_network",
        primary_keys=["event_id"],
        validate_schema=False
    )
    
    print_merge_summary("fact_outbound_network", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Security domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - SECURITY DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema, days_lookback = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Security").getOrCreate()
    
    try:
        # Primary audit table (chunked due to size)
        # Uses days_lookback for initial run (default: 7 days)
        # For historical data, use the separate gold_backfill_job
        print("\nStep 1: Merging fact_audit_logs (chunked)...")
        merge_fact_audit_logs(spark, catalog, bronze_schema, gold_schema, days_lookback)
        
        # Additional security tables
        print("\nStep 2: Merging fact_assistant_events...")
        merge_fact_assistant_events(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 3: Merging fact_clean_room_events...")
        merge_fact_clean_room_events(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 4: Merging fact_outbound_network...")
        merge_fact_outbound_network(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Security domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Security domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

