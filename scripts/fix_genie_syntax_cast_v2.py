#!/usr/bin/env python3
"""
Fix SYNTAX_ERROR and CAST_INVALID_INPUT errors - Version 2 with exact replacements.
"""

import json
from pathlib import Path

# Define exact SQL replacements for problematic queries
EXACT_FIXES = {
    'job_health_monitor': {
        4: {
            'old': '''SELECT * FROM get_failed_jobsCAST(
  1,
  CURRENT_DATE( AS STRING),
  '%'
) ORDER BY job_name DESC LIMIT 20;''',
            'new': '''SELECT * FROM get_failed_jobs(
  CAST(CURRENT_DATE() - INTERVAL 1 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  '%'
) ORDER BY job_name DESC LIMIT 20;'''
        },
        7: {
            'partial_match': 'get_job_success_rate',
            'old_pattern': '''get_job_success_rate(
  30,
  CAST(CURRENT_DATE() AS STRING),
  5
)''',
            'new_pattern': '''get_job_success_rate(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5
)'''
        },
        12: {
            'partial_match': 'get_job_repair_costs',
            'old_pattern': '''get_job_repair_costs(
  30,
  CAST(CURRENT_DATE() AS STRING),
  10
)''',
            'new_pattern': '''get_job_repair_costs(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  10
)'''
        }
    },
    'performance': {
        8: {
            'old': '''SELECT * FROM get_high_spill_queries(
  (CURRENT_DATE(), CAST(CURRENT_DATE() AS STRING),
  5.0
) - INTERVAL 7 DAYS)::STRING,  CAST(CURRENT_DATE() AS STRING),  1.0) ORDER BY spill_bytes DESC LIMIT 15;''',
            'new': '''SELECT * FROM get_high_spill_queries(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5.0,
  1.0
) ORDER BY spill_bytes DESC LIMIT 15;'''
        }
    },
    'security_auditor': {
        5: {
            'old': '''SELECT * FROM get_user_activity_summary(
  CAST(CURRENT_DATE(), CAST(CURRENT_DATE() AS STRING),
  10
) - INTERVAL 7 DAYS AS STRING),  CAST(CURRENT_DATE() AS STRING),  20) ORDER BY total_events DESC;''',
            'new': '''SELECT * FROM get_user_activity_summary(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  10,
  20
) ORDER BY total_events DESC LIMIT 20;'''
        },
        6: {
            'old': '''SELECT * FROM get_sensitive_table_access(
  CAST(CURRENT_DATE(), CAST(CURRENT_DATE() AS STRING),
  '%'
) - INTERVAL 7 DAYS AS STRING),  CAST(CURRENT_DATE() AS STRING)) ORDER BY access_count DESC LIMIT 20;''',
            'new': '''SELECT * FROM get_sensitive_table_access(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  '%'
) ORDER BY access_count DESC LIMIT 20;'''
        },
        8: {
            'partial_match': 'get_permission_changes',
            'old_pattern': '''get_permission_changes(
  7,
  CAST(CURRENT_DATE() AS STRING)
)''',
            'new_pattern': '''get_permission_changes(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
)'''
        }
    },
    'unified_health_monitor': {
        12: {
            'partial_match': 'get_warehouse_utilization',
            'old_pattern': '''get_warehouse_utilization(
  7,
  CAST(CURRENT_DATE() AS STRING)
)''',
            'new_pattern': '''get_warehouse_utilization(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
)'''
        }
    }
}

def apply_fix(sql: str, fix_config: dict) -> tuple[str, bool]:
    """Apply a single fix to SQL. Returns (fixed_sql, was_changed)."""
    if 'old' in fix_config:
        # Exact replacement
        if fix_config['old'] in sql:
            return fix_config['new'], True
    elif 'partial_match' in fix_config:
        # Partial pattern replacement
        if fix_config['old_pattern'] in sql:
            return sql.replace(fix_config['old_pattern'], fix_config['new_pattern']), True
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
    """Process all Genie Space JSON files with exact fixes."""
    genie_dir = Path('src/genie')
    
    print("=" * 80)
    print("GENIE SPACE SYNTAX/CAST ERROR FIXER V2 (Exact Replacements)")
    print("=" * 80)
    print()
    
    all_summaries = []
    total_queries_fixed = 0
    
    for space_name in EXACT_FIXES.keys():
        file_path = genie_dir / f"{space_name}_genie_export.json"
        if file_path.exists():
            print(f"Processing {file_path.name}...")
            summary = process_genie_space(file_path, EXACT_FIXES)
            all_summaries.append(summary)
            total_queries_fixed += summary['queries_fixed']
            
            if summary['queries_fixed'] > 0:
                print(f"  ✓ Fixed {summary['queries_fixed']} queries")
                for fix in summary['fixes']:
                    print(f"    • Q{fix['q_num']}: {fix['question']}")
            else:
                print(f"  • No fixes applied (patterns may have already been fixed)")
            print()
    
    print("=" * 80)
    print(f"SUMMARY: Fixed {total_queries_fixed} queries across {len([s for s in all_summaries if s['queries_fixed'] > 0])} files")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Deploy bundle: DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle deploy -t dev")
    print("2. Re-run validation: DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev genie_benchmark_sql_validation_job")

if __name__ == '__main__':
    main()

