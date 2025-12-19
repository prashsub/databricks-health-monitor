# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer MERGE - Compute Domain
# MAGIC
# MAGIC Merges Compute infrastructure dimension and fact tables from Bronze to Gold.
# MAGIC
# MAGIC **Tables:**
# MAGIC - dim_node_type (from compute.node_types) - reference data
# MAGIC - dim_cluster (from compute.clusters) - cluster configurations
# MAGIC - fact_node_timeline (from compute.node_timeline) - cluster utilization metrics

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, when, lit, to_json
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

def merge_dim_node_type(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_node_type from Bronze to Gold (SCD Type 1 - reference data).
    
    Bronze Source: system.compute.node_types → Bronze: node_types
    Gold Table: dim_node_type
    Primary Key: node_type (unique identifier)
    Grain: One row per node type (reference data)
    
    Column Mapping (Bronze → Gold):
    - Direct copy: account_id, node_type, core_count, memory_mb, gpu_count
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_node_type")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.node_types"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on node_type (PK)
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["node_type"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Prepare updates (all direct copy)
    updates_df = bronze_df.select(
        "account_id",
        "node_type",
        "core_count",
        "memory_mb",
        "gpu_count"
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (SCD Type 1 - reference data)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_node_type",
        business_keys=["node_type"],
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_node_type", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_dim_cluster(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge dim_cluster from Bronze to Gold (SCD Type 1).
    
    Bronze Source: system.compute.clusters → Bronze: clusters
    Gold Table: dim_cluster
    Primary Key: workspace_id, cluster_id (composite)
    Grain: One row per cluster per workspace
    
    Column Mapping (Bronze → Gold):
    - Direct copy: All cluster configuration columns
    - JSON serialization: tags → tags_json, init_scripts → init_scripts_json
    - Flattened: aws_attributes.*, azure_attributes.*, gcp_attributes.*
    """
    print("\n" + "=" * 80)
    print("MERGING: dim_cluster")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.clusters"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite business key
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "cluster_id"],
        order_by_column="change_time"
    )
    
    # Prepare updates - serialize complex types and flatten cloud attributes
    updates_df = (
        bronze_df
        # Serialize complex types to JSON strings
        .withColumn("tags_json",
                    when(col("tags").isNotNull(), to_json(col("tags")))
                    .otherwise(lit(None)))
        .withColumn("init_scripts_json",
                    when(col("init_scripts").isNotNull(), to_json(col("init_scripts")))
                    .otherwise(lit(None)))
        
        # Flatten AWS attributes (cast to STRING for consistency)
        .withColumn("aws_attributes_first_on_demand", 
                    col("aws_attributes.first_on_demand").cast("string"))
        .withColumn("aws_attributes_availability", 
                    col("aws_attributes.availability"))
        .withColumn("aws_attributes_zone_id", 
                    col("aws_attributes.zone_id"))
        .withColumn("aws_attributes_instance_profile_arn", 
                    col("aws_attributes.instance_profile_arn"))
        .withColumn("aws_attributes_spot_bid_price_percent", 
                    col("aws_attributes.spot_bid_price_percent").cast("string"))
        .withColumn("aws_attributes_ebs_volume_type", 
                    col("aws_attributes.ebs_volume_type"))
        .withColumn("aws_attributes_ebs_volume_count", 
                    col("aws_attributes.ebs_volume_count").cast("string"))
        .withColumn("aws_attributes_ebs_volume_size", 
                    col("aws_attributes.ebs_volume_size").cast("string"))
        .withColumn("aws_attributes_ebs_volume_iops", 
                    col("aws_attributes.ebs_volume_iops").cast("string"))
        .withColumn("aws_attributes_ebs_volume_throughput", 
                    col("aws_attributes.ebs_volume_throughput").cast("string"))
        
        # Flatten Azure attributes
        .withColumn("azure_attributes_first_on_demand", 
                    col("azure_attributes.first_on_demand").cast("string"))
        .withColumn("azure_attributes_availability", 
                    col("azure_attributes.availability"))
        .withColumn("azure_attributes_spot_bid_max_price", 
                    col("azure_attributes.spot_bid_max_price"))
        
        # Flatten GCP attributes
        .withColumn("gcp_attributes_use_preemptible_executors", 
                    col("gcp_attributes.use_preemptible_executors"))
        .withColumn("gcp_attributes_google_service_account", 
                    col("gcp_attributes.google_service_account"))
        .withColumn("gcp_attributes_boot_disk_size", 
                    col("gcp_attributes.boot_disk_size").cast("string"))
        .withColumn("gcp_attributes_availability", 
                    col("gcp_attributes.availability"))
        .withColumn("gcp_attributes_zone_id", 
                    col("gcp_attributes.zone_id"))
        .withColumn("gcp_attributes_local_ssd_count", 
                    col("gcp_attributes.local_ssd_count").cast("string"))
        
        .select(
            # Core identifiers
            "account_id",
            "workspace_id",
            "cluster_id",
            "cluster_name",
            "owned_by",
            "create_time",
            "delete_time",
            
            # Node configuration
            "driver_node_type",
            "worker_node_type",
            "worker_count",
            "min_autoscale_workers",
            "max_autoscale_workers",
            "auto_termination_minutes",
            "enable_elastic_disk",
            
            # Cluster metadata
            "cluster_source",
            "driver_instance_pool_id",
            "worker_instance_pool_id",
            "dbr_version",
            "change_time",
            "change_date",
            "data_security_mode",
            "policy_id",
            
            # JSON serialized columns
            "tags_json",
            "init_scripts_json",
            
            # AWS flattened attributes
            "aws_attributes_first_on_demand",
            "aws_attributes_availability",
            "aws_attributes_zone_id",
            "aws_attributes_instance_profile_arn",
            "aws_attributes_spot_bid_price_percent",
            "aws_attributes_ebs_volume_type",
            "aws_attributes_ebs_volume_count",
            "aws_attributes_ebs_volume_size",
            "aws_attributes_ebs_volume_iops",
            "aws_attributes_ebs_volume_throughput",
            
            # Azure flattened attributes
            "azure_attributes_first_on_demand",
            "azure_attributes_availability",
            "azure_attributes_spot_bid_max_price",
            
            # GCP flattened attributes
            "gcp_attributes_use_preemptible_executors",
            "gcp_attributes_google_service_account",
            "gcp_attributes_boot_disk_size",
            "gcp_attributes_availability",
            "gcp_attributes_zone_id",
            "gcp_attributes_local_ssd_count"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (SCD Type 1)
    merged_count = merge_dimension_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="dim_cluster",
        business_keys=["workspace_id", "cluster_id"],
        scd_type=1,
        validate_schema=True
    )
    
    print_merge_summary("dim_cluster", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def merge_fact_node_timeline(spark: SparkSession, catalog: str, bronze_schema: str, gold_schema: str):
    """
    Merge fact_node_timeline from Bronze to Gold.
    
    Bronze Source: system.compute.node_timeline → Bronze: node_timeline
    Gold Table: fact_node_timeline
    Primary Key: workspace_id, instance_id, start_time (composite)
    Grain: One row per node per hour (hourly time slices)
    
    Column Mapping (Bronze → Gold):
    - Direct copy: All utilization metrics (CPU, memory, disk, network)
    """
    print("\n" + "=" * 80)
    print("MERGING: fact_node_timeline")
    print("=" * 80)
    
    bronze_table = f"{catalog}.{bronze_schema}.node_timeline"
    
    # Read Bronze source
    bronze_raw = spark.table(bronze_table)
    
    # Deduplicate on composite PK
    bronze_df, original_count, deduped_count = deduplicate_bronze(
        bronze_raw,
        business_keys=["workspace_id", "instance_id", "start_time"],
        order_by_column="bronze_ingestion_timestamp"
    )
    
    # Prepare updates - serialize disk_free_bytes_per_mount_point to JSON
    updates_df = (
        bronze_df
        .withColumn("disk_free_bytes_per_mount_point_json",
                    when(col("disk_free_bytes_per_mount_point").isNotNull(), 
                         to_json(col("disk_free_bytes_per_mount_point")))
                    .otherwise(lit(None)))
        .select(
            # Core identifiers
            "account_id",
            "workspace_id",
            "cluster_id",
            "instance_id",
            "start_time",
            "end_time",
            "driver",
            
            # CPU metrics
            "cpu_user_percent",
            "cpu_system_percent",
            "cpu_wait_percent",
            
            # Memory metrics
            "mem_used_percent",
            "mem_swap_percent",
            
            # Network metrics
            "network_sent_bytes",
            "network_received_bytes",
            
            # Node info
            "node_type",
            "private_ip",
            
            # Disk metrics (JSON serialized from Bronze MAP type)
            "disk_free_bytes_per_mount_point_json"
        )
    )
    
    # NOTE: Gold table DDLs don't include audit timestamps
    
    # MERGE to Gold (hourly time slice grain)
    merged_count = merge_fact_table(
        spark=spark,
        updates_df=updates_df,
        catalog=catalog,
        gold_schema=gold_schema,
        table_name="fact_node_timeline",
        primary_keys=["workspace_id", "instance_id", "start_time"],
        validate_schema=True
    )
    
    print_merge_summary("fact_node_timeline", original_count, deduped_count, merged_count)
    
    return merged_count

# COMMAND ----------

def main():
    """Main entry point for Compute domain Gold layer MERGE."""
    print("\n" + "=" * 80)
    print("HEALTH MONITOR - GOLD LAYER MERGE - COMPUTE DOMAIN")
    print("=" * 80)
    
    catalog, bronze_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Gold Merge - Compute").getOrCreate()
    
    try:
        # Merge reference data first (dim_node_type)
        print("\nStep 1: Merging dim_node_type (reference data)...")
        merge_dim_node_type(spark, catalog, bronze_schema, gold_schema)
        
        # Merge cluster dimension
        print("\nStep 2: Merging dim_cluster...")
        merge_dim_cluster(spark, catalog, bronze_schema, gold_schema)
        
        # Merge node utilization fact
        print("\nStep 3: Merging fact_node_timeline...")
        merge_fact_node_timeline(spark, catalog, bronze_schema, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Compute domain MERGE completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during Compute domain MERGE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

