# Cluster Policies & Compute Governance

> **Document Owner:** Platform Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

Serverless is mandatory first choice. Cluster policies govern classic compute for the remaining use cases (GPU, 24/7 streaming). This document defines policy standards and compute type separation.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **PA-10** | All classic clusters must use approved policies | Critical |
| **PA-10a** | No unrestricted cluster creation | Critical |
| **PA-10b** | Instance types limited by policy | Required |
| **PA-10c** | Auto-termination required | Required |
| **PA-10d** | Serverless is 1st preference for all workloads | Critical |
| **PA-10e** | Jobs compute for scheduled, All-Purpose for exploration | Critical |
| **PA-10f** | Dependencies consistent between All-Purpose and Jobs | Required |

---

## Compute Type Selection

```
Workload Request
       │
       ▼
┌──────────────┐
│  Serverless  │ ◄── DEFAULT: Always evaluate first
│  Supported?  │
└──────┬───────┘
       │
  Yes ─┴── No (GPU, 24/7 Streaming)
   │       │
   ▼       ▼
┌──────┐  ┌──────────────────────────┐
│ Use  │  │ Scheduled? → Jobs Compute │
│Server│  │ Interactive? → All-Purpose│
│ less │  └──────────────────────────┘
└──────┘
```

---

## Jobs vs All-Purpose Compute

| Aspect | Jobs Compute | All-Purpose |
|--------|--------------|-------------|
| **Purpose** | Scheduled/automated | Interactive exploration |
| **Lifecycle** | Created per run | Long-running |
| **Use For** | ETL, ML training, reports | Debugging, prototyping |
| **Not For** | Interactive work | Production workloads |

---

## Dependency Consistency

Code developed in All-Purpose must work identically in Jobs. Both must use the same library versions.

### Policy-Based Libraries

```json
{
  "libraries": [
    { "pypi": { "package": "pandas==2.0.3" } },
    { "pypi": { "package": "pyarrow>=14.0.0" } },
    { "pypi": { "package": "scikit-learn==1.3.2" } },
    { "pypi": { "package": "mlflow>=2.17.0" } }
  ]
}
```

**Effect:** Users cannot install/uninstall libraries on compute using this policy.

---

## Standard Policies

### 1. Jobs - Data Engineering

```json
{
  "name": "Jobs - Data Engineering",
  "definition": {
    "spark_version": {
      "type": "allowlist",
      "values": ["14.3.x-scala2.12", "15.4.x-scala2.12"]
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["i3.xlarge", "i3.2xlarge"]
    },
    "num_workers": { "type": "range", "minValue": 1, "maxValue": 10 },
    "autotermination_minutes": { "type": "fixed", "value": 10 },
    "cluster_type": { "type": "fixed", "value": "job" },
    "custom_tags.team": { "type": "required" },
    "custom_tags.cost_center": { "type": "required" }
  },
  "libraries": [/* standard libraries */]
}
```

### 2. Jobs - ML Training GPU

```json
{
  "name": "Jobs - ML Training GPU",
  "definition": {
    "spark_version": {
      "type": "allowlist",
      "values": ["14.3.x-gpu-ml-scala2.12"]
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["g4dn.xlarge", "g4dn.2xlarge"]
    },
    "num_workers": { "type": "range", "minValue": 1, "maxValue": 4 },
    "autotermination_minutes": { "type": "fixed", "value": 30 }
  },
  "libraries": [/* standard + ML libraries */]
}
```

### 3. All-Purpose - Development

```json
{
  "name": "All-Purpose - Development",
  "definition": {
    "spark_version": {
      "type": "allowlist",
      "values": ["14.3.x-scala2.12", "15.4.x-scala2.12"]
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["i3.xlarge"]
    },
    "num_workers": { "type": "range", "minValue": 0, "maxValue": 2 },
    "autotermination_minutes": { "type": "fixed", "value": 15 },
    "cluster_type": { "type": "fixed", "value": "all-purpose" }
  },
  "libraries": [/* same as Jobs policy */],
  "max_clusters_per_user": 1
}
```

---

## Auto-Termination Settings

| Environment | Setting |
|-------------|---------|
| Development | 15 minutes |
| Staging | 30 minutes |
| Production (batch) | 60 minutes |
| Production (streaming) | Disabled (0) |

---

## Required Tags

```json
{
  "custom_tags.team": { "type": "required" },
  "custom_tags.cost_center": { "type": "required" },
  "custom_tags.environment": {
    "type": "allowlist",
    "values": ["dev", "staging", "prod"]
  }
}
```

---

## Policy Enforcement

When policies are updated, existing clusters may be out of compliance:

1. View compliance: **Compute** → **Policies** → **Compliance** column
2. Fix compliance: Click **Fix all** to update all resources
3. Monitor: Check `system.compute.clusters` for policy assignments

---

## Validation Checklist

### Serverless-First
- [ ] Serverless evaluated first for ALL workloads
- [ ] Classic compute only when serverless not supported
- [ ] Exception documented if using classic

### Compute Type Separation
- [ ] Jobs compute for scheduled workloads
- [ ] All-Purpose only for interactive exploration
- [ ] No production on All-Purpose

### Dependency Consistency
- [ ] Same library versions in Jobs and All-Purpose
- [ ] Libraries defined in policies
- [ ] Single source of truth (requirements.txt)

### Policy Design
- [ ] Instance types appropriate for workload
- [ ] Auto-termination configured
- [ ] Required tags defined
- [ ] max_clusters_per_user set for All-Purpose

---

## Related Documents

- [Serverless Compute](11-serverless-compute.md)
- [Platform Overview](10-platform-overview.md)

---

## References

- [Compute Policies](https://learn.microsoft.com/en-us/azure/databricks/admin/clusters/policies)
- [Add Libraries to Policy](https://learn.microsoft.com/en-us/azure/databricks/admin/clusters/policies#add-libraries-to-a-policy)
