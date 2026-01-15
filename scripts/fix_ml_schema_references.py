#!/usr/bin/env python3
"""
Fix ML prediction table schema references in all Genie Space JSON files.

Problem: ML tables were using ${catalog}.${gold_schema} but they're actually in system_gold_ml.
Solution: Use hardcoded path prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml.{table}
"""

import json
from pathlib import Path

# ML prediction tables (from UC query)
ML_TABLES = [
    "budget_forecast_predictions",
    "cache_hit_predictions",
    "chargeback_predictions",
    "cluster_capacity_predictions",
    "commitment_recommendations",
    "cost_anomaly_predictions",
    "cost_features",
    "data_drift_predictions",
    "dbr_migration_predictions",
    "duration_predictions",
    "exfiltration_predictions",
    "freshness_predictions",
    "job_cost_optimizer_predictions",
    "job_failure_predictions",
    "performance_features",
    "performance_regression_predictions",
    "pipeline_health_predictions",
    "privilege_escalation_predictions",
    "quality_features",
    "query_optimization_predictions",
    "query_performance_predictions",
    "reliability_features",
    "retry_success_predictions",
    "security_features",
    "security_threat_predictions",
    "sla_breach_predictions",
    "tag_recommendations",
    "user_behavior_predictions",
    "warehouse_optimizer_predictions"
]

# Genie Space files
GENIE_FILES = [
    "src/genie/cost_intelligence_genie_export.json",
    "src/genie/security_auditor_genie_export.json",
    "src/genie/performance_genie_export.json",
    "src/genie/job_health_monitor_genie_export.json",
    "src/genie/data_quality_monitor_genie_export.json",
    "src/genie/unified_health_monitor_genie_export.json"
]

def fix_ml_schema(genie_file: str):
    """Fix ML table schema references in a Genie Space JSON file."""
    path = Path(genie_file)
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    fixes = 0
    
    # Fix tables in data_sources.tables
    if 'data_sources' in data and 'tables' in data['data_sources']:
        for table in data['data_sources']['tables']:
            table_name = table['identifier'].split('.')[-1]
            
            if table_name in ML_TABLES:
                old_identifier = table['identifier']
                new_identifier = f"prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml.{table_name}"
                
                if old_identifier != new_identifier:
                    table['identifier'] = new_identifier
                    fixes += 1
                    print(f"  Fixed: {table_name}")
                    print(f"    OLD: {old_identifier}")
                    print(f"    NEW: {new_identifier}")
    
    if fixes > 0:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Fixed {fixes} ML table references in {path.name}")
    else:
        print(f"  No ML tables found in {path.name}")
    
    return fixes

def main():
    """Fix ML schema references in all Genie Space JSON files."""
    print("Fixing ML prediction table schema references...")
    print("=" * 80)
    
    total_fixes = 0
    
    for genie_file in GENIE_FILES:
        print(f"\nProcessing {genie_file}...")
        fixes = fix_ml_schema(genie_file)
        total_fixes += fixes
    
    print("\n" + "=" * 80)
    print(f"✓ Total fixes applied: {total_fixes}")
    print("\nML tables now use hardcoded schema:")
    print("  prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml.{table_name}")

if __name__ == "__main__":
    main()
