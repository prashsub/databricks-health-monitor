# Databricks Health Monitor - Quick Start

**Complete deployment guide with step-by-step instructions**

---

## Prerequisites

Before deploying, ensure you have:

1. **Databricks CLI** installed and authenticated
   ```bash
   databricks auth login --host https://<your-workspace>.databricks.com
   ```

2. **Unity Catalog** enabled with permissions to create catalogs/schemas

3. **SQL Warehouse** running (serverless recommended)
   - Note the `warehouse_id` for configuration

4. **Update `databricks.yml`** with your environment settings:
   - `catalog`: Your Unity Catalog name
   - `warehouse_id`: Your SQL Warehouse ID

---

## Deployment Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT SEQUENCE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌────────────────────────────────────────────────────┐ │
│  │ 1. DEPLOY    │    │ databricks bundle deploy -t dev                    │ │
│  │ (One-time)   │    │ Creates all jobs, pipelines, schemas               │ │
│  └──────┬───────┘    └────────────────────────────────────────────────────┘ │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐    ┌────────────────────────────────────────────────────┐ │
│  │ 2. SETUP     │    │ databricks bundle run -t dev master_setup_...      │ │
│  │ (One-time)   │    │ Bronze → Gold → Semantic → Monitoring → Alerting   │ │
│  └──────┬───────┘    └────────────────────────────────────────────────────┘ │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐    ┌────────────────────────────────────────────────────┐ │
│  │ 3. REFRESH   │    │ databricks bundle run -t dev master_refresh_...    │ │
│  │ (Daily)      │    │ Bronze Ingest → Gold Merge → ML Inference          │ │
│  └──────────────┘    └────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────┤
│  │                      OPTIONAL ADD-ONS                                    │
│  ├──────────────────────────────────────────────────────────────────────────┤
│  │ 4. ML TRAINING      │ ml_training_pipeline        │ Weekly (Sundays)    │
│  │ 5. DASHBOARDS       │ dashboard_deployment_job    │ On-demand           │
│  │ 6. GENIE SPACES     │ genie_spaces_deployment_job │ On-demand           │
│  │ 7. AGENT            │ agent_setup_job             │ On-demand           │
│  └──────────────────────────────────────────────────────────────────────────┘
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Deploy Infrastructure (One-Time)

Deploy all jobs, pipelines, and schemas to your Databricks workspace.

```bash
# Navigate to project directory
cd /path/to/DatabricksHealthMonitor

# Validate bundle configuration
databricks bundle validate

# Deploy all resources
databricks bundle deploy -t dev
```

**Expected Output:** ~50 jobs and pipelines created  
**Duration:** 1-2 minutes

---

## Phase 2: Initial Setup (One-Time)

Run the master setup orchestrator to create all tables and infrastructure.

```bash
databricks bundle run -t dev master_setup_orchestrator
```

### What Gets Created

| Phase | Job | What It Creates | Duration |
|-------|-----|-----------------|----------|
| 1 | Bronze Setup | 8 non-streaming tables + DQ rules | 5-10 min |
| 2 | Gold Setup | 39 domain tables + PK/FK constraints | 10-15 min |
| 3 | Semantic Layer | 60 TVFs + 10 Metric Views | 5-10 min |
| 4 | Monitoring | 8 Lakehouse Monitors (async) | 5 min |
| 5 | Wait | 20-minute pause for monitor table creation | 20 min |
| 6 | Documentation | Genie-friendly descriptions on monitor tables | 2 min |
| 7 | Alerting | 56 SQL Alerts (dry-run by default) | 5 min |
| 8 | ML Features | Empty feature tables (infrastructure) | 3 min |

**Total Duration:** 2-3 hours  
**Run:** Once per environment (dev, staging, prod)

### Setup Execution Flow

```
Bronze Setup
     │
     ▼
Gold Setup
     │
     ├───────────────┬───────────────┬───────────────┐
     ▼               ▼               ▼               ▼
Semantic Layer  Monitoring    Alerting Layer   ML Features
     │               │                              
     │               ▼                              
     │         Wait (20 min)                        
     │               │                              
     │               ▼                              
     │         Documentation                        
     └───────────────┴───────────────────────────────
```

---

## Phase 3: Data Refresh (Recurring)

After setup completes successfully, run the refresh pipeline to populate data.

```bash
databricks bundle run -t dev master_refresh_orchestrator
```

### What Gets Updated

| Phase | Job | What It Does | Duration |
|-------|-----|--------------|----------|
| 1 | Bronze Refresh | Ingest new data from system tables | 15-20 min |
| 2 | Gold Merge | Transform Bronze → Gold (incremental) | 20-30 min |
| 3 | Monitor Refresh | Refresh all Lakehouse Monitors | 10-15 min |
| 4 | ML Inference | Run batch predictions (25 models) | 15-20 min |

**Total Duration:** 1-2 hours  
**Schedule:** Daily at 2 AM UTC (PAUSED by default)

### Refresh Execution Flow

```
Bronze Refresh
     │
     ▼
Gold Merge
     │
     ├───────────────┐
     ▼               ▼
Monitoring      ML Inference
Refresh         (25 models)
```

---

## Phase 4: Optional Add-Ons

### 4a. ML Model Training (Weekly)

Trains all 25 ML models. Run manually first, then enable weekly schedule.

```bash
# First run: Manual (requires Gold data to exist)
databricks bundle run -t dev ml_training_pipeline
```

**Duration:** 2-3 hours  
**Schedule:** Weekly Sundays at 2 AM (PAUSED by default)  
**Prerequisite:** At least one successful refresh run

**ML Models by Domain:**
- 💰 Cost Agent: 6 models (anomaly detection, forecasting, optimization)
- 🔒 Security Agent: 4 models (threat detection, behavior baselines)
- ⚡ Performance Agent: 7 models (query optimization, capacity planning)
- 🔄 Reliability Agent: 5 models (failure prediction, SLA forecasting)
- 📊 Quality Agent: 3 models (drift detection, freshness prediction)

### 4b. Dashboard Deployment (On-Demand)

Deploys 6 AI/BI Lakeview dashboards.

```bash
databricks bundle run -t dev dashboard_deployment_job
```

**Duration:** 10-15 minutes  
**Prerequisite:** Gold layer setup complete

**Dashboards:**
- Cost Intelligence Dashboard
- Performance Dashboard
- Job Reliability Dashboard
- Security Audit Dashboard
- Data Quality Dashboard
- Unified Health Monitor Dashboard

### 4c. Genie Spaces Deployment (On-Demand)

Deploys 6 natural language query interfaces.

```bash
databricks bundle run -t dev genie_spaces_deployment_job
```

**Duration:** 5-10 minutes  
**Prerequisite:** Semantic layer (TVFs + Metric Views) deployed

**Genie Spaces:**
- 💰 Cost Intelligence Genie Space
- ⚡ Performance Genie Space
- 🔄 Job Health Monitor Genie Space
- 🔒 Security Auditor Genie Space
- 📊 Data Quality Monitor Genie Space
- 🏥 Unified Health Monitor Genie Space

### 4d. Agent Framework Setup (On-Demand)

Sets up the multi-agent orchestrator for AI-powered insights.

```bash
databricks bundle run -t dev agent_setup_job
```

**Duration:** 30 minutes  
**Prerequisite:** Genie Spaces deployed (for Genie tool integration)

---

## Phase 5: Enable Automated Schedules

After validating everything works, enable automated schedules.

### Option A: Via Databricks UI

1. Go to **Databricks Workflows**
2. Find the job you want to schedule
3. Click **Schedule** → **Resume**

### Option B: Via CLI

```bash
# Get job ID
databricks jobs list | grep "Master Refresh"

# Update schedule to UNPAUSED
databricks jobs update <job_id> --schedule '{"pause_status": "UNPAUSED"}'
```

### Recommended Schedule Configuration

| Job | Default Schedule | When to Enable |
|-----|-----------------|----------------|
| Master Refresh Orchestrator | Daily 2 AM UTC | After first manual refresh succeeds |
| ML Training Pipeline | Sundays 2 AM | After first manual training succeeds |

---

## Validation

### Quick Health Check

```sql
-- Run in Databricks SQL Warehouse

-- Check table counts by layer
SELECT 
  'Bronze' as layer, COUNT(*) as tables
FROM system.information_schema.tables
WHERE table_schema LIKE '%system_bronze'
UNION ALL
SELECT 
  'Gold', COUNT(*)
FROM system.information_schema.tables
WHERE table_schema LIKE '%system_gold';

-- Expected: Bronze ~35 tables, Gold ~38 tables
```

### Verify Data Freshness

```sql
-- Check Gold layer data freshness
SELECT 
  'dim_workspace' as table_name,
  COUNT(*) as rows,
  MAX(record_updated_timestamp) as last_updated
FROM system_gold.dim_workspace
UNION ALL
SELECT 'fact_job_run', COUNT(*), MAX(record_updated_timestamp)
FROM system_gold.fact_job_run;
```

### Check Job Status

```bash
# List recent job runs
databricks jobs list-runs --limit 10
```

---

## Troubleshooting

### Setup Job Fails

1. **Check prerequisites:**
   ```bash
   databricks bundle validate
   ```

2. **View job logs:**
   - Go to Databricks Workflows → Find failed job → View task logs

3. **Common issues:**
   - Missing permissions on Unity Catalog
   - SQL Warehouse not running
   - Incorrect `warehouse_id` in configuration

### Refresh Job Fails

1. **Ensure setup completed successfully first**
2. **Check Bronze data exists:**
   ```sql
   SELECT COUNT(*) FROM system_bronze.audit_log;
   ```

### Monitor Tables Not Created

Lakehouse Monitors create tables asynchronously (~15-20 minutes). The setup job includes a 20-minute wait, but you can verify:

```sql
SHOW TABLES IN system_gold LIKE '%_profile_metrics';
```

---

## Complete Deployment Commands

```bash
# === INITIAL DEPLOYMENT (One-time) ===
cd /path/to/DatabricksHealthMonitor
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle run -t dev master_setup_orchestrator  # 2-3 hours

# === FIRST DATA REFRESH (After setup) ===
databricks bundle run -t dev master_refresh_orchestrator  # 1-2 hours

# === OPTIONAL: ML Training (After refresh) ===
databricks bundle run -t dev ml_training_pipeline  # 2-3 hours

# === OPTIONAL: Dashboards ===
databricks bundle run -t dev dashboard_deployment_job

# === OPTIONAL: Genie Spaces ===
databricks bundle run -t dev genie_spaces_deployment_job

# === OPTIONAL: Agent Framework ===
databricks bundle run -t dev agent_setup_job

# === PRODUCTION: Enable schedules ===
# Via UI: Workflows → Job → Schedule → Resume
```

---

## What You Get

### Bronze Layer (35 Tables)
- System tables ingestion via DLT streaming
- Non-streaming tables for static data
- Full Unity Catalog governance

### Gold Layer (38 Tables)
- **23 Dimensions** (workspaces, clusters, jobs, users, etc.)
- **15 Facts** (job runs, costs, utilization, security events, etc.)
- Star schema with 85 PK/FK relationships
- SCD Type 2 historical tracking

### Semantic Layer
- **60 TVFs** (Table-Valued Functions) for Genie queries
- **10 Metric Views** for AI/BI dashboards

### Monitoring & Alerting
- **8 Lakehouse Monitors** with custom metrics
- **56 SQL Alerts** across 5 domains

### ML Models (25 Total)
- Cost optimization, security threat detection
- Performance forecasting, failure prediction
- Data quality drift detection

### Business Capabilities
- **FinOps:** Cost attribution, optimization, chargeback
- **Performance:** Job baselines, query optimization, anomaly detection
- **Governance:** Lineage, table health, data quality
- **MLOps:** Training tracking, serving metrics, model monitoring
- **Security:** Audit analysis, access patterns, compliance
- **Sharing:** Usage metrics, recipient activity

---

## Full Documentation

- [Master Orchestrator Guide](docs/deployment/MASTER_ORCHESTRATOR_GUIDE.md) - Detailed orchestrator documentation
- [Architecture Overview](docs/gold/FINAL_IMPLEMENTATION_SUMMARY.md) - Solution architecture
- [Troubleshooting Guide](docs/deployment/MASTER_ORCHESTRATOR_GUIDE.md#troubleshooting) - Common issues

---

**Ready to deploy?** Start with the commands in Phase 1 and work through each phase sequentially. Complete setup takes about 3-4 hours, after which you'll have a production-ready platform observability solution!
