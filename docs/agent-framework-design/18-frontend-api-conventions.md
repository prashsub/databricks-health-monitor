# 18 - Frontend API Conventions & Best Practices

> ⚠️ **DEPRECATED**: This guide has been reorganized and updated.
> 
> **👉 NEW LOCATION**: See `frontend-guides/03-api-reference.md`
> 
> **Why Moved**: Part of reorganized frontend guide series (01-06) with verified implementation.
> 
> **All Frontend Guides**: See `frontend-guides/00-README.md`

---

**This file is kept for backward compatibility but will not be updated.**

---

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Authentication](#authentication)
3. [Request Conventions](#request-conventions)
4. [Response Conventions](#response-conventions)
5. [Error Codes](#error-codes)
6. [Rate Limiting](#rate-limiting)
7. [CORS and Security](#cors-and-security)
8. [Deployment Environments](#deployment-environments)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Testing](#testing)

---

## API Endpoints

### Production Endpoint

```
https://<workspace-url>/serving-endpoints/<endpoint-name>/invocations
```

**Example**:
```
https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations
```

### Endpoint Discovery

**Option 1: From Environment Variables**

```typescript
const WORKSPACE_URL = process.env.NEXT_PUBLIC_DATABRICKS_WORKSPACE_URL;
const ENDPOINT_NAME = process.env.NEXT_PUBLIC_AGENT_ENDPOINT_NAME;
const ENDPOINT_URL = `${WORKSPACE_URL}/serving-endpoints/${ENDPOINT_NAME}/invocations`;
```

**Option 2: From Backend API**

```typescript
async function getAgentEndpoint(): Promise<string> {
  const response = await fetch('/api/agent/config');
  const { endpointUrl } = await response.json();
  return endpointUrl;
}
```

**Option 3: Hardcoded (Not Recommended)**

```typescript
const ENDPOINT_URL = "https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations";
```

### Health Check

**Check if endpoint is ready**:

```typescript
async function checkAgentHealth(): Promise<boolean> {
  try {
    const response = await fetch(
      `${WORKSPACE_URL}/api/2.0/serving-endpoints/${ENDPOINT_NAME}`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    const data = await response.json();
    return data.state?.ready === 'READY';
  } catch {
    return false;
  }
}
```

---

## Authentication

### User Token (Required)

**The agent uses On-Behalf-Of-User (OBO) authentication**, meaning queries execute with the **user's permissions**, not the deployer's.

```typescript
const headers = {
  'Authorization': `Bearer ${userDatabricksToken}`,
  'Content-Type': 'application/json'
};
```

### Token Management Patterns

#### Pattern 1: Backend Proxy (Recommended)

```typescript
// Frontend calls your backend
const response = await fetch('/api/agent/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${yourAppToken}`,  // Your app's auth
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ query: userQuery })
});

// Backend proxies to Databricks with user's token
```

**Benefits**:
- ✅ User tokens never exposed to client
- ✅ Backend can refresh tokens
- ✅ Centralized token management
- ✅ Additional validation/logging

#### Pattern 2: Direct Client (Simple)

```typescript
// Frontend calls Databricks directly
const response = await fetch(DATABRICKS_ENDPOINT_URL, {
  headers: {
    'Authorization': `Bearer ${userToken}`,  // User's Databricks PAT
  },
  body: JSON.stringify(request)
});
```

**Considerations**:
- ⚠️ User token exposed to client (less secure)
- ⚠️ CORS configuration required
- ✅ Simpler architecture
- ✅ No backend proxy needed

### Token Expiry Handling

```typescript
async function sendAgentRequestWithTokenRefresh(request: AgentRequest) {
  try {
    return await sendAgentRequest(request);
  } catch (error) {
    if (error.message.includes('401') || error.message.includes('Invalid access token')) {
      // Token expired - refresh and retry
      const newToken = await refreshUserToken();
      setUserToken(newToken);
      return await sendAgentRequest(request);  // Retry with new token
    }
    throw error;
  }
}
```

---

## Request Conventions

### Standard Request Format

```typescript
interface AgentRequest {
  // REQUIRED: User input messages
  input: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  
  // RECOMMENDED: Memory and tracking context
  custom_inputs?: {
    // Long-term memory (REQUIRED for personalization)
    user_id: string;
    
    // Session tracking (RECOMMENDED)
    session_id: string;
    request_id: string;
    
    // Short-term memory (REQUIRED for follow-ups)
    thread_id: string | null;
    
    // Genie follow-ups (REQUIRED for contextual Genie queries)
    genie_conversation_ids: Record<string, string>;
  };
}
```

### Field Requirements

| Field | Required? | Purpose | Default |
|---|---|---|---|
| `input` | ✅ YES | User's query | N/A |
| `user_id` | ⚠️ Highly Recommended | Long-term memory, personalization | "anonymous" |
| `session_id` | Recommended | Session tracking | Generated |
| `thread_id` | For follow-ups | Short-term memory | null |
| `genie_conversation_ids` | For Genie follow-ups | Contextual Genie queries | {} |
| `request_id` | Optional | Request tracing | Generated |

### Example Requests

#### First Query (No Context)

```typescript
{
  "input": [
    { "role": "user", "content": "What are the top 5 expensive jobs?" }
  ],
  "custom_inputs": {
    "user_id": "user@company.com",
    "session_id": "a1b2c3d4-e5f6-...",
    "request_id": "req_123"
  }
}
```

#### Follow-Up Query (With Context)

```typescript
{
  "input": [
    { "role": "user", "content": "Show me details for the first one" }
  ],
  "custom_inputs": {
    "user_id": "user@company.com",
    "session_id": "a1b2c3d4-e5f6-...",
    "thread_id": "thread_abc123",  // From previous response
    "genie_conversation_ids": {
      "cost": "conv_def456"        // From previous response
    },
    "request_id": "req_124"
  }
}
```

---

## Response Conventions

### Standard Response Format

```typescript
interface AgentResponse {
  // Response ID (for tracking)
  id: string;
  
  // Output messages
  output: Array<{
    type: "message";
    id: string;
    role: "assistant";
    content: Array<{
      type: "output_text";
      text: string;  // Markdown-formatted response
    }>;
  }>;
  
  // Metadata and memory state
  custom_outputs: {
    // Memory state (store for next request)
    thread_id: string;
    genie_conversation_ids: Record<string, string>;
    memory_status: "saved" | "error";
    
    // Query metadata
    domain: string;
    source: "genie" | "error";
    confidence?: number;
    sources?: string[];
    
    // Visualization (if data present)
    visualization_hint: VisualizationHint;
    data: TableRow[] | null;
    
    // Error handling
    error?: string;
  };
}
```

### Extracting Response Text

```typescript
function extractResponseText(response: AgentResponse): string {
  return response.output[0]?.content[0]?.text || "No response";
}
```

### Extracting Visualization Data

```typescript
function extractVisualization(response: AgentResponse) {
  const hint = response.custom_outputs.visualization_hint;
  const data = response.custom_outputs.data;
  const domain = response.custom_outputs.domain;
  
  return { hint, data, domain };
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Frontend Action |
|---|---|---|
| **200** | Success | Display response normally |
| **400** | Bad Request | Show validation error, check request format |
| **401** | Unauthorized | Redirect to login, refresh token |
| **403** | Forbidden | Show permission error, link to docs |
| **404** | Endpoint Not Found | Show configuration error |
| **429** | Rate Limit Exceeded | Wait 60s, auto-retry |
| **500** | Internal Server Error | Show generic error, retry after delay |
| **503** | Service Unavailable | Endpoint starting up, retry in 30s |

### Application Error Types

**Identified by `custom_outputs.source === "error"`**

| Error Type | Detection | User Message |
|---|---|---|
| **Genie Query Failed** | `error` includes "query failed" | "Failed to retrieve data. Please try again." |
| **Permission Error** | `error` includes "permission" or "authorized" | "You need CAN USE permissions on the SQL warehouse. [Setup Guide]" |
| **Genie Space Not Configured** | `error` === "genie_not_configured" | "This feature is not configured yet." |
| **Timeout** | `error` includes "timeout" or "timed out" | "Query timed out. Try a more specific question." |
| **Rate Limit** | `error` includes "rate limit" or "429" | "Too many requests. Retrying in 60 seconds..." |

### Error Handling Function

```typescript
function handleAgentError(response: AgentResponse): ErrorInfo {
  const customOutputs = response.custom_outputs;
  
  // Check if this is an error response
  if (customOutputs.source !== 'error') {
    return { type: 'none', message: null };
  }
  
  const error = customOutputs.error || '';
  
  // Permission error
  if (error.toLowerCase().includes('permission') || error.toLowerCase().includes('authorized')) {
    return {
      type: 'permission',
      message: 'You need CAN USE permissions on the SQL warehouse and Genie Space.',
      action: 'View Setup Guide',
      actionUrl: '/docs/permissions',
      severity: 'high',
      retryable: false
    };
  }
  
  // Rate limit
  if (error.toLowerCase().includes('rate limit') || error.includes('429')) {
    return {
      type: 'rate_limit',
      message: 'Genie API rate limit reached (5 queries/minute). Retrying in 60 seconds...',
      severity: 'medium',
      retryable: true,
      retryAfterSeconds: 60
    };
  }
  
  // Timeout
  if (error.toLowerCase().includes('timeout') || error.toLowerCase().includes('timed out')) {
    return {
      type: 'timeout',
      message: 'Query timed out. Try a more specific question or check Genie Space status.',
      severity: 'medium',
      retryable: true,
      retryAfterSeconds: 5
    };
  }
  
  // Configuration error
  if (error === 'genie_not_configured' || error.includes('not configured')) {
    return {
      type: 'configuration',
      message: `Genie Space for ${customOutputs.domain} is not configured.`,
      severity: 'high',
      retryable: false
    };
  }
  
  // Generic error
  return {
    type: 'unknown',
    message: error || 'An unknown error occurred',
    severity: 'medium',
    retryable: true,
    retryAfterSeconds: 5
  };
}

interface ErrorInfo {
  type: 'none' | 'permission' | 'rate_limit' | 'timeout' | 'configuration' | 'unknown';
  message: string | null;
  action?: string;
  actionUrl?: string;
  severity?: 'low' | 'medium' | 'high';
  retryable?: boolean;
  retryAfterSeconds?: number;
}
```

### Error Display Component

```typescript
export function ErrorDisplay({ response }: { response: AgentResponse }) {
  const errorInfo = handleAgentError(response);
  
  if (errorInfo.type === 'none') return null;
  
  const severityColors = {
    low: 'bg-gray-50 border-gray-200 text-gray-800',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    high: 'bg-red-50 border-red-200 text-red-800'
  };
  
  const colorClass = severityColors[errorInfo.severity || 'medium'];
  
  return (
    <div className={`error-display border p-4 rounded ${colorClass}`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">
          {errorInfo.type === 'permission' && '🔒'}
          {errorInfo.type === 'rate_limit' && '⏳'}
          {errorInfo.type === 'timeout' && '⏱️'}
          {errorInfo.type === 'configuration' && '⚙️'}
          {errorInfo.type === 'unknown' && '❌'}
        </span>
        
        <div className="flex-1">
          <h3 className="font-semibold mb-1">
            {errorInfo.type.replace('_', ' ').toUpperCase()}
          </h3>
          <p className="text-sm mb-2">{errorInfo.message}</p>
          
          {errorInfo.action && (
            <a
              href={errorInfo.actionUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm underline"
            >
              {errorInfo.action} →
            </a>
          )}
          
          {errorInfo.retryable && (
            <button
              onClick={() => retryQuery()}
              className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm"
            >
              🔄 Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## Rate Limiting

### Genie API Rate Limits

**Limits**:
- **5 queries per minute** per user per Genie Space
- **Applies per domain** (cost, security, etc.)
- **Enforced by Databricks**

### Client-Side Rate Limiting

```typescript
class RateLimiter {
  private requestTimes: Map<string, number[]> = new Map();
  private readonly limit = 5;  // requests
  private readonly window = 60000;  // 60 seconds
  
  canMakeRequest(domain: string): boolean {
    const now = Date.now();
    const times = this.requestTimes.get(domain) || [];
    
    // Remove requests outside the time window
    const recentTimes = times.filter(time => now - time < this.window);
    
    // Check if under limit
    return recentTimes.length < this.limit;
  }
  
  recordRequest(domain: string): void {
    const now = Date.now();
    const times = this.requestTimes.get(domain) || [];
    times.push(now);
    this.requestTimes.set(domain, times);
  }
  
  getTimeUntilNextAllowed(domain: string): number {
    const now = Date.now();
    const times = this.requestTimes.get(domain) || [];
    const recentTimes = times.filter(time => now - time < this.window);
    
    if (recentTimes.length < this.limit) return 0;
    
    // Time until oldest request exits the window
    const oldestTime = Math.min(...recentTimes);
    return this.window - (now - oldestTime);
  }
}

// Usage
const rateLimiter = new RateLimiter();

async function sendMessage(content: string, domain: string) {
  if (!rateLimiter.canMakeRequest(domain)) {
    const waitMs = rateLimiter.getTimeUntilNextAllowed(domain);
    showToast(`Rate limit reached. Please wait ${Math.ceil(waitMs / 1000)}s`);
    
    // Auto-retry after wait period
    await new Promise(resolve => setTimeout(resolve, waitMs));
  }
  
  rateLimiter.recordRequest(domain);
  return await sendAgentRequest(content);
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
      const waitTime = rateLimiter.getTimeUntilNextAllowed(domain);
      
      setRemaining(canMake ? 5 : 0);
      setResetIn(waitTime);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [domain]);
  
  if (remaining === 5) return null;  // Don't show if no issues
  
  return (
    <div className="rate-limit-indicator text-xs text-yellow-700 bg-yellow-50 px-2 py-1 rounded">
      ⏳ Rate limit: {remaining}/5 queries remaining
      {resetIn > 0 && ` (resets in ${Math.ceil(resetIn / 1000)}s)`}
    </div>
  );
}
```

---

## CORS and Security

### CORS Configuration (Backend)

**If using direct client connections**, your Databricks admin needs to configure CORS:

```python
# Databricks Serving Endpoint CORS configuration
# Done via API or Terraform, not exposed in UI
{
  "cors": {
    "allowed_origins": [
      "https://your-frontend-domain.com",
      "http://localhost:3000"  # For development
    ],
    "allowed_methods": ["POST", "OPTIONS"],
    "allowed_headers": ["Authorization", "Content-Type"],
    "allow_credentials": true
  }
}
```

### Content Security Policy

```html
<!-- Add to your HTML <head> -->
<meta http-equiv="Content-Security-Policy" 
      content="connect-src 'self' https://*.cloud.databricks.com;">
```

### Secure Token Storage

```typescript
// ❌ NEVER do this
localStorage.setItem('databricks_token', userToken);  // Exposed to XSS!

// ✅ Use httpOnly cookies (backend sets)
// OR secure session storage with encryption
```

---

## Deployment Environments

### Environment-Specific Endpoints

```typescript
const ENV_CONFIG = {
  development: {
    workspaceUrl: 'https://e2-demo-field-eng.cloud.databricks.com',
    endpointName: 'health_monitor_agent_dev',
    enableDebugLogs: true
  },
  staging: {
    workspaceUrl: 'https://e2-demo-field-eng.cloud.databricks.com',
    endpointName: 'health_monitor_agent_staging',
    enableDebugLogs: true
  },
  production: {
    workspaceUrl: 'https://prod-workspace.cloud.databricks.com',
    endpointName: 'health_monitor_agent',
    enableDebugLogs: false
  }
};

const config = ENV_CONFIG[process.env.NODE_ENV || 'development'];
const ENDPOINT_URL = `${config.workspaceUrl}/serving-endpoints/${config.endpointName}/invocations`;
```

### Environment Detection

```typescript
function getEnvironment(): 'development' | 'staging' | 'production' {
  const hostname = window.location.hostname;
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'development';
  }
  if (hostname.includes('staging')) {
    return 'staging';
  }
  return 'production';
}
```

---

## Monitoring and Logging

### Request Logging

```typescript
interface RequestLog {
  requestId: string;
  userId: string;
  query: string;
  domain: string;
  timestamp: Date;
  responseTimeMs: number;
  success: boolean;
  errorType?: string;
}

async function sendAgentRequestWithLogging(request: AgentRequest): Promise<AgentResponse> {
  const startTime = Date.now();
  const log: Partial<RequestLog> = {
    requestId: request.custom_inputs?.request_id,
    userId: request.custom_inputs?.user_id,
    query: request.input[0].content,
    timestamp: new Date()
  };
  
  try {
    const response = await sendAgentRequest(request);
    
    log.responseTimeMs = Date.now() - startTime;
    log.domain = response.custom_outputs.domain;
    log.success = response.custom_outputs.source !== 'error';
    log.errorType = response.custom_outputs.error || undefined;
    
    // Send to analytics
    analytics.track('agent_request', log);
    
    return response;
    
  } catch (error) {
    log.responseTimeMs = Date.now() - startTime;
    log.success = false;
    log.errorType = error.message;
    
    analytics.track('agent_request_failed', log);
    
    throw error;
  }
}
```

### Performance Monitoring

```typescript
interface PerformanceMetrics {
  totalRequests: number;
  successRate: number;
  avgResponseTime: number;
  p95ResponseTime: number;
  errorsByType: Record<string, number>;
}

class PerformanceTracker {
  private metrics: RequestLog[] = [];
  
  recordRequest(log: RequestLog) {
    this.metrics.push(log);
    
    // Keep only last 100 requests
    if (this.metrics.length > 100) {
      this.metrics.shift();
    }
  }
  
  getMetrics(): PerformanceMetrics {
    const total = this.metrics.length;
    const successful = this.metrics.filter(m => m.success).length;
    
    const responseTimes = this.metrics.map(m => m.responseTimeMs).sort((a, b) => a - b);
    const avg = responseTimes.reduce((a, b) => a + b, 0) / total;
    const p95Index = Math.floor(total * 0.95);
    const p95 = responseTimes[p95Index] || 0;
    
    const errorsByType: Record<string, number> = {};
    this.metrics.filter(m => !m.success).forEach(m => {
      errorsByType[m.errorType || 'unknown'] = (errorsByType[m.errorType || 'unknown'] || 0) + 1;
    });
    
    return {
      totalRequests: total,
      successRate: successful / total,
      avgResponseTime: avg,
      p95ResponseTime: p95,
      errorsByType
    };
  }
}
```

### Telemetry Dashboard (Optional)

```typescript
export function TelemetryDashboard() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(performanceTracker.getMetrics());
    }, 5000);
    return () => clearInterval(interval);
  }, []);
  
  if (!metrics) return null;
  
  return (
    <div className="telemetry-dashboard p-4 bg-gray-50 rounded">
      <h3 className="font-semibold mb-3">📊 Agent Performance</h3>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-gray-600">Success Rate</div>
          <div className="text-2xl font-semibold">
            {(metrics.successRate * 100).toFixed(1)}%
          </div>
        </div>
        
        <div>
          <div className="text-gray-600">Avg Response Time</div>
          <div className="text-2xl font-semibold">
            {(metrics.avgResponseTime / 1000).toFixed(1)}s
          </div>
        </div>
        
        <div>
          <div className="text-gray-600">Total Requests</div>
          <div className="text-xl font-semibold">{metrics.totalRequests}</div>
        </div>
        
        <div>
          <div className="text-gray-600">P95 Latency</div>
          <div className="text-xl font-semibold">
            {(metrics.p95ResponseTime / 1000).toFixed(1)}s
          </div>
        </div>
      </div>
      
      {Object.keys(metrics.errorsByType).length > 0 && (
        <div className="mt-3">
          <div className="text-gray-600 text-sm mb-1">Errors</div>
          {Object.entries(metrics.errorsByType).map(([type, count]) => (
            <div key={type} className="text-xs text-red-600">
              {type}: {count}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Testing

### Mock Agent Responses

```typescript
export function createMockResponse(overrides = {}): AgentResponse {
  return {
    id: 'resp_mock123',
    output: [{
      type: 'message',
      id: 'msg_mock',
      role: 'assistant',
      content: [{
        type: 'output_text',
        text: '**Analysis:**\nMock response text...\n\n**Query Results:**\n| Column | Value |\n|--------|-------|\n| Test | 123 |'
      }]
    }],
    custom_outputs: {
      thread_id: 'thread_mock',
      genie_conversation_ids: { cost: 'conv_mock' },
      memory_status: 'saved',
      domain: 'cost',
      source: 'genie',
      visualization_hint: {
        type: 'bar_chart',
        x_axis: 'Column',
        y_axis: 'Value',
        title: 'Mock Chart',
        reason: 'Test data'
      },
      data: [{ Column: 'Test', Value: '123' }],
      ...overrides
    }
  };
}
```

### Integration Tests

```typescript
describe('Agent Integration', () => {
  it('should handle successful query', async () => {
    const response = await sendAgentRequest({
      input: [{ role: "user", content: "What are top 5 jobs?" }],
      custom_inputs: { user_id: "test@example.com" }
    });
    
    expect(response.custom_outputs.source).toBe('genie');
    expect(response.custom_outputs.thread_id).toBeTruthy();
    expect(response.custom_outputs.visualization_hint).toBeDefined();
  });
  
  it('should handle rate limit error', async () => {
    // Make 6 rapid requests
    const requests = Array(6).fill(null).map((_, i) =>
      sendAgentRequest({
        input: [{ role: "user", content: `Query ${i}` }],
        custom_inputs: { user_id: "test@example.com" }
      })
    );
    
    const responses = await Promise.allSettled(requests);
    
    // 6th request should fail with rate limit
    const lastResponse = responses[5];
    expect(lastResponse.status).toBe('rejected');
    expect(lastResponse.reason.message).toContain('rate limit');
  });
  
  it('should preserve memory across requests', async () => {
    // First request
    const r1 = await sendAgentRequest({
      input: [{ role: "user", content: "Show cost trends" }],
      custom_inputs: { user_id: "test@example.com" }
    });
    
    const threadId = r1.custom_outputs.thread_id;
    
    // Follow-up with thread_id
    const r2 = await sendAgentRequest({
      input: [{ role: "user", content: "Break that down by workspace" }],
      custom_inputs: {
        user_id: "test@example.com",
        thread_id: threadId
      }
    });
    
    // Should return same thread_id
    expect(r2.custom_outputs.thread_id).toBe(threadId);
  });
});
```

---

## Debug Mode

### Enable Debug Logging

```typescript
const DEBUG = process.env.NODE_ENV === 'development';

async function sendAgentRequest(request: AgentRequest): Promise<AgentResponse> {
  if (DEBUG) {
    console.group('🤖 Agent Request');
    console.log('Query:', request.input[0].content);
    console.log('Memory:', {
      thread_id: request.custom_inputs?.thread_id,
      genie_conversation_ids: request.custom_inputs?.genie_conversation_ids
    });
    console.log('Full request:', JSON.stringify(request, null, 2));
    console.groupEnd();
  }
  
  const startTime = Date.now();
  const response = await fetch(ENDPOINT_URL, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request)
  });
  
  const data = await response.json();
  
  if (DEBUG) {
    console.group('🤖 Agent Response');
    console.log('Duration:', Date.now() - startTime, 'ms');
    console.log('Domain:', data.custom_outputs.domain);
    console.log('Source:', data.custom_outputs.source);
    console.log('Memory status:', data.custom_outputs.memory_status);
    console.log('Visualization:', data.custom_outputs.visualization_hint?.type);
    console.log('Full response:', JSON.stringify(data, null, 2));
    console.groupEnd();
  }
  
  return data;
}
```

### Debug Panel UI

```typescript
export function DebugPanel({ lastResponse }: { lastResponse: AgentResponse | null }) {
  if (!DEBUG) return null;
  if (!lastResponse) return null;
  
  return (
    <details className="debug-panel mt-4 p-4 bg-gray-900 text-gray-100 rounded text-xs font-mono">
      <summary className="cursor-pointer font-semibold">
        🐛 Debug Info
      </summary>
      
      <div className="mt-2">
        <h4 className="font-semibold text-green-400 mb-1">Custom Outputs:</h4>
        <pre className="overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(lastResponse.custom_outputs, null, 2)}
        </pre>
        
        <h4 className="font-semibold text-blue-400 mt-3 mb-1">Full Response:</h4>
        <pre className="overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(lastResponse, null, 2)}
        </pre>
      </div>
    </details>
  );
}
```

---

## TypeScript Types

### Complete Type Definitions

```typescript
// =============================================================================
// AGENT API TYPES
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
  // Memory
  thread_id: string;
  genie_conversation_ids: Record<string, string>;
  memory_status: "saved" | "error";
  
  // Query metadata
  domain: string;
  source: "genie" | "error";
  confidence?: number;
  sources?: string[];
  
  // Visualization
  visualization_hint: VisualizationHint;
  data: TableRow[] | null;
  
  // Error
  error?: string;
}

export interface VisualizationHint {
  type: "bar_chart" | "line_chart" | "pie_chart" | "table" | "text" | "error";
  x_axis?: string;
  y_axis?: string | string[];
  label?: string;
  value?: string;
  title?: string;
  reason?: string;
  row_count?: number;
  columns?: string[];
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
// STREAMING TYPES
// =============================================================================

export interface StreamEvent {
  type: "response.output_item.delta" | "response.output_item.done" | "response.done";
  item_id?: string;
  delta?: {
    type: "output_text";
    text: string;
  };
  item?: OutputItem;
  custom_outputs?: CustomOutputs;
}

// =============================================================================
// ERROR TYPES
// =============================================================================

export interface ErrorInfo {
  type: 'none' | 'permission' | 'rate_limit' | 'timeout' | 'configuration' | 'unknown';
  message: string | null;
  action?: string;
  actionUrl?: string;
  severity?: 'low' | 'medium' | 'high';
  retryable?: boolean;
  retryAfterSeconds?: number;
}
```

---

## Quick Reference Card

### Essential Request

```typescript
{
  input: [{ role: "user", content: "query" }],
  custom_inputs: {
    user_id: "user@example.com",    // Required
    session_id: "uuid",             // Recommended
    thread_id: "thread_id",         // For follow-ups
    genie_conversation_ids: {}      // For Genie follow-ups
  }
}
```

### Essential Response Fields

```typescript
{
  output: [{ content: [{ text: "response" }] }],
  custom_outputs: {
    thread_id: "...",               // Store for next request
    genie_conversation_ids: {...},  // Store for next request
    visualization_hint: {...},      // Render chart
    data: [...],                    // Chart data
    domain: "cost",
    source: "genie" | "error"
  }
}
```

### Frontend Checklist

- [ ] User authentication implemented
- [ ] `user_id` included in all requests
- [ ] `thread_id` tracked and included in follow-ups
- [ ] `genie_conversation_ids` tracked and included
- [ ] Streaming supported with fallback
- [ ] Visualization hints rendered as charts
- [ ] Error handling covers all error types
- [ ] Rate limiting implemented
- [ ] Memory state persisted in sessionStorage
- [ ] "New Conversation" clears memory
- [ ] Debug logging in development mode
- [ ] Performance monitoring enabled
- [ ] CORS configured (if direct connection)
- [ ] Security headers set
- [ ] Integration tests pass

---

## Support Resources

### Troubleshooting

**Issue**: "CORS error when calling agent"
- **Solution**: Contact Databricks admin to configure CORS on serving endpoint

**Issue**: "401 Unauthorized"
- **Solution**: Check user token is valid, refresh if expired

**Issue**: "No memory between messages"
- **Solution**: Ensure `thread_id` from previous response is included in next request

**Issue**: "Genie follow-ups don't work"
- **Solution**: Include `genie_conversation_ids` from previous response

**Issue**: "Rate limit errors"
- **Solution**: Implement client-side rate limiting (5 queries/minute per domain)

### Getting Help

- **Documentation**: See [15-frontend-integration-guide.md](15-frontend-integration-guide.md)
- **Backend Issues**: Check [OBO Authentication Guide](obo-authentication-guide.md)
- **API Reference**: See [Model Serving API Docs](https://docs.databricks.com/api/workspace/servingendpoints)

---

**Last Updated**: January 9, 2026  
**Version**: 1.0  
**Status**: Ready for Frontend Implementation

