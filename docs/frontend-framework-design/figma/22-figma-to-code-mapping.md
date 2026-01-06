# 22 - Figma to Code Capability Mapping

## Overview

This document maps every Figma UI element to its actual data source, API endpoint, and code location in the repository. Use this as the **single source of truth** when implementing the frontend from Figma designs.

---

## 📊 Data Architecture Summary

### Data Sources Available

| Source | Location | Purpose | Refresh |
|--------|----------|---------|---------|
| **System Tables** | `system.billing.*`, `system.access.*`, etc. | Raw Databricks telemetry | Near real-time |
| **Gold Layer Tables** | `{catalog}.gold_health_monitor.*` | Aggregated, business-ready metrics | Hourly |
| **Custom Metrics** | `{catalog}.gold_health_monitor.*_profile_metrics` | Lakehouse Monitoring output | Configurable |
| **ML Model Predictions** | `{catalog}.gold_health_monitor.ml_predictions_*` | Model inference results | On-demand/Scheduled |
| **Alert Rules** | `{catalog}.gold_health_monitor.alert_*` | SQL Alerts V2 triggers | Real-time |

### API Endpoints

| Endpoint Type | Service | Purpose |
|---------------|---------|---------|
| **AI Agent** | Model Serving | Main chat interface, tool orchestration |
| **Genie Spaces** | Databricks Genie | Natural language → SQL queries |
| **TVFs** | SQL Warehouse | Parameterized data retrieval |
| **Metric Views** | SQL Warehouse | Semantic aggregations |
| **Alerts API** | SQL Alerts V2 | Alert management |

---

## 🏠 Executive Overview Screen

### AI Command Center

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ UI Element                    │ Data Source                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ "Good morning, Prashanth!"    │ User context from OAuth session             │
│                               │ Code: src/agent/tools/user_context.py       │
├─────────────────────────────────────────────────────────────────────────────┤
│ "42% cost anomaly detected"   │ ML Model: cost_anomaly_detector             │
│                               │ Table: ml_predictions_cost_anomaly          │
│                               │ Code: src/ml/models/cost/anomaly_detector/  │
├─────────────────────────────────────────────────────────────────────────────┤
│ "3 critical issues"           │ SQL Alert: alert_critical_summary           │
│                               │ TVF: get_critical_alerts_summary()          │
│                               │ Code: src/semantic/tvfs/alerting/           │
├─────────────────────────────────────────────────────────────────────────────┤
│ "$4.2K savings opportunities" │ ML Model: cost_optimizer                    │
│                               │ TVF: get_optimization_opportunities()       │
│                               │ Code: src/ml/models/cost/optimizer/         │
├─────────────────────────────────────────────────────────────────────────────┤
│ "Fix Critical Issues" button  │ Action: Navigate to filtered Explorer       │
│                               │ Route: /explorer?severity=critical          │
├─────────────────────────────────────────────────────────────────────────────┤
│ "Apply Optimizations" button  │ Agent Tool: apply_optimization              │
│                               │ Code: src/agent/tools/cost_tools.py         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Agent Prompt for AI Command Center:**
```
Location: context/prompts/agent/executive_summary_prompt.md

The agent uses:
- Memory (Lakebase): Short-term (24h TTL), Long-term (365d TTL)
- Tools: get_daily_summary(), get_critical_alerts(), get_optimization_opportunities()
```

### Primary Metrics (4 KPI Tiles)

| Metric | Data Source | TVF/Query | Code Location |
|--------|-------------|-----------|---------------|
| **Health Score (87/100)** | Composite metric from all domains | `get_platform_health_score()` | `src/semantic/tvfs/health/health_score.sql` |
| **Cost Today ($45,230)** | `fact_daily_cost` Gold table | `get_daily_cost_summary()` | `src/semantic/tvfs/cost/daily_summary.sql` |
| **Active Alerts (7)** | `alert_active_summary` | `get_active_alerts_count()` | `src/semantic/tvfs/alerting/active_count.sql` |
| **SLA Status (98.2%)** | `fact_sla_metrics` Gold table | `get_sla_status()` | `src/semantic/tvfs/reliability/sla_status.sql` |

**Status Chips Logic:**
```python
# Code: src/api/utils/status_chips.py

def get_status_chip(metric_name: str, value: float, baseline: float) -> dict:
    """Returns chip color and label based on metric comparison."""
    
    # Anomaly detection uses ML model output
    if has_anomaly(metric_name):
        return {"color": "coral", "label": "Anomaly detected"}
    
    # Trend comparison
    delta = (value - baseline) / baseline * 100
    if metric_name in LOWER_IS_BETTER:
        return get_inverse_chip(delta)
    return get_standard_chip(delta)
```

### Domain Health Cards (5 Cards)

| Domain | Health Score Source | Key Metrics | TVF |
|--------|---------------------|-------------|-----|
| **💰 Cost** | `cost_health_score` custom metric | daily_spend, vs_baseline, waste_pct | `get_cost_health()` |
| **⚡ Reliability** | `reliability_health_score` | success_rate, mttr, sla_breaches | `get_reliability_health()` |
| **📈 Performance** | `performance_health_score` | p95_latency, throughput, slow_queries | `get_performance_health()` |
| **🛡️ Security** | `security_health_score` | findings_count, risk_score, coverage | `get_security_health()` |
| **📋 Quality** | `quality_health_score` | dq_score, anomalies, freshness_issues | `get_quality_health()` |

**Custom Metrics (Lakehouse Monitoring):**
```yaml
# Location: src/monitoring/metrics/domain_health_metrics.yaml

- metric_name: cost_health_score
  metric_type: aggregate
  input_columns: [":table"]
  definition: >
    100 - (
      (anomaly_count * 10) + 
      (waste_percentage * 0.5) + 
      (budget_overage_pct * 2)
    )
  output_data_type: double

- metric_name: reliability_health_score
  metric_type: aggregate
  input_columns: [":table"]
  definition: >
    (success_rate * 50) + 
    (sla_compliance * 30) + 
    ((1 - retry_rate) * 20)
  output_data_type: double
```

### Trend Charts (4 Charts)

| Chart | Data Source | Time Range | Visualization |
|-------|-------------|------------|---------------|
| **Cost Trend** | `fact_daily_cost` | Last 7 days | Line + anomaly markers |
| **Reliability Trend** | `fact_job_metrics` | Last 7 days | Line + SLA threshold |
| **Performance Trend** | `fact_query_metrics` | Last 7 days | Line + p95 overlay |
| **Quality Trend** | `fact_dq_metrics` | Last 7 days | Line + drift markers |

**Anomaly Markers Source:**
```sql
-- Location: src/semantic/tvfs/trends/cost_trend_with_anomalies.sql

SELECT 
    date,
    total_cost,
    baseline_cost,
    CASE 
        WHEN anomaly_score > 0.8 THEN 'critical'
        WHEN anomaly_score > 0.5 THEN 'warning'
        ELSE NULL 
    END AS anomaly_marker
FROM gold_health_monitor.fact_daily_cost_with_predictions
WHERE date >= CURRENT_DATE - INTERVAL 7 DAYS
```

---

## 🔍 Global Explorer Screen

### AI Summary Banner

| Element | Data Source | Code |
|---------|-------------|------|
| Total signals count | `COUNT(*)` from `fact_signals` | `get_signals_summary()` |
| Critical count | Filtered by `severity = 'critical'` | Same TVF with filter |
| Top pattern detection | ML Model: `signal_correlation_detector` | `src/ml/models/correlation/` |
| Correlation suggestions | Agent tool: `find_correlated_signals()` | `src/agent/tools/correlation_tools.py` |

### Signal Table Data

```sql
-- Location: src/semantic/tvfs/explorer/get_signals.sql

CREATE FUNCTION get_signals(
    p_severity ARRAY<STRING> DEFAULT ARRAY('critical', 'high', 'medium', 'low'),
    p_domain ARRAY<STRING> DEFAULT NULL,
    p_workspace ARRAY<STRING> DEFAULT NULL,
    p_time_range STRING DEFAULT '24h',
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    signal_id STRING,
    signal_type STRING,
    title STRING,
    description STRING,
    severity STRING,
    domain STRING,
    workspace_name STRING,
    resource_name STRING,
    resource_type STRING,
    impact_metric DOUBLE,
    impact_unit STRING,
    blast_radius INT,
    correlation_count INT,
    ai_insight STRING,
    owner STRING,
    status STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Facet Sidebar

| Facet | Data Source | Aggregation |
|-------|-------------|-------------|
| By Severity | `fact_signals` | `GROUP BY severity` |
| By Domain | `fact_signals` | `GROUP BY domain` |
| By Workspace | `dim_workspace` JOIN | `GROUP BY workspace_name` |
| By Owner | `dim_user` JOIN | `GROUP BY owner_email` |
| Timeline Distribution | `fact_signals` | `DATE_TRUNC('hour', created_at)` |

### Bulk Actions

| Action | API Endpoint | Agent Tool |
|--------|--------------|------------|
| Acknowledge | `PATCH /api/signals/{id}/acknowledge` | `acknowledge_signal()` |
| Assign | `PATCH /api/signals/{id}/assign` | `assign_signal()` |
| Mute | `POST /api/signals/{id}/mute` | `mute_signal()` |
| Merge into Incident | `POST /api/incidents` | `create_incident()` |
| Export | `GET /api/signals/export` | N/A (direct download) |

---

## 📊 Domain Pages

### Cost Analytics

#### KPI Tiles (6)

| KPI | Gold Table | Column | Custom Metric |
|-----|------------|--------|---------------|
| Total Spend | `fact_daily_cost` | `SUM(total_cost)` | `total_spend_7d` |
| Daily Burn | `fact_daily_cost` | `AVG(total_cost)` | `avg_daily_cost` |
| vs Baseline | `fact_cost_baseline` | `current - baseline` | `cost_vs_baseline_pct` |
| Top SKU | `fact_cost_by_sku` | `MAX(cost)` | N/A |
| Waste Score | ML prediction | `waste_score` | `waste_percentage` |
| Active Alerts | `alert_cost_*` | `COUNT(*)` | N/A |

#### Charts

| Chart | Data Source | Visualization Library |
|-------|-------------|----------------------|
| Cost Timeline | `fact_daily_cost` | Recharts AreaChart |
| Cost Treemap | `fact_cost_by_sku` | Recharts Treemap |
| Cost Heatmap | `fact_hourly_cost` | Custom D3 or Tremor |
| Forecast | ML: `cost_forecaster` | Recharts LineChart |

#### ML Models Used

```yaml
# Location: src/ml/models/cost/

models:
  - name: cost_anomaly_detector
    type: IsolationForest
    features: [daily_cost, hour_of_day, day_of_week, workspace_id]
    output: anomaly_score (0-1)
    table: ml_predictions_cost_anomaly
    
  - name: cost_forecaster
    type: Prophet / XGBoost
    features: [historical_cost, seasonality, trend]
    output: predicted_cost, lower_bound, upper_bound
    table: ml_predictions_cost_forecast
    
  - name: cost_optimizer
    type: Rule-based + ML ranking
    features: [resource_utilization, idle_time, cost_per_dbu]
    output: optimization_recommendations
    table: ml_recommendations_cost
```

### Reliability Analytics

| KPI | Data Source | TVF |
|-----|-------------|-----|
| Success Rate | `fact_job_runs` | `get_job_success_rate()` |
| Failed Jobs | `fact_job_runs` | `get_failed_jobs()` |
| SLA Breaches | `fact_sla_events` | `get_sla_breaches()` |
| MTTR | `fact_incident_metrics` | `get_mttr()` |
| Retry Rate | `fact_job_runs` | `get_retry_rate()` |
| Active Alerts | `alert_reliability_*` | `get_reliability_alerts()` |

**ML Models:**
- `failure_predictor`: Predicts job failure probability
- `sla_breach_forecaster`: Predicts SLA breach risk
- `retry_anomaly_detector`: Detects unusual retry patterns

### Performance Analytics

| KPI | Data Source | TVF |
|-----|-------------|-----|
| P50 Latency | `fact_query_metrics` | `get_query_latency_percentiles()` |
| P95 Latency | `fact_query_metrics` | Same TVF |
| Throughput | `fact_query_metrics` | `get_query_throughput()` |
| Slow Queries | `fact_slow_queries` | `get_slow_queries()` |
| Bottlenecks | ML prediction | `get_performance_bottlenecks()` |
| Cache Hit Rate | `fact_warehouse_metrics` | `get_cache_metrics()` |

### Governance & Security Analytics

| KPI | Data Source | TVF |
|-----|-------------|-----|
| UC Coverage | `fact_uc_coverage` | `get_uc_coverage()` |
| Tagged Tables | `fact_tag_coverage` | `get_tag_coverage()` |
| Owned Assets | `fact_ownership` | `get_ownership_coverage()` |
| PII Tables | `fact_pii_detection` | `get_pii_tables()` |
| Security Findings | `alert_security_*` | `get_security_findings()` |
| Permission Changes | `fact_permission_audit` | `get_permission_changes()` |

### Data Quality Analytics

| KPI | Data Source | TVF |
|-----|-------------|-----|
| Quality Score | `fact_dq_scores` | `get_quality_score()` |
| Monitored Tables | `dim_monitored_tables` | `get_monitored_tables()` |
| Anomalies | Lakehouse Monitoring | `get_dq_anomalies()` |
| Freshness Issues | `fact_freshness` | `get_freshness_issues()` |
| Schema Drift | `fact_schema_changes` | `get_schema_drift()` |
| DQ Alerts | `alert_quality_*` | `get_dq_alerts()` |

---

## 🔎 Signal Detail Screen

### Header Section

| Element | Data Source |
|---------|-------------|
| Signal title | `fact_signals.title` |
| Severity badge | `fact_signals.severity` |
| Status badge | `fact_signals.status` |
| Domain badge | `fact_signals.domain` |
| Impact metrics | `fact_signals.impact_*` columns |
| Blast radius | `fact_signal_blast_radius` |
| Owner | `dim_user` JOIN |
| Resource link | `dim_resource` JOIN |

### Timeline Section

```sql
-- Location: src/semantic/tvfs/signals/get_signal_timeline.sql

SELECT 
    event_type,
    event_title,
    event_description,
    event_timestamp,
    actor,
    metadata
FROM fact_signal_events
WHERE signal_id = :signal_id
ORDER BY event_timestamp DESC
```

### AI Root Cause Analysis

| Element | Source |
|---------|--------|
| Summary narrative | Agent: `analyze_root_cause()` tool |
| Root cause hypotheses | ML: `root_cause_analyzer` model |
| Evidence list | `fact_signal_evidence` table |
| Confidence scores | ML model output |
| Recommended actions | Agent: `get_recommended_actions()` |

**Agent Tool:**
```python
# Location: src/agent/tools/analysis_tools.py

@tool
def analyze_root_cause(signal_id: str) -> RootCauseAnalysis:
    """
    Analyzes a signal to determine root cause.
    
    Uses:
    1. Signal details from fact_signals
    2. Correlated signals from correlation model
    3. Recent changes from fact_changes
    4. Historical patterns from ML model
    
    Returns structured analysis with confidence scores.
    """
```

### Evidence & Context

| Section | Data Source |
|---------|-------------|
| Query Details | `fact_query_history` |
| Resource Metrics | `fact_resource_metrics` |
| Change History | `fact_changes` (audit log) |
| Related Signals | ML: `signal_correlation_detector` |

### Action Buttons

| Action | Implementation |
|--------|----------------|
| Acknowledge | `POST /api/signals/{id}/acknowledge` |
| Snooze | `POST /api/signals/{id}/snooze` |
| Mute | `POST /api/signals/{id}/mute` |
| Create Ticket | Integration: Jira/ServiceNow webhook |
| Notify | Integration: Slack/Email/PagerDuty |
| Apply Fix | Agent: `apply_remediation()` tool |

---

## 💬 Chat Interface Screen

### AI Agent Architecture

```yaml
# Location: src/agent/config/agent_config.yaml

agent:
  name: "Health Monitor AI"
  model: "databricks-meta-llama-3-3-70b-instruct"
  endpoint: "${MODEL_SERVING_ENDPOINT}"
  
  memory:
    short_term:
      type: "lakebase"
      ttl: "24h"
      table: "agent_memory_short_term"
    long_term:
      type: "lakebase"
      ttl: "365d"
      table: "agent_memory_long_term"
  
  tools:
    - name: get_cost_summary
      description: "Get cost metrics for a time period"
      source: src/agent/tools/cost_tools.py
    
    - name: get_failed_jobs
      description: "Get list of failed jobs with details"
      source: src/agent/tools/reliability_tools.py
    
    - name: analyze_root_cause
      description: "Perform AI root cause analysis"
      source: src/agent/tools/analysis_tools.py
    
    - name: apply_optimization
      description: "Apply a cost optimization recommendation"
      source: src/agent/tools/action_tools.py
    
    - name: search_web
      description: "Search web for documentation/solutions"
      source: src/agent/tools/utility_tools.py
      api: "tavily"
    
    - name: get_runbook
      description: "Retrieve relevant runbook from RAG"
      source: src/agent/tools/rag_tools.py
```

### Quick Actions

| Action | Agent Tool | Parameters |
|--------|------------|------------|
| "Show cost breakdown" | `get_cost_breakdown()` | time_range, group_by |
| "Why did this job fail?" | `analyze_job_failure()` | job_id |
| "What's causing the spike?" | `analyze_anomaly()` | metric_name, time_range |
| "Apply this fix" | `apply_remediation()` | recommendation_id |
| "Create an alert for this" | `create_alert()` | metric, threshold |

### Suggested Prompts

```python
# Location: src/agent/prompts/suggested_prompts.py

SUGGESTED_PROMPTS = {
    "cost": [
        "What's driving the cost increase this week?",
        "Show me cost optimization opportunities",
        "Compare cost to last month",
    ],
    "reliability": [
        "Why did the ETL pipeline fail?",
        "What jobs are at risk of SLA breach?",
        "Show me the retry patterns",
    ],
    "performance": [
        "What queries are running slow?",
        "Why is latency high right now?",
        "Show me the bottlenecks",
    ],
    "security": [
        "Any security risks I should know about?",
        "Who has access to PII tables?",
        "Show recent permission changes",
    ],
    "quality": [
        "What data quality issues exist?",
        "Which tables have freshness problems?",
        "Show me schema drift events",
    ],
}
```

---

## 🔔 Alert Center Screen

### Alert Configuration

```yaml
# Location: src/alerting/config/alert_rules.yaml

# Example alert rule
- rule_name: cost_spike_critical
  display_name: "Cost Spike - Critical"
  domain: cost
  severity: critical
  
  query: |
    SELECT 
      workspace_name,
      current_cost,
      baseline_cost,
      (current_cost - baseline_cost) / baseline_cost * 100 AS pct_increase
    FROM gold_health_monitor.fact_daily_cost_comparison
    WHERE pct_increase > 50
  
  condition:
    operator: "GREATER_THAN"
    value: 0
    aggregation: "COUNT"
  
  notifications:
    - channel: slack
      webhook: "${SLACK_WEBHOOK_COST}"
    - channel: email
      recipients: ["platform-team@company.com"]
    - channel: pagerduty
      service_key: "${PAGERDUTY_COST_KEY}"
      severity: critical
```

### Alert List Data

```sql
-- Location: src/semantic/tvfs/alerting/get_alerts.sql

SELECT 
    alert_id,
    rule_name,
    display_name,
    domain,
    severity,
    status,
    trigger_value,
    threshold_value,
    workspace_name,
    resource_name,
    triggered_at,
    acknowledged_at,
    acknowledged_by,
    resolved_at,
    notification_status
FROM gold_health_monitor.fact_alerts
WHERE triggered_at >= :start_time
ORDER BY triggered_at DESC
```

### Notification Channels

| Channel | Integration | Config Location |
|---------|-------------|-----------------|
| Slack | Webhook API | `src/alerting/channels/slack.py` |
| Email | SendGrid/SES | `src/alerting/channels/email.py` |
| PagerDuty | Events API v2 | `src/alerting/channels/pagerduty.py` |
| Microsoft Teams | Webhook | `src/alerting/channels/teams.py` |
| Custom Webhook | HTTP POST | `src/alerting/channels/webhook.py` |

---

## ⚙️ Settings Screen

### Workspace Configuration

| Setting | Storage | API |
|---------|---------|-----|
| Workspace list | `dim_workspace` | `GET /api/workspaces` |
| Data sources | `dim_data_source` | `GET /api/data-sources` |
| Sync status | `fact_sync_status` | `GET /api/sync-status` |

### Alert Preferences

| Setting | Storage | API |
|---------|---------|-----|
| Notification channels | `config_notification_channels` | `GET/POST /api/notifications` |
| Alert rules (enable/disable) | `config_alert_rules` | `PATCH /api/alerts/{id}` |
| Escalation policies | `config_escalation` | `GET/POST /api/escalations` |

### Team & Ownership

| Setting | Storage | API |
|---------|---------|-----|
| Teams | `dim_team` | `GET/POST /api/teams` |
| Ownership mappings | `fact_ownership_mapping` | `GET/POST /api/ownership` |
| RBAC roles | Unity Catalog + custom | `GET /api/roles` |

---

## 🎨 Component to Code Mapping

### Primitives → React Components

| Figma Component | React Component | File Path |
|-----------------|-----------------|-----------|
| Button | `<Button>` | `components/ui/button.tsx` |
| Badge | `<Badge>` | `components/ui/badge.tsx` |
| Card | `<Card>` | `components/ui/card.tsx` |
| Input | `<Input>` | `components/ui/input.tsx` |
| Select | `<Select>` | `components/ui/select.tsx` |
| Table | `<Table>` | `components/ui/table.tsx` |
| Chip | `<Chip>` | `components/ui/chip.tsx` |

### Composed → Custom Components

| Figma Component | React Component | Data Hook |
|-----------------|-----------------|-----------|
| KPITile | `<KPITile>` | `useKPIData()` |
| SignalRow | `<SignalRow>` | `useSignalData()` |
| InsightCard | `<InsightCard>` | `useAIInsight()` |
| ChartCard | `<ChartCard>` | `useChartData()` |
| AlertRow | `<AlertRow>` | `useAlertData()` |
| Sidebar | `<Sidebar>` | `useNavigation()` |
| TopBar | `<TopBar>` | `useGlobalFilters()` |

### Charts → Visualization Library

| Chart Type | Library | Component |
|------------|---------|-----------|
| Line/Area | Recharts | `<LineChart>` / `<AreaChart>` |
| Bar | Recharts | `<BarChart>` |
| Treemap | Recharts | `<Treemap>` |
| Heatmap | D3 or custom | `<Heatmap>` |
| Sparkline | Recharts | `<SparklineChart>` |

---

## 📁 File Structure Reference

```
src/
├── agent/
│   ├── config/
│   │   └── agent_config.yaml
│   ├── prompts/
│   │   ├── system_prompt.md
│   │   ├── domain_prompts/
│   │   └── suggested_prompts.py
│   ├── tools/
│   │   ├── cost_tools.py
│   │   ├── reliability_tools.py
│   │   ├── performance_tools.py
│   │   ├── security_tools.py
│   │   ├── quality_tools.py
│   │   ├── analysis_tools.py
│   │   ├── action_tools.py
│   │   └── utility_tools.py
│   └── memory/
│       └── lakebase_memory.py
│
├── semantic/
│   ├── tvfs/
│   │   ├── cost/
│   │   ├── reliability/
│   │   ├── performance/
│   │   ├── security/
│   │   ├── quality/
│   │   ├── alerting/
│   │   ├── explorer/
│   │   └── health/
│   ├── metric_views/
│   │   ├── cost_analytics.yaml
│   │   ├── reliability_analytics.yaml
│   │   └── ...
│   └── genie_spaces/
│       └── health_monitor_genie.yaml
│
├── ml/
│   ├── models/
│   │   ├── cost/
│   │   │   ├── anomaly_detector/
│   │   │   ├── forecaster/
│   │   │   └── optimizer/
│   │   ├── reliability/
│   │   ├── performance/
│   │   ├── security/
│   │   └── quality/
│   ├── features/
│   │   └── feature_tables.py
│   └── inference/
│       └── batch_inference.py
│
├── monitoring/
│   ├── metrics/
│   │   ├── aggregate_metrics.yaml
│   │   ├── derived_metrics.yaml
│   │   └── drift_metrics.yaml
│   └── monitors/
│       └── monitor_configs.yaml
│
├── alerting/
│   ├── config/
│   │   └── alert_rules.yaml
│   ├── channels/
│   │   ├── slack.py
│   │   ├── email.py
│   │   └── pagerduty.py
│   └── deployment/
│       └── deploy_alerts.py
│
└── gold_layer/
    ├── tables/
    │   ├── fact_daily_cost.sql
    │   ├── fact_job_runs.sql
    │   ├── fact_signals.sql
    │   └── ...
    └── setup/
        └── create_gold_tables.py
```

---

## 🔗 API Routes (Next.js)

```
app/
├── api/
│   ├── agent/
│   │   └── chat/
│   │       └── route.ts          # POST - AI chat endpoint
│   │
│   ├── signals/
│   │   ├── route.ts              # GET - List signals
│   │   └── [id]/
│   │       ├── route.ts          # GET/PATCH - Signal details
│   │       ├── acknowledge/
│   │       │   └── route.ts      # POST - Acknowledge
│   │       └── mute/
│   │           └── route.ts      # POST - Mute
│   │
│   ├── alerts/
│   │   ├── route.ts              # GET/POST - Alert rules
│   │   └── [id]/
│   │       └── route.ts          # GET/PATCH/DELETE
│   │
│   ├── metrics/
│   │   ├── health-score/
│   │   │   └── route.ts          # GET - Platform health
│   │   ├── cost/
│   │   │   └── route.ts          # GET - Cost metrics
│   │   ├── reliability/
│   │   │   └── route.ts          # GET - Reliability metrics
│   │   └── ...
│   │
│   └── export/
│       └── route.ts              # GET - Export data
│
├── (dashboard)/
│   ├── page.tsx                  # Executive Overview
│   ├── explorer/
│   │   └── page.tsx              # Global Explorer
│   ├── cost/
│   │   └── page.tsx              # Cost Domain
│   ├── reliability/
│   │   └── page.tsx              # Reliability Domain
│   ├── performance/
│   │   └── page.tsx              # Performance Domain
│   ├── security/
│   │   └── page.tsx              # Security Domain
│   ├── quality/
│   │   └── page.tsx              # Quality Domain
│   ├── signals/
│   │   └── [id]/
│   │       └── page.tsx          # Signal Detail
│   ├── chat/
│   │   └── page.tsx              # Chat Interface
│   ├── alerts/
│   │   └── page.tsx              # Alert Center
│   └── settings/
│       └── page.tsx              # Settings
│
└── layout.tsx                    # Root layout with sidebar
```

---

## ✅ Implementation Checklist

When implementing each Figma screen, ensure:

- [ ] **Data hooks** connected to correct TVFs/tables
- [ ] **Real-time updates** via SWR with appropriate refresh intervals
- [ ] **Error states** handled with fallback UI
- [ ] **Loading states** with skeletons
- [ ] **Empty states** with helpful messaging
- [ ] **Agent integration** for AI-powered features
- [ ] **Filter persistence** via URL params
- [ ] **Export functionality** for data tables
- [ ] **Accessibility** compliance (ARIA, keyboard nav)

---

## 📚 References

### Internal Documentation
- [Agent Framework Design](../../agent-framework-design/)
- [Dashboard Framework Design](../../dashboard-framework-design/)
- [ML Framework Design](../../ml-framework-design/)
- [Alerting Framework Design](../../alerting-framework-design/)

### External Documentation
- [Databricks SQL Warehouse API](https://docs.databricks.com/api/workspace/statementexecution)
- [Model Serving API](https://docs.databricks.com/api/workspace/servingendpoints)
- [Genie Spaces](https://docs.databricks.com/aws/en/genie/)

---

**This document should be updated whenever:**
1. New data sources are added
2. New TVFs or Metric Views are created
3. New ML models are deployed
4. Agent tools are added or modified
5. API routes change



