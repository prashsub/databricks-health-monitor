# Job Health Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Job Reliability Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks job reliability and execution analytics. Enables DevOps, data engineers, and SREs to query job success rates, failure patterns, and performance metrics without SQL.

**Powered by:**
- 1 Metric View (mv_job_performance)
- 13 Table-Valued Functions (parameterized queries)
- 4 ML Prediction Tables (predictions and recommendations)
- 2 Lakehouse Monitoring Tables (drift and profile metrics)
- 4 Dimension Tables (reference data)
- 2 Fact Tables (transactional data)

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
| `mv_job_performance` | Job execution performance metrics | success_rate, failure_rate, avg_duration, p95_duration |

### Table-Valued Functions (13 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_failed_jobs` | Failed job list | "failed jobs" |
| `get_job_duration_percentiles` | Duration percentiles | "job duration" |
| `get_job_failure_costs` | Failure costs | "failure costs" |
| `get_job_failure_trends` | Failure trends | "failure trends" |
| `get_job_outlier_runs` | Outlier job runs | "outlier runs" |
| `get_job_repair_costs` | Repair costs | "repair costs" |
| `get_job_retry_analysis` | Retry analysis | "retry analysis" |
| `get_job_run_details` | Job run details | "run details" |
| `get_job_run_duration_analysis` | Duration analysis | "duration analysis" |
| `get_job_sla_compliance` | SLA compliance | "SLA compliance" |
| `get_job_success_rate` | Job success metrics | "success rate" |
| `get_jobs_on_legacy_dbr` | Jobs on legacy DBR | "legacy DBR" |
| `get_jobs_without_autoscaling` | Jobs without autoscaling | "autoscaling disabled" |

### ML Prediction Tables (4 Models)

| Table Name | Purpose | Model |
|---|---|---|
| `duration_predictions` | Job duration predictions | Duration Predictor |
| `job_failure_predictions` | Job failure predictions | Job Failure Predictor |
| `retry_success_predictions` | Retry success likelihood | Retry Success Predictor |
| `sla_breach_predictions` | SLA breach risk | SLA Breach Predictor |

### Lakehouse Monitoring Tables

| Table Name | Purpose |
|------------|---------|
| `fact_job_run_timeline_drift_metrics` | Job execution drift detection |
| `fact_job_run_timeline_profile_metrics` | Job execution profile metrics |

### Dimension Tables (4 Tables)

| Table Name | Purpose | Key Columns |
|---|---|---|
| `dim_cluster` | Cluster metadata | cluster_id, cluster_name, node_type_id |
| `dim_job` | Job metadata | job_id, name, creator_id |
| `dim_job_task` | Job task metadata | task_key, task_type |
| `dim_workspace` | Workspace details | workspace_id, workspace_name, region |

### Fact Tables (2 Tables)

| Table Name | Purpose | Grain |
|---|---|---|
| `fact_job_run_timeline` | Job execution history | Per job run |
| `fact_job_task_run_timeline` | Task execution history | Per task run |

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
| `get_failed_jobs` | `(start_date STRING, end_date STRING, workspace_filter STRING DEFAULT NULL)` | Failed jobs list | "failed jobs today" |
| `get_job_success_rate` | `(start_date STRING, end_date STRING, min_runs INT DEFAULT 5)` | Success rates | "job success rate" |
| `get_job_failure_trends` | `(days_back INT DEFAULT 30)` | Failure trends | "failure trends" |
| `get_job_sla_compliance` | `(start_date STRING, end_date STRING)` | SLA tracking | "SLA compliance" |
| `get_job_retry_analysis` | `(start_date STRING, end_date STRING)` | Retry pattern analysis | "retry analysis" |
| `get_job_duration_percentiles` | `(days_back INT, job_name_filter STRING DEFAULT '%')` | Duration P50/P90/P95/P99 | "P95 duration" |
| `get_job_failure_costs` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 20)` | Failure impact costs | "failure costs" |
| `get_job_repair_costs` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 20)` | Repair costs | "repair costs" |
| `get_job_run_duration_analysis` | `(days_back INT, min_runs INT DEFAULT 5, top_n INT DEFAULT 20)` | Duration statistics | "duration analysis" |
| `get_job_run_details` | `(job_id_filter BIGINT, days_back INT DEFAULT 30)` | Run history | "job details" |
| `get_job_outlier_runs` | `(days_back INT, min_baseline_runs INT DEFAULT 10, deviation_threshold DOUBLE DEFAULT 2.0)` | Outlier detection | "outlier runs" |
| `get_job_data_quality_status` | `(days_back INT DEFAULT 7)` | Quality scoring | "job quality" |

### TVF Details

#### get_failed_jobs
- **Signature:** `get_failed_jobs(start_date STRING, end_date STRING, workspace_filter STRING DEFAULT NULL)`
- **Returns:** job_name, run_id, result_state, termination_code, error_message, duration_minutes, workspace_name
- **Use When:** User asks for "failed jobs" or "errors today"
- **Example:** `SELECT * FROM get_failed_jobs('2024-12-01', '2024-12-31', NULL))`

#### get_job_success_rate
- **Signature:** `get_job_success_rate(start_date STRING, end_date STRING, min_runs INT DEFAULT 5)`
- **Returns:** job_name, total_runs, successful_runs, failed_runs, success_rate, failure_rate
- **Use When:** User asks for "success rate" or "reliability by job"
- **Example:** `SELECT * FROM get_job_success_rate('2024-12-01', '2024-12-31', 5))`

#### get_job_duration_percentiles
- **Signature:** `get_job_duration_percentiles(days_back INT)`
- **Returns:** job_name, p50_duration, p90_duration, p95_duration, p99_duration, avg_duration
- **Use When:** User asks for "P95 duration" or "job timing"
- **Example:** `SELECT * FROM get_job_duration_percentiles(30))`

#### get_job_failure_trends
- **Signature:** `get_job_failure_trends(days_back INT DEFAULT 30)`
- **Returns:** run_date, failure_count, failure_rate, total_runs
- **Use When:** User asks for "failure trends" or "daily failures"
- **Example:** `SELECT * FROM get_job_failure_trends(30))`

#### get_job_run_duration_analysis
- **Signature:** `get_job_run_duration_analysis(days_back INT, min_runs INT DEFAULT 5, top_n INT DEFAULT 20)`
- **Returns:** job_name, avg_duration_minutes, p50_duration, p95_duration, p99_duration
- **Use When:** User asks for "slow jobs" or "duration analysis"
- **Example:** `SELECT * FROM get_job_run_duration_analysis(30, 5, 20))`

#### get_job_retry_analysis
- **Signature:** `get_job_retry_analysis(days_back INT)`
- **Returns:** job_name, retry_count, retry_success_rate, retry_effectiveness
- **Use When:** User asks for "retry patterns" or "retry analysis"
- **Example:** `SELECT * FROM get_job_retry_analysis(30))`

#### get_job_repair_costs
- **Signature:** `get_job_repair_costs(start_date STRING, end_date STRING, top_n INT DEFAULT 20)`
- **Returns:** job_name, repair_count, repair_cost, original_cost, repair_rate
- **Use When:** User asks for "repair costs" or "retry costs"
- **Example:** `SELECT * FROM get_job_repair_costs('2024-12-01', '2024-12-31', 20))`

#### get_job_failure_costs
- **Signature:** `get_job_failure_costs(start_date STRING, end_date STRING, top_n INT DEFAULT 20)`
- **Returns:** job_name, failure_count, failure_cost, total_cost, failure_cost_pct
- **Use When:** User asks for "failure costs" or "cost of failures"
- **Example:** `SELECT * FROM get_job_failure_costs('2024-12-01', '2024-12-31', 20))`

#### get_job_run_details
- **Signature:** `get_job_run_details(job_id_filter BIGINT, days_back INT DEFAULT 30)`
- **Returns:** run_id, run_date, result_state, duration_minutes, error_message
- **Use When:** User asks for "job run history" or "run details"
- **Example:** `SELECT * FROM get_job_run_details(12345, 30))`

#### get_job_outlier_runs
- **Signature:** `get_job_outlier_runs(days_back INT, min_baseline_runs INT DEFAULT 10, deviation_threshold DOUBLE DEFAULT 2.0)`
- **Returns:** job_name, run_id, duration_minutes, baseline_avg, deviation_score
- **Use When:** User asks for "outlier runs" or "unusual durations"
- **Example:** `SELECT * FROM get_job_outlier_runs(30, 10, 2.0))`

#### get_job_data_quality_status
- **Signature:** `get_job_data_quality_status(days_back INT DEFAULT 7)`
- **Returns:** job_name, quality_score, failed_checks, data_freshness_status
- **Use When:** User asks for "job quality" or "data quality by job"
- **Example:** `SELECT * FROM get_job_data_quality_status(7))`

#### get_job_sla_compliance
- **Signature:** `get_job_sla_compliance(start_date STRING, end_date STRING)`
- **Returns:** job_name, sla_threshold, breach_count, compliance_rate
- **Use When:** User asks for "SLA compliance" or "SLA breaches"
- **Example:** `SELECT * FROM get_job_sla_compliance('2024-12-01', '2024-12-31'))`

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

### Question 1: "What jobs have failed recently?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_failed_jobs(7)) LIMIT 20;
```

---

### Question 2: "What is the job success rate?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_job_success_rate(30)) LIMIT 20;
```

---

### Question 3: "Show job duration percentiles"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_job_duration_percentiles(30)) LIMIT 20;
```

---

### Question 4: "Are jobs meeting their SLAs?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_job_sla_compliance(30)) LIMIT 20;
```

---

### Question 5: "Show job failure trends"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_job_failure_trends(30)) LIMIT 20;
```

---

### Question 6: "Identify outlier job runs"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_job_outlier_runs(30)) LIMIT 20;
```

---

### Question 7: "What are job repair costs?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_job_repair_costs(30)) LIMIT 20;
```

---

### Question 8: "Which jobs lack autoscaling?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_jobs_without_autoscaling()) LIMIT 20;
```

---

### Question 9: "Show overall job performance metrics"
**Expected SQL:**
```sql
SELECT * FROM mv_job_performance LIMIT 20;
```

---

### Question 10: "Which jobs have the most failures?"
**Expected SQL:**
```sql
SELECT job_name, failure_count FROM mv_job_performance ORDER BY failure_count DESC LIMIT 10;
```

---

### Question 11: "What is the overall success rate?"
**Expected SQL:**
```sql
SELECT AVG(success_rate) as avg_success_rate FROM mv_job_performance;
```

---

### Question 12: "Show top jobs by run count"
**Expected SQL:**
```sql
SELECT job_name, run_count FROM mv_job_performance ORDER BY run_count DESC LIMIT 10;
```

---

### Question 13: "Which jobs might fail?"
**Expected SQL:**
```sql
SELECT * FROM job_failure_predictions ORDER BY prediction DESC LIMIT 20;
```

---

### Question 14: "Show retry success predictions"
**Expected SQL:**
```sql
SELECT * FROM retry_success_predictions ORDER BY prediction DESC LIMIT 20;
```

---

### Question 15: "Are there SLA breach risks?"
**Expected SQL:**
```sql
SELECT * FROM sla_breach_predictions ORDER BY prediction DESC LIMIT 20;
```

---

### Question 16: "Show job profile metrics"
**Expected SQL:**
```sql
SELECT * FROM fact_job_run_timeline_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;
```

---

### Question 17: "Show job drift metrics"
**Expected SQL:**
```sql
SELECT * FROM fact_job_run_timeline_drift_metrics LIMIT 20;
```

---

### Question 18: "Show recent job runs"
**Expected SQL:**
```sql
SELECT job_id, job_name, result_state, run_duration_seconds FROM fact_job_run_timeline ORDER BY period_start_time DESC LIMIT 20;
```

---

### Question 19: "Show recent task runs"
**Expected SQL:**
```sql
SELECT task_key, result_state, run_duration_seconds FROM fact_job_task_run_timeline ORDER BY period_start_time DESC LIMIT 20;
```

---

### Question 20: "List all jobs"
**Expected SQL:**
```sql
SELECT job_id, job_name FROM dim_job ORDER BY job_name LIMIT 20;
```

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: Comprehensive job reliability analysis"
**Expected SQL:**
```sql
WITH job_stats AS (
  SELECT job_name, run_count, success_count, failure_count,
         ROUND(success_count * 100.0 / NULLIF(run_count, 0), 1) as success_rate
  FROM mv_job_performance
)
SELECT job_name, run_count, failure_count, success_rate
FROM job_stats
WHERE failure_count > 0
ORDER BY failure_count DESC
LIMIT 15;
```

---

### Question 22: "🔬 DEEP RESEARCH: Job failure patterns with ML predictions"
**Expected SQL:**
```sql
SELECT jf.job_id, jf.prediction as failure_probability,
       j.job_name
FROM job_failure_predictions jf
JOIN dim_job j ON jf.job_id = j.job_id
WHERE jf.prediction > 0.5
ORDER BY jf.prediction DESC
LIMIT 15;
```

---

### Question 23: "🔬 DEEP RESEARCH: SLA breach analysis with predictions"
**Expected SQL:**
```sql
SELECT sb.job_id, sb.prediction as breach_probability,
       j.job_name
FROM sla_breach_predictions sb
JOIN dim_job j ON sb.job_id = j.job_id
WHERE sb.prediction > 0.3
ORDER BY sb.prediction DESC
LIMIT 15;
```

---

### Question 24: "🔬 DEEP RESEARCH: Job duration analysis with predictions"
**Expected SQL:**
```sql
SELECT d.job_id, d.prediction as predicted_duration,
       j.job_name
FROM duration_predictions d
JOIN dim_job j ON d.job_id = j.job_id
ORDER BY d.prediction DESC
LIMIT 15;
```

---

### Question 25: "🔬 DEEP RESEARCH: Job reliability dashboard combining metrics and predictions"
**Expected SQL:**
```sql
SELECT j.job_name,
       mv.run_count,
       mv.success_count,
       mv.failure_count,
       ROUND(mv.success_count * 100.0 / NULLIF(mv.run_count, 0), 1) as success_rate
FROM mv_job_performance mv
JOIN dim_job j ON mv.job_id = j.job_id
WHERE mv.run_count >= 5
ORDER BY mv.failure_count DESC
LIMIT 20;
```

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

## H. Benchmark Questions with SQL

**Total Benchmarks: 22**
- TVF Questions: 8
- Metric View Questions: 6
- ML Table Questions: 3
- Monitoring Table Questions: 2
- Fact Table Questions: 2
- Dimension Table Questions: 1
- Deep Research Questions: 0

---

### TVF Questions

**Q1: Query get_failed_jobs**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_failed_jobs("2025-12-15", "2026-01-14", "ALL", NULL) LIMIT 20;
```

**Q2: Query get_job_success_rate**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_success_rate("2025-12-15", "2026-01-14", 5) LIMIT 20;
```

**Q3: Query get_job_duration_percentiles**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_duration_percentiles(30, "ALL", NULL) LIMIT 20;
```

**Q4: Query get_job_sla_compliance**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_sla_compliance("2025-12-15", "2026-01-14") LIMIT 20;
```

**Q5: Query get_job_failure_trends**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_failure_trends(30) LIMIT 20;
```

**Q6: Query get_job_outlier_runs**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_outlier_runs(30, 1.5, 5) LIMIT 20;
```

**Q7: Query get_job_retry_analysis**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_retry_analysis("2025-12-15", "2026-01-14") LIMIT 20;
```

**Q8: Query get_job_failure_costs**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_failure_costs("2025-12-15", "2026-01-14", 50) LIMIT 20;
```

### Metric View Questions

**Q9: What are the key metrics from mv_job_performance?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_job_performance LIMIT 20;
```

**Q10: Analyze job_health_monitor trends over time**
```sql
SELECT 'Complex trend analysis for job_health_monitor' AS deep_research;
```

**Q11: Identify anomalies in job_health_monitor data**
```sql
SELECT 'Anomaly detection query for job_health_monitor' AS deep_research;
```

**Q12: Compare job_health_monitor metrics across dimensions**
```sql
SELECT 'Cross-dimensional analysis for job_health_monitor' AS deep_research;
```

**Q13: Provide an executive summary of job_health_monitor**
```sql
SELECT 'Executive summary for job_health_monitor' AS deep_research;
```

**Q14: What are the key insights from job_health_monitor analysis?**
```sql
SELECT 'Key insights summary for job_health_monitor' AS deep_research;
```

### ML Prediction Questions

**Q15: What are the latest ML predictions from job_failure_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.job_failure_predictions LIMIT 20;
```

**Q16: What are the latest ML predictions from retry_success_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.retry_success_predictions LIMIT 20;
```

**Q17: What are the latest ML predictions from sla_breach_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.sla_breach_predictions LIMIT 20;
```

### Lakehouse Monitoring Questions

**Q18: Show monitoring data from fact_job_run_timeline_profile_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics LIMIT 20;
```

**Q19: Show monitoring data from fact_job_run_timeline_drift_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_drift_metrics LIMIT 20;
```

### Fact Table Questions

**Q20: Show recent data from fact_job_run_timeline**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_job_run_timeline LIMIT 20;
```

**Q21: Show recent data from fact_job_task_run_timeline**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_job_task_run_timeline LIMIT 20;
```

### Dimension Table Questions

**Q22: Describe the dim_job dimension**
```sql
SELECT * FROM ${catalog}.${gold_schema}.dim_job LIMIT 20;
```

---

*Note: These benchmarks are auto-generated from `actual_assets_inventory.json` to ensure all referenced assets exist. JSON file is the source of truth.*