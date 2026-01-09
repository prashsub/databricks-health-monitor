#!/usr/bin/env python3
"""
Fix COLUMN_NOT_FOUND errors in Genie Space JSON files using ground truth from actual_assets.

This script:
1. Loads all tables and columns from docs/reference/actual_assets/
2. Analyzes COLUMN_NOT_FOUND errors from validation
3. Finds correct column names using fuzzy matching
4. Updates JSON files with fixes
5. Generates detailed report

Usage:
    python scripts/fix_genie_column_errors.py
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Set, List, Tuple
from difflib import get_close_matches

# Validation errors to fix (from the user's validation output)
COLUMN_ERRORS = [
    # Cost Intelligence
    ("cost_intelligence", "Q22", "sc.total_sku_cost", "CTE alias issue"),
    ("cost_intelligence", "Q25", "workspace_name", "cost predictions table"),
    
    # Performance
    ("performance", "Q14", "p99_duration", "Should be p99_seconds"),
    ("performance", "Q16", "recommended_action", "cluster rightsizing predictions"),
    ("performance", "Q25", "qh.query_volume", "CTE alias issue"),
    
    # Security Auditor
    ("security_auditor", "Q7", "failed_count", "get_failed_actions TVF output"),
    ("security_auditor", "Q8", "change_date", "get_permission_changes TVF output"),
    ("security_auditor", "Q10", "risk_level", "Should be audit_level"),
    ("security_auditor", "Q15", "unique_data_consumers", "mv_governance_analytics"),
    ("security_auditor", "Q16", "event_count", "Should be total_events"),
    ("security_auditor", "Q17", "event_volume_drift", "Should be event_volume_drift_pct"),
    
    # Unified Health Monitor
    ("unified_health_monitor", "Q4", "success_rate", "mv_security_events"),
    ("unified_health_monitor", "Q7", "failure_count", "get_failed_jobs output"),
    ("unified_health_monitor", "Q11", "utilization_rate", "commit tracking table"),
    ("unified_health_monitor", "Q12", "query_count", "Should be total_queries"),
    ("unified_health_monitor", "Q13", "failed_events", "DLT monitoring table"),
    ("unified_health_monitor", "Q15", "risk_level", "Should be audit_level"),
    ("unified_health_monitor", "Q16", "days_since_last_access", "Should be hours_since_update"),
    ("unified_health_monitor", "Q18", "recommended_action", "cluster rightsizing predictions"),
    ("unified_health_monitor", "Q19", "cost_7d", "mv_cost_analytics"),
    
    # Job Health Monitor
    ("job_health_monitor", "Q4", "failure_count", "get_failed_jobs output"),
    ("job_health_monitor", "Q6", "p95_duration_minutes", "Should be p95_duration_min"),
    ("job_health_monitor", "Q7", "success_rate", "Should be success_rate_pct or success_rate from mv_job_performance"),
    ("job_health_monitor", "Q8", "failure_count", "Should be failed_runs"),
    ("job_health_monitor", "Q9", "deviation_score", "Should be deviation_ratio"),
    ("job_health_monitor", "Q14", "f.start_time", "system.lakeflow.flow_events alias"),
    ("job_health_monitor", "Q18", "ft.run_date", "fact_job_run_timeline alias"),
]

# Manual fixes for known column name mappings
COLUMN_NAME_FIXES = {
    "p99_duration": "p99_seconds",
    "success_rate": "success_rate_pct",  # For most tables, but check mv_job_performance first
    "risk_level": "audit_level",
    "event_count": "total_events",
    "event_volume_drift": "event_volume_drift_pct",
    "query_count": "total_queries",
    "days_since_last_access": "hours_since_update",
    "p95_duration_minutes": "p95_duration_min",
    "failure_count": "failed_runs",  # Or could be from TVF - needs context
    "deviation_score": "deviation_ratio",
    "utilization_rate": None,  # Need to check what mv_commit_tracking actually has
    "cost_7d": "last_7_day_cost",  # From mv_cost_analytics
}


def load_tables_with_columns(assets_dir: Path) -> Dict[str, Set[str]]:
    """
    Load all tables and their columns from actual_assets folder.
    
    Returns:
        Dict mapping table_name -> set of column names
    """
    all_tables = {}
    
    # Load from tables.md, mvs.md, ml.md, monitoring.md
    asset_files = [
        assets_dir / "tables.md",
        assets_dir / "mvs.md",
        assets_dir / "ml.md",
        assets_dir / "monitoring.md",
    ]
    
    for file_path in asset_files:
        if not file_path.exists():
            print(f"⚠️  Warning: {file_path} not found")
            continue
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Skip header
        for line in lines[1:]:
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
            
            # table_catalog, table_schema, table_name, column_name, data_type
            table_name = parts[2]
            column_name = parts[3]
            
            if table_name not in all_tables:
                all_tables[table_name] = set()
            
            all_tables[table_name].add(column_name)
    
    print(f"✅ Loaded {len(all_tables)} tables with columns")
    return all_tables


def find_correct_column(incorrect_col: str, table_columns: Set[str]) -> str:
    """
    Find the correct column name using fuzzy matching.
    
    Args:
        incorrect_col: The incorrect column name
        table_columns: Set of correct column names for the table
    
    Returns:
        The correct column name, or the original if no match found
    """
    # First, check manual fixes
    if incorrect_col in COLUMN_NAME_FIXES:
        manual_fix = COLUMN_NAME_FIXES[incorrect_col]
        if manual_fix and manual_fix in table_columns:
            return manual_fix
    
    # Fuzzy match
    matches = get_close_matches(incorrect_col, table_columns, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    
    return incorrect_col  # No match found


def get_question_sql(genie_space: str, question_num: str) -> Tuple[str, str, List]:
    """
    Get the SQL query for a specific Genie space question.
    
    Returns:
        (file_path, question_id, answer_content_list)
    """
    file_path = f"src/genie/{genie_space}_genie_export.json"
    
    if not os.path.exists(file_path):
        return None, None, None
    
    with open(file_path, 'r') as f:
        content = json.load(f)
    
    # Find the question by array index (Q1 = index 0, Q2 = index 1, etc.)
    questions = content.get("benchmarks", {}).get("questions", [])
    q_num_int = int(question_num.replace("Q", ""))
    q_index = q_num_int - 1  # Convert to 0-based index
    
    if q_index < 0 or q_index >= len(questions):
        return file_path, None, None
    
    question = questions[q_index]
    
    if "answer" in question and isinstance(question["answer"], list):
        for answer_item in question["answer"]:
            if "content" in answer_item and isinstance(answer_item["content"], list):
                return file_path, question["id"], answer_item["content"]
    
    return file_path, None, None


def apply_column_fix(sql: str, incorrect_col: str, correct_col: str) -> str:
    """
    Apply column name fix to SQL query.
    
    Args:
        sql: The SQL query
        incorrect_col: The incorrect column name
        correct_col: The correct column name
    
    Returns:
        Updated SQL
    """
    # Handle different patterns:
    # 1. Simple column name: "column_name"
    # 2. Aliased column: "alias.column_name"
    # 3. In SELECT list
    # 4. In WHERE/ORDER BY clauses
    
    patterns = [
        # SELECT col, ORDER BY col, WHERE col
        (rf'\b{incorrect_col}\b', correct_col),
        # alias.col patterns
        (rf'\.{incorrect_col}\b', f'.{correct_col}'),
    ]
    
    modified_sql = sql
    for pattern, replacement in patterns:
        modified_sql = re.sub(pattern, replacement, modified_sql)
    
    return modified_sql


def main():
    """Main execution function."""
    print("=" * 80)
    print("GENIE SPACE COLUMN ERROR FIXER")
    print("=" * 80)
    print()
    
    # 1. Load ground truth
    script_dir = Path(__file__).parent
    assets_dir = script_dir.parent / "docs" / "reference" / "actual_assets"
    
    if not assets_dir.exists():
        print(f"❌ ERROR: {assets_dir} not found")
        return
    
    all_tables = load_tables_with_columns(assets_dir)
    print()
    
    # 2. Analyze errors and prepare fixes
    fixes_to_apply = []
    
    print("🔍 Analyzing COLUMN_NOT_FOUND errors...")
    print()
    
    for genie_space, question_num, incorrect_col, note in COLUMN_ERRORS:
        print(f"  {genie_space} {question_num}: {incorrect_col}")
        
        # Get the SQL for this question
        file_path, question_id, answer_content = get_question_sql(genie_space, question_num)
        
        if not answer_content:
            print(f"    ⚠️  Could not find question in JSON")
            continue
        
        sql = answer_content[0]
        
        # Determine which table this column should be in
        # This is a heuristic based on the query context
        target_tables = []
        if "mv_cost_analytics" in sql or "cost" in genie_space:
            target_tables.append("mv_cost_analytics")
        if "mv_security_events" in sql or "security" in genie_space:
            target_tables.append("mv_security_events")
        if "mv_job_performance" in sql or "job" in genie_space:
            target_tables.append("mv_job_performance")
        if "mv_governance_analytics" in sql:
            target_tables.append("mv_governance_analytics")
        if "mv_query_performance" in sql or "performance" in genie_space:
            target_tables.append("mv_query_performance")
        if "mv_commit_tracking" in sql:
            target_tables.append("mv_commit_tracking")
        
        # Try to find correct column name
        correct_col = None
        for table_name in target_tables:
            if table_name in all_tables:
                correct_col = find_correct_column(incorrect_col, all_tables[table_name])
                if correct_col != incorrect_col:
                    print(f"    ✅ {incorrect_col} → {correct_col} (from {table_name})")
                    fixes_to_apply.append((file_path, question_id, incorrect_col, correct_col, sql))
                    break
        
        if not correct_col or correct_col == incorrect_col:
            print(f"    ⚠️  No automatic fix found - needs manual review")
            print(f"       Note: {note}")
    
    print()
    print(f"📊 Summary: {len(fixes_to_apply)} automatic fixes identified")
    print()
    
    # 3. Apply fixes
    if not fixes_to_apply:
        print("⚠️  No fixes to apply")
        return
    
    print("🔧 Applying fixes...")
    print()
    
    files_modified = set()
    fixes_applied = 0
    
    for file_path, question_id, incorrect_col, correct_col, original_sql in fixes_to_apply:
        # Read JSON
        with open(file_path, 'r') as f:
            content = json.load(f)
        
        # Find and update the question
        questions = content.get("benchmarks", {}).get("questions", [])
        for question in questions:
            if question["id"] == question_id:
                if "answer" in question and isinstance(question["answer"], list):
                    for answer_item in question["answer"]:
                        if "content" in answer_item and isinstance(answer_item["content"], list):
                            old_sql = answer_item["content"][0]
                            new_sql = apply_column_fix(old_sql, incorrect_col, correct_col)
                            
                            if new_sql != old_sql:
                                answer_item["content"][0] = new_sql
                                fixes_applied += 1
                                files_modified.add(file_path)
                                print(f"  ✅ Fixed {question_id}: {incorrect_col} → {correct_col}")
        
        # Write back
        if file_path in files_modified:
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
    
    print()
    print("=" * 80)
    print(f"✅ COMPLETE: Applied {fixes_applied} fixes across {len(files_modified)} files")
    print("=" * 80)
    print()
    
    # 4. Generate report
    report_path = script_dir.parent / "docs" / "deployment" / "GENIE_COLUMN_FIXES_APPLIED.md"
    with open(report_path, 'w') as f:
        f.write("# Genie Space Column Error Fixes Report\n\n")
        f.write(f"**Date:** {os.popen('date').read().strip()}\n")
        f.write(f"**Total Fixes Applied:** {fixes_applied}\n")
        f.write(f"**Files Modified:** {len(files_modified)}\n\n")
        
        f.write("## Fixes Applied:\n\n")
        for file_path, question_id, incorrect_col, correct_col, _ in fixes_to_apply:
            f.write(f"- **{question_id}:** `{incorrect_col}` → `{correct_col}`\n")
        
        f.write("\n## Files Modified:\n\n")
        for file_path in sorted(files_modified):
            f.write(f"- `{file_path}`\n")
        
        f.write("\n## Next Steps:\n\n")
        f.write("1. Deploy bundle: `databricks bundle deploy -t dev`\n")
        f.write("2. Re-run validation: `databricks bundle run -t dev genie_benchmark_sql_validation_job`\n")
        f.write("3. Review remaining errors\n")
    
    print(f"📄 Report written to: {report_path}")
    print()


if __name__ == "__main__":
    main()

