#!/usr/bin/env python3
"""
Fix All Genie Space JSON Export Files

Converts all files to proper v1 format with benchmarks.questions[].answer[].content structure.

Fixes:
1. cost_intelligence: sql -> answer array (DONE via script)
2. security_auditor: query -> answer array
3. performance: v2 curated_questions -> v1 benchmarks.questions
4. unified_health_monitor: Trim TVFs from 60 to 50
5. job_health_monitor: Fix monitoring table schema references
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

BASE_PATH = Path("/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor")
GENIE_PATH = BASE_PATH / "src" / "genie"


def load_json(file_path: Path) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: dict, file_path: Path):
    """Save data to a JSON file with proper formatting."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {file_path.name}")


def convert_query_to_answer(query_content: Any) -> List[Dict]:
    """Convert query/sql field to proper answer array format."""
    if isinstance(query_content, list):
        sql_lines = query_content
    elif isinstance(query_content, str):
        sql_lines = query_content.split('\n')
    else:
        sql_lines = []

    return [{
        "format": "SQL",
        "content": sql_lines
    }]


def fix_security_auditor():
    """Fix security_auditor: Convert query -> answer format."""
    print("\n=== Fixing security_auditor_genie_export.json ===")

    file_path = GENIE_PATH / "security_auditor_genie_export.json"
    data = load_json(file_path)

    benchmarks = data.get("benchmarks", {}).get("questions", [])
    fixed_count = 0

    for benchmark in benchmarks:
        # Already has proper answer format?
        if "answer" in benchmark:
            answers = benchmark["answer"]
            if answers and any(a.get("format") == "SQL" for a in answers):
                continue

        # Convert query to answer
        if "query" in benchmark:
            benchmark["answer"] = convert_query_to_answer(benchmark["query"])
            del benchmark["query"]
            fixed_count += 1
        elif "sql" in benchmark:
            benchmark["answer"] = convert_query_to_answer(benchmark["sql"])
            del benchmark["sql"]
            fixed_count += 1

    save_json(data, file_path)
    print(f"  Fixed {fixed_count} benchmarks (query -> answer)")


def fix_cost_intelligence():
    """Fix cost_intelligence: Convert sql -> answer format."""
    print("\n=== Fixing cost_intelligence_genie_export.json ===")

    file_path = GENIE_PATH / "cost_intelligence_genie_export.json"
    data = load_json(file_path)

    benchmarks = data.get("benchmarks", {}).get("questions", [])
    fixed_count = 0

    for benchmark in benchmarks:
        # Already has proper answer format?
        if "answer" in benchmark:
            answers = benchmark["answer"]
            if answers and any(a.get("format") == "SQL" for a in answers):
                continue

        # Convert sql to answer
        if "sql" in benchmark:
            benchmark["answer"] = convert_query_to_answer(benchmark["sql"])
            del benchmark["sql"]
            fixed_count += 1
        elif "query" in benchmark:
            benchmark["answer"] = convert_query_to_answer(benchmark["query"])
            del benchmark["query"]
            fixed_count += 1

    save_json(data, file_path)
    print(f"  Fixed {fixed_count} benchmarks (sql -> answer)")


def fix_performance():
    """Fix performance: Convert v2 curated_questions -> v1 benchmarks.questions."""
    print("\n=== Fixing performance_genie_export.json ===")

    file_path = GENIE_PATH / "performance_genie_export.json"
    data = load_json(file_path)

    # Check if it's v2 format
    if "curated_questions" not in data:
        print("  Already v1 format, skipping conversion")
        return

    curated_questions = data.get("curated_questions", [])

    # Convert to v1 format
    v1_benchmarks = []
    for cq in curated_questions:
        question_text = cq.get("question", "")
        query = cq.get("query", "")
        question_id = cq.get("question_id", "")

        # Convert query string to array of lines
        if isinstance(query, str):
            sql_lines = query.split('\n')
        else:
            sql_lines = query

        v1_benchmark = {
            "id": question_id,
            "question": [question_text] if isinstance(question_text, str) else question_text,
            "answer": [{
                "format": "SQL",
                "content": sql_lines
            }]
        }
        v1_benchmarks.append(v1_benchmark)

    # Build v1 structure
    v1_data = {
        "version": 1,
        "config": {
            "name": data.get("genie_space_name", "Health Monitor Performance Space"),
            "description": [data.get("description", "Performance analytics for Databricks")],
            "sample_questions": [{"id": f"sq{i}", "question": [q]} for i, q in enumerate(data.get("sample_questions", []), 1)]
        },
        "data_sources": {
            "tables": [],
            "metric_views": []
        },
        "instructions": {
            "text_instructions": [{
                "id": "perf_instructions_001",
                "content": data.get("instructions", "").split('\n') if isinstance(data.get("instructions", ""), str) else ["Use metric views for aggregations"]
            }],
            "sql_functions": []
        },
        "benchmarks": {
            "questions": v1_benchmarks
        }
    }

    # Convert tables to proper format (extract TVFs and MVs)
    tables = data.get("tables", [])
    for table in tables:
        full_name = table.get("table_full_name", "")
        description = table.get("description", "")

        # Check if it's a TVF (has function signature in description)
        if "Signature:" in description or full_name.startswith("${catalog}.${gold_schema}.get_"):
            # It's a TVF
            v1_data["instructions"]["sql_functions"].append({
                "id": f"tvf_{len(v1_data['instructions']['sql_functions'])+1:03d}",
                "identifier": full_name
            })
        elif "_profile_metrics" in full_name or "_drift_metrics" in full_name:
            # It's a monitoring table - add as table
            v1_data["data_sources"]["tables"].append({
                "identifier": full_name,
                "description": [description] if isinstance(description, str) else description
            })
        elif "mv_" in full_name:
            # It's a metric view
            v1_data["data_sources"]["metric_views"].append({
                "identifier": full_name,
                "description": [description] if isinstance(description, str) else description
            })

    # Remove curated_questions
    del data["curated_questions"]

    save_json(v1_data, file_path)
    print(f"  Converted {len(curated_questions)} curated_questions to benchmarks.questions")
    print(f"  Extracted {len(v1_data['instructions']['sql_functions'])} TVFs")


def fix_unified_health_monitor():
    """Fix unified_health_monitor: Trim TVFs from 60 to 50."""
    print("\n=== Fixing unified_health_monitor_genie_export.json ===")

    file_path = GENIE_PATH / "unified_health_monitor_genie_export.json"
    data = load_json(file_path)

    tvfs = data.get("instructions", {}).get("sql_functions", [])
    original_count = len(tvfs)

    if original_count <= 50:
        print(f"  TVF count ({original_count}) is within limit, no trimming needed")
    else:
        # Trim to 50 - keep the most important ones (first 50)
        data["instructions"]["sql_functions"] = tvfs[:50]
        save_json(data, file_path)
        print(f"  Trimmed TVFs from {original_count} to 50")

    # Also fix any benchmark SQL format issues
    benchmarks = data.get("benchmarks", {}).get("questions", [])
    fixed_count = 0

    for benchmark in benchmarks:
        if "answer" not in benchmark:
            if "sql" in benchmark:
                benchmark["answer"] = convert_query_to_answer(benchmark["sql"])
                del benchmark["sql"]
                fixed_count += 1
            elif "query" in benchmark:
                benchmark["answer"] = convert_query_to_answer(benchmark["query"])
                del benchmark["query"]
                fixed_count += 1

    if fixed_count > 0:
        save_json(data, file_path)
        print(f"  Fixed {fixed_count} benchmarks (sql/query -> answer)")


def fix_job_health_monitor():
    """Fix job_health_monitor: Fix monitoring table schema references."""
    print("\n=== Fixing job_health_monitor_genie_export.json ===")

    file_path = GENIE_PATH / "job_health_monitor_genie_export.json"
    data = load_json(file_path)

    # Fix table references in data_sources
    tables = data.get("data_sources", {}).get("tables", [])
    fixed_tables = 0

    for table in tables:
        identifier = table.get("identifier", "")
        # Check for monitoring tables that should be in _monitoring schema
        if "_profile_metrics" in identifier or "_drift_metrics" in identifier:
            # Should use ${gold_schema}_monitoring for monitoring tables
            if "${gold_schema}." in identifier and "${gold_schema}_monitoring" not in identifier:
                # Fix: change ${gold_schema}.table_name to ${gold_schema}_monitoring.table_name
                old_id = identifier
                # Pattern: ${catalog}.${gold_schema}.fact_..._profile_metrics
                # Should be: ${catalog}.${gold_schema}_monitoring.fact_..._profile_metrics
                identifier = identifier.replace(
                    "${gold_schema}.",
                    "${gold_schema}_monitoring."
                )
                table["identifier"] = identifier
                fixed_tables += 1
                print(f"    Fixed: {old_id} -> {identifier}")

    # Fix SQL in benchmarks
    benchmarks = data.get("benchmarks", {}).get("questions", [])
    fixed_sql = 0

    for benchmark in benchmarks:
        answers = benchmark.get("answer", [])
        for answer in answers:
            if answer.get("format") == "SQL":
                content = answer.get("content", [])
                if isinstance(content, list):
                    new_content = []
                    for line in content:
                        # Fix monitoring table references in SQL
                        if ("_profile_metrics" in line or "_drift_metrics" in line):
                            if "${gold_schema}." in line and "${gold_schema}_monitoring" not in line:
                                old_line = line
                                line = line.replace(
                                    "${gold_schema}.",
                                    "${gold_schema}_monitoring."
                                )
                                if old_line != line:
                                    fixed_sql += 1
                        new_content.append(line)
                    answer["content"] = new_content

    if fixed_tables > 0 or fixed_sql > 0:
        save_json(data, file_path)
        print(f"  Fixed {fixed_tables} table references, {fixed_sql} SQL lines")
    else:
        print("  No monitoring schema fixes needed")


def validate_all_exports():
    """Validate all export files have proper format."""
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    genie_files = [
        "cost_intelligence_genie_export.json",
        "job_health_monitor_genie_export.json",
        "performance_genie_export.json",
        "security_auditor_genie_export.json",
        "unified_health_monitor_genie_export.json",
        "data_quality_monitor_genie_export.json",
    ]

    for genie_file in genie_files:
        file_path = GENIE_PATH / genie_file
        if not file_path.exists():
            print(f"  {genie_file}: NOT FOUND")
            continue

        data = load_json(file_path)

        # Check version
        version = data.get("version")

        # Check benchmarks
        benchmarks = data.get("benchmarks", {}).get("questions", [])
        benchmark_count = len(benchmarks)

        # Check answer format
        proper_format_count = 0
        for b in benchmarks:
            if "answer" in b:
                answers = b["answer"]
                if answers and any(a.get("format") == "SQL" for a in answers):
                    proper_format_count += 1

        # Check TVF count
        tvf_count = len(data.get("instructions", {}).get("sql_functions", []))

        status = "OK" if proper_format_count == benchmark_count and tvf_count <= 50 else "ISSUES"
        print(f"  {genie_file}:")
        print(f"    Version: {version}")
        print(f"    Benchmarks: {proper_format_count}/{benchmark_count} proper format")
        print(f"    TVFs: {tvf_count}/50 max")
        print(f"    Status: {status}")


def main():
    """Fix all genie export files."""
    print("="*60)
    print("FIXING ALL GENIE SPACE JSON EXPORTS")
    print("="*60)

    # Fix each file
    fix_cost_intelligence()
    fix_security_auditor()
    fix_performance()
    fix_unified_health_monitor()
    fix_job_health_monitor()

    # Validate
    validate_all_exports()

    print("\n" + "="*60)
    print("DONE - All files fixed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Deploy bundle: databricks bundle deploy -p health_monitor")
    print("2. Run validation job to test SQL against Databricks")
    print("3. Deploy genie spaces")


if __name__ == "__main__":
    main()
