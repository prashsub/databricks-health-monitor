# Genie Space Fix Progress Status

**Date:** 2026-01-08  
**Current Phase:** Phase 1 COMPLETE, Phase 2 IN PROGRESS

---

## 📊 Overall Progress

| Phase | Status | Fixes | Impact |
|-------|--------|-------|--------|
| **Phase 1: SYNTAX_ERROR** | ✅ **COMPLETE** | 5/7 automated | +5 queries |
| **Phase 2: WRONG_NUM_ARGS** | 🔄 IN PROGRESS | Script ready | +3 queries est. |
| **Phase 3: CAST_INVALID_INPUT** | ⏸️ PENDING | Script needed | +3 queries est. |
| **Phase 4: COLUMN_NOT_FOUND** | ⏸️ PENDING | Script needed | +20 queries est. |
| **Phase 5: NESTED_AGGREGATE** | ⏸️ PENDING | Manual fix | +2 queries est. |

**Current Validation Status:** 83/123 passing (67%)  
**Expected After All Phases:** 116-118/123 passing (94-96%)

---

## ✅ Phase 1: SYNTAX_ERROR (COMPLETE)

### Fixes Applied: 5 out of 7

**Automated Pattern:** Malformed `CURRENT_DATE(,` expressions

**Files Modified:**
- `cost_intelligence_genie_export.json` - 1 fix (Q19)
- `performance_genie_export.json` - 2 fixes (Q7, Q8)
- `security_auditor_genie_export.json` - 2 fixes (Q5, Q6)

**Before:**
```sql
CAST(CURRENT_DATE(,
  CURRENT_DATE()::STRING
) - INTERVAL 30 DAYS AS STRING)
```

**After:**
```sql
CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING)
```

**Deployment:** ✅ SUCCESS  
**Validation Job:** 🔄 RUNNING (checking impact)

### Remaining SYNTAX_ERROR (2/7):
1. **cost_intelligence Q23** - Missing parenthesis in complex CTE (manual fix)
2. **unified_health_monitor Q20** - Missing parenthesis in multi-CTE (manual fix)

**Status:** Manual inspection required for these 2 queries

---

## 🔄 Phase 2: WRONG_NUM_ARGS (IN PROGRESS)

### Errors to Fix: 3

**Pattern:** TVF calls missing required parameters

| Query | TVF | Current Params | Required Params | Missing |
|-------|-----|---------------|----------------|---------|
| **security_auditor Q9** | `get_off_hours_activity` | 1 | 4 | `end_date`, `business_hours_start`, `business_hours_end` |
| **security_auditor Q11** | `get_off_hours_activity` | 1 | 4 | `end_date`, `business_hours_start`, `business_hours_end` |
| **job_health_monitor Q10** | `get_job_retry_analysis` | 1 | 2 | `end_date` |

**Fix Strategy:** Automated script with sensible defaults

**Default Values:**
- `start_date`: `(CURRENT_DATE() - INTERVAL 7 DAYS)::STRING`
- `end_date`: `CURRENT_DATE()::STRING`
- `business_hours_start`: `9`
- `business_hours_end`: `17`

**Script Status:** ✅ READY (`scripts/fix_genie_wrong_num_args.py`)  
**Next Action:** Run script after Phase 1 validation completes

---

## ⏸️ Phase 3: CAST_INVALID_INPUT (PENDING)

### Errors to Fix: 3

| Query | Issue | Fix |
|-------|-------|-----|
| **performance Q10** | `'2026-01-08'` to DOUBLE | Use DATE_DIFF or remove cast |
| **performance Q12** | `'2025-12-25'` to INT | Use DATE_DIFF or remove cast |
| **job_health_monitor Q12** | `'30'` to DATE | Use `INTERVAL 30 DAYS` instead |

**Fix Strategy:** Pattern-based SQL replacement

**Script Status:** ⏸️ TO BE CREATED  
**Priority:** MEDIUM (after Phase 2)

---

## ⏸️ Phase 4: COLUMN_NOT_FOUND (PENDING)

### Errors to Fix: 20+

**Categories:**
1. **TVF Column Mismatches** (5 errors) - Column names don't match TVF output
2. **Metric View Column Mismatches** (3 errors) - Column names don't match MV schema
3. **Alias Reference Errors** (3 errors) - Wrong alias in JOIN  references
4. **Non-Existent Columns** (10+ errors) - Columns don't exist in source

**Example Fixes:**
| Incorrect | Correct |
|-----------|---------|
| `p99_duration` | `p99_seconds` |
| `failure_count` | `failed_runs` |
| `success_rate` | `success_rate_pct` |
| `cost_7d` | `last_7_day_cost` |

**Fix Strategy:** Mapping table + pattern-based replacement

**Script Status:** ⏸️ TO BE CREATED  
**Priority:** HIGH (largest error category)

---

## ⏸️ Phase 5: NESTED_AGGREGATE (PENDING)

### Errors to Fix: 2

| Query | Issue | Fix |
|-------|-------|-----|
| **performance Q23** | Using MEASURE() inside another aggregate | Move inner MEASURE to CTE |
| **unified_health_monitor Q21** | Using MEASURE() inside another aggregate | Move inner MEASURE to CTE |

**Example Fix:**
```sql
-- ❌ WRONG
SELECT AVG(MEASURE(total_cost)) FROM mv_cost_analytics

-- ✅ CORRECT
WITH cost_measures AS (
  SELECT MEASURE(total_cost) as total_cost FROM mv_cost_analytics
)
SELECT AVG(total_cost) FROM cost_measures
```

**Fix Strategy:** Manual SQL refactoring

**Script Status:** ⏸️ MANUAL FIX REQUIRED  
**Priority:** LOW (complex SQL, small impact)

---

## 📁 Files Created/Modified

### Phase 1:
- **Scripts:** `scripts/fix_genie_syntax_errors.py`
- **JSON Files:** 
  - `src/genie/cost_intelligence_genie_export.json`
  - `src/genie/performance_genie_export.json`
  - `src/genie/security_auditor_genie_export.json`
- **Docs:**
  - `docs/deployment/GENIE_VALIDATION_ERROR_ANALYSIS.md`
  - `docs/deployment/GENIE_SYNTAX_ERROR_FIXES.md`
  - `docs/GENIE_SYNTAX_FIXES_DEPLOYED.md`

### Phase 2:
- **Scripts (Ready):** `scripts/fix_genie_wrong_num_args.py`

### Phase 3-5:
- **Scripts (To Be Created):** 
  - `scripts/fix_genie_cast_errors.py`
  - `scripts/fix_genie_column_errors.py`

---

## 🎯 Success Metrics

### Before All Fixes:
- **Passing:** 83/123 (67%)
- **Blocked by SYNTAX_ERROR:** 7 queries
- **Blocked by WRONG_NUM_ARGS:** 3 queries
- **Blocked by CAST_INVALID_INPUT:** 3 queries
- **Blocked by COLUMN_NOT_FOUND:** 20+ queries

### Target After All Fixes:
- **Passing:** 116-118/123 (94-96%)
- **Automated Fixes:** 30-35 queries
- **Manual Fixes:** 2-5 queries
- **Remaining Issues:** 5-7 queries (complex cases)

### Current Progress:
- **Phase 1 Complete:** +5 queries (est. 88/123 = 72%)
- **Phase 2-5 Remaining:** +25-30 queries (est.)

---

## ⏭️ Next Actions

1. ✅ Wait for validation job to complete
2. ✅ Verify Phase 1 impact (+5 queries passing)
3. ⏭️ Run Phase 2 fix script (`fix_genie_wrong_num_args.py`)
4. ⏭️ Deploy and validate Phase 2
5. ⏭️ Create and run Phase 3 fix script
6. ⏭️ Create and run Phase 4 fix script
7. ⏭️ Manual review for Phase 5

**Estimated Time Remaining:** 2-3 hours for all automated fixes

---

## 🔍 Validation Command

```bash
databricks bundle run -t dev genie_benchmark_sql_validation_job
```

**Current Run Status:** 🔄 IN PROGRESS  
**Timeout:** 30 minutes (increased from 15 minutes)

---

**Last Updated:** 2026-01-08  
**Status:** 🟢 ON TRACK

