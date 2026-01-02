# Dashboard Rationalization Plan

## Executive Summary

This document outlines the strategy for consolidating **11 existing dashboards** into **5 domain-based dashboards** plus **1 unified executive dashboard**. The goal is to align dashboards with the 5 agent domains (Cost, Security, Performance, Reliability, Quality) while maximizing utilization of ML models, Lakehouse Monitors, and Metric Views.

---

## 1. Current State Analysis

### 1.1 Existing Dashboards

| Dashboard | Datasets | ML Datasets | Monitor Datasets | Domain Mapping |
|-----------|----------|-------------|------------------|----------------|
| cost_management.lvdash.json | 36 | 6 | 4 | **Cost** |
| commit_tracking.lvdash.json | 13 | 2 | 1 | **Cost** |
| security_audit.lvdash.json | 25 | 3 | 5 | **Security** |
| governance_hub.lvdash.json | 16 | 0 | 0 | Quality + Security |
| query_performance.lvdash.json | 23 | 3 | 5 | **Performance** |
| cluster_utilization.lvdash.json | 23 | 3 | 5 | **Performance** |
| dbr_migration.lvdash.json | 6 | 0 | 0 | **Performance** |
| job_reliability.lvdash.json | 31 | 6 | 7 | **Reliability** |
| job_optimization.lvdash.json | 7 | 0 | 0 | **Reliability** |
| table_health.lvdash.json | 7 | 0 | 0 | **Quality** |
| executive_overview.lvdash.json | 22 | 4 | 3 | Cross-domain |
| health_monitor_unified.lvdash.json | 83 | 0 | 1 | Cross-domain |

**Totals:**
- **Dashboards:** 12
- **Datasets:** 292
- **ML Datasets:** 27 (out of 25 models available - see [07-model-catalog.md](../ml-framework-design/07-model-catalog.md))
- **Monitor Datasets:** 31 (across 8 monitors with ~155 custom metrics - see [03-custom-metrics.md](../lakehouse-monitoring-design/03-custom-metrics.md))

### 1.2 Asset Utilization Gaps

> **Source of Truth:** 
> - ML Models: [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)
> - Custom Metrics: [03-custom-metrics.md](../lakehouse-monitoring-design/03-custom-metrics.md)

#### ML Models (25 Available)

| Domain | Models Available | Currently Used | Gap |
|--------|-----------------|----------------|-----|
| Cost | 6 | 6 | 0 ✅ |
| Security | 4 | 4 | 0 ✅ |
| Performance | 7 | 7 | 0 ✅ |
| Reliability | 5 | 5 | 0 ✅ |
| Quality | 3 | 3 | 0 ✅ |
| **Total** | **25** | **25** | **0** |

#### Lakehouse Monitor Metrics (~155 Available)

| Monitor | Source Table | Custom Metrics | Currently Visualized |
|---------|-------------|----------------|---------------------|
| Cost Monitor | fact_usage | 35 | ~20 |
| Job Monitor | fact_job_run_timeline | 50 | ~25 |
| Security Monitor | fact_audit_logs | 13 | ~10 |
| Query Monitor | fact_query_history | 14 | ~10 |
| Cluster Monitor | fact_node_timeline | 10 | ~8 |
| Quality Monitor | fact_data_quality_results | 10 | ~5 |
| Governance Monitor | fact_governance_metrics | 11 | ~5 |
| Inference Monitor | fact_model_serving | 15 | ~5 |
| **Total** | | **~155** | **~88** |

#### Metric Views (11 Available, Variable Usage)

| Metric View | Domain | Dashboard Usage |
|-------------|--------|-----------------|
| cost_analytics | Cost | Moderate |
| commit_tracking | Cost | Moderate |
| security_events | Security | Low |
| job_performance | Reliability | Low |
| query_performance | Performance | Moderate |
| cluster_utilization | Performance | Moderate |
| cluster_efficiency | Performance | Low |
| governance_analytics | Quality | Low |
| data_quality | Quality | Not Used |
| ml_intelligence | Cross-domain | Low |
| alert_sync_metrics | Cross-domain | Not Used |

---

## 2. Target State Design

### 2.1 Domain Dashboard Structure

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    UNIFIED DASHBOARD (Executive)                          │
│                  80-100 datasets (rationalized selection)                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│  │   COST    │  │ SECURITY  │  │PERFORMANCE│  │RELIABILITY│  │  QUALITY  │
│  │  90 ds    │  │  90 ds    │  │  90 ds    │  │  90 ds    │  │  90 ds    │
│  │           │  │           │  │           │  │           │  │           │
│  │ • Billing │  │ • Audit   │  │ • Query   │  │ • Jobs    │  │ • Data    │
│  │ • Commit  │  │ • Access  │  │ • Cluster │  │ • Pipeline│  │   Quality │
│  │ • Budget  │  │ • Threats │  │ • DBR     │  │ • SLA     │  │ • Govern- │
│  │ • Tags    │  │ • Perms   │  │ • Cache   │  │ • Retry   │  │   ance    │
│  │           │  │           │  │           │  │           │  │ • Lineage │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Dataset Allocation Per Domain

**Target: ~90 datasets per domain dashboard to stay under 100 limit**

#### Cost Domain Dashboard (~90 datasets)

| Category | Source | Dataset Count |
|----------|--------|---------------|
| KPIs | cost_management | 6 |
| Trend Analysis | cost_management | 8 |
| Breakdown Analysis | cost_management | 10 |
| Commit Tracking | commit_tracking | 10 |
| **ML Predictions** | 6 models | 8 |
| **Lakehouse Monitor** | cost_monitor (35 metrics) | 15 |
| **Metric Views** | cost_analytics, commit_tracking | 5 |
| Filters & Global | new | 6 |
| **Subtotal** | | **68** |
| *Buffer for enrichment* | | *22* |

#### Security Domain Dashboard (~90 datasets)

| Category | Source | Dataset Count |
|----------|--------|---------------|
| KPIs | security_audit | 5 |
| Event Analysis | security_audit | 8 |
| Access Patterns | security_audit | 8 |
| Governance (Access) | governance_hub | 8 |
| **ML Predictions** | 4 models | 6 |
| **Lakehouse Monitor** | security_monitor (13 metrics) | 12 |
| **Metric Views** | security_events, governance_analytics | 5 |
| Filters & Global | new | 6 |
| **Subtotal** | | **58** |
| *Buffer for enrichment* | | *32* |

#### Performance Domain Dashboard (~90 datasets)

| Category | Source | Dataset Count |
|----------|--------|---------------|
| Query Performance KPIs | query_performance | 5 |
| Query Analysis | query_performance | 10 |
| Cluster KPIs | cluster_utilization | 5 |
| Cluster Analysis | cluster_utilization | 10 |
| DBR Migration | dbr_migration | 6 |
| **ML Predictions** | 7 models | 10 |
| **Lakehouse Monitor** | query_monitor (14 metrics), cluster_monitor (10 metrics) | 12 |
| **Metric Views** | query_performance, cluster_utilization | 5 |
| Filters & Global | new | 6 |
| **Subtotal** | | **69** |
| *Buffer for enrichment* | | *21* |

#### Reliability Domain Dashboard (~90 datasets)

| Category | Source | Dataset Count |
|----------|--------|---------------|
| KPIs | job_reliability | 4 |
| Success/Failure Analysis | job_reliability | 10 |
| Duration Analysis | job_reliability | 8 |
| Optimization | job_optimization | 7 |
| **ML Predictions** | 5 models | 8 |
| **Lakehouse Monitor** | job_monitor (50 metrics) | 15 |
| **Metric Views** | job_performance | 5 |
| Filters & Global | new | 6 |
| **Subtotal** | | **63** |
| *Buffer for enrichment* | | *27* |

#### Quality Domain Dashboard (~90 datasets)

| Category | Source | Dataset Count |
|----------|--------|---------------|
| Table Health | table_health | 7 |
| Governance | governance_hub | 12 |
| Lineage | governance_hub | 6 |
| **ML Predictions** | 3 models | 5 |
| **Lakehouse Monitor** | quality_monitor (10 metrics), governance_monitor (11 metrics) | 12 |
| **Metric Views** | data_quality, governance_analytics | 5 |
| Filters & Global | new | 6 |
| **Subtotal** | | **53** |
| *Buffer for enrichment* | | *37* |

#### Unified Dashboard (~80-100 datasets)

| Category | Source | Dataset Count |
|----------|--------|---------------|
| Executive KPIs (All Domains) | curated | 10 |
| Cost Summary | cost_domain | 10 |
| Security Summary | security_domain | 10 |
| Performance Summary | performance_domain | 10 |
| Reliability Summary | reliability_domain | 10 |
| Quality Summary | quality_domain | 8 |
| Cross-domain ML | ml_intelligence | 8 |
| Global Filters | shared | 6 |
| Alert Summary | alerting | 5 |
| **Subtotal** | | **77** |
| *Buffer* | | *23* |

---

## 3. Asset Integration Plan

### 3.1 ML Model Integration Matrix (25 Models)

> **Source of Truth:** [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)

| # | Model | Domain | Algorithm | Dashboard Integration |
|---|-------|--------|-----------|----------------------|
| | **Cost Domain (6 Models)** | | | |
| 1 | cost_anomaly_detector | Cost | Isolation Forest | Cost Dashboard: Anomaly alerts, trend overlays |
| 2 | budget_forecaster | Cost | Gradient Boosting | Cost + Commit: Forecast projections |
| 3 | job_cost_optimizer | Cost | Gradient Boosting | Cost Dashboard: Job cost analysis |
| 4 | chargeback_attribution | Cost | Gradient Boosting | Cost Dashboard: Attribution charts |
| 5 | commitment_recommender | Cost | Gradient Boosting | Commit Dashboard: Recommendations table |
| 6 | tag_recommender | Cost | Random Forest + TF-IDF | Cost Dashboard: Tag suggestions |
| | **Security Domain (4 Models)** | | | |
| 7 | security_threat_detector | Security | Isolation Forest | Security: Threat alerts, risk scores |
| 8 | access_pattern_analyzer | Security | XGBoost | Security: Pattern anomalies |
| 9 | compliance_risk_classifier | Security | Random Forest | Security: Compliance scores |
| 10 | permission_recommender | Security | Random Forest | Security: Permission suggestions |
| | **Performance Domain (7 Models)** | | | |
| 11 | query_performance_forecaster | Performance | Gradient Boosting | Query: Duration forecasts |
| 12 | warehouse_optimizer | Performance | XGBoost | Query: Sizing recommendations |
| 13 | cache_hit_predictor | Performance | XGBoost | Query: Cache predictions |
| 14 | query_optimization_recommender | Performance | XGBoost | Query: Tuning suggestions |
| 15 | cluster_sizing_recommender | Performance | Gradient Boosting | Cluster: Right-sizing recs |
| 16 | cluster_capacity_planner | Performance | Gradient Boosting | Cluster: Capacity forecasts |
| 17 | regression_detector | Performance | Isolation Forest | Query: Regression alerts |
| | **Reliability Domain (5 Models)** | | | |
| 18 | job_failure_predictor | Reliability | XGBoost | Jobs: Failure predictions |
| 19 | job_duration_forecaster | Reliability | Gradient Boosting | Jobs: Duration forecasts |
| 20 | sla_breach_predictor | Reliability | XGBoost | Jobs: SLA risk alerts |
| 21 | pipeline_health_scorer | Reliability | Gradient Boosting | Jobs: Pipeline scores |
| 22 | retry_success_predictor | Reliability | XGBoost | Jobs: Retry recommendations |
| | **Quality Domain (3 Models)** | | | |
| 23 | data_drift_detector | Quality | Isolation Forest | Quality: Data drift view |
| 24 | schema_change_predictor | Quality | XGBoost | Quality: Change predictions |
| 25 | schema_evolution_predictor | Quality | Random Forest | Quality: Schema evolution alerts |

### 3.2 Lakehouse Monitor Integration

#### fact_usage Monitor → Cost Dashboard

| Metric | Widget Type | Description |
|--------|-------------|-------------|
| total_daily_cost | KPI + Trend | Primary cost metric |
| tag_coverage_pct | Gauge | Tag hygiene |
| serverless_ratio | Pie | Compute distribution |
| jobs_on_all_purpose_cost | Alert | Inefficient pattern detection |
| cost_drift_pct | Drift Alert | Period-over-period change |
| potential_job_cluster_savings | KPI | Savings opportunity |

#### fact_job_run_timeline Monitor → Reliability Dashboard

| Metric | Widget Type | Description |
|--------|-------------|-------------|
| success_rate | KPI + Trend | Primary reliability metric |
| failure_rate | KPI | Failure tracking |
| p95_duration_minutes | KPI | SLA monitoring |
| long_running_rate | Alert | Duration outliers |
| success_rate_drift | Drift Alert | Reliability changes |
| duration_cv | Gauge | Duration consistency |

#### fact_audit_logs Monitor → Security Dashboard

| Metric | Widget Type | Description |
|--------|-------------|-------------|
| total_events | KPI + Trend | Event volume |
| sensitive_action_rate | KPI | Security concern indicator |
| human_off_hours_rate | Alert | Off-hours activity |
| failure_rate | KPI | Access issues |
| event_volume_drift_pct | Drift Alert | Activity changes |
| unauthorized_rate | Alert | Access denials |

#### fact_query_history Monitor → Performance Dashboard

| Metric | Widget Type | Description |
|--------|-------------|-------------|
| query_count | KPI + Trend | Query volume |
| p95_duration_sec | KPI | Performance SLA |
| sla_breach_rate | Alert | 60s threshold breaches |
| efficiency_rate | Gauge | Efficient query % |
| spill_rate | Alert | Memory pressure |
| cache_hit_rate | KPI | Cache effectiveness |

#### fact_node_timeline Monitor → Performance Dashboard

| Metric | Widget Type | Description |
|--------|-------------|-------------|
| avg_cpu_total_pct | KPI + Trend | CPU utilization |
| avg_memory_pct | KPI + Trend | Memory utilization |
| efficiency_score | Gauge | Optimal utilization % |
| rightsizing_opportunity_pct | KPI | Savings opportunity |
| underprovisioned_rate | Alert | Scale-up needed |
| overprovisioned_rate | Alert | Scale-down opportunity |

---

## 4. Migration Strategy

### 4.1 Phase 1: Foundation (Week 1)
1. Create directory structure for new domain dashboards
2. Extract datasets from existing dashboards
3. Create mapping tables for dataset consolidation

### 4.2 Phase 2: Domain Dashboards (Weeks 2-3)
1. Build Cost Domain Dashboard
2. Build Security Domain Dashboard
3. Build Performance Domain Dashboard
4. Build Reliability Domain Dashboard
5. Build Quality Domain Dashboard

### 4.3 Phase 3: Integration (Week 4)
1. Add ML model datasets to each domain
2. Add Lakehouse Monitor datasets
3. Integrate Metric Views
4. Add global filters

### 4.4 Phase 4: Unified Dashboard (Week 5)
1. Build rationalized Unified Dashboard
2. Select best widgets from each domain
3. Add executive summary views
4. Test and validate

### 4.5 Phase 5: Deployment & Cleanup (Week 6)
1. Deploy all 6 dashboards
2. Update deployment scripts
3. Deprecate old individual dashboards
4. Document and train

---

## 5. Success Metrics

| Metric | Target |
|--------|--------|
| Dashboard Count | 6 (down from 12) |
| ML Model Integration | 100% (25/25 models) |
| Monitor Metric Integration | >60% of ~155 custom metrics |
| Metric View Integration | 100% (11/11 views) |
| Dataset Efficiency | <100 per dashboard |
| Query Performance | <3 second load time |

---

## 6. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Dataset limit exceeded | Use CTEs, efficient aggregations |
| Query performance degradation | Pre-aggregate in Gold layer |
| Missing functionality | Maintain individual dashboards during transition |
| User adoption | Gradual rollout with training |

---

## Next Steps

1. Review this plan with stakeholders
2. Begin asset inventory verification (see [02-asset-inventory.md](02-asset-inventory.md))
3. Start Phase 1 implementation

