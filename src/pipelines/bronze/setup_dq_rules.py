# Databricks notebook source
"""
Setup DQ Rules Table

Creates and populates the dq_rules Delta table with comprehensive data quality rules
for all Bronze streaming tables.

This table is used by the dq_rules_loader module to dynamically load rules at DLT runtime.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, BooleanType, TimestampType
from pyspark.sql.functions import current_timestamp
from datetime import datetime

def get_parameters():
    """Get job parameters from widgets."""
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Bronze Schema: {bronze_schema}")
    
    return catalog, bronze_schema

def create_dq_rules_table(spark: SparkSession, catalog: str, schema: str):
    """Create the dq_rules table if it doesn't exist."""
    
    # Ensure catalog and schema exist
    print(f"\nEnsuring catalog and schema exist...")
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    print(f"✓ Catalog and schema ready: {catalog}.{schema}")
    
    table_name = f"{catalog}.{schema}.dq_rules"
    
    print(f"\nCreating dq_rules table: {table_name}")
    
    # Drop existing table to ensure clean schema
    spark.sql(f"DROP TABLE IF EXISTS {table_name}")
    print(f"  Dropped existing table (if any)")
    
    spark.sql(f"""
        CREATE TABLE {table_name} (
            table_name STRING NOT NULL COMMENT 'Bronze table name',
            rule_name STRING NOT NULL COMMENT 'Unique rule name',
            rule_constraint STRING NOT NULL COMMENT 'SQL constraint for the rule',
            severity STRING NOT NULL COMMENT 'critical or warning',
            enabled BOOLEAN NOT NULL COMMENT 'Whether rule is active',
            description STRING COMMENT 'Rule description',
            created_timestamp TIMESTAMP NOT NULL COMMENT 'When rule was created',
            updated_timestamp TIMESTAMP COMMENT 'When rule was last updated',
            CONSTRAINT pk_dq_rules PRIMARY KEY (table_name, rule_name) NOT ENFORCED
        )
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'entity_type' = 'configuration',
            'description' = 'Data quality rules for Bronze streaming tables'
        )
        COMMENT 'Configuration table for DLT data quality expectations'
    """)
    
    print(f"✓ dq_rules table created/verified: {table_name}")

def get_all_dq_rules():
    """
    Define all DQ rules for Bronze streaming tables.
    
    Comprehensive data quality rules for all 20 active Bronze streaming tables.
    
    Returns:
        list: List of rule dictionaries
    """
    return [
        # ========================================================================
        # ACCESS DOMAIN (5 tables)
        # ========================================================================
        
        # audit rules
        {
            "table_name": "audit",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Audit event time must be present"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_service_name",
            "rule_constraint": "service_name IS NOT NULL AND LENGTH(service_name) > 0",
            "severity": "critical",
            "description": "Service name must be present"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_action_name",
            "rule_constraint": "action_name IS NOT NULL AND LENGTH(action_name) > 0",
            "severity": "critical",
            "description": "Action name must be present"
        },
        
        # clean_room_events rules
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_central_clean_room_id",
            "rule_constraint": "central_clean_room_id IS NOT NULL AND LENGTH(central_clean_room_id) > 0",
            "severity": "critical",
            "description": "Central clean room ID must be present"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event time must be present"
        },
        
        # column_lineage rules
        {
            "table_name": "column_lineage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_source_table_full_name",
            "rule_constraint": "source_table_full_name IS NOT NULL AND LENGTH(source_table_full_name) > 0",
            "severity": "critical",
            "description": "Source table full name must be present"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_target_table_full_name",
            "rule_constraint": "target_table_full_name IS NOT NULL AND LENGTH(target_table_full_name) > 0",
            "severity": "critical",
            "description": "Target table full name must be present"
        },
        # Note: source_column_name and target_column_name are nullable (is_nullable=YES in CSV)
        # This is valid for table-level lineage operations, so no rules for these columns
        
        # outbound_network rules
        {
            "table_name": "outbound_network",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event time must be present (correct column name!)"
        },
        
        # table_lineage rules
        {
            "table_name": "table_lineage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_source_table_full_name",
            "rule_constraint": "source_table_full_name IS NOT NULL AND LENGTH(source_table_full_name) > 0",
            "severity": "critical",
            "description": "Source table full name must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_target_table_full_name",
            "rule_constraint": "target_table_full_name IS NOT NULL AND LENGTH(target_table_full_name) > 0",
            "severity": "critical",
            "description": "Target table full name must be present"
        },
        
        # ========================================================================
        # BILLING DOMAIN (1 table)
        # ========================================================================
        
        # usage rules
        {
            "table_name": "usage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL AND LENGTH(workspace_id) > 0",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_sku_name",
            "rule_constraint": "sku_name IS NOT NULL AND LENGTH(sku_name) > 0",
            "severity": "critical",
            "description": "SKU name must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_usage_start_time",
            "rule_constraint": "usage_start_time IS NOT NULL",
            "severity": "critical",
            "description": "Usage start time must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_usage_end_time",
            "rule_constraint": "usage_end_time IS NOT NULL",
            "severity": "critical",
            "description": "Usage end time must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_time_sequence",
            "rule_constraint": "usage_end_time >= usage_start_time",
            "severity": "critical",
            "description": "End time must be after or equal to start time"
        },
        {
            "table_name": "usage",
            "rule_name": "non_negative_usage_quantity",
            "rule_constraint": "usage_quantity >= 0",
            "severity": "critical",
            "description": "Usage quantity must be non-negative"
        },
        
        # ========================================================================
        # COMPUTE DOMAIN (4 tables)
        # ========================================================================
        
        # clusters rules
        {
            "table_name": "clusters",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "clusters",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "clusters",
            "rule_name": "valid_cluster_id",
            "rule_constraint": "cluster_id IS NOT NULL AND LENGTH(cluster_id) > 0",
            "severity": "critical",
            "description": "Cluster ID must be present"
        },
        {
            "table_name": "clusters",
            "rule_name": "valid_cluster_name",
            "rule_constraint": "cluster_name IS NOT NULL AND LENGTH(cluster_name) > 0",
            "severity": "critical",
            "description": "Cluster name must be present"
        },
        
        # node_timeline rules
        {
            "table_name": "node_timeline",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "node_timeline",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "node_timeline",
            "rule_name": "valid_cluster_id",
            "rule_constraint": "cluster_id IS NOT NULL AND LENGTH(cluster_id) > 0",
            "severity": "critical",
            "description": "Cluster ID must be present"
        },
        {
            "table_name": "node_timeline",
            "rule_name": "valid_instance_id",
            "rule_constraint": "instance_id IS NOT NULL AND LENGTH(instance_id) > 0",
            "severity": "critical",
            "description": "Instance ID must be present"
        },
        {
            "table_name": "node_timeline",
            "rule_name": "valid_start_time",
            "rule_constraint": "start_time IS NOT NULL",
            "severity": "critical",
            "description": "Start time must be present"
        },
        
        # warehouse_events rules
        {
            "table_name": "warehouse_events",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "warehouse_events",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "warehouse_events",
            "rule_name": "valid_warehouse_id",
            "rule_constraint": "warehouse_id IS NOT NULL AND LENGTH(warehouse_id) > 0",
            "severity": "critical",
            "description": "Warehouse ID must be present"
        },
        {
            "table_name": "warehouse_events",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event time must be present"
        },
        
        # warehouses rules
        {
            "table_name": "warehouses",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "warehouses",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "warehouses",
            "rule_name": "valid_warehouse_id",
            "rule_constraint": "warehouse_id IS NOT NULL AND LENGTH(warehouse_id) > 0",
            "severity": "critical",
            "description": "Warehouse ID must be present"
        },
        {
            "table_name": "warehouses",
            "rule_name": "valid_warehouse_name",
            "rule_constraint": "warehouse_name IS NOT NULL AND LENGTH(warehouse_name) > 0",
            "severity": "critical",
            "description": "Warehouse name must be present"
        },
        
        # ========================================================================
        # LAKEFLOW DOMAIN (5 tables - including disabled pipeline_update_timeline)
        # ========================================================================
        
        # job_run_timeline rules
        {
            "table_name": "job_run_timeline",
            "rule_name": "valid_job_id",
            "rule_constraint": "job_id IS NOT NULL AND LENGTH(job_id) > 0",
            "severity": "critical",
            "description": "Job ID must be present"
        },
        {
            "table_name": "job_run_timeline",
            "rule_name": "valid_run_id",
            "rule_constraint": "run_id IS NOT NULL AND LENGTH(run_id) > 0",
            "severity": "critical",
            "description": "Run ID must be present"
        },
        {
            "table_name": "job_run_timeline",
            "rule_name": "valid_period_start_time",
            "rule_constraint": "period_start_time IS NOT NULL",
            "severity": "critical",
            "description": "Period start time must be present"
        },
        
        # job_task_run_timeline rules
        {
            "table_name": "job_task_run_timeline",
            "rule_name": "valid_run_id",
            "rule_constraint": "run_id IS NOT NULL AND LENGTH(run_id) > 0",
            "severity": "critical",
            "description": "Run ID must be present"
        },
        {
            "table_name": "job_task_run_timeline",
            "rule_name": "valid_task_key",
            "rule_constraint": "task_key IS NOT NULL AND LENGTH(task_key) > 0",
            "severity": "critical",
            "description": "Task key must be present"
        },
        {
            "table_name": "job_task_run_timeline",
            "rule_name": "valid_period_start_time",
            "rule_constraint": "period_start_time IS NOT NULL",
            "severity": "critical",
            "description": "Period start time must be present"
        },
        
        # job_tasks rules
        {
            "table_name": "job_tasks",
            "rule_name": "valid_job_id",
            "rule_constraint": "job_id IS NOT NULL AND LENGTH(job_id) > 0",
            "severity": "critical",
            "description": "Job ID must be present"
        },
        {
            "table_name": "job_tasks",
            "rule_name": "valid_task_key",
            "rule_constraint": "task_key IS NOT NULL AND LENGTH(task_key) > 0",
            "severity": "critical",
            "description": "Task key must be present"
        },
        
        # jobs rules
        {
            "table_name": "jobs",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "jobs",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "jobs",
            "rule_name": "valid_job_id",
            "rule_constraint": "job_id IS NOT NULL AND LENGTH(job_id) > 0",
            "severity": "critical",
            "description": "Job ID must be present"
        },
        {
            "table_name": "jobs",
            "rule_name": "valid_job_name",
            "rule_constraint": "name IS NOT NULL AND LENGTH(name) > 0",
            "severity": "critical",
            "description": "Job name must be present"
        },
        
        # pipelines rules
        {
            "table_name": "pipelines",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "pipelines",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "pipelines",
            "rule_name": "valid_pipeline_id",
            "rule_constraint": "pipeline_id IS NOT NULL AND LENGTH(pipeline_id) > 0",
            "severity": "critical",
            "description": "Pipeline ID must be present"
        },
        {
            "table_name": "pipelines",
            "rule_name": "valid_name",
            "rule_constraint": "name IS NOT NULL AND LENGTH(name) > 0",
            "severity": "critical",
            "description": "Pipeline name must be present"
        },
        
        # pipeline_update_timeline rules (DISABLED due to Deletion Vectors)
        {
            "table_name": "pipeline_update_timeline",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present and non-empty"
        },
        {
            "table_name": "pipeline_update_timeline",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL AND LENGTH(workspace_id) > 0",
            "severity": "critical",
            "description": "Workspace ID must be present and non-empty"
        },
        {
            "table_name": "pipeline_update_timeline",
            "rule_name": "valid_pipeline_id",
            "rule_constraint": "pipeline_id IS NOT NULL AND LENGTH(pipeline_id) > 0",
            "severity": "critical",
            "description": "Pipeline ID must be present and non-empty"
        },
        {
            "table_name": "pipeline_update_timeline",
            "rule_name": "valid_update_id",
            "rule_constraint": "update_id IS NOT NULL AND LENGTH(update_id) > 0",
            "severity": "critical",
            "description": "Update ID must be present and non-empty"
        },
        
        # ========================================================================
        # MARKETPLACE DOMAIN (2 tables)
        # ========================================================================
        
        # listing_funnel_events rules
        {
            "table_name": "listing_funnel_events",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "listing_funnel_events",
            "rule_name": "valid_listing_id",
            "rule_constraint": "listing_id IS NOT NULL AND LENGTH(listing_id) > 0",
            "severity": "critical",
            "description": "Listing ID must be present"
        },
        {
            "table_name": "listing_funnel_events",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event time must be present"
        },
        
        # listing_access_events rules
        {
            "table_name": "listing_access_events",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "listing_access_events",
            "rule_name": "valid_listing_id",
            "rule_constraint": "listing_id IS NOT NULL AND LENGTH(listing_id) > 0",
            "severity": "critical",
            "description": "Listing ID must be present"
        },
        {
            "table_name": "listing_access_events",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event time must be present"
        },
        
        # ========================================================================
        # MLFLOW DOMAIN (3 tables)
        # ========================================================================
        
        # experiments_latest rules
        {
            "table_name": "experiments_latest",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "experiments_latest",
            "rule_name": "valid_experiment_id",
            "rule_constraint": "experiment_id IS NOT NULL AND LENGTH(experiment_id) > 0",
            "severity": "critical",
            "description": "Experiment ID must be present"
        },
        {
            "table_name": "experiments_latest",
            "rule_name": "valid_experiment_name",
            "rule_constraint": "experiment_name IS NOT NULL AND LENGTH(experiment_name) > 0",
            "severity": "critical",
            "description": "Experiment name must be present"
        },
        
        # runs_latest rules
        {
            "table_name": "runs_latest",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "runs_latest",
            "rule_name": "valid_run_id",
            "rule_constraint": "run_id IS NOT NULL AND LENGTH(run_id) > 0",
            "severity": "critical",
            "description": "Run ID must be present"
        },
        {
            "table_name": "runs_latest",
            "rule_name": "valid_experiment_id",
            "rule_constraint": "experiment_id IS NOT NULL AND LENGTH(experiment_id) > 0",
            "severity": "critical",
            "description": "Experiment ID must be present"
        },
        
        # run_metrics_history rules
        {
            "table_name": "run_metrics_history",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "run_metrics_history",
            "rule_name": "valid_run_id",
            "rule_constraint": "run_id IS NOT NULL AND LENGTH(run_id) > 0",
            "severity": "critical",
            "description": "Run ID must be present"
        },
        {
            "table_name": "run_metrics_history",
            "rule_name": "valid_key",
            "rule_constraint": "key IS NOT NULL AND LENGTH(key) > 0",
            "severity": "critical",
            "description": "Metric key must be present"
        },
        {
            "table_name": "run_metrics_history",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp must be present"
        },
        
        # ========================================================================
        # SERVING DOMAIN (2 tables)
        # ========================================================================
        
        # served_entities rules
        {
            "table_name": "served_entities",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "served_entities",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "served_entities",
            "rule_name": "valid_endpoint_name",
            "rule_constraint": "endpoint_name IS NOT NULL AND LENGTH(endpoint_name) > 0",
            "severity": "critical",
            "description": "Endpoint name must be present"
        },
        {
            "table_name": "served_entities",
            "rule_name": "valid_entity_name",
            "rule_constraint": "entity_name IS NOT NULL AND LENGTH(entity_name) > 0",
            "severity": "critical",
            "description": "Entity name must be present"
        },
        
        # endpoint_usage rules
        {
            "table_name": "endpoint_usage",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "endpoint_usage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "endpoint_usage",
            "rule_name": "valid_endpoint_name",
            "rule_constraint": "endpoint_name IS NOT NULL AND LENGTH(endpoint_name) > 0",
            "severity": "critical",
            "description": "Endpoint name must be present"
        },
        {
            "table_name": "endpoint_usage",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp must be present"
        },
    ]

def populate_dq_rules(spark: SparkSession, catalog: str, schema: str):
    """Populate dq_rules table with comprehensive rules."""
    
    table_name = f"{catalog}.{schema}.dq_rules"
    
    print(f"\nPopulating DQ rules into: {table_name}")
    
    rules = get_all_dq_rules()
    print(f"  Generated {len(rules)} rules from get_all_dq_rules()")
    
    # Verify we have rules
    if len(rules) == 0:
        raise ValueError("No rules returned from get_all_dq_rules()!")
    
    # Add timestamps to all rules
    now = datetime.now()
    for rule in rules:
        rule['enabled'] = True
        rule['created_timestamp'] = now
        rule['updated_timestamp'] = now
    
    # Create DataFrame with explicit schema
    print(f"  Creating DataFrame from {len(rules)} rules...")
    try:
        rules_df = spark.createDataFrame(rules)
        print(f"  DataFrame created with {rules_df.count()} rows")
    except Exception as e:
        print(f"  ❌ Error creating DataFrame: {str(e)}")
        print(f"  Sample rule: {rules[0]}")
        raise
    
    # Insert rules (table was just created, so overwrite is safe)
    print(f"  Inserting {len(rules)} rules into {table_name}...")
    try:
        rules_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
        print(f"✓ Successfully inserted {len(rules)} DQ rules")
    except Exception as e:
        print(f"  ❌ Error writing to table: {str(e)}")
        raise
    
    # Verify insertion
    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['cnt']
    print(f"✓ Verified: {count} rules in table")
    
    if count == 0:
        raise ValueError(f"Table {table_name} is empty after insertion!")
    
    # Show summary
    print(f"\n📊 Rules by table:")
    spark.sql(f"""
        SELECT table_name, COUNT(*) as rule_count
        FROM {table_name}
        WHERE enabled = true
        GROUP BY table_name
        ORDER BY table_name
    """).show(100, truncate=False)
    
    # Show tables covered
    print(f"\n📋 Tables with DQ rules:")
    tables = spark.sql(f"""
        SELECT DISTINCT table_name 
        FROM {table_name} 
        WHERE enabled = true
        ORDER BY table_name
    """).collect()
    for row in tables:
        print(f"  • {row['table_name']}")

def main():
    """Main entry point."""
    
    catalog, bronze_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Setup DQ Rules").getOrCreate()
    
    try:
        print("=" * 80)
        print("🔧 Setting up DQ Rules Table")
        print("=" * 80)
        
        # Create table
        create_dq_rules_table(spark, catalog, bronze_schema)
        
        # Populate rules
        populate_dq_rules(spark, catalog, bronze_schema)
        
        print("\n" + "=" * 80)
        print("✅ DQ Rules setup completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during DQ rules setup: {str(e)}")
        raise
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main()

