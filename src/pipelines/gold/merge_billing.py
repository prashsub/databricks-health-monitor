# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Billing Domain
# MAGIC
# MAGIC Merges billing dimension and fact tables from Bronze to Gold.
# MAGIC
# MAGIC **Tables:**
# MAGIC - dim_sku (derived from billing.usage)
# MAGIC - fact_usage (from billing.usage with price enrichment)
# MAGIC - fact_list_prices (from billing.list_prices)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, when, lit, size, coalesce,
    to_date, unix_timestamp, to_json
)
from merge_helpers import (
    deduplicate_bronze,
    merge_dimension_table,
    merge_fact_table,
    flatten_struct_fields,
    add_tag_governance_columns,
    enrich_usage_with_list_prices,
    flatten_usage_metadata,
    flatten_identity_metadata,
    flatten_product_features,
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

def merge_dim_sku(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_sku from Bronze to Gold (SCD Type 1).
    
    Bronze Source: DERIVED from billing.usage (DISTINCT sku_name values)
    Gold Table: dim_sku
    Primary Key: sku_name
    Grain: One row per unique SKU
    
    Column Mapping (Bronze → Gold):
    - sku_name → sku_name (direct copy)
    - cloud → cloud (direct copy)
    - usage_unit → usage_unit (direct copy)
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_sku")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.usage"
    
    # Extract distinct SKUs from usage table
    bronze_raw = spark.table(bronze_table)
    
    # Get distinct SKUs - MUST deduplicate by sku_name (PK)
    # Same SKU may appear with different cloud/usage_unit values
    sku_df = (
        bronze_raw
        .select("sku_name", "cloud", "usage_unit")
        .filter(col("sku_name").isNotNull())  # Filter out NULLs
        .dropDuplicates(["sku_name"])  # Deduplicate on PK only
    )
    
    original_count = sku_df.count()
    print(f"  Found {original_count} distinct SKUs (deduplicated by sku_name)")
    
    # NOTE: Gold table DDLs don't include audit timestamps
    updates_df = sku_df
    
    # MERGE to Gold (SCD Type 1)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_sku",
        business_keys=["sku_name"],
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_sku", original_count, original_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_usage(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_usage from Bronze to Gold (TRUE INCREMENTAL).
    
    Bronze Source: system.billing.usage → Bronze: usage
    Gold Table: fact_usage
    Primary Key: record_id (transaction grain)
    Grain: One row per usage record
    
    ⚠️ INCREMENTAL PATTERN:
    - First run: Gold is empty → process ALL historical data (100M+ records, will be slow)
    - Subsequent runs: Only process records NEWER than Gold's max(usage_date) → fast!
    
    Transformations:
    1. Flatten usage_metadata struct (35 fields)
    2. Flatten identity_metadata struct (3 fields)
    3. Flatten product_features struct (15 fields)
    4. Enrich with list_price from system.billing.list_prices
    5. Derive list_cost (usage_quantity * list_price)
    6. Derive is_tagged and tag_count
    7. Preserve custom_tags as MAP type (already MAP in source)
    
    Column Mapping (Bronze → Gold):
    - Direct copy: All top-level columns
    - Flattened: usage_metadata.* → usage_metadata_*
    - Flattened: identity_metadata.* → identity_metadata_*
    - Flattened: product_features.* → product_features_*
    - Derived: list_price (from join), list_cost, is_tagged, tag_count
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_usage")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.usage"
    gold_table = f"{catalog}.{gold_schema}.fact_usage"
    
    # Get incremental filter from Gold table's high-water mark
    # NOTE: 90-day limit on first run for this 109M+ record table
    incremental_filter = get_incremental_filter(
        spark, gold_table, "usage_date",
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
    
    # Deduplicate on record_id (business key = PK)
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["record_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Flatten nested structs
    print("  Flattening nested structs...")
    bronze_df = flatten_usage_metadata(bronze_df)
    bronze_df = flatten_identity_metadata(bronze_df, prefix="identity_metadata")
    bronze_df = flatten_product_features(bronze_df)
    
    # Enrich with list prices
    print("  Enriching with list prices...")
    bronze_df = enrich_usage_with_list_prices(spark, bronze_df)
    
    # Add tag governance columns
    bronze_df = add_tag_governance_columns(bronze_df, tag_column="custom_tags")
    
    # Prepare updates
    updates_df = (
        bronze_df
        .select(
            # Core columns
            "account_id",
            "workspace_id",
            "record_id",
            "sku_name",
            "cloud",
            "usage_start_time",
            "usage_end_time",
            "usage_date",
            "usage_unit",
            col("usage_quantity").cast("DECIMAL(38,10)").alias("usage_quantity"),
            "record_type",
            "ingestion_date",
            "billing_origin_product",
            "usage_type",
            
            # MAP type (direct copy)
            "custom_tags",
            
            # Flattened usage_metadata (35 fields)
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
            
            # Flattened identity_metadata (3 fields)
            "identity_metadata_run_as",
            "identity_metadata_created_by",
            "identity_metadata_owned_by",
            
            # Flattened product_features (15 fields)
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
            
            # Enriched from list_prices (cast to proper precision)
            col("list_price").cast("DECIMAL(18,6)").alias("list_price"),
            col("list_cost").cast("DECIMAL(18,6)").alias("list_cost"),
            
            # Derived tag governance
            "is_tagged",
            "tag_count"
        )
        # Add audit timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
    )
    
    # MERGE to Gold (transaction grain - no aggregation)
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_usage",
        primary_keys=["record_id"],
        validate_schema=False  # Disabled for performance (100M+ records)
    )
    
    print_merge_summary("fact_usage", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_list_prices(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_list_prices from Bronze to Gold.
    
    Bronze Source: system.billing.list_prices → Bronze: list_prices
    Gold Table: fact_list_prices
    Primary Key: sku_name, price_start_time (composite)
    Grain: One row per SKU price change event
    
    Column Mapping (Bronze → Gold):
    - All top-level columns: Direct copy
    - Flattened: pricing.default → pricing_default
    - Flattened: pricing.promotional → pricing_promotional
    - Flattened: pricing.effective_list → pricing_effective_list
    
    Note: Bronze column names differ:
    - effective_start_time → price_start_time
    - effective_end_time → price_end_time
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_list_prices")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.list_prices"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite key (sku_name, price_start_time)
    # Note: Bronze uses price_start_time (not effective_start_time)
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["sku_name", "price_start_time"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Handle pricing struct - complex nested structure:
    # - pricing.default: DECIMAL(38,18) → cast to DECIMAL(38,6)
    # - pricing.promotional: STRUCT → serialize to JSON STRING
    # - pricing.effective_list: STRUCT → serialize to JSON STRING
    
    # Prepare updates - Bronze already has price_start_time and price_end_time
    updates_df = (
        bronze_df
        # pricing.default needs to be cast to DECIMAL(38,10) per actual Gold DDL
        .withColumn("pricing_default", 
                    col("pricing.default").cast("DECIMAL(38,10)"))
        # pricing.promotional is a STRUCT - serialize to JSON string
        .withColumn("pricing_promotional",
                    when(col("pricing.promotional").isNotNull(), 
                         to_json(col("pricing.promotional")))
                    .otherwise(lit(None)))
        # pricing.effective_list is a STRUCT - serialize to JSON string
        .withColumn("pricing_effective_list",
                    when(col("pricing.effective_list").isNotNull(), 
                         to_json(col("pricing.effective_list")))
                    .otherwise(lit(None)))
        .select(
            "account_id",
            "price_start_time",   # Direct copy (Bronze column name)
            "price_end_time",     # Direct copy (Bronze column name)
            "sku_name",
            "cloud",
            "currency_code",
            "usage_unit",
            "pricing_default",
            "pricing_promotional",
            "pricing_effective_list"
        )
        # NOTE: Gold table DDLs don't include audit timestamps
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_list_prices",
        primary_keys=["sku_name", "price_start_time"],
        validate_schema=True
    )
    
    print_merge_summary("fact_list_prices", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Billing domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - BILLING DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Billing").getOrCreate()
    
    try:
        # Merge in dependency order
        print("\nStep 1: Merging dim_sku (no dependencies)...")
        merge_dim_sku(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 2: Merging fact_list_prices...")
        merge_fact_list_prices(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 3: Merging fact_usage (depends on dim_sku)...")
        merge_fact_usage(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Billing domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Billing domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

