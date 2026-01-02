# Dashboard Framework Design

## Databricks Health Monitor - AI/BI Dashboard Architecture

**Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Design Documentation

---

## Overview

This documentation describes the comprehensive dashboard framework for the Databricks Health Monitor project. The framework is organized around **5 core domains** (Cost, Security, Performance, Reliability, Quality) plus a **Unified Dashboard** that provides executive-level insights across all domains.

---

## Document Index

| # | Document | Description |
|---|----------|-------------|
| **00** | [Index](00-index.md) | This document - framework overview and navigation |
| **01** | [Rationalization Plan](01-rationalization-plan.md) | Strategy for consolidating dashboards into domain-based structure |
| **02** | [Asset Inventory](02-asset-inventory.md) | Complete inventory of ML Models, Lakehouse Monitors, Metric Views |
| **03** | [Cost Dashboard](03-cost-dashboard.md) | Cost management, commit tracking, budget analysis |
| **04** | [Performance Dashboard](04-performance-dashboard.md) | Query performance, cluster utilization, DBR migration |
| **05** | [Quality Dashboard](05-quality-dashboard.md) | Data quality, governance, lineage |
| **06** | [Security Dashboard](06-security-dashboard.md) | Audit logs, access patterns, threat detection |
| **07** | [Reliability Dashboard](07-reliability-dashboard.md) | Job reliability, pipeline health, optimization |
| **08** | [Unified Dashboard](08-unified-dashboard.md) | Executive overview combining all domains |
| **09** | [Implementation Guide](09-implementation-guide.md) | Step-by-step implementation instructions |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        UNIFIED DASHBOARD (Executive)                          │
│                   Executive Summary + Best of Each Domain                     │
│                         ~80-100 datasets (target)                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    │    COST     │  │  SECURITY   │  │ PERFORMANCE │  │ RELIABILITY │  │  QUALITY    │
│    │   Domain    │  │   Domain    │  │   Domain    │  │   Domain    │  │   Domain    │
│    │  Dashboard  │  │  Dashboard  │  │  Dashboard  │  │  Dashboard  │  │  Dashboard  │
│    │             │  │             │  │             │  │             │  │             │
│    │ ~90 datasets│  │ ~90 datasets│  │ ~90 datasets│  │ ~90 datasets│  │ ~90 datasets│
│    └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
│          │                │                │                │                │
│          ▼                ▼                ▼                ▼                ▼
│    ┌─────────────────────────────────────────────────────────────────────────────┐
│    │                           SEMANTIC LAYER                                     │
│    │  • 11 Metric Views    • 60+ TVFs    • 5 Genie Spaces                       │
│    └─────────────────────────────────────────────────────────────────────────────┘
│          │                │                │                │                │
│          ▼                ▼                ▼                ▼                ▼
│    ┌─────────────────────────────────────────────────────────────────────────────┐
│    │                           ML INTELLIGENCE                                    │
│    │  • 25 ML Models across 5 domains                                           │
│    │  • Predictions, Anomalies, Forecasts, Recommendations                      │
│    └─────────────────────────────────────────────────────────────────────────────┘
│          │                │                │                │                │
│          ▼                ▼                ▼                ▼                ▼
│    ┌─────────────────────────────────────────────────────────────────────────────┐
│    │                      LAKEHOUSE MONITORING                                    │
│    │  • 8 Monitors with ~155 Custom Metrics                                     │
│    │  • Profile Metrics, Drift Metrics, Aggregate Metrics                       │
│    └─────────────────────────────────────────────────────────────────────────────┘
│          │                │                │                │                │
│          ▼                ▼                ▼                ▼                ▼
│    ┌─────────────────────────────────────────────────────────────────────────────┐
│    │                          GOLD LAYER TABLES                                  │
│    │  • fact_usage          • fact_audit_logs     • fact_query_history          │
│    │  • fact_job_run_timeline  • fact_node_timeline  • fact_table_lineage       │
│    │  • dim_workspace  • dim_job  • dim_cluster  • dim_sku  etc.               │
│    └─────────────────────────────────────────────────────────────────────────────┘
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Domain Alignment

The dashboard framework is aligned with the 5 core agent domains:

| Domain | Focus Areas | Primary Gold Tables | Key Metrics |
|--------|-------------|---------------------|-------------|
| **Cost** | Billing, Spend, Budget, Tags | `fact_usage` | Cost trends, tag coverage, serverless adoption |
| **Security** | Audit, Access, Permissions | `fact_audit_logs` | Event volume, failed access, sensitive actions |
| **Performance** | Queries, Clusters, Resources | `fact_query_history`, `fact_node_timeline` | Duration P95, CPU/Memory utilization |
| **Reliability** | Jobs, Pipelines, Uptime | `fact_job_run_timeline` | Success rate, MTTR, duration trends |
| **Quality** | Data Quality, Governance | `fact_table_lineage`, `fact_data_quality_results` | Quality scores, lineage coverage |

---

## Current vs Target State

### Current State (11 Dashboards)

| Dashboard | Datasets | Domain Alignment |
|-----------|----------|------------------|
| cost_management | 36 | Cost |
| commit_tracking | 13 | Cost |
| security_audit | 25 | Security |
| governance_hub | 16 | Quality + Security |
| query_performance | 23 | Performance |
| cluster_utilization | 23 | Performance |
| dbr_migration | 6 | Performance |
| job_reliability | 31 | Reliability |
| job_optimization | 7 | Reliability |
| table_health | 7 | Quality |
| executive_overview | 22 | Cross-domain |
| **health_monitor_unified** | 83 | Cross-domain |

**Total: ~292 datasets across 12 dashboards**

### Target State (6 Dashboards)

| Dashboard | Target Datasets | Source Dashboards |
|-----------|-----------------|-------------------|
| **Cost Domain** | ~90 | cost_management + commit_tracking |
| **Security Domain** | ~90 | security_audit + governance (partial) |
| **Performance Domain** | ~90 | query_performance + cluster_utilization + dbr_migration |
| **Reliability Domain** | ~90 | job_reliability + job_optimization |
| **Quality Domain** | ~90 | table_health + governance (partial) |
| **Unified (Executive)** | ~80 | Best of each domain |

**Total: 6 dashboards with comprehensive coverage**

---

## Key Features

### 1. ML Model Integration
- **43 ML models** providing predictions, anomaly detection, and recommendations
- Each domain dashboard has dedicated ML insights section
- Models produce inference tables that feed dashboards

### 2. Lakehouse Monitoring Integration
- **6 monitors** with **200+ custom metrics**
- Profile metrics for distribution analysis
- Drift metrics for change detection
- Custom aggregate, derived, and drift metrics

### 3. Global Filters
All dashboards support global filters:
- **Time Window**: Last 7 Days, 30 Days, 90 Days, 6 Months, 1 Year
- **Workspace**: Filter by workspace
- **Compute Type**: Serverless vs Classic
- **SKU Type**: Filter by product SKU
- **Job Status**: Success/Failed/All

### 4. Dataset Limit Management
- Lakeview dashboard limit: **100 datasets**
- Strategy: Consolidate within domains, rationalize in unified
- Use CTEs and efficient queries to reduce dataset count

---

## Related Documentation

- [Agent Framework Design](../agent-framework-design/00-index.md)
- [ML Framework Design](../ml-framework-design/)
- [Semantic Framework Design](../semantic-framework/)
- [Alerting Framework Design](../alerting-framework-design/)

---

## Quick Links

- **Implementation**: See [09-implementation-guide.md](09-implementation-guide.md)
- **Asset Inventory**: See [02-asset-inventory.md](02-asset-inventory.md)
- **Rationalization Details**: See [01-rationalization-plan.md](01-rationalization-plan.md)

