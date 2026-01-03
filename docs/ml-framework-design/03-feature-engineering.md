# 03 - Feature Engineering

## Overview

Unity Catalog Feature Engineering is the cornerstone of production ML on Databricks. It provides:

- **Training/Serving Consistency**: Same features used in training and inference
- **Feature Reuse**: Single feature computation powers multiple models
- **Automatic Lookup**: Features are automatically retrieved at inference
- **Governance**: Full lineage tracking through Unity Catalog

> **Critical Principle**: Features are computed ONCE in feature tables, then LOOKED UP during training and inference. This eliminates feature skew.

## Why Feature Engineering?

### The Problem Without Feature Engineering

```python
# ❌ WRONG: Manual feature computation at training and inference
# This leads to feature skew!

# Training (version 1)
def compute_features_v1(df):
    return df.withColumn("avg_cost", F.col("total") / F.col("count"))

# Later, inference (version 2 - bug introduced!)
def compute_features_v2(df):
    return df.withColumn("avg_cost", F.col("total") / (F.col("count") + 1))  # Bug!
```

### The Solution With Feature Engineering

```python
# ✅ CORRECT: Compute once, look up everywhere

# 1. Features computed once in feature table
spark.sql("""
    CREATE TABLE cost_features AS
    SELECT workspace_id, usage_date,
           total / count AS avg_cost
    FROM fact_usage
""")

# 2. Training: Features looked up
training_set = fe.create_training_set(base_df, feature_lookups, label)

# 3. Inference: Same features automatically retrieved
predictions = fe.score_batch(model_uri, scoring_df)
```

## Feature Table Design

### Primary Key Requirements

**Every feature table MUST have a primary key constraint:**

```python
# Feature tables require:
# 1. Primary key columns that are NOT NULL
# 2. A PRIMARY KEY constraint defined

# Example
spark.sql(f"""
    CREATE TABLE {catalog}.{schema}.cost_features (
        workspace_id STRING NOT NULL,
        usage_date DATE NOT NULL,
        daily_dbu DOUBLE,
        daily_cost DOUBLE,
        ...
        CONSTRAINT pk_cost_features PRIMARY KEY (workspace_id, usage_date)
    )
""")
```

### Handling NULL Primary Keys

**Critical**: Primary key columns cannot contain NULL values.

```python
# ❌ WRONG: Will fail with "column is nullable" error
base_df = spark.table(source).select("pk1", "pk2", "features")

# ✅ CORRECT: Filter NULLs before creating table
base_df = (spark.table(source)
           .filter(F.col("pk1").isNotNull())
           .filter(F.col("pk2").isNotNull())
           .select("pk1", "pk2", "features"))
```

### Type Consistency (CRITICAL)

**All numeric feature columns MUST be cast to DOUBLE in feature tables.**

This ensures consistency between:
1. **Feature Creation**: Spark DOUBLE type
2. **Training**: Pandas float64 type  
3. **Inference**: MLflow signature validation

```python
# ❌ WRONG: Feature table has mixed types
# INTEGER, DECIMAL types cause schema validation errors at inference

# ✅ CORRECT: Cast all numeric features to DOUBLE
from pyspark.sql.types import IntegerType, LongType, FloatType, DecimalType

def prepare_features_for_table(df: DataFrame, primary_keys: List[str]) -> DataFrame:
    """Cast all numeric columns to DOUBLE for MLflow compatibility."""
    for field in df.schema.fields:
        if field.name not in primary_keys:  # Don't cast primary keys
            if isinstance(field.dataType, (IntegerType, LongType, FloatType, DecimalType)):
                df = df.withColumn(field.name, F.col(field.name).cast("double"))
    return df
```

**Why This Matters:**
- Training scripts cast to `float64` (Python equivalent of Spark DOUBLE)
- Model signatures expect `float64` inputs
- Inference uses native Spark types from feature tables
- Type mismatch causes `Failed to enforce schema` errors

**Type Flow:**
```
Feature Table (Spark)  →  Training (Pandas)  →  Model Signature  →  Inference
     DOUBLE           →      float64        →     float64       ←    DOUBLE
          ↓                    ↓                    ↓                  ↓
       ✅ Compatible types throughout the pipeline!
```

### Feature Table Schema Pattern

```python
def create_feature_table(
    spark: SparkSession,
    catalog: str,
    schema: str,
    table_name: str,
    primary_keys: List[str],
    features_df: DataFrame,
    description: str
):
    """
    Create a feature table with proper constraints.
    
    IMPORTANT: Numeric columns are cast to DOUBLE for MLflow compatibility.
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        schema: Schema name
        table_name: Feature table name
        primary_keys: List of primary key column names
        features_df: DataFrame with features (NULLs filtered)
        description: Table description
    """
    from pyspark.sql.types import IntegerType, LongType, FloatType, DecimalType
    
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    # CRITICAL: Cast numeric columns to DOUBLE
    for field in features_df.schema.fields:
        if field.name not in primary_keys:
            if isinstance(field.dataType, (IntegerType, LongType, FloatType, DecimalType)):
                features_df = features_df.withColumn(field.name, F.col(field.name).cast("double"))
    
    # Step 1: Drop existing table
    spark.sql(f"DROP TABLE IF EXISTS {full_table_name}")
    
    # Step 2: Build column definitions with NOT NULL for PKs
    columns = []
    for field in features_df.schema.fields:
        col_def = f"{field.name} {field.dataType.simpleString()}"
        if field.name in primary_keys:
            col_def += " NOT NULL"
        columns.append(col_def)
    
    # Step 3: Create table with PK constraint
    pk_cols = ", ".join(primary_keys)
    columns_str = ",\n        ".join(columns)
    
    create_sql = f"""
        CREATE TABLE {full_table_name} (
            {columns_str},
            CONSTRAINT pk_{table_name} PRIMARY KEY ({pk_cols})
        )
        USING DELTA
        CLUSTER BY AUTO
        COMMENT '{description}'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
    """
    
    spark.sql(create_sql)
    
    # Step 4: Insert data
    features_df.write.format("delta").mode("append").saveAsTable(full_table_name)
    
    print(f"✓ Created feature table: {full_table_name}")
    print(f"  Primary keys: {pk_cols}")
    print(f"  Rows: {features_df.count():,}")
```

## Feature Table Definitions

### Cost Features

```python
def compute_cost_features(spark: SparkSession, catalog: str, gold_schema: str) -> DataFrame:
    """
    Compute cost features aggregated at workspace-date level.
    
    Primary Keys: workspace_id, usage_date
    """
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    
    return spark.sql(f"""
        WITH daily_agg AS (
            SELECT 
                workspace_id,
                DATE(usage_date) AS usage_date,
                SUM(usage_quantity) AS daily_dbu,
                SUM(list_cost) AS daily_cost,
                SUM(CASE WHEN sku_name LIKE '%SERVERLESS%' THEN list_cost ELSE 0 END) AS serverless_cost,
                SUM(CASE WHEN sku_name LIKE '%DLT%' THEN list_cost ELSE 0 END) AS dlt_cost,
                SUM(CASE WHEN sku_name LIKE '%ALL_PURPOSE%' AND usage_metadata_job_id IS NOT NULL 
                    THEN list_cost ELSE 0 END) AS jobs_on_all_purpose_cost,
                COUNT(DISTINCT CASE WHEN sku_name LIKE '%ALL_PURPOSE%' AND usage_metadata_job_id IS NOT NULL 
                    THEN usage_metadata_job_id END) AS jobs_on_all_purpose_count
            FROM {fact_usage}
            WHERE workspace_id IS NOT NULL AND usage_date IS NOT NULL
            GROUP BY workspace_id, DATE(usage_date)
        ),
        with_window AS (
            SELECT 
                *,
                AVG(daily_dbu) OVER (
                    PARTITION BY workspace_id 
                    ORDER BY usage_date 
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) AS avg_dbu_7d,
                AVG(daily_dbu) OVER (
                    PARTITION BY workspace_id 
                    ORDER BY usage_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS avg_dbu_30d,
                STDDEV(daily_dbu) OVER (
                    PARTITION BY workspace_id 
                    ORDER BY usage_date 
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) AS stddev_dbu_7d,
                LAG(daily_dbu, 1) OVER (
                    PARTITION BY workspace_id ORDER BY usage_date
                ) AS prev_day_dbu,
                LAG(daily_dbu, 7) OVER (
                    PARTITION BY workspace_id ORDER BY usage_date
                ) AS prev_week_dbu
            FROM daily_agg
        )
        SELECT 
            workspace_id,
            usage_date,
            daily_dbu,
            daily_cost,
            avg_dbu_7d,
            avg_dbu_30d,
            
            -- Change percentages
            CASE WHEN prev_day_dbu > 0 
                THEN (daily_dbu - prev_day_dbu) / prev_day_dbu * 100 
                ELSE 0 END AS dbu_change_pct_1d,
            CASE WHEN prev_week_dbu > 0 
                THEN (daily_dbu - prev_week_dbu) / prev_week_dbu * 100 
                ELSE 0 END AS dbu_change_pct_7d,
            
            -- Z-score for anomaly detection
            CASE WHEN stddev_dbu_7d > 0 
                THEN (daily_dbu - avg_dbu_7d) / stddev_dbu_7d 
                ELSE 0 END AS z_score_7d,
            
            -- Serverless adoption
            CASE WHEN daily_cost > 0 
                THEN serverless_cost / daily_cost 
                ELSE 0 END AS serverless_adoption_ratio,
            
            -- Cost breakdown
            jobs_on_all_purpose_cost,
            serverless_cost,
            dlt_cost,
            jobs_on_all_purpose_count,
            
            -- Inefficiency ratio
            CASE WHEN daily_cost > 0 
                THEN jobs_on_all_purpose_cost / daily_cost 
                ELSE 0 END AS all_purpose_inefficiency_ratio,
            
            -- Potential savings estimate
            jobs_on_all_purpose_cost * 0.3 AS potential_job_cluster_savings,
            
            -- Calendar features
            DAYOFWEEK(usage_date) IN (1, 7) AS is_weekend,
            DAYOFWEEK(usage_date) AS day_of_week
            
        FROM with_window
        WHERE workspace_id IS NOT NULL
    """)
```

### Security Features

```python
def compute_security_features(spark: SparkSession, catalog: str, gold_schema: str) -> DataFrame:
    """
    Compute security features aggregated at user-date level.
    
    Primary Keys: user_id, event_date
    """
    fact_audit = f"{catalog}.{gold_schema}.fact_audit_logs"
    
    return spark.sql(f"""
        SELECT 
            user_identity AS user_id,
            DATE(event_time) AS event_date,
            
            -- Event counts
            COUNT(*) AS event_count,
            COUNT(DISTINCT CASE WHEN action_name LIKE '%Table%' THEN request_id END) AS tables_accessed,
            
            -- Failed actions
            SUM(CASE WHEN response_status_code != 200 THEN 1 ELSE 0 END) AS failed_auth_count,
            
            -- Source diversity
            COUNT(DISTINCT source_ip_address) AS unique_source_ips,
            
            -- Off-hours activity (before 6 AM or after 8 PM)
            SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 20 THEN 1 ELSE 0 END) AS off_hours_events,
            
            -- Lateral movement risk (accessing multiple workspaces/catalogs)
            COUNT(DISTINCT request_params_workspace_id) * 0.1 AS lateral_movement_risk,
            
            -- Activity burst detection
            COUNT(*) > (SELECT AVG(cnt) * 3 FROM (
                SELECT user_identity, DATE(event_time), COUNT(*) as cnt 
                FROM {fact_audit} 
                GROUP BY 1, 2
            )) AS is_activity_burst
            
        FROM {fact_audit}
        WHERE user_identity IS NOT NULL 
          AND event_time IS NOT NULL
        GROUP BY user_identity, DATE(event_time)
    """)
```

### Performance Features

```python
def compute_performance_features(spark: SparkSession, catalog: str, gold_schema: str) -> DataFrame:
    """
    Compute performance features aggregated at warehouse-date level.
    
    Primary Keys: warehouse_id, query_date
    """
    fact_query = f"{catalog}.{gold_schema}.fact_query_history"
    
    return spark.sql(f"""
        WITH daily_stats AS (
            SELECT 
                compute_warehouse_id AS warehouse_id,
                DATE(start_time) AS query_date,
                COUNT(*) AS query_count,
                AVG(total_duration_ms) AS avg_duration_ms,
                PERCENTILE_APPROX(total_duration_ms, 0.5) AS p50_duration_ms,
                PERCENTILE_APPROX(total_duration_ms, 0.95) AS p95_duration_ms,
                PERCENTILE_APPROX(total_duration_ms, 0.99) AS p99_duration_ms,
                
                -- Spill rate
                SUM(CASE WHEN spill_to_disk_bytes > 0 THEN 1 ELSE 0 END) / COUNT(*) AS spill_rate,
                
                -- Error rate
                SUM(CASE WHEN error_message IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS error_rate,
                
                -- I/O metrics
                SUM(read_bytes) AS total_bytes_read,
                SUM(write_bytes) AS total_bytes_written,
                
                -- Read/write ratio
                CASE WHEN SUM(write_bytes) > 0 
                    THEN SUM(read_bytes) / SUM(write_bytes) 
                    ELSE SUM(read_bytes) END AS read_write_ratio
                
            FROM {fact_query}
            WHERE compute_warehouse_id IS NOT NULL 
              AND start_time IS NOT NULL
            GROUP BY compute_warehouse_id, DATE(start_time)
        )
        SELECT 
            *,
            -- Rolling averages
            AVG(query_count) OVER (
                PARTITION BY warehouse_id 
                ORDER BY query_date 
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) AS avg_query_count_7d,
            
            -- Calendar features
            DAYOFWEEK(query_date) IN (1, 7) AS is_weekend
            
        FROM daily_stats
    """)
```

### Reliability Features

```python
def compute_reliability_features(spark: SparkSession, catalog: str, gold_schema: str) -> DataFrame:
    """
    Compute reliability features aggregated at job-date level.
    
    Primary Keys: job_id, run_date
    """
    fact_job = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    
    return spark.sql(f"""
        WITH daily_stats AS (
            SELECT 
                job_id,
                DATE(start_time) AS run_date,
                COUNT(*) AS total_runs,
                AVG(duration_seconds) AS avg_duration_sec,
                MAX(duration_seconds) AS max_duration_sec,
                
                -- Success/failure rates
                SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*) AS success_rate,
                SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) / COUNT(*) AS failure_rate,
                
                -- Coefficient of variation (duration stability)
                CASE WHEN AVG(duration_seconds) > 0 
                    THEN STDDEV(duration_seconds) / AVG(duration_seconds) 
                    ELSE 0 END AS duration_cv,
                
                -- Repair runs
                SUM(CASE WHEN run_type = 'REPAIR' THEN 1 ELSE 0 END) AS repair_runs
                
            FROM {fact_job}
            WHERE job_id IS NOT NULL 
              AND start_time IS NOT NULL
            GROUP BY job_id, DATE(start_time)
        ),
        with_rolling AS (
            SELECT 
                *,
                -- Rolling failure rate
                AVG(failure_rate) OVER (
                    PARTITION BY job_id 
                    ORDER BY run_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS rolling_failure_rate_30d,
                
                -- Rolling duration
                AVG(avg_duration_sec) OVER (
                    PARTITION BY job_id 
                    ORDER BY run_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS rolling_avg_duration_30d,
                
                -- Total failures in 30 days
                SUM(CASE WHEN failure_rate > 0 THEN 1 ELSE 0 END) OVER (
                    PARTITION BY job_id 
                    ORDER BY run_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS total_failures_30d,
                
                -- Rolling repair rate
                AVG(repair_runs) OVER (
                    PARTITION BY job_id 
                    ORDER BY run_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS rolling_repair_rate_30d,
                
                -- Previous day failure
                LAG(failure_rate, 1) OVER (
                    PARTITION BY job_id ORDER BY run_date
                ) > 0 AS prev_day_failed
                
            FROM daily_stats
        )
        SELECT 
            *,
            DAYOFWEEK(run_date) IN (1, 7) AS is_weekend,
            DAYOFWEEK(run_date) AS day_of_week
        FROM with_rolling
    """)
```

## Using Feature Lookups

### Basic Pattern

```python
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

fe = FeatureEngineeringClient()

# Define which features to look up
feature_lookups = [
    FeatureLookup(
        table_name=f"{catalog}.{schema}.cost_features",
        feature_names=[
            "daily_dbu", "daily_cost", "avg_dbu_7d", "avg_dbu_30d",
            "z_score_7d", "serverless_adoption_ratio"
        ],
        lookup_key=["workspace_id", "usage_date"]
    )
]

# Create training set
training_set = fe.create_training_set(
    df=base_df,                              # Contains PKs + label
    feature_lookups=feature_lookups,         # Feature specifications
    label="daily_cost",                      # Target column
    exclude_columns=["workspace_id", "usage_date"]  # Don't include PKs in features
)

# Load as DataFrame
training_df = training_set.load_df()
```

### Column Name Mapping

**Critical**: Gold table column names may differ from feature table column names.

```python
# Common mapping issue: Gold has compute_warehouse_id, features has warehouse_id

# ❌ WRONG: Column mismatch
base_df = spark.table(fact_query).select(
    "compute_warehouse_id",  # Gold table column name
    "query_date"
)
# Error: FeatureLookup expects "warehouse_id"

# ✅ CORRECT: Map column names
base_df = (spark.table(fact_query)
           .withColumn("warehouse_id", F.col("compute_warehouse_id"))  # Map!
           .select("warehouse_id", "query_date", label))
```

### Common Column Mappings

| Gold Table Column | Feature Table Column | Reason |
|---|---|---|
| `compute_warehouse_id` | `warehouse_id` | Simplified name |
| `usage_metadata_job_id` | `job_id` | Simplified name |
| `user_identity` | `user_id` | Simplified name |

## Label Handling

### Critical: Cast Labels Before Training Set

**The most common error in Feature Engineering is not casting labels correctly.**

```python
# ❌ WRONG: DECIMAL label causes signature error
base_df = spark.table(ft).select("pk1", "pk2", "label")
# MLflow error: "signature contains only inputs"

# ✅ CORRECT: Cast label to DOUBLE (regression) or INT (classification)
base_df = spark.table(ft).select(
    "pk1", "pk2",
    F.col("label").cast("double").alias("label")  # CRITICAL!
)
```

### Label Type Reference

| Model Type | Label Type | Cast To |
|---|---|---|
| Regression | Continuous | `DOUBLE` / `float64` |
| Binary Classification | 0/1 | `INT` / `int` |
| Multi-class Classification | Integer class IDs | `INT` / `int` |
| Anomaly Detection | None (unsupervised) | N/A |

## Feature Pipeline Script

### Complete Example

```python
# Databricks notebook source

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from typing import List

# =============================================================================
# PARAMETERS
# =============================================================================

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# =============================================================================
# FEATURE TABLE CREATION
# =============================================================================

def create_feature_table(
    spark: SparkSession,
    catalog: str,
    schema: str,
    table_name: str,
    primary_keys: List[str],
    features_df: DataFrame,
    description: str
):
    """Create a feature table with PK constraints."""
    full_name = f"{catalog}.{schema}.{table_name}"
    
    print(f"\nCreating feature table: {full_name}")
    
    # Filter NULLs in PK columns
    for pk in primary_keys:
        features_df = features_df.filter(F.col(pk).isNotNull())
    
    # Drop existing
    spark.sql(f"DROP TABLE IF EXISTS {full_name}")
    
    # Build schema
    cols = []
    for field in features_df.schema.fields:
        col_def = f"`{field.name}` {field.dataType.simpleString()}"
        if field.name in primary_keys:
            col_def += " NOT NULL"
        cols.append(col_def)
    
    pk_clause = ", ".join([f"`{pk}`" for pk in primary_keys])
    
    create_sql = f"""
        CREATE TABLE {full_name} (
            {', '.join(cols)},
            CONSTRAINT pk_{table_name} PRIMARY KEY ({pk_clause})
        )
        USING DELTA
        CLUSTER BY AUTO
        COMMENT '{description}'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true'
        )
    """
    
    spark.sql(create_sql)
    features_df.write.format("delta").mode("append").saveAsTable(full_name)
    
    row_count = spark.table(full_name).count()
    print(f"✓ Created {full_name} with {row_count:,} rows")

# =============================================================================
# MAIN
# =============================================================================

def main():
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    print("=" * 80)
    print("ML FEATURE PIPELINE")
    print("=" * 80)
    
    # Create each feature table
    print("\n1. Creating cost_features...")
    cost_df = compute_cost_features(spark, catalog, gold_schema)
    create_feature_table(
        spark, catalog, feature_schema, "cost_features",
        ["workspace_id", "usage_date"], cost_df,
        "Daily cost and usage metrics by workspace"
    )
    
    print("\n2. Creating security_features...")
    security_df = compute_security_features(spark, catalog, gold_schema)
    create_feature_table(
        spark, catalog, feature_schema, "security_features",
        ["user_id", "event_date"], security_df,
        "Daily security event metrics by user"
    )
    
    # ... repeat for other feature tables
    
    print("\n" + "=" * 80)
    print("✓ FEATURE PIPELINE COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()
```

## Validation Checklist

### Feature Table Design
- [ ] Primary key columns defined
- [ ] Primary key columns are NOT NULL
- [ ] PRIMARY KEY constraint added
- [ ] NULLs filtered before insert
- [ ] Table has COMMENT description
- [ ] CLUSTER BY AUTO enabled

### Feature Lookups
- [ ] table_name uses full path: `{catalog}.{schema}.{table}`
- [ ] feature_names match actual column names
- [ ] lookup_key matches feature table primary keys
- [ ] Column names mapped if different from Gold

### Training Set
- [ ] base_df contains ONLY: primary keys + label
- [ ] Label is cast to DOUBLE (regression) or INT (classification)
- [ ] exclude_columns includes primary keys
- [ ] training_set passed to fe.log_model()

## Next Steps

- **[04-Model Training](04-model-training.md)**: Training patterns with MLflow
- **[06-Batch Inference](06-batch-inference.md)**: Using fe.score_batch()
- **[14-Debugging Guide](14-debugging-guide.md)**: Common errors and solutions

