# Frontend Integration Guides - Reorganization Complete ✅

**Date**: January 28, 2026  
**Status**: Complete and verified against implementation

---

## Summary

I've reorganized and updated all frontend integration guides into a clear, sequential series that provides your frontend team with complete instructions for integrating with the Health Monitor Agent.

---

## What Was Created

### New Organized Structure

```
docs/agent-framework-design/frontend-guides/
│
├── 📘 00-README.md ⭐ START HERE
│   Complete navigation and implementation checklist
│
├── 📄 QUICK-REFERENCE.md
│   One-page cheat sheet (print and keep handy)
│
├── 📄 REORGANIZATION-SUMMARY.md
│   This reorganization explained
│
├── 📗 01-overview-and-quickstart.md
│   10-minute getting started guide with working code
│
├── 📗 02-authentication-guide.md
│   Token management, OBO patterns, security
│
├── 📗 03-api-reference.md
│   Complete API spec, error codes, rate limiting, TypeScript types
│
├── 📗 04-streaming-responses.md
│   Real-time SSE implementation with cancellation
│
├── 📗 05-memory-integration.md
│   Conversation context and user personalization
│
└── 📗 06-visualization-rendering.md
    Chart rendering with Databricks styling
```

### Old Files (Deprecated but Kept)

- `15-frontend-integration-guide.md` → Now `frontend-guides/01-overview-and-quickstart.md`
- `16-frontend-streaming-guide.md` → Now `frontend-guides/04-streaming-responses.md`
- `17-frontend-memory-guide.md` → Now `frontend-guides/05-memory-integration.md`
- `18-frontend-api-conventions.md` → Now `frontend-guides/03-api-reference.md`
- `14-visualization-hints-frontend.md` → Now `frontend-guides/06-visualization-rendering.md`

All old files updated with deprecation notices pointing to new locations.

---

## Key Improvements

### 1. Clear Entry Point

**Before**: No clear starting point, scattered docs  
**After**: `00-README.md` provides complete roadmap

### 2. Sequential Learning Path

**Before**: Numbered 14, 15, 16, 17, 18 (arbitrary)  
**After**: 01 → 02 → 03 → 04 → 05 → 06 (logical progression)

### 3. Verified Implementation

**Before**: Some examples didn't match actual code  
**After**: All code examples verified against `src/agents/setup/log_agent_model.py`

### 4. Complete Code Examples

**Before**: Partial examples, missing imports  
**After**: Copy-paste ready, complete implementations

### 5. Quick Reference

**Before**: No cheat sheet  
**After**: `QUICK-REFERENCE.md` for quick lookups

---

## What Frontend Team Gets

### Immediate (10 minutes)
- Working basic chat interface (Guide 01)
- Authentication setup (Guide 02)
- Test queries to verify integration

### Week 1 (3-4 days)
- Complete API client implementation (Guide 03)
- Streaming responses (Guide 04)
- Error handling
- Basic production-ready chat

### Week 2 (2-3 days)
- Memory integration for follow-ups (Guide 05)
- Chart rendering (Guide 06)
- Full-featured production app

---

## Implementation Verified

All guides verified against actual backend implementation:

### ✅ Visualization Hints (Lines 1361-1560)

```python
# Confirmed methods exist:
def _extract_tabular_data(self, response_text: str)
def _suggest_visualization(self, data, query, domain)
def _is_datetime_value(self, value: str)
def _is_numeric_value(self, value: str)
def _get_domain_preferences(self, domain: str, query: str)
```

### ✅ Memory Integration (Lines 2040-2070)

```python
# Confirmed fields:
user_id = custom_inputs.get("user_id")
thread_id = self._resolve_thread_id(custom_inputs)
conversation_history = self._get_conversation_history(thread_id)
user_preferences = self._get_user_preferences(user_id, query)
genie_conversation_ids = custom_inputs.get("genie_conversation_ids", {})
```

### ✅ Response Format (Lines 2190-2240, 2535-2598)

```python
# Confirmed custom_outputs structure:
custom_outputs={
    "thread_id": thread_id,
    "genie_conversation_ids": updated_conv_ids,
    "memory_status": "saved",
    "domain": domain,
    "source": "genie" | "error",
    "visualization_hint": {...},
    "data": [...],
    "error": str(e)  # if error occurred
}
```

### ✅ Streaming Support (Lines 2321-2668)

```python
# Confirmed streaming implementation:
def predict_stream(self, request) -> Generator:
    # Yields ResponsesAgentStreamEvent with deltas
    # Final yield includes custom_outputs
```

---

## Guide Contents Summary

### Guide 01: Overview and Quickstart
- **What**: Health Monitor Agent capabilities overview
- **Includes**: 10-minute working chat example
- **Key Topics**: Basic request/response, memory basics, test queries
- **Time**: 10 minutes to working prototype

### Guide 02: Authentication
- **What**: Secure authentication patterns
- **Includes**: OBO explanation, token management, security best practices
- **Key Topics**: Backend proxy vs direct client, token storage, permissions
- **Time**: 30 minutes - 2 hours

### Guide 03: API Reference
- **What**: Complete API specification
- **Includes**: All request/response fields, error codes, rate limiting
- **Key Topics**: TypeScript types, error handling, rate limiter implementation
- **Time**: Reference doc (use while coding)

### Guide 04: Streaming Responses
- **What**: Real-time streaming implementation
- **Includes**: SSE parsing, cancellation, fallback strategies
- **Key Topics**: Server-Sent Events, React hooks, performance optimization
- **Time**: 2-3 hours

### Guide 05: Memory Integration
- **What**: Conversation context and personalization
- **Includes**: Short-term and long-term memory patterns
- **Key Topics**: thread_id tracking, genie_conversation_ids, state management
- **Time**: 2-3 hours

### Guide 06: Visualization Rendering
- **What**: Intelligent chart rendering
- **Includes**: Bar, line, pie chart components with Databricks styling
- **Key Topics**: Recharts integration, domain colors, chart/table toggle
- **Time**: 4-6 hours

---

## Critical Information for Frontend Team

### 1. Memory System (Most Important!)

**Short-Term Memory (Conversation Context)**:
```typescript
// Frontend tracks
threadId: string | null  // From previous response

// Backend stores
Lakebase checkpoints table (24-hour retention)

// Enables
Follow-up questions: "Show me details for the first one"
```

**Long-Term Memory (User Preferences)**:
```typescript
// Frontend provides
user_id: string  // User's email

// Backend stores
Lakebase store table (365-day retention)

// Enables
Personalization based on past interactions
```

**Pattern**:
```typescript
// Query 1
Request: { thread_id: null }
Response: { thread_id: "abc123" }

// Query 2 (with context)
Request: { thread_id: "abc123" }
Response: { thread_id: "abc123" }
```

### 2. Visualization Hints

**Agent suggests chart type**:
- `bar_chart`: Top N, comparisons
- `line_chart`: Time series, trends
- `pie_chart`: Distributions
- `table`: Complex data
- `text`: No tabular data

**Frontend renders based on hint**:
```typescript
if (hint.type === 'bar_chart') {
  return <BarChart data={data} hint={hint} />;
}
```

### 3. Streaming vs Non-Streaming

**Streaming** (Recommended):
- Add `?stream=true` to URL
- Parse Server-Sent Events
- Display text in real-time
- Better UX

**Non-Streaming** (Fallback):
- Standard JSON response
- Wait for complete response
- Simpler implementation

### 4. Genie Conversation Continuity

**Per-domain tracking**:
```typescript
genie_conversation_ids: {
  "cost": "conv_abc123",
  "security": "conv_def456"
}
```

**Why**: Each Genie Space has separate conversations. Switching between cost and security questions maintains context in each domain.

---

## Quick Start for Frontend Team

### Step 1: Read the README (5 minutes)
👉 **Start**: `frontend-guides/00-README.md`

### Step 2: Build Basic Chat (1 hour)
👉 **Follow**: `frontend-guides/01-overview-and-quickstart.md`

Result: Working chat interface with:
- Send/receive messages
- Display responses
- Basic error handling

### Step 3: Add Streaming (2 hours)
👉 **Follow**: `frontend-guides/04-streaming-responses.md`

Result: Real-time text updates, cancel button

### Step 4: Add Memory (2 hours)
👉 **Follow**: `frontend-guides/05-memory-integration.md`

Result: Follow-up questions work, conversation context

### Step 5: Add Charts (4 hours)
👉 **Follow**: `frontend-guides/06-visualization-rendering.md`

Result: Intelligent chart rendering, domain styling

### Total Time: 2-3 days for complete integration

---

## Testing Checklist for Frontend Team

### Basic Integration
- [ ] Can send query and receive response
- [ ] Natural language text displays
- [ ] Error messages show correctly
- [ ] Loading states work

### Streaming
- [ ] Text appears in real-time
- [ ] Cancel button works
- [ ] Fallback to non-streaming if SSE fails

### Memory
- [ ] First query: `thread_id` stored
- [ ] Second query: `thread_id` included, agent remembers context
- [ ] "New Conversation" clears `thread_id`
- [ ] Multiple domains tracked separately

### Visualization
- [ ] Bar charts render for "top N" queries
- [ ] Line charts render for "trend" queries
- [ ] Pie charts render for "breakdown" queries
- [ ] Table view available for all data
- [ ] Chart/table toggle works
- [ ] Domain colors applied correctly

---

## Where to Get Help

### Documentation
- **Start Here**: `frontend-guides/00-README.md`
- **Quick Lookup**: `frontend-guides/QUICK-REFERENCE.md`
- **Backend Details**: `14-visualization-hints-backend.md`
- **OBO Auth**: `obo-authentication-guide.md`

### Example Code
- **Complete React chat**: Guide 01, Guide 04
- **Memory management**: Guide 05
- **Chart components**: Guide 06
- **API client**: Guide 03

### Troubleshooting
- **Auth issues**: Guide 02
- **API errors**: Guide 03 (error codes section)
- **Streaming issues**: Guide 04 (debugging section)
- **Memory issues**: Guide 05 (debugging section)
- **Chart issues**: Guide 06 (testing section)

---

## Next Steps for You

### For Frontend Team Lead
1. **Share** `frontend-guides/00-README.md` with team
2. **Assign** Guide 01 as first task
3. **Review** completed code after each guide
4. **Track** progress using checklist in README

### For Individual Developers
1. **Read** `frontend-guides/00-README.md`
2. **Follow** guides 01 → 02 → 03 → 04 → 05 → 06 sequentially
3. **Keep** `QUICK-REFERENCE.md` open while coding
4. **Test** with example queries from each guide

### For Backend Developers
1. **Review** `frontend-guides/03-api-reference.md` to understand frontend expectations
2. **Reference** when frontend team asks questions
3. **Update** backend guide (`14-visualization-hints-backend.md`) if implementation changes

---

## Files Changed

### Created (9 new files)
✅ `frontend-guides/00-README.md`  
✅ `frontend-guides/01-overview-and-quickstart.md`  
✅ `frontend-guides/02-authentication-guide.md`  
✅ `frontend-guides/03-api-reference.md`  
✅ `frontend-guides/04-streaming-responses.md`  
✅ `frontend-guides/05-memory-integration.md`  
✅ `frontend-guides/06-visualization-rendering.md`  
✅ `frontend-guides/QUICK-REFERENCE.md`  
✅ `frontend-guides/REORGANIZATION-SUMMARY.md`  

### Updated (5 files with deprecation notices)
✅ `15-frontend-integration-guide.md`  
✅ `16-frontend-streaming-guide.md`  
✅ `17-frontend-memory-guide.md`  
✅ `18-frontend-api-conventions.md`  
✅ `14-visualization-hints-frontend.md`  

### Unchanged (backend docs)
- `14-visualization-hints-backend.md`
- `obo-authentication-guide.md`
- `visualization-hints-implementation-summary.md`

---

## Key Takeaways

### For Frontend Developers

1. **Memory is crucial**: Without `thread_id`, follow-up questions don't work
2. **Streaming is optional**: But significantly improves UX
3. **Visualization hints are automatic**: Agent decides chart type, you just render
4. **User permissions matter**: Queries execute with user's access rights
5. **Implementation is verified**: All code examples match actual backend

### For Backend Developers

1. **Frontend needs these fields**: `thread_id`, `genie_conversation_ids`, `visualization_hint`, `data`
2. **Error responses must include**: `source: "error"`, `error: "message"`
3. **Streaming works differently**: SSE events, not JSON response
4. **Rate limiting is enforced**: 5 queries/minute per domain per user

---

## Success Metrics

Your frontend team will have successfully integrated when:

- ✅ Basic queries work and display responses
- ✅ Follow-up questions reference previous context
- ✅ Responses stream in real-time
- ✅ Charts render automatically for appropriate queries
- ✅ Users can toggle between charts and tables
- ✅ Errors display helpful messages
- ✅ Memory state persists across page reloads (session)
- ✅ Production-ready security implemented

---

## Estimated Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| **Phase 1: Basic Integration** | 2-3 days | Working chat with error handling |
| **Phase 2: Streaming** | 1 day | Real-time responses with cancel |
| **Phase 3: Memory** | 1 day | Follow-up questions work |
| **Phase 4: Visualization** | 2 days | Charts render automatically |
| **Phase 5: Polish** | 1-2 days | Production-ready, tested |
| **Total** | **7-9 days** | Complete integration |

---

## What the Frontend Team Needs to Know

### 1. How Memory Works

**Short-Term Memory (24 hours)**:
- You include `thread_id` from previous response
- Backend loads conversation history
- Agent understands context ("the first one", "that query")

**Long-Term Memory (365 days)**:
- You include `user_id` (email)
- Backend learns user preferences
- Agent personalizes responses over time

**Genie Conversations (per domain)**:
- You include `genie_conversation_ids` object
- Backend maintains separate conversation per domain
- Enables domain-specific follow-ups

### 2. How to Visualize Data

**Agent Returns**:
```json
{
  "visualization_hint": {
    "type": "bar_chart",
    "x_axis": "Job Name",
    "y_axis": "Total Cost",
    "title": "Top 5 Jobs"
  },
  "data": [
    { "Job Name": "ETL", "Total Cost": "1250.50" }
  ]
}
```

**Frontend Renders**:
1. Check `hint.type`
2. Use appropriate chart component
3. Map `data` to chart using `x_axis`/`y_axis`
4. Apply domain-specific colors
5. Provide table toggle

### 3. How to Handle Errors

**Check Response**:
```typescript
if (response.custom_outputs.source === 'error') {
  // Query failed
  const errorMessage = response.custom_outputs.error;
  
  if (errorMessage.includes('permission')) {
    // Show permission setup guide
  } else if (errorMessage.includes('rate limit')) {
    // Wait 60s and retry
  } else {
    // Generic error message
  }
}
```

---

## Code Snippets (Copy-Paste Ready)

### Basic Request

```typescript
const response = await fetch(ENDPOINT_URL, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    input: [{ role: 'user', content: query }],
    custom_inputs: {
      user_id: userEmail,
      session_id: sessionId,
      thread_id: threadId,
      genie_conversation_ids: genieConvIds
    }
  })
});

const data = await response.json();
```

### Extract Response

```typescript
// Text
const text = response.output[0].content[0].text;

// Memory (store these!)
const { thread_id, genie_conversation_ids } = response.custom_outputs;

// Visualization
const { visualization_hint, data } = response.custom_outputs;

// Error check
const isError = response.custom_outputs.source === 'error';
```

### Render Chart

```typescript
import { BarChart, Bar, XAxis, YAxis } from 'recharts';

<BarChart data={data} width={600} height={400}>
  <XAxis dataKey={hint.x_axis} />
  <YAxis />
  <Bar dataKey={hint.y_axis} fill="#2272B4" />
</BarChart>
```

---

## Testing Queries

```typescript
// Basic queries (no memory needed)
"What are the top 5 most expensive jobs?"
"Show me costs for yesterday"
"List failed login attempts today"

// Follow-up queries (requires thread_id)
First: "What are top 5 expensive jobs?"
Then: "Show me details for the first one"
Then: "How does that compare to last month?"

// Multi-domain (tracks separate conversations)
"Show cost trends"           // domain=cost, conv_cost_123
"Show security events"       // domain=security, conv_security_456
"Break down those costs"     // domain=cost, uses conv_cost_123
```

---

## Critical Fields Checklist

### Request (Must Send)
- ✅ `input[0].content` - User's query
- ✅ `custom_inputs.user_id` - For personalization

### Request (For Follow-ups)
- ✅ `custom_inputs.thread_id` - From previous response
- ✅ `custom_inputs.genie_conversation_ids` - From previous response

### Response (Must Extract)
- ✅ `output[0].content[0].text` - Display this
- ✅ `custom_outputs.thread_id` - Store for next query
- ✅ `custom_outputs.genie_conversation_ids` - Store for next query
- ✅ `custom_outputs.source` - Check for errors

### Response (For Visualization)
- ✅ `custom_outputs.visualization_hint` - Chart type
- ✅ `custom_outputs.data` - Tabular data

---

## Contact & Support

- **Documentation**: `frontend-guides/00-README.md`
- **Quick Help**: `frontend-guides/QUICK-REFERENCE.md`
- **Detailed Guides**: `frontend-guides/01-*.md` through `06-*.md`
- **Backend Details**: `14-visualization-hints-backend.md`

---

**Status**: ✅ Complete and ready for frontend implementation  
**Last Updated**: January 28, 2026  
**Version**: 1.0
