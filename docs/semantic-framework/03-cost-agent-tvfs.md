# 03 - Cost Agent TVFs

## Overview

The Cost Agent domain provides **15 Table-Valued Functions** for comprehensive cost analysis, chargeback attribution, and spend optimization. These TVFs query the `fact_usage` table and related dimensions to provide insights into Databricks spending patterns.

## TVF Summary

| # | TVF Name | Purpose | Parameters |
|---|----------|---------|------------|
| 1 | `get_top_cost_contributors` | Top N cost contributors by workspace/SKU | start_date, end_date, top_n |
| 2 | `get_cost_trend_by_sku` | Daily cost trends by SKU | start_date, end_date, sku_filter |
| 3 | `get_cost_by_owner` | Cost breakdown by resource owner | start_date, end_date, top_n |
| 4 | `get_cost_by_tag` | Tag-based cost allocation | start_date, end_date, tag_key |
| 5 | `get_untagged_resources` | Resources without proper tagging | start_date, end_date |
| 6 | `get_cost_anomalies` | Cost spikes vs baseline | days_back, threshold_pct |
| 7 | `get_daily_cost_summary` | Daily cost rollup with comparison | start_date, end_date |
| 8 | `get_workspace_cost_comparison` | Cross-workspace cost analysis | start_date, end_date |
| 9 | `get_serverless_vs_classic_cost` | Serverless vs classic compute costs | start_date, end_date |
| 10 | `get_job_cost_breakdown` | Cost per job with efficiency metrics | start_date, end_date, top_n |
| 11 | `get_warehouse_cost_analysis` | SQL Warehouse cost efficiency | start_date, end_date |
| 12 | `get_cost_forecast` | Simple cost projection | days_back, forecast_days |
| 13 | `get_cost_by_cluster_type` | Cost by cluster configuration | start_date, end_date |
| 14 | `get_storage_cost_analysis` | Storage costs by catalog/schema | start_date, end_date |
| 15 | `get_cost_efficiency_metrics` | Cost per unit metrics | start_date, end_date |

---

## TVF Definitions

### 1. get_top_cost_contributors

**Purpose**: Identify the highest-cost workspaces, SKUs, or resources for prioritized optimization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| top_n | INT | No | 10 | Number of results to return |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| rank | INT | Rank by total cost |
| workspace_id | STRING | Workspace identifier |
| workspace_name | STRING | Workspace display name |
| sku_name | STRING | SKU name |
| total_dbu_cost | DOUBLE | Total DBU cost in USD |
| total_cloud_cost | DOUBLE | Total cloud provider cost |
| total_cost | DOUBLE | Combined DBU + cloud cost |
| dbu_count | DOUBLE | Total DBUs consumed |
| cost_pct_of_total | DOUBLE | Percentage of total spend |

**Example Queries**:
```sql
-- Get top 10 cost drivers for last month
SELECT * FROM TABLE(get_top_cost_contributors('2024-12-01', '2024-12-31', 10));

-- Get top 5 for December
SELECT * FROM TABLE(get_top_cost_contributors('2024-12-01', '2024-12-31', 5));
```

**Natural Language Examples**:
- "What are the top 10 cost drivers this month?"
- "Which workspaces are spending the most?"
- "Show me the biggest spenders"

---

### 2. get_cost_trend_by_sku

**Purpose**: Analyze daily cost trends by SKU to identify spending patterns and anomalies.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| sku_filter | STRING | No | '%' | SKU pattern filter (SQL LIKE) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| usage_date | DATE | Date of usage |
| sku_name | STRING | SKU identifier |
| daily_dbu_cost | DOUBLE | DBU cost for the day |
| daily_cloud_cost | DOUBLE | Cloud cost for the day |
| daily_total_cost | DOUBLE | Total cost for the day |
| daily_dbu_count | DOUBLE | DBUs consumed |
| day_over_day_change | DOUBLE | Percentage change from previous day |

**Example Queries**:
```sql
-- All SKU trends for last week
SELECT * FROM TABLE(get_cost_trend_by_sku('2024-12-24', '2024-12-31', '%'));

-- Only Jobs Compute SKUs
SELECT * FROM TABLE(get_cost_trend_by_sku('2024-12-01', '2024-12-31', '%JOBS%'));
```

---

### 3. get_cost_by_owner

**Purpose**: Break down costs by resource owner for chargeback and accountability.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| top_n | INT | No | 20 | Number of owners to return |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| rank | INT | Rank by total cost |
| owner | STRING | Resource owner (email or ID) |
| total_dbu_cost | DOUBLE | Owner's DBU cost |
| total_cloud_cost | DOUBLE | Owner's cloud cost |
| total_cost | DOUBLE | Owner's total cost |
| resource_count | BIGINT | Number of resources owned |
| avg_cost_per_resource | DOUBLE | Average cost per resource |

**Natural Language Examples**:
- "Who are the top spenders?"
- "Show me cost by owner"
- "Which users have the highest cloud bills?"

---

### 4. get_cost_by_tag

**Purpose**: Analyze costs by custom tags for project/team allocation and chargeback.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| tag_key | STRING | No | 'team' | Tag key to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| tag_value | STRING | Tag value |
| total_dbu_cost | DOUBLE | Cost for this tag value |
| total_cloud_cost | DOUBLE | Cloud cost for this tag |
| total_cost | DOUBLE | Combined cost |
| resource_count | BIGINT | Resources with this tag |
| cost_pct | DOUBLE | Percentage of tagged spend |

**Example Queries**:
```sql
-- Cost by team tag
SELECT * FROM TABLE(get_cost_by_tag('2024-12-01', '2024-12-31', 'team'));

-- Cost by project tag
SELECT * FROM TABLE(get_cost_by_tag('2024-12-01', '2024-12-31', 'project'));
```

---

### 5. get_untagged_resources

**Purpose**: Identify resources without proper tagging for governance and chargeback compliance.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| workspace_id | STRING | Workspace identifier |
| workspace_name | STRING | Workspace display name |
| resource_type | STRING | Type of resource |
| resource_id | STRING | Resource identifier |
| owner | STRING | Resource owner |
| total_cost | DOUBLE | Cost incurred |
| days_active | BIGINT | Days with usage |

**Natural Language Examples**:
- "What resources are missing tags?"
- "Show me untagged compute costs"
- "Which resources need tagging?"

---

### 6. get_cost_anomalies

**Purpose**: Detect cost spikes that deviate significantly from historical baseline.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |
| threshold_pct | DOUBLE | No | 50.0 | Percentage deviation threshold |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| anomaly_date | DATE | Date of anomaly |
| workspace_id | STRING | Affected workspace |
| sku_name | STRING | Affected SKU |
| actual_cost | DOUBLE | Actual cost on anomaly date |
| baseline_cost | DOUBLE | Expected baseline cost |
| deviation_pct | DOUBLE | Percentage deviation |
| anomaly_severity | STRING | HIGH/MEDIUM/LOW |

**Example Queries**:
```sql
-- Find anomalies >50% deviation in last 30 days
SELECT * FROM TABLE(get_cost_anomalies(30, 50.0));

-- More sensitive detection (>25% deviation)
SELECT * FROM TABLE(get_cost_anomalies(30, 25.0));
```

---

### 7. get_daily_cost_summary

**Purpose**: Daily cost rollup with day-over-day and week-over-week comparisons.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| usage_date | DATE | Date |
| total_dbu_cost | DOUBLE | Total DBU cost |
| total_cloud_cost | DOUBLE | Total cloud cost |
| total_cost | DOUBLE | Combined cost |
| dod_change_pct | DOUBLE | Day-over-day change % |
| wow_change_pct | DOUBLE | Week-over-week change % |
| running_total | DOUBLE | Cumulative total |

---

### 8. get_workspace_cost_comparison

**Purpose**: Compare costs across workspaces for cross-team analysis.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| workspace_id | STRING | Workspace identifier |
| workspace_name | STRING | Workspace display name |
| total_cost | DOUBLE | Total cost |
| cost_rank | INT | Rank by cost |
| pct_of_total | DOUBLE | Percentage of total spend |
| primary_sku | STRING | Most used SKU |
| primary_sku_cost | DOUBLE | Cost of primary SKU |

---

### 9. get_serverless_vs_classic_cost

**Purpose**: Compare serverless and classic compute costs to guide migration decisions.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| compute_type | STRING | SERVERLESS or CLASSIC |
| total_dbu_cost | DOUBLE | DBU cost |
| total_cloud_cost | DOUBLE | Cloud cost |
| total_cost | DOUBLE | Combined cost |
| dbu_count | DOUBLE | DBUs consumed |
| cost_per_dbu | DOUBLE | Efficiency metric |

---

### 10. get_job_cost_breakdown

**Purpose**: Analyze cost per job with efficiency metrics for optimization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| top_n | INT | No | 20 | Number of jobs to return |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| rank | INT | Rank by cost |
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| total_cost | DOUBLE | Total job cost |
| run_count | BIGINT | Number of runs |
| avg_cost_per_run | DOUBLE | Average cost per execution |
| total_duration_hours | DOUBLE | Total runtime |
| cost_per_hour | DOUBLE | Cost efficiency |

---

### 11. get_warehouse_cost_analysis

**Purpose**: SQL Warehouse cost and efficiency analysis.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| warehouse_id | STRING | Warehouse identifier |
| warehouse_name | STRING | Warehouse display name |
| total_cost | DOUBLE | Total cost |
| query_count | BIGINT | Queries executed |
| cost_per_query | DOUBLE | Efficiency metric |
| avg_query_duration_sec | DOUBLE | Average query time |
| total_uptime_hours | DOUBLE | Total uptime |

---

### 12. get_cost_forecast

**Purpose**: Simple linear projection of future costs based on recent trends.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Historical days for baseline |
| forecast_days | INT | No | 30 | Days to forecast |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| forecast_date | DATE | Projected date |
| projected_cost | DOUBLE | Forecasted cost |
| lower_bound | DOUBLE | Conservative estimate |
| upper_bound | DOUBLE | Aggressive estimate |
| confidence | STRING | Forecast confidence level |

---

### 13. get_cost_by_cluster_type

**Purpose**: Analyze costs by cluster configuration and type.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| cluster_type | STRING | Cluster type/configuration |
| total_cost | DOUBLE | Total cost |
| dbu_count | DOUBLE | DBUs consumed |
| cluster_count | BIGINT | Number of clusters |
| avg_cost_per_cluster | DOUBLE | Cost efficiency |

---

### 14. get_storage_cost_analysis

**Purpose**: Storage costs breakdown by catalog and schema.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Catalog name |
| schema_name | STRING | Schema name |
| storage_cost | DOUBLE | Storage cost |
| storage_gb | DOUBLE | Storage size in GB |
| cost_per_gb | DOUBLE | Cost efficiency |

---

### 15. get_cost_efficiency_metrics

**Purpose**: Cost-per-unit metrics for benchmarking and optimization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| metric_name | STRING | Efficiency metric name |
| metric_value | DOUBLE | Calculated value |
| comparison_period_value | DOUBLE | Previous period value |
| change_pct | DOUBLE | Period-over-period change |
| status | STRING | IMPROVED/DEGRADED/STABLE |

---

## SQL Source

**File Location**: `src/semantic/tvfs/cost_tvfs.sql`

**Tables Used**:
- `fact_usage` - Primary billing and usage data
- `dim_workspace` - Workspace metadata
- `dim_sku` - SKU pricing information

## Next Steps

- **[04-Reliability Agent TVFs](04-reliability-agent-tvfs.md)**: Job health and SLA tracking
- **[09-Usage Examples](09-usage-examples.md)**: More query examples

