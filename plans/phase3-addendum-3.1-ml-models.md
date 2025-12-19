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
    "daily_cost": "SUM(usage_quantity) * list_price (join dim_sku)",
    
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
-- NOTE: fact_usage requires join to dim_sku for list_price
WITH daily_cost AS (
    SELECT 
        f.usage_date,
        f.workspace_id,
        w.workspace_name,
        SUM(f.usage_quantity) AS daily_dbu,
        SUM(f.usage_quantity * s.list_price) AS daily_cost,
        COUNT(DISTINCT f.sku_name) AS sku_count,
        COUNT(DISTINCT f.usage_metadata_cluster_id) AS cluster_count,
        COUNT(DISTINCT f.usage_metadata_job_id) AS job_count
    FROM ${catalog}.${gold_schema}.fact_usage f
    LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
        ON f.workspace_id = w.workspace_id AND w.is_current = TRUE
    LEFT JOIN ${catalog}.${gold_schema}.dim_sku s
        ON f.sku_name = s.sku_name
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
-- NOTE: fact_usage requires join to dim_sku for list_price
WITH monthly_costs AS (
    SELECT 
        DATE_TRUNC('month', f.usage_date) AS month_start,
        f.workspace_id,
        SUM(f.usage_quantity * s.list_price) AS monthly_cost,
        SUM(f.usage_quantity) AS monthly_dbu,
        COUNT(DISTINCT f.usage_date) AS active_days
    FROM ${catalog}.${gold_schema}.fact_usage f
    LEFT JOIN ${catalog}.${gold_schema}.dim_sku s ON f.sku_name = s.sku_name
    WHERE f.usage_date >= DATE_ADD(CURRENT_DATE(), -365)
    GROUP BY DATE_TRUNC('month', f.usage_date), f.workspace_id
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
-- NOTE: fact_usage.usage_metadata_job_id links to jobs, requires dim_sku join for pricing
WITH job_costs AS (
    SELECT
        f.usage_metadata_job_id AS job_id,
        j.name AS job_name,
        SUM(f.usage_quantity * s.list_price) AS total_cost,
        COUNT(DISTINCT f.usage_metadata_job_run_id) AS run_count,
        AVG(f.usage_quantity * s.list_price) AS avg_cost_per_run
    FROM ${catalog}.${gold_schema}.fact_usage f
    LEFT JOIN ${catalog}.${gold_schema}.dim_sku s ON f.sku_name = s.sku_name
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
        ON f.workspace_id = j.workspace_id 
        AND f.usage_metadata_job_id = j.job_id 
        AND j.is_current = TRUE
    WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND f.usage_metadata_job_id IS NOT NULL
    GROUP BY f.usage_metadata_job_id, j.name
),
-- NOTE: fact_job_run_timeline uses compute_ids_json (JSON array) for cluster linkage
job_utilization AS (
    SELECT 
        jrt.job_id,
        AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_util,
        MAX(nt.cpu_user_percent + nt.cpu_system_percent) AS peak_cpu_util,
        AVG(nt.mem_used_percent) AS avg_mem_util,
        MAX(nt.mem_used_percent) AS peak_mem_util
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
    -- Parse cluster_id from compute_ids_json array
    LATERAL VIEW EXPLODE(from_json(jrt.compute_ids_json, 'array<string>')) AS cluster_id
    INNER JOIN ${catalog}.${gold_schema}.fact_node_timeline nt 
        ON cluster_id = nt.cluster_id
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
| **Gold Tables** | `fact_table_lineage`, `fact_audit_logs`, `dim_workspace` |
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
    # Volume anomalies (using fact_query_history.read_bytes)
    "read_bytes_24h": "Total bytes read in 24 hours",
    "read_bytes_vs_avg": "Ratio to user's average",
    "read_bytes_vs_peer": "Ratio to peer average",
    "large_query_count": "Queries with read_bytes > 1GB",
    
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
| **Gold Tables** | `fact_audit_logs`, `fact_table_lineage` |
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
    # NOTE: fact_query_history uses read_bytes, spilled_local_bytes
    "estimated_rows_scanned": "From query plan",
    "historical_read_bytes": "Actual read_bytes from similar queries",
    "historical_spill_bytes": "spilled_local_bytes from similar queries",
    
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
        f.usage_metadata_cluster_id AS cluster_id,
        SUM(f.usage_quantity * s.list_price) AS total_cost_30d
    FROM ${catalog}.${gold_schema}.fact_usage f
    LEFT JOIN ${catalog}.${gold_schema}.dim_sku s ON f.sku_name = s.sku_name
    WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
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
-- NOTE: fact_job_run_timeline does not have cluster_id column
-- Use compute_ids_json for cluster information if needed
WITH job_history AS (
    SELECT 
        f.job_id,
        f.run_id,
        f.compute_ids_json,  -- JSON array of cluster IDs
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

## 🆕 Dashboard Pattern Enhancements for ML Models

Based on analysis of real-world Databricks dashboards (see [phase3-use-cases.md SQL Patterns Catalog](./phase3-use-cases.md#-sql-query-patterns-catalog-from-dashboard-analysis)), the following feature engineering and model enhancements should be implemented:

### New Features from Dashboard Patterns

#### Period Comparison Features (Pattern 1, 2)
**Source:** Azure Serverless Cost Dashboard

Add to **Cost Anomaly Detector** and **Budget Forecaster**:
```python
# Period comparison features for anomaly detection
period_features = {
    # Short-term growth features
    "cost_7d_vs_prior_7d_growth": "(last_7d_cost - prior_7d_cost) / NULLIF(prior_7d_cost, 0)",
    "cost_7d_vs_prior_7d_abs_change": "last_7d_cost - prior_7d_cost",

    # Medium-term growth features
    "cost_30d_vs_prior_30d_growth": "(last_30d_cost - prior_30d_cost) / NULLIF(prior_30d_cost, 0)",
    "cost_30d_vs_prior_30d_abs_change": "last_30d_cost - prior_30d_cost",

    # Acceleration feature (growth of growth)
    "growth_acceleration": "cost_7d_growth - prior_cost_7d_growth",

    # Consistency feature
    "growth_consistency": "1 - STDDEV(daily_growth) / NULLIF(AVG(daily_growth), 0)",
}
```

#### P90 Deviation Features (Pattern 3)
**Source:** Azure Serverless Cost Dashboard

Add to **Cost Anomaly Detector** and **Job Cost Optimizer**:
```python
# Outlier detection features at job level
outlier_features = {
    # Current vs historical percentiles
    "cost_vs_p50_ratio": "current_run_cost / NULLIF(job_p50_cost, 0)",
    "cost_vs_p90_ratio": "current_run_cost / NULLIF(job_p90_cost, 0)",
    "cost_vs_p99_ratio": "current_run_cost / NULLIF(job_p99_cost, 0)",

    # Deviation from baseline
    "p90_deviation_pct": "(current_run_cost - job_p90_cost) / NULLIF(job_p90_cost, 0) * 100",

    # Is outlier flag (can be used as label for semi-supervised learning)
    "is_statistical_outlier": "CASE WHEN z_score > 3 OR cost_vs_p90_ratio > 2 THEN 1 ELSE 0 END",

    # Historical outlier frequency
    "job_outlier_frequency": "COUNT(CASE WHEN run_cost > p90_cost * 1.5) / NULLIF(total_runs, 0)",
}
```

#### Entity Type Features (Pattern 11)
**Source:** LakeFlow System Tables Dashboard

Add to all cost-related models:
```python
# Entity type classification features
entity_features = {
    "is_serverless": "CASE WHEN is_serverless = TRUE THEN 1 ELSE 0 END",
    "is_job": "CASE WHEN billing_origin_product = 'JOBS' THEN 1 ELSE 0 END",
    "is_pipeline": "CASE WHEN billing_origin_product IN ('DLT', 'LAKEFLOW_CONNECT') THEN 1 ELSE 0 END",
    "is_warehouse": "CASE WHEN billing_origin_product = 'SQL' AND dlt_pipeline_id IS NULL THEN 1 ELSE 0 END",

    # Entity type cost proportions
    "serverless_cost_pct": "serverless_cost / NULLIF(total_cost, 0)",
    "job_cost_pct": "job_cost / NULLIF(total_cost, 0)",
    "pipeline_cost_pct": "pipeline_cost / NULLIF(total_cost, 0)",
}
```

#### Tag Coverage Features (Pattern 9)
**Source:** Jobs System Tables Dashboard, Governance Hub Dashboard

Add to **Chargeback Optimizer** and **Cost Anomaly Detector**:
```python
# Tag hygiene features
tag_features = {
    # Coverage metrics
    "tag_coverage_pct": "tagged_cost / NULLIF(total_cost, 0) * 100",
    "untagged_cost_pct": "untagged_cost / NULLIF(total_cost, 0) * 100",

    # Tag diversity
    "unique_team_tags": "COUNT(DISTINCT custom_tags['team'])",
    "unique_project_tags": "COUNT(DISTINCT custom_tags['project'])",
    "tag_entropy": "Entropy of tag distribution (higher = more diverse)",

    # Tag compliance risk
    "is_high_cost_untagged": "CASE WHEN cost > 1000 AND is_tagged = FALSE THEN 1 ELSE 0 END",

    # Tag drift
    "tag_coverage_7d_change": "current_tag_coverage - prior_7d_tag_coverage",
}
```

#### Active/Inactive Table Features (Pattern 7)
**Source:** Governance Hub Dashboard

Add to new **Data Staleness Predictor** model:
```python
# Table activity features for predicting staleness
activity_features = {
    # Activity recency
    "days_since_last_read": "DATEDIFF(CURRENT_DATE(), last_read_date)",
    "days_since_last_write": "DATEDIFF(CURRENT_DATE(), last_write_date)",
    "days_since_any_activity": "LEAST(days_since_last_read, days_since_last_write)",

    # Activity velocity
    "reads_per_week": "read_count_30d / 4.3",
    "writes_per_week": "write_count_30d / 4.3",
    "read_write_ratio": "read_count / NULLIF(write_count, 0)",

    # Activity trend
    "activity_trend": "(activity_last_7d - activity_prior_7d) / NULLIF(activity_prior_7d, 0)",

    # Consumer diversity
    "unique_readers": "COUNT(DISTINCT reader_user)",
    "unique_writers": "COUNT(DISTINCT writer_user)",
}
```

### New Model: User Cost Behavior Predictor (🆕)
**Source:** Azure Serverless Cost Dashboard (Pattern 6)

**Problem Type:** Clustering + Regression
**Use Case:** Predict user cost behavior and identify high-growth users early
**Business Value:** Proactive cost management, capacity planning

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_usage`, `dim_workspace` |
| **Output** | User cluster assignment, predicted monthly cost, growth trajectory |
| **Algorithm** | K-Means for behavior clustering + Gradient Boosting for cost prediction |
| **Refresh** | Weekly |

**Feature Engineering:**
```python
user_behavior_features = {
    # Cost breakdown by product
    "jobs_cost_pct": "jobs_cost / NULLIF(total_cost, 0)",
    "notebooks_cost_pct": "notebooks_cost / NULLIF(total_cost, 0)",
    "warehouse_cost_pct": "warehouse_cost / NULLIF(total_cost, 0)",

    # Growth patterns
    "cost_7d_growth": "Growth rate in last 7 days",
    "cost_30d_growth": "Growth rate in last 30 days",
    "growth_acceleration": "Change in growth rate",

    # Usage patterns
    "active_days_pct": "Days with activity / Total days",
    "avg_daily_cost": "Total cost / Active days",
    "cost_volatility": "STDDEV(daily_cost) / AVG(daily_cost)",

    # Resource diversity
    "unique_workspaces": "COUNT(DISTINCT workspace_id)",
    "unique_clusters": "COUNT(DISTINCT cluster_id)",
    "unique_jobs": "COUNT(DISTINCT job_id)",
}
```

**User Behavior Clusters:**
| Cluster | Profile | Action |
|---------|---------|--------|
| 0 | Low & Stable | Monitor |
| 1 | Low & Growing | Watch |
| 2 | High & Stable | Optimize |
| 3 | High & Growing | **Alert** |
| 4 | Declining | Investigate |

### Enhanced Feature SQL (from Dashboard Patterns)

```sql
-- Enhanced cost anomaly features incorporating dashboard patterns
WITH daily_metrics AS (
    SELECT
        usage_date,
        workspace_id,
        identity_metadata_run_as AS user_email,

        -- Basic aggregations
        SUM(list_cost) AS daily_cost,
        SUM(usage_quantity) AS daily_dbu,

        -- Entity type breakdown (Pattern 11)
        SUM(CASE WHEN is_serverless THEN list_cost ELSE 0 END) AS serverless_cost,
        SUM(CASE WHEN billing_origin_product = 'JOBS' THEN list_cost ELSE 0 END) AS jobs_cost,
        SUM(CASE WHEN billing_origin_product = 'SQL' THEN list_cost ELSE 0 END) AS sql_cost,

        -- Tag coverage (Pattern 9)
        SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) AS tagged_cost,
        SUM(CASE WHEN NOT is_tagged THEN list_cost ELSE 0 END) AS untagged_cost

    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -90)
    GROUP BY usage_date, workspace_id, identity_metadata_run_as
),
with_periods AS (
    SELECT
        *,
        -- 7-day period comparison (Pattern 1)
        SUM(daily_cost) OVER (
            PARTITION BY workspace_id
            ORDER BY usage_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS cost_7d,
        SUM(daily_cost) OVER (
            PARTITION BY workspace_id
            ORDER BY usage_date
            ROWS BETWEEN 13 PRECEDING AND 7 PRECEDING
        ) AS cost_prior_7d,

        -- P90 calculation for outlier detection (Pattern 3)
        PERCENTILE(daily_cost, 0.9) OVER (
            PARTITION BY workspace_id
            ORDER BY usage_date
            ROWS BETWEEN 29 PRECEDING AND 1 PRECEDING
        ) AS cost_p90_30d

    FROM daily_metrics
)
SELECT
    *,
    -- Period growth features
    (cost_7d - cost_prior_7d) / NULLIF(cost_prior_7d, 0) AS cost_7d_growth_pct,

    -- Outlier score
    (daily_cost - cost_p90_30d) / NULLIF(cost_p90_30d, 0) AS p90_deviation,

    -- Tag coverage
    tagged_cost / NULLIF(daily_cost, 0) AS tag_coverage_pct,

    -- Entity mix
    serverless_cost / NULLIF(daily_cost, 0) AS serverless_pct,
    jobs_cost / NULLIF(daily_cost, 0) AS jobs_pct

FROM with_periods
```

---

# Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Models Trained** | 24 models (+1 User Behavior) | Count of registered models |
| **Feature Store Tables** | 10 feature tables | One per domain + shared |
| **Classification Accuracy** | >85% F1 | MLflow metrics |
| **Regression MAPE** | <15% | MLflow metrics |
| **Serving Latency** | <100ms p99 | Endpoint metrics |
| **Inference Coverage** | 100% | Daily data scored |
| **Alert Precision** | >90% | False positive rate |
| **Cost Savings Identified** | $X/month | From optimization models |

---

## 🆕 GitHub Repository Pattern Enhancements for ML Models

Based on analysis of open-source Databricks repositories, the following enhancements should be incorporated:

### From system-tables-audit-logs Repository

#### Time-Windowed Aggregation Features
**Pattern:** 24-hour rolling windows with temporal clustering

Add to **Security Threat Detector** and **Data Exfiltration Detector**:
```python
# Time-windowed security features (from audit logs repo)
time_window_features = {
    # 24-hour rolling aggregations
    "events_24h_rolling": "COUNT(*) OVER (PARTITION BY user_id ORDER BY event_time RANGE BETWEEN INTERVAL 24 HOURS PRECEDING AND CURRENT ROW)",
    "unique_tables_24h": "COUNT(DISTINCT table_name) OVER 24-hour window",
    "sensitive_access_24h": "COUNT sensitive table access in 24-hour window",

    # Temporal clustering (60-minute periods)
    "events_per_hour": "Events grouped into 60-minute buckets",
    "activity_concentration": "% of activity in top 3 hours",
    "burst_score": "MAX(hourly_events) / AVG(hourly_events)",

    # System account exclusion
    "is_system_account": "Exclude system.*, databricks-*, service principals from anomaly scoring",
    "is_human_user": "Flag for human vs automated activity"
}
```

#### Feature SQL Pattern (Temporal Clustering)
```sql
-- 60-minute temporal clustering for security analysis (from audit logs repo)
WITH hourly_activity AS (
    SELECT
        created_by AS user_id,
        DATE_TRUNC('hour', event_time) AS activity_hour,
        COUNT(*) AS events_in_hour,
        COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name)) AS tables_in_hour
    FROM ${catalog}.${gold_schema}.fact_table_lineage
    WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
      -- Exclude system accounts (from audit logs repo pattern)
      AND created_by NOT LIKE 'system.%'
      AND created_by NOT LIKE 'databricks-%'
    GROUP BY created_by, DATE_TRUNC('hour', event_time)
),
user_patterns AS (
    SELECT
        user_id,
        AVG(events_in_hour) AS avg_hourly_events,
        MAX(events_in_hour) AS max_hourly_events,
        STDDEV(events_in_hour) AS stddev_hourly_events,
        -- Burst detection (concentration in peak hours)
        MAX(events_in_hour) / NULLIF(AVG(events_in_hour), 0) AS burst_ratio,
        -- Activity spread (inverse of concentration)
        COUNT(DISTINCT activity_hour) AS active_hours
    FROM hourly_activity
    GROUP BY user_id
)
SELECT
    user_id,
    avg_hourly_events,
    max_hourly_events,
    burst_ratio,
    -- Anomaly indicators
    CASE WHEN burst_ratio > 5 THEN 1 ELSE 0 END AS has_activity_burst,
    CASE WHEN active_hours < 3 THEN 1 ELSE 0 END AS concentrated_activity
FROM user_patterns
```

### From Workflow Advisor Repository

#### Under/Over-Provisioning Detection Features
**Pattern:** Resource utilization metrics for cluster right-sizing

Add to **Job Cost Optimizer** and **Cluster Capacity Planner**:
```python
# Resource utilization features (from Workflow Advisor repo)
provisioning_features = {
    # Under-provisioning indicators
    "cpu_saturation_rate": "% time CPU > 90%",
    "memory_pressure_rate": "% time mem_used > 85%",
    "io_wait_rate": "% time io_wait > 20%",
    "autoscale_max_reached_rate": "% time at max workers",

    # Over-provisioning indicators
    "cpu_idle_rate": "% time CPU < 20%",
    "memory_underutil_rate": "% time mem_used < 30%",
    "worker_count_stability": "STDDEV(active_workers) / AVG(active_workers)",
    "autoscale_min_time": "% time at min workers",

    # Cost efficiency metrics
    "dbu_per_successful_run": "total_dbu / successful_runs",
    "cost_per_gb_processed": "total_cost / total_bytes_processed_gb",
    "idle_cluster_cost": "Cost while CPU < 10%",

    # Recommendations
    "recommended_min_workers": "Based on 80th percentile utilization",
    "recommended_max_workers": "Based on 95th percentile peaks",
    "spot_opportunity": "% of runtime where spot would be safe"
}
```

#### Feature SQL Pattern (Right-Sizing Analysis)
```sql
-- Cluster right-sizing features (from Workflow Advisor repo)
WITH cluster_utilization AS (
    SELECT
        cluster_id,
        DATE(start_time) AS util_date,
        -- CPU utilization buckets
        AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu,
        MAX(cpu_user_percent + cpu_system_percent) AS peak_cpu,
        SUM(CASE WHEN cpu_user_percent + cpu_system_percent > 90 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0) AS cpu_saturation_pct,
        SUM(CASE WHEN cpu_user_percent + cpu_system_percent < 20 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0) AS cpu_idle_pct,
        -- Memory utilization
        AVG(mem_used_percent) AS avg_memory,
        MAX(mem_used_percent) AS peak_memory,
        SUM(CASE WHEN mem_used_percent > 85 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0) AS memory_pressure_pct,
        -- IO wait
        AVG(cpu_wait_percent) AS avg_io_wait
    FROM ${catalog}.${gold_schema}.fact_node_timeline
    WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY cluster_id, DATE(start_time)
)
SELECT
    cluster_id,
    AVG(avg_cpu) AS overall_avg_cpu,
    AVG(peak_cpu) AS overall_peak_cpu,
    AVG(cpu_saturation_pct) AS avg_saturation_pct,
    AVG(cpu_idle_pct) AS avg_idle_pct,
    -- Right-sizing recommendation
    CASE
        WHEN AVG(cpu_saturation_pct) > 20 AND AVG(peak_cpu) > 95 THEN 'UNDERPROVISIONED'
        WHEN AVG(cpu_idle_pct) > 50 AND AVG(peak_cpu) < 60 THEN 'OVERPROVISIONED'
        ELSE 'OPTIMAL'
    END AS sizing_recommendation,
    -- Potential savings estimate
    CASE
        WHEN AVG(cpu_idle_pct) > 50 THEN AVG(cpu_idle_pct) / 100 * 0.5  -- 50% of idle time recoverable
        ELSE 0
    END AS potential_savings_factor
FROM cluster_utilization
GROUP BY cluster_id
```

### From DBSQL Warehouse Advisor Repository

#### Materialized View Layer Best Practices
**Pattern:** Pre-aggregate metrics in Gold layer for dashboard performance

Add to all feature tables and inference outputs:
```python
# Materialized view patterns (from DBSQL Warehouse Advisor repo)
materialized_view_patterns = {
    # Pre-calculated windows for dashboards
    "daily_aggregates": "Pre-computed daily rollups for fast filtering",
    "weekly_aggregates": "Pre-computed weekly summaries",
    "monthly_aggregates": "Pre-computed monthly summaries",

    # Dashboard-optimized grain
    "entity_daily_grain": "One row per entity per day for most dashboards",
    "hourly_grain_for_monitoring": "Hourly for real-time monitors",

    # Query efficiency flags
    "has_high_queue_time": "Pre-calculated flag for queue > 10% of runtime",
    "has_high_spill": "Pre-calculated flag for spill > 100MB",
    "is_complex_query": "Pre-calculated flag for joins > 5 or subqueries > 3"
}
```

#### Implementation Recommendation
```python
# Create materialized Gold views for dashboard performance
MATERIALIZED_VIEWS = [
    {
        "name": "mv_daily_cost_summary",
        "source": "fact_usage",
        "grain": "workspace_id, usage_date, sku_name",
        "measures": ["total_cost", "total_dbu", "record_count", "avg_list_price"],
        "refresh": "SCHEDULE CRON '0 0 2 * * ?'"  # Daily at 2 AM
    },
    {
        "name": "mv_daily_job_summary",
        "source": "fact_job_run_timeline",
        "grain": "job_id, run_date",
        "measures": ["run_count", "success_count", "failure_count", "avg_duration", "total_duration"],
        "refresh": "SCHEDULE CRON '0 0 2 * * ?'"
    },
    {
        "name": "mv_hourly_query_summary",
        "source": "fact_query_history",
        "grain": "warehouse_id, DATE_TRUNC('hour', start_time)",
        "measures": ["query_count", "p50_duration", "p95_duration", "spill_query_count"],
        "refresh": "SCHEDULE CRON '0 0 * * * ?'"  # Hourly
    }
]
```

### New Model: Cluster Right-Sizing Recommender (🆕)
**Source:** Workflow Advisor Repository patterns

**Problem Type:** Classification + Optimization
**Use Case:** Recommend optimal cluster configuration based on historical utilization
**Business Value:** 20-40% cost savings through right-sizing (validated in Workflow Advisor)

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_node_timeline`, `fact_usage`, `dim_cluster` |
| **Output** | sizing_recommendation, recommended_workers, potential_savings |
| **Algorithm** | Gradient Boosting + Constraint Optimization |
| **Refresh** | Weekly |

**Feature Engineering:**
```python
rightsizing_features = {
    # From Workflow Advisor patterns
    "utilization_efficiency": "avg_cpu / peak_cpu ratio",
    "memory_cpu_ratio": "avg_memory / avg_cpu",
    "io_bottleneck_score": "avg_io_wait / avg_cpu",
    "burst_handling_capability": "Peak handling without saturation",

    # Cost metrics
    "cost_per_compute_hour": "total_cost / compute_hours",
    "idle_cost_ratio": "idle_time_cost / total_cost",

    # Autoscaling effectiveness
    "autoscale_response_time": "Time to scale up on load increase",
    "scale_down_efficiency": "Time to scale down after load decrease"
}
```

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

### GitHub Repository References (🆕)
- [system-tables-audit-logs](https://github.com/andyweaves/system-tables-audit-logs) - Time-windowed security analysis, temporal clustering
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme) - Materialized view layer, query efficiency
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor) - Under/over-provisioning detection, right-sizing

---

## 🆕 Blog Post Pattern Enhancements for ML Models

Based on detailed analysis of Databricks engineering blog posts, the following specific enhancements should be incorporated:

### From DBSQL Warehouse Advisor v5 Blog

**Key Insight:** P99 percentiles are more important than P95 for SLA monitoring; queries exceeding 60 seconds are flagged as "slow" by default.

#### Enhanced Query Performance Features

Add to **Query Performance Forecaster** and **Warehouse Auto-Scaler Optimizer**:

```python
# DBSQL Warehouse Advisor v5 Blog features
dbsql_advisor_features = {
    # P99 metrics (critical for SLA monitoring)
    "p99_duration_sec": "PERCENTILE(total_duration_ms / 1000.0, 0.99)",
    "p99_vs_p95_ratio": "p99_duration / NULLIF(p95_duration, 0)",
    "tail_latency_severity": "CASE WHEN p99 > 2 * p95 THEN 'SEVERE' WHEN p99 > 1.5 * p95 THEN 'MODERATE' ELSE 'NORMAL' END",

    # 60-second SLA threshold (from blog)
    "sla_breach_count": "COUNT(CASE WHEN total_duration_ms > 60000 THEN 1 END)",
    "sla_breach_rate": "sla_breach_count / NULLIF(total_queries, 0) * 100",
    "avg_sla_breach_severity": "AVG(CASE WHEN total_duration_ms > 60000 THEN (total_duration_ms - 60000) / 1000.0 END)",

    # QPS/QPM throughput metrics
    "queries_per_minute": "COUNT(*) / NULLIF(TIMESTAMPDIFF(MINUTE, MIN(start_time), MAX(end_time)), 0)",
    "queries_per_second_peak": "MAX queries in any 1-second window",
    "throughput_variability": "STDDEV(qpm) / NULLIF(AVG(qpm), 0)",

    # Warehouse tier dimension
    "warehouse_tier": "SERVERLESS, PRO, or CLASSIC",
    "tier_efficiency_factor": "CASE WHEN warehouse_tier = 'SERVERLESS' THEN 1.0 WHEN warehouse_tier = 'PRO' THEN 0.85 ELSE 0.7 END",

    # Query efficiency classification (from blog)
    "efficiency_category": """
        CASE
            WHEN spilled_local_bytes = 0
             AND waiting_at_capacity_duration_ms <= total_duration_ms * 0.1
             AND total_duration_ms <= 60000
            THEN 'EFFICIENT'
            WHEN spilled_local_bytes > 0 THEN 'HIGH_SPILL'
            WHEN waiting_at_capacity_duration_ms > total_duration_ms * 0.1 THEN 'HIGH_QUEUE'
            ELSE 'SLOW'
        END
    """,
}
```

#### Feature SQL (60-Second SLA Analysis)

```sql
-- DBSQL Warehouse Advisor v5 Blog SLA analysis features
WITH query_metrics AS (
    SELECT
        qh.compute_warehouse_id AS warehouse_id,
        DATE(qh.start_time) AS query_date,
        qh.executed_by AS user_email,

        -- Duration metrics
        qh.total_duration_ms / 1000.0 AS duration_sec,
        qh.waiting_at_capacity_duration_ms / 1000.0 AS queue_sec,

        -- SLA breach flag (60-second threshold from blog)
        CASE WHEN qh.total_duration_ms > 60000 THEN 1 ELSE 0 END AS is_sla_breach,

        -- Efficiency flags
        CASE WHEN qh.spilled_local_bytes > 0 THEN 1 ELSE 0 END AS has_spill,
        CASE WHEN qh.waiting_at_capacity_duration_ms > qh.total_duration_ms * 0.1 THEN 1 ELSE 0 END AS has_high_queue,

        -- Data volume
        qh.read_bytes / 1073741824.0 AS read_gb

    FROM ${catalog}.${gold_schema}.fact_query_history qh
    WHERE qh.start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND qh.execution_status = 'SUCCEEDED'
),
warehouse_stats AS (
    SELECT
        warehouse_id,
        query_date,

        -- Volume metrics
        COUNT(*) AS total_queries,
        COUNT(DISTINCT user_email) AS unique_users,

        -- P95/P99 latency (P99 critical per blog)
        PERCENTILE(duration_sec, 0.95) AS p95_duration_sec,
        PERCENTILE(duration_sec, 0.99) AS p99_duration_sec,

        -- SLA metrics (60-second threshold)
        SUM(is_sla_breach) AS sla_breach_count,
        SUM(is_sla_breach) * 100.0 / NULLIF(COUNT(*), 0) AS sla_breach_rate,

        -- Efficiency breakdown
        SUM(has_spill) * 100.0 / NULLIF(COUNT(*), 0) AS spill_rate,
        SUM(has_high_queue) * 100.0 / NULLIF(COUNT(*), 0) AS high_queue_rate,

        -- QPS metrics
        COUNT(*) * 1.0 / NULLIF(TIMESTAMPDIFF(MINUTE, MIN(query_date), MAX(query_date)), 0) AS avg_qpm

    FROM query_metrics
    GROUP BY warehouse_id, query_date
)
SELECT
    *,
    -- Tail latency indicator
    p99_duration_sec / NULLIF(p95_duration_sec, 0) AS tail_ratio,
    -- Sizing indicator based on blog thresholds
    CASE
        WHEN sla_breach_rate > 10 OR high_queue_rate > 20 THEN 'SCALE_UP_NEEDED'
        WHEN sla_breach_rate < 2 AND high_queue_rate < 5 THEN 'SCALE_DOWN_POSSIBLE'
        ELSE 'OPTIMAL'
    END AS sizing_indicator
FROM warehouse_stats
```

### From Real-Time Query Monitoring Blog

**Key Insight:** Duration regression detection compares current query duration to historical baseline to identify performance degradation.

#### Duration Regression Detection Features

Add to **Query Performance Forecaster** and new **Regression Detector** model:

```python
# Real-Time Query Monitoring Blog features
regression_detection_features = {
    # Duration regression vs baseline
    "duration_vs_baseline_ratio": "current_duration / NULLIF(baseline_30d_avg, 0)",
    "duration_regression_pct": "(current_duration - baseline_30d_avg) / NULLIF(baseline_30d_avg, 0) * 100",
    "is_duration_regression": "CASE WHEN duration_regression_pct > 50 THEN 1 ELSE 0 END",

    # Regression severity
    "regression_severity": """
        CASE
            WHEN duration_regression_pct > 200 THEN 'CRITICAL'
            WHEN duration_regression_pct > 100 THEN 'SEVERE'
            WHEN duration_regression_pct > 50 THEN 'MODERATE'
            ELSE 'NORMAL'
        END
    """,

    # Query complexity metrics (from blog)
    "query_complexity_score": """
        CASE
            WHEN LENGTH(statement_text) > 10000 THEN 5
            WHEN LENGTH(statement_text) > 5000 THEN 4
            WHEN REGEXP_COUNT(UPPER(statement_text), 'JOIN') > 5 THEN 4
            WHEN REGEXP_COUNT(UPPER(statement_text), 'JOIN') > 3 THEN 3
            WHEN REGEXP_COUNT(UPPER(statement_text), 'SUBQUERY|SELECT.*SELECT') > 2 THEN 3
            ELSE 1
        END
    """,

    # Query pattern changes
    "query_plan_change_detected": "Hash of query plan differs from baseline",
    "data_volume_growth_pct": "(current_read_bytes - baseline_read_bytes) / NULLIF(baseline_read_bytes, 0) * 100",
}
```

### From Workflow Advisor Blog

**Key Insight:** ALL_PURPOSE clusters are ~40% more expensive than JOB clusters for the same work. Identifying jobs running on ALL_PURPOSE is a major cost optimization opportunity.

#### ALL_PURPOSE Cluster Inefficiency Features

Add to **Job Cost Optimizer** and **Chargeback Optimizer**:

```python
# Workflow Advisor Blog features
all_purpose_inefficiency_features = {
    # Cluster type classification
    "is_all_purpose_cluster": "CASE WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 1 ELSE 0 END",
    "is_job_cluster": "CASE WHEN sku_name LIKE '%JOBS%' THEN 1 ELSE 0 END",

    # Inefficiency detection (jobs on ALL_PURPOSE)
    "job_on_all_purpose": """
        CASE WHEN sku_name LIKE '%ALL_PURPOSE%'
             AND usage_metadata['job_id'] IS NOT NULL
        THEN 1 ELSE 0 END
    """,

    # Cost impact (40% savings potential from blog)
    "potential_savings_pct": "0.4 if job_on_all_purpose else 0",
    "potential_savings_amount": "list_cost * 0.4 if job_on_all_purpose else 0",

    # Cumulative inefficiency
    "all_purpose_job_cost_30d": "SUM(list_cost) WHERE job_on_all_purpose = 1 over 30 days",
    "total_potential_savings_30d": "all_purpose_job_cost_30d * 0.4",

    # Recommendation priority
    "migration_priority": """
        CASE
            WHEN potential_savings_amount > 1000 THEN 'HIGH'
            WHEN potential_savings_amount > 100 THEN 'MEDIUM'
            ELSE 'LOW'
        END
    """,
}
```

#### Feature SQL (ALL_PURPOSE Inefficiency Analysis)

```sql
-- Workflow Advisor Blog: ALL_PURPOSE cluster inefficiency detection
WITH job_cluster_analysis AS (
    SELECT
        f.usage_metadata_job_id AS job_id,
        j.name AS job_name,

        -- Cluster type breakdown
        SUM(CASE WHEN f.sku_name LIKE '%ALL_PURPOSE%' THEN f.list_cost ELSE 0 END) AS all_purpose_cost,
        SUM(CASE WHEN f.sku_name LIKE '%JOBS%' THEN f.list_cost ELSE 0 END) AS job_cluster_cost,
        SUM(f.list_cost) AS total_cost,

        -- Run counts by cluster type
        COUNT(DISTINCT CASE WHEN f.sku_name LIKE '%ALL_PURPOSE%' THEN f.usage_metadata_job_run_id END) AS all_purpose_runs,
        COUNT(DISTINCT CASE WHEN f.sku_name LIKE '%JOBS%' THEN f.usage_metadata_job_run_id END) AS job_cluster_runs,

        -- Cost per run comparison
        AVG(CASE WHEN f.sku_name LIKE '%ALL_PURPOSE%' THEN f.list_cost END) AS avg_all_purpose_cost_per_run,
        AVG(CASE WHEN f.sku_name LIKE '%JOBS%' THEN f.list_cost END) AS avg_job_cluster_cost_per_run

    FROM ${catalog}.${gold_schema}.fact_usage f
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j
        ON f.usage_metadata_job_id = j.job_id AND j.is_current = TRUE
    WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND f.usage_metadata_job_id IS NOT NULL
    GROUP BY f.usage_metadata_job_id, j.name
)
SELECT
    job_id,
    job_name,
    all_purpose_cost,
    job_cluster_cost,
    total_cost,

    -- Inefficiency metrics
    all_purpose_cost / NULLIF(total_cost, 0) * 100 AS all_purpose_pct,

    -- Potential savings (40% from Workflow Advisor Blog)
    all_purpose_cost * 0.4 AS potential_savings,

    -- Migration recommendation
    CASE
        WHEN all_purpose_cost > 1000 AND all_purpose_runs > job_cluster_runs THEN 'MIGRATE_HIGH_PRIORITY'
        WHEN all_purpose_cost > 100 THEN 'MIGRATE_MEDIUM_PRIORITY'
        WHEN all_purpose_cost > 0 THEN 'MIGRATE_LOW_PRIORITY'
        ELSE 'OPTIMAL'
    END AS recommendation,

    -- ML features for migration risk
    CASE WHEN job_cluster_runs > 0 THEN 0 ELSE 1 END AS never_used_job_cluster,
    all_purpose_runs,
    job_cluster_runs

FROM job_cluster_analysis
WHERE all_purpose_cost > 0
ORDER BY potential_savings DESC
```

### Enhanced Security Features: User Type Classification

**Source:** system-tables-audit-logs GitHub repo + Security Blog

Add to **Security Threat Detector**, **Data Exfiltration Detector**, and **User Behavior Baseline**:

```python
# User type classification features (from audit logs repo)
user_type_features = {
    # User type classification
    "user_type": """
        CASE
            -- System accounts (Databricks internal)
            WHEN user_identity_email LIKE 'System-%' THEN 'SYSTEM'
            WHEN user_identity_email LIKE 'system-%' THEN 'SYSTEM'
            -- Platform accounts (automated)
            WHEN user_identity_email IN ('Unity Catalog', 'Delta Sharing', 'Catalog', 'Schema') THEN 'PLATFORM'
            WHEN user_identity_email LIKE 'DBX_%' THEN 'PLATFORM'
            -- Service principals (apps)
            WHEN user_identity_email LIKE '%@%.iam.gserviceaccount.com' THEN 'SERVICE_PRINCIPAL'
            WHEN user_identity_email LIKE '%spn@%' THEN 'SERVICE_PRINCIPAL'
            WHEN user_identity_email NOT LIKE '%@%' THEN 'SERVICE_PRINCIPAL'
            -- Human users (everyone else with @ sign)
            ELSE 'HUMAN_USER'
        END
    """,

    # Human-specific features (more meaningful for security)
    "is_human_user": "CASE WHEN user_type = 'HUMAN_USER' THEN 1 ELSE 0 END",
    "is_automated": "CASE WHEN user_type IN ('SYSTEM', 'PLATFORM', 'SERVICE_PRINCIPAL') THEN 1 ELSE 0 END",

    # Human activity anomaly features
    "human_off_hours_events": "COUNT events WHERE is_human_user AND (hour < 7 OR hour >= 19)",
    "human_off_hours_rate": "human_off_hours_events / NULLIF(human_events, 0) * 100",
    "human_weekend_events": "COUNT events WHERE is_human_user AND day_of_week IN (1, 7)",

    # Service principal anomaly features
    "sp_new_ip_detected": "Service principal accessing from new IP",
    "sp_volume_spike": "SP event count > 3x baseline",

    # Activity pattern by user type
    "human_to_sp_event_ratio": "human_events / NULLIF(sp_events, 0)",
}
```

#### User Type Classification SQL

```sql
-- User type classification for security analysis (from audit logs repo)
WITH classified_events AS (
    SELECT
        event_date,
        user_identity_email,
        event_time,
        action_name,
        service_name,
        source_ip_address,
        is_failed_action,
        is_sensitive_action,

        -- User type classification
        CASE
            WHEN user_identity_email LIKE 'System-%' OR user_identity_email LIKE 'system-%' THEN 'SYSTEM'
            WHEN user_identity_email IN ('Unity Catalog', 'Delta Sharing', 'Catalog', 'Schema') THEN 'PLATFORM'
            WHEN user_identity_email LIKE 'DBX_%' THEN 'PLATFORM'
            WHEN user_identity_email LIKE '%@%.iam.gserviceaccount.com' THEN 'SERVICE_PRINCIPAL'
            WHEN user_identity_email LIKE '%spn@%' THEN 'SERVICE_PRINCIPAL'
            WHEN user_identity_email NOT LIKE '%@%' THEN 'SERVICE_PRINCIPAL'
            ELSE 'HUMAN_USER'
        END AS user_type

    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
        AND user_identity_email IS NOT NULL
),
user_metrics AS (
    SELECT
        user_identity_email,
        user_type,

        -- Event counts
        COUNT(*) AS total_events,
        SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
        SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) AS sensitive_events,

        -- Off-hours activity (human-focused)
        SUM(CASE WHEN HOUR(event_time) < 7 OR HOUR(event_time) >= 19 THEN 1 ELSE 0 END) AS off_hours_events,
        SUM(CASE WHEN DAYOFWEEK(event_date) IN (1, 7) THEN 1 ELSE 0 END) AS weekend_events,

        -- Unique IPs
        COUNT(DISTINCT source_ip_address) AS unique_ips,
        COUNT(DISTINCT service_name) AS unique_services

    FROM classified_events
    GROUP BY user_identity_email, user_type
)
SELECT
    *,
    -- Anomaly indicators by user type
    CASE
        WHEN user_type = 'HUMAN_USER' AND off_hours_events * 100.0 / NULLIF(total_events, 0) > 30 THEN 'HIGH_OFF_HOURS'
        WHEN user_type = 'SERVICE_PRINCIPAL' AND unique_ips > 5 THEN 'MULTIPLE_IPS'
        WHEN failed_events * 100.0 / NULLIF(total_events, 0) > 20 THEN 'HIGH_FAILURE_RATE'
        ELSE 'NORMAL'
    END AS anomaly_indicator,

    -- Risk scoring (higher for humans in off-hours)
    CASE user_type
        WHEN 'HUMAN_USER' THEN off_hours_events * 2 + sensitive_events * 3 + failed_events
        WHEN 'SERVICE_PRINCIPAL' THEN unique_ips * 2 + sensitive_events * 2 + failed_events
        ELSE 0  -- System/Platform accounts are expected behavior
    END AS risk_score

FROM user_metrics
ORDER BY risk_score DESC
```

### New Model: Query Regression Detector (🆕)

**Source:** Real-Time Query Monitoring Blog

**Problem Type:** Classification + Anomaly Detection
**Use Case:** Detect queries with performance regression vs historical baseline
**Business Value:** Early detection of performance degradation, prevent SLA breaches

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_query_history`, `dim_warehouse` |
| **Output** | regression_detected, regression_severity, root_cause_probability |
| **Algorithm** | Isolation Forest + Rule-based classification |
| **Refresh** | Real-time (per query) |

**Feature Engineering:**
```python
regression_detector_features = {
    # Baseline comparison (30-day rolling)
    "baseline_avg_duration": "AVG duration for this query hash over 30 days",
    "baseline_p95_duration": "P95 duration for this query hash over 30 days",
    "baseline_read_bytes": "AVG read_bytes for this query hash",

    # Current execution
    "current_duration_sec": "Current query duration",
    "current_read_bytes": "Current query read_bytes",

    # Regression indicators
    "duration_vs_baseline": "current / baseline ratio",
    "regression_severity_score": "0-100 based on deviation from baseline",

    # Root cause indicators
    "data_volume_changed": "read_bytes vs baseline",
    "plan_changed": "Query plan hash differs from baseline",
    "warehouse_changed": "Different warehouse than baseline",
    "peak_hours": "Running during high-load period"
}
```

### New Model: ALL_PURPOSE Migration Recommender (🆕)

**Source:** Workflow Advisor Blog

**Problem Type:** Classification + Optimization
**Use Case:** Recommend jobs to migrate from ALL_PURPOSE to JOB clusters
**Business Value:** 40% cost savings on migrated jobs (validated in blog)

| Aspect | Details |
|--------|---------|
| **Gold Tables** | `fact_usage`, `fact_job_run_timeline`, `dim_job`, `dim_cluster` |
| **Output** | migration_recommendation, estimated_savings, migration_risk |
| **Algorithm** | Gradient Boosting + Rule-based prioritization |
| **Refresh** | Weekly |

**Feature Engineering:**
```python
migration_features = {
    # Current state
    "all_purpose_cost_30d": "Cost on ALL_PURPOSE clusters",
    "all_purpose_runs_30d": "Runs on ALL_PURPOSE",
    "has_job_cluster_runs": "Has ever run on JOB cluster",

    # Migration risk factors
    "uses_init_scripts": "Custom initialization scripts",
    "uses_cluster_policies": "Attached to cluster policy",
    "uses_instance_pools": "Uses instance pool",
    "uses_spark_config": "Has custom Spark config",

    # Savings potential
    "estimated_savings": "all_purpose_cost * 0.4",
    "annual_projected_savings": "estimated_savings * 12",

    # Priority scoring
    "migration_priority_score": "savings * (1 - risk_score)",
}
```

---

## Updated Model Catalog Summary

| Agent Domain | Model Count | New Models Added |
|--------------|-------------|------------------|
| **💰 Cost** | 7 models (+2) | User Cost Behavior Predictor, ALL_PURPOSE Migration Recommender |
| **🔒 Security** | 4 models | (Enhanced with user type classification) |
| **⚡ Performance** | 7 models (+1) | Query Regression Detector |
| **🔄 Reliability** | 5 models | (Enhanced with duration regression) |
| **✅ Quality** | 3 models | |
| **Total** | **26 models** (+3) | |

---

## Updated Success Criteria

| Criteria | Target | Source |
|----------|--------|--------|
| **Models Trained** | 26 models (+3 from blogs) | |
| **SLA Breach Detection** | >95% recall on 60s threshold | DBSQL Advisor Blog |
| **Regression Detection** | <5 min latency to detect | Real-Time Monitoring Blog |
| **Cost Savings Identified** | >$X/month from ALL_PURPOSE migration | Workflow Advisor Blog |
| **Human vs System Classification** | >99% accuracy | Audit Logs Repo |
| **P99 Prediction Accuracy** | MAPE <20% | DBSQL Advisor Blog |
