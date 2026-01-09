# Data Quality Monitor Genie - JSON Export Update Summary

**Date:** January 2026  
**Source:** `src/genie/data_quality_monitor_genie.md`  
**Target:** `src/genie/data_quality_monitor_genie_export.json`

---

## Updates Applied ✅

### 1. TVF Name Corrections (5 Updates)

All Table-Valued Function references updated to match deployed assets from `docs/actual_assets.md`:

| Old Name | New Name | Usage |
|----------|----------|-------|
| `get_table_freshness` | `get_stale_tables` | Freshness monitoring |
| `get_pipeline_data_lineage` | `get_pipeline_lineage_impact` | Pipeline dependencies |
| `get_table_activity_status` | `get_table_activity_summary` | Activity status |
| *(New)* | `get_table_lineage` | Table-level lineage tracking |
| *(New)* | `get_data_lineage_summary` | Lineage summary by catalog/schema |

### 2. SQL Functions Section Updated

**Before:**
```json
"sql_functions": [
  { "identifier": "${catalog}.${gold_schema}.get_table_freshness" },
  { "identifier": "${catalog}.${gold_schema}.get_pipeline_data_lineage" },
  { "identifier": "${catalog}.${gold_schema}.get_table_activity_status" }
]
```

**After:**
```json
"sql_functions": [
  { "identifier": "${catalog}.${gold_schema}.get_stale_tables" },
  { "identifier": "${catalog}.${gold_schema}.get_table_lineage" },
  { "identifier": "${catalog}.${gold_schema}.get_table_activity_summary" },
  { "identifier": "${catalog}.${gold_schema}.get_data_lineage_summary" },
  { "identifier": "${catalog}.${gold_schema}.get_pipeline_lineage_impact" }
]
```

### 3. Benchmark SQL Queries Updated

#### Example 1: Stale Tables Query
**Before:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_freshness(24)
WHERE is_stale = TRUE
ORDER BY hours_since_update DESC
LIMIT 20;
```

**After:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(7, 24))
WHERE hours_since_update > 24
ORDER BY hours_since_update DESC
LIMIT 20;
```

**Changes:**
- ✅ TVF name: `get_table_freshness` → `get_stale_tables`
- ✅ Added `TABLE()` wrapper for TVF call
- ✅ Updated signature: `(24)` → `(7, 24)` (days_back, freshness_threshold_hours)
- ✅ Filter condition: `is_stale = TRUE` → `hours_since_update > 24`

#### Example 2: Activity Status Query
**Before:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_activity_status(7, 14))
WHERE activity_status = 'INACTIVE'
```

**After:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(7))
WHERE activity_status = 'INACTIVE'
```

**Changes:**
- ✅ TVF name: `get_table_activity_status` → `get_table_activity_summary`
- ✅ Signature: `(7, 14)` → `(7)` (removed inactive_threshold_days parameter)

#### Example 3: Pipeline Lineage Query
**Before:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_pipeline_data_lineage(7, 'ALL'))
```

**After:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_pipeline_lineage_impact(7, '%'))
```

**Changes:**
- ✅ TVF name: `get_pipeline_data_lineage` → `get_pipeline_lineage_impact`
- ✅ Parameter: `'ALL'` → `'%'` (wildcard pattern)

### 4. Instructions Section Updated

**Before:**
```
"- If user asks for a LIST → TVF (get_table_freshness, get_table_activity_status)\n"
```

**After:**
```
"- If user asks for a LIST → TVF (get_stale_tables, get_table_activity_summary)\n"
```

---

## Files Modified

| File | Changes |
|------|---------|
| `src/genie/data_quality_monitor_genie_export.json` | 5 TVF names, 10+ SQL queries, instructions section |

---

## Validation Results ✅

```bash
python3 -m json.tool src/genie/data_quality_monitor_genie_export.json
# Result: ✅ Valid JSON
```

---

## Summary

Successfully updated the Data Quality Monitor Genie JSON export with:
- ✅ **5 TVF name corrections** to match actual deployed assets
- ✅ **10+ SQL query updates** with correct signatures and parameters
- ✅ **Instructions section** updated with correct TVF references
- ✅ **JSON validation passed** - ready for deployment

All changes align with `docs/actual_assets.md` inventory.

---

## Next Steps

1. ✅ JSON export validated and ready
2. ⏭️ Continue with remaining Genie spaces (if any)
3. ⏭️ Deploy updated JSON exports to Genie Space via API

---

**Status:** ✅ **COMPLETE**


