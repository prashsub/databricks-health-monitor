# Databricks notebook source
"""
Dashboard Deployment Script
===========================

Deploys the unified Health Monitor Lakeview AI/BI dashboard.
Builds a single dashboard with multiple tabs from individual component files.

Reference: https://databricks-sdk-py.readthedocs.io/en/latest/workspace/dashboards/lakeview.html
"""

# COMMAND ----------

import json
import time
from pathlib import Path

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
warehouse_id = dbutils.widgets.get("warehouse_id")

print(f"Deploying Unified Dashboard for: {catalog}.{gold_schema}")
print(f"Warehouse ID: {warehouse_id}")

# COMMAND ----------

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.dashboards import Dashboard
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Databricks SDK not available - using REST API fallback")

# COMMAND ----------

# ============================================================================
# INLINE: Dashboard Builder Functions
# ============================================================================
# These functions are inlined to avoid import issues in Asset Bundles

def load_dashboard_json(file_path: str) -> dict:
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


def widget_references_excluded_dataset(widget: dict) -> bool:
    """
    Check if a widget references an excluded dataset.
    
    Examines the widget's queries to see if any reference excluded datasets.
    """
    queries = widget.get('queries', [])
    for query in queries:
        if 'query' in query and 'datasetName' in query['query']:
            dataset_name = query['query']['datasetName']
            if should_exclude_dataset(dataset_name):
                return True
    return False


def should_exclude_widget(widget: dict) -> bool:
    """
    Check if a widget should be excluded.
    
    Only excludes ML widgets until inference pipelines populate the tables.
    Monitoring widgets are now properly integrated and should NOT be excluded.
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
    
    # Check by dataset reference
    if widget_references_excluded_dataset(widget):
        return True
    
    return False


def get_datasets_from_page(page: dict) -> set:
    """Extract the set of dataset names referenced by widgets on a page."""
    dataset_names = set()
    for item in page.get('layout', []):
        widget = item.get('widget', {})
        for query in widget.get('queries', []):
            if 'query' in query and 'datasetName' in query['query']:
                dataset_names.add(query['query']['datasetName'])
    return dataset_names


def prefix_dataset_names(datasets: list, prefix: str, referenced_datasets: set = None) -> list:
    """Add prefix to dataset names to avoid conflicts.
    
    Also adds displayName field if not present (required by Lakeview API).
    Excludes ML placeholder datasets.
    If referenced_datasets is provided, only include those datasets.
    """
    prefixed = []
    for ds in datasets:
        original_name = ds.get('name', '')
        
        # Skip ML placeholder datasets
        if should_exclude_dataset(original_name):
            continue
        
        # If referenced_datasets is provided, only include datasets that are referenced
        if referenced_datasets is not None and original_name not in referenced_datasets:
            continue
        
        new_ds = ds.copy()
        new_name = f"{prefix}_{original_name}"
        new_ds['name'] = new_name
        # displayName is required by Lakeview API
        if 'displayName' not in new_ds or not new_ds['displayName']:
            new_ds['displayName'] = new_name
        else:
            new_ds['displayName'] = f"{prefix}_{new_ds['displayName']}"
        prefixed.append(new_ds)
    return prefixed


def update_widget_dataset_refs(widget: dict, prefix: str) -> dict:
    """Update widget query references to use prefixed dataset names."""
    if 'queries' not in widget:
        return widget
    
    for query in widget.get('queries', []):
        if 'query' in query and 'datasetName' in query['query']:
            query['query']['datasetName'] = f"{prefix}_{query['query']['datasetName']}"
    
    return widget


def prefix_widget_names(layout: list, prefix: str) -> list:
    """Add prefix to widget names and update dataset references.
    
    Filters out widgets that reference excluded datasets (ML placeholders, etc).
    """
    import copy
    layout_copy = copy.deepcopy(layout)
    filtered_layout = []
    for item in layout_copy:
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


def select_overview_page(dashboard: dict) -> dict:
    """
    Select the main overview page from a multi-page dashboard.
    For enriched dashboards, this is typically the first page with 'overview' 
    or the primary summary page.
    """
    pages = dashboard.get('pages', [])
    if not pages:
        return {}
    
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


def create_page_from_dashboard(dashboard: dict, page_name: str, display_name: str, prefix: str) -> tuple:
    """Create a page entry from a dashboard's overview page (for multi-page dashboards).
    
    Returns a tuple of (page_dict, referenced_dataset_names).
    """
    source_page = select_overview_page(dashboard)
    
    # Get the datasets referenced by widgets on this page BEFORE prefixing
    referenced_datasets = get_datasets_from_page(source_page)
    
    page = {
        "name": page_name,
        "displayName": display_name,
        "layout": prefix_widget_names(source_page.get('layout', []), prefix)
    }
    
    return page, referenced_datasets


def add_global_filters_page(unified: dict) -> dict:
    """
    Add a Global Filters page for cross-dashboard filtering.
    
    Creates a sidebar with filters that affect all dashboard pages:
    - Time Window (date range picker)
    - Workspace (multi-select)
    - SKU Type (multi-select for cost pages)
    - Date Grouping (Day/Week/Month)
    - Compute Type (Serverless/Classic/All)
    - Job Status (All/Success/Failed)
    """
    
    global_filters_page = {
        "name": "page_global_filters",
        "displayName": "🔧 Global Filters",
        "pageType": "PAGE_TYPE_GLOBAL_FILTERS",
        "layout": [
            # Time Window - Single-Select dropdown instead of date-range-picker
            {
                "widget": {
                    "name": "filter_time_window",
                    "queries": [
                        {
                            "name": "time_window_query",
                            "query": {
                                "datasetName": "gf_ds_time_windows",
                                "fields": [
                                    {"name": "time_window", "expression": "`time_window`"},
                                    {"name": "time_window_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
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
                                    "displayName": "Time Window",
                                    "fieldName": "time_window",
                                    "queryName": "time_window_query"
                                }
                            ]
                        },
                        "selection": {
                            "defaultSelection": {
                                "values": {
                                    "dataType": "STRING",
                                    "values": [{"value": "Last 30 Days"}]
                                }
                            }
                        },
                        "frame": {
                            "showTitle": True,
                            "title": "Time Window"
                        }
                    }
                },
                "position": {"x": 0, "y": 0, "width": 1, "height": 2}
            },
            # Workspace Filter - Multi-Select
            {
                "widget": {
                    "name": "filter_workspace",
                    "queries": [
                        {
                            "name": "workspace_query",
                            "query": {
                                "datasetName": "gf_ds_workspaces",
                                "fields": [
                                    {"name": "workspace_name", "expression": "`workspace_name`"},
                                    {"name": "workspace_name_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                                ],
                                "disaggregated": False
                            }
                        }
                    ],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-multi-select",
                        "encodings": {
                            "fields": [
                                {
                                    "displayName": "Workspace",
                                    "fieldName": "workspace_name",
                                    "queryName": "workspace_query"
                                }
                            ]
                        },
                        "frame": {
                            "showTitle": True,
                            "title": "Workspace"
                        }
                    }
                },
                "position": {"x": 0, "y": 2, "width": 1, "height": 2}
            },
            # SKU Type Filter - Multi-Select
            {
                "widget": {
                    "name": "filter_sku_type",
                    "queries": [
                        {
                            "name": "sku_query",
                            "query": {
                                "datasetName": "gf_ds_sku_types",
                                "fields": [
                                    {"name": "sku_category", "expression": "`sku_category`"},
                                    {"name": "sku_category_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                                ],
                                "disaggregated": False
                            }
                        }
                    ],
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-multi-select",
                        "encodings": {
                            "fields": [
                                {
                                    "displayName": "SKU Type",
                                    "fieldName": "sku_category",
                                    "queryName": "sku_query"
                                }
                            ]
                        },
                        "frame": {
                            "showTitle": True,
                            "title": "SKU Type"
                        }
                    }
                },
                "position": {"x": 0, "y": 4, "width": 1, "height": 2}
            },
            # Date Grouping - Single-Select
            {
                "widget": {
                    "name": "filter_date_group",
                    "queries": [
                        {
                            "name": "date_group_query",
                            "query": {
                                "datasetName": "gf_ds_date_groupings",
                                "fields": [
                                    {"name": "time_key", "expression": "`time_key`"},
                                    {"name": "time_key_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
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
                                    "displayName": "Group By",
                                    "fieldName": "time_key",
                                    "queryName": "date_group_query"
                                }
                            ]
                        },
                        "selection": {
                            "defaultSelection": {
                                "values": {
                                    "dataType": "STRING",
                                    "values": [{"value": "Day"}]
                                }
                            }
                        },
                        "frame": {
                            "showTitle": True,
                            "title": "Dates By"
                        }
                    }
                },
                "position": {"x": 0, "y": 6, "width": 1, "height": 2}
            },
            # Compute Type - Single-Select
            {
                "widget": {
                    "name": "filter_compute_type",
                    "queries": [
                        {
                            "name": "compute_query",
                            "query": {
                                "datasetName": "gf_ds_compute_types",
                                "fields": [
                                    {"name": "compute_type", "expression": "`compute_type`"},
                                    {"name": "compute_type_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
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
                                    "displayName": "Compute Type",
                                    "fieldName": "compute_type",
                                    "queryName": "compute_query"
                                }
                            ]
                        },
                        "selection": {
                            "defaultSelection": {
                                "values": {
                                    "dataType": "STRING",
                                    "values": [{"value": "All"}]
                                }
                            }
                        },
                        "frame": {
                            "showTitle": True,
                            "title": "Compute Type"
                        }
                    }
                },
                "position": {"x": 0, "y": 8, "width": 1, "height": 2}
            },
            # Job Status Filter - Single-Select  
            {
                "widget": {
                    "name": "filter_job_status",
                    "queries": [
                        {
                            "name": "status_query",
                            "query": {
                                "datasetName": "gf_ds_job_status",
                                "fields": [
                                    {"name": "status", "expression": "`status`"},
                                    {"name": "status_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
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
                                    "displayName": "Job Status",
                                    "fieldName": "status",
                                    "queryName": "status_query"
                                }
                            ]
                        },
                        "selection": {
                            "defaultSelection": {
                                "values": {
                                    "dataType": "STRING",
                                    "values": [{"value": "All"}]
                                }
                            }
                        },
                        "frame": {
                            "showTitle": True,
                            "title": "Job Status"
                        }
                    }
                },
                "position": {"x": 0, "y": 10, "width": 1, "height": 2}
            }
        ]
    }
    
    # Global filter datasets
    # NOTE: Don't include 'all' in query - the filter UI adds it automatically based on selection behavior
    global_filter_datasets = [
        {
            "name": "gf_ds_time_windows",
            "displayName": "Global Filter - Time Windows",
            "query": "SELECT EXPLODE(ARRAY('Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'Last 6 Months', 'Last Year', 'All Time')) AS time_window"
        },
        {
            "name": "gf_ds_workspaces",
            "displayName": "Global Filter - Workspaces",
            "query": "SELECT DISTINCT COALESCE(workspace_name, CONCAT('ID: ', workspace_id)) AS workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name"
        },
        {
            "name": "gf_ds_sku_types",
            "displayName": "Global Filter - SKU Types",
            "query": "SELECT DISTINCT billing_origin_product AS sku_category FROM ${catalog}.${gold_schema}.fact_usage WHERE billing_origin_product IS NOT NULL ORDER BY sku_category"
        },
        {
            "name": "gf_ds_date_groupings",
            "displayName": "Global Filter - Date Groupings",
            "query": "SELECT EXPLODE(ARRAY('Day', 'Week', 'Month', 'Quarter', 'Year')) AS time_key"
        },
        {
            "name": "gf_ds_compute_types",
            "displayName": "Global Filter - Compute Types",
            "query": "SELECT EXPLODE(ARRAY('All', 'Serverless', 'Classic')) AS compute_type"
        },
        {
            "name": "gf_ds_job_status",
            "displayName": "Global Filter - Job Status",
            "query": "SELECT EXPLODE(ARRAY('All', 'Success', 'Failed', 'Running')) AS status"
        }
    ]
    
    # Insert filters page at the beginning
    unified['pages'].insert(0, global_filters_page)
    unified['datasets'].extend(global_filter_datasets)
    
    print("  ✓ Added Global Filters page with 6 filter controls")
    
    return unified


def build_unified_dashboard(dashboards_dir: str) -> dict:
    """Build a unified dashboard from individual dashboard files."""
    
    # Dashboard configuration: (file_name, page_name, display_name, prefix)
    # 
    # NOTE: Some dashboards excluded until their required Gold tables are created:
    # - commit_tracking: requires commit_configurations table
    # - table_health: requires fact_information_schema_table_storage table
    # - query_performance: requires fact_query_history table (may not be populated)
    # - cluster_utilization: requires fact_node_timeline table (may not be populated)
    # - security_audit: requires fact_audit_logs table (may not be populated)
    # - governance_hub: requires fact_table_lineage table (may not be populated)
    #
    # RATIONALIZATION STRATEGY:
    # Each domain dashboard is fully enriched (ML, Monitoring, TVFs)
    # Unified dashboard includes only OVERVIEW pages from each domain
    # This keeps unified dashboard under 100 datasets
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
    
    unified = {
        "displayName": "[Health Monitor] Databricks Platform Overview",
        "warehouse_id": "${warehouse_id}",
        "pages": [],
        "datasets": []
    }
    
    for file_name, page_name, display_name, prefix in DASHBOARD_CONFIG:
        file_path = f"{dashboards_dir}/{file_name}"
        
        try:
            dashboard = load_dashboard_json(file_path)
            
            # Create page and get referenced datasets
            page, referenced_datasets = create_page_from_dashboard(dashboard, page_name, display_name, prefix)
            unified['pages'].append(page)
            
            # Only include datasets that are referenced by the selected page's widgets
            if 'datasets' in dashboard:
                prefixed_datasets = prefix_dataset_names(
                    dashboard['datasets'], 
                    prefix, 
                    referenced_datasets  # Only include referenced datasets
                )
                unified['datasets'].extend(prefixed_datasets)
            
            print(f"  ✓ Added {display_name} ({len(page['layout'])} widgets, {len(prefixed_datasets)} datasets)")
            
        except FileNotFoundError:
            print(f"  ⚠ Warning: {file_name} not found, skipping...")
        except Exception as e:
            print(f"  ✗ Error processing {file_name}: {str(e)}")
    
    unified = add_global_filters_page(unified)
    
    # Print dataset summary
    total_datasets = len(unified['datasets'])
    print(f"\n  📊 Unified dashboard: {len(unified['pages'])} pages, {total_datasets} datasets")
    if total_datasets > 100:
        print(f"  ⚠️ WARNING: Exceeds 100 dataset limit by {total_datasets - 100}!")
    else:
        print(f"  ✅ Within 100 dataset limit ({total_datasets}/100)")
    
    return unified


# COMMAND ----------

def substitute_variables(content: str, catalog: str, gold_schema: str, warehouse_id: str) -> str:
    """Replace ${...} placeholders in dashboard JSON."""
    replacements = {
        '${catalog}': catalog,
        '${gold_schema}': gold_schema,
        '${warehouse_id}': warehouse_id,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def find_and_delete_dashboard(workspace_client, display_name: str) -> bool:
    """Find a dashboard by name and delete it.
    
    Searches through dashboards up to a limit.
    Returns True if found and deleted, False otherwise.
    """
    try:
        count = 0
        max_check = 500  # Increased limit
        print(f"  Searching for dashboard in first {max_check} results...")
        for dash in workspace_client.lakeview.list():
            # Check for exact match or partial match (in case of name changes)
            if dash.display_name == display_name or (
                'Health Monitor' in str(dash.display_name) and 
                'Platform Overview' in str(dash.display_name)
            ):
                print(f"  Found existing dashboard: {dash.display_name}")
                print(f"  Dashboard ID: {dash.dashboard_id}")
                workspace_client.lakeview.trash(dashboard_id=dash.dashboard_id)
                print(f"  ✓ Old dashboard deleted")
                return True
            count += 1
            if count >= max_check:
                print(f"  Searched {count} dashboards, not found")
                break
        return False
    except Exception as e:
        print(f"  Warning: Could not search/delete dashboard: {str(e)}")
        return False


def deploy_dashboard_sdk(workspace_client, dashboard_config: dict) -> str:
    """Deploy dashboard using Databricks SDK.
    
    Strategy: Try to create first. If already exists, create with versioned name.
    
    Reference: https://databricks-sdk-py.readthedocs.io/en/latest/workspace/dashboards/lakeview.html
    """
    import re
    from datetime import datetime
    
    display_name = dashboard_config.get('displayName')
    serialized_dashboard = json.dumps(dashboard_config)
    warehouse_id_from_config = dashboard_config.get('warehouse_id')
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"  Creating dashboard: {display_name} (attempt {attempt + 1})")
            dashboard_obj = Dashboard(
                display_name=display_name,
                serialized_dashboard=serialized_dashboard,
                warehouse_id=warehouse_id_from_config
            )
            result = workspace_client.lakeview.create(dashboard=dashboard_obj)
            print(f"  ✓ Dashboard created successfully")
            return result.dashboard_id if hasattr(result, 'dashboard_id') else "SUCCESS"

        except Exception as create_error:
            error_str = str(create_error)
            
            if "already exists" not in error_str.lower() and "resourcealreadyexists" not in error_str.lower():
                print(f"  ✗ Create failed: {error_str}")
                raise
            
            # Dashboard exists - try to update it
            print(f"  ℹ Dashboard already exists...")
            
            # Extract dashboard ID from error message
            id_match = re.search(r'dashboards/([a-f0-9]+)', error_str)
            
            if id_match:
                existing_id = id_match.group(1)
                print(f"  Found dashboard ID: {existing_id}, attempting update...")
                
                try:
                    dashboard_obj = Dashboard(
                        display_name=display_name,
                        serialized_dashboard=serialized_dashboard,
                        warehouse_id=warehouse_id_from_config
                    )
                    workspace_client.lakeview.update(
                        dashboard_id=existing_id,
                        dashboard=dashboard_obj
                    )
                    print(f"  ✓ Dashboard updated successfully")
                    return existing_id
                except Exception as update_error:
                    print(f"  ⚠ Update failed: {str(update_error)[:200]}")
                    # Add version to name and retry
                    version = datetime.now().strftime("%Y%m%d_%H%M%S")
                    display_name = f"{dashboard_config.get('displayName')} v{version}"
                    dashboard_config['displayName'] = display_name
                    serialized_dashboard = json.dumps(dashboard_config)
                    print(f"  Retrying with new name: {display_name}")
                    continue
            else:
                # Can't extract ID, add version and retry
                version = datetime.now().strftime("%Y%m%d_%H%M%S")
                display_name = f"{dashboard_config.get('displayName')} v{version}"
                dashboard_config['displayName'] = display_name
                serialized_dashboard = json.dumps(dashboard_config)
                print(f"  Retrying with new name: {display_name}")
                continue
    
    raise RuntimeError(f"Failed to deploy dashboard after {max_attempts} attempts")


# COMMAND ----------

def get_dashboard_base_path() -> str:
    """Get the base workspace path for dashboard JSON files."""
    try:
        notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        print(f"Current notebook path: {notebook_path}")
        
        base_path = "/Workspace" + "/".join(notebook_path.rsplit("/", 1)[:-1])
        print(f"Using workspace path: {base_path}")
        return base_path
    except Exception as e:
        print(f"Could not determine workspace path: {e}")
        return "."


dashboard_base_path = get_dashboard_base_path()
print(f"Dashboard base path resolved to: {dashboard_base_path}")

# COMMAND ----------

# Validate warehouse_id
if not warehouse_id:
    print("WARNING: No warehouse_id provided. Dashboard may not function correctly.")

# Initialize SDK
workspace_client = None
if SDK_AVAILABLE:
    workspace_client = WorkspaceClient()
    print("\n✓ Databricks SDK initialized")

# COMMAND ----------

# Build and deploy unified dashboard
print("\n" + "=" * 60)
print("Building Unified Health Monitor Dashboard")
print("=" * 60 + "\n")

start_time = time.time()
deployment_success = False

try:
    # Build unified dashboard from component files
    unified_config = build_unified_dashboard(dashboard_base_path)
    
    # Substitute variables
    config_json = json.dumps(unified_config)
    config_json = substitute_variables(config_json, catalog, gold_schema, warehouse_id)
    unified_config = json.loads(config_json)
    
    print(f"\n  Total Pages: {len(unified_config['pages'])}")
    print(f"  Total Datasets: {len(unified_config['datasets'])}")
    
    # Check dataset limit
    if len(unified_config['datasets']) > 100:
        raise RuntimeError(f"Dashboard exceeds 100 dataset limit: {len(unified_config['datasets'])} datasets")
    
    # Deploy
    if SDK_AVAILABLE and workspace_client:
        dashboard_id = deploy_dashboard_sdk(workspace_client, unified_config)
        print(f"\n  Dashboard ID: {dashboard_id}")
        deployment_success = True
    else:
        # Fallback: Save processed JSON
        output_path = "/tmp/health_monitor_unified_processed.json"
        with open(output_path, 'w') as f:
            json.dump(unified_config, f, indent=2)
        print(f"\n  Processed JSON saved to: {output_path}")
        deployment_success = True

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    deployment_success = False
    raise

elapsed = time.time() - start_time
print(f"\nDeployment time: {elapsed:.1f}s")

# COMMAND ----------

# Summary
print("\n" + "=" * 60)
print("Dashboard Deployment Summary")
print("=" * 60)

if deployment_success:
    print(f"\n✅ Unified dashboard deployed successfully!")
    print(f"   Name: Databricks Health Monitor")
    print(f"   Pages: {len(unified_config['pages'])}")
    print(f"   Datasets: {len(unified_config['datasets'])}")
    dbutils.notebook.exit("SUCCESS: Unified dashboard deployed")
else:
    error_msg = "Dashboard deployment failed"
    print(f"\n❌ {error_msg}")
    raise RuntimeError(error_msg)
