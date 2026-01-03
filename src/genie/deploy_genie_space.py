# Databricks notebook source
"""
Genie Space Deployment Script

This script deploys Genie Spaces using the Export/Import API format.
Reference: .cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc

Usage:
  Run as Databricks notebook with parameters:
    - catalog: Unity Catalog name
    - gold_schema: Gold layer schema name
    - warehouse_id: SQL Warehouse ID for Genie Space
    - genie_space_json: Path to JSON export file (optional, defaults to all spaces)
"""

import json
import os
import re
from typing import Any, Optional

# COMMAND ----------

# Get parameters from widgets
dbutils.widgets.text("catalog", "", "Unity Catalog Name")
dbutils.widgets.text("gold_schema", "", "Gold Schema Name")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")
dbutils.widgets.text("genie_space_json", "", "JSON Export File Path (optional)")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
warehouse_id = dbutils.widgets.get("warehouse_id")
genie_space_json = dbutils.widgets.get("genie_space_json")

print(f"Catalog: {catalog}")
print(f"Gold Schema: {gold_schema}")
print(f"Warehouse ID: {warehouse_id}")
print(f"JSON File: {genie_space_json or 'All spaces'}")

# COMMAND ----------

# Genie Space metadata mapping (JSON file -> display name, description)
GENIE_SPACE_METADATA = {
    "job_health_monitor_genie_export.json": {
        "title": "Health Monitor Job Reliability Space",
        "description": "Natural language interface for Databricks job reliability and execution analytics. Enables DevOps, data engineers, and SREs to query job success rates, failure patterns, and performance metrics without SQL."
    },
    "cost_intelligence_genie_export.json": {
        "title": "Health Monitor Cost Intelligence Space",
        "description": "Natural language interface for Databricks cost analytics and FinOps. Enables finance teams, platform administrators, and executives to query billing, usage, and cost optimization insights without SQL."
    },
    "performance_genie_export.json": {
        "title": "Health Monitor Performance Space",
        "description": "Natural language interface for Databricks query and cluster performance analytics. Enables DBAs, platform engineers, and FinOps to query execution metrics, warehouse utilization, and cluster efficiency without SQL."
    },
    "security_auditor_genie_export.json": {
        "title": "Health Monitor Security Auditor Space",
        "description": "Natural language interface for Databricks security, audit, and compliance analytics. Enables security teams, compliance officers, and administrators to query access patterns, audit trails, and security events without SQL."
    },
    "data_quality_monitor_genie_export.json": {
        "title": "Health Monitor Data Quality Space",
        "description": "Natural language interface for data quality, freshness, and governance analytics. Enables data stewards, governance teams, and data engineers to query table health, lineage, and quality metrics without SQL."
    },
    "unified_health_monitor_genie_export.json": {
        "title": "Databricks Health Monitor Space",
        "description": "Comprehensive natural language interface for Databricks platform health monitoring. Enables leadership, platform administrators, and SREs to query costs, job reliability, query performance, cluster efficiency, security audit, and data quality."
    }
}

# COMMAND ----------

def substitute_variables(content: str, catalog: str, gold_schema: str) -> str:
    """
    Substitute ${catalog} and ${gold_schema} variables in content.
    
    Args:
        content: String containing variable placeholders
        catalog: Catalog name to substitute
        gold_schema: Gold schema name to substitute
    
    Returns:
        String with variables substituted
    """
    result = content.replace("${catalog}", catalog)
    result = result.replace("${gold_schema}", gold_schema)
    return result


def process_json_values(obj: Any, catalog: str, gold_schema: str) -> Any:
    """
    Recursively process JSON object and substitute variables.
    
    Args:
        obj: JSON object (dict, list, or primitive)
        catalog: Catalog name to substitute
        gold_schema: Gold schema name to substitute
    
    Returns:
        Processed JSON object with variables substituted
    """
    if isinstance(obj, dict):
        return {k: process_json_values(v, catalog, gold_schema) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [process_json_values(item, catalog, gold_schema) for item in obj]
    elif isinstance(obj, str):
        return substitute_variables(obj, catalog, gold_schema)
    else:
        return obj


def load_genie_space_export(json_path: str, catalog: str, gold_schema: str) -> dict:
    """
    Load and process a Genie Space JSON export file.
    
    Args:
        json_path: Path to JSON export file (can be Workspace path or absolute)
        catalog: Catalog name for variable substitution
        gold_schema: Gold schema name for variable substitution
    
    Returns:
        Processed GenieSpaceExport dictionary
    """
    # Try to read from Workspace path (Asset Bundles) or absolute path
    content = None
    try:
        # Try as Workspace file
        with open(json_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        # Try with /Workspace prefix (common in Databricks)
        try:
            workspace_path = f"/Workspace{json_path}" if not json_path.startswith("/Workspace") else json_path
            with open(workspace_path, 'r') as f:
                content = f.read()
        except:
            raise FileNotFoundError(f"Could not find JSON file: {json_path}")
    
    export_data = json.loads(content)
    
    # Substitute variables
    processed = process_json_values(export_data, catalog, gold_schema)
    
    return processed


def serialize_genie_space(export_data: dict) -> str:
    """
    Serialize GenieSpaceExport to JSON string for API.
    
    Args:
        export_data: GenieSpaceExport dictionary
    
    Returns:
        JSON string for serialized_space field
    """
    return json.dumps(export_data, indent=2)

# COMMAND ----------

def create_genie_space_via_api(
    host: str,
    token: str,
    title: str,
    description: str,
    warehouse_id: str,
    serialized_space: str
) -> dict:
    """
    Create a Genie Space using the REST API.
    
    Reference: .cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc
    
    Args:
        host: Databricks workspace host URL
        token: Personal access token
        title: Genie Space display name
        description: Genie Space description
        warehouse_id: SQL Warehouse ID for compute
        serialized_space: JSON string of GenieSpaceExport
    
    Returns:
        API response dict with space_id
    """
    import requests
    
    url = f"{host}/api/2.0/genie/spaces"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": title,
        "description": description,
        "warehouse_id": warehouse_id,
        "serialized_space": serialized_space
    }
    
    print(f"Creating Genie Space: {title}")
    print(f"  Warehouse ID: {warehouse_id}")
    print(f"  Serialized space size: {len(serialized_space)} bytes")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"  ❌ Error: {response.status_code}")
        print(f"  Response: {response.text}")
        raise Exception(f"Failed to create Genie Space: {response.text}")
    
    result = response.json()
    space_id = result.get("space_id")
    print(f"  ✅ Created successfully! Space ID: {space_id}")
    
    return result


def update_genie_space_via_api(
    host: str,
    token: str,
    space_id: str,
    title: str,
    description: str,
    warehouse_id: str,
    serialized_space: str
) -> dict:
    """
    Update an existing Genie Space using the REST API.
    
    Reference: https://docs.databricks.com/api/workspace/genie/updatespace
    Uses PATCH for partial updates.
    
    Args:
        host: Databricks workspace host URL
        token: Personal access token
        space_id: Existing Genie Space ID to update
        title: Genie Space display name
        description: Genie Space description
        warehouse_id: SQL Warehouse ID for compute
        serialized_space: JSON string of GenieSpaceExport
    
    Returns:
        API response dict
    """
    import requests
    
    url = f"{host}/api/2.0/genie/spaces/{space_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": title,
        "description": description,
        "warehouse_id": warehouse_id,
        "serialized_space": serialized_space
    }
    
    print(f"Updating Genie Space: {title}")
    print(f"  Space ID: {space_id}")
    
    # Use PATCH for partial updates (official API pattern)
    response = requests.patch(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"  ❌ Error: {response.status_code}")
        print(f"  Response: {response.text}")
        raise Exception(f"Failed to update Genie Space: {response.text}")
    
    print(f"  ✅ Updated successfully!")
    
    return response.json()

# COMMAND ----------

def find_existing_genie_space(host: str, token: str, title: str) -> Optional[str]:
    """
    Find an existing Genie Space by title.
    
    Args:
        host: Databricks workspace host URL
        token: Personal access token
        title: Genie Space title to search for
    
    Returns:
        space_id if found, None otherwise
    """
    import requests
    
    url = f"{host}/api/2.0/genie/spaces"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Warning: Could not list Genie Spaces: {response.text}")
        return None
    
    spaces = response.json().get("spaces", [])
    
    for space in spaces:
        if space.get("title") == title:
            return space.get("space_id")
    
    return None

# COMMAND ----------

def deploy_genie_space(
    json_file: str,
    catalog: str,
    gold_schema: str,
    warehouse_id: str,
    host: Optional[str] = None,
    token: Optional[str] = None,
    force_recreate: bool = False
) -> str:
    """
    Deploy a Genie Space from JSON export file.
    
    Args:
        json_file: Path to JSON export file
        catalog: Unity Catalog name
        gold_schema: Gold schema name
        warehouse_id: SQL Warehouse ID
        host: Databricks host (optional, auto-detected)
        token: Access token (optional, auto-detected)
        force_recreate: If True, always create new instead of updating
    
    Returns:
        Deployed space_id
    """
    # Get host and token from context if not provided
    if host is None:
        host = f"https://{spark.conf.get('spark.databricks.workspaceUrl')}"
    if token is None:
        token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
    
    # Get metadata for this JSON file
    filename = os.path.basename(json_file)
    metadata = GENIE_SPACE_METADATA.get(filename)
    
    if metadata is None:
        raise ValueError(f"Unknown Genie Space JSON file: {filename}. Add metadata to GENIE_SPACE_METADATA.")
    
    title = metadata["title"]
    description = metadata["description"]
    
    print(f"\n{'='*80}")
    print(f"Deploying Genie Space: {title}")
    print(f"{'='*80}")
    
    # Load and process JSON
    print(f"Loading JSON: {json_file}")
    export_data = load_genie_space_export(json_file, catalog, gold_schema)
    serialized_space = serialize_genie_space(export_data)
    
    # Check for existing space
    if not force_recreate:
        existing_space_id = find_existing_genie_space(host, token, title)
        if existing_space_id:
            print(f"Found existing space with ID: {existing_space_id}")
            update_genie_space_via_api(
                host, token, existing_space_id, title, description, 
                warehouse_id, serialized_space
            )
            return existing_space_id
    
    # Create new space
    result = create_genie_space_via_api(
        host, token, title, description, warehouse_id, serialized_space
    )
    
    return result.get("space_id")

# COMMAND ----------

def main():
    """Main deployment function."""
    
    if not catalog or not gold_schema or not warehouse_id:
        raise ValueError("Required parameters: catalog, gold_schema, warehouse_id")
    
    # Get the directory where JSON export files are located
    # In Asset Bundles, they're synced to the same directory as this notebook
    print("Detecting JSON export files...")
    
    if genie_space_json:
        # Deploy specific JSON file (path provided by user)
        json_files = [genie_space_json]
        print(f"Deploying specific file: {genie_space_json}")
    else:
        # Deploy the two known Genie Space exports
        # These files are located in src/genie/ and synced by Asset Bundles
        notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        script_dir = os.path.dirname(notebook_path)
        
        print(f"Notebook path: {notebook_path}")
        print(f"Script directory: {script_dir}")
        
        json_files = [
            os.path.join(script_dir, "cost_intelligence_genie_export.json"),
            os.path.join(script_dir, "job_health_monitor_genie_export.json")
        ]
        print(f"Deploying 2 Genie Spaces from JSON exports")
    
    deployed_spaces = []
    failed_spaces = []
    
    for json_file in json_files:
        try:
            print(f"\nProcessing: {json_file}")
            space_id = deploy_genie_space(
                json_file=json_file,
                catalog=catalog,
                gold_schema=gold_schema,
                warehouse_id=warehouse_id
            )
            deployed_spaces.append((os.path.basename(json_file), space_id))
        except Exception as e:
            print(f"❌ Failed to deploy {json_file}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed_spaces.append((os.path.basename(json_file), str(e)))
    
    # Summary
    print(f"\n{'='*80}")
    print("GENIE SPACE DEPLOYMENT SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n✅ Successfully Deployed: {len(deployed_spaces)}")
    for filename, space_id in deployed_spaces:
        print(f"   - {filename}: {space_id}")
    
    if failed_spaces:
        print(f"\n❌ Failed: {len(failed_spaces)}")
        for filename, error in failed_spaces:
            print(f"   - {filename}: {error}")
        raise RuntimeError(f"Failed to deploy {len(failed_spaces)} Genie Space(s)")
    
    print("\n✅ All Genie Spaces deployed successfully!")
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

# Execute
if __name__ == "__main__":
    main()

