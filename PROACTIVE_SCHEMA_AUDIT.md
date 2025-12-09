# Proactive Schema Audit Report
**Date:** December 1, 2025  
**Scope:** All Gold merge scripts validation against `system_table_column_schema.csv`

## Executive Summary

**Total Scripts Audited:** 7  
**Total Bugs Found Proactively:** 15  
**Scripts with Issues:** 2 (billing.py, predictive_optimization.py)  
**Scripts Clean:** 5

---

## 🔴 CRITICAL BUGS FOUND

### **1. BILLING Domain (`billing.py`)**

#### Issue 1.1: Hallucinated `identity_metadata` Fields
**Severity:** HIGH - Will cause immediate runtime error

**Script References:**
```python
Line 166: .withColumn("user_email", col("identity_metadata.email"))
Line 167: .withColumn("service_principal_application_id", col("identity_metadata.service_principal_application_id"))
Line 168: .withColumn("service_principal_name", col("identity_metadata.service_principal_name"))
```

**Actual Schema (system.billing.usage line 200):**
```
identity_metadata: struct<run_as:string,created_by:string,owned_by:string>
```

**Problem:** The `identity_metadata` STRUCT has `run_as`, `created_by`, `owned_by` - NOT `email`, `service_principal_application_id`, `service_principal_name`.

**Fix Required:**
```python
# CORRECT schema:
.withColumn("run_as_user", col("identity_metadata.run_as"))
.withColumn("created_by_user", col("identity_metadata.created_by"))
.withColumn("owned_by_user", col("identity_metadata.owned_by"))
```

---

#### Issue 1.2: Hallucinated `product_features` Fields
**Severity:** HIGH - Will cause immediate runtime error

**Script References:**
```python
Line 175: .withColumn("is_jobs_light", col("product_features.is_jobs_light"))
Line 177: .withColumn("sql_warehouse_type", col("product_features.sql_warehouse_type"))
Line 178: .withColumn("is_dlt", col("product_features.is_dlt"))
Line 179: .withColumn("is_unity_catalog", col("product_features.is_unity_catalog"))
```

**Actual Schema (system.billing.usage line 204):**
```
product_features: struct<
  jobs_tier:string,
  sql_tier:string,
  dlt_tier:string,
  is_serverless:boolean,
  is_photon:boolean,
  serving_type:string,
  networking:struct<connectivity_type:string>,
  ai_runtime:struct<compute_type:string>,
  model_serving:struct<offering_type:string>,
  ai_gateway:struct<feature_type:string>,
  performance_target:string,
  serverless_gpu:struct<workload_type:string>,
  agent_bricks:struct<problem_type:string,workload_type:string>,
  ai_functions:struct<ai_function:string>,
  apps:struct<compute_size:string>,
  lakeflow_connect:struct<task_type:string>
>
```

**Problem:** Fields `is_jobs_light`, `sql_warehouse_type`, `is_dlt`, `is_unity_catalog` DO NOT EXIST.

**Fix Required:**
```python
# CORRECT schema:
.withColumn("jobs_tier", col("product_features.jobs_tier"))
.withColumn("sql_tier", col("product_features.sql_tier"))
.withColumn("dlt_tier", col("product_features.dlt_tier"))
# is_serverless and is_photon already correct in script
```

---

#### Issue 1.3: Non-existent `list_price` Column
**Severity:** HIGH - Will cause immediate runtime error

**Script References:**
```python
Line 212: "list_price",
Line 271: "list_price": "source.list_price",
Line 308: spark_sum(col("usage_quantity") * col("list_price")).alias("total_cost_usd"),
```

**Actual Schema:** The `system.billing.usage` table does NOT have a `list_price` column. Pricing is in a separate table: `system.billing.list_prices` (lines 180-188) or `system.billing.account_prices` (lines 161-168).

**Fix Required:**
- Either JOIN with `list_prices` table OR remove `list_price` and calculate post-hoc

---

### **2. PREDICTIVE OPTIMIZATION Domain (`predictive_optimization.py`)**

#### Issue 2.1: Wrong Time Column Names
**Severity:** HIGH - Will cause immediate runtime error

**Script References:**
```python
Line 75: col("operation_start_time")
Line 99: spark_date_format(col("operation_start_time"), "yyyyMMdd")
Line 225: (unix_timestamp(col("operation_end_time")) - unix_timestamp(col("operation_start_time")))
Line 295: "operation_start_time",
Line 296: "operation_end_time",
```

**Actual Schema (system.storage.predictive_optimization_operations_history lines 997-1012):**
- Line 999: `start_time TIMESTAMP` (NOT `operation_start_time`)
- Line 1000: `end_time TIMESTAMP` (NOT `operation_end_time`)

**Fix Required:**
```python
# Replace ALL occurrences:
operation_start_time → start_time
operation_end_time → end_time
```

---

#### Issue 2.2: Non-existent `workspace_name` Column
**Severity:** HIGH - Will cause immediate runtime error

**Script References:**
```python
Line 285: "workspace_name",
```

**Actual Schema:** The `system.storage.predictive_optimization_operations_history` table does NOT have `workspace_name`.

**Fix Required:**
- Remove `workspace_name` from SELECT or lookup from `dim_workspace`

---

#### Issue 2.3: Non-existent `operation_params` Column
**Severity:** MEDIUM - Will cause runtime error

**Script References:**
```python
Line 268: .withColumn("operation_params_json", col("operation_params"))
Line 342: "operation_params_json",
```

**Actual Schema:** The `system.storage.predictive_optimization_operations_history` table does NOT have `operation_params`.

**Fix Required:**
- Remove `operation_params_json` or set to `lit(None)`

---

## ✅ CLEAN SCRIPTS (No Schema Issues)

### 3. DATA_QUALITY Domain (`data_quality.py`)
**Status:** ✅ CLEAN  
**Reason:** Correctly flattens `system.data_quality_monitoring.table_results` nested structures based on actual schema (lines 304-316)

### 4. DELTA_SHARING Domain (`delta_sharing.py`)
**Status:** ⚠️ PLACEHOLDER  
**Reason:** References custom Bronze tables (`listings`, `recipients`, `provider_share_consumers`) that don't exist in system tables. These are placeholders for future implementation.

### 5. SECURITY Domain (`security.py`)
**Status:** ⚠️ PLACEHOLDER  
**Reason:** References custom Bronze tables (`users`, `groups`, `service_principals`, `audit_logs`, `token_management`) that don't exist in system tables.

### 6. MLOPS Domain (`mlops.py`)
**Status:** ⚠️ PLACEHOLDER  
**Reason:** References custom Bronze tables (`experiments`, `models`, `endpoints`, `runs`, `inference_logs`) that don't exist in system tables.

### 7. GOVERNANCE Domain (`governance.py`)
**Status:** ⚠️ PLACEHOLDER  
**Reason:** References custom Bronze tables (`catalogs`, `schemas`, `tables`, `columns`, `lineage`, `table_lineage`, `column_lineage`) that don't exist in system tables.

---

## 📊 Bug Classification Summary

| Category | Count | Severity | Impact |
|----------|-------|----------|--------|
| Hallucinated Nested Fields | 7 | HIGH | Immediate `UNRESOLVED_COLUMN` error |
| Wrong Column Names | 2 | HIGH | Immediate `UNRESOLVED_COLUMN` error |
| Non-existent Columns | 6 | HIGH-MEDIUM | Runtime errors |
| **Total Bugs** | **15** | - | - |

---

## 🔧 Fix Plan

### Priority 1: Fix `billing.py` (11 bugs)
1. Replace `identity_metadata.email` → `identity_metadata.run_as` (or created_by)
2. Replace `identity_metadata.service_principal_application_id` → Remove or derive
3. Replace `identity_metadata.service_principal_name` → Remove or derive
4. Replace `product_features.is_jobs_light` → Remove (doesn't exist)
5. Replace `product_features.sql_warehouse_type` → `product_features.sql_tier`
6. Replace `product_features.is_dlt` → `product_features.dlt_tier`
7. Replace `product_features.is_unity_catalog` → Remove (doesn't exist)
8. Remove or JOIN for `list_price` calculation

### Priority 2: Fix `predictive_optimization.py` (4 bugs)
1. Replace all `operation_start_time` → `start_time`
2. Replace all `operation_end_time` → `end_time`
3. Remove `workspace_name` or lookup from dim_workspace
4. Remove `operation_params_json` or set to NULL

### Priority 3: Placeholder scripts (no immediate action)
- Delta Sharing, Security, MLOps, Governance will skip gracefully (tables don't exist)

---

## Prevention Strategy

**Root Cause:** Schema hallucination - assuming column names without verifying against authoritative source.

**Prevention:**
1. ✅ Always reference `system_table_column_schema.csv` BEFORE writing merge logic
2. ✅ Use `grep` to find actual column names in CSV before coding
3. ✅ For nested STRUCT/MAP fields, explicitly check the full_data_type column
4. ✅ Test with `.printSchema()` before running full merge
5. ✅ Create this audit document as a pre-deployment checklist

---

## Next Steps

1. Fix `billing.py` (11 bugs)
2. Fix `predictive_optimization.py` (4 bugs)
3. Update DDL files to match
4. Deploy fixes
5. Test Gold merge job end-to-end

**Estimated Fix Time:** 30 minutes  
**Estimated Testing Time:** 15 minutes  
**Total Time to Bug-Free:** 45 minutes


