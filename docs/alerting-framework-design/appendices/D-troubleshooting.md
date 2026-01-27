# Appendix D - Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: SDK Import Error

**Error:**
```
ImportError: cannot import name 'AlertV2' from 'databricks.sdk.service.sql'
```

**Cause:** Serverless environment has older pre-installed SDK (< 0.40.0)

**Solution:**
```python
# Add to top of notebook
%pip install --upgrade databricks-sdk>=0.40.0 --quiet
%restart_python
```

**Verification:**
```python
from databricks.sdk.service.sql import AlertV2
print("SDK version is compatible!")
```

---

### Issue 2: Query Validation Fails

**Error:**
```
UNRESOLVED_COLUMN: Column 'event_time' cannot be resolved
```

**Cause:** Column name doesn't match actual table schema

**Solution:**
1. Check table schema:
   ```sql
   DESCRIBE TABLE catalog.schema.fact_audit_logs;
   ```
2. Update alert query to use correct column name
3. Re-run validation

**Prevention:** Always validate column names against YAML schema or DESCRIBE TABLE.

---

### Issue 3: RESOURCE_ALREADY_EXISTS

**Error:**
```
HTTP 400: Alert with name 'Daily Cost Spike Alert' already exists
```

**Cause:** Alert was created in previous run or manually

**Solution:** This is handled automatically by the sync engine - it will update instead of create.

**Manual Fix:**
```sql
-- Check sync status
SELECT alert_id, databricks_alert_id, last_sync_status 
FROM alert_configurations 
WHERE alert_name = 'Daily Cost Spike Alert';

-- If needed, clear to force recreate
UPDATE alert_configurations
SET databricks_alert_id = NULL,
    last_synced_at = NULL
WHERE alert_id = 'COST-001';
```

---

### Issue 4: SQL Escaping (LIKE Patterns)

**Error:**
```
PARSE_SYNTAX_ERROR: Syntax error at or near '%'
```

**Cause:** SQL INSERT with string escaping strips quotes from LIKE patterns

**Example:**
```sql
-- Original: WHERE sku_name LIKE '%ALL_PURPOSE%'
-- After INSERT: WHERE sku_name LIKE %ALL_PURPOSE%  (invalid!)
```

**Solution:** Use DataFrame insertion (not SQL INSERT):
```python
df = spark.createDataFrame(rows, schema=ALERT_CONFIG_SCHEMA)
df.write.mode("append").saveAsTable("alert_configurations")
```

---

### Issue 5: Alert Never Triggers

**Symptoms:** Alert is enabled but never sends notifications

**Diagnosis Checklist:**
1. Run query manually - does it return rows?
   ```sql
   -- Test the query
   SELECT * FROM (
       {your_alert_query}
   );
   ```

2. Check condition logic:
   ```sql
   SELECT 
       threshold_column,
       CASE 
           WHEN threshold_column > threshold_value THEN 'WOULD_TRIGGER'
           ELSE 'OK'
       END as status
   FROM ({your_alert_query});
   ```

3. Verify schedule:
   ```sql
   SELECT schedule_cron, schedule_timezone, pause_status
   FROM alert_configurations
   WHERE alert_id = 'YOUR-ALERT-ID';
   ```

4. Check warehouse status - is it running?

**Common Fixes:**
- Missing HAVING clause (query always returns rows)
- Wrong operator direction (> instead of <)
- Threshold too high/low
- Alert is PAUSED
- Notification destination not configured

---

### Issue 6: Update Mask Missing

**Error:**
```
HTTP 400: Update mask is required
```

**Cause:** PATCH request without update_mask parameter

**Solution:** SDK handles this automatically with:
```python
ws.alerts_v2.update_alert(
    id=alert_id,
    alert=alert,
    update_mask="display_name,query_text,warehouse_id,condition,notification,schedule"
)
```

---

### Issue 7: Notification Not Received

**Diagnosis:**
1. Check destination configuration:
   ```sql
   SELECT * FROM notification_destinations
   WHERE destination_id = 'your_channel';
   ```

2. Verify databricks_destination_id is populated:
   ```sql
   SELECT destination_id, databricks_destination_id
   FROM notification_destinations
   WHERE databricks_destination_id IS NULL;
   ```

3. Check alert configuration:
   ```sql
   SELECT alert_id, notification_channels
   FROM alert_configurations
   WHERE alert_id = 'YOUR-ALERT-ID';
   ```

**Solutions:**
- Run notification sync job if UUID is NULL
- Verify email/webhook configuration
- Check notification channel spelling

---

### Issue 8: Partial Success - Some Alerts Fail

**Symptoms:** Job succeeds but some alerts show ERROR status

**Diagnosis:**
```sql
SELECT alert_id, last_sync_error
FROM alert_configurations
WHERE last_sync_status = 'ERROR';
```

**Solution:** Fix individual alerts and re-run deployment:
```bash
databricks bundle run -t dev alerting_deploy_job
```

---

### Issue 9: Sync Duration Too Long

**Symptoms:** Sync takes > 5 minutes for 30 alerts

**Solution:** Enable parallel sync:
```yaml
# In alerting_deploy_job.yml
base_parameters:
  enable_parallel: "true"
  parallel_workers: "10"
```

**Trade-off:** May hit API rate limits with too many workers.

---

### Issue 10: Wrong API Endpoint

**Error:**
```
HTTP 404: Not found
```

**Cause:** Using wrong V2 endpoint

**Incorrect:**
- `/api/2.0/sql/alerts`
- `/api/2.0/sql/alerts-v2`

**Correct:**
```
/api/2.0/alerts
```

---

## Debug Checklist

When an alert fails:

- [ ] Query syntax valid? → Run EXPLAIN
- [ ] Column names correct? → DESCRIBE TABLE
- [ ] Table exists? → SHOW TABLES
- [ ] Placeholders rendered? → Check query_text in error
- [ ] Notification configured? → Check destination table
- [ ] Schedule correct? → Verify cron expression
- [ ] Permissions? → Check UC grants

## Getting Help

### Log Locations

| Log Type | Location |
|----------|----------|
| Job logs | Databricks UI > Workflows > Job Runs |
| Alert sync logs | alert_sync_metrics table |
| Validation logs | alert_validation_results table |
| Config table | alert_configurations (last_sync_error column) |

### Useful Queries

```sql
-- Recent errors
SELECT alert_id, last_sync_error, last_synced_at
FROM alert_configurations
WHERE last_sync_status = 'ERROR'
ORDER BY last_synced_at DESC;

-- Validation failures
SELECT alert_id, error_message
FROM alert_validation_results
WHERE is_valid = FALSE;

-- Sync performance
SELECT 
    AVG(total_duration_seconds) as avg_duration,
    AVG(success_count * 100.0 / total_alerts) as avg_success_rate
FROM alert_sync_metrics
WHERE sync_started_at >= CURRENT_DATE() - 7;
```

## Support Contacts

- **Issues**: Create GitHub issue with `[ALERTING]` prefix
- **Questions**: #data-engineering Slack channel
- **Owner**: Data Platform Team


