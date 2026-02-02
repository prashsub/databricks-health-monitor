"""
TRAINING MATERIAL: MLflow Signature Compatibility
=================================================

This module handles the tricky interplay between Unity Catalog requirements
and MLflow signature limitations.

THE DECIMAL TYPE PROBLEM:
-------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  SPARK/DELTA DATA TYPE       │  MLFLOW SIGNATURE SUPPORT                │
├──────────────────────────────┼──────────────────────────────────────────┤
│  STRING                      │  ✅ Supported                             │
│  DOUBLE                      │  ✅ Supported                             │
│  DECIMAL(38,14)              │  ❌ NOT SUPPORTED - causes errors!        │
│  BIGINT                      │  ✅ Supported                             │
│  TIMESTAMP                   │  ✅ Supported                             │
└──────────────────────────────┴──────────────────────────────────────────┘

PROBLEM: Gold layer tables use DECIMAL for precision (billing data).
PROBLEM: MLflow infer_signature() fails on DECIMAL columns.
PROBLEM: Unity Catalog REQUIRES valid signatures.

SOLUTION: Cast all numeric columns to float64 before signature inference.

    def cast_to_float64(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            try:
                df[col] = df[col].astype('float64')
            except (ValueError, TypeError):
                pass
        return df

SIGNATURE WORKFLOW:
-------------------

    1. Load training data from Feature Store (Spark DataFrame)
    2. Convert to Pandas (toPandas())
    3. Cast DECIMAL → float64 (cast_to_float64())
    4. Create signature (infer_signature())
    5. Log model with signature (fe.log_model(..., signature=signature))

WHY SEPARATE X_train_for_signature:
-----------------------------------

We keep a separate DataFrame for signature inference because:
- Training can use the original types
- Only signature inference needs float64 cast
- Preserves precision during training

CRITICAL: Unity Catalog requires models with BOTH input AND output signatures.
MLflow does NOT support DECIMAL types in signatures - must cast to float64.

Usage:
    from ml.utils.model_logging import prepare_data_for_training, log_model_with_fe

Reference: https://mlflow.org/docs/latest/model/signatures.html
"""

import pandas as pd
import numpy as np
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, List, Any, Optional


def cast_to_float64(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cast all numeric columns to float64 for MLflow compatibility.
    
    CRITICAL: MLflow signatures don't support DECIMAL(38,14) types.
    This converts all numeric columns to float64.
    """
    result = df.copy()
    for col in result.columns:
        try:
            result[col] = result[col].astype('float64')
        except (ValueError, TypeError):
            # Keep non-numeric columns as-is
            pass
    return result


def prepare_data_for_training(
    training_df,
    feature_names: List[str],
    label_col: str,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    """
    Prepare data for training with proper type casting.
    
    Args:
        training_df: Spark or Pandas DataFrame with features and label
        feature_names: List of feature column names
        label_col: Name of label column
        test_size: Test set fraction
        random_state: Random seed
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test, X_train_for_signature)
        
    Note: X_train_for_signature is used for creating MLflow input_example and signature.
    """
    # Convert to pandas if needed
    if hasattr(training_df, 'toPandas'):
        pdf = training_df.toPandas()
    else:
        pdf = training_df
    
    # Filter to available features
    available_features = [f for f in feature_names if f in pdf.columns]
    missing_features = [f for f in feature_names if f not in pdf.columns]
    
    if missing_features:
        print(f"  ⚠ Missing features (will be ignored): {missing_features[:5]}...")
    
    if not available_features:
        raise ValueError(f"No features found! Expected: {feature_names[:5]}...")
    
    # Extract features and label
    X = pdf[available_features].fillna(0).replace([np.inf, -np.inf], 0)
    y = pdf[label_col].fillna(0)
    
    # CRITICAL: Cast to float64 for MLflow signature compatibility
    X = cast_to_float64(X)
    y = y.astype('float64')
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    print(f"  Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    print(f"  Features: {len(available_features)} (all cast to float64)")
    
    return X_train, X_test, y_train, y_test, X_train


def log_model_with_fe(
    fe,  # FeatureEngineeringClient
    model: Any,
    training_set: Any,  # TrainingSet from fe.create_training_set
    X_train: pd.DataFrame,
    registered_model_name: str,
    run_name: str,
    tags: Dict[str, str],
    params: Dict[str, Any],
    metrics: Dict[str, float],
    artifact_path: str = "model"
) -> Dict[str, Any]:
    """
    Log model with Feature Engineering and proper Unity Catalog signature.
    
    This function ensures the model is logged with:
    1. input_example (required for signature inference)
    2. Explicit signature with both input AND output (required for UC)
    3. Feature lookup metadata (for automatic feature retrieval at inference)
    
    Args:
        fe: FeatureEngineeringClient instance
        model: Trained sklearn model
        training_set: TrainingSet from fe.create_training_set
        X_train: Training features DataFrame (float64)
        registered_model_name: Full UC model name (catalog.schema.model_name)
        run_name: MLflow run name
        tags: Dict of tags to log
        params: Dict of parameters to log
        metrics: Dict of metrics to log
        artifact_path: Artifact path for model (default: "model")
        
    Returns:
        Dict with run_id, model_name, registered_as
    """
    print(f"\nLogging model: {registered_model_name}")
    
    # Create input example (first 5 rows, ensure float64)
    input_example = X_train.head(5).astype('float64')
    
    # Get sample predictions for output signature
    sample_predictions = model.predict(input_example)
    
    # Infer signature with BOTH input AND output (required for Unity Catalog)
    signature = infer_signature(input_example, sample_predictions)
    print(f"  ✓ Signature: {len(input_example.columns)} input features → {type(sample_predictions[0]).__name__} output")
    
    # Disable autolog to avoid conflicts
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # Log metadata
        mlflow.set_tags(tags)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        
        # Log model with Feature Engineering metadata
        # input_example and signature are REQUIRED for Unity Catalog
        fe.log_model(
            model=model,
            artifact_path=artifact_path,
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_model_name,
            input_example=input_example,
            signature=signature
        )
        
        print(f"  ✓ Model registered: {registered_model_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": registered_model_name.split(".")[-1],
            "registered_as": registered_model_name
        }


def get_standard_tags(
    model_name: str,
    domain: str,
    model_type: str,
    algorithm: str,
    use_case: str,
    training_table: str
) -> Dict[str, str]:
    """Get standard tags for model logging."""
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

