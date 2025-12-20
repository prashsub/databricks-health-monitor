# AI/BI Dashboard Inventory

## Overview

This document provides a comprehensive inventory of all Lakeview AI/BI dashboards implemented for the Databricks Health Monitor project. Dashboards are organized by Agent Domain to align with the project's five-agent architecture.

## Dashboard Summary by Agent Domain

| Agent Domain | Dashboard | Purpose | Key Widgets | Refresh |
|---|---|---|---|---|
| 💰 Cost | Executive Overview | Leadership KPIs | 3 KPIs + trend + summary | Daily |
| 💰 Cost | Cost Management | FinOps analysis | Top contributors, SKU, WoW | Daily |
| 💰 Cost | Commit Tracking | Budget vs Actual | Commit variance, forecast | Daily |
| 🔄 Reliability | Job Reliability | Job health | Success rate, failures | Hourly |
| 🔄 Reliability | Job Optimization | Cost savings | Autoscaling, stale datasets | Daily |
| ⚡ Performance | Query Performance | DBA optimization | Slow queries, queue time | Hourly |
| ⚡ Performance | Cluster Utilization | Right-sizing | CPU/Mem utilization | Daily |
| ⚡ Performance | DBR Migration | Modernization | Legacy DBR, serverless | Weekly |
| 🔒 Security | Security Audit | Compliance | User activity, access | Daily |
| 🔒 Security | Governance Hub | Data governance | Lineage, tags, freshness | Daily |
| ✅ Quality | Table Health | Storage health | File distribution, compaction | Daily |

---

## 💰 Cost Agent Dashboards

### 1. Executive Overview Dashboard

**File:** `executive_overview.lvdash.json`

**Purpose:** Single-pane-of-glass view for executives showing platform health at a glance.

**Key Widgets:**
- Total Cost (MTD) - KPI Counter
- Job Success Rate - KPI Counter
- Active Users - KPI Counter
- Cost Trend (30 days) - Line Chart
- Cost by SKU - Pie Chart
- Key Metrics Summary - Table

**Gold Tables Used:**
- `fact_usage`
- `fact_job_run_timeline`
- `dim_workspace`

---

### 2. Cost Management Dashboard

**File:** `cost_management.lvdash.json`

**Purpose:** Detailed cost analysis for FinOps teams including top contributors, tag coverage, and week-over-week trends.

**Key Widgets:**
- Total DBU (MTD) - KPI Counter
- Tag Coverage % - KPI Counter
- Serverless Adoption % - KPI Counter
- Top Cost Contributors - Table
- Week-over-Week Cost - Bar Chart
- Cost by Owner - Table
- Untagged Resources - Table

**Gold Tables Used:**
- `fact_usage`
- `dim_workspace`

---

### 3. Commit Tracking & Budget Forecast Dashboard

**File:** `commit_tracking.lvdash.json`

**Purpose:** Track actual spend against Databricks commit amount with variance analysis and forecasting.

**Key Widgets:**
- Annual Commit - KPI Counter
- YTD Spend - KPI Counter
- Commit Status - KPI Counter
- Monthly Spend vs Target - Line Chart
- YTD Cumulative Spend - Line Chart
- Projected Variance - KPI Counter
- Actual Run Rate - KPI Counter
- Required Run Rate - KPI Counter
- Monthly Spend Detail - Table

**Gold Tables Used:**
- `fact_usage`
- `commit_configurations`

---

## 🔄 Reliability Agent Dashboards

### 4. Job Reliability Dashboard

**File:** `job_reliability.lvdash.json`

**Purpose:** Monitor job execution health, failures, and reliability trends.

**Key Widgets:**
- Success Rate (7d) - KPI Counter
- Failed Jobs Today - KPI Counter
- Avg Duration - KPI Counter
- Job Success Rate Trend - Line Chart
- Failed Jobs - Table
- Job Duration Percentiles - Table

**Gold Tables Used:**
- `fact_job_run_timeline`
- `dim_job`
- `dim_workspace`

---

### 5. Job Optimization Dashboard

**File:** `job_optimization.lvdash.json`

**Purpose:** Identify job optimization opportunities including autoscaling, stale datasets, and cost outliers.

**Key Widgets:**
- Jobs Without Autoscaling - KPI Counter
- Stale Dataset Jobs - KPI Counter
- Jobs on All-Purpose - KPI Counter
- Jobs Without Autoscaling - Table
- Jobs Producing Stale Datasets - Table
- Jobs Using All-Purpose Clusters - Table
- Jobs with Cost Outliers - Table

**Gold Tables Used:**
- `dim_job`
- `dim_cluster`
- `fact_job_run_timeline`
- `fact_table_lineage`
- `fact_usage`

---

## ⚡ Performance Agent Dashboards

### 6. Query Performance Dashboard

**File:** `query_performance.lvdash.json`

**Purpose:** Monitor SQL Warehouse query performance and identify optimization opportunities.

**Key Widgets:**
- Query Volume - KPI Counter
- Avg Duration - KPI Counter
- P95 Duration - KPI Counter
- Query Volume Trend - Line Chart
- Slow Queries - Table
- Queue Time Analysis - Bar Chart

**Gold Tables Used:**
- `fact_query_history`
- `dim_warehouse`

---

### 7. Cluster Utilization Dashboard

**File:** `cluster_utilization.lvdash.json`

**Purpose:** Monitor cluster resource utilization for right-sizing recommendations.

**Key Widgets:**
- Avg CPU % - KPI Counter
- Avg Memory % - KPI Counter
- Active Clusters - KPI Counter
- CPU Utilization Distribution - Bar Chart
- Underutilized Clusters - Table

**Gold Tables Used:**
- `fact_node_timeline`
- `dim_cluster`
- `fact_usage`

---

### 8. DBR Migration Dashboard

**File:** `dbr_migration.lvdash.json`

**Purpose:** Track Databricks Runtime version adoption and identify workloads on legacy runtimes.

**Key Widgets:**
- Jobs on Legacy DBR - KPI Counter
- Serverless Adoption % - KPI Counter
- Current DBR Usage % - KPI Counter
- DBR Version Distribution - Bar Chart
- Serverless vs Classic - Pie Chart
- Jobs on Legacy Runtime - Table

**Gold Tables Used:**
- `dim_job`
- `dim_cluster`
- `fact_usage`
- `fact_job_run_timeline`

---

## 🔒 Security Agent Dashboards

### 9. Security Audit Dashboard

**File:** `security_audit.lvdash.json`

**Purpose:** Monitor data access patterns and security compliance.

**Key Widgets:**
- Total Events - KPI Counter
- Unique Users - KPI Counter
- Failed Actions - KPI Counter
- User Activity Summary - Table
- Most Accessed Tables - Bar Chart
- Sensitive Table Access - Table

**Gold Tables Used:**
- `fact_table_lineage`
- `dim_workspace`

---

### 10. Data Governance Hub Dashboard

**File:** `governance_hub.lvdash.json`

**Purpose:** Comprehensive data governance tracking including asset usage, tag coverage, and lineage.

**Key Widgets:**
- Total Tables - KPI Counter
- Active Tables - KPI Counter
- Tag Coverage % - KPI Counter
- Active vs Inactive Tables - Pie Chart
- Read/Write Activity Trend - Line Chart
- Top Users by Table Access - Table
- Tables Without Comments - Table
- Inactive Tables - Table

**Gold Tables Used:**
- `fact_table_lineage`
- `fact_usage`
- `information_schema.tables`

---

## ✅ Quality Agent Dashboards

### 11. Table Health Advisor Dashboard

**File:** `table_health.lvdash.json`

**Purpose:** Monitor Delta table health, optimization status, and storage patterns.

**Key Widgets:**
- Total Storage (GB) - KPI Counter
- Total Tables - KPI Counter
- Need Optimization - KPI Counter
- Table Size Distribution - Bar Chart
- File Count Distribution - Pie Chart
- Largest Tables - Table
- Tables Needing Optimization - Table
- Empty Tables - Table

**Gold Tables Used:**
- `fact_information_schema_table_storage`

---

## Implementation Details

### Grid System

All dashboards use a **6-column grid** (NOT 12!):

```json
{
  "position": {
    "x": 0,     // Column position: 0-5
    "y": 0,     // Row position
    "width": 3, // Width: 1, 2, 3, 4, or 6
    "height": 6 // Height: 2 (KPI), 6 (chart), 9 (large)
  }
}
```

### Widget Version Reference

| Widget Type | Version |
|-------------|---------|
| KPI Counter | 2 |
| Bar Chart | 3 |
| Line Chart | 3 |
| Pie Chart | 3 |
| Table | 1 |
| Filter | 2 |

### Variable Substitution

All dashboards use these variables:
- `${catalog}` - Unity Catalog name
- `${gold_schema}` - Gold layer schema
- `${warehouse_id}` - SQL Warehouse ID

---

## Deployment

### Using Deploy Script

```bash
# Deploy all dashboards
databricks bundle run -t dev dashboard_deployment_job

# Or run the deployment notebook directly
```

### Manual Deployment

1. Open the `.lvdash.json` file
2. Replace variables with actual values
3. Import via Databricks UI: Dashboards → Import

---

## Dashboard Statistics

| Metric | Count |
|--------|-------|
| Total Dashboards | 11 |
| KPI Widgets | 32 |
| Charts | 14 |
| Tables | 19 |
| Total Widgets | 65+ |

### By Agent Domain

| Domain | Dashboard Count | KPI Count |
|--------|----------------|-----------|
| 💰 Cost | 3 | 12 |
| 🔄 Reliability | 2 | 6 |
| ⚡ Performance | 3 | 9 |
| 🔒 Security | 2 | 6 |
| ✅ Quality | 1 | 3 |

---

## TVF and Metric View Usage

### Dashboards Using TVFs

| Dashboard | TVFs Referenced |
|-----------|-----------------|
| Cost Management | `get_top_cost_contributors`, `get_cost_by_owner` |
| Job Reliability | `get_failed_jobs`, `get_job_success_rate` |
| Query Performance | `get_slow_queries`, `get_warehouse_utilization` |
| Cluster Utilization | `get_cluster_utilization` |

### Dashboards Using Metric Views

| Dashboard | Metric Views |
|-----------|--------------|
| Executive Overview | `cost_analytics`, `job_performance` |
| Cost Management | `cost_analytics` |
| Job Reliability | `job_performance` |
| Query Performance | `query_performance` |
| Cluster Utilization | `cluster_efficiency` |

---

## References

- [Databricks Lakeview Documentation](https://docs.databricks.com/visualizations/lakeview)
- [Dashboard JSON Reference](https://docs.databricks.com/api/workspace/lakeview)
- [System Tables Overview](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Cursor Rule 18 - AI/BI Dashboards](../.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)

