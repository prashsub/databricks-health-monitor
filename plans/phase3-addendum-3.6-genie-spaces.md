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
| **💰 Cost** | Cost Intelligence | 4 TVFs | cost_analytics_metrics | FinOps, Finance |
| **🔒 Security** | Security Auditor | 2 TVFs | security_analytics_metrics | Security, Compliance |
| **⚡ Performance** | Query Performance Analyzer | 2 TVFs | query_analytics_metrics | DBAs |
| **⚡ Performance** | Cluster Optimizer | 1 TVF | cluster_utilization_metrics | Platform Eng |
| **🔄 Reliability** | Job Health Monitor | 5 TVFs | job_performance_metrics | DevOps, Data Eng |
| **Unified** | Databricks Health Monitor | 14 TVFs | All 5 metric views | Leadership |

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
  - JOBS_COMPUTE: Automated workflow compute
  - JOBS_LIGHT_COMPUTE: Low-cost job compute
  - SQL_COMPUTE: SQL Warehouse compute
  - ALL_PURPOSE_COMPUTE: Interactive notebook clusters
  - DLT: Delta Live Tables pipelines
  
  ## Query Guidance
  
  When users ask about:
  - "Top cost drivers" → Use get_top_cost_contributors TVF
  - "Cost trends" → Use get_cost_trend_by_sku TVF
  - "Cost by owner" → Use get_cost_by_owner TVF
  - "Week over week" → Use get_cost_week_over_week TVF
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
  
  # TVFs
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
  
  ## Query Guidance
  
  When users ask about:
  - "Failed jobs" → Use get_failed_jobs TVF
  - "Success rate" → Use get_job_success_rate TVF
  - "Expensive jobs" → Use get_most_expensive_jobs TVF
  - "Duration percentiles" → Use get_job_duration_percentiles TVF
  - "Repair costs" → Use get_job_repair_costs TVF
  - General job metrics → Use job_performance_metrics metric view

data_assets:
  - type: metric_view
    name: job_performance_metrics
    catalog: ${catalog}
    schema: ${gold_schema}
  
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

instructions: |
  You are a query performance analyst for Databricks SQL Warehouses.
  
  ## Domain Knowledge
  
  ### Warehouse Concepts
  - **SQL Warehouse**: Serverless compute for SQL queries
  - **Cluster**: Processing nodes within a warehouse
  - **Queue Time**: Time spent waiting for compute capacity
  - **Spill**: Data written to disk when memory is exceeded
  
  ### Performance Metrics
  - **Duration**: Total time from submission to completion
  - **Queue Time**: Time waiting at capacity
  - **Read Bytes**: Data scanned from storage
  - **Spill Bytes**: Data spilled to disk (indicates memory pressure)
  
  ### Query Types
  - SELECT: Read queries
  - INSERT/MERGE: Write queries
  - DDL: Schema modifications
  
  ### Performance Flags
  - Slow query: > 5 minutes (300 seconds)
  - High queue: Queue time > 50% of duration
  - High spill: Any spill indicates memory pressure
  
  ## Query Guidance
  
  When users ask about:
  - "Slow queries" → Use get_slow_queries TVF
  - "Warehouse utilization" → Use get_warehouse_utilization TVF
  - General query metrics → Use query_analytics_metrics metric view

data_assets:
  - type: metric_view
    name: query_analytics_metrics
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: function
    name: get_slow_queries
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: function
    name: get_warehouse_utilization
    catalog: ${catalog}
    schema: ${gold_schema}
  
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

instructions: |
  You are a cluster optimization advisor for Databricks compute.
  
  ## Domain Knowledge
  
  ### Cluster Types
  - **All-Purpose**: Interactive notebooks and exploration
  - **Job Cluster**: Ephemeral compute for workflow tasks
  - **Instance Pool**: Pre-allocated instances for faster startup
  
  ### Utilization Metrics
  - **CPU Utilization**: cpu_user_percent + cpu_system_percent
  - **Memory Utilization**: mem_used_percent
  - **CPU Wait**: IO-bound indicator (high means storage bottleneck)
  
  ### Optimization Thresholds
  - Underutilized: CPU < 30% average
  - Well-utilized: CPU 30-70% average
  - Over-utilized: CPU > 80% sustained
  
  ## Query Guidance
  
  When users ask about:
  - "Cluster utilization" → Use get_cluster_utilization TVF
  - "Underutilized clusters" → Filter by avg_cpu < 30
  - General metrics → Use cluster_utilization_metrics metric view

data_assets:
  - type: metric_view
    name: cluster_utilization_metrics
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: function
    name: get_cluster_utilization
    catalog: ${catalog}
    schema: ${gold_schema}
  
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
  
  ### Compliance Patterns
  - PII tables: Usually contain "pii", "personal", "sensitive" in name
  - Sensitive access: Access to tagged sensitive data
  - Off-hours access: Access outside business hours
  
  ## Query Guidance
  
  When users ask about:
  - "User activity" → Use get_user_activity_summary TVF
  - "Sensitive table access" → Use get_sensitive_table_access TVF
  - General security metrics → Use security_analytics_metrics metric view

data_assets:
  - type: metric_view
    name: security_analytics_metrics
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: function
    name: get_user_activity_summary
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: function
    name: get_sensitive_table_access
    catalog: ${catalog}
    schema: ${gold_schema}
  
  - type: table
    name: fact_table_lineage
    catalog: ${catalog}
    schema: ${gold_schema}
```

---

## Genie Space 6: Platform Health (Unified)

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
  
  # All TVFs
  - type: function
    name: get_top_cost_contributors
  - type: function
    name: get_cost_trend_by_sku
  - type: function
    name: get_cost_by_owner
  - type: function
    name: get_cost_week_over_week
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
    name: get_slow_queries
  - type: function
    name: get_warehouse_utilization
  - type: function
    name: get_cluster_utilization
  - type: function
    name: get_user_activity_summary
  - type: function
    name: get_sensitive_table_access
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

| Genie Space | Domain | TVF Count | Metric View | Benchmark Questions |
|-------------|--------|-----------|-------------|---------------------|
| Cost Intelligence | Billing | 4 | cost_analytics_metrics | 3 |
| Job Health Monitor | Reliability | 5 | job_performance_metrics | 3 |
| Query Performance | SQL | 2 | query_analytics_metrics | 2 |
| Cluster Optimizer | Compute | 1 | cluster_utilization_metrics | 2 |
| Security Auditor | Audit | 2 | security_analytics_metrics | 2 |
| Platform Health | Unified | 14 | All 5 | 5 |

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
| Genie Spaces Created | 6 spaces |
| TVF Integration | 100% of TVFs registered |
| Metric View Integration | 100% of metric views registered |
| Benchmark Pass Rate | > 80% |
| User Adoption | 10+ active users in first month |

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

