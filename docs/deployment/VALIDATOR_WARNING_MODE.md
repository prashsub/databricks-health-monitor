# Dashboard Validator: Warning-Only Mode

**Status:** ✅ ACTIVE  
**Mode:** Warning-Only with Baseline Tracking  
**Baseline Error Count:** 148 errors (as of 2026-01-08)  
**Last Updated:** 2026-01-08

---

## Overview

The dashboard validator is now running in **Warning-Only Mode** with baseline tracking. This provides protection against NEW whackamole issues while allowing gradual reduction of existing errors.

---

## How It Works

### Validation Rules

| Error Count | Status | Action | Message |
|------------|--------|--------|---------|
| **0 errors** | ✅ PERFECT | Allow deployment | "All validations passed!" |
| **1-148 errors** | ⚠️ BASELINE | Allow deployment with warning | "Within baseline - no new errors" |
| **>148 errors** | ❌ REGRESSION | **BLOCK deployment** | "NEW errors added - deployment blocked!" |

### What This Means

```
📊 Current State: 146 errors (down from 148)
   ├── ✅ IMPROVED: 2 errors fixed
   ├── ⚪ BASELINE: Still within 148 baseline
   └── 🎯 GOAL: Reduce to 0 for full blocking mode

🚨 If errors increase to 149+:
   ├── ❌ BLOCKED: New whackamole detected!
   ├── 🔍 INVESTIGATE: What change caused regression?
   └── 🛠️ FIX: Resolve NEW errors before deploying
```

---

## Current Error Breakdown (148 Total)

Based on local validation run:

| Error Type | Count | Severity | Example |
|-----------|-------|----------|---------|
| **Widget field mismatches** | ~120 | ERROR | Widget asks for `warehouse`, dataset has `warehouse_name` |
| **Missing parameters** | ~15 | ERROR | Widget uses `:time_range` but no parameter defined |
| **Databricks column typos** | ~8 | ERROR | `duration_ms` vs `total_duration_ms` |
| **Hardcoded zeros** | ~5 | WARNING | `0 AS some_column` instead of real calculation |

---

## When Validator Blocks Deployment

**The validator will ONLY block if you add NEW errors (>148 total).**

### Example: Regression Detected

```
❌ DEPLOYMENT BLOCKED: 150 errors found (baseline: 148)
================================================================================
🚨 NEW ERRORS ADDED: 2 additional errors

This indicates a REGRESSION - new whackamole issues introduced!
Please fix the NEW errors before deploying.
================================================================================

NEW ERRORS:
  performance.lvdash.json > ds_new_dataset
    Widget references columns not in dataset 'ds_new_dataset': invalid_column

  cost.lvdash.json > ds_cost_breakdown
    Uses 'warehouse_name' but fact_query_history uses 'compute_type'
```

**Action:** Fix the 2 NEW errors, then deployment will succeed.

---

## Gradual Error Reduction Strategy

### Phase 1: Fix Critical Errors (High Impact)
**Target:** Reduce to < 100 errors (32% reduction)

Focus on:
- [ ] Databricks-specific column name errors (8 errors)
- [ ] Widget field mismatches on most-used dashboards (30 errors)
- [ ] Missing critical parameters (5 errors)

**Time Estimate:** 2-3 hours

### Phase 2: Fix Common Patterns (Bulk Fixes)
**Target:** Reduce to < 50 errors (66% reduction)

Focus on:
- [ ] Standardize widget field naming across all dashboards
- [ ] Add missing parameter definitions globally
- [ ] Remove hardcoded zero columns

**Time Estimate:** 3-4 hours

### Phase 3: Zero Errors (Full Blocking Mode)
**Target:** 0 errors (100% reduction)

Focus on:
- [ ] Fix remaining edge cases
- [ ] Clean up legacy datasets
- [ ] Validate all dashboards pass

**Time Estimate:** 1-2 hours

**Total Estimate:** 6-9 hours over 2-3 weeks

---

## Automatic Mode Switching

When error count reaches **0**, the validator automatically switches to **full blocking mode**:

```python
if error_count == 0:
    # All errors fixed - full protection enabled!
    # Future: ANY new error will block deployment
    BASELINE_ERROR_COUNT = 0
```

---

## Benefits of Warning-Only Mode

| Benefit | Description |
|---------|-------------|
| **🛡️ Whackamole Protection** | Blocks NEW errors even if baseline exists |
| **📈 Gradual Improvement** | Reduce errors over time without pressure |
| **🚀 No Disruption** | Current workflow continues uninterrupted |
| **📊 Progress Tracking** | See error count decrease with each fix |
| **🎯 Clear Goal** | 0 errors = full protection enabled |

---

## Monitoring Progress

### Check Current Error Count

```bash
# Run validator locally
cd /path/to/DatabricksHealthMonitor
python3 scripts/validate_dashboards.py 2>&1 | grep "Errors found:"
```

**Output:**
```
Errors found:     146
```

**Progress:** 146/148 = 98.6% of baseline (2 errors fixed! 🎉)

### View Validation in Job Run

1. Go to job run URL (printed in deployment output)
2. Click "validate_dashboards" task
3. Scroll to bottom for validation summary

**Example Output:**
```
⚠️  WARNING-ONLY MODE: Validation found errors but allowing deployment
================================================================================
Current errors:  146
Baseline errors: 148
Status: ✅ IMPROVED - No new errors added

🎯 Goal: Reduce errors to 0 to enable full blocking mode
📊 Progress: 98.6% errors remaining
================================================================================

✅ Proceeding with deployment (baseline tracking mode)
```

---

## Common Scenarios

### Scenario 1: Fixed 2 Errors Today ✅

```
Before: 148 errors
After:  146 errors

Result: ✅ Deployment succeeds with improvement message
        📊 Progress: 98.6% (1.4% improvement)
```

### Scenario 2: No Changes

```
Before: 148 errors
After:  148 errors

Result: ⚪ Deployment succeeds at baseline
        📊 Progress: 100% (no change)
```

### Scenario 3: Added 1 New Error ❌

```
Before: 148 errors
After:  149 errors

Result: ❌ DEPLOYMENT BLOCKED
        🚨 Regression detected: 1 new error
        🛠️ Must fix before deploying
```

---

## Updating Baseline (Future)

When you fix errors and want to update baseline:

```python
# In scripts/validate_dashboards_notebook.py
BASELINE_ERROR_COUNT = 120  # Updated from 148 (28 errors fixed!)
```

**Rule:** Only reduce baseline, never increase it!

---

## Disabling Warning Mode (When Ready)

When error count reaches **0**, you can switch to full blocking:

```python
# In scripts/validate_dashboards_notebook.py
BASELINE_ERROR_COUNT = 0  # Full blocking mode - ANY error blocks deployment
```

Or simply remove the baseline logic entirely and use original validation.

---

## Related Files

- **Validator Script:** `scripts/validate_dashboards.py` (local testing)
- **Validator Notebook:** `scripts/validate_dashboards_notebook.py` (deployment)
- **Deployment Workflow:** `resources/dashboards/dashboard_deployment_job.yml`
- **Validation Output:** Check job run logs for detailed error list

---

## Summary

✅ **Warning-Only Mode is ACTIVE**  
⚠️ **148 errors exist but won't block deployment**  
🚨 **NEW errors (>148) WILL block deployment**  
🎯 **Goal: Gradually reduce to 0 for full protection**  
📊 **Current Progress: Track error count in job logs**

**This gives you the best of both worlds:**
- Continue fixing whackamole issues as they appear
- Protection against introducing NEW errors
- Clear path to zero errors and full validation

---

**Last Whackamole Fix:** 2026-01-08  
**Errors Fixed:** `last_activity_date` (rightsizing), `savings`/`clusters` → `potential_savings`/`warehouses`  
**Next Fix:** TBD (as issues appear)

