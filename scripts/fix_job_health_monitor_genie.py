#!/usr/bin/env python3
"""
Fix Job Health Monitor Genie Space to match specification.

Issues:
1. Missing 1 dim table (dim_date)
2. Missing 4 ML tables (duration_predictions, sla_breach_predictions, retry_success_predictions, pipeline_health_predictions)
3. Wrong ML table names (job_duration_predictions, job_retry_predictions)
4. Missing 3 TVFs
5. Wrong TVF name (get_job_failure_cost → get_job_failure_costs)
"""

import json
import uuid
from pathlib import Path

# Hardcoded schema paths
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def fix_job_health_monitor():
    """Fix Job Health Monitor Genie Space JSON."""
    
    json_path = Path("src/genie/job_health_monitor_genie_export.json")
    data = json.load(open(json_path))
    
    print("=" * 80)
    print("FIXING JOB HEALTH MONITOR GENIE SPACE")
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
        data["data_sources"]["tables"].insert(4, missing_dim)  # Insert after dim_workspace
        print("   ✅ Added dim_date")
    else:
        print("   ⚠️  dim_date already exists")
    
    # 2. Fix ML table names (rename existing ones)
    print("\n2. Fixing ML table names...")
    ml_name_fixes = {
        "job_duration_predictions": "duration_predictions",
        "job_retry_predictions": "retry_success_predictions"
    }
    
    for table in data["data_sources"]["tables"]:
        table_name = table["identifier"].split(".")[-1]
        if table_name in ml_name_fixes:
            new_name = ml_name_fixes[table_name]
            table["identifier"] = f"{SYSTEM_GOLD_ML}.{new_name}"
            print(f"   ✅ Renamed {table_name} → {new_name}")
    
    # 3. Add missing ML tables
    print("\n3. Adding missing ML tables...")
    missing_ml_tables = [
        {
            "name": "sla_breach_predictions",
            "description": [
                "ML predictions for SLA breach probability.",
                "Business: Predict whether jobs will miss their SLA thresholds."
            ]
        },
        {
            "name": "pipeline_health_predictions",
            "description": [
                "ML predictions for overall pipeline/job health scores (0-100).",
                "Business: Comprehensive health assessment for reliability dashboard."
            ]
        }
    ]
    
    existing_ml = [t["identifier"].split(".")[-1] for t in data["data_sources"]["tables"] if "prediction" in t["identifier"]]
    
    for ml_table in missing_ml_tables:
        if ml_table["name"] not in existing_ml:
            new_table = {
                "identifier": f"{SYSTEM_GOLD_ML}.{ml_table['name']}",
                "description": ml_table["description"]
            }
            data["data_sources"]["tables"].append(new_table)
            print(f"   ✅ Added {ml_table['name']}")
    
    # 4. Fix TVF names
    print("\n4. Fixing TVF names...")
    for tvf in data["instructions"]["sql_functions"]:
        tvf_name = tvf["identifier"].split(".")[-1]
        if tvf_name == "get_job_failure_cost":
            tvf["identifier"] = tvf["identifier"].replace("get_job_failure_cost", "get_job_failure_costs")
            print(f"   ✅ Renamed get_job_failure_cost → get_job_failure_costs")
    
    # 5. Add missing TVFs
    print("\n5. Adding missing TVFs...")
    missing_tvfs = [
        "get_job_run_details",
        "get_job_data_quality_status"
    ]
    
    existing_tvfs = [tvf["identifier"].split(".")[-1] for tvf in data["instructions"]["sql_functions"]]
    
    for tvf_name in missing_tvfs:
        if tvf_name not in existing_tvfs:
            new_tvf = {
                "id": uuid.uuid4().hex,
                "identifier": f"${{catalog}}.${{gold_schema}}.{tvf_name}"
            }
            data["instructions"]["sql_functions"].append(new_tvf)
            print(f"   ✅ Added {tvf_name}")
    
    # Save fixed JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print()
    print("=" * 80)
    print("✅ JOB HEALTH MONITOR FIX COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Added 1 dim table (dim_date)")
    print(f"  - Fixed 2 ML table names")
    print(f"  - Added 2 missing ML tables")
    print(f"  - Fixed 1 TVF name")
    print(f"  - Added 2 missing TVFs")
    print()

if __name__ == "__main__":
    fix_job_health_monitor()
