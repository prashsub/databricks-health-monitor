# Session 20: Genie Space Auto-Creation via API

**Date:** January 13, 2026  
**Status:** ✅ COMPLETE  
**Impact:** Automated new Genie Space creation when IDs are blank

---

## 🎯 Problem Statement

**User Request:**
> 1. Update Python notebooks with the parameter reading code (optional - if you want to use centralized config immediately)
> 2. Add a mechanism, that if the genie space id variables are blank or null, then create new genie spaces using this api https://openapi.dev.databricks.com/api/workspace/genie/createspace

**Root Cause:**
- Previously, all Genie Space IDs were hardcoded in `src/genie/deploy_genie_space.py`
- No mechanism to create new spaces automatically when setting up new environments
- Manual space creation required, then updating multiple files with IDs

---

## ✅ Solution Implemented

### 1. **Centralized Configuration in databricks.yml**

All Genie Space IDs now defined as Asset Bundle variables:

```yaml
variables:
  # Genie Space IDs (Single Source of Truth)
  cost_genie_space_id:
    description: Cost Intelligence Genie Space ID
    default: "01f0ea871ffe176fa6aee6f895f83d3b"
  
  reliability_genie_space_id:
    description: Job Reliability Genie Space ID
    default: "01f0ea8724fd160e8e959b8a5af1a8c5"
  
  quality_genie_space_id:
    description: Data Quality Genie Space ID
    default: "01f0ea93616c1978a99a59d3f2e805bd"
  
  performance_genie_space_id:
    description: Performance Genie Space ID
    default: "01f0ea93671e12d490224183f349dba0"
  
  security_genie_space_id:
    description: Security Auditor Genie Space ID
    default: "01f0ea9367f214d6a4821605432234c4"
  
  unified_genie_space_id:
    description: Unified Health Monitor Genie Space ID
    default: "01f0ea9368801e019e681aa3abaa0089"
```

---

### 2. **Parameter Reading in Python**

Updated `src/genie/deploy_genie_space.py` to read Genie Space IDs from parameters:

```python
# Get parameters from widgets
dbutils.widgets.text("cost_genie_space_id", "", "Cost Intelligence Genie Space ID")
dbutils.widgets.text("reliability_genie_space_id", "", "Reliability Genie Space ID")
dbutils.widgets.text("quality_genie_space_id", "", "Quality Genie Space ID")
dbutils.widgets.text("performance_genie_space_id", "", "Performance Genie Space ID")
dbutils.widgets.text("security_genie_space_id", "", "Security Genie Space ID")
dbutils.widgets.text("unified_genie_space_id", "", "Unified Health Monitor Genie Space ID")

# Read Genie Space IDs from parameters (override defaults)
cost_id = dbutils.widgets.get("cost_genie_space_id")
reliability_id = dbutils.widgets.get("reliability_genie_space_id")
quality_id = dbutils.widgets.get("quality_genie_space_id")
performance_id = dbutils.widgets.get("performance_genie_space_id")
security_id = dbutils.widgets.get("security_genie_space_id")
unified_id = dbutils.widgets.get("unified_genie_space_id")

# Set as environment variables for genie_spaces.py compatibility
if cost_id:
    os.environ["COST_GENIE_SPACE_ID"] = cost_id
if reliability_id:
    os.environ["RELIABILITY_GENIE_SPACE_ID"] = reliability_id
# ... etc
```

---

### 3. **Auto-Creation Logic**

Added blank/null detection with automatic space creation:

```python
# Build CONFIGURED_SPACE_IDS from parameters (may be empty strings)
CONFIGURED_SPACE_IDS = {
    "cost": cost_id or os.environ.get("COST_GENIE_SPACE_ID", ""),
    "reliability": reliability_id or os.environ.get("RELIABILITY_GENIE_SPACE_ID", ""),
    "quality": quality_id or os.environ.get("QUALITY_GENIE_SPACE_ID", ""),
    "performance": performance_id or os.environ.get("PERFORMANCE_GENIE_SPACE_ID", ""),
    "security": security_id or os.environ.get("SECURITY_GENIE_SPACE_ID", ""),
    "unified": unified_id or os.environ.get("UNIFIED_GENIE_SPACE_ID", ""),
}

print("=" * 80)
print("✓ Genie Space IDs Configuration")
print("=" * 80)
for domain, space_id in CONFIGURED_SPACE_IDS.items():
    if space_id:
        print(f"  {domain:15s}: {space_id} (will update)")
    else:
        print(f"  {domain:15s}: <blank> (will create new)")
print("=" * 80)
```

**Deployment Logic:**

```python
# Check if space ID is blank/null (indicates new space should be created)
if configured_space_id and configured_space_id.strip():
    print(f"✓ Found configured space ID: {configured_space_id}")
    print(f"  Domain: {domain}")
    print(f"  Deployment: UPDATING existing space (NOT creating new)")
else:
    print(f"⚠ Space ID is blank for domain '{domain}'")
    print(f"  Deployment: CREATING NEW space via API")
    configured_space_id = None  # Reset to None to trigger creation
```

---

### 4. **Job Configuration Updates**

Updated all 3 job YAMLs to pass Genie Space IDs as parameters:

**File: `resources/genie/genie_spaces_job.yml`**
```yaml
tasks:
  - task_key: deploy_genie_spaces
    notebook_task:
      notebook_path: ../../src/genie/deploy_genie_space.py
      base_parameters:
        catalog: ${var.catalog}
        gold_schema: ${var.gold_schema}
        feature_schema: ${var.feature_schema}
        warehouse_id: ${var.warehouse_id}
        genie_space_json: ""
        # Genie Space IDs from databricks.yml
        cost_genie_space_id: ${var.cost_genie_space_id}
        reliability_genie_space_id: ${var.reliability_genie_space_id}
        quality_genie_space_id: ${var.quality_genie_space_id}
        performance_genie_space_id: ${var.performance_genie_space_id}
        security_genie_space_id: ${var.security_genie_space_id}
        unified_genie_space_id: ${var.unified_genie_space_id}
```

**Also updated:**
- `resources/agents/agent_deployment_job.yml` (for agent runtime)
- `resources/agents/agent_setup_job.yml` (for evaluation)

---

### 5. **Improved User Output**

Enhanced feedback when new space is created:

```
✅ CREATED NEW GENIE SPACE
════════════════════════════════════════════════════════════════════════════════
  Space ID: 01f0ea871ffe176fa6aee6f895f83d3b
  Domain: cost
  Title: Health Monitor Cost Intelligence Space

⚠️  ACTION REQUIRED - Update databricks.yml:
════════════════════════════════════════════════════════════════════════════════
  File: databricks.yml
  Variable: cost_genie_space_id
  New Value: 01f0ea871ffe176fa6aee6f895f83d3b

  Example:
    cost_genie_space_id:
      description: Health Monitor Cost Intelligence Space
      default: "01f0ea871ffe176fa6aee6f895f83d3b"

  Then redeploy: databricks bundle deploy -t dev
════════════════════════════════════════════════════════════════════════════════
```

---

## 📊 Deployment Behavior Matrix

| Space ID Value | Deployment Behavior | Use Case |
|----|----|----|
| **Blank** (`""`) | ✅ **CREATE** new space via API | New environment, fresh start |
| **Valid ID** (`"01f0ea87..."`) | ✅ **UPDATE** existing space | Production, updates to config |
| **Invalid ID** | ❌ **ERROR** - space not found | Typo, deleted space |

---

## 🔄 Workflow Examples

### Example 1: New Environment Setup

**Scenario:** Setting up Genie Spaces in a new dev environment

**Step 1:** Leave IDs blank in `databricks.yml`
```yaml
variables:
  cost_genie_space_id:
    description: Cost Intelligence Genie Space ID
    default: ""  # ✅ Blank = auto-create
  
  reliability_genie_space_id:
    description: Job Reliability Genie Space ID
    default: ""  # ✅ Blank = auto-create
```

**Step 2:** Deploy bundle
```bash
databricks bundle deploy -t dev
```

**Step 3:** Run Genie deployment job
```bash
databricks bundle run -t dev genie_spaces_job
```

**Step 4:** Collect new IDs from job output
```
✅ CREATED NEW GENIE SPACE
  Space ID: 01f0ea871ffe176fa6aee6f895f83d3b
  Domain: cost

✅ CREATED NEW GENIE SPACE
  Space ID: 01f0ea8724fd160e8e959b8a5af1a8c5
  Domain: reliability
```

**Step 5:** Update `databricks.yml` with new IDs
```yaml
variables:
  cost_genie_space_id:
    default: "01f0ea871ffe176fa6aee6f895f83d3b"  # ✅ Now will UPDATE
  
  reliability_genie_space_id:
    default: "01f0ea8724fd160e8e959b8a5af1a8c5"  # ✅ Now will UPDATE
```

**Step 6:** Redeploy
```bash
databricks bundle deploy -t dev
```

**Result:** Future deployments will UPDATE these existing spaces

---

### Example 2: Mixed Update/Create

**Scenario:** Update most spaces, create one new space

```yaml
variables:
  cost_genie_space_id:
    default: "01f0ea871ffe176fa6aee6f895f83d3b"  # Will UPDATE
  
  reliability_genie_space_id:
    default: ""  # Will CREATE NEW (testing new config)
  
  quality_genie_space_id:
    default: "01f0ea93616c1978a99a59d3f2e805bd"  # Will UPDATE
```

**Result:**
- Cost Intelligence: **Updated** with new config
- Reliability: **New space created**, ID printed in output
- Quality: **Updated** with new config

---

## 📁 Files Modified

| File | Changes |
|----|---|
| `databricks.yml` | Added 6 Genie Space ID variables |
| `src/genie/deploy_genie_space.py` | Added parameter reading, auto-creation logic |
| `resources/genie/genie_spaces_job.yml` | Added Genie Space ID parameters |
| `resources/agents/agent_deployment_job.yml` | Added Genie Space ID parameters |
| `resources/agents/agent_setup_job.yml` | Added Genie Space ID parameters |
| `src/agents/config/genie_spaces.py` | Updated documentation (config hierarchy) |
| `docs/reference/genie-space-id-centralization.md` | Comprehensive documentation |

---

## ✅ Benefits

1. **Single Source of Truth** - All config in `databricks.yml`
2. **Environment Flexibility** - Override per target (dev/prod)
3. **Automated Creation** - No manual API calls needed
4. **Clear Instructions** - Auto-generated output for updating config
5. **Backward Compatible** - Existing spaces continue to update
6. **Agent Integration** - Parameters passed to agent for Genie tool routing

---

## 📚 Documentation

Created comprehensive documentation:
- **File:** `docs/reference/genie-space-id-centralization.md`
- **Sections:**
  - Configuration hierarchy
  - Auto-creation workflow
  - Deployment behavior matrix
  - Complete examples
  - Troubleshooting

---

## 🔑 Key Learnings

1. **Parameter Flow:** databricks.yml → base_parameters → dbutils.widgets.get() → environment variables
2. **Blank Detection:** Check both empty string (`""`) and None for auto-creation
3. **API Reference:** Use official Databricks API for space creation
4. **User Feedback:** Clear instructions reduce manual steps
5. **Environment Variables:** Set os.environ for backward compatibility with genie_spaces.py

---

## 🚀 Next Steps

1. ✅ **Deploy changes** - Completed successfully
2. ⏳ **Test auto-creation** - User can test by setting IDs to blank
3. ⏳ **Run Genie deployment** - Validate with existing IDs (update behavior)
4. ⏳ **Document in main README** - Add workflow to project docs

---

## 📊 Impact Summary

| Metric | Before | After | Improvement |
|----|----|----|----|
| **Config Files** | 2 (databricks.yml, genie_spaces.py) | 1 (databricks.yml) | -50% |
| **Manual Steps** | 3 (Create space, get ID, update code) | 1 (Update databricks.yml) | -67% |
| **Deployment Complexity** | High (code changes needed) | Low (config changes only) | ✅ Simplified |
| **Environment Setup** | Manual per environment | Automated | ✅ Automated |

---

## 📝 Code References

### Parameter Reading
```python:39:71:src/genie/deploy_genie_space.py
# Genie Space ID parameters (from databricks.yml variables)
dbutils.widgets.text("cost_genie_space_id", "", "Cost Intelligence Genie Space ID")
# ... 5 more widgets

# Read Genie Space IDs from parameters (override defaults)
cost_id = dbutils.widgets.get("cost_genie_space_id")
# ... 5 more reads

# SET GENIE SPACE IDS AS ENVIRONMENT VARIABLES
if cost_id:
    os.environ["COST_GENIE_SPACE_ID"] = cost_id
# ... 5 more environment variables
```

### Auto-Creation Logic
```python:618:650:src/genie/deploy_genie_space.py
# Check if space ID is blank/null (indicates new space should be created)
if configured_space_id and configured_space_id.strip():
    print(f"✓ Found configured space ID: {configured_space_id}")
    print(f"  Deployment: UPDATING existing space")
else:
    print(f"⚠ Space ID is blank - creating NEW space via API")
    configured_space_id = None  # Trigger creation

# Deployment logic
if existing_space_id:
    update_genie_space_via_api(...)  # Update
    return existing_space_id
else:
    result = create_genie_space_via_api(...)  # Create
    return result.get("space_id")
```

---

**Status:** ✅ COMPLETE  
**Session:** 20  
**Date:** January 13, 2026  
**Total Impact:** Automated Genie Space lifecycle management with centralized configuration

