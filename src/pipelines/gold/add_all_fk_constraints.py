# Databricks notebook source
"""
TRAINING MATERIAL: Foreign Key Constraint Management Pattern
=============================================================

This script adds ALL foreign key constraints across Gold layer tables.
It runs AFTER table creation to avoid circular dependency issues.

WHY SEPARATE FK CONSTRAINT SCRIPT:
----------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  THE PROBLEM: Constraint Timing Dependencies                             │
│                                                                         │
│  If you define FK constraints inline with CREATE TABLE:                 │
│                                                                         │
│  CREATE TABLE fact_usage (...                                           │
│    FOREIGN KEY (workspace_id) REFERENCES dim_workspace(workspace_id)    │
│  );                                                                     │
│                                                                         │
│  This FAILS if dim_workspace doesn't exist yet!                         │
│                                                                         │
│  Even worse: dim_workspace might need FK to fact_usage (circular)       │
│                                                                         │
│  THE SOLUTION: Two-Phase Deployment                                     │
│  ────────────────────────────────────────────────────────────────────── │
│  Phase 1: Create ALL tables with PK constraints                         │
│  Phase 2: Add ALL FK constraints (this script)                          │
└─────────────────────────────────────────────────────────────────────────┘

FK CONSTRAINT PATTERNS:
-----------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  1. WORKSPACE FK (Most Common)                                           │
│     fact_usage.workspace_id → dim_workspace.workspace_id                │
│     Almost every table has this FK                                      │
│                                                                         │
│  2. COMPOSITE FK (Lakeflow, MLflow)                                      │
│     fact_job_run.(workspace_id, job_id) → dim_job.(workspace_id, job_id)│
│     Why composite: job_id alone is not unique across workspaces         │
│                                                                         │
│  3. SKU FK (Billing)                                                     │
│     fact_usage.sku_name → dim_sku.sku_name                              │
│     Simple string match on SKU name                                     │
└─────────────────────────────────────────────────────────────────────────┘

NOT ENFORCED CLAUSE:
--------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  FOREIGN KEY (...) REFERENCES ... NOT ENFORCED                           │
│                                                                         │
│  Why "NOT ENFORCED"?                                                    │
│  - Unity Catalog FKs are for documentation and query optimization       │
│  - Actual enforcement would slow down writes                            │
│  - Data comes from Databricks system tables (already consistent)        │
│                                                                         │
│  Benefits even without enforcement:                                     │
│  - Query optimizer can use FK for join optimization                     │
│  - Documentation in DESCRIBE TABLE output                               │
│  - Lineage tracking in Unity Catalog                                    │
│  - BI tools can infer relationships                                     │
└─────────────────────────────────────────────────────────────────────────┘

IDEMPOTENCY PATTERN:
--------------------

The add_fk_constraint() function handles all edge cases:
- Table doesn't exist → skip
- Column doesn't exist → skip
- FK already exists → skip (no error)
- PK missing on reference table → skip
- Any other error → log and continue

This makes the script safe to run multiple times.

Prerequisites: All Gold layer tables and PKs must be created first.

GOLD LAYER TABLE TAXONOMY:
==========================
- dim_*   → Dimension tables (direct 1:1 from Bronze, entities)
- fact_*  → Fact tables (direct 1:1 from Bronze, events/transactions)

All tables are direct mappings from Bronze system tables with nested columns exploded.
No aggregate or derived tables in current implementation.

FK Constraint Categories:
1. workspace_id -> dim_workspace (most tables)
2. job_id -> dim_job (lakeflow tables)
3. pipeline_id -> dim_pipeline (pipeline tables)
4. cluster_id -> dim_cluster (compute tables)
5. warehouse_id -> dim_warehouse (query tables)
6. experiment_id -> dim_experiment (mlflow tables)
7. sku_name -> dim_sku (billing tables)
"""

from pyspark.sql import SparkSession


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print()
    
    return catalog, gold_schema


def table_exists(spark, catalog, schema, table):
    """Check if a table exists."""
    try:
        spark.sql(f"DESCRIBE TABLE {catalog}.{schema}.{table}")
        return True
    except:
        return False


def column_exists(spark, catalog, schema, table, column):
    """Check if a column exists in a table."""
    try:
        df = spark.sql(f"DESCRIBE TABLE {catalog}.{schema}.{table}")
        cols = [row.col_name for row in df.collect()]
        return column in cols
    except:
        return False


def add_fk_constraint(spark, catalog, schema, table, constraint_name, fk_cols, ref_table, ref_cols):
    """Add FK constraint with validation."""
    try:
        # Check if source table exists
        if not table_exists(spark, catalog, schema, table):
            return "skip", f"Source table {table} not found"
        
        # Check if target table exists
        if not table_exists(spark, catalog, schema, ref_table):
            return "skip", f"Reference table {ref_table} not found"
        
        # Check if source columns exist
        for col in fk_cols:
            if not column_exists(spark, catalog, schema, table, col):
                return "skip", f"Column {col} not in {table}"
        
        # Check if target columns exist
        for col in ref_cols:
            if not column_exists(spark, catalog, schema, ref_table, col):
                return "skip", f"Column {col} not in {ref_table}"
        
        # Build and execute constraint
        fk_col_str = ", ".join(fk_cols)
        ref_col_str = ", ".join(ref_cols)
        
        sql = f"""
        ALTER TABLE {catalog}.{schema}.{table}
        ADD CONSTRAINT {constraint_name}
        FOREIGN KEY ({fk_col_str})
        REFERENCES {catalog}.{schema}.{ref_table}({ref_col_str})
        NOT ENFORCED
        """
        
        spark.sql(sql)
        return "success", f"{table}({fk_col_str}) -> {ref_table}({ref_col_str})"
        
    except Exception as e:
        error_str = str(e).lower()
        if "already exists" in error_str:
            return "exists", "Already exists"
        elif "does not have a primary key" in error_str:
            return "skip", f"No PK on {ref_table}"
        else:
            return "error", str(e)[:100]


def main():
    """Add all FK constraints across Gold layer."""
    
    catalog, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Health Monitor Gold FK Constraints").getOrCreate()
    
    print("=" * 80)
    print("HEALTH MONITOR - ADDING ALL FK CONSTRAINTS")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Schema: {gold_schema}")
    print("=" * 80)
    print()
    
    # =========================================================================
    # COMPREHENSIVE FK CONSTRAINTS - Only tables with YAMLs in Gold layer
    # Format: (source_table, constraint_name, fk_cols, ref_table, ref_cols)
    # =========================================================================
    
    fk_constraints = [
        # =====================================================================
        # 1. COMPUTE DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("dim_cluster", "fk_dim_cluster_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("dim_node_type", "fk_dim_node_type_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("dim_warehouse", "fk_dim_warehouse_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_node_timeline", "fk_fact_node_timeline_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_warehouse_events", "fk_fact_warehouse_events_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 2. LAKEFLOW DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("dim_job", "fk_dim_job_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("dim_job_task", "fk_dim_job_task_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("dim_pipeline", "fk_dim_pipeline_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_job_run_timeline", "fk_fact_job_run_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_job_task_run_timeline", "fk_fact_job_task_run_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_pipeline_update_timeline", "fk_fact_pipeline_update_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 3. GOVERNANCE DOMAIN - workspace_id -> dim_workspace
        # (Note: dim_table_metadata and dim_column_metadata removed - sourced from information_schema, not Bronze)
        # =====================================================================
        ("fact_column_lineage", "fk_fact_column_lineage_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_table_lineage", "fk_fact_table_lineage_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 4. SECURITY DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("fact_audit_logs", "fk_fact_audit_logs_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_clean_room_events", "fk_fact_clean_room_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_inbound_network", "fk_fact_inbound_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_outbound_network", "fk_fact_outbound_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 5. QUERY PERFORMANCE DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("fact_query_history", "fk_fact_query_history_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 6. MLFLOW DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("dim_experiment", "fk_dim_experiment_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_mlflow_run", "fk_fact_mlflow_run_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_mlflow_run_metrics", "fk_fact_mlflow_metrics_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 7. MODEL SERVING DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("dim_served_entity", "fk_dim_served_entity_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_endpoint_usage", "fk_fact_endpoint_usage_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_payload_logs", "fk_fact_payload_logs_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 8. BILLING DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("fact_usage", "fk_fact_usage_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        # Note: fact_cloud_infra_cost removed - billing.cloud_infra_cost doesn't exist in account
        
        # =====================================================================
        # 9. STORAGE DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("fact_predictive_optimization", "fk_fact_pred_opt_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 10. DATA CLASSIFICATION DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("fact_data_classification", "fk_fact_data_class_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 11. DATA QUALITY MONITORING DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("fact_dq_monitoring", "fk_fact_dq_mon_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 12. AI/BI DOMAIN - workspace_id -> dim_workspace
        # =====================================================================
        ("fact_assistant_events", "fk_fact_assistant_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 13. MARKETPLACE DOMAIN - workspace_id -> dim_workspace (if applicable)
        # =====================================================================
        ("fact_listing_access", "fk_fact_listing_access_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        ("fact_listing_funnel", "fk_fact_listing_funnel_workspace", ["workspace_id"], "dim_workspace", ["workspace_id"]),
        
        # =====================================================================
        # 14. LAKEFLOW DOMAIN - job_id -> dim_job (composite keys)
        # =====================================================================
        ("dim_job_task", "fk_dim_job_task_job", ["workspace_id", "job_id"], "dim_job", ["workspace_id", "job_id"]),
        ("fact_job_run_timeline", "fk_fact_job_run_job", ["workspace_id", "job_id"], "dim_job", ["workspace_id", "job_id"]),
        ("fact_job_task_run_timeline", "fk_fact_job_task_run_job", ["workspace_id", "job_id"], "dim_job", ["workspace_id", "job_id"]),
        
        # =====================================================================
        # 15. LAKEFLOW DOMAIN - pipeline_id -> dim_pipeline (composite keys)
        # =====================================================================
        ("fact_pipeline_update_timeline", "fk_fact_pipeline_update_pipeline", ["workspace_id", "pipeline_id"], "dim_pipeline", ["workspace_id", "pipeline_id"]),
        
        # =====================================================================
        # 16. COMPUTE DOMAIN - cluster_id -> dim_cluster (composite keys)
        # =====================================================================
        ("fact_node_timeline", "fk_fact_node_timeline_cluster", ["workspace_id", "cluster_id"], "dim_cluster", ["workspace_id", "cluster_id"]),
        
        # =====================================================================
        # 17. QUERY DOMAIN - warehouse_id -> dim_warehouse (composite keys)
        # =====================================================================
        ("fact_warehouse_events", "fk_fact_warehouse_events_wh", ["workspace_id", "warehouse_id"], "dim_warehouse", ["workspace_id", "warehouse_id"]),
        
        # =====================================================================
        # 18. MLFLOW DOMAIN - experiment_id -> dim_experiment (composite keys)
        # =====================================================================
        ("fact_mlflow_run", "fk_fact_mlflow_run_experiment", ["workspace_id", "experiment_id"], "dim_experiment", ["workspace_id", "experiment_id"]),
        ("fact_mlflow_run_metrics", "fk_fact_mlflow_metrics_experiment", ["workspace_id", "experiment_id"], "dim_experiment", ["workspace_id", "experiment_id"]),
        
        # =====================================================================
        # 19. BILLING DOMAIN - sku_name -> dim_sku
        # =====================================================================
        ("fact_usage", "fk_fact_usage_sku", ["sku_name"], "dim_sku", ["sku_name"]),
        ("fact_list_prices", "fk_fact_list_prices_sku", ["sku_name"], "dim_sku", ["sku_name"]),
        ("fact_account_prices", "fk_fact_account_prices_sku", ["sku_name"], "dim_sku", ["sku_name"]),
        
        # =====================================================================
        # 20. SHARING DOMAIN - REMOVED
        # =====================================================================
        # Note: dim_recipient and dim_share were removed from Gold design
        # as they sourced from information_schema, not Bronze system tables.
        # Query information_schema.recipients and information_schema.shares directly.
    ]
    
    # =========================================================================
    # EXECUTE ALL CONSTRAINTS
    # =========================================================================
    
    success_count = 0
    exists_count = 0
    skip_count = 0
    error_count = 0
    
    print("📝 Adding FK constraints...")
    print()
    
    for table, constraint_name, fk_cols, ref_table, ref_cols in fk_constraints:
        status, message = add_fk_constraint(
            spark, catalog, gold_schema, 
            table, constraint_name, fk_cols, ref_table, ref_cols
        )
        
        if status == "success":
            print(f"   ✓ {constraint_name}: {message}")
            success_count += 1
        elif status == "exists":
            print(f"   ⊘ {constraint_name}: {message}")
            exists_count += 1
        elif status == "skip":
            print(f"   ⚠ {constraint_name}: SKIPPED - {message}")
            skip_count += 1
        else:
            print(f"   ❌ {constraint_name}: ERROR - {message}")
            error_count += 1
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    print()
    print("=" * 80)
    print("✅ HEALTH MONITOR - FK CONSTRAINTS COMPLETE")
    print("=" * 80)
    print(f"Total FK constraints defined: {len(fk_constraints)}")
    print(f"Successfully added: {success_count}")
    print(f"Already existed: {exists_count}")
    print(f"Skipped (missing tables/columns/PKs): {skip_count}")
    print(f"Errors: {error_count}")
    print()
    
    if error_count > 0:
        print("⚠️  Some FK constraints failed. Review errors above.")
    
    spark.stop()


if __name__ == "__main__":
    main()
