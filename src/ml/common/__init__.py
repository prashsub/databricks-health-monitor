"""
TRAINING MATERIAL: ML Common Utilities Package Architecture
===========================================================

This package provides shared utilities for all 25 ML models, ensuring
consistent patterns for MLflow, Feature Engineering, and training.

PACKAGE STRUCTURE:
------------------

    ml/common/
    ├── __init__.py          # This file - exports all public APIs
    ├── mlflow_utils.py      # MLflow 3.0 + Unity Catalog patterns
    ├── feature_utils.py     # Feature Engineering (UC Feature Store)
    └── training_utils.py    # Training, splitting, evaluation

WHY A COMMON PACKAGE:
---------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  WITHOUT COMMON UTILITIES          │  WITH COMMON UTILITIES              │
├────────────────────────────────────┼─────────────────────────────────────┤
│  Each model implements MLflow      │  MLflowConfig dataclass             │
│  Each model implements splitting   │  TrainingConfig + split_data()      │
│  Each model implements metrics     │  evaluate_model() standardized      │
│  Bugs fixed in one model only      │  Fixes propagate to all models      │
│  Inconsistent experiment naming    │  setup_mlflow_experiment() pattern  │
│  25 × duplicate code               │  1 × shared implementation          │
└────────────────────────────────────┴─────────────────────────────────────┘

KEY EXPORTS:
------------

MLflow Utilities:
- MLflowConfig: Dataclass for MLflow configuration
- setup_mlflow_experiment: Create/get experiment with standard naming
- log_model_with_signature: Log model with proper signature for UC

Feature Utilities:
- FeatureEngineeringConfig: Dataclass for feature table configuration
- create_feature_table: Create/update feature tables in UC
- get_feature_lookups: Build FeatureLookup list for training

Training Utilities:
- TrainingConfig: Dataclass for training parameters
- split_data: Train/val/test split with time-series support
- evaluate_model: Calculate standard metrics by problem type
- cross_validate: K-fold cross-validation
"""

from .mlflow_utils import MLflowConfig, setup_mlflow_experiment, log_model_with_signature
from .feature_utils import FeatureEngineeringConfig, create_feature_table, get_feature_lookups
from .training_utils import TrainingConfig, split_data, evaluate_model, cross_validate

__all__ = [
    "MLflowConfig",
    "setup_mlflow_experiment",
    "log_model_with_signature",
    "FeatureEngineeringConfig",
    "create_feature_table",
    "get_feature_lookups",
    "TrainingConfig",
    "split_data",
    "evaluate_model",
    "cross_validate",
]






