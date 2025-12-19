# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Marketplace Domain
# MAGIC
# MAGIC Merges marketplace listing and access tables from Bronze to Gold.
# MAGIC
# MAGIC **Tables:**
# MAGIC - fact_listing_access (from marketplace.listing_access_events)
# MAGIC - fact_listing_funnel (from marketplace.listing_funnel_events)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from merge_helpers import (
    deduplicate_bronze,
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

def merge_fact_listing_access(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_listing_access from Bronze to Gold.
    
    Bronze Source: system.marketplace.listing_access_events
    Gold Table: fact_listing_access
    Primary Key: account_id, listing_id, consumer_email, event_time (composite)
    Grain: One row per data access event per consumer per listing
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_listing_access")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.listing_access_events"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_listing_access")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["account_id", "listing_id", "consumer_email", "event_time"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Select columns matching Gold schema
    updates_df = bronze_df.select(
        "account_id",
        "metastore_id",
        "metastore_cloud",
        "metastore_region",
        "provider_id",
        "provider_name",
        "listing_id",
        "listing_name",
        "consumer_delta_sharing_recipient_name",
        "consumer_delta_sharing_recipient_type",
        "consumer_cloud",
        "consumer_region",
        "consumer_metastore_id",
        "consumer_email",
        "consumer_name",
        "consumer_company",
        "consumer_intended_use",
        "consumer_comment",
        "event_type",
        "event_time",
        "event_date"
    )
    
    # MERGE to Gold
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_listing_access",
        primary_keys=["account_id", "listing_id", "consumer_email", "event_time"],
        validate_schema=False
    )
    
    print_merge_summary("fact_listing_access", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def merge_fact_listing_funnel(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_listing_funnel from Bronze to Gold.
    
    Bronze Source: system.marketplace.listing_funnel_events
    Gold Table: fact_listing_funnel
    Primary Key: event_id
    Grain: One row per funnel event
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_listing_funnel")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.listing_funnel_events"
    
    # Check if Bronze table exists
    try:
        bronze_raw = spark.table(bronze_table)
    except Exception as e:
        print(f"  ⚠️ Bronze table not found: {bronze_table}")
        print(f"  Skipping fact_listing_funnel")
        return 0
    
    record_count = bronze_raw.count()
    print(f"  Records to process: {record_count:,}")
    
    if record_count == 0:
        print("  ✓ No records to process")
        return 0
    
    # Deduplicate - use all available columns as composite key since no event_id in Bronze
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["account_id", "listing_id", "event_type", "event_time"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Select columns matching Gold schema
    updates_df = bronze_df.select(
        "account_id",
        "metastore_id",
        "metastore_cloud",
        "metastore_region",
        "provider_id",
        "provider_name",
        "listing_id",
        "listing_name",
        "event_type",
        "event_time",
        "event_date",
        "consumer_cloud",
        "consumer_region"
    )
    
    # MERGE to Gold - use composite key since event_id may not exist in source
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_listing_funnel",
        primary_keys=["account_id", "listing_id", "event_type", "event_time"],
        validate_schema=False
    )
    
    print_merge_summary("fact_listing_funnel", original_count, deduped_count, merged_count)
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Marketplace domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - MARKETPLACE DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Marketplace").getOrCreate()
    
    try:
        print("\nStep 1: Merging fact_listing_access...")
        merge_fact_listing_access(spark, catalog, bronze_schema, gold_schema)
        
        print("\nStep 2: Merging fact_listing_funnel...")
        merge_fact_listing_funnel(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Marketplace domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Marketplace domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()




