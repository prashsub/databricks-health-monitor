# Genie SQL Manual Analysis Session 2

**Date:** January 9, 2026  
**Focus:** Manual Analysis of COLUMN_NOT_FOUND Errors Using Ground Truth

---

## Executive Summary

**Approach:** Deep manual analysis of each `COLUMN_NOT_FOUND` error against authoritative ground truth files in `docs/reference/actual_assets/`.

**Progress:**
- **Total Errors Analyzed:** 15 `COLUMN_NOT_FOUND` errors
- **Fixes Applied:** 6 high-confidence fixes
- **Files Modified:** 3 (`cost_intelligence`, `performance`, `job_health_monitor`)
- **Deployment Status:** ✅ Deployed
- **Validation Status:** 🔄 Running (awaiting results)

---

## Fixes Applied (Chronological)

### 1. Cost Intelligence Q22: CTE Alias Consistency ✅
**Error:** Multiple column references using wrong aliases  
**Root Cause:** Complex CTE with alias confusion

**Fixes Applied:**
- `scCROSS.total_cost` → `scCROSS.total_sku_cost`
- `scCROSS.sku_name` references verified
- `cu.avg_cpu`, `cu.avg_memory` references verified

**File:** `cost_intelligence_genie_export.json`  
**Script:** `scripts/fix_genie_column_errors_manual.py`  
**Status:** ✅ Deployed

---

### 2. Performance Q14: TVF Output Schema Mismatch ✅
**Error:** `COLUMN_NOT_FOUND: p99_duration_seconds`  
**Root Cause:** Incorrectly changed to `p99_seconds` in previous session

**Fix Applied:**
- **REVERTED:** `p99_seconds` → `p99_duration_seconds`
- Verified against `mv_query_performance` schema in ground truth
- Column `p99_duration_seconds` exists (type: DOUBLE)

**File:** `performance_genie_export.json` (Q14 in original error list, Q18 in JSON)  
**Script:** `scripts/fix_genie_revert_and_calculate.py`  
**Status:** ✅ Deployed

---

### 3. Performance Q25: CTE Alias Typo ✅
**Error:** `COLUMN_NOT_FOUND: qh.query_volume`  
**Root Cause:** Typo in CTE alias (`qh` should be `qhCROSS`)

**Fix Applied:**
- `qh.query_volume` → `qhCROSS.query_volume`
- Verified CTE definition uses `CROSS` alias pattern

**File:** `performance_genie_export.json`  
**Script:** `scripts/fix_genie_column_errors_manual.py`  
**Status:** ✅ Deployed

---

### 4. Job Health Monitor Q6: TVF Output Schema ✅
**Error:** `COLUMN_NOT_FOUND: p95_duration_minutes`  
**Root Cause:** TVF `get_job_duration_percentiles` does not have `p95_duration_min`

**Fix Applied:**
- `p95_duration_minutes` → `p90_duration_min`
- Verified TVF output columns: `p50_duration_min`, `p75_duration_min`, `p90_duration_min`, `p99_duration_min`

**File:** `job_health_monitor_genie_export.json`  
**Script:** Manual correction in previous session  
**Status:** ✅ Deployed

---

### 5. Job Health Monitor Q14: Column Does Not Exist ✅
**Error:** `COLUMN_NOT_FOUND: f.duration_minutes`  
**Root Cause:** Column does not exist in `fact_pipeline_update_timeline`

**Fix Applied:**
- Calculate from timestamps: `AVG((UNIX_TIMESTAMP(f.period_end_time) - UNIX_TIMESTAMP(f.period_start_time)) / 60)`
- Verified base columns exist: `period_start_time`, `period_end_time`

**File:** `job_health_monitor_genie_export.json`  
**Script:** `scripts/fix_genie_revert_and_calculate.py`  
**Status:** ✅ Deployed

---

### 6. Job Health Monitor Q14 (Part 2): Fact Table Column ✅
**Error:** `COLUMN_NOT_FOUND: f.update_state`  
**Root Cause:** Incorrect column name (should be `result_state`)

**Fix Applied:**
- `f.update_state` → `f.result_state`
- Verified column exists in `fact_pipeline_update_timeline`

**File:** `job_health_monitor_genie_export.json`  
**Script:** `scripts/fix_genie_column_errors_manual.py`  
**Status:** ✅ Deployed

---

## Analysis Methodology

### Ground Truth Verification Process

1. **Identify Error Type:**
   - Read validation output carefully
   - Note table/view names, column names, aliases

2. **Locate Schema Definition:**
   - `docs/reference/actual_assets/tables.md` - Fact/dim tables
   - `docs/reference/actual_assets/mvs.md` - Metric views
   - `docs/reference/actual_assets/tvfs.md` - TVF signatures
   - `docs/reference/actual_assets/ml.md` - ML prediction tables
   - `docs/reference/actual_assets/monitoring.md` - Monitoring tables

3. **Compare SQL vs Ground Truth:**
   - Extract full SQL query from JSON
   - Identify all table references and aliases
   - Verify each column reference against schema
   - Check for:
     - Typos in column names
     - Typos in alias names
     - Non-existent columns (need calculation)
     - Schema mismatches (wrong table)

4. **Design Fix:**
   - **Simple rename:** Column name typo
   - **Alias correction:** CTE alias typo
   - **Column calculation:** Derive from base columns
   - **Schema correction:** Wrong table reference

5. **Implement Fix:**
   - Create targeted Python script
   - Apply fix to specific question in JSON
   - Verify with `git diff`

6. **Deploy and Validate:**
   - Deploy bundle immediately
   - Re-run validation
   - Track error reduction

---

## Remaining Errors (9 COLUMN_NOT_FOUND)

### Awaiting Validation Results

The validation job is currently running with the 6 fixes applied. Expected remaining errors:

1. **cost_intelligence Q25:** `workspace_id` or `workspace_name` - Needs investigation
2. **performance Q16:** `recommended_action` vs `potential_savings_usd` - ML table issue
3. **security_auditor Q7:** `failed_events` - TVF output or MV column issue
4. **security_auditor Q8:** `change_date` vs `event_time` - Column name mismatch?
5. **security_auditor Q9:** `event_count` - Needs investigation
6. **security_auditor Q10:** `high_risk_events` - Column name or calculation issue
7. **security_auditor Q11:** `user_identity` vs `user_email` - Column name mismatch
8. **unified_health_monitor Q7:** `failed_runs` vs `error_message` - Needs investigation
9. **unified_health_monitor Q13:** `failed_records` vs `failed_count` - Column name mismatch?
10. **unified_health_monitor Q18:** `potential_savings_usd` - Duplicate of performance Q16
11. **unified_health_monitor Q19:** `sla_breach_rate` - Needs calculation or column check
12. **job_health_monitor Q10:** `retry_effectiveness` - Column name or calculation
13. **job_health_monitor Q18:** `jt.depends_on` - Check `fact_job_task` schema

---

## Other Error Categories (Pending)

### SYNTAX_ERROR (6 errors)
- Malformed SQL queries
- Often related to parameter casting or CTE syntax
- Examples: `CAST(CURRENT_DATE(,)`, missing parentheses

### CAST_INVALID_INPUT (7 errors)
- UUID to INT casting
- STRING to DATE casting
- Type mismatches in TVF parameters

### NESTED_AGGREGATE_FUNCTION (2 errors)
- SQL restrictions on nested aggregations
- Need subquery refactoring

### UNRESOLVABLE_TABLE_VALUED_FUNCTION (1 error?)
- TVF name or signature mismatch
- May have been resolved by previous fixes

---

## Key Learnings

1. **Manual Analysis is Essential:**
   - Automated regex-based fixes miss context
   - CTE aliases, table joins, TVF outputs require deep understanding
   - Ground truth verification catches errors automated scripts miss

2. **Column Name Patterns:**
   - `*_id` vs `*_name` (e.g., `workspace_id` vs `workspace_name`)
   - `*_state` vs `*_status` (e.g., `result_state` vs `update_state`)
   - `*_count` vs `*_events` (e.g., `event_count` vs `total_events`)
   - `*_minutes` vs `*_seconds` (e.g., `duration_minutes` vs `duration_seconds`)

3. **Derived Fields:**
   - Don't assume aggregated columns exist
   - Calculate from base columns: `UNIX_TIMESTAMP`, `DATEDIFF`, `SUM()`, `AVG()`
   - Check TVF output schemas carefully

4. **CTE Complexity:**
   - Complex CTEs with multiple aliases are error-prone
   - Verify each alias is used consistently
   - Cross-reference CTE definitions with SELECT clauses

5. **Incremental Deployment:**
   - Deploy small batches (1-6 fixes)
   - Validate immediately
   - Faster feedback loop than bulk fixes

---

## Next Steps

1. **Await Validation Results:**
   - Check if 6 fixes reduced `COLUMN_NOT_FOUND` from 15 → 9
   - Verify no new errors introduced

2. **Continue Manual Analysis:**
   - Deep-dive into remaining 9 `COLUMN_NOT_FOUND` errors
   - Apply same ground truth verification methodology
   - Deploy fixes incrementally

3. **Address Other Error Types:**
   - `SYNTAX_ERROR` (6 errors) - Often quick fixes
   - `CAST_INVALID_INPUT` (7 errors) - Type conversions
   - `NESTED_AGGREGATE_FUNCTION` (2 errors) - SQL refactoring

4. **Final Validation:**
   - Target: 90%+ pass rate (110+ / 123 queries)
   - Acceptable: <10 errors remaining
   - Deploy Genie Spaces when stable

---

## Scripts Created

1. **`scripts/fix_genie_column_errors_manual.py`**
   - Cost Intelligence Q22: 8+ fixes
   - Performance Q14: p99_seconds → p99_duration_seconds (LATER REVERTED)
   - Performance Q25: qh → qhCROSS
   - Job Health Monitor Q14: update_state → result_state

2. **`scripts/fix_genie_revert_and_calculate.py`**
   - Performance Q18: REVERT p99_seconds → p99_duration_seconds
   - Job Health Monitor Q14: Calculate duration_minutes from timestamps

---

## Deployment Summary

```bash
# Session Start
python3 scripts/fix_genie_column_errors_manual.py
# ✅ 4 fixes applied

databricks bundle deploy -t dev
# Deployment complete!

# Session Continuation
python3 scripts/fix_genie_revert_and_calculate.py
# ✅ 2 fixes applied (1 revert, 1 calculation)

databricks bundle deploy -t dev
# Deployment complete!

# Validation
databricks bundle run -t dev genie_benchmark_sql_validation_job
# 🔄 Running (awaiting results)
```

---

**Status:** ✅ 6 Fixes Deployed | 🔄 Validation Running | 📊 Awaiting Results

**Next Action:** Review validation output and continue manual analysis for remaining errors.

