# Performance Domain Metric Views

The Performance Domain provides query performance and cluster utilization analytics for optimizing Databricks compute resources.

## Views in This Domain

| View | Source | Primary Use Case |
|------|--------|------------------|
| `mv_query_performance` | `fact_query_history` | SQL Warehouse query metrics |
| `mv_cluster_utilization` | `fact_node_timeline` | Cluster resource utilization |
| `mv_cluster_efficiency` | `fact_node_timeline` | Cluster efficiency analysis |

---

## mv_query_performance

**Full Name**: `{catalog}.{gold_schema}.mv_query_performance`

### Purpose

SQL Warehouse query performance and efficiency metrics for identifying slow queries and optimizing warehouse configurations.

### Key Features

- **Latency percentiles** (P50, P95, P99)
- **Cache efficiency** metrics
- **Spill detection** for memory issues
- **Query efficiency classification**

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "What's the average query duration?" | `avg_duration_seconds` |
| "Show P95 latency by warehouse" | `p95_duration_seconds` |
| "Which warehouses have high spill?" | `spill_rate` |
| "What's the cache hit rate?" | `cache_hit_rate` |
| "How many queries ran today?" | `total_queries` |

### SQL Examples

```sql
-- Query latency by warehouse
SELECT 
    warehouse_name,
    MEASURE(avg_duration_seconds) as avg_duration,
    MEASURE(p95_duration_seconds) as p95,
    MEASURE(p99_duration_seconds) as p99
FROM mv_query_performance
GROUP BY warehouse_name;

-- Cache performance analysis
SELECT 
    warehouse_name,
    MEASURE(cache_hit_rate) as cache_pct,
    MEASURE(spill_rate) as spill_pct,
    MEASURE(total_queries) as queries
FROM mv_query_performance
WHERE query_date >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY warehouse_name;
```

---

## mv_cluster_utilization

**Full Name**: `{catalog}.{gold_schema}.mv_cluster_utilization`

### Purpose

Cluster resource utilization for capacity planning and right-sizing recommendations.

### Key Features

- **CPU and memory utilization** metrics
- **Provisioning status** classification (OPTIMAL, UNDERUTILIZED, OVERPROVISIONED)
- **Savings opportunity** identification
- **Idle time tracking**

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "Which clusters are underutilized?" | Filter by `provisioning_status` |
| "What's average CPU utilization?" | `avg_cpu_utilization` |
| "Show potential savings percentage" | `potential_savings_pct` |
| "How many wasted node hours?" | `wasted_hours` |

### SQL Examples

```sql
-- Utilization by cluster
SELECT 
    cluster_name,
    MEASURE(avg_cpu_utilization) as cpu_pct,
    MEASURE(avg_memory_utilization) as mem_pct,
    MEASURE(potential_savings_pct) as savings_opportunity
FROM mv_cluster_utilization
GROUP BY cluster_name;

-- Underutilized clusters
SELECT 
    cluster_name,
    provisioning_status,
    MEASURE(wasted_hours) as idle_hours,
    MEASURE(potential_savings_pct) as savings_pct
FROM mv_cluster_utilization
WHERE provisioning_status = 'UNDERUTILIZED'
GROUP BY cluster_name, provisioning_status;
```

---

## mv_cluster_efficiency

**Full Name**: `{catalog}.{gold_schema}.mv_cluster_efficiency`

### Purpose

Advanced cluster efficiency and right-sizing analysis for cost optimization.

### Key Features

- **Efficiency score** (0-100 composite metric)
- **Idle percentage** tracking
- **Aggregate problem counts**
- **Total wasted hours**

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "What's our overall efficiency score?" | `efficiency_score` |
| "Show idle percentage by cluster" | `idle_percentage` |
| "How many clusters are underutilized?" | `underutilized_cluster_count` |
| "Total idle node hours?" | `idle_node_hours_total` |

### SQL Examples

```sql
-- Overall efficiency summary
SELECT 
    MEASURE(efficiency_score) as score,
    MEASURE(underutilized_cluster_count) as problem_clusters,
    MEASURE(idle_node_hours_total) as wasted_hours
FROM mv_cluster_efficiency;

-- Efficiency by workspace
SELECT 
    workspace_name,
    MEASURE(efficiency_score) as score,
    MEASURE(idle_percentage) as idle_pct
FROM mv_cluster_efficiency
GROUP BY workspace_name
ORDER BY score ASC;
```

---

## When to Use Which View

| Use Case | Recommended View |
|----------|------------------|
| Query latency analysis | `mv_query_performance` |
| Cache optimization | `mv_query_performance` |
| Cluster right-sizing | `mv_cluster_utilization` |
| Capacity planning | `mv_cluster_utilization` |
| Executive efficiency summary | `mv_cluster_efficiency` |
| Savings identification | `mv_cluster_efficiency` |

## Related Resources

- [TVFs: Performance Agent TVFs](../05-performance-agent-tvfs.md)
