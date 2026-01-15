# Genie Space: unified_health_monitor - Complete Bug Analysis

**Date:** January 9, 2026  
**Status:** 5 errors found (1 TVF bug, 4 Genie SQL bugs to fix)  
**Pass Rate:** 76% (16/21)

---

## 📊 Error Summary

| Question | Error Type | Root Cause | Status |
|---|---|---|---|
| Q12 | CAST_INVALID_INPUT | TVF bug (`get_warehouse_utilization` UUID→INT) | ⚠️ **Known TVF Bug** |
| Q18 | CAST_INVALID_INPUT | ORDER BY categorical STRING→DOUBLE | ✅ **Fixed** |
| Q19 | COLUMN_NOT_FOUND | `success_rate`, `high_risk_events` don't exist | 🔧 **To Fix** |
| Q20 | SYNTAX_ERROR | Alias spacing (`uFULL` → `u FULL`) | 🔧 **To Fix** |
| Q21 | COLUMN_NOT_FOUND | `domain` doesn't exist | 🔧 **To Fix** |

---

## ✅ Error 1: Q12 - **KNOWN TVF BUG**

### Error Message
```
[CAST_INVALID_INPUT] UUID '01f0ec68-ef1e-1b09-9bf6-b3c9ab28f205' cannot be cast to INT
```

### Status
⚠️ **Known TVF Bug** - Same as cost Q19 and performance Q7

**Action:** No Genie SQL fix needed - TVF implementation bug  
**Reference:** `GENIE_TVF_BUGS_DETAILED_FIX_GUIDE.md` - Bug #1

---

## ✅ Error 2: Q18 - **FIXED** (Duplicate of performance Q16)

### Error Message
```
[CAST_INVALID_INPUT] 'DOWNSIZE' (STRING) cannot be cast to DOUBLE
```

### Problem
Same as performance Q16 - `ORDER BY prediction DESC` on categorical STRING triggers implicit DOUBLE casting.

### Fix Applied
```sql
-- BEFORE
ORDER BY prediction DESC, query_count DESC

-- AFTER
ORDER BY query_count DESC, prediction ASC
```

**Status:** ✅ **FIXED & DEPLOYED**

---

## 🔧 Error 3: Q19 - **COLUMN_NOT_FOUND** (2 columns)

### Error Messages
1. `success_rate` cannot be resolved
2. `high_risk_events` cannot be resolved

### Question
"🔬 DEEP RESEARCH: Platform health overview - combine cost, performance, reliability, security, and quality KPIs"

### Root Cause Analysis

**Issue 1: `success_rate`**

Query uses:
```sql
security_health AS (
  SELECT 
    MEASURE(success_rate) as auth_success_rate,  -- ❌ Column doesn't exist!
    MEASURE(high_risk_events) as high_risk_count,
    MEASURE(unique_users) as active_users
  FROM mv_security_events
)
```

**Ground Truth (`mv_security_events`):**
- ✅ `failure_rate` exists (DECIMAL)
- ❌ `success_rate` doesn't exist

**Fix:** Use `(100 - MEASURE(failure_rate))` or just use `failure_rate`

---

**Issue 2: `high_risk_events`**

**Ground Truth (`mv_security_events`):**
- ✅ `sensitive_events` exists (LONG)
- ✅ `failed_events` exists (LONG)
- ❌ `high_risk_events` doesn't exist

**Fix:** Change to `sensitive_events` (aligns with "high risk" concept)

---

### Complete Fix

```sql
-- BEFORE
security_health AS (
  SELECT 
    MEASURE(success_rate) as auth_success_rate,  -- ❌
    MEASURE(high_risk_events) as high_risk_count,  -- ❌
    MEASURE(unique_users) as active_users
  FROM mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
)

-- AFTER
security_health AS (
  SELECT 
    (100 - MEASURE(failure_rate)) as auth_success_rate,  -- ✅ Calculate from failure_rate
    MEASURE(sensitive_events) as high_risk_count,  -- ✅ Use sensitive_events
    MEASURE(unique_users) as active_users
  FROM mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
)
```

---

## 🔧 Error 4: Q20 - **SYNTAX_ERROR** (Alias Spacing)

### Error Message
```
[PARSE_SYNTAX_ERROR] Syntax error at or near 'OUTER': missing ')'
```

### Question
"🔬 DEEP RESEARCH: Cost optimization opportunities - combine underutilized clusters, right-sizing, and tagging gaps"

### Root Cause
Missing space between table alias and JOIN keyword: `uFULL` → `u FULL`

### Problematic SQL
```sql
FROM underutilized uFULL OUTER JOIN rightsizing r  -- ❌ uFULL (no space!)
```

### Fix
```sql
-- BEFORE
FROM underutilized uFULL OUTER JOIN rightsizing r ON u.cluster_name = r.cluster_name

-- AFTER
FROM underutilized u FULL OUTER JOIN rightsizing r ON u.cluster_name = r.cluster_name
```

**Pattern:** Same alias spacing bug as Session 6 (cost Q23, Q25, performance Q23, unified Q19-Q21)

---

## 🔧 Error 5: Q21 - **COLUMN_NOT_FOUND** (`domain`)

### Error Message
```
[UNRESOLVED_COLUMN.WITH_SUGGESTION] `domain` cannot be resolved.
Did you mean: year, month, cloud, run_as, env_tag
```

### Question
"🔬 DEEP RESEARCH: Executive FinOps dashboard - cost trends, efficiency, commit utilization, and optimization opportunities"

### Root Cause
`mv_cost_analytics` has NO `domain` column.

### Problematic SQL
```sql
cost_by_domain AS (
  SELECT 
    domain,  -- ❌ Column doesn't exist!
    MEASURE(total_cost) as domain_cost
  FROM mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY domain
  ORDER BY domain_cost DESC
  LIMIT 5
)
```

### Ground Truth (`mv_cost_analytics`)
**Available "domain-like" columns:**
- `entity_type` - STRING (job, cluster, warehouse, etc.)
- `team_tag` - STRING
- `billing_origin_product` - STRING
- `sku_name` - STRING

**Error suggestions indicate:** `env_tag` is closer match

### Fix
```sql
-- OPTION 1: Use entity_type (recommended - represents billing domain)
cost_by_domain AS (
  SELECT 
    entity_type as domain,  -- ✅ Use entity_type
    MEASURE(total_cost) as domain_cost
  FROM mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY entity_type
  ORDER BY domain_cost DESC
  LIMIT 5
)

-- OPTION 2: Use team_tag (if "domain" means business team)
cost_by_domain AS (
  SELECT 
    team_tag as domain,  -- ✅ Use team_tag
    MEASURE(total_cost) as domain_cost
  FROM mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND team_tag IS NOT NULL
  GROUP BY team_tag
  ORDER BY domain_cost DESC
  LIMIT 5
)
```

**Recommended:** Use `entity_type` (aligns with "cost by domain" = job costs vs cluster costs vs SQL costs)

---

## 📊 Summary of Fixes Needed

### Fixes to Apply
1. ✅ **Q18** - Already fixed (ORDER BY categorical)
2. 🔧 **Q19** - Change `success_rate` → `(100 - failure_rate)`, `high_risk_events` → `sensitive_events`
3. 🔧 **Q20** - Fix alias spacing `uFULL` → `u FULL`
4. 🔧 **Q21** - Change `domain` → `entity_type`

### Expected Impact
- **Before:** 16/21 passed (76%)
- **After:** 20/21 passed (95%)
- **Remaining:** 1 TVF bug (Q12 - not fixable in Genie SQL)

---

## 🎯 Lessons Learned

### 1. Metric View Schema Verification
**Problem:** Assumed `success_rate` exists when only `failure_rate` does  
**Solution:** Always check `docs/reference/actual_assets/mvs.md` for exact column names

### 2. Alias Spacing Bugs Persist
**Pattern:** Missing spaces between alias and JOIN keyword (`uFULL`, `tcCROSS`)  
**Prevention:** Validate SQL formatting before deployment

### 3. Generic Column Names Need Ground Truth
**Problem:** Used generic name like `domain` without verifying  
**Solution:** Check actual schema for closest semantic match (`entity_type`)

### 4. Semantic Mapping for Column Names
**Pattern:** When logical column doesn't exist, find semantic equivalent:
- `domain` → `entity_type` (cost domain = job/cluster/warehouse)
- `high_risk_events` → `sensitive_events` (high risk = sensitive actions)
- `success_rate` → calculate from `failure_rate`

---

## 📚 Reference

### Files to Update
- `src/genie/unified_health_monitor_genie_export.json` (Q18, Q19, Q20, Q21)

### Ground Truth Files Used
- `docs/reference/actual_assets/mvs.md` - Verified `mv_security_events` and `mv_cost_analytics` schemas

### Related Documents
- `GENIE_Q16_BUG_FIX.md` - performance Q18 fix (duplicate pattern)
- `GENIE_TVF_BUGS_DETAILED_FIX_GUIDE.md` - Q12 TVF bug reference
- `GENIE_ALIAS_SPACING_FIXES.md` - Session 6 similar fixes

---

**Status:** Analysis complete, ready to apply 3 fixes (Q19, Q20, Q21)  
**Expected:** 95% pass rate after fixes  
**Deployment:** Bundle deploy after Q19, Q20, Q21 fixes

