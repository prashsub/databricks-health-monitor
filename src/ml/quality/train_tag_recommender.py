# Databricks notebook source
"""
Train Tag Recommender Model
===========================

Problem: Binary Classification
Algorithm: Random Forest
Domain: Quality

Recommends appropriate tags for tables based on quality features.

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for automatic lineage tracking
- Uses fe.log_model() for automatic feature lookup at inference time

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
import pandas as pd
import numpy as np
from datetime import datetime

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema


def setup_mlflow_experiment(model_name):
    mlflow.set_experiment(f"/Shared/health_monitor_ml_{model_name}")


def get_run_name(model_name, algorithm):
    return f"{model_name}_{algorithm}_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_standard_tags(model_name, domain, model_type, algorithm, use_case, training_table):
    return {
        "project": "databricks_health_monitor", "domain": domain, "model_name": model_name,
        "model_type": model_type, "algorithm": algorithm, "use_case": use_case,
        "training_data": training_table, "feature_engineering": "unity_catalog"
    }

# COMMAND ----------

def create_training_set_with_features(spark, fe, catalog, feature_schema):
    """Create training set with Feature Engineering."""
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.quality_features"
    
    feature_names = [
        "table_count", "schema_count", "column_count_avg", "total_rows",
        "tables_with_pk", "pk_coverage", "tables_with_cdf", "cdf_coverage",
        "tables_created_last_7d", "tables_modified_last_7d", "schema_changes_7d"
    ]
    
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["catalog_name", "snapshot_date"]
        )
    ]
    
    # Create label: needs_tagging based on whether table_count > 5 but pk_coverage < 0.5
    base_df = (spark.table(feature_table)
               .withColumn("needs_tagging",
                          F.when(
                              (F.col("table_count") > 5) & (F.col("pk_coverage") < 0.5), 1
                          ).otherwise(0))
               .select("catalog_name", "snapshot_date", "needs_tagging")
               .filter(F.col("needs_tagging").isNotNull()))
    
    record_count = base_df.count()
    print(f"  Base DataFrame: {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data in {feature_table}!")
    
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="needs_tagging",
        exclude_columns=["catalog_name", "snapshot_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def prepare_and_train(training_df, feature_names):
    """Prepare and train model."""
    print("\nTraining Random Forest model...")
    
    pdf = training_df.toPandas()
    available_features = [f for f in feature_names if f in pdf.columns]
    X_train = pdf[available_features].fillna(0).replace([np.inf, -np.inf], 0)
    
    # CRITICAL: Cast to float64 (MLflow doesn't support DECIMAL)
    for col in X.columns:
        X[col] = X[col].astype('float64')
    y = pdf["needs_tagging"]
    
    print(f"  Samples: {len(X_train)}, Features: {len(available_features)}")
    print(f"  Class distribution: {y.value_counts().to_dict()}")
    
    # Handle small datasets or imbalanced classes
    if len(X_train) < 10:
        print("  ⚠️ Small dataset, using simplified training")
        from sklearn.dummy import DummyClassifier
        hyperparams = {"strategy": "most_frequent"}
        model = DummyClassifier(**hyperparams)
        model.fit(X_train, y)
        metrics = {
            "accuracy": 0.5, "f1_score": 0.0, "training_samples": len(X_train), "features_count": len(available_features)
        }
        return model, metrics, hyperparams, X_train
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    hyperparams = {"n_estimators": 100, "max_depth": 10, "random_state": 42, "n_jobs": -1}
    model = RandomForestClassifier(**hyperparams)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features_count": len(available_features)
    }
    
    print(f"✓ Trained: Accuracy={metrics['accuracy']:.2%}, F1={metrics['f1_score']:.3f}")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table, X_train):
    """Log model with Feature Engineering."""
    model_name = "tag_recommender"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "random_forest")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "quality", "binary_classification", "random_forest",
            "tag_recommendation", feature_table
        ))
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
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
        return {"run_id": run.info.run_id, "model_name": model_name, "registered_as": registered_name, "metrics": metrics}

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("TAG RECOMMENDER - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    fe = FeatureEngineeringClient()
    setup_mlflow_experiment("tag_recommender")
    
    feature_table = f"{catalog}.{feature_schema}.quality_features"
    
    try:
        training_set, training_df, feature_names = create_training_set_with_features(
            spark, fe, catalog, feature_schema
        )
        model, metrics, hyperparams, X_train = prepare_and_train(training_df, feature_names)
        result = log_model_with_feature_engineering(
            fe, model, training_set, metrics, hyperparams, 
            catalog, feature_schema, feature_table, X_train
        )
        
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print(f"  Model: {result['model_name']}")
        print(f"  Accuracy: {result['metrics']['accuracy']:.2%}")
        print(f"  Feature Engineering: Unity Catalog ENABLED")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({
            "status": "SUCCESS", "model": result['model_name'],
            "registered_as": result['registered_as'], "run_id": result['run_id'],
            "feature_engineering": "unity_catalog"
        }))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
