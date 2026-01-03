# Databricks notebook source
"""
Genie Spaces Deployment Script
==============================

Deploys and configures Databricks Genie Spaces for the Health Monitor project.
Creates 6 Genie Spaces - ONE per Agent Domain to prevent Genie sprawl.

Agent Domains (1 Space Each):
- 💰 Cost: Cost Intelligence Space
- 🔄 Reliability: Job Health Monitor Space
- ⚡ Performance: Performance Space (Query + Cluster combined)
- 🔒 Security: Security Auditor Space
- ✅ Quality: Data Quality Monitor Space
- 🌐 Unified: Databricks Health Monitor Space (Leadership overview)

SEMANTIC LAYER FRAMEWORK
========================
Each Genie Space uses a 3-layer semantic framework:
1. Metric Views (mv_*) - Dashboard KPIs, current state aggregates
2. TVFs (get_*) - Parameterized drill-down, lists, investigations
3. Custom Metrics (_profile_metrics, _drift_metrics) - Time series, drift detection

Asset Selection Priority:
- LIST queries → TVF
- TREND queries → Custom Metrics
- CURRENT VALUE queries → Metric View
- PREDICTION queries → ML Tables (25 models across all domains)
- ANOMALY queries → ML Tables (cost, security, quality anomaly detectors)
- RECOMMENDATION queries → ML Tables (optimizer, recommender models)
- RISK SCORE queries → ML Tables (user_risk_scores, health_scores)

ML Model Integration (25 Models by Domain):
- 💰 Cost (6): cost_anomaly_detector, budget_forecaster, job_cost_optimizer, 
              tag_recommender, commitment_recommender, chargeback_attribution
- 🔄 Reliability (5): job_failure_predictor, job_duration_forecaster, 
                      sla_breach_predictor, pipeline_health_scorer, retry_success_predictor
- ⚡ Performance (7): query_performance_forecaster, warehouse_optimizer, cache_hit_predictor,
                     query_optimization_recommender, cluster_sizing_recommender, 
                     cluster_capacity_planner, regression_detector
- 🔒 Security (4): security_threat_detector, access_pattern_analyzer, 
                   compliance_risk_classifier, permission_recommender
- 📋 Quality (3): data_drift_detector, schema_change_predictor, schema_evolution_predictor

CRITICAL: Lakehouse Monitoring Custom Metrics Query Patterns
============================================================
When querying _profile_metrics or _drift_metrics tables, ALWAYS include:

  -- For profile_metrics:
  WHERE column_name = ':table'     -- REQUIRED: Table-level custom metrics
    AND log_type = 'INPUT'         -- REQUIRED: Input data statistics
    AND slice_key IS NULL          -- For overall (or specify for dimensional)

  -- For drift_metrics:
  WHERE drift_type = 'CONSECUTIVE' -- REQUIRED: Period-over-period
    AND column_name = ':table'     -- REQUIRED: Table-level drift

References:
- docs/reference/metrics-inventory.md - Complete unified metrics inventory
- docs/reference/semantic-layer-rationalization.md - Design rationale
- docs/reference/genie-asset-selection-guide.md - Asset selection decision tree
- docs/lakehouse-monitoring-design/05-genie-integration.md - Query patterns
"""

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
warehouse_id = dbutils.widgets.get("warehouse_id")

print(f"Catalog: {catalog}")
print(f"Gold Schema: {gold_schema}")
print(f"Warehouse ID: {warehouse_id}")

# COMMAND ----------

# Genie Space Configurations
# Note: Genie Spaces are created via UI or API
# This script documents the configuration for each space

GENIE_SPACES = {
    "cost_intelligence": {
        "name": "Health Monitor Cost Intelligence Space",
        "domain": "💰 Cost",
        "description": """Natural language interface for Databricks cost analytics and FinOps. 
Enables finance teams, platform administrators, and executives to query billing, usage, 
and cost optimization insights without SQL. Powered by Cost Analytics Metric Views, 
15 Table-Valued Functions, 6 ML Models, and Lakehouse Monitoring custom metrics.""",
        "metric_views": ["cost_analytics", "commit_tracking"],
        "tvfs": [
            "get_top_cost_contributors",
            "get_cost_trend_by_sku",
            "get_cost_by_owner",
            "get_cost_by_tag",
            "get_untagged_resources",
            "get_tag_coverage",
            "get_cost_week_over_week",
            "get_cost_anomalies",
            "get_cost_forecast_summary",
            "get_cost_mtd_summary",
            "get_commit_vs_actual",
            "get_spend_by_custom_tags",
            "get_cost_growth_analysis",
            "get_cost_growth_by_period",
            "get_all_purpose_cluster_cost",
        ],
        "ml_tables": [
            "cost_anomaly_predictions",
            "cost_forecast_predictions",
            "tag_recommendations",
            "user_cost_segments",
            "migration_recommendations",
            "budget_alert_predictions",
        ],
        "ml_model_mapping": {
            # Question pattern → ML prediction table
            "unusual|anomaly|spike|abnormal": "cost_anomaly_predictions",
            "forecast|predict|next month|project": "cost_forecast_predictions",
            "recommend tags|suggest tags|auto-tag": "tag_recommendations",
            "save|reduce cost|optimize": "migration_recommendations",
            "budget|commit level": "budget_alert_predictions",
        },
        "monitoring_tables": [
            "fact_usage_profile_metrics",
            "fact_usage_drift_metrics",
        ],
        "slicing_dimensions": [
            "workspace_id", "sku_name", "cloud", "is_tagged", "product_features_is_serverless"
        ],
        "gold_tables": [
            "fact_usage",          # billing/fact_usage.yaml
            "fact_account_prices", # billing/fact_account_prices.yaml
            "fact_list_prices",    # billing/fact_list_prices.yaml
            "dim_sku",             # billing/dim_sku.yaml
            "dim_workspace",       # shared/dim_workspace.yaml
        ],
    },
    "job_health": {
        "name": "Health Monitor Job Reliability Space",
        "domain": "🔄 Reliability",
        "description": """Natural language interface for Databricks job reliability and execution analytics. 
Enables DevOps, data engineers, and SREs to query job success rates, failure patterns, 
and performance metrics without SQL.""",
        "metric_views": ["job_performance"],
        "tvfs": [
            "get_failed_jobs",
            "get_job_success_rate",
            "get_job_duration_percentiles",
            "get_job_failure_trends",
            "get_job_sla_compliance",
            "get_job_run_details",
            "get_most_expensive_jobs",
            "get_job_retry_analysis",
            "get_job_repair_costs",
            "get_job_spend_trend_analysis",
            "get_job_failure_costs",
            "get_job_run_duration_analysis",
        ],
        "ml_tables": [
            "job_failure_predictions",
            "retry_success_predictions",
            "pipeline_health_scores",
            "incident_impact_predictions",
            "self_healing_recommendations",
        ],
        "ml_model_mapping": {
            # Question pattern → ML prediction table
            "will fail|likely to fail|at risk|failure prediction": "job_failure_predictions",
            "retry succeed|recovery|will retry work": "retry_success_predictions",
            "pipeline health|health score|pipeline status": "pipeline_health_scores",
            "SLA breach|breach|impact": "incident_impact_predictions",
            "how long|duration estimate|expected time": "job_duration_predictions",
        },
        "monitoring_tables": [
            "fact_job_run_timeline_profile_metrics",
            "fact_job_run_timeline_drift_metrics",
        ],
        "slicing_dimensions": [
            "workspace_id", "job_name", "result_state", "trigger_type", "termination_code"
        ],
        "gold_tables": [
            "fact_job_run_timeline",      # lakeflow/fact_job_run_timeline.yaml
            "fact_job_task_run_timeline", # lakeflow/fact_job_task_run_timeline.yaml
            "fact_pipeline_update_timeline", # lakeflow/fact_pipeline_update_timeline.yaml
            "dim_job",                    # lakeflow/dim_job.yaml
            "dim_job_task",               # lakeflow/dim_job_task.yaml
            "dim_pipeline",               # lakeflow/dim_pipeline.yaml
            "dim_workspace",              # shared/dim_workspace.yaml
        ],
    },
    "performance": {
        "name": "Health Monitor Performance Space",
        "domain": "⚡ Performance",
        "description": """Natural language interface for Databricks query and cluster performance analytics. 
Enables DBAs, platform engineers, and FinOps to query execution metrics, warehouse utilization, 
cluster efficiency, and right-sizing opportunities without SQL. Combined Query + Cluster analytics.""",
        "metric_views": ["query_performance", "cluster_utilization", "cluster_efficiency"],
        "tvfs": [
            # Query TVFs
            "get_slow_queries",
            "get_warehouse_utilization",
            "get_query_efficiency",
            "get_high_spill_queries",
            "get_query_volume_trends",
            "get_user_query_summary",
            "get_query_latency_percentiles",
            "get_failed_queries",
            "get_query_efficiency_analysis",
            "get_job_outlier_runs",
            # Cluster TVFs
            "get_cluster_utilization",
            "get_cluster_resource_metrics",
            "get_underutilized_clusters",
            "get_jobs_without_autoscaling",
            "get_jobs_on_legacy_dbr",
            "get_cluster_right_sizing_recommendations",
        ],
        "ml_tables": [
            # Query ML
            "query_optimization_classifications",
            "query_optimization_recommendations",
            "cache_hit_predictions",
            "job_duration_predictions",
            # Cluster ML
            "cluster_capacity_recommendations",
            "cluster_rightsizing_recommendations",
            "dbr_migration_risk_scores",
        ],
        "ml_model_mapping": {
            # Question pattern → ML prediction table
            "optimize query|improve query|tune query": "query_optimization_recommendations",
            "cache|cache hit|caching": "cache_hit_predictions",
            "right-size|optimize cluster|savings|too big|too small": "cluster_rightsizing_recommendations",
            "capacity|scale|planning": "cluster_capacity_recommendations",
            "migration risk|DBR upgrade": "dbr_migration_risk_scores",
        },
        "monitoring_tables": [
            "fact_query_history_profile_metrics",
            "fact_query_history_drift_metrics",
            "fact_node_timeline_profile_metrics",
            "fact_node_timeline_drift_metrics",
        ],
        "slicing_dimensions": {
            "query": ["workspace_id", "compute_warehouse_id", "execution_status", "statement_type", "executed_by"],
            "cluster": ["workspace_id", "cluster_id", "node_type", "cluster_name", "driver"]
        },
        "gold_tables": [
            # Query Performance (query_performance/)
            "fact_query_history",   # query_performance/fact_query_history.yaml
            "fact_warehouse_events", # query_performance/fact_warehouse_events.yaml
            "dim_warehouse",        # query_performance/dim_warehouse.yaml
            # Compute (compute/)
            "fact_node_timeline",   # compute/fact_node_timeline.yaml
            "dim_cluster",          # compute/dim_cluster.yaml
            "dim_node_type",        # compute/dim_node_type.yaml
            "dim_workspace",        # shared/dim_workspace.yaml
        ],
    },
    "security_auditor": {
        "name": "Health Monitor Security Auditor Space",
        "domain": "🔒 Security",
        "description": """Natural language interface for Databricks security, audit, and compliance analytics. 
Enables security teams, compliance officers, and administrators to query access patterns, 
audit trails, and security events without SQL.""",
        "metric_views": ["security_events", "governance_analytics"],
        "tvfs": [
            "get_user_activity_summary",
            "get_sensitive_table_access",
            "get_failed_actions",
            "get_permission_changes",
            "get_off_hours_activity",
            "get_security_events_timeline",
            "get_ip_address_analysis",
            "get_table_access_audit",
            "get_user_activity_patterns",
            "get_service_account_audit",
        ],
        "ml_tables": [
            "access_anomaly_predictions",
            "user_risk_scores",
            "access_classifications",
            "off_hours_baseline_predictions",
        ],
        "ml_model_mapping": {
            # Question pattern → ML prediction table
            "threat|suspicious|unusual access|security risk|anomaly": "access_anomaly_predictions",
            "risk score|risky users|compliance risk|high risk": "user_risk_scores",
            "access pattern|behavior|classify user|normal access": "access_classifications",
            "off hours|after hours|night access": "off_hours_baseline_predictions",
        },
        "monitoring_tables": [
            "fact_audit_logs_profile_metrics",
            "fact_audit_logs_drift_metrics",
        ],
        "slicing_dimensions": [
            "workspace_id", "service_name", "audit_level", "action_name", "user_identity_email"
        ],
        "gold_tables": [
            # Security (security/)
            "fact_audit_logs",        # security/fact_audit_logs.yaml
            "fact_assistant_events",  # security/fact_assistant_events.yaml
            "fact_clean_room_events", # security/fact_clean_room_events.yaml
            "fact_inbound_network",   # security/fact_inbound_network.yaml
            "fact_outbound_network",  # security/fact_outbound_network.yaml
            # Governance (governance/)
            "fact_table_lineage",     # governance/fact_table_lineage.yaml
            "fact_column_lineage",    # governance/fact_column_lineage.yaml
            "dim_workspace",          # shared/dim_workspace.yaml
        ],
    },
    "data_quality": {
        "name": "Health Monitor Data Quality Space",
        "domain": "✅ Quality",
        "description": """Natural language interface for data quality, freshness, and governance analytics. 
Enables data stewards, governance teams, and data engineers to query table health, 
lineage, and quality metrics without SQL.""",
        "metric_views": ["data_quality", "ml_intelligence"],
        "tvfs": [
            "get_table_freshness",
            "get_job_data_quality_status",
            "get_data_freshness_by_domain",
            "get_data_quality_summary",
            "get_tables_failing_quality",
            "get_table_activity_status",
            "get_pipeline_data_lineage",
        ],
        "ml_tables": [
            "quality_anomaly_predictions",
            "quality_trend_predictions",
            "freshness_alert_predictions",
        ],
        "ml_model_mapping": {
            # Question pattern → ML prediction table
            "data drift|distribution change|quality anomaly|data changed": "quality_anomaly_predictions",
            "schema change|schema risk|will schema change|breaking change": "quality_trend_predictions",
            "freshness alert|stale prediction|will data be late": "freshness_alert_predictions",
        },
        "monitoring_tables": [
            "fact_table_quality_profile_metrics",
            "fact_governance_metrics_profile_metrics",
            "fact_table_quality_drift_metrics",
        ],
        "slicing_dimensions": [
            "catalog_name", "schema_name", "table_name", "has_critical_violations"
        ],
        "gold_tables": [
            # Governance (governance/)
            "fact_table_lineage",     # governance/fact_table_lineage.yaml
            "fact_column_lineage",    # governance/fact_column_lineage.yaml
            # Data Classification (data_classification/)
            "fact_data_classification", # data_classification/fact_data_classification.yaml
            "fact_data_classification_results", # data_classification/fact_data_classification_results.yaml
            # Data Quality Monitoring (data_quality_monitoring/)
            "fact_dq_monitoring",     # data_quality_monitoring/fact_dq_monitoring.yaml
            "fact_data_quality_monitoring_table_results", # data_quality_monitoring/fact_data_quality_monitoring_table_results.yaml
            # Storage (storage/)
            "fact_predictive_optimization", # storage/fact_predictive_optimization.yaml
            # MLflow (mlflow/)
            "dim_experiment",         # mlflow/dim_experiment.yaml
            "fact_mlflow_runs",       # mlflow/fact_mlflow_runs.yaml
            "fact_mlflow_run_metrics_history", # mlflow/fact_mlflow_run_metrics_history.yaml
            # Model Serving (model_serving/)
            "dim_served_entities",    # model_serving/dim_served_entities.yaml
            "fact_endpoint_usage",    # model_serving/fact_endpoint_usage.yaml
            "fact_payload_logs",      # model_serving/fact_payload_logs.yaml
            # Marketplace (marketplace/)
            "fact_listing_access",    # marketplace/fact_listing_access.yaml
            "fact_listing_funnel",    # marketplace/fact_listing_funnel.yaml
            "dim_workspace",          # shared/dim_workspace.yaml
        ],
    },
    "unified": {
        "name": "Databricks Health Monitor Space",
        "domain": "🌐 Unified",
        "description": """Comprehensive natural language interface for Databricks platform health monitoring. 
Enables leadership, platform administrators, and SREs to query costs, job reliability, 
query performance, cluster efficiency, security audit, and data quality - all in one unified space.""",
        "metric_views": [
            "cost_analytics", "commit_tracking", "job_performance",
            "query_performance", "cluster_utilization", "cluster_efficiency",
            "security_events", "governance_analytics", "data_quality", "ml_intelligence"
        ],
        "tvfs": "all",  # All 60 TVFs
        "ml_tables": "all",  # All 25 ML tables
        "ml_model_mapping": {
            # Cost domain
            "unusual spending|cost anomaly|spike": "cost_anomaly_predictions",
            "forecast cost|predict cost|next month cost": "cost_forecast_predictions",
            "tag recommendations|suggest tags": "tag_recommendations",
            # Reliability domain
            "will job fail|failure prediction|at risk job": "job_failure_predictions",
            "pipeline health|health score": "pipeline_health_scores",
            "retry succeed|recovery prediction": "retry_success_predictions",
            # Performance domain
            "optimize query|query optimization": "query_optimization_recommendations",
            "right-size cluster|cluster savings": "cluster_rightsizing_recommendations",
            "cache hit|cache prediction": "cache_hit_predictions",
            # Security domain
            "security threat|suspicious access": "access_anomaly_predictions",
            "user risk|risk score": "user_risk_scores",
            "access pattern|behavior analysis": "access_classifications",
            # Quality domain
            "data drift|quality anomaly": "quality_anomaly_predictions",
            "schema change|schema prediction": "quality_trend_predictions",
            "freshness alert|late data": "freshness_alert_predictions",
        },
        "monitoring_tables": "all",  # All 16 monitoring tables
        "gold_tables": [  # All 38 Gold tables from gold_layer_design/yaml/
            # Billing (4)
            "dim_sku", "fact_usage", "fact_account_prices", "fact_list_prices",
            # Compute (3)
            "dim_cluster", "dim_node_type", "fact_node_timeline",
            # Query Performance (3)
            "dim_warehouse", "fact_query_history", "fact_warehouse_events",
            # Lakeflow (6)
            "dim_job", "dim_job_task", "dim_pipeline", 
            "fact_job_run_timeline", "fact_job_task_run_timeline", "fact_pipeline_update_timeline",
            # Security (5)
            "fact_audit_logs", "fact_assistant_events", "fact_clean_room_events",
            "fact_inbound_network", "fact_outbound_network",
            # Governance (2)
            "fact_table_lineage", "fact_column_lineage",
            # Data Classification (2)
            "fact_data_classification", "fact_data_classification_results",
            # Data Quality Monitoring (2)
            "fact_dq_monitoring", "fact_data_quality_monitoring_table_results",
            # Storage (1)
            "fact_predictive_optimization",
            # MLflow (3)
            "dim_experiment", "fact_mlflow_runs", "fact_mlflow_run_metrics_history",
            # Model Serving (3)
            "dim_served_entities", "fact_endpoint_usage", "fact_payload_logs",
            # Marketplace (2)
            "fact_listing_access", "fact_listing_funnel",
            # Shared (1)
            "dim_workspace",
        ],
    },
}

# COMMAND ----------

def print_genie_space_summary():
    """Print summary of all Genie Spaces to configure."""
    print("=" * 80)
    print("GENIE SPACES DEPLOYMENT SUMMARY")
    print("=" * 80)
    
    for space_id, config in GENIE_SPACES.items():
        print(f"\n{config['domain']} {config['name']}")
        print(f"  Description: {config['description'][:80]}...")
        
        # Count assets
        mv_count = len(config['metric_views']) if isinstance(config['metric_views'], list) else 10
        tvf_count = len(config['tvfs']) if isinstance(config['tvfs'], list) else 60
        ml_count = len(config['ml_tables']) if isinstance(config['ml_tables'], list) else 25
        
        print(f"  Metric Views: {mv_count}")
        print(f"  TVFs: {tvf_count}")
        print(f"  ML Tables: {ml_count}")
    
    print("\n" + "=" * 80)
    print("TOTAL: 6 Genie Spaces (1 per Agent Domain + Unified)")
    print("=" * 80)

print_genie_space_summary()

# COMMAND ----------

def generate_genie_space_config(space_id: str, catalog: str, gold_schema: str):
    """Generate configuration dict for a Genie Space."""
    config = GENIE_SPACES[space_id]
    
    # Build data assets list
    data_assets = []
    
    # Add metric views
    for mv in config['metric_views']:
        data_assets.append({
            "type": "metric_view",
            "name": mv,
            "catalog": catalog,
            "schema": gold_schema
        })
    
    # Add TVFs
    tvfs = config['tvfs']
    if isinstance(tvfs, list):
        for tvf in tvfs:
            data_assets.append({
                "type": "function",
                "name": tvf,
                "catalog": catalog,
                "schema": gold_schema
            })
    
    # Add ML tables
    ml_tables = config['ml_tables']
    if isinstance(ml_tables, list):
        for ml_table in ml_tables:
            data_assets.append({
                "type": "table",
                "name": ml_table,
                "catalog": catalog,
                "schema": gold_schema,
                "comment": f"ML: {ml_table}"
            })
    
    # Add monitoring tables
    mon_tables = config['monitoring_tables']
    if isinstance(mon_tables, list):
        for mon_table in mon_tables:
            data_assets.append({
                "type": "table",
                "name": mon_table,
                "catalog": catalog,
                "schema": gold_schema,
                "comment": f"Lakehouse Monitoring: {mon_table}"
            })
    
    # Add gold tables
    gold_tables = config.get('gold_tables', [])
    if isinstance(gold_tables, list):
        for table in gold_tables:
            data_assets.append({
                "type": "table",
                "name": table,
                "catalog": catalog,
                "schema": gold_schema
            })
    
    return {
        "name": config['name'],
        "description": config['description'],
        "domain": config['domain'],
        "data_assets": data_assets,
        "asset_count": len(data_assets)
    }

# COMMAND ----------

# Generate configurations for all spaces
print("\nGenerating Genie Space configurations...")
print("=" * 80)

for space_id in GENIE_SPACES.keys():
    config = generate_genie_space_config(space_id, catalog, gold_schema)
    print(f"\n{config['domain']} {config['name']}")
    print(f"  Total Assets: {config['asset_count']}")

# COMMAND ----------

print("\n" + "=" * 80)
print("DEPLOYMENT INSTRUCTIONS")
print("=" * 80)
print("""
Genie Spaces are created via the Databricks UI:

1. Navigate to: Databricks Workspace → Genie → Create Space

2. For each Genie Space:
   a. Set Name (from configuration above)
   b. Set Description (from configuration above)
   c. Select SQL Warehouse: Serverless recommended
   d. Add Trusted Assets:
      - Metric Views (primary)
      - Table-Valued Functions
      - ML Prediction Tables
      - Lakehouse Monitoring Tables (_profile_metrics, _drift_metrics)
      - Gold Tables
   e. Configure Agent Instructions (from setup markdown files)
   f. Add Sample Questions (from setup markdown files)
   g. Set Permissions for user groups

3. Test each space with benchmark questions

4. Documentation files available in:
   - src/genie/cost_intelligence_genie.md (💰 Cost)
   - src/genie/performance_genie.md (⚡ Performance - Query + Cluster)
   - src/genie/job_health_monitor_genie.md (🔄 Reliability)
   - src/genie/security_auditor_genie.md (🔒 Security)
   - src/genie/data_quality_monitor_genie.md (✅ Quality)
   - src/genie/unified_health_monitor_genie.md (🌐 Unified)

⚠️  CRITICAL: Custom Metrics Query Patterns
   When querying _profile_metrics or _drift_metrics tables:
   - ALWAYS include: column_name = ':table' AND log_type = 'INPUT'
   - For drift: ALSO include: drift_type = 'CONSECUTIVE'
   - See: docs/lakehouse-monitoring-design/05-genie-integration.md

Total Genie Spaces: 6 (1 per domain to prevent sprawl)
""")

# COMMAND ----------

print("\n✅ Genie Spaces configuration complete!")
print(f"   Catalog: {catalog}")
print(f"   Schema: {gold_schema}")
print("   Spaces: 6 (5 domain + 1 unified)")
print("\n   Next: Create spaces in Databricks UI using the setup documents")

# Exit notebook successfully
dbutils.notebook.exit("SUCCESS")

