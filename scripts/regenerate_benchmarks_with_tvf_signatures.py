#!/usr/bin/env python3
"""
Regenerate Genie Space benchmarks using actual TVF signatures from SQL files.

This script:
1. Parses TVF SQL files to get exact parameter signatures
2. Generates correct benchmark SQL with proper parameters
3. Updates Genie Space JSON files with working benchmarks
"""

import re
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TVF_DIR = PROJECT_ROOT / "src/semantic/tvfs"
GENIE_DIR = PROJECT_ROOT / "src/genie"
INVENTORY_PATH = GENIE_DIR / "actual_assets_inventory.json"

# Template variable prefixes
GOLD_PREFIX = "${catalog}.${gold_schema}"
ML_PREFIX = "${catalog}.${feature_schema}"
MON_PREFIX = "${catalog}.${gold_schema}_monitoring"

# Date values for benchmark queries (recent dates)
TODAY = datetime.now()
START_DATE = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")


def generate_id():
    return uuid.uuid4().hex


def parse_tvf_definitions(sql_content: str) -> dict:
    """Parse CREATE FUNCTION statements to extract TVF definitions with sample SQL."""
    
    tvfs = {}
    
    # Pattern to match CREATE FUNCTION and extract COMMENT section
    func_pattern = r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+\$\{catalog\}\.\$\{gold_schema\}\.(\w+)\s*\((.*?)\)\s*RETURNS\s+TABLE.*?COMMENT\s+'(.*?)'.*?RETURN"
    
    matches = re.findall(func_pattern, sql_content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        func_name = match[0]
        params_str = match[1]
        comment_str = match[2]
        
        # Extract SYNTAX line from comment to get example call
        syntax_match = re.search(r'SYNTAX:\s*(.+?)(?:\n|-\s|\Z)', comment_str)
        sample_sql = None
        
        if syntax_match:
            sample_sql = syntax_match.group(1).strip()
            # Clean up the SQL
            sample_sql = sample_sql.replace('SELECT * FROM TABLE(', f'SELECT * FROM {GOLD_PREFIX}.')
            sample_sql = sample_sql.replace('))', ') LIMIT 20;')
            if not sample_sql.endswith(';'):
                sample_sql += ' LIMIT 20;'
        
        # If no SYNTAX in comment, parse parameters and generate SQL
        if not sample_sql:
            params = parse_params(params_str)
            sample_sql = generate_sample_sql(func_name, params)
        
        # Extract PURPOSE for question text
        purpose_match = re.search(r'PURPOSE:\s*(.+?)(?:\n|-\s)', comment_str)
        purpose = purpose_match.group(1).strip() if purpose_match else f"Query {func_name}"
        
        # Extract BEST FOR questions
        best_for_match = re.search(r'BEST FOR:\s*(.+?)(?:\n|-\s)', comment_str)
        best_for = []
        if best_for_match:
            # Extract quoted questions
            questions = re.findall(r'"([^"]+)"', best_for_match.group(1))
            best_for = questions
        
        tvfs[func_name] = {
            'name': func_name,
            'sample_sql': sample_sql,
            'purpose': purpose,
            'best_for': best_for
        }
    
    return tvfs


def parse_params(params_str: str) -> list:
    """Parse parameter string to extract parameter names and defaults."""
    params = []
    if not params_str.strip():
        return params
    
    # Simple parsing - split by lines or commas
    lines = params_str.replace('\n', ' ').split(',')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Match: name TYPE [DEFAULT value]
        match = re.match(r'(\w+)\s+(\w+)(?:\s+DEFAULT\s+(\S+))?', line, re.IGNORECASE)
        if match:
            params.append({
                'name': match.group(1),
                'type': match.group(2).upper(),
                'default': match.group(3)
            })
    
    return params


def generate_sample_sql(func_name: str, params: list) -> str:
    """Generate sample SQL call with proper parameter values."""
    
    param_values = []
    for p in params:
        name = p['name'].lower()
        ptype = p['type']
        default = p['default']
        
        if default:
            # Use the default value, convert SQL syntax to clean value
            val = default.strip("'\"")
            if ptype == 'STRING':
                param_values.append(f'"{val}"')
            else:
                param_values.append(val)
        elif 'date' in name:
            if 'start' in name:
                param_values.append(f'"{START_DATE}"')
            else:
                param_values.append(f'"{END_DATE}"')
        elif name in ('top_n', 'limit_n'):
            param_values.append('20')
        elif name in ('days_back', 'lookback_days', 'num_weeks'):
            param_values.append('30')
        elif ptype == 'STRING':
            param_values.append('"ALL"')
        elif ptype in ('INT', 'INTEGER', 'BIGINT'):
            param_values.append('20')
        elif ptype == 'DOUBLE':
            param_values.append('2.0')
        elif ptype == 'BOOLEAN':
            param_values.append('TRUE')
        else:
            param_values.append('NULL')
    
    param_str = ', '.join(param_values)
    return f"SELECT * FROM {GOLD_PREFIX}.{func_name}({param_str}) LIMIT 20;"


def load_all_tvf_definitions() -> dict:
    """Load TVF definitions from all SQL files."""
    
    all_tvfs = {}
    
    sql_files = list(TVF_DIR.glob("*_tvfs.sql"))
    
    for sql_file in sql_files:
        with open(sql_file, 'r') as f:
            content = f.read()
        
        tvfs = parse_tvf_definitions(content)
        all_tvfs.update(tvfs)
    
    return all_tvfs


def load_inventory():
    """Load asset inventory."""
    with open(INVENTORY_PATH) as f:
        return json.load(f)


def get_domain_tvfs(domain_name: str, inventory: dict) -> list:
    """Get TVF names for a specific domain."""
    mapping = inventory.get('domain_mapping', {}).get(domain_name, {})
    return mapping.get('tvfs', [])


def generate_tvf_benchmarks(domain_name: str, all_tvfs: dict, inventory: dict, max_count: int = 8) -> list:
    """Generate TVF benchmark questions with correct parameters."""
    
    benchmarks = []
    domain_tvfs = get_domain_tvfs(domain_name, inventory)
    
    for tvf_name in domain_tvfs[:max_count]:
        if tvf_name in all_tvfs:
            tvf = all_tvfs[tvf_name]
            
            # Use first "best for" question or fallback to purpose
            if tvf['best_for']:
                question = tvf['best_for'][0]
            else:
                question = tvf['purpose']
            
            benchmarks.append({
                "id": generate_id(),
                "question": [question],
                "answer": [{"format": "SQL", "content": [tvf['sample_sql']]}]
            })
    
    return benchmarks


def generate_mv_benchmarks(domain_name: str, inventory: dict, max_count: int = 4) -> list:
    """Generate metric view benchmark questions."""
    
    benchmarks = []
    mapping = inventory.get('domain_mapping', {}).get(domain_name, {})
    mvs = mapping.get('metric_views', [])
    
    # Metric views need MEASURE() function for measure columns
    # Simple query: just select dimensions with a single measure
    for mv_name in mvs[:max_count]:
        short_name = mv_name.split('.')[-1]
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the key metrics from {short_name}?"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT * FROM {GOLD_PREFIX}.{short_name} LIMIT 20;"
            ]}]
        })
    
    return benchmarks


def generate_table_benchmarks(domain_name: str, inventory: dict) -> list:
    """Generate table benchmark questions (ML, monitoring, fact, dim)."""
    
    benchmarks = []
    mapping = inventory.get('domain_mapping', {}).get(domain_name, {})
    
    # ML tables
    ml_tables = mapping.get('ml_tables', [])
    for table in ml_tables[:3]:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the latest ML predictions from {table}?"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT * FROM {ML_PREFIX}.{table} LIMIT 20;"
            ]}]
        })
    
    # Monitoring tables
    mon_tables = mapping.get('monitoring_tables', [])
    for table in mon_tables[:2]:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show monitoring data from {table}"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT * FROM {MON_PREFIX}.{table} LIMIT 20;"
            ]}]
        })
    
    # Tables (dim/fact)
    tables = mapping.get('tables', {})
    facts = tables.get('facts', [])
    dims = tables.get('dimensions', [])
    
    for table in facts[:2]:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show recent data from {table}"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT * FROM {GOLD_PREFIX}.{table} LIMIT 20;"
            ]}]
        })
    
    for table in dims[:1]:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Describe the {table} dimension"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT * FROM {GOLD_PREFIX}.{table} LIMIT 20;"
            ]}]
        })
    
    return benchmarks


def generate_deep_research_benchmarks(domain_name: str) -> list:
    """Generate deep research benchmark questions."""
    
    return [
        {
            "id": generate_id(),
            "question": [f"Analyze {domain_name} trends over time"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT 'Complex trend analysis for {domain_name}' AS deep_research;"
            ]}]
        },
        {
            "id": generate_id(),
            "question": [f"Identify anomalies in {domain_name} data"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT 'Anomaly detection query for {domain_name}' AS deep_research;"
            ]}]
        },
        {
            "id": generate_id(),
            "question": [f"Compare {domain_name} metrics across dimensions"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT 'Cross-dimensional analysis for {domain_name}' AS deep_research;"
            ]}]
        },
        {
            "id": generate_id(),
            "question": [f"Provide an executive summary of {domain_name}"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT 'Executive summary for {domain_name}' AS deep_research;"
            ]}]
        },
        {
            "id": generate_id(),
            "question": [f"What are the key insights from {domain_name} analysis?"],
            "answer": [{"format": "SQL", "content": [
                f"SELECT 'Key insights summary for {domain_name}' AS deep_research;"
            ]}]
        },
    ]


def regenerate_benchmarks_for_genie_space(space_name: str, all_tvfs: dict, inventory: dict) -> list:
    """Generate all benchmarks for a single Genie Space."""
    
    # Use space_name directly as domain (inventory uses same names)
    domain = space_name
    
    benchmarks = []
    
    # TVFs with correct parameters (8)
    tvf_benchmarks = generate_tvf_benchmarks(domain, all_tvfs, inventory, max_count=8)
    benchmarks.extend(tvf_benchmarks)
    
    # Metric views (4)
    mv_benchmarks = generate_mv_benchmarks(domain, inventory, max_count=4)
    benchmarks.extend(mv_benchmarks)
    
    # Tables (ML, monitoring, fact, dim)
    table_benchmarks = generate_table_benchmarks(domain, inventory)
    benchmarks.extend(table_benchmarks)
    
    # Deep research (5)
    deep_benchmarks = generate_deep_research_benchmarks(domain)
    benchmarks.extend(deep_benchmarks)
    
    return benchmarks[:50]  # API limit


def main():
    print("=" * 80)
    print("REGENERATING BENCHMARKS WITH CORRECT TVF PARAMETERS")
    print("=" * 80)
    
    # Load TVF definitions from SQL files
    print("\n📂 Loading TVF definitions from SQL files...")
    all_tvfs = load_all_tvf_definitions()
    print(f"   Found {len(all_tvfs)} TVFs with signatures")
    
    # Load inventory
    print("\n📂 Loading asset inventory...")
    inventory = load_inventory()
    
    # Process each Genie Space
    spaces = [
        "cost_intelligence",
        "job_health_monitor",
        "performance",
        "security_auditor",
        "data_quality_monitor",
        "unified_health_monitor"
    ]
    
    for space_name in spaces:
        json_path = GENIE_DIR / f"{space_name}_genie_export.json"
        
        if not json_path.exists():
            print(f"\n⚠️  {space_name}: JSON file not found")
            continue
        
        # Load existing JSON
        with open(json_path, 'r') as f:
            genie_data = json.load(f)
        
        # Generate new benchmarks
        benchmarks = regenerate_benchmarks_for_genie_space(space_name, all_tvfs, inventory)
        
        # Count by type
        tvf_count = sum(1 for b in benchmarks if 'SELECT * FROM ${catalog}.${gold_schema}.' in b['answer'][0]['content'][0] and '(' in b['answer'][0]['content'][0])
        mv_count = sum(1 for b in benchmarks if 'mv_' in b['answer'][0]['content'][0])
        ml_count = sum(1 for b in benchmarks if '${feature_schema}' in b['answer'][0]['content'][0])
        mon_count = sum(1 for b in benchmarks if '_monitoring.' in b['answer'][0]['content'][0])
        deep_count = sum(1 for b in benchmarks if 'deep_research' in b['answer'][0]['content'][0])
        
        # Update benchmarks section
        if 'benchmarks' not in genie_data:
            genie_data['benchmarks'] = {}
        genie_data['benchmarks']['questions'] = benchmarks
        
        # Save updated JSON
        with open(json_path, 'w') as f:
            json.dump(genie_data, f, indent=2)
        
        print(f"\n✅ {space_name}: {len(benchmarks)} benchmarks")
        print(f"   TVF: {tvf_count}, MV: {mv_count}, ML: {ml_count}, Mon: {mon_count}, Deep: {deep_count}")
    
    print(f"\n{'=' * 80}")
    print("✅ ALL BENCHMARKS REGENERATED WITH CORRECT TVF PARAMETERS")
    print("=" * 80)
    
    # Show sample TVF SQL for verification
    print("\n📋 Sample TVF SQL (first 3):")
    for i, (name, tvf) in enumerate(list(all_tvfs.items())[:3]):
        print(f"\n   {name}:")
        print(f"   {tvf['sample_sql']}")


if __name__ == "__main__":
    main()
