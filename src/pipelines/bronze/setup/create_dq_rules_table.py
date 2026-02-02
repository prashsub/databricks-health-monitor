# Databricks notebook source
"""
TRAINING MATERIAL: Configuration-as-Data Pattern
=================================================

This script creates the DQ rules configuration table, demonstrating
the "Configuration-as-Data" pattern for runtime-configurable systems.

WHY CONFIGURATION-AS-DATA:
--------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PATTERN              │  CHANGE PROCESS                │  DOWNTIME     │
├───────────────────────┼────────────────────────────────┼───────────────┤
│  Hardcoded in Python  │  Code change → PR → Deploy     │  Yes          │
│  Config file (YAML)   │  File change → Deploy          │  Yes          │
│  Delta Table ✅        │  SQL UPDATE → Immediate        │  No           │
└───────────────────────┴────────────────────────────────┴───────────────┘

RUNTIME QUERY PATTERN:
----------------------

DLT pipelines query rules at runtime (not at deploy time):

    @dlt.expect_all_or_drop(get_critical_rules_for_table("audit"))
    def audit():
        ...

get_critical_rules_for_table() queries the Delta table at pipeline start,
so rule changes take effect on next pipeline run without redeployment.

TABLE PROPERTIES FOR CHANGE TRACKING:
-------------------------------------

    'delta.enableChangeDataFeed' = 'true'    # Audit trail of rule changes
    'delta.enableRowTracking' = 'true'       # Track row-level modifications
    'delta.enableDeletionVectors' = 'true'   # Fast deletes

These properties enable:
- Audit history of who changed what rule when
- Frontend app can show rule change history
- Compliance reporting on DQ configuration changes

Usage:
    databricks bundle run dq_rules_setup_job
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit
import uuid

def create_dq_rules_table(spark: SparkSession, catalog: str, schema: str):
    """Create dq_rules configuration table."""
    
    table_name = f"{catalog}.{schema}.dq_rules"
    
    print(f"Creating DQ rules configuration table: {table_name}")
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        rule_id STRING NOT NULL COMMENT 'Unique identifier for the rule (UUID)',
        table_name STRING NOT NULL COMMENT 'Bronze table name (e.g., audit, usage)',
        rule_name STRING NOT NULL COMMENT 'Descriptive rule name (e.g., valid_event_id)',
        rule_constraint STRING NOT NULL COMMENT 'SQL constraint expression',
        severity STRING NOT NULL COMMENT 'Severity: critical or warning',
        enabled BOOLEAN NOT NULL COMMENT 'Whether this rule is active',
        description STRING COMMENT 'Human-readable explanation of the rule',
        created_by STRING COMMENT 'User who created this rule',
        created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp',
        updated_by STRING COMMENT 'User who last updated this rule',
        updated_at TIMESTAMP NOT NULL COMMENT 'Last update timestamp',
        
        CONSTRAINT pk_dq_rules PRIMARY KEY (rule_id) NOT ENFORCED
    )
    USING DELTA
    CLUSTER BY AUTO
    COMMENT 'Data quality rules configuration for Bronze layer DLT pipelines. User-modifiable via frontend app.'
    TBLPROPERTIES (
        'delta.enableChangeDataFeed' = 'true',
        'delta.enableRowTracking' = 'true',
        'delta.enableDeletionVectors' = 'true',
        'delta.autoOptimize.autoCompact' = 'true',
        'delta.autoOptimize.optimizeWrite' = 'true',
        'layer' = 'bronze',
        'domain' = 'data_quality',
        'entity_type' = 'configuration',
        'contains_pii' = 'false',
        'data_classification' = 'internal',
        'business_owner' = 'Platform Engineering',
        'technical_owner' = 'Data Engineering'
    )
    """
    
    spark.sql(create_sql)
    print(f"✓ Created {table_name}")
    
    # Verify table
    row_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]["cnt"]
    print(f"  Current rule count: {row_count}")

def main():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("system_bronze_schema")
    
    print(f"Parameters: catalog={catalog}, schema={schema}")
    
    spark = SparkSession.builder.appName("Create DQ Rules Table").getOrCreate()
    
    try:
        create_dq_rules_table(spark, catalog, schema)
        print("\n" + "=" * 80)
        print("✓ DQ rules table setup completed!")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()

