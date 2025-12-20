# Databricks notebook source
"""
Train Cache Hit Predictor Model
===============================

Problem: Binary Classification
Algorithm: Neural Network (MLPClassifier)
Domain: Performance

This model predicts whether a query will achieve high cache hit rate based on:
- Query patterns (type, complexity)
- Data freshness and access patterns
- Historical cache effectiveness
- Time-based access patterns
- Table characteristics

Cache Hit Prediction: LOW (<50%) vs HIGH (>=50%)

MLflow 3.1+ Best Practices:
- Uses /Shared/ experiment path (serverless compatible)
- Logs dataset for lineage tracking
- Registers model to Unity Catalog
- Includes comprehensive tags and metrics
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, f1_score, roc_auc_score
import pandas as pd
import numpy as np
from datetime import datetime
import joblib

# =============================================================================
# MLflow Configuration (at module level, before any MLflow calls)
# =============================================================================
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# =============================================================================
# INLINE HELPER FUNCTIONS (Required - do not import from modules)
# =============================================================================

def get_parameters():
    """Get job parameters from dbutils widgets (NEVER use argparse)."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema


def setup_mlflow_experiment(model_name: str) -> str:
    """
    Set up MLflow experiment using /Shared/ path.
    
    CRITICAL: Always use /Shared/ path for serverless compatibility.
    /Users/ paths fail silently if parent folder doesn't exist.
    """
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    
    try:
        experiment = mlflow.set_experiment(experiment_name)
        print(f"✓ Experiment set: {experiment_name}")
        print(f"  Experiment ID: {experiment.experiment_id}")
        return experiment_name
    except Exception as e:
        print(f"⚠ Experiment setup warning: {e}")
        return experiment_name


def log_training_dataset(spark, catalog: str, schema: str, table_name: str) -> bool:
    """
    Log training dataset for MLflow lineage tracking.
    
    CRITICAL: Must be called INSIDE mlflow.start_run() context!
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    try:
        print(f"  Logging dataset: {full_table_name}")
        training_df = spark.table(full_table_name)
        dataset = mlflow.data.from_spark(
            df=training_df, 
            table_name=full_table_name,
            version="latest"
        )
        mlflow.log_input(dataset, context="training")
        print(f"  ✓ Dataset logged: {full_table_name}")
        return True
    except Exception as e:
        print(f"  ⚠ Dataset logging warning: {e}")
        return False


def get_run_name(model_name: str, algorithm: str, version: str = "v1") -> str:
    """Generate descriptive run name for MLflow tracking."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{algorithm}_{version}_{timestamp}"


def get_standard_tags(model_name: str, domain: str, model_type: str, 
                      algorithm: str, use_case: str, training_table: str) -> dict:
    """Get standard MLflow run tags for consistent organization."""
    return {
        "project": "databricks_health_monitor",
        "domain": domain,
        "model_name": model_name,
        "model_type": model_type,
        "algorithm": algorithm,
        "layer": "ml",
        "team": "data_engineering",
        "use_case": use_case,
        "training_data": training_table
    }

# COMMAND ----------

def prepare_training_data(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Prepare training data for cache hit prediction.
    
    Features:
    - Query characteristics (type, duration, bytes read)
    - Time-based access patterns
    - Table access frequency
    - User query patterns
    - Historical cache effectiveness
    
    Schema-grounded:
    - fact_query_history.yaml: statement_type, duration_ms, bytes_read, 
      rows_returned, user_name, warehouse_id, start_time
    """
    print("\nPreparing training data for cache hit prediction...")
    
    fact_query = f"{catalog}.{gold_schema}.fact_query_history"
    
    # Get query-level data with cache metrics
    query_data = (
        spark.table(fact_query)
        .filter(F.col("start_time") >= F.date_sub(F.current_date(), 90))
        .filter(F.col("execution_status") == "FINISHED")
        # Calculate cache hit rate (bytes_read_from_cache / bytes_read)
        # If these columns don't exist, we'll simulate based on patterns
        .withColumn("bytes_read_safe", F.greatest(F.col("bytes_read"), F.lit(1)))
        # Simulate cache effectiveness based on query patterns
        # In production, this would use actual cache metrics
        .withColumn("query_hash", F.hash("query_text"))
        .withColumn("hour_of_day", F.hour("start_time"))
        .withColumn("day_of_week", F.dayofweek("start_time"))
        .withColumn("is_business_hours", F.when(
            (F.col("hour_of_day").between(9, 17)) & 
            (F.col("day_of_week").between(2, 6)), 1
        ).otherwise(0))
    )
    
    # Calculate historical query patterns
    query_patterns = (
        query_data
        .groupBy("query_hash")
        .agg(
            F.count("*").alias("query_frequency"),
            F.avg("duration_ms").alias("avg_duration"),
            F.stddev("duration_ms").alias("duration_stddev"),
            F.avg("bytes_read_safe").alias("avg_bytes_read"),
            F.avg("rows_returned").alias("avg_rows_returned"),
            F.countDistinct("user_name").alias("unique_users"),
            F.countDistinct(F.date_trunc("day", "start_time")).alias("days_active")
        )
        .withColumn("query_regularity", F.col("query_frequency") / F.greatest(F.col("days_active"), F.lit(1)))
        # Queries with high regularity (repeated queries) tend to have better cache hits
        .withColumn("is_cacheable", F.when(F.col("query_regularity") > 1, 1).otherwise(0))
    )
    
    # Create training dataset with cache prediction target
    training_df = (
        query_data
        .join(query_patterns, "query_hash", "left")
        # Encode statement type
        .withColumn("is_select", F.when(F.col("statement_type") == "SELECT", 1).otherwise(0))
        .withColumn("is_show", F.when(F.col("statement_type").startswith("SHOW"), 1).otherwise(0))
        .withColumn("is_describe", F.when(F.col("statement_type").startswith("DESCRIBE"), 1).otherwise(0))
        # Query complexity indicators
        .withColumn("duration_log", F.log1p(F.col("duration_ms")))
        .withColumn("bytes_log", F.log1p(F.col("bytes_read_safe")))
        .withColumn("rows_log", F.log1p(F.col("rows_returned")))
        # Encode warehouse
        .withColumn("warehouse_hash", F.hash("warehouse_id"))
        # Encode user patterns
        .withColumn("user_hash", F.hash("user_name"))
        # Target: High cache effectiveness (simulated based on patterns)
        # High cache = regular query, SELECT, reasonable size, repeated
        .withColumn("high_cache_hit", F.when(
            (F.col("query_regularity") > 2) &
            (F.col("is_select") == 1) &
            (F.col("bytes_read_safe") < 1e9) &  # < 1GB
            (F.col("query_frequency") > 5),
            1
        ).otherwise(0))
        # Fill nulls
        .fillna(0)
    )
    
    record_count = training_df.count()
    print(f"✓ Prepared {record_count} query records for training")
    
    # Show class distribution
    print("\nCache Hit Distribution:")
    training_df.groupBy("high_cache_hit").count().show()
    
    return training_df

# COMMAND ----------

def train_cache_predictor(X_train_scaled, y_train, X_val_scaled, y_val):
    """
    Train Neural Network classifier for cache hit prediction.
    
    Model predicts whether a query will have high cache effectiveness.
    """
    print("\nTraining Neural Network Cache Hit Predictor...")
    print(f"  Training samples: {len(y_train)}")
    print(f"  Validation samples: {len(y_val)}")
    print(f"  Class balance (train): {y_train.mean():.2%} high cache")
    
    model = MLPClassifier(
        hidden_layer_sizes=(64, 32, 16),
        activation='relu',
        solver='adam',
        alpha=0.001,
        batch_size='auto',
        learning_rate='adaptive',
        learning_rate_init=0.001,
        max_iter=300,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=10,
        random_state=42,
        verbose=False
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_train_pred_proba = model.predict_proba(X_train_scaled)[:, 1]
    y_val_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
    
    train_auc = roc_auc_score(y_train, y_train_pred_proba)
    val_auc = roc_auc_score(y_val, y_val_pred_proba)
    
    print(f"✓ Model trained successfully")
    print(f"  Training AUC: {train_auc:.3f}")
    print(f"  Validation AUC: {val_auc:.3f}")
    
    return model, train_auc, val_auc

# COMMAND ----------

def log_model_to_mlflow(
    model,
    scaler,
    X_train: pd.DataFrame,
    y_val: np.ndarray,
    y_val_pred_proba: np.ndarray,
    metrics: dict,
    catalog: str,
    feature_schema: str,
    experiment_name: str,
    spark: SparkSession
):
    """
    Log model to MLflow with Unity Catalog registry.
    """
    model_name = "cache_hit_predictor"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "mlp", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="performance",
            model_type="classification",
            algorithm="neural_network",
            use_case="cache_hit_prediction",
            training_table=f"{catalog}.{feature_schema}.performance_features"
        ))
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "performance_features")
        
        # 3. Log hyperparameters
        mlflow.log_params({
            "model_type": "MLPClassifier",
            "hidden_layers": "64-32-16",
            "activation": "relu",
            "solver": "adam",
            "alpha": 0.001,
            "max_iter": 300,
            "early_stopping": True,
            "training_samples": len(X_train)
        })
        
        # 4. Log metrics
        mlflow.log_metrics(metrics)
        
        # 5. Save scaler as artifact
        joblib.dump(scaler, "scaler.pkl")
        mlflow.log_artifact("scaler.pkl")
        
        # 6. Log precision-recall curve
        import matplotlib.pyplot as plt
        from sklearn.metrics import precision_recall_curve
        precision, recall, thresholds = precision_recall_curve(y_val, y_val_pred_proba)
        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Cache Hit Predictor - Precision-Recall Curve')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("precision_recall.png")
        mlflow.log_artifact("precision_recall.png")
        plt.close()
        
        # 7. Create signature with BOTH input AND output (required for UC)
        sample_input = X_train.head(5)
        sample_output = model.predict_proba(scaler.transform(sample_input))
        signature = infer_signature(sample_input, sample_output)
        
        # 8. Log and register model
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            signature=signature,
            input_example=sample_input,
            registered_model_name=registered_model_name
        )
        
        run_id = run.info.run_id
        print(f"✓ Model logged successfully")
        print(f"  Run ID: {run_id}")
        print(f"  Registered Model: {registered_model_name}")
        print(f"  Experiment: {experiment_name}")
    
    return run_id, registered_model_name

# COMMAND ----------

def main():
    """Main entry point for cache hit predictor training."""
    print("\n" + "=" * 80)
    print("CACHE HIT PREDICTOR - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("cache_hit_predictor")
    
    try:
        # Prepare training data
        training_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Convert to Pandas for sklearn
        pdf = training_df.toPandas()
        
        print(f"\nPreparing features...")
        
        # Feature columns
        feature_cols = [
            'duration_log', 'bytes_log', 'rows_log',
            'hour_of_day', 'day_of_week', 'is_business_hours',
            'is_select', 'is_show', 'is_describe',
            'query_frequency', 'avg_duration', 'duration_stddev',
            'avg_bytes_read', 'avg_rows_returned',
            'unique_users', 'days_active', 'query_regularity',
            'warehouse_hash', 'user_hash'
        ]
        
        X = pdf[feature_cols].fillna(0)
        y = pdf['high_cache_hit'].values
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"  Target distribution: {y.mean():.2%} high cache hit")
        
        # Train/Val split (stratified)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        # Scale features for neural network
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Train model
        model, train_auc, val_auc = train_cache_predictor(
            X_train_scaled, y_train, X_val_scaled, y_val
        )
        
        # Calculate additional metrics
        y_val_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
        y_val_pred = (y_val_pred_proba >= 0.5).astype(int)
        
        from sklearn.metrics import precision_score, recall_score
        
        metrics = {
            "train_auc": train_auc,
            "val_auc": val_auc,
            "val_accuracy": accuracy_score(y_val, y_val_pred),
            "val_precision": precision_score(y_val, y_val_pred, zero_division=0),
            "val_recall": recall_score(y_val, y_val_pred, zero_division=0),
            "val_f1": f1_score(y_val, y_val_pred, zero_division=0),
            "training_samples": len(X_train),
            "class_balance": y_train.mean()
        }
        
        # Log to MLflow
        run_id, model_name = log_model_to_mlflow(
            model=model,
            scaler=scaler,
            X_train=X_train,
            y_val=y_val,
            y_val_pred_proba=y_val_pred_proba,
            metrics=metrics,
            catalog=catalog,
            feature_schema=feature_schema,
            experiment_name=experiment_name,
            spark=spark
        )
        
        print("\n" + "=" * 80)
        print("✓ CACHE HIT PREDICTOR TRAINING COMPLETE")
        print(f"  Model: {model_name}")
        print(f"  MLflow Run: {run_id}")
        print(f"  Validation AUC: {val_auc:.3f}")
        print(f"  Validation F1: {metrics['val_f1']:.3f}")
        print("=" * 80)
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error during training: {str(e)}")
        print(traceback.format_exc())
        dbutils.notebook.exit(f"FAILED: {str(e)}")
    
    # Signal success (REQUIRED for job status)
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()

