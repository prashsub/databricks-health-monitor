#!/usr/bin/env python3
"""
Extract TVF signatures from SQL files and generate correct benchmark SQL.

This script parses the actual TVF SQL definitions to get:
- Function name
- Parameter names, types, and default values
- Example usage SQL with proper parameter values
"""

import re
import json
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TVF_DIR = PROJECT_ROOT / "src/semantic/tvfs"
OUTPUT_PATH = PROJECT_ROOT / "src/genie/tvf_signatures.json"

# Default values for benchmark queries
# Use dates relative to "today" for realistic queries
TODAY = datetime.now()
START_DATE = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")
START_DATE_7D = (TODAY - timedelta(days=7)).strftime("%Y-%m-%d")

# Default sample values for common parameter types
DEFAULT_VALUES = {
    # Date parameters
    'start_date': f'"{START_DATE}"',
    'end_date': f'"{END_DATE}"',
    # Numeric parameters
    'top_n': '20',
    'limit_n': '20',
    'num_weeks': '4',
    'lookback_days': '30',
    'threshold': '100',
    'days_back': '30',
    'threshold_seconds': '300',
    'anomaly_threshold': '2.0',
    'threshold_pct': '50',
    'retention_threshold_days': '30',
    'idle_threshold_days': '30',
    'hours_threshold': '1',
    # String filter parameters
    'sku_filter': '"ALL"',
    'tag_key': '"team"',
    'workspace_filter': '"ALL"',
    'job_name_filter': '"ALL"',
    'job_id': 'NULL',
    'cluster_type_filter': '"ALL"',
    'warehouse_filter': '"ALL"',
    'user_filter': '"ALL"',
    'period_type': '"daily"',
    'action_filter': '"ALL"',
    'table_filter': '"ALL"',
    'domain_filter': '"ALL"',
    'risk_level': '"ALL"',
    'include_service_principals': 'TRUE',
}


def parse_tvf_signature(sql_content: str) -> list:
    """Parse CREATE FUNCTION statements to extract TVF signatures."""
    
    tvfs = []
    
    # Pattern to match CREATE FUNCTION ... RETURNS TABLE
    pattern = r'CREATE\s+OR\s+REPLACE\s+FUNCTION\s+\$\{catalog\}\.\$\{gold_schema\}\.(\w+)\s*\((.*?)\)\s*RETURNS\s+TABLE'
    
    matches = re.findall(pattern, sql_content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        func_name = match[0]
        params_str = match[1]
        
        # Parse parameters
        params = []
        if params_str.strip():
            # Split by comma, but be careful with nested parentheses
            param_lines = re.split(r',\s*(?=\w+\s+\w+)', params_str.strip())
            
            for param_line in param_lines:
                param_line = param_line.strip()
                if not param_line:
                    continue
                
                # Pattern: param_name TYPE [DEFAULT value] [COMMENT '...']
                param_match = re.match(
                    r"(\w+)\s+(\w+)(?:\s+DEFAULT\s+([^\s']+|'[^']*'))?",
                    param_line,
                    re.IGNORECASE
                )
                
                if param_match:
                    param_name = param_match.group(1)
                    param_type = param_match.group(2).upper()
                    default_val = param_match.group(3) if param_match.group(3) else None
                    
                    params.append({
                        'name': param_name,
                        'type': param_type,
                        'default': default_val,
                        'has_default': default_val is not None
                    })
        
        tvfs.append({
            'name': func_name,
            'params': params,
            'param_count': len(params),
            'required_params': sum(1 for p in params if not p['has_default'])
        })
    
    return tvfs


def generate_sample_call(tvf: dict, catalog_prefix: str = "${catalog}.${gold_schema}") -> str:
    """Generate a sample SQL call for a TVF with proper parameters."""
    
    func_name = tvf['name']
    params = tvf['params']
    
    # Build parameter list
    param_values = []
    for param in params:
        param_name = param['name']
        
        # Use default value from SQL if available
        if param['has_default'] and param['default']:
            val = param['default']
            # Clean up the value
            if val.startswith("'") and val.endswith("'"):
                val = f'"{val[1:-1]}"'  # Convert SQL string to double-quoted
            param_values.append(val)
        # Use our predefined sample values
        elif param_name in DEFAULT_VALUES:
            param_values.append(DEFAULT_VALUES[param_name])
        # Generate sensible defaults based on type
        elif param['type'] == 'STRING':
            param_values.append('"ALL"')
        elif param['type'] in ('INT', 'INTEGER', 'BIGINT'):
            param_values.append('20')
        elif param['type'] == 'DOUBLE':
            param_values.append('2.0')
        elif param['type'] == 'BOOLEAN':
            param_values.append('TRUE')
        else:
            param_values.append('NULL')
    
    # Build SQL
    param_str = ', '.join(param_values)
    return f"SELECT * FROM {catalog_prefix}.{func_name}({param_str}) LIMIT 20;"


def main():
    print("=" * 80)
    print("EXTRACTING TVF SIGNATURES FROM SQL FILES")
    print("=" * 80)
    
    all_tvfs = {}
    
    # Process each SQL file
    sql_files = list(TVF_DIR.glob("*_tvfs.sql"))
    print(f"\nFound {len(sql_files)} TVF SQL files:")
    
    for sql_file in sorted(sql_files):
        print(f"\n📄 Processing: {sql_file.name}")
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        tvfs = parse_tvf_signature(content)
        
        for tvf in tvfs:
            tvf['source_file'] = sql_file.name
            tvf['sample_sql'] = generate_sample_call(tvf)
            all_tvfs[tvf['name']] = tvf
            
            # Print summary
            param_summary = ', '.join(
                f"{p['name']}{'*' if not p['has_default'] else ''}"
                for p in tvf['params']
            )
            print(f"   ✓ {tvf['name']}({param_summary})")
    
    print(f"\n\n{'=' * 80}")
    print(f"TOTAL TVFs EXTRACTED: {len(all_tvfs)}")
    print("=" * 80)
    
    # Save to JSON
    output = {
        'generated_at': datetime.now().isoformat(),
        'tvf_count': len(all_tvfs),
        'sample_date_range': {
            'start_date': START_DATE,
            'end_date': END_DATE
        },
        'tvfs': all_tvfs
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved TVF signatures to: {OUTPUT_PATH}")
    
    # Print sample SQL for verification
    print(f"\n{'=' * 80}")
    print("SAMPLE SQL CALLS (first 5 TVFs)")
    print("=" * 80)
    
    for i, (name, tvf) in enumerate(list(all_tvfs.items())[:5]):
        print(f"\n{i+1}. {name}:")
        print(f"   {tvf['sample_sql']}")
    
    return all_tvfs


if __name__ == "__main__":
    main()
