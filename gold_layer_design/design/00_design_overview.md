# Gold Layer Design Overview

## Architecture Summary

The Gold layer implements a **dimensional model** (star schema) for Databricks platform observability, transforming 35 Bronze system tables into 37 analytics-ready tables across 13 business domains.

## Table Distribution

| Category | Count | Description |
|----------|-------|-------------|
| **Dimensions** | 12 | Reference/lookup tables with descriptive attributes |
| **Facts** | 25 | Transactional/metric tables with measures |
| **Total** | 37 | |

## Domain Organization

### 1. Shared (1 table)
Central dimension shared across all domains.
- `dim_workspace` - Workspace metadata (referenced by most facts)

### 2. Compute (3 tables)
Cluster and compute resource management.
- `dim_cluster` - Cluster configurations
- `dim_node_type` - Available node types
- `fact_node_timeline` - Node utilization metrics

### 3. Lakeflow (6 tables)
Job and pipeline orchestration.
- `dim_job` - Job definitions
- `dim_job_task` - Task definitions within jobs
- `dim_pipeline` - DLT pipeline metadata
- `fact_job_run_timeline` - Job execution metrics
- `fact_job_task_run_timeline` - Task-level execution
- `fact_pipeline_update_timeline` - Pipeline update events

### 4. Query Performance (3 tables)
SQL warehouse and query analytics.
- `dim_warehouse` - SQL warehouse configurations
- `fact_query_history` - Query execution history
- `fact_warehouse_events` - Warehouse lifecycle events

### 5. Billing (4 tables)
Cost management and usage tracking.
- `dim_sku` - SKU/pricing definitions
- `fact_usage` - Billable usage records
- `fact_list_prices` - Published pricing
- `fact_account_prices` - Account-specific pricing

### 6. Governance (2 tables)
Data lineage and metadata.
- `fact_table_lineage` - Table-level lineage
- `fact_column_lineage` - Column-level lineage

### 7. MLflow (3 tables)
ML experiment tracking.
- `dim_experiment` - Experiment definitions
- `fact_mlflow_runs` - Training run records
- `fact_mlflow_run_metrics_history` - Metric timeseries

### 8. Model Serving (3 tables)
Model deployment and inference.
- `dim_served_entities` - Deployed model entities
- `fact_endpoint_usage` - Endpoint utilization
- `fact_payload_logs` - Inference request logs

### 9. Security (5 tables)
Access control and auditing.
- `fact_audit_logs` - Security audit trail
- `fact_assistant_events` - AI assistant usage
- `fact_clean_room_events` - Clean room activity
- `fact_inbound_network` - Inbound access events
- `fact_outbound_network` - Outbound access events

### 10. Marketplace (2 tables)
Databricks Marketplace analytics.
- `fact_listing_access` - Listing data access
- `fact_listing_funnel` - Listing engagement funnel

### 11. Data Quality Monitoring (2 tables)
Data quality metrics.
- `fact_data_quality_monitoring_table_results` - Table DQ results
- `fact_dq_monitoring` - DQ monitoring events

### 12. Data Classification (2 tables)
Data classification results.
- `fact_data_classification` - Classification events
- `fact_data_classification_results` - Classification outcomes

### 13. Storage (1 table)
Storage optimization.
- `fact_predictive_optimization` - Optimization operations

## Key Design Principles

### 1. YAML-Driven Schema
All table schemas defined in `gold_layer_design/yaml/{domain}/*.yaml`
- Single source of truth
- Runtime table creation from YAML
- No embedded DDL in code

### 2. Dimensional Modeling
- **Surrogate keys** for dimension PKs
- **Composite keys** for fact PKs (typically workspace_id + entity_id)
- **Foreign keys** reference dimension PKs (NOT ENFORCED)

### 3. Column Documentation
Every column has LLM-friendly descriptions with:
- Business context
- Technical implementation details
- Data lineage information

### 4. Standard Properties
All tables include:
```sql
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'layer' = 'gold'
)
CLUSTER BY AUTO
```

## Relationship Strategy

### Dimension-Fact Relationships
- Facts contain foreign keys to relevant dimensions
- `workspace_id` is the most common FK (links to `dim_workspace`)
- Composite FKs used where dimensions have composite PKs

### Cross-Domain Relationships
```
dim_workspace (shared)
    ↓
├── dim_job → fact_job_run_timeline
├── dim_cluster → fact_node_timeline
├── dim_warehouse → fact_query_history
├── dim_experiment → fact_mlflow_runs
└── ... (all domains reference workspace)
```

## File Structure

```
gold_layer_design/
├── design/
│   └── 00_design_overview.md      # This file
├── erd/
│   ├── 00_erd_index.md            # ERD navigation
│   ├── 01_lakeflow_erd.md         # Domain ERDs
│   └── ...
└── yaml/
    ├── billing/                    # Domain YAMLs
    ├── compute/
    └── ...
```

## References

- [Databricks System Tables](https://docs.databricks.com/en/admin/system-tables/)
- [Unity Catalog Constraints](https://docs.databricks.com/en/tables/constraints.html)
- [Kimball Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)

