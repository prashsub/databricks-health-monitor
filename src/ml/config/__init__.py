"""
TRAINING MATERIAL: ML Configuration Package
===========================================

This package provides centralized configuration for all ML training,
most importantly the FeatureRegistry for dynamic schema queries.

WHY A FEATURE REGISTRY:
-----------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PROBLEM: Hardcoded Feature Lists                                        │
│                                                                         │
│  # train_cost_anomaly_detector.py                                       │
│  features = ["daily_dbu", "daily_cost", "serverless_cost"]              │
│                                                                         │
│  # train_budget_forecaster.py (different list!)                         │
│  features = ["daily_dbu", "daily_cost", "jobs_on_all_purpose_cost"]     │
│                                                                         │
│  # Feature table adds new column → ALL training scripts need updating!   │
│                                                                         │
│  SOLUTION: Dynamic Feature Registry                                      │
│                                                                         │
│  # All training scripts:                                                 │
│  registry = FeatureRegistry(spark, catalog, schema)                     │
│  schema_info = registry.get_feature_table_schema("cost_features")       │
│  features = registry.get_feature_columns(schema_info, exclude=[...])    │
│                                                                         │
│  # New column added → All models pick it up automatically!              │
└─────────────────────────────────────────────────────────────────────────┘

KEY COMPONENTS:
---------------

1. FeatureRegistry Class
   - Queries Unity Catalog for feature table schemas at runtime
   - Caches schemas to avoid repeated queries
   - Methods: get_feature_table_schema(), get_feature_columns()

2. FeatureTableConfig Dataclass
   - Defines domain, primary keys, label columns for each table
   - Stored in FEATURE_TABLE_CONFIGS dictionary

3. Helper Functions
   - get_feature_names_for_model: Get appropriate features for a model
   - validate_feature_list: Check features exist in table

DYNAMIC SCHEMA BENEFITS:
------------------------

- No hardcoded column lists in training scripts
- Single source of truth (Unity Catalog)
- Schema validation at runtime
- Automatic adaptation to feature engineering changes
"""

from .feature_registry import (
    FeatureRegistry,
    FeatureTableConfig,
    FEATURE_TABLE_CONFIGS,
    get_feature_names_for_model,
    validate_feature_list,
)

__all__ = [
    "FeatureRegistry",
    "FeatureTableConfig",
    "FEATURE_TABLE_CONFIGS",
    "get_feature_names_for_model",
    "validate_feature_list",
]

