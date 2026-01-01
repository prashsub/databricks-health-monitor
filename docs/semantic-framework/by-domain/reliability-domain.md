# Reliability Domain Metric Views

The Reliability Domain provides job execution reliability and SLA monitoring metrics.

## Views in This Domain

| View | Source | Primary Use Case |
|------|--------|------------------|
| `mv_job_performance` | `fact_job_run_timeline` | Job success rates and duration |

---

## mv_job_performance

**Full Name**: `{catalog}.{gold_schema}.mv_job_performance`

### Purpose

Job execution reliability and efficiency metrics for monitoring job health, tracking SLAs, and identifying performance issues.

### Key Features

- **Success/failure rates** tracking
- **Duration percentiles** (P50, P95, P99)
- **Outcome categorization** (SUCCESS, FAILURE, TIMEOUT, CANCELLED)
- **Trigger type analysis** (PERIODIC, ONE_TIME, RETRY)

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "What's our job success rate?" | `success_rate` |
| "Show failed jobs today" | `failures_today` |
| "Which jobs are slowest?" | `avg_duration_minutes`, `p95_duration_minutes` |
| "What's the failure rate by job?" | `failure_rate` |
| "How many total runs?" | `total_runs` |

### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `job_name` | Human-readable job name |
| `outcome_category` | SUCCESS, FAILURE, TIMEOUT, CANCELLED |
| `trigger_type` | PERIODIC, ONE_TIME, RETRY |
| `workspace_name` | Workspace identifier |
| `run_date` | Date of job execution |

### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `success_rate` | percentage | % successful runs |
| `failure_rate` | percentage | % failed runs |
| `avg_duration_minutes` | number | Average runtime |
| `p95_duration_minutes` | number | P95 runtime |
| `total_runs` | number | Total executions |
| `failures_today` | number | Today's failure count |

### SQL Examples

```sql
-- Overall success rate
SELECT 
    MEASURE(success_rate) as success_pct,
    MEASURE(failure_rate) as failure_pct,
    MEASURE(total_runs) as total
FROM mv_job_performance;

-- Success rate by job
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
GROUP BY job_name
ORDER BY p95_min DESC;

-- Failures by outcome category
SELECT 
    outcome_category,
    MEASURE(total_runs) as count
FROM mv_job_performance
WHERE outcome_category != 'SUCCESS'
GROUP BY outcome_category;

-- Daily failure trend
SELECT 
    run_date,
    MEASURE(failure_rate) as failure_pct,
    MEASURE(failures_today) as failures
FROM mv_job_performance
WHERE run_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY run_date
ORDER BY run_date;
```

---

## Use Cases

| Use Case | How to Query |
|----------|--------------|
| SLA monitoring | Check `success_rate` against threshold |
| Performance regression | Compare `p95_duration_minutes` over time |
| Failure investigation | Filter by `outcome_category = 'FAILURE'` |
| Capacity planning | Analyze `total_runs` by time period |

## Related Resources

- [TVFs: Reliability Agent TVFs](../04-reliability-agent-tvfs.md)
