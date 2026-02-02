# Quick Reference: Health Monitor Agent Integration

> **One-page cheat sheet for frontend developers**
> 
> **Print this page** for quick reference while coding

---

## Essential URLs

```typescript
// Endpoint URL format
https://<workspace-url>/serving-endpoints/<endpoint-name>/invocations

// Development
https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations

// Add for streaming
?stream=true
```

---

## Minimal Request

```typescript
{
  "input": [
    { "role": "user", "content": "What are top 5 expensive jobs?" }
  ],
  "custom_inputs": {
    "user_id": "user@company.com"
  }
}
```

---

## Full Request (With Memory)

```typescript
{
  "input": [
    { "role": "user", "content": "Show me details for the first one" }
  ],
  "custom_inputs": {
    "user_id": "user@company.com",
    "session_id": "uuid-from-frontend",
    "thread_id": "thread_from_previous_response",
    "genie_conversation_ids": {
      "cost": "conv_from_previous_response"
    },
    "request_id": "new-uuid"
  }
}
```

---

## Response Structure

```typescript
{
  "output": [
    { "content": [{ "text": "Natural language response..." }] }
  ],
  "custom_outputs": {
    // MEMORY STATE - Store these for next request!
    "thread_id": "thread_abc123",
    "genie_conversation_ids": { "cost": "conv_def456" },
    "memory_status": "saved",
    
    // QUERY METADATA
    "domain": "cost",
    "source": "genie",  // or "error"
    
    // VISUALIZATION
    "visualization_hint": {
      "type": "bar_chart",  // or line_chart, pie_chart, table, text
      "x_axis": "Job Name",
      "y_axis": "Total Cost",
      "title": "Top 5 Jobs by Cost"
    },
    "data": [
      { "Job Name": "ETL", "Total Cost": "1250.50" }
    ]
  }
}
```

---

## Extract Response Data

```typescript
// Text response
const text = response.output[0].content[0].text;

// Memory state (store for next query!)
const { thread_id, genie_conversation_ids } = response.custom_outputs;

// Check for errors
const isError = response.custom_outputs.source === 'error';

// Visualization
const hint = response.custom_outputs.visualization_hint;
const data = response.custom_outputs.data;
```

---

## TypeScript Types

```typescript
interface AgentRequest {
  input: Array<{ role: 'user' | 'assistant'; content: string }>;
  custom_inputs?: {
    user_id?: string;
    session_id?: string;
    thread_id?: string | null;
    genie_conversation_ids?: Record<string, string>;
    request_id?: string;
  };
}

interface AgentResponse {
  output: Array<{
    content: Array<{ text: string }>;
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
      label?: string;
      value?: string;
      title?: string;
      reason?: string;
      domain_preferences?: {
        prefer_currency_format?: boolean;
        color_scheme?: string;
        [key: string]: any;
      };
    };
    data?: Array<Record<string, string | number>>;
    error?: string;
  };
}
```

---

## Streaming Implementation

```typescript
// Add ?stream=true to URL
const response = await fetch(`${ENDPOINT_URL}?stream=true`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(request)
});

// Read stream
const reader = response.body!.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      
      // Text chunk
      if (event.type === 'response.output_item.delta') {
        displayTextChunk(event.delta.text);
      }
      
      // Final custom_outputs
      if (event.type === 'response.done') {
        saveMemoryState(event.custom_outputs);
      }
    }
  }
}
```

---

## Memory Pattern

```typescript
// Initialize session
const [sessionId] = useState(() => crypto.randomUUID());
const [threadId, setThreadId] = useState<string | null>(null);
const [genieConvIds, setGenieConvIds] = useState<Record<string, string>>({});

// Include in request
const request = {
  custom_inputs: {
    user_id: 'user@company.com',
    session_id: sessionId,
    thread_id: threadId,
    genie_conversation_ids: genieConvIds
  }
};

// Update from response
const response = await sendQuery(request);
setThreadId(response.custom_outputs.thread_id);
setGenieConvIds(response.custom_outputs.genie_conversation_ids);

// Clear for new conversation
setThreadId(null);
setGenieConvIds({});
```

---

## Visualization Rendering

```typescript
function renderVisualization(hint, data, domain) {
  switch (hint.type) {
    case 'bar_chart':
      return (
        <BarChart data={data}>
          <XAxis dataKey={hint.x_axis} />
          <YAxis />
          <Bar dataKey={hint.y_axis} fill={DOMAIN_COLORS[domain]} />
        </BarChart>
      );
    
    case 'line_chart':
      const yAxes = Array.isArray(hint.y_axis) ? hint.y_axis : [hint.y_axis];
      return (
        <LineChart data={data}>
          <XAxis dataKey={hint.x_axis} />
          <YAxis />
          {yAxes.map((metric, idx) => (
            <Line key={metric} dataKey={metric} stroke={COLORS[idx]} />
          ))}
        </LineChart>
      );
    
    case 'pie_chart':
      return (
        <PieChart>
          <Pie
            data={data}
            dataKey={hint.value}
            nameKey={hint.label}
            cx="50%"
            cy="50%"
          />
        </PieChart>
      );
    
    case 'table':
    default:
      return <DataTable data={data} />;
  }
}
```

---

## Error Handling

```typescript
// Check for errors
if (response.custom_outputs.source === 'error') {
  const error = response.custom_outputs.error || 'Unknown error';
  
  // Permission error
  if (error.includes('permission') || error.includes('authorized')) {
    showError('You need CAN USE permission on the SQL warehouse');
  }
  
  // Rate limit
  else if (error.includes('rate limit') || error.includes('429')) {
    showError('Rate limit reached. Wait 60 seconds.');
    setTimeout(retry, 60000);
  }
  
  // Timeout
  else if (error.includes('timeout')) {
    showError('Query timed out. Try a more specific question.');
  }
  
  // Generic
  else {
    showError('Query failed. Please try again.');
  }
}
```

---

## Rate Limiting (5 queries/minute per domain)

```typescript
class RateLimiter {
  private log: Map<string, number[]> = new Map();
  
  canMakeRequest(domain: string): boolean {
    const now = Date.now();
    const times = this.log.get(domain) || [];
    const recent = times.filter(t => now - t < 60000);
    return recent.length < 5;
  }
  
  recordRequest(domain: string) {
    const times = this.log.get(domain) || [];
    times.push(Date.now());
    this.log.set(domain, times.filter(t => Date.now() - t < 60000));
  }
}
```

---

## Databricks Colors

```typescript
const DOMAIN_COLORS = {
  cost: '#FF3621',       // Lava-600 (red)
  security: '#FF5F46',   // Lava-500 (orange-red)
  performance: '#2272B4', // Blue-600
  reliability: '#00A972', // Green-600
  quality: '#98102A'     // Maroon-600
};

const CHART_COLORS = [
  '#2272B4',  // Blue-600
  '#00A972',  // Green-600
  '#FFAB00',  // Yellow-600
  '#FF3621',  // Lava-600
];
```

---

## Common Queries for Testing

```typescript
// Bar charts
"What are the top 10 most expensive jobs?"
"Show me the slowest queries"
"Which workspaces use the most DBUs?"

// Line charts
"Show cost trend over the last 7 days"
"Display job success rate over time"
"Show cluster utilization trends"

// Pie charts
"Cost breakdown by workspace"
"Distribution of job types"
"Show error types distribution"

// Follow-up questions (requires memory)
First: "What are top 5 expensive jobs?"
Then: "Show me details for the first one"
Then: "How does that compare to last month?"
```

---

## Implementation Checklist

### Phase 1: Basic (1-2 days)
- [ ] Authentication working (user tokens)
- [ ] Basic request/response
- [ ] Display text responses
- [ ] Error handling

### Phase 2: Streaming (1 day)
- [ ] SSE streaming implemented
- [ ] Real-time text display
- [ ] Cancel button

### Phase 3: Memory (1 day)
- [ ] Track thread_id
- [ ] Track genie_conversation_ids
- [ ] Update from responses
- [ ] New conversation button

### Phase 4: Visualization (1-2 days)
- [ ] Install Recharts
- [ ] Bar chart component
- [ ] Line chart component
- [ ] Pie chart component
- [ ] Data table component
- [ ] Chart/table toggle
- [ ] Domain colors applied

---

## Getting Help

- **Detailed Guides**: See [00-README.md](00-README.md)
- **Backend Details**: See [../14-visualization-hints-backend.md](../14-visualization-hints-backend.md)
- **API Issues**: Check response in browser DevTools Network tab
- **Memory Issues**: Check sessionStorage for 'agent_memory' key
- **Chart Issues**: Verify `data` array format matches `hint` fields

---

**Total Implementation Time**: 4-6 days for complete integration

**Priority Order**: Basic → Streaming → Memory → Visualization
