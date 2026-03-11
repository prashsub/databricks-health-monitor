# Databricks Platform Monitor — Alert Catalog

Organized by the five Control Tower pillars plus cross-cutting operational alerts. Each alert includes the trigger condition, severity guidance, and a recommended next-best-action.

---

## 1. COST

| # | Alert | Trigger Condition | Severity | Recommended Action |
|---|-------|-------------------|----------|--------------------|
| C-01 | **Cost Anomaly Detected** | Isolation Forest model flags `prediction = -1` (anomalous cost pattern) for a workspace/SKU | CRITICAL if anomaly_score ≥ 0.9, WARNING otherwise | Investigate the workspace; check for runaway jobs, misconfigured auto-scaling, or unexpected workloads. Drill into SKU breakdown. |
| C-02 | **Daily Spend Spike** | `dbu_change_pct_1d` exceeds ±50% day-over-day for a workspace | WARNING (CRITICAL if > 100%) | Compare today's job/query mix to yesterday. Identify new or changed workloads. Consider kill/pause if unplanned. |
| C-03 | **Week-over-Week Cost Growth** | `dbu_change_pct_7d` exceeds ±30% for sustained 3+ days | WARNING | Review whether growth is organic (new team onboarding) or a regression. Flag to workspace owner. |
| C-04 | **Budget Forecast Breach** | `budget_forecast_predictions` projects spend will exceed budget threshold within 7/14/30 days | CRITICAL at 7 days, WARNING at 14 days, INFO at 30 days | Notify finance/workspace owner. Recommend throttling non-critical workloads, right-sizing warehouses, or requesting budget increase. |
| C-05 | **All-Purpose Cluster Inefficiency** | `all_purpose_inefficiency_ratio` > 0.3 (30%+ of cost from jobs running on all-purpose clusters) | WARNING | Migrate recurring jobs to job clusters (~40% savings typical). Show `potential_job_cluster_savings` estimate. |
| C-06 | **Low Serverless Adoption** | `serverless_adoption_ratio` drops below org target or decreases significantly | INFO | Review which workloads could migrate to serverless. Share cost comparison projections. |
| C-07 | **Commitment Underutilization** | `commitment_recommendations` shows committed capacity utilization < 70% | WARNING | Right-size commitments at next renewal. Consider reallocating unused capacity across workspaces. |
| C-08 | **Commitment Overrun** | On-demand spend exceeds committed capacity by > 20% | WARNING | Evaluate purchasing additional commitments. Identify bursty workloads driving overrun. |
| C-09 | **Chargeback Anomaly** | `chargeback_predictions` show cost attribution shifting unexpectedly between teams/departments | INFO | Validate tagging accuracy. Confirm whether workload ownership actually changed or if tags are misconfigured. |
| C-10 | **Tag Coverage Gap** | Untagged cost exceeds threshold (e.g., > 15% of total spend has no cost-center tag) | WARNING | Run `tag_recommendations` model. Push tag governance policy to workspace admins. |
| C-11 | **Weekend/Off-Hours Spend Spike** | `is_weekend = 1` and daily cost > 2× weekday average | INFO | Investigate scheduled jobs running unnecessarily. Consider pausing non-critical weekend pipelines. |
| C-12 | **Month-End Batch Overrun** | `is_month_end = 1` and cost exceeds historical month-end average by > 40% | WARNING | Verify if new month-end processes were added. Optimize heavy batch jobs or stagger their schedules. |

---

## 2. PERFORMANCE

| # | Alert | Trigger Condition | Severity | Recommended Action |
|---|-------|-------------------|----------|--------------------|
| P-01 | **Query Performance Regression** | `performance_regression_predictions` flags a query/warehouse with degradation | CRITICAL if P95 duration > 2× baseline, WARNING otherwise | Run `query_optimization_predictions` for tuning recommendations. Check for missing statistics, changed data volumes, or plan regressions. |
| P-02 | **P95 Duration Drift** | `p95_duration_drift` exceeds threshold in `fact_query_history_drift_metrics` | WARNING | Identify affected queries. Check for table growth, missing Z-ORDER, stale statistics, or concurrent contention. |
| P-03 | **Spill Rate Drift** | `spill_rate_drift` increases significantly — queries spilling to disk | WARNING (CRITICAL if widespread) | Upsize warehouse or optimize queries causing spills. Review join strategies and partition pruning. |
| P-04 | **Efficiency Rate Drift** | `efficiency_rate_drift` degrades across a warehouse | WARNING | Audit query patterns. Look for full table scans, missing predicates, or Cartesian joins. |
| P-05 | **Cache Hit Rate Drop** | `cache_hit_predictions` show cache effectiveness declining | INFO | Investigate if data churn increased, warehouse restarts are too frequent, or query patterns changed. Consider enabling result caching or adjusting photon settings. |
| P-06 | **Warehouse Right-Sizing Opportunity** | `warehouse_optimizer_predictions` recommends resize (up or down) | INFO (WARNING if undersized causing failures) | Apply recommended warehouse size. For undersized: scale up to reduce queue times. For oversized: scale down to save cost. |
| P-07 | **CPU Utilization Drift** | `cpu_utilization_drift` in `fact_node_timeline_drift_metrics` exceeds threshold | WARNING | Investigate workload changes. High CPU drift may indicate query plan regressions or new heavy workloads. |
| P-08 | **Memory Utilization Drift** | `memory_utilization_drift` spikes in node timeline metrics | WARNING (CRITICAL if OOM-adjacent) | Check for memory-intensive operations (large shuffles, exploding joins). Consider node type upgrade or query optimization. |
| P-09 | **Cluster Efficiency Score Drift** | `efficiency_score_drift` degrades in node metrics | WARNING | Cross-reference with query drift metrics to identify if compute or queries are the root cause. |
| P-10 | **Query Optimization Available** | `query_optimization_predictions` identifies high-impact tuning opportunities | INFO | Apply recommendations: add Z-ORDER, update statistics, rewrite inefficient patterns, add partition filters. |

---

## 3. SECURITY

| # | Alert | Trigger Condition | Severity | Recommended Action |
|---|-------|-------------------|----------|--------------------|
| S-01 | **Security Threat Detected** | `security_threat_predictions` flags high risk score | CRITICAL if risk_score ≥ 0.9, HIGH if ≥ 0.7 | Investigate immediately. Cross-reference user activity logs. Consider revoking access pending review. |
| S-02 | **Data Exfiltration Risk** | `exfiltration_predictions` flags user with high data volume access + export activity | CRITICAL | Lock down the user's export permissions. Audit accessed tables and download history. Escalate to security team. |
| S-03 | **Privilege Escalation Detected** | `privilege_escalation_predictions` flags unexpected permission changes | CRITICAL | Revert unauthorized permission changes. Audit who granted the escalation and from which IP. |
| S-04 | **Anomalous User Behavior** | `user_behavior_predictions` anomaly score exceeds baseline significantly | WARNING (CRITICAL for service principals) | Compare current behavior to historical baseline. Investigate if credentials were compromised. |
| S-05 | **Failed Authentication Spike** | Failed login count exceeds 3× baseline in `security_events` | CRITICAL | Check for brute-force attempts. Consider IP blocking, MFA enforcement, or temporary account lockout. |
| S-06 | **Off-Hours Sensitive Data Access** | Sensitive actions (`is_sensitive_action = true`) occurring during unusual hours | WARNING | Verify with the user. If unauthorized, revoke session tokens and audit accessed data. |
| S-07 | **Service Principal Anomaly** | Service principal activity volume or pattern deviates from baseline | WARNING | Check if automation changed, credentials were leaked, or the SP is being misused. Rotate credentials if suspicious. |
| S-08 | **Audit Event Volume Surge** | 24h event growth rate exceeds threshold in security events | WARNING | Determine if caused by legitimate activity (migration, bulk operations) or potential security incident. |
| S-09 | **New IP Address Access** | User or SP accessing from previously unseen IP range | INFO (WARNING for admin accounts) | Validate the IP. Update allowlists if legitimate. Investigate if combined with other anomalous signals. |
| S-10 | **Permission Change on Critical Assets** | PERMISSION-type events on production tables/schemas | WARNING | Audit the change. Ensure it follows change management process. Revert if unauthorized. |

---

## 4. RELIABILITY

| # | Alert | Trigger Condition | Severity | Recommended Action |
|---|-------|-------------------|----------|--------------------|
| R-01 | **Job Failure Predicted** | `job_failure_predictions` probability exceeds threshold for upcoming run | WARNING (CRITICAL if mission-critical job) | Pre-emptively check dependencies, cluster availability, and input data. Consider running a dry-run or adjusting resources. |
| R-02 | **Job Failure Rate Spike** | Rolling 30-day failure rate exceeds baseline in `job_performance` | CRITICAL if success_rate < 80%, WARNING if < 95% | Analyze termination codes. Group failures by cluster, job type, and time. Address top failure causes. |
| R-03 | **SLA Breach Predicted** | `sla_breach_predictions` probability > 0.7 for a job/pipeline | CRITICAL | Prioritize the at-risk job. Pre-allocate dedicated compute, reduce upstream dependencies, or notify stakeholders of potential delay. |
| R-04 | **Pipeline Health Degradation** | `pipeline_health_predictions` health score drops below threshold | WARNING (CRITICAL if < 50) | Inspect pipeline stages for bottlenecks. Check source system health, schema changes, or infrastructure issues. |
| R-05 | **Job Duration Regression** | `duration_predictions` shows predicted duration significantly exceeds historical average | WARNING | Investigate data volume growth, cluster changes, or code regressions. Right-size compute or optimize transformations. |
| R-06 | **Job Duration Drastic Decrease** | Job completes in < 50% of expected time | INFO (WARNING if output looks suspicious) | Verify output completeness — a fast run may mean upstream data was missing/empty. Check row counts and data quality. |
| R-07 | **Retry Failure Predicted** | `retry_success_predictions` shows low probability of retry success | WARNING | Don't blindly retry — fix root cause first. Apply recommended retry strategy (backoff, different cluster, skip and alert). |
| R-08 | **Job Timeout** | Job exceeds configured timeout threshold | CRITICAL | Kill and investigate. Check for data skew, lock contention, or infrastructure issues. Consider splitting into smaller tasks. |
| R-09 | **Cluster Capacity Predicted Shortage** | `cluster_capacity_predictions` forecasts insufficient capacity for upcoming workload | WARNING | Pre-scale clusters, stagger job schedules, or switch to serverless for burst capacity. |
| R-10 | **DBR Migration Readiness** | `dbr_migration_predictions` flags clusters running deprecated/EOL Databricks Runtime | INFO (WARNING near EOL date) | Plan migration to supported DBR version. Test workloads on new runtime in staging before cutover. |
| R-11 | **Trigger Type Anomaly** | Unusual trigger pattern (e.g., spike in RETRY triggers or unexpected FILE_ARRIVAL triggers) | INFO | Investigate upstream systems. Excessive retries suggest systemic issues; unexpected file arrivals may indicate misconfigured sources. |

---

## 5. DATA QUALITY

| # | Alert | Trigger Condition | Severity | Recommended Action |
|---|-------|-------------------|----------|--------------------|
| Q-01 | **Table Freshness SLA Breach** | `freshness_status = STALE` (>48h since last update) in `data_quality` | CRITICAL for fact tables, WARNING for dimensions | Investigate upstream pipeline. Check if the source job failed, was paused, or is stuck. Restart pipeline if needed. |
| Q-02 | **Freshness Warning** | `freshness_status = WARNING` (24-48h since last update) | WARNING | Monitor closely. If the pipeline is scheduled and missed, trigger a manual run. Notify pipeline owner. |
| Q-03 | **Freshness Breach Predicted** | `freshness_predictions` forecasts a table will go stale before next scheduled refresh | WARNING | Pre-emptively trigger refresh or adjust schedule. Verify upstream dependencies are healthy. |
| Q-04 | **Data Drift Detected** | `data_drift_predictions` drift score exceeds threshold | WARNING (CRITICAL if drift_score > 0.8) | Investigate affected columns. Determine if drift is from legitimate business changes or data corruption. Update downstream models/dashboards if needed. |
| Q-05 | **Schema Change Detected** | `schema_changes_7d > 0` in `data_drift_predictions` | WARNING | Validate whether schema change was planned. Check downstream consumers for compatibility. Update ETL mappings if needed. |
| Q-06 | **Completeness Degradation** | `completeness_status` distribution shifts — more tables showing incomplete data | WARNING | Check source systems for partial loads. Investigate NULL rates and row count trends. |
| Q-07 | **Downstream Impact — Stale Source** | A stale table feeds multiple downstream consumers (`downstream_impact` count is high) | CRITICAL | Prioritize refresh of this table. Notify all downstream consumers. Consider circuit-breaking dependent pipelines. |
| Q-08 | **Tag Governance Gap** | `tag_recommendations` flags tables/resources missing required governance tags | INFO | Apply recommended tags. Enforce tagging policies via Unity Catalog governance rules. |
| Q-09 | **PII Exposure Risk** | Sensitive columns detected without proper masking/access controls | CRITICAL | Apply column-level masking immediately. Audit who has accessed the unprotected data. Update access policies. |

---

## 6. CROSS-CUTTING / OPERATIONAL

| # | Alert | Trigger Condition | Severity | Recommended Action |
|---|-------|-------------------|----------|--------------------|
| X-01 | **Platform Health Score Drop** | Executive health score for any pillar drops below threshold (e.g., < 70/100) | CRITICAL if < 50, WARNING if < 70 | Drill into the degraded pillar. Address the top contributing issue surfaced in the health score breakdown. |
| X-02 | **ML Model Staleness** | Any ML prediction model hasn't produced predictions in > 24h | WARNING | Check the model pipeline. Verify input data availability, compute resources, and MLflow run status. |
| X-03 | **ML Model Accuracy Degradation** | Model anomaly detection rate drifts significantly from baseline | WARNING | Retrain the model. Investigate if underlying data distributions shifted (concept drift). |
| X-04 | **Alert Sync Failure** | `alert_sync_metrics` shows failed syncs to Databricks SQL Alerts | WARNING | Check API connectivity, alert query validation errors, and warehouse availability. Re-sync manually. |
| X-05 | **Alert Validation Failure** | `alert_validation_results` shows alerts with invalid SQL or unreachable notification channels | WARNING | Fix the invalid SQL template. Test notification channel connectivity. Re-validate before re-enabling. |
| X-06 | **Notification Channel Down** | Test notification to EMAIL/SLACK/PAGERDUTY/WEBHOOK fails | CRITICAL | Repair the notification channel. Check credentials, endpoints, and permissions. Switch to backup channel. |
| X-07 | **Anomaly Cost Spike** | `anomaly_cost_pct` — percentage of total cost flagged as anomalous — exceeds threshold | WARNING | Prioritize investigating the highest-cost anomalies. Cross-reference with cost and security pillars. |
| X-08 | **Multi-Pillar Correlated Incident** | Anomalies fire across 2+ pillars simultaneously (e.g., cost spike + job failures + stale data) | CRITICAL | Treat as a platform incident. Likely root cause is shared (infrastructure failure, bad deployment, data source outage). Investigate holistically. |
| X-09 | **High-Risk Prediction Surge** | `high_risk_count` or `critical_count` in `ml_intelligence` spikes across models | CRITICAL | Triage by pillar. Multiple models firing high-risk simultaneously suggests a systemic issue, not isolated noise. |
| X-10 | **Data Pipeline Backfill Stalled** | `_backfill_checkpoints` shows no progress for extended period | WARNING | Investigate pipeline compute. Check for resource contention, lock conflicts, or upstream blockers. |