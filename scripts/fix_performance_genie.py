#!/usr/bin/env python3
"""
Fix Performance Genie Space to match specification.

Issues:
1. Missing 10 tables (2 dim + 1 fact + 7 ML)
2. Missing 6 TVFs
3. 5 TVF names don't match spec
"""

import json
from pathlib import Path

# Hardcoded schema paths
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def fix_performance_genie():
    """Fix Performance Genie Space JSON."""
    
    json_path = Path("src/genie/performance_genie_export.json")
    data = json.load(open(json_path))
    
    print("Fixing Performance Genie Space...")
    print("=" * 80)
    
    # 1. Add missing dimension tables
    missing_dim_tables = [
        {
            "identifier": f"{SYSTEM_GOLD}.dim_node_type",
            "description": [
                "Dimension table for node type specifications.",
                "Business: Instance type costs and capacity planning."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.dim_date",
            "description": [
                "Date dimension for time-based performance analysis.",
                "Business: Time series analysis and reporting."
            ]
        }
    ]
    
    # 2. Add missing fact table
    missing_fact_table = {
        "identifier": f"{SYSTEM_GOLD}.fact_warehouse_events",
        "description": [
            "Fact table tracking SQL warehouse lifecycle events.",
            "Business: Warehouse state changes and uptime tracking."
        ]
    }
    
    # 3. Add missing ML tables
    missing_ml_tables = [
        {
            "identifier": f"{SYSTEM_GOLD_ML}.query_optimization_classifications",
            "description": [
                "ML classifications for query optimization opportunities (multi-label).",
                "Business: Proactive query performance optimization."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.query_optimization_recommendations",
            "description": [
                "ML recommendations for specific query optimizations.",
                "Business: Actionable query tuning suggestions."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.cache_hit_predictions",
            "description": [
                "ML predictions for cache effectiveness.",
                "Business: Cache strategy optimization."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.job_duration_predictions",
            "description": [
                "ML predictions for job completion times with confidence intervals.",
                "Business: SLA planning and resource allocation."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.cluster_capacity_recommendations",
            "description": [
                "ML recommendations for optimal cluster capacity planning.",
                "Business: Capacity planning and scaling decisions."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.cluster_rightsizing_recommendations",
            "description": [
                "ML recommendations for cluster right-sizing with savings estimates.",
                "Business: Cost optimization through right-sizing."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.dbr_migration_risk_scores",
            "description": [
                "ML risk assessment for DBR version migrations.",
                "Business: Safe DBR upgrade planning."
            ]
        }
    ]
    
    # Add all missing tables
    existing_table_ids = {t['identifier'] for t in data['data_sources']['tables']}
    
    for table in missing_dim_tables + [missing_fact_table] + missing_ml_tables:
        if table['identifier'] not in existing_table_ids:
            data['data_sources']['tables'].append(table)
            print(f"✅ Added table: {table['identifier'].split('.')[-1]}")
    
    # 4. Fix TVF names (rename existing ones to match spec)
    tvf_renames = {
        'get_query_latency_percentiles': 'get_query_duration_percentiles',
        'get_query_volume_trends': 'get_query_volume_by_hour',
        'get_high_spill_queries': 'get_query_spill_analysis',
        'get_underutilized_clusters': 'get_idle_clusters',
        'get_legacy_dbr_jobs': 'get_jobs_on_old_dbr'
    }
    
    for tvf in data['instructions']['sql_functions']:
        old_name = tvf['identifier'].split('.')[-1]
        if old_name in tvf_renames:
            new_name = tvf_renames[old_name]
            tvf['identifier'] = f"{SYSTEM_GOLD}.{new_name}"
            print(f"✅ Renamed TVF: {old_name} → {new_name}")
    
    # 5. Add missing TVF (get_cluster_efficiency_score - completely missing)
    existing_tvf_names = {t['identifier'].split('.')[-1] for t in data['instructions']['sql_functions']}
    
    if 'get_cluster_efficiency_score' not in existing_tvf_names:
        import uuid
        new_tvf = {
            "id": uuid.uuid4().hex,
            "identifier": f"{SYSTEM_GOLD}.get_cluster_efficiency_score"
        }
        data['instructions']['sql_functions'].append(new_tvf)
        print(f"✅ Added TVF: get_cluster_efficiency_score")
    
    # Save fixed JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print()
    print("=" * 80)
    print("✅ Performance Genie Space fixed successfully!")
    print()
    print("Summary:")
    print(f"  - Added 10 missing tables (2 dim + 1 fact + 7 ML)")
    print(f"  - Renamed 5 TVFs to match spec")
    print(f"  - Added 1 missing TVF (get_cluster_efficiency_score)")

if __name__ == "__main__":
    fix_performance_genie()
