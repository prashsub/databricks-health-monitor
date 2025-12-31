# Databricks notebook source
"""
Train Tag Recommender Model
===========================

Problem: Classification + NLP
Algorithm: Random Forest + Job Name Embedding
Domain: Cost

This model recommends tags for untagged resources based on:
- Job naming patterns (NLP embedding)
- Usage patterns from cost_features
- Similar job tags
- Workspace common tags

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for cost features
- Combines with NLP features computed at training time
- Enables automatic feature lookup at inference

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
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
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
from datetime import datetime

# Feature Engineering imports
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

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
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    try:
        experiment = mlflow.set_experiment(experiment_name)
        print(f"✓ Experiment set: {experiment_name}")
        return experiment_name
    except Exception as e:
        print(f"⚠ Experiment setup warning: {e}")
        return experiment_name


def get_run_name(model_name: str, algorithm: str, version: str = "v1") -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{algorithm}_{version}_{timestamp}"


def get_standard_tags(model_name: str, domain: str, model_type: str, 
                      algorithm: str, use_case: str, training_table: str) -> dict:
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

# COMMAND ----------

def create_training_set_with_features(
    spark: SparkSession, 
    fe: FeatureEngineeringClient,
    catalog: str, 
    gold_schema: str,
    feature_schema: str
):
    """
    Create training set using Feature Engineering in Unity Catalog.
    
    This model combines:
    - Cost features from feature table (via FeatureLookup)
    - NLP features from job names (computed at training time)
    """
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    
    # Get tagged jobs for training from Gold layer
    # NOTE: cost_features PK is [workspace_id, usage_date] - sku_name was aggregated away
    tagged_jobs = (
        spark.table(fact_usage)
        .filter(F.col("is_tagged") == True)
        .filter(F.col("usage_metadata_job_id").isNotNull())
        .groupBy(F.col("usage_metadata_job_id").alias("job_id"))
        .agg(
            F.first("workspace_id").alias("workspace_id"),
            F.first(F.to_date("usage_date")).alias("usage_date"),
            F.first(F.coalesce(
                F.element_at(F.col("custom_tags"), "team"),
                F.element_at(F.col("custom_tags"), "project"),
                F.element_at(F.col("custom_tags"), "cost_center")
            )).alias("tag_value"),
            F.sum("list_cost").alias("total_cost_30d")
        )
        .filter(F.col("tag_value").isNotNull())
    )
    
    # Join to get job names
    # NOTE: dim_job is NOT SCD2, no is_current column
    base_df = (
        tagged_jobs
        .join(
            spark.table(dim_job)
                .select("job_id", "name")
                .dropDuplicates(["job_id"]),  # Handle potential duplicates
            "job_id",
            "inner"
        )
        .withColumnRenamed("name", "job_name")
    )
    
    record_count = base_df.count()
    print(f"  Tagged jobs found: {record_count}")
    
    if record_count == 0:
        raise ValueError("No tagged jobs found for training!")
    
    # Cost feature columns to look up
    cost_feature_names = [
        "daily_dbu", "daily_cost", "avg_dbu_7d", "avg_dbu_30d",
        "jobs_on_all_purpose_cost", "all_purpose_inefficiency_ratio"
    ]
    
    # Create FeatureLookup for cost features
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=cost_feature_names,
            lookup_key=["workspace_id", "usage_date"]
        )
    ]
    
    # Create training set - using tag_value as label
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="tag_value",
        exclude_columns=["workspace_id", "usage_date", "job_id"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set created with {training_df.count()} rows")
    
    return training_set, training_df, cost_feature_names

# COMMAND ----------

def prepare_nlp_features(training_df, cost_feature_names):
    """
    Prepare NLP features from job names and combine with cost features.
    """
    print("\nPreparing NLP and cost features...")
    
    # Convert to pandas
    pdf = training_df.toPandas()
    
    # Job name NLP features using TF-IDF
    tfidf = TfidfVectorizer(
        max_features=50,
        lowercase=True,
        ngram_range=(1, 2),
        stop_words='english'
    )
    
    job_name_features = tfidf.fit_transform(pdf['job_name'].fillna('')).toarray()
    job_name_df = pd.DataFrame(
        job_name_features,
        columns=[f"tfidf_{i}" for i in range(job_name_features.shape[1])]
    )
    
    # Combine cost features with NLP features
    cost_features = pdf[cost_feature_names].copy()
    for col in cost_features.columns:
        cost_features[col] = pd.to_numeric(cost_features[col], errors='coerce')
    cost_features = cost_features.fillna(0).replace([np.inf, -np.inf], 0)
    
    X = pd.concat([cost_features.reset_index(drop=True), job_name_df.reset_index(drop=True)], axis=1)
    
    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(pdf['tag_value'])
    
    feature_names = list(cost_feature_names) + list(job_name_df.columns)
    
    print(f"✓ Feature matrix shape: {X.shape}")
    print(f"  Cost features: {len(cost_feature_names)}")
    print(f"  NLP features: {job_name_features.shape[1]}")
    print(f"  Unique tags: {len(label_encoder.classes_)}")
    
    return X, y, feature_names, tfidf, label_encoder

# COMMAND ----------

def train_model(X, y):
    """Train Random Forest classifier."""
    print("\nTraining Random Forest Tag Recommender...")
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    hyperparams = {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "random_state": 42
    }
    
    model = RandomForestClassifier(**hyperparams, n_jobs=-1)
    model.fit(X_train, y_train)
    
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    
    metrics = {
        "train_accuracy": round(train_acc, 4),
        "val_accuracy": round(val_acc, 4),
        "training_samples": len(X_train),
        "validation_samples": len(X_val)
    }
    
    print(f"✓ Model trained - Train: {train_acc:.3f}, Val: {val_acc:.3f}")
    
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(
    fe: FeatureEngineeringClient,
    model,
    training_set,
    X_train,
    metrics,
    hyperparams,
    feature_names,
    tfidf,
    label_encoder,
    catalog: str,
    feature_schema: str
):
    """Log model using Feature Engineering client."""
    model_name = "tag_recommender"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=get_run_name(model_name, "random_forest")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "cost", "classification", "random_forest",
            "tag_recommendation", f"{catalog}.{feature_schema}.cost_features"
        ))
        
        mlflow.log_params(hyperparams)
        mlflow.log_params({
            "tfidf_max_features": 50,
            "feature_engineering": "unity_catalog"
        })
        mlflow.log_metrics(metrics)
        
        # Log TF-IDF vectorizer and label encoder as artifacts
        import pickle
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tfidf_path = os.path.join(tmpdir, "tfidf_vectorizer.pkl")
            le_path = os.path.join(tmpdir, "label_encoder.pkl")
            
            with open(tfidf_path, 'wb') as f:
                pickle.dump(tfidf, f)
            with open(le_path, 'wb') as f:
                pickle.dump(label_encoder, f)
            
            mlflow.log_artifact(tfidf_path)
            mlflow.log_artifact(le_path)
        
        # Log model with Feature Engineering
        # Create input example and signature (REQUIRED for Unity Catalog)
        input_example = X_train.head(5).astype('float64')
        sample_predictions = model.predict(input_example)
        signature = infer_signature(input_example, sample_predictions)
        
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name,
            input_example=input_example,
            signature=signature
        )
        
        print(f"✓ Model logged with Feature Engineering")
        print(f"  Run ID: {run.info.run_id}")
        print(f"  Registered: {registered_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": "RandomForestClassifier",
            "hyperparameters": hyperparams,
            "metrics": metrics
        }

# COMMAND ----------

def main():
    import json
    
    print("\n" + "=" * 80)
    print("TAG RECOMMENDER - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("tag_recommender")
    
    try:
        # Create training set with Feature Engineering
        training_set, training_df, cost_feature_names = create_training_set_with_features(
            spark, fe, catalog, gold_schema, feature_schema
        )
        
        # Prepare NLP features and combine with cost features
        X, y, feature_names, tfidf, label_encoder = prepare_nlp_features(
            training_df, cost_feature_names
        )
        
        # Train model
        model, metrics, hyperparams, X_train = train_model(X, y)
        
        # Log model with Feature Engineering
        result = log_model_with_feature_engineering(
            fe, model, training_set, X_train, metrics, hyperparams,
            feature_names, tfidf, label_encoder, catalog, feature_schema
        )
        
        print("\n" + "=" * 80)
        print("✓ TAG RECOMMENDER TRAINING COMPLETE")
        print(f"  Model: {result['registered_as']}")
        print(f"  MLflow Run: {result['run_id']}")
        print(f"  Feature Engineering: Unity Catalog ENABLED")
        print("=" * 80)
        
        dbutils.notebook.exit(json.dumps({
            "status": "SUCCESS",
            "model": result['model_name'],
            "registered_as": result['registered_as'],
            "run_id": result['run_id'],
            "algorithm": result['algorithm'],
            "metrics": result['metrics'],
            "feature_engineering": "unity_catalog"
        }))
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error during training: {str(e)}")
        print(traceback.format_exc())
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()
