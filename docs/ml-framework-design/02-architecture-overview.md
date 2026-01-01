# 02 - Architecture Overview

## System Architecture

The ML system follows a layered architecture that separates concerns and enables scalability:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ML SYSTEM ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONSUMPTION LAYER                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ Dashboards  │  │ Metric Views│  │ Genie Spaces│  │   Alerts   │  │   │
│  │  │             │  │             │  │             │  │            │  │   │
│  │  │ Visualize   │  │ Business    │  │ Natural     │  │ Threshold  │  │   │
│  │  │ predictions │  │ KPIs        │  │ language    │  │ monitoring │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    INFERENCE LAYER                                    │   │
│  │                                                                       │   │
│  │  ┌───────────────────────────────────────────────────────────────┐   │   │
│  │  │ Prediction Tables (25 tables)                                  │   │   │
│  │  │                                                                │   │   │
│  │  │ cost_anomaly_predictions, budget_forecast_predictions,        │   │   │
│  │  │ security_threat_predictions, failure_predictions, ...          │   │   │
│  │  └───────────────────────────────────────────────────────────────┘   │   │
│  │                                                                       │   │
│  │  Process: ml_inference_pipeline → fe.score_batch() → Delta tables   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MODEL LAYER                                        │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ Unity Catalog Model Registry                                    │ │   │
│  │  │                                                                 │ │   │
│  │  │ ${catalog}.${feature_schema}.{model_name}                       │ │   │
│  │  │ • 25 registered models                                          │ │   │
│  │  │ • Versioning and staging                                        │ │   │
│  │  │ • Signatures and lineage                                        │ │   │
│  │  │ • Feature lookup metadata embedded                              │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                       │   │
│  │  Process: ml_training_pipeline → fe.log_model() → Registry           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FEATURE LAYER                                      │   │
│  │                                                                       │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐│   │
│  │  │   cost    │ │ security  │ │performance│ │reliability│ │ quality ││   │
│  │  │ _features │ │ _features │ │ _features │ │ _features │ │_features││   │
│  │  │           │ │           │ │           │ │           │ │         ││   │
│  │  │ ~2.7K rows│ │ ~625K rows│ │ ~10K rows │ │ ~435K rows│ │ ~100    ││   │
│  │  │ PK: ws+dt │ │ PK: usr+dt│ │ PK: wh+dt │ │ PK: job+dt│ │ PK:cat+ ││   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └─────────┘│   │
│  │                                                                       │   │
│  │  Process: ml_feature_pipeline → aggregate/transform → Delta tables   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DATA LAYER (Gold)                                  │   │
│  │                                                                       │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐│   │
│  │  │fact_usage │ │fact_audit │ │fact_query │ │fact_job   │ │info_    ││   │
│  │  │           │ │_logs      │ │_history   │ │_run_timel │ │schema   ││   │
│  │  │           │ │           │ │           │ │           │ │         ││   │
│  │  │ Billing   │ │ Audit     │ │ Query     │ │ Job runs  │ │ Table   ││   │
│  │  │ data      │ │ events    │ │ metrics   │ │ history   │ │ metadata││   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └─────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Architecture

### Three-Pipeline System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE EXECUTION ORDER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Prerequisites: Gold layer tables must exist and be populated               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. FEATURE PIPELINE (ml_feature_pipeline)                           │   │
│  │    ─────────────────────────────────────────────────────────────   │   │
│  │                                                                      │   │
│  │    Purpose: Create and refresh feature tables                        │   │
│  │                                                                      │   │
│  │    Input:   Gold layer tables (fact_usage, fact_audit_logs, etc.)   │   │
│  │    Output:  5 feature tables with PRIMARY KEY constraints            │   │
│  │                                                                      │   │
│  │    Script:  src/ml/features/create_feature_tables.py                │   │
│  │    Schedule: Daily at 2:00 AM                                        │   │
│  │    Duration: ~15 minutes                                             │   │
│  │                                                                      │   │
│  │    Dependencies: None (runs after Gold layer refresh)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. TRAINING PIPELINE (ml_training_pipeline)                         │   │
│  │    ─────────────────────────────────────────────────────────────   │   │
│  │                                                                      │   │
│  │    Purpose: Train all 25 models and register in Unity Catalog        │   │
│  │                                                                      │   │
│  │    Input:   Feature tables (via FeatureLookup)                       │   │
│  │    Output:  25 registered models with feature metadata               │   │
│  │                                                                      │   │
│  │    Scripts: src/ml/{domain}/train_*.py (25 scripts)                 │   │
│  │    Schedule: Daily at 3:00 AM (or weekly)                            │   │
│  │    Duration: ~2-4 hours (parallel execution)                         │   │
│  │                                                                      │   │
│  │    Dependencies: Feature pipeline must complete first                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. INFERENCE PIPELINE (ml_inference_pipeline)                       │   │
│  │    ─────────────────────────────────────────────────────────────   │   │
│  │                                                                      │   │
│  │    Purpose: Generate predictions using trained models                │   │
│  │                                                                      │   │
│  │    Input:   Feature tables (lookup keys only) + trained models       │   │
│  │    Output:  25 prediction tables                                     │   │
│  │                                                                      │   │
│  │    Script:  src/ml/inference/batch_inference_all_models.py          │   │
│  │    Schedule: Daily at 4:00 AM                                        │   │
│  │    Duration: ~30-60 minutes                                          │   │
│  │                                                                      │   │
│  │    Dependencies: Training pipeline must complete first               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Technologies

| Layer | Technology | Purpose |
|---|---|---|
| **Data Storage** | Delta Lake | ACID transactions, time travel, versioning |
| **Governance** | Unity Catalog | Access control, lineage, discovery |
| **Feature Store** | Feature Engineering (UC) | Feature management, automatic lookup |
| **Training** | scikit-learn, XGBoost | Model algorithms |
| **Tracking** | MLflow | Experiments, metrics, artifacts |
| **Registry** | Unity Catalog Models | Model versioning, staging, governance |
| **Compute** | Serverless | Auto-scaling, cost-efficient |
| **Orchestration** | Asset Bundles | Infrastructure-as-code |

### Library Versions

```python
# Databricks Runtime 15.4 LTS ML includes:
{
    "python": "3.11.x",
    "spark": "3.5.x",
    "delta": "3.1.x",
    "mlflow": "2.14.x",  # Upgrade to 3.1+ recommended
    "scikit-learn": "1.3.x",
    "xgboost": "2.0.x",
    "pandas": "2.0.x",
    "numpy": "1.24.x"
}

# Additional requirements (job-level)
"databricks-feature-engineering"  # Latest
"PyYAML>=6.0"                     # For config files
```

## Data Model

### Feature Tables Schema

```sql
-- Cost Features (workspace-date level)
cost_features (
    workspace_id STRING NOT NULL,       -- PK1
    usage_date DATE NOT NULL,           -- PK2
    daily_dbu DOUBLE,
    daily_cost DOUBLE,
    avg_dbu_7d DOUBLE,
    avg_dbu_30d DOUBLE,
    dbu_change_pct_1d DOUBLE,
    dbu_change_pct_7d DOUBLE,
    z_score_7d DOUBLE,
    serverless_adoption_ratio DOUBLE,
    jobs_on_all_purpose_cost DOUBLE,
    all_purpose_inefficiency_ratio DOUBLE,
    potential_job_cluster_savings DOUBLE,
    is_weekend BOOLEAN,
    day_of_week INT,
    -- PRIMARY KEY (workspace_id, usage_date)
)

-- Security Features (user-date level)
security_features (
    user_id STRING NOT NULL,            -- PK1
    event_date DATE NOT NULL,           -- PK2
    event_count BIGINT,
    tables_accessed BIGINT,
    failed_auth_count BIGINT,
    unique_source_ips BIGINT,
    off_hours_events BIGINT,
    lateral_movement_risk DOUBLE,
    is_activity_burst BOOLEAN,
    -- PRIMARY KEY (user_id, event_date)
)

-- Performance Features (warehouse-date level)
performance_features (
    warehouse_id STRING NOT NULL,       -- PK1
    query_date DATE NOT NULL,           -- PK2
    query_count BIGINT,
    avg_duration_ms DOUBLE,
    p50_duration_ms DOUBLE,
    p95_duration_ms DOUBLE,
    p99_duration_ms DOUBLE,
    spill_rate DOUBLE,
    error_rate DOUBLE,
    total_bytes_read BIGINT,
    read_write_ratio DOUBLE,
    avg_query_count_7d DOUBLE,
    is_weekend BOOLEAN,
    -- PRIMARY KEY (warehouse_id, query_date)
)

-- Reliability Features (job-date level)
reliability_features (
    job_id STRING NOT NULL,             -- PK1
    run_date DATE NOT NULL,             -- PK2
    total_runs BIGINT,
    avg_duration_sec DOUBLE,
    success_rate DOUBLE,
    failure_rate DOUBLE,
    duration_cv DOUBLE,
    rolling_failure_rate_30d DOUBLE,
    rolling_avg_duration_30d DOUBLE,
    total_failures_30d BIGINT,
    prev_day_failed BOOLEAN,
    repair_runs BIGINT,
    rolling_repair_rate_30d DOUBLE,
    is_weekend BOOLEAN,
    day_of_week INT,
    max_duration_sec DOUBLE,
    -- PRIMARY KEY (job_id, run_date)
)

-- Quality Features (catalog-date level)
quality_features (
    catalog_name STRING NOT NULL,       -- PK1
    snapshot_date DATE NOT NULL,        -- PK2
    table_count BIGINT,
    column_count BIGINT,
    nullable_column_ratio DOUBLE,
    avg_columns_per_table DOUBLE,
    -- PRIMARY KEY (catalog_name, snapshot_date)
)
```

### Prediction Tables Schema

All prediction tables follow a standard schema:

```sql
{model}_predictions (
    -- Primary key columns from feature table
    {pk_column_1} {type} NOT NULL,
    {pk_column_2} {type} NOT NULL,
    
    -- Prediction columns (vary by model type)
    prediction DOUBLE,                  -- Main prediction value
    is_anomaly INT,                     -- For anomaly detection
    probability DOUBLE,                 -- For classification
    anomaly_score DOUBLE,               -- For anomaly detection
    
    -- Metadata
    model_version INT,                  -- Version of model used
    model_name STRING,                  -- Name of model
    scored_at TIMESTAMP                 -- When scored
)
```

## Component Interactions

### Training Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRAINING DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CREATE BASE DATAFRAME (with label)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ base_df = spark.table(feature_table)                                │   │
│  │   .select("pk1", "pk2", F.col("label").cast("double"))              │   │
│  │   .filter(F.col("pk1").isNotNull())                                 │   │
│  │   .distinct()                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  2. DEFINE FEATURE LOOKUPS                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ feature_lookups = [                                                  │   │
│  │     FeatureLookup(                                                   │   │
│  │         table_name=f"{catalog}.{schema}.{feature_table}",           │   │
│  │         feature_names=["feat1", "feat2", ...],                      │   │
│  │         lookup_key=["pk1", "pk2"]                                   │   │
│  │     )                                                                │   │
│  │ ]                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  3. CREATE TRAINING SET                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ training_set = fe.create_training_set(                              │   │
│  │     df=base_df,                                                      │   │
│  │     feature_lookups=feature_lookups,                                │   │
│  │     label="label",                                                   │   │
│  │     exclude_columns=["pk1", "pk2"]                                  │   │
│  │ )                                                                    │   │
│  │ training_df = training_set.load_df()                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  4. TRAIN MODEL                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ X_train = training_df[feature_names].toPandas()                     │   │
│  │ y_train = training_df[label_col].toPandas()                         │   │
│  │ model = GradientBoostingRegressor()                                  │   │
│  │ model.fit(X_train, y_train)                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  5. LOG MODEL WITH FEATURE METADATA                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ fe.log_model(                                                        │   │
│  │     model=model,                                                     │   │
│  │     artifact_path="model",                                           │   │
│  │     flavor=mlflow.sklearn,                                           │   │
│  │     training_set=training_set,  # ← Embeds feature lookup metadata  │   │
│  │     registered_model_name=f"{catalog}.{schema}.{model_name}",       │   │
│  │     signature=signature,                                             │   │
│  │     input_example=input_example                                      │   │
│  │ )                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Inference Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INFERENCE DATA FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. PREPARE SCORING DATAFRAME (keys only)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ scoring_df = spark.table(feature_table)                             │   │
│  │   .select("pk1", "pk2")  # Only lookup keys, NO features!           │   │
│  │   .distinct()                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  2. SCORE WITH AUTOMATIC FEATURE RETRIEVAL                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ # fe.score_batch automatically:                                      │   │
│  │ # 1. Loads model from registry                                       │   │
│  │ # 2. Reads feature lookup metadata from model                        │   │
│  │ # 3. Joins features from feature tables                              │   │
│  │ # 4. Applies model                                                   │   │
│  │                                                                       │   │
│  │ predictions_df = fe.score_batch(                                     │   │
│  │     model_uri=f"models:/{catalog}.{schema}.{model}/{version}",      │   │
│  │     df=scoring_df                                                    │   │
│  │ )                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  3. SAVE PREDICTIONS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ predictions_df                                                       │   │
│  │   .withColumn("model_version", lit(version))                         │   │
│  │   .withColumn("model_name", lit(model_name))                         │   │
│  │   .withColumn("scored_at", current_timestamp())                      │   │
│  │   .write.mode("overwrite")                                           │   │
│  │   .saveAsTable(f"{catalog}.{schema}.{model}_predictions")           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Organization

```
DatabricksHealthMonitor/
├── src/
│   └── ml/
│       ├── features/
│       │   └── create_feature_tables.py      # Feature pipeline script
│       │
│       ├── cost/                             # Cost domain models
│       │   ├── train_cost_anomaly.py
│       │   ├── train_budget_forecaster.py
│       │   ├── train_job_cost_optimizer.py
│       │   ├── train_chargeback_attribution.py
│       │   ├── train_commitment_recommender.py
│       │   └── train_tag_recommender.py
│       │
│       ├── security/                         # Security domain models
│       │   ├── train_threat_detector.py
│       │   ├── train_exfiltration_detector.py
│       │   ├── train_privilege_escalation.py
│       │   └── train_user_behavior_baseline.py
│       │
│       ├── performance/                      # Performance domain models
│       │   ├── train_query_forecaster.py
│       │   ├── train_warehouse_optimizer.py
│       │   ├── train_regression_detector.py
│       │   ├── train_cache_hit_predictor.py
│       │   ├── train_cluster_capacity_planner.py
│       │   ├── train_dbr_migration_risk_scorer.py
│       │   └── train_query_optimization_recommender.py
│       │
│       ├── reliability/                      # Reliability domain models
│       │   ├── train_failure_predictor.py
│       │   ├── train_duration_forecaster.py
│       │   ├── train_sla_breach_predictor.py
│       │   ├── train_retry_success_predictor.py
│       │   └── train_pipeline_health_scorer.py
│       │
│       ├── quality/                          # Quality domain models
│       │   ├── train_drift_detector.py
│       │   ├── train_schema_change_predictor.py
│       │   └── train_freshness_predictor.py
│       │
│       └── inference/
│           └── batch_inference_all_models.py # Inference pipeline script
│
├── resources/
│   └── ml/
│       ├── ml_feature_pipeline.yml           # Feature job definition
│       ├── ml_training_pipeline.yml          # Training job definition
│       └── ml_inference_pipeline.yml         # Inference job definition
│
└── docs/
    └── ml-framework-design/                  # This documentation
        ├── 00-index.md
        ├── 01-introduction.md
        ├── 02-architecture-overview.md
        └── ...
```

## Security and Governance

### Unity Catalog Integration

| Aspect | Implementation |
|---|---|
| **Access Control** | Table-level grants via Unity Catalog |
| **Lineage** | Automatic tracking: Gold → Features → Models → Predictions |
| **Auditing** | All model operations logged |
| **Discovery** | Models searchable in catalog browser |
| **Versioning** | Automatic version management |

### Data Classification

| Table Type | Classification | Access |
|---|---|---|
| Feature tables | Internal | Data engineers + ML engineers |
| Models | Internal | ML engineers |
| Predictions | Internal | All analysts |

## Next Steps

- **[03-Feature Engineering](03-feature-engineering.md)**: Deep dive into feature table design
- **[04-Model Training](04-model-training.md)**: Training patterns and best practices
- **[16-Implementation Guide](16-implementation-guide.md)**: Step-by-step setup

