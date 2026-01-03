# Genie Space Deployment Status

**Date:** January 1, 2026  
**Status:** ⚠️ **DEPLOYMENT IN PROGRESS - TROUBLESHOOTING NEEDED**

---

## ✅ Completed Steps

### 1. Bundle Configuration Fixed
- ✅ Added `src/**/*.json` to sync includes (JSON export files now sync)
- ✅ Added `src/**/*.md` to sync includes (documentation files now sync)
- ✅ Moved job YAML to correct location: `resources/semantic/genie_spaces_deployment_job.yml`
- ✅ Updated job to use REST APIs (PATCH for updates, POST for creates)

### 2. Deployment Script Updated
- ✅ Fixed API method: `requests.patch()` instead of `requests.put()`
- ✅ Enhanced file loading with Workspace path fallback
- ✅ Simplified JSON file detection (hardcoded list)
- ✅ Added better error handling with stack traces

### 3. Bundle Deployed Successfully
```bash
✅ databricks bundle deploy -t dev --profile health_monitor
   Deployment complete!
```

---

## ❌ Current Issue

### Job Execution Failure

**Run URL:** https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/1036781264978047/run/878722248110421

**Error:**
```
RuntimeError: Failed to deploy 2 Genie Space(s)
```

**Problem:** The error message doesn't show the **specific failures** for each Genie Space. The script's error handling is catching exceptions but the detailed messages aren't appearing in the job output.

---

## 🔍 Troubleshooting Steps

### Step 1: Check Databricks Run Output

**Action:** Open the run URL and check the notebook output cells:
- https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/1036781264978047/run/878722248110421

**Look for:**
1. "Processing: /Workspace/..." messages
2. Error messages before the final RuntimeError
3. API response errors (403, 404, 500, etc.)

### Step 2: Verify JSON Files Are Synced

**Action:** Check if JSON export files exist in Workspace:

```python
# In Databricks notebook
import os

notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
script_dir = os.path.dirname(notebook_path)

print(f"Notebook directory: {script_dir}")

# Try to list files
try:
    files = dbutils.fs.ls(f"file:{script_dir}")
    print("\nFiles in directory:")
    for f in files:
        print(f"  - {f.name}")
except Exception as e:
    print(f"Error listing files: {e}")

# Try to read JSON files directly
json_files = [
    os.path.join(script_dir, "cost_intelligence_genie_export.json"),
    os.path.join(script_dir, "job_health_monitor_genie_export.json")
]

for json_file in json_files:
    try:
        with open(json_file, 'r') as f:
            content = f.read()
        print(f"\n✅ {os.path.basename(json_file)}: {len(content)} bytes")
    except Exception as e:
        print(f"\n❌ {os.path.basename(json_file)}: {e}")
```

### Step 3: Verify API Permissions

**Possible Issues:**
1. **Genie not enabled** - Workspace may not have Genie feature enabled
2. **API permissions** - Personal Access Token may lack `genie` scope
3. **Warehouse permissions** - SQL Warehouse ID may be invalid or user lacks access

**Action:** Test API access manually:

```bash
# List existing Genie Spaces
curl -X GET \
  "https://e2-demo-field-eng.cloud.databricks.com/api/2.0/genie/spaces" \
  -H "Authorization: Bearer <your_token>"

# Expected: JSON list of spaces OR 403/404 error
```

### Step 4: Check JSON Export File Contents

**Action:** Verify JSON files are valid and contain correct variable placeholders:

```bash
# Check file exists
ls -lh src/genie/*_export.json

# Verify JSON is valid
cat src/genie/cost_intelligence_genie_export.json | python -m json.tool | head -n 20

# Check for variable placeholders
grep -n '${catalog}' src/genie/cost_intelligence_genie_export.json
grep -n '${gold_schema}' src/genie/cost_intelligence_genie_export.json
```

---

## 🐛 Common Failure Scenarios

### Scenario 1: File Not Found
**Symptoms:** `FileNotFoundError: Could not find JSON file`

**Cause:** JSON files not synced or wrong path detection

**Fix:**
- Verify `src/**/*.json` in `databricks.yml` sync section ✅ (already done)
- Check files exist locally: `ls src/genie/*_export.json`
- Verify bundle deployed them: Check Workspace file browser

### Scenario 2: API Authentication Error
**Symptoms:** `403 Forbidden` or `401 Unauthorized`

**Cause:** Token expired or lacks permissions

**Fix:**
```bash
# Re-authenticate
databricks auth login --host https://e2-demo-field-eng.cloud.databricks.com --profile health_monitor

# Verify authentication
databricks auth profiles
```

### Scenario 3: Genie Feature Not Enabled
**Symptoms:** `404 Not Found` or `Feature not available`

**Cause:** Workspace doesn't have Genie enabled

**Fix:** Contact Databricks admin to enable Genie feature

### Scenario 4: Invalid JSON Schema
**Symptoms:** `METRIC_VIEW_INVALID_VIEW_DEFINITION` or similar API errors

**Cause:** JSON export format doesn't match API schema

**Fix:** Validate JSON export against cursor rule schema:
- Check `.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc`
- Verify all IDs are 32-char hex strings (UUID without dashes)
- Ensure all string fields are arrays: `"question": ["text"]`

### Scenario 5: SQL Warehouse Invalid
**Symptoms:** `Invalid warehouse_id`

**Cause:** Warehouse ID doesn't exist or user lacks access

**Fix:**
```python
# Get valid warehouse ID
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
warehouses = w.warehouses.list()

for wh in warehouses:
    print(f"  - {wh.name}: {wh.id}")
```

---

## 📊 Expected Deployment Flow

### Normal Execution (When Working)

```
1. Detecting JSON export files...
   Notebook path: /Workspace/Users/.../src/genie/deploy_genie_space.py
   Script directory: /Workspace/Users/.../src/genie
   Deploying 2 Genie Spaces from JSON exports

2. Processing: /Workspace/Users/.../src/genie/cost_intelligence_genie_export.json
   ════════════════════════════════════════════════════
   Deploying Genie Space: Health Monitor Cost Intelligence Space
   ════════════════════════════════════════════════════
   Loading JSON: /Workspace/Users/.../src/genie/cost_intelligence_genie_export.json
   Found existing space with ID: abc123...
   Updating Genie Space: Health Monitor Cost Intelligence Space
     Space ID: abc123...
     ✅ Updated successfully!

3. Processing: /Workspace/Users/.../src/genie/job_health_monitor_genie_export.json
   ════════════════════════════════════════════════════
   Deploying Genie Space: Health Monitor Job Reliability Space
   ════════════════════════════════════════════════════
   Loading JSON: /Workspace/Users/.../src/genie/job_health_monitor_genie_export.json
   Creating Genie Space: Health Monitor Job Reliability Space
     Warehouse ID: 4b9b953939869799
     Serialized space size: 50000 bytes
     ✅ Created successfully! Space ID: def456...

4. ════════════════════════════════════════════════════
   GENIE SPACE DEPLOYMENT SUMMARY
   ════════════════════════════════════════════════════
   
   ✅ Successfully Deployed: 2
      - cost_intelligence_genie_export.json: abc123...
      - job_health_monitor_genie_export.json: def456...
   
   ✅ All Genie Spaces deployed successfully!
```

---

## 🚀 Next Actions

### Immediate Actions (You)
1. ✅ Open the run URL in Databricks UI
2. ✅ Check notebook output cells for detailed error messages
3. ✅ Note specific API errors or file access errors
4. ✅ Share error details for further troubleshooting

### Follow-Up Actions (After Getting Error Details)

**If File Not Found:**
- Check Workspace file browser for JSON files
- Verify sync configuration worked correctly

**If API Error:**
- Check Genie feature availability
- Verify token permissions
- Test API manually with curl

**If Schema Error:**
- Validate JSON format
- Check all required fields present
- Verify variable substitution worked

---

## 📁 Files Updated

1. ✅ `databricks.yml` - Added JSON/MD to sync includes
2. ✅ `src/genie/deploy_genie_space.py` - Fixed API calls, improved error handling
3. ✅ `resources/semantic/genie_spaces_deployment_job.yml` - Updated job config
4. ✅ `src/genie/DEPLOYMENT_UPDATES.md` - Comprehensive deployment guide
5. ✅ `docs/deployment/genie-spaces/deployment-status.md` - This troubleshooting document

---

## 📚 Reference Documentation

### API Documentation
- [Create Space](https://docs.databricks.com/api/workspace/genie/createspace)
- [Update Space](https://docs.databricks.com/api/workspace/genie/updatespace)
- [List Spaces](https://docs.databricks.com/api/workspace/genie/listspaces)

### Cursor Rules
- [Genie Space Export/Import API](../../.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc)

### Project Documentation
- [Genie Spaces Inventory](../../reference/genie-spaces-inventory.md)
- [Deployment Updates](./DEPLOYMENT_UPDATES.md)

---

**Current Status:** Awaiting error details from Databricks UI to continue troubleshooting.

**Run URL:** https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/1036781264978047/run/878722248110421

