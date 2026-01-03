# Databricks notebook source
"""
Dashboard Deployment Script
===========================

Deploys the 6 Health Monitor Lakeview AI/BI dashboards:

1. Domain Dashboards (5):
   - cost.lvdash.json: Cost & Commitment (💰)
   - performance.lvdash.json: Performance (⚡)
   - reliability.lvdash.json: Reliability (🔄)
   - security.lvdash.json: Security (🔒)
   - quality.lvdash.json: Quality & Governance (✅)

2. Unified Dashboard (1):
   - unified.lvdash.json: Executive overviews from all domains (📊)

All dashboards are static JSON files - no runtime generation.
Fix SQL errors directly in the JSON files, then redeploy.

Parameters:
- catalog: Target Unity Catalog
- gold_schema: Gold layer schema name
- warehouse_id: SQL Warehouse ID for dashboard queries

Reference: https://databricks-sdk-py.readthedocs.io/en/latest/workspace/dashboards/lakeview.html
"""

# COMMAND ----------

import json
import re
from datetime import datetime
from pathlib import Path

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
    print("Databricks SDK not available")

# COMMAND ----------

# Dashboard files to deploy
DASHBOARDS = [
    ("cost.lvdash.json", "[Health Monitor] Cost & Commitment"),
    ("performance.lvdash.json", "[Health Monitor] Performance"),
    ("reliability.lvdash.json", "[Health Monitor] Reliability"),
    ("security.lvdash.json", "[Health Monitor] Security"),
    ("quality.lvdash.json", "[Health Monitor] Quality & Governance"),
    ("unified.lvdash.json", "[Health Monitor] Unified Dashboard"),
]

# COMMAND ----------

def substitute_variables(json_str: str, catalog: str, gold_schema: str, warehouse_id: str) -> str:
    """Replace variable placeholders with actual values."""
    json_str = json_str.replace('${catalog}', catalog)
    json_str = json_str.replace('${gold_schema}', gold_schema)
    json_str = json_str.replace('${warehouse_id}', warehouse_id)
    return json_str


def load_dashboard(file_path: str, catalog: str, gold_schema: str, warehouse_id: str) -> dict:
    """Load dashboard JSON and substitute variables."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    content = substitute_variables(content, catalog, gold_schema, warehouse_id)
    return json.loads(content)


def deploy_dashboard(workspace_client, dashboard_config: dict, display_name: str) -> str:
    """
    Deploy a dashboard using the SDK.
    
    Simple approach: Always create with timestamp suffix to avoid conflicts.
    """
    # Add timestamp to ensure unique name
    timestamp = datetime.now().strftime("%m%d_%H%M")
    unique_name = f"{display_name} ({timestamp})"
    
    dashboard_config['displayName'] = unique_name
    
    if not dashboard_config.get('warehouse_id') or dashboard_config.get('warehouse_id') == '${warehouse_id}':
        raise ValueError(f"warehouse_id not set for {display_name}")
    
    serialized_dashboard = json.dumps(dashboard_config)
    warehouse_id = dashboard_config.get('warehouse_id')
    
    # Log size info
    size_kb = len(serialized_dashboard) / 1024
    print(f"  Creating: {unique_name} (size: {size_kb:.1f} KB)")
    
    try:
        dashboard_obj = Dashboard(
            display_name=unique_name,
            serialized_dashboard=serialized_dashboard,
            warehouse_id=warehouse_id
        )
        result = workspace_client.lakeview.create(dashboard=dashboard_obj)
        print(f"  ✅ Created successfully")
        return result.dashboard_id if hasattr(result, 'dashboard_id') else "SUCCESS"
    except Exception as e:
        # Print detailed error info
        print(f"  ❌ SDK ERROR: {type(e).__name__}: {str(e)[:500]}")
        if hasattr(e, 'response'):
            print(f"  Response: {e.response}")
        if hasattr(e, 'error_code'):
            print(f"  Error code: {e.error_code}")
        raise

# COMMAND ----------

# Main deployment logic
print("\n" + "=" * 60)
print("DASHBOARD DEPLOYMENT")
print("=" * 60 + "\n")

# Get dashboard directory
try:
    dashboard_dir = Path("/Workspace/Users/prashanth.subrahmanyam@databricks.com/.bundle/databricks_health_monitor/dev/files/src/dashboards")
    if not dashboard_dir.exists():
        raise FileNotFoundError()
except:
    dashboard_dir = Path(".")

print(f"Dashboard directory: {dashboard_dir}")

# Initialize SDK client
if SDK_AVAILABLE:
    workspace_client = WorkspaceClient()
    print("SDK client initialized")
else:
    raise RuntimeError("Databricks SDK required for deployment")

# Deploy each dashboard
results = {}
for filename, display_name in DASHBOARDS:
    print(f"\n{'─' * 50}")
    print(f"📊 Deploying: {display_name}")
    print(f"   Source: {filename}")
    
    file_path = dashboard_dir / filename
    
    if not file_path.exists():
        print(f"   ⚠️ File not found, skipping")
        results[filename] = {"status": "SKIPPED", "reason": "File not found"}
        continue
    
    try:
        # Load and prepare dashboard
        dashboard_config = load_dashboard(str(file_path), catalog, gold_schema, warehouse_id)
        
        # Log dashboard size
        ds_count = len(dashboard_config.get('datasets', []))
        pg_count = len(dashboard_config.get('pages', []))
        print(f"   Loaded: {pg_count} pages, {ds_count} datasets")
        
        # Deploy
        dashboard_id = deploy_dashboard(workspace_client, dashboard_config, display_name)
        results[filename] = {"status": "SUCCESS", "id": dashboard_id}
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Failed: {error_msg[:500]}")
        # Log full error for debugging
        import traceback
        print(f"   Stack trace: {traceback.format_exc()[:500]}")
        results[filename] = {"status": "FAILED", "error": error_msg}

# COMMAND ----------

# Summary
print("\n" + "=" * 60)
print("DEPLOYMENT SUMMARY")
print("=" * 60 + "\n")

success_count = sum(1 for r in results.values() if r.get("status") == "SUCCESS")
failed_count = sum(1 for r in results.values() if r.get("status") == "FAILED")
skipped_count = sum(1 for r in results.values() if r.get("status") == "SKIPPED")

print(f"Total Dashboards: {len(DASHBOARDS)}")
print(f"  ✅ Deployed: {success_count}")
print(f"  ❌ Failed: {failed_count}")
print(f"  ⚠️ Skipped: {skipped_count}")

# List results for each dashboard
print("\n📊 Individual Results:")
for filename, result in results.items():
    status = result.get("status", "UNKNOWN")
    if status == "SUCCESS":
        print(f"  ✅ {filename}: {result.get('id', 'deployed')}")
    elif status == "FAILED":
        print(f"  ❌ {filename}: {result.get('error', 'Unknown error')[:150]}")
    elif status == "SKIPPED":
        print(f"  ⚠️ {filename}: {result.get('reason', 'Skipped')}")

if success_count == len(DASHBOARDS):
    print("\n✅ All 6 dashboards deployed successfully!")
    print("\n🔗 View at: https://e2-demo-field-eng.cloud.databricks.com/sql/dashboards")
    dbutils.notebook.exit("SUCCESS: All 6 dashboards deployed")
elif success_count > 0:
    failed_list = [f for f, r in results.items() if r.get("status") == "FAILED"]
    # Capture first error details for debugging
    first_error = ""
    for f, r in results.items():
        if r.get("status") == "FAILED" and r.get("error"):
            first_error = r.get("error", "")[:200]
            break
    print(f"\n⚠️ PARTIAL: {success_count}/{len(DASHBOARDS)} dashboards deployed")
    # Include error details in notebook exit
    dbutils.notebook.exit(f"PARTIAL: {success_count}/6. Failed: {failed_list}. Error: {first_error}")
else:
    raise RuntimeError(f"Deployment failed: 0/{len(DASHBOARDS)} dashboards deployed")
