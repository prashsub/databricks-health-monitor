"""
TRAINING MATERIAL: ML Inference Package
=======================================

This package contains batch inference scripts for scoring data using
trained ML models from Unity Catalog.

BATCH INFERENCE ARCHITECTURE:
-----------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  FEATURE TABLES (UC)         MODELS (UC)              PREDICTIONS       │
│  ─────────────────────       ────────────             ───────────       │
│  cost_features               cost_anomaly_detector    cost_predictions  │
│  security_features           security_threat_detect   security_preds    │
│  performance_features        query_optimizer          perf_predictions  │
│  reliability_features        job_failure_predictor    reliability_preds │
│  quality_features            drift_detector           quality_preds     │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  fe.score_batch(model_uri, features_df)                           │  │
│  │  ─────────────────────────────────────────                        │  │
│  │  1. Loads model from UC registry                                  │  │
│  │  2. Joins features via FeatureLookup (built into model)          │  │
│  │  3. Applies model.predict()                                       │  │
│  │  4. Returns DataFrame with predictions                            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

KEY FILES:
----------

- batch_inference_all_models.py: Main orchestrator for all 25 models
- score_cost_anomalies.py: Standalone cost anomaly scoring
- score_tag_recommender.py: Specialized tag recommendation scoring

FEATURE STORE INFERENCE:
------------------------

The key advantage of using Feature Store for inference:

    # Training: FeatureLookup is LOGGED with the model
    fe.log_model(model, training_set=training_set, ...)

    # Inference: Just provide primary keys, features auto-joined
    predictions = fe.score_batch(
        model_uri="models:/catalog.schema.model/1",
        df=keys_df  # Only needs workspace_id, usage_date
    )

No need to manually join features at inference time!
"""






