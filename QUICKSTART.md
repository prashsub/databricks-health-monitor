# Databricks Health Monitor - Quick Start

**⚡ Get started in 5 minutes**

---

## 🚀 One-Time Setup

```bash
# 1. Navigate to project
cd /path/to/DatabricksHealthMonitor

# 2. Validate configuration
databricks bundle validate

# 3. Deploy infrastructure
databricks bundle deploy -t dev

# 4. Run complete setup (Bronze + Gold)
databricks bundle run -t dev master_setup_orchestrator
```

**Expected Duration:** 30-40 minutes  
**Creates:** 35 Bronze + 38 Gold tables with data

---

## 🔄 Daily Data Refresh

```bash
# Run complete pipeline (Bronze ingestion → Gold transformation)
databricks bundle run -t dev master_refresh_orchestrator
```

**Expected Duration:** 45-60 minutes  
**Updates:** All 73 tables with latest data

---

## ✅ Quick Validation

```sql
-- Verify table counts (run in Databricks SQL Warehouse)
SELECT 
  'Bronze' as layer, COUNT(*) as tables, 35 as expected
FROM system.information_schema.tables
WHERE table_schema LIKE '%system_bronze'
UNION ALL
SELECT 
  'Gold', COUNT(*), 38
FROM system.information_schema.tables
WHERE table_schema LIKE '%system_gold';

-- Check Gold data freshness
SELECT 
  'dim_workspace' as table_name,
  COUNT(*) as rows,
  MAX(record_updated_timestamp) as last_updated
FROM system_gold.dim_workspace
UNION ALL
SELECT 'fact_job_run', COUNT(*), MAX(record_updated_timestamp)
FROM system_gold.fact_job_run;
```

---

## 📅 Enable Automatic Scheduling

1. Go to **Databricks Workflows**
2. Find `[dev] Master Refresh Orchestrator`
3. Click **Schedule** → **Resume**
4. Default: Daily at 2 AM UTC

---

## 📚 Full Documentation

- [Master Orchestrator Guide](docs/deployment/MASTER_ORCHESTRATOR_GUIDE.md) - Complete setup
- [Implementation Summary](docs/gold/FINAL_IMPLEMENTATION_SUMMARY.md) - Architecture
- [Troubleshooting](docs/deployment/MASTER_ORCHESTRATOR_GUIDE.md#troubleshooting) - Common issues

---

## 🎯 What You Get

### Bronze Layer (35 Tables)
- System tables ingestion via DLT
- Streaming + non-streaming tables
- Full Unity Catalog governance

### Gold Layer (38 Tables)
- **23 Dimensions** (workspaces, clusters, jobs, users, etc.)
- **15 Facts** (job runs, costs, utilization, security events, etc.)
- Star schema with 85 PK/FK relationships
- SCD Type 2 historical tracking

### Business Capabilities
- FinOps: Cost attribution, optimization, chargeback
- Performance: Job baselines, anomaly detection
- Governance: Lineage, table health, data quality
- MLOps: Training, serving, model metrics
- Security: Audit, access patterns, compliance
- Sharing: Usage metrics, recipient activity

---

**Ready to deploy?** Run the setup command above and you'll have a complete platform observability solution in 40 minutes!
