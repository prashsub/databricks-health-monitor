# Delta Lake Best Practices

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-DP-004 |
| **Version** | 1.0 |
| **Last Updated** | February 2026 |
| **Owner** | Data Engineering Team |
| **Status** | Approved |

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 2026 | Initial compilation from official Databricks documentation |

### Source References
| Source | URL |
|--------|-----|
| Delta Lake Best Practices | https://docs.databricks.com/en/delta/best-practices.html |
| Liquid Clustering | https://docs.databricks.com/en/delta/clustering.html |
| Predictive Optimization | https://docs.databricks.com/en/optimizations/predictive-optimization.html |

---

## Executive Summary

This document consolidates official Delta Lake best practices from Databricks documentation. These patterns cover table management, performance optimization, clustering, caching guidelines, and MERGE optimization.

> **Key Principle:** Delta Lake provides ACID transactions, scalable metadata handling, and unifies streaming and batch data processing. Follow these patterns to maximize performance and reliability.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| BP-01 | Use Unity Catalog managed tables | 🔴 Critical |
| BP-02 | Enable predictive optimization | 🔴 Critical |
| BP-03 | Use liquid clustering (CLUSTER BY AUTO) | 🔴 Critical |
| BP-06 | Do not use Spark caching with Delta Lake | 🟡 Required |
| BP-07 | Never manually modify Delta data files | 🔴 Critical |
| BP-10 | Remove legacy Delta configurations on upgrade | 🟢 Recommended |

---

## BP-01: Use Unity Catalog Managed Tables (Critical)

> **Official Recommendation:** "Use Unity Catalog managed tables... Databricks recommends managed tables and volumes because they allow you to take full advantage of Unity Catalog governance capabilities and performance optimizations." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Why Managed Tables

| Benefit | Description |
|---------|-------------|
| **Governance** | Full lineage, audit, access control |
| **Auto compaction** | Automatic OPTIMIZE runs |
| **Auto optimize** | Intelligent file sizing |
| **Metadata caching** | Faster metadata reads |
| **File optimization** | Intelligent file size tuning |

### Implementation

```sql
-- ✅ CORRECT: Managed table in Unity Catalog
CREATE TABLE catalog.schema.my_table (
    id BIGINT,
    name STRING,
    created_at TIMESTAMP
)
USING DELTA
CLUSTER BY AUTO
COMMENT 'Managed table with full UC governance';

-- ❌ WRONG: External table without UC management
CREATE TABLE my_table
USING DELTA
LOCATION 's3://bucket/path/my_table';
```

### When to Use External Tables

| Scenario | Recommendation |
|----------|----------------|
| Migrating from Hive metastore | External (temporary) |
| Disaster recovery requirements | External (if managed can't meet DR) |
| External readers/writers required | External (sparingly) |
| Non-Delta/non-Iceberg formats | External (required) |

> **Migration Path:** Databricks recommends eventually migrating external tables to managed tables for full governance benefits.

---

## BP-02: Enable Predictive Optimization (Critical)

> **Official Recommendation:** "Use predictive optimization. Predictive optimization automatically runs OPTIMIZE and VACUUM commands on Unity Catalog managed tables." — [Databricks Docs](https://docs.databricks.com/en/delta/best-practices.html)

### What Predictive Optimization Does

```
┌─────────────────────────────────────────────────────────────┐
│                 PREDICTIVE OPTIMIZATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Automatic OPTIMIZE                Automatic VACUUM        │
│   ├── File compaction               ├── Old file cleanup    │
│   ├── Small file merging            ├── Transaction log     │
│   └── Based on usage patterns       └── Based on retention  │
│                                                             │
│   Self-Tuning                       Zero Configuration      │
│   ├── Learns query patterns         ├── No manual jobs      │
│   └── Adapts over time              └── Background runs     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```sql
-- Enable at schema level (recommended)
ALTER SCHEMA catalog.gold_schema 
ENABLE PREDICTIVE OPTIMIZATION;

-- Enable at catalog level (broader scope)
ALTER CATALOG my_catalog 
ENABLE PREDICTIVE OPTIMIZATION;

-- Verify status
DESCRIBE SCHEMA EXTENDED catalog.gold_schema;

-- Check optimization history
SELECT * FROM system.storage.predictive_optimization_operations
WHERE catalog_name = 'my_catalog'
ORDER BY timestamp DESC;
```

### Predictive Optimization vs Manual OPTIMIZE

| Aspect | Predictive | Manual |
|--------|------------|--------|
| Configuration | Zero | Requires scheduling |
| Timing | Automatic | Fixed schedule |
| Adaptation | Learns patterns | Static |
| Coverage | All managed tables | Specified tables only |
| Overhead | None | Job maintenance |

---

## BP-03: Use Liquid Clustering (Critical)

> **Official Recommendation:** "Use liquid clustering." — [Databricks Docs](https://docs.databricks.com/en/delta/best-practices.html)

### Liquid Clustering vs Z-ORDER

| Feature | Liquid Clustering | Z-ORDER (Legacy) |
|---------|-------------------|------------------|
| Configuration | `CLUSTER BY AUTO` | Manual columns |
| Adaptation | Self-tuning | Static |
| Column selection | Automatic | Manual |
| Incremental | Yes | Full rewrite |
| Data types | All supported | Some limitations |

### Implementation

```sql
-- ✅ CORRECT: Automatic liquid clustering
CREATE TABLE catalog.schema.fact_sales (
    sale_id BIGINT,
    customer_id BIGINT,
    sale_date DATE,
    amount DECIMAL(18,2)
)
USING DELTA
CLUSTER BY AUTO;

-- ✅ CORRECT: Enable on existing table
ALTER TABLE catalog.schema.fact_sales
CLUSTER BY AUTO;

-- ❌ WRONG: Manual Z-ORDER (legacy pattern)
OPTIMIZE catalog.schema.fact_sales ZORDER BY (sale_date, customer_id);

-- ❌ WRONG: Manual cluster columns (may not be optimal)
CREATE TABLE catalog.schema.fact_sales
CLUSTER BY (sale_date);
```

### How Liquid Clustering Works

```
Query Patterns Analysis
        │
        ▼
┌───────────────────┐
│ Automatic Column  │ ◄── Based on WHERE clauses
│ Selection         │     JOIN conditions
└───────────────────┘     GROUP BY patterns
        │
        ▼
┌───────────────────┐
│ Incremental       │ ◄── Only new/modified files
│ Clustering        │     Not full table rewrite
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Data Skipping     │ ◄── Min/max statistics
│ Optimization      │     File pruning
└───────────────────┘
```

---

## BP-06: Do Not Use Spark Caching with Delta Lake (Required)

> **Official Recommendation:** "Databricks does not recommend that you use Spark caching for the following reasons: You lose any data skipping that can come from additional filters... The data that gets cached might not be updated if the table is accessed using a different identifier." — [Databricks Docs](https://docs.databricks.com/en/delta/best-practices.html)

### Why Caching Hurts Delta Performance

| Issue | Description |
|-------|-------------|
| **Lost data skipping** | Filters after cache don't skip files |
| **Stale data** | Cached data may not reflect updates |
| **Memory pressure** | Consumes executor memory |
| **Different identifiers** | Table vs path access inconsistencies |

### Anti-Pattern

```python
# ❌ WRONG: Caching Delta table
df = spark.table("catalog.schema.my_table")
df.cache()  # Loses data skipping benefits!
df.filter("date = '2025-01-01'").count()  # No file pruning!

# ❌ WRONG: Persist with Delta
df = spark.read.format("delta").load("/path/to/table")
df.persist(StorageLevel.MEMORY_AND_DISK)  # Stale data risk!
```

### Correct Pattern

```python
# ✅ CORRECT: Let Delta handle optimization
df = spark.table("catalog.schema.my_table")
df.filter("date = '2025-01-01'").count()  # Uses data skipping!

# ✅ CORRECT: For repeated operations, use Delta's caching
# Delta automatically caches frequently accessed data
result1 = df.filter("region = 'US'").groupBy("product").count()
result2 = df.filter("region = 'US'").groupBy("customer").count()
# Delta reuses cached file metadata
```

### When Caching May Be Acceptable

| Scenario | Consideration |
|----------|---------------|
| Non-Delta sources | Caching may help |
| Static reference data | Small, unchanging datasets |
| Cross-format joins | Cache non-Delta side only |

---

## BP-07: Never Manually Modify Delta Data Files (Critical)

> **Official Recommendation:** "Don't manually modify data files: Delta Lake uses the transaction log to commit changes to the table atomically. Do not directly modify, add, or delete Parquet data files in a Delta table, because this can lead to lost data or table corruption." — [Databricks Docs](https://docs.databricks.com/en/delta/best-practices.html)

### What NOT to Do

```bash
# ❌ WRONG: Direct file deletion
aws s3 rm s3://bucket/delta-table/part-00001.parquet

# ❌ WRONG: Direct file addition
aws s3 cp new-data.parquet s3://bucket/delta-table/

# ❌ WRONG: External tools writing to Delta location
spark.write.parquet("s3://bucket/delta-table/new-partition/")

# ❌ WRONG: Manual file moves
aws s3 mv s3://bucket/delta-table/part-00001.parquet s3://archive/
```

### Why This Causes Problems

```
┌─────────────────────────────────────────────────────────────┐
│                    DELTA TRANSACTION LOG                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   _delta_log/                                               │
│   ├── 00000000000000000000.json  ◄── Tracks all files      │
│   ├── 00000000000000000001.json  ◄── Every transaction     │
│   └── ...                        ◄── Maintains consistency  │
│                                                             │
│   Manual file changes bypass the transaction log!           │
│                                                             │
│   Result:                                                   │
│   • Lost data (log says file exists, but deleted)          │
│   • Duplicate data (file exists but not in log)            │
│   • Table corruption (inconsistent state)                  │
│   • Failed queries (missing file errors)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Correct Data Operations

```sql
-- ✅ CORRECT: Delete data through Delta
DELETE FROM catalog.schema.my_table 
WHERE date < '2024-01-01';

-- ✅ CORRECT: Insert data through Delta
INSERT INTO catalog.schema.my_table 
SELECT * FROM source_table;

-- ✅ CORRECT: Update data through Delta
UPDATE catalog.schema.my_table 
SET status = 'archived' 
WHERE date < '2024-01-01';

-- ✅ CORRECT: Merge (upsert) through Delta
MERGE INTO catalog.schema.my_table AS target
USING updates AS source
ON target.id = source.id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

-- ✅ CORRECT: Remove old files through VACUUM
VACUUM catalog.schema.my_table RETAIN 168 HOURS;
```

---

## BP-10: Remove Legacy Delta Configurations (Recommended)

> **Official Recommendation:** "Databricks recommends removing most explicit legacy Delta configurations from Spark configurations and table properties when upgrading to a new Databricks Runtime version. Legacy configurations can prevent new optimizations and default values introduced by Databricks from being applied." — [Databricks Docs](https://docs.databricks.com/en/delta/best-practices.html)

### Legacy Configurations to Review

| Configuration | Action | Reason |
|---------------|--------|--------|
| `delta.autoOptimize.optimizeWrite` | Remove if using predictive optimization | Redundant |
| `delta.autoOptimize.autoCompact` | Remove if using predictive optimization | Redundant |
| `spark.sql.shuffle.partitions` | Let Spark auto-tune | AQE handles this |
| Explicit file size configs | Use Databricks defaults | Self-tuning now |
| `delta.targetFileSize` | Remove | Automatic tuning |
| `delta.tuneFileSizesForRewrites` | Remove | Default behavior |

### Migration Pattern

```sql
-- Check current table properties
SHOW TBLPROPERTIES catalog.schema.my_table;

-- Remove legacy properties
ALTER TABLE catalog.schema.my_table 
UNSET TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite',
  'delta.autoOptimize.autoCompact',
  'delta.targetFileSize'
);

-- Verify predictive optimization is enabled
DESCRIBE SCHEMA EXTENDED catalog.schema;
```

### Runtime Upgrade Checklist

- [ ] Review Spark configurations for legacy Delta settings
- [ ] Check table properties for outdated configs
- [ ] Enable predictive optimization at schema/catalog level
- [ ] Verify CLUSTER BY AUTO on critical tables
- [ ] Remove explicit shuffle partition settings
- [ ] Test query performance after changes

---

## MERGE Performance Optimization

> **Official Recommendation:** "You can reduce the time it takes to merge by... reducing the search space for matches." — [Databricks Docs](https://docs.databricks.com/en/delta/best-practices.html)

### Strategy 1: Reduce Search Space

```sql
-- ✅ CORRECT: Constrained MERGE (much faster)
MERGE INTO catalog.schema.events AS target
USING updates AS source
ON target.event_id = source.event_id
   AND target.event_date = current_date()  -- Partition filter!
   AND target.region = 'US'                -- Additional constraint
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

-- ❌ WRONG: Full table scan (slow)
MERGE INTO catalog.schema.events AS target
USING updates AS source
ON target.event_id = source.event_id  -- Scans entire table!
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

### Strategy 2: Enable Optimized Writes

```sql
-- Enable optimized writes for partitioned tables
ALTER TABLE catalog.schema.my_table
SET TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true');
```

> **Note:** If using predictive optimization, this is handled automatically.

### Strategy 3: Low Shuffle Merge

Low Shuffle Merge is **enabled by default** and provides:
- Better performance for most workloads
- Preserves existing data layout (clustering)
- Reduces shuffle operations
- Maintains Z-ordering on unmodified data

### Strategy 4: Compact Files Before MERGE

```sql
-- If not using predictive optimization, compact first
OPTIMIZE catalog.schema.my_table;

-- Then run MERGE
MERGE INTO catalog.schema.my_table ...
```

### MERGE Performance Factors

| Factor | Impact | Solution |
|--------|--------|----------|
| Search space | High | Add partition/constraint filters |
| File count | Medium | Use predictive optimization |
| Shuffle partitions | Medium | Let AQE auto-tune |
| File sizes | Low-Medium | Enable optimized writes |

---

## Delta Lake Operations Reference

### Don't Need These with Delta

> **Official Recommendation:** "Delta Lake handles the following operations automatically. You should never perform these operations manually." — [Databricks Docs](https://docs.databricks.com/en/delta/best-practices.html)

| Operation | Why Not Needed |
|-----------|----------------|
| `REFRESH TABLE` | Delta always returns up-to-date data |
| `ALTER TABLE ADD PARTITION` | Partitions tracked automatically |
| `ALTER TABLE DROP PARTITION` | Partitions tracked automatically |
| `MSCK REPAIR TABLE` | Not applicable to Delta |
| Direct partition reads | Use WHERE clause for data skipping |

### Correct Patterns

```sql
-- ❌ WRONG: Direct partition read (Parquet pattern)
-- spark.read.parquet("/data/date=2025-01-01")

-- ✅ CORRECT: WHERE clause with data skipping
SELECT * FROM catalog.schema.events
WHERE date = '2025-01-01';

-- ❌ WRONG: Refresh table (not needed)
-- REFRESH TABLE catalog.schema.my_table;

-- ✅ CORRECT: Just query - always fresh
SELECT * FROM catalog.schema.my_table;
```

---

## Validation Checklist

### Table Configuration
- [ ] All tables are Unity Catalog managed (BP-01)
- [ ] Predictive optimization enabled at schema/catalog level (BP-02)
- [ ] Liquid clustering enabled (`CLUSTER BY AUTO`) (BP-03)
- [ ] No manual Z-ORDER commands in pipelines
- [ ] No external writes to Delta locations (BP-07)

### Code Review
- [ ] No `df.cache()` or `df.persist()` on Delta tables (BP-06)
- [ ] No direct file system operations on Delta paths
- [ ] MERGE includes partition/constraint filters
- [ ] Legacy configurations removed after upgrades (BP-10)

### Operations
- [ ] No manual OPTIMIZE if predictive optimization enabled
- [ ] No manual VACUUM if predictive optimization enabled
- [ ] No REFRESH TABLE commands (not needed)
- [ ] No manual partition management

---

## Quick Reference

```sql
-- Enable predictive optimization
ALTER SCHEMA catalog.schema ENABLE PREDICTIVE OPTIMIZATION;

-- Enable liquid clustering
CREATE TABLE ... CLUSTER BY AUTO;
ALTER TABLE ... CLUSTER BY AUTO;

-- Check table properties
DESCRIBE EXTENDED catalog.schema.my_table;
SHOW TBLPROPERTIES catalog.schema.my_table;

-- Remove legacy configs
ALTER TABLE ... UNSET TBLPROPERTIES ('legacy.config');

-- Optimized MERGE pattern
MERGE INTO target USING source
ON target.key = source.key 
   AND target.partition_col = source.partition_col  -- Filter!
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

---

## References

- [Delta Lake Best Practices](https://docs.databricks.com/en/delta/best-practices.html)
- [Liquid Clustering](https://docs.databricks.com/en/delta/clustering.html)
- [Predictive Optimization](https://docs.databricks.com/en/optimizations/predictive-optimization.html)
- [Low Shuffle Merge](https://docs.databricks.com/en/optimizations/low-shuffle-merge.html)
- [OPTIMIZE Command](https://docs.databricks.com/en/delta/optimize.html)
- [VACUUM Command](https://docs.databricks.com/en/delta/vacuum.html)
