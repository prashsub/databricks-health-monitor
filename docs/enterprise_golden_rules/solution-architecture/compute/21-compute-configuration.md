# Compute Configuration Best Practices

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-CMP-001 |
| **Version** | 1.0 |
| **Last Updated** | February 2026 |
| **Owner** | Platform Team |
| **Status** | Approved |

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 2026 | Initial compilation from official Databricks documentation |

### Source References
| Source | URL |
|--------|-----|
| Compute Configuration Recommendations | https://docs.databricks.com/en/compute/cluster-config-best-practices.html |
| Serverless Compute | https://docs.databricks.com/en/compute/serverless/ |
| Photon | https://docs.databricks.com/en/compute/photon.html |

---

## Executive Summary

This document consolidates official Databricks compute configuration best practices. These patterns cover serverless compute adoption, access mode selection, cluster sizing, Photon enablement, and workload-specific configurations.

> **Key Principle:** Prefer serverless compute when supported. It requires no configuration, is always available, and scales according to your workload. For workloads that require classic compute, follow these guidelines for optimal configuration.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| BP-04 | Use serverless compute when supported | 🔴 Critical |
| CMP-01 | Use standard access mode for most workloads | 🟡 Required |
| CMP-02 | Use compute policies for governance | 🟡 Required |
| CMP-03 | Enable Photon for complex transformations | 🟢 Recommended |
| CMP-04 | Right-size clusters based on workload | 🟡 Required |

---

## BP-04: Use Serverless Compute (Critical)

> **Official Recommendation:** "If your workload is supported, Databricks recommends using serverless compute rather than configuring your own compute resource. Serverless compute is the simplest and most reliable compute option. It requires no configuration, is always available, and scales according to your workload." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

### Serverless Benefits

| Benefit | Description |
|---------|-------------|
| **No configuration** | Zero cluster management |
| **Always available** | No cold start delays |
| **Auto-scaling** | Scales to workload automatically |
| **Cost-effective** | Pay per use, no idle costs |
| **Latest features** | Automatic runtime updates |

### Serverless Availability

| Workload Type | Serverless Available | Configuration |
|---------------|---------------------|---------------|
| **SQL Queries** | ✅ Yes | Serverless SQL Warehouse |
| **Notebooks** | ✅ Yes | Serverless compute |
| **Jobs** | ✅ Yes | Serverless environment |
| **DLT Pipelines** | ✅ Yes | `serverless: true` |
| **ML Training** | ⚠️ Limited | Use for small/medium models |
| **GPU Workloads** | ❌ No | Use dedicated access mode |

### Implementation - Serverless Jobs

```yaml
# ✅ CORRECT: Serverless job configuration
resources:
  jobs:
    data_pipeline:
      name: "[${bundle.target}] Data Pipeline"
      
      # Serverless environment
      environments:
        - environment_key: "default"
          spec:
            environment_version: "4"
            dependencies:
              - pandas==2.0.3
              - pyarrow==14.0.1
      
      tasks:
        - task_key: process_data
          environment_key: default
          notebook_task:
            notebook_path: ../src/process.py
```

### Implementation - Serverless SQL Warehouse

```yaml
# ✅ CORRECT: Serverless SQL Warehouse
resources:
  warehouses:
    analytics_warehouse:
      name: "[${bundle.target}] Analytics Warehouse"
      warehouse_type: PRO
      cluster_size: "Small"
      enable_serverless_compute: true
      auto_stop_mins: 10
```

### Implementation - Serverless DLT

```yaml
# ✅ CORRECT: Serverless DLT pipeline
resources:
  pipelines:
    silver_pipeline:
      name: "[${bundle.target}] Silver Pipeline"
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      serverless: true  # ✅ Enable serverless
      photon: true
```

---

## CMP-01: Use Standard Access Mode (Required)

> **Official Recommendation:** "Standard compute can be shared by multiple users and groups while still enforcing user isolation and all user- and group-level data access permissions. This makes it an easier-to-manage, cost-effective option for most workloads." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

### Access Mode Comparison

| Feature | Standard (Shared) | Dedicated (Single-User) |
|---------|-------------------|------------------------|
| **Multi-user** | ✅ Yes | ❌ No |
| **User isolation** | ✅ Yes | N/A |
| **Access control** | ✅ Fine-grained | ✅ Full |
| **Cost efficiency** | ✅ High (shared) | ❌ Low (dedicated) |
| **Unity Catalog** | ✅ Required | ✅ Required |
| **RDD APIs** | ❌ No | ✅ Yes |
| **GPU support** | ❌ Limited | ✅ Full |
| **R language** | ❌ No | ✅ Yes |
| **Container Service** | ❌ No | ✅ Yes |

### Decision Tree

```
Do you need GPU, RDD, R, or Container Service?
├── YES → Dedicated Access Mode
└── NO → Standard Access Mode (recommended)
    └── Is this for multiple users?
        ├── YES → Standard (shared)
        └── NO → Still prefer Standard (simpler)
```

### Implementation

```yaml
# ✅ CORRECT: Standard access mode (recommended)
job_clusters:
  - job_cluster_key: shared_cluster
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      num_workers: 4
      data_security_mode: USER_ISOLATION  # Standard access mode

# Only when needed: Dedicated access mode
job_clusters:
  - job_cluster_key: gpu_cluster
    new_cluster:
      spark_version: "14.3.x-gpu-ml-scala2.12"
      num_workers: 2
      node_type_id: "g5.xlarge"
      data_security_mode: SINGLE_USER  # Dedicated for GPU
```

---

## CMP-02: Use Compute Policies (Required)

> **Official Recommendation:** "If you are creating new compute from scratch, Databricks recommends using compute policies. Compute policies let you create preconfigured compute resources designed for specific purposes, such as personal compute, shared compute, power users, and jobs." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

### Policy Benefits

| Benefit | Description |
|---------|-------------|
| **Governance** | Enforce standards across teams |
| **Cost control** | Limit instance types, sizes |
| **Simplicity** | Reduce configuration decisions |
| **Security** | Ensure Unity Catalog compliance |

### Recommended Policies

| Policy | Use Case | Key Settings |
|--------|----------|--------------|
| **Personal Compute** | Individual development | Single node, auto-terminate |
| **Shared Compute** | Team collaboration | Standard access, multi-user |
| **Jobs Compute** | Production pipelines | Fixed size, optimized |
| **ML Compute** | Model training | GPU options, larger memory |

### Policy Configuration Example

```json
{
  "name": "Data Engineering - Standard",
  "definition": {
    "spark_version": {
      "type": "fixed",
      "value": "14.3.x-scala2.12"
    },
    "data_security_mode": {
      "type": "fixed",
      "value": "USER_ISOLATION"
    },
    "autotermination_minutes": {
      "type": "range",
      "minValue": 10,
      "maxValue": 120,
      "defaultValue": 30
    },
    "num_workers": {
      "type": "range",
      "minValue": 1,
      "maxValue": 10,
      "defaultValue": 2
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["i3.xlarge", "i3.2xlarge", "m5.xlarge", "m5.2xlarge"]
    }
  }
}
```

---

## CMP-03: Enable Photon for Complex Transformations (Recommended)

> **Official Recommendation:** "Many workloads benefit from Photon, but it is most beneficial for SQL workloads and DataFrame operations involving complex transformations, such as joins, aggregations, and data scans on large tables." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

### When Photon Helps Most

| Workload Type | Photon Benefit |
|---------------|----------------|
| **Complex joins** | ✅ High |
| **Large aggregations** | ✅ High |
| **Data scans (large tables)** | ✅ High |
| **Wide tables** | ✅ High |
| **Frequent disk access** | ✅ High |
| **Repeated data processing** | ✅ Medium |
| **Simple ETL (narrow transforms)** | ⚠️ Low |
| **Queries < 2 seconds** | ⚠️ Low |

### When Photon May Not Help

> **Official Recommendation:** "Simple batch ETL jobs that do not involve wide transformations or large data volumes may see minimal impact from enabling Photon, especially if queries typically complete in under two seconds." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

### Implementation

```yaml
# ✅ Enable Photon for complex workloads
job_clusters:
  - job_cluster_key: etl_cluster
    new_cluster:
      spark_version: "14.3.x-photon-scala2.12"  # Photon runtime
      runtime_engine: PHOTON
      num_workers: 4

# DLT with Photon
resources:
  pipelines:
    gold_pipeline:
      name: "[${bundle.target}] Gold Pipeline"
      photon: true  # ✅ Enable Photon
      serverless: true
```

### Photon Cost-Benefit Analysis

```
┌─────────────────────────────────────────────────────────────┐
│                    PHOTON DECISION MATRIX                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Workload Complexity                                       │
│        │                                                    │
│   High │  ██████████████████  ← Photon: Strong YES         │
│        │  ████████████████                                  │
│ Medium │  ██████████████  ← Photon: Likely YES             │
│        │  ██████████                                        │
│   Low  │  ██████  ← Photon: Test first                     │
│        │  ██                                                │
│   None │  ← Photon: Probably not needed                    │
│        └────────────────────────────────────────────►       │
│                    Data Volume                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CMP-04: Right-Size Clusters Based on Workload (Required)

> **Official Recommendation:** "There's a balancing act between the number of workers and the size of worker instance types. Configuring compute with two workers, each with 16 cores and 128 GB of RAM, has the same compute and memory as configuring compute with 8 workers, each with 4 cores and 32 GB of RAM." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

### Sizing Factors

| Factor | Description |
|--------|-------------|
| **Total executor cores** | Maximum parallelism |
| **Total executor memory** | Data that fits in memory |
| **Local storage** | Shuffle and cache spills |
| **Network bandwidth** | Shuffle performance |

### Key Questions for Sizing

1. **How much data will your workload consume?**
2. **What's the computational complexity?**
3. **Where are you reading data from?**
4. **How is the data partitioned?**
5. **How much parallelism do you need?**

### Workload-Specific Configurations

#### Data Analysis

> **Official Recommendation:** "A single-node compute with a large VM type is likely the best choice, particularly for a single analyst. Analytical workloads will likely require reading the same data repeatedly, so recommended node types are storage optimized with disk cache enabled." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

```yaml
# Data Analysis configuration
job_clusters:
  - job_cluster_key: analysis_cluster
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      num_workers: 0  # Single node
      driver_node_type_id: "i3.2xlarge"  # Storage optimized
      spark_conf:
        spark.databricks.io.cache.enabled: "true"
      autotermination_minutes: 30
```

#### Basic Batch ETL

> **Official Recommendation:** "For simple batch ETL jobs that don't require wide transformations, such as joins or aggregations, use instances with lower requirements for memory and storage." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

```yaml
# Basic ETL configuration
job_clusters:
  - job_cluster_key: basic_etl
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      num_workers: 2
      node_type_id: "m5.large"  # General purpose, smaller
```

#### Complex Batch ETL

> **Official Recommendation:** "For a complex ETL job, such as one that requires unions and joins across multiple tables, Databricks recommends using fewer workers to reduce the amount of data shuffled. To compensate for having fewer workers, increase the size of your instances." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

```yaml
# Complex ETL configuration
job_clusters:
  - job_cluster_key: complex_etl
    new_cluster:
      spark_version: "14.3.x-photon-scala2.12"
      num_workers: 4  # Fewer, larger workers
      node_type_id: "i3.2xlarge"  # Larger instances
      runtime_engine: PHOTON
```

#### Machine Learning Training

> **Official Recommendation:** "To train machine learning models, Databricks recommends creating a compute resource using the Personal compute policy. You should use a single node compute with a large node type for initial experimentation." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

```yaml
# ML Training configuration
job_clusters:
  - job_cluster_key: ml_training
    new_cluster:
      spark_version: "14.3.x-ml-scala2.12"
      num_workers: 0  # Single node for experimentation
      driver_node_type_id: "i3.4xlarge"
      spark_conf:
        spark.databricks.io.cache.enabled: "true"
      autotermination_minutes: 60
```

### Configuration Summary by Workload

| Workload | Workers | Instance Size | Photon | Storage |
|----------|---------|---------------|--------|---------|
| **Data Analysis** | 0 (single) | Large | Optional | Storage-optimized |
| **Basic ETL** | 2-4 | Small/Medium | No | General purpose |
| **Complex ETL** | 2-4 | Large | Yes | Storage-optimized |
| **ML Training** | 0-2 | Large | No | Storage-optimized |
| **Streaming** | 4-8 (fixed) | Medium | Optional | Memory-optimized |

---

## Cluster Pools

> **Official Recommendation:** "Optionally, use pools to decrease compute launch times and reduce total runtime when running job pipelines." — [Databricks Docs](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)

### When to Use Pools

| Scenario | Pool Benefit |
|----------|--------------|
| **Frequent job runs** | ✅ Reduced cold start |
| **Similar configurations** | ✅ Resource reuse |
| **Pipeline sequences** | ✅ Faster transitions |
| **One-off jobs** | ❌ No benefit |
| **Diverse configurations** | ❌ Limited benefit |

### Pool Configuration

```yaml
# Pool definition
resources:
  instance_pools:
    etl_pool:
      instance_pool_name: "[${bundle.target}] ETL Pool"
      node_type_id: "i3.xlarge"
      min_idle_instances: 0
      max_capacity: 10
      idle_instance_autotermination_minutes: 15

# Use pool in job
job_clusters:
  - job_cluster_key: etl_cluster
    new_cluster:
      instance_pool_id: ${resources.instance_pools.etl_pool.id}
      num_workers: 4
```

---

## Auto-Scaling Guidelines

### When to Use Auto-Scaling

| Workload | Auto-Scaling | Reason |
|----------|--------------|--------|
| **Interactive notebooks** | ✅ Yes | Variable usage |
| **Batch ETL (variable)** | ✅ Yes | Load varies |
| **Batch ETL (fixed)** | ⚠️ Optional | Predictable load |
| **Streaming** | ❌ No | Scale-down issues |
| **ML Training** | ❌ No | Fixed resource needs |

### Auto-Scaling Configuration

```yaml
# Auto-scaling enabled
job_clusters:
  - job_cluster_key: variable_etl
    new_cluster:
      autoscale:
        min_workers: 2
        max_workers: 8
      spark_version: "14.3.x-scala2.12"

# Fixed size (streaming)
job_clusters:
  - job_cluster_key: streaming
    new_cluster:
      num_workers: 4  # No autoscale
      spark_version: "14.3.x-scala2.12"
```

---

## Validation Checklist

### Serverless Adoption
- [ ] Serverless used for SQL queries (BP-04)
- [ ] Serverless used for jobs when supported (BP-04)
- [ ] Serverless DLT pipelines when possible
- [ ] Classic compute only when serverless not available

### Access Modes
- [ ] Standard access mode for most workloads (CMP-01)
- [ ] Dedicated access mode only when required (GPU, RDD, R)
- [ ] Unity Catalog enabled on all clusters

### Compute Policies
- [ ] Compute policies defined and enforced (CMP-02)
- [ ] Instance types restricted to approved list
- [ ] Auto-termination configured
- [ ] Cost controls in place

### Sizing
- [ ] Workload-appropriate sizing (CMP-04)
- [ ] Photon enabled for complex transformations (CMP-03)
- [ ] Storage-optimized instances for repeated reads
- [ ] Fixed size for streaming (no auto-scaling)

---

## Quick Reference

```yaml
# Serverless job template
environments:
  - environment_key: default
    spec:
      environment_version: "4"
tasks:
  - task_key: process
    environment_key: default
    notebook_task:
      notebook_path: ../src/process.py

# Standard access mode cluster
new_cluster:
  spark_version: "14.3.x-scala2.12"
  data_security_mode: USER_ISOLATION
  num_workers: 4
  node_type_id: "i3.xlarge"

# Photon-enabled cluster
new_cluster:
  spark_version: "14.3.x-photon-scala2.12"
  runtime_engine: PHOTON
  num_workers: 4
  node_type_id: "i3.xlarge"

# Single-node for analysis/ML
new_cluster:
  num_workers: 0
  driver_node_type_id: "i3.2xlarge"
  spark_conf:
    spark.databricks.io.cache.enabled: "true"

# Streaming (fixed size, no autoscaling)
new_cluster:
  num_workers: 4  # Fixed!
  node_type_id: "m5.xlarge"
```

---

## References

- [Compute Configuration Recommendations](https://docs.databricks.com/en/compute/cluster-config-best-practices.html)
- [Serverless Compute](https://docs.databricks.com/en/compute/serverless/)
- [Access Modes](https://docs.databricks.com/en/compute/configure#access-mode)
- [Photon](https://docs.databricks.com/en/compute/photon.html)
- [Compute Policies](https://docs.databricks.com/en/admin/clusters/policies.html)
- [Instance Pools](https://docs.databricks.com/en/compute/pool-best-practices.html)
