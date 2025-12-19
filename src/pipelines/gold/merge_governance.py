# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Governance Domain
# MAGIC
# MAGIC Merges lineage tables from Bronze to Gold.
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

