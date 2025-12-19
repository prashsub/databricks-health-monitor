# Databricks Health Monitor - Project Plans

## Overview

This folder contains comprehensive implementation plans for the Databricks Health Monitor project, a platform observability solution built on Databricks system tables.

---

## Phase Summary

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| **1** | [Bronze Ingestion](./phase1-bronze-ingestion.md) | ✅ Implemented | Ingest 21 system tables via DLT streaming |
| **2** | [Gold Layer Design](./phase2-gold-layer-design.md) | ✅ Implemented | 37-table dimensional model (12 dims, 25 facts) |
| **3** | [Use Cases](./phase3-use-cases.md) | 📋 Planned | ML, TVFs, Metric Views, Monitoring, Dashboards, Genie |
| **4** | [Agent Framework](./phase4-agent-framework.md) | 📋 Planned | 6 specialized agents with orchestrator |
| **5** | [Frontend App](./phase5-frontend-app.md) | 📋 Planned | React + TypeScript web application |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABRICKS SYSTEM TABLES                             │
│                              (35+ tables)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: BRONZE LAYER (DLT Streaming)                     │
│                         21 streaming tables                                  │
│                    + Data Quality Rules + CDF                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: GOLD LAYER (Dimensional Model)                   │
│                12 Dimensions + 25 Facts = 37 tables                          │
│                   YAML-driven + PK/FK constraints                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 3: USE CASES                                   │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  3.1 ML     │  │  3.2 TVFs   │  │ 3.3 Metric  │  │3.4 Monitors │        │
│  │   Models    │  │             │  │   Views     │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐                                           │
│  │ 3.5 AI/BI   │  │ 3.6 Genie   │                                           │
│  │ Dashboards  │  │   Spaces    │                                           │
│  └─────────────┘  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: AGENT FRAMEWORK                                  │
│                                                                              │
│            ┌──────────────────────────────────┐                             │
│            │      ORCHESTRATOR AGENT          │                             │
│            └──────────────────────────────────┘                             │
│                           │                                                  │
│       ┌───────────────────┼───────────────────┐                             │
│       ▼                   ▼                   ▼                             │
│  ┌─────────┐        ┌─────────┐        ┌─────────┐                         │
│  │  Cost   │        │Security │        │ Perf    │                         │
│  │  Agent  │        │ Agent   │        │ Agent   │                         │
│  └─────────┘        └─────────┘        └─────────┘                         │
│  ┌─────────┐        ┌─────────┐        ┌─────────┐                         │
│  │Reliab.  │        │  DQ &   │        │ ML Ops  │                         │
│  │ Agent   │        │Gov Agent│        │ Agent   │                         │
│  └─────────┘        └─────────┘        └─────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 5: FRONTEND APPLICATION                             │
│                                                                              │
│                    React + TypeScript + Databricks Apps                      │
│                                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │Dashboard│  │  Chat   │  │  Cost   │  │  Jobs   │  │Security │          │
│  │   Hub   │  │Interface│  │ Center  │  │ Center  │  │ Center  │          │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 3 Addendums

| Addendum | Topic | Document | Key Deliverables |
|----------|-------|----------|------------------|
| **3.1** | ML Models | [📄 phase3-addendum-3.1-ml-models.md](./phase3-addendum-3.1-ml-models.md) | 5 predictive models (cost anomaly, job failure, query forecast, capacity, security) |
| **3.2** | Table-Valued Functions | [📄 phase3-addendum-3.2-tvfs.md](./phase3-addendum-3.2-tvfs.md) | 31 TVFs across 5 domains (cost, jobs, queries, security, compute) |
| **3.3** | UC Metric Views | [📄 phase3-addendum-3.3-metric-views.md](./phase3-addendum-3.3-metric-views.md) | 5 metric views with semantic layer for Genie |
| **3.4** | Lakehouse Monitoring | [📄 phase3-addendum-3.4-lakehouse-monitoring.md](./phase3-addendum-3.4-lakehouse-monitoring.md) | 5 monitors with 25+ custom metrics and alerts |
| **3.5** | AI/BI Dashboards | [📄 phase3-addendum-3.5-ai-bi-dashboards.md](./phase3-addendum-3.5-ai-bi-dashboards.md) | 6 Lakeview dashboards (Executive, Cost, Jobs, Queries, Clusters, Security) |
| **3.6** | Genie Spaces | [📄 phase3-addendum-3.6-genie-spaces.md](./phase3-addendum-3.6-genie-spaces.md) | 6 Genie spaces with agent instructions and benchmark questions |

---

## Implementation Timeline

```
Phase 1 ──────────────────────────────────────────▶ ✅ Complete
       └─ Bronze DLT Pipeline
       └─ Data Quality Rules
       └─ Non-streaming Tables

Phase 2 ──────────────────────────────────────────▶ ✅ Complete
       └─ YAML Schema Definitions
       └─ Gold Table Creation
       └─ PK/FK Constraints

Phase 3 ──────────────────────────────────────────▶ 📋 Planned
       └─ 3.1 ML Models
       └─ 3.2 TVFs
       └─ 3.3 Metric Views
       └─ 3.4 Lakehouse Monitoring
       └─ 3.5 AI/BI Dashboards
       └─ 3.6 Genie Spaces

Phase 4 ──────────────────────────────────────────▶ 📋 Planned
       └─ Agent Definitions
       └─ Tool Integration
       └─ Orchestrator
       └─ Deployment

Phase 5 ──────────────────────────────────────────▶ 📋 Planned
       └─ Frontend Components
       └─ API Development
       └─ Databricks Apps Deployment
```

---

## Key Technologies

| Layer | Technologies |
|-------|--------------|
| **Data Ingestion** | Delta Live Tables, Serverless |
| **Data Model** | Unity Catalog, Delta Lake, YAML schemas |
| **ML/AI** | MLflow, Feature Store, Model Serving |
| **Semantic Layer** | Metric Views, Table-Valued Functions |
| **Monitoring** | Lakehouse Monitoring, Custom Metrics |
| **Visualization** | AI/BI Dashboards (Lakeview) |
| **NL Interface** | Genie Spaces, Agent Framework |
| **Frontend** | React, TypeScript, Databricks Apps |

---

## Related Documentation

- [Gold Layer Column Mapping Guide](./GOLD_COLUMN_MAPPING.md) ⚠️ **Critical for Phase 3 implementation**
- [Gold Layer Design Overview](../gold_layer_design/design/00_design_overview.md)
- [ERD Documentation](../gold_layer_design/erd/)
- [YAML Schemas](../gold_layer_design/yaml/)
- [Cursor Rules](../.cursor/rules/)

---

## Getting Started

### Phase 1 & 2 (Implemented)

```bash
# Deploy all resources
databricks bundle deploy -t dev

# Run Bronze setup
databricks bundle run -t dev bronze_streaming_pipeline

# Run Gold setup
databricks bundle run -t dev gold_setup_job
```

### Phase 3+ (Future)

See individual phase documents for detailed implementation plans.

---

## Contact

- **Project**: Databricks Health Monitor
- **Repository**: DatabricksHealthMonitor
- **Owner**: Data Engineering Team

