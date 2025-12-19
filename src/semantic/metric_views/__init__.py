"""
Metric Views for Databricks Health Monitor
==========================================

Metric Views provide a semantic layer for natural language queries via Genie.
Each view is defined in YAML v1.1 format with dimensions, measures, and synonyms.

Available metric views:
- cost_analytics: Cost and DBU consumption metrics for FinOps analysis
- job_performance: Job reliability and duration metrics for ops teams
- query_performance: Query latency and efficiency metrics for SQL optimization
- cluster_utilization: Cluster CPU/memory metrics for capacity planning
- security_events: Security audit metrics for compliance monitoring
- commit_tracking: Budget and commitment tracking metrics for finance

Usage:
    Deploy metric views using: resources/semantic/metric_view_deployment_job.yml
    Or run: src/metric_views/deploy_metric_views.py

Reference:
    https://docs.databricks.com/sql/language-manual/sql-ref-syntax-ddl-create-metric-view.html
"""

# Metric view configurations
METRIC_VIEWS = [
    "cost_analytics",
    "job_performance",
    "query_performance",
    "cluster_utilization",
    "security_events",
    "commit_tracking",
]
