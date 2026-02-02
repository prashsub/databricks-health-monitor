"""
TRAINING MATERIAL: Standardized ML Training Utilities
=====================================================

This module provides standardized functions that ALL training scripts should use.
It eliminates the copy-paste errors that cause recurring issues:
- Variable naming inconsistencies (X vs X_train)
- Missing MLflow signature handling
- Incorrect data type casting
- Feature validation

WHY CENTRALIZED UTILITIES:
--------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  COPY-PASTE PROBLEMS (Without this module):                              │
│                                                                         │
│  Script 1: X = df[features]         Script 2: X_train = df[features]    │
│  Script 1: y.astype('float')        Script 2: y.astype(float)           │
│  Script 1: mlflow.sklearn.log_model Script 2: fe.log_model (different!) │
│                                                                         │
│  → Inconsistent behavior across models                                  │
│  → Hard to find bugs                                                    │
│  → Changes need to be made in 25+ files                                 │
│                                                                         │
│  WITH CENTRALIZED UTILITIES:                                            │
│  - Single implementation, used everywhere                               │
│  - Fix once, fix all models                                             │
│  - Guaranteed consistency                                               │
└─────────────────────────────────────────────────────────────────────────┘

KEY PATTERNS IN THIS MODULE:
----------------------------

1. SETUP FUNCTIONS
   - setup_training_environment(): Set MLflow experiment
   - get_run_name(): Generate unique run names
   - get_standard_tags(): Consistent MLflow tags

2. DATA PREPARATION (CRITICAL)
   - prepare_training_data(): For supervised models
   - prepare_anomaly_detection_data(): For unsupervised models
   
   Why this matters:
   - MLflow requires float64 (Spark DECIMAL doesn't work!)
   - NaN/Inf values crash sklearn
   - Consistent train/test split with stratification

3. MODEL LOGGING (CRITICAL)
   - log_model_with_features(): With Feature Store
   - log_anomaly_model_with_features(): Anomaly detection + Feature Store
   - log_model_without_features(): Custom preprocessing
   
   Why this matters:
   - Unity Catalog requires proper signatures
   - Feature Store lineage requires fe.log_model()
   - Anomaly detection has different output schema

4. METRIC CALCULATION
   - calculate_classification_metrics()
   - calculate_regression_metrics()
   - calculate_anomaly_metrics()

DATA TYPE CASTING PATTERN:
--------------------------
MLflow and sklearn have strict type requirements:

┌─────────────────────────────────────────────────────────────────────────┐
│  SOURCE DATA TYPE      │  PROBLEM                  │  SOLUTION          │
├────────────────────────┼───────────────────────────┼────────────────────┤
│  Spark DECIMAL         │  MLflow can't serialize   │  Cast to float64   │
│  NaN / Inf             │  sklearn crashes          │  fillna(0)         │
│  bool                  │  Some models need numeric │  Cast to float64   │
│  int                   │  Regression needs float   │  Cast to float64   │
└────────────────────────┴───────────────────────────┴────────────────────┘

The prepare_training_data() function handles ALL of these automatically.

OUTPUT SCHEMA PATTERN:
----------------------
Unity Catalog models REQUIRE explicit output schema:

- Regression: Schema([ColSpec(DataType.double)])
- Classification/Anomaly: Schema([ColSpec(DataType.long)])

The log_model functions handle this automatically based on model_type.

Usage:
    from src.ml.utils.training_base import (
        prepare_training_data,
        log_model_with_features,
        setup_training_environment,
        create_feature_lookup_training_set,
    )
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from sklearn.model_selection import train_test_split
from mlflow.models.signature import infer_signature
import mlflow
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set MLflow registry URI for Unity Catalog
mlflow.set_registry_uri("databricks-uc")


# =============================================================================
# SETUP FUNCTIONS
# =============================================================================

def setup_training_environment(model_name: str) -> None:
    """
    Set up MLflow experiment for training.
    
    Args:
        model_name: Name of the model being trained
    """
    experiment_path = f"/Shared/health_monitor_ml_{model_name}"
    mlflow.set_experiment(experiment_path)
    print(f"✓ Experiment: {experiment_path}")


def get_run_name(model_name: str, algorithm: str) -> str:
    """Generate a unique run name with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{algorithm}_v1_{timestamp}"


def get_standard_tags(
    model_name: str,
    domain: str,
    model_type: str,
    algorithm: str,
    use_case: str,
    training_table: str
) -> Dict[str, str]:
    """
    Get standard MLflow tags for all models.
    
    Args:
        model_name: Name of the model
        domain: Domain (cost, security, performance, reliability, quality)
        model_type: Type (classification, regression, anomaly_detection)
        algorithm: Algorithm name (e.g., "gradient_boosting", "isolation_forest")
        use_case: Business use case description
        training_table: Feature table used for training
        
    Returns:
        Dictionary of tags
    """
    return {
        "project": "databricks_health_monitor",
        "domain": domain,
        "model_name": model_name,
        "model_type": model_type,
        "algorithm": algorithm,
        "use_case": use_case,
        "training_data": training_table,
        "feature_engineering": "unity_catalog"
    }


# =============================================================================
# FEATURE LOOKUP & TRAINING SET CREATION
# =============================================================================

def create_feature_lookup_training_set(
    spark: SparkSession,
    fe: FeatureEngineeringClient,
    feature_table: str,
    feature_names: List[str],
    label_column: str,
    lookup_keys: List[str],
    additional_filter: Optional[str] = None
) -> Tuple[Any, DataFrame, List[str]]:
    """
    Create training set using Feature Engineering with proper validation.
    
    This is the STANDARD way to create training sets - use this instead of
    implementing your own FeatureLookup logic.
    
    Args:
        spark: SparkSession
        fe: FeatureEngineeringClient
        feature_table: Fully qualified feature table name
        feature_names: List of feature columns (will be validated)
        label_column: Name of the label column
        lookup_keys: Primary key columns for feature lookup
        additional_filter: Optional SQL filter condition
        
    Returns:
        Tuple of (training_set, training_df, available_features)
    """
    print("\nCreating training set with Feature Engineering...")
    
    # Validate feature table exists and get actual schema
    try:
        actual_schema = spark.table(feature_table).schema
        actual_columns = {f.name for f in actual_schema.fields}
    except Exception as e:
        raise ValueError(f"Feature table {feature_table} not found: {e}")
    
    # Validate and filter feature names to only those that exist
    available_features = [f for f in feature_names if f in actual_columns]
    missing_features = [f for f in feature_names if f not in actual_columns]
    
    if missing_features:
        print(f"  ⚠ Removing missing features: {missing_features}")
    
    if not available_features:
        raise ValueError(f"No valid features found in {feature_table}!")
    
    # Validate label column exists
    if label_column not in actual_columns:
        raise ValueError(f"Label column '{label_column}' not found in {feature_table}!")
    
    # Create FeatureLookup
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=available_features,
            lookup_key=lookup_keys
        )
    ]
    
    # Build base DataFrame with only lookup keys + label
    select_cols = lookup_keys + [label_column]
    base_df = (
        spark.table(feature_table)
        .select(*select_cols)
        .filter(F.col(label_column).isNotNull())
    )
    
    # Apply additional filter if provided
    if additional_filter:
        base_df = base_df.filter(additional_filter)
    
    base_df = base_df.distinct()
    record_count = base_df.count()
    
    print(f"  Base DataFrame has {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data found in {feature_table} with non-null {label_column}!")
    
    # Create training set
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label=label_column,
        exclude_columns=lookup_keys  # Exclude PKs from features
    )
    
    training_df = training_set.load_df()
    final_count = training_df.count()
    
    print(f"✓ Training set: {final_count} rows, {len(available_features)} features")
    
    return training_set, training_df, available_features


# =============================================================================
# DATA PREPARATION - USE THESE INSTEAD OF CUSTOM IMPLEMENTATIONS
# =============================================================================

def prepare_training_data(
    training_df: DataFrame,
    feature_names: List[str],
    label_column: str,
    test_size: float = 0.2,
    random_state: int = 42,
    cast_label_to: str = "float64",
    stratify: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    STANDARD data preparation function for ALL training scripts.
    
    This function handles:
    - Converting Spark DF to Pandas
    - Filtering to available features
    - Casting to float64 (required for MLflow)
    - Train/test split with consistent variable naming
    - Handling missing values and infinities
    
    ALWAYS use this instead of implementing your own prepare function.
    
    Args:
        training_df: Spark DataFrame from create_training_set
        feature_names: List of feature column names
        label_column: Name of the label column
        test_size: Proportion for test set (default 0.2)
        random_state: Random seed (default 42)
        cast_label_to: Type to cast label ("float64" for regression, "int" for classification)
        stratify: Whether to use stratified split (for classification)
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
        
    Note:
        X_train is what you pass to model.fit() and for input_example in log_model
    """
    print("\nPreparing training data...")
    
    # Convert to pandas
    pdf = training_df.toPandas()
    
    # Filter to available features (handles missing columns gracefully)
    available_features = [f for f in feature_names if f in pdf.columns]
    missing_features = [f for f in feature_names if f not in pdf.columns]
    
    if missing_features:
        print(f"  ⚠ Features not in DataFrame: {missing_features}")
    
    if not available_features:
        raise ValueError("No valid features found in DataFrame!")
    
    # Prepare features - X (NOT X_train at this point!)
    X = pdf[available_features].copy()
    
    # Handle missing values and infinities
    X = X.fillna(0).replace([np.inf, -np.inf], 0)
    
    # CRITICAL: Cast all columns to float64 (MLflow doesn't support DECIMAL)
    for col in X.columns:
        X[col] = X[col].astype('float64')
    
    # Prepare label
    y = pdf[label_column].fillna(0)
    
    # Cast label to appropriate type
    if cast_label_to == "int":
        y = y.astype(int)
    else:
        y = y.astype('float64')
    
    print(f"  Features: {len(available_features)}, Samples: {len(X)}")
    
    # Train/test split
    stratify_param = y if stratify and y.nunique() > 1 else None
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size, 
        random_state=random_state,
        stratify=stratify_param
    )
    
    print(f"✓ Split: Train={len(X_train)}, Test={len(X_test)}")
    
    return X_train, X_test, y_train, y_test


def prepare_anomaly_detection_data(
    training_df: DataFrame,
    feature_names: List[str]
) -> pd.DataFrame:
    """
    STANDARD data preparation for unsupervised anomaly detection models.
    
    Anomaly detection models (Isolation Forest) don't have labels,
    so they use the full dataset.
    
    Args:
        training_df: Spark DataFrame with features
        feature_names: List of feature column names
        
    Returns:
        X_train: Pandas DataFrame ready for model.fit()
    """
    print("\nPreparing data for anomaly detection...")
    
    pdf = training_df.toPandas()
    
    # Filter to available features
    available_features = [f for f in feature_names if f in pdf.columns]
    missing_features = [f for f in feature_names if f not in pdf.columns]
    
    if missing_features:
        print(f"  ⚠ Features not in DataFrame: {missing_features}")
    
    if not available_features:
        raise ValueError("No valid features found in DataFrame!")
    
    # Prepare features
    X_train = pdf[available_features].copy()
    X_train = X_train.fillna(0).replace([np.inf, -np.inf], 0)
    
    # CRITICAL: Cast to float64
    for col in X_train.columns:
        X_train[col] = X_train[col].astype('float64')
    
    print(f"✓ Samples: {len(X_train)}, Features: {len(available_features)}")
    
    return X_train


# =============================================================================
# MODEL LOGGING - USE THESE INSTEAD OF CUSTOM IMPLEMENTATIONS
# =============================================================================

def log_model_with_features(
    fe: FeatureEngineeringClient,
    model: Any,
    training_set: Any,
    X_train: pd.DataFrame,
    metrics: Dict[str, float],
    hyperparams: Dict[str, Any],
    model_name: str,
    domain: str,
    model_type: str,
    algorithm: str,
    use_case: str,
    catalog: str,
    feature_schema: str,
    feature_table: str
) -> Dict[str, Any]:
    """
    STANDARD model logging with Feature Engineering.
    
    This function handles:
    - Creating input example (first 5 rows)
    - Inferring signature with BOTH input AND output (required for Unity Catalog)
    - Logging with proper tags and metrics
    - Registering model in Unity Catalog
    
    ALWAYS use this instead of implementing your own log_model function.
    
    Args:
        fe: FeatureEngineeringClient
        model: Trained model
        training_set: TrainingSet from create_training_set
        X_train: Training features (Pandas DataFrame)
        metrics: Dictionary of metrics to log
        hyperparams: Dictionary of hyperparameters
        model_name: Model name for registration
        domain: Domain (cost, security, etc.)
        model_type: Type (classification, regression, anomaly_detection)
        algorithm: Algorithm name
        use_case: Business use case description
        catalog: Unity Catalog name
        feature_schema: Feature schema name
        feature_table: Feature table name
        
    Returns:
        Dictionary with run_id, model_name, registered_as, metrics
    """
    from mlflow.types import ColSpec, DataType, Schema
    
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    # Determine output schema based on model type
    # Regression: double, Classification: long
    if model_type == "regression":
        output_schema = Schema([ColSpec(DataType.double)])
        print(f"  Output schema: double (regression)")
    else:
        output_schema = Schema([ColSpec(DataType.long)])
        print(f"  Output schema: long (classification)")
    
    # Disable autolog to prevent conflicts
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=get_run_name(model_name, algorithm)) as run:
        # Set tags
        tags = get_standard_tags(
            model_name, domain, model_type, algorithm, use_case, feature_table
        )
        mlflow.set_tags(tags)
        
        # Log hyperparameters
        mlflow.log_params(hyperparams)
        mlflow.log_param("feature_engineering", "unity_catalog")
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Log model with Feature Engineering client
        # Uses output_schema + infer_input_example (recommended pattern per official docs)
        # This pattern ensures proper schema inference at inference time
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name,
            infer_input_example=True,
            output_schema=output_schema
        )
        
        print(f"✓ Model logged: {registered_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": algorithm,
            "hyperparameters": hyperparams,
            "metrics": metrics
        }


def log_anomaly_model_with_features(
    fe: FeatureEngineeringClient,
    model: Any,
    training_set: Any,
    X_train: pd.DataFrame,
    metrics: Dict[str, float],
    hyperparams: Dict[str, Any],
    model_name: str,
    domain: str,
    algorithm: str,
    use_case: str,
    catalog: str,
    feature_schema: str,
    feature_table: str
) -> Dict[str, Any]:
    """
    STANDARD anomaly detection model logging.
    
    For unsupervised models (Isolation Forest) that don't have labels.
    Uses mlflow.sklearn.log_model directly since anomaly detection models
    with label=None training_set have signature issues with fe.log_model.
    
    Args:
        fe: FeatureEngineeringClient
        model: Trained anomaly detection model
        training_set: TrainingSet from create_training_set (with label=None) - NOT USED
        X_train: Training features (Pandas DataFrame)
        metrics: Dictionary of metrics to log
        hyperparams: Dictionary of hyperparameters
        model_name: Model name for registration
        domain: Domain (cost, security, etc.)
        algorithm: Algorithm name
        use_case: Business use case description
        catalog: Unity Catalog name
        feature_schema: Feature schema name
        feature_table: Feature table name
        
    Returns:
        Dictionary with run_id, model_name, registered_as, metrics
    """
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging anomaly model: {registered_name}")
    
    # Create input example and get predictions for signature
    input_example = X_train.head(5).astype('float64')
    predictions = model.predict(input_example)
    signature = infer_signature(input_example, predictions)
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=get_run_name(model_name, algorithm)) as run:
        tags = get_standard_tags(
            model_name, domain, "anomaly_detection", algorithm, use_case, feature_table
        )
        mlflow.set_tags(tags)
        mlflow.log_params(hyperparams)
        mlflow.log_param("feature_table", feature_table)
        mlflow.log_metrics(metrics)
        
        # Log model with Feature Engineering client
        # Uses explicit signature and input_example for proper UC registration
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            signature=signature,
            input_example=input_example,
            registered_model_name=registered_name
        )
        
        print(f"✓ Anomaly model logged: {registered_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": algorithm,
            "hyperparameters": hyperparams,
            "metrics": metrics
        }


def log_model_without_features(
    model: Any,
    X_train: pd.DataFrame,
    metrics: Dict[str, float],
    hyperparams: Dict[str, Any],
    model_name: str,
    domain: str,
    model_type: str,
    algorithm: str,
    use_case: str,
    catalog: str,
    feature_schema: str,
    training_table: str
) -> Dict[str, Any]:
    """
    STANDARD model logging WITHOUT Feature Engineering.
    
    Use this when the model uses custom preprocessing (e.g., TF-IDF) that
    can't be represented as feature lookups.
    
    Args:
        model: Trained model
        X_train: Training features (Pandas DataFrame)
        metrics: Dictionary of metrics to log
        hyperparams: Dictionary of hyperparameters
        model_name: Model name for registration
        domain: Domain (cost, security, etc.)
        model_type: Type (classification, regression, anomaly_detection)
        algorithm: Algorithm name
        use_case: Business use case description
        catalog: Unity Catalog name
        feature_schema: Feature schema name
        training_table: Training table name (for documentation)
        
    Returns:
        Dictionary with run_id, model_name, registered_as, metrics
    """
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model (without FE): {registered_name}")
    
    # Create input example
    input_example = X_train.head(5).astype('float64')
    predictions = model.predict(input_example)
    signature = infer_signature(input_example, predictions)
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=get_run_name(model_name, algorithm)) as run:
        tags = get_standard_tags(
            model_name, domain, model_type, algorithm, use_case, training_table
        )
        mlflow.set_tags(tags)
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name=registered_name,
            input_example=input_example,
            signature=signature
        )
        
        print(f"✓ Model logged: {registered_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": algorithm,
            "hyperparameters": hyperparams,
            "metrics": metrics
        }


# =============================================================================
# METRIC CALCULATION HELPERS
# =============================================================================

def calculate_classification_metrics(
    model: Any,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series
) -> Dict[str, float]:
    """
    Calculate standard classification metrics.
    
    Returns:
        Dictionary with accuracy, f1, precision, recall, and sample counts
    """
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    
    y_pred = model.predict(X_test)
    
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1": round(float(f1_score(y_test, y_pred, average='weighted', zero_division=0)), 4),
        "precision": round(float(precision_score(y_test, y_pred, average='weighted', zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, average='weighted', zero_division=0)), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features_count": len(X_train.columns)
    }
    
    print(f"✓ Accuracy: {metrics['accuracy']}, F1: {metrics['f1']}")
    return metrics


def calculate_regression_metrics(
    model: Any,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series
) -> Dict[str, float]:
    """
    Calculate standard regression metrics.
    
    Returns:
        Dictionary with r2, mse, mae, and sample counts
    """
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    
    y_pred = model.predict(X_test)
    
    metrics = {
        "train_r2": round(float(model.score(X_train, y_train)), 4),
        "test_r2": round(float(r2_score(y_test, y_pred)), 4),
        "mse": round(float(mean_squared_error(y_test, y_pred)), 4),
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features_count": len(X_train.columns)
    }
    
    print(f"✓ R²: {metrics['test_r2']}, MSE: {metrics['mse']}")
    return metrics


def calculate_anomaly_metrics(
    model: Any,
    X_train: pd.DataFrame
) -> Dict[str, float]:
    """
    Calculate anomaly detection metrics.
    
    Returns:
        Dictionary with anomaly_rate and sample counts
    """
    predictions = model.predict(X_train)
    anomaly_rate = float((predictions == -1).sum() / len(predictions))
    
    metrics = {
        "anomaly_rate": round(anomaly_rate, 4),
        "training_samples": len(X_train),
        "features_count": len(X_train.columns),
        "anomalies_detected": int((predictions == -1).sum())
    }
    
    print(f"✓ Anomaly rate: {metrics['anomaly_rate'] * 100:.1f}%")
    return metrics

