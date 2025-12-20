# Databricks notebook source
"""
Train Retry Success Predictor Model
===================================

Problem: Binary Classification
Algorithm: XGBoost
Domain: Reliability

This model predicts whether a failed job will succeed on retry based on:
- Error type and termination code
- Historical retry patterns
- Resource availability patterns
- Time-based factors (day of week, hour)

Use case: Intelligent auto-retry with confidence scoring

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
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
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
    
    CRITICAL: Always use /Shared/ path for serverless compatible.
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
    Prepare training data for retry success prediction.
    
    Features from fact_job_run_timeline:
    - Failed jobs and their retry patterns
    - Termination codes and error types
    - Resource and timing patterns
    - Historical retry success rates
    
    Target: Whether next retry succeeded (binary)
    
    Schema-grounded:
    - fact_job_run_timeline.yaml: result_state, termination_code, run_id, 
      run_start_timestamp, run_duration_seconds, job_id
    """
    print("\nPreparing training data for retry success prediction...")
    
    fact_job = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    
    # Get failed jobs
    failed_jobs = (
        spark.table(fact_job)
        .filter(F.col("result_state") == "FAILED")
        .filter(F.col("run_start_timestamp") >= F.date_sub(F.current_date(), 90))
        .select(
            "run_id",
            "job_id",
            "run_start_timestamp",
            "termination_code",
            "run_duration_seconds",
            "cluster_id",
            # Extract time features
            F.hour("run_start_timestamp").alias("hour_of_day"),
            F.dayofweek("run_start_timestamp").alias("day_of_week"),
            F.when(F.dayofweek("run_start_timestamp").isin(1, 7), 1).otherwise(0).alias("is_weekend")
        )
        .withColumn("row_num", F.row_number().over(
            Window.partitionBy("job_id").orderBy("run_start_timestamp")
        ))
    )
    
    # Get next run for each failed job (within 24 hours)
    retry_outcomes = (
        failed_jobs.alias("failed")
        .join(
            spark.table(fact_job).alias("retry")
            .select(
                F.col("job_id").alias("retry_job_id"),
                F.col("run_start_timestamp").alias("retry_timestamp"),
                F.col("result_state").alias("retry_result")
            ),
            on=[
                F.col("failed.job_id") == F.col("retry.retry_job_id"),
                F.col("retry.retry_timestamp") > F.col("failed.run_start_timestamp"),
                F.col("retry.retry_timestamp") <= F.col("failed.run_start_timestamp") + F.expr("INTERVAL 24 HOURS")
            ],
            how="inner"
        )
        # Get first retry only
        .withColumn("retry_rank", F.row_number().over(
            Window.partitionBy("failed.run_id").orderBy("retry.retry_timestamp")
        ))
        .filter(F.col("retry_rank") == 1)
        .select(
            F.col("failed.run_id").alias("failed_run_id"),
            F.col("failed.job_id").alias("job_id"),
            F.col("failed.termination_code").alias("error_code"),
            F.col("failed.run_duration_seconds").alias("failed_duration_sec"),
            F.col("failed.hour_of_day"),
            F.col("failed.day_of_week"),
            F.col("failed.is_weekend"),
            F.col("failed.row_num").alias("failure_count"),
            F.col("failed.cluster_id"),
            # Time to retry
            (F.col("retry.retry_timestamp").cast("long") - F.col("failed.run_start_timestamp").cast("long")).alias("time_to_retry_sec"),
            # Target
            F.when(F.col("retry.retry_result") == "SUCCESS", 1).otherwise(0).alias("retry_succeeded")
        )
    )
    
    # Add historical success rate per job
    job_success_rates = (
        spark.table(fact_job)
        .filter(F.col("run_start_timestamp") < F.date_sub(F.current_date(), 7))
        .groupBy("job_id")
        .agg(
            (F.sum(F.when(F.col("result_state") == "SUCCESS", 1).otherwise(0)) / F.count("*")).alias("historical_success_rate")
        )
    )
    
    # Add historical success rate per error code
    error_retry_rates = (
        retry_outcomes
        .groupBy("error_code")
        .agg(
            (F.sum("retry_succeeded") / F.count("*")).alias("error_code_retry_success_rate")
        )
    )
    
    # Join enrichments
    training_df = (
        retry_outcomes
        .join(job_success_rates, "job_id", "left")
        .join(error_retry_rates, "error_code", "left")
        # Fill nulls
        .fillna(0.5, subset=["historical_success_rate", "error_code_retry_success_rate"])
        # Encode categorical
        .withColumn("error_code_hash", F.hash("error_code"))
        .withColumn("cluster_hash", F.hash("cluster_id"))
        # Convert time to retry to minutes
        .withColumn("time_to_retry_min", F.col("time_to_retry_sec") / 60.0)
    )
    
    record_count = training_df.count()
    print(f"✓ Prepared {record_count} failed job records with retry outcomes")
    
    # Show class balance
    training_df.groupBy("retry_succeeded").count().show()
    
    return training_df

# COMMAND ----------

def train_retry_predictor(X_train, y_train, X_val, y_val):
    """
    Train XGBoost classifier for retry success prediction.
    
    Model predicts whether a failed job will succeed on retry.
    """
    print("\nTraining XGBoost Retry Success Predictor...")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"  Class balance (train): {y_train.mean():.2%} success rate")
    
    # Calculate scale_pos_weight for imbalanced data
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    
    model = XGBClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_train_pred_proba = model.predict_proba(X_train)[:, 1]
    y_val_pred_proba = model.predict_proba(X_val)[:, 1]
    
    train_auc = roc_auc_score(y_train, y_train_pred_proba)
    val_auc = roc_auc_score(y_val, y_val_pred_proba)
    
    print(f"✓ Model trained successfully")
    print(f"  Training AUC: {train_auc:.3f}")
    print(f"  Validation AUC: {val_auc:.3f}")
    
    return model, train_auc, val_auc

# COMMAND ----------

def log_model_to_mlflow(
    model,
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
    model_name = "retry_success_predictor"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "xgboost", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="reliability",
            model_type="classification",
            algorithm="xgboost",
            use_case="retry_success_prediction",
            training_table=f"{catalog}.{feature_schema}.reliability_features"
        ))
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "reliability_features")
        
        # 3. Log hyperparameters
        mlflow.log_params({
            "model_type": "XGBClassifier",
            "n_estimators": model.n_estimators,
            "learning_rate": model.learning_rate,
            "max_depth": model.max_depth,
            "min_child_weight": model.min_child_weight,
            "subsample": model.subsample,
            "colsample_bytree": model.colsample_bytree,
            "random_state": 42,
            "training_samples": len(X_train)
        })
        
        # 4. Log metrics
        mlflow.log_metrics(metrics)
        
        # 5. Log feature importance
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        plt.barh(feature_importance['feature'].head(10), feature_importance['importance'].head(10))
        plt.xlabel('Importance')
        plt.title('Top 10 Features - Retry Success Predictor')
        plt.tight_layout()
        plt.savefig("feature_importance.png")
        mlflow.log_artifact("feature_importance.png")
        plt.close()
        
        # 6. Log precision-recall curve
        precision, recall, thresholds = precision_recall_curve(y_val, y_val_pred_proba)
        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("precision_recall.png")
        mlflow.log_artifact("precision_recall.png")
        plt.close()
        
        # 7. Create signature with BOTH input AND output (required for UC)
        sample_input = X_train.head(5)
        sample_output = model.predict_proba(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # 8. Log and register model
        mlflow.xgboost.log_model(
            xgb_model=model,
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
    """Main entry point for retry success predictor training."""
    print("\n" + "=" * 80)
    print("RETRY SUCCESS PREDICTOR - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("retry_success_predictor")
    
    try:
        # Prepare training data
        training_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Convert to Pandas for sklearn
        pdf = training_df.toPandas()
        
        print(f"\nPreparing features...")
        
        # Feature columns
        feature_cols = [
            'failed_duration_sec', 'hour_of_day', 'day_of_week', 'is_weekend',
            'failure_count', 'time_to_retry_min', 'historical_success_rate',
            'error_code_retry_success_rate', 'error_code_hash', 'cluster_hash'
        ]
        
        X = pdf[feature_cols].fillna(0)
        y = pdf['retry_succeeded'].values
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"  Target distribution: {y.mean():.2%} success rate")
        
        # Train/Val split (stratified for balanced classes)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        # Train model
        model, train_auc, val_auc = train_retry_predictor(
            X_train, y_train, X_val, y_val
        )
        
        # Calculate additional metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        y_val_pred_proba = model.predict_proba(X_val)[:, 1]
        y_val_pred = (y_val_pred_proba >= 0.5).astype(int)
        
        metrics = {
            "train_auc": train_auc,
            "val_auc": val_auc,
            "val_accuracy": accuracy_score(y_val, y_val_pred),
            "val_precision": precision_score(y_val, y_val_pred),
            "val_recall": recall_score(y_val, y_val_pred),
            "val_f1": f1_score(y_val, y_val_pred),
            "training_samples": len(X_train),
            "class_balance": y_train.mean()
        }
        
        # Log to MLflow
        run_id, model_name = log_model_to_mlflow(
            model=model,
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
        print("✓ RETRY SUCCESS PREDICTOR TRAINING COMPLETE")
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

