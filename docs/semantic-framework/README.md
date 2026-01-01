# Semantic Framework Documentation

The **Databricks Health Monitor Semantic Framework** provides a unified semantic layer over the Gold layer tables, enabling natural language queries through Genie Spaces and AI/BI dashboards. The framework consists of two complementary asset types:

| Asset Type | Count | Purpose | Documentation |
|------------|-------|---------|---------------|
| **Table-Valued Functions (TVFs)** | 60 | Parameterized queries for specific, filtered analysis | [00-07 files](00-index.md) |
| **Metric Views** | 10 | Pre-defined aggregate analytics for dashboards and Genie | [20-24 files](20-metric-views-index.md) |

## Architecture Principle

> **TVFs and Metric Views are the semantic layer between Genie Spaces and Gold layer tables.**
> They provide documented, optimized queries that Genie can invoke based on natural language questions.

## Quick Navigation

### Table-Valued Functions (60 TVFs)

Parameterized functions that accept user inputs and return filtered result sets.

| # | Document | Description |
|---|----------|-------------|
| 00 | [Index](00-index.md) | TVF documentation overview |
| 01 | [Introduction](01-introduction.md) | Purpose, scope, design patterns |
| 02 | [Architecture Overview](02-architecture-overview.md) | System architecture, data flows |
| 03 | [Cost Agent TVFs](03-cost-agent-tvfs.md) | 15 cost analysis TVFs |
| 04 | [Reliability Agent TVFs](04-reliability-agent-tvfs.md) | 12 reliability monitoring TVFs |
| 05 | [Performance Agent TVFs](05-performance-agent-tvfs.md) | 16 performance analysis TVFs |
| 06 | [Security Agent TVFs](06-security-agent-tvfs.md) | 10 security audit TVFs |
| 07 | [Quality Agent TVFs](07-quality-agent-tvfs.md) | 7 data quality TVFs |

### Metric Views (10 Views)

Pre-configured aggregate views that support MEASURE() function queries.

| # | Document | Description |
|---|----------|-------------|
| 20 | [Index](20-metric-views-index.md) | Metric views overview |
| 21 | [Introduction](21-metric-views-introduction.md) | Purpose, scope, design patterns |
| 22 | [Architecture](22-metric-views-architecture.md) | YAML structure, deployment flow |
| 23 | [Deployment Guide](23-metric-views-deployment.md) | How to deploy and verify |
| 24 | [Reference](24-metric-views-reference.md) | Complete view specifications |

### Domain-Specific Documentation

Detailed guides for each Agent Domain:

| Domain | TVFs | Metric Views | Documentation |
|--------|------|--------------|---------------|
| **Cost** | 15 | 2 | [03-cost-agent-tvfs.md](03-cost-agent-tvfs.md), [by-domain/cost-domain.md](by-domain/cost-domain.md) |
| **Performance** | 16 | 3 | [05-performance-agent-tvfs.md](05-performance-agent-tvfs.md), [by-domain/performance-domain.md](by-domain/performance-domain.md) |
| **Reliability** | 12 | 1 | [04-reliability-agent-tvfs.md](04-reliability-agent-tvfs.md), [by-domain/reliability-domain.md](by-domain/reliability-domain.md) |
| **Security** | 10 | 2 | [06-security-agent-tvfs.md](06-security-agent-tvfs.md), [by-domain/security-domain.md](by-domain/security-domain.md) |
| **Quality** | 7 | 2 | [07-quality-agent-tvfs.md](07-quality-agent-tvfs.md), [by-domain/quality-domain.md](by-domain/quality-domain.md) |

### Appendices

| # | Document | Description |
|---|----------|-------------|
| A | [TVF Quick Reference](appendices/A-quick-reference.md) | TVF parameter reference |
| B | [TVF SQL Patterns](appendices/B-sql-patterns.md) | Common SQL patterns |
| C | [References](appendices/C-references.md) | Official documentation links |
| mv-A | [Metric Views Quick Reference](appendices/mv-A-quick-reference.md) | View dimensions/measures |
| mv-B | [YAML Patterns](appendices/mv-B-yaml-patterns.md) | Metric view YAML examples |
| mv-C | [Troubleshooting](appendices/mv-C-troubleshooting.md) | Common errors and solutions |

## TVF vs Metric View Comparison

| Aspect | TVFs | Metric Views |
|--------|------|--------------|
| **Use Case** | Specific, filtered queries | Aggregate analytics |
| **Parameters** | User-defined inputs | Pre-configured |
| **Invocation** | `SELECT * FROM TABLE(tvf(...))` | `SELECT MEASURE(...) FROM mv_*` |
| **Flexibility** | High (parameter-driven) | Lower (fixed dimensions/measures) |
| **Performance** | Query-time computation | Pre-defined aggregations |
| **Genie Usage** | For specific questions | For aggregate questions |
| **Dashboard Usage** | Less common | Primary use case |

### When to Use What

| Question Type | Use | Example |
|---------------|-----|---------|
| "Show top 10 cost drivers last week" | TVF | `get_top_cost_contributors('2024-01-01', '2024-01-07', 10)` |
| "What's total spend by workspace?" | Metric View | `SELECT workspace_name, MEASURE(total_cost) FROM mv_cost_analytics GROUP BY 1` |
| "Jobs that failed in the last hour" | TVF | `get_failed_jobs(1)` |
| "What's our overall success rate?" | Metric View | `SELECT MEASURE(success_rate) FROM mv_job_performance` |

## Metric Views Summary

| View | Domain | Source | Key Questions |
|------|--------|--------|---------------|
| `mv_cost_analytics` | Cost | `fact_usage` | Total spend, cost by workspace, SKU breakdown |
| `mv_commit_tracking` | Cost | `fact_usage` | Budget projection, burn rate |
| `mv_query_performance` | Performance | `fact_query_history` | Query latency, cache rates |
| `mv_cluster_utilization` | Performance | `fact_node_timeline` | CPU/memory utilization |
| `mv_cluster_efficiency` | Performance | `fact_node_timeline` | Efficiency score, idle time |
| `mv_job_performance` | Reliability | `fact_job_run_timeline` | Success rates, duration |
| `mv_security_events` | Security | `fact_audit_logs` | Audit events, user activity |
| `mv_governance_analytics` | Security | `fact_table_lineage` | Data lineage, access patterns |
| `mv_data_quality` | Quality | `information_schema` | Table freshness |
| `mv_ml_intelligence` | Quality | `cost_anomaly_predictions` | Cost anomalies |

## Directory Structure

```
docs/semantic-framework/
├── README.md                           # This file - unified entry point
│
├── TVF Documentation (00-07)
│   ├── 00-index.md                     # TVF index
│   ├── 01-introduction.md              # TVF introduction
│   ├── 02-architecture-overview.md     # TVF architecture
│   ├── 03-cost-agent-tvfs.md           # Cost domain TVFs
│   ├── 04-reliability-agent-tvfs.md    # Reliability domain TVFs
│   ├── 05-performance-agent-tvfs.md    # Performance domain TVFs
│   ├── 06-security-agent-tvfs.md       # Security domain TVFs
│   └── 07-quality-agent-tvfs.md        # Quality domain TVFs
│
├── Metric Views Documentation (20-24)
│   ├── 20-metric-views-index.md        # Metric views index
│   ├── 21-metric-views-introduction.md # Metric views introduction
│   ├── 22-metric-views-architecture.md # Metric views architecture
│   ├── 23-metric-views-deployment.md   # Deployment guide
│   └── 24-metric-views-reference.md    # Complete reference
│
├── by-domain/                          # Metric views by domain
│   ├── cost-domain.md
│   ├── performance-domain.md
│   ├── reliability-domain.md
│   ├── security-domain.md
│   └── quality-domain.md
│
└── appendices/                         # Reference materials
    ├── A-quick-reference.md            # TVF reference
    ├── B-sql-patterns.md               # TVF SQL patterns
    ├── C-references.md                 # External links
    ├── mv-A-quick-reference.md         # Metric view reference
    ├── mv-B-yaml-patterns.md           # YAML patterns
    └── mv-C-troubleshooting.md         # Troubleshooting
```

## Quick Start

### For TVFs
1. Read [01-introduction.md](01-introduction.md)
2. Follow [TVF deployment guide](appendices/A-quick-reference.md)
3. Test with examples from domain docs (03-07)

### For Metric Views
1. Read [21-metric-views-introduction.md](21-metric-views-introduction.md)
2. Follow [23-metric-views-deployment.md](23-metric-views-deployment.md)
3. Test with examples from [24-metric-views-reference.md](24-metric-views-reference.md)

## Related Documentation

- [Gold Layer Design](../../gold_layer_design/README.md)
- [Phase 3.2: TVF Plan](../../plans/phase3-addendum-3.2-tvfs.md)
- [Phase 3.3: Metric Views Plan](../../plans/phase3-addendum-3.3-metric-views.md)
- [Phase 3.6: Genie Spaces Plan](../../plans/phase3-addendum-3.6-genie-spaces.md)
- [Agent Framework Design](../agent-framework-design/00-index.md)
