#!/usr/bin/env python3
"""
Validate benchmarks against ACTUAL ground truth - FIXED extraction.
"""

import re
from pathlib import Path
from typing import Dict, Set, List

# Hardcoded ground truth from manual review
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
    # Cost (6)
    'cost_anomaly_predictions', 'budget_forecast_predictions', 
    'job_cost_optimizer_predictions', 'chargeback_predictions',
    'commitment_recommendations', 'tag_recommendations',
    
    # Reliability (5)
    'job_failure_predictions', 'duration_predictions', 'sla_breach_predictions',
    'retry_success_predictions', 'pipeline_health_predictions',
    
    # Performance (7)
    'query_optimization_classifications', 'query_optimization_recommendations',
    'cache_hit_predictions', 'job_duration_predictions',
    'cluster_capacity_recommendations', 'cluster_rightsizing_recommendations',
    'dbr_migration_risk_scores',
    
    # Security (4)
    'access_anomaly_predictions', 'user_risk_scores', 'access_classifications',
    'off_hours_baseline_predictions',
    
    # Quality (2)
    'quality_anomaly_predictions', 'freshness_alert_predictions',
}

VALID_METRIC_VIEWS = {
    'mv_cost_analytics', 'mv_commit_tracking', 'mv_query_performance',
    'mv_cluster_utilization', 'mv_cluster_efficiency', 'mv_job_performance',
    'mv_security_events', 'mv_governance_analytics', 'mv_data_quality',
    'mv_ml_intelligence',
}

VALID_MONITOR_TABLES = {
    'fact_usage_profile_metrics', 'fact_usage_drift_metrics',
    'fact_job_run_timeline_profile_metrics', 'fact_job_run_timeline_drift_metrics',
    'fact_query_history_profile_metrics', 'fact_query_history_drift_metrics',
    'fact_node_timeline_profile_metrics', 'fact_node_timeline_drift_metrics',
    'fact_audit_logs_profile_metrics', 'fact_audit_logs_drift_metrics',
    'fact_table_quality_profile_metrics', 'fact_table_quality_drift_metrics',
    'fact_governance_metrics_profile_metrics', 'fact_governance_metrics_drift_metrics',
    'fact_model_serving_profile_metrics', 'fact_model_serving_drift_metrics',
}

def validate_genie_space(space_name: str) -> tuple:
    """Validate a Genie Space and return (valid_count, errors)."""
    
    md_path = Path(f"src/genie/{space_name}.md")
    content = md_path.read_text()
    
    # Extract benchmark SQL
    pattern = r'### Question (\d+): "([^"]+)"\n\*\*Expected SQL:\*\*\n```sql\n(.*?)\n```'
    questions = list(re.finditer(pattern, content, re.DOTALL))
    
    print(f"\n{'='*80}")
    print(f"{space_name}: {len(questions)} questions")
    print(f"{'='*80}\n")
    
    valid_count = 0
    errors = []
    
    for match in questions:
        q_num = match.group(1)
        q_text = match.group(2)
        sql = match.group(3)
        
        question_errors = []
        
        # Check TVFs
        tvfs = re.findall(r'(get_[a-z_]+)\(', sql)
        for tvf in set(tvfs):
            if tvf not in VALID_TVFs:
                question_errors.append(f"TVF not found: {tvf}")
        
        # Check Metric Views
        mvs = re.findall(r'FROM .*?(mv_[a-z_]+)', sql)
        for mv in set(mvs):
            if mv not in VALID_METRIC_VIEWS:
                question_errors.append(f"Metric View not found: {mv}")
        
        # Check ML tables
        ml_tables = re.findall(r'([a-z_]+(?:predictions|recommendations|scores|classifications))', sql)
        for ml in set(ml_tables):
            if ml in VALID_ML_TABLES or ml.startswith('mv_'):  # Skip metric views
                continue
            if ml not in VALID_ML_TABLES:
                question_errors.append(f"ML Table not found: {ml}")
        
        # Check Monitor tables
        monitors = re.findall(r'(fact_[a-z_]+_(?:profile_metrics|drift_metrics))', sql)
        for mon in set(monitors):
            if mon not in VALID_MONITOR_TABLES:
                question_errors.append(f"Monitor Table not found: {mon}")
        
        if question_errors:
            print(f"❌ Q{q_num}: {q_text[:60]}...")
            for err in question_errors:
                print(f"   - {err}")
            errors.append((q_num, question_errors))
        else:
            print(f"✅ Q{q_num}: {q_text[:60]}...")
            valid_count += 1
    
    print(f"\n✅ Valid: {valid_count}/{len(questions)}")
    print(f"❌ Invalid: {len(errors)}/{len(questions)}")
    
    return valid_count, errors

def main():
    """Main entry point."""
    
    print("="*80)
    print("Benchmark Validation Against Ground Truth")
    print("="*80)
    print(f"\n📊 Ground Truth:")
    print(f"  - TVFs: {len(VALID_TVFs)}")
    print(f"  - Metric Views: {len(VALID_METRIC_VIEWS)}")
    print(f"  - ML Tables: {len(VALID_ML_TABLES)}")
    print(f"  - Monitor Tables: {len(VALID_MONITOR_TABLES)}")
    
    genie_spaces = [
        "cost_intelligence_genie",
        "data_quality_monitor_genie",
        "job_health_monitor_genie",
        "performance_genie",
        "security_auditor_genie",
        "unified_health_monitor_genie"
    ]
    
    total_valid = 0
    total_questions = 0
    all_errors = {}
    
    for space in genie_spaces:
        valid, errors = validate_genie_space(space)
        total_valid += valid
        total_questions += (valid + len(errors))
        if errors:
            all_errors[space] = errors
    
    print(f"\n{'='*80}")
    print(f"OVERALL: {total_valid}/{total_questions} valid ({total_valid*100//total_questions}%)")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
