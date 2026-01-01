# 24 - Metric Views Complete Reference

This document provides a comprehensive reference for all 10 deployed metric views in the Databricks Health Monitor semantic framework.

---

## Table of Contents

1. [Cost Domain](#cost-domain)
   - [mv_cost_analytics](#mv_cost_analytics)
   - [mv_commit_tracking](#mv_commit_tracking)
2. [Performance Domain](#performance-domain)
   - [mv_query_performance](#mv_query_performance)
   - [mv_cluster_utilization](#mv_cluster_utilization)
   - [mv_cluster_efficiency](#mv_cluster_efficiency)
3. [Reliability Domain](#reliability-domain)
   - [mv_job_performance](#mv_job_performance)
4. [Security Domain](#security-domain)
   - [mv_security_events](#mv_security_events)
   - [mv_governance_analytics](#mv_governance_analytics)
5. [Quality Domain](#quality-domain)
   - [mv_data_quality](#mv_data_quality)
   - [mv_ml_intelligence](#mv_ml_intelligence)

---

## Cost Domain

### mv_cost_analytics

**Purpose**: Comprehensive cost analytics for Databricks billing and usage analysis.

**Source Table**: `fact_usage` (billing domain)

**Joins**: `dim_workspace` (workspace details)

#### Best For
- Total spend by workspace
- Cost trend over time
- SKU cost breakdown
- Tagged vs untagged spend
- Serverless vs classic cost comparison

#### Not For
- Commit/contract tracking → use `mv_commit_tracking`
- Real-time cost alerts → use `get_daily_cost_summary` TVF

#### Key Dimensions (26 total)

| Dimension | Description | Synonyms |
|-----------|-------------|----------|
| `usage_date` | Date of usage record | date, billing date |
| `workspace_name` | Human-readable workspace name | workspace |
| `sku_name` | Product SKU category | sku, product |
| `entity_type` | Serverless/classic + product | compute type |
| `team_tag` | Team tag value | team |
| `project_tag` | Project tag value | project |
| `is_serverless` | Serverless compute flag | serverless |
| `tag_status` | Tagged/Untagged | tagging status |

#### Key Measures (30 total)

| Measure | Format | Description |
|---------|--------|-------------|
| `total_cost` | currency | Total USD cost |
| `total_dbu` | number | Total DBUs consumed |
| `tag_coverage_pct` | percentage | % of cost with tags |
| `serverless_ratio` | percentage | % serverless spend |
| `week_over_week_growth_pct` | percentage | WoW growth |
| `mtd_cost` | currency | Month-to-date cost |
| `ytd_cost` | currency | Year-to-date cost |
| `last_7_day_cost` | currency | Last 7 days |
| `prior_7_day_cost` | currency | Prior 7 days |
| `cost_per_dbu` | currency | Effective rate |

#### SQL Examples

```sql
-- Total cost by workspace (last 30 days)
SELECT 
    workspace_name,
    MEASURE(total_cost) as spend,
    MEASURE(total_dbu) as dbus,
    MEASURE(serverless_ratio) as serverless_pct
FROM mv_cost_analytics
WHERE usage_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY workspace_name
ORDER BY spend DESC;

-- Week-over-week growth by SKU
SELECT 
    sku_name,
    MEASURE(last_7_day_cost) as this_week,
    MEASURE(prior_7_day_cost) as last_week,
    MEASURE(week_over_week_growth_pct) as wow_growth
FROM mv_cost_analytics
GROUP BY sku_name
ORDER BY this_week DESC;

-- Tag coverage analysis
SELECT 
    tag_status,
    MEASURE(total_cost) as cost,
    MEASURE(tag_coverage_pct) as coverage
FROM mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY tag_status;
```

---

### mv_commit_tracking

**Purpose**: Budget and commitment tracking for FinOps.

**Source Table**: `fact_usage` (billing domain)

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `mtd_cost` | currency | Month-to-date cost |
| `projected_monthly_cost` | currency | Projected month-end |
| `daily_avg_cost` | currency | Average daily burn rate |
| `cost_per_dbu` | currency | Effective DBU rate |
| `ytd_cost` | currency | Year-to-date cost |
| `serverless_ratio` | percentage | Serverless adoption |

#### SQL Examples

```sql
-- Budget tracking summary
SELECT 
    MEASURE(mtd_cost) as mtd_spend,
    MEASURE(projected_monthly_cost) as projected,
    MEASURE(daily_avg_cost) as daily_burn,
    MEASURE(ytd_cost) as ytd_total
FROM mv_commit_tracking;

-- Monthly projection by workspace
SELECT 
    workspace_name,
    MEASURE(mtd_cost) as current_spend,
    MEASURE(projected_monthly_cost) as projected,
    MEASURE(serverless_ratio) as serverless_pct
FROM mv_commit_tracking
GROUP BY workspace_name
ORDER BY projected DESC;
```

---

## Performance Domain

### mv_query_performance

**Purpose**: SQL Warehouse query performance and efficiency metrics.

**Source Table**: `fact_query_history`

**Joins**: `dim_warehouse`, `dim_workspace`

#### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `warehouse_name` | SQL Warehouse name |
| `statement_type` | Query type (SELECT, INSERT) |
| `query_efficiency_status` | EFFICIENT/SLOW/HIGH_QUEUE/HIGH_SPILL |
| `user_name` | Query executor |

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `avg_duration_seconds` | number | Average query duration |
| `p95_duration_seconds` | number | 95th percentile latency |
| `p99_duration_seconds` | number | 99th percentile latency |
| `cache_hit_rate` | percentage | Cache efficiency % |
| `spill_rate` | percentage | Spill to disk % |
| `total_queries` | number | Query count |

#### SQL Examples

```sql
-- Query latency by warehouse
SELECT 
    warehouse_name,
    MEASURE(avg_duration_seconds) as avg_duration,
    MEASURE(p95_duration_seconds) as p95,
    MEASURE(p99_duration_seconds) as p99
FROM mv_query_performance
GROUP BY warehouse_name;

-- Cache performance
SELECT 
    warehouse_name,
    MEASURE(cache_hit_rate) as cache_pct,
    MEASURE(spill_rate) as spill_pct
FROM mv_query_performance
GROUP BY warehouse_name;
```

---

### mv_cluster_utilization

**Purpose**: Cluster resource utilization for capacity planning.

**Source Table**: `fact_node_timeline`

**Joins**: `dim_cluster`, `dim_workspace`

#### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `cluster_name` | Cluster name |
| `provisioning_status` | OPTIMAL/UNDERUTILIZED/OVERPROVISIONED |
| `savings_opportunity` | HIGH/MEDIUM/LOW |
| `workspace_name` | Workspace |

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `avg_cpu_utilization` | percentage | Average CPU % |
| `avg_memory_utilization` | percentage | Average memory % |
| `potential_savings_pct` | percentage | Estimated savings % |
| `wasted_hours` | number | Idle node hours |
| `total_node_hours` | number | Total node hours |

---

### mv_cluster_efficiency

**Purpose**: Advanced cluster efficiency and right-sizing analysis.

**Source Table**: `fact_node_timeline`

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `efficiency_score` | number | Combined efficiency (0-100) |
| `idle_percentage` | percentage | % time CPU < 10% |
| `underutilized_cluster_count` | number | Problem cluster count |
| `idle_node_hours_total` | number | Total wasted hours |

---

## Reliability Domain

### mv_job_performance

**Purpose**: Job execution reliability and efficiency metrics.

**Source Table**: `fact_job_run_timeline`

**Joins**: `dim_job`, `dim_workspace`

#### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `job_name` | Human-readable job name |
| `outcome_category` | SUCCESS/FAILURE/TIMEOUT/CANCELLED |
| `trigger_type` | PERIODIC/ONE_TIME/RETRY |
| `workspace_name` | Workspace |

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `success_rate` | percentage | % successful runs |
| `failure_rate` | percentage | % failed runs |
| `avg_duration_minutes` | number | Average runtime |
| `p95_duration_minutes` | number | P95 runtime |
| `total_runs` | number | Total executions |
| `failures_today` | number | Today's failures |

#### SQL Examples

```sql
-- Job success rates
SELECT 
    job_name,
    MEASURE(success_rate) as success_pct,
    MEASURE(failure_rate) as failure_pct,
    MEASURE(total_runs) as runs
FROM mv_job_performance
GROUP BY job_name
ORDER BY failure_pct DESC;

-- Duration percentiles
SELECT 
    job_name,
    MEASURE(avg_duration_minutes) as avg_min,
    MEASURE(p95_duration_minutes) as p95_min
FROM mv_job_performance
GROUP BY job_name;
```

---

## Security Domain

### mv_security_events

**Purpose**: Security and audit event analytics.

**Source Table**: `fact_audit_logs`

**Joins**: `dim_workspace`

#### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `user_email` | User identity |
| `user_type` | HUMAN/SERVICE_PRINCIPAL/SYSTEM |
| `action_category` | CREATE/READ/UPDATE/DELETE/PERMISSION |
| `is_sensitive_action` | Sensitive action flag |
| `service_name` | Databricks service |

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `total_events` | number | Total audit events |
| `failed_events` | number | Failed action count |
| `sensitive_events_24h` | number | Recent sensitive actions |
| `unique_users` | number | Distinct users |
| `event_growth_rate` | percentage | Day-over-day change % |

---

### mv_governance_analytics

**Purpose**: Data lineage and governance analytics.

**Source Table**: `fact_table_lineage`

**Joins**: `dim_workspace`

#### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `source_table_full_name` | Read table FQN |
| `target_table_full_name` | Write table FQN |
| `entity_type` | NOTEBOOK/JOB/PIPELINE |
| `activity_status` | ACTIVE/MODERATE/INACTIVE |

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `read_events` | number | Read operation counts |
| `write_events` | number | Write operation counts |
| `active_table_count` | number | Tables accessed in 30d |
| `inactive_table_count` | number | Stale tables |

---

## Quality Domain

### mv_data_quality

**Purpose**: Table freshness and data quality metrics.

**Source Table**: `information_schema.tables`

#### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `table_full_name` | Fully qualified name |
| `freshness_status` | FRESH/WARNING/STALE |
| `table_category` | FACT/DIMENSION/OTHER |
| `domain` | Inferred data domain |
| `table_schema` | Schema name |

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `freshness_rate` | percentage | % tables updated < 24h |
| `staleness_rate` | percentage | % tables > 48h old |
| `stale_tables` | number | Count of stale tables |
| `fresh_tables` | number | Count of fresh tables |
| `avg_hours_since_update` | number | Average table age |

#### SQL Examples

```sql
-- Freshness summary
SELECT 
    MEASURE(total_tables) as total,
    MEASURE(fresh_tables) as fresh,
    MEASURE(stale_tables) as stale,
    MEASURE(freshness_rate) as freshness_pct
FROM mv_data_quality
WHERE table_schema = 'gold';

-- Stale tables detail
SELECT 
    table_full_name,
    freshness_status,
    hours_since_update
FROM mv_data_quality
WHERE freshness_status = 'STALE'
ORDER BY hours_since_update DESC;
```

---

### mv_ml_intelligence

**Purpose**: ML-powered anomaly detection insights.

**Source Table**: `cost_anomaly_predictions` (requires ML pipeline)

**Joins**: `dim_workspace`, `fact_usage`

#### Prerequisites

⚠️ **Requires ML inference pipeline to run first**:

```bash
databricks bundle run -t dev ml_inference_pipeline
```

#### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `is_anomaly` | Anomaly flag (BIGINT: 0/1) |
| `risk_level` | CRITICAL/HIGH/MEDIUM/LOW |
| `workspace_name` | Workspace |
| `sku_name` | Product SKU |
| `prediction_date` | Prediction date |

#### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `total_predictions` | number | Total predictions |
| `anomaly_count` | number | Flagged anomalies |
| `anomaly_rate` | percentage | % predictions flagged |
| `avg_anomaly_score` | number | Average score (0-1) |
| `high_risk_count` | number | Score >= 0.7 |
| `critical_count` | number | Score >= 0.9 |
| `anomaly_cost` | currency | Cost of anomalies |

#### Technical Note

The `is_anomaly` column is **BIGINT** (not BOOLEAN). Use `= 1` comparisons:

```yaml
# CORRECT
anomaly_count: SUM(CASE WHEN source.is_anomaly = 1 THEN 1 ELSE 0 END)

# WRONG (causes DATATYPE_MISMATCH error)
anomaly_count: SUM(CASE WHEN source.is_anomaly THEN 1 ELSE 0 END)
```

#### SQL Examples

```sql
-- Anomaly summary
SELECT 
    MEASURE(total_predictions) as predictions,
    MEASURE(anomaly_count) as anomalies,
    MEASURE(anomaly_rate) as anomaly_pct,
    MEASURE(avg_anomaly_score) as avg_score
FROM mv_ml_intelligence;

-- High-risk anomalies by workspace
SELECT 
    workspace_name,
    MEASURE(high_risk_count) as high_risk,
    MEASURE(critical_count) as critical,
    MEASURE(anomaly_cost) as cost_impact
FROM mv_ml_intelligence
WHERE risk_level IN ('CRITICAL', 'HIGH')
GROUP BY workspace_name
ORDER BY cost_impact DESC;

-- Anomaly trend
SELECT 
    prediction_date,
    MEASURE(anomaly_count) as anomalies,
    MEASURE(anomaly_rate) as rate_pct
FROM mv_ml_intelligence
WHERE prediction_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY prediction_date
ORDER BY prediction_date;
```

---

## Quick Reference Table

| View | Domain | Source | Dims | Measures | ML Required |
|------|--------|--------|------|----------|-------------|
| `mv_cost_analytics` | Cost | `fact_usage` | 26 | 30 | No |
| `mv_commit_tracking` | Cost | `fact_usage` | 10 | 12 | No |
| `mv_query_performance` | Performance | `fact_query_history` | 15 | 18 | No |
| `mv_cluster_utilization` | Performance | `fact_node_timeline` | 12 | 14 | No |
| `mv_cluster_efficiency` | Performance | `fact_node_timeline` | 8 | 10 | No |
| `mv_job_performance` | Reliability | `fact_job_run_timeline` | 14 | 16 | No |
| `mv_security_events` | Security | `fact_audit_logs` | 16 | 12 | No |
| `mv_governance_analytics` | Security | `fact_table_lineage` | 10 | 8 | No |
| `mv_data_quality` | Quality | `information_schema` | 8 | 10 | No |
| `mv_ml_intelligence` | Quality | `cost_anomaly_predictions` | 10 | 14 | **Yes** |

---

## Related Documentation

- [20-Metric Views Index](20-metric-views-index.md)
- [21-Metric Views Introduction](21-metric-views-introduction.md)
- [22-Metric Views Architecture](22-metric-views-architecture.md)
- [23-Metric Views Deployment](23-metric-views-deployment.md)
- [Domain-Specific Guides](by-domain/)

