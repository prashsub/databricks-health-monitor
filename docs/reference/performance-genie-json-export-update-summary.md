# Performance Genie - JSON Export Update Summary

**Date:** January 2026  
**Source:** `src/genie/performance_genie.md`  
**Target:** `src/genie/performance_genie_export.json`

---

## Updates Applied ✅

### 1. Query TVF Name Corrections (10 updates)

All Table-Valued Function references updated to match deployed assets from `docs/actual_assets.md`:

| Old Name | New Name | Usage |
|----------|----------|-------|
| `get_slowest_queries` | `get_slow_queries` | Slow query identification |
| `get_query_latency_percentiles` | `get_query_duration_percentiles` | Duration percentile analysis |
| `get_warehouse_performance` | `get_warehouse_utilization` | Warehouse metrics |
| `get_top_users_by_query_count` | `get_top_query_users` | Top users by query volume |
| `get_query_efficiency_by_user` | `get_user_query_efficiency` | User-level efficiency |
| `get_query_queue_analysis` | `get_warehouse_queue_analysis` | Queue time analysis |
| `get_failed_queries_summary` | `get_failed_queries` | Failed query list |
| `get_cache_hit_analysis` | `get_query_cache_analysis` | Cache effectiveness |
| `get_spill_analysis` | `get_query_spill_analysis` | Memory pressure queries |

### 2. Cluster TVF Name Corrections (3 updates)

| Old Name | New Name | Usage |
|----------|----------|-------|
| `get_cluster_utilization` | `get_cluster_resource_utilization` | Cluster resource metrics |
| `get_underutilized_clusters` | `get_idle_clusters` | Underutilized clusters |
| `get_autoscaling_disabled_jobs` | `get_jobs_without_autoscaling` | Jobs missing autoscale |

### 3. TVF Removals (2 non-existent or duplicate functions)

| Removed Function | Reason |
|------------------|--------|
| `get_cluster_resource_metrics` | Duplicate/non-existent function |
| `get_cluster_rightsizing_recommendations` | ML table, not a TVF |

### 4. Benchmark SQL Query Updates (8 queries)

**Query 5 - Slow queries:**
```sql
-- Old (DATE_FORMAT)
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_slow_queries(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 1 DAY, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  30
))

-- New (::STRING cast + top_n parameter)
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_slow_queries(
  CURRENT_DATE()::STRING,
  CURRENT_DATE()::STRING,
  30,
  50
))
```

**Query 7 - Warehouse utilization:**
```sql
-- Old function name + DATE_FORMAT
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_warehouse_performance(...))

-- New function name + ::STRING cast
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_warehouse_utilization(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
```

**Query 8 - High spill queries:**
```sql
-- Old function name + column name
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_high_spill_queries(...))
ORDER BY local_spill_gb DESC

-- New function name + corrected column
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_query_spill_analysis(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  1.0
))
ORDER BY spill_bytes DESC
```

**Query 10 - Underutilized clusters:**
```sql
-- Old function name + single parameter
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_underutilized_clusters(30))

-- New function name + full signature
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_idle_clusters(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  20.0
))
```

**Query 12 - Query volume trends:**
```sql
-- Old DATE_FORMAT
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_query_volume_trends(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 14 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
))

-- New ::STRING cast
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_query_volume_trends(
  (CURRENT_DATE() - INTERVAL 14 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
```

**Query 14 - Query latency percentiles:**
```sql
-- Old function name + column name
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_query_latency_percentiles(...))
ORDER BY p99_seconds DESC

-- New function name + corrected column
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_query_duration_percentiles(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
ORDER BY p99_duration DESC
```

**Query 16 - Cluster right-sizing:**
```sql
-- Old (TVF call - incorrect)
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cluster_right_sizing_recommendations(30))

-- New (ML table query - correct)
SELECT * FROM ${catalog}.${feature_schema}.cluster_rightsizing_recommendations
WHERE recommended_action IN ('DOWNSIZE', 'UPSIZE')
ORDER BY potential_savings_usd DESC
LIMIT 20;
```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Total TVF Name Corrections** | **13** |
| **TVF Removals** | **2** |
| **Benchmark SQL Query Updates** | **8** |
| **Total Changes** | **23** |

---

## Key Patterns Applied

### 1. Date Parameter Format
- **Old:** `DATE_FORMAT(CURRENT_DATE() - INTERVAL X DAYS, 'yyyy-MM-dd')`
- **New:** `(CURRENT_DATE() - INTERVAL X DAYS)::STRING`

### 2. TVF Signature Compliance
- Added missing parameters (e.g., `top_n INT DEFAULT 50` for `get_slow_queries`)
- Updated all signatures to match deployed TVF definitions

### 3. ML Table vs TVF Distinction
- Removed `get_cluster_rightsizing_recommendations` from TVF list
- Updated benchmark query to query ML table directly with `${feature_schema}`

### 4. Column Name Standardization
- `local_spill_gb` → `spill_bytes`
- `p99_seconds` → `p99_duration`
- `potential_savings` → `potential_savings_usd`

---

## Validation

✅ **JSON is valid** - Confirmed with `python3 -m json.tool`

---

## References

- **Source Markdown:** `src/genie/performance_genie.md` - 21 TVF definitions
- **Actual Assets Inventory:** `docs/actual_assets.md` - Source of truth for deployed assets
- **ML Models Inventory:** `src/ml/ML_MODELS_INVENTORY.md` - 7 Performance ML models


