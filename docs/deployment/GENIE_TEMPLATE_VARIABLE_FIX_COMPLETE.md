# Genie Space Template Variable Fix - Complete

**Date:** January 7, 2026  
**Status:** ✅ COMPLETE - All template variables removed from SQL queries

---

## 🎯 Problem Summary

**Issue:** SQL queries in Genie Space benchmark `answer.content` sections contained template variables like `${catalog}.${gold_schema}.function_name`, which were being substituted at runtime into three-part names. Even though the validation script used `USE CATALOG/SCHEMA`, these three-part references caused issues.

**Impact:** 
- Potential `NOT_A_SCALAR_FUNCTION` errors (45 "OTHER" errors in validation)
- Template variables in 8 queries across 6 Genie Spaces

---

## 🔧 Fixes Applied

### 1. Fixed Template Variables in SQL Queries

**Pattern Applied:**
```sql
# BEFORE
${catalog}.${gold_schema}.get_function_name(...)
${catalog}.${feature_schema}.table_name

# AFTER
get_function_name(...)
table_name
```

**Rationale:** With `USE CATALOG/SCHEMA` executed before queries, simple names work correctly and avoid parser limitations with three-part names in TABLE() wrappers.

### 2. Files Modified

| File | Issues Fixed | Description |
|------|--------------|-------------|
| `cost_intelligence_genie_export.json` | 2 queries | ML prediction tables, metric view CTEs |
| `performance_genie_export.json` | 1 query | ML cluster capacity predictions |
| `unified_health_monitor_genie_export.json` | 3 queries | ML tables, complex CTEs |
| `job_health_monitor_genie_export.json` | 2 queries | Monitoring tables with `_monitoring` suffix |
| `data_quality_monitor_genie_export.json` | 0 queries | Already correct |
| `security_auditor_genie_export.json` | 0 queries | Already correct |

**Total:** 8 queries fixed across 6 files

### 3. Specific Fixes

#### Cost Intelligence (Q24, Q25)
- **Before:** `${catalog}.${feature_schema}.cost_anomaly_predictions`
- **After:** `cost_anomaly_predictions`
- **Context:** ML prediction table references

#### Performance (Q16)
- **Before:** `${catalog}.${feature_schema}.cluster_capacity_predictions`
- **After:** `cluster_capacity_predictions`
- **Context:** Cluster rightsizing recommendations

#### Unified Health Monitor (Q18, Q20, Q21)
- **Before:** `${catalog}.${feature_schema}.cluster_capacity_predictions`
- **After:** `cluster_capacity_predictions`
- **Context:** ML tables and complex CTEs with metric views

#### Job Health Monitor (Q16, Q17)
- **Before:** `${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_drift_metrics`
- **After:** `fact_job_run_timeline_drift_metrics`
- **Context:** Lakehouse Monitoring output tables

---

## 📊 Verification

### Before Fix
```bash
$ grep -o '\${catalog}' src/genie/*_genie_export.json | wc -l
8  # Template variables in SQL queries
```

### After Fix
```bash
$ grep -o '\${catalog}' src/genie/*_genie_export.json | wc -l
0  # All template variables removed from SQL
```

✅ **Zero template variables remaining in benchmark SQL queries**

---

## 🚀 Deployment

**Commands Executed:**
```bash
# Deploy updated JSON files and validation script
DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle deploy -t dev

# Re-run validation with fixed queries
DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev genie_benchmark_sql_validation_job
```

**Status:** ✅ Deployed successfully  
**Validation:** 🔄 Running (in progress)

---

## 📈 Expected Impact

### Error Reduction
- **Before:** 66 errors (45 "OTHER" type, likely NOT_A_SCALAR_FUNCTION)
- **Expected After:** ~21-25 errors (only COLUMN_NOT_FOUND, FUNCTION_NOT_FOUND, TABLE_NOT_FOUND remain)
- **Improvement:** ~60% error reduction

### Categories Expected to Remain
1. **COLUMN_NOT_FOUND (14 errors)** - Column name mismatches
2. **FUNCTION_NOT_FOUND (6 errors)** - TVF signature issues
3. **TABLE_NOT_FOUND (1 error)** - Missing table

---

## 🔑 Key Learnings

### 1. USE CATALOG/SCHEMA Pattern
- ✅ **Works:** Simple TVF names after `USE CATALOG catalog; USE SCHEMA schema;`
- ✅ **Requires:** `.collect()` to ensure execution before main query
- ❌ **Doesn't work:** Three-part names in TABLE() due to Spark SQL parser limitations

### 2. Template Variable Strategy
- ✅ **For deployment:** Use `${catalog}.${gold_schema}` in identifiers (data sources, sql_functions)
- ❌ **For queries:** Use simple names in benchmark SQL (validation script substitutes context)

### 3. Validation Approach
- ✅ **Execute with LIMIT 1:** Catches runtime errors (NOT_A_SCALAR_FUNCTION, type mismatches)
- ✅ **Set catalog/schema context:** Enables simple names
- ❌ **EXPLAIN only:** Misses runtime errors

---

## 📝 Next Steps

1. **Monitor validation run** - Check for remaining errors
2. **Fix COLUMN_NOT_FOUND errors** - Update column names (~14 queries)
3. **Investigate FUNCTION_NOT_FOUND** - Verify TVF deployment (~6 queries)
4. **Deploy Genie Spaces** - Once validation passes

---

## 🔗 References

- [Validation Script](../../src/genie/validate_genie_benchmark_sql.py) - `USE CATALOG/SCHEMA` with `.collect()`
- [Genie JSON Files](../../src/genie/) - 6 export files with fixed queries
- [Previous Fix](GENIE_NOT_A_SCALAR_FUNCTION_FIX_SUMMARY.md) - sql_functions.identifier updates

---

**Last Updated:** January 7, 2026  
**Next Validation:** In progress (terminal 10.txt)

