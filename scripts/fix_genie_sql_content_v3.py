#!/usr/bin/env python3
"""
Fix Genie Benchmark SQL Content - Version 3

CRITICAL FIXES:
1. Remove empty strings from SQL content arrays - they create invalid SQL
2. Fix TABLE() wrapper missing closing parenthesis
3. Ensure all SQL is on correct lines

The root cause of SYNTAX_ERROR issues:
- SQL content arrays have empty strings "" between lines
- When joined, this creates malformed SQL like:
  SELECT * FROM TABLE(get_xxx(params)

  WHERE ...  <- Error: TABLE() not closed
"""

import json
import re
from pathlib import Path
from typing import List

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


def fix_sql_content(sql_lines: List[str]) -> List[str]:
    """
    Fix SQL content array by:
    1. Removing empty strings
    2. Fixing TABLE() wrapper missing closing parenthesis
    """
    # Remove empty lines first
    non_empty = [line for line in sql_lines if line.strip()]

    # Join all lines
    sql = '\n'.join(non_empty)

    # Fix TABLE() wrapper - pattern: FROM TABLE(catalog.schema.get_xxx(params)
    # followed by WHERE/ORDER/etc without closing )

    # Pattern to find: TABLE(...get_xxx(params)) followed by keyword without )
    # Regex: TABLE\(.*?get_\w+\([^)]*\)\s*\n\s*(WHERE|ORDER|GROUP|LIMIT|HAVING)
    # This finds cases where TABLE( is opened but the line ends with ) from get_xxx()
    # and next line starts with a keyword

    # Simpler approach: Fix lines that end with )  but need ))
    fixed_lines = []
    for i, line in enumerate(non_empty):
        stripped = line.strip()

        # Check if this line has TABLE( and ends with single )
        if 'TABLE(' in line.upper() and stripped.endswith(')') and not stripped.endswith('))'):
            # Check if next line starts with a keyword
            if i + 1 < len(non_empty):
                next_stripped = non_empty[i + 1].strip().upper()
                keywords = ['WHERE', 'ORDER', 'GROUP', 'HAVING', 'LIMIT', 'UNION', 'EXCEPT', 'INTERSECT', 'AS']
                if any(next_stripped.startswith(kw) for kw in keywords):
                    # Add missing ) to close TABLE()
                    line = line.rstrip() + ')'

        fixed_lines.append(line)

    return fixed_lines


def process_genie_export(file_path: Path) -> int:
    """Process a genie export file and fix SQL content."""
    data = load_json(file_path)

    benchmarks = data.get('benchmarks', {}).get('questions', [])
    fixed_count = 0

    for i, benchmark in enumerate(benchmarks):
        answers = benchmark.get('answer', [])
        for answer in answers:
            if answer.get('format') == 'SQL':
                content = answer.get('content', [])
                if isinstance(content, list):
                    original = content.copy()
                    fixed = fix_sql_content(content)
                    if fixed != original:
                        fixed_count += 1
                        question = benchmark.get('question', [''])[0][:50]
                        print(f"  Q{i+1}: {question}...")
                    answer['content'] = fixed

    data['benchmarks']['questions'] = benchmarks
    save_json(data, file_path)

    return fixed_count


def main():
    """Fix all genie export files."""
    print("=" * 70)
    print("FIX GENIE SQL CONTENT - V3")
    print("=" * 70)
    print()
    print("Fixes:")
    print("- Remove empty strings from SQL content arrays")
    print("- Fix TABLE() wrapper missing closing parenthesis")
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
        fixed = process_genie_export(file_path)
        total_fixed += fixed
        print(f"  Fixed: {fixed} queries")

    print()
    print("=" * 70)
    print(f"DONE - Fixed {total_fixed} queries")
    print("=" * 70)


if __name__ == "__main__":
    main()
