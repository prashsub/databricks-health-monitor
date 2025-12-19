# Databricks notebook source
"""
Feature Engineering Utilities for Databricks Health Monitor
============================================================

This module provides utilities for Feature Engineering in Unity Catalog,
following official Databricks best practices for feature store integration.

Key Features:
- Feature tables in Unity Catalog
- FeatureLookup for training set creation
- Time series features with point-in-time lookups
- Automatic lineage tracking

Reference: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/feature-store/
"""

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureEngineeringConfig:
    """
    Configuration for Feature Engineering in Unity Catalog.
    
    Attributes:
        catalog: Unity Catalog name
        schema: Schema name for feature tables
        gold_schema: Schema name for Gold layer source tables
    """
    catalog: str
    schema: str
    gold_schema: str
    
    def get_feature_table_name(self, table_name: str) -> str:
        """Get fully qualified feature table name."""
        return f"{self.catalog}.{self.schema}.{table_name}"
    
    def get_gold_table_name(self, table_name: str) -> str:
        """Get fully qualified Gold layer table name."""
        return f"{self.catalog}.{self.gold_schema}.{table_name}"


def get_feature_engineering_client() -> FeatureEngineeringClient:
    """Get Feature Engineering client for Unity Catalog."""
    return FeatureEngineeringClient()


def create_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    table_name: str,
    df: DataFrame,
    primary_keys: List[str],
    description: str,
    timestamp_keys: Optional[List[str]] = None,
    partition_columns: Optional[List[str]] = None,
    tags: Optional[Dict[str, str]] = None
) -> str:
    """
    Create or update a feature table in Unity Catalog.
    
    Feature Engineering in Unity Catalog uses any Delta table with a primary key
    as a feature table. This function ensures proper table creation with all
    required metadata.
    
    Args:
        spark: SparkSession
        config: Feature engineering configuration
        table_name: Name of the feature table
        df: DataFrame containing feature data
        primary_keys: List of primary key columns
        description: Table description
        timestamp_keys: Timestamp columns for time series features (point-in-time lookups)
        partition_columns: Columns to partition by
        tags: Optional tags for the table
        
    Returns:
        Fully qualified table name
    """
    fe = get_feature_engineering_client()
    full_table_name = config.get_feature_table_name(table_name)
    
    # Prepare table properties
    table_properties = {
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "feature_store",
        "project": "databricks_health_monitor",
    }
    
    if tags:
        table_properties.update(tags)
    
    # Check if table exists
    table_exists = spark.catalog.tableExists(full_table_name)
    
    if table_exists:
        # Update existing feature table
        logger.info(f"Updating existing feature table: {full_table_name}")
        
        # Write new data using merge
        fe.write_table(
            name=full_table_name,
            df=df,
            mode="merge",
        )
    else:
        # Create new feature table
        logger.info(f"Creating new feature table: {full_table_name}")
        
        # Build CREATE TABLE statement with proper syntax
        pk_str = ", ".join(primary_keys)
        
        # Create table using Spark SQL for full control
        # First create an empty table with the schema
        temp_view_name = f"temp_features_{table_name}"
        df.createOrReplaceTempView(temp_view_name)
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {full_table_name}
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        COMMENT '{description}'
        AS SELECT * FROM {temp_view_name}
        """
        
        spark.sql(create_sql)
        
        # Add primary key constraint
        alter_pk_sql = f"""
        ALTER TABLE {full_table_name}
        ADD CONSTRAINT pk_{table_name} PRIMARY KEY ({pk_str}) NOT ENFORCED
        """
        try:
            spark.sql(alter_pk_sql)
        except Exception as e:
            logger.warning(f"Could not add primary key constraint: {e}")
    
    logger.info(f"Feature table ready: {full_table_name}")
    return full_table_name


def get_feature_lookups(
    config: FeatureEngineeringConfig,
    feature_specs: List[Dict[str, Any]]
) -> List[FeatureLookup]:
    """
    Create FeatureLookup objects for training set creation.
    
    Args:
        config: Feature engineering configuration
        feature_specs: List of feature specifications, each containing:
            - table_name: Name of the feature table
            - feature_names: List of feature column names
            - lookup_key: Column(s) to join on
            - timestamp_lookup_key: (optional) Timestamp column for point-in-time lookups
            
    Returns:
        List of FeatureLookup objects
    """
    feature_lookups = []
    
    for spec in feature_specs:
        table_name = config.get_feature_table_name(spec["table_name"])
        
        lookup_kwargs = {
            "table_name": table_name,
            "feature_names": spec["feature_names"],
            "lookup_key": spec["lookup_key"],
        }
        
        # Add timestamp for point-in-time lookups
        if "timestamp_lookup_key" in spec:
            lookup_kwargs["timestamp_lookup_key"] = spec["timestamp_lookup_key"]
        
        feature_lookups.append(FeatureLookup(**lookup_kwargs))
    
    return feature_lookups


def create_training_set(
    config: FeatureEngineeringConfig,
    training_df: DataFrame,
    feature_lookups: List[FeatureLookup],
    label: str,
    exclude_columns: Optional[List[str]] = None
) -> DataFrame:
    """
    Create a training set by joining features from feature tables.
    
    This uses Feature Engineering in Unity Catalog to:
    - Automatically track lineage
    - Enable feature lookup at inference time
    - Support point-in-time correctness for time series
    
    Args:
        config: Feature engineering configuration
        training_df: Base DataFrame with labels and lookup keys
        feature_lookups: List of FeatureLookup objects
        label: Name of the label column
        exclude_columns: Columns to exclude from the training set
        
    Returns:
        TrainingSet.load_df() result - DataFrame ready for training
    """
    fe = get_feature_engineering_client()
    
    training_set = fe.create_training_set(
        df=training_df,
        feature_lookups=feature_lookups,
        label=label,
        exclude_columns=exclude_columns or [],
    )
    
    # Load the training DataFrame
    training_data = training_set.load_df()
    
    logger.info(f"Training set created with {training_data.count()} rows")
    logger.info(f"Features: {training_data.columns}")
    
    return training_data


# =============================================================================
# Feature Engineering Functions for Each Agent Domain
# =============================================================================

def compute_cost_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 90
) -> DataFrame:
    """
    Compute cost-related features from Gold layer tables.
    
    Features include:
    - Daily/hourly DBU usage and cost
    - Rolling statistics (7-day, 30-day moving averages)
    - Z-scores for anomaly detection
    - Cyclical features for seasonality
    - Tag-based features for chargeback
    
    Args:
        spark: SparkSession
        config: Feature engineering configuration
        lookback_days: Number of days to look back
        
    Returns:
        DataFrame with computed features
    """
    fact_usage = config.get_gold_table_name("fact_usage")
    dim_workspace = config.get_gold_table_name("dim_workspace")
    dim_sku = config.get_gold_table_name("dim_sku")
    
    # Define window specifications
    window_7d = Window.partitionBy("workspace_id").orderBy("usage_date").rowsBetween(-7, -1)
    window_30d = Window.partitionBy("workspace_id").orderBy("usage_date").rowsBetween(-30, -1)
    
    cost_features = spark.sql(f"""
        WITH daily_usage AS (
            SELECT 
                u.usage_date,
                u.workspace_id,
                w.workspace_name,
                u.sku_name,
                s.sku_category,
                SUM(u.usage_quantity) AS daily_dbu,
                COUNT(DISTINCT u.usage_metadata_job_id) AS job_count,
                COUNT(DISTINCT u.usage_metadata_cluster_id) AS cluster_count,
                COUNT(DISTINCT u.usage_metadata_warehouse_id) AS warehouse_count
            FROM {fact_usage} u
            LEFT JOIN {dim_workspace} w 
                ON u.workspace_id = w.workspace_id
            LEFT JOIN {dim_sku} s
                ON u.sku_name = s.sku_name
            WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), {lookback_days})
            GROUP BY u.usage_date, u.workspace_id, w.workspace_name, u.sku_name, s.sku_category
        )
        SELECT 
            usage_date,
            workspace_id,
            workspace_name,
            sku_name,
            sku_category,
            daily_dbu,
            job_count,
            cluster_count,
            warehouse_count,
            -- Cyclical features
            SIN(2 * PI() * DAYOFWEEK(usage_date) / 7) AS dow_sin,
            COS(2 * PI() * DAYOFWEEK(usage_date) / 7) AS dow_cos,
            SIN(2 * PI() * DAYOFMONTH(usage_date) / 31) AS dom_sin,
            COS(2 * PI() * DAYOFMONTH(usage_date) / 31) AS dom_cos,
            -- Contextual features
            CASE WHEN DAYOFWEEK(usage_date) IN (1, 7) THEN 1 ELSE 0 END AS is_weekend,
            CASE WHEN DAYOFMONTH(usage_date) >= 25 THEN 1 ELSE 0 END AS is_month_end,
            -- Timestamp for time series
            usage_date AS feature_timestamp
        FROM daily_usage
    """)
    
    # Add window-based features using PySpark
    cost_features = cost_features \
        .withColumn("dbu_7day_avg", F.avg("daily_dbu").over(window_7d)) \
        .withColumn("dbu_7day_std", F.stddev("daily_dbu").over(window_7d)) \
        .withColumn("dbu_30day_avg", F.avg("daily_dbu").over(window_30d)) \
        .withColumn("z_score", 
            F.when(F.col("dbu_7day_std") > 0,
                (F.col("daily_dbu") - F.col("dbu_7day_avg")) / F.col("dbu_7day_std")
            ).otherwise(0)
        ) \
        .withColumn("pct_change_7day",
            F.when(F.col("dbu_7day_avg") > 0,
                (F.col("daily_dbu") - F.col("dbu_7day_avg")) / F.col("dbu_7day_avg") * 100
            ).otherwise(0)
        ) \
        .fillna(0)
    
    return cost_features


def compute_security_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 30
) -> DataFrame:
    """
    Compute security-related features from Gold layer tables.
    
    Features include:
    - User activity patterns
    - Access pattern anomalies
    - Off-hours activity rates
    - Sensitive data access counts
    
    Args:
        spark: SparkSession
        config: Feature engineering configuration
        lookback_days: Number of days to look back
        
    Returns:
        DataFrame with computed features
    """
    fact_table_lineage = config.get_gold_table_name("fact_table_lineage")
    
    window_7d = Window.partitionBy("user_id").orderBy("event_date").rowsBetween(-7, -1)
    
    security_features = spark.sql(f"""
        WITH user_activity AS (
            SELECT 
                created_by AS user_id,
                DATE(event_time) AS event_date,
                COUNT(*) AS event_count,
                COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name)) AS tables_accessed,
                SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 THEN 1 ELSE 0 END) AS off_hours_events,
                SUM(CASE WHEN DAYOFWEEK(event_date) IN (1, 7) THEN 1 ELSE 0 END) AS weekend_events,
                SUM(CASE 
                    WHEN source_table_full_name LIKE '%pii%' 
                    OR source_table_full_name LIKE '%sensitive%' 
                    OR source_table_full_name LIKE '%confidential%' 
                    THEN 1 ELSE 0 
                END) AS sensitive_access
            FROM {fact_table_lineage}
            WHERE DATE(event_time) >= DATE_SUB(CURRENT_DATE(), {lookback_days})
                AND created_by IS NOT NULL
            GROUP BY created_by, DATE(event_time)
        )
        SELECT 
            user_id,
            event_date,
            event_count,
            tables_accessed,
            off_hours_events,
            weekend_events,
            sensitive_access,
            -- Derived ratios
            CASE WHEN event_count > 0 
                THEN off_hours_events / event_count 
                ELSE 0 
            END AS off_hours_rate,
            CASE WHEN event_count > 0 
                THEN weekend_events / event_count 
                ELSE 0 
            END AS weekend_rate,
            CASE WHEN event_count > 0 
                THEN sensitive_access / event_count 
                ELSE 0 
            END AS sensitive_access_rate,
            -- Timestamp
            event_date AS feature_timestamp
        FROM user_activity
        WHERE user_id IS NOT NULL
    """)
    
    # Add rolling statistics
    security_features = security_features \
        .withColumn("event_7day_avg", F.avg("event_count").over(window_7d)) \
        .withColumn("event_7day_std", F.stddev("event_count").over(window_7d)) \
        .withColumn("event_z_score",
            F.when(F.col("event_7day_std") > 0,
                (F.col("event_count") - F.col("event_7day_avg")) / F.col("event_7day_std")
            ).otherwise(0)
        ) \
        .fillna(0)
    
    return security_features


def compute_performance_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 30
) -> DataFrame:
    """
    Compute performance-related features from Gold layer tables.
    
    Features include:
    - Query performance metrics
    - Warehouse utilization
    - Queue times
    - Data volume statistics
    
    Args:
        spark: SparkSession
        config: Feature engineering configuration
        lookback_days: Number of days to look back
        
    Returns:
        DataFrame with computed features
    """
    fact_query_history = config.get_gold_table_name("fact_query_history")
    dim_warehouse = config.get_gold_table_name("dim_warehouse")
    
    performance_features = spark.sql(f"""
        SELECT 
            q.warehouse_id,
            w.name AS warehouse_name,
            w.cluster_size AS warehouse_size,
            DATE(q.start_time) AS query_date,
            COUNT(*) AS query_count,
            AVG(q.duration_ms) AS avg_duration_ms,
            PERCENTILE_APPROX(q.duration_ms, 0.5) AS p50_duration_ms,
            PERCENTILE_APPROX(q.duration_ms, 0.95) AS p95_duration_ms,
            PERCENTILE_APPROX(q.duration_ms, 0.99) AS p99_duration_ms,
            AVG(q.read_bytes) AS avg_read_bytes,
            SUM(q.read_bytes) AS total_read_bytes,
            AVG(q.spill_to_disk_bytes) AS avg_spill_bytes,
            SUM(CASE WHEN q.spill_to_disk_bytes > 0 THEN 1 ELSE 0 END) AS queries_with_spill,
            -- Error rates
            SUM(CASE WHEN q.error_message IS NOT NULL THEN 1 ELSE 0 END) AS error_count,
            -- Query type distribution
            SUM(CASE WHEN q.statement_type = 'SELECT' THEN 1 ELSE 0 END) AS select_count,
            SUM(CASE WHEN q.statement_type IN ('INSERT', 'MERGE', 'UPDATE', 'DELETE') THEN 1 ELSE 0 END) AS write_count,
            -- Time features
            DATE(q.start_time) AS feature_timestamp
        FROM {fact_query_history} q
        LEFT JOIN {dim_warehouse} w 
            ON q.warehouse_id = w.warehouse_id
        WHERE DATE(q.start_time) >= DATE_SUB(CURRENT_DATE(), {lookback_days})
            AND q.warehouse_id IS NOT NULL
        GROUP BY q.warehouse_id, w.name, w.cluster_size, DATE(q.start_time)
    """)
    
    # Add derived features
    performance_features = performance_features \
        .withColumn("spill_rate", 
            F.when(F.col("query_count") > 0,
                F.col("queries_with_spill") / F.col("query_count")
            ).otherwise(0)
        ) \
        .withColumn("error_rate",
            F.when(F.col("query_count") > 0,
                F.col("error_count") / F.col("query_count")
            ).otherwise(0)
        ) \
        .withColumn("write_ratio",
            F.when(F.col("query_count") > 0,
                F.col("write_count") / F.col("query_count")
            ).otherwise(0)
        ) \
        .fillna(0)
    
    return performance_features


def compute_reliability_features(
    spark: SparkSession,
    config: FeatureEngineeringConfig,
    lookback_days: int = 90
) -> DataFrame:
    """
    Compute reliability-related features from Gold layer tables.
    
    Features include:
    - Job success/failure rates
    - Runtime statistics
    - Retry patterns
    - Consecutive failures
    
    Args:
        spark: SparkSession
        config: Feature engineering configuration
        lookback_days: Number of days to look back
        
    Returns:
        DataFrame with computed features
    """
    fact_job_run = config.get_gold_table_name("fact_job_run_timeline")
    dim_job = config.get_gold_table_name("dim_job")
    
    window_30d = Window.partitionBy("job_id").orderBy("run_date").rowsBetween(-30, -1)
    
    reliability_features = spark.sql(f"""
        SELECT 
            jrt.job_id,
            j.name AS job_name,
            j.task_count,
            DATE(jrt.period_start_time) AS run_date,
            COUNT(*) AS run_count,
            SUM(CASE WHEN jrt.result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS success_count,
            SUM(CASE WHEN jrt.result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END) AS failure_count,
            AVG(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time)) AS avg_duration_minutes,
            STDDEV(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time)) AS duration_std_minutes,
            MAX(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time)) AS max_duration_minutes,
            -- Timestamp
            DATE(jrt.period_start_time) AS feature_timestamp
        FROM {fact_job_run} jrt
        LEFT JOIN {dim_job} j 
            ON jrt.job_id = j.job_id
        WHERE DATE(jrt.period_start_time) >= DATE_SUB(CURRENT_DATE(), {lookback_days})
            AND jrt.result_state IS NOT NULL
        GROUP BY jrt.job_id, j.name, j.task_count, DATE(jrt.period_start_time)
    """)
    
    # Add derived features
    reliability_features = reliability_features \
        .withColumn("failure_rate",
            F.when(F.col("run_count") > 0,
                F.col("failure_count") / F.col("run_count")
            ).otherwise(0)
        ) \
        .withColumn("success_rate",
            F.when(F.col("run_count") > 0,
                F.col("success_count") / F.col("run_count")
            ).otherwise(0)
        ) \
        .withColumn("duration_cv",  # Coefficient of variation
            F.when(F.col("avg_duration_minutes") > 0,
                F.col("duration_std_minutes") / F.col("avg_duration_minutes")
            ).otherwise(0)
        ) \
        .withColumn("failure_rate_30d", F.avg("failure_rate").over(window_30d)) \
        .fillna(0)
    
    return reliability_features




