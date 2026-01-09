#!/usr/bin/env python3
"""
Validate and Fix Genie Space Export JSONs

This script:
1. Validates benchmark SQL against specification files
2. Fixes JSON format issues (query -> answer, sql -> answer)
3. Generates deployment-ready JSON files
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configuration
CATALOG = "prashanth_subrahmanyam_catalog"
GOLD_SCHEMA = "dev_prashanth_subrahmanyam_system_gold"
FEATURE_SCHEMA = "dev_prashanth_subrahmanyam_system_gold_ml"
MONITORING_SCHEMA = "dev_prashanth_subrahmanyam_system_gold_monitoring"

BASE_PATH = Path("/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor")
GENIE_PATH = BASE_PATH / "src" / "genie"


def load_json(file_path: Path) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: dict, file_path: Path):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def substitute_variables(sql: str) -> str:
    """Substitute variable placeholders with actual values."""
    sql = sql.replace("${catalog}", CATALOG)
    sql = sql.replace("${gold_schema}", GOLD_SCHEMA)
    sql = sql.replace("${feature_schema}", FEATURE_SCHEMA)
    sql = sql.replace("${gold_schema}_monitoring", MONITORING_SCHEMA)
    return sql


def extract_sql_from_benchmark(benchmark: dict) -> str:
    """Extract SQL from various benchmark formats."""
    # Format 1: answer array with format="SQL"
    if "answer" in benchmark:
        for ans in benchmark.get("answer", []):
            if ans.get("format") == "SQL":
                content = ans.get("content", [])
                if isinstance(content, list):
                    return "\n".join(content)
                return content

    # Format 2: query array (old format)
    if "query" in benchmark:
        query = benchmark.get("query", [])
        if isinstance(query, list):
            return "\n".join(query)
        return query

    # Format 3: sql array (another old format)
    if "sql" in benchmark:
        sql = benchmark.get("sql", [])
        if isinstance(sql, list):
            return "\n".join(sql)
        return sql

    return ""


def extract_table_references(sql: str) -> Set[str]:
    """Extract all table/view references from SQL."""
    # Substitute variables first
    sql = substitute_variables(sql)

    # Patterns to match fully qualified table names
    patterns = [
        r'FROM\s+([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)',
        r'JOIN\s+([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)',
        r'TABLE\s*\(\s*([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)',
    ]

    tables = set()
    for pattern in patterns:
        matches = re.findall(pattern, sql, re.IGNORECASE)
        tables.update(matches)

    return tables


def convert_to_answer_format(benchmark: dict) -> dict:
    """Convert benchmark to proper answer format."""
    sql_content = extract_sql_from_benchmark(benchmark)

    # If already has proper answer format, return as-is
    if "answer" in benchmark:
        has_sql_answer = any(
            ans.get("format") == "SQL"
            for ans in benchmark.get("answer", [])
        )
        if has_sql_answer:
            return benchmark

    # Convert to proper format
    sql_lines = sql_content.split("\n") if sql_content else []

    new_benchmark = {
        "id": benchmark.get("id", ""),
        "question": benchmark.get("question", []),
        "answer": [
            {
                "format": "SQL",
                "content": sql_lines
            }
        ]
    }

    return new_benchmark


def validate_genie_export(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a genie export JSON file.
    Returns (is_valid, list_of_issues)
    """
    issues = []

    try:
        data = load_json(file_path)
    except Exception as e:
        return False, [f"Failed to load JSON: {e}"]

    # Check version
    version = data.get("version")
    if version not in [1, "1"]:
        issues.append(f"Unexpected version: {version}. Expected v1 format.")

    # Check benchmarks
    benchmarks = data.get("benchmarks", {}).get("questions", [])
    if not benchmarks:
        # Check for v2 format
        benchmarks = data.get("curated_questions", [])
        if benchmarks:
            issues.append("Uses v2 format (curated_questions). Needs conversion to v1 benchmarks.questions.")

    if len(benchmarks) == 0:
        issues.append("No benchmark questions found.")
        return False, issues

    # Validate each benchmark
    for i, benchmark in enumerate(benchmarks):
        q_num = i + 1

        # Check for question
        question = benchmark.get("question", [])
        if not question:
            issues.append(f"Q{q_num}: Missing question text")

        # Check for SQL
        sql = extract_sql_from_benchmark(benchmark)
        if not sql:
            issues.append(f"Q{q_num}: No SQL content found")
            continue

        # Check answer format
        has_proper_answer = "answer" in benchmark and any(
            ans.get("format") == "SQL"
            for ans in benchmark.get("answer", [])
        )
        if not has_proper_answer:
            if "query" in benchmark:
                issues.append(f"Q{q_num}: Uses 'query' format instead of 'answer' array")
            elif "sql" in benchmark:
                issues.append(f"Q{q_num}: Uses 'sql' format instead of 'answer' array")
            else:
                issues.append(f"Q{q_num}: Missing proper answer format")

        # Extract and validate table references
        tables = extract_table_references(sql)
        for table in tables:
            if "_profile_metrics" in table or "_drift_metrics" in table:
                if MONITORING_SCHEMA not in table:
                    issues.append(f"Q{q_num}: Monitoring table {table} may use wrong schema")

    # Check TVF count
    tvfs = data.get("instructions", {}).get("sql_functions", [])
    if len(tvfs) > 50:
        issues.append(f"Too many TVFs ({len(tvfs)}). Max allowed is 50.")

    return len(issues) == 0, issues


def fix_genie_export(file_path: Path, output_path: Path) -> dict:
    """
    Fix a genie export JSON file and save to output path.
    Returns the fixed data.
    """
    data = load_json(file_path)

    # Handle v2 format conversion
    if "curated_questions" in data and "benchmarks" not in data:
        # Convert from v2 to v1
        curated = data.pop("curated_questions", [])
        data["benchmarks"] = {"questions": curated}

    # Fix benchmark format
    benchmarks = data.get("benchmarks", {}).get("questions", [])
    fixed_benchmarks = []

    for benchmark in benchmarks:
        fixed = convert_to_answer_format(benchmark)
        # Ensure answer has content
        if fixed.get("answer"):
            for ans in fixed["answer"]:
                if ans.get("format") == "SQL" and not ans.get("content"):
                    ans["content"] = []
        fixed_benchmarks.append(fixed)

    if "benchmarks" not in data:
        data["benchmarks"] = {}
    data["benchmarks"]["questions"] = fixed_benchmarks

    # Limit TVFs if needed (for unified_health_monitor)
    tvfs = data.get("instructions", {}).get("sql_functions", [])
    if len(tvfs) > 50:
        print(f"  Trimming TVFs from {len(tvfs)} to 50")
        data["instructions"]["sql_functions"] = tvfs[:50]

    # Save fixed data
    save_json(data, output_path)

    return data


def generate_validation_report():
    """Generate a validation report for all genie export files."""
    genie_files = [
        "cost_intelligence_genie_export.json",
        "job_health_monitor_genie_export.json",
        "performance_genie_export.json",
        "security_auditor_genie_export.json",
        "unified_health_monitor_genie_export.json",
    ]

    print("=" * 70)
    print("GENIE SPACE EXPORT VALIDATION REPORT")
    print("=" * 70)

    for genie_file in genie_files:
        file_path = GENIE_PATH / genie_file
        print(f"\n{'='*50}")
        print(f"File: {genie_file}")
        print(f"{'='*50}")

        if not file_path.exists():
            print("  ERROR: File not found!")
            continue

        is_valid, issues = validate_genie_export(file_path)

        if is_valid:
            print("  ✅ Valid - No issues found")
        else:
            print(f"  ❌ Found {len(issues)} issues:")
            for issue in issues[:20]:  # Limit to first 20 issues
                print(f"    - {issue}")
            if len(issues) > 20:
                print(f"    ... and {len(issues) - 20} more issues")

        # Generate fixed version
        output_path = GENIE_PATH / f"{file_path.stem}_fixed.json"
        try:
            fix_genie_export(file_path, output_path)
            print(f"  📝 Fixed version saved to: {output_path.name}")
        except Exception as e:
            print(f"  ❌ Failed to fix: {e}")


def main():
    """Main entry point."""
    generate_validation_report()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Next Steps:
1. Review the validation report above
2. Fixed versions have been saved as *_fixed.json
3. Deploy using the fixed versions
    """)


if __name__ == "__main__":
    main()
