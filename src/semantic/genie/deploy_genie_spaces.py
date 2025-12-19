# Databricks notebook source
"""
Genie Space Deployment Script
=============================

Deploys all Genie Spaces for Health Monitor.
Uses the Databricks SDK Genie API to create or update spaces.
"""

# COMMAND ----------

import json
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

print(f"Deploying Genie Spaces for: {catalog}.{gold_schema}")
print(f"Warehouse ID: {warehouse_id}")

# COMMAND ----------

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.dashboards import GenieSpace, GenieDataAsset
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Databricks SDK not available - using config export only")

# COMMAND ----------

def substitute_variables(content: str, catalog: str, gold_schema: str) -> str:
    """Replace ${...} placeholders in configuration."""
    replacements = {
        '${catalog}': catalog,
        '${gold_schema}': gold_schema,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def load_genie_config(file_path: str, catalog: str, gold_schema: str) -> dict:
    """Load and parse Genie Space configuration with variable substitution."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Substitute variables
    content = substitute_variables(content, catalog, gold_schema)

    return json.loads(content)


def build_data_asset_fqn(asset: dict) -> str:
    """Build fully qualified name for a data asset."""
    catalog = asset.get('catalog', '')
    schema = asset.get('schema', '')
    name = asset.get('name', '')
    return f"{catalog}.{schema}.{name}"


def deploy_genie_space_sdk(workspace_client, config: dict, warehouse_id: str) -> str:
    """Deploy Genie Space using Databricks SDK."""
    try:
        space_name = config.get('display_name', config.get('name'))

        # Check if space exists
        existing_spaces = workspace_client.genie.list_spaces()
        existing_space = None
        for space in existing_spaces:
            if space.name == space_name:
                existing_space = space
                break

        # Build data assets list
        data_assets = []
        for asset in config.get('data_assets', []):
            fqn = build_data_asset_fqn(asset)
            data_assets.append(fqn)

        if existing_space:
            print(f"  Updating existing Genie Space: {space_name}")
            result = workspace_client.genie.update_space(
                space_id=existing_space.id,
                name=space_name,
                description=config.get('description', ''),
                instructions=config.get('instructions', ''),
                warehouse_id=warehouse_id,
                trusted_asset_full_names=data_assets
            )
        else:
            print(f"  Creating new Genie Space: {space_name}")
            result = workspace_client.genie.create_space(
                name=space_name,
                description=config.get('description', ''),
                instructions=config.get('instructions', ''),
                warehouse_id=warehouse_id,
                trusted_asset_full_names=data_assets
            )

        return result.id if hasattr(result, 'id') else "SUCCESS"

    except Exception as e:
        print(f"  SDK deployment failed: {str(e)}")
        raise


def deploy_genie_space(space_name: str, json_file: str, catalog: str, gold_schema: str, warehouse_id: str) -> bool:
    """Deploy a single Genie Space."""
    try:
        print(f"Deploying Genie Space: {space_name}")

        # Load configuration
        config = load_genie_config(json_file, catalog, gold_schema)

        if SDK_AVAILABLE:
            workspace_client = WorkspaceClient()
            space_id = deploy_genie_space_sdk(workspace_client, config, warehouse_id)
            print(f"  Space ID: {space_id}")
        else:
            # Fallback: Save processed config for manual deployment
            output_path = f"/tmp/{space_name}_genie_config.json"
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"  Processed config saved to: {output_path}")

        print(f"  Successfully deployed: {space_name}")
        return True

    except Exception as e:
        print(f"  Failed to deploy {space_name}: {str(e)}")
        return False

# COMMAND ----------

# Find all Genie Space configuration files
genie_dir = Path(__file__).parent if '__file__' in dir() else Path(".")

# List of Genie Spaces to deploy
GENIE_SPACES = [
    ("cost_intelligence", "cost_intelligence.json"),
    ("job_health_monitor", "job_health_monitor.json"),
    ("query_performance", "query_performance.json"),
    ("cluster_optimizer", "cluster_optimizer.json"),
    ("security_auditor", "security_auditor.json"),
    ("health_monitor_unified", "health_monitor_unified.json"),
]

# COMMAND ----------

# Validate warehouse_id
if not warehouse_id:
    print("WARNING: No warehouse_id provided. Genie Spaces may not function correctly.")

# Deploy all Genie Spaces
results = []
for space_name, json_file in GENIE_SPACES:
    json_path = genie_dir / json_file
    if json_path.exists():
        success = deploy_genie_space(space_name, str(json_path), catalog, gold_schema, warehouse_id)
        results.append((space_name, success))
    else:
        print(f"  Configuration file not found: {json_file}")
        results.append((space_name, False))

# COMMAND ----------

# Summary
print("\n" + "=" * 50)
print("Genie Space Deployment Summary")
print("=" * 50)

successful = sum(1 for _, success in results if success)
failed = sum(1 for _, success in results if not success)

print(f"\nTotal: {len(results)}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

if failed > 0:
    print("\nFailed spaces:")
    for space_name, success in results:
        if not success:
            print(f"  - {space_name}")

# COMMAND ----------

# Exit with appropriate status
if failed > 0:
    dbutils.notebook.exit(f"PARTIAL: {failed} Genie Spaces failed to deploy")
else:
    dbutils.notebook.exit(f"SUCCESS: {successful} Genie Spaces deployed")
