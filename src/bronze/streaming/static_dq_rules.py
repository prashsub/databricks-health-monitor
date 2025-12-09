"""
Static Data Quality Rules for Bronze Streaming Tables
======================================================

Pure static rules that don't require database queries.
Based on official Databricks pattern:
https://docs.databricks.com/aws/en/ldp/expectation-patterns

This module is importable after restartPython() because it has NO
'# Databricks notebook source' header.
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

