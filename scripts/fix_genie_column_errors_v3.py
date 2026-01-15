#!/usr/bin/env python3
"""
Fix COLUMN_NOT_FOUND errors from validation run (Jan 9, 20:09).

Fixes based on ground truth from docs/reference/actual_assets/:
1. security_auditor Q5: total_events → event_count
2. performance Q8: spill_bytes → total_spill_gb
3. unified_health_monitor Q19: sla_breach_rate → Remove (column doesn't exist)

Usage:
    python3 scripts/fix_genie_column_errors_v3.py
"""

import json
from pathlib import Path

FIXES = {
    'security_auditor_genie_export.json': {
        5: {
            'old': 'total_events',
            'new': 'event_count',
            'description': 'Q5: get_user_activity_summary outputs event_count, not total_events'
        }
    },
    'performance_genie_export.json': {
        8: {
            'old': 'spill_bytes',
            'new': 'total_spill_gb',
            'description': 'Q8: get_high_spill_queries outputs total_spill_gb, not spill_bytes'
        }
    },
    'unified_health_monitor_genie_export.json': {
        19: {
            'old': 'sla_breach_rate',
            'new': 'failure_rate',  # Use existing metric
            'description': 'Q19: sla_breach_rate column does not exist, use failure_rate instead'
        }
    }
}

def fix_json_file(file_path: Path, fixes: dict):
    """Apply column name fixes to a single JSON file."""
    print(f"\n🔧 Processing {file_path.name}...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    fixed_count = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    
    for q_num, fix_info in fixes.items():
        if len(questions) >= q_num:
            question_obj = questions[q_num - 1]
            answer_list = question_obj.get('answer', [])
            
            if answer_list and 'content' in answer_list[0]:
                old_sql = ''.join(answer_list[0]['content']).strip()
                
                if fix_info['old'] in old_sql:
                    new_sql = old_sql.replace(fix_info['old'], fix_info['new'])
                    answer_list[0]['content'] = [new_sql]
                    print(f"  ✅ Q{q_num}: {fix_info['description']}")
                    fixed_count += 1
                else:
                    print(f"  ⚠️  Q{q_num}: Column '{fix_info['old']}' not found in SQL")
    
    if fixed_count > 0:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  💾 Saved {fixed_count} fixes to {file_path.name}")
    
    return fixed_count

def main():
    """Apply all column name fixes."""
    print("=" * 80)
    print("GENIE SPACE COLUMN NAME FIXES - SESSION 3")
    print("=" * 80)
    
    src_dir = Path("src/genie")
    total_fixed = 0
    
    for filename, fixes in FIXES.items():
        file_path = src_dir / filename
        if file_path.exists():
            count = fix_json_file(file_path, fixes)
            total_fixed += count
        else:
            print(f"⚠️  File not found: {filename}")
    
    print("\n" + "=" * 80)
    print(f"✅ COMPLETE: Fixed {total_fixed} column name errors")
    print("=" * 80)

if __name__ == "__main__":
    main()

