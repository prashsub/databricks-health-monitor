# 14B - Visualization Hints: Frontend Implementation

> ⚠️ **DEPRECATED**: This guide has been reorganized and updated.
> 
> **👉 NEW LOCATION**: See `frontend-guides/06-visualization-rendering.md`
> 
> **Why Moved**: Part of reorganized frontend guide series (01-06) with complete, verified implementations.
> 
> **Status Changed**: From PLANNED to COMPLETE with working code examples.
> 
> **All Frontend Guides**: See `frontend-guides/00-README.md`

---

**This file is kept for backward compatibility but will not be updated.**

---

## Overview (Original Content Below)

The frontend receives agent responses with visualization hints and tabular data. It renders the appropriate chart type (bar, line, pie) or falls back to a table view. Users can toggle between chart and table views.

## Architecture

```
┌──────────────┐       ┌─────────────────┐       ┌──────────────┐
│ Orchestrator │──────▶│ Frontend React  │──────▶│ Chart Library│
│   Response   │       │   Component     │       │  (Recharts)  │
└──────────────┘       └─────────────────┘       └──────────────┘
       │                       │                         │
       │ JSON Response         │ Parse Hint              │ Render Chart
       │ with hints + data     │ Select Chart Type       │ or Table
```

### Data Flow

1. Frontend receives agent response via API
2. Extract `custom_outputs.visualization_hints` and `custom_outputs.data`
3. Determine chart type from hint
4. Render appropriate visualization component
5. Provide toggle for user to switch to table view

---

## Response Format (From Backend)

The frontend will receive this structure:

```typescript
interface AgentResponse {
  messages: Array<{
    role: "assistant" | "user";
    content: string;  // Natural language response with markdown table
  }>;
  custom_outputs: {
    thread_id: string;
    domains: string[];
    confidence: number;
    sources: string[];
    // ✨ NEW: Visualization hints
    visualization_hints?: Record<string, VisualizationHint>;
    data?: Record<string, TableRow[]>;
  };
}

interface VisualizationHint {
  type: "bar_chart" | "line_chart" | "pie_chart" | "table" | "text" | "error";
  x_axis?: string;
  y_axis?: string | string[];
  label?: string;
  value?: string;
  title?: string;
  reason?: string;
  // Domain-specific preferences
  prefer_currency_format?: boolean;
  color_scheme?: "red_amber_green" | "sequential";
  highlight_outliers?: boolean;
  highlight_critical?: boolean;
  show_thresholds?: boolean;
  show_percentages?: boolean;
}

interface TableRow {
  [columnName: string]: string | number;
}
```

---

## Implementation Tasks

### Task 1: Install Chart Library

**Install Recharts** (React charting library):

```bash
npm install recharts
# or
yarn add recharts
```

**Why Recharts?**
- Built for React
- Responsive and accessible
- Supports bar, line, pie, and area charts
- Easy customization with Databricks colors

---

### Task 2: Create Visualization Component

**File**: `src/frontend/components/AgentResponseDisplay.tsx` (NEW)

```typescript
import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie,
  XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

// Databricks brand colors
const DATABRICKS_COLORS = {
  primary: '#FF3621',      // Lava-600
  blue: '#2272B4',         // Blue-600
  green: '#00A972',        // Green-600
  yellow: '#FFAB00',       // Yellow-600
  navy: '#0B2026',         // Navy-900
};

const CHART_COLORS = [
  DATABRICKS_COLORS.blue,
  DATABRICKS_COLORS.green,
  DATABRICKS_COLORS.yellow,
  DATABRICKS_COLORS.primary,
];

interface VisualizationHint {
  type: 'bar_chart' | 'line_chart' | 'pie_chart' | 'table' | 'text' | 'error';
  x_axis?: string;
  y_axis?: string | string[];
  label?: string;
  value?: string;
  title?: string;
  reason?: string;
  prefer_currency_format?: boolean;
  color_scheme?: string;
}

interface AgentResponse {
  messages: Array<{
    role: string;
    content: string;
  }>;
  custom_outputs: {
    visualization_hints?: Record<string, VisualizationHint>;
    data?: Record<string, any[]>;
    [key: string]: any;
  };
}

interface Props {
  response: AgentResponse;
}

export function AgentResponseDisplay({ response }: Props) {
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  
  const { visualization_hints = {}, data = {} } = response.custom_outputs;
  
  // Get first domain's hint and data
  const domain = Object.keys(visualization_hints)[0];
  const hint = visualization_hints[domain];
  const tableData = data[domain];
  
  // If no hint or data, just show text response
  if (!hint || !tableData || hint.type === 'text' || hint.type === 'error') {
    return (
      <div className="agent-response">
        <div className="response-text prose">
          {response.messages[0].content}
        </div>
      </div>
    );
  }
  
  const renderVisualization = () => {
    // Force table view if user toggled or hint suggests table
    if (viewMode === 'table' || hint.type === 'table') {
      return <DataTable data={tableData} hint={hint} />;
    }
    
    switch (hint.type) {
      case 'bar_chart':
        return <BarChartViz data={tableData} hint={hint} />;
      
      case 'line_chart':
        return <LineChartViz data={tableData} hint={hint} />;
      
      case 'pie_chart':
        return <PieChartViz data={tableData} hint={hint} />;
      
      default:
        return <DataTable data={tableData} hint={hint} />;
    }
  };
  
  return (
    <div className="agent-response">
      {/* Natural language response */}
      <div className="response-text prose mb-4">
        {response.messages[0].content}
      </div>
      
      {/* Visualization */}
      <div className="visualization-container bg-white rounded-lg shadow p-4">
        {renderVisualization()}
        
        {/* Toggle button */}
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => setViewMode(prev => prev === 'chart' ? 'table' : 'chart')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            {viewMode === 'chart' ? '📊 Show Table' : '📈 Show Chart'}
          </button>
        </div>
        
        {/* Hint reason */}
        {hint.reason && (
          <p className="mt-2 text-sm text-gray-600 italic">
            💡 {hint.reason}
          </p>
        )}
      </div>
    </div>
  );
}

// Bar Chart Component
function BarChartViz({ data, hint }: { data: any[]; hint: VisualizationHint }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <XAxis dataKey={hint.x_axis} />
          <YAxis />
          <Tooltip formatter={(value) => 
            hint.prefer_currency_format ? `$${value}` : value
          } />
          <Bar dataKey={hint.y_axis as string} fill={DATABRICKS_COLORS.primary} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Line Chart Component
function LineChartViz({ data, hint }: { data: any[]; hint: VisualizationHint }) {
  const yAxisList = Array.isArray(hint.y_axis) ? hint.y_axis : [hint.y_axis];
  
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis dataKey={hint.x_axis} />
          <YAxis />
          <Tooltip />
          <Legend />
          {yAxisList.map((metric, idx) => (
            <Line
              key={metric}
              type="monotone"
              dataKey={metric}
              stroke={CHART_COLORS[idx % CHART_COLORS.length]}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Pie Chart Component
function PieChartViz({ data, hint }: { data: any[]; hint: VisualizationHint }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey={hint.value}
            nameKey={hint.label}
            cx="50%"
            cy="50%"
            outerRadius={100}
            label
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// Data Table Component
function DataTable({ data, hint }: { data: any[]; hint: VisualizationHint }) {
  if (!data || data.length === 0) {
    return <p className="text-gray-500">No data available</p>;
  }
  
  const columns = Object.keys(data[0]);
  
  return (
    <div>
      {hint.title && <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map(col => (
                <th
                  key={col}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {columns.map(col => (
                  <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {hint.prefer_currency_format && typeof row[col] === 'number'
                      ? `$${row[col].toFixed(2)}`
                      : row[col]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

### Task 3: Integrate with Chat Interface

**File**: `src/frontend/components/ChatInterface.tsx` (MODIFY)

**Use the new component in your chat interface**:

```typescript
import { AgentResponseDisplay } from './AgentResponseDisplay';

function ChatInterface() {
  const [messages, setMessages] = useState<AgentResponse[]>([]);
  
  const handleSendMessage = async (userMessage: string) => {
    // Send to agent API
    const response = await fetch('/api/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: userMessage }]
      })
    });
    
    const agentResponse = await response.json();
    setMessages(prev => [...prev, agentResponse]);
  };
  
  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <AgentResponseDisplay key={idx} response={msg} />
        ))}
      </div>
      
      <input 
        type="text" 
        placeholder="Ask a question..."
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSendMessage(e.currentTarget.value);
            e.currentTarget.value = '';
          }
        }}
      />
    </div>
  );
}
```

---

### Task 4: Add Styling

**File**: `src/frontend/styles/visualizations.css` (NEW)

```css
/* Agent Response Display */
.agent-response {
  margin-bottom: 1.5rem;
}

.response-text {
  padding: 1rem;
  background-color: #F9F7F4; /* Databricks Oat-light */
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.visualization-container {
  border: 1px solid #DCE0E2; /* Databricks Gray-lines */
  border-radius: 0.5rem;
  padding: 1rem;
  background-color: white;
}

.toggle-view-btn {
  padding: 0.5rem 1rem;
  background-color: #2272B4; /* Databricks Blue-600 */
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.toggle-view-btn:hover {
  background-color: #0E538B; /* Databricks Blue-700 */
}

/* Data Table */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background-color: #143D4A; /* Databricks Navy-700 */
  color: white;
}

.data-table th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.data-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #DCE0E2;
}

.data-table tbody tr:hover {
  background-color: #F9F7F4; /* Databricks Oat-light */
}

/* Chart styling */
.recharts-tooltip-wrapper {
  border: 1px solid #DCE0E2;
  background-color: white;
  padding: 0.5rem;
  border-radius: 0.25rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

---

### Task 5: Handle Edge Cases

**Add error handling and loading states**:

```typescript
// In AgentResponseDisplay.tsx

export function AgentResponseDisplay({ response }: Props) {
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  const [error, setError] = useState<string | null>(null);
  
  const { visualization_hints = {}, data = {} } = response.custom_outputs;
  
  // Get first domain's hint and data
  const domain = Object.keys(visualization_hints)[0];
  const hint = visualization_hints[domain];
  const tableData = data[domain];
  
  // Error state
  if (hint?.type === 'error') {
    return (
      <div className="agent-response">
        <div className="response-text prose">
          {response.messages[0].content}
        </div>
        <div className="bg-red-50 border border-red-200 rounded p-4 mt-4">
          <p className="text-red-700">
            ⚠️ Unable to generate visualization. Data source error.
          </p>
        </div>
      </div>
    );
  }
  
  // No visualization data
  if (!hint || !tableData || hint.type === 'text') {
    return (
      <div className="agent-response">
        <div className="response-text prose">
          {response.messages[0].content}
        </div>
      </div>
    );
  }
  
  // Empty data
  if (tableData.length === 0) {
    return (
      <div className="agent-response">
        <div className="response-text prose">
          {response.messages[0].content}
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded p-4 mt-4">
          <p className="text-gray-600">
            ℹ️ No data available to visualize.
          </p>
        </div>
      </div>
    );
  }
  
  // Render visualization (existing logic)
  // ...
}
```

---

## Testing

### Manual Testing Checklist

Test with these queries to verify all chart types:

**Bar Chart Tests:**
- [ ] "What are the top 10 most expensive jobs?"
- [ ] "Show me the slowest queries"
- [ ] "Which workspaces use the most DBUs?"

**Line Chart Tests:**
- [ ] "Show cost trend over the last 7 days"
- [ ] "Show job success rate over time"
- [ ] "Display cluster utilization trends"

**Pie Chart Tests:**
- [ ] "Show cost breakdown by workspace"
- [ ] "Display distribution of job types"
- [ ] "Show error types distribution"

**Table Fallback Tests:**
- [ ] "Show all failed login attempts today"
- [ ] "List tables with data quality issues"
- [ ] Any query returning >20 rows

### Interaction Tests
- [ ] Toggle between chart and table views works
- [ ] Charts are responsive (resize window)
- [ ] Hover tooltips show correct values
- [ ] Currency formatting appears when `prefer_currency_format: true`
- [ ] Colors use Databricks brand palette

### Edge Case Tests
- [ ] Response with no visualization hint (shows text only)
- [ ] Response with empty data array (shows message)
- [ ] Response with error hint (shows error message)
- [ ] Malformed data (graceful fallback)

---

## Validation Checklist

After implementation:

### Component Structure
- [ ] `AgentResponseDisplay.tsx` component created
- [ ] Recharts library installed and imported
- [ ] All chart types implemented (Bar, Line, Pie, Table)
- [ ] Databricks colors applied

### Functionality
- [ ] Parses `custom_outputs.visualization_hints`
- [ ] Parses `custom_outputs.data`
- [ ] Renders appropriate chart based on hint type
- [ ] Toggle button switches between chart and table
- [ ] Currency formatting applied when specified
- [ ] Responsive design works on mobile/desktop

### Error Handling
- [ ] Gracefully handles missing hints
- [ ] Gracefully handles missing data
- [ ] Shows error message when hint.type === "error"
- [ ] Shows "no data" message when data is empty

### Styling
- [ ] Uses Databricks brand colors
- [ ] Follows Databricks design system
- [ ] Charts are properly sized and responsive
- [ ] Hover states work correctly

---

## Example Queries and Expected Results

| Query | Chart Type | Data Columns | Visual |
|-------|-----------|--------------|--------|
| "Top 10 expensive jobs" | Bar Chart | job_name, total_cost | Horizontal bars, red |
| "Cost trend last 7 days" | Line Chart | date, total_cost | Time series, blue line |
| "Cost breakdown by workspace" | Pie Chart | workspace, cost | Donut chart, multi-color |
| "Failed login attempts today" | Table | timestamp, user, ip_address | Data grid |

---

## Implementation Estimate

| Task | Time | Complexity |
|------|------|------------|
| Task 1: Install Recharts | 5 min | Trivial |
| Task 2: Create visualization component | 3-4 hours | Medium |
| Task 3: Integrate with chat interface | 1 hour | Low |
| Task 4: Add styling | 1 hour | Low |
| Task 5: Error handling | 1 hour | Medium |
| Testing | 2 hours | Medium |
| **Total** | **8-10 hours** | **Medium** |

---

## References

### Internal
- [Backend Implementation](14-visualization-hints-backend.md)
- [Databricks Design System](.cursor/rules/front-end/databricks-design-system.mdc)

### External
- [Recharts Documentation](https://recharts.org/en-US/)
- [Databricks UI Kit](https://databricks.com/brand-assets)
- [React Chart Libraries Comparison](https://openbase.com/categories/js/best-react-chart-libraries)

---

## Future Enhancements

### v2.0 Features
- **Export to dashboard**: Save visualization to AI/BI dashboard
- **Custom color themes**: User-selected color schemes
- **Animation effects**: Smooth transitions between chart types
- **Drill-down**: Click chart elements to filter/explore
- **Multiple visualizations**: Show multiple domains side-by-side

### Accessibility
- Keyboard navigation for chart toggle
- Screen reader support for data tables
- High contrast mode for charts
- ARIA labels for all interactive elements

