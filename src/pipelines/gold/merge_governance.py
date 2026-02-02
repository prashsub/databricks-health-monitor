# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Governance Domain
# MAGIC
# MAGIC ## TRAINING MATERIAL: Lineage Data Processing Pattern
# MAGIC
# MAGIC This notebook demonstrates handling complex nested data structures (like `entity_metadata`)
# MAGIC and extracting them into flat columns for analytics.
# MAGIC
# MAGIC ### Key Patterns Demonstrated:
# MAGIC
# MAGIC 1. **Nested Struct Extraction**
# MAGIC    - Bronze lineage tables have deeply nested `entity_metadata` structs
# MAGIC    - Gold layer needs flat columns for SQL analytics and joins
# MAGIC    - Use `.withColumn("flat_col", col("nested.path.field"))` pattern
# MAGIC
# MAGIC 2. **Entity Metadata Structure**:
# MAGIC    ```
# MAGIC    entity_metadata
# MAGIC    ├── job_info
# MAGIC    │   ├── job_id
# MAGIC    │   └── job_run_id
# MAGIC    ├── dlt_pipeline_info
# MAGIC    │   └── dlt_pipeline_id
# MAGIC    ├── notebook_id
# MAGIC    ├── dashboard_id
# MAGIC    └── sql_query_id
# MAGIC    ```
# MAGIC
# MAGIC 3. **NULL Handling for NOT NULL Constraints**
# MAGIC    - Gold tables have NOT NULL constraints on key columns
# MAGIC    - Must filter out NULL records before merge
# MAGIC    - Prevents constraint violation errors
# MAGIC
# MAGIC 4. **Array Column Handling**
# MAGIC    - Some columns are arrays (e.g., `source_column_ids`)
# MAGIC    - Use `to_json()` to serialize to string for compatibility
# MAGIC    - Alternative: explode() for row-per-element
# MAGIC
# MAGIC **Tables:**
# MAGIC - fact_column_lineage (from access.column_lineage)
# MAGIC - fact_table_lineage (from access.table_lineage)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, to_json
from merge_helpers import deduplicate_bronze, merge_fact_table, print_merge_summary

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    gold_schema = dbutils.widgets.get("gold_schema")
    print(f"Catalog: {catalog}")
    print(f"Bronze Schema: {bronze_schema}")
    print(f"Gold Schema: {gold_schema}")
    return catalog, bronze_schema, gold_schema

# COMMAND ----------

def merge_fact_column_lineage(spark, catalog, bronze_schema, gold_schema):
    print("\n" + "=" * 80)
    print("MERGING: fact_column_lineage")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.column_lineage"
    
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception:
        print(f"  Bronze table not found: {bronze_table}")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  No records to process")
        return 0
    
    # Filter out records with NULL required columns (NOT NULL constraints in Gold)
    # Required: record_id, source_table_name, source_column_name, target_table_name, target_column_name, event_time
    bronze_filtered = bronze_raw.filter(
        col("record_id").isNotNull() &
        col("source_table_name").isNotNull() &
        col("source_column_name").isNotNull() &
        col("target_table_name").isNotNull() &
        col("target_column_name").isNotNull() &
        col("event_time").isNotNull()
    )
    null_count = record_count - bronze_filtered.count()
    if null_count > 0:
        print(f"  Filtered out {null_count:,} records with NULL required columns")
    
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_filtered, business_keys=["record_id"], order_by_column="event_time"
    )
    
    # Extract individual IDs from entity_metadata for FK relationships
    updates_df = (
        bronze_df
        # Extract job info IDs
        .withColumn("entity_metadata_job_id", col("entity_metadata.job_info.job_id"))
        .withColumn("entity_metadata_job_run_id", col("entity_metadata.job_info.job_run_id"))
        # Extract dashboard/notebook/query IDs
        .withColumn("entity_metadata_dashboard_id", col("entity_metadata.dashboard_id"))
        .withColumn("entity_metadata_legacy_dashboard_id", col("entity_metadata.legacy_dashboard_id"))
        .withColumn("entity_metadata_notebook_id", col("entity_metadata.notebook_id"))
        .withColumn("entity_metadata_sql_query_id", col("entity_metadata.sql_query_id"))
        # Extract DLT pipeline IDs
        .withColumn("entity_metadata_pipeline_id", col("entity_metadata.dlt_pipeline_info.dlt_pipeline_id"))
        .withColumn("entity_metadata_pipeline_update_id", col("entity_metadata.dlt_pipeline_info.dlt_update_id"))
        .select(
            "account_id", "metastore_id", "workspace_id", "entity_type", "entity_id",
            "entity_run_id", "source_table_full_name", "source_table_catalog",
            "source_table_schema", "source_table_name", "source_path", "source_type",
            "source_column_name", "target_table_full_name", "target_table_catalog",
            "target_table_schema", "target_table_name", "target_path", "target_type",
            "target_column_name", "created_by", "event_time", "event_date", "record_id",
            "event_id", "statement_id",
            # Extracted entity metadata IDs (for FK relationships)
            "entity_metadata_job_id", "entity_metadata_job_run_id",
            "entity_metadata_dashboard_id", "entity_metadata_legacy_dashboard_id",
            "entity_metadata_notebook_id", "entity_metadata_sql_query_id",
            "entity_metadata_pipeline_id", "entity_metadata_pipeline_update_id"
        )
    )
    
    merged_count = merge_fact_table(
        spark=spark, updates_df=updates_df, catalog=catalog, gold_schema=gold_schema,
        table_name="fact_column_lineage", primary_keys=["record_id"], validate_schema=False
    )
    
    print_merge_summary("fact_column_lineage", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def merge_fact_table_lineage(spark, catalog, bronze_schema, gold_schema):
    print("\n" + "=" * 80)
    print("MERGING: fact_table_lineage")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.table_lineage"
    
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception:
        print(f"  Bronze table not found: {bronze_table}")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  No records to process")
        return 0
    
    # Filter out records with NULL record_id (required for PK constraint)
    bronze_filtered = bronze_raw.filter(col("record_id").isNotNull())
    null_count = record_count - bronze_filtered.count()
    if null_count > 0:
        print(f"  Filtered out {null_count:,} records with NULL record_id")
    
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_filtered, business_keys=["record_id"], order_by_column="event_time"
    )
    
    # Extract individual IDs from entity_metadata for FK relationships
    updates_df = (
        bronze_df
        # Extract job info IDs
        .withColumn("entity_metadata_job_id", col("entity_metadata.job_info.job_id"))
        .withColumn("entity_metadata_job_run_id", col("entity_metadata.job_info.job_run_id"))
        # Extract dashboard/notebook/query IDs
        .withColumn("entity_metadata_dashboard_id", col("entity_metadata.dashboard_id"))
        .withColumn("entity_metadata_legacy_dashboard_id", col("entity_metadata.legacy_dashboard_id"))
        .withColumn("entity_metadata_notebook_id", col("entity_metadata.notebook_id"))
        .withColumn("entity_metadata_sql_query_id", col("entity_metadata.sql_query_id"))
        # Extract DLT pipeline IDs
        .withColumn("entity_metadata_pipeline_id", col("entity_metadata.dlt_pipeline_info.dlt_pipeline_id"))
        .withColumn("entity_metadata_pipeline_update_id", col("entity_metadata.dlt_pipeline_info.dlt_update_id"))
        .select(
            "account_id", "metastore_id", "workspace_id", "entity_type", "entity_id",
            "entity_run_id", "source_table_full_name", "source_table_catalog",
            "source_table_schema", "source_table_name", "source_path", "source_type",
            "target_table_full_name", "target_table_catalog", "target_table_schema",
            "target_table_name", "target_path", "target_type", "created_by",
            "event_time", "event_date", "record_id", "event_id", "statement_id",
            # Extracted entity metadata IDs (for FK relationships)
            "entity_metadata_job_id", "entity_metadata_job_run_id",
            "entity_metadata_dashboard_id", "entity_metadata_legacy_dashboard_id",
            "entity_metadata_notebook_id", "entity_metadata_sql_query_id",
            "entity_metadata_pipeline_id", "entity_metadata_pipeline_update_id"
        )
    )
    
    merged_count = merge_fact_table(
        spark=spark, updates_df=updates_df, catalog=catalog, gold_schema=gold_schema,
        table_name="fact_table_lineage", primary_keys=["record_id"], validate_schema=False
    )
    
    print_merge_summary("fact_table_lineage", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def main():
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - GOVERNANCE DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    spark = SparkSession.builder.appName("Gold Merge - Governance").getOrCreate()
    
    try:
        print("\nStep 1: Merging fact_column_lineage...")
        merge_fact_column_lineage(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 2: Merging fact_table_lineage...")
        merge_fact_table_lineage(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("Governance domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError during Governance domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

