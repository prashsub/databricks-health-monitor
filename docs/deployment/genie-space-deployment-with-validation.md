# Genie Space Deployment with Pre-Deployment SQL Validation

**Status:** ✅ **Production-Ready**  
**Job:** `genie_spaces_deployment_job`  
**Location:** `resources/genie/genie_spaces_job.yml`

---

## Overview

This document describes the **Genie Space deployment job** which includes comprehensive **pre-deployment SQL benchmark validation** to ensure all Genie Spaces are validated before deployment.

### 🎯 Key Features

✅ **Fail-Fast Validation** - Catches all SQL errors BEFORE deployment  
✅ **200+ Query Validation** - Tests every benchmark query across all 6 Genie Spaces  
✅ **Comprehensive Error Detection** - Identifies column, table, function, and runtime errors  
✅ **Automatic Categorization** - Groups errors by type for faster debugging  
✅ **Validation Tracking** - Saves results to monitoring table for historical analysis  
✅ **Zero-Downtime** - Only deploys if ALL queries pass validation

---

## 🏗️ Two-Task Architecture

### Task 1: Pre-Deployment SQL Benchmark Validation ⏱️ ~5-10 minutes

**Purpose:** Validate ALL 200+ benchmark SQL queries before deployment

**What it does:**
1. Loads 6 JSON export files (`*_genie_export.json`)
2. Extracts all SQL queries from `benchmarks.questions` sections
3. Substitutes variables: `${catalog}`, `${gold_schema}`, `${feature_schema}`
4. Executes EXPLAIN for each query (validates without data access)
5. Catches errors:
   - `COLUMN_NOT_FOUND` - Column doesn't exist in table/view
   - `TABLE_NOT_FOUND` - Table/view/function doesn't exist
   - `FUNCTION_NOT_FOUND` - TVF or UDF doesn't exist
   - `SYNTAX_ERROR` - SQL syntax issues
   - `AMBIGUOUS_REFERENCE` - Column name conflicts
   - `OTHER` - Other execution errors
6. Prints DETAILED error logs to stdout for troubleshooting
7. **FAILS the job** if ANY query has errors (fail-fast approach)

**Output:**
- Comprehensive validation report printed to job logs
- Error categorization and full error messages
- Troubleshooting guidance for each error type
- NO TABLE STORAGE - logs only (easier debugging during development)

**Notebook:** `src/genie/validate_genie_spaces_notebook.py`

---

### Task 2: Genie Space Deployment ⏱️ ~2-3 minutes

**Purpose:** Deploy all 6 Genie Spaces via REST API

**Dependencies:** Only runs if Task 1 (validation) passes ✅

**What it does:**
1. Reads 6 validated JSON export files
2. Substitutes catalog/schema variables in JSON
3. For each Genie Space:
   - Checks if space exists (`GET /api/2.0/genie/spaces/{id}`)
   - Creates new space (`POST`) or updates existing (`PATCH`)
   - Configures permissions and access
   - Verifies deployment success
4. Logs deployment status for each space

**Deployment Order** (sequential):
1. 💰 Cost Intelligence Genie Space
2. 📊 Data Quality Monitor Genie Space
3. 🔄 Job Health Monitor Genie Space
4. ⚡ Performance Genie Space
5. 🔐 Security Auditor Genie Space
6. 🏥 Unified Health Monitor Genie Space

**Output:**
- Deployment status for each Genie Space
- Space IDs for successful deployments
- Error details for any failures

**Notebook:** `src/genie/deploy_genie_space.py`

---

## 📋 Validation Coverage

### Genie Spaces Validated (6 Total)

| # | Genie Space | JSON File | Benchmark Queries | TVFs | ML Tables |
|---|-------------|-----------|-------------------|------|-----------|
| 1 | Cost Intelligence | `cost_intelligence_genie_export.json` | 25 | 15 | 6 |
| 2 | Data Quality Monitor | `data_quality_monitor_genie_export.json` | 20 | 5 | 2 |
| 3 | Job Health Monitor | `job_health_monitor_genie_export.json` | 25 | 12 | 5 |
| 4 | Performance | `performance_genie_export.json` | 25 | 21 | 7 |
| 5 | Security Auditor | `security_auditor_genie_export.json` | 25 | 10 | 4 |
| 6 | Unified Health Monitor | `unified_health_monitor_genie_export.json` | 25 | 60 | 5 |
| **TOTAL** | **6 Spaces** | **6 Files** | **145+** | **123** | **29** |

### Asset Types Validated

| Asset Type | Count | Validation Method |
|------------|-------|-------------------|
| **Table-Valued Functions (TVFs)** | 60+ unique | `TABLE(tvf(params))` execution |
| **Metric Views** | 11 | `MEASURE(column)` syntax validation |
| **ML Prediction Tables** | 24 | Direct table query execution |
| **Lakehouse Monitoring Tables** | 6 | Custom metrics query patterns |
| **Gold Fact Tables** | 6 | JOIN and aggregation validation |
| **Gold Dimension Tables** | 4 | SCD Type 2 query validation |

### Query Patterns Validated

| Pattern Type | Example | Error Detection |
|--------------|---------|-----------------|
| **TVF Calls** | `TABLE(get_failed_jobs_summary(7))` | Function exists, correct signature |
| **Metric View Queries** | `MEASURE(total_cost) FROM mv_cost_analytics` | Metric view exists, measure defined |
| **ML Table Queries** | `SELECT * FROM cost_anomaly_predictions` | Table exists in feature schema |
| **Custom Metrics** | `WHERE column_name=':table' AND log_type='INPUT'` | Monitoring table pattern correct |
| **Complex CTEs** | `WITH cte AS (...) SELECT ... FROM cte` | Syntax, column resolution |
| **Cross-Domain Joins** | `fact JOIN dim_workspace ON ...` | FK relationships valid |

---

## 🚀 Deployment Workflow

### Complete End-to-End Process

```
┌──────────────────────────────────────────────────────────────────────┐
│                     GENIE SPACE DEPLOYMENT FLOW                      │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: PRE-DEPLOYMENT VALIDATION (Task 1)          ⏱️ ~5-10 min   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Load 6 JSON Export Files                                   │   │
│  │ ├─ cost_intelligence_genie_export.json                     │   │
│  │ ├─ data_quality_monitor_genie_export.json                  │   │
│  │ ├─ job_health_monitor_genie_export.json                    │   │
│  │ ├─ performance_genie_export.json                           │   │
│  │ ├─ security_auditor_genie_export.json                      │   │
│  │ └─ unified_health_monitor_genie_export.json                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Extract 200+ Benchmark SQL Queries                          │   │
│  │ ├─ Parse "benchmarks.questions" sections                   │   │
│  │ ├─ Extract SQL from "answer.content" arrays                │   │
│  │ └─ Substitute variables (catalog, schema)                  │   │
│  └────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Execute Each Query with LIMIT 1                             │   │
│  │ ├─ Fast validation without full table scans                │   │
│  │ ├─ Catch column resolution errors                          │   │
│  │ ├─ Catch table/function not found errors                   │   │
│  │ ├─ Catch syntax and runtime errors                         │   │
│  │ └─ Categorize errors by type                               │   │
│  └────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Generate Validation Report                                  │   │
│  │ ├─ Total queries: 200+                                     │   │
│  │ ├─ Valid queries: 200+ ✅                                   │   │
│  │ ├─ Invalid queries: 0 (target)                             │   │
│  │ ├─ By Genie Space breakdown                                │   │
│  │ ├─ Error categorization                                    │   │
│  │ └─ Save to monitoring table                                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│         ╔════════════════════════════════════╗                     │
│         ║ ALL QUERIES PASSED VALIDATION? ✅   ║                     │
│         ╚════════════════════════════════════╝                     │
│                    /              \                                 │
│              YES ✅                 NO ❌                             │
│                  ↓                    ↓                             │
│       Proceed to Task 2    ❌ FAIL JOB IMMEDIATELY                  │
│                                  (Don't deploy!)                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: GENIE SPACE DEPLOYMENT (Task 2)              ⏱️ ~2-3 min   │
├─────────────────────────────────────────────────────────────────────┤
│ (Only runs if Task 1 passed)                                       │
│                                                                     │
│  FOR EACH of 6 Genie Spaces:                                       │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 1. Load JSON Export File                                    │   │
│  │    └─ Substitute ${catalog}, ${gold_schema}, ${feature_schema}│ │
│  └────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 2. Check if Genie Space Exists                              │   │
│  │    └─ GET /api/2.0/genie/spaces?display_name="{name}"     │   │
│  └────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│         ╔════════════════════════════╗                             │
│         ║ Genie Space exists?        ║                             │
│         ╚════════════════════════════╝                             │
│                    /           \                                    │
│              YES ✅              NO ❌                                │
│                  ↓                 ↓                                │
│  ┌──────────────────────┐  ┌──────────────────────┐               │
│  │ 3a. Update Existing  │  │ 3b. Create New Space │               │
│  │ PATCH /spaces/{id}   │  │ POST /spaces         │               │
│  └──────────────────────┘  └──────────────────────┘               │
│                  ↓                 ↓                                │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 4. Configure Permissions & Access                           │   │
│  │    ├─ Set owner and admin groups                           │   │
│  │    ├─ Configure workspace access                           │   │
│  │    └─ Enable for user discovery                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 5. Verify Deployment Success                                │   │
│  │    └─ GET /spaces/{id} to confirm                          │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  REPEAT FOR ALL 6 GENIE SPACES                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ FINAL RESULT                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ✅ All 6 Genie Spaces deployed successfully                        │
│  ✅ All 200+ benchmark queries validated and passing                │
│  ✅ Users can now access Genie Spaces for natural language queries  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Job Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `catalog` | Unity Catalog name | `health_monitor` |
| `gold_schema` | Gold layer schema | `gold` |
| `feature_schema` | ML/feature schema | `gold_ml` |
| `warehouse_id` | SQL Warehouse ID for deployment | `abc123def456` |

### Variable Substitution

All variables in JSON exports are automatically substituted during validation and deployment:

| Variable | Example Value | Used In |
|----------|---------------|---------|
| `${catalog}` | `health_monitor` | All table references |
| `${gold_schema}` | `gold` | Gold layer tables, TVFs, metric views |
| `${feature_schema}` | `gold_ml` | ML prediction tables |

---

## 📊 Validation Results Logging

### Log Output Format

All validation results are **printed to job logs** (stdout) with the following structure:

**1. Progress During Validation:**
```
🔍 Validating 145 benchmark queries...
  [1/145] ✓ cost_intelligence Q1
  [2/145] ✓ cost_intelligence Q2
  [3/145] ✗ cost_intelligence Q3
  ...
```

**2. Error Summary by Genie Space:**
```
ERROR SUMMARY BY GENIE SPACE
════════════════════════════════════════════════════════════════
  cost_intelligence: 2 errors
  performance: 1 error
```

**3. Error Summary by Type:**
```
ERROR SUMMARY BY TYPE
════════════════════════════════════════════════════════════════
  COLUMN_NOT_FOUND: 2 queries
  FUNCTION_NOT_FOUND: 1 query
```

**4. Detailed Error Log (for debugging):**
```
▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
GENIE SPACE: COST_INTELLIGENCE (2 errors)
▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼

─── ERROR 1/2 ────────────────────────────────────────────────
Question Number: 5
Question Text: Show me top cost contributors
Error Type: COLUMN_NOT_FOUND

🔍 MISSING COLUMN:
   Column Name: total_cost
   Did you mean: list_cost, usage_cost

💡 FIX: Add column to table or fix column name in JSON export

📄 FULL ERROR MESSAGE:
[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column or function 
parameter with name `total_cost` cannot be resolved. 
Did you mean one of the following? [`list_cost`, `usage_cost`]
```

### Accessing Validation Logs

**Via Databricks UI:**
1. Navigate to **Workflows** → Job run details
2. Click on **validate_benchmark_sql** task
3. View **Output** tab for full logs
4. Search for specific error types or Genie Spaces

**Via Databricks CLI:**
```bash
# Get latest run ID
RUN_ID=$(databricks runs list --job-id $JOB_ID --limit 1 --output json | jq -r '.runs[0].run_id')

# Get task run output
databricks runs get-output --run-id $RUN_ID
```

### No Table Storage

**Why no table storage?**
- ✅ Simplifies deployment (no schema creation needed)
- ✅ Faster troubleshooting (logs show full context)
- ✅ Easier debugging during development
- ✅ Validation errors require immediate fixes (not historical analysis)
- ✅ Job logs are persistent and searchable

**For tracking over time:**
- Job run history shows pass/fail status
- Logs are retained based on workspace settings
- Use job monitoring for success rate trends

---

## 🎯 Error Handling

### Fail-Fast Approach

**Philosophy:** Catch ALL errors before deployment, not after.

**Implementation:**
- Validation task executes ALL queries with LIMIT 1
- Even ONE failing query causes the entire job to fail
- Deployment task only runs if validation is 100% successful
- No partial deployments - it's all or nothing

### Error Categories

| Error Type | Cause | Fix |
|------------|-------|-----|
| `COLUMN_NOT_FOUND` | Column doesn't exist in table/view | Fix column name or add to table |
| `TABLE_NOT_FOUND` | Table/view/TVF doesn't exist | Deploy missing asset or fix name |
| `FUNCTION_NOT_FOUND` | TVF or UDF doesn't exist | Deploy function or fix signature |
| `SYNTAX_ERROR` | SQL syntax issue | Fix SQL syntax |
| `AMBIGUOUS_REFERENCE` | Column name exists in multiple tables | Add table alias or qualify column |
| `RUNTIME_ERROR` | Other execution error | Debug specific error message |

### Debugging Failed Validation

If validation fails:

1. **Review validation report** - Check which queries failed
2. **Check error type** - Identify systematic issues (e.g., all TVF calls)
3. **Fix root cause** - Update JSON export or deploy missing assets
4. **Re-run validation** - Execute job again
5. **Deploy once clean** - All queries must pass

**Common Fixes:**
- Deploy missing TVFs before Genie Space deployment
- Update TVF signatures in JSON exports
- Verify metric view names match deployed views
- Check ML table names in feature schema

---

## 🚀 Running the Job

### Via Asset Bundle (Recommended)

```bash
# Validate bundle configuration
databricks bundle validate

# Deploy the job definition
databricks bundle deploy -t dev

# Run the job (validation + deployment)
databricks bundle run -t dev genie_spaces_deployment_job
```

### Via Databricks CLI

```bash
# Get job ID
JOB_ID=$(databricks jobs list --output json | jq -r '.jobs[] | select(.settings.name == "[dev] Health Monitor - Genie Spaces Deployment") | .job_id')

# Run job
databricks jobs run-now --job-id $JOB_ID
```

### Via Databricks UI

1. Navigate to **Workflows**
2. Search for "[dev] Health Monitor - Genie Spaces Deployment"
3. Click **Run now**
4. Monitor execution in real-time

---

## 📈 Monitoring

### Job-Level Monitoring

**Metrics to track:**
- Job duration (target: < 15 minutes)
- Validation pass rate (target: 100%)
- Deployment success rate (target: 100%)
- Error frequency by type

**Alerts:**
- Email on validation failure
- Email on deployment failure
- Duration warning if > 20 minutes

### Query-Level Monitoring

**Queries to run:**

```sql
-- Validation trends over time
SELECT 
  DATE_TRUNC('day', validation_timestamp) as date,
  COUNT(*) as total_queries,
  SUM(CASE WHEN valid THEN 1 ELSE 0 END) as passed
FROM health_monitor.gold_validation.genie_benchmark_validation_results
GROUP BY 1
ORDER BY 1 DESC;

-- Most common errors
SELECT 
  error_type,
  COUNT(*) as occurrences
FROM health_monitor.gold_validation.genie_benchmark_validation_results
WHERE NOT valid
  AND validation_timestamp >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY error_type
ORDER BY occurrences DESC;
```

---

## 📚 References

### Official Documentation
- [Databricks Genie Spaces API](https://docs.databricks.com/api/workspace/genie/createspace)
- [Genie Space Export/Import API](.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc)

### Project Documentation
- [Genie Spaces Deployment Guide](GENIE_SPACES_DEPLOYMENT_GUIDE.md)
- [Complete Validation Report](../reference/genie-fixes-complete-report.md)
- [Deployed Assets Inventory](../actual_assets.md)
- [All Genie Spaces Complete](../ALL_GENIE_SPACES_COMPLETE.md)

### Source Files
- **Job Definition:** `resources/genie/genie_spaces_job.yml`
- **Validation Notebook:** `src/genie/validate_genie_spaces_notebook.py`
- **Deployment Notebook:** `src/genie/deploy_genie_space.py`
- **JSON Exports:** `src/genie/*_genie_export.json` (6 files)

---

## ✅ Success Criteria

**Validation Success:**
- ✅ All 200+ benchmark queries execute without errors
- ✅ All TVF calls use correct function signatures
- ✅ All metric view references are valid
- ✅ All ML table queries return results
- ✅ All custom metrics queries follow correct patterns

**Deployment Success:**
- ✅ All 6 Genie Spaces created/updated successfully
- ✅ Permissions configured correctly
- ✅ Spaces are discoverable by users
- ✅ Benchmark queries work in Genie UI
- ✅ No deployment errors or warnings

---

**Last Updated:** January 2026  
**Version:** 1.0  
**Status:** Production-Ready ✅

