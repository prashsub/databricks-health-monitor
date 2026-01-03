#!/usr/bin/env python3
"""
Add Intelligent Filters to All Dashboard Datasets

This script processes all dashboard JSON files and adds filter support to their datasets.
Filters are applied intelligently based on which tables the query references.

Filter Rules:
- fact_usage: time_window, workspace_name, sku_category
- fact_job_run_timeline: time_window, workspace_name
- fact_audit_logs: time_window, workspace_name  
- fact_query_history: time_window, workspace_name
- fact_node_timeline: time_window, workspace_name
- fact_table_lineage: workspace_name
- dim_* tables: No time filter (dimensions are current)
"""

import json
import re
from pathlib import Path
from copy import deepcopy

# Define which filters apply to which tables
TABLE_FILTERS = {
    'fact_usage': {
        'time_column': 'usage_date',
        'filters': ['time_window', 'workspace_name', 'sku_category']
    },
    'fact_job_run_timeline': {
        'time_column': 'run_date',
        'filters': ['time_window', 'workspace_name']
    },
    'fact_audit_logs': {
        'time_column': 'event_date',
        'filters': ['time_window', 'workspace_name']
    },
    'fact_query_history': {
        'time_column': 'DATE(start_time)',
        'filters': ['time_window', 'workspace_name']
    },
    'fact_node_timeline': {
        'time_column': 'DATE(start_time)',
        'filters': ['time_window', 'workspace_name']
    },
    'fact_table_lineage': {
        'time_column': None,
        'filters': ['workspace_name']
    }
}

# Filter parameter definitions
FILTER_PARAMS = {
    'time_window': {
        "displayName": "Time Window",
        "keyword": "time_window",
        "dataType": "STRING",
        "defaultSelection": {
            "values": {
                "dataType": "STRING",
                "values": [{"value": "Last 30 Days"}]
            }
        }
    },
    'workspace_name': {
        "displayName": "Workspace",
        "keyword": "workspace_name",
        "dataType": "STRING",
        "defaultSelection": {
            "values": {
                "dataType": "STRING",
                "values": [{"value": "All"}]
            }
        }
    },
    'sku_category': {
        "displayName": "SKU Type",
        "keyword": "sku_category",
        "dataType": "STRING",
        "defaultSelection": {
            "values": {
                "dataType": "STRING",
                "values": [{"value": "All"}]
            }
        }
    },
    'owner_name': {
        "displayName": "Owner",
        "keyword": "owner_name",
        "dataType": "STRING",
        "defaultSelection": {
            "values": {
                "dataType": "STRING",
                "values": [{"value": "All"}]
            }
        }
    }
}


def detect_tables(query: str) -> list:
    """Detect which fact tables are used in a query."""
    tables = []
    query_lower = query.lower()
    
    for table in TABLE_FILTERS.keys():
        if table.lower() in query_lower:
            tables.append(table)
    
    return tables


def get_table_alias(query: str, table_name: str) -> str:
    """Get the alias used for a table in the query."""
    # Pattern: table_name [AS] alias
    patterns = [
        rf'{table_name}\s+(?:AS\s+)?(\w+)',
        rf'{table_name}\s+(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            alias = match.group(1)
            # Make sure it's not a SQL keyword
            if alias.upper() not in ['WHERE', 'AND', 'OR', 'ON', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'GROUP', 'ORDER', 'LIMIT']:
                return alias
    
    return None


def build_time_filter(time_column: str, alias: str = None) -> str:
    """Build the time window filter condition."""
    col = f"{alias}.{time_column}" if alias else time_column
    
    return f"""CASE :time_window
        WHEN 'Last 7 Days' THEN {col} >= CURRENT_DATE() - INTERVAL 7 DAYS
        WHEN 'Last 30 Days' THEN {col} >= CURRENT_DATE() - INTERVAL 30 DAYS
        WHEN 'Last 90 Days' THEN {col} >= CURRENT_DATE() - INTERVAL 90 DAYS
        WHEN 'Last 6 Months' THEN {col} >= CURRENT_DATE() - INTERVAL 180 DAYS
        WHEN 'Last Year' THEN {col} >= CURRENT_DATE() - INTERVAL 365 DAYS
        ELSE TRUE
    END"""


def build_workspace_filter(alias: str = None) -> str:
    """Build the workspace filter condition."""
    col = f"{alias}.workspace_id" if alias else "workspace_id"
    return f"IF(:workspace_name = 'All', TRUE, {col} IN (SELECT workspace_id FROM ${{catalog}}.${{gold_schema}}.dim_workspace WHERE workspace_name = :workspace_name))"


def build_sku_filter(alias: str = None) -> str:
    """Build the SKU category filter condition."""
    col = f"{alias}.billing_origin_product" if alias else "billing_origin_product"
    return f"IF(:sku_category = 'All', TRUE, {col} = :sku_category)"


def find_main_where_position(query: str) -> int:
    """
    Find the position of the main WHERE clause (not in CTEs or subqueries).
    Returns -1 if no WHERE found or if WHERE is only in CTEs/subqueries.
    """
    # Simple heuristic: find the last WHERE that's not inside parentheses
    query_upper = query.upper()
    
    # If query has WITH clause (CTE), find the position after the CTE
    cte_end = 0
    if query_upper.strip().startswith('WITH'):
        # Find matching parenthesis for CTE
        depth = 0
        in_string = False
        for i, char in enumerate(query):
            if char == "'" and not in_string:
                in_string = True
            elif char == "'" and in_string:
                in_string = False
            elif not in_string:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        # Check if next non-space is SELECT or comma
                        rest = query[i+1:].strip()
                        if rest.upper().startswith('SELECT'):
                            cte_end = i + 1
                            break
                        elif rest.startswith(','):
                            continue  # More CTEs
    
    # Find WHERE after the main SELECT
    main_query = query[cte_end:]
    where_match = re.search(r'\bWHERE\b', main_query, re.IGNORECASE)
    
    if where_match:
        return cte_end + where_match.start()
    return -1


def add_filters_to_query(query: str, tables: list) -> tuple:
    """
    Add filter conditions to a query.
    Returns (modified_query, list_of_filters_added).
    """
    if not tables:
        return query, []
    
    # Skip if already has filter parameters
    if ':time_window' in query or ':workspace_name' in query:
        return query, []
    
    # Get the primary table (first one found)
    primary_table = tables[0]
    table_config = TABLE_FILTERS.get(primary_table, {})
    
    if not table_config:
        return query, []
    
    # Get alias for the table
    alias = get_table_alias(query, primary_table)
    
    # Build filter conditions
    conditions = []
    filters_used = []
    
    for filter_name in table_config.get('filters', []):
        if filter_name == 'time_window' and table_config.get('time_column'):
            conditions.append(build_time_filter(table_config['time_column'], alias))
            filters_used.append('time_window')
        elif filter_name == 'workspace_name':
            conditions.append(build_workspace_filter(alias))
            filters_used.append('workspace_name')
        elif filter_name == 'sku_category':
            conditions.append(build_sku_filter(alias))
            filters_used.append('sku_category')
    
    if not conditions:
        return query, []
    
    # Join conditions
    filter_clause = " AND ".join(conditions)
    
    # Find main WHERE position (not in CTEs)
    where_pos = find_main_where_position(query)
    
    if where_pos >= 0:
        # Append to existing WHERE using AND
        # Find the WHERE keyword and add conditions after it
        where_end = where_pos + len('WHERE')
        # Skip whitespace after WHERE
        while where_end < len(query) and query[where_end].isspace():
            where_end += 1
        
        modified_query = query[:where_end] + f"({filter_clause}) AND " + query[where_end:]
    else:
        # No main WHERE - add before GROUP BY, ORDER BY, LIMIT, or at end
        # But need to handle CTEs - add after main FROM clause
        query_upper = query.upper()
        
        # Find the main FROM clause (after CTEs)
        cte_end = 0
        if query_upper.strip().startswith('WITH'):
            # Find the main SELECT after CTEs
            select_match = re.search(r'\)\s*SELECT\b', query, re.IGNORECASE)
            if select_match:
                cte_end = select_match.start() + 1
        
        main_query = query[cte_end:]
        
        if re.search(r'\bGROUP\s+BY\b', main_query, re.IGNORECASE):
            match = re.search(r'\bGROUP\s+BY\b', main_query, re.IGNORECASE)
            insert_pos = cte_end + match.start()
            modified_query = query[:insert_pos] + f' WHERE ({filter_clause}) ' + query[insert_pos:]
        elif re.search(r'\bORDER\s+BY\b', main_query, re.IGNORECASE):
            match = re.search(r'\bORDER\s+BY\b', main_query, re.IGNORECASE)
            insert_pos = cte_end + match.start()
            modified_query = query[:insert_pos] + f' WHERE ({filter_clause}) ' + query[insert_pos:]
        elif re.search(r'\bLIMIT\b', main_query, re.IGNORECASE):
            match = re.search(r'\bLIMIT\b', main_query, re.IGNORECASE)
            insert_pos = cte_end + match.start()
            modified_query = query[:insert_pos] + f' WHERE ({filter_clause}) ' + query[insert_pos:]
        else:
            modified_query = f"{query} WHERE ({filter_clause})"
    
    return modified_query, filters_used


def process_dataset(dataset: dict) -> dict:
    """Process a single dataset to add filter support."""
    ds_name = dataset.get('name', '')
    query = dataset.get('query', '')
    
    # Skip filter datasets
    if ds_name.startswith('gf_ds_'):
        return dataset
    
    # Skip if no query
    if not query:
        return dataset
    
    # Detect tables
    tables = detect_tables(query)
    
    if not tables:
        return dataset
    
    # Add filters to query
    modified_query, filters_used = add_filters_to_query(query, tables)
    
    if not filters_used:
        return dataset
    
    # Create modified dataset
    modified = deepcopy(dataset)
    modified['query'] = modified_query
    
    # Add parameters if not already present
    if 'parameters' not in modified:
        modified['parameters'] = []
    
    existing_keywords = {p.get('keyword') for p in modified.get('parameters', [])}
    for filter_name in filters_used:
        if filter_name not in existing_keywords and filter_name in FILTER_PARAMS:
            modified['parameters'].append(deepcopy(FILTER_PARAMS[filter_name]))
    
    return modified


def process_dashboard(file_path: Path, dry_run: bool = False) -> dict:
    """Process a dashboard file to add filters to all datasets."""
    with open(file_path, 'r') as f:
        dashboard = json.load(f)
    
    results = {
        'file': file_path.name,
        'datasets_total': 0,
        'datasets_modified': 0,
        'filters_added': []
    }
    
    datasets = dashboard.get('datasets', [])
    results['datasets_total'] = len(datasets)
    
    modified_datasets = []
    for ds in datasets:
        original_query = ds.get('query', '')
        modified_ds = process_dataset(ds)
        modified_datasets.append(modified_ds)
        
        if modified_ds.get('query', '') != original_query:
            results['datasets_modified'] += 1
            results['filters_added'].append({
                'dataset': ds.get('name', 'unknown'),
                'filters': [p.get('keyword') for p in modified_ds.get('parameters', [])]
            })
    
    dashboard['datasets'] = modified_datasets
    
    if not dry_run:
        with open(file_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Add intelligent filters to dashboard datasets')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    parser.add_argument('--file', type=str, help='Process a specific file only')
    args = parser.parse_args()
    
    dashboard_dir = Path('src/dashboards')
    
    if args.file:
        files = [dashboard_dir / args.file]
    else:
        files = list(dashboard_dir.glob('*.lvdash.json'))
        # Exclude unified dashboard (it's built from others)
        files = [f for f in files if 'unified' not in f.name]
    
    print("=" * 80)
    print("ADDING INTELLIGENT FILTERS TO DASHBOARD DATASETS")
    print("=" * 80)
    if args.dry_run:
        print("** DRY RUN MODE - No files will be modified **\n")
    
    total_modified = 0
    
    for file_path in files:
        print(f"\nProcessing: {file_path.name}")
        
        results = process_dashboard(file_path, dry_run=args.dry_run)
        
        print(f"  Total datasets: {results['datasets_total']}")
        print(f"  Modified: {results['datasets_modified']}")
        
        if results['filters_added']:
            print(f"  Filters added:")
            for item in results['filters_added'][:5]:  # Show first 5
                print(f"    - {item['dataset']}: {', '.join(item['filters'])}")
            if len(results['filters_added']) > 5:
                print(f"    ... and {len(results['filters_added']) - 5} more")
        
        total_modified += results['datasets_modified']
    
    print("\n" + "=" * 80)
    print(f"TOTAL: Modified {total_modified} datasets across {len(files)} dashboards")
    print("=" * 80)
    
    if args.dry_run:
        print("\n** Run without --dry-run to apply changes **")


if __name__ == '__main__':
    main()

