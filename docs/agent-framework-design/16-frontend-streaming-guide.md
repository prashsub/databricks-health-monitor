# 16 - Frontend Streaming Responses Guide

> **📋 Implementation Status**: GUIDE FOR FRONTEND DEVELOPERS
> 
> **Purpose**: Detailed guide for implementing streaming agent responses with proper fallback handling.
> 
> **Audience**: Frontend developers implementing real-time chat interfaces

---

## Overview

The Health Monitor Agent supports **streaming responses** using Server-Sent Events (SSE). Streaming provides:
- ✅ Immediate visual feedback ("Querying Cost Genie Space...")
- ✅ Real-time display of analysis as it generates
- ✅ Reduced perceived latency (user sees progress immediately)
- ✅ Cancellable requests (user can stop long-running queries)

This guide covers implementation with fallback strategies for non-streaming environments.

---

## Streaming vs Non-Streaming

### Streaming Response

**Request**: Add `?stream=true` query parameter

```typescript
fetch(`${ENDPOINT_URL}?stream=true`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify(request)
})
```

**Response**: Server-Sent Events (SSE) stream

```
data: {"type": "response.output_item.delta", "delta": {"type": "output_text", "text": "The"}}
data: {"type": "response.output_item.delta", "delta": {"type": "output_text", "text": " top"}}
data: {"type": "response.output_item.delta", "delta": {"type": "output_text", "text": " 5"}}
...
data: {"type": "response.output_item.done", "item": {...}}
data: {"type": "response.done", "custom_outputs": {...}}
```

### Non-Streaming Response

**Request**: No query parameter (or `?stream=false`)

```typescript
fetch(ENDPOINT_URL, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify(request)
})
```

**Response**: Single JSON response

```json
{
  "id": "resp_123",
  "output": [{
    "type": "message",
    "content": [{"type": "output_text", "text": "Complete response..."}]
  }],
  "custom_outputs": {...}
}
```

---

## Implementation: Streaming Client

### TypeScript Streaming Function

```typescript
/**
 * Stream agent responses with Server-Sent Events (SSE).
 * 
 * Yields text chunks as they arrive, then returns final custom_outputs.
 * 
 * @param request - Agent request with input and custom_inputs
 * @param onChunk - Callback for each text chunk
 * @returns Final custom_outputs with visualization hints, memory state
 */
export async function streamAgentResponse(
  request: AgentRequest,
  onChunk: (text: string) => void
): Promise<any> {
  const response = await fetch(
    `${ENDPOINT_URL}?stream=true`,  // ⚠️ CRITICAL: stream=true
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getUserToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  if (!response.body) {
    throw new Error('Response body is null');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  let buffer = '';
  let finalCustomOutputs = null;
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });
      
      // Split by newlines (SSE format: "data: {...}\n")
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';  // Keep incomplete line in buffer
      
      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue;
        
        const jsonStr = line.slice(6);  // Remove "data: " prefix
        
        try {
          const event = JSON.parse(jsonStr);
          
          // ================================================================
          // TEXT DELTA: Real-time text chunks
          // ================================================================
          if (event.type === 'response.output_item.delta') {
            if (event.delta?.type === 'output_text' && event.delta.text) {
              onChunk(event.delta.text);
            }
          }
          
          // ================================================================
          // OUTPUT ITEM DONE: Complete output item (usually ignored)
          // ================================================================
          else if (event.type === 'response.output_item.done') {
            // This contains the full accumulated text
            // Usually not needed since we've been receiving deltas
          }
          
          // ================================================================
          // RESPONSE DONE: Final event with custom_outputs
          // ================================================================
          else if (event.type === 'response.done') {
            // Store custom_outputs for next request
            finalCustomOutputs = event.custom_outputs || {};
          }
          
        } catch (parseError) {
          console.error('Failed to parse SSE event:', parseError);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
  
  return finalCustomOutputs || {};
}
```

### React Hook with Streaming

```typescript
import { useState, useCallback, useRef } from 'react';

interface UseStreamingOptions {
  onError?: (error: Error) => void;
  onComplete?: (customOutputs: any) => void;
}

export function useStreamingAgent(options: UseStreamingOptions = {}) {
  const [content, setContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [customOutputs, setCustomOutputs] = useState<any>(null);
  const [error, setError] = useState<Error | null>(null);
  
  // Track if component is mounted
  const isMountedRef = useRef(true);
  useEffect(() => {
    return () => { isMountedRef.current = false; };
  }, []);
  
  const sendMessage = useCallback(async (request: AgentRequest) => {
    if (!isMountedRef.current) return;
    
    setContent('');
    setIsStreaming(true);
    setError(null);
    setCustomOutputs(null);
    
    try {
      const outputs = await streamAgentResponse(
        request,
        (chunk) => {
          // Only update if component still mounted
          if (isMountedRef.current) {
            setContent(prev => prev + chunk);
          }
        }
      );
      
      if (isMountedRef.current) {
        setCustomOutputs(outputs);
        options.onComplete?.(outputs);
      }
      
    } catch (err) {
      if (isMountedRef.current) {
        setError(err as Error);
        options.onError?.(err as Error);
      }
    } finally {
      if (isMountedRef.current) {
        setIsStreaming(false);
      }
    }
  }, [options]);
  
  const reset = useCallback(() => {
    setContent('');
    setCustomOutputs(null);
    setError(null);
    setIsStreaming(false);
  }, []);
  
  return {
    content,
    isStreaming,
    customOutputs,
    error,
    sendMessage,
    reset
  };
}
```

### Usage in Component

```typescript
export function ChatInterface() {
  const { content, isStreaming, customOutputs, error, sendMessage } = 
    useStreamingAgent({
      onComplete: (outputs) => {
        console.log('Stream complete:', outputs);
        // Update conversation state
        updateMemoryState(outputs);
      },
      onError: (err) => {
        console.error('Stream error:', err);
        showErrorToast(err.message);
      }
    });
  
  const handleSend = async (text: string) => {
    await sendMessage({
      input: [{ role: "user", content: text }],
      custom_inputs: {
        user_id: userEmail,
        session_id: sessionId,
        thread_id: threadId,
        genie_conversation_ids: genieConvIds
      }
    });
  };
  
  return (
    <div>
      {/* Display streaming content */}
      {content && (
        <div className="agent-message">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )}
      
      {/* Show visualization when stream completes */}
      {customOutputs?.data && customOutputs?.visualization_hint && (
        <AgentVisualization
          hint={customOutputs.visualization_hint}
          data={customOutputs.data}
          domain={customOutputs.domain}
        />
      )}
      
      {/* Error display */}
      {error && <ErrorBanner error={error} />}
      
      {/* Loading indicator */}
      {isStreaming && <StreamingIndicator />}
    </div>
  );
}
```

---

## Fallback Strategies

### Strategy 1: Automatic Fallback

**Try streaming first, fall back to non-streaming on error**:

```typescript
async function sendAgentRequest(
  request: AgentRequest,
  onChunk?: (text: string) => void
): Promise<{ content: string; customOutputs: any }> {
  // Try streaming first
  if (onChunk) {
    try {
      let content = '';
      const customOutputs = await streamAgentResponse(request, (chunk) => {
        content += chunk;
        onChunk(chunk);
      });
      return { content, customOutputs };
      
    } catch (streamError) {
      console.warn('Streaming failed, falling back to non-streaming:', streamError);
      // Fall through to non-streaming
    }
  }
  
  // Non-streaming fallback
  const response = await fetch(ENDPOINT_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getUserToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  const data = await response.json();
  const content = data.output[0]?.content[0]?.text || '';
  const customOutputs = data.custom_outputs || {};
  
  return { content, customOutputs };
}
```

### Strategy 2: User Preference

**Let users choose streaming vs instant responses**:

```typescript
interface UserPreferences {
  streamingEnabled: boolean;
  autoRetryOnError: boolean;
  showVisualizationHints: boolean;
}

const [preferences, setPreferences] = useState<UserPreferences>({
  streamingEnabled: true,   // Default to streaming
  autoRetryOnError: true,
  showVisualizationHints: true
});

async function sendMessage(text: string) {
  if (preferences.streamingEnabled) {
    return await sendStreamingRequest(text);
  } else {
    return await sendNonStreamingRequest(text);
  }
}
```

### Strategy 3: Network Detection

**Disable streaming on slow/unreliable networks**:

```typescript
function isNetworkSuitable(): boolean {
  if ('connection' in navigator) {
    const conn = (navigator as any).connection;
    
    // Disable streaming on slow connections
    if (conn.effectiveType === 'slow-2g' || conn.effectiveType === '2g') {
      return false;
    }
    
    // Disable streaming if data saver is on
    if (conn.saveData) {
      return false;
    }
  }
  
  return true;  // Default: streaming enabled
}

const shouldStream = isNetworkSuitable() && preferences.streamingEnabled;
```

### Strategy 4: Feature Detection

**Check if browser supports ReadableStream**:

```typescript
function supportsStreaming(): boolean {
  return typeof ReadableStream !== 'undefined' && 
         typeof TextDecoder !== 'undefined';
}

if (supportsStreaming()) {
  // Use streaming
} else {
  // Use non-streaming fallback
}
```

---

## Cancelling Streaming Requests

### AbortController Pattern

```typescript
export function useStreamingAgent() {
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const sendMessage = useCallback(async (request: AgentRequest) => {
    // Cancel previous request if still running
    abortControllerRef.current?.abort();
    
    // Create new abort controller
    abortControllerRef.current = new AbortController();
    
    try {
      const response = await fetch(
        `${ENDPOINT_URL}?stream=true`,
        {
          method: 'POST',
          headers: { /* ... */ },
          body: JSON.stringify(request),
          signal: abortControllerRef.current.signal  // ✅ Pass abort signal
        }
      );
      
      // ... streaming logic
      
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request cancelled by user');
        return;  // Don't treat as error
      }
      throw error;
    }
  }, []);
  
  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);
  
  return { sendMessage, cancel, /* ... */ };
}
```

### UI for Cancellation

```typescript
export function ChatInterface() {
  const { sendMessage, cancel, isStreaming } = useStreamingAgent();
  
  return (
    <div>
      {/* Input area */}
      <input
        disabled={isStreaming}
        onKeyPress={(e) => e.key === 'Enter' && !isStreaming && handleSend()}
      />
      
      {/* Cancel button (only visible during streaming) */}
      {isStreaming && (
        <button
          onClick={cancel}
          className="px-4 py-2 bg-red-600 text-white rounded"
        >
          ⏹️ Cancel
        </button>
      )}
      
      {/* Send button */}
      {!isStreaming && (
        <button
          onClick={handleSend}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          📤 Send
        </button>
      )}
    </div>
  );
}
```

---

## Event Types Reference

### 1. `response.output_item.delta`

**When**: During streaming, for each text chunk

**Payload**:
```json
{
  "type": "response.output_item.delta",
  "item_id": "msg_123",
  "delta": {
    "type": "output_text",
    "text": "The top 5 jobs "
  }
}
```

**Frontend Action**: Append `delta.text` to display

---

### 2. `response.output_item.done`

**When**: After all deltas for an output item

**Payload**:
```json
{
  "type": "response.output_item.done",
  "item": {
    "type": "message",
    "id": "msg_123",
    "role": "assistant",
    "content": [{
      "type": "output_text",
      "text": "Complete accumulated text..."
    }]
  }
}
```

**Frontend Action**: Optional - can use for final text if needed, but deltas should have already provided it

---

### 3. `response.done` (MOST IMPORTANT)

**When**: At the very end of the stream

**Payload**:
```json
{
  "type": "response.done",
  "id": "resp_a1b2c3",
  "custom_outputs": {
    "thread_id": "thread_abc123",
    "genie_conversation_ids": { "cost": "conv_def456" },
    "memory_status": "saved",
    "visualization_hint": { "type": "bar_chart", ... },
    "data": [...]
  }
}
```

**Frontend Action**: 
- ✅ Store `custom_outputs` for next request
- ✅ Render visualization if `data` is present
- ✅ Update conversation state with `thread_id` and `genie_conversation_ids`

---

## Streaming UI Patterns

### Pattern 1: Typewriter Effect

```typescript
export function StreamingMessage({ content }: { content: string }) {
  return (
    <div className="streaming-message">
      <ReactMarkdown>{content}</ReactMarkdown>
      {/* Blinking cursor */}
      <span className="animate-pulse ml-1">|</span>
    </div>
  );
}
```

### Pattern 2: Progress Stages

```typescript
export function StreamingIndicator({ content }: { content: string }) {
  // Detect stage from content
  const stage = detectStage(content);
  
  return (
    <div className="flex items-center gap-2 text-sm text-gray-600">
      {stage === 'querying' && (
        <>
          <Spinner />
          <span>🔍 Querying Genie Space...</span>
        </>
      )}
      {stage === 'analyzing' && (
        <>
          <Spinner />
          <span>🧠 Analyzing results...</span>
        </>
      )}
      {stage === 'complete' && (
        <span className="text-green-600">✓ Complete</span>
      )}
    </div>
  );
}

function detectStage(content: string): 'querying' | 'analyzing' | 'complete' {
  if (content.includes('Querying')) return 'querying';
  if (content.includes('Analysis:')) return 'analyzing';
  return 'complete';
}
```

### Pattern 3: Incremental Rendering

```typescript
export function StreamingChat() {
  const [chunks, setChunks] = useState<string[]>([]);
  
  const sendMessage = async (text: string) => {
    setChunks([]);
    
    await streamAgentResponse(request, (chunk) => {
      setChunks(prev => [...prev, chunk]);
    });
  };
  
  return (
    <div className="streaming-container">
      {chunks.map((chunk, idx) => (
        <span key={idx} className="chunk-animation">
          {chunk}
        </span>
      ))}
    </div>
  );
}
```

---

## Error Handling in Streaming

### Connection Errors

```typescript
try {
  await streamAgentResponse(request, onChunk);
} catch (error) {
  if (error.message.includes('Failed to fetch')) {
    // Network error - retry or show offline message
    showErrorToast('Network error. Please check your connection.');
  } else if (error.message.includes('HTTP 401')) {
    // Authentication error - redirect to login
    redirectToLogin();
  } else if (error.message.includes('HTTP 403')) {
    // Permission error - show permission guide
    showPermissionError(error);
  } else if (error.message.includes('HTTP 429')) {
    // Rate limit - retry after delay
    setTimeout(() => retryRequest(), 60000);  // 1 minute
  } else {
    // Unknown error - show generic message
    showErrorToast('An error occurred. Please try again.');
  }
}
```

### Partial Stream Errors

**If stream fails mid-response**:

```typescript
async function streamAgentResponse(request, onChunk) {
  let receivedAnyData = false;
  
  try {
    // ... streaming logic
    
    for (const event of events) {
      receivedAnyData = true;
      // Process event
    }
    
  } catch (error) {
    if (receivedAnyData) {
      // Stream started but failed mid-way
      onChunk('\n\n---\n⚠️ Stream interrupted. Response may be incomplete.');
    }
    throw error;
  }
}
```

### Timeout Handling

```typescript
async function streamWithTimeout(
  request: AgentRequest,
  onChunk: (text: string) => void,
  timeoutMs: number = 120000  // 2 minutes
): Promise<any> {
  return Promise.race([
    streamAgentResponse(request, onChunk),
    
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Request timeout')), timeoutMs)
    )
  ]);
}
```

---

## Streaming Performance

### Buffering Strategy

**Buffer small chunks to reduce render overhead**:

```typescript
async function streamAgentResponse(request, onChunk) {
  let chunkBuffer = '';
  let lastFlush = Date.now();
  const FLUSH_INTERVAL_MS = 50;  // Flush every 50ms
  
  const flushBuffer = () => {
    if (chunkBuffer) {
      onChunk(chunkBuffer);
      chunkBuffer = '';
    }
  };
  
  for await (const event of events) {
    if (event.type === 'response.output_item.delta') {
      chunkBuffer += event.delta.text;
      
      // Flush buffer every 50ms or when buffer gets large
      const now = Date.now();
      if (now - lastFlush > FLUSH_INTERVAL_MS || chunkBuffer.length > 100) {
        flushBuffer();
        lastFlush = now;
      }
    }
  }
  
  // Flush remaining buffer
  flushBuffer();
}
```

### React Performance

**Use React.memo for message components**:

```typescript
export const MessageBubble = React.memo(({ message }: { message: Message }) => {
  return (
    <div className="message-bubble">
      <ReactMarkdown>{message.content}</ReactMarkdown>
    </div>
  );
}, (prev, next) => {
  // Only re-render if content changed
  return prev.message.content === next.message.content;
});
```

---

## Testing Streaming

### Unit Tests

```typescript
describe('streamAgentResponse', () => {
  it('should yield text chunks', async () => {
    const chunks: string[] = [];
    
    await streamAgentResponse(
      mockRequest,
      (chunk) => chunks.push(chunk)
    );
    
    expect(chunks.length).toBeGreaterThan(0);
    expect(chunks.join('')).toContain('Analysis:');
  });
  
  it('should return custom_outputs', async () => {
    let finalOutputs = null;
    
    finalOutputs = await streamAgentResponse(mockRequest, () => {});
    
    expect(finalOutputs).toBeDefined();
    expect(finalOutputs.thread_id).toBeTruthy();
    expect(finalOutputs.visualization_hint).toBeDefined();
  });
  
  it('should handle cancellation', async () => {
    const controller = new AbortController();
    
    setTimeout(() => controller.abort(), 100);
    
    await expect(
      streamAgentResponse(mockRequest, () => {}, controller.signal)
    ).rejects.toThrow('AbortError');
  });
});
```

### Integration Tests

```typescript
describe('Streaming Integration', () => {
  it('should stream real agent response', async () => {
    const chunks: string[] = [];
    
    const outputs = await streamAgentResponse(
      {
        input: [{ role: "user", content: "What are the top 5 expensive jobs?" }],
        custom_inputs: { user_id: "test@example.com" }
      },
      (chunk) => chunks.push(chunk)
    );
    
    // Verify streaming happened
    expect(chunks.length).toBeGreaterThan(5);
    
    // Verify final outputs
    expect(outputs.visualization_hint?.type).toBe('bar_chart');
    expect(outputs.data).toBeDefined();
    expect(outputs.thread_id).toBeTruthy();
  }, 30000);  // 30s timeout for real API call
});
```

---

## Debugging Streaming Issues

### Common Issues

#### Issue 1: No chunks received

**Symptoms**: `isStreaming: true` but no content updates

**Debug**:
```typescript
await streamAgentResponse(request, (chunk) => {
  console.log('[CHUNK]', chunk.length, 'chars');  // Add logging
  onChunk(chunk);
});
```

**Common Causes**:
- Browser buffering SSE events
- CORS blocking streaming
- Reverse proxy buffering responses
- Missing `?stream=true` parameter

---

#### Issue 2: Incomplete responses

**Symptoms**: Stream stops mid-response, no final event

**Debug**:
```typescript
for await (const event of events) {
  console.log('[EVENT]', event.type);  // Log all events
  
  if (event.type === 'response.done') {
    console.log('[FINAL]', event.custom_outputs);
  }
}
```

**Common Causes**:
- Network timeout
- Backend error mid-stream
- Browser tab suspended

---

#### Issue 3: custom_outputs not received

**Symptoms**: Streaming completes but no visualization hints

**Debug**:
```typescript
console.log('[FINAL EVENT]', JSON.stringify(event, null, 2));
```

**Check**:
- Is `event.type === 'response.done'` received?
- Does event have `custom_outputs` field?
- Are you awaiting the full stream?

---

## Browser Compatibility

### Supported Browsers

| Browser | Streaming | Fallback |
|---|---|---|
| Chrome 89+ | ✅ Full support | N/A |
| Firefox 88+ | ✅ Full support | N/A |
| Safari 14.1+ | ✅ Full support | N/A |
| Edge 89+ | ✅ Full support | N/A |
| Mobile Safari | ✅ Full support | N/A |
| Mobile Chrome | ✅ Full support | N/A |
| IE 11 | ❌ No support | ✅ Non-streaming |

### Polyfill for Older Browsers

```typescript
import { ReadableStream } from 'web-streams-polyfill';

if (!window.ReadableStream) {
  window.ReadableStream = ReadableStream;
}
```

---

## Complete Example: Streaming Chat

```typescript
import { useState, useCallback, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export function StreamingAgentChat() {
  // Messages
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentContent, setCurrentContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  // Memory state
  const [sessionId] = useState(() => crypto.randomUUID());
  const [threadId, setThreadId] = useState<string | null>(null);
  const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({});
  
  // Input
  const [inputValue, setInputValue] = useState('');
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentContent]);
  
  const sendMessage = useCallback(async () => {
    if (!inputValue.trim() || isStreaming) return;
    
    const userText = inputValue;
    setInputValue('');
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userText,
      timestamp: new Date()
    }]);
    
    setCurrentContent('');
    setIsStreaming(true);
    
    // Cancel any previous request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    
    try {
      // Build request with full memory context
      const request = {
        input: [{ role: "user", content: userText }],
        custom_inputs: {
          user_id: getUserEmail(),
          session_id: sessionId,
          thread_id: threadId,
          genie_conversation_ids: genieConvIds,
          request_id: crypto.randomUUID()
        }
      };
      
      // Stream response
      const customOutputs = await streamAgentResponse(
        request,
        (chunk) => {
          setCurrentContent(prev => prev + chunk);
        },
        abortControllerRef.current.signal
      );
      
      // Add completed assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: currentContent,
        customOutputs,
        timestamp: new Date()
      }]);
      
      // Update memory state
      setThreadId(customOutputs.thread_id);
      setGenieConvIds(customOutputs.genie_conversation_ids || {});
      
      // Reset streaming content
      setCurrentContent('');
      
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Streaming error:', error);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${error.message}`,
          timestamp: new Date()
        }]);
      }
      setCurrentContent('');
    } finally {
      setIsStreaming(false);
    }
  }, [inputValue, isStreaming, sessionId, threadId, genieConvIds, currentContent]);
  
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-db-navy text-white p-4">
        <h1 className="text-xl font-semibold">Databricks Health Monitor</h1>
        <div className="text-xs text-gray-300 mt-1">
          Session: {sessionId.slice(0, 8)}
          {threadId && ` | Memory: Active`}
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-db-oat">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        
        {/* Current streaming message */}
        {isStreaming && currentContent && (
          <div className="message-bubble assistant">
            <StreamingMessage content={currentContent} />
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="border-t p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about costs, security, performance..."
            className="flex-1 px-4 py-2 border rounded"
            disabled={isStreaming}
          />
          
          {isStreaming ? (
            <button
              onClick={() => abortControllerRef.current?.abort()}
              className="px-6 py-2 bg-red-600 text-white rounded"
            >
              ⏹️ Cancel
            </button>
          ) : (
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim()}
              className="px-6 py-2 bg-primary text-white rounded disabled:opacity-50"
            >
              📤 Send
            </button>
          )}
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
            🔄 New Conversation (Clear Memory)
          </button>
        )}
      </div>
    </div>
  );
}
```

---

## References

### Related Documentation
- [15 - Frontend Integration Guide](15-frontend-integration-guide.md) - Complete integration overview
- [07 - Memory Management](07-memory-management.md) - Backend memory implementation
- [13 - Deployment and Monitoring](13-deployment-and-monitoring.md) - Endpoint deployment

### Official Documentation
- [Databricks Model Serving](https://docs.databricks.com/machine-learning/model-serving/)
- [ResponsesAgent Streaming](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent#streaming-responses)
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

## Quick Reference

### Streaming Request

```typescript
fetch(`${ENDPOINT_URL}?stream=true`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify(request)
})
```

### Event Types

1. **`response.output_item.delta`** → Append text chunk
2. **`response.output_item.done`** → Output complete (optional)
3. **`response.done`** → Save custom_outputs

### Essential Fields in custom_outputs

- `thread_id` → Store for next request (short-term memory)
- `genie_conversation_ids` → Store for Genie follow-ups
- `visualization_hint` → Render chart
- `data` → Chart data

---

**Last Updated**: January 9, 2026  
**Version**: 1.0  
**Status**: Ready for Frontend Implementation

