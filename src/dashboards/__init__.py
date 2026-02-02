"""
TRAINING MATERIAL: AI/BI Lakeview Dashboard Deployment
======================================================

This module manages Lakeview dashboard deployment using a standardized
pattern with UPDATE-or-CREATE semantics and variable substitution.

DEPLOYMENT ARCHITECTURE:
------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  SOURCE FILES                                                            │
│  ────────────                                                            │
│  src/dashboards/cost.lvdash.json       (version controlled)             │
│  src/dashboards/reliability.lvdash.json                                  │
│  ...                                                                     │
│                                                                         │
│       │ Variable Substitution                                           │
│       │ ${catalog} → prashanth_catalog                                  │
│       │ ${gold_schema} → gold                                           │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  deploy_dashboards.py                                            │   │
│  │  - Reads JSON files                                              │   │
│  │  - Substitutes variables                                         │   │
│  │  - Calls Workspace Import API with overwrite=True                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                  │
│       ▼                                                                  │
│  DATABRICKS WORKSPACE                                                    │
│  /Users/{email}/Dashboards/cost.lvdash                                  │
│  (Same URL preserved on updates)                                         │
└─────────────────────────────────────────────────────────────────────────┘

UPDATE-or-CREATE PATTERN:
-------------------------

Using Workspace Import API with overwrite=True:
- Creates if doesn't exist
- Updates if exists
- Preserves dashboard URL
- Preserves sharing permissions
- Single code path (no if/else)

VALIDATION STRATEGY:
--------------------

validate_dashboard_queries.py executes queries with LIMIT 1:
- Catches column resolution errors
- Catches ambiguous reference errors
- Catches type mismatch errors
- 90% faster than running full dashboards

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
