# Phase 3 Addendum 3.3: UC Metric Views for Databricks Health Monitor

## Overview

**Status:** 🔧 Enhanced  
**Dependencies:** Gold Layer (Phase 2)  
**Estimated Effort:** 1.5 weeks  
**Reference:** [Cursor Rule: Metric Views Patterns](../.cursor/rules/14-metric-views-patterns.mdc)

---

## Purpose

Create Unity Catalog Metric Views that provide:
- **Semantic layer** for natural language queries via Genie
- **Standardized KPIs** for AI/BI dashboards
- **Self-service analytics** with pre-defined dimensions and measures
- **Governance** through centralized business logic

---

## Metric Views by Agent Domain

| Agent Domain | Metric View | Source Gold Table | Key Measures |
|--------------|-------------|-------------------|--------------|
| **💰 Cost** | cost_analytics_metrics | fact_usage | total_cost, avg_daily_cost, **tagged_cost**, **untagged_cost**, **tag_coverage_pct** |
| **💰 Cost** | **commit_tracking_metrics** (NEW) | fact_usage + commit_configurations | monthly_spend, annual_commit, monthly_target, ytd_spend |
| **🔒 Security** | security_analytics_metrics | fact_table_lineage | total_events, read_events, unique_users |
| **⚡ Performance** | query_analytics_metrics | fact_query_history | avg_duration, p95_duration, queue_time |
| **⚡ Performance** | cluster_utilization_metrics | fact_node_timeline | avg_cpu_util, avg_mem_util, node_hours |
| **🔄 Reliability** | job_performance_metrics | fact_job_run_timeline | success_rate, failure_rate, avg_duration |
| **✅ Quality** | data_quality_metrics | fact_data_quality_monitoring_table_results | quality_score, rules_passed |

### Key Enhancements for FinOps

1. **Tag-Based Dimensions** - Filter by team, project, cost_center, env tags
2. **Tag Coverage Measures** - Track tagged vs untagged cost
3. **Commit Tracking** - Compare actual spend vs required run rate

---

## Metric View Design Principles

### Version 1.1 Compliance

All metric views must comply with UC Metric View Specification v1.1:

```yaml
# Required fields
version: "1.1"
source: ${catalog}.${gold_schema}.fact_table_name

# Joins must have: name, source, 'on' (quoted)
joins:
  - name: dim_alias
    source: ${catalog}.${gold_schema}.dim_table
    'on': source.fk = dim_alias.pk AND dim_alias.is_current = true

# Column references use prefixes
dimensions:
  - name: col_name
    expr: source.column  # Main table prefix
  - name: dim_col
    expr: dim_alias.column  # Join alias prefix

# Measures must have format and synonyms
measures:
  - name: total_cost
    expr: SUM(source.cost)
    format:
      type: currency
      currency_code: USD
```

### ⚠️ v1.1 Limitations

| Unsupported Feature | Alternative |
|---------------------|-------------|
| `time_dimension` field | Use regular dimension |
| `window_measures` | Pre-calculate in Gold layer or SQL |
| `join_type` | Defaults to LEFT OUTER |
| `table` in joins | Use `source` instead |

---

## Metric Views Catalog

### 💰 Cost Agent: cost_analytics_metrics

```yaml
version: "1.1"

- name: cost_analytics_metrics
  comment: |
    Comprehensive cost analytics metrics for Databricks billing and usage analysis.
    Optimized for natural language queries via Genie.
    Use for: Cost trends, chargeback reporting, budget monitoring, SKU analysis.
    Example queries: "What is our total spend this month?", "Show cost by workspace",
    "Which SKU costs the most?", "Daily cost trend for last 30 days"
  
  source: ${catalog}.${gold_schema}.fact_usage
  
  joins:
    - name: dim_workspace
      source: ${catalog}.${gold_schema}.dim_workspace
      'on': source.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
    
    - name: dim_sku
      source: ${catalog}.${gold_schema}.dim_sku
      'on': source.sku_name = dim_sku.sku_name
    
    - name: dim_date
      source: ${catalog}.${gold_schema}.dim_date
      'on': source.usage_date = dim_date.date
  
  dimensions:
    # Primary dimensions
    - name: usage_date
      expr: source.usage_date
      comment: Date of usage record
      display_name: Usage Date
      synonyms:
        - date
        - day
        - billing date
    
    - name: workspace_id
      expr: source.workspace_id
      comment: Databricks workspace identifier
      display_name: Workspace ID
      synonyms:
        - workspace
        - environment
    
    - name: workspace_name
      expr: dim_workspace.workspace_name
      comment: Workspace display name
      display_name: Workspace Name
      synonyms:
        - workspace
        - env name
    
    - name: sku_name
      expr: source.sku_name
      comment: Product SKU category (JOBS_COMPUTE, SQL, etc.)
      display_name: SKU Name
      synonyms:
        - sku
        - product
        - service
        - product type
    
    - name: sku_description
      expr: dim_sku.sku_description
      comment: Human-readable SKU description
      display_name: SKU Description
      synonyms:
        - product description
        - sku desc
    
    - name: billing_category
      expr: dim_sku.billing_category
      comment: High-level billing category
      display_name: Billing Category
      synonyms:
        - category
        - cost category
    
    # Owner dimensions
    - name: run_as
      expr: source.run_as
      comment: User or service principal who ran the workload
      display_name: Run As User
      synonyms:
        - owner
        - user
        - run by
        - executed by
    
    # Time dimensions
    - name: year
      expr: dim_date.year
      comment: Calendar year
      display_name: Year
      synonyms:
        - calendar year
    
    - name: quarter
      expr: dim_date.quarter
      comment: Calendar quarter (1-4)
      display_name: Quarter
      synonyms:
        - q
        - qtr
    
    - name: month_name
      expr: dim_date.month_name
      comment: Month name
      display_name: Month
      synonyms:
        - month
    
    - name: week_of_year
      expr: dim_date.week_of_year
      comment: Week number in year
      display_name: Week
      synonyms:
        - week
        - week number
    
    - name: day_of_week
      expr: dim_date.day_of_week_name
      comment: Day of week name
      display_name: Day of Week
      synonyms:
        - weekday
        - day name
    
    # Tag dimensions for cost attribution (NEW)
    # Reference: https://docs.databricks.com/aws/en/admin/system-tables/billing
    - name: is_tagged
      expr: CASE WHEN source.custom_tags IS NOT NULL AND cardinality(source.custom_tags) > 0 THEN 'Tagged' ELSE 'Untagged' END
      comment: Whether the usage record has custom tags for cost attribution
      display_name: Tag Status
      synonyms:
        - tagged
        - has tags
        - tag coverage
    
    - name: team_tag
      expr: COALESCE(source.custom_tags['team'], 'Unassigned')
      comment: Team tag value for chargeback reporting
      display_name: Team
      synonyms:
        - team
        - department
        - business unit
        - team tag
    
    - name: project_tag
      expr: COALESCE(source.custom_tags['project'], 'Unassigned')
      comment: Project tag value for cost allocation
      display_name: Project
      synonyms:
        - project
        - initiative
        - project tag
    
    - name: cost_center_tag
      expr: COALESCE(source.custom_tags['cost_center'], 'Unassigned')
      comment: Cost center tag for financial reporting
      display_name: Cost Center
      synonyms:
        - cost center
        - cc
        - cost_center
    
    - name: env_tag
      expr: COALESCE(source.custom_tags['env'], source.custom_tags['environment'], 'Unknown')
      comment: Environment tag (dev, staging, prod)
      display_name: Environment
      synonyms:
        - environment
        - env
        - stage
  
  measures:
    - name: total_dbu
      expr: SUM(source.usage_quantity)
      comment: Total Databricks Units consumed
      display_name: Total DBUs
      format:
        type: number
        decimal_places:
          type: exact
          places: 2
        abbreviation: compact
      synonyms:
        - dbu
        - dbus
        - units
        - usage
    
    - name: total_cost
      expr: SUM(source.usage_quantity * COALESCE(source.list_price, 0))
      comment: Total estimated cost in USD based on list price
      display_name: Total Cost
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
        abbreviation: compact
      synonyms:
        - cost
        - spend
        - spending
        - dollars
        - amount
    
    - name: avg_daily_cost
      expr: AVG(source.usage_quantity * COALESCE(source.list_price, 0))
      comment: Average daily cost
      display_name: Avg Daily Cost
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
      synonyms:
        - daily average
        - average cost
        - avg cost
    
    - name: active_workspaces
      expr: COUNT(DISTINCT source.workspace_id)
      comment: Number of workspaces with usage
      display_name: Active Workspaces
      format:
        type: number
        decimal_places:
          type: exact
          places: 0
      synonyms:
        - workspace count
        - workspaces
    
    - name: active_users
      expr: COUNT(DISTINCT source.run_as)
      comment: Number of unique users/principals with usage
      display_name: Active Users
      format:
        type: number
        decimal_places:
          type: exact
          places: 0
      synonyms:
        - user count
        - users
        - principals
    
    - name: usage_days
      expr: COUNT(DISTINCT source.usage_date)
      comment: Number of days with usage
      display_name: Usage Days
      format:
        type: number
      synonyms:
        - days
        - active days
    
    # Tag Coverage Measures (NEW)
    # Support fine-grained cost attribution via custom_tags
    - name: tagged_cost
      expr: SUM(CASE WHEN source.custom_tags IS NOT NULL AND cardinality(source.custom_tags) > 0 THEN source.usage_quantity * COALESCE(source.list_price, 0) ELSE 0 END)
      comment: Cost from resources that have custom tags assigned
      display_name: Tagged Cost
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
        abbreviation: compact
      synonyms:
        - tagged spend
        - attributed cost
    
    - name: untagged_cost
      expr: SUM(CASE WHEN source.custom_tags IS NULL OR cardinality(source.custom_tags) = 0 THEN source.usage_quantity * COALESCE(source.list_price, 0) ELSE 0 END)
      comment: Cost from resources without custom tags - needs tagging for proper attribution
      display_name: Untagged Cost
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
        abbreviation: compact
      synonyms:
        - unattributed cost
        - cost needing tags
    
    - name: tag_coverage_pct
      expr: SUM(CASE WHEN source.custom_tags IS NOT NULL AND cardinality(source.custom_tags) > 0 THEN source.usage_quantity * COALESCE(source.list_price, 0) ELSE 0 END) / NULLIF(SUM(source.usage_quantity * COALESCE(source.list_price, 0)), 0) * 100
      comment: Percentage of cost that has custom tags for attribution
      display_name: Tag Coverage %
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - tag coverage
        - tagging rate
        - attribution rate
```

---

### 💰 Cost Agent: commit_tracking_metrics (NEW)

This metric view supports tracking actual spend vs Databricks commit amount with forecasting.

```yaml
version: "1.1"

- name: commit_tracking_metrics
  comment: |
    Tracks actual spend against Databricks commit amount for FinOps planning.
    Provides required run rate vs actual run rate analysis with variance tracking.
    Use for: Commit planning, budget forecasting, variance analysis, undershoot/overshoot detection.
    Example queries: "Are we on track to meet our commit?", "What is our required run rate?",
    "Will we undershoot our Databricks commitment?", "Show commit variance by month"
  
  source: ${catalog}.${gold_schema}.fact_usage
  
  joins:
    - name: dim_date
      source: ${catalog}.${gold_schema}.dim_date
      'on': source.usage_date = dim_date.date
    
    - name: commit_config
      source: ${catalog}.${gold_schema}.commit_configurations
      'on': dim_date.year = commit_config.commit_year
  
  dimensions:
    - name: usage_month
      expr: DATE_TRUNC('month', source.usage_date)
      comment: Month of usage for monthly tracking
      display_name: Month
      synonyms:
        - month
        - billing month
    
    - name: commit_year
      expr: commit_config.commit_year
      comment: Year of the commit being tracked
      display_name: Commit Year
      synonyms:
        - year
        - fiscal year
  
  measures:
    - name: monthly_spend
      expr: SUM(source.usage_quantity * COALESCE(source.list_price, 0))
      comment: Total monthly spend in USD
      display_name: Monthly Spend
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
        abbreviation: compact
      synonyms:
        - spend
        - monthly cost
    
    - name: annual_commit
      expr: MAX(commit_config.annual_commit_amount)
      comment: Annual commit amount from configuration
      display_name: Annual Commit
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 0
        abbreviation: compact
      synonyms:
        - commit
        - commitment
        - committed amount
    
    - name: monthly_target
      expr: MAX(commit_config.annual_commit_amount) / 12
      comment: Required monthly spend to meet commit (commit / 12)
      display_name: Monthly Target
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
      synonyms:
        - target
        - required rate
        - run rate target
    
    - name: ytd_spend
      expr: SUM(SUM(source.usage_quantity * COALESCE(source.list_price, 0))) OVER (ORDER BY DATE_TRUNC('month', source.usage_date))
      comment: Year-to-date cumulative spend
      display_name: YTD Spend
      format:
        type: currency
        currency_code: USD
        abbreviation: compact
      synonyms:
        - cumulative spend
        - year to date
```

---

### 🔄 Reliability Agent: job_performance_metrics

```yaml
version: "1.1"

- name: job_performance_metrics
  comment: |
    Job execution performance metrics for reliability and efficiency analysis.
    Optimized for Genie natural language queries.
    Use for: Job success rates, failure analysis, runtime tracking, SLA monitoring.
    Example queries: "What is our job success rate?", "Show failed jobs today",
    "Which jobs are slowest?", "Job failure rate by workspace"
  
  source: ${catalog}.${gold_schema}.fact_job_run_timeline
  
  joins:
    - name: dim_job
      source: ${catalog}.${gold_schema}.dim_job
      'on': source.job_id = dim_job.job_id AND dim_job.is_current = true
    
    - name: dim_workspace
      source: ${catalog}.${gold_schema}.dim_workspace
      'on': source.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
    
    - name: dim_cluster
      source: ${catalog}.${gold_schema}.dim_cluster
      'on': source.cluster_id = dim_cluster.cluster_id AND dim_cluster.is_current = true
    
    - name: dim_date
      source: ${catalog}.${gold_schema}.dim_date
      'on': DATE(source.period_start_time) = dim_date.date
  
  dimensions:
    - name: job_id
      expr: source.job_id
      comment: Unique job identifier
      display_name: Job ID
      synonyms:
        - job
    
    - name: job_name
      expr: dim_job.name
      comment: Human-readable job name
      display_name: Job Name
      synonyms:
        - job
        - workflow
        - workflow name
    
    - name: result_state
      expr: source.result_state
      comment: Job result (SUCCEEDED, FAILED, ERROR, TIMED_OUT)
      display_name: Result State
      synonyms:
        - status
        - result
        - outcome
    
    - name: termination_code
      expr: source.termination_code
      comment: Detailed termination reason
      display_name: Termination Code
      synonyms:
        - error code
        - failure reason
    
    - name: run_as
      expr: source.run_as
      comment: User or service principal running the job
      display_name: Run As User
      synonyms:
        - owner
        - user
        - run by
    
    - name: workspace_name
      expr: dim_workspace.workspace_name
      comment: Workspace where job ran
      display_name: Workspace
      synonyms:
        - workspace
        - environment
    
    - name: cluster_name
      expr: dim_cluster.cluster_name
      comment: Cluster used for job execution
      display_name: Cluster Name
      synonyms:
        - cluster
    
    - name: run_date
      expr: DATE(source.period_start_time)
      comment: Date of job run
      display_name: Run Date
      synonyms:
        - date
        - execution date
    
    - name: year
      expr: dim_date.year
      comment: Calendar year of run
      display_name: Year
      synonyms:
        - year
    
    - name: month_name
      expr: dim_date.month_name
      comment: Month of run
      display_name: Month
      synonyms:
        - month
    
    - name: day_of_week
      expr: dim_date.day_of_week_name
      comment: Day of week of run
      display_name: Day of Week
      synonyms:
        - weekday
  
  measures:
    - name: total_runs
      expr: COUNT(*)
      comment: Total number of job runs
      display_name: Total Runs
      format:
        type: number
        abbreviation: compact
      synonyms:
        - runs
        - executions
        - run count
    
    - name: successful_runs
      expr: SUM(CASE WHEN source.result_state = 'SUCCEEDED' THEN 1 ELSE 0 END)
      comment: Number of successful job runs
      display_name: Successful Runs
      format:
        type: number
        abbreviation: compact
      synonyms:
        - successes
        - passed
    
    - name: failed_runs
      expr: SUM(CASE WHEN source.result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END)
      comment: Number of failed job runs
      display_name: Failed Runs
      format:
        type: number
        abbreviation: compact
      synonyms:
        - failures
        - errors
        - failed
    
    - name: success_rate
      expr: (SUM(CASE WHEN source.result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100
      comment: Percentage of successful runs
      display_name: Success Rate
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - success percentage
        - pass rate
        - reliability
    
    - name: failure_rate
      expr: (SUM(CASE WHEN source.result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100
      comment: Percentage of failed runs
      display_name: Failure Rate
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - failure percentage
        - error rate
    
    - name: avg_duration_minutes
      expr: AVG(TIMESTAMPDIFF(MINUTE, source.period_start_time, source.period_end_time))
      comment: Average job run duration in minutes
      display_name: Avg Duration (min)
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - average runtime
        - avg runtime
        - typical duration
    
    - name: total_runtime_hours
      expr: SUM(TIMESTAMPDIFF(MINUTE, source.period_start_time, source.period_end_time)) / 60
      comment: Total cumulative runtime in hours
      display_name: Total Runtime (hrs)
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - total hours
        - cumulative runtime
    
    - name: unique_jobs
      expr: COUNT(DISTINCT source.job_id)
      comment: Number of unique jobs run
      display_name: Unique Jobs
      format:
        type: number
      synonyms:
        - job count
        - distinct jobs
```

---

### ⚡ Performance Agent: query_analytics_metrics

```yaml
version: "1.1"

- name: query_analytics_metrics
  comment: |
    SQL Warehouse query performance and efficiency metrics.
    Optimized for Genie natural language queries.
    Use for: Query performance tuning, warehouse optimization, capacity planning.
    Example queries: "Average query duration", "Slowest queries today",
    "Warehouse query count", "Query efficiency by user"
  
  source: ${catalog}.${gold_schema}.fact_query_history
  
  joins:
    - name: dim_warehouse
      source: ${catalog}.${gold_schema}.dim_warehouse
      'on': source.warehouse_id = dim_warehouse.warehouse_id AND dim_warehouse.is_current = true
    
    - name: dim_date
      source: ${catalog}.${gold_schema}.dim_date
      'on': DATE(source.start_time) = dim_date.date
  
  dimensions:
    - name: warehouse_id
      expr: source.warehouse_id
      comment: SQL Warehouse identifier
      display_name: Warehouse ID
      synonyms:
        - warehouse
    
    - name: warehouse_name
      expr: dim_warehouse.warehouse_name
      comment: SQL Warehouse name
      display_name: Warehouse Name
      synonyms:
        - warehouse
        - sql warehouse
    
    - name: warehouse_size
      expr: dim_warehouse.warehouse_size
      comment: Warehouse T-shirt size (XS to 4XL)
      display_name: Warehouse Size
      synonyms:
        - size
        - t-shirt size
    
    - name: statement_type
      expr: source.statement_type
      comment: Query type (SELECT, INSERT, MERGE, etc.)
      display_name: Statement Type
      synonyms:
        - query type
        - statement
    
    - name: execution_status
      expr: source.execution_status
      comment: Execution result status
      display_name: Execution Status
      synonyms:
        - status
        - result
    
    - name: executed_by
      expr: source.executed_by
      comment: User who executed the query
      display_name: Executed By
      synonyms:
        - user
        - query user
    
    - name: query_date
      expr: DATE(source.start_time)
      comment: Date query was executed
      display_name: Query Date
      synonyms:
        - date
    
    - name: year
      expr: dim_date.year
      comment: Year of query
      display_name: Year
    
    - name: month_name
      expr: dim_date.month_name
      comment: Month of query
      display_name: Month
    
    - name: hour_of_day
      expr: HOUR(source.start_time)
      comment: Hour query was executed (0-23)
      display_name: Hour of Day
      synonyms:
        - hour
  
  measures:
    - name: total_queries
      expr: COUNT(*)
      comment: Total number of queries executed
      display_name: Total Queries
      format:
        type: number
        abbreviation: compact
      synonyms:
        - query count
        - queries
    
    - name: avg_duration_seconds
      expr: AVG(source.total_duration_ms / 1000)
      comment: Average query duration in seconds
      display_name: Avg Duration (sec)
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - average duration
        - avg runtime
        - typical query time
    
    - name: p50_duration_seconds
      expr: PERCENTILE(source.total_duration_ms / 1000, 0.5)
      comment: Median query duration in seconds
      display_name: Median Duration (sec)
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - median
        - p50
    
    - name: p95_duration_seconds
      expr: PERCENTILE(source.total_duration_ms / 1000, 0.95)
      comment: 95th percentile query duration
      display_name: P95 Duration (sec)
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - p95
        - 95th percentile
    
    - name: avg_queue_time_seconds
      expr: AVG(source.waiting_at_capacity_duration_ms / 1000)
      comment: Average time queries waited in queue
      display_name: Avg Queue Time (sec)
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - queue time
        - wait time
    
    - name: total_bytes_read_tb
      expr: SUM(source.read_bytes) / (1024*1024*1024*1024)
      comment: Total data read in terabytes
      display_name: Data Read (TB)
      format:
        type: number
        decimal_places:
          type: exact
          places: 2
      synonyms:
        - bytes read
        - data scanned
    
    - name: avg_bytes_spilled_gb
      expr: AVG((COALESCE(source.spill_local_bytes, 0) + COALESCE(source.spill_remote_bytes, 0)) / (1024*1024*1024))
      comment: Average data spilled to disk in GB
      display_name: Avg Spill (GB)
      format:
        type: number
        decimal_places:
          type: exact
          places: 2
      synonyms:
        - spill
        - disk spill
    
    - name: unique_users
      expr: COUNT(DISTINCT source.executed_by)
      comment: Number of unique users executing queries
      display_name: Unique Users
      format:
        type: number
      synonyms:
        - user count
        - users
```

---

### ⚡ Performance Agent: cluster_utilization_metrics

```yaml
version: "1.1"

- name: cluster_utilization_metrics
  comment: |
    Cluster resource utilization metrics for capacity planning and optimization.
    Optimized for Genie natural language queries.
    Use for: Identifying underutilized clusters, right-sizing, cost optimization.
    Example queries: "Cluster CPU utilization", "Underutilized clusters",
    "Memory usage by cluster", "Most expensive clusters"
  
  source: ${catalog}.${gold_schema}.fact_node_timeline
  
  joins:
    - name: dim_cluster
      source: ${catalog}.${gold_schema}.dim_cluster
      'on': source.cluster_id = dim_cluster.cluster_id AND dim_cluster.is_current = true
    
    - name: dim_workspace
      source: ${catalog}.${gold_schema}.dim_workspace
      'on': dim_cluster.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
  
  dimensions:
    - name: cluster_id
      expr: source.cluster_id
      comment: Cluster identifier
      display_name: Cluster ID
    
    - name: cluster_name
      expr: dim_cluster.cluster_name
      comment: Cluster name
      display_name: Cluster Name
      synonyms:
        - cluster
    
    - name: cluster_source
      expr: dim_cluster.cluster_source
      comment: Cluster type (JOB, ALL_PURPOSE)
      display_name: Cluster Type
      synonyms:
        - type
        - cluster type
    
    - name: owned_by
      expr: dim_cluster.owned_by
      comment: Cluster owner
      display_name: Owner
      synonyms:
        - owner
        - created by
    
    - name: workspace_name
      expr: dim_workspace.workspace_name
      comment: Workspace name
      display_name: Workspace
    
    - name: node_type
      expr: source.node_type
      comment: Instance type of the node
      display_name: Node Type
      synonyms:
        - instance type
    
    - name: utilization_date
      expr: DATE(source.start_time)
      comment: Date of utilization measurement
      display_name: Date
  
  measures:
    - name: avg_cpu_utilization
      expr: AVG(source.cpu_user_percent + source.cpu_system_percent)
      comment: Average CPU utilization percentage
      display_name: Avg CPU Utilization
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - cpu
        - cpu usage
        - cpu percent
    
    - name: peak_cpu_utilization
      expr: MAX(source.cpu_user_percent + source.cpu_system_percent)
      comment: Peak CPU utilization
      display_name: Peak CPU
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - max cpu
    
    - name: avg_memory_utilization
      expr: AVG(source.mem_used_percent)
      comment: Average memory utilization percentage
      display_name: Avg Memory Utilization
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - memory
        - mem
        - ram
    
    - name: peak_memory_utilization
      expr: MAX(source.mem_used_percent)
      comment: Peak memory utilization
      display_name: Peak Memory
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - max memory
    
    - name: avg_cpu_wait
      expr: AVG(source.cpu_wait_percent)
      comment: Average CPU wait (IO bound indicator)
      display_name: Avg CPU Wait
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - cpu wait
        - io wait
    
    - name: total_node_hours
      expr: SUM(TIMESTAMPDIFF(MINUTE, source.start_time, source.end_time) / 60)
      comment: Total node runtime hours
      display_name: Node Hours
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms:
        - hours
        - runtime
    
    - name: unique_nodes
      expr: COUNT(DISTINCT source.instance_id)
      comment: Number of unique nodes
      display_name: Node Count
      format:
        type: number
      synonyms:
        - nodes
        - instances
```

---

### 🔒 Security Agent: security_analytics_metrics

```yaml
version: "1.1"

- name: security_analytics_metrics
  comment: |
    Security and data access analytics for audit and compliance.
    Optimized for Genie natural language queries.
    Use for: Access auditing, compliance reporting, user activity tracking.
    Example queries: "Who accessed this table?", "Table access by user",
    "Write operations today", "Most accessed tables"
  
  source: ${catalog}.${gold_schema}.fact_table_lineage
  
  joins:
    - name: dim_workspace
      source: ${catalog}.${gold_schema}.dim_workspace
      'on': source.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
  
  dimensions:
    - name: source_table
      expr: source.source_table_full_name
      comment: Full name of source table accessed
      display_name: Source Table
      synonyms:
        - read table
        - input table
    
    - name: target_table
      expr: source.target_table_full_name
      comment: Full name of target table written
      display_name: Target Table
      synonyms:
        - write table
        - output table
    
    - name: created_by
      expr: source.created_by
      comment: User who performed the operation
      display_name: User
      synonyms:
        - user
        - accessed by
    
    - name: entity_type
      expr: source.entity_type
      comment: Type of operation entity
      display_name: Entity Type
    
    - name: workspace_name
      expr: dim_workspace.workspace_name
      comment: Workspace where access occurred
      display_name: Workspace
    
    - name: event_date
      expr: source.event_date
      comment: Date of access event
      display_name: Event Date
      synonyms:
        - date
  
  measures:
    - name: total_events
      expr: COUNT(*)
      comment: Total number of lineage events
      display_name: Total Events
      format:
        type: number
        abbreviation: compact
      synonyms:
        - events
        - operations
    
    - name: read_events
      expr: SUM(CASE WHEN source.source_table_full_name IS NOT NULL THEN 1 ELSE 0 END)
      comment: Number of table read operations
      display_name: Read Operations
      format:
        type: number
        abbreviation: compact
      synonyms:
        - reads
    
    - name: write_events
      expr: SUM(CASE WHEN source.target_table_full_name IS NOT NULL THEN 1 ELSE 0 END)
      comment: Number of table write operations
      display_name: Write Operations
      format:
        type: number
        abbreviation: compact
      synonyms:
        - writes
    
    - name: unique_users
      expr: COUNT(DISTINCT source.created_by)
      comment: Number of unique users
      display_name: Unique Users
      format:
        type: number
      synonyms:
        - users
        - user count
    
    - name: unique_tables
      expr: COUNT(DISTINCT COALESCE(source.source_table_full_name, source.target_table_full_name))
      comment: Number of unique tables accessed
      display_name: Tables Accessed
      format:
        type: number
      synonyms:
        - tables
        - table count
```

---

## Metric Views Summary

| Metric View | Source Fact Table | Key Dimensions | Key Measures | Genie Use Cases |
|-------------|-------------------|----------------|--------------|-----------------|
| **cost_analytics_metrics** | fact_usage | workspace, sku, owner, date | total_cost, total_dbu, avg_daily_cost | Cost analysis, chargeback |
| **job_performance_metrics** | fact_job_run_timeline | job, workspace, result | success_rate, failure_rate, avg_duration | Reliability monitoring |
| **query_analytics_metrics** | fact_query_history | warehouse, user, statement_type | avg_duration, p95_duration, queue_time | Query optimization |
| **cluster_utilization_metrics** | fact_node_timeline | cluster, owner, node_type | cpu_utilization, memory_utilization | Right-sizing |
| **security_analytics_metrics** | fact_table_lineage | table, user, workspace | read_events, write_events | Audit, compliance |

---

## Deployment Configuration

```yaml
# resources/gold/metric_views_setup_job.yml
resources:
  jobs:
    metric_views_setup_job:
      name: "[${bundle.target}] Health Monitor - Metric Views Setup"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - pyyaml>=6.0
      
      tasks:
        - task_key: deploy_metric_views
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/metric_views/deploy_metric_views.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
      
      tags:
        project: health_monitor
        layer: gold
        artifact_type: metric_view
```

---

## Python Deployment Script Pattern

```python
# src/gold/metric_views/deploy_metric_views.py
import yaml
from pathlib import Path

def create_metric_view(spark, catalog: str, schema: str, view_config: dict):
    """Create a metric view from YAML configuration."""
    view_name = view_config['name']
    fqn = f"{catalog}.{schema}.{view_name}"
    
    # Drop existing view/table
    spark.sql(f"DROP VIEW IF EXISTS {fqn}")
    spark.sql(f"DROP TABLE IF EXISTS {fqn}")
    
    # Convert config to YAML string
    yaml_str = yaml.dump([view_config], default_flow_style=False)
    
    # Escape single quotes in comment
    comment_escaped = view_config.get('comment', '').replace("'", "''")
    
    # Create metric view using correct syntax
    create_sql = f"""
    CREATE VIEW {fqn}
    WITH METRICS
    LANGUAGE YAML
    COMMENT '{comment_escaped}'
    AS $$
{yaml_str}
    $$
    """
    
    try:
        spark.sql(create_sql)
        print(f"✓ Created metric view: {view_name}")
        return True
    except Exception as e:
        print(f"✗ Error creating {view_name}: {e}")
        return False
```

---

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Metric Views Created** | 5 views | Count in information_schema |
| **Genie Recognition** | 100% | All views discoverable in Genie |
| **Synonym Coverage** | 3+ per measure | Average synonyms per measure |
| **Query Performance** | <3s response | P95 latency for Genie queries |
| **Documentation** | Complete | LLM comments on every field |

---

## References

### Official Databricks Documentation
- [Databricks Metric Views](https://docs.databricks.com/metric-views)
- [Metric View YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [Deploy Metric Views with DABs](https://community.databricks.com/t5/technical-blog/how-to-deploy-metric-views-with-dabs/ba-p/138432)

### Microsoft Learn Documentation
- [Metric Views Semantic Metadata](https://docs.databricks.com/aws/en/metric-views/semantic-metadata)
- [Metric Views Joins](https://docs.databricks.com/aws/en/metric-views/joins)

### Inspiration Repositories
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme) - Query efficiency metrics patterns
- [System Tables Audit Logs](https://github.com/andyweaves/system-tables-audit-logs) - Security metrics patterns

### Cursor Rules Reference
- [Cursor Rule: Metric Views Patterns](mdc:.cursor/rules/14-metric-views-patterns.mdc)

