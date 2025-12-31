# Genie Spaces Deployment Guide
# Databricks Health Monitor - Agent Framework Natural Language Interface

**Version:** 2.0  
**Last Updated:** December 30, 2025  
**Status:** Production-Ready  
**Related:** Phase 4 - Agent Framework

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Agent Framework Integration](#agent-framework-integration)
3. [Prerequisites](#prerequisites)
4. [Deployment Architecture](#deployment-architecture)
5. [Pre-Deployment Validation](#pre-deployment-validation)
6. [Genie Space Configurations](#genie-space-configurations)
7. [Deployment Steps](#deployment-steps)
8. [Testing & Validation](#testing--validation)
9. [Post-Deployment](#post-deployment)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

---

## Overview

### What This Guide Covers

This guide provides complete deployment instructions for **Genie Spaces** that serve as the **natural language query interface** for the **Phase 4 Agent Framework**.

### Role in Agent Framework

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: AGENT FRAMEWORK                              │
│          (LangChain/LangGraph + Databricks Foundation Models)            │
│                                                                          │
│  6 Specialized Agents + Orchestrator Agent                              │
│  - Cost Agent                                                           │
│  - Security Agent                                                       │
│  - Performance Agent                                                    │
│  - Reliability Agent                                                    │
│  - Data Quality & Governance Agent                                      │
│  - ML Ops Agent                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Uses as Natural Language Interface
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3.6: GENIE SPACES                               │
│            (Natural Language Query Execution Layer)                      │
│                                                                          │
│  7 Genie Spaces = Natural Language Interface for Agents                 │
│  - Cost Intelligence Genie → Cost Agent's Query Interface               │
│  - Job Health Monitor Genie → Reliability Agent's Query Interface       │
│  - Performance Analyzer Genie → Performance Agent's Query Interface     │
│  - Security Auditor Genie → Security Agent's Query Interface            │
│  - Data Quality Genie → DQ Agent's Query Interface                      │
│  - ML Intelligence Genie → MLOps Agent's Query Interface                │
│  - Unified Health Monitor Genie → Orchestrator Agent's Query Interface  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Queries via Natural Language
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: DATA ASSETS (Tools)                          │
│                                                                          │
│  - 60 Table-Valued Functions (Parameterized Queries)                    │
│  - 10 Metric Views (Pre-Aggregated Analytics)                           │
│  - 25 ML Models (Predictions & Anomalies)                               │
│  - 8 Lakehouse Monitors (Drift Detection)                               │
│  - 38 Gold Tables (Reference Data)                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Concept:** Genie Spaces provide the **natural language query execution layer** that agents use to interact with data assets. Each specialized agent has a corresponding Genie Space that understands domain-specific terminology and routes to appropriate tools.

### Genie Spaces → Agent Mapping

| Genie Space | Phase 4 Agent | Agent Purpose | Assets (Agent Tools) | Status |
|-------------|---------------|---------------|----------------------|--------|
| **Cost Intelligence** | 💰 Cost Agent | Analyze costs, forecast spending, optimize resources | 15 TVFs, 2 Metric Views, 6 ML Models, 1 Monitor | ✅ Ready |
| **Job Health Monitor** | 🔄 Reliability Agent | Ensure platform reliability, manage incidents, track SLAs | 12 TVFs, 1 Metric View, 5 ML Models, 1 Monitor | ✅ Ready |
| **Performance Analyzer** | ⚡ Performance Agent | Monitor job/query/cluster performance, optimize bottlenecks | 16 TVFs, 3 Metric Views, 7 ML Models, 2 Monitors | ✅ Ready |
| **Security Auditor** | 🔒 Security Agent | Monitor security posture, detect threats, ensure compliance | 10 TVFs, 2 Metric Views, 4 ML Models, 1 Monitor | ✅ Ready |
| **Data Quality Monitor** | ✅ Data Quality Agent | Ensure data quality, maintain lineage, enforce governance | 7 TVFs, 2 Metric Views, 3 ML Models, 2 Monitors | ✅ Ready |
| **ML Intelligence** | 🤖 ML Ops Agent | Monitor ML experiments, models, and serving endpoints | Integrated in other spaces | ✅ Ready |
| **Databricks Health Monitor** | 🌐 Orchestrator Agent | Route queries to specialized agents, coordinate workflows | All 60 TVFs, 10 Metric Views, 25 ML Models, 8 Monitors | ✅ Ready |

**Note:** Performance Analyzer consolidates Query Performance + Cluster Optimizer from Phase 3 to align with the single Performance Agent in Phase 4.

### Total Asset Inventory

| Asset Type | Total Count | Phase | Status |
|------------|-------------|-------|--------|
| **Gold Tables** | 38 | Phase 2 | ✅ Deployed |
| **TVFs** | 60 | Phase 3.2 | ✅ Deployed |
| **Metric Views** | 10 | Phase 3.3 | ✅ Deployed |
| **Lakehouse Monitors** | 8 | Phase 3.4 | ✅ Deployed |
| **ML Models** | 25 | Phase 3.1 | ✅ Deployed |
| **Genie Spaces** | 7 | Phase 3.6 | 🔄 Ready to Deploy |
| **AI Agents** | 7 | Phase 4 | 📋 Planned |

---

## Agent Framework Integration

### How Genie Spaces Enable the Agent Framework

Genie Spaces serve as the **natural language query execution engine** for Phase 4 AI agents. Each agent uses its corresponding Genie Space to translate natural language queries into executable SQL and function calls.

#### Agent → Genie Space → Tool Flow

```
User Query: "Why did costs spike last Tuesday?"
                    ↓
        [ORCHESTRATOR AGENT]
                    ↓ (Intent Classification: Cost)
            [COST AGENT]
                    ↓ (Uses Cost Intelligence Genie Space)
    [COST INTELLIGENCE GENIE SPACE]
                    ↓ (Translates to SQL + TVF calls)
        ┌───────────┴───────────┐
        ▼                       ▼
[cost_analytics MV]    [get_cost_trend_by_sku TVF]
        │                       │
        └───────────┬───────────┘
                    ▼
        [cost_anomaly_predictions ML]
                    ▼
            Results → Cost Agent
                    ↓
        Natural Language Response
```

### Agent Tools = Genie Space Data Assets

Each agent's "tools" (in LangChain terminology) are the data assets registered in its Genie Space:

| Agent | Genie Space | Tool Types Available |
|-------|-------------|----------------------|
| **Cost Agent** | Cost Intelligence | • 15 TVFs (e.g., `get_top_cost_contributors`)<br>• 2 Metric Views (`cost_analytics`, `commit_tracking`)<br>• 6 ML Models (anomaly, forecaster, tag recommender) |
| **Security Agent** | Security Auditor | • 10 TVFs (e.g., `get_user_activity_summary`)<br>• 2 Metric Views (`security_events`, `governance_analytics`)<br>• 4 ML Models (access anomaly, user risk scorer) |
| **Performance Agent** | Performance Analyzer | • 16 TVFs (e.g., `get_slow_queries`, `get_cluster_utilization`)<br>• 3 Metric Views (query, cluster metrics)<br>• 7 ML Models (query optimizer, cache predictor) |
| **Reliability Agent** | Job Health Monitor | • 12 TVFs (e.g., `get_failed_jobs`, `get_job_sla_compliance`)<br>• 1 Metric View (`job_performance`)<br>• 5 ML Models (failure predictor, retry success) |
| **Data Quality Agent** | Data Quality Monitor | • 7 TVFs (e.g., `get_table_freshness`, `get_pipeline_data_lineage`)<br>• 2 Metric Views (`data_quality`, `ml_intelligence`)<br>• 3 ML Models (quality anomaly, trend predictor) |
| **ML Ops Agent** | ML Intelligence | • Integrated ML monitoring across all spaces<br>• Access to `fact_mlflow_runs`, `fact_endpoint_usage` |
| **Orchestrator Agent** | Unified Health Monitor | • All 60 TVFs + 10 Metric Views + 25 ML Models<br>• Routes to specialized Genie Spaces based on intent |

### Example: Cost Agent Using Genie Space

**User asks Cost Agent:** "What are the top 5 cost drivers this month?"

**Cost Agent workflow:**
1. **Intent Classification:** Cost analysis query
2. **Tool Selection:** Use `get_top_cost_contributors` TVF
3. **Query Construction:** Agent sends natural language to Cost Intelligence Genie Space
4. **Genie Translation:** "What are the top 5 cost drivers this month?" → 
   ```sql
   SELECT * FROM get_top_cost_contributors(
     DATE_TRUNC('month', CURRENT_DATE),
     CURRENT_DATE,
     5
   );
   ```
5. **Execution:** Genie executes SQL
6. **Results:** Returns structured data to Cost Agent
7. **Agent Response:** Cost Agent formats results with context and recommendations

### Multi-Agent Workflows via Unified Genie Space

**Complex query:** "Why did costs spike AND were there any job failures last Tuesday?"

**Orchestrator Agent workflow:**
1. **Intent Classification:** Multi-domain (Cost + Reliability)
2. **Agent Routing:** Fork to Cost Agent + Reliability Agent
3. **Parallel Execution:**
   - Cost Agent → Cost Intelligence Genie → Cost spike analysis
   - Reliability Agent → Job Health Monitor Genie → Failure analysis
4. **Correlation:** Orchestrator checks if failures caused cost spike
5. **Synthesis:** Unified response combining both analyses

### Benefits of Genie Spaces for Agents

| Benefit | Description | Impact |
|---------|-------------|--------|
| **Natural Language Understanding** | Agents don't need to write SQL - Genie translates | Faster agent development |
| **Semantic Layer** | Genie understands domain terminology and synonyms | Better query accuracy |
| **Tool Abstraction** | Agents call Genie, not raw SQL/APIs | Simpler agent logic |
| **Performance Optimization** | Genie uses metric views (pre-aggregated) first | <10 sec responses |
| **Error Handling** | Genie handles malformed queries gracefully | Robust agents |
| **Context Retention** | Genie maintains conversation context | Multi-turn conversations |

### Deployment Order

```
Phase 2: Gold Tables (38)
         ↓
Phase 3.1: ML Models (25)
         ↓
Phase 3.2: TVFs (60)
         ↓
Phase 3.3: Metric Views (10)
         ↓
Phase 3.4: Lakehouse Monitors (8)
         ↓
Phase 3.6: Genie Spaces (7)  ← YOU ARE HERE
         ↓
Phase 4: AI Agents (7)  ← Next Step
```

---

## Prerequisites

### ✅ Completed Deployments

Before deploying Genie Spaces, verify all dependencies are deployed:

- [ ] **Gold Layer Tables** (38 tables across 12 domains)
  - Location: `src/pipelines/gold/`
  - Validation: `SELECT COUNT(*) FROM system.information_schema.tables WHERE table_catalog = '{catalog}' AND table_schema = '{gold_schema}'`
  - Expected: 38 tables

- [ ] **Table-Valued Functions** (60 TVFs across 5 domains)
  - Location: `src/semantic/tvfs/`
  - Validation: `SELECT COUNT(*) FROM system.information_schema.routines WHERE routine_catalog = '{catalog}' AND routine_schema = '{gold_schema}' AND routine_type = 'FUNCTION'`
  - Expected: 60 functions

- [ ] **Metric Views** (10 metric views across 5 domains)
  - Location: `src/semantic/metric_views/`
  - Validation: `DESCRIBE EXTENDED {catalog}.{gold_schema}.cost_analytics` (check Type: METRIC_VIEW)
  - Expected: 10 metric views

- [ ] **ML Models** (25 models with prediction tables)
  - Location: `src/ml/`
  - Validation: `SELECT COUNT(*) FROM system.information_schema.tables WHERE table_name LIKE '%_predictions'`
  - Expected: 25 prediction tables

- [ ] **Lakehouse Monitors** (8 monitors with profile/drift tables)
  - Location: `src/monitoring/`
  - Validation: `SELECT COUNT(*) FROM system.information_schema.tables WHERE table_name LIKE '%_profile_metrics'`
  - Expected: 16 monitoring tables (8 profile + 8 drift)

### ✅ System Requirements

- [ ] **Databricks Runtime:** 14.3 LTS or higher
- [ ] **Databricks SQL Warehouse:** Serverless or Pro tier
- [ ] **Unity Catalog:** Enabled with catalog/schema created
- [ ] **Permissions:**
  - `USE CATALOG` on target catalog
  - `USE SCHEMA` on gold schema
  - `CREATE GENIE SPACE` permission
  - `SELECT` on all Gold tables, TVFs, and metric views
  - Workspace Admin or Account Admin (for Space creation)

### ✅ Access Requirements

- [ ] **Workspace URL:** `https://<workspace>.cloud.databricks.com`
- [ ] **Catalog Name:** Documented in `databricks.yml`
- [ ] **Gold Schema Name:** Documented in `databricks.yml`
- [ ] **SQL Warehouse ID:** For Genie Space compute

---

## Deployment Architecture

### Phase 4 Agent Framework + Genie Spaces Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 4: AGENT LAYER                                 │
│                    (LangChain/LangGraph Agents)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │              ORCHESTRATOR AGENT                               │          │
│  │  • Intent classification                                      │          │
│  │  • Multi-agent coordination                                   │          │
│  │  • Uses: Unified Health Monitor Genie                        │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                               │                                              │
│         ┌─────────────────────┼──────────────────────┐                     │
│         ▼                     ▼                      ▼                     │
│  ┌─────────────┐      ┌─────────────┐       ┌─────────────┐              │
│  │ Cost Agent  │      │Security Agent│       │Performance  │              │
│  │             │      │              │       │   Agent     │              │
│  │Uses: Cost   │      │Uses: Security│       │Uses: Perf   │              │
│  │Intelligence │      │Auditor Genie │       │Analyzer     │              │
│  │Genie        │      │              │       │Genie        │              │
│  └─────────────┘      └─────────────┘       └─────────────┘              │
│         ▼                     ▼                      ▼                     │
│  ┌─────────────┐      ┌─────────────┐       ┌─────────────┐              │
│  │Reliability  │      │Data Quality │       │  ML Ops     │              │
│  │Agent        │      │Agent        │       │  Agent      │              │
│  │             │      │             │       │             │              │
│  │Uses: Job    │      │Uses: DQ     │       │Uses: ML     │              │
│  │Health       │      │Monitor      │       │Intelligence │              │
│  │Monitor Genie│      │Genie        │       │Genie        │              │
│  └─────────────┘      └─────────────┘       └─────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Natural Language Queries
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3.6: GENIE SPACES LAYER                             │
│                 (Natural Language Query Execution)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │          UNIFIED HEALTH MONITOR GENIE (Orchestrator)         │          │
│  │  All 60 TVFs + 10 Metric Views + 25 ML Models               │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                               │                                              │
│         ┌─────────────────────┼──────────────────────┐                     │
│         ▼                     ▼                      ▼                     │
│  ┌─────────────┐      ┌─────────────┐       ┌─────────────┐              │
│  │Cost Intel   │      │Security     │       │Performance  │              │
│  │Genie        │      │Auditor      │       │Analyzer     │              │
│  │15 TVFs      │      │Genie        │       │Genie        │              │
│  │2 MVs        │      │10 TVFs      │       │16 TVFs      │              │
│  │6 ML Models  │      │2 MVs        │       │3 MVs        │              │
│  └─────────────┘      └─────────────┘       └─────────────┘              │
│         ▼                     ▼                      ▼                     │
│  ┌─────────────┐      ┌─────────────┐       ┌─────────────┐              │
│  │Job Health   │      │Data Quality │       │ML Intel     │              │
│  │Monitor      │      │Monitor      │       │Genie        │              │
│  │Genie        │      │Genie        │       │(Integrated) │              │
│  │12 TVFs      │      │7 TVFs       │       │             │              │
│  │1 MV         │      │2 MVs        │       │             │              │
│  └─────────────┘      └─────────────┘       └─────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ SQL + Function Calls
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: DATA ASSETS (Agent Tools)                        │
│              60 TVFs + 10 Metric Views + 25 ML Models + 8 Monitors          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Asset Hierarchy in Each Space

```
1. METRIC VIEWS (Primary - Genie uses first)
   ├── Pre-aggregated for fast queries
   ├── Rich semantic metadata
   └── 30+ measures per view

2. TABLE-VALUED FUNCTIONS (Specific patterns)
   ├── Parameterized queries
   ├── Business logic encapsulation
   └── Complex filtering

3. ML PREDICTION TABLES (ML-powered insights)
   ├── Anomaly detection
   ├── Forecasting
   └── Risk scoring

4. LAKEHOUSE MONITORING TABLES (Drift detection)
   ├── Profile metrics
   └── Drift metrics

5. GOLD TABLES (Reference only, use sparingly)
   └── Direct table access when above insufficient
```

---

## Pre-Deployment Validation

### Step 1: Validate All Data Assets Exist

Run this validation script to check all dependencies:

```python
# Databricks notebook source
# File: scripts/validate_genie_prerequisites.py

from pyspark.sql import SparkSession

def validate_genie_prerequisites(spark: SparkSession, catalog: str, schema: str):
    """Validate all Genie Space prerequisites."""
    
    results = []
    
    # 1. Check Gold Tables
    tables = spark.sql(f"""
        SELECT COUNT(*) as count 
        FROM system.information_schema.tables 
        WHERE table_catalog = '{catalog}' 
        AND table_schema = '{schema}'
        AND table_type = 'MANAGED'
    """).collect()[0]['count']
    
    results.append(('Gold Tables', tables, 38, tables >= 38))
    
    # 2. Check TVFs
    tvfs = spark.sql(f"""
        SELECT COUNT(*) as count 
        FROM system.information_schema.routines 
        WHERE routine_catalog = '{catalog}' 
        AND routine_schema = '{schema}'
        AND routine_type = 'FUNCTION'
    """).collect()[0]['count']
    
    results.append(('TVFs', tvfs, 60, tvfs >= 60))
    
    # 3. Check Metric Views
    metric_views = spark.sql(f"""
        SELECT COUNT(*) as count 
        FROM system.information_schema.tables 
        WHERE table_catalog = '{catalog}' 
        AND table_schema = '{schema}'
        AND table_type = 'VIEW'
        AND table_name IN (
            'cost_analytics', 'commit_tracking', 'job_performance',
            'query_performance', 'cluster_utilization', 'cluster_efficiency',
            'security_events', 'governance_analytics', 'data_quality', 'ml_intelligence'
        )
    """).collect()[0]['count']
    
    results.append(('Metric Views', metric_views, 10, metric_views >= 10))
    
    # 4. Check ML Prediction Tables
    ml_predictions = spark.sql(f"""
        SELECT COUNT(*) as count 
        FROM system.information_schema.tables 
        WHERE table_catalog = '{catalog}' 
        AND table_schema = '{schema}'
        AND table_name LIKE '%_predictions'
    """).collect()[0]['count']
    
    results.append(('ML Prediction Tables', ml_predictions, 25, ml_predictions >= 25))
    
    # 5. Check Monitoring Tables
    monitoring_tables = spark.sql(f"""
        SELECT COUNT(*) as count 
        FROM system.information_schema.tables 
        WHERE table_catalog = '{catalog}' 
        AND table_schema = '{schema}'
        AND (table_name LIKE '%_profile_metrics' OR table_name LIKE '%_drift_metrics')
    """).collect()[0]['count']
    
    results.append(('Monitoring Tables', monitoring_tables, 16, monitoring_tables >= 16))
    
    # Print results
    print("\n" + "="*80)
    print("GENIE SPACE PREREQUISITES VALIDATION")
    print("="*80)
    print(f"{'Asset Type':<30} {'Actual':<10} {'Expected':<10} {'Status'}")
    print("-"*80)
    
    all_passed = True
    for asset_type, actual, expected, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{asset_type:<30} {actual:<10} {expected:<10} {status}")
        if not passed:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("✅ ALL PREREQUISITES MET - Ready to deploy Genie Spaces")
    else:
        print("❌ MISSING PREREQUISITES - Deploy missing assets first")
        raise RuntimeError("Genie Space prerequisites not met")
    
    return all_passed

# Execute
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("gold_schema")

spark = SparkSession.builder.appName("Validate Genie Prerequisites").getOrCreate()
validate_genie_prerequisites(spark, catalog, schema)
```

### Step 2: Validate SQL Warehouse

```sql
-- Check warehouse exists and is running
SHOW WAREHOUSES;

-- Test query performance
SELECT COUNT(*) FROM ${catalog}.${gold_schema}.fact_usage;
```

### Step 3: Test Sample Queries

Test key queries from each domain:

```sql
-- Cost Analytics
SELECT MEASURE(total_cost) FROM ${catalog}.${gold_schema}.cost_analytics;

-- Job Performance  
SELECT * FROM ${catalog}.${gold_schema}.get_failed_jobs(CURRENT_DATE - 7, CURRENT_DATE) LIMIT 10;

-- Query Performance
SELECT MEASURE(p95_duration_seconds) FROM ${catalog}.${gold_schema}.query_performance;

-- Security
SELECT * FROM ${catalog}.${gold_schema}.get_user_activity_summary('john@company.com', CURRENT_DATE - 30, CURRENT_DATE);

-- Data Quality
SELECT * FROM ${catalog}.${gold_schema}.get_table_freshness(24);
```

---

## Genie Space Configurations

### Genie Spaces as Agent Query Interfaces

Each Genie Space serves as the **natural language query interface** for its corresponding Phase 4 agent.

```
src/genie/
├── cost_intelligence_genie.md          # Cost Agent Query Interface
├── job_health_monitor_genie.md         # Reliability Agent Query Interface
├── performance_genie.md                # Performance Agent Query Interface
├── security_auditor_genie.md           # Security Agent Query Interface
├── data_quality_monitor_genie.md       # Data Quality Agent Query Interface
├── ml_intelligence_genie.md            # ML Ops Agent Query Interface (TBD)
└── unified_health_monitor_genie.md     # Orchestrator Agent Query Interface
```

### Agent → Genie Space → Tools Mapping

| Phase 4 Agent | Genie Space | Agent Responsibilities | Tools Available (via Genie) |
|---------------|-------------|------------------------|------------------------------|
| **💰 Cost Agent** | Cost Intelligence | • Analyze costs & spending<br>• Forecast DBU usage<br>• Budget variance detection<br>• Cost optimization recommendations | • 15 TVFs (e.g., `get_top_cost_contributors`)<br>• 2 Metric Views<br>• 6 ML Models (anomaly, forecaster)<br>• 1 Monitor |
| **🔒 Security Agent** | Security Auditor | • Monitor audit logs<br>• Detect threats<br>• Track access patterns<br>• Compliance reporting | • 10 TVFs (e.g., `get_user_activity_summary`)<br>• 2 Metric Views<br>• 4 ML Models (access anomaly, risk scorer)<br>• 1 Monitor |
| **⚡ Performance Agent** | Performance Analyzer | • Monitor job/query/cluster performance<br>• Identify bottlenecks<br>• Optimize resource utilization<br>• Performance trending | • 16 TVFs (e.g., `get_slow_queries`)<br>• 3 Metric Views<br>• 7 ML Models (optimizer, predictor)<br>• 2 Monitors |
| **🔄 Reliability Agent** | Job Health Monitor | • Track SLAs<br>• Incident detection<br>• Failure pattern analysis<br>• Recovery time tracking | • 12 TVFs (e.g., `get_failed_jobs`)<br>• 1 Metric View<br>• 5 ML Models (failure predictor)<br>• 1 Monitor |
| **✅ Data Quality Agent** | Data Quality Monitor | • Data quality monitoring<br>• Lineage tracking<br>• Governance compliance<br>• Freshness monitoring | • 7 TVFs (e.g., `get_table_freshness`)<br>• 2 Metric Views<br>• 3 ML Models (quality anomaly)<br>• 2 Monitors |
| **🤖 ML Ops Agent** | ML Intelligence | • Experiment tracking<br>• Model performance monitoring<br>• Serving endpoint health<br>• Model drift detection | • Integrated across spaces<br>• Access to MLflow tables<br>• Endpoint usage data |
| **🌐 Orchestrator Agent** | Unified Health Monitor | • Intent classification<br>• Multi-agent coordination<br>• Cross-domain queries<br>• Response synthesis | • All 60 TVFs<br>• All 10 Metric Views<br>• All 25 ML Models<br>• All 8 Monitors |

### Mandatory 7-Section Structure

**Each Genie Space configuration document contains:**

| Section | Content | Purpose for Agents | Status |
|---------|---------|-------------------|--------|
| **A. Space Name** | Exact Genie Space name | Agent identifies its query interface | ✅ |
| **B. Space Description** | 2-3 sentence purpose | Agent understands domain scope | ✅ |
| **C. Sample Questions** | 10-15 user-facing questions | Agent learns query patterns | ✅ |
| **D. Data Assets** | All tables & metric views | Agent discovers available tools | ✅ |
| **E. General Instructions** | ≤20 lines LLM rules | Agent behavior configuration | ✅ |
| **F. TVFs** | All functions with signatures | Agent function call specs | ✅ |
| **G. Benchmark Questions** | 10-15 with EXACT SQL | Agent validation & testing | ✅ |

---

## Deployment Steps

### Deployment Script

```python
# Databricks notebook source
# File: src/genie/deploy_genie_spaces.py

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.genie import GenieSpaceCreateRequest
import yaml

def create_genie_space(
    workspace: WorkspaceClient,
    space_name: str,
    description: str,
    instructions: str,
    warehouse_id: str,
    data_assets: list
):
    """Create a Genie Space with trusted data assets."""
    
    print(f"Creating Genie Space: {space_name}")
    
    # Create the Genie Space
    space = workspace.genie.create_genie_space(
        GenieSpaceCreateRequest(
            display_name=space_name,
            description=description,
            instructions=instructions,
            sql_warehouse_id=warehouse_id
        )
    )
    
    space_id = space.space_id
    print(f"✓ Created Genie Space ID: {space_id}")
    
    # Add trusted data assets
    print(f"Adding {len(data_assets)} trusted data assets...")
    for asset in data_assets:
        asset_type = asset['type']
        asset_name = asset['name']
        full_name = f"{asset['catalog']}.{asset['schema']}.{asset_name}"
        
        try:
            if asset_type == 'metric_view':
                workspace.genie.add_metric_view_asset(space_id, full_name)
            elif asset_type == 'function':
                workspace.genie.add_function_asset(space_id, full_name)
            elif asset_type == 'table':
                workspace.genie.add_table_asset(space_id, full_name)
            
            print(f"  ✓ Added {asset_type}: {asset_name}")
        except Exception as e:
            print(f"  ⚠ Warning adding {asset_name}: {e}")
    
    print(f"✅ Genie Space '{space_name}' deployed successfully!")
    return space_id

# Execute
catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
warehouse_id = dbutils.widgets.get("warehouse_id")

workspace = WorkspaceClient()

# Deploy all 7 Genie Spaces
spaces_config = [
    {
        'name': 'Cost Intelligence',
        'description': 'Natural language interface for Databricks cost analytics, spending trends, and optimization with ML-powered forecasting and anomaly detection.',
        'instructions': open('cost_intelligence_instructions.txt').read(),
        'assets': 'cost_intelligence_assets.yaml'
    },
    # ... (repeat for all 7 spaces)
]

deployed_spaces = []
for config in spaces_config:
    space_id = create_genie_space(
        workspace,
        config['name'],
        config['description'],
        config['instructions'],
        warehouse_id,
        yaml.safe_load(open(config['assets']))
    )
    deployed_spaces.append((config['name'], space_id))

print("\n" + "="*80)
print("GENIE SPACE DEPLOYMENT COMPLETE")
print("="*80)
for name, space_id in deployed_spaces:
    print(f"{name}: {space_id}")
```

### Step-by-Step Manual Deployment

If deploying manually via Databricks UI:

#### Step 1: Create Genie Space

1. Navigate to **Databricks SQL** → **Genie Spaces**
2. Click **Create Genie Space**
3. Enter **Space Name** (from Section A)
4. Enter **Description** (from Section B)
5. Select **SQL Warehouse** (Serverless recommended)
6. Click **Create**

#### Step 2: Configure General Instructions

1. Open the created Genie Space
2. Click **Edit Space**
3. Paste **General Instructions** (from Section E - ≤20 lines)
4. Click **Save**

⚠️ **CRITICAL:** General Instructions MUST be ≤20 lines for Genie to process effectively.

#### Step 3: Add Trusted Data Assets

**Order matters - add in this sequence:**

1. **Metric Views** (PRIMARY - add first)
   - Click **Add Trusted Asset** → **Metric View**
   - Select each metric view from Section D
   - Example: `cost_analytics`, `job_performance`, etc.

2. **Table-Valued Functions** (SPECIFIC - add second)
   - Click **Add Trusted Asset** → **Function**
   - Select each TVF from Section F
   - Example: `get_top_cost_contributors`, `get_failed_jobs`, etc.

3. **ML Prediction Tables** (ML - add third)
   - Click **Add Trusted Asset** → **Table**
   - Select prediction tables
   - Example: `cost_anomaly_predictions`, `job_failure_predictions`, etc.

4. **Monitoring Tables** (METRICS - add fourth)
   - Click **Add Trusted Asset** → **Table**
   - Select profile/drift tables
   - Example: `fact_usage_profile_metrics`, `fact_usage_drift_metrics`, etc.

5. **Gold Tables** (REFERENCE - add last, sparingly)
   - Click **Add Trusted Asset** → **Table**
   - Only add if explicitly needed
   - Example: `fact_usage`, `fact_job_run_timeline`, etc.

#### Step 4: Grant Permissions

1. Click **Permissions** tab
2. Add user groups:
   - **OWNER**: Your team (e.g., `data_engineering`)
   - **CAN USE**: Business users (e.g., `finance`, `operations`)
3. Verify users have SELECT on all data assets

---

## Testing & Validation

### Three-Level Testing Strategy

#### Level 1: Genie Space Standalone Testing (Phase 3.6)

Test each Genie Space independently before agent integration.

**Each Genie Space has 10-15 benchmark questions with EXACT SQL (Section G).**

**Testing Protocol:**

For each benchmark question:

1. **Ask the question** in natural language in Genie UI
2. **Review generated SQL** from Genie
3. **Compare to expected SQL** from Section G
4. **Validate results** match expected format
5. **Measure query time** (target: <10 seconds)

#### Level 2: Agent Integration Testing (Phase 4)

Test agents using Genie Spaces as their query interface.

**Agent Testing Protocol:**

For each agent:

1. **Initialize agent** with corresponding Genie Space
2. **Send sample query** to agent (same as Genie benchmark)
3. **Verify agent calls Genie** Space correctly
4. **Check agent receives results** from Genie
5. **Validate agent response** includes context and recommendations
6. **Measure end-to-end latency** (target: <15 seconds including agent reasoning)

**Example: Cost Agent Test**

```python
# Test Cost Agent using Cost Intelligence Genie
from agents import CostAgent

cost_agent = CostAgent(genie_space="cost_intelligence")

# Level 2 Test: Agent → Genie → Tool
query = "What are the top 5 cost contributors this month?"
response = cost_agent.execute(query)

# Validate:
assert response.genie_space_used == "cost_intelligence"
assert response.tool_called == "get_top_cost_contributors"
assert len(response.results) == 5
assert response.latency_seconds < 15
```

#### Level 3: Multi-Agent Workflow Testing (Phase 4)

Test Orchestrator Agent coordinating multiple specialized agents.

**Multi-Agent Testing Protocol:**

For complex queries:

1. **Send multi-domain query** to Orchestrator Agent
2. **Verify intent classification** routes to correct agents
3. **Check parallel agent execution** (if applicable)
4. **Validate result correlation** between agents
5. **Confirm synthesized response** addresses full query
6. **Measure total workflow time** (target: <20 seconds)

**Example: Multi-Agent Test**

```python
# Test Orchestrator with Cost + Reliability agents
from agents import OrchestratorAgent

orchestrator = OrchestratorAgent()

# Level 3 Test: Orchestrator → Multiple Agents → Multiple Genies
query = "Why did costs spike AND were there job failures last Tuesday?"
response = orchestrator.execute(query)

# Validate:
assert len(response.agents_used) == 2
assert "cost_agent" in response.agents_used
assert "reliability_agent" in response.agents_used
assert response.cost_results is not None
assert response.reliability_results is not None
assert response.correlation_analysis is not None
assert response.latency_seconds < 20
```

#### Example Test (Cost Intelligence)

**Question 1:** "What is our total spend this month?"

**Expected SQL:**
```sql
SELECT 
  SUM(MEASURE(total_cost)) as total_spend
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE);
```

**Expected Result:** Single row with total spend value

**Validation:**
- [ ] Genie used `cost_analytics` metric view
- [ ] Date filter applied correctly
- [ ] Result format is currency
- [ ] Query completed in <5 seconds

### Coverage Testing

Ensure benchmark questions cover:

- [ ] All metric views (at least 3 questions each)
- [ ] All TVFs (at least 1 question each)
- [ ] All time periods (today, last week, month, quarter, YTD)
- [ ] All major dimensions (workspace, owner, SKU, etc.)
- [ ] Key calculations (growth %, rates, rankings)
- [ ] ML predictions and anomalies
- [ ] Monitoring metrics and drift detection

### Accuracy Targets

| Question Type | Target Accuracy |
|---------------|-----------------|
| Basic (COUNT, SUM, AVG) | 95% |
| Filtered (time, dimension) | 90% |
| Comparative (trends, growth) | 85% |
| ML-Powered (predictions, anomalies) | 85% |
| Complex (multi-step) | 75% |

---

## Post-Deployment

### Step 1: Validate Agent Integration Readiness

**Before proceeding to Phase 4 (Agent Framework), confirm:**

#### API Access Validation

```python
# Validate Genie Space is accessible via SDK
from databricks.sdk import WorkspaceClient

workspace = WorkspaceClient()

# Test Cost Intelligence Genie Space
try:
    space = workspace.genie.get_space_by_name("Cost Intelligence")
    print(f"✅ Space ID: {space.space_id}")
    print(f"✅ SQL Warehouse: {space.sql_warehouse_id}")
    
    # Test a simple query
    response = workspace.genie.execute_query(
        space_id=space.space_id,
        query="What is the total cost this month?"
    )
    print(f"✅ Query successful: {response.result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Fix before proceeding to Phase 4")
```

#### Data Asset Registration Check

```python
# Verify all tools are registered as trusted assets
def validate_space_assets(space_id):
    """Validate all data assets are registered."""
    
    assets = workspace.genie.list_assets(space_id)
    
    expected_tvfs = 15  # For Cost Intelligence
    expected_mvs = 2
    expected_ml_tables = 6
    
    actual_tvfs = sum(1 for a in assets if a.type == 'FUNCTION')
    actual_mvs = sum(1 for a in assets if a.type == 'METRIC_VIEW')
    actual_ml_tables = sum(1 for a in assets if '_predictions' in a.name)
    
    print(f"TVFs: {actual_tvfs}/{expected_tvfs}")
    print(f"Metric Views: {actual_mvs}/{expected_mvs}")
    print(f"ML Tables: {actual_ml_tables}/{expected_ml_tables}")
    
    return (actual_tvfs >= expected_tvfs and 
            actual_mvs >= expected_mvs and 
            actual_ml_tables >= expected_ml_tables)

# Test for each Genie Space
spaces = [
    ("Cost Intelligence", 15, 2, 6),
    ("Job Health Monitor", 12, 1, 5),
    ("Performance Analyzer", 16, 3, 7),
    ("Security Auditor", 10, 2, 4),
    ("Data Quality Monitor", 7, 2, 3)
]

all_valid = True
for space_name, tvfs, mvs, ml in spaces:
    space = workspace.genie.get_space_by_name(space_name)
    if not validate_space_assets(space.space_id):
        print(f"❌ {space_name} missing assets")
        all_valid = False
    else:
        print(f"✅ {space_name} ready for agents")

if all_valid:
    print("\n✅ ALL GENIE SPACES READY FOR PHASE 4 AGENT FRAMEWORK")
else:
    print("\n❌ FIX MISSING ASSETS BEFORE PHASE 4")
```

#### Performance Baseline

```python
# Establish performance baselines for agent SLAs
import time

def benchmark_genie_query(space_id, query):
    """Measure Genie query latency."""
    start = time.time()
    response = workspace.genie.execute_query(space_id=space_id, query=query)
    latency = time.time() - start
    return latency, response

# Test representative queries from each domain
test_queries = {
    "Cost Intelligence": "What is the total cost this month?",
    "Job Health Monitor": "Show me failed jobs today",
    "Performance Analyzer": "What is the average query duration?",
    "Security Auditor": "Show me user activity for john@company.com",
    "Data Quality Monitor": "Which tables are stale?"
}

baselines = {}
for space_name, query in test_queries.items():
    space = workspace.genie.get_space_by_name(space_name)
    latency, _ = benchmark_genie_query(space.space_id, query)
    baselines[space_name] = latency
    
    status = "✅" if latency < 10 else "⚠️"
    print(f"{status} {space_name}: {latency:.2f}s")

# Agent target: Genie latency + 5s reasoning
print("\n📊 Expected Agent Latencies (Genie + 5s reasoning):")
for space_name, genie_latency in baselines.items():
    agent_latency = genie_latency + 5
    print(f"{space_name} Agent: ~{agent_latency:.2f}s")
```

#### Agent System Prompt Extraction

```python
# Extract General Instructions for agent system prompts
def extract_agent_instructions(space_name):
    """Extract Genie instructions for agent configuration."""
    space = workspace.genie.get_space_by_name(space_name)
    instructions = space.instructions
    
    # Save to agent config file
    with open(f"agents/config/{space_name.lower().replace(' ', '_')}_prompt.txt", "w") as f:
        f.write(instructions)
    
    print(f"✅ Extracted instructions for {space_name}")

# Extract for all agents
for space_name in test_queries.keys():
    extract_agent_instructions(space_name)

print("\n✅ Agent system prompts ready in agents/config/")
```

---

### Step 2: User Training (Human Users)

Create Quick Start Guide for each Genie Space:

```markdown
# Quick Start Guide: [Genie Space Name]

## What is Genie?
Natural language interface for [domain] analytics - ask questions in plain English!

## How to Access
1. Go to Databricks SQL
2. Click "Genie" in left navigation
3. Select "[Genie Space Name]"

## Example Questions

### [Category 1]
- "[Example question 1]"
- "[Example question 2]"

### [Category 2]
- "[Example question 3]"
- "[Example question 4]"

## Tips for Better Results
✓ Be specific with time periods ("last 30 days", "this quarter")
✓ Use business terms (we handle synonyms!)
✓ Ask follow-up questions to drill down
✓ Request visualizations ("show as chart")

## Need Help?
Contact: [Team Name]
Email: [email]
Slack: [channel]
```

### Step 2: Monitor Adoption

Track KPIs in first 30 days:

| Metric | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|--------|--------|--------|--------|
| Active Users | ___ | ___ | ___ | ___ |
| Questions Asked | ___ | ___ | ___ | ___ |
| Success Rate % | ___ | ___ | ___ | ___ |
| Avg Response Time (sec) | ___ | ___ | ___ | ___ |

### Step 3: Collect Feedback

Create feedback channel:

```markdown
## Genie Space Feedback Form

**Genie Space:** [Name]
**Date:** [Date]
**User:** [Name]

**What worked well?**
[Response]

**What didn't work?**
[Response]

**Questions that failed:**
1. [Question]
2. [Question]

**Feature requests:**
[Response]

**Overall Rating:** ⭐⭐⭐⭐⭐
```

### Step 4: Iterate

Based on usage patterns:

**Weekly:**
- Review failed queries
- Update instructions with clarifications
- Add new synonyms to metric views

**Monthly:**
- Analyze most frequent questions
- Add new benchmark questions
- Optimize slow queries
- User feedback session

**Quarterly:**
- Usage report (adoption, satisfaction)
- Training for new team members
- Review and update all benchmarks

---

## Troubleshooting

### Common Issues

#### Issue 1: Genie Uses Wrong Metric View

**Symptoms:** Query works but returns unexpected results

**Root Cause:** Contradictory or ambiguous routing rules in General Instructions

**Fix:**
1. Review General Instructions (Section E)
2. Add explicit routing rules:
```markdown
⚠️ CRITICAL - Routing:
- Host revenue → get_host_performance TVF (NOT host_analytics_metrics)
- Property revenue → revenue_analytics_metrics
```

3. Test with benchmark questions

#### Issue 2: MEASURE() Syntax Error

**Symptoms:** `UNRESOLVED_COLUMN` error on MEASURE()

**Root Cause:** Using `display_name` instead of column `name`

**Fix:**
```sql
-- ❌ WRONG
SELECT MEASURE(`Total Revenue`) FROM metrics;

-- ✅ CORRECT
SELECT MEASURE(total_revenue) FROM metrics;
```

Always use snake_case column `name`, not backticked `display_name`.

#### Issue 3: TVF Returns Empty Results

**Symptoms:** TVF query succeeds but returns 0 rows

**Root Cause:** Date parameters outside data range

**Fix:**
```sql
-- Use wide date range for all data
SELECT * FROM get_cost_trend_by_sku('1900-01-01', '2100-12-31', 'JOBS_COMPUTE');
```

#### Issue 4: Query Timeout

**Symptoms:** Query exceeds 10 second target

**Root Cause:** Querying fact tables directly instead of metric views

**Fix:**
1. Review General Instructions routing
2. Ensure Genie uses metric views (pre-aggregated)
3. Add rule: "NEVER query fact tables directly - use metric views"

#### Issue 5: Genie Wraps TVF with TABLE()

**Symptoms:** `NOT_A_SCALAR_FUNCTION` error

**Root Cause:** Missing TVF syntax guidance

**Fix:** Add to General Instructions:
```markdown
## TVF Syntax
1. NEVER wrap TVFs in TABLE() - call directly:
   ✅ SELECT * FROM get_customer_segments('2020-01-01', '2024-12-31')
   ❌ SELECT * FROM TABLE(get_customer_segments(...))
```

### Debug Checklist

When troubleshooting failed queries:

- [ ] Check General Instructions for contradictions
- [ ] Verify column names in MEASURE() (use `name`, not `display_name`)
- [ ] Confirm full 3-part namespace used (`catalog.schema.object`)
- [ ] Validate TVF parameters match signature
- [ ] Test SQL manually in SQL Editor
- [ ] Review Genie query history for patterns
- [ ] Check user permissions on all assets

---

## Maintenance

### Weekly Tasks

- [ ] Review Genie query history
- [ ] Identify failed queries (< 90% success rate)
- [ ] Update General Instructions with clarifications
- [ ] Add new example questions based on usage

### Monthly Tasks

- [ ] Analyze most frequently asked questions
- [ ] Update Space instructions with new patterns
- [ ] Add new synonyms to metric views/TVFs
- [ ] Review performance (query time, success rate)
- [ ] User feedback session

### Quarterly Tasks

- [ ] Comprehensive usage report (adoption, satisfaction)
- [ ] Training session for new team members
- [ ] Review and update all benchmark questions
- [ ] Optimize slow-performing queries
- [ ] Add new business questions as use cases evolve
- [ ] Update data assets with new TVFs/metric views

### Annual Review

- [ ] Full Genie Space audit
- [ ] User satisfaction survey
- [ ] ROI analysis (time saved, decisions made faster)
- [ ] Strategic roadmap for next year

---

## Success Criteria

### Phase 3.6: Genie Spaces (Immediate - First 30 Days)

**Standalone Genie Space Deployment:**

- [ ] All 7 Genie Spaces deployed
- [ ] All benchmark questions pass (>80% success rate)
- [ ] 10+ active users per space (human users testing)
- [ ] Average query time <10 seconds
- [ ] User satisfaction rating >4/5 (human feedback)

**Agent Integration Readiness:**

- [ ] Each Genie Space accessible via Databricks SDK
- [ ] All data assets (TVFs, MVs, ML models) registered as trusted assets
- [ ] General Instructions optimized for LLM agents (≤20 lines)
- [ ] API endpoints documented for agent consumption
- [ ] Rate limits and quotas configured

### Phase 4: Agent Framework (Short-Term - 3 Months)

**Agent Deployment:**

- [ ] 6 specialized agents deployed to Databricks Model Serving
- [ ] Orchestrator agent with intent classification (>90% accuracy)
- [ ] Each agent successfully uses corresponding Genie Space
- [ ] Agent → Genie → Tool flow validated end-to-end
- [ ] Multi-agent workflows functional

**Agent Performance:**

- [ ] Single-agent response time <15 seconds
- [ ] Multi-agent workflow time <20 seconds
- [ ] 90%+ query success rate via agents
- [ ] Agents handle 100+ queries/day
- [ ] <5% error rate in tool selection

**User Adoption (Agents):**

- [ ] 50+ users interacting with agents (vs direct Genie access)
- [ ] 1000+ agent queries executed
- [ ] 5+ teams using agents for daily monitoring
- [ ] Documented time savings >20 hours/week
- [ ] Agent responses rated 4+/5 for helpfulness

### Long-Term (6 Months) - Mature Agent Framework

**Scale & Reliability:**

- [ ] 100+ daily active users (agent + direct Genie)
- [ ] 5000+ agent queries executed
- [ ] 99%+ agent uptime
- [ ] <1 second p95 agent reasoning latency
- [ ] Agents scale to 1000+ concurrent queries

**Business Impact:**

- [ ] Ad-hoc SQL requests reduced by 50%
- [ ] Mean time to insight reduced by 60%
- [ ] Platform issues detected 80% faster
- [ ] Cost optimization recommendations implemented ($100K+ savings)
- [ ] Security incidents detected 2x faster

**Ecosystem Integration:**

- [ ] Agents integrated with Slack, Teams, Email
- [ ] Agents trigger automated runbooks
- [ ] Agents create Jira tickets for incidents
- [ ] Agents integrated into CI/CD pipelines
- [ ] Custom agents created by users (agent framework is extensible)

---

## Asset Summary by Domain

### 💰 Cost Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 15 | `get_top_cost_contributors`, `get_cost_anomalies`, `get_all_purpose_cluster_cost` |
| Metric Views | 2 | `cost_analytics`, `commit_tracking` |
| ML Models | 6 | Cost Anomaly, Forecaster, Budget Alert, Tag Recommender, User Behavior, Migration |
| Monitors | 1 | Cost Monitor (13 custom metrics) |

### ⚡ Performance Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 16 | `get_slow_queries`, `get_cluster_utilization`, `get_query_efficiency_analysis` |
| Metric Views | 3 | `query_performance`, `cluster_utilization`, `cluster_efficiency` |
| ML Models | 7 | Job Duration, Query Optimizer, Cache Hit, Capacity Planner, Right-Sizing, DBR Risk, Query Recommender |
| Monitors | 2 | Query Monitor (13 metrics), Cluster Monitor (11 metrics) |

### 🔄 Reliability Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 12 | `get_failed_jobs`, `get_job_success_rate`, `get_job_repair_costs` |
| Metric Views | 1 | `job_performance` |
| ML Models | 5 | Failure Predictor, Retry Success, Pipeline Health, Incident Impact, Self-Healing |
| Monitors | 1 | Job Monitor (14 custom metrics) |

### 🔒 Security Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 10 | `get_user_activity_summary`, `get_sensitive_table_access`, `get_off_hours_activity` |
| Metric Views | 2 | `security_events`, `governance_analytics` |
| ML Models | 4 | Access Anomaly, User Risk, Access Classifier, Off-Hours Predictor |
| Monitors | 1 | Security Monitor (14 custom metrics) |

### ✅ Quality Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 7 | `get_table_freshness`, `get_data_quality_summary`, `get_pipeline_data_lineage` |
| Metric Views | 2 | `data_quality`, `ml_intelligence` |
| ML Models | 3 | Quality Anomaly, Trend Predictor, Freshness Alert |
| Monitors | 2 | Quality Monitor (10 metrics), Governance Monitor (12 metrics) |

---

## References

### Phase 4 Integration
- [Phase 4 - Agent Framework Plan](../../plans/phase4-agent-framework.md) - **Multi-agent architecture for Databricks monitoring**
- [Agent Framework Architecture](../../plans/phase4-agent-framework.md#architecture) - Orchestrator + 6 specialized agents
- [Agent Tool Integration](../../plans/phase4-agent-framework.md#implementation) - LangChain + Databricks Foundation Models

### Official Databricks Documentation
- [Databricks Genie](https://docs.databricks.com/genie)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Genie Instructions Best Practices](https://docs.databricks.com/genie/instructions)
- [Genie Conversation API](https://docs.databricks.com/aws/genie/set-up)
- [Databricks Foundation Models](https://docs.databricks.com/en/machine-learning/foundation-models/) - LLMs for agents
- [Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/) - Agent deployment
- [LangChain Integration](https://python.langchain.com/docs/integrations/providers/databricks) - Agent framework

### Project Documentation - Phase 3 Outputs
- [Genie Space Configurations](../../src/genie/) - All 7 Genie Space setup documents
- [TVF Inventory](../../src/semantic/tvfs/TVF_INVENTORY.md) - 60 TVFs (Agent Tools)
- [Metric Views Inventory](../../src/semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 10 Metric Views (Agent Tools)
- [ML Models Inventory](../../src/ml/ML_MODELS_INVENTORY.md) - 25 ML Models (Agent Tools)
- [Lakehouse Monitoring Inventory](../../docs/reference/LAKEHOUSE_MONITORING_INVENTORY.md) - 8 Monitors (Agent Tools)
- [Genie Space Post-Mortem](../../docs/reference/genie-space-semantic-layer-postmortem.md) - Lessons learned

### Cursor Rules
- [16-genie-space-patterns.mdc](mdc:../../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc) - Mandatory 7-section structure
- [15-databricks-table-valued-functions.mdc](mdc:../../.cursor/rules/semantic-layer/15-databricks-table-valued-functions.mdc) - TVF patterns
- [14-metric-views-patterns.mdc](mdc:../../.cursor/rules/semantic-layer/14-metric-views-patterns.mdc) - Metric view patterns

---

## Next Steps: Phase 4 Agent Framework

### Roadmap to AI Agents

Once Genie Spaces are deployed and validated, proceed to Phase 4: Agent Framework.

#### Phase 4 Implementation Plan

**Week 1-2: Agent Framework Setup**

- [ ] Install LangChain and LangGraph libraries
- [ ] Configure Databricks Foundation Model (DBRX) access
- [ ] Create agent configuration templates
- [ ] Set up agent state management (Unity Catalog tables)
- [ ] Configure Model Serving endpoints

**Week 3-4: Specialized Agent Development**

Develop agents in this order (based on complexity):

1. **Cost Agent** (Simplest - good starting point)
   - Tools: Cost Intelligence Genie Space
   - System prompt: `agents/config/cost_agent_prompt.txt`
   - Test queries: Budget variance, cost spikes, top contributors

2. **Security Agent** (Similar complexity)
   - Tools: Security Auditor Genie Space
   - System prompt: `agents/config/security_agent_prompt.txt`
   - Test queries: Threat detection, user activity, access anomalies

3. **Performance Agent** (Moderate complexity)
   - Tools: Performance Analyzer Genie Space
   - System prompt: `agents/config/performance_agent_prompt.txt`
   - Test queries: Slow queries, cluster utilization, bottlenecks

4. **Reliability Agent** (Moderate complexity)
   - Tools: Job Health Monitor Genie Space
   - System prompt: `agents/config/reliability_agent_prompt.txt`
   - Test queries: SLA compliance, job failures, incident detection

5. **Data Quality Agent** (Higher complexity - lineage queries)
   - Tools: Data Quality Monitor Genie Space
   - System prompt: `agents/config/dq_agent_prompt.txt`
   - Test queries: Table freshness, lineage tracking, quality scores

6. **ML Ops Agent** (Highest complexity - ML-specific)
   - Tools: ML Intelligence Genie Space
   - System prompt: `agents/config/mlops_agent_prompt.txt`
   - Test queries: Model performance, drift detection, experiment tracking

**Week 5-6: Orchestrator Agent**

- [ ] Implement intent classification (keyword-based → ML-based)
- [ ] Build agent routing logic
- [ ] Develop multi-agent workflow coordination
- [ ] Implement response synthesis
- [ ] Test complex multi-domain queries

**Week 7-8: Deployment & Integration**

- [ ] Deploy agents to Databricks Model Serving
- [ ] Integrate with Slack/Teams/Email
- [ ] Create agent monitoring dashboard
- [ ] Set up alerting for agent failures
- [ ] Load testing (1000+ concurrent queries)

#### Agent Development Template

```python
# agents/cost_agent.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain_databricks import ChatDatabricks
from langchain.tools import StructuredTool
from databricks.sdk import WorkspaceClient

class CostAgent:
    """Cost Agent using Cost Intelligence Genie Space."""
    
    def __init__(self, genie_space_name="Cost Intelligence"):
        """Initialize Cost Agent with Genie Space."""
        
        self.workspace = WorkspaceClient()
        self.genie_space = self.workspace.genie.get_space_by_name(genie_space_name)
        
        # Load system prompt from Genie instructions
        self.system_prompt = self._load_system_prompt()
        
        # Initialize LLM
        self.llm = ChatDatabricks(
            model="databricks-meta-llama-3-70b-instruct",
            temperature=0
        )
        
        # Define tools (Genie Space as primary tool)
        self.tools = [
            self._create_genie_tool(),
            self._create_anomaly_detector_tool()
        ]
        
        # Create agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.system_prompt
        )
        
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=5,
            handle_parsing_errors=True,
            verbose=True
        )
    
    def _load_system_prompt(self):
        """Load system prompt from Genie Space instructions."""
        with open("agents/config/cost_agent_prompt.txt", "r") as f:
            return f.read()
    
    def _create_genie_tool(self):
        """Create tool that queries Cost Intelligence Genie Space."""
        
        def query_cost_genie(query: str) -> dict:
            """Query the Cost Intelligence Genie Space."""
            try:
                response = self.workspace.genie.execute_query(
                    space_id=self.genie_space.space_id,
                    query=query
                )
                return {
                    "success": True,
                    "results": response.result,
                    "sql": response.sql_generated
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        return StructuredTool.from_function(
            func=query_cost_genie,
            name="cost_intelligence_genie",
            description="""Query the Cost Intelligence Genie Space for cost analytics.
            Use this for: cost trends, top contributors, budget variance, SKU analysis.
            Input: Natural language question about costs.
            Returns: Query results with cost data."""
        )
    
    def _create_anomaly_detector_tool(self):
        """Create tool that checks cost anomaly predictions."""
        
        def check_cost_anomalies(date: str = None) -> dict:
            """Check ML-detected cost anomalies."""
            query = f"""
                SELECT * FROM cost_anomaly_predictions
                WHERE is_anomaly = true
                {'AND usage_date = ' + date if date else 'AND usage_date = CURRENT_DATE'}
                ORDER BY anomaly_score DESC
                LIMIT 10
            """
            # Execute via Genie or direct SQL
            return self.workspace.genie.execute_query(
                space_id=self.genie_space.space_id,
                query=f"Show me cost anomalies for {date or 'today'}"
            )
        
        return StructuredTool.from_function(
            func=check_cost_anomalies,
            name="cost_anomaly_detector",
            description="""Check for ML-detected cost anomalies.
            Use this when user asks about 'unusual costs', 'cost spikes', or 'anomalies'.
            Input: Date to check (optional, defaults to today).
            Returns: List of detected cost anomalies with scores."""
        )
    
    def execute(self, query: str) -> dict:
        """Execute a cost-related query."""
        try:
            result = self.executor.invoke({"input": query})
            return {
                "success": True,
                "response": result["output"],
                "genie_space_used": self.genie_space.display_name,
                "tools_called": [t.name for t in self.tools if t.name in result.get("intermediate_steps", [])]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Usage
if __name__ == "__main__":
    cost_agent = CostAgent()
    
    # Test query
    response = cost_agent.execute(
        "What are the top 5 cost contributors this month?"
    )
    
    print(response)
```

#### Orchestrator Agent Template

```python
# agents/orchestrator_agent.py
from langchain.agents import AgentExecutor
from agents.cost_agent import CostAgent
from agents.security_agent import SecurityAgent
from agents.performance_agent import PerformanceAgent
# ... import other agents

class OrchestratorAgent:
    """Orchestrator Agent that routes to specialized agents."""
    
    def __init__(self):
        """Initialize Orchestrator with all specialized agents."""
        
        self.agents = {
            "cost": CostAgent(),
            "security": SecurityAgent(),
            "performance": PerformanceAgent(),
            "reliability": ReliabilityAgent(),
            "data_quality": DataQualityAgent(),
            "mlops": MLOpsAgent()
        }
        
        # Keywords for intent classification
        self.intent_keywords = {
            "cost": ["cost", "spending", "dbu", "budget", "expensive", "price"],
            "security": ["security", "access", "audit", "threat", "permission"],
            "performance": ["slow", "performance", "latency", "bottleneck", "query"],
            "reliability": ["failed", "failure", "sla", "incident", "down"],
            "data_quality": ["quality", "lineage", "fresh", "stale", "governance"],
            "mlops": ["model", "experiment", "serving", "drift", "mlflow"]
        }
    
    def classify_intent(self, query: str) -> list:
        """Classify user query to determine which agent(s) to use."""
        query_lower = query.lower()
        intents = []
        
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                intents.append(intent)
        
        # Default to cost if no clear intent
        if not intents:
            intents = ["cost"]
        
        return intents
    
    def execute(self, query: str) -> dict:
        """Execute query by routing to appropriate agent(s)."""
        
        # Classify intent
        intents = self.classify_intent(query)
        
        if len(intents) == 1:
            # Single agent
            agent = self.agents[intents[0]]
            return agent.execute(query)
        
        else:
            # Multi-agent workflow
            results = {}
            for intent in intents:
                agent = self.agents[intent]
                results[intent] = agent.execute(query)
            
            # Synthesize results
            return self._synthesize_results(query, results)
    
    def _synthesize_results(self, query: str, results: dict) -> dict:
        """Synthesize results from multiple agents."""
        
        # Use LLM to combine and correlate results
        synthesis_prompt = f"""
        User Query: {query}
        
        Results from multiple agents:
        {results}
        
        Synthesize a unified response that:
        1. Answers the original query
        2. Correlates findings across agents
        3. Provides actionable recommendations
        """
        
        # Call LLM for synthesis
        # ... implementation
        
        return {
            "success": True,
            "agents_used": list(results.keys()),
            "synthesized_response": synthesized_text,
            "individual_results": results
        }

# Usage
if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    
    # Test single-intent query
    response1 = orchestrator.execute(
        "What are the top cost drivers?"
    )
    
    # Test multi-intent query
    response2 = orchestrator.execute(
        "Why did costs spike AND were there job failures last Tuesday?"
    )
    
    print(response1)
    print(response2)
```

#### Deployment to Model Serving

```python
# deploy_agents.py
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

workspace = WorkspaceClient()

# Register agents as Unity Catalog models
# Then deploy to Model Serving endpoints

agents = [
    "cost_agent",
    "security_agent", 
    "performance_agent",
    "reliability_agent",
    "data_quality_agent",
    "mlops_agent",
    "orchestrator_agent"
]

for agent_name in agents:
    # Create serving endpoint
    endpoint = workspace.serving_endpoints.create(
        name=f"health_monitor_{agent_name}",
        config=EndpointCoreConfigInput(
            served_entities=[
                ServedEntityInput(
                    entity_name=f"health_monitor.agents.{agent_name}",
                    entity_version="1",
                    scale_to_zero_enabled=True,
                    workload_size="Small"
                )
            ]
        )
    )
    
    print(f"✅ Deployed {agent_name} to endpoint: {endpoint.id}")
```

---

## Appendix

### A. Deployment Checklist

**Pre-Deployment:**
- [ ] All Gold tables deployed (38 tables)
- [ ] All TVFs deployed (60 functions)
- [ ] All Metric Views deployed (10 views)
- [ ] All ML models deployed (25 prediction tables)
- [ ] All Lakehouse Monitors deployed (8 monitors)
- [ ] SQL Warehouse created and running
- [ ] Permissions granted to users

**Configuration:**
- [ ] Space Name defined (Section A)
- [ ] Space Description written (Section B)
- [ ] Sample Questions documented (Section C - 10-15)
- [ ] Data Assets listed (Section D)
- [ ] General Instructions written (Section E - ≤20 lines)
- [ ] TVFs documented (Section F)
- [ ] Benchmark Questions with SQL (Section G - 10-15)

**Deployment:**
- [ ] Genie Space created in UI
- [ ] General Instructions added
- [ ] All metric views added as trusted assets
- [ ] All TVFs added as trusted assets
- [ ] ML prediction tables added
- [ ] Monitoring tables added
- [ ] Permissions granted

**Testing:**
- [ ] All benchmark questions tested (>80% pass rate)
- [ ] Query performance validated (<10 sec)
- [ ] Results validated against expected format
- [ ] User training materials created
- [ ] Quick Start Guide distributed

**Post-Deployment:**
- [ ] Monitoring dashboard set up
- [ ] Feedback channel created
- [ ] Weekly review scheduled
- [ ] Monthly analysis scheduled

### B. Environment Variables

```yaml
# databricks.yml
variables:
  catalog:
    description: Unity Catalog name
    default: prashanth_subrahmanyam_catalog
  
  gold_schema:
    description: Gold layer schema name
    default: health_monitor_gold
  
  warehouse_id:
    description: SQL Warehouse ID for Genie Spaces
    default: "<warehouse-id>"

targets:
  dev:
    variables:
      catalog: prashanth_subrahmanyam_catalog
      gold_schema: dev_prashanth_subrahmanyam_health_monitor_gold
      warehouse_id: "<dev-warehouse-id>"
  
  prod:
    variables:
      catalog: prashanth_subrahmanyam_catalog
      gold_schema: health_monitor_gold
      warehouse_id: "<prod-warehouse-id>"
```

### C. Contact Information

**Project Team:**
- **Project Lead:** [Name]
- **Data Engineering:** [Team]
- **Support Channel:** #databricks-health-monitor
- **Email:** databricks-support@company.com

**Escalation:**
- **Technical Issues:** [Engineering Lead]
- **Access Issues:** [Workspace Admin]
- **Feature Requests:** [Product Owner]

---

## Complete Architecture Flow

### From Data Assets → Genie Spaces → AI Agents → Users

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             END USERS                                        │
│  Natural language questions about Databricks platform health                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ "Why did costs spike last Tuesday?"
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: AI AGENT FRAMEWORK                               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │ ORCHESTRATOR AGENT (LangChain/LangGraph)                   │            │
│  │ • Intent: "cost spike" → Cost Agent                        │            │
│  │ • Unified Health Monitor Genie Space                       │            │
│  └────────────────────────────────────────────────────────────┘            │
│                               │                                              │
│                               ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │ COST AGENT                                                  │            │
│  │ • Receives query from Orchestrator                         │            │
│  │ • Uses Cost Intelligence Genie Space as tool               │            │
│  │ • System prompt from Genie instructions                    │            │
│  └────────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ "Show cost trend for last 14 days"
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3.6: GENIE SPACES LAYER                             │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │ COST INTELLIGENCE GENIE SPACE                              │            │
│  │ • Translates natural language → SQL                        │            │
│  │ • Selects appropriate tool (Metric View vs TVF)            │            │
│  │ • Decision: Use get_cost_trend_by_sku TVF                  │            │
│  └────────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ SELECT * FROM get_cost_trend_by_sku(
                                  │   DATE_SUB(CURRENT_DATE, 14), 
                                  │   CURRENT_DATE,
                                  │   'JOBS_COMPUTE'
                                  │ )
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: DATA ASSETS (Agent Tools)                        │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │ get_cost_trend_by_sku TVF (Phase 3.2)                     │            │
│  │ • Parameterized query: start_date, end_date, sku_name     │            │
│  │ • Returns daily cost trend data                            │            │
│  └────────────────────────────────────────────────────────────┘            │
│                               │                                              │
│                               ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │ fact_usage Gold Table (Phase 2)                            │            │
│  │ • System table data transformed to Gold layer              │            │
│  │ • Aggregated by workspace, SKU, date                       │            │
│  └────────────────────────────────────────────────────────────┘            │
│                               │                                              │
│                               ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │ cost_anomaly_predictions ML Table (Phase 3.1)             │            │
│  │ • ML-detected anomalies in cost data                       │            │
│  │ • Anomaly score, expected vs actual cost                   │            │
│  └────────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Results + Anomaly Detection
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENT RESPONSE SYNTHESIS                                  │
│                                                                              │
│  Cost Agent receives:                                                       │
│  1. Cost trend data (14 days) from TVF                                      │
│  2. Anomaly detection results from ML table                                 │
│  3. Context from cost_analytics metric view                                 │
│                                                                              │
│  Cost Agent synthesizes:                                                    │
│  "Your costs increased by 35% on Tuesday (Dec 26).                          │
│  Analysis shows:                                                            │
│  • JOBS_COMPUTE SKU spike: $15K → $21K (+40%)                              │
│  • ML detected this as an anomaly (score: 0.85)                            │
│  • Root cause: 3 new data pipelines launched by workspace 'data-eng'       │
│  • Recommendation: Review pipeline efficiency, consider cost optimization"  │
│                                                                              │
│  Orchestrator Agent returns response to user                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Benefits of This Architecture

| Layer | Benefit | Impact |
|-------|---------|--------|
| **AI Agents (Phase 4)** | Natural conversation, proactive insights, automated actions | Users get intelligent responses, not just data |
| **Genie Spaces (Phase 3.6)** | Natural language → SQL translation, semantic understanding | Agents don't write SQL, faster development |
| **Data Assets (Phase 3)** | Pre-aggregated analytics, ML predictions, monitoring | Fast queries (<10s), predictive insights |
| **Gold Tables (Phase 2)** | Clean, modeled data with business semantics | Accurate, trusted data foundation |

### Success Metrics: Genie Spaces + Agents

| Metric | Genie Spaces Alone | With AI Agents | Improvement |
|--------|-------------------|----------------|-------------|
| **User Adoption** | 50-100 power users | 500+ all users | 5-10x |
| **Query Success Rate** | 85% (humans iterate) | 95% (agents retry) | +10% |
| **Time to Insight** | 2-5 minutes (human) | 10-30 seconds (agent) | 10x faster |
| **Proactive Alerts** | 0 (reactive only) | 100+ daily (agents monitor) | ∞ |
| **Complex Analysis** | 10% of queries | 40% of queries | 4x more |
| **24/7 Availability** | No (human analysts) | Yes (agents always on) | Always |

---

**Document Version:** 2.0  
**Last Updated:** December 30, 2025  
**Next Review:** March 30, 2026  

**Phase 3.6 Status:** ✅ Ready for Deployment  
**Phase 4 Status:** 📋 Ready to Start (after Genie Spaces deployed)

