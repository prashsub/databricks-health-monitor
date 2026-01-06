# 01 - Introduction

## Purpose

The Lakehouse Monitoring system provides **automated, continuous observation** of Databricks Health Monitor Gold layer tables. It serves three critical functions:

1. **Automated Data Quality Tracking**: Monitor data completeness, freshness, and consistency without manual intervention
2. **Business Metric Computation**: Calculate domain-specific KPIs (success rates, cost efficiency, utilization) automatically
3. **Drift Detection**: Identify period-over-period changes that may indicate issues requiring attention

This system enables **proactive platform health management** by surfacing insights through:
- Scheduled metric computation at configurable granularities
- Period-over-period drift detection for trend analysis
- Genie-ready documentation for natural language queries
- SQL-based alerting integration for automated notifications

## Scope

### In Scope

- **8 Gold Layer Fact Tables**: All major fact tables from the Health Monitor Gold layer
- **5 Agent Domains**: Cost, Performance, Reliability, Security, Quality
- **300+ Custom Metrics**: Business-aligned KPIs computed automatically
- **Genie Integration**: LLM-friendly table and column documentation
- **Asset Bundle Deployment**: YAML-driven, serverless job configuration
- **Scheduled Refresh**: Daily automated metric refresh capability
- **Drift Detection**: Automatic period-over-period comparison

### Out of Scope

- **Real-time Monitoring**: This is batch-based (minimum 1-hour granularity)
- **Dimension Tables**: Monitors are for fact tables only
- **Custom Dashboards**: Dashboard creation is separate from monitoring
- **Alert Configuration**: SQL Alerts are configured separately
- **ML Model Drift**: Model performance drift is tracked via inference monitor, not ML-specific drift

## Prerequisites

### Completed Components

| Component | Count | Status | Documentation |
|-----------|-------|--------|---------------|
| **Gold Layer Tables** | 8 fact tables | Required | [Gold Layer Design](../gold/GOLD_LAYER_PROGRESS.md) |
| **Bronze Layer Ingestion** | System tables | Required | [Phase 1 Plan](../../plans/phase1-bronze-ingestion.md) |
| **Silver Layer Processing** | DLT pipelines | Required | [Silver Pipeline](../../src/pipelines/) |
| **Unity Catalog** | Catalog/Schema setup | Required | [Schema Management](../../.cursor/rules/common/03-schema-management-patterns.mdc) |

### Infrastructure Requirements

| Requirement | Specification |
|-------------|---------------|
| **Databricks Runtime** | 13.3 LTS or later |
| **Databricks SDK** | ≥0.28.0 (for Lakehouse Monitoring API) |
| **Compute** | Serverless (recommended) or shared cluster |
| **Unity Catalog** | Enabled with write access to Gold schema |
| **Workspace Permissions** | MANAGE permission on monitored tables |

### Required Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| **SELECT** | Gold layer tables | Read source data for monitoring |
| **MANAGE** | Gold layer tables | Create/modify monitors |
| **CREATE TABLE** | `{gold_schema}_monitoring` | Create output tables |
| **ALTER** | Monitoring output tables | Add Genie documentation |
| **USE CATALOG** | Target catalog | Access Unity Catalog |
| **USE SCHEMA** | Gold and monitoring schemas | Access schemas |

## Best Practices Matrix

| # | Best Practice | Implementation | Document |
|---|---------------|----------------|----------|
| 1 | **Table-Level Aggregation** | All metrics use `input_columns=[":table"]` for cross-column business KPIs | [03-Custom Metrics](03-custom-metrics.md#table-level-aggregation) |
| 2 | **Three Metric Types** | AGGREGATE (base), DERIVED (ratios), DRIFT (change) pattern | [03-Custom Metrics](03-custom-metrics.md#metric-types) |
| 3 | **Complete Cleanup** | Delete monitor + drop output tables before recreation | [06-Implementation](06-implementation-guide.md#cleanup-pattern) |
| 4 | **Schema Pre-Creation** | Create `{gold_schema}_monitoring` schema before monitor | [06-Implementation](06-implementation-guide.md#schema-creation) |
| 5 | **Genie Documentation** | Add descriptions 15+ min after monitor creation | [05-Genie Integration](05-genie-integration.md) |
| 6 | **Pure Python Utils** | `monitor_utils.py` without notebook header for imports | [02-Architecture](02-architecture-overview.md#code-organization) |
| 7 | **Serverless Deployment** | All jobs use serverless compute for cost efficiency | [06-Implementation](06-implementation-guide.md#deployment) |
| 8 | **Full Config Updates** | Never omit `custom_metrics` in updates (deletes all!) | [07-Operations](07-operations-guide.md#update-behavior) |

## Development Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. **Design** | 1 day | Metric definitions, schema design |
| 2. **Utilities** | 1 day | `monitor_utils.py` with helpers |
| 3. **Monitor Implementation** | 2 days | 8 monitor notebooks with metrics |
| 4. **Genie Documentation** | 1 day | 100+ metric descriptions, documentation job |
| 5. **Deployment** | 1 day | Asset Bundle YAML, testing |
| 6. **Documentation** | 1 day | This documentation set |
| **Total** | **7 days** | Complete monitoring system |

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Monitor Coverage** | 100% of Gold fact tables | 8/8 tables monitored |
| **Metric Count** | ≥30 per monitor | Average 40+ metrics |
| **Genie Understanding** | Natural language queries work | Test with 10 sample questions |
| **Deployment Success** | Zero errors on deploy | Asset Bundle validation passes |
| **Documentation Coverage** | 100% of custom metrics | All metrics have descriptions |
| **Drift Detection** | Enabled for all monitors | Drift tables populated |

## Document Conventions

### Code Examples

All code examples in this documentation are:
- **Production-ready**: Can be copied and used directly
- **Complete**: Include all imports and error handling
- **Tested**: Validated in Databricks workspace

### Diagrams

- **ASCII Art**: Used for text-based documentation
- **Mermaid**: Used where rendered (GitHub, Databricks notebooks)

### Configuration

- **Parameterized**: All catalog/schema values use variables
- **Environment-aware**: `${bundle.target}` for dev/prod
- **Secrets**: No hardcoded credentials

## Monitor Summary

| Monitor | Gold Table | Domain | Metrics | Schedule |
|---------|------------|--------|---------|----------|
| **Cost** | `fact_usage` | 💰 Cost | 35 | Daily 6 AM |
| **Job** | `fact_job_run_timeline` | 🔄 Reliability | 50 | Hourly |
| **Query** | `fact_query_history` | ⚡ Performance | 40 | Hourly |
| **Cluster** | `fact_node_timeline` | ⚡ Performance | 40 | Hourly |
| **Security** | `fact_audit_logs` | 🔒 Security | 15 | Hourly |
| **Quality** | `fact_table_quality` | ✅ Quality | 15 | Daily |
| **Governance** | `fact_governance_metrics` | 📊 Quality | 15 | Daily |
| **Inference** | `fact_model_serving` | 🤖 ML | 15 | Hourly |

## Next Steps

1. **Read [02-Architecture Overview](02-architecture-overview.md)** to understand the system design
2. **Review [03-Custom Metrics](03-custom-metrics.md)** for metric patterns
3. **Explore [04-Monitor Catalog](04-monitor-catalog.md)** for complete metric inventory
4. **Follow [06-Implementation Guide](06-implementation-guide.md)** for step-by-step setup

---

**Version:** 1.0  
**Last Updated:** January 2026




