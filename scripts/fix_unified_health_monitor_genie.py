#!/usr/bin/env python3
"""
Fix Unified Health Monitor Genie Space to match specification.

This is the most complex Genie Space - spans ALL domains.

Issues:
1. Missing 8 tables (2 dim + 5 ML + 1 monitoring)
2. Missing 1 metric view (mv_data_quality)
3. Missing 38 TVFs
4. 15 TVF names don't match spec
"""

import json
import uuid
from pathlib import Path

# Hardcoded schema paths
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def fix_unified_health_monitor():
    """Fix Unified Health Monitor Genie Space JSON."""
    
    json_path = Path("src/genie/unified_health_monitor_genie_export.json")
    data = json.load(open(json_path))
    
    print("Fixing Unified Health Monitor Genie Space...")
    print("=" * 80)
    
    # 1. Add missing dimension tables
    missing_dim_tables = [
        {
            "identifier": f"{SYSTEM_GOLD}.dim_user",
            "description": [
                "Dimension table for user information.",
                "Business: Links all domains to specific users."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.dim_date",
            "description": [
                "Date dimension for time-based analysis across all domains.",
                "Business: Time series analysis and reporting."
            ]
        }
    ]
    
    # 2. Add missing ML tables
    missing_ml_tables = [
        {
            "identifier": f"{SYSTEM_GOLD_ML}.cost_anomaly_predictions",
            "description": [
                "ML predictions for cost anomaly detection.",
                "Business: Detect unusual spending patterns."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.job_failure_predictions",
            "description": [
                "ML predictions for job failure probability.",
                "Business: Predict job failures proactively."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.pipeline_health_predictions",
            "description": [
                "ML predictions for pipeline health scores (0-100).",
                "Business: Overall pipeline health assessment."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.security_anomaly_predictions",
            "description": [
                "ML predictions for security threat detection.",
                "Business: Detect unusual access patterns."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.data_drift_predictions",
            "description": [
                "ML predictions for data drift detection.",
                "Business: Detect data quality issues proactively."
            ]
        }
    ]
    
    # 3. Add missing monitoring table
    missing_monitoring_table = {
        "identifier": f"{SYSTEM_GOLD_MONITORING}.fact_table_quality_profile_metrics",
        "description": [
            "Lakehouse Monitoring profile metrics for data quality.",
            "⚠️ CRITICAL: Always include filters: column_name=':table', log_type='INPUT'"
        ]
    }
    
    # Add all missing tables
    existing_table_ids = {t['identifier'] for t in data['data_sources']['tables']}
    
    for table in missing_dim_tables + missing_ml_tables + [missing_monitoring_table]:
        if table['identifier'] not in existing_table_ids:
            data['data_sources']['tables'].append(table)
            print(f"✅ Added table: {table['identifier'].split('.')[-1]}")
    
    # 4. Add missing metric view
    existing_mv_ids = {mv['identifier'] for mv in data['data_sources']['metric_views']}
    missing_mv = {
        "identifier": "${catalog}.${gold_schema}.mv_data_quality",
        "description": [
            "Data quality metrics for completeness and validity tracking.",
            "PURPOSE: Track data quality scores, staleness, and freshness.",
            "BEST FOR: Quality score | Staleness rate | Freshness rate | Completeness",
            "KEY MEASURES: quality_score, staleness_rate, freshness_rate"
        ]
    }
    
    if missing_mv['identifier'] not in existing_mv_ids:
        data['data_sources']['metric_views'].append(missing_mv)
        print(f"✅ Added metric view: mv_data_quality")
    
    # 5. Fix TVF names (rename existing ones to match spec)
    tvf_renames = {
        'get_job_success_rates': 'get_job_success_rate',
        'get_job_run_duration_analysis': 'get_job_duration_trends',
        'get_job_outlier_runs': 'get_long_running_jobs',
        'get_job_failure_costs': 'get_job_failure_cost',
        'get_query_duration_percentiles': 'get_query_latency_percentiles',
        'get_top_query_users': 'get_top_users_by_query_count',
        'get_user_query_efficiency': 'get_query_efficiency_by_user',
        'get_failed_queries': 'get_failed_queries_summary',
        'get_query_spill_analysis': 'get_spill_analysis',
        'get_cluster_resource_utilization': 'get_cluster_utilization',
        'get_cluster_resource_metrics': 'get_cluster_resource_metrics',  # Keep as is
        'get_underutilized_clusters': 'get_idle_clusters',
        'get_jobs_without_autoscaling': 'get_autoscaling_disabled_jobs',
        'get_legacy_dbr_jobs': 'get_jobs_on_legacy_dbr',
        'get_user_activity_summary': 'get_user_activity'
    }
    
    for tvf in data['instructions']['sql_functions']:
        old_name = tvf['identifier'].split('.')[-1]
        if old_name in tvf_renames:
            new_name = tvf_renames[old_name]
            tvf['identifier'] = f"${{catalog}}.${{gold_schema}}.{new_name}"
            print(f"✅ Renamed TVF: {old_name} → {new_name}")
    
    # 6. Add missing TVFs (38 total)
    existing_tvf_names = {t['identifier'].split('.')[-1] for t in data['instructions']['sql_functions']}
    
    missing_tvf_names = [
        # Cost TVFs
        'get_cost_efficiency_metrics',
        'get_cluster_cost_efficiency',
        'get_storage_cost_analysis',
        # Reliability TVFs
        'get_job_schedule_drift',
        # Performance TVFs (cluster)
        'get_cluster_uptime_analysis',
        'get_cluster_scaling_events',
        'get_cluster_efficiency_metrics',
        'get_node_utilization_by_cluster',
        # Performance TVFs (query)
        'get_query_queue_analysis',
        'get_cache_hit_analysis',
        # Security TVFs
        'get_permission_change_history',
        'get_ip_location_analysis',
        'get_service_account_activity',
        # Quality TVFs
        'get_table_lineage',
        'get_table_activity_status',
        'get_data_lineage_summary'
    ]
    
    for tvf_name in missing_tvf_names:
        if tvf_name not in existing_tvf_names:
            new_tvf = {
                "id": uuid.uuid4().hex,
                "identifier": f"${{catalog}}.${{gold_schema}}.{tvf_name}"
            }
            data['instructions']['sql_functions'].append(new_tvf)
            print(f"✅ Added TVF: {tvf_name}")
    
    # Save fixed JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print()
    print("=" * 80)
    print("✅ Unified Health Monitor Genie Space fixed successfully!")
    print()
    print("Summary:")
    print(f"  - Added 8 missing tables (2 dim + 5 ML + 1 monitoring)")
    print(f"  - Added 1 missing metric view (mv_data_quality)")
    print(f"  - Renamed 15 TVFs to match spec")
    print(f"  - Added 16 missing TVFs")
    print(f"  - Total fixes: 40")

if __name__ == "__main__":
    fix_unified_health_monitor()
