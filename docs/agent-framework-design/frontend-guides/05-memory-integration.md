# Frontend Guide 05: Memory Integration

> **Purpose**: Implement conversation context and user personalization
> 
> **Audience**: Frontend developers adding stateful chat
> 
> **Time to Implement**: 2-3 hours

---

## Memory System Overview

The agent has **two types of memory**, both fully managed by the backend:

### 1. Short-Term Memory (Conversation Context)

| Aspect | Details |
|---|---|
| **Purpose** | Remember conversation within a session |
| **Duration** | 24 hours |
| **Storage** | Lakebase `checkpoints` table |
| **Key** | `thread_id` |
| **Example** | "Show me details for the first one" (references previous query) |

### 2. Long-Term Memory (User Preferences)

| Aspect | Details |
|---|---|
| **Purpose** | Learn user patterns across sessions |
| **Duration** | 365 days |
| **Storage** | Lakebase `store` table with semantic search |
| **Key** | `user_id` |
| **Example** | User often asks about serverless → Agent prioritizes serverless data |

### Frontend Responsibility

**You only need to**:
- ✅ Provide `user_id` in all requests (for long-term memory)
- ✅ Track and include `thread_id` from responses (for short-term memory)
- ✅ Track and include `genie_conversation_ids` (for Genie follow-ups)

**Backend handles everything else** (storing, retrieving, analyzing).

---

## Short-Term Memory Implementation

### Step 1: Initialize Session State

```typescript
interface MemoryState {
  // Identity
  userId: string;          // User's email
  sessionId: string;       // Browser session (you generate)
  
  // Short-term memory
  threadId: string | null; // From agent response
  
  // Genie conversations
  genieConversationIds: Record<string, string>;  // Per-domain
}

function useMemoryState(userId: string) {
  const [state, setState] = useState<MemoryState>(() => {
    // Try to restore from sessionStorage
    const saved = sessionStorage.getItem('agent_memory');
    if (saved) {
      const parsed = JSON.parse(saved);
      
      // Validate session age (< 24 hours)
      const age = Date.now() - new Date(parsed.lastUpdated).getTime();
      if (age < 24 * 60 * 60 * 1000) {
        return { ...parsed, userId };  // Restore with current userId
      }
    }
    
    // New session
    return {
      userId,
      sessionId: crypto.randomUUID(),
      threadId: null,
      genieConversationIds: {}
    };
  });
  
  // Persist to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('agent_memory', JSON.stringify({
      ...state,
      lastUpdated: new Date()
    }));
  }, [state]);
  
  return [state, setState] as const;
}
```

### Step 2: Include in Requests

```typescript
async function sendMessage(query: string) {
  const request = {
    input: [{ role: 'user', content: query }],
    custom_inputs: {
      user_id: memoryState.userId,          // ✅ For long-term memory
      session_id: memoryState.sessionId,    // ✅ For tracking
      thread_id: memoryState.threadId,      // ✅ For short-term memory
      genie_conversation_ids: memoryState.genieConversationIds,  // ✅ For Genie follow-ups
      request_id: crypto.randomUUID()
    }
  };
  
  return await sendAgentQuery(request, userToken);
}
```

### Step 3: Update from Response

```typescript
async function sendAndUpdateMemory(query: string) {
  const response = await sendMessage(query);
  
  // Extract memory state from response
  const { thread_id, genie_conversation_ids } = response.custom_outputs;
  
  // Update state for next query
  setMemoryState(prev => ({
    ...prev,
    threadId: thread_id,                    // ✅ Store for next query
    genieConversationIds: genie_conversation_ids || {}  // ✅ Store for Genie follow-ups
  }));
  
  return response;
}
```

---

## Memory Lifecycle Example

```
┌────────────────────────────────────────────────────────────────┐
│                    CONVERSATION LIFECYCLE                       │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User opens app                                               │
│     Frontend: sessionId = new UUID(), threadId = null           │
│                                                                  │
│  2. First query: "What are top 5 expensive jobs?"               │
│     Request: { thread_id: null }                                │
│     Response: { thread_id: "thread_abc123" }                    │
│     Frontend stores: thread_abc123                              │
│                                                                  │
│  3. Follow-up: "Show me details for the first one"              │
│     Request: { thread_id: "thread_abc123" }                     │
│     Backend loads previous query from memory                    │
│     Agent understands "the first one" = "ETL Pipeline"          │
│     Response: { thread_id: "thread_abc123" }                    │
│                                                                  │
│  4. User clicks "New Conversation"                              │
│     Frontend: threadId = null, genieConversationIds = {}        │
│     Next query starts fresh (no context)                        │
│                                                                  │
│  5. User closes tab                                              │
│     sessionStorage cleared automatically                        │
│     Next visit: new sessionId, threadId = null                  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Genie Conversation Continuity

### Why Per-Domain Tracking?

Each Genie Space maintains its own conversation:

```
User: "What are top 5 expensive jobs?"
Agent: [domain=cost, conversation_id="conv_cost_123"]

User: "Show me security events"
Agent: [domain=security, conversation_id="conv_security_456"]

User: "Break down those costs by workspace"
Agent: [domain=cost, uses "conv_cost_123" for context]
      [Understands "those costs" refers to original cost query]
```

### Implementation

```typescript
// Track conversations per domain
const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({
  // Format: { "cost": "conv_abc123", "security": "conv_def456" }
});

// Include in every request
const request = {
  input: [{ role: 'user', content: query }],
  custom_inputs: {
    genie_conversation_ids: genieConvIds  // ✅ All domain conversations
  }
};

// Update from every response
const response = await sendAgentQuery(request);
setGenieConvIds(response.custom_outputs.genie_conversation_ids);
```

---

## Long-Term Memory (User Preferences)

### How It Works

**Backend automatically**:
1. Extracts insights from each conversation ("user often asks about cost")
2. Stores with semantic embeddings in Lakebase
3. Retrieves relevant insights on new queries
4. Personalizes responses based on past interactions

**Frontend only needs to**:
- ✅ Include `user_id` in every request
- ✅ That's it!

### Example

```
Day 1:
User: "Show me serverless costs"
Agent: [Saves: "User interested in serverless compute costs"]

Day 7:
User: "What are my biggest expenses?"
Agent: [Retrieves: "User interested in serverless compute costs"]
      [Response prioritizes serverless breakdown]
```

---

## React Context for Memory

### Create Memory Provider

```typescript
// contexts/MemoryContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface MemoryContextType {
  state: MemoryState;
  updateFromResponse: (customOutputs: CustomOutputs) => void;
  startNewConversation: () => void;
}

const MemoryContext = createContext<MemoryContextType | null>(null);

export function MemoryProvider({ 
  children, 
  userId 
}: { 
  children: ReactNode; 
  userId: string;
}) {
  const [state, setState] = useState<MemoryState>(() => {
    // Restore from sessionStorage
    const saved = sessionStorage.getItem('agent_memory');
    if (saved) {
      const parsed = JSON.parse(saved);
      const age = Date.now() - new Date(parsed.lastUpdated).getTime();
      
      // Keep if < 24 hours old
      if (age < 24 * 60 * 60 * 1000) {
        return { ...parsed, userId };
      }
    }
    
    // New state
    return {
      userId,
      sessionId: crypto.randomUUID(),
      threadId: null,
      genieConversationIds: {}
    };
  });
  
  // Persist to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('agent_memory', JSON.stringify({
      ...state,
      lastUpdated: new Date()
    }));
  }, [state]);
  
  const updateFromResponse = useCallback((customOutputs: CustomOutputs) => {
    setState(prev => ({
      ...prev,
      threadId: customOutputs.thread_id,
      genieConversationIds: customOutputs.genie_conversation_ids || prev.genieConversationIds
    }));
  }, []);
  
  const startNewConversation = useCallback(() => {
    setState(prev => ({
      ...prev,
      threadId: null,
      genieConversationIds: {},
      sessionId: crypto.randomUUID()
    }));
  }, []);
  
  return (
    <MemoryContext.Provider value={{ state, updateFromResponse, startNewConversation }}>
      {children}
    </MemoryContext.Provider>
  );
}

export function useMemory() {
  const context = useContext(MemoryContext);
  if (!context) throw new Error('useMemory must be used within MemoryProvider');
  return context;
}
```

### Usage in Chat

```typescript
export function ChatInterface() {
  const { state: memory, updateFromResponse } = useMemory();
  
  const sendMessage = async (query: string) => {
    // Build request with full memory context
    const request = {
      input: [{ role: 'user', content: query }],
      custom_inputs: {
        user_id: memory.userId,
        session_id: memory.sessionId,
        thread_id: memory.threadId,
        genie_conversation_ids: memory.genieConversationIds
      }
    };
    
    const response = await sendAgentQuery(request);
    
    // Update memory from response
    updateFromResponse(response.custom_outputs);
    
    return response;
  };
  
  return <ChatUI onSend={sendMessage} />;
}
```

---

## Memory Status UI

### Status Indicator

```typescript
export function MemoryStatusBadge({ threadId, messageCount }: Props) {
  if (!threadId) {
    return (
      <span className="text-xs text-gray-500">
        💭 New conversation (no context)
      </span>
    );
  }
  
  return (
    <span className="text-xs text-green-600 flex items-center gap-1">
      ✓ Context active ({messageCount} messages remembered)
    </span>
  );
}
```

### Domain Context Indicator

```typescript
export function DomainContextBadges({ 
  genieConvIds 
}: { 
  genieConvIds: Record<string, string> 
}) {
  const activeDomains = Object.keys(genieConvIds);
  
  if (activeDomains.length === 0) return null;
  
  const domainColors = {
    cost: 'bg-red-50 text-red-700',
    security: 'bg-orange-50 text-orange-700',
    performance: 'bg-blue-50 text-blue-700',
    reliability: 'bg-green-50 text-green-700',
    quality: 'bg-purple-50 text-purple-700'
  };
  
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-gray-600">🔗 Active:</span>
      {activeDomains.map(domain => (
        <span
          key={domain}
          className={`px-2 py-1 rounded ${domainColors[domain] || 'bg-gray-50 text-gray-700'}`}
        >
          {domain}
        </span>
      ))}
    </div>
  );
}
```

---

## Testing Memory

### Test Scenarios

#### Scenario 1: Context Preservation

```typescript
test('should remember previous query', async () => {
  // First query
  const r1 = await sendQuery("Show top 5 jobs");
  const threadId = r1.custom_outputs.thread_id;
  expect(threadId).toBeTruthy();
  
  // Follow-up query with thread_id
  const r2 = await sendQuery("Show details for the first one", { threadId });
  
  // Agent should understand "the first one"
  expect(r2.custom_outputs.source).toBe('genie');
  expect(r2.output[0].content[0].text).toContain('ETL Pipeline');
});
```

#### Scenario 2: Domain Switching

```typescript
test('should track separate Genie conversations', async () => {
  // Cost query
  const r1 = await sendQuery("Show cost trends");
  const costConvId = r1.custom_outputs.genie_conversation_ids.cost;
  
  // Security query (different domain)
  const r2 = await sendQuery("Show security events", {
    genieConversationIds: r1.custom_outputs.genie_conversation_ids
  });
  const securityConvId = r2.custom_outputs.genie_conversation_ids.security;
  
  // Both conversations preserved
  expect(r2.custom_outputs.genie_conversation_ids.cost).toBe(costConvId);
  expect(r2.custom_outputs.genie_conversation_ids.security).toBe(securityConvId);
});
```

---

## When to Clear Memory

### Clear Short-Term Memory

```typescript
function clearConversationContext() {
  setThreadId(null);
  setGenieConvIds({});
  setMessages([]);  // Optional: clear visible messages
}
```

**Trigger when**:
- User clicks "New Conversation" button
- User explicitly requests context reset
- Session expires (24+ hours old)

### Never Clear Long-Term Memory

```typescript
// DON'T clear user_id or delete long-term insights
// Long-term memory should persist across sessions
// Only clear if user explicitly requests (GDPR compliance)
```

---

## Session Expiry Handling

### Auto-Detect Expired Sessions

```typescript
useEffect(() => {
  if (!threadId) return;
  
  const checkSessionAge = () => {
    const sessionAge = Date.now() - sessionStartTime.getTime();
    const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;
    
    if (sessionAge > TWENTY_FOUR_HOURS) {
      // Session expired
      clearConversationContext();
      showToast('Session expired. Starting new conversation.');
    }
  };
  
  // Check every 5 minutes
  const interval = setInterval(checkSessionAge, 5 * 60 * 1000);
  return () => clearInterval(interval);
}, [threadId]);
```

---

## Memory Debugging (Development)

### Debug Panel

```typescript
export function MemoryDebugPanel({ state }: { state: MemoryState }) {
  if (process.env.NODE_ENV !== 'development') return null;
  
  return (
    <details className="debug-panel p-4 bg-gray-900 text-gray-100 rounded text-xs font-mono">
      <summary className="cursor-pointer font-semibold text-green-400">
        🔍 Memory Debug Info
      </summary>
      
      <div className="mt-3 space-y-2">
        <div>
          <span className="text-blue-400">User ID:</span> {state.userId}
        </div>
        <div>
          <span className="text-blue-400">Session ID:</span> {state.sessionId}
        </div>
        <div>
          <span className="text-blue-400">Thread ID:</span> {state.threadId || '(none - new conversation)'}
        </div>
        <div>
          <span className="text-blue-400">Genie Conversations:</span>
          <pre className="mt-1 text-gray-300 overflow-x-auto">
            {JSON.stringify(state.genieConversationIds, null, 2)}
          </pre>
        </div>
        
        <button
          onClick={() => console.log('Memory state:', state)}
          className="mt-2 px-3 py-1 bg-blue-600 rounded text-white"
        >
          Log to Console
        </button>
      </div>
    </details>
  );
}
```

---

## First Conversation Warning

### Handling Initialization

On the **very first conversation**, backend may show:
```
⚠ Short-term memory retrieval failed: relation "checkpoints" does not exist
⚠ Long-term memory retrieval failed: relation "store" does not exist
```

**This is NORMAL**. The agent automatically creates these tables.

### Frontend Handling

```typescript
function getMemoryStatus(customOutputs: CustomOutputs): 'initializing' | 'active' | 'error' {
  const { memory_status, error } = customOutputs;
  
  // First-time initialization
  if (memory_status === 'error' && error?.includes('does not exist')) {
    return 'initializing';
  }
  
  // Active memory
  if (memory_status === 'saved') {
    return 'active';
  }
  
  return 'error';
}

// Display
{memoryStatus === 'initializing' && (
  <div className="text-xs text-blue-600">
    ⏳ Initializing memory (first conversation)...
  </div>
)}

{memoryStatus === 'active' && (
  <div className="text-xs text-green-600">
    ✓ Memory active
  </div>
)}
```

---

## User Insights Dashboard (Optional)

### Show What Agent Has Learned

```typescript
export function UserInsightsDashboard({ userId }: { userId: string }) {
  const [insights, setInsights] = useState<Insight[]>([]);
  
  useEffect(() => {
    // Query via your backend
    fetch(`/api/agent/insights?user_id=${userId}`)
      .then(r => r.json())
      .then(setInsights);
  }, [userId]);
  
  return (
    <div className="insights-dashboard p-6">
      <h2 className="text-xl font-semibold mb-4">
        🧠 What Your Agent Has Learned
      </h2>
      
      <div className="space-y-3">
        {insights.map(insight => (
          <div key={insight.id} className="insight-card border rounded p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <span className="text-xs font-semibold text-gray-600 uppercase">
                  {insight.category}
                </span>
                <p className="text-sm mt-1">{insight.content}</p>
                <p className="text-xs text-gray-400 mt-2">
                  {new Date(insight.timestamp).toLocaleDateString()}
                </p>
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
      
      {insights.length === 0 && (
        <p className="text-gray-500 text-center py-8">
          No insights yet. Keep chatting and the agent will learn your preferences!
        </p>
      )}
      
      <button
        onClick={() => clearAllInsights(userId)}
        className="mt-4 w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
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
```

---

## Privacy Controls (GDPR Compliance)

### Export and Delete User Data

```typescript
export function PrivacyControls({ userId }: { userId: string }) {
  const exportData = async () => {
    // Call your backend to fetch all user insights
    const response = await fetch(`/api/agent/insights?user_id=${userId}`);
    const insights = await response.json();
    
    // Download as JSON
    const blob = new Blob([JSON.stringify(insights, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-insights-${userId}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  const deleteAllData = async () => {
    if (!confirm('Delete all agent insights? This cannot be undone.')) return;
    
    await fetch(`/api/agent/insights?user_id=${userId}`, {
      method: 'DELETE'
    });
    
    alert('All insights deleted successfully');
  };
  
  return (
    <div className="privacy-controls border rounded p-4">
      <h3 className="font-semibold mb-3">🔒 Privacy & Data</h3>
      
      <p className="text-sm text-gray-600 mb-4">
        The agent stores insights from your conversations to improve future responses.
        You can export or delete this data at any time.
      </p>
      
      <div className="flex gap-3">
        <button
          onClick={exportData}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          📥 Export My Data
        </button>
        
        <button
          onClick={deleteAllData}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          🗑️ Delete All Insights
        </button>
      </div>
    </div>
  );
}
```

---

## Complete Integration Example

### App.tsx

```typescript
import { MemoryProvider } from './contexts/MemoryContext';
import { ChatInterface } from './components/ChatInterface';
import { useAuth } from './contexts/AuthContext';

export function App() {
  const { user } = useAuth();
  
  return (
    <MemoryProvider userId={user.email}>
      <div className="app-container">
        <Header />
        <ChatInterface />
      </div>
    </MemoryProvider>
  );
}
```

### ChatInterface.tsx

```typescript
import { useMemory } from '../contexts/MemoryContext';

export function ChatInterface() {
  const { state: memory, updateFromResponse, startNewConversation } = useMemory();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  const sendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userText = inputValue;
    setInputValue('');
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    
    try {
      // Send with FULL memory context
      const response = await sendAgentQuery({
        input: [{ role: 'user', content: userText }],
        custom_inputs: {
          user_id: memory.userId,           // Long-term memory
          session_id: memory.sessionId,     // Session tracking
          thread_id: memory.threadId,       // Short-term memory
          genie_conversation_ids: memory.genieConversationIds  // Genie context
        }
      });
      
      // Add assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.output[0].content[0].text,
        customOutputs: response.custom_outputs
      }]);
      
      // Update memory state
      updateFromResponse(response.custom_outputs);
      
    } catch (error) {
      console.error('Query error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`
      }]);
    }
  };
  
  return (
    <div className="chat-interface">
      {/* Header with memory status */}
      <div className="header bg-gray-900 text-white p-4">
        <h1 className="text-xl font-semibold">Databricks Health Monitor</h1>
        <div className="flex items-center justify-between mt-2">
          <MemoryStatusBadge 
            threadId={memory.threadId}
            messageCount={messages.length}
          />
          {memory.threadId && (
            <button
              onClick={startNewConversation}
              className="text-sm bg-white text-gray-900 px-3 py-1 rounded"
            >
              🔄 New Chat
            </button>
          )}
        </div>
        <DomainContextBadges genieConvIds={memory.genieConversationIds} />
      </div>
      
      {/* Messages */}
      <div className="messages flex-1 overflow-y-auto p-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
      </div>
      
      {/* Input */}
      <div className="input border-t p-4">
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

## Best Practices

### 1. Always Include All IDs

```typescript
// ✅ GOOD: Complete memory context
const request = {
  custom_inputs: {
    user_id: userId,                    // Long-term memory
    session_id: sessionId,              // Session tracking
    thread_id: threadId,                // Short-term memory
    genie_conversation_ids: genieConvIds  // Genie follow-ups
  }
};

// ❌ BAD: Missing IDs
const request = {
  input: [{ role: 'user', content: '...' }]
  // No custom_inputs!
};
```

### 2. Update After Every Response

```typescript
// ✅ GOOD: Always update
const response = await sendAgentQuery(request);
setThreadId(response.custom_outputs.thread_id);
setGenieConvIds(response.custom_outputs.genie_conversation_ids);

// ❌ BAD: Ignore custom_outputs
const response = await sendAgentQuery(request);
// No update!
```

### 3. Persist Across Page Reloads

```typescript
// Save to sessionStorage (secure, cleared on tab close)
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
// Let users know context is active
{threadId && (
  <div className="text-sm text-green-600">
    ✓ Conversation context active
    <button onClick={clearContext} className="ml-2 text-blue-600 underline">
      Clear
    </button>
  </div>
)}
```

---

## Checklist: Memory Integration

### Implementation
- [ ] `user_id` included in ALL requests
- [ ] `session_id` generated on app load
- [ ] `thread_id` extracted from responses
- [ ] `thread_id` included in follow-up queries
- [ ] `genie_conversation_ids` tracked per domain
- [ ] Memory state updated after every response
- [ ] Memory persisted in sessionStorage

### UI/UX
- [ ] Memory status indicator visible
- [ ] "New Conversation" button clears context
- [ ] User can view stored insights (optional)
- [ ] User can delete insights (GDPR)
- [ ] Session expiry handled gracefully

### Error Handling
- [ ] Memory errors don't block queries
- [ ] First-conversation warnings suppressed
- [ ] Session timeout shows user-friendly message

---

## Quick Reference

### Essential Memory Fields

```typescript
// Request
{
  custom_inputs: {
    user_id: "email",              // For personalization
    thread_id: "thread_id",        // From previous response
    genie_conversation_ids: {...}  // From previous response
  }
}

// Response (Store these!)
{
  custom_outputs: {
    thread_id: "...",               // Store for next request
    genie_conversation_ids: {...}   // Store for next request
  }
}
```

### Memory Lifecycle

```
1. First query: thread_id=null → Get thread_abc123
2. Follow-up: thread_id=thread_abc123 → Get thread_abc123
3. New conversation: thread_id=null → Get thread_def456 (new)
```

---

**Next Guide**: [06 - Visualization Rendering](06-visualization-rendering.md) (Render charts based on hints)

**Previous Guide**: [04 - Streaming Responses](04-streaming-responses.md)
