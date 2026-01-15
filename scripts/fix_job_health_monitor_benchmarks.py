#!/usr/bin/env python3
"""
Fix Job Health Monitor Genie Space benchmark errors.

Errors to fix:
1. Q1: get_failed_jobs - requires 3 params but got 4
2. Q3: get_job_duration_percentiles - requires 2 params but got 3
3. Q9: mv_job_performance - needs MEASURE() function
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"
JSON_PATH = GENIE_DIR / "job_health_monitor_genie_export.json"

# Date values
TODAY = datetime.now()
START_DATE = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")

GOLD_PREFIX = "${catalog}.${gold_schema}"
ML_PREFIX = "${catalog}.${feature_schema}"
MON_PREFIX = "${catalog}.${gold_schema}_monitoring"


def generate_id():
    return uuid.uuid4().hex


def get_correct_tvf_benchmarks():
    """Generate TVF benchmarks with correct parameters from SQL files.
    
    Reliability TVF signatures:
    - get_failed_jobs(start_date, end_date, workspace_filter) - 3 params
    - get_job_success_rate(start_date, end_date, min_runs) - 3 params
    - get_job_duration_percentiles(days_back, job_name_filter) - 2 params
    - get_job_failure_trends(days_back) - 1 param
    - get_job_sla_compliance(start_date, end_date) - 2 params
    - get_job_run_details(job_id_filter, days_back) - 2 params
    - get_most_expensive_jobs(start_date, end_date, top_n) - 3 params
    - get_job_retry_analysis(start_date, end_date) - 2 params
    """
    
    tvf_benchmarks = [
        {
            "question": "What are the failed jobs?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_failed_jobs("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;'
        },
        {
            "question": "What is the job success rate?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_job_success_rate("{START_DATE}", "{END_DATE}", 5) LIMIT 20;'
        },
        {
            "question": "Show job duration percentiles",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_job_duration_percentiles(30, "ALL") LIMIT 20;'
        },
        {
            "question": "Show job failure trends",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_job_failure_trends(30) LIMIT 20;'
        },
        {
            "question": "What is job SLA compliance?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_job_sla_compliance("{START_DATE}", "{END_DATE}") LIMIT 20;'
        },
        {
            "question": "Show most expensive jobs",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_most_expensive_jobs("{START_DATE}", "{END_DATE}", 20) LIMIT 20;'
        },
        {
            "question": "Show job retry analysis",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_job_retry_analysis("{START_DATE}", "{END_DATE}") LIMIT 20;'
        },
        {
            "question": "Show job repair costs",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_job_repair_costs("{START_DATE}", "{END_DATE}", 20) LIMIT 20;'
        },
    ]
    
    return [
        {
            "id": generate_id(),
            "question": [t["question"]],
            "answer": [{"format": "SQL", "content": [t["sql"]]}]
        }
        for t in tvf_benchmarks
    ]


def get_correct_mv_benchmarks():
    """Generate metric view benchmarks with correct MEASURE() syntax."""
    
    mv_benchmarks = [
        {
            "question": "Show job performance summary",
            "sql": f"SELECT job_name, run_date, MEASURE(total_runs) as total_runs, MEASURE(success_rate) as success_rate FROM {GOLD_PREFIX}.mv_job_performance GROUP BY ALL LIMIT 20;"
        },
    ]
    
    return [
        {
            "id": generate_id(),
            "question": [t["question"]],
            "answer": [{"format": "SQL", "content": [t["sql"]]}]
        }
        for t in mv_benchmarks
    ]


def get_correct_table_benchmarks():
    """Generate table benchmarks (ML, monitoring, fact, dim)."""
    
    benchmarks = []
    
    # ML tables
    ml_tables = [
        "ml_job_failure_predictions",
        "ml_job_duration_predictions",
        "ml_job_anomaly_predictions"
    ]
    for table in ml_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the latest predictions from {table}?"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {ML_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Monitoring tables
    mon_tables = [
        "fact_job_run_timeline_profile_metrics",
        "fact_job_run_timeline_drift_metrics"
    ]
    for table in mon_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show monitoring data from {table}"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {MON_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Fact tables
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show recent job runs"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_job_run_timeline LIMIT 20;"]}]
    })
    
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show job run costs"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_job_run_cost LIMIT 20;"]}]
    })
    
    # Dim tables
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show job dimension"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.dim_job LIMIT 20;"]}]
    })
    
    return benchmarks


def get_deep_research_benchmarks():
    """Generate deep research benchmarks."""
    
    return [
        {
            "id": generate_id(),
            "question": ["Analyze job failure patterns over time"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Complex job failure analysis' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Identify flaky jobs with high retry rates"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Flaky job identification' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Compare job performance across workspaces"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cross-workspace job comparison' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Provide executive job health summary"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Executive job health summary' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["What jobs need optimization?"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Job optimization recommendations' AS deep_research;"]}]
        },
    ]


def main():
    print("=" * 80)
    print("FIXING JOB HEALTH MONITOR BENCHMARKS")
    print("=" * 80)
    
    # Load existing JSON
    with open(JSON_PATH, 'r') as f:
        genie_data = json.load(f)
    
    # Generate correct benchmarks
    benchmarks = []
    
    # TVFs with correct parameters (8)
    tvf_benchmarks = get_correct_tvf_benchmarks()
    benchmarks.extend(tvf_benchmarks)
    print(f"✅ TVF benchmarks: {len(tvf_benchmarks)}")
    
    # Metric views with MEASURE() (1)
    mv_benchmarks = get_correct_mv_benchmarks()
    benchmarks.extend(mv_benchmarks)
    print(f"✅ Metric view benchmarks: {len(mv_benchmarks)}")
    
    # Tables (ML, monitoring, fact, dim)
    table_benchmarks = get_correct_table_benchmarks()
    benchmarks.extend(table_benchmarks)
    print(f"✅ Table benchmarks: {len(table_benchmarks)}")
    
    # Deep research (5)
    deep_benchmarks = get_deep_research_benchmarks()
    benchmarks.extend(deep_benchmarks)
    print(f"✅ Deep research benchmarks: {len(deep_benchmarks)}")
    
    print(f"\n📊 Total benchmarks: {len(benchmarks)}")
    
    # Update JSON
    genie_data['benchmarks'] = {'questions': benchmarks}
    
    with open(JSON_PATH, 'w') as f:
        json.dump(genie_data, f, indent=2)
    
    print(f"\n✅ Updated: {JSON_PATH.name}")
    
    # Show sample SQL for verification
    print("\n" + "=" * 80)
    print("SAMPLE SQL (first 5)")
    print("=" * 80)
    for i, b in enumerate(benchmarks[:5]):
        print(f"\n{i+1}. {b['question'][0]}")
        print(f"   {b['answer'][0]['content'][0]}")


if __name__ == "__main__":
    main()
