# Genie Space Deployment - Update Existing Spaces

**Date:** January 10, 2026  
**Deployment Type:** UPDATE existing Genie Spaces (not create new)  
**Status:** ✅ Deploying

---

## Single Source of Truth: `genie_spaces.py`

All Genie Space IDs are maintained in **ONE** location:
```
src/agents/config/genie_spaces.py
```

This file contains the `GENIE_SPACE_REGISTRY` with all 6 configured space IDs.

---

## Genie Spaces Being Updated

### 1. Cost Intelligence Genie Space
- **Space ID:** `01f0ea871ffe176fa6aee6f895f83d3b`
- **Domain:** `cost`
- **JSON File:** `cost_intelligence_genie_export.json`
- **Status:** Updating existing space

### 2. Job Reliability Genie Space (Job Health Monitor)
- **Space ID:** `01f0ea8724fd160e8e959b8a5af1a8c5`
- **Domain:** `reliability`
- **JSON File:** `job_health_monitor_genie_export.json`
- **Status:** Updating existing space

### 3. Data Quality Monitor Genie Space
- **Space ID:** `01f0ea93616c1978a99a59d3f2e805bd`
- **Domain:** `quality`
- **JSON File:** `data_quality_monitor_genie_export.json`
- **Status:** Updating existing space

### 4. Performance Genie Space
- **Space ID:** `01f0ea93671e12d490224183f349dba0`
- **Domain:** `performance`
- **JSON File:** `performance_genie_export.json`
- **Status:** Updating existing space

### 5. Security Auditor Genie Space
- **Space ID:** `01f0ea9367f214d6a4821605432234c4`
- **Domain:** `security`
- **JSON File:** `security_auditor_genie_export.json`
- **Status:** Updating existing space

### 6. Unified Health Monitor Genie Space
- **Space ID:** `01f0ea9368801e019e681aa3abaa0089`
- **Domain:** `unified`
- **JSON File:** `unified_health_monitor_genie_export.json`
- **Status:** Updating existing space

---

## Deployment Method

### Script: `deploy_genie_space.py`

The deployment script was updated to:

1. **Import Space IDs from `genie_spaces.py`** (single source of truth)
2. **Map JSON files to domains** via `GENIE_SPACE_METADATA`
3. **Update existing spaces** using configured IDs (via PATCH API)
4. **Only create new spaces** if no ID is configured

### Key Changes

**BEFORE (Legacy):**
- Searched for spaces by title
- Could create duplicates
- No central configuration

**AFTER (Current):**
```python
# Import from single source of truth
from src.agents.config.genie_spaces import GENIE_SPACE_REGISTRY, DOMAINS

# Map JSON file to domain
domain = metadata.get("domain")  # e.g., "cost", "security"

# Get configured space ID
configured_space_id = GENIE_SPACE_REGISTRY[domain].get_id()

# Update existing space (PATCH API)
if configured_space_id:
    update_genie_space_via_api(
        host, token, configured_space_id, title, description,
        warehouse_id, serialized_space, preserve_title=True
    )
```

---

## API Calls Being Made

### For Each Genie Space:

```bash
# Update existing space (PATCH)
PATCH /api/2.0/genie/spaces/{space_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "description": "Natural language interface for...",
  "warehouse_id": "abc123",
  "serialized_space": "{...JSON export content...}"
}
```

**Note:** `preserve_title=True` ensures title doesn't change (avoids conflicts with spaces that have numeric suffixes like "(3)").

---

## What Gets Updated

Each Genie Space update includes:

### 1. Data Assets
- **Tables:** Unity Catalog tables with column configs
- **Metric Views:** Semantic layer metric definitions
- **Sample Questions:** 25 benchmark questions per space

### 2. Instructions
- **Text Instructions:** LLM guidance and business context
- **SQL Functions (TVFs):** 60 Table-Valued Functions
- **Join Specifications:** Table relationship definitions
- **Example Question SQLs:** Benchmark answers

### 3. Benchmarks
- **150 Total Questions:** 25 per space
- **100% Pass Rate:** All SQL queries validated
- **Ground Truth Verified:** Using `docs/reference/actual_assets/`

---

## Deployment Status

### Pre-Deployment Validation ✅

**Genie Benchmark SQL Validation Job:**
- **Run:** Jan 10, 2026 (Session 18)
- **Status:** 150/150 (100%) ✅
- **Errors Fixed:** 26 errors across Sessions 16-18
- **Method:** Ground truth verification from `docs/reference/actual_assets/`

### Current Deployment 🚀

**Job:** `genie_spaces_deployment_job`  
**Run URL:** [View Deployment](https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/874836782436399/run/29354148347831)  
**Status:** Running

**Expected Duration:** ~2-3 minutes (6 spaces × ~20-30 seconds each)

---

## Deployment Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   GENIE SPACE DEPLOYMENT FLOW                    │
└─────────────────────────────────────────────────────────────────┘

Step 1: Load Space IDs from genie_spaces.py
  ├─ Cost Intelligence:      01f0ea871ffe176fa6aee6f895f83d3b
  ├─ Job Reliability:        01f0ea8724fd160e8e959b8a5af1a8c5
  ├─ Data Quality:           01f0ea93616c1978a99a59d3f2e805bd
  ├─ Performance:            01f0ea93671e12d490224183f349dba0
  ├─ Security Auditor:       01f0ea9367f214d6a4821605432234c4
  └─ Unified Health Monitor: 01f0ea9368801e019e681aa3abaa0089

Step 2: For Each JSON Export File
  ├─ Load JSON export file
  ├─ Substitute catalog/schema variables
  ├─ Get domain from GENIE_SPACE_METADATA
  ├─ Lookup configured space ID from genie_spaces.py
  ├─ Serialize to Genie Space format
  ├─ PATCH /api/2.0/genie/spaces/{space_id} (update)
  └─ Verify success

Step 3: Deployment Summary
  ├─ 6/6 spaces updated successfully
  └─ All spaces ready for production use
```

---

## Configuration Files Updated

### 1. `src/genie/deploy_genie_space.py`
- Added import from `src/agents/config/genie_spaces.py`
- Updated `deploy_genie_space()` to use configured space IDs
- Added domain mapping in `GENIE_SPACE_METADATA`
- Added fallback messaging if no space ID found

### 2. `src/agents/config/genie_spaces.py`
- **No changes** - Already contains all 6 space IDs
- Serves as single source of truth
- Used by both agent framework and deployment script

---

## Benefits of This Approach

### 1. Single Source of Truth
- All space IDs in one place (`genie_spaces.py`)
- No duplicate configuration
- Easy to update/maintain

### 2. Safe Updates
- Updates existing spaces (no duplicates)
- Uses PATCH API (partial updates)
- Preserves space titles and permissions

### 3. Agent Framework Integration
- Same space IDs used by agent routing
- Consistent across deployment and runtime
- Environment variable overrides supported

### 4. Version Control
- Space IDs tracked in Git
- Changes auditable
- Easy to rollback if needed

---

## Verification After Deployment

### Check Space IDs

```python
# Verify all 6 spaces exist with correct IDs
from src.agents.config.genie_spaces import GENIE_SPACE_REGISTRY

for domain, config in GENIE_SPACE_REGISTRY.items():
    space_id = config.get_id()
    print(f"{domain}: {space_id}")
```

### Test in UI

1. Navigate to Databricks Genie Spaces
2. Find each space by ID
3. Test sample questions:
   - "Why did costs spike yesterday?"
   - "Which jobs failed today?"
   - "Show me slow queries"
   - "Which tables haven't been updated?"
   - "Show failed login attempts"
   - "What's the overall platform health?"

### Query Validation

All 150 benchmark questions should return results without errors.

---

## Rollback Plan (If Needed)

### Option 1: Redeploy Previous Version

1. Checkout previous commit
2. Run `databricks bundle deploy -t dev`
3. Run `databricks bundle run -t dev genie_spaces_deployment_job`

### Option 2: Manual Rollback via UI

1. Open Genie Space in UI
2. Manually revert configuration changes
3. Test queries

---

## Key Learning: Space ID Management

### ✅ DO THIS
- Maintain space IDs in `genie_spaces.py` (single source of truth)
- Use domain mapping to link JSON files to space IDs
- Update existing spaces via PATCH API
- Import space IDs for both deployment and runtime

### ❌ DON'T DO THIS
- Hardcode space IDs in multiple files
- Search for spaces by title (can create duplicates)
- Create new spaces when updating existing ones
- Use different space IDs for deployment vs runtime

---

## References

### Documentation
- [Genie Space Export/Import API](../cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc)
- [Genie Space Configuration](../../src/agents/config/genie_spaces.py)
- [Validation Report](GENIE_SESSION18_UNIFIED_FINAL_4.md)

### API Endpoints
- POST `/api/2.0/genie/spaces` - Create new space
- **PATCH `/api/2.0/genie/spaces/{id}`** - Update existing (THIS DEPLOYMENT)
- GET `/api/2.0/genie/spaces/{id}` - Get space details
- DELETE `/api/2.0/genie/spaces/{id}` - Delete space

---

**Status:** ✅ **Deployment Running**  
**Run URL:** [View Progress](https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/874836782436399/run/29354148347831)  
**Expected Completion:** ~2-3 minutes

