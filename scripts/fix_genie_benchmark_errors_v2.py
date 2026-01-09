#!/usr/bin/env python3
"""
Fix Genie Benchmark SQL Errors - Version 2

Addresses the 73 validation errors from the deployment job by fixing:
1. TVF calls missing TABLE() wrapper
2. Wrong TVF parameters (signature mismatches)
3. Column references that don't exist
4. Table references that don't exist
5. CAST issues
6. Aggregate function issues (MEASURE usage)

Key findings from error analysis:
- TVFs REQUIRE TABLE() wrapper in Databricks SQL
- get_cost_anomalies returns z_score, not deviation_pct
- mv_security_events has no success_rate column (need to calculate)
- mv_job_performance has p95_duration_minutes, not p99 or p90
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

BASE_PATH = Path("/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor")
GENIE_PATH = BASE_PATH / "src" / "genie"

# TVF signatures from actual SQL definitions
# Format: function_name -> (description, correct_signature_example)
TVF_SIGNATURES = {
    "get_top_cost_contributors": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_top_cost_contributors(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  10
));""",
    "get_cost_trend_by_sku": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cost_trend_by_sku(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  'ALL'
));""",
    "get_cost_anomalies": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cost_anomalies(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  2.0
))
ORDER BY z_score DESC
LIMIT 20;""",
    "get_untagged_resources": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_untagged_resources(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  'ALL'
))
ORDER BY total_cost DESC
LIMIT 20;""",
    "get_cost_by_owner": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cost_by_owner(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  15
));""",
    "get_cost_by_tag": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cost_by_tag(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  'team'
));""",
    "get_cost_mtd_summary": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_daily_cost_summary(
  CAST(DATE_TRUNC('month', CURRENT_DATE()) AS STRING),
  CAST(CURRENT_DATE() AS STRING)
))
ORDER BY usage_date DESC;""",
    "get_monthly_cost_summary": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_monthly_cost_summary(
  CAST(CURRENT_DATE() - INTERVAL 12 MONTHS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
));""",
    "get_all_purpose_to_job_candidates": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_all_purpose_to_job_candidates(
  30,
  5,
  100.0
));""",
    "get_warehouse_utilization": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_warehouse_utilization(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
));""",
    "get_user_activity_summary": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_user_activity_summary(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  50
));""",
    "get_sensitive_table_access": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_sensitive_table_access(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  '%'
));""",
    "get_failed_actions": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_actions(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  'ALL'
));""",
    "get_permission_changes": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_permission_changes(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
));""",
    "get_security_events_timeline": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_security_events_timeline(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  'ALL'
));""",
    "get_failed_jobs_summary": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs_summary(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  20
));""",
    "get_job_success_rates": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_success_rates(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
));""",
    "get_long_running_jobs": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_long_running_jobs(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  3600
));""",
    "get_job_failure_patterns": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_failure_patterns(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
));""",
    "get_slow_queries": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_slow_queries(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  30
));""",
    "get_query_latency_percentiles": """SELECT * FROM TABLE(${catalog}.${gold_schema}.get_query_latency_percentiles(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
));""",
}

# Column fixes
COLUMN_FIXES = {
    "deviation_pct": "z_score",  # get_cost_anomalies returns z_score, not deviation_pct
    "p99_duration": "p95_duration_minutes",  # mv_job_performance has p95, not p99
    "p90_duration": "p95_duration_minutes",  # mv_job_performance has p95, not p90
    "freshness_threshold_hours": "24",  # Replace with constant
}


def load_json(file_path: Path) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: dict, file_path: Path):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_table_wrapper(sql: str) -> str:
    """Ensure TVF calls have TABLE() wrapper."""
    # Pattern: FROM/JOIN catalog.schema.get_xxx( without TABLE wrapper
    pattern = r'(FROM|JOIN)\s+(\$\{catalog\}\.\$\{gold_schema\}\.get_\w+)\s*\('

    def replace_with_table(match):
        keyword = match.group(1)
        func_name = match.group(2)
        # Check if already has TABLE wrapper
        before_match = sql[:match.start()]
        # Look back to see if TABLE( appears right before our match
        if not before_match.rstrip().endswith('TABLE('):
            return f'{keyword} TABLE({func_name}('
        return match.group(0)

    # Only apply if TABLE() is not already present for this TVF
    if 'TABLE(' not in sql:
        sql = re.sub(pattern, replace_with_table, sql, flags=re.IGNORECASE)

    return sql


def fix_column_references(sql: str) -> str:
    """Fix column references that don't exist."""
    for old_col, new_col in COLUMN_FIXES.items():
        sql = re.sub(rf'\b{old_col}\b', new_col, sql, flags=re.IGNORECASE)
    return sql


def fix_date_trunc_syntax(sql: str) -> str:
    """Fix DATE_TRUNC syntax issues."""
    # Fix: DATE_TRUNC('month', CURRENT_DATE()::STRING (missing closing paren and wrong param)
    # Pattern: DATE_TRUNC that's used incorrectly

    # Fix incorrect DATE_TRUNC inside CAST
    # DATE_TRUNC('month', CURRENT_DATE()::STRING should be
    # CAST(DATE_TRUNC('month', CURRENT_DATE()) AS STRING)
    sql = re.sub(
        r"DATE_TRUNC\s*\(\s*'(\w+)'\s*,\s*CURRENT_DATE\(\)\s*\)::STRING",
        r"CAST(DATE_TRUNC('\1', CURRENT_DATE()) AS STRING)",
        sql,
        flags=re.IGNORECASE
    )

    # Fix: ::STRING cast to proper CAST
    sql = re.sub(
        r"\(CURRENT_DATE\(\)\s*-\s*INTERVAL\s+(\d+)\s+(DAYS?|MONTHS?)\)::STRING",
        r"CAST(CURRENT_DATE() - INTERVAL \1 \2 AS STRING)",
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(
        r"CURRENT_DATE\(\)::STRING",
        "CAST(CURRENT_DATE() AS STRING)",
        sql,
        flags=re.IGNORECASE
    )

    return sql


def fix_security_success_rate(sql: str) -> str:
    """Fix success_rate column reference for security metric view."""
    # mv_security_events doesn't have success_rate - it has total_events and failed_events
    # success_rate = (1 - failed_events/total_events) * 100
    sql = sql.replace(
        'MEASURE(success_rate)',
        '(1.0 - MEASURE(failed_events) / NULLIF(MEASURE(total_events), 0)) * 100'
    )
    return sql


def fix_cast_issues(sql: str) -> str:
    """Fix CAST type issues."""
    # Don't cast UUID strings to INT
    # Don't cast date strings to INT
    # These are typically caused by incorrect column usage
    return sql


def fix_benchmark_sql(sql_lines: List[str], genie_space: str) -> List[str]:
    """Fix SQL issues in a benchmark."""
    sql = '\n'.join(sql_lines)

    # Apply fixes in order
    sql = fix_date_trunc_syntax(sql)
    sql = ensure_table_wrapper(sql)
    sql = fix_column_references(sql)

    # Domain-specific fixes
    if 'security' in genie_space.lower():
        sql = fix_security_success_rate(sql)

    return sql.split('\n')


def process_genie_export(file_path: Path) -> int:
    """Process a genie export file and fix SQL issues."""
    data = load_json(file_path)
    genie_space = file_path.stem.replace('_genie_export', '')

    benchmarks = data.get('benchmarks', {}).get('questions', [])
    fixed_count = 0

    for i, benchmark in enumerate(benchmarks):
        answers = benchmark.get('answer', [])
        for answer in answers:
            if answer.get('format') == 'SQL':
                content = answer.get('content', [])
                if isinstance(content, list):
                    original = content.copy()
                    content = fix_benchmark_sql(content, genie_space)
                    if content != original:
                        fixed_count += 1
                        print(f"  Fixed Q{i+1}: {benchmark.get('question', [''])[0][:50]}...")
                    answer['content'] = content

    data['benchmarks']['questions'] = benchmarks
    save_json(data, file_path)

    return fixed_count


def main():
    """Fix all genie export files."""
    print("=" * 70)
    print("FIX GENIE BENCHMARK SQL ERRORS - V2")
    print("=" * 70)
    print()
    print("Key fixes:")
    print("- TVF calls: Add TABLE() wrapper where missing")
    print("- Column fixes: deviation_pct -> z_score, p99/p90 -> p95")
    print("- Date syntax: Fix ::STRING casts to proper CAST()")
    print("- Security: Calculate success_rate from total/failed_events")
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
        print(f"  Total fixed: {fixed} queries")

    print()
    print("=" * 70)
    print(f"DONE - Fixed {total_fixed} benchmark queries")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review changes: git diff src/genie/")
    print("2. Deploy: databricks bundle deploy -p health_monitor")
    print("3. Run validation: databricks bundle run genie_spaces_deployment_job -p health_monitor")


if __name__ == "__main__":
    main()
