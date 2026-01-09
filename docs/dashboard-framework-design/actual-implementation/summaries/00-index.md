# Dashboard Actual Implementation Documentation

## Overview

This folder contains comprehensive documentation of the **actual implementation** of the Databricks Health Monitor dashboards. Unlike the design specifications, this documentation reflects the **real metrics, queries, and data sources** currently deployed.

---

## Organization Structure

Documentation is organized by **domain** (Cost, Reliability, Performance, Quality, Security) with each domain containing:

1. **Metrics Reference** - All KPIs, scores, and measures tracked
2. **Dataset Catalog** - Complete listing of all datasets with purposes
3. **SQL Query Library** - All SQL queries used, categorized by function
4. **Data Source Mapping** - Which Gold/Silver tables power each metric
5. **ML Model Integration** - How ML predictions are incorporated
6. **Lakehouse Monitoring** - Custom metrics and drift detection

---

## Domain Files

### [01-cost-domain.md](01-cost-domain.md)
**59 datasets** covering:
- Daily/Monthly spend analytics
- Budget tracking and forecasting
- Tag compliance and governance
- Serverless adoption metrics
- Cost optimization opportunities
- Commitment utilization
- Drift detection

**Key Tables:** `fact_usage`, `fact_usage_profile_metrics`, `fact_usage_drift_metrics`

---

### [02-reliability-domain.md](02-reliability-domain.md)
**51 datasets** covering:
- Job success/failure rates
- Pipeline health monitoring
- Retry and self-healing patterns
- Incident impact analysis
- Duration forecasting
- ML failure risk predictions
- Drift detection

**Key Tables:** `fact_job_run_timeline`, `fact_job_run_timeline_profile_metrics`, `fact_job_run_timeline_drift_metrics`, `dim_job`, `dim_workspace`

---

### [03-performance-domain.md](03-performance-domain.md)
**48 datasets** covering:
- Query performance analytics
- Slow query identification
- Warehouse utilization
- Cluster CPU/memory metrics
- Right-sizing recommendations
- Performance regression detection
- ML optimization predictions

**Key Tables:** `fact_query_history`, `fact_node_timeline`, `fact_cluster_timeline`

---

### [04-quality-domain.md](04-quality-domain.md)
**39 datasets** covering:
- Table governance (tags, documentation)
- Data quality scores
- Lineage tracking
- Catalog/schema statistics
- Undocumented tables
- Compaction needs
- Table usage patterns

**Key Tables:** `system.information_schema.tables`, `system.information_schema.columns`, `system.information_schema.table_tags`, `fact_table_lineage`, `fact_query_history`

---

### [05-security-domain.md](05-security-domain.md)
**44 datasets** covering:
- Audit event monitoring
- Access control analytics
- Failed access attempts
- High-risk events
- User behavior patterns
- Security anomaly detection
- Compliance metrics

**Key Tables:** `fact_audit_logs`, `fact_audit_logs_profile_metrics`, `fact_audit_logs_drift_metrics`, `dim_workspace`, `dim_user`

---

### [06-unified-domain.md](06-unified-domain.md)
**Cross-domain overview dashboard** with:
- Health score aggregation across domains
- Executive KPI summary
- Domain health status
- Critical alert aggregation
- Trend sparklines

**Key Tables:** Aggregates from all domain fact tables

---

## Quick Reference: Metric Categories

### Financial Metrics (Cost Domain)
- `total_cost` - Total DBU list price cost
- `total_dbus` - Total DBUs consumed
- `tag_coverage_percentage` - % of cost with tags
- `serverless_percentage` - % of cost from serverless
- `cost_drift_pct` - Week-over-week cost change

### Reliability Metrics (Reliability Domain)
- `success_rate` - Job success percentage
- `failure_rate` - Job failure percentage
- `avg_duration_seconds` - Average job runtime
- `mttr_hours` - Mean time to recovery
- `incident_count` - Failed job count

### Performance Metrics (Performance Domain)
- `avg_duration_ms` - Average query duration
- `p95_duration_ms` - 95th percentile latency
- `total_queries` - Query volume
- `avg_cpu_utilization_pct` - Cluster CPU usage
- `avg_memory_utilization_pct` - Cluster memory usage

### Quality Metrics (Quality Domain)
- `total_tables` - Table count by catalog
- `tagged_tables` - Tables with governance tags
- `documented_tables` - Tables with descriptions
- `quality_score` - Overall data quality percentage
- `lineage_depth` - Dependency chain length

### Security Metrics (Security Domain)
- `total_events` - Audit event count
- `failed_events` - Failed access attempts
- `high_risk_events` - Critical security events
- `unique_users` - Active user count
- `compliance_score` - Security posture percentage

---

## How to Use This Documentation

### For Dashboard Development
1. Find the domain you're working on
2. Review the metrics catalog to understand what's measured
3. Use the SQL query library to see actual implementations
4. Check data source mapping to understand table dependencies

### For Data Engineering
1. Identify which Gold tables power which dashboards
2. Understand query patterns and optimization opportunities
3. Review join patterns and filter logic
4. See how custom metrics are calculated

### For Analytics
1. Understand metric definitions and calculations
2. Learn which filters and parameters are available
3. See how time windows and aggregations work
4. Understand drift detection methodologies

### For ML Engineering
1. Review ML model integration patterns
2. Understand prediction columns used in dashboards
3. See how model outputs drive recommendations
4. Identify feature engineering patterns

---

## Common Patterns

### Time Windows
```sql
-- Last 30 days
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS

-- Month-to-date
WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())

-- Last 90 days for trends
WHERE start_time >= CURRENT_DATE() - INTERVAL 90 DAYS
```

### Lakehouse Monitoring Metrics
```sql
-- Profile metrics (aggregated)
FROM ${catalog}.${gold_schema}.fact_${domain}_profile_metrics

-- Drift metrics (week-over-week)
FROM ${catalog}.${gold_schema}.fact_${domain}_drift_metrics

-- Custom metrics by slice
WHERE column_name = ':table' -- Table-level metrics
WHERE column_name != ':table' -- Column-level metrics
```

### ML Predictions
```sql
-- Prediction columns
prediction -- Main prediction value
probability -- Confidence score
anomaly_score -- Anomaly detection
risk_category -- Classification (High/Medium/Low)
```

### User Lookup Pattern
```sql
-- Owner resolution
LEFT JOIN ${catalog}.${gold_schema}.dim_user u
  ON COALESCE(j.run_as, j.creator_id) = u.user_id

-- Display name
COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner
```

---

## Metadata Summary

| Domain | Datasets | Key Tables | ML Models | Monitors |
|--------|----------|------------|-----------|----------|
| **Cost** | 59 | 3 | 4 | 1 |
| **Reliability** | 51 | 4 | 5 | 1 |
| **Performance** | 48 | 3 | 4 | 2 |
| **Quality** | 39 | 5 | 0 | 2 |
| **Security** | 44 | 3 | 2 | 1 |
| **Unified** | 24 | All | N/A | N/A |
| **TOTAL** | **265** | **12** | **15** | **7** |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial documentation of deployed dashboards |

---

## Related Documentation

- [Design Specifications](../) - Original dashboard design documents
- [Gold Layer Schema](../../../gold_layer_design/) - Table definitions
- [ML Models](../../../docs/ml/) - Model documentation
- [Lakehouse Monitoring](../../../docs/monitoring/) - Monitor setup guides

