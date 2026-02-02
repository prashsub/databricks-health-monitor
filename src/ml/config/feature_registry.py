"""
TRAINING MATERIAL: Dynamic Feature Registry Pattern
====================================================

This module dynamically queries feature table schemas from Unity Catalog
at runtime, eliminating the need to hardcode feature names in training scripts.

WHY DYNAMIC REGISTRY:
---------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  THE PROBLEM: Feature List Drift                                         │
│                                                                         │
│  create_feature_tables.py:              train_cost_model.py:            │
│  ─────────────────────────              ─────────────────────           │
│  Features: [A, B, C, D, E]              Features: [A, B, C, D] ← Stale! │
│           ↓ (added E)                                                   │
│  Features: [A, B, C, D, E, F]           Features: [A, B, C, D] ← Broken!│
│                                                                         │
│  HARDCODED LISTS DRIFT OUT OF SYNC!                                     │
│                                                                         │
│  THE SOLUTION: Query the table at runtime                               │
│  ─────────────────────────────────────────                              │
│  registry.get_feature_columns("cost_features")                          │
│  → Returns [A, B, C, D, E, F]  ← Always current!                        │
└─────────────────────────────────────────────────────────────────────────┘

KEY PRINCIPLE: Feature tables ARE the registry.

Training scripts should QUERY the schema, not duplicate it.

ARCHITECTURE:
-------------

┌─────────────────────────────────────────────────────────────────────────┐
│                    FEATURE REGISTRY FLOW                                 │
│                                                                         │
│  create_feature_tables.py                                               │
│  ────────────────────────                                               │
│  1. Create cost_features table with columns [A, B, C, D, E]             │
│  2. Table is the source of truth                                        │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Unity Catalog: catalog.schema.cost_features                  │      │
│  │  Schema: [workspace_id, usage_date, A, B, C, D, E, ...]       │      │
│  └──────────────────────────────────────────────────────────────┘      │
│           │                                                             │
│           ▼                                                             │
│  train_cost_model.py                                                    │
│  ──────────────────                                                     │
│  registry = FeatureRegistry(spark, catalog, schema)                     │
│  features = registry.get_feature_columns("cost_features")               │
│  → Queries actual table schema                                          │
│  → Returns [A, B, C, D, E] (always current!)                            │
└─────────────────────────────────────────────────────────────────────────┘

WHAT'S IN THE REGISTRY:
-----------------------
Static configuration (doesn't change):
- Primary keys: Which columns uniquely identify a row
- Timestamp column: For point-in-time lookups
- Exclude columns: Metadata columns that aren't features

Dynamic from Unity Catalog:
- Feature columns: Queried at runtime from actual table schema

EXCLUDE COLUMNS:
----------------
Some columns aren't features but exist in the table:
- Primary keys (workspace_id, usage_date) → Used for lookups, not features
- Metadata (feature_timestamp) → Housekeeping, not features
- Identifiers (user_id, job_id) → Can't use as features (leakage risk)

The registry automatically excludes these when returning feature columns.

Benefits:
- No more hardcoded feature lists that drift out of sync
- Changes to feature tables automatically propagate to all training scripts
- Single point of maintenance (create_feature_tables.py)
- Runtime validation catches errors immediately

Usage:
    from src.ml.config.feature_registry import FeatureRegistry
    
    registry = FeatureRegistry(spark, catalog, feature_schema)
    feature_names = registry.get_feature_columns("cost_features")
    primary_keys = registry.get_primary_keys("cost_features")
"""

from pyspark.sql import SparkSession
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field


@dataclass
class FeatureTableConfig:
    """Configuration for a feature table."""
    table_name: str
    primary_keys: List[str]
    timestamp_column: Optional[str] = None
    domain: str = ""
    description: str = ""
    
    # Columns to exclude from feature set (metadata columns)
    exclude_columns: List[str] = field(default_factory=lambda: [
        "feature_timestamp"  # Common metadata column
    ])


# Static registry of feature table metadata
# Primary keys and excluded columns are defined here since they're structural
FEATURE_TABLE_CONFIGS = {
    "cost_features": FeatureTableConfig(
        table_name="cost_features",
        primary_keys=["workspace_id", "usage_date"],
        timestamp_column="usage_date",
        domain="cost",
        description="Cost agent features for anomaly detection and forecasting",
        exclude_columns=["feature_timestamp", "workspace_id", "usage_date"]
    ),
    "security_features": FeatureTableConfig(
        table_name="security_features",
        primary_keys=["user_id", "event_date"],
        timestamp_column="event_date",
        domain="security",
        description="Security agent features for threat and anomaly detection",
        exclude_columns=["feature_timestamp", "user_id", "event_date", "user_type"]
    ),
    "performance_features": FeatureTableConfig(
        table_name="performance_features",
        primary_keys=["warehouse_id", "query_date"],
        timestamp_column="query_date",
        domain="performance",
        description="Performance agent features for query and warehouse optimization",
        exclude_columns=["feature_timestamp", "warehouse_id", "query_date"]
    ),
    "reliability_features": FeatureTableConfig(
        table_name="reliability_features",
        primary_keys=["job_id", "run_date"],
        timestamp_column="run_date",
        domain="reliability",
        description="Reliability agent features for job failure and SLA prediction",
        exclude_columns=["feature_timestamp", "job_id", "run_date"]
    ),
    "quality_features": FeatureTableConfig(
        table_name="quality_features",
        primary_keys=["catalog_name", "snapshot_date"],
        timestamp_column="snapshot_date",
        domain="quality",
        description="Quality agent features for data governance monitoring",
        exclude_columns=["feature_timestamp", "catalog_name", "snapshot_date"]
    ),
}


class FeatureRegistry:
    """
    Dynamic feature registry that queries Unity Catalog at runtime.
    
    This class provides the single source of truth for feature schemas by
    querying actual feature table schemas, not hardcoded lists.
    
    Example:
        registry = FeatureRegistry(spark, "my_catalog", "features_schema")
        
        # Get all features for a table
        feature_names = registry.get_feature_columns("cost_features")
        
        # Get primary keys
        pks = registry.get_primary_keys("cost_features")
        
        # Validate features exist
        valid = registry.validate_features("cost_features", ["daily_dbu", "fake_col"])
    """
    
    def __init__(self, spark: SparkSession, catalog: str, schema: str):
        """
        Initialize the feature registry.
        
        Args:
            spark: SparkSession for querying Unity Catalog
            catalog: Unity Catalog name
            schema: Schema containing feature tables
        """
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        self._schema_cache: Dict[str, List[str]] = {}
    
    def _get_full_table_name(self, table_name: str) -> str:
        """Get fully qualified table name."""
        return f"{self.catalog}.{self.schema}.{table_name}"
    
    def get_table_schema(self, table_name: str, use_cache: bool = True) -> List[str]:
        """
        Get all column names from a feature table.
        
        Args:
            table_name: Name of the feature table (e.g., "cost_features")
            use_cache: Whether to use cached schema (default True)
            
        Returns:
            List of all column names in the table
        """
        if use_cache and table_name in self._schema_cache:
            return self._schema_cache[table_name]
        
        full_name = self._get_full_table_name(table_name)
        
        try:
            schema = self.spark.table(full_name).schema
            columns = [field.name for field in schema.fields]
            self._schema_cache[table_name] = columns
            return columns
        except Exception as e:
            raise ValueError(f"Failed to get schema for {full_name}: {e}")
    
    def get_feature_columns(
        self,
        table_name: str,
        exclude_columns: Optional[List[str]] = None,
        include_only: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get feature columns from a table, excluding primary keys and metadata.
        
        THIS IS THE KEY METHOD - it queries the actual table schema at runtime,
        ensuring training scripts always use correct column names.
        
        Args:
            table_name: Name of the feature table
            exclude_columns: Additional columns to exclude (beyond defaults)
            include_only: If provided, only return these columns (must exist)
            
        Returns:
            List of feature column names suitable for ML training
        """
        all_columns = self.get_table_schema(table_name)
        
        # Get default exclusions from config
        config = FEATURE_TABLE_CONFIGS.get(table_name)
        default_exclude = set(config.exclude_columns if config else [])
        
        # Add any additional exclusions
        if exclude_columns:
            default_exclude.update(exclude_columns)
        
        # Filter columns
        if include_only:
            # Validate that requested columns exist
            available = set(all_columns)
            missing = set(include_only) - available
            if missing:
                raise ValueError(f"Columns not found in {table_name}: {missing}")
            feature_columns = [c for c in include_only if c in available]
        else:
            # Return all columns except exclusions
            feature_columns = [c for c in all_columns if c not in default_exclude]
        
        return feature_columns
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """
        Get primary key columns for a feature table.
        
        Args:
            table_name: Name of the feature table
            
        Returns:
            List of primary key column names
        """
        config = FEATURE_TABLE_CONFIGS.get(table_name)
        if config:
            return config.primary_keys
        else:
            raise ValueError(f"Unknown feature table: {table_name}")
    
    def get_timestamp_column(self, table_name: str) -> Optional[str]:
        """
        Get timestamp column for time series lookups.
        
        Args:
            table_name: Name of the feature table
            
        Returns:
            Timestamp column name, or None if not applicable
        """
        config = FEATURE_TABLE_CONFIGS.get(table_name)
        return config.timestamp_column if config else None
    
    def validate_features(
        self,
        table_name: str,
        requested_features: List[str]
    ) -> Dict[str, List[str]]:
        """
        Validate that requested features exist in the table.
        
        Args:
            table_name: Name of the feature table
            requested_features: List of feature names to validate
            
        Returns:
            Dict with 'valid' and 'invalid' lists
        """
        available = set(self.get_table_schema(table_name))
        requested = set(requested_features)
        
        return {
            "valid": list(requested & available),
            "invalid": list(requested - available)
        }
    
    def get_domain(self, table_name: str) -> str:
        """Get the domain for a feature table."""
        config = FEATURE_TABLE_CONFIGS.get(table_name)
        return config.domain if config else "unknown"
    
    def get_all_tables(self) -> List[str]:
        """Get list of all registered feature tables."""
        return list(FEATURE_TABLE_CONFIGS.keys())
    
    def print_table_info(self, table_name: str) -> None:
        """Print detailed information about a feature table."""
        config = FEATURE_TABLE_CONFIGS.get(table_name)
        if not config:
            print(f"Unknown table: {table_name}")
            return
        
        columns = self.get_table_schema(table_name)
        features = self.get_feature_columns(table_name)
        
        print(f"\n{'=' * 60}")
        print(f"Feature Table: {table_name}")
        print(f"{'=' * 60}")
        print(f"Domain: {config.domain}")
        print(f"Description: {config.description}")
        print(f"Primary Keys: {config.primary_keys}")
        print(f"Timestamp Column: {config.timestamp_column}")
        print(f"Total Columns: {len(columns)}")
        print(f"Feature Columns: {len(features)}")
        print(f"\nFeatures:")
        for i, f in enumerate(features, 1):
            print(f"  {i:2d}. {f}")


# =============================================================================
# Convenience Functions
# =============================================================================

def get_feature_names_for_model(
    spark: SparkSession,
    catalog: str,
    feature_schema: str,
    table_name: str,
    label_column: str
) -> List[str]:
    """
    Get feature names for ML model training, excluding label column.
    
    This is the simplest interface for training scripts.
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        feature_schema: Feature schema name
        table_name: Feature table name
        label_column: Label column to exclude
        
    Returns:
        List of feature column names
    """
    registry = FeatureRegistry(spark, catalog, feature_schema)
    return registry.get_feature_columns(
        table_name,
        exclude_columns=[label_column]
    )


def validate_feature_list(
    spark: SparkSession,
    catalog: str,
    feature_schema: str,
    table_name: str,
    feature_names: List[str]
) -> None:
    """
    Validate a feature list against the actual table schema.
    Raises ValueError if any features are invalid.
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        feature_schema: Feature schema name
        table_name: Feature table name
        feature_names: List of feature names to validate
        
    Raises:
        ValueError: If any feature names are invalid
    """
    registry = FeatureRegistry(spark, catalog, feature_schema)
    result = registry.validate_features(table_name, feature_names)
    
    if result["invalid"]:
        raise ValueError(
            f"Invalid features for {table_name}: {result['invalid']}\n"
            f"Available features: {registry.get_feature_columns(table_name)}"
        )

