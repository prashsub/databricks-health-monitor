# Genie Space Fixes Post-Mortem

**Date:** 2026-01-08  
**Status:** Partial success - 1/9 fixes confirmed working  
**Overall Impact:** +4% validation success (68% → 72%)

---

## 🎯 What Was Attempted

Created automated fix script (`scripts/fix_genie_ground_truth_v2.py`) to fix:
1. `COLUMN_NOT_FOUND` errors (8 fixes attempted)
2. `UNRESOLVABLE_TABLE_VALUED_FUNCTION` error (1 fix attempted)

---

## ❌ Why Most Fixes Failed

### Root Cause: Guessing Instead of Verifying

| What I Did | What I Should Have Done |
|---|---|
| ❌ Pattern matching column names | ✅ Read full SQL query context |
| ❌ Assumed similar names = correct | ✅ Check EXACT TVF/table output schema |
| ❌ Applied fixes without testing | ✅ Verify each fix against ground truth |

### Concrete Examples:

#### Example 1: security_auditor Q7 ❌
```python
# My Fix:
"off_hours_events" → "failed_events"

# Reality:
# TVF `get_failed_actions` returns ROWS (user_email, action, service...)
# Query expects aggregated column `failed_events` which doesn't exist
# Correct fix: Need to COUNT(*) the TVF results or use different data source
```

#### Example 2: job_health_monitor Q6 ❌ → ✅
```python
# My Fix (WRONG):
"p95_duration_min" → "p95_duration_minutes"

# Reality:
# TVF `get_job_duration_percentiles` doesn't have P95 AT ALL!
# Only has: p50_duration_min, p75_duration_min, p90_duration_min, p99_duration_min

# Correct Fix:
"p95_duration_minutes" → "p90_duration_min"
```

---

## ✅ The ONE Fix That Worked

### job_health_monitor Q6

**Before:**
```sql
SELECT * FROM get_job_duration_percentiles(30) 
ORDER BY p95_duration_minutes DESC LIMIT 15;
```

**After:**
```sql
SELECT * FROM get_job_duration_percentiles(30) 
ORDER BY p90_duration_min DESC LIMIT 15;
```

**Why It Worked:** 
- Checked TVF definition in `@docs/reference/actual_assets/tvfs.md`
- Confirmed P95 doesn't exist
- Chose next closest percentile (P90)
- Verified column name suffix (`_min` not `_minutes`)

---

## 📊 Validation Results

### Before Ground Truth Fixes:
- Success: 68/107 = **68%**
- Failures: 39 errors

### After Ground Truth Fixes:
- Success: 77/107 = **72%**
- Failures: 30 errors
- **Improvement:** +4% (but unclear if my fixes helped or just shifted errors)

---

## 🔍 Remaining Errors Breakdown

### Missing Column Errors: **15 errors** (need manual investigation)

#### cost_intelligence (2 errors)
1. Q22: `scCROSS.total_cost` - **Alias issue, not simple column rename**
2. Q25: `workspace_name` - Context: `cost_anomaly_predictions` table

#### performance (3 errors)
1. Q14: `p99_duration_seconds` → Use `p99_seconds`
2. Q16: `recommended_action` → Use `prediction` (ML table column)
3. Q25: `qh.query_volume` → Alias issue (multiple `qh.` references)

#### security_auditor (5 errors)
1. Q7: `failed_events` - **TVF returns rows, not aggregated count**
2. Q8: `change_date` → `event_time` (from `get_permission_changes`)
3. Q9: `event_count` - **TVF returns rows, not aggregated count**
4. Q10: `high_risk_events` - **Need to check mv_security_events schema**
5. Q11: `user_identity` → `user_email`

#### unified_health_monitor (4 errors)
1. Q7: `failed_runs` - **TVF returns rows, not aggregated count**
2. Q13: `failed_records` - **Need to check DLT monitoring table schema**
3. Q18: `potential_savings_usd` → **Check cluster_rightsizing_predictions**
4. Q19: `sla_breach_rate` - **Complex multi-source query**

#### job_health_monitor (1 error)
1. Q14: `f.update_state` → `f.result_state`

### Other Error Types:

- **SYNTAX_ERROR: 6 errors** (malformed SQL)
- **CAST_INVALID_INPUT: 7 errors** (UUID → INT, STRING → DATE conversions)
- **NESTED_AGGREGATE_FUNCTION: 2 errors** (SQL logic issue)
- **UNRESOLVABLE_TABLE_VALUED_FUNCTION: 1 error** (wrong TVF name)

---

## 🎯 Recommended Next Steps

### 1. Manual Investigation Required ⚠️

For each remaining `COLUMN_NOT_FOUND` error:
1. ✅ Read the FULL SQL query
2. ✅ Check the EXACT TVF/table definition in `@docs/reference/actual_assets`
3. ✅ Understand the query intent (aggregation vs row-level data)
4. ✅ Verify the fix in isolation before applying

### 2. Focus on High-Impact Fixes First

**Priority 1: Simple Column Renames** (verify exact name first)
- performance Q14: `p99_duration_seconds` → `p99_seconds`
- security_auditor Q8: `change_date` → `event_time`
- security_auditor Q11: `user_identity` → `user_email`
- job_health_monitor Q14: `f.update_state` → `f.result_state`

**Priority 2: ML Table Columns** (check schema carefully)
- performance Q16: `recommended_action` → `prediction`
- cost_intelligence Q25: `workspace_name` (verify column exists)
- unified_health_monitor Q18: `potential_savings_usd` (check column name)

**Priority 3: Complex Query Rewrites** (need SQL logic changes)
- security_auditor Q7, Q9: TVFs return rows, not counts
- unified_health_monitor Q7: Similar issue
- cost_intelligence Q22: Alias resolution
- performance Q25: Multiple alias fixes

---

## 📈 Success Metrics

| Metric | Value |
|---|---|
| **Total Queries** | 123 |
| **Currently Passing** | 77 (72%) |
| **Remaining Failures** | 30 (28%) |
| **My Confirmed Fixes** | 1/9 (11%) |
| **Need Manual Review** | 15 COLUMN_NOT_FOUND errors |

---

## 🧠 Key Learnings

1. **Automated fixes only work for simple renames** where:
   - Column name is clearly wrong
   - Ground truth has exact match
   - No context needed (not part of aggregation, JOIN, etc.)

2. **Manual review required when:**
   - TVFs return rows vs aggregated columns
   - Aliases are involved
   - Complex queries with CTEs
   - ML prediction table columns (schema varies)

3. **Ground truth is necessary but not sufficient:**
   - Must understand SQL query context
   - Must know if query expects rows or aggregated data
   - Must verify column actually exists in that context

---

## 🔗 References

- Ground Truth Files: `@docs/reference/actual_assets/`
- Validation Output: Latest run (123 queries, 72% pass rate)
- Fix Script: `scripts/fix_genie_ground_truth_v2.py`
- Previous Fixes: `docs/deployment/GENIE_GROUND_TRUTH_V2_FIXES.md`

