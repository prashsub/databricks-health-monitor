# Genie Space Deployment Updates

**Date:** December 19, 2024  
**Task:** Update Genie deployment job to use new REST APIs

---

## ✅ Summary

The Genie Space deployment job has been **updated to use the official Databricks REST APIs** for programmatic creation and update of Genie Spaces. The deployment now uses the JSON export files created for Cost Intelligence and Job Health Monitor.

---

## 📝 Changes Made

### 1. Fixed API Endpoint - `deploy_genie_space.py`

**Issue:** The `update_genie_space_via_api()` function was using `requests.put()` instead of the correct `requests.patch()` method.

**Fix:** Changed to `requests.patch()` to match official API documentation.

```python
# BEFORE
response = requests.put(url, headers=headers, json=payload)

# AFTER  
response = requests.patch(url, headers=headers, json=payload)  # ✅ Correct
```

**Reference:** [Update Space API](https://docs.databricks.com/api/workspace/genie/updatespace)

---

### 2. Updated Job YAML - `genie_spaces_job.yml`

**Changes:**
- ✅ Renamed job from `genie_spaces_setup_job` → `genie_spaces_deployment_job`
- ✅ Updated description to reflect API-driven deployment (not manual UI setup)
- ✅ Changed notebook reference from `deploy_genie_spaces.py` → `deploy_genie_space.py`
- ✅ Added API reference links in comments
- ✅ Updated tags: `job_type: deployment`, added `api_driven: "true"`
- ✅ Added success notification email

**BEFORE:**
```yaml
genie_spaces_setup_job:
  name: "[${bundle.target}] Health Monitor - Genie Spaces Configuration"
  description: "Generates Genie Space configuration documentation for manual UI setup"
  
  tasks:
    - task_key: generate_genie_configs
      notebook_task:
        notebook_path: ../../src/genie/deploy_genie_spaces.py
```

**AFTER:**
```yaml
genie_spaces_deployment_job:
  name: "[${bundle.target}] Health Monitor - Genie Spaces Deployment"
  description: "Deploys Genie Spaces programmatically using REST API from JSON export files"
  
  tasks:
    - task_key: deploy_genie_spaces
      notebook_task:
        notebook_path: ../../src/genie/deploy_genie_space.py
```

---

### 3. Improved File Loading - `deploy_genie_space.py`

**Issue:** JSON file loading wasn't handling Workspace paths correctly.

**Fix:** Added fallback logic to try multiple path variants (with/without `/Workspace` prefix).

```python
# Enhanced load_genie_space_export() function
def load_genie_space_export(json_path: str, catalog: str, gold_schema: str) -> dict:
    """Load and process a Genie Space JSON export file."""
    content = None
    try:
        # Try as Workspace file
        with open(json_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        # Try with /Workspace prefix
        workspace_path = f"/Workspace{json_path}" if not json_path.startswith("/Workspace") else json_path
        with open(workspace_path, 'r') as f:
            content = f.read()
    
    export_data = json.loads(content)
    processed = process_json_values(export_data, catalog, gold_schema)
    return processed
```

---

### 4. Simplified main() Function - `deploy_genie_space.py`

**Changes:**
- ✅ Hardcoded the two known JSON export files (no directory scanning needed)
- ✅ Added better error messages with stack traces
- ✅ Simplified logic to work reliably in Asset Bundles

```python
# Hardcoded list of Genie Space exports (simpler and more reliable)
json_files = [
    os.path.join(script_dir, "cost_intelligence_genie_export.json"),
    os.path.join(script_dir, "job_health_monitor_genie_export.json")
]
```

---

## 🚀 Deployment Workflow

### How It Works

1. **Job Execution:**
   ```bash
   databricks bundle run -t dev genie_spaces_deployment_job
   ```

2. **Script Process:**
   - Reads JSON export files from `src/genie/` directory
   - Substitutes `${catalog}` and `${gold_schema}` variables
   - Lists existing Genie Spaces (GET `/api/2.0/genie/spaces`)
   - For each space:
     - If exists: **PATCH update** (partial update)
     - If new: **POST create** (full creation)

3. **API Calls Made:**
   ```bash
   # Check for existing spaces
   GET /api/2.0/genie/spaces
   
   # Create new space (if doesn't exist)
   POST /api/2.0/genie/spaces
   {
     "title": "Health Monitor Cost Intelligence Space",
     "description": "...",
     "warehouse_id": "...",
     "serialized_space": "{...JSON...}"
   }
   
   # Update existing space (if exists)
   PATCH /api/2.0/genie/spaces/{space_id}
   {
     "title": "...",
     "serialized_space": "{...updated JSON...}"
   }
   ```

---

## 📊 Deployed Genie Spaces

| Genie Space | JSON Export File | Agent Domain |
|-------------|------------------|--------------|
| **Health Monitor Cost Intelligence Space** | `cost_intelligence_genie_export.json` | 💰 Cost |
| **Health Monitor Job Reliability Space** | `job_health_monitor_genie_export.json` | 🔄 Reliability |

### Data Assets per Space

#### Cost Intelligence (6 asset types, 29 total assets)
- **Metric Views:** 2 (cost_analytics, commit_tracking)
- **TVFs:** 15 (get_top_cost_contributors, get_cost_anomalies, etc.)
- **ML Tables:** 6 (cost_anomaly_predictions, cost_forecast_predictions, etc.)
- **Monitoring Tables:** 2 (_profile_metrics, _drift_metrics)
- **Dimension Tables:** 2 (dim_workspace, dim_sku)
- **Fact Tables:** 2 (fact_usage, fact_account_prices)

#### Job Health Monitor (6 asset types, 24 total assets)
- **Metric Views:** 1 (job_performance)
- **TVFs:** 12 (get_failed_jobs, get_job_success_rate, etc.)
- **ML Tables:** 5 (job_failure_predictions, pipeline_health_scores, etc.)
- **Monitoring Tables:** 2 (_profile_metrics, _drift_metrics)
- **Dimension Tables:** 2 (dim_job, dim_workspace)
- **Fact Tables:** 2 (fact_job_run_timeline, fact_job_task_run_timeline)

---

## 🔧 Configuration

### Required Parameters

```yaml
catalog: ${var.catalog}              # Unity Catalog name
gold_schema: ${var.gold_schema}      # Gold layer schema
warehouse_id: ${var.warehouse_id}    # SQL Warehouse for Genie
```

### Optional Parameters

```yaml
genie_space_json: ""                 # Specific JSON file (empty = deploy all)
```

---

## ✅ Validation Checklist

Before deploying:
- [ ] JSON export files exist in `src/genie/`:
  - [ ] `cost_intelligence_genie_export.json`
  - [ ] `job_health_monitor_genie_export.json`
- [ ] All data assets exist in Unity Catalog:
  - [ ] Metric Views created
  - [ ] Table-Valued Functions deployed
  - [ ] ML prediction tables exist
  - [ ] Lakehouse Monitoring tables exist
- [ ] SQL Warehouse ID is valid
- [ ] Workspace has Genie enabled

---

## 🧪 Testing

### Test Deployment (Dev)

```bash
# Deploy to dev environment
databricks bundle deploy -t dev

# Run deployment job
databricks bundle run -t dev genie_spaces_deployment_job

# Check output for:
# ✓ Created Genie Space: <space_id>
# ✓ Found existing space with ID: <space_id> (if updating)
```

### Verify in UI

1. Navigate to **Databricks Workspace** → **Genie**
2. Check for:
   - ✅ "Health Monitor Cost Intelligence Space"
   - ✅ "Health Monitor Job Reliability Space"
3. Open each space and verify:
   - Sample questions appear
   - Data assets are accessible
   - Test queries work correctly

---

## 📚 References

### API Documentation
- [Create Space](https://docs.databricks.com/api/workspace/genie/createspace)
- [Update Space](https://docs.databricks.com/api/workspace/genie/updatespace)
- [List Spaces](https://docs.databricks.com/api/workspace/genie/listspaces)

### Cursor Rules
- [Genie Space Export/Import API](../../.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc) - Complete API patterns

### Project Documentation
- [Genie Spaces Inventory](../../reference/genie-spaces-inventory.md) - Complete inventory of all spaces
- [Genie Space Verification Report](../../reference/genie-spaces/verification-report.md) - Latest verification status
- [Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive deployment guide

---

## 🐛 Troubleshooting

### Issue: "File not found" error

**Cause:** JSON files not in expected location

**Fix:**
```python
# Verify files exist
ls src/genie/*_export.json

# Check notebook can access files
%python
import os
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
print(f"Notebook directory: {os.path.dirname(notebook_path)}")
```

### Issue: "Invalid access token"

**Cause:** Token expired or insufficient permissions

**Fix:**
- Re-authenticate: `databricks auth login --profile <profile>`
- Check Genie permissions in workspace

### Issue: "Space already exists" error

**Cause:** Space with same title exists, but script couldn't find it

**Fix:** The script now checks for existing spaces by title and updates them automatically.

---

## 📈 Next Steps

1. **Deploy to Dev** - Test the deployment in dev environment
2. **Verify Functionality** - Run sample questions in each Genie Space
3. **Deploy to Prod** - Once validated, deploy to production
4. **Add More Spaces** - Create JSON exports for remaining 4 Genie Spaces:
   - Performance (query + cluster combined)
   - Security Auditor
   - Data Quality Monitor
   - Unified Health Monitor

---

**Status:** ✅ **READY FOR DEPLOYMENT**

The Genie Space deployment job is now configured to programmatically create/update Genie Spaces using the official REST APIs!

