# Alert Management

> 3-tier alert interaction model extracted from `src/alerting/setup_alerting_tables.py`, `src/alerting/evaluate_alerts.py`, and `src/alerting/sync_sql_alerts.py`.

## Critical Truths

1. **No dedicated alert REST API.** There is no Flask/FastAPI/Gradio server for alerts. The frontend interacts with alerts via SQL against Delta tables and the Databricks SQL Alerts V2 API.
2. **`alert_context` does NOT exist** in the agent's `custom_inputs`. The agent has no special alert analysis mode. Alert analysis is done via natural language queries or by reading the pre-computed `ai_analysis` column.
3. **Three Delta tables** store alert data: `alert_configurations` (definitions), `alert_history` (evaluation results), `notification_destinations` (channels).

---

## 3-Tier Architecture

```
┌─────────────────────────────────────────────────────┐
│ Tier 3: AI Analysis                                 │
│   Pre-computed: alert_history.ai_analysis           │
│   Interactive:  Natural language query to agent      │
├─────────────────────────────────────────────────────┤
│ Tier 2: Real-Time States                            │
│   GET /api/2.0/alerts → live TRIGGERED/OK/UNKNOWN   │
├─────────────────────────────────────────────────────┤
│ Tier 1: Delta Table Snapshot                        │
│   alert_configurations (34 cols) + alert_history    │
│   (24 cols) + notification_destinations             │
└─────────────────────────────────────────────────────┘
```

---

## Tier 1: Delta Table Snapshot

### `alert_configurations` (34 columns)

Source: `setup_alerting_tables.py` line 157.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `alert_id` | `STRING` | NOT NULL | PK. Format: `COST-001`, `PERF-009`, etc. |
| `alert_name` | `STRING` | NOT NULL | Human-readable name |
| `alert_description` | `STRING` | yes | What the alert monitors |
| `agent_domain` | `STRING` | NOT NULL | `COST`, `SECURITY`, `PERFORMANCE`, `RELIABILITY`, `QUALITY` |
| `severity` | `STRING` | NOT NULL | `CRITICAL`, `WARNING`, `INFO` |
| `alert_query_template` | `STRING` | NOT NULL | SQL query template (supports `${catalog}`, `${gold_schema}`) |
| `query_source` | `STRING` | yes | `CUSTOM`, `TVF`, `METRIC_VIEW`, `MONITORING` |
| `source_artifact_name` | `STRING` | yes | Name of backing TVF/Metric View |
| `threshold_column` | `STRING` | NOT NULL | Column name in query results for evaluation |
| `threshold_operator` | `STRING` | NOT NULL | `>`, `<`, `>=`, `<=`, `=`, `!=`, etc. |
| `threshold_value_type` | `STRING` | NOT NULL | `DOUBLE`, `STRING`, `BOOLEAN` |
| `threshold_value_double` | `DOUBLE` | yes | Numeric threshold (when type=DOUBLE) |
| `threshold_value_string` | `STRING` | yes | String threshold (when type=STRING) |
| `threshold_value_bool` | `BOOLEAN` | yes | Boolean threshold (when type=BOOLEAN) |
| `empty_result_state` | `STRING` | NOT NULL | `OK`, `TRIGGERED`, `ERROR` (when query returns empty) |
| `aggregation_type` | `STRING` | yes | `NONE`, `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`, etc. |
| `schedule_cron` | `STRING` | NOT NULL | Quartz cron expression |
| `schedule_timezone` | `STRING` | NOT NULL | Java timezone ID |
| `pause_status` | `STRING` | NOT NULL | `UNPAUSED` or `PAUSED` |
| `is_enabled` | `BOOLEAN` | NOT NULL | Whether alert is deployed |
| `notification_channels` | `ARRAY<STRING>` | NOT NULL | Channel IDs or email addresses |
| `notify_on_ok` | `BOOLEAN` | NOT NULL | Notify on return to OK |
| `retrigger_seconds` | `INT` | yes | Cooldown before re-notify |
| `use_custom_template` | `BOOLEAN` | NOT NULL | Custom notification templates |
| `custom_subject_template` | `STRING` | yes | Mustache-supported subject |
| `custom_body_template` | `STRING` | yes | HTML body template |
| `owner` | `STRING` | NOT NULL | Alert owner |
| `created_by` | `STRING` | NOT NULL | Creator |
| `created_at` | `TIMESTAMP` | NOT NULL | Creation time |
| `updated_by` | `STRING` | yes | Last updater |
| `updated_at` | `TIMESTAMP` | yes | Last update time |
| `tags` | `MAP<STRING, STRING>` | yes | Free-form tags |
| `databricks_alert_id` | `STRING` | yes | Deployed SQL Alert v2 ID |
| `databricks_display_name` | `STRING` | yes | Deployed display name |
| `last_synced_at` | `TIMESTAMP` | yes | Last sync time |
| `last_sync_status` | `STRING` | yes | `CREATED`, `UPDATED`, `UNCHANGED`, `SKIPPED`, `ERROR` |
| `last_sync_error` | `STRING` | yes | Last sync error |

### `alert_history` (24 columns)

Source: `setup_alerting_tables.py` line 274.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `evaluation_id` | `STRING` | NOT NULL | PK. UUID for this evaluation. |
| `alert_id` | `STRING` | NOT NULL | FK to `alert_configurations.alert_id` |
| `alert_name` | `STRING` | NOT NULL | Denormalized name at evaluation time |
| `agent_domain` | `STRING` | NOT NULL | Denormalized domain |
| `severity` | `STRING` | NOT NULL | Denormalized severity |
| `evaluation_timestamp` | `TIMESTAMP` | NOT NULL | When evaluation ran |
| `evaluation_date` | `DATE` | NOT NULL | Partition column |
| `evaluation_status` | `STRING` | NOT NULL | `OK`, `TRIGGERED`, `ERROR` |
| `previous_status` | `STRING` | yes | For state change detection |
| `query_result_value_double` | `DOUBLE` | yes | Numeric result of query |
| `query_result_value_string` | `STRING` | yes | String result |
| `threshold_operator` | `STRING` | NOT NULL | Snapshot of operator |
| `threshold_value_type` | `STRING` | NOT NULL | Snapshot of threshold type |
| `threshold_value_double` | `DOUBLE` | yes | Snapshot of threshold |
| `threshold_value_string` | `STRING` | yes | Snapshot of threshold |
| `threshold_value_bool` | `BOOLEAN` | yes | Snapshot of threshold |
| `query_duration_ms` | `BIGINT` | yes | Query execution time |
| `error_message` | `STRING` | yes | Error details if status=ERROR |
| `ml_score` | `DOUBLE` | yes | ML anomaly score (0-1) |
| `ml_suppressed` | `BOOLEAN` | yes | Whether ML suppressed alert |
| `ai_analysis` | `STRING` | yes | FMAPI-generated analysis (TRIGGERED only) |
| `notification_sent` | `BOOLEAN` | yes | Whether notification was sent |
| `notification_channels_used` | `ARRAY<STRING>` | yes | Channels used |
| `record_created_timestamp` | `TIMESTAMP` | NOT NULL | Insert timestamp |

### Common Queries

**All enabled alerts with latest status:**

```sql
SELECT ac.alert_id, ac.alert_name, ac.agent_domain, ac.severity,
       ac.is_enabled, ac.pause_status,
       ah.evaluation_status, ah.evaluation_timestamp, ah.ai_analysis,
       ah.query_result_value_double, ah.threshold_value_double, ah.ml_score
FROM {catalog}.{gold_schema}.alert_configurations ac
LEFT JOIN (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY alert_id ORDER BY evaluation_timestamp DESC) as rn
  FROM {catalog}.{gold_schema}.alert_history
) ah ON ac.alert_id = ah.alert_id AND ah.rn = 1
WHERE ac.is_enabled = true
ORDER BY ac.agent_domain, ac.severity
```

**Currently triggered alerts:**

```sql
SELECT ah.alert_id, ah.alert_name, ah.agent_domain, ah.severity,
       ah.evaluation_status, ah.evaluation_timestamp,
       ah.query_result_value_double, ah.threshold_value_double,
       ah.ai_analysis, ah.ml_score
FROM {catalog}.{gold_schema}.alert_history ah
WHERE ah.evaluation_status = 'TRIGGERED'
  AND ah.evaluation_timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY ah.evaluation_timestamp DESC
```

**Alert evaluation history (for timeline view):**

```sql
SELECT evaluation_timestamp, evaluation_status, 
       query_result_value_double, threshold_value_double, ml_score
FROM {catalog}.{gold_schema}.alert_history
WHERE alert_id = 'COST-001'
ORDER BY evaluation_timestamp DESC
LIMIT 100
```

**Alerts by domain:**

```sql
SELECT agent_domain, severity,
       COUNT(*) as total_alerts,
       SUM(CASE WHEN is_enabled THEN 1 ELSE 0 END) as enabled_alerts
FROM {catalog}.{gold_schema}.alert_configurations
GROUP BY agent_domain, severity
ORDER BY agent_domain, severity
```

---

## Tier 2: Real-Time Alert States via V2 API

The Databricks SQL Alerts V2 API returns the live state of deployed alerts.

### Endpoint

```
GET https://<workspace-url>/api/2.0/alerts
Authorization: Bearer <token>
```

**This is NOT** `/api/2.0/sql/alerts` or `/api/2.0/sql/alerts-v2`. The correct endpoint is `/api/2.0/alerts`.

### Response

```json
{
  "alerts": [
    {
      "id": "abc123-def456",
      "display_name": "[CRITICAL] High DBU Cost Spike",
      "query_text": "SELECT ...",
      "state": {
        "value": "TRIGGERED",
        "last_triggered_at": "2026-03-11T10:30:00.000Z"
      },
      "schedule": {
        "quartz_cron_expression": "0 */15 * * * ?",
        "timezone_id": "America/Los_Angeles"
      },
      "owner": { "user_name": "admin@company.com" }
    }
  ]
}
```

### Matching V2 API to Delta Tables

The `alert_configurations.databricks_alert_id` column stores the V2 alert ID. Match with:

```sql
SELECT ac.alert_id, ac.alert_name, ac.databricks_alert_id
FROM {catalog}.{gold_schema}.alert_configurations ac
WHERE ac.databricks_alert_id IS NOT NULL
```

Then match by `databricks_alert_id = v2_alert.id` in the frontend.

### Rate Limits

- **GET requests**: More lenient than POST.
- **POST/PATCH requests**: 5 per minute per workspace.
- For a polling pattern, use a 30-60 second interval for GET requests.

---

## Tier 3: AI Analysis

### Source A: Pre-Computed AI Analysis

The `alert_history.ai_analysis` column contains a 2-3 sentence FMAPI-generated analysis. This is populated by `evaluate_alerts.py` (line 270-319) for TRIGGERED alerts only.

```sql
SELECT alert_id, alert_name, ai_analysis, evaluation_timestamp, ml_score
FROM {catalog}.{gold_schema}.alert_history
WHERE alert_id = 'COST-001'
  AND evaluation_status = 'TRIGGERED'
  AND ai_analysis IS NOT NULL
ORDER BY evaluation_timestamp DESC
LIMIT 1
```

**Characteristics:**
- Only generated for `TRIGGERED` alerts (not OK or ERROR).
- Max ~1000 characters (2-3 sentences).
- Available after the evaluator job runs (batch process, not real-time).
- Includes context from ML score when available.

### Source B: Interactive Agent Analysis

Send the alert details as a natural language query to the agent:

```json
{
  "input": [{ "role": "user", "content": "Alert COST-001 'High DBU Cost Spike' triggered. The observed value was $45,000 vs threshold $30,000 (operator >). What is causing the cost spike in the cost domain and what actions should I take?" }],
  "custom_inputs": {
    "user_id": "alice@company.com",
    "thread_id": "alert_investigation_001"
  }
}
```

The agent routes this to the cost domain Genie Space based on keyword matching. The Genie Space queries Gold layer tables for data-backed analysis.

**Characteristics:**
- Real-time, interactive.
- Can follow up with `thread_id` for deeper investigation.
- Quality depends on how much alert context is embedded in the query text.
- Agent does NOT have a special `alert_context` input field. All context must be in the natural language query.

### Recommended Hybrid Pattern

1. **Immediate**: Show `alert_history.ai_analysis` from the Delta table for quick context.
2. **On demand**: Offer a "Deep Dive" button that opens a chat session with the agent, pre-populated with the alert details in the query text.
3. **Investigation**: Use `thread_id` to maintain a multi-turn conversation about the alert.

```typescript
async function investigateAlert(alert: AlertHistoryRow) {
  const query = [
    `Alert ${alert.alert_id} "${alert.alert_name}" triggered.`,
    `Domain: ${alert.agent_domain}. Severity: ${alert.severity}.`,
    `Observed value: ${alert.query_result_value_double}`,
    `Threshold: ${alert.threshold_operator} ${alert.threshold_value_double}.`,
    alert.ai_analysis ? `Pre-analysis: ${alert.ai_analysis}` : "",
    `What is causing this and what should I do?`,
  ].filter(Boolean).join(" ");

  const response = await callAgent({
    input: [{ role: "user", content: query }],
    custom_inputs: {
      user_id: currentUser.email,
      thread_id: `alert_investigation_${alert.alert_id}`,
    },
  });

  return response;
}
```

---

## Frontend Alert Dashboard Data Flow

```
On page load:
  1. Tier 1: Query alert_configurations + alert_history (Delta tables via SQL Warehouse)
     → Populate alert list with definitions, latest statuses, ai_analysis
  
  2. Tier 2: GET /api/2.0/alerts
     → Overlay live states (TRIGGERED/OK/UNKNOWN) from V2 API
     → Match via databricks_alert_id
  
On 30-60s polling interval:
  3. Re-fetch Tier 2 (V2 API) for live state updates
  
On user clicks alert:
  4. Show Tier 1 data (definition + history) + Tier 3A (pre-computed ai_analysis)
  
On user clicks "Deep Dive":
  5. Open chat with agent (Tier 3B) with alert details pre-populated
```
