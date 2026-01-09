#!/usr/bin/env python3
"""
Fix SYNTAX_ERROR patterns in Genie Space JSON files.

Fixes:
1. CURRENT_DATE(, pattern → CURRENT_DATE()
2. Malformed date interval expressions
3. Missing closing parentheses in complex queries
"""

import json
import re
from pathlib import Path

def fix_current_date_pattern(sql: str) -> tuple[str, bool]:
    """
    Fix malformed CURRENT_DATE(, patterns.
    
    Pattern: CAST(CURRENT_DATE(,\n  CURRENT_DATE()::STRING\n) - INTERVAL X DAYS AS STRING)
    Fix: CAST(CURRENT_DATE() - INTERVAL X DAYS AS STRING)
    
    Returns: (fixed_sql, was_fixed)
    """
    original = sql
    
    # Pattern 1: CAST(CURRENT_DATE(, ... ) - INTERVAL X DAYS AS STRING)
    # The malformed part has a comma and extra CURRENT_DATE()::STRING
    pattern1 = r'CAST\(\s*CURRENT_DATE\(\s*,\s*[\\n\s]*CURRENT_DATE\(\)::STRING\s*[\\n\s]*\)\s*-\s*INTERVAL\s+(\d+)\s+(DAYS?|MONTHS?)\s+AS\s+STRING\)'
    replacement1 = r'CAST(CURRENT_DATE() - INTERVAL \1 \2 AS STRING)'
    sql = re.sub(pattern1, replacement1, sql, flags=re.IGNORECASE | re.DOTALL)
    
    # Pattern 2: (CURRENT_DATE(, ... )::STRING
    pattern2 = r'\(\s*CURRENT_DATE\(\s*,\s*[\\n\s]*CURRENT_DATE\(\)::STRING\s*[\\n\s]*\)\s*-\s*INTERVAL\s+(\d+)\s+(DAYS?|MONTHS?)\s*\)::STRING'
    replacement2 = r'(CURRENT_DATE() - INTERVAL \1 \2)::STRING'
    sql = re.sub(pattern2, replacement2, sql, flags=re.IGNORECASE | re.DOTALL)
    
    # Pattern 3: Just CURRENT_DATE(, without the complex CAST
    # This is likely a malformed opening parenthesis
    pattern3 = r'CURRENT_DATE\(\s*,\s*'
    replacement3 = r'CURRENT_DATE(), '
    sql = re.sub(pattern3, replacement3, sql, flags=re.IGNORECASE)
    
    return sql, sql != original

def fix_missing_parentheses(sql: str) -> tuple[str, bool]:
    """
    Fix missing closing parentheses in complex queries.
    
    This is a basic check - manually validate results!
    
    Returns: (fixed_sql, was_fixed)
    """
    original = sql
    
    # Count opening and closing parentheses
    open_count = sql.count('(')
    close_count = sql.count(')')
    
    if open_count > close_count:
        # Add missing closing parentheses at the end
        missing = open_count - close_count
        sql += ')' * missing
        return sql, True
    
    return sql, False

def fix_json_file(json_path: Path) -> dict:
    """Fix SYNTAX_ERROR patterns in a single JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixes_applied = []
    
    # Iterate through benchmark questions
    if 'benchmarks' in data and 'questions' in data['benchmarks']:
        for q in data['benchmarks']['questions']:
            # Handle structure: answer[0].content[0]
            if 'answer' in q and len(q['answer']) > 0:
                answer_block = q['answer'][0]
                if 'content' in answer_block and len(answer_block['content']) > 0:
                    sql = answer_block['content'][0]
                    question_id = q.get('id', 'unknown')
                    
                    # Try fixing CURRENT_DATE pattern
                    fixed_sql, was_fixed = fix_current_date_pattern(sql)
                    if was_fixed:
                        answer_block['content'][0] = fixed_sql
                        fixes_applied.append({
                            'question_id': question_id,
                            'fix_type': 'CURRENT_DATE_PATTERN',
                            'before_snippet': sql[:100],
                            'after_snippet': fixed_sql[:100]
                        })
                        sql = fixed_sql
                
                    # Try fixing missing parentheses (be careful!)
                    # This is disabled by default - too risky for automated fix
                    # fixed_sql, was_fixed = fix_missing_parentheses(sql)
                    # if was_fixed:
                    #     answer_block['content'][0] = fixed_sql
                    #     fixes_applied.append({
                    #         'question_id': question_id,
                    #         'fix_type': 'MISSING_PARENTHESES',
                    #         'added_count': sql.count(')') - fixed_sql.count(')')
                    #     })
    
    # Write back to file
    if fixes_applied:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return {
        'file': json_path.name,
        'fixes_applied': len(fixes_applied),
        'details': fixes_applied
    }

def main():
    genie_dir = Path('src/genie')
    json_files = list(genie_dir.glob('*_genie_export.json'))
    
    print("=" * 80)
    print("GENIE SPACE SYNTAX_ERROR FIXER")
    print("=" * 80)
    print(f"Found {len(json_files)} Genie Space JSON files\n")
    
    all_results = []
    total_fixes = 0
    
    for json_file in sorted(json_files):
        print(f"Processing: {json_file.name}")
        result = fix_json_file(json_file)
        all_results.append(result)
        total_fixes += result['fixes_applied']
        
        if result['fixes_applied'] > 0:
            print(f"  ✅ Applied {result['fixes_applied']} fixes")
            for detail in result['details']:
                print(f"     - {detail['question_id']}: {detail['fix_type']}")
        else:
            print(f"  ⚪ No fixes needed")
        print()
    
    print("=" * 80)
    print(f"✅ COMPLETE: Applied {total_fixes} fixes across {len(json_files)} files")
    print("=" * 80)
    
    # Write summary report
    summary_path = Path('docs/deployment/GENIE_SYNTAX_ERROR_FIXES.md')
    with open(summary_path, 'w') as f:
        f.write("# Genie Space SYNTAX_ERROR Fixes Applied\n\n")
        f.write(f"**Date:** 2026-01-08\n")
        f.write(f"**Total Fixes:** {total_fixes}\n\n")
        f.write("## Files Modified\n\n")
        for result in all_results:
            if result['fixes_applied'] > 0:
                f.write(f"### {result['file']}\n\n")
                f.write(f"**Fixes Applied:** {result['fixes_applied']}\n\n")
                for detail in result['details']:
                    f.write(f"- **{detail['question_id']}**: {detail['fix_type']}\n")
                    f.write(f"  - Before: `{detail['before_snippet']}...`\n")
                    f.write(f"  - After: `{detail['after_snippet']}...`\n\n")
    
    print(f"\n📄 Summary report written to: {summary_path}")

if __name__ == '__main__':
    main()

