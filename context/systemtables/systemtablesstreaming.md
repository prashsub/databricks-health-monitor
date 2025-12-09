Table	Description	Supports streaming	Free retention period	Includes global or regional data
Audit logs (Public Preview)	"Includes records for all audit events from workspaces in your region. For a list of available audit events, see Audit log reference.
Table path: system.access.audit"	Yes	365 days	Regional for workspace-level events. Global for account-level events.
Billable usage	"Includes records for all billable usage across your account.
Table path: system.billing.usage"	Yes	365 days	Global
Clean room events (Public Preview)	"Captures events related to clean rooms.
Table path: system.access.clean_room_events"	Yes	365 days	Regional
Clusters	A slow-changing dimension table that contains the full history of compute configurations over time for any cluster.	Yes	365 days	Regional
Column lineage	"Includes a record for each read or write event on a Unity Catalog column (but does not include events that do not have a source).
Table path: system.access.column_lineage"	Yes	365 days	Regional
Data classification results (Beta)	"Stores column-level detections of sensitive data classes across enabled catalogs in your metastore.
Table path: system.data_classification.results"	No	365 days	Regional
Data quality monitoring results (Beta)	"Stores results of data quality monitoring checks (freshness, completeness) and incident information, including downstream impact and root cause analysis, across enabled tables in your metastore.
Table path: system.data_quality_monitoring.table_results"	No	Indefinite	Regional
Databricks Assistant events (Public Preview)	"Tracks user messages sent to the Databricks Assistant.
Table path: system.access.assistant_events"	No	365 days	Regional
Delta Sharing data materialization events	"Captures data materialization events created from view, materialized view, and streaming table sharing.
Table path: system.sharing.materialization_history"	Yes	365 days	Regional for workspace-level events.
Job run timeline (Public Preview)	"Tracks the start and end times of job runs.
Table path: system.lakeflow.job_run_timeline"	Yes	365 days	Regional
Job task timeline (Public Preview)	"Tracks the start and end times and compute resources used for job task runs.
Table path: system.lakeflow.job_task_run_timeline"	Yes	365 days	Regional
Job tasks (Public Preview)	"Tracks all job tasks that run in the account.
Table path: system.lakeflow.job_tasks"	Yes	365 days	Regional
Jobs (Public Preview)	"Tracks all jobs created in the account.
Table path: system.lakeflow.jobs"	Yes	365 days	Regional
Marketplace funnel events (Public Preview)	"Includes consumer impression and funnel data for your listings.
Table path: system.marketplace.listing_funnel_events"	Yes	365 days	Regional
Marketplace listing access (Public Preview)	"Includes consumer info for completed request data or get data events on your listings.
Table path: system.marketplace.listing_access_events"	Yes	365 days	Regional
MLflow tracking experiment metadata (Public Preview)	"Each row represents an experiment created in the Databricks-managed MLflow system.
Table path: system.mlflow.experiments_latest"	Yes	180 days	Regional
MLflow tracking run metadata (Public Preview)	"Each row represents a run created in the Databricks-managed MLflow system.
Table path: system.mlflow.runs_latest"	Yes	180 days	Regional
MLflow tracking run metrics (Public Preview)	"Holds the timeseries metrics logged to MLflow associated with a given model training, evaluation, or agent development.
Table path: system.mlflow.run_metrics_history"	Yes	180 days	Regional
Model serving endpoint data (Public Preview)	"A slow-changing dimension table that stores metadata for each served foundation model in a model serving endpoint.
Table path: system.serving.served_entities"	Yes	365 days	Regional
Model serving endpoint usage (Public Preview)	"Captures token counts for each request to a model serving endpoint and its responses. To capture the endpoint usage in this table, you must enable usage tracking on your serving endpoint.
Table path: system.serving.endpoint_usage"	Yes	90 days	Regional
Network access events (Inbound) (Public Preview)	"A table that records an event for every time inbound access to a workspace is denied by an ingress policy.
Table path: system.access.inbound_network"	Yes	30 days	Regional
Network access events (Outbound) (Public Preview)	"A table that records an event every time outbound internet access is denied from your account.
Table path: system.access.outbound_network"	Yes	365 days	Regional
Node timeline	"Captures the utilization metrics of your all-purpose and jobs compute resources.
Table path: system.compute.node_timeline"	Yes	90 days	Regional
Node types	"Captures the currently available node types with their basic hardware information.
Table path: system.compute.node_types"	No	Indefinite	Regional
Pipeline update timeline (Public Preview)	"Tracks the start and end times and compute resources used for pipeline updates.
Table path: system.lakeflow.pipeline_update_timeline"	Yes	365 days	Regional
Pipelines (Public Preview)	"Tracks all pipelines created in the account.
Table path: system.lakeflow.pipelines"	Yes	365 days	Regional
Predictive optimization (Public Preview)	"Tracks the operation history of the predictive optimization feature.
Table path: system.storage.predictive_optimization_operations_history"	No	180 days	Regional
Pricing	"A historical log of SKU pricing. A record gets added each time there is a change to a SKU price.
Table path: system.billing.list_prices"	No	Indefinite	Global
Query history (Public Preview)	"Captures records for all queries run on SQL warehouses and serverless compute for notebooks and jobs.
Table path: system.query.history"	No	365 days	Regional
SQL warehouse events (Public Preview)	"Captures events related to SQL warehouses. For example, starting, stopping, running, scaling up and down.
Table path: system.compute.warehouse_events"	Yes	365 days	Regional
SQL warehouses (Public Preview)	"Contains the full history of configurations over time for any SQL warehouse.
Table path: system.compute.warehouses"	Yes	365 days	Regional
Table lineage	"Includes a record for each read or write event on a Unity Catalog table or path.
Table path: system.access.table_lineage"	Yes	365 days	Regional
Workspaces (Public Preview)	"The workspaces_latest table is a slow-changing dimension table of metadata for all the workspaces in the account.
Table path: system.access.workspaces_latest"	No	Indefinite	Global