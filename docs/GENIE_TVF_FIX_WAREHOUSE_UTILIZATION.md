# TVF Fix: get_warehouse_utilization UUID Casting Error

**Date:** January 9, 2026  
**Fix Type:** TVF Implementation Bug  
**Impact:** 2 Genie spaces (cost_intelligence Q19, performance Q7)

---

## Problem

**Error:**
```
[CAST_INVALID_INPUT] The value '01f0ec1f-9c1f-1f18-858a-40a7fec0501d' 
of the type "STRING" cannot be cast to "INT" because it is malformed.
```

**Root Cause:** 
The `get_warehouse_utilization` TVF had an incorrect placeholder calculation for `peak_concurrency`:

```sql
MAX(q.statement_id) AS peak_concurrency,  -- Placeholder: need proper concurrency calc
```

**Why It Failed:**
- `statement_id` is a UUID STRING column
- `MAX()` on a UUID string doesn't provide meaningful concurrency data
- Spark's query optimizer attempted implicit casting to INT during aggregation → casting error

---

## Solution

**Changed Line 105 in `src/semantic/tvfs/performance_tvfs.sql`:**

### ❌ BEFORE (Incorrect)
```sql
MAX(q.statement_id) AS peak_concurrency,  -- Placeholder: need proper concurrency calc
```

### ✅ AFTER (Fixed)
```sql
CAST(NULL AS INT) AS peak_concurrency,  -- Requires window function calculation - not available in simple GROUP BY
```

**Rationale:**
1. **Removes UUID casting:** No longer attempts to aggregate a UUID column
2. **Explicit NULL:** Returns `NULL` for `peak_concurrency` (indicates data not available)
3. **Type-safe:** `CAST(NULL AS INT)` satisfies the `INT` return type without casting errors
4. **Accurate comment:** Documents why concurrency isn't calculated (requires window functions)

---

## Impact

### Affected Genie Spaces (2 queries)

| Genie Space | Question | Status |
|-------------|----------|--------|
| **cost_intelligence** | Q19: "Show me warehouse cost analysis" | ✅ Will pass after TVF redeploy |
| **performance** | Q7: "Show me warehouse utilization metrics" | ✅ Will pass after TVF redeploy |

### Expected Pass Rates After Fix

| Genie Space | Before | After | Change |
|-------------|--------|-------|--------|
| cost_intelligence | 24/25 (96%) | **25/25 (100%)** | +1 |
| performance | 24/25 (96%) | **25/25 (100%)** | +1 |

**Overall:** 146/150 → **148/150 (98.7%)**

---

## Validation

### Test Query (Should Now Pass)
```sql
-- Test the fixed TVF
SELECT * FROM get_warehouse_utilization(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
) ORDER BY total_queries DESC LIMIT 10;
```

**Expected Result:**
- ✅ No casting errors
- ✅ `peak_concurrency` column returns NULL for all rows
- ✅ All other metrics (total_queries, avg_duration_seconds, etc.) populated correctly

---

## Why Not Calculate Actual Concurrency?

**Proper concurrency calculation requires:**

```sql
-- Complex window function approach (not supported in simple GROUP BY)
WITH query_windows AS (
  SELECT
    compute_warehouse_id,
    start_time,
    end_time,
    COUNT(*) OVER (
      PARTITION BY compute_warehouse_id
      ORDER BY start_time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) - COUNT(*) OVER (
      PARTITION BY compute_warehouse_id
      ORDER BY end_time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS concurrent_count
  FROM fact_query_history
)
SELECT
  compute_warehouse_id,
  MAX(concurrent_count) AS peak_concurrency
FROM query_windows
GROUP BY compute_warehouse_id;
```

**Complexity:**
- Requires window functions with complex frame specifications
- Not compatible with the current TVF's simple GROUP BY structure
- Would significantly impact performance for large date ranges

**Decision:** Return NULL for now, implement as separate TVF if needed (e.g., `get_warehouse_concurrency_analysis`)

---

## Alternative Fix Considered

### Option 2: Use COUNT(DISTINCT statement_id) as Proxy
```sql
COUNT(DISTINCT q.statement_id) AS peak_concurrency_proxy,  -- Total unique queries as proxy
```

**Why Not Used:**
- Not a true concurrency metric (doesn't measure overlapping queries)
- Misleading metric name (`peak_concurrency` implies max concurrent queries)
- Better to return NULL than incorrect data

---

## Files Modified

1. **`src/semantic/tvfs/performance_tvfs.sql`**
   - Line 105: Changed `MAX(q.statement_id)` to `CAST(NULL AS INT)`
   - Updated comment to explain why concurrency isn't calculated

---

## Deployment Status

✅ **Deployed:** January 9, 2026  
📦 **Bundle:** dev target  
🔄 **Validation:** Pending (re-run Q19 and Q7)

### Next Steps

1. **Re-validate cost_intelligence Q19:**
   ```bash
   databricks bundle run -t dev genie_benchmark_sql_validation_job \
     --only validate_cost_intelligence --no-wait
   ```

2. **Re-validate performance Q7:**
   ```bash
   databricks bundle run -t dev genie_benchmark_sql_validation_job \
     --only validate_performance --no-wait
   ```

3. **Confirm 100% pass rate:**
   - cost_intelligence: Expected 25/25
   - performance: Expected 25/25

---

## Related TVF Bugs

This fix resolves the UUID casting issue. **One other TVF bug remains:**

| Genie Space | Question | TVF | Error | Status |
|-------------|----------|-----|-------|--------|
| unified_health_monitor | Q12 | `get_warehouse_utilization` | DATE parameter casting | Separate issue |

**Note:** The unified Q12 error is a different bug related to date parameter handling, not UUID casting.

---

## Lessons Learned

1. **Never aggregate UUID columns:** UUIDs are identifiers, not numeric values
2. **Placeholder calculations are dangerous:** Use explicit NULL instead of meaningless aggregates
3. **Type safety matters:** Implicit casts can fail in unpredictable ways
4. **Document limitations:** If a metric isn't available, say so explicitly

---

## Summary

✅ **Fixed:** `get_warehouse_utilization` TVF no longer attempts to cast UUID to INT  
✅ **Impact:** Resolves 2 Genie space errors (cost Q19, performance Q7)  
✅ **Expected Result:** 100% pass rate for cost_intelligence and performance spaces  
✅ **Deployed:** January 9, 2026

**This fix brings us from 146/150 (97.3%) to an expected 148/150 (98.7%) pass rate across all 6 Genie spaces.**

