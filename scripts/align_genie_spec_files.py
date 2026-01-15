#!/usr/bin/env python3
"""
Align Genie Space spec files (.md) with the actual_assets_inventory.json.

This script:
1. Reads the verified assets from actual_assets_inventory.json
2. Compares against each .md spec file's Data Assets section
3. Reports discrepancies and generates updates
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

# Paths
INVENTORY_PATH = Path("src/genie/actual_assets_inventory.json")
GENIE_DIR = Path("src/genie")

def load_inventory():
    """Load the verified assets inventory."""
    with open(INVENTORY_PATH) as f:
        return json.load(f)

def extract_tables_from_md(md_content: str, section_pattern: str) -> Set[str]:
    """Extract table names from a markdown table section."""
    tables = set()
    # Find the section and extract table names from markdown tables
    # Pattern matches: | `table_name` |
    pattern = r'\| `([^`]+)` \|'
    
    # Find the section
    section_match = re.search(section_pattern, md_content, re.IGNORECASE)
    if section_match:
        start = section_match.end()
        # Find next major section (starts with ###)
        end_match = re.search(r'\n### ', md_content[start:])
        end = start + end_match.start() if end_match else len(md_content)
        section_text = md_content[start:end]
        
        # Extract table names
        tables = set(re.findall(pattern, section_text))
    
    return tables

def compare_assets(spec_name: str, inventory: Dict, md_content: str) -> Dict:
    """Compare spec file assets against inventory."""
    domain_mapping = inventory.get('domain_mapping', {}).get(spec_name, {})
    
    results = {
        'dimensions': {'inventory': set(), 'spec': set()},
        'facts': {'inventory': set(), 'spec': set()},
        'ml_tables': {'inventory': set(), 'spec': set()},
        'monitoring_tables': {'inventory': set(), 'spec': set()},
        'metric_views': {'inventory': set(), 'spec': set()},
        'tvfs': {'inventory': set(), 'spec': set()}
    }
    
    # Get inventory assets
    if domain_mapping:
        results['dimensions']['inventory'] = set(domain_mapping.get('tables', {}).get('dimensions', []))
        results['facts']['inventory'] = set(domain_mapping.get('tables', {}).get('facts', []))
        results['ml_tables']['inventory'] = set(domain_mapping.get('ml_tables', []))
        results['monitoring_tables']['inventory'] = set(domain_mapping.get('monitoring_tables', []))
        results['metric_views']['inventory'] = set(domain_mapping.get('metric_views', []))
        results['tvfs']['inventory'] = set(domain_mapping.get('tvfs', []))
    
    # Extract from spec file
    results['dimensions']['spec'] = extract_tables_from_md(md_content, r'### Dimension Tables')
    results['facts']['spec'] = extract_tables_from_md(md_content, r'### Fact Tables')
    results['ml_tables']['spec'] = extract_tables_from_md(md_content, r'### ML Prediction Tables')
    results['monitoring_tables']['spec'] = extract_tables_from_md(md_content, r'### Lakehouse Monitoring Tables')
    results['metric_views']['spec'] = extract_tables_from_md(md_content, r'### Metric Views')
    results['tvfs']['spec'] = extract_tables_from_md(md_content, r'### Table-Valued Functions|### TVF Quick Reference')
    
    return results

def analyze_discrepancies(results: Dict) -> Dict:
    """Analyze differences between inventory and spec."""
    discrepancies = {}
    
    for asset_type, data in results.items():
        inv = data['inventory']
        spec = data['spec']
        
        missing_in_spec = inv - spec
        extra_in_spec = spec - inv
        
        if missing_in_spec or extra_in_spec:
            discrepancies[asset_type] = {
                'missing_in_spec': sorted(missing_in_spec),
                'extra_in_spec': sorted(extra_in_spec),
                'inventory_count': len(inv),
                'spec_count': len(spec)
            }
    
    return discrepancies

def main():
    print("=" * 80)
    print("GENIE SPEC FILE ALIGNMENT ANALYSIS")
    print("=" * 80)
    print(f"Inventory: {INVENTORY_PATH}")
    print()
    
    inventory = load_inventory()
    
    genie_spaces = {
        'cost_intelligence': 'cost_intelligence_genie.md',
        'job_health_monitor': 'job_health_monitor_genie.md',
        'performance': 'performance_genie.md',
        'security_auditor': 'security_auditor_genie.md',
        'data_quality_monitor': 'data_quality_monitor_genie.md',
        'unified_health_monitor': 'unified_health_monitor_genie.md'
    }
    
    all_discrepancies = {}
    
    for space_key, md_file in genie_spaces.items():
        md_path = GENIE_DIR / md_file
        
        if not md_path.exists():
            print(f"⚠️  {md_file} not found")
            continue
        
        print(f"\n--- {space_key.replace('_', ' ').upper()} ---")
        print(f"  File: {md_file}")
        
        with open(md_path) as f:
            md_content = f.read()
        
        results = compare_assets(space_key, inventory, md_content)
        discrepancies = analyze_discrepancies(results)
        
        if discrepancies:
            all_discrepancies[space_key] = discrepancies
            print(f"  ⚠️  Found discrepancies:")
            
            for asset_type, diff in discrepancies.items():
                print(f"\n    {asset_type.upper()}:")
                print(f"      Inventory: {diff['inventory_count']} | Spec: {diff['spec_count']}")
                
                if diff['missing_in_spec']:
                    print(f"      Missing in spec: {', '.join(diff['missing_in_spec'][:5])}")
                    if len(diff['missing_in_spec']) > 5:
                        print(f"        ... and {len(diff['missing_in_spec']) - 5} more")
                
                if diff['extra_in_spec']:
                    print(f"      Extra in spec: {', '.join(diff['extra_in_spec'][:5])}")
                    if len(diff['extra_in_spec']) > 5:
                        print(f"        ... and {len(diff['extra_in_spec']) - 5} more")
        else:
            print(f"  ✅ Fully aligned with inventory")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_spaces = len(genie_spaces)
    aligned_spaces = total_spaces - len(all_discrepancies)
    
    print(f"  Total Genie Spaces: {total_spaces}")
    print(f"  Fully Aligned: {aligned_spaces}")
    print(f"  Need Updates: {len(all_discrepancies)}")
    
    if all_discrepancies:
        print("\n  Spaces needing updates:")
        for space in all_discrepancies:
            print(f"    - {space}")
    
    # Generate update recommendations
    if all_discrepancies:
        print("\n" + "=" * 80)
        print("RECOMMENDED UPDATES")
        print("=" * 80)
        
        for space, discrepancies in all_discrepancies.items():
            print(f"\n### {space}.md")
            
            for asset_type, diff in discrepancies.items():
                if diff['missing_in_spec']:
                    print(f"\n  ADD to {asset_type} section:")
                    for item in diff['missing_in_spec']:
                        print(f"    + {item}")
                
                if diff['extra_in_spec']:
                    print(f"\n  REMOVE from {asset_type} section:")
                    for item in diff['extra_in_spec']:
                        print(f"    - {item}")
    
    return all_discrepancies

if __name__ == "__main__":
    main()
