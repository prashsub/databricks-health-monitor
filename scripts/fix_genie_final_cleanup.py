#!/usr/bin/env python3
"""
Final cleanup of all SYNTAX/CAST errors in Genie Space SQL queries.
Fixes the concatenation issues and numeric day count parameters.
"""

import json
from pathlib import Path

# Define exact SQL replacements
FINAL_FIXES = {
    'job_health_monitor': {
        7: {
            'old': '''SELECT * FROM get_job_success_rateCAST(
  30,
  CURRENT_DATE( AS STRING),
  5
) ORDER BY success_rate_pct ASC LIMIT 10;''',
            'new': '''SELECT * FROM get_job_success_rate(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5
) ORDER BY success_rate_pct ASC LIMIT 10;'''
        },
        12: {
            'old': '''SELECT * FROM get_job_repair_costsCAST(
  30,
  CURRENT_DATE( AS STRING),
  10
) ORDER BY repair_cost DESC LIMIT 15;''',
            'new': '''SELECT * FROM get_job_repair_costs(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  10
) ORDER BY repair_cost DESC LIMIT 15;'''
        }
    },
    'security_auditor': {
        8: {
            'old': '''SELECT * FROM get_permission_changesCAST(
  7,
  CURRENT_DATE( AS STRING)
) ORDER BY event_time DESC LIMIT 20;''',
            'new': '''SELECT * FROM get_permission_changes(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
) ORDER BY event_time DESC LIMIT 20;'''
        }
    },
    'unified_health_monitor': {
        12: {
            'old': '''SELECT * FROM get_warehouse_utilizationCAST(
  7,
  CURRENT_DATE( AS STRING)
) ORDER BY total_queries DESC LIMIT 10;''',
            'new': '''SELECT * FROM get_warehouse_utilization(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
) ORDER BY total_queries DESC LIMIT 10;'''
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
    """Process all Genie Space JSON files with final cleanup fixes."""
    genie_dir = Path('src/genie')
    
    print("=" * 80)
    print("GENIE SPACE FINAL CLEANUP - SYNTAX/CAST ERRORS")
    print("=" * 80)
    print()
    
    all_summaries = []
    total_queries_fixed = 0
    
    for space_name in FINAL_FIXES.keys():
        file_path = genie_dir / f"{space_name}_genie_export.json"
        if file_path.exists():
            print(f"Processing {file_path.name}...")
            summary = process_genie_space(file_path, FINAL_FIXES)
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
    print(f"FINAL SUMMARY: Fixed {total_queries_fixed} queries across {len([s for s in all_summaries if s['queries_fixed'] > 0])} files")
    print("=" * 80)
    print()
    
    # Count total fixes across all scripts
    print("📊 Total SYNTAX/CAST fixes applied across all scripts:")
    print("  - Script 1 (PostgreSQL ::): 16 queries")
    print("  - Script 2 (Malformed CAST): 4 queries")
    print(f"  - Script 3 (Final cleanup): {total_queries_fixed} queries")
    print(f"  - **TOTAL**: {16 + 4 + total_queries_fixed} queries fixed")
    print()
    print("Next steps:")
    print("1. Deploy: DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle deploy -t dev")
    print("2. Validate: DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev genie_benchmark_sql_validation_job")

if __name__ == '__main__':
    main()

