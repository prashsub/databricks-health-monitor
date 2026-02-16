# Databricks Asset Bundle Standards

> **Document Owner:** Platform Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

Databricks Asset Bundles (DABs) are the standard for infrastructure-as-code deployment. This document defines mandatory patterns for job configuration, serverless environments, and hierarchical job architecture.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **IN-01** | Serverless compute for all jobs | Required |
| **IN-02** | Environment-level dependencies (not task) | Critical |
| **IN-03** | Use `notebook_task` (never `python_task`) | Critical |
| **IN-04** | Use `dbutils.widgets.get()` for parameters | Critical |
| **IN-05** | Hierarchical job architecture | Required |
| **IN-06** | Notebooks in exactly ONE atomic job | Critical |
| **IN-07** | Use `run_job_task` for job references | Critical |
| **IN-08** | Include `[${bundle.target}]` prefix | Required |

---

## Serverless Job Template

Every job must include this serverless configuration:

```yaml
resources:
  jobs:
    my_job:
      name: "[${bundle.target}] My Job Name"
      
      environments:
        - environment_key: "default"
          spec:
            environment_version: "4"
            dependencies:
              - "pandas==2.0.3"
      
      tasks:
        - task_key: task_name
          environment_key: default
          notebook_task:
            notebook_path: ../src/my_script.py
            base_parameters:
              catalog: ${var.catalog}
```

### Common Mistakes

```yaml
# ❌ WRONG: Task-level libraries
tasks:
  - task_key: my_task
    libraries:
      - pypi: { package: pandas }

# ❌ WRONG: python_task doesn't exist
tasks:
  - task_key: my_task
    python_task:
      python_file: ../src/script.py
```

---

## Parameter Passing

### In YAML

```yaml
notebook_task:
  notebook_path: ../src/script.py
  base_parameters:
    catalog: ${var.catalog}
    schema: ${var.gold_schema}
```

### In Python

```python
# ✅ CORRECT
def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("schema")
    return catalog, schema

# ❌ WRONG: argparse fails in notebook_task
parser = argparse.ArgumentParser()
args = parser.parse_args()  # ERROR!
```

---

## Hierarchical Job Architecture

Each notebook appears in exactly ONE atomic job. Higher levels reference jobs, not notebooks.

### Layer 1: Atomic Jobs (Notebook References)

```yaml
resources:
  jobs:
    tvf_deployment_job:
      name: "[${bundle.target}] TVF Deployment"
      
      tasks:
        - task_key: deploy
          notebook_task:
            notebook_path: ../../src/deploy_tvfs.py
      
      tags:
        job_level: atomic
```

### Layer 2: Composite Jobs (Job References)

```yaml
resources:
  jobs:
    semantic_layer_setup:
      name: "[${bundle.target}] Semantic Layer Setup"
      
      tasks:
        - task_key: deploy_tvfs
          run_job_task:
            job_id: ${resources.jobs.tvf_deployment_job.id}
        
        - task_key: deploy_metrics
          depends_on:
            - task_key: deploy_tvfs
          run_job_task:
            job_id: ${resources.jobs.metric_view_job.id}
      
      tags:
        job_level: composite
```

### Layer 3: Orchestrators (References Composites)

```yaml
resources:
  jobs:
    master_setup:
      name: "[${bundle.target}] Master Setup"
      
      tasks:
        - task_key: gold_setup
          run_job_task:
            job_id: ${resources.jobs.gold_setup_job.id}
        
        - task_key: semantic_setup
          depends_on:
            - task_key: gold_setup
          run_job_task:
            job_id: ${resources.jobs.semantic_layer_setup.id}
      
      tags:
        job_level: orchestrator
```

---

## DLT Pipeline Configuration

```yaml
resources:
  pipelines:
    silver_pipeline:
      name: "[${bundle.target}] Silver Pipeline"
      
      root_path: ../src/silver_pipeline
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      
      serverless: true
      photon: true
      channel: CURRENT
      edition: ADVANCED
      
      libraries:
        - notebook:
            path: ../src/silver_pipeline/transforms.py
```

### Triggering from Workflows

```yaml
# ✅ Native pipeline_task
tasks:
  - task_key: run_pipeline
    pipeline_task:
      pipeline_id: ${resources.pipelines.silver_pipeline.id}
      full_refresh: false
```

---

## Path Resolution

| YAML Location | Path to `src/` |
|---------------|----------------|
| `resources/*.yml` | `../src/` |
| `resources/<layer>/*.yml` | `../../src/` |

---

## Variable References

```yaml
# ✅ CORRECT
base_parameters:
  catalog: ${var.catalog}

# ❌ WRONG: Missing var. prefix
base_parameters:
  catalog: ${catalog}
```

---

## Directory Structure

```
resources/
├── orchestrators/           # Layer 3
│   └── master_setup.yml
├── semantic/                # Domain
│   ├── semantic_setup.yml   # Layer 2
│   └── tvf_job.yml          # Layer 1
├── monitoring/              # Domain
│   └── lakehouse_job.yml    # Layer 1
└── pipelines/
    └── silver_pipeline.yml
```

---

## Validation Checklist

- [ ] `environments:` block at job level
- [ ] `environment_key: default` on every task
- [ ] `[${bundle.target}]` prefix in job name
- [ ] `notebook_task` (never `python_task`)
- [ ] `base_parameters` dictionary format
- [ ] `${var.name}` for variables
- [ ] Each notebook in ONE atomic job only
- [ ] Orchestrators use `run_job_task` only

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `arguments are required` | argparse | Use `dbutils.widgets.get()` |
| `Invalid task type` | python_task | Use `notebook_task` |
| `Variable not found` | Missing prefix | Use `${var.name}` |

---

## CI/CD Best Practices

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Version control everything** | All code, configs, infra in Git |
| **Automate testing** | Unit, integration, data quality tests |
| **Use IaC** | Asset Bundles for all resources |
| **Environment isolation** | Separate dev/staging/prod |
| **Unified asset management** | DABs for code + infra together |

### Branching Strategy

```
main (production)
  │
  └── staging
        │
        └── feature/XXX-description
```

| Branch | Deploys To | Triggered By |
|--------|------------|--------------|
| `main` | Production | Merge from staging |
| `staging` | Staging | Merge from feature |
| `feature/*` | Development | Push |

### CI Workflow Template

```yaml
# .github/workflows/ci.yml
name: Databricks CI

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main, staging]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Databricks CLI
        run: pip install databricks-cli
      
      - name: Validate Bundle
        run: databricks bundle validate
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}

  deploy-dev:
    if: github.ref == 'refs/heads/staging'
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Dev
        run: databricks bundle deploy -t dev
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    needs: validate
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: databricks bundle deploy -t prod
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

### ML CI/CD (MLOps Stacks)

For ML projects, use the MLOps Stacks pattern:

```
├── feature_engineering/     # Feature pipelines
├── training/               # Model training
├── validation/             # Model validation
├── deployment/             # Model deployment
└── monitoring/             # Model monitoring
```

### Best Practices

| Practice | Implementation |
|----------|----------------|
| **Workload identity federation** | Use OIDC, not static tokens |
| **Environment promotion** | dev → staging → prod |
| **Automated testing** | pytest for transforms, DLT for quality |
| **Rollback procedures** | Document and test regularly |
| **Secrets management** | GitHub Secrets, never in code |

---

## Related Documents

- [Python Development](21-python-development.md)
- [Serverless Compute](11-serverless-compute.md)
- [Reliability & DR](18-reliability-disaster-recovery.md)

---

## References

- [Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Bundle Resources](https://docs.databricks.com/dev-tools/bundles/resources)
- [CI/CD Best Practices](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/ci-cd/best-practices)
- [MLOps Stacks](https://docs.databricks.com/mlops/mlops-stacks.html)
