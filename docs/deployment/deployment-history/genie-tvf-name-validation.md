# Genie TVF Name Validation Against Deployed Assets

**Date:** January 7, 2026  
**Source:** `docs/actual_assets.md` - Section 4: Table-Valued Functions  
**Total FUNCTION_NOT_FOUND Errors:** 20

---

## ✅ Summary

| Status | Count | Description |
|--------|-------|-------------|
| ❌ **Wrong Name** | 17 | Function name is incorrect - needs fix |
| ✅ **Exists** | 3 | Function exists - likely wrong signature or TABLE() wrapper issue |
| 🔍 **Not Deployed** | 0 | Function genuinely doesn't exist |

---

## 🔴 Security Domain (7 errors)

### ❌ 1. `get_user_activity` → `get_user_activity_summary`

**Error:** `get_user_activity` not found  
**Correct Name:** `get_user_activity_summary`  
**Signature:** `(start_date STRING, end_date STRING, top_n INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_user_activity"
→
"${catalog}.${gold_schema}.get_user_activity_summary"
```

---

### ❌ 2. `get_pii_access_events` → `get_sensitive_table_access`

**Error:** `get_pii_access_events` not found  
**Correct Name:** `get_sensitive_table_access`  
**Signature:** `(start_date STRING, end_date STRING, table_pattern STRING)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_pii_access_events"
→
"${catalog}.${gold_schema}.get_sensitive_table_access"
```

---

### ❌ 3. `get_failed_authentication_events` → `get_failed_actions`

**Error:** `get_failed_authentication_events` not found  
**Correct Name:** `get_failed_actions`  
**Signature:** `(start_date STRING, end_date STRING, user_filter STRING)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_failed_authentication_events"
→
"${catalog}.${gold_schema}.get_failed_actions"
```

---

### ❌ 4. `get_permission_change_events` → `get_permission_changes`

**Error:** `get_permission_change_events` not found  
**Correct Name:** `get_permission_changes`  
**Signature:** `(start_date STRING, end_date STRING)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_permission_change_events"
→
"${catalog}.${gold_schema}.get_permission_changes"
```

---

### ❌ 5. `get_service_account_activity` → `get_service_account_audit`

**Error:** `get_service_account_activity` not found  
**Correct Name:** `get_service_account_audit`  
**Signature:** `(days_back INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_service_account_activity"
→
"${catalog}.${gold_schema}.get_service_account_audit"
```

---

### ❌ 6. `get_data_export_events` → ⚠️ **NOT DEPLOYED**

**Error:** `get_data_export_events` not found  
**Status:** ⚠️ No equivalent function exists  
**Action:** Remove queries using this function OR use `get_table_access_audit` with filter

**Alternative:**
```sql
-- Use get_table_access_audit with action filter
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_access_audit(
  start_date, end_date, '%'
))
WHERE action_name LIKE '%EXPORT%' OR action_name LIKE '%DOWNLOAD%'
```

---

### ✅ 7. `get_table_access_audit` → **EXISTS!**

**Status:** ✅ Function exists  
**Signature:** `(start_date STRING, end_date STRING, table_pattern STRING)`  
**Issue:** Likely missing TABLE() wrapper or wrong parameters

**Check SQL:**
```sql
-- ❌ WRONG
SELECT * FROM get_table_access_audit(...)

-- ✅ CORRECT
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_access_audit(
  start_date, end_date, table_pattern
))
```

---

## 🔴 Performance Domain (3 errors)

### ❌ 8. `get_query_spill_analysis` → `get_high_spill_queries`

**Error:** `get_query_spill_analysis` not found  
**Correct Name:** `get_high_spill_queries`  
**Signature:** `(start_date STRING, end_date STRING, min_spill_gb DOUBLE)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_query_spill_analysis"
→
"${catalog}.${gold_schema}.get_high_spill_queries"
```

---

### ❌ 9. `get_idle_clusters` → `get_underutilized_clusters`

**Error:** `get_idle_clusters` not found  
**Correct Name:** `get_underutilized_clusters`  
**Signature:** `(days_back INT, cpu_threshold DOUBLE, min_hours INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_idle_clusters"
→
"${catalog}.${gold_schema}.get_underutilized_clusters"
```

**Parameter Update:**
```sql
-- OLD (2 params)
get_idle_clusters(30)

-- NEW (3 params)
get_underutilized_clusters(30, 0.3, 1)
-- days_back=30, cpu_threshold=30%, min_hours=1
```

---

### ❌ 10. `get_query_duration_percentiles` → `get_query_latency_percentiles`

**Error:** `get_query_duration_percentiles` not found  
**Correct Name:** `get_query_latency_percentiles`  
**Signature:** `(start_date STRING, end_date STRING)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_query_duration_percentiles"
→
"${catalog}.${gold_schema}.get_query_latency_percentiles"
```

---

## 🔴 Job Health Domain (5 errors)

### ❌ 11. `get_failed_jobs_summary` → `get_failed_jobs`

**Error:** `get_failed_jobs_summary` not found  
**Correct Name:** `get_failed_jobs`  
**Signature:** `(start_date STRING, end_date STRING, workspace_filter STRING)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_failed_jobs_summary"
→
"${catalog}.${gold_schema}.get_failed_jobs"
```

---

### ❌ 12. `get_job_success_rates` → `get_job_success_rate`

**Error:** `get_job_success_rates` not found  
**Correct Name:** `get_job_success_rate` (singular!)  
**Signature:** `(start_date STRING, end_date STRING, min_runs INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_job_success_rates"
→
"${catalog}.${gold_schema}.get_job_success_rate"
```

---

### ❌ 13. `get_job_failure_patterns` → `get_job_failure_trends`

**Error:** `get_job_failure_patterns` not found  
**Correct Name:** `get_job_failure_trends`  
**Signature:** `(days_back INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_job_failure_patterns"
→
"${catalog}.${gold_schema}.get_job_failure_trends"
```

---

### ❌ 14. `get_repair_cost_analysis` → `get_job_repair_costs`

**Error:** `get_repair_cost_analysis` not found  
**Correct Name:** `get_job_repair_costs`  
**Signature:** `(start_date STRING, end_date STRING, top_n INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_repair_cost_analysis"
→
"${catalog}.${gold_schema}.get_job_repair_costs"
```

---

### ❌ 15. `get_pipeline_health` → ⚠️ **NOT DEPLOYED**

**Error:** `get_pipeline_health` not found  
**Status:** ⚠️ No equivalent function exists  
**Action:** Remove queries OR use monitoring tables directly

**Alternative:**
```sql
-- Query DLT pipeline status from job run timeline
SELECT 
  job_name,
  COUNT(*) as total_events,
  SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
  SUM(CASE WHEN result_state != 'SUCCESS' THEN 1 ELSE 0 END) as failed_events,
  ROUND(100.0 * SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND job_name LIKE '%DLT%' OR job_name LIKE '%Pipeline%'
GROUP BY job_name
ORDER BY failed_events DESC
```

---

## 🔴 Data Quality Domain (5 errors)

### ❌ 16. `get_stale_tables` → `get_table_freshness`

**Error:** `get_stale_tables` not found  
**Correct Name:** `get_table_freshness`  
**Signature:** `(freshness_threshold_hours INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_stale_tables"
→
"${catalog}.${gold_schema}.get_table_freshness"
```

**Query Update:**
```sql
-- OLD
SELECT * FROM TABLE(get_stale_tables(7))
WHERE is_stale = TRUE

-- NEW
SELECT * FROM TABLE(get_table_freshness(24))
WHERE hours_since_update > 24
ORDER BY hours_since_update DESC
```

---

### ❌ 17. `get_quality_check_failures` → `get_tables_failing_quality`

**Error:** `get_quality_check_failures` not found  
**Correct Name:** `get_tables_failing_quality`  
**Signature:** `(freshness_threshold_hours INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_quality_check_failures"
→
"${catalog}.${gold_schema}.get_tables_failing_quality"
```

---

### ✅ 18. `get_data_quality_summary` → **EXISTS!**

**Status:** ✅ Function exists  
**Signature:** `()` (no parameters)  
**Issue:** Likely missing TABLE() wrapper

**Check SQL:**
```sql
-- ❌ WRONG
SELECT * FROM get_data_quality_summary()

-- ✅ CORRECT
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_data_quality_summary())
```

---

### ❌ 19. `get_table_activity_summary` → `get_table_activity_status`

**Error:** `get_table_activity_summary` not found  
**Correct Name:** `get_table_activity_status`  
**Signature:** `(days_back INT, inactive_threshold_days INT)`

**Fix:**
```json
"${catalog}.${gold_schema}.get_table_activity_summary"
→
"${catalog}.${gold_schema}.get_table_activity_status"
```

---

### ✅ 20. `get_pipeline_data_lineage` → **EXISTS!**

**Status:** ✅ Function exists  
**Signature:** `(days_back INT, entity_filter STRING)`  
**Issue:** Likely missing TABLE() wrapper or wrong parameters

**Check SQL:**
```sql
-- ❌ WRONG
SELECT * FROM get_pipeline_data_lineage(7)

-- ✅ CORRECT
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_pipeline_data_lineage(7, '%'))
-- Note: entity_filter is REQUIRED (use '%' for all)
```

---

## 📊 Fix Summary by Domain

| Domain | Total Errors | Wrong Names | Exists | Not Deployed |
|--------|--------------|-------------|--------|--------------|
| **Security** | 7 | 5 | 1 | 1 |
| **Performance** | 3 | 3 | 0 | 0 |
| **Job Health** | 5 | 4 | 0 | 1 |
| **Data Quality** | 5 | 3 | 2 | 0 |
| **TOTAL** | 20 | 15 | 3 | 2 |

---

## 🚀 Bulk Fix Script

Here's a find/replace list for bulk fixes:

```bash
# Security Domain
get_user_activity → get_user_activity_summary
get_pii_access_events → get_sensitive_table_access
get_failed_authentication_events → get_failed_actions
get_permission_change_events → get_permission_changes
get_service_account_activity → get_service_account_audit

# Performance Domain
get_query_spill_analysis → get_high_spill_queries
get_idle_clusters → get_underutilized_clusters
get_query_duration_percentiles → get_query_latency_percentiles

# Job Health Domain
get_failed_jobs_summary → get_failed_jobs
get_job_success_rates → get_job_success_rate
get_job_failure_patterns → get_job_failure_trends
get_repair_cost_analysis → get_job_repair_costs

# Data Quality Domain
get_stale_tables → get_table_freshness
get_quality_check_failures → get_tables_failing_quality
get_table_activity_summary → get_table_activity_status
```

---

## ⚠️ Functions Not Deployed (Need Action)

1. **`get_data_export_events`** - No direct equivalent
   - **Action:** Remove queries OR use `get_table_access_audit` with filter

2. **`get_pipeline_health`** - No direct equivalent
   - **Action:** Remove queries OR query `fact_job_run_timeline` directly

---

## 📋 Next Steps

1. ✅ **Apply bulk find/replace** (15 name fixes) - 30 minutes
2. ✅ **Fix parameter signatures** (3 functions need param updates) - 15 minutes
3. ✅ **Handle non-existent functions** (2 functions to remove/rewrite) - 30 minutes
4. ✅ **Revalidate** - Run validation job again

**Total Estimated Time:** 75 minutes


