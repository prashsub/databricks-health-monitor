# Databricks notebook source
# =============================================================================
# TRAINING MATERIAL: ML Model Training Pipeline
# =============================================================================
# This notebook demonstrates production-grade ML model training patterns
# for Databricks, including Feature Store integration, MLflow tracking,
# and Unity Catalog model registration.
#
# KEY CONCEPTS COVERED:
# 1. Asset Bundle imports (sys.path setup)
# 2. Feature Store integration (FeatureEngineeringClient)
# 3. MLflow experiment tracking
# 4. Unity Catalog model registration
# 5. Unsupervised learning (Isolation Forest)
# 6. Production deployment patterns
#
# ALGORITHM: Isolation Forest
# ---------------------------
# Isolation Forest is ideal for anomaly detection because:
# - Works well on high-dimensional data
# - Doesn't require labeled anomaly examples
# - Fast training and inference
# - Handles mixed feature types
#
# WHY UNSUPERVISED FOR ANOMALIES:
# In cost anomaly detection, we rarely have labeled "anomaly" data.
# Isolation Forest learns "normal" patterns and flags deviations.
# =============================================================================

# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
# TRAINING MATERIAL: Why This Path Setup Is Required
# ---------------------------------------------------
# When notebooks are deployed via Databricks Asset Bundles:
# - They run in /Workspace/.bundle/<target>/files/src/ml/cost/
# - Python can't find modules in src.ml.config by default
# - This setup adds the bundle root to sys.path
#
# ALTERNATIVE APPROACHES (why they don't work):
# 1. Relative imports: Fail in notebooks (no package context)
# 2. %run magic: Doesn't work after deployment
# 3. pip install local package: Too slow, complex CI/CD
#
# Reference: https://docs.databricks.com/aws/en/notebooks/share-code
import sys
import os

try:
    # Get current notebook path and compute bundle root
    # WHY getDbutils(): Only way to get notebook path in Databricks runtime
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    # WHY rsplit on '/src/': Bundle structure puts code under src/
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    # WHY catch Exception: Allows local development without Databricks runtime
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================

"""
Train Cost Anomaly Detector Model
=======================================

TRAINING MATERIAL: Complete ML Training Pipeline
------------------------------------------------

This notebook demonstrates a production ML training pipeline with:

PIPELINE STAGES:
┌─────────────────────────────────────────────────────────────────────────┐
│  1. FEATURE RETRIEVAL                                                    │
│     FeatureEngineeringClient → Feature Table → Training Features        │
├─────────────────────────────────────────────────────────────────────────┤
│  2. DATA PREPARATION                                                     │
│     Handle NaN/Inf → Type conversion → Pandas DataFrame                 │
├─────────────────────────────────────────────────────────────────────────┤
│  3. MODEL TRAINING                                                       │
│     Isolation Forest → Fit on "normal" data → Learn anomaly patterns   │
├─────────────────────────────────────────────────────────────────────────┤
│  4. METRIC CALCULATION                                                   │
│     Anomaly rate → Contamination verification → Model diagnostics       │
├─────────────────────────────────────────────────────────────────────────┤
│  5. MODEL LOGGING                                                        │
│     MLflow → Feature Store → Unity Catalog → Version & Alias           │
└─────────────────────────────────────────────────────────────────────────┘

CRITICAL PATTERNS:
- Feature Store for lineage tracking (fe.log_model)
- output_schema REQUIRED for Unity Catalog models
- Experiment path under /Shared/ (not /Users/)
- dbutils.notebook.exit() for job signaling

Problem: Anomaly Detection (Unsupervised)
Algorithm: Isolation Forest
Domain: Cost

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization
# 
# CATEGORIES:
# 1. Standard library (sys, os, json)
# 2. Third-party packages (sklearn, mlflow)
# 3. Databricks packages (feature_engineering)
# 4. Local modules (src.ml.*)
#
# WHY THIS ORDER: PEP 8 convention, makes dependencies clear

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# sklearn's Isolation Forest - core algorithm for anomaly detection
# WHY ISOLATION FOREST:
# - Efficient O(n log n) complexity
# - Handles high-dimensional data well
# - No assumption about data distribution
# - Returns anomaly score, not just label
from sklearn.ensemble import IsolationForest

# MLflow for experiment tracking and model registry
# WHY MLFLOW:
# - Unified tracking across training runs
# - Unity Catalog integration for model versioning
# - Automatic artifact storage
import mlflow
from mlflow.types import ColSpec, DataType, Schema
import json

# Databricks Feature Engineering Client
# WHY FEATURE STORE:
# - Lineage tracking (know what features trained the model)
# - Automatic feature lookup at inference time
# - Centralized feature management
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

# Local modules for configuration and utilities
# WHY SEPARATE MODULES:
# - Reusable across all training scripts
# - Single source of truth for feature schemas
# - Standardized training patterns
from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,      # MLflow experiment setup
    prepare_anomaly_detection_data,  # Data cleaning for sklearn
    get_run_name,                    # Consistent run naming
    get_standard_tags,               # Standard MLflow tags
    calculate_anomaly_metrics,       # Anomaly-specific metrics
)

# =============================================================================
# MLFLOW CONFIGURATION
# =============================================================================
# CRITICAL: This MUST be set before any MLflow operations
# WHY "databricks-uc": Enables Unity Catalog model registry
# WITHOUT THIS: Models go to workspace-level registry (deprecated)
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
# TRAINING MATERIAL: Centralized Configuration Pattern
#
# WHY CONSTANTS AT TOP:
# - Easy to modify without digging through code
# - Clear what model this script produces
# - Consistent naming across training and inference
#
# NAMING CONVENTION: <domain>_<problem_type>
# Example: cost_anomaly_detector, reliability_failure_predictor

MODEL_NAME = "cost_anomaly_detector"   # Registered model name
DOMAIN = "cost"                         # Domain for organization
FEATURE_TABLE = "cost_features"         # Source feature table
ALGORITHM = "isolation_forest"          # Algorithm identifier

# COMMAND ----------

# =============================================================================
# PARAMETER RETRIEVAL
# =============================================================================
# TRAINING MATERIAL: Widget-Based Parameter Passing
#
# WHY WIDGETS (not argparse):
# - Asset Bundle notebooks run via notebook_task
# - notebook_task passes parameters via widgets, NOT command line
# - argparse will FAIL with "error: required arguments"
#
# Reference: databricks-asset-bundles.mdc rule

def get_parameters():
    """
    Retrieve job parameters from Databricks widgets.
    
    TRAINING MATERIAL: Parameter Passing in Databricks Jobs
    ========================================================
    
    WIDGET TYPES:
    - dbutils.widgets.text(): For free-form text
    - dbutils.widgets.dropdown(): For predefined choices
    - dbutils.widgets.combobox(): Dropdown with free-form option
    - dbutils.widgets.get(): Retrieve value by name
    
    HOW PARAMETERS FLOW:
    1. Job YAML defines base_parameters:
       base_parameters:
         catalog: ${var.catalog}
         gold_schema: ${var.gold_schema}
         feature_schema: ${var.feature_schema}
    
    2. Databricks creates widgets automatically
    
    3. Code retrieves via dbutils.widgets.get()
    
    COMMON MISTAKE:
    Using argparse in notebooks WILL FAIL:
    "error: the following arguments are required: --catalog"
    
    Returns:
        Tuple of (catalog, gold_schema, feature_schema)
    """
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

# =============================================================================
# TRAINING SET CREATION
# =============================================================================
# TRAINING MATERIAL: Feature Store Training Set Pattern

def create_training_set(spark, fe, registry, catalog, feature_schema):
    """
    Create training set using Feature Store.
    
    TRAINING MATERIAL: Feature Store Training Sets
    ===============================================
    
    WHY FEATURE STORE:
    ------------------
    1. LINEAGE: Model knows which features it was trained on
    2. INFERENCE: Automatic feature lookup at prediction time
    3. CONSISTENCY: Same features used in training and serving
    4. GOVERNANCE: Centralized feature definitions
    
    TRAINING SET vs DIRECT TABLE READ:
    -----------------------------------
    
    ❌ DIRECT READ (loses lineage):
    training_df = spark.table("feature_table")
    model.fit(training_df.toPandas())
    mlflow.sklearn.log_model(model)  # No feature lineage!
    
    ✅ FEATURE STORE (preserves lineage):
    training_set = fe.create_training_set(...)
    training_df = training_set.load_df()
    model.fit(...)
    fe.log_model(model, training_set=training_set)  # Lineage preserved!
    
    FEATURE LOOKUP PATTERN:
    -----------------------
    FeatureLookup tells Feature Store:
    - table_name: Where to get features
    - feature_names: Which columns to use
    - lookup_key: How to join (primary key)
    
    UNSUPERVISED LEARNING:
    ----------------------
    For anomaly detection, label=None
    The model learns "normal" patterns without labeled examples
    
    Args:
        spark: SparkSession
        fe: FeatureEngineeringClient
        registry: FeatureRegistry for schema info
        catalog: Unity Catalog name
        feature_schema: Schema containing feature tables
        
    Returns:
        Tuple of (training_set, training_df, feature_names)
    """
    print("\nCreating training set...")
    
    # Build fully qualified table name (3-level: catalog.schema.table)
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    
    # Get feature columns from registry (NOT hardcoded!)
    # WHY REGISTRY: Single source of truth for feature schemas
    feature_names = registry.get_feature_columns(FEATURE_TABLE)
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    # Define feature lookup
    # WHY FeatureLookup: Enables automatic feature lookup at inference time
    feature_lookups = [
        FeatureLookup(table_name=feature_table_full, feature_names=feature_names, lookup_key=lookup_keys)
    ]
    
    # Create base DataFrame with just the keys
    # WHY DISTINCT: Ensure one row per entity (no duplicates)
    base_df = spark.table(feature_table_full).select(*lookup_keys).distinct()
    print(f"  Base DataFrame: {base_df.count()} records")
    
    # Create training set
    # WHY label=None: Unsupervised learning (anomaly detection)
    # WHY exclude_columns: Don't include keys as features
    training_set = fe.create_training_set(df=base_df, feature_lookups=feature_lookups, label=None, exclude_columns=lookup_keys)
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

# =============================================================================
# MODEL TRAINING
# =============================================================================
# TRAINING MATERIAL: Isolation Forest for Anomaly Detection

def train_model(X_train, feature_names):
    """
    Train Isolation Forest model.
    
    TRAINING MATERIAL: Isolation Forest Algorithm
    ==============================================
    
    HOW ISOLATION FOREST WORKS:
    ---------------------------
    1. Randomly select a feature
    2. Randomly select a split value between min and max
    3. Split data into two branches
    4. Repeat until each point is isolated
    
    KEY INSIGHT: Anomalies are easier to isolate
    - Normal points: Many splits needed to isolate
    - Anomalies: Few splits needed (they're unusual)
    
    HYPERPARAMETERS EXPLAINED:
    --------------------------
    n_estimators=100: Number of trees in the forest
      - Higher = more accurate but slower
      - 100 is a good default balance
    
    contamination=0.05: Expected proportion of anomalies
      - 0.05 = expect 5% of data to be anomalies
      - Affects the threshold for anomaly/normal decision
      - Tune based on domain knowledge
    
    random_state=42: For reproducibility
      - Same seed = same results across runs
      - Essential for debugging and testing
    
    n_jobs=-1: Use all CPU cores
      - Training can parallelize across trees
      - -1 = auto-detect available cores
    
    OUTPUT:
    -------
    - predict() returns: -1 (anomaly) or 1 (normal)
    - decision_function() returns: anomaly score (lower = more anomalous)
    
    WHY NOT SUPERVISED:
    -------------------
    Cost anomalies are rare and domain-specific.
    Getting labeled "anomaly" data is expensive and subjective.
    Unsupervised approach learns what "normal" looks like.
    
    Args:
        X_train: Prepared training data (Pandas DataFrame or numpy array)
        feature_names: List of feature names (for logging)
        
    Returns:
        Tuple of (trained_model, metrics_dict, hyperparams_dict)
    """
    print("\nTraining Isolation Forest...")
    
    # Define hyperparameters
    # BEST PRACTICE: Store in dict for MLflow logging
    hyperparams = {
        "n_estimators": 100,    # Number of trees
        "contamination": 0.05,  # Expected anomaly rate
        "random_state": 42,     # Reproducibility
        "n_jobs": -1            # Use all cores
    }
    
    # Create and train model
    model = IsolationForest(**hyperparams)
    model.fit(X_train)
    
    # Calculate anomaly-specific metrics
    # WHY CUSTOM METRICS: Standard metrics (accuracy, F1) don't apply to unsupervised
    metrics = calculate_anomaly_metrics(model, X_train)
    
    return model, metrics, hyperparams

# COMMAND ----------

# =============================================================================
# MODEL LOGGING
# =============================================================================
# TRAINING MATERIAL: Unity Catalog Model Registration

def log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full):
    """
    Log model to MLflow and register in Unity Catalog.
    
    TRAINING MATERIAL: Model Logging Best Practices
    ================================================
    
    WHY fe.log_model (not mlflow.sklearn.log_model):
    ------------------------------------------------
    fe.log_model() from FeatureEngineeringClient:
    - Embeds feature lineage in model metadata
    - Enables automatic feature lookup at inference
    - Required when using create_training_set()
    
    mlflow.sklearn.log_model() loses feature lineage!
    
    output_schema vs signature:
    ---------------------------
    For Unity Catalog models, BOTH input and output must be specified.
    
    ❌ WRONG (will fail):
    fe.log_model(model, training_set=training_set)  # No output spec!
    
    ✅ CORRECT:
    output_schema = Schema([ColSpec(DataType.long)])
    fe.log_model(..., output_schema=output_schema)
    
    WHY DataType.long FOR ANOMALY DETECTION:
    Isolation Forest returns -1 (anomaly) or 1 (normal)
    These are integers, so DataType.long is appropriate
    
    DISABLE AUTOLOG:
    ----------------
    mlflow.autolog() can conflict with custom logging.
    Disable it to have full control over what gets logged.
    
    Args:
        fe: FeatureEngineeringClient
        model: Trained model
        training_set: Feature Store training set
        X_train: Training data (for metrics)
        metrics: Calculated metrics dict
        hyperparams: Hyperparameters dict
        catalog: Unity Catalog name
        feature_schema: Schema for model registration
        feature_table_full: Full feature table name for tags
        
    Returns:
        Dict with run_id, model_name, registered_as, metrics
    """
    # Build 3-level model name for Unity Catalog
    # FORMAT: catalog.schema.model_name
    registered_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    print(f"\nLogging model: {registered_name}")
    
    # ==========================================================================
    # CRITICAL: output_schema for Unity Catalog
    # ==========================================================================
    # For anomaly detection (unsupervised), use output_schema NOT signature
    # Isolation Forest returns -1 (anomaly) or 1 (normal), so output is long
    # 
    # LESSON LEARNED: Without this, model registration fails with:
    # "Model passed for registration contained a signature that includes only inputs"
    output_schema = Schema([ColSpec(DataType.long)])
    
    # Disable autolog to prevent conflicts with custom logging
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=get_run_name(MODEL_NAME, ALGORITHM)) as run:
        # Log tags for organization and filtering
        # TAGS: Searchable in MLflow UI, used for filtering
        mlflow.set_tags(get_standard_tags(MODEL_NAME, DOMAIN, "anomaly_detection", ALGORITHM, "cost_anomaly_detection", feature_table_full))
        
        # Log hyperparameters for reproducibility
        # PARAMS: Fixed values that defined the training run
        mlflow.log_params(hyperparams)
        
        # Log metrics for performance tracking
        # METRICS: Numeric values, can be compared across runs
        mlflow.log_metrics(metrics)
        
        # Log model with Feature Store lineage
        # WHY fe.log_model: Preserves feature lookup metadata
        # WHY flavor=mlflow.sklearn: Required parameter, specifies serialization format
        # WHY infer_input_example=True: Automatically captures sample input
        fe.log_model(model=model, artifact_path="model", flavor=mlflow.sklearn, training_set=training_set,
                    registered_model_name=registered_name, infer_input_example=True, output_schema=output_schema)
        
        print(f"✓ Model logged: {registered_name}")
        return {"run_id": run.info.run_id, "model_name": MODEL_NAME, "registered_as": registered_name, "metrics": metrics}

# COMMAND ----------

# =============================================================================
# MAIN FUNCTION
# =============================================================================
# TRAINING MATERIAL: Production Training Pipeline Entry Point

def main():
    """
    Main training pipeline entry point.
    
    TRAINING MATERIAL: Pipeline Structure
    ======================================
    
    PIPELINE FLOW:
    1. Print banner (for job logs)
    2. Get parameters (from widgets)
    3. Initialize clients (Spark, Feature Store, Registry)
    4. Setup MLflow experiment
    5. Create training set
    6. Prepare data
    7. Train model
    8. Log model
    9. Exit with status
    
    ERROR HANDLING:
    ---------------
    - try/except catches all errors
    - Traceback printed for debugging
    - Exception re-raised (job will fail)
    - No dbutils.notebook.exit() on error (job shows FAILED)
    
    SUCCESS SIGNALING:
    ------------------
    dbutils.notebook.exit() is REQUIRED for proper job signaling.
    Without it, job may show SUCCESS even on failure.
    
    WHY JSON OUTPUT:
    The exit message can be parsed by downstream jobs.
    Enables pipeline orchestration based on training results.
    """
    print("\n" + "=" * 60)
    print(f"{MODEL_NAME.upper().replace('_', ' ')} - TRAINING")
    print("Using FeatureRegistry (Dynamic Schema)")
    print("=" * 60)
    
    # Get job parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Initialize Spark session
    # WHY getOrCreate: Reuses existing session if available
    spark = SparkSession.builder.getOrCreate()
    
    # Initialize clients
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    # Setup MLflow experiment (creates if doesn't exist)
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    
    try:
        # =================================================================
        # PIPELINE EXECUTION
        # =================================================================
        
        # Step 1: Create training set from Feature Store
        training_set, training_df, feature_names = create_training_set(spark, fe, registry, catalog, feature_schema)
        
        # Step 2: Prepare data for sklearn (Pandas conversion, NaN handling)
        X_train = prepare_anomaly_detection_data(training_df, feature_names)
        
        # Step 3: Train model
        model, metrics, hyperparams = train_model(X_train, feature_names)
        
        # Step 4: Log model to MLflow and Unity Catalog
        result = log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full)
        
        # =================================================================
        # SUCCESS OUTPUT
        # =================================================================
        print("\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - Anomaly Rate: {result['metrics']['anomaly_rate']*100:.1f}%")
        print("=" * 60)
        
        # CRITICAL: Exit with JSON for downstream job parsing
        # Status: SUCCESS enables conditional workflow execution
        dbutils.notebook.exit(json.dumps({"status": "SUCCESS", **result}))
        
    except Exception as e:
        # =================================================================
        # ERROR HANDLING
        # =================================================================
        # Print full traceback for debugging in job logs
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        # Re-raise to ensure job shows FAILED status
        raise

# Standard Python entry point
# WHY: Allows running as script or importing without execution
if __name__ == "__main__":
    main()
