# Appendix A - Metric Views Quick Reference

## All Metric Views at a Glance

| View Name | Domain | Source Table | Key Question |
|-----------|--------|--------------|--------------|
| `mv_cost_analytics` | Cost | `fact_usage` | "What's our total spend?" |
| `mv_commit_tracking` | Cost | `fact_usage` | "What's our projected monthly cost?" |
| `mv_query_performance` | Performance | `fact_query_history` | "What's our query P95 latency?" |
| `mv_cluster_utilization` | Performance | `fact_node_timeline` | "Which clusters are underutilized?" |
| `mv_cluster_efficiency` | Performance | `fact_node_timeline` | "What's our efficiency score?" |
| `mv_job_performance` | Reliability | `fact_job_run_timeline` | "What's our job success rate?" |
| `mv_security_events` | Security | `fact_audit_logs` | "Who accessed this resource?" |
| `mv_governance_analytics` | Security | `fact_table_lineage` | "Show data lineage" |
| `mv_data_quality` | Quality | `information_schema` | "Which tables are stale?" |
| `mv_ml_intelligence` | Quality | `cost_anomaly_predictions` | "What anomalies were detected?" |

## Dimensions by Domain

### Cost Domain

| View | Dimensions |
|------|------------|
| `mv_cost_analytics` | usage_date, workspace_name, sku_name, entity_type, team_tag, project_tag, cost_center_tag, env_tag, is_serverless, tag_status, billing_origin_product, ... (26 total) |
| `mv_commit_tracking` | usage_date, workspace_name, sku_name, is_serverless (10 total) |

### Performance Domain

| View | Dimensions |
|------|------------|
| `mv_query_performance` | warehouse_name, statement_type, query_efficiency_status, user_name, workspace_name (15 total) |
| `mv_cluster_utilization` | cluster_name, provisioning_status, savings_opportunity, workspace_name (12 total) |
| `mv_cluster_efficiency` | cluster_name, efficiency_category, workspace_name (8 total) |

### Reliability Domain

| View | Dimensions |
|------|------------|
| `mv_job_performance` | job_name, outcome_category, trigger_type, workspace_name, run_date (14 total) |

### Security Domain

| View | Dimensions |
|------|------------|
| `mv_security_events` | user_email, user_type, action_category, service_name, is_sensitive_action, workspace_name (16 total) |
| `mv_governance_analytics` | source_table_full_name, target_table_full_name, entity_type, activity_status (10 total) |

### Quality Domain

| View | Dimensions |
|------|------------|
| `mv_data_quality` | table_full_name, freshness_status, table_category, domain, table_schema (8 total) |
| `mv_ml_intelligence` | is_anomaly, risk_level, workspace_name, sku_name, prediction_date, model_version (10 total) |

## Measures by Domain

### Cost Domain

| View | Measure | Format | Description |
|------|---------|--------|-------------|
| `mv_cost_analytics` | total_cost | currency | Total USD cost |
| `mv_cost_analytics` | total_dbu | number | Total DBUs consumed |
| `mv_cost_analytics` | tag_coverage_pct | percentage | % cost with tags |
| `mv_cost_analytics` | serverless_ratio | percentage | % serverless spend |
| `mv_cost_analytics` | week_over_week_growth_pct | percentage | WoW growth |
| `mv_commit_tracking` | projected_monthly_cost | currency | Projected month-end |
| `mv_commit_tracking` | daily_avg_cost | currency | Daily burn rate |

### Performance Domain

| View | Measure | Format | Description |
|------|---------|--------|-------------|
| `mv_query_performance` | avg_duration_seconds | number | Avg query duration |
| `mv_query_performance` | p95_duration_seconds | number | P95 latency |
| `mv_query_performance` | cache_hit_rate | percentage | Cache efficiency |
| `mv_cluster_utilization` | avg_cpu_utilization | percentage | Avg CPU % |
| `mv_cluster_utilization` | potential_savings_pct | percentage | Est. savings |
| `mv_cluster_efficiency` | efficiency_score | number | 0-100 score |

### Reliability Domain

| View | Measure | Format | Description |
|------|---------|--------|-------------|
| `mv_job_performance` | success_rate | percentage | % successful |
| `mv_job_performance` | failure_rate | percentage | % failed |
| `mv_job_performance` | avg_duration_minutes | number | Avg runtime |
| `mv_job_performance` | p95_duration_minutes | number | P95 runtime |

### Security Domain

| View | Measure | Format | Description |
|------|---------|--------|-------------|
| `mv_security_events` | total_events | number | Event count |
| `mv_security_events` | failed_events | number | Failed actions |
| `mv_security_events` | sensitive_events_24h | number | Recent sensitive |
| `mv_governance_analytics` | active_table_count | number | Active tables |

### Quality Domain

| View | Measure | Format | Description |
|------|---------|--------|-------------|
| `mv_data_quality` | freshness_rate | percentage | % fresh tables |
| `mv_data_quality` | stale_tables | number | Stale count |
| `mv_ml_intelligence` | anomaly_rate | percentage | % anomalies |
| `mv_ml_intelligence` | anomaly_cost | currency | Anomaly cost |

## SQL Query Templates

### Basic MEASURE Query

```sql
SELECT 
    {dimension},
    MEASURE({measure}) as {alias}
FROM {metric_view}
GROUP BY {dimension};
```

### Multiple Measures

```sql
SELECT 
    {dimension},
    MEASURE({measure1}) as {alias1},
    MEASURE({measure2}) as {alias2},
    MEASURE({measure3}) as {alias3}
FROM {metric_view}
WHERE {filter_condition}
GROUP BY {dimension}
ORDER BY {alias1} DESC;
```

### Date-Filtered Query

```sql
SELECT 
    {date_dimension},
    MEASURE({measure}) as {alias}
FROM {metric_view}
WHERE {date_dimension} >= CURRENT_DATE - INTERVAL {n} DAYS
GROUP BY {date_dimension}
ORDER BY {date_dimension};
```

## One-Liner Examples per View

```sql
-- mv_cost_analytics: Total spend by workspace
SELECT workspace_name, MEASURE(total_cost) as spend FROM mv_cost_analytics GROUP BY 1;

-- mv_commit_tracking: Monthly projection
SELECT MEASURE(projected_monthly_cost) as projected FROM mv_commit_tracking;

-- mv_query_performance: P95 by warehouse
SELECT warehouse_name, MEASURE(p95_duration_seconds) as p95 FROM mv_query_performance GROUP BY 1;

-- mv_cluster_utilization: Underutilized clusters
SELECT cluster_name, MEASURE(avg_cpu_utilization) as cpu FROM mv_cluster_utilization WHERE provisioning_status = 'UNDERUTILIZED' GROUP BY 1;

-- mv_cluster_efficiency: Overall efficiency
SELECT MEASURE(efficiency_score) as score FROM mv_cluster_efficiency;

-- mv_job_performance: Success rate by job
SELECT job_name, MEASURE(success_rate) as success FROM mv_job_performance GROUP BY 1;

-- mv_security_events: Events by user type
SELECT user_type, MEASURE(total_events) as events FROM mv_security_events GROUP BY 1;

-- mv_governance_analytics: Active tables
SELECT MEASURE(active_table_count) as active FROM mv_governance_analytics;

-- mv_data_quality: Stale tables
SELECT table_full_name FROM mv_data_quality WHERE freshness_status = 'STALE';

-- mv_ml_intelligence: Anomaly rate
SELECT MEASURE(anomaly_rate) as rate FROM mv_ml_intelligence;
```

## Deployment Command Reference

```bash
# Validate
databricks bundle validate -t dev

# Deploy
databricks bundle deploy -t dev

# Run metric view deployment
databricks bundle run -t dev metric_view_deployment_job

# Verify
databricks sql-cli -e "SHOW VIEWS IN health_monitor.gold LIKE 'mv_*'"
```

