# Frontend Guide 04: Streaming Responses

> **Purpose**: Implement real-time streaming for better user experience
> 
> **Audience**: Frontend developers enhancing chat interfaces
> 
> **Time to Implement**: 2-3 hours

---

## Why Streaming?

**User Experience Benefits**:
- ✅ Immediate feedback ("Querying Cost Genie Space...")
- ✅ See analysis generate in real-time
- ✅ Reduced perceived latency (feels faster)
- ✅ Cancellable long-running queries
- ✅ Progress indicators during processing

**Without Streaming**:
- ❌ User waits 10-30 seconds for complete response
- ❌ No feedback during processing
- ❌ Can't cancel if query takes too long

---

## How Streaming Works

### Server-Sent Events (SSE)

The agent uses **Server-Sent Events** to stream responses:

```
1. Frontend: POST with ?stream=true
2. Backend: Opens SSE connection
3. Backend: Sends multiple "data: {...}" events
4. Frontend: Receives and processes each event
5. Backend: Sends final "data: {...}" with custom_outputs
6. Frontend: Closes connection
```

### Event Types

| Event Type | When Sent | Contains | Frontend Action |
|---|---|---|---|
| `response.output_item.delta` | During generation | Text chunk | Append to display |
| `response.output_item.done` | After all chunks | Complete text | Optional (usually ignore) |
| `response.done` | At end | `custom_outputs` | **Store memory state, render viz** |

---

## Implementation

### Basic Streaming Function

```typescript
/**
 * Stream agent response using Server-Sent Events.
 * 
 * @param request - Agent request
 * @param onChunk - Callback for each text chunk
 * @returns Final custom_outputs with memory state and viz hints
 */
export async function streamAgentResponse(
  request: AgentRequest,
  userToken: string,
  onChunk: (text: string) => void
): Promise<CustomOutputs> {
  // Add streaming parameter
  const streamUrl = `${ENDPOINT_URL}?stream=true`;
  
  const response = await fetch(streamUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  if (!response.body) {
    throw new Error('Response body is null');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  let buffer = '';
  let finalCustomOutputs: CustomOutputs | null = null;
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      // Decode and add to buffer
      buffer += decoder.decode(value, { stream: true });
      
      // Split by newlines (SSE format: "data: {...}\n")
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';  // Keep incomplete line
      
      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue;
        
        const jsonStr = line.slice(6);  // Remove "data: " prefix
        
        try {
          const event = JSON.parse(jsonStr);
          
          // TEXT DELTA: Real-time text chunks
          if (event.type === 'response.output_item.delta') {
            if (event.delta?.type === 'output_text' && event.delta.text) {
              onChunk(event.delta.text);
            }
          }
          
          // RESPONSE DONE: Final event with custom_outputs
          else if (event.type === 'response.done') {
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
  
  return finalCustomOutputs || { 
    thread_id: '', 
    genie_conversation_ids: {}, 
    memory_status: 'error',
    domain: 'unified',
    source: 'error'
  };
}
```

### React Hook for Streaming

```typescript
import { useState, useCallback, useRef, useEffect } from 'react';

interface UseStreamingOptions {
  onComplete?: (customOutputs: CustomOutputs) => void;
  onError?: (error: Error) => void;
}

export function useAgentStreaming(options: UseStreamingOptions = {}) {
  const [content, setContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [customOutputs, setCustomOutputs] = useState<CustomOutputs | null>(null);
  const [error, setError] = useState<Error | null>(null);
  
  const isMountedRef = useRef(true);
  
  useEffect(() => {
    return () => { isMountedRef.current = false; };
  }, []);
  
  const sendMessage = useCallback(async (
    request: AgentRequest,
    userToken: string
  ) => {
    if (!isMountedRef.current) return;
    
    setContent('');
    setIsStreaming(true);
    setError(null);
    setCustomOutputs(null);
    
    try {
      const outputs = await streamAgentResponse(
        request,
        userToken,
        (chunk) => {
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
        const error = err as Error;
        setError(error);
        options.onError?.(error);
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

### Usage in Chat Component

```typescript
export function StreamingChatInterface({ userToken }: { userToken: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  // Memory state
  const [sessionId] = useState(() => crypto.randomUUID());
  const [threadId, setThreadId] = useState<string | null>(null);
  const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({});
  
  // Streaming hook
  const { content, isStreaming, customOutputs, sendMessage } = useAgentStreaming({
    onComplete: (outputs) => {
      // Update memory state
      setThreadId(outputs.thread_id);
      setGenieConvIds(outputs.genie_conversation_ids);
      
      // Add completed message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: content,
        customOutputs: outputs,
        timestamp: new Date()
      }]);
    }
  });
  
  const handleSend = async () => {
    if (!inputValue.trim() || isStreaming) return;
    
    const userText = inputValue;
    setInputValue('');
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userText,
      timestamp: new Date()
    }]);
    
    // Send with streaming
    await sendMessage(
      {
        input: [{ role: 'user', content: userText }],
        custom_inputs: {
          user_id: 'user@company.com',
          session_id: sessionId,
          thread_id: threadId,
          genie_conversation_ids: genieConvIds
        }
      },
      userToken
    );
  };
  
  return (
    <div className="h-screen flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        
        {/* Current streaming message */}
        {isStreaming && content && (
          <div className="message assistant streaming">
            <ReactMarkdown>{content}</ReactMarkdown>
            <span className="animate-pulse ml-1">▋</span>
          </div>
        )}
      </div>
      
      {/* Input */}
      <div className="border-t p-4">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          disabled={isStreaming}
          placeholder="Ask about costs, security, performance..."
          className="w-full px-4 py-2 border rounded"
        />
        
        {isStreaming && (
          <div className="mt-2 text-sm text-gray-600 flex items-center gap-2">
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
            <span>Streaming response...</span>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## Cancelling Requests

### AbortController Pattern

```typescript
export function useAgentStreaming() {
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const sendMessage = useCallback(async (request: AgentRequest, userToken: string) => {
    // Cancel previous request if still running
    abortControllerRef.current?.abort();
    
    // Create new controller
    abortControllerRef.current = new AbortController();
    
    try {
      const response = await fetch(
        `${ENDPOINT_URL}?stream=true`,
        {
          method: 'POST',
          headers: { /* ... */ },
          body: JSON.stringify(request),
          signal: abortControllerRef.current.signal  // ✅ Add abort signal
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

### Cancel Button UI

```typescript
export function StreamingInput({ isStreaming, onSend, onCancel }: Props) {
  return (
    <div className="flex gap-2">
      <input
        type="text"
        disabled={isStreaming}
        onKeyPress={(e) => e.key === 'Enter' && !isStreaming && onSend()}
      />
      
      {isStreaming ? (
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          ⏹️ Cancel
        </button>
      ) : (
        <button
          onClick={onSend}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          📤 Send
        </button>
      )}
    </div>
  );
}
```

---

## Fallback Strategy

### Automatic Fallback to Non-Streaming

```typescript
async function sendAgentQuery(
  request: AgentRequest,
  userToken: string,
  preferStreaming: boolean = true
): Promise<{ content: string; customOutputs: CustomOutputs }> {
  
  // Try streaming first if preferred
  if (preferStreaming) {
    try {
      let content = '';
      const customOutputs = await streamAgentResponse(
        request,
        userToken,
        (chunk) => { content += chunk; }
      );
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
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  const data = await response.json();
  const content = data.output[0]?.content[0]?.text || '';
  const customOutputs = data.custom_outputs;
  
  return { content, customOutputs };
}
```

---

## Performance Optimization

### Buffered Rendering

Instead of updating UI for every tiny chunk, buffer small chunks:

```typescript
async function streamWithBuffering(
  request: AgentRequest,
  userToken: string,
  onChunk: (text: string) => void
): Promise<CustomOutputs> {
  let buffer = '';
  let lastFlush = Date.now();
  const FLUSH_INTERVAL_MS = 50;  // Flush every 50ms
  
  const flushBuffer = () => {
    if (buffer) {
      onChunk(buffer);
      buffer = '';
    }
  };
  
  const customOutputs = await streamAgentResponse(
    request,
    userToken,
    (chunk) => {
      buffer += chunk;
      
      // Flush if enough time passed or buffer is large
      const now = Date.now();
      if (now - lastFlush > FLUSH_INTERVAL_MS || buffer.length > 100) {
        flushBuffer();
        lastFlush = now;
      }
    }
  );
  
  // Flush any remaining buffer
  flushBuffer();
  
  return customOutputs;
}
```

### React.memo for Messages

```typescript
export const MessageBubble = React.memo(
  ({ message }: { message: Message }) => {
    return (
      <div className="message-bubble">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
    );
  },
  // Only re-render if content changed
  (prev, next) => prev.message.content === next.message.content
);
```

---

## Streaming UI Patterns

### Pattern 1: Typewriter Effect

```typescript
export function StreamingText({ content }: { content: string }) {
  return (
    <div className="streaming-text">
      <ReactMarkdown>{content}</ReactMarkdown>
      {/* Blinking cursor */}
      <span className="animate-pulse ml-1 text-blue-600">▋</span>
    </div>
  );
}
```

### Pattern 2: Progress Stages

```typescript
export function StreamingIndicator({ content }: { content: string }) {
  // Detect stage from content
  const stage = 
    content.includes('Querying') ? 'querying' :
    content.includes('Analysis:') ? 'analyzing' :
    'complete';
  
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
```

---

## Error Handling

### Connection Errors

```typescript
try {
  await streamAgentResponse(request, userToken, onChunk);
} catch (error) {
  if (error.message.includes('Failed to fetch')) {
    showError('Network error. Please check your connection.');
  } else if (error.message.includes('HTTP 401')) {
    redirectToLogin('Token expired');
  } else if (error.message.includes('HTTP 429')) {
    showError('Rate limit exceeded. Please wait 60 seconds.');
    setTimeout(() => retryQuery(), 60000);
  } else {
    showError('An error occurred. Please try again.');
  }
}
```

### Partial Stream Errors

```typescript
async function streamWithErrorRecovery(
  request: AgentRequest,
  userToken: string,
  onChunk: (text: string) => void
): Promise<CustomOutputs> {
  let receivedAnyData = false;
  
  try {
    return await streamAgentResponse(request, userToken, (chunk) => {
      receivedAnyData = true;
      onChunk(chunk);
    });
    
  } catch (error) {
    if (receivedAnyData) {
      // Stream started but interrupted
      onChunk('\n\n---\n⚠️ Response interrupted. Results may be incomplete.');
    }
    throw error;
  }
}
```

---

## Browser Compatibility

### Supported Browsers

| Browser | Streaming Support | Fallback Needed |
|---|---|---|
| Chrome 89+ | ✅ Full support | No |
| Firefox 88+ | ✅ Full support | No |
| Safari 14.1+ | ✅ Full support | No |
| Edge 89+ | ✅ Full support | No |
| Mobile Safari | ✅ Full support | No |
| Mobile Chrome | ✅ Full support | No |
| IE 11 | ❌ No support | Yes (non-streaming) |

### Feature Detection

```typescript
function supportsStreaming(): boolean {
  return (
    typeof ReadableStream !== 'undefined' &&
    typeof TextDecoder !== 'undefined' &&
    typeof fetch !== 'undefined'
  );
}

// Use appropriate method
const sendQuery = supportsStreaming()
  ? sendStreamingQuery
  : sendNonStreamingQuery;
```

---

## Complete Example: Streaming Chat

```typescript
import { useState, useCallback, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

export function StreamingAgentChat({ userToken }: { userToken: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentContent, setCurrentContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [inputValue, setInputValue] = useState('');
  
  // Memory state
  const [sessionId] = useState(() => crypto.randomUUID());
  const [threadId, setThreadId] = useState<string | null>(null);
  const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({});
  
  // Refs
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll
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
    
    // Cancel previous request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    
    try {
      // Build request with memory
      const request = {
        input: [{ role: 'user', content: userText }],
        custom_inputs: {
          user_id: 'user@company.com',
          session_id: sessionId,
          thread_id: threadId,
          genie_conversation_ids: genieConvIds,
          request_id: crypto.randomUUID()
        }
      };
      
      // Stream response
      const customOutputs = await streamAgentResponse(
        request,
        userToken,
        (chunk) => setCurrentContent(prev => prev + chunk)
      );
      
      // Add completed assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: currentContent,
        customOutputs,
        timestamp: new Date()
      }]);
      
      // Update memory
      setThreadId(customOutputs.thread_id);
      setGenieConvIds(customOutputs.genie_conversation_ids);
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
  }, [inputValue, isStreaming, sessionId, threadId, genieConvIds, currentContent, userToken]);
  
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-gray-900 text-white p-4">
        <h1 className="text-xl font-semibold">Databricks Health Monitor</h1>
        <p className="text-sm text-gray-400">
          {threadId ? `💬 ${messages.length / 2} exchanges` : '💭 New conversation'}
        </p>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        
        {/* Streaming content */}
        {isStreaming && currentContent && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg p-4 max-w-2xl">
              <StreamingText content={currentContent} />
            </div>
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
            disabled={isStreaming}
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          
          {isStreaming ? (
            <button
              onClick={() => abortControllerRef.current?.abort()}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              ⏹️ Cancel
            </button>
          ) : (
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
            🔄 New Conversation
          </button>
        )}
      </div>
    </div>
  );
}
```

---

## Testing Streaming

### Manual Tests

- [ ] **Text appears in real-time** (not all at once)
- [ ] **Cancel button works** (stops mid-stream)
- [ ] **custom_outputs received** at end of stream
- [ ] **Memory state updated** after stream completes
- [ ] **Fallback works** if streaming fails
- [ ] **Multiple rapid queries** don't interfere with each other

### Automated Tests

```typescript
describe('Streaming', () => {
  it('should receive text chunks', async () => {
    const chunks: string[] = [];
    
    await streamAgentResponse(
      mockRequest,
      'test_token',
      (chunk) => chunks.push(chunk)
    );
    
    expect(chunks.length).toBeGreaterThan(5);
    expect(chunks.join('')).toContain('Analysis:');
  });
  
  it('should return custom_outputs', async () => {
    const outputs = await streamAgentResponse(
      mockRequest,
      'test_token',
      () => {}
    );
    
    expect(outputs.thread_id).toBeTruthy();
    expect(outputs.visualization_hint).toBeDefined();
  });
  
  it('should handle cancellation', async () => {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 100);
    
    await expect(
      streamAgentResponse(mockRequest, 'test_token', () => {}, controller.signal)
    ).rejects.toThrow('AbortError');
  });
});
```

---

## Debugging Streaming

### Add Logging

```typescript
async function streamAgentResponse(request, userToken, onChunk) {
  console.log('[STREAM] Starting...');
  
  const response = await fetch(`${ENDPOINT_URL}?stream=true`, { /* ... */ });
  const reader = response.body!.getReader();
  
  let chunkCount = 0;
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    chunkCount++;
    console.log(`[STREAM] Chunk ${chunkCount}: ${value.length} bytes`);
    
    // ... process chunk
  }
  
  console.log(`[STREAM] Complete: ${chunkCount} chunks received`);
}
```

### Common Issues

**Issue: No chunks received**
- Check URL has `?stream=true`
- Verify CORS allows streaming
- Check network tab for response

**Issue: Incomplete responses**
- Network timeout occurred
- Backend error mid-stream
- Check for `response.done` event

**Issue: custom_outputs not received**
- Verify `response.done` event is received
- Check event parsing logic
- Log all events to console

---

## Quick Reference

### Enable Streaming

```typescript
// Add ?stream=true to URL
const streamUrl = `${ENDPOINT_URL}?stream=true`;
```

### Parse Events

```typescript
// Parse SSE format: "data: {...}\n"
if (line.startsWith('data: ')) {
  const event = JSON.parse(line.slice(6));
  
  if (event.type === 'response.output_item.delta') {
    onChunk(event.delta.text);  // Text chunk
  }
  
  if (event.type === 'response.done') {
    return event.custom_outputs;  // Final state
  }
}
```

### Essential Pattern

```typescript
1. Add ?stream=true to URL
2. Read response.body with getReader()
3. Decode chunks with TextDecoder
4. Split by '\n' and parse "data: {...}"
5. Yield delta.text for display
6. Return custom_outputs from response.done
```

---

**Next Guide**: [05 - Memory Integration](05-memory-integration.md) (Conversation context and personalization)

**Previous Guide**: [03 - API Reference](03-api-reference.md)
