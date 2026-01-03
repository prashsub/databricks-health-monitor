# Genie Space Deployment Prerequisites

**Date:** January 1, 2026  
**Issue:** Genie Space deployment failing due to missing prerequisite tables

---

## ✅ Fixed: Duplicate Job Removed

**Problem:** Two Genie Space deployment job files existed:
- `resources/semantic/genie_space_deployment_job.yml` (older, deleted)
- `resources/semantic/genie_spaces_deployment_job.yml` (current, kept)

**Resolution:** ✅ Deleted the duplicate older file.

---

## ❌ Current Issue: Missing Prerequisite Tables

### Error Summary

**Error Code:** `PERMISSION_DENIED` (misleading - actually means "tables don't exist")

**Root Cause:** Genie Spaces reference tables that **haven't been created yet**. Databricks validates all table references during Genie Space creation and fails if any table is missing.

---

## 📊 Missing Tables by Category

### Cost Intelligence Space - Missing 8 Tables

#### Lakehouse Monitoring Tables (2)
| Table | Type | Created By |
|-------|------|------------|
| `fact_usage_profile_metrics` | Monitoring output | Lakehouse Monitoring setup job |
| `fact_usage_drift_metrics` | Monitoring output | Lakehouse Monitoring setup job |

#### ML Prediction Tables (6)
| Table | ML Model | Created By |
|-------|----------|------------|
| `cost_anomaly_predictions` | cost_anomaly_detector | ML training pipeline |
| `cost_forecast_predictions` | budget_forecaster | ML training pipeline |
| `tag_recommendations` | tag_recommender | ML training pipeline |
| `user_cost_segments` | Clustering model | ML training pipeline |
| `migration_recommendations` | job_cost_optimizer | ML training pipeline |
| `budget_alert_predictions` | commitment_recommender | ML training pipeline |

---

### Job Health Monitor Space - Missing 7 Tables

#### Lakehouse Monitoring Tables (2)
| Table | Type | Created By |
|-------|------|------------|
| `fact_job_run_timeline_profile_metrics` | Monitoring output | Lakehouse Monitoring setup job |
| `fact_job_run_timeline_drift_metrics` | Monitoring output | Lakehouse Monitoring setup job |

#### ML Prediction Tables (5)
| Table | ML Model | Created By |
|-------|----------|------------|
| `job_failure_predictions` | job_failure_predictor | ML training pipeline |
| `retry_success_predictions` | retry_success_predictor | ML training pipeline |
| `pipeline_health_scores` | pipeline_health_scorer | ML training pipeline |
| `incident_impact_predictions` | sla_breach_predictor | ML training pipeline |
| `self_healing_recommendations` | Self-healing recommender | ML training pipeline |

---

## 🚀 Deployment Order (Correct Sequence)

### Phase 1: Core Data Layer ✅ (Likely Complete)
1. ✅ Bronze layer streaming ingestion
2. ✅ Silver layer DLT pipelines
3. ✅ Gold layer dimensional model
4. ✅ Semantic layer (TVFs, Metric Views)

### Phase 2: Monitoring & ML ⚠️ (Required Before Genie)
5. ⚠️ **Lakehouse Monitoring Setup** - Creates `*_profile_metrics` and `*_drift_metrics` tables
6. ⚠️ **ML Model Training** - Creates ML prediction tables

### Phase 3: Genie Spaces 🔴 (Currently Failing)
7. 🔴 **Genie Space Deployment** - Requires all tables from Phase 2 to exist

---

## ✅ Solution: Deploy Prerequisites First

### Option 1: Deploy Lakehouse Monitoring (Recommended First Step)

**Run the Lakehouse Monitoring setup job:**
```bash
databricks bundle run -t dev lakehouse_monitoring_setup_job --profile health_monitor
```

**This will create:**
- `fact_usage_profile_metrics`
- `fact_usage_drift_metrics`
- `fact_job_run_timeline_profile_metrics`
- `fact_job_run_timeline_drift_metrics`
- ... and all other monitoring tables

**Estimated Time:** 15-30 minutes (monitoring tables are created asynchronously)

---

### Option 2: Deploy ML Training Pipelines

**Run ML training jobs to create prediction tables:**

```bash
# Cost domain ML models (6 models)
databricks bundle run -t dev ml_cost_anomaly_detector --profile health_monitor
databricks bundle run -t dev ml_budget_forecaster --profile health_monitor
databricks bundle run -t dev ml_tag_recommender --profile health_monitor
databricks bundle run -t dev ml_user_cost_segments --profile health_monitor
databricks bundle run -t dev ml_migration_recommendations --profile health_monitor
databricks bundle run -t dev ml_budget_alert_predictions --profile health_monitor

# Reliability domain ML models (5 models)
databricks bundle run -t dev ml_job_failure_predictor --profile health_monitor
databricks bundle run -t dev ml_retry_success_predictor --profile health_monitor
databricks bundle run -t dev ml_pipeline_health_scorer --profile health_monitor
databricks bundle run -t dev ml_incident_impact_predictor --profile health_monitor
databricks bundle run -t dev ml_self_healing_recommender --profile health_monitor
```

**Estimated Time:** 2-4 hours (depending on data volume and model complexity)

---

### Option 3: Remove Optional Tables from Genie Spaces (Temporary Workaround)

If you want to deploy Genie Spaces **now** without waiting for ML/Monitoring:

**Edit the JSON export files to remove references to missing tables:**

1. **Edit `cost_intelligence_genie_export.json`:**
   - Remove ML prediction tables from `data_sources.tables`
   - Remove Lakehouse Monitoring tables from `data_sources.tables`
   - Keep only: Metric Views, TVFs, Gold tables (fact_usage, dim_sku, dim_workspace)

2. **Edit `job_health_monitor_genie_export.json`:**
   - Remove ML prediction tables from `data_sources.tables`
   - Remove Lakehouse Monitoring tables from `data_sources.tables`
   - Keep only: Metric Views, TVFs, Gold tables (fact_job_run_timeline, dim_job, dim_workspace)

3. **Redeploy Genie Spaces:**
   ```bash
   databricks bundle deploy -t dev --profile health_monitor
   databricks bundle run -t dev genie_spaces_deployment_job --profile health_monitor
   ```

4. **Later:** After ML/Monitoring tables are created, **update** the Genie Spaces to add them back.

---

## 📋 Verification Checklist

Before deploying Genie Spaces, verify these tables exist:

### Cost Intelligence Prerequisites
```sql
-- Check Lakehouse Monitoring tables
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold 
LIKE '*fact_usage*metrics';

-- Check ML prediction tables
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold 
LIKE '*cost*predictions';
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold 
LIKE '*tag_recommendations';
```

### Job Health Monitor Prerequisites
```sql
-- Check Lakehouse Monitoring tables
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold 
LIKE '*fact_job_run_timeline*metrics';

-- Check ML prediction tables
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold 
LIKE '*job*predictions';
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold 
LIKE '*pipeline_health_scores';
```

---

## 🔄 Recommended Workflow

### Immediate Actions (Deploy in Order)

1. **✅ Verify Gold Layer Complete**
   ```bash
   # Check if Gold tables exist
   databricks sql -e "SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold" --profile health_monitor
   ```

2. **⚠️ Deploy Lakehouse Monitoring (15-30 min)**
   ```bash
   databricks bundle run -t dev lakehouse_monitoring_setup_job --profile health_monitor
   
   # Wait ~15 minutes for async monitor creation
   # Then refresh monitors
   databricks bundle run -t dev lakehouse_monitoring_refresh_job --profile health_monitor
   ```

3. **⚠️ Deploy ML Pipelines (2-4 hours)**
   ```bash
   # Or use orchestrator if available
   databricks bundle run -t dev ml_layer_setup_job --profile health_monitor
   ```

4. **✅ Deploy Genie Spaces (1-2 min)**
   ```bash
   databricks bundle run -t dev genie_spaces_deployment_job --profile health_monitor
   ```

---

## 📚 Related Documentation

### Phase 3 Project Plan
- [Addendum 3.7: Lakehouse Monitoring](../../docs/project-plan/phase-3/addendum-3-7-lakehouse-monitoring.md)
- [Addendum 3.5: ML Models](../../docs/project-plan/phase-3/addendum-3-5-ml-models.md)
- [Addendum 3.6: Genie Spaces](../../docs/project-plan/phase-3/addendum-3-6-genie-spaces.md)

### Deployment Guides
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - List of all 25 ML models
- [Lakehouse Monitoring Design](../../docs/lakehouse-monitoring-design/) - Complete monitoring setup guide

### Cursor Rules
- [MLflow ML Models Patterns](../../.cursor/rules/ml/27-mlflow-mlmodels-patterns.mdc)
- [Lakehouse Monitoring Patterns](../../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

---

## ⚠️ Important Notes

1. **Misleading Error:** The API returns `PERMISSION_DENIED` but the real issue is **missing tables**, not permissions.

2. **Validation on Creation:** Databricks Genie validates **all** table references when creating a space. You cannot create a space with missing tables.

3. **Async Monitoring:** Lakehouse Monitoring tables are created **asynchronously**. After running the setup job, wait ~15 minutes before the `*_profile_metrics` and `*_drift_metrics` tables appear.

4. **ML Tables:** ML prediction tables are created by ML training pipelines. These must complete successfully before the tables exist.

5. **Deployment Order Matters:** Always deploy in this order:
   - Bronze → Silver → Gold → Semantic → Monitoring → ML → Genie

---

**Status:** ⚠️ **BLOCKED - Prerequisites Required**

**Next Action:** Deploy Lakehouse Monitoring and/or ML training pipelines before retrying Genie Space deployment.

