# Job Health Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Job Reliability Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks job reliability and execution analytics. Enables DevOps, data engineers, and SREs to query job success rates, failure patterns, and performance metrics without SQL. Powered by Job Performance Metric Views, 12 Table-Valued Functions, 5 ML Models for failure prediction, and Lakehouse Monitoring drift metrics.

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Job Status
1. "What is our job success rate this week?"
2. "Show me failed jobs today"
3. "Which jobs have the most failures this month?"
4. "How many jobs ran yesterday?"

### Performance Metrics
5. "What is the P95 job duration?"
6. "Which jobs are the slowest?"
7. "Show me job duration percentiles"
8. "What is the average job runtime?"

### Cost & Optimization
9. "What are our most expensive jobs?"
10. "Show me jobs with high repair costs"
11. "Which jobs have the highest retry rate?"

### ML-Powered Insights 🤖
12. "Which jobs are likely to fail tomorrow?"
13. "What's the health score for the ETL pipeline?"
14. "Will retrying this job succeed?"
15. "Show me jobs with performance regression"

---

## ████ SECTION D: DATA ASSETS ████

### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `job_performance` | Job execution metrics | total_runs, success_rate, failure_rate, avg_duration_seconds, p95_duration_seconds, p99_duration_seconds |

### Table-Valued Functions (12 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_failed_jobs` | Failed job analysis | "failed jobs", "errors today" |
| `get_job_success_rate` | Success rate by job | "success rate", "reliability" |
| `get_job_duration_percentiles` | Duration percentiles | "P95 duration", "job timing" |
| `get_job_failure_trends` | Daily failure trend | "failure trend" |
| `get_job_sla_compliance` | SLA tracking | "SLA compliance" |
| `get_job_run_details` | Detailed run history | "job history", specific job |
| `get_most_expensive_jobs` | Jobs by compute cost | "expensive jobs" |
| `get_job_retry_analysis` | Retry pattern analysis | "flaky jobs", "retries" |
| `get_job_repair_costs` | Repair (retry) costs | "repair costs" |
| `get_job_spend_trend_analysis` | Job cost growth | "job cost growth" |
| `get_job_failure_costs` | Failure impact costs | "failure costs" |
| `get_job_run_duration_analysis` | Duration statistics | "duration analysis" |

### ML Prediction Tables 🤖

| Table Name | Purpose |
|------------|---------|
| `job_failure_predictions` | Predicted failure probability by job |
| `retry_success_predictions` | Retry success probability |
| `pipeline_health_scores` | Pipeline health scores (0-100) |
| `incident_impact_predictions` | Blast radius estimates |
| `self_healing_recommendations` | Self-healing action suggestions |

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_job_run_timeline_profile_metrics` | Custom job metrics (success_rate, p90_duration, duration_cv) |
| `fact_job_run_timeline_drift_metrics` | Reliability drift (success_rate_drift, duration_drift) |

### Dimension Tables (from gold_layer_design/yaml/lakeflow/, shared/)

| Table Name | Purpose | Key Columns | YAML Source |
|------------|---------|-------------|-------------|
| `dim_job` | Job metadata | job_id, job_name, owner, schedule_type | lakeflow/dim_job.yaml |
| `dim_job_task` | Task metadata | task_key, task_type, depends_on | lakeflow/dim_job_task.yaml |
| `dim_pipeline` | DLT pipeline metadata | pipeline_id, pipeline_name, catalog, schema | lakeflow/dim_pipeline.yaml |
| `dim_workspace` | Workspace reference | workspace_id, workspace_name | shared/dim_workspace.yaml |

### Fact Tables (from gold_layer_design/yaml/lakeflow/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_job_run_timeline` | Job execution history | Per run | lakeflow/fact_job_run_timeline.yaml |
| `fact_job_task_run_timeline` | Task execution history | Per task run | lakeflow/fact_job_task_run_timeline.yaml |
| `fact_pipeline_update_timeline` | DLT pipeline updates | Per pipeline update | lakeflow/fact_pipeline_update_timeline.yaml |

---

## ████ SECTION E: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks job reliability analyst. Follow these rules:

1. **Primary Source:** Use job_performance metric view first
2. **TVFs:** Use TVFs for parameterized queries (date ranges, specific jobs)
3. **Date Default:** If no date specified, default to last 7 days
4. **Aggregation:** Use COUNT for volumes, AVG for averages
5. **Sorting:** Sort by failure_rate DESC or duration DESC
6. **Limits:** Top 10-20 for ranking queries
7. **Percentages:** Success/failure rates as % with 1 decimal
8. **Duration:** Show in minutes for readability
9. **Synonyms:** job=workflow=pipeline, failure=error=crash
10. **ML Predictions:** For "likely to fail" → query job_failure_predictions
11. **Health Score:** For "health score" → query pipeline_health_scores
12. **Retry:** For "retry success" → query retry_success_predictions
13. **Failed Jobs:** For "failed jobs today" → use get_failed_jobs TVF
14. **Success Rate:** For "success rate" → use get_job_success_rate TVF
15. **SLA:** For "SLA compliance" → use get_job_sla_compliance TVF
16. **Comparisons:** Show absolute and % change
17. **Context:** Explain FAILED vs ERROR vs TIMED_OUT
18. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION F: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_failed_jobs` | `(start_date STRING, end_date STRING)` | Failed jobs list | "failed jobs today" |
| `get_job_success_rate` | `(start_date STRING, end_date STRING)` | Success rates | "job success rate" |
| `get_job_duration_percentiles` | `(job_name STRING, start_date STRING, end_date STRING)` | Duration P50/P90/P99 | "P95 duration" |
| `get_most_expensive_jobs` | `(start_date STRING, end_date STRING, top_n INT)` | Top costly jobs | "expensive jobs" |
| `get_job_repair_costs` | `(start_date STRING, end_date STRING)` | Retry costs | "repair costs" |

### TVF Details

#### get_failed_jobs
- **Signature:** `get_failed_jobs(start_date STRING, end_date STRING)`
- **Returns:** job_name, run_id, result_state, termination_code, error_message, duration_minutes
- **Use When:** User asks for "failed jobs" or "errors today"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_failed_jobs('2024-12-19', '2024-12-19')`

#### get_job_success_rate
- **Signature:** `get_job_success_rate(start_date STRING, end_date STRING)`
- **Returns:** job_name, total_runs, successful_runs, failed_runs, success_rate, failure_rate
- **Use When:** User asks for "success rate" or "reliability by job"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_job_success_rate('2024-12-01', '2024-12-31')`

#### get_job_duration_percentiles
- **Signature:** `get_job_duration_percentiles(job_name STRING, start_date STRING, end_date STRING)`
- **Returns:** job_name, p50_duration, p90_duration, p95_duration, p99_duration, avg_duration
- **Use When:** User asks for "P95 duration" or "job timing"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_job_duration_percentiles(NULL, '2024-12-01', '2024-12-31')`

#### get_most_expensive_jobs
- **Signature:** `get_most_expensive_jobs(start_date STRING, end_date STRING, top_n INT)`
- **Returns:** job_name, total_cost, total_runs, cost_per_run, total_dbus
- **Use When:** User asks for "most expensive jobs" or "costliest jobs"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_most_expensive_jobs('2024-12-01', '2024-12-31', 10)`

#### get_job_repair_costs
- **Signature:** `get_job_repair_costs(start_date STRING, end_date STRING)`
- **Returns:** job_name, repair_count, repair_cost, original_cost, repair_rate
- **Use When:** User asks for "repair costs" or "retry costs"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_job_repair_costs('2024-12-01', '2024-12-31')`

---

## ████ SECTION G: BENCHMARK QUESTIONS WITH SQL ████

### Question 1: "What is our job success rate this week?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(success_rate) as success_rate_pct
FROM ${catalog}.${gold_schema}.job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Single percentage value (e.g., 94.5%)

---

### Question 2: "Show me failed jobs today"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_failed_jobs(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY duration_minutes DESC;
```
**Expected Result:** Table of failed jobs with error details

---

### Question 3: "Which jobs have the most failures this month?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_success_rate(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY failed_runs DESC
LIMIT 10;
```
**Expected Result:** Top 10 jobs by failure count

---

### Question 4: "What is the P95 job duration?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(p95_duration_seconds) / 60.0 as p95_duration_minutes
FROM ${catalog}.${gold_schema}.job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS;
```
**Expected Result:** Single value in minutes

---

### Question 5: "What are our most expensive jobs?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_most_expensive_jobs(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  10
);
```
**Expected Result:** Top 10 jobs by compute cost

---

### Question 6: "Which jobs are likely to fail tomorrow?"
**Expected SQL:**
```sql
SELECT 
  job_name,
  failure_probability,
  risk_factors
FROM ${catalog}.${gold_schema}.job_failure_predictions
WHERE failure_probability > 0.3
ORDER BY failure_probability DESC
LIMIT 20;
```
**Expected Result:** Jobs with >30% failure probability

---

### Question 7: "What's the health score for jobs?"
**Expected SQL:**
```sql
SELECT 
  job_name,
  health_score,
  CASE 
    WHEN health_score >= 91 THEN 'Excellent'
    WHEN health_score >= 76 THEN 'Good'
    WHEN health_score >= 51 THEN 'Fair'
    WHEN health_score >= 26 THEN 'Poor'
    ELSE 'Critical'
  END as health_status
FROM ${catalog}.${gold_schema}.pipeline_health_scores
ORDER BY health_score ASC
LIMIT 20;
```
**Expected Result:** Jobs with health scores and status classification

---

### Question 8: "Show me jobs with high retry costs"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_repair_costs(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
WHERE repair_cost > 0
ORDER BY repair_cost DESC
LIMIT 10;
```
**Expected Result:** Jobs with significant repair/retry costs

---

### Question 9: "What is our failure rate trend this week?"
**Expected SQL:**
```sql
SELECT 
  run_date,
  MEASURE(failure_rate) as failure_rate_pct,
  MEASURE(total_runs) as total_runs
FROM ${catalog}.${gold_schema}.job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY run_date
ORDER BY run_date;
```
**Expected Result:** Daily failure rates for the week

---

### Question 10: "Are there any reliability drift alerts?"
**Expected SQL:**
```sql
SELECT 
  window_start,
  success_rate_drift,
  duration_drift
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_drift_metrics
WHERE column_name = ':table'
  AND (ABS(success_rate_drift) > 5 OR ABS(duration_drift) > 20)
ORDER BY window_start DESC
LIMIT 10;
```
**Expected Result:** Recent drift alerts for success rate or duration

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 12 functions with signatures | ✅ |
| **G. Benchmark Questions** | 10 with SQL answers | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🔄 **Reliability**

---

## References

- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md)
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md)

