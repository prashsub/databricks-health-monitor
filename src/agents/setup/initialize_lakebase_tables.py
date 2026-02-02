"""
TRAINING MATERIAL: Lakebase Memory Schema Design
=================================================

This script demonstrates manual initialization of Lakebase memory tables,
providing visibility into the schema that powers agent memory.

LAKEBASE MEMORY ARCHITECTURE:
-----------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  AGENT MEMORY SYSTEM                                                     │
│                                                                         │
│  ┌─────────────────────────┐    ┌─────────────────────────────────────┐│
│  │  SHORT-TERM MEMORY      │    │  LONG-TERM MEMORY                   ││
│  │  (checkpoints table)    │    │  (store table)                      ││
│  ├─────────────────────────┤    ├─────────────────────────────────────┤│
│  │  • Conversation state   │    │  • User preferences                 ││
│  │  • LangGraph checkpoints│    │  • Learned insights                 ││
│  │  • Thread-based         │    │  • User namespace isolation         ││
│  │  • 24h retention        │    │  • 1 year retention                 ││
│  │  • Per-conversation     │    │  • Cross-conversation               ││
│  └─────────────────────────┘    └─────────────────────────────────────┘│
│                                                                         │
│  Key: thread_id + checkpoint_ns  Key: namespace + key                  │
└─────────────────────────────────────────────────────────────────────────┘

CHECKPOINTS TABLE (Short-Term):

    Schema matches langgraph-checkpoint-databricks requirements:
    - thread_id: Conversation identifier
    - checkpoint_ns: Namespace for isolation
    - checkpoint_id: Unique checkpoint ID
    - checkpoint: Serialized LangGraph state (JSON)
    - metadata: Additional context

STORE TABLE (Long-Term):

    Schema matches DatabricksStore requirements:
    - namespace: User isolation (e.g., "user_123")
    - key: Memory key (e.g., "preferences", "insights")
    - value: Serialized memory content (JSON)
    - Vector embedding for semantic search

AUTO-CREATION vs MANUAL:

Normally tables auto-create on first agent query. Manual creation is useful for:
- Pre-initialization in CI/CD pipelines
- Schema validation before deployment
- Testing memory isolation

Usage:
    databricks bundle exec python src/agents/setup/initialize_lakebase_tables.py
"""

import os
import sys
from datetime import datetime
from pyspark.sql import SparkSession


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def print_success(message: str):
    """Print success message."""
    print(f"  ✅ {message}")


def print_info(message: str, indent: int = 2):
    """Print info message."""
    print(f"{' ' * indent}• {message}")


def print_error(message: str):
    """Print error message."""
    print(f"  ❌ {message}")


def create_checkpoints_table(spark: SparkSession, catalog: str, schema: str) -> bool:
    """
    Create the checkpoints table for short-term memory (LangGraph CheckpointSaver).
    
    Schema matches langgraph-checkpoint-databricks requirements.
    """
    print_section("Creating Short-Term Memory Table (checkpoints)")
    
    table_name = f"{catalog}.{schema}.checkpoints"
    print_info(f"Table: {table_name}")
    
    try:
        # Create table with schema matching CheckpointSaver requirements
        spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                thread_id STRING NOT NULL,
                checkpoint_ns STRING NOT NULL,
                checkpoint_id STRING NOT NULL,
                parent_checkpoint_id STRING,
                type STRING,
                checkpoint STRING,
                metadata STRING,
                created_at TIMESTAMP DEFAULT current_timestamp(),
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id) NOT ENFORCED
            )
            USING DELTA
            COMMENT 'Short-term memory for agent conversations (24h retention)'
            TBLPROPERTIES (
                'delta.enableChangeDataFeed' = 'true',
                'delta.deletedFileRetentionDuration' = 'interval 1 days',
                'delta.logRetentionDuration' = 'interval 1 days',
                'memory_type' = 'short_term',
                'retention_hours' = '24',
                'managed_by' = 'health_monitor_agent'
            )
        """)
        
        print_success("Table created successfully")
        
        # Verify table exists
        count = spark.sql(f"SELECT COUNT(*) as count FROM {table_name}").collect()[0]["count"]
        print_info(f"Current row count: {count}")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to create table: {str(e)}")
        return False


def create_store_table(spark: SparkSession, catalog: str, schema: str) -> bool:
    """
    Create the store table for long-term memory (DatabricksStore).
    
    Schema matches langgraph-checkpoint-databricks requirements.
    """
    print_section("Creating Long-Term Memory Table (store)")
    
    table_name = f"{catalog}.{schema}.store"
    print_info(f"Table: {table_name}")
    
    try:
        # Create table with schema matching DatabricksStore requirements
        spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                namespace STRING NOT NULL,
                key STRING NOT NULL,
                value STRING,
                created_at TIMESTAMP DEFAULT current_timestamp(),
                updated_at TIMESTAMP DEFAULT current_timestamp(),
                PRIMARY KEY (namespace, key) NOT ENFORCED
            )
            USING DELTA
            COMMENT 'Long-term memory for agent user preferences and insights (1yr retention)'
            TBLPROPERTIES (
                'delta.enableChangeDataFeed' = 'true',
                'delta.deletedFileRetentionDuration' = 'interval 30 days',
                'delta.logRetentionDuration' = 'interval 30 days',
                'memory_type' = 'long_term',
                'retention_days' = '365',
                'managed_by' = 'health_monitor_agent'
            )
        """)
        
        print_success("Table created successfully")
        
        # Verify table exists
        count = spark.sql(f"SELECT COUNT(*) as count FROM {table_name}").collect()[0]["count"]
        print_info(f"Current row count: {count}")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to create table: {str(e)}")
        return False


def verify_schema_permissions(spark: SparkSession, catalog: str, schema: str) -> bool:
    """Verify schema exists and we have write permissions."""
    print_section("Verifying Schema Permissions")
    
    print_info(f"Catalog: {catalog}")
    print_info(f"Schema: {schema}")
    
    try:
        # Check if schema exists
        schemas = spark.sql(f"SHOW SCHEMAS IN {catalog}").collect()
        schema_names = [row.databaseName for row in schemas]
        
        if schema not in schema_names:
            print_error(f"Schema {schema} does not exist in catalog {catalog}")
            print_info(f"Available schemas: {', '.join(schema_names)}")
            return False
        
        print_success(f"Schema {catalog}.{schema} exists")
        
        # Try to show tables (tests read permission)
        tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
        print_info(f"Schema contains {len(tables)} tables")
        
        return True
        
    except Exception as e:
        print_error(f"Permission check failed: {str(e)}")
        return False


def main():
    """Main initialization flow."""
    print_section("LAKEBASE MEMORY TABLES INITIALIZATION")
    print_info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Get configuration
    catalog = os.environ.get("CATALOG", "prashanth_subrahmanyam_catalog")
    schema = os.environ.get("AGENT_SCHEMA", "dev_prashanth_subrahmanyam_system_gold_agent")
    
    print_info(f"Target Schema: {catalog}.{schema}")
    
    # Initialize Spark
    spark = SparkSession.builder.appName("Initialize Lakebase Memory").getOrCreate()
    
    # Verify permissions
    if not verify_schema_permissions(spark, catalog, schema):
        print()
        print_section("❌ INITIALIZATION FAILED - PERMISSION ISSUE")
        print_info("Required Actions:")
        print("    1. Verify the schema exists")
        print("    2. Ensure you have CREATE TABLE permission on the schema")
        print("    3. Contact your workspace admin if needed")
        return 1
    
    # Create tables
    checkpoints_success = create_checkpoints_table(spark, catalog, schema)
    store_success = create_store_table(spark, catalog, schema)
    
    # Summary
    print_section("INITIALIZATION SUMMARY")
    print()
    print_info(f"Short-term memory (checkpoints): {'✅ CREATED' if checkpoints_success else '❌ FAILED'}")
    print_info(f"Long-term memory (store):        {'✅ CREATED' if store_success else '❌ FAILED'}")
    
    if checkpoints_success and store_success:
        print()
        print_success("All memory tables initialized successfully!")
        print()
        print_info("Next Steps:")
        print("    1. Run verification script:")
        print("       python src/agents/setup/verify_lakebase_memory.py")
        print()
        print("    2. Test agent memory by querying your endpoint")
        print("       • Send 2-3 test queries")
        print("       • Check that new rows appear in the tables")
        print()
        print_section("✅ INITIALIZATION COMPLETE")
        return 0
    else:
        print()
        print_error("Some tables failed to initialize")
        print_info("Review error messages above and fix issues before retrying")
        print()
        print_section("❌ INITIALIZATION INCOMPLETE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
