"""
TRAINING MATERIAL: Performance Domain ML Models Package
======================================================

This package contains 6 ML models for the Performance Agent domain,
addressing query optimization, capacity planning, and performance tuning.

PERFORMANCE DOMAIN MODEL INVENTORY:
-----------------------------------

┌────────────────────────────────────────────────────────────────────────────┐
│  MODEL                       │  TYPE          │  USE CASE                   │
├──────────────────────────────┼────────────────┼─────────────────────────────┤
│  query_forecaster            │  Regression    │  Predict query duration     │
│  warehouse_optimizer         │  Classification│  Warehouse sizing advice    │
│  query_optimization_recommender│ Classification│  Optimize this query?       │
│  cluster_capacity_planner    │  Regression    │  Cluster size prediction    │
│  dbr_migration_risk_scorer   │  Regression    │  DBR upgrade risk score     │
│  cache_hit_predictor         │  Classification│  Will query hit cache?      │
│  regression_detector         │  Anomaly (IF)  │  Performance regression     │
└──────────────────────────────┴────────────────┴─────────────────────────────┘

PERFORMANCE OPTIMIZATION WORKFLOW:
----------------------------------

    Query Submitted
         │
         ▼
    ┌─────────────────────────────┐
    │ cache_hit_predictor         │──▶ Likely cache hit? → Skip optimization
    └─────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────┐
    │ query_forecaster            │──▶ Expected duration > SLA? → Optimize
    └─────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────┐
    │ query_optimization_recommender │──▶ Suggest indexing, partitioning
    └─────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────┐
    │ warehouse_optimizer         │──▶ Right-size warehouse for workload
    └─────────────────────────────┘

FEATURE TABLE: performance_features
-----------------------------------

Primary Keys: workspace_id, warehouse_id, query_date
Key Features:
- avg_query_duration: Average query time
- p95_query_duration: 95th percentile
- cache_hit_rate: Cache effectiveness
- concurrent_query_count: Workload intensity
- data_scanned_tb: Data volume processed

DBR MIGRATION RISK:
-------------------

Special model that predicts risk of upgrading Databricks Runtime:

- Uses historical cluster performance data
- Compares behavior across DBR versions
- Outputs risk score 0-100
- High risk → Recommend testing in dev first

6 Models: Query Forecaster, Warehouse Optimizer, Query Recommender, Cluster Capacity Planner, DBR Migration Risk, Cache Hit Predictor
"""






