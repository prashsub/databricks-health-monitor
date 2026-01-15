# Genie TVF Bug Analysis - Detailed Investigation

**Date:** 2026-01-09  
**Status:** Investigation Complete - Awaiting User Guidance  

---

## 🔍 Investigation Summary

I investigated the TVF source code and underlying table schemas to identify the root cause of the 5 TVF bugs mentioned. Here are my findings:

---

## Bug Category 1: UUID Casting Errors (2 errors)

### Error Details
```
[CAST_INVALID_INPUT] The value '01f0ec1f-9c1f-1f18-858a-40a7fec0501d' 
of the type "STRING" cannot be cast to "INT/DOUBLE"
```

### Affected Queries
1. **cost_intelligence Q19** - "Show me warehouse cost analysis" - UUID → INT
2. **performance Q7** - "Show me warehouse utilization metrics" - UUID → DOUBLE

### Investigation Results

**TVF Examined:** `get_warehouse_utilization` (src/semantic/tvfs/performance_tvfs.sql)

**Signature:** Lines 71-94
```sql
CREATE OR REPLACE FUNCTION get_warehouse_utilization(
    start_date STRING,
    end_date STRING
)
RETURNS TABLE(
    warehouse_id STRING,  -- ✅ Correctly defined as STRING
    warehouse_name STRING,
    ...
)
```

**Implementation:** Lines 96-113
```sql
RETURN
    SELECT
        q.compute_warehouse_id AS warehouse_id,  -- ✅ No casting
        w.warehouse_name,
        ...
        COUNT(*) AS total_queries,
        SUM(q.total_duration_ms) / 3600000.0 AS total_duration_hours,
        ...
    FROM fact_query_history q
    LEFT JOIN dim_warehouse w
        ON q.compute_warehouse_id = w.warehouse_id  -- ✅ Both are STRING
        AND w.delete_time IS NULL
    WHERE DATE(q.start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND q.compute_warehouse_id IS NOT NULL
    GROUP BY q.compute_warehouse_id, w.warehouse_name, w.warehouse_size
    ORDER BY total_queries DESC;
```

**Underlying Tables Verified:**
- `fact_query_history.compute_warehouse_id` = **STRING** ✅
- `dim_warehouse.warehouse_id` = **STRING** ✅

**Genie Queries:**
```sql
-- cost_intelligence Q19
SELECT * FROM get_warehouse_utilization(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
) ORDER BY total_queries DESC LIMIT 15;
```

### 🤔 Mystery: Why Does This Fail?

**Problem:** The TVF implementation looks CORRECT. There is no explicit UUID→INT casting anywhere.

**Possible Explanations:**

1. **Hidden Metric View Aggregation**  
   - The Genie query might be internally using a Metric View that aggregates warehouse data
   - Metric Views might be trying to SUM() or AVG() warehouse_id thinking it's numeric

2. **Databricks SQL Optimizer Issue**  
   - The optimizer might be trying to optimize the query and incorrectly inferring types
   - UUID strings in certain contexts might trigger implicit casting

3. **Missing Data / NULL Handling**  
   - Some warehouse_id values might be malformed or NULL
   - Error handling might be attempting to cast to INT as fallback

4. **Different Execution Path**  
   - The validation query might be hitting a different code path than expected
   - There might be a view or intermediate table doing the casting

### ✅ Recommended Fix Strategy

**Option A: Defensive Casting in TVF**
```sql
-- Force warehouse_id to remain STRING explicitly
CAST(q.compute_warehouse_id AS STRING) AS warehouse_id
```

**Option B: TRY_CAST for Robustness**
```sql
-- If there's implicit casting happening, make it explicit and safe
TRY_CAST(warehouse_id AS STRING) AS warehouse_id
```

**Option C: Investigate Metric Views**
```bash
# Check if there's a metric view involved
grep -i "warehouse.*metric" src/semantic/metric_views/*.yaml
```

---

## Bug Category 2: Date Casting Errors (7 errors)

### Error Details
```
[CAST_INVALID_INPUT] The value '7' of the type "STRING" cannot be cast to "DATE"
[CAST_INVALID_INPUT] The value '30' of the type "STRING" cannot be cast to "DATE"
[CAST_INVALID_INPUT] The value '2026-01-09' of the type "STRING" cannot be cast to "DOUBLE/INT"
```

### Affected Queries
1. **performance Q10** - "Show me underutilized clusters" - date → DOUBLE
2. **performance Q12** - "Show me query volume trends" - date → INT
3. **unified_health_monitor Q12** - "Show me warehouse utilization" - '7' → DATE
4. **security_auditor Q8** - "What permission changes" - '7' → DATE
5. **job_health_monitor Q4** - "Show me failed jobs today" - '1' → DATE
6. **job_health_monitor Q7** - "Which jobs lowest success rate" - '30' → DATE
7. **job_health_monitor Q12** - "Show me job repair costs" - '30' → DATE

### 🎯 Root Cause: Genie SQL Bugs (Not TVF Bugs!)

**These are likely NOT TVF bugs** - they're Genie SQL queries passing incorrect parameter types.

**Example:** Instead of:
```sql
-- ❌ WRONG
WHERE DATE(event_date) >= '7'  -- Trying to compare DATE to string '7'
```

Should be:
```sql
-- ✅ CORRECT
WHERE DATE(event_date) >= CURRENT_DATE() - INTERVAL 7 DAYS
```

**Analysis:** These errors suggest the Genie queries are:
1. Passing day counts (7, 30) directly into WHERE clauses expecting DATE values
2. Passing date strings where numeric parameters are expected

**Recommendation:** These should be fixed in the Genie SQL queries, not in the TVFs.

---

## Bug Category 3: Cluster Rightsizing (2 errors)

### Error Details
```
[COLUMN_NOT_FOUND] potential_savings_usd
```

### Affected Queries
1. **performance Q16** - "Show me cluster right-sizing recommendations"
2. **unified_health_monitor Q18** - "Show me cluster right-sizing recommendations"

### Investigation Results

**Genie Query:**
```sql
SELECT * FROM cluster_capacity_predictions 
WHERE prediction IN ('DOWNSIZE', 'UPSIZE') 
ORDER BY prediction DESC, query_count DESC 
LIMIT 20;
```

**ML Table Schema:** `cluster_capacity_predictions`
- Has `prediction` column ✅
- Has many numeric columns (avg_duration_ms, query_count, etc.) ✅
- Does **NOT** have `potential_savings_usd` column ❌

### ✅ Fix: Column Name Correction

The Genie queries are referencing a non-existent column. This is a **Genie SQL bug**, not a TVF bug.

**Possible Solutions:**
1. Remove references to `potential_savings_usd` from the queries
2. Calculate savings based on available columns
3. Add `potential_savings_usd` to the ML predictions table

---

## 📊 Summary: TVF Bugs vs Genie SQL Bugs

| Category | Count | Type | Action Required |
|---|---|---|---|
| **UUID Casting** | 2 | Possible TVF bug | Investigate further / Add defensive casting |
| **Date Casting** | 7 | Genie SQL bug | Fix Genie SQL queries |
| **Column Not Found** | 2 | Genie SQL bug | Fix column references |

**Total Errors:** 11  
**Actual TVF Bugs:** 2 (possibly)  
**Genie SQL Bugs:** 9

---

## 🎯 Recommended Next Steps

1. **For UUID Casting (2 errors):**
   - Add defensive casting in `get_warehouse_utilization` TVF
   - Test with actual warehouse data
   - Check if Metric Views are involved

2. **For Date Casting (7 errors):**
   - Fix Genie SQL queries to use proper date parameters
   - Replace day count strings with `CURRENT_DATE() - INTERVAL X DAYS`

3. **For Column Not Found (2 errors):**
   - Update Genie queries to use existing columns
   - Or add `potential_savings_usd` to ML predictions

---

## 🚨 User Decision Needed

**Question:** Should I proceed with:

**Option A:** Fix the 2 possible TVF bugs (UUID casting) by adding defensive casting?

**Option B:** Focus on fixing the 9 Genie SQL bugs first (easier, faster)?

**Option C:** Do both in parallel?

**Your input:** Which approach would you prefer?


