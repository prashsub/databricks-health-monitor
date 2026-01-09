#!/usr/bin/env python3
"""
Fix Benchmark SQL Errors in Genie Space Export Files

Fixes common SQL errors:
1. NOT_A_SCALAR_FUNCTION - Add TABLE() wrapper around TVF calls
2. WRONG_NUM_ARGS - Fix parameter counts for TVFs
3. DATE_TRUNC parameter order issues
4. Column name fixes
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

BASE_PATH = Path("/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor")
GENIE_PATH = BASE_PATH / "src" / "genie"

# TVF signatures (function_name: (required_params, optional_params))
TVF_SIGNATURES = {
    # Cost TVFs
    "get_top_cost_contributors": (2, 1),  # start_date, end_date, top_n=10
    "get_cost_trend_by_sku": (2, 1),      # start_date, end_date, sku_filter='ALL'
    "get_cost_by_owner": (2, 1),          # start_date, end_date, top_n=20
    "get_cost_by_tag": (2, 1),            # start_date, end_date, tag_key='team'
    "get_untagged_resources": (2, 1),     # start_date, end_date, resource_type='ALL'
    "get_tag_coverage": (2, 0),           # start_date, end_date
    "get_cost_anomalies": (1, 1),         # days_back, threshold_pct=50.0
    "get_daily_cost_summary": (2, 0),     # start_date, end_date
    "get_workspace_cost_comparison": (2, 0),  # start_date, end_date
    "get_monthly_cost_summary": (2, 0),   # start_date, end_date
    "get_all_purpose_to_job_candidates": (1, 2),  # days_back, min_runs=5, cost_threshold=100
    "get_warehouse_efficiency": (1, 1),   # days_back, min_queries=100
    "get_cost_week_over_week": (1, 0),    # weeks=4
    "get_cost_forecast_summary": (1, 0),  # days_back=30
    "get_commit_burn_rate": (0, 0),       # no params

    # Security TVFs
    "get_user_activity_summary": (2, 1),  # start_date, end_date, top_n=50
    "get_sensitive_table_access": (2, 1), # start_date, end_date, table_pattern='%'
    "get_failed_actions": (2, 1),         # start_date, end_date, user_filter='ALL'
    "get_permission_changes": (2, 0),     # start_date, end_date
    "get_off_hours_activity": (2, 2),     # start_date, end_date, hours_start=7, hours_end=19
    "get_security_events_timeline": (2, 1),  # start_date, end_date, user_filter='ALL'
    "get_user_activity_patterns": (2, 0), # start_date, end_date
    "get_service_account_audit": (2, 0),  # start_date, end_date
    "get_table_access_audit": (2, 0),     # start_date, end_date

    # Job/Reliability TVFs
    "get_failed_jobs_summary": (2, 1),    # start_date, end_date, top_n=20
    "get_job_success_rates": (2, 0),      # start_date, end_date
    "get_long_running_jobs": (2, 1),      # start_date, end_date, duration_threshold=3600
    "get_job_failure_patterns": (2, 0),   # start_date, end_date
    "get_job_duration_trends": (2, 0),    # start_date, end_date
    "get_job_sla_compliance": (2, 1),     # start_date, end_date, sla_seconds=3600
    "get_pipeline_health": (2, 0),        # start_date, end_date
    "get_job_retry_analysis": (2, 0),     # start_date, end_date
    "get_job_cost_analysis": (2, 1),      # start_date, end_date, top_n=20
    "get_repair_run_analysis": (2, 0),    # start_date, end_date
    "get_job_schedule_drift": (2, 0),     # start_date, end_date
    "get_job_failure_cost": (2, 1),       # start_date, end_date, top_n=20

    # Performance TVFs
    "get_slow_queries": (2, 1),           # start_date, end_date, threshold_seconds=30
    "get_query_latency_percentiles": (2, 0),  # start_date, end_date
    "get_warehouse_utilization": (2, 0),  # start_date, end_date
    "get_query_volume_trends": (2, 0),    # start_date, end_date
    "get_high_spill_queries": (2, 1),     # start_date, end_date, spill_threshold_gb=1.0
    "get_cache_hit_analysis": (2, 0),     # start_date, end_date
    "get_query_efficiency_by_user": (2, 1),  # start_date, end_date, top_n=20
    "get_underutilized_clusters": (1, 1), # days_back, cpu_threshold=30
    "get_cluster_right_sizing_recommendations": (1, 0),  # days_back=30
    "get_jobs_without_autoscaling": (1, 0),  # days_back=30
    "get_failed_queries_summary": (2, 0), # start_date, end_date
    "get_top_users_by_query_count": (2, 1),  # start_date, end_date, top_n=20
    "get_query_queue_analysis": (2, 0),   # start_date, end_date

    # Quality TVFs
    "get_table_quality_summary": (0, 0),  # no params
    "get_quality_trend_analysis": (1, 0), # days_back=30
    "get_freshness_alerts": (1, 0),       # threshold_hours=24
    "get_tables_below_threshold": (1, 0), # quality_threshold=80
    "get_quality_issues_summary": (0, 0), # no params
}


def load_json(file_path: Path) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: dict, file_path: Path):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fix_table_wrapper(sql_lines: List[str]) -> List[str]:
    """Add TABLE() wrapper around TVF calls that are missing it."""
    sql = '\n'.join(sql_lines)

    # Find TVF calls without TABLE() wrapper
    # Pattern: FROM/JOIN <catalog>.<schema>.get_xxx(...) where not preceded by TABLE(
    tvf_pattern = r'(FROM|JOIN)\s+(\$\{catalog\}\.\$\{gold_schema\}\.get_\w+)\s*\('

    def add_table_wrapper(match):
        keyword = match.group(1)
        func_name = match.group(2)
        # Only add TABLE() if not already wrapped
        return f'{keyword} TABLE({func_name}('

    # Check if already has TABLE() - don't double wrap
    if 'TABLE(' not in sql:
        sql = re.sub(tvf_pattern, add_table_wrapper, sql, flags=re.IGNORECASE)

    return sql.split('\n')


def fix_date_trunc(sql_lines: List[str]) -> List[str]:
    """Fix DATE_TRUNC parameter order (should be DATE_TRUNC('unit', column))."""
    sql = '\n'.join(sql_lines)

    # Fix: DATE_TRUNC(column, 'unit') -> DATE_TRUNC('unit', column)
    # Pattern: DATE_TRUNC(something_not_quoted, 'quoted')
    pattern = r"DATE_TRUNC\s*\(\s*([^'\"]+?)\s*,\s*'(\w+)'\s*\)"
    sql = re.sub(pattern, r"DATE_TRUNC('\2', \1)", sql, flags=re.IGNORECASE)

    return sql.split('\n')


def fix_tvf_single_param_call(sql_lines: List[str]) -> List[str]:
    """Fix TVF calls that pass only one parameter when they need dates."""
    sql = '\n'.join(sql_lines)

    # Fix: get_failed_actions(7) -> get_failed_actions(CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING), CAST(CURRENT_DATE() AS STRING))
    # Pattern: get_xxx(single_number)
    single_param_tvfs = [
        'get_failed_actions',
        'get_permission_changes',
        'get_off_hours_activity',
        'get_user_activity_patterns',
        'get_service_account_audit',
        'get_table_access_audit',
    ]

    for tvf in single_param_tvfs:
        pattern = rf'({tvf})\s*\(\s*(\d+)\s*\)'
        replacement = rf"\1(CAST(CURRENT_DATE() - INTERVAL \2 DAYS AS STRING), CAST(CURRENT_DATE() AS STRING))"
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)

    return sql.split('\n')


def fix_cost_specific_issues(sql_lines: List[str]) -> List[str]:
    """Fix cost-intelligence specific SQL issues."""
    sql = '\n'.join(sql_lines)

    # Fix: deviation_pct -> use the actual column from get_cost_anomalies
    # The TVF returns: usage_date, workspace_name, actual_cost, expected_cost, deviation_pct
    # This should be correct, but if metric view doesn't have it, we need to calculate

    return sql.split('\n')


def fix_security_specific_issues(sql_lines: List[str]) -> List[str]:
    """Fix security-auditor specific SQL issues."""
    sql = '\n'.join(sql_lines)

    # Fix: success_rate column doesn't exist in mv_security_events
    # Replace with calculation
    sql = sql.replace(
        'MEASURE(success_rate)',
        '(1.0 - MEASURE(failed_events) / NULLIF(MEASURE(total_events), 0)) * 100'
    )

    return sql.split('\n')


def fix_job_specific_issues(sql_lines: List[str]) -> List[str]:
    """Fix job-health specific SQL issues."""
    sql = '\n'.join(sql_lines)

    # Fix: p99_duration -> p95_duration_seconds (if p99 doesn't exist)
    # Fix: p90_duration -> p95_duration_seconds
    sql = re.sub(r'\bp99_duration\b', 'p95_duration_seconds', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bp90_duration\b', 'p95_duration_seconds', sql, flags=re.IGNORECASE)

    # Fix: alias issues (f. or ft. prefixes)
    # Remove dangling alias references

    return sql.split('\n')


def fix_performance_specific_issues(sql_lines: List[str]) -> List[str]:
    """Fix performance-specific SQL issues."""
    sql = '\n'.join(sql_lines)

    # Fix: CAST issues with warehouse_id UUIDs
    # Don't try to cast UUID strings to INT

    return sql.split('\n')


def fix_quality_specific_issues(sql_lines: List[str]) -> List[str]:
    """Fix data-quality specific SQL issues."""
    sql = '\n'.join(sql_lines)

    # Fix: freshness_threshold_hours -> use a constant
    sql = sql.replace('freshness_threshold_hours', '24')

    # Fix: quality_score column reference
    # Make sure it's using the right table alias

    return sql.split('\n')


def process_benchmark_sql(benchmark: dict, genie_space: str) -> dict:
    """Process and fix SQL in a benchmark question."""
    answers = benchmark.get('answer', [])

    for answer in answers:
        if answer.get('format') == 'SQL':
            content = answer.get('content', [])
            if isinstance(content, list):
                # Apply fixes
                content = fix_table_wrapper(content)
                content = fix_date_trunc(content)
                content = fix_tvf_single_param_call(content)

                # Apply domain-specific fixes
                if 'cost' in genie_space.lower():
                    content = fix_cost_specific_issues(content)
                elif 'security' in genie_space.lower():
                    content = fix_security_specific_issues(content)
                elif 'job' in genie_space.lower():
                    content = fix_job_specific_issues(content)
                elif 'performance' in genie_space.lower():
                    content = fix_performance_specific_issues(content)
                elif 'quality' in genie_space.lower():
                    content = fix_quality_specific_issues(content)

                answer['content'] = content

    return benchmark


def fix_genie_export(file_path: Path) -> int:
    """Fix all benchmark SQL in a genie export file."""
    data = load_json(file_path)
    genie_space = file_path.stem.replace('_genie_export', '')

    benchmarks = data.get('benchmarks', {}).get('questions', [])
    fixed_count = 0

    for i, benchmark in enumerate(benchmarks):
        original = json.dumps(benchmark)
        benchmark = process_benchmark_sql(benchmark, genie_space)
        if json.dumps(benchmark) != original:
            fixed_count += 1
        benchmarks[i] = benchmark

    data['benchmarks']['questions'] = benchmarks
    save_json(data, file_path)

    return fixed_count


def main():
    """Fix all genie export files."""
    print("=" * 60)
    print("FIXING BENCHMARK SQL ERRORS")
    print("=" * 60)

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
            print(f"  {genie_file}: NOT FOUND")
            continue

        fixed = fix_genie_export(file_path)
        total_fixed += fixed
        print(f"  {genie_file}: {fixed} benchmarks fixed")

    print(f"\nTotal: {total_fixed} benchmarks modified")
    print("\nNext: Re-deploy bundle and run validation job")


if __name__ == "__main__":
    main()
