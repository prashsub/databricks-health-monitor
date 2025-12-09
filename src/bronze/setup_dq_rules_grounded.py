# Databricks notebook source
"""
Setup DQ Rules Table - GROUNDED IN ACTUAL SYSTEM TABLE SCHEMAS

Creates and populates the dq_rules Delta table with INTELLIGENT, FACT-BASED data quality rules
for all Bronze streaming tables.

Rules are grounded in:
- Actual column names from systemtablesschema CSV
- Official Databricks system tables documentation
- Enum values, conditional logic, temporal constraints, business rules

References:
- https://docs.databricks.com/aws/en/admin/system-tables/
- context/systemtables/systemtablesschema - Sheet1.csv
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, BooleanType, TimestampType
from pyspark.sql.functions import current_timestamp, md5, concat_ws, col
from datetime import datetime

def get_parameters():
    """Get job parameters from widgets."""
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Bronze Schema: {bronze_schema}")
    
    return catalog, bronze_schema

def create_dq_rules_table(spark: SparkSession, catalog: str, schema: str):
    """Create the dq_rules table if it doesn't exist."""
    
    # Ensure catalog and schema exist
    print(f"\nEnsuring catalog and schema exist...")
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    print(f"✓ Catalog and schema ready: {catalog}.{schema}")
    
    table_name = f"{catalog}.{schema}.dq_rules"
    
    print(f"\nCreating dq_rules table: {table_name}")
    
    # Drop existing table to ensure clean schema
    spark.sql(f"DROP TABLE IF EXISTS {table_name}")
    print(f"  Dropped existing table (if any)")
    
    spark.sql(f"""
        CREATE TABLE {table_name} (
            table_name STRING NOT NULL COMMENT 'Bronze table name',
            rule_name STRING NOT NULL COMMENT 'Unique rule name',
            rule_constraint STRING NOT NULL COMMENT 'SQL constraint for the rule',
            severity STRING NOT NULL COMMENT 'critical or warning',
            enabled BOOLEAN NOT NULL COMMENT 'Whether rule is active',
            description STRING COMMENT 'Rule description',
            rule_id STRING NOT NULL COMMENT 'MD5 hash (PK)',
            created_at TIMESTAMP NOT NULL COMMENT 'Rule creation timestamp',
            updated_at TIMESTAMP NOT NULL COMMENT 'Rule last update timestamp',
            CONSTRAINT pk_dq_rules PRIMARY KEY (rule_id)
        )
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'entity_type' = 'configuration',
            'description' = 'Intelligent DQ rules grounded in actual system table schemas'
        )
        COMMENT 'Configuration table for DLT data quality expectations with intelligent, fact-based rules'
    """)
    
    print(f"✓ dq_rules table created/verified: {table_name}")

def get_all_dq_rules():
    """
    Define ALL INTELLIGENT DQ rules for Bronze streaming tables.
    
    Rules are GROUNDED in actual system table schemas and official documentation.
    Categories:
    - CRITICAL: Data integrity, required fields, referential integrity
    - WARNING: Business logic, reasonableness checks, enum validation
    
    Returns:
        list: List of rule dictionaries
    """
    return [
        # ========================================================================
        # ACCESS DOMAIN - system.access.* tables
        # Reference: https://docs.databricks.com/aws/en/admin/system-tables/audit-logs
        # ========================================================================
        
        # -------------------------
        # audit (system.access.audit)
        # Schema: Lines 1-20 in CSV
        # -------------------------
        {
            "table_name": "audit",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present (primary identifier)"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event timestamp must be present"
        },
        {
            "table_name": "audit",
            "rule_name": "event_time_not_future",
            "rule_constraint": "event_time <= CURRENT_TIMESTAMP()",
            "severity": "warning",
            "description": "Event time should not be in the future"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_event_date",
            "rule_constraint": "event_date IS NOT NULL AND event_date = CAST(event_time AS DATE)",
            "severity": "critical",
            "description": "Event date must match event_time date (partition key)"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_service_name",
            "rule_constraint": "service_name IS NOT NULL AND LENGTH(service_name) > 0",
            "severity": "critical",
            "description": "Service name must be present (e.g., unityCatalog, jobs)"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_action_name",
            "rule_constraint": "action_name IS NOT NULL AND LENGTH(action_name) > 0",
            "severity": "critical",
            "description": "Action name must be present (e.g., getTable, createJob)"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_audit_level",
            "rule_constraint": "audit_level IN ('ACCOUNT_LEVEL', 'WORKSPACE_LEVEL')",
            "severity": "warning",
            "description": "Audit level should be valid enum value"
        },
        {
            "table_name": "audit",
            "rule_name": "valid_event_id",
            "rule_constraint": "event_id IS NOT NULL AND LENGTH(event_id) > 0",
            "severity": "critical",
            "description": "Event ID must be present (uniqueness key)"
        },
        
        # -------------------------
        # clean_room_events (system.access.clean_room_events)
        # Schema: Lines 400-450 in CSV
        # -------------------------
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_metastore_id",
            "rule_constraint": "metastore_id IS NOT NULL AND LENGTH(metastore_id) > 0",
            "severity": "critical",
            "description": "Metastore ID must be present"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_event_id",
            "rule_constraint": "event_id IS NOT NULL AND LENGTH(event_id) > 0",
            "severity": "critical",
            "description": "Event ID must be present"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_clean_room_name",
            "rule_constraint": "clean_room_name IS NOT NULL AND LENGTH(clean_room_name) > 0",
            "severity": "critical",
            "description": "Clean room name must be present"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event time must be present"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "event_time_not_future",
            "rule_constraint": "event_time <= CURRENT_TIMESTAMP()",
            "severity": "warning",
            "description": "Event time should not be in future"
        },
        {
            "table_name": "clean_room_events",
            "rule_name": "valid_event_type",
            "rule_constraint": "event_type IN ('CLEAN_ROOM_CREATED', 'CLEAN_ROOM_DELETED', 'RUN_NOTEBOOK_STARTED', 'RUN_NOTEBOOK_COMPLETED', 'CLEAN_ROOM_ASSETS_UPDATED', 'ASSET_REVIEW_CREATED', 'OUTPUT_SCHEMA_DELETED')",
            "severity": "warning",
            "description": "Event type should be valid clean room event"
        },
        
        # -------------------------
        # column_lineage (system.access.column_lineage)
        # Schema: Lines 21-60 in CSV
        # -------------------------
        {
            "table_name": "column_lineage",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_metastore_id",
            "rule_constraint": "metastore_id IS NOT NULL AND LENGTH(metastore_id) > 0",
            "severity": "critical",
            "description": "Metastore ID must be present"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_source_table_full_name",
            "rule_constraint": "source_table_full_name IS NOT NULL AND LENGTH(source_table_full_name) > 0",
            "severity": "critical",
            "description": "Source table full name must be present (3-part name)"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_target_table_full_name",
            "rule_constraint": "target_table_full_name IS NOT NULL AND LENGTH(target_table_full_name) > 0",
            "severity": "critical",
            "description": "Target table full name must be present (3-part name)"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_source_type",
            "rule_constraint": "source_type IN ('TABLE', 'PATH', 'VIEW', 'MATERIALIZED_VIEW', 'METRIC_VIEW', 'STREAMING_TABLE')",
            "severity": "warning",
            "description": "Source type should be valid Unity Catalog object type"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_target_type",
            "rule_constraint": "target_type IN ('TABLE', 'PATH', 'VIEW', 'MATERIALIZED_VIEW', 'METRIC_VIEW', 'STREAMING_TABLE')",
            "severity": "warning",
            "description": "Target type should be valid Unity Catalog object type"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Lineage event time must be present"
        },
        {
            "table_name": "column_lineage",
            "rule_name": "valid_entity_type",
            "rule_constraint": "entity_type IS NULL OR entity_type IN ('NOTEBOOK', 'JOB', 'PIPELINE', 'DASHBOARD_V3', 'DBSQL_DASHBOARD', 'DBSQL_QUERY')",
            "severity": "warning",
            "description": "Entity type should be valid when present"
        },
        
        # -------------------------
        # outbound_network (system.access.outbound_network)
        # Schema: Lines 452-463 in CSV
        # -------------------------
        {
            "table_name": "outbound_network",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "valid_event_id",
            "rule_constraint": "event_id IS NOT NULL AND LENGTH(event_id) > 0",
            "severity": "critical",
            "description": "Event ID must be present"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Event time must be present"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "event_time_not_future",
            "rule_constraint": "event_time <= CURRENT_TIMESTAMP()",
            "severity": "warning",
            "description": "Event time should not be in future"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "valid_destination_type",
            "rule_constraint": "destination_type IN ('DNS', 'IP', 'STORAGE')",
            "severity": "warning",
            "description": "Destination type should be DNS, IP, or STORAGE"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "valid_destination",
            "rule_constraint": "destination IS NOT NULL AND LENGTH(destination) > 0",
            "severity": "critical",
            "description": "Blocked destination must be present (domain/IP/storage path)"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "dns_event_conditional",
            "rule_constraint": "destination_type != 'DNS' OR dns_event IS NOT NULL",
            "severity": "warning",
            "description": "DNS event details should be present when destination_type=DNS"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "storage_event_conditional",
            "rule_constraint": "destination_type != 'STORAGE' OR storage_event IS NOT NULL",
            "severity": "warning",
            "description": "Storage event details should be present when destination_type=STORAGE"
        },
        {
            "table_name": "outbound_network",
            "rule_name": "valid_network_source_type",
            "rule_constraint": "network_source_type IN ('DBSQL', 'General Compute', 'MLServing', 'ML Build', 'Apps')",
            "severity": "warning",
            "description": "Network source type should be valid product/service"
        },
        
        # -------------------------
        # table_lineage (system.access.table_lineage)
        # Schema: Lines 21-60 in CSV (same as column_lineage but table-level)
        # -------------------------
        {
            "table_name": "table_lineage",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_metastore_id",
            "rule_constraint": "metastore_id IS NOT NULL AND LENGTH(metastore_id) > 0",
            "severity": "critical",
            "description": "Metastore ID must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_source_table_full_name",
            "rule_constraint": "source_table_full_name IS NOT NULL AND LENGTH(source_table_full_name) > 0",
            "severity": "critical",
            "description": "Source table full name must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_target_table_full_name",
            "rule_constraint": "target_table_full_name IS NOT NULL AND LENGTH(target_table_full_name) > 0",
            "severity": "critical",
            "description": "Target table full name must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_event_time",
            "rule_constraint": "event_time IS NOT NULL",
            "severity": "critical",
            "description": "Lineage event time must be present"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_source_type",
            "rule_constraint": "source_type IN ('TABLE', 'PATH', 'VIEW', 'MATERIALIZED_VIEW', 'METRIC_VIEW', 'STREAMING_TABLE')",
            "severity": "warning",
            "description": "Source type should be valid object type"
        },
        {
            "table_name": "table_lineage",
            "rule_name": "valid_target_type",
            "rule_constraint": "target_type IN ('TABLE', 'PATH', 'VIEW', 'MATERIALIZED_VIEW', 'METRIC_VIEW', 'STREAMING_TABLE')",
            "severity": "warning",
            "description": "Target type should be valid object type"
        },
        
        # ========================================================================
        # BILLING DOMAIN - system.billing.* tables
        # Reference: https://docs.databricks.com/aws/en/admin/system-tables/billing
        # ========================================================================
        
        # -------------------------
        # list_prices (system.billing.list_prices)
        # Schema: Lines 116-130 in CSV
        # -------------------------
        {
            "table_name": "list_prices",
            "rule_name": "valid_price_start_time",
            "rule_constraint": "price_start_time IS NOT NULL",
            "severity": "critical",
            "description": "Price effective start time must be present"
        },
        {
            "table_name": "list_prices",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "list_prices",
            "rule_name": "valid_sku_name",
            "rule_constraint": "sku_name IS NOT NULL AND LENGTH(sku_name) > 0",
            "severity": "critical",
            "description": "SKU name must be present"
        },
        {
            "table_name": "list_prices",
            "rule_name": "valid_cloud",
            "rule_constraint": "cloud IN ('AWS', 'AZURE', 'GCP')",
            "severity": "warning",
            "description": "Cloud should be AWS, AZURE, or GCP"
        },
        {
            "table_name": "list_prices",
            "rule_name": "valid_currency_code",
            "rule_constraint": "currency_code IS NOT NULL AND LENGTH(currency_code) = 3",
            "severity": "critical",
            "description": "Currency code must be 3-letter ISO code (e.g., USD)"
        },
        {
            "table_name": "list_prices",
            "rule_name": "valid_usage_unit",
            "rule_constraint": "usage_unit IS NOT NULL AND LENGTH(usage_unit) > 0",
            "severity": "critical",
            "description": "Usage unit must be present (e.g., DBU)"
        },
        {
            "table_name": "list_prices",
            "rule_name": "price_end_after_start",
            "rule_constraint": "price_end_time IS NULL OR price_end_time >= price_start_time",
            "severity": "warning",
            "description": "Price end time should be after start time when present"
        },
        
        # -------------------------
        # usage (system.billing.usage)
        # Schema: Lines 61-115 in CSV
        # -------------------------
        {
            "table_name": "usage",
            "rule_name": "valid_record_id",
            "rule_constraint": "record_id IS NOT NULL AND LENGTH(record_id) > 0",
            "severity": "critical",
            "description": "Record ID must be present (unique identifier)"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_account_id",
            "rule_constraint": "account_id IS NOT NULL AND LENGTH(account_id) > 0",
            "severity": "critical",
            "description": "Account ID must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_workspace_id",
            "rule_constraint": "workspace_id IS NOT NULL",
            "severity": "critical",
            "description": "Workspace ID must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_sku_name",
            "rule_constraint": "sku_name IS NOT NULL AND LENGTH(sku_name) > 0",
            "severity": "critical",
            "description": "SKU name must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_cloud",
            "rule_constraint": "cloud IN ('AWS', 'AZURE', 'GCP')",
            "severity": "warning",
            "description": "Cloud should be AWS, AZURE, or GCP"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_usage_start_time",
            "rule_constraint": "usage_start_time IS NOT NULL",
            "severity": "critical",
            "description": "Usage start time must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_usage_end_time",
            "rule_constraint": "usage_end_time IS NOT NULL",
            "severity": "critical",
            "description": "Usage end time must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "usage_end_after_start",
            "rule_constraint": "usage_end_time >= usage_start_time",
            "severity": "warning",
            "description": "Usage end time should be after start time"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_usage_date",
            "rule_constraint": "usage_date IS NOT NULL AND usage_date = CAST(usage_start_time AS DATE)",
            "severity": "critical",
            "description": "Usage date must match usage_start_time date (partition key)"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_usage_unit",
            "rule_constraint": "usage_unit IS NOT NULL",
            "severity": "critical",
            "description": "Usage unit must be present"
        },
        {
            "table_name": "usage",
            "rule_name": "positive_usage_quantity",
            "rule_constraint": "usage_quantity >= 0",
            "severity": "critical",
            "description": "Usage quantity must be non-negative"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_record_type",
            "rule_constraint": "record_type IN ('ORIGINAL', 'RETRACTION', 'RESTATEMENT')",
            "severity": "warning",
            "description": "Record type should be valid correction type"
        },
        {
            "table_name": "usage",
            "rule_name": "valid_usage_type",
            "rule_constraint": "usage_type IN ('COMPUTE_TIME', 'STORAGE_SPACE', 'NETWORK_BYTE', 'NETWORK_HOUR', 'API_OPERATION', 'TOKEN', 'GPU_TIME')",
            "severity": "warning",
            "description": "Usage type should be valid billing category"
        },
    ]

def populate_dq_rules(spark: SparkSession, catalog: str, schema: str, rules: list):
    """Populate the dq_rules table with all rules."""
    
    table_name = f"{catalog}.{schema}.dq_rules"
    
    print(f"\nPopulating {table_name} with {len(rules)} rules...")
    
    # Add metadata columns
    now = current_timestamp()
    for rule in rules:
        rule['rule_id'] = md5(concat_ws("||", 
            col("table_name").cast("string"), 
            col("rule_name").cast("string")
        )).cast("string")
        rule['created_at'] = now
        rule['updated_at'] = now
        rule['enabled'] = True
    
    # Create DataFrame with explicit schema
    schema_def = StructType([
        StructField("table_name", StringType(), False),
        StructField("rule_name", StringType(), False),
        StructField("rule_constraint", StringType(), False),
        StructField("severity", StringType(), False),
        StructField("enabled", BooleanType(), False),
        StructField("description", StringType(), True),
    ])
    
    try:
        rules_df = spark.createDataFrame(rules, schema=schema_def)
        
        # Add MD5 hash for rule_id
        rules_df = rules_df.withColumn(
            "rule_id",
            md5(concat_ws("||", col("table_name"), col("rule_name")))
        ).withColumn(
            "created_at",
            current_timestamp()
        ).withColumn(
            "updated_at",
            current_timestamp()
        )
        
        # Write to Delta table
        rules_df.write.format("delta").mode("append").saveAsTable(table_name)
        
        print(f"✓ Populated {len(rules)} rules into {table_name}")
        
        # Show summary
        print("\n" + "=" * 80)
        print("DQ RULES SUMMARY (GROUNDED IN ACTUAL SCHEMAS)")
        print("=" * 80)
        spark.sql(f"""
            SELECT 
                table_name,
                COUNT(*) as rule_count,
                SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_rules,
                SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) as warning_rules
            FROM {table_name}
            WHERE enabled = true
            GROUP BY table_name
            ORDER BY table_name
        """).show(100, False)
        
    except Exception as e:
        print(f"❌ Error populating rules: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Main entry point for DQ rules setup."""
    
    catalog, bronze_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Bronze DQ Rules Setup (Grounded)").getOrCreate()
    
    try:
        print("\n" + "=" * 80)
        print("BRONZE DQ RULES SETUP - GROUNDED IN ACTUAL SCHEMAS")
        print("=" * 80)
        print(f"Catalog: {catalog}")
        print(f"Schema: {bronze_schema}")
        print("=" * 80)
        
        # Create table
        create_dq_rules_table(spark, catalog, bronze_schema)
        
        # Get all rules (grounded in actual schemas!)
        all_rules = get_all_dq_rules()
        print(f"\n✓ Defined {len(all_rules)} intelligent, fact-based DQ rules")
        
        # Populate table
        populate_dq_rules(spark, catalog, bronze_schema, all_rules)
        
        print("\n" + "=" * 80)
        print("✓ DQ RULES SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nRules are:")
        print("  ✓ Grounded in actual system table schemas (CSV + docs)")
        print("  ✓ Intelligent (enum validation, conditional logic, temporal checks)")
        print("  ✓ Business-relevant (not just generic null checks)")
        print("\nNext: Apply to Bronze streaming tables via dq_rules_loader module")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error in DQ rules setup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main()



