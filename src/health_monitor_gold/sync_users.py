# Databricks notebook source
"""
User Sync Job - Populates dim_user table
========================================

This job syncs user information from the Databricks SCIM API to a dim_user 
dimension table, enabling dashboards to display email addresses instead of 
numeric user IDs.

The dim_user table maps:
- user_id (numeric) -> email, display_name

Usage:
  Run this job periodically (daily recommended) to keep user info current.

Parameters:
- catalog: Target Unity Catalog
- gold_schema: Gold layer schema name
"""

# COMMAND ----------

dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")

print(f"Syncing users to: {catalog}.{gold_schema}.dim_user")

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import current_timestamp, lit
from datetime import datetime

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

def create_dim_user_table(catalog: str, schema: str):
    """Create the dim_user table if it doesn't exist."""
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{schema}.dim_user (
        user_id STRING NOT NULL COMMENT 'Databricks user ID (numeric string)',
        email STRING COMMENT 'User email address (primary identifier)',
        display_name STRING COMMENT 'User display name',
        active BOOLEAN COMMENT 'Whether the user is active',
        created_at TIMESTAMP COMMENT 'When user was created in Databricks',
        synced_at TIMESTAMP NOT NULL COMMENT 'When this record was last synced',
        
        CONSTRAINT pk_dim_user PRIMARY KEY (user_id) NOT ENFORCED
    )
    USING DELTA
    CLUSTER BY AUTO
    COMMENT 'Dimension table mapping Databricks user IDs to emails and names. Synced from SCIM API.'
    TBLPROPERTIES (
        'delta.enableChangeDataFeed' = 'true',
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true',
        'layer' = 'gold',
        'domain' = 'identity',
        'entity_type' = 'dimension',
        'contains_pii' = 'true',
        'data_classification' = 'internal'
    )
    """
    
    spark.sql(create_sql)
    print(f"✓ Table {catalog}.{schema}.dim_user ready")

# COMMAND ----------

def sync_users_from_scim(catalog: str, schema: str):
    """
    Sync all users from Databricks SCIM API to dim_user table.
    
    Uses MERGE to upsert - updates existing users and inserts new ones.
    """
    
    print("Fetching users from Databricks SCIM API...")
    
    w = WorkspaceClient()
    
    # Collect all users
    users_data = []
    
    try:
        # List all users - handles pagination automatically
        for user in w.users.list():
            user_record = {
                "user_id": user.id,
                "email": user.user_name,  # In Databricks, user_name is typically the email
                "display_name": user.display_name or user.user_name,
                "active": user.active if user.active is not None else True,
                "created_at": None  # SCIM API doesn't always provide this
            }
            users_data.append(user_record)
            
    except Exception as e:
        print(f"⚠️ Error fetching users: {e}")
        # Try alternative approach - list from identity API
        try:
            for user in w.users.list(attributes="id,userName,displayName,active"):
                user_record = {
                    "user_id": user.id,
                    "email": user.user_name,
                    "display_name": user.display_name or user.user_name,
                    "active": user.active if user.active is not None else True,
                    "created_at": None
                }
                users_data.append(user_record)
        except Exception as e2:
            print(f"❌ Failed to fetch users: {e2}")
            raise
    
    print(f"  Found {len(users_data)} users")
    
    if not users_data:
        print("⚠️ No users found - skipping sync")
        return 0
    
    # Create DataFrame with explicit schema to avoid type inference issues
    user_schema = StructType([
        StructField("user_id", StringType(), False),
        StructField("email", StringType(), True),
        StructField("display_name", StringType(), True),
        StructField("active", StringType(), True),  # Will convert to boolean
        StructField("created_at", StringType(), True)  # String to avoid None type issues
    ])
    
    # Convert dict to tuples for schema compatibility
    users_rows = [
        (u["user_id"], u["email"], u["display_name"], str(u["active"]) if u["active"] is not None else "true", None)
        for u in users_data
    ]
    
    users_df = spark.createDataFrame(users_rows, schema=user_schema)
    
    # Add sync timestamp and cast types
    users_df = users_df.withColumn("synced_at", current_timestamp()) \
                       .withColumn("active", users_df.active.cast("boolean"))
    
    # Create temp view for MERGE
    users_df.createOrReplaceTempView("users_staging")
    
    # MERGE into dim_user
    target_table = f"{catalog}.{gold_schema}.dim_user"
    
    merge_sql = f"""
    MERGE INTO {target_table} AS target
    USING users_staging AS source
    ON target.user_id = source.user_id
    WHEN MATCHED THEN
        UPDATE SET
            email = source.email,
            display_name = source.display_name,
            active = source.active,
            synced_at = source.synced_at
    WHEN NOT MATCHED THEN
        INSERT (user_id, email, display_name, active, created_at, synced_at)
        VALUES (source.user_id, source.email, source.display_name, source.active, source.created_at, source.synced_at)
    """
    
    spark.sql(merge_sql)
    
    # Get final count
    count = spark.sql(f"SELECT COUNT(*) FROM {target_table}").collect()[0][0]
    print(f"✓ Synced {len(users_data)} users to {target_table} (total: {count})")
    
    return len(users_data)

# COMMAND ----------

def sync_service_principals(catalog: str, schema: str):
    """
    Sync service principals to dim_user table.
    
    Service principals are also valid owners of jobs/resources.
    """
    
    print("Fetching service principals...")
    
    w = WorkspaceClient()
    sp_rows = []  # Build rows directly as tuples of primitives
    skipped_count = 0
    
    try:
        for sp in w.service_principals.list():
            # Skip service principals without an ID (shouldn't happen but be defensive)
            if not sp.id:
                skipped_count += 1
                continue
            
            # CRITICAL: Convert ALL values to Python primitives immediately
            # to avoid CANNOT_DETERMINE_TYPE errors
            sp_id = str(sp.id) if sp.id is not None else None
            
            # Get application_id safely - it might be a complex object
            app_id = None
            if hasattr(sp, 'application_id') and sp.application_id is not None:
                app_id = str(sp.application_id)
            
            # Get display_name safely
            disp_name = None
            if hasattr(sp, 'display_name') and sp.display_name is not None:
                disp_name = str(sp.display_name)
            
            # Get active status safely - convert to string "true"/"false"
            active_val = "true"  # Default
            if hasattr(sp, 'active') and sp.active is not None:
                active_val = "true" if sp.active else "false"
            
            # Skip if no ID
            if not sp_id:
                skipped_count += 1
                continue
            
            # Build identifier - prefer application_id, fall back to display_name, then ID
            identifier = app_id or disp_name or f"sp-{sp_id}"
            
            # Build display name with [SP] prefix
            if disp_name:
                display_name = f"[SP] {disp_name}"
            elif app_id:
                display_name = f"[SP] {app_id}"
            else:
                display_name = f"[SP] Service Principal {sp_id}"
            
            # Append tuple of primitives only (str or None)
            sp_rows.append((
                sp_id,           # user_id: str
                identifier,      # email: str
                display_name,    # display_name: str
                active_val,      # active: str ("true"/"false")
                None             # created_at: None (will be cast to string)
            ))
            
    except Exception as e:
        print(f"⚠️ Could not fetch service principals: {e}")
        return 0
    
    print(f"  Found {len(sp_rows)} service principals" + (f" (skipped {skipped_count} without ID)" if skipped_count else ""))
    
    if not sp_rows:
        print("⚠️ No valid service principals to sync")
        return 0
    
    # Create DataFrame with explicit schema to avoid type inference issues
    sp_schema = StructType([
        StructField("user_id", StringType(), False),
        StructField("email", StringType(), True),
        StructField("display_name", StringType(), True),
        StructField("active", StringType(), True),  # Will convert to boolean
        StructField("created_at", StringType(), True)  # String to avoid None type issues
    ])
    
    # Create DataFrame - data is already clean tuples of primitives
    sp_df = spark.createDataFrame(sp_rows, schema=sp_schema)
    
    # Add sync timestamp and cast types
    sp_df = sp_df.withColumn("synced_at", current_timestamp()) \
                 .withColumn("active", sp_df.active.cast("boolean"))
    
    sp_df.createOrReplaceTempView("sp_staging")
    
    target_table = f"{catalog}.{gold_schema}.dim_user"
    
    merge_sql = f"""
    MERGE INTO {target_table} AS target
    USING sp_staging AS source
    ON target.user_id = source.user_id
    WHEN MATCHED THEN
        UPDATE SET
            email = source.email,
            display_name = source.display_name,
            active = source.active,
            synced_at = source.synced_at
    WHEN NOT MATCHED THEN
        INSERT (user_id, email, display_name, active, created_at, synced_at)
        VALUES (source.user_id, source.email, source.display_name, source.active, source.created_at, source.synced_at)
    """
    
    spark.sql(merge_sql)
    print(f"✓ Synced {len(sp_rows)} service principals")
    
    return len(sp_rows)

# COMMAND ----------

# Main execution
print("=" * 60)
print("USER SYNC JOB")
print("=" * 60)

# Create table if not exists
create_dim_user_table(catalog, gold_schema)

# Sync users
user_count = sync_users_from_scim(catalog, gold_schema)

# Sync service principals
sp_count = sync_service_principals(catalog, gold_schema)

# Summary
print("\n" + "=" * 60)
print("SYNC COMPLETE")
print("=" * 60)
print(f"  Users synced: {user_count}")
print(f"  Service principals synced: {sp_count}")
print(f"  Total identities: {user_count + sp_count}")

# Verify
final_count = spark.sql(f"SELECT COUNT(*) FROM {catalog}.{gold_schema}.dim_user").collect()[0][0]
print(f"  dim_user total records: {final_count}")

dbutils.notebook.exit(f"SUCCESS: Synced {user_count + sp_count} identities to dim_user")

