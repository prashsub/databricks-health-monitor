#!/usr/bin/env python3
"""
Fix final validation errors after Q20-Q25 sync.

Errors to fix:
1. performance Q16 & unified Q18: Already fixed, may need reconfirmation
2. unified Q23: TABLE_NOT_FOUND
3. unified Q24: SYNTAX_ERROR (missing ))
4. data_quality Q14-Q25: Multiple SYNTAX_ERROR and TABLE_NOT_FOUND issues
"""

import json
import re
from pathlib import Path

def fix_data_quality_monitor():
    """Fix all data_quality_monitor errors."""
    json_path = Path("src/genie/data_quality_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    questions = data.get("benchmarks", {}).get("questions", [])
    changes_made = False
    
    # Q14, Q15, Q17: Remove GROUP BY sku_name (causes sku_name resolution issues)
    for idx in [13, 14, 16]:  # 0-indexed
        if len(questions) > idx:
            q = questions[idx]
            answer = q.get("answer", [])
            if answer:
                sql = answer[0].get("content", [""])[0]
                old_sql = sql
                
                # Remove GROUP BY sku_name line
                sql = re.sub(r'\s*GROUP BY sku_name\s*', '', sql)
                
                if sql != old_sql:
                    answer[0]["content"] = [sql]
                    print(f"✅ data_quality Q{idx+1}: Removed GROUP BY sku_name")
                    changes_made = True
    
    # Q16: Already fixed earlier (check if fix is present)
    if len(questions) > 15:
        q16 = questions[15]
        answer = q16.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            if "mv_data_quality" in sql:
                # Need to use source table in CTE
                sql = sql.replace(
                    "FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.mv_data_quality",
                    "FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_data_quality"
                )
                answer[0]["content"] = [sql]
                print("✅ data_quality Q16: Changed mv_data_quality → fact_data_quality")
                changes_made = True
    
    # Q18: Fix monitoring table schema
    if len(questions) > 17:
        q18 = questions[17]
        answer = q18.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            sql = sql.replace(
                "dev_prashanth_subrahmanyam_system_gold.fact_table_lineage_drift_metrics",
                "dev_prashanth_subrahmanyam_system_gold_monitoring.fact_table_lineage_drift_metrics"
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ data_quality Q18: Fixed monitoring table schema")
                changes_made = True
    
    # Q20: Fix evaluation_date column (doesn't exist in mv_data_quality)
    if len(questions) > 19:
        q20 = questions[19]
        answer = q20.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Remove WHERE evaluation_date filter (column doesn't exist)
            sql = re.sub(r'\s*WHERE evaluation_date[^\n]+', '', sql)
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ data_quality Q20: Removed evaluation_date filter")
                changes_made = True
    
    # Q21-Q25: Fix extra `)` after TVF calls in CTEs
    for idx in range(20, 25):  # Q21-Q25 (0-indexed)
        if len(questions) > idx:
            q = questions[idx]
            answer = q.get("answer", [])
            if answer:
                sql = answer[0].get("content", [""])[0]
                old_sql = sql
                
                # Pattern: FROM get_func(params))\n),
                # Should be: FROM get_func(params)\n),
                sql = re.sub(r'\(([^)]+)\)\)\s*\n\s*\),', r'(\1)\n),', sql)
                
                if sql != old_sql:
                    answer[0]["content"] = [sql]
                    print(f"✅ data_quality Q{idx+1}: Fixed extra `)` after TVF")
                    changes_made = True
    
    if changes_made:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    return False

def fix_unified_health_monitor():
    """Fix unified_health_monitor errors."""
    json_path = Path("src/genie/unified_health_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    questions = data.get("benchmarks", {}).get("questions", [])
    changes_made = False
    
    # Q18: Already fixed in Session 12 (verify)
    if len(questions) > 17:
        q18 = questions[17]
        answer = q18.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            # Should not have ORDER BY
            if "ORDER BY" in sql:
                sql = re.sub(r'\s*ORDER BY[^\n]+', '', sql)
                answer[0]["content"] = [sql]
                print("✅ unified Q18: Removed ORDER BY")
                changes_made = True
    
    # Q23: Fix ML table schema
    if len(questions) > 22:
        q23 = questions[22]
        answer = q23.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            sql = sql.replace(
                "dev_prashanth_subrahmanyam_system_gold_ml.security_anomaly_predictions",
                "dev_prashanth_subrahmanyam_system_gold_ml_feature.security_anomaly_predictions"
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ unified Q23: Fixed ML table schema")
                changes_made = True
    
    # Q24: Fix missing `)` (SYNTAX_ERROR near COALESCE)
    if len(questions) > 23:
        q24 = questions[23]
        answer = q24.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Find the line with "FROM get_failed_jobs" and ensure it has proper closing
            # Pattern: get_failed_jobs(params)\n),
            sql = re.sub(r'get_failed_jobs\(([^)]+)\)\s*\n\s*\),', r'get_failed_jobs(\1)\n),', sql)
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ unified Q24: Fixed syntax near COALESCE")
                changes_made = True
    
    if changes_made:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    return False

def main():
    print("=" * 80)
    print("FIXING FINAL VALIDATION ERRORS")
    print("=" * 80)
    print()
    
    success_count = 0
    
    if fix_data_quality_monitor():
        success_count += 1
    
    if fix_unified_health_monitor():
        success_count += 1
    
    print()
    print("=" * 80)
    print(f"✅ Fixed errors in {success_count}/2 Genie spaces")
    print("=" * 80)

if __name__ == "__main__":
    main()

