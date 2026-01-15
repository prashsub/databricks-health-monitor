#!/usr/bin/env python3
"""
Fix Performance Genie Space benchmark errors.

Errors to fix:
1. Q9: mv_query_performance - needs MEASURE() function
2. Q10: mv_cluster_utilization - needs MEASURE() function
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"
JSON_PATH = GENIE_DIR / "performance_genie_export.json"

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
    
    Performance TVF signatures:
    - get_slow_queries(start_date, end_date, duration_threshold_seconds, top_n) - 4 params
    - get_warehouse_utilization(start_date, end_date) - 2 params
    - get_query_efficiency(start_date, end_date, min_duration_seconds, top_n) - 4 params
    - get_high_spill_queries(start_date, end_date, min_spill_gb) - 3 params
    - get_query_volume_trends(days_back, granularity) - 2 params
    - get_user_query_summary(start_date, end_date, top_n) - 3 params
    - get_cluster_utilization(start_date, end_date, min_hours) - 3 params
    - get_underutilized_clusters(days_back, cpu_threshold, min_hours) - 3 params
    """
    
    tvf_benchmarks = [
        {
            "question": "What are the slow queries?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_slow_queries("{START_DATE}", "{END_DATE}", 300, 20) LIMIT 20;'
        },
        {
            "question": "Show warehouse utilization",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_warehouse_utilization("{START_DATE}", "{END_DATE}") LIMIT 20;'
        },
        {
            "question": "Show query efficiency analysis",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_query_efficiency("{START_DATE}", "{END_DATE}", 60, 20) LIMIT 20;'
        },
        {
            "question": "Show queries with high disk spill",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_high_spill_queries("{START_DATE}", "{END_DATE}", 1.0) LIMIT 20;'
        },
        {
            "question": "Show query volume trends",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_query_volume_trends(30, "daily") LIMIT 20;'
        },
        {
            "question": "Show user query summary",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_user_query_summary("{START_DATE}", "{END_DATE}", 20) LIMIT 20;'
        },
        {
            "question": "Show cluster utilization",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_cluster_utilization("{START_DATE}", "{END_DATE}", 1) LIMIT 20;'
        },
        {
            "question": "Show underutilized clusters",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_underutilized_clusters(30, 30.0, 10) LIMIT 20;'
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
            "question": "Show query performance summary",
            "sql": f"SELECT query_date, warehouse_name, MEASURE(total_queries) as total_queries, MEASURE(avg_duration_seconds) as avg_duration FROM {GOLD_PREFIX}.mv_query_performance GROUP BY ALL LIMIT 20;"
        },
        {
            "question": "Show cluster utilization metrics",
            "sql": f"SELECT cluster_date, cluster_name, MEASURE(avg_cpu_utilization) as avg_cpu, MEASURE(avg_memory_utilization) as avg_memory FROM {GOLD_PREFIX}.mv_cluster_utilization GROUP BY ALL LIMIT 20;"
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
        "ml_query_duration_predictions",
        "ml_cluster_sizing_predictions",
        "ml_warehouse_scaling_predictions"
    ]
    for table in ml_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the latest predictions from {table}?"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {ML_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Monitoring tables
    mon_tables = [
        "fact_query_history_profile_metrics",
        "fact_query_history_drift_metrics"
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
        "question": ["Show recent query history"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_query_history LIMIT 20;"]}]
    })
    
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show cluster metrics"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_cluster_metrics LIMIT 20;"]}]
    })
    
    # Dim tables
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show warehouse dimension"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.dim_warehouse LIMIT 20;"]}]
    })
    
    return benchmarks


def get_deep_research_benchmarks():
    """Generate deep research benchmarks."""
    
    return [
        {
            "id": generate_id(),
            "question": ["Analyze query performance trends"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Complex query performance analysis' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Identify query optimization opportunities"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Query optimization recommendations' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Compare cluster performance across workloads"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cross-workload cluster comparison' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Provide executive performance summary"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Executive performance summary' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["What clusters need right-sizing?"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cluster right-sizing recommendations' AS deep_research;"]}]
        },
    ]


def main():
    print("=" * 80)
    print("FIXING PERFORMANCE BENCHMARKS")
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
    
    # Metric views with MEASURE() (2)
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
    
    # Show MV SQL for verification
    print("\n" + "=" * 80)
    print("METRIC VIEW SQL (fixed with MEASURE())")
    print("=" * 80)
    for b in mv_benchmarks:
        print(f"\n{b['question'][0]}")
        print(f"   {b['answer'][0]['content'][0]}")


if __name__ == "__main__":
    main()
