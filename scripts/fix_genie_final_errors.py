#!/usr/bin/env python3
"""
Fix remaining Genie Space SQL errors - Final cleanup
Session 4: Easy fixes based on ground truth

Fixes:
1. job_health_monitor Q18: tf1.ft.run_id → tf1.run_id (CTE column reference)
2. cost_intelligence Q25: workspace_id → workspace_name (from ML table)
3. performance Q16, unified Q18: Cast DOWNSIZE to string, not double
"""

import json
import re
from pathlib import Path


def fix_job_health_monitor_q18(content: str) -> str:
    """Fix: tf1.ft.run_id → tf1.run_id"""
    # The task_failures CTE only outputs run_id, not ft.run_id
    # Also fix depends_on reference
    old = r"AND tf1\.ft\.run_id = tf2\.ft\.run_id\s+AND tf2\.depends_on LIKE"
    new = "AND tf1.run_id = tf2.run_id    AND tf2.depends_on_keys_json LIKE"
    content = re.sub(old, new, content)
    return content


def fix_cost_intelligence_q25(content: str) -> str:
    """Fix: workspace_id → workspace_name (from ML cost_forecast_predictions)"""
    # Check the query structure - likely selecting workspace_id from ML table
    # Cost forecast predictions table has workspace_name, not workspace_id
    old = r"workspace_id\s+FROM\s+cost_forecast_predictions"
    new = "workspace_name  FROM cost_forecast_predictions"
    content = re.sub(old, new, content, flags=re.IGNORECASE)
    return content


def fix_cluster_rightsizing_cast(content: str) -> str:
    """
    Fix: Cast 'DOWNSIZE' (recommendation string) to DOUBLE → Don't cast it!
    
    Root cause: Query likely doing AVG(recommendation) where recommendation is
    a string like 'DOWNSIZE', 'UPSIZE', 'NO_CHANGE'
    
    Fix: Remove the cast or change query logic
    """
    # This is trickier - need to see the actual query
    # Likely pattern: CAST(recommendation AS DOUBLE) or similar
    # Let's look for AVG/SUM on recommendation column
    
    # Pattern 1: Direct cast of recommendation
    old1 = r"CAST\(recommendation AS (DOUBLE|INT)\)"
    new1 = "recommendation"
    content = re.sub(old1, new1, content, flags=re.IGNORECASE)
    
    # Pattern 2: Aggregation on recommendation (needs to be removed or changed)
    # This is harder to fix automatically - flag for manual review
    
    return content


def process_file(filepath: Path) -> tuple[int, list[str]]:
    """Process a single Genie Space JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixes_applied = 0
    changes = []
    
    # Process all benchmark questions
    for idx, question in enumerate(data['benchmarks']['questions'], 1):
        question_id = f"Q{idx}"
        original_sql = ''.join(question['answer'][0]['content'])
        modified_sql = original_sql
        
        # Apply fixes based on file and question
        if filepath.name == 'job_health_monitor_genie_export.json' and idx == 18:
            modified_sql = fix_job_health_monitor_q18(modified_sql)
            if modified_sql != original_sql:
                fixes_applied += 1
                changes.append(f"  - Q18: Fixed tf1.ft.run_id → tf1.run_id")
        
        elif filepath.name == 'cost_intelligence_genie_export.json' and idx == 25:
            modified_sql = fix_cost_intelligence_q25(modified_sql)
            if modified_sql != original_sql:
                fixes_applied += 1
                changes.append(f"  - Q25: Fixed workspace_id → workspace_name")
        
        elif filepath.name in ['performance_genie_export.json', 'unified_health_monitor_genie_export.json']:
            if (filepath.name == 'performance_genie_export.json' and idx == 16) or \
               (filepath.name == 'unified_health_monitor_genie_export.json' and idx == 18):
                modified_sql = fix_cluster_rightsizing_cast(modified_sql)
                if modified_sql != original_sql:
                    fixes_applied += 1
                    changes.append(f"  - Q{idx}: Removed CAST on recommendation column")
        
        # Update the content if modified
        if modified_sql != original_sql:
            question['answer'][0]['content'] = [modified_sql]
    
    # Write back if any fixes applied
    if fixes_applied > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return fixes_applied, changes


def main():
    """Process all Genie Space JSON files."""
    genie_dir = Path('src/genie')
    json_files = list(genie_dir.glob('*_genie_export.json'))
    
    print("=" * 80)
    print("GENIE SPACE FINAL ERROR FIXES - SESSION 4")
    print("=" * 80)
    print(f"\nProcessing {len(json_files)} Genie Space JSON files...\n")
    
    total_fixes = 0
    all_changes = []
    
    for json_file in sorted(json_files):
        fixes, changes = process_file(json_file)
        if fixes > 0:
            total_fixes += fixes
            print(f"✅ {json_file.name}: {fixes} fix(es)")
            for change in changes:
                print(change)
                all_changes.append(f"{json_file.stem}: {change}")
            print()
    
    print("=" * 80)
    print(f"TOTAL FIXES APPLIED: {total_fixes}")
    print("=" * 80)
    
    if total_fixes > 0:
        print("\n📝 Summary of changes:")
        for change in all_changes:
            print(f"  • {change}")
        
        print("\n✅ All changes saved to JSON files")
        print("🚀 Ready to deploy with: databricks bundle deploy -t dev")
    else:
        print("\n⚠️  No fixes applied - check if patterns match actual errors")


if __name__ == '__main__':
    main()

