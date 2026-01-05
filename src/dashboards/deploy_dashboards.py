# Databricks notebook source
"""
Dashboard Deployment Script
===========================

Deploys the 6 Health Monitor Lakeview AI/BI dashboards using UPDATE-or-CREATE pattern.

**Deployment Strategy:**
- If a dashboard with the same name exists in the target folder → UPDATE it (preserves URL, permissions)
- If no matching dashboard exists → CREATE a new one

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
- dashboard_folder: Target folder (updates dashboards with same name in this folder)

API References:
- CREATE: POST /api/2.0/lakeview/dashboards
- UPDATE: PATCH /api/2.0/lakeview/dashboards/{dashboard_id}
- LIST: GET /api/2.0/lakeview/dashboards
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
dbutils.widgets.text("dashboard_folder", "/Shared/health_monitor/dashboards", "Dashboard Folder")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
warehouse_id = dbutils.widgets.get("warehouse_id")
dashboard_folder = dbutils.widgets.get("dashboard_folder")

print(f"Deploying Dashboards for: {catalog}.{gold_schema}")
print(f"Warehouse ID: {warehouse_id}")
print(f"Dashboard Folder: {dashboard_folder}")

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
# Note: Display names use parentheses instead of square brackets 
# because square brackets cause API validation errors
DASHBOARDS = [
    ("cost.lvdash.json", "Health Monitor - Cost & Commitment"),
    ("performance.lvdash.json", "Health Monitor - Performance"),
    ("reliability.lvdash.json", "Health Monitor - Reliability"),
    ("security.lvdash.json", "Health Monitor - Security"),
    ("quality.lvdash.json", "Health Monitor - Quality & Governance"),
    ("unified.lvdash.json", "Health Monitor - Unified Dashboard"),
]

# COMMAND ----------

def substitute_variables(json_str: str, catalog: str, gold_schema: str, warehouse_id: str) -> str:
    """Replace variable placeholders with actual values."""
    json_str = json_str.replace('${catalog}', catalog)
    json_str = json_str.replace('${gold_schema}', gold_schema)
    json_str = json_str.replace('${warehouse_id}', warehouse_id)
    
    # ML/Feature schema - derives from gold_schema pattern
    # dev_prashanth_subrahmanyam_system_gold -> dev_prashanth_subrahmanyam_system_gold_ml
    feature_schema = gold_schema.replace('_system_gold', '_system_gold_ml')
    json_str = json_str.replace('${feature_schema}', feature_schema)
    json_str = json_str.replace('${ml_schema}', feature_schema)
    
    return json_str


def load_dashboard(file_path: str, catalog: str, gold_schema: str, warehouse_id: str) -> dict:
    """Load dashboard JSON and substitute variables."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    content = substitute_variables(content, catalog, gold_schema, warehouse_id)
    return json.loads(content)


def ensure_folder_exists(workspace_client, folder_path: str):
    """
    Ensure the target folder exists in the workspace.
    Creates it recursively if it doesn't exist.
    """
    from databricks.sdk.service.workspace import ObjectType
    
    try:
        # Try to get the folder - if it exists, we're done
        workspace_client.workspace.get_status(folder_path)
        print(f"  📁 Folder exists: {folder_path}")
    except Exception:
        # Folder doesn't exist, create it
        try:
            workspace_client.workspace.mkdirs(folder_path)
            print(f"  📁 Created folder: {folder_path}")
        except Exception as e:
            print(f"  ⚠️ Could not create folder: {e}")


def cleanup_old_dashboards(workspace_client, folder_path: str, keep_filenames: list):
    """
    Delete any dashboards in the folder that are NOT in the keep_filenames list.
    This ensures we don't have duplicate dashboards with old naming conventions.
    
    Args:
        workspace_client: Databricks workspace client
        folder_path: Workspace folder path containing dashboards
        keep_filenames: List of filenames to keep (e.g., ['cost.lvdash.json', 'performance.lvdash.json'])
    """
    print(f"\n🧹 Cleaning up old dashboards in {folder_path}...")
    
    try:
        # List all items in the folder
        items = workspace_client.workspace.list(folder_path)
        
        deleted_count = 0
        for item in items:
            item_name = item.path.split('/')[-1]
            
            # Check if this is a dashboard file we should delete
            if item_name.endswith('.lvdash.json') and item_name not in keep_filenames:
                try:
                    workspace_client.workspace.delete(item.path)
                    print(f"  🗑️ Deleted old dashboard: {item_name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ⚠️ Could not delete {item_name}: {e}")
        
        if deleted_count == 0:
            print(f"  ✅ No old dashboards to clean up in folder")
        else:
            print(f"  ✅ Cleaned up {deleted_count} old dashboard(s) from folder")
            
    except Exception as e:
        print(f"  ⚠️ Could not list folder contents: {e}")


def cleanup_lakeview_duplicates(workspace_client, keep_display_names: list):
    """
    Delete duplicate dashboards from the Lakeview API that match "Health Monitor" pattern
    but are NOT in our expected display names list.
    
    This handles dashboards that were created with old naming patterns and appear
    in the SQL Dashboards list.
    
    Args:
        workspace_client: Databricks workspace client
        keep_display_names: List of display names to keep
    """
    print(f"\n🧹 Cleaning up duplicate dashboards from Lakeview API...")
    
    try:
        # List all dashboards via Lakeview API
        result = workspace_client.api_client.do(
            method="GET",
            path="/api/2.0/lakeview/dashboards",
            query={"page_size": 200}
        )
        
        dashboards = result.get("dashboards", [])
        deleted_count = 0
        
        for dashboard in dashboards:
            display_name = dashboard.get("display_name", "")
            dashboard_id = dashboard.get("dashboard_id", "")
            
            # Check if this is a Health Monitor dashboard that's NOT in our keep list
            if ("Health Monitor" in display_name or "[Health Monitor]" in display_name):
                if display_name not in keep_display_names:
                    try:
                        # Delete via Lakeview API
                        workspace_client.api_client.do(
                            method="DELETE",
                            path=f"/api/2.0/lakeview/dashboards/{dashboard_id}"
                        )
                        print(f"  🗑️ Deleted duplicate: {display_name}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"  ⚠️ Could not delete '{display_name}': {e}")
        
        if deleted_count == 0:
            print(f"  ✅ No duplicate dashboards found in Lakeview")
        else:
            print(f"  ✅ Cleaned up {deleted_count} duplicate dashboard(s) from Lakeview")
            
    except Exception as e:
        print(f"  ⚠️ Could not list Lakeview dashboards: {e}")


def deploy_dashboard_via_workspace_import(workspace_client, dashboard_config: dict, display_name: str, parent_path: str, source_filename: str = None) -> tuple:
    """
    Deploy a dashboard using Workspace Import API with overwrite support.
    
    This is the RECOMMENDED approach per Microsoft documentation.
    Reference: https://learn.microsoft.com/en-us/azure/databricks/dashboards/tutorials/workspace-dashboard-api
    
    Args:
        workspace_client: Databricks workspace client
        dashboard_config: Dashboard configuration dictionary
        display_name: Display name for the dashboard (shown in UI)
        parent_path: Workspace folder path to deploy dashboard to
        source_filename: Original filename to use (e.g., cost.lvdash.json)
    
    Returns:
        Tuple of (dashboard_path, action) where action is 'CREATED' or 'UPDATED'
        
    Strategy: 
    1. Serialize dashboard to JSON
    2. Encode to base64
    3. Use POST /api/2.0/workspace/import with overwrite=true
    4. If exists, overwrites; if not, creates new
    """
    import base64
    
    # Set display name in the config
    dashboard_config['displayName'] = display_name
    
    # Serialize dashboard to JSON string
    serialized_dashboard = json.dumps(dashboard_config)
    
    # Encode to base64
    content_base64 = base64.b64encode(serialized_dashboard.encode('utf-8')).decode('utf-8')
    
    # Construct the file path - use source filename directly (clean, no timestamps)
    # e.g., cost.lvdash.json, not Health_Monitor_Cost_and_Commitment.lvdash.json
    file_path = f"{parent_path}/{source_filename}"
    
    # Log info
    size_kb = len(serialized_dashboard) / 1024
    print(f"  📤 Importing: {display_name} ({size_kb:.1f} KB)")
    print(f"     Path: {file_path}")
    
    try:
        # Check if dashboard already exists
        existing = False
        try:
            result = workspace_client.api_client.do(
                method="GET",
                path="/api/2.0/workspace/get-status",
                query={"path": file_path}
            )
            existing = result.get("object_type") == "DASHBOARD"
            if existing:
                print(f"  🔄 Dashboard exists, will overwrite...")
        except Exception:
            # Dashboard doesn't exist yet
            pass
        
        # Import/overwrite the dashboard
        # Reference: POST /api/2.0/workspace/import
        workspace_client.api_client.do(
            method="POST",
            path="/api/2.0/workspace/import",
            body={
                "path": file_path,
                "content": content_base64,
                "format": "AUTO",
                "overwrite": True  # Key setting - allows update
            }
        )
        
        action = "UPDATED" if existing else "CREATED"
        print(f"  ✅ {action} successfully at: {file_path}")
        
        # Get the resource_id for reference
        try:
            status = workspace_client.api_client.do(
                method="GET",
                path="/api/2.0/workspace/get-status",
                query={"path": file_path}
            )
            dashboard_id = status.get("resource_id", file_path)
        except Exception:
            dashboard_id = file_path
            
        return dashboard_id, action
        
    except Exception as e:
        print(f"  ❌ Import failed: {type(e).__name__}: {str(e)}")
        if hasattr(e, 'response'):
            try:
                print(f"  Response: {e.response.text}")
            except:
                pass
        raise


def deploy_dashboard(workspace_client, dashboard_config: dict, display_name: str, parent_path: str = None, source_filename: str = None) -> tuple:
    """
    Deploy a dashboard using Workspace Import API (recommended approach).
    
    This wraps deploy_dashboard_via_workspace_import for backward compatibility.
    """
    if not parent_path:
        raise ValueError("parent_path is required for dashboard deployment")
    if not source_filename:
        raise ValueError("source_filename is required for dashboard deployment")
    
    return deploy_dashboard_via_workspace_import(
        workspace_client, 
        dashboard_config, 
        display_name, 
        parent_path,
        source_filename
    )

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
print(f"Target folder: {dashboard_folder}")

# Initialize SDK client
if SDK_AVAILABLE:
    workspace_client = WorkspaceClient()
    print("SDK client initialized")
else:
    raise RuntimeError("Databricks SDK required for deployment")

# Ensure target folder exists
if dashboard_folder:
    ensure_folder_exists(workspace_client, dashboard_folder)

# Clean up old dashboards with different naming patterns
# This prevents duplicates when we changed from "Health_Monitor_X.lvdash.json" to "x.lvdash.json"
keep_filenames = [filename for filename, _ in DASHBOARDS]
keep_display_names = [display_name for _, display_name in DASHBOARDS]
cleanup_old_dashboards(workspace_client, dashboard_folder, keep_filenames)
cleanup_lakeview_duplicates(workspace_client, keep_display_names)

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
        
        # Deploy to specified folder (UPDATE if exists, CREATE if new)
        # Use source filename directly for clean paths (e.g., cost.lvdash.json)
        dashboard_id, action = deploy_dashboard(
            workspace_client, 
            dashboard_config, 
            display_name,
            parent_path=dashboard_folder if dashboard_folder else None,
            source_filename=filename  # Use original filename (cost.lvdash.json, etc.)
        )
        results[filename] = {
            "status": "SUCCESS", 
            "id": dashboard_id, 
            "folder": dashboard_folder,
            "action": action  # CREATED or UPDATED
        }
        
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
created_count = sum(1 for r in results.values() if r.get("action") == "CREATED")
updated_count = sum(1 for r in results.values() if r.get("action") == "UPDATED")

print(f"Total Dashboards: {len(DASHBOARDS)}")
print(f"  ✅ Deployed: {success_count}")
print(f"     🆕 Created: {created_count}")
print(f"     🔄 Updated: {updated_count}")
print(f"  ❌ Failed: {failed_count}")
print(f"  ⚠️ Skipped: {skipped_count}")
print(f"  📁 Target Folder: {dashboard_folder or 'Default (user home)'}")

# List results for each dashboard
print("\n📊 Individual Results:")
for filename, result in results.items():
    status = result.get("status", "UNKNOWN")
    if status == "SUCCESS":
        action = result.get('action', 'deployed')
        action_icon = "🆕" if action == "CREATED" else "🔄"
        dashboard_id = result.get('id', 'N/A')
        # Truncate long paths for readability
        if isinstance(dashboard_id, str) and len(dashboard_id) > 50:
            dashboard_id = "..." + dashboard_id[-40:]
        print(f"  {action_icon} {filename}: {action} ({dashboard_id})")
    elif status == "FAILED":
        print(f"  ❌ {filename}: {result.get('error', 'Unknown error')[:150]}")
    elif status == "SKIPPED":
        print(f"  ⚠️ {filename}: {result.get('reason', 'Skipped')}")

if success_count == len(DASHBOARDS):
    action_summary = f"{updated_count} updated, {created_count} created"
    print(f"\n✅ All 6 dashboards deployed successfully! ({action_summary})")
    folder_msg = f" to folder: {dashboard_folder}" if dashboard_folder else ""
    print(f"\n🔗 Dashboards deployed{folder_msg}")
    print("   View at: https://e2-demo-field-eng.cloud.databricks.com/sql/dashboards")
    dbutils.notebook.exit(f"SUCCESS: All 6 dashboards to {dashboard_folder or 'default location'} ({action_summary})")
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
    # All failed - collect error details
    failed_list = [f for f, r in results.items() if r.get("status") == "FAILED"]
    error_summary = []
    for f, r in results.items():
        if r.get("status") == "FAILED" and r.get("error"):
            error_summary.append(f"{f}: {r.get('error', '')[:100]}")
    error_details = "; ".join(error_summary[:3])  # First 3 errors
    print(f"\n❌ All dashboards failed to deploy!")
    print(f"   Failed: {failed_list}")
    print(f"   Errors: {error_details}")
    raise RuntimeError(f"Deployment failed: 0/{len(DASHBOARDS)} dashboards. Errors: {error_details}")
