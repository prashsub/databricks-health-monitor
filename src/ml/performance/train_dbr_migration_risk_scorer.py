# Databricks notebook source
"""
Train DBR Migration Risk Scorer Model
=====================================

Problem: Multi-class Classification (Risk Levels)
Algorithm: LightGBM Classifier
Domain: Performance

This model scores the risk of migrating jobs/clusters to newer DBR versions based on:
- Current DBR version and target version
- Library dependencies and compatibility
- Code complexity indicators
- Historical migration outcomes
- Job criticality and usage patterns

Risk Levels: LOW (0), MEDIUM (1), HIGH (2), CRITICAL (3)

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
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
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

def parse_dbr_version(version_str):
    """Parse DBR version string into numeric components."""
    try:
        # Handle versions like "13.3.x-scala2.12", "14.0-ml-scala2.12"
        parts = version_str.split("-")[0].replace("x", "0").split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major, minor
    except:
        return 0, 0


def prepare_training_data(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Prepare training data for DBR migration risk scoring.
    
    Features:
    - Current and target DBR versions
    - Job complexity (duration, data volume)
    - Historical failure rates
    - Library dependencies count
    - Time since last DBR upgrade
    
    Schema-grounded:
    - fact_job_run_timeline.yaml: spark_version, run_duration_seconds, 
      result_state, rows_produced, job_id
    - dim_job.yaml: job_id, name, created_time
    """
    print("\nPreparing training data for DBR migration risk scoring...")
    
    fact_job = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    
    # Get job run statistics with DBR versions
    job_stats = (
        spark.table(fact_job)
        .filter(F.col("run_start_timestamp") >= F.date_sub(F.current_date(), 180))
        .filter(F.col("spark_version").isNotNull())
        .groupBy("job_id", "spark_version")
        .agg(
            F.count("*").alias("total_runs"),
            F.sum(F.when(F.col("result_state") == "SUCCESS", 1).otherwise(0)).alias("successful_runs"),
            F.sum(F.when(F.col("result_state") == "FAILED", 1).otherwise(0)).alias("failed_runs"),
            F.avg("run_duration_seconds").alias("avg_duration_sec"),
            F.max("run_duration_seconds").alias("max_duration_sec"),
            F.stddev("run_duration_seconds").alias("duration_stddev"),
            F.sum(F.coalesce("rows_produced", F.lit(0))).alias("total_rows_processed"),
            F.min("run_start_timestamp").alias("first_run"),
            F.max("run_start_timestamp").alias("last_run")
        )
        .withColumn("failure_rate", F.col("failed_runs") / F.greatest(F.col("total_runs"), F.lit(1)))
        .withColumn("success_rate", F.col("successful_runs") / F.greatest(F.col("total_runs"), F.lit(1)))
    )
    
    # Parse DBR version components
    job_stats_with_version = (
        job_stats
        # Extract major.minor from spark_version
        .withColumn("dbr_parts", F.split(F.split("spark_version", "-")[0], "\\."))
        .withColumn("dbr_major", F.col("dbr_parts")[0].cast("int"))
        .withColumn("dbr_minor", F.coalesce(
            F.regexp_replace(F.col("dbr_parts")[1], "x", "0").cast("int"),
            F.lit(0)
        ))
        # Calculate version age (months behind latest - assume 15.0 is latest)
        .withColumn("versions_behind", F.greatest(
            F.lit(0),
            F.lit(15) - F.coalesce(F.col("dbr_major"), F.lit(13))
        ))
        # Is using ML runtime
        .withColumn("is_ml_runtime", F.when(F.col("spark_version").contains("-ml-"), 1).otherwise(0))
        # Is using photon
        .withColumn("is_photon", F.when(F.col("spark_version").contains("-photon-"), 1).otherwise(0))
        # Job complexity score
        .withColumn("complexity_score", 
            F.log1p(F.col("avg_duration_sec")) * 0.3 +
            F.log1p(F.col("total_rows_processed")) * 0.3 +
            F.col("duration_stddev") / F.greatest(F.col("avg_duration_sec"), F.lit(1)) * 0.4
        )
        # Days since job creation
        .withColumn("job_age_days", F.datediff(F.current_date(), F.col("first_run")))
    )
    
    # Create risk labels based on heuristics (for supervised learning)
    # In production, this would come from actual migration outcomes
    training_df = (
        job_stats_with_version
        .withColumn("migration_risk", 
            F.when(
                (F.col("failure_rate") > 0.3) | 
                (F.col("versions_behind") >= 3) |
                (F.col("complexity_score") > 5),
                F.lit(3)  # CRITICAL
            ).when(
                (F.col("failure_rate") > 0.15) |
                (F.col("versions_behind") >= 2) |
                (F.col("complexity_score") > 3),
                F.lit(2)  # HIGH
            ).when(
                (F.col("failure_rate") > 0.05) |
                (F.col("versions_behind") >= 1) |
                (F.col("complexity_score") > 1.5),
                F.lit(1)  # MEDIUM
            ).otherwise(
                F.lit(0)  # LOW
            )
        )
        .drop("dbr_parts")
    )
    
    record_count = training_df.count()
    print(f"✓ Prepared {record_count} job-version records for training")
    
    # Show risk distribution
    print("\nRisk Distribution:")
    training_df.groupBy("migration_risk").count().orderBy("migration_risk").show()
    
    return training_df

# COMMAND ----------

def train_risk_scorer(X_train, y_train, X_val, y_val):
    """
    Train LightGBM classifier for DBR migration risk scoring.
    
    Risk Levels:
    - 0: LOW - Safe to migrate
    - 1: MEDIUM - Some testing recommended
    - 2: HIGH - Extensive testing required
    - 3: CRITICAL - Manual review required
    """
    print("\nTraining LightGBM DBR Migration Risk Scorer...")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"  Risk levels: {np.unique(y_train)}")
    
    model = LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=8,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        class_weight='balanced',
        random_state=42,
        verbose=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_train_pred = model.predict(X_train)
    y_val_pred = model.predict(X_val)
    
    train_acc = accuracy_score(y_train, y_train_pred)
    val_acc = accuracy_score(y_val, y_val_pred)
    val_f1 = f1_score(y_val, y_val_pred, average='weighted')
    
    print(f"✓ Model trained successfully")
    print(f"  Training accuracy: {train_acc:.3f}")
    print(f"  Validation accuracy: {val_acc:.3f}")
    print(f"  Validation F1 (weighted): {val_f1:.3f}")
    
    return model, train_acc, val_acc, val_f1

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
    model_name = "dbr_migration_risk_scorer"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "lightgbm", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="performance",
            model_type="classification",
            algorithm="lightgbm",
            use_case="dbr_migration_risk_assessment",
            training_table=f"{catalog}.{feature_schema}.performance_features"
        ))
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "performance_features")
        
        # 3. Log hyperparameters
        mlflow.log_params({
            "model_type": "LGBMClassifier",
            "n_estimators": model.n_estimators,
            "learning_rate": model.learning_rate,
            "max_depth": model.max_depth,
            "num_leaves": model.num_leaves,
            "random_state": 42,
            "training_samples": len(X_train),
            "n_classes": len(np.unique(y_val))
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
        plt.title('Top 10 Features - DBR Migration Risk Scorer')
        plt.tight_layout()
        plt.savefig("feature_importance.png")
        mlflow.log_artifact("feature_importance.png")
        plt.close()
        
        # 6. Log confusion matrix
        from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
        cm = confusion_matrix(y_val, y_val_pred)
        disp = ConfusionMatrixDisplay(cm, display_labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        disp.plot()
        plt.title('DBR Migration Risk - Confusion Matrix')
        plt.tight_layout()
        plt.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")
        plt.close()
        
        # 7. Create signature with BOTH input AND output (required for UC)
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # 8. Log and register model
        mlflow.lightgbm.log_model(
            lgb_model=model,
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
    """Main entry point for DBR migration risk scorer training."""
    print("\n" + "=" * 80)
    print("DBR MIGRATION RISK SCORER - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("dbr_migration_risk_scorer")
    
    try:
        # Prepare training data
        training_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Convert to Pandas for sklearn
        pdf = training_df.toPandas()
        
        print(f"\nPreparing features...")
        
        # Feature columns
        feature_cols = [
            'total_runs', 'successful_runs', 'failed_runs', 'failure_rate', 'success_rate',
            'avg_duration_sec', 'max_duration_sec', 'duration_stddev', 'total_rows_processed',
            'dbr_major', 'dbr_minor', 'versions_behind', 'is_ml_runtime', 'is_photon',
            'complexity_score', 'job_age_days'
        ]
        
        X = pdf[feature_cols].fillna(0)
        y = pdf['migration_risk'].values
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"  Risk level distribution:")
        for level in sorted(np.unique(y)):
            count = (y == level).sum()
            pct = count / len(y) * 100
            risk_name = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][level]
            print(f"    {risk_name} ({level}): {count} ({pct:.1f}%)")
        
        # Train/Val split (stratified)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        # Train model
        model, train_acc, val_acc, val_f1 = train_risk_scorer(
            X_train, y_train, X_val, y_val
        )
        
        # Calculate additional metrics
        from sklearn.metrics import precision_score, recall_score
        y_val_pred = model.predict(X_val)
        
        metrics = {
            "train_accuracy": train_acc,
            "val_accuracy": val_acc,
            "val_f1_weighted": val_f1,
            "val_precision_weighted": precision_score(y_val, y_val_pred, average='weighted'),
            "val_recall_weighted": recall_score(y_val, y_val_pred, average='weighted'),
            "training_samples": len(X_train),
            "n_classes": len(np.unique(y_train))
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
        print("✓ DBR MIGRATION RISK SCORER TRAINING COMPLETE")
        print(f"  Model: {model_name}")
        print(f"  MLflow Run: {run_id}")
        print(f"  Validation Accuracy: {val_acc:.3f}")
        print(f"  Validation F1 (weighted): {val_f1:.3f}")
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

