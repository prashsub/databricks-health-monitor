# AI/BI Dashboard Inventory

## Overview

The Databricks Health Monitor project uses a **single unified dashboard** with multiple tabs, organized by Agent Domain. This consolidation provides a better user experience with seamless navigation between different health monitoring views.

## Unified Dashboard: Databricks Health Monitor

**Single Dashboard, 12 Tabs (Pages)**

The deployment script dynamically builds the unified dashboard from individual component JSON files, allowing for modular development while delivering a cohesive user experience.

## Tab Summary by Agent Domain

| Tab Name | Agent Domain | Purpose | Key Widgets |
|---|---|---|---|
| 🏠 Executive Overview | 💰 Cost | Leadership KPIs | 3 KPIs + cost trend + SKU breakdown |
| 💰 Cost Management | 💰 Cost | FinOps analysis | Top contributors, WoW, tag coverage |
| 💰 Commit Tracking | 💰 Cost | Budget vs Actual | Commit variance, run rate, forecast |
| 🔄 Job Reliability | 🔄 Reliability | Job health | Success rate, failures, duration trend |
| 🔄 Job Optimization | 🔄 Reliability | Cost savings | Autoscaling, stale datasets, outliers |
| ⚡ Query Performance | ⚡ Performance | DBA optimization | Slow queries, latency, cache hits |
| ⚡ Cluster Utilization | ⚡ Performance | Right-sizing | CPU/Memory utilization, swap |
| ⚡ DBR Migration | ⚡ Performance | Modernization | Legacy DBR, serverless adoption |
| 🔒 Security Audit | 🔒 Security | Compliance | User activity, sensitive actions |
| 🔒 Governance Hub | 🔒 Security | Data governance | Lineage, tags, inactive tables |
| ✅ Table Health | ✅ Quality | Storage health | File distribution, compaction |
| 🔧 Filters | Global | Cross-tab filtering | Workspace filter, date range |

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

## Architecture: Modular Build

The unified dashboard is built dynamically at deployment time from individual component files:

```
src/dashboards/
├── deploy_dashboards.py          # Deployment script (builds + deploys)
├── build_unified_dashboard.py    # Standalone builder (for local testing)
│
├── # Component Files (one per tab):
├── executive_overview.lvdash.json
├── cost_management.lvdash.json
├── commit_tracking.lvdash.json
├── job_reliability.lvdash.json
├── job_optimization.lvdash.json
├── query_performance.lvdash.json
├── cluster_utilization.lvdash.json
├── dbr_migration.lvdash.json
├── security_audit.lvdash.json
├── governance_hub.lvdash.json
├── table_health.lvdash.json
│
└── DASHBOARD_INVENTORY.md        # This file
```

### How It Works

1. **Component Files**: Each tab has its own `.lvdash.json` file for modular development
2. **Build Process**: The deployment script merges all components into one dashboard
3. **Prefix Isolation**: Each tab's widgets and datasets are prefixed to avoid naming conflicts
4. **Variable Substitution**: `${catalog}`, `${gold_schema}`, `${warehouse_id}` are replaced at deploy time

### Benefits

- ✅ **Modular Development**: Edit individual tabs without affecting others
- ✅ **Version Control**: Clear diffs for each tab
- ✅ **Single Dashboard UX**: Users navigate via tabs, not separate dashboards
- ✅ **Consistent Filters**: Global filters apply across all tabs
- ✅ **Easier Maintenance**: 1 dashboard to manage instead of 11

---

## Deployment

### Deploy Unified Dashboard

```bash
# Deploy the unified dashboard
databricks bundle run -t dev dashboard_deployment_job
```

### Local Testing (Build Only)

```bash
# Build unified JSON locally (for testing)
cd src/dashboards
python build_unified_dashboard.py
# Output: health_monitor_unified.lvdash.json
```

### Manual Import

1. Run `build_unified_dashboard.py` locally
2. Replace `${catalog}`, `${gold_schema}`, `${warehouse_id}` in output JSON
3. Import via Databricks UI: Dashboards → Import

---

## Dashboard Statistics

| Metric | Count |
|--------|-------|
| Total Dashboards | **1 (Unified)** |
| Total Tabs/Pages | 12 |
| KPI Widgets | 32 |
| Charts | 14 |
| Tables | 19 |
| Total Widgets | 65+ |
| Total Datasets | 60+ |

### Widgets by Agent Domain

| Domain | Tabs | KPI Count | Charts | Tables |
|--------|------|-----------|--------|--------|
| 💰 Cost | 3 | 12 | 4 | 5 |
| 🔄 Reliability | 2 | 6 | 4 | 4 |
| ⚡ Performance | 3 | 9 | 6 | 5 |
| 🔒 Security | 2 | 6 | 4 | 4 |
| ✅ Quality | 1 | 3 | 2 | 3 |
| 🔧 Filters | 1 | 0 | 0 | 0 |

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



