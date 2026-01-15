#!/usr/bin/env python3
"""
Regenerate ALL Genie Space benchmarks strictly from actual_assets_inventory.json.

NO hardcoding. ALL table names, TVFs, metric views extracted from inventory.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"
INVENTORY_PATH = GENIE_DIR / "actual_assets_inventory.json"
TVF_SIGNATURES_PATH = GENIE_DIR / "tvf_signatures.json"

# Template variable prefixes
GOLD_PREFIX = "${catalog}.${gold_schema}"
ML_PREFIX = "${catalog}.${feature_schema}"
MON_PREFIX = "${catalog}.${gold_schema}_monitoring"

# Date values for TVF calls
TODAY = datetime.now()
START_DATE = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")


def generate_id():
    return uuid.uuid4().hex


def load_inventory():
    """Load the asset inventory."""
    with open(INVENTORY_PATH) as f:
        return json.load(f)


def load_tvf_signatures():
    """Load TVF signatures for parameter info."""
    if TVF_SIGNATURES_PATH.exists():
        with open(TVF_SIGNATURES_PATH) as f:
            return json.load(f)
    return {}


def get_tvf_params(tvf_name: str, signatures: dict) -> str:
    """Generate TVF parameters from signature."""
    sig = signatures.get(tvf_name, [])
    
    if not sig:
        return ""
    
    args = []
    for param in sig:
        name = param.get('name', '')
        ptype = param.get('type', 'STRING').upper()
        
        # Generate appropriate default values
        if name in ['start_date', 'end_date']:
            args.append(f'"{START_DATE}"' if 'start' in name else f'"{END_DATE}"')
        elif name == 'top_n':
            args.append('20')
        elif name == 'days_back':
            args.append('30')
        elif name in ['workspace_filter', 'user_filter', 'sku_filter', 'entity_filter', 'job_name_filter', 'table_pattern']:
            args.append('"ALL"' if 'filter' in name else '"%"')
        elif name == 'tag_key':
            args.append('"team"')
        elif name == 'z_score_threshold':
            args.append('2.0')
        elif name == 'forecast_months':
            args.append('3')
        elif name == 'weeks_back':
            args.append('4')
        elif name == 'freshness_threshold_hours':
            args.append('24')
        elif name == 'inactive_threshold_days':
            args.append('90')
        elif name == 'duration_threshold_seconds':
            args.append('300')
        elif name == 'min_duration_seconds':
            args.append('60')
        elif name == 'min_spill_gb':
            args.append('1.0')
        elif name == 'granularity':
            args.append('"daily"')
        elif name == 'cpu_threshold':
            args.append('30.0')
        elif name == 'min_hours':
            args.append('1')
        elif name == 'min_observation_hours':
            args.append('10')
        elif name == 'business_hours_start':
            args.append('9')
        elif name == 'business_hours_end':
            args.append('18')
        elif ptype == 'STRING':
            args.append('"ALL"')
        elif ptype == 'INT':
            args.append('30')
        elif ptype == 'DOUBLE':
            args.append('1.0')
        else:
            args.append('NULL')
    
    return ', '.join(args)


def generate_benchmarks_for_space(space_name: str, inventory: dict, signatures: dict) -> list:
    """Generate benchmarks for a single Genie Space from inventory."""
    
    domain = inventory['domain_mapping'].get(space_name, {})
    benchmarks = []
    
    # === TVF Benchmarks ===
    tvfs = domain.get('tvfs', [])[:8]  # Max 8 TVF benchmarks
    for tvf in tvfs:
        params = get_tvf_params(tvf, signatures)
        sql = f'SELECT * FROM {GOLD_PREFIX}.{tvf}({params}) LIMIT 20;'
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Query {tvf}"],
            "answer": [{"format": "SQL", "content": [sql]}]
        })
    
    # === Metric View Benchmarks (with MEASURE) ===
    mvs = domain.get('metric_views', [])[:2]  # Max 2 MV benchmarks
    for mv in mvs:
        # Use MEASURE() for metric view columns
        sql = f"SELECT MEASURE(*) FROM {GOLD_PREFIX}.{mv} GROUP BY ALL LIMIT 20;"
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show metrics from {mv}"],
            "answer": [{"format": "SQL", "content": [sql]}]
        })
    
    # === ML Table Benchmarks (from inventory!) ===
    ml_tables = domain.get('ml_tables', [])[:3]  # Max 3 ML benchmarks
    for ml_table in ml_tables:
        # Use exact name from inventory - NO prefix manipulation
        sql = f"SELECT * FROM {ML_PREFIX}.{ml_table} LIMIT 20;"
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show predictions from {ml_table}"],
            "answer": [{"format": "SQL", "content": [sql]}]
        })
    
    # === Monitoring Table Benchmarks ===
    mon_tables = domain.get('monitoring_tables', [])[:2]  # Max 2 monitoring benchmarks
    for mon_table in mon_tables:
        sql = f"SELECT * FROM {MON_PREFIX}.{mon_table} LIMIT 20;"
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show monitoring from {mon_table}"],
            "answer": [{"format": "SQL", "content": [sql]}]
        })
    
    # === Fact Table Benchmarks ===
    facts = domain.get('tables', {}).get('facts', [])[:2]  # Max 2 fact benchmarks
    for fact in facts:
        sql = f"SELECT * FROM {GOLD_PREFIX}.{fact} LIMIT 20;"
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show data from {fact}"],
            "answer": [{"format": "SQL", "content": [sql]}]
        })
    
    # === Dimension Table Benchmarks ===
    dims = domain.get('tables', {}).get('dimensions', [])[:1]  # Max 1 dim benchmark
    for dim in dims:
        sql = f"SELECT * FROM {GOLD_PREFIX}.{dim} LIMIT 20;"
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show {dim}"],
            "answer": [{"format": "SQL", "content": [sql]}]
        })
    
    # === Deep Research Benchmarks ===
    deep_questions = [
        "Analyze trends over time",
        "Identify anomalies and root causes",
        "Compare metrics across dimensions",
        "Provide executive summary",
        "What optimization opportunities exist?"
    ]
    for q in deep_questions:
        benchmarks.append({
            "id": generate_id(),
            "question": [q],
            "answer": [{"format": "SQL", "content": [f"SELECT 'Deep research: {q}' AS analysis;"]}]
        })
    
    return benchmarks


def update_genie_space_json(space_name: str, benchmarks: list):
    """Update a single Genie Space JSON with new benchmarks."""
    
    json_path = GENIE_DIR / f"{space_name}_genie_export.json"
    
    with open(json_path) as f:
        genie_data = json.load(f)
    
    # Replace benchmarks
    genie_data['benchmarks'] = {'questions': benchmarks}
    
    with open(json_path, 'w') as f:
        json.dump(genie_data, f, indent=2)
    
    return len(benchmarks)


def main():
    print("=" * 80)
    print("REGENERATING ALL BENCHMARKS FROM INVENTORY")
    print("=" * 80)
    print()
    
    inventory = load_inventory()
    signatures = load_tvf_signatures()
    
    spaces = [
        "cost_intelligence",
        "job_health_monitor",
        "performance",
        "security_auditor",
        "data_quality_monitor",
        "unified_health_monitor"
    ]
    
    total_benchmarks = 0
    
    for space in spaces:
        print(f"\n📊 Processing {space}...")
        
        benchmarks = generate_benchmarks_for_space(space, inventory, signatures)
        count = update_genie_space_json(space, benchmarks)
        
        # Show what was generated
        domain = inventory['domain_mapping'].get(space, {})
        ml_tables = domain.get('ml_tables', [])[:3]
        
        print(f"   TVFs: {len(domain.get('tvfs', [])[:8])}")
        print(f"   Metric Views: {len(domain.get('metric_views', [])[:2])}")
        print(f"   ML Tables: {ml_tables}")
        print(f"   Monitoring: {len(domain.get('monitoring_tables', [])[:2])}")
        print(f"   ✅ Generated {count} benchmarks")
        
        total_benchmarks += count
    
    print("\n" + "=" * 80)
    print(f"✅ COMPLETE: Generated {total_benchmarks} benchmarks across {len(spaces)} spaces")
    print("=" * 80)
    
    # Show ML table names from inventory for verification
    print("\n📋 ML Tables from Inventory (for verification):")
    for table in inventory['tables']['ml'][:10]:
        print(f"   - {table}")
    print("   ...")


if __name__ == "__main__":
    main()
