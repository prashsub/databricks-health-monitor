# Genie Space Deployment Status - Current

**Date:** January 2, 2026  
**Status:** ⚠️ **TROUBLESHOOTING IN PROGRESS**

---

## ✅ Actions Completed

### 1. Removed Duplicate Job Definition
- ✅ Deleted: `resources/semantic/genie_space_deployment_job.yml`
- ✅ Kept: `resources/semantic/genie_spaces_deployment_job.yml`

### 2. Removed ML Prediction Tables from JSON Exports
- ✅ Cost Intelligence: Removed 6 ML tables
  - `cost_anomaly_predictions`
  - `cost_forecast_predictions`
  - `tag_recommendations`
  - `user_cost_segments`
  - `migration_recommendations`
  - `budget_alert_predictions`
  
- ✅ Job Health Monitor: Removed 5 ML tables
  - `job_failure_predictions`
  - `retry_success_predictions`
  - `pipeline_health_scores`
  - `incident_impact_predictions`
  - `self_healing_recommendations`

### 3. Bundle Deployment
- ✅ Updated JSON files synced to Workspace
- ✅ Job definition updated

---

## ❌ Current Issue

**Status:** Job runs but both Genie Spaces fail to deploy

**Error Pattern:**
```
RuntimeError: Failed to deploy 2 Genie Space(s)
```

**Missing Information:** The error traceback doesn't show the specific failure reason for each Genie Space. The detailed error message (from the API) should show which tables are missing.

---

## 🔍 Diagnostic Steps

### Check Databricks Run Logs

**Run URL:** https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/1036781264978047/run/1013587872118726

**What to look for in the logs:**
1. Look for `❌ Error: <status_code>` messages
2. Look for `Response: {error details}` showing which tables don't exist
3. Check if it's the **Lakehouse Monitoring tables** or other tables

### Expected Tables in JSON Exports (After ML Removal)

#### Cost Intelligence Space - 5 Tables:
1. `fact_usage` (Gold fact table) ✅ Should exist
2. `dim_workspace` (Gold dimension) ✅ Should exist  
3. `dim_sku` (Gold dimension) ✅ Should exist
4. `fact_usage_profile_metrics` (Monitoring) ✅ User confirmed exists
5. `fact_usage_drift_metrics` (Monitoring) ✅ User confirmed exists

#### Job Health Monitor Space - 5 Tables:
1. `fact_job_run_timeline` (Gold fact table) ✅ Should exist
2. `dim_job` (Gold dimension) ✅ Should exist
3. `dim_workspace` (Gold dimension) ✅ Should exist
4. `fact_job_run_timeline_profile_metrics` (Monitoring) ✅ User confirmed exists
5. `fact_job_run_timeline_drift_metrics` (Monitoring) ✅ User confirmed exists

### Plus Metric Views and TVFs
- Both spaces reference metric views (e.g., `cost_analytics`, `job_performance`)
- Both spaces reference 15 TVFs each
- These should all exist from previous deployments

---

## 📋 Next Steps

### Option 1: Check Detailed Logs (Recommended)
1. Open the Run URL above in your browser
2. Click on the "deploy_genie_spaces" task
3. Look at the full output logs
4. Find the specific error message showing which table(s) don't exist
5. **Report back:** Which tables are missing?

### Option 2: Verify Tables Exist
Run this query in Databricks SQL:
```sql
-- Check Cost tables
SELECT tableName FROM information_schema.tables 
WHERE table_catalog = 'prashanth_subrahmanyam_catalog'
  AND table_schema = 'dev_prashanth_subrahmanyam_system_gold'
  AND tableName IN (
    'fact_usage',
    'dim_workspace',
    'dim_sku',
    'fact_usage_profile_metrics',
    'fact_usage_drift_metrics'
  )
ORDER BY tableName;

-- Check Job tables
SELECT tableName FROM information_schema.tables
WHERE table_catalog = 'prashanth_subrahmanyam_catalog'
  AND table_schema = 'dev_prashanth_subrahmanyam_system_gold'
  AND tableName IN (
    'fact_job_run_timeline',
    'dim_job',
    'fact_job_run_timeline_profile_metrics',
    'fact_job_run_timeline_drift_metrics'
  )
ORDER BY tableName;
```

### Option 3: Deploy One Space at a Time
Modify the job to deploy just Cost Intelligence first:
```python
# In deploy_genie_space.py, line ~407
json_files = [
    os.path.join(script_dir, "cost_intelligence_genie_export.json")  # Only this one
]
```

---

## 🤔 Possible Root Causes

### 1. TVFs Don't Exist
- The JSON references 15 TVFs per space (30 total)
- If these haven't been deployed yet, Genie Space creation will fail

### 2. Metric Views Don't Exist  
- `cost_analytics` and `commit_tracking` for Cost Intelligence
- `job_performance` for Job Health Monitor
- These must exist before creating Genie Spaces

### 3. Schema Name Mismatch
- JSON uses `${gold_schema}` variable
- This should expand to `dev_prashanth_subrahmanyam_system_gold`
- Verify the substitution is working correctly

### 4. Monitoring Table Names
- Monitoring tables might have different suffixes
- Check exact table names: `fact_usage_profile_metrics` vs `fact_usage__profile_metrics` (double underscore)

---

## 💡 Quick Fix: Minimal Genie Space

If we want to test the deployment mechanism, I can create a minimal JSON with ONLY:
- 1 Metric View
- 0 TVFs
- 0 ML tables
- 0 Monitoring tables

This would verify the API integration works, then we can incrementally add assets.

---

## 📊 Deployment Architecture

```
Deployment Order (Must Follow):
1. Gold Tables ✅ (exists)
2. Metric Views ⚠️ (verify exist)
3. TVFs ⚠️ (verify exist)  
4. Lakehouse Monitoring ✅ (user confirmed)
5. Genie Spaces ❌ (blocked)
```

**Current Blocker:** Somewhere between steps 2-4, a dependency is missing.

---

## 🔄 What to Do Next

**Immediate Action:** Check the Databricks run logs and tell me:
1. Which specific table(s) are causing the error
2. The exact error message from the API

**Then I can:** Fix the JSON exports or identify which prerequisite deployment is missing.


