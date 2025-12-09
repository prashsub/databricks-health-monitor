# Databricks notebook source
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
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.feature_utils import (
    FeatureEngineeringConfig,
    create_feature_table,
    compute_cost_features,
    compute_security_features,
    compute_performance_features,
    compute_reliability_features,
)

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

def create_cost_feature_table(
    spark: SparkSession,
    config: FeatureEngineeringConfig
) -> str:
    """
    Create cost agent feature table.
    
    Features for:
    - Cost Anomaly Detection
    - Budget Forecasting
    - Chargeback Attribution
    - Job Cost Optimization
    """
    print("\n" + "=" * 60)
    print("Creating Cost Feature Table")
    print("=" * 60)
    
    # Compute features
    cost_features = compute_cost_features(spark, config, lookback_days=90)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="cost_features",
        df=cost_features,
        primary_keys=["workspace_id", "sku_name", "usage_date"],
        description="""
        Cost agent features for anomaly detection and forecasting.
        
        Business: Captures daily DBU usage patterns, rolling statistics,
        and contextual features (weekends, month-end) for each workspace-SKU
        combination. Used to detect cost anomalies, forecast budgets, and
        optimize job costs.
        
        Technical: Primary key is (workspace_id, sku_name, usage_date).
        Features include 7-day and 30-day rolling averages, z-scores,
        and cyclical encoding for day-of-week seasonality.
        Refreshed daily with 90-day lookback.
        """,
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
    """
    Create security agent feature table.
    
    Features for:
    - Threat Detection
    - Data Exfiltration Detection
    - Privilege Escalation Detection
    - User Behavior Baselines
    """
    print("\n" + "=" * 60)
    print("Creating Security Feature Table")
    print("=" * 60)
    
    # Compute features
    security_features = compute_security_features(spark, config, lookback_days=30)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="security_features",
        df=security_features,
        primary_keys=["user_id", "event_date"],
        description="""
        Security agent features for threat and anomaly detection.
        
        Business: Captures user activity patterns including event counts,
        tables accessed, off-hours activity, and sensitive data access.
        Used to detect security threats, data exfiltration attempts,
        and privilege escalation patterns.
        
        Technical: Primary key is (user_id, event_date).
        Features include rolling 7-day statistics, z-scores for activity
        deviation, and rates for off-hours and sensitive access.
        Refreshed daily with 30-day lookback.
        """,
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
    """
    Create performance agent feature table.
    
    Features for:
    - Query Performance Forecasting
    - Warehouse Auto-Scaler Optimization
    - Query Optimization Recommendations
    - Cluster Capacity Planning
    """
    print("\n" + "=" * 60)
    print("Creating Performance Feature Table")
    print("=" * 60)
    
    # Compute features
    performance_features = compute_performance_features(spark, config, lookback_days=30)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="performance_features",
        df=performance_features,
        primary_keys=["warehouse_id", "query_date"],
        description="""
        Performance agent features for query and warehouse optimization.
        
        Business: Captures query performance metrics by warehouse-day,
        including duration percentiles, data volume, spill rates, and
        error rates. Used to forecast query performance, optimize
        warehouse sizing, and identify query optimization opportunities.
        
        Technical: Primary key is (warehouse_id, query_date).
        Features include P50/P95/P99 durations, spill and error rates,
        read/write ratios. Refreshed daily with 30-day lookback.
        """,
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
    """
    Create reliability agent feature table.
    
    Features for:
    - Job Failure Prediction
    - Job Duration Forecasting
    - SLA Breach Prediction
    - Retry Success Prediction
    """
    print("\n" + "=" * 60)
    print("Creating Reliability Feature Table")
    print("=" * 60)
    
    # Compute features
    reliability_features = compute_reliability_features(spark, config, lookback_days=90)
    
    # Create feature table
    table_name = create_feature_table(
        spark=spark,
        config=config,
        table_name="reliability_features",
        df=reliability_features,
        primary_keys=["job_id", "run_date"],
        description="""
        Reliability agent features for job failure and SLA prediction.
        
        Business: Captures job execution patterns including success/failure
        rates, duration statistics, and historical trends. Used to predict
        job failures before execution, forecast durations, and assess
        SLA breach risk.
        
        Technical: Primary key is (job_id, run_date).
        Features include daily success/failure rates, duration mean/std,
        coefficient of variation, and 30-day rolling failure rate.
        Refreshed daily with 90-day lookback.
        """,
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

def create_all_feature_tables(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str
) -> dict:
    """
    Create all feature tables for ML model training.
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        gold_schema: Gold layer schema name
        feature_schema: Feature table schema name
        
    Returns:
        Dictionary mapping domain to table name
    """
    print("\n" + "=" * 80)
    print("Creating All Feature Tables for Databricks Health Monitor ML")
    print("=" * 80)
    
    config = FeatureEngineeringConfig(
        catalog=catalog,
        schema=feature_schema,
        gold_schema=gold_schema
    )
    
    # Ensure feature schema exists
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{feature_schema}")
    
    # Enable predictive optimization
    try:
        spark.sql(f"""
            ALTER SCHEMA {catalog}.{feature_schema}
            SET TBLPROPERTIES ('databricks.pipelines.predictiveOptimizations.enabled' = 'true')
        """)
    except Exception as e:
        print(f"Warning: Could not enable predictive optimization: {e}")
    
    # Create feature tables
    tables = {}
    
    try:
        tables["cost"] = create_cost_feature_table(spark, config)
    except Exception as e:
        print(f"Error creating cost features: {e}")
    
    try:
        tables["security"] = create_security_feature_table(spark, config)
    except Exception as e:
        print(f"Error creating security features: {e}")
    
    try:
        tables["performance"] = create_performance_feature_table(spark, config)
    except Exception as e:
        print(f"Error creating performance features: {e}")
    
    try:
        tables["reliability"] = create_reliability_feature_table(spark, config)
    except Exception as e:
        print(f"Error creating reliability features: {e}")
    
    print("\n" + "=" * 80)
    print("Feature Table Creation Summary")
    print("=" * 80)
    for domain, table in tables.items():
        print(f"  {domain}: {table}")
    print(f"\nTotal tables created: {len(tables)}")
    
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
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

