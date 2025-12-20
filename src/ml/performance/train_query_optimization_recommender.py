# Databricks notebook source
"""
Train Query Optimization Recommender Model
==========================================

Problem: Multi-Label Classification
Algorithm: Random Forest Classifier (One-vs-Rest)
Domain: Performance

This model recommends specific optimizations for slow queries based on:
- Query execution characteristics
- Resource consumption patterns
- Data access patterns
- Historical optimization outcomes

Optimization Categories (Multi-Label):
1. PARTITION_PRUNING - Add/improve partitioning
2. CACHING - Enable result caching
3. BROADCAST_JOIN - Use broadcast for small tables
4. PREDICATE_PUSHDOWN - Improve predicate ordering
5. COLUMN_PRUNING - Select only needed columns
6. CLUSTER_SIZING - Right-size compute resources

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
from sklearn.ensemble import RandomForestClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, hamming_loss
import pandas as pd
import numpy as np
from datetime import datetime

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

# Optimization labels
OPTIMIZATION_LABELS = [
    'needs_partition_pruning',
    'needs_caching',
    'needs_broadcast_join',
    'needs_predicate_pushdown',
    'needs_column_pruning',
    'needs_cluster_resize'
]

def prepare_training_data(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Prepare training data for query optimization recommendation.
    
    Features:
    - Query execution metrics (duration, bytes, rows)
    - Resource utilization indicators
    - Query patterns and complexity
    
    Labels (Multi-Label):
    - Simulated based on query characteristics
    - In production, would come from actual optimization outcomes
    
    Schema-grounded:
    - fact_query_history.yaml: duration_ms, bytes_read, bytes_written,
      rows_returned, spill_to_disk_bytes, statement_type
    """
    print("\nPreparing training data for query optimization recommendation...")
    
    fact_query = f"{catalog}.{gold_schema}.fact_query_history"
    
    # Get query-level data with performance indicators
    query_data = (
        spark.table(fact_query)
        .filter(F.col("start_time") >= F.date_sub(F.current_date(), 90))
        .filter(F.col("execution_status") == "FINISHED")
        .filter(F.col("statement_type") == "SELECT")
        # Safe division helpers
        .withColumn("bytes_read_safe", F.greatest(F.col("bytes_read"), F.lit(1)))
        .withColumn("duration_safe", F.greatest(F.col("duration_ms"), F.lit(1)))
        # Performance indicators
        .withColumn("bytes_per_ms", F.col("bytes_read_safe") / F.col("duration_safe"))
        .withColumn("rows_per_ms", F.col("rows_returned") / F.col("duration_safe"))
        # Spill indicator (if available, otherwise estimate)
        .withColumn("spill_bytes", F.coalesce(F.col("spill_to_disk_bytes"), F.lit(0)))
        .withColumn("has_spill", F.when(F.col("spill_bytes") > 0, 1).otherwise(0))
        # Size categorization
        .withColumn("is_large_scan", F.when(F.col("bytes_read_safe") > 1e10, 1).otherwise(0))  # >10GB
        .withColumn("is_slow_query", F.when(F.col("duration_ms") > 60000, 1).otherwise(0))  # >1min
        .withColumn("is_wide_result", F.when(F.col("rows_returned") > 1000000, 1).otherwise(0))  # >1M rows
        # Time features
        .withColumn("hour_of_day", F.hour("start_time"))
        .withColumn("is_peak_hours", F.when(F.col("hour_of_day").between(9, 17), 1).otherwise(0))
        # Log transforms
        .withColumn("duration_log", F.log1p(F.col("duration_ms")))
        .withColumn("bytes_log", F.log1p(F.col("bytes_read_safe")))
        .withColumn("rows_log", F.log1p(F.col("rows_returned")))
        .withColumn("spill_log", F.log1p(F.col("spill_bytes")))
    )
    
    # Create optimization labels based on heuristics
    # In production, these would come from actual optimization outcomes
    training_df = (
        query_data
        # PARTITION_PRUNING: Large scans with high duration
        .withColumn("needs_partition_pruning", F.when(
            (F.col("is_large_scan") == 1) & (F.col("duration_ms") > 30000), 1
        ).otherwise(0))
        # CACHING: Frequently run queries with moderate size
        .withColumn("needs_caching", F.when(
            (F.col("bytes_read_safe") < 1e9) & (F.col("duration_ms") > 5000), 1
        ).otherwise(0))
        # BROADCAST_JOIN: Small table joins (detected by row/byte ratio)
        .withColumn("needs_broadcast_join", F.when(
            (F.col("rows_returned") > 0) &
            (F.col("bytes_read_safe") / F.col("rows_returned") > 10000), 1  # Wide rows = potential join issues
        ).otherwise(0))
        # PREDICATE_PUSHDOWN: Large scans with small results
        .withColumn("needs_predicate_pushdown", F.when(
            (F.col("is_large_scan") == 1) & 
            (F.col("rows_returned") < 10000), 1  # Large scan, small result = late filtering
        ).otherwise(0))
        # COLUMN_PRUNING: High bytes per row
        .withColumn("needs_column_pruning", F.when(
            (F.col("bytes_read_safe") / F.greatest(F.col("rows_returned"), F.lit(1)) > 50000), 1
        ).otherwise(0))
        # CLUSTER_RESIZE: Spill + slow
        .withColumn("needs_cluster_resize", F.when(
            (F.col("has_spill") == 1) | 
            ((F.col("is_slow_query") == 1) & (F.col("is_large_scan") == 1)), 1
        ).otherwise(0))
        # Hash for grouping
        .withColumn("warehouse_hash", F.hash("warehouse_id"))
        .withColumn("user_hash", F.hash("user_name"))
    )
    
    record_count = training_df.count()
    print(f"✓ Prepared {record_count} query records for training")
    
    # Show optimization distribution
    print("\nOptimization Needs Distribution:")
    for label in OPTIMIZATION_LABELS:
        positive_count = training_df.filter(F.col(label) == 1).count()
        print(f"  {label}: {positive_count} ({positive_count/record_count*100:.1f}%)")
    
    return training_df

# COMMAND ----------

def train_optimization_recommender(X_train, y_train, X_val, y_val):
    """
    Train Multi-Label Random Forest classifier for optimization recommendation.
    
    Uses OneVsRest strategy for multi-label classification.
    """
    print("\nTraining Multi-Label Optimization Recommender...")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"  Labels: {y_train.shape[1]}")
    
    base_classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    model = OneVsRestClassifier(base_classifier)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_train_pred = model.predict(X_train)
    y_val_pred = model.predict(X_val)
    
    train_f1 = f1_score(y_train, y_train_pred, average='samples', zero_division=0)
    val_f1 = f1_score(y_val, y_val_pred, average='samples', zero_division=0)
    val_hamming = hamming_loss(y_val, y_val_pred)
    
    print(f"✓ Model trained successfully")
    print(f"  Training F1 (samples): {train_f1:.3f}")
    print(f"  Validation F1 (samples): {val_f1:.3f}")
    print(f"  Validation Hamming Loss: {val_hamming:.3f}")
    
    return model, train_f1, val_f1, val_hamming

# COMMAND ----------

def log_model_to_mlflow(
    model,
    X_train: pd.DataFrame,
    y_val: np.ndarray,
    y_val_pred: np.ndarray,
    metrics: dict,
    catalog: str,
    feature_schema: str,
    experiment_name: str,
    spark: SparkSession
):
    """
    Log model to MLflow with Unity Catalog registry.
    """
    model_name = "query_optimization_recommender"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "random_forest_ovr", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="performance",
            model_type="multi_label_classification",
            algorithm="random_forest_ovr",
            use_case="query_optimization_recommendation",
            training_table=f"{catalog}.{feature_schema}.performance_features"
        ))
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "performance_features")
        
        # 3. Log hyperparameters
        mlflow.log_params({
            "model_type": "OneVsRestClassifier(RandomForest)",
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 10,
            "class_weight": "balanced",
            "random_state": 42,
            "training_samples": len(X_train),
            "n_labels": len(OPTIMIZATION_LABELS)
        })
        
        # 4. Log metrics
        mlflow.log_metrics(metrics)
        
        # 5. Log per-label metrics
        import matplotlib.pyplot as plt
        
        per_label_f1 = f1_score(y_val, y_val_pred, average=None, zero_division=0)
        for i, label in enumerate(OPTIMIZATION_LABELS):
            mlflow.log_metric(f"{label}_f1", per_label_f1[i])
        
        # Plot per-label performance
        plt.figure(figsize=(10, 6))
        plt.barh(OPTIMIZATION_LABELS, per_label_f1)
        plt.xlabel('F1 Score')
        plt.title('Per-Label F1 Scores - Query Optimization Recommender')
        plt.tight_layout()
        plt.savefig("per_label_f1.png")
        mlflow.log_artifact("per_label_f1.png")
        plt.close()
        
        # 6. Log label mapping
        label_mapping = {i: label for i, label in enumerate(OPTIMIZATION_LABELS)}
        mlflow.log_dict(label_mapping, "label_mapping.json")
        
        # 7. Create signature with BOTH input AND output (required for UC)
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
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
    """Main entry point for query optimization recommender training."""
    print("\n" + "=" * 80)
    print("QUERY OPTIMIZATION RECOMMENDER - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("query_optimization_recommender")
    
    try:
        # Prepare training data
        training_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Convert to Pandas for sklearn
        pdf = training_df.toPandas()
        
        print(f"\nPreparing features...")
        
        # Feature columns
        feature_cols = [
            'duration_log', 'bytes_log', 'rows_log', 'spill_log',
            'bytes_per_ms', 'rows_per_ms',
            'has_spill', 'is_large_scan', 'is_slow_query', 'is_wide_result',
            'hour_of_day', 'is_peak_hours',
            'warehouse_hash', 'user_hash'
        ]
        
        X = pdf[feature_cols].fillna(0)
        y = pdf[OPTIMIZATION_LABELS].values
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"✓ Label matrix shape: {y.shape}")
        
        # Train/Val split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model, train_f1, val_f1, val_hamming = train_optimization_recommender(
            X_train, y_train, X_val, y_val
        )
        
        # Calculate additional metrics
        y_val_pred = model.predict(X_val)
        
        metrics = {
            "train_f1_samples": train_f1,
            "val_f1_samples": val_f1,
            "val_f1_micro": f1_score(y_val, y_val_pred, average='micro', zero_division=0),
            "val_f1_macro": f1_score(y_val, y_val_pred, average='macro', zero_division=0),
            "val_hamming_loss": val_hamming,
            "training_samples": len(X_train),
            "n_labels": len(OPTIMIZATION_LABELS)
        }
        
        # Log to MLflow
        run_id, model_name = log_model_to_mlflow(
            model=model,
            X_train=X_train,
            y_val=y_val,
            y_val_pred=y_val_pred,
            metrics=metrics,
            catalog=catalog,
            feature_schema=feature_schema,
            experiment_name=experiment_name,
            spark=spark
        )
        
        print("\n" + "=" * 80)
        print("✓ QUERY OPTIMIZATION RECOMMENDER TRAINING COMPLETE")
        print(f"  Model: {model_name}")
        print(f"  MLflow Run: {run_id}")
        print(f"  Validation F1 (samples): {val_f1:.3f}")
        print(f"  Validation Hamming Loss: {val_hamming:.3f}")
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

