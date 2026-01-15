# Genie Space Deployment Troubleshooting Guide

**Date:** January 10, 2026  
**Issue:** Genie Space deployment failures  
**Status:** 🔧 Troubleshooting in progress

---

## Problem Summary

Initial deployment attempt failed for 5 out of 6 spaces:

| Space | Error Type | Status |
|-------|------------|--------|
| **cost_intelligence** | `BAD_REQUEST` - Invalid JSON | ❌ Failed |
| **job_health_monitor** | `INTERNAL_ERROR` - Unity Catalog | ❌ Failed |
| **data_quality_monitor** | `INTERNAL_ERROR` - Unity Catalog | ❌ Failed |
| **security_auditor** | `INTERNAL_ERROR` - Generic | ❌ Failed |
| **unified_health_monitor** | `INTERNAL_ERROR` - Unity Catalog | ❌ Failed |
| **performance** | Success | ✅ Deployed |

---

## Root Causes Identified

### 1. Wrong Space IDs Used (FIXED)

**Problem:** Script couldn't import `genie_spaces.py` due to path issues, fell back to title-based lookup, found old duplicate spaces

**Configured vs. Found (OLD BEHAVIOR):**
```
Job Reliability:     01f0ea8724fd160e8e959b8a5af1a8c5 → Found: 01f0edfaee791e118c82a4c284c766b1 ❌
Data Quality:        01f0ea93616c1978a99a59d3f2e805bd → Found: 01f0edfaef1719deb11e07386af11b02 ❌
Performance:         01f0ea93671e12d490224183f349dba0 → Found: 01f0edfaef9113d685bfcdad5833d255 ❌
Unified:             01f0ea9368801e019e681aa3abaa0089 → Found: 01f0edfaf0341d49bda1e0825f747b77 ❌
```

**Fix Applied:**
- Embedded space IDs directly in `deploy_genie_space.py` (no imports needed)
- Changed lookup logic to use `CONFIGURED_SPACE_IDS` directly
- Now correctly references the configured production space IDs

**Verification:**
```python
# Embedded space IDs (from genie_spaces.py - updated Jan 10, 2026)
CONFIGURED_SPACE_IDS = {
    "cost": "01f0ea871ffe176fa6aee6f895f83d3b",           # ✅ Correct
    "reliability": "01f0ea8724fd160e8e959b8a5af1a8c5",    # ✅ Correct
    "quality": "01f0ea93616c1978a99a59d3f2e805bd",       # ✅ Correct
    "performance": "01f0ea93671e12d490224183f349dba0",   # ✅ Correct
    "security": "01f0ea9367f214d6a4821605432234c4",      # ✅ Correct
    "unified": "01f0ea9368801e019e681aa3abaa0089",       # ✅ Correct
}
```

---

### 2. Invalid JSON Serialization

**Error:**
```
[cost_intelligence] BAD_REQUEST: Invalid JSON in field 'serialized_space'
```

**Possible Causes:**
1. **Special characters** in instruction text or descriptions (quotes, newlines, Unicode)
2. **JSON escaping issues** in SQL queries within `answer.content`
3. **Large payload size** (33,618 bytes for cost_intelligence)
4. **Malformed nested JSON** in the `serialized_space` field

**Troubleshooting Steps:**
1. Validate JSON structure locally:
   ```bash
   python -m json.tool src/genie/cost_intelligence_genie_export.json
   ```

2. Check for problematic characters:
   ```python
   import json
   with open('src/genie/cost_intelligence_genie_export.json') as f:
       data = json.load(f)
       serialized = json.dumps(data, indent=2)
       # Check for issues
       print(f"Size: {len(serialized)} bytes")
       print(f"Contains \\u escape: {r'\\u' in serialized}")
   ```

3. Compare with working space (performance):
   - Size: 33,618 bytes (cost) vs. ? bytes (performance)
   - Structure differences

**Next Steps:**
- [ ] Validate JSON structure for cost_intelligence
- [ ] Compare with performance (working space)
- [ ] Check for Unicode/escape issues

---

### 3. Unity Catalog Schema Errors

**Error:**
```
[job_health_monitor, data_quality_monitor, unified_health_monitor]
INTERNAL_ERROR: Failed to retrieve schema from unity catalog
```

**Possible Causes:**
1. **Table/view doesn't exist** in the referenced catalog/schema
2. **Permission issues** - workspace can't read the Unity Catalog asset
3. **Incorrect table_full_name** in `data_assets` section (e.g., wrong catalog, schema, or table name)
4. **Table was dropped/renamed** after JSON was generated

**Affected Assets Check:**
```sql
-- Check if tables exist
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold;
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml;
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring;
```

**Validation Script:**
```python
# Extract data_assets from JSON
import json

def validate_assets(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    assets = data.get('space_entity', {}).get('data_assets', [])
    
    print(f"Validating {len(assets)} assets in {json_file}...")
    for asset in assets:
        table_name = asset.get('table_full_name', '')
        print(f"  - {table_name}")
        
        try:
            spark.sql(f"DESCRIBE TABLE {table_name}").collect()
            print(f"    ✅ Exists")
        except Exception as e:
            print(f"    ❌ NOT FOUND: {e}")

# Run for each failing space
validate_assets('src/genie/job_health_monitor_genie_export.json')
validate_assets('src/genie/data_quality_monitor_genie_export.json')
validate_assets('src/genie/unified_health_monitor_genie_export.json')
```

**Next Steps:**
- [ ] Run asset validation script
- [ ] Identify missing tables
- [ ] Fix `data_assets` section in JSON files
- [ ] Ensure all TVFs, Metric Views, and tables are deployed

---

### 4. Generic Internal Errors

**Error:**
```
[security_auditor] INTERNAL_ERROR: An internal error occurred, please try again later
```

**Possible Causes:**
1. **Databricks API rate limiting**
2. **Transient service error**
3. **Same underlying issues** as other spaces (Unity Catalog, JSON)

**Retry Strategy:**
- Wait 5-10 minutes between deployment attempts
- Deploy spaces one at a time instead of all 6
- Check Databricks service status

---

## Action Plan

### Immediate (Session 19)

1. ✅ **Fix space ID lookup** (COMPLETED)
   - Embedded space IDs directly
   - Fixed lookup logic

2. 🔄 **Wait for redeployment results** (IN PROGRESS)
   - Run URL: https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/874836782436399/run/242736443272448
   - Expected: All 6 spaces should now use correct IDs

3. **If still failing:**
   - Run Unity Catalog asset validation
   - Check JSON serialization for cost_intelligence
   - Deploy spaces one at a time with detailed logging

### Follow-up

4. **Create Unity Catalog validator**
   - Add `validate_unity_catalog_assets()` function
   - Check all `data_assets` before deployment

5. **Add JSON sanitization**
   - Strip problematic characters
   - Validate serialized_space size
   - Add pre-deployment JSON validation

6. **Improve error messages**
   - Log full API response
   - Include request_id for Databricks support

---

## Success Criteria

- [ ] All 6 Genie Spaces deployed to correct space IDs
- [ ] No "Invalid JSON" errors
- [ ] No "Failed to retrieve schema" errors
- [ ] All spaces accessible in Databricks UI
- [ ] Benchmark questions work in each space

---

## Resources

- **Genie Space Export/Import API**: `.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc`
- **Configured Space IDs**: `src/agents/config/genie_spaces.py`
- **Deployment Script**: `src/genie/deploy_genie_space.py`
- **Job Config**: `resources/genie/genie_spaces_job.yml`

---

## Next: Await Redeployment Results

The deployment is running with the fixed space ID logic. Next steps:
1. Check deployment logs
2. If successful: Test spaces in UI
3. If failed: Run asset validation and debug specific errors

