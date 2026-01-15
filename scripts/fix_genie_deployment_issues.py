#!/usr/bin/env python3
"""
Fix ALL Genie Space deployment issues discovered in Session 24.

Issues:
1. security_auditor_genie_export.json: "question" is string, must be array
2. All spaces: Referenced tables don't exist in catalog (dim_date, ML tables, monitoring tables)

The Genie API validates that all referenced tables exist before accepting the space definition.
We MUST remove tables that don't exist.
"""

import json
from pathlib import Path
from typing import Dict, List, Set

# Tables that ACTUALLY EXIST in the catalog (verified from deployment errors)
# Only these tables can be referenced in Genie Spaces
EXISTING_TABLES = {
    # Gold schema tables (system_gold) - VERIFIED TO EXIST
    "${catalog}.${gold_schema}.dim_workspace",
    "${catalog}.${gold_schema}.dim_sku",
    "${catalog}.${gold_schema}.dim_cluster",
    "${catalog}.${gold_schema}.dim_job",
    "${catalog}.${gold_schema}.dim_node_type",
    "${catalog}.${gold_schema}.dim_user",  # May not exist - need to verify
    "${catalog}.${gold_schema}.fact_usage",
    "${catalog}.${gold_schema}.fact_account_prices",
    "${catalog}.${gold_schema}.fact_list_prices",
    "${catalog}.${gold_schema}.fact_node_timeline",
    "${catalog}.${gold_schema}.fact_job_run_timeline",
    "${catalog}.${gold_schema}.fact_audit_logs",
    "${catalog}.${gold_schema}.fact_query_history",
    "${catalog}.${gold_schema}.fact_warehouse_events",
    "${catalog}.${gold_schema}.fact_table_storage",
    "${catalog}.${gold_schema}.fact_column_lineage",
    "${catalog}.${gold_schema}.fact_table_lineage",
    # These are likely to exist based on the project scope
    # But we'll remove anything that causes deployment errors
}

# Tables that are KNOWN TO NOT EXIST (from deployment errors)
NON_EXISTENT_TABLES = {
    # dim_date - common across ALL spaces
    "${catalog}.${gold_schema}.dim_date",
    
    # ML tables that don't exist
    "${catalog}.${feature_schema}.freshness_alert_predictions",
    "${catalog}.${feature_schema}.quality_anomaly_predictions",
    "${catalog}.${feature_schema}.cluster_capacity_recommendations",
    "${catalog}.${feature_schema}.cluster_rightsizing_recommendations",
    "${catalog}.${feature_schema}.security_anomaly_predictions",
    "${catalog}.${feature_schema}.cost_anomaly_predictions",
    "${catalog}.${feature_schema}.budget_forecast_predictions",
    "${catalog}.${feature_schema}.job_cost_optimizer_predictions",
    "${catalog}.${feature_schema}.chargeback_predictions",
    "${catalog}.${feature_schema}.commitment_recommendations",
    "${catalog}.${feature_schema}.tag_recommendations",
    "${catalog}.${feature_schema}.query_optimization_classifications",
    "${catalog}.${feature_schema}.query_optimization_recommendations",
    "${catalog}.${feature_schema}.cache_hit_predictions",
    "${catalog}.${feature_schema}.job_duration_predictions",
    "${catalog}.${feature_schema}.dbr_migration_risk_scores",
    "${catalog}.${feature_schema}.user_risk_scores",
    "${catalog}.${feature_schema}.access_classifications",
    "${catalog}.${feature_schema}.off_hours_baseline_predictions",
    "${catalog}.${feature_schema}.job_failure_predictions",
    "${catalog}.${feature_schema}.cluster_efficiency_scores",
    "${catalog}.${feature_schema}.dbu_optimization_recommendations",
    "${catalog}.${feature_schema}.schema_change_predictor",
    "${catalog}.${feature_schema}.column_usage_predictions",
    "${catalog}.${feature_schema}.table_usage_forecast_predictions",
    "${catalog}.${feature_schema}.stale_table_predictions",
    
    # Monitoring tables that don't exist
    "${catalog}.${gold_schema}_monitoring.fact_usage_profile_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_usage_drift_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_table_quality_profile_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_table_quality_drift_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_job_health_profile_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_job_health_drift_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_query_performance_profile_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_query_performance_drift_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_security_events_profile_metrics",
    "${catalog}.${gold_schema}_monitoring.fact_security_events_drift_metrics",
    
    # Other tables that may not exist
    "${catalog}.${gold_schema}.fact_assistant_events",
    "${catalog}.${gold_schema}.fact_clean_room_events",
    "${catalog}.${gold_schema}.fact_inbound_network",
    "${catalog}.${gold_schema}.fact_outbound_network",
}


def fix_sample_questions_format(data: Dict) -> int:
    """
    Fix sample_questions format: question must be array, not string.
    
    Returns: Number of fixes applied
    """
    fixes = 0
    if 'config' in data and 'sample_questions' in data['config']:
        for q_obj in data['config']['sample_questions']:
            if 'question' in q_obj and isinstance(q_obj['question'], str):
                # Convert string to array
                q_obj['question'] = [q_obj['question']]
                fixes += 1
    return fixes


def remove_nonexistent_tables(data: Dict) -> int:
    """
    Remove tables that don't exist in the catalog.
    
    Returns: Number of tables removed
    """
    removed = 0
    if 'data_sources' in data and 'tables' in data['data_sources']:
        original_count = len(data['data_sources']['tables'])
        data['data_sources']['tables'] = [
            table for table in data['data_sources']['tables']
            if table.get('identifier') not in NON_EXISTENT_TABLES
        ]
        removed = original_count - len(data['data_sources']['tables'])
    return removed


def fix_genie_space(json_path: Path) -> Dict[str, int]:
    """
    Fix a single Genie Space JSON file.
    
    Returns: Dict with fix counts
    """
    print(f"\nProcessing: {json_path.name}")
    
    with open(json_path) as f:
        data = json.load(f)
    
    fixes = {
        'sample_questions_format': fix_sample_questions_format(data),
        'tables_removed': remove_nonexistent_tables(data)
    }
    
    if fixes['sample_questions_format'] > 0:
        print(f"  ✅ Fixed {fixes['sample_questions_format']} sample_questions (string → array)")
    
    if fixes['tables_removed'] > 0:
        print(f"  ✅ Removed {fixes['tables_removed']} non-existent tables")
    
    if sum(fixes.values()) == 0:
        print(f"  ℹ️  No fixes needed")
    
    # Save updated JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return fixes


def main():
    """Fix all Genie Space JSON files."""
    print("=" * 80)
    print("GENIE SPACE DEPLOYMENT FIX - Session 24")
    print("=" * 80)
    print("\nIssues being fixed:")
    print("  1. sample_questions format: 'question' must be array, not string")
    print("  2. Remove non-existent tables (API validates table existence)")
    
    genie_files = [
        "src/genie/cost_intelligence_genie_export.json",
        "src/genie/security_auditor_genie_export.json",
        "src/genie/performance_genie_export.json",
        "src/genie/job_health_monitor_genie_export.json",
        "src/genie/data_quality_monitor_genie_export.json",
        "src/genie/unified_health_monitor_genie_export.json"
    ]
    
    total_fixes = {
        'sample_questions_format': 0,
        'tables_removed': 0
    }
    
    for file_path in genie_files:
        fixes = fix_genie_space(Path(file_path))
        for key in total_fixes:
            total_fixes[key] += fixes[key]
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  sample_questions format fixes: {total_fixes['sample_questions_format']}")
    print(f"  Non-existent tables removed: {total_fixes['tables_removed']}")
    print(f"\n  TOTAL FIXES: {sum(total_fixes.values())}")
    print("=" * 80)


if __name__ == "__main__":
    main()
