# 17 - Frontend Memory Integration Guide

> ⚠️ **DEPRECATED**: This guide has been reorganized and updated.
> 
> **👉 NEW LOCATION**: See `frontend-guides/05-memory-integration.md`
> 
> **Why Moved**: Part of reorganized frontend guide series (01-06) with verified implementation.
> 
> **All Frontend Guides**: See `frontend-guides/00-README.md`

---

**This file is kept for backward compatibility but will not be updated.**

---

## Overview

The Health Monitor Agent uses **Lakebase** to provide two types of memory:

1. **Short-Term Memory** (Conversation Context)
   - Persists conversation within a session
   - Duration: 24 hours
   - Key: `thread_id`
   - Purpose: Multi-turn conversations with context

2. **Long-Term Memory** (User Preferences)
   - Persists insights across sessions
   - Duration: 365 days
   - Key: `user_id`
   - Purpose: Personalization and learning user patterns

**Frontend Responsibility**: Provide and track the correct IDs. **Backend handles all memory operations.**

---

## Short-Term Memory (Conversation Context)

### What is Short-Term Memory?

Short-term memory enables the agent to **remember previous questions and answers within a conversation thread**.

**Use Cases**:
- ✅ "Show me details for the first one" (references previous query)
- ✅ "How does that compare to last month?" (continues previous analysis)
- ✅ "Break that down by workspace" (expands on previous results)

**Storage**:
- **Backend**: Lakebase `checkpoints` table
- **Frontend**: Only stores `thread_id` (UUID)

---

### Implementation: thread_id Tracking

#### Step 1: Initialize Session

```typescript
interface ConversationSession {
  sessionId: string;       // Browser session (page load)
  threadId: string | null; // Conversation thread (from agent)
  startTime: Date;
  messageCount: number;
}

const [session, setSession] = useState<ConversationSession>(() => {
  // Try to restore from sessionStorage
  const saved = sessionStorage.getItem('agent_session');
  if (saved) {
    const parsed = JSON.parse(saved);
    // Check if session is still valid (< 24 hours old)
    const age = Date.now() - new Date(parsed.startTime).getTime();
    if (age < 24 * 60 * 60 * 1000) {  // 24 hours
      return parsed;
    }
  }
  
  // Create new session
  return {
    sessionId: crypto.randomUUID(),
    threadId: null,
    startTime: new Date(),
    messageCount: 0
  };
});

// Persist session to sessionStorage
useEffect(() => {
  sessionStorage.setItem('agent_session', JSON.stringify(session));
}, [session]);
```

#### Step 2: Include thread_id in Requests

```typescript
async function sendAgentMessage(content: string): Promise<AgentResponse> {
  const request = {
    input: [{ role: "user", content }],
    custom_inputs: {
      user_id: getUserEmail(),
      session_id: session.sessionId,
      thread_id: session.threadId,  // ✅ null for first message, UUID for follow-ups
      request_id: crypto.randomUUID()
    }
  };
  
  const response = await sendAgentRequest(request);
  return response;
}
```

#### Step 3: Update thread_id from Response

```typescript
async function sendAndUpdateMemory(content: string) {
  const response = await sendAgentMessage(content);
  
  // Extract thread_id from response
  const newThreadId = response.custom_outputs.thread_id;
  
  // Update session state
  setSession(prev => ({
    ...prev,
    threadId: newThreadId,  // ✅ Store for next request
    messageCount: prev.messageCount + 1
  }));
  
  return response;
}
```

---

### Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    CONVERSATION LIFECYCLE                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. User opens chat                                           │
│     → sessionId: generated (UUID)                             │
│     → threadId: null                                          │
│                                                               │
│  2. First query: "Show top 5 expensive jobs"                  │
│     → Request: { thread_id: null }                            │
│     → Response: { thread_id: "thread_abc123" }                │
│     → Frontend stores: thread_abc123                          │
│                                                               │
│  3. Follow-up: "How do these compare to last month?"          │
│     → Request: { thread_id: "thread_abc123" }                 │
│     → Agent loads context, understands "these" = top 5 jobs   │
│     → Response: { thread_id: "thread_abc123" }                │
│                                                               │
│  4. User clicks "New Conversation"                            │
│     → Frontend: threadId = null                               │
│     → Next query starts fresh (no context)                    │
│                                                               │
│  5. User closes tab                                           │
│     → sessionStorage cleared                                  │
│     → Next visit: new sessionId, threadId                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### UI Indicators for Memory

#### Show Memory Status

```typescript
export function MemoryStatusBadge({ threadId }: { threadId: string | null }) {
  if (!threadId) {
    return (
      <span className="text-xs text-gray-500">
        💭 No context (new conversation)
      </span>
    );
  }
  
  return (
    <span className="text-xs text-green-600 flex items-center gap-1">
      ✓ Context active
      <button
        onClick={() => showMemorySidebar()}
        className="text-blue-600 underline"
        title="View conversation context"
      >
        View
      </button>
    </span>
  );
}
```

#### Memory Context Sidebar (Optional)

```typescript
export function MemoryContextSidebar({ threadId }: { threadId: string }) {
  const [context, setContext] = useState<any>(null);
  
  useEffect(() => {
    // Optionally query backend for conversation history
    // This is for debugging/transparency, not required
    fetchConversationContext(threadId).then(setContext);
  }, [threadId]);
  
  return (
    <div className="memory-sidebar border-l p-4 w-80">
      <h3 className="font-semibold mb-2">💭 Conversation Context</h3>
      
      {context?.messages?.map((msg, idx) => (
        <div key={idx} className="text-xs mb-2 p-2 bg-gray-50 rounded">
          <div className="font-semibold">{msg.role}:</div>
          <div className="text-gray-600 truncate">{msg.content}</div>
        </div>
      ))}
      
      <button
        onClick={() => clearMemory()}
        className="mt-4 text-sm text-red-600"
      >
        🗑️ Clear Context
      </button>
    </div>
  );
}
```

---

## Long-Term Memory (User Preferences)

### What is Long-Term Memory?

Long-term memory enables the agent to **learn from past interactions** and personalize responses.

**Examples**:
- User frequently asks about serverless costs → Agent prioritizes serverless breakdowns
- User often queries security for a specific workspace → Agent filters to that workspace
- User prefers charts over tables → Agent adjusts visualization hints

**Storage**:
- **Backend**: Lakebase `store` table with semantic embeddings
- **Frontend**: Only provides `user_id`

---

### Implementation: user_id Tracking

#### Step 1: Get User Identifier

```typescript
function getUserId(): string {
  // Option 1: From authentication context
  const auth = useAuth();
  return auth.user.email;
  
  // Option 2: From backend session
  const session = await fetch('/api/session');
  const data = await session.json();
  return data.userId;
  
  // Option 3: From OAuth token
  const token = parseJWT(authToken);
  return token.email;
}
```

#### Step 2: Include in ALL Requests

```typescript
const request = {
  input: [{ role: "user", content: query }],
  custom_inputs: {
    user_id: getUserId(),  // ✅ ALWAYS include user_id
    session_id: sessionId,
    thread_id: threadId
  }
};
```

**That's it!** Backend handles:
- Extracting insights from conversations
- Storing insights with embeddings
- Retrieving relevant insights on new queries
- Personalizing responses

---

### How Backend Uses user_id

#### Insight Extraction

After each query/response pair, the agent:
1. Analyzes what the user cared about
2. Extracts actionable insights
3. Stores with semantic embeddings

**Example**:
```
User: "Show me serverless cost breakdown"
Agent extracts insight: {
  user_id: "user@example.com",
  content: "User frequently monitors serverless compute costs and prefers cost breakdowns by compute type",
  category: "preference",
  domain: "cost",
  timestamp: "2026-01-09T..."
}
```

#### Insight Retrieval

On new query, the agent:
1. Searches long-term memory for relevant insights
2. Uses semantic similarity (embeddings) to find related preferences
3. Incorporates insights into response

**Example**:
```
New query: "What are my biggest expenses?"
Agent retrieves: "User frequently monitors serverless compute costs..."
Agent prioritizes: Serverless cost breakdown in response
```

---

### UI for User Insights (Optional Feature)

#### Show What Agent Has Learned

```typescript
export function UserInsightsDashboard({ userId }: { userId: string }) {
  const [insights, setInsights] = useState<Insight[]>([]);
  
  useEffect(() => {
    // Query long-term memory table
    fetchUserInsights(userId).then(setInsights);
  }, [userId]);
  
  return (
    <div className="insights-dashboard">
      <h2 className="text-xl font-semibold mb-4">
        🧠 What Your Agent Has Learned
      </h2>
      
      <div className="grid gap-4">
        {insights.map(insight => (
          <div key={insight.id} className="insight-card p-4 border rounded">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-sm font-semibold text-gray-700">
                  {insight.category}
                </span>
                <p className="text-sm text-gray-600 mt-1">
                  {insight.content}
                </p>
                <div className="text-xs text-gray-400 mt-2">
                  {new Date(insight.timestamp).toLocaleDateString()}
                </div>
              </div>
              
              <button
                onClick={() => deleteInsight(insight.id)}
                className="text-red-600 hover:text-red-800"
                title="Delete this insight"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>
      
      <button
        onClick={() => clearAllInsights(userId)}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
      >
        Clear All Insights
      </button>
    </div>
  );
}

interface Insight {
  id: string;
  content: string;
  category: string;
  timestamp: string;
  domain: string;
}

async function fetchUserInsights(userId: string): Promise<Insight[]> {
  // Query Lakebase store table via backend API
  const response = await fetch(`/api/agent/insights?user_id=${userId}`);
  return await response.json();
}
```

#### Backend API for Insights (Python)

```python
# Backend endpoint to query Lakebase store
from databricks_langchain.memory import DatabricksStore
from databricks.sdk import WorkspaceClient

def get_user_insights(user_id: str):
    """Get all stored insights for a user."""
    client = WorkspaceClient()
    store = DatabricksStore(
        client=client,
        database_instance_name="vibe-coding-workshop-lakebase",
        embedding_endpoint="databricks-gte-large-en"
    )
    
    # Query store by namespace (user_id)
    insights = store.search(
        query="",  # Empty query returns all
        namespace=user_id,
        k=50  # Return up to 50 insights
    )
    
    return [
        {
            "id": doc.id,
            "content": doc.page_content,
            "timestamp": doc.metadata.get("timestamp"),
            "domain": doc.metadata.get("domain"),
            "category": doc.metadata.get("category", "general")
        }
        for doc in insights
    ]
```

---

### Privacy & Transparency

#### GDPR Compliance

**Allow users to view and delete their data**:

```typescript
export function PrivacyControls({ userId }: { userId: string }) {
  const [isLoading, setIsLoading] = useState(false);
  
  const exportData = async () => {
    const insights = await fetchUserInsights(userId);
    const dataStr = JSON.stringify(insights, null, 2);
    
    // Download as JSON file
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-insights-${userId}-${Date.now()}.json`;
    a.click();
  };
  
  const deleteAllData = async () => {
    if (!confirm('Delete all agent insights? This cannot be undone.')) return;
    
    setIsLoading(true);
    try {
      await fetch(`/api/agent/insights?user_id=${userId}`, {
        method: 'DELETE'
      });
      alert('All insights deleted successfully');
    } catch (error) {
      alert('Error deleting insights: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="privacy-controls p-4 border rounded">
      <h3 className="font-semibold mb-4">🔒 Privacy & Data</h3>
      
      <div className="flex gap-4">
        <button
          onClick={exportData}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          📥 Export My Data
        </button>
        
        <button
          onClick={deleteAllData}
          disabled={isLoading}
          className="px-4 py-2 bg-red-600 text-white rounded"
        >
          🗑️ Delete All Insights
        </button>
      </div>
      
      <p className="text-xs text-gray-500 mt-4">
        The agent stores insights from your conversations to improve future responses.
        You can export or delete this data at any time.
      </p>
    </div>
  );
}
```

---

## Memory State Management

### Complete State Interface

```typescript
interface MemoryState {
  // Short-term memory (conversation context)
  sessionId: string;       // Browser session UUID
  threadId: string | null; // Conversation thread (from agent response)
  
  // Long-term memory (user preferences)
  userId: string;          // User's email or unique ID
  
  // Genie conversations (per domain)
  genieConversationIds: Record<string, string>;
  
  // Metadata
  lastUpdated: Date;
  memoryStatus: 'active' | 'inactive' | 'error';
}
```

### React Context for Memory

```typescript
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface MemoryContextType {
  state: MemoryState;
  updateFromResponse: (customOutputs: any) => void;
  startNewConversation: () => void;
  clearMemory: () => void;
}

const MemoryContext = createContext<MemoryContextType | null>(null);

export function MemoryProvider({ children, userId }: { children: ReactNode; userId: string }) {
  const [state, setState] = useState<MemoryState>(() => {
    // Restore from sessionStorage
    const saved = sessionStorage.getItem('agent_memory');
    if (saved) {
      const parsed = JSON.parse(saved);
      // Validate session age
      const age = Date.now() - new Date(parsed.lastUpdated).getTime();
      if (age < 24 * 60 * 60 * 1000) {
        return { ...parsed, userId };  // Keep session, update userId
      }
    }
    
    // New memory state
    return {
      sessionId: crypto.randomUUID(),
      threadId: null,
      userId,
      genieConversationIds: {},
      lastUpdated: new Date(),
      memoryStatus: 'inactive'
    };
  });
  
  // Persist to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('agent_memory', JSON.stringify(state));
  }, [state]);
  
  const updateFromResponse = useCallback((customOutputs: any) => {
    setState(prev => ({
      ...prev,
      threadId: customOutputs.thread_id || prev.threadId,
      genieConversationIds: customOutputs.genie_conversation_ids || prev.genieConversationIds,
      lastUpdated: new Date(),
      memoryStatus: customOutputs.memory_status === 'saved' ? 'active' : 'error'
    }));
  }, []);
  
  const startNewConversation = useCallback(() => {
    setState(prev => ({
      ...prev,
      threadId: null,
      genieConversationIds: {},
      sessionId: crypto.randomUUID(),
      lastUpdated: new Date(),
      memoryStatus: 'inactive'
    }));
  }, []);
  
  const clearMemory = useCallback(() => {
    sessionStorage.removeItem('agent_memory');
    setState({
      sessionId: crypto.randomUUID(),
      threadId: null,
      userId,
      genieConversationIds: {},
      lastUpdated: new Date(),
      memoryStatus: 'inactive'
    });
  }, [userId]);
  
  return (
    <MemoryContext.Provider value={{ state, updateFromResponse, startNewConversation, clearMemory }}>
      {children}
    </MemoryContext.Provider>
  );
}

export function useMemory() {
  const context = useContext(MemoryContext);
  if (!context) {
    throw new Error('useMemory must be used within MemoryProvider');
  }
  return context;
}
```

### Usage in Chat Component

```typescript
export function ChatComponent() {
  const { state: memoryState, updateFromResponse } = useMemory();
  
  const sendMessage = async (text: string) => {
    const request = {
      input: [{ role: "user", content: text }],
      custom_inputs: {
        user_id: memoryState.userId,
        session_id: memoryState.sessionId,
        thread_id: memoryState.threadId,  // ✅ From context
        genie_conversation_ids: memoryState.genieConversationIds,
        request_id: crypto.randomUUID()
      }
    };
    
    const response = await sendAgentRequest(request);
    
    // Update memory state from response
    updateFromResponse(response.custom_outputs);
    
    return response;
  };
  
  return (
    <div>
      <MemoryStatusIndicator state={memoryState} />
      {/* ... chat interface */}
    </div>
  );
}
```

---

## Genie Conversation Continuity

### Per-Domain Conversation Tracking

**Why per-domain?** Each Genie Space maintains its own conversation context. If user asks about cost, then security, then cost again, the cost Genie should remember the first cost question.

```typescript
interface GenieConversations {
  cost?: string;
  security?: string;
  performance?: string;
  reliability?: string;
  quality?: string;
  unified?: string;
}

const [genieConvIds, setGenieConvIds] = useState<GenieConversations>({});
```

### Tracking Pattern

```typescript
async function sendMessage(text: string) {
  // 1. Include current conversation IDs
  const request = {
    input: [{ role: "user", content: text }],
    custom_inputs: {
      user_id: userId,
      genie_conversation_ids: genieConvIds  // ✅ All domain conversations
    }
  };
  
  // 2. Send request
  const response = await sendAgentRequest(request);
  
  // 3. Update conversation IDs from response
  const newConvIds = response.custom_outputs.genie_conversation_ids;
  setGenieConvIds(newConvIds || {});
  
  // Example: newConvIds = { "cost": "conv_abc123" }
}
```

### Multi-Domain Example

```
User: "What are the top 5 expensive jobs?"
Agent: [domain=cost, creates conv_abc123]
       genieConvIds = { cost: "conv_abc123" }

User: "Show me recent security events"
Agent: [domain=security, creates conv_def456]
       genieConvIds = { cost: "conv_abc123", security: "conv_def456" }

User: "Compare cost trends"
Agent: [domain=cost, uses conv_abc123 for context]
       genieConvIds = { cost: "conv_abc123", security: "conv_def456" }
```

### UI for Domain Context

```typescript
export function DomainContextIndicator({ genieConvIds }: { genieConvIds: GenieConversations }) {
  const activeDomains = Object.keys(genieConvIds);
  
  if (activeDomains.length === 0) {
    return null;
  }
  
  return (
    <div className="domain-context text-xs text-gray-600 flex items-center gap-2">
      <span>🔗 Active contexts:</span>
      {activeDomains.map(domain => (
        <span key={domain} className="px-2 py-1 bg-blue-50 rounded">
          {domain}
        </span>
      ))}
    </div>
  );
}
```

---

## Memory Initialization

### ⚠️ First Conversation Warning

On the **first conversation ever**, backend may show:

```
⚠ Short-term memory retrieval failed: relation "checkpoints" does not exist
⚠ Long-term memory retrieval failed: relation "store" does not exist
```

**This is NORMAL**. The agent automatically creates these tables.

### Frontend Handling

```typescript
function handleMemoryStatus(customOutputs: any) {
  const status = customOutputs.memory_status;
  
  if (status === 'error' && customOutputs.error?.includes('does not exist')) {
    // First-time initialization - tables will be created
    console.log('Memory tables initializing (first conversation)');
    return 'initializing';
  }
  
  if (status === 'saved') {
    return 'active';
  }
  
  return 'inactive';
}

// UI indicator
{memoryStatus === 'initializing' && (
  <div className="text-xs text-blue-600 flex items-center gap-1">
    <Spinner size="xs" />
    Initializing memory (first conversation)...
  </div>
)}

{memoryStatus === 'active' && (
  <div className="text-xs text-green-600">
    ✓ Memory active
  </div>
)}
```

---

## Session Management

### When to Clear Memory

#### Clear Short-Term Memory

```typescript
function clearShortTermMemory() {
  setThreadId(null);
  setGenieConvIds({});
  
  // Optionally clear messages
  setMessages([]);
}
```

**Trigger on**:
- User clicks "New Conversation"
- User switches to different topic
- User explicitly requests context reset

#### Preserve Long-Term Memory

```typescript
// DON'T clear user_id or sessionStorage for long-term insights
// Long-term memory should persist across sessions
```

**Never clear**:
- User's long-term insights (require explicit user action)
- User preferences

### Session Timeout

```typescript
useEffect(() => {
  // Check session age
  const checkSessionAge = () => {
    if (!threadId) return;
    
    const sessionAge = Date.now() - session.startTime.getTime();
    const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;
    
    if (sessionAge > TWENTY_FOUR_HOURS) {
      // Session expired - clear short-term memory
      clearShortTermMemory();
      showToast('Session expired. Starting new conversation.');
    }
  };
  
  // Check every 5 minutes
  const interval = setInterval(checkSessionAge, 5 * 60 * 1000);
  return () => clearInterval(interval);
}, [threadId, session]);
```

---

## Memory Debugging

### Debug Panel (Development Only)

```typescript
export function MemoryDebugPanel({ memoryState }: { memoryState: MemoryState }) {
  if (process.env.NODE_ENV !== 'development') return null;
  
  return (
    <details className="debug-panel p-4 bg-gray-100 border rounded text-xs">
      <summary className="cursor-pointer font-semibold">
        🔍 Memory Debug Info
      </summary>
      
      <div className="mt-2 space-y-2">
        <div>
          <strong>Session ID:</strong> {memoryState.sessionId}
        </div>
        <div>
          <strong>Thread ID:</strong> {memoryState.threadId || '(none)'}
        </div>
        <div>
          <strong>User ID:</strong> {memoryState.userId}
        </div>
        <div>
          <strong>Genie Conversations:</strong>
          <pre className="bg-white p-2 mt-1 rounded overflow-x-auto">
            {JSON.stringify(memoryState.genieConversationIds, null, 2)}
          </pre>
        </div>
        <div>
          <strong>Last Updated:</strong> {memoryState.lastUpdated.toLocaleString()}
        </div>
        <div>
          <strong>Memory Status:</strong>{' '}
          <span className={`font-semibold ${
            memoryState.memoryStatus === 'active' ? 'text-green-600' : 'text-gray-500'
          }`}>
            {memoryState.memoryStatus}
          </span>
        </div>
      </div>
      
      <button
        onClick={() => {
          console.log('Full memory state:', memoryState);
          console.log('SessionStorage:', sessionStorage.getItem('agent_memory'));
        }}
        className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-xs"
      >
        Log to Console
      </button>
    </details>
  );
}
```

### Logging Memory Effectiveness

```typescript
// Track how often memory is used
const logMemoryUsage = (customOutputs: any) => {
  analytics.track('agent_memory_used', {
    thread_id: customOutputs.thread_id,
    had_previous_context: !!customOutputs.thread_id,
    genie_domains_active: Object.keys(customOutputs.genie_conversation_ids || {}).length,
    memory_status: customOutputs.memory_status
  });
};
```

---

## Best Practices

### 1. Always Include IDs

```typescript
// ✅ GOOD: Include all memory IDs
const request = {
  custom_inputs: {
    user_id: userId,        // Required for long-term memory
    session_id: sessionId,  // Recommended for tracking
    thread_id: threadId,    // Required for short-term memory
    genie_conversation_ids: genieConvIds  // Required for Genie follow-ups
  }
};

// ❌ BAD: Missing IDs
const request = {
  input: [{ role: "user", content: "..." }]
  // No custom_inputs!
};
```

### 2. Update After Every Response

```typescript
const response = await sendAgentRequest(request);

// ✅ ALWAYS update memory state
setThreadId(response.custom_outputs.thread_id);
setGenieConvIds(response.custom_outputs.genie_conversation_ids);

// ❌ NEVER ignore custom_outputs
```

### 3. Persist Across Page Reloads

```typescript
// Use sessionStorage (not localStorage - security)
useEffect(() => {
  sessionStorage.setItem('agent_memory', JSON.stringify({
    sessionId,
    threadId,
    genieConversationIds,
    lastUpdated: new Date()
  }));
}, [sessionId, threadId, genieConversationIds]);
```

### 4. Show Memory Status to Users

```typescript
export function MemoryStatusBadge({ threadId, messageCount }: Props) {
  if (!threadId) {
    return (
      <div className="text-xs text-gray-500">
        💭 New conversation
      </div>
    );
  }
  
  return (
    <div className="text-xs text-green-600 flex items-center gap-1">
      ✓ Context from {messageCount} previous messages
    </div>
  );
}
```

### 5. Handle Memory Errors Gracefully

```typescript
if (response.custom_outputs.memory_status === 'error') {
  console.warn('Memory save failed, but query succeeded');
  
  // Show non-blocking warning
  showToast('Memory save failed. Follow-up questions may lack context.', 'warning');
  
  // Continue normally - don't block user
}
```

---

## Testing Memory

### Test Scenarios

#### Scenario 1: Context Preservation

```typescript
test('should preserve context across messages', async () => {
  // First message
  const response1 = await sendAgentMessage("Show top 5 expensive jobs");
  const threadId = response1.custom_outputs.thread_id;
  expect(threadId).toBeTruthy();
  
  // Follow-up message
  const response2 = await sendAgentMessage("Show details for the first one", threadId);
  
  // Agent should understand "the first one" = "ETL Pipeline" (first job)
  expect(response2.output[0].content[0].text).toContain('ETL Pipeline');
});
```

#### Scenario 2: Domain Switching

```typescript
test('should maintain separate Genie conversations per domain', async () => {
  // Cost query
  const r1 = await sendAgentMessage("Show cost trends");
  const costConvId = r1.custom_outputs.genie_conversation_ids.cost;
  expect(costConvId).toBeTruthy();
  
  // Security query (different domain)
  const r2 = await sendAgentMessage("Show security events", {
    genie_conversation_ids: { cost: costConvId }
  });
  const securityConvId = r2.custom_outputs.genie_conversation_ids.security;
  expect(securityConvId).toBeTruthy();
  
  // Back to cost (should still have cost conversation)
  const r3 = await sendAgentMessage("Show more cost details", {
    genie_conversation_ids: r2.custom_outputs.genie_conversation_ids
  });
  expect(r3.custom_outputs.genie_conversation_ids.cost).toBe(costConvId);
  expect(r3.custom_outputs.genie_conversation_ids.security).toBe(securityConvId);
});
```

#### Scenario 3: Session Expiry

```typescript
test('should clear memory after 24 hours', () => {
  const oldState = {
    threadId: 'thread_abc123',
    lastUpdated: new Date(Date.now() - 25 * 60 * 60 * 1000)  // 25 hours ago
  };
  
  sessionStorage.setItem('agent_memory', JSON.stringify(oldState));
  
  // Component mount should detect expired session
  const { threadId } = restoreMemoryState();
  
  expect(threadId).toBeNull();  // Expired, should be cleared
});
```

---

## Memory Limitations

### Backend Limitations

| Feature | Limit | Impact |
|---|---|---|
| **Short-term memory TTL** | 24 hours | Conversations expire after 1 day |
| **Long-term memory TTL** | 365 days | Insights expire after 1 year |
| **Conversation messages** | ~50 messages | Lakebase CheckpointSaver limitation |
| **Insight count** | Unlimited | May impact retrieval performance |

### Frontend Considerations

**Storage Limits**:
- sessionStorage: ~5MB per origin
- Storing 100+ messages may hit limit

**Solution**:
```typescript
// Only store essential state, not full messages
const essentialState = {
  sessionId: state.sessionId,
  threadId: state.threadId,
  genieConversationIds: state.genieConversationIds,
  // DON'T store full message history
};
sessionStorage.setItem('agent_memory', JSON.stringify(essentialState));
```

---

## AI Playground Limitations

### ⚠️ Memory Not Fully Supported in AI Playground

**Issue**: AI Playground **does not persist `custom_inputs` between turns**.

**Impact**:
- ❌ `thread_id` is lost between messages → No short-term memory
- ❌ `genie_conversation_ids` are lost → No Genie follow-ups
- ✅ `user_id` works for long-term memory (if manually entered each time)

**Workaround for Testing**:
- Test memory in your custom frontend
- Or manually include `custom_inputs` in each AI Playground query

**Example (AI Playground Manual Input)**:
```json
{
  "input": [{"role": "user", "content": "Show details for the first one"}],
  "custom_inputs": {
    "user_id": "user@example.com",
    "thread_id": "thread_abc123",
    "genie_conversation_ids": {"cost": "conv_def456"}
  }
}
```

---

## Complete Integration Example

### App.tsx with Memory Provider

```typescript
import { MemoryProvider } from './contexts/MemoryContext';
import { ChatInterface } from './components/ChatInterface';

export function App() {
  const { user } = useAuth();
  
  return (
    <MemoryProvider userId={user.email}>
      <div className="app-container">
        <Header />
        <ChatInterface />
        <Footer />
      </div>
    </MemoryProvider>
  );
}
```

### ChatInterface with Full Memory Support

```typescript
export function ChatInterface() {
  const { state: memory, updateFromResponse, startNewConversation } = useMemory();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  const sendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userText = inputValue;
    setInputValue('');
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userText,
      timestamp: new Date()
    }]);
    
    try {
      // Build request with FULL memory context
      const request = {
        input: [{ role: "user", content: userText }],
        custom_inputs: {
          user_id: memory.userId,           // Long-term memory
          session_id: memory.sessionId,     // Session tracking
          thread_id: memory.threadId,       // Short-term memory
          genie_conversation_ids: memory.genieConversationIds,  // Genie follow-ups
          request_id: crypto.randomUUID()   // Request tracking
        }
      };
      
      // Stream response
      let responseContent = '';
      const customOutputs = await streamAgentResponse(
        request,
        (chunk) => {
          responseContent += chunk;
          // Update UI with streaming content
          setMessages(prev => {
            const updated = [...prev];
            if (updated[updated.length - 1]?.role === 'assistant') {
              updated[updated.length - 1].content = responseContent;
            } else {
              updated.push({
                role: 'assistant',
                content: responseContent,
                timestamp: new Date()
              });
            }
            return updated;
          });
        }
      );
      
      // Update memory state from response
      updateFromResponse(customOutputs);
      
      // Attach custom_outputs to final message
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1].customOutputs = customOutputs;
        return updated;
      });
      
    } catch (error) {
      console.error('Message error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date()
      }]);
    }
  };
  
  return (
    <div className="chat-interface h-screen flex flex-col">
      {/* Header with memory status */}
      <div className="chat-header bg-db-navy text-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Databricks Health Monitor</h1>
            <MemoryStatusBadge
              threadId={memory.threadId}
              messageCount={messages.filter(m => m.role === 'assistant').length}
            />
          </div>
          
          {memory.threadId && (
            <button
              onClick={startNewConversation}
              className="px-3 py-1 bg-white text-db-navy rounded text-sm"
            >
              🔄 New Chat
            </button>
          )}
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
      </div>
      
      {/* Input */}
      <div className="border-t p-4">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about costs, security, performance..."
          className="w-full px-4 py-2 border rounded"
        />
      </div>
    </div>
  );
}
```

---

## Checklist: Memory Integration

### Implementation
- [ ] `user_id` included in ALL requests
- [ ] `session_id` generated on app load, persisted in sessionStorage
- [ ] `thread_id` extracted from responses, included in follow-ups
- [ ] `genie_conversation_ids` tracked per domain, passed in requests
- [ ] Memory state updated after every response
- [ ] "New Conversation" button clears `thread_id` and `genie_conversation_ids`

### UI/UX
- [ ] Memory status indicator visible
- [ ] User can clear conversation context
- [ ] User can view stored insights (optional)
- [ ] User can delete insights (GDPR compliance)
- [ ] Session expiry handled gracefully
- [ ] First-conversation warnings suppressed

### Error Handling
- [ ] Memory errors don't block queries
- [ ] Initialization warnings handled
- [ ] Session timeout displays user-friendly message
- [ ] Memory failures logged for debugging

### Performance
- [ ] Only essential state in sessionStorage (not full messages)
- [ ] Session age checked periodically (not on every render)
- [ ] Memory updates debounced (if updating frequently)

---

## References

### Related Documentation
- [15 - Frontend Integration Guide](15-frontend-integration-guide.md) - Complete integration overview
- [16 - Frontend Streaming Guide](16-frontend-streaming-guide.md) - Streaming implementation
- [07 - Memory Management](07-memory-management.md) - Backend memory architecture
- [OBO Authentication Guide](obo-authentication-guide.md) - Authentication patterns

### Official Documentation
- [Lakebase Memory](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/stateful-agents)
- [Short-Term Memory](https://docs.databricks.com/aws/en/notebooks/source/generative-ai/short-term-memory-agent-lakebase.html)
- [Long-Term Memory](https://docs.databricks.com/aws/en/notebooks/source/generative-ai/long-term-memory-agent-lakebase.html)

---

## Quick Reference

### Essential State

```typescript
{
  userId: "user@example.com",         // For long-term memory
  sessionId: "uuid",                  // For session tracking
  threadId: "thread_uuid" | null,     // For short-term memory
  genieConversationIds: {             // For Genie follow-ups
    "cost": "conv_uuid",
    "security": "conv_uuid"
  }
}
```

### Request Format

```typescript
{
  input: [{ role: "user", content: "..." }],
  custom_inputs: {
    user_id: state.userId,
    session_id: state.sessionId,
    thread_id: state.threadId,
    genie_conversation_ids: state.genieConversationIds
  }
}
```

### Update Pattern

```typescript
const response = await sendRequest();
setThreadId(response.custom_outputs.thread_id);
setGenieConvIds(response.custom_outputs.genie_conversation_ids);
```

---

**Last Updated**: January 9, 2026  
**Version**: 1.0  
**Status**: Ready for Frontend Implementation

