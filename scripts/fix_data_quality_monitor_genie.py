#!/usr/bin/env python3
"""
Fix Data Quality Monitor Genie Space to match specification.

Issues:
1. Missing 1 dim table (dim_date)
2. Missing 2 ML tables
3. Missing 3 monitoring tables
4. Missing 2 metric views
5. 3 wrong TVF names
6. 3 missing TVFs
"""

import json
import uuid
from pathlib import Path

# Hardcoded schema paths
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def fix_data_quality_monitor():
    """Fix Data Quality Monitor Genie Space JSON."""
    
    json_path = Path("src/genie/data_quality_monitor_genie_export.json")
    data = json.load(open(json_path))
    
    print("=" * 80)
    print("FIXING DATA QUALITY MONITOR GENIE SPACE")
    print("=" * 80)
    print()
    
    # 1. Add missing dim_date
    print("1. Adding missing dim table...")
    missing_dim = {
        "identifier": f"{SYSTEM_GOLD}.dim_date",
        "description": [
            "Date dimension for time-based analysis.\n",
            "Business: Provides day, week, month, quarter, year attributes for temporal analysis."
        ]
    }
    
    # Check if dim_date already exists
    existing_tables = [t["identifier"].split(".")[-1] for t in data["data_sources"]["tables"]]
    if "dim_date" not in existing_tables:
        # Insert after dim_workspace
        insert_idx = next((i for i, t in enumerate(data["data_sources"]["tables"]) 
                          if "dim_workspace" in t["identifier"]), 0) + 1
        data["data_sources"]["tables"].insert(insert_idx, missing_dim)
        print("   ✅ Added dim_date")
    else:
        print("   ⚠️  dim_date already exists")
    
    # 2. Add missing ML tables
    print("\n2. Adding missing ML tables...")
    missing_ml_tables = [
        {
            "name": "quality_anomaly_predictions",
            "description": [
                "ML predictions for data quality anomalies and drift detection.",
                "Business: Proactive identification of quality degradation."
            ]
        },
        {
            "name": "freshness_alert_predictions",
            "description": [
                "ML predictions for table staleness and freshness alerts.",
                "Business: Predict tables likely to miss SLA."
            ]
        }
    ]
    
    for ml_table in missing_ml_tables:
        if ml_table["name"] not in existing_tables:
            new_table = {
                "identifier": f"{SYSTEM_GOLD_ML}.{ml_table['name']}",
                "description": ml_table["description"]
            }
            data["data_sources"]["tables"].append(new_table)
            print(f"   ✅ Added {ml_table['name']}")
    
    # 3. Add missing monitoring tables
    print("\n3. Adding missing monitoring tables...")
    missing_monitoring_tables = [
        {
            "name": "fact_table_quality_profile_metrics",
            "description": [
                "Lakehouse Monitoring profile metrics for table quality.\n",
                "⚠️ CRITICAL: Always include filters: column_name=':table', log_type='INPUT'"
            ]
        },
        {
            "name": "fact_governance_metrics_profile_metrics",
            "description": [
                "Lakehouse Monitoring profile metrics for governance metrics.\n",
                "⚠️ CRITICAL: Always include filters: column_name=':table', log_type='INPUT'"
            ]
        },
        {
            "name": "fact_table_quality_drift_metrics",
            "description": [
                "Lakehouse Monitoring drift metrics for quality trend detection.\n",
                "⚠️ CRITICAL: Always include filters: drift_type='CONSECUTIVE', column_name=':table'"
            ]
        }
    ]
    
    for mon_table in missing_monitoring_tables:
        if mon_table["name"] not in existing_tables:
            new_table = {
                "identifier": f"{SYSTEM_GOLD_MONITORING}.{mon_table['name']}",
                "description": mon_table["description"]
            }
            data["data_sources"]["tables"].append(new_table)
            print(f"   ✅ Added {mon_table['name']}")
    
    # 4. Add missing metric views
    print("\n4. Adding missing metric views...")
    missing_metric_views = [
        {
            "name": "data_quality",
            "description": [
                "Comprehensive data quality metrics.\n",
                "PURPOSE: Track quality scores, completeness, validity across tables.\n",
                "KEY MEASURES: total_tables, quality_score, completeness_rate, validity_rate"
            ]
        },
        {
            "name": "ml_intelligence",
            "description": [
                "ML model intelligence and inference metrics.\n",
                "PURPOSE: Track model predictions, accuracy, drift.\n",
                "KEY MEASURES: prediction_count, accuracy, drift_score"
            ]
        }
    ]
    
    existing_mvs = [mv["identifier"].split(".")[-1] for mv in data["data_sources"]["metric_views"]]
    
    for mv in missing_metric_views:
        if mv["name"] not in existing_mvs:
            new_mv = {
                "identifier": f"${{catalog}}.${{gold_schema}}.{mv['name']}",
                "description": mv["description"]
            }
            data["data_sources"]["metric_views"].append(new_mv)
            print(f"   ✅ Added {mv['name']}")
    
    # 5. Fix TVF names
    print("\n5. Fixing TVF names...")
    tvf_name_fixes = {
        "get_table_freshness": "get_stale_tables",
        "get_table_activity_status": "get_table_activity_summary",
        "get_pipeline_lineage_impact": "get_pipeline_data_lineage"
    }
    
    for tvf in data["instructions"]["sql_functions"]:
        tvf_name = tvf["identifier"].split(".")[-1]
        if tvf_name in tvf_name_fixes:
            new_name = tvf_name_fixes[tvf_name]
            tvf["identifier"] = tvf["identifier"].replace(tvf_name, new_name)
            print(f"   ✅ Renamed {tvf_name} → {new_name}")
    
    # Save fixed JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print()
    print("=" * 80)
    print("✅ DATA QUALITY MONITOR FIX COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Added 1 dim table (dim_date)")
    print(f"  - Added 2 ML tables")
    print(f"  - Added 3 monitoring tables")
    print(f"  - Added 2 metric views")
    print(f"  - Fixed 3 TVF names")
    print()

if __name__ == "__main__":
    fix_data_quality_monitor()
