# Complete Job Reliability Metrics Catalog

## Overview

This document catalogs ALL metrics, calculations, and measures from the Job Reliability dashboard.

---

## Metrics Extracted from Datasets


### KPI: Success Rate
**Dataset:** `ds_kpi_success_rate`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### KPI: Totals
**Dataset:** `ds_kpi_totals`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### KPI: Duration
**Dataset:** `ds_kpi_duration`  

**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### KPI: MTTR
**Dataset:** `ds_kpi_mttr`  

**Aggregations:** AVG  
**Source Table:** fact_job_run_timeline  


### Success Trend
**Dataset:** `ds_success_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Runs by Status
**Dataset:** `ds_runs_by_status`  

**Aggregations:** SUM  
**Source Table:** fact_job_run_timeline  


### Duration Trend
**Dataset:** `ds_duration_trend`  

**Aggregations:** AVG  
**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### Failed Today
**Dataset:** `ds_failed_today`  

**Source Table:** fact_job_run_timeline  


### Low Success Jobs
**Dataset:** `ds_low_success_jobs`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Highest Failure Jobs
**Dataset:** `ds_highest_failure_jobs`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Failure by Type
**Dataset:** `ds_failure_by_type`  

**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Failure Trend by Type
**Dataset:** `ds_failure_trend_by_type`  

**Aggregations:** SUM  
**Source Table:** fact_job_run_timeline  


### Most Repaired
**Dataset:** `ds_most_repaired`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Slowest Jobs
**Dataset:** `ds_slowest_jobs`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### Duration Regression
**Dataset:** `ds_duration_regression`  

**Aggregations:** AVG  
**Source Table:** fact_job_run_timeline  


### Duration Outliers
**Dataset:** `ds_duration_outliers`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### Runs by Hour
**Dataset:** `ds_runs_by_hour`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Runs by Day
**Dataset:** `ds_runs_by_day`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### ML: Failure Risk
**Dataset:** `ds_ml_failure_risk`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_job_run_timeline  


### ML: Pipeline Health
**Dataset:** `ds_ml_pipeline_health`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_job_run_timeline  


### ML: Retry Success
**Dataset:** `ds_ml_retry_success`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_job_run_timeline  


### ML: Incident Impact
**Dataset:** `ds_ml_incident_impact`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_job_run_timeline  


### ML: Self Healing
**Dataset:** `ds_ml_self_healing`  

**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_job_run_timeline  


### ML: Duration Forecast
**Dataset:** `ds_ml_duration_forecast`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### Monitor: Latest
**Dataset:** `ds_monitor_latest`  

**Source Table:** fact_job_run_timeline  


### Monitor: Trend
**Dataset:** `ds_monitor_trend`  

**Source Table:** fact_job_run_timeline  


### Monitor: Duration
**Dataset:** `ds_monitor_duration`  

**Source Table:** fact_job_run_timeline  


### Monitor: Run Types
**Dataset:** `ds_monitor_run_types`  

**Source Table:** fact_job_run_timeline  


### Monitor: Errors
**Dataset:** `ds_monitor_errors`  

**Source Table:** fact_job_run_timeline  


### Monitor: Drift
**Dataset:** `ds_monitor_drift`  

**Source Table:** fact_job_run_timeline  


### Monitor: Detailed
**Dataset:** `ds_monitor_detailed`  

**Source Table:** fact_job_run_timeline  


### No Autoscale Count
**Dataset:** `ds_no_autoscale_count`  

**Aggregations:** COUNT  


### Stale Count
**Dataset:** `ds_stale_count`  

**Aggregations:** COUNT  


### Ap Count
**Dataset:** `ds_ap_count`  

**Aggregations:** COUNT  


### No Autoscale
**Dataset:** `ds_no_autoscale`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Stale Datasets
**Dataset:** `ds_stale_datasets`  

**Aggregations:** COUNT  


### Ap Jobs
**Dataset:** `ds_ap_jobs`  

**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Outliers
**Dataset:** `ds_outliers`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### Time Windows
**Dataset:** `ds_time_windows`  



### Workspaces
**Dataset:** `ds_workspaces`  



### Reliability Aggregate Metrics
**Dataset:** `ds_monitor_reliability_aggregate`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Reliability Derived KPIs
**Dataset:** `ds_monitor_reliability_derived`  

**Source Table:** fact_job_run_timeline  


### Reliability Drift Metrics
**Dataset:** `ds_monitor_reliability_drift`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Reliability Slice Keys
**Dataset:** `ds_monitor_reliability_slice_keys`  

**Source Table:** fact_job_run_timeline  


### Reliability Slice Values
**Dataset:** `ds_monitor_reliability_slice_values`  

**Source Table:** fact_job_run_timeline  

