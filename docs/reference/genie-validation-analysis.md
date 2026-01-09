# Genie Space Validation Analysis - NOT_A_SCALAR_FUNCTION Investigation

**Date:** January 7, 2026  
**Status:** 🔍 INVESTIGATING - Unexpected errors persist after fixes

---

## 📊 Current Validation Results

**Total:** 123 queries  
**Valid:** 54 (44%)  
**Invalid:** 69 (56%)

### Error Breakdown
| Error Type | Count | % |
|------------|-------|---|
| **OTHER** (NOT_A_SCALAR_FUNCTION) | 45 | 65% |
| **COLUMN_NOT_FOUND** | 12 | 17% |
| **TABLE_NOT_FOUND** | 6 | 9% |
| **FUNCTION_NOT_FOUND** | 6 | 9% |

---

## 🔧 Fixes Already Applied

### 1. Removed Template Variables ✅
- **Removed:** All `${catalog}.${gold_schema}.` prefixes from SQL queries
- **Verified:** 0 template variables remaining in answer.content
- **Example:**
  ```sql
  # BEFORE
  FROM ${catalog}.${gold_schema}.get_function(...)
  
  # AFTER
  FROM TABLE(get_function(...))
  ```

### 2. Updated Validation Script ✅
- **Added:** `.collect()` to `USE CATALOG` and `USE SCHEMA` statements
- **Purpose:** Ensure context is set before query execution
- **Code:**
  ```python
  spark.sql(f"USE CATALOG {catalog}").collect()
  spark.sql(f"USE SCHEMA {gold_schema}").collect()
  ```

### 3. Deployed to Databricks ✅
- All JSON files updated
- Validation script deployed
- Changes live in dev environment

---

## ❓ Unexpected Behavior

### Issue
Despite removing template variables and adding simple function names, we still get 45 `NOT_A_SCALAR_FUNCTION` errors.

### Sample Error (Truncated)
```
• cost_intelligence Q6: OTHER ([NOT_A_SCALAR_FUNCTION] prashanth_subrahmanyam_cat)
```

### Affected Queries
**All use correct syntax:**
- ✅ `TABLE(get_function_name(...))` wrapper
- ✅ Simple function names (no three-part names)
- ✅ No template variables

**Example Q6 queries:**
- `cost_intelligence Q6`: `TABLE(get_top_cost_contributors(...))`
- `data_quality_monitor Q6`: `TABLE(get_table_activity_status(...))`
- `job_health_monitor Q6`: `TABLE(get_job_duration_percentiles(...))`
- `security_auditor Q6`: `TABLE(get_sensitive_table_access(...))`

---

## 🔍 Possible Root Causes

### Hypothesis 1: USE CATALOG/SCHEMA Not Persisting
**Theory:** The `USE CATALOG/SCHEMA` statements might not be persisting for the subsequent query execution.

**Evidence:**
- Error mentions catalog name (`prashanth_subrahmanyam_cat`)
- Suggests Spark is trying to resolve function with full path

**Test:** Add debug logging to validation script to confirm context is set

### Hypothesis 2: Spark Session State
**Theory:** Each `spark.sql()` call might create a new session context.

**Evidence:**
- `.collect()` should force execution
- But context might not persist to next `spark.sql()` call

**Test:** Execute `USE` and query in single SQL statement

### Hypothesis 3: Error Categorization Issue
**Theory:** The error message is being truncated incorrectly.

**Evidence:**
- Error shows `prashanth_subrahmanyam_cat` (truncated)
- Actual error might be different

**Test:** Check full error message in Databricks workspace logs

### Hypothesis 4: Function Registry Issue
**Theory:** Simple function names require different resolution.

**Evidence:**
- Functions might need to be referenced differently
- Catalog/schema context might not apply to TVFs

**Test:** Try explicit catalog prefix in TABLE() wrapper

---

## 📋 Next Steps

### Immediate Actions
1. **Check Databricks Workspace Logs** ✅ PRIORITY
   - Get complete error message
   - Identify exact Spark error
   - Confirm catalog/schema context

2. **Test Single-Statement Approach**
   - Combine `USE` and query in one SQL block
   - Example:
     ```sql
     USE CATALOG catalog;
     USE SCHEMA schema;
     SELECT * FROM TABLE(get_function(...)) LIMIT 1;
     ```

3. **Add Debug Logging**
   - Print catalog/schema before query
   - Print actual SQL being executed
   - Verify context with `SELECT current_catalog(), current_schema()`

### Alternative Approaches

#### Option A: Revert to Three-Part Names (with substitution)
```python
# In validation script
sql = sql.replace('TABLE(get_', f'TABLE({catalog}.{gold_schema}.get_')
```
**Pros:** Known to work  
**Cons:** Doesn't solve parser limitation

#### Option B: Use String Substitution in JSON
```python
# When loading JSON
content = content.replace('get_', f'{catalog}.{gold_schema}.get_')
```
**Pros:** Simple fix  
**Cons:** Hardcodes environment

#### Option C: Modify TABLE() Wrapper
```sql
# Instead of
TABLE(get_function(...))

# Try
TABLE(${catalog}.${gold_schema}.get_function(...))
```
**Pros:** Explicit catalog reference  
**Cons:** Back to original issue

---

## 🎯 Success Criteria

### For Next Validation Run
- **Target:** < 25 errors (down from 69)
- **Focus:** Eliminate 45 `NOT_A_SCALAR_FUNCTION` errors
- **Remaining:** Only COLUMN_NOT_FOUND, TABLE_NOT_FOUND, FUNCTION_NOT_FOUND

### Expected Error Distribution (After Fix)
| Error Type | Current | Target |
|------------|---------|--------|
| OTHER | 45 | 0 |
| COLUMN_NOT_FOUND | 12 | 12 |
| TABLE_NOT_FOUND | 6 | 6 |
| FUNCTION_NOT_FOUND | 6 | 6 |
| **TOTAL** | **69** | **24** |

---

## 📝 Investigation Log

### Attempt 1: Remove Template Variables
- **Date:** Jan 7, 2026
- **Action:** Removed `${catalog}.${gold_schema}.` from all SQL
- **Result:** No change (still 45 OTHER errors)
- **Conclusion:** Template variables were not the root cause

### Attempt 2: Add .collect() to USE statements
- **Date:** Jan 7, 2026
- **Action:** Force execution of USE CATALOG/SCHEMA
- **Result:** No change (still 45 OTHER errors)
- **Conclusion:** Context setting alone doesn't solve issue

---

## 🔗 References

- **Run URL:** https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/881616094315044/run/706714631737383
- **Validation Script:** [src/genie/validate_genie_benchmark_sql.py](../../src/genie/validate_genie_benchmark_sql.py)
- **JSON Files:** [src/genie/](../../src/genie/)
- **Terminal Output:** [terminals/10.txt]

---

**Last Updated:** January 7, 2026  
**Next Action:** Check Databricks workspace logs for complete error messages

