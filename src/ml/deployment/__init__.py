"""
TRAINING MATERIAL: ML Deployment Package
========================================

This package handles the deployment phase of ML models:
- Model registration to Unity Catalog
- Model Serving endpoint deployment
- Inference table monitoring setup

DEPLOYMENT WORKFLOW:
--------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  1. Training (ml/cost/, ml/security/, etc.)                              │
│     └── Models logged to MLflow, registered to UC                       │
│                                                                         │
│  2. Registration (register_all_models.py)                                │
│     └── Verify all models registered, set aliases ("production")        │
│                                                                         │
│  3. Endpoint Deployment (deploy_endpoints.py)                            │
│     └── Create/update Model Serving endpoints                           │
│                                                                         │
│  4. Inference Tables (automatic)                                         │
│     └── Model Serving auto-creates inference tables in UC               │
│                                                                         │
│  5. Monitoring (Lakehouse Monitoring)                                    │
│     └── Track prediction drift and data quality                         │
└─────────────────────────────────────────────────────────────────────────┘

ENDPOINT TYPES:
---------------

| Type | Latency | Scale | Use Case |
|------|---------|-------|----------|
| Real-time | <100ms | Scale-to-zero | Security alerts, cost anomalies |
| Batch | Minutes | Scheduled job | Budget forecasts, capacity plans |

KEY FILES:
----------

- register_all_models.py: Verify registration, set aliases
- deploy_endpoints.py: Create Model Serving endpoints

INFERENCE TABLES:
-----------------

Model Serving automatically logs predictions to Unity Catalog:

    catalog.schema.{endpoint_name}_inference_logs

Contains: timestamp, input features, predictions, latency
Used for: Monitoring, debugging, retraining
"""






