| System table path                                           | Primary category                       | Secondary categories                    |
| ----------------------------------------------------------- | -------------------------------------- | --------------------------------------- |
| `system.billing.usage`                                      | **Cost**                               | Performance, Reliability                |
| `system.billing.list_prices`                                | **Cost**                               | –                                       |
| `system.compute.node_timeline`                              | **Cost**                               | Performance, Reliability                |
| `system.compute.node_types`                                 | **Cost**                               | Performance                             |
| `system.compute.clusters`                                   | **Performance**                        | Cost, Reliability                       |
| `system.compute.warehouses`                                 | **Performance**                        | Cost, Reliability                       |
| `system.compute.warehouse_events`                           | **Performance**                        | Reliability                             |
| `system.query.history`                                      | **Performance**                        | Cost, Reliability                       |
| `system.lakeflow.job_run_timeline`                          | **Reliability**                        | Performance, Cost                       |
| `system.lakeflow.job_task_run_timeline`                     | **Reliability**                        | Performance, Cost                       |
| `system.lakeflow.pipeline_update_timeline`                  | **Reliability**                        | Performance, Governance & Data Quality  |
| `system.lakeflow.jobs`                                      | **Reliability**                        | Performance, Cost                       |
| `system.lakeflow.job_tasks`                                 | **Reliability**                        | Performance                             |
| `system.lakeflow.pipelines`                                 | **Reliability**                        | Performance, Governance & Data Quality  |
| `system.storage.predictive_optimization_operations_history` | **Governance & Data Quality**          | Performance, Cost                       |
| `system.data_quality_monitoring.table_results`              | **Governance & Data Quality**          | Reliability                             |
| `system.data_classification.results`                        | **Governance & Data Quality**          | Security                                |
| `system.access.table_lineage`                               | **Governance & Data Quality**          | Security                                |
| `system.access.column_lineage`                              | **Governance & Data Quality**          | Security                                |
| `system.access.audit`                                       | **Security**                           | Governance & Data Quality               |
| `system.access.inbound_network`                             | **Security**                           | Performance                             |
| `system.access.outbound_network`                            | **Security**                           | Performance                             |
| `system.access.clean_room_events`                           | **Security**                           | Governance & Data Quality               |
| `system.sharing.materialization_history`                    | **Governance & Data Quality**          | Security                                |
| `system.marketplace.listing_funnel_events`                  | **Governance & Data Quality**          | Security                                |
| `system.marketplace.listing_access_events`                  | **Governance & Data Quality**          | Security                                |
| `system.serving.served_entities`                            | **Performance**                        | Cost, Reliability                       |
| `system.serving.endpoint_usage`                             | **Cost**                               | Performance, Reliability                |
| `system.mlflow.experiments_latest`                          | **Governance & Data Quality**          | Reliability                             |
| `system.mlflow.runs_latest`                                 | **Governance & Data Quality**          | Reliability                             |
| `system.mlflow.run_metrics_history`                         | **Reliability**                        | Performance                             |
| `system.access.assistant_events`                            | **Governance & Data Quality**          | Security                                |
| `system.access.workspaces_latest`                           | **All Categories (Global Dimension)**  | Cost, Performance, Security, Reliability, Governance & Data Quality |


Shared core dimensions

| Table                             | Logical PK                                               | Important FKs / relationships                                                                                                                                                                         |
| --------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `system.access.workspaces_latest` | `workspace_id` (plus `account_id` as attribute)          | **Referenced by** almost every other table via `workspace_id` and `account_id`.                                                                                                                       |
| `system.compute.clusters`         | `(cluster_id, change_time)` (SCD), plus `workspace_id`   | **Referenced by** `billing.usage.usage_metadata.cluster_id`, `compute.node_timeline.cluster_id`, `lakeflow.*_timeline.compute_ids`, `query.history.cluster_id` (when present). ([Microsoft Learn][1]) |
| `system.compute.node_types`       | `node_type`                                              | **Referenced by** `compute.clusters.driver_node_type`, `compute.clusters.worker_node_type`, `compute.node_timeline.node_type`. ([Microsoft Learn][1])                                                 |
| `system.compute.warehouses`       | `(warehouse_id, change_time)` (SCD), plus `workspace_id` | **Referenced by** `compute.warehouse_events.warehouse_id`, `query.history.warehouse_id`, and `billing.usage.usage_metadata.warehouse_id`. ([Databricks Documentation][2])                             |

[1]: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute "Compute system tables reference - Azure Databricks | Microsoft Learn"
[2]: https://docs.databricks.com/aws/en/admin/system-tables/warehouses?utm_source=chatgpt.com "Warehouses system table reference | Databricks on AWS"



A. Cost
| Table                                                       | Logical PK                              | Important FKs                                                                                                                                                                                                                                                                                                                     |
| ----------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `system.billing.usage`                                      | `record_id`                             | `workspace_id → access.workspaces_latest.workspace_id`; `usage_metadata.cluster_id → compute.clusters.cluster_id`; `usage_metadata.dlt_pipeline_id → lakeflow.pipelines.pipeline_id`; `usage_metadata.warehouse_id → compute.warehouses.warehouse_id`; `sku_name → billing.list_prices.sku_name`. ([Databricks Documentation][1]) |
| `system.billing.list_prices`                                | `(sku_name, effective_start_time)`      | Joined from `billing.usage.sku_name` for price context. ([Databricks Documentation][2])                                                                                                                                                                                                                                           |
| `system.compute.node_types`                                 | `node_type`                             | `account_id` links to other tables, but main join is via `node_type`.                                                                                                                                                                                                                                                             |
| `system.compute.node_timeline`                              | `(cluster_id, instance_id, start_time)` | `workspace_id → access.workspaces_latest`; `cluster_id → compute.clusters.cluster_id`; `node_type → compute.node_types.node_type`. ([Microsoft Learn][3])                                                                                                                                                                         |
| `system.compute.warehouses`                                 | `(warehouse_id, change_time)`           | `workspace_id → access.workspaces_latest`; joined from `billing.usage` & `query.history`. ([Databricks Documentation][4])                                                                                                                                                                                                         |
| `system.serving.endpoint_usage`                             | `(request_id)` (per call)               | `workspace_id → access.workspaces_latest`; `endpoint_id → serving.served_entities.endpoint_id`. ([Medium][5])                                                                                                                                                                                                                     |
| `system.storage.predictive_optimization_operations_history` | `(operation_id)`                        | `workspace_id → access.workspaces_latest`; `table_full_name` ties logically to objects that also appear in lineage, DQ, etc. ([Databricks Documentation][6])                                                                                                                                                                      |

[1]: https://docs.databricks.com/aws/en/admin/system-tables/billing?utm_source=chatgpt.com "Billable usage system table reference | Databricks on AWS"
[2]: https://docs.databricks.com/aws/en/admin/usage/system-tables?utm_source=chatgpt.com "Monitor costs using system tables | Databricks on AWS"
[3]: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute "Compute system tables reference - Azure Databricks | Microsoft Learn"
[4]: https://docs.databricks.com/aws/en/admin/system-tables/warehouses?utm_source=chatgpt.com "Warehouses system table reference | Databricks on AWS"
[5]: https://medium.com/%40wesbert/databricks-system-tables-overview-its-about-answering-questions-f1c22f190275?utm_source=chatgpt.com "Databricks System Tables Overview — It's About ..."
[6]: https://docs.databricks.com/aws/en/admin/system-tables/predictive-optimization?utm_source=chatgpt.com "Predictive optimization system table reference"

B. Performance

| Table                                      | Logical PK                              | Important FKs                                                                                                                                                                                                                     |
| ------------------------------------------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `system.compute.clusters`                  | `(cluster_id, change_time)`             | FKs from `billing.usage`, `compute.node_timeline`, `lakeflow.*_timeline`, `query.history`.                                                                                                                                        |
| `system.compute.warehouses`                | `(warehouse_id, change_time)`           | `workspace_id → access.workspaces_latest`; joined from `billing.usage` & `query.history`. ([Databricks Documentation][1])                                                                                                         |
| `system.compute.warehouse_events`          | `(warehouse_id, event_time)`            | `warehouse_id → compute.warehouses.warehouse_id`; `workspace_id → access.workspaces_latest`. ([Databricks Documentation][2])                                                                                                      |
| `system.query.history`                     | `statement_id`                          | `workspace_id → access.workspaces_latest`; `warehouse_id → compute.warehouses.warehouse_id`; `cluster_id → compute.clusters.cluster_id` (where set); `job_id → lakeflow.jobs.job_id` (where set). ([Databricks Documentation][3]) |
| `system.serving.served_entities`           | `endpoint_id` (plus `served_entity_id`) | `workspace_id → access.workspaces_latest`; referenced by `serving.endpoint_usage.endpoint_id`. ([Microsoft Learn][4])                                                                                                             |

[1]: https://docs.databricks.com/aws/en/admin/system-tables/warehouses?utm_source=chatgpt.com "Warehouses system table reference | Databricks on AWS"
[2]: https://docs.databricks.com/aws/en/admin/system-tables/warehouse-events?utm_source=chatgpt.com "Warehouse events system table reference"
[3]: https://docs.databricks.com/aws/en/admin/system-tables/query-history?utm_source=chatgpt.com "Query history system table reference | Databricks on AWS"
[4]: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ "Monitor account activity with system tables - Azure Databricks | Microsoft Learn"

C. Reliability

| Table                                      | Logical PK                              | Important FKs                                                                                                                                                                                                                     |
| ------------------------------------------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `system.lakeflow.jobs`                     | `job_id`                                | `workspace_id → access.workspaces_latest`; referenced by `job_tasks`, `job_run_timeline`, `job_task_run_timeline`. ([Databricks Documentation][1])                                                                                |
| `system.lakeflow.job_tasks`                | `(job_id, task_id)`                     | `job_id → lakeflow.jobs.job_id`. ([Databricks Documentation][1])                                                                                                                                                                  |
| `system.lakeflow.job_run_timeline`         | `job_run_id`                            | `job_id → lakeflow.jobs.job_id`; `workspace_id → access.workspaces_latest`; `compute_ids.cluster_id → compute.clusters.cluster_id`. ([Microsoft Learn][2])                                                                        |
| `system.lakeflow.job_task_run_timeline`    | `(job_run_id, task_id)`                 | `job_run_id → lakeflow.job_run_timeline.job_run_id`; `task_id → lakeflow.job_tasks.task_id`; `compute_ids.cluster_id → compute.clusters.cluster_id`. ([Microsoft Learn][2])                                                       |
| `system.lakeflow.pipelines`                | `pipeline_id`                           | `workspace_id → access.workspaces_latest`; referenced by `pipeline_update_timeline` and `billing.usage.usage_metadata.dlt_pipeline_id`. ([Microsoft Learn][2])                                                                    |
| `system.lakeflow.pipeline_update_timeline` | `pipeline_update_id`                    | `pipeline_id → lakeflow.pipelines.pipeline_id`; `compute_ids.cluster_id → compute.clusters.cluster_id`. ([Microsoft Learn][2])                                                                                                    |
| `system.mlflow.run_metrics_history`        | `(run_id, metric_key, timestamp)`       | `run_id → mlflow.runs_latest.run_id`. ([Microsoft Learn][2])                                                                                                                                                                      |

[1]: https://docs.databricks.com/aws/en/admin/system-tables/jobs?utm_source=chatgpt.com "Jobs system table reference | Databricks on AWS"
[2]: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ "Monitor account activity with system tables - Azure Databricks | Microsoft Learn"

D. Security
| Table                                    | Logical PK                 | Important FKs                                                                                                                                                                                               |
| ---------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `system.access.workspaces_latest`        | `workspace_id`             | Central dimension: referenced by nearly all tables. ([Microsoft Learn][1])                                                                                                                                  |
| `system.access.audit`                    | `(audit_id)`               | `workspace_id → access.workspaces_latest`; `account_id` common key with others; includes object identifiers that link logically to UC objects that also appear in lineage / billing. ([Microsoft Learn][1]) |
| `system.access.inbound_network`          | `event_id`                 | `workspace_id → access.workspaces_latest`. ([Microsoft Learn][1])                                                                                                                                           |
| `system.access.outbound_network`         | `event_id`                 | `workspace_id → access.workspaces_latest`. ([Microsoft Learn][1])                                                                                                                                           |
| `system.access.clean_room_events`        | `event_id`                 | `workspace_id → access.workspaces_latest`; listing / clean room identifiers tie to marketplace tables. ([Microsoft Learn][1])                                                                               |

[1]: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ "Monitor account activity with system tables - Azure Databricks | Microsoft Learn"

E. Governance & Data Quality
| Table                                                       | Logical PK                                                 | Important FKs                                                                                                                                                                                               |
| ----------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `system.access.table_lineage`                               | `(lineage_id)`                                             | `workspace_id → access.workspaces_latest`; references table identifiers that overlap with DQ, classification, predictive optimization target tables. ([Databricks Documentation][1])                        |
| `system.access.column_lineage`                              | `(column_lineage_id)`                                      | Shares table and column identifiers with `table_lineage` and `data_classification.results`. ([Microsoft Learn][2])                                                                                          |
| `system.data_classification.results`                        | `(classification_id)`                                      | `workspace_id → access.workspaces_latest`; `table_full_name` & `column_name` join logically to lineage and DQ tables. ([Microsoft Learn][2])                                                                |
| `system.data_quality_monitoring.table_results`              | `result_id` (or `(table_full_name, check_time)` logically) | `workspace_id → access.workspaces_latest`; `table_full_name` aligns with lineage, predictive optimization, classification. ([Microsoft Learn][2])                                                            |
| `system.storage.predictive_optimization_operations_history` | `operation_id`                                             | `workspace_id → access.workspaces_latest`; `table_full_name` ties logically to objects that also appear in lineage, DQ, etc. ([Databricks Documentation][3])                                               |
| `system.sharing.materialization_history`                    | `materialization_event_id`                                 | `workspace_id → access.workspaces_latest`; table identifiers connect to lineage / DQ / predictive optimization. ([Microsoft Learn][2])                                                                      |
| `system.marketplace.listing_funnel_events`                  | `funnel_event_id`                                          | Listing identifiers connect to `marketplace.listing_access_events`; `workspace_id` where applicable. ([Microsoft Learn][2])                                                                                  |
| `system.marketplace.listing_access_events`                  | `access_event_id`                                          | Shares listing identifiers with funnel events.                                                                                                                                                              |
| `system.mlflow.experiments_latest`                          | `experiment_id`                                            | `workspace_id → access.workspaces_latest`. ([Microsoft Learn][2])                                                                                                                                           |
| `system.mlflow.runs_latest`                                 | `run_id`                                                   | `experiment_id → mlflow.experiments_latest.experiment_id`; `workspace_id → access.workspaces_latest`. ([Microsoft Learn][2])                                                                                 |
| `system.access.assistant_events`                            | `assistant_event_id`                                       | `workspace_id → access.workspaces_latest`; user principal / workspace join logically with audit & billing for adoption analysis. ([Microsoft Learn][2])                                                      |

[1]: https://docs.databricks.com/aws/en/admin/system-tables/lineage?utm_source=chatgpt.com "Lineage system tables reference | Databricks on AWS"
[2]: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ "Monitor account activity with system tables - Azure Databricks | Microsoft Learn"
[3]: https://docs.databricks.com/aws/en/admin/system-tables/predictive-optimization?utm_source=chatgpt.com "Predictive optimization system table reference"




