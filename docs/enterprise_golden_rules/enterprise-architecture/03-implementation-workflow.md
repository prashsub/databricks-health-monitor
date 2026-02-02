# Implementation Workflow

## Step-by-Step Guide for Golden Rules Implementation

**Version:** 1.0  
**Effective Date:** January 2026

---

## Overview

This document provides detailed workflows for implementing the Golden Rules in new and existing data platform projects.

---

## Workflow 1: New Data Domain Implementation

### Phase 1: Planning & Design (Week 1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: PLANNING                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 1.1: Requirements Gathering                                      │
│   ├── Identify data sources                                             │
│   ├── Document business requirements                                    │
│   ├── Define success metrics                                            │
│   └── Deliverable: Requirements Document                                │
│                                                                         │
│   Step 1.2: Data Classification                                         │
│   ├── Identify PII columns                                              │
│   ├── Assign data classification level                                  │
│   ├── Define retention requirements                                     │
│   └── Deliverable: Data Classification Matrix                           │
│                                                                         │
│   Step 1.3: Architecture Design                                         │
│   ├── Design Bronze schema                                              │
│   ├── Design Silver schema with expectations                            │
│   ├── Design Gold star schema (ERD)                                     │
│   └── Deliverable: Architecture Design Document                         │
│                                                                         │
│   Step 1.4: Schema Definition                                           │
│   ├── Create Gold layer YAML schemas                                    │
│   ├── Define PK/FK relationships                                        │
│   ├── Document column metadata                                          │
│   └── Deliverable: YAML Schema Files                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Step 1.1: Requirements Document Template

```markdown
# Data Domain: [Domain Name]

## Business Context
- **Purpose:** [Why this data domain is needed]
- **Stakeholders:** [Who will use this data]
- **Use Cases:** [Primary use cases]

## Source Systems
| Source | Type | Frequency | Volume | Format |
|--------|------|-----------|--------|--------|
| [System 1] | API | Real-time | 1M/day | JSON |
| [System 2] | File | Daily | 500K/file | CSV |

## Success Metrics
- [ ] Data freshness: < 2 hours
- [ ] Data quality: > 99% completeness
- [ ] Query performance: < 5 seconds
```

#### Step 1.2: Data Classification Matrix

| Column | Table | Contains PII | Classification | Retention |
|--------|-------|--------------|----------------|-----------|
| customer_name | dim_customer | Yes | Confidential | 7 years |
| email | dim_customer | Yes | Confidential | 7 years |
| order_amount | fact_orders | No | Internal | 5 years |
| product_name | dim_product | No | Internal | Forever |

#### Step 1.3: Architecture Design Checklist

- [ ] Bronze layer tables identified
- [ ] CDF enabled for all Bronze tables
- [ ] Silver DLT pipeline designed
- [ ] DLT expectations defined (5+ per table)
- [ ] Quarantine tables designed
- [ ] Gold star schema ERD created
- [ ] Fact table grain defined
- [ ] Dimension tables identified (SCD type assigned)

#### Step 1.4: YAML Schema Template

```yaml
# gold_layer_design/yaml/sales/dim_customer.yaml
table_name: dim_customer
schema: gold
domain: sales
scd_type: 2

columns:
  - name: customer_key
    type: STRING
    nullable: false
    comment: "Surrogate key - unique per version"
    
  - name: customer_id
    type: BIGINT
    nullable: false
    comment: "Business key from source system"
    
  - name: customer_name
    type: STRING
    nullable: true
    comment: "Full customer name. Contains PII."
    pii: true

primary_key:
  - customer_key

foreign_keys: []

table_properties:
  layer: gold
  domain: sales
  contains_pii: "true"
  data_classification: confidential
```

---

### Phase 2: Infrastructure Setup (Week 2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 2.1: Unity Catalog Setup                                         │
│   ├── Create catalog (if needed)                                        │
│   ├── Create schemas (bronze, silver, gold)                             │
│   ├── Apply schema properties                                           │
│   └── Enable predictive optimization                                    │
│                                                                         │
│   Step 2.2: Asset Bundle Creation                                       │
│   ├── Create bundle directory structure                                 │
│   ├── Write databricks.yml                                              │
│   ├── Create schema resource definitions                                │
│   └── Validate bundle configuration                                     │
│                                                                         │
│   Step 2.3: Access Control                                              │
│   ├── Create/identify user groups                                       │
│   ├── Grant schema permissions                                          │
│   ├── Configure service principals                                      │
│   └── Document access matrix                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Step 2.1: Unity Catalog Setup Script

```sql
-- Create catalog (if new)
CREATE CATALOG IF NOT EXISTS ${catalog};

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ${catalog}.bronze
COMMENT 'Bronze layer - raw data ingestion';

CREATE SCHEMA IF NOT EXISTS ${catalog}.silver
COMMENT 'Silver layer - cleaned and validated data';

CREATE SCHEMA IF NOT EXISTS ${catalog}.gold
COMMENT 'Gold layer - business-ready data';

-- Enable predictive optimization
ALTER SCHEMA ${catalog}.bronze ENABLE PREDICTIVE OPTIMIZATION;
ALTER SCHEMA ${catalog}.silver ENABLE PREDICTIVE OPTIMIZATION;
ALTER SCHEMA ${catalog}.gold ENABLE PREDICTIVE OPTIMIZATION;
```

#### Step 2.2: Asset Bundle Structure

```bash
# Create directory structure
mkdir -p my_domain/{resources/{bronze,silver,gold},src/{bronze,silver,gold}}

# Required files
touch my_domain/databricks.yml
touch my_domain/resources/schemas.yml
touch my_domain/resources/bronze/bronze_ingestion_job.yml
touch my_domain/resources/silver/silver_dlt_pipeline.yml
touch my_domain/resources/gold/gold_setup_job.yml
touch my_domain/resources/gold/gold_merge_job.yml
```

---

### Phase 3: Bronze Layer Implementation (Week 3)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PHASE 3: BRONZE LAYER                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 3.1: Create Bronze Tables                                        │
│   ├── Define table DDL with metadata                                    │
│   ├── Enable CDF on all tables                                          │
│   ├── Apply proper TBLPROPERTIES                                        │
│   └── Add table and column comments                                     │
│                                                                         │
│   Step 3.2: Build Ingestion Pipeline                                    │
│   ├── Create Auto Loader configuration                                  │
│   ├── Add ingestion metadata columns                                    │
│   ├── Configure checkpoint locations                                    │
│   └── Test with sample data                                             │
│                                                                         │
│   Step 3.3: Deploy Bronze Job                                           │
│   ├── Create Asset Bundle job definition                                │
│   ├── Configure serverless environment                                  │
│   ├── Deploy and test                                                   │
│   └── Verify CDF is working                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Step 3.1: Bronze Table Checklist

For each Bronze table, verify:

- [ ] Table created with `USING DELTA`
- [ ] `CLUSTER BY AUTO` specified
- [ ] `delta.enableChangeDataFeed = true`
- [ ] `delta.autoOptimize.optimizeWrite = true`
- [ ] `delta.autoOptimize.autoCompact = true`
- [ ] `layer = bronze` tag applied
- [ ] `source_system` tag specified
- [ ] `domain` tag specified
- [ ] Table COMMENT is LLM-friendly
- [ ] All columns have COMMENTs
- [ ] Ingestion metadata columns present (`_source_file`, `_ingestion_timestamp`, `_batch_id`)

---

### Phase 4: Silver Layer Implementation (Week 4)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PHASE 4: SILVER LAYER                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 4.1: Design DLT Pipeline                                         │
│   ├── Create DLT notebook structure                                     │
│   ├── Define streaming tables                                           │
│   ├── Design expectations (5+ per table)                                │
│   └── Create quarantine tables                                          │
│                                                                         │
│   Step 4.2: Implement Data Quality                                      │
│   ├── Null checks (expect_or_drop)                                      │
│   ├── Format validation (expect_or_drop)                                │
│   ├── Range validation (expect)                                         │
│   ├── Referential checks (expect)                                       │
│   └── Business rule validation                                          │
│                                                                         │
│   Step 4.3: Deploy DLT Pipeline                                         │
│   ├── Create pipeline Asset Bundle definition                           │
│   ├── Configure serverless + Photon                                     │
│   ├── Set up notifications                                              │
│   └── Run initial pipeline                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Step 4.2: DLT Expectations Template

```python
# Minimum expectations per table
@dlt.table(name="silver_orders")
# Critical - drop failing records
@dlt.expect_or_drop("has_order_id", "order_id IS NOT NULL")
@dlt.expect_or_drop("has_customer", "customer_id IS NOT NULL")
@dlt.expect_or_drop("valid_date", "order_date IS NOT NULL")
# Important - monitor but keep
@dlt.expect("positive_amount", "total_amount > 0")
@dlt.expect("valid_status", "status IN ('new', 'processing', 'shipped', 'delivered', 'cancelled')")
# Nice to have - just track
@dlt.expect("has_shipping", "shipping_address IS NOT NULL")
def silver_orders():
    return dlt.read_stream("bronze.raw_orders")
```

---

### Phase 5: Gold Layer Implementation (Week 5)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHASE 5: GOLD LAYER                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 5.1: Create Gold Tables                                          │
│   ├── Create dimension tables from YAML                                 │
│   ├── Create fact tables from YAML                                      │
│   ├── Add comprehensive comments                                        │
│   └── Verify table properties                                           │
│                                                                         │
│   Step 5.2: Apply Constraints                                           │
│   ├── Add PKs to all dimensions                                         │
│   ├── Add composite PK to facts                                         │
│   ├── Add FKs after all PKs exist                                       │
│   └── Verify constraint application                                     │
│                                                                         │
│   Step 5.3: Build MERGE Pipelines                                       │
│   ├── Implement deduplication                                           │
│   ├── Create dimension MERGE scripts                                    │
│   ├── Create fact MERGE scripts                                         │
│   └── Test with sample data                                             │
│                                                                         │
│   Step 5.4: Deploy Gold Jobs                                            │
│   ├── Create setup job (tables + constraints)                           │
│   ├── Create merge job (recurring)                                      │
│   ├── Configure schedules (PAUSED in dev)                               │
│   └── Deploy and test                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Step 5.2: Constraint Application Order

```python
# CORRECT ORDER:
# 1. Create ALL dimension tables (with inline PKs)
# 2. Create ALL fact tables (with inline composite PKs)
# 3. Apply ALL FKs via ALTER TABLE

def add_all_constraints(spark, catalog, schema):
    """Apply constraints in correct order."""
    
    # Step 1: Verify all PKs exist
    dimensions = ["dim_customer", "dim_product", "dim_store", "dim_date"]
    for dim in dimensions:
        result = spark.sql(f"""
            SELECT constraint_name 
            FROM information_schema.table_constraints
            WHERE table_schema = '{schema}' 
            AND table_name = '{dim}'
            AND constraint_type = 'PRIMARY KEY'
        """)
        if result.count() == 0:
            raise ValueError(f"Missing PK on {dim}!")
    
    # Step 2: Apply FKs
    spark.sql(f"""
        ALTER TABLE {catalog}.{schema}.fact_sales
        ADD CONSTRAINT fk_sales_customer 
        FOREIGN KEY (customer_key) 
        REFERENCES {catalog}.{schema}.dim_customer(customer_key) NOT ENFORCED
    """)
    # ... more FKs
```

---

### Phase 6: Semantic Layer Implementation (Week 6)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PHASE 6: SEMANTIC LAYER                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 6.1: Create Table-Valued Functions                               │
│   ├── Identify common query patterns                                    │
│   ├── Design TVF signatures                                             │
│   ├── Write TVF SQL with proper comments                                │
│   └── Test in Genie Space                                               │
│                                                                         │
│   Step 6.2: Create Metric Views                                         │
│   ├── Design metric view YAML                                           │
│   ├── Define dimensions and measures                                    │
│   ├── Add comprehensive comments                                        │
│   └── Deploy and verify                                                 │
│                                                                         │
│   Step 6.3: Configure Genie Space (Optional)                            │
│   ├── Create Genie Space                                                │
│   ├── Add trusted assets                                                │
│   ├── Configure sample questions                                        │
│   └── Test natural language queries                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 7: Monitoring & Production (Week 7-8)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PHASE 7: MONITORING & PRODUCTION                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 7.1: Set Up Lakehouse Monitoring                                 │
│   ├── Create monitors for Gold tables                                   │
│   ├── Define custom metrics                                             │
│   ├── Configure refresh schedule                                        │
│   └── Document metric meanings                                          │
│                                                                         │
│   Step 7.2: Create Alerts                                               │
│   ├── Data freshness alerts                                             │
│   ├── Data quality alerts                                               │
│   ├── Pipeline failure alerts                                           │
│   └── Cost threshold alerts                                             │
│                                                                         │
│   Step 7.3: Production Deployment                                       │
│   ├── Final code review                                                 │
│   ├── Security review (if PII)                                          │
│   ├── Deploy to production                                              │
│   ├── Enable schedules                                                  │
│   └── Monitor initial runs                                              │
│                                                                         │
│   Step 7.4: Documentation & Handoff                                     │
│   ├── Create runbook                                                    │
│   ├── Document troubleshooting steps                                    │
│   ├── Update data catalog                                               │
│   └── Train stakeholders                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow 2: Golden Rules Compliance Audit

### Audit Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COMPLIANCE AUDIT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Step 1: Inventory                                                     │
│   ├── List all tables in catalog                                        │
│   ├── Identify table ownership                                          │
│   ├── Categorize by layer                                               │
│   └── Generate audit scope                                              │
│                                                                         │
│   Step 2: Rule-by-Rule Assessment                                       │
│   ├── Rule 1: Unity Catalog compliance                                  │
│   ├── Rule 2: Medallion architecture adherence                          │
│   ├── Rule 3: Data quality coverage                                     │
│   ├── Rule 4: Delta Lake configuration                                  │
│   ├── Rule 5: Constraint coverage                                       │
│   ├── Rule 6: Compute configuration                                     │
│   ├── Rule 7: IaC coverage                                              │
│   ├── Rule 8: Documentation coverage                                    │
│   ├── Rule 9: Schema-first compliance                                   │
│   └── Rule 10: MERGE pattern compliance                                 │
│                                                                         │
│   Step 3: Findings Report                                               │
│   ├── Document violations                                               │
│   ├── Assign severity                                                   │
│   ├── Create remediation plan                                           │
│   └── Schedule follow-up                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Automated Audit Queries

```sql
-- Rule 4: Check Delta Lake properties
SELECT 
    table_catalog,
    table_schema,
    table_name,
    CASE WHEN option_value IS NULL THEN '❌ Missing' ELSE '✅ Enabled' END as cdf_status
FROM information_schema.tables t
LEFT JOIN information_schema.table_options o 
    ON t.table_catalog = o.table_catalog 
    AND t.table_schema = o.table_schema 
    AND t.table_name = o.table_name
    AND o.option_name = 'delta.enableChangeDataFeed'
WHERE t.table_schema IN ('bronze', 'silver', 'gold');

-- Rule 5: Check PK coverage
SELECT 
    table_schema,
    table_name,
    COUNT(constraint_name) as pk_count,
    CASE WHEN COUNT(constraint_name) > 0 THEN '✅' ELSE '❌' END as has_pk
FROM information_schema.table_constraints
WHERE constraint_type = 'PRIMARY KEY'
AND table_schema = 'gold'
GROUP BY table_schema, table_name;

-- Rule 8: Check documentation coverage
SELECT 
    table_schema,
    table_name,
    CASE WHEN comment IS NOT NULL AND LENGTH(comment) > 50 THEN '✅' ELSE '❌' END as has_comment,
    LENGTH(comment) as comment_length
FROM information_schema.tables
WHERE table_schema IN ('bronze', 'silver', 'gold');
```

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **1. Planning** | 1 week | Requirements, classification, schema YAMLs |
| **2. Infrastructure** | 1 week | UC setup, Asset Bundle, access control |
| **3. Bronze** | 1 week | Bronze tables, ingestion pipeline |
| **4. Silver** | 1 week | DLT pipeline, expectations, quarantine |
| **5. Gold** | 1 week | Star schema, constraints, MERGE |
| **6. Semantic** | 1 week | TVFs, Metric Views |
| **7-8. Production** | 2 weeks | Monitoring, alerts, deployment |

**Total: 8 weeks for new domain implementation**

---

## Related Documents

- [Golden Rules](../01-golden-rules-enterprise-data-platform.md)
- [Roles and Responsibilities](./01-roles-and-responsibilities-raci.md)
- [Verification Checklist](./03-verification-checklist.md)
