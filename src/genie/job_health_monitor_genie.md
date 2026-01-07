# Job Health Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Job Reliability Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks job reliability and execution analytics. Enables DevOps, data engineers, and SREs to query job success rates, failure patterns, and performance metrics without SQL.

**Powered by:**
- 1 Metric View (mv_job_performance)
- 12 Table-Valued Functions (job status, failure analysis, duration/SLA queries)
- 5 ML Prediction Tables (failure prediction, retry success, health scoring)
- 2 Lakehouse Monitoring Tables (reliability drift and profile metrics)
- 5 Dimension Tables (job, job_task, pipeline, workspace, date)
- 3 Fact Tables (job runs, task runs, pipeline updates)

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
| `mv_job_performance` | Job execution metrics | total_runs, success_rate, failure_rate, avg_duration_seconds, p95_duration_seconds, p99_duration_seconds |

### Table-Valued Functions (12 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_failed_jobs_summary` | Failed job analysis | "failed jobs", "errors today" |
| `get_job_success_rates` | Success rate by job | "success rate", "reliability" |
| `get_job_duration_trends` | Duration trends over time | "duration trends" |
| `get_job_sla_compliance` | SLA tracking | "SLA compliance" |
| `get_job_failure_patterns` | Failure pattern analysis | "failure patterns" |
| `get_long_running_jobs` | Long-running jobs | "slow jobs", "long duration" |
| `get_job_retry_analysis` | Retry pattern analysis | "flaky jobs", "retries" |
| `get_job_duration_percentiles` | Duration percentiles | "P95 duration", "job timing" |
| `get_job_failure_cost` | Failure impact costs | "failure costs" |
| `get_pipeline_health` | Pipeline health status | "pipeline health", "DLT health" |
| `get_job_schedule_drift` | Schedule drift analysis | "schedule drift", "late jobs" |
| `get_repair_cost_analysis` | Repair (retry) costs | "repair costs" |

### ML Prediction Tables 🤖 (5 Models)

| Table Name | Purpose | Model | Key Columns |
|---|---|---|---|
| `job_failure_predictions` | Predicted failure probability before execution | Job Failure Predictor | `prediction`, `job_id`, `run_date` |
| `duration_predictions` | Predicted job duration in seconds | Job Duration Forecaster | `prediction`, `job_id`, `run_date` |
| `sla_breach_predictions` | Predicted SLA breach probability | SLA Breach Predictor | `prediction`, `job_id`, `run_date` |
| `retry_success_predictions` | Predict whether failed job will succeed on retry | Retry Success Predictor | `prediction`, `job_id`, `run_date` |
| `pipeline_health_predictions` | Overall pipeline/job health scores (0-100) | Pipeline Health Scorer | `prediction`, `job_id`, `run_date` |

**Training Source:** `src/ml/reliability/` | **Inference:** `src/ml/inference/batch_inference_all_models.py`

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_job_run_timeline_profile_metrics` | Custom job metrics (success_rate, failure_count, p90_duration, duration_cv) |
| `fact_job_run_timeline_drift_metrics` | Reliability drift (success_rate_drift, duration_drift) |

#### ⚠️ CRITICAL: Custom Metrics Query Patterns

**Always include these filters when querying Lakehouse Monitoring tables:**

```sql
-- ✅ CORRECT: Get job reliability metrics
SELECT 
  window.start AS window_start,
  success_rate,
  failure_count,
  p90_duration
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'     -- REQUIRED: Table-level custom metrics
  AND log_type = 'INPUT'         -- REQUIRED: Input data statistics
  AND slice_key IS NULL          -- For overall metrics
ORDER BY window.start DESC;

-- ✅ CORRECT: Get success rate by job name (sliced)
SELECT 
  slice_value AS job_name,
  AVG(success_rate) AS avg_success_rate,
  SUM(failure_count) AS total_failures
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'job_name'
GROUP BY slice_value
ORDER BY avg_success_rate ASC;

-- ✅ CORRECT: Get reliability drift
SELECT 
  window.start AS window_start,
  success_rate_drift,
  duration_drift
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC;
```

#### Available Slicing Dimensions (Job Monitor)

| Slice Key | Use Case |
|-----------|----------|
| `workspace_id` | Reliability by workspace |
| `job_name` | Metrics by specific job |
| `result_state` | Breakdown by outcome |
| `trigger_type` | Scheduled vs manual |
| `termination_code` | Failures by termination code |

### Dimension Tables (5 Tables)

**Sources:** `gold_layer_design/yaml/lakeflow/`, `shared/`

| Table Name | Purpose | Key Columns | YAML Source |
|---|---|---|---|
| `dim_job` | Job metadata | `job_id`, `job_name`, `creator_user_name`, `schedule_type`, `job_type` | lakeflow/dim_job.yaml |
| `dim_job_task` | Task metadata | `task_key`, `task_type`, `depends_on`, `cluster_spec` | lakeflow/dim_job_task.yaml |
| `dim_pipeline` | DLT pipeline metadata | `pipeline_id`, `pipeline_name`, `catalog`, `schema`, `channel` | lakeflow/dim_pipeline.yaml |
| `dim_workspace` | Workspace reference | `workspace_id`, `workspace_name`, `region`, `cloud_provider` | shared/dim_workspace.yaml |
| `dim_date` | Date dimension for time analysis | `date_key`, `day_of_week`, `month`, `quarter`, `year`, `is_weekend` | shared/dim_date.yaml |

### Fact Tables (from gold_layer_design/yaml/lakeflow/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_job_run_timeline` | Job execution history | Per run | lakeflow/fact_job_run_timeline.yaml |
| `fact_job_task_run_timeline` | Task execution history | Per task run | lakeflow/fact_job_task_run_timeline.yaml |
| `fact_pipeline_update_timeline` | DLT pipeline updates | Per pipeline update | lakeflow/fact_pipeline_update_timeline.yaml |

### Data Model Relationships 🔗

**Foreign Key Constraints** (extracted from `gold_layer_design/yaml/lakeflow/`)

| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_job_run_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_job_run_timeline` | → | `dim_job` | `(workspace_id, job_id)` = `(workspace_id, job_id)` | LEFT |
| `fact_job_task_run_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_job_task_run_timeline` | → | `dim_job` | `(workspace_id, job_id)` = `(workspace_id, job_id)` | LEFT |
| `fact_job_task_run_timeline` | → | `dim_job_task` | `(workspace_id, job_id, task_key)` = `(workspace_id, job_id, task_key)` | LEFT |
| `fact_pipeline_update_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_pipeline_update_timeline` | → | `dim_pipeline` | `(workspace_id, pipeline_id)` = `(workspace_id, pipeline_id)` | LEFT |

**Join Patterns:**
- **Single Key:** `ON fact.key = dim.key`
- **Composite Key (workspace-scoped):** `ON fact.workspace_id = dim.workspace_id AND fact.fk = dim.pk`
- **Three-Part Key (task-level):** `ON fact.workspace_id = dim.workspace_id AND fact.job_id = dim.job_id AND fact.task_key = dim.task_key`

---

## ████ SECTION E: ASSET SELECTION FRAMEWORK ████

### Semantic Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASSET SELECTION DECISION TREE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER QUERY PATTERN                → USE THIS ASSET             │
│  ─────────────────────────────────────────────────────────────  │
│  "What's the current success rate?"→ Metric View (mv_job_performance)│
│  "Show me job success by X"        → Metric View (mv_job_performance)│
│  ─────────────────────────────────────────────────────────────  │
│  "Is success rate degrading?"      → Custom Metrics (_drift_metrics)│
│  "Failure trend since last week"   → Custom Metrics (_profile_metrics)│
│  ─────────────────────────────────────────────────────────────  │
│  "Which jobs failed today?"        → TVF (get_failed_jobs_summary)       │
│  "Top 10 failing jobs"             → TVF (get_job_success_rates) │
│  "Jobs slower than threshold"      → TVF (get_long_running_jobs)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Current success rate** | Metric View | "Job success rate" → `mv_job_performance` |
| **Trend over time** | Custom Metrics | "Is reliability degrading?" → `_drift_metrics` |
| **List of failed jobs** | TVF | "Failed jobs today" → `get_failed_jobs_summary` |
| **SLA compliance** | TVF | "SLA breaches" → `get_job_sla_compliance` |
| **Failure predictions** | ML Tables | "Jobs likely to fail" → `job_failure_predictions` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for PREDICTION** → ML Tables

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks job reliability analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists, Custom Metrics for trends
2. **Primary Source:** Use mv_job_performance metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for "which jobs", "top N", "list" queries - always wrap in TABLE()
4. **Trends:** For "is success rate degrading?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 7 days
6. **Aggregation:** Use COUNT for volumes, AVG for averages
7. **Sorting:** Sort by failure_rate DESC or duration DESC
8. **Limits:** Top 10-20 for ranking queries
9. **Percentages:** Success/failure rates as % with 1 decimal
10. **Duration:** Show in minutes for readability
11. **Synonyms:** job=workflow=pipeline, failure=error=crash
12. **ML Predictions:** For "likely to fail" → query job_failure_predictions with ${feature_schema}
13. **Failed Jobs:** For "failed jobs today" → use get_failed_jobs_summary(1, 1) with TABLE()
14. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
15. **Context:** Explain FAILED vs ERROR vs TIMED_OUT
16. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_failed_jobs_summary` | `(days_back INT, min_failures INT DEFAULT 1)` | Failed jobs list | "failed jobs today" |
| `get_job_success_rates` | `(start_date STRING, end_date STRING, min_runs INT DEFAULT 5)` | Success rates | "job success rate" |
| `get_job_duration_trends` | `(start_date STRING, end_date STRING)` | Duration trends over time | "duration trends" |
| `get_job_sla_compliance` | `(start_date STRING, end_date STRING)` | SLA tracking | "SLA compliance" |
| `get_job_failure_patterns` | `(days_back INT)` | Failure pattern analysis | "failure patterns" |
| `get_long_running_jobs` | `(days_back INT, duration_threshold_min INT DEFAULT 60)` | Long-running jobs | "slow jobs" |
| `get_job_retry_analysis` | `(days_back INT)` | Retry pattern analysis | "retry analysis" |
| `get_job_duration_percentiles` | `(days_back INT)` | Duration P50/P90/P95/P99 | "P95 duration" |
| `get_job_failure_cost` | `(start_date STRING, end_date STRING)` | Failure impact costs | "failure costs" |
| `get_pipeline_health` | `(days_back INT)` | Pipeline health status | "pipeline health" |
| `get_job_schedule_drift` | `(days_back INT)` | Schedule drift analysis | "schedule drift" |
| `get_repair_cost_analysis` | `(start_date STRING, end_date STRING)` | Repair costs | "repair costs" |

### TVF Details

#### get_failed_jobs_summary
- **Signature:** `get_failed_jobs_summary(days_back INT, min_failures INT DEFAULT 1)`
- **Returns:** job_name, run_id, result_state, termination_code, error_message, duration_minutes
- **Use When:** User asks for "failed jobs" or "errors today"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs_summary(1, 1))`

#### get_job_success_rates
- **Signature:** `get_job_success_rates(start_date STRING, end_date STRING, min_runs INT DEFAULT 5)`
- **Returns:** job_name, total_runs, successful_runs, failed_runs, success_rate, failure_rate
- **Use When:** User asks for "success rate" or "reliability by job"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_success_rates('2024-12-01', '2024-12-31', 5))`

#### get_job_duration_percentiles
- **Signature:** `get_job_duration_percentiles(days_back INT)`
- **Returns:** job_name, p50_duration, p90_duration, p95_duration, p99_duration, avg_duration
- **Use When:** User asks for "P95 duration" or "job timing"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_duration_percentiles(30))`

#### get_job_failure_patterns
- **Signature:** `get_job_failure_patterns(days_back INT)`
- **Returns:** job_name, failure_category, failure_count, failure_rate
- **Use When:** User asks for "failure patterns" or "failure trends"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_failure_patterns(30))`

#### get_long_running_jobs
- **Signature:** `get_long_running_jobs(days_back INT, duration_threshold_min INT DEFAULT 60)`
- **Returns:** job_name, run_duration_minutes, exceeded_by_minutes
- **Use When:** User asks for "slow jobs" or "long-running jobs"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_long_running_jobs(7, 60))`

#### get_job_retry_analysis
- **Signature:** `get_job_retry_analysis(days_back INT)`
- **Returns:** job_name, retry_count, retry_success_rate, retry_effectiveness
- **Use When:** User asks for "retry patterns" or "retry analysis"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_retry_analysis(30))`

#### get_repair_cost_analysis
- **Signature:** `get_repair_cost_analysis(start_date STRING, end_date STRING)`
- **Returns:** job_name, repair_count, repair_cost, original_cost, repair_rate
- **Use When:** User asks for "repair costs" or "retry costs"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_repair_cost_analysis('2024-12-01', '2024-12-31'))`

#### get_job_failure_cost
- **Signature:** `get_job_failure_cost(start_date STRING, end_date STRING)`
- **Returns:** job_name, failure_count, failure_cost, total_cost, failure_cost_pct
- **Use When:** User asks for "failure costs" or "cost of failures"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_failure_cost('2024-12-01', '2024-12-31'))`

#### get_pipeline_health
- **Signature:** `get_pipeline_health(days_back INT)`
- **Returns:** pipeline_name, health_score, update_count, failure_rate
- **Use When:** User asks for "pipeline health" or "DLT health"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_pipeline_health(7))`

#### get_job_schedule_drift
- **Signature:** `get_job_schedule_drift(days_back INT)`
- **Returns:** job_name, expected_start, actual_start, drift_minutes
- **Use When:** User asks for "schedule drift" or "late jobs"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_schedule_drift(7))`

#### get_job_duration_trends
- **Signature:** `get_job_duration_trends(start_date STRING, end_date STRING)`
- **Returns:** job_name, run_date, duration_minutes, trend
- **Use When:** User asks for "duration trends" or "duration over time"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_duration_trends('2024-12-01', '2024-12-31'))`

#### get_job_sla_compliance
- **Signature:** `get_job_sla_compliance(start_date STRING, end_date STRING)`
- **Returns:** job_name, sla_threshold, breach_count, compliance_rate
- **Use When:** User asks for "SLA compliance" or "SLA breaches"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_sla_compliance('2024-12-01', '2024-12-31'))`

---

## ████ SECTION G: ML MODEL INTEGRATION (5 Models) ████

### Reliability ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `job_failure_predictor` | `job_failure_predictions` | `prediction` (failure probability) | "Will this job fail?" |
| `job_duration_forecaster` | `duration_predictions` | `prediction` (duration in minutes) | "How long will it take?" |
| `sla_breach_predictor` | `sla_breach_predictions` | `prediction` (breach probability) | "Will SLA breach?" |
| `pipeline_health_scorer` | `pipeline_health_predictions` | `prediction` (0-100) | "Pipeline health score" |
| `retry_success_predictor` | `retry_success_predictions` | `prediction` (retry success probability) | "Will retry succeed?" |

### ML Model Usage Patterns

#### job_failure_predictor (Failure Prediction)
- **Question Triggers:** "will fail", "likely to fail", "at risk", "failure prediction"
- **Query Pattern:**
```sql
SELECT j.name as job_name, jfp.prediction as failure_probability, jfp.run_date
FROM ${catalog}.${feature_schema}.job_failure_predictions jfp
JOIN ${catalog}.${gold_schema}.dim_job j ON jfp.job_id = j.job_id
WHERE jfp.run_date = CURRENT_DATE()
  AND jfp.prediction > 0.5
ORDER BY jfp.prediction DESC;
```
- **Interpretation:** `prediction > 0.5` = High risk of failure

#### job_duration_forecaster (Duration Prediction)
- **Question Triggers:** "how long", "duration estimate", "expected time", "forecast duration"
- **Query Pattern:**
```sql
SELECT j.name as job_name, dp.prediction as predicted_duration_minutes, dp.run_date
FROM ${catalog}.${feature_schema}.duration_predictions dp
JOIN ${catalog}.${gold_schema}.dim_job j ON dp.job_id = j.job_id
WHERE j.name = '{job_name}'
  AND dp.run_date >= CURRENT_DATE()
ORDER BY dp.run_date DESC LIMIT 1;
```

#### pipeline_health_scorer (Health Score)
- **Question Triggers:** "pipeline health", "health score", "pipeline status", "healthy pipelines"
- **Query Pattern:**
```sql
SELECT j.name as job_name, php.prediction as health_score, php.run_date,
       CASE WHEN php.prediction >= 90 THEN 'Excellent'
            WHEN php.prediction >= 70 THEN 'Good'
            WHEN php.prediction >= 50 THEN 'Warning'
            ELSE 'Critical' END as health_status
FROM ${catalog}.${feature_schema}.pipeline_health_predictions php
JOIN ${catalog}.${gold_schema}.dim_job j ON php.job_id = j.job_id
WHERE php.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY php.prediction ASC;
```
- **Interpretation:** `prediction < 70` = Needs attention

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Will job X fail?"                      → ML: job_failure_predictions
"How long will job X take?"             → ML: duration_predictions
"Pipeline health score"                 → ML: pipeline_health_predictions
"Will SLA be breached?"                 → ML: sla_breach_predictions
────────────────────────────────────────────────────
"What is the success rate?"             → Metric View: mv_job_performance
"Is reliability trending down?"         → Custom Metrics: _drift_metrics
"Show failed jobs today"                → TVF: get_failed_jobs_summary
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**
> **Grounded in:** mv_job_performance, TVFs, ML Tables, Lakehouse Monitors, Fact/Dim Tables

### ✅ Normal Benchmark Questions (Q1-Q20)

### Question 1: "What is our job success rate this week?"
**Expected SQL:**
```sql
SELECT MEASURE(success_rate) as success_rate_pct
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall job success rate percentage for last 7 days

---

### Question 2: "Show me job performance by workspace"
**Expected SQL:**
```sql
SELECT 
  workspace_name,
  MEASURE(success_rate) as success_pct,
  MEASURE(failure_rate) as failure_pct,
  MEASURE(total_runs) as runs
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY workspace_name
ORDER BY runs DESC
LIMIT 10;
```
**Expected Result:** Top 10 workspaces by job execution volume with success/failure rates

---

### Question 3: "What is the P95 job duration?"
**Expected SQL:**
```sql
SELECT MEASURE(p95_duration_minutes) as p95_minutes
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** P95 job duration in minutes for SLA tracking

---

### Question 4: "Show me failed jobs today"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs_summary(
  1,
  1
))
ORDER BY failure_count DESC
LIMIT 20;
```
**Expected Result:** List of jobs that failed today with error details

---

### Question 5: "What is the average job duration?"
**Expected SQL:**
```sql
SELECT MEASURE(avg_duration_minutes) as avg_minutes
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Average job execution time across all jobs

---

### Question 6: "Show me job duration percentiles"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_duration_percentiles(
  30
))
ORDER BY p99_duration DESC
LIMIT 15;
```
**Expected Result:** P50/P90/P95/P99 duration statistics for all jobs

---

### Question 7: "Which jobs have the lowest success rate?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_success_rates(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  5
))
ORDER BY success_rate ASC
LIMIT 10;
```
**Expected Result:** Jobs with poorest reliability requiring attention

---

### Question 8: "Show me job failure trends"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_failure_patterns(
  30
))
ORDER BY failure_count DESC;
```
**Expected Result:** Failure patterns by error category over last 30 days

---

### Question 9: "What jobs are running longer than their SLA?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_long_running_jobs(
  7,
  60
))
ORDER BY exceeded_by_minutes DESC
LIMIT 20;
```
**Expected Result:** Jobs exceeding 60-minute threshold with SLA breach details

---

### Question 10: "Show me job retry analysis"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_retry_analysis(
  30
))
WHERE retry_count > 0
ORDER BY retry_effectiveness DESC;
```
**Expected Result:** Jobs with retry patterns and success rates after retry

---

### Question 11: "What is the most expensive job by compute cost?"
**Expected SQL:**
```sql
SELECT 
  j.name as job_name,
  SUM(f.run_duration_minutes) as total_minutes,
  COUNT(*) as run_count
FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
WHERE f.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND f.is_success = TRUE
GROUP BY j.name
ORDER BY total_minutes DESC
LIMIT 10;
```
**Expected Result:** Jobs with highest cumulative runtime (proxy for compute cost)

---

### Question 12: "Show me job repair costs from retries"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_repair_cost_analysis(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
ORDER BY repair_cost DESC
LIMIT 15;
```
**Expected Result:** Repair costs from job retries with efficiency metrics

---

### Question 13: "What is our job failure rate by trigger type?"
**Expected SQL:**
```sql
SELECT 
  trigger_type,
  MEASURE(failure_rate) as failure_pct,
  MEASURE(total_runs) as runs
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY trigger_type
ORDER BY failure_pct DESC;
```
**Expected Result:** Failure rates broken down by SCHEDULED vs MANUAL vs RETRY

---

### Question 14: "Show me pipeline health from DLT updates"
**Expected SQL:**
```sql
SELECT 
  p.pipeline_name,
  COUNT(*) as update_count,
  SUM(CASE WHEN f.update_state = 'COMPLETED' THEN 1 ELSE 0 END) as successful_updates,
  AVG(f.duration_minutes) as avg_duration
FROM ${catalog}.${gold_schema}.fact_pipeline_update_timeline f
JOIN ${catalog}.${gold_schema}.dim_pipeline p ON f.workspace_id = p.workspace_id AND f.pipeline_id = p.pipeline_id
WHERE f.start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY p.pipeline_name
ORDER BY successful_updates DESC
LIMIT 10;
```
**Expected Result:** DLT pipeline execution health with success rates

---

### Question 15: "Which jobs have been cancelled the most?"
**Expected SQL:**
```sql
SELECT 
  j.name as job_name,
  COUNT(*) as cancellation_count
FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
WHERE f.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND f.result_state = 'CANCELED'
GROUP BY j.name
ORDER BY cancellation_count DESC
LIMIT 10;
```
**Expected Result:** Jobs with high manual cancellation rates

---

### Question 16: "What jobs are predicted to fail tomorrow?"
**Expected SQL:**
```sql
SELECT 
  j.name as job_name,
  jfp.run_date,
  jfp.prediction as failure_probability
FROM ${catalog}.${feature_schema}.job_failure_predictions jfp
JOIN ${catalog}.${gold_schema}.dim_job j ON jfp.job_id = j.job_id
WHERE jfp.run_date = CURRENT_DATE() + INTERVAL 1 DAY
  AND jfp.prediction > 0.5
ORDER BY jfp.prediction DESC
LIMIT 15;
```
**Expected Result:** ML-predicted job failures for next day with probabilities

---

### Question 17: "Show me predicted job durations for tomorrow"
**Expected SQL:**
```sql
SELECT 
  j.name as job_name,
  dp.run_date,
  dp.prediction as predicted_duration_minutes
FROM ${catalog}.${feature_schema}.duration_predictions dp
JOIN ${catalog}.${gold_schema}.dim_job j ON dp.job_id = j.job_id
WHERE dp.run_date = CURRENT_DATE() + INTERVAL 1 DAY
ORDER BY predicted_duration_minutes DESC
LIMIT 15;
```
**Expected Result:** Estimated job durations for capacity planning

---

### Question 18: "What is the job success rate drift?"
**Expected SQL:**
```sql
SELECT 
  window.start AS period_start,
  success_rate_drift,
  failure_count_drift,
  duration_drift_pct
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC
LIMIT 10;
```
**Expected Result:** Recent reliability drift metrics showing degradation trends

---

### Question 19: "Show me custom job metrics by job name from monitoring"
**Expected SQL:**
```sql
SELECT 
  slice_value AS job_name,
  AVG(success_rate) AS avg_success_rate,
  SUM(failure_count) AS total_failures,
  AVG(p90_duration) AS avg_p90_duration
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'job_name'
GROUP BY slice_value
ORDER BY total_failures DESC
LIMIT 15;
```
**Expected Result:** Per-job custom metrics from Lakehouse Monitoring

---

### Question 20: "What is the pipeline health score?"
**Expected SQL:**
```sql
SELECT 
  j.name as job_name,
  php.run_date,
  php.prediction as health_score
FROM ${catalog}.${feature_schema}.pipeline_health_predictions php
JOIN ${catalog}.${gold_schema}.dim_job j ON php.job_id = j.job_id
WHERE php.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY php.prediction ASC
LIMIT 15;
```
**Expected Result:** ML-generated pipeline health scores (0-100 scale)

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: Comprehensive job reliability analysis - identify jobs with high failure rates, long durations, and predicted failure risk"
**Expected SQL:**
```sql
WITH job_metrics AS (
  SELECT 
    job_name,
    MEASURE(failure_rate) as failure_rate,
    MEASURE(avg_duration_minutes) as avg_duration,
    MEASURE(total_runs) as total_runs
  FROM ${catalog}.${gold_schema}.mv_job_performance
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
ml_failure_predictions AS (
  SELECT 
    j.name as job_name,
    AVG(jfp.prediction) as avg_failure_probability
  FROM ${catalog}.${feature_schema}.job_failure_predictions jfp
  JOIN ${catalog}.${gold_schema}.dim_job j ON jfp.job_id = j.job_id
  WHERE jfp.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY j.name
)
SELECT 
  jm.job_name,
  jm.failure_rate,
  jm.avg_duration,
  jm.total_runs,
  COALESCE(ml.avg_failure_probability, 0) as predicted_failure_risk,
  CASE 
    WHEN jm.failure_rate > 20 AND ml.avg_failure_probability > 0.5 THEN 'Critical - High Failure Risk'
    WHEN jm.failure_rate > 10 AND jm.avg_duration > 60 THEN 'High Priority - Long & Unreliable'
    WHEN jm.failure_rate > 5 THEN 'Medium Priority - Monitor'
    ELSE 'Normal'
  END as priority
FROM job_metrics jm
LEFT JOIN ml_failure_predictions ml ON jm.job_name = ml.job_name
WHERE jm.failure_rate > 1
ORDER BY jm.failure_rate DESC, predicted_failure_risk DESC
LIMIT 15;
```
**Expected Result:** Prioritized job reliability issues combining metric view aggregations and ML predictions for proactive intervention

---

### Question 22: "🔬 DEEP RESEARCH: Cross-task dependency analysis - identify cascading failure patterns where upstream task failures cause downstream job failures"
**Expected SQL:**
```sql
WITH task_failures AS (
  SELECT 
    ft.workspace_id,
    ft.job_id,
    ft.task_key,
    jt.depends_on,
    COUNT(*) as failure_count,
    ft.run_date
  FROM ${catalog}.${gold_schema}.fact_job_task_run_timeline ft
  JOIN ${catalog}.${gold_schema}.dim_job_task jt 
    ON ft.workspace_id = jt.workspace_id 
    AND ft.job_id = jt.job_id 
    AND ft.task_key = jt.task_key
  WHERE ft.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND ft.result_state != 'SUCCESS'
  GROUP BY ft.workspace_id, ft.job_id, ft.task_key, jt.depends_on, ft.run_date
),
downstream_impact AS (
  SELECT 
    tf1.workspace_id,
    tf1.job_id,
    tf1.task_key as upstream_task,
    COUNT(DISTINCT tf2.task_key) as downstream_failures
  FROM task_failures tf1
  JOIN task_failures tf2 
    ON tf1.workspace_id = tf2.workspace_id 
    AND tf1.job_id = tf2.job_id 
    AND tf1.run_date = tf2.run_date
    AND tf2.depends_on LIKE CONCAT('%', tf1.task_key, '%')
  GROUP BY tf1.workspace_id, tf1.job_id, tf1.task_key
)
SELECT 
  j.name as job_name,
  di.upstream_task,
  di.downstream_failures,
  tf.failure_count as upstream_failure_count
FROM downstream_impact di
JOIN ${catalog}.${gold_schema}.dim_job j ON di.workspace_id = j.workspace_id AND di.job_id = j.job_id
JOIN task_failures tf ON di.workspace_id = tf.workspace_id AND di.job_id = tf.job_id AND di.upstream_task = tf.task_key
WHERE di.downstream_failures > 0
ORDER BY di.downstream_failures DESC, tf.failure_count DESC
LIMIT 15;
```
**Expected Result:** Cascading failure analysis showing how upstream task failures impact downstream tasks - critical for dependency debugging

---

### Question 23: "🔬 DEEP RESEARCH: Job SLA breach prediction with duration forecasting - which jobs are at risk of missing their SLA next week"
**Expected SQL:**
```sql
WITH job_sla_config AS (
  SELECT 
    job_name,
    MEASURE(p95_duration_minutes) as current_p95,
    60 as sla_threshold_minutes
  FROM ${catalog}.${gold_schema}.mv_job_performance
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
duration_forecast AS (
  SELECT 
    j.name as job_name,
    AVG(dp.prediction) as predicted_duration_minutes
  FROM ${catalog}.${feature_schema}.duration_predictions dp
  JOIN ${catalog}.${gold_schema}.dim_job j ON dp.job_id = j.job_id
  WHERE dp.run_date BETWEEN CURRENT_DATE() AND CURRENT_DATE() + INTERVAL 7 DAYS
  GROUP BY j.name
),
sla_risk AS (
  SELECT 
    j.name as job_name,
    AVG(sb.prediction) as breach_probability
  FROM ${catalog}.${feature_schema}.sla_breach_predictions sb
  JOIN ${catalog}.${gold_schema}.dim_job j ON sb.job_id = j.job_id
  WHERE sb.run_date BETWEEN CURRENT_DATE() AND CURRENT_DATE() + INTERVAL 7 DAYS
  GROUP BY j.name
)
SELECT 
  sla.job_name,
  sla.current_p95,
  sla.sla_threshold_minutes,
  df.predicted_duration_minutes,
  sr.breach_probability,
  (df.predicted_duration_minutes - sla.sla_threshold_minutes) as predicted_breach_minutes,
  CASE 
    WHEN sr.breach_probability > 0.7 THEN 'Very High Risk'
    WHEN sr.breach_probability > 0.5 THEN 'High Risk'
    WHEN sr.breach_probability > 0.3 THEN 'Medium Risk'
    ELSE 'Low Risk'
  END as risk_level
FROM job_sla_config sla
JOIN duration_forecast df ON sla.job_name = df.job_name
JOIN sla_risk sr ON sla.job_name = sr.job_name
WHERE sr.breach_probability > 0.2
ORDER BY sr.breach_probability DESC, predicted_breach_minutes DESC
LIMIT 15;
```
**Expected Result:** SLA breach risk assessment combining historical P95, ML duration forecasts, and breach probability predictions

---

### Question 24: "🔬 DEEP RESEARCH: Job retry effectiveness and self-healing analysis - which failed jobs succeed on retry vs require manual intervention"
**Expected SQL:**
```sql
WITH job_retry_patterns AS (
  SELECT 
    j.name as job_name,
    COUNT(*) as total_failures,
    SUM(CASE WHEN f.trigger_type = 'RETRY' THEN 1 ELSE 0 END) as retry_attempts,
    SUM(CASE WHEN f.trigger_type = 'RETRY' AND f.is_success = TRUE THEN 1 ELSE 0 END) as successful_retries
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
  JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
  WHERE f.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND f.result_state IN ('FAILED', 'RETRY')
  GROUP BY j.name
),
ml_retry_predictions AS (
  SELECT 
    j.name as job_name,
    AVG(rsp.prediction) as predicted_retry_success_rate
  FROM ${catalog}.${feature_schema}.retry_success_predictions rsp
  JOIN ${catalog}.${gold_schema}.dim_job j ON rsp.job_id = j.job_id
  WHERE rsp.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY j.name
)
SELECT 
  jrp.job_name,
  jrp.total_failures,
  jrp.retry_attempts,
  jrp.successful_retries,
  CASE 
    WHEN jrp.retry_attempts > 0 THEN jrp.successful_retries * 100.0 / jrp.retry_attempts
    ELSE 0
  END as historical_retry_success_rate,
  COALESCE(rp.predicted_retry_success_rate, 0) as ml_predicted_retry_rate,
  CASE 
    WHEN jrp.successful_retries * 100.0 / NULLIF(jrp.retry_attempts, 0) > 80 THEN 'Self-Healing'
    WHEN jrp.successful_retries * 100.0 / NULLIF(jrp.retry_attempts, 0) > 50 THEN 'Partial Self-Healing'
    ELSE 'Manual Intervention Required'
  END as retry_effectiveness
FROM job_retry_patterns jrp
LEFT JOIN ml_retry_predictions rp ON jrp.job_name = rp.job_name
WHERE jrp.retry_attempts > 0
ORDER BY jrp.total_failures DESC, historical_retry_success_rate ASC
LIMIT 15;
```
**Expected Result:** Retry pattern analysis combining historical effectiveness and ML predictions - identifies jobs needing manual fixes vs auto-recovery

---

### Question 25: "🔬 DEEP RESEARCH: Multi-dimensional job health scoring - combine success rate, duration performance, retry patterns, and ML health scores for comprehensive reliability dashboard"
**Expected SQL:**
```sql
WITH job_reliability AS (
  SELECT 
    job_name,
    MEASURE(success_rate) as success_rate,
    MEASURE(failure_rate) as failure_rate,
    MEASURE(avg_duration_minutes) as avg_duration,
    MEASURE(p95_duration_minutes) as p95_duration,
    MEASURE(total_runs) as total_runs
  FROM ${catalog}.${gold_schema}.mv_job_performance
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
ml_health AS (
  SELECT 
    j.name as job_name,
    AVG(php.prediction) as ml_health_score
  FROM ${catalog}.${feature_schema}.pipeline_health_predictions php
  JOIN ${catalog}.${gold_schema}.dim_job j ON php.job_id = j.job_id
  WHERE php.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY j.name
),
drift_metrics AS (
  SELECT 
    slice_value as job_name,
    AVG(success_rate_drift) as avg_success_drift,
    AVG(duration_drift_pct) as avg_duration_drift
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND slice_key = 'job_name'
  GROUP BY slice_value
)
SELECT 
  jr.job_name,
  jr.success_rate,
  jr.failure_rate,
  jr.avg_duration,
  jr.p95_duration,
  jr.total_runs,
  COALESCE(mh.ml_health_score, 50) as ml_health_score,
  COALESCE(dm.avg_success_drift, 0) as success_drift,
  COALESCE(dm.avg_duration_drift, 0) as duration_drift,
  (jr.success_rate + COALESCE(mh.ml_health_score, 50) - ABS(COALESCE(dm.avg_success_drift, 0)) * 10) / 2.0 as composite_health_score,
  CASE 
    WHEN jr.failure_rate > 20 OR mh.ml_health_score < 50 THEN 'Critical'
    WHEN jr.failure_rate > 10 OR dm.avg_success_drift < -5 THEN 'Warning'
    WHEN jr.success_rate > 95 AND mh.ml_health_score > 80 THEN 'Excellent'
    ELSE 'Normal'
  END as health_status
FROM job_reliability jr
LEFT JOIN ml_health mh ON jr.job_name = mh.job_name
LEFT JOIN drift_metrics dm ON jr.job_name = dm.job_name
WHERE jr.total_runs >= 10
ORDER BY composite_health_score ASC
LIMIT 20;
```
**Expected Result:** Comprehensive multi-dimensional job health dashboard combining metric views, ML predictions, and drift detection - executive reliability report

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
| **H. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🔄 **Reliability**

---

## References

### 📊 Semantic Layer Framework (Essential Reading)
- [**Metrics Inventory**](../../docs/reference/metrics-inventory.md) - **START HERE**: Complete inventory of 277 measurements across TVFs, Metric Views, and Custom Metrics
- [**Semantic Layer Rationalization**](../../docs/reference/semantic-layer-rationalization.md) - Design rationale: why overlaps are intentional and complementary
- [**Genie Asset Selection Guide**](../../docs/reference/genie-asset-selection-guide.md) - Quick decision tree for choosing correct asset type

### 📈 Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions for Job Monitor
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns and required filters
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md) - 50 reliability-specific custom metrics

### 📁 Asset Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 12 Reliability TVFs
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 5 Reliability ML Models

### 🚀 Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting

