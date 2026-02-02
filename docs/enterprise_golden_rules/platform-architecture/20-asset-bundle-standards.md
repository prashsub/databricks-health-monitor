# Databricks Asset Bundle Standards

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | IN-01 through IN-08 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Platform Engineering Team |
| **Status** | Approved |

---

## Executive Summary

Databricks Asset Bundles (DABs) are our standard for infrastructure-as-code deployment. This document defines mandatory patterns for job configuration, serverless environments, parameter passing, and hierarchical job architecture.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| IN-01 | Serverless compute for all jobs | 🟡 Required |
| IN-02 | Environment-level dependencies (not task-level) | 🔴 Critical |
| IN-03 | Use `notebook_task` (never `python_task`) | 🔴 Critical |
| IN-04 | Use `dbutils.widgets.get()` for parameters | 🔴 Critical |
| IN-05 | Hierarchical job architecture (atomic → composite → orchestrator) | 🟡 Required |
| IN-06 | Notebooks appear in exactly ONE atomic job | 🔴 Critical |
| IN-07 | Use `run_job_task` for job references | 🔴 Critical |
| IN-08 | Include `[${bundle.target}]` prefix in job names | 🟡 Required |

---

## Rule IN-01: Serverless Environment Configuration

**EVERY job MUST include serverless environment configuration.**

### Standard Template

```yaml
resources:
  jobs:
    my_job:
      name: "[${bundle.target}] My Job Name"
      
      # ✅ MANDATORY: Serverless environment at job level
      environments:
        - environment_key: "default"
          spec:
            environment_version: "4"
            dependencies:
              - "Faker==22.0.0"      # Pin versions
              - "pandas==2.0.3"
      
      tasks:
        - task_key: task_name
          environment_key: default  # ✅ MANDATORY: Reference in EVERY task
          notebook_task:
            notebook_path: ../src/my_script.py
            base_parameters:
              catalog: ${var.catalog}
              schema: ${var.gold_schema}
```

### Why This Matters

- Enables serverless compute for cost optimization
- Ensures consistent Python environment across tasks
- Required for library dependency management
- Prevents deployment and runtime failures

### Rule IN-02: Environment-Level Dependencies

**Dependencies MUST be at environment level, NOT task level.**

```yaml
# ❌ WRONG: Task-level libraries (fails on serverless)
tasks:
  - task_key: my_task
    libraries:
      - pypi:
          package: Faker==22.0.0

# ✅ CORRECT: Environment-level dependencies
environments:
  - environment_key: "default"
    spec:
      environment_version: "4"
      dependencies:
        - "Faker==22.0.0"
```

---

## Rule IN-03 & IN-04: Notebook Tasks and Parameters

### Use `notebook_task`, Never `python_task`

```yaml
# ❌ WRONG: python_task doesn't exist in DABs
tasks:
  - task_key: my_task
    python_task:
      python_file: ../src/script.py
      parameters:
        - "--catalog=my_catalog"

# ✅ CORRECT: notebook_task with base_parameters
tasks:
  - task_key: my_task
    notebook_task:
      notebook_path: ../src/script.py
      base_parameters:
        catalog: ${var.catalog}
        schema: ${var.gold_schema}
```

### Parameter Passing in Python

**ALWAYS use `dbutils.widgets.get()` for parameters. NEVER use `argparse`.**

```python
# ❌ WRONG: argparse fails in notebook_task
import argparse

def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()  # ERROR: arguments are required
    return args.catalog

# ✅ CORRECT: dbutils.widgets.get()
def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("schema")
    
    print(f"Parameters: catalog={catalog}, schema={schema}")
    return catalog, schema
```

### Parameter Method Decision Table

| Execution Context | YAML Config | Python Method |
|-------------------|-------------|---------------|
| `notebook_task` in DABs | `base_parameters: {}` | `dbutils.widgets.get()` |
| Interactive notebook | Widgets in UI | `dbutils.widgets.get()` |
| Local Python script | Command line | `argparse` |

---

## Rule IN-05, IN-06, IN-07: Hierarchical Job Architecture

### Core Principle: No Notebook Duplication

**Each notebook appears in EXACTLY ONE atomic job.** Higher-level jobs reference lower-level jobs via `run_job_task`.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: MASTER ORCHESTRATORS                                                │
│ References Layer 2 via run_job_task                                          │
│ NO direct notebook references                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ master_setup_orchestrator                    master_refresh_orchestrator     │
│        │                                              │                      │
│    ┌───┴───┬────────────┐                    ┌───────┴────────┐             │
│    ▼       ▼            ▼                    ▼                ▼             │
│ semantic  monitoring   ml_layer          monitoring     ml_inference        │
│ _setup    _setup       _setup            _refresh                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: COMPOSITE JOBS                                                      │
│ References Layer 1 via run_job_task                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ semantic_layer_setup_job                    monitoring_layer_setup_job       │
│        │                                              │                      │
│    ┌───┴────┐                                        │                      │
│    ▼        ▼                                        ▼                      │
│ tvf_job  metric_view_job                    lakehouse_monitoring_job        │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: ATOMIC JOBS                                                         │
│ Contains actual notebook_task references                                     │
│ Single-purpose, testable independently                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ tvf_deployment_job        metric_view_deployment_job                         │
│ lakehouse_monitoring_job  ml_training_pipeline                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Layer 1: Atomic Jobs (Notebook References)

```yaml
# resources/semantic/tvf_deployment_job.yml
resources:
  jobs:
    tvf_deployment_job:
      name: "[${bundle.target}] TVF Deployment"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
      
      tasks:
        - task_key: deploy_all_tvfs
          environment_key: default
          notebook_task:  # ✅ Actual notebook reference
            notebook_path: ../../src/semantic/deploy_tvfs.py
            base_parameters:
              catalog: ${var.catalog}
      
      tags:
        job_level: atomic  # ✅ Mark as atomic
        layer: semantic
```

### Layer 2: Composite Jobs (Job References)

```yaml
# resources/semantic/semantic_layer_setup_job.yml
resources:
  jobs:
    semantic_layer_setup_job:
      name: "[${bundle.target}] Semantic Layer Setup"
      
      tasks:
        # ✅ Reference atomic job, NOT notebook
        - task_key: deploy_tvfs
          run_job_task:
            job_id: ${resources.jobs.tvf_deployment_job.id}
        
        # ✅ Reference another atomic job with dependency
        - task_key: deploy_metric_views
          depends_on:
            - task_key: deploy_tvfs
          run_job_task:
            job_id: ${resources.jobs.metric_view_deployment_job.id}
      
      tags:
        job_level: composite  # ✅ Mark as composite
```

### Layer 3: Master Orchestrators

```yaml
# resources/orchestrators/master_setup_orchestrator.yml
resources:
  jobs:
    master_setup_orchestrator:
      name: "[${bundle.target}] Master Setup Orchestrator"
      
      tasks:
        - task_key: bronze_setup
          run_job_task:
            job_id: ${resources.jobs.bronze_setup_job.id}
        
        - task_key: gold_setup
          depends_on:
            - task_key: bronze_setup
          run_job_task:
            job_id: ${resources.jobs.gold_setup_job.id}
        
        - task_key: semantic_layer_setup
          depends_on:
            - task_key: gold_setup
          run_job_task:
            job_id: ${resources.jobs.semantic_layer_setup_job.id}
      
      tags:
        job_level: orchestrator  # ✅ Mark as orchestrator
```

### ❌ WRONG: Notebook Duplication

```yaml
# ❌ WRONG: Same notebook in multiple jobs!

# File 1: resources/semantic/tvf_job.yml
tasks:
  - task_key: deploy_tvfs
    notebook_task:
      notebook_path: ../../src/deploy_tvfs.py  # ❌ Duplicated!

# File 2: resources/orchestrators/setup.yml
tasks:
  - task_key: deploy_tvfs
    notebook_task:
      notebook_path: ../../src/deploy_tvfs.py  # ❌ Same notebook!
```

---

## Directory Structure Pattern

```
resources/
├── orchestrators/              # Layer 3
│   ├── master_setup_orchestrator.yml
│   └── master_refresh_orchestrator.yml
│
├── semantic/                   # Domain: Semantic
│   ├── semantic_layer_setup_job.yml    # Layer 2
│   ├── tvf_deployment_job.yml          # Layer 1
│   └── metric_view_deployment_job.yml  # Layer 1
│
├── monitoring/                 # Domain: Monitoring
│   ├── monitoring_layer_setup_job.yml  # Layer 2
│   └── lakehouse_monitoring_job.yml    # Layer 1
│
├── ml/                         # Domain: ML
│   ├── ml_layer_setup_job.yml          # Layer 2
│   ├── ml_training_pipeline.yml        # Layer 1
│   └── ml_inference_pipeline.yml       # Layer 1
│
└── pipelines/                  # Domain: Data
    ├── bronze/
    │   └── bronze_setup_job.yml        # Layer 1
    └── gold/
        └── gold_setup_job.yml          # Layer 1
```

---

## DLT Pipeline Configuration

### Standard DLT Pipeline Pattern

```yaml
resources:
  pipelines:
    silver_dlt_pipeline:
      name: "[${bundle.target}] Silver DLT Pipeline"
      
      # Pipeline root folder (required)
      root_path: ../src/silver_pipeline
      
      # Direct Publishing Mode (modern pattern)
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      
      libraries:
        - notebook:
            path: ../src/silver_pipeline/silver_dimensions.py
        - notebook:
            path: ../src/silver_pipeline/silver_facts.py
      
      configuration:
        catalog: ${var.catalog}
        bronze_schema: ${var.bronze_schema}
        silver_schema: ${var.silver_schema}
      
      serverless: true
      photon: true
      channel: CURRENT
      continuous: false
      development: true
      edition: ADVANCED
      
      tags:
        layer: silver
        pipeline_type: dlt
```

### Triggering DLT from Workflows

```yaml
# ✅ CORRECT: Native pipeline_task
tasks:
  - task_key: run_silver_pipeline
    depends_on:
      - task_key: bronze_complete
    pipeline_task:
      pipeline_id: ${resources.pipelines.silver_dlt_pipeline.id}
      full_refresh: false

# ❌ WRONG: Python wrapper
tasks:
  - task_key: run_pipeline
    python_task:
      python_file: ../src/trigger_pipeline.py
```

---

## Path Resolution Rules

**Relative paths depend on YAML file location:**

| YAML Location | Path to `src/` |
|---------------|----------------|
| `resources/*.yml` | `../src/` |
| `resources/<layer>/*.yml` | `../../src/` |
| `resources/<layer>/<sublayer>/*.yml` | `../../../src/` |

```yaml
# From resources/gold/gold_setup_job.yml
notebook_task:
  notebook_path: ../../src/gold/setup_tables.py  # Two levels up

# From resources/bronze_job.yml
notebook_task:
  notebook_path: ../src/bronze/setup_tables.py   # One level up
```

---

## Variable Reference Pattern

**ALWAYS use `${var.name}` format:**

```yaml
# ✅ CORRECT
base_parameters:
  catalog: ${var.catalog}
  schema: ${var.gold_schema}

# ❌ WRONG: Missing var. prefix
base_parameters:
  catalog: ${catalog}
  schema: ${gold_schema}
```

---

## Pre-Deployment Validation

### Validation Script

```bash
#!/bin/bash
# scripts/validate_bundle.sh

echo "🔍 Pre-Deployment Validation"

# 1. Check for duplicate YAML files
duplicates=$(find resources -name "*.yml" | awk -F/ '{print $NF}' | sort | uniq -d)
if [ -n "$duplicates" ]; then
    echo "❌ Duplicate files: $duplicates"
    exit 1
fi

# 2. Check for python_task (invalid)
if grep -r "python_task:" resources/; then
    echo "❌ Found python_task (use notebook_task)"
    exit 1
fi

# 3. Check for missing var. prefix
if grep -r '\${catalog}' resources/ | grep -v '\${var.catalog}'; then
    echo "❌ Found \${catalog} without var. prefix"
    exit 1
fi

# 4. Validate bundle syntax
databricks bundle validate || exit 1

echo "✅ All checks passed!"
```

### Run Before Every Deployment

```bash
./scripts/validate_bundle.sh && databricks bundle deploy -t dev
```

---

## Validation Checklist

### Job Configuration
- [ ] `environments:` block at job level
- [ ] `environment_key: default` on every task
- [ ] Dependencies at environment level (not task libraries)
- [ ] `[${bundle.target}]` prefix in job name
- [ ] `job_level` tag (atomic, composite, or orchestrator)

### Hierarchical Architecture
- [ ] Each notebook in exactly ONE atomic job
- [ ] Composite jobs use `run_job_task` only
- [ ] Orchestrators use `run_job_task` only
- [ ] Job references use `${resources.jobs.<name>.id}`

### Task Configuration
- [ ] `notebook_task` (never `python_task`)
- [ ] `base_parameters` dictionary format
- [ ] Python uses `dbutils.widgets.get()` (not argparse)
- [ ] `${var.name}` for variable references

### Paths
- [ ] Relative paths correct for YAML location
- [ ] DLT libraries within `root_path`
- [ ] Include paths in `databricks.yml` cover all subdirectories

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `error: arguments are required` | Using argparse | Use `dbutils.widgets.get()` |
| `Invalid task type` | `python_task` usage | Use `notebook_task` |
| `Variable not found` | Missing `var.` prefix | Use `${var.name}` |
| `Path does not exist` | Wrong relative path | Check YAML location depth |
| `Duplicate resource` | Same file in multiple locations | Remove duplicates |

---

## Related Documents

- [Python Development Standards](21-python-development-standards.md)
- [Schema Management Standards](22-schema-management-standards.md)
- [Deployment Checklist](../part6-templates/deployment-checklist.md)

---

## References

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Bundle Resources Reference](https://docs.databricks.com/dev-tools/bundles/resources)
- [Serverless Job Example](https://github.com/databricks/bundle-examples/blob/main/knowledge_base/serverless_job/resources/serverless_job.yml)
