#!/usr/bin/env python3
"""
Fix concatenation bug and WRONG_NUM_ARGS errors from previous fix scripts.

Critical Issues:
1. Function names concatenated with CAST: get_slow_queriesCAST( → get_slow_queries(
2. Too many parameters added to TVF calls

Usage:
    python3 scripts/fix_genie_concatenation_bug.py
"""

import json
from pathlib import Path

# Define exact fixes
FIXES = {
    'performance': {
        5: {
            'old': '''SELECT * FROM get_slow_queriesCAST(  CURRENT_DATE( AS STRING),  CAST(CURRENT_DATE() AS STRING),  30,  50) ORDER BY duration_seconds DESC LIMIT 1''',
            'new': '''SELECT * FROM get_slow_queries(
  CAST(CURRENT_DATE() AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  30,
  50
) ORDER BY duration_seconds DESC LIMIT 1;'''
        },
        8: {
            # Remove the 4th parameter (1.0) - TVF only takes 3 params
            'old': '''SELECT * FROM get_high_spill_queries(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5.0,
  1.0
) ORDER BY spill_bytes DESC LIMIT 15;''',
            'new': '''SELECT * FROM get_high_spill_queries(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5.0
) ORDER BY spill_bytes DESC LIMIT 15;'''
        }
    },
    'security_auditor': {
        5: {
            # Remove the 4th parameter (20) - TVF only takes 3 params
            'old': '''SELECT * FROM get_user_activity_summary(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  10,
  20
) ORDER BY total_events DESC LIMIT 20;''',
            'new': '''SELECT * FROM get_user_activity_summary(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  10
) ORDER BY total_events DESC LIMIT 20;'''
        },
        7: {
            'old': '''SELECT * FROM get_failed_actionsCAST(
  7,
  CURRENT_DATE( AS STRING),
  '%'
) ORDER BY event_time DESC LIMIT 1''',
            'new': '''SELECT * FROM get_failed_actions(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  '%'
) ORDER BY event_time DESC LIMIT 20;'''
        }
    },
    'unified_health_monitor': {
        7: {
            'old': '''SELECT * FROM get_failed_jobsCAST(
  1,
  CURRENT_DATE( AS STRING),
  '%'
) ORDER BY start_time DESC LIMIT 1''',
            'new': '''SELECT * FROM get_failed_jobs(
  CAST(CURRENT_DATE() - INTERVAL 1 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  '%'
) ORDER BY start_time DESC LIMIT 20;'''
        },
        8: {
            'old': '''SELECT * FROM get_slow_queriesCAST(  CURRENT_DATE( AS STRING),  CAST(CURRENT_DATE() AS STRING),  30,  50) ORDER BY duration_seconds DESC LIMIT 1''',
            'new': '''SELECT * FROM get_slow_queries(
  CAST(CURRENT_DATE() AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  30,
  50
) ORDER BY duration_seconds DESC LIMIT 15;'''
        }
    }
}

def apply_fix(sql: str, fix_config: dict) -> tuple[str, bool]:
    """Apply a single fix to SQL. Returns (fixed_sql, was_changed)."""
    if fix_config['old'] in sql:
        return fix_config['new'], True
    return sql, False

def process_genie_space(file_path: Path, fixes_config: dict) -> dict:
    """Process a single Genie Space JSON file and apply exact fixes."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    space_name = file_path.stem.replace('_genie_export', '')
    fixes_summary = {
        'file': file_path.name,
        'space': space_name,
        'queries_fixed': 0,
        'fixes': []
    }
    
    if space_name not in fixes_config:
        return fixes_summary
    
    if 'benchmarks' not in data or 'questions' not in data['benchmarks']:
        return fixes_summary
    
    questions = data['benchmarks']['questions']
    space_fixes = fixes_config[space_name]
    
    for q_num, fix_config in space_fixes.items():
        idx = q_num - 1  # 0-indexed
        if idx < len(questions):
            question = questions[idx]
            if 'answer' in question and len(question['answer']) > 0:
                if 'content' in question['answer'][0] and len(question['answer'][0]['content']) > 0:
                    original_sql = question['answer'][0]['content'][0]
                    fixed_sql, was_changed = apply_fix(original_sql, fix_config)
                    
                    if was_changed:
                        question['answer'][0]['content'][0] = fixed_sql
                        fixes_summary['queries_fixed'] += 1
                        fixes_summary['fixes'].append({
                            'q_num': q_num,
                            'question': question['question'][0][:60] + '...'
                        })
    
    # Write back if changes were made
    if fixes_summary['queries_fixed'] > 0:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixes_summary

def main():
    """Process all Genie Space JSON files with concatenation bug fixes."""
    genie_dir = Path('src/genie')
    
    print("=" * 80)
    print("GENIE SPACE CONCATENATION BUG FIXER")
    print("=" * 80)
    print()
    print("Fixing:")
    print("  1. Function name concatenation: get_slow_queriesCAST( → get_slow_queries(")
    print("  2. WRONG_NUM_ARGS: Remove extra parameters from TVF calls")
    print()
    
    all_summaries = []
    total_queries_fixed = 0
    
    for space_name in FIXES.keys():
        file_path = genie_dir / f"{space_name}_genie_export.json"
        if file_path.exists():
            print(f"Processing {file_path.name}...")
            summary = process_genie_space(file_path, FIXES)
            all_summaries.append(summary)
            total_queries_fixed += summary['queries_fixed']
            
            if summary['queries_fixed'] > 0:
                print(f"  ✓ Fixed {summary['queries_fixed']} queries")
                for fix in summary['fixes']:
                    print(f"    • Q{fix['q_num']}: {fix['question']}")
            else:
                print(f"  • No fixes needed")
            print()
    
    print("=" * 80)
    print(f"SUMMARY: Fixed {total_queries_fixed} queries across {len([s for s in all_summaries if s['queries_fixed'] > 0])} files")
    print("=" * 80)
    print()
    print("Fixes Applied:")
    print("  - Function concatenation bugs: 4 queries")
    print("  - WRONG_NUM_ARGS (extra parameters): 2 queries")
    print(f"  - **TOTAL**: {total_queries_fixed} critical fixes")
    print()
    print("Next steps:")
    print("1. Deploy: DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle deploy -t dev")
    print("2. Re-validate: DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev genie_benchmark_sql_validation_job")

if __name__ == '__main__':
    main()

