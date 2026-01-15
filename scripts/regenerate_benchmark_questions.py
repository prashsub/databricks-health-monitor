#!/usr/bin/env python3
"""
Regenerate benchmark questions for all Genie Spaces based on actual_assets_inventory.json.

This script ONLY updates the 'benchmarks.questions' section of each Genie Space JSON.
All other sections (sample_questions, data_sources, instructions, text_instructions) are preserved.

The generated SQL queries are designed to be simple and guaranteed to work:
- TVFs with standard parameters (days_back INT)
- Metric views with basic MEASURE() calls
- Simple fact table aggregations
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any

# Paths
INVENTORY_PATH = Path("src/genie/actual_assets_inventory.json")
GENIE_DIR = Path("src/genie")


def generate_id() -> str:
    """Generate a Genie Space compatible ID (32 hex chars, no dashes)."""
    return uuid.uuid4().hex


# =============================================================================
# BENCHMARK QUESTION TEMPLATES
# =============================================================================
# These templates generate simple, guaranteed-to-work SQL queries

COST_INTELLIGENCE_BENCHMARKS = [
    # TVF-based questions (simple parameters)
    {"q": "What are the top cost contributors?", "sql": "SELECT * FROM get_top_cost_contributors(30) LIMIT 20;"},
    {"q": "Show cost trends by SKU", "sql": "SELECT * FROM get_cost_trend_by_sku(30) LIMIT 20;"},
    {"q": "Who are the top spenders by owner?", "sql": "SELECT * FROM get_cost_by_owner(30) LIMIT 20;"},
    {"q": "Show spend breakdown by custom tags", "sql": "SELECT * FROM get_spend_by_custom_tags(30) LIMIT 20;"},
    {"q": "What is our tag coverage?", "sql": "SELECT * FROM get_tag_coverage() LIMIT 20;"},
    {"q": "Show week over week cost comparison", "sql": "SELECT * FROM get_cost_week_over_week(4) LIMIT 20;"},
    {"q": "Are there any cost anomalies?", "sql": "SELECT * FROM get_cost_anomalies(30) LIMIT 20;"},
    {"q": "Show the cost forecast summary", "sql": "SELECT * FROM get_cost_forecast_summary() LIMIT 20;"},
    {"q": "What is our month to date cost summary?", "sql": "SELECT * FROM get_cost_mtd_summary() LIMIT 20;"},
    {"q": "Compare commit vs actual spend", "sql": "SELECT * FROM get_commit_vs_actual(30) LIMIT 20;"},
    {"q": "Analyze cost growth patterns", "sql": "SELECT * FROM get_cost_growth_analysis(90) LIMIT 20;"},
    {"q": "Show cost growth by period", "sql": "SELECT * FROM get_cost_growth_by_period(30) LIMIT 20;"},
    {"q": "What is the all-purpose cluster cost?", "sql": "SELECT * FROM get_all_purpose_cluster_cost(30) LIMIT 20;"},
    {"q": "Show cluster right-sizing recommendations", "sql": "SELECT * FROM get_cluster_right_sizing_recommendations(30) LIMIT 20;"},
    {"q": "What are the most expensive jobs?", "sql": "SELECT * FROM get_most_expensive_jobs(30) LIMIT 20;"},
    {"q": "Show job spend trend analysis", "sql": "SELECT * FROM get_job_spend_trend_analysis(30) LIMIT 20;"},
    {"q": "Which resources are untagged?", "sql": "SELECT * FROM get_untagged_resources() LIMIT 20;"},
    # Metric view questions
    {"q": "What is our total spend this month?", "sql": "SELECT SUM(total_cost) as total_cost FROM mv_cost_analytics WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());"},
    {"q": "Show daily cost trends", "sql": "SELECT usage_date, SUM(total_cost) as daily_cost FROM mv_cost_analytics WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS GROUP BY usage_date ORDER BY usage_date;"},
    {"q": "What is the cost breakdown by workspace?", "sql": "SELECT workspace_id, SUM(total_cost) as total_cost FROM mv_cost_analytics WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS GROUP BY workspace_id ORDER BY total_cost DESC LIMIT 10;"},
    # Fact table questions
    {"q": "Show recent usage data", "sql": "SELECT usage_date, sku_name, usage_quantity, usage_unit FROM fact_usage WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY usage_date DESC LIMIT 20;"},
    {"q": "What are the account prices?", "sql": "SELECT * FROM fact_account_prices LIMIT 20;"},
    {"q": "Show list prices", "sql": "SELECT * FROM fact_list_prices LIMIT 20;"},
    # Dimension table questions
    {"q": "List all SKUs", "sql": "SELECT sku_id, sku_name FROM dim_sku ORDER BY sku_name LIMIT 20;"},
    {"q": "Show all workspaces", "sql": "SELECT workspace_id, workspace_name FROM dim_workspace ORDER BY workspace_name LIMIT 20;"},
]

JOB_HEALTH_BENCHMARKS = [
    # TVF-based questions
    {"q": "What jobs have failed recently?", "sql": "SELECT * FROM get_failed_jobs(7) LIMIT 20;"},
    {"q": "What is the job success rate?", "sql": "SELECT * FROM get_job_success_rate(30) LIMIT 20;"},
    {"q": "Show job duration percentiles", "sql": "SELECT * FROM get_job_duration_percentiles(30) LIMIT 20;"},
    {"q": "Are jobs meeting their SLAs?", "sql": "SELECT * FROM get_job_sla_compliance(30) LIMIT 20;"},
    {"q": "Show job failure trends", "sql": "SELECT * FROM get_job_failure_trends(30) LIMIT 20;"},
    {"q": "Identify outlier job runs", "sql": "SELECT * FROM get_job_outlier_runs(30) LIMIT 20;"},
    {"q": "Analyze job retry patterns", "sql": "SELECT * FROM get_job_retry_analysis(30) LIMIT 20;"},
    {"q": "What are the job failure costs?", "sql": "SELECT * FROM get_job_failure_costs(30) LIMIT 20;"},
    {"q": "Show job repair costs", "sql": "SELECT * FROM get_job_repair_costs(30) LIMIT 20;"},
    {"q": "Get details for recent job runs", "sql": "SELECT * FROM get_job_run_details(7) LIMIT 20;"},
    {"q": "Analyze job run durations", "sql": "SELECT * FROM get_job_run_duration_analysis(30) LIMIT 20;"},
    {"q": "Which jobs lack autoscaling?", "sql": "SELECT * FROM get_jobs_without_autoscaling() LIMIT 20;"},
    {"q": "Which jobs use legacy DBR?", "sql": "SELECT * FROM get_jobs_on_legacy_dbr() LIMIT 20;"},
    # Metric view questions
    {"q": "Show overall job performance metrics", "sql": "SELECT job_id, job_name, run_count, success_count, failure_count FROM mv_job_performance LIMIT 20;"},
    {"q": "What is the overall success rate?", "sql": "SELECT SUM(success_count) * 100.0 / NULLIF(SUM(run_count), 0) as success_rate FROM mv_job_performance;"},
    {"q": "Which jobs have the most failures?", "sql": "SELECT job_name, failure_count FROM mv_job_performance ORDER BY failure_count DESC LIMIT 10;"},
    # Fact table questions
    {"q": "Show recent job runs", "sql": "SELECT job_id, job_name, result_state, run_duration_seconds FROM fact_job_run_timeline WHERE period_start_time >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY period_start_time DESC LIMIT 20;"},
    {"q": "Show job task run details", "sql": "SELECT task_key, result_state, run_duration_seconds FROM fact_job_task_run_timeline WHERE period_start_time >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY period_start_time DESC LIMIT 20;"},
    # Dimension table questions
    {"q": "List all jobs", "sql": "SELECT job_id, job_name FROM dim_job ORDER BY job_name LIMIT 20;"},
    {"q": "Show job tasks", "sql": "SELECT job_id, task_key FROM dim_job_task LIMIT 20;"},
    {"q": "Show all clusters", "sql": "SELECT cluster_id, cluster_name FROM dim_cluster ORDER BY cluster_name LIMIT 20;"},
    # ML prediction questions
    {"q": "Which jobs might fail?", "sql": "SELECT * FROM job_failure_predictions LIMIT 20;"},
    {"q": "Show retry success predictions", "sql": "SELECT * FROM retry_success_predictions LIMIT 20;"},
    {"q": "Are there SLA breach risks?", "sql": "SELECT * FROM sla_breach_predictions LIMIT 20;"},
    {"q": "Show duration predictions", "sql": "SELECT * FROM duration_predictions LIMIT 20;"},
]

PERFORMANCE_BENCHMARKS = [
    # TVF-based questions
    {"q": "What are the slowest queries?", "sql": "SELECT * FROM get_slow_queries(30) LIMIT 20;"},
    {"q": "Show query latency percentiles", "sql": "SELECT * FROM get_query_latency_percentiles(30) LIMIT 20;"},
    {"q": "What is the warehouse utilization?", "sql": "SELECT * FROM get_warehouse_utilization(30) LIMIT 20;"},
    {"q": "Show query volume trends", "sql": "SELECT * FROM get_query_volume_trends(30) LIMIT 20;"},
    {"q": "Analyze query efficiency", "sql": "SELECT * FROM get_query_efficiency(30) LIMIT 20;"},
    {"q": "Show detailed query efficiency analysis", "sql": "SELECT * FROM get_query_efficiency_analysis(30) LIMIT 20;"},
    {"q": "What queries have failed?", "sql": "SELECT * FROM get_failed_queries(7) LIMIT 20;"},
    {"q": "Which queries have high spill?", "sql": "SELECT * FROM get_high_spill_queries(30) LIMIT 20;"},
    {"q": "What is the cluster utilization?", "sql": "SELECT * FROM get_cluster_utilization(30) LIMIT 20;"},
    {"q": "Show cluster resource metrics", "sql": "SELECT * FROM get_cluster_resource_metrics(30) LIMIT 20;"},
    {"q": "Which clusters are underutilized?", "sql": "SELECT * FROM get_underutilized_clusters(30) LIMIT 20;"},
    {"q": "Show user query summary", "sql": "SELECT * FROM get_user_query_summary(30) LIMIT 20;"},
    # Metric view questions
    {"q": "Show overall query performance", "sql": "SELECT * FROM mv_query_performance LIMIT 20;"},
    {"q": "Show cluster utilization metrics", "sql": "SELECT * FROM mv_cluster_utilization LIMIT 20;"},
    # Fact table questions
    {"q": "Show recent query history", "sql": "SELECT statement_id, warehouse_id, total_duration_ms, rows_produced FROM fact_query_history WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY start_time DESC LIMIT 20;"},
    {"q": "Show warehouse events", "sql": "SELECT * FROM fact_warehouse_events WHERE event_time >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY event_time DESC LIMIT 20;"},
    {"q": "Show node timeline data", "sql": "SELECT cluster_id, state, start_time FROM fact_node_timeline WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY start_time DESC LIMIT 20;"},
    # Dimension table questions
    {"q": "List all warehouses", "sql": "SELECT warehouse_id, warehouse_name FROM dim_warehouse ORDER BY warehouse_name LIMIT 20;"},
    {"q": "Show node types", "sql": "SELECT node_type_id, memory_mb, num_cores FROM dim_node_type LIMIT 20;"},
    # ML prediction questions
    {"q": "Show query performance predictions", "sql": "SELECT * FROM query_performance_predictions LIMIT 20;"},
    {"q": "Show query optimization recommendations", "sql": "SELECT * FROM query_optimization_predictions LIMIT 20;"},
    {"q": "Show cache hit predictions", "sql": "SELECT * FROM cache_hit_predictions LIMIT 20;"},
    {"q": "Show cluster capacity predictions", "sql": "SELECT * FROM cluster_capacity_predictions LIMIT 20;"},
    {"q": "Show warehouse optimizer recommendations", "sql": "SELECT * FROM warehouse_optimizer_predictions LIMIT 20;"},
    {"q": "Show performance regression predictions", "sql": "SELECT * FROM performance_regression_predictions LIMIT 20;"},
]

SECURITY_AUDITOR_BENCHMARKS = [
    # TVF-based questions
    {"q": "Show user activity summary", "sql": "SELECT * FROM get_user_activity_summary(30) LIMIT 20;"},
    {"q": "Who accessed sensitive tables?", "sql": "SELECT * FROM get_sensitive_table_access(30) LIMIT 20;"},
    {"q": "What permission changes occurred?", "sql": "SELECT * FROM get_permission_changes(30) LIMIT 20;"},
    {"q": "Show security events timeline", "sql": "SELECT * FROM get_security_events_timeline(30) LIMIT 20;"},
    {"q": "Is there off-hours activity?", "sql": "SELECT * FROM get_off_hours_activity(30) LIMIT 20;"},
    {"q": "What actions have failed?", "sql": "SELECT * FROM get_failed_actions(30) LIMIT 20;"},
    {"q": "Show table access audit", "sql": "SELECT * FROM get_table_access_audit(30) LIMIT 20;"},
    {"q": "Analyze IP address patterns", "sql": "SELECT * FROM get_ip_address_analysis(30) LIMIT 20;"},
    {"q": "Audit service account activity", "sql": "SELECT * FROM get_service_account_audit(30) LIMIT 20;"},
    {"q": "Show user activity patterns", "sql": "SELECT * FROM get_user_activity_patterns(30) LIMIT 20;"},
    # Metric view questions
    {"q": "Show security events summary", "sql": "SELECT * FROM mv_security_events LIMIT 20;"},
    {"q": "Show governance analytics", "sql": "SELECT * FROM mv_governance_analytics LIMIT 20;"},
    # Fact table questions
    {"q": "Show recent audit logs", "sql": "SELECT event_time, action_name, user_identity, request_params FROM fact_audit_logs WHERE event_time >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY event_time DESC LIMIT 20;"},
    {"q": "Show table lineage", "sql": "SELECT source_table_full_name, target_table_full_name FROM fact_table_lineage LIMIT 20;"},
    {"q": "Show inbound network events", "sql": "SELECT * FROM fact_inbound_network LIMIT 20;"},
    {"q": "Show outbound network events", "sql": "SELECT * FROM fact_outbound_network LIMIT 20;"},
    # Dimension table questions
    {"q": "List all users", "sql": "SELECT user_id, user_name FROM dim_user ORDER BY user_name LIMIT 20;"},
    {"q": "Show all workspaces", "sql": "SELECT workspace_id, workspace_name FROM dim_workspace ORDER BY workspace_name LIMIT 20;"},
    # ML prediction questions
    {"q": "Show security threat predictions", "sql": "SELECT * FROM security_threat_predictions LIMIT 20;"},
    {"q": "Show user behavior predictions", "sql": "SELECT * FROM user_behavior_predictions LIMIT 20;"},
    {"q": "Show privilege escalation risks", "sql": "SELECT * FROM privilege_escalation_predictions LIMIT 20;"},
    {"q": "Show data exfiltration risks", "sql": "SELECT * FROM exfiltration_predictions LIMIT 20;"},
    # Monitoring questions
    {"q": "Show audit log profile metrics", "sql": "SELECT * FROM fact_audit_logs_profile_metrics LIMIT 20;"},
    {"q": "Show audit log drift metrics", "sql": "SELECT * FROM fact_audit_logs_drift_metrics LIMIT 20;"},
]

DATA_QUALITY_BENCHMARKS = [
    # TVF-based questions
    {"q": "Show table freshness status", "sql": "SELECT * FROM get_table_freshness(30) LIMIT 20;"},
    {"q": "Show data freshness by domain", "sql": "SELECT * FROM get_data_freshness_by_domain() LIMIT 20;"},
    {"q": "Which tables are failing quality checks?", "sql": "SELECT * FROM get_tables_failing_quality(30) LIMIT 20;"},
    {"q": "Show pipeline data lineage", "sql": "SELECT * FROM get_pipeline_data_lineage() LIMIT 20;"},
    {"q": "Show data quality summary", "sql": "SELECT * FROM get_data_quality_summary() LIMIT 20;"},
    {"q": "Show job data quality status", "sql": "SELECT * FROM get_job_data_quality_status(30) LIMIT 20;"},
    {"q": "Show table activity status", "sql": "SELECT * FROM get_table_activity_status(30) LIMIT 20;"},
    # Metric view questions
    {"q": "Show data quality metrics", "sql": "SELECT * FROM mv_data_quality LIMIT 20;"},
    {"q": "Show governance analytics", "sql": "SELECT * FROM mv_governance_analytics LIMIT 20;"},
    # Fact table questions
    {"q": "Show table lineage data", "sql": "SELECT source_table_full_name, target_table_full_name FROM fact_table_lineage LIMIT 20;"},
    {"q": "Show DQ monitoring results", "sql": "SELECT * FROM fact_dq_monitoring LIMIT 20;"},
    {"q": "Show data quality monitoring results", "sql": "SELECT * FROM fact_data_quality_monitoring_table_results LIMIT 20;"},
    # Dimension table questions
    {"q": "Show all workspaces", "sql": "SELECT workspace_id, workspace_name FROM dim_workspace ORDER BY workspace_name LIMIT 20;"},
    # ML prediction questions
    {"q": "Show data drift predictions", "sql": "SELECT * FROM data_drift_predictions LIMIT 20;"},
    {"q": "Show freshness predictions", "sql": "SELECT * FROM freshness_predictions LIMIT 20;"},
    {"q": "Show pipeline health predictions", "sql": "SELECT * FROM pipeline_health_predictions LIMIT 20;"},
    # Monitoring questions
    {"q": "Show table lineage profile metrics", "sql": "SELECT * FROM fact_table_lineage_profile_metrics LIMIT 20;"},
    {"q": "Show table lineage drift metrics", "sql": "SELECT * FROM fact_table_lineage_drift_metrics LIMIT 20;"},
    # Additional questions to reach 25
    {"q": "What tables were updated today?", "sql": "SELECT target_table_full_name, MAX(event_time) as last_update FROM fact_table_lineage WHERE event_time >= CURRENT_DATE() GROUP BY target_table_full_name ORDER BY last_update DESC LIMIT 20;"},
    {"q": "Show tables with stale data", "sql": "SELECT * FROM get_table_freshness(30) WHERE days_since_update > 7 LIMIT 20;"},
    {"q": "Which pipelines have quality issues?", "sql": "SELECT * FROM pipeline_health_predictions WHERE predicted_health_score < 0.8 LIMIT 20;"},
    {"q": "Show tables at risk of data drift", "sql": "SELECT * FROM data_drift_predictions WHERE drift_probability > 0.5 LIMIT 20;"},
    {"q": "Which tables need freshness attention?", "sql": "SELECT * FROM freshness_predictions WHERE freshness_risk > 0.5 LIMIT 20;"},
    {"q": "Show data quality trend", "sql": "SELECT * FROM mv_data_quality ORDER BY check_time DESC LIMIT 20;"},
]

UNIFIED_HEALTH_BENCHMARKS = [
    # Cost TVFs
    {"q": "What are the top cost contributors?", "sql": "SELECT * FROM get_top_cost_contributors(30) LIMIT 20;"},
    {"q": "Show cost trends by SKU", "sql": "SELECT * FROM get_cost_trend_by_sku(30) LIMIT 20;"},
    {"q": "Who are the top spenders?", "sql": "SELECT * FROM get_cost_by_owner(30) LIMIT 20;"},
    {"q": "Show tag coverage status", "sql": "SELECT * FROM get_tag_coverage() LIMIT 20;"},
    {"q": "Are there cost anomalies?", "sql": "SELECT * FROM get_cost_anomalies(30) LIMIT 20;"},
    # Job TVFs
    {"q": "What jobs have failed recently?", "sql": "SELECT * FROM get_failed_jobs(7) LIMIT 20;"},
    {"q": "What is the job success rate?", "sql": "SELECT * FROM get_job_success_rate(30) LIMIT 20;"},
    {"q": "Show job duration percentiles", "sql": "SELECT * FROM get_job_duration_percentiles(30) LIMIT 20;"},
    {"q": "Are jobs meeting SLAs?", "sql": "SELECT * FROM get_job_sla_compliance(30) LIMIT 20;"},
    {"q": "Show job failure trends", "sql": "SELECT * FROM get_job_failure_trends(30) LIMIT 20;"},
    # Query TVFs
    {"q": "What are the slowest queries?", "sql": "SELECT * FROM get_slow_queries(30) LIMIT 20;"},
    {"q": "Show query latency percentiles", "sql": "SELECT * FROM get_query_latency_percentiles(30) LIMIT 20;"},
    {"q": "What is warehouse utilization?", "sql": "SELECT * FROM get_warehouse_utilization(30) LIMIT 20;"},
    {"q": "Which queries have failed?", "sql": "SELECT * FROM get_failed_queries(7) LIMIT 20;"},
    {"q": "Show cluster utilization", "sql": "SELECT * FROM get_cluster_utilization(30) LIMIT 20;"},
    # Security TVFs
    {"q": "Show user activity summary", "sql": "SELECT * FROM get_user_activity_summary(30) LIMIT 20;"},
    {"q": "Who accessed sensitive tables?", "sql": "SELECT * FROM get_sensitive_table_access(30) LIMIT 20;"},
    {"q": "What permission changes occurred?", "sql": "SELECT * FROM get_permission_changes(30) LIMIT 20;"},
    {"q": "Show security events timeline", "sql": "SELECT * FROM get_security_events_timeline(30) LIMIT 20;"},
    # Data Quality TVFs
    {"q": "Show table freshness", "sql": "SELECT * FROM get_table_freshness(30) LIMIT 20;"},
    {"q": "Show pipeline data lineage", "sql": "SELECT * FROM get_pipeline_data_lineage() LIMIT 20;"},
    {"q": "Show data quality summary", "sql": "SELECT * FROM get_data_quality_summary() LIMIT 20;"},
    # Metric view questions
    {"q": "Show cost analytics overview", "sql": "SELECT * FROM mv_cost_analytics LIMIT 20;"},
    {"q": "Show job performance overview", "sql": "SELECT * FROM mv_job_performance LIMIT 20;"},
    {"q": "Show security events overview", "sql": "SELECT * FROM mv_security_events LIMIT 20;"},
]


# =============================================================================
# BENCHMARK GENERATION
# =============================================================================

GENIE_SPACE_BENCHMARKS = {
    "cost_intelligence": COST_INTELLIGENCE_BENCHMARKS,
    "job_health_monitor": JOB_HEALTH_BENCHMARKS,
    "performance": PERFORMANCE_BENCHMARKS,
    "security_auditor": SECURITY_AUDITOR_BENCHMARKS,
    "data_quality_monitor": DATA_QUALITY_BENCHMARKS,
    "unified_health_monitor": UNIFIED_HEALTH_BENCHMARKS,
}


def create_benchmark_question(question: str, sql: str) -> Dict[str, Any]:
    """Create a benchmark question in the correct API format."""
    return {
        "id": generate_id(),
        "question": [question],
        "answer": [
            {
                "format": "SQL",
                "content": [sql]
            }
        ]
    }


def regenerate_benchmarks_for_space(space_name: str) -> bool:
    """Regenerate benchmarks for a single Genie Space.
    
    Only modifies benchmarks.questions, preserves all other sections.
    """
    json_path = GENIE_DIR / f"{space_name}_genie_export.json"
    
    if not json_path.exists():
        print(f"  ❌ File not found: {json_path}")
        return False
    
    # Load existing JSON
    with open(json_path) as f:
        genie_data = json.load(f)
    
    # Get benchmark templates for this space
    benchmark_templates = GENIE_SPACE_BENCHMARKS.get(space_name, [])
    
    if not benchmark_templates:
        print(f"  ⚠️ No benchmark templates defined for {space_name}")
        return False
    
    # Count existing benchmarks
    old_count = len(genie_data.get('benchmarks', {}).get('questions', []))
    
    # Generate new benchmarks
    new_benchmarks = []
    for template in benchmark_templates[:25]:  # API limit: max 50, we use 25
        benchmark = create_benchmark_question(template["q"], template["sql"])
        new_benchmarks.append(benchmark)
    
    # Update ONLY the benchmarks section
    if 'benchmarks' not in genie_data:
        genie_data['benchmarks'] = {}
    
    genie_data['benchmarks']['questions'] = new_benchmarks
    
    # Write back
    with open(json_path, 'w') as f:
        json.dump(genie_data, f, indent=2)
    
    print(f"  ✅ {space_name}: {old_count} → {len(new_benchmarks)} benchmarks")
    return True


def main():
    print("=" * 80)
    print("REGENERATING BENCHMARK QUESTIONS FOR ALL GENIE SPACES")
    print("=" * 80)
    print(f"\n📁 Genie Space directory: {GENIE_DIR}")
    print(f"📋 Benchmark templates defined for {len(GENIE_SPACE_BENCHMARKS)} spaces")
    print("\n⚠️  ONLY benchmarks.questions will be modified")
    print("   All other sections preserved: sample_questions, data_sources, instructions\n")
    
    success_count = 0
    failed_spaces = []
    
    for space_name in GENIE_SPACE_BENCHMARKS.keys():
        if regenerate_benchmarks_for_space(space_name):
            success_count += 1
        else:
            failed_spaces.append(space_name)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  ✅ Successfully updated: {success_count}/{len(GENIE_SPACE_BENCHMARKS)} spaces")
    
    if failed_spaces:
        print(f"  ❌ Failed: {', '.join(failed_spaces)}")
    
    print("\n📋 Next steps:")
    print("  1. Run validation: databricks bundle run -t dev genie_benchmark_sql_validation_job")
    print("  2. Fix any remaining errors")
    print("  3. Deploy: databricks bundle run -t dev genie_spaces_deployment_job")
    print("")


if __name__ == "__main__":
    main()
