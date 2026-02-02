# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Shared Domain
# MAGIC
# MAGIC ## TRAINING MATERIAL: Shared Dimension Pattern
# MAGIC
# MAGIC This notebook processes shared dimension tables that are used across
# MAGIC multiple domains and fact tables.
# MAGIC
# MAGIC ### Why Shared Dimensions?
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────────────┐
# MAGIC │                           dim_workspace                                  │
# MAGIC │  ┌─────────────────────────────────────────────────────────────────┐    │
# MAGIC │  │  workspace_id (PK)                                              │    │
# MAGIC │  │  workspace_name                                                 │    │
# MAGIC │  │  region, cloud, pricing_tier                                    │    │
# MAGIC │  └─────────────────────────────────────────────────────────────────┘    │
# MAGIC │                               ▲                                         │
# MAGIC │          ┌────────────────────┼────────────────────┐                   │
# MAGIC │          │                    │                    │                   │
# MAGIC │   fact_usage        fact_audit_logs      fact_query_history           │
# MAGIC │   (billing)         (security)           (performance)                 │
# MAGIC │                                                                         │
# MAGIC │  Same workspace_id used across ALL domains                             │
# MAGIC └─────────────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ### SCD Type 1 for Workspaces
# MAGIC
# MAGIC Workspaces use SCD Type 1 (overwrite) because:
# MAGIC - Workspace attributes (name, region) are current state
# MAGIC - Historical workspace names not needed for analytics
# MAGIC - Simpler querying (no is_current filter needed)
# MAGIC
# MAGIC **Tables:**
# MAGIC - dim_workspace (from access.workspaces_latest)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from merge_helpers import (
    deduplicate_bronze,
    merge_dimension_table,
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

def merge_dim_workspace(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_workspace from Bronze to Gold (SCD Type 1).
    
    Bronze Source: system.access.workspaces_latest → Bronze: workspaces_latest
    Gold Table: dim_workspace
    Primary Key: workspace_id
    Grain: One row per workspace (overwrites on changes)
    
    Column Mapping (Bronze → Gold):
    - All columns are direct copy (names match)
    - No nested structs to flatten
    - No derived columns needed
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_workspace")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.workspaces_latest"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on workspace_id (business key)
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Prepare updates (direct column mapping - no transformations needed)
    # NOTE: Gold table DDLs don't include audit timestamps
    updates_df = (
        bronze_df
        .select(
            # All columns from Bronze (direct copy)
            "account_id",
            "workspace_id",
            "workspace_name",
            "workspace_url",
            "create_time",
            "status"
        )
    )
    
    # MERGE to Gold (SCD Type 1)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_workspace",
        business_keys=["workspace_id"],
        scd_type=1,
        validate_schema=True  # CRITICAL: Validate before merge
    )
    
    print_merge_summary("dim_workspace", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Shared domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - SHARED DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Shared").getOrCreate()
    
    try:
        # Merge dimension tables
        merge_dim_workspace(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Shared domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Shared domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

