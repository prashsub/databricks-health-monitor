# Appendix C - References

## Official Databricks Documentation

### Feature Engineering
- [Unity Catalog Feature Engineering Overview](https://docs.databricks.com/en/machine-learning/feature-store/uc/index.html)
- [Create Feature Tables](https://docs.databricks.com/en/machine-learning/feature-store/uc/feature-tables-uc.html)
- [FeatureLookup API](https://docs.databricks.com/en/machine-learning/feature-store/uc/train-models-with-feature-store-uc.html)
- [Feature Engineering Client API](https://docs.databricks.com/en/machine-learning/feature-store/uc/api-reference.html)
- [Score Batch with Feature Lookups](https://docs.databricks.com/en/machine-learning/feature-store/uc/score-batch.html)

### MLflow
- [MLflow on Databricks Overview](https://docs.databricks.com/en/mlflow/index.html)
- [Unity Catalog Model Registry](https://docs.databricks.com/en/mlflow/models-in-uc.html)
- [Model Signatures](https://mlflow.org/docs/latest/model/signatures.html)
- [Experiment Tracking](https://docs.databricks.com/en/mlflow/tracking.html)
- [MLflow Autologging](https://docs.databricks.com/en/mlflow/tracking-autolog.html)

### Databricks Asset Bundles
- [Asset Bundles Overview](https://docs.databricks.com/en/dev-tools/bundles/index.html)
- [Bundle Resources Reference](https://docs.databricks.com/en/dev-tools/bundles/resources.html)
- [Jobs Configuration](https://docs.databricks.com/en/dev-tools/bundles/jobs.html)
- [Serverless Compute for Bundles](https://docs.databricks.com/en/dev-tools/bundles/serverless.html)

### Unity Catalog
- [Unity Catalog Overview](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [Table Constraints](https://docs.databricks.com/en/tables/constraints.html)
- [Managed vs External Tables](https://docs.databricks.com/en/data-governance/unity-catalog/create-tables.html)

### Lakehouse Monitoring
- [Lakehouse Monitoring Overview](https://docs.databricks.com/en/lakehouse-monitoring/index.html)
- [Inference Tables](https://docs.databricks.com/en/lakehouse-monitoring/inference-tables.html)
- [Custom Metrics](https://docs.databricks.com/en/lakehouse-monitoring/custom-metrics.html)

## MLflow Python API

### Core Classes
```python
# MLflow Client
from mlflow import MlflowClient
client = MlflowClient()

# Feature Engineering
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
fe = FeatureEngineeringClient()

# Signatures
from mlflow.models.signature import infer_signature, ModelSignature
from mlflow.types import ColSpec, DataType, Schema
```

### Key Methods

| Class | Method | Purpose |
|---|---|---|
| `FeatureEngineeringClient` | `create_training_set()` | Join features to base DataFrame |
| `FeatureEngineeringClient` | `log_model()` | Register model with feature metadata |
| `FeatureEngineeringClient` | `score_batch()` | Inference with auto feature lookup |
| `MlflowClient` | `search_model_versions()` | List model versions |
| `MlflowClient` | `get_run()` | Get experiment run details |
| `mlflow` | `set_experiment()` | Set active experiment |
| `mlflow` | `start_run()` | Start tracking run |
| `mlflow` | `log_params()` | Log hyperparameters |
| `mlflow` | `log_metrics()` | Log evaluation metrics |

## Scikit-learn Algorithms

### Regression
- [GradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html)
- [RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)

### Classification
- [XGBClassifier](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier)
- [RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [DummyClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html)

### Anomaly Detection
- [IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)

### Metrics
- [sklearn.metrics module](https://scikit-learn.org/stable/modules/classes.html#module-sklearn.metrics)

## Project-Specific Documentation

### Cursor Rules
- `/.cursor/rules/ml/27-mlflow-mlmodels-patterns.mdc` - Complete ML patterns
- `/.cursor/rules/common/02-databricks-asset-bundles.mdc` - DAB patterns
- `/.cursor/rules/common/03-schema-management-patterns.mdc` - Schema patterns

### Implementation Files
- `src/ml/features/create_feature_tables.py` - Feature table creation
- `src/ml/inference/batch_inference_all_models.py` - Batch scoring
- `src/ml/{domain}/train_{model}.py` - Individual training scripts

### Job Configuration
- `resources/ml/ml_feature_pipeline_job.yml` - Feature pipeline
- `resources/ml/ml_training_pipeline_job.yml` - Training pipeline
- `resources/ml/ml_inference_pipeline_job.yml` - Inference pipeline

## External Resources

### Best Practices
- [Databricks ML Development Best Practices](https://docs.databricks.com/en/machine-learning/ml-development-best-practices.html)
- [MLOps Guide](https://docs.databricks.com/en/machine-learning/mlops/index.html)
- [Feature Store Best Practices](https://docs.databricks.com/en/machine-learning/feature-store/uc/best-practices.html)

### Examples
- [Databricks ML Examples GitHub](https://github.com/databricks/databricks-ml-examples)
- [MLflow Examples](https://github.com/mlflow/mlflow/tree/master/examples)
- [Feature Store Examples](https://github.com/databricks/feature-store-examples)

## Version Information

| Component | Version | Notes |
|---|---|---|
| Databricks Runtime | 15.4 LTS ML | Recommended |
| MLflow | 2.x+ | UC support |
| scikit-learn | 1.3+ | Algorithm support |
| XGBoost | 2.0+ | Classification |
| Python | 3.10+ | Language version |

