# Databricks notebook source
# MAGIC %md
# MAGIC # Non-Streaming System Tables MERGE
# MAGIC 
# MAGIC Performs MERGE operations to sync non-streaming system tables to Bronze layer.
# MAGIC Uses natural keys for deduplication and handles incremental updates.
# MAGIC 
# MAGIC **Tables synced:**
# MAGIC - assistant_events (event_id)
# MAGIC - workspaces_latest (workspace_id - SCD Type 1)
# MAGIC - list_prices (sku_name, cloud, price_start_time)
# MAGIC - node_types (node_type_id)
# MAGIC - predictive_optimization_operations_history (operation_id)
# MAGIC - data_classification_results (catalog_name, schema_name, table_name, column_name, class_tag)
# MAGIC - data_quality_monitoring_table_results (catalog_name, schema_name, table_name, event_time)
# MAGIC - query_history (statement_id)
# MAGIC - pipeline_update_timeline (workspace_id, update_id) - has Deletion Vectors

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, col, row_number
from delta.tables import DeltaTable

# COMMAND ----------

def get_parameters():
    """Get parameters from Databricks widgets."""
    catalog = dbutils.widgets.get("catalog")
    system_bronze_schema = dbutils.widgets.get("system_bronze_schema")
    return catalog, system_bronze_schema

# COMMAND ----------

def merge_assistant_events(spark: SparkSession, catalog: str, schema: str):
    """MERGE assistant_events using event_id as natural key."""
    print("Merging assistant_events...")
    
    source_df = (
        spark.table("system.access.assistant_events")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.assistant_events"
    delta_table = DeltaTable.forName(spark, target_table)
    
    delta_table.alias("target").merge(
        source_df.alias("source"),
        "target.event_id = source.event_id"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into assistant_events")
    return record_count

# COMMAND ----------

def merge_workspaces_latest(spark: SparkSession, catalog: str, schema: str):
    """MERGE workspaces_latest using workspace_id as natural key (SCD Type 1)."""
    print("Merging workspaces_latest...")
    
    source_df = (
        spark.table("system.access.workspaces_latest")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.workspaces_latest"
    delta_table = DeltaTable.forName(spark, target_table)
    
    delta_table.alias("target").merge(
        source_df.alias("source"),
        "target.workspace_id = source.workspace_id"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into workspaces_latest")
    return record_count

# COMMAND ----------

def merge_list_prices(spark: SparkSession, catalog: str, schema: str):
    """MERGE list_prices using composite key (sku_name, cloud, price_start_time)."""
    print("Merging list_prices...")
    
    source_df = (
        spark.table("system.billing.list_prices")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.list_prices"
    delta_table = DeltaTable.forName(spark, target_table)
    
    delta_table.alias("target").merge(
        source_df.alias("source"),
        """target.sku_name = source.sku_name 
           AND target.cloud = source.cloud 
           AND target.price_start_time = source.price_start_time"""
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into list_prices")
    return record_count

# COMMAND ----------

def merge_node_types(spark: SparkSession, catalog: str, schema: str):
    """MERGE node_types using composite key (account_id, node_type)."""
    print("Merging node_types...")
    
    source_df = (
        spark.table("system.compute.node_types")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.node_types"
    delta_table = DeltaTable.forName(spark, target_table)
    
    # Composite key: account_id + node_type
    delta_table.alias("target").merge(
        source_df.alias("source"),
        "target.account_id = source.account_id AND target.node_type = source.node_type"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into node_types")
    return record_count

# COMMAND ----------

def merge_predictive_optimization_operations_history(spark: SparkSession, catalog: str, schema: str):
    """MERGE predictive_optimization_operations_history using operation_id as natural key."""
    print("Merging predictive_optimization_operations_history...")
    
    source_df = (
        spark.table("system.storage.predictive_optimization_operations_history")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.predictive_optimization_operations_history"
    delta_table = DeltaTable.forName(spark, target_table)
    
    delta_table.alias("target").merge(
        source_df.alias("source"),
        "target.operation_id = source.operation_id"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into predictive_optimization_operations_history")
    return record_count

# COMMAND ----------

def merge_data_classification_results(spark: SparkSession, catalog: str, schema: str):
    """MERGE data_classification_results using composite key with deduplication."""
    print("Merging data_classification_results...")
    
    from pyspark.sql import Window
    
    # Deduplicate source by composite key, keeping latest record
    # Pattern: Gold layer MERGE deduplication (rule 11-gold-delta-merge-deduplication.mdc)
    window_spec = Window.partitionBy(
        "catalog_name", "schema_name", "table_name", "column_name", "class_tag"
    ).orderBy(col("latest_detected_time").desc())
    
    source_df = (
        spark.table("system.data_classification.results")
        .withColumn("_row_num", row_number().over(window_spec))
        .filter(col("_row_num") == 1)  # Keep only most recent per key
        .drop("_row_num")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.data_classification_results"
    delta_table = DeltaTable.forName(spark, target_table)
    
    # Spark Connect compatible: Use whenMatchedUpdateAll() without set parameter
    delta_table.alias("target").merge(
        source_df.alias("source"),
        """target.catalog_name = source.catalog_name 
           AND target.schema_name = source.schema_name 
           AND target.table_name = source.table_name 
           AND target.column_name = source.column_name 
           AND target.class_tag = source.class_tag"""
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into data_classification_results (deduplicated)")
    return record_count

# COMMAND ----------

def merge_data_quality_monitoring_table_results(spark: SparkSession, catalog: str, schema: str):
    """MERGE data_quality_monitoring_table_results using composite key."""
    print("Merging data_quality_monitoring_table_results...")
    
    source_df = (
        spark.table("system.data_quality_monitoring.table_results")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.data_quality_monitoring_table_results"
    delta_table = DeltaTable.forName(spark, target_table)
    
    delta_table.alias("target").merge(
        source_df.alias("source"),
        """target.catalog_name = source.catalog_name 
           AND target.schema_name = source.schema_name 
           AND target.table_name = source.table_name 
           AND target.event_time = source.event_time"""
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into data_quality_monitoring_table_results")
    return record_count

# COMMAND ----------

def merge_query_history(spark: SparkSession, catalog: str, schema: str):
    """MERGE query_history using statement_id as natural key with update_time check."""
    print("Merging query_history...")
    
    source_df = (
        spark.table("system.query.history")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.query_history"
    delta_table = DeltaTable.forName(spark, target_table)
    
    # Spark Connect compatible: Move time condition into merge condition
    delta_table.alias("target").merge(
        source_df.alias("source"),
        "target.statement_id = source.statement_id AND source.update_time > target.update_time"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into query_history")
    return record_count

# COMMAND ----------

def merge_pipeline_update_timeline(spark: SparkSession, catalog: str, schema: str):
    """MERGE pipeline_update_timeline using composite key (workspace_id, update_id).
    
    Note: This table has Deletion Vectors enabled, which is incompatible with 
    Delta Sharing streaming. We ingest it via non-streaming MERGE instead.
    """
    print("Merging pipeline_update_timeline...")
    
    source_df = (
        spark.table("system.lakeflow.pipeline_update_timeline")
        .withColumn("bronze_ingestion_timestamp", current_timestamp())
    )
    
    target_table = f"{catalog}.{schema}.pipeline_update_timeline"
    delta_table = DeltaTable.forName(spark, target_table)
    
    # Composite key: workspace_id + update_id (unique per pipeline update)
    delta_table.alias("target").merge(
        source_df.alias("source"),
        "target.workspace_id = source.workspace_id AND target.update_id = source.update_id"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = source_df.count()
    print(f"✓ Merged {record_count} records into pipeline_update_timeline")
    return record_count

# COMMAND ----------

def main():
    """Main entry point for non-streaming MERGE operations."""
    
    catalog, system_bronze_schema = get_parameters()
    
    spark = SparkSession.builder.appName("System Tables Non-Streaming MERGE").getOrCreate()
    
    print("\n" + "=" * 80)
    print("SYSTEM TABLES NON-STREAMING MERGE")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Schema: {system_bronze_schema}")
    print("=" * 80 + "\n")
    
    failed_tables = []
    total_records = 0
    
    try:
        # Merge all 8 non-streaming tables
        # Continue on failure so we can see all errors
        
        try:
            total_records += merge_assistant_events(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge assistant_events: {str(e)}")
            failed_tables.append("assistant_events")
        
        try:
            total_records += merge_workspaces_latest(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge workspaces_latest: {str(e)}")
            failed_tables.append("workspaces_latest")
        
        try:
            total_records += merge_list_prices(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge list_prices: {str(e)}")
            failed_tables.append("list_prices")
        
        try:
            total_records += merge_node_types(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge node_types: {str(e)}")
            failed_tables.append("node_types")
        
        try:
            total_records += merge_predictive_optimization_operations_history(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge predictive_optimization_operations_history: {str(e)}")
            failed_tables.append("predictive_optimization_operations_history")
        
        try:
            total_records += merge_data_classification_results(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge data_classification_results: {str(e)}")
            failed_tables.append("data_Referenced_results")
        
        try:
            total_records += merge_data_quality_monitoring_table_results(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge data_quality_monitoring_table_results: {str(e)}")
            failed_tables.append("data_quality_monitoring_table_results")
        
        try:
            total_records += merge_query_history(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge query_history: {str(e)}")
            failed_tables.append("query_history")
        
        try:
            total_records += merge_pipeline_update_timeline(spark, catalog, system_bronze_schema)
        except Exception as e:
            print(f"❌ Failed to merge pipeline_update_timeline: {str(e)}")
            failed_tables.append("pipeline_update_timeline")
        
        print("\n" + "=" * 80)
        if failed_tables:
            print(f"⚠️  MERGE completed with {len(failed_tables)} failure(s)")
            print(f"✓ Successfully merged {9 - len(failed_tables)}/9 tables")
            print(f"✓ Total records processed: {total_records}")
            print(f"❌ Failed tables: {', '.join(failed_tables)}")
            print("=" * 80)
            raise RuntimeError(f"Failed to merge {len(failed_tables)} table(s): {', '.join(failed_tables)}")
        else:
            print("✓ Non-streaming MERGE completed successfully!")
            print(f"✓ Successfully merged all 9 tables")
            print(f"✓ Total records processed: {total_records}")
            print("=" * 80)
        
    except Exception as e:
        if not failed_tables:
            print(f"\n❌ Error during non-streaming MERGE: {str(e)}")
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

