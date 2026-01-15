#!/usr/bin/env python3
"""
Fix Cost Intelligence Genie Space to match specification.

Issues:
1. Missing ALL tables (dim, fact, ML, monitoring)
"""

import json
import uuid
from pathlib import Path

# Hardcoded schema paths
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def fix_cost_intelligence():
    """Fix Cost Intelligence Genie Space JSON."""
    
    json_path = Path("src/genie/cost_intelligence_genie_export.json")
    data = json.load(open(json_path))
    
    print("=" * 80)
    print("FIXING COST INTELLIGENCE GENIE SPACE")
    print("=" * 80)
    print()
    
    # Create tables section if missing
    if 'tables' not in data['data_sources']:
        data['data_sources']['tables'] = []
    
    # Add dimension tables
    dim_tables = [
        'dim_workspace',
        'dim_sku',
        'dim_cluster',
        'dim_node_type',
        'dim_job'
    ]
    
    print("1. Adding dimension tables...")
    for table_name in dim_tables:
        data['data_sources']['tables'].append({
            'identifier': f'{SYSTEM_GOLD}.{table_name}'
        })
        print(f"   ✅ Added {table_name}")
    
    # Add fact tables
    fact_tables = [
        'fact_usage',
        'fact_account_prices',
        'fact_list_prices',
        'fact_node_timeline',
        'fact_job_run_timeline'
    ]
    
    print("\n2. Adding fact tables...")
    for table_name in fact_tables:
        data['data_sources']['tables'].append({
            'identifier': f'{SYSTEM_GOLD}.{table_name}'
        })
        print(f"   ✅ Added {table_name}")
    
    # Add ML tables
    ml_tables = [
        'cost_anomaly_predictions',
        'budget_forecast_predictions',
        'job_cost_optimizer_predictions',
        'chargeback_predictions',
        'commitment_recommendations',
        'tag_recommendations'
    ]
    
    print("\n3. Adding ML tables...")
    for table_name in ml_tables:
        data['data_sources']['tables'].append({
            'identifier': f'{SYSTEM_GOLD_ML}.{table_name}'
        })
        print(f"   ✅ Added {table_name}")
    
    # Add monitoring tables
    monitoring_tables = [
        'fact_usage_profile_metrics',
        'fact_usage_drift_metrics'
    ]
    
    print("\n4. Adding monitoring tables...")
    for table_name in monitoring_tables:
        data['data_sources']['tables'].append({
            'identifier': f'{SYSTEM_GOLD_MONITORING}.{table_name}'
        })
        print(f"   ✅ Added {table_name}")
    
    # Save
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ COST INTELLIGENCE FIX COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  - Added 5 dim tables")
    print(f"  - Added 5 fact tables")
    print(f"  - Added 6 ML tables")
    print(f"  - Added 2 monitoring tables")
    print(f"  - Total: 18 tables")

if __name__ == "__main__":
    fix_cost_intelligence()
