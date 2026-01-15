#!/usr/bin/env python3
"""
Fix job_health_monitor Genie space errors (2 fixes)
- Q19 & Q25: Fix monitoring schema reference (add _monitoring)
"""

import json
import re
from pathlib import Path

def fix_job_health_monitor():
    """Fix both job_health_monitor monitoring schema errors."""
    
    json_path = Path("src/genie/job_health_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    questions = data.get("benchmarks", {}).get("questions", [])
    changes_made = False
    
    print("=" * 80)
    print("FIXING JOB_HEALTH_MONITOR ERRORS")
    print("=" * 80)
    
    # Fix Q19: profile_metrics table schema
    if len(questions) >= 19:
        q19 = questions[18]
        answer = q19.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Fix: ${gold_schema}. → ${gold_schema}_monitoring.
            sql = sql.replace(
                "${gold_schema}.fact_job_run_timeline_profile_metrics",
                "${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics"
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("\n✅ Q19: Fixed monitoring schema reference")
                print(f"   Changed: ${{gold_schema}}.fact_job_run_timeline_profile_metrics")
                print(f"         → ${{gold_schema}}_monitoring.fact_job_run_timeline_profile_metrics")
                changes_made = True
    
    # Fix Q25: drift_metrics table schema
    if len(questions) >= 25:
        q25 = questions[24]
        answer = q25.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Fix: ${gold_schema}. → ${gold_schema}_monitoring.
            sql = sql.replace(
                "${gold_schema}.fact_job_run_timeline_drift_metrics",
                "${gold_schema}_monitoring.fact_job_run_timeline_drift_metrics"
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("\n✅ Q25: Fixed monitoring schema reference")
                print(f"   Changed: ${{gold_schema}}.fact_job_run_timeline_drift_metrics")
                print(f"         → ${{gold_schema}}_monitoring.fact_job_run_timeline_drift_metrics")
                changes_made = True
    
    if changes_made:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        print("\n" + "=" * 80)
        print("✅ JOB_HEALTH_MONITOR FIXES COMPLETE")
        print("=" * 80)
        print(f"Updated: {json_path}")
        return True
    else:
        print("\n⚠️  No changes needed")
        return False

if __name__ == "__main__":
    success = fix_job_health_monitor()
    exit(0 if success else 1)

