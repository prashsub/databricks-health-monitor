# Genie Spaces Ground Truth - Deployed Assets Only

This document lists ALL assets that actually exist and can be referenced in Genie Space benchmark questions.

## ✅ Metric Views (10)

- `mv_cost_analytics`
- `mv_commit_tracking`
- `mv_query_performance`
- `mv_cluster_utilization`
- `mv_cluster_efficiency`
- `mv_job_performance`
- `mv_security_events`
- `mv_governance_analytics`
- `mv_data_quality`
- `mv_ml_intelligence`

## ✅ Table-Valued Functions (60)

### Cost TVFs (15)
- `get_top_cost_contributors`
- `get_cost_trend_by_sku`
- `get_cost_by_owner`
- `get_spend_by_custom_tags`
- `get_tag_coverage`
- `get_cost_week_over_week`
- `get_cost_anomaly_analysis`
- `get_cost_forecast_summary`
- `get_cost_mtd_summary`
- `get_commit_vs_actual`
- `get_cost_growth_analysis`
- `get_cost_growth_by_period`
- `get_cost_efficiency_metrics`
- `get_cluster_cost_efficiency`
- `get_storage_cost_analysis`

### Reliability TVFs (12)
- `get_failed_jobs_summary`
- `get_job_success_rates`
- `get_job_duration_trends`
- `get_job_sla_compliance`
- `get_job_failure_patterns`
- `get_long_running_jobs`
- `get_job_retry_analysis`
- `get_job_duration_percentiles`
- `get_job_failure_cost`
- `get_pipeline_health`
- `get_job_schedule_drift`
- `get_repair_cost_analysis`

### Performance - Query TVFs (10)
- `get_slowest_queries`
- `get_query_latency_percentiles`
- `get_warehouse_performance`
- `get_query_volume_trends`
- `get_top_users_by_query_count`
- `get_query_efficiency_by_user`
- `get_query_queue_analysis`
- `get_failed_queries_summary`
- `get_cache_hit_analysis`
- `get_spill_analysis`

### Performance - Cluster TVFs (11)
- `get_cluster_utilization`
- `get_cluster_resource_metrics`
- `get_underutilized_clusters`
- `get_cluster_rightsizing_recommendations`
- `get_autoscaling_disabled_jobs`
- `get_legacy_dbr_jobs`
- `get_cluster_cost_by_type`
- `get_cluster_uptime_analysis`
- `get_cluster_scaling_events`
- `get_cluster_efficiency_metrics`
- `get_node_utilization_by_cluster`

### Security TVFs (7)
- `get_user_activity`
- `get_sensitive_data_access`
- `get_failed_access_attempts`
- `get_permission_change_history`
- `get_off_hours_access`
- `get_ip_location_analysis`
- `get_service_account_activity`

### Quality TVFs (5)
- `get_stale_tables`
- `get_table_lineage`
- `get_table_activity_summary`
- `get_data_lineage_summary`
- `get_pipeline_lineage_impact`

## ✅ ML Prediction Tables (19+ Available)

Based on successful batch scoring:

### Cost Domain (6)
- `cost_anomaly_predictions`
- `budget_forecast_predictions`
- `job_cost_optimizer_predictions`
- `chargeback_predictions`
- `commitment_recommendations`
- `tag_recommendations`

### Reliability Domain (5)
- `job_failure_predictions`
- `duration_predictions`
- `sla_breach_predictions`
- `retry_success_predictions`
- `pipeline_health_predictions`

### Performance Domain (7)
- `query_optimization_classifications`
- `query_optimization_recommendations`
- `cache_hit_predictions`
- `job_duration_predictions`
- `cluster_capacity_recommendations`
- `cluster_rightsizing_recommendations`
- `dbr_migration_risk_scores`

### Security Domain (4)
- `access_anomaly_predictions`
- `user_risk_scores`
- `access_classifications`
- `off_hours_baseline_predictions`

### Quality Domain (2)
- `quality_anomaly_predictions`
- `freshness_alert_predictions`

> **Note:** `quality_trend_predictions` (schema change predictor) was removed due to single-class data.

## ✅ Lakehouse Monitor Tables (16)

Pattern: `{source_table}_profile_metrics` and `{source_table}_drift_metrics`

- `fact_usage_profile_metrics`
- `fact_usage_drift_metrics`
- `fact_job_run_timeline_profile_metrics`
- `fact_job_run_timeline_drift_metrics`
- `fact_query_history_profile_metrics`
- `fact_query_history_drift_metrics`
- `fact_node_timeline_profile_metrics`
- `fact_node_timeline_drift_metrics`
- `fact_audit_logs_profile_metrics`
- `fact_audit_logs_drift_metrics`
- `fact_table_quality_profile_metrics`
- `fact_table_quality_drift_metrics`
- `fact_governance_metrics_profile_metrics`
- `fact_governance_metrics_drift_metrics`
- `fact_model_serving_profile_metrics`
- `fact_model_serving_drift_metrics`

## ✅ Fact Tables (27)

From `gold_layer_design/yaml/`:
- `fact_usage`
- `fact_account_prices`
- `fact_list_prices`
- `fact_job_run_timeline`
- `fact_job_task_run_timeline`
- `fact_pipeline_update_timeline`
- `fact_query_history`
- `fact_warehouse_events`
- `fact_node_timeline`
- `fact_audit_logs`
- `fact_table_lineage`
- `fact_column_lineage`
- `fact_data_classification`
- `fact_dq_monitoring`
- And more...

## ✅ Dimension Tables (10)

From `gold_layer_design/yaml/`:
- `dim_workspace`
- `dim_sku`
- `dim_job`
- `dim_job_task`
- `dim_pipeline`
- `dim_warehouse`
- `dim_cluster`
- `dim_node_type`
- `dim_experiment`
- `dim_served_entities`

---

**Last Updated:** 2026-01-06
**Source:** Validated against docs/semantic-framework/, docs/lakehouse-monitoring-design/, docs/ml-framework-design/
