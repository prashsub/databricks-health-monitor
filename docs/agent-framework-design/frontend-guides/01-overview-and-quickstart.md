# Frontend Guide 01: Overview and Quickstart

> **Purpose**: Get started with the Health Monitor Agent in 10 minutes
> 
> **Audience**: Frontend developers (React, TypeScript)
> 
> **Prerequisites**: Node.js, basic React knowledge

---

## What is the Health Monitor Agent?

The **Health Monitor Agent** is a Databricks-hosted AI assistant that answers questions about your Databricks environment. It provides:

### Core Capabilities

| Feature | Description | Example |
|---|---|---|
| **Natural Language Queries** | Ask questions in plain English | "What are the top 5 expensive jobs?" |
| **Real-time Streaming** | Responses appear as they're generated | See text appear word-by-word |
| **Intelligent Visualizations** | Automatic chart type selection | Bar charts for top N, line charts for trends |
| **Conversation Memory** | Remembers context within a session | "Show me details for the first one" |
| **User Personalization** | Learns preferences across sessions | Prioritizes topics you ask about often |
| **Multi-Domain Coverage** | Cost, security, performance, reliability, quality | All Databricks platform areas |

### Technical Details

- **Hosted on**: Databricks Model Serving (serverless)
- **Authentication**: On-Behalf-Of-User (uses your permissions)
- **Response Time**: 3-15 seconds typical
- **Streaming**: Server-Sent Events (SSE)
- **Memory**: Lakebase (24-hour and 365-day retention)

---

## 10-Minute Quickstart

### Step 1: Install Dependencies (1 minute)

```bash
npm install recharts react-markdown
# or
yarn add recharts react-markdown
```

### Step 2: Configure Endpoint (1 minute)

```typescript
// config.ts
export const AGENT_CONFIG = {
  workspaceUrl: 'https://your-workspace.cloud.databricks.com',
  endpointName: 'health_monitor_agent_dev',  // or 'health_monitor_agent' for prod
  get endpointUrl() {
    return `${this.workspaceUrl}/serving-endpoints/${this.endpointName}/invocations`;
  }
};
```

### Step 3: Create API Client (3 minutes)

```typescript
// agentClient.ts
interface AgentRequest {
  input: Array<{ role: 'user' | 'assistant'; content: string }>;
  custom_inputs?: {
    user_id?: string;
    session_id?: string;
    thread_id?: string;
    genie_conversation_ids?: Record<string, string>;
  };
}

interface AgentResponse {
  output: Array<{
    type: 'message';
    content: Array<{ type: 'output_text'; text: string }>;
  }>;
  custom_outputs: {
    thread_id: string;
    genie_conversation_ids: Record<string, string>;
    memory_status: 'saved' | 'error';
    domain: string;
    source: 'genie' | 'error';
    visualization_hint?: {
      type: 'bar_chart' | 'line_chart' | 'pie_chart' | 'table' | 'text' | 'error';
      x_axis?: string;
      y_axis?: string | string[];
      title?: string;
      [key: string]: any;
    };
    data?: Array<Record<string, string | number>>;
    error?: string;
  };
}

export async function sendAgentQuery(
  query: string,
  userToken: string,
  memoryContext?: {
    userId?: string;
    sessionId?: string;
    threadId?: string;
    genieConversationIds?: Record<string, string>;
  }
): Promise<AgentResponse> {
  const request: AgentRequest = {
    input: [{ role: 'user', content: query }],
    custom_inputs: {
      user_id: memoryContext?.userId || 'anonymous',
      session_id: memoryContext?.sessionId || crypto.randomUUID(),
      thread_id: memoryContext?.threadId,
      genie_conversation_ids: memoryContext?.genieConversationIds || {}
    }
  };

  const response = await fetch(AGENT_CONFIG.endpointUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error(`Agent request failed: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}
```

### Step 4: Create Chat Component (5 minutes)

```typescript
// AgentChat.tsx
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendAgentQuery } from './agentClient';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  customOutputs?: any;
}

export function AgentChat({ userToken }: { userToken: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Memory state
  const [sessionId] = useState(() => crypto.randomUUID());
  const [threadId, setThreadId] = useState<string | null>(null);
  const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({});

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue;
    setInputValue('');
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userText }]);

    try {
      // Send to agent
      const response = await sendAgentQuery(
        userText,
        userToken,
        {
          userId: 'user@company.com',  // Replace with actual user
          sessionId,
          threadId,
          genieConversationIds: genieConvIds
        }
      );

      // Add assistant message
      const assistantText = response.output[0].content[0].text;
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: assistantText,
        customOutputs: response.custom_outputs
      }]);

      // Update memory for next query
      setThreadId(response.custom_outputs.thread_id);
      setGenieConvIds(response.custom_outputs.genie_conversation_ids);

    } catch (error) {
      console.error('Agent error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}. Please try again.`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-gray-900 text-white p-4">
        <h1 className="text-xl font-semibold">Databricks Health Monitor</h1>
        {threadId && (
          <p className="text-sm text-gray-400">
            💬 Context active | {messages.length / 2} exchanges
          </p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl rounded-lg p-4 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <ReactMarkdown>{msg.content}</ReactMarkdown>
              
              {/* Show visualization if data present */}
              {msg.customOutputs?.data && (
                <div className="mt-4 p-4 bg-gray-50 rounded">
                  <p className="text-sm text-gray-600">
                    📊 Chart: {msg.customOutputs.visualization_hint?.type || 'table'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {msg.customOutputs.data.length} rows
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600">
                <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
            placeholder="Ask about costs, security, performance..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Send
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

**That's it!** You now have a working chat interface. 🎉

---

## What You Just Built

### ✅ Working Features
- Send queries to agent
- Display natural language responses
- Track conversation context (memory)
- Clear conversation and start fresh
- Error handling

### ⚠️ Not Yet Implemented
- Streaming responses (see Guide 04)
- Chart rendering (see Guide 06)
- Advanced memory features (see Guide 05)

---

## Testing Your Integration

### Test Queries

Try these queries to verify everything works:

**Basic Query (No Memory)**:
```
"What are the top 5 most expensive jobs this month?"
```
Expected: Response with job list and costs

**Follow-Up Query (With Memory)**:
```
First: "What are the top 5 expensive jobs?"
Then: "Show me details for the first one"
```
Expected: Agent understands "the first one" = top job from previous query

**Domain Coverage**:
- Cost: "What were my total costs yesterday?"
- Security: "Show me failed login attempts today"
- Performance: "Which queries are running slowly?"
- Reliability: "Show me recent job failures"
- Quality: "Which tables have data quality issues?"

### Validation Checklist

- [ ] Can send query and receive response
- [ ] Natural language text displays correctly
- [ ] `thread_id` is stored after first query
- [ ] Second query includes `thread_id` from first query
- [ ] "New Conversation" button clears `thread_id`
- [ ] Error messages display when queries fail
- [ ] Loading state shows while waiting

---

## Common Issues

### Issue: "401 Unauthorized"
**Solution**: Check that `userToken` is a valid Databricks personal access token (PAT)

### Issue: "CORS error"
**Solution**: If calling directly from browser, your Databricks admin needs to configure CORS. Alternative: Route through your backend.

### Issue: "No response received"
**Solution**: Verify endpoint URL is correct. Check endpoint is deployed and ready.

### Issue: "Follow-up questions don't work"
**Solution**: Ensure you're including `thread_id` from previous response in subsequent requests.

---

## Next Steps

### Phase 1: Add Streaming (Recommended)
👉 **Read [04 - Streaming Responses](04-streaming-responses.md)**
- Get real-time updates instead of waiting
- Show "Querying..." → "Analyzing..." → "Complete"
- Add cancel button for long queries

### Phase 2: Add Charts (Visual Appeal)
👉 **Read [06 - Visualization Rendering](06-visualization-rendering.md)**
- Render bar charts for top N queries
- Render line charts for trends
- Render pie charts for distributions
- Add chart/table toggle

### Phase 3: Understand Authentication
👉 **Read [02 - Authentication Guide](02-authentication-guide.md)**
- Learn about On-Behalf-Of-User (OBO)
- Understand token management
- Implement secure patterns

### Phase 4: Master API Details
👉 **Read [03 - API Reference](03-api-reference.md)**
- Complete request/response reference
- All error codes and handling
- Rate limiting strategies
- TypeScript types

### Phase 5: Advanced Memory Features
👉 **Read [05 - Memory Integration](05-memory-integration.md)**
- Understand short vs long-term memory
- Implement Genie conversation continuity
- Add memory debugging tools

---

## Architecture Summary

```
┌───────────────────────────────────────────────────────────────┐
│                     Your Frontend App                          │
│                                                                 │
│  1. User types query                                            │
│  2. Send to agent endpoint with memory context                  │
│  3. Receive streaming response                                  │
│  4. Display text + optional chart                               │
│  5. Store thread_id for next query                              │
│                                                                 │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│              Databricks Model Serving Endpoint                 │
│                  (Health Monitor Agent)                         │
│                                                                 │
│  - Analyzes query intent                                        │
│  - Routes to appropriate domain (cost, security, etc.)          │
│  - Queries Genie Space with your permissions                    │
│  - Generates natural language analysis                          │
│  - Suggests visualization type                                  │
│  - Saves conversation to memory                                 │
│                                                                 │
└───────────────────────────────────────────────────────────────┘
```

---

## Request Format (Minimal)

```typescript
{
  "input": [
    { "role": "user", "content": "What are the top 5 expensive jobs?" }
  ],
  "custom_inputs": {
    "user_id": "user@company.com",
    "session_id": "uuid-from-frontend"
  }
}
```

## Response Format (Minimal)

```typescript
{
  "output": [
    {
      "type": "message",
      "content": [
        { "type": "output_text", "text": "**Analysis:**\nThe top 5..." }
      ]
    }
  ],
  "custom_outputs": {
    "thread_id": "thread_abc123",           // Store this!
    "domain": "cost",
    "source": "genie",
    "visualization_hint": {
      "type": "bar_chart",
      "x_axis": "Job Name",
      "y_axis": "Total Cost"
    },
    "data": [
      { "Job Name": "ETL Pipeline", "Total Cost": "1250.50" },
      ...
    ]
  }
}
```

---

## Essential Concepts

### 1. Memory Context
**Frontend tracks, backend stores:**
- `thread_id`: Conversation thread (changes with each query)
- `genie_conversation_ids`: Per-domain Genie conversations
- `session_id`: Your browser session (you generate once)
- `user_id`: User's email (for personalization)

**Pattern**:
```
Query 1: Send with no thread_id → Get thread_abc123
Query 2: Send with thread_abc123 → Get thread_abc123 (same)
Query 3: Send with thread_abc123 → Get thread_abc123 (same)
```

### 2. Visualization Hints
**Agent suggests, you render:**
- `bar_chart`: Comparisons, top N queries
- `line_chart`: Time series, trends
- `pie_chart`: Distributions, breakdowns
- `table`: Complex data, large datasets
- `text`: No tabular data (just text response)

**You decide**: Always provide a chart/table toggle so users can choose.

### 3. Streaming
**Optional but recommended:**
- Add `?stream=true` to URL
- Parse Server-Sent Events (SSE)
- Display text in real-time
- Better user experience

---

## Quick Reference: Essential Fields

### Request (Must Include)
```typescript
{
  input: [{ role: "user", content: "query" }],  // ✅ Required
  custom_inputs: {
    user_id: "email"                             // ✅ For personalization
  }
}
```

### Response (Must Extract)
```typescript
{
  output[0].content[0].text,                     // Natural language text
  custom_outputs: {
    thread_id,                                    // Store for next query
    genie_conversation_ids,                       // Store for Genie follow-ups
    visualization_hint,                           // Chart type suggestion
    data                                          // Tabular data (if present)
  }
}
```

---

## Next Steps

### Immediate Next Steps
1. **Copy the code above** into your project
2. **Replace `userToken`** with your Databricks PAT
3. **Test with a simple query**: "What are top 5 expensive jobs?"
4. **Verify response** includes `thread_id` and `data`

### Enhance Your Integration
Once the basic example works, enhance it:
- **Add streaming** → [Guide 04](04-streaming-responses.md)
- **Add charts** → [Guide 06](06-visualization-rendering.md)
- **Understand auth** → [Guide 02](02-authentication-guide.md)

### Production Readiness
Before deploying to production:
- **Review API details** → [Guide 03](03-api-reference.md)
- **Implement proper error handling** → [Guide 03](03-api-reference.md)
- **Add rate limiting** → [Guide 03](03-api-reference.md)
- **Secure token storage** → [Guide 02](02-authentication-guide.md)

---

**Time to First Query**: 10 minutes  
**Time to Production**: 2-3 days (following all guides)  
**Next Guide**: [02 - Authentication Guide](02-authentication-guide.md)
