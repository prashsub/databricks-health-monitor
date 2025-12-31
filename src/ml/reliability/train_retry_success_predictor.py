# Databricks notebook source
"""
Train Retry Success Predictor Model
===================================

Problem: Binary Classification
Algorithm: XGBoost/DummyClassifier (fallback)
Domain: Reliability

Predicts likelihood of retry success for failed jobs.

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for automatic lineage tracking
- Enables automatic feature lookup at inference time

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
import mlflow
from mlflow.models.signature import infer_signature
from xgboost import XGBClassifier
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
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

def create_training_set_with_features(spark, fe, catalog, feature_schema, gold_schema):
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.reliability_features"
    fact_job = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    
    feature_names = ["total_runs", "avg_duration_sec", "success_rate", "failure_rate",
                     "duration_cv", "rolling_failure_rate_30d", "is_weekend", "day_of_week"]
    
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["job_id", "run_date"]
        )
    ]
    
    # Create retry success labels: 1 if retry succeeded, 0 if failed
    window_spec = Window.partitionBy("job_id").orderBy("period_start_time")
    
    base_df = (spark.table(fact_job)
               .filter(F.col("result_state") != "SUCCEEDED")  # Failed runs
               .withColumn("run_date", F.to_date("period_start_time"))
               .withColumn("next_result", F.lead("result_state").over(window_spec))
               .withColumn("retry_succeeded", F.when(F.col("next_result") == "SUCCEEDED", 1).otherwise(0))
               .select("job_id", "run_date", "retry_succeeded")
               .filter(F.col("retry_succeeded").isNotNull())
               .groupBy("job_id", "run_date")
               .agg(F.max("retry_succeeded").alias("retry_succeeded")))
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    if record_count == 0:
        raise ValueError(f"No data found!")
    
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="retry_succeeded",
        exclude_columns=["job_id", "run_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def get_positive_proba(model, X):
    """Get positive class probability, handling DummyClassifier with one class."""
    probas = model.predict_proba(X)
    if probas.shape[1] > 1:
        return probas[:, 1]
    else:
        # DummyClassifier with one class
        return probas[:, 0] if model.classes_[0] == 1 else (1 - probas[:, 0])


def prepare_and_train(training_df, feature_names):
    print("\nPreparing data and training model...")
    
    pdf = training_df.toPandas()
    X_train = pdf[feature_names].fillna(0).replace([np.inf, -np.inf], 0)
    y = pdf["retry_succeeded"].fillna(0).astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    # Check class balance
    pos_count = int(y_train.sum())
    neg_count = len(y_train) - pos_count
    print(f"  Class distribution: {pos_count} positive, {neg_count} negative")
    
    is_dummy_model = False
    
    if pos_count == 0 or neg_count == 0:
        print("  ⚠ Insufficient class diversity - using DummyClassifier")
        model = DummyClassifier(strategy='prior', random_state=42)
        model.fit(X_train, y_train)
        is_dummy_model = True
        algorithm = "DummyClassifier"
        hyperparams = {"strategy": "prior", "reason": "insufficient_class_diversity"}
    else:
        base_score = pos_count / len(y_train)
        hyperparams = {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1,
                       "random_state": 42, "use_label_encoder": False, 
                       "eval_metric": "logloss", "base_score": base_score}
        model = XGBClassifier(**hyperparams)
        model.fit(X_train, y_train)
        algorithm = "XGBClassifier"
    
    y_pred = model.predict(X_test)
    y_proba = get_positive_proba(model, X_test)
    
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4) if len(np.unique(y_test)) > 1 else 0.5,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "is_dummy_model": int(is_dummy_model)
    }
    
    print(f"✓ Algorithm: {algorithm}, Accuracy: {metrics['accuracy']:.4f}")
    return model, metrics, hyperparams, algorithm

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, algorithm, catalog, feature_schema, X_train):
    model_name = "retry_success_predictor"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, algorithm.lower())) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "reliability", "classification", algorithm.lower(),
            "retry_prediction", f"{catalog}.{feature_schema}.reliability_features"
        ))
        mlflow.log_params(hyperparams)
        mlflow.log_params({"feature_engineering": "unity_catalog"})
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
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": algorithm,
            "hyperparameters": hyperparams,
            "metrics": metrics
        }

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("RETRY SUCCESS PREDICTOR - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("retry_success_predictor")
    
    try:
        training_set, training_df, feature_names = create_training_set_with_features(spark, fe, catalog, feature_schema, gold_schema)
        model, metrics, hyperparams, algorithm = prepare_and_train(training_df, feature_names)
        result = log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, algorithm, catalog, feature_schema, X_train)
        
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print(f"  Model: {result['model_name']}")
        print(f"  Algorithm: {result['algorithm']}")
        print(f"  Feature Engineering: Unity Catalog ENABLED")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({
            "status": "SUCCESS", "model": result['model_name'],
            "registered_as": result['registered_as'], "run_id": result['run_id'],
            "metrics": result['metrics'], "feature_engineering": "unity_catalog"
        }))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
