"""
TRAINING MATERIAL: ML Models Package Architecture
==================================================

This package implements 25 ML models for predictive analytics using MLflow 3.0
best practices. The models are organized by agent domain and support the
Health Monitor's AI-driven insights.

MODEL INVENTORY BY DOMAIN:
--------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                        25 ML MODELS BY DOMAIN                            │
│                                                                         │
│  COST AGENT (6 models):                                                 │
│  ──────────────────────                                                 │
│  • cost_anomaly_detector     - Isolation Forest for spending spikes     │
│  • budget_forecaster         - Time series for budget prediction        │
│  • job_cost_optimizer        - Recommendations for cost reduction       │
│  • chargeback_attribution    - Team cost attribution                    │
│  • commitment_recommender    - Reserved capacity suggestions            │
│  • tag_recommender           - Auto-tagging for cost allocation         │
│                                                                         │
│  SECURITY AGENT (4 models):                                             │
│  ─────────────────────────                                              │
│  • security_threat_detector  - Anomaly detection for security threats   │
│  • exfiltration_detector     - Data exfiltration pattern detection      │
│  • privilege_escalation      - Unusual permission changes               │
│  • user_behavior_baseline    - Normal behavior modeling                 │
│                                                                         │
│  PERFORMANCE AGENT (7 models):                                          │
│  ─────────────────────────────                                          │
│  • query_performance_forecaster - Query duration prediction             │
│  • warehouse_optimizer       - Warehouse sizing recommendations         │
│  • performance_regression    - Performance degradation detection        │
│  • cluster_capacity_planner  - Capacity planning                        │
│  • dbr_migration_risk_scorer - DBR upgrade risk assessment              │
│  • cache_hit_predictor       - Query cache optimization                 │
│  • query_optimization_recomm - Query rewrite suggestions                │
│                                                                         │
│  RELIABILITY AGENT (5 models):                                          │
│  ─────────────────────────────                                          │
│  • job_failure_predictor     - Predict which jobs will fail             │
│  • job_duration_forecaster   - Estimate job completion time             │
│  • sla_breach_predictor      - SLA violation risk scoring               │
│  • retry_success_predictor   - Predict retry success likelihood         │
│  • pipeline_health_scorer    - Overall pipeline health assessment       │
│                                                                         │
│  QUALITY AGENT (3 models):                                              │
│  ─────────────────────────                                              │
│  • data_drift_detector       - Feature/data drift detection             │
│  • schema_change_predictor   - Schema evolution risk                    │
│  • data_freshness_predictor  - Data staleness prediction                │
└─────────────────────────────────────────────────────────────────────────┘

MLFLOW 3.0 PATTERNS USED:
-------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PATTERN                          │  IMPLEMENTATION                      │
├───────────────────────────────────┼──────────────────────────────────────┤
│  Unity Catalog Model Registry     │  mlflow.set_registry_uri("databricks-uc") │
│  LoggedModel with 'name'          │  log_model(model, name="model_name")  │
│  Model Signatures (required)      │  infer_signature(X, y)               │
│  Feature Engineering in UC        │  fe.log_model() with feature table   │
│  Output Schema                    │  output_schema=Schema([ColSpec(...)])│
│  Model Aliases                    │  set_registered_model_alias("champion") │
└───────────────────────────────────┴──────────────────────────────────────┘

PACKAGE STRUCTURE:
------------------

ml/
├── __init__.py              # This file
├── config/                  # Feature registry, model configuration
│   └── feature_registry.py  # Dynamic feature table schema lookup
├── common/                  # Shared utilities
│   ├── mlflow_utils.py      # MLflow 3.0 helpers
│   ├── training_utils.py    # Training utilities
│   └── feature_utils.py     # Feature engineering helpers
├── features/                # Feature table creation
│   └── create_feature_tables.py
├── inference/               # Batch and online inference
│   ├── batch_inference_all_models.py
│   └── score_*.py           # Per-model scoring
├── deployment/              # Model registration and deployment
│   └── register_all_models.py
├── cost/                    # Cost domain models
├── security/                # Security domain models
├── performance/             # Performance domain models
├── reliability/             # Reliability domain models
└── quality/                 # Quality domain models

Agent Domains:
  - Cost Agent (6 models): Anomaly detection, forecasting, optimization
  - Security Agent (4 models): Threat detection, exfiltration, privilege escalation
  - Performance Agent (7 models): Query forecasting, warehouse optimization
  - Reliability Agent (5 models): Failure prediction, SLA breach
  - Quality Agent (3 models): Freshness prediction, schema drift

MLflow 3.0 Features Used:
  - LoggedModel with name parameter (not artifact_path)
  - Unity Catalog Model Registry (databricks-uc)
  - Feature Engineering in Unity Catalog
  - Inference tables for model monitoring
  - mlflow.models.evaluate for traditional ML
  - Model signatures required for UC registration
"""

__version__ = "1.0.0"






