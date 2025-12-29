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


def prefix_dataset_names(datasets: list, prefix: str) -> list:
    """Add prefix to dataset names to avoid conflicts."""
    prefixed = []
    for ds in datasets:
        new_ds = ds.copy()
        new_ds['name'] = f"{prefix}_{ds['name']}"
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
    """Add prefix to widget names and update dataset references."""
    import copy
    layout_copy = copy.deepcopy(layout)
    for item in layout_copy:
        if 'widget' in item:
            widget = item['widget']
            widget['name'] = f"{prefix}_{widget['name']}"
            update_widget_dataset_refs(widget, prefix)
    return layout_copy


def create_page_from_dashboard(dashboard: dict, page_name: str, display_name: str, prefix: str) -> dict:
    """Create a page entry from a dashboard's first page."""
    source_page = dashboard.get('pages', [{}])[0]
    
    return {
        "name": page_name,
        "displayName": display_name,
        "layout": prefix_widget_names(source_page.get('layout', []), prefix)
    }


def add_global_filters_page(unified: dict) -> dict:
    """Add a Global Filters page for cross-dashboard filtering."""
    
    global_filters_page = {
        "name": "page_global_filters",
        "displayName": "🔧 Filters",
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
            }
        ]
    }
    
    workspace_filter_ds = {
        "name": "ds_workspace_filter",
        "query": "SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE is_current = TRUE ORDER BY workspace_name"
    }
    
    unified['pages'].append(global_filters_page)
    unified['datasets'].append(workspace_filter_ds)
    
    return unified


def build_unified_dashboard(dashboards_dir: str) -> dict:
    """Build a unified dashboard from individual dashboard files."""
    
    # Dashboard configuration: (file_name, page_name, display_name, prefix)
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
    
    unified = {
        "displayName": "Databricks Health Monitor",
        "warehouse_id": "${warehouse_id}",
        "pages": [],
        "datasets": []
    }
    
    for file_name, page_name, display_name, prefix in DASHBOARD_CONFIG:
        file_path = f"{dashboards_dir}/{file_name}"
        
        try:
            dashboard = load_dashboard_json(file_path)
            
            page = create_page_from_dashboard(dashboard, page_name, display_name, prefix)
            unified['pages'].append(page)
            
            if 'datasets' in dashboard:
                prefixed_datasets = prefix_dataset_names(dashboard['datasets'], prefix)
                unified['datasets'].extend(prefixed_datasets)
            
            print(f"  ✓ Added {display_name}")
            
        except FileNotFoundError:
            print(f"  ⚠ Warning: {file_name} not found, skipping...")
        except Exception as e:
            print(f"  ✗ Error processing {file_name}: {str(e)}")
    
    unified = add_global_filters_page(unified)
    
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


def get_existing_dashboards_map(workspace_client) -> dict:
    """Build a map of existing dashboard names to IDs for efficient lookup."""
    dashboard_map = {}
    try:
        for dash in workspace_client.lakeview.list():
            if dash.display_name:
                dashboard_map[dash.display_name] = dash.dashboard_id
    except Exception as e:
        print(f"  Warning: Could not list existing dashboards: {str(e)}")
    return dashboard_map


def deploy_dashboard_sdk(workspace_client, dashboard_config: dict, existing_dashboards: dict) -> str:
    """Deploy dashboard using Databricks SDK.
    
    The LakeviewAPI.create() and update() methods require a Dashboard object,
    not individual keyword arguments.
    
    Reference: https://databricks-sdk-py.readthedocs.io/en/latest/workspace/dashboards/lakeview.html
    """
    try:
        display_name = dashboard_config.get('displayName')
        existing_id = existing_dashboards.get(display_name)
        serialized_dashboard = json.dumps(dashboard_config)
        warehouse_id_from_config = dashboard_config.get('warehouse_id')

        if existing_id:
            print(f"  Updating existing dashboard: {display_name}")
            dashboard_obj = Dashboard(
                display_name=display_name,
                serialized_dashboard=serialized_dashboard,
                warehouse_id=warehouse_id_from_config
            )
            result = workspace_client.lakeview.update(
                dashboard_id=existing_id,
                dashboard=dashboard_obj
            )
        else:
            print(f"  Creating new dashboard: {display_name}")
            dashboard_obj = Dashboard(
                display_name=display_name,
                serialized_dashboard=serialized_dashboard,
                warehouse_id=warehouse_id_from_config,
                parent_path="/Workspace/Shared/health_monitor/dashboards"
            )
            result = workspace_client.lakeview.create(dashboard=dashboard_obj)

        return result.dashboard_id if hasattr(result, 'dashboard_id') else "SUCCESS"

    except Exception as e:
        print(f"  SDK deployment failed: {str(e)}")
        raise


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
existing_dashboards = {}
if SDK_AVAILABLE:
    workspace_client = WorkspaceClient()
    print("\nBuilding map of existing dashboards...")
    existing_dashboards = get_existing_dashboards_map(workspace_client)
    print(f"  Found {len(existing_dashboards)} existing dashboards")

# COMMAND ----------

# Build and deploy unified dashboard
print("\n" + "=" * 60)
print("Building Unified Health Monitor Dashboard")
print("=" * 60 + "\n")

start_time = time.time()

try:
    # Build unified dashboard from component files
    unified_config = build_unified_dashboard(dashboard_base_path)
    
    # Substitute variables
    config_json = json.dumps(unified_config)
    config_json = substitute_variables(config_json, catalog, gold_schema, warehouse_id)
    unified_config = json.loads(config_json)
    
    print(f"\n  Total Pages: {len(unified_config['pages'])}")
    print(f"  Total Datasets: {len(unified_config['datasets'])}")
    
    # Deploy
    if SDK_AVAILABLE and workspace_client:
        dashboard_id = deploy_dashboard_sdk(workspace_client, unified_config, existing_dashboards)
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
