# Databricks notebook source
"""
TRAINING MATERIAL: MLflow 3.0 Integration Pattern for Unity Catalog
====================================================================

This module provides utilities for MLflow 3.0 integration with Unity Catalog.
MLflow 3.0 introduced significant changes that affect model logging, registration,
and evaluation.

MLFLOW 3.0 KEY CHANGES (CRITICAL):
----------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  MLflow 2.x vs MLflow 3.0                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  REGISTRY URI                                                            │
│  ──────────────                                                          │
│  2.x: Default was local file store or databricks registry                │
│  3.0: Default is 'databricks-uc' (Unity Catalog)  ✅                     │
│                                                                         │
│  MODEL LOGGING                                                           │
│  ─────────────                                                           │
│  2.x: mlflow.sklearn.log_model(model, artifact_path="model")             │
│  3.0: mlflow.sklearn.log_model(model, name="model")  ✅                  │
│       ⚠️ 'artifact_path' still works but 'name' is preferred             │
│                                                                         │
│  MODEL SIGNATURES                                                        │
│  ────────────────                                                        │
│  2.x: Optional (but recommended)                                        │
│  3.0: REQUIRED for Unity Catalog registration  ⚠️                        │
│       Without signature → registration fails!                           │
│                                                                         │
│  MODEL EVALUATION                                                        │
│  ─────────────────                                                       │
│  2.x: mlflow.evaluate(model_uri, data, ...)                             │
│  3.0: mlflow.models.evaluate(model_uri, data, ...)  ✅                   │
│       mlflow.evaluate is DEPRECATED                                     │
│                                                                         │
│  LOGGEDMODEL OBJECT                                                      │
│  ────────────────────                                                    │
│  2.x: LoggedModel was not a first-class object                          │
│  3.0: LoggedModel is a first-class citizen  ✅                           │
│       Can be created without active run                                 │
└─────────────────────────────────────────────────────────────────────────┘

UNITY CATALOG MODEL NAMING:
---------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  Three-Level Naming Required for Unity Catalog:                          │
│                                                                         │
│  {catalog}.{schema}.{model_name}                                        │
│                                                                         │
│  Example: health_monitor.ml.cost_anomaly_detector                       │
│                                                                         │
│  This provides:                                                         │
│  - Governance: Access control at model level                            │
│  - Lineage: Track model data dependencies                               │
│  - Discovery: Models visible in Unity Catalog UI                        │
└─────────────────────────────────────────────────────────────────────────┘

MODEL SIGNATURE PATTERN:
------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  SIGNATURE IS REQUIRED:                                                  │
│                                                                         │
│  from mlflow.models import infer_signature                               │
│                                                                         │
│  # For supervised models:                                               │
│  signature = infer_signature(X_train, y_train)                          │
│                                                                         │
│  # For unsupervised models (e.g., anomaly detection):                   │
│  predictions = model.predict(X_sample)                                  │
│  signature = infer_signature(X_sample, predictions)                     │
│                                                                         │
│  mlflow.sklearn.log_model(                                              │
│      model,                                                             │
│      name="model_name",                                                 │
│      signature=signature,  ← REQUIRED!                                  │
│      registered_model_name="catalog.schema.model_name"                  │
│  )                                                                      │
└─────────────────────────────────────────────────────────────────────────┘

KEY FUNCTIONS IN THIS MODULE:
-----------------------------

1. MLflowConfig - Configuration dataclass for consistent naming
2. setup_mlflow_experiment() - Initialize experiment with UC registry
3. log_model_with_signature() - Log model with required signature
4. evaluate_logged_model() - Use mlflow.models.evaluate (3.0 pattern)
5. get_latest_model_version() - Get latest version from UC registry
6. load_model_for_inference() - Load model for prediction

Reference: https://learn.microsoft.com/en-us/azure/databricks/mlflow/mlflow-3-install
"""

import mlflow
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MLflowConfig:
    """
    Configuration for MLflow 3.0 with Unity Catalog integration.
    
    Attributes:
        catalog: Unity Catalog name for model registry
        schema: Schema name for models and feature tables
        experiment_base_path: Base path for MLflow experiments
        model_prefix: Prefix for registered model names
        tags: Default tags to apply to all runs and models
    """
    catalog: str
    schema: str
    experiment_base_path: str = "/Shared/health_monitor/ml"
    model_prefix: str = "health_monitor"
    tags: Dict[str, str] = field(default_factory=lambda: {
        "project": "databricks_health_monitor",
        "mlflow_version": "3.0",
        "framework": "unity_catalog"
    })
    
    def get_registered_model_name(self, model_name: str) -> str:
        """
        Get fully qualified model name for Unity Catalog.
        
        MLflow 3.0 requires three-level names: catalog.schema.model_name
        
        Args:
            model_name: Short model name (e.g., 'cost_anomaly_detector')
            
        Returns:
            Fully qualified name (e.g., 'catalog.schema.health_monitor_cost_anomaly_detector')
        """
        full_name = f"{self.model_prefix}_{model_name}" if self.model_prefix else model_name
        return f"{self.catalog}.{self.schema}.{full_name}"
    
    def get_experiment_path(self, agent_domain: str, model_name: str) -> str:
        """
        Get experiment path for a model.
        
        Args:
            agent_domain: Agent domain (cost, security, performance, reliability, quality)
            model_name: Short model name
            
        Returns:
            Full experiment path
        """
        return f"{self.experiment_base_path}/{agent_domain}/{model_name}"


def setup_mlflow_experiment(config: MLflowConfig, agent_domain: str, model_name: str) -> str:
    """
    Set up MLflow experiment and configure for Unity Catalog.
    
    MLflow 3.0: Default registry URI is databricks-uc, but we set it explicitly
    for clarity and backwards compatibility.
    
    Args:
        config: MLflow configuration
        agent_domain: Agent domain (cost, security, performance, reliability, quality)
        model_name: Short model name
        
    Returns:
        Experiment ID
    """
    # Set registry URI to Unity Catalog (default in MLflow 3.0)
    mlflow.set_registry_uri("databricks-uc")
    
    # Create or get experiment
    experiment_path = config.get_experiment_path(agent_domain, model_name)
    experiment = mlflow.set_experiment(experiment_path)
    
    logger.info(f"MLflow experiment set: {experiment_path}")
    logger.info(f"Registry URI: {mlflow.get_registry_uri()}")
    
    return experiment.experiment_id


def log_model_with_signature(
    model,
    model_name: str,
    config: MLflowConfig,
    flavor: str,
    X_sample,
    y_sample=None,
    input_example=None,
    extra_pip_requirements: Optional[List[str]] = None,
    custom_tags: Optional[Dict[str, str]] = None,
    metrics: Optional[Dict[str, float]] = None,
    params: Optional[Dict[str, Any]] = None,
    register_model: bool = True
) -> mlflow.models.model.ModelInfo:
    """
    Log a model with signature using MLflow 3.0 best practices.
    
    MLflow 3.0 Key Changes:
    - Use 'name' parameter (not 'artifact_path')
    - Signatures are REQUIRED for Unity Catalog registration
    - LoggedModel is created automatically
    
    Args:
        model: Trained model object
        model_name: Short model name
        config: MLflow configuration
        flavor: MLflow flavor (sklearn, xgboost, lightgbm, etc.)
        X_sample: Sample input data for signature inference
        y_sample: Sample output data for signature inference (optional)
        input_example: Input example for model documentation
        extra_pip_requirements: Additional pip requirements
        custom_tags: Additional tags for the model
        metrics: Metrics to log
        params: Parameters to log
        register_model: Whether to register in Unity Catalog
        
    Returns:
        ModelInfo object with model metadata
    """
    # Get the appropriate log_model function
    flavor_map = {
        "sklearn": mlflow.sklearn,
        "xgboost": mlflow.xgboost,
        "lightgbm": mlflow.lightgbm,
        "pyfunc": mlflow.pyfunc,
        "tensorflow": mlflow.tensorflow,
        "keras": mlflow.keras,
    }
    
    if flavor not in flavor_map:
        raise ValueError(f"Unsupported flavor: {flavor}. Supported: {list(flavor_map.keys())}")
    
    flavor_module = flavor_map[flavor]
    
    # Infer model signature (REQUIRED for Unity Catalog)
    if y_sample is not None:
        signature = infer_signature(X_sample, y_sample)
    else:
        # For models that don't have a clear output (e.g., anomaly detection)
        predictions = model.predict(X_sample) if hasattr(model, 'predict') else None
        signature = infer_signature(X_sample, predictions)
    
    # Prepare registered model name
    registered_model_name = config.get_registered_model_name(model_name) if register_model else None
    
    # Combine tags
    all_tags = {**config.tags}
    if custom_tags:
        all_tags.update(custom_tags)
    all_tags["logged_at"] = datetime.now().isoformat()
    
    # Start run and log model
    with mlflow.start_run() as run:
        # Log parameters
        if params:
            mlflow.log_params(params)
        
        # Log metrics
        if metrics:
            mlflow.log_metrics(metrics)
        
        # MLflow 3.0: Use 'name' parameter instead of 'artifact_path'
        # Signature is REQUIRED for Unity Catalog registration
        model_info = flavor_module.log_model(
            model,
            name=model_name,  # MLflow 3.0: use 'name' not 'artifact_path'
            signature=signature,
            input_example=input_example if input_example is not None else X_sample[:5],
            registered_model_name=registered_model_name,
            pip_requirements=extra_pip_requirements,
        )
        
        # Set tags on the logged model
        if hasattr(model_info, 'model_id') and model_info.model_id:
            mlflow.set_logged_model_tags(model_info.model_id, all_tags)
        
        # Set run tags
        mlflow.set_tags(all_tags)
        
        logger.info(f"Model logged: {model_name}")
        logger.info(f"Run ID: {run.info.run_id}")
        if registered_model_name:
            logger.info(f"Registered model: {registered_model_name}")
        
        return model_info


def evaluate_logged_model(
    model_uri: str,
    eval_data,
    targets: str,
    model_type: str = "classifier",
    extra_metrics: Optional[List] = None
) -> Dict[str, Any]:
    """
    Evaluate a logged model using mlflow.models.evaluate (MLflow 3.0).
    
    Note: mlflow.evaluate is DEPRECATED in MLflow 3.0.
    Use mlflow.models.evaluate for traditional ML models.
    
    Args:
        model_uri: URI of the logged model
        eval_data: Evaluation dataset (pandas DataFrame)
        targets: Name of the target column
        model_type: Type of model (classifier, regressor)
        extra_metrics: Additional custom metrics
        
    Returns:
        Evaluation results dictionary
    """
    # MLflow 3.0: Use mlflow.models.evaluate instead of mlflow.evaluate
    results = mlflow.models.evaluate(
        model=model_uri,
        data=eval_data,
        targets=targets,
        model_type=model_type,
        extra_metrics=extra_metrics,
    )
    
    logger.info(f"Model evaluation complete for: {model_uri}")
    logger.info(f"Metrics: {results.metrics}")
    
    return results


def get_latest_model_version(config: MLflowConfig, model_name: str) -> Optional[int]:
    """
    Get the latest version number of a registered model.
    
    Args:
        config: MLflow configuration
        model_name: Short model name
        
    Returns:
        Latest version number or None if model doesn't exist
    """
    client = MlflowClient(registry_uri="databricks-uc")
    full_name = config.get_registered_model_name(model_name)
    
    try:
        versions = client.search_model_versions(f"name='{full_name}'")
        if versions:
            return max(int(v.version) for v in versions)
        return None
    except Exception as e:
        logger.warning(f"Could not get model version: {e}")
        return None


def load_model_for_inference(config: MLflowConfig, model_name: str, version: Optional[int] = None):
    """
    Load a model from Unity Catalog for inference.
    
    Args:
        config: MLflow configuration
        model_name: Short model name
        version: Specific version to load (latest if None)
        
    Returns:
        Loaded model
    """
    full_name = config.get_registered_model_name(model_name)
    
    if version is None:
        version = get_latest_model_version(config, model_name)
        if version is None:
            raise ValueError(f"No versions found for model: {full_name}")
    
    model_uri = f"models:/{full_name}/{version}"
    logger.info(f"Loading model: {model_uri}")
    
    return mlflow.pyfunc.load_model(model_uri)






