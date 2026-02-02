# Databricks notebook source
"""
TRAINING MATERIAL: Infrastructure-as-Code for Notification Destinations
=======================================================================

This notebook demonstrates auto-creating notification destinations,
eliminating manual UI configuration.

NOTIFICATION DESTINATION TYPES:
-------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  TYPE       │  USE CASE                    │  CONFIG REQUIRED           │
├─────────────┼──────────────────────────────┼────────────────────────────┤
│  EMAIL      │  Team email lists            │  addresses (comma-sep)     │
│  SLACK      │  Real-time team alerts       │  webhook_url               │
│  WEBHOOK    │  Custom integrations         │  url, method, headers      │
│  PAGERDUTY  │  On-call escalation          │  integration_key           │
│  TEAMS      │  Microsoft Teams channels    │  webhook_url               │
└─────────────┴──────────────────────────────┴────────────────────────────┘

CONFIG-DRIVEN DESTINATION MANAGEMENT:
-------------------------------------

Destinations defined in notification_destinations table:

    | dest_name     | dest_type | config_json                          |
    |---------------|-----------|--------------------------------------|
    | data-eng-team | EMAIL     | {"addresses": ["team@company.com"]}  |
    | urgent-slack  | SLACK     | {"webhook_url": "https://..."}       |

SYNC PATTERN:
-------------

    1. Read destinations from Delta table
    2. For each destination:
       a. Check if exists in workspace
       b. Create if missing (SDK call)
       c. Update if changed
       d. Skip if unchanged
    3. Report sync summary

PERMISSION REQUIREMENTS:
------------------------

Admin permissions required for:
- Creating new notification destinations
- Modifying existing destinations
- Listing all destinations

Service principal must have workspace admin or similar role.

Note: Admin permissions required for destination creation.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Databricks SDK for notification destinations
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.settings import (
    CreateNotificationDestinationRequest,
    DestinationType,
    EmailConfig,
    SlackConfig,
    GenericWebhookConfig,
)


def get_parameters() -> tuple[str, str, bool]:
    """Get job parameters from dbutils widgets."""
    dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
    dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
    dbutils.widgets.text("dry_run", "true", "Dry run (true/false)")

    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    dry_run = dbutils.widgets.get("dry_run").lower() == "true"

    return catalog, gold_schema, dry_run


def get_destination_type(type_str: str) -> DestinationType:
    """Convert string type to DestinationType enum."""
    type_map = {
        "EMAIL": DestinationType.EMAIL,
        "SLACK": DestinationType.SLACK,
        "WEBHOOK": DestinationType.GENERIC_WEBHOOK,
        "PAGERDUTY": DestinationType.PAGERDUTY,
        "TEAMS": DestinationType.MICROSOFT_TEAMS,
    }
    return type_map.get(type_str.upper(), DestinationType.EMAIL)


def parse_config_json(config_json: str) -> dict:
    """Parse config_json field safely."""
    if not config_json:
        return {}
    try:
        import json
        return json.loads(config_json)
    except Exception:
        return {}


def create_destination(
    ws: WorkspaceClient,
    dest_name: str,
    dest_type: str,
    config_json: str,
) -> str:
    """
    Create a notification destination in the workspace.
    
    Args:
        ws: WorkspaceClient
        dest_name: Display name for the destination
        dest_type: Destination type (EMAIL, SLACK, WEBHOOK, etc.)
        config_json: JSON configuration specific to destination type
    
    Returns:
        UUID of created destination
    """
    config = parse_config_json(config_json)
    dtype = get_destination_type(dest_type)
    
    request = CreateNotificationDestinationRequest(display_name=dest_name)
    
    if dtype == DestinationType.EMAIL:
        # Email config: addresses should be in config_json or extracted from somewhere
        addresses = config.get("addresses", [])
        if not addresses:
            addresses = [config.get("address", "admin@company.com")]
        request.config = EmailConfig(addresses=addresses)
        
    elif dtype == DestinationType.SLACK:
        # Slack config: requires URL
        url = config.get("url") or config.get("webhook_url")
        if not url:
            raise ValueError(f"Slack destination {dest_name} missing webhook URL in config_json")
        request.config = SlackConfig(url=url)
        
    elif dtype == DestinationType.GENERIC_WEBHOOK:
        # Webhook config
        url = config.get("url") or config.get("webhook_url")
        if not url:
            raise ValueError(f"Webhook destination {dest_name} missing URL in config_json")
        request.config = GenericWebhookConfig(
            url=url,
            username=config.get("username"),
            password=config.get("password"),
        )
    else:
        raise ValueError(f"Unsupported destination type: {dest_type}")
    
    # Create destination
    result = ws.notification_destinations.create(request=request)
    return result.id


def sync_notification_destinations(
    spark: SparkSession,
    ws: WorkspaceClient,
    catalog: str,
    gold_schema: str,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """
    Sync notification destinations from config table to workspace.
    
    Args:
        spark: SparkSession
        ws: WorkspaceClient
        catalog: Target catalog
        gold_schema: Target schema
        dry_run: If True, don't make API calls
    
    Returns:
        (created_count, verified_count, error_count)
    """
    dest_table = f"{catalog}.{gold_schema}.notification_destinations"
    
    print("=" * 80)
    print("NOTIFICATION DESTINATION SYNC")
    print("=" * 80)
    print(f"Config table: {dest_table}")
    print(f"Dry run:      {dry_run}")
    print("-" * 80)
    
    # Load destinations from config table
    destinations = (
        spark.table(dest_table)
        .where(col("is_enabled") == True)  # noqa: E712
        .select(
            "destination_id",
            "destination_name",
            "destination_type",
            "databricks_destination_id",
            "config_json",
        )
        .collect()
    )
    
    print(f"Found {len(destinations)} enabled destinations\n")
    
    # List existing workspace destinations for verification
    existing_destinations = {}
    try:
        for dest in ws.notification_destinations.list():
            existing_destinations[dest.id] = dest
    except Exception as e:
        print(f"⚠️ Could not list existing destinations: {e}")
    
    created = 0
    verified = 0
    errors = 0
    
    for dest in destinations:
        dest_id = dest["destination_id"]
        dest_name = dest["destination_name"]
        dest_type = dest["destination_type"]
        databricks_id = dest["databricks_destination_id"]
        config_json = dest["config_json"]
        
        print(f"[{dest_id}] {dest_name} ({dest_type})")
        
        if databricks_id:
            # Verify existing destination
            if databricks_id in existing_destinations:
                print(f"  ✓ Verified: {databricks_id}")
                verified += 1
            else:
                print(f"  ⚠️ Destination ID {databricks_id} not found in workspace")
                # Could recreate here if needed
                errors += 1
        else:
            # Create new destination
            if dry_run:
                print(f"  [DRY RUN] Would create {dest_type} destination")
                created += 1
                continue
            
            try:
                new_id = create_destination(ws, dest_name, dest_type, config_json)
                
                # Update config table with new ID
                safe_dest_id = dest_id.replace("'", "''")
                spark.sql(f"""
                UPDATE {dest_table}
                SET databricks_destination_id = '{new_id}',
                    updated_at = CURRENT_TIMESTAMP()
                WHERE destination_id = '{safe_dest_id}'
                """)
                
                print(f"  ✓ Created: {new_id}")
                created += 1
                
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                errors += 1
    
    # Summary
    print("\n" + "-" * 80)
    print(f"Created:  {created}")
    print(f"Verified: {verified}")
    print(f"Errors:   {errors}")
    print("=" * 80)
    
    return created, verified, errors


def main() -> None:
    """Main entry point."""
    catalog, gold_schema, dry_run = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    ws = WorkspaceClient()
    
    try:
        created, verified, errors = sync_notification_destinations(
            spark, ws, catalog, gold_schema, dry_run
        )
        
        if errors > 0:
            print(f"\n⚠️ Completed with {errors} error(s)")
        else:
            print("\n✅ All notification destinations synced successfully!")
        
        dbutils.notebook.exit(f"SUCCESS: {created} created, {verified} verified, {errors} errors")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        dbutils.notebook.exit(f"FAILED: {e}")
        raise


if __name__ == "__main__":
    main()

