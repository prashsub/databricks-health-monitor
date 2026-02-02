# Unity Catalog Tables & Storage

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | PA-UC-001 |
| **Version** | 1.0 |
| **Last Updated** | January 2026 |
| **Owner** | Platform Engineering |
| **Status** | Approved |

---

## Executive Summary

Unity Catalog is the unified governance layer for all data assets. This document defines standards for table types (managed vs external), storage locations, table properties, and governance configurations.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| PA-01 | All tables in Unity Catalog (no HMS) | 🔴 Critical |
| PA-01a | Managed tables are the default | 🔴 Critical |
| PA-01b | External tables require approval | 🟡 Required |
| PA-02 | All tables use Delta Lake format | 🔴 Critical |
| PA-02a | CLUSTER BY AUTO on all tables | 🔴 Critical |
| PA-02b | Standard TBLPROPERTIES required | 🟡 Required |

---

## Unity Catalog Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          UNITY CATALOG STRUCTURE                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   METASTORE (Organization Level)                                                    │
│   └── CATALOG (Environment: dev, staging, prod)                                     │
│       ├── SCHEMA (Layer/Domain: bronze, silver, gold)                              │
│       │   ├── TABLE (Managed or External)                                          │
│       │   ├── VIEW (SQL Views)                                                     │
│       │   ├── METRIC VIEW (Semantic Layer)                                         │
│       │   ├── FUNCTION (SQL/Python UDFs, TVFs)                                     │
│       │   └── MODEL (MLflow Models)                                                │
│       └── VOLUME (Unstructured Data)                                               │
│                                                                                     │
│   EXAMPLE:                                                                          │
│   metastore: company-main                                                           │
│   └── company_prod (catalog)                                                        │
│       ├── bronze (schema)                                                          │
│       │   ├── bronze_orders (managed table)                                        │
│       │   └── bronze_customers (managed table)                                     │
│       ├── silver (schema)                                                          │
│       │   ├── silver_orders (streaming table - DLT)                               │
│       │   └── silver_customers (streaming table - DLT)                            │
│       └── gold (schema)                                                            │
│           ├── dim_customer (managed table)                                         │
│           ├── fact_orders (managed table)                                          │
│           ├── get_daily_orders (TVF)                                               │
│           └── orders_metrics (metric view)                                         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Rule PA-01a: Managed Tables (Default)

### What Are Managed Tables?

Managed tables store data in Unity Catalog's managed storage. Databricks handles the storage lifecycle.

```sql
-- ✅ CORRECT: Managed Table (No LOCATION clause)
CREATE TABLE catalog.schema.my_table (
    id BIGINT,
    name STRING,
    created_at TIMESTAMP
)
USING DELTA
CLUSTER BY AUTO;

-- When you DROP a managed table, data is also deleted
DROP TABLE catalog.schema.my_table;  -- Data deleted!
```

### Benefits of Managed Tables

| Benefit | Description |
|---------|-------------|
| **Simplified management** | No storage paths to configure |
| **Automatic cleanup** | Data deleted when table dropped |
| **Unified governance** | Single place for access control |
| **Predictive optimization** | Automatic compaction, Z-ordering |
| **Time travel** | 30-day retention by default |

### When to Use Managed Tables

| Scenario | Use Managed? |
|----------|--------------|
| New data products | ✅ Yes |
| Internal analytics | ✅ Yes |
| ML feature tables | ✅ Yes |
| Staging/temp tables | ✅ Yes |
| Shared with external systems | ❌ No (use external) |
| Data must persist after DROP | ❌ No (use external) |

---

## Rule PA-01b: External Tables (Requires Approval)

### What Are External Tables?

External tables point to data stored in your own cloud storage (S3, ADLS, GCS). You manage the storage lifecycle.

```sql
-- External table requires LOCATION and External Location grant
CREATE TABLE catalog.schema.external_table (
    id BIGINT,
    name STRING
)
USING DELTA
LOCATION 's3://my-bucket/data/external_table';

-- When you DROP an external table, data remains
DROP TABLE catalog.schema.external_table;  -- Data NOT deleted!
```

### External Location Setup

```sql
-- 1. Create Storage Credential (admin)
CREATE STORAGE CREDENTIAL my_s3_credential
WITH (
    STORAGE_CREDENTIAL_TYPE = 'AWS_IAM_ROLE',
    ARN = 'arn:aws:iam::123456789:role/databricks-s3-role'
);

-- 2. Create External Location
CREATE EXTERNAL LOCATION my_external_location
URL 's3://my-bucket/data/'
WITH (STORAGE CREDENTIAL my_s3_credential);

-- 3. Grant access
GRANT READ FILES, WRITE FILES ON EXTERNAL LOCATION my_external_location
TO `data_engineers`;
```

### When External Tables Are Required

| Scenario | Justification | Approval |
|----------|---------------|----------|
| Data sharing with external systems | Other systems read directly | Platform Architect |
| Regulatory data retention | Data must persist indefinitely | Compliance + Platform |
| Cross-cloud replication | Data in multiple clouds | Platform Architect |
| Legacy migration | Existing data locations | Team Lead (temporary) |

---

## Rule PA-02: Delta Lake Format

### All Tables Use Delta

```sql
-- ✅ CORRECT: Delta format (explicit or default)
CREATE TABLE catalog.schema.my_table (...)
USING DELTA;

-- ✅ Also correct (Delta is default in Unity Catalog)
CREATE TABLE catalog.schema.my_table (...);

-- ❌ WRONG: Other formats
CREATE TABLE catalog.schema.my_table (...)
USING PARQUET;  -- ❌ No governance features!

CREATE TABLE catalog.schema.my_table (...)
USING CSV;  -- ❌ No ACID, no versioning!
```

### Delta Lake Features

| Feature | Benefit |
|---------|---------|
| **ACID Transactions** | Reliable concurrent writes |
| **Time Travel** | Query historical data |
| **Schema Evolution** | Add/modify columns safely |
| **Change Data Feed** | Track row-level changes |
| **Liquid Clustering** | Automatic optimization |
| **Deletion Vectors** | Fast deletes/updates |
| **Row Tracking** | Identify changed rows |

---

## Rule PA-02a: CLUSTER BY AUTO

### Automatic Liquid Clustering

```sql
-- ✅ CORRECT: Automatic clustering
CREATE TABLE catalog.schema.my_table (
    id BIGINT,
    customer_id BIGINT,
    order_date DATE,
    amount DECIMAL(18,2)
)
USING DELTA
CLUSTER BY AUTO;  -- Let Delta choose optimal clustering

-- ❌ WRONG: Manual clustering (legacy)
CLUSTER BY (customer_id, order_date);  -- Don't specify columns
```

### Why AUTO?

| Manual Clustering | Automatic Clustering |
|-------------------|----------------------|
| Requires analysis | Self-tuning |
| Static over time | Adapts to query patterns |
| May become stale | Always optimized |
| Column type limits | No restrictions |

---

## Rule PA-02b: Standard Table Properties

### Required TBLPROPERTIES

```sql
CREATE TABLE catalog.schema.fact_orders (
    -- columns...
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
    -- Performance & Optimization
    'delta.enableChangeDataFeed' = 'true',       -- For downstream streaming
    'delta.enableRowTracking' = 'true',          -- Track row changes
    'delta.enableDeletionVectors' = 'true',      -- Fast deletes
    'delta.autoOptimize.optimizeWrite' = 'true', -- Optimize writes
    'delta.autoOptimize.autoCompact' = 'true',   -- Auto compact small files
    
    -- Governance Tags
    'layer' = 'gold',                            -- bronze/silver/gold
    'domain' = 'sales',                          -- Business domain
    'entity_type' = 'fact',                      -- dimension/fact
    'contains_pii' = 'false',                    -- PII flag
    'data_classification' = 'internal',          -- confidential/internal/public
    
    -- Ownership
    'business_owner' = 'Sales Analytics',
    'technical_owner' = 'Data Engineering'
);
```

### Property Reference

| Property | Values | Purpose |
|----------|--------|---------|
| `delta.enableChangeDataFeed` | true/false | Enable CDF for streaming |
| `delta.enableRowTracking` | true/false | Track row-level changes |
| `delta.enableDeletionVectors` | true/false | Fast delete operations |
| `delta.autoOptimize.optimizeWrite` | true/false | Optimize file sizes on write |
| `delta.autoOptimize.autoCompact` | true/false | Compact small files |
| `layer` | bronze/silver/gold | Medallion layer |
| `domain` | string | Business domain |
| `entity_type` | dimension/fact/bridge | Table type |
| `contains_pii` | true/false | PII presence |
| `data_classification` | confidential/internal/public | Data sensitivity |

---

## Volumes (Unstructured Data)

### What Are Volumes?

Volumes store unstructured data (files, images, models) with Unity Catalog governance.

```sql
-- Create a managed volume
CREATE VOLUME catalog.schema.raw_files
COMMENT 'Raw data files for ingestion';

-- Create an external volume
CREATE EXTERNAL VOLUME catalog.schema.ml_artifacts
LOCATION 's3://my-bucket/ml-artifacts/'
COMMENT 'ML model artifacts and checkpoints';

-- List files in volume
LIST '/Volumes/catalog/schema/raw_files/';

-- Copy files
COPY INTO catalog.schema.bronze_table
FROM '/Volumes/catalog/schema/raw_files/data.csv'
FILEFORMAT = CSV;
```

### Volume Types

| Type | Storage | Lifecycle | Use Case |
|------|---------|-----------|----------|
| **Managed** | UC-managed | Deleted with volume | Temporary files, staging |
| **External** | Your storage | Persists after DROP | ML artifacts, raw data |

---

## Schema Management

### Predictive Optimization

```sql
-- Enable at schema level (RECOMMENDED)
ALTER SCHEMA catalog.gold ENABLE PREDICTIVE OPTIMIZATION;

-- Verify status
SELECT 
    schema_name,
    enable_predictive_optimization
FROM system.information_schema.schemata
WHERE catalog_name = 'catalog';
```

### Schema Properties

```yaml
# Asset Bundle schema definition
resources:
  schemas:
    gold_schema:
      name: gold
      catalog_name: ${var.catalog}
      comment: "Gold layer - business aggregates and analytics"
      properties:
        layer: "gold"
        managed_by: "databricks_asset_bundles"
        delta.autoOptimize.optimizeWrite: "true"
        delta.autoOptimize.autoCompact: "true"
```

---

## Table Documentation

### LLM-Friendly Comments

```sql
-- Table comment with business context
CREATE TABLE catalog.gold.fact_orders (
    -- columns...
)
COMMENT 'Daily order facts aggregated by customer and product. 
Business: Primary source for revenue reporting and customer analytics.
Contains order amounts, quantities, discounts, and status.
Grain: One row per order_id.
Technical: Surrogate key is order_key (MD5 hash). 
Source: Silver layer order stream.';

-- Column comments
ALTER TABLE catalog.gold.fact_orders
ALTER COLUMN total_amount 
COMMENT 'Total order amount in USD after discounts. 
Business: Primary revenue metric.
Technical: Calculated as quantity * unit_price * (1 - discount_pct).';
```

### Required Documentation

| Element | Requirement |
|---------|-------------|
| Table COMMENT | Business purpose, grain, source |
| Column COMMENT | Every column (especially measures) |
| PII tags | All PII columns tagged |
| Classification | Table-level data classification |

---

## Constraints

### Primary and Foreign Keys

```sql
-- Add PK constraint (informational, not enforced)
ALTER TABLE catalog.gold.dim_customer
ADD CONSTRAINT pk_dim_customer 
PRIMARY KEY (customer_key) NOT ENFORCED;

-- Add FK constraint
ALTER TABLE catalog.gold.fact_orders
ADD CONSTRAINT fk_orders_customer
FOREIGN KEY (customer_key) 
REFERENCES catalog.gold.dim_customer(customer_key) NOT ENFORCED;
```

### Important Notes

- Constraints are **NOT ENFORCED** (informational only)
- Used by query optimizer for join optimization
- Required for Metric View relationships
- Document relationships in ERD

---

## Access Control

### Grant Patterns

```sql
-- Schema-level grants (preferred)
GRANT USE SCHEMA ON SCHEMA catalog.gold TO `analysts`;
GRANT SELECT ON SCHEMA catalog.gold TO `analysts`;

-- Table-level grants (when needed)
GRANT SELECT ON TABLE catalog.gold.fact_orders TO `finance_team`;

-- Function grants
GRANT EXECUTE ON FUNCTION catalog.gold.get_daily_orders TO `analysts`;

-- Column-level (for PII masking)
GRANT SELECT (id, name) ON TABLE catalog.gold.dim_customer TO `limited_users`;
-- PII columns excluded
```

---

## Validation Checklist

### New Table
- [ ] Created in Unity Catalog (not HMS)
- [ ] Uses DELTA format
- [ ] CLUSTER BY AUTO applied
- [ ] Required TBLPROPERTIES set
- [ ] Table COMMENT present
- [ ] All columns have COMMENT
- [ ] PII columns tagged
- [ ] PK/FK constraints added (Gold)

### Schema Setup
- [ ] Predictive Optimization enabled
- [ ] Schema properties set
- [ ] Appropriate grants applied

### External Tables
- [ ] Exception documented and approved
- [ ] External Location created
- [ ] Storage Credential configured
- [ ] Access grants applied

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Table not found` | Using HMS reference | Use 3-part name: `catalog.schema.table` |
| `Permission denied` | Missing grants | Request access via proper channel |
| `Invalid location` | External location not configured | Create External Location first |
| `Cannot cluster by BOOLEAN` | Manual clustering | Use CLUSTER BY AUTO |

---

## Related Documents

- [Serverless Compute](11-serverless-compute.md)
- [Data Governance](../enterprise-architecture/01-data-governance.md)
- [Gold Layer Patterns](../solution-architecture/data-pipelines/12-gold-layer-patterns.md)

---

## References

- [Unity Catalog](https://docs.databricks.com/unity-catalog/)
- [Managed vs External Tables](https://docs.databricks.com/tables/managed-vs-external.html)
- [Delta Lake Properties](https://docs.databricks.com/delta/table-properties.html)
- [Liquid Clustering](https://docs.databricks.com/delta/clustering.html)
