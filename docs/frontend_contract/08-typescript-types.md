# TypeScript Types

> Generated from the Python source code in `src/agents/setup/log_agent_model.py` and `src/alerting/setup_alerting_tables.py`.

## Agent Request / Response

```typescript
/** POST body for /invocations */
interface AgentRequest {
  input: InputMessage[];
  custom_inputs?: CustomInputs;
}

interface InputMessage {
  role: "user" | "assistant";
  content: string;
}

interface CustomInputs {
  /** Stable user identifier for long-term memory. Defaults to "anonymous". */
  user_id?: string;
  /** Session identifier. Also accepts conversation_id alias. Defaults to "single-turn". */
  session_id?: string;
  /** Short-term memory thread. Omit for new conversations. */
  thread_id?: string;
  /** Client-generated request ID for tracing. Auto-generated if omitted. */
  request_id?: string;
  /** Genie conversation IDs per domain for follow-ups. */
  genie_conversation_ids?: Record<string, string>;
}
```

```typescript
/** Response from predict() and final SSE event from predict_stream() */
interface AgentResponse {
  id: string;
  output: OutputItem[];
  custom_outputs: CustomOutputs;
}

interface OutputItem {
  type: "message";
  id: string;
  content: OutputContent[];
}

interface OutputContent {
  type: "output_text";
  text: string;
}

interface CustomOutputs {
  /** Classified domain: cost, security, performance, reliability, quality, unified, or cross_domain */
  domain: AgentDomain;
  /** genie, genie_multi, or error */
  source: "genie" | "genie_multi" | "error";
  /** Thread ID for short-term memory (always present, even on errors) */
  thread_id: string;
  /** Updated Genie conversation IDs per domain */
  genie_conversation_ids: Record<string, string>;
  /** "saved" when memory operations succeeded */
  memory_status?: "saved";
  /** Visualization suggestion for the frontend chart renderer */
  visualization_hint: VisualizationHint;
  /** Parsed tabular data. Array for single-domain, object for cross-domain, null on error/no data. */
  data: Record<string, any>[] | Record<string, Record<string, any>[]> | null;
  /** Error message (present when source is "error") */
  error?: string;
  /** List of domains queried (present only for cross-domain) */
  domains?: string[];
  /** Per-domain errors (present only for cross-domain) */
  cross_domain_errors?: Record<string, string> | null;
}

type AgentDomain =
  | "cost"
  | "security"
  | "performance"
  | "reliability"
  | "quality"
  | "unified"
  | "cross_domain";
```

---

## Streaming Events

```typescript
/** SSE event: text chunk (multiple per response, same item_id) */
interface StreamTextDelta {
  type: "response.output_text.delta";
  delta: string;
  item_id: string;
}

/** SSE event: text streaming complete (one per response) */
interface StreamItemDone {
  type: "response.output_item.done";
  item: OutputItem;
}

/** Final SSE event: full response with custom_outputs (same shape as AgentResponse) */
type StreamFinalEvent = AgentResponse;

/** Union of all possible SSE event payloads */
type StreamEvent = StreamTextDelta | StreamItemDone | StreamFinalEvent;

/** Type guard helpers */
function isTextDelta(event: StreamEvent): event is StreamTextDelta {
  return "type" in event && event.type === "response.output_text.delta";
}

function isItemDone(event: StreamEvent): event is StreamItemDone {
  return "type" in event && event.type === "response.output_item.done";
}

function isFinalResponse(event: StreamEvent): event is StreamFinalEvent {
  return "custom_outputs" in event;
}
```

---

## Visualization Hints (7 variants)

```typescript
type VisualizationHint =
  | LineChartHint
  | BarChartHint
  | PieChartHint
  | TableHint
  | TextHint
  | MultiDomainHint
  | ErrorHint;

interface LineChartHint {
  type: "line_chart";
  x_axis: string;
  y_axis: string[];
  title: string;
  reason: string;
  row_count: number;
  domain_preferences: DomainPreferences;
}

interface BarChartHint {
  type: "bar_chart";
  x_axis: string;
  y_axis: string;
  title: string;
  reason: string;
  row_count: number;
  domain_preferences: DomainPreferences;
}

interface PieChartHint {
  type: "pie_chart";
  label: string;
  value: string;
  title: string;
  reason: string;
  row_count: number;
  domain_preferences: DomainPreferences;
}

interface TableHint {
  type: "table";
  columns: string[];
  reason: string;
  row_count: number;
  domain_preferences: DomainPreferences;
}

interface TextHint {
  type: "text";
  reason: string;
  domain_preferences: DomainPreferences;
}

interface MultiDomainHint {
  type: "multi_domain";
  domains_analyzed: string[];
  reason: string;
}

interface ErrorHint {
  type: "error";
  reason: string;
}
```

---

## Domain Preferences

```typescript
type DomainPreferences =
  | CostPreferences
  | PerformancePreferences
  | SecurityPreferences
  | ReliabilityPreferences
  | QualityPreferences
  | UnifiedPreferences
  | DefaultPreferences;

interface CostPreferences {
  prefer_currency_format: true;
  color_scheme: "red_amber_green";
  default_sort: "descending";
  highlight_threshold: "high values";
  suggested_formats: { currency: "USD"; decimals: 2 };
}

interface PerformancePreferences {
  highlight_outliers: true;
  color_scheme: "sequential";
  default_sort: "descending";
  suggested_formats: { duration: "seconds"; percentage: true };
}

interface SecurityPreferences {
  highlight_critical: true;
  color_scheme: "red_amber_green";
  default_sort: "severity";
  severity_levels: ["critical", "high", "medium", "low"];
}

interface ReliabilityPreferences {
  show_thresholds: true;
  color_scheme: "red_amber_green";
  default_sort: "descending";
  suggested_formats: { rate: "percentage"; count: true };
}

interface QualityPreferences {
  show_percentages: true;
  color_scheme: "red_amber_green";
  default_sort: "quality_score";
  suggested_formats: { score: "percentage" };
}

interface UnifiedPreferences {
  color_scheme: "categorical";
  default_sort: "relevance";
  multi_domain: true;
}

interface DefaultPreferences {
  color_scheme: "default";
  default_sort: "ascending";
}
```

---

## Alert Configuration (34 fields)

```typescript
/** From alert_configurations Delta table (setup_alerting_tables.py line 157) */
interface AlertConfiguration {
  alert_id: string;
  alert_name: string;
  alert_description: string | null;
  agent_domain: AlertDomain;
  severity: AlertSeverity;

  alert_query_template: string;
  query_source: "CUSTOM" | "TVF" | "METRIC_VIEW" | "MONITORING" | null;
  source_artifact_name: string | null;

  threshold_column: string;
  threshold_operator: ThresholdOperator;
  threshold_value_type: "DOUBLE" | "STRING" | "BOOLEAN";
  threshold_value_double: number | null;
  threshold_value_string: string | null;
  threshold_value_bool: boolean | null;

  empty_result_state: EvaluationStatus;
  aggregation_type: AggregationType | null;

  schedule_cron: string;
  schedule_timezone: string;
  pause_status: "UNPAUSED" | "PAUSED";
  is_enabled: boolean;

  notification_channels: string[];
  notify_on_ok: boolean;
  retrigger_seconds: number | null;

  use_custom_template: boolean;
  custom_subject_template: string | null;
  custom_body_template: string | null;

  owner: string;
  created_by: string;
  created_at: string;
  updated_by: string | null;
  updated_at: string | null;
  tags: Record<string, string> | null;

  databricks_alert_id: string | null;
  databricks_display_name: string | null;
  last_synced_at: string | null;
  last_sync_status: SyncStatus | null;
  last_sync_error: string | null;
}

type AlertDomain = "COST" | "SECURITY" | "PERFORMANCE" | "RELIABILITY" | "QUALITY";
type AlertSeverity = "CRITICAL" | "WARNING" | "INFO";
type ThresholdOperator = ">" | "<" | ">=" | "<=" | "=" | "==" | "!=" | "<>";
type EvaluationStatus = "OK" | "TRIGGERED" | "ERROR";
type AggregationType =
  | "NONE" | "SUM" | "COUNT" | "COUNT_DISTINCT"
  | "AVG" | "MEDIAN" | "MIN" | "MAX" | "STDDEV";
type SyncStatus = "CREATED" | "UPDATED" | "UNCHANGED" | "SKIPPED" | "ERROR";
```

---

## Alert History (24 fields)

```typescript
/** From alert_history Delta table (setup_alerting_tables.py line 274) */
interface AlertHistory {
  evaluation_id: string;
  alert_id: string;
  alert_name: string;
  agent_domain: AlertDomain;
  severity: AlertSeverity;

  evaluation_timestamp: string;
  evaluation_date: string;
  evaluation_status: EvaluationStatus;
  previous_status: EvaluationStatus | null;

  query_result_value_double: number | null;
  query_result_value_string: string | null;

  threshold_operator: ThresholdOperator;
  threshold_value_type: "DOUBLE" | "STRING" | "BOOLEAN";
  threshold_value_double: number | null;
  threshold_value_string: string | null;
  threshold_value_bool: boolean | null;

  query_duration_ms: number | null;
  error_message: string | null;

  ml_score: number | null;
  ml_suppressed: boolean | null;

  /** FMAPI-generated analysis. Only populated for TRIGGERED alerts. */
  ai_analysis: string | null;

  notification_sent: boolean | null;
  notification_channels_used: string[] | null;

  record_created_timestamp: string;
}
```

---

## V2 Alert API Response

```typescript
/** GET /api/2.0/alerts response */
interface AlertsV2Response {
  alerts: AlertV2[];
}

interface AlertV2 {
  id: string;
  display_name: string;
  query_text: string;
  state: AlertV2State;
  schedule: {
    quartz_cron_expression: string;
    timezone_id: string;
  };
  owner: {
    user_name: string;
  };
}

interface AlertV2State {
  value: "TRIGGERED" | "OK" | "UNKNOWN";
  last_triggered_at?: string;
}
```

---

## Utility Types

```typescript
/** Combined alert view: config + latest history + live V2 state */
interface AlertDashboardRow {
  config: AlertConfiguration;
  latestHistory: AlertHistory | null;
  liveState: AlertV2State | null;
}

/** Genie conversation IDs map (domain -> conversation UUID) */
type GenieConversationIds = Record<string, string>;

/** Short helper for custom_inputs construction */
function buildCustomInputs(
  userId: string,
  threadId?: string | null,
  genieConvIds?: GenieConversationIds
): CustomInputs {
  return {
    user_id: userId,
    ...(threadId ? { thread_id: threadId } : {}),
    genie_conversation_ids: genieConvIds ?? {},
  };
}
```
