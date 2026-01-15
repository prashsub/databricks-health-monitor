#!/usr/bin/env python3
"""
Update the Data Assets section of each Genie Space spec file (.md) 
based on the actual_assets_inventory.json.

This script regenerates ONLY the Data Assets sections, preserving all other content.
"""

import json
import re
from pathlib import Path
from typing import Dict, List

# Paths
INVENTORY_PATH = Path("src/genie/actual_assets_inventory.json")
GENIE_DIR = Path("src/genie")

def load_inventory():
    """Load the verified assets inventory."""
    with open(INVENTORY_PATH) as f:
        return json.load(f)

def generate_metric_views_section(metric_views: List[str]) -> str:
    """Generate the Metric Views markdown table."""
    if not metric_views:
        return ""
    
    # Mapping of metric view names to their purpose and key measures
    mv_info = {
        'mv_cost_analytics': ('Comprehensive cost analytics', 'total_cost, total_dbus, cost_7d, cost_30d, serverless_percentage'),
        'mv_commit_tracking': ('Contract/commit monitoring', 'commit_amount, consumed_amount, remaining_amount, burn_rate_daily'),
        'mv_job_performance': ('Job execution performance metrics', 'success_rate, failure_rate, avg_duration, p95_duration'),
        'mv_query_performance': ('Query execution analytics', 'total_queries, avg_duration, p95_duration, cache_hit_rate'),
        'mv_cluster_utilization': ('Cluster resource utilization', 'avg_cpu_utilization, avg_memory_utilization'),
        'mv_cluster_efficiency': ('Cluster efficiency metrics', 'efficiency_score, cost_per_dbu'),
        'mv_security_events': ('Security event monitoring', 'total_events, failed_events, risk_score'),
        'mv_governance_analytics': ('Data governance analytics', 'table_count, lineage_coverage, classification_coverage'),
        'mv_data_quality': ('Data quality metrics', 'quality_score, freshness_score, completeness_score'),
        'mv_ml_intelligence': ('ML model insights', 'model_count, inference_count, prediction_quality'),
    }
    
    lines = [
        "### Metric Views (PRIMARY - Use First)",
        "",
        "| Metric View Name | Purpose | Key Measures |",
        "|------------------|---------|--------------|"
    ]
    
    for mv in sorted(metric_views):
        purpose, measures = mv_info.get(mv, ('Analytics', 'Various measures'))
        lines.append(f"| `{mv}` | {purpose} | {measures} |")
    
    return "\n".join(lines)

def generate_tvfs_section(tvfs: List[str]) -> str:
    """Generate the TVFs markdown table."""
    if not tvfs:
        return ""
    
    # TVF info mapping
    tvf_info = {
        'get_top_cost_contributors': ('Top N cost contributors', '"top workspaces by cost"'),
        'get_cost_trend_by_sku': ('Daily cost by SKU', '"cost trend by SKU"'),
        'get_cost_by_owner': ('Cost allocation by owner', '"cost by owner", "chargeback"'),
        'get_cost_by_tag': ('Tag-based cost allocation', '"cost by team"'),
        'get_untagged_resources': ('Resources without tags', '"untagged resources"'),
        'get_cost_anomalies': ('Cost anomaly detection', '"cost anomalies"'),
        'get_cost_week_over_week': ('Weekly cost trends', '"week over week"'),
        'get_spend_by_custom_tags': ('Multi-tag cost analysis', '"cost by tags"'),
        'get_tag_coverage': ('Tag coverage metrics', '"tag coverage"'),
        'get_most_expensive_jobs': ('Top expensive jobs', '"job costs"'),
        'get_cost_growth_analysis': ('Cost growth analysis', '"cost growth"'),
        'get_cost_growth_by_period': ('Period-over-period growth', '"period comparison"'),
        'get_cost_forecast_summary': ('Cost forecasting', '"forecast", "predict"'),
        'get_all_purpose_cluster_cost': ('ALL_PURPOSE cluster costs', '"cluster costs"'),
        'get_commit_vs_actual': ('Commit tracking', '"commit status"'),
        'get_cost_mtd_summary': ('Month-to-date summary', '"MTD cost"'),
        'get_cluster_right_sizing_recommendations': ('Cluster right-sizing', '"right-sizing"'),
        'get_job_spend_trend_analysis': ('Job spend trends', '"job spend trend"'),
        'get_failed_jobs': ('Failed job list', '"failed jobs"'),
        'get_job_success_rate': ('Job success metrics', '"success rate"'),
        'get_job_duration_percentiles': ('Duration percentiles', '"job duration"'),
        'get_job_sla_compliance': ('SLA compliance', '"SLA compliance"'),
        'get_job_failure_trends': ('Failure trends', '"failure trends"'),
        'get_job_outlier_runs': ('Outlier job runs', '"outlier runs"'),
        'get_job_retry_analysis': ('Retry analysis', '"retry analysis"'),
        'get_job_failure_costs': ('Failure costs', '"failure costs"'),
        'get_job_repair_costs': ('Repair costs', '"repair costs"'),
        'get_job_run_details': ('Job run details', '"run details"'),
        'get_job_run_duration_analysis': ('Duration analysis', '"duration analysis"'),
        'get_jobs_without_autoscaling': ('Jobs without autoscaling', '"autoscaling disabled"'),
        'get_jobs_on_legacy_dbr': ('Jobs on legacy DBR', '"legacy DBR"'),
        'get_slow_queries': ('Slow query analysis', '"slow queries"'),
        'get_query_latency_percentiles': ('Query latency percentiles', '"query latency"'),
        'get_warehouse_utilization': ('Warehouse utilization', '"warehouse utilization"'),
        'get_query_volume_trends': ('Query volume trends', '"query volume"'),
        'get_query_efficiency': ('Query efficiency', '"query efficiency"'),
        'get_query_efficiency_analysis': ('Query efficiency analysis', '"efficiency analysis"'),
        'get_failed_queries': ('Failed queries', '"failed queries"'),
        'get_high_spill_queries': ('High spill queries', '"spill queries"'),
        'get_cluster_utilization': ('Cluster utilization', '"cluster utilization"'),
        'get_cluster_resource_metrics': ('Cluster resource metrics', '"cluster resources"'),
        'get_underutilized_clusters': ('Underutilized clusters', '"underutilized"'),
        'get_user_query_summary': ('User query summary', '"user queries"'),
        'get_user_activity_summary': ('User activity summary', '"user activity"'),
        'get_sensitive_table_access': ('Sensitive table access', '"sensitive access"'),
        'get_permission_changes': ('Permission changes', '"permission changes"'),
        'get_security_events_timeline': ('Security events timeline', '"security events"'),
        'get_off_hours_activity': ('Off-hours activity', '"off hours"'),
        'get_failed_actions': ('Failed actions', '"failed actions"'),
        'get_table_access_audit': ('Table access audit', '"access audit"'),
        'get_ip_address_analysis': ('IP address analysis', '"IP analysis"'),
        'get_service_account_audit': ('Service account audit', '"service accounts"'),
        'get_user_activity_patterns': ('User activity patterns', '"activity patterns"'),
        'get_table_freshness': ('Table freshness', '"table freshness"'),
        'get_data_freshness_by_domain': ('Freshness by domain', '"freshness by domain"'),
        'get_tables_failing_quality': ('Tables failing quality', '"failing quality"'),
        'get_pipeline_data_lineage': ('Pipeline data lineage', '"data lineage"'),
        'get_data_quality_summary': ('Data quality summary', '"quality summary"'),
        'get_job_data_quality_status': ('Job data quality status', '"job quality"'),
        'get_table_activity_status': ('Table activity status', '"table activity"'),
    }
    
    lines = [
        f"### Table-Valued Functions ({len(tvfs)} TVFs)",
        "",
        "| Function Name | Purpose | When to Use |",
        "|---------------|---------|-------------|"
    ]
    
    for tvf in sorted(tvfs):
        purpose, when_to_use = tvf_info.get(tvf, ('Specialized query', '"query for specific data"'))
        lines.append(f"| `{tvf}` | {purpose} | {when_to_use} |")
    
    return "\n".join(lines)

def generate_ml_tables_section(ml_tables: List[str]) -> str:
    """Generate the ML Tables markdown section."""
    if not ml_tables:
        return ""
    
    ml_info = {
        'cost_anomaly_predictions': ('Detected cost anomalies', 'Cost Anomaly Detector'),
        'budget_forecast_predictions': ('Cost forecasts', 'Budget Forecaster'),
        'job_cost_optimizer_predictions': ('Job cost optimization', 'Job Cost Optimizer'),
        'chargeback_predictions': ('Cost allocation', 'Chargeback Attribution'),
        'commitment_recommendations': ('Commit level recommendations', 'Commitment Recommender'),
        'tag_recommendations': ('Suggested tags', 'Tag Recommender'),
        'job_failure_predictions': ('Job failure predictions', 'Job Failure Predictor'),
        'retry_success_predictions': ('Retry success likelihood', 'Retry Success Predictor'),
        'sla_breach_predictions': ('SLA breach risk', 'SLA Breach Predictor'),
        'duration_predictions': ('Job duration predictions', 'Duration Predictor'),
        'query_performance_predictions': ('Query performance predictions', 'Query Performance Predictor'),
        'query_optimization_predictions': ('Query optimization suggestions', 'Query Optimizer'),
        'cache_hit_predictions': ('Cache hit predictions', 'Cache Hit Predictor'),
        'cluster_capacity_predictions': ('Cluster capacity needs', 'Capacity Planner'),
        'warehouse_optimizer_predictions': ('Warehouse optimization', 'Warehouse Optimizer'),
        'performance_regression_predictions': ('Performance regressions', 'Regression Detector'),
        'dbr_migration_predictions': ('DBR migration risk', 'Migration Analyzer'),
        'security_threat_predictions': ('Security threats', 'Threat Detector'),
        'user_behavior_predictions': ('User behavior anomalies', 'Behavior Analyzer'),
        'privilege_escalation_predictions': ('Privilege escalation risk', 'Privilege Analyzer'),
        'exfiltration_predictions': ('Data exfiltration risk', 'Exfiltration Detector'),
        'data_drift_predictions': ('Data drift detection', 'Drift Detector'),
        'freshness_predictions': ('Data freshness predictions', 'Freshness Predictor'),
        'pipeline_health_predictions': ('Pipeline health', 'Pipeline Health Monitor'),
    }
    
    lines = [
        f"### ML Prediction Tables ({len(ml_tables)} Models)",
        "",
        "| Table Name | Purpose | Model |",
        "|---|---|---|"
    ]
    
    for table in sorted(ml_tables):
        purpose, model = ml_info.get(table, ('ML predictions', 'ML Model'))
        lines.append(f"| `{table}` | {purpose} | {model} |")
    
    return "\n".join(lines)

def generate_monitoring_tables_section(monitoring_tables: List[str]) -> str:
    """Generate the Lakehouse Monitoring tables section."""
    if not monitoring_tables:
        return ""
    
    monitoring_info = {
        'fact_usage_profile_metrics': 'Cost profile metrics (total_daily_cost, serverless_ratio)',
        'fact_usage_drift_metrics': 'Cost drift detection (cost_drift_pct)',
        'fact_job_run_timeline_profile_metrics': 'Job execution profile metrics',
        'fact_job_run_timeline_drift_metrics': 'Job execution drift detection',
        'fact_query_history_profile_metrics': 'Query execution profile metrics',
        'fact_query_history_drift_metrics': 'Query execution drift detection',
        'fact_node_timeline_profile_metrics': 'Node utilization profile metrics',
        'fact_node_timeline_drift_metrics': 'Node utilization drift detection',
        'fact_audit_logs_profile_metrics': 'Security event profile metrics',
        'fact_audit_logs_drift_metrics': 'Security event drift detection',
        'fact_table_lineage_profile_metrics': 'Table lineage profile metrics',
        'fact_table_lineage_drift_metrics': 'Table lineage drift detection',
    }
    
    lines = [
        "### Lakehouse Monitoring Tables",
        "",
        "| Table Name | Purpose |",
        "|------------|---------|"
    ]
    
    for table in sorted(monitoring_tables):
        purpose = monitoring_info.get(table, 'Monitoring metrics')
        lines.append(f"| `{table}` | {purpose} |")
    
    return "\n".join(lines)

def generate_dimension_tables_section(dimensions: List[str]) -> str:
    """Generate the Dimension Tables section."""
    if not dimensions:
        return ""
    
    dim_info = {
        'dim_workspace': ('Workspace details', 'workspace_id, workspace_name, region'),
        'dim_sku': ('SKU reference', 'sku_name, sku_category, is_serverless'),
        'dim_cluster': ('Cluster metadata', 'cluster_id, cluster_name, node_type_id'),
        'dim_node_type': ('Node specifications', 'node_type_id, num_cores, memory_gb'),
        'dim_job': ('Job metadata', 'job_id, name, creator_id'),
        'dim_job_task': ('Job task metadata', 'task_key, task_type'),
        'dim_warehouse': ('Warehouse details', 'warehouse_id, warehouse_name'),
        'dim_user': ('User details', 'user_id, user_name, email'),
        'dim_pipeline': ('Pipeline metadata', 'pipeline_id, pipeline_name'),
        'dim_experiment': ('ML experiment details', 'experiment_id, experiment_name'),
        'dim_served_entities': ('Model serving entities', 'entity_id, entity_name'),
    }
    
    lines = [
        f"### Dimension Tables ({len(dimensions)} Tables)",
        "",
        "| Table Name | Purpose | Key Columns |",
        "|---|---|---|"
    ]
    
    for table in sorted(dimensions):
        purpose, columns = dim_info.get(table, ('Reference data', 'Various'))
        lines.append(f"| `{table}` | {purpose} | {columns} |")
    
    return "\n".join(lines)

def generate_fact_tables_section(facts: List[str]) -> str:
    """Generate the Fact Tables section."""
    if not facts:
        return ""
    
    fact_info = {
        'fact_usage': ('Primary billing usage', 'Daily usage by workspace/SKU'),
        'fact_account_prices': ('Account-specific pricing', 'Per SKU per account'),
        'fact_list_prices': ('List prices over time', 'Per SKU per date'),
        'fact_node_timeline': ('Cluster node usage', 'Per node per interval'),
        'fact_job_run_timeline': ('Job execution history', 'Per job run'),
        'fact_job_task_run_timeline': ('Task execution history', 'Per task run'),
        'fact_query_history': ('Query execution history', 'Per query execution'),
        'fact_warehouse_events': ('Warehouse events', 'Per warehouse event'),
        'fact_audit_logs': ('Security audit logs', 'Per audit event'),
        'fact_table_lineage': ('Table lineage', 'Per lineage relationship'),
        'fact_inbound_network': ('Inbound network traffic', 'Per network event'),
        'fact_outbound_network': ('Outbound network traffic', 'Per network event'),
        'fact_dq_monitoring': ('Data quality monitoring', 'Per quality check'),
        'fact_data_quality_monitoring_table_results': ('DQ table results', 'Per table check'),
    }
    
    lines = [
        f"### Fact Tables ({len(facts)} Tables)",
        "",
        "| Table Name | Purpose | Grain |",
        "|---|---|---|"
    ]
    
    for table in sorted(facts):
        purpose, grain = fact_info.get(table, ('Transaction data', 'Per event'))
        lines.append(f"| `{table}` | {purpose} | {grain} |")
    
    return "\n".join(lines)

def generate_data_assets_section(domain: Dict) -> str:
    """Generate the complete Data Assets section."""
    sections = []
    
    # Metric Views
    metric_views = domain.get('metric_views', [])
    if metric_views:
        sections.append(generate_metric_views_section(metric_views))
    
    # TVFs
    tvfs = domain.get('tvfs', [])
    if tvfs:
        sections.append(generate_tvfs_section(tvfs))
    
    # ML Tables
    ml_tables = domain.get('ml_tables', [])
    if ml_tables:
        sections.append(generate_ml_tables_section(ml_tables))
    
    # Monitoring Tables
    monitoring_tables = domain.get('monitoring_tables', [])
    if monitoring_tables:
        sections.append(generate_monitoring_tables_section(monitoring_tables))
    
    # Dimension Tables
    dimensions = domain.get('tables', {}).get('dimensions', [])
    if dimensions:
        sections.append(generate_dimension_tables_section(dimensions))
    
    # Fact Tables
    facts = domain.get('tables', {}).get('facts', [])
    if facts:
        sections.append(generate_fact_tables_section(facts))
    
    return "\n\n".join(sections)

def update_spec_file(spec_path: Path, domain: Dict) -> bool:
    """Update a spec file's Data Assets section."""
    with open(spec_path) as f:
        content = f.read()
    
    # Generate new Data Assets section
    new_data_assets = generate_data_assets_section(domain)
    
    # Find and replace the Data Assets section
    # Pattern: From "## ████ SECTION D: DATA ASSETS ████" to next "## ████ SECTION"
    pattern = r'(## ████ SECTION D: DATA ASSETS ████\s*)(.*?)(## ████ SECTION [EF]:)'
    
    replacement = f'\\1\n\n{new_data_assets}\n\n---\n\n\\3'
    
    new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
    
    if count > 0:
        with open(spec_path, 'w') as f:
            f.write(new_content)
        return True
    
    return False

def main():
    print("=" * 80)
    print("UPDATING GENIE SPEC FILE DATA ASSETS SECTIONS")
    print("=" * 80)
    
    inventory = load_inventory()
    
    genie_spaces = {
        'cost_intelligence': 'cost_intelligence_genie.md',
        'job_health_monitor': 'job_health_monitor_genie.md',
        'performance': 'performance_genie.md',
        'security_auditor': 'security_auditor_genie.md',
        'data_quality_monitor': 'data_quality_monitor_genie.md',
        'unified_health_monitor': 'unified_health_monitor_genie.md'
    }
    
    updated = 0
    failed = 0
    
    for space_key, md_file in genie_spaces.items():
        md_path = GENIE_DIR / md_file
        
        if not md_path.exists():
            print(f"  Skipped: {md_file} not found")
            continue
        
        domain = inventory.get('domain_mapping', {}).get(space_key, {})
        
        if not domain:
            print(f"  Skipped: {space_key} not in inventory")
            continue
        
        if update_spec_file(md_path, domain):
            updated += 1
            print(f"  Updated: {md_file}")
            
            # Print summary
            tables = domain.get('tables', {})
            print(f"    - {len(domain.get('metric_views', []))} metric views")
            print(f"    - {len(domain.get('tvfs', []))} TVFs")
            print(f"    - {len(domain.get('ml_tables', []))} ML tables")
            print(f"    - {len(domain.get('monitoring_tables', []))} monitoring tables")
            print(f"    - {len(tables.get('dimensions', []))} dimension tables")
            print(f"    - {len(tables.get('facts', []))} fact tables")
        else:
            failed += 1
            print(f"  Failed: {md_file} - Could not locate Data Assets section")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Updated: {updated}")
    print(f"  Failed: {failed}")
    
    if updated > 0:
        print("\n  Next steps:")
        print("  1. Review the updated spec files")
        print("  2. Commit: git add src/genie/*.md && git commit -m 'Align spec files with inventory'")

if __name__ == "__main__":
    main()
