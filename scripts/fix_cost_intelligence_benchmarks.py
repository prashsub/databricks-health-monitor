#!/usr/bin/env python3
"""
Fix Cost Intelligence Genie Space benchmark errors.

Errors to fix:
1. Q2: get_cost_trend_by_sku - has 4 params, should have 3
2. Q9-10: Metric views need MEASURE() function, can't use SELECT *
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"
JSON_PATH = GENIE_DIR / "cost_intelligence_genie_export.json"

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
    """Generate TVF benchmarks with correct parameters from SQL files."""
    
    # Correct TVF calls based on actual SQL definitions
    tvf_benchmarks = [
        {
            "question": "Who are the top cost contributors?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_top_cost_contributors("{START_DATE}", "{END_DATE}", 10) LIMIT 20;'
        },
        {
            "question": "Show cost trend by SKU",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_cost_trend_by_sku("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;'
        },
        {
            "question": "Show cost by owner for chargeback",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_cost_by_owner("{START_DATE}", "{END_DATE}", 20) LIMIT 20;'
        },
        {
            "question": "What is spend by custom tags?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_spend_by_custom_tags("{START_DATE}", "{END_DATE}", "team") LIMIT 20;'
        },
        {
            "question": "What is our tag coverage?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_tag_coverage("{START_DATE}", "{END_DATE}") LIMIT 20;'
        },
        {
            "question": "Show cost week over week",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_cost_week_over_week(4) LIMIT 20;'
        },
        {
            "question": "Show cost anomalies",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_cost_anomalies("{START_DATE}", "{END_DATE}", 2.0) LIMIT 20;'
        },
        {
            "question": "What is the cost forecast?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_cost_forecast_summary(3) LIMIT 20;'
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
    
    # For metric views, we need to use MEASURE() for measure columns
    # Or query just the dimension columns
    # Best approach: Use a simple aggregation query
    mv_benchmarks = [
        {
            "question": "Show cost analytics summary",
            "sql": f"SELECT usage_date, workspace_name, sku_name, MEASURE(total_cost) as total_cost, MEASURE(total_dbu) as total_dbu FROM {GOLD_PREFIX}.mv_cost_analytics GROUP BY ALL LIMIT 20;"
        },
        {
            "question": "Show commit tracking status",
            "sql": f"SELECT usage_date, MEASURE(total_cost) as total_cost, MEASURE(mtd_cost) as mtd_cost FROM {GOLD_PREFIX}.mv_commit_tracking GROUP BY ALL LIMIT 20;"
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
        "ml_cost_anomaly_predictions",
        "ml_budget_forecast_predictions", 
        "ml_usage_trend_predictions"
    ]
    for table in ml_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the latest predictions from {table}?"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {ML_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Monitoring tables
    mon_tables = [
        "fact_usage_profile_metrics",
        "fact_usage_drift_metrics"
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
        "question": ["Show recent usage data"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_usage LIMIT 20;"]}]
    })
    
    # Dim tables
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show workspace dimension"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.dim_workspace LIMIT 20;"]}]
    })
    
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show SKU dimension"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.dim_sku LIMIT 20;"]}]
    })
    
    return benchmarks


def get_deep_research_benchmarks():
    """Generate deep research benchmarks."""
    
    return [
        {
            "id": generate_id(),
            "question": ["Analyze cost trends over time"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Complex cost trend analysis' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Identify cost anomalies and root causes"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Anomaly root cause analysis' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Compare cost across workspaces and teams"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cross-workspace comparison' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Provide executive cost summary"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Executive cost summary' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["What are the key cost optimization opportunities?"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cost optimization recommendations' AS deep_research;"]}]
        },
    ]


def main():
    print("=" * 80)
    print("FIXING COST INTELLIGENCE BENCHMARKS")
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
    
    # Show sample SQL for verification
    print("\n" + "=" * 80)
    print("SAMPLE SQL (first 5)")
    print("=" * 80)
    for i, b in enumerate(benchmarks[:5]):
        print(f"\n{i+1}. {b['question'][0]}")
        print(f"   {b['answer'][0]['content'][0]}")


if __name__ == "__main__":
    main()
