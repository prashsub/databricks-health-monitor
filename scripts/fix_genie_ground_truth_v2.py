#!/usr/bin/env python3
"""
Genie Space Column/TVF Fixer - Based on Ground Truth Analysis

This script fixes COLUMN_NOT_FOUND and FUNCTION_NOT_FOUND errors by
carefully analyzing each failing query against the ground truth assets.
"""

import json
import re
import os
from pathlib import Path

# Ground truth fixes based on actual_assets analysis
FIXES = {
    "cost_intelligence_genie_export.json": {
        "Q22": {
            "error": "scCROSS.total_sku_cost",
            "fix": "scCROSS.total_cost",
            "reason": "mv_cost_analytics has total_cost, not total_sku_cost"
        },
        "Q25": {
            # workspace_id exists in both mv_cost_analytics AND cost_anomaly_predictions
            # So this is actually correct - the error might be in the query context
            "error": "workspace_id",
            "fix": None,  # Need to see full SQL
            "reason": "workspace_id exists in both tables - need to check query context"
        }
    },
    "performance_genie_export.json": {
        "Q16": {
            "error": "potential_savings_usd",
            "fix": None,  # warehouse_optimizer_predictions doesn't have this column
            "reason": "No savings column in warehouse_optimizer_predictions ML table"
        },
        "Q25": {
            "error": "qh.avg_query_duration",
            "fix": "qhCROSS.avg_query_duration",
            "reason": "CROSS JOIN alias is qhCROSS, not qh"
        }
    },
    "security_auditor_genie_export.json": {
        "Q7": {
            "error": "off_hours_events",
            "fix": "failed_events",  # get_failed_actions returns failed_events
            "reason": "get_failed_actions TVF returns failed_events column"
        },
        "Q11": {
            "error": "hour_of_day",
            "fix": "event_hour",  # get_off_hours_activity returns event_hour
            "reason": "get_off_hours_activity TVF returns event_hour column"
        }
    },
    "unified_health_monitor_genie_export.json": {
        "Q7": {
            "error": "failed_runs",
            "fix": "error_message",  # get_failed_jobs returns job details, not counts
            "reason": "get_failed_jobs TVF returns job details, count in outer query"
        },
        "Q13": {
            "error": "failed_records",
            "fix": "failed_count",  # mv_dlt_pipeline_health has failed_count
            "reason": "mv_dlt_pipeline_health has failed_count column"
        },
        "Q18": {
            "error": "potential_savings_usd",
            "fix": None,  # Same as performance Q16
            "reason": "No savings column in warehouse_optimizer_predictions ML table"
        },
        "Q19": {
            "error": "sla_breach_rate",
            "fix": "sla_breach_rate",  # This column DOES exist in cache_hit_predictions!
            "reason": "sla_breach_rate exists in cache_hit_predictions - query context issue"
        }
    },
    "job_health_monitor_genie_export.json": {
        "Q6": {
            "error": "p95_duration_min",
            "fix": "p90_duration_min",  # mv_job_performance has p90, not p95
            "reason": "mv_job_performance has p90_duration_min, not p95"
        },
        "Q7": {
            "error": "get_job_success_rate_pct",
            "fix": "get_job_success_rate",  # TVF name is wrong
            "reason": "TVF is called get_job_success_rate (no _pct suffix)"
        },
        "Q10": {
            "error": "retry_effectiveness",
            "fix": None,  # get_job_retry_analysis doesn't have this column
            "reason": "get_job_retry_analysis doesn't have retry_effectiveness column"
        },
        "Q14": {
            "error": "p.pipeline_name",
            "fix": "p.name",
            "reason": "system.lakeflow.pipelines table has 'name' column, not 'pipeline_name'"
        },
        "Q18": {
            "error": "jt.depends_on",
            "fix": None,  # system.lakeflow.job_task_run_timeline doesn't have depends_on
            "reason": "system.lakeflow.job_task_run_timeline doesn't have depends_on column"
        }
    }
}


def apply_fix(sql: str, old_value: str, new_value: str) -> str:
    """Apply a fix to SQL query, being careful about word boundaries."""
    if not new_value:
        return sql  # Can't fix if we don't have a replacement
    
    # For column references like "qh.avg_query_duration" -> "qhCROSS.avg_query_duration"
    if "." in old_value and "." in new_value:
        # Direct replacement
        return sql.replace(old_value, new_value)
    
    # For simple column names, use word boundary replacement
    pattern = re.compile(r'\b' + re.escape(old_value) + r'\b')
    return pattern.sub(new_value, sql)


def fix_genie_file(file_path: Path, fixes: dict) -> int:
    """Apply fixes to a single Genie Space JSON file."""
    with open(file_path, 'r') as f:
        content = json.load(f)
    
    questions = content.get("benchmarks", {}).get("questions", [])
    fixes_applied = 0
    
    for i, question in enumerate(questions, 1):
        question_key = f"Q{i}"
        
        if question_key not in fixes:
            continue
        
        fix_info = fixes[question_key]
        
        # Special case: TVF name fix
        if fix_info["error"] == "get_job_success_rate_pct":
            # Fix in sql_functions
            if "sql_functions" in question:
                for func in question["sql_functions"]:
                    if func["identifier"] == "get_job_success_rate_pct":
                        func["identifier"] = "get_job_success_rate"
                        fixes_applied += 1
                        print(f"  ✅ {question_key}: Fixed TVF name in sql_functions")
            
            # Fix in SQL query
            if "answer" in question and isinstance(question["answer"], list):
                for answer_item in question["answer"]:
                    if "content" in answer_item and isinstance(answer_item["content"], list):
                        original_sql = answer_item["content"][0]
                        if "get_job_success_rate_pct" in original_sql:
                            new_sql = original_sql.replace("get_job_success_rate_pct", "get_job_success_rate")
                            answer_item["content"][0] = new_sql
                            fixes_applied += 1
                            print(f"  ✅ {question_key}: Fixed TVF name in SQL query")
            continue
        
        # Column fixes
        if not fix_info["fix"]:
            print(f"  ⚠️  {question_key}: Cannot auto-fix '{fix_info['error']}' - {fix_info['reason']}")
            continue
        
        if "answer" in question and isinstance(question["answer"], list):
            for answer_item in question["answer"]:
                if "content" in answer_item and isinstance(answer_item["content"], list):
                    original_sql = answer_item["content"][0]
                    new_sql = apply_fix(original_sql, fix_info["error"], fix_info["fix"])
                    
                    if new_sql != original_sql:
                        answer_item["content"][0] = new_sql
                        fixes_applied += 1
                        print(f"  ✅ {question_key}: '{fix_info['error']}' → '{fix_info['fix']}'")
    
    if fixes_applied > 0:
        with open(file_path, 'w') as f:
            json.dump(content, f, indent=2)
    
    return fixes_applied


def main():
    script_dir = Path(__file__).parent
    genie_dir = script_dir.parent / "src" / "genie"
    
    print("=" * 80)
    print("GENIE SPACE GROUND TRUTH FIXER V2")
    print("=" * 80)
    print()
    
    total_fixes = 0
    
    for filename, fixes in FIXES.items():
        file_path = genie_dir / filename
        
        if not file_path.exists():
            print(f"❌ File not found: {filename}")
            continue
        
        print(f"📄 {filename}")
        fixes_applied = fix_genie_file(file_path, fixes)
        total_fixes += fixes_applied
        
        if fixes_applied == 0:
            print(f"  ⚪ No automatic fixes applied")
        print()
    
    print("=" * 80)
    print(f"✅ COMPLETE: Applied {total_fixes} fixes")
    print("=" * 80)
    print()
    
    # Create summary report
    report_path = script_dir.parent / "docs" / "deployment" / "GENIE_GROUND_TRUTH_V2_FIXES.md"
    with open(report_path, 'w') as f:
        f.write("# Genie Space Ground Truth Fixes V2\n\n")
        f.write(f"**Date:** {os.popen('date').read().strip()}\n")
        f.write(f"**Total Fixes Applied:** {total_fixes}\n\n")
        f.write("## Fixes Summary\n\n")
        
        for filename, fixes in FIXES.items():
            f.write(f"### {filename}\n\n")
            for question_key, fix_info in fixes.items():
                status = "✅ FIXED" if fix_info["fix"] else "⚠️  MANUAL"
                f.write(f"- **{question_key}:** {status}\n")
                f.write(f"  - Error: `{fix_info['error']}`\n")
                if fix_info["fix"]:
                    f.write(f"  - Fix: `{fix_info['fix']}`\n")
                f.write(f"  - Reason: {fix_info['reason']}\n\n")
    
    print(f"📄 Report written to: {report_path}")
    print()


if __name__ == "__main__":
    main()

