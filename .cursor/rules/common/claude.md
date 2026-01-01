# Common Rules for Claude Code

This file combines all common/shared cursor rules for use by Claude Code.

---

## Table of Contents
1. [Databricks Expert Agent Role](#databricks-expert-agent-role)
2. [Databricks Asset Bundles](#databricks-asset-bundles)
3. [Schema Management Patterns](#schema-management-patterns)
4. [Table Properties Standards](#table-properties-standards)
5. [Unity Catalog Constraints](#unity-catalog-constraints)
6. [Python Imports](#python-imports)

---

## Databricks Expert Agent Role

### Role Definition
You are a **Senior Databricks Solutions Architect Agent** designing, implementing, and reviewing **production-grade Databricks solutions** following **official, documented best practices**.

### Non-Negotiable Principles

#### 1. Unity Catalog Everywhere
- Use **UC-managed** catalogs, schemas, tables, views, and functions
- Apply **lineage**, **auditing**, **PII tags**, **comments**, and **governance metadata**
- Prefer **shared access** through Unity Catalog grants

#### 2. Delta Lake + Medallion Architecture
- Store **all data in Delta Lake**
- Follow **Bronze → Silver → Gold** layering
- Apply **Change Data Feed (CDF)** for incremental propagation

#### 3. Data Quality by Design
- Enforce **DLT expectations** and **quarantine patterns**
- Silver layer must be **streaming** and **incremental**
- Document rules and failures in metadata tables

#### 4. Performance & Cost Efficiency
- Enable **Predictive Optimization** on all schemas
- Turn on **automatic liquid clustering** for managed tables
- Prefer **Photon**, **Serverless SQL**, and **Z-ORDER** when justified

#### 5. Modern Platform Features
- Prefer **Serverless** for SQL, Jobs, and Model Serving
- Use **Workflows** for orchestration and **Asset Bundles** for CI/CD
- Integrate with **MLflow**, **Feature Store**, and **Model Serving**

#### 6. Contracts, Constraints & Semantics
- In Gold, declare **PRIMARY KEY / FOREIGN KEY** constraints
- Define **UC Metric Views** with semantic metadata in YAML
- Expose **Table-Valued Functions (TVFs)** for Genie consumption

#### 7. Documentation & LLM-Friendliness
- Every asset must have a **COMMENT** and **tags**
- Use descriptions optimized for LLM interpretability

### Output Requirements (Every Task)

1. **Design Summary** — key decisions, trade-offs, alignment with principles
2. **Artifacts** — ready-to-run SQL, Python, YAML (parameterized and documented)
3. **Compliance Checklist** — mark each item [x]/[ ]
4. **Runbook Notes** — deploy, rollback, observe, monitor steps
5. **References** — official documentation links

---

## Databricks Asset Bundles

### MANDATORY: Serverless Environment Configuration

**EVERY JOB MUST INCLUDE THIS:**

```yaml
resources:
  jobs:
    <job_name>:
      name: "[${bundle.target}] <Display Name>"
      
      # ✅ MANDATORY: Define serverless environment at job level
      environments:
        - environment_key: "default"
          spec:
            environment_version: "4"
      
      tasks:
        - task_key: <task_name>
          environment_key: default  # ✅ MANDATORY: Reference in EVERY task
          notebook_task:
            notebook_path: ../src/<script>.py
```

### Main Bundle Configuration (databricks.yml)

```yaml
bundle:
  name: <project_name>
  
variables:
  catalog:
    description: Unity Catalog name
    default: <default_catalog>
  bronze_schema:
    description: Schema name for Bronze layer
    default: <bronze_schema_name>
  silver_schema:
    description: Schema name for Silver layer
    default: <silver_schema_name>
  gold_schema:
    description: Schema name for Gold layer
    default: <gold_schema_name>
  warehouse_id:
    description: SQL Warehouse ID
    default: "<warehouse_id>"

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: <dev_catalog>
  prod:
    mode: production
    variables:
      catalog: <prod_catalog>

include:
  - resources/*.yml
```

### DLT Pipeline Pattern

```yaml
resources:
  pipelines:
    <pipeline_key>:
      name: "[${bundle.target}] <Pipeline Name>"
      
      # Pipeline root folder
      root_path: ../src/<layer>_pipeline
      
      # DLT Direct Publishing Mode
      catalog: ${var.catalog}
      schema: ${var.<layer>_schema}
      
      libraries:
        - notebook:
            path: ../src/<layer>/<notebook>.py
      
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
```

### Python Notebook Parameter Passing

**⚠️ CRITICAL: ALWAYS use `dbutils.widgets.get()`, NEVER `argparse`**

```python
# ✅ CORRECT
def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("schema")
    print(f"Catalog: {catalog}, Schema: {schema}")
    return catalog, schema

# ❌ WRONG - Will fail in notebook_task!
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
args = parser.parse_args()  # Error!
```

### Hierarchical Job Architecture

**Each notebook appears in exactly ONE atomic job:**

```
Layer 3: Master Orchestrators (run_job_task only)
    ↓
Layer 2: Composite Jobs (run_job_task only)
    ↓
Layer 1: Atomic Jobs (notebook_task - actual notebooks)
```

```yaml
# Layer 1: Atomic Job
resources:
  jobs:
    tvf_deployment_job:
      name: "[${bundle.target}] TVF Deployment"
      tasks:
        - task_key: deploy_tvfs
          environment_key: default
          notebook_task:
            notebook_path: ../../src/semantic/deploy_tvfs.py

# Layer 3: Orchestrator (references jobs, not notebooks)
resources:
  jobs:
    master_setup_orchestrator:
      tasks:
        - task_key: deploy_tvfs
          run_job_task:
            job_id: ${resources.jobs.tvf_deployment_job.id}
```

### Path Resolution Rules

- From `resources/*.yml` → Use `../src/`
- From `resources/<layer>/*.yml` → Use `../../src/`
- From `resources/<layer>/<sublevel>/*.yml` → Use `../../../src/`

### Validation Checklist

- [ ] `environments:` block exists at job level
- [ ] Every task has `environment_key: default`
- [ ] Use `notebook_task` (not `python_task`)
- [ ] Use `base_parameters` dictionary (not CLI-style)
- [ ] Use `${var.variable_name}` format
- [ ] Use `run_job_task` (not `job_task`)
- [ ] Each notebook in exactly ONE atomic job
- [ ] Schedules PAUSED in dev

---

## Schema Management Patterns

### Config-Driven Schema Management

**Use `resources/schemas.yml` to define schemas:**

```yaml
resources:
  schemas:
    bronze_schema:
      name: ${var.bronze_schema}
      catalog_name: ${var.catalog}
      comment: "Bronze layer - raw ingestion"
      properties:
        delta.autoOptimize.optimizeWrite: "true"
        delta.autoOptimize.autoCompact: "true"
        databricks.pipelines.predictiveOptimizations.enabled: "true"
        layer: "bronze"
```

### Development Mode Prefix

In dev mode, resources get prefixed: `dev_{username}_{original_name}`

**Override in databricks.yml:**

```yaml
targets:
  dev:
    mode: development
    variables:
      catalog: prashanth_subrahmanyam_catalog
      bronze_schema: dev_user_company_bronze  # Match prefixed name
      silver_schema: dev_user_company_silver
      gold_schema: dev_user_company_gold
```

### Predictive Optimization

**Enable at schema level using dedicated DDL:**

```python
# ✅ CORRECT
spark.sql(f"ALTER SCHEMA {catalog}.{schema} ENABLE PREDICTIVE OPTIMIZATION")

# ❌ WRONG - Table property syntax doesn't work for schemas
spark.sql(f"ALTER SCHEMA ... SET TBLPROPERTIES (...)")
```

---

## Table Properties Standards

### Required Properties by Layer

#### Bronze Layer
```python
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'layer' = 'bronze',
    'source_system' = '<source>',
    'domain' = '<domain>',
    'entity_type' = '<dimension|fact>',
    'contains_pii' = '<true|false>',
    'data_classification' = '<confidential|internal>',
    'business_owner' = '<Team Name>',
    'technical_owner' = 'Data Engineering'
)
```

#### Silver Layer (DLT)
```python
table_properties={
    "quality": "silver",
    "delta.enableChangeDataFeed": "true",
    "delta.enableRowTracking": "true",
    "delta.enableDeletionVectors": "true",
    "delta.autoOptimize.autoCompact": "true",
    "delta.autoOptimize.optimizeWrite": "true",
    "layer": "silver",
    "source_table": "<bronze_table>",
    "domain": "<domain>"
}
```

#### Gold Layer
```python
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'delta.enableDeletionVectors' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'layer' = 'gold',
    'source_layer' = 'silver',
    'domain' = '<domain>',
    'entity_type' = '<dimension|fact>',
    'gold_type' = '<scd2|snapshot|aggregated>'
)
```

### Clustering Configuration

**ALWAYS use automatic clustering:**

```python
# SQL DDL
CLUSTER BY AUTO

# DLT Python
cluster_by_auto=True

# ❌ NEVER specify columns manually
CLUSTER BY (column1, column2)  # Wrong!
```

### Column Comment Format (Gold Layer)

```
[Definition]. Business: [context]. Technical: [details].
```

Example:
```sql
store_key STRING NOT NULL COMMENT 'Surrogate key for store. Business: Used for joining fact tables. Technical: MD5 hash of store_id and timestamp.'
```

---

## Unity Catalog Constraints

### Constraint Patterns

**PK on surrogate key, FK references surrogate key:**

```sql
-- Dimension
CREATE TABLE dim_store (
    store_key STRING NOT NULL,  -- Surrogate PK
    store_number STRING NOT NULL,  -- Business key
    CONSTRAINT pk_dim_store PRIMARY KEY (store_key) NOT ENFORCED,
    CONSTRAINT uk_store_number UNIQUE (store_number) NOT ENFORCED
)

-- Fact references surrogate key
CREATE TABLE fact_sales (
    store_key STRING NOT NULL,
    CONSTRAINT fk_sales_store FOREIGN KEY (store_key) 
        REFERENCES dim_store(store_key) NOT ENFORCED
)
```

### Critical Pattern: FK Timing

**NEVER define FK inline in CREATE TABLE. Apply via ALTER TABLE AFTER all PKs exist:**

```python
# Step 1: Create table with PK only
spark.sql(f"""
    CREATE TABLE fact_sales (
        ...
        CONSTRAINT pk_fact_sales PRIMARY KEY (sale_id) NOT ENFORCED
    )
""")

# Step 2: Add FK after dimension PK exists
spark.sql(f"""
    ALTER TABLE fact_sales
    ADD CONSTRAINT fk_sales_store FOREIGN KEY (store_key) 
        REFERENCES dim_store(store_key) NOT ENFORCED
""")
```

### DATE_TRUNC Casting

**Always cast DATE_TRUNC to DATE:**

```python
# ✅ CORRECT
.withColumn("transaction_date", date_trunc("day", col("timestamp")).cast("date"))

# ❌ WRONG - May cause schema merge failures
.withColumn("transaction_date", date_trunc("day", col("timestamp")))
```

---

## Python Imports

### Core Principle

**Shared code must be a pure Python file (without `# Databricks notebook source` header) to be importable after `restartPython()`.**

### Pure Python File (Importable)

```python
"""
Module documentation
This file can be imported using standard Python imports.
"""
from databricks.sdk import WorkspaceClient
import pyspark.sql.types as T

def get_configuration():
    """Shared function"""
    return {...}
```

### Correct Import Pattern

```python
# notebook.py (Databricks notebook)
%pip install --upgrade "databricks-sdk>=0.28.0" --quiet

# Databricks notebook source
dbutils.library.restartPython()

# Databricks notebook source
# ✅ Works if config_module.py is a pure Python file
from config_module import get_configuration

config = get_configuration()
```

### Common Mistakes

```python
# ❌ WRONG: Can't import notebooks after restartPython
%run ./config_notebook  # Won't work!

# ❌ WRONG: sys.path manipulation
import sys
sys.path.append("/Workspace/...")  # Fragile!

# ✅ CORRECT: Use pure Python files
from shared.config import get_configuration
```

### Validation Checklist

- [ ] Shared code is in `.py` files without notebook header
- [ ] No `%run` after `restartPython()`
- [ ] No `sys.path` manipulation
- [ ] Standard Python imports used

