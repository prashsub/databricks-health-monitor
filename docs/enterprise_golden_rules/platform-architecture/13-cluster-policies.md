# Cluster Policies & Compute Governance

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | PA-POL-001 |
| **Version** | 1.0 |
| **Last Updated** | January 2026 |
| **Owner** | Platform Engineering |
| **Status** | Approved |

---

## Executive Summary

Cluster policies enforce compute governance by restricting cluster configurations. While serverless is preferred for most workloads, cluster policies govern the remaining classic compute use cases.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| PA-10 | All classic clusters must use approved policies | 🔴 Critical |
| PA-10a | No unrestricted cluster creation | 🔴 Critical |
| PA-10b | Instance types limited by policy | 🟡 Required |
| PA-10c | Auto-termination required | 🟡 Required |

---

## When Cluster Policies Apply

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         COMPUTE GOVERNANCE FLOW                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   New Workload Request                                                              │
│          │                                                                          │
│          ▼                                                                          │
│   ┌──────────────┐                                                                 │
│   │  Serverless  │ ◄───── DEFAULT: Always try serverless first                    │
│   │  Supported?  │                                                                 │
│   └──────┬───────┘                                                                 │
│          │                                                                          │
│    Yes ──┴── No (GPU, Streaming, Legacy)                                           │
│     │         │                                                                     │
│     ▼         ▼                                                                     │
│   ┌──────┐  ┌──────────────────┐                                                   │
│   │ Use  │  │  Select Cluster  │                                                   │
│   │Server│  │  Policy          │                                                   │
│   │ less │  └────────┬─────────┘                                                   │
│   └──────┘           │                                                              │
│                      ▼                                                              │
│            ┌─────────────────────────────────────────┐                             │
│            │  APPROVED POLICIES                      │                             │
│            │  ├── data-engineering-standard          │                             │
│            │  ├── ml-training-gpu                    │                             │
│            │  ├── streaming-production               │                             │
│            │  └── development-small                  │                             │
│            └─────────────────────────────────────────┘                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Standard Cluster Policies

### 1. Data Engineering Standard

For ETL and data processing that cannot use serverless.

```json
{
  "name": "Data Engineering Standard",
  "definition": {
    "spark_version": {
      "type": "allowlist",
      "values": ["14.3.x-scala2.12", "15.0.x-scala2.12"]
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["i3.xlarge", "i3.2xlarge", "r5.xlarge", "r5.2xlarge"]
    },
    "num_workers": {
      "type": "range",
      "minValue": 1,
      "maxValue": 10
    },
    "autotermination_minutes": {
      "type": "range",
      "minValue": 10,
      "maxValue": 60,
      "defaultValue": 30
    },
    "custom_tags.team": {
      "type": "fixed",
      "value": "data-engineering"
    },
    "custom_tags.cost_center": {
      "type": "required"
    },
    "spark_conf.spark.databricks.cluster.profile": {
      "type": "fixed",
      "value": "serverCompatible"
    }
  }
}
```

### 2. ML Training (GPU)

For machine learning training with GPU instances.

```json
{
  "name": "ML Training GPU",
  "definition": {
    "spark_version": {
      "type": "allowlist",
      "values": ["14.3.x-gpu-ml-scala2.12", "15.0.x-gpu-ml-scala2.12"]
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["g4dn.xlarge", "g4dn.2xlarge", "p3.2xlarge"]
    },
    "driver_node_type_id": {
      "type": "allowlist",
      "values": ["i3.xlarge", "r5.xlarge"]
    },
    "num_workers": {
      "type": "range",
      "minValue": 1,
      "maxValue": 4
    },
    "autotermination_minutes": {
      "type": "range",
      "minValue": 30,
      "maxValue": 120,
      "defaultValue": 60
    },
    "custom_tags.workload_type": {
      "type": "fixed",
      "value": "ml-training"
    },
    "custom_tags.cost_center": {
      "type": "required"
    }
  }
}
```

### 3. Streaming Production

For long-running streaming workloads.

```json
{
  "name": "Streaming Production",
  "definition": {
    "spark_version": {
      "type": "allowlist",
      "values": ["14.3.x-scala2.12"]
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["r5.xlarge", "r5.2xlarge"]
    },
    "num_workers": {
      "type": "range",
      "minValue": 2,
      "maxValue": 8
    },
    "autotermination_minutes": {
      "type": "fixed",
      "value": 0,
      "hidden": true
    },
    "enable_elastic_disk": {
      "type": "fixed",
      "value": true
    },
    "custom_tags.workload_type": {
      "type": "fixed",
      "value": "streaming"
    },
    "custom_tags.environment": {
      "type": "fixed",
      "value": "production"
    }
  }
}
```

### 4. Development Small

For development and exploration.

```json
{
  "name": "Development Small",
  "definition": {
    "spark_version": {
      "type": "allowlist",
      "values": ["14.3.x-scala2.12", "15.0.x-scala2.12"]
    },
    "node_type_id": {
      "type": "fixed",
      "value": "i3.xlarge"
    },
    "num_workers": {
      "type": "range",
      "minValue": 0,
      "maxValue": 2
    },
    "autotermination_minutes": {
      "type": "fixed",
      "value": 15,
      "hidden": true
    },
    "custom_tags.workload_type": {
      "type": "fixed",
      "value": "development"
    }
  }
}
```

---

## Policy Attribute Reference

### Value Types

| Type | Description | Example |
|------|-------------|---------|
| `fixed` | Exact value, user cannot change | `"value": "i3.xlarge"` |
| `allowlist` | User picks from list | `"values": ["i3.xlarge", "i3.2xlarge"]` |
| `blocklist` | User cannot use these | `"values": ["p4d.24xlarge"]` |
| `range` | Numeric range | `"minValue": 1, "maxValue": 10` |
| `regex` | Pattern match | `"pattern": "^[a-z]+-.*"` |
| `unlimited` | No restriction | (default) |
| `required` | User must provide | Tag must be set |

### Common Attributes

```json
{
  // Spark version
  "spark_version": { "type": "allowlist", "values": [...] },
  
  // Instance types
  "node_type_id": { "type": "allowlist", "values": [...] },
  "driver_node_type_id": { "type": "allowlist", "values": [...] },
  
  // Cluster size
  "num_workers": { "type": "range", "minValue": 1, "maxValue": 10 },
  "autoscale.min_workers": { "type": "range", "minValue": 1, "maxValue": 5 },
  "autoscale.max_workers": { "type": "range", "minValue": 2, "maxValue": 10 },
  
  // Termination
  "autotermination_minutes": { "type": "range", "minValue": 10, "maxValue": 60 },
  
  // Features
  "enable_elastic_disk": { "type": "fixed", "value": true },
  "data_security_mode": { "type": "fixed", "value": "USER_ISOLATION" },
  
  // Tagging
  "custom_tags.team": { "type": "required" },
  "custom_tags.cost_center": { "type": "required" },
  
  // Spark configuration
  "spark_conf.spark.databricks.delta.preview.enabled": { "type": "fixed", "value": "true" }
}
```

---

## Rule PA-10a: No Unrestricted Clusters

### Block Unrestricted Creation

```json
// Workspace admin setting
{
  "enforce_cluster_policies": true,
  "allow_unrestricted_cluster_creation": false
}
```

### Grant Policy Access

```sql
-- Grant policy access to group
-- (via Admin Console or API)
-- Users can only create clusters using assigned policies
```

---

## Rule PA-10c: Auto-Termination

### Required Settings

| Environment | Auto-Termination | Rationale |
|-------------|------------------|-----------|
| Development | 15 minutes | Cost control |
| Staging | 30 minutes | Testing needs |
| Production (batch) | 60 minutes | Job completion buffer |
| Production (streaming) | Disabled (0) | 24/7 operation |

### Enforce in Policy

```json
{
  "autotermination_minutes": {
    "type": "range",
    "minValue": 10,
    "maxValue": 60,
    "defaultValue": 30
  }
}
```

---

## Cost Control Tags

### Required Tags

```json
{
  "custom_tags.team": {
    "type": "required"
  },
  "custom_tags.cost_center": {
    "type": "required"
  },
  "custom_tags.environment": {
    "type": "allowlist",
    "values": ["dev", "staging", "prod"]
  },
  "custom_tags.workload_type": {
    "type": "allowlist",
    "values": ["etl", "ml-training", "analytics", "streaming", "development"]
  }
}
```

### Cost Reporting Query

```sql
-- Cost by policy and tags
SELECT 
    cluster_name,
    custom_tags:team as team,
    custom_tags:cost_center as cost_center,
    SUM(list_cost) as total_cost
FROM system.billing.usage u
JOIN system.compute.clusters c 
    ON u.usage_metadata.cluster_id = c.cluster_id
WHERE usage_date >= CURRENT_DATE - 30
GROUP BY 1, 2, 3
ORDER BY total_cost DESC;
```

---

## Policy Management

### Create Policy (Admin Console or API)

```python
from databricks.sdk import WorkspaceClient
import json

w = WorkspaceClient()

policy_definition = {
    "spark_version": {
        "type": "allowlist",
        "values": ["14.3.x-scala2.12"]
    },
    # ... rest of policy
}

policy = w.cluster_policies.create(
    name="Data Engineering Standard",
    definition=json.dumps(policy_definition)
)

print(f"Created policy: {policy.policy_id}")
```

### Grant Policy to Group

```python
w.cluster_policies.set_permissions(
    cluster_policy_id=policy.policy_id,
    access_control_list=[
        {
            "group_name": "data_engineers",
            "permission_level": "CAN_USE"
        }
    ]
)
```

---

## Instance Pool Integration

### Pool for Cost Savings

```json
{
  "name": "Data Engineering with Pool",
  "definition": {
    "instance_pool_id": {
      "type": "fixed",
      "value": "pool-12345-abcde"
    },
    "driver_instance_pool_id": {
      "type": "fixed",
      "value": "pool-12345-abcde"
    }
  }
}
```

### Pool Benefits

- Faster cluster startup (pre-warmed instances)
- Cost savings from pooled resources
- Consistent instance types

---

## Validation Checklist

### Policy Design
- [ ] Instance types appropriate for workload
- [ ] Auto-termination configured
- [ ] Required tags defined
- [ ] Spark version limited to supported
- [ ] Cost center tagging required

### Policy Assignment
- [ ] Policy assigned to appropriate groups
- [ ] Unrestricted cluster creation disabled
- [ ] Default policy set for workspace

### Monitoring
- [ ] Cost reports include policy tags
- [ ] Alerts for unusual usage
- [ ] Regular policy review scheduled

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No matching policy" | User has no policy access | Grant policy to user's group |
| "Cluster creation denied" | Violates policy constraint | Use allowed values from policy |
| "Auto-termination required" | Policy enforces termination | Cannot disable for this policy |
| "Invalid instance type" | Not in allowlist | Select from allowed types |

---

## Related Documents

- [Serverless Compute](11-serverless-compute.md)
- [Unity Catalog Tables](12-unity-catalog-tables.md)
- [Cost Management](../solution-architecture/monitoring/41-lakehouse-monitoring.md)

---

## References

- [Cluster Policies](https://docs.databricks.com/clusters/policy.html)
- [Policy Definition](https://docs.databricks.com/clusters/policy-definition.html)
- [Instance Pools](https://docs.databricks.com/clusters/instance-pools/)
