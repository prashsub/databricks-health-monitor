# Frontend Team Handoff: Health Monitor Agent Integration

**Date**: January 28, 2026  
**For**: Frontend Development Team  
**From**: Backend/ML Engineering Team

---

## 🎯 Your Mission

Build a chat interface that lets users ask questions about their Databricks environment using natural language.

**Example**:
- User asks: "What are my top 5 most expensive jobs?"
- Agent responds with analysis + auto-generated chart
- User follows up: "Show me details for the first one"
- Agent understands context and responds

---

## 📚 Documentation Location

**All guides are here**: `docs/agent-framework-design/frontend-guides/`

### Start Here (Required Reading)

1. **`00-README.md`** ⭐ - Complete roadmap and navigation
2. **`01-overview-and-quickstart.md`** - Build your first working chat in 10 minutes

### Reference While Coding

- **`QUICK-REFERENCE.md`** - One-page cheat sheet (print this!)
- **`03-api-reference.md`** - Complete API specification

### Implement These Features (In Order)

3. **`02-authentication-guide.md`** - Secure token management
4. **`04-streaming-responses.md`** - Real-time text updates
5. **`05-memory-integration.md`** - Conversation context
6. **`06-visualization-rendering.md`** - Chart rendering

---

## 🚀 Quick Start (10 Minutes)

### 1. Install Dependencies

```bash
npm install recharts react-markdown
```

### 2. Configure Endpoint

```typescript
// config.ts
export const AGENT_ENDPOINT = 
  'https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations';
```

### 3. Copy This Code (Working Chat Interface)

See **complete code in `01-overview-and-quickstart.md`**

It includes:
- Send/receive messages
- Display responses
- Memory tracking (thread_id)
- Error handling
- "New Conversation" button

---

## 🧠 How Memory Works (Critical!)

### Two Types of Memory

**Short-Term Memory** (Conversation Context):
- **Lasts**: 24 hours
- **You track**: `thread_id` (string from response)
- **Enables**: Follow-up questions ("Show me the first one")
- **How it works**: You include `thread_id` from previous response in next request

**Long-Term Memory** (User Preferences):
- **Lasts**: 365 days
- **You track**: `user_id` (user's email)
- **Enables**: Agent learns user patterns (often asks about cost → prioritizes cost data)
- **How it works**: You include `user_id` in all requests

### The Pattern

```typescript
// State
const [threadId, setThreadId] = useState(null);
const [genieConvIds, setGenieConvIds] = useState({});

// Query 1
Request: { thread_id: null }  // No context
Response: { thread_id: "abc123" }
Action: setThreadId("abc123")  // ← STORE THIS!

// Query 2
Request: { thread_id: "abc123" }  // ← INCLUDE THIS!
Response: { thread_id: "abc123" }
Action: Agent remembers Query 1

// New Conversation
Action: setThreadId(null)  // Clear context
```

**Critical**: If you don't include `thread_id`, follow-up questions won't work!

---

## 📊 How Visualization Works

### Agent Suggests, You Render

**Agent analyzes data and suggests chart type**:

```typescript
{
  "visualization_hint": {
    "type": "bar_chart",  // or line_chart, pie_chart, table
    "x_axis": "Job Name",
    "y_axis": "Total Cost",
    "title": "Top 5 Jobs by Cost"
  },
  "data": [
    { "Job Name": "ETL Pipeline", "Total Cost": "1250.50" },
    { "Job Name": "ML Training", "Total Cost": "980.25" }
  ]
}
```

**You render based on `type`**:

```typescript
if (hint.type === 'bar_chart') {
  return <BarChart data={data} xAxis={hint.x_axis} yAxis={hint.y_axis} />;
}
```

**Always provide**: Chart/table toggle (some users prefer tables)

---

## 🔐 Authentication (Important!)

### What You Need to Know

The agent uses **On-Behalf-Of-User (OBO) authentication**, which means:
- Queries execute with **the user's permissions**
- Each user sees only data they can access
- You must provide the **user's Databricks token** in requests

### Two Approaches

**Option 1: Backend Proxy (Recommended)**:
```
Your Frontend → Your Backend → Databricks Agent
             (your auth)    (user's Databricks token)
```

**Option 2: Direct Client**:
```
Your Frontend → Databricks Agent
             (user's Databricks token)
```

**See Guide 02 for complete implementation.**

---

## ⚡ Streaming (Recommended)

### Why Streaming?

**Without Streaming**:
```
User: "What are top jobs?"
[Waits 15 seconds...]
Agent: "Here are the results: ..."
```

**With Streaming**:
```
User: "What are top jobs?"
[Immediately] "Querying Cost Genie Space..."
[2s later] "Analyzing results..."
[5s later] "The top 5 jobs are: ETL Pipeline..."
[10s later] Charts appear
```

### How to Enable

Add `?stream=true` to endpoint URL and parse Server-Sent Events.

**See Guide 04 for complete implementation.**

---

## 📋 Implementation Checklist

### Week 1: Core Features

**Day 1-2**: Basic Chat
- [ ] Send query to agent
- [ ] Display text response
- [ ] Handle errors
- [ ] Loading states

**Day 3**: Authentication
- [ ] User token management
- [ ] Permission error handling
- [ ] Token expiry/refresh

**Day 4**: Streaming
- [ ] Real-time text updates
- [ ] Cancel button
- [ ] Fallback to non-streaming

### Week 2: Advanced Features

**Day 5**: Memory
- [ ] Track `thread_id`
- [ ] Include in follow-up queries
- [ ] "New Conversation" button
- [ ] Test multi-turn conversations

**Day 6-7**: Visualization
- [ ] Install Recharts
- [ ] Bar chart component
- [ ] Line chart component
- [ ] Pie chart component
- [ ] Data table component
- [ ] Chart/table toggle

**Day 8-9**: Polish
- [ ] Error messages polished
- [ ] Loading states refined
- [ ] Responsive design
- [ ] Accessibility
- [ ] Testing

---

## 🧪 How to Test

### Test Queries (Copy-Paste These)

**Test Basic Queries**:
```
"What are the top 5 most expensive jobs?"
"Show me costs for yesterday"
"List failed login attempts today"
```

**Test Follow-Ups** (requires memory):
```
1. "What are top 5 expensive jobs?"
2. "Show me details for the first one"
3. "How does that compare to last month?"
```

**Test Charts**:
- Bar chart: "Top 10 most expensive jobs"
- Line chart: "Cost trend over last 7 days"
- Pie chart: "Cost breakdown by workspace"

### Validation

- [ ] Basic query returns response
- [ ] `thread_id` stored after first query
- [ ] Follow-up query includes `thread_id`
- [ ] Agent understands context in follow-up
- [ ] Chart renders for data queries
- [ ] Table toggle works
- [ ] Errors display helpfully

---

## 🆘 Common Issues & Solutions

### "401 Unauthorized"
**Problem**: Invalid token  
**Solution**: Verify user's Databricks PAT is valid and not expired

### "Follow-up questions don't work"
**Problem**: Not including `thread_id`  
**Solution**: Store `thread_id` from response, include in next request

### "CORS error"
**Problem**: CORS not configured  
**Solution**: Use backend proxy OR ask Databricks admin to configure CORS

### "No charts appear"
**Problem**: Not checking for `data` in response  
**Solution**: Check if `custom_outputs.data` exists before rendering chart

### "Agent seems to forget context"
**Problem**: `thread_id` not persisted across page reloads  
**Solution**: Save to sessionStorage, restore on mount

---

## 📞 Getting Help

### Documentation
- **Navigation**: Start at `frontend-guides/00-README.md`
- **Quick help**: See `frontend-guides/QUICK-REFERENCE.md`
- **Detailed guides**: `frontend-guides/01-*.md` through `06-*.md`

### Example Code
- **Complete chat**: Guide 01
- **Streaming**: Guide 04
- **Memory**: Guide 05
- **Charts**: Guide 06

### Debugging
- **API errors**: Check Guide 03 error codes section
- **Auth issues**: See Guide 02 troubleshooting
- **Memory issues**: See Guide 05 debugging section
- **Chart issues**: See Guide 06 testing section

---

## 🎁 What We Built for You

### Backend (Already Complete)

✅ Agent with 5 domains (cost, security, performance, reliability, quality)  
✅ Genie Space integration for data queries  
✅ Memory system (short-term and long-term)  
✅ Visualization hint generation  
✅ Streaming support (SSE)  
✅ OBO authentication  
✅ Error handling and rate limiting  

### Documentation (Complete)

✅ 6 sequential guides (01-06)  
✅ Quick reference cheat sheet  
✅ Complete API specification  
✅ TypeScript type definitions  
✅ Copy-paste ready code examples  
✅ Testing queries and checklists  

### What You Need to Build

Your frontend app that:
1. Sends queries to agent endpoint
2. Displays streaming responses
3. Renders charts based on hints
4. Tracks memory state
5. Handles errors gracefully

---

## ⏱️ Timeline Expectations

### Realistic Timeline (7-9 days)
- Day 1-2: Basic chat working
- Day 3: Authentication secure
- Day 4: Streaming implemented
- Day 5: Memory working
- Day 6-7: Charts rendering
- Day 8-9: Polish and testing

### Optimistic Timeline (4-5 days)
- Day 1: Basic chat + auth
- Day 2: Streaming + memory
- Day 3-4: Charts
- Day 5: Polish

### What Can Slow You Down
- CORS configuration (if using direct client)
- Token management complexity
- Chart library learning curve
- Testing across browsers

---

## ✅ Definition of Done

Your integration is complete when:

### Functionality
- [ ] User can send queries and receive responses
- [ ] Responses stream in real-time (with fallback)
- [ ] Follow-up questions work ("show me the first one")
- [ ] Charts render automatically for data queries
- [ ] Users can toggle between chart and table views
- [ ] Errors display helpful messages with action items
- [ ] "New Conversation" clears context properly

### Quality
- [ ] Works on Chrome, Firefox, Safari, Edge
- [ ] Responsive on mobile and desktop
- [ ] Accessible (keyboard navigation, screen readers)
- [ ] Secure (tokens not exposed, input sanitized)
- [ ] Tested with all query types
- [ ] Rate limiting implemented

### Production Ready
- [ ] Authentication secure (httpOnly cookies or backend proxy)
- [ ] Error handling comprehensive
- [ ] Loading states for all async operations
- [ ] No console errors
- [ ] Performance optimized (lazy loading, memoization)

---

## 🎉 Success Criteria

**Week 1**: Basic chat working with streaming and memory  
**Week 2**: Charts rendering, production-ready

**Demo-able**: Users can have multi-turn conversations with intelligent visualizations

**Production-ready**: Secure, tested, performant, accessible

---

## 📞 Questions?

### Before You Start
1. Read `frontend-guides/00-README.md`
2. Follow `frontend-guides/01-overview-and-quickstart.md`
3. Get basic chat working (10 minutes)

### While Implementing
- Keep `frontend-guides/QUICK-REFERENCE.md` open
- Reference detailed guides as needed
- Check code examples in each guide

### If Stuck
- Check troubleshooting sections in guides
- Verify your requests match examples
- Check browser DevTools Network tab
- Review error handling in Guide 03

---

**Your Starting Point**: `frontend-guides/00-README.md`

**Good luck!** 🚀
