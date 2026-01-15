#!/usr/bin/env python3
"""
Fix VERIFIED Genie Space SQL errors
Session 4: Targeted fixes for confirmed errors

VERIFIED ERRORS TO FIX:
1. Nested MEASURE aggregates (2 queries) - HIGH PRIORITY
2. Unbalanced parentheses (1 query) - MEDIUM
3. workspace_id column (1 query) - LOW (might be TVF issue)

SKIPPING (TVF bugs, not Genie SQL bugs):
- UUID→INT casting (3 queries) - These are TVF implementation bugs
- String→DOUBLE casting (2 queries) - Need more investigation
"""

import json
import re
from pathlib import Path


def fix_nested_measure_aggregates(content: str) -> str:
    """
    Fix: AVG(MEASURE(...)) or SUM(MEASURE(...))
    
    MEASURE() already returns aggregated values from metric views.
    You can't aggregate an aggregation.
    
    Solution: Remove outer aggregation, just use MEASURE()
    """
    # Pattern: AVG(MEASURE(column_name))
    old_pattern = r"(AVG|SUM)\(MEASURE\(([^)]+)\)\)"
    new_pattern = r"MEASURE(\2)"
    content = re.sub(old_pattern, new_pattern, content, flags=re.IGNORECASE)
    
    return content


def fix_unbalanced_parentheses(content: str) -> str:
    """
    Fix cost_intelligence Q23: Has 1 extra closing parenthesis.
    
    Pattern: Query likely has )) where it should have )
    """
    # Count parentheses
    open_count = content.count('(')
    close_count = content.count(')')
    
    if close_count > open_count:
        # Has extra closing parenthesis
        # Try to find the likely location - usually at end of WHERE clause
        # Pattern: "... IS NOT NULL )" followed by nothing or SELECT
        
        # Look for pattern where query seems incomplete after closing paren
        pattern = r"(IS NOT NULL\s+)\)(\s*$)"
        if re.search(pattern, content):
            # Remove the extra closing paren
            content = re.sub(pattern, r"\1\2", content)
            print(f"  ✓ Removed extra closing parenthesis")
    
    return content


def fix_cost_q25_workspace(content: str) -> str:
    """
    Fix cost_intelligence Q25: workspace_id not found in ML table.
    
    The error suggests workspace_id doesn't exist in cost_forecast_predictions.
    But the query uses get_cost_forecast_summary TVF which should return it.
    
    This might be a TVF bug, but let's try adding workspace_name as fallback.
    """
    # Check if this is the problematic CTE
    if "FROM get_cost_forecast_summary" in content:
        # Add workspace_name as workspace_id alias
        old = r"SELECT\s+workspace_id,\s+predicted_cost"
        new = "SELECT    COALESCE(workspace_id, workspace_name) as workspace_id,    predicted_cost"
        content = re.sub(old, new, content, flags=re.IGNORECASE | re.DOTALL)
    
    return content


def process_file(filepath: Path) -> tuple[int, list[str]]:
    """Process a single Genie Space JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixes_applied = 0
    changes = []
    
    # Target queries based on verified errors
    targets = {
        'cost_intelligence_genie_export.json': {
            23: ('unbalanced_parens', 'Fix unbalanced parentheses'),
            25: ('workspace_column', 'Fix workspace_id column'),
        },
        'performance_genie_export.json': {
            23: ('nested_measure', 'Fix AVG(MEASURE(...))'),
        },
        'unified_health_monitor_genie_export.json': {
            20: ('nested_measure', 'Fix nested MEASURE aggregates'),
            21: ('nested_measure', 'Fix nested MEASURE aggregates'),
        },
    }
    
    file_targets = targets.get(filepath.name, {})
    
    for idx, question in enumerate(data['benchmarks']['questions'], 1):
        if idx not in file_targets:
            continue
        
        fix_type, description = file_targets[idx]
        question_id = f"Q{idx}"
        original_sql = ''.join(question['answer'][0]['content'])
        modified_sql = original_sql
        
        # Apply appropriate fix
        if fix_type == 'nested_measure':
            modified_sql = fix_nested_measure_aggregates(modified_sql)
        elif fix_type == 'unbalanced_parens':
            modified_sql = fix_unbalanced_parentheses(modified_sql)
        elif fix_type == 'workspace_column':
            modified_sql = fix_cost_q25_workspace(modified_sql)
        
        # Update if modified
        if modified_sql != original_sql:
            question['answer'][0]['content'] = [modified_sql]
            fixes_applied += 1
            changes.append(f"  - {question_id}: {description}")
            
            # Show before/after for nested MEASURE fixes
            if fix_type == 'nested_measure':
                old_measures = re.findall(r'(AVG|SUM)\(MEASURE\([^)]+\)\)', original_sql, re.IGNORECASE)
                if old_measures:
                    print(f"    Before: {old_measures[0]}")
                    print(f"    After:  MEASURE(...)")
    
    # Write back if fixes applied
    if fixes_applied > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return fixes_applied, changes


def main():
    """Process all Genie Space JSON files."""
    genie_dir = Path('src/genie')
    json_files = list(genie_dir.glob('*_genie_export.json'))
    
    print("=" * 80)
    print("GENIE SPACE VERIFIED ERROR FIXES - SESSION 4")
    print("=" * 80)
    print("Targeting: 4 confirmed fixable errors")
    print("  • 2x Nested MEASURE aggregates (performance Q23, unified Q20/Q21)")
    print("  • 1x Unbalanced parentheses (cost Q23)")
    print("  • 1x workspace_id column (cost Q25)")
    print("\nSkipping 5 errors that are TVF bugs or need investigation:")
    print("  • 3x UUID→INT casting (TVF implementation issues)")
    print("  • 2x String→DOUBLE casting (need more analysis)")
    print("=" * 80)
    print()
    
    total_fixes = 0
    all_changes = []
    
    for json_file in sorted(json_files):
        fixes, changes = process_file(json_file)
        if fixes > 0:
            total_fixes += fixes
            print(f"✅ {json_file.name}: {fixes} fix(es)")
            for change in changes:
                print(change)
            all_changes.extend(changes)
            print()
    
    print("=" * 80)
    print(f"TOTAL FIXES APPLIED: {total_fixes}")
    print("=" * 80)
    
    if total_fixes > 0:
        print("\n✅ Changes saved to JSON files")
        print("\n📊 Expected Impact:")
        print(f"  • Before: 93% pass rate (114/123)")
        print(f"  • After:  ~96% pass rate ({114 + total_fixes}/123)")
        print(f"  • Remaining: {10 - total_fixes} errors (mostly TVF bugs)")
        print("\n🚀 Next Steps:")
        print("  1. Deploy: databricks bundle deploy -t dev")
        print("  2. Re-validate to confirm fixes")
        print("  3. Address remaining TVF implementation bugs separately")
    else:
        print("\n⚠️  No fixes applied - patterns may need adjustment")


if __name__ == '__main__':
    main()

