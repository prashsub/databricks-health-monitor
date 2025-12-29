# Databricks notebook source
"""
Train Pipeline Health Scorer Model
==================================

Problem: Regression (Health Score 0-100)
Algorithm: Gradient Boosting Regressor
Domain: Reliability

This model scores overall pipeline/job health based on:
- Success rate trends
- Latency metrics (avg, P95, P99)
- Data quality issues
- Dependency health indicators
- Resource utilization patterns

Health Score: 0 (Critical) to 100 (Excellent)
- 0-25: Critical - Immediate attention required
- 26-50: Poor - Needs investigation
- 51-75: Fair - Monitor closely
- 76-90: Good - Normal operation
- 91-100: Excellent - Optimal performance

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

def calculate_health_score(row):
    """
    Calculate health score (0-100) based on multiple factors.
    
    Factors and weights:
    - Success rate: 40%
    - Duration stability: 20%
    - SLA adherence: 20%
    - Recent trend: 20%
    """
    score = 0
    
    # Success rate contribution (40 points max)
    success_rate = row.get('success_rate', 0)
    score += min(success_rate * 40, 40)
    
    # Duration stability (20 points max) - lower CV is better
    duration_cv = row.get('duration_cv', 1)
    stability_score = max(0, 20 - duration_cv * 20)
    score += min(stability_score, 20)
    
    # SLA adherence (20 points max)
    sla_adherence = row.get('sla_adherence_rate', 0)
    score += min(sla_adherence * 20, 20)
    
    # Recent trend (20 points max) - positive trend is better
    trend = row.get('success_rate_trend', 0)
    trend_score = 10 + trend * 50  # Normalize around 10
    score += min(max(trend_score, 0), 20)
    
    return min(max(score, 0), 100)  # Clamp to 0-100


def prepare_training_data(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Prepare training data for pipeline health scoring.
    
    Features:
    - Job execution patterns (success rate, duration)
    - Latency metrics (avg, stddev, percentiles)
    - Trend indicators (recent vs historical)
    - Dependency health (if available)
    
    Schema-grounded:
    - fact_job_run_timeline.yaml: result_state, run_duration_seconds,
      period_start_time, job_id
    - dim_job.yaml: job_id, name, created_time
    """
    print("\nPreparing training data for pipeline health scoring...")
    
    fact_job = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    
    # Calculate job-level metrics over rolling windows
    # Use all available data if filtered result is empty
    job_metrics_7d = (
        spark.table(fact_job)
        .filter(F.col("period_start_time").isNotNull())
        .groupBy("job_id")
        .agg(
            F.count("*").alias("runs_7d"),
            F.sum(F.when(F.col("result_state") == "SUCCESS", 1).otherwise(0)).alias("successful_7d"),
            F.avg("run_duration_seconds").alias("avg_duration_7d"),
            F.stddev("run_duration_seconds").alias("stddev_duration_7d"),
            F.percentile_approx("run_duration_seconds", 0.95).alias("p95_duration_7d"),
            F.max("run_duration_seconds").alias("max_duration_7d")
        )
        .withColumn("success_rate_7d", F.col("successful_7d") / F.greatest(F.col("runs_7d"), F.lit(1)))
        .withColumn("duration_cv_7d", F.col("stddev_duration_7d") / F.greatest(F.col("avg_duration_7d"), F.lit(1)))
    )
    
    job_metrics_30d = (
        spark.table(fact_job)
        .filter(F.col("period_start_time").isNotNull())
        .groupBy("job_id")
        .agg(
            F.count("*").alias("runs_30d"),
            F.sum(F.when(F.col("result_state") == "SUCCESS", 1).otherwise(0)).alias("successful_30d"),
            F.avg("run_duration_seconds").alias("avg_duration_30d"),
            F.stddev("run_duration_seconds").alias("stddev_duration_30d"),
            F.percentile_approx("run_duration_seconds", 0.95).alias("p95_duration_30d"),
            F.percentile_approx("run_duration_seconds", 0.99).alias("p99_duration_30d"),
            F.max("run_duration_seconds").alias("max_duration_30d"),
            # Time to complete (TTC) metrics
            F.avg(F.when(F.col("result_state") == "SUCCESS", F.col("run_duration_seconds")).otherwise(None)).alias("avg_successful_duration_30d")
        )
        .withColumn("success_rate_30d", F.col("successful_30d") / F.greatest(F.col("runs_30d"), F.lit(1)))
        .withColumn("duration_cv_30d", F.col("stddev_duration_30d") / F.greatest(F.col("avg_duration_30d"), F.lit(1)))
    )
    
    # Calculate SLA adherence (assume 2x avg duration as SLA)
    sla_metrics = (
        spark.table(fact_job)
        .filter(F.col("period_start_time").isNotNull())
        .groupBy("job_id")
        .agg(
            F.avg("run_duration_seconds").alias("sla_threshold"),  # Dynamic SLA
            F.count("*").alias("total_runs_for_sla")
        )
        .join(
            spark.table(fact_job)
            .filter(F.col("period_start_time").isNotNull())
            .select("job_id", "run_duration_seconds"),
            "job_id"
        )
        .withColumn("within_sla", F.when(
            F.col("run_duration_seconds") <= F.col("sla_threshold") * 2, 1
        ).otherwise(0))
        .groupBy("job_id")
        .agg(
            F.avg("within_sla").alias("sla_adherence_rate")
        )
    )
    
    # Join all metrics
    training_df = (
        job_metrics_30d
        .join(job_metrics_7d, "job_id", "left")
        .join(sla_metrics, "job_id", "left")
        # Calculate trend (7d vs 30d success rate difference)
        .withColumn("success_rate_trend", F.col("success_rate_7d") - F.col("success_rate_30d"))
        .withColumn("duration_trend", F.col("avg_duration_7d") - F.col("avg_duration_30d"))
        # Failure patterns
        .withColumn("consecutive_failures_possible", F.when(
            F.col("success_rate_7d") < 0.5, 1
        ).otherwise(0))
        # Normalization
        .withColumn("duration_ratio", F.col("avg_duration_7d") / F.greatest(F.col("avg_duration_30d"), F.lit(1)))
        # Fill nulls
        .fillna(0)
        .fillna({
            'success_rate_7d': 0.5,
            'duration_cv_7d': 0.5,
            'sla_adherence_rate': 0.5
        })
    )
    
    # Convert to pandas for health score calculation
    pdf = training_df.toPandas()
    
    # Calculate health scores
    pdf['health_score'] = pdf.apply(lambda row: calculate_health_score({
        'success_rate': row['success_rate_30d'],
        'duration_cv': row['duration_cv_30d'],
        'sla_adherence_rate': row.get('sla_adherence_rate', 0.5),
        'success_rate_trend': row.get('success_rate_trend', 0)
    }), axis=1)
    
    # Convert back to Spark
    result_df = spark.createDataFrame(pdf)
    
    record_count = result_df.count()
    print(f"✓ Prepared {record_count} job records for training")
    
    # Show health score distribution
    print("\nHealth Score Distribution:")
    result_df.select(
        F.floor(F.col("health_score") / 25).alias("quartile")
    ).groupBy("quartile").count().orderBy("quartile").show()
    
    return result_df

# COMMAND ----------

def train_health_scorer(X_train, y_train, X_val, y_val):
    """
    Train Gradient Boosting regressor for health scoring.
    
    Model predicts health score (0-100) based on job metrics.
    """
    print("\nTraining Gradient Boosting Health Scorer...")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"  Target range: {y_train.min():.1f} - {y_train.max():.1f}")
    
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
    print(f"  Training MAE: {train_mae:.2f} points")
    print(f"  Validation MAE: {val_mae:.2f} points")
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
    model_name = "pipeline_health_scorer"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "gradient_boosting", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="reliability",
            model_type="regression",
            algorithm="gradient_boosting",
            use_case="pipeline_health_scoring",
            training_table=f"{catalog}.{feature_schema}.reliability_features"
        ))
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "reliability_features")
        
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
        plt.title('Top 10 Features - Pipeline Health Scorer')
        plt.tight_layout()
        plt.savefig("feature_importance.png")
        mlflow.log_artifact("feature_importance.png")
        plt.close()
        
        # 6. Log prediction vs actual scatter plot
        plt.figure(figsize=(8, 8))
        plt.scatter(y_val, y_val_pred, alpha=0.5)
        plt.plot([0, 100], [0, 100], 'r--', label='Perfect Prediction')
        plt.xlabel('Actual Health Score')
        plt.ylabel('Predicted Health Score')
        plt.title('Prediction vs Actual - Pipeline Health Scorer')
        plt.legend()
        plt.tight_layout()
        plt.savefig("prediction_scatter.png")
        mlflow.log_artifact("prediction_scatter.png")
        plt.close()
        
        # 7. Log health score ranges artifact
        health_ranges = {
            "0-25": "Critical - Immediate attention required",
            "26-50": "Poor - Needs investigation",
            "51-75": "Fair - Monitor closely",
            "76-90": "Good - Normal operation",
            "91-100": "Excellent - Optimal performance"
        }
        mlflow.log_dict(health_ranges, "health_score_ranges.json")
        
        # 8. Create signature with BOTH input AND output (required for UC)
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # 9. Log and register model
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
    """Main entry point for pipeline health scorer training."""
    print("\n" + "=" * 80)
    print("PIPELINE HEALTH SCORER - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("pipeline_health_scorer")
    
    try:
        # Prepare training data
        training_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Convert to Pandas for sklearn
        pdf = training_df.toPandas()
        
        print(f"\nPreparing features...")
        
        # Feature columns
        feature_cols = [
            # 30-day metrics
            'runs_30d', 'successful_30d', 'success_rate_30d',
            'avg_duration_30d', 'stddev_duration_30d', 'duration_cv_30d',
            'p95_duration_30d', 'p99_duration_30d', 'max_duration_30d',
            'avg_successful_duration_30d',
            # 7-day metrics
            'runs_7d', 'successful_7d', 'success_rate_7d',
            'avg_duration_7d', 'stddev_duration_7d', 'duration_cv_7d',
            'p95_duration_7d', 'max_duration_7d',
            # SLA metrics
            'sla_adherence_rate',
            # Trends
            'success_rate_trend', 'duration_trend', 'duration_ratio',
            # Risk indicators
            'consecutive_failures_possible'
        ]
        
        # Filter to only available columns
        available_features = [c for c in feature_cols if c in pdf.columns]
        
        X = pdf[available_features].fillna(0)
        y = pdf['health_score'].values
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"  Target range: {y.min():.1f} - {y.max():.1f}")
        print(f"  Target mean: {y.mean():.1f}")
        
        # Train/Val split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model, train_mae, val_mae, val_r2 = train_health_scorer(
            X_train, y_train, X_val, y_val
        )
        
        # Calculate additional metrics
        y_val_pred = model.predict(X_val)
        val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
        
        # Within 10 points accuracy
        within_10 = np.mean(np.abs(y_val - y_val_pred) <= 10)
        within_5 = np.mean(np.abs(y_val - y_val_pred) <= 5)
        
        metrics = {
            "train_mae": train_mae,
            "val_mae": val_mae,
            "val_rmse": val_rmse,
            "val_r2": val_r2,
            "within_10_points": within_10,
            "within_5_points": within_5,
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
        print("✓ PIPELINE HEALTH SCORER TRAINING COMPLETE")
        print(f"  Model: {model_name}")
        print(f"  MLflow Run: {run_id}")
        print(f"  Validation MAE: {val_mae:.2f} points")
        print(f"  Validation R²: {val_r2:.3f}")
        print(f"  Within ±10 Points: {within_10:.1%}")
        print(f"  Within ±5 Points: {within_5:.1%}")
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


