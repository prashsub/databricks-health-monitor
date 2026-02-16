# Serverless Compute Standards

> **Document Owner:** Platform Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

Serverless compute is the default for all new workloads. This document defines when and how to use serverless across SQL Warehouses, Jobs, and DLT Pipelines.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **PA-03** | Serverless is default for all new workloads | Critical |
| **PA-03a** | Serverless SQL Warehouses for all SQL | Critical |
| **PA-03b** | Serverless Jobs for notebooks and Python | Critical |
| **PA-03c** | Serverless DLT for all pipelines | Required |

---

## Why Serverless First?

| Benefit | Description |
|---------|-------------|
| **Instant startup** | Seconds vs 5-10 minutes |
| **Auto-scaling** | No manual configuration |
| **Pay-per-use** | No idle time costs |
| **Built-in Photon** | 2-8x performance |
| **30-50% cost reduction** | Compared to classic clusters |

### Classic Compute Exceptions

| Exception | Justification | Approval Required |
|-----------|---------------|-------------------|
| GPU workloads | ML training with GPUs | Platform Architect |
| 24/7 Streaming | Long-running streams | Platform Architect |
| Specialty libraries | Native C/C++ dependencies | Platform Engineer |

---

## Serverless SQL Warehouses

### Configuration

```yaml
resources:
  warehouses:
    analytics_warehouse:
      name: "[${bundle.target}] Analytics Warehouse"
      warehouse_type: "SERVERLESS"
      cluster_size: "Small"
      auto_stop_mins: 10
      enable_photon: true
      min_num_clusters: 1
      max_num_clusters: 4
```

### Sizing Guide

| Size | vCPUs | Use Case |
|------|-------|----------|
| 2X-Small | 4 | Development |
| Small | 16 | Standard analytics |
| Medium | 32 | Heavy dashboards, Genie |
| Large | 64 | Complex queries |

---

## Serverless Jobs

### Mandatory Configuration

```yaml
resources:
  jobs:
    my_job:
      name: "[${bundle.target}] My Job"
      
      # MANDATORY: Serverless environment
      environments:
        - environment_key: "default"
          spec:
            environment_version: "4"
            dependencies:
              - "pandas==2.0.3"
      
      tasks:
        - task_key: main_task
          environment_key: default
          notebook_task:
            notebook_path: ../src/my_notebook.py
```

### Never Do This

```yaml
# ❌ WRONG: Classic cluster configuration
job_clusters:
  - job_cluster_key: "my_cluster"
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      node_type_id: "i3.xlarge"
```

---

## Serverless DLT Pipelines

```yaml
resources:
  pipelines:
    silver_pipeline:
      name: "[${bundle.target}] Silver Pipeline"
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      serverless: true        # MANDATORY
      photon: true            # MANDATORY
      channel: CURRENT
      edition: ADVANCED
```

---

## Cost Monitoring

```sql
SELECT 
    usage_date,
    workspace_id,
    sku_name,
    SUM(usage_quantity) as total_dbus,
    SUM(list_cost) as total_cost
FROM system.billing.usage
WHERE sku_name LIKE '%SERVERLESS%'
    AND usage_date >= CURRENT_DATE - 30
GROUP BY 1, 2, 3
ORDER BY total_cost DESC;
```

---

## Validation Checklist

### SQL Warehouses
- [ ] Warehouse type is SERVERLESS
- [ ] Photon enabled
- [ ] Auto-stop configured (5-15 min)

### Jobs
- [ ] `environments` block defined
- [ ] `environment_key` on every task
- [ ] No `job_clusters` or `new_cluster`

### DLT Pipelines
- [ ] `serverless: true` set
- [ ] `photon: true` set
- [ ] No cluster configuration

---

## Related Documents

- [Platform Overview](10-platform-overview.md)
- [Cluster Policies](13-cluster-policies.md)

---

## References

- [Performance Efficiency Best Practices](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/performance-efficiency/best-practices)
- [Serverless SQL Warehouses](https://docs.databricks.com/sql/admin/serverless.html)
- [Serverless Jobs](https://docs.databricks.com/jobs/serverless.html)
