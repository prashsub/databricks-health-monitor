"""
TRAINING MATERIAL: ML Features Package
======================================

This package creates and manages feature tables for all 5 agent domains,
following Unity Catalog Feature Engineering best practices.

FEATURE TABLE ARCHITECTURE:
---------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  GOLD LAYER                      FEATURE TABLES                         │
│  ───────────                     ──────────────                         │
│  fact_usage           ──▶        cost_features                          │
│  fact_audit_logs      ──▶        security_features                      │
│  fact_query_history   ──▶        performance_features                   │
│  fact_job_run_timeline──▶        reliability_features                   │
│  fact_table_lineage   ──▶        quality_features                       │
│                                                                         │
│  Aggregations:                                                          │
│  - Daily rollups (SUM, AVG, COUNT)                                      │
│  - Rolling windows (7d, 30d)                                            │
│  - Derived ratios (failure_rate, serverless_pct)                        │
└─────────────────────────────────────────────────────────────────────────┘

FEATURE ENGINEERING PATTERNS:
-----------------------------

1. PRIMARY KEY DEFINITION
   Every feature table needs explicit primary keys for Feature Store:
   
   ```python
   spark.sql(f'''
       ALTER TABLE {feature_table}
       ADD CONSTRAINT pk_{table_name} PRIMARY KEY (workspace_id, usage_date)
   ''')
   ```

2. DATA TYPE CONSISTENCY
   All numeric features must be DOUBLE for ML compatibility:
   
   ```python
   .withColumn("daily_cost", F.col("daily_cost").cast("double"))
   ```

3. NULL HANDLING
   Replace NaN/NULL with 0 for ML models:
   
   ```python
   .withColumn("feature", F.coalesce(F.col("feature"), F.lit(0.0)))
   ```

4. ROLLING WINDOWS
   Use window functions for temporal features:
   
   ```python
   window_7d = Window.partitionBy("workspace_id").orderBy("date").rowsBetween(-6, 0)
   .withColumn("cost_7d_avg", F.avg("daily_cost").over(window_7d))
   ```

FEATURE TABLE INVENTORY:
------------------------

| Table | Domain | Primary Keys | Source Tables |
|-------|--------|--------------|---------------|
| cost_features | Cost | workspace_id, usage_date | fact_usage |
| security_features | Security | workspace_id, event_date | fact_audit_logs |
| performance_features | Performance | workspace_id, query_date | fact_query_history |
| reliability_features | Reliability | workspace_id, job_id, run_date | fact_job_run_timeline |
| quality_features | Quality | table_id, snapshot_date | fact_table_lineage |

ML Features Package - Contains feature table creation scripts for each agent domain
"""

from .create_feature_tables import create_all_feature_tables

__all__ = ["create_all_feature_tables"]






