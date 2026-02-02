# Platform Architecture Overview

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | PA-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Platform Architecture Team |
| **Status** | Approved |

---

## Executive Summary

This document provides a comprehensive overview of our enterprise data platform built on Databricks. It defines the core architectural decisions, technology stack, and integration patterns that all solutions must follow.

---

## Platform Vision

Our data platform enables the organization to:
- **Unify** all data in a single, governed lakehouse
- **Democratize** access through self-service analytics
- **Accelerate** insights with AI/ML capabilities
- **Ensure** compliance with governance and security controls

---

## Architecture Principles

### Principle 1: Lakehouse Architecture

We implement a lakehouse combining the best of data lakes and data warehouses:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            DATABRICKS LAKEHOUSE                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          CONSUMPTION LAYER                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │  AI/BI   │  │  SQL     │  │ ML Model │  │  GenAI   │  │External  │      │  │
│  │  │Dashboards│  │Analytics │  │ Serving  │  │ Agents   │  │   APIs   │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          SEMANTIC LAYER                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │  │
│  │  │ Metric Views │  │     TVFs     │  │Genie Spaces  │  │   AI/BI     │     │  │
│  │  │   (YAML)     │  │    (SQL)     │  │(NL Interface)│  │ Dashboards  │     │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          GOLD LAYER (Business Entities)                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │   dim_   │  │   dim_   │  │  fact_   │  │  fact_   │  │  agg_    │      │  │
│  │  │ customer │  │ product  │  │  orders  │  │  events  │  │ metrics  │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │  │
│  │              YAML-Driven Schema | PK/FK Constraints | MERGE Updates          │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          SILVER LAYER (Validated)                             │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐    │  │
│  │  │              DELTA LIVE TABLES (Streaming + Expectations)             │    │  │
│  │  │  • DLT Expectations (expect_or_drop)                                  │    │  │
│  │  │  • DQX Advanced Validation                                            │    │  │
│  │  │  • Quarantine Tables                                                  │    │  │
│  │  └──────────────────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          BRONZE LAYER (Raw)                                   │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                   Raw Data with CDF Enabled                           │    │  │
│  │  │  • Append-only ingestion                                              │    │  │
│  │  │  • Change Data Feed for incremental Silver                            │    │  │
│  │  │  • Source system schema preservation                                  │    │  │
│  │  └──────────────────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          STORAGE LAYER                                        │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                    DELTA LAKE ON CLOUD STORAGE                        │    │  │
│  │  │  • ACID Transactions  • Time Travel  • Schema Evolution               │    │  │
│  │  │  • Liquid Clustering  • Deletion Vectors  • Predictive Optimization   │    │  │
│  │  └──────────────────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Principle 2: Unity Catalog Foundation

All assets are managed through Unity Catalog:

| Asset Type | Unity Catalog Object | Example |
|------------|---------------------|---------|
| Databases | Catalogs + Schemas | `company_prod.gold` |
| Tables | Managed Tables | `company_prod.gold.dim_customer` |
| Views | Views + Metric Views | `company_prod.semantic.cost_metrics` |
| Functions | UDFs + TVFs | `company_prod.semantic.get_daily_sales` |
| ML Models | Model Registry | `company_prod.ml.customer_churn_model` |
| Files | Volumes | `company_prod.raw.landing_files` |

### Principle 3: Delta Lake Everywhere

**Rule PA-02: All tables MUST use Delta Lake format**

Benefits:
- ACID transactions for reliable data
- Time travel for audit and recovery
- Schema enforcement and evolution
- Optimized performance with liquid clustering

```sql
-- Every table uses Delta
CREATE TABLE catalog.schema.table_name (...)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);
```

### Principle 4: Serverless-First Compute

All compute uses serverless by default:

| Workload | Compute Type |
|----------|--------------|
| SQL Analytics | Serverless SQL Warehouse |
| ETL Jobs | Serverless Workflows |
| DLT Pipelines | Serverless DLT |
| ML Training | Serverless Compute |
| Model Serving | Serverless Endpoints |

---

## Technology Stack

### Core Platform

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Compute** | Databricks Serverless | All processing |
| **Storage** | Delta Lake on Cloud | All data storage |
| **Governance** | Unity Catalog | Metadata, access, lineage |
| **Orchestration** | Databricks Workflows | Job scheduling |
| **CI/CD** | Asset Bundles | Infrastructure as code |

### Data Pipeline Stack

| Layer | Technology | Key Features |
|-------|------------|--------------|
| **Bronze** | Delta Lake + CDF | Raw ingestion, change tracking |
| **Silver** | Delta Live Tables | Streaming, expectations, DQX |
| **Gold** | Delta MERGE | YAML-driven, constraints |

### Semantic Layer Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Metrics** | Metric Views (YAML) | Business KPIs |
| **Functions** | TVFs (SQL) | Parameterized queries |
| **NL Interface** | Genie Spaces | Natural language analytics |
| **Dashboards** | AI/BI Lakeview | Interactive visualization |

### ML/AI Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Experiment Tracking** | MLflow | Model development |
| **Feature Store** | Unity Catalog | Feature management |
| **Model Registry** | Unity Catalog | Model governance |
| **Model Serving** | Serverless Endpoints | Inference |
| **Agents** | LangGraph + MLflow | GenAI applications |
| **Memory** | Lakebase | Agent state management |

---

## Workspace Organization

### Environment Strategy

| Environment | Purpose | Catalog Pattern |
|-------------|---------|-----------------|
| **Dev** | Development, experimentation | `company_dev` |
| **Staging** | Integration testing | `company_staging` |
| **Production** | Live workloads | `company_prod` |

### Catalog Structure

```
company_prod/
├── bronze/                    # Raw data layer
│   ├── crm_raw/              # CRM source data
│   ├── erp_raw/              # ERP source data
│   └── web_raw/              # Web analytics
├── silver/                    # Validated layer
│   ├── customer_validated/
│   ├── product_validated/
│   └── sales_validated/
├── gold/                      # Business entities
│   └── analytics/            # Dimensional model
├── semantic/                  # Metric Views, TVFs
│   └── analytics/
├── ml/                        # ML assets
│   ├── features/             # Feature tables
│   └── models/               # Registered models
├── monitoring/                # Monitoring outputs
│   └── metrics/
└── sandbox/                   # Ad-hoc exploration
    └── analysts/
```

---

## Integration Patterns

### Data Ingestion

| Source Type | Pattern | Technology |
|-------------|---------|------------|
| Databases | CDC | Fivetran/Airbyte → Bronze |
| Files | Batch/Streaming | Auto Loader → Bronze |
| APIs | Pull | Python ETL → Bronze |
| Streaming | Real-time | Kafka → Bronze |

### Data Consumption

| Consumer | Interface | Pattern |
|----------|-----------|---------|
| BI Tools | SQL Warehouse | Direct query to Gold/Semantic |
| Data Science | Notebooks | Unity Catalog tables |
| Applications | REST APIs | Model Serving / Genie API |
| Reports | AI/BI | Lakeview dashboards |

---

## Operational Model

### Deployment Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            DEPLOYMENT PIPELINE                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐           │
│   │   Git   │──▶│   CI    │──▶│Validate │──▶│   Dev   │──▶│  Prod   │           │
│   │  Push   │   │  Build  │   │ Bundle  │   │ Deploy  │   │ Deploy  │           │
│   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘           │
│        │             │             │             │             │                  │
│        │             │             │             │             │                  │
│   ┌────▼─────────────▼─────────────▼─────────────▼─────────────▼────────────────┐│
│   │                        ASSET BUNDLES                                         ││
│   │  • Jobs  • Pipelines  • Schemas  • Functions  • Dashboards                  ││
│   └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Monitoring Strategy

| Layer | Monitoring Approach |
|-------|---------------------|
| **Infrastructure** | System tables, Workflow metrics |
| **Data Quality** | Lakehouse Monitoring, DLT expectations |
| **Business KPIs** | Custom metrics, Dashboards |
| **Alerts** | SQL Alerts → Slack/PagerDuty |

---

## Security Model

### Access Control

| Level | Mechanism |
|-------|-----------|
| **Catalog** | Unity Catalog grants |
| **Schema** | Schema-level permissions |
| **Table** | Table-level permissions |
| **Column** | Column masking, row filters |

### Secret Management

All secrets managed via Databricks Secret Scopes:

```python
# Access secret
api_key = dbutils.secrets.get(scope="my-scope", key="api-key")

# Never hardcode secrets
# ❌ api_key = "sk-1234..."
```

---

## Platform Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| PA-01 | All data in Unity Catalog | 🔴 Critical |
| PA-02 | All tables use Delta Lake | 🔴 Critical |
| PA-03 | Serverless compute for all jobs | 🟡 Required |
| PA-04 | Asset Bundles for all deployments | 🔴 Critical |
| PA-05 | Predictive Optimization enabled | 🟡 Required |
| PA-06 | Automatic Liquid Clustering | 🟡 Required |
| PA-07 | CDF enabled on Bronze tables | 🟡 Required |
| PA-08 | Table COMMENTs mandatory | 🟡 Required |
| PA-09 | Layer tags on all tables | 🟡 Required |

---

## Related Documents

- [Unity Catalog Standards](11-unity-catalog.md)
- [Compute Resources](12-compute-resources.md)
- [CI/CD Asset Bundles](20-cicd-asset-bundles.md)
- [Security Standards](23-security-standards.md)

---

## References

- [Databricks Lakehouse](https://docs.databricks.com/lakehouse/)
- [Unity Catalog](https://docs.databricks.com/unity-catalog/)
- [Delta Lake](https://docs.delta.io/)
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
