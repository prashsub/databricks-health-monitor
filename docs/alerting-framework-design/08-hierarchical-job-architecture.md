# 08 - Hierarchical Job Architecture

## Overview

The alerting framework uses a **hierarchical job architecture** that separates concerns into atomic (single-purpose) jobs orchestrated by composite jobs. This pattern is a Databricks Asset Bundle best practice.

## Architecture Principle

> **Each notebook appears in exactly ONE atomic job.**
> **Composite jobs orchestrate atomic jobs using `run_job_task`, never `notebook_task`.**

## Two-Layer Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: COMPOSITE JOBS                                   │
│         Reference atomic jobs via run_job_task                              │
│         NO direct notebook references                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   alerting_setup_orchestrator_job (Orchestrator)                                  │
│   │                                                                         │
│   ├── Task: setup_alerting_tables                                          │
│   │   └── run_job_task: alerting_tables_job                          │
│   │                                                                         │
│   ├── Task: seed_all_alerts (depends_on: setup_alerting_tables)            │
│   │   └── run_job_task: alerting_seed_job                                │
│   │                                                                         │
│   ├── Task: validate_alert_queries (depends_on: seed_all_alerts)           │
│   │   └── run_job_task: alerting_validation_job                         │
│   │                                                                         │
│   ├── Task: sync_notification_destinations (depends_on: setup)             │
│   │   └── run_job_task: alerting_notifications_job                 │
│   │                                                                         │
│   └── Task: deploy_sql_alerts (depends_on: validate, sync_notif)           │
│       └── run_job_task: alerting_deploy_job                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 1: ATOMIC JOBS                                      │
│         Contains actual notebook_task references                            │
│         Single-purpose, testable independently                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   alerting_tables_job                                                │
│   └── notebook_task: setup_alerting_tables.py                              │
│       └── job_level: atomic                                                 │
│                                                                             │
│   alerting_seed_job                                                      │
│   └── notebook_task: seed_all_alerts.py                                    │
│       └── job_level: atomic                                                 │
│                                                                             │
│   alerting_validation_job                                               │
│   └── notebook_task: validate_alert_queries.py                             │
│       └── job_level: atomic                                                 │
│                                                                             │
│   alerting_notifications_job                                       │
│   └── notebook_task: sync_notification_destinations.py                     │
│       └── job_level: atomic                                                 │
│                                                                             │
│   alerting_deploy_job                                                 │
│   └── notebook_task: sync_sql_alerts.py                                    │
│       └── job_level: atomic                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Benefits

| Benefit | Description |
|---------|-------------|
| **Modularity** | Change one job without affecting others |
| **Debugging** | Isolate failures to specific atomic jobs |
| **Monitoring** | Track success/failure at granular level |
| **Flexibility** | Run any subset of the pipeline |
| **Testability** | Test atomic jobs independently |
| **Ownership** | Clear responsibility per job |

## YAML Configuration

### Atomic Job Example

```yaml
# resources/alerting/alerting_tables_job.yml

resources:
  jobs:
    alerting_tables_job:
      name: "[${bundle.target}] Health Monitor - Alerting Tables Setup"
      description: "Atomic job: Creates alerting configuration tables in Unity Catalog"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
      
      tasks:
        - task_key: setup_tables
          environment_key: default
          notebook_task:
            notebook_path: ../../src/alerting/setup_alerting_tables.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
      
      tags:
        job_level: atomic  # ✅ Mark as atomic
        layer: alerting
        purpose: setup
```

### Composite Job Example

```yaml
# resources/alerting/alerting_setup_orchestrator_job.yml

resources:
  jobs:
    alerting_setup_orchestrator_job:
      name: "[${bundle.target}] Health Monitor - Alerting Layer Setup"
      description: "Composite job: Orchestrates complete alerting setup via atomic jobs"
      
      tasks:
        # Step 1: Create tables
        - task_key: setup_alerting_tables
          run_job_task:  # ✅ Reference atomic job
            job_id: ${resources.jobs.alerting_tables_job.id}
        
        # Step 2: Seed alerts (depends on tables)
        - task_key: seed_all_alerts
          depends_on:
            - task_key: setup_alerting_tables
          run_job_task:
            job_id: ${resources.jobs.alerting_seed_job.id}
        
        # Step 3: Validate queries (depends on seeding)
        - task_key: validate_alert_queries
          depends_on:
            - task_key: seed_all_alerts
          run_job_task:
            job_id: ${resources.jobs.alerting_validation_job.id}
        
        # Step 4: Sync notification destinations (parallel with validation)
        - task_key: sync_notification_destinations
          depends_on:
            - task_key: setup_alerting_tables
          run_job_task:
            job_id: ${resources.jobs.alerting_notifications_job.id}
        
        # Step 5: Deploy alerts (depends on validation + destinations)
        - task_key: deploy_sql_alerts
          depends_on:
            - task_key: validate_alert_queries
            - task_key: sync_notification_destinations
          run_job_task:
            job_id: ${resources.jobs.alerting_deploy_job.id}
      
      tags:
        job_level: composite  # ✅ Mark as composite
        layer: alerting
        orchestrator: "true"
```

## Dependency Graph

```
                      ┌─────────────────────────┐
                      │  alerting_layer_setup   │
                      │  (Composite Orchestrator)│
                      └───────────┬─────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   │                   │
┌─────────────────────────┐       │                   │
│ setup_alerting_tables   │       │                   │
│ (Atomic)                │       │                   │
└───────────┬─────────────┘       │                   │
            │                     │                   │
    ┌───────┴────────┐            │                   │
    │                │            │                   │
    ▼                ▼            │                   │
┌─────────────┐ ┌────────────────┐│                   │
│seed_all_    │ │sync_notif_     ││                   │
│alerts       │ │destinations    ││                   │
│(Atomic)     │ │(Atomic)        ││                   │
└──────┬──────┘ └───────┬────────┘│                   │
       │                │         │                   │
       ▼                │         │                   │
┌─────────────────────┐ │         │                   │
│validate_alert_      │ │         │                   │
│queries (Atomic)     │ │         │                   │
└──────────┬──────────┘ │         │                   │
           │            │         │                   │
           └────────┬───┘         │                   │
                    │             │                   │
                    ▼             │                   │
           ┌────────────────────┐ │                   │
           │deploy_sql_alerts   │ │                   │
           │(Atomic)            │ │                   │
           └────────────────────┘ │                   │
```

## Wrong vs. Right Pattern

### ❌ WRONG: Notebook Duplication

```yaml
# File 1: alerting_tables_job.yml
tasks:
  - task_key: setup_tables
    notebook_task:
      notebook_path: ../../src/alerting/setup_alerting_tables.py  # ❌ Duplicated!

# File 2: alerting_setup_orchestrator_job.yml
tasks:
  - task_key: setup_alerting_tables
    notebook_task:
      notebook_path: ../../src/alerting/setup_alerting_tables.py  # ❌ Same notebook!
```

**Problems:**
- Changes require updating multiple files
- Inconsistent parameter passing
- No single source of truth
- Difficult to track failures

### ✅ CORRECT: Job Reference Pattern

```yaml
# File 1: alerting_tables_job.yml (ATOMIC)
tasks:
  - task_key: setup_tables
    notebook_task:
      notebook_path: ../../src/alerting/setup_alerting_tables.py  # ✅ Single source

# File 2: alerting_setup_orchestrator_job.yml (COMPOSITE)
tasks:
  - task_key: setup_alerting_tables
    run_job_task:
      job_id: ${resources.jobs.alerting_tables_job.id}  # ✅ Reference job
```

## File Organization

```
resources/
└── alerting/
    ├── alerting_setup_orchestrator_job.yml      # Layer 2: Composite orchestrator
    ├── alerting_tables_job.yml     # Layer 1: Atomic - table creation
    ├── alerting_seed_job.yml           # Layer 1: Atomic - alert seeding
    ├── alerting_validation_job.yml    # Layer 1: Atomic - query validation
    ├── alerting_notifications_job.yml  # Layer 1: Atomic - destinations
    └── alerting_deploy_job.yml      # Layer 1: Atomic - SDK deployment
```

## Standard Tags

All jobs should include a `job_level` tag:

```yaml
tags:
  job_level: atomic      # For single-notebook jobs
  # OR
  job_level: composite   # For orchestrator jobs
  
  layer: alerting        # Domain/layer
  purpose: setup         # What it does
```

## Running Jobs

### Run Complete Pipeline (Composite)

```bash
# Full alerting setup
databricks bundle run -t dev alerting_setup_orchestrator_job
```

### Run Individual Step (Atomic)

```bash
# Just create tables
databricks bundle run -t dev alerting_tables_job

# Just seed alerts
databricks bundle run -t dev alerting_seed_job

# Just validate queries
databricks bundle run -t dev alerting_validation_job

# Just deploy alerts
databricks bundle run -t dev alerting_deploy_job
```

### Testing Strategy

1. **Test atomics first** - Verify each piece works independently
2. **Then test composite** - Verify orchestration works
3. **Debug at atomic level** - If composite fails, identify which atomic failed

## Validation Checklist

- [ ] Each notebook appears in exactly ONE atomic job
- [ ] Composite jobs use `run_job_task` only (no `notebook_task`)
- [ ] All jobs have `job_level` tag (atomic or composite)
- [ ] Job references use `${resources.jobs.<job_name>.id}` format
- [ ] Dependencies use `depends_on` with `task_key`
- [ ] Atomic jobs have `environment_key` and `environments` block

## Next Steps

- **[09-Partial Success Patterns](09-partial-success-patterns.md)**: Error handling
- **[11-Implementation Guide](11-implementation-guide.md)**: Step-by-step setup
- **[12-Deployment and Operations](12-deployment-and-operations.md)**: Production deployment


