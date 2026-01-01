# 05 - Databricks SDK Integration

## Overview

The alerting framework uses the **Databricks SDK for Python** to manage SQL Alerts programmatically. This provides type-safe, auto-authenticated access to the Alerts v2 API.

## Why SDK Over REST API?

| Feature | SDK | REST API |
|---------|-----|----------|
| **Authentication** | Automatic (notebook context) | Manual token handling |
| **Type Safety** | Typed objects (`AlertV2`, etc.) | Raw dictionaries |
| **Error Handling** | Built-in exceptions | Parse JSON responses |
| **Pagination** | Automatic iterator | Manual page tokens |
| **Update Mask** | Handled by method | Manual parameter |

## SDK Version Requirements

### Critical: Version ≥ 0.40.0

The `AlertV2` types are only available in SDK version 0.40.0 and later. Serverless environments may have older versions pre-installed.

**Problem:**
```python
# This fails in serverless with older SDK
from databricks.sdk.service.sql import AlertV2
# ImportError: cannot import name 'AlertV2'
```

**Solution:**
```python
# At the TOP of your notebook (before other imports)
%pip install --upgrade databricks-sdk>=0.40.0 --quiet
%restart_python
```

## SDK Type Hierarchy

```
databricks.sdk
├── WorkspaceClient
│   └── alerts_v2
│       ├── create_alert(alert: AlertV2) -> AlertV2
│       ├── get_alert(id: str) -> AlertV2
│       ├── list_alerts() -> Iterator[AlertV2]
│       ├── update_alert(id: str, alert: AlertV2, update_mask: str) -> AlertV2
│       └── trash_alert(id: str) -> None
│
└── databricks.sdk.service.sql
    ├── AlertV2                    # Main alert object
    ├── AlertV2Condition           # Evaluation condition
    ├── AlertV2ConditionOperand    # Left/right operands
    ├── AlertV2ConditionThreshold  # Threshold configuration
    ├── AlertV2ConditionThresholdValue  # Threshold value
    ├── AlertV2Notification        # Notification settings
    ├── AlertV2NotificationSubscription  # Subscription details
    ├── AlertV2Schedule            # Schedule configuration
    └── AlertV2State               # Alert state enum
```

## Complete Import Pattern

```python
# Databricks notebook source
# COMMAND ----------
# MAGIC %pip install --upgrade databricks-sdk>=0.40.0 --quiet
# MAGIC %restart_python
# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    AlertV2,
    AlertV2Condition,
    AlertV2ConditionOperand,
    AlertV2ConditionThreshold,
    AlertV2ConditionThresholdValue,
    AlertV2Notification,
    AlertV2NotificationSubscription,
    AlertV2Schedule,
)
from databricks.sdk.errors import ResourceAlreadyExists
```

## WorkspaceClient Authentication

### Automatic (Notebook Context)

```python
# In Databricks notebook - auto-authenticates
ws = WorkspaceClient()
```

### Manual (Local Development)

```python
# Using environment variables
import os
os.environ["DATABRICKS_HOST"] = "https://workspace.cloud.databricks.com"
os.environ["DATABRICKS_TOKEN"] = "dapi..."

ws = WorkspaceClient()

# Or using config file (~/.databrickscfg)
ws = WorkspaceClient(profile="my-profile")
```

## Building Alert Objects

### Complete AlertV2 Object

```python
def build_alert_v2(
    config: AlertConfigRow,
    warehouse_id: str,
    catalog: str,
    gold_schema: str,
    destination_map: Dict[str, str]
) -> AlertV2:
    """Build a typed AlertV2 object from configuration."""
    
    # 1. Render query template
    query_text = config.alert_query_template.replace(
        "${catalog}", catalog
    ).replace(
        "${gold_schema}", gold_schema
    )
    
    # 2. Build condition
    condition = AlertV2Condition(
        operand=AlertV2ConditionOperand(column=AlertV2ConditionOperandColumn(name=config.threshold_column)),
        op=map_operator(config.threshold_operator),
        threshold=AlertV2ConditionThreshold(
            value=AlertV2ConditionThresholdValue(
                double_value=config.threshold_value_double
                if config.threshold_value_type == "DOUBLE"
                else None,
                string_value=config.threshold_value_string
                if config.threshold_value_type == "STRING"
                else None,
                bool_value=config.threshold_value_bool
                if config.threshold_value_type == "BOOLEAN"
                else None,
            )
        ),
        empty_result_state=config.empty_result_state,
    )
    
    # 3. Build notification subscriptions
    subscriptions = build_notification_subscriptions(
        config.notification_channels, 
        destination_map
    )
    
    notification = AlertV2Notification(
        subscriptions=subscriptions,
        notify_on_ok=config.notify_on_ok,
    )
    
    # 4. Build schedule
    schedule = AlertV2Schedule(
        quartz_cron_schedule=config.schedule_cron,
        timezone_id=config.schedule_timezone,
        pause_status=config.pause_status,
    )
    
    # 5. Create AlertV2 object
    return AlertV2(
        display_name=config.alert_name,
        query_text=query_text,
        warehouse_id=warehouse_id,
        condition=condition,
        notification=notification,
        schedule=schedule,
    )
```

### Operator Mapping

```python
def map_operator(operator: str) -> str:
    """Map configuration operator to SDK operator."""
    mapping = {
        ">": "GREATER_THAN",
        "<": "LESS_THAN",
        ">=": "GREATER_THAN_OR_EQUAL",
        "<=": "LESS_THAN_OR_EQUAL",
        "=": "EQUAL",
        "==": "EQUAL",
        "!=": "NOT_EQUAL",
        "<>": "NOT_EQUAL",
    }
    return mapping.get(operator, "GREATER_THAN")
```

### Aggregation Mapping

```python
def normalize_aggregation(aggregation_type: str) -> Optional[str]:
    """Normalize aggregation type for SDK."""
    if not aggregation_type or aggregation_type.upper() in ("NONE", ""):
        return None
    
    valid = {"SUM", "COUNT", "COUNT_DISTINCT", "AVG", "MEDIAN", 
             "MIN", "MAX", "STDDEV", "FIRST"}
    
    upper = aggregation_type.upper()
    if upper in valid:
        # FIRST maps to None in V2 API
        return None if upper == "FIRST" else upper
    
    raise ValueError(f"Unsupported aggregation_type: {aggregation_type}")
```

## SDK Operations

### Create Alert

```python
def create_alert(ws: WorkspaceClient, alert: AlertV2) -> AlertV2:
    """Create a new alert."""
    try:
        result = ws.alerts_v2.create_alert(alert)
        print(f"✓ Created alert: {result.display_name} (ID: {result.id})")
        return result
    except ResourceAlreadyExists:
        # Alert exists - need to find and update instead
        existing = find_alert_by_name(ws, alert.display_name)
        if existing:
            return update_alert(ws, existing.id, alert)
        raise
```

### Get Alert

```python
def get_alert(ws: WorkspaceClient, alert_id: str) -> AlertV2:
    """Get alert by ID."""
    return ws.alerts_v2.get_alert(alert_id)
```

### List Alerts

```python
def list_all_alerts(ws: WorkspaceClient) -> List[AlertV2]:
    """List all alerts (handles pagination automatically)."""
    return list(ws.alerts_v2.list_alerts())

def find_alert_by_name(ws: WorkspaceClient, display_name: str) -> Optional[AlertV2]:
    """Find alert by display name."""
    for alert in ws.alerts_v2.list_alerts():
        if alert.display_name == display_name:
            return alert
    return None
```

### Update Alert

```python
def update_alert(
    ws: WorkspaceClient, 
    alert_id: str, 
    alert: AlertV2,
    update_mask: str = "display_name,query_text,warehouse_id,condition,notification,schedule"
) -> AlertV2:
    """Update existing alert."""
    result = ws.alerts_v2.update_alert(
        id=alert_id,
        alert=alert,
        update_mask=update_mask
    )
    print(f"✓ Updated alert: {result.display_name} (ID: {alert_id})")
    return result
```

### Delete (Trash) Alert

```python
def delete_alert(ws: WorkspaceClient, alert_id: str) -> None:
    """Soft delete alert (30-day recovery window)."""
    ws.alerts_v2.trash_alert(alert_id)
    print(f"✓ Trashed alert: {alert_id}")
```

## Error Handling

### Common SDK Errors

```python
from databricks.sdk.errors import (
    ResourceAlreadyExists,
    NotFound,
    BadRequest,
    PermissionDenied,
)

def sync_alert_safely(ws: WorkspaceClient, alert: AlertV2) -> Tuple[str, bool, str]:
    """Sync alert with comprehensive error handling."""
    try:
        result = ws.alerts_v2.create_alert(alert)
        return (alert.display_name, True, "CREATED")
    
    except ResourceAlreadyExists:
        # Find existing and update
        existing = find_alert_by_name(ws, alert.display_name)
        if existing:
            update_alert(ws, existing.id, alert)
            return (alert.display_name, True, "UPDATED")
        return (alert.display_name, False, "EXISTS_BUT_NOT_FOUND")
    
    except NotFound as e:
        return (alert.display_name, False, f"NOT_FOUND: {e}")
    
    except BadRequest as e:
        return (alert.display_name, False, f"BAD_REQUEST: {e}")
    
    except PermissionDenied as e:
        return (alert.display_name, False, f"PERMISSION_DENIED: {e}")
    
    except Exception as e:
        return (alert.display_name, False, f"ERROR: {e}")
```

### RESOURCE_ALREADY_EXISTS Handling

When creating alerts that already exist, the SDK raises `ResourceAlreadyExists`. The proper pattern is to catch this and update instead:

```python
def create_or_update_alert(
    ws: WorkspaceClient, 
    alert: AlertV2
) -> Tuple[str, str]:  # Returns (id, action)
    """Create alert or update if exists."""
    try:
        result = ws.alerts_v2.create_alert(alert)
        return (result.id, "CREATED")
    except ResourceAlreadyExists:
        # Find by display_name and update
        existing = find_alert_by_name(ws, alert.display_name)
        if existing:
            result = update_alert(ws, existing.id, alert)
            return (existing.id, "UPDATED")
        raise RuntimeError(f"Alert exists but cannot find: {alert.display_name}")
```

## Notification Subscriptions

### Building Subscriptions

```python
def build_notification_subscriptions(
    channels: List[str],
    destination_map: Dict[str, str]  # channel_id -> databricks_destination_id
) -> List[AlertV2NotificationSubscription]:
    """Build notification subscriptions from channel list."""
    subscriptions = []
    
    for channel in channels:
        if "@" in channel:
            # Direct email address
            subscriptions.append(
                AlertV2NotificationSubscription(
                    user_email=channel
                )
            )
        elif channel in destination_map:
            # Named destination
            subscriptions.append(
                AlertV2NotificationSubscription(
                    destination_id=destination_map[channel]
                )
            )
        else:
            print(f"⚠️ Unknown channel: {channel}")
    
    return subscriptions
```

### Destination Map Loading

```python
def load_destination_map(spark, catalog: str, gold_schema: str) -> Dict[str, str]:
    """Load destination ID to UUID mapping from Delta table."""
    df = spark.sql(f"""
        SELECT destination_id, databricks_destination_id
        FROM {catalog}.{gold_schema}.notification_destinations
        WHERE is_enabled = TRUE
          AND databricks_destination_id IS NOT NULL
    """)
    
    return {row.destination_id: row.databricks_destination_id 
            for row in df.collect()}
```

## Complete Sync Flow

```python
def sync_alerts(
    spark: SparkSession,
    ws: WorkspaceClient,
    catalog: str,
    gold_schema: str,
    warehouse_id: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Sync all enabled alerts from config to Databricks."""
    
    # 1. Load configurations
    configs = load_alert_configs(spark, catalog, gold_schema)
    destination_map = load_destination_map(spark, catalog, gold_schema)
    
    results = {"created": 0, "updated": 0, "errors": []}
    
    # 2. Process each config
    for config in configs:
        try:
            # Build typed AlertV2 object
            alert = build_alert_v2(
                config, warehouse_id, catalog, gold_schema, destination_map
            )
            
            if dry_run:
                print(f"[DRY RUN] Would sync: {config.alert_name}")
                continue
            
            # Create or update
            alert_id, action = create_or_update_alert(ws, alert)
            
            # Update config table
            update_sync_status(
                spark, catalog, gold_schema, 
                config.alert_id, alert_id, "SUCCESS"
            )
            
            if action == "CREATED":
                results["created"] += 1
            else:
                results["updated"] += 1
                
        except Exception as e:
            results["errors"].append((config.alert_id, str(e)))
            update_sync_status(
                spark, catalog, gold_schema,
                config.alert_id, None, "ERROR", str(e)
            )
    
    return results
```

## SDK Reference Links

| Resource | URL |
|----------|-----|
| SDK Documentation | https://databricks-sdk-py.readthedocs.io/ |
| AlertsV2 Reference | https://databricks-sdk-py.readthedocs.io/en/latest/workspace/sql/alerts_v2.html |
| API Documentation | https://docs.databricks.com/api/workspace/alertsv2 |

## Next Steps

- **[06-Notification Destinations](06-notification-destinations.md)**: Channel configuration
- **[07-Query Validation](07-query-validation.md)**: Pre-deployment validation
- **[09-Partial Success Patterns](09-partial-success-patterns.md)**: Error handling


