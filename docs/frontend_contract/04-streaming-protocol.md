# Streaming Protocol

> Extracted from `predict_stream()` at `src/agents/setup/log_agent_model.py` line 2906.

## HTTP Request

The streaming request uses the same endpoint and body as non-streaming. The difference is the `Accept` header:

```
POST https://<workspace>.cloud.databricks.com/serving-endpoints/<endpoint-name>/invocations
Authorization: Bearer <token>
Content-Type: application/json
Accept: text/event-stream
```

Request body is identical to `predict()`:

```json
{
  "input": [{ "role": "user", "content": "Show me cost trends" }],
  "custom_inputs": {
    "user_id": "alice@company.com",
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "genie_conversation_ids": { "cost": "genie_conv_abc" }
  }
}
```

---

## SSE Event Stream

The response is a Server-Sent Events (SSE) stream. The agent yields 3 event types in order:

### Event Type 1: `response.output_text.delta` (multiple)

Text chunks streamed incrementally. All deltas for a single response share the same `item_id`.

```
event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "🔍 Querying Cost Genie Space...\n\n", "item_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "## Cost Analysis\n\nThe top 5 most expensive jobs are:", "item_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "\n\n| Job Name | Cost |\n|---|---|\n| etl_main | $12,500 |", "item_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"}
```

**Chunking strategy:** The agent splits the response by double newlines (`\n\n`) and streams each paragraph as a separate delta. The initial "thinking" message (e.g., "Querying Cost Genie Space...") is always the first delta.

### Event Type 2: `response.output_item.done` (one)

Signals that text streaming is complete. Contains the full aggregated text.

```
event: response.output_item.done
data: {"type": "response.output_item.done", "item": {"type": "message", "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "content": [{"type": "output_text", "text": "🔍 Querying Cost Genie Space...\n\n## Cost Analysis\n\nThe top 5 most expensive jobs are:\n\n| Job Name | Cost |\n|---|---|\n| etl_main | $12,500 |"}]}}
```

### Event Type 3: `ResponsesAgentResponse` (one, final)

The last event in the stream. Contains `custom_outputs` with `thread_id`, `genie_conversation_ids`, `visualization_hint`, and `data`. This is the same shape as the non-streaming `predict()` response.

```
data: {"id": "resp_abc123def456", "output": [{"type": "message", "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "content": [{"type": "output_text", "text": "🔍 Querying Cost Genie Space...\n\n## Cost Analysis\n\n..."}]}], "custom_outputs": {"domain": "cost", "source": "genie", "thread_id": "550e8400-e29b-41d4-a716-446655440000", "genie_conversation_ids": {"cost": "genie_conv_abc"}, "memory_status": "saved", "visualization_hint": {"type": "bar_chart", "x_axis": "job_name", "y_axis": "total_cost", "title": "Top 5 Jobs by Total Cost", "reason": "Top N comparison query", "row_count": 5, "domain_preferences": {"prefer_currency_format": true}}, "data": [{"job_name": "etl_main", "total_cost": 12500}]}}
```

**The frontend MUST wait for this final event** to get `custom_outputs`. Do not render charts or update state until this event arrives.

---

## Cross-Domain Streaming

Cross-domain queries emit additional progress deltas:

```
event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "🔀 Analyzing across multiple domains: Cost, Reliability...\n\n", "item_id": "item_123"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "✓ Cost data retrieved\n", "item_id": "item_123"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "✓ Reliability data retrieved\n", "item_id": "item_123"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "\n🧠 Synthesizing insights...\n\n", "item_id": "item_123"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "## Cross-Domain Analysis\n\n...", "item_id": "item_123"}
```

The final `ResponsesAgentResponse` for cross-domain will have `domain: "cross_domain"` and `data` as an object keyed by domain name.

---

## Error Streaming

When a Genie query fails, the stream still emits all 3 event types:

```
event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "🔍 Querying Cost Genie Space...\n\n", "item_id": "item_456"}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "delta": "\n\n## Genie Query Failed\n\n**Domain:** cost\n**Error:** Connection timeout...", "item_id": "item_456"}

event: response.output_item.done
data: {"type": "response.output_item.done", "item": {"type": "message", "id": "item_456", "content": [{"type": "output_text", "text": "...full error text..."}]}}

data: {"id": "resp_xyz", "output": [...], "custom_outputs": {"domain": "cost", "source": "error", "error": "Connection timeout", "thread_id": "...", "visualization_hint": {"type": "error", "reason": "Query failed"}, "data": null}}
```

---

## Frontend Implementation

### Using `fetch` + `ReadableStream`

```typescript
async function streamAgentQuery(
  endpointUrl: string,
  token: string,
  query: string,
  customInputs: Record<string, any>
): Promise<void> {
  const response = await fetch(endpointUrl, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
    },
    body: JSON.stringify({
      input: [{ role: "user", content: query }],
      custom_inputs: customInputs,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop()!;

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;

      const raw = line.slice(6);
      if (raw === "[DONE]") continue;

      let payload: any;
      try {
        payload = JSON.parse(raw);
      } catch {
        continue;
      }

      if (payload.type === "response.output_text.delta") {
        // Append text chunk to chat UI
        fullText += payload.delta;
        onTextDelta(payload.delta);

      } else if (payload.type === "response.output_item.done") {
        // Full text is in payload.item.content[0].text
        // Can be used as fallback if deltas were missed
        onTextComplete(payload.item.content[0].text);

      } else if (payload.custom_outputs) {
        // Final ResponsesAgentResponse -- extract state
        const outputs = payload.custom_outputs;

        // Update thread_id for next request
        updateThreadId(outputs.thread_id);

        // Update Genie conversation IDs for next request
        updateGenieConversationIds(outputs.genie_conversation_ids);

        // Render visualization if data exists
        if (outputs.visualization_hint && outputs.data) {
          renderVisualization(outputs.visualization_hint, outputs.data);
        }
      }
    }
  }
}
```

### Using `EventSource` (simpler, limited)

`EventSource` does not support POST requests or custom headers natively. Use an `EventSource` polyfill (e.g., `eventsource-parser`) or the `fetch` approach above.

---

## Key Implementation Notes

1. **Same input format**: Streaming uses the exact same request body as non-streaming. The only difference is the `Accept: text/event-stream` header.
2. **Memory is loaded identically**: `user_id`, `thread_id`, `genie_conversation_ids`, and `user_preferences` are all extracted and loaded the same way in both paths.
3. **Wait for the final event**: `custom_outputs` (with visualization, data, memory state) only appear in the last SSE event. Do not render charts until that arrives.
4. **`item_id` is consistent**: All delta events for a single response share the same `item_id`. Use this to group chunks if needed.
5. **Errors stream too**: Error responses still emit all 3 event types, so the same parsing logic works for both success and error cases.
