# Semantic Framework Documentation

## Overview

This documentation suite provides comprehensive reference for the **Databricks Health Monitor Semantic Framework** - a portfolio of 60 Table-Valued Functions (TVFs) that enable natural language data queries through Genie Spaces. These TVFs encapsulate complex analytical patterns with LLM-friendly metadata.

## Architecture Principle

> **TVFs are the semantic layer between Genie Spaces and Gold layer tables.**
> They provide parameterized, documented queries that Genie can invoke based on natural language questions.

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 01 | [Introduction](01-introduction.md) | Purpose, scope, prerequisites, design patterns |
| 02 | [Architecture Overview](02-architecture-overview.md) | System architecture, data flow, SQL patterns |
| 03 | [Cost Agent TVFs](03-cost-agent-tvfs.md) | 15 TVFs for cost analysis, chargeback, attribution |
| 04 | [Reliability Agent TVFs](04-reliability-agent-tvfs.md) | 12 TVFs for job health, SLA tracking, failure analysis |
| 05 | [Performance Agent TVFs](05-performance-agent-tvfs.md) | 16 TVFs for query performance, compute optimization |
| 06 | [Security Agent TVFs](06-security-agent-tvfs.md) | 10 TVFs for audit analysis, access patterns, risk scoring |
| 07 | [Quality Agent TVFs](07-quality-agent-tvfs.md) | 7 TVFs for data freshness, lineage, governance |
| 08 | [Deployment Guide](08-deployment-guide.md) | How to deploy and verify TVFs |
| 09 | [Usage Examples](09-usage-examples.md) | Example natural language queries and SQL invocations |

## Appendices

| # | Document | Description |
|---|----------|-------------|
| A | [Quick Reference](appendices/A-quick-reference.md) | Complete TVF reference table with parameters |
| B | [SQL Patterns](appendices/B-sql-patterns.md) | Common SQL patterns used in TVFs |
| C | [References](appendices/C-references.md) | Official documentation links |

## TVF Summary by Domain

```
SEMANTIC FRAMEWORK (60 TVFs)
├── 💰 COST AGENT (15 TVFs)
│   ├── Cost attribution and chargeback
│   ├── Tag-based allocation
│   ├── Trend analysis and forecasting
│   └── Anomaly detection
│
├── 🔄 RELIABILITY AGENT (12 TVFs)
│   ├── Job success rates and failure analysis
│   ├── SLA compliance tracking
│   ├── Duration percentiles
│   └── Repair cost analysis
│
├── ⚡ PERFORMANCE AGENT (16 TVFs)
│   ├── Query performance (10 TVFs)
│   │   ├── Slow query identification
│   │   ├── Warehouse utilization
│   │   └── Latency percentiles
│   └── Compute optimization (6 TVFs)
│       ├── Cluster utilization
│       ├── Right-sizing recommendations
│       └── Autoscaling analysis
│
├── 🔒 SECURITY AGENT (10 TVFs)
│   ├── User activity and risk scoring
│   ├── Table access audit
│   ├── Permission change tracking
│   └── Service account monitoring
│
└── 📋 QUALITY AGENT (7 TVFs)
    ├── Table freshness monitoring
    ├── Data lineage tracking
    └── Governance reporting
```

## Quick Start

1. **Understand the Architecture**: Start with [02-architecture-overview.md](02-architecture-overview.md)
2. **Deploy TVFs**: Follow [08-deployment-guide.md](08-deployment-guide.md)
3. **Test with Examples**: Try queries from [09-usage-examples.md](09-usage-examples.md)
4. **Reference Specific TVFs**: Navigate to domain-specific docs (03-07)

## SQL File Locations

```
src/semantic/tvfs/
├── cost_tvfs.sql          # 15 cost analysis TVFs
├── reliability_tvfs.sql   # 12 reliability monitoring TVFs
├── performance_tvfs.sql   # 10 query performance TVFs
├── compute_tvfs.sql       # 6 compute optimization TVFs
├── security_tvfs.sql      # 10 security audit TVFs
└── quality_tvfs.sql       # 7 data quality TVFs
```

## Design Patterns Showcased

| # | Pattern | Implementation |
|---|---------|----------------|
| 1 | **STRING Date Parameters** | Genie-compatible date handling with CAST |
| 2 | **Required-First Parameters** | Parameters without DEFAULT come before optional |
| 3 | **ROW_NUMBER Top N** | Use WHERE rank <= param instead of LIMIT param |
| 4 | **NULLIF Division Safety** | All divisions use NULLIF(denominator, 0) |
| 5 | **LLM-Friendly Comments** | Structured PURPOSE/BEST FOR/NOT FOR/PARAMS comments |
| 6 | **SCD2 Dimension Joins** | Filter with delete_time IS NULL for current records |
| 7 | **Composite Key Handling** | Join on workspace_id + entity_id for dimensions |
| 8 | **PERCENTILE_APPROX** | Use approximate percentiles for performance |

## Related Documentation

- [Agent Framework Design](../agent-framework-design/)
- [Gold Layer Design](../../gold_layer_design/design/00_design_overview.md)
- [Phase 3.2 TVF Plan](../../plans/phase3-addendum-3.2-tvfs.md)
- [Genie Spaces Plan](../../plans/phase3-addendum-3.6-genie-spaces.md)

