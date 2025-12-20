# Phase 3 Addendum 3.6: Genie Spaces for Databricks Health Monitor

## Overview

**Status:** ✅ Implemented (2025-12-19)  
**Dependencies:** Gold Layer (Phase 2), TVFs (Phase 3.2), Metric Views (Phase 3.3), Lakehouse Monitoring (Phase 3.4), ML Models (Phase 3.1)  
**Estimated Effort:** 1.5 weeks  
**Reference:** Cursor Rule 16 - Genie Space Patterns

### Implementation Summary

**Consolidated to 6 Genie Spaces (1 per domain) to prevent sprawl:**

| Genie Space | Agent Domain | Status | Setup Document |
|---|---|---|---|
| Cost Intelligence | 💰 Cost | ✅ Documented | `src/genie/cost_intelligence_genie.md` |
| Job Health Monitor | 🔄 Reliability | ✅ Documented | `src/genie/job_health_monitor_genie.md` |
| Performance | ⚡ Performance | ✅ Documented | `src/genie/performance_genie.md` |
| Security Auditor | 🔒 Security | ✅ Documented | `src/genie/security_auditor_genie.md` |
| Data Quality Monitor | ✅ Quality | ✅ Documented | `src/genie/data_quality_monitor_genie.md` |
| Unified Health Monitor | 🌐 All | ✅ Documented | `src/genie/unified_health_monitor_genie.md` |

**All 6 Genie Spaces have complete setup documents with:**
- ✅ 7-section mandatory structure (A-G)
- ✅ 10-15 benchmark questions with SQL
- ✅ General Instructions (≤20 lines)
- ✅ Data assets documented
- ✅ TVF signatures and examples

**Inventory:** See [`src/genie/GENIE_SPACES_INVENTORY.md`](../src/genie/GENIE_SPACES_INVENTORY.md)

---

## Purpose

Create Databricks Genie Spaces that enable:
- **Natural Language Queries** - Ask questions in plain English
- **Self-Service Analytics** - Non-technical users can explore data
- **Guided Analysis** - Pre-defined questions and context
- **Trusted Assets** - Curated TVFs and metric views for accurate answers
- **ML-Powered Insights** - Leverage predictions, anomaly detection, and forecasts

---

## Asset Summary Across All Addendums

### Comprehensive Asset Inventory

| Asset Type | Total Count | By Domain |
|------------|-------------|-----------|
| **TVFs** | 60 | Cost: 15, Reliability: 12, Performance: 16, Security: 10, Quality: 7 |
| **Metric Views** | 10 | Cost: 2, Performance: 3, Reliability: 1, Security: 2, Quality: 2 |
| **Lakehouse Monitors** | 8 | Cost: 1, Performance: 2, Reliability: 1, Security: 1, Quality: 1, Governance: 1, ML: 1 |
| **ML Models** | 25 | Cost: 6, Performance: 7, Reliability: 5, Quality: 3, Security: 4 |
| **Gold Tables** | 38 | Cost: 4, Performance: 6, Reliability: 6, Security: 7, Quality: 14, Shared: 1 |

### Gold Layer Table Mapping

**Source:** `gold_layer_design/yaml/`

| YAML Folder | Agent Domain | Table Count | Key Tables |
|-------------|--------------|-------------|------------|
| `billing/` | 💰 Cost | 4 | dim_sku, fact_usage, fact_account_prices, fact_list_prices |
| `compute/` | ⚡ Performance | 3 | dim_cluster, dim_node_type, fact_node_timeline |
| `query_performance/` | ⚡ Performance | 3 | dim_warehouse, fact_query_history, fact_warehouse_events |
| `lakeflow/` | 🔄 Reliability | 6 | dim_job, dim_job_task, dim_pipeline, fact_job_run_timeline, fact_job_task_run_timeline, fact_pipeline_update_timeline |
| `security/` | 🔒 Security | 5 | fact_audit_logs, fact_assistant_events, fact_clean_room_events, fact_inbound_network, fact_outbound_network |
| `governance/` | 🔒 Security | 2 | fact_table_lineage, fact_column_lineage |
| `data_classification/` | ✅ Quality | 2 | fact_data_classification, fact_data_classification_results |
| `data_quality_monitoring/` | ✅ Quality | 2 | fact_dq_monitoring, fact_data_quality_monitoring_table_results |
| `storage/` | ✅ Quality | 1 | fact_predictive_optimization |
| `mlflow/` | ✅ Quality | 3 | dim_experiment, fact_mlflow_runs, fact_mlflow_run_metrics_history |
| `model_serving/` | ✅ Quality | 3 | dim_served_entities, fact_endpoint_usage, fact_payload_logs |
| `marketplace/` | ✅ Quality | 2 | fact_listing_access, fact_listing_funnel |
| `shared/` | 🌐 All | 1 | dim_workspace |

---

## Genie Spaces by Agent Domain (1 per Domain)

| Agent Domain | Genie Space | TVFs | Metric Views | ML Models | Monitors | Target Users |
|--------------|-------------|------|--------------|-----------|----------|--------------|
| **💰 Cost** | Cost Intelligence | 15 | 2 | 6 | 1 | FinOps, Finance |
| **⚡ Performance** | Performance (Query + Cluster) | 16 | 3 | 7 | 2 | DBAs, Platform Eng |
| **🔄 Reliability** | Job Health Monitor | 12 | 1 | 5 | 1 | DevOps, Data Eng |
| **🔒 Security** | Security Auditor | 10 | 2 | 4 | 1 | Security, Compliance |
| **✅ Quality** | Data Quality Monitor | 7 | 2 | 3 | 2 | Data Governance |
| **🌐 Unified** | Databricks Health Monitor | 60 | 10 | 25 | 8 | Leadership |

**Total: 6 Genie Spaces** (5 domain-specific + 1 unified for leadership)

---

## Genie Space Design Principles

### Best Practices

1. **1 Space Per Domain** - Prevent Genie sprawl by consolidating to 1 space per agent domain
2. **Rich Context in Instructions** - Provide domain knowledge to the LLM
3. **Trusted Assets** - Register TVFs, metric views, and ML predictions for reliable queries
4. **Benchmark Questions** - Test questions that validate Genie accuracy
5. **Synonyms Everywhere** - Multiple ways to ask the same thing
6. **Guardrails** - Guide users away from unsupported queries
7. **ML Integration** - Surface ML predictions and anomaly alerts naturally

---

## 💰 Cost Agent: Cost Intelligence Genie Space

### Purpose
Enable business users to explore Databricks costs through natural language, with ML-powered forecasting and anomaly detection.

### Configuration

```yaml
# Genie Space: Cost Intelligence
name: "Cost Intelligence"
description: |
  Ask questions about Databricks costs, spending trends, and cost optimization.
  Now with ML-powered forecasting and anomaly detection!
  
  Example questions:
  - "What is our total spend this month?"
  - "Which workspace costs the most?"
  - "Show me daily cost trend for the last 30 days"
  - "Who are the top 10 cost contributors?"
  - "What is our week-over-week cost growth?"
  - "Are there any cost anomalies today?" 🤖
  - "What's the cost forecast for next month?" 🤖
  - "Which resources need tags?" 🤖
  - "Show savings from migrating ALL_PURPOSE clusters" 🤖

instructions: |
  You are a cost analytics assistant for Databricks platform usage, 
  enhanced with ML predictions for forecasting and anomaly detection.
  
  ## Domain Knowledge
  
  ### Key Concepts
  - **DBU (Databricks Unit)**: The unit of processing capability per hour
  - **SKU (Stock Keeping Unit)**: Product category (JOBS_COMPUTE, SQL, etc.)
  - **Workspace**: A Databricks environment for a team or project
  - **List Price**: The per-DBU price for a SKU
  
  ### Cost Hierarchy
  - Account → Workspace → User/Service Principal
  - Costs are attributed to: Jobs, Clusters, Warehouses, or Pipelines
  
  ### Time Periods
  - When users ask about "this month", use DATE_TRUNC('month', CURRENT_DATE())
  - "Last week" means CURRENT_DATE() - INTERVAL 7 DAYS
  - "Last month" means the previous calendar month
  
  ### SKU Categories
  - JOBS_COMPUTE: Automated workflow compute (most efficient for jobs)
  - JOBS_LIGHT_COMPUTE: Low-cost job compute
  - SQL_COMPUTE: SQL Warehouse compute
  - ALL_PURPOSE_COMPUTE: Interactive notebook clusters (less efficient for jobs)
  - DLT: Delta Live Tables pipelines

  ### Cost Efficiency Insight (from Workflow Advisor Blog)
  ALL_PURPOSE clusters are ~40% more expensive than JOB clusters for the same work.
  If a job is running on ALL_PURPOSE, recommend migrating to JOB cluster.

  ## ML Models Available 🤖
  
  ### Cost Anomaly Detector (Isolation Forest)
  - Detects unusual cost patterns in billing data
  - Query `cost_anomaly_predictions` for detected anomalies
  - Fields: `anomaly_score`, `is_anomaly`, `expected_cost`
  
  ### Cost Forecaster (Prophet)
  - 30-day cost forecasting with confidence intervals
  - Query `cost_forecast_predictions` for predictions
  - Fields: `predicted_cost`, `lower_bound`, `upper_bound`, `forecast_date`
  
  ### Tag Recommender (Random Forest + TF-IDF)
  - Recommends tags for untagged resources
  - Query `tag_recommendations` for suggestions
  - Fields: `resource_id`, `recommended_tag`, `confidence_score`
  
  ### User Cost Behavior Predictor (K-Means)
  - Clusters users by cost behavior patterns
  - Query `user_cost_segments` for segments
  - Fields: `user_id`, `segment`, `avg_daily_cost`, `serverless_adoption`
  
  ### ALL_PURPOSE Migration Recommender (Decision Tree)
  - Identifies clusters for migration to JOBS clusters
  - Query `migration_recommendations` for candidates
  - Fields: `cluster_id`, `potential_savings`, `migration_risk`

  ## Lakehouse Monitoring Metrics 📊
  
  Query `fact_usage_profile_metrics` for custom metrics:
  - `total_cost`, `total_dbus`, `serverless_cost`, `tagged_cost`
  - `cost_per_dbu`, `serverless_percentage`, `tag_coverage_percentage`
  
  Query `fact_usage_drift_metrics` for drift detection:
  - `cost_trend` (significant if > 10%)
  - `serverless_adoption_drift`

  ## Query Guidance

  When users ask about:
  - "Top cost drivers" → Use get_top_cost_contributors TVF
  - "Cost trends" → Use get_cost_trend_by_sku TVF
  - "Cost by owner" → Use get_cost_by_owner TVF
  - "Week over week" or "cost growth" → Use get_cost_growth_by_period TVF
  - "ALL_PURPOSE costs" → Use get_all_purpose_cluster_cost TVF
  - "Cost anomalies" → Query cost_anomaly_predictions table 🤖
  - "Cost forecast" → Query cost_forecast_predictions table 🤖
  - "Tag recommendations" → Query tag_recommendations table 🤖
  - "Commit tracking" → Use commit_tracking metric view
  - General cost metrics → Use cost_analytics metric view

  ## Guardrails

  - Do NOT attempt to modify data; this is read-only
  - Do NOT access tables outside the Gold schema
  - If a question cannot be answered, explain what data is needed

data_assets:
  # Metric Views (2)
  - type: metric_view
    name: cost_analytics
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Primary cost analytics with 20 dimensions, 18 measures"

  - type: metric_view
    name: commit_tracking
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Commit/contract tracking for financial planning"

  # TVFs (15)
  - type: function
    name: get_top_cost_contributors
  - type: function
    name: get_cost_trend_by_sku
  - type: function
    name: get_cost_by_owner
  - type: function
    name: get_cost_by_tag
  - type: function
    name: get_untagged_resources
  - type: function
    name: get_tag_coverage
  - type: function
    name: get_cost_week_over_week
  - type: function
    name: get_cost_anomalies
  - type: function
    name: get_cost_forecast_summary
  - type: function
    name: get_cost_mtd_summary
  - type: function
    name: get_commit_vs_actual
  - type: function
    name: get_spend_by_custom_tags
  - type: function
    name: get_cost_growth_analysis
  - type: function
    name: get_cost_growth_by_period
  - type: function
    name: get_all_purpose_cluster_cost
  
  # ML Prediction Tables (6 models) 🤖
  - type: table
    name: cost_anomaly_predictions
    comment: "ML: Anomaly scores and detected cost anomalies"
  - type: table
    name: cost_forecast_predictions
    comment: "ML: 30-day cost forecasts with confidence intervals"
  - type: table
    name: tag_recommendations
    comment: "ML: Suggested tags for untagged resources"
  - type: table
    name: user_cost_segments
    comment: "ML: User segmentation by cost behavior"
  - type: table
    name: migration_recommendations
    comment: "ML: ALL_PURPOSE to JOBS migration candidates"
  - type: table
    name: budget_alert_predictions
    comment: "ML: Prioritized budget alerts by urgency"
  
  # Lakehouse Monitoring Tables 📊
  - type: table
    name: fact_usage_profile_metrics
    comment: "Custom cost metrics from Lakehouse Monitor"
  - type: table
    name: fact_usage_drift_metrics
    comment: "Cost drift detection metrics"
  
  # Gold Tables
  - type: table
    name: fact_usage
  - type: table
    name: dim_workspace
  - type: table
    name: dim_sku

benchmark_questions:
  - question: "What is our total spend this month?"
    expected_result_type: "single_value"
  
  - question: "Show me the top 5 cost contributors"
    expected_result_type: "table"
  
  - question: "Are there any cost anomalies today?"
    expected_result_type: "table"
    note: "Should query cost_anomaly_predictions"
  
  - question: "What's the cost forecast for next week?"
    expected_result_type: "table"
    note: "Should query cost_forecast_predictions"
  
  - question: "Which resources are untagged?"
    expected_result_type: "table"
```

---

## 🔄 Reliability Agent: Job Health Monitor Genie Space

### Purpose
Enable DevOps and data engineers to explore job reliability through natural language, with ML-powered failure prediction and pipeline health scoring.

### Configuration

```yaml
name: "Job Health Monitor"
description: |
  Ask questions about job execution, failures, and reliability metrics.
  Now with ML-powered failure prediction and pipeline health scoring!

  Example questions:
  - "What is our job success rate?"
  - "Show me failed jobs today"
  - "Which jobs have the most failures this week?"
  - "What are our most expensive jobs?"
  - "What is the P95 job duration?"
  - "Show me job outliers"
  - "Which jobs are likely to fail?" 🤖
  - "What's the health score for pipeline X?" 🤖
  - "Will retrying this job succeed?" 🤖

instructions: |
  You are a job monitoring assistant for Databricks workflows,
  enhanced with ML predictions for failure prediction and health scoring.

  ## Domain Knowledge

  ### Job Concepts
  - **Job**: A scheduled or triggered workflow with one or more tasks
  - **Run**: A single execution of a job
  - **Task**: A unit of work within a job (notebook, Python, SQL, etc.)
  - **Result State**: SUCCEEDED, FAILED, ERROR, TIMED_OUT, CANCELED

  ### Termination Codes
  - SUCCESS: Job completed successfully
  - RUN_EXECUTION_ERROR: Task execution failed
  - INTERNAL_ERROR: Platform issue
  - DRIVER_TIMEOUT: Spark driver timed out
  - CLUSTER_ERROR: Cluster failed to start

  ### Metrics
  - **Success Rate**: % of runs with SUCCEEDED state
  - **Failure Rate**: % of runs with FAILED, ERROR, or TIMED_OUT
  - **Repair**: Re-running a failed job or task

  ### Outcome Categories
  - **SUCCEEDED**: Completed successfully
  - **FAILED**: Execution error
  - **SKIPPED**: Task skipped (dependency not met)
  - **UPSTREAM_FAILED**: Previous task failed
  - **CANCELED**: User or system canceled

  ### Outlier Detection (P90 deviation pattern)
  - **DURATION_OUTLIER**: Run duration >1.5x the P90 baseline
  - **COST_OUTLIER**: Run cost >1.5x the P90 baseline
  - Jobs with frequent outliers may have data skew or resource contention

  ## ML Models Available 🤖
  
  ### Job Failure Predictor (XGBoost)
  - Predicts probability of job failure before execution
  - Query `job_failure_predictions` for risk scores
  - Fields: `job_id`, `failure_probability`, `risk_factors`
  
  ### Retry Success Predictor (XGBoost)
  - Predicts whether a failed job will succeed on retry
  - Query `retry_success_predictions` for recommendations
  - Fields: `run_id`, `retry_success_probability`, `recommendation`
  
  ### Pipeline Health Scorer (Gradient Boosting)
  - Scores overall pipeline health (0-100)
  - Query `pipeline_health_scores` for current scores
  - Health Score Ranges:
    - 0-25: Critical - Immediate attention
    - 26-50: Poor - Needs investigation
    - 51-75: Fair - Monitor closely
    - 76-90: Good - Normal operation
    - 91-100: Excellent - Optimal
  
  ### Incident Impact Estimator (Random Forest)
  - Estimates blast radius of job failures
  - Query `incident_impact_predictions` for estimates
  - Fields: `job_id`, `downstream_jobs_affected`, `estimated_impact_hours`
  
  ### Self-Healing Recommender (Thompson Sampling)
  - Recommends self-healing actions with confidence
  - Query `self_healing_recommendations` for suggestions
  - Fields: `run_id`, `recommended_action`, `success_confidence`

  ## Lakehouse Monitoring Metrics 📊
  
  Query `fact_job_run_timeline_profile_metrics` for:
  - `total_runs`, `successful_runs`, `failed_runs`
  - `success_rate`, `failure_rate`
  - `avg_duration_minutes`, `p90_duration_minutes`, `p99_duration_minutes`
  - `duration_cv` (coefficient of variation - stability metric)
  
  Query `fact_job_run_timeline_drift_metrics` for:
  - `success_rate_drift` (significant if < -5%)
  - `duration_drift` (significant if > 20%)

  ## Query Guidance

  When users ask about:
  - "Failed jobs" → Use get_failed_jobs TVF
  - "Success rate" → Use get_job_success_rate TVF
  - "Expensive jobs" → Use get_most_expensive_jobs TVF
  - "Duration percentiles" → Use get_job_duration_percentiles TVF
  - "Repair costs" → Use get_job_repair_costs TVF
  - "Outliers" → Use get_job_outlier_runs TVF
  - "Failure prediction" → Query job_failure_predictions 🤖
  - "Pipeline health" → Query pipeline_health_scores 🤖
  - "Should I retry?" → Query retry_success_predictions 🤖
  - General job metrics → Use job_performance metric view

data_assets:
  # Metric View (1)
  - type: metric_view
    name: job_performance
    comment: "Job execution with 22 measures including P99 duration"

  # TVFs (12)
  - type: function
    name: get_failed_jobs
  - type: function
    name: get_job_success_rate
  - type: function
    name: get_job_duration_percentiles
  - type: function
    name: get_job_failure_trends
  - type: function
    name: get_job_sla_compliance
  - type: function
    name: get_job_run_details
  - type: function
    name: get_most_expensive_jobs
  - type: function
    name: get_job_retry_analysis
  - type: function
    name: get_job_repair_costs
  - type: function
    name: get_job_spend_trend_analysis
  - type: function
    name: get_job_failure_costs
  - type: function
    name: get_job_run_duration_analysis

  # ML Prediction Tables (5 models) 🤖
  - type: table
    name: job_failure_predictions
    comment: "ML: Failure probability scores"
  - type: table
    name: retry_success_predictions
    comment: "ML: Retry success probability"
  - type: table
    name: pipeline_health_scores
    comment: "ML: Pipeline health 0-100"
  - type: table
    name: incident_impact_predictions
    comment: "ML: Blast radius estimates"
  - type: table
    name: self_healing_recommendations
    comment: "ML: Self-healing action suggestions"

  # Lakehouse Monitoring Tables 📊
  - type: table
    name: fact_job_run_timeline_profile_metrics
  - type: table
    name: fact_job_run_timeline_drift_metrics

  # Gold Tables
  - type: table
    name: fact_job_run_timeline
  - type: table
    name: dim_job

benchmark_questions:
  - question: "What is our job success rate this week?"
    expected_result_type: "single_value"
  
  - question: "Show me failed jobs today"
    expected_result_type: "table"
  
  - question: "Which jobs are at risk of failing?"
    expected_result_type: "table"
    note: "Should query job_failure_predictions"
  
  - question: "What's the health score for the ETL pipeline?"
    expected_result_type: "single_value"
    note: "Should query pipeline_health_scores"
```

---

## ⚡ Performance Agent: Query Performance Analyzer Genie Space

### Purpose
Enable DBAs and analysts to explore SQL Warehouse performance with ML-powered optimization recommendations.

### Configuration

```yaml
name: "Query Performance Analyzer"
description: |
  Ask questions about SQL query performance and warehouse efficiency.
  Now with ML-powered query optimization and cache prediction!

  Example questions:
  - "What is our average query duration?"
  - "Show me slow queries from today"
  - "Which warehouse has the highest queue time?"
  - "What is the P95 query duration?"
  - "How many queries ran this week?"
  - "Show me warehouse efficiency analysis"
  - "Which queries need optimization?" 🤖
  - "Will this query hit the cache?" 🤖
  - "What optimizations should I apply?" 🤖

instructions: |
  You are a query performance analyst for Databricks SQL Warehouses,
  enhanced with ML-powered optimization recommendations.

  ## Domain Knowledge

  ### Warehouse Concepts
  - **SQL Warehouse**: Serverless compute for SQL queries
  - **Cluster**: Processing nodes within a warehouse
  - **Queue Time**: Time spent waiting for compute capacity
  - **Spill**: Data written to disk when memory is exceeded
  - **Warehouse Tier**: SERVERLESS (managed), PRO (user-managed), or CLASSIC

  ### Performance Metrics
  - **Duration**: Total time from submission to completion
  - **Queue Time**: Time waiting at capacity
  - **Read Bytes**: Data scanned from storage
  - **Spill Bytes**: Data spilled to disk (indicates memory pressure)

  ### Query Types
  - SELECT: Read queries
  - INSERT/MERGE: Write queries
  - DDL: Schema modifications

  ### Performance Flags (from DBSQL Warehouse Advisor)
  - **SLA breach**: Query duration > 60 seconds (critical threshold)
  - **Slow query**: > 5 minutes (300 seconds)
  - **High queue**: Queue time > 10% of total duration
  - **High spill**: Any spill indicates memory pressure
  - **Query complexity**: Long queries (>5000 chars) or >3 JOINs

  ### Efficiency Categories
  - **EFFICIENT**: No spills, queue <10%, duration <60s
  - **HIGH_SPILL**: Spill bytes > 0
  - **HIGH_QUEUE**: Queue time > 10% of duration
  - **SLOW**: Duration > 60 seconds

  ## ML Models Available 🤖
  
  ### Query Performance Optimizer (XGBoost)
  - Classifies queries as "optimal" or "needs optimization"
  - Query `query_optimization_classifications` for flags
  - Fields: `query_id`, `needs_optimization`, `reason`
  
  ### Cache Hit Predictor (Neural Network)
  - Predicts cache effectiveness for queries
  - Query `cache_hit_predictions` for predictions
  - Fields: `query_id`, `cache_hit_probability`, `recommended_action`
  
  ### Query Optimization Recommender (Multi-Label Classification)
  - Recommends specific optimizations for slow queries
  - Query `query_optimization_recommendations` for suggestions
  - Optimization Categories:
    1. PARTITION_PRUNING
    2. CACHING
    3. BROADCAST_JOIN
    4. PREDICATE_PUSHDOWN
    5. COLUMN_PRUNING
    6. CLUSTER_SIZING
  
  ### Job Duration Predictor (Gradient Boosting)
  - Predicts job completion time
  - Query `job_duration_predictions` for estimates
  - Fields: `job_id`, `predicted_duration_minutes`, `confidence`

  ## Lakehouse Monitoring Metrics 📊
  
  Query `fact_query_history_profile_metrics` for:
  - `total_queries`, `p50_duration_seconds`, `p95_duration_seconds`, `p99_duration_seconds`
  - `avg_queue_time_seconds`, `slow_query_count`, `sla_breach_count`
  - `qps`, `sla_breach_rate`, `query_efficiency`
  
  Query `fact_query_history_drift_metrics` for:
  - `duration_drift` (performance regression)
  - `qps_drift` (volume trend)

  ## Query Guidance

  When users ask about:
  - "Slow queries" → Use get_slow_queries TVF
  - "Warehouse utilization" → Use get_warehouse_utilization TVF
  - "Query efficiency" → Use get_query_efficiency_analysis TVF
  - "High spill queries" → Use get_high_spill_queries TVF
  - "Optimization needed" → Query query_optimization_classifications 🤖
  - "What optimizations?" → Query query_optimization_recommendations 🤖
  - "Cache hit prediction" → Query cache_hit_predictions 🤖
  - General query metrics → Use query_performance metric view

data_assets:
  # Metric Views (3)
  - type: metric_view
    name: query_performance
    comment: "Query performance with 25 measures including P99"
  - type: metric_view
    name: cluster_utilization
    comment: "Cluster resource utilization metrics"
  - type: metric_view
    name: cluster_efficiency
    comment: "Advanced cluster efficiency analytics"

  # TVFs (10)
  - type: function
    name: get_slow_queries
  - type: function
    name: get_warehouse_utilization
  - type: function
    name: get_query_efficiency
  - type: function
    name: get_high_spill_queries
  - type: function
    name: get_query_volume_trends
  - type: function
    name: get_user_query_summary
  - type: function
    name: get_query_latency_percentiles
  - type: function
    name: get_failed_queries
  - type: function
    name: get_query_efficiency_analysis
  - type: function
    name: get_job_outlier_runs

  # ML Prediction Tables (4) 🤖
  - type: table
    name: query_optimization_classifications
    comment: "ML: Query optimization flags"
  - type: table
    name: query_optimization_recommendations
    comment: "ML: Specific optimization suggestions"
  - type: table
    name: cache_hit_predictions
    comment: "ML: Cache effectiveness predictions"
  - type: table
    name: job_duration_predictions
    comment: "ML: Job completion time predictions"

  # Lakehouse Monitoring Tables 📊
  - type: table
    name: fact_query_history_profile_metrics
  - type: table
    name: fact_query_history_drift_metrics

  # Gold Tables
  - type: table
    name: fact_query_history
  - type: table
    name: dim_warehouse
```

---

## ⚡ Performance Agent: Cluster Optimizer Genie Space

### Purpose
Enable infrastructure teams to explore cluster utilization for right-sizing with ML-powered recommendations.

### Configuration

```yaml
name: "Cluster Optimizer"
description: |
  Ask questions about cluster resource utilization and optimization.
  Now with ML-powered capacity planning and right-sizing!

  Example questions:
  - "Which clusters are underutilized?"
  - "What is the average CPU utilization?"
  - "Show me cluster costs by owner"
  - "Which clusters have low memory usage?"
  - "Show me right-sizing recommendations" 🤖
  - "Which clusters are overprovisioned?" 🤖
  - "What's the optimal cluster size for this job?" 🤖

instructions: |
  You are a cluster optimization advisor for Databricks compute,
  enhanced with ML-powered capacity planning.

  ## Domain Knowledge

  ### Cluster Types
  - **All-Purpose**: Interactive notebooks and exploration (less cost-efficient)
  - **Job Cluster**: Ephemeral compute for workflow tasks (most cost-efficient)
  - **Instance Pool**: Pre-allocated instances for faster startup

  ### Utilization Metrics
  - **CPU Utilization**: cpu_user_percent + cpu_system_percent
  - **Memory Utilization**: mem_used_percent
  - **CPU Wait**: IO-bound indicator (high means storage bottleneck)

  ### Provisioning Status (from Workflow Advisor Repo)
  - **UNDERPROVISIONED**: CPU saturation >90% or Memory >85% (scale up)
  - **OVERPROVISIONED**: CPU <20% AND Memory <30% (scale down)
  - **UNDERUTILIZED**: CPU <30% OR Memory <40% (potential savings)
  - **OPTIMAL**: CPU 30-80% and Memory 30-85% (well-sized)

  ### Optimization Thresholds
  - Underutilized: CPU < 30% average
  - Well-utilized: CPU 30-70% average
  - Over-utilized: CPU > 80% sustained

  ### Savings Opportunity
  - **HIGH**: >50% wasted capacity, >$100/day potential savings
  - **MEDIUM**: 30-50% wasted capacity
  - **LOW**: 20-30% wasted capacity
  - **NONE**: Optimal utilization

  ## ML Models Available 🤖
  
  ### Cluster Capacity Planner (Gradient Boosting)
  - Predicts optimal cluster capacity (nodes, cores, memory)
  - Query `cluster_capacity_recommendations` for predictions
  - Fields: `cluster_id`, `recommended_nodes`, `recommended_instance_type`
  
  ### Cluster Right-Sizing Recommender (Multi-Output Regression)
  - Recommends optimal cluster size
  - Query `cluster_rightsizing_recommendations` for suggestions
  - Fields: `cluster_id`, `current_size`, `recommended_size`, `potential_savings`
  
  ### DBR Migration Risk Scorer (LightGBM)
  - Scores risk of migrating to newer DBR versions
  - Query `dbr_migration_risk_scores` for assessments
  - Risk Levels: LOW, MEDIUM, HIGH, CRITICAL
  - Fields: `cluster_id`, `current_dbr`, `target_dbr`, `risk_score`, `risk_level`

  ## Lakehouse Monitoring Metrics 📊
  
  Query `fact_node_timeline_profile_metrics` for:
  - `avg_cpu_utilization`, `avg_memory_utilization`
  - `p95_cpu_total_pct`, `total_node_hours`
  - `cpu_saturation_hours`, `cpu_idle_hours`, `underprovisioned_hours`
  
  Query `fact_node_timeline_drift_metrics` for:
  - `cpu_drift`, `memory_drift`

  ## Query Guidance

  When users ask about:
  - "Cluster utilization" → Use get_cluster_utilization TVF
  - "Underutilized clusters" → Use get_underutilized_clusters TVF
  - "Right-sizing" → Query cluster_rightsizing_recommendations 🤖
  - "Optimal cluster size" → Query cluster_capacity_recommendations 🤖
  - "DBR migration risk" → Query dbr_migration_risk_scores 🤖
  - General metrics → Use cluster_utilization metric view

data_assets:
  # Metric Views (2)
  - type: metric_view
    name: cluster_utilization
  - type: metric_view
    name: cluster_efficiency

  # TVFs (6)
  - type: function
    name: get_cluster_utilization
  - type: function
    name: get_cluster_resource_metrics
  - type: function
    name: get_underutilized_clusters
  - type: function
    name: get_jobs_without_autoscaling
  - type: function
    name: get_jobs_on_legacy_dbr
  - type: function
    name: get_cluster_right_sizing_recommendations

  # ML Prediction Tables (3) 🤖
  - type: table
    name: cluster_capacity_recommendations
    comment: "ML: Optimal cluster capacity"
  - type: table
    name: cluster_rightsizing_recommendations
    comment: "ML: Right-sizing suggestions with savings"
  - type: table
    name: dbr_migration_risk_scores
    comment: "ML: DBR migration risk assessment"

  # Lakehouse Monitoring Tables 📊
  - type: table
    name: fact_node_timeline_profile_metrics
  - type: table
    name: fact_node_timeline_drift_metrics

  # Gold Tables
  - type: table
    name: fact_node_timeline
  - type: table
    name: dim_cluster
```

---

## 🔒 Security Agent: Security Auditor Genie Space

### Purpose
Enable security teams to explore data access and audit trails with ML-powered anomaly detection.

### Configuration

```yaml
name: "Security Auditor"
description: |
  Ask questions about data access patterns and security compliance.
  Now with ML-powered anomaly detection and risk scoring!

  Example questions:
  - "Who accessed this table?"
  - "Show me user activity for john@company.com"
  - "Which tables are most frequently accessed?"
  - "Who accessed sensitive data this week?"
  - "Show me bursty user activity"
  - "Which service accounts are most active?"
  - "Are there any security anomalies?" 🤖
  - "What's the risk score for this user?" 🤖
  - "Show me suspicious off-hours activity" 🤖

instructions: |
  You are a security and compliance auditor for Databricks,
  enhanced with ML-powered anomaly detection and risk scoring.

  ## Domain Knowledge

  ### Access Types
  - **READ**: SELECT queries, table scans
  - **WRITE**: INSERT, UPDATE, DELETE, MERGE
  - **DDL**: CREATE, ALTER, DROP operations

  ### Audit Concepts
  - **Lineage**: Tracks data flow from source to target
  - **Event**: A single access or modification action
  - **Entity**: The object being accessed (table, view, etc.)

  ### User Type Classification (from audit logs repo)
  - **HUMAN_USER**: Regular users with email addresses
  - **SERVICE_PRINCIPAL**: Apps and automation
  - **SYSTEM**: Databricks internal accounts
  - **PLATFORM**: Unity Catalog, Delta Sharing internal operations

  ### Compliance Patterns
  - PII tables: Usually contain "pii", "personal", "sensitive" in name
  - Sensitive access: Access to tagged sensitive data
  - Off-hours access: Access outside business hours (before 7am or after 7pm)
  - Activity burst: >3x average hourly activity indicates suspicious pattern

  ## ML Models Available 🤖
  
  ### Access Anomaly Detector (Isolation Forest)
  - Detects unusual access patterns
  - Query `access_anomaly_predictions` for detected anomalies
  - Fields: `user_id`, `anomaly_score`, `is_anomaly`, `reason`
  
  ### User Risk Scorer (XGBoost)
  - Scores user risk based on behavior
  - Query `user_risk_scores` for assessments
  - Risk Levels: LOW (0-25), MEDIUM (26-50), HIGH (51-75), CRITICAL (76-100)
  - Fields: `user_id`, `risk_score`, `risk_factors`
  
  ### Data Access Classifier (Random Forest)
  - Classifies access patterns (normal vs suspicious)
  - Query `access_classifications` for labels
  - Fields: `event_id`, `classification`, `confidence`
  
  ### Off-Hours Activity Predictor (LightGBM)
  - Predicts expected off-hours activity baseline
  - Query `off_hours_baseline_predictions` for comparison
  - Fields: `user_id`, `expected_off_hours_events`, `actual_events`, `deviation`

  ## Lakehouse Monitoring Metrics 📊
  
  Query `fact_audit_logs_profile_metrics` for:
  - `total_events`, `distinct_users`, `sensitive_action_count`, `failed_action_count`
  - `human_user_events`, `service_principal_events`, `system_account_events`
  - `human_off_hours_events`, `sensitive_rate`, `failure_rate`, `off_hours_rate`
  
  Query `fact_audit_logs_drift_metrics` for:
  - `event_volume_drift` (unusual activity spikes)
  - `sensitive_action_drift` (increased sensitive access)

  ## Query Guidance

  When users ask about:
  - "User activity" → Use get_user_activity_summary TVF
  - "Sensitive table access" → Use get_sensitive_table_access TVF
  - "User patterns" → Use get_user_activity_patterns TVF
  - "Service accounts" → Use get_service_account_audit TVF
  - "Security anomalies" → Query access_anomaly_predictions 🤖
  - "User risk" → Query user_risk_scores 🤖
  - "Suspicious activity" → Query access_classifications 🤖
  - General security metrics → Use security_events metric view

data_assets:
  # Metric Views (2)
  - type: metric_view
    name: security_events
    comment: "Security audit events with 20 measures"
  - type: metric_view
    name: governance_analytics
    comment: "Data lineage and governance"

  # TVFs (10)
  - type: function
    name: get_user_activity_summary
  - type: function
    name: get_sensitive_table_access
  - type: function
    name: get_failed_actions
  - type: function
    name: get_permission_changes
  - type: function
    name: get_off_hours_activity
  - type: function
    name: get_security_events_timeline
  - type: function
    name: get_ip_address_analysis
  - type: function
    name: get_table_access_audit
  - type: function
    name: get_user_activity_patterns
  - type: function
    name: get_service_account_audit

  # ML Prediction Tables (4) 🤖
  - type: table
    name: access_anomaly_predictions
    comment: "ML: Unusual access pattern detection"
  - type: table
    name: user_risk_scores
    comment: "ML: User risk assessment"
  - type: table
    name: access_classifications
    comment: "ML: Normal vs suspicious access"
  - type: table
    name: off_hours_baseline_predictions
    comment: "ML: Expected off-hours activity"

  # Lakehouse Monitoring Tables 📊
  - type: table
    name: fact_audit_logs_profile_metrics
  - type: table
    name: fact_audit_logs_drift_metrics

  # Gold Tables
  - type: table
    name: fact_audit_logs
  - type: table
    name: fact_table_lineage
```

---

## ✅ Quality Agent: Data Quality Monitor Genie Space

### Purpose
Enable data governance teams to explore data quality and lineage with ML-powered insights.

### Configuration

```yaml
name: "Data Quality Monitor"
description: |
  Ask questions about data quality, freshness, and table lineage.
  Now with ML-powered quality scoring and anomaly detection!

  Example questions:
  - "Which tables are stale?"
  - "What is our data quality score?"
  - "Show me inactive tables"
  - "Which pipelines have the most data dependencies?"
  - "What tables are orphaned?"
  - "Are there any data quality anomalies?" 🤖
  - "Which tables have degrading quality?" 🤖
  - "Predict data freshness issues" 🤖

instructions: |
  You are a data quality and governance assistant for Databricks,
  enhanced with ML-powered quality monitoring.

  ## Domain Knowledge

  ### Data Quality Concepts
  - **Freshness**: Time since last table update (stale if >24 hours)
  - **Completeness**: Percentage of non-null values
  - **Validity**: Percentage of values passing business rules
  - **Quality Score**: Combined metric (0-100) across dimensions

  ### Table Activity Status (from lineage patterns)
  - **ACTIVE**: Table accessed within threshold (default 14 days)
  - **INACTIVE**: Table not accessed recently but has historical activity
  - **ORPHANED**: Table with no detected reads or writes in period

  ### Lineage Concepts
  - **Upstream**: Tables that feed into a target (dependencies)
  - **Downstream**: Tables that consume from a source (dependents)
  - **Entity**: JOB, NOTEBOOK, or PIPELINE that accesses data
  - **Complexity Score**: Based on number of source/target tables

  ### Freshness Thresholds
  - **Fresh**: <24 hours since last update
  - **Stale**: >24 hours since last update
  - **Critical**: >72 hours since last update

  ## ML Models Available 🤖
  
  ### Data Quality Anomaly Detector (Isolation Forest)
  - Detects unusual quality patterns
  - Query `quality_anomaly_predictions` for detected issues
  - Fields: `table_name`, `anomaly_score`, `is_anomaly`, `dimension`
  
  ### Quality Trend Predictor (Prophet)
  - Predicts future quality score trends
  - Query `quality_trend_predictions` for forecasts
  - Fields: `table_name`, `predicted_quality_score`, `forecast_date`
  
  ### Freshness Alert Predictor (XGBoost)
  - Predicts tables likely to become stale
  - Query `freshness_alert_predictions` for at-risk tables
  - Fields: `table_name`, `staleness_probability`, `expected_stale_date`

  ## Lakehouse Monitoring Metrics 📊
  
  Query `fact_information_schema_table_storage_profile_metrics` for:
  - `total_tables`, `total_size_gb`, `total_rows`
  - `large_tables`, `empty_tables`, `unpartitioned_large_tables`
  - `avg_table_size_gb`, `empty_table_rate`
  
  Query `fact_table_lineage_profile_metrics` for:
  - `total_lineage_events`, `active_tables`, `read_events`, `write_events`
  - `unique_data_consumers`, `cross_catalog_events`
  - `data_sharing_rate`, `read_write_ratio`

  ## Query Guidance

  When users ask about:
  - "Stale tables" → Use get_table_freshness TVF
  - "Quality score" → Use get_data_quality_summary TVF
  - "Inactive tables" → Use get_table_activity_status TVF
  - "Pipeline lineage" → Use get_pipeline_data_lineage TVF
  - "Quality anomalies" → Query quality_anomaly_predictions 🤖
  - "Quality trends" → Query quality_trend_predictions 🤖
  - "Freshness alerts" → Query freshness_alert_predictions 🤖
  - General quality metrics → Use data_quality metric view

data_assets:
  # Metric Views (2)
  - type: metric_view
    name: data_quality
    comment: "Data quality monitoring with 15 measures"
  - type: metric_view
    name: ml_intelligence
    comment: "ML model inference monitoring"

  # TVFs (7)
  - type: function
    name: get_table_freshness
  - type: function
    name: get_job_data_quality_status
  - type: function
    name: get_data_freshness_by_domain
  - type: function
    name: get_data_quality_summary
  - type: function
    name: get_tables_failing_quality
  - type: function
    name: get_table_activity_status
  - type: function
    name: get_pipeline_data_lineage

  # ML Prediction Tables (3) 🤖
  - type: table
    name: quality_anomaly_predictions
    comment: "ML: Quality anomaly detection"
  - type: table
    name: quality_trend_predictions
    comment: "ML: Quality score forecasts"
  - type: table
    name: freshness_alert_predictions
    comment: "ML: Staleness probability"

  # Lakehouse Monitoring Tables 📊
  - type: table
    name: fact_information_schema_table_storage_profile_metrics
  - type: table
    name: fact_table_lineage_profile_metrics
  - type: table
    name: fact_table_lineage_drift_metrics

  # Gold Tables
  - type: table
    name: fact_table_lineage

benchmark_questions:
  - question: "Which tables are stale?"
    expected_result_type: "table"

  - question: "What is our overall data quality score?"
    expected_result_type: "single_value"

  - question: "Are there any quality anomalies?"
    expected_result_type: "table"
    note: "Should query quality_anomaly_predictions"
```

---

## 🌐 Unified: Databricks Health Monitor Genie Space

### Purpose
Unified Genie Space for comprehensive platform health monitoring with all ML models, metric views, and TVFs.

### Configuration

```yaml
name: "Databricks Health Monitor"
description: |
  Comprehensive platform health monitoring - ask about costs, jobs, 
  queries, clusters, security, and data quality all in one place.
  Enhanced with 25 ML models for predictions and anomaly detection!
  
  Example questions:
  - "What is our total spend this month?"
  - "How many job failures today?"
  - "Which warehouses have the longest queue times?"
  - "Show me underutilized clusters"
  - "Who are the most active users?"
  - "Are there any anomalies across the platform?" 🤖
  - "Show me all high-priority alerts" 🤖
  - "What's the overall platform health score?" 🤖

instructions: |
  You are a comprehensive health monitor for the Databricks platform,
  enhanced with 25 ML models across all domains.
  
  ## Domains
  
  ### 1. Cost & Billing (6 ML Models)
  - Total spend, cost trends, cost by workspace/owner/SKU
  - Week-over-week growth, cost anomalies
  - ML: Anomaly detection, forecasting, tag recommendations, migration advice
  
  ### 2. Job Reliability (5 ML Models)
  - Success rates, failure analysis, job durations
  - Repair costs, expensive jobs
  - ML: Failure prediction, retry success, pipeline health, self-healing
  
  ### 3. Query Performance (4 ML Models)
  - Query durations, queue times, slow queries
  - Warehouse utilization
  - ML: Query optimization, cache prediction, duration prediction
  
  ### 4. Cluster Optimization (3 ML Models)
  - CPU/memory utilization, underutilized clusters
  - Right-sizing recommendations
  - ML: Capacity planning, right-sizing, DBR migration risk
  
  ### 5. Security & Audit (4 ML Models)
  - User activity, table access, sensitive data
  - ML: Anomaly detection, risk scoring, access classification
  
  ### 6. Data Quality (3 ML Models)
  - Table freshness, quality scores, lineage
  - ML: Quality anomalies, trend prediction, freshness alerts
  
  ## Routing Logic
  
  - Cost questions → cost_analytics metric view + cost TVFs + cost ML predictions
  - Job questions → job_performance metric view + job TVFs + reliability ML predictions
  - Query questions → query_performance metric view + query TVFs + performance ML predictions
  - Cluster questions → cluster_utilization metric view + cluster TVFs + cluster ML predictions
  - Security questions → security_events metric view + security TVFs + security ML predictions
  - Quality questions → data_quality metric view + quality TVFs + quality ML predictions
  
  ## Lakehouse Monitoring
  
  All 8 monitors provide profile and drift metrics:
  - `*_profile_metrics`: Custom aggregated metrics
  - `*_drift_metrics`: Change detection over time
  
  When uncertain, start with the relevant metric view for aggregated answers,
  then drill down with TVFs or ML predictions for specifics.

data_assets:
  # All Metric Views (10)
  - type: metric_view
    name: cost_analytics
  - type: metric_view
    name: commit_tracking
  - type: metric_view
    name: job_performance
  - type: metric_view
    name: query_performance
  - type: metric_view
    name: cluster_utilization
  - type: metric_view
    name: cluster_efficiency
  - type: metric_view
    name: security_events
  - type: metric_view
    name: governance_analytics
  - type: metric_view
    name: data_quality
  - type: metric_view
    name: ml_intelligence

  # All TVFs (60)
  # Cost TVFs (15)
  - type: function
    name: get_top_cost_contributors
  - type: function
    name: get_cost_trend_by_sku
  - type: function
    name: get_cost_by_owner
  - type: function
    name: get_cost_by_tag
  - type: function
    name: get_untagged_resources
  - type: function
    name: get_tag_coverage
  - type: function
    name: get_cost_week_over_week
  - type: function
    name: get_cost_anomalies
  - type: function
    name: get_cost_forecast_summary
  - type: function
    name: get_cost_mtd_summary
  - type: function
    name: get_commit_vs_actual
  - type: function
    name: get_spend_by_custom_tags
  - type: function
    name: get_cost_growth_analysis
  - type: function
    name: get_cost_growth_by_period
  - type: function
    name: get_all_purpose_cluster_cost

  # Reliability TVFs (12)
  - type: function
    name: get_failed_jobs
  - type: function
    name: get_job_success_rate
  - type: function
    name: get_job_duration_percentiles
  - type: function
    name: get_job_failure_trends
  - type: function
    name: get_job_sla_compliance
  - type: function
    name: get_job_run_details
  - type: function
    name: get_most_expensive_jobs
  - type: function
    name: get_job_retry_analysis
  - type: function
    name: get_job_repair_costs
  - type: function
    name: get_job_spend_trend_analysis
  - type: function
    name: get_job_failure_costs
  - type: function
    name: get_job_run_duration_analysis

  # Performance TVFs (16)
  - type: function
    name: get_slow_queries
  - type: function
    name: get_warehouse_utilization
  - type: function
    name: get_query_efficiency
  - type: function
    name: get_high_spill_queries
  - type: function
    name: get_query_volume_trends
  - type: function
    name: get_user_query_summary
  - type: function
    name: get_query_latency_percentiles
  - type: function
    name: get_failed_queries
  - type: function
    name: get_query_efficiency_analysis
  - type: function
    name: get_job_outlier_runs
  - type: function
    name: get_cluster_utilization
  - type: function
    name: get_cluster_resource_metrics
  - type: function
    name: get_underutilized_clusters
  - type: function
    name: get_jobs_without_autoscaling
  - type: function
    name: get_jobs_on_legacy_dbr
  - type: function
    name: get_cluster_right_sizing_recommendations

  # Security TVFs (10)
  - type: function
    name: get_user_activity_summary
  - type: function
    name: get_sensitive_table_access
  - type: function
    name: get_failed_actions
  - type: function
    name: get_permission_changes
  - type: function
    name: get_off_hours_activity
  - type: function
    name: get_security_events_timeline
  - type: function
    name: get_ip_address_analysis
  - type: function
    name: get_table_access_audit
  - type: function
    name: get_user_activity_patterns
  - type: function
    name: get_service_account_audit

  # Quality TVFs (7)
  - type: function
    name: get_table_freshness
  - type: function
    name: get_job_data_quality_status
  - type: function
    name: get_data_freshness_by_domain
  - type: function
    name: get_data_quality_summary
  - type: function
    name: get_tables_failing_quality
  - type: function
    name: get_table_activity_status
  - type: function
    name: get_pipeline_data_lineage

  # All ML Prediction Tables (25 models)
  # Cost ML (6)
  - type: table
    name: cost_anomaly_predictions
  - type: table
    name: cost_forecast_predictions
  - type: table
    name: tag_recommendations
  - type: table
    name: user_cost_segments
  - type: table
    name: migration_recommendations
  - type: table
    name: budget_alert_predictions

  # Performance ML (7)
  - type: table
    name: job_duration_predictions
  - type: table
    name: query_optimization_classifications
  - type: table
    name: query_optimization_recommendations
  - type: table
    name: cache_hit_predictions
  - type: table
    name: cluster_capacity_recommendations
  - type: table
    name: cluster_rightsizing_recommendations
  - type: table
    name: dbr_migration_risk_scores

  # Reliability ML (5)
  - type: table
    name: job_failure_predictions
  - type: table
    name: retry_success_predictions
  - type: table
    name: pipeline_health_scores
  - type: table
    name: incident_impact_predictions
  - type: table
    name: self_healing_recommendations

  # Security ML (4)
  - type: table
    name: access_anomaly_predictions
  - type: table
    name: user_risk_scores
  - type: table
    name: access_classifications
  - type: table
    name: off_hours_baseline_predictions

  # Quality ML (3)
  - type: table
    name: quality_anomaly_predictions
  - type: table
    name: quality_trend_predictions
  - type: table
    name: freshness_alert_predictions

  # All Lakehouse Monitoring Tables (16)
  - type: table
    name: fact_usage_profile_metrics
  - type: table
    name: fact_usage_drift_metrics
  - type: table
    name: fact_job_run_timeline_profile_metrics
  - type: table
    name: fact_job_run_timeline_drift_metrics
  - type: table
    name: fact_query_history_profile_metrics
  - type: table
    name: fact_query_history_drift_metrics
  - type: table
    name: fact_node_timeline_profile_metrics
  - type: table
    name: fact_node_timeline_drift_metrics
  - type: table
    name: fact_audit_logs_profile_metrics
  - type: table
    name: fact_audit_logs_drift_metrics
  - type: table
    name: fact_information_schema_table_storage_profile_metrics
  - type: table
    name: fact_table_lineage_profile_metrics
  - type: table
    name: fact_table_lineage_drift_metrics
  - type: table
    name: cost_anomaly_predictions_profile_metrics
  - type: table
    name: cost_anomaly_predictions_drift_metrics
```

---

## Deployment Configuration

```yaml
resources:
  jobs:
    genie_space_setup_job:
      name: "[${bundle.target}] Health Monitor - Genie Space Setup"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - databricks-sdk>=0.20.0
      
      tasks:
        - task_key: create_cost_genie
          environment_key: default
          notebook_task:
            notebook_path: ../src/genie/create_cost_genie.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
        
        - task_key: create_job_genie
          depends_on: [create_cost_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/genie/create_job_genie.py
        
        - task_key: create_query_genie
          depends_on: [create_job_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/genie/create_query_genie.py
        
        - task_key: create_cluster_genie
          depends_on: [create_query_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/genie/create_cluster_genie.py
        
        - task_key: create_security_genie
          depends_on: [create_cluster_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/genie/create_security_genie.py
        
        - task_key: create_quality_genie
          depends_on: [create_security_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/genie/create_quality_genie.py
        
        - task_key: create_unified_genie
          depends_on: [create_quality_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/genie/create_unified_genie.py
      
      tags:
        project: health_monitor
        layer: gold
        artifact_type: genie_space
```

---

## Complete Asset Summary by Agent Domain

### 💰 Cost Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 15 | `get_top_cost_contributors`, `get_cost_anomalies`, `get_all_purpose_cluster_cost` |
| Metric Views | 2 | `cost_analytics`, `commit_tracking` |
| ML Models | 6 | Cost Anomaly, Forecaster, Budget Alert, Tag Recommender, User Behavior, Migration |
| Monitors | 1 | Cost Monitor (13 custom metrics) |

### ⚡ Performance Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 16 | `get_slow_queries`, `get_cluster_utilization`, `get_query_efficiency_analysis` |
| Metric Views | 3 | `query_performance`, `cluster_utilization`, `cluster_efficiency` |
| ML Models | 7 | Job Duration, Query Optimizer, Cache Hit, Capacity Planner, Right-Sizing, DBR Risk, Query Recommender |
| Monitors | 2 | Query Monitor (13 metrics), Cluster Monitor (11 metrics) |

### 🔄 Reliability Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 12 | `get_failed_jobs`, `get_job_success_rate`, `get_job_repair_costs` |
| Metric Views | 1 | `job_performance` |
| ML Models | 5 | Failure Predictor, Retry Success, Pipeline Health, Incident Impact, Self-Healing |
| Monitors | 1 | Job Monitor (14 custom metrics) |

### 🔒 Security Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 10 | `get_user_activity_summary`, `get_sensitive_table_access`, `get_off_hours_activity` |
| Metric Views | 2 | `security_events`, `governance_analytics` |
| ML Models | 4 | Access Anomaly, User Risk, Access Classifier, Off-Hours Predictor |
| Monitors | 1 | Security Monitor (14 custom metrics) |

### ✅ Quality Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 7 | `get_table_freshness`, `get_data_quality_summary`, `get_pipeline_data_lineage` |
| Metric Views | 2 | `data_quality`, `ml_intelligence` |
| ML Models | 3 | Quality Anomaly, Trend Predictor, Freshness Alert |
| Monitors | 2 | Quality Monitor (10 metrics), Governance Monitor (12 metrics) |

---

## Benchmark Testing Protocol

### Test Each Genie Space

1. **Basic Questions** - Simple aggregations
   - "What is the total?" 
   - "How many?"
   - "Show me the average"

2. **Filtered Questions** - Time and dimension filters
   - "Show me X for last 7 days"
   - "What is Y for workspace Z?"

3. **Comparative Questions** - Trends and comparisons
   - "Compare this week to last week"
   - "What is the growth rate?"

4. **ML-Powered Questions** 🤖 - Predictions and anomalies
   - "Are there any anomalies?"
   - "What's the forecast?"
   - "Show me predictions"
   - "What's the risk score?"

5. **Complex Questions** - Multi-step reasoning
   - "Which underutilized clusters have the highest cost?"
   - "Show me failed jobs with predicted retry success > 80%"

### Accuracy Targets

| Question Type | Target Accuracy |
|---------------|-----------------|
| Basic (COUNT, SUM, AVG) | 95% |
| Filtered | 90% |
| Comparative | 85% |
| ML-Powered 🤖 | 85% |
| Complex | 75% |

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Genie Spaces Created | 7 spaces (6 domain + 1 unified) |
| TVF Integration | 60 TVFs registered |
| Metric View Integration | 10 metric views registered |
| ML Model Integration | 25 models with prediction tables |
| Lakehouse Monitor Integration | 8 monitors with profile/drift tables |
| Benchmark Pass Rate | > 80% |
| User Adoption | 10+ active users in first month |

---

## Total Asset Count Summary

| Asset Category | Count |
|----------------|-------|
| **TVFs** | 60 |
| **Metric Views** | 10 |
| **ML Models** | 25 |
| **Lakehouse Monitors** | 8 |
| **Custom Metrics (in Monitors)** | 87 |
| **Genie Spaces** | 7 |
| **AI/BI Dashboards** | 11 |
| **Total Semantic Assets** | 208 |

---

## References

### Official Databricks Documentation
- [Databricks Genie](https://docs.databricks.com/genie)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Genie Instructions Best Practices](https://docs.databricks.com/genie/instructions)
- [Genie Conversation API](https://docs.databricks.com/aws/genie/set-up)

### Internal Inventory Documentation
- [TVF Inventory](../src/semantic/tvfs/TVF_INVENTORY.md) - 60 TVFs
- [Metric Views Inventory](../src/semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 10 Metric Views
- [ML Models Inventory](../src/ml/ML_MODELS_INVENTORY.md) - 25 ML Models
- [Lakehouse Monitoring Inventory](../docs/reference/LAKEHOUSE_MONITORING_INVENTORY.md) - 8 Monitors
- [Dashboard Inventory](../src/dashboards/DASHBOARD_INVENTORY.md) - 11 Dashboards

### Inspiration Repositories
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme) - Query patterns
- [System Tables Audit Logs](https://github.com/andyweaves/system-tables-audit-logs) - Security patterns
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor) - Job optimization patterns
