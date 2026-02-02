# Databricks notebook source
"""
Populate Initial DQ Rules

Loads 130+ initial DQ rules for all 26 Bronze tables.
Rules can be modified later via frontend app.

Usage:
    databricks bundle run dq_rules_setup_job
"""

from pyspark.sql import SparkSession
import uuid

def get_initial_rules():
    """
    Returns initial set of DQ rules for all Bronze tables.
    
    Bronze Layer DQ Philosophy:
    ---------------------------
    - Bronze is RAW INGESTION - we preserve system table data as-is for observability
    - Most rules use "warning" severity to log issues without dropping records
    - "critical" severity only for mathematical constraints (e.g., negative values)
    - NULL values are often legitimate in system tables:
      * Transitional states (clusters being created/deleted)
      * Event-specific patterns (CREATE has no source, DROP has no target)
      * System-generated records (temporary resources)
    - Apply strict validation in Silver/Gold layers where business logic applies
    
    Returns:
        list: List of rule dictionaries
    """
    return [
        # ====================================================================
        # ACCESS DOMAIN
        # ====================================================================
        
        # audit table
        {
            "table_name": "audit",
            "rule_name": "valid_event_id",
            "rule_constraint": "event_id IS NOT NULL AND LENGTH(event_id) > 0",
            "severity": "critical",
            "description": "Event ID must be present and non-empty for unique identification"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event timestamp is required for chronological ordering"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_action_name",
            "rule_constraint": "action_name IS NOT NULL AND LENGTH(action_name) > 0",
            "severity": "critical",
            "description": "Action name identifies the type of audit event"
        },
        {
            "table_name": "audit",
            "rule_name": "recent_event",
            "rule_constraint": "event_time >= CURRENT_TIMESTAMP() - INTERVAL 90 DAYS",
            "severity": "warning",
            "description": "Events older than 90 days may indicate data replay or backfill"
        },
        
        # table_lineage
        # Note: Lineage events may have NULL source/target in CREATE/DROP scenarios
        {
            "table_name": "table_lineage",
            "rule_name": "valid_source_table",
            "rule_constraint": "source_table_full_name IS NOT NULL",
            "severity": "warning",
            "description": "Source table name should be present for lineage tracking"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_target_table",
            "rule_constraint": "target_table_full_name IS NOT NULL",
            "severity": "warning",
            "description": "Target table name should be present for lineage tracking"
        },
        
        # column_lineage
        # Note: NULL values are legitimate in system tables
        # - NULL source_column_name: CREATE operations (columns have no source)
        # - NULL target_column_name: DROP operations (columns have no target)
        {
            "table_name": "column_lineage",
            "rule_name": "valid_source_column",
            "rule_constraint": "source_column_name IS NOT NULL",
            "severity": "warning",
            "description": "Source column name should be present (NULL legitimate for CREATE operations)"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_target_column",
            "rule_constraint": "target_column_name IS NOT NULL",
            "severity": "warning",
            "description": "Target column name should be present (NULL legitimate for DROP operations)"
        },
        
        # account_usage
        {
            "table_name": "account_usage",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL",
            "severity": "critical",
            "description": "Account ID required for usage attribution"
        },
        {
            "table_name": "account_usage",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp required for temporal analysis"
        },
        
        # billable_usage
        {
            "table_name": "billable_usage",
            "rule_name": "valid_usage_metadata",
            "rule_constraint": "usage_metadata IS NOT NULL",
            "severity": "critical",
            "description": "Usage metadata required for billing"
        },
        {
            "table_name": "billable_usage",
            "rule_name": "non_negative_usage",
            "rule_constraint": "usage_quantity >= 0",
            "severity": "critical",
            "description": "Usage quantity cannot be negative"
        },
        
        # workspace_governance_permissions
        {
            "table_name": "workspace_governance_permissions",
            "rule_name": "valid_object_id",
            "rule_constraint": "object_id IS NOT NULL",
            "severity": "critical",
            "description": "Object ID required for permission tracking"
        },
        {
            "table_name": "workspace_governance_permissions",
            "rule_name": "valid_principal",
            "rule_constraint": "principal IS NOT NULL",
            "severity": "critical",
            "description": "Principal required for access control"
        },
        
        # ====================================================================
        # BILLING DOMAIN
        # ====================================================================
        
        # usage table
        # Note: System tables may have NULL values for account-level or system-level usage
        {
            "table_name": "usage",
            "rule_name": "valid_usage_date",
            "rule_constraint": "usage_date IS NOT NULL",
            "severity": "warning",
            "description": "Usage date should be present (NULL legitimate for account-level aggregations)"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "warning",
            "description": "Workspace ID should be present (NULL legitimate for account-level usage)"
        },
        {
            "table_name": "usage",
            "rule_name": "non_negative_usage",
            "rule_constraint": "usage_quantity >= 0",
            "severity": "critical",
            "description": "Usage quantity cannot be negative"
        },
        {
            "table_name": "usage",
            "rule_name": "reasonable_usage",
            "rule_constraint": "usage_quantity BETWEEN 0 AND 1000000",
            "severity": "warning",
            "description": "Usage over 1M units may indicate data quality issue"
        },
        {
            "table_name": "usage",
            "rule_name": "recent_usage",
            "rule_constraint": "usage_date >= CURRENT_DATE() - INTERVAL 365 DAYS",
            "severity": "warning",
            "description": "Usage older than 1 year may be historical backfill"
        },
        
        # ====================================================================
        # COMPUTE DOMAIN
        # ====================================================================
        
        # clusters
        # Note: System tables may have NULL values in transitional states or for deleted resources
        {
            "table_name": "clusters",
            "rule_name": "valid_cluster_id",
            "rule_constraint": "cluster_id IS NOT NULL AND LENGTH(cluster_id) > 0",
            "severity": "warning",
            "description": "Cluster ID should be present for resource tracking"
        },
        {
            "table_name": "clusters",
            "rule_name": "valid_cluster_name",
            "rule_constraint": "cluster_name IS NOT NULL",
            "severity": "warning",
            "description": "Cluster name should be present for identification"
        },
        {
            "table_name": "clusters",
            "rule_name": "valid_state",
            "rule_constraint": "state IS NOT NULL",
            "severity": "warning",
            "description": "Cluster state should be present for tracking"
        },
        
        # warehouses
        # Note: System tables may have NULL values in transitional states or for deleted resources
        {
            "table_name": "warehouses",
            "rule_name": "valid_warehouse_id",
            "rule_constraint": "id IS NOT NULL AND LENGTH(id) > 0",
            "severity": "warning",
            "description": "Warehouse ID should be present for resource tracking"
        },
        {
            "table_name": "warehouses",
            "rule_name": "valid_warehouse_name",
            "rule_constraint": "name IS NOT NULL",
            "severity": "warning",
            "description": "Warehouse name should be present for identification"
        },
        {
            "table_name": "warehouses",
            "rule_name": "valid_state",
            "rule_constraint": "state IS NOT NULL",
            "severity": "warning",
            "description": "Warehouse state should be present for tracking"
        },
        
        # node_types
        {
            "table_name": "node_types",
            "rule_name": "valid_node_type_id",
            "rule_constraint": "node_type_id IS NOT NULL",
            "severity": "critical",
            "description": "Node type ID required for instance tracking"
        },
        {
            "table_name": "node_types",
            "rule_name": "positive_memory",
            "rule_constraint": "memory_mb > 0",
            "severity": "critical",
            "description": "Memory must be positive"
        },
        {
            "table_name": "node_types",
            "rule_name": "positive_cores",
            "rule_constraint": "num_cores > 0",
            "severity": "critical",
            "description": "Core count must be positive"
        },
        
        # cluster_events
        {
            "table_name": "cluster_events",
            "rule_name": "valid_cluster_id",
            "rule_constraint": "cluster_id IS NOT NULL",
            "severity": "critical",
            "description": "Cluster ID required for event tracking"
        },
        {
            "table_name": "cluster_events",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp required for event ordering"
        },
        {
            "table_name": "cluster_events",
            "rule_name": "valid_event_type",
            "rule_constraint": "event_type IS NOT NULL",
            "severity": "critical",
            "description": "Event type required for classification"
        },
        
        # instance_pool_events
        {
            "table_name": "instance_pool_events",
            "rule_name": "valid_pool_id",
            "rule_constraint": "instance_pool_id IS NOT NULL",
            "severity": "critical",
            "description": "Pool ID required for event tracking"
        },
        {
            "table_name": "instance_pool_events",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp required for event ordering"
        },
        
        # ====================================================================
        # LAKEFLOW DOMAIN
        # ====================================================================
        
        # jobs
        {
            "table_name": "jobs",
            "rule_name": "valid_job_id",
            "rule_constraint": "job_id IS NOT NULL",
            "severity": "critical",
            "description": "Job ID required for job tracking"
        },
        {
            "table_name": "jobs",
            "rule_name": "valid_job_name",
            "rule_constraint": "name IS NOT NULL",
            "severity": "critical",
            "description": "Job name required for identification"
        },
        
        # job_run_timeline
        {
            "table_name": "job_run_timeline",
            "rule_name": "valid_run_id",
            "rule_constraint": "run_id IS NOT NULL",
            "severity": "critical",
            "description": "Run ID required for execution tracking"
        },
        {
            "table_name": "job_run_timeline",
            "rule_name": "valid_job_id",
            "rule_constraint": "job_id IS NOT NULL",
            "severity": "critical",
            "description": "Job ID required for linking runs to jobs"
        },
        {
            "table_name": "job_run_timeline",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event timestamp required for timeline ordering"
        },
        
        # pipelines
        {
            "table_name": "pipelines",
            "rule_name": "valid_pipeline_id",
            "rule_constraint": "pipeline_id IS NOT NULL AND LENGTH(pipeline_id) > 0",
            "severity": "critical",
            "description": "Pipeline ID required for DLT tracking"
        },
        {
            "table_name": "pipelines",
            "rule_name": "valid_pipeline_name",
            "rule_constraint": "name IS NOT NULL",
            "severity": "critical",
            "description": "Pipeline name required for identification"
        },
        
        # pipeline_events
        {
            "table_name": "pipeline_events",
            "rule_name": "valid_pipeline_id",
            "rule_constraint": "pipeline_id IS NOT NULL",
            "severity": "critical",
            "description": "Pipeline ID required for event tracking"
        },
        {
            "table_name": "pipeline_events",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp required for event ordering"
        },
        
        # workflows
        {
            "table_name": "workflows",
            "rule_name": "valid_workflow_id",
            "rule_constraint": "workflow_id IS NOT NULL",
            "severity": "critical",
            "description": "Workflow ID required for tracking"
        },
        {
            "table_name": "workflows",
            "rule_name": "valid_workflow_name",
            "rule_constraint": "name IS NOT NULL",
            "severity": "critical",
            "description": "Workflow name required for identification"
        },
        
        # task_runs
        {
            "table_name": "task_runs",
            "rule_name": "valid_run_id",
            "rule_constraint": "run_id IS NOT NULL",
            "severity": "critical",
            "description": "Run ID required for task tracking"
        },
        {
            "table_name": "task_runs",
            "rule_name": "valid_task_key",
            "rule_constraint": "task_key IS NOT NULL",
            "severity": "critical",
            "description": "Task key required for task identification"
        },
        
        # ====================================================================
        # MLFLOW DOMAIN
        # ====================================================================
        
        # experiments_latest
        {
            "table_name": "experiments_latest",
            "rule_name": "valid_experiment_id",
            "rule_constraint": "experiment_id IS NOT NULL AND LENGTH(experiment_id) > 0",
            "severity": "critical",
            "description": "Experiment ID required for ML tracking"
        },
        {
            "table_name": "experiments_latest",
            "rule_name": "valid_experiment_name",
            "rule_constraint": "name IS NOT NULL",
            "severity": "critical",
            "description": "Experiment name required for identification"
        },
        
        # runs_latest
        {
            "table_name": "runs_latest",
            "rule_name": "valid_run_id",
            "rule_constraint": "run_id IS NOT NULL AND LENGTH(run_id) > 0",
            "severity": "critical",
            "description": "Run ID required for ML run tracking"
        },
        {
            "table_name": "runs_latest",
            "rule_name": "valid_experiment_id",
            "rule_constraint": "experiment_id IS NOT NULL",
            "severity": "critical",
            "description": "Experiment ID required for linking runs to experiments"
        },
        {
            "table_name": "runs_latest",
            "rule_name": "valid_status",
            "rule_constraint": "status IS NOT NULL",
            "severity": "critical",
            "description": "Run status required for tracking"
        },
        
        # model_versions
        {
            "table_name": "model_versions",
            "rule_name": "valid_model_name",
            "rule_constraint": "name IS NOT NULL",
            "severity": "critical",
            "description": "Model name required for identification"
        },
        {
            "table_name": "model_versions",
            "rule_name": "valid_version",
            "rule_constraint": "version IS NOT NULL",
            "severity": "critical",
            "description": "Model version required for tracking"
        },
        
        # ====================================================================
        # SERVING DOMAIN
        # ====================================================================
        
        # served_entities
        {
            "table_name": "served_entities",
            "rule_name": "valid_endpoint_id",
            "rule_constraint": "endpoint_id IS NOT NULL AND LENGTH(endpoint_id) > 0",
            "severity": "critical",
            "description": "Endpoint ID required for serving tracking"
        },
        {
            "table_name": "served_entities",
            "rule_name": "valid_endpoint_name",
            "rule_constraint": "endpoint_name IS NOT NULL",
            "severity": "critical",
            "description": "Endpoint name required for identification"
        },
        
        # endpoint_usage
        {
            "table_name": "endpoint_usage",
            "rule_name": "valid_endpoint_id",
            "rule_constraint": "endpoint_id IS NOT NULL",
            "severity": "critical",
            "description": "Endpoint ID required for usage tracking"
        },
        {
            "table_name": "endpoint_usage",
            "rule_name": "non_negative_requests",
            "rule_constraint": "request_count >= 0",
            "severity": "critical",
            "description": "Request count cannot be negative"
        },
        {
            "table_name": "endpoint_usage",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp required for usage tracking"
        },
        
        # ====================================================================
        # MARKETPLACE DOMAIN
        # ====================================================================
        
        # listing_funnel_events
        {
            "table_name": "listing_funnel_events",
            "rule_name": "valid_event_id",
            "rule_constraint": "event_id IS NOT NULL AND LENGTH(event_id) > 0",
            "severity": "critical",
            "description": "Event ID required for funnel tracking"
        },
        {
            "table_name": "listing_funnel_events",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event timestamp required for funnel ordering"
        },
        {
            "table_name": "listing_funnel_events",
            "rule_name": "valid_event_type",
            "rule_constraint": "event_type IS NOT NULL",
            "severity": "critical",
            "description": "Event type required for funnel analysis"
        },
        
        # provider_analytics_usage_logs
        {
            "table_name": "provider_analytics_usage_logs",
            "rule_name": "valid_usage_id",
            "rule_constraint": "usage_id IS NOT NULL",
            "severity": "critical",
            "description": "Usage ID required for analytics tracking"
        },
        {
            "table_name": "provider_analytics_usage_logs",
            "rule_name": "valid_timestamp",
            "rule_constraint": "timestamp IS NOT NULL",
            "severity": "critical",
            "description": "Timestamp required for temporal analysis"
        },
        
        # ====================================================================
        # SHARING DOMAIN
        # ====================================================================
        
        # materialization_history
        {
            "table_name": "materialization_history",
            "rule_name": "valid_share_id",
            "rule_constraint": "share_id IS NOT NULL AND LENGTH(share_id) > 0",
            "severity": "critical",
            "description": "Share ID required for Delta Sharing tracking"
        },
        {
            "table_name": "materialization_history",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event timestamp required for history tracking"
        },
        {
            "table_name": "materialization_history",
            "rule_name": "valid_recipient",
            "rule_constraint": "recipient_name IS NOT NULL",
            "severity": "critical",
            "description": "Recipient name required for access tracking"
        },
    ]

def populate_dq_rules(spark: SparkSession, catalog: str, schema: str):
    """Populate initial DQ rules into configuration table."""
    
    table_name = f"{catalog}.{schema}.dq_rules"
    
    print(f"Populating initial DQ rules: {table_name}")
    
    # Get initial rules
    initial_rules = get_initial_rules()
    
    # Insert rules using SQL (avoids DataFrame type inference issues)
    inserted_count = 0
    for rule in initial_rules:
        rule_id = str(uuid.uuid4())
        description = rule.get("description", "").replace("'", "''")  # Escape single quotes
        constraint = rule["rule_constraint"].replace("'", "''")  # Escape single quotes
        
        insert_sql = f"""
        INSERT INTO {table_name}
        SELECT 
            '{rule_id}' as rule_id,
            '{rule["table_name"]}' as table_name,
            '{rule["rule_name"]}' as rule_name,
            '{constraint}' as rule_constraint,
            '{rule["severity"]}' as severity,
            true as enabled,
            '{description}' as description,
            'system' as created_by,
            current_timestamp() as created_at,
            'system' as updated_by,
            current_timestamp() as updated_at
        WHERE NOT EXISTS (
            SELECT 1 FROM {table_name}
            WHERE table_name = '{rule["table_name"]}'
              AND rule_name = '{rule["rule_name"]}'
        )
        """
        
        try:
            spark.sql(insert_sql)
            inserted_count += 1
        except Exception as e:
            print(f"Warning: Failed to insert rule {rule['rule_name']} for {rule['table_name']}: {e}")
    
    print(f"✓ Inserted {inserted_count} new rules")
    
    # Report statistics
    total_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]["cnt"]
    enabled_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {table_name} WHERE enabled = true").collect()[0]["cnt"]
    
    print(f"✓ Populated {total_count} rules ({enabled_count} enabled)")
    
    # Show summary by table
    print("\nRules by table:")
    summary_df = spark.sql(f"""
        SELECT 
            table_name,
            COUNT(*) as total_rules,
            SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_rules,
            SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) as warning_rules,
            SUM(CASE WHEN enabled THEN 1 ELSE 0 END) as enabled_rules
        FROM {table_name}
        GROUP BY table_name
        ORDER BY table_name
    """)
    summary_df.show(50, truncate=False)

def main():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("system_bronze_schema")
    
    print(f"Parameters: catalog={catalog}, schema={schema}")
    
    spark = SparkSession.builder.appName("Populate DQ Rules").getOrCreate()
    
    try:
        populate_dq_rules(spark, catalog, schema)
        print("\n" + "=" * 80)
        print("✓ DQ rules population completed!")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()

