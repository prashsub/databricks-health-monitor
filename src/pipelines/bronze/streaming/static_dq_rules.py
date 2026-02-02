"""
TRAINING MATERIAL: Static DQ Rules for Fast Pipeline Startup
============================================================

This module provides hardcoded DQ rules as a FALLBACK when the
dq_rules Delta table is unavailable.

STATIC vs DYNAMIC RULES:
------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  APPROACH          │  LOAD TIME    │  CONFIGURABILITY │  USE CASE       │
├────────────────────┼───────────────┼──────────────────┼─────────────────┤
│  Static (this)     │  Instant      │  Code changes    │  Fallback       │
│  Dynamic (Delta)   │  ~1 second    │  SQL UPDATE      │  Production     │
└────────────────────┴───────────────┴──────────────────┴─────────────────┘

WHY STATIC RULES:
-----------------

1. DLT pipelines may run before Delta table exists
2. Provides baseline rules without database dependency
3. Faster pipeline startup (no query overhead)
4. Unit testable without Spark

PURE PYTHON MODULE REQUIREMENT:
-------------------------------

This file has NO '# Databricks notebook source' header because:
- Notebooks can't be imported after restartPython()
- DLT pipelines need to import this module
- Pure Python (.py) files are always importable

RULE FORMAT:
------------

    {
        "table_name": {
            "rule_name": "SQL constraint expression",
        }
    }

Usage in DLT:
    
    from static_dq_rules import get_all_rules_for_table
    
    @dlt.expect_all(get_all_rules_for_table("audit"))
    def audit():
        ...

Based on official Databricks pattern:
https://docs.databricks.com/aws/en/ldp/expectation-patterns
"""

# COMMAND ----------

def get_all_rules_for_table(table_name):
    """
    Get ALL DQ rules for a specific Bronze table.
    
    Args:
        table_name: Name of the Bronze table (e.g., "audit")
    
    Returns:
        dict: Dictionary of rule_name: constraint
    """
    # Static rules for each table
    rules_by_table = {
        "audit": {
            "valid_workspace_id": "workspace_id IS NOT NULL",
            "valid_timestamp": "timestamp IS NOT NULL",
            "valid_service_name": "service_name IS NOT NULL AND LENGTH(service_name) > 0",
            "valid_action_name": "action_name IS NOT NULL AND LENGTH(action_name) > 0"
        },
        "clusters": {
            "valid_cluster_id": "cluster_id IS NOT NULL AND LENGTH(cluster_id) > 0",
            "valid_account_id": "account_id IS NOT NULL",
            "valid_cluster_name": "cluster_name IS NOT NULL"
        },
        "jobs": {
            "valid_job_id": "job_id IS NOT NULL",
            "valid_account_id": "account_id IS NOT NULL",
            "valid_created_time": "created_time IS NOT NULL"
        },
        "node_timeline": {
            "valid_cluster_id": "cluster_id IS NOT NULL",
            "valid_timestamp": "timestamp IS NOT NULL"
        },
        "usage": {
            "valid_workspace_id": "workspace_id IS NOT NULL",
            "valid_sku_name": "sku_name IS NOT NULL",
            "valid_usage_date": "usage_date IS NOT NULL"
        }
    }
    
    return rules_by_table.get(table_name, {})

