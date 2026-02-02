"""
TRAINING MATERIAL: Centralized DQ Rules Loader Pattern
======================================================

This module loads Data Quality rules from a Delta table at DLT pipeline runtime,
implementing the "Centralized Delta Table" pattern from official Databricks docs.

WHY CENTRALIZED DQ RULES:
-------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PATTERN              │  RULES LOCATION     │  CHANGE MANAGEMENT        │
├───────────────────────┼─────────────────────┼───────────────────────────┤
│  Hardcoded            │  Python source      │  Code deploy required     │
│  YAML file            │  Config file        │  File deploy required     │
│  Delta Table ✅        │  Delta table        │  SQL UPDATE, no deploy    │
└───────────────────────┴─────────────────────┴───────────────────────────┘

DQ RULES TABLE SCHEMA:
----------------------

    dq_rules (Delta table)
    ├── table_name STRING       -- Bronze table this rule applies to
    ├── rule_name STRING        -- Unique rule identifier
    ├── rule_constraint STRING  -- SQL expression (e.g., "column IS NOT NULL")
    ├── severity STRING         -- "CRITICAL" or "WARNING"
    ├── enabled BOOLEAN         -- Toggle rules on/off without delete
    └── created_at TIMESTAMP    -- Audit trail

DLT EXPECTATION PATTERNS:
-------------------------

    # CRITICAL: Drop records that violate these rules
    @dlt.expect_all_or_drop(get_critical_rules_for_table("audit"))
    
    # WARNING: Log violations but keep records
    @dlt.expect_all(get_warning_rules_for_table("audit"))

HOW IT WORKS:
-------------

1. DLT pipeline starts
2. This module queries dq_rules table for the target table
3. Rules are formatted as {"rule_name": "constraint"} dict
4. DLT applies rules via @dlt.expect_all_or_drop() and @dlt.expect_all()

PURE PYTHON REQUIREMENT:
------------------------

This file MUST be a pure Python file (.py), NOT a Databricks notebook.
Databricks notebooks (with "# Databricks notebook source" header) cannot be
imported with standard Python imports.

Usage in DLT notebooks:
    from dq_rules_loader import get_critical_rules_for_table, get_warning_rules_for_table
    
    @dlt.table(...)
    @dlt.expect_all_or_drop(get_critical_rules_for_table("audit"))
    @dlt.expect_all(get_warning_rules_for_table("audit"))
    def audit():
        ...
"""

from pyspark.sql import SparkSession

def _get_dq_rules_table_name():
    """Get fully qualified dq_rules table name from configuration."""
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog", "main")
    schema = spark.conf.get("bronze_schema", "system_bronze")
    
    # Debug logging
    print(f"[DQ_RULES_LOADER] catalog from spark.conf: {catalog}")
    print(f"[DQ_RULES_LOADER] bronze_schema from spark.conf: {schema}")
    print(f"[DQ_RULES_LOADER] Full table name: {catalog}.{schema}.dq_rules")
    
    return f"{catalog}.{schema}.dq_rules"

def _load_rules_for_table(table_name: str):
    """
    Load all enabled rules for a specific table from Delta configuration.
    
    Args:
        table_name: Name of the Bronze table
    
    Returns:
        list: List of rule dictionaries
    """
    spark = SparkSession.getActiveSession()
    rules_table = _get_dq_rules_table_name()
    
    print(f"[DQ_RULES_LOADER] Loading rules for table: {table_name}")
    
    try:
        # Query enabled rules for this table
        rules_df = spark.sql(f"""
            SELECT 
                rule_name,
                rule_constraint,
                severity
            FROM {rules_table}
            WHERE table_name = '{table_name}'
              AND enabled = true
            ORDER BY severity DESC, rule_name
        """)
        
        rules = rules_df.collect()
        print(f"[DQ_RULES_LOADER] Found {len(rules)} rules for '{table_name}'")
        
        if len(rules) == 0:
            print(f"[DQ_RULES_LOADER] ⚠️  WARNING: No rules found for '{table_name}'")
            print(f"[DQ_RULES_LOADER] ⚠️  Verify table name and check {rules_table} contents")
        
        return rules
        
    except Exception as e:
        print(f"[DQ_RULES_LOADER] ❌ ERROR loading rules for '{table_name}': {str(e)}")
        print(f"[DQ_RULES_LOADER] ❌ Rules table: {rules_table}")
        raise

def get_critical_rules_for_table(table_name: str) -> dict:
    """
    Get all enabled critical DQ rules for a specific table.
    
    Critical rules will FAIL the record if violated (expect_all_or_fail).
    
    Args:
        table_name: Name of the Bronze table (e.g., "audit", "usage")
    
    Returns:
        dict: Dictionary mapping rule names to SQL constraints
              Returns empty dict if rules cannot be loaded
    """
    try:
        rules = _load_rules_for_table(table_name)
        critical_rules = [r for r in rules if r.severity == "critical"]
        result = {r.rule_name: r.rule_constraint for r in critical_rules}
        
        if not result:
            print(f"[DQ_RULES_LOADER] ⚠️  No critical rules found for '{table_name}'")
        
        return result
    except Exception as e:
        print(f"[DQ_RULES_LOADER] ❌ ERROR in get_critical_rules_for_table('{table_name}'): {str(e)}")
        print(f"[DQ_RULES_LOADER] ⚠️  Returning empty dict - no DQ rules will be applied!")
        return {}

def get_warning_rules_for_table(table_name: str) -> dict:
    """
    Get all enabled warning DQ rules for a specific table.
    
    Warning rules will LOG but pass the record if violated (expect_all).
    
    Args:
        table_name: Name of the Bronze table (e.g., "audit", "usage")
    
    Returns:
        dict: Dictionary mapping rule names to SQL constraints
              Returns empty dict if rules cannot be loaded
    """
    try:
        rules = _load_rules_for_table(table_name)
        warning_rules = [r for r in rules if r.severity == "warning"]
        result = {r.rule_name: r.rule_constraint for r in warning_rules}
        
        if not result:
            print(f"[DQ_RULES_LOADER] ⚠️  No warning rules found for '{table_name}'")
        
        return result
    except Exception as e:
        print(f"[DQ_RULES_LOADER] ❌ ERROR in get_warning_rules_for_table('{table_name}'): {str(e)}")
        print(f"[DQ_RULES_LOADER] ⚠️  Returning empty dict - no DQ rules will be applied!")
        return {}

def get_all_rules_for_table(table_name: str) -> dict:
    """
    Get ALL enabled DQ rules for a specific table (both critical and warning).
    
    Use this with @dlt.expect_all_or_drop() for strict enforcement.
    
    Args:
        table_name: Name of the Bronze table
    
    Returns:
        dict: Dictionary mapping rule names to SQL constraints
              Returns empty dict if rules cannot be loaded
    """
    try:
        rules = _load_rules_for_table(table_name)
        result = {r.rule_name: r.rule_constraint for r in rules}
        
        if not result:
            print(f"[DQ_RULES_LOADER] ⚠️  No rules found for '{table_name}'")
        
        return result
    except Exception as e:
        print(f"[DQ_RULES_LOADER] ❌ ERROR in get_all_rules_for_table('{table_name}'): {str(e)}")
        print(f"[DQ_RULES_LOADER] ⚠️  Returning empty dict - no DQ rules will be applied!")
        return {}

