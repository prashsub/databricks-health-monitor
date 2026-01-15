#!/usr/bin/env python3
"""
Fix remaining CAST_INVALID_INPUT and WRONG_NUM_ARGS errors.

Fixes:
1. performance Q7: get_warehouse_utilization - UUID→INT casting issue
2. performance Q10: get_underutilized_clusters - DATE→DOUBLE casting issue
3. performance Q12: get_query_volume_trends - DATE→INT casting issue
4. unified_health_monitor Q12: get_warehouse_utilization - UUID→INT casting issue

Usage:
    python3 scripts/fix_genie_remaining_errors.py
"""

import json
from pathlib import Path

# Define fixes
FIXES = {
    'performance_genie_export.json': {
        7: {
            'old': '''(CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,  CAST(CURRENT_DATE() AS STRING)''',
            'new': '''CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),\n  CAST(CURRENT_DATE() AS STRING)''',
            'description': 'Q7: Fix PostgreSQL ::STRING syntax for get_warehouse_utilization'
        },
        10: {
            'old': '''(CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,  CAST(CURRENT_DATE() AS STRING),  20.0''',
            'new': '''30,\n  20.0,\n  10''',
            'description': 'Q10: get_underutilized_clusters(days_back INT=30, cpu_threshold DOUBLE=20.0, min_hours INT=10)'
        },
        12: {
            'old': "(CURRENT_DATE() - INTERVAL 14 DAYS)::STRING,  CAST(CURRENT_DATE() AS STRING)",
            'new': "14,\n  'DAY'",
            'description': 'Q12: get_query_volume_trends(days_back INT=14, granularity STRING)'
        }
    }
}

def fix_json_file(file_path: Path, fixes: dict):
    """Apply fixes to a single JSON file."""
    print(f"\n🔧 Processing {file_path.name}...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    fixed_count = 0
    for q_num, fix_info in fixes.items():
        # Find the question in the JSON benchmarks
        q_found = False
        questions = data.get('benchmarks', {}).get('questions', [])
        
        if len(questions) >= q_num:
            question_obj = questions[q_num - 1]  # 0-indexed
            answer_list = question_obj.get('answer', [])
            
            if answer_list and 'content' in answer_list[0]:
                old_sql = ''.join(answer_list[0]['content']).strip()
                
                # Apply fix
                if fix_info['old'] in old_sql:
                    new_sql = old_sql.replace(fix_info['old'], fix_info['new'])
                    answer_list[0]['content'] = [new_sql]
                    print(f"  ✅ Q{q_num}: {fix_info['description']}")
                    fixed_count += 1
                    q_found = True
                else:
                    print(f"  ⚠️  Q{q_num}: Pattern not found exactly - manual fix needed")
                    print(f"      Expected: {fix_info['old'][:80]}...")
                    print(f"      Found: {old_sql[:80]}...")
        
        if not q_found and q_num <= len(questions):
            print(f"  ❌ Q{q_num}: Could not apply fix")
    
    # Save fixed JSON
    if fixed_count > 0:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  💾 Saved {fixed_count} fixes to {file_path.name}")
    
    return fixed_count

def main():
    """Apply all fixes."""
    print("=" * 80)
    print("GENIE SPACE REMAINING ERROR FIXES")
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
    print(f"✅ COMPLETE: Fixed {total_fixed} queries")
    print("=" * 80)

if __name__ == "__main__":
    main()

