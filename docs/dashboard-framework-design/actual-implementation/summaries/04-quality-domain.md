# Quality Domain - Actual Implementation

## Overview

**Dashboard:** `quality.lvdash.json`  
**Total Datasets:** 32  
**Primary Tables:**
- `system.information_schema.tables` (table metadata)
- `system.information_schema.columns` (column metadata)
- `system.information_schema.table_tags` (governance tags)
- `fact_table_lineage` (table dependencies)
- `fact_query_history` (usage patterns)

---

## 📊 Key Metrics

### Governance Metrics
- **Total Tables**: Count of all tables by catalog
- **Tagged Tables %**: Percentage of tables with governance tags
- **Documented Tables %**: Tables with table and column descriptions
- **Quality Score**: Overall data quality percentage

### Usage Metrics
- **Query Count**: Number of queries accessing table
- **Days Accessed**: Days table was accessed in last 90 days
- **Active Tables**: Tables accessed in last 30 days
- **Stale Tables**: Tables not accessed >90 days

### Lineage Metrics
- **Upstream Dependencies**: Tables this table depends on
- **Downstream Dependencies**: Tables depending on this table
- **Lineage Depth**: Maximum dependency chain length

---

## 🔑 Key Datasets

### ds_untagged_tables
**Purpose:** Tables without governance tags, prioritized by usage  
**Source:** `system.information_schema.tables` + `fact_query_history`  
**Key Query:**
```sql
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
  WHERE t.table_catalog NOT IN ('system', '__databricks_internal', 'samples')
    AND t.table_schema NOT IN ('information_schema', 'default')
    AND t.table_type IN ('MANAGED', 'EXTERNAL', 'VIEW')
    AND tt.tag_name IS NULL
),
usage_stats AS (
  SELECT
    CONCAT(catalog, '.', schema, '.', table_name) AS full_table_name,
    COUNT(*) AS query_count,
    COUNT(DISTINCT DATE(start_time)) AS days_accessed
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 90 DAYS
    AND catalog IS NOT NULL
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
LEFT JOIN usage_stats s
  ON CONCAT(u.catalog_name, '.', u.schema_name, '.', u.table_name) = s.full_table_name
ORDER BY query_count DESC NULLS LAST, days_accessed DESC NULLS LAST
LIMIT 50
```

### ds_undocumented_tables
**Purpose:** Tables with missing documentation  
**Source:** `system.information_schema.tables`, `system.information_schema.columns`, `fact_query_history`  
**Documentation Status:**
- **Missing Table & Column Descriptions**: No table comment AND missing column comments
- **Missing Table Description**: No table comment
- **Missing N of M Column Descriptions**: Some columns without comments

**Key Query:**
```sql
WITH table_docs AS (
  SELECT
    table_catalog,
    table_schema,
    table_name,
    table_type,
    table_owner,
    CASE
      WHEN comment IS NULL OR TRIM(comment) = '' THEN 1
      ELSE 0
    END AS missing_table_comment
  FROM system.information_schema.tables
  WHERE table_type IN ('MANAGED', 'EXTERNAL', 'VIEW')
),
column_docs AS (
  SELECT
    table_catalog,
    table_schema,
    table_name,
    COUNT(*) AS total_columns,
    SUM(CASE WHEN comment IS NULL OR TRIM(comment) = '' THEN 1 ELSE 0 END) AS missing_column_comments
  FROM system.information_schema.columns
  GROUP BY 1, 2, 3
)
SELECT
  td.table_catalog AS catalog_name,
  td.table_schema AS schema_name,
  td.table_name,
  td.table_type,
  td.table_owner,
  CASE
    WHEN td.missing_table_comment = 1 AND COALESCE(cd.missing_column_comments, 0) > 0 
      THEN 'Missing Table & Column Descriptions'
    WHEN td.missing_table_comment = 1 
      THEN 'Missing Table Description'
    WHEN COALESCE(cd.missing_column_comments, 0) > 0 
      THEN CONCAT('Missing ', cd.missing_column_comments, ' of ', cd.total_columns, ' Column Descriptions')
    ELSE 'OK'
  END AS doc_status
FROM table_docs td
LEFT JOIN column_docs cd
  ON td.table_catalog = cd.table_catalog
  AND td.table_schema = cd.table_schema
  AND td.table_name = cd.table_name
WHERE td.missing_table_comment = 1 OR COALESCE(cd.missing_column_comments, 0) > 0
LIMIT 50
```

### ds_tables_by_catalog
**Purpose:** Table distribution by catalog and schema  
**Source:** `system.information_schema.tables`  
**Key Query:**
```sql
SELECT 
  table_catalog,
  table_schema,
  COUNT(*) AS table_count,
  SUM(CASE WHEN table_type = 'MANAGED' THEN 1 ELSE 0 END) AS managed_count,
  SUM(CASE WHEN table_type = 'EXTERNAL' THEN 1 ELSE 0 END) AS external_count,
  SUM(CASE WHEN table_type = 'VIEW' THEN 1 ELSE 0 END) AS view_count
FROM system.information_schema.tables
WHERE table_catalog NOT IN ('system', '__databricks_internal', 'samples')
  AND table_schema NOT IN ('information_schema', 'default')
GROUP BY table_catalog, table_schema
ORDER BY table_count DESC
```

### ds_lineage_sources
**Purpose:** Tables with most downstream dependencies  
**Source:** `fact_table_lineage`  
**Key Query:**
```sql
SELECT 
  source_table_full_name AS source_table,
  COUNT(DISTINCT target_table_full_name) AS downstream_count
FROM ${catalog}.${gold_schema}.fact_table_lineage
GROUP BY source_table_full_name
ORDER BY downstream_count DESC
LIMIT 15
```

---

## 📑 Data Sources

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `system.information_schema.tables` | table_catalog, table_schema, table_name, comment, table_owner | Table metadata |
| `system.information_schema.columns` | table_name, column_name, comment | Column documentation |
| `system.information_schema.table_tags` | tag_name, tag_value | Governance tags |
| `fact_table_lineage` | source_table_full_name, target_table_full_name | Dependencies |
| `fact_query_history` | catalog, schema, table_name | Usage patterns |

---

## 🔍 Common Query Patterns

### Multi-Select Catalog Filter
```sql
WHERE (ARRAY_CONTAINS(:param_catalog, 'all') 
   OR ARRAY_CONTAINS(:param_catalog, table_catalog))
```

### Tag Existence Check
```sql
LEFT JOIN system.information_schema.table_tags tt
  ON t.table_catalog = tt.catalog_name
  AND t.table_schema = tt.schema_name
  AND t.table_name = tt.table_name
WHERE tt.tag_name IS NULL  -- No tags
```

### Documentation Status
```sql
CASE
  WHEN comment IS NULL OR TRIM(comment) = '' THEN 'Missing'
  ELSE 'Documented'
END AS doc_status
```

### Usage-Based Prioritization
```sql
-- Prioritize by recent usage
ORDER BY query_count DESC NULLS LAST, 
         days_accessed DESC NULLS LAST
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial documentation |

