# Quickstart: Working Examples for All 6 Patterns

> Copy-paste-ready `curl` and `fetch` examples. Replace `<ENDPOINT_URL>` and `<TOKEN>` with real values.

**Endpoint URL format:**

```
https://<workspace>.cloud.databricks.com/serving-endpoints/<endpoint-name>/invocations
```

---

## Pattern 0: Long-Term Memory (Automatic)

Pass a stable `user_id`. The agent handles preference loading and insight saving automatically.

```bash
curl -X POST "${ENDPOINT_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{ "role": "user", "content": "What are the top cost drivers?" }],
    "custom_inputs": {
      "user_id": "alice@company.com"
    }
  }'
```

Response includes `memory_status` confirming automatic save:

```json
{
  "id": "resp_abc123def456",
  "output": [{ "type": "message", "content": [{ "type": "output_text", "text": "Based on your usage..." }] }],
  "custom_outputs": {
    "domain": "cost",
    "source": "genie",
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "genie_conversation_ids": { "cost": "genie_conv_abc" },
    "memory_status": "saved",
    "visualization_hint": { "type": "bar_chart", "x_axis": "workspace_name", "y_axis": "total_cost" },
    "data": [{ "workspace_name": "prod-ws", "total_cost": 45000 }]
  }
}
```

No additional calls needed for long-term memory. If `user_id` is omitted, it defaults to `"anonymous"` and no personalization occurs.

---

## Pattern 1: Short-Term Memory via thread_id

### First message (no thread_id)

```bash
curl -X POST "${ENDPOINT_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{ "role": "user", "content": "Show me cost trends for the last 7 days" }],
    "custom_inputs": {
      "user_id": "alice@company.com"
    }
  }'
```

Response returns a new `thread_id`:

```json
{
  "custom_outputs": {
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "genie_conversation_ids": { "cost": "genie_conv_abc" }
  }
}
```

### Follow-up message (pass thread_id back)

```bash
curl -X POST "${ENDPOINT_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{ "role": "user", "content": "Now break that down by workspace" }],
    "custom_inputs": {
      "user_id": "alice@company.com",
      "thread_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }'
```

The agent loads conversation history from Lakebase and has context of the prior exchange.

---

## Pattern 2: Continue Genie Conversations

### First query (no genie_conversation_ids)

```bash
curl -X POST "${ENDPOINT_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{ "role": "user", "content": "What is the total spend this month?" }],
    "custom_inputs": {
      "user_id": "alice@company.com",
      "genie_conversation_ids": {}
    }
  }'
```

Response starts a new Genie conversation:

```json
{
  "custom_outputs": {
    "domain": "cost",
    "genie_conversation_ids": { "cost": "genie_conv_123abc" }
  }
}
```

### Follow-up in same Genie conversation

```bash
curl -X POST "${ENDPOINT_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{ "role": "user", "content": "Filter that to just the analytics workspace" }],
    "custom_inputs": {
      "user_id": "alice@company.com",
      "thread_id": "550e8400-e29b-41d4-a716-446655440000",
      "genie_conversation_ids": { "cost": "genie_conv_123abc" }
    }
  }'
```

The agent uses `create_message_and_wait` instead of `start_conversation_and_wait`, continuing the same Genie conversation for context-aware follow-ups.

---

## Pattern 3: Streaming Responses

```bash
curl -N -X POST "${ENDPOINT_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "input": [{ "role": "user", "content": "Show me the top 5 most expensive jobs" }],
    "custom_inputs": {
      "user_id": "alice@company.com"
    }
  }'
```

SSE event stream:

```
event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "## Cost Analysis\n\n", "item_id": "item_abc123"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "Here are the top 5 most expensive jobs...", "item_id": "item_abc123"}

event: response.output_item.done
data: {"type": "response.output_item.done", "item": {"type": "message", "id": "item_abc123", "content": [{"type": "output_text", "text": "## Cost Analysis\n\nHere are the top 5 most expensive jobs..."}]}}

data: {"id": "resp_abc123def456", "output": [...], "custom_outputs": {"domain": "cost", "thread_id": "...", "visualization_hint": {"type": "bar_chart"}, "data": [...]}}
```

**JavaScript `fetch` example:**

```javascript
const response = await fetch(ENDPOINT_URL, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
  },
  body: JSON.stringify({
    input: [{ role: "user", content: query }],
    custom_inputs: { user_id: userId, thread_id: threadId },
  }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n");
  buffer = lines.pop();

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const payload = JSON.parse(line.slice(6));

      if (payload.type === "response.output_text.delta") {
        appendToChat(payload.delta);
      } else if (payload.type === "response.output_item.done") {
        // Full text available in payload.item.content[0].text
      } else if (payload.custom_outputs) {
        // Final event with custom_outputs
        handleCustomOutputs(payload.custom_outputs);
      }
    }
  }
}
```

---

## Pattern 4: Alert Analysis (Triggered Alert)

### Approach A: Read pre-computed AI analysis from Delta table

```sql
SELECT alert_id, alert_name, evaluation_status, ai_analysis,
       query_result_value_double, threshold_value_double,
       evaluation_timestamp, ml_score
FROM <catalog>.<gold_schema>.alert_history
WHERE alert_id = 'COST-001'
  AND evaluation_status = 'TRIGGERED'
ORDER BY evaluation_timestamp DESC
LIMIT 1
```

The `ai_analysis` column contains a 2-3 sentence FMAPI-generated analysis. Only populated for `TRIGGERED` alerts.

### Approach B: Ask the agent for interactive analysis

```bash
curl -X POST "${ENDPOINT_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{ "role": "user", "content": "Alert COST-001 High DBU Cost Spike triggered. Value was $45,000 vs threshold $30,000. What is causing the cost spike and what should I do?" }],
    "custom_inputs": {
      "user_id": "alice@company.com",
      "thread_id": "alert_investigation_thread_1"
    }
  }'
```

The agent routes this to the cost domain Genie Space based on keyword matching and returns data-backed analysis. Use `thread_id` to ask follow-up questions about the same alert.

### Approach C: Hybrid (recommended)

1. Display `alert_history.ai_analysis` immediately for quick context.
2. Offer a "Deep Dive" button that sends the alert details to the agent.
3. Use `thread_id` to maintain an investigation conversation.

---

## Pattern 5: 3-Tier Alert Checking

### Tier 1: Delta table snapshot

```sql
-- All enabled alerts with latest evaluation status
SELECT ac.alert_id, ac.alert_name, ac.agent_domain, ac.severity,
       ah.evaluation_status, ah.evaluation_timestamp, ah.ai_analysis,
       ah.query_result_value_double, ah.ml_score
FROM <catalog>.<gold_schema>.alert_configurations ac
LEFT JOIN (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY alert_id ORDER BY evaluation_timestamp DESC) as rn
  FROM <catalog>.<gold_schema>.alert_history
) ah ON ac.alert_id = ah.alert_id AND ah.rn = 1
WHERE ac.is_enabled = true
ORDER BY ac.agent_domain, ac.severity
```

### Tier 2: Real-time alert states

```bash
curl -X GET "https://<workspace-url>/api/2.0/alerts" \
  -H "Authorization: Bearer ${TOKEN}"
```

Response:

```json
{
  "alerts": [{
    "id": "abc123",
    "display_name": "[CRITICAL] High DBU Cost Spike",
    "state": { "value": "TRIGGERED" },
    "last_triggered_at": "2026-03-11T10:30:00Z"
  }]
}
```

Match to Delta table via `alert_configurations.databricks_alert_id`.

### Tier 3: AI analysis

Read `alert_history.ai_analysis` for pre-computed analysis, or send to agent for interactive investigation (see Pattern 4 above).
