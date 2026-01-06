# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
import sys
import os

try:
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================
"""
Create Agent Schema (Consolidated)
==================================

Creates a SINGLE Unity Catalog schema for all agent data (avoids schema sprawl):
- Models: health_monitor_agent
- Tables (Structured): config, evaluation, inference logs, memory
- Volumes (Unstructured): runbooks, embeddings, artifacts

Schema Naming Convention:
    Dev: prashanth_subrahmanyam_catalog.dev_<user>_system_gold_agent
    Prod: main.system_gold_agent
"""

# COMMAND ----------

from pyspark.sql import SparkSession


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    agent_schema = dbutils.widgets.get("agent_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Agent Schema: {agent_schema}")
    
    return catalog, agent_schema


def create_schema_if_not_exists(spark: SparkSession, catalog: str, schema: str, comment: str):
    """Create schema with proper comment and properties."""
    print(f"Creating schema: {catalog}.{schema}")
    
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    
    spark.sql(f"""
        CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}
        COMMENT '{comment}'
    """)
    
    # Enable predictive optimization
    try:
        spark.sql(f"ALTER SCHEMA {catalog}.{schema} ENABLE PREDICTIVE OPTIMIZATION")
        print(f"  ✓ Enabled predictive optimization")
    except Exception as e:
        print(f"  ⚠ Could not enable predictive optimization: {e}")
    
    print(f"  ✓ Schema {catalog}.{schema} created")


def create_volume_if_not_exists(spark: SparkSession, catalog: str, schema: str, volume: str, comment: str):
    """Create a managed volume for unstructured data."""
    volume_path = f"{catalog}.{schema}.{volume}"
    print(f"Creating volume: {volume_path}")
    
    spark.sql(f"""
        CREATE VOLUME IF NOT EXISTS {volume_path}
        COMMENT '{comment}'
    """)
    
    print(f"  ✓ Volume {volume_path} created")


def create_config_tables(spark: SparkSession, catalog: str, schema: str):
    """Create configuration and experimentation tables."""
    print(f"\nCreating config tables...")
    
    # Agent configuration table
    # Note: No DEFAULT values - not supported without delta.feature.allowColumnDefaults
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.agent_config (
            config_key STRING NOT NULL COMMENT 'Configuration parameter name',
            config_value STRING COMMENT 'Configuration parameter value',
            config_type STRING COMMENT 'Type: string, int, float, json',
            description STRING COMMENT 'Human-readable description',
            updated_at TIMESTAMP COMMENT 'Last update time',
            updated_by STRING COMMENT 'User who made the update',
            CONSTRAINT pk_agent_config PRIMARY KEY (config_key)
        )
        COMMENT 'Runtime configuration for the Health Monitor Agent'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'config'
        )
    """)
    print(f"  ✓ agent_config")
    
    # A/B test assignments table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.ab_test_assignments (
            user_id STRING NOT NULL COMMENT 'User identifier',
            experiment_name STRING NOT NULL COMMENT 'Name of the A/B test',
            variant STRING NOT NULL COMMENT 'Assigned variant: control, variant_A, etc.',
            assigned_at TIMESTAMP COMMENT 'Assignment timestamp',
            CONSTRAINT pk_ab_test PRIMARY KEY (user_id, experiment_name)
        )
        COMMENT 'A/B test variant assignments for prompt experiments'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'experimentation'
        )
    """)
    print(f"  ✓ ab_test_assignments")


def create_evaluation_tables(spark: SparkSession, catalog: str, schema: str):
    """Create evaluation-related tables."""
    print(f"\nCreating evaluation tables...")
    
    # Evaluation datasets table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.evaluation_datasets (
            dataset_id STRING NOT NULL COMMENT 'Unique dataset identifier',
            dataset_name STRING NOT NULL COMMENT 'Human-readable dataset name',
            query STRING NOT NULL COMMENT 'Test query',
            expected_domains ARRAY<STRING> COMMENT 'Expected domain classifications',
            expected_response_keywords ARRAY<STRING> COMMENT 'Keywords expected in response',
            difficulty STRING COMMENT 'easy, medium, hard',
            domain_focus STRING COMMENT 'Primary domain: cost, security, performance, reliability, quality',
            created_at TIMESTAMP COMMENT 'Creation timestamp',
            CONSTRAINT pk_eval_datasets PRIMARY KEY (dataset_id)
        )
        COMMENT 'Benchmark datasets for agent evaluation'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'evaluation'
        )
    """)
    print(f"  ✓ evaluation_datasets")
    
    # Evaluation results table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.evaluation_results (
            evaluation_id STRING NOT NULL COMMENT 'Unique evaluation run ID',
            mlflow_run_id STRING COMMENT 'MLflow run ID for full details',
            model_version STRING COMMENT 'Model version evaluated',
            dataset_name STRING COMMENT 'Dataset used for evaluation',
            relevance_score DOUBLE COMMENT 'MLflow Relevance scorer result',
            safety_score DOUBLE COMMENT 'MLflow Safety scorer result',
            correctness_score DOUBLE COMMENT 'MLflow Correctness scorer result',
            domain_accuracy_score DOUBLE COMMENT 'Custom domain accuracy judge',
            overall_score DOUBLE COMMENT 'Weighted average of all scores',
            num_samples INT COMMENT 'Number of test samples',
            evaluation_timestamp TIMESTAMP COMMENT 'Evaluation timestamp',
            CONSTRAINT pk_eval_results PRIMARY KEY (evaluation_id)
        )
        COMMENT 'Aggregated evaluation results for agent versions'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'evaluation'
        )
    """)
    print(f"  ✓ evaluation_results")


def create_inference_tables(spark: SparkSession, catalog: str, schema: str):
    """Create inference logging tables (prefix: inference_*)."""
    print(f"\nCreating inference tables...")
    
    # Note: These tables are typically auto-created by Model Serving auto-capture,
    # but we create them here for manual logging and schema consistency.
    
    # Request logs
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.inference_request_logs (
            request_id STRING NOT NULL COMMENT 'Unique request identifier',
            session_id STRING COMMENT 'Session identifier for multi-turn conversations',
            user_id STRING COMMENT 'User identifier',
            timestamp TIMESTAMP NOT NULL COMMENT 'Request timestamp',
            messages ARRAY<STRUCT<role: STRING, content: STRING>> COMMENT 'Input messages',
            custom_inputs MAP<STRING, STRING> COMMENT 'Additional custom inputs',
            model_version STRING COMMENT 'Model version used',
            CONSTRAINT pk_inference_request PRIMARY KEY (request_id)
        )
        COMMENT 'Agent inference request logs for monitoring and debugging'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'inference'
        )
    """)
    print(f"  ✓ inference_request_logs")
    
    # Response logs
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.inference_response_logs (
            request_id STRING NOT NULL COMMENT 'Links to inference_request_logs',
            timestamp TIMESTAMP NOT NULL COMMENT 'Response timestamp',
            response_content STRING COMMENT 'Generated response content',
            domains ARRAY<STRING> COMMENT 'Domains that handled the query',
            confidence DOUBLE COMMENT 'Response confidence score (0-1)',
            sources ARRAY<STRING> COMMENT 'Data sources referenced',
            latency_ms BIGINT COMMENT 'End-to-end latency in milliseconds',
            token_count_input INT COMMENT 'Input token count',
            token_count_output INT COMMENT 'Output token count',
            error STRING COMMENT 'Error message if failed',
            CONSTRAINT pk_inference_response PRIMARY KEY (request_id)
        )
        COMMENT 'Agent inference response logs with metrics'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'inference'
        )
    """)
    print(f"  ✓ inference_response_logs")


def create_memory_tables(spark: SparkSession, catalog: str, schema: str):
    """Create memory tables (prefix: memory_*)."""
    print(f"\nCreating memory tables...")
    
    # Note: These are managed by Lakebase but we create structure for reference
    
    # Short-term memory (conversation context)
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.memory_short_term (
            session_id STRING NOT NULL COMMENT 'Session identifier',
            user_id STRING NOT NULL COMMENT 'User identifier',
            checkpoint_id STRING NOT NULL COMMENT 'LangGraph checkpoint ID',
            thread_id STRING COMMENT 'Conversation thread ID',
            state_data STRING COMMENT 'Serialized state JSON',
            created_at TIMESTAMP COMMENT 'Creation timestamp',
            expires_at TIMESTAMP COMMENT 'TTL expiration (default: 24h)',
            CONSTRAINT pk_memory_short PRIMARY KEY (session_id, checkpoint_id)
        )
        COMMENT 'Short-term conversation memory (TTL: 24 hours)'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'memory'
        )
    """)
    print(f"  ✓ memory_short_term")
    
    # Long-term memory (user preferences and insights)
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.memory_long_term (
            memory_id STRING NOT NULL COMMENT 'Unique memory identifier',
            user_id STRING NOT NULL COMMENT 'User identifier',
            memory_type STRING COMMENT 'preference, insight, history',
            key STRING NOT NULL COMMENT 'Memory key/topic',
            value STRING COMMENT 'Memory content',
            embedding ARRAY<FLOAT> COMMENT 'Vector embedding for semantic search',
            metadata MAP<STRING, STRING> COMMENT 'Additional metadata',
            created_at TIMESTAMP COMMENT 'Creation timestamp',
            updated_at TIMESTAMP COMMENT 'Last update timestamp',
            expires_at TIMESTAMP COMMENT 'TTL expiration (default: 365 days)',
            CONSTRAINT pk_memory_long PRIMARY KEY (memory_id)
        )
        COMMENT 'Long-term user preferences and insights (TTL: 365 days)'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'agent',
            'domain' = 'memory'
        )
    """)
    print(f"  ✓ memory_long_term")


def main():
    """Main entry point."""
    catalog, agent_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Agent Schema Setup").getOrCreate()
    
    try:
        # =====================================================================
        # 1. Create Schema
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Creating Consolidated Agent Schema")
        print("=" * 70)
        
        create_schema_if_not_exists(
            spark, catalog, agent_schema,
            "Health Monitor Agent - models, config, evaluation, inference, memory"
        )
        
        # =====================================================================
        # 2. Create Volumes (Unstructured Data)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Creating Volumes (Unstructured Data)")
        print("=" * 70)
        
        create_volume_if_not_exists(
            spark, catalog, agent_schema, "runbooks",
            "RAG knowledge base: troubleshooting guides, best practices, docs"
        )
        
        create_volume_if_not_exists(
            spark, catalog, agent_schema, "embeddings",
            "Pre-computed vector embeddings for RAG retrieval"
        )
        
        create_volume_if_not_exists(
            spark, catalog, agent_schema, "artifacts",
            "Model artifacts, checkpoints, and miscellaneous files"
        )
        
        # =====================================================================
        # 3. Create Tables (Structured Data)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Creating Tables (Structured Data)")
        print("=" * 70)
        
        create_config_tables(spark, catalog, agent_schema)
        create_evaluation_tables(spark, catalog, agent_schema)
        create_inference_tables(spark, catalog, agent_schema)
        create_memory_tables(spark, catalog, agent_schema)
        
        # =====================================================================
        # Summary
        # =====================================================================
        print("\n" + "=" * 70)
        print("✓ Agent infrastructure created successfully!")
        print("=" * 70)
        print(f"\nSchema: {catalog}.{agent_schema}")
        print(f"\n[MODEL]")
        print(f"  └── health_monitor_agent (created via log_agent_model.py)")
        print(f"\n[TABLES] Structured Data")
        print(f"  ├── agent_config           (config)")
        print(f"  ├── ab_test_assignments    (experimentation)")
        print(f"  ├── evaluation_datasets    (evaluation)")
        print(f"  ├── evaluation_results     (evaluation)")
        print(f"  ├── inference_request_logs (inference)")
        print(f"  ├── inference_response_logs(inference)")
        print(f"  ├── memory_short_term      (memory, TTL: 24h)")
        print(f"  └── memory_long_term       (memory, TTL: 365d)")
        print(f"\n[VOLUMES] Unstructured Data")
        print(f"  ├── runbooks/              (RAG knowledge base)")
        print(f"  ├── embeddings/            (vector embeddings)")
        print(f"  └── artifacts/             (checkpoints, files)")
        
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Error creating infrastructure: {str(e)}")
        raise


# COMMAND ----------

if __name__ == "__main__":
    main()
