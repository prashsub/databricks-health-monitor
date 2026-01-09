#!/usr/bin/env python3
"""
Local Genie Space Deployment Script

Deploys Genie Spaces using the REST API without requiring Databricks notebook environment.
Uses databricks CLI profile for authentication.

Usage:
    python scripts/deploy_genie_spaces_local.py cost_intelligence
    python scripts/deploy_genie_spaces_local.py --all
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
import requests

# Configuration
CATALOG = "pras_demo"
GOLD_SCHEMA = "health_monitor_gold"
FEATURE_SCHEMA = "health_monitor_gold_ml"
WAREHOUSE_ID = "79fcb4f1ccf2e53a"

GENIE_DIR = Path(__file__).parent.parent / "src" / "genie"

# Genie Space metadata mapping (JSON file -> display name, description)
GENIE_SPACE_METADATA = {
    "job_health_monitor_genie_export.json": {
        "title": "Health Monitor Job Reliability Space",
        "description": "Natural language interface for Databricks job reliability and execution analytics."
    },
    "cost_intelligence_genie_export.json": {
        "title": "Health Monitor Cost Intelligence Space",
        "description": "Natural language interface for Databricks cost analytics and FinOps."
    },
    "performance_genie_export.json": {
        "title": "Health Monitor Performance Space",
        "description": "Natural language interface for Databricks query and cluster performance analytics."
    },
    "security_auditor_genie_export.json": {
        "title": "Health Monitor Security Auditor Space",
        "description": "Natural language interface for Databricks security, audit, and compliance analytics."
    },
    "data_quality_monitor_genie_export.json": {
        "title": "Health Monitor Data Quality Space",
        "description": "Natural language interface for data quality, freshness, and governance analytics."
    },
    "unified_health_monitor_genie_export.json": {
        "title": "Databricks Health Monitor Space",
        "description": "Comprehensive natural language interface for Databricks platform health monitoring."
    }
}


def get_databricks_auth(profile: str = "DEFAULT"):
    """Get Databricks authentication from CLI config."""
    # Get host from profile
    host = "https://e2-demo-field-eng.cloud.databricks.com"

    # Get token using profile (returns JSON)
    token_result = subprocess.run(
        ["databricks", "auth", "token", "--host", host],
        capture_output=True, text=True
    )
    if token_result.returncode != 0:
        raise RuntimeError(f"Failed to get databricks token: {token_result.stderr}")

    # Parse JSON response and extract access_token
    try:
        token_data = json.loads(token_result.stdout.strip())
        token = token_data.get("access_token")
        if not token:
            raise RuntimeError("No access_token in response")
    except json.JSONDecodeError:
        # Maybe it's just the token directly
        token = token_result.stdout.strip()

    return host, token


def substitute_variables(content: str) -> str:
    """Substitute ${catalog}, ${gold_schema}, and ${feature_schema} variables."""
    result = content.replace("${catalog}", CATALOG)
    result = result.replace("${gold_schema}", GOLD_SCHEMA)
    result = result.replace("${feature_schema}", FEATURE_SCHEMA)
    return result


def process_json_values(obj: Any) -> Any:
    """Recursively process JSON object and substitute variables."""
    if isinstance(obj, dict):
        return {k: process_json_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [process_json_values(item) for item in obj]
    elif isinstance(obj, str):
        return substitute_variables(obj)
    else:
        return obj


def load_genie_space_export(json_path: Path) -> dict:
    """Load and process a Genie Space JSON export file."""
    with open(json_path, 'r') as f:
        export_data = json.load(f)

    # Substitute variables
    processed = process_json_values(export_data)

    # Sort data_sources.tables by identifier (API requires sorted tables)
    if 'data_sources' in processed:
        if 'tables' in processed['data_sources']:
            processed['data_sources']['tables'].sort(key=lambda x: x.get('identifier', ''))
            for table in processed['data_sources']['tables']:
                if 'column_configs' in table:
                    table['column_configs'].sort(key=lambda x: x.get('column_name', ''))
        if 'metric_views' in processed['data_sources']:
            processed['data_sources']['metric_views'].sort(key=lambda x: x.get('identifier', ''))
            for mv in processed['data_sources']['metric_views']:
                if 'column_configs' in mv:
                    mv['column_configs'].sort(key=lambda x: x.get('column_name', ''))

    # Sort instructions by (id, identifier) - API requirement
    if 'instructions' in processed:
        if 'sql_functions' in processed['instructions']:
            funcs = processed['instructions']['sql_functions']
            if funcs and isinstance(funcs[0], dict):
                funcs.sort(key=lambda x: (x.get('id', ''), x.get('identifier', '')))
        if 'text_instructions' in processed['instructions']:
            instructions = processed['instructions']['text_instructions']
            if instructions and isinstance(instructions[0], dict):
                instructions.sort(key=lambda x: (x.get('id', ''), x.get('content', '')))
        if 'example_question_sqls' in processed['instructions']:
            examples = processed['instructions']['example_question_sqls']
            if examples and isinstance(examples[0], dict):
                examples.sort(key=lambda x: (x.get('id', ''), x.get('question', '')))
        if 'join_specs' in processed['instructions']:
            joins = processed['instructions']['join_specs']
            if joins and isinstance(joins[0], dict):
                joins.sort(key=lambda x: (x.get('id', '')))

    return processed


def find_existing_genie_space(host: str, token: str, title: str) -> Optional[str]:
    """Find an existing Genie Space by title."""
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

    # Search for spaces with numeric suffix pattern: "Title (N)"
    suffix_pattern = re.compile(rf"^{re.escape(title)} \(\d+\)$")

    matching_spaces = []
    for space in spaces:
        space_title = space.get("title", "")
        if suffix_pattern.match(space_title):
            matching_spaces.append(space)

    if matching_spaces:
        def extract_suffix(space):
            match = re.search(r"\((\d+)\)$", space.get("title", ""))
            return int(match.group(1)) if match else 0

        most_recent = max(matching_spaces, key=extract_suffix)
        print(f"  Found existing space with suffix: {most_recent.get('title')}")
        return most_recent.get("space_id")

    return None


def update_genie_space_via_api(
    host: str,
    token: str,
    space_id: str,
    title: str,
    description: str,
    serialized_space: str
) -> dict:
    """Update an existing Genie Space using PATCH."""
    url = f"{host}/api/2.0/genie/spaces/{space_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "description": description,
        "warehouse_id": WAREHOUSE_ID,
        "serialized_space": serialized_space
    }

    print(f"Updating Genie Space: {title}")
    print(f"  Space ID: {space_id}")

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"  Error: {response.status_code}")
        print(f"  Response: {response.text}")
        raise Exception(f"Failed to update Genie Space: {response.text}")

    print(f"  Updated successfully!")

    return response.json()


def create_genie_space_via_api(
    host: str,
    token: str,
    title: str,
    description: str,
    serialized_space: str
) -> dict:
    """Create a new Genie Space."""
    url = f"{host}/api/2.0/genie/spaces"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": title,
        "description": description,
        "warehouse_id": WAREHOUSE_ID,
        "serialized_space": serialized_space
    }

    print(f"Creating Genie Space: {title}")
    print(f"  Warehouse ID: {WAREHOUSE_ID}")

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"  Error: {response.status_code}")
        print(f"  Response: {response.text}")
        raise Exception(f"Failed to create Genie Space: {response.text}")

    result = response.json()
    space_id = result.get("space_id")
    print(f"  Created successfully! Space ID: {space_id}")

    return result


def deploy_genie_space(json_file: Path, host: str, token: str) -> str:
    """Deploy a single Genie Space from JSON export file."""
    filename = json_file.name
    metadata = GENIE_SPACE_METADATA.get(filename)

    if metadata is None:
        raise ValueError(f"Unknown Genie Space JSON file: {filename}")

    title = metadata["title"]
    description = metadata["description"]

    print(f"\n{'='*70}")
    print(f"Deploying: {title}")
    print(f"{'='*70}")

    # Load and process JSON
    print(f"Loading JSON: {json_file.name}")
    export_data = load_genie_space_export(json_file)
    serialized_space = json.dumps(export_data, indent=2)
    print(f"  Serialized space size: {len(serialized_space)} bytes")

    # Check for existing space
    existing_space_id = find_existing_genie_space(host, token, title)
    if existing_space_id:
        print(f"Found existing space with ID: {existing_space_id}")
        update_genie_space_via_api(
            host, token, existing_space_id, title, description, serialized_space
        )
        return existing_space_id

    # Create new space
    result = create_genie_space_via_api(
        host, token, title, description, serialized_space
    )

    return result.get("space_id")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Genie Spaces locally")
    parser.add_argument("space", nargs="?", help="Space name (without _genie_export.json suffix)")
    parser.add_argument("--all", action="store_true", help="Deploy all spaces")
    parser.add_argument("--list", action="store_true", help="List available spaces")

    args = parser.parse_args()

    if args.list:
        print("Available Genie Spaces:")
        for filename, metadata in GENIE_SPACE_METADATA.items():
            name = filename.replace("_genie_export.json", "")
            print(f"  - {name}: {metadata['title']}")
        return

    # Get authentication
    print("Getting Databricks authentication...")
    host, token = get_databricks_auth()
    print(f"Host: {host}")

    # Determine which spaces to deploy
    if args.all:
        json_files = list(GENIE_DIR.glob("*_genie_export.json"))
    elif args.space:
        json_file = GENIE_DIR / f"{args.space}_genie_export.json"
        if not json_file.exists():
            print(f"Error: {json_file} not found")
            sys.exit(1)
        json_files = [json_file]
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\nDeploying {len(json_files)} Genie Space(s)...")

    deployed = []
    failed = []

    for json_file in sorted(json_files):
        try:
            space_id = deploy_genie_space(json_file, host, token)
            deployed.append((json_file.name, space_id))
        except Exception as e:
            print(f"  Failed: {str(e)}")
            failed.append((json_file.name, str(e)))

    # Summary
    print(f"\n{'='*70}")
    print("DEPLOYMENT SUMMARY")
    print(f"{'='*70}")

    print(f"\nSuccessfully deployed: {len(deployed)}")
    for filename, space_id in deployed:
        print(f"   {filename}: {space_id}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for filename, error in failed:
            # Truncate long errors
            error_short = error[:200] + "..." if len(error) > 200 else error
            print(f"   {filename}: {error_short}")
        sys.exit(1)

    print("\nAll Genie Spaces deployed successfully!")


if __name__ == "__main__":
    main()
