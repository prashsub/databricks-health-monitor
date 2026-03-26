# Metric Views Documentation

## Overview

This documentation suite provides comprehensive reference for the **Databricks Health Monitor Metric Views** - a portfolio of 10 Metric Views that enable aggregate analytics and natural language queries through Genie Spaces. These metric views provide semantic layer abstractions over Gold layer tables with LLM-friendly metadata.

## Architecture Principle

> **Metric Views are the semantic layer between Genie Spaces and Gold layer fact tables.**
> They provide pre-defined dimensions, measures, and aggregation patterns that Genie can leverage for natural language queries.

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 20 | [Index](20-metric-views-index.md) | This file - overview and navigation |
| 21 | [Introduction](21-metric-views-introduction.md) | Purpose, scope, prerequisites, design patterns |
| 22 | [Architecture](22-metric-views-architecture.md) | System architecture, YAML structure, deployment flow |
| 23 | [Deployment Guide](23-metric-views-deployment.md) | How to deploy and verify metric views |
| 24 | [Reference](24-metric-views-reference.md) | Complete metric view specifications |

## Domain Documentation

| Domain | Document | Metric Views |
|--------|----------|--------------|
| Cost | [cost-domain.md](by-domain/cost-domain.md) | `mv_cost_analytics`, `mv_commit_tracking` |
| Performance | [performance-domain.md](by-domain/performance-domain.md) | `mv_query_performance`, `mv_cluster_utilization`, `mv_cluster_efficiency` |
| Reliability | [reliability-domain.md](by-domain/reliability-domain.md) | `mv_job_performance` |
| Security | [security-domain.md](by-domain/security-domain.md) | `mv_security_events`, `mv_governance_analytics` |
| Quality | [quality-domain.md](by-domain/quality-domain.md) | `mv_data_quality`, `mv_ml_intelligence` |

## Appendices

| # | Document | Description |
|---|----------|-------------|
| A | [Quick Reference](appendices/mv-A-quick-reference.md) | Complete metric view table with dimensions/measures |
| B | [YAML Patterns](appendices/mv-B-yaml-patterns.md) | Common YAML patterns and examples |
| C | [Troubleshooting](appendices/mv-C-troubleshooting.md) | Common errors and solutions |

## Metric Views Summary by Domain

```
METRIC VIEWS FRAMEWORK (10 Views)
├── 💰 COST DOMAIN (2 Views)
│   ├── mv_cost_analytics        # Comprehensive cost analytics
│   │   └── 26 dimensions, 30 measures
│   └── mv_commit_tracking       # Budget and commitment tracking
│       └── Projection and burn rate
│
├── ⚡ PERFORMANCE DOMAIN (3 Views)
│   ├── mv_query_performance     # SQL warehouse query metrics
│   │   └── Latency, throughput, cache rates
│   ├── mv_cluster_utilization   # Cluster resource utilization
│   │   └── CPU, memory, node hours
│   └── mv_cluster_efficiency    # Cluster efficiency metrics
│       └── Idle time, right-sizing
│
├── 🔄 RELIABILITY DOMAIN (1 View)
│   └── mv_job_performance       # Job execution reliability
│       └── Success rates, duration percentiles
│
├── 🔒 SECURITY DOMAIN (2 Views)
│   ├── mv_security_events       # Audit event analytics
│   │   └── User activity, risk scoring
│   └── mv_governance_analytics  # Data lineage governance
│       └── Access patterns, activity
│
└── 📋 QUALITY DOMAIN (2 Views)
    ├── mv_data_quality          # Table freshness monitoring
    │   └── Staleness detection, domain health
    └── mv_ml_intelligence       # ML anomaly detection
        └── Cost anomaly insights
```

## Relationship with TVFs

| Aspect | TVFs (60) | Metric Views (10) |
|--------|-----------|-------------------|
| **Purpose** | Parameterized queries | Aggregate analytics |
| **Parameters** | User-defined inputs | Pre-configured |
| **Invocation** | `SELECT * FROM TABLE(tvf(...))` | `SELECT MEASURE(...) FROM mv_*` |
| **Documentation** | [00-07 files](00-index.md) | [20-24 files](20-metric-views-index.md) |
| **Use Case** | Specific, filtered queries | Dashboard aggregations |

## Quick Start

1. **Understand the Structure**: Start with [21-metric-views-introduction.md](21-metric-views-introduction.md)
2. **Review Architecture**: See [22-metric-views-architecture.md](22-metric-views-architecture.md)
3. **Deploy Views**: Follow [23-metric-views-deployment.md](23-metric-views-deployment.md)
4. **Reference Specific Views**: Navigate to domain-specific docs

## YAML File Locations

```
src/semantic/metric_views/
├── deploy_metric_views.py      # Deployment script
├── cost_analytics.yaml         # Cost domain
├── commit_tracking.yaml        # Cost domain
├── query_performance.yaml      # Performance domain
├── cluster_utilization.yaml    # Performance domain
├── cluster_efficiency.yaml     # Performance domain
├── job_performance.yaml        # Reliability domain
├── security_events.yaml        # Security domain
├── governance_analytics.yaml   # Security domain
├── data_quality.yaml           # Quality domain
└── ml_intelligence.yaml        # Quality domain (requires ML pipeline)
```

## Design Patterns Showcased

| # | Pattern | Implementation |
|---|---------|----------------|
| 1 | **v1.1 YAML Specification** | Standard metric view YAML structure |
| 2 | **`mv_` Prefix Convention** | All views prefixed for discoverability |
| 3 | **Gold Schema Deployment** | Views deployed alongside Gold tables |
| 4 | **LLM-Friendly Comments** | Structured PURPOSE/BEST FOR/NOT FOR comments |
| 5 | **Dimension Joins** | SCD2-aware dimension table joins |
| 6 | **Measure Formatting** | Currency, percentage, number formats |
| 7 | **Synonyms for NLP** | Multiple synonyms per dimension/measure |
| 8 | **Strict Error Handling** | Job fails if any view fails |

## Related Documentation

- [TVF Documentation (00-07)](00-index.md)
- [Gold Layer Design](../../gold_layer_design/design/00_design_overview.md)
- [Phase 3.3 Metric Views Plan](../../plans/phase3-addendum-3.3-metric-views.md)
- [Genie Spaces Plan](../../plans/phase3-addendum-3.6-genie-spaces.md)
