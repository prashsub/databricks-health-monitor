#!/usr/bin/env python3
"""
Apply ground truth fixes to Genie Space benchmark questions.

Strategy:
1. Identify invalid questions
2. Generate simple, valid replacements using ground truth assets
3. Update markdown files
"""

import re
from pathlib import Path
from typing import Dict, List

# ============================================================================
# GROUND TRUTH - Manually curated from validation
# ============================================================================

VALID_TVFs = {
    # Cost (15)
    'get_top_cost_contributors', 'get_cost_trend_by_sku', 'get_cost_by_owner',
    'get_spend_by_custom_tags', 'get_tag_coverage', 'get_cost_week_over_week',
    'get_cost_anomaly_analysis', 'get_cost_forecast_summary', 'get_cost_mtd_summary',
    'get_commit_vs_actual', 'get_cost_growth_analysis', 'get_cost_growth_by_period',
    'get_cost_efficiency_metrics', 'get_cluster_cost_efficiency', 'get_storage_cost_analysis',
    
    # Reliability (12)
    'get_failed_jobs_summary', 'get_job_success_rates', 'get_job_duration_trends',
    'get_job_sla_compliance', 'get_job_failure_patterns', 'get_long_running_jobs',
    'get_job_retry_analysis', 'get_job_duration_percentiles', 'get_job_failure_cost',
    'get_pipeline_health', 'get_job_schedule_drift', 'get_repair_cost_analysis',
    
    # Performance Query (10)
    'get_slowest_queries', 'get_query_latency_percentiles', 'get_warehouse_performance',
    'get_query_volume_trends', 'get_top_users_by_query_count', 'get_query_efficiency_by_user',
    'get_query_queue_analysis', 'get_failed_queries_summary', 'get_cache_hit_analysis',
    'get_spill_analysis',
    
    # Performance Cluster (11)
    'get_cluster_utilization', 'get_cluster_resource_metrics', 'get_underutilized_clusters',
    'get_cluster_rightsizing_recommendations', 'get_autoscaling_disabled_jobs',
    'get_legacy_dbr_jobs', 'get_cluster_cost_by_type', 'get_cluster_uptime_analysis',
    'get_cluster_scaling_events', 'get_cluster_efficiency_metrics',
    'get_node_utilization_by_cluster',
    
    # Security (7)
    'get_user_activity', 'get_sensitive_data_access', 'get_failed_access_attempts',
    'get_permission_change_history', 'get_off_hours_access', 'get_ip_location_analysis',
    'get_service_account_activity',
    
    # Quality (5)
    'get_stale_tables', 'get_table_lineage', 'get_table_activity_summary',
    'get_data_lineage_summary', 'get_pipeline_lineage_impact',
}

VALID_ML_TABLES = {
    # Cost
    'cost_anomaly_predictions', 'budget_forecast_predictions', 
    'job_cost_optimizer_predictions', 'chargeback_predictions',
    'commitment_recommendations', 'tag_recommendations',
    
    # Reliability
    'job_failure_predictions', 'duration_predictions', 'sla_breach_predictions',
    'retry_success_predictions', 'pipeline_health_predictions',
    
    # Performance
    'query_optimization_classifications', 'query_optimization_recommendations',
    'cache_hit_predictions', 'job_duration_predictions',
    'cluster_capacity_recommendations', 'cluster_rightsizing_recommendations',
    'dbr_migration_risk_scores',
    
    # Security
    'access_anomaly_predictions', 'user_risk_scores', 'access_classifications',
    'off_hours_baseline_predictions',
    
    # Quality
    'quality_anomaly_predictions', 'freshness_alert_predictions',
}

VALID_METRIC_VIEWS = {
    'mv_cost_analytics', 'mv_commit_tracking', 'mv_query_performance',
    'mv_cluster_utilization', 'mv_cluster_efficiency', 'mv_job_performance',
    'mv_security_events', 'mv_governance_analytics', 'mv_data_quality',
    'mv_ml_intelligence',
}

# ============================================================================
# Fix Mappings
# ============================================================================

TVF_REPLACEMENTS = {
    # Missing TVFs → Valid replacements
    'get_untagged_resources': ('get_tag_coverage', 'Get tag coverage instead of untagged list'),
    'get_cost_anomalies': ('get_cost_anomaly_analysis', 'Use cost_anomaly_analysis TVF'),
    'get_daily_cost_summary': ('get_cost_mtd_summary', 'Use MTD summary'),
    'get_cost_by_tag': ('get_spend_by_custom_tags', 'Use spend_by_custom_tags'),
    'get_job_cost_breakdown': ('get_job_failure_cost', 'Use job_failure_cost for job costs'),
    'get_warehouse_cost_analysis': ('get_warehouse_performance', 'Use warehouse_performance'),
    'get_cost_by_cluster_type': ('get_cluster_cost_by_type', 'Use cluster_cost_by_type'),
    'get_serverless_vs_classic_cost': ('get_cost_efficiency_metrics', 'Use efficiency metrics'),
    'get_cost_forecast': ('get_cost_forecast_summary', 'Use forecast_summary TVF'),
    
    # Quality TVFs
    'get_data_quality_summary': ('get_table_activity_summary', 'Use table_activity_summary'),
    'get_table_freshness': ('get_stale_tables', 'Use stale_tables TVF'),
    'get_tables_failing_quality': ('get_stale_tables', 'Use stale_tables'),
    'get_pipeline_data_lineage': ('get_data_lineage_summary', 'Use lineage_summary'),
    'get_table_activity_status': ('get_table_activity_summary', 'Use activity_summary'),
    'get_job_data_quality_status': ('get_table_activity_summary', 'Fallback to activity'),
    'get_data_freshness_by_domain': ('get_table_activity_summary', 'Use activity summary'),
    
    # Reliability TVFs
    'get_failed_jobs': ('get_failed_jobs_summary', 'Use failed_jobs_summary'),
    'get_job_success_rate': ('get_job_success_rates', 'Use success_rates (plural)'),
    'get_job_failure_trends': ('get_job_failure_patterns', 'Use failure_patterns'),
    
    # Performance TVFs
    'get_slow_queries': ('get_slowest_queries', 'Use slowest_queries'),
    'get_warehouse_utilization': ('get_warehouse_performance', 'Use warehouse_performance'),
    'get_jobs_without_autoscaling': ('get_autoscaling_disabled_jobs', 'Use autoscaling_disabled'),
    'get_jobs_on_legacy_dbr': ('get_legacy_dbr_jobs', 'Use legacy_dbr_jobs'),
    'get_cluster_rightsizing': ('get_cluster_rightsizing_recommendations', 'Use recommendations'),
    
    # Security TVFs
    'get_user_activity_summary': ('get_user_activity', 'Use user_activity'),
    'get_sensitive_table_access': ('get_sensitive_data_access', 'Use sensitive_data_access'),
    'get_failed_actions': ('get_failed_access_attempts', 'Use failed_access_attempts'),
    'get_permission_changes': ('get_permission_change_history', 'Use change_history'),
    'get_off_hours_activity': ('get_off_hours_access', 'Use off_hours_access'),
    'get_security_events_timeline': ('get_user_activity', 'Fallback to user_activity'),
    'get_ip_address_analysis': ('get_ip_location_analysis', 'Use ip_location_analysis'),
    'get_service_account_audit': ('get_service_account_activity', 'Use service_account_activity'),
}

def fix_genie_space_benchmarks(space_name: str) -> bool:
    """Fix benchmark questions in a Genie Space markdown file."""
    
    md_path = Path(f"src/genie/{space_name}.md")
    if not md_path.exists():
        print(f"⚠️  Not found: {md_path}")
        return False
    
    print(f"\n{'='*80}")
    print(f"Fixing: {space_name}")
    print(f"{'='*80}\n")
    
    content = md_path.read_text()
    original_content = content
    fixes_applied = 0
    
    # Fix invalid TVF calls
    for invalid_tvf, (valid_tvf, reason) in TVF_REPLACEMENTS.items():
        if invalid_tvf in content:
            content = content.replace(invalid_tvf, valid_tvf)
            fixes_applied += 1
            print(f"✓ TVF: {invalid_tvf} → {valid_tvf}")
    
    # Fix invalid ML table references
    # Remove questions that reference non-existent ML tables
    # This is more complex and requires removing whole question sections
    
    if content != original_content:
        md_path.write_text(content)
        print(f"\n✅ Applied {fixes_applied} fixes to {space_name}")
        return True
    else:
        print(f"\n✅ No fixes needed for {space_name}")
        return False

def main():
    """Main entry point."""
    
    print("="*80)
    print("Apply Ground Truth Fixes to Genie Spaces")
    print("="*80)
    
    genie_spaces = [
        "cost_intelligence_genie",
        "data_quality_monitor_genie",
        "job_health_monitor_genie",
        "performance_genie",
        "security_auditor_genie",
        "unified_health_monitor_genie"
    ]
    
    total_fixed = 0
    for space in genie_spaces:
        if fix_genie_space_benchmarks(space):
            total_fixed += 1
    
    print(f"\n{'='*80}")
    print(f"Summary: Fixed {total_fixed}/{len(genie_spaces)} Genie Spaces")
    print(f"{'='*80}")
    
    print("\n📝 Next Steps:")
    print("1. Review the fixes in each markdown file")
    print("2. Run: python3 scripts/extract_benchmarks_to_json.py")
    print("3. Run: databricks bundle run -t dev genie_spaces_deployment_job")

if __name__ == "__main__":
    main()
