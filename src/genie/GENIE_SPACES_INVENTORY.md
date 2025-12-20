# Genie Spaces Inventory

## Overview

This document provides a comprehensive inventory of all Genie Spaces implemented for the Databricks Health Monitor project. **Consolidated to 1 Genie Space per Agent Domain to prevent sprawl.**

## Genie Space Summary by Agent Domain

| Agent Domain | Genie Space | Purpose | Assets | Target Users |
|--------------|-------------|---------|--------|--------------|
| 💰 Cost | Cost Intelligence | FinOps and billing analytics | 15 TVFs, 2 MVs, 6 ML | Finance, Platform Admin |
| 🔄 Reliability | Job Health Monitor | Job reliability tracking | 12 TVFs, 1 MV, 5 ML | DevOps, Data Engineering |
| ⚡ Performance | Performance | Query + Cluster combined | 16 TVFs, 3 MVs, 7 ML | DBAs, Platform Eng |
| 🔒 Security | Security Auditor | Audit and compliance | 10 TVFs, 2 MVs, 4 ML | Security, Compliance |
| ✅ Quality | Data Quality Monitor | Freshness, lineage | 7 TVFs, 2 MVs, 3 ML | Data Governance |
| 🌐 Unified | Health Monitor | All domains | 60 TVFs, 10 MVs, 25 ML | Leadership, SREs |

**Total: 6 Genie Spaces (5 domain-specific + 1 unified)**

---

## Genie Space Details

### 💰 Cost Intelligence Space

**Name:** `Health Monitor Cost Intelligence Space`

**Description:** Natural language interface for Databricks cost analytics and FinOps. Enables finance teams, platform administrators, and executives to query billing, usage, and cost optimization insights without SQL.

**Data Assets:**
- **Metric Views (2):** `cost_analytics`, `commit_tracking`
- **TVFs (15):** `get_top_cost_contributors`, `get_cost_trend_by_sku`, `get_cost_by_owner`, `get_cost_by_tag`, `get_untagged_resources`, `get_tag_coverage`, `get_cost_week_over_week`, `get_cost_anomalies`, `get_cost_forecast_summary`, `get_cost_mtd_summary`, `get_commit_vs_actual`, `get_spend_by_custom_tags`, `get_cost_growth_analysis`, `get_cost_growth_by_period`, `get_all_purpose_cluster_cost`
- **ML Tables (6):** `cost_anomaly_predictions`, `cost_forecast_predictions`, `tag_recommendations`, `user_cost_segments`, `migration_recommendations`, `budget_alert_predictions`
- **Monitoring Tables (2):** `fact_usage_profile_metrics`, `fact_usage_drift_metrics`

**Sample Questions:**
1. "What is our total spend this month?"
2. "Which workspaces cost the most?"
3. "Show me cost anomalies"
4. "What's the cost forecast for next month?"

**Setup Document:** [`cost_intelligence_genie.md`](./cost_intelligence_genie.md)

---

### 🔄 Job Health Monitor Space

**Name:** `Health Monitor Job Reliability Space`

**Description:** Natural language interface for Databricks job reliability and execution analytics. Enables DevOps, data engineers, and SREs to query job success rates, failure patterns, and performance metrics without SQL.

**Data Assets:**
- **Metric Views (1):** `job_performance`
- **TVFs (12):** `get_failed_jobs`, `get_job_success_rate`, `get_job_duration_percentiles`, `get_job_failure_trends`, `get_job_sla_compliance`, `get_job_run_details`, `get_most_expensive_jobs`, `get_job_retry_analysis`, `get_job_repair_costs`, `get_job_spend_trend_analysis`, `get_job_failure_costs`, `get_job_run_duration_analysis`
- **ML Tables (5):** `job_failure_predictions`, `retry_success_predictions`, `pipeline_health_scores`, `incident_impact_predictions`, `self_healing_recommendations`
- **Monitoring Tables (2):** `fact_job_run_timeline_profile_metrics`, `fact_job_run_timeline_drift_metrics`

**Sample Questions:**
1. "What is our job success rate?"
2. "Show me failed jobs today"
3. "Which jobs are likely to fail?"
4. "What's the health score for jobs?"

**Setup Document:** [`job_health_monitor_genie.md`](./job_health_monitor_genie.md)

---

### ⚡ Performance Space (Combined Query + Cluster)

**Name:** `Health Monitor Performance Space`

**Description:** Natural language interface for Databricks query and cluster performance analytics. Enables DBAs, platform engineers, and FinOps to query execution metrics, warehouse utilization, cluster efficiency, and right-sizing opportunities without SQL. **Combined Query Performance + Cluster Optimizer into single space.**

**Data Assets:**
- **Metric Views (3):** `query_performance`, `cluster_utilization`, `cluster_efficiency`
- **TVFs (16):**
  - *Query TVFs:* `get_slow_queries`, `get_warehouse_utilization`, `get_query_efficiency`, `get_high_spill_queries`, `get_query_volume_trends`, `get_user_query_summary`, `get_query_latency_percentiles`, `get_failed_queries`, `get_query_efficiency_analysis`, `get_job_outlier_runs`
  - *Cluster TVFs:* `get_cluster_utilization`, `get_cluster_resource_metrics`, `get_underutilized_clusters`, `get_jobs_without_autoscaling`, `get_jobs_on_legacy_dbr`, `get_cluster_right_sizing_recommendations`
- **ML Tables (7):**
  - *Query ML:* `query_optimization_classifications`, `query_optimization_recommendations`, `cache_hit_predictions`, `job_duration_predictions`
  - *Cluster ML:* `cluster_capacity_recommendations`, `cluster_rightsizing_recommendations`, `dbr_migration_risk_scores`
- **Monitoring Tables (4):** `fact_query_history_profile_metrics`, `fact_query_history_drift_metrics`, `fact_node_timeline_profile_metrics`, `fact_node_timeline_drift_metrics`

**Sample Questions:**
1. "What is our P95 query duration?"
2. "Show me slow queries today"
3. "Which clusters are underutilized?"
4. "Show me right-sizing recommendations"
5. "What is our average CPU utilization?"

**Setup Document:** [`performance_genie.md`](./performance_genie.md)

---

### 🔒 Security Auditor Space

**Name:** `Health Monitor Security Auditor Space`

**Description:** Natural language interface for Databricks security, audit, and compliance analytics. Enables security teams, compliance officers, and administrators to query access patterns, audit trails, and security events without SQL.

**Data Assets:**
- **Metric Views (2):** `security_events`, `governance_analytics`
- **TVFs (10):** `get_user_activity_summary`, `get_sensitive_table_access`, `get_failed_actions`, `get_permission_changes`, `get_off_hours_activity`, `get_security_events_timeline`, `get_ip_address_analysis`, `get_table_access_audit`, `get_user_activity_patterns`, `get_service_account_audit`
- **ML Tables (4):** `access_anomaly_predictions`, `user_risk_scores`, `access_classifications`, `off_hours_baseline_predictions`
- **Monitoring Tables (2):** `fact_audit_logs_profile_metrics`, `fact_audit_logs_drift_metrics`

**Sample Questions:**
1. "Who accessed sensitive data?"
2. "Are there any security anomalies?"
3. "Show me off-hours activity"
4. "What's the risk score for users?"

**Setup Document:** [`security_auditor_genie.md`](./security_auditor_genie.md)

---

### ✅ Data Quality Monitor Space

**Name:** `Health Monitor Data Quality Space`

**Description:** Natural language interface for data quality, freshness, and governance analytics. Enables data stewards, governance teams, and data engineers to query table health, lineage, and quality metrics without SQL.

**Data Assets:**
- **Metric Views (2):** `data_quality`, `ml_intelligence`
- **TVFs (7):** `get_table_freshness`, `get_job_data_quality_status`, `get_data_freshness_by_domain`, `get_data_quality_summary`, `get_tables_failing_quality`, `get_table_activity_status`, `get_pipeline_data_lineage`
- **ML Tables (3):** `quality_anomaly_predictions`, `quality_trend_predictions`, `freshness_alert_predictions`
- **Monitoring Tables (3):** `fact_information_schema_table_storage_profile_metrics`, `fact_table_lineage_profile_metrics`, `fact_table_lineage_drift_metrics`

**Sample Questions:**
1. "Which tables are stale?"
2. "What is our data quality score?"
3. "Are there any quality anomalies?"
4. "Predict freshness issues"

**Setup Document:** [`data_quality_monitor_genie.md`](./data_quality_monitor_genie.md)

---

### 🌐 Unified Health Monitor Space

**Name:** `Databricks Health Monitor Space`

**Description:** Comprehensive natural language interface for Databricks platform health monitoring. Enables leadership, platform administrators, and SREs to query costs, job reliability, query performance, cluster efficiency, security audit, and data quality - all in one unified space.

**Data Assets:**
- **Metric Views (10):** All metric views from all domains
- **TVFs (60):** All TVFs from all domains
- **ML Tables (25):** All ML prediction tables
- **Monitoring Tables (16):** All Lakehouse Monitoring tables

**Sample Questions:**
1. "What is the overall platform health?"
2. "Show me anomalies across all domains"
3. "What is our total spend and job success rate?"
4. "Which areas need attention today?"

**Setup Document:** [`unified_health_monitor_genie.md`](./unified_health_monitor_genie.md)

---

## Asset Count Summary

| Asset Type | Cost | Reliability | Performance | Security | Quality | Unified | Total Unique |
|------------|------|-------------|-------------|----------|---------|---------|--------------|
| Metric Views | 2 | 1 | 3 | 2 | 2 | 10 | **10** |
| TVFs | 15 | 12 | 16 | 10 | 7 | 60 | **60** |
| ML Tables | 6 | 5 | 7 | 4 | 3 | 25 | **25** |
| Monitoring Tables | 2 | 2 | 4 | 2 | 3 | 16 | **16** |
| **Gold Tables** | 4 | 6 | 6 | 7 | 14 | 38 | **38** |

**Total Genie Spaces:** 6 (5 domain-specific + 1 unified)

---

## Gold Layer Table Mapping by Agent Domain

**Source:** `gold_layer_design/yaml/`

| Agent Domain | YAML Folders | Tables | Examples |
|--------------|--------------|--------|----------|
| 💰 **Cost** | billing/ | 4 | dim_sku, fact_usage, fact_account_prices, fact_list_prices |
| ⚡ **Performance** | compute/, query_performance/ | 6 | dim_cluster, dim_node_type, fact_node_timeline, dim_warehouse, fact_query_history, fact_warehouse_events |
| 🔄 **Reliability** | lakeflow/ | 6 | dim_job, dim_job_task, dim_pipeline, fact_job_run_timeline, fact_job_task_run_timeline, fact_pipeline_update_timeline |
| 🔒 **Security** | security/, governance/ | 7 | fact_audit_logs, fact_assistant_events, fact_clean_room_events, fact_inbound_network, fact_outbound_network, fact_table_lineage, fact_column_lineage |
| ✅ **Quality** | data_classification/, data_quality_monitoring/, storage/, mlflow/, model_serving/, marketplace/ | 14 | fact_data_classification, fact_dq_monitoring, fact_predictive_optimization, dim_experiment, fact_mlflow_runs, dim_served_entities, fact_endpoint_usage, fact_listing_access |
| 🌐 **Shared** | shared/ | 1 | dim_workspace |

**Total Gold Tables:** 38

---

## Deployment Status

| Genie Space | Status | Setup Document | Last Updated |
|-------------|--------|----------------|--------------|
| Cost Intelligence | 📝 Documented | ✅ Complete | 2025-12-19 |
| Job Health Monitor | 📝 Documented | ✅ Complete | 2025-12-19 |
| Performance | 📝 Documented | ✅ Complete | 2025-12-19 |
| Security Auditor | 📝 Documented | ✅ Complete | 2025-12-19 |
| Data Quality Monitor | 📝 Documented | ✅ Complete | 2025-12-19 |
| Unified Health Monitor | 📝 Documented | ✅ Complete | 2025-12-19 |

**Note:** Genie Spaces are created via the Databricks UI. Use the setup documents for configuration.

---

## Benchmark Questions Summary

Each Genie Space has 10-15 benchmark questions with expected SQL for validation:

| Genie Space | Benchmark Questions | SQL Provided |
|-------------|---------------------|--------------|
| Cost Intelligence | 12 | ✅ All |
| Job Health Monitor | 10 | ✅ All |
| Performance | 10 | ✅ All |
| Security Auditor | 10 | ✅ All |
| Data Quality Monitor | 10 | ✅ All |
| Unified Health Monitor | 12 | ✅ All |

---

## References

### Setup Documents
- [Cost Intelligence](./cost_intelligence_genie.md) - 💰 Cost
- [Job Health Monitor](./job_health_monitor_genie.md) - 🔄 Reliability
- [Performance](./performance_genie.md) - ⚡ Performance (Query + Cluster)
- [Security Auditor](./security_auditor_genie.md) - 🔒 Security
- [Data Quality Monitor](./data_quality_monitor_genie.md) - ✅ Quality
- [Unified Health Monitor](./unified_health_monitor_genie.md) - 🌐 Unified

### Related Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md)
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md)
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md)
- [Lakehouse Monitoring Inventory](../../docs/reference/LAKEHOUSE_MONITORING_INVENTORY.md)
- [Dashboard Inventory](../dashboards/DASHBOARD_INVENTORY.md)

### Official Documentation
- [Databricks Genie](https://docs.databricks.com/genie/)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Genie Instructions](https://docs.databricks.com/genie/instructions)

### Cursor Rules
- [Genie Space Patterns](../../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc)
