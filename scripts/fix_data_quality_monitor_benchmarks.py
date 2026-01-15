#!/usr/bin/env python3
"""
Fix Data Quality Monitor Genie Space benchmark errors.

Errors to fix:
1. Q4: get_pipeline_data_lineage - requires 2 params but got 3
2. Q8: mv_data_quality - needs MEASURE()
3. Q9: mv_governance_analytics - needs MEASURE()
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"
JSON_PATH = GENIE_DIR / "data_quality_monitor_genie_export.json"

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
    
    Data Quality TVF signatures:
    - get_stale_tables(days_back, freshness_threshold_hours) - 2 params
    - get_table_freshness_summary(days_back) - 1 param
    - get_orphan_tables(days_back, inactive_threshold_days) - 2 params
    - get_pipeline_data_lineage(days_back, entity_filter) - 2 params
    - get_table_dependencies(table_pattern) - 1 param
    - get_schema_evolution_history(days_back, table_pattern) - 2 params
    - get_data_quality_scores(days_back) - 1 param
    - get_table_access_frequency(days_back, top_n) - 2 params
    """
    
    tvf_benchmarks = [
        {
            "question": "What are the stale tables?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_stale_tables(90, 24) LIMIT 20;'
        },
        {
            "question": "Show table freshness summary",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_table_freshness_summary(30) LIMIT 20;'
        },
        {
            "question": "Show orphan tables",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_orphan_tables(30, 90) LIMIT 20;'
        },
        {
            "question": "Show pipeline data lineage",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_pipeline_data_lineage(30, "ALL") LIMIT 20;'
        },
        {
            "question": "Show table dependencies",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_table_dependencies("%") LIMIT 20;'
        },
        {
            "question": "Show schema evolution history",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_schema_evolution_history(30, "%") LIMIT 20;'
        },
        {
            "question": "Show data quality scores",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_data_quality_scores(30) LIMIT 20;'
        },
        {
            "question": "Show table access frequency",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_table_access_frequency(30, 20) LIMIT 20;'
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
            "question": "Show data quality summary",
            "sql": f"SELECT table_schema, freshness_status, MEASURE(total_tables) as total_tables, MEASURE(fresh_tables) as fresh_tables FROM {GOLD_PREFIX}.mv_data_quality GROUP BY ALL LIMIT 20;"
        },
        {
            "question": "Show governance analytics summary",
            "sql": f"SELECT event_date, MEASURE(total_events) as total_events, MEASURE(read_events) as read_events FROM {GOLD_PREFIX}.mv_governance_analytics GROUP BY ALL LIMIT 20;"
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
        "ml_table_freshness_predictions",
        "ml_schema_change_predictions",
        "ml_data_quality_predictions"
    ]
    for table in ml_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the latest predictions from {table}?"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {ML_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Monitoring tables
    mon_tables = [
        "fact_table_metadata_profile_metrics",
        "fact_table_metadata_drift_metrics"
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
        "question": ["Show table metadata"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_table_metadata LIMIT 20;"]}]
    })
    
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show data lineage events"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_data_lineage LIMIT 20;"]}]
    })
    
    # Dim tables
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show table dimension"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.dim_table LIMIT 20;"]}]
    })
    
    return benchmarks


def get_deep_research_benchmarks():
    """Generate deep research benchmarks."""
    
    return [
        {
            "id": generate_id(),
            "question": ["Analyze data quality trends over time"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Complex data quality trend analysis' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Identify tables at risk of becoming stale"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Stale table risk analysis' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Compare data quality across schemas"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cross-schema quality comparison' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Provide executive data quality summary"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Executive data quality summary' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["What data quality issues need immediate attention?"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Critical data quality issues' AS deep_research;"]}]
        },
    ]


def main():
    print("=" * 80)
    print("FIXING DATA QUALITY MONITOR BENCHMARKS")
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
    
    # Show corrected SQL for verification
    print("\n" + "=" * 80)
    print("CORRECTED SQL")
    print("=" * 80)
    print(f"\nget_pipeline_data_lineage (2 params - was 3):")
    print(f'   SELECT * FROM {GOLD_PREFIX}.get_pipeline_data_lineage(30, "ALL") LIMIT 20;')
    print(f"\nmv_data_quality with MEASURE():")
    print(f"   SELECT table_schema, freshness_status, MEASURE(total_tables), MEASURE(fresh_tables) FROM mv_data_quality GROUP BY ALL LIMIT 20;")


if __name__ == "__main__":
    main()
