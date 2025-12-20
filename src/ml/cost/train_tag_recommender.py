# Databricks notebook source
"""
Train Tag Recommender Model
===========================

Problem: Classification + NLP
Algorithm: Random Forest + Job Name Embedding
Domain: Cost

This model recommends tags for untagged resources based on:
- Job naming patterns (NLP embedding)
- Usage patterns
- Similar job tags
- Workspace common tags

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
from sklearn.feature_extraction.text import TfidfVectorizer
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

def prepare_training_data(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Prepare training data for tag recommendation.
    
    Features from fact_usage and fact_job_run_timeline:
    - Job names (for NLP)
    - Workspace patterns
    - SKU usage patterns
    - Existing tags from tagged jobs
    
    Schema-grounded:
    - fact_usage.yaml: usage_metadata (MAP), custom_tags (MAP), sku_name, workspace_id
    - fact_job_run_timeline.yaml: job_id, result_state
    """
    print("\nPreparing training data for tag recommendation...")
    
    # Load job-level usage data with tags
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    
    # Get tagged jobs for training
    tagged_jobs = (
        spark.table(fact_usage)
        .filter(F.col("is_tagged") == True)
        .filter(F.col("usage_metadata")["job_id"].isNotNull())
        .groupBy(F.col("usage_metadata")["job_id"].alias("job_id"))
        .agg(
            F.first("workspace_id").alias("workspace_id"),
            # Extract first available tag as target
            F.first(F.coalesce(
                F.col("custom_tags")["team"],
                F.col("custom_tags")["project"],
                F.col("custom_tags")["cost_center"]
            )).alias("tag_value"),
            # Determine which tag key was found
            F.first(F.when(
                F.col("custom_tags")["team"].isNotNull(), "team"
            ).when(
                F.col("custom_tags")["project"].isNotNull(), "project"
            ).otherwise("cost_center")).alias("tag_key"),
            # Most common SKU
            F.first(F.col("sku_name")).alias("primary_sku"),
            # Total cost (importance weight)
            F.sum("list_cost").alias("total_cost_30d")
        )
        .filter(F.col("tag_value").isNotNull())
    )
    
    # Get job names from dim_job
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    
    # Join to get job names (SCD2 dimension)
    training_df = (
        tagged_jobs
        .join(
            spark.table(dim_job)
                .filter(F.col("is_current") == True)
                .select("job_id", "name", "owned_by"),
            "job_id",
            "inner"
        )
        # Job name features
        .withColumn("job_name_length", F.length("name"))
        .withColumn("job_name_lower", F.lower("name"))
        .withColumn("job_prefix", F.split("job_name_lower", "[_-]")[0])
        .withColumn("has_test_in_name", F.when(F.col("job_name_lower").contains("test"), 1).otherwise(0))
        .withColumn("has_prod_in_name", F.when(F.col("job_name_lower").contains("prod"), 1).otherwise(0))
        .withColumn("has_dev_in_name", F.when(F.col("job_name_lower").contains("dev"), 1).otherwise(0))
        # Encode workspace patterns
        .withColumn("workspace_encoded", F.hash("workspace_id"))
        # Encode primary SKU
        .withColumn("sku_encoded", F.hash("primary_sku"))
    )
    
    record_count = training_df.count()
    print(f"✓ Prepared {record_count} tagged jobs for training")
    
    return training_df

# COMMAND ----------

def train_tag_recommender(X_train, y_train, X_val, y_val):
    """
    Train Random Forest classifier for tag recommendation.
    
    Model predicts tag value based on job name patterns and usage.
    """
    print("\nTraining Random Forest Tag Recommender...")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"  Unique tags: {len(np.unique(y_train))}")
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    
    print(f"✓ Model trained successfully")
    print(f"  Training accuracy: {train_acc:.3f}")
    print(f"  Validation accuracy: {val_acc:.3f}")
    
    return model, train_acc, val_acc

# COMMAND ----------

def log_model_to_mlflow(
    model,
    tfidf,
    label_encoder,
    X_train: pd.DataFrame,
    metrics: dict,
    catalog: str,
    feature_schema: str,
    experiment_name: str,
    spark: SparkSession
):
    """
    Log model to MLflow with Unity Catalog registry.
    
    Includes TF-IDF vectorizer and label encoder as artifacts.
    """
    model_name = "tag_recommender"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "random_forest", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="cost",
            model_type="classification",
            algorithm="random_forest",
            use_case="tag_recommendation",
            training_table=f"{catalog}.{feature_schema}.cost_features"
        ))
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "cost_features")
        
        # 3. Log hyperparameters
        mlflow.log_params({
            "model_type": "RandomForestClassifier",
            "n_estimators": model.n_estimators,
            "max_depth": model.max_depth,
            "min_samples_split": model.min_samples_split,
            "random_state": 42,
            "training_samples": len(X_train),
            "n_classes": len(label_encoder.classes_)
        })
        
        # 4. Log metrics
        mlflow.log_metrics(metrics)
        
        # 5. Save preprocessors as artifacts
        import joblib
        joblib.dump(tfidf, "tfidf_vectorizer.pkl")
        joblib.dump(label_encoder, "label_encoder.pkl")
        mlflow.log_artifact("tfidf_vectorizer.pkl")
        mlflow.log_artifact("label_encoder.pkl")
        
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
    """Main entry point for tag recommender training."""
    print("\n" + "=" * 80)
    print("TAG RECOMMENDER - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("tag_recommender")
    
    try:
        # Prepare training data
        training_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Convert to Pandas for sklearn
        pdf = training_df.toPandas()
        
        print(f"\nPreparing features...")
        
        # TF-IDF on job names
        tfidf = TfidfVectorizer(max_features=50, ngram_range=(1, 2))
        job_name_features = tfidf.fit_transform(pdf['job_name_lower']).toarray()
        
        # Create feature matrix
        numeric_features = pdf[[
            'job_name_length', 'has_test_in_name', 'has_prod_in_name', 'has_dev_in_name',
            'workspace_encoded', 'sku_encoded', 'total_cost_30d'
        ]].fillna(0).values
        
        # Combine TF-IDF and numeric features
        X = np.hstack([job_name_features, numeric_features])
        
        # Encode labels
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(pdf['tag_value'])
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"✓ Unique tags: {len(label_encoder.classes_)}")
        print(f"  Tags: {list(label_encoder.classes_)[:10]}...")
        
        # Train/Val split (stratified)
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        # Convert to DataFrame for MLflow signature
        feature_names = [f"tfidf_{i}" for i in range(job_name_features.shape[1])] + [
            'job_name_length', 'has_test_in_name', 'has_prod_in_name', 'has_dev_in_name',
            'workspace_encoded', 'sku_encoded', 'total_cost_30d'
        ]
        X_train_df = pd.DataFrame(X_train, columns=feature_names)
        X_val_df = pd.DataFrame(X_val, columns=feature_names)
        
        # Train model
        model, train_acc, val_acc = train_tag_recommender(
            X_train_df, y_train, X_val_df, y_val
        )
        
        # Calculate additional metrics
        from sklearn.metrics import precision_score, recall_score, f1_score
        y_val_pred = model.predict(X_val)
        
        metrics = {
            "train_accuracy": train_acc,
            "val_accuracy": val_acc,
            "val_precision": precision_score(y_val, y_val_pred, average='weighted'),
            "val_recall": recall_score(y_val, y_val_pred, average='weighted'),
            "val_f1": f1_score(y_val, y_val_pred, average='weighted'),
            "training_samples": len(X_train),
            "n_classes": len(label_encoder.classes_)
        }
        
        # Log to MLflow
        run_id, model_name = log_model_to_mlflow(
            model=model,
            tfidf=tfidf,
            label_encoder=label_encoder,
            X_train=X_train_df,
            metrics=metrics,
            catalog=catalog,
            feature_schema=feature_schema,
            experiment_name=experiment_name,
            spark=spark
        )
        
        print("\n" + "=" * 80)
        print("✓ TAG RECOMMENDER TRAINING COMPLETE")
        print(f"  Model: {model_name}")
        print(f"  MLflow Run: {run_id}")
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

