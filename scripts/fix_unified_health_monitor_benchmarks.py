#!/usr/bin/env python3
"""
Fix Unified Health Monitor Genie Space benchmark errors.

Errors to fix:
1. Q2: get_cost_trend_by_sku - requires 3 params but got 4
2. Q9: mv_cost_analytics - needs MEASURE()
3. Q10: mv_job_performance - needs MEASURE()
4. Q11: mv_query_performance - needs MEASURE()
5. Q12: mv_security_events - needs MEASURE()
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"
JSON_PATH = GENIE_DIR / "unified_health_monitor_genie_export.json"

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
    """Generate TVF benchmarks with correct parameters.
    
    Unified Health Monitor covers all domains. Key TVF signatures:
    - get_top_cost_contributors(start_date, end_date, top_n) - 3 params
    - get_cost_trend_by_sku(start_date, end_date, sku_filter) - 3 params
    - get_failed_jobs(start_date, end_date, workspace_filter) - 3 params
    - get_slow_queries(start_date, end_date, duration_threshold, top_n) - 4 params
    - get_security_events_timeline(start_date, end_date, user_filter) - 3 params
    - get_stale_tables(days_back, freshness_threshold_hours) - 2 params
    - get_underutilized_clusters(days_back, cpu_threshold, min_hours) - 3 params
    - get_warehouse_utilization(start_date, end_date) - 2 params
    """
    
    tvf_benchmarks = [
        {
            "question": "Show top cost contributors",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_top_cost_contributors("{START_DATE}", "{END_DATE}", 20) LIMIT 20;'
        },
        {
            "question": "Show cost trend by SKU",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_cost_trend_by_sku("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;'
        },
        {
            "question": "What are the failed jobs?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_failed_jobs("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;'
        },
        {
            "question": "Show slow queries",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_slow_queries("{START_DATE}", "{END_DATE}", 300, 20) LIMIT 20;'
        },
        {
            "question": "Show security events timeline",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_security_events_timeline("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;'
        },
        {
            "question": "Show stale tables",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_stale_tables(90, 24) LIMIT 20;'
        },
        {
            "question": "Show underutilized clusters",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_underutilized_clusters(30, 30.0, 10) LIMIT 20;'
        },
        {
            "question": "Show warehouse utilization",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_warehouse_utilization("{START_DATE}", "{END_DATE}") LIMIT 20;'
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
    """Generate metric view benchmarks with correct MEASURE() syntax.
    
    Unified Health Monitor has metric views from all domains.
    """
    
    mv_benchmarks = [
        {
            "question": "Show cost analytics summary",
            "sql": f"SELECT usage_date, workspace_name, MEASURE(total_cost) as total_cost, MEASURE(total_dbu) as total_dbu FROM {GOLD_PREFIX}.mv_cost_analytics GROUP BY ALL LIMIT 20;"
        },
        {
            "question": "Show job performance summary",
            "sql": f"SELECT run_date, job_name, MEASURE(total_runs) as total_runs, MEASURE(success_rate) as success_rate FROM {GOLD_PREFIX}.mv_job_performance GROUP BY ALL LIMIT 20;"
        },
        {
            "question": "Show query performance summary",
            "sql": f"SELECT query_date, warehouse_name, MEASURE(total_queries) as total_queries, MEASURE(avg_duration_seconds) as avg_duration FROM {GOLD_PREFIX}.mv_query_performance GROUP BY ALL LIMIT 20;"
        },
        {
            "question": "Show security events summary",
            "sql": f"SELECT event_date, service_name, MEASURE(total_events) as total_events, MEASURE(failed_events) as failed_events FROM {GOLD_PREFIX}.mv_security_events GROUP BY ALL LIMIT 20;"
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
    
    # ML tables (from various domains)
    ml_tables = [
        "ml_cost_anomaly_predictions",
        "ml_job_failure_predictions",
        "ml_query_duration_predictions",
        "ml_security_risk_predictions"
    ]
    for table in ml_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the latest predictions from {table}?"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {ML_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Fact tables (one from each domain)
    fact_tables = [
        ("fact_usage", "Show billing usage data"),
        ("fact_job_run_timeline", "Show job execution data"),
        ("fact_query_history", "Show query history"),
        ("fact_audit_logs", "Show audit logs")
    ]
    for table, question in fact_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [question],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    return benchmarks


def get_deep_research_benchmarks():
    """Generate deep research benchmarks."""
    
    return [
        {
            "id": generate_id(),
            "question": ["Provide executive health summary across all domains"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Executive health summary' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Correlate cost with job performance"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cost-performance correlation' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Identify cross-domain optimization opportunities"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cross-domain optimization' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["What are the overall platform health trends?"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Platform health trends' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Provide monthly platform health report"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Monthly platform health report' AS deep_research;"]}]
        },
    ]


def main():
    print("=" * 80)
    print("FIXING UNIFIED HEALTH MONITOR BENCHMARKS")
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
    
    # Metric views with MEASURE() (4)
    mv_benchmarks = get_correct_mv_benchmarks()
    benchmarks.extend(mv_benchmarks)
    print(f"✅ Metric view benchmarks: {len(mv_benchmarks)}")
    
    # Tables (ML, fact)
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
    
    # Show corrected SQL for verification
    print("\n" + "=" * 80)
    print("CORRECTED SQL")
    print("=" * 80)
    print(f"\nget_cost_trend_by_sku (3 params - was 4):")
    print(f'   SELECT * FROM {GOLD_PREFIX}.get_cost_trend_by_sku("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;')
    print(f"\nmv_cost_analytics with MEASURE():")
    print(f"   SELECT usage_date, workspace_name, MEASURE(total_cost) as total_cost FROM mv_cost_analytics GROUP BY ALL LIMIT 20;")


if __name__ == "__main__":
    main()
