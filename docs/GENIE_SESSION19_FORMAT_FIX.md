# Genie Session 19 - JSON Format Transformation Fix

**Date:** January 10, 2026  
**Issue:** Genie Space deployment failures due to JSON format mismatch  
**Status:** ✅ Fixed with format transformer

---

## Problem Summary

Genie Space deployments were failing for 5 out of 6 spaces with two types of errors:

1. **Invalid JSON** (cost_intelligence): `BAD_REQUEST: Invalid JSON in field 'serialized_space'`
2. **Unity Catalog Errors** (4 spaces): `INTERNAL_ERROR: Failed to retrieve schema from unity catalog`

Root cause: **JSON files were in a custom simplified format, not the Databricks API format.**

---

## Root Cause Analysis

### What We Had (Custom Format)

```json
{
  "version": 1,
  "config": {
    "name": "Health Monitor Cost Intelligence Space",  // ❌ Invalid field
    "description": [...],  // ❌ Invalid field
    "sample_questions": [  // ❌ Wrong structure (array of strings)
      "What is our total spend this month?",
      "Show me the top 10 workspaces by cost"
    ]
  },
  "data_sources": {
    "metric_views": [
      {
        "id": "a1b2c3d4...",  // ❌ Invalid field
        "name": "mv_cost_analytics",  // ❌ Should be "identifier"
        "full_name": "${catalog}.${gold_schema}.mv_cost_analytics",  // ❌ Should be "identifier"
        "description": [...]
      }
    ]
  }
}
```

### What Databricks API Expects (Official Format)

```json
{
  "version": 1,
  "config": {
    "sample_questions": [  // ✅ Array of objects
      {
        "id": "01f0ad3bc23713a48b30c9fbe1792b64",
        "question": ["What is our total spend this month?"]  // ✅ Question is array
      },
      {
        "id": "01f0ad3bc2361bebb2f6bb245992759f",
        "question": ["Show me the top 10 workspaces by cost"]
      }
    ]
  },
  "data_sources": {
    "metric_views": [
      {
        "identifier": "catalog.schema.mv_cost_analytics",  // ✅ Use "identifier"
        "description": [...],
        "column_configs": [...]
      }
    ]
  }
}
```

---

## Key Differences

| Field | Custom Format | API Format |
|-------|---------------|------------|
| **config.name** | ❌ Present | ❌ Must not exist |
| **config.description** | ❌ Present | ❌ Must not exist |
| **config.sample_questions** | ❌ Array of strings | ✅ Array of objects with `id` and `question` |
| **metric_views[].id** | ❌ Present | ❌ Must not exist |
| **metric_views[].name** | ❌ Present | ❌ Must not exist |
| **metric_views[].full_name** | ❌ Present | ❌ Must not exist |
| **metric_views[].identifier** | ❌ Missing | ✅ Required (full 3-part name) |

---

## Solution: Format Transformer

Created `transform_custom_format_to_api()` function in `deploy_genie_space.py`:

```python
def transform_custom_format_to_api(custom_data: dict) -> dict:
    """
    Transform custom simplified Genie Space format to Databricks API format.
    """
    import uuid
    
    api_data = {"version": custom_data.get("version", 1)}
    
    # Transform config section
    if "config" in custom_data:
        config = custom_data["config"]
        api_config = {}
        
        # Transform sample_questions: array of strings → array of objects
        if "sample_questions" in config:
            sample_qs = config["sample_questions"]
            if sample_qs and isinstance(sample_qs[0], str):
                # Generate UUIDs for each question
                api_config["sample_questions"] = [
                    {"id": uuid.uuid4().hex, "question": [q]}
                    for q in sample_qs
                ]
        
        api_data["config"] = api_config
    
    # Transform data_sources section
    if "data_sources" in custom_data:
        ds = custom_data["data_sources"]
        api_ds = {}
        
        # Transform metric_views: {full_name} → {identifier}
        if "metric_views" in ds:
            api_ds["metric_views"] = []
            for mv in ds["metric_views"]:
                if "full_name" in mv:
                    api_mv = {"identifier": mv["full_name"]}
                    if "description" in mv:
                        api_mv["description"] = mv["description"]
                    if "column_configs" in mv:
                        api_mv["column_configs"] = mv["column_configs"]
                    api_ds["metric_views"].append(api_mv)
        
        api_data["data_sources"] = api_ds
    
    # Copy instructions and benchmarks as-is
    if "instructions" in custom_data:
        api_data["instructions"] = custom_data["instructions"]
    if "benchmarks" in custom_data:
        api_data["benchmarks"] = custom_data["benchmarks"]
    
    return api_data
```

### Transformation Rules

1. **Remove** `config.name` and `config.description` (go in outer API wrapper)
2. **Convert** `sample_questions` from string array to object array with UUIDs
3. **Rename** `metric_views[].full_name` to `identifier`
4. **Remove** `metric_views[].id` and `.name` fields
5. **Keep** `instructions` and `benchmarks` as-is (already correct)

---

## Deployment Timeline

| Step | Status | Notes |
|------|--------|-------|
| **Initial Deployment** | ❌ 5/6 failed | Wrong space IDs + format issues |
| **Space ID Fix (Session 19)** | ✅ Deployed | Embedded space IDs directly |
| **Redeployment #1** | ❌ 5/6 failed | Correct IDs but invalid JSON format |
| **Format Transformer Fix** | ✅ Deployed | Transform custom → API format |
| **Redeployment #2** | ❌ 5/6 failed | Transformer ran too late (after sorting) |
| **Transformation Order Fix** | ✅ Deployed | Transform after substitution, before sorting |
| **Redeployment #3** | 🔄 Running | Expected: All 6 spaces should succeed |

**Run URLs:**
- Run #2: https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/874836782436399/run/45561803659984
- Run #3: https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/874836782436399/run/375821018278285

---

## Root Cause #2: Transformation Order

**Deployment #2 failed** even with the transformer because the transformation was happening **too late**:

### Incorrect Order (Deployment #2)
```python
def load_genie_space_export(...):
    export_data = json.loads(content)
    processed = process_json_values(export_data, ...)  # Substitute variables
    # Sort by 'identifier' - but metric views still have 'full_name'!
    processed['data_sources']['metric_views'].sort(key=lambda x: x.get('identifier', ''))
    return processed

def serialize_genie_space(export_data):
    transformed = transform_custom_format_to_api(export_data)  # Transform HERE (too late!)
    return json.dumps(transformed)
```

**Problem:** Sorting expected `identifier` field, but it was still `full_name`. Transformation happened after serialization, not after loading.

### Correct Order (Deployment #3)
```python
def load_genie_space_export(...):
    export_data = json.loads(content)
    processed = process_json_values(export_data, ...)  # 1. Substitute variables
    processed = transform_custom_format_to_api(processed)  # 2. Transform format ✅
    # 3. Sort by 'identifier' - NOW it exists!
    processed['data_sources']['metric_views'].sort(key=lambda x: x.get('identifier', ''))
    return processed

def serialize_genie_space(export_data):
    return json.dumps(export_data)  # 4. Simple serialization (no transformation)
```

**Fix:** Transform happens immediately after variable substitution, before sorting, and only once.

---

## Expected Results

After format transformation:

- ✅ **cost_intelligence**: No more "Invalid JSON" error
- ✅ **job_health_monitor**: No more Unity Catalog error
- ✅ **data_quality_monitor**: No more Unity Catalog error
- ✅ **security_auditor**: No more generic internal error
- ✅ **unified_health_monitor**: No more Unity Catalog error
- ✅ **performance**: Should continue to succeed

**Success Criteria:** 6/6 spaces deployed to correct production space IDs.

---

## Key Learnings

### 1. **Databricks API Format is Strict**

The Genie Space Export/Import API has a **very specific JSON schema**. Any deviation causes:
- `BAD_REQUEST: Invalid JSON` for structural issues
- `INTERNAL_ERROR: Failed to retrieve schema` for missing/invalid identifiers

### 2. **Custom Formats Need Transformation**

Our custom simplified format was more developer-friendly but incompatible with the API. Always follow the official schema or transform before serialization.

### 3. **Error Messages are Misleading**

"Failed to retrieve schema from unity catalog" actually meant "Invalid JSON structure", not "Tables don't exist". The API validates structure before checking Unity Catalog assets.

### 4. **Reference Implementation is Critical**

Having a working example (`context/genie/genie_space_export_formatted.json`) was essential to identify the correct API format.

### 5. **Transformation Order Matters**

The transformation must happen **after variable substitution** but **before sorting**. Otherwise:
- Variables like `${catalog}` remain unsubstituted
- Sorting fails because fields don't exist yet
- Double-transformation can corrupt the data

**Correct order:** Load → Substitute → Transform → Sort → Serialize

---

## Files Modified

1. **`src/genie/deploy_genie_space.py`**:
   - Added `transform_custom_format_to_api()` function
   - Updated `serialize_genie_space()` to call transformer
   - Embedded space IDs directly (no imports needed)

2. **JSON Files** (unchanged):
   - `src/genie/cost_intelligence_genie_export.json`
   - `src/genie/job_health_monitor_genie_export.json`
   - `src/genie/data_quality_monitor_genie_export.json`
   - `src/genie/performance_genie_export.json`
   - `src/genie/security_auditor_genie_export.json`
   - `src/genie/unified_health_monitor_genie_export.json`

**Note:** JSON files remain in custom format for developer convenience. Transformation happens at deployment time.

---

## Validation Checklist

To verify the fix worked:

- [ ] All 6 spaces deploy without errors
- [ ] Correct space IDs used (from `genie_spaces.py`)
- [ ] No "Invalid JSON" errors
- [ ] No "Failed to retrieve schema" errors
- [ ] Spaces accessible in Databricks UI
- [ ] Sample questions appear correctly
- [ ] Metric views/TVFs are accessible

---

## References

- **Genie Space Export/Import API Rule**: `.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc`
- **Reference Implementation**: `context/genie/genie_space_export_formatted.json`
- **Configured Space IDs**: `src/agents/config/genie_spaces.py`
- **Deployment Script**: `src/genie/deploy_genie_space.py`
- **Official API Docs**: https://docs.databricks.com/api/workspace/genie/createspace

---

## Next Steps

1. **Await deployment results** (~5-10 minutes)
2. **If successful**: Test all 6 spaces in UI with benchmark questions
3. **If failed**: Debug specific error messages (likely Unity Catalog asset issues)
4. **Update**: `genie_spaces.py` if any new space IDs were created

---

**Status:** 🔄 Awaiting deployment results - format transformer deployed, expecting 6/6 success

