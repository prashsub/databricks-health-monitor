# Alerting Framework for Databricks Health Monitor
# ================================================
#
# TRAINING MATERIAL: Config-Driven SQL Alerting Architecture
# ==========================================================
#
# This package implements a production alerting framework where alert
# configurations are stored in Delta tables, not hardcoded.
#
# CONFIG-DRIVEN PATTERN:
# ----------------------
#
#     ┌─────────────────────────────────────────────────────────────────────────┐
#     │  alert_configurations (Delta Table)                                      │
#     │  ─────────────────────────────────                                       │
#     │  alert_id, display_name, query_text, threshold, schedule, ...           │
#     │                                                                          │
#     │       │ INSERT/UPDATE via SQL or Frontend App                           │
#     │       ▼                                                                  │
#     │  ┌─────────────────────────────────────────────────────────────────┐    │
#     │  │  sync_sql_alerts.py                                              │    │
#     │  │  Reads Delta table → Syncs to Databricks SQL Alerts V2 API      │    │
#     │  └─────────────────────────────────────────────────────────────────┘    │
#     │       │                                                                  │
#     │       ▼                                                                  │
#     │  Databricks SQL Alert (managed by platform)                             │
#     │  - Scheduled evaluation                                                  │
#     │  - Email/Slack/Webhook notifications                                     │
#     └─────────────────────────────────────────────────────────────────────────┘
#
# WHY CONFIG-DRIVEN:
# ------------------
#
#     APPROACH          │ ADD NEW ALERT                  │ CHANGE THRESHOLD
#     ──────────────────┼────────────────────────────────┼─────────────────────
#     Hardcoded Python  │ Code change → PR → Deploy      │ Same
#     Config-Driven ✅   │ INSERT INTO alert_configs ...  │ UPDATE ... SET threshold
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
