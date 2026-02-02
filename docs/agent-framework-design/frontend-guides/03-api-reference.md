# Frontend Guide 03: API Reference

> **Purpose**: Complete API specification for the Health Monitor Agent
> 
> **Audience**: Frontend developers implementing the API client
> 
> **Use As**: Reference documentation while coding

---

## Table of Contents

1. [Endpoint URL](#endpoint-url)
2. [Request Format](#request-format)
3. [Response Format](#response-format)
4. [Error Codes](#error-codes)
5. [Rate Limiting](#rate-limiting)
6. [TypeScript Types](#typescript-types)
7. [Examples](#examples)

---

## Endpoint URL

### Format

```
https://<workspace-url>/serving-endpoints/<endpoint-name>/invocations
```

### Environment-Specific URLs

| Environment | Workspace URL | Endpoint Name |
|---|---|---|
| **Development** | `https://e2-demo-field-eng.cloud.databricks.com` | `health_monitor_agent_dev` |
| **Production** | `https://prod-workspace.cloud.databricks.com` | `health_monitor_agent` |

### Configuration

```typescript
const ENV_CONFIG = {
  development: {
    workspaceUrl: 'https://e2-demo-field-eng.cloud.databricks.com',
    endpointName: 'health_monitor_agent_dev'
  },
  production: {
    workspaceUrl: 'https://prod-workspace.cloud.databricks.com',
    endpointName: 'health_monitor_agent'
  }
};

const env = process.env.NODE_ENV || 'development';
const config = ENV_CONFIG[env];
const ENDPOINT_URL = `${config.workspaceUrl}/serving-endpoints/${config.endpointName}/invocations`;
```

---

## Request Format

### Complete Request Structure

```typescript
interface AgentRequest {
  // REQUIRED: User's query
  input: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  
  // OPTIONAL: Memory and tracking context
  custom_inputs?: {
    // Long-term memory (personalization)
    user_id?: string;           // User's email, required for personalization
    
    // Session tracking
    session_id?: string;        // Browser session UUID
    request_id?: string;        // Individual request UUID (for tracing)
    
    // Short-term memory (conversation context)
    thread_id?: string | null;  // From previous response, enables follow-ups
    
    // Genie conversation continuity
    genie_conversation_ids?: Record<string, string>;  // Per-domain conversation IDs
  };
}
```

### Field Requirements

| Field | Required? | Purpose | Default Value |
|---|---|---|---|
| `input` | ✅ **YES** | User's query | N/A (must provide) |
| `user_id` | ⚠️ **Highly Recommended** | Personalization & audit | "anonymous" |
| `session_id` | Recommended | Session tracking | Auto-generated |
| `thread_id` | For follow-ups | Conversation context | null (new conversation) |
| `genie_conversation_ids` | For Genie follow-ups | Domain-specific context | {} (empty) |
| `request_id` | Optional | Request tracing/debugging | Auto-generated |

### Example Requests

#### First Query (No Context)

```json
{
  "input": [
    { "role": "user", "content": "What are the top 5 most expensive jobs?" }
  ],
  "custom_inputs": {
    "user_id": "user@company.com",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "request_id": "req_12345"
  }
}
```

#### Follow-Up Query (With Context)

```json
{
  "input": [
    { "role": "user", "content": "Show me details for the first one" }
  ],
  "custom_inputs": {
    "user_id": "user@company.com",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "thread_id": "thread_abc123",
    "genie_conversation_ids": {
      "cost": "conv_def456"
    },
    "request_id": "req_12346"
  }
}
```

---

## Response Format

### Complete Response Structure

```typescript
interface AgentResponse {
  // Response identifier
  id: string;
  
  // Output messages (natural language)
  output: Array<{
    type: "message";
    id: string;
    role: "assistant";
    content: Array<{
      type: "output_text";
      text: string;  // Markdown-formatted response
    }>;
  }>;
  
  // Metadata and structured data
  custom_outputs: {
    // Memory state (store for next request!)
    thread_id: string;
    genie_conversation_ids: Record<string, string>;
    memory_status: "saved" | "error";
    
    // Query metadata
    domain: string;  // "cost" | "security" | "performance" | "reliability" | "quality" | "unified"
    source: "genie" | "error";  // Success indicator
    confidence?: number;
    sources?: string[];
    
    // Visualization (if data present)
    visualization_hint?: VisualizationHint;
    data?: TableRow[];
    
    // Error handling
    error?: string;
  };
}
```

### Example Success Response

```json
{
  "id": "resp_a1b2c3d4e5f6",
  "output": [
    {
      "type": "message",
      "id": "msg_123",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "**Analysis:**\nThe top 5 most expensive jobs this month are:\n\n**Query Results:**\n| Job Name | Total Cost |\n|---|---|\n| ETL Pipeline | $1,250.50 |\n| ML Training | $980.25 |\n..."
        }
      ]
    }
  ],
  "custom_outputs": {
    "thread_id": "thread_abc123",
    "genie_conversation_ids": {
      "cost": "conv_def456"
    },
    "memory_status": "saved",
    "domain": "cost",
    "source": "genie",
    "confidence": 0.95,
    "visualization_hint": {
      "type": "bar_chart",
      "x_axis": "Job Name",
      "y_axis": "Total Cost",
      "title": "Top 5 Jobs by Cost",
      "reason": "Top N comparison query",
      "row_count": 5,
      "domain_preferences": {
        "prefer_currency_format": true,
        "color_scheme": "red_amber_green",
        "default_sort": "descending"
      }
    },
    "data": [
      { "Job Name": "ETL Pipeline", "Total Cost": "1250.50" },
      { "Job Name": "ML Training", "Total Cost": "980.25" },
      { "Job Name": "Data Validation", "Total Cost": "450.75" },
      { "Job Name": "Reporting", "Total Cost": "320.00" },
      { "Job Name": "Archive", "Total Cost": "180.50" }
    ]
  }
}
```

### Example Error Response

```json
{
  "id": "resp_error123",
  "output": [
    {
      "type": "message",
      "content": [
        {
          "type": "output_text",
          "text": "**Permission Error**\n\nUnable to access the Genie Space for cost..."
        }
      ]
    }
  ],
  "custom_outputs": {
    "thread_id": "thread_abc123",
    "genie_conversation_ids": {},
    "memory_status": "saved",
    "domain": "cost",
    "source": "error",
    "error": "User 'user@company.com' is not authorized to use this SQL Endpoint.",
    "visualization_hint": {
      "type": "error",
      "reason": "Permission denied"
    },
    "data": null
  }
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Frontend Action |
|---|---|---|
| **200** | Success | Parse response normally |
| **400** | Bad Request | Show validation error, check request format |
| **401** | Unauthorized | Refresh token, redirect to login if refresh fails |
| **403** | Forbidden | Show permission error with setup instructions |
| **404** | Endpoint Not Found | Show configuration error |
| **429** | Too Many Requests | Implement retry with 60s delay |
| **500** | Internal Server Error | Show generic error, retry after 5s |
| **503** | Service Unavailable | Endpoint starting up, retry in 30s |

### Application Errors (source === "error")

Detected via `custom_outputs.source === "error"`:

| Error Type | Detection Pattern | User Message | Retryable? |
|---|---|---|---|
| **Permission** | `error` includes "permission" or "authorized" | "You need CAN USE permission. [Setup Guide]" | ❌ No |
| **Rate Limit** | `error` includes "rate limit" or "429" | "Rate limit reached. Retrying in 60s..." | ✅ Yes (60s) |
| **Timeout** | `error` includes "timeout" or "timed out" | "Query timed out. Try a more specific question." | ✅ Yes (5s) |
| **Genie Not Configured** | `error === "genie_not_configured"` | "This domain is not configured yet." | ❌ No |
| **Query Failed** | `error` includes "query failed" | "Failed to retrieve data. Please try again." | ✅ Yes (5s) |

### Error Handling Function

```typescript
interface ErrorInfo {
  type: 'none' | 'permission' | 'rate_limit' | 'timeout' | 'configuration' | 'query_failed';
  severity: 'low' | 'medium' | 'high';
  message: string;
  userAction?: string;
  retryable: boolean;
  retryAfterSeconds?: number;
}

function parseAgentError(response: AgentResponse): ErrorInfo {
  // Success case
  if (response.custom_outputs.source !== 'error') {
    return { type: 'none', severity: 'low', message: '', retryable: false };
  }
  
  const error = response.custom_outputs.error || '';
  const errorLower = error.toLowerCase();
  
  // Permission error
  if (errorLower.includes('permission') || errorLower.includes('authorized') || errorLower.includes('can use')) {
    return {
      type: 'permission',
      severity: 'high',
      message: 'You need CAN USE permission on the SQL warehouse and CAN RUN permission on the Genie Space.',
      userAction: 'Contact your Databricks administrator to request access.',
      retryable: false
    };
  }
  
  // Rate limit
  if (errorLower.includes('rate limit') || error.includes('429')) {
    return {
      type: 'rate_limit',
      severity: 'medium',
      message: 'Genie API rate limit reached (5 queries/minute per domain).',
      userAction: 'Please wait 60 seconds before trying again.',
      retryable: true,
      retryAfterSeconds: 60
    };
  }
  
  // Timeout
  if (errorLower.includes('timeout') || errorLower.includes('timed out')) {
    return {
      type: 'timeout',
      severity: 'medium',
      message: 'Query timed out. Try asking a more specific question.',
      retryable: true,
      retryAfterSeconds: 5
    };
  }
  
  // Configuration error
  if (error === 'genie_not_configured' || errorLower.includes('not configured')) {
    return {
      type: 'configuration',
      severity: 'high',
      message: `The ${response.custom_outputs.domain} domain is not configured yet.`,
      userAction: 'This feature is coming soon.',
      retryable: false
    };
  }
  
  // Generic query failure
  return {
    type: 'query_failed',
    severity: 'medium',
    message: error || 'Query failed. Please try again.',
    retryable: true,
    retryAfterSeconds: 5
  };
}
```

---

## Rate Limiting

### Genie API Limits

**Official Limits**:
- **5 queries per minute** per user per Genie Space
- **Applies per domain** (cost, security, performance, reliability, quality)
- **Enforced by Databricks** at the Genie API level

**Example**: User can send 5 cost queries + 5 security queries in the same minute (different domains).

### Client-Side Rate Limiter

```typescript
class DomainRateLimiter {
  private requestLog: Map<string, number[]> = new Map();
  private readonly LIMIT = 5;          // requests
  private readonly WINDOW_MS = 60000;  // 60 seconds

  canMakeRequest(domain: string): boolean {
    const now = Date.now();
    const times = this.requestLog.get(domain) || [];
    
    // Remove requests outside window
    const recentRequests = times.filter(t => now - t < this.WINDOW_MS);
    
    return recentRequests.length < this.LIMIT;
  }

  recordRequest(domain: string): void {
    const now = Date.now();
    const times = this.requestLog.get(domain) || [];
    times.push(now);
    
    // Clean old entries
    const recentTimes = times.filter(t => now - t < this.WINDOW_MS);
    this.requestLog.set(domain, recentTimes);
  }

  getSecondsUntilNextAllowed(domain: string): number {
    const now = Date.now();
    const times = this.requestLog.get(domain) || [];
    const recentTimes = times.filter(t => now - t < this.WINDOW_MS);
    
    if (recentTimes.length < this.LIMIT) return 0;
    
    // Time until oldest request exits the window
    const oldestTime = Math.min(...recentTimes);
    return Math.ceil((this.WINDOW_MS - (now - oldestTime)) / 1000);
  }
}

// Usage
const rateLimiter = new DomainRateLimiter();

async function sendQuery(query: string, domain: string) {
  // Check rate limit before sending
  if (!rateLimiter.canMakeRequest(domain)) {
    const waitSeconds = rateLimiter.getSecondsUntilNextAllowed(domain);
    throw new Error(`Rate limit exceeded. Please wait ${waitSeconds} seconds.`);
  }
  
  // Send request
  const response = await sendAgentQuery(query);
  
  // Record successful request
  if (response.custom_outputs.source === 'genie') {
    rateLimiter.recordRequest(domain);
  }
  
  return response;
}
```

### Rate Limit UI Indicator

```typescript
export function RateLimitIndicator({ domain }: { domain: string }) {
  const [remaining, setRemaining] = useState(5);
  const [resetIn, setResetIn] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      const canMake = rateLimiter.canMakeRequest(domain);
      const wait = rateLimiter.getSecondsUntilNextAllowed(domain);
      
      setRemaining(canMake ? 5 : 0);
      setResetIn(wait);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [domain]);
  
  if (remaining === 5) return null;
  
  return (
    <div className="rate-limit-indicator text-xs bg-yellow-50 border border-yellow-200 text-yellow-800 px-3 py-2 rounded">
      ⏳ Rate limit: {remaining}/5 remaining
      {resetIn > 0 && ` (resets in ${resetIn}s)`}
    </div>
  );
}
```

---

## TypeScript Types

### Complete Type Definitions

```typescript
// =============================================================================
// REQUEST TYPES
// =============================================================================

export interface AgentRequest {
  input: ChatMessage[];
  custom_inputs?: CustomInputs;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface CustomInputs {
  user_id?: string;
  session_id?: string;
  thread_id?: string | null;
  genie_conversation_ids?: Record<string, string>;
  request_id?: string;
}

// =============================================================================
// RESPONSE TYPES
// =============================================================================

export interface AgentResponse {
  id: string;
  output: OutputItem[];
  custom_outputs: CustomOutputs;
}

export interface OutputItem {
  type: "message";
  id: string;
  role: "assistant";
  content: OutputContent[];
}

export interface OutputContent {
  type: "output_text";
  text: string;
}

export interface CustomOutputs {
  // Memory state
  thread_id: string;
  genie_conversation_ids: Record<string, string>;
  memory_status: "saved" | "error";
  
  // Query metadata
  domain: Domain;
  source: "genie" | "error";
  confidence?: number;
  sources?: string[];
  
  // Visualization
  visualization_hint?: VisualizationHint;
  data?: TableRow[];
  
  // Error
  error?: string;
}

export type Domain = "cost" | "security" | "performance" | "reliability" | "quality" | "unified";

export interface VisualizationHint {
  type: "bar_chart" | "line_chart" | "pie_chart" | "table" | "text" | "error";
  
  // Chart-specific fields
  x_axis?: string;
  y_axis?: string | string[];
  label?: string;
  value?: string;
  title?: string;
  columns?: string[];
  
  // Metadata
  reason?: string;
  row_count?: number;
  
  // Domain-specific preferences
  domain_preferences?: DomainPreferences;
}

export interface DomainPreferences {
  prefer_currency_format?: boolean;
  color_scheme?: "red_amber_green" | "sequential" | "categorical";
  default_sort?: string;
  highlight_outliers?: boolean;
  highlight_critical?: boolean;
  show_thresholds?: boolean;
  show_percentages?: boolean;
  suggested_formats?: Record<string, any>;
}

export interface TableRow {
  [columnName: string]: string | number;
}

// =============================================================================
// ERROR TYPES
// =============================================================================

export interface ErrorInfo {
  type: 'none' | 'permission' | 'rate_limit' | 'timeout' | 'configuration' | 'query_failed';
  severity: 'low' | 'medium' | 'high';
  message: string;
  userAction?: string;
  retryable: boolean;
  retryAfterSeconds?: number;
}
```

---

## Response Parsing

### Extract Text Response

```typescript
function extractResponseText(response: AgentResponse): string {
  try {
    return response.output[0]?.content[0]?.text || "No response text";
  } catch {
    return "Error parsing response";
  }
}
```

### Extract Visualization Data

```typescript
function extractVisualizationData(response: AgentResponse) {
  return {
    hint: response.custom_outputs.visualization_hint || null,
    data: response.custom_outputs.data || null,
    domain: response.custom_outputs.domain
  };
}
```

### Extract Memory State

```typescript
function extractMemoryState(response: AgentResponse) {
  return {
    threadId: response.custom_outputs.thread_id,
    genieConversationIds: response.custom_outputs.genie_conversation_ids || {},
    memoryStatus: response.custom_outputs.memory_status
  };
}
```

### Check for Errors

```typescript
function isErrorResponse(response: AgentResponse): boolean {
  return response.custom_outputs.source === 'error';
}

function getErrorMessage(response: AgentResponse): string | null {
  if (response.custom_outputs.source === 'error') {
    return response.custom_outputs.error || 'Unknown error occurred';
  }
  return null;
}
```

---

## Complete API Client Example

```typescript
// agentClient.ts
export class AgentClient {
  private endpointUrl: string;
  private rateLimiter: DomainRateLimiter;
  
  constructor(endpointUrl: string) {
    this.endpointUrl = endpointUrl;
    this.rateLimiter = new DomainRateLimiter();
  }
  
  async query(
    query: string,
    userToken: string,
    context?: {
      userId?: string;
      sessionId?: string;
      threadId?: string;
      genieConversationIds?: Record<string, string>;
    }
  ): Promise<AgentResponse> {
    // Build request
    const request: AgentRequest = {
      input: [{ role: 'user', content: query }],
      custom_inputs: {
        user_id: context?.userId || 'anonymous',
        session_id: context?.sessionId || crypto.randomUUID(),
        thread_id: context?.threadId || null,
        genie_conversation_ids: context?.genieConversationIds || {},
        request_id: crypto.randomUUID()
      }
    };
    
    // Send request
    const response = await fetch(this.endpointUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
    
    // Handle HTTP errors
    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication failed. Token may be expired.');
      }
      if (response.status === 429) {
        throw new Error('Rate limit exceeded. Please wait and try again.');
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    // Parse response
    const data = await response.json();
    
    // Record successful query for rate limiting
    if (data.custom_outputs.source === 'genie') {
      this.rateLimiter.recordRequest(data.custom_outputs.domain);
    }
    
    return data;
  }
  
  canMakeRequest(domain: string): boolean {
    return this.rateLimiter.canMakeRequest(domain);
  }
  
  getSecondsUntilNextRequest(domain: string): number {
    return this.rateLimiter.getSecondsUntilNextAllowed(domain);
  }
}

// Usage
const client = new AgentClient(ENDPOINT_URL);

const response = await client.query(
  "What are top 5 jobs?",
  userToken,
  { userId: 'user@company.com', sessionId: 'session123' }
);
```

---

## Request/Response Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        REQUEST FLOW                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. User enters query                                              │
│     ↓                                                              │
│  2. Frontend builds request                                        │
│     - input: [{ role: "user", content: query }]                   │
│     - custom_inputs: { user_id, session_id, thread_id, ... }      │
│     ↓                                                              │
│  3. Send POST request                                              │
│     - URL: /serving-endpoints/health_monitor_agent_dev/invocations│
│     - Headers: Authorization (user's Databricks token)            │
│     ↓                                                              │
│  4. Databricks validates token                                     │
│     - Checks user permissions                                      │
│     - Extracts user identity                                       │
│     ↓                                                              │
│  5. Agent processes query                                          │
│     - Routes to appropriate domain                                 │
│     - Queries Genie with user's permissions                        │
│     - Generates response with viz hints                            │
│     - Saves to memory (Lakebase)                                   │
│     ↓                                                              │
│  6. Response returned                                              │
│     - output: Natural language text (markdown)                     │
│     - custom_outputs: Memory state, viz hints, data                │
│     ↓                                                              │
│  7. Frontend processes response                                    │
│     - Display text                                                 │
│     - Render chart (if data present)                               │
│     - Store thread_id for next query                               │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference Card

### Making a Request

```typescript
fetch(ENDPOINT_URL, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    input: [{ role: 'user', content: query }],
    custom_inputs: {
      user_id: 'user@company.com',
      session_id: sessionId,
      thread_id: threadId || null
    }
  })
})
```

### Processing Response

```typescript
const response = await fetch(...).then(r => r.json());

// Extract essentials
const text = response.output[0].content[0].text;
const threadId = response.custom_outputs.thread_id;
const isError = response.custom_outputs.source === 'error';
const hasData = !!response.custom_outputs.data;
```

### Essential Response Fields

| Field | Type | Purpose | Action |
|---|---|---|---|
| `output[0].content[0].text` | string | Natural language response | Display as markdown |
| `custom_outputs.thread_id` | string | Conversation context | **Store for next query** |
| `custom_outputs.source` | string | Success indicator | Check if "error" |
| `custom_outputs.data` | array | Tabular data | Render as chart/table |
| `custom_outputs.visualization_hint` | object | Chart suggestion | Use for rendering |

---

**Next Guide**: [04 - Streaming Responses](04-streaming-responses.md) (Real-time text updates)

**Previous Guide**: [01 - Overview and Quickstart](01-overview-and-quickstart.md)
