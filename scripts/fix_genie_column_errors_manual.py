#!/usr/bin/env python3
"""
Genie Space COLUMN_NOT_FOUND Manual Fixes
Based on systematic ground truth analysis of @docs/reference/actual_assets/

This script applies HIGH confidence fixes for 7 COLUMN_NOT_FOUND errors.
"""

import json
import os
import re


def fix_cost_intelligence_q22(content):
    """
    Fix: cost_intelligence Q22 - SKU-level cost efficiency analysis
    
    Issues:
    1. MEASURE(scCROSS.total_cost) in CTE → MEASURE(total_cost)
    2. scCROSS.total_cost in main SELECT → scCROSS.total_sku_cost
    3. Alias inconsistency: sc. → scCROSS.
    """
    question_id = "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a6"
    
    for question in content["benchmarks"]["questions"]:
        if question["id"] == question_id:
            if "answer" in question and len(question["answer"]) > 0:
                sql = question["answer"][0]["content"][0]
                
                # Fix 1: MEASURE(scCROSS.total_cost) → MEASURE(total_cost) in CTE
                sql = sql.replace("MEASURE(scCROSS.total_cost)", "MEASURE(total_cost)")
                
                # Fix 2: scCROSS.total_cost → scCROSS.total_sku_cost (in main SELECT and CASE statements)
                sql = sql.replace("scCROSS.total_cost", "scCROSS.total_sku_cost")
                
                # Fix 3: Inconsistent alias sc. → scCROSS.
                sql = sql.replace("sc.sku_name", "scCROSS.sku_name")
                sql = sql.replace("sc.total_dbu", "scCROSS.total_dbu")
                sql = sql.replace("sc.cost_per_dbu", "scCROSS.cost_per_dbu")
                
                question["answer"][0]["content"][0] = sql
                return True, "cost_intelligence Q22 - Fixed 8+ column/alias references"
    
    return False, "Question ID not found"


def fix_performance_q14(content):
    """
    Fix: performance Q14 - Query latency percentiles
    
    Issue: p99_duration_seconds → p99_seconds
    """
    question_id = "f1e2d3c4b5a69780a1b2c3d4e5f67895"  # Need to find actual ID
    
    for question in content["benchmarks"]["questions"]:
        # Find by question text since ID might vary
        if "answer" in question and len(question["answer"]) > 0:
            sql = question["answer"][0]["content"][0]
            if "p99_duration_seconds" in sql:
                sql = sql.replace("p99_duration_seconds", "p99_seconds")
                question["answer"][0]["content"][0] = sql
                return True, f"performance {question['id'][:8]} - Fixed p99_duration_seconds → p99_seconds"
    
    return False, "Query with p99_duration_seconds not found"


def fix_performance_q16(content):
    """
    Fix: performance Q16 - Cluster right-sizing recommendations
    
    Issue: recommended_action → prediction
    """
    for question in content["benchmarks"]["questions"]:
        if "answer" in question and len(question["answer"]) > 0:
            sql = question["answer"][0]["content"][0]
            if "recommended_action" in sql and "cluster_rightsizing" in sql.lower():
                sql = sql.replace("recommended_action", "prediction")
                question["answer"][0]["content"][0] = sql
                return True, f"performance {question['id'][:8]} - Fixed recommended_action → prediction"
    
    return False, "Query with recommended_action not found"


def fix_performance_q25(content):
    """
    Fix: performance Q25 - End-to-end performance health dashboard
    
    Issue: qh. → qhCROSS. (alias mismatch)
    """
    for question in content["benchmarks"]["questions"]:
        if "answer" in question and len(question["answer"]) > 0:
            sql = question["answer"][0]["content"][0]
            # Look for queries with both qh. and qhCROSS
            if "qh." in sql and "qhCROSS" in sql:
                # Replace all qh. with qhCROSS. (but not qhCROSS itself)
                sql = re.sub(r'\bqh\.', 'qhCROSS.', sql)
                question["answer"][0]["content"][0] = sql
                return True, f"performance {question['id'][:8]} - Fixed qh. → qhCROSS."
    
    return False, "Query with qh./qhCROSS alias not found"


def fix_security_auditor_q8(content):
    """
    Fix: security_auditor Q8 - Permission changes
    
    Issue: change_date → event_time
    """
    for question in content["benchmarks"]["questions"]:
        if "answer" in question and len(question["answer"]) > 0:
            sql = question["answer"][0]["content"][0]
            if "change_date" in sql and "get_permission_changes" in sql:
                sql = sql.replace("change_date", "event_time")
                question["answer"][0]["content"][0] = sql
                return True, f"security_auditor {question['id'][:8]} - Fixed change_date → event_time"
    
    return False, "Query with change_date not found"


def fix_security_auditor_q11(content):
    """
    Fix: security_auditor Q11 - User activity patterns
    
    Issue: user_identity → user_email
    """
    for question in content["benchmarks"]["questions"]:
        if "answer" in question and len(question["answer"]) > 0:
            sql = question["answer"][0]["content"][0]
            if "user_identity" in sql:
                sql = sql.replace("user_identity", "user_email")
                question["answer"][0]["content"][0] = sql
                return True, f"security_auditor {question['id'][:8]} - Fixed user_identity → user_email"
    
    return False, "Query with user_identity not found"


def fix_job_health_monitor_q14(content):
    """
    Fix: job_health_monitor Q14 - Pipeline health from DLT updates
    
    Issue: f.update_state → f.result_state
    """
    question_id = "bb5f4ff19a4840e08311cde2b7aebc88"
    
    for question in content["benchmarks"]["questions"]:
        if question["id"] == question_id:
            if "answer" in question and len(question["answer"]) > 0:
                sql = question["answer"][0]["content"][0]
                sql = sql.replace("f.update_state", "f.result_state")
                question["answer"][0]["content"][0] = sql
                return True, "job_health_monitor Q14 - Fixed f.update_state → f.result_state"
    
    return False, "Question ID not found"


def main():
    script_dir = os.path.dirname(__file__)
    genie_dir = os.path.join(script_dir, "..", "src", "genie")
    
    fixes = {
        "cost_intelligence_genie_export.json": [fix_cost_intelligence_q22],
        "performance_genie_export.json": [fix_performance_q14, fix_performance_q16, fix_performance_q25],
        "security_auditor_genie_export.json": [fix_security_auditor_q8, fix_security_auditor_q11],
        "job_health_monitor_genie_export.json": [fix_job_health_monitor_q14],
    }
    
    total_fixes = 0
    all_results = []
    
    print("=" * 80)
    print("GENIE SPACE COLUMN_NOT_FOUND MANUAL FIXES")
    print("=" * 80)
    print("Based on systematic ground truth analysis\n")
    
    for filename, fix_functions in fixes.items():
        file_path = os.path.join(genie_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"⚠️  {filename} not found")
            continue
        
        print(f"📄 Processing: {filename}")
        
        with open(file_path, 'r') as f:
            content = json.load(f)
        
        file_fixes = 0
        for fix_func in fix_functions:
            success, message = fix_func(content)
            if success:
                file_fixes += 1
                total_fixes += 1
                print(f"   ✅ {message}")
                all_results.append({"file": filename, "fix": message, "success": True})
            else:
                print(f"   ⚠️  {message}")
                all_results.append({"file": filename, "fix": message, "success": False})
        
        if file_fixes > 0:
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
        
        print()
    
    print("=" * 80)
    print(f"✅ COMPLETE: Applied {total_fixes} fixes across {len(fixes)} files")
    print("=" * 80)
    
    # Write report
    report_path = os.path.join(script_dir, "..", "docs", "deployment", "GENIE_MANUAL_COLUMN_FIXES.md")
    with open(report_path, 'w') as f:
        f.write("# Genie Space Manual Column Fixes Report\n\n")
        f.write(f"**Date:** {os.popen('date').read().strip()}\n")
        f.write(f"**Total Fixes Applied:** {total_fixes}\n\n")
        f.write("## Fixes Applied:\n\n")
        for result in all_results:
            status = "✅" if result["success"] else "⚠️"
            f.write(f"{status} **{result['file']}**: {result['fix']}\n")
        f.write("\n## Next Steps:\n\n")
        f.write("1. Deploy bundle: `databricks bundle deploy -t dev`\n")
        f.write("2. Re-run validation: `databricks bundle run -t dev genie_benchmark_sql_validation_job`\n")
        f.write("3. Review remaining 8 COLUMN_NOT_FOUND errors\n")
    
    print(f"\n📄 Report written to: {report_path}\n")


if __name__ == "__main__":
    main()

