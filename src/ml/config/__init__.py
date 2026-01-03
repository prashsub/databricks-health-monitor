"""
ML Configuration Package
========================

This package contains configuration modules for ML training:
- feature_registry: Single source of truth for feature table schemas
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

