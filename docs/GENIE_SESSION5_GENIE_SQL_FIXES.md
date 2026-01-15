# Genie Session 5: Final Genie SQL Bug Fixes

**Date:** 2026-01-09  
**Session:** 5  
**Focus:** Fix final 2 Genie SQL bugs (cost Q23, Q25)  

---

## 📋 Fixes Applied

### Fix 1: cost_intelligence Q23 - SYNTAX_ERROR

**Issue:** Extra closing parenthesis in `untagged` CTE

**Error Message:**
```
[PARSE_SYNTAX_ERROR] Syntax error at or near ')'. SQLSTATE: 42601 (line 1, pos 544)
```

**Root Cause:**
```sql
-- ❌ BEFORE: 3 closing parentheses
untagged AS (
  SELECT SUM(total_cost) as total_untagged
  FROM get_untagged_resources(
    CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
  )))  <-- Extra closing paren!
```

**Fix Applied:**
```sql
-- ✅ AFTER: 2 closing parentheses (correct)
untagged AS (
  SELECT SUM(total_cost) as total_untagged
  FROM get_untagged_resources(
    CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
  ))  <-- Fixed
```

**Fix Method:** Direct search_replace in JSON

---

### Fix 2: cost_intelligence Q25 - COLUMN_NOT_FOUND

**Issue:** `workspace_id` not available from `get_cost_forecast_summary` TVF

**Error Message:**
```
[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter with name `workspace_id` cannot be resolved.
```

**Root Cause:**
```sql
-- ❌ BEFORE: TVF doesn't return workspace_name or workspace_id
WITH cost_forecast AS (
  SELECT
    workspace_name as workspace_id,  -- Column doesn't exist!
    predicted_cost as projected_monthly_cost
  FROM get_cost_forecast_summary(1)
  LIMIT 1
),
current_costs AS (
  ...
```

**TVF Returns (Platform-Level Forecast):**
- `forecast_month` (DATE)
- `predicted_cost_p50` (DOUBLE)
- `predicted_cost_p10` (DOUBLE)
- `predicted_cost_p90` (DOUBLE)
- `mtd_actual` (DOUBLE)
- `variance_vs_actual` (DOUBLE)

**❌ NO workspace-level columns!**

**Fix Applied:**
```sql
-- ✅ AFTER: Removed unused CTE
WITH current_costs AS (
  SELECT
    workspace_id,
    MEASURE(total_cost) / 30.0 as projected_daily_cost
  FROM mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_id
),
...
```

**Note:** The `cost_forecast` CTE was never used in the main query, so removing it doesn't affect functionality.

**Fix Method:** Direct search_replace in JSON

---

## 📊 Estimated Impact

### Before Session 5
```
Pass Rate: 96% (118/123)
Errors: 7 total
- 2 Genie SQL bugs
- 5 TVF bugs (UUID/String casting)
```

### After Session 5
```
Pass Rate: 98% (120/123) ✅ +2%
Errors: 5 total
- 0 Genie SQL bugs ✅
- 5 TVF bugs (UUID/String casting - requires deeper investigation)
```

---

## 🎯 Remaining Work

### TVF Bugs (5 queries)

**Category A: UUID Casting (2 queries)**
1. cost Q19 - UUID → INT
2. perf Q7 - UUID → DOUBLE

**Status:** Requires investigation of `get_warehouse_utilization` TVF  
**Next Step:** Add defensive casting or investigate Metric View involvement

**Category B: Cluster Rightsizing (2 queries)**
3. perf Q16 - COLUMN_NOT_FOUND: `potential_savings_usd`
4. unified Q18 - COLUMN_NOT_FOUND: `potential_savings_usd`

**Status:** Column doesn't exist in `cluster_capacity_predictions` ML table  
**Next Step:** Either remove column reference or add to ML predictions

**Category C: Date Casting (1 query)**
5. unified Q12 - '7' → DATE

**Status:** Likely a Genie SQL bug in WHERE clause  
**Next Step:** Manual inspection of query logic

---

## 📈 Cumulative Progress

```
Session  Date       Focus                    Fixes  Pass Rate  Errors
-------  ---------  -----------------------  -----  ---------  ------
  1      2026-01-08 SYNTAX/CAST (Batch 1)   16     88%        15
  2A     2026-01-09 Concatenation bugs       6      89%        13
  2B     2026-01-09 SYNTAX/CAST (Batch 2)   16      91%        11
  3      2026-01-09 COLUMN_NOT_FOUND        3      93%        9
  4      2026-01-09 NESTED_AGGREGATE        3      96%        7
  5      2026-01-09 Final Genie SQL bugs    2      98%*       5
-------  ---------  -----------------------  -----  ---------  ------
TOTAL                                        46                 5

* Estimated after deployment and validation
```

---

## 🚀 Deployment Steps

```bash
# 1. Deploy fixes
databricks bundle deploy -t dev

# 2. Run validation
databricks bundle run -t dev genie_benchmark_sql_validation_job

# 3. Check results
# Expected: 120/123 pass (98%)
# Remaining: 5 TVF bugs
```

---

## 📝 Files Modified

1. `src/genie/cost_intelligence_genie_export.json`
   - Q23: Fixed syntax error (extra closing paren)
   - Q25: Removed invalid cost_forecast CTE

---

## 🔍 Key Learnings

### 1. Manual Verification is Critical
- Automated regex patterns missed nuances
- Direct search_replace was more reliable for these fixes

### 2. TVF Return Columns Must Match Usage
- `get_cost_forecast_summary` returns platform-level forecasts
- Cannot be used for workspace-level queries
- Always verify TVF signatures before use

### 3. Syntax Errors Can Be Subtle
- Extra closing parenthesis at position 544 in a long query
- Required manual inspection to identify exact location

### 4. Unused CTEs Should Be Removed
- cost_forecast CTE was never referenced in main query
- Removing it simplified the query and fixed the error

---

**Status:** ✅ Complete - 2 Genie SQL bugs fixed  
**Next:** Deploy and validate, then investigate remaining 5 TVF bugs


