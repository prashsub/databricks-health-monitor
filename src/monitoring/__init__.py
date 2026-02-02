"""
TRAINING MATERIAL: Lakehouse Monitoring Architecture
====================================================

This module implements automated data quality tracking for Gold layer
tables using Databricks Lakehouse Monitoring.

LAKEHOUSE MONITORING COMPONENTS:
--------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  GOLD TABLE                                                              │
│  fact_usage                                                              │
│      │                                                                   │
│      ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  LAKEHOUSE MONITOR                                              │    │
│  │  - Profile metrics (null%, distinct, min/max)                   │    │
│  │  - Drift detection (distribution changes)                       │    │
│  │  - Custom metrics (business KPIs)                               │    │
│  └────────────────────────────────────────────────────────────────┘    │
│      │                                                                   │
│      ▼                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ _profile_metrics │  │ _drift_metrics  │  │ _analysis_view  │        │
│  │ (output table)   │  │ (output table)  │  │ (dashboard)     │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘

MONITOR TYPES:
--------------

| Type | Use Case | Output |
|---|---|---|
| Time Series | Fact tables with date column | Trend analysis |
| Snapshot | Dimension tables, full refresh | Point-in-time |
| Inference | ML prediction tables | Model monitoring |

CUSTOM METRICS:
---------------

Beyond built-in profile metrics, we add business KPIs:

    custom_metrics = [
        {
            "name": "tag_coverage",
            "type": "derived",
            "expr": "SUM(CASE WHEN tags IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*)"
        },
        {
            "name": "serverless_ratio",
            "type": "derived",
            "expr": "SUM(serverless_cost) / SUM(total_cost)"
        }
    ]

OUTPUT TABLE DOCUMENTATION:
---------------------------

Monitor output tables need documentation for Genie:
- _profile_metrics: Column statistics over time
- _drift_metrics: Distribution change scores

The document_monitors.py script adds table/column comments.

Available monitors:
- Cost Monitor: Track billing data quality and cost anomalies
- Security Monitor: Track data access patterns and compliance
- Query Monitor: Track query performance and efficiency
- Cluster Monitor: Track resource utilization
- Job Monitor: Track job reliability and failures
- Quality Monitor: Track data quality scores

Usage:
    Deploy monitors using: resources/monitoring/lakehouse_monitors.yml
    Or run: src/monitoring/setup_all_monitors.py

Reference:
    https://docs.databricks.com/lakehouse-monitoring
"""

# Monitor configurations
MONITORS = [
    ("fact_usage", "cost_monitor", "time_series"),
    ("fact_table_lineage", "security_monitor", "time_series"),
    ("fact_query_history", "query_monitor", "time_series"),
    ("fact_node_timeline", "cluster_monitor", "time_series"),
    ("fact_job_run_timeline", "job_monitor", "time_series"),
    ("fact_data_quality_monitoring_table_results", "quality_monitor", "time_series"),
]
