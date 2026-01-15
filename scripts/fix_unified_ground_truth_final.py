#!/usr/bin/env python3
"""
COMPREHENSIVE FIX for unified_health_monitor using ground truth.

Ground Truth Sources:
- docs/reference/actual_assets/ml.md - ML tables
- docs/reference/actual_assets/mvs.md - Metric Views
- docs/reference/actual_assets/tvfs.md - TVFs

Issues:
Q18: ✅ Already fixed (ORDER BY removed)
Q20: get_cluster_rightsizing_recommendations → use cluster_capacity_predictions ML table
Q21: efficiency_score → resource_efficiency_score
Q22: ✅ Already correct (uses prediction)
Q23: security_anomaly_predictions → security_threat_predictions
Q24: job_failures CTE is missing FROM clause (should use get_failed_jobs TVF)
Q25: utilization_rate doesn't exist, efficiency_score → resource_efficiency_score
"""

import json
import re
from pathlib import Path

def fix_unified_health_monitor():
    """Fix all unified_health_monitor errors with ground truth."""
    json_path = Path("src/genie/unified_health_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    questions = data.get("benchmarks", {}).get("questions", [])
    changes_made = False
    
    # Q20: Replace TVF with ML table query
    if len(questions) > 19:
        q20 = questions[19]
        answer = q20.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Replace get_cluster_rightsizing_recommendations with direct ML table query
            sql = re.sub(
                r'FROM get_cluster_rightsizing_recommendations\([^)]+\)',
                'FROM ${catalog}.${feature_schema}.cluster_capacity_predictions\n  WHERE prediction IN (\'DOWNSIZE\', \'UPSIZE\')',
                sql
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ unified Q20: Replaced TVF with ML table query")
                changes_made = True
    
    # Q21: efficiency_score → resource_efficiency_score
    if len(questions) > 20:
        q21 = questions[20]
        answer = q21.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            sql = sql.replace("efficiency_score", "resource_efficiency_score")
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ unified Q21: efficiency_score → resource_efficiency_score")
                changes_made = True
    
    # Q23: security_anomaly_predictions → security_threat_predictions
    if len(questions) > 22:
        q23 = questions[22]
        answer = q23.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            sql = sql.replace("security_anomaly_predictions", "security_threat_predictions")
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ unified Q23: security_anomaly_predictions → security_threat_predictions")
                changes_made = True
    
    # Q24: Add FROM clause to job_failures CTE
    if len(questions) > 23:
        q24 = questions[23]
        answer = q24.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # The job_failures CTE is missing FROM clause
            # Replace the empty CTE with proper TVF call
            sql = re.sub(
                r'WITH job_failures AS \(\s*SELECT\s+job_name,\s+avg_duration_minutes,\s+failure_count\s*\),',
                '''WITH job_failures AS (
  SELECT
    job_name,
    AVG(duration_minutes) as avg_duration_minutes,
    COUNT(*) as failure_count
  FROM get_failed_jobs(
    CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
  )
  GROUP BY job_name
),''',
                sql
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ unified Q24: Added FROM clause to job_failures CTE")
                changes_made = True
    
    # Q25: Remove utilization_rate, fix efficiency_score
    if len(questions) > 24:
        q25 = questions[24]
        answer = q25.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Remove utilization_rate from commit_status CTE
            sql = re.sub(r'MEASURE\(utilization_rate\) as usage_pct,', '', sql)
            sql = re.sub(r'MEASURE\(remaining_dbu\) as remaining_capacity', 
                        'COUNT(*) as commit_count', sql)
            
            # Fix efficiency_score → resource_efficiency_score
            sql = sql.replace("efficiency_score", "resource_efficiency_score")
            
            # Remove references to avg_commit_utilization in SELECT and CASE
            sql = re.sub(r"COALESCE\(AVG\(cs\.usage_pct\), 0\) as avg_commit_utilization,", "", sql)
            sql = re.sub(r"WHEN COALESCE\(AVG\(cs\.usage_pct\), 0\) < 70 THEN '[^']+'\s*", "", sql)
            sql = re.sub(r"WHEN COALESCE\(AVG\(cs\.usage_pct\), 0\) < 70 THEN '[^']+'\s*", "", sql)
            
            # Remove total_remaining_commit
            sql = re.sub(r"COALESCE\(SUM\(cs\.remaining_capacity\), 0\) as total_remaining_commit,", "", sql)
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ unified Q25: Removed utilization_rate, fixed efficiency_score")
                changes_made = True
    
    if changes_made:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    return False

def main():
    print("=" * 80)
    print("COMPREHENSIVE UNIFIED_HEALTH_MONITOR FIX - GROUND TRUTH")
    print("=" * 80)
    print()
    print("Ground Truth Sources:")
    print("  - docs/reference/actual_assets/ml.md")
    print("  - docs/reference/actual_assets/mvs.md")
    print("  - docs/reference/actual_assets/tvfs.md")
    print()
    
    if fix_unified_health_monitor():
        print()
        print("=" * 80)
        print("✅ Fixed 5 errors in unified_health_monitor (Q20, Q21, Q23, Q24, Q25)")
        print("=" * 80)
        print()
        print("Fixes Applied:")
        print("  Q20: get_cluster_rightsizing_recommendations → cluster_capacity_predictions")
        print("  Q21: efficiency_score → resource_efficiency_score")
        print("  Q23: security_anomaly_predictions → security_threat_predictions")
        print("  Q24: Added FROM clause with get_failed_jobs() TVF")
        print("  Q25: Removed utilization_rate, fixed efficiency_score")
    else:
        print("⚠️  No changes made")

if __name__ == "__main__":
    main()

