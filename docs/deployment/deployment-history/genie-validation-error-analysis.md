# Genie Space Validation Error Analysis

**Date:** 2026-01-08  
**Validation Run:** Complete (123 queries)  
**Results:** 83 passed (67%), 40 failed (33%)

---

## Error Summary by Category

| Error Type | Count | Severity | Fix Complexity |
|-----------|-------|----------|----------------|
| **SYNTAX_ERROR** | 7 | 🔴 CRITICAL | Easy (Pattern-based) |
| **COLUMN_NOT_FOUND** | 20+ | 🟠 HIGH | Medium (Schema validation) |
| **CAST_INVALID_INPUT** | 3 | 🟠 HIGH | Easy (Type casting) |
| **WRONG_NUM_ARGS** | 3 | 🟠 HIGH | Easy (Add params) |
| **NESTED_AGGREGATE** | 2 | 🟡 MEDIUM | Hard (SQL refactoring) |
| **OTHER** | 5+ | 🟡 MEDIUM | Varies |

**Total Errors:** 40

---

## 1. SYNTAX_ERROR (7 errors) - CRITICAL ⚠️

### Pattern 1: `CURRENT_DATE(,` Malformation (5 errors)

**Affected Queries:**
- `cost_intelligence Q19` - Warehouse cost analysis
- `performance Q7` - Warehouse utilization
- `performance Q8` - High spill queries
- `security_auditor Q5` - User activity summary
- `security_auditor Q6` - Sensitive table access

**Current (WRONG):**
```sql
CAST(CURRENT_DATE(,
  CURRENT_DATE()::STRING
) - INTERVAL 7 DAYS AS STRING)
```

**Expected (CORRECT):**
```sql
CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING)
```

**Root Cause:** Extra opening parenthesis or malformed function call formatting.

### Pattern 2: Missing Closing Parenthesis (2 errors)

**Affected Queries:**
- `cost_intelligence Q23` - Tag compliance analysis
- `unified_health_monitor Q20` - Cost optimization

**Error:** `Syntax error at or near ')'` or `missing ')'`

---

## 2. COLUMN_NOT_FOUND (20+ errors) - HIGH ⚠️

### Pattern 1: Incorrect Column Names from TVFs

| Query | Missing Column | Actual Column | TVF Source |
|-------|---------------|---------------|------------|
| **performance Q14** | `p99_duration` | `p99_seconds` | `get_query_latency_percentiles` |
| **job_health_monitor Q6** | `p95_duration_minutes` | `p95_duration_min` | `get_job_duration_percentiles` |
| **job_health_monitor Q7** | `success_rate` | `success_rate_pct` | `get_job_success_rate` |
| **job_health_monitor Q8** | `failure_count` | `failed_runs` | `get_job_failure_trends` |
| **job_health_monitor Q9** | `deviation_score` | `deviation_ratio` | `get_job_outlier_runs` |

### Pattern 2: Incorrect Column Names from Metric Views

| Query | Missing Column | Actual Column | Metric View Source |
|-------|---------------|---------------|-------------------|
| **unified_health_monitor Q19** | `cost_7d` | `last_7_day_cost` | `mv_cost_analytics` |
| **unified_health_monitor Q11** | `utilization_rate` | (does not exist) | `mv_commit_tracking` |
| **unified_health_monitor Q12** | `query_count` | `total_queries` | (TVF result) |

### Pattern 3: Alias Reference Errors

| Query | Error | Issue |
|-------|-------|-------|
| **cost_intelligence Q22** | `sc.total_sku_cost` | Should be `scCROSS.total_sku_cost` |
| **cost_intelligence Q25** | `workspace_name` | Missing in forecast TVF result |
| **performance Q25** | `qh.query_volume` | Should be `qhCROSS.query_volume` |

### Pattern 4: Non-Existent Columns

| Query | Missing Column | Table/View | Fix |
|-------|---------------|------------|-----|
| **security_auditor Q7** | `failed_count` | `get_failed_actions` result | Use `COUNT(*)` instead |
| **security_auditor Q8** | `change_date` | `get_permission_changes` result | Use `event_time` |
| **security_auditor Q10** | `risk_level` | `mv_security_events` | Does not exist |
| **security_auditor Q15** | `unique_data_consumers` | `mv_governance_analytics` | Use `unique_users` |
| **security_auditor Q16** | `event_count` | `get_service_account_audit` | Use `total_events` |
| **security_auditor Q17** | `event_volume_drift` | Monitoring table | Use `event_volume_drift_pct` |
| **unified_health_monitor Q4** | `success_rate` | `mv_security_events` | Use `1 - failure_rate` |
| **unified_health_monitor Q7** | `failure_count` | `get_failed_jobs` | Aggregate with `COUNT(*)` |
| **unified_health_monitor Q13** | `failed_events` | `get_pipeline_data_lineage` | Does not exist |
| **unified_health_monitor Q16** | `days_since_last_access` | `get_table_freshness` | Use `hours_since_update / 24` |
| **performance Q16** | `recommended_action` | ML prediction table | Does not exist |
| **unified_health_monitor Q18** | `recommended_action` | ML prediction table | Does not exist |
| **job_health_monitor Q4** | `failure_count` | `get_failed_jobs` | Aggregate with `COUNT(*)` |
| **job_health_monitor Q14** | `f.start_time` | Fact table | Use `f.period_start_time` |
| **job_health_monitor Q18** | `ft.run_date` | Fact table | Use `ft.job_run_date` or similar |

---

## 3. CAST_INVALID_INPUT (3 errors) - HIGH ⚠️

| Query | Issue | Expected Type | Actual Type | Fix |
|-------|-------|---------------|-------------|-----|
| **performance Q10** | `'2026-01-08'` to DOUBLE | DOUBLE | STRING (DATE) | Remove cast or use correct function |
| **performance Q12** | `'2025-12-25'` to INT | INT | STRING (DATE) | Remove cast or use DATEDIFF |
| **job_health_monitor Q12** | `'30'` to DATE | DATE | STRING (INT) | Use `CAST('30' AS INT)` |

---

## 4. WRONG_NUM_ARGS (3 errors) - HIGH ⚠️

| Query | TVF | Required Params | Provided | Missing |
|-------|-----|----------------|----------|---------|
| **security_auditor Q9** | `get_off_hours_activity` | 4 | 1 | `end_date`, `business_hours_start`, `business_hours_end` |
| **security_auditor Q11** | `get_off_hours_activity` | 4 | 1 | `end_date`, `business_hours_start`, `business_hours_end` |
| **job_health_monitor Q10** | `get_job_retry_analysis` | 2 | 1 | `end_date` |

**Required Signatures (from `docs/reference/actual_assets/tvfs.md`):**
```sql
get_off_hours_activity(start_date, end_date, business_hours_start, business_hours_end)
get_job_retry_analysis(start_date, end_date)
```

---

## 5. NESTED_AGGREGATE_FUNCTION (2 errors) - MEDIUM ⚠️

| Query | Issue | Fix |
|-------|-------|-----|
| **performance Q23** | Using MEASURE() inside another aggregate | Move inner MEASURE to CTE |
| **unified_health_monitor Q21** | Using MEASURE() inside another aggregate | Move inner MEASURE to CTE |

**Example Fix Pattern:**
```sql
-- ❌ WRONG
SELECT AVG(MEASURE(total_cost)) FROM mv_cost_analytics

-- ✅ CORRECT
WITH cost_measures AS (
  SELECT MEASURE(total_cost) as total_cost FROM mv_cost_analytics
)
SELECT AVG(total_cost) FROM cost_measures
```

---

## Recommended Fix Order (By Impact)

### Phase 1: SYNTAX_ERROR (Blocks 7 queries)
1. Fix `CURRENT_DATE(,` pattern (5 queries) - **CRITICAL**
2. Fix missing parentheses (2 queries) - **CRITICAL**

**Expected Impact:** +7 queries pass (90 total, 73%)

### Phase 2: WRONG_NUM_ARGS (Blocks 3 queries)
3. Add missing TVF parameters (3 queries) - **HIGH**

**Expected Impact:** +3 queries pass (93 total, 76%)

### Phase 3: CAST_INVALID_INPUT (Blocks 3 queries)
4. Fix type casting errors (3 queries) - **HIGH**

**Expected Impact:** +3 queries pass (96 total, 78%)

### Phase 4: COLUMN_NOT_FOUND (Blocks 20+ queries)
5. Fix TVF column names (5 queries) - **HIGH**
6. Fix Metric View column names (3 queries) - **MEDIUM**
7. Fix alias references (3 queries) - **MEDIUM**
8. Fix non-existent columns (10+ queries) - **MEDIUM**

**Expected Impact:** +20 queries pass (116 total, 94%)

### Phase 5: NESTED_AGGREGATE (Blocks 2 queries)
9. Refactor nested aggregates with CTEs (2 queries) - **MEDIUM**

**Expected Impact:** +2 queries pass (118 total, 96%)

### Final Goal: 118/123 passing (96%)

**Remaining 5 queries may require:**
- Schema changes
- Question rewording
- Advanced SQL refactoring
- Data availability

---

## Next Actions

1. ✅ Create Python script to fix SYNTAX_ERROR patterns
2. ✅ Create Python script to add missing TVF parameters
3. ✅ Create Python script to fix CAST_INVALID_INPUT
4. ✅ Create Python script to fix COLUMN_NOT_FOUND (pattern-based)
5. ⚠️ Manual review for NESTED_AGGREGATE and complex queries
6. ✅ Deploy and re-validate

**Estimated Total Fixes:** 30-35 queries (from 40 errors)  
**Final Expected Pass Rate:** 94-96%

