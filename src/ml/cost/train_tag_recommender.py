# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
# This enables imports from src.ml.config and src.ml.utils when deployed
# via Databricks Asset Bundles. The bundle root is computed dynamically.
# Reference: https://docs.databricks.com/aws/en/notebooks/share-code
import sys
import os

try:
    # Get current notebook path and compute bundle root
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================
"""
Train Tag Recommender Model
===========================

Problem: Classification + NLP
Algorithm: Random Forest + TF-IDF
Domain: Cost

This model recommends tags for untagged resources using:
- Job naming patterns (TF-IDF embedding)
- Cost features from feature table

REFACTORED: Uses FeatureRegistry for cost features.
NOTE: TF-IDF features are custom and computed at training time,
      so this model uses mlflow.sklearn.log_model (NOT fe.log_model).
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import json

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    get_run_name,
    get_standard_tags,
)

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Configuration
MODEL_NAME = "tag_recommender"
DOMAIN = "cost"
FEATURE_TABLE = "cost_features"
ALGORITHM = "random_forest"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def create_training_set_with_features(spark, fe, registry, catalog, gold_schema, feature_schema):
    """
    Create training set combining:
    - Cost features (via FeatureLookup with dynamic schema)
    - Job name for NLP features (computed at training time)
    """
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    
    # Get cost feature names dynamically from registry
    cost_feature_names = registry.get_feature_columns(
        FEATURE_TABLE,
        include_only=[
            "daily_dbu", "daily_cost", "avg_dbu_7d", "avg_dbu_30d",
            "jobs_on_all_purpose_cost", "all_purpose_inefficiency_ratio"
        ]
    )
    print(f"  Cost features from registry: {len(cost_feature_names)}")
    
    # Get primary keys from registry
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    # Get tagged jobs for training from Gold layer
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
    base_df = (
        tagged_jobs
        .join(
            spark.table(dim_job)
                .select("job_id", "name")
                .dropDuplicates(["job_id"]),
            "job_id", "inner"
        )
        .withColumnRenamed("name", "job_name")
    )
    
    record_count = base_df.count()
    print(f"  Tagged jobs found: {record_count}")
    
    if record_count == 0:
        raise ValueError("No tagged jobs found for training!")
    
    # Create FeatureLookup for cost features
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=cost_feature_names,
            lookup_key=lookup_keys
        )
    ]
    
    # Create training set
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="tag_value",
        exclude_columns=lookup_keys + ["job_id"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, cost_feature_names

# COMMAND ----------

def prepare_nlp_features(training_df, cost_feature_names):
    """
    Prepare TF-IDF features from job names and combine with cost features.
    """
    print("\nPreparing NLP and cost features...")
    
    pdf = training_df.toPandas()
    
    # TF-IDF on job names
    tfidf = TfidfVectorizer(max_features=50, lowercase=True, ngram_range=(1, 2), stop_words='english')
    job_name_features = tfidf.fit_transform(pdf['job_name'].fillna('')).toarray()
    job_name_df = pd.DataFrame(job_name_features, columns=[f"tfidf_{i}" for i in range(job_name_features.shape[1])])
    
    # Prepare cost features (filter to available)
    available_cost = [c for c in cost_feature_names if c in pdf.columns]
    cost_features = pdf[available_cost].copy()
    for col in cost_features.columns:
        cost_features[col] = pd.to_numeric(cost_features[col], errors='coerce')
    cost_features = cost_features.fillna(0).replace([np.inf, -np.inf], 0)
    
    # CRITICAL: Cast to float64 for MLflow
    for col in cost_features.columns:
        cost_features[col] = cost_features[col].astype('float64')
    
    # Combine features
    X = pd.concat([cost_features.reset_index(drop=True), job_name_df.reset_index(drop=True)], axis=1)
    
    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(pdf['tag_value'])
    
    feature_names = list(available_cost) + list(job_name_df.columns)
    
    print(f"✓ Features: {len(feature_names)} (Cost: {len(available_cost)}, NLP: {job_name_features.shape[1]})")
    print(f"  Unique tags: {len(label_encoder.classes_)}")
    
    return X, y, feature_names, tfidf, label_encoder

# COMMAND ----------

def train_model(X, y):
    """Train Random Forest classifier."""
    print("\nTraining Random Forest...")
    
    # CORRECT: Use X (pre-split) for train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    hyperparams = {"n_estimators": 100, "max_depth": 10, "min_samples_split": 5, "min_samples_leaf": 2, "random_state": 42}
    model = RandomForestClassifier(**hyperparams, n_jobs=-1)
    model.fit(X_train, y_train)
    
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    
    metrics = {
        "train_accuracy": round(train_acc, 4),
        "test_accuracy": round(test_acc, 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features_count": X_train.shape[1]
    }
    
    print(f"✓ Train: {train_acc:.3f}, Test: {test_acc:.3f}")
    
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model(model, X_train, metrics, hyperparams, tfidf, label_encoder, catalog, feature_schema):
    """
    Log model using mlflow.sklearn (NOT fe.log_model).
    
    NOTE: This model uses custom TF-IDF features computed at training time,
    which are not stored in the feature table. Therefore, we log it as a 
    regular sklearn model with explicit signature.
    """
    registered_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    feature_table = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    
    print(f"\nLogging model: {registered_name}")
    print("  NOTE: Using mlflow.sklearn.log_model (custom TF-IDF features)")
    
    # Create signature with float64 types
    input_example = X_train.head(5).astype('float64')
    predictions = model.predict(input_example)
    signature = infer_signature(input_example, predictions)
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=get_run_name(MODEL_NAME, ALGORITHM)) as run:
        mlflow.set_tags(get_standard_tags(MODEL_NAME, DOMAIN, "classification", ALGORITHM, "tag_recommendation", feature_table))
        mlflow.log_params(hyperparams)
        mlflow.log_params({"tfidf_max_features": 50, "feature_engineering": "custom_tfidf"})
        mlflow.log_metrics(metrics)
        
        # Save TF-IDF vectorizer and label encoder as artifacts
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
        
        # Log model with explicit signature (REQUIRED for Unity Catalog)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name=registered_name,
            input_example=input_example,
            signature=signature
        )
        
        print(f"✓ Model logged: {registered_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": MODEL_NAME,
            "registered_as": registered_name,
            "algorithm": ALGORITHM,
            "hyperparameters": hyperparams,
            "metrics": metrics
        }

# COMMAND ----------

def main():
    print("\n" + "=" * 60)
    print(f"{MODEL_NAME.upper().replace('_', ' ')} - TRAINING")
    print("Using FeatureRegistry (Dynamic Schema) + Custom TF-IDF")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    setup_training_environment(MODEL_NAME)
    
    try:
        # Create training set with Feature Engineering
        training_set, training_df, cost_feature_names = create_training_set_with_features(
            spark, fe, registry, catalog, gold_schema, feature_schema
        )
        
        # Prepare NLP + cost features
        X, y, feature_names, tfidf, label_encoder = prepare_nlp_features(training_df, cost_feature_names)
        
        # Train model
        model, metrics, hyperparams, X_train = train_model(X, y)
        
        # Log model
        result = log_model(model, X_train, metrics, hyperparams, tfidf, label_encoder, catalog, feature_schema)
        
        print("\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - Accuracy: {result['metrics']['test_accuracy']}")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({"status": "SUCCESS", **result}))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
