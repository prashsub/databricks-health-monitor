# 21 - Metric Views Introduction

## Purpose

Metric Views provide a **semantic layer** over Gold layer fact tables, enabling natural language queries through Genie Spaces and efficient aggregate analytics for AI/BI dashboards. Unlike TVFs which accept parameters for filtered queries, Metric Views define pre-configured dimensions and measures that support MEASURE() aggregation functions.

## Scope

### In Scope

- **Cost Analytics**: Billing analysis, tag-based attribution, trend tracking
- **Performance Analytics**: Query latency, cluster utilization, efficiency metrics
- **Reliability Analytics**: Job success rates, duration percentiles, failure analysis
- **Security Analytics**: Audit events, governance tracking, access patterns
- **Quality Analytics**: Data freshness, ML anomaly detection

### Out of Scope

- Parameterized queries (use TVFs instead)
- Real-time streaming metrics (batch aggregation only)
- Raw system table access (Gold layer abstraction)
- Custom ad-hoc calculations (pre-defined measures only)

## Prerequisites

### Required Components

| Component | Count | Status | Documentation |
|-----------|-------|--------|---------------|
| Gold Layer Fact Tables | 6 | Required | [Gold Layer Design](../../gold_layer_design/) |
| Gold Layer Dimension Tables | 5 | Required | [Gold Layer Design](../../gold_layer_design/) |
| Unity Catalog | 1 | Required | Databricks workspace |
| SQL Warehouse | 1 | Required | Serverless recommended |
| ML Inference Pipeline | 1 | Optional | For `mv_ml_intelligence` |

### Gold Layer Tables Used

**Fact Tables (Sources)**:
- `fact_usage` - Billing and cost data
- `fact_job_run_timeline` - Job execution history
- `fact_query_history` - SQL query metrics
- `fact_audit_logs` - Security audit events
- `fact_node_timeline` - Cluster node metrics
- `fact_table_lineage` - Data lineage events
- `cost_anomaly_predictions` - ML prediction output

**Dimension Tables (Joins)**:
- `dim_workspace` - Workspace metadata
- `dim_job` - Job definitions
- `dim_warehouse` - SQL Warehouse metadata
- `dim_cluster` - Cluster configurations

### Infrastructure Requirements

| Requirement | Specification |
|-------------|---------------|
| Databricks Runtime | SQL Warehouse (any version) |
| Unity Catalog | Enabled with SELECT permissions |
| Metric Views | Databricks workspace feature enabled |
| YAML Parser | PyYAML library |

## Design Principles

### 1. v1.1 YAML Specification

All metric views use the Databricks Metric Views v1.1 specification:

```yaml
version: "1.1"
comment: >
  PURPOSE: What this view provides
  BEST FOR: Questions it answers well
  NOT FOR: Questions to redirect elsewhere

source: catalog.schema.fact_table

joins:
  - name: dim_table
    source: catalog.schema.dim_table
    'on': source.fk = dim_table.pk AND dim_table.is_current = true

dimensions:
  - name: dimension_name
    expr: source.column
    comment: Business description
    display_name: User-Friendly Name
    synonyms: [alt1, alt2, alt3]

measures:
  - name: measure_name
    expr: SUM(source.column)
    comment: Business description
    format:
      type: currency|number|percentage
```

### 2. Naming Convention

All metric views use the `mv_` prefix for discoverability:

```
{catalog}.{gold_schema}.mv_{view_name}

Example: health_monitor.gold.mv_cost_analytics
```

### 3. LLM-Friendly Comments

Every metric view includes structured comments optimized for Genie:

```yaml
comment: >
  PURPOSE: Comprehensive cost analytics for Databricks billing.
  
  BEST FOR: Total spend by workspace | Cost trend over time | SKU breakdown
  
  NOT FOR: Commit tracking (use mv_commit_tracking) | Real-time alerts (use TVF)
  
  DIMENSIONS: usage_date, workspace_name, sku_name, entity_type
  
  MEASURES: total_cost, total_dbu, tag_coverage_pct, serverless_ratio
  
  SOURCE: fact_usage (billing domain)
  
  JOINS: dim_workspace (workspace details)
  
  NOTE: Cost values are list prices. Actual billed amounts may vary.
```

### 4. SCD2 Dimension Joins

All dimension joins include current record filtering:

```yaml
joins:
  - name: dim_workspace
    source: catalog.schema.dim_workspace
    'on': source.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
```

### 5. Null-Safe Calculations

All percentage and ratio calculations use NULLIF for safety:

```yaml
measures:
  - name: tag_coverage_pct
    expr: (SUM(CASE WHEN is_tagged THEN cost ELSE 0 END) * 100.0) / NULLIF(SUM(cost), 0)
```

### 6. Format Specifications

Measures include proper format hints for display:

```yaml
# Currency
format:
  type: currency
  currency_code: USD
  decimal_places:
    type: exact
    places: 2
  abbreviation: compact  # Shows 1.5M

# Percentage
format:
  type: percentage
  decimal_places:
    type: exact
    places: 1

# Number
format:
  type: number
  abbreviation: compact
```

## Metric Views Inventory

| Domain | Views | Primary Source | Key Measures |
|--------|-------|----------------|--------------|
| Cost | 2 | `fact_usage` | total_cost, total_dbu, tag_coverage_pct |
| Performance | 3 | `fact_query_history`, `fact_node_timeline` | avg_duration, p95_latency, cache_hit_rate |
| Reliability | 1 | `fact_job_run_timeline` | success_rate, failure_rate, avg_duration |
| Security | 2 | `fact_audit_logs`, `fact_table_lineage` | total_events, failed_events, active_tables |
| Quality | 2 | `information_schema`, `cost_anomaly_predictions` | freshness_rate, anomaly_rate |
| **Total** | **10** | | |

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Metric view deployment | 100% | All 10 views deploy successfully |
| Documentation coverage | 100% | Every view has structured comment |
| Genie compatibility | 100% | All views queryable via Genie |
| Format correctness | 100% | Currency/percentage display properly |
| Query performance | <5s | Average MEASURE() query time |

## Next Steps

1. **Read [22-Metric Views Architecture](22-metric-views-architecture.md)** to understand the data flow
2. **Review domain-specific docs** for detailed view specifications
3. **Follow [23-Metric Views Deployment](23-metric-views-deployment.md)** to deploy views
4. **Use [24-Metric Views Reference](24-metric-views-reference.md)** for quick lookup
