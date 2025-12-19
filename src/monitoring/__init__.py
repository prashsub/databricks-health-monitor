"""
Lakehouse Monitoring for Databricks Health Monitor
===================================================

Monitors for tracking data quality, business KPIs, and ML model performance.

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
