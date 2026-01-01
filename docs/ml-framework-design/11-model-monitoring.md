# 11 - Model Monitoring

## Overview

Model monitoring ensures ML models continue to perform well in production. This document covers strategies for detecting model degradation, data drift, and triggering retraining.

## Monitoring Dimensions

### What to Monitor

| Dimension | What It Measures | Signals |
|---|---|---|
| **Prediction Quality** | Model accuracy over time | Drift in metrics |
| **Data Drift** | Feature distribution changes | KL divergence, PSI |
| **Concept Drift** | Target distribution changes | Label shift |
| **Operational Health** | Pipeline reliability | Latency, errors |
| **Business Impact** | Real-world outcomes | Alert quality, user feedback |

## Prediction Quality Monitoring

### Tracking Prediction Distributions

```python
from pyspark.sql import functions as F

def analyze_prediction_distribution(spark, prediction_table: str, days: int = 7):
    """Analyze prediction distribution over time."""
    
    df = spark.table(prediction_table).filter(
        f"scored_at >= current_date() - INTERVAL {days} DAYS"
    )
    
    stats = df.groupBy(F.date_trunc("day", "scored_at").alias("date")).agg(
        F.count("*").alias("count"),
        F.avg("prediction").alias("avg_prediction"),
        F.stddev("prediction").alias("std_prediction"),
        F.min("prediction").alias("min_prediction"),
        F.max("prediction").alias("max_prediction"),
        F.percentile_approx("prediction", 0.5).alias("median_prediction")
    ).orderBy("date")
    
    return stats

# Example usage
stats = analyze_prediction_distribution(spark, "cost_anomaly_predictions")
stats.display()
```

### Anomaly Detection Rate Monitoring

```sql
-- Track anomaly rate over time (should be 2-10%)
SELECT 
    DATE(scored_at) as date,
    COUNT(*) as total,
    SUM(is_anomaly) as anomalies,
    ROUND(100.0 * SUM(is_anomaly) / COUNT(*), 2) as anomaly_pct
FROM ${catalog}.${schema}.cost_anomaly_predictions
WHERE scored_at >= current_date() - INTERVAL 30 DAYS
GROUP BY DATE(scored_at)
ORDER BY date DESC;
```

### Alert on Anomaly Rate Drift

```sql
-- Alert if anomaly rate outside 2-15% range
WITH daily_rates AS (
    SELECT 
        DATE(scored_at) as date,
        100.0 * SUM(is_anomaly) / COUNT(*) as anomaly_pct
    FROM ${catalog}.${schema}.cost_anomaly_predictions
    WHERE scored_at >= current_date() - INTERVAL 7 DAYS
    GROUP BY DATE(scored_at)
)
SELECT 
    date,
    anomaly_pct,
    CASE 
        WHEN anomaly_pct < 2 THEN 'TOO_LOW'
        WHEN anomaly_pct > 15 THEN 'TOO_HIGH'
        ELSE 'NORMAL'
    END as status
FROM daily_rates
WHERE anomaly_pct < 2 OR anomaly_pct > 15;
```

## Data Drift Detection

### Feature Distribution Tracking

```python
def track_feature_drift(
    spark,
    feature_table: str,
    feature_columns: list,
    reference_date: str,
    current_date: str
):
    """Compare feature distributions between reference and current periods."""
    
    df = spark.table(feature_table)
    
    # Reference period stats
    ref_stats = df.filter(f"usage_date = '{reference_date}'").select(
        *[F.avg(c).alias(f"ref_avg_{c}") for c in feature_columns] +
        *[F.stddev(c).alias(f"ref_std_{c}") for c in feature_columns]
    ).collect()[0]
    
    # Current period stats
    curr_stats = df.filter(f"usage_date = '{current_date}'").select(
        *[F.avg(c).alias(f"curr_avg_{c}") for c in feature_columns] +
        *[F.stddev(c).alias(f"curr_std_{c}") for c in feature_columns]
    ).collect()[0]
    
    # Calculate drift for each feature
    drift_report = []
    for col in feature_columns:
        ref_avg = ref_stats[f"ref_avg_{col}"]
        curr_avg = curr_stats[f"curr_avg_{col}"]
        ref_std = ref_stats[f"ref_std_{col}"] or 1
        
        # Z-score of current mean vs reference
        drift = abs(curr_avg - ref_avg) / ref_std if ref_std else 0
        
        drift_report.append({
            "feature": col,
            "ref_mean": ref_avg,
            "curr_mean": curr_avg,
            "drift_score": drift,
            "status": "DRIFT" if drift > 2 else "OK"
        })
    
    return drift_report

# Usage
drift = track_feature_drift(
    spark, "cost_features",
    ["daily_dbu", "daily_cost", "avg_dbu_7d"],
    "2025-12-01", "2026-01-01"
)
print(drift)
```

### Using Lakehouse Monitoring

```python
from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# Create monitor on predictions table
monitor = client.lakehouse_monitors.create(
    table_name=f"{catalog}.{schema}.cost_anomaly_predictions",
    profile_type="INFERENCE_LOG",
    time_series_column="scored_at",
    granularities=["1 day"],
    prediction_column="prediction",
    custom_metrics=[
        {
            "name": "anomaly_rate",
            "definition": "SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) / COUNT(*)",
            "type": "aggregate"
        }
    ]
)
```

## Concept Drift Detection

### Label Distribution Monitoring

```python
def check_label_drift(spark, training_labels, production_labels):
    """Compare label distributions between training and production."""
    import numpy as np
    from scipy import stats
    
    # KS test for distribution difference
    ks_stat, p_value = stats.ks_2samp(training_labels, production_labels)
    
    return {
        "ks_statistic": ks_stat,
        "p_value": p_value,
        "drift_detected": p_value < 0.05
    }
```

### Feedback Loop Integration

```sql
-- Track prediction accuracy when actual outcomes are known
SELECT 
    DATE(scored_at) as date,
    COUNT(*) as predictions,
    SUM(CASE WHEN predicted_failure = actual_failure THEN 1 ELSE 0 END) as correct,
    ROUND(100.0 * SUM(CASE WHEN predicted_failure = actual_failure THEN 1 ELSE 0 END) / COUNT(*), 2) as accuracy
FROM (
    SELECT 
        p.scored_at,
        p.will_fail as predicted_failure,
        CASE WHEN j.result_state = 'FAILED' THEN 1 ELSE 0 END as actual_failure
    FROM ${catalog}.${schema}.failure_predictions p
    JOIN ${catalog}.${gold_schema}.fact_job_run_timeline j
        ON p.job_id = j.job_id 
        AND DATE(p.scored_at) = DATE(j.start_time) - INTERVAL 1 DAY
)
WHERE scored_at >= current_date() - INTERVAL 30 DAYS
GROUP BY DATE(scored_at)
ORDER BY date DESC;
```

## Operational Health Monitoring

### Pipeline Success Tracking

```sql
-- Track ML pipeline job success
SELECT 
    job_name,
    DATE(run_start_time) as date,
    COUNT(*) as runs,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE job_name LIKE '%ML%'
  AND run_start_time >= current_date() - INTERVAL 7 DAYS
GROUP BY job_name, DATE(run_start_time)
ORDER BY date DESC;
```

### Inference Latency Tracking

```python
def track_inference_latency(spark, prediction_table: str, days: int = 7):
    """Track inference job duration over time."""
    
    return spark.sql(f"""
        SELECT 
            DATE(scored_at) as date,
            COUNT(*) as records,
            MAX(scored_at) - MIN(scored_at) as inference_duration
        FROM {prediction_table}
        WHERE scored_at >= current_date() - INTERVAL {days} DAYS
        GROUP BY DATE(scored_at)
        ORDER BY date DESC
    """)
```

## Retraining Triggers

### Automatic Retraining Criteria

| Trigger | Threshold | Action |
|---|---|---|
| Prediction drift | > 2σ from baseline | Alert + schedule retrain |
| Feature drift | > 3 features drifted | Investigate + retrain |
| Concept drift | KS p-value < 0.05 | Mandatory retrain |
| Age-based | > 30 days since training | Scheduled retrain |
| Performance drop | Accuracy < baseline - 5% | Mandatory retrain |

### Retraining Decision Logic

```python
def should_retrain(
    prediction_drift_score: float,
    feature_drift_count: int,
    days_since_training: int,
    accuracy_drop: float
) -> dict:
    """Determine if model should be retrained."""
    
    reasons = []
    
    if prediction_drift_score > 2.0:
        reasons.append(f"Prediction drift score {prediction_drift_score:.2f} > 2.0")
    
    if feature_drift_count >= 3:
        reasons.append(f"{feature_drift_count} features show significant drift")
    
    if days_since_training > 30:
        reasons.append(f"Model is {days_since_training} days old (> 30)")
    
    if accuracy_drop > 0.05:
        reasons.append(f"Accuracy dropped by {accuracy_drop:.1%} (> 5%)")
    
    return {
        "should_retrain": len(reasons) > 0,
        "reasons": reasons,
        "urgency": "HIGH" if accuracy_drop > 0.05 else "NORMAL"
    }

# Example usage
decision = should_retrain(
    prediction_drift_score=2.5,
    feature_drift_count=2,
    days_since_training=45,
    accuracy_drop=0.03
)
print(decision)
# {'should_retrain': True, 'reasons': ['Prediction drift score 2.50 > 2.0', 'Model is 45 days old (> 30)'], 'urgency': 'NORMAL'}
```

## MLflow Model Performance Tracking

### Version Comparison

```python
from mlflow import MlflowClient

def compare_model_versions(model_name: str, last_n: int = 5) -> pd.DataFrame:
    """Compare metrics across recent model versions."""
    
    client = MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")
    versions = sorted(versions, key=lambda v: int(v.version), reverse=True)[:last_n]
    
    comparisons = []
    for v in versions:
        run = client.get_run(v.run_id)
        metrics = run.data.metrics
        
        comparisons.append({
            "version": v.version,
            "created": v.creation_timestamp,
            **metrics
        })
    
    return pd.DataFrame(comparisons)

# Usage
comparison = compare_model_versions("catalog.schema.cost_anomaly_detector")
print(comparison[["version", "test_r2", "rmse", "anomaly_rate"]])
```

## Alerting Setup

### SQL Alert for Anomaly Rate Drift

```sql
-- Create SQL Alert
WITH today_rate AS (
    SELECT 100.0 * SUM(is_anomaly) / COUNT(*) as anomaly_rate
    FROM ${catalog}.${schema}.cost_anomaly_predictions
    WHERE scored_at >= current_date()
),
baseline_rate AS (
    SELECT 100.0 * SUM(is_anomaly) / COUNT(*) as anomaly_rate
    FROM ${catalog}.${schema}.cost_anomaly_predictions
    WHERE scored_at BETWEEN current_date() - INTERVAL 30 DAYS AND current_date() - INTERVAL 1 DAY
)
SELECT 
    t.anomaly_rate as today_rate,
    b.anomaly_rate as baseline_rate,
    ABS(t.anomaly_rate - b.anomaly_rate) as drift
FROM today_rate t, baseline_rate b
WHERE ABS(t.anomaly_rate - b.anomaly_rate) > 5;  -- Alert if drift > 5%
```

### Python Alert Integration

```python
def send_model_drift_alert(
    model_name: str,
    drift_type: str,
    drift_score: float,
    threshold: float
):
    """Send alert when drift detected."""
    
    message = f"""
    🚨 Model Drift Alert
    
    Model: {model_name}
    Drift Type: {drift_type}
    Score: {drift_score:.2f}
    Threshold: {threshold:.2f}
    
    Action Required: Review model performance and consider retraining.
    """
    
    # Integration with alerting system (e.g., Slack, PagerDuty)
    print(message)
    
    # Log to MLflow
    import mlflow
    with mlflow.start_run(run_name=f"drift_alert_{model_name}"):
        mlflow.log_metrics({
            f"{drift_type}_drift_score": drift_score,
            f"{drift_type}_threshold": threshold
        })
        mlflow.set_tags({
            "alert_type": "drift",
            "model_name": model_name
        })
```

## Monitoring Dashboard Queries

### Model Health Summary

```sql
SELECT 
    model_name,
    MAX(scored_at) as last_prediction,
    DATEDIFF(current_date(), MAX(DATE(scored_at))) as days_since_prediction,
    COUNT(DISTINCT DATE(scored_at)) as active_days_last_week
FROM (
    SELECT 'cost_anomaly_detector' as model_name, scored_at FROM cost_anomaly_predictions
    UNION ALL
    SELECT 'budget_forecaster', scored_at FROM budget_forecast_predictions
    UNION ALL
    SELECT 'failure_predictor', scored_at FROM failure_predictions
    -- ... other models
)
WHERE scored_at >= current_date() - INTERVAL 7 DAYS
GROUP BY model_name;
```

### Prediction Volume Trends

```sql
SELECT 
    DATE(scored_at) as date,
    model_name,
    COUNT(*) as predictions
FROM (
    SELECT 'cost_anomaly_detector' as model_name, scored_at FROM cost_anomaly_predictions
    UNION ALL
    SELECT 'budget_forecaster', scored_at FROM budget_forecast_predictions
    -- ... other models
)
WHERE scored_at >= current_date() - INTERVAL 14 DAYS
GROUP BY DATE(scored_at), model_name
ORDER BY date DESC, model_name;
```

## Monitoring Checklist

### Daily Checks
- [ ] All models generated predictions
- [ ] No significant anomaly rate drift
- [ ] No failed inference jobs
- [ ] Prediction volumes within expected range

### Weekly Checks
- [ ] Feature drift analysis
- [ ] Model performance comparison vs baseline
- [ ] Training data freshness
- [ ] Alert review and tuning

### Monthly Checks
- [ ] Full model performance audit
- [ ] Retraining decision review
- [ ] Monitoring threshold tuning
- [ ] Documentation updates

## Next Steps

- **[12-MLflow UI Guide](12-mlflow-ui-guide.md)**: Navigate experiments
- **[09-Deployment](09-deployment.md)**: Pipeline orchestration
- **[10-Troubleshooting](10-troubleshooting.md)**: Common issues

