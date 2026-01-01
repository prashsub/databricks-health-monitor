# 09 - Partial Success Patterns

## Overview

When syncing multiple alerts, a single failure shouldn't block the entire deployment. The alerting framework implements **partial success patterns** that allow the majority of alerts to deploy even when some fail.

## The Problem

### Without Partial Success

```python
# ❌ Single failure stops everything
for alert in alerts:
    try:
        ws.alerts_v2.create_alert(alert)
    except Exception as e:
        raise RuntimeError(f"Failed: {e}")  # Stops at first failure
```

**Issues:**
- 28 valid alerts don't deploy because 1 failed
- Must fix every issue before any deployment
- No visibility into which alerts would work

### With Partial Success

```python
# ✅ Continue on failure, report at end
results = []
for alert in alerts:
    try:
        ws.alerts_v2.create_alert(alert)
        results.append((alert.name, True, None))
    except Exception as e:
        results.append((alert.name, False, str(e)))

# Evaluate overall success
success_rate = sum(1 for _, ok, _ in results if ok) / len(results)
if success_rate < 0.90:
    raise RuntimeError("Too many failures")
```

## Success Threshold

### Default: 90%

The framework uses a **90% success threshold**:

| Total Alerts | Min Successes | Max Failures |
|--------------|---------------|--------------|
| 10 | 9 | 1 |
| 20 | 18 | 2 |
| 29 | 26 | 3 |
| 50 | 45 | 5 |

### Rationale

- **Too strict (100%)**: One typo blocks entire deployment
- **Too lenient (50%)**: Major issues go unnoticed
- **90%**: Balances reliability with practicality

## Implementation

### sync_sql_alerts.py Pattern

```python
def sync_alerts(
    spark: SparkSession,
    ws: WorkspaceClient,
    catalog: str,
    gold_schema: str,
    warehouse_id: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Sync alerts with partial success handling."""
    
    configs = load_alert_configs(spark, catalog, gold_schema)
    destination_map = load_destination_map(spark, catalog, gold_schema)
    
    successes = []
    errors = []
    
    for config in configs:
        try:
            alert = build_alert_v2(config, warehouse_id, catalog, gold_schema, destination_map)
            
            if dry_run:
                print(f"[DRY RUN] Would sync: {config.alert_name}")
                successes.append(config.alert_id)
                continue
            
            # Attempt create/update
            alert_id, action = create_or_update_alert(ws, alert)
            successes.append(config.alert_id)
            
            # Update config table
            update_sync_status(spark, catalog, gold_schema, config.alert_id, alert_id, "SUCCESS")
            
        except Exception as e:
            errors.append((config.alert_id, str(e)))
            update_sync_status(spark, catalog, gold_schema, config.alert_id, None, "ERROR", str(e))
    
    # Evaluate success rate
    total = len(configs)
    success_count = len(successes)
    error_count = len(errors)
    success_rate = success_count / total if total > 0 else 0
    
    print("\n" + "=" * 60)
    print(f"SYNC SUMMARY")
    print(f"  Total:     {total}")
    print(f"  Success:   {success_count} ({success_rate:.1%})")
    print(f"  Errors:    {error_count}")
    print("=" * 60)
    
    # Handle based on success rate
    if errors:
        print(f"\nFailed alerts ({len(errors)}):")
        for aid, msg in errors[:25]:  # Limit output
            print(f"  - {aid}: {msg[:200]}")
    
    if success_rate < 0.90:
        raise RuntimeError(
            f"SQL Alert sync failed: {success_rate:.1%} success rate "
            f"(threshold: 90%). Failed: {', '.join(aid for aid, _ in errors)}"
        )
    elif errors:
        print(f"\n⚠️ WARNING: Completed with {len(errors)} failures.")
        print(f"   Failed alert IDs: {', '.join(aid for aid, _ in errors)}")
    
    print("\n✅ Alert sync completed successfully!")
    
    return {
        "total": total,
        "success_count": success_count,
        "error_count": error_count,
        "success_rate": success_rate,
        "errors": errors
    }
```

## Error Logging

### Structured Error Output

```
================================================================
SYNC SUMMARY
  Total:     29
  Success:   28 (96.6%)
  Errors:    1
================================================================

Failed alerts (1):
  - CLUSTER-002: RESOURCE_ALREADY_EXISTS: Alert with name 'Overprovisioned Cluster...' already exists

⚠️ WARNING: Completed with 1 failures.
   Failed alert IDs: CLUSTER-002

✅ Alert sync completed successfully!
```

### Key Information Logged

| Field | Purpose |
|-------|---------|
| **Alert ID** | Which alert failed |
| **Error Type** | Category of failure |
| **Error Message** | Specific error details |
| **Summary Counts** | Total/Success/Error |
| **Success Rate** | Percentage for threshold check |

## Error Handling Strategies

### Strategy 1: Log and Continue

```python
try:
    create_alert(ws, alert)
except Exception as e:
    print(f"⚠️ Failed: {alert.name}: {e}")
    errors.append((alert.name, str(e)))
    # Continue to next alert
```

**Use for:** Non-critical failures, recoverable errors

### Strategy 2: Classify and Decide

```python
try:
    create_alert(ws, alert)
except ResourceAlreadyExists:
    # Expected - update instead
    update_alert(ws, existing_id, alert)
except PermissionDenied as e:
    # Critical - cannot proceed
    raise
except BadRequest as e:
    # Log and continue
    errors.append((alert.name, f"Bad config: {e}"))
```

**Use for:** Different error types need different handling

### Strategy 3: Exponential Backoff

```python
def create_with_retry(ws, alert, max_retries=3):
    for attempt in range(max_retries):
        try:
            return ws.alerts_v2.create_alert(alert)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s
```

**Use for:** Transient failures, rate limiting

## Common Failure Scenarios

### Scenario 1: RESOURCE_ALREADY_EXISTS

**Cause:** Alert was created manually or in previous run

```python
except ResourceAlreadyExists:
    existing = find_alert_by_name(ws, alert.display_name)
    if existing:
        update_alert(ws, existing.id, alert)
    else:
        errors.append((config.alert_id, "Exists but cannot find"))
```

### Scenario 2: Invalid Query

**Cause:** Query validation missed an issue

```python
except BadRequest as e:
    if "query" in str(e).lower():
        errors.append((config.alert_id, f"Invalid query: {e}"))
    else:
        raise
```

### Scenario 3: Missing Destination

**Cause:** Notification destination not synced

```python
if channel not in destination_map:
    print(f"⚠️ Unknown channel: {channel} - using direct email fallback")
    # Continue without this channel
```

## Monitoring Failed Alerts

### Query Config Table for Errors

```sql
-- All alerts that failed to sync
SELECT 
    alert_id,
    alert_name,
    last_sync_status,
    last_sync_error,
    last_synced_at
FROM alert_configurations
WHERE last_sync_status = 'ERROR'
ORDER BY last_synced_at DESC;
```

### Dashboard Query

```sql
-- Sync status distribution
SELECT 
    last_sync_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
FROM alert_configurations
WHERE is_enabled = TRUE
GROUP BY last_sync_status;
```

## Recovery Procedures

### Re-sync Single Alert

```python
# After fixing the configuration
def resync_single_alert(spark, ws, catalog, gold_schema, warehouse_id, alert_id):
    config = spark.sql(f"""
        SELECT * FROM {catalog}.{gold_schema}.alert_configurations
        WHERE alert_id = '{alert_id}'
    """).first()
    
    alert = build_alert_v2(config, warehouse_id, catalog, gold_schema, {})
    create_or_update_alert(ws, alert)
```

### Disable and Skip Problem Alert

```sql
-- Disable problematic alert
UPDATE alert_configurations
SET is_enabled = FALSE,
    updated_by = 'admin',
    updated_at = CURRENT_TIMESTAMP()
WHERE alert_id = 'CLUSTER-002';
```

### Force Re-seed and Re-sync

```bash
# If data is corrupted, force reseed
databricks bundle run -t dev seed_all_alerts_job \
  --parameters force_reseed=true

# Then re-sync
databricks bundle run -t dev sql_alert_deployment_job
```

## Configuring Threshold

### Environment Variable

```yaml
# In job YAML
base_parameters:
  success_threshold: "0.90"  # 90%
```

### Runtime Override

```python
# In sync script
success_threshold = float(dbutils.widgets.get("success_threshold") or "0.90")

if success_rate < success_threshold:
    raise RuntimeError("Below threshold")
```

## Best Practices

### 1. Always Log Failed IDs

```python
if errors:
    failed_ids = [aid for aid, _ in errors]
    print(f"Failed IDs: {', '.join(failed_ids)}")
```

### 2. Update Config Table Status

```python
# Always update status, even on failure
update_sync_status(spark, catalog, gold_schema, 
                   alert_id, None, "ERROR", str(e))
```

### 3. Include Error in Exit Message

```python
if errors:
    dbutils.notebook.exit(f"PARTIAL_SUCCESS: {len(errors)} failures: {failed_ids}")
else:
    dbutils.notebook.exit("SUCCESS")
```

### 4. Don't Hide Failures

```python
# ❌ Bad: Silent failure
try:
    create_alert(ws, alert)
except:
    pass  # Hidden!

# ✅ Good: Logged failure
try:
    create_alert(ws, alert)
except Exception as e:
    print(f"❌ {alert.name}: {e}")
    errors.append((alert.name, str(e)))
```

## Next Steps

- **[10-Alert Templates](10-alert-templates.md)**: Pre-built templates
- **[11-Implementation Guide](11-implementation-guide.md)**: Step-by-step setup
- **[12-Deployment and Operations](12-deployment-and-operations.md)**: Production deployment


