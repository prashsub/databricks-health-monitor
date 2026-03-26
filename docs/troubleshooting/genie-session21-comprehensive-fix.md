# Genie Session 21: Comprehensive Fix & Deployment Status

## Executive Summary

**Deployment Status**: 2/6 (33% success rate)
- ✅ **SUCCESS**: `cost_intelligence`, `performance`
- ❌ **FAILED**: `job_health_monitor`, `data_quality_monitor`, `security_auditor`, `unified_health_monitor`

**Root Causes Identified**:
1. ✅ **FIXED**: SQL CROSS JOIN syntax errors (`scCROSS`, `qhCROSS`)
2. ✅ **FIXED**: JSON format mismatches (`text_instructions`, `sql_functions`, `config.name/description`, `data_sources.tables`)
3. ⏳ **UNRESOLVED**: Unity Catalog internal errors (API/permissions issue)

---

## Problems & Solutions

### Issue 1: SQL CROSS JOIN Syntax Errors

**Files Affected**: `cost_intelligence` Q23, `performance` Q23

**Problem**:
- `scCROSS.sku_name` and `FROM sku_costs scCROSS JOIN` (wrong)
- `qhCROSS.query_volume` and `FROM query_health qhCROSS JOIN` (wrong)

**Solution**:
```python
# scripts/fix_cost_intelligence_cross_join_bug.py
# scripts/fix_performance_cross_join_bug.py

# Fixed to: sc.sku_name and FROM sku_costs sc CROSS JOIN
# Fixed to: qh.query_volume and FROM query_health qh CROSS JOIN
```

**Result**: ✅ Fixed

---

### Issue 2: JSON Structure Mismatch (Root Cause of BAD_REQUEST)

#### 2a. `text_instructions` Format

**Problem**:
```json
{
  "text_instructions": ["instruction 1", "instruction 2", ...]  // ❌ WRONG
}
```

**Solution**:
```json
{
  "text_instructions": [
    {
      "id": "abc123...",
      "content": ["combined instructions"]
    }
  ]  // ✅ CORRECT
}
```

**Script**: `scripts/fix_cost_instructions_format.py` (later `scripts/fix_all_genie_instructions_format.py`)

---

#### 2b. `sql_functions` Format

**Problem**:
```json
{
  "sql_functions": [
    {
      "id": "...",
      "name": "...",           // ❌ Extra fields
      "signature": "...",      // ❌ Extra fields
      "full_name": "...",      // ❌ Extra fields
      "description": [...],    // ❌ Extra fields
      "identifier": "..."
    }
  ]
}
```

**Solution**:
```json
{
  "sql_functions": [
    {
      "id": "...",
      "identifier": "..."      // ✅ Only required fields
    }
  ]
}
```

**Script**: `scripts/fix_cost_instructions_format.py`

---

#### 2c. `config.name` and `config.description`

**Problem**:
```json
{
  "config": {
    "name": "Cost Intelligence",           // ❌ Not allowed in serialized_space
    "description": "Cost analytics...",    // ❌ Not allowed in serialized_space
    "sample_questions": [...]
  }
}
```

**Solution**: Remove `config.name` and `config.description` (they belong at the top level of the API payload, not in `serialized_space`)

**Script**: `scripts/fix_config_name_description.py`

---

#### 2d. Missing `data_sources.tables`

**Problem**: `cost_intelligence` did not have a `data_sources.tables` field at all

**Solution**: Add empty `tables` array
```json
{
  "data_sources": {
    "metric_views": [...],
    "tables": []  // ✅ Must be present even if empty
  }
}
```

**Script**: `scripts/fix_cost_missing_tables.py`

---

#### 2e. Sample Questions Format

**Problem** (`security_auditor`):
```json
{
  "sample_questions": [
    {
      "id": "...",
      "question": "Who accessed this table?"  // ❌ String instead of array
    }
  ]
}
```

**Solution**:
```json
{
  "sample_questions": [
    {
      "id": "...",
      "question": ["Who accessed this table?"]  // ✅ Array
    }
  ]
}
```

**Script**: `scripts/fix_security_auditor_sample_questions.py`

---

### Issue 3: Unity Catalog Internal Errors (UNRESOLVED)

**Error Type**: `INTERNAL_ERROR: Failed to retrieve schema from unity catalog`

**Affected Spaces**:
- ❌ `job_health_monitor`
- ❌ `data_quality_monitor`
- ❌ `unified_health_monitor`
- ❌ `security_auditor` (different error: "An internal error occurred")

#### Investigation Results:

**✅ Verified**: Template variable substitution works correctly for all files
- `${catalog}` → `prashanth_subrahmanyam_catalog`
- `${gold_schema}` → `dev_prashanth_subrahmanyam_system_gold`
- `${feature_schema}` → `dev_prashanth_subrahmanyam_system_gold_ml`

**✅ Verified**: All metric views exist in Unity Catalog
- `mv_job_performance` ✅
- `mv_ml_intelligence` ✅
- `mv_security_events` ✅
- `mv_cost_analytics` ✅

**✅ Verified**: All column names in `column_configs` match Unity Catalog schema

#### Observed Pattern:

| Space | Has column_configs | Deployment Action | Result |
|---|---|---|---|
| `cost_intelligence` | ❌ No | CREATE/UPDATE | ✅ SUCCESS |
| `performance` | ❌ No | CREATE/UPDATE | ✅ SUCCESS |
| `job_health_monitor` | ✅ Yes | UPDATE | ❌ FAILED |
| `data_quality_monitor` | ✅ Yes | UPDATE | ❌ FAILED |
| `security_auditor` | ❌ No | CREATE | ❌ FAILED |
| `unified_health_monitor` | ✅ Yes | UPDATE | ❌ FAILED |

**Hypothesis**: `column_configs` is NOT the root cause (since `security_auditor` fails without it).

**Alternative Hypotheses**:
1. **Databricks API transient error**: The INTERNAL_ERROR suggests a Databricks backend issue
2. **Permissions issue**: Genie Space may not have permission to access metric views/tables
3. **Schema validation timeout**: Large spaces with many tables/column_configs may timeout during validation
4. **Existing space corruption**: UPDATE operations may be failing because existing spaces have bad state

---

## Deployment Timeline

### Deployment #1 (SQL syntax only)
- **Status**: Complete failure
- **Reason**: JSON structure issues still present

### Deployment #2 (After text_instructions + sql_functions fixes)
- **Status**: Partial success (2/6 = 33%)
- **✅ SUCCESS**: `cost_intelligence`, `performance`
- **❌ FAILED**: 4 spaces with Unity Catalog errors

---

## Scripts Created

| Script | Purpose | Status |
|---|---|---|
| `scripts/fix_cost_intelligence_cross_join_bug.py` | Fix SQL CROSS JOIN in cost_intelligence | ✅ Applied |
| `scripts/fix_performance_cross_join_bug.py` | Fix SQL CROSS JOIN in performance | ✅ Applied |
| `scripts/fix_cost_instructions_format.py` | Fix JSON format for cost_intelligence | ✅ Applied |
| `scripts/fix_all_genie_instructions_format.py` | Fix JSON format for all 6 spaces | ✅ Applied |
| `scripts/fix_config_name_description.py` | Remove config.name/description | ✅ Applied |
| `scripts/fix_cost_missing_tables.py` | Add empty tables array | ✅ Applied |
| `scripts/fix_security_auditor_sample_questions.py` | Fix sample question format | ✅ Applied |
| `scripts/compare_with_reference.py` | Compare with working reference | ✅ Used |
| `scripts/debug_cost_transformation.py` | Debug transformation flow | ✅ Used |
| `scripts/investigate_transformation.py` | Simulate deployment transformation | ✅ Used |

---

## Next Steps (Recommended Priority)

### Option 1: Retry Deployment (Low Effort)
**Hypothesis**: Transient Databricks API error

**Actions**:
1. Re-deploy immediately (no changes needed)
2. Monitor for different error patterns

**Rationale**: INTERNAL_ERROR suggests transient backend issue. May resolve on retry.

---

### Option 2: Remove `column_configs` (Medium Effort)
**Hypothesis**: column_configs triggers schema validation that fails

**Actions**:
1. Remove `column_configs` from all metric_views and tables in the 4 failed spaces
2. Re-deploy

**Pros**: Matches the format of successful spaces
**Cons**: Loses column-level metadata (descriptions, value dictionaries)

---

### Option 3: Delete & Recreate Existing Spaces (High Effort)
**Hypothesis**: Existing spaces have corrupted state causing UPDATE to fail

**Actions**:
1. Manually delete existing Genie Spaces in UI
2. Clear all space IDs in `databricks.yml` (already blank)
3. Re-deploy (will force CREATE for all)

**Pros**: Forces fresh creation
**Cons**: Loses existing space history, requires manual cleanup

---

### Option 4: Contact Databricks Support (Parallel Action)
**Hypothesis**: This is a Databricks backend bug

**Actions**:
1. File support ticket with request IDs:
   - `job_health_monitor`: `726a0ff2-6d94-490a-adb2-794cc6e71186`
   - `data_quality_monitor`: `a022a2dc-568f-4e9c-8ee7-81b2c3725024`
   - `security_auditor`: `ba62cc13-afdc-4529-addb-75869473a653`
   - `unified_health_monitor`: `8986579d-ba50-471e-bfb3-8b5fdd969507`

2. Include:
   - Error: "INTERNAL_ERROR: Failed to retrieve schema from unity catalog"
   - Context: Genie Space deployment via API
   - Working examples: `cost_intelligence`, `performance`

---

## Key Learnings

1. **JSON Format Validation is Critical**: Databricks Genie Space API has strict format requirements that differ from custom export formats

2. **`text_instructions` Must Be Objects**: The API requires `{id, content: [text]}`, not just string arrays

3. **Minimize Fields in `sql_functions`**: Only `id` and `identifier` are needed; extra fields cause issues

4. **Always Include `data_sources.tables`**: Even if empty, the API requires this field

5. **INTERNAL_ERROR ≠ JSON Format Error**: Internal errors suggest backend issues, not client payload problems

6. **Variable Substitution Works Correctly**: Template variables are properly substituted during deployment

7. **Successful Spaces Don't Have `column_configs`**: The 2 successful spaces omit this field

---

## Files Modified

### SQL Fixes:
- `src/genie/cost_intelligence_genie_export.json` - Q23 CROSS JOIN fix
- `src/genie/performance_genie_export.json` - Q23 CROSS JOIN fix (proactive)

### JSON Format Fixes:
- `src/genie/cost_intelligence_genie_export.json` - text_instructions, sql_functions, tables
- All 6 `*_genie_export.json` files - text_instructions, sql_functions format

### Documentation:
- `docs/reference/GENIE_SESSION21_CROSS_JOIN_FIX.md` - Cross join fixes
- `docs/reference/GENIE_SESSION21_COMPREHENSIVE_FIX.md` - This document

---

## References

- [Databricks Genie API Documentation](https://docs.databricks.com/api/workspace/genie/createspace)
- `context/genie/genie_space_export.json` - Reference for correct JSON format
- [docs/reference/GENIE_SESSION19_FORMAT_FIX.md](./GENIE_SESSION19_FORMAT_FIX.md) - Previous JSON format fixes
- [docs/reference/GENIE_SESSION20_AUTO_CREATION.md](./GENIE_SESSION20_AUTO_CREATION.md) - Auto-creation feature

---

**Session Date**: 2026-01-13  
**Status**: In Progress  
**Deployment Success Rate**: 2/6 (33%)  
**Next Session**: Session 22 - Retry deployment or remove column_configs
