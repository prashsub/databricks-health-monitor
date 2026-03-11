# Memory and Context Management

> Covers all 3 state mechanisms: long-term memory (`user_id`), short-term memory (`thread_id`), and Genie conversation continuity (`genie_conversation_ids`).

## Overview

The agent manages state across three layers, each with different lifetimes and frontend responsibilities:

| Layer | Key | Lifetime | Frontend Responsibility | Backend Storage |
|---|---|---|---|---|
| **Long-term memory** | `user_id` | 365 days | Pass stable `user_id`. Everything else is automatic. | `DatabricksStore` (Lakebase Postgres + vector embeddings) |
| **Short-term memory** | `thread_id` | 24 hours | Store `thread_id` from response; pass it back on follow-ups. | `CheckpointSaver` (Lakebase Postgres) |
| **Genie conversations** | `genie_conversation_ids` | Session-scoped | Store dict from response; pass it back on follow-ups. | Genie SDK (stateless -- frontend is the source of truth) |

**Critical warning:** Model Serving replicas do NOT share state. The agent code explicitly notes: *"don't assume the same replica handles all requests."* This is why `thread_id` and `genie_conversation_ids` must round-trip through the frontend.

---

## Section 0: Long-Term Memory via `user_id`

**Code source:** `_get_user_preferences()` (line 586), `_extract_and_save_insights()` (line 703), `_save_user_insight()` (line 652).

### Frontend Responsibility

Pass a stable `user_id` on every request. That is the only requirement. The agent handles everything else automatically.

### Sequence Diagram

```
Frontend                               Agent
   |                                      |
   |-- POST /invocations ----------------->|
   |   custom_inputs: {                   |
   |     user_id: "alice@company.com"     |
   |   }                                  |
   |                                      |  1. _get_user_preferences("alice@company.com", query)
   |                                      |     -> semantic search in DatabricksStore
   |                                      |     -> returns {preferred_domains, recent_topics}
   |                                      |
   |                                      |  2. Process query (with user context influencing response)
   |                                      |
   |                                      |  3. _extract_and_save_insights("alice@company.com", ...)
   |                                      |     -> saves topic_{domain}_{hash} record
   |                                      |     -> saves domain_{domain} preference record
   |                                      |
   |<-- Response --------------------------| 
   |   custom_outputs: {                  |
   |     memory_status: "saved"           |
   |   }                                  |
```

### Key Facts

- **`user_id` extraction** (line 2454): `custom_inputs.get("user_id", os.environ.get("USER_ID", "anonymous"))`
- **Default**: If `user_id` is omitted, defaults to `"anonymous"` -- agent works but with no personalization.
- **Namespace isolation**: Each user has a separate namespace `("health_monitor_users", sanitized_user_id)` where `@` becomes `-at-`, `.` becomes `-`.
- **Semantic search**: The agent uses vector embeddings to find memories relevant to the current query (up to 5 results).
- **What gets auto-saved per interaction** (line 721-744):
  - `topic_{domain}_{hash}`: query summary, domain, response length
  - `domain_{domain}`: domain usage frequency
- **`memory_status`**: Returned in `custom_outputs` as `"saved"` on success. The frontend can display this but needs no action on it.
- **Non-fatal failures**: Memory load/save errors are caught silently (lines 2496, 2760-2761). The agent still returns a normal response.
- **TTL**: 365 days.

### What Frontend Does NOT Need to Do

- No explicit save, delete, list, or search calls for memories.
- No memory key tracking.
- No memory lifecycle management.
- No retrieval requests.

---

## Section 1: Short-Term Memory via `thread_id`

**Code source:** `_resolve_thread_id()` (line 400), `_get_conversation_history()` (line 422), `_save_to_short_term_memory()`.

### Frontend Responsibility

1. On first request, omit `thread_id` (or send empty string).
2. Store `thread_id` from response `custom_outputs`.
3. Pass it back on every follow-up request in the same conversation.

### Sequence Diagram

```
Frontend                               Agent Serving Endpoint
   |                                      |
   |-- POST /invocations ----------------->|  (new conversation)
   |   custom_inputs: {}                  |
   |                                      |  _resolve_thread_id(None)
   |                                      |  -> generates UUID "thread_abc"
   |                                      |  Saves exchange to Lakebase CheckpointSaver
   |<-- Response --------------------------| 
   |   custom_outputs: {                  |
   |     thread_id: "thread_abc"          |
   |   }                                  |
   |                                      |
   |   ** Frontend stores thread_id **    |
   |                                      |
   |-- POST /invocations ----------------->|  (follow-up)
   |   custom_inputs: {                   |
   |     thread_id: "thread_abc"          |
   |   }                                  |  _resolve_thread_id("thread_abc")
   |                                      |  -> returns "thread_abc"
   |                                      |  _get_conversation_history("thread_abc")
   |                                      |  -> loads prior messages from CheckpointSaver
   |<-- Response --------------------------| 
   |   custom_outputs: {                  |
   |     thread_id: "thread_abc"          |  (same thread_id echoed back)
   |   }                                  |
```

### Key Facts

- **Resolution** (line 400-420): If `custom_inputs["thread_id"]` is present and truthy, use it. Otherwise, generate `uuid.uuid4()`.
- **Storage**: `CheckpointSaver(instance_name=self.lakebase_instance_name)` writes to Lakebase Postgres.
- **TTL**: 24 hours (configured in `initialize_lakebase_tables.py`).
- **Always returned**: `thread_id` is ALWAYS present in `custom_outputs`, even on error responses.
- **Non-fatal**: If CheckpointSaver fails, the agent logs a warning and proceeds without conversation history.

### Frontend State Management

```typescript
// React example
const [threadId, setThreadId] = useState<string | null>(null);

async function sendMessage(query: string) {
  const response = await callAgent({
    input: [{ role: "user", content: query }],
    custom_inputs: {
      user_id: currentUser.email,
      ...(threadId ? { thread_id: threadId } : {}),
    },
  });

  // Always update threadId from response
  setThreadId(response.custom_outputs.thread_id);
}

function startNewConversation() {
  setThreadId(null); // Next request will get a fresh thread_id
}
```

---

## Section 2: Genie Conversation Continuity via `genie_conversation_ids`

**Code source:** Extraction at line 2464-2471, follow-up at line 2726-2747, `_query_genie()` at line 981, `_follow_up_genie_internal()` at line 1729.

### Frontend Responsibility

1. On first request, send `genie_conversation_ids: {}` or omit it.
2. Store `genie_conversation_ids` dict from response `custom_outputs`.
3. Pass the entire dict back on every follow-up request.

### Sequence Diagram

```
Frontend                     Agent                        Genie Space (per domain)
   |                           |                                   |
   |-- Request 1 (new) ------->|                                   |
   |   genie_conversation_ids: |                                   |
   |     {}                    |  existing_conv_id = None          |
   |                           |  _query_genie(conversation_id=None)
   |                           |--start_conversation_and_wait----->|
   |                           |<--response + conv_id "genie_X"---|
   |<-- Response 1 ------------|                                   |
   |   genie_conversation_ids: |                                   |
   |     { "cost": "genie_X" } |                                   |
   |                           |                                   |
   |   ** Frontend stores dict **                                  |
   |                           |                                   |
   |-- Request 2 (follow-up) ->|                                   |
   |   genie_conversation_ids: |                                   |
   |     { "cost": "genie_X" } |  existing_conv_id = "genie_X"    |
   |                           |  _query_genie(conversation_id="genie_X")
   |                           |--create_message_and_wait--------->|
   |                           |<--follow-up response ------------|
   |<-- Response 2 ------------|                                   |
   |   genie_conversation_ids: |                                   |
   |     { "cost": "genie_X" } |                                   |
```

### Key Facts

- **Dict format**: `{"cost": "conv_abc", "security": "conv_def"}` -- keys are domain names, values are Genie conversation IDs.
- **Per-domain**: Each domain has its own Genie conversation. A cost question and a security question create separate conversations.
- **Cross-domain**: When a cross-domain query runs, multiple domains are queried and the returned dict has multiple keys: `{"cost": "conv_1", "reliability": "conv_2"}`.
- **New vs follow-up**:
  - No conversation ID for domain -> `start_conversation_and_wait()` (new conversation)
  - Conversation ID exists for domain -> `create_message_and_wait()` (follow-up in existing conversation)
- **Merge pattern** (line 2745-2747): The agent merges new IDs into the existing dict: `updated_conv_ids = dict(genie_conversation_ids); updated_conv_ids[domain] = new_conv_id`
- **Stateless replicas**: The agent does NOT persist Genie conversation IDs internally. The frontend is the sole source of truth.

### Frontend State Management

```typescript
const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({});

async function sendMessage(query: string) {
  const response = await callAgent({
    input: [{ role: "user", content: query }],
    custom_inputs: {
      user_id: currentUser.email,
      thread_id: threadId,
      genie_conversation_ids: genieConvIds,
    },
  });

  // Merge returned IDs into local state
  setGenieConvIds(response.custom_outputs.genie_conversation_ids);
}

function startNewConversation() {
  setThreadId(null);
  setGenieConvIds({}); // Clear Genie state for fresh conversations
}
```

---

## State Lifecycle Summary

```
User opens app
  └─ user_id = current user email (stable, never changes within session)
  └─ thread_id = null
  └─ genie_conversation_ids = {}

User sends first message
  └─ Request: { custom_inputs: { user_id, genie_conversation_ids: {} } }
  └─ Response: { custom_outputs: { thread_id: "abc", genie_conversation_ids: { "cost": "xyz" } } }
  └─ State update: thread_id = "abc", genie_conversation_ids = { "cost": "xyz" }

User sends follow-up
  └─ Request: { custom_inputs: { user_id, thread_id: "abc", genie_conversation_ids: { "cost": "xyz" } } }
  └─ Response: { custom_outputs: { thread_id: "abc", genie_conversation_ids: { "cost": "xyz" } } }
  └─ State update: no change (same thread, same Genie conv)

User asks about security (new domain)
  └─ Request: { custom_inputs: { user_id, thread_id: "abc", genie_conversation_ids: { "cost": "xyz" } } }
  └─ Response: { custom_outputs: { thread_id: "abc", genie_conversation_ids: { "cost": "xyz", "security": "new_id" } } }
  └─ State update: genie_conversation_ids gains "security" key

User clicks "New Conversation"
  └─ thread_id = null
  └─ genie_conversation_ids = {}
  └─ Next request starts fresh
```
