# 06 - Notification Destinations

## Overview

Notification destinations define where alerts are sent when triggered. The framework supports multiple channel types with both direct addressing (email) and named destinations (Slack, Webhook, etc.).

## Destination Types

| Type | Description | Configuration |
|------|-------------|---------------|
| **EMAIL** | Direct email addresses | Single or list of emails |
| **SLACK** | Slack channel via webhook | Webhook URL |
| **WEBHOOK** | Custom HTTP endpoint | URL + optional auth |
| **TEAMS** | Microsoft Teams | Connector URL |
| **PAGERDUTY** | PagerDuty incidents | Integration key |

## Two Approaches

### Approach 1: Direct Email (Simplest)

Include email addresses directly in `notification_channels`:

```sql
-- In alert_configurations
notification_channels = array('alice@company.com', 'bob@company.com')
```

**Pros:**
- No additional setup
- Simple for individual alerts
- Self-documenting

**Cons:**
- Repetitive for team alerts
- Hard to update across multiple alerts
- No abstraction

### Approach 2: Named Destinations (Recommended)

Create entries in `notification_destinations` table and reference by ID:

```sql
-- Step 1: Create destination
INSERT INTO notification_destinations (
    destination_id, destination_name, destination_type,
    databricks_destination_id, config_json,
    owner, is_enabled, created_by, created_at
) VALUES (
    'finops_team',
    'FinOps Team Alerts',
    'EMAIL',
    NULL,  -- Will be populated by sync
    '{"addresses": ["finops@company.com", "finops-lead@company.com"]}',
    'finops@company.com',
    TRUE,
    'system',
    CURRENT_TIMESTAMP()
);

-- Step 2: Reference in alerts
notification_channels = array('finops_team')
```

**Pros:**
- Single update affects all referencing alerts
- Abstraction for team ownership
- Supports all channel types

**Cons:**
- Additional setup step
- Requires destination sync job

## notification_destinations Table

### Schema

```sql
CREATE TABLE ${catalog}.${gold_schema}.notification_destinations (
    -- Identity
    destination_id STRING NOT NULL,
    -- Internal ID (e.g., 'finops_team', 'oncall_slack')
    
    destination_name STRING NOT NULL,
    -- Human-readable display name
    
    destination_type STRING NOT NULL,
    -- Type: EMAIL, SLACK, WEBHOOK, TEAMS, PAGERDUTY
    
    -- Databricks Integration
    databricks_destination_id STRING,
    -- Workspace destination UUID (from Databricks)
    -- Populated by sync job, NULL initially
    
    config_json STRING,
    -- Type-specific configuration as JSON
    
    -- Ownership
    owner STRING NOT NULL,
    is_enabled BOOLEAN NOT NULL,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING,
    updated_at TIMESTAMP,
    tags MAP<STRING, STRING>,
    
    CONSTRAINT pk_notification_destinations PRIMARY KEY (destination_id) NOT ENFORCED
)
USING DELTA;
```

### Configuration by Type

#### EMAIL

```sql
INSERT INTO notification_destinations VALUES (
    'platform_team',
    'Platform Engineering Team',
    'EMAIL',
    NULL,
    '{"addresses": ["platform@company.com", "platform-lead@company.com"]}',
    'platform@company.com',
    TRUE,
    'system',
    CURRENT_TIMESTAMP(),
    NULL, NULL, NULL
);
```

#### SLACK

```sql
INSERT INTO notification_destinations VALUES (
    'alerts_slack',
    '#databricks-alerts Slack Channel',
    'SLACK',
    NULL,
    '{"url": "https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_WEBHOOK_TOKEN"}',  -- gitleaks:allow
    'platform@company.com',
    TRUE,
    'system',
    CURRENT_TIMESTAMP(),
    NULL, NULL, NULL
);
```

#### WEBHOOK

```sql
INSERT INTO notification_destinations VALUES (
    'custom_webhook',
    'Custom Alert Handler',
    'WEBHOOK',
    NULL,
    '{
        "url": "https://alerts.company.com/webhook",
        "auth_type": "bearer",
        "auth_token_secret": "alerts/webhook_token"
    }',
    'platform@company.com',
    TRUE,
    'system',
    CURRENT_TIMESTAMP(),
    NULL, NULL, NULL
);
```

#### TEAMS

```sql
INSERT INTO notification_destinations VALUES (
    'teams_channel',
    'Engineering Alerts - Teams',
    'TEAMS',
    NULL,
    '{"url": "https://company.webhook.office.com/webhookb2/..."}',
    'platform@company.com',
    TRUE,
    'system',
    CURRENT_TIMESTAMP(),
    NULL, NULL, NULL
);
```

#### PAGERDUTY

```sql
INSERT INTO notification_destinations VALUES (
    'oncall_pagerduty',
    'On-Call PagerDuty',
    'PAGERDUTY',
    NULL,
    '{"integration_key": "your-pagerduty-integration-key"}',
    'oncall@company.com',
    TRUE,
    'system',
    CURRENT_TIMESTAMP(),
    NULL, NULL, NULL
);
```

## Channel Resolution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CHANNEL RESOLUTION FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

  notification_channels = ['finops@co.com', 'finops_team', 'oncall_slack']
                               │                  │                │
                               ▼                  ▼                ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Contains '@'?   │  │ Lookup in       │  │ Lookup in       │
│ YES → Direct    │  │ notification_   │  │ notification_   │
│ email           │  │ destinations    │  │ destinations    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AlertV2         │  │ AlertV2         │  │ AlertV2         │
│ Notification    │  │ Notification    │  │ Notification    │
│ Subscription:   │  │ Subscription:   │  │ Subscription:   │
│ user_email=     │  │ destination_id= │  │ destination_id= │
│ 'finops@co.com' │  │ '<uuid>'        │  │ '<uuid>'        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Implementation

### build_notification_subscriptions

```python
from typing import Dict, List, Optional
from databricks.sdk.service.sql import AlertV2NotificationSubscription


def build_notification_subscriptions(
    channels: Optional[List[str]],
    destination_map: Dict[str, str]  # destination_id -> databricks_destination_id
) -> List[AlertV2NotificationSubscription]:
    """
    Build notification subscriptions from channel list.
    
    Args:
        channels: List of channel IDs or email addresses
        destination_map: Mapping of internal IDs to Databricks UUIDs
        
    Returns:
        List of SDK subscription objects
    """
    if not channels:
        return []
    
    subscriptions = []
    
    for channel in channels:
        if "@" in channel:
            # Direct email address
            subscriptions.append(
                AlertV2NotificationSubscription(user_email=channel)
            )
        elif channel in destination_map:
            # Named destination
            subscriptions.append(
                AlertV2NotificationSubscription(
                    destination_id=destination_map[channel]
                )
            )
        else:
            # Unknown channel - log warning but don't fail
            print(f"⚠️ Warning: Unknown notification channel '{channel}' - skipping")
    
    return subscriptions
```

### Loading Destination Map

```python
def load_destination_map(
    spark: SparkSession, 
    catalog: str, 
    gold_schema: str
) -> Dict[str, str]:
    """
    Load destination_id to databricks_destination_id mapping.
    
    Returns:
        Dictionary mapping internal IDs to Databricks UUIDs
    """
    query = f"""
        SELECT 
            destination_id,
            databricks_destination_id
        FROM {catalog}.{gold_schema}.notification_destinations
        WHERE is_enabled = TRUE
          AND databricks_destination_id IS NOT NULL
    """
    
    df = spark.sql(query)
    
    return {
        row.destination_id: row.databricks_destination_id 
        for row in df.collect()
    }
```

## Destination Sync Process

Named destinations require a sync step to create them in Databricks and obtain UUIDs:

```python
def sync_notification_destinations(
    spark: SparkSession,
    ws: WorkspaceClient,
    catalog: str,
    gold_schema: str
) -> Dict[str, int]:
    """Sync notification destinations to Databricks."""
    
    # Load destinations needing sync
    df = spark.sql(f"""
        SELECT destination_id, destination_name, destination_type, config_json
        FROM {catalog}.{gold_schema}.notification_destinations
        WHERE is_enabled = TRUE
          AND databricks_destination_id IS NULL
    """)
    
    results = {"created": 0, "errors": 0}
    
    for row in df.collect():
        try:
            # Create destination in Databricks
            dest = create_databricks_destination(ws, row)
            
            # Update table with UUID
            spark.sql(f"""
                UPDATE {catalog}.{gold_schema}.notification_destinations
                SET databricks_destination_id = '{dest.id}',
                    updated_at = CURRENT_TIMESTAMP()
                WHERE destination_id = '{row.destination_id}'
            """)
            
            results["created"] += 1
            
        except Exception as e:
            print(f"❌ Error creating destination {row.destination_id}: {e}")
            results["errors"] += 1
    
    return results
```

## Severity-Based Routing

A common pattern is routing alerts to different channels based on severity:

```python
def get_channels_for_severity(
    base_channels: List[str],
    severity: str
) -> List[str]:
    """Augment channels based on severity."""
    
    channels = base_channels.copy()
    
    if severity == "CRITICAL":
        # Add PagerDuty for critical
        channels.append("oncall_pagerduty")
    elif severity == "WARNING":
        # Add Slack for warnings
        channels.append("alerts_slack")
    
    return channels
```

**Alert Configuration Example:**

```sql
-- CRITICAL alert → page on-call
INSERT INTO alert_configurations (
    ...,
    severity = 'CRITICAL',
    notification_channels = array('platform_team', 'oncall_pagerduty'),
    ...
);

-- WARNING alert → Slack only
INSERT INTO alert_configurations (
    ...,
    severity = 'WARNING',
    notification_channels = array('alerts_slack'),
    ...
);

-- INFO alert → email digest
INSERT INTO alert_configurations (
    ...,
    severity = 'INFO',
    notification_channels = array('weekly_digest@company.com'),
    ...
);
```

## Best Practices

### 1. Use Named Destinations for Teams

```sql
-- ✅ Good: Named destination
notification_channels = array('finops_team')

-- ❌ Avoid: Multiple individual emails
notification_channels = array('alice@co.com', 'bob@co.com', 'charlie@co.com')
```

### 2. Include Fallback Email

```sql
-- Always include at least one direct email as fallback
notification_channels = array('finops_team', 'finops-oncall@company.com')
```

### 3. Match Severity to Channel Type

| Severity | Recommended Channels |
|----------|----------------------|
| CRITICAL | PagerDuty + Slack + Email |
| WARNING | Slack + Email |
| INFO | Email only |

### 4. Test Destinations Before Use

```python
def test_destination(ws: WorkspaceClient, destination_id: str) -> bool:
    """Send test notification to verify destination works."""
    try:
        # Implementation depends on destination type
        # Most destinations support a test/ping endpoint
        pass
    except Exception as e:
        print(f"Destination test failed: {e}")
        return False
    return True
```

### 5. Document Destination Ownership

```sql
-- Include owner and tags for accountability
INSERT INTO notification_destinations (
    ...,
    owner = 'finops@company.com',
    tags = map('team', 'finops', 'oncall_rotation', 'weekly'),
    ...
);
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Alert created but no notification | Destination UUID not populated | Run destination sync job |
| Unknown channel warning | destination_id not in table | Add to notification_destinations |
| Slack not receiving | Webhook URL expired | Update config_json with new URL |
| Email not received | User not in workspace | Use destination_id instead |

### Verification Query

```sql
-- Check destination sync status
SELECT 
    d.destination_id,
    d.destination_name,
    d.destination_type,
    CASE 
        WHEN d.databricks_destination_id IS NOT NULL THEN '✓ Synced'
        ELSE '❌ Not Synced'
    END as sync_status,
    COUNT(DISTINCT a.alert_id) as alert_count
FROM notification_destinations d
LEFT JOIN alert_configurations a 
    ON array_contains(a.notification_channels, d.destination_id)
WHERE d.is_enabled = TRUE
GROUP BY d.destination_id, d.destination_name, d.destination_type, 
         d.databricks_destination_id
ORDER BY alert_count DESC;
```

## Next Steps

- **[07-Query Validation](07-query-validation.md)**: Pre-deployment validation
- **[08-Hierarchical Job Architecture](08-hierarchical-job-architecture.md)**: Job structure
- **[12-Deployment and Operations](12-deployment-and-operations.md)**: Production deployment


