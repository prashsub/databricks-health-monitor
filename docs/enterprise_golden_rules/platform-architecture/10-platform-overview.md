# Platform Architecture Overview

> **Document Owner:** Platform Architecture Team | **Status:** Approved | **Last Updated:** February 2026

## Overview

This document defines the core architectural decisions, technology stack, and integration patterns for our enterprise data platform built on Azure Databricks.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **PA-01** | All data in Unity Catalog (no HMS) | Critical |
| **PA-02** | All tables use Delta Lake | Critical |
| **PA-03** | Serverless compute for all jobs | Required |
| **PA-04** | Asset Bundles for all deployments | Critical |
| **PA-05** | Predictive Optimization enabled | Required |
| **PA-06** | Automatic Liquid Clustering (CLUSTER BY AUTO) | Required |
| **PA-07** | CDF enabled on Bronze tables | Required |
| **PA-08** | Table COMMENTs mandatory | Required |
| **PA-09** | Layer tags on all tables | Required |
| **PA-10** | Time Travel retention ≥7 days | Required |
| **PA-11** | Prefer Lakeflow Connect for ingestion | Critical |
| **PA-12** | Use incremental ingestion (not full loads) | Critical |

---

## Architecture Principles

### 1. Lakehouse with Medallion Architecture

Data flows through three layers of increasing quality:

| Layer | Purpose | Technology |
|-------|---------|------------|
| **Bronze** | Raw data with CDF | Delta Lake + Auto Loader |
| **Silver** | Validated data | Delta Live Tables + Expectations |
| **Gold** | Business entities | YAML-driven MERGE |

### 2. Unity Catalog Foundation

All assets managed through Unity Catalog's three-level namespace:

```
<catalog>.<schema>.<object>
```

| Asset Type | Example |
|------------|---------|
| Tables | `company_prod.gold.dim_customer` |
| Views | `company_prod.semantic.cost_metrics` |
| Functions | `company_prod.semantic.get_daily_sales` |
| ML Models | `company_prod.ml.customer_churn_model` |
| Volumes | `company_prod.raw.landing_files` |

### 3. Delta Lake with Automatic Clustering

Every table uses Delta Lake with automatic liquid clustering:

```sql
CREATE TABLE catalog.schema.my_table (...)
USING DELTA
CLUSTER BY AUTO  -- Let Databricks choose optimal clustering
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);
```

### 4. Serverless-First Compute

All workloads default to serverless:

| Workload | Compute | Benefit |
|----------|---------|---------|
| SQL Analytics | Serverless SQL Warehouse | Instant, built-in Photon |
| ETL Jobs | Serverless Workflows | Auto-scaling, no config |
| DLT Pipelines | Serverless DLT | Efficient workflows |
| Interactive | Serverless Notebooks | Fast startup |

---

## Technology Stack

### Core Platform

| Component | Technology |
|-----------|------------|
| Compute | Databricks Serverless |
| Storage | Delta Lake on Cloud |
| Governance | Unity Catalog |
| Orchestration | Databricks Workflows |
| CI/CD | Asset Bundles |

### Semantic Layer

| Component | Technology |
|-----------|------------|
| Metrics | Metric Views (YAML) |
| Functions | TVFs (SQL) |
| NL Interface | Genie Spaces |
| Dashboards | AI/BI Lakeview |

### ML/AI

| Component | Technology |
|-----------|------------|
| Experiments | MLflow |
| Feature Store | Unity Catalog |
| Model Registry | Unity Catalog |
| Model Serving | Serverless Endpoints |
| Agents | LangGraph + MLflow |

---

## Data Ingestion Strategy

**Priority order for ingestion approaches:**

| Priority | Approach | Use For |
|----------|----------|---------|
| 1 | **Lakeflow Connect** | Salesforce, ServiceNow, SQL Server, Workday |
| 2 | **DLT + Auto Loader** | File-based sources, message buses |
| 3 | **Structured Streaming** | Complex real-time requirements only |

**Avoid:** Custom batch pipelines with full loads (legacy only).

---

## Catalog Structure

```
company_prod/
├── bronze/           # Raw data layer
├── silver/           # Validated layer  
├── gold/             # Business entities
├── semantic/         # Metric Views, TVFs
├── ml/               # Features, models
├── monitoring/       # Monitoring outputs
└── sandbox/          # Ad-hoc exploration
```

---

## Deployment Model

All infrastructure deployed via Asset Bundles:

```
Git Push → CI Build → Validate Bundle → Dev Deploy → Prod Deploy
```

Resources managed:
- Jobs
- Pipelines
- Schemas
- Functions
- Dashboards

---

## Related Documents

- [Serverless Compute](11-serverless-compute.md)
- [Unity Catalog Tables](12-unity-catalog-tables.md)
- [Cluster Policies](13-cluster-policies.md)
- [Secrets Management](14-secrets-workspace-management.md)

---

## References

- [Azure Databricks Architecture](https://learn.microsoft.com/en-us/azure/databricks/getting-started/architecture)
- [Medallion Architecture](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- [Unity Catalog](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/)
- [Lakeflow Connect](https://learn.microsoft.com/en-us/azure/databricks/ingestion/overview)
