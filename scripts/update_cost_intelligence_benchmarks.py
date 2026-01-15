#!/usr/bin/env python3
"""
Update Cost Intelligence Genie Space benchmarks with comprehensive coverage.

Target: 20 Basic + 5 Deep Research = 25 Total Questions
Coverage: TVFs, Metric Views, Monitoring Tables, ML Tables, Fact Tables, Dim Tables
"""

import json
import uuid
from pathlib import Path

def generate_id() -> str:
    return uuid.uuid4().hex

# Catalog and schema templates
CATALOG = "${catalog}"
GOLD = "${gold_schema}"
ML = "${feature_schema}"
MON = "${gold_schema}_monitoring"

# =============================================================================
# 20 BASIC BENCHMARK QUESTIONS
# =============================================================================

BASIC_BENCHMARKS = [
    # --- TVFs (8 questions) ---
    {
        "category": "TVF",
        "question": "What are the top cost contributors this month?",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_top_cost_contributors(30) LIMIT 20;"
    },
    {
        "category": "TVF",
        "question": "Show cost breakdown by owner",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_cost_by_owner(30) LIMIT 20;"
    },
    {
        "category": "TVF",
        "question": "What is the week over week cost trend?",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_cost_week_over_week(4) LIMIT 20;"
    },
    {
        "category": "TVF",
        "question": "Show cost trend by SKU",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_cost_trend_by_sku(30) LIMIT 20;"
    },
    {
        "category": "TVF",
        "question": "Are there any cost anomalies?",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_cost_anomalies(30) LIMIT 20;"
    },
    {
        "category": "TVF",
        "question": "What is the tag coverage?",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_tag_coverage() LIMIT 20;"
    },
    {
        "category": "TVF",
        "question": "Show the most expensive jobs",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_most_expensive_jobs(30) LIMIT 20;"
    },
    {
        "category": "TVF",
        "question": "Show cluster right-sizing recommendations",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.get_cluster_right_sizing_recommendations(30) LIMIT 20;"
    },
    
    # --- Metric Views (4 questions) ---
    {
        "category": "MetricView",
        "question": "What is our total spend this month?",
        "sql": f"SELECT SUM(total_cost) as total_cost FROM {CATALOG}.{GOLD}.mv_cost_analytics WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());"
    },
    {
        "category": "MetricView",
        "question": "Show daily cost trend for last 7 days",
        "sql": f"SELECT usage_date, SUM(total_cost) as daily_cost FROM {CATALOG}.{GOLD}.mv_cost_analytics WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS GROUP BY usage_date ORDER BY usage_date;"
    },
    {
        "category": "MetricView",
        "question": "What is cost by workspace?",
        "sql": f"SELECT workspace_id, SUM(total_cost) as cost FROM {CATALOG}.{GOLD}.mv_cost_analytics WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS GROUP BY workspace_id ORDER BY cost DESC LIMIT 10;"
    },
    {
        "category": "MetricView",
        "question": "Show commit tracking status",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.mv_commit_tracking LIMIT 20;"
    },
    
    # --- ML Prediction Tables (3 questions) ---
    {
        "category": "ML",
        "question": "Show cost anomaly predictions",
        "sql": f"SELECT * FROM {CATALOG}.{ML}.cost_anomaly_predictions LIMIT 20;"
    },
    {
        "category": "ML",
        "question": "What are the budget forecasts?",
        "sql": f"SELECT * FROM {CATALOG}.{ML}.budget_forecast_predictions LIMIT 20;"
    },
    {
        "category": "ML",
        "question": "Show commitment recommendations",
        "sql": f"SELECT * FROM {CATALOG}.{ML}.commitment_recommendations LIMIT 20;"
    },
    
    # --- Monitoring Tables (2 questions) ---
    {
        "category": "Monitoring",
        "question": "Show cost profile metrics",
        "sql": f"SELECT * FROM {CATALOG}.{MON}.fact_usage_profile_metrics LIMIT 20;"
    },
    {
        "category": "Monitoring",
        "question": "Show cost drift metrics",
        "sql": f"SELECT * FROM {CATALOG}.{MON}.fact_usage_drift_metrics LIMIT 20;"
    },
    
    # --- Fact Tables (2 questions) ---
    {
        "category": "Fact",
        "question": "Show recent usage data",
        "sql": f"SELECT usage_date, sku_name, usage_quantity FROM {CATALOG}.{GOLD}.fact_usage WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS ORDER BY usage_date DESC LIMIT 20;"
    },
    {
        "category": "Fact",
        "question": "Show list prices",
        "sql": f"SELECT * FROM {CATALOG}.{GOLD}.fact_list_prices LIMIT 20;"
    },
    
    # --- Dimension Tables (1 question) ---
    {
        "category": "Dimension",
        "question": "List all SKUs",
        "sql": f"SELECT sku_id, sku_name FROM {CATALOG}.{GOLD}.dim_sku ORDER BY sku_name LIMIT 20;"
    },
]

# =============================================================================
# 5 DEEP RESEARCH QUESTIONS (More comprehensive but still executable)
# =============================================================================

DEEP_RESEARCH_BENCHMARKS = [
    {
        "category": "DeepResearch",
        "question": "🔬 DEEP: Which workspaces have highest cost with cost anomalies?",
        "sql": f"""SELECT 
  u.workspace_id,
  SUM(u.usage_quantity) as total_usage,
  COUNT(DISTINCT a.usage_date) as anomaly_days
FROM {CATALOG}.{GOLD}.fact_usage u
LEFT JOIN {CATALOG}.{ML}.cost_anomaly_predictions a 
  ON u.workspace_id = a.workspace_id
WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY u.workspace_id
ORDER BY total_usage DESC
LIMIT 10;"""
    },
    {
        "category": "DeepResearch",
        "question": "🔬 DEEP: Cost by SKU category with serverless breakdown",
        "sql": f"""SELECT 
  s.sku_name,
  SUM(u.usage_quantity) as total_usage,
  COUNT(DISTINCT u.usage_date) as active_days
FROM {CATALOG}.{GOLD}.fact_usage u
JOIN {CATALOG}.{GOLD}.dim_sku s ON u.sku_name = s.sku_name
WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY s.sku_name
ORDER BY total_usage DESC
LIMIT 15;"""
    },
    {
        "category": "DeepResearch",
        "question": "🔬 DEEP: Job cost analysis with run frequency",
        "sql": f"""SELECT 
  j.job_id,
  j.job_name,
  COUNT(*) as run_count,
  SUM(jr.run_duration_seconds) as total_duration_seconds
FROM {CATALOG}.{GOLD}.fact_job_run_timeline jr
JOIN {CATALOG}.{GOLD}.dim_job j ON jr.job_id = j.job_id
WHERE jr.period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY j.job_id, j.job_name
ORDER BY run_count DESC
LIMIT 20;"""
    },
    {
        "category": "DeepResearch",
        "question": "🔬 DEEP: Workspace cost trend with node usage correlation",
        "sql": f"""SELECT 
  w.workspace_id,
  w.workspace_name,
  COUNT(DISTINCT n.cluster_id) as clusters_used
FROM {CATALOG}.{GOLD}.dim_workspace w
LEFT JOIN {CATALOG}.{GOLD}.fact_node_timeline n 
  ON w.workspace_id = n.workspace_id
WHERE n.start_time >= CURRENT_DATE() - INTERVAL 30 DAYS OR n.start_time IS NULL
GROUP BY w.workspace_id, w.workspace_name
ORDER BY clusters_used DESC
LIMIT 15;"""
    },
    {
        "category": "DeepResearch",
        "question": "🔬 DEEP: ML tag recommendations with cost impact",
        "sql": f"""SELECT 
  t.workspace_id,
  COUNT(*) as recommendation_count
FROM {CATALOG}.{ML}.tag_recommendations t
GROUP BY t.workspace_id
ORDER BY recommendation_count DESC
LIMIT 20;"""
    },
]


def create_benchmark(question: str, sql: str) -> dict:
    """Create a benchmark in the correct API format."""
    return {
        "id": generate_id(),
        "question": [question],
        "answer": [
            {
                "format": "SQL",
                "content": [sql]
            }
        ]
    }


def main():
    json_path = Path("src/genie/cost_intelligence_genie_export.json")
    
    print("=" * 80)
    print("UPDATING COST INTELLIGENCE BENCHMARKS")
    print("=" * 80)
    
    # Load existing JSON
    with open(json_path) as f:
        genie_data = json.load(f)
    
    # Generate benchmarks
    benchmarks = []
    
    print("\n📋 Basic Questions (20):")
    for i, b in enumerate(BASIC_BENCHMARKS, 1):
        benchmark = create_benchmark(b["question"], b["sql"])
        benchmarks.append(benchmark)
        print(f"  {i}. [{b['category']}] {b['question'][:50]}...")
    
    print(f"\n🔬 Deep Research Questions (5):")
    for i, b in enumerate(DEEP_RESEARCH_BENCHMARKS, 1):
        benchmark = create_benchmark(b["question"], b["sql"])
        benchmarks.append(benchmark)
        print(f"  {20+i}. [{b['category']}] {b['question'][:50]}...")
    
    # Update benchmarks section
    genie_data["benchmarks"] = {"questions": benchmarks}
    
    # Write back
    with open(json_path, 'w') as f:
        json.dump(genie_data, f, indent=2)
    
    print(f"\n✅ Updated {json_path}")
    print(f"   Total benchmarks: {len(benchmarks)}")
    
    # Print category summary
    categories = {}
    for b in BASIC_BENCHMARKS + DEEP_RESEARCH_BENCHMARKS:
        cat = b["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📊 Category Distribution:")
    for cat, count in categories.items():
        print(f"   {cat}: {count}")


if __name__ == "__main__":
    main()
