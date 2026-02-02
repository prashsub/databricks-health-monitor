"""
TRAINING MATERIAL: Quality Domain ML Models Package
===================================================

This package contains ML models for the Data Quality Agent domain,
focusing on schema changes, data freshness, and drift detection.

QUALITY DOMAIN MODEL INVENTORY:
-------------------------------

┌────────────────────────────────────────────────────────────────────────────┐
│  MODEL                    │  TYPE          │  USE CASE                      │
├───────────────────────────┼────────────────┼────────────────────────────────┤
│  data_drift_detector      │  Anomaly (IF)  │  Detect data distribution shift│
│  schema_change_predictor  │  Classification│  Predict schema evolution      │
│  freshness_predictor      │  Regression    │  Predict data staleness        │
└───────────────────────────┴────────────────┴────────────────────────────────┘

DATA QUALITY CHALLENGES:
------------------------

1. DATA DRIFT
   - Feature distributions change over time
   - Upstream data source changes
   - Seasonal patterns shift

2. SCHEMA EVOLUTION
   - Columns added/removed
   - Type changes
   - Constraint changes

3. FRESHNESS ISSUES
   - Late-arriving data
   - Pipeline delays
   - Source system outages

FEATURE TABLE: quality_features
-------------------------------

Primary Keys: table_id, snapshot_date
Key Features:
- null_rate_change: Change in NULL percentage
- distinct_count_change: Change in cardinality
- schema_version_count: Number of schema changes
- avg_update_frequency: Historical update cadence
- last_update_lag: Time since last update

ALGORITHM SELECTION:
--------------------

1. data_drift_detector → Isolation Forest (Unsupervised)
   - No labeled "drift" examples
   - Drift patterns are diverse
   - Need to detect unknown distribution shifts

2. schema_change_predictor → XGBoost Classifier
   - Binary: will schema change?
   - Based on historical patterns
   - Table naming, update frequency, etc.

3. freshness_predictor → Gradient Boosting Regressor
   - Predict expected lag in hours
   - Based on historical update patterns
   - Used for SLA monitoring

Quality Agent ML Models
"""






