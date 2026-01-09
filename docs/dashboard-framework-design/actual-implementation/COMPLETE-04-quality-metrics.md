# Complete Data Quality Metrics Catalog

## Overview

This document catalogs ALL metrics, calculations, and measures from the Data Quality dashboard.

---

## Metrics Extracted from Datasets


### KPI: Tables
**Dataset:** `ds_kpi_tables`  

**Aggregations:** COUNT  


### KPI: Tagged
**Dataset:** `ds_kpi_tagged`  



### KPI: Documented
**Dataset:** `ds_kpi_documented`  



### KPI: Lineage
**Dataset:** `ds_kpi_lineage`  



### KPI: Jobs
**Dataset:** `ds_kpi_jobs`  

**Aggregations:** COUNT  


### KPI: Workspaces
**Dataset:** `ds_kpi_workspaces`  

**Aggregations:** COUNT  


### Tables by Catalog
**Dataset:** `ds_tables_by_catalog`  

**Aggregations:** COUNT  


### Lineage Trend
**Dataset:** `ds_lineage_trend`  

**Aggregations:** COUNT  


### Untagged Tables
**Dataset:** `ds_untagged_tables`  

**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Undocumented Tables
**Dataset:** `ds_undocumented_tables`  

**Aggregations:** SUM  
**Aggregations:** COUNT  
**Source Table:** fact_query_history  


### Quality Distribution
**Dataset:** `ds_quality_distribution`  



### Lineage Sources
**Dataset:** `ds_lineage_sources`  

**Aggregations:** COUNT  


### Lineage Sinks
**Dataset:** `ds_lineage_sinks`  

**Aggregations:** COUNT  


### Stale Lineage
**Dataset:** `ds_stale_lineage`  

**Aggregations:** MAX  


### Catalog Summary
**Dataset:** `ds_catalog_summary`  

**Aggregations:** COUNT  


### Schema Summary
**Dataset:** `ds_schema_summary`  

**Aggregations:** COUNT  
**Aggregations:** MAX  


### Summary
**Dataset:** `ds_summary`  

**Aggregations:** SUM  
**Aggregations:** COUNT  


### Optimization Needed
**Dataset:** `ds_optimization_needed`  

**Aggregations:** COUNT  


### Size Buckets
**Dataset:** `ds_size_buckets`  

**Aggregations:** SUM  
**Aggregations:** COUNT  


### File Buckets
**Dataset:** `ds_file_buckets`  

**Aggregations:** COUNT  


### Largest Tables
**Dataset:** `ds_largest_tables`  



### Needs Compaction
**Dataset:** `ds_needs_compaction`  



### Empty Tables
**Dataset:** `ds_empty_tables`  



### Time Windows
**Dataset:** `ds_time_windows`  



### Monitor: Governance Latest
**Dataset:** `ds_monitor_gov_latest`  



### Monitor: Governance Trend
**Dataset:** `ds_monitor_gov_trend`  



### Monitor: Governance Drift
**Dataset:** `ds_monitor_gov_drift`  



### Monitor: Governance Detailed
**Dataset:** `ds_monitor_gov_detailed`  



### Workspaces
**Dataset:** `ds_workspaces`  


