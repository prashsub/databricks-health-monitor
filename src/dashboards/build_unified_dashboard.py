"""
Build Unified Dashboard
========================

Consolidates all individual dashboard JSON files into a single unified
Health Monitor dashboard with multiple tabs (pages).

This script is called at deployment time to generate the unified dashboard.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def load_dashboard_json(file_path: Path) -> Dict[str, Any]:
    """Load a dashboard JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def prefix_dataset_names(datasets: List[Dict], prefix: str) -> List[Dict]:
    """Add prefix to dataset names to avoid conflicts."""
    prefixed = []
    for ds in datasets:
        new_ds = ds.copy()
        new_ds['name'] = f"{prefix}_{ds['name']}"
        prefixed.append(new_ds)
    return prefixed


def update_widget_dataset_refs(widget: Dict, prefix: str) -> Dict:
    """Update widget query references to use prefixed dataset names."""
    if 'queries' not in widget:
        return widget
    
    for query in widget.get('queries', []):
        if 'query' in query and 'datasetName' in query['query']:
            query['query']['datasetName'] = f"{prefix}_{query['query']['datasetName']}"
    
    return widget


def prefix_widget_names(layout: List[Dict], prefix: str) -> List[Dict]:
    """Add prefix to widget names and update dataset references."""
    for item in layout:
        if 'widget' in item:
            widget = item['widget']
            widget['name'] = f"{prefix}_{widget['name']}"
            update_widget_dataset_refs(widget, prefix)
    return layout


def create_page_from_dashboard(
    dashboard: Dict[str, Any],
    page_name: str,
    display_name: str,
    prefix: str
) -> Dict[str, Any]:
    """Create a page entry from a dashboard's first page."""
    source_page = dashboard.get('pages', [{}])[0]
    
    return {
        "name": page_name,
        "displayName": display_name,
        "layout": prefix_widget_names(source_page.get('layout', []).copy(), prefix)
    }


def build_unified_dashboard(dashboards_dir: Path) -> Dict[str, Any]:
    """
    Build a unified dashboard from individual dashboard files.
    
    Returns a complete dashboard JSON with all pages merged.
    """
    
    # Dashboard configuration: (file_name, page_name, display_name, prefix, emoji)
    DASHBOARD_CONFIG = [
        # 💰 Cost Agent
        ("executive_overview.lvdash.json", "page_exec", "🏠 Executive Overview", "exec"),
        ("cost_management.lvdash.json", "page_cost", "💰 Cost Management", "cost"),
        ("commit_tracking.lvdash.json", "page_commit", "💰 Commit Tracking", "commit"),
        
        # 🔄 Reliability Agent
        ("job_reliability.lvdash.json", "page_reliability", "🔄 Job Reliability", "rel"),
        ("job_optimization.lvdash.json", "page_optimization", "🔄 Job Optimization", "opt"),
        
        # ⚡ Performance Agent
        ("query_performance.lvdash.json", "page_query", "⚡ Query Performance", "query"),
        ("cluster_utilization.lvdash.json", "page_cluster", "⚡ Cluster Utilization", "cluster"),
        ("dbr_migration.lvdash.json", "page_dbr", "⚡ DBR Migration", "dbr"),
        
        # 🔒 Security Agent
        ("security_audit.lvdash.json", "page_security", "🔒 Security Audit", "sec"),
        ("governance_hub.lvdash.json", "page_governance", "🔒 Governance Hub", "gov"),
        
        # ✅ Quality Agent
        ("table_health.lvdash.json", "page_quality", "✅ Table Health", "qual"),
    ]
    
    # Initialize unified dashboard
    unified = {
        "displayName": "Databricks Health Monitor",
        "warehouse_id": "${warehouse_id}",
        "pages": [],
        "datasets": []
    }
    
    # Process each dashboard
    for file_name, page_name, display_name, prefix in DASHBOARD_CONFIG:
        file_path = dashboards_dir / file_name
        
        if not file_path.exists():
            print(f"  Warning: {file_name} not found, skipping...")
            continue
        
        try:
            dashboard = load_dashboard_json(file_path)
            
            # Create page from dashboard
            page = create_page_from_dashboard(
                dashboard, page_name, display_name, prefix
            )
            unified['pages'].append(page)
            
            # Add prefixed datasets
            if 'datasets' in dashboard:
                prefixed_datasets = prefix_dataset_names(dashboard['datasets'], prefix)
                unified['datasets'].extend(prefixed_datasets)
            
            print(f"  ✓ Added {display_name}")
            
        except Exception as e:
            print(f"  ✗ Error processing {file_name}: {str(e)}")
    
    return unified


def add_global_filters_page(unified: Dict[str, Any]) -> Dict[str, Any]:
    """Add a Global Filters page for cross-dashboard filtering."""
    
    global_filters_page = {
        "name": "page_global_filters",
        "displayName": "🔧 Filters",
        "pageType": "PAGE_TYPE_GLOBAL_FILTERS",
        "layout": [
            {
                "widget": {
                    "name": "filter_workspace",
                    "queries": [
                        {
                            "name": "main_query",
                            "query": {
                                "datasetName": "ds_workspace_filter",
                                "fields": [
                                    {"name": "workspace_name", "expression": "`workspace_name`"}
                                ],
                                "disaggregated": False
                            }
                        }
                    ],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-single-select",
                        "encodings": {
                            "fields": [
                                {
                                    "displayName": "Workspace",
                                    "fieldName": "workspace_name",
                                    "queryName": "main_query"
                                }
                            ]
                        },
                        "frame": {
                            "showTitle": True,
                            "title": "Workspace Filter"
                        }
                    }
                },
                "position": {"x": 0, "y": 0, "width": 3, "height": 2}
            },
            {
                "widget": {
                    "name": "filter_date_range",
                    "queries": [],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-date-range-picker",
                        "encodings": {},
                        "frame": {
                            "showTitle": True,
                            "title": "Date Range"
                        }
                    }
                },
                "position": {"x": 3, "y": 0, "width": 3, "height": 2}
            }
        ]
    }
    
    # Add workspace filter dataset
    workspace_filter_ds = {
        "name": "ds_workspace_filter",
        "query": "SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT workspace_name FROM ${catalog}.${gold_schema}.dim_workspace ORDER BY workspace_name"
    }
    
    # Insert filters page at the end
    unified['pages'].append(global_filters_page)
    unified['datasets'].append(workspace_filter_ds)
    
    return unified


def save_unified_dashboard(unified: Dict[str, Any], output_path: Path):
    """Save the unified dashboard to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(unified, f, indent=2)
    print(f"\n✓ Unified dashboard saved to: {output_path}")


def main():
    """Main entry point for building the unified dashboard."""
    
    # Determine the dashboards directory
    script_dir = Path(__file__).parent
    dashboards_dir = script_dir
    
    print("=" * 60)
    print("Building Unified Health Monitor Dashboard")
    print("=" * 60)
    print(f"\nSource directory: {dashboards_dir}\n")
    
    # Build unified dashboard
    unified = build_unified_dashboard(dashboards_dir)
    
    # Add global filters
    unified = add_global_filters_page(unified)
    
    # Save to file
    output_path = dashboards_dir / "health_monitor_unified.lvdash.json"
    save_unified_dashboard(unified, output_path)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print("=" * 60)
    print(f"  Pages: {len(unified['pages'])}")
    print(f"  Datasets: {len(unified['datasets'])}")
    print(f"  Output: {output_path.name}")
    
    return unified


if __name__ == "__main__":
    main()

