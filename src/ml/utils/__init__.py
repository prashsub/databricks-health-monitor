"""
TRAINING MATERIAL: ML Utilities Package
=======================================

This package provides the standardized training pipeline functions used
by all 25 ML models in the project.

TRAINING PIPELINE FLOW:
-----------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  1. setup_training_environment()                                         │
│     └── Creates MLflow experiment: /Shared/health_monitor_ml_{model}    │
│                                                                         │
│  2. create_feature_lookup_training_set()                                 │
│     └── Joins features to labels using FeatureLookup                    │
│                                                                         │
│  3. prepare_training_data() or prepare_anomaly_detection_data()          │
│     └── Handles NaN/Inf, type conversions, train/test split             │
│                                                                         │
│  4. [Model-specific training code]                                       │
│     └── XGBClassifier, GradientBoostingRegressor, IsolationForest       │
│                                                                         │
│  5. calculate_*_metrics()                                                │
│     └── classification_metrics, regression_metrics, anomaly_metrics     │
│                                                                         │
│  6. log_model_with_features() or log_model_without_features()            │
│     └── Logs to MLflow with fe.log_model(), registers to UC             │
└─────────────────────────────────────────────────────────────────────────┘

FUNCTION CATEGORIES:
--------------------

**Setup Functions:**
- setup_training_environment: MLflow experiment + FeatureRegistry
- get_run_name: Consistent run naming with timestamp
- get_standard_tags: Domain, algorithm, model name tags

**Feature Lookup:**
- create_feature_lookup_training_set: Builds training_set with lineage

**Data Preparation:**
- prepare_training_data: For classification/regression
- prepare_anomaly_detection_data: For unsupervised anomaly detection

**Model Logging:**
- log_model_with_features: Uses fe.log_model() with Feature Store
- log_model_without_features: Uses mlflow.sklearn.log_model()

**Metrics:**
- calculate_classification_metrics: accuracy, precision, recall, f1, roc_auc
- calculate_regression_metrics: mse, rmse, mae, mape, r2
- calculate_anomaly_metrics: contamination-adjusted scores
"""

from .training_base import (
    # Setup functions
    setup_training_environment,
    get_run_name,
    get_standard_tags,
    
    # Feature lookup & training set
    create_feature_lookup_training_set,
    
    # Data preparation
    prepare_training_data,
    prepare_anomaly_detection_data,
    
    # Model logging
    log_model_with_features,
    log_model_without_features,
    
    # Metrics
    calculate_classification_metrics,
    calculate_regression_metrics,
    calculate_anomaly_metrics,
)

__all__ = [
    "setup_training_environment",
    "get_run_name",
    "get_standard_tags",
    "create_feature_lookup_training_set",
    "prepare_training_data",
    "prepare_anomaly_detection_data",
    "log_model_with_features",
    "log_model_without_features",
    "calculate_classification_metrics",
    "calculate_regression_metrics",
    "calculate_anomaly_metrics",
]

