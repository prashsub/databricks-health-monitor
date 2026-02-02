# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
# TRAINING MATERIAL: Databricks Asset Bundle Import Pattern
# ----------------------------------------------------------
# When notebooks are deployed via Asset Bundles, they run in /Workspace/...
# but local imports (from src.ml.config import...) fail because Python
# doesn't know where to find the src package.
#
# Solution: Dynamically add the bundle root to sys.path at runtime.
#
# How it works:
# 1. Get current notebook path: /Workspace/Repos/user/project/src/ml/train.py
# 2. Find bundle root: /Workspace/Repos/user/project
# 3. Add to sys.path: Now "from src.ml.config import X" works!
#
# This pattern is necessary because:
# - Asset Bundles don't automatically configure PYTHONPATH
# - The notebook path varies between environments
# - Local imports require the parent directory in sys.path
# ===========================================================================
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
TRAINING MATERIAL: ML Model Training Pattern (Anomaly Detection)
================================================================

This notebook demonstrates the standard ML training pattern for anomaly
detection models using Isolation Forest with Databricks Feature Store.

SECURITY THREAT DETECTION USE CASE:
-----------------------------------
Detect anomalous behavior patterns that may indicate security threats:
- Unusual access times (3am access to sensitive data)
- Abnormal data volumes (user downloading 10x normal amount)
- Suspicious patterns (multiple failed logins then success)
- Privilege escalation indicators

WHY ISOLATION FOREST FOR SECURITY:
----------------------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  ALGORITHM CHOICE: ISOLATION FOREST                                      │
│                                                                         │
│  SUPERVISED ML:                      UNSUPERVISED (Isolation Forest):   │
│  ────────────────                    ──────────────────────────────────  │
│  - Requires labeled threats          - No labels needed!                │
│  - Can't detect novel threats        - Detects ANY anomaly              │
│  - Limited by training data          - Finds "unknown unknowns"         │
│                                                                         │
│  For security: Most attacks are NEW (zero-day). Isolation Forest        │
│  excels at finding things that are "different" without needing          │
│  examples of what threats look like.                                    │
└─────────────────────────────────────────────────────────────────────────┘

HOW ISOLATION FOREST WORKS:
---------------------------
1. Build random trees that isolate points
2. Anomalies are easier to isolate (shorter path)
3. Normal points require more splits to isolate
4. Score = average path length across all trees
5. Shorter path → Higher anomaly score

FEATURE STORE INTEGRATION:
--------------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  WHY FEATURE STORE FOR ML?                                               │
│                                                                         │
│  WITHOUT Feature Store:            WITH Feature Store:                  │
│  ────────────────────              ──────────────────                   │
│  - Training uses raw data           - Training uses curated features    │
│  - Inference recalculates           - Inference uses same features!    │
│  - Training/serving skew            - Consistency guaranteed            │
│  - No feature lineage               - Full lineage in Unity Catalog     │
│                                                                         │
│  fe.create_training_set() → fe.log_model() → fe.score_batch()          │
│  Same feature definitions used everywhere!                              │
└─────────────────────────────────────────────────────────────────────────┘

MODEL OUTPUT:
-------------
Isolation Forest returns:
- -1 = Anomaly (potential threat)
- +1 = Normal

We log to Unity Catalog Model Registry for:
- Version control
- Lineage tracking
- Deployment to batch inference

Problem: Anomaly Detection (Unsupervised)
Algorithm: Isolation Forest
Domain: Security

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from sklearn.ensemble import IsolationForest
import mlflow
from mlflow.types import ColSpec, DataType, Schema
import json

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    prepare_anomaly_detection_data,
    get_run_name,
    get_standard_tags,
    calculate_anomaly_metrics,
)

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Configuration
MODEL_NAME = "security_threat_detector"
DOMAIN = "security"
FEATURE_TABLE = "security_features"
ALGORITHM = "isolation_forest"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def create_training_set(spark, fe, registry, catalog, feature_schema):
    print("\nCreating training set...")
    
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    feature_names = registry.get_feature_columns(FEATURE_TABLE)
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    feature_lookups = [
        FeatureLookup(table_name=feature_table_full, feature_names=feature_names, lookup_key=lookup_keys)
    ]
    
    base_df = spark.table(feature_table_full).select(*lookup_keys).distinct()
    print(f"  Base DataFrame: {base_df.count()} records")
    
    training_set = fe.create_training_set(df=base_df, feature_lookups=feature_lookups, label=None, exclude_columns=lookup_keys)
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def train_model(X_train, feature_names):
    print("\nTraining Isolation Forest...")
    hyperparams = {"n_estimators": 100, "contamination": 0.05, "random_state": 42, "n_jobs": -1}
    model = IsolationForest(**hyperparams)
    model.fit(X_train)
    metrics = calculate_anomaly_metrics(model, X_train)
    return model, metrics, hyperparams

# COMMAND ----------

def log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full):
    registered_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    print(f"\nLogging model: {registered_name}")
    
    # CRITICAL: For anomaly detection (unsupervised), use output_schema NOT signature
    # Isolation Forest returns -1 (anomaly) or 1 (normal), so output is long
    output_schema = Schema([ColSpec(DataType.long)])
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(MODEL_NAME, ALGORITHM)) as run:
        mlflow.set_tags(get_standard_tags(MODEL_NAME, DOMAIN, "anomaly_detection", ALGORITHM, "threat_detection", feature_table_full))
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        fe.log_model(model=model, artifact_path="model", flavor=mlflow.sklearn, training_set=training_set,
                    registered_model_name=registered_name, infer_input_example=True, output_schema=output_schema)
        
        print(f"✓ Model logged: {registered_name}")
        return {"run_id": run.info.run_id, "model_name": MODEL_NAME, "registered_as": registered_name, "metrics": metrics}

# COMMAND ----------

def main():
    print("\n" + "=" * 60)
    print(f"{MODEL_NAME.upper().replace('_', ' ')} - TRAINING")
    print("Using FeatureRegistry (Dynamic Schema)")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    
    try:
        training_set, training_df, feature_names = create_training_set(spark, fe, registry, catalog, feature_schema)
        X_train = prepare_anomaly_detection_data(training_df, feature_names)
        model, metrics, hyperparams = train_model(X_train, feature_names)
        result = log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full)
        
        print("\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - Anomaly Rate: {result['metrics']['anomaly_rate']*100:.1f}%")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({"status": "SUCCESS", **result}))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
