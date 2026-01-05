# TVF and Metric View Schema Validation Summary

## Date: 2025-12-19

## Overview

This document summarizes the schema validation performed on TVFs and Metric Views against the Gold Layer YAML definitions as the single source of truth.

## Key Issues Identified and Fixed

### 1. Non-Existent Column: `is_current`

**Issue:** Multiple TVF and Metric View files referenced `is_current = TRUE` for filtering dimension tables. However, most dimension tables in the Gold layer do NOT have an `is_current` column.

**Tables Affected:**
- `dim_workspace` - Has NO `is_current` or `delete_time` column (simple reference table)
- `dim_job` - Uses `delete_time IS NULL` instead of `is_current = TRUE`
- `dim_cluster` - Uses `delete_time IS NULL` instead of `is_current = TRUE`
- `dim_warehouse` - Uses `delete_time IS NULL` instead of `is_current = TRUE`
- `dim_sku` - Has NO `is_current` column (simple lookup table)

**Fix Applied:**
- Removed `is_current = TRUE` conditions from all `dim_workspace` joins
- Replaced `is_current = TRUE` with `delete_time IS NULL` for `dim_job`, `dim_cluster`, `dim_warehouse`
- Removed `dim_sku` joins entirely where only `sku_description` was being used (column doesn't exist)

### 2. Non-Existent Column: `sku_description`

**Issue:** Multiple metric views referenced `dim_sku.sku_description`, but this column doesn't exist in `dim_sku`.

**Available columns in `dim_sku`:**
- `sku_name` (PRIMARY KEY)
- `cloud`
- `usage_unit`

**Fix Applied:** Removed all references to `sku_description` and removed `dim_sku` joins where only this column was being used.

### 3. Incorrect Column Name: `owned_by` → `identity_metadata_owned_by`

**Issue:** TVFs referenced `owned_by` column in `fact_usage`, but the actual column name is `identity_metadata_owned_by` (flattened from nested struct).

**Fix Applied:** Updated all references from `owned_by` to `identity_metadata_owned_by`.

### 4. Incorrect Column Name: `cluster_size` → `warehouse_size`

**Issue:** `performance_tvfs.sql` referenced `w.cluster_size` for dim_warehouse, but the actual column is `warehouse_size`.

**Fix Applied:** Changed `cluster_size` to `warehouse_size` in the query and GROUP BY.

### 5. Missing Composite Key in Joins

**Issue:** `dim_job` has a composite primary key `(workspace_id, job_id)`, but some joins only used `job_id`.

**Fix Applied:** Updated all dim_job joins to include both `workspace_id` AND `job_id`:
```sql
ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
```

### 6. Run-as Column Not in fact_job_run_timeline

**Issue:** `reliability_tvfs.sql` referenced `jrt.run_as` but `fact_job_run_timeline` doesn't have a `run_as` column. The column is in `dim_job`.

**Fix Applied:** Changed references from `jrt.run_as` to `j.run_as` (joining to dim_job).

## Files Modified

### TVF SQL Files

| File | Issues Fixed |
|------|--------------|
| `cost_tvfs.sql` | `is_current` → `delete_time IS NULL`, `owned_by` → `identity_metadata_owned_by` |
| `reliability_tvfs.sql` | `is_current` → `delete_time IS NULL`, composite key joins, `jrt.run_as` → `j.run_as`, `owned_by` → `identity_metadata_owned_by` |
| `performance_tvfs.sql` | `is_current` → `delete_time IS NULL`, composite key joins, `cluster_size` → `warehouse_size` |
| `quality_tvfs.sql` | `is_current` → `delete_time IS NULL`, composite key joins |
| `security_tvfs.sql` | No changes needed (no dimension joins) |

### Metric View YAML Files

| File | Issues Fixed |
|------|--------------|
| `cost_analytics.yaml` | Removed `dim_sku` join, removed `sku_description` dimension, fixed `dim_workspace` join |
| `ml_intelligence.yaml` | Removed `dim_sku` join, removed `sku_description` dimension, fixed `dim_workspace` join |
| `governance_analytics.yaml` | Fixed `dim_workspace` join |
| `security_events.yaml` | Fixed `dim_workspace` join |
| `cluster_efficiency.yaml` | Fixed `dim_workspace` and `dim_cluster` joins |
| `cluster_utilization.yaml` | Fixed `dim_workspace` and `dim_cluster` joins |
| `query_performance.yaml` | Fixed `dim_workspace` and `dim_warehouse` joins |
| `job_performance.yaml` | Fixed `dim_workspace` and `dim_job` joins |
| `commit_tracking.yaml` | Removed `dim_sku` join, fixed `dim_workspace` join |

## Validation Pattern

### Gold Layer YAML as Single Source of Truth

All column references should be validated against the Gold Layer YAML files:

```
gold_layer_design/yaml/
├── billing/
│   ├── dim_sku.yaml         # sku_name, cloud, usage_unit
│   └── fact_usage.yaml      # identity_metadata_* (flattened)
├── compute/
│   └── dim_cluster.yaml     # delete_time for filtering
├── lakeflow/
│   ├── dim_job.yaml         # workspace_id, job_id (composite PK), delete_time
│   └── fact_job_run_timeline.yaml
├── query_performance/
│   └── dim_warehouse.yaml   # warehouse_size (not cluster_size), delete_time
└── shared/
    └── dim_workspace.yaml   # No is_current, no delete_time
```

### Filter Patterns by Table

| Dimension Table | Filter Pattern |
|-----------------|----------------|
| `dim_workspace` | No filter needed (simple reference) |
| `dim_job` | `AND j.delete_time IS NULL` |
| `dim_cluster` | `AND c.delete_time IS NULL` |
| `dim_warehouse` | `AND w.delete_time IS NULL` |
| `dim_sku` | No filter needed (simple lookup) |

### Composite Key Join Patterns

| Fact/Dim Pair | Join Pattern |
|---------------|--------------|
| `fact_job_run_timeline` → `dim_job` | `ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id` |
| `fact_usage` → `dim_workspace` | `ON f.workspace_id = w.workspace_id` |
| `fact_query_history` → `dim_warehouse` | `ON f.workspace_id = w.workspace_id AND f.compute_warehouse_id = w.warehouse_id` |
| `fact_node_timeline` → `dim_cluster` | `ON f.workspace_id = c.workspace_id AND f.cluster_id = c.cluster_id` |

## Prevention Recommendations

1. **Always validate column names** against Gold Layer YAML before using in TVF/Metric View
2. **Check for composite keys** when joining to dimension tables
3. **Use `delete_time IS NULL`** instead of `is_current = TRUE` for dimensions with soft delete
4. **Don't assume flattened column names** - check the actual column names in YAML (e.g., `identity_metadata_owned_by` not `owned_by`)
5. **Run schema validation script** before deploying TVFs or Metric Views

## Next Steps

1. Deploy the fixed TVF and Metric View files
2. Validate deployment in Databricks workspace
3. Run integration tests against live Gold layer tables
4. Monitor for any remaining schema-related errors in deployment logs





