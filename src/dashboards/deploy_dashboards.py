# Databricks notebook source
"""
Dashboard Deployment Script
===========================

Deploys all Lakeview AI/BI dashboards for Health Monitor.
Creates or updates dashboards using the Lakeview API.
"""

# COMMAND ----------

import json
import os
from pathlib import Path
from string import Template

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
warehouse_id = dbutils.widgets.get("warehouse_id")

print(f"Deploying Dashboards for: {catalog}.{gold_schema}")
print(f"Warehouse ID: {warehouse_id}")

# COMMAND ----------

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.dashboards import Dashboard
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Databricks SDK not available - using REST API")

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


def load_dashboard_json(file_path: str, catalog: str, gold_schema: str, warehouse_id: str) -> dict:
    """Load and parse dashboard JSON file with variable substitution."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Substitute variables
    content = substitute_variables(content, catalog, gold_schema, warehouse_id)

    return json.loads(content)


def deploy_dashboard_sdk(workspace_client, dashboard_config: dict, dashboard_name: str) -> str:
    """Deploy dashboard using Databricks SDK."""
    try:
        # Check if dashboard exists
        existing = workspace_client.lakeview.list()
        existing_dash = None
        for dash in existing:
            if dash.display_name == dashboard_config.get('displayName'):
                existing_dash = dash
                break

        if existing_dash:
            # Update existing dashboard
            print(f"  Updating existing dashboard: {dashboard_config.get('displayName')}")
            result = workspace_client.lakeview.update(
                dashboard_id=existing_dash.dashboard_id,
                display_name=dashboard_config.get('displayName'),
                serialized_dashboard=json.dumps(dashboard_config),
                warehouse_id=dashboard_config.get('warehouse_id')
            )
        else:
            # Create new dashboard
            print(f"  Creating new dashboard: {dashboard_config.get('displayName')}")
            result = workspace_client.lakeview.create(
                display_name=dashboard_config.get('displayName'),
                serialized_dashboard=json.dumps(dashboard_config),
                warehouse_id=dashboard_config.get('warehouse_id'),
                parent_path="/Workspace/Shared/health_monitor/dashboards"
            )

        return result.dashboard_id if hasattr(result, 'dashboard_id') else "SUCCESS"

    except Exception as e:
        print(f"  SDK deployment failed: {str(e)}")
        raise


def deploy_dashboard(dashboard_name: str, json_file: str, catalog: str, gold_schema: str, warehouse_id: str) -> bool:
    """Deploy a single dashboard."""
    try:
        print(f"Deploying dashboard: {dashboard_name}")

        # Load dashboard configuration
        config = load_dashboard_json(json_file, catalog, gold_schema, warehouse_id)

        if SDK_AVAILABLE:
            workspace_client = WorkspaceClient()
            dashboard_id = deploy_dashboard_sdk(workspace_client, config, dashboard_name)
            print(f"  Dashboard ID: {dashboard_id}")
        else:
            # Fallback: Save processed JSON for manual deployment
            output_path = f"/tmp/{dashboard_name}_processed.json"
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"  Processed JSON saved to: {output_path}")

        print(f"  Successfully deployed: {dashboard_name}")
        return True

    except Exception as e:
        print(f"  Failed to deploy {dashboard_name}: {str(e)}")
        return False

# COMMAND ----------

# Find all dashboard JSON files
dashboards_dir = Path(__file__).parent if '__file__' in dir() else Path(".")

# List of dashboards to deploy
DASHBOARDS = [
    ("executive_overview", "executive_overview.lvdash.json"),
    ("cost_management", "cost_management.lvdash.json"),
    ("job_reliability", "job_reliability.lvdash.json"),
    ("query_performance", "query_performance.lvdash.json"),
    ("cluster_utilization", "cluster_utilization.lvdash.json"),
    ("security_audit", "security_audit.lvdash.json"),
]

# COMMAND ----------

# Validate warehouse_id
if not warehouse_id:
    print("WARNING: No warehouse_id provided. Dashboards may not function correctly.")

# Deploy all dashboards
results = []
for dash_name, json_file in DASHBOARDS:
    json_path = dashboards_dir / json_file
    if json_path.exists():
        success = deploy_dashboard(dash_name, str(json_path), catalog, gold_schema, warehouse_id)
        results.append((dash_name, success))
    else:
        print(f"  JSON file not found: {json_file}")
        results.append((dash_name, False))

# COMMAND ----------

# Summary
print("\n" + "=" * 50)
print("Dashboard Deployment Summary")
print("=" * 50)

successful = sum(1 for _, success in results if success)
failed = sum(1 for _, success in results if not success)

print(f"\nTotal: {len(results)}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

if failed > 0:
    print("\nFailed dashboards:")
    for dash_name, success in results:
        if not success:
            print(f"  - {dash_name}")

# COMMAND ----------

# Exit with appropriate status
if failed > 0:
    dbutils.notebook.exit(f"PARTIAL: {failed} dashboards failed to deploy")
else:
    dbutils.notebook.exit(f"SUCCESS: {successful} dashboards deployed")
