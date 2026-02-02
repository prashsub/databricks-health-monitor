"""
TRAINING MATERIAL: Cost Domain ML Models Package
================================================

This package contains 5 ML models for the Cost Agent domain,
addressing different aspects of Databricks cost optimization.

COST DOMAIN MODEL INVENTORY:
----------------------------

┌────────────────────────────────────────────────────────────────────────────┐
│  MODEL                    │  TYPE          │  USE CASE                      │
├───────────────────────────┼────────────────┼────────────────────────────────┤
│  cost_anomaly_detector    │  Anomaly (IF)  │  Detect unusual spending spikes│
│  budget_forecaster        │  Regression    │  Predict future costs          │
│  chargeback_attribution   │  Regression    │  Allocate costs to teams       │
│  job_cost_optimizer       │  Classification│  Identify inefficient jobs     │
│  tag_recommender          │  Classification│  Suggest missing tags          │
│  commitment_recommender   │  Classification│  Recommend commit purchases    │
└───────────────────────────┴────────────────┴────────────────────────────────┘

ALGORITHM SELECTION RATIONALE:
------------------------------

1. cost_anomaly_detector → Isolation Forest
   - No labeled "anomaly" data available
   - Need to detect unknown anomaly patterns
   - Unsupervised learns "normal" cost behavior

2. budget_forecaster → Gradient Boosting Regressor
   - Predicting continuous value (future cost)
   - Handles non-linear patterns (seasonal, trending)
   - Feature importance for explainability

3. job_cost_optimizer → XGBoost Classifier
   - Binary classification: optimize/don't optimize
   - Can use job efficiency features
   - Handles class imbalance well

4. tag_recommender → XGBoost Classifier
   - Multi-label classification: recommend tags
   - Based on resource naming patterns
   - Improves cost attribution

FEATURE TABLE: cost_features
----------------------------

Primary Keys: workspace_id, usage_date
Key Features:
- daily_dbu: Total DBU consumption
- daily_cost: Total cost in USD
- serverless_cost: Serverless compute spend
- jobs_on_all_purpose_cost: Optimization opportunity
- dlt_cost: Delta Live Tables spend
- model_serving_cost: ML serving spend

5 Models: Anomaly Detector, Budget Forecaster, Chargeback Optimizer, Job Cost Optimizer, Tag Recommender
"""






