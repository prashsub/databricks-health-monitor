# Reliability & Disaster Recovery

> **Document Owner:** Platform Team | **Status:** Approved | **Last Updated:** February 2026

## Overview

This document defines reliability, high availability, and disaster recovery patterns for the Databricks platform. These patterns ensure business continuity during failures, outages, and regional disruptions.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **REL-01** | Enable Delta Lake time travel (≥7 days retention) | Critical |
| **REL-02** | Configure job retry with exponential backoff | Required |
| **REL-03** | Use structured streaming with checkpointing | Critical |
| **REL-04** | Enable cluster autoscaling for variable workloads | Required |
| **REL-05** | Configure auto-termination on all clusters | Required |
| **REL-06** | Use cluster pools for faster recovery | Recommended |
| **REL-07** | Implement workspace backup procedures | Critical |
| **REL-08** | Test disaster recovery procedures quarterly | Required |

---

## REL-01: Delta Lake Time Travel

### Rule
All Delta tables must retain at least 7 days of history for point-in-time recovery.

### Why It Matters
- Enables recovery from accidental deletes or updates
- Provides audit trail for compliance
- Supports debugging production issues
- No external backup system required

### Implementation
```sql
-- Check current retention
DESCRIBE HISTORY catalog.schema.my_table;

-- Set retention (default is 30 days)
ALTER TABLE catalog.schema.my_table
SET TBLPROPERTIES ('delta.logRetentionDuration' = '7 days');

-- Restore to previous version
RESTORE TABLE catalog.schema.my_table TO VERSION AS OF 42;

-- Restore to timestamp
RESTORE TABLE catalog.schema.my_table TO TIMESTAMP AS OF '2025-02-01 00:00:00';
```

---

## REL-02: Job Retry Configuration

### Rule
Configure intelligent retry policies with exponential backoff for all production jobs.

### Why It Matters
- Automatic recovery from transient failures
- Prevents overwhelming downstream services
- Distinguishes recoverable vs. permanent failures
- Reduces manual intervention

### Implementation
```yaml
resources:
  jobs:
    production_etl:
      name: "[${bundle.target}] Production ETL"
      
      # Timeout at job level
      timeout_seconds: 7200  # 2 hours
      
      tasks:
        - task_key: process_data
          # Task-level retry configuration
          retry_on_timeout: true
          max_retries: 3
          min_retry_interval_millis: 60000  # 1 minute initial wait
          
          notebook_task:
            notebook_path: ../src/process.py
```

### Retry Decision Guide

| Error Type | Retry? | Max Attempts |
|------------|--------|--------------|
| Network timeout | Yes | 3 |
| Resource unavailable | Yes | 3 |
| Authentication failure | No | 0 |
| Data validation error | No | 0 |
| Out of memory | Maybe | 1 (with larger cluster) |

---

## REL-03: Streaming Checkpointing

### Rule
All structured streaming jobs must use checkpointing with highly available storage (ZRS or cross-region).

### Why It Matters
- Enables exactly-once processing guarantees
- Allows automatic recovery from cluster failures
- Preserves processing state across restarts
- Supports seamless upgrades

### Implementation
```python
# Correct: ZRS storage for checkpoints
checkpoint_path = "abfss://container@storage.dfs.core.windows.net/checkpoints/my_stream"

streaming_query = (
    spark.readStream
    .format("delta")
    .table("bronze.events")
    .writeStream
    .format("delta")
    .option("checkpointLocation", checkpoint_path)
    .trigger(availableNow=True)  # Or processingTime="10 seconds"
    .toTable("silver.events")
)

# Wait for completion (batch mode)
streaming_query.awaitTermination()
```

### Checkpoint Storage Requirements

| Feature | Requirement |
|---------|-------------|
| Storage type | Zone-redundant (ZRS) or geo-redundant (GRS) |
| Latency | Low latency for frequent writes |
| Durability | 11 nines (99.999999999%) |
| Location | Same region as cluster |

---

## REL-04: Cluster Autoscaling

### Rule
Enable autoscaling for all variable workloads. Use fixed sizing only for streaming with predictable load.

### Why It Matters
- Handles demand fluctuations automatically
- Prevents under-provisioning during peak
- Optimizes cost during low demand
- No manual scaling intervention needed

### Implementation
```yaml
# For Serverless Jobs (automatic)
environments:
  - environment_key: default
    spec:
      environment_version: "4"  # Auto-scales automatically

# For Classic Clusters (when required)
new_cluster:
  autoscale:
    min_workers: 2
    max_workers: 10
  autotermination_minutes: 30
```

### Autoscaling Guidelines

| Workload | Autoscaling | Min Workers | Max Workers |
|----------|-------------|-------------|-------------|
| Interactive notebooks | Yes | 1 | 4 |
| Variable batch ETL | Yes | 2 | 10 |
| Streaming (variable) | Limited | 2 | 8 |
| Streaming (steady) | No (fixed) | 4 | 4 |
| ML Training | No (fixed) | 2 | 2 |

---

## REL-05: Auto-Termination

### Rule
Configure auto-termination on all clusters to prevent idle resource costs and ensure cluster refresh.

### Why It Matters
- Reduces costs from idle clusters
- Forces regular cluster refresh (security patches)
- Prevents zombie clusters
- Maintains cluster hygiene

### Settings by Environment

| Environment | Auto-Terminate |
|-------------|----------------|
| Development | 15 minutes |
| Staging | 30 minutes |
| Production (batch) | 60 minutes |
| Production (streaming) | Disabled (0) |

---

## REL-06: Cluster Pools

### Rule
Use cluster pools for frequently used configurations to reduce startup time and improve availability.

### Why It Matters
- Reduces startup from 5-10 minutes to <60 seconds
- Ensures instance availability during capacity constraints
- No DBU charges for idle pool instances
- Provides consistent cluster provisioning

### Implementation
```yaml
resources:
  cluster_pools:
    data_engineering_pool:
      pool_name: "[${bundle.target}] Data Engineering Pool"
      node_type_id: "i3.xlarge"
      min_idle_instances: 2
      max_capacity: 20
      idle_instance_autotermination_minutes: 60
      preloaded_spark_versions:
        - "14.3.x-scala2.12"
```

---

## REL-07: Workspace Backup

### Rule
Implement automated backup procedures for all workspace assets with cross-region replication.

### Why It Matters
- Enables rapid recovery from workspace corruption
- Preserves development work and configurations
- Supports disaster recovery requirements
- Maintains audit trail

### Backup Scope

| Asset | Backup Method | Frequency |
|-------|---------------|-----------|
| Notebooks | Git repos | Continuous |
| Job definitions | Asset Bundles | On deploy |
| Cluster configs | Asset Bundles | On deploy |
| Secrets | External vault | Daily |
| Unity Catalog metadata | System tables | Automatic |

### Implementation
```bash
# Export workspace artifacts using Databricks CLI
databricks workspace export_dir /Workspace/Shared ./backup/workspace/

# Export jobs
databricks jobs list --output JSON > ./backup/jobs.json

# For Asset Bundles - all configs are in Git
git push origin main  # Continuous backup
```

---

## Failure Mitigation Patterns

### Cluster Driver Node Failure

| Mitigation | Implementation |
|------------|----------------|
| Auto-restart policies | Enable on cluster config |
| Checkpointing | All streaming jobs |
| Fault-tolerant state | Structured streaming |
| Idempotent operations | MERGE with deduplication |

### Job Execution Failures

| Mitigation | Implementation |
|------------|----------------|
| Retry with backoff | Task-level retry config |
| Timeout settings | Job and task level |
| Error handling | try/except with logging |
| Alerting | Email notifications |

### Data Corruption

| Mitigation | Implementation |
|------------|----------------|
| ACID transactions | Delta Lake (automatic) |
| Time travel | 7+ day retention |
| DLT expectations | Quality enforcement |
| Validation checks | Pre-merge validation |

### Workspace Unavailability

| Mitigation | Implementation |
|------------|----------------|
| Multi-region deployment | For mission-critical |
| Git-based code | All code in repos |
| Asset Bundles | Declarative configs |
| Cross-region data replication | Delta Sharing or copy |

---

## Disaster Recovery Procedures

### RTO/RPO Targets

| Tier | RTO | RPO | Use Case |
|------|-----|-----|----------|
| Tier 1 | <1 hour | <15 min | Critical pipelines |
| Tier 2 | <4 hours | <1 hour | Standard ETL |
| Tier 3 | <24 hours | <4 hours | Development |

### DR Runbook

1. **Detection**
   - Monitor workspace health via Azure Monitor
   - Automated alerts on job failures
   - Unity Catalog accessibility checks

2. **Assessment**
   - Determine scope of impact
   - Identify affected workloads
   - Check data integrity

3. **Recovery**
   - Restore workspace from backup (if needed)
   - Redeploy Asset Bundles
   - Restart streaming jobs from checkpoints
   - Validate data consistency

4. **Validation**
   - Run data quality checks
   - Verify job executions
   - Confirm downstream dependencies

---

## Validation Checklist

### Data Protection
- [ ] Delta Lake time travel ≥7 days retention
- [ ] Streaming checkpoints on ZRS/GRS storage
- [ ] DLT expectations for data quality
- [ ] MERGE operations are idempotent

### Compute Resilience
- [ ] Autoscaling enabled for variable workloads
- [ ] Auto-termination configured
- [ ] Cluster pools for frequently used configs
- [ ] Job retry policies configured

### Operational Readiness
- [ ] Workspace backup procedures documented
- [ ] DR runbook tested quarterly
- [ ] Monitoring and alerting configured
- [ ] Recovery contacts documented

---

## Related Documents

- [Platform Overview](10-platform-overview.md)
- [Serverless Compute](11-serverless-compute.md)
- [Delta Lake Best Practices](17-delta-lake-best-practices.md)

---

## References

- [Reliability Best Practices](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/reliability/best-practices)
- [Architecture Best Practices for Azure Databricks](https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-databricks)
- [Structured Streaming Checkpointing](https://docs.databricks.com/structured-streaming/production.html)
- [Delta Lake Time Travel](https://docs.databricks.com/delta/history.html)
