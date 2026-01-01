# ML Framework Design Documentation

## Overview

This documentation suite provides comprehensive architecture, implementation, and best practices guidance for **Classical Machine Learning on Databricks**. The system showcases Unity Catalog Feature Engineering, MLflow integration, and production ML patterns through 25 models across 5 domains.

> **This documentation serves dual purposes:**
> 1. **Project Documentation**: Complete reference for the Databricks Health Monitor ML system
> 2. **Training Material**: Best practices guide for ML on Databricks applicable to any ML project

## Architecture Principle

> **All models use Unity Catalog Feature Engineering for training/serving consistency.**
> Features are computed once, stored in feature tables, and automatically retrieved at inference.
> Models are registered in Unity Catalog for governance, versioning, and lineage.

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 01 | [Introduction](01-introduction.md) | Purpose, scope, prerequisites, best practices matrix |
| 02 | [Architecture Overview](02-architecture-overview.md) | System architecture, data flows, technology stack |
| 03 | [Feature Engineering](03-feature-engineering.md) | Unity Catalog Feature Engineering deep dive |
| 04 | [Model Training](04-model-training.md) | Training patterns, algorithms, MLflow signatures |
| 05 | [Model Registry](05-model-registry.md) | Unity Catalog Model Registry patterns |
| 06 | [Batch Inference](06-batch-inference.md) | Production inference with fe.score_batch |
| 07 | [Model Catalog](07-model-catalog.md) | All 25 models across 5 domains |
| 08 | [MLflow Best Practices](08-mlflow-best-practices.md) | Experiment tracking, logging patterns |
| 09 | [Deployment](09-deployment.md) | Databricks Asset Bundles, job orchestration |
| 10 | [Troubleshooting](10-troubleshooting.md) | Common errors and solutions |
| 11 | [Model Monitoring](11-model-monitoring.md) | Drift detection, retraining triggers |

## Appendices

| # | Document | Description |
|---|----------|-------------|
| A | [Code Examples](appendices/A-code-examples.md) | Complete working code snippets |
| B | [Cursor Rule Summary](appendices/B-cursor-rule.md) | Key patterns from ML cursor rule |
| C | [References](appendices/C-references.md) | Official documentation links |

## ML System Summary

```
ML SYSTEM ARCHITECTURE
├── FEATURE LAYER (5 Feature Tables)
│   ├── cost_features         # Daily DBU, cost, trends
│   ├── security_features     # Event counts, risk scores
│   ├── performance_features  # Query metrics, latencies
│   ├── reliability_features  # Job stats, failure rates
│   └── quality_features      # Table stats, freshness
│
├── MODEL LAYER (25 Models across 5 Domains)
│   ├── COST (6)              # Anomaly, forecaster, optimizer, chargeback, commitment, tag
│   ├── SECURITY (4)          # Threat, access, compliance, permission
│   ├── PERFORMANCE (7)       # Query forecast, warehouse, regression, cache, capacity, sizing, optimization
│   ├── RELIABILITY (5)       # Failure, duration, SLA, retry, health
│   └── QUALITY (3)           # Drift, schema change, schema evolution
│
├── INFERENCE LAYER (25 Prediction Tables)
│   └── {model_name}_predictions  # Scored predictions with timestamps
│
└── ORCHESTRATION LAYER (3 Jobs)
    ├── ml_feature_pipeline   # Creates feature tables
    ├── ml_training_pipeline  # Trains all 25 models
    └── ml_inference_pipeline # Generates predictions
```

## Quick Start

1. **Understand the Architecture**: Start with [02-Architecture Overview](02-architecture-overview.md)
2. **Learn Feature Engineering**: Read [03-Feature Engineering](03-feature-engineering.md)
3. **Review Training Patterns**: See [04-Model Training](04-model-training.md)
4. **Understand Deployment**: Check [09-Deployment](09-deployment.md)
5. **Debug Issues**: Reference [10-Troubleshooting](10-troubleshooting.md)

## Best Practices Showcased

| # | Best Practice | Implementation | Document |
|---|---------------|----------------|----------|
| 1 | **Unity Catalog Feature Engineering** | FeatureLookup + create_training_set | [03-Feature Engineering](03-feature-engineering.md) |
| 2 | **MLflow Model Signatures** | Explicit input/output schemas for UC | [04-Model Training](04-model-training.md) |
| 3 | **Unity Catalog Model Registry** | Governance, versioning, lineage | [05-Model Registry](05-model-registry.md) |
| 4 | **Batch Inference with fe.score_batch** | Automatic feature retrieval | [06-Batch Inference](06-batch-inference.md) |
| 5 | **Serverless Compute** | Cost-efficient, auto-scaling | [09-Deployment](09-deployment.md) |
| 6 | **MLflow Experiment Tracking** | Parameters, metrics, artifacts | [08-MLflow Best Practices](08-mlflow-best-practices.md) |
| 7 | **Model Monitoring** | Drift detection, quality metrics | [11-Model Monitoring](11-model-monitoring.md) |
| 8 | **Label Type Casting** | DOUBLE for regression, INT for classification | [04-Model Training](04-model-training.md) |
| 9 | **Anomaly Detection** | Isolation Forest for unsupervised | [07-Model Catalog](07-model-catalog.md) |
| 10 | **Time Series Forecasting** | Gradient Boosting Regressor | [04-Model Training](04-model-training.md) |
| 11 | **Databricks Asset Bundles** | Infrastructure-as-code | [09-Deployment](09-deployment.md) |
| 12 | **Production Debugging** | Structured logging, error handling | [10-Troubleshooting](10-troubleshooting.md) |

## Model Statistics

| Domain | Models | Algorithms Used | Primary Use Cases |
|---|:---:|---|---|
| 💰 Cost | 6 | Isolation Forest, GBR, XGBoost, RF+TF-IDF | Anomaly detection, forecasting, optimization |
| 🔒 Security | 4 | Isolation Forest, XGBoost, Random Forest | Threat detection, access patterns, compliance |
| ⚡ Performance | 7 | GBR, Isolation Forest, XGBoost | Query optimization, capacity planning |
| 🔄 Reliability | 5 | XGBoost, GBR, Random Forest | Failure prediction, SLA monitoring |
| 📊 Quality | 3 | Isolation Forest, Random Forest, XGBoost | Drift detection, schema change prediction |

## Technology Stack

| Component | Technology | Version |
|---|---|---|
| Feature Store | Unity Catalog Feature Engineering | Latest |
| Model Training | scikit-learn, XGBoost | 1.3+, 2.0+ |
| Experiment Tracking | MLflow | 2.x+ |
| Model Registry | Unity Catalog | Latest |
| Compute | Databricks Serverless | Environment v4 |
| Orchestration | Databricks Asset Bundles | Latest |
| Data Format | Delta Lake | Latest |

## Critical Patterns Summary

### Non-Negotiable Rules

1. **ALWAYS cast label columns** to DOUBLE (regression) or INT (classification) in `base_df` before `fe.create_training_set()`

2. **ALWAYS use `fe.log_model()`** with `training_set` parameter to embed feature lookup metadata

3. **ALWAYS provide `signature` and `input_example`** to `fe.log_model()` - Unity Catalog requires both

4. **ALWAYS use float64** for `input_example`: `X_train.head(5).astype('float64')`

5. **NEVER use DECIMAL types** in training data - cast to DOUBLE before creating signature

6. **ALWAYS use `X_train` consistently** - don't mix `X` and `X_train` variable names

7. **ALWAYS return `X_train`** from prepare functions for signature creation

8. **ALWAYS verify feature names** match actual feature table columns before training

See [Appendix B - Cursor Rule](appendices/B-cursor-rule.md) for the full pattern reference.

## Related Documentation

- [Phase 3.1: ML Models Plan](../../plans/phase3-addendum-3.1-ml-models.md)
- [MLflow ML Patterns Cursor Rule](../../.cursor/rules/ml/27-mlflow-mlmodels-patterns.mdc)
- [Gold Layer Design](../../gold_layer_design/)
- [Databricks Asset Bundles Rule](../../.cursor/rules/common/02-databricks-asset-bundles.mdc)
- [Agent Framework Design](../agent-framework-design/00-index.md)

## Document Conventions

### Code Examples

All code examples are:
- **Production-ready**: Can be copied directly into notebooks
- **Fully typed**: Include type hints for clarity
- **Well-commented**: Explain the "why" not just the "what"
- **Tested**: Validated against Databricks Runtime 15.4+

### Diagrams

- Architecture diagrams use ASCII art and Mermaid format
- Data flow diagrams show the complete path from Gold layer to predictions
- Component diagrams show dependencies and interactions

### Configuration

- All configuration uses environment variables or widgets
- No hardcoded credentials or workspace URLs
- Supports dev/staging/prod environments via parameterization
