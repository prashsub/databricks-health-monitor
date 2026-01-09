# Two Critical Manual Fixes Applied

**Date:** January 9, 2026  
**Session:** Continuation of Manual COLUMN_NOT_FOUND Analysis

## Summary

Applied 2 critical fixes to resolve errors from previous incorrect fixes:

### 1. Performance Q18: Reverted Incorrect Column Name ✅

**Error:** `COLUMN_NOT_FOUND: p99_seconds`  
**Actual Column:** `p99_duration_seconds` (verified in `mv_query_performance`)

**Root Cause:**  
Previous manual fix session incorrectly changed `p99_duration_seconds` → `p99_seconds`.

**Fix Applied:**
- **File:** `src/genie/performance_genie_export.json`
- **Question:** "What is the P99 query duration?"
- **Change:** Reverted `MEASURE(p99_seconds)` → `MEASURE(p99_duration_seconds)`

**Before:**
```sql
SELECT MEASURE(p99_seconds) as p99_sec FROM mv_query_performance 
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```

**After:**
```sql
SELECT MEASURE(p99_duration_seconds) as p99_sec FROM mv_query_performance 
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```

---

### 2. Job Health Monitor Q14: Calculate Duration from Timestamps ✅

**Error:** `COLUMN_NOT_FOUND: f.duration_minutes`  
**Root Cause:** Column does not exist in `fact_pipeline_update_timeline`

**Fix Applied:**
- **File:** `src/genie/job_health_monitor_genie_export.json`
- **Question:** "Show me pipeline health from DLT updates"
- **Change:** Calculate duration from `period_start_time` and `period_end_time`

**Before:**
```sql
AVG(f.duration_minutes)
```

**After:**
```sql
AVG((UNIX_TIMESTAMP(f.period_end_time) - UNIX_TIMESTAMP(f.period_start_time)) / 60)
```

**Full SQL After Fix:**
```sql
SELECT 
  p.name,
  COUNT(*) as update_count,
  SUM(CASE WHEN f.result_state = 'COMPLETED' THEN 1 ELSE 0 END) as successful_updates,
  AVG((UNIX_TIMESTAMP(f.period_end_time) - UNIX_TIMESTAMP(f.period_start_time)) / 60) as avg_duration
FROM fact_pipeline_update_timeline f
JOIN dim_pipeline p ON f.workspace_id = p.workspace_id AND f.pipeline_id = p.pipeline_id
WHERE f.period_start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY p.name
ORDER BY successful_updates DESC
LIMIT 10;
```

---

## Validation Against Ground Truth

Both fixes verified against `docs/reference/actual_assets/`:

### Performance Q18 Verification
**Source:** `docs/reference/actual_assets/mvs.md`
```
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	mv_query_performance	p99_duration_seconds	DOUBLE
```
✅ Column `p99_duration_seconds` exists  
❌ Column `p99_seconds` does NOT exist

### Job Health Monitor Q14 Verification
**Source:** `docs/reference/actual_assets/tables.md`
```
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	fact_pipeline_update_timeline	period_start_time	TIMESTAMP
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	fact_pipeline_update_timeline	period_end_time	TIMESTAMP
```
✅ Columns `period_start_time` and `period_end_time` exist  
❌ Column `duration_minutes` does NOT exist

---

## Deployment

```bash
cd DatabricksHealthMonitor
python3 scripts/fix_genie_revert_and_calculate.py
# ✅ performance Q18: Reverted MEASURE(p99_seconds) → MEASURE(p99_duration_seconds)
# ✅ job_health_monitor Q14: Calculate duration_minutes from period_start_time/period_end_time

databricks bundle deploy -t dev
# Deployment complete!
```

---

## Impact

- **Files Modified:** 2
- **SQL Queries Fixed:** 2
- **Expected Validation Impact:** 2 fewer `COLUMN_NOT_FOUND` errors

---

## Next Steps

1. Re-run validation to confirm these 2 errors are resolved
2. Continue manual analysis for remaining `COLUMN_NOT_FOUND` errors (13 → 11 expected)
3. Address other error categories:
   - 6 `SYNTAX_ERROR`
   - 7 `CAST_INVALID_INPUT`
   - 2 `NESTED_AGGREGATE_FUNCTION`
   - 1 `UNRESOLVABLE_TABLE_VALUED_FUNCTION` (if still present)

---

## Key Learnings

1. **Always verify column names against ground truth** - Even previous "fixes" can be wrong
2. **Calculate derived fields from base columns** - Don't assume aggregated columns exist
3. **Use `UNIX_TIMESTAMP()` for duration calculations** - Standard Spark SQL pattern for timestamp diffs
4. **Test incrementally** - Deploy small batches of fixes for faster feedback

---

**Status:** ✅ Deployed and Ready for Validation

