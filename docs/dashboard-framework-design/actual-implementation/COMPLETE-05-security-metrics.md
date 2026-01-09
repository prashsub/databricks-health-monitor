# Complete Security & Audit Metrics Catalog

## Overview

This document catalogs ALL metrics, calculations, and measures from the Security & Audit dashboard.

---

## Metrics Extracted from Datasets


### KPI: Events
**Dataset:** `ds_kpi_events`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### KPI: High Risk
**Dataset:** `ds_kpi_high_risk`  

**Aggregations:** SUM  
**Source Table:** fact_audit_logs  


### KPI: Denied
**Dataset:** `ds_kpi_denied`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### KPI: Permissions
**Dataset:** `ds_kpi_permissions`  

**Aggregations:** SUM  
**Source Table:** fact_audit_logs  


### KPI: Admin
**Dataset:** `ds_kpi_admin`  

**Aggregations:** SUM  
**Source Table:** fact_audit_logs  


### Event Trend
**Dataset:** `ds_event_trend`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Risk Trend
**Dataset:** `ds_risk_trend`  

**Aggregations:** SUM  
**Source Table:** fact_audit_logs  


### Denied Access
**Dataset:** `ds_denied_access`  

**Source Table:** fact_audit_logs  


### Permission Changes
**Dataset:** `ds_permission_changes`  

**Source Table:** fact_audit_logs  


### Denied by Service
**Dataset:** `ds_denied_by_service`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Denied by User
**Dataset:** `ds_denied_by_user`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Admin Actions
**Dataset:** `ds_admin_actions`  

**Source Table:** fact_audit_logs  


### Sensitive Actions
**Dataset:** `ds_sensitive_actions`  

**Source Table:** fact_audit_logs  


### Admin by Action
**Dataset:** `ds_admin_by_action`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Data Access
**Dataset:** `ds_data_access`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Access by Service
**Dataset:** `ds_access_by_service`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Access Hourly
**Dataset:** `ds_access_hourly`  

**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### ML: Threats
**Dataset:** `ds_ml_threats`  



### ML: Exfiltration
**Dataset:** `ds_ml_exfiltration`  



### ML: Privilege
**Dataset:** `ds_ml_privilege`  



### Monitor: Latest
**Dataset:** `ds_monitor_latest`  

**Source Table:** fact_audit_logs  


### Monitor: Trend
**Dataset:** `ds_monitor_trend`  

**Source Table:** fact_audit_logs  


### Monitor: Access
**Dataset:** `ds_monitor_access`  

**Source Table:** fact_audit_logs  


### Monitor: Drift
**Dataset:** `ds_monitor_drift`  

**Source Table:** fact_audit_logs  


### Monitor: Detailed
**Dataset:** `ds_monitor_detailed`  

**Source Table:** fact_audit_logs  


### Time Windows
**Dataset:** `ds_time_windows`  



### Workspaces
**Dataset:** `ds_workspaces`  



### Security Aggregate Metrics
**Dataset:** `ds_monitor_security_aggregate`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_audit_logs  


### Security Derived KPIs
**Dataset:** `ds_monitor_security_derived`  

**Source Table:** fact_audit_logs  


### Security Slice Keys
**Dataset:** `ds_monitor_security_slice_keys`  

**Source Table:** fact_audit_logs  


### Security Slice Values
**Dataset:** `ds_monitor_security_slice_values`  

**Source Table:** fact_audit_logs  

