# Complete Unified Overview Metrics Catalog

## Overview

This document catalogs ALL metrics, calculations, and measures from the Unified Overview dashboard.

---

## Metrics Extracted from Datasets


### KPI: Query
**Dataset:** `ds_kpi_query`  

**Aggregations:** AVG  
**Source Table:** fact_query_history  


### ML: Capacity
**Dataset:** `ds_ml_capacity`  



### KPI: Events
**Dataset:** `ds_kpi_events`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### WoW Growth
**Dataset:** `ds_wow_growth`  

**Aggregations:** SUM  
**Aggregations:** AVG  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### KPI: Duration
**Dataset:** `ds_kpi_duration`  

**Aggregations:** PERCENTILE  
**Source Table:** fact_job_run_timeline  


### KPI: Slow
**Dataset:** `ds_kpi_slow`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### KPI: Queries
**Dataset:** `ds_kpi_queries`  

**Aggregations:** AVG  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### Top Workspaces
**Dataset:** `ds_top_workspaces`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  


### KPI: Jobs
**Dataset:** `ds_kpi_jobs`  

**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Unique Counts
**Dataset:** `ds_unique_counts`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Monitor: Query Drift
**Dataset:** `ds_monitor_query_drift`  

**Source Table:** fact_query_history  


### Risk Trend
**Dataset:** `ds_risk_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Tables by Catalog
**Dataset:** `ds_tables_by_catalog`  

**Aggregations:** COUNT  


### KPI: Cost
**Dataset:** `ds_kpi_cost`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Duration Trend
**Dataset:** `ds_duration_trend`  

**Aggregations:** AVG  
**Aggregations:** PERCENTILE  
**Source Table:** fact_query_history  


### ML: Security Threats
**Dataset:** `ds_ml_security_threats`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_audit_logs  


### Runs by Status
**Dataset:** `ds_runs_by_status`  

**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### KPI: Tagged
**Dataset:** `ds_kpi_tagged`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Job Trend
**Dataset:** `ds_job_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Health Score
**Dataset:** `ds_health_score`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  
**Source Table:** fact_query_history  
**Source Table:** fact_audit_logs  


### Health Trend
**Dataset:** `ds_health_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  
**Source Table:** fact_query_history  
**Source Table:** fact_audit_logs  


### Reliability Health
**Dataset:** `ds_reliability_health`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### Daily Cost
**Dataset:** `ds_daily_cost`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Serverless Adoption
**Dataset:** `ds_serverless_adoption`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Cost Health
**Dataset:** `ds_cost_health`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### ML: Job Risks
**Dataset:** `ds_ml_job_risks`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_job_run_timeline  


### KPI: MTTR
**Dataset:** `ds_kpi_mttr`  

**Aggregations:** AVG  
**Source Table:** fact_job_run_timeline  


### KPI: Lineage
**Dataset:** `ds_kpi_lineage`  

**Aggregations:** COUNT  


### Drift Trend
**Dataset:** `ds_drift_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  
**Source Table:** fact_query_history  


### Event Trend
**Dataset:** `ds_event_trend`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### KPI: Success Rate
**Dataset:** `ds_kpi_success_rate`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### KPI: Cluster
**Dataset:** `ds_kpi_cluster`  

**Aggregations:** AVG  


### KPI: Totals
**Dataset:** `ds_kpi_totals`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### KPI: Tables
**Dataset:** `ds_kpi_tables`  

**Aggregations:** COUNT  


### Monitor: Cost Drift
**Dataset:** `ds_monitor_cost_drift`  

**Source Table:** fact_usage  


### KPI: Documented
**Dataset:** `ds_kpi_documented`  

**Aggregations:** COUNT  


### KPI: 30d Spend
**Dataset:** `ds_kpi_30d`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### KPI: Denied
**Dataset:** `ds_kpi_denied`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Tag Coverage
**Dataset:** `ds_tag_coverage`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### 30 vs 60 Day Compare
**Dataset:** `ds_30_60_compare`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### ML: Cost Anomalies
**Dataset:** `ds_ml_cost_anomalies`  

**Aggregations:** SUM  
**Aggregations:** MAX  
**Source Table:** fact_usage  


### Health Issues
**Dataset:** `ds_health_issues`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** MAX  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  
**Source Table:** fact_query_history  
**Source Table:** fact_audit_logs  


### Billing Origin Product Breakdown
**Dataset:** `ds_sku_breakdown`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### KPI: Admin
**Dataset:** `ds_kpi_admin`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### KPI: Users
**Dataset:** `ds_kpi_users`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Cost Trend
**Dataset:** `ds_cost_trend`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### Monitor: Job Drift
**Dataset:** `ds_monitor_job_drift`  

**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### KPI: MTD Spend
**Dataset:** `ds_kpi_mtd`  

**Aggregations:** SUM  
**Source Table:** fact_usage  


### KPI: Permissions
**Dataset:** `ds_kpi_permissions`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### KPI: High Risk
**Dataset:** `ds_kpi_high_risk`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Success Trend
**Dataset:** `ds_success_trend`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_job_run_timeline  


### KPI: Workspaces
**Dataset:** `ds_kpi_workspaces`  

**Aggregations:** COUNT  
**Source Table:** fact_usage  


### Drift Alerts
**Dataset:** `ds_drift_alerts`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Aggregations:** PERCENTILE  
**Source Table:** fact_usage  
**Source Table:** fact_job_run_timeline  
**Source Table:** fact_query_history  


### KPI: Failed Queries
**Dataset:** `ds_kpi_failed`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Query Volume
**Dataset:** `ds_query_volume`  

**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Lineage Trend
**Dataset:** `ds_lineage_trend`  

**Aggregations:** COUNT  


### KPI: Security
**Dataset:** `ds_kpi_security`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Time Windows
**Dataset:** `ds_time_windows`  



### Workspaces
**Dataset:** `ds_workspaces`  


