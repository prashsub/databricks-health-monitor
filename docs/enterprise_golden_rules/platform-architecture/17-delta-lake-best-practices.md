# Delta Lake Best Practices

> **Document Owner:** Platform Team | **Status:** Approved | **Last Updated:** February 2026

## Overview

Delta Lake is the mandatory storage format for all tables on the Databricks platform. This document defines the required patterns for table management, performance optimization, and operational best practices.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **DL-01** | Use Unity Catalog managed tables | Critical |
| **DL-02** | Enable predictive optimization | Critical |
| **DL-03** | Use automatic liquid clustering (CLUSTER BY AUTO) | Critical |
| **DL-04** | Never use Spark caching with Delta tables | Required |
| **DL-05** | Never manually modify Delta data files | Critical |
| **DL-06** | Remove legacy Delta configurations on upgrade | Recommended |

---

## DL-01: Managed Tables

### Rule
All tables must be Unity Catalog managed tables using Delta Lake format. External tables require documented justification and approval.

### Why It Matters
| Managed Tables | External Tables |
|----------------|-----------------|
| Full UC governance | Limited governance |
| Auto compaction | Manual maintenance |
| Auto optimize | Manual tuning |
| Metadata caching | No caching |

### Implementation
```sql
-- Correct: Managed table
CREATE TABLE catalog.schema.my_table (
    id BIGINT,
    name STRING
)
USING DELTA
CLUSTER BY AUTO;

-- Avoid: External table
-- CREATE TABLE my_table USING DELTA LOCATION 's3://...';
```

---

## DL-02: Predictive Optimization

### Rule
Enable predictive optimization at the schema or catalog level for all production schemas.

### Why It Matters
- Automatically runs OPTIMIZE and VACUUM
- Self-tuning based on usage patterns
- Zero configuration maintenance
- Background execution with no manual scheduling

### Implementation
```sql
-- Enable at schema level (recommended)
ALTER SCHEMA catalog.gold ENABLE PREDICTIVE OPTIMIZATION;

-- Enable at catalog level (broader scope)
ALTER CATALOG my_catalog ENABLE PREDICTIVE OPTIMIZATION;

-- Verify status
DESCRIBE SCHEMA EXTENDED catalog.gold;
```

### Removes Need For
- Manual OPTIMIZE jobs
- Manual VACUUM scheduling
- File size tuning configurations

---

## DL-03: Automatic Liquid Clustering

### Rule
All tables must use `CLUSTER BY AUTO`. Never specify clustering columns manually.

### Why It Matters
- Automatic column selection based on query patterns
- Self-tuning as workloads evolve
- Incremental clustering (not full table rewrites)
- Works with all data types

### Implementation
```sql
-- Correct: Automatic clustering
CREATE TABLE catalog.schema.fact_sales (...)
CLUSTER BY AUTO;

-- Correct: Enable on existing table
ALTER TABLE catalog.schema.fact_sales CLUSTER BY AUTO;

-- Wrong: Manual column specification
-- CLUSTER BY (sale_date, region)

-- Wrong: Legacy Z-ORDER
-- OPTIMIZE table ZORDER BY (column);
```

---

## DL-04: No Spark Caching

### Rule
Never use `.cache()` or `.persist()` on Delta tables.

### Why It Matters
- Caching bypasses Delta's data skipping
- Cached data may become stale after updates
- Consumes executor memory unnecessarily
- Delta automatically optimizes repeated reads

### Anti-Pattern
```python
# ❌ Wrong: Caching Delta table
df = spark.table("catalog.schema.my_table")
df.cache()  # Loses data skipping!
df.filter("date = '2025-01-01'").count()
```

### Correct Pattern
```python
# ✅ Correct: Let Delta handle optimization
df = spark.table("catalog.schema.my_table")
df.filter("date = '2025-01-01'").count()  # Uses data skipping
```

---

## DL-05: No Manual File Modifications

### Rule
Never directly modify, add, or delete Parquet files in a Delta table location.

### Why It Matters
- Delta uses transaction log for atomic commits
- Manual changes bypass the log, causing inconsistency
- Results in lost data, duplicates, or corruption
- Queries may fail with missing file errors

### Prohibited Operations
```bash
# ❌ Never do this
aws s3 rm s3://bucket/delta-table/part-00001.parquet
aws s3 cp data.parquet s3://bucket/delta-table/
```

### Correct Operations
```sql
-- ✅ Use Delta operations
DELETE FROM table WHERE condition;
INSERT INTO table SELECT ...;
UPDATE table SET column = value WHERE condition;
VACUUM table RETAIN 168 HOURS;
```

---

## DL-06: Remove Legacy Configurations

### Rule
Remove explicit legacy Delta configurations when upgrading Databricks Runtime. Let the platform use optimized defaults.

### Why It Matters
- Legacy settings may block new optimizations
- Predictive optimization handles most tuning
- Reduces configuration maintenance

### Configurations to Review

| Configuration | Action |
|---------------|--------|
| `delta.autoOptimize.optimizeWrite` | Remove if predictive optimization enabled |
| `delta.autoOptimize.autoCompact` | Remove if predictive optimization enabled |
| `spark.sql.shuffle.partitions` | Let AQE auto-tune |
| `delta.targetFileSize` | Remove (automatic tuning) |

### Migration
```sql
-- Check current properties
SHOW TBLPROPERTIES catalog.schema.my_table;

-- Remove legacy properties
ALTER TABLE catalog.schema.my_table 
UNSET TBLPROPERTIES ('delta.targetFileSize');
```

---

## Operations You Don't Need

Delta handles these automatically—do not run them manually:

| Operation | Why Not Needed |
|-----------|----------------|
| `REFRESH TABLE` | Delta always returns current data |
| `ALTER TABLE ADD PARTITION` | Partitions tracked automatically |
| `MSCK REPAIR TABLE` | Not applicable to Delta |
| Direct partition reads | Use WHERE clause instead |

---

## MERGE Performance Tips

### Reduce Search Space
```sql
-- ✅ Faster: Constrained MERGE
MERGE INTO events AS target
USING updates AS source
ON target.id = source.id
   AND target.event_date = current_date()  -- Partition filter
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

-- ❌ Slower: Full table scan
MERGE INTO events AS target
USING updates AS source
ON target.id = source.id  -- Scans entire table
...
```

---

## Validation Checklist

- [ ] All tables are Unity Catalog managed
- [ ] Predictive optimization enabled at schema/catalog level
- [ ] All tables use CLUSTER BY AUTO
- [ ] No .cache() or .persist() on Delta tables in code
- [ ] No direct file system operations on Delta paths
- [ ] Legacy configurations removed after runtime upgrades
- [ ] MERGE operations include partition filters where possible

---

## Quick Reference

```sql
-- Enable predictive optimization
ALTER SCHEMA catalog.schema ENABLE PREDICTIVE OPTIMIZATION;

-- Create table with auto clustering
CREATE TABLE catalog.schema.my_table (...)
USING DELTA CLUSTER BY AUTO;

-- Enable on existing table
ALTER TABLE catalog.schema.my_table CLUSTER BY AUTO;

-- Remove legacy config
ALTER TABLE catalog.schema.my_table 
UNSET TBLPROPERTIES ('legacy.config');
```

---

## References

- [Delta Lake Best Practices](https://docs.databricks.com/en/delta/best-practices.html)
- [Liquid Clustering](https://docs.databricks.com/en/delta/clustering.html)
- [Predictive Optimization](https://docs.databricks.com/en/optimizations/predictive-optimization.html)
