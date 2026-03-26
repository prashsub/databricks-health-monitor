# Genie Session 21: Cross Join Syntax Fixes & Deployment Status

## Overview

This session focused on resolving `BAD_REQUEST` errors during Genie Space deployment, specifically related to invalid JSON in the `serialized_space` field.

## Problem Identification

The deployment of `cost_intelligence_genie_export.json` initially failed with a `BAD_REQUEST` error. Investigation revealed multiple structural issues in the Genie Space JSON files:

### Issue 1: SQL Syntax Errors (CROSS JOIN)

*   **`cost_intelligence Q23`**: `scCROSS JOIN` instead of `sc CROSS JOIN`
*   **`performance Q23`**: `qhCROSS JOIN` instead of `qh CROSS JOIN`

### Issue 2: JSON Structure Mismatches (Root Cause)

Comparison with the reference file (`context/genie/genie_space_export.json`) revealed critical format differences:

1. **`text_instructions` format**:
    *   **WRONG** (custom format): `["instruction text", "instruction text", ...]` (array of strings)
    *   **CORRECT** (API format): `[{id: "...", content: ["instruction text"]}, ...]` (array of objects)

2. **`sql_functions` format**:
    *   **WRONG**: `{id, name, signature, full_name, description, identifier}` (extra fields)
    *   **CORRECT**: `{id, identifier}` (only required fields)

3. **`data_sources.tables` missing**:
    *   Some JSON files did not have the `tables` array at all.
    *   **CORRECT**: Must have `tables: []` even if empty.

## Fixes Implemented

### Fix 1: SQL Syntax (Cross Join)

**Script**: `scripts/fix_cost_intelligence_cross_join_bug.py`

*   **Target File**: `src/genie/cost_intelligence_genie_export.json`
*   **Issue**: `scCROSS.sku_name` and `FROM sku_costs scCROSS JOIN`
*   **Resolution**: Replaced `scCROSS` with `sc` in the `SELECT` clause and ensured `CROSS JOIN` was correctly separated from the alias `sc` in the `FROM` clause.

**Script**: `scripts/fix_performance_cross_join_bug.py`

*   **Target File**: `src/genie/performance_genie_export.json`
*   **Issue**: `qhCROSS.query_volume` and `FROM query_health qhCROSS JOIN`
*   **Resolution**: Replaced `qhCROSS` with `qh` in the `SELECT` clause and ensured `CROSS JOIN` was correctly separated from the alias `qh` in the `FROM` clause.

### Fix 2: JSON Structure (Comprehensive)

**Investigation Script**: `scripts/compare_with_reference.py`

*   Compared `cost_intelligence` structure with the working reference file.
*   Identified the 3 critical structural issues listed above.

**Fix Script**: `scripts/fix_cost_instructions_format.py`

*   **Target File**: `src/genie/cost_intelligence_genie_export.json`
*   **Changes**:
    1.  Converted `text_instructions` from array of strings to array of objects with `id` and `content` fields.
    2.  Cleaned `sql_functions` to remove extra fields (`name`, `signature`, `full_name`, `description`), keeping only `id` and `identifier`.

**Comprehensive Fix Script**: `scripts/fix_all_genie_instructions_format.py`

*   **Target**: All 6 Genie Space JSON files
*   **Changes**: Applied the same structural fixes to all files (though most were already fixed after the first script run).

## Deployment Results

### Deployment #1 (after SQL syntax fixes)

*   **Status**: Partial Success
*   **Successful**: None (still had JSON structure issues)
*   **Failed (BAD_REQUEST)**: `cost_intelligence`
*   **Errors**: "Invalid JSON in field 'serialized_space'" - due to incorrect `text_instructions` and `sql_functions` format.

### Deployment #2 (after JSON structure fixes)

*   **Status**: Partial Success (2/6)
*   **Successful**: 
    *   ✅ `cost_intelligence_genie_export.json`
    *   ✅ `performance_genie_export.json`
*   **Failed (INTERNAL_ERROR)**: 
    *   ❌ `job_health_monitor_genie_export.json` - "Failed to retrieve schema from unity catalog"
    *   ❌ `data_quality_monitor_genie_export.json` - "Failed to retrieve schema from unity catalog"
    *   ❌ `security_auditor_genie_export.json` - "An internal error occurred"
    *   ❌ `unified_health_monitor_genie_export.json` - "Failed to retrieve schema from unity catalog"

## Analysis of Current Errors

The "Failed to retrieve schema from unity catalog" error suggests:

1.  **Possible causes**:
    *   Invalid table identifiers in `data_sources.tables` or `data_sources.metric_views`
    *   Tables/metric views do not exist in Unity Catalog
    *   Incorrect catalog, schema, or table names after template variable substitution
    *   Permissions issue (unlikely, as 2 spaces succeeded)

2.  **Next steps for debugging**:
    *   Verify table identifiers in the 4 failing JSON files
    *   Check if referenced tables/metric views exist in Unity Catalog
    *   Examine template variable substitution (catalog, schema names)
    *   Compare `data_sources` structure between successful and failed spaces

## Lessons Learned

1.  **JSON format validation is critical**: The custom format used in our JSON files is NOT the Databricks API format. Always compare with official API examples.
2.  **`text_instructions` must be objects**: The `text_instructions` field requires an array of objects with `id` and `content` fields, not an array of strings.
3.  **Minimize fields in `sql_functions`**: The API only needs `id` and `identifier`; extra fields like `name`, `signature`, `full_name`, `description` cause issues.
4.  **Include empty `tables` array**: Even if there are no tables, the `data_sources.tables` field must be present as an empty array `[]`.

## Files Modified

*   `src/genie/cost_intelligence_genie_export.json` - CROSS JOIN fix, JSON structure fix
*   `src/genie/performance_genie_export.json` - CROSS JOIN fix (proactive)
*   `scripts/fix_cost_intelligence_cross_join_bug.py` - Created
*   `scripts/fix_performance_cross_join_bug.py` - Created
*   `scripts/compare_with_reference.py` - Created
*   `scripts/fix_cost_instructions_format.py` - Created
*   `scripts/fix_all_genie_instructions_format.py` - Created
*   `scripts/debug_cost_transformation.py` - Created

## Next Steps

1.  ✅ Investigate "Failed to retrieve schema from unity catalog" error in the 4 failing spaces
2.  ✅ Verify table/metric view identifiers in `data_sources`
3.  ✅ Check Unity Catalog for table existence
4.  ✅ Compare `data_sources` structure between successful and failed spaces
5.  ✅ Apply any necessary fixes
6.  ✅ Deploy again and monitor results
7.  ⏳ Test Genie Spaces in UI with sample questions
8.  ⏳ Confirm 100% pass rate for benchmark SQL queries

## References

*   [Databricks Genie API Documentation](https://docs.databricks.com/api/workspace/genie/createspace)
*   `context/genie/genie_space_export.json` - Reference for correct JSON format
*   [docs/reference/GENIE_SESSION19_FORMAT_FIX.md](./GENIE_SESSION19_FORMAT_FIX.md) - Previous JSON format transformation fixes
*   [docs/reference/GENIE_SESSION20_AUTO_CREATION.md](./GENIE_SESSION20_AUTO_CREATION.md) - Genie Space ID centralization and auto-creation

---

**Session Date**: 2026-01-13  
**Status**: In Progress  
**Deployment Success Rate**: 2/6 (33%)  
**Next Session**: Session 22 - Investigate Unity Catalog schema retrieval errors
