# Genie Space Validation - Final Status Report

**Date:** 2026-01-08
**Validation Run:** After SYNTAX_ERROR fixes (5/7)
**Total Queries:** 123
**Passed:** 83 (67%)
**Failed:** 40 (33%)

---

## ✅ Progress Summary

- **Fixed:** 83 queries now pass (was 54 before syntax fixes)
- **Improvement:** +29 queries fixed
- **Remaining:** 40 errors to fix

---

## 📊 Error Breakdown by Type

| Error Type | Count | % of Total |
|---|---|---|
| **COLUMN_NOT_FOUND** | 23 | 57.5% |
| **SYNTAX_ERROR** | 5 | 12.5% |
| **CAST_INVALID_INPUT** | 4 | 10% |
| **WRONG_NUM_ARGS** | 3 | 7.5% |
| **NESTED_AGGREGATE_FUNCTION** | 2 | 5% |
| **OTHER** | 3 | 7.5% |

---

## 🎯 Fixable with Ground Truth (docs/reference/actual_assets)

### 1. COLUMN_NOT_FOUND (23 errors) ✅ FIXABLE
**These should be 100% fixable by validating against actual_assets.**

**Cost Intelligence (2):**
- Q22: `sc.total_sku_cost` → Verify alias `sc` in CTE
- Q25: `workspace_name` → Check actual column name in cost predictions table

**Performance (3):**
- Q14: `p99_duration` → Should be `p99_seconds`
- Q16: `recommended_action` → Check cluster rightsizing predictions schema
- Q25: `qh.query_volume` → Verify alias `qh` in CTE

**Security Auditor (6):**
- Q7: `failed_count` → Check get_failed_actions TVF output
- Q8: `change_date` → Check get_permission_changes TVF output
- Q10: `risk_level` → Should be `audit_level`?
- Q15: `unique_data_consumers` → Check mv_security_analytics columns
- Q16: `event_count` → Should be `total_events`
- Q17: `event_volume_drift` → Should be `event_volume_drift_pct`

**Unified Health Monitor (9):**
- Q4: `success_rate` → Check mv_security_analytics columns
- Q7: `failure_count` → Check get_failed_jobs output
- Q11: `utilization_rate` → Check commit tracking table
- Q12: `query_count` → Should be `total_queries`
- Q13: `failed_events` → Check DLT monitoring table
- Q15: `risk_level` → Should be `audit_level`
- Q16: `days_since_last_access` → Should be `hours_since_update`?
- Q18: `recommended_action` → Check cluster rightsizing predictions
- Q19: `cost_7d` → Check mv_cost_analytics columns

**Job Health Monitor (3):**
- Q4: `failure_count` → Check get_failed_jobs output
- Q6: `p95_duration_minutes` → Check column name (p95_duration_min?)
- Q7: `success_rate` → Should be `success_rate_pct`
- Q8: `failure_count` → Should be `failed_runs`
- Q9: `deviation_score` → Should be `deviation_ratio`
- Q14: `f.start_time` → Check system.lakeflow.flow_events alias
- Q18: `ft.run_date` → Check fact_job_run_timeline alias

---

### 2. SYNTAX_ERROR (5 errors) ✅ FIXABLE
**Remaining malformed CURRENT_DATE() calls.**

- cost_intelligence Q23: Truncated CTE (missing closing parenthesis)
- performance Q8: Malformed CAST(CURRENT_DATE(), ...)
- security_auditor Q5: Malformed CAST(CURRENT_DATE(), ...)
- security_auditor Q6: Malformed CAST(CURRENT_DATE(), ...)
- unified_health_monitor Q20: Truncated CTE (missing closing parenthesis)

---

### 3. WRONG_NUM_ARGS (3 errors) ✅ FIXABLE
**Missing parameters for TVF calls.**

- security_auditor Q9: `get_off_hours_activity` requires 4 params (has 1)
- security_auditor Q11: `get_off_hours_activity` requires 4 params (has 1)
- job_health_monitor Q10: `get_job_retry_analysis` requires 2 params (has 1)

---

## 🔧 Runtime Issues (9 errors) ⚠️ NEEDS INVESTIGATION

### CAST_INVALID_INPUT (4 errors)
- cost_intelligence Q19: UUID to INT cast
- performance Q7: UUID to INT cast
- performance Q10: DATE to DOUBLE cast
- performance Q12: DATE to INT cast
- job_health_monitor Q12: STRING '30' to DATE cast

### NESTED_AGGREGATE_FUNCTION (2 errors)
- performance Q23: Aggregate in aggregate (needs subquery)
- unified_health_monitor Q21: Aggregate in aggregate (needs subquery)

### OTHER (3 errors)
- Already categorized above

---

## 🎯 Next Actions

1. **Create comprehensive column fix script** using `docs/reference/actual_assets`
2. **Fix remaining SYNTAX_ERROR patterns** (2 more CURRENT_DATE issues)
3. **Fix WRONG_NUM_ARGS** by adding missing TVF parameters
4. **Investigate CAST_INVALID_INPUT** errors (may need query refactoring)
5. **Fix NESTED_AGGREGATE_FUNCTION** errors (add subqueries)

---

## 📈 Success Rate Trajectory

- **Start:** 54/123 (44%)
- **After syntax fixes:** 83/123 (67%)
- **Target after column fixes:** ~105/123 (85%)
- **Final target:** 115+/123 (93%+)


