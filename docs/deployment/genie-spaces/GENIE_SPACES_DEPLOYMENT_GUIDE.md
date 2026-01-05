# Genie Spaces Deployment Guide
# Databricks Health Monitor - Agent Framework Natural Language Interface

**Version:** 3.1  
**Last Updated:** January 1, 2026  
**Status:** Production-Ready  
**Related:** Phase 4 - Agent Framework

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Semantic Layer Architecture](#semantic-layer-architecture)
3. [Agent Framework Integration](#agent-framework-integration)
4. [Prerequisites](#prerequisites)
5. [Deployment Architecture](#deployment-architecture)
6. [Pre-Deployment Validation](#pre-deployment-validation)
7. [Genie Space Configurations](#genie-space-configurations)
8. [Asset Selection Framework](#asset-selection-framework)
9. [Deployment Steps](#deployment-steps)
10. [Testing & Validation](#testing--validation)
11. [Post-Deployment](#post-deployment)
12. [Troubleshooting](#troubleshooting)
13. [Maintenance](#maintenance)

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
│  - 8 Lakehouse Monitors (210+ Custom Metrics for Drift Detection)       │
│  - 38 Gold Tables (Reference Data)                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Concept:** Genie Spaces provide the **natural language query execution layer** that agents use to interact with data assets. Each specialized agent has a corresponding Genie Space that understands domain-specific terminology and routes to appropriate tools.

### Genie Spaces → Agent Mapping

| Genie Space | Phase 4 Agent | Agent Purpose | Assets (Agent Tools) | Status |
|-------------|---------------|---------------|----------------------|--------|
| **Cost Intelligence** | 💰 Cost Agent | Analyze costs, forecast spending, optimize resources | 15 TVFs, 2 Metric Views, 35 Custom Metrics, 1 Monitor | ✅ Ready |
| **Job Health Monitor** | 🔄 Reliability Agent | Ensure platform reliability, manage incidents, track SLAs | 12 TVFs, 1 Metric View, 50 Custom Metrics, 1 Monitor | ✅ Ready |
| **Performance Analyzer** | ⚡ Performance Agent | Monitor job/query/cluster performance, optimize bottlenecks | 16 TVFs, 3 Metric Views, 86 Custom Metrics, 2 Monitors | ✅ Ready |
| **Security Auditor** | 🔒 Security Agent | Monitor security posture, detect threats, ensure compliance | 10 TVFs, 2 Metric Views, 13 Custom Metrics, 1 Monitor | ✅ Ready |
| **Data Quality Monitor** | ✅ Data Quality Agent | Ensure data quality, maintain lineage, enforce governance | 7 TVFs, 2 Metric Views, 26 Custom Metrics, 2 Monitors | ✅ Ready |
| **ML Intelligence** | 🤖 ML Ops Agent | Monitor ML experiments, models, and serving endpoints | Integrated in other spaces | ✅ Ready |
| **Databricks Health Monitor** | 🌐 Orchestrator Agent | Route queries to specialized agents, coordinate workflows | All 60 TVFs, 10 Metric Views, 210+ Custom Metrics, 8 Monitors | ✅ Ready |

**Note:** Performance Analyzer consolidates Query Performance + Cluster Optimizer from Phase 3 to align with the single Performance Agent in Phase 4.

### Total Asset Inventory

| Asset Type | Total Count | Phase | Status |
|------------|-------------|-------|--------|
| **Gold Tables** | 38 | Phase 2 | ✅ Deployed |
| **TVFs** | 60 | Phase 3.2 | ✅ Deployed |
| **Metric Views** | 10 | Phase 3.3 | ✅ Deployed |
| **Custom Metrics** | 210+ | Phase 3.4 | ✅ Deployed |
| **Lakehouse Monitors** | 8 | Phase 3.4 | ✅ Deployed |
| **Genie Spaces** | 7 | Phase 3.6 | 🔄 Ready to Deploy |
| **AI Agents** | 7 | Phase 4 | 📋 Planned |

---

## Semantic Layer Architecture

### The Three-Pillar Semantic Layer

The Databricks Health Monitor implements a **rationalized semantic layer** with three complementary components, each serving a distinct purpose:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SEMANTIC LAYER HIERARCHY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    CUSTOM METRICS (Lakehouse Monitoring)            │    │
│  │         Purpose: TIME SERIES ANALYSIS & DRIFT DETECTION              │    │
│  │                                                                      │    │
│  │   ✅ Automated computation every refresh                            │    │
│  │   ✅ Period-over-period drift (baseline vs current)                 │    │
│  │   ✅ Statistical profiling (distribution, nulls, cardinality)       │    │
│  │   ✅ Anomaly detection via drift thresholds                         │    │
│  │   ❌ NOT for user-parameterized queries                             │    │
│  │   ❌ NOT for ad-hoc drill-down                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                         │
│                                    │ Alerts trigger when drift exceeds       │
│                                    │ thresholds, then user drills down       │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    METRIC VIEWS (10 Views)                          │    │
│  │         Purpose: AGGREGATE ANALYTICS FOR DASHBOARDS                  │    │
│  │                                                                      │    │
│  │   ✅ Pre-configured dimensions and measures                         │    │
│  │   ✅ Natural language: "Show me total cost by workspace"            │    │
│  │   ✅ Dashboard KPIs with formatting                                 │    │
│  │   ❌ NOT for specific date range queries                            │    │
│  │   ❌ NOT for entity-specific lookups                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                         │
│                                    │ Dashboard shows high-level trend,       │
│                                    │ user wants to drill into specifics      │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    TVFs (60 Functions)                              │    │
│  │         Purpose: PARAMETERIZED DRILL-DOWN QUERIES                    │    │
│  │                                                                      │    │
│  │   ✅ User-specified date ranges, top_n, thresholds                  │    │
│  │   ✅ "Show me the top 10 cost drivers this week"                    │    │
│  │   ✅ Entity-specific lookups (job, user, table)                     │    │
│  │   ✅ Actionable lists (what failed, what's slow)                    │    │
│  │   ❌ NOT for trend analysis over time                               │    │
│  │   ❌ NOT for automated monitoring                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Principle: Alert → Dashboard → Drill-Down

```
1. CUSTOM METRICS detect drift, trigger SQL Alerts
2. User checks METRIC VIEW dashboard for context
3. User calls TVF for specific investigation
```

### Component Comparison

| Aspect | Custom Metrics | Metric Views | TVFs |
|--------|----------------|--------------|------|
| **Count** | 210+ | 10 (122+ dims/measures) | 60 |
| **Invocation** | Auto-computed | `SELECT MEASURE(...)` | `SELECT * FROM func(...)` |
| **Parameters** | None (time series) | Dimension filters | Date ranges, thresholds, top_n |
| **Best For** | Alerting, drift detection | Dashboard KPIs | Investigation, action lists |
| **Time Capability** | Period comparison | Aggregate over periods | Point-in-time filters |

### 277 Total Measurements

All measurements across the platform are documented in the **Metrics Inventory**:

| Domain | Total Measurements | TVF | Metric View | Custom Metric |
|--------|-------------------|-----|-------------|---------------|
| 💰 Cost | 67 | 38 | 42 | 35 |
| 🔄 Reliability | 58 | 32 | 16 | 50 |
| ⚡ Performance (Query) | 52 | 28 | 18 | 46 |
| ⚡ Performance (Cluster) | 38 | 18 | 24 | 40 |
| 🔒 Security | 28 | 24 | 12 | 13 |
| 📋 Quality | 32 | 18 | 10 | 26 |
| **Total** | **277** | **158** | **122** | **210** |

> **Note:** Some measurements appear in multiple methods (e.g., `success_rate` is in all three), which is **intentional** as they serve different use cases.

### Reference Documents

| Document | Purpose |
|----------|---------|
| [Metrics Inventory](../reference/metrics-inventory.md) | Complete list of all 277 measurements with method availability |
| [Semantic Layer Rationalization](../reference/semantic-layer-rationalization.md) | Analysis of overlaps and complementary purposes |
| [Genie Asset Selection Guide](../reference/genie-asset-selection-guide.md) | Decision tree for Genie to select the right asset |

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
        [fact_usage_drift_metrics] (Custom Metrics)
                    ↓
            Results → Cost Agent
                    ↓
        Natural Language Response
```

### Agent Tools = Genie Space Data Assets

Each agent's "tools" (in LangChain terminology) are the data assets registered in its Genie Space:

| Agent | Genie Space | Tool Types Available |
|-------|-------------|----------------------|
| **Cost Agent** | Cost Intelligence | • 15 TVFs (e.g., `get_top_cost_contributors`)<br>• 2 Metric Views (`cost_analytics`, `commit_tracking`)<br>• 35 Custom Metrics (cost drift, tag coverage drift) |
| **Security Agent** | Security Auditor | • 10 TVFs (e.g., `get_user_activity_summary`)<br>• 2 Metric Views (`security_events`, `governance_analytics`)<br>• 13 Custom Metrics (auth failure drift) |
| **Performance Agent** | Performance Analyzer | • 16 TVFs (e.g., `get_slow_queries`, `get_cluster_utilization`)<br>• 3 Metric Views (query, cluster metrics)<br>• 86 Custom Metrics (latency drift, efficiency drift) |
| **Reliability Agent** | Job Health Monitor | • 12 TVFs (e.g., `get_failed_jobs`, `get_job_sla_compliance`)<br>• 1 Metric View (`job_performance`)<br>• 50 Custom Metrics (success rate drift) |
| **Data Quality Agent** | Data Quality Monitor | • 7 TVFs (e.g., `get_table_freshness`, `get_pipeline_data_lineage`)<br>• 2 Metric Views (`data_quality`, `ml_intelligence`)<br>• 26 Custom Metrics (freshness drift, quality drift) |
| **ML Ops Agent** | ML Intelligence | • Integrated ML monitoring across all spaces<br>• Access to `fact_mlflow_runs`, `fact_endpoint_usage` |
| **Orchestrator Agent** | Unified Health Monitor | • All 60 TVFs + 10 Metric Views + 210+ Custom Metrics<br>• Routes to specialized Genie Spaces based on intent |

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
Phase 3.4: Lakehouse Monitors (8) + Custom Metrics (210+)
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

- [ ] **Lakehouse Monitors** (8 monitors with profile/drift tables)
  - Location: `src/monitoring/`
  - Validation: `SELECT COUNT(*) FROM system.information_schema.tables WHERE table_name LIKE '%_profile_metrics'`
  - Expected: 16 monitoring tables (8 profile + 8 drift)

- [ ] **Custom Metrics** (210+ metrics in monitoring tables)
  - Validation: Query `_profile_metrics` tables for custom columns
  - Expected: Custom metric columns in all monitoring tables

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
│  │  All 60 TVFs + 10 Metric Views + 210+ Custom Metrics         │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                               │                                              │
│         ┌─────────────────────┼──────────────────────┐                     │
│         ▼                     ▼                      ▼                     │
│  ┌─────────────┐      ┌─────────────┐       ┌─────────────┐              │
│  │Cost Intel   │      │Security     │       │Performance  │              │
│  │Genie        │      │Auditor      │       │Analyzer     │              │
│  │15 TVFs      │      │Genie        │       │Genie        │              │
│  │2 MVs        │      │10 TVFs      │       │16 TVFs      │              │
│  │35 CMs       │      │2 MVs        │       │3 MVs        │              │
│  └─────────────┘      │13 CMs       │       │86 CMs       │              │
│         ▼             └─────────────┘       └─────────────┘              │
│  ┌─────────────┐      ┌─────────────┐       ┌─────────────┐              │
│  │Job Health   │      │Data Quality │       │ML Intel     │              │
│  │Monitor      │      │Monitor      │       │Genie        │              │
│  │Genie        │      │Genie        │       │(Integrated) │              │
│  │12 TVFs      │      │7 TVFs       │       │             │              │
│  │1 MV         │      │2 MVs        │       │             │              │
│  │50 CMs       │      │26 CMs       │       │             │              │
│  └─────────────┘      └─────────────┘       └─────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ SQL + Function Calls
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: DATA ASSETS (Agent Tools)                        │
│              60 TVFs + 10 Metric Views + 210+ Custom Metrics + 8 Monitors   │
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

3. CUSTOM METRICS (Drift detection - Lakehouse Monitoring)
   ├── _profile_metrics tables (time series)
   ├── _drift_metrics tables (period comparison)
   └── Automated alerting

4. GOLD TABLES (Reference only, use sparingly)
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
    
    # 4. Check Monitoring Tables (Profile + Drift)
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
-- Cost Analytics (Metric View)
SELECT MEASURE(total_cost) FROM ${catalog}.${gold_schema}.cost_analytics;

-- Job Performance (TVF)
SELECT * FROM ${catalog}.${gold_schema}.get_failed_jobs(CURRENT_DATE - 7, CURRENT_DATE) LIMIT 10;

-- Query Performance (Metric View)
SELECT MEASURE(p95_duration_seconds) FROM ${catalog}.${gold_schema}.query_performance;

-- Custom Metrics (Drift Detection)
SELECT * FROM ${catalog}.${gold_schema}.fact_usage_drift_metrics ORDER BY window_end DESC LIMIT 1;

-- Security (TVF)
SELECT * FROM ${catalog}.${gold_schema}.get_user_activity_summary('john@company.com', CURRENT_DATE - 30, CURRENT_DATE);

-- Data Quality (TVF)
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
| **💰 Cost Agent** | Cost Intelligence | • Analyze costs & spending<br>• Forecast DBU usage<br>• Budget variance detection<br>• Cost optimization recommendations | • 15 TVFs (e.g., `get_top_cost_contributors`)<br>• 2 Metric Views<br>• 35 Custom Metrics (cost drift)<br>• 1 Monitor |
| **🔒 Security Agent** | Security Auditor | • Monitor audit logs<br>• Detect threats<br>• Track access patterns<br>• Compliance reporting | • 10 TVFs (e.g., `get_user_activity_summary`)<br>• 2 Metric Views<br>• 13 Custom Metrics (auth drift)<br>• 1 Monitor |
| **⚡ Performance Agent** | Performance Analyzer | • Monitor job/query/cluster performance<br>• Identify bottlenecks<br>• Optimize resource utilization<br>• Performance trending | • 16 TVFs (e.g., `get_slow_queries`)<br>• 3 Metric Views<br>• 86 Custom Metrics (latency drift)<br>• 2 Monitors |
| **🔄 Reliability Agent** | Job Health Monitor | • Track SLAs<br>• Incident detection<br>• Failure pattern analysis<br>• Recovery time tracking | • 12 TVFs (e.g., `get_failed_jobs`)<br>• 1 Metric View<br>• 50 Custom Metrics (success drift)<br>• 1 Monitor |
| **✅ Data Quality Agent** | Data Quality Monitor | • Data quality monitoring<br>• Lineage tracking<br>• Governance compliance<br>• Freshness monitoring | • 7 TVFs (e.g., `get_table_freshness`)<br>• 2 Metric Views<br>• 26 Custom Metrics (quality drift)<br>• 2 Monitors |
| **🤖 ML Ops Agent** | ML Intelligence | • Experiment tracking<br>• Model performance monitoring<br>• Serving endpoint health<br>• Model drift detection | • Integrated across spaces<br>• Access to MLflow tables<br>• Endpoint usage data |
| **🌐 Orchestrator Agent** | Unified Health Monitor | • Intent classification<br>• Multi-agent coordination<br>• Cross-domain queries<br>• Response synthesis | • All 60 TVFs<br>• All 10 Metric Views<br>• All 210+ Custom Metrics<br>• All 8 Monitors |

### Mandatory 7-Section Structure

**Each Genie Space configuration document contains:**

| Section | Content | Purpose for Agents | Status |
|---------|---------|-------------------|--------|
| **A. Space Name** | Exact Genie Space name | Agent identifies its query interface | ✅ |
| **B. Space Description** | 2-3 sentence purpose | Agent understands domain scope | ✅ |
| **C. Sample Questions** | 10-15 user-facing questions | Agent learns query patterns | ✅ |
| **D. Data Assets** | All tables, metric views, TVFs, monitoring tables | Agent discovers available tools | ✅ |
| **E. General Instructions** | ≤20 lines LLM rules + **Asset Selection Rules** | Agent behavior + tool selection | ✅ |
| **F. TVFs** | All functions with signatures | Agent function call specs | ✅ |
| **G. Benchmark Questions** | 10-15 with EXACT SQL | Agent validation & testing | ✅ |

---

## Asset Selection Framework

### Quick Decision Tree for Genie

This decision tree should be included in each Genie Space's General Instructions (Section E):

```
USER QUERY                                          → USE THIS
─────────────────────────────────────────────────────────────────
"What's the current X?"                             → Metric View
"Show me total X by Y"                              → Metric View
"Dashboard of X"                                    → Metric View
─────────────────────────────────────────────────────────────────
"Is X increasing/decreasing over time?"             → Custom Metrics (_drift_metrics)
"How has X changed since last week?"                → Custom Metrics (_drift_metrics)
"Alert me when X exceeds threshold"                 → Custom Metrics (for alerting)
─────────────────────────────────────────────────────────────────
"Which specific items have X?"                      → TVF
"List the top N items with X"                       → TVF
"Show me items from DATE to DATE with X"            → TVF
"What failed/what's slow/what's stale?"             → TVF
─────────────────────────────────────────────────────────────────
```

### Asset Selection by Query Type

#### Current State Queries → **Metric Views**

| Example Query | Metric View | Measure |
|---------------|-------------|---------|
| "What's the current job success rate?" | `mv_job_performance` | `success_rate` |
| "Total cost this month" | `mv_cost_analytics` | `mtd_cost` |
| "Query latency P95" | `mv_query_performance` | `p95_duration_seconds` |
| "How much cost is untagged?" | `mv_cost_analytics` | `tag_coverage_pct` |

#### Trend/Drift Queries → **Custom Metrics (Lakehouse Monitoring)**

| Example Query | Table | Metric |
|---------------|-------|--------|
| "Is success rate degrading?" | `fact_job_run_timeline_drift_metrics` | `success_rate_drift` |
| "Is cost increasing vs last period?" | `fact_usage_drift_metrics` | `cost_drift_pct` |
| "Query latency trend" | `fact_query_history_profile_metrics` | `p95_duration_seconds` over time |
| "Tag coverage trend" | `fact_usage_profile_metrics` | `tag_coverage_pct` over time |

#### Investigation Queries → **TVFs**

| Example Query | TVF | Key Parameters |
|---------------|-----|----------------|
| "Which jobs failed this week?" | `get_failed_jobs_summary` | `days_back=7` |
| "Top 10 cost drivers" | `get_top_cost_contributors` | `top_n=10` |
| "Queries over 30 seconds" | `get_slow_queries` | `duration_threshold_sec=30` |
| "Stale tables" | `get_stale_tables` | `staleness_threshold_days=7` |
| "User risk scores" | `get_user_risk_scores` | `days_back=30` |

---

## Custom Metrics Query Patterns (Critical for Genie)

Lakehouse Monitoring output tables (`_profile_metrics`, `_drift_metrics`) have **special query patterns** that Genie must follow to return correct results. Without proper filters, queries will return incorrect or incomplete data.

> **Reference:** See [05-genie-integration.md](../lakehouse-monitoring-design/05-genie-integration.md) for complete documentation.

### Profile Metrics Query Pattern

The `_profile_metrics` tables contain time-series custom metrics. To query correctly:

```sql
-- ✅ CORRECT: Get table-level business KPIs
SELECT 
  window.start AS window_start,
  window.end AS window_end,
  total_daily_cost,
  tag_coverage_pct,
  serverless_ratio
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'     -- CRITICAL: Filters to custom metrics (not per-column stats)
  AND log_type = 'INPUT'         -- CRITICAL: Input data statistics
  AND slice_key IS NULL          -- Optional: No slicing (overall metrics)
  AND window.start >= '2024-01-01'
ORDER BY window.start DESC
```

### Key Filter Columns Explained

| Column | Purpose | Required Values | When to Use |
|--------|---------|-----------------|-------------|
| `column_name` | Filters table-level vs column-level stats | `':table'` for custom metrics | **ALWAYS** for custom KPIs |
| `log_type` | Input vs output statistics | `'INPUT'` for source data | **ALWAYS** for monitoring queries |
| `slice_key` | Dimension for sliced analysis | `NULL` for overall, or `'workspace_id'`, etc. | Optional |
| `slice_value` | Value of the slicing dimension | Depends on slice_key | When slice_key is set |
| `window.start` | Time window start | TIMESTAMP | For time filtering |
| `window.end` | Time window end | TIMESTAMP | For time filtering |

### Slicing Dimensions by Monitor

Each monitor supports different slicing dimensions for dimensional analysis:

| Monitor | Profile Table | Available Slicing Dimensions | Use Cases |
|---------|---------------|------------------------------|-----------|
| **Cost** | `fact_usage_profile_metrics` | `workspace_id`, `sku_name`, `cloud`, `is_tagged`, `product_features_is_serverless` | Cost by workspace, SKU breakdown, serverless vs classic, tagged vs untagged |
| **Job** | `fact_job_run_timeline_profile_metrics` | `workspace_id`, `result_state`, `trigger_type`, `job_name`, `termination_code` | Success by job name, failures by termination code, scheduled vs manual |
| **Query** | `fact_query_history_profile_metrics` | `workspace_id`, `compute_warehouse_id`, `execution_status`, `statement_type`, `executed_by` | Performance by warehouse, queries by user, status breakdown |
| **Cluster** | `fact_node_timeline_profile_metrics` | `workspace_id`, `cluster_id`, `node_type`, `cluster_name`, `driver` | Utilization by cluster, driver vs worker analysis |
| **Security** | `fact_audit_logs_profile_metrics` | `workspace_id`, `service_name`, `audit_level`, `action_name`, `user_identity_email` | Events by service, actions by user, audit level breakdown |
| **Quality** | `fact_table_quality_profile_metrics` | `catalog_name`, `schema_name`, `table_name`, `has_critical_violations` | Quality by schema/table, critical violations filtering |
| **Governance** | `fact_governance_metrics_profile_metrics` | `workspace_id`, `entity_type`, `created_by`, `source_catalog_name` | Coverage by entity type, ownership analysis |
| **Inference** | `fact_cost_anomaly_predictions_profile_metrics` | `workspace_id`, `is_anomaly`, `anomaly_category` | Anomaly distribution, category breakdown |

### Slicing Query Patterns

#### Overall Metrics (No Slicing)

```sql
-- Pattern: Get overall (non-sliced) metrics
SELECT 
  window.start AS window_start,
  total_daily_cost,
  tag_coverage_pct
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL           -- No slicing = overall metrics
ORDER BY window.start DESC
```

#### Dimensional Analysis (With Slicing)

```sql
-- Pattern: Get cost breakdown by workspace
SELECT 
  slice_value AS workspace_id,
  SUM(total_daily_cost) AS total_cost,
  AVG(tag_coverage_pct) AS avg_tag_coverage
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'workspace_id'  -- Slice by workspace
  AND window.start >= DATEADD(day, -30, CURRENT_DATE())
GROUP BY slice_value
ORDER BY total_cost DESC
```

```sql
-- Pattern: Get cost breakdown by SKU
SELECT 
  slice_value AS sku_name,
  SUM(total_daily_cost) AS total_cost
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'sku_name'      -- Slice by SKU
ORDER BY total_cost DESC
```

### Drift Metrics Query Pattern

The `_drift_metrics` tables contain period-over-period comparisons:

```sql
-- Pattern: Get cost drift over time
SELECT 
  window.start AS window_start,
  cost_drift_pct,
  dbu_drift_pct,
  tag_coverage_drift
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'  -- CRITICAL: Compare consecutive periods
  AND column_name = ':table'       -- CRITICAL: Table-level drift
  AND slice_key IS NULL            -- Optional: Overall drift
ORDER BY window.start DESC
```

### Example: Serverless vs Classic Cost Comparison

```sql
-- Question: "Compare serverless vs classic compute cost"
SELECT 
  CASE 
    WHEN slice_value = 'true' THEN 'Serverless'
    ELSE 'Classic'
  END AS compute_type,
  SUM(total_daily_cost) AS total_cost,
  COUNT(*) AS days
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'product_features_is_serverless'
GROUP BY slice_value
```

### Example: Jobs with Lowest Success Rate

```sql
-- Question: "Which jobs have lowest success rate?"
SELECT 
  slice_value AS job_name,
  AVG(success_rate) AS avg_success_rate,
  SUM(failure_count) AS total_failures
FROM catalog.gold_monitoring.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'job_name'
  AND window.start >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY slice_value
HAVING AVG(success_rate) < 95
ORDER BY avg_success_rate ASC
```

### Safe Handling of NULL Slice Values

When slice columns are NULL (overall metrics), use COALESCE pattern:

```sql
-- Pattern: Safe handling for dashboard queries
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND COALESCE(slice_key, 'No Slice') = COALESCE(:requested_slice, 'No Slice')
  AND COALESCE(slice_value, 'No Slice') = COALESCE(:requested_value, 'No Slice')
```

### Genie Natural Language → Query Mapping

| User Question | Required Filters | Expected Query |
|---------------|------------------|----------------|
| "What's the total cost this month?" | `column_name=':table'`, `log_type='INPUT'`, `slice_key IS NULL` | SUM over window in profile_metrics |
| "Show cost breakdown by workspace" | `slice_key='workspace_id'` | GROUP BY slice_value |
| "Is cost increasing vs last period?" | `drift_type='CONSECUTIVE'` in drift_metrics | Query drift_pct columns |
| "Compare serverless vs classic cost" | `slice_key='product_features_is_serverless'` | GROUP BY slice_value |
| "Which job failed most?" | `slice_key='job_name'`, filter failure_count | ORDER BY failures DESC |

---

### Genie Space Asset Selection Rules

**Include this in every Genie Space's General Instructions (Section E):**

```markdown
## Asset Selection Rules

When answering user queries, select the appropriate asset type:

### Use Metric Views (mv_*) when:
- User wants current state aggregates
- Query is for dashboard-style KPIs
- No specific date range or entity filter needed
- Examples: "total cost", "success rate", "query latency"

### Use Custom Metrics (*_profile_metrics, *_drift_metrics) when:
- User asks about trends over time
- User asks if something is increasing/decreasing
- Query involves period comparison (vs baseline)
- Examples: "is X degrading?", "X trend", "X over time"

### Use TVFs (get_*) when:
- User wants a specific list of items
- Query includes "top N", "which", "list"
- User specifies date range or threshold
- User needs actionable investigation results
- Examples: "which jobs failed?", "top 10 cost drivers", "slow queries"

### Priority Order:
1. If user asks for a LIST → TVF
2. If user asks about TREND → Custom Metrics
3. If user asks for CURRENT VALUE → Metric View
```

### Common Confusion Scenarios (Prevent in Instructions)

| Scenario | User Query | Wrong Choice | Correct Choice | Why |
|----------|-----------|--------------|----------------|-----|
| 1 | "What's the success rate?" | TVF `get_job_success_rates` | Metric View `mv_job_performance` | User wants current aggregate, not parameterized list |
| 2 | "Is cost going up?" | Metric View `mv_cost_analytics` | Custom Metrics `fact_usage_drift_metrics` | User wants trend comparison, not current value |
| 3 | "Which jobs failed yesterday?" | Custom Metrics | TVF `get_failed_jobs_summary(1, 1)` | User wants specific list, not aggregate |
| 4 | "Show me cost by workspace" | TVF | Metric View grouped by `workspace_name` | Dashboard-style aggregate with dimension |

### Overlap Guidance by Domain

#### 💰 Cost Domain

| Measurement Concept | Custom Metric | Metric View | TVF | **Primary Owner** |
|---------------------|---------------|-------------|-----|-------------------|
| Total daily cost | `total_daily_cost` | `total_cost` | `get_daily_cost_summary` | **Metric View** (dashboard) |
| Cost by SKU | SKU-specific totals | By dimension | `get_cost_trend_by_sku` | **TVF** (drill-down) |
| Tag coverage % | `tag_coverage_pct` | `tag_coverage_pct` | — | **Custom Metric** (drift tracking) |
| Cost anomalies | `cost_drift_pct` | — | `get_cost_anomalies` | **Custom Metric** (automated) + **TVF** (investigation) |

#### 🔄 Reliability Domain

| Measurement Concept | Custom Metric | Metric View | TVF | **Primary Owner** |
|---------------------|---------------|-------------|-----|-------------------|
| Success rate | `success_rate` | `success_rate` | `get_job_success_rates` | **Metric View** (current) + **CM** (trend) |
| Failure count | `failure_count` | `total_failures` | `get_failed_jobs_summary` | **TVF** (action list) |
| Duration P95 | `p95_duration_minutes` | `p95_duration_minutes` | `get_job_duration_percentiles` | **Custom Metric** (trend) |

#### ⚡ Performance Domain

| Measurement Concept | Custom Metric | Metric View | TVF | **Primary Owner** |
|---------------------|---------------|-------------|-----|-------------------|
| Query latency P95 | `p95_duration_seconds` | `p95_duration_seconds` | `get_query_latency_percentiles` | **Metric View** (dashboard) |
| Slow query list | — | — | `get_slow_queries` | **TVF** (action list) |
| Cluster CPU | `avg_cpu_pct` | `avg_cpu_utilization` | `get_cluster_utilization` | **Custom Metric** (trend) |

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
4. **CRITICAL:** Include the Asset Selection Rules section
5. Click **Save**

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

3. **Monitoring Tables** (DRIFT - add third)
   - Click **Add Trusted Asset** → **Table**
   - Select `_profile_metrics` and `_drift_metrics` tables
   - Example: `fact_usage_profile_metrics`, `fact_usage_drift_metrics`, etc.

4. **Gold Tables** (REFERENCE - add last, sparingly)
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
4. **Verify correct asset type** was selected (Metric View vs TVF vs Custom Metrics)
5. **Validate results** match expected format
6. **Measure query time** (target: <10 seconds)

#### Level 2: Asset Selection Testing (NEW)

Test that Genie selects the correct asset type based on query intent:

**Asset Selection Tests:**

| Test | Query | Expected Asset | Expected SQL Pattern |
|------|-------|----------------|---------------------|
| Current State | "What's the success rate?" | Metric View | `SELECT MEASURE(success_rate) FROM mv_job_performance` |
| Trend/Drift | "Is success rate degrading?" | Custom Metrics | `SELECT * FROM fact_job_run_timeline_drift_metrics` |
| Investigation | "Which jobs failed yesterday?" | TVF | `SELECT * FROM get_failed_jobs_summary(1, 1)` |
| Dimension Grouping | "Cost by workspace" | Metric View | `SELECT ... FROM mv_cost_analytics GROUP BY workspace_name` |

#### Level 2a: Custom Metrics Query Pattern Testing (NEW)

Test that Genie correctly applies required filters when querying Lakehouse Monitoring tables:

**Custom Metrics Filter Tests:**

| Test | Query | Expected Filters | Pass Criteria |
|------|-------|------------------|---------------|
| Overall Metrics | "What's the total cost trend?" | `column_name=':table'`, `log_type='INPUT'`, `slice_key IS NULL` | Returns non-empty results |
| Sliced Metrics | "Show cost by workspace" | `slice_key='workspace_id'`, `GROUP BY slice_value` | Results grouped by workspace |
| Drift Query | "Is cost increasing?" | `drift_type='CONSECUTIVE'`, `column_name=':table'` | Returns drift_pct values |
| Complex Slice | "Compare serverless vs classic" | `slice_key='product_features_is_serverless'` | Two rows: Serverless/Classic |

**Test SQL for Validation:**

```sql
-- Test 1: Verify overall metrics query
SELECT COUNT(*) as row_count
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table' AND log_type = 'INPUT' AND slice_key IS NULL;
-- Expected: > 0 rows

-- Test 2: Verify sliced metrics query
SELECT COUNT(DISTINCT slice_value) as workspace_count
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table' AND log_type = 'INPUT' AND slice_key = 'workspace_id';
-- Expected: > 0 distinct workspaces

-- Test 3: Verify drift metrics query
SELECT COUNT(*) as drift_rows
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table';
-- Expected: > 0 rows with drift values
```

#### Level 3: Agent Integration Testing (Phase 4)

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

### Coverage Testing

Ensure benchmark questions cover:

- [ ] All metric views (at least 3 questions each)
- [ ] All TVFs (at least 1 question each)
- [ ] All time periods (today, last week, month, quarter, YTD)
- [ ] All major dimensions (workspace, owner, SKU, etc.)
- [ ] Key calculations (growth %, rates, rankings)
- [ ] Custom metrics and drift detection
- [ ] **Asset type selection** (Metric View vs TVF vs Custom Metrics)

### Accuracy Targets

| Question Type | Target Accuracy |
|---------------|-----------------|
| Basic (COUNT, SUM, AVG) | 95% |
| Filtered (time, dimension) | 90% |
| Comparative (trends, growth) | 85% |
| Trend/Drift (Custom Metrics) | 85% |
| Complex (multi-step) | 75% |
| **Asset Selection** | 90% |

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
    expected_monitoring_tables = 2  # profile + drift
    
    actual_tvfs = sum(1 for a in assets if a.type == 'FUNCTION')
    actual_mvs = sum(1 for a in assets if a.type == 'METRIC_VIEW')
    actual_monitoring = sum(1 for a in assets if '_metrics' in a.name)
    
    print(f"TVFs: {actual_tvfs}/{expected_tvfs}")
    print(f"Metric Views: {actual_mvs}/{expected_mvs}")
    print(f"Monitoring Tables: {actual_monitoring}/{expected_monitoring_tables}")
    
    return (actual_tvfs >= expected_tvfs and 
            actual_mvs >= expected_mvs and 
            actual_monitoring >= expected_monitoring_tables)

# Test for each Genie Space
spaces = [
    ("Cost Intelligence", 15, 2, 2),
    ("Job Health Monitor", 12, 1, 2),
    ("Performance Analyzer", 16, 3, 4),
    ("Security Auditor", 10, 2, 2),
    ("Data Quality Monitor", 7, 2, 4)
]

all_valid = True
for space_name, tvfs, mvs, monitoring in spaces:
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

### Current State (Uses Metric Views)
- "What is the current success rate?"
- "Show me total cost this month"

### Trends (Uses Custom Metrics)
- "Is success rate degrading over time?"
- "How has cost changed since last week?"

### Investigation (Uses TVFs)
- "Which jobs failed yesterday?"
- "Top 10 cost drivers this week"

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

### Step 3: Monitor Adoption

Track KPIs in first 30 days:

| Metric | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|--------|--------|--------|--------|
| Active Users | ___ | ___ | ___ | ___ |
| Questions Asked | ___ | ___ | ___ | ___ |
| Success Rate % | ___ | ___ | ___ | ___ |
| Avg Response Time (sec) | ___ | ___ | ___ | ___ |
| **Asset Selection Accuracy %** | ___ | ___ | ___ | ___ |

---

## Troubleshooting

### Common Issues

#### Issue 1: Genie Uses Wrong Asset Type

**Symptoms:** Query works but returns wrong type of data (e.g., aggregate when user wanted list)

**Root Cause:** Asset Selection Rules not included or contradictory in General Instructions

**Fix:**
1. Review General Instructions (Section E)
2. **Add explicit Asset Selection Rules section:**
```markdown
## Asset Selection Rules
1. If user asks for a LIST → Use TVF
2. If user asks about TREND → Use Custom Metrics (_drift_metrics)
3. If user asks for CURRENT VALUE → Use Metric View
```
3. Add explicit routing for confusing cases:
```markdown
⚠️ CRITICAL - Routing:
- "What's the success rate?" → Metric View (current state)
- "Is success rate degrading?" → Custom Metrics (trend)
- "Which jobs failed?" → TVF (investigation)
```

#### Issue 2: Genie Queries Fact Tables Instead of Metric Views

**Symptoms:** Slow queries (>10 sec), Genie queries `fact_*` tables directly

**Root Cause:** Missing guidance on Metric View priority

**Fix:** Add to General Instructions:
```markdown
## Query Priority
1. ALWAYS prefer Metric Views for aggregate queries
2. NEVER query fact tables directly for KPIs
3. Use fact tables ONLY when specific filters not available in Metric Views
```

#### Issue 3: Genie Doesn't Use Custom Metrics for Drift

**Symptoms:** User asks "Is X increasing?" but Genie queries Metric View

**Root Cause:** Custom metrics tables not added as trusted assets, or missing routing rule

**Fix:**
1. Add `_profile_metrics` and `_drift_metrics` tables as trusted assets
2. Add explicit routing rule:
```markdown
## Trend/Drift Queries
For "Is X increasing/decreasing?", "X trend", "X over time":
→ Query _drift_metrics table for drift percentage
→ Query _profile_metrics table for time series
```

#### Issue 3a: Custom Metrics Query Returns Wrong/Empty Data

**Symptoms:** Query to `_profile_metrics` returns NULL values, incorrect data, or empty results

**Root Cause:** Missing required filter columns

**Fix:** Ensure ALL required filters are present:
```sql
-- ❌ WRONG: Missing filters
SELECT total_daily_cost FROM fact_usage_profile_metrics;

-- ✅ CORRECT: All required filters present
SELECT total_daily_cost 
FROM fact_usage_profile_metrics
WHERE column_name = ':table'     -- REQUIRED: Table-level metrics
  AND log_type = 'INPUT'         -- REQUIRED: Input statistics
  AND slice_key IS NULL;         -- For overall metrics
```

Add to General Instructions:
```markdown
## Custom Metrics Query Rules
ALWAYS include these filters when querying _profile_metrics or _drift_metrics:
- `column_name = ':table'` — required for custom business KPIs
- `log_type = 'INPUT'` — required for monitoring queries
- `slice_key IS NULL` — for overall metrics (or specific slice_key for dimensional analysis)
```

#### Issue 3b: Sliced Custom Metrics Not Working

**Symptoms:** User asks "cost by workspace" but Genie doesn't use slice_key

**Root Cause:** Missing slicing pattern in instructions

**Fix:** Add slicing guidance to General Instructions:
```markdown
## Custom Metrics Slicing
For "X by Y" questions (e.g., "cost by workspace"):
→ Use slice_key filter: `slice_key = 'workspace_id'`
→ Group by slice_value: `GROUP BY slice_value`

Available slice dimensions:
- Cost: workspace_id, sku_name, cloud, is_tagged, product_features_is_serverless
- Job: workspace_id, job_name, result_state, trigger_type, termination_code
- Query: workspace_id, compute_warehouse_id, execution_status, statement_type
```

#### Issue 3c: Drift Metrics Query Returns Wrong Data

**Symptoms:** Drift query returns unexpected results or errors

**Root Cause:** Missing `drift_type` filter

**Fix:** 
```sql
-- ❌ WRONG: Missing drift_type
SELECT cost_drift_pct FROM fact_usage_drift_metrics;

-- ✅ CORRECT: Include drift_type
SELECT cost_drift_pct 
FROM fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'  -- REQUIRED for drift metrics
  AND column_name = ':table';      -- REQUIRED for table-level drift
```

#### Issue 4: MEASURE() Syntax Error

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

#### Issue 5: TVF Returns Empty Results

**Symptoms:** TVF query succeeds but returns 0 rows

**Root Cause:** Date parameters outside data range

**Fix:**
```sql
-- Use wide date range for all data
SELECT * FROM get_cost_trend_by_sku('1900-01-01', '2100-12-31', 'JOBS_COMPUTE');
```

#### Issue 6: Query Timeout

**Symptoms:** Query exceeds 10 second target

**Root Cause:** Querying fact tables directly instead of metric views

**Fix:**
1. Review General Instructions routing
2. Ensure Genie uses metric views (pre-aggregated)
3. Add rule: "NEVER query fact tables directly - use metric views"

#### Issue 7: Genie Wraps TVF with TABLE()

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

**Asset Selection:**
- [ ] Check General Instructions for Asset Selection Rules
- [ ] Verify correct asset type used (Metric View vs TVF vs Custom Metrics)
- [ ] Check if _profile_metrics and _drift_metrics tables are trusted assets

**Metric Views:**
- [ ] Check column names in MEASURE() (use `name`, not `display_name`)
- [ ] Confirm full 3-part namespace used (`catalog.schema.object`)

**TVFs:**
- [ ] Validate TVF parameters match signature
- [ ] Check if date parameters are within data range

**Custom Metrics (Critical Filters):**
- [ ] Verify `column_name = ':table'` filter is present
- [ ] Verify `log_type = 'INPUT'` filter is present
- [ ] For overall metrics: `slice_key IS NULL`
- [ ] For dimensional analysis: correct `slice_key` value (e.g., `'workspace_id'`)
- [ ] For drift queries: `drift_type = 'CONSECUTIVE'`

**General:**
- [ ] Test SQL manually in SQL Editor
- [ ] Review Genie query history for patterns
- [ ] Check user permissions on all assets

---

## Maintenance

### Weekly Tasks

- [ ] Review Genie query history
- [ ] Identify failed queries (< 90% success rate)
- [ ] **Review asset selection accuracy** (correct asset type used)
- [ ] Update General Instructions with clarifications
- [ ] Add new example questions based on usage

### Monthly Tasks

- [ ] Analyze most frequently asked questions
- [ ] Update Space instructions with new patterns
- [ ] Add new synonyms to metric views/TVFs
- [ ] Review performance (query time, success rate)
- [ ] **Review asset selection patterns** - update routing rules if needed
- [ ] User feedback session

### Quarterly Tasks

- [ ] Comprehensive usage report (adoption, satisfaction)
- [ ] Training session for new team members
- [ ] Review and update all benchmark questions
- [ ] Optimize slow-performing queries
- [ ] Add new business questions as use cases evolve
- [ ] Update data assets with new TVFs/metric views
- [ ] **Update Metrics Inventory document** with new measurements

### Annual Review

- [ ] Full Genie Space audit
- [ ] User satisfaction survey
- [ ] ROI analysis (time saved, decisions made faster)
- [ ] Strategic roadmap for next year
- [ ] **Semantic layer rationalization review** - ensure components still aligned

---

## Success Criteria

### Phase 3.6: Genie Spaces (Immediate - First 30 Days)

**Standalone Genie Space Deployment:**

- [ ] All 7 Genie Spaces deployed
- [ ] All benchmark questions pass (>80% success rate)
- [ ] **Asset selection accuracy >90%** (correct asset type used)
- [ ] 10+ active users per space (human users testing)
- [ ] Average query time <10 seconds
- [ ] User satisfaction rating >4/5 (human feedback)

**Agent Integration Readiness:**

- [ ] Each Genie Space accessible via Databricks SDK
- [ ] All data assets (TVFs, MVs, Custom Metrics tables) registered as trusted assets
- [ ] General Instructions include Asset Selection Rules (≤20 lines)
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

### Monitor Summary (8 Lakehouse Monitors)

| Monitor | Gold Table | Domain | AGGREGATE | DERIVED | DRIFT | Slicing Dimensions |
|---------|------------|--------|-----------|---------|-------|-------------------|
| **Cost** | `fact_usage` | 💰 Cost | 19 | 13 | 3 | `workspace_id`, `sku_name`, `cloud`, `is_tagged`, `product_features_is_serverless` |
| **Job** | `fact_job_run_timeline` | 🔄 Reliability | 26 | 15 | 9 | `workspace_id`, `result_state`, `trigger_type`, `job_name`, `termination_code` |
| **Query** | `fact_query_history` | ⚡ Performance | 26 | 13 | 7 | `workspace_id`, `compute_warehouse_id`, `execution_status`, `statement_type`, `executed_by` |
| **Cluster** | `fact_node_timeline` | ⚡ Performance | ~30 | ~10 | ~6 | `workspace_id`, `cluster_id`, `node_type`, `cluster_name`, `driver` |
| **Security** | `fact_audit_logs` | 🔒 Security | ~8 | ~4 | ~1 | `workspace_id`, `service_name`, `audit_level`, `action_name`, `user_identity_email` |
| **Quality** | `fact_table_quality` | ✅ Quality | ~10 | ~5 | ~2 | `catalog_name`, `schema_name`, `table_name`, `has_critical_violations` |
| **Governance** | `fact_governance_metrics` | 📋 Quality | ~8 | ~5 | ~2 | `workspace_id`, `entity_type`, `created_by`, `source_catalog_name` |
| **Inference** | `fact_model_serving` | 🤖 ML | ~10 | ~4 | ~2 | `workspace_id`, `is_anomaly`, `anomaly_category` |

> **Reference:** See [Monitor Catalog](../lakehouse-monitoring-design/04-monitor-catalog.md) for complete metric definitions.

---

### 💰 Cost Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 15 | `get_top_cost_contributors`, `get_cost_anomalies`, `get_all_purpose_cluster_cost` |
| Metric Views | 2 | `cost_analytics`, `commit_tracking` |
| Custom Metrics | 35 | `total_daily_cost`, `tag_coverage_pct`, `cost_drift_pct`, `serverless_ratio` |
| Monitors | 1 | Cost Monitor (`fact_usage_profile_metrics`, `fact_usage_drift_metrics`) |

### ⚡ Performance Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 16 | `get_slow_queries`, `get_cluster_utilization`, `get_query_efficiency_analysis` |
| Metric Views | 3 | `query_performance`, `cluster_utilization`, `cluster_efficiency` |
| Custom Metrics | 86 | `p95_duration_seconds`, `cache_hit_rate`, `efficiency_score`, `spill_rate_drift` |
| Monitors | 2 | Query Monitor + Cluster Monitor |

### 🔄 Reliability Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 12 | `get_failed_jobs`, `get_job_success_rate`, `get_job_repair_costs` |
| Metric Views | 1 | `job_performance` |
| Custom Metrics | 50 | `success_rate`, `failure_count`, `p95_duration_minutes`, `success_rate_drift` |
| Monitors | 1 | Job Monitor (`fact_job_run_timeline_profile_metrics`) |

### 🔒 Security Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 10 | `get_user_activity_summary`, `get_sensitive_table_access`, `get_off_hours_activity` |
| Metric Views | 2 | `security_events`, `governance_analytics` |
| Custom Metrics | 13 | `failed_auth_count`, `admin_actions`, `auth_failure_drift` |
| Monitors | 1 | Security Monitor (`fact_audit_logs_profile_metrics`) |

### ✅ Quality Agent
| Asset Type | Count | Examples |
|------------|-------|----------|
| TVFs | 7 | `get_table_freshness`, `get_data_quality_summary`, `get_pipeline_data_lineage` |
| Metric Views | 2 | `data_quality`, `ml_intelligence` |
| Custom Metrics | 26 | `freshness_rate`, `tables_with_issues`, `governance_score`, `quality_drift` |
| Monitors | 2 | Quality Monitor + Governance Monitor |

---

## References

### Semantic Layer Documentation
- [Metrics Inventory](../reference/metrics-inventory.md) - **Complete list of all 277 measurements**
- [Semantic Layer Rationalization](../reference/semantic-layer-rationalization.md) - Analysis of component alignment
- [Genie Asset Selection Guide](../reference/genie-asset-selection-guide.md) - Decision tree for Genie

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
- [TVF Documentation](../../docs/semantic-framework/) - 60 TVFs (Agent Tools)
- [Metric Views Documentation](../../docs/semantic-framework/20-metric-views-index.md) - 10 Metric Views (Agent Tools)
- [Genie Space Post-Mortem](../../docs/reference/genie-space-semantic-layer-postmortem.md) - Lessons learned

### Lakehouse Monitoring Documentation
- [Lakehouse Monitoring Index](../lakehouse-monitoring-design/00-index.md) - Overview of monitoring framework
- [Custom Metrics Reference](../lakehouse-monitoring-design/03-custom-metrics.md) - 210+ custom metrics definitions
- [Monitor Catalog](../lakehouse-monitoring-design/04-monitor-catalog.md) - **Complete inventory of 8 monitors with all metrics**
- [Genie Integration](../lakehouse-monitoring-design/05-genie-integration.md) - **Critical query patterns for Genie**

### Cursor Rules
- [16-genie-space-patterns.mdc](mdc:../../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc) - Mandatory 7-section structure
- [15-databricks-table-valued-functions.mdc](mdc:../../.cursor/rules/semantic-layer/15-databricks-table-valued-functions.mdc) - TVF patterns
- [14-metric-views-patterns.mdc](mdc:../../.cursor/rules/semantic-layer/14-metric-views-patterns.mdc) - Metric view patterns

---

## Appendix

### A. Deployment Checklist

**Pre-Deployment:**
- [ ] All Gold tables deployed (38 tables)
- [ ] All TVFs deployed (60 functions)
- [ ] All Metric Views deployed (10 views)
- [ ] All Lakehouse Monitors deployed (8 monitors + 210+ custom metrics)
- [ ] SQL Warehouse created and running
- [ ] Permissions granted to users

**Configuration:**
- [ ] Space Name defined (Section A)
- [ ] Space Description written (Section B)
- [ ] Sample Questions documented (Section C - 10-15)
- [ ] Data Assets listed (Section D) - **including monitoring tables**
- [ ] General Instructions written (Section E - ≤20 lines) - **with Asset Selection Rules**
- [ ] TVFs documented (Section F)
- [ ] Benchmark Questions with SQL (Section G - 10-15)

**Deployment:**
- [ ] Genie Space created in UI
- [ ] General Instructions added (with Asset Selection Rules)
- [ ] All metric views added as trusted assets
- [ ] All TVFs added as trusted assets
- [ ] **Monitoring tables added** (`_profile_metrics`, `_drift_metrics`)
- [ ] Permissions granted

**Testing:**
- [ ] All benchmark questions tested (>80% pass rate)
- [ ] **Asset selection accuracy tested** (>90%)
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

**Document Version:** 3.1  
**Last Updated:** January 1, 2026  
**Next Review:** April 1, 2026  

**Phase 3.6 Status:** ✅ Ready for Deployment  
**Phase 4 Status:** 📋 Ready to Start (after Genie Spaces deployed)

**Change Log:**
| Version | Date | Changes |
|---------|------|---------|
| 3.1 | Jan 1, 2026 | Added Custom Metrics Query Patterns section with critical filters (`column_name=':table'`, `log_type='INPUT'`), Slicing Dimensions by Monitor table, Drift Metrics patterns, enhanced troubleshooting for custom metrics, Monitor Summary table, custom metrics testing patterns |
| 3.0 | Jan 1, 2026 | Added Semantic Layer Architecture section, Asset Selection Framework, updated counts to include Custom Metrics (210+), added Metrics Inventory reference |
| 2.0 | Dec 30, 2025 | Added Agent Framework integration, Phase 4 roadmap |
| 1.0 | Dec 15, 2025 | Initial deployment guide |
