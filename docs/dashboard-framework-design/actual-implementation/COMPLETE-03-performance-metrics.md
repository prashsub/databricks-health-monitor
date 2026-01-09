# Complete Query Performance Metrics Catalog

## Overview

This document catalogs ALL metrics, calculations, and measures from the Query Performance dashboard.

---

## Metrics Extracted from Datasets


### KPI: Queries
**Dataset:** `ds_kpi_queries`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### KPI: Slow
**Dataset:** `ds_kpi_slow`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### KPI: Failed
**Dataset:** `ds_kpi_failed`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Query Volume
**Dataset:** `ds_query_volume`  

**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Duration Trend
**Dataset:** `ds_duration_trend`  

**Aggregations:** AVG  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### Slowest Queries
**Dataset:** `ds_slowest_queries`  

**Source Table:** fact_query_history  


### Slow by User
**Dataset:** `ds_slow_by_user`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Slow by Warehouse
**Dataset:** `ds_slow_by_warehouse`  

**Source Table:** fact_query_history  


### Slow Query Trend
**Dataset:** `ds_slow_query_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Failed Queries
**Dataset:** `ds_failed_queries`  

**Source Table:** fact_query_history  


### Failed by Error
**Dataset:** `ds_failed_by_error`  

**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Failed Trend
**Dataset:** `ds_failed_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Warehouse Performance
**Dataset:** `ds_warehouse_perf`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### Queries by Warehouse
**Dataset:** `ds_queries_by_warehouse`  

**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Warehouse Hourly
**Dataset:** `ds_warehouse_hourly`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Warehouse Usage Over Time
**Dataset:** `ds_warehouse_usage_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Usage by Warehouse Type
**Dataset:** `ds_warehouse_type_distribution`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Warehouse Current Config
**Dataset:** `ds_warehouse_config_snapshot`  



### Long-Running Queries by Warehouse
**Dataset:** `ds_warehouse_long_queries`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Query Source Distribution
**Dataset:** `ds_query_source_distribution`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Top Warehouses by Cost
**Dataset:** `ds_warehouse_cost_ranking`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### ML: Optimization
**Dataset:** `ds_ml_optimization`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### ML: Regression
**Dataset:** `ds_ml_regression`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_query_history  


### ML: Warehouse
**Dataset:** `ds_ml_warehouse`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### Monitor: Latest
**Dataset:** `ds_monitor_latest`  

**Source Table:** fact_query_history  


### Monitor: Trend
**Dataset:** `ds_monitor_trend`  

**Source Table:** fact_query_history  


### Monitor: Volume
**Dataset:** `ds_monitor_volume`  

**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Monitor: Drift
**Dataset:** `ds_monitor_drift`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  


### Monitor: Detailed
**Dataset:** `ds_monitor_detailed`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  


### Drift Investigation
**Dataset:** `ds_drift_investigation`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### KPI: Utilization
**Dataset:** `ds_kpi_utilization`  

**Aggregations:** AVG  
**Aggregations:** COUNT  


### KPI: Underutilized
**Dataset:** `ds_kpi_underutilized`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  


### KPI: Overutilized
**Dataset:** `ds_kpi_overutilized`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  


### CPU Trend
**Dataset:** `ds_cpu_trend`  

**Aggregations:** AVG  
**Aggregations:** MAX  


### Memory Trend
**Dataset:** `ds_memory_trend`  

**Aggregations:** AVG  
**Aggregations:** MAX  


### Disk I/O Trend
**Dataset:** `ds_disk_io_trend`  

**Aggregations:** AVG  
**Aggregations:** MAX  


### Underutilized Clusters
**Dataset:** `ds_underutilized_clusters`  

**Aggregations:** AVG  
**Aggregations:** MAX  


### Overutilized Clusters
**Dataset:** `ds_overutilized_clusters`  

**Aggregations:** AVG  
**Aggregations:** MAX  


### High Memory Swap
**Dataset:** `ds_high_memory_swap`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** MAX  


### High I/O Wait
**Dataset:** `ds_high_io_wait`  

**Aggregations:** AVG  
**Aggregations:** MAX  


### Utilization Distribution
**Dataset:** `ds_utilization_distribution`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MIN  


### Right-Sizing Recommendations
**Dataset:** `ds_rightsizing_recommendations`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  
**Source Table:** fact_usage  
**Source Table:** fact_query_history  


### Low CPU High Cost
**Dataset:** `ds_low_cpu_high_cost`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  


### High Memory Jobs
**Dataset:** `ds_high_memory_jobs`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### Savings Opportunity
**Dataset:** `ds_savings_opportunity`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_query_history  


### ML: Capacity Predictions
**Dataset:** `ds_ml_capacity_predictions`  



### ML: Right-Sizing
**Dataset:** `ds_ml_rightsizing`  



### ML: DBR Risk
**Dataset:** `ds_ml_dbr_risk`  



### Monitor: CPU Trend
**Dataset:** `ds_monitor_cpu_trend`  

**Aggregations:** AVG  
**Aggregations:** PERCENTILE  


### Monitor: Memory Trend
**Dataset:** `ds_monitor_memory_trend`  

**Aggregations:** AVG  
**Aggregations:** PERCENTILE  


### Most Expensive Jobs
**Dataset:** `ds_job_expensive`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Jobs with Highest Cost Change
**Dataset:** `ds_job_cost_change`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Job Failure Cost Analysis
**Dataset:** `ds_job_failure_cost`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  


### Jobs on All-Purpose Clusters
**Dataset:** `ds_job_ap_clusters`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  


### Legacy Count
**Dataset:** `ds_legacy_count`  

**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Serverless Adoption
**Dataset:** `ds_serverless_adoption`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Current Dbr
**Dataset:** `ds_current_dbr`  

**Aggregations:** SUM  
**Aggregations:** COUNT  


### Dbr Dist
**Dataset:** `ds_dbr_dist`  

**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Compute Type
**Dataset:** `ds_compute_type`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Legacy Jobs
**Dataset:** `ds_legacy_jobs`  

**Aggregations:** MAX  
**Source Table:** fact_job_run_timeline  


### Time Windows
**Dataset:** `ds_time_windows`  



### Workspaces
**Dataset:** `ds_workspaces`  



### Performance Aggregate Metrics
**Dataset:** `ds_monitor_performance_aggregate`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### Performance Derived KPIs
**Dataset:** `ds_monitor_performance_derived`  

**Source Table:** fact_query_history  


### Performance Slice Keys
**Dataset:** `ds_monitor_performance_slice_keys`  

**Source Table:** fact_query_history  


### Performance Slice Values
**Dataset:** `ds_monitor_performance_slice_values`  

**Source Table:** fact_query_history  


### Jobs with Low CPU Utilization
**Dataset:** `ds_job_low_cpu`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Jobs with High Memory Utilization
**Dataset:** `ds_job_high_mem`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Job Cost Savings Opportunities
**Dataset:** `ds_job_cost_savings`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Job CPU Utilization Distribution
**Dataset:** `ds_job_utilization_distribution`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** MIN  
**Source Table:** fact_usage  


### Job Utilization KPIs
**Dataset:** `ds_job_kpi_utilization`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_usage  

