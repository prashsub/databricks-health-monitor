# Reliability Dashboard Specification

## Overview

**Purpose:** Job reliability, failure analysis, SLA tracking, and pipeline health monitoring.

**Existing Dashboards to Consolidate:**
- `job_reliability.lvdash.json` (31 datasets)

**Target Dataset Count:** ~70 datasets (within 100 limit after enrichment)

---

## Page Structure

### Page 1: Reliability Overview (Overview Page for Unified)
**Purpose:** Executive summary of reliability health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Success Rate | KPI | ds_kpi_success | Monitor: success_rate |
| Failed Jobs (24h) | KPI | ds_kpi_failed | Monitor: failure_count |
| Avg Duration | KPI | ds_kpi_duration | Monitor: avg_duration_minutes |
| Total Runs (24h) | KPI | ds_kpi_runs | Monitor: total_runs |
| Success Rate Trend | Line | ds_success_trend | - |
| High Risk Jobs | Table | ds_ml_high_risk | ML: job_failure_predictor |

### Page 2: Job Health
**Purpose:** Overall job health metrics

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Success Rate Trend | Line | ds_success_rate_trend | Monitor: success_rate |
| Failure Rate Trend | Line | ds_failure_trend | Monitor: failure_rate |
| Jobs by Result State | Pie | ds_jobs_by_state | - |
| Duration Distribution | Histogram | ds_duration_dist | - |
| P95 Duration Trend | Line | ds_p95_trend | Monitor: p95_duration_minutes |
| Duration Variability | KPI | ds_duration_cv | Monitor: duration_cv |

### Page 3: Failure Analysis
**Purpose:** Deep dive into failures

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Failed Jobs Table | Table | ds_failed_jobs | - |
| Failures by Termination | Pie | ds_failures_term | - |
| Failure Trend | Line | ds_failure_count_trend | Monitor: failure_count |
| Timeout Count | KPI | ds_timeout | Monitor: timeout_count |
| Long Running Jobs | KPI | ds_long_running | Monitor: long_running_count |
| Failure Root Causes | Table | ds_ml_root_cause | ML: failure_root_cause_analyzer |

### Page 4: SLA Tracking
**Purpose:** SLA compliance and breach analysis

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| SLA Breach Count | KPI | ds_sla_breach | - |
| SLA Breach Rate | Gauge | ds_sla_breach_rate | - |
| SLA Breach Predictions | Table | ds_ml_sla_breach | ML: sla_breach_predictor |
| Jobs at Risk | Table | ds_jobs_at_risk | ML: sla_breach_predictor |
| SLA Trend | Line | ds_sla_trend | - |
| Recovery Time (MTTR) | KPI | ds_mttr | ML: recovery_time_predictor |

### Page 5: Pipeline Health
**Purpose:** Pipeline-level health metrics

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Pipeline Health Score | KPI | ds_pipeline_health | ML: pipeline_health_scorer |
| Healthy Pipelines % | Gauge | ds_healthy_pct | ML: pipeline_health_classifier |
| Pipeline Health Table | Table | ds_ml_pipeline_health | ML: pipeline_health_scorer |
| Dependency Impact | Table | ds_ml_dependency | ML: dependency_impact_predictor |
| Pipeline Trend | Line | ds_pipeline_trend | - |
| Critical Pipelines | Table | ds_critical_pipelines | - |

### Page 6: Retry & Recovery
**Purpose:** Retry analysis and recovery recommendations

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Retry Success Rate | KPI | ds_retry_success | - |
| Jobs Needing Retry | Table | ds_retry_needed | - |
| Retry Success Predictions | Table | ds_ml_retry | ML: retry_success_predictor |
| Recovery Time Predictions | Table | ds_ml_recovery | ML: recovery_time_predictor |
| Retry Trend | Line | ds_retry_trend | - |
| Auto-Recovery Candidates | Table | ds_auto_recovery | - |

### Page 7: Failure Predictions
**Purpose:** ML-based failure predictions

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| High Risk Jobs | KPI | ds_high_risk_count | ML: job_failure_predictor |
| Failure Predictions | Table | ds_ml_failure_pred | ML: job_failure_predictor |
| Duration Forecasts | Table | ds_ml_duration | ML: job_duration_forecaster |
| Impact Analysis | Table | ds_ml_impact | ML: dependency_impact_predictor |
| Risk Trend | Line | ds_risk_trend | - |

### Page 8: Reliability Drift
**Purpose:** Monitor-based reliability drift

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Success Rate Drift | KPI | ds_success_drift | Monitor: success_rate_drift |
| Duration Drift % | KPI | ds_duration_drift | Monitor: duration_drift_pct |
| Reliability Profile | Table | ds_reliability_profile | Monitor: profile metrics |
| Drift Trend | Line | ds_reliability_drift_trend | Monitor: drift metrics |
| Monitor Alerts | Table | ds_reliability_alerts | - |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_success
SELECT 
    CONCAT(ROUND(SUM(CASE WHEN termination_code = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / 
    NULLIF(COUNT(*), 0), 1), '%') AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND termination_code IS NOT NULL

-- ds_failed_jobs
SELECT 
    f.job_id,
    j.name AS job_name,
    f.run_id,
    f.run_date,
    f.termination_code,
    f.run_duration_minutes
FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
JOIN ${catalog}.${gold_schema}.dim_job j ON f.job_id = j.job_id
WHERE f.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND f.termination_code IS NOT NULL
  AND f.termination_code != 'SUCCESS'
ORDER BY f.run_date DESC
LIMIT 50
```

### ML Datasets

```sql
-- ds_ml_failure_pred
SELECT 
    job_id,
    job_name,
    failure_probability,
    risk_factors,
    recommended_actions,
    prediction_date
FROM ${catalog}.${gold_schema}.job_failure_predictions
WHERE prediction_date = CURRENT_DATE()
  AND failure_probability > 0.5
ORDER BY failure_probability DESC
LIMIT 20

-- ds_ml_sla_breach
SELECT 
    job_id,
    job_name,
    sla_threshold_minutes,
    predicted_duration_minutes,
    breach_probability,
    risk_factors
FROM ${catalog}.${gold_schema}.sla_breach_predictions
WHERE prediction_date = CURRENT_DATE()
  AND breach_probability > 0.5
ORDER BY breach_probability DESC
LIMIT 20

-- ds_ml_pipeline_health
SELECT 
    pipeline_name,
    health_score,
    health_status,
    failing_stages,
    bottleneck_stages,
    recommendations
FROM ${catalog}.${gold_schema}.pipeline_health_scores
WHERE score_date = CURRENT_DATE()
ORDER BY health_score ASC
LIMIT 20

-- ds_ml_retry
SELECT 
    job_id,
    job_name,
    retry_success_probability,
    recommended_wait_minutes,
    historical_retry_success_rate
FROM ${catalog}.${gold_schema}.retry_success_predictions
WHERE prediction_date = CURRENT_DATE()
ORDER BY retry_success_probability DESC

-- ds_ml_recovery
SELECT 
    job_id,
    job_name,
    predicted_recovery_time_minutes,
    recovery_steps,
    confidence
FROM ${catalog}.${gold_schema}.recovery_time_predictions
WHERE prediction_date = CURRENT_DATE()
ORDER BY predicted_recovery_time_minutes ASC

-- ds_ml_root_cause
SELECT 
    job_id,
    job_name,
    failure_time,
    root_cause_category,
    root_cause_detail,
    confidence,
    recommended_fix
FROM ${catalog}.${gold_schema}.failure_root_causes
WHERE failure_time >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY failure_time DESC
LIMIT 20

-- ds_ml_dependency
SELECT 
    job_id,
    job_name,
    dependent_jobs_count,
    impact_score,
    downstream_impact_minutes,
    affected_pipelines
FROM ${catalog}.${gold_schema}.dependency_impact_scores
WHERE score_date = CURRENT_DATE()
ORDER BY impact_score DESC
LIMIT 20
```

### Monitor Datasets

```sql
-- ds_reliability_profile
SELECT 
    window.start AS period_start,
    total_runs,
    success_rate * 100 AS success_rate_pct,
    failure_rate * 100 AS failure_rate_pct,
    avg_duration_minutes,
    p50_duration_minutes,
    p95_duration_minutes,
    p99_duration_minutes,
    long_running_count,
    timeout_count,
    duration_cv
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_reliability_drift
SELECT 
    window.start AS period_start,
    success_rate_drift * 100 AS success_rate_drift_pct,
    duration_drift_pct * 100 AS duration_drift_pct
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 30
```

---

## ML Model Integration Summary (5 Models)

> **Source of Truth:** [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| job_failure_predictor | Failure predictions, risk alerts | job_failure_predictions |
| job_duration_forecaster | Duration predictions | job_duration_forecasts |
| sla_breach_predictor | SLA risk predictions | sla_breach_predictions |
| pipeline_health_scorer | Pipeline health metrics | pipeline_health_scores |
| retry_success_predictor | Retry recommendations | retry_success_predictions |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_job_run_timeline_profile_metrics | total_runs, success_count, failure_count, success_rate, failure_rate, avg_duration_minutes, p50_duration_minutes, p95_duration_minutes, p99_duration_minutes, long_running_count, timeout_count, duration_cv, long_running_rate |
| fact_job_run_timeline_drift_metrics | success_rate_drift, duration_drift_pct |

