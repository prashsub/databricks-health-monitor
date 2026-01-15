#!/usr/bin/env python3
"""
Regenerate ALL Genie Space benchmarks using ONLY assets from actual_assets_inventory.json.

This script ensures every benchmark SQL query references ONLY:
- TVFs that actually exist in Unity Catalog (with FULLY QUALIFIED names)
- Metric views that actually exist (with FULLY QUALIFIED names)
- Tables (dim, fact, ML, monitoring) that actually exist (with FULLY QUALIFIED names)

CRITICAL: All SQL uses template variables that are substituted at runtime:
- ${catalog}.${gold_schema}.table_name
- ${catalog}.${feature_schema}.ml_table_name
- ${catalog}.${gold_schema}_monitoring.monitoring_table_name
"""

import json
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
INVENTORY_PATH = PROJECT_ROOT / "src/genie/actual_assets_inventory.json"
GENIE_DIR = PROJECT_ROOT / "src/genie"

# Template variable prefixes
GOLD_PREFIX = "${catalog}.${gold_schema}"
ML_PREFIX = "${catalog}.${feature_schema}"
MON_PREFIX = "${catalog}.${gold_schema}_monitoring"

def generate_id():
    return uuid.uuid4().hex

# Load inventory
with open(INVENTORY_PATH) as f:
    INVENTORY = json.load(f)

def get_domain_assets(domain_name):
    """Get all assets for a specific domain from inventory."""
    mapping = INVENTORY['domain_mapping'].get(domain_name, {})
    
    # Flatten tables
    tables = mapping.get('tables', {})
    dims = tables.get('dimensions', [])
    facts = tables.get('facts', [])
    
    return {
        'metric_views': mapping.get('metric_views', []),
        'tvfs': mapping.get('tvfs', []),
        'ml_tables': mapping.get('ml_tables', []),
        'monitoring_tables': mapping.get('monitoring_tables', []),
        'dim_tables': dims,
        'fact_tables': facts,
    }


def build_tvf_benchmarks(tvfs: list, max_count: int = 8) -> list:
    """Generate TVF benchmark questions - use FULLY QUALIFIED names with template variables.
    
    CRITICAL: All TVFs take NO parameters - they use internal defaults.
    CRITICAL: Fully qualified TVFs do NOT use TABLE() wrapper.
    Call pattern: SELECT * FROM catalog.schema.function_name()
    """
    benchmarks = []
    
    # TVF question templates - SQL uses fully qualified names with template variables
    # IMPORTANT: All TVFs have NO parameters (verified from Unity Catalog)
    # IMPORTANT: NO TABLE() wrapper for fully qualified TVF calls
    tvf_questions = {
        # Cost
        'get_top_cost_contributors': ("Who are the top cost contributors?", f"SELECT * FROM {GOLD_PREFIX}.get_top_cost_contributors() LIMIT 20;"),
        'get_cost_trend_by_sku': ("Show cost trend by SKU", f"SELECT * FROM {GOLD_PREFIX}.get_cost_trend_by_sku() LIMIT 20;"),
        'get_cost_by_owner': ("Show cost by owner", f"SELECT * FROM {GOLD_PREFIX}.get_cost_by_owner() LIMIT 20;"),
        'get_spend_by_custom_tags': ("Show spend by custom tags", f"SELECT * FROM {GOLD_PREFIX}.get_spend_by_custom_tags() LIMIT 20;"),
        'get_tag_coverage': ("What is our tag coverage?", f"SELECT * FROM {GOLD_PREFIX}.get_tag_coverage() LIMIT 20;"),
        'get_cost_week_over_week': ("Show cost week over week", f"SELECT * FROM {GOLD_PREFIX}.get_cost_week_over_week() LIMIT 20;"),
        'get_cost_anomalies': ("Show cost anomalies", f"SELECT * FROM {GOLD_PREFIX}.get_cost_anomalies() LIMIT 20;"),
        'get_cost_forecast_summary': ("Show cost forecast", f"SELECT * FROM {GOLD_PREFIX}.get_cost_forecast_summary() LIMIT 20;"),
        'get_cost_mtd_summary': ("Show month-to-date cost summary", f"SELECT * FROM {GOLD_PREFIX}.get_cost_mtd_summary() LIMIT 20;"),
        'get_commit_vs_actual': ("Compare commit vs actual spend", f"SELECT * FROM {GOLD_PREFIX}.get_commit_vs_actual() LIMIT 20;"),
        'get_cost_growth_analysis': ("Analyze cost growth", f"SELECT * FROM {GOLD_PREFIX}.get_cost_growth_analysis() LIMIT 20;"),
        'get_cost_growth_by_period': ("Show cost growth by period", f"SELECT * FROM {GOLD_PREFIX}.get_cost_growth_by_period() LIMIT 20;"),
        'get_all_purpose_cluster_cost': ("Show all-purpose cluster costs", f"SELECT * FROM {GOLD_PREFIX}.get_all_purpose_cluster_cost() LIMIT 20;"),
        'get_cluster_right_sizing_recommendations': ("Show cluster right-sizing recommendations", f"SELECT * FROM {GOLD_PREFIX}.get_cluster_right_sizing_recommendations() LIMIT 20;"),
        'get_most_expensive_jobs': ("What are the most expensive jobs?", f"SELECT * FROM {GOLD_PREFIX}.get_most_expensive_jobs() LIMIT 20;"),
        'get_job_spend_trend_analysis': ("Analyze job spend trends", f"SELECT * FROM {GOLD_PREFIX}.get_job_spend_trend_analysis() LIMIT 20;"),
        'get_untagged_resources': ("Show untagged resources", f"SELECT * FROM {GOLD_PREFIX}.get_untagged_resources() LIMIT 20;"),
        
        # Jobs
        'get_failed_jobs': ("What jobs have failed recently?", f"SELECT * FROM {GOLD_PREFIX}.get_failed_jobs() LIMIT 20;"),
        'get_job_success_rate': ("What is the job success rate?", f"SELECT * FROM {GOLD_PREFIX}.get_job_success_rate() LIMIT 20;"),
        'get_job_duration_percentiles': ("Show job duration percentiles", f"SELECT * FROM {GOLD_PREFIX}.get_job_duration_percentiles() LIMIT 20;"),
        'get_job_sla_compliance': ("Show job SLA compliance", f"SELECT * FROM {GOLD_PREFIX}.get_job_sla_compliance() LIMIT 20;"),
        'get_job_failure_trends': ("Show job failure trends", f"SELECT * FROM {GOLD_PREFIX}.get_job_failure_trends() LIMIT 20;"),
        'get_job_outlier_runs': ("Show outlier job runs", f"SELECT * FROM {GOLD_PREFIX}.get_job_outlier_runs() LIMIT 20;"),
        'get_job_retry_analysis': ("Analyze job retries", f"SELECT * FROM {GOLD_PREFIX}.get_job_retry_analysis() LIMIT 20;"),
        'get_job_failure_costs': ("What are job failure costs?", f"SELECT * FROM {GOLD_PREFIX}.get_job_failure_costs() LIMIT 20;"),
        'get_job_repair_costs': ("Show job repair costs", f"SELECT * FROM {GOLD_PREFIX}.get_job_repair_costs() LIMIT 20;"),
        'get_job_run_details': ("Show job run details", f"SELECT * FROM {GOLD_PREFIX}.get_job_run_details() LIMIT 20;"),
        'get_job_run_duration_analysis': ("Analyze job run durations", f"SELECT * FROM {GOLD_PREFIX}.get_job_run_duration_analysis() LIMIT 20;"),
        'get_jobs_without_autoscaling': ("Which jobs lack autoscaling?", f"SELECT * FROM {GOLD_PREFIX}.get_jobs_without_autoscaling() LIMIT 20;"),
        'get_jobs_on_legacy_dbr': ("Which jobs use legacy DBR?", f"SELECT * FROM {GOLD_PREFIX}.get_jobs_on_legacy_dbr() LIMIT 20;"),
        'get_job_data_quality_status': ("Show job data quality status", f"SELECT * FROM {GOLD_PREFIX}.get_job_data_quality_status() LIMIT 20;"),
        
        # Performance
        'get_slow_queries': ("What are the slowest queries?", f"SELECT * FROM {GOLD_PREFIX}.get_slow_queries() LIMIT 20;"),
        'get_query_latency_percentiles': ("Show query latency percentiles", f"SELECT * FROM {GOLD_PREFIX}.get_query_latency_percentiles() LIMIT 20;"),
        'get_warehouse_utilization': ("Show warehouse utilization", f"SELECT * FROM {GOLD_PREFIX}.get_warehouse_utilization() LIMIT 20;"),
        'get_query_volume_trends': ("Show query volume trends", f"SELECT * FROM {GOLD_PREFIX}.get_query_volume_trends() LIMIT 20;"),
        'get_query_efficiency': ("Analyze query efficiency", f"SELECT * FROM {GOLD_PREFIX}.get_query_efficiency() LIMIT 20;"),
        'get_query_efficiency_analysis': ("Show detailed query efficiency analysis", f"SELECT * FROM {GOLD_PREFIX}.get_query_efficiency_analysis() LIMIT 20;"),
        'get_failed_queries': ("Show failed queries", f"SELECT * FROM {GOLD_PREFIX}.get_failed_queries() LIMIT 20;"),
        'get_high_spill_queries': ("Show queries with high spill", f"SELECT * FROM {GOLD_PREFIX}.get_high_spill_queries() LIMIT 20;"),
        'get_cluster_utilization': ("Show cluster utilization", f"SELECT * FROM {GOLD_PREFIX}.get_cluster_utilization() LIMIT 20;"),
        'get_cluster_resource_metrics': ("Show cluster resource metrics", f"SELECT * FROM {GOLD_PREFIX}.get_cluster_resource_metrics() LIMIT 20;"),
        'get_underutilized_clusters': ("Show underutilized clusters", f"SELECT * FROM {GOLD_PREFIX}.get_underutilized_clusters() LIMIT 20;"),
        'get_user_query_summary': ("Show user query summary", f"SELECT * FROM {GOLD_PREFIX}.get_user_query_summary() LIMIT 20;"),
        
        # Security
        'get_user_activity_summary': ("Show user activity summary", f"SELECT * FROM {GOLD_PREFIX}.get_user_activity_summary() LIMIT 20;"),
        'get_sensitive_table_access': ("Show sensitive table access", f"SELECT * FROM {GOLD_PREFIX}.get_sensitive_table_access() LIMIT 20;"),
        'get_permission_changes': ("Show permission changes", f"SELECT * FROM {GOLD_PREFIX}.get_permission_changes() LIMIT 20;"),
        'get_security_events_timeline': ("Show security events timeline", f"SELECT * FROM {GOLD_PREFIX}.get_security_events_timeline() LIMIT 20;"),
        'get_off_hours_activity': ("Show off-hours activity", f"SELECT * FROM {GOLD_PREFIX}.get_off_hours_activity() LIMIT 20;"),
        'get_failed_actions': ("Show failed actions", f"SELECT * FROM {GOLD_PREFIX}.get_failed_actions() LIMIT 20;"),
        'get_table_access_audit': ("Show table access audit", f"SELECT * FROM {GOLD_PREFIX}.get_table_access_audit() LIMIT 20;"),
        'get_ip_address_analysis': ("Analyze IP address patterns", f"SELECT * FROM {GOLD_PREFIX}.get_ip_address_analysis() LIMIT 20;"),
        'get_service_account_audit': ("Show service account audit", f"SELECT * FROM {GOLD_PREFIX}.get_service_account_audit() LIMIT 20;"),
        'get_user_activity_patterns': ("Show user activity patterns", f"SELECT * FROM {GOLD_PREFIX}.get_user_activity_patterns() LIMIT 20;"),
        
        # Data Quality
        'get_table_freshness': ("Show table freshness", f"SELECT * FROM {GOLD_PREFIX}.get_table_freshness() LIMIT 20;"),
        'get_data_freshness_by_domain': ("Show data freshness by domain", f"SELECT * FROM {GOLD_PREFIX}.get_data_freshness_by_domain() LIMIT 20;"),
        'get_tables_failing_quality': ("Show tables failing quality", f"SELECT * FROM {GOLD_PREFIX}.get_tables_failing_quality() LIMIT 20;"),
        'get_pipeline_data_lineage': ("Show pipeline data lineage", f"SELECT * FROM {GOLD_PREFIX}.get_pipeline_data_lineage() LIMIT 20;"),
        'get_data_quality_summary': ("Show data quality summary", f"SELECT * FROM {GOLD_PREFIX}.get_data_quality_summary() LIMIT 20;"),
        'get_table_activity_status': ("Show table activity status", f"SELECT * FROM {GOLD_PREFIX}.get_table_activity_status() LIMIT 20;"),
    }
    
    for tvf in tvfs[:max_count]:
        if tvf in tvf_questions:
            q, sql = tvf_questions[tvf]
            benchmarks.append({
                "id": generate_id(),
                "question": [q],
                "answer": [{"format": "SQL", "content": [sql]}]
            })
    
    return benchmarks


def build_mv_benchmarks(metric_views: list, max_count: int = 4) -> list:
    """Generate metric view benchmark questions - use FULLY QUALIFIED names."""
    benchmarks = []
    
    mv_questions = {
        'mv_cost_analytics': [
            ("Show cost analytics overview", f"SELECT * FROM {GOLD_PREFIX}.mv_cost_analytics LIMIT 20;"),
        ],
        'mv_commit_tracking': [
            ("Show commit tracking status", f"SELECT * FROM {GOLD_PREFIX}.mv_commit_tracking LIMIT 20;"),
        ],
        'mv_job_performance': [
            ("Show job performance metrics", f"SELECT * FROM {GOLD_PREFIX}.mv_job_performance LIMIT 20;"),
        ],
        'mv_query_performance': [
            ("Show query performance metrics", f"SELECT * FROM {GOLD_PREFIX}.mv_query_performance LIMIT 20;"),
        ],
        'mv_cluster_utilization': [
            ("Show cluster utilization metrics", f"SELECT * FROM {GOLD_PREFIX}.mv_cluster_utilization LIMIT 20;"),
        ],
        'mv_security_events': [
            ("Show security event metrics", f"SELECT * FROM {GOLD_PREFIX}.mv_security_events LIMIT 20;"),
        ],
        'mv_governance_analytics': [
            ("Show governance analytics", f"SELECT * FROM {GOLD_PREFIX}.mv_governance_analytics LIMIT 20;"),
        ],
        'mv_data_quality': [
            ("Show data quality metrics", f"SELECT * FROM {GOLD_PREFIX}.mv_data_quality LIMIT 20;"),
        ],
        'mv_ml_intelligence': [
            ("Show ML intelligence metrics", f"SELECT * FROM {GOLD_PREFIX}.mv_ml_intelligence LIMIT 20;"),
        ],
        'mv_cluster_efficiency': [
            ("Show cluster efficiency metrics", f"SELECT * FROM {GOLD_PREFIX}.mv_cluster_efficiency LIMIT 20;"),
        ],
    }
    
    count = 0
    for mv in metric_views:
        if mv in mv_questions and count < max_count:
            for q, sql in mv_questions[mv]:
                if count < max_count:
                    benchmarks.append({
                        "id": generate_id(),
                        "question": [q],
                        "answer": [{"format": "SQL", "content": [sql]}]
                    })
                    count += 1
    
    return benchmarks


def build_ml_benchmarks(ml_tables: list, max_count: int = 3) -> list:
    """Generate ML table benchmark questions - use FULLY QUALIFIED names."""
    benchmarks = []
    
    ml_questions = {
        'cost_anomaly_predictions': ("Show cost anomaly predictions", f"SELECT * FROM {ML_PREFIX}.cost_anomaly_predictions LIMIT 20;"),
        'budget_forecast_predictions': ("Show budget forecasts", f"SELECT * FROM {ML_PREFIX}.budget_forecast_predictions LIMIT 20;"),
        'job_cost_optimizer_predictions': ("Show job cost optimization predictions", f"SELECT * FROM {ML_PREFIX}.job_cost_optimizer_predictions LIMIT 20;"),
        'chargeback_predictions': ("Show chargeback predictions", f"SELECT * FROM {ML_PREFIX}.chargeback_predictions LIMIT 20;"),
        'commitment_recommendations': ("Show commitment recommendations", f"SELECT * FROM {ML_PREFIX}.commitment_recommendations LIMIT 20;"),
        'tag_recommendations': ("Show tag recommendations", f"SELECT * FROM {ML_PREFIX}.tag_recommendations LIMIT 20;"),
        'job_failure_predictions': ("Which jobs might fail?", f"SELECT * FROM {ML_PREFIX}.job_failure_predictions LIMIT 20;"),
        'retry_success_predictions': ("Show retry success predictions", f"SELECT * FROM {ML_PREFIX}.retry_success_predictions LIMIT 20;"),
        'sla_breach_predictions': ("Show SLA breach predictions", f"SELECT * FROM {ML_PREFIX}.sla_breach_predictions LIMIT 20;"),
        'duration_predictions': ("Show duration predictions", f"SELECT * FROM {ML_PREFIX}.duration_predictions LIMIT 20;"),
        'query_performance_predictions': ("Show query performance predictions", f"SELECT * FROM {ML_PREFIX}.query_performance_predictions LIMIT 20;"),
        'query_optimization_predictions': ("Show query optimization predictions", f"SELECT * FROM {ML_PREFIX}.query_optimization_predictions LIMIT 20;"),
        'cache_hit_predictions': ("Show cache hit predictions", f"SELECT * FROM {ML_PREFIX}.cache_hit_predictions LIMIT 20;"),
        'cluster_capacity_predictions': ("Show cluster capacity predictions", f"SELECT * FROM {ML_PREFIX}.cluster_capacity_predictions LIMIT 20;"),
        'warehouse_optimizer_predictions': ("Show warehouse optimization predictions", f"SELECT * FROM {ML_PREFIX}.warehouse_optimizer_predictions LIMIT 20;"),
        'performance_regression_predictions': ("Show performance regression predictions", f"SELECT * FROM {ML_PREFIX}.performance_regression_predictions LIMIT 20;"),
        'dbr_migration_predictions': ("Show DBR migration predictions", f"SELECT * FROM {ML_PREFIX}.dbr_migration_predictions LIMIT 20;"),
        'security_threat_predictions': ("Show security threat predictions", f"SELECT * FROM {ML_PREFIX}.security_threat_predictions LIMIT 20;"),
        'user_behavior_predictions': ("Show user behavior predictions", f"SELECT * FROM {ML_PREFIX}.user_behavior_predictions LIMIT 20;"),
        'privilege_escalation_predictions': ("Show privilege escalation predictions", f"SELECT * FROM {ML_PREFIX}.privilege_escalation_predictions LIMIT 20;"),
        'exfiltration_predictions': ("Show exfiltration risk predictions", f"SELECT * FROM {ML_PREFIX}.exfiltration_predictions LIMIT 20;"),
        'data_drift_predictions': ("Show data drift predictions", f"SELECT * FROM {ML_PREFIX}.data_drift_predictions LIMIT 20;"),
        'freshness_predictions': ("Show freshness predictions", f"SELECT * FROM {ML_PREFIX}.freshness_predictions LIMIT 20;"),
        'pipeline_health_predictions': ("Show pipeline health predictions", f"SELECT * FROM {ML_PREFIX}.pipeline_health_predictions LIMIT 20;"),
    }
    
    for ml_table in ml_tables[:max_count]:
        if ml_table in ml_questions:
            q, sql = ml_questions[ml_table]
            benchmarks.append({
                "id": generate_id(),
                "question": [q],
                "answer": [{"format": "SQL", "content": [sql]}]
            })
    
    return benchmarks


def build_monitoring_benchmarks(monitoring_tables: list, max_count: int = 2) -> list:
    """Generate Lakehouse Monitoring table benchmark questions - use FULLY QUALIFIED names."""
    benchmarks = []
    
    monitoring_questions = {
        'fact_usage_profile_metrics': ("Show usage profile metrics", f"SELECT * FROM {MON_PREFIX}.fact_usage_profile_metrics LIMIT 20;"),
        'fact_usage_drift_metrics': ("Show usage drift metrics", f"SELECT * FROM {MON_PREFIX}.fact_usage_drift_metrics LIMIT 20;"),
        'fact_job_run_timeline_profile_metrics': ("Show job profile metrics", f"SELECT * FROM {MON_PREFIX}.fact_job_run_timeline_profile_metrics LIMIT 20;"),
        'fact_job_run_timeline_drift_metrics': ("Show job drift metrics", f"SELECT * FROM {MON_PREFIX}.fact_job_run_timeline_drift_metrics LIMIT 20;"),
        'fact_query_history_profile_metrics': ("Show query profile metrics", f"SELECT * FROM {MON_PREFIX}.fact_query_history_profile_metrics LIMIT 20;"),
        'fact_query_history_drift_metrics': ("Show query drift metrics", f"SELECT * FROM {MON_PREFIX}.fact_query_history_drift_metrics LIMIT 20;"),
        'fact_node_timeline_profile_metrics': ("Show node timeline profile metrics", f"SELECT * FROM {MON_PREFIX}.fact_node_timeline_profile_metrics LIMIT 20;"),
        'fact_node_timeline_drift_metrics': ("Show node timeline drift metrics", f"SELECT * FROM {MON_PREFIX}.fact_node_timeline_drift_metrics LIMIT 20;"),
        'fact_audit_logs_profile_metrics': ("Show audit log profile metrics", f"SELECT * FROM {MON_PREFIX}.fact_audit_logs_profile_metrics LIMIT 20;"),
        'fact_audit_logs_drift_metrics': ("Show audit log drift metrics", f"SELECT * FROM {MON_PREFIX}.fact_audit_logs_drift_metrics LIMIT 20;"),
        'fact_table_lineage_profile_metrics': ("Show lineage profile metrics", f"SELECT * FROM {MON_PREFIX}.fact_table_lineage_profile_metrics LIMIT 20;"),
        'fact_table_lineage_drift_metrics': ("Show lineage drift metrics", f"SELECT * FROM {MON_PREFIX}.fact_table_lineage_drift_metrics LIMIT 20;"),
    }
    
    for mon_table in monitoring_tables[:max_count]:
        if mon_table in monitoring_questions:
            q, sql = monitoring_questions[mon_table]
            benchmarks.append({
                "id": generate_id(),
                "question": [q],
                "answer": [{"format": "SQL", "content": [sql]}]
            })
    
    return benchmarks


def build_fact_benchmarks(fact_tables: list, max_count: int = 2) -> list:
    """Generate fact table benchmark questions - use FULLY QUALIFIED names."""
    benchmarks = []
    
    fact_questions = {
        'fact_usage': ("Show recent usage data", f"SELECT * FROM {GOLD_PREFIX}.fact_usage LIMIT 20;"),
        'fact_account_prices': ("Show account pricing", f"SELECT * FROM {GOLD_PREFIX}.fact_account_prices LIMIT 20;"),
        'fact_list_prices': ("Show list prices", f"SELECT * FROM {GOLD_PREFIX}.fact_list_prices LIMIT 20;"),
        'fact_node_timeline': ("Show node timeline", f"SELECT * FROM {GOLD_PREFIX}.fact_node_timeline LIMIT 20;"),
        'fact_job_run_timeline': ("Show recent job runs", f"SELECT * FROM {GOLD_PREFIX}.fact_job_run_timeline LIMIT 20;"),
        'fact_job_task_run_timeline': ("Show recent task runs", f"SELECT * FROM {GOLD_PREFIX}.fact_job_task_run_timeline LIMIT 20;"),
        'fact_query_history': ("Show recent queries", f"SELECT * FROM {GOLD_PREFIX}.fact_query_history LIMIT 20;"),
        'fact_warehouse_events': ("Show warehouse events", f"SELECT * FROM {GOLD_PREFIX}.fact_warehouse_events LIMIT 20;"),
        'fact_audit_logs': ("Show recent audit logs", f"SELECT * FROM {GOLD_PREFIX}.fact_audit_logs LIMIT 20;"),
        'fact_table_lineage': ("Show table lineage", f"SELECT * FROM {GOLD_PREFIX}.fact_table_lineage LIMIT 20;"),
        'fact_inbound_network': ("Show inbound network activity", f"SELECT * FROM {GOLD_PREFIX}.fact_inbound_network LIMIT 20;"),
        'fact_outbound_network': ("Show outbound network activity", f"SELECT * FROM {GOLD_PREFIX}.fact_outbound_network LIMIT 20;"),
        'fact_dq_monitoring': ("Show data quality monitoring", f"SELECT * FROM {GOLD_PREFIX}.fact_dq_monitoring LIMIT 20;"),
        'fact_data_quality_monitoring_table_results': ("Show DQ monitoring results", f"SELECT * FROM {GOLD_PREFIX}.fact_data_quality_monitoring_table_results LIMIT 20;"),
    }
    
    for fact_table in fact_tables[:max_count]:
        if fact_table in fact_questions:
            q, sql = fact_questions[fact_table]
            benchmarks.append({
                "id": generate_id(),
                "question": [q],
                "answer": [{"format": "SQL", "content": [sql]}]
            })
    
    return benchmarks


def build_dim_benchmarks(dim_tables: list, max_count: int = 1) -> list:
    """Generate dimension table benchmark questions - use FULLY QUALIFIED names."""
    benchmarks = []
    
    dim_questions = {
        'dim_sku': ("List all SKUs", f"SELECT * FROM {GOLD_PREFIX}.dim_sku LIMIT 20;"),
        'dim_workspace': ("List all workspaces", f"SELECT * FROM {GOLD_PREFIX}.dim_workspace LIMIT 20;"),
        'dim_cluster': ("List all clusters", f"SELECT * FROM {GOLD_PREFIX}.dim_cluster LIMIT 20;"),
        'dim_node_type': ("List all node types", f"SELECT * FROM {GOLD_PREFIX}.dim_node_type LIMIT 20;"),
        'dim_job': ("List all jobs", f"SELECT * FROM {GOLD_PREFIX}.dim_job LIMIT 20;"),
        'dim_job_task': ("List job tasks", f"SELECT * FROM {GOLD_PREFIX}.dim_job_task LIMIT 20;"),
        'dim_warehouse': ("List all warehouses", f"SELECT * FROM {GOLD_PREFIX}.dim_warehouse LIMIT 20;"),
        'dim_user': ("List all users", f"SELECT * FROM {GOLD_PREFIX}.dim_user LIMIT 20;"),
    }
    
    for dim_table in dim_tables[:max_count]:
        if dim_table in dim_questions:
            q, sql = dim_questions[dim_table]
            benchmarks.append({
                "id": generate_id(),
                "question": [q],
                "answer": [{"format": "SQL", "content": [sql]}]
            })
    
    return benchmarks


def build_deep_research_benchmarks(domain_name: str, assets: dict) -> list:
    """Generate 5 deep research questions for each domain - use FULLY QUALIFIED names."""
    
    deep_research = {
        'cost_intelligence': [
            {
                "question": "Deep Research: What is the total cost by workspace?",
                "sql": f"SELECT workspace_id, SUM(usage_quantity) as total_usage FROM {GOLD_PREFIX}.fact_usage GROUP BY workspace_id ORDER BY total_usage DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show cost anomaly predictions with high scores",
                "sql": f"SELECT * FROM {ML_PREFIX}.cost_anomaly_predictions ORDER BY prediction DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show budget forecast summary",
                "sql": f"SELECT * FROM {ML_PREFIX}.budget_forecast_predictions LIMIT 15;"
            },
            {
                "question": "Deep Research: Show usage profile metrics summary",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_usage_profile_metrics LIMIT 15;"
            },
            {
                "question": "Deep Research: Show usage drift metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_usage_drift_metrics LIMIT 15;"
            },
        ],
        'job_health_monitor': [
            {
                "question": "Deep Research: What is the job success rate by workspace?",
                "sql": f"SELECT workspace_id, result_state, COUNT(*) as run_count FROM {GOLD_PREFIX}.fact_job_run_timeline GROUP BY workspace_id, result_state LIMIT 15;"
            },
            {
                "question": "Deep Research: Show job failure predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.job_failure_predictions ORDER BY prediction DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show SLA breach risk predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.sla_breach_predictions ORDER BY prediction DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show job run profile metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_job_run_timeline_profile_metrics LIMIT 15;"
            },
            {
                "question": "Deep Research: Show job run drift metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_job_run_timeline_drift_metrics LIMIT 15;"
            },
        ],
        'performance': [
            {
                "question": "Deep Research: Show query performance by warehouse",
                "sql": f"SELECT warehouse_id, COUNT(*) as query_count, AVG(duration_ms) as avg_duration_ms FROM {GOLD_PREFIX}.fact_query_history GROUP BY warehouse_id LIMIT 15;"
            },
            {
                "question": "Deep Research: Show query performance predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.query_performance_predictions ORDER BY prediction DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show warehouse optimization predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.warehouse_optimizer_predictions LIMIT 15;"
            },
            {
                "question": "Deep Research: Show query profile metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_query_history_profile_metrics LIMIT 15;"
            },
            {
                "question": "Deep Research: Show query drift metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_query_history_drift_metrics LIMIT 15;"
            },
        ],
        'security_auditor': [
            {
                "question": "Deep Research: Show audit events by action",
                "sql": f"SELECT action_name, COUNT(*) as event_count FROM {GOLD_PREFIX}.fact_audit_logs GROUP BY action_name ORDER BY event_count DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show security threat predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.security_threat_predictions ORDER BY prediction DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show user behavior predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.user_behavior_predictions ORDER BY prediction DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show audit log profile metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_audit_logs_profile_metrics LIMIT 15;"
            },
            {
                "question": "Deep Research: Show audit log drift metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_audit_logs_drift_metrics LIMIT 15;"
            },
        ],
        'data_quality_monitor': [
            {
                "question": "Deep Research: Show table lineage summary",
                "sql": f"SELECT * FROM {GOLD_PREFIX}.fact_table_lineage LIMIT 15;"
            },
            {
                "question": "Deep Research: Show data drift predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.data_drift_predictions ORDER BY prediction DESC LIMIT 15;"
            },
            {
                "question": "Deep Research: Show pipeline health predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.pipeline_health_predictions LIMIT 15;"
            },
            {
                "question": "Deep Research: Show lineage profile metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_table_lineage_profile_metrics LIMIT 15;"
            },
            {
                "question": "Deep Research: Show lineage drift metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_table_lineage_drift_metrics LIMIT 15;"
            },
        ],
        'unified_health_monitor': [
            {
                "question": "Deep Research: Show cost summary by workspace",
                "sql": f"SELECT * FROM {GOLD_PREFIX}.mv_cost_analytics LIMIT 15;"
            },
            {
                "question": "Deep Research: Show job performance summary",
                "sql": f"SELECT * FROM {GOLD_PREFIX}.mv_job_performance LIMIT 15;"
            },
            {
                "question": "Deep Research: Show pipeline health predictions",
                "sql": f"SELECT * FROM {ML_PREFIX}.pipeline_health_predictions LIMIT 15;"
            },
            {
                "question": "Deep Research: Show job run profile metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_job_run_timeline_profile_metrics LIMIT 15;"
            },
            {
                "question": "Deep Research: Show query profile metrics",
                "sql": f"SELECT * FROM {MON_PREFIX}.fact_query_history_profile_metrics LIMIT 15;"
            },
        ],
    }
    
    benchmarks = []
    if domain_name in deep_research:
        for dr in deep_research[domain_name]:
            benchmarks.append({
                "id": generate_id(),
                "question": [dr["question"]],
                "answer": [{"format": "SQL", "content": [dr["sql"]]}]
            })
    
    return benchmarks


def regenerate_genie_benchmarks(domain_name: str):
    """Regenerate benchmarks for a single Genie Space from inventory."""
    
    json_path = GENIE_DIR / f"{domain_name}_genie_export.json"
    
    if not json_path.exists():
        print(f"⚠️ {json_path.name} not found")
        return False
    
    # Get domain assets
    assets = get_domain_assets(domain_name)
    
    # Build benchmarks from actual assets
    benchmarks = []
    
    # TVFs (8)
    benchmarks.extend(build_tvf_benchmarks(assets['tvfs'], max_count=8))
    
    # Metric Views (4)
    benchmarks.extend(build_mv_benchmarks(assets['metric_views'], max_count=4))
    
    # ML Tables (3)
    benchmarks.extend(build_ml_benchmarks(assets['ml_tables'], max_count=3))
    
    # Monitoring Tables (2)
    benchmarks.extend(build_monitoring_benchmarks(assets['monitoring_tables'], max_count=2))
    
    # Fact Tables (2)
    benchmarks.extend(build_fact_benchmarks(assets['fact_tables'], max_count=2))
    
    # Dim Tables (1)
    benchmarks.extend(build_dim_benchmarks(assets['dim_tables'], max_count=1))
    
    # Deep Research (5)
    benchmarks.extend(build_deep_research_benchmarks(domain_name, assets))
    
    # Load existing JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Update only benchmarks section
    data['benchmarks'] = {'questions': benchmarks}
    
    # Write back
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Count distribution
    print(f"\n✅ {domain_name}: {len(benchmarks)} benchmarks generated")
    print(f"   TVFs: {len(build_tvf_benchmarks(assets['tvfs'], max_count=8))}")
    print(f"   MVs: {len(build_mv_benchmarks(assets['metric_views'], max_count=4))}")
    print(f"   ML: {len(build_ml_benchmarks(assets['ml_tables'], max_count=3))}")
    print(f"   Monitoring: {len(build_monitoring_benchmarks(assets['monitoring_tables'], max_count=2))}")
    print(f"   Fact: {len(build_fact_benchmarks(assets['fact_tables'], max_count=2))}")
    print(f"   Dim: {len(build_dim_benchmarks(assets['dim_tables'], max_count=1))}")
    print(f"   Deep Research: {len(build_deep_research_benchmarks(domain_name, assets))}")
    
    return True


def main():
    print("=" * 70)
    print("REGENERATING ALL GENIE SPACE BENCHMARKS FROM INVENTORY")
    print("Using FULLY QUALIFIED names with template variables:")
    print(f"  - Gold:       {GOLD_PREFIX}.<object>")
    print(f"  - ML:         {ML_PREFIX}.<object>")
    print(f"  - Monitoring: {MON_PREFIX}.<object>")
    print("=" * 70)
    
    domains = [
        'cost_intelligence',
        'job_health_monitor',
        'performance',
        'security_auditor',
        'data_quality_monitor',
        'unified_health_monitor',
    ]
    
    for domain in domains:
        regenerate_genie_benchmarks(domain)
    
    print("\n" + "=" * 70)
    print("✅ ALL BENCHMARKS REGENERATED WITH FULLY QUALIFIED NAMES")
    print("=" * 70)


if __name__ == "__main__":
    main()
