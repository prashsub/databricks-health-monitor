# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Storage Domain
# MAGIC
# MAGIC ## TRAINING MATERIAL: Predictive Optimization Tracking
# MAGIC
# MAGIC This notebook processes Predictive Optimization operations history,
# MAGIC tracking automatic OPTIMIZE, VACUUM, and ZORDER operations.
# MAGIC
# MAGIC ### What is Predictive Optimization?
# MAGIC
# MAGIC ```
# MAGIC Databricks Predictive Optimization automatically:
# MAGIC
# MAGIC ┌─────────────────────────────────────────────────────────────────────────┐
# MAGIC │  OPTIMIZE        │  Compacts small files into optimal sizes            │
# MAGIC │  VACUUM          │  Removes old versions and deleted files             │
# MAGIC │  ZORDER          │  Co-locates related data for faster queries         │
# MAGIC └─────────────────────────────────────────────────────────────────────────┘
# MAGIC
# MAGIC System tables track all automatic operations for:
# MAGIC - Cost attribution (each operation has usage_quantity)
# MAGIC - Performance analysis (before/after metrics)
# MAGIC - Governance (who enabled it, when)
# MAGIC ```
# MAGIC
# MAGIC ### Operation Metrics Structure
# MAGIC
# MAGIC The `operation_metrics` column contains operation-specific metrics:
# MAGIC - OPTIMIZE: files_before, files_after, bytes_rewritten
# MAGIC - VACUUM: files_deleted, bytes_freed
# MAGIC - ZORDER: columns_ordered, data_skipping_effectiveness
# MAGIC
# MAGIC We serialize this to `operation_metrics_json` for BI compatibility.
# MAGIC
# MAGIC **Tables:**
# MAGIC - fact_predictive_optimization (from storage.predictive_optimization_operations_history)

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

def merge_fact_predictive_optimization(spark, catalog, bronze_schema, gold_schema):
    print("\n" + "=" * 80)
    print("MERGING: fact_predictive_optimization")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.predictive_optimization_operations_history"
    
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
    
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw, business_keys=["operation_id"], order_by_column="end_time"
    )
    
    # Serialize operation_metrics to JSON
    updates_df = (
        bronze_df
        .withColumn("operation_metrics_json",
                    when(col("operation_metrics").isNotNull(),
                         to_json(col("operation_metrics"))).otherwise(lit(None)))
        .select(
            "account_id", "workspace_id", "start_time", "end_time",
            "metastore_name", "metastore_id", "catalog_name", "schema_name",
            "table_name", "table_id", "operation_type", "operation_id",
            "operation_status", "usage_unit", "usage_quantity",
            "operation_metrics_json"
        )
    )
    
    merged_count = merge_fact_table(
        spark=spark, updates_df=updates_df, catalog=catalog, gold_schema=gold_schema,
        table_name="fact_predictive_optimization", primary_keys=["operation_id"],
        validate_schema=False
    )
    
    print_merge_summary("fact_predictive_optimization", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def main():
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - STORAGE DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    spark = SparkSession.builder.appName("Gold Merge - Storage").getOrCreate()
    
    try:
        print("\nStep 1: Merging fact_predictive_optimization...")
        merge_fact_predictive_optimization(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("Storage domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError during Storage domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()




