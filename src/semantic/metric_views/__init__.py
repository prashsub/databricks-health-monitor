"""
TRAINING MATERIAL: Metric Views Semantic Layer
==============================================

This module contains Metric View definitions for the semantic layer,
enabling natural language queries via Genie and AI/BI dashboards.

METRIC VIEWS vs REGULAR VIEWS:
------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  REGULAR VIEW                     │  METRIC VIEW ✅                     │
├───────────────────────────────────┼─────────────────────────────────────┤
│  SQL SELECT definition            │  YAML semantic definition           │
│  No metadata for dimensions       │  Dimensions with synonyms           │
│  No measure aggregations          │  Measures with formats              │
│  BI tool interprets schema        │  Genie understands semantics        │
│  Hardcoded joins                  │  Declarative relationships          │
└───────────────────────────────────┴─────────────────────────────────────┘

METRIC VIEW STRUCTURE:
----------------------

    version: "1.1"
    comment: "Cost analytics for FinOps"
    source: ${catalog}.${gold_schema}.fact_usage
    
    dimensions:
      - name: workspace_name
        expr: dim_workspace.workspace_name
        synonyms: ["workspace", "ws"]
    
    measures:
      - name: total_cost
        expr: SUM(source.list_cost)
        format:
          type: currency
          currency_code: USD
        synonyms: ["cost", "spend", "bill"]

WHY METRIC VIEWS FOR GENIE:
---------------------------

1. NATURAL LANGUAGE
   User: "What's our serverless cost by workspace?"
   Genie knows "cost" = total_cost measure, "workspace" = workspace_name dimension

2. CONSISTENT AGGREGATIONS
   Measures define how to aggregate (SUM, AVG, COUNT)
   No ambiguity in "total cost" vs "average cost"

3. LLM-FRIENDLY METADATA
   Synonyms help LLM match user vocabulary to schema
   Comments explain business meaning

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
