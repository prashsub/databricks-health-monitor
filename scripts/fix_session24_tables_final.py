#!/usr/bin/env python3
"""
Fix Session 24 - Remove all tables from undeployed domains.

Based on successful deployments, these tables EXIST:
- billing: dim_sku, fact_usage, fact_account_prices, fact_list_prices
- compute: dim_cluster, dim_node_type, fact_node_timeline
- lakeflow: dim_job, dim_job_task, dim_pipeline, fact_job_run_timeline, 
           fact_job_task_run_timeline, fact_pipeline_update_timeline
- shared: dim_workspace
- security: dim_user, fact_table_lineage, fact_audit_logs
- query_performance: dim_warehouse, fact_query_history, fact_warehouse_events
- monitoring: *_profile_metrics, *_drift_metrics (for deployed tables)

These domains are NOT deployed yet:
- data_quality_monitoring: fact_dq_monitoring, fact_data_quality_monitoring_table_results
- data_classification: fact_data_classification, fact_data_classification_results
- mlflow: dim_experiment, fact_mlflow_runs, fact_mlflow_run_metrics_history
- model_serving: dim_served_entities, fact_endpoint_usage, fact_payload_logs
- marketplace: fact_listing_access, fact_listing_funnel
- storage: fact_predictive_optimization
- Some ML tables that don't exist yet
"""

import json
from pathlib import Path
from typing import Set

# Tables that are KNOWN TO NOT EXIST (from undeployed domains)
NONEXISTENT_TABLES = {
    # Data Quality Monitoring domain - not deployed
    "dim_dq_monitoring",
    "fact_dq_monitoring",
    "fact_data_quality_monitoring_table_results",
    
    # Data Classification domain - not deployed
    "fact_data_classification",
    "fact_data_classification_results",
    
    # MLflow domain - not deployed
    "dim_experiment",
    "fact_mlflow_runs",
    "fact_mlflow_run_metrics_history",
    
    # Model Serving domain - not deployed
    "dim_served_entities",
    "fact_endpoint_usage",
    "fact_payload_logs",
    
    # Marketplace domain - not deployed
    "fact_listing_access",
    "fact_listing_funnel",
    
    # Storage domain - not deployed
    "fact_predictive_optimization",
    
    # Security additional tables that may not exist
    "fact_assistant_events",
    "fact_clean_room_events",
    "fact_inbound_network",
    "fact_outbound_network",
    
    # Monitoring tables that don't exist (only some domains have monitoring)
    "fact_governance_metrics_profile_metrics",
    "fact_data_classification_profile_metrics",
    "fact_dq_monitoring_profile_metrics",
    "fact_mlflow_runs_profile_metrics",
    "fact_endpoint_usage_profile_metrics",
    "fact_listing_funnel_profile_metrics",
    
    # ML tables that don't exist
    "freshness_alert_predictions",
    "quality_anomaly_predictions",
    "cluster_capacity_recommendations",
    "cluster_rightsizing_recommendations",
    "security_anomaly_predictions",
    "cost_anomaly_predictions",
    "budget_forecast_predictions",
    "job_cost_optimizer_predictions",
    "chargeback_predictions",
    "commitment_recommendations",
    "tag_recommendations",
    "query_optimization_classifications",
    "query_optimization_recommendations",
    "cache_hit_predictions",
    "job_duration_predictions",
    "dbr_migration_risk_scores",
    "user_risk_scores",
    "access_classifications",
    "off_hours_baseline_predictions",
    "job_failure_predictions",
    "cluster_efficiency_scores",
    "dbu_optimization_recommendations",
    "schema_change_predictor",
    "column_usage_predictions",
    "table_usage_forecast_predictions",
    "stale_table_predictions",
    "data_drift_predictions",
}


def should_remove_table(identifier: str) -> bool:
    """Check if table should be removed based on identifier."""
    # Extract table name from identifier
    table_name = identifier.split(".")[-1]
    return table_name in NONEXISTENT_TABLES


def fix_genie_space(json_path: Path) -> int:
    """Remove non-existent tables from a Genie Space JSON file."""
    with open(json_path) as f:
        data = json.load(f)
    
    tables = data.get('data_sources', {}).get('tables', [])
    original_count = len(tables)
    
    # Filter out non-existent tables
    data['data_sources']['tables'] = [
        t for t in tables
        if not should_remove_table(t.get('identifier', ''))
    ]
    
    removed = original_count - len(data['data_sources']['tables'])
    
    if removed > 0:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return removed


def main():
    """Fix all failing Genie Spaces."""
    print("=" * 80)
    print("SESSION 24 - REMOVE TABLES FROM UNDEPLOYED DOMAINS")
    print("=" * 80)
    print()
    
    # Only fix the failing spaces
    failing_spaces = [
        "src/genie/data_quality_monitor_genie_export.json",
        "src/genie/unified_health_monitor_genie_export.json",
    ]
    
    total_removed = 0
    for json_path in failing_spaces:
        path = Path(json_path)
        removed = fix_genie_space(path)
        print(f"{path.stem}: Removed {removed} non-existent tables")
        total_removed += removed
    
    print()
    print(f"Total tables removed: {total_removed}")
    print("=" * 80)


if __name__ == "__main__":
    main()
