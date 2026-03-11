# Agent API Reference

> Exact request/response contract extracted from `predict()` in `src/agents/setup/log_agent_model.py`.

## Endpoint

```
POST https://<workspace>.cloud.databricks.com/serving-endpoints/<endpoint-name>/invocations
```

## Request Format

The agent implements `mlflow.pyfunc.ResponsesAgent`, which uses the `input` key (not `messages`).

```json
{
  "input": [
    { "role": "user", "content": "What are the top cost drivers this month?" }
  ],
  "custom_inputs": {
    "user_id": "alice@company.com",
    "session_id": "session_abc123",
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "request_id": "req_xyz",
    "genie_conversation_ids": {
      "cost": "genie_conv_abc",
      "security": "genie_conv_def"
    }
  }
}
```

### `input` (required)

Array of message objects. The agent extracts the **last user message** as the query.

| Field | Type | Required | Description |
|---|---|---|---|
| `role` | `string` | yes | `"user"` or `"assistant"` |
| `content` | `string` | yes | The message text |

The agent also accepts a plain string for `input`, a dict with `content`/`query`/`text` keys, or the legacy `messages` key.

### `custom_inputs` (optional)

All fields are optional. Missing fields use safe defaults.

| Field | Type | Default | Description |
|---|---|---|---|
| `user_id` | `string` | `"anonymous"` | Stable user identifier for long-term memory. If omitted, no personalization occurs. |
| `session_id` | `string` | `"single-turn"` | Session identifier. Also accepts `conversation_id`. |
| `thread_id` | `string` | auto-generated UUID | Short-term memory thread. Omit for new conversations; pass back for follow-ups. |
| `request_id` | `string` | auto-generated 8-char UUID | Client-generated request ID for tracing. |
| `genie_conversation_ids` | `object` | `{}` | Dict mapping domain names to Genie conversation IDs. Pass back from previous response for follow-ups. |

---

## Response Format

All responses are `ResponsesAgentResponse` objects.

```json
{
  "id": "resp_abc123def456",
  "output": [
    {
      "type": "message",
      "id": "item_uuid",
      "content": [
        {
          "type": "output_text",
          "text": "## Cost Analysis\n\nHere are the top cost drivers..."
        }
      ]
    }
  ],
  "custom_outputs": {
    "domain": "cost",
    "source": "genie",
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "genie_conversation_ids": { "cost": "genie_conv_abc" },
    "memory_status": "saved",
    "visualization_hint": {
      "type": "bar_chart",
      "x_axis": "workspace_name",
      "y_axis": "total_cost",
      "title": "Top Workspace by Total Cost",
      "reason": "Top N comparison query",
      "row_count": 10,
      "domain_preferences": { "prefer_currency_format": true, "color_scheme": "red_amber_green" }
    },
    "data": [
      { "workspace_name": "prod-analytics", "total_cost": 45000.50 },
      { "workspace_name": "prod-ml", "total_cost": 32000.75 }
    ]
  }
}
```

### `output` (always present)

Array containing one message item:

| Field | Type | Description |
|---|---|---|
| `output[0].type` | `string` | Always `"message"` |
| `output[0].id` | `string` | UUID for the output item |
| `output[0].content[0].type` | `string` | Always `"output_text"` |
| `output[0].content[0].text` | `string` | The full response text (Markdown) |

### `custom_outputs` (always present)

| Field | Type | Always Present | Description |
|---|---|---|---|
| `domain` | `string` | yes | Classified domain: `"cost"`, `"security"`, `"performance"`, `"reliability"`, `"quality"`, `"unified"`, or `"cross_domain"` |
| `source` | `string` | yes | `"genie"`, `"genie_multi"`, or `"error"` |
| `thread_id` | `string` | yes | Thread ID for short-term memory (always returned, even on errors) |
| `genie_conversation_ids` | `object` | yes | Updated dict mapping domain to Genie conversation ID |
| `memory_status` | `string` | on success | `"saved"` when memory operations succeeded |
| `visualization_hint` | `object` | yes | Visualization suggestion (see [06-visualization-contract.md](06-visualization-contract.md)) |
| `data` | `array\|object\|null` | yes | Parsed tabular data, or `null` if none |
| `error` | `string` | on error | Error message when `source` is `"error"` |
| `domains` | `array` | cross-domain only | List of domains queried (e.g., `["cost", "performance"]`) |
| `cross_domain_errors` | `object\|null` | cross-domain only | Dict of per-domain errors if any failed |

---

## Response Shapes by Query Type

### Single-Domain Response

Query: "What is our total spend this month?"

```json
{
  "custom_outputs": {
    "domain": "cost",
    "source": "genie",
    "thread_id": "...",
    "genie_conversation_ids": { "cost": "genie_conv_abc" },
    "memory_status": "saved",
    "visualization_hint": { "type": "bar_chart", "x_axis": "sku_name", "y_axis": "total_cost" },
    "data": [{ "sku_name": "JOBS_COMPUTE", "total_cost": 15000 }]
  }
}
```

### Cross-Domain Response

Query: "Compare our cost trends with job reliability"

```json
{
  "custom_outputs": {
    "domain": "cross_domain",
    "domains": ["cost", "reliability"],
    "source": "genie_multi",
    "thread_id": "...",
    "genie_conversation_ids": { "cost": "conv_1", "reliability": "conv_2" },
    "memory_status": "saved",
    "visualization_hint": {
      "type": "multi_domain",
      "domains_analyzed": ["cost", "reliability"],
      "reason": "Cross-domain analysis combining multiple data sources"
    },
    "data": {
      "cost": [{ "usage_date": "2026-03-10", "total_cost": 5000 }],
      "reliability": [{ "job_name": "etl_pipeline", "success_rate": 0.95 }]
    },
    "cross_domain_errors": null
  }
}
```

For cross-domain responses, `data` is an **object** keyed by domain name, not an array.

### Error Response

Query routed to unconfigured Genie Space, or Genie query fails.

```json
{
  "custom_outputs": {
    "domain": "cost",
    "source": "error",
    "error": "Connection timeout to Genie Space",
    "thread_id": "...",
    "visualization_hint": { "type": "error", "reason": "Query failed" },
    "data": null
  }
}
```

Errors always include `thread_id` for memory continuity. The response text (`output[0].content[0].text`) contains a Markdown-formatted error message with troubleshooting guidance.

---

## Domain Routing

The agent routes queries using keyword matching in `_classify_domains()`. The 6 supported domains and their trigger keywords:

| Domain | Example Triggers |
|---|---|
| `cost` | cost, spend, billing, dbu, price, budget, expensive |
| `security` | security, audit, access, permission, compliance, gdpr |
| `performance` | performance, slow, latency, duration, speed, optimization |
| `reliability` | reliability, failure, success rate, uptime, sla, availability |
| `quality` | quality, data quality, freshness, completeness, accuracy |
| `unified` | (fallback when no domain keywords match) |

Cross-domain queries are detected when multiple domains are matched AND the query contains cross-domain indicators like "and", "vs", "compare", "holistic", or "comprehensive".

---

## Rate Limits and Timeouts

| Setting | Value | Source |
|---|---|---|
| Genie query timeout | ~120 seconds (SDK default) | `start_conversation_and_wait` / `create_message_and_wait` |
| Memory operations | Non-blocking, failures are non-fatal | Wrapped in try/except |
| Visualization analysis | Non-blocking, failures are non-fatal | Wrapped in try/except |

If a Genie query times out, the agent returns an error response (never hallucinates data).
