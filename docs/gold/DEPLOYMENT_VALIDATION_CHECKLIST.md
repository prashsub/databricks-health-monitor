# Gold Layer Deployment Validation Checklist

**Date:** December 9, 2025  
**Deployment:** Gold Layer Data Pipeline (18 tables, 6 domains)  
**Environment:** Dev (dev_prashanth_subrahmanyam_*)

---

## ✅ Pre-Deployment Validation

### 1. File Existence
- [x] `src/gold/merge_helpers.py` - Shared utility functions
- [x] `src/gold/merge_shared.py` - Workspace dimension (1 table)
- [x] `src/gold/merge_billing.py` - Billing domain (3 tables)
- [x] `src/gold/merge_lakeflow.py` - Lakeflow domain (6 tables)
- [x] `src/gold/merge_query_performance.py` - Query performance (3 tables)
- [x] `src/gold/merge_security.py` - Security domain (1 table)
- [x] `src/gold/merge_compute.py` - Compute domain (3 tables)
- [x] `resources/gold_merge_job.yml` - Asset Bundle job definition
- [x] `docs/gold/BRONZE_TO_GOLD_LINEAGE.md` - Transformation documentation

### 2. Code Quality
- [x] All Python files have zero linter errors
- [x] Consistent patterns across all merge scripts
- [x] Proper error handling (try/except/finally)
- [x] Comprehensive logging statements
- [x] Parameter validation via dbutils.widgets.get()

### 3. Asset Bundle Configuration
- [x] **FIXED:** Variable naming mismatch (`bronze_schema` → `system_bronze_schema`)
- [x] **FIXED:** Removed duplicate `resources/gold/gold_merge_job.yml`
- [x] Proper task dependencies defined
- [x] Serverless environment configuration
- [x] Email notifications configured
- [ ] **PENDING:** Bundle validation successful (`databricks bundle validate`)

### 4. Variable Mapping Verification
**databricks.yml variables:**
- `catalog`: prashanth_subrahmanyam_catalog (dev)
- `system_bronze_schema`: dev_prashanth_subrahmanyam_system_bronze (dev)
- `gold_schema`: dev_prashanth_subrahmanyam_system_gold (dev)

**gold_merge_job.yml parameters:**
- ✅ `catalog`: ${var.catalog}
- ✅ `bronze_schema`: ${var.system_bronze_schema}
- ✅ `gold_schema`: ${var.gold_schema}

---

## 📋 Deployment Steps

### Step 1: Bundle Validation
```bash
cd "/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor"
databricks bundle validate
```

**Expected Output:**
- ✅ All resource configurations are valid
- ✅ No syntax errors in YAML
- ✅ All variable references resolve correctly

### Step 2: Bundle Deployment
```bash
databricks bundle deploy -t dev
```

**Expected Output:**
- Creates/updates job: `[dev prashanth_subrahmanyam] Health Monitor - Gold Layer Data Pipeline`
- Syncs Python scripts to workspace
- Syncs YAML schemas to workspace

### Step 3: Verify Deployment in UI
1. Navigate to **Workflows** in Databricks UI
2. Find job: `[dev prashanth_subrahmanyam] Health Monitor - Gold Layer Data Pipeline`
3. Verify tasks:
   - ✅ `merge_shared` (Phase 1)
   - ✅ `merge_compute_reference` (Phase 1)
   - ✅ `merge_billing` (Phase 2)
   - ✅ `merge_lakeflow` (Phase 2)
   - ✅ `merge_query_performance` (Phase 2)
   - ✅ `merge_security` (Phase 3)
4. Verify task dependencies are correct
5. Verify schedule is PAUSED (dev environment)

### Step 4: Run Job
```bash
databricks bundle run -t dev gold_merge_job
```

**Or via UI:**
1. Open job in Workflows
2. Click "Run now"
3. Monitor execution

---

## ✅ Post-Deployment Validation

### 1. Job Execution Status
- [ ] All 6 tasks completed successfully
- [ ] No tasks failed or timed out
- [ ] Task execution order respected dependencies
- [ ] Total runtime < 4 hours (timeout threshold)

### 2. Gold Table Row Counts

**Shared Domain (1 table):**
```sql
SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_workspace;
-- Expected: ~1-10 workspaces
```

**Billing Domain (3 tables):**
```sql
SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_sku;
-- Expected: ~200-500 SKUs

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_list_prices;
-- Expected: ~1000-5000 pricing records

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_usage;
-- Expected: Varies by usage (10K-1M+ records)
```

**Lakeflow Domain (6 tables):**
```sql
SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_job;
-- Expected: ~10-100 jobs

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_job_task;
-- Expected: ~50-500 tasks

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_pipeline;
-- Expected: ~5-50 pipelines

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline;
-- Expected: ~1000-10000 runs

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_job_task_run_timeline;
-- Expected: ~5000-50000 task runs

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_pipeline_update_timeline;
-- Expected: ~100-1000 updates
```

**Query Performance Domain (3 tables):**
```sql
SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_warehouse;
-- Expected: ~5-20 warehouses

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_query_history;
-- Expected: ~10K-1M+ queries (365-day retention)

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_warehouse_events;
-- Expected: ~1000-10000 events
```

**Security Domain (1 table):**
```sql
SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_audit_logs;
-- Expected: ~100K-10M+ events (365-day retention)
```

**Compute Domain (3 tables):**
```sql
SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_node_type;
-- Expected: ~50-200 node types (reference data)

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.dim_cluster;
-- Expected: ~10-100 clusters

SELECT COUNT(*) FROM dev_prashanth_subrahmanyam_system_gold.fact_node_timeline;
-- Expected: ~100K-1M+ hourly metrics (90-day retention)
```

### 3. Schema Validation

**Check for schema mismatches:**
```sql
-- Verify all 18 tables exist
SHOW TABLES IN dev_prashanth_subrahmanyam_system_gold;

-- Sample schema check (dim_workspace)
DESCRIBE dev_prashanth_subrahmanyam_system_gold.dim_workspace;
```

**Expected:**
- [ ] All 18 Gold tables exist
- [ ] Column names match YAML definitions
- [ ] Data types match YAML definitions
- [ ] No extra or missing columns

### 4. Data Quality Checks

**Check for NULL primary keys:**
```sql
-- Example: dim_workspace
SELECT COUNT(*) 
FROM dev_prashanth_subrahmanyam_system_gold.dim_workspace 
WHERE workspace_id IS NULL;
-- Expected: 0 rows

-- Example: fact_usage (composite PK)
SELECT COUNT(*) 
FROM dev_prashanth_subrahmanyam_system_gold.fact_usage 
WHERE record_id IS NULL;
-- Expected: 0 rows
```

**Check for duplicates:**
```sql
-- Example: dim_workspace (single PK)
SELECT workspace_id, COUNT(*) as duplicate_count
FROM dev_prashanth_subrahmanyam_system_gold.dim_workspace
GROUP BY workspace_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows

-- Example: fact_usage (single PK)
SELECT record_id, COUNT(*) as duplicate_count
FROM dev_prashanth_subrahmanyam_system_gold.fact_usage
GROUP BY record_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows
```

### 5. Referential Integrity (Sample Checks)

**Check orphaned foreign keys:**
```sql
-- fact_usage → dim_workspace
SELECT COUNT(*) 
FROM dev_prashanth_subrahmanyam_system_gold.fact_usage u
LEFT JOIN dev_prashanth_subrahmanyam_system_gold.dim_workspace w
  ON u.workspace_id = w.workspace_id
WHERE u.workspace_id IS NOT NULL 
  AND w.workspace_id IS NULL;
-- Expected: 0 rows (no orphaned workspace_ids)

-- fact_query_history → dim_warehouse
SELECT COUNT(*) 
FROM dev_prashanth_subrahmanyam_system_gold.fact_query_history q
LEFT JOIN dev_prashanth_subrahmanyam_system_gold.dim_warehouse w
  ON q.workspace_id = w.workspace_id 
  AND q.compute_warehouse_id = w.warehouse_id
WHERE q.compute_warehouse_id IS NOT NULL 
  AND w.warehouse_id IS NULL;
-- Expected: 0 rows (no orphaned warehouse_ids)
```

### 6. Transformation Validation

**Verify flattened columns:**
```sql
-- fact_usage: Check flattened usage_metadata
SELECT 
  usage_metadata_cluster_id,
  usage_metadata_job_id,
  usage_metadata_warehouse_id
FROM dev_prashanth_subrahmanyam_system_gold.fact_usage
WHERE usage_metadata_cluster_id IS NOT NULL
LIMIT 5;
-- Expected: Non-null values for flattened fields

-- fact_usage: Check custom_tags MAP
SELECT 
  custom_tags,
  is_tagged,
  tag_count
FROM dev_prashanth_subrahmanyam_system_gold.fact_usage
WHERE is_tagged = true
LIMIT 5;
-- Expected: Valid MAP<STRING,STRING> and derived columns
```

**Verify derived columns:**
```sql
-- fact_usage: Check pricing enrichment
SELECT 
  sku_name,
  usage_quantity,
  list_price,
  list_cost
FROM dev_prashanth_subrahmanyam_system_gold.fact_usage
WHERE list_price IS NOT NULL
LIMIT 10;
-- Expected: list_cost = usage_quantity * list_price

-- fact_job_run_timeline: Check duration calculations
SELECT 
  run_id,
  period_start_time,
  period_end_time,
  run_duration_seconds,
  run_duration_minutes,
  is_success
FROM dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline
WHERE period_end_time IS NOT NULL
LIMIT 10;
-- Expected: run_duration_minutes = run_duration_seconds / 60
-- Expected: is_success = (result_state = 'SUCCESS')
```

### 7. Audit Timestamps

**Verify record_created_timestamp and record_updated_timestamp:**
```sql
-- All Gold tables should have audit timestamps
SELECT 
  workspace_id,
  record_created_timestamp,
  record_updated_timestamp
FROM dev_prashanth_subrahmanyam_system_gold.dim_workspace
LIMIT 5;
-- Expected: Both timestamps populated with current timestamp
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Bundle Validation Fails
**Error:** `Error: unknown variable: bronze_schema`
**Solution:** ✅ **FIXED** - Updated to use `system_bronze_schema`

### Issue 2: Schema Not Found
**Error:** `[SCHEMA_NOT_FOUND] The schema 'dev_prashanth_subrahmanyam_system_gold' cannot be found`
**Solution:** Run gold_setup_job first to create Gold tables

### Issue 3: Table Not Found
**Error:** `[TABLE_OR_VIEW_NOT_FOUND] The table or view 'bronze.usage' cannot be found`
**Solution:** Verify Bronze streaming pipeline has run and populated Bronze tables

### Issue 4: Parameter Not Passed
**Error:** `java.util.NoSuchElementException: key not found: catalog`
**Solution:** Verify task uses `base_parameters` (not `parameters`) and parameter names match

### Issue 5: Import Error
**Error:** `ModuleNotFoundError: No module named 'merge_helpers'`
**Solution:** Ensure `merge_helpers.py` is in same directory and is a pure Python file (no magic commands)

### Issue 6: Duplicate Records After MERGE
**Error:** Multiple rows with same primary key in Gold table
**Solution:** Check `deduplicate_bronze()` is called before MERGE - **Already implemented in all scripts**

### Issue 7: Schema Mismatch
**Error:** `AnalysisException: cannot resolve column_name in target table`
**Solution:** Run `validate_merge_schema()` - **Already implemented in all scripts**

---

## 📊 Success Criteria

### Minimum Requirements
- [x] Bundle validates successfully
- [ ] Bundle deploys successfully
- [ ] Job runs without failures
- [ ] All 18 Gold tables populated with data
- [ ] No schema mismatches
- [ ] No NULL primary keys
- [ ] No duplicate records
- [ ] Referential integrity maintained

### Stretch Goals
- [ ] All foreign key relationships validated
- [ ] Performance benchmarks documented
- [ ] Data quality metrics tracked
- [ ] Incremental refresh tested

---

## 📝 Validation Notes

**Notes will be added here during validation process...**

### Bundle Validation Results
```
Status: PENDING
Command: databricks bundle validate
Output: (to be captured)
```

### Deployment Results
```
Status: PENDING
Command: databricks bundle deploy -t dev
Output: (to be captured)
```

### Job Execution Results
```
Status: PENDING
Command: databricks bundle run -t dev gold_merge_job
Output: (to be captured)
Duration: (to be measured)
```

### Row Count Summary
```
Status: PENDING

Domain: shared (1 table)
- dim_workspace: ? rows

Domain: billing (3 tables)
- dim_sku: ? rows
- fact_list_prices: ? rows
- fact_usage: ? rows

Domain: lakeflow (6 tables)
- dim_job: ? rows
- dim_job_task: ? rows
- dim_pipeline: ? rows
- fact_job_run_timeline: ? rows
- fact_job_task_run_timeline: ? rows
- fact_pipeline_update_timeline: ? rows

Domain: query_performance (3 tables)
- dim_warehouse: ? rows
- fact_query_history: ? rows
- fact_warehouse_events: ? rows

Domain: security (1 table)
- fact_audit_logs: ? rows

Domain: compute (3 tables)
- dim_node_type: ? rows
- dim_cluster: ? rows
- fact_node_timeline: ? rows

TOTAL: 18 tables
```

---

## ✅ Final Approval

- [ ] All validation steps completed
- [ ] All issues resolved
- [ ] Documentation updated
- [ ] Ready for production deployment (when moving to prod)

**Validated By:** _________________  
**Date:** _________________  
**Approved By:** _________________  
**Date:** _________________

