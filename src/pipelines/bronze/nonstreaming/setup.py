# Databricks notebook source
# MAGIC %md
# MAGIC # Non-Streaming System Tables Setup
# MAGIC 
# MAGIC Creates Bronze layer tables for the 8 system tables that don't support streaming.
# MAGIC These tables will be populated via MERGE operations on a scheduled basis.
# MAGIC 
# MAGIC **Tables created:**
# MAGIC - assistant_events (system.access.assistant_events)
# MAGIC - workspaces_latest (system.access.workspaces_latest)
# MAGIC - list_prices (system.billing.list_prices)
# MAGIC - node_types (system.compute.node_types)
# MAGIC - predictive_optimization_operations_history (system.storage.predictive_optimization_operations_history)
# MAGIC - results (system.data_classification.results)
# MAGIC - table_results (system.data_quality_monitoring.table_results)
# MAGIC - history (system.query.history)
# MAGIC - pipeline_update_timeline (system.lakeflow.pipeline_update_timeline) - has Deletion Vectors

# COMMAND ----------

from pyspark.sql import SparkSession

# COMMAND ----------

def get_parameters():
    """Get parameters from Databricks widgets."""
    catalog = dbutils.widgets.get("catalog")
    system_bronze_schema = dbutils.widgets.get("system_bronze_schema")
    return catalog, system_bronze_schema

# COMMAND ----------

def create_catalog_and_schema(spark: SparkSession, catalog: str, schema: str):
    """Ensures the Unity Catalog schema exists with proper configuration."""
    print(f"Verifying catalog '{catalog}' exists and creating schema '{schema}'...")
    
    # Verify catalog exists (fail if not)
    catalogs = [row.catalog for row in spark.sql("SHOW CATALOGS").collect()]
    if catalog not in catalogs:
        raise ValueError(
            f"❌ Catalog '{catalog}' does not exist. "
            f"Please create it manually before running setup.\n"
            f"Available catalogs: {', '.join(catalogs)}"
        )
    
    # Create schema with full properties
    spark.sql(f"""
        CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}
        COMMENT 'Bronze layer - Databricks system tables ingestion with streaming and non-streaming sources for health monitoring and observability'
        WITH DBPROPERTIES (
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'managed_by' = 'databricks_asset_bundles',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'databricks.pipelines.predictiveOptimizations.enabled' = 'true',
            'data_classification' = 'confidential',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'purpose' = 'health_monitoring_observability'
        )
    """)
    
    print(f"✓ Schema {catalog}.{schema} ready")

# COMMAND ----------

def create_assistant_events(spark: SparkSession, catalog: str, schema: str):
    """Create assistant_events table from system.access.assistant_events."""
    print("Creating assistant_events table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.assistant_events
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'access',
            'entity_type' = 'fact',
            'contains_pii' = 'true',
            'data_classification' = 'confidential',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.access.assistant_events',
            'retention_period' = '365_days'
        )
        COMMENT 'Bronze layer ingestion of system.access.assistant_events - tracks user messages sent to Databricks Assistant'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.access.assistant_events
        WHERE 1=0
    """)
    
    print("✓ Created assistant_events table")

# COMMAND ----------

def create_workspaces_latest(spark: SparkSession, catalog: str, schema: str):
    """Create workspaces_latest table from system.access.workspaces_latest."""
    print("Creating workspaces_latest table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.workspaces_latest
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'access',
            'entity_type' = 'dimension',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.access.workspaces_latest',
            'retention_period' = 'indefinite'
        )
        COMMENT 'Bronze layer ingestion of system.access.workspaces_latest - slow-changing dimension table of metadata for all workspaces in the account'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.access.workspaces_latest
        WHERE 1=0
    """)
    
    print("✓ Created workspaces_latest table")

# COMMAND ----------

def create_list_prices(spark: SparkSession, catalog: str, schema: str):
    """Create list_prices table from system.billing.list_prices."""
    print("Creating list_prices table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.list_prices
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'billing',
            'entity_type' = 'dimension',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.billing.list_prices',
            'retention_period' = 'indefinite'
        )
        COMMENT 'Bronze layer ingestion of system.billing.list_prices - historical log of SKU pricing with records added on each price change'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.billing.list_prices
        WHERE 1=0
    """)
    
    print("✓ Created list_prices table")

# COMMAND ----------

def create_node_types(spark: SparkSession, catalog: str, schema: str):
    """Create node_types table from system.compute.node_types."""
    print("Creating node_types table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.node_types
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'compute',
            'entity_type' = 'dimension',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.compute.node_types',
            'retention_period' = 'indefinite'
        )
        COMMENT 'Bronze layer ingestion of system.compute.node_types - captures currently available node types with basic hardware information'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.compute.node_types
        WHERE 1=0
    """)
    
    print("✓ Created node_types table")

# COMMAND ----------

def create_predictive_optimization_operations_history(spark: SparkSession, catalog: str, schema: str):
    """Create predictive_optimization_operations_history table."""
    print("Creating predictive_optimization_operations_history table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.predictive_optimization_operations_history
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'storage',
            'entity_type' = 'fact',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.storage.predictive_optimization_operations_history',
            'retention_period' = '180_days'
        )
        COMMENT 'Bronze layer ingestion of system.storage.predictive_optimization_operations_history - tracks operation history of predictive optimization feature'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.storage.predictive_optimization_operations_history
        WHERE 1=0
    """)
    
    print("✓ Created predictive_optimization_operations_history table")

# COMMAND ----------

def create_data_classification_results(spark: SparkSession, catalog: str, schema: str):
    """Create results table from system.data_classification.results."""
    print("Creating data_classification_results table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.data_classification_results
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'data_classification',
            'entity_type' = 'fact',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.data_classification.results',
            'retention_period' = '365_days'
        )
        COMMENT 'Bronze layer ingestion of system.data_classification.results - stores column-level detections of sensitive data classes across enabled catalogs'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.data_classification.results
        WHERE 1=0
    """)
    
    print("✓ Created data_classification_results table")

# COMMAND ----------

def create_data_quality_monitoring_table_results(spark: SparkSession, catalog: str, schema: str):
    """Create table_results table from system.data_quality_monitoring.table_results."""
    print("Creating data_quality_monitoring_table_results table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.data_quality_monitoring_table_results
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'data_quality_monitoring',
            'entity_type' = 'fact',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.data_quality_monitoring.table_results',
            'retention_period' = 'indefinite'
        )
        COMMENT 'Bronze layer ingestion of system.data_quality_monitoring.table_results - stores results of data quality monitoring checks (freshness, completeness) and incident information'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.data_quality_monitoring.table_results
        WHERE 1=0
    """)
    
    print("✓ Created data_quality_monitoring_table_results table")

# COMMAND ----------

def create_query_history(spark: SparkSession, catalog: str, schema: str):
    """Create history table from system.query.history."""
    print("Creating query_history table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.query_history
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'query',
            'entity_type' = 'fact',
            'contains_pii' = 'true',
            'data_classification' = 'confidential',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.query.history',
            'retention_period' = '365_days'
        )
        COMMENT 'Bronze layer ingestion of system.query.history - captures records for all queries run on SQL warehouses and serverless compute'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.query.history
        WHERE 1=0
    """)
    
    print("✓ Created query_history table")

# COMMAND ----------

def create_pipeline_update_timeline(spark: SparkSession, catalog: str, schema: str):
    """Create pipeline_update_timeline table from system.lakeflow.pipeline_update_timeline.
    
    Note: This table has Deletion Vectors enabled, which is incompatible with 
    Delta Sharing streaming. We ingest it via non-streaming MERGE instead.
    """
    print("Creating pipeline_update_timeline table...")
    
    spark.sql(f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.pipeline_update_timeline
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = 'databricks_system_tables',
            'domain' = 'lakeflow',
            'entity_type' = 'fact',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Platform Operations',
            'technical_owner' = 'Data Engineering',
            'source_table' = 'system.lakeflow.pipeline_update_timeline',
            'retention_period' = '365_days',
            'streaming_incompatible' = 'true',
            'streaming_incompatible_reason' = 'Deletion Vectors enabled'
        )
        COMMENT 'Bronze layer ingestion of system.lakeflow.pipeline_update_timeline - tracks start and end times and compute resources used for DLT pipeline updates. Ingested via MERGE due to Deletion Vectors incompatibility with streaming.'
        AS SELECT *, current_timestamp() AS bronze_ingestion_timestamp
        FROM system.lakeflow.pipeline_update_timeline
        WHERE 1=0
    """)
    
    print("✓ Created pipeline_update_timeline table")

# COMMAND ----------

def main():
    """Main entry point for non-streaming table setup."""
    
    catalog, system_bronze_schema = get_parameters()
    
    spark = SparkSession.builder.appName("System Tables Non-Streaming Setup").getOrCreate()
    
    print("\n" + "=" * 80)
    print("SYSTEM TABLES NON-STREAMING SETUP")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Schema: {system_bronze_schema}")
    print("=" * 80 + "\n")
    
    try:
        # Ensure schema exists
        create_catalog_and_schema(spark, catalog, system_bronze_schema)
        
        # Create all 8 non-streaming tables
        create_assistant_events(spark, catalog, system_bronze_schema)
        create_workspaces_latest(spark, catalog, system_bronze_schema)
        create_list_prices(spark, catalog, system_bronze_schema)
        create_node_types(spark, catalog, system_bronze_schema)
        create_predictive_optimization_operations_history(spark, catalog, system_bronze_schema)
        create_data_classification_results(spark, catalog, system_bronze_schema)
        create_data_quality_monitoring_table_results(spark, catalog, system_bronze_schema)
        create_query_history(spark, catalog, system_bronze_schema)
        create_pipeline_update_timeline(spark, catalog, system_bronze_schema)
        
        print("\n" + "=" * 80)
        print("✓ Non-streaming table setup completed successfully!")
        print(f"✓ Created 9 tables in {catalog}.{system_bronze_schema}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during non-streaming table setup: {str(e)}")
        raise
        
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

