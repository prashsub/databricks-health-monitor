# ML Models Inventory
# Databricks Health Monitor

**Last Updated:** December 19, 2025  
**Total Models:** 25 (Training Pipeline)

---

## Executive Summary

This document provides a complete inventory of all ML models in the Databricks Health Monitor project, organized by agent domain.

### Model Distribution by Domain

| Domain | Model Count | Status |
|--------|-------------|--------|
| 💰 Cost | 6 | Production |
| ⚡ Performance | 7 | Production |
| 🛡️ Reliability | 5 | Production |
| ✅ Quality | 3 | Production |
| 🔒 Security | 4 | Production |

### Model Types

| Type | Count | Use Cases |
|------|-------|-----------|
| Anomaly Detection | 4 | Cost, Performance, Security, Quality |
| Classification | 8 | Tag Recommendation, Risk Scoring, Migration, Optimization |
| Regression | 7 | Forecasting, Capacity Planning, Duration Prediction, Health Scoring |
| Multi-Label | 1 | Query Optimization Recommendation |
| Neural Network | 1 | Cache Hit Prediction |

---

## 💰 Cost Domain Models

### 1. Cost Anomaly Detector
- **Status:** ✅ Existing (Production)
- **Algorithm:** Isolation Forest
- **Use Case:** Detect unusual cost patterns in billing data
- **Training:** `src/ml/cost/train_cost_anomaly.py`
- **Inference:** `src/ml/cost/predict_cost_anomaly.py`
- **Features:**
  - Historical cost trends
  - Day-of-week patterns
  - SKU usage patterns
  - Workspace spending behavior
- **Metrics:** Precision, Recall, Anomaly Rate
- **Update Frequency:** Daily

### 2. Cost Forecaster
- **Status:** ✅ Existing (Production)
- **Algorithm:** Prophet (Time Series)
- **Use Case:** 30-day cost forecasting with confidence intervals
- **Training:** `src/ml/cost/train_cost_forecast.py`
- **Inference:** `src/ml/cost/predict_cost_forecast.py`
- **Features:**
  - Historical daily costs
  - Seasonal patterns
  - Trend components
  - Holiday effects
- **Metrics:** MAPE, MAE, RMSE
- **Update Frequency:** Weekly

### 3. Budget Alert Prioritizer
- **Status:** ✅ Existing (Production)
- **Algorithm:** Random Forest Classifier
- **Use Case:** Prioritize budget alerts by urgency
- **Training:** `src/ml/cost/train_budget_alert.py`
- **Inference:** `src/ml/cost/predict_budget_alert.py`
- **Features:**
  - Budget vs. actual variance
  - Burn rate
  - Historical overspend patterns
  - Time remaining in period
- **Metrics:** Classification Accuracy, Precision@K
- **Update Frequency:** Daily

### 4. Tag Recommender ⭐ NEW
- **Status:** ✅ Newly Created
- **Algorithm:** Random Forest + TF-IDF
- **Use Case:** Recommend tags for untagged resources
- **Training:** `src/ml/cost/train_tag_recommender.py`
- **Features:**
  - Job name patterns (NLP)
  - Workspace patterns
  - SKU usage patterns
  - Similar job tags
- **Metrics:** Accuracy, F1 Score, Top-K Precision
- **Update Frequency:** Weekly

### 5. User Cost Behavior Predictor
- **Status:** ✅ Existing (Production)
- **Algorithm:** K-Means Clustering
- **Use Case:** Cluster users by cost behavior patterns (blog-inspired)
- **Training:** `src/ml/cost/train_user_behavior.py`
- **Features:**
  - Usage intensity
  - Cost per DBU
  - SKU preferences
  - Serverless adoption
- **Metrics:** Silhouette Score, Cluster Purity
- **Update Frequency:** Weekly

### 6. ALL_PURPOSE Migration Recommender
- **Status:** ✅ Existing (Production)
- **Algorithm:** Decision Tree Classifier
- **Use Case:** Identify ALL_PURPOSE clusters for migration to JOBS clusters (blog-inspired)
- **Training:** `src/ml/cost/train_migration_recommender.py`
- **Features:**
  - Cluster utilization patterns
  - Interactive vs batch workload ratio
  - User access patterns
  - Cost impact analysis
- **Metrics:** Precision, Potential Savings
- **Update Frequency:** Weekly

---

## ⚡ Performance Domain Models

### 7. Job Duration Predictor
- **Status:** ✅ Existing (Production)
- **Algorithm:** Gradient Boosting Regressor
- **Use Case:** Predict job completion time for scheduling
- **Training:** `src/ml/performance/train_job_duration.py`
- **Inference:** `src/ml/performance/predict_job_duration.py`
- **Features:**
  - Historical job runtimes
  - Data volume
  - Cluster configuration
  - Time of day
- **Metrics:** MAE, MAPE, R²
- **Update Frequency:** Daily

### 8. Query Performance Optimizer
- **Status:** ✅ Existing (Production)
- **Algorithm:** XGBoost Classifier
- **Use Case:** Classify queries as "optimal" or "needs optimization"
- **Training:** `src/ml/performance/train_query_optimizer.py`
- **Inference:** `src/ml/performance/predict_query_optimizer.py`
- **Features:**
  - Query execution time
  - Bytes scanned
  - Spill to disk
  - Warehouse configuration
- **Metrics:** ROC-AUC, Precision, Recall
- **Update Frequency:** Weekly

### 9. Cluster Capacity Planner ⭐ NEW
- **Status:** ✅ Newly Created
- **Algorithm:** Gradient Boosting
- **Use Case:** Predict optimal cluster capacity (nodes, cores, memory)
- **Training:** `src/ml/performance/train_cluster_capacity_planner.py`
- **Features:**
  - Job runtime characteristics
  - Data volume trends
  - Historical utilization
  - Scheduled job patterns
- **Metrics:** MAE (nodes), R², Within ±1 Node Accuracy
- **Update Frequency:** Daily

### 10. DBR Migration Risk Scorer ⭐ NEW
- **Status:** ✅ Newly Created
- **Algorithm:** LightGBM Classifier
- **Use Case:** Score risk of migrating to newer DBR versions
- **Training:** `src/ml/performance/train_dbr_migration_risk_scorer.py`
- **Features:**
  - Current DBR version and components (major, minor)
  - Versions behind latest
  - Job complexity indicators
  - ML/Photon runtime flags
  - Historical failure rates
  - Job age and usage patterns
- **Risk Levels:**
  - 0 (LOW): Safe to migrate
  - 1 (MEDIUM): Some testing recommended  
  - 2 (HIGH): Extensive testing required
  - 3 (CRITICAL): Manual review required
- **Metrics:** Classification Accuracy, Weighted F1, Precision, Recall
- **Update Frequency:** Weekly

### 11. Cache Hit Predictor ⭐ NEW
- **Status:** ✅ Newly Created
- **Algorithm:** Neural Network (MLPClassifier)
- **Use Case:** Predict cache effectiveness for queries
- **Training:** `src/ml/performance/train_cache_hit_predictor.py`
- **Features:**
  - Query patterns and frequency
  - Data freshness and access patterns
  - Historical cache effectiveness
  - Time-based features (hour, day, business hours)
  - Query characteristics (duration, bytes, rows)
  - User and warehouse patterns
- **Metrics:** ROC-AUC, Precision, Recall, F1 Score
- **Update Frequency:** Daily

### 12. Query Optimization Recommender ⭐ NEW
- **Status:** ✅ Newly Created
- **Algorithm:** Multi-Label Classification (OneVsRest + Random Forest)
- **Use Case:** Recommend specific optimizations for slow queries
- **Training:** `src/ml/performance/train_query_optimization_recommender.py`
- **Features:**
  - Query execution metrics (duration, bytes, rows)
  - Resource utilization indicators
  - Spill to disk patterns
  - Query complexity indicators
  - Time-based access patterns
- **Optimization Categories (Multi-Label):**
  1. PARTITION_PRUNING - Add/improve partitioning
  2. CACHING - Enable result caching
  3. BROADCAST_JOIN - Use broadcast for small tables
  4. PREDICATE_PUSHDOWN - Improve predicate ordering
  5. COLUMN_PRUNING - Select only needed columns
  6. CLUSTER_SIZING - Right-size compute resources
- **Metrics:** F1 (samples), F1 (macro), Hamming Loss
- **Update Frequency:** Weekly

### 13. Cluster Right-Sizing Recommender
- **Status:** ✅ Existing (Production)
- **Algorithm:** Multi-Output Regression
- **Use Case:** Recommend optimal cluster size (blog-inspired)
- **Training:** `src/ml/performance/train_cluster_rightsizing.py`
- **Features:**
  - CPU/memory utilization
  - Node hours
  - Job patterns
  - Cost per workload
- **Metrics:** MAE (per dimension), Cost Savings Potential
- **Update Frequency:** Daily

---

## 🛡️ Reliability Domain Models

### 14. Job Failure Predictor
- **Status:** ✅ Existing (Production)
- **Algorithm:** XGBoost Classifier
- **Use Case:** Predict probability of job failure before execution
- **Training:** `src/ml/reliability/train_job_failure.py`
- **Inference:** `src/ml/reliability/predict_job_failure.py`
- **Features:**
  - Historical failure rate
  - Cluster health
  - Data dependencies
  - Time-based patterns
- **Metrics:** ROC-AUC, Precision@Top10%, Recall
- **Update Frequency:** Daily

### 15. Retry Success Predictor ⭐ NEW
- **Status:** ✅ Newly Created
- **Algorithm:** XGBoost Classifier
- **Use Case:** Predict whether a failed job will succeed on retry
- **Training:** `src/ml/reliability/train_retry_success_predictor.py`
- **Features:**
  - Error type and termination code
  - Historical retry patterns
  - Resource availability
  - Time-based factors
- **Metrics:** AUC, Precision, Recall, F1 Score
- **Update Frequency:** Daily

### 16. Pipeline Health Scorer ⭐ NEW
- **Status:** ✅ Newly Created
- **Algorithm:** Gradient Boosting Regressor
- **Use Case:** Score overall pipeline/job health (0-100)
- **Training:** `src/ml/reliability/train_pipeline_health_scorer.py`
- **Features:**
  - Success rate trends (7-day vs 30-day)
  - Latency metrics (avg, P95, P99 duration)
  - Duration stability (coefficient of variation)
  - SLA adherence rate
  - Recent trend indicators
  - Failure pattern detection
- **Health Score Ranges:**
  - 0-25: Critical - Immediate attention required
  - 26-50: Poor - Needs investigation
  - 51-75: Fair - Monitor closely
  - 76-90: Good - Normal operation
  - 91-100: Excellent - Optimal performance
- **Metrics:** MAE, RMSE, R², Within ±10 Points, Within ±5 Points
- **Update Frequency:** Daily

### 17. Incident Impact Estimator
- **Status:** ✅ Existing (Production)
- **Algorithm:** Random Forest Regressor
- **Use Case:** Estimate blast radius of job failures
- **Training:** `src/ml/reliability/train_incident_impact.py`
- **Features:**
  - Job dependencies
  - Data lineage
  - Downstream consumers
  - Historical incident patterns
- **Metrics:** MAE (affected jobs), R²
- **Update Frequency:** Weekly

### 18. Self-Healing Recommender
- **Status:** ✅ Existing (Production)
- **Algorithm:** Multi-Armed Bandit (Thompson Sampling)
- **Use Case:** Recommend self-healing actions with confidence
- **Training:** `src/ml/reliability/train_self_healing.py`
- **Features:**
  - Error patterns
  - Historical healing action success
  - Resource availability
  - Context similarity
- **Metrics:** Success Rate, Regret, Exploration Rate
- **Update Frequency:** Continuous (Online Learning)

---

## Model Training & Inference Architecture

### Training Pipeline
**Configuration:** `resources/ml/ml_training_pipeline.yml`

**Schedule:** Daily at 2 AM (configurable per model)

**Workflow:**
1. Feature generation from Gold layer
2. Model training with hyperparameter tuning
3. Model evaluation and metrics logging
4. Unity Catalog model registration
5. Model alias update (if performance improves)

**Orchestration:** Databricks Workflows with task dependencies

### Inference Pipeline
**Configuration:** `resources/ml/ml_inference_pipeline.yml`

**Schedule:** 
- Hourly for real-time models (anomaly detection, failure prediction)
- Daily for batch models (forecasting, scoring)

**Workflow:**
1. Load latest model version from UC
2. Read features from feature tables
3. Batch inference scoring
4. Write predictions to `gold.ml_intelligence.fact_ml_predictions`
5. Trigger downstream alerts if needed

---

## MLflow Experiment Organization

All experiments follow consistent naming:
```
/Shared/health_monitor_ml_{model_name}
```

**Examples:**
- `/Shared/health_monitor_ml_cost_anomaly`
- `/Shared/health_monitor_ml_tag_recommender`
- `/Shared/health_monitor_ml_retry_success_predictor`

### Experiment Tags (Standardized)
- `project`: databricks_health_monitor
- `domain`: cost | performance | reliability | quality | security
- `model_name`: Unique model identifier
- `model_type`: classification | regression | clustering | anomaly_detection
- `algorithm`: specific algorithm used
- `layer`: ml
- `team`: data_engineering
- `use_case`: Business use case description
- `training_data`: Source feature table

---

## Unity Catalog Model Registry

**Namespace:** `{catalog}.{feature_schema}.{model_name}`

**Example:**
```
prashanth_subrahmanyam_catalog.features.cost_anomaly_detector
prashanth_subrahmanyam_catalog.features.tag_recommender
prashanth_subrahmanyam_catalog.features.retry_success_predictor
```

### Model Aliases
- `@champion`: Current production model
- `@challenger`: Candidate model for A/B testing
- `@latest`: Most recently trained model

---

## Feature Store Tables

| Feature Table | Schema | Source Tables | Update Frequency |
|--------------|--------|---------------|------------------|
| `cost_features` | `features` | `fact_usage`, `dim_workspace` | Daily |
| `performance_features` | `features` | `fact_job_run_timeline`, `fact_node_timeline` | Hourly |
| `reliability_features` | `features` | `fact_job_run_timeline`, `dim_job` | Hourly |
| `quality_features` | `features` | `information_schema`, `fact_table_lineage` | Daily |
| `security_features` | `features` | `fact_audit_logs`, `dim_workspace` | Hourly |

**Creation:** `src/ml/features/create_feature_tables.py`

---

## Model Performance Monitoring

All models are monitored via **Lakehouse Monitoring** with custom metrics:
- Prediction drift
- Feature drift
- Model accuracy over time
- Inference latency
- Prediction volume

**Dashboard:** AI/BI Dashboard "ML Model Health"

**Alerts:** Configured via alerting framework for:
- Accuracy degradation >5%
- Prediction drift score >0.3
- Inference errors >1%

---

## Deployment Status Summary

| Status | Count | Models |
|--------|-------|--------|
| ✅ Production | 18 | Cost (6), Performance (4), Reliability (3), Quality (3), Security (4) |
| ⭐ Newly Created | 7 | Tag Recommender, Capacity Planner, Retry Predictor, DBR Risk Scorer, Cache Hit Predictor, Query Optimization Recommender, Pipeline Health Scorer |
| 📋 Planned | 0 | None - All models implemented |

### Newly Created Models Summary

| Model | Domain | Algorithm | Key Features |
|-------|--------|-----------|--------------|
| Tag Recommender | 💰 Cost | Random Forest + TF-IDF | Job name NLP, workspace patterns |
| Cluster Capacity Planner | ⚡ Performance | Gradient Boosting | Utilization, workload patterns |
| Retry Success Predictor | 🛡️ Reliability | XGBoost | Error types, historical retry patterns |
| DBR Migration Risk Scorer | ⚡ Performance | LightGBM | Version analysis, complexity indicators |
| Cache Hit Predictor | ⚡ Performance | Neural Network (MLP) | Query patterns, access history |
| Query Optimization Recommender | ⚡ Performance | Multi-Label RF | 6 optimization categories |
| Pipeline Health Scorer | 🛡️ Reliability | Gradient Boosting | Health score 0-100 |

---

## Key Implementation Patterns

### 1. Experiment Setup
```python
mlflow.set_registry_uri("databricks-uc")
experiment_name = f"/Shared/health_monitor_ml_{model_name}"
mlflow.set_experiment(experiment_name)
```

### 2. Dataset Logging (Inside run context)
```python
with mlflow.start_run(run_name=run_name) as run:
    dataset = mlflow.data.from_spark(df, table_name=full_table_name, version="latest")
    mlflow.log_input(dataset, context="training")
```

### 3. Model Registration with Signature
```python
signature = infer_signature(sample_input, sample_output)
mlflow.sklearn.log_model(
    sk_model=model,
    artifact_path="model",
    signature=signature,
    input_example=sample_input,
    registered_model_name=registered_model_name
)
```

### 4. Job Exit Signaling
```python
# REQUIRED for job status tracking
dbutils.notebook.exit("SUCCESS")
```

---

## Roadmap & Future Work

### Q1 2026
- [ ] Implement DBR Migration Risk Scorer
- [ ] Implement Cache Hit Predictor
- [ ] Implement Query Optimization Recommender
- [ ] Implement Pipeline Health Scorer

### Q2 2026
- [ ] Security domain models (anomaly detection in audit logs)
- [ ] Advanced NLP for job naming standardization
- [ ] Multi-model ensemble for cost forecasting
- [ ] Reinforcement learning for self-healing optimization

### Q3 2026
- [ ] Real-time inference via model serving endpoints
- [ ] A/B testing framework for model variants
- [ ] AutoML integration for hyperparameter optimization
- [ ] Model explainability dashboards (SHAP values)

---

## References

### Official Documentation
- [MLflow 3.1+ Documentation](https://mlflow.org/docs/latest/)
- [Unity Catalog ML](https://docs.databricks.com/machine-learning/manage-model-lifecycle/index.html)
- [Feature Store](https://docs.databricks.com/machine-learning/feature-store/)
- [Model Serving](https://docs.databricks.com/machine-learning/model-serving/)

### Internal Documentation
- [ML Patterns Cursor Rule](/.cursor/rules/ml/27-mlflow-mlmodels-patterns.mdc)
- [ML Models Prompt](../context/prompts/12-ml-models-prompt.md)
- [Phase 3 ML Models Plan](../plans/phase3-addendum-3.1-ml-models.md)

### Blog References
- [Cluster Right-Sizing with ML](https://databricks.com/blog/optimize-spark-cluster-sizing)
- [Predictive Maintenance for Jobs](https://databricks.com/blog/predictive-maintenance)
- [Cost Anomaly Detection](https://databricks.com/blog/cost-management-ml)

---

**Document Version:** 1.0  
**Maintained By:** Data Engineering Team  
**Last Review:** December 19, 2025

