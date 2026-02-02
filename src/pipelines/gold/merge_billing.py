# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Billing Domain
# MAGIC 
# MAGIC ## TRAINING MATERIAL: Production Data Pipeline Patterns
# MAGIC 
# MAGIC This notebook demonstrates production-grade Gold layer data transformation patterns.
# MAGIC 
# MAGIC ### Architecture Context
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────────────┐
# MAGIC │  BRONZE          SILVER               GOLD                              │
# MAGIC │  (Raw)           (Cleaned)            (Business)                        │
# MAGIC │  ↓               ↓                    ↓                                 │
# MAGIC │  Landing        DLT Pipeline         THIS NOTEBOOK                     │
# MAGIC │  Tables         (streaming)          (MERGE operations)                │
# MAGIC │                 - Deduplication      - Aggregation                     │
# MAGIC │                 - Validation         - Denormalization                 │
# MAGIC │                 - Type casting       - Business logic                  │
# MAGIC │                                      - SCD handling                    │
# MAGIC └─────────────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC 
# MAGIC ### Key Concepts Demonstrated
# MAGIC 1. **MERGE Pattern**: Idempotent upsert operations (vs INSERT/UPDATE)
# MAGIC 2. **Struct Flattening**: Converting nested structures to flat columns
# MAGIC 3. **Incremental Processing**: Only process new/changed data
# MAGIC 4. **Deduplication**: Handle duplicates before MERGE
# MAGIC 5. **Data Enrichment**: Join with lookup tables (list_prices)
# MAGIC 6. **Schema Validation**: Ensure source matches target schema
# MAGIC 
# MAGIC **Tables:**
# MAGIC - dim_sku (derived from billing.usage)
# MAGIC - fact_usage (from billing.usage with price enrichment)
# MAGIC - fact_list_prices (from billing.list_prices)

# COMMAND ----------

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization for Pipeline Notebooks
#
# CATEGORIES:
# 1. PySpark core (SparkSession)
# 2. PySpark functions (individual imports for clarity)
# 3. Local helpers (merge_helpers module)
#
# WHY EXPLICIT FUNCTION IMPORTS:
# - Makes it clear which functions are used
# - Avoids `from x import *` anti-pattern
# - Easier to debug and maintain

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, when, lit, size, coalesce,
    to_date, unix_timestamp, to_json
)

# Local merge helpers - shared across all domain merge notebooks
# WHY SHARED HELPERS:
# - Consistent patterns across domains
# - DRY principle (Don't Repeat Yourself)
# - Tested utility functions
from merge_helpers import (
    deduplicate_bronze,           # Remove duplicates by business key
    merge_dimension_table,        # SCD Type 1/2 MERGE for dimensions
    merge_fact_table,             # Standard MERGE for facts
    flatten_struct_fields,        # Generic struct flattening
    add_tag_governance_columns,   # Derive is_tagged, tag_count
    enrich_usage_with_list_prices, # Join with price lookup
    flatten_usage_metadata,       # Domain-specific: usage_metadata struct
    flatten_identity_metadata,    # Domain-specific: identity_metadata struct
    flatten_product_features,     # Domain-specific: product_features struct
    print_merge_summary,          # Standardized output formatting
    get_incremental_filter        # High-water mark logic
)

# COMMAND ----------

# =============================================================================
# PARAMETER RETRIEVAL
# =============================================================================
# TRAINING MATERIAL: Job Parameter Pattern

def get_parameters():
    """
    Get job parameters from dbutils widgets.
    
    TRAINING MATERIAL: Widget-Based Parameter Passing
    ==================================================
    
    WHY WIDGETS (not argparse):
    - Databricks Asset Bundles use notebook_task
    - notebook_task passes parameters via widgets
    - argparse will FAIL in this execution context
    
    PARAMETER SOURCES:
    1. Job definition (base_parameters in YAML)
    2. Manual run (interactive input)
    3. Scheduled run (uses defaults)
    
    BEST PRACTICES:
    - Print parameter values (for job logs)
    - Return tuple (not dict) for clean unpacking
    - Use descriptive parameter names
    
    Returns:
        Tuple of (catalog, bronze_schema, gold_schema)
    """
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    # Print for job log visibility
    print(f"Catalog: {catalog}")
    print(f"Bronze Schema: {bronze_schema}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, bronze_schema, gold_schema

# COMMAND ----------

# =============================================================================
# DIMENSION TABLE MERGE: dim_sku
# =============================================================================
# TRAINING MATERIAL: Dimension Table Merge Pattern

def merge_dim_sku(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_sku from Bronze to Gold (SCD Type 1).
    
    TRAINING MATERIAL: Dimension Table Derivation
    ==============================================
    
    UNIQUE PATTERN: This dimension is DERIVED from a fact source.
    Most dimensions come from dedicated source tables.
    Here, we extract distinct SKU values from usage records.
    
    WHY DERIVE FROM USAGE:
    - No separate SKU master in system.billing
    - SKU data exists within usage records
    - Extract unique values to normalize
    
    SCD TYPE 1 EXPLAINED:
    ---------------------
    SCD Type 1 = Overwrite on match (no history)
    - When SKU attributes change, old values are lost
    - Simple, efficient for non-critical dimensions
    - Use when historical tracking isn't needed
    
    ALTERNATIVES:
    - SCD Type 2: Track history with effective dates
    - SCD Type 3: Keep current + previous value only
    - SCD Type 6: Hybrid of 1, 2, and 3
    
    DEDUPLICATION STRATEGY:
    -----------------------
    Same sku_name may appear with different cloud/usage_unit.
    We deduplicate on PRIMARY KEY (sku_name) only.
    This means we keep ONE arbitrary cloud/usage_unit per SKU.
    
    ALTERNATIVE: Keep most recent based on timestamp
    sku_df = (
        bronze_raw
        .withColumn("rn", row_number().over(
            Window.partitionBy("sku_name")
            .orderBy(desc("bronze_ingestion_timestamp"))
        ))
        .filter(col("rn") == 1)
        .drop("rn")
    )
    
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
    # WHY usage: No separate SKU dimension source exists
    bronze_raw = spark.table(bronze_table)
    
    # Get distinct SKUs - MUST deduplicate by sku_name (PK)
    # Same SKU may appear with different cloud/usage_unit values
    sku_df = (
        bronze_raw
        .select("sku_name", "cloud", "usage_unit")
        .filter(col("sku_name").isNotNull())  # Filter out NULLs (PK can't be NULL)
        .dropDuplicates(["sku_name"])  # Deduplicate on PK only
    )
    
    original_count = sku_df.count()
    print(f"  Found {original_count} distinct SKUs (deduplicated by sku_name)")
    
    # NOTE: Gold table DDLs don't include audit timestamps
    # If needed, add: .withColumn("record_updated_timestamp", current_timestamp())
    updates_df = sku_df
    
    # MERGE to Gold (SCD Type 1 = Overwrite on match)
    # WHY SCD Type 1: SKU attributes rarely change, history not critical
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_sku",
        business_keys=["sku_name"],  # Natural key, also serves as PK
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_sku", original_count, original_count, merged_count)
    
    return merged_count

# COMMAND ----------

# =============================================================================
# FACT TABLE MERGE: fact_usage
# =============================================================================
# TRAINING MATERIAL: Complex Fact Table Merge with Incremental Processing

def merge_fact_usage(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_usage from Bronze to Gold (TRUE INCREMENTAL).
    
    TRAINING MATERIAL: High-Volume Fact Table Processing
    =====================================================
    
    This is the most complex merge in the billing domain:
    - 100M+ records (requires incremental processing)
    - 3 nested structs (requires flattening)
    - Data enrichment (join with list_prices)
    - Derived columns (list_cost, is_tagged, tag_count)
    
    INCREMENTAL PROCESSING PATTERN:
    -------------------------------
    
    ┌─────────────────────────────────────────────────────────────────┐
    │  HIGH WATER MARK APPROACH                                       │
    │                                                                 │
    │  Gold Table: fact_usage                                         │
    │  ├── Max(usage_date) = 2024-01-15  ← High Water Mark           │
    │                                                                 │
    │  Bronze Table: usage                                            │
    │  ├── Records from 2024-01-01 to 2024-01-20                     │
    │                                                                 │
    │  Incremental Filter: usage_date > '2024-01-15'                 │
    │  Records to Process: 2024-01-16 to 2024-01-20 only            │
    └─────────────────────────────────────────────────────────────────┘
    
    WHY HIGH WATER MARK:
    - Avoids full table scan on every run
    - O(new data) instead of O(all data)
    - Critical for 100M+ record tables
    
    FIRST RUN LIMITATION:
    - Gold is empty → no high water mark
    - Must process all data (or limit)
    - max_initial_days=90 limits first run
    
    STRUCT FLATTENING:
    ------------------
    Bronze has nested structs:
    ```
    usage_metadata: STRUCT<cluster_id, job_id, ...>  (35 fields)
    identity_metadata: STRUCT<run_as, created_by, owned_by>
    product_features: STRUCT<jobs_tier, sql_tier, ...>  (15 fields)
    ```
    
    Gold has flat columns:
    ```
    usage_metadata_cluster_id: STRING
    usage_metadata_job_id: STRING
    ...
    ```
    
    WHY FLATTEN:
    - SQL queries are simpler (no struct traversal)
    - Better query performance (predicate pushdown)
    - BI tools work better with flat schemas
    
    DATA ENRICHMENT:
    ----------------
    Join with list_prices to get:
    - list_price: Unit price for the SKU
    - list_cost: usage_quantity * list_price
    
    WHY ENRICH IN GOLD:
    - Avoids join in every query
    - Pre-computed list_cost for aggregation
    - Single source of truth for pricing
    
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

# =============================================================================
# MAIN FUNCTION
# =============================================================================
# TRAINING MATERIAL: Pipeline Entry Point Pattern

def main():
    """
    Main entry point for Billing domain Gold layer MERGE.
    
    TRAINING MATERIAL: Pipeline Execution Pattern
    ==============================================
    
    EXECUTION FLOW:
    ---------------
    1. Print banner (for job log visibility)
    2. Get parameters (from widgets)
    3. Initialize SparkSession
    4. Execute merges in DEPENDENCY ORDER
    5. Handle success/failure
    6. Cleanup (spark.stop())
    
    DEPENDENCY ORDER:
    -----------------
    Tables must be merged in dependency order:
    
    ┌─────────────────────────────────────────────────────────────────┐
    │  DEPENDENCY GRAPH                                               │
    │                                                                 │
    │  dim_sku (no dependencies)                                      │
    │     ↑                                                           │
    │  fact_usage (references dim_sku via sku_name)                  │
    │                                                                 │
    │  fact_list_prices (no dependencies)                            │
    │     ↑                                                           │
    │  fact_usage (enriched with list_price)                         │
    └─────────────────────────────────────────────────────────────────┘
    
    MERGE ORDER:
    1. dim_sku - No dependencies, create first
    2. fact_list_prices - Lookup table for enrichment
    3. fact_usage - Depends on both (FK + enrichment)
    
    ERROR HANDLING:
    ---------------
    - try/except for clean error reporting
    - Traceback printed for debugging
    - Re-raise exception (job will fail)
    - finally block ensures cleanup
    
    WHY spark.stop():
    - Releases cluster resources
    - Clean shutdown in local mode
    - Note: In Databricks, this is often optional
    """
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - BILLING DOMAIN")
    print("=" * 80)
    
    # Get job parameters
    catalog, bronze_schema, gold_schema = get_parameters()
    
    # Initialize SparkSession
    # WHY appName: Appears in Spark UI, aids debugging
    spark = SparkSession.builder.appName("Gold Merge - Billing").getOrCreate()
    
    try:
        # =====================================================================
        # MERGE IN DEPENDENCY ORDER
        # =====================================================================
        # CRITICAL: Order matters for foreign key relationships
        
        # Step 1: Dimension tables first (no dependencies)
        print("\nStep 1: Merging dim_sku (no dependencies)...")
        merge_dim_sku(spark, catalog, bronze_schema, gold_schema)
        
        # Step 2: Lookup tables for enrichment
        print("\nStep 2: Merging fact_list_prices...")
        merge_fact_list_prices(spark, catalog, bronze_schema, gold_schema)
        
        # Step 3: Fact tables last (depend on dimensions)
        print("\nStep 3: Merging fact_usage (depends on dim_sku)...")
        merge_fact_usage(spark, catalog, bronze_schema, gold_schema)
        
        # Success banner
        print("\n" + "=" * 80)
        print("✓ Billing domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        # =====================================================================
        # ERROR HANDLING
        # =====================================================================
        # Print error and traceback for job logs
        print(f"\n❌ Error during Billing domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        # Re-raise to ensure job fails (not silent success)
        raise
        
    finally:
        # =====================================================================
        # CLEANUP
        # =====================================================================
        # Release resources (optional in Databricks, required locally)
        spark.stop()

# COMMAND ----------

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
# TRAINING MATERIAL: Standard Python Entry Point
#
# WHY if __name__ == "__main__":
# - Allows importing this module without executing main()
# - Standard Python convention
# - Enables unit testing of individual functions

if __name__ == "__main__":
    main()

