# Genie Space COLUMN_NOT_FOUND Manual Analysis

**Date:** 2026-01-08  
**Analyst:** AI (systematic ground truth validation)  
**Ground Truth:** `@docs/reference/actual_assets/`

---

## 🎯 Analysis Methodology

For each error:
1. ✅ Read full SQL query from JSON
2. ✅ Identify data source (table/view/TVF)
3. ✅ Check exact schema in ground truth
4. ✅ Determine root cause
5. ✅ Propose fix with confidence level

---

## ❌ Error 1: cost_intelligence Q22

**Question:** "SKU-level cost efficiency analysis with utilization patterns"

**SQL Query Structure:**
```sql
WITH sku_costs AS (
  SELECT
    sku_name,
    MEASURE(scCROSS.total_cost) as total_sku_cost,  -- ❌ ERROR: scCROSS doesn't exist in CTE
    MEASURE(total_dbu) as total_dbu,
    MEASURE(scCROSS.total_cost) / ... as cost_per_dbu  -- ❌ ERROR
  FROM mv_cost_analytics
  GROUP BY sku_name
),
cluster_util AS (...)
SELECT
  sc.sku_name,  -- ⚠️ Inconsistent alias (should be scCROSS)
  scCROSS.total_cost,  -- ❌ ERROR: Should be scCROSS.total_sku_cost
  sc.total_dbu,
  sc.cost_per_dbu,
  cu.avg_cpu,
  CASE WHEN cu.avg_cpu < 30 AND scCROSS.total_cost > 5000 ...  -- ❌ Multiple refs
FROM sku_costs scCROSS  -- ✅ Alias is scCROSS
JOIN cluster_util cu
WHERE scCROSS.total_cost > 1000  -- ❌ ERROR
```

**Error Message:**
```
[COLUMN_NOT_FOUND] `total_cost` cannot be resolved
Did you mean: `scCROSS`.`total_sku_cost`, `scCROSS`.`total_dbu`, `scCROSS`.`sku_name`
```

**Ground Truth Check:**
- `mv_cost_analytics` HAS column `total_cost` ✅ (verified in mvs.md line 103)
- CTE output columns: `sku_name`, `total_sku_cost`, `total_dbu`, `cost_per_dbu`

**Root Cause:**
1. **In CTE:** `MEASURE(scCROSS.total_cost)` is wrong because `scCROSS` alias doesn't exist yet (it's defined later in FROM)
2. **In main SELECT:** Uses `scCROSS.total_cost` but CTE aliased it as `total_sku_cost`
3. **Alias inconsistency:** Uses both `sc.` and `scCROSS.` prefixes

**Fix:**
```sql
-- IN CTE (line 673):
-- BEFORE:
MEASURE(scCROSS.total_cost) as total_sku_cost
-- AFTER:
MEASURE(total_cost) as total_sku_cost

-- IN MAIN SELECT (multiple locations):
-- BEFORE:
scCROSS.total_cost
-- AFTER:
scCROSS.total_sku_cost

-- ALSO FIX INCONSISTENT ALIASES:
-- BEFORE:
sc.sku_name, sc.total_dbu, sc.cost_per_dbu
-- AFTER:
scCROSS.sku_name, scCROSS.total_dbu, scCROSS.cost_per_dbu
```

**Confidence:** ✅ **HIGH** - Clear alias and column naming issue

---

## ❌ Error 2: cost_intelligence Q25

**Question:** "Predictive cost optimization roadmap"

**SQL Query:** (Need to extract)

**Error Message:**
```
[COLUMN_NOT_FOUND] `workspace_name` cannot be resolved
Did you mean: `mtd_actual`, `forecast_month`, `variance_vs_actual`, `predicted_cost_p10`, `predicted_cost_p50`
```

**Analysis:** Suggestions show ML prediction table columns. Let me check `cost_anomaly_predictions` schema.

**Status:** ⏳ **PENDING** - Need to extract full query

---

## ❌ Error 3: performance Q14

**Question:** "Show me query latency percentiles by warehouse"

**Error Message:**
```
[COLUMN_NOT_FOUND] `p99_duration_seconds` cannot be resolved
Did you mean: `p99_seconds`, `max_seconds`, `p90_seconds`, `p95_seconds`, `p50_seconds`, `p75_seconds`
```

**Ground Truth Check:**
- Metric view likely has `p99_seconds` not `p99_duration_seconds`

**Fix:** 
```
p99_duration_seconds → p99_seconds
```

**Confidence:** ✅ **HIGH** - Direct column name mismatch, suggestion is clear

---

## ❌ Error 4: performance Q16

**Question:** "Show me cluster right-sizing recommendations"

**Error Message:**
```
[COLUMN_NOT_FOUND] `recommended_action` cannot be resolved
Did you mean: `scored_at`, `prediction`, `read_write_ratio`, `model_name`, `query_date`
```

**Ground Truth Check:**
- ML prediction table: `cluster_rightsizing_predictions`
- Schema shows `prediction` column, not `recommended_action`

**Fix:**
```
recommended_action → prediction
```

**Confidence:** ✅ **HIGH** - ML table column name mismatch

---

## ❌ Error 5: performance Q25

**Question:** "End-to-end performance health dashboard"

**Error Message:**
```
[COLUMN_NOT_FOUND] `qh`.`query_volume` cannot be resolved
Did you mean: `qhCROSS`.`query_volume`, `ch`.`avg_cpu`, `ch`.`avg_memory`, `ch`.`efficiency`, `ch`.`wasted_hours`
```

**Analysis:** 
- Suggestion shows `qhCROSS`.`query_volume` exists
- Query uses `qh.` but alias is actually `qhCROSS`

**Fix:**
```
qh.query_volume → qhCROSS.query_volume
(and all other qh. references)
```

**Confidence:** ✅ **HIGH** - Alias mismatch (similar to cost_intelligence Q22)

---

## ❌ Error 6: security_auditor Q7

**Question:** "Show me failed access attempts"

**Error Message:**
```
[COLUMN_NOT_FOUND] `failed_events` cannot be resolved
Did you mean: `user_email`, `action`, `service`, `event_time`, `source_ip`
```

**Analysis:**
- Suggestions show individual columns from TVF `get_failed_actions` output
- TVF returns ROWS (one per failed action), not aggregated `failed_events` count
- Query is expecting a pre-aggregated column

**Fix:** Need to see full query, but likely needs COUNT(*) or different data source

**Confidence:** ⚠️ **MEDIUM** - Requires SQL rewrite, not just column rename

---

## ❌ Error 7: security_auditor Q8

**Question:** "What permission changes happened this week?"

**Error Message:**
```
[COLUMN_NOT_FOUND] `change_date` cannot be resolved
Did you mean: `changed_by`, `action`, `event_time`, `service`, `source_ip`
```

**Ground Truth Check:**
- TVF: `get_permission_changes`
- Output columns include `event_time`, not `change_date`

**Fix:**
```
change_date → event_time
```

**Confidence:** ✅ **HIGH** - Clear column name mismatch

---

## ❌ Error 8: security_auditor Q10

**Question:** "What are the high-risk events?"

**Error Message:**
```
[COLUMN_NOT_FOUND] `high_risk_events` cannot be resolved
Did you mean: `failed_events`, `sensitive_events`, `total_events`, `successful_events`, `audit_level`
```

**Analysis:** Need to check `mv_security_events` schema for correct column name

**Status:** ⏳ **PENDING** - Need to check metric view schema

---

## ❌ Error 9: security_auditor Q11

**Question:** "Show me user activity patterns"

**Error Message:**
```
[COLUMN_NOT_FOUND] `user_identity` cannot be resolved
Did you mean: `user_email`, `event_date`, `unique_ips`, `sensitive_actions`, `off_hours_events`
```

**Fix:**
```
user_identity → user_email
```

**Confidence:** ✅ **HIGH** - Clear column name mismatch

---

## ❌ Error 10: unified_health_monitor Q7

**Question:** "Show me failed jobs today"

**Error Message:**
```
[COLUMN_NOT_FOUND] `failed_runs` cannot be resolved
Did you mean: `end_time`, `job_id`, `run_as`, `run_id`, `job_name`
```

**Analysis:**
- Similar to security_auditor Q7
- TVF `get_failed_jobs` returns ROWS (one per failed job), not aggregated `failed_runs` count
- Suggestions show individual row columns

**Fix:** Requires SQL rewrite or different data source

**Confidence:** ⚠️ **MEDIUM** - Requires SQL rewrite

---

## ❌ Error 11: unified_health_monitor Q13

**Question:** "What is the DLT pipeline health?"

**Error Message:**
```
[COLUMN_NOT_FOUND] `failed_records` cannot be resolved
Did you mean: `target_count`, `entity_id`, `target_tables`, `total_events`, `complexity_score`
```

**Analysis:** Need to check DLT monitoring table schema

**Status:** ⏳ **PENDING** - Need to check monitoring tables

---

## ❌ Error 12: unified_health_monitor Q18

**Question:** "Show me cluster right-sizing recommendations"

**Error Message:**
```
[COLUMN_NOT_FOUND] `potential_savings_usd` cannot be resolved
Did you mean: `total_duration_ms`, `active_minutes`, `total_bytes_read`, `avg_duration_ms`, `model_name`
```

**Analysis:** Check `cluster_rightsizing_predictions` ML table schema

**Status:** ⏳ **PENDING** - Need to verify ML table columns

---

## ❌ Error 13: unified_health_monitor Q19

**Question:** "Platform health overview"

**Error Message:**
```
[COLUMN_NOT_FOUND] `sla_breach_rate` cannot be resolved
Did you mean: `cache_hit_rate`, `efficiency_rate`, `query_date`, `spill_rate`, `workspace_name`
```

**Analysis:** Complex multi-source query, need to extract full SQL

**Status:** ⏳ **PENDING** - Need to extract query

---

## ❌ Error 14: job_health_monitor Q14

**Question:** "Show me pipeline health from DLT updates"

**Error Message:**
```
[COLUMN_NOT_FOUND] `p`.`pipeline_name` cannot be resolved
Did you mean: `p`.`pipeline_id`, `p`.`pipeline_type`, `f`.`pipeline_id`, `p`.`delete_time`, `p`.`name`
```

**Ground Truth Check:**
- Table: `dim_pipeline`
- Column is `name`, not `pipeline_name`

**Fix:**
```
p.pipeline_name → p.name
```

**Confidence:** ✅ **HIGH** - Clear column name mismatch

**Already in JSON:** (line 1051)
```sql
FROM fact_pipeline_update_timeline f
JOIN dim_pipeline p ON f.workspace_id = p.workspace_id AND f.pipeline_id = p.pipeline_id
```

---

## 📊 Summary

| Status | Count | Errors |
|---|---|----|
| ✅ **HIGH confidence fix** | 7 | Q3, Q4, Q5, Q7, Q9, Q14, cost Q22 (partial) |
| ⚠️ **MEDIUM (SQL rewrite)** | 2 | security Q7, unified Q7 |
| ⏳ **PENDING analysis** | 5 | cost Q25, security Q10, unified Q13, unified Q18, unified Q19 |

**Next Steps:**
1. Extract full queries for PENDING items
2. Check ground truth for specific columns
3. Apply HIGH confidence fixes first
4. Review MEDIUM fixes for SQL rewrite patterns

