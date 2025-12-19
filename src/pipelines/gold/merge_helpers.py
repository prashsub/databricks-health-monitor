"""
Gold Layer Merge Helpers

Shared utilities for Bronze→Gold MERGE operations.
Implements patterns from cursor rules to prevent common bugs.

References:
- 10-gold-layer-merge-patterns.mdc
- 11-gold-delta-merge-deduplication.mdc
- 23-gold-layer-schema-validation.mdc
- 24-fact-table-grain-validation.mdc
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, when, lit, unix_timestamp,
    to_date, size, coalesce, md5, concat_ws, from_json, to_json
)
from pyspark.sql.types import MapType, StringType, ArrayType
from delta.tables import DeltaTable
from typing import List, Dict, Optional


def get_incremental_filter(
    spark: SparkSession,
    gold_table: str,
    watermark_column: str,
    max_initial_days: Optional[int] = None
) -> Optional[str]:
    """
    Get high-water mark from Gold table for incremental processing.
    
    Returns filter condition to apply to Bronze for incremental loads.
    First run (Gold empty): 
        - If max_initial_days is set: Returns filter for last N days
        - Otherwise: Returns None (process all data)
    Subsequent runs: Returns filter for records newer than Gold's max timestamp
    
    Args:
        spark: SparkSession
        gold_table: Fully qualified Gold table name
        watermark_column: Column to use for high-water mark (e.g., event_date, usage_date)
        max_initial_days: For large tables, limit first run to last N days (default: None = all data)
    
    Returns:
        Filter string to apply to Bronze, or None if Gold is empty and no max_initial_days
    """
    try:
        # Check if Gold table has data
        max_watermark = spark.sql(f"""
            SELECT MAX({watermark_column}) as max_val 
            FROM {gold_table}
        """).collect()[0]["max_val"]
        
        if max_watermark is None:
            # Gold is empty - first run
            if max_initial_days is not None:
                # Limit first run to last N days for large tables
                print(f"  ℹ️ Gold table is empty - limiting first run to last {max_initial_days} days")
                return f"{watermark_column} >= CURRENT_DATE() - INTERVAL {max_initial_days} DAYS"
            else:
                print(f"  ℹ️ Gold table is empty - processing ALL historical data (first run)")
                return None
        else:
            print(f"  ℹ️ Incremental mode: processing records where {watermark_column} > '{max_watermark}'")
            return f"{watermark_column} > '{max_watermark}'"
            
    except Exception as e:
        # Table doesn't exist or other error
        if max_initial_days is not None:
            print(f"  ℹ️ Gold table not accessible - limiting to last {max_initial_days} days: {str(e)[:100]}")
            return f"{watermark_column} >= CURRENT_DATE() - INTERVAL {max_initial_days} DAYS"
        else:
            print(f"  ℹ️ Gold table not accessible - processing ALL data: {str(e)[:100]}")
            return None


def deduplicate_bronze(
    df: DataFrame,
    business_keys: List[str],
    order_by_column: str = "bronze_ingestion_timestamp"
) -> tuple[DataFrame, int, int]:
    """
    Deduplicate Bronze source before MERGE (CRITICAL PATTERN).
    
    Pattern from: 11-gold-delta-merge-deduplication.mdc
    
    Args:
        df: Bronze DataFrame
        business_keys: List of business key columns for deduplication
        order_by_column: Timestamp column to order by (latest first)
    
    Returns:
        Tuple of (deduplicated_df, original_count, deduped_count)
    """
    original_count = df.count()
    
    deduped_df = (
        df
        .orderBy(col(order_by_column).desc())  # Latest first
        .dropDuplicates(business_keys)
    )
    
    deduped_count = deduped_df.count()
    duplicates_removed = original_count - deduped_count
    
    print(f"  Deduplicated: {original_count:,} → {deduped_count:,} records ({duplicates_removed:,} duplicates removed)")
    
    return deduped_df, original_count, deduped_count


def flatten_struct_fields(
    df: DataFrame,
    struct_column: str,
    field_mappings: Dict[str, str]
) -> DataFrame:
    """
    Flatten struct column into individual columns with explicit naming.
    
    Pattern from: 10-gold-layer-merge-patterns.mdc
    
    Args:
        df: Source DataFrame
        struct_column: Name of the struct column to flatten
        field_mappings: Dict mapping Bronze field → Gold column name
                       Example: {"cluster_id": "usage_metadata_cluster_id"}
    
    Returns:
        DataFrame with flattened columns
    """
    for bronze_field, gold_column in field_mappings.items():
        df = df.withColumn(
            gold_column,
            when(col(struct_column).isNotNull(), col(struct_column).getField(bronze_field))
            .otherwise(lit(None))
        )
    
    return df


def add_derived_duration_columns(
    df: DataFrame,
    start_col: str,
    end_col: str,
    prefix: str = "run"
) -> DataFrame:
    """
    Add derived duration columns (seconds and minutes).
    
    Pattern: Standard temporal calculations
    
    Args:
        df: Source DataFrame
        start_col: Start timestamp column name
        end_col: End timestamp column name
        prefix: Prefix for derived column names (e.g., "run", "execution")
    
    Returns:
        DataFrame with duration_seconds and duration_minutes columns
    """
    return (
        df
        .withColumn(f"{prefix}_duration_seconds",
                    when(col(end_col).isNotNull(),
                         unix_timestamp(col(end_col)) - unix_timestamp(col(start_col)))
                    .otherwise(None))
        .withColumn(f"{prefix}_duration_minutes",
                    col(f"{prefix}_duration_seconds") / 60.0)
    )


def add_tag_governance_columns(df: DataFrame, tag_column: str = "custom_tags") -> DataFrame:
    """
    Add tag governance columns (is_tagged, tag_count).
    
    Args:
        df: Source DataFrame with MAP<STRING,STRING> tag column
        tag_column: Name of the tag MAP column
    
    Returns:
        DataFrame with is_tagged and tag_count columns
    """
    return (
        df
        .withColumn("is_tagged",
                    (col(tag_column).isNotNull()) & (size(col(tag_column)) > 0))
        .withColumn("tag_count",
                    when(col(tag_column).isNotNull(), size(col(tag_column)))
                    .otherwise(None))
    )


def add_success_flag(
    df: DataFrame,
    status_column: str,
    success_values: List[str]
) -> DataFrame:
    """
    Add is_success boolean flag based on status column.
    
    Args:
        df: Source DataFrame
        status_column: Column containing status value
        success_values: List of status values considered "success"
    
    Returns:
        DataFrame with is_success column
    """
    return df.withColumn(
        "is_success",
        col(status_column).isin(success_values)
    )


def validate_merge_schema(
    spark: SparkSession,
    updates_df: DataFrame,
    catalog: str,
    schema: str,
    table_name: str,
    raise_on_mismatch: bool = True
) -> Dict:
    """
    Validate that merge DataFrame matches target table schema.
    
    Pattern from: 23-gold-layer-schema-validation.mdc
    
    Args:
        spark: SparkSession
        updates_df: DataFrame to merge
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        raise_on_mismatch: Whether to raise exception on mismatch
    
    Returns:
        Dict with 'valid', 'missing_in_df', 'extra_in_df', 'type_mismatches'
    
    Raises:
        ValueError if raise_on_mismatch=True and schema doesn't match
    """
    # Get target table schema
    target_table = f"{catalog}.{schema}.{table_name}"
    target_schema = spark.table(target_table).schema
    target_cols = {field.name: str(field.dataType) for field in target_schema.fields}
    
    # Get source DataFrame schema
    source_cols = {field.name: str(field.dataType) for field in updates_df.schema.fields}
    
    # Find mismatches
    missing_in_df = set(target_cols.keys()) - set(source_cols.keys())
    extra_in_df = set(source_cols.keys()) - set(target_cols.keys())
    
    type_mismatches = {}
    for col_name in set(target_cols.keys()) & set(source_cols.keys()):
        if target_cols[col_name] != source_cols[col_name]:
            type_mismatches[col_name] = {
                'target': target_cols[col_name],
                'source': source_cols[col_name]
            }
    
    is_valid = not (missing_in_df or extra_in_df or type_mismatches)
    
    result = {
        'valid': is_valid,
        'missing_in_df': list(missing_in_df),
        'extra_in_df': list(extra_in_df),
        'type_mismatches': type_mismatches
    }
    
    if not is_valid:
        error_msg = f"\n❌ Schema mismatch for {target_table}:\n"
        if missing_in_df:
            error_msg += f"  Missing in DataFrame: {sorted(missing_in_df)}\n"
        if extra_in_df:
            error_msg += f"  Extra in DataFrame: {sorted(extra_in_df)}\n"
        if type_mismatches:
            error_msg += "  Type mismatches:\n"
            for col_name, types in type_mismatches.items():
                error_msg += f"    {col_name}: target={types['target']}, source={types['source']}\n"
        
        if raise_on_mismatch:
            raise ValueError(error_msg)
        else:
            print(error_msg)
    
    return result


def merge_dimension_table(
    spark: SparkSession,
    updates_df: DataFrame,
    catalog: str,
    gold_schema: str,
    table_name: str,
    business_keys: List[str],
    scd_type: int = 1,
    validate_schema: bool = True
) -> int:
    """
    Generic MERGE pattern for dimension tables.
    
    Args:
        spark: SparkSession
        updates_df: Prepared updates DataFrame
        catalog: Catalog name
        gold_schema: Gold schema name
        table_name: Gold table name
        business_keys: Business key columns for MERGE condition
        scd_type: 1 (overwrite) or 2 (historical tracking)
        validate_schema: Whether to run schema validation
    
    Returns:
        Number of records merged
    """
    gold_table = f"{catalog}.{gold_schema}.{table_name}"
    
    # Schema validation (CRITICAL)
    if validate_schema:
        validate_merge_schema(spark, updates_df, catalog, gold_schema, table_name)
    
    # Build MERGE condition
    if scd_type == 2:
        # SCD Type 2: Match on business key + is_current flag
        merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in business_keys])
        merge_condition += " AND target.is_current = true"
    else:
        # SCD Type 1: Match on business key only
        merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in business_keys])
    
    # Execute MERGE
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    if scd_type == 2:
        # SCD Type 2: Only update timestamp for current records
        delta_gold.alias("target").merge(
            updates_df.alias("source"),
            merge_condition
        ).whenMatchedUpdate(set={
            "record_updated_timestamp": "source.record_updated_timestamp"
        }).whenNotMatchedInsertAll(
        ).execute()
    else:
        # SCD Type 1: Update all fields
        delta_gold.alias("target").merge(
            updates_df.alias("source"),
            merge_condition
        ).whenMatchedUpdateAll(
        ).whenNotMatchedInsertAll(
        ).execute()
    
    record_count = updates_df.count()
    print(f"✓ Merged {record_count} records into {table_name}")
    
    return record_count


def merge_fact_table(
    spark: SparkSession,
    updates_df: DataFrame,
    catalog: str,
    gold_schema: str,
    table_name: str,
    primary_keys: List[str],
    validate_schema: bool = True
) -> int:
    """
    Generic MERGE pattern for fact tables.
    
    Args:
        spark: SparkSession
        updates_df: Prepared updates DataFrame (already aggregated if needed)
        catalog: Catalog name
        gold_schema: Gold schema name
        table_name: Gold table name
        primary_keys: Primary key columns (defines grain)
        validate_schema: Whether to run schema validation
    
    Returns:
        Number of records merged
    """
    gold_table = f"{catalog}.{gold_schema}.{table_name}"
    
    # Schema validation (CRITICAL)
    if validate_schema:
        validate_merge_schema(spark, updates_df, catalog, gold_schema, table_name)
    
    # Build MERGE condition
    merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in primary_keys])
    
    # Execute MERGE
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        updates_df.alias("source"),
        merge_condition
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = updates_df.count()
    print(f"✓ Merged {record_count} records into {table_name}")
    
    return record_count


def enrich_usage_with_list_prices(
    spark: SparkSession,
    usage_df: DataFrame
) -> DataFrame:
    """
    Enrich usage records with list_price and list_cost from system.billing.list_prices.
    
    Joins usage records with pricing based on:
    - sku_name
    - cloud
    - usage_start_time within price effective period
    
    Args:
        spark: SparkSession
        usage_df: Bronze usage DataFrame
    
    Returns:
        DataFrame with list_price and list_cost columns
    """
    # Read list prices (non-streaming)
    list_prices_df = (
        spark.table("system.billing.list_prices")
        .select(
            col("sku_name").alias("price_sku_name"),
            col("cloud").alias("price_cloud"),
            col("price_start_time"),  # System table uses price_start_time
            col("price_end_time"),    # System table uses price_end_time
            col("pricing.default").alias("list_price")
        )
    )
    
    # Join with usage
    enriched_df = (
        usage_df
        .join(
            list_prices_df,
            on=[
                (col("sku_name") == col("price_sku_name")) &
                (col("cloud") == col("price_cloud")) &
                (col("usage_start_time") >= col("price_start_time")) &
                (
                    col("price_end_time").isNull() |
                    (col("usage_start_time") < col("price_end_time"))
                )
            ],
            how="left"
        )
        .withColumn("list_cost", col("usage_quantity") * col("list_price"))
        .drop("price_sku_name", "price_cloud", "price_start_time", "price_end_time")
    )
    
    return enriched_df


def flatten_usage_metadata(df: DataFrame) -> DataFrame:
    """
    Flatten usage_metadata struct into individual columns.
    
    Args:
        df: Bronze usage DataFrame with usage_metadata struct
    
    Returns:
        DataFrame with flattened usage_metadata_* columns
    """
    fields = [
        "cluster_id", "job_id", "warehouse_id", "instance_pool_id", "node_type",
        "job_run_id", "notebook_id", "dlt_pipeline_id", "endpoint_name", "endpoint_id",
        "dlt_update_id", "dlt_maintenance_id", "run_name", "job_name", "notebook_path",
        "central_clean_room_id", "source_region", "destination_region", "app_id",
        "app_name", "metastore_id", "private_endpoint_name", "storage_api_type",
        "budget_policy_id", "ai_runtime_pool_id", "ai_runtime_workload_id",
        "uc_table_catalog", "uc_table_schema", "uc_table_name", "database_instance_id",
        "sharing_materialization_id", "schema_id", "usage_policy_id",
        "base_environment_id", "agent_bricks_id", "index_id", "catalog_id"
    ]
    
    for field in fields:
        df = df.withColumn(
            f"usage_metadata_{field}",
            when(col("usage_metadata").isNotNull(), col("usage_metadata").getField(field))
            .otherwise(lit(None))
        )
    
    return df


def flatten_identity_metadata(df: DataFrame, prefix: str = "identity_metadata") -> DataFrame:
    """
    Flatten identity_metadata struct into individual columns.
    
    Args:
        df: Source DataFrame with identity_metadata struct
        prefix: Prefix for flattened column names
    
    Returns:
        DataFrame with flattened columns
    """
    # Note: Bronze identity struct has: run_as, created_by, owned_by (NOT run_by)
    fields = ["run_as", "created_by", "owned_by"]
    
    for field in fields:
        df = df.withColumn(
            f"{prefix}_{field}",
            when(col(prefix).isNotNull(), col(prefix).getField(field))
            .otherwise(lit(None))
        )
    
    return df


def flatten_product_features(df: DataFrame) -> DataFrame:
    """
    Flatten product_features struct into individual columns.
    
    Some fields are simple types (STRING, BOOLEAN) - extract directly.
    Some fields are nested structs - serialize to JSON STRING.
    
    Args:
        df: Bronze usage DataFrame with product_features struct
    
    Returns:
        DataFrame with flattened product_features_* columns (all as STRING except BOOLEANs)
    """
    # Simple string fields - extract directly
    simple_string_fields = [
        "jobs_tier", "sql_tier", "dlt_tier", "serving_type", "performance_target"
    ]
    
    # Boolean fields - extract directly
    boolean_fields = ["is_serverless", "is_photon"]
    
    # Struct fields - need to serialize to JSON string
    # These are struct types in Bronze that need to be STRING in Gold
    struct_fields = [
        "networking", "ai_runtime", "model_serving", "ai_gateway",
        "serverless_gpu", "agent_bricks", "ai_functions", "apps", "lakeflow_connect"
    ]
    
    # Extract simple string fields
    for field in simple_string_fields:
        df = df.withColumn(
            f"product_features_{field}",
            when(col("product_features").isNotNull(), col("product_features").getField(field))
            .otherwise(lit(None))
        )
    
    # Extract boolean fields
    for field in boolean_fields:
        df = df.withColumn(
            f"product_features_{field}",
            when(col("product_features").isNotNull(), col("product_features").getField(field))
            .otherwise(lit(None))
        )
    
    # Serialize struct fields to JSON STRING
    for field in struct_fields:
        df = df.withColumn(
            f"product_features_{field}",
            when(
                col("product_features").isNotNull() & col("product_features").getField(field).isNotNull(),
                to_json(col("product_features").getField(field))
            ).otherwise(lit(None))
        )
    
    return df


def check_table_exists(spark: SparkSession, catalog: str, schema: str, table_name: str) -> bool:
    """
    Check if a table exists.
    
    Args:
        spark: SparkSession
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
    
    Returns:
        True if table exists, False otherwise
    """
    try:
        spark.table(f"{catalog}.{schema}.{table_name}")
        return True
    except Exception:
        return False


def get_latest_by_timestamp(
    df: DataFrame,
    partition_keys: List[str],
    timestamp_col: str = "change_time"
) -> DataFrame:
    """
    Get latest record per partition (for SCD Type 2 dimensions).
    
    Args:
        df: Source DataFrame
        partition_keys: Columns to partition by
        timestamp_col: Timestamp column to order by
    
    Returns:
        DataFrame with latest record per partition
    """
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number
    
    window_spec = Window.partitionBy(*partition_keys).orderBy(col(timestamp_col).desc())
    
    return (
        df
        .withColumn("row_num", row_number().over(window_spec))
        .filter(col("row_num") == 1)
        .drop("row_num")
    )


def add_audit_timestamps(df: DataFrame) -> DataFrame:
    """
    Add record_created_timestamp and record_updated_timestamp columns.
    
    Args:
        df: Source DataFrame
    
    Returns:
        DataFrame with timestamp columns
    """
    return (
        df
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
    )


def print_merge_summary(
    table_name: str,
    original_count: int,
    deduped_count: int,
    merged_count: int
):
    """
    Print standardized merge summary.
    
    Args:
        table_name: Name of the table being merged
        original_count: Original record count from Bronze
        deduped_count: Count after deduplication
        merged_count: Final count merged to Gold
    """
    print(f"\n{'=' * 80}")
    print(f"MERGE SUMMARY: {table_name}")
    print(f"{'=' * 80}")
    print(f"  Original Bronze records: {original_count:,}")
    print(f"  After deduplication: {deduped_count:,}")
    print(f"  Duplicates removed: {original_count - deduped_count:,}")
    print(f"  Merged to Gold: {merged_count:,}")
    print(f"{'=' * 80}\n")

