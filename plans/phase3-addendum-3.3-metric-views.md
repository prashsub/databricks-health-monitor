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
      expr: source.identity_metadata_run_as
      comment: User or service principal who ran the workload (flattened from identity_metadata)
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
    - name: tag_status
      expr: CASE WHEN source.is_tagged = TRUE THEN 'Tagged' ELSE 'Untagged' END
      comment: Whether the usage record has custom tags for cost attribution (uses pre-calculated is_tagged flag)
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
      expr: SUM(source.list_cost)
      comment: Total estimated cost in USD (pre-calculated from list_price * usage_quantity)
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
      expr: AVG(source.list_cost)
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
      expr: SUM(CASE WHEN source.is_tagged = TRUE THEN source.list_cost ELSE 0 END)
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
      expr: SUM(CASE WHEN source.is_tagged = FALSE THEN source.list_cost ELSE 0 END)
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
      expr: SUM(CASE WHEN source.is_tagged = TRUE THEN source.list_cost ELSE 0 END) / NULLIF(SUM(source.list_cost), 0) * 100
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
      expr: SUM(source.list_cost)
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
      expr: SUM(SUM(source.list_cost)) OVER (ORDER BY DATE_TRUNC('month', source.usage_date))
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
      'on': source.run_date = dim_date.date  # Using pre-calculated run_date
  
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
      expr: source.run_date  # Using pre-calculated run_date
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
      expr: SUM(CASE WHEN source.is_success = TRUE THEN 1 ELSE 0 END)
      comment: Number of successful job runs (uses pre-calculated is_success flag)
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
      expr: (SUM(CASE WHEN source.is_success = TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100
      comment: Percentage of successful runs (uses pre-calculated is_success flag)
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
      expr: (SUM(CASE WHEN source.is_success = FALSE THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100
      comment: Percentage of failed runs (inverse of is_success flag)
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
      expr: AVG(source.run_duration_minutes)
      comment: Average job run duration in minutes (uses pre-calculated run_duration_minutes)
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
      expr: SUM(source.run_duration_minutes) / 60
      comment: Total cumulative runtime in hours (uses pre-calculated run_duration_minutes)
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

## 🆕 ML-Enhanced Metric Views (Phase 3.3a)

### Overview

The ML model inference pipeline (batch_inference_all_models.py) produces prediction tables that can significantly enhance Genie queries with predictive insights. This section defines new metric views that leverage ML predictions.

### ML Inference Output Tables

| Domain | Model | Output Table | Key Predictions |
|--------|-------|--------------|-----------------|
| **Cost** | cost_anomaly_detector | cost_anomaly_predictions | is_anomaly, anomaly_score |
| **Cost** | budget_forecaster | budget_forecast_predictions | predicted_cost, confidence |
| **Cost** | commitment_recommender | commitment_recommendations | recommended_commit |
| **Security** | security_threat_detector | security_threat_predictions | threat_score, is_threat |
| **Security** | exfiltration_detector | exfiltration_predictions | exfil_risk_score |
| **Performance** | performance_regression_detector | performance_regression_predictions | is_regression, regression_score |
| **Reliability** | job_failure_predictor | failure_predictions | failure_probability |
| **Reliability** | sla_breach_predictor | sla_breach_predictions | breach_probability |
| **Quality** | data_drift_detector | data_drift_predictions | drift_score, is_drift |

### New Metric Views

#### 1. ml_intelligence_metrics (NEW)

Unified view of ML predictions across all domains for executive dashboards and alerting.

```yaml
version: "1.1"
comment: >
  Unified ML intelligence metrics aggregating predictions across all domains.
  Use for: Executive AI/ML dashboards, anomaly monitoring, predictive alerts.
  Example: "How many anomalies detected today?", "Show high-risk entities"

source: ${catalog}.${ml_schema}.ml_predictions_summary

dimensions:
  - name: prediction_date
    expr: source.prediction_date
    comment: Date of ML prediction
  - name: domain
    expr: source.domain
    comment: Domain (cost, security, performance, reliability, quality)
  - name: model_name
    expr: source.model_name
    comment: ML model that generated the prediction
  - name: entity_type
    expr: source.entity_type
    comment: Type of entity (workspace, job, warehouse, user)
  - name: entity_id
    expr: source.entity_id
    comment: ID of the entity being scored

measures:
  - name: total_predictions
    expr: COUNT(source.prediction_id)
    comment: Total predictions generated
  - name: anomaly_count
    expr: SUM(CASE WHEN source.is_anomaly THEN 1 ELSE 0 END)
    comment: Count of detected anomalies
  - name: high_risk_count
    expr: SUM(CASE WHEN source.risk_score > 0.8 THEN 1 ELSE 0 END)
    comment: Count of high-risk predictions (score > 0.8)
  - name: avg_risk_score
    expr: AVG(source.risk_score)
    comment: Average risk/anomaly score (0-1)
  - name: anomaly_rate
    expr: (SUM(CASE WHEN source.is_anomaly THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0)
    comment: Percentage of predictions flagged as anomalies
```

#### 2. data_quality_metrics (NEW)

Data quality monitoring metrics combining Lakehouse Monitor outputs with Gold layer metadata.

```yaml
version: "1.1"
comment: >
  Data quality metrics for freshness, drift, and schema monitoring.
  Use for: Data quality dashboards, SLA monitoring, data governance.
  Example: "Which tables are stale?", "Show data quality score by domain"

source: ${catalog}.${gold_schema}.dim_table

joins:
  - name: freshness
    source: ${catalog}.${ml_schema}.freshness_predictions
    'on': source.table_full_name = freshness.table_full_name

dimensions:
  - name: domain
    expr: source.domain
    comment: Data domain (billing, compute, security, etc.)
  - name: table_name
    expr: source.table_name
    comment: Table name
  - name: table_type
    expr: source.table_type
    comment: Type (fact, dim)
  - name: last_modified
    expr: source.last_modified
    comment: Last modification time

measures:
  - name: total_tables
    expr: COUNT(source.table_id)
    comment: Total tables in Gold layer
  - name: stale_tables
    expr: SUM(CASE WHEN freshness.is_stale THEN 1 ELSE 0 END)
    comment: Tables exceeding freshness SLA
  - name: freshness_rate
    expr: (1 - SUM(CASE WHEN freshness.is_stale THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100
    comment: Percentage of tables meeting freshness SLA
  - name: avg_hours_since_update
    expr: AVG(TIMESTAMPDIFF(HOUR, source.last_modified, CURRENT_TIMESTAMP()))
    comment: Average hours since last update
```

### Enhancement to Existing Metric Views

The following existing metric views should be enhanced with ML prediction joins:

| Metric View | ML Table to Join | New Measures |
|-------------|------------------|--------------|
| cost_analytics | cost_anomaly_predictions | is_cost_anomaly, anomaly_score, predicted_cost |
| job_performance | failure_predictions, sla_breach_predictions | failure_probability, sla_risk |
| security_events | security_threat_predictions | threat_score, is_high_risk_user |
| query_performance | performance_regression_predictions | is_regression, regression_severity |

### Implementation Priority

1. **Phase 1 (Core):** ml_intelligence_metrics, data_quality_metrics
2. **Phase 2 (Enhancement):** Add ML joins to existing metric views
3. **Phase 3 (Advanced):** Create domain-specific ML dashboards

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

## 🆕 Dashboard Pattern Enhancements for Metric Views

Based on analysis of real-world Databricks dashboards (see [phase3-use-cases.md SQL Patterns Catalog](./phase3-use-cases.md#-sql-query-patterns-catalog-from-dashboard-analysis)), the following dimensions and measures should be added to existing metric views:

### New Dimensions (from Dashboard Patterns)

#### Entity Type Classification (Pattern 11)
**Source:** LakeFlow System Tables Dashboard

Add to `cost_analytics_metrics`:
```yaml
- name: entity_type
  expr: >
    CONCAT_WS(' ',
      CASE WHEN source.is_serverless THEN 'SERVERLESS' ELSE 'CLASSIC' END,
      CASE
        WHEN source.billing_origin_product = 'JOBS' THEN 'JOB'
        WHEN source.billing_origin_product IN ('DLT', 'LAKEFLOW_CONNECT') THEN 'PIPELINE'
        WHEN source.billing_origin_product = 'SQL' AND source.dlt_pipeline_id IS NOT NULL THEN 'PIPELINE'
        WHEN source.billing_origin_product = 'SQL' THEN 'WAREHOUSE'
        ELSE source.billing_origin_product
      END)
  comment: Classification of workload by serverless status and product type
  display_name: Entity Type
  synonyms:
    - workload type
    - compute type
    - product type
    - serverless status
```

#### Risk Level Classification
**Source:** Serverless Cost Dashboard (P90 deviation)

Add to `job_performance_metrics`:
```yaml
- name: cost_risk_level
  expr: >
    CASE
      WHEN source.run_cost > (source.job_avg_cost * 2) THEN 'HIGH'
      WHEN source.run_cost > (source.job_avg_cost * 1.5) THEN 'MEDIUM'
      ELSE 'NORMAL'
    END
  comment: Risk classification based on deviation from typical job cost
  display_name: Cost Risk Level
  synonyms:
    - outlier status
    - cost warning level
    - deviation level
```

### New Measures (from Dashboard Patterns)

#### Period Comparison Measures (Pattern 1, 2)
**Source:** Azure Serverless Cost Dashboard

Add to `cost_analytics_metrics`:
```yaml
# 7-day vs prior 7-day comparison
- name: last_7_day_cost
  expr: >
    SUM(CASE WHEN source.usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -7) AND CURRENT_DATE()
        THEN source.list_cost ELSE 0 END)
  comment: Total cost in the last 7 days
  display_name: Last 7 Day Cost
  format:
    type: currency
    currency_code: USD
  synonyms:
    - this week cost
    - recent week spend

- name: prior_7_day_cost
  expr: >
    SUM(CASE WHEN source.usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7)
        THEN source.list_cost ELSE 0 END)
  comment: Total cost in the 7 days prior to last week
  display_name: Prior 7 Day Cost
  format:
    type: currency
    currency_code: USD
  synonyms:
    - last week cost
    - previous week spend

- name: week_over_week_growth_pct
  expr: >
    TRY_DIVIDE(
      SUM(CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -7) THEN source.list_cost ELSE 0 END) -
      SUM(CASE WHEN source.usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN source.list_cost ELSE 0 END),
      NULLIF(SUM(CASE WHEN source.usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -14) AND DATE_ADD(CURRENT_DATE(), -7) THEN source.list_cost ELSE 0 END), 0)
    ) * 100
  comment: Week-over-week cost growth percentage
  display_name: WoW Growth %
  format:
    type: percentage
    decimal_places:
      type: exact
      places: 1
  synonyms:
    - weekly growth
    - wow change
    - week over week

# 30-day vs 60-day comparison
- name: last_30_day_cost
  expr: >
    SUM(CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -30)
        THEN source.list_cost ELSE 0 END)
  comment: Total cost in the last 30 days
  display_name: Last 30 Day Cost
  format:
    type: currency
    currency_code: USD
  synonyms:
    - this month cost
    - recent month spend

- name: month_over_month_growth_pct
  expr: >
    TRY_DIVIDE(
      SUM(CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -30) THEN source.list_cost ELSE 0 END) -
      SUM(CASE WHEN source.usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -60) AND DATE_ADD(CURRENT_DATE(), -30) THEN source.list_cost ELSE 0 END),
      NULLIF(SUM(CASE WHEN source.usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -60) AND DATE_ADD(CURRENT_DATE(), -30) THEN source.list_cost ELSE 0 END), 0)
    ) * 100
  comment: Month-over-month cost growth percentage (30 vs prior 30 days)
  display_name: MoM Growth %
  format:
    type: percentage
    decimal_places:
      type: exact
      places: 1
  synonyms:
    - monthly growth
    - mom change
    - month over month
```

#### KPI Summary Measures (Pattern 13)
**Source:** Azure Serverless Cost Dashboard

Add to `cost_analytics_metrics`:
```yaml
- name: unique_jobs_30d
  expr: COUNT(DISTINCT CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -30) THEN source.usage_metadata_job_id END)
  comment: Count of unique jobs that incurred cost in last 30 days
  display_name: Active Jobs (30d)
  format:
    type: number
  synonyms:
    - job count
    - active jobs

- name: unique_users_30d
  expr: COUNT(DISTINCT CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -30) THEN source.identity_metadata_run_as END)
  comment: Count of unique users who ran workloads in last 30 days
  display_name: Active Users (30d)
  format:
    type: number
  synonyms:
    - user count
    - active users

- name: unique_workspaces_30d
  expr: COUNT(DISTINCT CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -30) THEN source.workspace_id END)
  comment: Count of unique workspaces with activity in last 30 days
  display_name: Active Workspaces (30d)
  format:
    type: number
  synonyms:
    - workspace count
    - active environments
```

#### Lineage Activity Measures (Pattern 7)
**Source:** Governance Hub Dashboard

Add to new `governance_analytics_metrics`:
```yaml
- name: active_table_count
  expr: COUNT(DISTINCT CASE WHEN source.event_date >= DATE_ADD(CURRENT_DATE(), -30) THEN COALESCE(source.source_table_full_name, source.target_table_full_name) END)
  comment: Tables with read or write activity in last 30 days
  display_name: Active Tables
  format:
    type: number
  synonyms:
    - tables with activity
    - used tables

- name: read_event_count
  expr: SUM(CASE WHEN source.source_table_full_name IS NOT NULL THEN 1 ELSE 0 END)
  comment: Count of read operations from tables
  display_name: Read Events
  format:
    type: number
  synonyms:
    - reads
    - table reads

- name: write_event_count
  expr: SUM(CASE WHEN source.target_table_full_name IS NOT NULL THEN 1 ELSE 0 END)
  comment: Count of write operations to tables
  display_name: Write Events
  format:
    type: number
  synonyms:
    - writes
    - table writes
```

### New Metric View: governance_analytics_metrics (🆕)

Based on Governance Hub Dashboard patterns, add a new metric view:

**Source:** `${catalog}.${gold_schema}.fact_table_lineage`

**Key Dimensions:**
- `table_catalog`, `table_schema`, `table_name`
- `created_by` (user who triggered lineage event)
- `event_type` (READ, WRITE)
- `activity_status` (ACTIVE if accessed in 30 days)

**Key Measures:**
- `total_lineage_events` - COUNT(*)
- `active_table_count` - Tables with recent activity
- `inactive_table_count` - Tables without recent activity
- `read_write_ratio` - Read events / Write events
- `unique_users` - Distinct users accessing data

---

## 🆕 GitHub Repository Pattern Enhancements for Metric Views

Based on analysis of open-source Databricks repositories, the following enhancements should be incorporated into metric views:

### From system-tables-audit-logs Repository

#### Time-Windowed Measures
**Pattern:** 24-hour and 90-day rolling window aggregations for baseline comparison

Add to `security_analytics_metrics`:
```yaml
# Time-windowed security measures (from audit logs repo)
measures:
  - name: events_24h
    expr: COUNT(CASE WHEN source.event_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS THEN 1 END)
    comment: Events in last 24 hours for anomaly detection baseline
    display_name: Events (24h)
    synonyms:
      - daily events
      - recent events

  - name: events_7d_avg
    expr: COUNT(*) / 7
    comment: Average daily events over 7 days
    display_name: Avg Daily Events (7d)
    synonyms:
      - average events
      - daily average

  - name: event_growth_rate
    expr: >
      (COUNT(CASE WHEN source.event_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS THEN 1 END) -
       COUNT(CASE WHEN source.event_time BETWEEN CURRENT_TIMESTAMP() - INTERVAL 48 HOURS
                                            AND CURRENT_TIMESTAMP() - INTERVAL 24 HOURS THEN 1 END)) /
      NULLIF(COUNT(CASE WHEN source.event_time BETWEEN CURRENT_TIMESTAMP() - INTERVAL 48 HOURS
                                                   AND CURRENT_TIMESTAMP() - INTERVAL 24 HOURS THEN 1 END), 0) * 100
    comment: 24-hour event growth rate compared to prior 24 hours
    display_name: Event Growth %
    synonyms:
      - growth rate
      - day over day
```

#### System Account Exclusion Dimension
**Pattern:** Filter out system and service accounts from user-centric analysis

```yaml
# System account filtering (from audit logs repo)
dimensions:
  - name: user_type
    expr: >
      CASE
        WHEN source.created_by LIKE 'system.%' THEN 'SYSTEM'
        WHEN source.created_by LIKE 'databricks-%' THEN 'PLATFORM'
        WHEN source.created_by LIKE '%service-principal%' THEN 'SERVICE_PRINCIPAL'
        WHEN source.created_by LIKE '%@%' THEN 'HUMAN_USER'
        ELSE 'UNKNOWN'
      END
    comment: User type classification for filtering system vs human activity
    display_name: User Type
    synonyms:
      - account type
      - user classification

  - name: is_human_user
    expr: >
      CASE
        WHEN source.created_by NOT LIKE 'system.%'
         AND source.created_by NOT LIKE 'databricks-%'
         AND source.created_by LIKE '%@%'
        THEN 'Yes' ELSE 'No'
      END
    comment: Flag for human users (excludes system and service accounts)
    display_name: Human User
    synonyms:
      - real user
      - human activity
```

### From Workflow Advisor Repository

#### Resource Efficiency Dimensions
**Pattern:** Cluster utilization status classification

Add to `cluster_utilization_metrics`:
```yaml
# Provisioning status dimension (from Workflow Advisor repo)
dimensions:
  - name: provisioning_status
    expr: >
      CASE
        WHEN source.cpu_user_percent + source.cpu_system_percent > 90
          OR source.mem_used_percent > 85 THEN 'UNDERPROVISIONED'
        WHEN source.cpu_user_percent + source.cpu_system_percent < 20
         AND source.mem_used_percent < 30 THEN 'OVERPROVISIONED'
        WHEN source.cpu_user_percent + source.cpu_system_percent < 50
         AND source.mem_used_percent < 50 THEN 'UNDERUTILIZED'
        ELSE 'OPTIMAL'
      END
    comment: Cluster provisioning status based on CPU and memory utilization
    display_name: Provisioning Status
    synonyms:
      - sizing status
      - utilization status
      - right-sizing status

  - name: savings_opportunity
    expr: >
      CASE
        WHEN source.cpu_user_percent + source.cpu_system_percent < 30
         AND source.mem_used_percent < 40 THEN 'HIGH'
        WHEN source.cpu_user_percent + source.cpu_system_percent < 50
         AND source.mem_used_percent < 60 THEN 'MEDIUM'
        ELSE 'LOW'
      END
    comment: Cost savings opportunity level based on underutilization
    display_name: Savings Opportunity
    synonyms:
      - cost opportunity
      - right-sizing potential
```

#### Resource Efficiency Measures
```yaml
# Cost efficiency measures (from Workflow Advisor repo)
measures:
  - name: wasted_capacity_pct
    expr: >
      (100 - AVG(source.cpu_user_percent + source.cpu_system_percent)) *
      (100 - AVG(source.mem_used_percent)) / 10000
    comment: Combined CPU and memory waste percentage - lower is better
    display_name: Wasted Capacity %
    format:
      type: percentage
    synonyms:
      - waste percentage
      - unused capacity

  - name: resource_efficiency_score
    expr: AVG(source.cpu_user_percent + source.cpu_system_percent) * AVG(source.mem_used_percent) / 100
    comment: Combined efficiency score (0-100) - higher is better utilization
    display_name: Efficiency Score
    format:
      type: number
      decimal_places:
        type: exact
        places: 1
    synonyms:
      - utilization score
      - efficiency rating

  - name: potential_savings_pct
    expr: >
      CASE
        WHEN AVG(source.cpu_user_percent + source.cpu_system_percent) < 30 THEN 50
        WHEN AVG(source.cpu_user_percent + source.cpu_system_percent) < 50 THEN 30
        WHEN AVG(source.cpu_user_percent + source.cpu_system_percent) < 70 THEN 15
        ELSE 0
      END
    comment: Estimated potential cost savings percentage from right-sizing
    display_name: Potential Savings %
    format:
      type: percentage
    synonyms:
      - savings estimate
      - cost reduction opportunity
```

### From DBSQL Warehouse Advisor Repository

#### Query Efficiency Dimensions
**Pattern:** Pre-calculated efficiency flags for dashboard filtering

Add to `query_analytics_metrics`:
```yaml
# Query efficiency dimensions (from DBSQL Warehouse Advisor repo)
dimensions:
  - name: query_efficiency_status
    expr: >
      CASE
        WHEN (COALESCE(source.spill_local_bytes, 0) + COALESCE(source.spill_remote_bytes, 0)) > 100000000 THEN 'HIGH_SPILL'
        WHEN source.waiting_at_capacity_duration_ms > source.total_duration_ms * 0.1 THEN 'HIGH_QUEUE'
        WHEN source.total_duration_ms > 300000 THEN 'SLOW'
        ELSE 'EFFICIENT'
      END
    comment: Query efficiency classification for performance analysis
    display_name: Efficiency Status
    synonyms:
      - query status
      - performance status

  - name: query_complexity
    expr: >
      CASE
        WHEN LENGTH(source.statement_text) > 10000 THEN 'VERY_COMPLEX'
        WHEN LENGTH(source.statement_text) > 5000 THEN 'COMPLEX'
        WHEN LENGTH(source.statement_text) > 1000 THEN 'MODERATE'
        ELSE 'SIMPLE'
      END
    comment: Query complexity classification based on query length
    display_name: Query Complexity
    synonyms:
      - complexity level
      - query size

  - name: warehouse_sizing_indicator
    expr: >
      CASE
        WHEN AVG(source.waiting_at_capacity_duration_ms) > 30000 THEN 'SCALE_UP_NEEDED'
        WHEN AVG(source.total_duration_ms) < 1000
         AND COUNT(*) < 100 THEN 'SCALE_DOWN_POSSIBLE'
        ELSE 'OPTIMAL'
      END
    comment: Warehouse sizing recommendation based on queue times and query patterns
    display_name: Sizing Indicator
    synonyms:
      - scaling recommendation
      - size adjustment
```

#### Query Efficiency Measures
```yaml
# Query efficiency measures (from DBSQL Warehouse Advisor repo)
measures:
  - name: inefficient_query_count
    expr: >
      COUNT(CASE
        WHEN (COALESCE(source.spill_local_bytes, 0) + COALESCE(source.spill_remote_bytes, 0)) > 0
          OR source.waiting_at_capacity_duration_ms > 30000
          OR source.total_duration_ms > 300000
        THEN 1
      END)
    comment: Count of queries with efficiency issues (spill, queue, or slow)
    display_name: Inefficient Queries
    synonyms:
      - problem queries
      - queries needing optimization

  - name: efficiency_rate
    expr: >
      (1 - COUNT(CASE
        WHEN (COALESCE(source.spill_local_bytes, 0) + COALESCE(source.spill_remote_bytes, 0)) > 0
          OR source.waiting_at_capacity_duration_ms > 30000
          OR source.total_duration_ms > 300000
        THEN 1
      END) / NULLIF(COUNT(*), 0)) * 100
    comment: Percentage of queries without efficiency issues
    display_name: Efficiency Rate
    format:
      type: percentage
    synonyms:
      - success rate
      - health rate

  - name: avg_queue_to_execution_ratio
    expr: >
      AVG(source.waiting_at_capacity_duration_ms * 100.0 / NULLIF(source.total_duration_ms, 0))
    comment: Average ratio of queue time to total execution time - lower is better
    display_name: Queue/Execution Ratio
    format:
      type: percentage
    synonyms:
      - queue ratio
      - wait percentage
```

### New Metric View: cluster_efficiency_metrics (🆕)
**Source:** Workflow Advisor Repository

A dedicated metric view for cluster right-sizing analysis:

```yaml
version: "1.1"

- name: cluster_efficiency_metrics
  comment: |
    Cluster efficiency and right-sizing metrics for cost optimization.
    Use for: Right-sizing recommendations, cost savings identification, capacity planning.
    Example queries: "Which clusters are overprovisioned?", "Show potential savings"
    Source pattern: Workflow Advisor repository

  source: ${catalog}.${gold_schema}.fact_node_timeline

  joins:
    - name: dim_cluster
      source: ${catalog}.${gold_schema}.dim_cluster
      'on': source.cluster_id = dim_cluster.cluster_id AND dim_cluster.is_current = true

  dimensions:
    - name: cluster_name
      expr: dim_cluster.cluster_name
      comment: Cluster name
      display_name: Cluster
      synonyms: [cluster]

    - name: provisioning_status
      expr: >
        CASE
          WHEN source.cpu_user_percent + source.cpu_system_percent > 90 THEN 'UNDERPROVISIONED'
          WHEN source.cpu_user_percent + source.cpu_system_percent < 20 THEN 'OVERPROVISIONED'
          ELSE 'OPTIMAL'
        END
      comment: Cluster sizing status
      display_name: Status
      synonyms: [sizing status, utilization status]

  measures:
    - name: avg_cpu_utilization
      expr: AVG(source.cpu_user_percent + source.cpu_system_percent)
      comment: Average CPU utilization
      display_name: Avg CPU %
      format:
        type: percentage
      synonyms: [cpu, cpu usage]

    - name: avg_memory_utilization
      expr: AVG(source.mem_used_percent)
      comment: Average memory utilization
      display_name: Avg Memory %
      format:
        type: percentage
      synonyms: [memory, mem usage]

    - name: underprovisioned_hours
      expr: >
        SUM(CASE WHEN source.cpu_user_percent + source.cpu_system_percent > 90 THEN 1 ELSE 0 END) / 60.0
      comment: Hours of CPU saturation
      display_name: Saturated Hours
      synonyms: [overloaded time]

    - name: wasted_hours
      expr: >
        SUM(CASE WHEN source.cpu_user_percent + source.cpu_system_percent < 20 THEN 1 ELSE 0 END) / 60.0
      comment: Hours of significant underutilization
      display_name: Wasted Hours
      synonyms: [idle time, unused capacity]
```

---

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Metric Views Created** | 10 views (6 core + 2 ML-enhanced + 1 governance + 1 efficiency) | Count in information_schema |
| **Genie Recognition** | 100% | All views discoverable in Genie |
| **Synonym Coverage** | 3+ per measure | Average synonyms per measure |
| **Query Performance** | <3s response | P95 latency for Genie queries |
| **Documentation** | Complete | LLM comments on every field |
| **ML Integration** | 2 new views | ml_intelligence_metrics, data_quality_metrics |
| **Efficiency Metrics** | Complete | Right-sizing dimensions and measures |

---

## References

### Official Databricks Documentation
- [Databricks Metric Views](https://docs.databricks.com/metric-views)
- [Metric View YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [Deploy Metric Views with DABs](https://community.databricks.com/t5/technical-blog/how-to-deploy-metric-views-with-dabs/ba-p/138432)

### Microsoft Learn Documentation
- [Metric Views Semantic Metadata](https://docs.databricks.com/aws/en/metric-views/semantic-metadata)
- [Metric Views Joins](https://docs.databricks.com/aws/en/metric-views/joins)

### GitHub Repository References (🆕)
- [system-tables-audit-logs](https://github.com/andyweaves/system-tables-audit-logs) - Time-windowed aggregations, system account filtering
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme) - Query efficiency metrics, warehouse sizing indicators
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor) - Resource efficiency dimensions, right-sizing measures

### Blog Post References (🆕)
- [DBSQL Warehouse Advisor v5](https://medium.com/dbsql-sme-engineering/the-dbsql-warehouse-advisor-dashboard-v5-multi-warehouse-analytics-ef4f07578ac1) - P95/P99 percentiles, QPS/QPM metrics, multi-warehouse analytics
- [Workflow Advisor Dashboard](https://medium.com/dbsql-sme-engineering/analyzing-workflows-in-dbsql-with-the-workflows-advisor-dashboard-95fee9f01fe6) - Job state classification, owner attribution, duration regression

### Cursor Rules Reference
- [Cursor Rule: Metric Views Patterns](mdc:.cursor/rules/14-metric-views-patterns.mdc)

---

## 🆕 Blog Post Pattern Enhancements for Metric Views

Based on analysis of Databricks engineering blog posts, the following metric view enhancements should be incorporated:

### From "DBSQL Warehouse Advisor v5" Blog

#### P99 Percentile Measures (Enhancement)
**Pattern:** Blog tracks "P95/99 percentiles" not just P95 - add P99 for stricter SLA monitoring

Add to `query_analytics_metrics`:
```yaml
# P99 measures for stricter SLA analysis (from Warehouse Advisor v5 blog)
measures:
  - name: p99_query_duration_sec
    expr: PERCENTILE(source.total_duration_ms / 1000.0, 0.99)
    comment: 99th percentile query duration in seconds - for strict SLA tracking
    display_name: P99 Duration (sec)
    format:
      type: number
      decimal_places:
        type: exact
        places: 2
    synonyms:
      - p99 latency
      - 99th percentile duration

  - name: p99_queue_time_sec
    expr: PERCENTILE(source.waiting_at_capacity_duration_ms / 1000.0, 0.99)
    comment: 99th percentile queue time - identifies worst-case waits
    display_name: P99 Queue Time (sec)
    synonyms:
      - p99 wait time
      - worst case queue
```

#### Throughput Measures (QPS/QPM)
**Pattern:** Blog tracks "QPS/QPM metrics (queries per second/minute) for throughput analysis"

```yaml
# Throughput measures (from Warehouse Advisor v5 blog)
measures:
  - name: queries_per_minute
    expr: COUNT(*) / NULLIF(TIMESTAMPDIFF(MINUTE, MIN(source.query_start_time), MAX(source.query_start_time)), 0)
    comment: Average queries per minute - throughput metric
    display_name: QPM
    synonyms:
      - throughput
      - query rate
      - queries per minute

  - name: queries_per_second
    expr: COUNT(*) / NULLIF(TIMESTAMPDIFF(SECOND, MIN(source.query_start_time), MAX(source.query_start_time)), 0)
    comment: Average queries per second - high-frequency throughput metric
    display_name: QPS
    synonyms:
      - query throughput
      - queries per second
```

#### Multi-Warehouse Comparison Dimensions
**Pattern:** Blog enables "side-by-side SLA comparison across multiple warehouses"

```yaml
# Multi-warehouse comparison support (from Warehouse Advisor v5 blog)
dimensions:
  - name: warehouse_tier
    expr: >
      CASE
        WHEN dim_warehouse.warehouse_size IN ('2X-Small', 'X-Small', 'Small') THEN 'SMALL'
        WHEN dim_warehouse.warehouse_size IN ('Medium', 'Large') THEN 'MEDIUM'
        WHEN dim_warehouse.warehouse_size IN ('X-Large', '2X-Large', '3X-Large', '4X-Large') THEN 'LARGE'
        ELSE 'UNKNOWN'
      END
    comment: Warehouse size tier for comparative SLA analysis
    display_name: Warehouse Tier
    synonyms:
      - size category
      - warehouse class
```

### From "Workflow Advisor Dashboard" Blog

#### Job State Dimensions
**Pattern:** Blog tracks 5 distinct outcome states: succeeded, errored, failed, timed_out, cancelled

Add to `job_performance_metrics`:
```yaml
# Complete job state classification (from Workflow Advisor blog)
dimensions:
  - name: outcome_category
    expr: >
      CASE
        WHEN source.result_state = 'SUCCEEDED' THEN 'SUCCESS'
        WHEN source.result_state IN ('ERRORED', 'FAILED') THEN 'FAILURE'
        WHEN source.result_state = 'TIMED_OUT' THEN 'TIMEOUT'
        WHEN source.result_state = 'CANCELLED' THEN 'CANCELLED'
        ELSE 'OTHER'
      END
    comment: Grouped outcome category for simplified analysis
    display_name: Outcome
    synonyms:
      - result category
      - job outcome

  - name: cluster_type_efficiency
    expr: >
      CASE
        WHEN source.cluster_spec LIKE '%all_purpose%' THEN 'ALL_PURPOSE (Less Efficient)'
        WHEN source.cluster_spec LIKE '%job%' THEN 'JOB_CLUSTER (Efficient)'
        ELSE 'OTHER'
      END
    comment: Cluster type with efficiency indicator - ALL_PURPOSE clusters are less cost-efficient
    display_name: Cluster Efficiency Type
    synonyms:
      - cluster type
      - compute type
```

#### Duration Regression Measure
**Pattern:** Blog tracks "% Change in duration of last job from its previous run"

```yaml
# Duration regression detection (from Workflow Advisor blog)
measures:
  - name: jobs_with_regression
    expr: >
      COUNT(CASE
        WHEN source.run_duration_seconds > source.prev_run_duration_seconds * 1.5
        THEN 1
      END)
    comment: Count of jobs with >50% duration increase from previous run
    display_name: Jobs with Regression
    synonyms:
      - regressed jobs
      - slower jobs
```

#### Dashboard Layout Recommendations (Implementation Note)
From the blog: **"Counter metrics at the top provide quick snapshots; rollup charts beneath enable dimensional analysis"**

Metric views should be designed with this hierarchy in mind:
1. **KPI counters** - Single-value metrics for quick health checks
2. **Trend measures** - Time-series aggregations for pattern detection
3. **Dimensional breakdowns** - Grouped metrics for drill-down analysis

#### Temporal Granularity Options
Blog recommends supporting: **hour, day, week, month, quarter, year**

All time-based metric views should include a `time_grain` dimension that supports these levels for flexible analysis.

