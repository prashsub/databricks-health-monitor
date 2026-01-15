# Genie Remaining Errors Analysis

**Date:** January 9, 2026  
**Status:** 150 questions deployed, some SQL syntax errors remain

---

## Error Summary

**Total Errors:** 15 across 3 Genie spaces  
- **performance**: 1 error
- **unified_health_monitor**: 3 errors  
- **data_quality_monitor**: 11 errors

**Pass Rate:** 135/150 (90%)

---

## Errors by Category

### 1. CAST_INVALID_INPUT (2 errors)

**Files:** performance Q16, unified Q18  
**Error:** `The value 'DOWNSIZE' of the type "STRING" cannot be cast to "DOUBLE"`  
**Query Pattern:** `WHERE prediction IN ('DOWNSIZE', 'UPSIZE')`

**Root Cause:** Query tries to ORDER BY query_count but query_count isn't in SELECT  
**Fix:** Remove ORDER BY clause (already applied in Session 12, may need redeployment)

---

### 2. TABLE_NOT_FOUND (3 errors)

| File | Question | Missing Table | Fix |
|------|----------|---------------|-----|
| unified Q23 | Security posture | `security_anomaly_predictions` | Change schema to `${feature_schema}` |
| data_quality Q16 | Quality distribution | `fact_data_quality` | Already uses source table in CTE |
| data_quality Q18 | Quality drift | `fact_table_lineage_drift_metrics` | Add `_monitoring` suffix to schema |

---

### 3. SYNTAX_ERROR (6 errors)

All in `data_quality_monitor` Q21-Q25:

**Pattern:** Extra `)` after TVF calls in CTEs

```sql
# ❌ WRONG:
FROM get_table_freshness(24))
),

# ✅ CORRECT:
FROM get_table_freshness(24)
),
```

**Affected:**
- Q21: `get_table_freshness(24))`
- Q22: Similar pattern
- Q23: `get_data_lineage_summary('main', '%'))`
- Q24: `get_tables_failing_quality(24))`
- Q25: Missing WHERE/GROUP BY orderQ24 also has missing `)` before COALESCE

---

### 4. UNRESOLVED_COLUMN (4 errors)

| File | Question | Column | Issue |
|------|----------|--------|-------|
| data_quality Q14 | ML model performance | `sku_name` | MEASURE() query structure issue |
| data_quality Q15 | ML prediction accuracy | `sku_name` | MEASURE() query structure issue |
| data_quality Q17 | ML prediction accuracy | `sku_name` | MEASURE() query structure issue |
| data_quality Q20 | Quality distribution | `evaluation_date` | Column doesn't exist in mv_data_quality |

**Q14/Q15/Q17 Root Cause:**  
The error suggests `fact_usage.sku_name` exists, but query references Metric View. This indicates the Metric View definition may have issues or the query structure needs adjustment.

**Q20 Root Cause:**  
Metric View `mv_data_quality` doesn't have `evaluation_date` column

---

## Recommended Fix Strategy

### Priority 1: Fix Syntax Errors (Q21-Q25)
- Search/replace pattern: `\(([^)]+)\)\)\s*\n\s*\),` → `(\1)\n),`
- 5 queries affected
- **Impact:** +5 questions (90% → 93%)

### Priority 2: Fix TABLE_NOT_FOUND (Q16, Q18, Q23)
- Q16: Already fixed (verify deployment)
- Q18: Add `_monitoring` suffix
- Q23: Change ML schema reference  
- **Impact:** +3 questions (93% → 95%)

### Priority 3: Fix CAST_INVALID_INPUT (Q16, Q18)
- Remove ORDER BY clauses (already fixed Session 12)
- Verify deployment
- **Impact:** +2 questions (95% → 96.7%)

### Priority 4: Fix UNRESOLVED_COLUMN (Q14, Q15, Q17, Q20)
- Q14/Q15/Q17: Complex - may need query redesign or Metric View fix
- Q20: Remove `evaluation_date` filter
- **Impact:** +4 questions (96.7% → 100%)

---

## Expected Timeline

1. **Immediate (5 min):** Fix syntax errors → 93% pass rate
2. **Short term (10 min):** Fix TABLE_NOT_FOUND → 95% pass rate  
3. **Medium term (15 min):** Fix CAST_INVALID_INPUT → 96.7% pass rate
4. **Complex (30 min):** Fix UNRESOLVED_COLUMN → 100% pass rate

---

## Files to Modify

1. `src/genie/data_quality_monitor_genie_export.json` (11 fixes)
2. `src/genie/unified_health_monitor_genie_export.json` (3 fixes)  
3. `src/genie/performance_genie_export.json` (1 fix - verify)

---

**Next Step:** Run comprehensive fix script for Priority 1-3 errors (10 easy fixes)

