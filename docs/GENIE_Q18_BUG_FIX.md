# Genie Space: job_health_monitor Q18 Bug Fix

**Date:** January 9, 2026  
**Status:** ✅ Fixed  
**Error Type:** CAST_INVALID_INPUT (run_id → DATE)

---

## 🐛 Bug Details

### Error Message
```
[CAST_INVALID_INPUT] The value '995059011755915' of the type "STRING" 
cannot be cast to "DATE" because it is malformed.
```

### Question
"🔬 DEEP RESEARCH: Cross-task dependency analysis - identify cascading failure patterns where upstream task failures cause downstream job failures"

### Root Cause
The query was filtering on `run_id` (a STRING containing a numeric ID) using a date comparison:

```sql
WHERE ft.run_id >= CURRENT_DATE() - INTERVAL 30 DAYS
```

**Problem:** `run_id` is a STRING field containing values like '995059011755915' (Databricks run IDs), NOT a date/timestamp.

---

## 📊 Schema Validation

From `docs/reference/actual_assets/tables.md`:

| Column | Data Type | Purpose |
|---|---|---|
| `run_id` | STRING | ❌ Numeric run identifier (NOT a date!) |
| `period_start_time` | TIMESTAMP | ✅ Actual timestamp for filtering |
| `period_end_time` | TIMESTAMP | ✅ End timestamp |

---

## ✅ The Fix

### BEFORE (Incorrect)
```sql
WITH task_failures AS (
  SELECT  
    ft.workspace_id,
    ft.job_id,
    ft.task_key,
    jt.depends_on_keys_json,
    COUNT(*) as failure_count,
    ft.run_id
  FROM fact_job_task_run_timeline ft
  JOIN dim_job_task jt 
    ON ft.workspace_id = jt.workspace_id 
    AND ft.job_id = jt.job_id 
    AND ft.task_key = jt.task_key
  WHERE ft.run_id >= CURRENT_DATE() - INTERVAL 30 DAYS  -- ❌ WRONG COLUMN!
    AND ft.result_state != 'SUCCESS'
  GROUP BY ft.workspace_id, ft.job_id, ft.task_key, jt.depends_on_keys_json, ft.run_id
)
...
```

### AFTER (Correct)
```sql
WITH task_failures AS (
  SELECT  
    ft.workspace_id,
    ft.job_id,
    ft.task_key,
    jt.depends_on_keys_json,
    COUNT(*) as failure_count,
    ft.run_id
  FROM fact_job_task_run_timeline ft
  JOIN dim_job_task jt 
    ON ft.workspace_id = jt.workspace_id 
    AND ft.job_id = jt.job_id 
    AND ft.task_key = jt.task_key
  WHERE DATE(ft.period_start_time) >= CURRENT_DATE() - INTERVAL 30 DAYS  -- ✅ CORRECT!
    AND ft.result_state != 'SUCCESS'
  GROUP BY ft.workspace_id, ft.job_id, ft.task_key, jt.depends_on_keys_json, ft.run_id
)
...
```

**Key Change:** `ft.run_id` → `DATE(ft.period_start_time)`

---

## 🎯 Why This Bug Wasn't Caught Earlier

This bug was **NOT present in our previous validation runs** because:

1. **Different validation environment** - Previous runs may not have had data in `fact_job_task_run_timeline`
2. **Query never executed successfully** - The query failed immediately on casting, preventing deeper validation
3. **New parallel validation** - This is the first time we're running comprehensive validation across all 123 questions with real data

---

## 📊 Impact Analysis

### Questions Affected
- **job_health_monitor Q18** (1 query)

### Error Category
- **Genie SQL Bug** (not a TVF implementation bug)
- **Column selection error** (using wrong column for date filtering)

### Similar Patterns to Check
Need to verify that no other queries in `job_health_monitor` or other Genie spaces use `run_id` for date filtering. This pattern might exist elsewhere:

```bash
# Search for similar issues
grep -r "run_id.*CURRENT_DATE\|run_id.*INTERVAL" src/genie/*.json
```

---

## ✅ Verification

### Test Query (After Fix)
```sql
-- Verify the fix works
WITH task_failures AS (
  SELECT  
    ft.workspace_id,
    ft.job_id,
    ft.task_key,
    COUNT(*) as failure_count
  FROM fact_job_task_run_timeline ft
  WHERE DATE(ft.period_start_time) >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND ft.result_state != 'SUCCESS'
  GROUP BY ft.workspace_id, ft.job_id, ft.task_key
  LIMIT 5
)
SELECT * FROM task_failures;
```

**Expected:** Query executes successfully, returns failed tasks from last 30 days.

---

## 📈 Updated Validation Stats

### Job Health Monitor
- **Before fix:** 17/18 passed (94%)
- **After fix:** Expected 18/18 passed (100%)

### Overall Genie Validation
- **Before fix:** 118/123 passed (96%)
- **After fix:** Expected 119/123 passed (97%)
- **Remaining errors:** 4 known TVF bugs (not Genie SQL issues)

---

## 🔍 Lessons Learned

### 1. Column Name Assumptions
**Problem:** Query assumed `run_id` was a date/timestamp based on naming or context.

**Solution:** Always verify column types against ground truth (`docs/reference/actual_assets/tables.md`) before writing date comparisons.

### 2. Parallel Validation Benefits
**Discovery:** Parallel validation caught this bug that sequential validation might have missed due to different data states or execution order.

**Benefit:** Running all 6 Genie spaces in parallel with `LIMIT 1` execution catches more runtime errors than sequential validation.

### 3. Ground Truth is Critical
**Value:** Having `docs/reference/actual_assets/` with exact schemas prevented hours of debugging. The fix was immediate once we checked the actual column types.

---

## 📝 Fix Applied

**File:** `src/genie/job_health_monitor_genie_export.json`  
**Line:** 1107 (benchmark question 18, answer.content)  
**Change:** `ft.run_id` → `DATE(ft.period_start_time)` in WHERE clause

**Deployment:** Ready to deploy with `databricks bundle deploy -t dev`

---

## 🚀 Next Steps

1. ✅ **Deploy fix** - `databricks bundle deploy -t dev`
2. 🔄 **Re-run validation** - Verify Q18 now passes
3. 📊 **Collect remaining task results** - Wait for other 5 tasks to complete
4. 📝 **Update comprehensive summary** - Document all findings

---

**Status:** ✅ Bug fixed, ready to deploy  
**Impact:** 1 query fixed (job_health_monitor Q18)  
**Expected Pass Rate:** 97% (119/123)

