# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Model Serving Domain
# MAGIC
# MAGIC ## TRAINING MATERIAL: Model Serving Cost Attribution
# MAGIC
# MAGIC This notebook processes Model Serving tables for ML deployment
# MAGIC observability and cost tracking.
# MAGIC
# MAGIC ### Model Serving Cost Components
# MAGIC
# MAGIC ```
# MAGIC Total Serving Cost = Compute + Token Usage (for LLMs)
# MAGIC
# MAGIC ┌─────────────────────────────────────────────────────────────────────────┐
# MAGIC │  COMPONENT         │  SOURCE                  │  COST DRIVER            │
# MAGIC ├────────────────────┼──────────────────────────┼─────────────────────────┤
# MAGIC │  Compute           │  endpoint_usage          │  GPU hours × price      │
# MAGIC │  Foundation Model  │  endpoint_usage          │  Tokens × token price   │
# MAGIC │  External Model    │  endpoint_usage          │  Tokens × provider rate │
# MAGIC └────────────────────┴──────────────────────────┴─────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ### Served Entities Dimension
# MAGIC
# MAGIC `dim_served_entities` tracks model deployment configurations:
# MAGIC
# MAGIC | Field | Description |
# MAGIC |-------|-------------|
# MAGIC | endpoint_name | Logical endpoint name |
# MAGIC | entity_name | Model name in UC |
# MAGIC | entity_version | Model version deployed |
# MAGIC | workload_size | Small/Medium/Large |
# MAGIC | scale_to_zero | Cost optimization setting |
# MAGIC
# MAGIC **Tables:**
# MAGIC - dim_served_entities (from serving.served_entities)
# MAGIC - fact_endpoint_usage (from serving.endpoint_usage)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, lit, to_json
)
from merge_helpers import (
    deduplicate_bronze,
    merge_dimension_table,
    merge_fact_table,
    print_merge_summary
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

def merge_dim_served_entities(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_served_entities from Bronze to Gold (SCD Type 1).
    
    Bronze Source: system.serving.served_entities
    Gold Table: dim_served_entities
    Primary Key: served_entity_id
    Grain: One row per served model entity
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_served_entities")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.served_entities"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping dim_served_entities")
        return 0
    
    # Deduplicate on business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["served_entity_id"],
        order_by_column="change_time"
    )
    
    # Flatten nested configuration fields
    updates_df = (
        bronze_df
        # Flatten external_model_config
        .withColumn("external_model_config_provider",
                    col("external_model_config.provider"))
        # Flatten foundation_model_config
        .withColumn("foundation_model_config_min_provisioned_throughput",
                    col("foundation_model_config.min_provisioned_throughput").cast("string"))
        .withColumn("foundation_model_config_max_provisioned_throughput",
                    col("foundation_model_config.max_provisioned_throughput").cast("string"))
        # Flatten custom_model_config
        .withColumn("custom_model_config_min_concurrency",
                    col("custom_model_config.min_concurrency"))
        .withColumn("custom_model_config_max_concurrency",
                    col("custom_model_config.max_concurrency"))
        .withColumn("custom_model_config_compute_type",
                    col("custom_model_config.compute_type"))
        # Flatten feature_spec_config
        .withColumn("feature_spec_config_min_concurrency",
                    col("feature_spec_config.min_concurrency"))
        .withColumn("feature_spec_config_max_concurrency",
                    col("feature_spec_config.max_concurrency"))
        .withColumn("feature_spec_config_compute_type",
                    col("feature_spec_config.compute_type"))
        .select(
            "served_entity_id",
            "account_id",
            "workspace_id",
            "created_by",
            "endpoint_name",
            "endpoint_id",
            "served_entity_name",
            "entity_type",
            "entity_name",
            "entity_version",
            "endpoint_config_version",
            "task",
            "change_time",
            "endpoint_delete_time",
            "external_model_config_provider",
            "foundation_model_config_min_provisioned_throughput",
            "foundation_model_config_max_provisioned_throughput",
            "custom_model_config_min_concurrency",
            "custom_model_config_max_concurrency",
            "custom_model_config_compute_type",
            "feature_spec_config_min_concurrency",
            "feature_spec_config_max_concurrency",
            "feature_spec_config_compute_type"
        )
    )
    
    # MERGE to Gold (SCD Type 1)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_served_entities",
        business_keys=["served_entity_id"],
        scd_type=1,
        validate_schema=False
    )
    
    print_merge_summary("dim_served_entities", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def merge_fact_endpoint_usage(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_endpoint_usage from Bronze to Gold.
    
    Bronze Source: system.serving.endpoint_usage
    Gold Table: fact_endpoint_usage
    Primary Key: databricks_request_id
    Grain: One row per inference request
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_endpoint_usage")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.endpoint_usage"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_endpoint_usage")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate on business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["databricks_request_id"],
        order_by_column="request_time"
    )
    
    # Serialize nested fields to JSON
    updates_df = (
        bronze_df
        .withColumn("usage_context_json",
                    when(col("usage_context").isNotNull(), to_json(col("usage_context")))
                    .otherwise(lit(None)))
        .select(
            "workspace_id",
            "account_id",
            "client_request_id",
            "databricks_request_id",
            "requester",
            "status_code",
            "request_time",
            "input_token_count",
            "output_token_count",
            "input_character_count",
            "output_character_count",
            "request_streaming",
            "served_entity_id",
            "usage_context_json"
        )
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_endpoint_usage",
        primary_keys=["databricks_request_id"],
        validate_schema=False
    )
    
    print_merge_summary("fact_endpoint_usage", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Model Serving domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - MODEL SERVING DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Model Serving").getOrCreate()
    
    try:
        # Merge dimension first
        print("\nStep 1: Merging dim_served_entities...")
        merge_dim_served_entities(spark, catalog, bronze_schema, gold_schema)
        
        # Merge fact
        print("\nStep 2: Merging fact_endpoint_usage...")
        merge_fact_endpoint_usage(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Model Serving domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Model Serving domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()




