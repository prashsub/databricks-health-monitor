# Phase 2: Gold Layer Design

## Overview

**Status:** ✅ Implemented  
**Purpose:** Transform Bronze system tables into a dimensional model (star schema) optimized for analytics, AI/BI, and Genie natural language queries.

---

## Architecture Summary

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BRONZE LAYER (21+ tables)                            │
│                                                                              │
│   Raw system tables with CDF enabled, minimal transformation                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOLD LAYER (37 tables)                               │
│                                                                              │
│  ┌───────────────────┐    ┌──────────────────────────────────────────────┐  │
│  │   DIMENSIONS (12) │    │              FACTS (25)                      │  │
│  │                   │    │                                              │  │
│  │  dim_workspace    │───▶│  fact_job_run_timeline                      │  │
│  │  dim_cluster      │    │  fact_query_history                         │  │
│  │  dim_job          │    │  fact_usage                                 │  │
│  │  dim_warehouse    │    │  fact_audit_logs                            │  │
│  │  dim_experiment   │    │  fact_node_timeline                         │  │
│  │  ...              │    │  ...                                        │  │
│  └───────────────────┘    └──────────────────────────────────────────────┘  │
│                                                                              │
│                    Primary Keys + Foreign Keys (NOT ENFORCED)                │
│                    LLM-Friendly Column Descriptions                          │
│                    YAML-Driven Schema Definitions                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Distribution

| Category | Count | Description |
|----------|-------|-------------|
| **Dimensions** | 12 | Reference/lookup tables with descriptive attributes |
| **Facts** | 25 | Transactional/metric tables with measures |
| **Total** | 37 | |

---

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

---

## Key Design Principles

### 1. YAML-Driven Schema (Single Source of Truth)

All table schemas defined in `gold_layer_design/yaml/{domain}/*.yaml`:

```yaml
# Example: dim_job.yaml
table_name: dim_job
description: "Dimension table containing job definitions and configurations"
columns:
  - name: job_key
    type: STRING
    nullable: false
    description: "Surrogate key for job dimension (MD5 hash)"
  - name: workspace_id
    type: STRING
    nullable: false
    description: "Workspace identifier (FK to dim_workspace)"
  - name: job_id
    type: STRING
    nullable: false
    description: "Natural key - Databricks job identifier"
primary_key:
  columns: [job_key]
  constraint_name: pk_dim_job
foreign_keys:
  - columns: [workspace_id]
    references:
      table: dim_workspace
      columns: [workspace_id]
    constraint_name: fk_dim_job_workspace
```

**Benefits:**
- Schema changes require only YAML edits
- Runtime table creation from configuration
- No embedded DDL in Python code
- Reviewable diffs for schema changes

### 2. Dimensional Modeling (Kimball)

| Concept | Implementation |
|---------|----------------|
| **Surrogate Keys** | MD5 hash for dimension PKs |
| **Composite Keys** | workspace_id + entity_id for fact PKs |
| **Foreign Keys** | NOT ENFORCED (informational only) |
| **SCD Type** | Type 1 (overwrite) for most dimensions |

### 3. LLM-Friendly Documentation

Every column includes dual-purpose descriptions:

```yaml
- name: total_dbu_usage
  description: |
    Total DBU consumption for the billing period.
    Business: Primary cost metric for compute usage tracking and budgeting.
    Technical: Aggregated from system.billing.usage, rounded to 2 decimal places.
```

### 4. Standard Table Properties

All Gold tables include:

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

---

## Implementation Details

### Asset Bundle Structure

```
resources/gold/
├── gold_setup_job.yml       # Table creation orchestrator
└── gold_merge_job.yml       # Data pipeline (future)

src/gold/
├── setup_tables.py          # YAML-driven table creation
└── add_all_fk_constraints.py # FK constraint application

gold_layer_design/
├── design/
│   └── 00_design_overview.md
├── erd/
│   ├── 00_master_erd.md
│   └── {domain}_erd.md
└── yaml/
    ├── billing/*.yaml
    ├── compute/*.yaml
    ├── governance/*.yaml
    ├── lakeflow/*.yaml
    ├── marketplace/*.yaml
    ├── mlflow/*.yaml
    ├── model_serving/*.yaml
    ├── query_performance/*.yaml
    ├── security/*.yaml
    ├── shared/*.yaml
    └── storage/*.yaml
```

### Setup Job Configuration

```yaml
resources:
  jobs:
    gold_setup_job:
      name: "[${bundle.target}] Health Monitor - Gold Setup"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - pyyaml>=6.0
      
      tasks:
        - task_key: setup_all_tables
          notebook_task:
            notebook_path: ../../src/gold/setup_tables.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.system_gold_schema}
        
        - task_key: add_fk_constraints
          depends_on:
            - task_key: setup_all_tables
          notebook_task:
            notebook_path: ../../src/gold/add_all_fk_constraints.py
```

### Table Creation Flow

```python
# Simplified flow in setup_tables.py

1. Discover all YAML files in gold_layer_design/yaml/
2. Parse each YAML into TableSchema dataclass
3. Generate CREATE TABLE DDL from schema
4. Execute DDL with inline PK constraint
5. Apply FK constraints in separate step (after all tables exist)
```

---

## Relationship Strategy

### Primary Key Pattern

**Dimensions:**
```sql
-- Surrogate key as PK
CONSTRAINT pk_dim_job PRIMARY KEY (job_key) NOT ENFORCED
```

**Facts:**
```sql
-- Composite key reflecting grain
CONSTRAINT pk_fact_job_run PRIMARY KEY (workspace_id, job_id, run_id) NOT ENFORCED
```

### Foreign Key Pattern

```sql
-- Applied via ALTER TABLE after all tables exist
ALTER TABLE fact_job_run_timeline
ADD CONSTRAINT fk_job_run_workspace
FOREIGN KEY (workspace_id) REFERENCES dim_workspace(workspace_id) NOT ENFORCED
```

### Cross-Domain Relationships

```
dim_workspace (shared)
    │
    ├──▶ dim_job ──────────▶ fact_job_run_timeline
    │                              │
    │                              ├──▶ fact_job_task_run_timeline
    │                              │
    ├──▶ dim_cluster ──────▶ fact_node_timeline
    │
    ├──▶ dim_warehouse ────▶ fact_query_history
    │                              │
    │                              └──▶ fact_warehouse_events
    │
    ├──▶ dim_experiment ───▶ fact_mlflow_runs
    │                              │
    │                              └──▶ fact_mlflow_run_metrics_history
    │
    └──▶ fact_usage (direct FK)
```

---

## Deployment

### Prerequisites

1. Phase 1 Bronze layer deployed
2. Unity Catalog schema created
3. Service principal with schema permissions

### Deployment Commands

```bash
# Deploy bundle
databricks bundle deploy -t dev

# Create all Gold tables
databricks bundle run -t dev gold_setup_job

# Verify tables created
databricks bundle run -t dev gold_setup_job  # Idempotent
```

---

## Success Criteria

- [ ] 37 Gold tables created with proper schema
- [ ] 12 dimension tables with surrogate PKs
- [ ] 25 fact tables with composite PKs
- [ ] All FK constraints applied (NOT ENFORCED)
- [ ] YAML files as single source of truth
- [ ] LLM-friendly descriptions on all columns
- [ ] ERD documentation complete for all domains

---

## References

- [Databricks Unity Catalog Constraints](https://docs.databricks.com/en/tables/constraints.html)
- [Kimball Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/)
- [cursor rule: YAML-Driven Gold Setup](../.cursor/rules/25-yaml-driven-gold-setup.mdc)
- [cursor rule: Unity Catalog Constraints](../.cursor/rules/05-unity-catalog-constraints.mdc)

