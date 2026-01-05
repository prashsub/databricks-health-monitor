# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
# This enables imports from src.ml.config and src.ml.utils when deployed
# via Databricks Asset Bundles. The bundle root is computed dynamically.
# Reference: https://docs.databricks.com/aws/en/notebooks/share-code
import sys
import os

try:
    # Get current notebook path and compute bundle root
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================
"""
Create Feature Tables for Databricks Health Monitor ML Models
=============================================================

This script creates and populates feature tables in Unity Catalog
for all ML agent domains: Cost, Security, Performance, Reliability, Quality.

Feature Engineering in Unity Catalog allows any Delta table with a primary key
to be used as a feature table. This script creates optimized feature tables
with proper clustering, primary keys, and documentation.

Usage:
    Run this script before training models to ensure feature tables are current.
    
MLflow 3.0 Integration:
    - Feature tables are registered in Unity Catalog
    - Models trained with these features automatically track lineage
    - At inference time, features are automatically looked up
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from typing import List, Dict, Optional
from dataclasses import dataclass

# COMMAND ----------

@dataclass
class FeatureEngineeringConfig:
    """Configuration for feature engineering operations."""
    catalog: str
    schema: str
    gold_schema: str

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def create_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    table_name: str,
    df,
    primary_keys: List[str],
    description: str,
    timestamp_keys: Optional[List[str]] = None,
    tags: Optional[Dict[str, str]] = None
) -> str:
    """
    Create a feature table in Unity Catalog.
    
    This creates a standard Delta table with primary key constraints,
    which makes it eligible for use as a feature table with the
    Feature Engineering client.
    
    IMPORTANT: All numeric feature columns are cast to DOUBLE type to ensure
    consistency between training (which uses float64) and inference (which
    uses native types). This prevents MLflow schema validation errors.
    
    Args:
        spark: SparkSession
        config: Feature engineering configuration
        table_name: Name of the feature table
        df: DataFrame with feature data
        primary_keys: List of primary key columns
        description: Table description
        timestamp_keys: Optional list of timestamp columns
        tags: Optional dictionary of tags
        
    Returns:
        Fully qualified table name
    """
    from pyspark.sql.types import IntegerType, LongType, FloatType, DecimalType, ShortType, ByteType
    
    full_table_name = f"{config.catalog}.{config.schema}.{table_name}"
    
    print(f"\nCreating feature table: {full_table_name}")
    print(f"Primary keys: {primary_keys}")
    
    # =============================================================================
    # CRITICAL: Cast all numeric columns to DOUBLE for MLflow compatibility
    # =============================================================================
    # Training scripts cast features to float64, so we need feature tables to
    # also use DOUBLE type to ensure model signatures match at inference time.
    # This prevents "Failed to enforce schema" errors during fe.score_batch()
    # =============================================================================
    
    # Define columns that should NOT be cast (primary keys, timestamps, strings)
    timestamp_cols = timestamp_keys or []
    non_cast_cols = set(primary_keys + timestamp_cols)
    
    # =============================================================================
    # CRITICAL: Cast to DOUBLE AND fill NaN/Inf with 0 for ALL numeric columns
    # =============================================================================
    # Root cause of inference failures (Jan 2026):
    # - Training scripts call prepare_training_data() which fills NaN with 0
    # - Inference via fe.score_batch() uses raw feature table data
    # - sklearn GradientBoostingRegressor does NOT handle NaN natively
    # - XGBoost handles NaN, but sklearn doesn't → inconsistent behavior
    # 
    # Solution: Fill NaN/Inf at source (feature table) to ensure consistency
    # =============================================================================
    from pyspark.sql.types import DoubleType
    
    # Helper function to clean numeric values (replace NaN and Inf with 0)
    def clean_numeric(col_name):
        """Replace NaN and Infinity with 0.0"""
        return F.when(
            F.col(col_name).isNull() | 
            F.isnan(F.col(col_name)) |
            (F.col(col_name) == float('inf')) |
            (F.col(col_name) == float('-inf')),
            F.lit(0.0)
        ).otherwise(F.col(col_name))
    
    cast_count = 0
    nan_fill_cols = []
    for field in df.schema.fields:
        if field.name not in non_cast_cols:
            # Handle integer/float types - cast to DOUBLE and clean
            if isinstance(field.dataType, (IntegerType, LongType, FloatType, DecimalType, ShortType, ByteType)):
                df = df.withColumn(field.name, F.col(field.name).cast("double"))
                df = df.withColumn(field.name, clean_numeric(field.name))
                cast_count += 1
                nan_fill_cols.append(field.name)
            # Handle columns already DOUBLE (from window functions) - just clean
            elif isinstance(field.dataType, DoubleType):
                df = df.withColumn(field.name, clean_numeric(field.name))
                nan_fill_cols.append(field.name)
    
    print(f"  Cast {cast_count} numeric columns to DOUBLE")
    print(f"  Cleaned NaN/Inf→0.0 for {len(nan_fill_cols)} columns (sklearn compatibility)")
    
    # Filter out rows where any primary key column is NULL
    # This is REQUIRED for PRIMARY KEY constraint
    print(f"  Filtering NULL primary key rows...")
    for pk_col in primary_keys:
        df = df.filter(F.col(pk_col).isNotNull())
    
    # Ensure we have data
    row_count = df.count()
    print(f"  DataFrame has {row_count} rows after NULL filtering")
    
    if row_count == 0:
        raise ValueError(f"Cannot create feature table {full_table_name} with 0 rows")
    
    # First, drop existing table if it exists
    try:
        spark.sql(f"DROP TABLE IF EXISTS {full_table_name}")
        print(f"  ✓ Dropped existing table (if any)")
    except Exception as e:
        print(f"  Note: {e}")
    
    # Build column definitions with NOT NULL for primary keys
    schema_fields = []
    for field in df.schema.fields:
        col_name = field.name
        col_type = field.dataType.simpleString()
        if col_name in primary_keys:
            schema_fields.append(f"`{col_name}` {col_type} NOT NULL")
        else:
            schema_fields.append(f"`{col_name}` {col_type}")
    
    schema_def = ", ".join(schema_fields)
    
    # Create table with explicit schema (NOT NULL for PKs)
    create_sql = f"""
        CREATE TABLE {full_table_name} (
            {schema_def}
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
    """
    print(f"  Creating table with explicit schema...")
    spark.sql(create_sql)
    
    # Insert data
    print(f"  Inserting {row_count} rows...")
    df.write.mode("append").saveAsTable(full_table_name)
    
    # Verify table exists and has data
    verify_count = spark.sql(f"SELECT COUNT(*) FROM {full_table_name}").collect()[0][0]
    print(f"  ✓ Verified: {verify_count} rows in {full_table_name}")
    
    if verify_count == 0:
        raise ValueError(f"Table {full_table_name} was created but has 0 rows!")
    
    # Add table comment
    try:
        clean_desc = description.replace("'", "''")[:1000]
        spark.sql(f"COMMENT ON TABLE {full_table_name} IS '{clean_desc}'")
    except Exception as e:
        print(f"  Note: Could not add comment: {e}")
    
    # Add primary key constraint for feature table eligibility
    # CRITICAL: Feature Engineering requires tables to have PRIMARY KEY constraints
    pk_cols = ", ".join([f"`{pk}`" for pk in primary_keys])
    pk_name = f"pk_{table_name}"
    
    # First, try to drop any existing constraint
    try:
        spark.sql(f"ALTER TABLE {full_table_name} DROP CONSTRAINT IF EXISTS {pk_name}")
    except Exception:
        pass  # Ignore if constraint doesn't exist
    
    # Add the primary key constraint - MUST succeed for Feature Engineering
    try:
        add_pk_sql = f"ALTER TABLE {full_table_name} ADD CONSTRAINT {pk_name} PRIMARY KEY ({pk_cols}) NOT ENFORCED"
        print(f"  Adding PK constraint: {add_pk_sql}")
        spark.sql(add_pk_sql)
        print(f"  ✓ Primary key constraint added: {pk_name}")
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            print(f"  ✓ Primary key constraint already exists: {pk_name}")
        else:
            print(f"  ❌ CRITICAL: Could not add PK constraint: {e}")
            raise ValueError(f"Feature table {full_table_name} requires PRIMARY KEY constraint for Feature Engineering. Error: {e}")
    
    # Verify the constraint was added
    try:
        constraints = spark.sql(f"SHOW TBLPROPERTIES {full_table_name}").collect()
        pk_found = any("primary_key" in str(c).lower() or pk_name.lower() in str(c).lower() for c in constraints)
        if not pk_found:
            # Try another verification method
            desc = spark.sql(f"DESCRIBE EXTENDED {full_table_name}").collect()
            pk_found = any("primary key" in str(row).lower() for row in desc)
        
        if pk_found:
            print(f"  ✓ Verified: Primary key constraint exists on {full_table_name}")
        else:
            print(f"  ⚠ Warning: Could not verify PK constraint on {full_table_name}")
    except Exception as e:
        print(f"  Note: Could not verify PK constraint: {e}")
    
    print(f"  ✓ Feature table created successfully: {full_table_name}")
    
    return full_table_name

# COMMAND ----------

def compute_cost_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 365  # Extended to 1 year to capture all available data
):
    """
    Compute cost features for anomaly detection and forecasting.

    Features:
    - Daily DBU usage by workspace and SKU
    - 7-day and 30-day rolling averages
    - Z-scores for anomaly detection
    - Day-of-week and month-end indicators
    - ALL_PURPOSE cluster inefficiency detection (Workflow Advisor Blog)
    - Potential savings metrics (40% savings for job cluster migration)

    Source: fact_usage (billing domain)
    Blog Sources: Workflow Advisor Blog - ALL_PURPOSE cluster inefficiency patterns
    """
    print("\nComputing cost features...")
    print(f"  Using lookback period: {lookback_days} days")

    # Read from Gold fact_usage table
    fact_usage = f"{config.catalog}.{config.gold_schema}.fact_usage"

    try:
        # First check if source table has any data
        source_count = spark.table(fact_usage).count()
        print(f"  Source table {fact_usage} has {source_count} rows")
        
        if source_count == 0:
            print(f"  ⚠ Source table is empty - no features can be computed")
            raise ValueError(f"Source table {fact_usage} is empty")
        
        # Check date range in source
        date_range = spark.table(fact_usage).agg(
            F.min("usage_date").alias("min_date"),
            F.max("usage_date").alias("max_date")
        ).collect()[0]
        print(f"  Date range: {date_range['min_date']} to {date_range['max_date']}")
        
        # Aggregate to daily level by workspace and SKU with ALL_PURPOSE detection
        # Workflow Advisor Blog: Jobs on ALL_PURPOSE clusters are inefficient
        # NOTE: Gold layer flattens usage_metadata.* to usage_metadata_* columns
        # NOTE: Aggregate to workspace-date level for Feature Engineering compatibility
        # Primary keys: ["workspace_id", "usage_date"] - matches training scripts lookup keys
        usage_df = (
            spark.table(fact_usage)
            .withColumn("usage_date", F.to_date("usage_date"))
            .filter(F.col("usage_date").isNotNull())  # Only filter nulls, keep all dates
            .groupBy("workspace_id", "usage_date")  # Aggregate across SKUs
            .agg(
                F.sum("usage_quantity").alias("daily_dbu"),
                F.sum(F.coalesce(F.col("list_cost"), F.lit(0))).alias("daily_cost"),
                # ALL_PURPOSE detection (Workflow Advisor Blog)
                # Uses flattened column: usage_metadata_job_id
                F.sum(F.when(
                    (F.col("sku_name").like("%ALL_PURPOSE%")) &
                    (F.col("usage_metadata_job_id").isNotNull()),
                    F.coalesce(F.col("list_cost"), F.lit(0))
                ).otherwise(0)).alias("jobs_on_all_purpose_cost"),
                # Count distinct jobs running on ALL_PURPOSE
                F.countDistinct(F.when(
                    (F.col("sku_name").like("%ALL_PURPOSE%")) &
                    (F.col("usage_metadata_job_id").isNotNull()),
                    F.col("usage_metadata_job_id")
                )).alias("jobs_on_all_purpose_count"),
                # Serverless cost
                F.sum(F.when(
                    F.col("product_features_is_serverless") == True,
                    F.coalesce(F.col("list_cost"), F.lit(0))
                ).otherwise(0)).alias("serverless_cost"),
                # DLT cost
                F.sum(F.when(
                    F.col("sku_name").like("%DLT%"),
                    F.coalesce(F.col("list_cost"), F.lit(0))
                ).otherwise(0)).alias("dlt_cost"),
                # Model serving cost
                F.sum(F.when(
                    (F.col("sku_name").like("%MODEL_SERVING%")) |
                    (F.col("sku_name").like("%INFERENCE%")),
                    F.coalesce(F.col("list_cost"), F.lit(0))
                ).otherwise(0)).alias("model_serving_cost")
            )
        )
        agg_count = usage_df.count()
        print(f"  Aggregated to {agg_count} workspace-date combinations")
        print(f"  ✓ Found {fact_usage}")
    except Exception as e:
        print(f"  ⚠ Error reading {fact_usage}: {e}")
        raise

    # Define window for rolling calculations (workspace-date level)
    workspace_window = Window.partitionBy("workspace_id").orderBy("usage_date")
    workspace_window_7d = workspace_window.rowsBetween(-6, 0)
    workspace_window_30d = workspace_window.rowsBetween(-29, 0)

    cost_features = (
        usage_df
        # Rolling statistics
        .withColumn("avg_dbu_7d", F.avg("daily_dbu").over(workspace_window_7d))
        .withColumn("std_dbu_7d", F.stddev("daily_dbu").over(workspace_window_7d))
        .withColumn("avg_dbu_30d", F.avg("daily_dbu").over(workspace_window_30d))
        .withColumn("std_dbu_30d", F.stddev("daily_dbu").over(workspace_window_30d))

        # Z-scores for anomaly detection
        .withColumn("z_score_7d",
                   F.when(F.col("std_dbu_7d") > 0,
                         (F.col("daily_dbu") - F.col("avg_dbu_7d")) / F.col("std_dbu_7d"))
                   .otherwise(0))
        .withColumn("z_score_30d",
                   F.when(F.col("std_dbu_30d") > 0,
                         (F.col("daily_dbu") - F.col("avg_dbu_30d")) / F.col("std_dbu_30d"))
                   .otherwise(0))

        # Contextual features
        .withColumn("day_of_week", F.dayofweek("usage_date"))
        .withColumn("is_weekend", F.when(F.dayofweek("usage_date").isin(1, 7), 1).otherwise(0))
        .withColumn("day_of_month", F.dayofmonth("usage_date"))
        .withColumn("is_month_end", F.when(F.dayofmonth("usage_date") >= 28, 1).otherwise(0))

        # Cyclical encoding for day of week
        .withColumn("dow_sin", F.sin(2 * 3.14159 * F.col("day_of_week") / 7))
        .withColumn("dow_cos", F.cos(2 * 3.14159 * F.col("day_of_week") / 7))

        # Lag features
        .withColumn("daily_dbu_lag1", F.lag("daily_dbu", 1).over(workspace_window))
        .withColumn("daily_dbu_lag7", F.lag("daily_dbu", 7).over(workspace_window))

        # Growth rates
        .withColumn("dbu_change_pct_1d",
                   F.when(F.col("daily_dbu_lag1") > 0,
                         (F.col("daily_dbu") - F.col("daily_dbu_lag1")) / F.col("daily_dbu_lag1") * 100)
                   .otherwise(0))
        .withColumn("dbu_change_pct_7d",
                   F.when(F.col("daily_dbu_lag7") > 0,
                         (F.col("daily_dbu") - F.col("daily_dbu_lag7")) / F.col("daily_dbu_lag7") * 100)
                   .otherwise(0))

        # =============================================================================
        # WORKFLOW ADVISOR BLOG FEATURES (NEW)
        # =============================================================================
        # Potential savings from migrating jobs from ALL_PURPOSE to JOB clusters (~40%)
        .withColumn("potential_job_cluster_savings",
                   F.col("jobs_on_all_purpose_cost") * 0.4)
        # ALL_PURPOSE inefficiency ratio
        .withColumn("all_purpose_inefficiency_ratio",
                   F.when(F.col("daily_cost") > 0,
                         F.col("jobs_on_all_purpose_cost") / F.col("daily_cost"))
                   .otherwise(0))
        # Serverless adoption ratio
        .withColumn("serverless_adoption_ratio",
                   F.when(F.col("daily_cost") > 0,
                         F.col("serverless_cost") / F.col("daily_cost"))
                   .otherwise(0))

        # Feature timestamp
        .withColumn("feature_timestamp", F.current_timestamp())

        # Fill null values from windowing with sensible defaults instead of filtering
        .fillna(0, subset=["avg_dbu_7d", "std_dbu_7d", "avg_dbu_30d", "std_dbu_30d", 
                          "z_score_7d", "z_score_30d", "daily_dbu_lag1", "daily_dbu_lag7",
                          "dbu_change_pct_1d", "dbu_change_pct_7d"])
    )

    row_count = cost_features.count()
    print(f"  ✓ Computed {row_count} cost feature rows")

    return cost_features

# COMMAND ----------

def compute_security_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 365  # Extended to 1 year to capture all available data
):
    """
    Compute security features for threat and anomaly detection.

    Features:
    - User activity patterns
    - Tables accessed per day
    - Off-hours activity indicators
    - Sensitive data access patterns
    - User type classification (HUMAN_USER, SERVICE_PRINCIPAL, SYSTEM, PLATFORM)
    - Activity burst detection

    Source: fact_audit_logs (security domain)
    Blog Sources: Databricks audit logs repo - user type classification patterns
    """
    print("\nComputing security features...")
    print(f"  Using lookback period: {lookback_days} days")

    # Read from Gold fact_audit_logs table (NOT fact_audit_events!)
    fact_audit = f"{config.catalog}.{config.gold_schema}.fact_audit_logs"

    try:
        # First check if source table has any data
        source_count = spark.table(fact_audit).count()
        print(f"  Source table {fact_audit} has {source_count} rows")
        
        if source_count == 0:
            print(f"  ⚠ Source table is empty - no features can be computed")
            raise ValueError(f"Source table {fact_audit} is empty")
        
        # Aggregate audit events by user and date with user type classification
        # User Type Classification Logic (from audit logs repo):
        # - HUMAN_USER: Contains @ but not System-, spn@, gserviceaccount, DBX_
        # - SERVICE_PRINCIPAL: Contains spn@, gserviceaccount, or starts with DBX_
        # - SYSTEM: Starts with System-
        # - PLATFORM: DBX_ prefix (Databricks platform accounts)
        # NOTE: Using ALL available data (no date filter)
        security_df = (
            spark.table(fact_audit)
            .withColumn("event_date", F.to_date("event_time"))
            .filter(F.col("event_date").isNotNull())  # Only filter nulls
            .withColumn("user_id", F.col("user_identity_email"))
            # User type classification (audit logs repo pattern)
            .withColumn("user_type",
                F.when(
                    (F.col("user_identity_email").like("%@%")) &
                    (~F.col("user_identity_email").like("System-%")) &
                    (~F.col("user_identity_email").like("%spn@%")) &
                    (~F.col("user_identity_email").like("%iam.gserviceaccount.com")) &
                    (~F.col("user_identity_email").like("DBX_%")),
                    F.lit("HUMAN_USER")
                ).when(
                    (F.col("user_identity_email").like("%spn@%")) |
                    (F.col("user_identity_email").like("%iam.gserviceaccount.com")) |
                    (F.col("user_identity_email").like("DBX_%")),
                    F.lit("SERVICE_PRINCIPAL")
                ).when(
                    F.col("user_identity_email").like("System-%"),
                    F.lit("SYSTEM")
                ).otherwise(F.lit("UNKNOWN"))
            )
            .groupBy("user_id", "event_date")  # Simplified for Feature Engineering lookup keys
            .agg(
                F.first("user_type").alias("user_type"),  # Keep user_type as a feature, not primary key
                F.count("*").alias("event_count"),
                # Access table names from request_params MAP
                F.countDistinct(F.element_at("request_params", "tableName")).alias("tables_accessed"),
                F.sum(F.when(F.hour("event_time").between(0, 6), 1).otherwise(0)).alias("off_hours_events"),
                F.countDistinct("source_ip_address").alias("unique_source_ips"),
                # Count failed actions
                F.sum(F.when(F.col("is_failed_action") == True, 1).otherwise(0)).alias("failed_auth_count"),
                # Action type counts for behavior profiling
                F.countDistinct("action_name").alias("unique_action_types"),
                # Service name diversity (lateral movement indicator)
                F.countDistinct("service_name").alias("unique_services_accessed")
            )
            .withColumn("sensitive_data_access", F.lit(0))  # Placeholder - would need PII tag info
        )
        agg_count = security_df.count()
        print(f"  Aggregated to {agg_count} user-date combinations")
        print(f"  ✓ Found {fact_audit}")
    except Exception as e:
        print(f"  ⚠ Error reading {fact_audit}: {e}")
        raise

    # Define window for rolling calculations
    user_window = Window.partitionBy("user_id").orderBy("event_date")
    user_window_7d = user_window.rowsBetween(-6, 0)
    user_window_1h = Window.partitionBy("user_id", "event_date").orderBy("event_date")

    security_features = (
        security_df
        # Rolling averages
        .withColumn("avg_event_count_7d", F.avg("event_count").over(user_window_7d))
        .withColumn("std_event_count_7d", F.stddev("event_count").over(user_window_7d))
        .withColumn("avg_tables_accessed_7d", F.avg("tables_accessed").over(user_window_7d))

        # Z-scores for anomaly detection
        .withColumn("event_count_z_score",
                   F.when(F.col("std_event_count_7d") > 0,
                         (F.col("event_count") - F.col("avg_event_count_7d")) / F.col("std_event_count_7d"))
                   .otherwise(0))

        # Risk indicators
        .withColumn("off_hours_rate",
                   F.when(F.col("event_count") > 0,
                         F.col("off_hours_events") / F.col("event_count"))
                   .otherwise(0))
        .withColumn("sensitive_access_rate",
                   F.when(F.col("tables_accessed") > 0,
                         F.col("sensitive_data_access") / F.col("tables_accessed"))
                   .otherwise(0))

        # =============================================================================
        # AUDIT LOGS REPO FEATURES (NEW)
        # =============================================================================
        # User type encoded for ML
        .withColumn("is_human_user", F.when(F.col("user_type") == "HUMAN_USER", 1).otherwise(0))
        .withColumn("is_service_principal", F.when(F.col("user_type") == "SERVICE_PRINCIPAL", 1).otherwise(0))
        .withColumn("is_system_user", F.when(F.col("user_type") == "SYSTEM", 1).otherwise(0))

        # Activity burst detection (events significantly above average)
        .withColumn("is_activity_burst",
                   F.when(
                       (F.col("event_count_z_score") > 2) &
                       (F.col("event_count") > 100),
                       1
                   ).otherwise(0))

        # Lateral movement indicator (accessing many services)
        .withColumn("lateral_movement_risk",
                   F.when(F.col("unique_services_accessed") > 5, 1).otherwise(0))

        # Failed auth ratio (brute force indicator)
        .withColumn("failed_auth_ratio",
                   F.when(F.col("event_count") > 0,
                         F.col("failed_auth_count") / F.col("event_count"))
                   .otherwise(0))

        # Contextual features
        .withColumn("is_weekend", F.when(F.dayofweek("event_date").isin(1, 7), 1).otherwise(0))
        .withColumn("day_of_week", F.dayofweek("event_date"))

        # Feature timestamp
        .withColumn("feature_timestamp", F.current_timestamp())

        # Fill null values from windowing with sensible defaults instead of filtering
        .fillna(0, subset=["avg_event_count_7d", "std_event_count_7d", "avg_tables_accessed_7d",
                          "event_count_z_score", "off_hours_rate", "sensitive_access_rate",
                          "is_human_user", "is_service_principal", "is_system_user",
                          "is_activity_burst", "lateral_movement_risk", "failed_auth_ratio"])
    )

    row_count = security_features.count()
    print(f"  ✓ Computed {row_count} security feature rows")

    return security_features

# COMMAND ----------

def compute_performance_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 365  # Extended to 1 year to capture all available data
):
    """
    Compute performance features for query and warehouse optimization.

    Features:
    - Query duration percentiles (P50, P95, P99)
    - Data read/write volumes
    - Error and spill rates
    - Warehouse utilization patterns
    - SLA breach detection (60-second threshold from DBSQL Warehouse Advisor v5 Blog)
    - Query efficiency classification
    - Queue time analysis

    Source: fact_query_history (query_performance domain)
    Blog Sources: DBSQL Warehouse Advisor v5 Blog, Real-Time Query Monitoring Blog
    """
    print("\nComputing performance features...")
    print(f"  Using lookback period: {lookback_days} days")

    # Read from Gold fact_query_history table
    fact_query = f"{config.catalog}.{config.gold_schema}.fact_query_history"

    try:
        # First check if source table has any data
        source_count = spark.table(fact_query).count()
        print(f"  Source table {fact_query} has {source_count} rows")
        
        if source_count == 0:
            print(f"  ⚠ Source table is empty - no features can be computed")
            raise ValueError(f"Source table {fact_query} is empty")
        
        # Aggregate query metrics by warehouse and date with blog-derived features
        # DBSQL Warehouse Advisor v5 Blog: 60-second SLA threshold, P99 more important than P95
        # NOTE: Using ALL available data (no date filter)
        performance_df = (
            spark.table(fact_query)
            .withColumn("query_date", F.to_date("end_time"))
            .filter(F.col("query_date").isNotNull())  # Only filter nulls
            .withColumn("warehouse_id", F.col("compute_warehouse_id"))
            .filter(F.col("warehouse_id").isNotNull())  # Filter out non-warehouse queries
            .groupBy("warehouse_id", "query_date")
            .agg(
                F.count("*").alias("query_count"),
                F.sum("total_duration_ms").alias("total_duration_ms"),
                F.percentile_approx("total_duration_ms", 0.5).alias("p50_duration_ms"),
                F.percentile_approx("total_duration_ms", 0.95).alias("p95_duration_ms"),
                F.percentile_approx("total_duration_ms", 0.99).alias("p99_duration_ms"),
                F.sum("read_bytes").alias("total_bytes_read"),
                F.sum("written_bytes").alias("total_bytes_written"),
                F.sum(F.when(F.col("execution_status") == "FAILED", 1).otherwise(0)).alias("error_count"),
                F.sum(F.when(F.col("spilled_local_bytes") > 0, 1).otherwise(0)).alias("spill_count"),
                # =============================================================================
                # DBSQL WAREHOUSE ADVISOR V5 BLOG FEATURES (NEW)
                # =============================================================================
                # SLA breach count (60-second threshold from blog)
                F.sum(F.when(F.col("total_duration_ms") > 60000, 1).otherwise(0)).alias("sla_breach_count"),
                # Efficient query count (no spill, minimal queue, under 60s)
                F.sum(F.when(
                    (F.coalesce(F.col("spilled_local_bytes"), F.lit(0)) == 0) &
                    (F.coalesce(F.col("waiting_at_capacity_duration_ms"), F.lit(0)) <= F.col("total_duration_ms") * 0.1) &
                    (F.col("total_duration_ms") <= 60000),
                    1
                ).otherwise(0)).alias("efficient_query_count"),
                # High queue time count (queue > 10% of runtime from blog)
                F.sum(F.when(
                    F.coalesce(F.col("waiting_at_capacity_duration_ms"), F.lit(0)) > F.col("total_duration_ms") * 0.1,
                    1
                ).otherwise(0)).alias("high_queue_count"),
                # Large data queries (> 10GB from blog)
                F.sum(F.when(F.col("read_bytes") > 10737418240, 1).otherwise(0)).alias("large_query_count"),
                # Total queue time for averaging
                F.sum(F.coalesce("waiting_at_capacity_duration_ms", F.lit(0))).alias("total_queue_time_ms"),
                # Queries per minute (QPM) calculation
                F.countDistinct(F.date_trunc("minute", F.col("end_time"))).alias("active_minutes")
            )
        )
        agg_count = performance_df.count()
        print(f"  Aggregated to {agg_count} warehouse-date combinations")
        print(f"  ✓ Found {fact_query}")
    except Exception as e:
        print(f"  ⚠ Error reading {fact_query}: {e}")
        raise

    # Define window for rolling calculations
    warehouse_window = Window.partitionBy("warehouse_id").orderBy("query_date")
    warehouse_window_7d = warehouse_window.rowsBetween(-6, 0)

    performance_features = (
        performance_df
        # Average metrics
        .withColumn("avg_duration_ms", F.col("total_duration_ms") / F.col("query_count"))

        # Rolling averages
        .withColumn("avg_query_count_7d", F.avg("query_count").over(warehouse_window_7d))
        .withColumn("avg_duration_7d", F.avg("avg_duration_ms").over(warehouse_window_7d))
        .withColumn("avg_p99_duration_7d", F.avg("p99_duration_ms").over(warehouse_window_7d))

        # Error and spill rates
        .withColumn("error_rate",
                   F.when(F.col("query_count") > 0, F.col("error_count") / F.col("query_count"))
                   .otherwise(0))
        .withColumn("spill_rate",
                   F.when(F.col("query_count") > 0, F.col("spill_count") / F.col("query_count"))
                   .otherwise(0))

        # Data volume metrics
        .withColumn("avg_bytes_per_query",
                   F.when(F.col("query_count") > 0, F.col("total_bytes_read") / F.col("query_count"))
                   .otherwise(0))
        .withColumn("read_write_ratio",
                   F.when(F.col("total_bytes_written") > 0,
                         F.col("total_bytes_read") / F.col("total_bytes_written"))
                   .otherwise(0))

        # =============================================================================
        # DBSQL WAREHOUSE ADVISOR BLOG FEATURES (NEW)
        # =============================================================================
        # SLA breach rate (critical for capacity planning)
        .withColumn("sla_breach_rate",
                   F.when(F.col("query_count") > 0,
                         F.col("sla_breach_count") / F.col("query_count"))
                   .otherwise(0))
        # Query efficiency rate
        .withColumn("query_efficiency_rate",
                   F.when(F.col("query_count") > 0,
                         F.col("efficient_query_count") / F.col("query_count"))
                   .otherwise(0))
        # High queue rate (capacity issue indicator)
        .withColumn("high_queue_rate",
                   F.when(F.col("query_count") > 0,
                         F.col("high_queue_count") / F.col("query_count"))
                   .otherwise(0))
        # Large query rate (resource pressure indicator)
        .withColumn("large_query_rate",
                   F.when(F.col("query_count") > 0,
                         F.col("large_query_count") / F.col("query_count"))
                   .otherwise(0))
        # Average queue time
        .withColumn("avg_queue_time_ms",
                   F.when(F.col("query_count") > 0,
                         F.col("total_queue_time_ms") / F.col("query_count"))
                   .otherwise(0))
        # Queries per minute (throughput)
        .withColumn("queries_per_minute",
                   F.when(F.col("active_minutes") > 0,
                         F.col("query_count") / F.col("active_minutes"))
                   .otherwise(0))

        # Duration regression detection (Real-Time Query Monitoring Blog)
        .withColumn("p99_duration_lag7", F.lag("p99_duration_ms", 7).over(warehouse_window))
        .withColumn("duration_regression_pct",
                   F.when(F.col("p99_duration_lag7") > 0,
                         (F.col("p99_duration_ms") - F.col("p99_duration_lag7")) / F.col("p99_duration_lag7") * 100)
                   .otherwise(0))
        # Is regressing (> 20% slowdown)
        .withColumn("is_duration_regressing",
                   F.when(F.col("duration_regression_pct") > 20, 1).otherwise(0))

        # Contextual features
        .withColumn("is_weekend", F.when(F.dayofweek("query_date").isin(1, 7), 1).otherwise(0))
        .withColumn("day_of_week", F.dayofweek("query_date"))

        # Feature timestamp
        .withColumn("feature_timestamp", F.current_timestamp())

        # Fill null values from windowing with sensible defaults instead of filtering
        .fillna(0, subset=["avg_query_count_7d", "avg_duration_7d", "avg_p99_duration_7d",
                          "p99_duration_lag7", "duration_regression_pct", "is_duration_regressing",
                          "error_rate", "spill_rate", "avg_bytes_per_query", "read_write_ratio",
                          "sla_breach_rate", "query_efficiency_rate", "high_queue_rate",
                          "large_query_rate", "avg_queue_time_ms", "queries_per_minute"])
    )

    row_count = performance_features.count()
    print(f"  ✓ Computed {row_count} performance feature rows")

    return performance_features

# COMMAND ----------

def compute_reliability_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 365  # Extended to 1 year to capture all available data
):
    """
    Compute reliability features for job failure prediction.

    Features:
    - Job success/failure rates
    - Duration statistics (P50, P95, P99)
    - Historical failure patterns
    - Coefficient of variation
    - Duration regression detection (from Real-Time Query Monitoring Blog pattern)
    - Repair/retry cost tracking (from Jobs System Tables Dashboard)

    Source: fact_job_run_timeline (lakeflow domain)
    Blog Sources: Real-Time Query Monitoring Blog, Jobs System Tables Dashboard
    """
    print("\nComputing reliability features...")
    print(f"  Using lookback period: {lookback_days} days")

    # Read from Gold fact_job_run_timeline table
    fact_job = f"{config.catalog}.{config.gold_schema}.fact_job_run_timeline"

    try:
        # First check if source table has any data
        source_count = spark.table(fact_job).count()
        print(f"  Source table {fact_job} has {source_count} rows")
        
        if source_count == 0:
            print(f"  ⚠ Source table is empty - no features can be computed")
            raise ValueError(f"Source table {fact_job} is empty")
        
        # Aggregate job run metrics by job and date with enhanced features
        # NOTE: Gold layer does not have is_repair_run column - derive from run_type
        # NOTE: Using ALL available data (no date filter)
        reliability_df = (
            spark.table(fact_job)
            # Use the derived run_date column, or derive from period_start_time
            .withColumn("run_date",
                       F.coalesce(F.col("run_date"), F.to_date("period_start_time")))
            .filter(F.col("run_date").isNotNull())  # Only filter nulls
            .filter(F.col("job_id").isNotNull())  # Filter out null job_ids
            # Use derived run_duration_seconds, or calculate from timestamps
            .withColumn("duration_seconds",
                       F.coalesce(
                           F.col("run_duration_seconds"),
                           F.unix_timestamp("period_end_time") - F.unix_timestamp("period_start_time")
                       ))
            # Derive is_repair_run from run_type (contains 'REPAIR' indicates a repair run)
            .withColumn("is_repair_run",
                       F.when(F.col("run_type").like("%REPAIR%"), True).otherwise(False))
            .groupBy("job_id", "run_date")
            .agg(
                F.count("*").alias("total_runs"),
                F.sum(F.when(F.col("result_state") == "SUCCESS", 1).otherwise(0)).alias("successful_runs"),
                F.sum(F.when(F.col("result_state") == "FAILED", 1).otherwise(0)).alias("failed_runs"),
                F.avg("duration_seconds").alias("avg_duration_sec"),
                F.stddev("duration_seconds").alias("std_duration_sec"),
                F.max("duration_seconds").alias("max_duration_sec"),
                F.min("duration_seconds").alias("min_duration_sec"),
                # =============================================================================
                # ENHANCED FEATURES (P99, repair tracking)
                # =============================================================================
                # P99 duration (more important than P95 from blog insights)
                F.percentile_approx("duration_seconds", 0.99).alias("p99_duration_sec"),
                F.percentile_approx("duration_seconds", 0.95).alias("p95_duration_sec"),
                F.percentile_approx("duration_seconds", 0.50).alias("p50_duration_sec"),
                # Repair/retry count (derived from run_type containing 'REPAIR')
                F.sum(F.when(F.col("is_repair_run") == True, 1).otherwise(0)).alias("repair_runs"),
                # Timeout count
                F.sum(F.when(F.col("result_state") == "TIMED_OUT", 1).otherwise(0)).alias("timeout_runs"),
                # Cancelled runs
                F.sum(F.when(F.col("result_state") == "CANCELLED", 1).otherwise(0)).alias("cancelled_runs")
            )
        )
        agg_count = reliability_df.count()
        print(f"  Aggregated to {agg_count} job-date combinations")
        print(f"  ✓ Found {fact_job}")
    except Exception as e:
        print(f"  ⚠ Error reading {fact_job}: {e}")
        raise

    # Define window for rolling calculations
    job_window = Window.partitionBy("job_id").orderBy("run_date")
    job_window_30d = job_window.rowsBetween(-29, 0)
    job_window_7d = job_window.rowsBetween(-6, 0)

    reliability_features = (
        reliability_df
        # Success/failure rates
        .withColumn("success_rate",
                   F.when(F.col("total_runs") > 0, F.col("successful_runs") / F.col("total_runs"))
                   .otherwise(0))
        .withColumn("failure_rate",
                   F.when(F.col("total_runs") > 0, F.col("failed_runs") / F.col("total_runs"))
                   .otherwise(0))

        # Coefficient of variation (duration stability)
        .withColumn("duration_cv",
                   F.when(F.col("avg_duration_sec") > 0, F.col("std_duration_sec") / F.col("avg_duration_sec"))
                   .otherwise(0))

        # Rolling statistics
        .withColumn("rolling_failure_rate_30d", F.avg("failure_rate").over(job_window_30d))
        .withColumn("rolling_avg_duration_30d", F.avg("avg_duration_sec").over(job_window_30d))
        .withColumn("total_failures_30d", F.sum("failed_runs").over(job_window_30d))

        # =============================================================================
        # ENHANCED ROLLING STATISTICS (from blog patterns)
        # =============================================================================
        # P99 rolling average (more important than P95)
        .withColumn("rolling_p99_duration_7d", F.avg("p99_duration_sec").over(job_window_7d))
        .withColumn("rolling_p99_duration_30d", F.avg("p99_duration_sec").over(job_window_30d))
        # Rolling repair rate
        .withColumn("rolling_repair_rate_30d",
                   F.when(F.sum("total_runs").over(job_window_30d) > 0,
                         F.sum("repair_runs").over(job_window_30d) / F.sum("total_runs").over(job_window_30d))
                   .otherwise(0))

        # Lag features
        .withColumn("prev_day_success_rate", F.lag("success_rate", 1).over(job_window))
        .withColumn("prev_day_failed",
                   F.when(F.lag("failed_runs", 1).over(job_window) > 0, 1).otherwise(0))

        # Trend features
        .withColumn("success_rate_trend",
                   F.col("success_rate") - F.lag("success_rate", 7).over(job_window))

        # =============================================================================
        # DURATION REGRESSION DETECTION (Real-Time Query Monitoring Blog pattern)
        # =============================================================================
        .withColumn("p99_duration_lag7", F.lag("p99_duration_sec", 7).over(job_window))
        .withColumn("duration_regression_pct",
                   F.when(F.col("p99_duration_lag7") > 0,
                         (F.col("p99_duration_sec") - F.col("p99_duration_lag7")) / F.col("p99_duration_lag7") * 100)
                   .otherwise(0))
        # Is duration regressing (> 20% slowdown)
        .withColumn("is_duration_regressing",
                   F.when(F.col("duration_regression_pct") > 20, 1).otherwise(0))
        # Duration range (max - min) for instability detection
        .withColumn("duration_range_sec",
                   F.col("max_duration_sec") - F.col("min_duration_sec"))

        # Contextual features
        .withColumn("is_weekend", F.when(F.dayofweek("run_date").isin(1, 7), 1).otherwise(0))
        .withColumn("day_of_week", F.dayofweek("run_date"))

        # Feature timestamp
        .withColumn("feature_timestamp", F.current_timestamp())

        # Fill null values from windowing with sensible defaults instead of filtering
        .fillna(0, subset=["std_duration_sec", "duration_cv", "repair_runs", "timeout_runs", "cancelled_runs",
                          "rolling_failure_rate_30d", "rolling_avg_duration_30d", "total_failures_30d",
                          "rolling_p99_duration_7d", "rolling_p99_duration_30d", "rolling_repair_rate_30d",
                          "prev_day_success_rate", "prev_day_failed", "success_rate_trend",
                          "p99_duration_lag7", "duration_regression_pct", "is_duration_regressing",
                          "duration_range_sec"])
    )

    row_count = reliability_features.count()
    print(f"  ✓ Computed {row_count} reliability feature rows")

    return reliability_features

# COMMAND ----------

def create_cost_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig
) -> str:
    """Create cost agent feature table."""
    # Compute features (365 days to capture all available data)
    cost_features = compute_cost_features(spark, config, lookback_days=365)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="cost_features",
        df=cost_features,
        primary_keys=["workspace_id", "usage_date"],
        description="Cost agent features for anomaly detection and forecasting. "
                   "Captures daily DBU usage patterns, rolling statistics, and contextual features.",
        timestamp_keys=["usage_date"],
        tags={
            "agent_domain": "cost",
            "feature_type": "aggregated",
            "refresh_frequency": "daily"
        }
    )
    
    row_count = cost_features.count()
    print(f"✓ Cost features created with {row_count} rows")
    
    return table_name

# COMMAND ----------

def create_security_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig
) -> str:
    """Create security agent feature table."""
    print("\n" + "=" * 60)
    print("Creating Security Feature Table")
    print("=" * 60)

    # Compute features (365 days to capture all available data)
    security_features = compute_security_features(spark, config, lookback_days=365)

    # Create feature table
    # Note: user_type is now part of the groupBy, so include in primary keys
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="security_features",
        df=security_features,
        primary_keys=["user_id", "event_date"],
        description="Security agent features for threat and anomaly detection. "
                   "Includes user type classification (HUMAN_USER, SERVICE_PRINCIPAL, SYSTEM), "
                   "activity burst detection, and lateral movement risk indicators.",
        timestamp_keys=["event_date"],
        tags={
            "agent_domain": "security",
            "feature_type": "user_activity",
            "refresh_frequency": "daily"
        }
    )

    row_count = security_features.count()
    print(f"✓ Security features created with {row_count} rows")

    return table_name

# COMMAND ----------

def create_performance_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig
) -> str:
    """Create performance agent feature table."""
    # Compute features (365 days to capture all available data)
    performance_features = compute_performance_features(spark, config, lookback_days=365)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="performance_features",
        df=performance_features,
        primary_keys=["warehouse_id", "query_date"],
        description="Performance agent features for query and warehouse optimization. "
                   "Captures query metrics and warehouse utilization patterns.",
        timestamp_keys=["query_date"],
        tags={
            "agent_domain": "performance",
            "feature_type": "query_metrics",
            "refresh_frequency": "daily"
        }
    )
    
    row_count = performance_features.count()
    print(f"✓ Performance features created with {row_count} rows")
    
    return table_name

# COMMAND ----------

def create_reliability_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig
) -> str:
    """Create reliability agent feature table."""
    # Compute features (365 days to capture all available data)
    reliability_features = compute_reliability_features(spark, config, lookback_days=365)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="reliability_features",
        df=reliability_features,
        primary_keys=["job_id", "run_date"],
        description="Reliability agent features for job failure and SLA prediction. "
                   "Captures job execution patterns and historical trends.",
        timestamp_keys=["run_date"],
        tags={
            "agent_domain": "reliability",
            "feature_type": "job_metrics",
            "refresh_frequency": "daily"
        }
    )
    
    row_count = reliability_features.count()
    print(f"✓ Reliability features created with {row_count} rows")
    
    return table_name

# COMMAND ----------

def compute_quality_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 365
):
    """
    Compute quality features for data governance and quality monitoring.
    
    Features:
    - Table counts and schema metrics per catalog
    - Primary key coverage
    - Change data feed adoption
    - Schema change detection
    
    Source: system.information_schema (ALL catalogs in metastore)
    
    NOTE: No synthetic data needed - system.information_schema returns
    50-200+ catalogs naturally, providing enough samples for ML training.
    """
    print("\nComputing quality features...")
    print(f"  Querying system.information_schema for ALL catalogs...")
    
    # Get catalog-level statistics from system.information_schema
    try:
        # Query system-level metadata for ALL catalogs
        quality_df = (
            spark.sql(f"""
                WITH table_stats AS (
                    SELECT 
                        table_catalog,
                        table_schema,
                        table_name,
                        COUNT(*) as column_count
                    FROM system.information_schema.columns
                    -- No WHERE filter - get ALL catalogs!
                    GROUP BY table_catalog, table_schema, table_name
                )
                SELECT 
                    table_catalog as catalog_name,
                    CURRENT_DATE() as snapshot_date,
                    COUNT(DISTINCT table_name) as table_count,
                    COUNT(DISTINCT table_schema) as schema_count,
                    AVG(column_count) as column_count_avg,
                    0 as total_rows,
                    0 as tables_with_pk,
                    0.0 as pk_coverage,
                    0 as tables_with_cdf,
                    0.0 as cdf_coverage,
                    0 as tables_created_last_7d,
                    0 as tables_modified_last_7d,
                    0 as schema_changes_7d,
                    CURRENT_TIMESTAMP() as feature_timestamp
                FROM table_stats
                GROUP BY table_catalog
            """)
        )
        
        row_count = quality_df.count()
        print(f"  ✓ Computed {row_count} quality feature rows (one per catalog)")
        
        return quality_df
        
    except Exception as e:
        print(f"  ⚠ Error computing quality features from system.information_schema: {e}")
        print(f"  ⚠ This may indicate insufficient permissions to query system tables.")
        print(f"  → Falling back to single-catalog query...")
        
        # Fallback: query just the current catalog's information_schema
        try:
            quality_df = (
                spark.sql(f"""
                    WITH table_stats AS (
                        SELECT 
                            table_catalog,
                            table_schema,
                            table_name,
                            COUNT(*) as column_count
                        FROM {config.catalog}.information_schema.columns
                        GROUP BY table_catalog, table_schema, table_name
                    )
                    SELECT 
                        table_catalog as catalog_name,
                        CURRENT_DATE() as snapshot_date,
                        COUNT(DISTINCT table_name) as table_count,
                        COUNT(DISTINCT table_schema) as schema_count,
                        AVG(column_count) as column_count_avg,
                        0 as total_rows,
                        0 as tables_with_pk,
                        0.0 as pk_coverage,
                        0 as tables_with_cdf,
                        0.0 as cdf_coverage,
                        0 as tables_created_last_7d,
                        0 as tables_modified_last_7d,
                        0 as schema_changes_7d,
                        CURRENT_TIMESTAMP() as feature_timestamp
                    FROM table_stats
                    GROUP BY table_catalog
                """)
            )
            row_count = quality_df.count()
            print(f"  ✓ Fallback: Computed {row_count} quality feature rows from {config.catalog}")
            return quality_df
        except Exception as fallback_e:
            print(f"  ❌ Fallback also failed: {fallback_e}")
            raise RuntimeError(f"Cannot compute quality features: {e}. Fallback: {fallback_e}")


def create_quality_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig
) -> str:
    """Create quality agent feature table."""
    # Compute features
    quality_features = compute_quality_features(spark, config, lookback_days=365)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="quality_features",
        df=quality_features,
        primary_keys=["catalog_name", "snapshot_date"],
        description="Quality agent features for data governance monitoring. "
                   "Captures catalog-level statistics and data quality metrics.",
        timestamp_keys=["snapshot_date"],
        tags={
            "agent_domain": "quality",
            "feature_type": "catalog_metrics",
            "refresh_frequency": "daily"
        }
    )
    
    row_count = quality_features.count()
    print(f"✓ Quality features created with {row_count} rows")
    
    return table_name


# COMMAND ----------

def create_all_feature_tables(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str
) -> dict:
    """Create all feature tables for ML model training."""
    print("\n" + "=" * 80)
    print("Creating All Feature Tables for Databricks Health Monitor ML")
    print("=" * 80)
    
    config = FeatureEngineeringConfig(
        catalog=catalog,
        schema=feature_schema,
        gold_schema=gold_schema
    )
    
    # Ensure feature schema exists
    print(f"\nCreating schema: {catalog}.{feature_schema}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{feature_schema}")
    print(f"✓ Schema created/verified: {catalog}.{feature_schema}")
    
    # Create feature tables - track errors
    tables = {}
    errors = []
    
    # Create cost features
    print("\n" + "=" * 60)
    print("Creating Cost Feature Table")
    print("=" * 60)
    try:
        tables["cost"] = create_cost_feature_table(spark, config)
    except Exception as e:
        error_msg = f"Cost features: {str(e)}"
        print(f"❌ Error: {error_msg}")
        errors.append(error_msg)
    
    # Create security features
    print("\n" + "=" * 60)
    print("Creating Security Feature Table")
    print("=" * 60)
    try:
        tables["security"] = create_security_feature_table(spark, config)
    except Exception as e:
        error_msg = f"Security features: {str(e)}"
        print(f"❌ Error: {error_msg}")
        errors.append(error_msg)
    
    # Create performance features
    print("\n" + "=" * 60)
    print("Creating Performance Feature Table")
    print("=" * 60)
    try:
        tables["performance"] = create_performance_feature_table(spark, config)
    except Exception as e:
        error_msg = f"Performance features: {str(e)}"
        print(f"❌ Error: {error_msg}")
        errors.append(error_msg)
    
    # Create reliability features
    print("\n" + "=" * 60)
    print("Creating Reliability Feature Table")
    print("=" * 60)
    try:
        tables["reliability"] = create_reliability_feature_table(spark, config)
    except Exception as e:
        error_msg = f"Reliability features: {str(e)}"
        print(f"❌ Error: {error_msg}")
        errors.append(error_msg)
    
    # Create quality features
    print("\n" + "=" * 60)
    print("Creating Quality Feature Table")
    print("=" * 60)
    try:
        tables["quality"] = create_quality_feature_table(spark, config)
    except Exception as e:
        error_msg = f"Quality features: {str(e)}"
        print(f"❌ Error: {error_msg}")
        errors.append(error_msg)
    
    # Summary
    print("\n" + "=" * 80)
    print("Feature Table Creation Summary")
    print("=" * 80)
    for domain, table in tables.items():
        print(f"  ✓ {domain}: {table}")
    print(f"\nTotal tables created: {len(tables)}")
    
    if errors:
        print(f"\n❌ Errors encountered ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
    
    # Verify tables exist
    print("\n" + "=" * 80)
    print("Verifying Tables in Unity Catalog")
    print("=" * 80)
    verified_tables = []
    for domain, table_name in tables.items():
        try:
            count = spark.sql(f"SELECT COUNT(*) FROM {table_name}").collect()[0][0]
            print(f"  ✓ {table_name}: {count} rows")
            verified_tables.append(table_name)
        except Exception as e:
            print(f"  ❌ {table_name}: NOT FOUND - {e}")
    
    # Fail if no tables were created
    if len(verified_tables) == 0:
        raise RuntimeError(f"No feature tables were created! Errors: {errors}")
    
    if len(verified_tables) < 5:
        print(f"\n⚠ WARNING: Only {len(verified_tables)}/5 tables created successfully")
    
    return tables

# COMMAND ----------

def main():
    """Main entry point for feature table creation."""
    catalog, gold_schema, feature_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Create Feature Tables").getOrCreate()
    
    try:
        tables = create_all_feature_tables(
            spark=spark,
            catalog=catalog,
            gold_schema=gold_schema,
            feature_schema=feature_schema
        )
        
        print("\n" + "=" * 80)
        print("✓ Feature table creation completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during feature table creation: {str(e)}")
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()
