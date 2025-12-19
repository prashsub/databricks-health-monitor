# Phase 3 Addendum 3.6: Genie Spaces for Databricks Health Monitor

## Overview

**Status:** 🔧 Enhanced  
**Dependencies:** Gold Layer (Phase 2), TVFs (Phase 3.2), Metric Views (Phase 3.3)  
**Estimated Effort:** 1.5 weeks  
**Reference:** Cursor Rule 16 - Genie Space Patterns

---

## Purpose

Create Databricks Genie Spaces that enable:
- **Natural Language Queries** - Ask questions in plain English
- **Self-Service Analytics** - Non-technical users can explore data
- **Guided Analysis** - Pre-defined questions and context
- **Trusted Assets** - Curated TVFs and metric views for accurate answers

---

## Genie Spaces by Agent Domain

| Agent Domain | Genie Space | Key TVFs | Metric View | Target Users |
|--------------|-------------|----------|-------------|--------------|
| **💰 Cost** | Cost Intelligence | 6 TVFs | cost_analytics_metrics | FinOps, Finance |
| **🔒 Security** | Security Auditor | 4 TVFs | security_analytics_metrics | Security, Compliance |
| **⚡ Performance** | Query Performance Analyzer | 4 TVFs | query_analytics_metrics | DBAs |
| **⚡ Performance** | Cluster Optimizer | 2 TVFs | cluster_utilization_metrics | Platform Eng |
| **🔄 Reliability** | Job Health Monitor | 6 TVFs | job_performance_metrics | DevOps, Data Eng |
| **✅ Quality** | Data Quality Monitor (🆕) | 3 TVFs | data_quality_metrics | Data Governance |
| **Unified** | Databricks Health Monitor | 25 TVFs | All 8 metric views | Leadership |

---

## Genie Space Design Principles

### Best Practices

1. **Rich Context in Instructions** - Provide domain knowledge to the LLM
2. **Trusted Assets** - Register TVFs and metric views for reliable queries
3. **Benchmark Questions** - Test questions that validate Genie accuracy
4. **Synonyms Everywhere** - Multiple ways to ask the same thing
5. **Guardrails** - Guide users away from unsupported queries

---

## 💰 Cost Agent: Cost Intelligence Genie Space

### Purpose
Enable business users to explore Databricks costs through natural language.

### Configuration

```yaml
# Genie Space: Cost Intelligence
name: "Cost Intelligence"
description: |
  Ask questions about Databricks costs, spending trends, and cost optimization.
  
  Example questions:
  - "What is our total spend this month?"
  - "Which workspace costs the most?"
  - "Show me daily cost trend for the last 30 days"
  - "Who are the top 10 cost contributors?"
  - "What is our week-over-week cost growth?"

instructions: |
  You are a cost analytics assistant for Databricks platform usage.
  
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

  ## Query Guidance

  When users ask about:
  - "Top cost drivers" → Use get_top_cost_contributors TVF
  - "Cost trends" → Use get_cost_trend_by_sku TVF
  - "Cost by owner" → Use get_cost_by_owner TVF
  - "Week over week" or "cost growth" → Use get_cost_growth_by_period TVF (🆕)
  - "ALL_PURPOSE costs" or "cluster efficiency" → Use get_all_purpose_cluster_cost TVF (🆕)
  - General cost metrics → Use cost_analytics_metrics metric view

  ## Guardrails

  - Do NOT attempt to modify data; this is read-only
  - Do NOT access tables outside the Gold schema
  - If a question cannot be answered, explain what data is needed

data_assets:
  # Metric Views
  - type: metric_view
    name: cost_analytics_metrics
    catalog: ${catalog}
    schema: ${gold_schema}

  # TVFs (6 total)
  - type: function
    name: get_top_cost_contributors
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_cost_trend_by_sku
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_cost_by_owner
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_cost_week_over_week
    catalog: ${catalog}
    schema: ${gold_schema}

  # 🆕 New TVFs from dashboard/blog patterns
  - type: function
    name: get_cost_growth_by_period
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Period-over-period cost growth analysis with spike detection"

  - type: function
    name: get_all_purpose_cluster_cost
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Identifies costly ALL_PURPOSE usage that could be JOB clusters"
  
  # Tables (for ad-hoc queries)
  - type: table
    name: fact_usage
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: table
    name: dim_workspace
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: table
    name: dim_sku
    catalog: ${catalog}
    schema: ${gold_schema}

benchmark_questions:
  - question: "What is our total spend this month?"
    expected_sql: |
      SELECT SUM(usage_quantity * list_price) AS total_cost
      FROM fact_usage
      WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
    expected_result_type: "single_value"
  
  - question: "Show me the top 5 cost contributors"
    expected_sql: |
      SELECT * FROM TABLE(get_top_cost_contributors(
        DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        5
      ))
    expected_result_type: "table"
  
  - question: "What is the cost by SKU this month?"
    expected_sql: |
      SELECT sku_name, SUM(usage_quantity * list_price) AS total_cost
      FROM fact_usage
      WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
      GROUP BY sku_name
      ORDER BY total_cost DESC
    expected_result_type: "table"
```

---

## 🔄 Reliability Agent: Job Health Monitor Genie Space

### Purpose
Enable DevOps and data engineers to explore job reliability through natural language.

### Configuration

```yaml
name: "Job Health Monitor"
description: |
  Ask questions about job execution, failures, and reliability metrics.

  Example questions:
  - "What is our job success rate?"
  - "Show me failed jobs today"
  - "Which jobs have the most failures this week?"
  - "What are our most expensive jobs?"
  - "What is the P95 job duration?"
  - "Show me job outliers" (🆕)
  - "Which jobs have duration regressions?" (🆕)

instructions: |
  You are a job monitoring assistant for Databricks workflows.

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

  ### Outcome Categories (from dashboard patterns) (🆕)
  - **SUCCEEDED**: Completed successfully
  - **FAILED**: Execution error
  - **SKIPPED**: Task skipped (dependency not met)
  - **UPSTREAM_FAILED**: Previous task failed
  - **CANCELED**: User or system canceled

  ### Outlier Detection (from P90 deviation pattern) (🆕)
  - **DURATION_OUTLIER**: Run duration >1.5x the P90 baseline
  - **COST_OUTLIER**: Run cost >1.5x the P90 baseline
  - Jobs with frequent outliers may have data skew or resource contention

  ## Query Guidance

  When users ask about:
  - "Failed jobs" → Use get_failed_jobs TVF
  - "Success rate" → Use get_job_success_rate TVF
  - "Expensive jobs" → Use get_most_expensive_jobs TVF
  - "Duration percentiles" → Use get_job_duration_percentiles TVF
  - "Repair costs" → Use get_job_repair_costs TVF
  - "Outliers" or "duration regression" → Use get_job_outlier_runs TVF (🆕)
  - General job metrics → Use job_performance_metrics metric view

data_assets:
  - type: metric_view
    name: job_performance_metrics
    catalog: ${catalog}
    schema: ${gold_schema}

  # TVFs (6 total)
  - type: function
    name: get_failed_jobs
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_job_success_rate
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_most_expensive_jobs
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_job_duration_percentiles
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_job_repair_costs
    catalog: ${catalog}
    schema: ${gold_schema}

  # 🆕 New TVF from dashboard P90 outlier detection pattern
  - type: function
    name: get_job_outlier_runs
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Jobs with runs exceeding P90 baseline by configurable threshold"

  - type: table
    name: fact_job_run_timeline
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: table
    name: dim_job
    catalog: ${catalog}
    schema: ${gold_schema}

benchmark_questions:
  - question: "What is our job success rate this week?"
    expected_result_type: "single_value"
  
  - question: "Show me failed jobs today"
    expected_result_type: "table"
  
  - question: "Which jobs have the lowest success rate?"
    expected_result_type: "table"
```

---

## ⚡ Performance Agent: Query Performance Analyzer Genie Space

### Purpose
Enable DBAs and analysts to explore SQL Warehouse performance.

### Configuration

```yaml
name: "Query Performance Analyzer"
description: |
  Ask questions about SQL query performance and warehouse efficiency.

  Example questions:
  - "What is our average query duration?"
  - "Show me slow queries from today"
  - "Which warehouse has the highest queue time?"
  - "What is the P95 query duration?"
  - "How many queries ran this week?"
  - "Show me warehouse efficiency analysis" (🆕)
  - "Which queries have high spill rates?" (🆕)

instructions: |
  You are a query performance analyst for Databricks SQL Warehouses.

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

  ### Performance Flags (from DBSQL Warehouse Advisor Blog) (🆕)
  - **SLA breach**: Query duration > 60 seconds (critical threshold)
  - **Slow query**: > 5 minutes (300 seconds)
  - **High queue**: Queue time > 10% of total duration
  - **High spill**: Any spill indicates memory pressure
  - **Query complexity**: Long queries (>5000 chars) or >3 JOINs

  ### Efficiency Categories (🆕)
  - **EFFICIENT**: No spills, queue <10%, duration <60s
  - **HIGH_SPILL**: Spill bytes > 0
  - **HIGH_QUEUE**: Queue time > 10% of duration
  - **SLOW**: Duration > 60 seconds

  ## Query Guidance

  When users ask about:
  - "Slow queries" → Use get_slow_queries TVF
  - "Warehouse utilization" → Use get_warehouse_utilization TVF
  - "Query efficiency" or "efficiency analysis" → Use get_query_efficiency_analysis TVF (🆕)
  - "High spill queries" → Use get_high_spill_queries TVF
  - General query metrics → Use query_analytics_metrics metric view

data_assets:
  - type: metric_view
    name: query_analytics_metrics
    catalog: ${catalog}
    schema: ${gold_schema}

  # TVFs (4 total)
  - type: function
    name: get_slow_queries
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_warehouse_utilization
    catalog: ${catalog}
    schema: ${gold_schema}

  # 🆕 New TVFs from DBSQL Warehouse Advisor patterns
  - type: function
    name: get_query_efficiency_analysis
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Warehouse efficiency with spill rate, queue rate, P95/P99 metrics"

  - type: function
    name: get_high_spill_queries
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Queries with disk spills indicating memory pressure"

  - type: table
    name: fact_query_history
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: table
    name: dim_warehouse
    catalog: ${catalog}
    schema: ${gold_schema}
```

---

## ⚡ Performance Agent: Cluster Optimizer Genie Space

### Purpose
Enable infrastructure teams to explore cluster utilization for right-sizing.

### Configuration

```yaml
name: "Cluster Optimizer"
description: |
  Ask questions about cluster resource utilization and optimization.

  Example questions:
  - "Which clusters are underutilized?"
  - "What is the average CPU utilization?"
  - "Show me cluster costs by owner"
  - "Which clusters have low memory usage?"
  - "Show me right-sizing recommendations" (🆕)
  - "Which clusters are overprovisioned?" (🆕)

instructions: |
  You are a cluster optimization advisor for Databricks compute.

  ## Domain Knowledge

  ### Cluster Types
  - **All-Purpose**: Interactive notebooks and exploration (less cost-efficient)
  - **Job Cluster**: Ephemeral compute for workflow tasks (most cost-efficient)
  - **Instance Pool**: Pre-allocated instances for faster startup

  ### Utilization Metrics
  - **CPU Utilization**: cpu_user_percent + cpu_system_percent
  - **Memory Utilization**: mem_used_percent
  - **CPU Wait**: IO-bound indicator (high means storage bottleneck)

  ### Provisioning Status (from Workflow Advisor Repo) (🆕)
  - **UNDERPROVISIONED**: CPU saturation >90% or Memory >85% (scale up)
  - **OVERPROVISIONED**: CPU <20% AND Memory <30% (scale down)
  - **UNDERUTILIZED**: CPU <30% OR Memory <40% (potential savings)
  - **OPTIMAL**: CPU 30-80% and Memory 30-85% (well-sized)

  ### Optimization Thresholds
  - Underutilized: CPU < 30% average
  - Well-utilized: CPU 30-70% average
  - Over-utilized: CPU > 80% sustained

  ### Savings Opportunity (🆕)
  - **HIGH**: >50% wasted capacity, >$100/day potential savings
  - **MEDIUM**: 30-50% wasted capacity
  - **LOW**: 20-30% wasted capacity
  - **NONE**: Optimal utilization

  ## Query Guidance

  When users ask about:
  - "Cluster utilization" → Use get_cluster_utilization TVF
  - "Underutilized clusters" → Filter by avg_cpu < 30
  - "Right-sizing" or "recommendations" → Use get_cluster_right_sizing_recommendations TVF (🆕)
  - "Overprovisioned" or "underprovisioned" → Use get_cluster_right_sizing_recommendations TVF (🆕)
  - General metrics → Use cluster_utilization_metrics metric view

data_assets:
  - type: metric_view
    name: cluster_utilization_metrics
    catalog: ${catalog}
    schema: ${gold_schema}

  # TVFs (2 total)
  - type: function
    name: get_cluster_utilization
    catalog: ${catalog}
    schema: ${gold_schema}

  # 🆕 New TVF from Workflow Advisor patterns
  - type: function
    name: get_cluster_right_sizing_recommendations
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Right-sizing recommendations with under/over-provisioning detection"

  - type: table
    name: fact_node_timeline
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: table
    name: dim_cluster
    catalog: ${catalog}
    schema: ${gold_schema}
```

---

## 🔒 Security Agent: Security Auditor Genie Space

### Purpose
Enable security teams to explore data access and audit trails.

### Configuration

```yaml
name: "Security Auditor"
description: |
  Ask questions about data access patterns and security compliance.

  Example questions:
  - "Who accessed this table?"
  - "Show me user activity for john@company.com"
  - "Which tables are most frequently accessed?"
  - "Who accessed sensitive data this week?"
  - "Show me bursty user activity" (🆕)
  - "Which service accounts are most active?" (🆕)

instructions: |
  You are a security and compliance auditor for Databricks.

  ## Domain Knowledge

  ### Access Types
  - **READ**: SELECT queries, table scans
  - **WRITE**: INSERT, UPDATE, DELETE, MERGE
  - **DDL**: CREATE, ALTER, DROP operations

  ### Audit Concepts
  - **Lineage**: Tracks data flow from source to target
  - **Event**: A single access or modification action
  - **Entity**: The object being accessed (table, view, etc.)

  ### User Type Classification (from audit logs repo) (🆕)
  - **HUMAN_USER**: Regular users with email addresses (human@company.com)
  - **SERVICE_PRINCIPAL**: Apps and automation (spn@tenant.com, *.iam.gserviceaccount.com)
  - **SYSTEM**: Databricks internal accounts (System-*, DBX_*)
  - **PLATFORM**: Unity Catalog, Delta Sharing internal operations

  ### Compliance Patterns
  - PII tables: Usually contain "pii", "personal", "sensitive" in name
  - Sensitive access: Access to tagged sensitive data
  - Off-hours access: Access outside business hours (before 7am or after 7pm)
  - Activity burst: >3x average hourly activity indicates suspicious pattern

  ## Query Guidance

  When users ask about:
  - "User activity" → Use get_user_activity_summary TVF
  - "Sensitive table access" → Use get_sensitive_table_access TVF
  - "User patterns" or "bursty activity" → Use get_user_activity_patterns TVF (🆕)
  - "Service accounts" or "system activity" → Use get_service_account_audit TVF (🆕)
  - General security metrics → Use security_analytics_metrics metric view

data_assets:
  - type: metric_view
    name: security_analytics_metrics
    catalog: ${catalog}
    schema: ${gold_schema}

  # TVFs (4 total)
  - type: function
    name: get_user_activity_summary
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_sensitive_table_access
    catalog: ${catalog}
    schema: ${gold_schema}

  # 🆕 New TVFs from audit logs repo patterns
  - type: function
    name: get_user_activity_patterns
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Temporal patterns with burst detection and user type classification"

  - type: function
    name: get_service_account_audit
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Service principal and system account activity audit"

  - type: table
    name: fact_audit_logs
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: table
    name: fact_table_lineage
    catalog: ${catalog}
    schema: ${gold_schema}
```

---

## ✅ Quality Agent: Data Quality Monitor Genie Space (🆕)

### Purpose
Enable data governance teams to explore data quality and lineage through natural language.

### Configuration

```yaml
name: "Data Quality Monitor"
description: |
  Ask questions about data quality, freshness, and table lineage.

  Example questions:
  - "Which tables are stale?"
  - "What is our data quality score?"
  - "Show me inactive tables"
  - "Which pipelines have the most data dependencies?"
  - "What tables are orphaned?"

instructions: |
  You are a data quality and governance assistant for Databricks.

  ## Domain Knowledge

  ### Data Quality Concepts
  - **Freshness**: Time since last table update (stale if >24 hours)
  - **Completeness**: Percentage of non-null values
  - **Validity**: Percentage of values passing business rules
  - **Quality Score**: Combined metric (0-100) across dimensions

  ### Table Activity Status (from lineage patterns) (🆕)
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

  ## Query Guidance

  When users ask about:
  - "Stale tables" or "freshness" → Use get_table_freshness TVF
  - "Quality score" or "quality summary" → Use get_data_quality_summary TVF
  - "Inactive tables" or "orphaned" → Use get_table_activity_status TVF (🆕)
  - "Pipeline lineage" or "dependencies" → Use get_pipeline_data_lineage TVF (🆕)
  - General quality metrics → Use data_quality_metrics metric view

data_assets:
  - type: metric_view
    name: data_quality_metrics
    catalog: ${catalog}
    schema: ${gold_schema}

  # TVFs (3 total, 2 new)
  - type: function
    name: get_table_freshness
    catalog: ${catalog}
    schema: ${gold_schema}

  - type: function
    name: get_data_quality_summary
    catalog: ${catalog}
    schema: ${gold_schema}

  # 🆕 New TVFs from lineage patterns
  - type: function
    name: get_table_activity_status
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Active/inactive/orphaned table detection from lineage data"

  - type: function
    name: get_pipeline_data_lineage
    catalog: ${catalog}
    schema: ${gold_schema}
    comment: "Pipeline data dependencies with complexity scoring"

  - type: table
    name: fact_table_lineage
    catalog: ${catalog}
    schema: ${gold_schema}

benchmark_questions:
  - question: "Which tables are stale?"
    expected_result_type: "table"

  - question: "What is our overall data quality score?"
    expected_result_type: "single_value"

  - question: "Show me orphaned tables"
    expected_result_type: "table"
```

---

## Genie Space 7: Platform Health (Unified)

### Purpose
Unified Genie Space for comprehensive platform health monitoring.

### Configuration

```yaml
name: "Databricks Health Monitor"
description: |
  Comprehensive platform health monitoring - ask about costs, jobs, 
  queries, clusters, and security all in one place.
  
  Example questions:
  - "What is our total spend this month?"
  - "How many job failures today?"
  - "Which warehouses have the longest queue times?"
  - "Show me underutilized clusters"
  - "Who are the most active users?"

instructions: |
  You are a comprehensive health monitor for the Databricks platform.
  You can answer questions across multiple domains:
  
  ## Domains
  
  ### 1. Cost & Billing
  - Total spend, cost trends, cost by workspace/owner/SKU
  - Week-over-week growth, cost anomalies
  
  ### 2. Job Reliability
  - Success rates, failure analysis, job durations
  - Repair costs, expensive jobs
  
  ### 3. Query Performance
  - Query durations, queue times, slow queries
  - Warehouse utilization
  
  ### 4. Cluster Optimization
  - CPU/memory utilization, underutilized clusters
  - Right-sizing recommendations
  
  ### 5. Security & Audit
  - User activity, table access, sensitive data
  
  ## Routing Logic
  
  - Cost questions → Use cost_analytics_metrics or cost TVFs
  - Job questions → Use job_performance_metrics or job TVFs
  - Query questions → Use query_analytics_metrics or query TVFs
  - Cluster questions → Use cluster_utilization_metrics or cluster TVFs
  - Security questions → Use security_analytics_metrics or security TVFs
  
  When uncertain, start with the relevant metric view for aggregated answers.

data_assets:
  # All metric views
  - type: metric_view
    name: cost_analytics_metrics
  - type: metric_view
    name: job_performance_metrics
  - type: metric_view
    name: query_analytics_metrics
  - type: metric_view
    name: cluster_utilization_metrics
  - type: metric_view
    name: security_analytics_metrics
  
  # All TVFs (25 total)
  # Cost TVFs (6)
  - type: function
    name: get_top_cost_contributors
  - type: function
    name: get_cost_trend_by_sku
  - type: function
    name: get_cost_by_owner
  - type: function
    name: get_cost_week_over_week
  - type: function
    name: get_cost_growth_by_period
    comment: "🆕 Period-over-period cost analysis"
  - type: function
    name: get_all_purpose_cluster_cost
    comment: "🆕 ALL_PURPOSE inefficiency detection"

  # Job TVFs (6)
  - type: function
    name: get_failed_jobs
  - type: function
    name: get_job_success_rate
  - type: function
    name: get_most_expensive_jobs
  - type: function
    name: get_job_duration_percentiles
  - type: function
    name: get_job_repair_costs
  - type: function
    name: get_job_outlier_runs
    comment: "🆕 P90 outlier detection"

  # Query TVFs (4)
  - type: function
    name: get_slow_queries
  - type: function
    name: get_warehouse_utilization
  - type: function
    name: get_query_efficiency_analysis
    comment: "🆕 Warehouse efficiency metrics"
  - type: function
    name: get_high_spill_queries

  # Cluster TVFs (2)
  - type: function
    name: get_cluster_utilization
  - type: function
    name: get_cluster_right_sizing_recommendations
    comment: "🆕 Under/over-provisioning detection"

  # Security TVFs (4)
  - type: function
    name: get_user_activity_summary
  - type: function
    name: get_sensitive_table_access
  - type: function
    name: get_user_activity_patterns
    comment: "🆕 Temporal patterns and burst detection"
  - type: function
    name: get_service_account_audit
    comment: "🆕 Service principal activity audit"

  # Quality TVFs (3)
  - type: function
    name: get_table_activity_status
    comment: "🆕 Active/inactive/orphaned detection"
  - type: function
    name: get_pipeline_data_lineage
    comment: "🆕 Pipeline dependency tracking"
  - type: function
    name: get_table_freshness
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
            notebook_path: ../src/gold/genie/create_cost_genie.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
        
        - task_key: create_job_genie
          depends_on: [create_cost_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/genie/create_job_genie.py
        
        - task_key: create_query_genie
          depends_on: [create_job_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/genie/create_query_genie.py
        
        - task_key: create_cluster_genie
          depends_on: [create_query_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/genie/create_cluster_genie.py
        
        - task_key: create_security_genie
          depends_on: [create_cluster_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/genie/create_security_genie.py
        
        - task_key: create_unified_genie
          depends_on: [create_security_genie]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/genie/create_unified_genie.py
      
      tags:
        project: health_monitor
        layer: gold
        artifact_type: genie_space
```

---

## Genie Space Summary

| Genie Space | Domain | TVF Count | Metric View | Benchmark Questions | New TVFs |
|-------------|--------|-----------|-------------|---------------------|----------|
| Cost Intelligence | Billing | 6 | cost_analytics_metrics | 3 | +2 🆕 |
| Job Health Monitor | Reliability | 6 | job_performance_metrics | 3 | +1 🆕 |
| Query Performance | SQL | 4 | query_analytics_metrics | 2 | +2 🆕 |
| Cluster Optimizer | Compute | 2 | cluster_utilization_metrics | 2 | +1 🆕 |
| Security Auditor | Audit | 4 | security_analytics_metrics | 2 | +2 🆕 |
| Data Quality (🆕) | Governance | 3 | data_quality_metrics | 3 | +2 🆕 |
| Platform Health | Unified | 25 | All 8 | 5 | +11 🆕 |

### New TVFs Added (11 total)

| TVF | Domain | Source Pattern |
|-----|--------|----------------|
| `get_cost_growth_by_period` | Cost | Dashboard: period-over-period comparison |
| `get_all_purpose_cluster_cost` | Cost | Workflow Advisor Blog: ALL_PURPOSE inefficiency |
| `get_job_outlier_runs` | Reliability | Dashboard: P90 deviation detection |
| `get_query_efficiency_analysis` | Performance | DBSQL Warehouse Advisor: efficiency metrics |
| `get_high_spill_queries` | Performance | DBSQL Warehouse Advisor: memory pressure |
| `get_cluster_right_sizing_recommendations` | Compute | Workflow Advisor Repo: under/over-provisioning |
| `get_user_activity_patterns` | Security | Audit Logs Repo: temporal patterns, burst detection |
| `get_service_account_audit` | Security | Audit Logs Repo: system account filtering |
| `get_table_activity_status` | Quality | Dashboard: lineage-based activity detection |
| `get_pipeline_data_lineage` | Quality | Dashboard: pipeline dependency tracking |
| `get_table_freshness` | Quality | Standard: freshness monitoring |

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

4. **Complex Questions** - Multi-step reasoning
   - "Which underutilized clusters have the highest cost?"
   - "Show me failed jobs with repair costs over $100"

### Accuracy Targets

| Question Type | Target Accuracy |
|---------------|-----------------|
| Basic (COUNT, SUM, AVG) | 95% |
| Filtered | 90% |
| Comparative | 85% |
| Complex | 75% |

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Genie Spaces Created | 7 spaces (6 domain + 1 unified) |
| TVF Integration | 25 TVFs registered (11 new from patterns) |
| Metric View Integration | 8 metric views registered |
| Benchmark Pass Rate | > 80% |
| User Adoption | 10+ active users in first month |
| New Pattern Coverage | 100% of blog/GitHub patterns implemented |

---

## References

### Official Databricks Documentation
- [Databricks Genie](https://docs.databricks.com/genie)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Genie Instructions Best Practices](https://docs.databricks.com/genie/instructions)
- [Genie Conversation API](https://docs.databricks.com/aws/genie/set-up)

### Microsoft Learn System Tables Documentation
- [Jobs Cost Observability](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost)
- [Audit Logs Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)
- [Compute Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute)

### Inspiration Repositories
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme) - Query patterns for warehouse analysis
- [System Tables Audit Logs](https://github.com/andyweaves/system-tables-audit-logs) - Security audit patterns
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor) - Job optimization patterns

