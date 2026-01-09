# Complete Cost Management Metrics Catalog

## Overview

This document catalogs ALL metrics, calculations, and measures from the Cost Management dashboard.

---

## Metrics Extracted from Datasets


### KPI: MTD Spend
**Dataset:** `ds_kpi_mtd`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### KPI: 30d Spend
**Dataset:** `ds_kpi_30d`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### 30 vs 60 Day Compare
**Dataset:** `ds_30_60_compare`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Tag Coverage
**Dataset:** `ds_tag_coverage`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Serverless Adoption
**Dataset:** `ds_serverless_adoption`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Unique Counts
**Dataset:** `ds_unique_counts`  

**Aggregations:** COUNT  
**Source Table:** fact_usage  


### WoW Growth
**Dataset:** `ds_wow_growth`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Daily Cost
**Dataset:** `ds_daily_cost`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Top Workspaces
**Dataset:** `ds_top_workspaces`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Billing Origin Product Breakdown
**Dataset:** `ds_sku_breakdown`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Top Owners
**Dataset:** `ds_top_owners`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Spend by Tag
**Dataset:** `ds_spend_by_tag`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Spend by Tag Values
**Dataset:** `ds_spend_by_tag_values`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Highest Change Users
**Dataset:** `ds_highest_change_users`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Untagged Cost
**Dataset:** `ds_untagged_cost`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Expensive Jobs
**Dataset:** `ds_expensive_jobs`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Expensive Runs
**Dataset:** `ds_expensive_runs`  

**Aggregations:** SUM  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Highest Change Jobs
**Dataset:** `ds_highest_change_jobs`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Outlier Runs
**Dataset:** `ds_outlier_runs`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_usage  


### Failure Cost
**Dataset:** `ds_failure_cost`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  


### Repair Cost
**Dataset:** `ds_repair_cost`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  


### Stale Datasets
**Dataset:** `ds_stale_datasets`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### AP Cluster Jobs
**Dataset:** `ds_ap_cluster_jobs`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  


### No Autoscale Jobs
**Dataset:** `ds_no_autoscale`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Low DBR Jobs
**Dataset:** `ds_low_dbr_jobs`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### No Tags Jobs
**Dataset:** `ds_no_tags_jobs`  

**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Savings Potential
**Dataset:** `ds_savings_potential`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** MIN  
**Source Table:** fact_usage  


### ML: Cost Forecast
**Dataset:** `ds_ml_cost_forecast`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### ML: Cost Anomalies
**Dataset:** `ds_ml_anomalies`  

**Aggregations:** SUM  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### ML: Budget Alerts
**Dataset:** `ds_ml_budget_alerts`  

**Aggregations:** SUM  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### ML: Tag Recommendations
**Dataset:** `ds_ml_tag_recs`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### ML: User Behavior
**Dataset:** `ds_ml_user_behavior`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### ML: Migration Recs
**Dataset:** `ds_ml_migration_recs`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Monitor: Cost Trend
**Dataset:** `ds_monitor_cost_trend`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Monitor: Serverless
**Dataset:** `ds_monitor_serverless`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Monitor: Drift
**Dataset:** `ds_monitor_drift`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Monitor: Summary
**Dataset:** `ds_monitor_summary`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Commit Amount Options
**Dataset:** `ds_commit_options`  



### YTD Spend
**Dataset:** `ds_ytd_spend`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Commit Status
**Dataset:** `ds_commit_status`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Forecast Summary
**Dataset:** `ds_forecast_summary`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Projected Variance
**Dataset:** `ds_variance`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Run Rate
**Dataset:** `ds_run_rate`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Usage vs Forecast
**Dataset:** `ds_usage_forecast`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Cumulative vs Commit
**Dataset:** `ds_cumulative_vs_commit`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Monthly Breakdown
**Dataset:** `ds_monthly_breakdown`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Monthly Detail
**Dataset:** `ds_monthly_detail`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### ML: Budget Forecast
**Dataset:** `ds_ml_budget_forecast`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** PERCENTILE  
**Source Table:** fact_usage  


### ML: Commitment Recommendations
**Dataset:** `ds_ml_commitment_rec`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** MAX  
**Aggregations:** MIN  
**Aggregations:** PERCENTILE  
**Source Table:** fact_usage  


### Time Windows
**Dataset:** `ds_time_windows`  



### Workspaces
**Dataset:** `ds_workspaces`  



### Cost Aggregate Metrics
**Dataset:** `ds_monitor_cost_aggregate`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Cost Derived KPIs
**Dataset:** `ds_monitor_cost_derived`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Cost Drift Metrics
**Dataset:** `ds_monitor_cost_drift`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Source Table:** fact_usage  


### Cost Slice Keys
**Dataset:** `ds_monitor_cost_slice_keys`  



### Cost Slice Values
**Dataset:** `ds_monitor_cost_slice_values`  

**Source Table:** fact_usage  

