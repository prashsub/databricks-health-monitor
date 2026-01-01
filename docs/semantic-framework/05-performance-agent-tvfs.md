# 05 - Performance Agent TVFs

## Overview

The Performance Agent domain provides **16 Table-Valued Functions** for query performance analysis and compute optimization. This domain is split into two categories:
- **Query Performance (10 TVFs)**: SQL query latency, warehouse efficiency, slow query identification
- **Compute Optimization (6 TVFs)**: Cluster utilization, right-sizing, autoscaling analysis

## TVF Summary

### Query Performance TVFs (10)

| # | TVF Name | Purpose | Parameters |
|---|----------|---------|------------|
| 1 | `get_slow_queries` | Queries exceeding duration threshold | days_back, duration_threshold_sec |
| 2 | `get_query_latency_percentiles` | P50/P90/P95/P99 latencies | start_date, end_date |
| 3 | `get_warehouse_utilization` | SQL Warehouse efficiency metrics | start_date, end_date |
| 4 | `get_query_volume_trends` | Query volume over time | start_date, end_date |
| 5 | `get_top_users_by_query_count` | Most active query users | start_date, end_date, top_n |
| 6 | `get_query_error_analysis` | Failed query patterns | days_back |
| 7 | `get_spill_analysis` | Queries with data spill | days_back |
| 8 | `get_query_queue_analysis` | Queue time metrics | start_date, end_date |
| 9 | `get_warehouse_scaling_events` | Auto-scaling activity | days_back |
| 10 | `get_query_cost_by_user` | Query costs per user | start_date, end_date, top_n |

### Compute Optimization TVFs (6)

| # | TVF Name | Purpose | Parameters |
|---|----------|---------|------------|
| 11 | `get_cluster_utilization` | Cluster resource utilization | start_date, end_date |
| 12 | `get_underutilized_clusters` | Low utilization clusters | days_back |
| 13 | `get_cluster_cost_efficiency` | Cost per compute unit | start_date, end_date |
| 14 | `get_cluster_rightsizing` | Right-sizing recommendations | days_back |
| 15 | `get_jobs_without_autoscaling` | Jobs not using autoscaling | days_back |
| 16 | `get_jobs_on_legacy_dbr` | Jobs on old DBR versions | days_back |

---

## Query Performance TVF Definitions

### 1. get_slow_queries

**Purpose**: Identify slow-running queries for optimization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |
| duration_threshold_sec | INT | No | 30 | Slowness threshold in seconds |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| statement_id | STRING | Query identifier |
| executed_by | STRING | User who ran query |
| warehouse_id | STRING | Warehouse used |
| warehouse_name | STRING | Warehouse display name |
| duration_sec | DOUBLE | Query duration |
| rows_returned | BIGINT | Result row count |
| bytes_scanned | BIGINT | Data scanned |
| start_time | TIMESTAMP | Query start |
| query_text_preview | STRING | First 200 chars of query |

**Example Queries**:
```sql
-- Queries over 30 seconds in last 7 days
SELECT * FROM TABLE(get_slow_queries(7, 30));

-- Queries over 60 seconds
SELECT * FROM TABLE(get_slow_queries(7, 60));
```

**Natural Language Examples**:
- "What are the slowest queries?"
- "Show me queries taking over a minute"
- "Which queries need optimization?"

---

### 2. get_query_latency_percentiles

**Purpose**: Calculate query latency percentiles for SLA monitoring.

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
| query_count | BIGINT | Total queries |
| p50_latency_sec | DOUBLE | Median latency |
| p90_latency_sec | DOUBLE | 90th percentile |
| p95_latency_sec | DOUBLE | 95th percentile |
| p99_latency_sec | DOUBLE | 99th percentile |
| max_latency_sec | DOUBLE | Maximum latency |

---

### 3. get_warehouse_utilization

**Purpose**: SQL Warehouse efficiency and resource utilization metrics.

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
| total_queries | BIGINT | Query count |
| total_runtime_hr | DOUBLE | Total execution time |
| avg_queries_per_day | DOUBLE | Average daily queries |
| avg_concurrent_queries | DOUBLE | Average concurrency |
| peak_concurrent_queries | BIGINT | Maximum concurrency |
| queue_time_pct | DOUBLE | Time spent queuing |

---

### 4. get_query_volume_trends

**Purpose**: Track query volume patterns over time.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| query_date | DATE | Date |
| query_count | BIGINT | Total queries |
| unique_users | BIGINT | Distinct users |
| avg_duration_sec | DOUBLE | Average query time |
| total_bytes_scanned | BIGINT | Data processed |
| dod_change_pct | DOUBLE | Day-over-day change |

---

### 5. get_top_users_by_query_count

**Purpose**: Identify most active query users.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| top_n | INT | No | 20 | Number of users to return |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| rank | INT | Rank by query count |
| user_email | STRING | User email |
| query_count | BIGINT | Total queries |
| total_duration_hr | DOUBLE | Total execution time |
| avg_duration_sec | DOUBLE | Average query duration |
| failed_queries | BIGINT | Queries with errors |
| data_scanned_gb | DOUBLE | Total data processed |

---

### 6. get_query_error_analysis

**Purpose**: Analyze query failures and error patterns.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| error_category | STRING | Categorized error type |
| error_count | BIGINT | Number of occurrences |
| affected_users | BIGINT | Users experiencing error |
| sample_error | STRING | Sample error message |
| first_seen | TIMESTAMP | First occurrence |
| last_seen | TIMESTAMP | Most recent occurrence |

---

### 7. get_spill_analysis

**Purpose**: Identify queries with memory spill for optimization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| statement_id | STRING | Query identifier |
| executed_by | STRING | User who ran query |
| spill_bytes | BIGINT | Bytes spilled to disk |
| duration_sec | DOUBLE | Query duration |
| rows_returned | BIGINT | Result row count |
| query_text_preview | STRING | First 200 chars |
| warehouse_name | STRING | Warehouse used |

---

### 8. get_query_queue_analysis

**Purpose**: Analyze query queuing patterns.

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
| queries_queued | BIGINT | Queries that were queued |
| total_queue_time_sec | DOUBLE | Total queue wait |
| avg_queue_time_sec | DOUBLE | Average queue wait |
| max_queue_time_sec | DOUBLE | Maximum queue wait |
| peak_queue_depth | BIGINT | Maximum queue depth |

---

### 9. get_warehouse_scaling_events

**Purpose**: Track warehouse auto-scaling activity.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| warehouse_id | STRING | Warehouse identifier |
| warehouse_name | STRING | Warehouse display name |
| scale_up_events | BIGINT | Scale up count |
| scale_down_events | BIGINT | Scale down count |
| avg_cluster_count | DOUBLE | Average cluster count |
| max_cluster_count | BIGINT | Peak cluster count |
| min_cluster_count | BIGINT | Minimum clusters |

---

### 10. get_query_cost_by_user

**Purpose**: Query costs attributed to users.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| top_n | INT | No | 20 | Number of users |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| rank | INT | Rank by cost |
| user_email | STRING | User email |
| query_count | BIGINT | Total queries |
| estimated_cost | DOUBLE | Estimated DBU cost |
| total_duration_hr | DOUBLE | Total runtime |
| data_scanned_gb | DOUBLE | Data processed |

---

## Compute Optimization TVF Definitions

### 11. get_cluster_utilization

**Purpose**: Cluster CPU and memory utilization metrics.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| cluster_id | STRING | Cluster identifier |
| cluster_name | STRING | Cluster display name |
| avg_cpu_pct | DOUBLE | Average CPU utilization |
| max_cpu_pct | DOUBLE | Peak CPU |
| avg_memory_pct | DOUBLE | Average memory usage |
| max_memory_pct | DOUBLE | Peak memory |
| total_runtime_hr | DOUBLE | Total uptime |
| node_hours | DOUBLE | Total node-hours |

---

### 12. get_underutilized_clusters

**Purpose**: Identify clusters with low resource utilization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| cluster_id | STRING | Cluster identifier |
| cluster_name | STRING | Cluster display name |
| avg_cpu_pct | DOUBLE | Average CPU (low = underutilized) |
| avg_memory_pct | DOUBLE | Average memory |
| total_cost | DOUBLE | Cost incurred |
| potential_savings | DOUBLE | Estimated savings |
| recommendation | STRING | Right-sizing suggestion |

**Natural Language Examples**:
- "Which clusters are underutilized?"
- "Where can we reduce compute spend?"
- "Show me wasted cluster resources"

---

### 13. get_cluster_cost_efficiency

**Purpose**: Cost efficiency metrics per cluster.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| cluster_id | STRING | Cluster identifier |
| cluster_name | STRING | Cluster display name |
| total_cost | DOUBLE | Total cost |
| jobs_executed | BIGINT | Jobs run |
| cost_per_job | DOUBLE | Cost efficiency |
| total_runtime_hr | DOUBLE | Total runtime |
| cost_per_hour | DOUBLE | Hourly cost |

---

### 14. get_cluster_rightsizing

**Purpose**: Right-sizing recommendations based on utilization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| cluster_id | STRING | Cluster identifier |
| cluster_name | STRING | Cluster display name |
| current_node_type | STRING | Current instance type |
| recommended_node_type | STRING | Suggested instance type |
| current_num_workers | INT | Current worker count |
| recommended_num_workers | INT | Suggested worker count |
| estimated_savings_pct | DOUBLE | Potential savings |
| recommendation_reason | STRING | Why recommended |

---

### 15. get_jobs_without_autoscaling

**Purpose**: Identify jobs that could benefit from autoscaling.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| run_count | BIGINT | Number of runs |
| total_cost | DOUBLE | Total cost |
| avg_duration_min | DOUBLE | Average duration |
| cluster_type | STRING | Fixed cluster type |
| autoscaling_potential | STRING | Potential benefit assessment |

---

### 16. get_jobs_on_legacy_dbr

**Purpose**: Identify jobs running on legacy Databricks Runtime versions.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| dbr_version | STRING | Current DBR version |
| run_count | BIGINT | Number of runs |
| total_cost | DOUBLE | Total cost |
| recommended_dbr | STRING | Suggested upgrade version |
| recommendation | STRING | Upgrade benefit assessment |

**Natural Language Examples**:
- "Which jobs are on old Databricks versions?"
- "Show me jobs needing DBR upgrade"
- "What's running on legacy runtime?"

---

## SQL Source

**File Locations**:
- Query Performance: `src/semantic/tvfs/performance_tvfs.sql`
- Compute Optimization: `src/semantic/tvfs/compute_tvfs.sql`

**Tables Used**:
- `fact_query_history` - SQL query execution data
- `fact_node_timeline` - Cluster node metrics
- `fact_job_run_timeline` - Job execution history
- `fact_usage` - Billing data
- `dim_warehouse` - Warehouse metadata
- `dim_cluster` - Cluster configurations
- `dim_job` - Job definitions

## Next Steps

- **[06-Security Agent TVFs](06-security-agent-tvfs.md)**: Audit and access patterns
- **[09-Usage Examples](09-usage-examples.md)**: More query examples

