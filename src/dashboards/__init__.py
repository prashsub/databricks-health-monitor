"""
AI/BI Lakeview Dashboards for Databricks Health Monitor
========================================================

Dashboards for executive, cost, reliability, and performance analysis.

Available dashboards:
- Executive Overview: High-level health metrics for leadership
- Cost Management: Detailed cost analysis and optimization
- Job Reliability: Job execution health and failures
- Query Performance: SQL query latency and efficiency
- Cluster Utilization: Resource usage and right-sizing
- Security Audit: Access patterns and compliance

Usage:
    Deploy dashboards using: resources/dashboards/dashboard_deployment_job.yml
    Or run: src/dashboards/deploy_dashboards.py

Reference:
    https://docs.databricks.com/visualizations/lakeview
"""

# Dashboard configurations
DASHBOARDS = [
    ("executive_overview", "Executive Health Overview"),
    ("cost_management", "Cost Management"),
    ("job_reliability", "Job Reliability"),
    ("query_performance", "Query Performance"),
    ("cluster_utilization", "Cluster Utilization"),
    ("security_audit", "Security & Audit"),
]
