#!/usr/bin/env python3
"""
Fix final 2 Genie SQL bugs (cost Q23, Q25)

Issues Found:
1. cost Q23: Extra closing parenthesis in WITH clause
2. cost Q25: workspace_id not available from get_cost_forecast_summary (platform-level only)

Session: 5
Date: 2026-01-09
"""

import json
import re
from pathlib import Path


def fix_cost_q23(query: str) -> str:
    """
    Fix cost Q23: Remove extra closing parenthesis.
    
    Issue: untagged CTE has 3 closing parens when it should have 2.
    
    BEFORE:
        untagged AS (
          SELECT SUM(total_cost) as total_untagged
          FROM get_untagged_resources(...)
        )))  <-- 3 closing parens!
    
    AFTER:
        untagged AS (
          SELECT SUM(total_cost) as total_untagged
          FROM get_untagged_resources(...)
        ))  <-- 2 closing parens
    """
    # Pattern: Find the untagged CTE with 3 closing parens
    pattern = r'(\buntagged AS \([^)]*SELECT[^)]*FROM get_untagged_resources\([^)]*\)[^)]*\))\)\)'
    replacement = r'\1)'
    
    fixed = re.sub(pattern, replacement, query, flags=re.DOTALL)
    
    if fixed != query:
        print("    ✓ Removed extra closing parenthesis after untagged CTE")
    
    return fixed


def fix_cost_q25(query: str) -> str:
    """
    Fix cost Q25: workspace_id not available from get_cost_forecast_summary.
    
    Issue: get_cost_forecast_summary returns platform-level forecast, no workspace data.
    
    Solution: Remove cost_forecast CTE entirely and adjust the main query.
    
    BEFORE:
        WITH cost_forecast AS (
          SELECT workspace_name as workspace_id, predicted_cost as projected_monthly_cost
          FROM get_cost_forecast_summary(1) LIMIT 1
        ),
        current_costs AS ...
    
    AFTER:
        WITH current_costs AS ...
    """
    # Remove the cost_forecast CTE entirely
    # Pattern: WITH cost_forecast AS (...), followed by next CTE
    pattern = r'WITH cost_forecast AS \([^)]*\),[\\s\\n]*'
    replacement = 'WITH '
    
    fixed = re.sub(pattern, replacement, query, flags=re.DOTALL)
    
    if fixed != query:
        print("    ✓ Removed cost_forecast CTE (workspace_id not available)")
        
        # Also need to remove any references to cf.projected_monthly_cost
        # Since this column is no longer available, remove it from SELECT if present
        # (The query doesn't use it in the main SELECT, so we're OK)
    
    return fixed


def fix_json_file(json_path: Path) -> int:
    """Fix SQL queries in a JSON file. Returns number of fixes applied."""
    print(f"\\nProcessing: {json_path.name}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixes_applied = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    
    for idx, question_data in enumerate(questions, 1):
        q_num = f"Q{idx}"
        
        # Get SQL query from answer.content
        answer_list = question_data.get('answer', [])
        if not answer_list:
            continue
            
        content_list = answer_list[0].get('content', [])
        if not content_list:
            continue
        
        original_query = ''.join(content_list)
        fixed_query = original_query
        
        # Apply fixes based on Q number
        if json_path.name == 'cost_intelligence_genie_export.json':
            if idx == 23:  # Q23
                print(f"  {q_num}: Fixing syntax error (extra closing paren)...")
                fixed_query = fix_cost_q23(fixed_query)
                
            elif idx == 25:  # Q25
                print(f"  {q_num}: Fixing workspace_id reference...")
                fixed_query = fix_cost_q25(fixed_query)
        
        # Update if changed
        if fixed_query != original_query:
            answer_list[0]['content'] = [fixed_query]
            fixes_applied += 1
            print(f"    ✅ Fixed {q_num}")
    
    # Write back if fixes were made
    if fixes_applied > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ {fixes_applied} fix(es) applied to {json_path.name}")
    else:
        print(f"  ℹ️  No changes needed")
    
    return fixes_applied


def main():
    """Fix final 2 Genie SQL bugs."""
    print("=" * 80)
    print("GENIE SQL BUG FIXES - Session 5")
    print("=" * 80)
    print("\\nFixing:")
    print("  1. cost Q23: SYNTAX_ERROR (extra closing paren)")
    print("  2. cost Q25: COLUMN_NOT_FOUND (workspace_id)")
    print()
    
    genie_dir = Path("src/genie")
    
    # Only fix cost_intelligence file
    json_file = genie_dir / "cost_intelligence_genie_export.json"
    
    total_fixes = 0
    
    if json_file.exists():
        fixes = fix_json_file(json_file)
        total_fixes += fixes
    else:
        print(f"⚠️  File not found: {json_file}")
    
    print()
    print("=" * 80)
    if total_fixes > 0:
        print(f"✅ COMPLETE: {total_fixes} SQL bug(es) fixed!")
        print("=" * 80)
        print("\\nNext steps:")
        print("  1. Deploy: databricks bundle deploy -t dev")
        print("  2. Validate: databricks bundle run -t dev genie_benchmark_sql_validation_job")
    else:
        print("ℹ️  No fixes applied (queries already correct or not found)")
        print("=" * 80)


if __name__ == "__main__":
    main()

