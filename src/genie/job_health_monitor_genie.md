# Job Health Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Job Reliability Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks job reliability and execution analytics. Enables DevOps, data engineers, and SREs to query job success rates, failure patterns, and performance metrics without SQL.

**Powered by:**
- 1 Metric View (job_performance)
- 12 Table-Valued Functions (job status, failure analysis, cost queries)
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
│  "What's the current success rate?"→ Metric View (job_performance)│
│  "Show me job success by X"        → Metric View (job_performance)│
│  ─────────────────────────────────────────────────────────────  │
│  "Is success rate degrading?"      → Custom Metrics (_drift_metrics)│
│  "Failure trend since last week"   → Custom Metrics (_profile_metrics)│
│  ─────────────────────────────────────────────────────────────  │
│  "Which jobs failed today?"        → TVF (get_failed_jobs)       │
│  "Top 10 failing jobs"             → TVF (get_job_success_rate) │
│  "Jobs slower than threshold"      → TVF (get_job_duration_percentiles)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Current success rate** | Metric View | "Job success rate" → `job_performance` |
| **Trend over time** | Custom Metrics | "Is reliability degrading?" → `_drift_metrics` |
| **List of failed jobs** | TVF | "Failed jobs today" → `get_failed_jobs` |
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
2. **Primary Source:** Use job_performance metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for "which jobs", "top N", "list" queries
4. **Trends:** For "is success rate degrading?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 7 days
6. **Aggregation:** Use COUNT for volumes, AVG for averages
7. **Sorting:** Sort by failure_rate DESC or duration DESC
8. **Limits:** Top 10-20 for ranking queries
9. **Percentages:** Success/failure rates as % with 1 decimal
10. **Duration:** Show in minutes for readability
11. **Synonyms:** job=workflow=pipeline, failure=error=crash
12. **ML Predictions:** For "likely to fail" → query job_failure_predictions
13. **Failed Jobs:** For "failed jobs today" → use get_failed_jobs TVF
14. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
15. **Context:** Explain FAILED vs ERROR vs TIMED_OUT
16. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

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

## ████ SECTION G: ML MODEL INTEGRATION (5 Models) ████

### Reliability ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `job_failure_predictor` | `job_failure_predictions` | `failure_probability`, `will_fail` | "Will this job fail?" |
| `job_duration_forecaster` | `job_duration_predictions` | `predicted_duration_sec` | "How long will it take?" |
| `sla_breach_predictor` | `incident_impact_predictions` | `breach_probability` | "Will SLA breach?" |
| `pipeline_health_scorer` | `pipeline_health_scores` | `health_score` (0-100) | "Pipeline health score" |
| `retry_success_predictor` | `retry_success_predictions` | `retry_success_prob` | "Will retry succeed?" |

### ML Model Usage Patterns

#### job_failure_predictor (Failure Prediction)
- **Question Triggers:** "will fail", "likely to fail", "at risk", "failure prediction"
- **Query Pattern:**
```sql
SELECT job_name, failure_probability, will_fail, risk_factors
FROM ${catalog}.${gold_schema}.job_failure_predictions
WHERE prediction_date = CURRENT_DATE()
  AND failure_probability > 0.5
ORDER BY failure_probability DESC;
```
- **Interpretation:** `failure_probability > 0.5` = High risk of failure

#### job_duration_forecaster (Duration Prediction)
- **Question Triggers:** "how long", "duration estimate", "expected time", "forecast duration"
- **Query Pattern:**
```sql
SELECT job_name, predicted_duration_sec / 60.0 as predicted_minutes, 
       confidence_interval_lower, confidence_interval_upper
FROM ${catalog}.${gold_schema}.job_duration_predictions
WHERE job_name = '{job_name}'
ORDER BY prediction_date DESC LIMIT 1;
```

#### pipeline_health_scorer (Health Score)
- **Question Triggers:** "pipeline health", "health score", "pipeline status", "healthy pipelines"
- **Query Pattern:**
```sql
SELECT pipeline_name, health_score, 
       CASE WHEN health_score >= 90 THEN 'Excellent'
            WHEN health_score >= 70 THEN 'Good'
            WHEN health_score >= 50 THEN 'Warning'
            ELSE 'Critical' END as health_status
FROM ${catalog}.${gold_schema}.pipeline_health_scores
ORDER BY health_score ASC;
```
- **Interpretation:** `health_score < 70` = Needs attention

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Will job X fail?"                      → ML: job_failure_predictions
"How long will job X take?"             → ML: job_duration_predictions
"Pipeline health score"                 → ML: pipeline_health_scores
"Will SLA be breached?"                 → ML: incident_impact_predictions
────────────────────────────────────────────────────
"What is the success rate?"             → Metric View: job_performance
"Is reliability trending down?"         → Custom Metrics: _drift_metrics
"Show failed jobs today"                → TVF: get_failed_jobs
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

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

### Question 11: "What jobs have the highest retry rate?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_retry_analysis(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY retry_rate DESC
LIMIT 20;
```
**Expected Result:** Jobs with highest retry rates

---

### Question 12: "Show me job SLA compliance"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_sla_compliance(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY sla_breach_count DESC
LIMIT 20;
```
**Expected Result:** Jobs with SLA breaches

---

### Question 13: "Which jobs have performance regression?"
**Expected SQL:**
```sql
SELECT 
  job_name,
  avg_duration_current,
  avg_duration_previous,
  (avg_duration_current - avg_duration_previous) / avg_duration_previous * 100 as regression_pct
FROM ${catalog}.${gold_schema}.pipeline_health_scores
WHERE avg_duration_current > avg_duration_previous * 1.2
ORDER BY regression_pct DESC
LIMIT 20;
```
**Expected Result:** Jobs with >20% duration increase

---

### Question 14: "What's the job cost per run?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_most_expensive_jobs(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  20
)
ORDER BY cost_per_run DESC;
```
**Expected Result:** Jobs sorted by cost per execution

---

### Question 15: "Will retrying the failed job succeed?"
**Expected SQL:**
```sql
SELECT 
  job_name,
  run_id,
  retry_success_prob,
  error_type,
  recommendation
FROM ${catalog}.${gold_schema}.retry_success_predictions
WHERE retry_success_prob > 0.5
ORDER BY retry_success_prob DESC
LIMIT 20;
```
**Expected Result:** Jobs likely to succeed on retry

---

### Question 16: "Show me pipeline health by owner"
**Expected SQL:**
```sql
SELECT 
  owner,
  AVG(health_score) as avg_health_score,
  COUNT(*) as job_count
FROM ${catalog}.${gold_schema}.pipeline_health_scores
GROUP BY owner
ORDER BY avg_health_score ASC
LIMIT 20;
```
**Expected Result:** Health scores aggregated by owner

---

### Question 17: "What is the average duration by job type?"
**Expected SQL:**
```sql
SELECT 
  job_type,
  AVG(duration_minutes) as avg_duration_minutes,
  COUNT(*) as run_count
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY job_type
ORDER BY avg_duration_minutes DESC;
```
**Expected Result:** Duration by job type

---

### Question 18: "Show me jobs with incident impact"
**Expected SQL:**
```sql
SELECT 
  job_name,
  affected_jobs,
  downstream_consumers,
  severity
FROM ${catalog}.${gold_schema}.incident_impact_predictions
WHERE severity IN ('HIGH', 'CRITICAL')
ORDER BY downstream_consumers DESC
LIMIT 20;
```
**Expected Result:** Jobs with high blast radius

---

### Question 19: "What self-healing actions are recommended?"
**Expected SQL:**
```sql
SELECT 
  job_name,
  recommended_action,
  confidence,
  success_probability
FROM ${catalog}.${gold_schema}.self_healing_recommendations
WHERE confidence > 0.7
ORDER BY success_probability DESC
LIMIT 20;
```
**Expected Result:** High-confidence remediation recommendations

---

### Question 20: "Show me DLT pipeline update failures"
**Expected SQL:**
```sql
SELECT 
  pipeline_name,
  update_id,
  state,
  error_message,
  duration_minutes
FROM ${catalog}.${gold_schema}.fact_pipeline_update_timeline
WHERE state = 'FAILED'
  AND update_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY update_date DESC
LIMIT 20;
```
**Expected Result:** Recent DLT pipeline failures

---

### 🔬 DEEP RESEARCH QUESTIONS (Complex Multi-Source Analysis)

### Question 21: "Which jobs have the highest failure cost impact considering both direct compute cost and downstream pipeline delays, and which ones would benefit most from self-healing automation?"
**Deep Research Complexity:** Combines failure analysis, cost impact calculation, downstream delay estimation, incident blast radius, and self-healing recommendation assessment.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Calculate direct failure costs
WITH failure_costs AS (
  SELECT 
    job_name,
    COUNT(*) as failure_count,
    SUM(compute_cost_usd) as direct_failure_cost,
    AVG(duration_minutes) as avg_failure_duration
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE result_state = 'FAILED'
    AND run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
-- Step 2: Get downstream impact from incident predictions
downstream_impact AS (
  SELECT 
    job_name,
    affected_jobs,
    downstream_consumers,
    severity,
    CASE severity 
      WHEN 'CRITICAL' THEN 4
      WHEN 'HIGH' THEN 3
      WHEN 'MEDIUM' THEN 2
      ELSE 1 
    END as severity_weight
  FROM ${catalog}.${gold_schema}.incident_impact_predictions
),
-- Step 3: Estimate downstream delay cost (assuming $50/hour pipeline delay cost)
delay_cost AS (
  SELECT 
    d.job_name,
    d.affected_jobs * f.avg_failure_duration * 50 / 60 as estimated_delay_cost
  FROM downstream_impact d
  JOIN failure_costs f ON d.job_name = f.job_name
),
-- Step 4: Get self-healing recommendations
self_healing AS (
  SELECT 
    job_name,
    recommended_action,
    confidence,
    success_probability
  FROM ${catalog}.${gold_schema}.self_healing_recommendations
  WHERE confidence > 0.6
)
SELECT 
  f.job_name,
  f.failure_count,
  f.direct_failure_cost,
  d.affected_jobs as downstream_jobs_impacted,
  d.severity,
  COALESCE(dc.estimated_delay_cost, 0) as estimated_delay_cost,
  f.direct_failure_cost + COALESCE(dc.estimated_delay_cost, 0) as total_failure_impact,
  sh.recommended_action as self_healing_action,
  sh.success_probability as automation_success_rate,
  CASE 
    WHEN sh.success_probability > 0.8 AND f.failure_count > 5 THEN '🟢 HIGH VALUE - AUTOMATE NOW'
    WHEN sh.success_probability > 0.6 THEN '🟡 MEDIUM VALUE - CONSIDER AUTOMATION'
    ELSE '🔴 MANUAL INTERVENTION RECOMMENDED'
  END as automation_recommendation
FROM failure_costs f
LEFT JOIN downstream_impact d ON f.job_name = d.job_name
LEFT JOIN delay_cost dc ON f.job_name = dc.job_name
LEFT JOIN self_healing sh ON f.job_name = sh.job_name
WHERE f.failure_count >= 3
ORDER BY (f.direct_failure_cost + COALESCE(dc.estimated_delay_cost, 0)) DESC
LIMIT 15;
```
**Expected Result:** Jobs ranked by total failure impact (direct + downstream costs) with self-healing automation recommendations.

---

### Question 22: "What is the predicted reliability for our top 10 most expensive jobs next week, and what proactive actions can prevent predicted failures?"
**Deep Research Complexity:** Combines cost ranking, ML failure predictions, risk factor analysis, and proactive remediation recommendations.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify top 10 most expensive jobs
WITH expensive_jobs AS (
  SELECT 
    job_name,
    SUM(compute_cost_usd) as total_cost_30d,
    AVG(compute_cost_usd) as avg_cost_per_run,
    COUNT(*) as run_count
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
  ORDER BY total_cost_30d DESC
  LIMIT 10
),
-- Step 2: Get ML failure predictions for these jobs
failure_predictions AS (
  SELECT 
    job_name,
    failure_probability,
    will_fail,
    risk_factors
  FROM ${catalog}.${gold_schema}.job_failure_predictions
  WHERE prediction_date = CURRENT_DATE()
),
-- Step 3: Get historical failure patterns
historical_patterns AS (
  SELECT 
    job_name,
    SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as historical_failure_rate,
    MODE(termination_code) as most_common_failure_code
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
-- Step 4: Get health scores and recommendations
health_recs AS (
  SELECT 
    job_name,
    health_score,
    health_status,
    trend_indicator
  FROM ${catalog}.${gold_schema}.pipeline_health_scores
)
SELECT 
  e.job_name,
  e.total_cost_30d,
  e.avg_cost_per_run,
  e.run_count,
  COALESCE(fp.failure_probability, 0) as predicted_failure_prob_next_week,
  fp.risk_factors,
  hp.historical_failure_rate,
  hp.most_common_failure_code,
  hr.health_score,
  hr.trend_indicator,
  CASE 
    WHEN fp.failure_probability > 0.7 THEN '🔴 CRITICAL: ' || fp.risk_factors
    WHEN fp.failure_probability > 0.4 THEN '🟠 WARNING: Review ' || fp.risk_factors
    WHEN hr.trend_indicator = 'DECLINING' THEN '🟡 MONITOR: Health declining'
    ELSE '🟢 HEALTHY: No immediate action needed'
  END as proactive_action,
  e.total_cost_30d * COALESCE(fp.failure_probability, hp.historical_failure_rate/100) as projected_failure_cost_at_risk
FROM expensive_jobs e
LEFT JOIN failure_predictions fp ON e.job_name = fp.job_name
LEFT JOIN historical_patterns hp ON e.job_name = hp.job_name
LEFT JOIN health_recs hr ON e.job_name = hr.job_name
ORDER BY projected_failure_cost_at_risk DESC;
```
**Expected Result:** Top expensive jobs with predicted failure probability, specific risk factors, and prioritized proactive actions to prevent failures.

---

### Question 23: "What is the optimal retry strategy for each job based on historical retry success patterns, failure modes, and cost-benefit analysis?"
**Deep Research Complexity:** Analyzes retry patterns, success rates by retry count, failure categorization, and cost of retries to recommend optimal retry strategies.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Analyze retry patterns by job
WITH retry_analysis AS (
  SELECT 
    job_name,
    attempt_number,
    COUNT(*) as attempts_at_this_level,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) as successes,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
    AVG(duration_seconds) as avg_duration,
    AVG(compute_cost_usd) as avg_cost_per_attempt
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name, attempt_number
),
-- Step 2: Get failure categorization
failure_modes AS (
  SELECT 
    job_name,
    termination_code,
    COUNT(*) as failure_count,
    CASE 
      WHEN termination_code IN ('USER_CANCELED', 'DRIVER_ERROR', 'CLOUD_FAILURE') THEN 'TRANSIENT'
      WHEN termination_code IN ('INVALID_CLUSTER_REQUEST', 'DBFS_DOWN', 'INIT_SCRIPT_FAILURE') THEN 'INFRASTRUCTURE'
      ELSE 'APPLICATION'
    END as failure_category
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE result_state = 'FAILED'
    AND run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name, termination_code
),
-- Step 3: Get retry success predictions
retry_predictions AS (
  SELECT 
    job_name,
    retry_success_probability,
    recommended_max_retries,
    recommended_retry_delay_seconds
  FROM ${catalog}.${gold_schema}.retry_success_predictions
  WHERE prediction_date = CURRENT_DATE()
),
-- Step 4: Calculate optimal strategy
optimal_strategy AS (
  SELECT 
    r.job_name,
    MAX(CASE WHEN r.attempt_number = 1 THEN r.success_rate END) as first_attempt_success_rate,
    MAX(CASE WHEN r.attempt_number = 2 THEN r.success_rate END) as second_attempt_success_rate,
    MAX(CASE WHEN r.attempt_number = 3 THEN r.success_rate END) as third_attempt_success_rate,
    SUM(r.avg_cost_per_attempt * r.attempts_at_this_level) / SUM(r.attempts_at_this_level) as avg_total_cost,
    MODE(fm.failure_category) as primary_failure_category,
    p.recommended_max_retries as ml_recommended_retries,
    p.retry_success_probability as ml_retry_success_prob
  FROM retry_analysis r
  LEFT JOIN failure_modes fm ON r.job_name = fm.job_name
  LEFT JOIN retry_predictions p ON r.job_name = p.job_name
  GROUP BY r.job_name, p.recommended_max_retries, p.retry_success_probability
)
SELECT 
  job_name,
  ROUND(first_attempt_success_rate, 1) as first_try_success_pct,
  ROUND(second_attempt_success_rate, 1) as second_try_success_pct,
  ROUND(third_attempt_success_rate, 1) as third_try_success_pct,
  primary_failure_category,
  COALESCE(ml_recommended_retries, 
    CASE 
      WHEN primary_failure_category = 'TRANSIENT' AND second_attempt_success_rate > 80 THEN 2
      WHEN primary_failure_category = 'TRANSIENT' THEN 3
      WHEN primary_failure_category = 'INFRASTRUCTURE' THEN 2
      ELSE 1
    END
  ) as recommended_max_retries,
  CASE 
    WHEN primary_failure_category = 'TRANSIENT' THEN 'Exponential backoff: 30s, 60s, 120s'
    WHEN primary_failure_category = 'INFRASTRUCTURE' THEN 'Fixed delay: 300s between retries'
    ELSE 'No auto-retry - fix root cause'
  END as recommended_retry_strategy,
  ROUND(avg_total_cost * (1 + COALESCE(ml_recommended_retries, 2)), 2) as estimated_cost_with_retries,
  CASE 
    WHEN first_attempt_success_rate > 95 THEN '🟢 NO RETRY NEEDED: High first-attempt success'
    WHEN COALESCE(ml_retry_success_prob, second_attempt_success_rate/100) > 0.8 THEN '🟢 RETRY WORTHWHILE: High retry success rate'
    WHEN primary_failure_category = 'APPLICATION' THEN '🔴 FIX CODE: Retries won''t help'
    ELSE '🟡 LIMITED RETRY: Set max 2 with monitoring'
  END as retry_recommendation
FROM optimal_strategy
ORDER BY first_attempt_success_rate ASC
LIMIT 20;
```
**Expected Result:** Jobs with retry analysis showing success rates by attempt, failure categories, ML recommendations, and optimal retry strategies with cost estimates.

---

### Question 24: "Which pipelines have cascading failure patterns where one job failure triggers multiple downstream failures, and what's the blast radius and recovery strategy?"
**Deep Research Complexity:** Analyzes job dependencies, failure propagation patterns, and calculates blast radius to recommend circuit breaker and recovery strategies.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Build job dependency graph from task dependencies
WITH job_dependencies AS (
  SELECT DISTINCT
    jt.job_id,
    jt.task_key as job_name,
    d.dependent_task as downstream_job
  FROM ${catalog}.${gold_schema}.dim_job_task jt
  LEFT JOIN (
    SELECT task_key, EXPLODE(depends_on) as dependent_task 
    FROM ${catalog}.${gold_schema}.dim_job_task
    WHERE depends_on IS NOT NULL
  ) d ON jt.task_key = d.task_key
),
-- Step 2: Identify jobs that failed and caused downstream failures
failure_cascades AS (
  SELECT 
    jr.job_name as root_failure_job,
    jr.run_id as root_run_id,
    jr.start_time as failure_time,
    jr.termination_code as root_failure_code,
    jr_downstream.job_name as downstream_job,
    jr_downstream.result_state as downstream_state,
    jr_downstream.start_time as downstream_start_time
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline jr
  JOIN job_dependencies jd ON jr.job_name = jd.job_name
  JOIN ${catalog}.${gold_schema}.fact_job_run_timeline jr_downstream 
    ON jd.downstream_job = jr_downstream.job_name
    AND jr_downstream.start_time BETWEEN jr.start_time AND jr.start_time + INTERVAL 4 HOURS
    AND jr_downstream.result_state IN ('FAILED', 'SKIPPED', 'CANCELED')
  WHERE jr.result_state = 'FAILED'
    AND jr.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
-- Step 3: Calculate blast radius metrics
blast_radius AS (
  SELECT 
    root_failure_job,
    COUNT(DISTINCT downstream_job) as direct_downstream_failures,
    COUNT(*) as total_cascade_events,
    COUNT(DISTINCT DATE_TRUNC('day', failure_time)) as days_with_cascades,
    AVG(TIMESTAMPDIFF(MINUTE, failure_time, downstream_start_time)) as avg_propagation_time_mins
  FROM failure_cascades
  GROUP BY root_failure_job
),
-- Step 4: Get pipeline health context
pipeline_context AS (
  SELECT 
    job_name,
    health_score,
    health_status,
    trend_indicator
  FROM ${catalog}.${gold_schema}.pipeline_health_scores
),
-- Step 5: Calculate recovery metrics
recovery_metrics AS (
  SELECT 
    job_name,
    AVG(CASE WHEN result_state = 'SUCCESS' AND attempt_number > 1 
        THEN duration_seconds END) as avg_recovery_time_seconds,
    SUM(CASE WHEN result_state = 'SUCCESS' AND attempt_number > 1 THEN 1 ELSE 0 END) * 100.0 /
      NULLIF(SUM(CASE WHEN attempt_number > 1 THEN 1 ELSE 0 END), 0) as recovery_success_rate
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
)
SELECT 
  b.root_failure_job,
  b.direct_downstream_failures,
  b.total_cascade_events,
  b.days_with_cascades,
  ROUND(b.avg_propagation_time_mins, 1) as avg_cascade_delay_mins,
  COALESCE(p.health_score, 0) as pipeline_health_score,
  p.trend_indicator,
  ROUND(COALESCE(r.recovery_success_rate, 0), 1) as historical_recovery_rate,
  CASE 
    WHEN b.direct_downstream_failures > 5 THEN '🔴 HIGH BLAST RADIUS: ' || b.direct_downstream_failures || ' downstream jobs at risk'
    WHEN b.direct_downstream_failures > 2 THEN '🟠 MEDIUM BLAST RADIUS: Monitor downstream carefully'
    ELSE '🟢 LOW BLAST RADIUS: Isolated failure impact'
  END as blast_radius_assessment,
  CASE 
    WHEN b.direct_downstream_failures > 5 THEN 'CIRCUIT BREAKER: Implement dependency health check before downstream jobs'
    WHEN b.total_cascade_events > 10 THEN 'RETRY GATE: Add conditional retry based on upstream status'
    WHEN r.recovery_success_rate > 80 THEN 'AUTO-RECOVER: Enable auto-retry with backoff'
    ELSE 'MANUAL INTERVENTION: Alert on-call and pause downstream'
  END as recovery_strategy
FROM blast_radius b
LEFT JOIN pipeline_context p ON b.root_failure_job = p.job_name
LEFT JOIN recovery_metrics r ON b.root_failure_job = r.job_name
ORDER BY b.direct_downstream_failures DESC, b.total_cascade_events DESC
LIMIT 15;
```
**Expected Result:** Jobs that trigger cascade failures with blast radius metrics, propagation timing, and recommended circuit breaker/recovery strategies.

---

### Question 25: "What's the total operational cost of job failures including compute waste, SLA penalties, team productivity loss, and incident response time, and how can we reduce it?"
**Deep Research Complexity:** Quantifies full cost of failures including direct costs, opportunity costs, and team impact to prioritize reliability investments.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Calculate direct compute waste from failures
WITH compute_waste AS (
  SELECT 
    job_name,
    COUNT(*) as failed_runs,
    SUM(compute_cost_usd) as direct_compute_waste,
    SUM(duration_seconds) / 3600.0 as wasted_compute_hours,
    AVG(compute_cost_usd) as avg_cost_per_failure
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE result_state = 'FAILED'
    AND run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
-- Step 2: Estimate SLA penalty impact (heuristic based on job criticality)
sla_impact AS (
  SELECT 
    jr.job_name,
    COUNT(*) as sla_breaches,
    SUM(CASE 
      WHEN j.job_type = 'STREAMING' THEN 500  -- Critical streaming
      WHEN jr.duration_seconds > 7200 THEN 200  -- Long-running batch
      ELSE 50  -- Standard batch
    END) as estimated_sla_penalty
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline jr
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON jr.job_id = j.job_id
  WHERE jr.result_state = 'FAILED'
    AND jr.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY jr.job_name
),
-- Step 3: Estimate team productivity impact
team_impact AS (
  SELECT 
    job_name,
    COUNT(DISTINCT run_id) * 0.5 as estimated_investigation_hours,  -- 30 min avg investigation per failure
    COUNT(DISTINCT DATE_TRUNC('day', start_time)) * 0.25 as estimated_incident_response_hours,
    COUNT(DISTINCT run_id) * 75 as estimated_productivity_cost  -- $150/hr * 0.5 hr
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE result_state = 'FAILED'
    AND run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
-- Step 4: Get repair/remediation costs
repair_costs AS (
  SELECT 
    job_name,
    SUM(repair_cost_usd) as total_repair_costs,
    COUNT(*) as repair_runs
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE is_repair_run = TRUE
    AND run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_name
),
-- Step 5: Get ML recommendations for cost reduction
ml_recommendations AS (
  SELECT 
    job_name,
    failure_probability,
    risk_factors,
    CASE 
      WHEN failure_probability > 0.5 THEN 'HIGH: Significant reliability investment needed'
      WHEN failure_probability > 0.2 THEN 'MEDIUM: Targeted improvements recommended'
      ELSE 'LOW: Maintenance mode'
    END as investment_priority
  FROM ${catalog}.${gold_schema}.job_failure_predictions
  WHERE prediction_date = CURRENT_DATE()
)
SELECT 
  c.job_name,
  c.failed_runs,
  ROUND(c.direct_compute_waste, 2) as compute_waste_usd,
  ROUND(COALESCE(s.estimated_sla_penalty, 0), 2) as sla_penalty_usd,
  ROUND(COALESCE(t.estimated_productivity_cost, 0), 2) as productivity_cost_usd,
  ROUND(COALESCE(r.total_repair_costs, 0), 2) as repair_costs_usd,
  ROUND(c.direct_compute_waste + COALESCE(s.estimated_sla_penalty, 0) + 
        COALESCE(t.estimated_productivity_cost, 0) + COALESCE(r.total_repair_costs, 0), 2) as total_failure_cost,
  ROUND(t.estimated_investigation_hours, 1) as investigation_hours,
  m.investment_priority,
  m.risk_factors,
  CASE 
    WHEN c.direct_compute_waste + COALESCE(s.estimated_sla_penalty, 0) > 1000 
      THEN '🔴 HIGH COST: Prioritize for reliability engineering'
    WHEN c.failed_runs > 10 THEN '🟠 FREQUENT FAILURES: Implement automated recovery'
    ELSE '🟡 MANAGEABLE: Monitor and optimize incrementally'
  END as cost_reduction_priority,
  CASE 
    WHEN m.risk_factors LIKE '%resource%' THEN 'OPTIMIZE: Right-size compute resources'
    WHEN m.risk_factors LIKE '%timeout%' THEN 'TUNE: Increase timeouts or optimize job'
    WHEN m.risk_factors LIKE '%dependency%' THEN 'DECOUPLE: Add circuit breakers'
    ELSE 'INVESTIGATE: Analyze failure patterns'
  END as cost_reduction_action
FROM compute_waste c
LEFT JOIN sla_impact s ON c.job_name = s.job_name
LEFT JOIN team_impact t ON c.job_name = t.job_name
LEFT JOIN repair_costs r ON c.job_name = r.job_name
LEFT JOIN ml_recommendations m ON c.job_name = m.job_name
ORDER BY (c.direct_compute_waste + COALESCE(s.estimated_sla_penalty, 0) + 
          COALESCE(t.estimated_productivity_cost, 0) + COALESCE(r.total_repair_costs, 0)) DESC
LIMIT 20;
```
**Expected Result:** Total cost of job failures including compute waste, SLA penalties, productivity loss, and repair costs with prioritized cost reduction recommendations.

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

