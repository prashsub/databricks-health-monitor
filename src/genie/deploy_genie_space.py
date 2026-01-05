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
dbutils.widgets.text("feature_schema", "", "Feature Schema Name (for ML tables)")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")
dbutils.widgets.text("genie_space_json", "", "JSON Export File Path (optional)")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
feature_schema = dbutils.widgets.get("feature_schema") or f"{gold_schema}_ml"
warehouse_id = dbutils.widgets.get("warehouse_id")
genie_space_json = dbutils.widgets.get("genie_space_json")

print(f"Catalog: {catalog}")
print(f"Gold Schema: {gold_schema}")
print(f"Feature Schema: {feature_schema}")
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

def substitute_variables(content: str, catalog: str, gold_schema: str, feature_schema: str) -> str:
    """
    Substitute ${catalog}, ${gold_schema}, and ${feature_schema} variables in content.
    
    Args:
        content: String containing variable placeholders
        catalog: Catalog name to substitute
        gold_schema: Gold schema name to substitute
        feature_schema: Feature schema name to substitute (for ML tables)
    
    Returns:
        String with variables substituted
    """
    result = content.replace("${catalog}", catalog)
    result = result.replace("${gold_schema}", gold_schema)
    result = result.replace("${feature_schema}", feature_schema)
    return result


def process_json_values(obj: Any, catalog: str, gold_schema: str, feature_schema: str) -> Any:
    """
    Recursively process JSON object and substitute variables.
    
    Args:
        obj: JSON object (dict, list, or primitive)
        catalog: Catalog name to substitute
        gold_schema: Gold schema name to substitute
        feature_schema: Feature schema name to substitute (for ML tables)
    
    Returns:
        Processed JSON object with variables substituted
    """
    if isinstance(obj, dict):
        return {k: process_json_values(v, catalog, gold_schema, feature_schema) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [process_json_values(item, catalog, gold_schema, feature_schema) for item in obj]
    elif isinstance(obj, str):
        return substitute_variables(obj, catalog, gold_schema, feature_schema)
    else:
        return obj


def load_genie_space_export(json_path: str, catalog: str, gold_schema: str, feature_schema: str) -> dict:
    """
    Load and process a Genie Space JSON export file.
    
    Args:
        json_path: Path to JSON export file (can be Workspace path or absolute)
        catalog: Catalog name for variable substitution
        gold_schema: Gold schema name for variable substitution
        feature_schema: Feature schema name for variable substitution (for ML tables)
    
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
    processed = process_json_values(export_data, catalog, gold_schema, feature_schema)
    
    # Sort data_sources.tables by identifier (API requires sorted tables)
    if 'data_sources' in processed:
        if 'tables' in processed['data_sources']:
            processed['data_sources']['tables'].sort(key=lambda x: x.get('identifier', ''))
            # Also sort column_configs within each table
            for table in processed['data_sources']['tables']:
                if 'column_configs' in table:
                    table['column_configs'].sort(key=lambda x: x.get('column_name', ''))
        if 'metric_views' in processed['data_sources']:
            processed['data_sources']['metric_views'].sort(key=lambda x: x.get('identifier', ''))
            # Also sort column_configs within each metric view
            for mv in processed['data_sources']['metric_views']:
                if 'column_configs' in mv:
                    mv['column_configs'].sort(key=lambda x: x.get('column_name', ''))
    
    # Sort instructions by (id, identifier) - API requirement
    if 'instructions' in processed:
        if 'sql_functions' in processed['instructions']:
            processed['instructions']['sql_functions'].sort(key=lambda x: (x.get('id', ''), x.get('identifier', '')))
        if 'text_instructions' in processed['instructions']:
            processed['instructions']['text_instructions'].sort(key=lambda x: (x.get('id', ''), x.get('content', '')))
        if 'example_question_sqls' in processed['instructions']:
            processed['instructions']['example_question_sqls'].sort(key=lambda x: (x.get('id', ''), x.get('question', '')))
        if 'join_specs' in processed['instructions']:
            processed['instructions']['join_specs'].sort(key=lambda x: (x.get('id', '')))
    
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
    serialized_space: str,
    preserve_title: bool = True
) -> dict:
    """
    Update an existing Genie Space using the REST API.
    
    Reference: https://docs.databricks.com/api/workspace/genie/updatespace
    Uses PATCH for partial updates.
    
    Args:
        host: Databricks workspace host URL
        token: Personal access token
        space_id: Existing Genie Space ID to update
        title: Genie Space display name (only used if preserve_title=False)
        description: Genie Space description
        warehouse_id: SQL Warehouse ID for compute
        serialized_space: JSON string of GenieSpaceExport
        preserve_title: If True, don't change the existing title (avoids naming conflicts)
    
    Returns:
        API response dict
    """
    import requests
    
    url = f"{host}/api/2.0/genie/spaces/{space_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Build payload - only include title if we want to change it
    payload = {
        "description": description,
        "warehouse_id": warehouse_id,
        "serialized_space": serialized_space
    }
    
    # Only include title if not preserving existing title
    if not preserve_title:
        payload["title"] = title
    
    print(f"Updating Genie Space: {title}")
    print(f"  Space ID: {space_id}")
    print(f"  Preserve title: {preserve_title}")
    
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
    
    Handles Databricks's automatic numeric suffix addition (e.g., "My Space (1)", "My Space (2)").
    Searches for exact match first, then falls back to prefix match.
    
    Args:
        host: Databricks workspace host URL
        token: Personal access token
        title: Genie Space title to search for
    
    Returns:
        space_id if found, None otherwise
    """
    import requests
    import re
    
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
    
    # First, try exact match
    for space in spaces:
        if space.get("title") == title:
            print(f"  Found exact match: {title}")
            return space.get("space_id")
    
    # If no exact match, search for spaces with numeric suffix pattern: "Title (N)"
    # Example: "Health Monitor Cost Intelligence Space (3)"
    suffix_pattern = re.compile(rf"^{re.escape(title)} \(\d+\)$")
    
    matching_spaces = []
    for space in spaces:
        space_title = space.get("title", "")
        if suffix_pattern.match(space_title):
            matching_spaces.append(space)
    
    if matching_spaces:
        # Return the one with highest suffix number (most recent)
        def extract_suffix(space):
            match = re.search(r"\((\d+)\)$", space.get("title", ""))
            return int(match.group(1)) if match else 0
        
        most_recent = max(matching_spaces, key=extract_suffix)
        print(f"  Found existing space with suffix: {most_recent.get('title')}")
        return most_recent.get("space_id")
    
    return None

# COMMAND ----------

def deploy_genie_space(
    json_file: str,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
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
        feature_schema: Feature schema name (for ML tables)
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
    export_data = load_genie_space_export(json_file, catalog, gold_schema, feature_schema)
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

def validate_json_export(json_file: str) -> bool:
    """
    Pre-deployment validation of JSON export file.
    
    Args:
        json_file: Path to JSON export file
    
    Returns:
        True if validation passes, False otherwise
    """
    import sys
    import importlib.util
    
    # Import validation module
    validator_path = os.path.join(os.path.dirname(json_file), "validate_genie_space.py")
    
    if not os.path.exists(validator_path):
        print(f"⚠️  Warning: Validator not found at {validator_path}, skipping validation")
        return True
    
    # Load validator module
    spec = importlib.util.spec_from_file_location("validator", validator_path)
    validator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator_module)
    
    # Run validation
    validator = validator_module.GenieSpaceValidator(json_file)
    passed = validator.validate()
    
    return passed


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
            
            # Pre-deployment validation
            print(f"Running pre-deployment validation...")
            if not validate_json_export(json_file):
                raise ValueError(f"Validation failed for {json_file}")
            print(f"✅ Validation passed")
            
            space_id = deploy_genie_space(
                json_file=json_file,
                catalog=catalog,
                gold_schema=gold_schema,
                feature_schema=feature_schema,
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
        error_details = []
        for filename, error in failed_spaces:
            print(f"   - {filename}: {error}")
            error_details.append(f"{filename}: {error[:500]}")  # Truncate long errors
        
        error_summary = "\n".join(error_details)
        raise RuntimeError(f"Failed to deploy {len(failed_spaces)} Genie Space(s):\n{error_summary}")
    
    print("\n✅ All Genie Spaces deployed successfully!")
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

# Execute
if __name__ == "__main__":
    main()

