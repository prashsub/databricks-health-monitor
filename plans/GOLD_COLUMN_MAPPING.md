# Gold Layer Column Mapping Guide

## Purpose

This document maps column names used in Phase 3 plans to the actual Gold layer schema. **Updated after schema enhancements.**

---

## Schema Enhancements Summary

| Enhancement | Status | Details |
|-------------|--------|---------|
| `list_price` added to fact_usage | ✅ Complete | Enriched from system.billing.list_prices |
| `list_cost` added to fact_usage | ✅ Complete | Derived: usage_quantity * list_price |
| JSON → MAP type conversion | ✅ Complete | custom_tags, request_params, job_parameters, query_tags |
| JSON → ARRAY type conversion | ✅ Complete | compute_ids |
| Derived columns added | ✅ Complete | run_date, run_duration_seconds, is_tagged, etc. |

---

## 1. 💰 Cost Domain: `fact_usage`

**Table Status:** ✅ Schema Enhanced

### Key Column Mappings

| Column Name | Type | Source/Derivation | Query Pattern |
|-------------|------|-------------------|---------------|
| `list_price` | DECIMAL(18,6) | system.billing.list_prices | Direct: `f.list_price` |
| `list_cost` | DECIMAL(18,6) | Derived | Direct: `f.list_cost` |
| `custom_tags` | MAP<STRING,STRING> | Native type | Direct: `custom_tags['team']` |
| `is_tagged` | BOOLEAN | Derived | Direct: `WHERE is_tagged = TRUE` |
| `tag_count` | INT | Derived | Direct: `f.tag_count` |
| `usage_metadata_job_id` | STRING | Flattened | Direct: `f.usage_metadata_job_id` |
| `usage_metadata_cluster_id` | STRING | Flattened | Direct: `f.usage_metadata_cluster_id` |
| `usage_metadata_warehouse_id` | STRING | Flattened | Direct: `f.usage_metadata_warehouse_id` |
| `identity_metadata_run_as` | STRING | Flattened | Direct: `f.identity_metadata_run_as` |

### Cost Calculation Patterns

```sql
-- ✅ SIMPLE: Use pre-calculated list_cost
SELECT 
    usage_date,
    workspace_id,
    SUM(list_cost) AS total_cost
FROM fact_usage
GROUP BY usage_date, workspace_id;

-- ✅ Tag-based cost attribution using MAP type
SELECT 
    custom_tags['team'] AS team,
    custom_tags['cost_center'] AS cost_center,
    SUM(list_cost) AS total_cost
FROM fact_usage
WHERE is_tagged = TRUE
GROUP BY custom_tags['team'], custom_tags['cost_center'];

-- ✅ Untagged resources
SELECT workspace_id, SUM(list_cost) AS untagged_cost
FROM fact_usage
WHERE is_tagged = FALSE
GROUP BY workspace_id;
```

---

## 2. 🔒 Security Domain: `fact_audit_logs`

**Table Status:** ✅ Schema Enhanced  
**Note:** Table is `fact_audit_logs` (NOT `fact_audit_events`)

### Key Column Mappings

| Column Name | Type | Source/Derivation | Query Pattern |
|-------------|------|-------------------|---------------|
| `request_params` | MAP<STRING,STRING> | Native type | `request_params['tableName']` |
| `user_identity_email` | STRING | Flattened | Direct: `user_identity_email` |
| `event_time` | TIMESTAMP | Direct | Direct: `event_time` |
| `event_date` | DATE | Direct | Direct: `event_date` |
| `is_sensitive_action` | BOOLEAN | Derived | Direct: `WHERE is_sensitive_action = TRUE` |
| `is_failed_action` | BOOLEAN | Derived | Direct: `WHERE is_failed_action = TRUE` |

### Security Query Patterns

```sql
-- ✅ Table access audit using MAP type
SELECT 
    user_identity_email AS user,
    request_params['tableName'] AS table_name,
    request_params['catalogName'] AS catalog,
    COUNT(*) AS access_count
FROM fact_audit_logs
WHERE action_name = 'getTable'
    AND event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_identity_email, request_params['tableName'], request_params['catalogName'];

-- ✅ Failed actions (pre-computed flag)
SELECT user_identity_email, action_name, COUNT(*) AS failures
FROM fact_audit_logs
WHERE is_failed_action = TRUE
GROUP BY user_identity_email, action_name;
```

---

## 3. ⚡ Performance Domain: `fact_query_history`

**Table Status:** ✅ Schema Enhanced

### Key Column Mappings

| Column Name | Type | Source/Derivation | Query Pattern |
|-------------|------|-------------------|---------------|
| `compute_warehouse_id` | STRING | Flattened | Direct (not `warehouse_id`) |
| `compute_cluster_id` | STRING | Flattened | Direct (not `cluster_id`) |
| `read_bytes` | BIGINT | Direct | Direct (not `bytes_read`) |
| `written_bytes` | BIGINT | Direct | Direct (not `bytes_written`) |
| `spilled_local_bytes` | BIGINT | Direct | Direct |
| `execution_status` | STRING | Direct | Direct (not `status`) |
| `query_tags` | MAP<STRING,STRING> | Native type | `query_tags['tag_key']` |

### Performance Query Patterns

```sql
-- ✅ Slow queries with correct column names
SELECT 
    compute_warehouse_id AS warehouse_id,
    executed_by,
    total_duration_ms,
    read_bytes,
    spilled_local_bytes,
    execution_status
FROM fact_query_history
WHERE total_duration_ms > 60000  -- > 1 minute
    AND execution_status = 'FINISHED';

-- ✅ Query tags using MAP type
SELECT 
    query_tags['application'] AS app,
    AVG(total_duration_ms) AS avg_duration
FROM fact_query_history
WHERE query_tags IS NOT NULL
GROUP BY query_tags['application'];
```

---

## 4. 🔄 Reliability Domain: `fact_job_run_timeline`

**Table Status:** ✅ Schema Enhanced

### Key Column Mappings

| Column Name | Type | Source/Derivation | Query Pattern |
|-------------|------|-------------------|---------------|
| `period_start_time` | TIMESTAMP | Direct | Use instead of `run_start_time` |
| `period_end_time` | TIMESTAMP | Direct | Use instead of `run_end_time` |
| `run_date` | DATE | Derived | Direct: `run_date` |
| `run_duration_seconds` | BIGINT | Derived | Direct: `run_duration_seconds` |
| `run_duration_minutes` | DOUBLE | Derived | Direct: `run_duration_minutes` |
| `is_success` | BOOLEAN | Derived | Direct: `WHERE is_success = TRUE` |
| `compute_ids` | ARRAY<STRING> | Native type | `array_contains(compute_ids, 'id')` |
| `job_parameters` | MAP<STRING,STRING> | Native type | `job_parameters['param']` |

### Reliability Query Patterns

```sql
-- ✅ Job performance with pre-computed columns
SELECT 
    job_id,
    run_date,
    AVG(run_duration_minutes) AS avg_duration_min,
    SUM(CASE WHEN is_success THEN 1 ELSE 0 END) / COUNT(*) * 100 AS success_rate
FROM fact_job_run_timeline
WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY job_id, run_date;

-- ✅ Failed jobs with duration
SELECT 
    job_id,
    run_id,
    run_duration_seconds,
    result_state,
    termination_code
FROM fact_job_run_timeline
WHERE is_success = FALSE
    AND run_date = CURRENT_DATE();

-- ✅ Jobs using specific cluster (ARRAY type)
SELECT job_id, run_id
FROM fact_job_run_timeline
WHERE array_contains(compute_ids, 'cluster-123');
```

---

## Complete Column Reference

### fact_usage (Billing)

| Old/Expected | New/Actual | Type |
|--------------|------------|------|
| `list_price` | `list_price` ✅ | DECIMAL(18,6) |
| `list_cost` | `list_cost` ✅ | DECIMAL(18,6) |
| `custom_tags_json` | `custom_tags` | MAP<STRING,STRING> |
| `job_id` | `usage_metadata_job_id` | STRING |
| `cluster_id` | `usage_metadata_cluster_id` | STRING |
| `warehouse_id` | `usage_metadata_warehouse_id` | STRING |
| `run_as` | `identity_metadata_run_as` | STRING |

### fact_audit_logs (Security)

| Old/Expected | New/Actual | Type |
|--------------|------------|------|
| `fact_audit_events` | `fact_audit_logs` | TABLE NAME |
| `request_params_json` | `request_params` | MAP<STRING,STRING> |
| `user_id` | `user_identity_email` | STRING |
| `event_timestamp` | `event_time` | TIMESTAMP |

### fact_query_history (Performance)

| Old/Expected | New/Actual | Type |
|--------------|------------|------|
| `warehouse_id` | `compute_warehouse_id` | STRING |
| `cluster_id` | `compute_cluster_id` | STRING |
| `bytes_read` | `read_bytes` | BIGINT |
| `bytes_written` | `written_bytes` | BIGINT |
| `status` | `execution_status` | STRING |
| `query_tags_json` | `query_tags` | MAP<STRING,STRING> |

### fact_job_run_timeline (Reliability)

| Old/Expected | New/Actual | Type |
|--------------|------------|------|
| `run_start_time` | `period_start_time` | TIMESTAMP |
| `run_end_time` | `period_end_time` | TIMESTAMP |
| `run_duration_seconds` | `run_duration_seconds` ✅ | BIGINT (derived) |
| `run_date` | `run_date` ✅ | DATE (derived) |
| `compute_ids_json` | `compute_ids` | ARRAY<STRING> |
| `job_parameters_json` | `job_parameters` | MAP<STRING,STRING> |

---

## Query Pattern Summary

### MAP Type Access (replaces get_json_object)

```sql
-- ❌ OLD: JSON parsing
SELECT get_json_object(custom_tags_json, '$.team') AS team

-- ✅ NEW: Direct MAP access
SELECT custom_tags['team'] AS team
```

### ARRAY Type Access

```sql
-- Check if array contains value
WHERE array_contains(compute_ids, 'cluster-123')

-- Explode array for joins
FROM fact_job_run_timeline
LATERAL VIEW explode(compute_ids) AS cluster_id
```

### Pre-computed Derived Columns

```sql
-- ❌ OLD: Runtime calculation
SELECT (UNIX_TIMESTAMP(period_end_time) - UNIX_TIMESTAMP(period_start_time)) AS duration

-- ✅ NEW: Pre-computed column
SELECT run_duration_seconds
```

---

## Implementation Notes

### Gold Merge Script Changes Required

The following transformations must be implemented in the Bronze → Gold merge scripts:

#### fact_usage merge:
```python
# Add list_price from system.billing.list_prices
.join(list_prices, join_condition, "left")
.withColumn("list_price", col("lp.pricing.default"))
.withColumn("list_cost", col("usage_quantity") * col("list_price"))
.withColumn("is_tagged", size(col("custom_tags")) > 0)
.withColumn("tag_count", size(col("custom_tags")))
```

#### fact_job_run_timeline merge:
```python
# Add derived duration columns
.withColumn("run_date", to_date(col("period_start_time")))
.withColumn("run_duration_seconds", 
    unix_timestamp(col("period_end_time")) - unix_timestamp(col("period_start_time")))
.withColumn("run_duration_minutes", col("run_duration_seconds") / 60.0)
.withColumn("is_success", col("result_state") == "SUCCESS")
```

#### fact_audit_logs merge:
```python
# Add derived security columns
.withColumn("is_sensitive_action", 
    col("action_name").isin(["grantPermission", "revokePermission", "delete", "getSecret"]))
.withColumn("is_failed_action", 
    (col("response_status_code") >= 400) | col("response_error_message").isNotNull())
```
