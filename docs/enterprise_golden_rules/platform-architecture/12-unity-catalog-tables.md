# Unity Catalog Tables & Storage

> **Document Owner:** Platform Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

Unity Catalog is the unified governance layer for all data and AI assets. This document defines standards for table types, storage, properties, and documentation.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **PA-01** | All tables in Unity Catalog (no HMS) | Critical |
| **PA-01a** | Managed tables are the default | Critical |
| **PA-01b** | External tables require approval | Required |
| **PA-02** | All tables use Delta Lake format | Critical |
| **PA-02a** | CLUSTER BY AUTO on all tables | Critical |
| **PA-02b** | Standard TBLPROPERTIES required | Required |
| **PA-02c** | LLM-friendly COMMENTs required | Required |

---

## Managed Tables (Default)

Managed tables are the recommended table type, offering automatic optimization and lower costs.

### Why Managed Tables?

| Benefit | Description |
|---------|-------------|
| Reduced costs | AI-driven optimization |
| Faster queries | Automatic maintenance |
| Secure access | Open APIs for external tools |
| Auto cleanup | Files deleted 8 days after DROP |

### Creating Managed Tables

```sql
-- Managed table (NO LOCATION clause)
CREATE TABLE catalog.schema.my_table (
    id BIGINT,
    name STRING,
    created_at TIMESTAMP
)
USING DELTA
CLUSTER BY AUTO;
```

---

## External Tables (Requires Approval)

External tables point to your own cloud storage. Use only when data must persist after DROP.

```sql
-- External table (requires External Location grant)
CREATE TABLE catalog.schema.external_table (...)
USING DELTA
LOCATION 's3://my-bucket/data/external_table';
```

| Scenario | Approval |
|----------|----------|
| Data sharing with external systems | Platform Architect |
| Regulatory data retention | Compliance + Platform |
| Legacy migration | Team Lead (temporary) |

---

## Automatic Liquid Clustering

Every table should use automatic clustering:

```sql
CREATE TABLE catalog.schema.my_table (...)
USING DELTA
CLUSTER BY AUTO;

-- Enable on existing table
ALTER TABLE catalog.schema.my_table CLUSTER BY AUTO;
```

### Why CLUSTER BY AUTO?

| Manual Clustering | Automatic (AUTO) |
|-------------------|------------------|
| Requires analysis | Self-tuning |
| Static over time | Adapts to queries |
| May become stale | Always optimized |

---

## Required Table Properties

```sql
CREATE TABLE catalog.schema.fact_orders (...)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
    -- Performance
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'delta.enableDeletionVectors' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    
    -- Governance
    'layer' = 'gold',
    'domain' = 'sales',
    'entity_type' = 'fact',
    'contains_pii' = 'false',
    'data_classification' = 'internal'
);
```

---

## Documentation Standards

### Table Comments

```sql
COMMENT ON TABLE gold.fact_orders IS 
'Daily order facts aggregated by customer and product.
Business: Primary source for revenue reporting.
Grain: One row per order_id.
Technical: Source is Silver layer order stream.';
```

### Column Comments

```sql
COMMENT ON COLUMN gold.fact_orders.total_amount IS
'Total order amount in USD after discounts.
Business: Primary revenue metric.
Technical: quantity * unit_price * (1 - discount_pct).';
```

---

## Primary/Foreign Keys

```sql
-- Add PK (informational, not enforced)
ALTER TABLE gold.dim_customer
ADD CONSTRAINT pk_dim_customer 
PRIMARY KEY (customer_key) NOT ENFORCED;

-- Add FK
ALTER TABLE gold.fact_orders
ADD CONSTRAINT fk_orders_customer
FOREIGN KEY (customer_key) 
REFERENCES gold.dim_customer(customer_key) NOT ENFORCED;
```

---

## Schema Management

### Enable Predictive Optimization

```sql
ALTER SCHEMA catalog.gold ENABLE PREDICTIVE OPTIMIZATION;
```

### Schema Properties (Asset Bundle)

```yaml
resources:
  schemas:
    gold_schema:
      name: gold
      catalog_name: ${var.catalog}
      comment: "Gold layer - business aggregates"
      properties:
        layer: "gold"
        delta.autoOptimize.optimizeWrite: "true"
```

---

## Access Control

```sql
-- Schema-level grants (preferred)
GRANT USE SCHEMA ON SCHEMA catalog.gold TO `analysts`;
GRANT SELECT ON SCHEMA catalog.gold TO `analysts`;

-- Function grants
GRANT EXECUTE ON FUNCTION catalog.gold.get_daily_orders TO `analysts`;
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

### Gold Layer
- [ ] PK constraint added
- [ ] FK constraints added (after all PKs exist)

---

## Related Documents

- [Serverless Compute](11-serverless-compute.md)
- [Data Governance](../enterprise-architecture/01-data-governance.md)

---

## References

- [Unity Catalog Managed Tables](https://learn.microsoft.com/en-us/azure/databricks/tables/managed)
- [Liquid Clustering](https://learn.microsoft.com/en-us/azure/databricks/delta/clustering)
- [Unity Catalog](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/)
