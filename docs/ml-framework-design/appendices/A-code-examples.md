# Appendix A - Code Examples

## Complete Training Script Template

This is a production-ready template for creating new ML models using Unity Catalog Feature Engineering.

```python
# Databricks notebook source

"""
================================================================================
MODEL: {model_name}
DOMAIN: {cost|security|performance|reliability|quality}
TYPE: {regression|classification|anomaly_detection}
================================================================================

Description:
    {Brief description of what this model does}

Features:
    Source: {feature_table_name}
    Primary Keys: {pk1, pk2}
    Label: {label_column}

Algorithm: {algorithm_name}

Usage:
    1. Run Feature Pipeline to create/update feature tables
    2. Run this script to train and register model
    3. Run Inference Pipeline to generate predictions

Dependencies:
    - Feature table with PRIMARY KEY constraint
    - MLflow registry URI set to databricks-uc

Author: {author}
Created: {date}
================================================================================
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingRegressor  # Change as needed
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
from datetime import datetime

# Set MLflow registry to Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# =============================================================================
# CONFIGURATION - UPDATE THESE FOR YOUR MODEL
# =============================================================================

MODEL_NAME = "model_name"
DOMAIN = "cost"  # cost|security|performance|reliability|quality
ALGORITHM = "gradient_boosting"
MODEL_TYPE = "regression"  # regression|classification|anomaly_detection

FEATURE_TABLE_NAME = "cost_features"
PRIMARY_KEY_COLUMNS = ["workspace_id", "usage_date"]
LABEL_COLUMN = "daily_cost"  # Set to None for anomaly detection

# Features to use from feature table
FEATURE_NAMES = [
    "daily_dbu",
    "daily_cost", 
    "avg_dbu_7d",
    "avg_dbu_30d",
    "dbu_change_pct_1d",
    "dbu_change_pct_7d",
    "z_score_7d",
    "is_weekend",
    "day_of_week"
]

# Hyperparameters
HYPERPARAMS = {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "random_state": 42
}

# COMMAND ----------

# =============================================================================
# PARAMETERS
# =============================================================================

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Configuration:")
    print(f"  Catalog: {catalog}")
    print(f"  Gold Schema: {gold_schema}")
    print(f"  Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema

# COMMAND ----------

# =============================================================================
# MLFLOW SETUP
# =============================================================================

def setup_mlflow(model_name: str) -> str:
    """Set up MLflow experiment."""
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    
    try:
        mlflow.set_experiment(experiment_name)
    except Exception:
        mlflow.create_experiment(experiment_name)
        mlflow.set_experiment(experiment_name)
    
    print(f"  ✓ Experiment: {experiment_name}")
    return experiment_name

# COMMAND ----------

# =============================================================================
# TRAINING SET CREATION
# =============================================================================

def create_training_set_with_features(
    spark: SparkSession,
    fe: FeatureEngineeringClient,
    catalog: str,
    feature_schema: str
):
    """
    Create training set using Feature Engineering.
    
    CRITICAL PATTERNS:
    1. base_df contains ONLY: primary keys + label
    2. Label MUST be cast to DOUBLE (regression) or INT (classification)
    3. Features are automatically looked up
    """
    feature_table = f"{catalog}.{feature_schema}.{FEATURE_TABLE_NAME}"
    
    print(f"\nCreating training set...")
    print(f"  Feature table: {feature_table}")
    
    # =================================================================
    # STEP 1: Create base DataFrame with PKs + label
    # =================================================================
    if LABEL_COLUMN:
        # Supervised: include label, cast to appropriate type
        label_type = "double" if MODEL_TYPE == "regression" else "int"
        
        base_df = (spark.table(feature_table)
                   .select(
                       *PRIMARY_KEY_COLUMNS,
                       F.col(LABEL_COLUMN).cast(label_type).alias(LABEL_COLUMN)
                   )
                   .filter(F.col(LABEL_COLUMN).isNotNull()))
    else:
        # Unsupervised: no label needed
        base_df = spark.table(feature_table).select(*PRIMARY_KEY_COLUMNS)
    
    # Filter NULL primary keys
    for pk in PRIMARY_KEY_COLUMNS:
        base_df = base_df.filter(F.col(pk).isNotNull())
    
    base_df = base_df.distinct()
    
    record_count = base_df.count()
    print(f"  Records: {record_count:,}")
    
    if record_count == 0:
        raise ValueError("No records found for training!")
    
    # =================================================================
    # STEP 2: Define feature lookups
    # =================================================================
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=FEATURE_NAMES,
            lookup_key=PRIMARY_KEY_COLUMNS
        )
    ]
    
    # =================================================================
    # STEP 3: Create training set
    # =================================================================
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label=LABEL_COLUMN,
        exclude_columns=PRIMARY_KEY_COLUMNS
    )
    
    training_df = training_set.load_df()
    print(f"  ✓ Training set created with {len(FEATURE_NAMES)} features")
    
    return training_set, training_df

# COMMAND ----------

# =============================================================================
# MODEL TRAINING
# =============================================================================

def prepare_and_train(training_df, feature_names, label_column):
    """
    Prepare features and train model.
    
    Returns: (model, metrics, hyperparams, X_train)
    """
    print("\nPreparing training data...")
    
    # Select columns
    if label_column:
        pdf = training_df.select(feature_names + [label_column]).toPandas()
    else:
        pdf = training_df.select(feature_names).toPandas()
    
    # Handle data types - convert all features to numeric
    for col in feature_names:
        pdf[col] = pd.to_numeric(pdf[col], errors='coerce')
    pdf = pdf.fillna(0).replace([np.inf, -np.inf], 0)
    
    # Prepare features
    X = pdf[feature_names].astype('float64')
    
    # Prepare labels (if supervised)
    if label_column:
        if MODEL_TYPE == "regression":
            y = pdf[label_column].astype('float64')
        else:
            y = pdf[label_column].astype('int')
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    else:
        X_train = X
        X_test = None
        y_train = None
        y_test = None
    
    print(f"  Training samples: {len(X_train):,}")
    if X_test is not None:
        print(f"  Test samples: {len(X_test):,}")
    
    # =================================================================
    # TRAIN MODEL
    # =================================================================
    print("\nTraining model...")
    
    if MODEL_TYPE == "regression":
        from sklearn.ensemble import GradientBoostingRegressor
        model = GradientBoostingRegressor(**HYPERPARAMS)
        model.fit(X_train, y_train)
        
        # Metrics
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        y_pred = model.predict(X_test)
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        mae = np.mean(np.abs(y_test - y_pred))
        
        metrics = {
            "train_r2": train_score,
            "test_r2": test_score,
            "rmse": rmse,
            "mae": mae,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
        
        print(f"  ✓ Train R²: {train_score:.4f}")
        print(f"  ✓ Test R²: {test_score:.4f}")
        
    elif MODEL_TYPE == "classification":
        from xgboost import XGBClassifier
        model = XGBClassifier(**HYPERPARAMS)
        model.fit(X_train, y_train)
        
        # Metrics
        from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
            "auc_roc": roc_auc_score(y_test, y_prob),
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
        
        print(f"  ✓ Accuracy: {metrics['accuracy']:.4f}")
        print(f"  ✓ F1: {metrics['f1']:.4f}")
        
    elif MODEL_TYPE == "anomaly_detection":
        from sklearn.ensemble import IsolationForest
        model = IsolationForest(**HYPERPARAMS)
        model.fit(X_train)
        
        # Metrics
        predictions = model.predict(X_train)
        scores = model.decision_function(X_train)
        anomaly_rate = (predictions == -1).mean()
        
        metrics = {
            "anomaly_rate": anomaly_rate,
            "avg_anomaly_score": scores[predictions == -1].mean() if anomaly_rate > 0 else 0,
            "training_samples": len(X_train)
        }
        
        print(f"  ✓ Anomaly rate: {anomaly_rate:.2%}")
    
    return model, metrics, HYPERPARAMS, X_train

# COMMAND ----------

# =============================================================================
# MODEL LOGGING
# =============================================================================

def log_model_with_feature_engineering(
    fe: FeatureEngineeringClient,
    model,
    training_set,
    X_train: pd.DataFrame,
    metrics: dict,
    hyperparams: dict,
    catalog: str,
    feature_schema: str
):
    """
    Log model to Unity Catalog with Feature Engineering metadata.
    
    CRITICAL: Must include training_set, signature, and input_example.
    """
    registered_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=f"{MODEL_NAME}_{ALGORITHM}") as run:
        # =================================================================
        # SET TAGS
        # =================================================================
        mlflow.set_tags({
            "project": "databricks_health_monitor",
            "domain": DOMAIN,
            "model_name": MODEL_NAME,
            "model_type": MODEL_TYPE,
            "algorithm": ALGORITHM,
            "feature_engineering": "unity_catalog"
        })
        
        # =================================================================
        # LOG PARAMETERS AND METRICS
        # =================================================================
        mlflow.log_params(hyperparams)
        mlflow.log_params({
            "feature_table": f"{catalog}.{feature_schema}.{FEATURE_TABLE_NAME}",
            "primary_keys": ",".join(PRIMARY_KEY_COLUMNS),
            "feature_count": len(FEATURE_NAMES)
        })
        mlflow.log_metrics(metrics)
        
        # =================================================================
        # CREATE SIGNATURE (CRITICAL!)
        # =================================================================
        input_example = X_train.head(5).astype('float64')
        sample_predictions = model.predict(input_example)
        signature = infer_signature(input_example, sample_predictions)
        
        # =================================================================
        # LOG MODEL WITH FEATURE METADATA
        # =================================================================
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name,
            input_example=input_example,
            signature=signature
        )
        
        print(f"  ✓ Model logged")
        print(f"  Run ID: {run.info.run_id}")
        print(f"  Registered: {registered_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": MODEL_NAME,
            "registered_as": registered_name,
            "metrics": metrics
        }

# COMMAND ----------

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 80)
    print(f"{MODEL_NAME.upper()} - TRAINING")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    fe = FeatureEngineeringClient()
    
    # Setup MLflow
    setup_mlflow(MODEL_NAME)
    
    # Create training set with Feature Engineering
    training_set, training_df = create_training_set_with_features(
        spark, fe, catalog, feature_schema
    )
    
    # Train model
    model, metrics, hyperparams, X_train = prepare_and_train(
        training_df, FEATURE_NAMES, LABEL_COLUMN
    )
    
    # Log model with Feature Engineering metadata
    result = log_model_with_feature_engineering(
        fe, model, training_set, X_train, metrics, hyperparams,
        catalog, feature_schema
    )
    
    print("\n" + "=" * 80)
    print(f"✓ {MODEL_NAME} TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()
```

## Feature Table Creation Pattern

```python
def create_feature_table(
    spark,
    df,
    catalog: str,
    schema: str,
    table_name: str,
    primary_keys: list,
    description: str
):
    """
    Create feature table with PRIMARY KEY constraint.
    
    Args:
        spark: SparkSession
        df: DataFrame with features
        catalog: Unity Catalog catalog name
        schema: Schema name
        table_name: Feature table name
        primary_keys: List of primary key columns
        description: Table description
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    print(f"Creating feature table: {full_table_name}")
    
    # 1. Filter NULL values in primary keys
    for pk in primary_keys:
        df = df.filter(F.col(pk).isNotNull())
    
    # 2. Drop existing table
    spark.sql(f"DROP TABLE IF EXISTS {full_table_name}")
    
    # 3. Create table with features
    (df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(full_table_name))
    
    # 4. Add table comment
    spark.sql(f"COMMENT ON TABLE {full_table_name} IS '{description}'")
    
    # 5. Add PRIMARY KEY constraint (REQUIRED for feature lookups)
    pk_cols = ", ".join(primary_keys)
    spark.sql(f"""
        ALTER TABLE {full_table_name}
        ADD CONSTRAINT pk_{table_name} PRIMARY KEY ({pk_cols})
    """)
    
    # 6. Refresh table
    spark.sql(f"REFRESH TABLE {full_table_name}")
    
    row_count = spark.table(full_table_name).count()
    print(f"  ✓ Created with {row_count:,} rows")
    
    return full_table_name
```

## Batch Inference Pattern

```python
def score_with_feature_engineering(
    fe: FeatureEngineeringClient,
    spark: SparkSession,
    catalog: str,
    schema: str,
    model_name: str,
    feature_table: str,
    id_columns: list,
    output_table: str
) -> int:
    """
    Score using fe.score_batch for automatic feature retrieval.
    """
    from mlflow import MlflowClient
    
    client = MlflowClient()
    full_model_name = f"{catalog}.{schema}.{model_name}"
    
    # Get latest model version
    versions = client.search_model_versions(f"name='{full_model_name}'")
    latest = max(versions, key=lambda v: int(v.version))
    model_uri = f"models:/{full_model_name}/{latest.version}"
    
    # Prepare scoring DataFrame with ONLY lookup keys
    scoring_df = (spark.table(f"{catalog}.{schema}.{feature_table}")
                  .select(*id_columns)
                  .distinct())
    
    # Score with automatic feature lookup
    predictions_df = fe.score_batch(
        model_uri=model_uri,
        df=scoring_df
    )
    
    # Add metadata
    predictions_df = (predictions_df
        .withColumn("model_version", F.lit(latest.version))
        .withColumn("model_name", F.lit(model_name))
        .withColumn("scored_at", F.current_timestamp()))
    
    # Save predictions
    full_output_table = f"{catalog}.{schema}.{output_table}"
    (predictions_df.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(full_output_table))
    
    return spark.table(full_output_table).count()
```

## Signature Validation Utility

```python
def validate_model_signature(catalog: str, schema: str, model_name: str):
    """
    Validate that model has complete signature.
    """
    from mlflow import MlflowClient
    
    client = MlflowClient()
    full_name = f"{catalog}.{schema}.{model_name}"
    
    versions = client.search_model_versions(f"name='{full_name}'")
    if not versions:
        print(f"❌ Model not found: {full_name}")
        return False
    
    latest = max(versions, key=lambda v: int(v.version))
    run = client.get_run(latest.run_id)
    
    # Get model artifact
    artifacts = client.list_artifacts(latest.run_id, "model")
    
    # Load model to check signature
    model_uri = f"models:/{full_name}/{latest.version}"
    model_info = mlflow.models.get_model_info(model_uri)
    
    if model_info.signature:
        print(f"✓ Model has signature")
        print(f"  Inputs: {model_info.signature.inputs}")
        print(f"  Outputs: {model_info.signature.outputs}")
        return True
    else:
        print(f"❌ Model missing signature!")
        return False

# Usage
validate_model_signature("catalog", "schema", "cost_anomaly_detector")
```

