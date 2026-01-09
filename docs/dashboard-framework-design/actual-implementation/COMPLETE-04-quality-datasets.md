# Complete Data Quality Dataset Catalog

## Overview
**Total Datasets:** 32  
**Dashboard:** `quality.lvdash.json`  
**Coverage:** ALL datasets from ALL pages with FULL details

---

## Dataset Index

| # | Dataset Name | Display Name | Has Query | Parameters |
|---|--------------|--------------|-----------|------------|
| 1 | ds_kpi_tables | KPI: Tables | ✅ | param_catalog |
| 2 | ds_kpi_tagged | KPI: Tagged | ✅ | - |
| 3 | ds_kpi_documented | KPI: Documented | ✅ | - |
| 4 | ds_kpi_lineage | KPI: Lineage | ✅ | - |
| 5 | ds_kpi_jobs | KPI: Jobs | ✅ | param_catalog |
| 6 | ds_kpi_workspaces | KPI: Workspaces | ✅ | param_catalog |
| 7 | ds_tables_by_catalog | Tables by Catalog | ✅ | param_catalog |
| 8 | ds_lineage_trend | Lineage Trend | ✅ | time_range, param_catalog |
| 9 | ds_untagged_tables | Untagged Tables | ✅ | param_catalog, catalog, gold_schema |
| 10 | ds_undocumented_tables | Undocumented Tables | ✅ | param_catalog, catalog, gold_schema |
| 11 | ds_quality_distribution | Quality Distribution | ✅ | - |
| 12 | ds_lineage_sources | Lineage Sources | ✅ | param_catalog |
| 13 | ds_lineage_sinks | Lineage Sinks | ✅ | param_catalog |
| 14 | ds_stale_lineage | Stale Lineage | ✅ | time_range, param_catalog |
| 15 | ds_catalog_summary | Catalog Summary | ✅ | param_catalog |
| 16 | ds_schema_summary | Schema Summary | ✅ | time_range, param_catalog |
| 17 | ds_summary | Summary | ✅ | param_catalog |
| 18 | ds_optimization_needed | Optimization Needed | ✅ | param_catalog |
| 19 | ds_size_buckets | Size Buckets | ✅ | param_catalog |
| 20 | ds_file_buckets | File Buckets | ✅ | param_catalog |
| 21 | ds_largest_tables | Largest Tables | ✅ | param_catalog |
| 22 | ds_needs_compaction | Needs Compaction | ✅ | param_catalog |
| 23 | ds_empty_tables | Empty Tables | ✅ | param_catalog |
| 24 | ds_time_windows | Time Windows | ✅ | - |
| 25 | ds_monitor_gov_latest | Monitor: Governance Latest | ✅ | - |
| 26 | ds_monitor_gov_trend | Monitor: Governance Trend | ✅ | - |
| 27 | ds_monitor_gov_drift | Monitor: Governance Drift | ✅ | - |
| 28 | ds_monitor_gov_detailed | Monitor: Governance Detailed | ✅ | - |
| 29 | ds_workspaces | Workspaces | ✅ | param_catalog |
| 30 | select_workspace | select_workspace | ✅ | param_catalog |
| 31 | select_time_key | select_time_key | ✅ | - |
| 32 | ds_select_catalog | ds_select_catalog | ✅ | - |

---

## Complete SQL Queries


### Dataset 1: ds_kpi_tables

**Display Name:** KPI: Tables  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT FORMAT_NUMBER(COUNT(DISTINCT target_table_full_name), 0) AS total_tables FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE 1=1
```

---

### Dataset 2: ds_kpi_tagged

**Display Name:** KPI: Tagged  
**SQL Query:**
```sql
SELECT '75%' AS tagged_pct
```

---

### Dataset 3: ds_kpi_documented

**Display Name:** KPI: Documented  
**SQL Query:**
```sql
SELECT '60%' AS documented_pct
```

---

### Dataset 4: ds_kpi_lineage

**Display Name:** KPI: Lineage  
**SQL Query:**
```sql
SELECT '85%' AS lineage_pct
```

---

### Dataset 5: ds_kpi_jobs

**Display Name:** KPI: Jobs  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT FORMAT_NUMBER(COUNT(DISTINCT job_id), 0) AS total_jobs FROM ${catalog}.${gold_schema}.dim_job
```

---

### Dataset 6: ds_kpi_workspaces

**Display Name:** KPI: Workspaces  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT FORMAT_NUMBER(COUNT(DISTINCT workspace_id), 0) AS total_workspaces FROM ${catalog}.${gold_schema}.dim_workspace
```

---

### Dataset 7: ds_tables_by_catalog

**Display Name:** Tables by Catalog  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
-- Tables by catalog from system tables
SELECT 
  table_catalog AS catalog_name,
  COUNT(*) AS table_count
FROM system.information_schema.tables
WHERE table_catalog IS NOT NULL
  AND table_catalog NOT IN ('system', 'information_schema', 'hive_metastore', '__databricks_internal', 'samples')
  AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, table_catalog))
GROUP BY table_catalog
ORDER BY table_count DESC
LIMIT 10
```

---

### Dataset 8: ds_lineage_trend

**Display Name:** Lineage Trend  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT DATE(event_time) AS day, COUNT(*) AS lineage_events FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE 1=1  AND  event_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 9: ds_untagged_tables

**Display Name:** Untagged Tables  
**Parameters:**
- `param_catalog` (STRING) - param_catalog
- `catalog` (STRING) - catalog
- `gold_schema` (STRING) - gold_schema

**SQL Query:**
```sql
-- Tables without governance tags (prioritized by usage)
WITH untagged AS (
  SELECT
    t.table_catalog AS catalog_name,
    t.table_schema AS schema_name,
    t.table_name,
    t.table_type,
    t.table_owner,
    'No Tags' AS tag_status
  FROM system.information_schema.tables t
  LEFT JOIN system.information_schema.table_tags tt
    ON t.table_catalog = tt.catalog_name
    AND t.table_schema = tt.schema_name
    AND t.table_name = tt.table_name
  WHERE t.table_catalog NOT IN ('system', '__databricks_internal', 'samples', 'hive_metastore')
    AND t.table_schema NOT IN ('information_schema', 'default', '__databricks_internal')
    AND t.table_type IN ('MANAGED', 'EXTERNAL', 'VIEW')
    AND tt.tag_name IS NULL
    AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, t.table_catalog))
),
usage_stats AS (
  SELECT
    CONCAT(catalog, '.', schema, '.', table_name) AS full_table_name,
    COUNT(*) AS query_count,
    COUNT(DISTINCT DATE(start_time)) AS days_accessed
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 90 DAYS
    AND catalog IS NOT NULL
    AND schema IS NOT NULL
    AND table_name IS NOT NULL
  GROUP BY 1
)
SELECT
  u.catalog_name,
  u.schema_name,
  u.table_name,
  u.table_type,
  u.table_owner,
  COALESCE(s.query_count, 0) AS query_count,
  COALESCE(s.days_accessed, 0) AS days_accessed,
  u.tag_status
FROM untagged u
LEFT JOIN usage_stats s ON CONCAT(u.catalog_name, '.', u.schema_name, '.', u.table_name) = s.full_table_name
ORDER BY query_count DESC NULLS LAST, days_accessed DESC NULLS LAST
LIMIT 50
```

---

### Dataset 10: ds_undocumented_tables

**Display Name:** Undocumented Tables  
**Parameters:**
- `param_catalog` (STRING) - param_catalog
- `catalog` (STRING) - catalog
- `gold_schema` (STRING) - gold_schema

**SQL Query:**
```sql
-- Tables with missing documentation (table or column descriptions) prioritized by usage
WITH table_docs AS (
  SELECT
    t.table_catalog,
    t.table_schema,
    t.table_name,
    t.table_type,
    t.table_owner,
    CASE
      WHEN t.comment IS NULL OR TRIM(t.comment) = '' THEN 1
      ELSE 0
    END AS missing_table_comment
  FROM system.information_schema.tables t
  WHERE t.table_type IN ('MANAGED', 'EXTERNAL', 'VIEW')
    AND t.table_catalog NOT IN ('system', '__databricks_internal', 'samples', 'hive_metastore')
    AND t.table_schema NOT IN ('information_schema', 'default', '__databricks_internal')
    AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, t.table_catalog))
),
column_docs AS (
  SELECT
    table_catalog,
    table_schema,
    table_name,
    COUNT(*) AS total_columns,
    SUM(CASE WHEN comment IS NULL OR TRIM(comment) = '' THEN 1 ELSE 0 END) AS missing_column_comments
  FROM system.information_schema.columns
  WHERE table_catalog NOT IN ('system', '__databricks_internal', 'samples', 'hive_metastore')
    AND table_schema NOT IN ('information_schema', 'default', '__databricks_internal')
  GROUP BY 1, 2, 3
),
usage_stats AS (
  SELECT
    CONCAT(catalog, '.', schema, '.', table_name) AS full_table_name,
    COUNT(*) AS query_count,
    COUNT(DISTINCT DATE(start_time)) AS days_accessed
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 90 DAYS
    AND catalog IS NOT NULL
    AND schema IS NOT NULL
    AND table_name IS NOT NULL
  GROUP BY 1
)
SELECT
  td.table_catalog AS catalog_name,
  td.table_schema AS schema_name,
  td.table_name,
  td.table_type,
  td.table_owner,
  COALESCE(s.query_count, 0) AS query_count,
  COALESCE(s.days_accessed, 0) AS days_accessed,
  CASE
    WHEN td.missing_table_comment = 1 AND COALESCE(cd.missing_column_comments, 0) > 0 THEN 'Missing Table & Column Descriptions'
    WHEN td.missing_table_comment = 1 THEN 'Missing Table Description'
    WHEN COALESCE(cd.missing_column_comments, 0) > 0 THEN CONCAT('Missing ', cd.missing_column_comments, ' of ', cd.total_columns, ' Column Descriptions')
    ELSE 'OK'
  END AS doc_status
FROM table_docs td
LEFT JOIN column_docs cd
  ON td.table_catalog = cd.table_catalog
  AND td.table_schema = cd.table_schema
  AND td.table_name = cd.table_name
LEFT JOIN usage_stats s
  ON CONCAT(td.table_catalog, '.', td.table_schema, '.', td.table_name) = s.full_table_name
WHERE td.missing_table_comment = 1 OR COALESCE(cd.missing_column_comments, 0) > 0
ORDER BY query_count DESC NULLS LAST, days_accessed DESC NULLS LAST
LIMIT 50
```

---

### Dataset 11: ds_quality_distribution

**Display Name:** Quality Distribution  
**SQL Query:**
```sql
SELECT 'Gold' AS quality_tier, 100 AS table_count UNION ALL SELECT 'Silver' AS quality_tier, 200 AS table_count UNION ALL SELECT 'Bronze' AS quality_tier, 150 AS table_count
```

---

### Dataset 12: ds_lineage_sources

**Display Name:** Lineage Sources  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT source_table_full_name AS source_table, COUNT(DISTINCT target_table_full_name) AS downstream_count FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE 1=1 GROUP BY 1 ORDER BY 2 DESC LIMIT 15
```

---

### Dataset 13: ds_lineage_sinks

**Display Name:** Lineage Sinks  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT target_table_full_name AS target_table, COUNT(DISTINCT source_table_full_name) AS upstream_count FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE 1=1 GROUP BY 1 ORDER BY 2 DESC LIMIT 15
```

---

### Dataset 14: ds_stale_lineage

**Display Name:** Stale Lineage  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT target_table_full_name AS table_name, MAX(event_time) AS last_update, DATEDIFF(CURRENT_DATE(), DATE(MAX(event_time))) AS days_stale FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE 1=1 GROUP BY 1 HAVING DATEDIFF(CURRENT_DATE(), DATE(MAX(event_time))) > 7 ORDER BY days_stale DESC LIMIT 20
```

---

### Dataset 15: ds_catalog_summary

**Display Name:** Catalog Summary  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
-- Catalog summary from system tables
SELECT 
  table_catalog AS catalog_name,
  COUNT(*) AS table_count
FROM system.information_schema.tables
WHERE table_catalog IS NOT NULL
  AND table_catalog NOT IN ('system', 'information_schema', 'hive_metastore', '__databricks_internal', 'samples')
  AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, table_catalog))
GROUP BY table_catalog
ORDER BY table_count DESC
LIMIT 15
```

---

### Dataset 16: ds_schema_summary

**Display Name:** Schema Summary  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
-- Schema summary from system tables
SELECT 
  table_catalog AS catalog_name,
  table_schema AS schema_name,
  COUNT(*) AS table_count,
  MAX(last_altered) AS last_modified
FROM system.information_schema.tables
WHERE table_catalog IS NOT NULL
  AND table_schema IS NOT NULL
  AND table_catalog NOT IN ('system', 'information_schema', 'hive_metastore', '__databricks_internal', 'samples')
  AND table_schema NOT IN ('information_schema', 'default', '__databricks_internal')
  AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, table_catalog))
GROUP BY table_catalog, table_schema
ORDER BY table_count DESC
LIMIT 20
```

---

### Dataset 17: ds_summary

**Display Name:** Summary  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT COUNT(DISTINCT table_name) AS table_count, COUNT(*) AS total_operations, ROUND(SUM(COALESCE(usage_quantity, 0)), 2) AS total_size_gb, COUNT(DISTINCT CASE WHEN operation_type = 'COMPACTION' THEN table_id END) AS optimized_tables FROM ${catalog}.${gold_schema}.fact_predictive_optimization WHERE operation_status = 'SUCCESSFUL'
```

---

### Dataset 18: ds_optimization_needed

**Display Name:** Optimization Needed  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
WITH recent_optimizations AS (SELECT DISTINCT table_id FROM ${catalog}.${gold_schema}.fact_predictive_optimization WHERE operation_type = 'COMPACTION' AND start_time >= CURRENT_DATE() - INTERVAL 30 DAYS), all_tables AS (SELECT DISTINCT COALESCE(source_table_full_name, target_table_full_name) AS table_name FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE event_date >= CURRENT_DATE() - INTERVAL 90 DAYS) SELECT COUNT(*) AS count FROM all_tables WHERE table_name NOT IN (SELECT table_id FROM recent_optimizations WHERE table_id IS NOT NULL)
```

---

### Dataset 19: ds_size_buckets

**Display Name:** Size Buckets  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT CASE WHEN total_usage < 1 THEN '< 1 GB' WHEN total_usage < 10 THEN '1-10 GB' WHEN total_usage < 100 THEN '10-100 GB' WHEN total_usage < 1000 THEN '100 GB - 1 TB' ELSE '> 1 TB' END AS size_bucket, COUNT(*) AS table_count FROM (SELECT table_name, SUM(COALESCE(usage_quantity, 0)) AS total_usage FROM ${catalog}.${gold_schema}.fact_predictive_optimization WHERE operation_status = 'SUCCESSFUL' GROUP BY table_name) GROUP BY 1 ORDER BY CASE WHEN size_bucket = '< 1 GB' THEN 1 WHEN size_bucket = '1-10 GB' THEN 2 WHEN size_bucket = '10-100 GB' THEN 3 WHEN size_bucket = '100 GB - 1 TB' THEN 4 ELSE 5 END
```

---

### Dataset 20: ds_file_buckets

**Display Name:** File Buckets  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT operation_type AS file_bucket, COUNT(*) AS table_count FROM ${catalog}.${gold_schema}.fact_predictive_optimization WHERE operation_status = 'SUCCESSFUL' GROUP BY operation_type ORDER BY table_count DESC
```

---

### Dataset 21: ds_largest_tables

**Display Name:** Largest Tables  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
-- Largest tables by row count (size not available in info schema)
SELECT 
  table_name,
  table_schema AS schema_name,
  table_catalog AS catalog_name,
  table_type,
  created AS created_at,
  last_altered
FROM system.information_schema.tables
WHERE table_catalog NOT IN ('system', 'information_schema', 'hive_metastore', '__databricks_internal', 'samples')
  AND table_type IN ('MANAGED', 'EXTERNAL')
  AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, table_catalog))
ORDER BY last_altered DESC NULLS LAST
LIMIT 20
```

---

### Dataset 22: ds_needs_compaction

**Display Name:** Needs Compaction  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
-- Tables needing optimization (based on age and activity)
SELECT 
  table_name,
  table_schema AS schema_name,
  table_catalog AS catalog_name,
  table_type,
  created,
  last_altered,
  CASE 
    WHEN DATEDIFF(CURRENT_DATE(), last_altered) > 365 THEN 'STALE: Not modified in 1+ years'
    WHEN DATEDIFF(CURRENT_DATE(), last_altered) > 180 THEN 'WARNING: Not modified in 6+ months'
    WHEN DATEDIFF(CURRENT_DATE(), last_altered) > 90 THEN 'MONITOR: Not modified in 3+ months'
    ELSE 'OK: Recently modified'
  END AS optimization_status
FROM system.information_schema.tables
WHERE table_catalog NOT IN ('system', 'information_schema', 'hive_metastore', '__databricks_internal', 'samples')
  AND table_type IN ('MANAGED', 'EXTERNAL')
  AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, table_catalog))
ORDER BY last_altered ASC NULLS FIRST
LIMIT 20
```

---

### Dataset 23: ds_empty_tables

**Display Name:** Empty Tables  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
-- Recently created tables (potential empty candidates)
SELECT 
  table_name,
  table_schema AS schema_name,
  table_catalog AS catalog_name,
  table_type,
  created AS created_at,
  last_altered
FROM system.information_schema.tables
WHERE table_type IN ('MANAGED', 'EXTERNAL')
  AND table_catalog NOT IN ('system', 'information_schema', 'hive_metastore', '__databricks_internal', 'samples')
  AND (ARRAY_CONTAINS(:param_catalog, 'all') OR ARRAY_CONTAINS(:param_catalog, table_catalog))
  AND created >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY created DESC
LIMIT 20
```

---

### Dataset 24: ds_time_windows

**Display Name:** Time Windows  
**SQL Query:**
```sql
SELECT 'Last 7 Days' AS time_window UNION ALL SELECT 'Last 30 Days' UNION ALL SELECT 'Last 90 Days' UNION ALL SELECT 'Last 6 Months' UNION ALL SELECT 'Last Year' UNION ALL SELECT 'All Time'
```

---

### Dataset 25: ds_monitor_gov_latest

**Display Name:** Monitor: Governance Latest  
**SQL Query:**
```sql
SELECT 
  COALESCE(total_lineage_events, 0) AS total_events,
  COALESCE(active_tables_count, 0) AS active_tables,
  COALESCE(distinct_users, 0) AS distinct_users,
  COALESCE(read_event_count, 0) AS read_events,
  COALESCE(write_event_count, 0) AS write_events
FROM ${catalog}.${gold_schema}_monitoring.fact_table_lineage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY window.start DESC
LIMIT 1
```

---

### Dataset 26: ds_monitor_gov_trend

**Display Name:** Monitor: Governance Trend  
**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  COALESCE(total_lineage_events, 0) AS total_events,
  COALESCE(active_tables_count, 0) AS active_tables,
  COALESCE(distinct_users, 0) AS distinct_users
FROM ${catalog}.${gold_schema}_monitoring.fact_table_lineage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY window_start
```

---

### Dataset 27: ds_monitor_gov_drift

**Display Name:** Monitor: Governance Drift  
**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  COALESCE(lineage_volume_drift_pct, 0) AS event_drift,
  COALESCE(user_count_drift, 0) AS user_drift,
  COALESCE(active_tables_drift, 0) AS table_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_table_lineage_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
  AND slice_key IS NULL
  AND window.start >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY window_start
```

---

### Dataset 28: ds_monitor_gov_detailed

**Display Name:** Monitor: Governance Detailed  
**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  COALESCE(total_lineage_events, 0) AS total_events,
  COALESCE(active_tables_count, 0) AS active_tables,
  COALESCE(distinct_users, 0) AS distinct_users,
  COALESCE(read_event_count, 0) AS read_events,
  COALESCE(write_event_count, 0) AS write_events,
  COALESCE(read_write_ratio, 0) AS read_write_ratio
FROM ${catalog}.${gold_schema}_monitoring.fact_table_lineage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY window_start DESC
LIMIT 30
```

---

### Dataset 29: ds_workspaces

**Display Name:** Workspaces  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name
```

---

### Dataset 30: select_workspace

**Display Name:** select_workspace  
**Parameters:**
- `param_catalog` (STRING) - param_catalog

**SQL Query:**
```sql
SELECT DISTINCT 
  COALESCE(workspace_name, CONCAT('id: ', workspace_id)) AS workspace_name
FROM ${catalog}.${gold_schema}.dim_workspace 
WHERE workspace_name IS NOT NULL 
ORDER BY workspace_name
```

---

### Dataset 31: select_time_key

**Display Name:** select_time_key  
**SQL Query:**
```sql
SELECT explode(array(
  'Day',
  'Week',
  'Month',
  'Quarter',
  'Year'
)) AS time_key
```

---

### Dataset 32: ds_select_catalog

**Display Name:** ds_select_catalog  
**SQL Query:**
```sql
SELECT 'all' AS catalog_name UNION ALL SELECT DISTINCT table_catalog AS catalog_name FROM system.information_schema.tables WHERE table_catalog NOT IN ('system', 'information_schema', 'hive_metastore', '__databricks_internal', 'samples') ORDER BY 1
```

---
