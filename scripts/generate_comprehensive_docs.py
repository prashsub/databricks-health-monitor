#!/usr/bin/env python3
"""
Generate comprehensive dashboard documentation with ALL datasets and SQL queries.

This script extracts every dataset, metric, widget, and query from all dashboards
and generates complete markdown documentation.

Usage:
    python scripts/generate_comprehensive_docs.py
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Dashboard configuration
DASHBOARDS = {
    'cost': {
        'file': 'src/dashboards/cost.lvdash.json',
        'display_name': 'Cost Management',
        'domain_number': '01'
    },
    'reliability': {
        'file': 'src/dashboards/reliability.lvdash.json',
        'display_name': 'Job Reliability',
        'domain_number': '02'
    },
    'performance': {
        'file': 'src/dashboards/performance.lvdash.json',
        'display_name': 'Query Performance',
        'domain_number': '03'
    },
    'quality': {
        'file': 'src/dashboards/quality.lvdash.json',
        'display_name': 'Data Quality',
        'domain_number': '04'
    },
    'security': {
        'file': 'src/dashboards/security.lvdash.json',
        'display_name': 'Security & Audit',
        'domain_number': '05'
    },
    'unified': {
        'file': 'src/dashboards/unified.lvdash.json',
        'display_name': 'Unified Overview',
        'domain_number': '06'
    }
}

OUTPUT_DIR = Path('docs/dashboard-framework-design/actual-implementation')


def load_dashboard(dashboard_path: str) -> dict:
    """Load dashboard JSON file"""
    with open(dashboard_path, 'r') as f:
        return json.load(f)


def extract_datasets(dashboard: dict) -> List[dict]:
    """Extract all datasets with full details"""
    datasets = []
    for ds in dashboard.get('datasets', []):
        dataset_info = {
            'name': ds.get('name', ''),
            'display_name': ds.get('displayName', ''),
            'query': ds.get('query', ''),
            'parameters': [
                {
                    'keyword': p.get('keyword', ''),
                    'dataType': p.get('dataType', ''),
                    'displayName': p.get('displayName', '')
                }
                for p in ds.get('parameters', [])
            ]
        }
        datasets.append(dataset_info)
    return datasets


def extract_pages(dashboard: dict) -> List[dict]:
    """Extract page information"""
    pages = []
    for page in dashboard.get('pages', []):
        page_info = {
            'name': page.get('name', ''),
            'display_name': page.get('displayName', ''),
            'layout': page.get('layout', [])
        }
        pages.append(page_info)
    return pages


def generate_dataset_catalog(domain: str, config: dict, datasets: List[dict]) -> str:
    """Generate complete dataset catalog markdown"""
    
    md = f"""# Complete {config['display_name']} Dataset Catalog

## Overview
**Total Datasets:** {len(datasets)}  
**Dashboard:** `{Path(config['file']).name}`  
**Coverage:** ALL datasets from ALL pages with FULL details

---

## Dataset Index

| # | Dataset Name | Display Name | Has Query | Parameters |
|---|--------------|--------------|-----------|------------|
"""
    
    for i, ds in enumerate(datasets, 1):
        has_query = '✅' if ds['query'] else '❌'
        params = ', '.join([p['keyword'] for p in ds['parameters']]) if ds['parameters'] else '-'
        md += f"| {i} | {ds['name']} | {ds['display_name']} | {has_query} | {params} |\n"
    
    md += "\n---\n\n## Complete SQL Queries\n\n"
    
    for i, ds in enumerate(datasets, 1):
        md += f"\n### Dataset {i}: {ds['name']}\n\n"
        md += f"**Display Name:** {ds['display_name']}  \n"
        
        if ds['parameters']:
            md += f"**Parameters:**\n"
            for param in ds['parameters']:
                md += f"- `{param['keyword']}` ({param['dataType']})"
                if param['displayName']:
                    md += f" - {param['displayName']}"
                md += "\n"
            md += "\n"
        
        if ds['query']:
            md += f"**SQL Query:**\n```sql\n{ds['query']}\n```\n\n"
        else:
            md += f"**SQL Query:** None (parameter/filter dataset)\n\n"
        
        md += "---\n"
    
    return md


def generate_metrics_catalog(domain: str, config: dict, datasets: List[dict]) -> str:
    """Generate metrics catalog from dataset queries"""
    
    md = f"""# Complete {config['display_name']} Metrics Catalog

## Overview

This document catalogs ALL metrics, calculations, and measures from the {config['display_name']} dashboard.

---

## Metrics Extracted from Datasets

"""
    
    # Analyze queries to extract metrics
    for ds in datasets:
        if ds['query'] and not ds['name'].startswith('select_') and not ds['name'].startswith('ds_select'):
            md += f"\n### {ds['display_name']}\n"
            md += f"**Dataset:** `{ds['name']}`  \n\n"
            
            query = ds['query'].upper()
            
            # Extract common metric patterns
            if 'SUM(' in query:
                md += "**Aggregations:** SUM  \n"
            if 'AVG(' in query:
                md += "**Aggregations:** AVG  \n"
            if 'COUNT(' in query:
                md += "**Aggregations:** COUNT  \n"
            if 'MAX(' in query:
                md += "**Aggregations:** MAX  \n"
            if 'MIN(' in query:
                md += "**Aggregations:** MIN  \n"
            if 'PERCENTILE' in query:
                md += "**Aggregations:** PERCENTILE  \n"
            
            # Identify fact tables
            if 'fact_usage' in ds['query']:
                md += "**Source Table:** fact_usage  \n"
            if 'fact_job_run_timeline' in ds['query']:
                md += "**Source Table:** fact_job_run_timeline  \n"
            if 'fact_query_history' in ds['query']:
                md += "**Source Table:** fact_query_history  \n"
            if 'fact_audit_logs' in ds['query']:
                md += "**Source Table:** fact_audit_logs  \n"
            
            md += "\n"
    
    return md


def main():
    """Generate comprehensive documentation for all dashboards"""
    
    print("🔍 Generating Comprehensive Dashboard Documentation")
    print("=" * 80)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_datasets = 0
    
    for domain, config in DASHBOARDS.items():
        print(f"\n📊 Processing {config['display_name']}...")
        
        # Load dashboard
        dashboard = load_dashboard(config['file'])
        datasets = extract_datasets(dashboard)
        pages = extract_pages(dashboard)
        
        total_datasets += len(datasets)
        print(f"   ✅ Extracted {len(datasets)} datasets")
        print(f"   ✅ Extracted {len(pages)} pages")
        
        # Generate dataset catalog
        catalog_md = generate_dataset_catalog(domain, config, datasets)
        catalog_file = OUTPUT_DIR / f"COMPLETE-{config['domain_number']}-{domain}-datasets.md"
        catalog_file.write_text(catalog_md)
        print(f"   ✅ Generated {catalog_file.name}")
        
        # Generate metrics catalog
        metrics_md = generate_metrics_catalog(domain, config, datasets)
        metrics_file = OUTPUT_DIR / f"COMPLETE-{config['domain_number']}-{domain}-metrics.md"
        metrics_file.write_text(metrics_md)
        print(f"   ✅ Generated {metrics_file.name}")
    
    print("\n" + "=" * 80)
    print(f"✅ COMPLETE: Generated comprehensive documentation for {total_datasets} datasets")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("\nGenerated files:")
    print("- Dataset catalogs: COMPLETE-[NN]-[domain]-datasets.md (all datasets + full SQL)")
    print("- Metrics catalogs: COMPLETE-[NN]-[domain]-metrics.md (all metrics extracted)")


if __name__ == '__main__':
    main()




