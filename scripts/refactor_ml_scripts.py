#!/usr/bin/env python3
"""
Refactor ML Scripts to Use Feature Registry and Training Base
==============================================================

This script automatically refactors all training scripts to use the new
standardized utilities:
- FeatureRegistry for dynamic feature names
- training_base for standardized functions

Usage:
    python scripts/refactor_ml_scripts.py --dry-run  # Preview changes
    python scripts/refactor_ml_scripts.py            # Apply changes
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Model configurations by script name
MODEL_CONFIGS = {
    # COST DOMAIN (6 models)
    "train_budget_forecaster.py": {
        "model_name": "budget_forecaster",
        "domain": "cost",
        "feature_table": "cost_features",
        "label_column": "daily_cost",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "budget_forecasting",
    },
    "train_cost_anomaly_detector.py": {
        "model_name": "cost_anomaly_detector",
        "domain": "cost",
        "feature_table": "cost_features",
        "label_column": None,  # Anomaly detection - no label
        "model_type": "anomaly_detection",
        "algorithm": "isolation_forest",
        "use_case": "cost_anomaly_detection",
    },
    "train_job_cost_optimizer.py": {
        "model_name": "job_cost_optimizer",
        "domain": "cost",
        "feature_table": "cost_features",
        "label_column": "potential_job_cluster_savings",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "job_cost_optimization",
    },
    "train_chargeback_attribution.py": {
        "model_name": "chargeback_attribution",
        "domain": "cost",
        "feature_table": "cost_features",
        "label_column": "daily_cost",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "chargeback_attribution",
    },
    "train_commitment_recommender.py": {
        "model_name": "commitment_recommender",
        "domain": "cost",
        "feature_table": "cost_features",
        "label_column": "serverless_adoption_ratio",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "commitment_recommendation",
    },
    "train_tag_recommender.py": {
        "model_name": "tag_recommender",
        "domain": "cost",
        "feature_table": "cost_features",
        "label_column": None,  # Special - uses TF-IDF
        "model_type": "classification",
        "algorithm": "random_forest",
        "use_case": "tag_recommendation",
        "special": "tfidf",  # Uses custom preprocessing
    },
    
    # SECURITY DOMAIN (4 models)
    "train_security_threat_detector.py": {
        "model_name": "security_threat_detector",
        "domain": "security",
        "feature_table": "security_features",
        "label_column": None,
        "model_type": "anomaly_detection",
        "algorithm": "isolation_forest",
        "use_case": "threat_detection",
    },
    "train_access_pattern_analyzer.py": {
        "model_name": "access_pattern_analyzer",
        "domain": "security",
        "feature_table": "security_features",
        "label_column": "is_activity_burst",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "access_pattern_analysis",
    },
    "train_compliance_risk_classifier.py": {
        "model_name": "compliance_risk_classifier",
        "domain": "security",
        "feature_table": "security_features",
        "label_column": "lateral_movement_risk",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "compliance_risk_classification",
    },
    "train_permission_recommender.py": {
        "model_name": "permission_recommender",
        "domain": "security",
        "feature_table": "security_features",
        "label_column": "is_human_user",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "permission_recommendation",
    },
    
    # PERFORMANCE DOMAIN (7 models)
    "train_query_performance_forecaster.py": {
        "model_name": "query_performance_forecaster",
        "domain": "performance",
        "feature_table": "performance_features",
        "label_column": "p99_duration_ms",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "query_performance_forecasting",
    },
    "train_query_optimization_recommender.py": {
        "model_name": "query_optimization_recommender",
        "domain": "performance",
        "feature_table": "performance_features",
        "label_column": "sla_breach_rate",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "query_optimization_recommendation",
    },
    "train_cluster_efficiency_optimizer.py": {
        "model_name": "cluster_efficiency_optimizer",
        "domain": "performance",
        "feature_table": "performance_features",
        "label_column": "query_efficiency_rate",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "cluster_efficiency_optimization",
    },
    "train_cluster_sizing_recommender.py": {
        "model_name": "cluster_sizing_recommender",
        "domain": "performance",
        "feature_table": "performance_features",
        "label_column": "queries_per_minute",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "cluster_sizing_recommendation",
    },
    "train_resource_rightsizer.py": {
        "model_name": "resource_rightsizer",
        "domain": "performance",
        "feature_table": "performance_features",
        "label_column": "avg_bytes_per_query",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "resource_rightsizing",
    },
    "train_cache_hit_predictor.py": {
        "model_name": "cache_hit_predictor",
        "domain": "performance",
        "feature_table": "performance_features",
        "label_column": "spill_rate",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "cache_hit_prediction",
    },
    "train_regression_detector.py": {
        "model_name": "performance_regression_detector",
        "domain": "performance",
        "feature_table": "performance_features",
        "label_column": None,
        "model_type": "anomaly_detection",
        "algorithm": "isolation_forest",
        "use_case": "performance_regression_detection",
    },
    
    # RELIABILITY DOMAIN (5 models)
    "train_job_failure_predictor.py": {
        "model_name": "job_failure_predictor",
        "domain": "reliability",
        "feature_table": "reliability_features",
        "label_column": "failure_rate",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "job_failure_prediction",
    },
    "train_job_duration_forecaster.py": {
        "model_name": "job_duration_forecaster",
        "domain": "reliability",
        "feature_table": "reliability_features",
        "label_column": "avg_duration_sec",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "job_duration_forecasting",
    },
    "train_pipeline_health_scorer.py": {
        "model_name": "pipeline_health_scorer",
        "domain": "reliability",
        "feature_table": "reliability_features",
        "label_column": "success_rate",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "pipeline_health_scoring",
    },
    "train_sla_breach_predictor.py": {
        "model_name": "sla_breach_predictor",
        "domain": "reliability",
        "feature_table": "reliability_features",
        "label_column": "failure_rate",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "sla_breach_prediction",
    },
    "train_retry_success_predictor.py": {
        "model_name": "retry_success_predictor",
        "domain": "reliability",
        "feature_table": "reliability_features",
        "label_column": "success_rate",
        "model_type": "classification",
        "algorithm": "xgboost",
        "use_case": "retry_success_prediction",
    },
    
    # QUALITY DOMAIN (3 models)
    "train_data_drift_detector.py": {
        "model_name": "data_drift_detector",
        "domain": "quality",
        "feature_table": "quality_features",
        "label_column": None,
        "model_type": "anomaly_detection",
        "algorithm": "isolation_forest",
        "use_case": "data_drift_detection",
    },
    "train_schema_change_predictor.py": {
        "model_name": "schema_change_predictor",
        "domain": "quality",
        "feature_table": "quality_features",
        "label_column": "schema_changes_7d",
        "model_type": "classification",
        "algorithm": "random_forest",
        "use_case": "schema_change_prediction",
    },
    "train_freshness_predictor.py": {
        "model_name": "data_freshness_predictor",
        "domain": "quality",
        "feature_table": "quality_features",
        "label_column": "table_count",
        "model_type": "regression",
        "algorithm": "gradient_boosting",
        "use_case": "data_freshness_prediction",
    },
}


def generate_regression_script(config: Dict) -> str:
    """Generate a refactored regression training script."""
    return f'''# Databricks notebook source
"""
Train {config["model_name"].replace("_", " ").title()} Model
{"=" * (len(config["model_name"]) + 18)}

Problem: Regression
Algorithm: Gradient Boosting Regressor
Domain: {config["domain"].title()}

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from sklearn.ensemble import GradientBoostingRegressor
import json

from databricks.feature_engineering import FeatureEngineeringClient
from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    create_feature_lookup_training_set,
    prepare_training_data,
    log_model_with_features,
    calculate_regression_metrics,
)

# COMMAND ----------

# Configuration
MODEL_NAME = "{config["model_name"]}"
DOMAIN = "{config["domain"]}"
FEATURE_TABLE = "{config["feature_table"]}"
LABEL_COLUMN = "{config["label_column"]}"
ALGORITHM = "{config["algorithm"]}"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {{catalog}}, Gold Schema: {{gold_schema}}, Feature Schema: {{feature_schema}}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def train_model(X_train, X_test, y_train, y_test):
    print("\\nTraining model...")
    hyperparams = {{"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "random_state": 42}}
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    metrics = calculate_regression_metrics(model, X_train, X_test, y_train, y_test)
    return model, metrics, hyperparams

# COMMAND ----------

def main():
    print("\\n" + "=" * 60)
    print(f"{{MODEL_NAME.upper().replace('_', ' ')}} - TRAINING")
    print("Using FeatureRegistry (Dynamic Schema)")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    feature_names = registry.get_feature_columns(FEATURE_TABLE, exclude_columns=[LABEL_COLUMN])
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{{catalog}}.{{feature_schema}}.{{FEATURE_TABLE}}"
    
    try:
        training_set, training_df, available_features = create_feature_lookup_training_set(
            spark, fe, feature_table_full, feature_names, LABEL_COLUMN, lookup_keys
        )
        
        X_train, X_test, y_train, y_test = prepare_training_data(
            training_df, available_features, LABEL_COLUMN, cast_label_to="float64"
        )
        
        model, metrics, hyperparams = train_model(X_train, X_test, y_train, y_test)
        
        result = log_model_with_features(
            fe, model, training_set, X_train, metrics, hyperparams,
            MODEL_NAME, DOMAIN, "regression", ALGORITHM, "{config["use_case"]}",
            catalog, feature_schema, feature_table_full
        )
        
        print("\\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - R²: {{result['metrics']['test_r2']}}")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({{"status": "SUCCESS", **result}}))
        
    except Exception as e:
        import traceback
        print(f"❌ {{e}}\\n{{traceback.format_exc()}}")
        raise

if __name__ == "__main__":
    main()
'''


def generate_classification_script(config: Dict) -> str:
    """Generate a refactored classification training script."""
    return f'''# Databricks notebook source
"""
Train {config["model_name"].replace("_", " ").title()} Model
{"=" * (len(config["model_name"]) + 18)}

Problem: Classification
Algorithm: {config["algorithm"].upper()}
Domain: {config["domain"].title()}

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from xgboost import XGBClassifier
import json

from databricks.feature_engineering import FeatureEngineeringClient
from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    create_feature_lookup_training_set,
    prepare_training_data,
    log_model_with_features,
    calculate_classification_metrics,
)

# COMMAND ----------

# Configuration
MODEL_NAME = "{config["model_name"]}"
DOMAIN = "{config["domain"]}"
FEATURE_TABLE = "{config["feature_table"]}"
LABEL_COLUMN = "{config["label_column"]}"
ALGORITHM = "{config["algorithm"]}"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {{catalog}}, Gold Schema: {{gold_schema}}, Feature Schema: {{feature_schema}}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def train_model(X_train, X_test, y_train, y_test):
    print("\\nTraining model...")
    hyperparams = {{"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "random_state": 42, "eval_metric": "logloss"}}
    model = XGBClassifier(**hyperparams)
    model.fit(X_train, y_train)
    metrics = calculate_classification_metrics(model, X_train, X_test, y_train, y_test)
    return model, metrics, hyperparams

# COMMAND ----------

def main():
    print("\\n" + "=" * 60)
    print(f"{{MODEL_NAME.upper().replace('_', ' ')}} - TRAINING")
    print("Using FeatureRegistry (Dynamic Schema)")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    feature_names = registry.get_feature_columns(FEATURE_TABLE, exclude_columns=[LABEL_COLUMN])
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{{catalog}}.{{feature_schema}}.{{FEATURE_TABLE}}"
    
    try:
        training_set, training_df, available_features = create_feature_lookup_training_set(
            spark, fe, feature_table_full, feature_names, LABEL_COLUMN, lookup_keys
        )
        
        X_train, X_test, y_train, y_test = prepare_training_data(
            training_df, available_features, LABEL_COLUMN, cast_label_to="int", stratify=True
        )
        
        model, metrics, hyperparams = train_model(X_train, X_test, y_train, y_test)
        
        result = log_model_with_features(
            fe, model, training_set, X_train, metrics, hyperparams,
            MODEL_NAME, DOMAIN, "classification", ALGORITHM, "{config["use_case"]}",
            catalog, feature_schema, feature_table_full
        )
        
        print("\\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - Accuracy: {{result['metrics']['accuracy']}}, F1: {{result['metrics']['f1']}}")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({{"status": "SUCCESS", **result}}))
        
    except Exception as e:
        import traceback
        print(f"❌ {{e}}\\n{{traceback.format_exc()}}")
        raise

if __name__ == "__main__":
    main()
'''


def generate_anomaly_script(config: Dict) -> str:
    """Generate a refactored anomaly detection training script."""
    return f'''# Databricks notebook source
"""
Train {config["model_name"].replace("_", " ").title()} Model
{"=" * (len(config["model_name"]) + 18)}

Problem: Anomaly Detection (Unsupervised)
Algorithm: Isolation Forest
Domain: {config["domain"].title()}

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from sklearn.ensemble import IsolationForest
import mlflow
from mlflow.models.signature import infer_signature
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
MODEL_NAME = "{config["model_name"]}"
DOMAIN = "{config["domain"]}"
FEATURE_TABLE = "{config["feature_table"]}"
ALGORITHM = "isolation_forest"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {{catalog}}, Gold Schema: {{gold_schema}}, Feature Schema: {{feature_schema}}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def create_training_set(spark, fe, registry, catalog, feature_schema):
    print("\\nCreating training set...")
    
    feature_table_full = f"{{catalog}}.{{feature_schema}}.{{FEATURE_TABLE}}"
    feature_names = registry.get_feature_columns(FEATURE_TABLE)
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    feature_lookups = [
        FeatureLookup(table_name=feature_table_full, feature_names=feature_names, lookup_key=lookup_keys)
    ]
    
    base_df = spark.table(feature_table_full).select(*lookup_keys).distinct()
    print(f"  Base DataFrame: {{base_df.count()}} records")
    
    training_set = fe.create_training_set(df=base_df, feature_lookups=feature_lookups, label=None, exclude_columns=lookup_keys)
    training_df = training_set.load_df()
    print(f"✓ Training set: {{training_df.count()}} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def train_model(X_train, feature_names):
    print("\\nTraining Isolation Forest...")
    hyperparams = {{"n_estimators": 100, "contamination": 0.05, "random_state": 42, "n_jobs": -1}}
    model = IsolationForest(**hyperparams)
    model.fit(X_train)
    metrics = calculate_anomaly_metrics(model, X_train)
    return model, metrics, hyperparams

# COMMAND ----------

def log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full):
    registered_name = f"{{catalog}}.{{feature_schema}}.{{MODEL_NAME}}"
    print(f"\\nLogging model: {{registered_name}}")
    
    input_example = X_train.head(5).astype('float64')
    predictions = model.predict(input_example)
    signature = infer_signature(input_example, predictions)
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(MODEL_NAME, ALGORITHM)) as run:
        mlflow.set_tags(get_standard_tags(MODEL_NAME, DOMAIN, "anomaly_detection", ALGORITHM, "{config["use_case"]}", feature_table_full))
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        fe.log_model(model=model, artifact_path="model", flavor=mlflow.sklearn, training_set=training_set,
                    registered_model_name=registered_name, input_example=input_example, signature=signature)
        
        print(f"✓ Model logged: {{registered_name}}")
        return {{"run_id": run.info.run_id, "model_name": MODEL_NAME, "registered_as": registered_name, "metrics": metrics}}

# COMMAND ----------

def main():
    print("\\n" + "=" * 60)
    print(f"{{MODEL_NAME.upper().replace('_', ' ')}} - TRAINING")
    print("Using FeatureRegistry (Dynamic Schema)")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{{catalog}}.{{feature_schema}}.{{FEATURE_TABLE}}"
    
    try:
        training_set, training_df, feature_names = create_training_set(spark, fe, registry, catalog, feature_schema)
        X_train = prepare_anomaly_detection_data(training_df, feature_names)
        model, metrics, hyperparams = train_model(X_train, feature_names)
        result = log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full)
        
        print("\\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - Anomaly Rate: {{result['metrics']['anomaly_rate']*100:.1f}}%")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({{"status": "SUCCESS", **result}}))
        
    except Exception as e:
        import traceback
        print(f"❌ {{e}}\\n{{traceback.format_exc()}}")
        raise

if __name__ == "__main__":
    main()
'''


def refactor_scripts(base_path: Path, dry_run: bool = False):
    """Refactor all training scripts."""
    print("=" * 70)
    print("REFACTORING ML SCRIPTS TO USE FEATURE REGISTRY")
    print("=" * 70)
    
    refactored = 0
    skipped = 0
    
    for script_name, config in MODEL_CONFIGS.items():
        # Find the script
        domain = config["domain"]
        script_path = base_path / "src" / "ml" / domain / script_name
        
        if not script_path.exists():
            print(f"⚠️  Not found: {script_path}")
            skipped += 1
            continue
        
        # Skip special scripts (e.g., TF-IDF based)
        if config.get("special"):
            print(f"⏭️  Skipping (special): {script_name}")
            skipped += 1
            continue
        
        # Generate refactored content
        model_type = config["model_type"]
        if model_type == "regression":
            new_content = generate_regression_script(config)
        elif model_type == "classification":
            new_content = generate_classification_script(config)
        elif model_type == "anomaly_detection":
            new_content = generate_anomaly_script(config)
        else:
            print(f"⚠️  Unknown model type: {model_type}")
            skipped += 1
            continue
        
        if dry_run:
            print(f"📄 Would refactor: {script_path}")
        else:
            script_path.write_text(new_content)
            print(f"✅ Refactored: {script_path}")
        
        refactored += 1
    
    print("\n" + "=" * 70)
    print(f"Refactored: {refactored}")
    print(f"Skipped:    {skipped}")
    if dry_run:
        print("\n(DRY RUN - no changes made)")
    print("=" * 70)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Refactor ML training scripts')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--base-path', type=Path, default=Path('.'), help='Base path of the project')
    
    args = parser.parse_args()
    refactor_scripts(args.base_path, args.dry_run)


if __name__ == '__main__':
    main()

