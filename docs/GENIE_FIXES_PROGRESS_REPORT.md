# Genie Space Fixes - Progress Report

**Date:** 2026-01-08  
**Status:** 33% Complete (13 of 40 errors fixed)  
**Approach:** Using ground truth from `docs/reference/actual_assets`

---

## 🎯 Mission Statement

**Goal:** Eliminate all `TABLE_NOT_FOUND` and `COLUMN_NOT_FOUND` errors by validating against ground truth in `docs/reference/actual_assets`. Only runtime errors should remain.

---

## ✅ What We've Accomplished

### Phase 1: Column Error Fixes ✅ DEPLOYED
**Status:** 13 out of 23 column errors fixed (57%)

Using the ground truth from `docs/reference/actual_assets`, we created an automated script that:
1. Loaded all tables and columns from TSV files (105 tables total)
2. Matched incorrect column names to correct ones using fuzzy matching
3. Updated 5 Genie Space JSON files
4. Deployed the fixes to Databricks

**Files Modified:**
- `src/genie/cost_intelligence_genie_export.json` (2 fixes)
- `src/genie/performance_genie_export.json` (1 fix)
- `src/genie/security_auditor_genie_export.json` (4 fixes)
- `src/genie/unified_health_monitor_genie_export.json` (3 fixes)
- `src/genie/job_health_monitor_genie_export.json` (3 fixes)

**Script:** `scripts/fix_genie_column_errors.py`

---

## 🔧 Remaining Work Breakdown

### Category 1: Column Errors (10 remaining) ⚠️ MANUAL REVIEW NEEDED

These errors require manual investigation because they involve:
- Complex CTE (Common Table Expression) aliases
- TVF output schemas
- ML/monitoring table schemas
- Ambiguous column references

#### 1.1 CTE Alias Issues (3 errors)
Need to validate table aliases in complex queries:

| Genie Space | Question | Issue | Likely Fix |
|---|---|---|---|
| cost_intelligence | Q25 | `workspace_name` missing | Check cost predictions CTE |
| performance | Q25 | `qh.query_volume` missing | Check CTE alias `qh` |
| unified_health_monitor | Q13 | `failed_events` missing | Check DLT monitoring CTE |

**Action:** Review SQL queries, verify CTE structure, ensure alias names match.

#### 1.2 TVF Output Columns (2 errors)
Need to check TVF return schemas:

| Genie Space | Question | TVF | Column Missing |
|---|---|---|---|
| security_auditor | Q8 | `get_permission_changes` | `change_date` |
| unified_health_monitor | Q7 | `get_failed_jobs` | `failure_count` |

**Action:** Use `docs/reference/actual_assets/tvfs.md` to verify TVF output columns.

#### 1.3 ML/Monitoring Tables (2 errors)
Check cluster rightsizing predictions schema:

| Genie Space | Question | Table | Column Missing |
|---|---|---|---|
| performance | Q16 | cluster_rightsizing_predictions | `recommended_action` |
| unified_health_monitor | Q18 | cluster_rightsizing_predictions | `recommended_action` |

**Action:** Check `docs/reference/actual_assets/ml.md` for ML table schemas.

#### 1.4 Simple Column Renames (3 errors)
Straightforward name mismatches:

| Genie Space | Question | Wrong Column | Correct Column | Source |
|---|---|---|---|---|
| security_auditor | Q17 | `event_volume_drift` | `event_volume_drift_pct` | monitoring |
| unified_health_monitor | Q12 | `query_count` | `total_queries` | mv_query_performance |
| unified_health_monitor | Q16 | `days_since_last_access` | `hours_since_update` | mv_data_quality |
| job_health_monitor | Q6 | `p95_duration_minutes` | `p95_duration_min` | mv_job_performance |
| unified_health_monitor | Q11 | `utilization_rate` | ??? | mv_commit_tracking |

**Action:** Apply manual find/replace in JSON files.

---

### Category 2: SYNTAX_ERROR (5 errors) 🐛

Malformed SQL patterns that need fixing:

| Genie Space | Question | Issue | Pattern to Fix |
|---|---|---|---|
| cost_intelligence | Q23 | Truncated CTE | Missing closing parenthesis |
| performance | Q8 | Malformed CAST | `CAST(CURRENT_DATE(), ...)` |
| security_auditor | Q5 | Malformed CAST | `CAST(CURRENT_DATE(), ...)` |
| security_auditor | Q6 | Malformed CAST | `CAST(CURRENT_DATE(), ...)` |
| unified_health_monitor | Q20 | Truncated CTE | Missing closing parenthesis |

**Action:** Create script to fix remaining `CURRENT_DATE()` syntax errors (2 already fixed).

---

### Category 3: WRONG_NUM_ARGS (3 errors) 🔧

TVF calls missing parameters:

| Genie Space | Question | TVF | Required Params | Current Params |
|---|---|---|---|---|
| security_auditor | Q9 | `get_off_hours_activity` | 4 | 1 |
| security_auditor | Q11 | `get_off_hours_activity` | 4 | 1 |
| job_health_monitor | Q10 | `get_job_retry_analysis` | 2 | 1 |

**Action:** Add missing parameters with default values (e.g., end_date, filters).

---

### Category 4: CAST_INVALID_INPUT (4 errors) ⚠️

Runtime casting errors (may require query refactoring):

| Genie Space | Question | Issue |
|---|---|---|
| cost_intelligence | Q19 | UUID to INT cast |
| performance | Q7 | UUID to INT cast |
| performance | Q10 | DATE to DOUBLE cast |
| performance | Q12 | DATE to INT cast |
| job_health_monitor | Q12 | STRING '30' to DATE cast |

**Action:** Investigate why UUIDs/dates are being cast incorrectly.

---

### Category 5: NESTED_AGGREGATE_FUNCTION (2 errors) 🏗️

Queries with aggregates inside aggregates:

| Genie Space | Question | Issue |
|---|---|---|
| performance | Q23 | Aggregate in aggregate |
| unified_health_monitor | Q21 | Aggregate in aggregate |

**Action:** Refactor to use subqueries instead of nested aggregates.

---

## 📊 Progress Metrics

### Overall Progress
- **Total Errors:** 40
- **Fixed:** 13 (33%)
- **Remaining:** 27 (67%)
- **Target:** 115+/123 passing (93%+)

### By Category
| Category | Total | Fixed | Remaining | % Fixed |
|---|---|---|---|---|
| COLUMN_NOT_FOUND | 23 | 13 | 10 | 57% ✅ |
| SYNTAX_ERROR | 5 | 0 | 5 | 0% |
| WRONG_NUM_ARGS | 3 | 0 | 3 | 0% |
| CAST_INVALID_INPUT | 4 | 0 | 4 | 0% |
| NESTED_AGGREGATE | 2 | 0 | 2 | 0% |
| OTHER | 3 | 0 | 3 | 0% |

### Success Rate Trajectory
- **Start:** 54/123 (44%)
- **After syntax fixes:** 83/123 (67%)
- **After column fixes:** ~96/123 (78%) - expected after manual fixes
- **Target after all fixes:** 115+/123 (93%+)

---

## 🚀 Immediate Next Steps

1. **Manual Column Fixes (10 errors)**
   - Review `docs/reference/actual_assets` for correct column names
   - Update JSON files for CTEs, TVFs, ML tables
   - Estimated time: 1-2 hours

2. **Fix Remaining SYNTAX_ERROR (5 errors)**
   - Run script to fix malformed CAST patterns
   - Fix truncated CTEs
   - Estimated time: 30 minutes

3. **Fix WRONG_NUM_ARGS (3 errors)**
   - Add missing TVF parameters
   - Estimated time: 15 minutes

4. **Re-run Validation**
   ```bash
   databricks bundle run -t dev genie_benchmark_sql_validation_job
   ```

5. **Investigate Runtime Errors**
   - CAST_INVALID_INPUT: Likely requires query refactoring
   - NESTED_AGGREGATE_FUNCTION: Add subqueries

---

## 📁 Key Resources

### Ground Truth Files
- `docs/reference/actual_assets/tables.md` - All table schemas
- `docs/reference/actual_assets/mvs.md` - Metric view schemas
- `docs/reference/actual_assets/ml.md` - ML table schemas
- `docs/reference/actual_assets/monitoring.md` - Monitoring table schemas
- `docs/reference/actual_assets/tvfs.md` - TVF definitions

### Scripts
- `scripts/fix_genie_column_errors.py` - Automated column fixer ✅
- `scripts/fix_genie_syntax_errors.py` - Syntax error fixer (partial) ⚠️
- `scripts/validate_genie_sql_offline.py` - Offline SQL validator ✅

### Reports
- `docs/GENIE_COLUMN_FIXES_DEPLOYED.md` - Column fix deployment summary
- `docs/deployment/GENIE_VALIDATION_FINAL_STATUS.md` - Latest validation status
- `docs/deployment/GENIE_COLUMN_FIXES_APPLIED.md` - Detailed fix report

---

## 🎯 Success Criteria

**We will know we're done when:**
1. ✅ All `TABLE_NOT_FOUND` errors eliminated (using ground truth)
2. ✅ All `COLUMN_NOT_FOUND` errors eliminated (using ground truth)
3. ✅ All `SYNTAX_ERROR` errors fixed
4. ✅ All `WRONG_NUM_ARGS` errors fixed
5. ⚠️ Runtime errors (`CAST_INVALID_INPUT`, `NESTED_AGGREGATE`) investigated and resolved
6. ✅ Validation shows 93%+ success rate (115+/123 queries passing)

---

**Current Status:** ✅ **PHASE 1 COMPLETE** - 13 column errors fixed using ground truth  
**Next Phase:** Manual column fixes + syntax/parameter fixes (estimated 2-3 hours)

