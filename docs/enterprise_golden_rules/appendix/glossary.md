# Glossary of Terms

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | APP-GLOSS-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Platform Team |
| **Status** | Approved |

---

## A

### AGGREGATE Metric
A Lakehouse Monitoring custom metric type that performs aggregations (SUM, AVG, COUNT) on source data. Stored in `_profile_metrics` table under the `input_columns` value.

### Asset Bundle
See **Databricks Asset Bundle**.

### Auto Loader
Databricks feature for incrementally processing new data files as they arrive in cloud storage. Uses `cloudFiles` format in Spark structured streaming.

---

## B

### Bronze Layer
First layer in Medallion Architecture. Contains raw, unvalidated data as ingested from source systems. Key property: CDF enabled for downstream streaming.

### Business Key
Natural identifier from source system (e.g., `customer_id`, `order_id`). Contrasts with surrogate keys which are generated.

---

## C

### CDF (Change Data Feed)
Delta Lake feature that records row-level changes. Enables incremental streaming from Bronze to Silver layer without full table scans.

### Checkpoint
Stored state for streaming queries or LangGraph workflows. Enables resume from failure and conversation continuity.

### CLUSTER BY AUTO
Delta Lake feature that automatically selects optimal clustering columns based on query patterns. Replaces manual Z-ORDER.

### Constraint (PK/FK)
Unity Catalog supports informational PRIMARY KEY and FOREIGN KEY constraints with `NOT ENFORCED`. Used for query optimization and documentation, not data validation.

---

## D

### Databricks Asset Bundle (DAB)
Infrastructure-as-code approach for defining Databricks resources (jobs, pipelines, schemas) in YAML. Deployed via `databricks bundle` CLI.

### Delta Lake
Open-source storage layer providing ACID transactions, time travel, and schema enforcement on data lakes. Required format for all tables.

### Delta Live Tables (DLT)
Declarative framework for building ETL pipelines with automatic dependency management and data quality expectations.

### DERIVED Metric
Lakehouse Monitoring metric type calculated from other metrics. Can only reference metrics in the same `column_name` row.

### DLT Expectation
Data quality rule in Delta Live Tables. Types: `expect` (warn), `expect_or_drop` (drop invalid), `expect_or_fail` (stop pipeline).

### DQX
Databricks Labs Data Quality framework. Provides detailed failure diagnostics beyond basic DLT expectations.

---

## E

### Enriched View
Pre-joined view combining fact and dimension data to work around Metric View transitive join limitations.

---

## F

### Fact Table
Gold layer table containing measurable events/transactions. Has grain (what each row represents) and foreign keys to dimensions.

### Feature Table
Unity Catalog table containing ML features with defined primary keys for point-in-time lookups during training and inference.

---

## G

### Genie Space
Natural language interface to data. Uses Metric Views, TVFs, and tables as trusted assets for query generation.

### Gold Layer
Third layer in Medallion Architecture. Contains business-level entities (dimensions, facts) with constraints, documentation, and semantic clarity.

---

## I

### input_columns
Lakehouse Monitoring parameter that determines where custom metrics are stored. Use `[":table"]` for table-level KPIs.

### is_current
Boolean column in SCD Type 2 dimensions indicating the current version of a record. Always filter on `is_current = true` for current state.

---

## L

### Lakebase
Databricks memory system for GenAI agents. Provides CheckpointSaver (short-term) and DatabricksStore (long-term) storage.

### Lakehouse Monitoring
Automated data quality monitoring with drift detection, profiling, and custom metrics. Creates `_profile_metrics` and `_drift_metrics` tables.

### LangGraph
Framework for building stateful, multi-actor LLM applications with graph-based workflows.

### Liquid Clustering
Delta Lake feature for automatic data organization. Enabled via `CLUSTER BY AUTO`.

---

## M

### Medallion Architecture
Data organization pattern with three layers: Bronze (raw), Silver (validated), Gold (business). Standard for lakehouse implementations.

### Metric View
Semantic layer object defining dimensions and measures in YAML. Enables business-friendly querying via Genie and AI/BI.

### MLflow
Open-source platform for ML lifecycle management. Used for experiment tracking, model registry, and serving.

---

## O

### OBO (On-Behalf-Of)
Authentication pattern where Model Serving uses end-user credentials to access resources. Only works in Model Serving context.

### output_schema
Required MLflow parameter for Unity Catalog models defining the model's output structure.

---

## P

### Photon
Databricks vectorized query engine providing significant performance improvements for SQL and DataFrame operations.

### Predictive Optimization
Delta Lake feature that automatically optimizes tables based on query patterns. Enabled at catalog or schema level.

### Profile Metrics
Lakehouse Monitoring output table containing data profiling results and custom metrics. Named `{table}_profile_metrics`.

---

## Q

### Quarantine Table
DLT table capturing records that failed data quality expectations. Pattern: `expect_or_drop` + separate quarantine capture.

---

## R

### ResponsesAgent
MLflow base class for building conversational AI agents. Required for production agent deployment.

### RACI Matrix
Framework defining roles: Responsible (does work), Accountable (approves), Consulted (provides input), Informed (notified).

### ROW_NUMBER
SQL window function used in TVFs to implement parameterized limit (since `LIMIT ${param}` is not allowed).

---

## S

### SCD Type 2
Slowly Changing Dimension pattern preserving history. Uses `effective_from`, `effective_to`, and `is_current` columns.

### Serverless
Compute type where Databricks manages infrastructure. Required for all new jobs and warehouses.

### Silver Layer
Second layer in Medallion Architecture. Contains validated, deduplicated, and quality-checked data processed by DLT.

### Surrogate Key
System-generated unique identifier (often MD5 hash). Contrasts with business keys from source systems.

---

## T

### TBLPROPERTIES
Delta Lake table metadata. Includes optimization settings (`delta.enableChangeDataFeed`) and governance tags (`layer`, `domain`).

### TVF (Table-Valued Function)
SQL function returning a table. Used for parameterized queries in Genie Spaces. Must use STRING for date parameters.

---

## U

### Unity Catalog
Databricks unified governance solution for data and AI assets. Provides catalogs, schemas, access control, and lineage.

---

## V

### v1.1 (Metric View)
Current Metric View specification version. Does NOT support `name`, `time_dimension`, or `window_measures` fields.

### v3.0 (Comment Format)
Standardized comment format for TVFs and Metric Views. Uses bullet points: PURPOSE, BEST FOR, NOT FOR, RETURNS, PARAMS, SYNTAX, NOTE.

---

## W

### Widget
Databricks notebook parameter mechanism. Access via `dbutils.widgets.get()` in notebooks running via `notebook_task`.

### Workspace Client
Databricks SDK class for interacting with workspace APIs. Context-aware creation is required for proper authentication.

---

## Y

### YAML-Driven Schema
Pattern where Gold layer table schemas are defined in YAML files (`gold_layer_design/yaml/`) and tables are created dynamically from these definitions.

---

## Acronym Reference

| Acronym | Meaning |
|---------|---------|
| **CDF** | Change Data Feed |
| **DAB** | Databricks Asset Bundle |
| **DLT** | Delta Live Tables |
| **DQX** | Data Quality (Databricks Labs) |
| **FK** | Foreign Key |
| **KPI** | Key Performance Indicator |
| **LLM** | Large Language Model |
| **ML** | Machine Learning |
| **OBO** | On-Behalf-Of |
| **PII** | Personally Identifiable Information |
| **PK** | Primary Key |
| **RACI** | Responsible, Accountable, Consulted, Informed |
| **SCD** | Slowly Changing Dimension |
| **TVF** | Table-Valued Function |
| **UC** | Unity Catalog |

---

## Rule ID Prefixes

| Prefix | Domain |
|--------|--------|
| **EA** | Enterprise Architecture |
| **PA** | Platform Architecture |
| **DP** | Data Pipelines |
| **SL** | Semantic Layer |
| **ML** | Machine Learning |
| **MO** | Monitoring |
| **DB** | Dashboards |

---

## Related Documents

- [Golden Rules Index](../README.md)
- [Quick Reference Cards](quick-reference-cards.md)
- [All Standards Documents](../)
