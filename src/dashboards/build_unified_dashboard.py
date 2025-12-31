"""
Build Unified Dashboard
========================

Consolidates individual dashboard JSON files into a single unified
Health Monitor dashboard with rationalized pages from each domain.

ARCHITECTURE:
- Each domain dashboard (cost_management, job_reliability, etc.) is enriched 
  with full ML, Monitoring, TVFs, and Metric Views (up to 100 datasets each)
- The unified dashboard selects ONLY the OVERVIEW PAGE from each domain
- This keeps the unified dashboard under 100 datasets while providing 
  a comprehensive executive summary

Users can drill down to individual domain dashboards for full detail.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


def load_dashboard_json(file_path: Path) -> Dict[str, Any]:
    """Load a dashboard JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def should_exclude_dataset(dataset_name: str) -> bool:
    """
    Check if a dataset should be excluded to stay under the 100 dataset limit.
    
    Excludes only ML placeholder datasets until inference pipeline runs.
    Monitoring datasets are now properly integrated and should NOT be excluded.
    """
    # Only exclude ML placeholder datasets until inference tables are created
    if 'ds_ml_' in dataset_name:
        return True
    return False


def widget_references_excluded_dataset(widget: Dict) -> bool:
    """Check if a widget references an excluded dataset."""
    queries = widget.get('queries', [])
    for query in queries:
        if 'query' in query and 'datasetName' in query['query']:
            dataset_name = query['query']['datasetName']
            if should_exclude_dataset(dataset_name):
                return True
    return False


def should_exclude_widget(widget: Dict) -> bool:
    """
    Check if a widget should be excluded for the unified dashboard.
    
    Only excludes ML widgets until inference pipelines populate the tables.
    Monitoring widgets are now properly integrated.
    """
    widget_name = widget.get('name', '')
    
    # Only exclude ML-related widgets until inference tables exist
    ml_patterns = [
        'table_ml_', '_ml_failure', '_ml_sla', '_ml_anomaly', '_ml_capacity',
        '_ml_optimization', '_ml_threat', '_ml_query', '_ml_cost', '_ml_commitment',
        '_ml_pipeline', '_ml_retry', '_ml_incident', '_ml_rightsizing', '_ml_cache',
        '_ml_exfiltration', '_ml_privilege', '_ml_regression', '_ml_warehouse',
        '_ml_dbr_risk', '_ml_duration', 'chart_ml_'
    ]
    
    for pattern in ml_patterns:
        if pattern in widget_name:
            return True
    
    if widget_references_excluded_dataset(widget):
        return True
    
    return False


def get_datasets_used_in_page(page: Dict) -> Set[str]:
    """Extract all dataset names referenced by widgets in a page."""
    datasets_used = set()
    
    for item in page.get('layout', []):
        if 'widget' not in item:
            continue
        widget = item['widget']
        for query in widget.get('queries', []):
            if 'query' in query and 'datasetName' in query['query']:
                datasets_used.add(query['query']['datasetName'])
    
    return datasets_used


def prefix_dataset_names(datasets: List[Dict], prefix: str, used_datasets: Optional[Set[str]] = None) -> List[Dict]:
    """
    Add prefix to dataset names to avoid conflicts.
    Optionally filter to only include datasets that are actually used.
    """
    prefixed = []
    for ds in datasets:
        name = ds.get('name', '')
        
        # Skip ML placeholder datasets
        if should_exclude_dataset(name):
            continue
        
        # If filtering by used datasets, skip unused ones
        if used_datasets is not None and name not in used_datasets:
            continue
        
        new_ds = ds.copy()
        new_ds['name'] = f"{prefix}_{name}"
        # Ensure displayName exists
        if 'displayName' not in new_ds or not new_ds['displayName']:
            new_ds['displayName'] = new_ds['name']
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
    """Add prefix to widget names and update dataset references, filtering excluded widgets."""
    filtered_layout = []
    for item in layout:
        if 'widget' in item:
            widget = item['widget']
            # Skip widgets that reference excluded datasets
            if should_exclude_widget(widget):
                continue
            widget['name'] = f"{prefix}_{widget['name']}"
            update_widget_dataset_refs(widget, prefix)
            filtered_layout.append(item)
        else:
            filtered_layout.append(item)
    return filtered_layout


def select_overview_page(dashboard: Dict[str, Any]) -> Optional[Dict]:
    """
    Select the main overview page from a multi-page dashboard.
    For enriched dashboards, this is typically the first page with 'overview' 
    or the primary summary page.
    """
    pages = dashboard.get('pages', [])
    if not pages:
        return None
    
    # Priority order for selecting pages
    priority_keywords = ['overview', 'summary', 'executive', 'main', 'kpi']
    
    # Try to find a page with priority keywords
    for keyword in priority_keywords:
        for page in pages:
            page_name = page.get('name', '').lower()
            display_name = page.get('displayName', '').lower()
            if keyword in page_name or keyword in display_name:
                return page
    
    # Default to first page
    return pages[0]


def create_page_from_dashboard(
    dashboard: Dict[str, Any],
    page_name: str,
    display_name: str,
    prefix: str
) -> Dict[str, Any]:
    """Create a unified dashboard page from a domain dashboard's overview page."""
    
    # For enriched dashboards with multiple pages, select the overview page
    source_page = select_overview_page(dashboard)
    
    if source_page is None:
        return {
            "name": page_name,
            "displayName": display_name,
            "layout": []
        }
    
    return {
        "name": page_name,
        "displayName": display_name,
        "layout": prefix_widget_names(source_page.get('layout', []).copy(), prefix)
    }


def build_unified_dashboard(dashboards_dir: Path) -> Dict[str, Any]:
    """
    Build a unified dashboard from individual dashboard files.
    
    RATIONALIZATION STRATEGY:
    - Select only the OVERVIEW PAGE from each enriched domain dashboard
    - Only include datasets that are actually referenced by those pages
    - This keeps total datasets under 100 while providing executive summary
    
    Returns a complete dashboard JSON with rationalized pages merged.
    """
    
    # Dashboard configuration: (file_name, page_name, display_name, prefix)
    # Each domain dashboard has full enrichment (ML, Monitoring, TVFs)
    # We only include the overview/summary page in the unified dashboard
    DASHBOARD_CONFIG = [
        # 📊 Executive Summary
        ("executive_overview.lvdash.json", "page_exec", "📊 Executive Summary", "exec"),
        
        # 💰 Cost Domain
        ("cost_management.lvdash.json", "page_cost", "💰 Cost Management", "cost"),
        ("commit_tracking.lvdash.json", "page_commit", "💰 Commit Tracking", "commit"),
        
        # 🔄 Reliability Domain
        ("job_reliability.lvdash.json", "page_reliability", "🔄 Job Reliability", "rel"),
        ("job_optimization.lvdash.json", "page_optimization", "🔄 Job Optimization", "opt"),
        
        # ⚡ Performance Domain
        ("query_performance.lvdash.json", "page_query", "⚡ Query Performance", "query"),
        ("cluster_utilization.lvdash.json", "page_cluster", "⚡ Cluster Utilization", "cluster"),
        ("dbr_migration.lvdash.json", "page_dbr", "⚡ DBR Migration", "dbr"),
        
        # 🔒 Security & Governance Domain
        ("security_audit.lvdash.json", "page_security", "🔒 Security Audit", "sec"),
        ("governance_hub.lvdash.json", "page_governance", "🔒 Governance Hub", "gov"),
        
        # ✅ Quality Domain
        ("table_health.lvdash.json", "page_quality", "✅ Table Health", "qual"),
    ]
    
    # Initialize unified dashboard
    unified = {
        "displayName": "Databricks Health Monitor",
        "warehouse_id": "${warehouse_id}",
        "pages": [],
        "datasets": []
    }
    
    total_datasets = 0
    DATASET_LIMIT = 95  # Leave room for global filter datasets
    
    # Process each dashboard
    for file_name, page_name, display_name, prefix in DASHBOARD_CONFIG:
        file_path = dashboards_dir / file_name
        
        if not file_path.exists():
            print(f"  ⚠️ {file_name} not found, skipping...")
            continue
        
        try:
            dashboard = load_dashboard_json(file_path)
            
            # Create page from dashboard's overview page
            page = create_page_from_dashboard(
                dashboard, page_name, display_name, prefix
            )
            
            # Get datasets actually used by this page
            original_dataset_names = get_datasets_used_in_page(page)
            # Convert prefixed names back to original for filtering
            used_datasets = {name.replace(f"{prefix}_", "") for name in original_dataset_names}
            
            # Get datasets used by the prefixed page widgets
            prefixed_page = page
            used_in_page = set()
            for item in prefixed_page.get('layout', []):
                if 'widget' in item:
                    for query in item['widget'].get('queries', []):
                        if 'query' in query and 'datasetName' in query['query']:
                            # Get the unprefixed name for matching
                            prefixed_name = query['query']['datasetName']
                            unprefixed_name = prefixed_name.replace(f"{prefix}_", "")
                            used_in_page.add(unprefixed_name)
            
            # Filter datasets to only those used by the overview page
            if 'datasets' in dashboard:
                prefixed_datasets = prefix_dataset_names(
                    dashboard['datasets'], 
                    prefix, 
                    used_datasets=used_in_page
                )
                
                # Check if we're within limits
                if total_datasets + len(prefixed_datasets) > DATASET_LIMIT:
                    print(f"  ⚠️ {file_name}: Would exceed {DATASET_LIMIT} datasets, trimming...")
                    remaining = DATASET_LIMIT - total_datasets
                    prefixed_datasets = prefixed_datasets[:remaining]
                
                unified['datasets'].extend(prefixed_datasets)
                total_datasets += len(prefixed_datasets)
            
            unified['pages'].append(page)
            print(f"  ✓ Added {display_name} ({len(page.get('layout', []))} widgets, {len(used_in_page)} datasets)")
            
        except Exception as e:
            print(f"  ✗ Error processing {file_name}: {str(e)}")
    
    print(f"\n  📊 Total datasets so far: {total_datasets}")
    
    return unified


def add_global_filters_page(unified: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a Global Filters page for cross-dashboard filtering.
    """
    
    global_filters_page = {
        "name": "page_global_filters",
        "displayName": "🔧 Global Filters",
        "pageType": "PAGE_TYPE_GLOBAL_FILTERS",
        "layout": [
            # Time Window - Date Range Picker
            {
                "widget": {
                    "name": "filter_time_window",
                    "queries": [],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-date-range-picker",
                        "encodings": {"fields": []},
                        "selection": {
                            "defaultSelection": {
                                "range": {
                                    "dataType": "DATE",
                                    "min": {"value": "now-90d/d"},
                                    "max": {"value": "now/d"}
                                }
                            }
                        },
                        "frame": {"showTitle": True, "title": "Time Window"}
                    }
                },
                "position": {"x": 0, "y": 0, "width": 1, "height": 2}
            },
            # Workspace Filter
            {
                "widget": {
                    "name": "filter_workspace",
                    "queries": [{
                        "name": "workspace_query",
                        "query": {
                            "datasetName": "gf_ds_workspaces",
                            "fields": [
                                {"name": "workspace_name", "expression": "`workspace_name`"},
                                {"name": "workspace_name_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                            ],
                            "disaggregated": False
                        }
                    }],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-multi-select",
                        "encodings": {
                            "fields": [{
                                "displayName": "Workspace",
                                "fieldName": "workspace_name",
                                "queryName": "workspace_query"
                            }]
                        },
                        "selection": {"defaultSelection": {"values": {"dataType": "STRING", "values": [{"value": "all"}]}}},
                        "frame": {"showTitle": True, "title": "Workspace"}
                    }
                },
                "position": {"x": 0, "y": 2, "width": 1, "height": 2}
            },
            # SKU Type Filter
            {
                "widget": {
                    "name": "filter_sku_type",
                    "queries": [{
                        "name": "sku_query",
                        "query": {
                            "datasetName": "gf_ds_sku_types",
                            "fields": [
                                {"name": "sku_category", "expression": "`sku_category`"},
                                {"name": "sku_category_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                            ],
                            "disaggregated": False
                        }
                    }],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-multi-select",
                        "encodings": {
                            "fields": [{
                                "displayName": "SKU Type",
                                "fieldName": "sku_category",
                                "queryName": "sku_query"
                            }]
                        },
                        "selection": {"defaultSelection": {"values": {"dataType": "STRING", "values": [{"value": "all"}]}}},
                        "frame": {"showTitle": True, "title": "SKU Type"}
                    }
                },
                "position": {"x": 0, "y": 4, "width": 1, "height": 2}
            },
            # Date Grouping
            {
                "widget": {
                    "name": "filter_date_group",
                    "queries": [{
                        "name": "date_group_query",
                        "query": {
                            "datasetName": "gf_ds_date_groupings",
                            "fields": [
                                {"name": "time_key", "expression": "`time_key`"},
                                {"name": "time_key_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                            ],
                            "disaggregated": False
                        }
                    }],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-single-select",
                        "encodings": {
                            "fields": [{
                                "displayName": "Group By",
                                "fieldName": "time_key",
                                "queryName": "date_group_query"
                            }]
                        },
                        "selection": {"defaultSelection": {"values": {"dataType": "STRING", "values": [{"value": "Day"}]}}},
                        "frame": {"showTitle": True, "title": "Dates By"}
                    }
                },
                "position": {"x": 0, "y": 6, "width": 1, "height": 2}
            },
            # Compute Type
            {
                "widget": {
                    "name": "filter_compute_type",
                    "queries": [{
                        "name": "compute_query",
                        "query": {
                            "datasetName": "gf_ds_compute_types",
                            "fields": [
                                {"name": "compute_type", "expression": "`compute_type`"},
                                {"name": "compute_type_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                            ],
                            "disaggregated": False
                        }
                    }],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-single-select",
                        "encodings": {
                            "fields": [{
                                "displayName": "Compute Type",
                                "fieldName": "compute_type",
                                "queryName": "compute_query"
                            }]
                        },
                        "selection": {"defaultSelection": {"values": {"dataType": "STRING", "values": [{"value": "All"}]}}},
                        "frame": {"showTitle": True, "title": "Compute Type"}
                    }
                },
                "position": {"x": 0, "y": 8, "width": 1, "height": 2}
            },
            # Job Status
            {
                "widget": {
                    "name": "filter_job_status",
                    "queries": [{
                        "name": "status_query",
                        "query": {
                            "datasetName": "gf_ds_job_status",
                            "fields": [
                                {"name": "status", "expression": "`status`"},
                                {"name": "status_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                            ],
                            "disaggregated": False
                        }
                    }],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-single-select",
                        "encodings": {
                            "fields": [{
                                "displayName": "Job Status",
                                "fieldName": "status",
                                "queryName": "status_query"
                            }]
                        },
                        "selection": {"defaultSelection": {"values": {"dataType": "STRING", "values": [{"value": "All"}]}}},
                        "frame": {"showTitle": True, "title": "Job Status"}
                    }
                },
                "position": {"x": 0, "y": 10, "width": 1, "height": 2}
            }
        ]
    }
    
    # Global filter datasets
    global_filter_datasets = [
        {"name": "gf_ds_workspaces", "displayName": "Global Filter - Workspaces", 
         "query": "SELECT 'all' AS workspace_name UNION ALL SELECT DISTINCT COALESCE(workspace_name, CONCAT('ID: ', workspace_id)) AS workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name"},
        {"name": "gf_ds_sku_types", "displayName": "Global Filter - SKU Types",
         "query": "SELECT 'all' AS sku_category UNION ALL SELECT DISTINCT billing_origin_product AS sku_category FROM ${catalog}.${gold_schema}.fact_usage WHERE billing_origin_product IS NOT NULL ORDER BY sku_category"},
        {"name": "gf_ds_date_groupings", "displayName": "Global Filter - Date Groupings",
         "query": "SELECT EXPLODE(ARRAY('Day', 'Week', 'Month', 'Quarter', 'Year')) AS time_key"},
        {"name": "gf_ds_compute_types", "displayName": "Global Filter - Compute Types",
         "query": "SELECT EXPLODE(ARRAY('All', 'Serverless', 'Classic')) AS compute_type"},
        {"name": "gf_ds_job_status", "displayName": "Global Filter - Job Status",
         "query": "SELECT EXPLODE(ARRAY('All', 'Success', 'Failed', 'Running')) AS status"}
    ]
    
    # Insert filters page at the beginning
    unified['pages'].insert(0, global_filters_page)
    unified['datasets'].extend(global_filter_datasets)
    
    print(f"  ✓ Added Global Filters page with 6 filter controls (5 datasets)")
    
    return unified


def save_unified_dashboard(unified: Dict[str, Any], output_path: Path):
    """Save the unified dashboard to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(unified, f, indent=2)
    print(f"\n✓ Unified dashboard saved to: {output_path}")


def main():
    """Main entry point for building the unified dashboard."""
    
    script_dir = Path(__file__).parent
    dashboards_dir = script_dir
    
    print("=" * 70)
    print("Building Unified Health Monitor Dashboard")
    print("=" * 70)
    print(f"\nSource directory: {dashboards_dir}")
    print("\nRATIONALIZATION STRATEGY:")
    print("  - Each domain dashboard is fully enriched (ML, Monitoring, TVFs)")
    print("  - Unified dashboard includes only OVERVIEW pages from each domain")
    print("  - This keeps unified dashboard under 100 datasets")
    print("  - Users drill down to domain dashboards for full detail")
    print()
    
    # Build unified dashboard
    unified = build_unified_dashboard(dashboards_dir)
    
    # Add global filters
    unified = add_global_filters_page(unified)
    
    # Save to file
    output_path = dashboards_dir / "health_monitor_unified.lvdash.json"
    save_unified_dashboard(unified, output_path)
    
    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    print(f"  📄 Pages: {len(unified['pages'])}")
    print(f"  📊 Datasets: {len(unified['datasets'])} (limit: 100)")
    print(f"  📁 Output: {output_path.name}")
    
    if len(unified['datasets']) > 100:
        print(f"\n  ⚠️ WARNING: Dataset count ({len(unified['datasets'])}) exceeds limit of 100!")
    else:
        print(f"\n  ✅ Dashboard within limits ({len(unified['datasets'])}/100 datasets)")
    
    return unified


if __name__ == "__main__":
    main()
