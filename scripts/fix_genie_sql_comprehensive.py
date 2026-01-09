#!/usr/bin/env python3
"""
Comprehensive Genie SQL Fix Script

Fixes all known SQL issues in genie benchmark exports:
1. TABLE() wrapper closing - ensures ))
2. TVF argument types - dates should be STRING not INT
3. DATE_TRUNC syntax - proper casting
4. Missing semicolons
5. Column name corrections
"""

import json
import re
from pathlib import Path
from typing import List, Tuple

BASE_PATH = Path("/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor")
GENIE_PATH = BASE_PATH / "src" / "genie"


def load_json(file_path: Path) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: dict, file_path: Path):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fix_sql_query(sql: str, question_hint: str = "") -> Tuple[str, List[str]]:
    """
    Fix SQL query issues. Returns (fixed_sql, list_of_fixes_applied)
    """
    fixes = []
    original = sql

    # Fix 1: DATE_TRUNC syntax - should be CAST(DATE_TRUNC('unit', date) AS STRING)
    # Bad: DATE_TRUNC('month', CAST(CURRENT_DATE() AS STRING)
    # Good: CAST(DATE_TRUNC('month', CURRENT_DATE()) AS STRING)
    bad_date_trunc = r"DATE_TRUNC\s*\(\s*'(\w+)'\s*,\s*CAST\s*\(\s*CURRENT_DATE\s*\(\s*\)\s*AS\s*STRING\s*\)"
    if re.search(bad_date_trunc, sql, re.IGNORECASE):
        sql = re.sub(
            bad_date_trunc,
            r"CAST(DATE_TRUNC('\1', CURRENT_DATE()) AS STRING)",
            sql,
            flags=re.IGNORECASE
        )
        fixes.append("Fixed DATE_TRUNC syntax")

    # Fix 2: get_cost_anomalies with wrong arguments (30, 50.0) -> proper date strings
    # Bad: get_cost_anomalies(30, 50.0)
    # Good: get_cost_anomalies(CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING), CAST(CURRENT_DATE() AS STRING), 2.0)
    bad_anomaly_args = r"get_cost_anomalies\s*\(\s*30\s*,\s*50\.0\s*\)"
    if re.search(bad_anomaly_args, sql, re.IGNORECASE):
        sql = re.sub(
            bad_anomaly_args,
            r"get_cost_anomalies(CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING), CAST(CURRENT_DATE() AS STRING), 2.0)",
            sql,
            flags=re.IGNORECASE
        )
        fixes.append("Fixed get_cost_anomalies arguments")

    # Fix 3: TABLE() with single ) should be ))
    # Pattern: TABLE(...get_xxx(...)) followed by ORDER/WHERE/etc without proper closure
    # Look for lines that end with ) but should end with ))
    lines = sql.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if line has TABLE( but content ends with single )
        if 'TABLE(' in line.upper():
            # Collect all lines until we see the end of TABLE() call
            table_block = [line]
            paren_count = line.upper().count('TABLE(')  # Start with TABLE( open

            for char in line:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1

            j = i + 1
            while j < len(lines) and paren_count > 0:
                next_line = lines[j]
                table_block.append(next_line)
                for char in next_line:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                j += 1

            # Check if last line of block ends with single ) followed by keyword
            if table_block:
                last_line = table_block[-1].strip()
                # If ends with ) but next non-empty line starts with ORDER/WHERE/etc
                if last_line.endswith(')') and not last_line.endswith('))'):
                    # Check what comes next
                    next_idx = j
                    while next_idx < len(lines):
                        next_stripped = lines[next_idx].strip().upper()
                        if next_stripped:  # Non-empty line
                            if next_stripped.startswith(('ORDER', 'WHERE', 'GROUP', 'HAVING', 'LIMIT')):
                                # Need to add ) to close TABLE()
                                table_block[-1] = table_block[-1].rstrip() + ')'
                                fixes.append("Added closing ) for TABLE()")
                            break
                        next_idx += 1

            fixed_lines.extend(table_block)
            i = j
        else:
            fixed_lines.append(line)
            i += 1

    sql = '\n'.join(fixed_lines)

    # Fix 4: Ensure semicolon at end
    sql_stripped = sql.strip()
    if sql_stripped and not sql_stripped.endswith(';'):
        sql = sql_stripped + ';'
        fixes.append("Added missing semicolon")

    # Fix 5: Column name corrections
    column_fixes = {
        r'\bdeviation_pct\b': 'z_score',
        r'\bp99_duration\b': 'p95_duration_minutes',
        r'\bp90_duration\b': 'p95_duration_minutes',
        r'\bsuccess_rate\b(?!\s*[,\)])': 'ROUND(100.0 * (total_events - failed_events) / NULLIF(total_events, 0), 2)',
    }
    for pattern, replacement in column_fixes.items():
        if re.search(pattern, sql, re.IGNORECASE):
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
            fixes.append(f"Fixed column: {pattern} -> {replacement[:30]}")

    return sql, fixes


def fix_content_array(content: List[str]) -> Tuple[List[str], List[str]]:
    """Fix SQL content array and return (fixed_content, fixes)"""
    # Remove empty strings
    non_empty = [line for line in content if line.strip()]

    # Join and fix
    sql = '\n'.join(non_empty)
    fixed_sql, fixes = fix_sql_query(sql)

    # Split back into array
    return fixed_sql.split('\n'), fixes


def process_genie_export(file_path: Path) -> Tuple[int, List[dict]]:
    """Process a genie export file and fix SQL content."""
    data = load_json(file_path)

    benchmarks = data.get('benchmarks', {}).get('questions', [])
    fixed_count = 0
    all_fixes = []

    for i, benchmark in enumerate(benchmarks):
        question = benchmark.get('question', [''])[0][:60] if benchmark.get('question') else 'Unknown'
        answers = benchmark.get('answer', [])

        for answer in answers:
            if answer.get('format') == 'SQL':
                content = answer.get('content', [])
                if isinstance(content, list):
                    fixed_content, fixes = fix_content_array(content)
                    if fixes:
                        fixed_count += 1
                        all_fixes.append({
                            'question': f"Q{i+1}: {question}",
                            'fixes': fixes
                        })
                    answer['content'] = fixed_content

    data['benchmarks']['questions'] = benchmarks
    save_json(data, file_path)

    return fixed_count, all_fixes


def main():
    """Fix all genie export files."""
    print("=" * 70)
    print("COMPREHENSIVE GENIE SQL FIX")
    print("=" * 70)
    print()
    print("Fixes:")
    print("- DATE_TRUNC syntax errors")
    print("- TVF argument type errors")
    print("- TABLE() missing closing parenthesis")
    print("- Missing semicolons")
    print("- Column name corrections")
    print()

    genie_files = [
        "cost_intelligence_genie_export.json",
        "job_health_monitor_genie_export.json",
        "performance_genie_export.json",
        "security_auditor_genie_export.json",
        "unified_health_monitor_genie_export.json",
        "data_quality_monitor_genie_export.json",
    ]

    total_fixed = 0
    for genie_file in genie_files:
        file_path = GENIE_PATH / genie_file
        if not file_path.exists():
            print(f"\n{genie_file}: NOT FOUND")
            continue

        print(f"\n{genie_file}:")
        fixed, fixes = process_genie_export(file_path)
        total_fixed += fixed

        if fixes:
            for fix in fixes:
                print(f"  {fix['question']}")
                for f in fix['fixes']:
                    print(f"    - {f}")
        else:
            print("  No fixes needed")

    print()
    print("=" * 70)
    print(f"DONE - Fixed {total_fixed} queries")
    print("=" * 70)


if __name__ == "__main__":
    main()
