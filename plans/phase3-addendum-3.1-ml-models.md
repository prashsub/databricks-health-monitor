# Phase 3 Addendum 3.1: ML Models for Databricks Health Monitor

## Overview

**Status:** 🔧 Significantly Enhanced  
**Dependencies:** Gold Layer (Phase 2)  
**Estimated Effort:** 6-8 weeks  

---

## Purpose

Train machine learning models on **Gold layer tables** to enable:
- **Predictive Analytics** - Forecast costs, job failures, and capacity needs
- **Anomaly Detection** - Identify unusual patterns in real-time
- **Intelligent Alerting** - Context-aware notifications based on ML predictions
- **Optimization Recommendations** - Data-driven suggestions for cost and performance
- **Risk Scoring** - Quantify risks across security, reliability, and compliance

---

## ML Models Catalog by Agent Domain

| Agent Domain | Model Count | Key Models |
|--------------|-------------|------------|
| **💰 Cost** | 5 models | Cost Anomaly, Budget Forecaster, Chargeback Optimizer |
| **🔒 Security** | 4 models | Threat Detector, Exfiltration Detector, Privilege Abuse |
| **⚡ Performance** | 6 models | Query Forecaster, Warehouse Optimizer, DBR Migration Risk |
| **🔄 Reliability** | 5 models | Failure Predictor, SLA Breach, Retry Success Predictor |
| **✅ Quality** | 3 models | Freshness Predictor, Schema Drift, Quality Degradation |
| **Total** | **23 models** | |

---

# 💰 Cost Agent Models (5 Models)

## Model 1.1: Cost Anomaly Detector

**Problem Type:** Anomaly Detection (Unsupervised → Semi-supervised)  
**Use Case:** Detect unusual spending patterns before they impact budgets  
**Business Value:** Prevent budget overruns, identify runaway jobs, detect billing errors

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_usage`, `dim_workspace`, `dim_sku` |
| **Output** | Anomaly score (0-1), is_anomaly flag, deviation_pct |
| **Algorithm** | Isolation Forest → LSTM Autoencoder |
| **Refresh** | Hourly scoring, daily retraining |

### Feature Engineering

```python
# Cost Anomaly Detection Features
cost_features = {
    # Volume features
    "daily_dbu_usage": "SUM(usage_quantity) per day",
    "hourly_dbu_usage": "SUM(usage_quantity) per hour",
    "daily_cost": "SUM(usage_quantity * list_price)",
    
    # Rolling statistics
    "dbu_7day_moving_avg": "AVG(daily_dbu) OVER (ORDER BY date ROWS 7 PRECEDING)",
    "dbu_7day_std_dev": "STDDEV(daily_dbu) OVER (ORDER BY date ROWS 7 PRECEDING)",
    "dbu_30day_moving_avg": "AVG(daily_dbu) OVER (ORDER BY date ROWS 30 PRECEDING)",
    "cost_7day_growth_pct": "(last_7d - prev_7d) / prev_7d * 100",
    
    # Ratio features
    "pct_change_vs_7day_avg": "(daily_dbu - dbu_7day_moving_avg) / dbu_7day_moving_avg",
    "z_score": "(daily_dbu - dbu_7day_moving_avg) / dbu_7day_std_dev",
    
    # Cyclical features (for seasonality)
    "day_of_week_sin": "SIN(2 * PI * day_of_week / 7)",
    "day_of_week_cos": "COS(2 * PI * day_of_week / 7)",
    "hour_of_day_sin": "SIN(2 * PI * hour / 24)",
    "hour_of_day_cos": "COS(2 * PI * hour / 24)",
    "is_month_end": "DAY(usage_date) >= 25",
    "is_weekend": "day_of_week IN (6, 7)",
    
    # Contextual features
    "workspace_count": "COUNT(DISTINCT workspace_id)",
    "active_cluster_count": "COUNT(DISTINCT cluster_id)",
    "sku_count": "COUNT(DISTINCT sku_name)",
    "job_count": "COUNT(DISTINCT job_id)",
    
    # Tag features (from Jobs System Tables Dashboard patterns)
    "untagged_cost_pct": "Percentage of cost without tags",
    "dominant_tag_pct": "Percentage from largest tag bucket",
    
    # Lag features
    "dbu_lag_1d": "LAG(daily_dbu, 1) OVER (ORDER BY date)",
    "dbu_lag_7d": "LAG(daily_dbu, 7) OVER (ORDER BY date)",
    "dbu_lag_30d": "LAG(daily_dbu, 30) OVER (ORDER BY date)",
}
```

### Training SQL (from Gold Layer)

```sql
-- Cost anomaly feature extraction from Gold layer tables
WITH daily_cost AS (
    SELECT 
        f.usage_date,
        f.workspace_id,
        w.workspace_name,
        SUM(f.usage_quantity) AS daily_dbu,
        SUM(f.usage_quantity * f.list_price) AS daily_cost,
        COUNT(DISTINCT f.sku_name) AS sku_count,
        COUNT(DISTINCT f.cluster_id) AS cluster_count,
        COUNT(DISTINCT f.job_id) AS job_count
    FROM ${catalog}.${gold_schema}.fact_usage f
    LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
        ON f.workspace_id = w.workspace_id AND w.is_current = TRUE
    WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
    GROUP BY f.usage_date, f.workspace_id, w.workspace_name
),
with_rolling AS (
    SELECT *,
        AVG(daily_cost) OVER (
            PARTITION BY workspace_id 
            ORDER BY usage_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) AS cost_7day_avg,
        STDDEV(daily_cost) OVER (
            PARTITION BY workspace_id 
            ORDER BY usage_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) AS cost_7day_std,
        (daily_cost - cost_7day_avg) / NULLIF(cost_7day_std, 0) AS z_score,
        -- Cyclical encoding
        SIN(2 * 3.14159 * DAYOFWEEK(usage_date) / 7) AS dow_sin,
        COS(2 * 3.14159 * DAYOFWEEK(usage_date) / 7) AS dow_cos
    FROM daily_cost
)
SELECT * FROM with_rolling
WHERE cost_7day_std IS NOT NULL
```

---

## Model 1.2: Budget Forecaster

**Problem Type:** Time Series Forecasting  
**Use Case:** Predict end-of-month costs for proactive budget management and **commit tracking**  
**Business Value:** Enable proactive budget adjustments, prevent overruns, improve planning, **track progress toward Databricks commit amount**

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_usage`, `dim_workspace`, `dim_date`, **`commit_configurations`** |
| **Output** | Predicted monthly cost, confidence intervals (P10/P50/P90), **commit variance forecast** |
| **Algorithm** | Prophet / ARIMA / LightGBM |
| **Refresh** | Daily forecast updates |

### 🆕 Commit Tracking Integration

The Budget Forecaster outputs are used for **commit vs actual tracking**:

| Output Field | Description | Used For |
|--------------|-------------|----------|
| `predicted_monthly_cost` | P50 forecast for each future month | Expected spend |
| `predicted_monthly_cost_p10` | Optimistic forecast | Best-case scenario |
| `predicted_monthly_cost_p90` | Conservative forecast | Worst-case scenario |
| `cumulative_forecast` | YTD + forecast to year-end | Commit comparison |
| `commit_variance_forecast` | Forecast - Commit | Undershoot/Overshoot prediction |

**Inference Table:** `budget_forecast_predictions` - Stores daily forecasts for downstream use by dashboards, TVFs, and alerting.

### Feature Engineering

```python
# Budget Forecasting Features
budget_features = {
    # Historical patterns
    "mtd_cost": "Month-to-date cost",
    "mtd_dbu": "Month-to-date DBU usage",
    "days_elapsed": "Days elapsed in month",
    "days_remaining": "Days remaining in month",
    
    # Run rate projections
    "daily_run_rate": "mtd_cost / days_elapsed",
    "projected_monthly_cost": "daily_run_rate * days_in_month",
    
    # Historical comparisons
    "same_day_last_month": "Cost on same day last month",
    "same_day_last_year": "Cost on same day last year",
    "mom_growth_rate": "Month-over-month growth",
    "yoy_growth_rate": "Year-over-year growth",
    
    # Seasonality indicators
    "is_quarter_end": "Last month of quarter",
    "is_year_end": "December",
    "month_of_year": "1-12",
    
    # Workspace-level patterns
    "workspace_monthly_avg": "Average monthly cost per workspace",
    "workspace_growth_trend": "Workspace growth rate",
    
    # SKU mix features
    "jobs_pct": "Jobs SKU % of total",
    "sql_pct": "SQL SKU % of total",
    "dlt_pct": "DLT SKU % of total",
}
```

### Training SQL

```sql
-- Budget forecasting features from Gold layer
WITH monthly_costs AS (
    SELECT 
        DATE_TRUNC('month', usage_date) AS month_start,
        workspace_id,
        SUM(usage_quantity * list_price) AS monthly_cost,
        SUM(usage_quantity) AS monthly_dbu,
        COUNT(DISTINCT usage_date) AS active_days
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -365)
    GROUP BY DATE_TRUNC('month', usage_date), workspace_id
),
with_trends AS (
    SELECT *,
        LAG(monthly_cost, 1) OVER (PARTITION BY workspace_id ORDER BY month_start) AS prev_month_cost,
        LAG(monthly_cost, 12) OVER (PARTITION BY workspace_id ORDER BY month_start) AS prev_year_cost,
        (monthly_cost - LAG(monthly_cost, 1) OVER (PARTITION BY workspace_id ORDER BY month_start)) 
            / NULLIF(LAG(monthly_cost, 1) OVER (PARTITION BY workspace_id ORDER BY month_start), 0) AS mom_growth,
        AVG(monthly_cost) OVER (PARTITION BY workspace_id ORDER BY month_start ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) AS rolling_6m_avg
    FROM monthly_costs
)
SELECT * FROM with_trends
WHERE prev_month_cost IS NOT NULL
```

---

## Model 1.3: Chargeback Optimizer

**Problem Type:** Clustering + Attribution Modeling  
**Use Case:** Fairly allocate shared costs to business units  
**Business Value:** Accurate cost allocation, accountability, reduce disputes

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_usage`, `fact_job_run_timeline`, `dim_job`, `dim_workspace` |
| **Output** | Recommended allocation weights, attribution confidence |
| **Algorithm** | K-Means Clustering + Shapley Value Attribution |
| **Refresh** | Weekly |

### Feature Engineering

```python
# Chargeback Attribution Features
chargeback_features = {
    # Direct attribution
    "direct_job_cost": "Cost directly attributable to a job",
    "direct_user_cost": "Cost directly attributable to a user",
    "direct_workspace_cost": "Cost directly attributable to workspace",
    
    # Shared resource usage
    "shared_cluster_usage_pct": "% of shared cluster time used",
    "shared_warehouse_query_pct": "% of warehouse queries",
    "shared_storage_pct": "% of shared storage used",
    
    # Activity-based allocation
    "query_count_pct": "% of total queries",
    "job_run_count_pct": "% of total job runs",
    "data_processed_pct": "% of data processed",
    
    # Tag-based grouping
    "team_tag": "Team identifier from tags",
    "project_tag": "Project identifier from tags",
    "cost_center_tag": "Cost center from tags",
}
```

---

## Model 1.4: Job Cost Optimizer

**Problem Type:** Regression + Optimization  
**Use Case:** Predict job cost and recommend optimizations (from Jobs System Tables Dashboard patterns)  
**Business Value:** 20-50% cost reduction through right-sizing

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_usage`, `fact_job_run_timeline`, `fact_node_timeline`, `dim_cluster` |
| **Output** | Predicted cost, optimization recommendations, savings estimate |
| **Algorithm** | Gradient Boosting + Constraint Optimization |
| **Refresh** | Per job run |

### Feature Engineering (from Jobs System Tables Dashboard)

```python
# Job Cost Optimization Features
job_cost_features = {
    # Current configuration
    "worker_count": "Number of workers",
    "driver_memory_gb": "Driver memory",
    "worker_memory_gb": "Worker memory",
    "spot_instance_pct": "% of spot instances",
    "autoscaling_enabled": "Is autoscaling on?",
    "min_workers": "Min autoscale workers",
    "max_workers": "Max autoscale workers",
    
    # Utilization metrics (key for right-sizing)
    "avg_cpu_utilization": "Average CPU usage",
    "peak_cpu_utilization": "Peak CPU usage",
    "avg_memory_utilization": "Average memory usage",
    "peak_memory_utilization": "Peak memory usage",
    "cpu_wait_pct": "IO wait time",
    
    # Cost metrics
    "historical_avg_cost": "Average cost per run",
    "cost_per_dbu": "Cost per DBU",
    "cost_variability": "Standard deviation of cost",
    
    # Right-sizing indicators (from Jobs System Tables Dashboard pattern)
    "underutilization_score": "1 if CPU < 30%, else 0",
    "potential_savings_pct": "50% if avg_cpu < 30%, 30% if < 50%",
}
```

### Training SQL (Cost Savings Pattern from Dashboard)

```sql
-- Job cost optimization features (pattern from Jobs System Tables Dashboard)
WITH job_costs AS (
    SELECT
        f.job_id,
        j.name AS job_name,
        SUM(f.usage_quantity * f.list_price) AS total_cost,
        COUNT(DISTINCT f.usage_metadata_job_run_id) AS run_count,
        AVG(f.usage_quantity * f.list_price) AS avg_cost_per_run
    FROM ${catalog}.${gold_schema}.fact_usage f
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.job_id = j.job_id AND j.is_current = TRUE
    WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND f.job_id IS NOT NULL
    GROUP BY f.job_id, j.name
),
job_utilization AS (
    SELECT 
        jrt.job_id,
        AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_util,
        MAX(nt.cpu_user_percent + nt.cpu_system_percent) AS peak_cpu_util,
        AVG(nt.mem_used_percent) AS avg_mem_util,
        MAX(nt.mem_used_percent) AS peak_mem_util
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
    INNER JOIN ${catalog}.${gold_schema}.fact_node_timeline nt 
        ON jrt.cluster_id = nt.cluster_id
        AND nt.start_time BETWEEN jrt.period_start_time AND jrt.period_end_time
    WHERE jrt.period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY jrt.job_id
)
SELECT 
    jc.*,
    ju.avg_cpu_util,
    ju.peak_cpu_util,
    ju.avg_mem_util,
    ju.peak_mem_util,
    -- Potential savings calculation (from Jobs System Tables Dashboard)
    CASE 
        WHEN ju.avg_cpu_util < 30 THEN jc.total_cost * 0.5
        WHEN ju.avg_cpu_util < 50 THEN jc.total_cost * 0.3
        ELSE 0
    END AS potential_savings
FROM job_costs jc
LEFT JOIN job_utilization ju ON jc.job_id = ju.job_id
ORDER BY potential_savings DESC
```

---

## Model 1.5: Tag Recommender

**Problem Type:** Classification + NLP  
**Use Case:** Recommend tags for untagged resources based on usage patterns  
**Business Value:** Improve tag hygiene, enable accurate chargeback

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_usage`, `fact_job_run_timeline`, `dim_job` |
| **Output** | Recommended tags, confidence score |
| **Algorithm** | Random Forest + Job Name NLP Embedding |
| **Refresh** | Weekly |

### Feature Engineering

```python
# Tag Recommendation Features
tag_features = {
    # Job naming patterns
    "job_name_tokens": "Tokenized job name",
    "job_name_embedding": "BERT embedding of job name",
    "job_prefix": "First word/prefix of job name",
    
    # Usage patterns
    "primary_sku": "Most used SKU",
    "workspace_name": "Workspace name",
    "run_schedule_pattern": "Scheduled time pattern",
    
    # Similar jobs with tags
    "similar_job_tags": "Tags from similar jobs (by name)",
    "same_workspace_common_tags": "Common tags in workspace",
}
```

---

# 🔒 Security Agent Models (4 Models)

## Model 2.1: Security Threat Detector

**Problem Type:** Anomaly Detection + Classification  
**Use Case:** Identify suspicious access patterns and potential security threats  
**Business Value:** Early threat detection, compliance monitoring, incident prevention

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_table_lineage`, `fact_audit_events`, `dim_workspace` |
| **Output** | Threat score (0-1), threat_type classification, alert_priority |
| **Algorithm** | Isolation Forest + Rule-based Classification |
| **Refresh** | Real-time scoring, daily model updates |

### Feature Engineering

```python
# Security Threat Detection Features
security_features = {
    # User behavior patterns
    "login_count_24h": "Login attempts in last 24 hours",
    "unique_ip_count_24h": "Unique IPs in last 24 hours",
    "unique_location_count": "Unique geolocations",
    "failed_login_rate": "Failed / total logins",
    "off_hours_activity_rate": "Activity outside 6AM-10PM",
    "weekend_activity_rate": "Activity on weekends",
    
    # Access pattern features
    "tables_accessed_24h": "Unique tables accessed",
    "sensitive_table_access_count": "PII-tagged table access",
    "new_table_access_count": "First-time table access",
    "permission_change_count": "Permission modifications",
    
    # Data volume features
    "data_downloaded_bytes": "Data extracted volume",
    "unusual_data_export": "Export volume vs historical avg",
    "read_to_write_ratio": "Reads vs writes",
    
    # Temporal patterns
    "time_since_last_activity": "Gap since last action",
    "activity_burst_score": "Concentration of activity",
    
    # Peer comparison
    "activity_vs_peer_avg": "Activity level vs similar users",
    "table_access_vs_peer": "Table access patterns vs peers",
}
```

### Training SQL

```sql
-- Security feature extraction from Gold layer
WITH user_activity AS (
    SELECT 
        created_by AS user_id,
        DATE(event_time) AS event_date,
        COUNT(*) AS event_count,
        COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name)) AS tables_accessed,
        SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 THEN 1 ELSE 0 END) AS off_hours_events,
        SUM(CASE WHEN DAYOFWEEK(event_date) IN (1, 7) THEN 1 ELSE 0 END) AS weekend_events,
        SUM(CASE WHEN source_table_full_name LIKE '%pii%' OR source_table_full_name LIKE '%sensitive%' THEN 1 ELSE 0 END) AS sensitive_access
    FROM ${catalog}.${gold_schema}.fact_table_lineage
    WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY created_by, DATE(event_time)
),
with_rolling AS (
    SELECT *,
        AVG(event_count) OVER (PARTITION BY user_id ORDER BY event_date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS avg_events_7d,
        STDDEV(event_count) OVER (PARTITION BY user_id ORDER BY event_date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS std_events_7d,
        (event_count - avg_events_7d) / NULLIF(std_events_7d, 0) AS event_z_score
    FROM user_activity
)
SELECT * FROM with_rolling WHERE avg_events_7d IS NOT NULL
```

---

## Model 2.2: Data Exfiltration Detector

**Problem Type:** Anomaly Detection  
**Use Case:** Detect unusual data extraction patterns that may indicate data theft  
**Business Value:** Prevent data breaches, compliance with data protection regulations

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_table_lineage`, `fact_query_history` |
| **Output** | Exfiltration risk score, volume anomaly flag |
| **Algorithm** | Isolation Forest + Threshold Rules |
| **Refresh** | Real-time |

### Feature Engineering

```python
# Data Exfiltration Features
exfiltration_features = {
    # Volume anomalies
    "bytes_read_24h": "Total bytes read in 24 hours",
    "bytes_read_vs_avg": "Ratio to user's average",
    "bytes_read_vs_peer": "Ratio to peer average",
    "large_query_count": "Queries reading > 1GB",
    
    # Pattern anomalies
    "unique_tables_read": "Tables accessed",
    "first_time_table_access": "New tables accessed",
    "export_statement_count": "COPY/EXPORT commands",
    
    # Timing anomalies
    "off_hours_data_access": "Data access outside hours",
    "bulk_download_burst": "High volume in short time",
}
```

---

## Model 2.3: Privilege Escalation Detector

**Problem Type:** Classification  
**Use Case:** Detect potential privilege abuse or escalation attempts  
**Business Value:** Prevent unauthorized access, audit compliance

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_audit_events`, `fact_table_lineage` |
| **Output** | Escalation risk score, suspicious_action flag |
| **Algorithm** | Gradient Boosting Classifier |
| **Refresh** | Real-time |

### Feature Engineering

```python
# Privilege Escalation Features
privilege_features = {
    # Permission changes
    "grant_count_24h": "GRANT statements in 24h",
    "role_change_count": "Role modifications",
    "self_permission_grant": "User granting to self",
    
    # Access pattern changes
    "new_schema_access": "First-time schema access",
    "admin_action_count": "Administrative actions",
    "cross_workspace_access": "Access across workspaces",
    
    # Anomaly indicators
    "permission_velocity": "Rate of permission changes",
    "unusual_admin_time": "Admin actions at unusual times",
}
```

---

## Model 2.4: User Behavior Baseline

**Problem Type:** Clustering + Anomaly Detection  
**Use Case:** Establish normal behavior baselines for each user to detect deviations  
**Business Value:** Personalized security monitoring, reduced false positives

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_table_lineage`, `fact_query_history`, `fact_job_run_timeline` |
| **Output** | User cluster assignment, deviation score |
| **Algorithm** | DBSCAN Clustering + Autoencoder |
| **Refresh** | Weekly baseline update |

---

# ⚡ Performance Agent Models (6 Models)

## Model 3.1: Query Performance Forecaster

**Problem Type:** Regression  
**Use Case:** Forecast query execution time for capacity planning and SLA management  
**Business Value:** Accurate SLA commitments, better capacity planning

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_query_history`, `dim_warehouse` |
| **Output** | Predicted duration (seconds), confidence interval |
| **Algorithm** | Gradient Boosting + Query Embedding |
| **Refresh** | Real-time prediction, daily retraining |

### Feature Engineering

```python
# Query Performance Prediction Features
query_features = {
    # Query characteristics
    "query_text_length": "LENGTH(statement_text)",
    "query_hash": "Hash for similar query detection",
    "statement_type": "SELECT/INSERT/MERGE/etc",
    "table_count": "Number of tables accessed",
    "join_count": "Number of JOINs",
    "subquery_count": "Number of subqueries",
    "has_aggregation": "Contains GROUP BY",
    "has_window_function": "Contains OVER clause",
    
    # Historical query performance
    "similar_query_avg_duration": "Avg duration of similar queries",
    "query_historical_avg": "Avg duration for this exact query",
    "query_historical_p95": "P95 duration for this query",
    
    # Data volume features (from DBSQL Warehouse Advisor patterns)
    "estimated_rows_scanned": "From query plan",
    "historical_bytes_read": "Actual bytes from similar queries",
    "historical_spill_bytes": "Spill from similar queries",
    
    # Warehouse features
    "warehouse_size_encoded": "XS=1, S=2, M=3, L=4, etc",
    "warehouse_cluster_count": "Number of clusters",
    "warehouse_current_load": "Concurrent queries",
    "warehouse_queue_depth": "Queries in queue",
    
    # Time features
    "hour_of_day": "Query submission hour",
    "is_peak_hours": "9 AM - 5 PM weekdays",
    "day_of_week": "Query submission day",
}
```

---

## Model 3.2: Warehouse Auto-Scaler Optimizer

**Problem Type:** Time Series + Optimization  
**Use Case:** Predict optimal warehouse size based on workload patterns  
**Business Value:** 20-40% cost savings through right-sizing (from DBSQL Warehouse Advisor insights)

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_query_history`, `fact_usage`, `dim_warehouse` |
| **Output** | Recommended size, predicted queue time, cost impact |
| **Algorithm** | Prophet + Constraint Optimization |
| **Refresh** | Hourly predictions |

### Feature Engineering (from DBSQL Warehouse Advisor patterns)

```python
# Warehouse Optimization Features
warehouse_features = {
    # Query load patterns
    "queries_per_hour": "Query volume by hour",
    "concurrent_query_avg": "Average concurrent queries",
    "concurrent_query_peak": "Peak concurrent queries",
    "queue_time_avg": "Average queue wait time",
    "queue_time_p95": "P95 queue wait time",
    
    # Performance flags (from DBSQL Warehouse Advisor)
    "high_queue_rate": "% queries with queue > 10% of runtime",
    "high_spill_rate": "% queries with spill",
    "high_data_volume_rate": "% queries reading > 10GB",
    
    # Utilization patterns
    "active_hours_per_day": "Hours with queries",
    "weekend_utilization": "Weekend query volume",
    "night_utilization": "Night query volume",
    
    # Cost metrics
    "cost_per_query": "Average cost per query",
    "dbu_per_query": "DBUs consumed per query",
}
```

---

## Model 3.3: Query Optimization Recommender

**Problem Type:** Multi-class Classification  
**Use Case:** Recommend query optimizations based on query patterns (from DBSQL Warehouse Advisor)  
**Business Value:** Faster queries, reduced compute costs

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_query_history` |
| **Output** | Optimization recommendations, expected improvement |
| **Algorithm** | Multi-label Classification |
| **Refresh** | Per query |

### Feature Engineering

```python
# Query Optimization Features (from DBSQL Warehouse Advisor patterns)
optimization_features = {
    # Performance indicators
    "query_efficiency_ratio": "CPU time / runtime ratio",
    "spill_to_read_ratio": "Spill bytes / read bytes",
    "result_fetch_ratio": "Result time / total time",
    
    # Query patterns
    "has_select_star": "SELECT * usage",
    "missing_partition_filter": "No partition pruning",
    "cartesian_join": "Cross join detected",
    "excessive_shuffle": "High shuffle bytes",
    
    # Optimization opportunities
    "cacheable": "Query result could be cached",
    "z_order_candidate": "Would benefit from Z-ORDER",
    "materialization_candidate": "Should be materialized",
}
```

---

## Model 3.4: Cluster Capacity Planner

**Problem Type:** Time Series Forecasting + Optimization  
**Use Case:** Recommend optimal cluster sizing based on workload patterns  
**Business Value:** Right-sized clusters, cost optimization

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_node_timeline`, `fact_usage`, `dim_cluster` |
| **Output** | Recommended size, expected utilization, cost savings |
| **Algorithm** | Prophet/ARIMA + Constraint Optimization |
| **Refresh** | Weekly recommendations |

### Training SQL

```sql
-- Cluster capacity planning from Gold layer
WITH cluster_utilization AS (
    SELECT 
        nt.cluster_id,
        c.cluster_name,
        c.owned_by,
        c.worker_count,
        c.min_autoscale_workers,
        c.max_autoscale_workers,
        DATE(nt.start_time) AS util_date,
        AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_util,
        MAX(nt.cpu_user_percent + nt.cpu_system_percent) AS peak_cpu_util,
        AVG(nt.mem_used_percent) AS avg_mem_util,
        MAX(nt.mem_used_percent) AS peak_mem_util,
        AVG(nt.cpu_wait_percent) AS avg_io_wait
    FROM ${catalog}.${gold_schema}.fact_node_timeline nt
    LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c 
        ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
    WHERE nt.start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY nt.cluster_id, c.cluster_name, c.owned_by, c.worker_count, 
             c.min_autoscale_workers, c.max_autoscale_workers, DATE(nt.start_time)
),
cluster_costs AS (
    SELECT 
        cluster_id,
        SUM(usage_quantity * list_price) AS total_cost_30d
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND cluster_id IS NOT NULL
    GROUP BY cluster_id
)
SELECT 
    cu.*,
    cc.total_cost_30d,
    -- Sizing recommendation
    CASE
        WHEN cu.avg_cpu_util < 30 AND cu.peak_cpu_util < 60 THEN 'DOWNSIZE_AGGRESSIVE'
        WHEN cu.avg_cpu_util < 50 AND cu.peak_cpu_util < 80 THEN 'DOWNSIZE_MODERATE'
        WHEN cu.avg_cpu_util > 80 OR cu.peak_cpu_util > 95 THEN 'UPSIZE'
        ELSE 'OPTIMAL'
    END AS sizing_recommendation,
    -- Autoscaling recommendation
    CASE
        WHEN cu.min_autoscale_workers IS NULL AND cu.worker_count > 1 THEN 'ENABLE_AUTOSCALING'
        ELSE 'OK'
    END AS autoscale_recommendation
FROM cluster_utilization cu
LEFT JOIN cluster_costs cc ON cu.cluster_id = cc.cluster_id
```

---

## Model 3.5: DBR Migration Risk Scorer

**Problem Type:** Classification  
**Use Case:** Predict risk of DBR version upgrade for each job (from DBR Migration Dashboard patterns)  
**Business Value:** Safer migrations, reduced downtime

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_job_run_timeline`, `dim_cluster`, `dim_job` |
| **Output** | Migration risk score (0-100), breaking_change_probability |
| **Algorithm** | Gradient Boosting Classifier |
| **Refresh** | Per migration assessment |

### Feature Engineering (from DBR Migration Dashboard)

```python
# DBR Migration Risk Features
migration_features = {
    # Current state
    "current_dbr_version": "Current DBR version",
    "target_dbr_version": "Target DBR version",
    "major_version_jump": "Number of major versions",
    
    # Job characteristics
    "uses_spark_sql": "Uses Spark SQL",
    "uses_ml_runtime": "Uses ML libraries",
    "uses_delta": "Uses Delta Lake",
    "library_count": "Number of custom libraries",
    
    # Historical stability
    "historical_success_rate": "Job success rate",
    "historical_failure_types": "Common failure types",
    "last_successful_migration": "Days since last DBR change",
    
    # Dependency complexity
    "upstream_job_count": "Upstream dependencies",
    "downstream_job_count": "Downstream dependencies",
    "table_count": "Tables accessed",
}
```

---

## Model 3.6: Cache Hit Predictor

**Problem Type:** Binary Classification  
**Use Case:** Predict whether a query will hit cache  
**Business Value:** Better capacity planning, faster query routing

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_query_history` |
| **Output** | Cache hit probability, freshness_score |
| **Algorithm** | Logistic Regression |
| **Refresh** | Per query |

---

# 🔄 Reliability Agent Models (5 Models)

## Model 4.1: Job Failure Predictor

**Problem Type:** Binary Classification  
**Use Case:** Predict job failures before execution to enable proactive intervention  
**Business Value:** Reduce failed runs, improve SLA compliance

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_job_run_timeline`, `dim_job`, `dim_cluster`, `fact_node_timeline` |
| **Output** | Failure probability (0-1), risk_level (LOW/MEDIUM/HIGH) |
| **Algorithm** | Gradient Boosting (XGBoost/LightGBM) |
| **Refresh** | Pre-run prediction, daily retraining |

### Feature Engineering

```python
# Job Failure Prediction Features
failure_features = {
    # Historical job performance
    "historical_failure_rate": "COUNT(failures) / COUNT(*) for job",
    "recent_failure_rate_7d": "Failure rate in last 7 days",
    "consecutive_failures": "Current streak of failures",
    "time_since_last_success_hours": "Hours since last successful run",
    "time_since_last_failure_hours": "Hours since last failure",
    
    # Job configuration
    "task_count": "Number of tasks in job",
    "dependency_count": "Number of upstream dependencies",
    "has_retry_policy": "Whether retry is configured",
    "max_retries": "Maximum retry count",
    "timeout_minutes": "Configured timeout",
    
    # Cluster features
    "cluster_memory_gb": "Total cluster memory",
    "cluster_cores": "Total cluster cores",
    "worker_count": "Number of workers",
    "is_autoscaling": "Whether autoscaling enabled",
    "dbr_version_major": "DBR major version",
    
    # Historical runtime
    "avg_runtime_minutes": "Historical average runtime",
    "runtime_std_dev": "Runtime variability",
    "p99_runtime": "99th percentile runtime",
    
    # Resource utilization (from historical runs)
    "avg_cpu_utilization": "Average CPU usage",
    "peak_memory_utilization": "Peak memory in recent runs",
    "spill_rate": "Rate of disk spills",
    
    # Time features
    "hour_of_day": "Scheduled run hour",
    "day_of_week": "Scheduled run day",
    "is_business_hours": "9 AM - 6 PM weekdays",
}
```

### Training SQL

```sql
-- Job failure prediction features from Gold layer
WITH job_history AS (
    SELECT 
        f.job_id,
        f.run_id,
        f.cluster_id,
        f.result_state,
        TIMESTAMPDIFF(MINUTE, f.period_start_time, f.period_end_time) AS duration_minutes,
        f.period_start_time,
        -- Historical failure rate
        AVG(CASE WHEN f.result_state != 'SUCCEEDED' THEN 1 ELSE 0 END) OVER (
            PARTITION BY f.job_id 
            ORDER BY f.period_start_time 
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ) AS recent_failure_rate,
        -- Consecutive failures
        SUM(CASE WHEN f.result_state != 'SUCCEEDED' THEN 1 ELSE 0 END) OVER (
            PARTITION BY f.job_id 
            ORDER BY f.period_start_time 
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS historical_failures,
        COUNT(*) OVER (PARTITION BY f.job_id ORDER BY f.period_start_time ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS total_runs
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
    WHERE f.result_state IS NOT NULL
        AND f.period_start_time >= CURRENT_DATE() - INTERVAL 90 DAYS
),
with_features AS (
    SELECT 
        jh.*,
        j.name AS job_name,
        j.task_count,
        c.worker_count,
        c.dbr_version,
        HOUR(jh.period_start_time) AS hour_of_day,
        DAYOFWEEK(jh.period_start_time) AS day_of_week,
        CASE WHEN jh.result_state IN ('ERROR', 'FAILED', 'TIMED_OUT') THEN 1 ELSE 0 END AS is_failure
    FROM job_history jh
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON jh.job_id = j.job_id AND j.is_current = TRUE
    LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON jh.cluster_id = c.cluster_id AND c.is_current = TRUE
)
SELECT * FROM with_features WHERE total_runs >= 10
```

---

## Model 4.2: Job Duration Forecaster

**Problem Type:** Regression  
**Use Case:** Predict job runtime for scheduling optimization  
**Business Value:** Better scheduling, accurate SLA estimates

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_job_run_timeline`, `dim_job` |
| **Output** | Predicted duration (minutes), confidence interval |
| **Algorithm** | Gradient Boosting Regression |
| **Refresh** | Per job run |

### Feature Engineering

```python
# Job Duration Features
duration_features = {
    # Historical performance
    "historical_avg_duration": "Average runtime",
    "historical_p50_duration": "Median runtime",
    "historical_p95_duration": "P95 runtime",
    "duration_trend": "Is duration increasing/decreasing",
    
    # Data volume indicators
    "expected_data_volume": "Expected input data size",
    "upstream_freshness": "Age of upstream data",
    
    # Resource configuration
    "cluster_size": "Cluster worker count",
    "spark_partition_count": "Expected partitions",
}
```

---

## Model 4.3: SLA Breach Predictor

**Problem Type:** Binary Classification  
**Use Case:** Predict SLA breaches before they happen  
**Business Value:** Proactive alerts, improved SLA compliance

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_job_run_timeline`, custom SLA table |
| **Output** | Breach probability, expected completion time |
| **Algorithm** | Gradient Boosting |
| **Refresh** | Per job run |

### Feature Engineering

```python
# SLA Breach Features
sla_features = {
    # SLA context
    "sla_deadline": "Expected completion time",
    "time_remaining": "Time until SLA deadline",
    "predicted_duration": "From duration forecaster",
    "buffer_time": "SLA deadline - predicted completion",
    
    # Historical SLA performance
    "historical_sla_compliance": "% of runs meeting SLA",
    "recent_sla_breaches": "Breaches in last 7 days",
    "breach_severity_avg": "Average breach duration",
    
    # Current run status
    "current_progress_pct": "Estimated % complete",
    "tasks_completed": "Tasks done / total tasks",
    "current_runtime": "Time since job started",
}
```

---

## Model 4.4: Retry Success Predictor

**Problem Type:** Binary Classification  
**Use Case:** Predict if a retry will succeed (from Jobs System Tables Dashboard repair patterns)  
**Business Value:** Avoid wasted retries, faster incident response

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_job_run_timeline` |
| **Output** | Retry success probability, recommended_action |
| **Algorithm** | Gradient Boosting |
| **Refresh** | On failure |

### Feature Engineering (from Jobs System Tables Dashboard repair patterns)

```python
# Retry Success Features
retry_features = {
    # Failure context
    "failure_type": "Termination code",
    "error_message_embedding": "Embedding of error message",
    "failure_stage": "Stage where failure occurred",
    
    # Historical retry patterns
    "historical_retry_success_rate": "Retry success rate for this job",
    "same_error_retry_success": "Success rate for same error type",
    "retry_count_in_run": "Number of retries already attempted",
    
    # Resource state
    "cluster_health": "Cluster health at failure time",
    "memory_pressure": "OOM indicators",
    
    # Recommendations
    "should_auto_retry": "Probability of retry success > 50%",
    "recommended_wait_time": "Optimal wait before retry",
    "requires_investigation": "Probability of retry success < 20%",
}
```

---

## Model 4.5: Pipeline Health Scorer

**Problem Type:** Regression (Scoring)  
**Use Case:** Overall pipeline reliability score combining multiple factors  
**Business Value:** Unified health metric for leadership dashboards

| Aspect | Details |
|--------|---------|
| **Gold Tables** | All job-related Gold tables |
| **Output** | Health score (0-100), component scores |
| **Algorithm** | Ensemble of component models |
| **Refresh** | Daily |

### Score Components

```python
# Pipeline Health Score Components
health_components = {
    "success_rate_score": "Weight: 30%, based on 7-day success rate",
    "duration_stability_score": "Weight: 20%, based on runtime variability",
    "sla_compliance_score": "Weight: 25%, based on SLA adherence",
    "error_diversity_score": "Weight: 10%, penalty for many error types",
    "recovery_speed_score": "Weight: 15%, time to recover from failures",
}
```

---

# ✅ Quality Agent Models (3 Models)

## Model 5.1: Data Freshness Predictor

**Problem Type:** Regression  
**Use Case:** Predict when data will arrive for downstream dependencies  
**Business Value:** Better scheduling, accurate data availability SLAs

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_job_run_timeline`, `fact_table_lineage` |
| **Output** | Predicted arrival time, confidence interval |
| **Algorithm** | Time Series + Regression |
| **Refresh** | Hourly |

### Feature Engineering

```python
# Data Freshness Features
freshness_features = {
    # Historical patterns
    "historical_avg_arrival_time": "Average arrival time",
    "historical_arrival_variability": "Standard deviation of arrival",
    "typical_arrival_hour": "Most common arrival hour",
    
    # Upstream dependencies
    "upstream_job_status": "Status of upstream jobs",
    "upstream_completion_time": "When upstream completed",
    "upstream_delay_propagation": "Historical delay correlation",
    
    # Current state
    "upstream_started": "Has upstream job started?",
    "upstream_progress": "Estimated progress of upstream",
}
```

---

## Model 5.2: Schema Drift Detector

**Problem Type:** Anomaly Detection  
**Use Case:** Detect unexpected schema changes that may break pipelines  
**Business Value:** Prevent pipeline failures, maintain data contracts

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `information_schema` views, `fact_table_lineage` |
| **Output** | Drift risk score, breaking_change_flag |
| **Algorithm** | Rule-based + Anomaly Detection |
| **Refresh** | On schema change |

### Feature Engineering

```python
# Schema Drift Features
drift_features = {
    # Column changes
    "columns_added": "New columns added",
    "columns_removed": "Columns removed (breaking)",
    "columns_renamed": "Columns renamed (breaking)",
    "type_changes": "Data type changes",
    
    # Table changes
    "partition_change": "Partition scheme changed",
    "clustering_change": "Clustering changed",
    
    # Impact assessment
    "downstream_table_count": "Tables dependent on this",
    "downstream_job_count": "Jobs reading this table",
    "last_schema_change_days": "Days since last change",
}
```

---

## Model 5.3: Data Quality Degradation Forecaster

**Problem Type:** Time Series Forecasting  
**Use Case:** Predict future data quality issues based on trends  
**Business Value:** Proactive quality management, early intervention

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_data_quality_monitoring_table_results` |
| **Output** | Predicted quality score, degradation_probability |
| **Algorithm** | Prophet / ARIMA |
| **Refresh** | Daily |

### Feature Engineering

```python
# Quality Degradation Features
quality_features = {
    # Historical quality trends
    "quality_score_trend": "Is score improving/degrading?",
    "violation_rate_trend": "Is violation rate increasing?",
    "critical_violation_trend": "Critical violation rate trend",
    
    # Pattern indicators
    "seasonal_quality_pattern": "Quality varies by day/week",
    "source_system_health": "Upstream source quality",
    
    # Risk factors
    "recent_schema_changes": "Schema changed recently",
    "recent_pipeline_changes": "Pipeline modified recently",
    "new_data_source": "New data source added",
}
```

---

# Implementation Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Gold Layer Tables                            │
│  (fact_usage, fact_job_run_timeline, fact_query_history, etc.)      │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Feature Engineering                            │
│                                                                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │ 💰 Cost   │  │ 🔒 Security│  │ ⚡ Perf   │  │ 🔄 Reliab │        │
│  │ Features  │  │ Features   │  │ Features  │  │ Features  │        │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘        │
│                                                                      │
│              Stored in: Feature Store (Unity Catalog)                │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MLflow Training Pipeline                        │
│                                                                      │
│  💰 Cost Agent Models (5)        🔒 Security Agent Models (4)       │
│  ⚡ Performance Agent Models (6)  🔄 Reliability Agent Models (5)   │
│  ✅ Quality Agent Models (3)                                        │
│                                                                      │
│              Tracked in: MLflow Experiments                          │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Model Registry (Unity Catalog)                  │
│                                                                      │
│  health_monitor.cost_anomaly_detector                               │
│  health_monitor.budget_forecaster                                   │
│  health_monitor.security_threat_detector                            │
│  health_monitor.job_failure_predictor                               │
│  ... 19 more models                                                  │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Model Serving Endpoints                         │
│                                                                      │
│  Real-time: cost-anomaly, security-threat, job-failure, query-perf  │
│  Batch: budget-forecast, capacity-plan, sla-breach                  │
│                                                                      │
│              Predictions logged to: Inference Tables                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

# Asset Bundle Configuration

```yaml
# resources/ml/ml_training_pipeline.yml
resources:
  jobs:
    health_monitor_ml_training:
      name: "[${bundle.target}] Health Monitor - ML Training Pipeline"
      
      environments:
        - environment_key: ml_env
          spec:
            environment_version: "4"
            dependencies:
              - mlflow>=2.10.0
              - scikit-learn>=1.3.0
              - xgboost>=2.0.0
              - lightgbm>=4.0.0
              - prophet>=1.1.0
      
      tasks:
        # ========================================
        # 💰 COST AGENT MODELS
        # ========================================
        - task_key: train_cost_anomaly_detector
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/cost/train_cost_anomaly.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
        
        - task_key: train_budget_forecaster
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/cost/train_budget_forecaster.py
        
        - task_key: train_job_cost_optimizer
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/cost/train_job_cost_optimizer.py
        
        # ========================================
        # 🔒 SECURITY AGENT MODELS
        # ========================================
        - task_key: train_security_threat_detector
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/security/train_threat_detector.py
        
        - task_key: train_exfiltration_detector
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/security/train_exfiltration_detector.py
        
        # ========================================
        # ⚡ PERFORMANCE AGENT MODELS
        # ========================================
        - task_key: train_query_forecaster
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/performance/train_query_forecaster.py
        
        - task_key: train_warehouse_optimizer
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/performance/train_warehouse_optimizer.py
        
        - task_key: train_capacity_planner
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/performance/train_capacity_planner.py
        
        - task_key: train_dbr_migration_risk
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/performance/train_dbr_migration_risk.py
        
        # ========================================
        # 🔄 RELIABILITY AGENT MODELS
        # ========================================
        - task_key: train_job_failure_predictor
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/reliability/train_failure_predictor.py
        
        - task_key: train_duration_forecaster
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/reliability/train_duration_forecaster.py
        
        - task_key: train_sla_breach_predictor
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/reliability/train_sla_breach.py
        
        - task_key: train_retry_success_predictor
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/reliability/train_retry_success.py
        
        # ========================================
        # ✅ QUALITY AGENT MODELS
        # ========================================
        - task_key: train_freshness_predictor
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/quality/train_freshness_predictor.py
        
        - task_key: train_schema_drift_detector
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/quality/train_schema_drift.py
        
        # ========================================
        # MODEL REGISTRATION & DEPLOYMENT
        # ========================================
        - task_key: register_all_models
          depends_on:
            - task_key: train_cost_anomaly_detector
            - task_key: train_budget_forecaster
            - task_key: train_job_cost_optimizer
            - task_key: train_security_threat_detector
            - task_key: train_exfiltration_detector
            - task_key: train_query_forecaster
            - task_key: train_warehouse_optimizer
            - task_key: train_capacity_planner
            - task_key: train_dbr_migration_risk
            - task_key: train_job_failure_predictor
            - task_key: train_duration_forecaster
            - task_key: train_sla_breach_predictor
            - task_key: train_retry_success_predictor
            - task_key: train_freshness_predictor
            - task_key: train_schema_drift_detector
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/deployment/register_all_models.py
        
        - task_key: deploy_serving_endpoints
          depends_on:
            - task_key: register_all_models
          environment_key: ml_env
          notebook_task:
            notebook_path: ../src/ml/deployment/deploy_endpoints.py
      
      schedule:
        quartz_cron_expression: "0 0 3 * * ?"  # Daily at 3 AM
        pause_status: PAUSED
      
      tags:
        environment: ${bundle.target}
        project: health_monitor
        layer: ml
        job_type: training
```

---

# Model Serving Endpoints

| Agent | Endpoint | Model | Latency | Use Case |
|-------|----------|-------|---------|----------|
| 💰 Cost | `/cost-anomaly` | Cost Anomaly Detector | <100ms | Real-time cost alerts |
| 💰 Cost | `/budget-forecast` | Budget Forecaster | <500ms | Daily budget predictions |
| 🔒 Security | `/security-threat` | Threat Detector | <50ms | Real-time threat scoring |
| 🔒 Security | `/exfiltration-risk` | Exfiltration Detector | <100ms | Real-time data protection |
| ⚡ Performance | `/query-forecast` | Query Forecaster | <100ms | Pre-query latency prediction |
| ⚡ Performance | `/warehouse-recommend` | Warehouse Optimizer | <200ms | Sizing recommendations |
| 🔄 Reliability | `/job-failure-risk` | Failure Predictor | <100ms | Pre-run failure probability |
| 🔄 Reliability | `/retry-success` | Retry Predictor | <100ms | Should we retry? |
| 🔄 Reliability | `/sla-breach-risk` | SLA Breach Predictor | <100ms | SLA compliance alerts |

---

# Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Models Trained** | 23 models | Count of registered models |
| **Feature Store Tables** | 10 feature tables | One per domain + shared |
| **Classification Accuracy** | >85% F1 | MLflow metrics |
| **Regression MAPE** | <15% | MLflow metrics |
| **Serving Latency** | <100ms p99 | Endpoint metrics |
| **Inference Coverage** | 100% | Daily data scored |
| **Alert Precision** | >90% | False positive rate |
| **Cost Savings Identified** | $X/month | From optimization models |

---

# References

### Official Databricks Documentation
- [MLflow Model Registry in Unity Catalog](https://docs.databricks.com/mlflow/model-registry-uc.html)
- [Feature Store in Unity Catalog](https://docs.databricks.com/machine-learning/feature-store/uc/feature-tables-uc.html)
- [Model Serving](https://docs.databricks.com/machine-learning/model-serving/index.html)
- [Lakehouse Monitoring for ML](https://docs.databricks.com/lakehouse-monitoring/index.html)

### Inspiration Dashboards & Patterns
- **DBSQL Warehouse Advisor** - Query efficiency patterns
- **Jobs System Tables Dashboard** - Repair cost, cost savings patterns
- **DBR Migration Dashboard** - Migration risk patterns
- **Workflow Advisor** - Job optimization patterns
