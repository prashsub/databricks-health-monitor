#!/usr/bin/env python3
"""
Anti-Regression Validation for Dashboard Widget Encodings

This script validates that all widget field references (encodings) 
match the columns returned by their associated queries.

Run BEFORE every dashboard edit to capture baseline:
    python validate_widget_encodings.py --snapshot

Run AFTER every edit to check for regressions:
    python validate_widget_encodings.py --validate

Usage:
    python validate_widget_encodings.py [--snapshot | --validate | --check]
    
Options:
    --snapshot  Save current state as baseline (run before editing)
    --validate  Compare current state against baseline (run after editing)  
    --check     Just check for column mismatches (default, no baseline comparison)
"""

import json
import re
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Set, List, Tuple


def get_query_columns(query: str) -> Set[str]:
    """Extract column names from SELECT clause.
    
    Handles:
    - SELECT col AS alias → returns 'alias'
    - SELECT table.col → returns 'col'
    - SELECT col → returns 'col'
    - SELECT FUNC(col) AS alias → returns 'alias'
    """
    if not query:
        return set()
    
    cols = set()
    
    # Match "AS column_name" patterns (most reliable)
    cols.update(re.findall(r'\s+AS\s+(\w+)', query, re.IGNORECASE))
    
    # Match direct column references in SELECT (before FROM)
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
    if select_match:
        select_part = select_match.group(1)
        for part in select_part.split(','):
            part = part.strip()
            # If it has AS, skip (already handled above)
            if ' AS ' in part.upper():
                continue
            # Get the last identifier (handles table.column patterns)
            words = re.findall(r'\b(\w+)\b', part)
            if words:
                cols.add(words[-1])
    
    return cols


def get_widget_fields(widget: dict) -> Set[str]:
    """Extract all field references from widget encodings."""
    fields = set()
    spec = widget.get('spec', {})
    encodings = spec.get('encodings', {})
    
    for enc_name, enc_value in encodings.items():
        if isinstance(enc_value, dict) and 'fieldName' in enc_value:
            fields.add(enc_value['fieldName'])
    
    return fields


def get_widget_title(widget: dict) -> str:
    """Get widget title for display."""
    spec = widget.get('spec', {})
    frame = spec.get('frame', {})
    return frame.get('title', widget.get('name', 'Unknown'))


def analyze_dashboard(dashboard_path: Path) -> Dict:
    """Analyze a dashboard and return widget-query mapping."""
    with open(dashboard_path) as f:
        dashboard = json.load(f)
    
    # Build dataset name → columns mapping
    dataset_columns = {}
    for ds in dashboard.get('datasets', []):
        name = ds.get('name', '')
        query = ds.get('query', '')
        dataset_columns[name] = get_query_columns(query)
    
    # Analyze each widget
    results = {
        'file': str(dashboard_path),
        'pages': len(dashboard.get('pages', [])),
        'datasets': len(dashboard.get('datasets', [])),
        'widgets': [],
        'mismatches': []
    }
    
    for page in dashboard.get('pages', []):
        page_name = page.get('displayName', page.get('name', ''))
        
        for item in page.get('layout', []):
            widget = item.get('widget', {})
            widget_name = widget.get('name', '')
            widget_title = get_widget_title(widget)
            widget_fields = get_widget_fields(widget)
            
            for q in widget.get('queries', []):
                ds_name = q.get('query', {}).get('datasetName', '')
                if ds_name:
                    query_cols = dataset_columns.get(ds_name, set())
                    missing = widget_fields - query_cols
                    
                    widget_info = {
                        'page': page_name,
                        'widget': widget_name,
                        'title': widget_title,
                        'dataset': ds_name,
                        'widget_expects': sorted(widget_fields),
                        'query_returns': sorted(query_cols)
                    }
                    results['widgets'].append(widget_info)
                    
                    if missing:
                        widget_info['missing'] = sorted(missing)
                        results['mismatches'].append(widget_info)
    
    return results


def generate_fingerprint(results: Dict) -> str:
    """Generate a fingerprint hash of widget-column mappings."""
    # Create stable representation
    mapping = []
    for w in sorted(results['widgets'], key=lambda x: (x['page'], x['widget'])):
        mapping.append(f"{w['widget']}:{w['dataset']}:{','.join(w['widget_expects'])}")
    
    content = '\n'.join(mapping)
    return hashlib.md5(content.encode()).hexdigest()[:12]


def save_snapshot(results: Dict, output_path: Path):
    """Save current state as baseline."""
    snapshot = {
        'fingerprint': generate_fingerprint(results),
        'widget_count': len(results['widgets']),
        'widgets': results['widgets']
    }
    
    with open(output_path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"✅ Snapshot saved to {output_path}")
    print(f"   Fingerprint: {snapshot['fingerprint']}")
    print(f"   Widgets: {snapshot['widget_count']}")


def compare_with_baseline(results: Dict, baseline_path: Path) -> List[Dict]:
    """Compare current state with baseline and report regressions."""
    if not baseline_path.exists():
        print(f"⚠️ No baseline found at {baseline_path}")
        print("   Run with --snapshot first to create baseline")
        return []
    
    with open(baseline_path) as f:
        baseline = json.load(f)
    
    current_fingerprint = generate_fingerprint(results)
    
    print(f"📊 Comparing against baseline:")
    print(f"   Baseline fingerprint: {baseline['fingerprint']}")
    print(f"   Current fingerprint:  {current_fingerprint}")
    
    if current_fingerprint == baseline['fingerprint']:
        print("✅ No changes detected - encodings match baseline")
        return []
    
    # Find differences
    baseline_widgets = {w['widget']: w for w in baseline['widgets']}
    current_widgets = {w['widget']: w for w in results['widgets']}
    
    regressions = []
    
    # Check for changed encodings
    for widget_name, current in current_widgets.items():
        if widget_name in baseline_widgets:
            baseline_w = baseline_widgets[widget_name]
            
            if current['widget_expects'] != baseline_w['widget_expects']:
                regressions.append({
                    'type': 'encoding_changed',
                    'widget': widget_name,
                    'before': baseline_w['widget_expects'],
                    'after': current['widget_expects']
                })
            
            if current['dataset'] != baseline_w['dataset']:
                regressions.append({
                    'type': 'dataset_changed',
                    'widget': widget_name,
                    'before': baseline_w['dataset'],
                    'after': current['dataset']
                })
    
    # Check for removed widgets
    for widget_name in baseline_widgets:
        if widget_name not in current_widgets:
            regressions.append({
                'type': 'widget_removed',
                'widget': widget_name
            })
    
    # Check for new widgets
    for widget_name in current_widgets:
        if widget_name not in baseline_widgets:
            regressions.append({
                'type': 'widget_added',
                'widget': widget_name
            })
    
    return regressions


def main():
    parser = argparse.ArgumentParser(description='Validate dashboard widget encodings')
    parser.add_argument('--snapshot', action='store_true', help='Save current state as baseline')
    parser.add_argument('--validate', action='store_true', help='Compare against baseline')
    parser.add_argument('--check', action='store_true', help='Just check for mismatches (default)')
    parser.add_argument('--dashboard', type=str, default='unified.lvdash.json', 
                       help='Dashboard file to analyze')
    
    args = parser.parse_args()
    
    # Default to --check if no action specified
    if not (args.snapshot or args.validate):
        args.check = True
    
    dashboard_path = Path(__file__).parent / args.dashboard
    baseline_path = dashboard_path.with_suffix('.baseline.json')
    
    print(f"\n{'='*70}")
    print("🔍 Dashboard Widget Encoding Validator")
    print(f"{'='*70}\n")
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard not found: {dashboard_path}")
        return 1
    
    results = analyze_dashboard(dashboard_path)
    
    print(f"📊 Analyzed: {dashboard_path.name}")
    print(f"   Pages: {results['pages']}")
    print(f"   Datasets: {results['datasets']}")
    print(f"   Widgets: {len(results['widgets'])}\n")
    
    # Always check for mismatches
    if results['mismatches']:
        print(f"❌ Found {len(results['mismatches'])} column mismatches:\n")
        for m in results['mismatches']:
            print(f"   Page: {m['page']}")
            print(f"   Widget: {m['widget']} ({m['title']})")
            print(f"   Dataset: {m['dataset']}")
            print(f"   Widget expects: {m['widget_expects']}")
            print(f"   Query returns: {m['query_returns']}")
            print(f"   ❌ Missing: {m.get('missing', [])}\n")
        
        if not args.snapshot:
            return 1
    else:
        print("✅ All widget encodings match query columns!\n")
    
    # Handle snapshot mode
    if args.snapshot:
        save_snapshot(results, baseline_path)
    
    # Handle validate mode
    if args.validate:
        regressions = compare_with_baseline(results, baseline_path)
        
        if regressions:
            print(f"\n⚠️ Found {len(regressions)} changes from baseline:\n")
            for r in regressions:
                if r['type'] == 'encoding_changed':
                    print(f"   Widget '{r['widget']}' encoding changed:")
                    print(f"     Before: {r['before']}")
                    print(f"     After:  {r['after']}")
                elif r['type'] == 'dataset_changed':
                    print(f"   Widget '{r['widget']}' dataset changed:")
                    print(f"     Before: {r['before']}")
                    print(f"     After:  {r['after']}")
                elif r['type'] == 'widget_removed':
                    print(f"   Widget '{r['widget']}' was REMOVED")
                elif r['type'] == 'widget_added':
                    print(f"   Widget '{r['widget']}' was ADDED")
                print()
            
            return 1
        else:
            print("\n✅ No regressions detected!")
    
    return 0


if __name__ == '__main__':
    exit(main())


