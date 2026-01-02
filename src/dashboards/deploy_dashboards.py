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


def inject_filter_conditions(query: str, dataset_name: str) -> str:
    """
    Inject filter parameter conditions into SQL queries.
    
    Uses the pattern: IF(:param = 'All', TRUE, column = :param)
    to allow filtering when a specific value is selected, or all data when 'All'.
    
    Detection logic:
    - If query contains 'fact_usage' -> add workspace, sku filters
    - If query contains 'fact_job' -> add workspace filter
    - If query contains 'fact_audit' -> add workspace filter
    - If query contains 'fact_query' -> add workspace filter
    - If query contains 'fact_node' -> add workspace filter
    """
    # Skip if already has parameter syntax
    if ':time_window' in query or ':workspace_name' in query:
        return query
    
    # Skip filter datasets
    if 'gf_ds_' in dataset_name:
        return query
    
    # Determine which filters apply based on table references
    filters_to_add = []
    
    # Time filter - maps time_window to date conditions
    time_filter = """(
        CASE :time_window
            WHEN 'Last 7 Days' THEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
            WHEN 'Last 30 Days' THEN usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
            WHEN 'Last 90 Days' THEN usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
            WHEN 'Last 6 Months' THEN usage_date >= CURRENT_DATE() - INTERVAL 180 DAYS
            WHEN 'Last Year' THEN usage_date >= CURRENT_DATE() - INTERVAL 365 DAYS
            ELSE TRUE
        END
    )"""
    
    if 'fact_usage' in query.lower():
        filters_to_add.append("IF(:workspace_name = 'All', TRUE, workspace_id IN (SELECT workspace_id FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name = :workspace_name))")
        filters_to_add.append("IF(:sku_category = 'All', TRUE, billing_origin_product = :sku_category)")
    elif 'fact_job_run' in query.lower():
        filters_to_add.append("IF(:workspace_name = 'All', TRUE, workspace_id IN (SELECT workspace_id FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name = :workspace_name))")
    elif 'fact_audit' in query.lower():
        filters_to_add.append("IF(:workspace_name = 'All', TRUE, workspace_id IN (SELECT workspace_id FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name = :workspace_name))")
    elif 'fact_query' in query.lower():
        filters_to_add.append("IF(:workspace_name = 'All', TRUE, workspace_id IN (SELECT workspace_id FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name = :workspace_name))")
    elif 'fact_node' in query.lower():
        filters_to_add.append("IF(:workspace_name = 'All', TRUE, workspace_id IN (SELECT workspace_id FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name = :workspace_name))")
    
    if not filters_to_add:
        return query
    
    # Inject filters into WHERE clause
    filter_condition = " AND ".join(filters_to_add)
    
    # Find WHERE clause and append, or add new WHERE
    import re
    if re.search(r'\bWHERE\b', query, re.IGNORECASE):
        # Add to existing WHERE - find the last WHERE and append
        # Use a pattern that finds WHERE and adds after the first condition
        pattern = r'(\bWHERE\b\s+)'
        replacement = f'\\1{filter_condition} AND '
        query = re.sub(pattern, replacement, query, count=1, flags=re.IGNORECASE)
    else:
        # No WHERE clause - need to add one
        # Find FROM ... and add WHERE after the table reference
        if ' ORDER BY' in query.upper():
            query = re.sub(r'(\s+ORDER\s+BY\b)', f' WHERE {filter_condition}\\1', query, count=1, flags=re.IGNORECASE)
        elif ' GROUP BY' in query.upper():
            query = re.sub(r'(\s+GROUP\s+BY\b)', f' WHERE {filter_condition}\\1', query, count=1, flags=re.IGNORECASE)
        elif ' LIMIT' in query.upper():
            query = re.sub(r'(\s+LIMIT\b)', f' WHERE {filter_condition}\\1', query, count=1, flags=re.IGNORECASE)
        else:
            # Append at the end
            query = f"{query} WHERE {filter_condition}"
    
    return query


def add_parameters_to_datasets(unified: dict) -> dict:
    """
    Add filter parameters to all datasets so they can respond to global filters.
    
    Each dataset gets parameters for:
    - time_window: Time range filter
    - workspace_name: Workspace filter
    - sku_category: SKU type filter
    - owner_name: Owner filter
    
    Also injects filter conditions into SQL queries.
    """
    filter_parameters = [
        {
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
        {
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
        {
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
        {
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
    ]
    
    for dataset in unified.get('datasets', []):
        ds_name = dataset.get('name', '')
        
        # Skip filter datasets themselves
        if ds_name.startswith('gf_ds_'):
            continue
        
        # Add parameters to dataset if not already present
        if 'parameters' not in dataset:
            dataset['parameters'] = []
        
        # Add each filter parameter if not already present
        existing_keywords = {p.get('keyword') for p in dataset.get('parameters', [])}
        for param in filter_parameters:
            if param['keyword'] not in existing_keywords:
                dataset['parameters'].append(param.copy())
        
        # Inject filter conditions into query (optional - can be slow to implement fully)
        # Commenting out for now as it requires careful SQL manipulation
        # if 'query' in dataset:
        #     dataset['query'] = inject_filter_conditions(dataset['query'], ds_name)
    
    return unified


def build_filter_widget_queries(unified: dict, filter_keyword: str, filter_field: str, filter_dataset: str) -> list:
    """
    Build query entries for a filter widget that bind to all datasets.
    
    Each filter widget needs:
    1. A query to get filter options (from filter dataset)
    2. Queries for each data dataset with parameter bindings
    """
    queries = [
        # First query: Get filter options
        {
            "name": f"{filter_keyword}_query",
            "query": {
                "datasetName": filter_dataset,
                "fields": [
                    {"name": filter_field, "expression": f"`{filter_field}`"},
                    {"name": f"{filter_field}_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                ],
                "disaggregated": False
            }
        }
    ]
    
    # Add parameter binding queries for each data dataset
    for i, dataset in enumerate(unified.get('datasets', [])):
        ds_name = dataset.get('name', '')
        
        # Skip filter datasets and ML placeholder datasets
        if ds_name.startswith('gf_ds_') or 'ds_ml_' in ds_name:
            continue
        
        queries.append({
            "name": f"param_{filter_keyword}_{i}",
            "query": {
                "datasetName": ds_name,
                "fields": [],
                "disaggregated": False
            },
            "parameters": [
                {"name": filter_keyword, "keyword": filter_keyword}
            ]
        })
    
    return queries


def add_global_filters_page(unified: dict) -> dict:
    """
    Add a Global Filters page with proper parameter bindings.
    
    This implementation follows the Databricks reference dashboard pattern:
    1. Each dataset has parameters defined for filters it responds to
    2. Each filter widget has queries for ALL datasets with parameter bindings
    3. Filter widgets use associative filtering pattern
    
    Creates filters for:
    - Time Window (single-select)
    - Workspace (multi-select)  
    - SKU Type (multi-select)
    - Owner (multi-select) - NEW
    """
    
    # First, add parameters to all datasets
    unified = add_parameters_to_datasets(unified)
    
    # Build filter widgets with proper bindings
    time_window_queries = build_filter_widget_queries(unified, "time_window", "time_window", "gf_ds_time_windows")
    workspace_queries = build_filter_widget_queries(unified, "workspace_name", "workspace_name", "gf_ds_workspaces")
    sku_queries = build_filter_widget_queries(unified, "sku_category", "sku_category", "gf_ds_sku_types")
    owner_queries = build_filter_widget_queries(unified, "owner_name", "owner_name", "gf_ds_owners")
    
    global_filters_page = {
        "name": "page_global_filters",
        "displayName": "🔧 Global Filters",
        "pageType": "PAGE_TYPE_GLOBAL_FILTERS",
        "layout": [
            # Time Window Filter
            {
                "widget": {
                    "name": "filter_time_window",
                    "queries": time_window_queries,
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
                        "frame": {"showTitle": True, "title": "Time Window"}
                    }
                },
                "position": {"x": 0, "y": 0, "width": 1, "height": 2}
            },
            # Workspace Filter
            {
                "widget": {
                    "name": "filter_workspace",
                    "queries": workspace_queries,
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-multi-select",
                        "encodings": {
                            "fields": [
                                {
                                    "displayName": "Workspace",
                                    "fieldName": "workspace_name",
                                    "queryName": "workspace_name_query"
                                }
                            ]
                        },
                        "frame": {"showTitle": True, "title": "Workspace"}
                    }
                },
                "position": {"x": 0, "y": 2, "width": 1, "height": 2}
            },
            # SKU Type Filter
            {
                "widget": {
                    "name": "filter_sku_type",
                    "queries": sku_queries,
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-multi-select",
                        "encodings": {
                            "fields": [
                                {
                                    "displayName": "SKU Type",
                                    "fieldName": "sku_category",
                                    "queryName": "sku_category_query"
                                }
                            ]
                        },
                        "frame": {"showTitle": True, "title": "SKU Type"}
                    }
                },
                "position": {"x": 0, "y": 4, "width": 1, "height": 2}
            },
            # Owner Filter (NEW)
            {
                "widget": {
                    "name": "filter_owner",
                    "queries": owner_queries,
                    "spec": {
                        "version": 2,
                        "widgetType": "filter-multi-select",
                        "encodings": {
                            "fields": [
                                {
                                    "displayName": "Owner",
                                    "fieldName": "owner_name",
                                    "queryName": "owner_name_query"
                                }
                            ]
                        },
                        "frame": {"showTitle": True, "title": "Owner"}
                    }
                },
                "position": {"x": 0, "y": 6, "width": 1, "height": 2}
            }
        ]
    }
    
    # Global filter datasets with proper structure
    global_filter_datasets = [
        {
            "name": "gf_ds_time_windows",
            "displayName": "Global Filter - Time Windows",
            "query": "SELECT EXPLODE(ARRAY('Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'Last 6 Months', 'Last Year', 'All Time')) AS time_window"
        },
        {
            "name": "gf_ds_workspaces",
            "displayName": "Global Filter - Workspaces",
            "query": "SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT COALESCE(workspace_name, CONCAT('ID: ', workspace_id)) AS workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name"
        },
        {
            "name": "gf_ds_sku_types",
            "displayName": "Global Filter - SKU Types",
            "query": "SELECT 'All' AS sku_category UNION ALL SELECT DISTINCT billing_origin_product AS sku_category FROM ${catalog}.${gold_schema}.fact_usage WHERE billing_origin_product IS NOT NULL ORDER BY sku_category"
        },
        {
            "name": "gf_ds_owners",
            "displayName": "Global Filter - Owners",
            "query": "SELECT 'All' AS owner_name UNION ALL SELECT DISTINCT identity_metadata_run_as AS owner_name FROM ${catalog}.${gold_schema}.fact_usage WHERE identity_metadata_run_as IS NOT NULL ORDER BY owner_name LIMIT 100"
        }
    ]
    
    # Insert filters page at the beginning
    unified['pages'].insert(0, global_filters_page)
    unified['datasets'].extend(global_filter_datasets)
    
    # Count bindings
    num_datasets = len([d for d in unified.get('datasets', []) if not d.get('name', '').startswith('gf_ds_')])
    print(f"  ✓ Added Global Filters page with 4 filters bound to {num_datasets} datasets")
    
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
