# Compute Configuration Standards

> **Document Owner:** Platform Team | **Status:** Approved | **Last Updated:** February 2026

## Overview

This document defines compute configuration standards for the Databricks platform. Serverless compute is the mandatory default for all new workloads.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **CMP-01** | Use serverless compute when supported | Critical |
| **CMP-02** | Use standard access mode for most workloads | Required |
| **CMP-03** | Require compute policies for classic clusters | Required |
| **CMP-04** | Enable Photon for complex transformations | Recommended |
| **CMP-05** | Right-size clusters based on workload type | Required |

---

## CMP-01: Serverless First

### Rule
Serverless compute is mandatory for all new workloads where supported. Classic clusters require documented justification.

### Why It Matters
- Zero configuration and management overhead
- Automatic scaling based on workload
- No idle costs—pay only for usage
- Always running latest optimizations

### Serverless Availability

| Workload | Serverless | Configuration |
|----------|------------|---------------|
| SQL queries | ✅ | Serverless SQL Warehouse |
| Notebooks | ✅ | Serverless compute |
| Jobs | ✅ | Environment block in Asset Bundle |
| DLT Pipelines | ✅ | `serverless: true` |
| GPU workloads | ❌ | Use dedicated access mode |

### Implementation

**Serverless Job:**
```yaml
environments:
  - environment_key: default
    spec:
      environment_version: "4"
      dependencies:
        - pandas==2.0.3

tasks:
  - task_key: process
    environment_key: default
    notebook_task:
      notebook_path: ../src/process.py
```

**Serverless SQL Warehouse:**
```yaml
warehouses:
  analytics:
    warehouse_type: PRO
    enable_serverless_compute: true
    auto_stop_mins: 10
```

**Serverless DLT:**
```yaml
pipelines:
  silver:
    serverless: true
    photon: true
```

---

## CMP-02: Standard Access Mode

### Rule
Use standard (shared) access mode for most workloads. Dedicated access mode is only for GPU, RDD APIs, R, or container services.

### Why It Matters
- Multi-user with full user isolation
- More cost-effective through resource sharing
- Enforces Unity Catalog governance

### Decision Guide

```
Need GPU, RDD, R, or Container Service?
├── YES → Dedicated Access Mode
└── NO → Standard Access Mode (default)
```

### Configuration
```yaml
# Standard access mode (default)
new_cluster:
  data_security_mode: USER_ISOLATION
  
# Dedicated (only when required)
new_cluster:
  data_security_mode: SINGLE_USER
```

---

## CMP-03: Compute Policies

### Rule
All classic clusters must be created through approved compute policies. Unrestricted cluster creation is prohibited.

### Why It Matters
- Enforces cost and security guardrails
- Standardizes configurations across teams
- Simplifies cluster creation for end users

### Standard Policies

| Policy | Use Case | Key Settings |
|--------|----------|--------------|
| Personal Compute | Individual development | Single node, auto-terminate |
| Shared Compute | Team collaboration | Standard access, multi-user |
| Jobs Compute | Production pipelines | Fixed size, optimized |
| ML Compute | Model training | GPU options, larger memory |

### Policy Example
```json
{
  "name": "Data Engineering - Standard",
  "definition": {
    "spark_version": { "type": "fixed", "value": "14.3.x-scala2.12" },
    "data_security_mode": { "type": "fixed", "value": "USER_ISOLATION" },
    "autotermination_minutes": { "type": "range", "minValue": 10, "maxValue": 120 },
    "num_workers": { "type": "range", "minValue": 1, "maxValue": 10 }
  }
}
```

---

## CMP-04: Photon for Complex Workloads

### Rule
Enable Photon for workloads with complex joins, large aggregations, or frequent disk access.

### Why It Matters
- Significant performance improvement for complex SQL
- Native vectorized query execution
- Optimized for wide transformations

### When Photon Helps Most

| Workload | Benefit |
|----------|---------|
| Complex joins | High |
| Large aggregations | High |
| Large table scans | High |
| Simple ETL (<2 sec queries) | Low |

### Implementation
```yaml
new_cluster:
  spark_version: "14.3.x-photon-scala2.12"
  runtime_engine: PHOTON

# Or for DLT
pipelines:
  gold:
    photon: true
```

---

## CMP-05: Workload-Based Sizing

### Rule
Size clusters based on workload characteristics. Use fewer larger workers for shuffle-heavy jobs; use single-node for interactive analysis.

### Sizing Guide

| Workload | Workers | Instance Size | Photon |
|----------|---------|---------------|--------|
| Data Analysis | 0 (single node) | Large | Optional |
| Basic ETL | 2-4 | Small/Medium | No |
| Complex ETL | 2-4 | Large | Yes |
| ML Training | 0-2 | Large | No |
| Streaming | 4-8 (fixed) | Medium | Optional |

### Auto-Scaling Guidelines

| Workload | Auto-Scaling |
|----------|--------------|
| Interactive notebooks | ✅ Yes |
| Variable batch ETL | ✅ Yes |
| Streaming | ❌ No (fixed size) |
| ML Training | ❌ No (fixed size) |

---

## Validation Checklist

- [ ] Serverless used for all supported workloads
- [ ] Classic compute justified and documented
- [ ] Compute policies enforced for classic clusters
- [ ] Standard access mode unless GPU/RDD/R required
- [ ] Photon enabled for complex transformations
- [ ] Auto-termination configured on all clusters

---

## Quick Reference

```yaml
# Serverless job (preferred)
environments:
  - environment_key: default
    spec:
      environment_version: "4"

# Standard access cluster
new_cluster:
  data_security_mode: USER_ISOLATION
  spark_version: "14.3.x-scala2.12"

# Photon-enabled cluster
new_cluster:
  spark_version: "14.3.x-photon-scala2.12"
  runtime_engine: PHOTON

# Single-node for analysis
new_cluster:
  num_workers: 0
  driver_node_type_id: "i3.2xlarge"
```

---

## References

- [Compute Configuration Recommendations](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)
- [Serverless Compute](https://docs.databricks.com/en/compute/serverless/)
- [Photon](https://docs.databricks.com/en/compute/photon.html)
- [Compute Policies](https://docs.databricks.com/en/admin/clusters/policies.html)
