# Alerting Framework for Databricks Health Monitor
# ================================================
#
# This package provides a config-driven SQL alerting framework.
#
# Core Modules:
#   - alerting_config: Pure Python configuration helpers (testable locally)
#   - setup_alerting_tables: Creates Gold alerting tables
#   - sync_sql_alerts: Syncs alert configurations to Databricks SQL Alerts v2
#
# Phase 2 Enhancements:
#   - query_validator: Validates SQL queries before deployment
#   - alert_templates: Pre-built alert template library
#   - alerting_metrics: Sync metrics collection and logging
#   - validate_all_queries: Pre-deployment validation notebook
#   - sync_notification_destinations: Auto-create notification destinations

__all__ = [
    # Core modules
    "alerting_config",
    "setup_alerting_tables",
    "sync_sql_alerts",
    # Phase 2 enhancements
    "query_validator",
    "alert_templates",
    "alerting_metrics",
    "validate_all_queries",
    "sync_notification_destinations",
]
