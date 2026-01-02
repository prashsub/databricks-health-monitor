# Lakehouse Monitoring Design Documentation

## Overview

This documentation covers the comprehensive Lakehouse Monitoring implementation for the Databricks Health Monitor platform. The monitoring system tracks **8 Gold layer fact tables** across **5 agent domains** (Cost, Performance, Reliability, Security, Quality), providing **300+ custom metrics** for automated data quality tracking, drift detection, and Genie-powered natural language analytics.

> **Core Principle:**
> Monitor Gold layer tables with business-aligned custom metrics that enable both automated alerting AND natural language queries through Genie.

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 01 | [Introduction](01-introduction.md) | Purpose, scope, prerequisites, best practices matrix |
| 02 | [Architecture Overview](02-architecture-overview.md) | System architecture, data flows, technology stack |
| 03 | [Custom Metrics](03-custom-metrics.md) | Metric types (AGGREGATE, DERIVED, DRIFT), patterns |
| 04 | [Monitor Catalog](04-monitor-catalog.md) | All 8 monitors with metrics breakdown by domain |
| 05 | [Genie Integration](05-genie-integration.md) | Table/column documentation for LLM understanding |
| 06 | [Implementation Guide](06-implementation-guide.md) | Step-by-step setup and deployment |
| 07 | [Operations Guide](07-operations-guide.md) | Production operations, refresh, troubleshooting |

## Appendices

| # | Document | Description |
|---|----------|-------------|
| A | [Code Examples](appendices/A-code-examples.md) | Complete working code snippets |
| B | [Troubleshooting](appendices/B-troubleshooting.md) | Error reference and solutions |
| C | [References](appendices/C-references.md) | Official documentation links |

## Lakehouse Monitoring Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MONITORING LAYER                                    │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    Asset Bundle Jobs (YAML)                          │   │
│   │  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐    │   │
│   │  │  Setup Job     │  │  Refresh Job   │  │  Documentation Job  │    │   │
│   │  │  (one-time)    │  │  (scheduled)   │  │  (post-init)        │    │   │
│   │  └────────────────┘  └────────────────┘  └─────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Monitor Notebooks (Python)                       │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│   │  │ Cost     │ │ Job      │ │ Query    │ │ Cluster  │ │ Security │   │   │
│   │  │ Monitor  │ │ Monitor  │ │ Monitor  │ │ Monitor  │ │ Monitor  │   │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐                             │   │
│   │  │ Quality  │ │Governance│ │Inference │                             │   │
│   │  │ Monitor  │ │ Monitor  │ │ Monitor  │                             │   │
│   │  └──────────┘ └──────────┘ └──────────┘                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    Shared Utilities (Pure Python)                    │   │
│   │  ┌──────────────────────────────────────────────────────────────┐   │   │
│   │  │ monitor_utils.py                                              │   │   │
│   │  │ • create_time_series_monitor()  • create_aggregate_metric()   │   │   │
│   │  │ • delete_monitor_if_exists()    • create_derived_metric()     │   │   │
│   │  │ • document_monitor_tables()     • create_drift_metric()       │   │   │
│   │  │ • METRIC_DESCRIPTIONS (100+)    • MONITOR_TABLE_DESCRIPTIONS  │   │   │
│   │  └──────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GOLD LAYER TABLES                                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                │
│  │ fact_usage      │ │fact_job_run_    │ │fact_query_      │                │
│  │ (Cost)          │ │timeline (Rel)   │ │history (Perf)   │                │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                │
│  │fact_node_       │ │fact_audit_logs  │ │fact_table_      │                │
│  │timeline (Perf)  │ │(Security)       │ │quality (Qual)   │                │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘                │
│  ┌─────────────────┐ ┌─────────────────┐                                    │
│  │fact_governance_ │ │fact_model_      │                                    │
│  │metrics (Gov)    │ │serving (ML)     │                                    │
│  └─────────────────┘ └─────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MONITORING OUTPUT SCHEMA                                 │
│                     {catalog}.{gold_schema}_monitoring                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Profile Metrics Tables                           │    │
│  │  • fact_usage_profile_metrics (35 metrics)                          │    │
│  │  • fact_job_run_timeline_profile_metrics (50 metrics)               │    │
│  │  • fact_query_history_profile_metrics (40 metrics)                  │    │
│  │  • fact_node_timeline_profile_metrics (40 metrics)                  │    │
│  │  • fact_audit_logs_profile_metrics                                  │    │
│  │  • ... (8 total)                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Drift Metrics Tables                             │    │
│  │  • fact_usage_drift_metrics                                         │    │
│  │  • fact_job_run_timeline_drift_metrics                              │    │
│  │  • ... (8 total)                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONSUMERS                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ AI/BI        │  │ Genie        │  │ SQL Alerts   │  │ Dashboards   │    │
│  │ Dashboards   │  │ Spaces       │  │ (V2)         │  │ (Lakeview)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

1. **Understand the Architecture**: Start with [02-Architecture Overview](02-architecture-overview.md)
2. **Review Metric Types**: Learn AGGREGATE, DERIVED, DRIFT patterns in [03-Custom Metrics](03-custom-metrics.md)
3. **Explore Monitor Catalog**: Browse all monitors in [04-Monitor Catalog](04-monitor-catalog.md)
4. **Deploy Monitors**: Follow [06-Implementation Guide](06-implementation-guide.md)
5. **Enable Genie**: Configure LLM documentation per [05-Genie Integration](05-genie-integration.md)

## Best Practices Showcased

| # | Best Practice | Implementation | Document |
|---|---------------|----------------|----------|
| 1 | **Time Series Monitoring** | All monitors use `MonitorTimeSeries` with timestamp columns | [03-Custom Metrics](03-custom-metrics.md) |
| 2 | **Business KPIs at Table Level** | `input_columns=[":table"]` for all custom metrics | [03-Custom Metrics](03-custom-metrics.md#table-level-aggregation) |
| 3 | **Derived Metrics from Base** | Business ratios computed from AGGREGATE metrics | [03-Custom Metrics](03-custom-metrics.md#derived-metrics) |
| 4 | **Drift Detection** | Period-over-period comparison with `{{current_df}}` / `{{base_df}}` | [03-Custom Metrics](03-custom-metrics.md#drift-metrics) |
| 5 | **Genie Documentation** | Table/column comments via ALTER TABLE/COLUMN | [05-Genie Integration](05-genie-integration.md) |
| 6 | **Dimensional Slicing** | Multiple slicing expressions per monitor for granular analysis | [05-Genie Integration](05-genie-integration.md#slicing-dimensional-analysis) |
| 7 | **Complete Cleanup** | Delete monitor + drop output tables before recreation | [06-Implementation](06-implementation-guide.md#cleanup) |
| 8 | **Serverless Deployment** | All jobs use serverless compute | [06-Implementation](06-implementation-guide.md#deployment) |
| 9 | **Pure Python Utilities** | `monitor_utils.py` importable without notebook header | [02-Architecture](02-architecture-overview.md#code-organization) |

## Critical Query Patterns

**Lakehouse Monitoring tables require specific query patterns for correct results.**

### Key Filter Columns

| Column | Purpose | Value |
|--------|---------|-------|
| `column_name` | Filter to table-level vs column-level metrics | Use `':table'` for custom business KPIs |
| `log_type` | Input vs output statistics | Use `'INPUT'` for source data |
| `slice_key` | Dimension for sliced analysis | `NULL` for overall, or dimension name |
| `slice_value` | Value of slicing dimension | Specific value to filter |
| `drift_type` | Type of drift comparison | Use `'CONSECUTIVE'` for period-over-period |

### Example Query Patterns

```sql
-- Overall KPIs (no slicing)
SELECT total_daily_cost, tag_coverage_pct
FROM fact_usage_profile_metrics
WHERE column_name = ':table' AND log_type = 'INPUT' AND slice_key IS NULL;

-- Sliced by dimension
SELECT slice_value AS workspace, total_daily_cost
FROM fact_usage_profile_metrics
WHERE column_name = ':table' AND log_type = 'INPUT' AND slice_key = 'workspace_id';

-- Drift analysis
SELECT cost_drift_pct FROM fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table';
```

See [05-Genie Integration](05-genie-integration.md#critical-query-patterns-for-genie) for comprehensive query guidance.

## Key Statistics

| Metric | Value |
|--------|-------|
| **Total Monitors** | 8 |
| **Agent Domains Covered** | 5 (Cost, Performance, Reliability, Security, Quality) |
| **Custom Metrics** | 300+ |
| **Metric Descriptions** | 100+ (for Genie) |
| **Profile Output Tables** | 8 |
| **Drift Output Tables** | 8 |
| **Deployment Jobs** | 3 (Setup, Document, Refresh) |
| **Lines of Code** | ~2,500 |

## Monitors by Agent Domain

| Domain | Gold Table | Metrics | Use Cases |
|--------|------------|---------|-----------|
| 💰 **Cost** | `fact_usage` | 35 | Budget tracking, tag coverage, SKU analysis |
| ⚡ **Performance** | `fact_query_history` | 40 | Query latency, SLA breaches, efficiency |
| ⚡ **Performance** | `fact_node_timeline` | 40 | CPU/memory utilization, right-sizing |
| 🔄 **Reliability** | `fact_job_run_timeline` | 50 | Success rates, duration, failures |
| 🔒 **Security** | `fact_audit_logs` | 15 | Auth failures, sensitive actions |
| ✅ **Quality** | `fact_table_quality` | 15 | Data freshness, schema drift |
| 📊 **Governance** | `fact_governance_metrics` | 15 | Documentation, tagging, lineage |
| 🤖 **ML** | `fact_model_serving` | 15 | Inference latency, error rates |

## Related Documentation

- [Gold Layer Design](../gold/GOLD_LAYER_PROGRESS.md) - Source tables for monitoring
- [Genie Spaces Deployment](../deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Natural language query setup
- [SQL Alerting Patterns](../../.cursor/rules/monitoring/19-sql-alerting-patterns.mdc) - Alert configuration
- [Lakehouse Monitoring Cursor Rule](../../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc) - Development patterns

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Author:** Data Engineering Team

