# 09 - Usage Examples

## Overview

This document provides example queries demonstrating how to use TVFs for common analysis scenarios. These examples can be used directly in SQL queries or as natural language questions in Genie Spaces.

## Cost Analysis Examples

### Q: What are our biggest cost drivers?

**Natural Language**: "What are the top 10 cost drivers this month?"

**SQL**:
```sql
SELECT * FROM TABLE(get_top_cost_contributors(
    '2024-12-01',  -- start_date
    '2024-12-31',  -- end_date
    10             -- top_n
));
```

### Q: How are costs trending?

**Natural Language**: "Show me daily cost trend for December"

**SQL**:
```sql
SELECT * FROM TABLE(get_daily_cost_summary(
    '2024-12-01',
    '2024-12-31'
));
```

### Q: Who is spending the most?

**Natural Language**: "Which users have the highest cloud bills?"

**SQL**:
```sql
SELECT * FROM TABLE(get_cost_by_owner(
    '2024-12-01',
    '2024-12-31',
    20
));
```

### Q: Are there cost anomalies?

**Natural Language**: "Are there any unusual cost spikes?"

**SQL**:
```sql
SELECT * FROM TABLE(get_cost_anomalies(
    30,    -- days_back
    50.0   -- threshold_pct (50% deviation)
));
```

### Q: What resources need tagging?

**Natural Language**: "Which resources are missing tags?"

**SQL**:
```sql
SELECT * FROM TABLE(get_untagged_resources(
    '2024-12-01',
    '2024-12-31'
));
```

---

## Reliability Analysis Examples

### Q: Which jobs are failing?

**Natural Language**: "What jobs failed this week?"

**SQL**:
```sql
SELECT * FROM TABLE(get_failed_jobs_summary(
    7,   -- days_back
    1    -- min_failures
));
```

### Q: What's our job success rate?

**Natural Language**: "Show me job success rates for December"

**SQL**:
```sql
SELECT * FROM TABLE(get_job_success_rates(
    '2024-12-01',
    '2024-12-31',
    5    -- min_runs
));
```

### Q: Are jobs meeting SLA?

**Natural Language**: "Which jobs are missing SLA?"

**SQL**:
```sql
SELECT * FROM TABLE(get_job_sla_compliance(
    '2024-12-01',
    '2024-12-31'
));
```

### Q: How long do jobs take?

**Natural Language**: "What are the job duration percentiles?"

**SQL**:
```sql
SELECT * FROM TABLE(get_job_duration_percentiles(
    30   -- days_back
));
```

### Q: What are the common errors?

**Natural Language**: "What error patterns are we seeing?"

**SQL**:
```sql
SELECT * FROM TABLE(get_job_failure_patterns(
    14   -- days_back
));
```

---

## Performance Analysis Examples

### Q: What queries are slow?

**Natural Language**: "Show me queries taking over 30 seconds"

**SQL**:
```sql
SELECT * FROM TABLE(get_slow_queries(
    7,    -- days_back
    30    -- duration_threshold_sec
));
```

### Q: What's our query latency?

**Natural Language**: "What are query latency percentiles?"

**SQL**:
```sql
SELECT * FROM TABLE(get_query_latency_percentiles(
    '2024-12-01',
    '2024-12-31'
));
```

### Q: How are warehouses performing?

**Natural Language**: "Show me SQL Warehouse utilization"

**SQL**:
```sql
SELECT * FROM TABLE(get_warehouse_utilization(
    '2024-12-01',
    '2024-12-31'
));
```

### Q: Who is running the most queries?

**Natural Language**: "Top 10 most active query users"

**SQL**:
```sql
SELECT * FROM TABLE(get_top_users_by_query_count(
    '2024-12-01',
    '2024-12-31',
    10
));
```

### Q: Are clusters underutilized?

**Natural Language**: "Which clusters are underutilized?"

**SQL**:
```sql
SELECT * FROM TABLE(get_underutilized_clusters(
    30   -- days_back
));
```

### Q: What jobs need DBR upgrade?

**Natural Language**: "Which jobs are on legacy Databricks Runtime?"

**SQL**:
```sql
SELECT * FROM TABLE(get_jobs_on_legacy_dbr(
    30   -- days_back
));
```

---

## Security Analysis Examples

### Q: Who are the most active users?

**Natural Language**: "Show me user activity this month"

**SQL**:
```sql
SELECT * FROM TABLE(get_user_activity_summary(
    '2024-12-01',
    '2024-12-31',
    50
));
```

### Q: What tables are being accessed?

**Natural Language**: "Which tables are most accessed?"

**SQL**:
```sql
SELECT * FROM TABLE(get_table_access_audit(
    '2024-12-01',
    '2024-12-31'
));
```

### Q: Are there permission changes?

**Natural Language**: "Show me permission changes this week"

**SQL**:
```sql
SELECT * FROM TABLE(get_permission_changes(
    7   -- days_back
));
```

### Q: Any failed login attempts?

**Natural Language**: "Are there failed access attempts?"

**SQL**:
```sql
SELECT * FROM TABLE(get_failed_access_attempts(
    7   -- days_back
));
```

### Q: Who has the highest risk?

**Natural Language**: "Show me user risk scores"

**SQL**:
```sql
SELECT * FROM TABLE(get_user_risk_scores(
    30   -- days_back
));
```

---

## Data Quality Examples

### Q: Is our data fresh?

**Natural Language**: "Are our tables up to date?"

**SQL**:
```sql
SELECT * FROM TABLE(get_table_freshness(
    30   -- days_back
));
```

### Q: What tables are stale?

**Natural Language**: "Which tables haven't been updated?"

**SQL**:
```sql
SELECT * FROM TABLE(get_stale_tables(
    30,  -- days_back
    7    -- staleness_threshold_days
));
```

### Q: What are the data dependencies?

**Natural Language**: "Show me table lineage"

**SQL**:
```sql
SELECT * FROM TABLE(get_data_lineage_summary(
    'my_catalog',   -- catalog_filter
    '%'             -- schema_filter
));
```

### Q: What data is unused?

**Natural Language**: "Which tables are orphaned?"

**SQL**:
```sql
SELECT * FROM TABLE(get_orphan_tables(
    90   -- days_back
));
```

### Q: Are tables properly tagged?

**Natural Language**: "Check governance compliance"

**SQL**:
```sql
SELECT * FROM TABLE(get_governance_compliance(
    '%'   -- catalog_filter
));
```

---

## Combined Analysis Examples

### Executive Dashboard Query

```sql
-- Get key metrics for executive summary
WITH cost_summary AS (
    SELECT 
        SUM(total_cost) as total_spend,
        COUNT(DISTINCT workspace_id) as active_workspaces
    FROM TABLE(get_daily_cost_summary('2024-12-01', '2024-12-31'))
),
reliability_summary AS (
    SELECT 
        AVG(success_rate) as avg_success_rate,
        COUNT(*) as monitored_jobs
    FROM TABLE(get_job_success_rates('2024-12-01', '2024-12-31', 5))
),
performance_summary AS (
    SELECT 
        AVG(p95_latency_sec) as avg_p95_latency,
        SUM(query_count) as total_queries
    FROM TABLE(get_query_latency_percentiles('2024-12-01', '2024-12-31'))
)
SELECT 
    c.total_spend,
    c.active_workspaces,
    r.avg_success_rate,
    r.monitored_jobs,
    p.avg_p95_latency,
    p.total_queries
FROM cost_summary c
CROSS JOIN reliability_summary r
CROSS JOIN performance_summary p;
```

### Incident Investigation Query

```sql
-- Investigate a cost spike on a specific date
WITH anomalies AS (
    SELECT * FROM TABLE(get_cost_anomalies(30, 25.0))
    WHERE anomaly_date = '2024-12-15'
),
related_jobs AS (
    SELECT * FROM TABLE(get_failed_jobs_summary(7, 1))
),
slow_queries AS (
    SELECT * FROM TABLE(get_slow_queries(7, 60))
)
SELECT 
    'Cost Anomaly' as category,
    a.workspace_id,
    a.sku_name,
    a.actual_cost,
    a.deviation_pct
FROM anomalies a
UNION ALL
SELECT 
    'Failed Job' as category,
    j.workspace_id,
    j.job_name,
    j.failure_count,
    100 - j.success_rate
FROM related_jobs j
WHERE j.last_failure_time >= '2024-12-14';
```

---

## Genie Space Integration

### Sample Genie Space Configuration

These TVFs should be registered in Genie Spaces with appropriate metadata:

**Cost Intelligence Space**:
- `get_top_cost_contributors`
- `get_cost_trend_by_sku`
- `get_cost_by_owner`
- `get_cost_by_tag`
- `get_untagged_resources`
- `get_cost_anomalies`
- (All 15 cost TVFs)

**Performance Optimizer Space**:
- `get_slow_queries`
- `get_query_latency_percentiles`
- `get_warehouse_utilization`
- (All 16 performance TVFs)

**Job Health Monitor Space**:
- `get_failed_jobs_summary`
- `get_job_success_rates`
- `get_job_sla_compliance`
- (All 12 reliability TVFs)

**Security Auditor Space**:
- `get_user_activity_summary`
- `get_table_access_audit`
- `get_permission_changes`
- (All 10 security TVFs)

**Data Quality Monitor Space**:
- `get_table_freshness`
- `get_stale_tables`
- `get_data_lineage_summary`
- (All 7 quality TVFs)

## Next Steps

- **[Appendices/A-Quick Reference](appendices/A-quick-reference.md)**: Complete TVF parameter reference
- **[Appendices/B-SQL Patterns](appendices/B-sql-patterns.md)**: Common SQL patterns

