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
SELECT * FROM ${catalog}.${gold_schema}.get_failed_jobs_summary(
  1,
  1
)
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
SELECT * FROM ${catalog}.${gold_schema}.get_job_duration_percentiles(
  30
)
ORDER BY p99_duration DESC
LIMIT 15;
```
**Expected Result:** P50/P90/P95/P99 duration statistics for all jobs

---

### Question 7: "Which jobs have the lowest success rate?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_success_rates(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  5
)
ORDER BY success_rate ASC
LIMIT 10;
```
**Expected Result:** Jobs with poorest reliability requiring attention

---

### Question 8: "Show me job failure trends"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_failure_patterns(
  30
)
ORDER BY failure_count DESC;
```
**Expected Result:** Failure patterns by error category over last 30 days

---

### Question 9: "What jobs are running longer than their SLA?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_long_running_jobs(
  7,
  60
)
ORDER BY exceeded_by_minutes DESC
LIMIT 20;
```
**Expected Result:** Jobs exceeding 60-minute threshold with SLA breach details

---

### Question 10: "Show me job retry analysis"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_retry_analysis(
  30
)
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
SELECT * FROM ${catalog}.${gold_schema}.get_repair_cost_analysis(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING
)
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
ml_predictions AS (
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
LEFT JOIN ml_predictions ml ON jm.job_name = ml.job_name
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
retry_predictions AS (
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
LEFT JOIN retry_predictions rp ON jrp.job_name = rp.job_name
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





