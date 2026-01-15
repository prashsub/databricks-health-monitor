# 15 - Frontend Integration Guide

> **📋 Implementation Status**: GUIDE FOR FRONTEND DEVELOPERS
> 
> **Purpose**: Comprehensive guide for frontend developers to integrate with the Health Monitor Agent.
> 
> **Audience**: Frontend developers, UI/UX engineers

---

## Overview

The Health Monitor Agent is a **Databricks Model Serving endpoint** that provides:
- ✅ **Streaming responses** for real-time feedback
- ✅ **Visualization hints** for intelligent chart rendering
- ✅ **Short-term memory** for conversation context (within a session)
- ✅ **Long-term memory** for user preferences across sessions
- ✅ **Genie conversation continuity** for follow-up questions
- ✅ **On-behalf-of-user authentication** (queries use end-user permissions)

This guide covers all aspects of frontend integration with practical examples.

---

## Table of Contents

1. [API Connection](#api-connection)
2. [Request Format](#request-format)
3. [Response Format](#response-format)
4. [Streaming Responses](#streaming-responses)
5. [Visualization Hints](#visualization-hints)
6. [Short-Term Memory (Conversation Context)](#short-term-memory)
7. [Long-Term Memory (User Preferences)](#long-term-memory)
8. [Genie Follow-Up Questions](#genie-follow-up-questions)
9. [Error Handling](#error-handling)
10. [Complete Examples](#complete-examples)

---

## API Connection

### Endpoint URL

```
https://<workspace-url>/serving-endpoints/health_monitor_agent_dev/invocations
```

**Example**:
```
https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations
```

### Authentication

**Required**: User's Databricks personal access token (PAT)

```typescript
const headers = {
  'Authorization': `Bearer ${userToken}`,
  'Content-Type': 'application/json'
};
```

**Why user's token?**
- Agent uses **On-Behalf-Of-User (OBO) authentication**
- Genie queries respect the user's permissions
- Different users see different data based on their access

---

## Request Format

### Basic Request

```typescript
interface AgentRequest {
  input: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  custom_inputs?: {
    user_id?: string;
    session_id?: string;
    thread_id?: string;
    genie_conversation_ids?: Record<string, string>;
    request_id?: string;
  };
}
```

### Example: First Query

```typescript
const request = {
  input: [
    {
      role: "user",
      content: "What are the top 5 most expensive jobs this month?"
    }
  ],
  custom_inputs: {
    user_id: "user@company.com",
    session_id: generateSessionId(),  // UUID for this browser session
    request_id: generateRequestId()   // UUID for this specific request
  }
};
```

### Example: Follow-Up Query (With Memory)

```typescript
const request = {
  input: [
    {
      role: "user",
      content: "How does that compare to last month?"
    }
  ],
  custom_inputs: {
    user_id: "user@company.com",
    session_id: previousSessionId,     // SAME session ID
    thread_id: previousThreadId,       // From previous response
    genie_conversation_ids: previousGenieConvIds,  // From previous response
    request_id: generateRequestId()    // NEW request ID
  }
};
```

---

## Response Format

### Non-Streaming Response

```typescript
interface AgentResponse {
  id: string;  // Response ID
  output: Array<{
    type: "message";
    id: string;
    role: "assistant";
    content: Array<{
      type: "output_text";
      text: string;  // Natural language response (markdown formatted)
    }>;
  }>;
  custom_outputs: {
    // Memory & State
    thread_id: string;
    genie_conversation_ids: Record<string, string>;
    memory_status: "saved" | "error";
    
    // Query Metadata
    domain: string;  // "cost" | "security" | "performance" | "reliability" | "quality" | "unified"
    source: "genie" | "error";
    confidence?: number;
    sources?: string[];
    
    // Visualization (NEW)
    visualization_hint: VisualizationHint;
    data: TableRow[] | null;
    
    // Error Handling
    error?: string;
  };
}
```

### Example Response

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
          "text": "**Analysis:**\nThe top 5 most expensive jobs this month are led by ETL Pipeline at $1,250.50...\n\n**Query Results:**\n| Job Name | Total Cost |\n|----------|------------|\n| ETL Pipeline | $1,250.50 |\n..."
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
      {"Job Name": "ETL Pipeline", "Total Cost": "1250.50"},
      {"Job Name": "ML Training", "Total Cost": "980.25"},
      {"Job Name": "Data Validation", "Total Cost": "450.75"},
      {"Job Name": "Reporting", "Total Cost": "320.00"},
      {"Job Name": "Archive", "Total Cost": "180.50"}
    ]
  }
}
```

---

## Streaming Responses

### Why Streaming?

**User Experience Benefits**:
- ✅ Immediate feedback ("Querying Cost Genie Space...")
- ✅ Real-time display of analysis as it generates
- ✅ Reduced perceived latency
- ✅ Cancellable long-running queries

### Streaming API Call

```typescript
async function* streamAgentResponse(request: AgentRequest): AsyncGenerator<string> {
  const response = await fetch(
    `${ENDPOINT_URL}?stream=true`,  // ⚠️ CRITICAL: Add ?stream=true
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    }
  );

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  let buffer = '';
  
  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    // Split by newlines (SSE format)
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';  // Keep incomplete line in buffer
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const jsonStr = line.slice(6);  // Remove "data: " prefix
        
        try {
          const event = JSON.parse(jsonStr);
          
          // Yield text deltas for display
          if (event.type === 'response.output_item.delta') {
            if (event.delta?.type === 'output_text' && event.delta.text) {
              yield event.delta.text;
            }
          }
          
          // Final response with custom_outputs
          if (event.type === 'response.done') {
            // Store custom_outputs for next request
            const customOutputs = event.custom_outputs;
            return customOutputs;
          }
        } catch (e) {
          console.error('Failed to parse SSE event:', e);
        }
      }
    }
  }
}
```

### React Hook for Streaming

```typescript
import { useState, useCallback } from 'react';

interface StreamingState {
  content: string;
  isStreaming: boolean;
  customOutputs: any | null;
  error: string | null;
}

export function useAgentStreaming() {
  const [state, setState] = useState<StreamingState>({
    content: '',
    isStreaming: false,
    customOutputs: null,
    error: null
  });

  const sendMessage = useCallback(async (request: AgentRequest) => {
    setState({ content: '', isStreaming: true, customOutputs: null, error: null });
    
    try {
      const stream = streamAgentResponse(request);
      
      for await (const chunk of stream) {
        if (typeof chunk === 'string') {
          // Text delta - append to content
          setState(prev => ({
            ...prev,
            content: prev.content + chunk
          }));
        } else {
          // Final custom_outputs
          setState(prev => ({
            ...prev,
            isStreaming: false,
            customOutputs: chunk
          }));
        }
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: error.message
      }));
    }
  }, []);

  return { ...state, sendMessage };
}
```

### Streaming Fallback

**If streaming fails or is not supported**:

```typescript
async function sendNonStreamingRequest(request: AgentRequest): Promise<AgentResponse> {
  const response = await fetch(ENDPOINT_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    throw new Error(`Agent request failed: ${response.status}`);
  }
  
  return await response.json();
}
```

**When to use non-streaming**:
- Browser doesn't support streaming
- Network doesn't support SSE
- User preference for instant full responses
- Automated testing or batch queries

---

## Visualization Hints

### Parsing Hints from Response

```typescript
function extractVisualizationData(response: AgentResponse) {
  const customOutputs = response.custom_outputs;
  
  // Get the domain that responded (usually only one)
  const domain = customOutputs.domain || Object.keys(customOutputs.visualization_hints || {})[0];
  
  const hint = customOutputs.visualization_hint;
  const data = customOutputs.data;
  
  return { hint, data, domain };
}
```

### Rendering Based on Hint Type

```typescript
interface VisualizationProps {
  hint: VisualizationHint;
  data: TableRow[];
  domain: string;
}

export function AgentVisualization({ hint, data, domain }: VisualizationProps) {
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  
  if (!hint || !data) {
    return <EmptyState message="No data to display" />;
  }
  
  // User can toggle between chart and table
  if (viewMode === 'table' || hint.type === 'table' || hint.type === 'text') {
    return <DataTable data={data} />;
  }
  
  // Render chart based on hint type
  switch (hint.type) {
    case 'bar_chart':
      return <BarChart hint={hint} data={data} domain={domain} />;
    
    case 'line_chart':
      return <LineChart hint={hint} data={data} domain={domain} />;
    
    case 'pie_chart':
      return <PieChart hint={hint} data={data} domain={domain} />;
    
    case 'error':
      return <ErrorDisplay message={hint.reason} />;
    
    default:
      return <DataTable data={data} />;
  }
}
```

### Bar Chart Component

```typescript
import { BarChart as RechartsBar, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function BarChart({ hint, data, domain }: VisualizationProps) {
  const { x_axis, y_axis, title } = hint;
  const prefs = hint.domain_preferences || {};
  
  // Domain-specific color schemes
  const getColor = (domain: string) => {
    const colors = {
      cost: '#FF3621',      // Databricks Lava-600
      performance: '#2272B4', // Databricks Blue-600
      security: '#FF5F46',    // Lava-500
      reliability: '#00A972',  // Green-600
      quality: '#98102A'      // Maroon-600
    };
    return colors[domain] || '#2272B4';
  };
  
  // Format values based on preferences
  const formatValue = (value: string | number) => {
    const num = typeof value === 'string' ? parseFloat(value.replace(/[$,]/g, '')) : value;
    
    if (prefs.prefer_currency_format) {
      return `$${num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
    }
    return num.toLocaleString();
  };
  
  return (
    <div className="visualization-container">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={400}>
        <RechartsBar data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={x_axis} />
          <YAxis tickFormatter={formatValue} />
          <Tooltip formatter={formatValue} />
          <Legend />
          <Bar dataKey={y_axis} fill={getColor(domain)} />
        </RechartsBar>
      </ResponsiveContainer>
      
      <button 
        onClick={() => /* Toggle to table view */}
        className="mt-4 text-sm text-blue-600"
      >
        📊 View as Table
      </button>
    </div>
  );
}
```

**See [14-visualization-hints-frontend.md](14-visualization-hints-frontend.md) for complete chart implementations.**

---

## Short-Term Memory

### What is Short-Term Memory?

**Short-term memory** persists conversation context **within a single session** (browser tab, chat window).

- **Duration**: 24 hours by default
- **Storage**: Lakebase `checkpoints` table
- **Key**: `thread_id` (unique per conversation thread)
- **Purpose**: Enable follow-up questions that reference previous context

### Frontend Responsibilities

#### 1. Generate Session ID (Once per Page Load)

```typescript
// On app initialization or page load
const sessionId = crypto.randomUUID();  // e.g., "a1b2c3d4-e5f6-..."
sessionStorage.setItem('agent_session_id', sessionId);
```

#### 2. Track thread_id (Returned by Agent)

```typescript
interface ConversationState {
  sessionId: string;
  threadId: string | null;
  genieConversationIds: Record<string, string>;
}

const [conversation, setConversation] = useState<ConversationState>({
  sessionId: sessionStorage.getItem('agent_session_id') || crypto.randomUUID(),
  threadId: null,
  genieConversationIds: {}
});
```

#### 3. Include thread_id in Subsequent Requests

```typescript
async function sendFollowUpMessage(content: string) {
  const request = {
    input: [{ role: "user", content }],
    custom_inputs: {
      user_id: userEmail,
      session_id: conversation.sessionId,
      thread_id: conversation.threadId,  // ✅ Include previous thread_id
      genie_conversation_ids: conversation.genieConversationIds,
      request_id: crypto.randomUUID()
    }
  };
  
  const response = await sendAgentRequest(request);
  
  // Update thread_id from response
  setConversation(prev => ({
    ...prev,
    threadId: response.custom_outputs.thread_id,  // ✅ Store new thread_id
    genieConversationIds: response.custom_outputs.genie_conversation_ids
  }));
  
  return response;
}
```

### How Agent Uses thread_id

**Backend Behavior**:
1. If `thread_id` is provided, agent loads previous conversation from Lakebase
2. Agent appends new query and response to conversation history
3. Agent returns updated `thread_id` in response
4. Context is available for up to 24 hours

**Example Conversation Flow**:

```
User: "What are the top 5 expensive jobs?"
Agent: [Returns thread_id: "thread_abc123"]

User: "How do these compare to last month?"  [Includes thread_id: "thread_abc123"]
Agent: [Knows "these" refers to "top 5 expensive jobs"]
      [Returns same thread_id: "thread_abc123"]
```

### Memory Initialization

**⚠️ IMPORTANT**: Memory tables auto-initialize on first conversation.

**Backend behavior**:
- First query: May show warning `⚠ relation "checkpoints" does not exist`
- Agent creates tables automatically
- Subsequent queries use existing tables

**Frontend should**:
- Ignore first-conversation warnings
- Continue normally if `memory_status: "saved"` in response

---

## Long-Term Memory

### What is Long-Term Memory?

**Long-term memory** persists user preferences and insights **across sessions** (days, weeks, months).

- **Duration**: 365 days by default
- **Storage**: Lakebase `store` table with semantic search
- **Key**: `user_id` (typically email address)
- **Purpose**: Personalize responses based on past interactions

### How Agent Uses user_id

**Backend Behavior**:
1. Extract insights from each query/response pair (e.g., "user frequently asks about cost")
2. Store insights with embeddings for semantic search
3. On new query, retrieve relevant past insights
4. Use insights to personalize response

**Example**:

```
Day 1:
User: "Show me serverless costs"
Agent: [Saves insight: "User interested in serverless compute cost tracking"]

Day 7:
User: "What are my biggest costs?"
Agent: [Retrieves insight: "User interested in serverless compute cost tracking"]
      [Prioritizes serverless breakdowns in response]
```

### Frontend Responsibilities

#### 1. Provide Consistent user_id

```typescript
// User's email or unique identifier
const userId = getUserEmail();  // e.g., "user@company.com"

const request = {
  input: [{ role: "user", content: query }],
  custom_inputs: {
    user_id: userId,  // ✅ ALWAYS include user_id
    session_id: sessionId,
    request_id: requestId
  }
};
```

#### 2. No Additional Storage Needed

**Long-term memory is fully managed by the backend**. Frontend just needs to:
- ✅ Include `user_id` in every request
- ✅ That's it!

### Viewing User Insights (Optional)

**If you want to show user their stored insights**:

```sql
-- Query the long-term memory table directly
SELECT
  document_id,
  content,
  timestamp,
  metadata
FROM vibe_coding_workshop_lakebase.store
WHERE namespace = '<user_id>'
ORDER BY timestamp DESC
LIMIT 10;
```

**UI Feature Idea**:
- "Your Agent Preferences" page
- Show insights the agent has learned
- Allow users to delete specific insights
- Useful for transparency and GDPR compliance

---

## Genie Follow-Up Questions

### What Are Genie Conversations?

**Genie conversations** enable follow-up questions that reference previous queries **within the same domain**.

**Example**:
```
User: "What are the top 5 expensive jobs?"
Agent: [Cost Genie creates conversation: "conv_abc123"]

User: "Show me details for the first one"
Agent: [Uses conversation: "conv_abc123" to understand "first one" = "ETL Pipeline"]
```

### Frontend Responsibilities

#### 1. Track genie_conversation_ids Per Domain

```typescript
interface GenieConversations {
  cost?: string;
  security?: string;
  performance?: string;
  reliability?: string;
  quality?: string;
  unified?: string;
}

const [genieConversations, setGenieConversations] = useState<GenieConversations>({});
```

#### 2. Include in Requests

```typescript
const request = {
  input: [{ role: "user", content: "Show me details for the first one" }],
  custom_inputs: {
    user_id: userId,
    session_id: sessionId,
    thread_id: threadId,
    genie_conversation_ids: genieConversations,  // ✅ Include all domain conversations
    request_id: requestId
  }
};
```

#### 3. Update After Each Response

```typescript
async function sendMessage(content: string) {
  const response = await sendAgentRequest({
    input: [{ role: "user", content }],
    custom_inputs: {
      user_id: userId,
      session_id: sessionId,
      thread_id: threadId,
      genie_conversation_ids: genieConversations,
      request_id: crypto.randomUUID()
    }
  });
  
  // Update conversation IDs from response
  setGenieConversations(response.custom_outputs.genie_conversation_ids || {});
  
  return response;
}
```

### When to Reset Conversations

**Reset genie_conversation_ids when**:
- User clicks "New Conversation" button
- User switches to a different topic/domain
- Session expires (user closes tab)
- Error occurs (optional, for clean slate)

```typescript
function startNewConversation() {
  setGenieConversations({});  // Clear all domain conversations
  setThreadId(null);          // Clear short-term memory
  setSessionId(crypto.randomUUID());  // New session
}
```

---

## Error Handling

### Error Types

| Error Type | custom_outputs.source | Handling |
|---|---|---|
| **Genie Query Failed** | `"error"` | Show error message, offer retry |
| **Permission Error** | `"error"` | Show permission instructions |
| **Genie Space Not Configured** | `"error"` | Show configuration error |
| **Timeout** | `"error"` | Offer retry with timeout warning |
| **Rate Limit** | `"error"` | Show wait message, auto-retry in 60s |

### Error Display Component

```typescript
export function ErrorDisplay({ customOutputs }: { customOutputs: any }) {
  const error = customOutputs.error;
  const domain = customOutputs.domain;
  
  // Permission error - show instructions
  if (error?.toLowerCase().includes('permission')) {
    return (
      <div className="error-container bg-red-50 border border-red-200 p-4 rounded">
        <h3 className="text-red-800 font-semibold mb-2">🔒 Permission Required</h3>
        <p className="text-red-700">
          You need CAN USE permission on the SQL warehouse and Genie Space for {domain}.
        </p>
        <button 
          onClick={() => window.open('/docs/genie-permissions', '_blank')}
          className="mt-2 text-sm text-blue-600 underline"
        >
          View Permission Setup Guide →
        </button>
      </div>
    );
  }
  
  // Rate limit error - auto-retry
  if (error?.toLowerCase().includes('rate limit')) {
    return (
      <div className="error-container bg-yellow-50 border border-yellow-200 p-4 rounded">
        <h3 className="text-yellow-800 font-semibold mb-2">⏳ Rate Limit Reached</h3>
        <p className="text-yellow-700">
          Genie API rate limit reached (5 queries/minute). Retrying in 60 seconds...
        </p>
      </div>
    );
  }
  
  // Generic error - show retry
  return (
    <div className="error-container bg-gray-50 border border-gray-200 p-4 rounded">
      <h3 className="text-gray-800 font-semibold mb-2">❌ Query Failed</h3>
      <p className="text-gray-700">{error || "An unknown error occurred"}</p>
      <button 
        onClick={handleRetry}
        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded"
      >
        🔄 Retry Query
      </button>
    </div>
  );
}
```

### Retry Logic with Exponential Backoff

```typescript
async function sendWithRetry(
  request: AgentRequest,
  maxRetries: number = 3
): Promise<AgentResponse> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await sendAgentRequest(request);
      
      // Success - return immediately
      if (response.custom_outputs.source !== 'error') {
        return response;
      }
      
      // Check if error is retryable
      const error = response.custom_outputs.error || '';
      if (!isRetryableError(error)) {
        return response;  // Don't retry permission/config errors
      }
      
      lastError = new Error(error);
      
      // Exponential backoff: 1s, 2s, 4s
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      
    } catch (error) {
      lastError = error;
    }
  }
  
  throw lastError || new Error('Max retries exceeded');
}

function isRetryableError(error: string): boolean {
  const retryable = ['timeout', 'rate limit', 'temporary', 'unavailable'];
  return retryable.some(keyword => error.toLowerCase().includes(keyword));
}
```

---

## Complete React Integration Example

### Full Chat Component

```typescript
import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  customOutputs?: any;
  timestamp: Date;
}

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Conversation state
  const [sessionId] = useState(() => crypto.randomUUID());
  const [threadId, setThreadId] = useState<string | null>(null);
  const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({});
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const sendMessage = async () => {
    if (!inputValue.trim()) return;
    
    // Add user message to UI
    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    try {
      // Build request with memory context
      const request = {
        input: [{ role: "user", content: inputValue }],
        custom_inputs: {
          user_id: getUserEmail(),
          session_id: sessionId,
          thread_id: threadId,  // For short-term memory
          genie_conversation_ids: genieConvIds,  // For Genie follow-ups
          request_id: crypto.randomUUID()
        }
      };
      
      // Send to agent (streaming)
      let responseContent = '';
      const stream = streamAgentResponse(request);
      
      // Add placeholder message
      const placeholderMessage: Message = {
        role: 'assistant',
        content: '',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, placeholderMessage]);
      
      for await (const chunk of stream) {
        if (typeof chunk === 'string') {
          // Text delta - update placeholder
          responseContent += chunk;
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1].content = responseContent;
            return updated;
          });
        } else {
          // Final custom_outputs
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1].customOutputs = chunk;
            return updated;
          });
          
          // Update conversation state for next query
          setThreadId(chunk.thread_id);
          setGenieConvIds(chunk.genie_conversation_ids || {});
        }
      }
      
    } catch (error) {
      console.error('Agent error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}. Please try again.`,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="chat-container h-screen flex flex-col">
      {/* Header */}
      <div className="chat-header bg-db-navy text-white p-4">
        <h1 className="text-xl font-semibold">Databricks Health Monitor</h1>
        <p className="text-sm text-gray-300">
          Session: {sessionId.slice(0, 8)}...
          {threadId && ` | Thread: ${threadId.slice(0, 8)}...`}
        </p>
      </div>
      
      {/* Messages */}
      <div className="chat-messages flex-1 overflow-y-auto p-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="chat-input border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about costs, security, performance..."
            className="flex-1 px-4 py-2 border rounded"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-2 bg-primary text-white rounded disabled:opacity-50"
          >
            {isLoading ? '⏳' : '📤'} Send
          </button>
        </div>
        
        {threadId && (
          <button
            onClick={() => {
              setThreadId(null);
              setGenieConvIds({});
              setMessages([]);
            }}
            className="mt-2 text-sm text-gray-600 hover:text-gray-800"
          >
            🔄 New Conversation
          </button>
        )}
      </div>
    </div>
  );
}
```

### Message Bubble Component

```typescript
interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const customOutputs = message.customOutputs;
  
  return (
    <div className={`message-bubble mb-4 ${isUser ? 'text-right' : 'text-left'}`}>
      {/* User Message */}
      {isUser && (
        <div className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg max-w-2xl">
          {message.content}
        </div>
      )}
      
      {/* Assistant Message */}
      {!isUser && (
        <div className="inline-block bg-white border border-gray-200 px-4 py-2 rounded-lg max-w-4xl">
          {/* Natural language response */}
          <div className="prose mb-4">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
          
          {/* Visualization (if data available) */}
          {customOutputs?.data && customOutputs?.visualization_hint && (
            <AgentVisualization
              hint={customOutputs.visualization_hint}
              data={customOutputs.data}
              domain={customOutputs.domain}
            />
          )}
          
          {/* Metadata */}
          <div className="text-xs text-gray-500 mt-2 flex gap-4">
            <span>🏷️ {customOutputs?.domain || 'unknown'}</span>
            {customOutputs?.memory_status === 'saved' && (
              <span>💾 Saved to memory</span>
            )}
            <span>⏱️ {message.timestamp.toLocaleTimeString()}</span>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## State Management Best Practices

### Conversation State Structure

```typescript
interface AgentState {
  // Identity
  userId: string;
  sessionId: string;
  
  // Short-term memory (conversation context)
  threadId: string | null;
  
  // Genie conversations (per domain)
  genieConversationIds: Record<string, string>;
  
  // UI state
  messages: Message[];
  isLoading: boolean;
  currentDomain: string | null;
}
```

### State Persistence

#### Session Storage (Recommended)

**Persist for browser session only**:

```typescript
// On state change
useEffect(() => {
  sessionStorage.setItem('agent_state', JSON.stringify({
    sessionId,
    threadId,
    genieConversationIds
  }));
}, [sessionId, threadId, genieConversationIds]);

// On component mount
useEffect(() => {
  const saved = sessionStorage.getItem('agent_state');
  if (saved) {
    const state = JSON.parse(saved);
    setSessionId(state.sessionId);
    setThreadId(state.threadId);
    setGenieConvIds(state.genieConversationIds);
  }
}, []);
```

#### Local Storage (Optional)

**Persist across browser sessions**:

```typescript
// Save messages to local storage for history
useEffect(() => {
  localStorage.setItem(`agent_history_${userId}`, JSON.stringify(messages));
}, [messages, userId]);
```

**⚠️ Caution**: Messages may contain sensitive data. Consider:
- Encryption before storage
- Clear on logout
- Respect user privacy settings

---

## Performance Optimization

### Debounce Input

**Prevent accidental multiple submissions**:

```typescript
import { debounce } from 'lodash';

const debouncedSend = useCallback(
  debounce((content: string) => {
    sendMessage(content);
  }, 300),
  []
);
```

### Lazy Load Chart Library

**Only load Recharts when needed**:

```typescript
import { lazy, Suspense } from 'react';

const BarChart = lazy(() => import('./charts/BarChart'));
const LineChart = lazy(() => import('./charts/LineChart'));
const PieChart = lazy(() => import('./charts/PieChart'));

export function AgentVisualization({ hint, data, domain }) {
  return (
    <Suspense fallback={<ChartLoadingSkeleton />}>
      {hint.type === 'bar_chart' && <BarChart {...props} />}
      {hint.type === 'line_chart' && <LineChart {...props} />}
      {hint.type === 'pie_chart' && <PieChart {...props} />}
    </Suspense>
  );
}
```

### Virtualize Long Message Lists

**For chat history with 100+ messages**:

```typescript
import { FixedSizeList } from 'react-window';

export function MessageList({ messages }: { messages: Message[] }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={messages.length}
      itemSize={150}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          <MessageBubble message={messages[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

---

## Security Considerations

### 1. Token Management

**NEVER store tokens in localStorage**:

```typescript
// ❌ BAD: Exposes token to XSS
localStorage.setItem('databricks_token', userToken);

// ✅ GOOD: Use secure httpOnly cookies
// Token should be managed by backend auth service
```

### 2. Input Sanitization

**Sanitize user input before sending**:

```typescript
import DOMPurify from 'isomorphic-dompurify';

function sanitizeInput(content: string): string {
  // Remove script tags, dangerous HTML
  const clean = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: [],  // Strip all HTML
    ALLOWED_ATTR: []
  });
  
  // Limit length
  return clean.slice(0, 5000);
}

const request = {
  input: [{ role: "user", content: sanitizeInput(userInput) }]
};
```

### 3. Response Validation

**Validate response structure**:

```typescript
function validateAgentResponse(response: any): response is AgentResponse {
  if (!response || typeof response !== 'object') return false;
  if (!response.output || !Array.isArray(response.output)) return false;
  if (!response.custom_outputs) return false;
  
  return true;
}

const response = await sendAgentRequest(request);
if (!validateAgentResponse(response)) {
  throw new Error('Invalid response format');
}
```

---

## Accessibility

### Keyboard Navigation

```typescript
// Support Enter to send, Escape to cancel
<input
  onKeyDown={(e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
    if (e.key === 'Escape') {
      setInputValue('');
    }
  }}
/>
```

### Screen Reader Support

```typescript
<button
  onClick={sendMessage}
  aria-label="Send message to Health Monitor Agent"
  aria-busy={isLoading}
>
  Send
</button>

<div
  role="log"
  aria-live="polite"
  aria-label="Agent responses"
>
  {messages.map(msg => (
    <div key={msg.id} role="article">
      <span className="sr-only">
        {msg.role === 'user' ? 'You said' : 'Agent responded'}:
      </span>
      {msg.content}
    </div>
  ))}
</div>
```

### Loading States

```typescript
{isLoading && (
  <div className="loading-indicator flex items-center gap-2" role="status">
    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <span>Querying Databricks system data...</span>
    <span className="sr-only">Loading response from agent</span>
  </div>
)}
```

---

## Testing

### Manual Testing Checklist

- [ ] **Basic query** works without memory
- [ ] **Follow-up question** uses previous context (thread_id)
- [ ] **Genie follow-up** references previous query ("Show me details for the first one")
- [ ] **Visualization hints** render correct chart types
- [ ] **Toggle** between chart and table view works
- [ ] **Error states** display user-friendly messages
- [ ] **New conversation** clears memory correctly
- [ ] **Multiple sessions** don't interfere with each other
- [ ] **Streaming** displays real-time updates
- [ ] **Fallback** to non-streaming works if streaming fails

### Integration Tests

```typescript
describe('Agent Integration', () => {
  it('should maintain conversation context', async () => {
    // First query
    const response1 = await sendAgentRequest({
      input: [{ role: "user", content: "Show top 5 jobs" }],
      custom_inputs: { user_id: "test@example.com", session_id: "test_session" }
    });
    
    const threadId = response1.custom_outputs.thread_id;
    expect(threadId).toBeTruthy();
    
    // Follow-up query with thread_id
    const response2 = await sendAgentRequest({
      input: [{ role: "user", content: "Show details for the first one" }],
      custom_inputs: {
        user_id: "test@example.com",
        session_id: "test_session",
        thread_id: threadId  // ✅ Include previous thread
      }
    });
    
    // Agent should understand "the first one" refers to first job
    expect(response2.custom_outputs.source).toBe('genie');
    expect(response2.output[0].content[0].text).toContain('ETL Pipeline');
  });
  
  it('should track genie conversations per domain', async () => {
    const response1 = await sendAgentRequest({
      input: [{ role: "user", content: "Show cost trends" }]
    });
    
    const costConvId = response1.custom_outputs.genie_conversation_ids.cost;
    expect(costConvId).toBeTruthy();
    
    const response2 = await sendAgentRequest({
      input: [{ role: "user", content: "Show me more details" }],
      custom_inputs: {
        genie_conversation_ids: { cost: costConvId }
      }
    });
    
    // Genie should understand "more details" in context of cost trends
    expect(response2.custom_outputs.domain).toBe('cost');
  });
});
```

---

## Environment Variables (Frontend)

```bash
# .env.local
NEXT_PUBLIC_DATABRICKS_WORKSPACE_URL=https://e2-demo-field-eng.cloud.databricks.com
NEXT_PUBLIC_AGENT_ENDPOINT_NAME=health_monitor_agent_dev

# Backend-only (secure)
DATABRICKS_TOKEN=dapi...  # Service account token for backend API
```

**Never expose user tokens in environment variables.**

---

## Deployment Checklist

### Before Production

- [ ] Token management secure (httpOnly cookies or backend proxy)
- [ ] Input sanitization implemented
- [ ] Response validation implemented
- [ ] Error handling covers all error types
- [ ] Retry logic with exponential backoff
- [ ] Loading states for all async operations
- [ ] Memory state persisted in sessionStorage
- [ ] New conversation clears state correctly
- [ ] Accessibility features implemented (keyboard nav, screen reader, ARIA)
- [ ] Performance optimizations (debounce, lazy loading, virtualization)
- [ ] Visualization hints render correctly
- [ ] Chart toggle works
- [ ] Mobile responsive design
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
- [ ] Integration tests pass

### Production Considerations

**Rate Limiting**:
- Genie API: 5 queries/minute per user
- Implement client-side rate limiting to avoid errors

**Monitoring**:
- Track response times
- Monitor error rates
- Log visualization hint usage
- Track memory usage effectiveness

**Feedback Loop**:
- Allow users to report incorrect visualizations
- Log chart type preferences per user
- Use data to improve visualization rules

---

## Reference Documentation

### Related Guides
- [14A - Visualization Hints: Backend](14-visualization-hints-backend.md) - Backend implementation
- [14B - Visualization Hints: Frontend](14-visualization-hints-frontend.md) - Chart rendering details
- [07 - Memory Management](07-memory-management.md) - Lakebase memory architecture
- [OBO Authentication Guide](obo-authentication-guide.md) - Authentication patterns

### Official Databricks Docs
- [Model Serving Client API](https://docs.databricks.com/api/workspace/servingendpoints)
- [AI Playground](https://docs.databricks.com/machine-learning/model-serving/playground)
- [Genie Conversation API](https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api)

---

## Quick Reference

### Essential Request Fields

```typescript
{
  input: [{ role: "user", content: "query" }],      // ✅ REQUIRED
  custom_inputs: {
    user_id: "email",                                // ✅ REQUIRED for long-term memory
    session_id: "uuid",                              // ✅ Recommended
    thread_id: "thread_id",                          // ✅ For follow-ups
    genie_conversation_ids: { domain: "conv_id" }    // ✅ For Genie follow-ups
  }
}
```

### Essential Response Fields

```typescript
{
  output: [{ content: [{ text: "response" }] }],     // Text response
  custom_outputs: {
    thread_id: "thread_id",                          // Store for next request
    genie_conversation_ids: { domain: "conv_id" },   // Store for next request
    visualization_hint: { type: "bar_chart", ... },  // Render hint
    data: [{...}],                                   // Chart data
    domain: "cost",                                  // Query domain
    source: "genie" | "error"                        // Success indicator
  }
}
```

---

**Last Updated**: January 9, 2026  
**Version**: 1.0  
**Status**: Ready for Frontend Implementation

