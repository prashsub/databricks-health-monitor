# Frontend Integration Guides for Health Monitor Agent

> **Purpose**: Complete guide series for frontend developers integrating with the Health Monitor Agent
> 
> **Last Updated**: January 28, 2026

---

## Quick Navigation

These guides are designed to be read in sequence. Each builds on concepts from previous guides.

### Getting Started (Read First)

**[01 - Overview and Quickstart](01-overview-and-quickstart.md)**
- What the agent is and what it can do
- Quick integration example
- 10-minute getting started guide
- When to read: **Start here**

**[02 - Authentication Guide](02-authentication-guide.md)**
- On-Behalf-Of-User (OBO) authentication
- Token management patterns
- Security best practices
- When to read: **Before making your first API call**

### Core Integration (Essential)

**[03 - API Reference](03-api-reference.md)**
- Request and response formats
- Error codes and handling
- Rate limiting and timeouts
- TypeScript type definitions
- When to read: **When implementing the API client**

**[04 - Streaming Responses](04-streaming-responses.md)**
- Server-Sent Events (SSE) implementation
- Real-time text updates
- Cancellation support
- Fallback strategies
- When to read: **When adding real-time chat experience**

### Advanced Features (Recommended)

**[05 - Memory Integration](05-memory-integration.md)**
- Short-term memory (conversation context)
- Long-term memory (user preferences)
- Genie conversation continuity
- State management patterns
- When to read: **After basic chat works, to add follow-up questions**

**[06 - Visualization Rendering](06-visualization-rendering.md)**
- Parsing visualization hints
- Rendering bar, line, and pie charts
- Domain-specific styling
- Chart/table toggle
- When to read: **After memory works, to add intelligent charts**

---

## Implementation Checklist

Use this to track your progress:

### Phase 1: Basic Integration (Day 1-2)
- [ ] Read guides 01-03 (Overview, Auth, API)
- [ ] Set up authentication (user tokens)
- [ ] Implement basic request/response
- [ ] Handle errors gracefully
- [ ] Test with simple queries

### Phase 2: Streaming (Day 3-4)
- [ ] Read guide 04 (Streaming)
- [ ] Implement SSE streaming
- [ ] Add real-time text updates
- [ ] Add cancellation button
- [ ] Test streaming with long queries

### Phase 3: Memory (Day 5-6)
- [ ] Read guide 05 (Memory)
- [ ] Track thread_id for conversation context
- [ ] Track genie_conversation_ids for follow-ups
- [ ] Add "New Conversation" button
- [ ] Test multi-turn conversations

### Phase 4: Visualization (Day 7-8)
- [ ] Read guide 06 (Visualization)
- [ ] Install chart library (Recharts)
- [ ] Implement chart components
- [ ] Parse visualization hints
- [ ] Add chart/table toggle
- [ ] Test with different query types

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                        Frontend App                             │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Input → API Client → Streaming Handler → State Manager   │
│                    │              │                  │           │
│                    ▼              ▼                  ▼           │
│               Auth Layer    SSE Parser      Memory Context      │
│                    │              │                  │           │
│                    ▼              ▼                  ▼           │
│               Token Mgmt    Text Deltas     thread_id tracking  │
│                    │              │                  │           │
│                    └──────────────┴──────────────────┘           │
│                                   │                              │
│                                   ▼                              │
│                            Response Display                      │
│                                   │                              │
│                        ┌──────────┴──────────┐                  │
│                        ▼                     ▼                   │
│                 Markdown Text         Visualization              │
│                                              │                   │
│                                   ┌──────────┴────────┐          │
│                                   ▼                   ▼          │
│                            Chart Renderer      Data Table        │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
         ┌──────────────────────────────────────────────┐
         │    Databricks Model Serving Endpoint         │
         │         (Health Monitor Agent)               │
         └──────────────────────────────────────────────┘
```

---

## Key Concepts

### 1. Streaming Responses
- Agent sends text in real-time chunks (Server-Sent Events)
- Improves perceived performance
- Allows cancellation of long-running queries

### 2. Memory System
- **Short-term**: Conversation context within a session (24 hours)
- **Long-term**: User preferences across sessions (365 days)
- Frontend only tracks IDs, backend manages storage

### 3. Visualization Hints
- Agent analyzes data and suggests chart type
- Frontend renders based on hint (bar, line, pie, table)
- Domain-specific styling preferences included

### 4. OBO Authentication
- Queries execute with end-user's permissions
- Each user sees their own data
- Frontend provides user's Databricks token

---

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
npm install recharts react-markdown
# or
yarn add recharts react-markdown
```

### 2. Basic Request Example

```typescript
const response = await fetch(
  'https://workspace.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userDatabricksToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      input: [{ role: "user", content: "What are the top 5 expensive jobs?" }],
      custom_inputs: {
        user_id: "user@company.com",
        session_id: generateUUID()
      }
    })
  }
);

const data = await response.json();
console.log(data.output[0].content[0].text);  // Natural language response
console.log(data.custom_outputs.visualization_hint);  // Chart suggestion
console.log(data.custom_outputs.data);  // Tabular data
```

### 3. Render Response

```typescript
import ReactMarkdown from 'react-markdown';

function AgentMessage({ response }) {
  return (
    <div>
      {/* Natural language text */}
      <ReactMarkdown>{response.output[0].content[0].text}</ReactMarkdown>
      
      {/* Visualization (if data present) */}
      {response.custom_outputs.data && (
        <ChartOrTable 
          hint={response.custom_outputs.visualization_hint}
          data={response.custom_outputs.data}
        />
      )}
    </div>
  );
}
```

---

## Common Questions

### Q: Do I need to implement memory?
**A:** Memory is optional but highly recommended. Without it:
- ✅ Basic queries work fine
- ❌ Follow-up questions don't work ("Show me details for the first one")
- ❌ Agent can't personalize to user preferences

### Q: Can I skip streaming?
**A:** Yes, streaming is optional. Non-streaming works but:
- ✅ Simpler implementation
- ❌ User waits for complete response (10-30s)
- ❌ No real-time feedback
- ❌ Can't cancel long queries

### Q: What if I don't want charts?
**A:** You can always show tables instead:
- Ignore `visualization_hint`
- Render `custom_outputs.data` as a table
- Still works perfectly

### Q: How do I handle errors?
**A:** Check `custom_outputs.source`:
- `"genie"` = Success, show response normally
- `"error"` = Query failed, show error message from `custom_outputs.error`

---

## Support and Resources

### Documentation
- **Backend Implementation**: See `../14-visualization-hints-backend.md`
- **Databricks Docs**: https://docs.databricks.com/machine-learning/model-serving/
- **Agent Framework**: https://docs.databricks.com/generative-ai/agent-framework/

### Example Code
- Complete React example: See Guide 01
- TypeScript types: See Guide 03
- Chart components: See Guide 06

### Getting Help
- Check troubleshooting sections in each guide
- Review error handling in Guide 03
- See authentication debugging in Guide 02

---

## Next Steps

👉 **Start with [01 - Overview and Quickstart](01-overview-and-quickstart.md)**

After completing all 6 guides, you'll have a fully functional integration with:
- ✅ Streaming responses for real-time feedback
- ✅ Intelligent chart rendering based on data
- ✅ Conversation context for follow-up questions
- ✅ User personalization across sessions
- ✅ Robust error handling
- ✅ Secure OBO authentication
