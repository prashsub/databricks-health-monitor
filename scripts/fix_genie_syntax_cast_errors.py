#!/usr/bin/env python3
"""
Fix SYNTAX_ERROR and CAST_INVALID_INPUT errors in Genie Space SQL queries.

Patterns Fixed:
1. PostgreSQL-style ::STRING casting → CAST(...AS STRING)
2. Numeric day counts → Proper date STRING parameters
3. Malformed CAST statements → Correct SQL syntax
4. Complex CTE syntax errors → Manual review needed

Usage:
    python3 scripts/fix_genie_syntax_cast_errors.py
"""

import json
import re
from pathlib import Path

def fix_postgresql_cast(sql: str) -> str:
    """
    Fix PostgreSQL-style ::STRING casting to SQL CAST syntax.
    
    Examples:
        CURRENT_DATE()::STRING → CAST(CURRENT_DATE() AS STRING)
        (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING → CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING)
    """
    # Pattern: (...expression...)::STRING
    pattern = r'\(([^)]+)\)::STRING'
    replacement = r'CAST(\1 AS STRING)'
    sql = re.sub(pattern, replacement, sql, flags=re.DOTALL)
    
    # Pattern: CURRENT_DATE()::STRING (without parens around DATE)
    pattern2 = r'CURRENT_DATE\(\)::STRING'
    replacement2 = r'CAST(CURRENT_DATE() AS STRING)'
    sql = re.sub(pattern2, replacement2, sql)
    
    return sql

def fix_numeric_date_parameters(sql: str) -> str:
    """
    Fix TVF calls that pass numeric day counts instead of STRING dates.
    
    TVF signatures expect:
        start_date STRING (format: YYYY-MM-DD)
        end_date STRING (format: YYYY-MM-DD)
    
    Patterns to fix:
        get_failed_jobs(1, ...) → get_failed_jobs(CAST(CURRENT_DATE() - INTERVAL 1 DAYS AS STRING), ...)
        get_failed_jobs(7, ...) → get_failed_jobs(CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING), ...)
        get_failed_jobs(30, ...) → get_failed_jobs(CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING), ...)
    """
    
    # Pattern 1: Single-digit day count at start of TVF call
    # get_failed_jobs(\n  1,
    pattern1 = r'(get_(?:failed_jobs|job_success_rate|job_repair_costs|warehouse_utilization|permission_changes))\(\s*(\d+),\s*(CAST\(CURRENT_DATE\(\)|CURRENT_DATE\(\))'
    replacement1 = r"\1(\n  CAST(CURRENT_DATE() - INTERVAL \2 DAYS AS STRING),\n  \3"
    sql = re.sub(pattern1, replacement1, sql)
    
    return sql

def fix_malformed_cast_security(sql: str) -> str:
    """
    Fix malformed CAST statements in security_auditor queries.
    
    Pattern:
        CAST(CURRENT_DATE(), CURRENT_DATE()::STRING,
          10
        ) - INTERVAL 7 DAYS AS STRING)
    
    Should be:
        CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
        CAST(CURRENT_DATE() AS STRING),
        10
    """
    
    # Fix security_auditor Q5 pattern
    pattern_q5 = r'CAST\(CURRENT_DATE\(\), CURRENT_DATE\(\)::STRING,\s+(\d+)\s*\) - INTERVAL (\d+) DAYS AS STRING\)'
    replacement_q5 = r'CAST(CURRENT_DATE() - INTERVAL \2 DAYS AS STRING),\n  CAST(CURRENT_DATE() AS STRING),\n  \1'
    sql = re.sub(pattern_q5, replacement_q5, sql, flags=re.DOTALL)
    
    # Fix security_auditor Q6 pattern (similar but with extra param)
    pattern_q6 = r'CAST\(CURRENT_DATE\(\), CURRENT_DATE\(\)::STRING,\s+(\'[^\']+\')\s*\) - INTERVAL (\d+) DAYS AS STRING\)'
    replacement_q6 = r'CAST(CURRENT_DATE() - INTERVAL \2 DAYS AS STRING),\n  CAST(CURRENT_DATE() AS STRING),\n  \1'
    sql = re.sub(pattern_q6, replacement_q6, sql, flags=re.DOTALL)
    
    return sql

def fix_performance_q8(sql: str) -> str:
    """
    Fix performance Q8: get_high_spill_queries with completely malformed parameters.
    
    Current (broken):
        SELECT * FROM get_high_spill_queries(
          (CURRENT_DATE(), CURRENT_DATE()::STRING,
          5.0
        ) - INTERVAL 7 DAYS)::STRING,  CURRENT_DATE()::STRING,  1.0)
    
    Should be:
        SELECT * FROM get_high_spill_queries(
          CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
          CAST(CURRENT_DATE() AS STRING),
          5.0,
          1.0)
    """
    
    # This is too complex for regex - do exact replacement
    broken_pattern = r'get_high_spill_queries\(\s*\(CURRENT_DATE\(\), CURRENT_DATE\(\)::STRING,\s*5\.0\s*\) - INTERVAL 7 DAYS\)::STRING,\s*CURRENT_DATE\(\)::STRING,\s*1\.0\)'
    fixed_text = '''get_high_spill_queries(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5.0,
  1.0)'''
    
    sql = re.sub(broken_pattern, fixed_text, sql, flags=re.DOTALL)
    
    return sql

def apply_fixes_to_query(sql: str, space_name: str, q_num: int) -> tuple[str, list[str]]:
    """Apply all fixes to a SQL query and return fixed SQL + list of fixes applied."""
    fixes_applied = []
    original_sql = sql
    
    # Fix 1: PostgreSQL-style casting
    sql = fix_postgresql_cast(sql)
    if sql != original_sql:
        fixes_applied.append("PostgreSQL ::STRING → CAST(...AS STRING)")
        original_sql = sql
    
    # Fix 2: Malformed security CAST statements
    sql = fix_malformed_cast_security(sql)
    if sql != original_sql:
        fixes_applied.append("Fixed malformed CAST(CURRENT_DATE(), ...)")
        original_sql = sql
    
    # Fix 3: performance Q8 specific fix
    if space_name == 'performance' and q_num == 8:
        sql = fix_performance_q8(sql)
        if sql != original_sql:
            fixes_applied.append("Fixed get_high_spill_queries malformed parameters")
            original_sql = sql
    
    # Fix 4: Numeric date parameters
    sql = fix_numeric_date_parameters(sql)
    if sql != original_sql:
        fixes_applied.append("Numeric day count → CAST(CURRENT_DATE() - INTERVAL N DAYS AS STRING)")
        original_sql = sql
    
    return sql, fixes_applied

def process_genie_space(file_path: Path) -> dict:
    """Process a single Genie Space JSON file and apply fixes."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    space_name = file_path.stem.replace('_genie_export', '')
    fixes_summary = {
        'file': file_path.name,
        'space': space_name,
        'queries_fixed': 0,
        'fixes': []
    }
    
    if 'benchmarks' not in data or 'questions' not in data['benchmarks']:
        return fixes_summary
    
    questions = data['benchmarks']['questions']
    
    for idx, question in enumerate(questions):
        q_num = idx + 1
        if 'answer' in question and len(question['answer']) > 0:
            if 'content' in question['answer'][0] and len(question['answer'][0]['content']) > 0:
                original_sql = question['answer'][0]['content'][0]
                fixed_sql, fixes_applied = apply_fixes_to_query(original_sql, space_name, q_num)
                
                if fixes_applied:
                    question['answer'][0]['content'][0] = fixed_sql
                    fixes_summary['queries_fixed'] += 1
                    fixes_summary['fixes'].append({
                        'q_num': q_num,
                        'question': question['question'][0][:60] + '...',
                        'fixes': fixes_applied
                    })
    
    # Write back if changes were made
    if fixes_summary['queries_fixed'] > 0:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixes_summary

def main():
    """Process all Genie Space JSON files."""
    genie_dir = Path('src/genie')
    json_files = list(genie_dir.glob('*_genie_export.json'))
    
    print("=" * 80)
    print("GENIE SPACE SYNTAX/CAST ERROR FIXER")
    print("=" * 80)
    print(f"\nFound {len(json_files)} Genie Space JSON files\n")
    
    all_summaries = []
    total_queries_fixed = 0
    
    for file_path in sorted(json_files):
        print(f"Processing {file_path.name}...")
        summary = process_genie_space(file_path)
        all_summaries.append(summary)
        total_queries_fixed += summary['queries_fixed']
        
        if summary['queries_fixed'] > 0:
            print(f"  ✓ Fixed {summary['queries_fixed']} queries")
            for fix in summary['fixes']:
                print(f"    • Q{fix['q_num']}: {fix['question']}")
                for fix_type in fix['fixes']:
                    print(f"      - {fix_type}")
        else:
            print(f"  • No fixes needed")
        print()
    
    print("=" * 80)
    print(f"SUMMARY: Fixed {total_queries_fixed} queries across {len([s for s in all_summaries if s['queries_fixed'] > 0])} files")
    print("=" * 80)
    
    # Write detailed report
    with open('docs/deployment/GENIE_SYNTAX_CAST_FIXES.md', 'w') as f:
        f.write("# Genie Space SYNTAX/CAST Error Fixes\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total queries fixed**: {total_queries_fixed}\n")
        f.write(f"- **Files modified**: {len([s for s in all_summaries if s['queries_fixed'] > 0])}\n\n")
        f.write("## Detailed Changes\n\n")
        
        for summary in all_summaries:
            if summary['queries_fixed'] > 0:
                f.write(f"### {summary['space']}\n\n")
                f.write(f"**File**: `{summary['file']}`  \n")
                f.write(f"**Queries fixed**: {summary['queries_fixed']}\n\n")
                
                for fix in summary['fixes']:
                    f.write(f"#### Q{fix['q_num']}: {fix['question']}\n\n")
                    for fix_type in fix['fixes']:
                        f.write(f"- {fix_type}\n")
                    f.write("\n")
                f.write("\n")
    
    print("\n✓ Detailed report written to: docs/deployment/GENIE_SYNTAX_CAST_FIXES.md")

if __name__ == '__main__':
    main()

