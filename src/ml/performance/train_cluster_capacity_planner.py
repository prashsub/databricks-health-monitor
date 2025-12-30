# Databricks notebook source
"""
Train Cluster Capacity Planner Model
====================================

Problem: Regression (Time Series)
Algorithm: Gradient Boosting
Domain: Performance

This model predicts optimal cluster capacity (nodes, cores, memory) based on:
- Job runtime characteristics
- Data volume trends
- Historical cluster utilization
- Scheduled job patterns

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
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
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

def prepare_training_data(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Prepare training data for cluster capacity planning.
    
    Features from fact_node_timeline and fact_job_run_timeline:
    - Historical job runtime
    - Cluster resource utilization
    - Job concurrency patterns
    - Data volume processed
    
    Target: Optimal node count for future capacity
    
    Schema-grounded:
    - fact_node_timeline.yaml: start_time, cpu_utilization_percent, 
      memory_utilization_percent, cluster_id
    - fact_job_run_timeline.yaml: run_duration_seconds, rows_produced, 
      task_execution_time_ms
    """
    print("\nPreparing training data for cluster capacity planning...")
    
    fact_node = f"{catalog}.{gold_schema}.fact_node_timeline"
    fact_job = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    
    # Aggregate cluster utilization by cluster and day
    cluster_metrics = (
        spark.table(fact_node)
        .filter(F.col("start_time") >= F.date_sub(F.current_date(), 90))
        .groupBy("cluster_id", F.date_trunc("day", "start_time").alias("usage_date"))
        .agg(
            F.count("*").alias("node_hours"),
            F.avg("cpu_utilization_percent").alias("avg_cpu_util"),
            F.max("cpu_utilization_percent").alias("peak_cpu_util"),
            F.avg("memory_utilization_percent").alias("avg_memory_util"),
            F.max("memory_utilization_percent").alias("peak_memory_util"),
            F.countDistinct("node_id").alias("num_nodes_used")
        )
    )
    
    # Aggregate job metrics by cluster
    # Note: compute_ids is an array, we need to explode it to get cluster_id
    job_metrics = (
        spark.table(fact_job)
        .filter(F.col("period_start_time").isNotNull())
        .withColumn("cluster_id", F.explode_outer(F.col("compute_ids")))
        .filter(F.col("cluster_id").isNotNull())
        .groupBy("cluster_id", F.date_trunc("day", "period_start_time").alias("usage_date"))
        .agg(
            F.count("*").alias("jobs_run"),
            F.avg("run_duration_seconds").alias("avg_job_duration_sec"),
            F.max("run_duration_seconds").alias("max_job_duration_sec"),
            # Concurrent jobs metric
            F.countDistinct("run_id").alias("max_concurrent_jobs")
        )
    )
    
    # Join cluster and job metrics
    training_df = (
        cluster_metrics
        .join(job_metrics, ["cluster_id", "usage_date"], "inner")
        # Add temporal features
        .withColumn("day_of_week", F.dayofweek("usage_date"))
        .withColumn("is_weekend", F.when(F.col("day_of_week").isin(1, 7), 1).otherwise(0))
        # Efficiency metrics
        .withColumn("cpu_efficiency", F.col("avg_cpu_util") / F.greatest(F.col("peak_cpu_util"), F.lit(1)))
        .withColumn("memory_efficiency", F.col("avg_memory_util") / F.greatest(F.col("peak_memory_util"), F.lit(1)))
        # Workload intensity
        .withColumn("jobs_per_node_hour", F.col("jobs_run") / F.greatest(F.col("node_hours"), F.lit(1)))
        # .withColumn("rows_per_node_hour", F.col("total_rows_processed") / F.greatest(F.col("node_hours"), F.lit(1)))  # Column not in Gold schema
        # Lag features (previous day capacity)
        .withColumn("prev_day_nodes", F.lag("num_nodes_used", 1).over(
            Window.partitionBy("cluster_id").orderBy("usage_date")
        ))
        .withColumn("prev_day_peak_cpu", F.lag("peak_cpu_util", 1).over(
            Window.partitionBy("cluster_id").orderBy("usage_date")
        ))
        # Fill nulls
        .fillna(0, subset=["prev_day_nodes", "prev_day_peak_cpu"])
        # Drop first record per cluster (no lag available)
        .filter(F.col("prev_day_nodes") > 0)
    )
    
    record_count = training_df.count()
    print(f"✓ Prepared {record_count} cluster-day records for training")
    
    return training_df

# COMMAND ----------

def train_capacity_planner(X_train, y_train, X_val, y_val):
    """
    Train Gradient Boosting regressor for capacity planning.
    
    Model predicts optimal node count based on job and utilization patterns.
    """
    print("\nTraining Gradient Boosting Capacity Planner...")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        min_samples_split=10,
        min_samples_leaf=5,
        subsample=0.8,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_train_pred = model.predict(X_train)
    y_val_pred = model.predict(X_val)
    
    train_mae = mean_absolute_error(y_train, y_train_pred)
    val_mae = mean_absolute_error(y_val, y_val_pred)
    val_r2 = r2_score(y_val, y_val_pred)
    
    print(f"✓ Model trained successfully")
    print(f"  Training MAE: {train_mae:.2f} nodes")
    print(f"  Validation MAE: {val_mae:.2f} nodes")
    print(f"  Validation R²: {val_r2:.3f}")
    
    return model, train_mae, val_mae, val_r2

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
    model_name = "cluster_capacity_planner"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "gradient_boosting", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="performance",
            model_type="regression",
            algorithm="gradient_boosting",
            use_case="cluster_capacity_planning",
            training_table=f"{catalog}.{feature_schema}.performance_features"
        ))
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "performance_features")
        
        # 3. Log hyperparameters
        mlflow.log_params({
            "model_type": "GradientBoostingRegressor",
            "n_estimators": model.n_estimators,
            "learning_rate": model.learning_rate,
            "max_depth": model.max_depth,
            "min_samples_split": model.min_samples_split,
            "subsample": model.subsample,
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
        plt.title('Top 10 Features - Cluster Capacity Planner')
        plt.tight_layout()
        plt.savefig("feature_importance.png")
        mlflow.log_artifact("feature_importance.png")
        plt.close()
        
        # 6. Create signature with BOTH input AND output (required for UC)
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # 7. Log and register model
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
    """Main entry point for cluster capacity planner training."""
    print("\n" + "=" * 80)
    print("CLUSTER CAPACITY PLANNER - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("cluster_capacity_planner")
    
    try:
        # Prepare training data
        training_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Convert to Pandas for sklearn
        pdf = training_df.toPandas()
        
        print(f"\nPreparing features...")
        
        # Feature columns
        feature_cols = [
            'node_hours', 'avg_cpu_util', 'peak_cpu_util', 'avg_memory_util', 'peak_memory_util',
            'jobs_run', 'avg_job_duration_sec', 'max_job_duration_sec',
            'max_concurrent_jobs', 'day_of_week', 'is_weekend',
            'cpu_efficiency', 'memory_efficiency', 'jobs_per_node_hour',
            'prev_day_nodes', 'prev_day_peak_cpu'
        ]
        
        X = pdf[feature_cols].fillna(0)
        y = pdf['num_nodes_used'].values
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"  Target range: {y.min():.1f} - {y.max():.1f} nodes")
        print(f"  Target mean: {y.mean():.1f} nodes")
        
        # Train/Val split (time-based split would be better but we use random for simplicity)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model, train_mae, val_mae, val_r2 = train_capacity_planner(
            X_train, y_train, X_val, y_val
        )
        
        # Calculate additional metrics
        y_val_pred = model.predict(X_val)
        val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
        
        # Within ±1 node accuracy
        within_1_node = np.mean(np.abs(y_val - y_val_pred) <= 1)
        
        metrics = {
            "train_mae": train_mae,
            "val_mae": val_mae,
            "val_rmse": val_rmse,
            "val_r2": val_r2,
            "within_1_node_accuracy": within_1_node,
            "training_samples": len(X_train)
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
        print("✓ CLUSTER CAPACITY PLANNER TRAINING COMPLETE")
        print(f"  Model: {model_name}")
        print(f"  MLflow Run: {run_id}")
        print(f"  Validation MAE: {val_mae:.2f} nodes")
        print(f"  Validation R²: {val_r2:.3f}")
        print(f"  Within ±1 Node: {within_1_node:.1%}")
        print("=" * 80)
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error during training: {str(e)}")
        print(traceback.format_exc())
        raise  # Re-raise to fail the job
    
    # Exit with comprehensive JSON summary
    import json
    hyperparams = {'n_estimators': 100, 'max_depth': 5, 'learning_rate': 0.1}
    exit_summary = json.dumps({
        "status": "SUCCESS",
        "model": "cluster_capacity_planner",
        "registered_as": model_name,
        "run_id": run_id,
        "algorithm": "GradientBoostingRegressor",
        "hyperparameters": hyperparams,
        "metrics": {k: round(v, 4) if isinstance(v, float) else v for k, v in metrics.items()}
    })
    dbutils.notebook.exit(exit_summary)

# COMMAND ----------

if __name__ == "__main__":
    main()

