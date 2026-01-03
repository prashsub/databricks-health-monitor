"""
ML Utilities Package
====================

This package contains standardized utilities for ML training:
- training_base: Standard functions for data preparation and model logging
- model_logging: Legacy model logging utilities (use training_base for new code)
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

