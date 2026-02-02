# Frontend Guide 06: Visualization Rendering

> **Purpose**: Render intelligent charts based on agent visualization hints
> 
> **Audience**: Frontend developers implementing data visualization
> 
> **Time to Implement**: 4-6 hours

---

## Overview

The agent analyzes query results and suggests the best chart type:

| Chart Type | When Suggested | Example Query |
|---|---|---|
| **Bar Chart** | Top N, comparisons | "Top 5 expensive jobs" |
| **Line Chart** | Time series, trends | "Cost trend over last 7 days" |
| **Pie Chart** | Distributions, breakdowns | "Cost breakdown by workspace" |
| **Table** | Complex data, many columns | "Show all job details" |
| **Text** | No tabular data | "What is Databricks?" |

**Your responsibility**: Render the appropriate visualization based on the hint.

---

## Setup

### Install Chart Library

```bash
npm install recharts
# or
yarn add recharts
```

**Why Recharts?**
- ✅ Built for React
- ✅ Responsive and accessible
- ✅ Supports all chart types we need
- ✅ Easy to customize with Databricks colors

---

## Visualization Hint Structure

### What You Receive

```typescript
interface VisualizationHint {
  // Chart type
  type: 'bar_chart' | 'line_chart' | 'pie_chart' | 'table' | 'text' | 'error';
  
  // Chart configuration (if type is bar/line/pie)
  x_axis?: string;           // Column name for X-axis
  y_axis?: string | string[]; // Column name(s) for Y-axis
  label?: string;            // Column name for pie chart labels
  value?: string;            // Column name for pie chart values
  title?: string;            // Chart title
  columns?: string[];        // Column list (for tables)
  
  // Metadata
  reason?: string;           // Why this chart type was chosen
  row_count?: number;        // Number of data rows
  
  // Domain-specific styling
  domain_preferences?: {
    prefer_currency_format?: boolean;
    color_scheme?: 'red_amber_green' | 'sequential' | 'categorical';
    default_sort?: string;
    highlight_outliers?: boolean;
    highlight_critical?: boolean;
    show_thresholds?: boolean;
    show_percentages?: boolean;
  };
}

// Accompanying data
interface TableRow {
  [columnName: string]: string | number;
}
```

### Example Hints

**Bar Chart**:
```json
{
  "type": "bar_chart",
  "x_axis": "Job Name",
  "y_axis": "Total Cost",
  "title": "Top 5 Jobs by Cost",
  "reason": "Top N comparison query",
  "row_count": 5,
  "domain_preferences": {
    "prefer_currency_format": true,
    "color_scheme": "red_amber_green"
  }
}
```

**Line Chart**:
```json
{
  "type": "line_chart",
  "x_axis": "Date",
  "y_axis": ["Total Cost", "Serverless Cost"],
  "title": "Cost Trend Over Time",
  "reason": "Time series data"
}
```

**Pie Chart**:
```json
{
  "type": "pie_chart",
  "label": "Workspace",
  "value": "Cost",
  "title": "Cost Distribution",
  "reason": "Breakdown query"
}
```

---

## Implementation

### Main Visualization Component

```typescript
import { useState } from 'react';
import { BarChartViz, LineChartViz, PieChartViz, DataTable } from './charts';

interface Props {
  hint: VisualizationHint;
  data: TableRow[];
  domain: string;
}

export function AgentVisualization({ hint, data, domain }: Props) {
  const [viewMode, setViewMode] = useState<'chart' | 'table'>(
    hint.type === 'table' ? 'table' : 'chart'
  );
  
  // No visualization needed
  if (!hint || !data || hint.type === 'text' || hint.type === 'error') {
    return null;
  }
  
  // Empty data
  if (data.length === 0) {
    return (
      <div className="bg-gray-50 border rounded p-4 text-center text-gray-600">
        ℹ️ No data to visualize
      </div>
    );
  }
  
  return (
    <div className="visualization-container bg-white border rounded-lg p-4 mt-4">
      {/* Render based on view mode */}
      {viewMode === 'table' || hint.type === 'table' ? (
        <DataTable data={data} hint={hint} />
      ) : (
        <>
          {hint.type === 'bar_chart' && <BarChartViz data={data} hint={hint} domain={domain} />}
          {hint.type === 'line_chart' && <LineChartViz data={data} hint={hint} domain={domain} />}
          {hint.type === 'pie_chart' && <PieChartViz data={data} hint={hint} domain={domain} />}
        </>
      )}
      
      {/* Toggle button (if not text/error) */}
      {hint.type !== 'text' && hint.type !== 'error' && (
        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={() => setViewMode(prev => prev === 'chart' ? 'table' : 'chart')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
          >
            {viewMode === 'chart' ? '📊 Show Table' : '📈 Show Chart'}
          </button>
        </div>
      )}
      
      {/* Hint reason (optional) */}
      {hint.reason && (
        <p className="mt-3 text-xs text-gray-500 italic">
          💡 {hint.reason}
        </p>
      )}
    </div>
  );
}
```

---

## Chart Components

### Databricks Colors

```typescript
// Databricks brand colors
const DATABRICKS_COLORS = {
  primary: '#FF3621',     // Lava-600 (red)
  blue: '#2272B4',        // Blue-600
  green: '#00A972',       // Green-600
  yellow: '#FFAB00',      // Yellow-600
  navy: '#0B2026',        // Navy-900
  gray: '#5A6F77',        // Gray-text
};

const CHART_COLORS = [
  DATABRICKS_COLORS.blue,
  DATABRICKS_COLORS.green,
  DATABRICKS_COLORS.yellow,
  DATABRICKS_COLORS.primary,
];

// Domain-specific colors
const DOMAIN_COLORS = {
  cost: DATABRICKS_COLORS.primary,      // Red for cost
  security: '#FF5F46',                   // Lava-500 for security
  performance: DATABRICKS_COLORS.blue,  // Blue for performance
  reliability: DATABRICKS_COLORS.green, // Green for reliability
  quality: '#98102A',                    // Maroon for quality
  unified: DATABRICKS_COLORS.navy       // Navy for unified
};
```

### Bar Chart Component

```typescript
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface BarChartProps {
  data: TableRow[];
  hint: VisualizationHint;
  domain: string;
}

export function BarChartViz({ data, hint, domain }: BarChartProps) {
  const prefs = hint.domain_preferences || {};
  
  // Format values (currency, percentage, etc.)
  const formatValue = (value: string | number) => {
    const num = typeof value === 'string' 
      ? parseFloat(value.replace(/[$,]/g, ''))
      : value;
    
    if (isNaN(num)) return value;
    
    if (prefs.prefer_currency_format) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
      }).format(num);
    }
    
    if (prefs.show_percentages) {
      return `${num.toFixed(1)}%`;
    }
    
    return num.toLocaleString();
  };
  
  return (
    <div className="bar-chart">
      <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#DCE0E2" />
          <XAxis 
            dataKey={hint.x_axis} 
            angle={-45}
            textAnchor="end"
            height={100}
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            tickFormatter={formatValue}
            style={{ fontSize: '12px' }}
          />
          <Tooltip 
            formatter={formatValue}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #DCE0E2',
              borderRadius: '4px'
            }}
          />
          <Legend />
          <Bar 
            dataKey={hint.y_axis as string} 
            fill={DOMAIN_COLORS[domain] || DATABRICKS_COLORS.blue}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Line Chart Component

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function LineChartViz({ data, hint, domain }: LineChartProps) {
  const yAxisList = Array.isArray(hint.y_axis) ? hint.y_axis : [hint.y_axis];
  const prefs = hint.domain_preferences || {};
  
  const formatValue = (value: string | number) => {
    const num = typeof value === 'string' 
      ? parseFloat(value.replace(/[$,]/g, ''))
      : value;
    
    if (isNaN(num)) return value;
    
    if (prefs.prefer_currency_format) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
      }).format(num);
    }
    
    return num.toLocaleString();
  };
  
  return (
    <div className="line-chart">
      <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>
      
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#DCE0E2" />
          <XAxis 
            dataKey={hint.x_axis}
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            tickFormatter={formatValue}
            style={{ fontSize: '12px' }}
          />
          <Tooltip formatter={formatValue} />
          <Legend />
          {yAxisList.map((metric, idx) => (
            <Line
              key={metric}
              type="monotone"
              dataKey={metric}
              stroke={CHART_COLORS[idx % CHART_COLORS.length]}
              strokeWidth={2}
              dot={{ fill: CHART_COLORS[idx % CHART_COLORS.length], r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Pie Chart Component

```typescript
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function PieChartViz({ data, hint, domain }: PieChartProps) {
  const prefs = hint.domain_preferences || {};
  
  const formatValue = (value: string | number) => {
    const num = typeof value === 'string' 
      ? parseFloat(value.replace(/[$,]/g, ''))
      : value;
    
    if (isNaN(num)) return value;
    
    if (prefs.prefer_currency_format) {
      return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    
    return num.toLocaleString();
  };
  
  // Custom label to show percentage
  const renderLabel = (entry: any) => {
    const total = data.reduce((sum, item) => {
      const val = parseFloat(String(item[hint.value!]).replace(/[$,]/g, ''));
      return sum + (isNaN(val) ? 0 : val);
    }, 0);
    
    const value = parseFloat(String(entry[hint.value!]).replace(/[$,]/g, ''));
    const percentage = ((value / total) * 100).toFixed(1);
    
    return `${entry[hint.label!]} (${percentage}%)`;
  };
  
  return (
    <div className="pie-chart">
      <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>
      
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={data}
            dataKey={hint.value}
            nameKey={hint.label}
            cx="50%"
            cy="50%"
            outerRadius={120}
            label={renderLabel}
            labelLine={{ stroke: '#5A6F77', strokeWidth: 1 }}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={CHART_COLORS[index % CHART_COLORS.length]} 
              />
            ))}
          </Pie>
          <Tooltip 
            formatter={formatValue}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #DCE0E2',
              borderRadius: '4px'
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Data Table Component

```typescript
export function DataTable({ data, hint }: { data: TableRow[]; hint: VisualizationHint }) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No data available
      </div>
    );
  }
  
  const columns = Object.keys(data[0]);
  const prefs = hint.domain_preferences || {};
  
  const formatValue = (value: string | number, columnName: string) => {
    // Try to detect if this column contains currency
    const isCurrency = 
      prefs.prefer_currency_format &&
      (columnName.toLowerCase().includes('cost') ||
       columnName.toLowerCase().includes('price') ||
       columnName.toLowerCase().includes('revenue'));
    
    if (typeof value === 'number' || !isNaN(parseFloat(String(value).replace(/[$,]/g, '')))) {
      const num = typeof value === 'number' 
        ? value 
        : parseFloat(String(value).replace(/[$,]/g, ''));
      
      if (isCurrency) {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(num);
      }
      
      return num.toLocaleString();
    }
    
    return value;
  };
  
  return (
    <div className="data-table overflow-x-auto">
      {hint.title && <h3 className="text-lg font-semibold mb-4">{hint.title}</h3>}
      
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-900">
          <tr>
            {columns.map(col => (
              <th
                key={col}
                className="px-6 py-3 text-left text-xs font-semibold text-white uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50 transition">
              {columns.map(col => (
                <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatValue(row[col], col)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      {data.length > 20 && (
        <p className="mt-2 text-xs text-gray-500 text-right">
          Showing {data.length} rows
        </p>
      )}
    </div>
  );
}
```

---

## Integration with Chat

### Message Display with Visualization

```typescript
interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const customOutputs = message.customOutputs;
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-4xl rounded-lg p-4 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white border border-gray-200'
        }`}
      >
        {/* Natural language response */}
        <div className="prose max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        
        {/* Visualization (if data present) */}
        {!isUser && customOutputs?.data && customOutputs?.visualization_hint && (
          <AgentVisualization
            hint={customOutputs.visualization_hint}
            data={customOutputs.data}
            domain={customOutputs.domain}
          />
        )}
        
        {/* Metadata */}
        {!isUser && customOutputs && (
          <div className="mt-3 pt-3 border-t border-gray-200 flex items-center gap-3 text-xs text-gray-500">
            <span>🏷️ {customOutputs.domain}</span>
            {customOutputs.memory_status === 'saved' && (
              <span>💾 Saved to memory</span>
            )}
            <span>⏱️ {message.timestamp.toLocaleTimeString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## Domain-Specific Styling

### Apply Domain Colors

```typescript
function getChartColor(domain: string, hint: VisualizationHint): string {
  // Use domain-specific color
  return DOMAIN_COLORS[domain] || DATABRICKS_COLORS.blue;
}

function getColorScheme(hint: VisualizationHint): string[] {
  const scheme = hint.domain_preferences?.color_scheme;
  
  if (scheme === 'red_amber_green') {
    return ['#FF3621', '#FFAB00', '#00A972'];  // Critical → Warning → Good
  }
  
  if (scheme === 'sequential') {
    return ['#2272B4', '#0E538B', '#0B2026'];  // Light → Dark blue
  }
  
  // Default: categorical
  return CHART_COLORS;
}
```

### Apply Formatting Preferences

```typescript
function formatWithPreferences(
  value: string | number,
  prefs: DomainPreferences
): string {
  const num = typeof value === 'string'
    ? parseFloat(value.replace(/[$,]/g, ''))
    : value;
  
  if (isNaN(num)) return String(value);
  
  // Currency
  if (prefs.prefer_currency_format) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(num);
  }
  
  // Percentage
  if (prefs.show_percentages) {
    return `${num.toFixed(1)}%`;
  }
  
  // Number with commas
  return num.toLocaleString();
}
```

---

## Advanced Features

### Export Chart as Image

```typescript
import html2canvas from 'html2canvas';

async function exportChartAsImage(chartRef: React.RefObject<HTMLDivElement>) {
  if (!chartRef.current) return;
  
  const canvas = await html2canvas(chartRef.current);
  const image = canvas.toDataURL('image/png');
  
  // Download
  const link = document.createElement('a');
  link.download = `chart-${Date.now()}.png`;
  link.href = image;
  link.click();
}

// Usage
export function BarChartViz({ data, hint, domain }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  
  return (
    <div ref={chartRef}>
      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        {/* ... */}
      </ResponsiveContainer>
      
      {/* Export button */}
      <button
        onClick={() => exportChartAsImage(chartRef)}
        className="mt-2 text-sm text-blue-600 hover:text-blue-800"
      >
        📥 Export as Image
      </button>
    </div>
  );
}
```

### Highlight Outliers

```typescript
function highlightOutliers(data: TableRow[], yAxis: string): TableRow[] {
  if (!yAxis) return data;
  
  // Calculate mean and stddev
  const values = data.map(row => {
    const val = String(row[yAxis]).replace(/[$,]/g, '');
    return parseFloat(val) || 0;
  });
  
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const stddev = Math.sqrt(
    values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
  );
  
  // Mark outliers (> 2 standard deviations)
  return data.map(row => {
    const val = parseFloat(String(row[yAxis]).replace(/[$,]/g, '')) || 0;
    const isOutlier = Math.abs(val - mean) > 2 * stddev;
    
    return { ...row, _isOutlier: isOutlier };
  });
}

// In BarChart component
<Bar dataKey={hint.y_axis as string}>
  {data.map((entry, index) => (
    <Cell
      key={`cell-${index}`}
      fill={entry._isOutlier ? '#FF3621' : DOMAIN_COLORS[domain]}
    />
  ))}
</Bar>
```

---

## Testing Visualizations

### Manual Test Queries

**Bar Chart**:
- [ ] "What are the top 10 most expensive jobs?"
- [ ] "Show me the slowest queries"
- [ ] "Which workspaces use the most DBUs?"

**Line Chart**:
- [ ] "Show cost trend over the last 7 days"
- [ ] "Display job success rate over time"
- [ ] "Show cluster utilization trends"

**Pie Chart**:
- [ ] "Cost breakdown by workspace"
- [ ] "Distribution of job types"
- [ ] "Show error types distribution"

**Table**:
- [ ] "Show all failed jobs today"
- [ ] "List tables with quality issues"

### Interaction Tests

- [ ] Toggle between chart and table works
- [ ] Charts resize with window
- [ ] Hover tooltips show correct values
- [ ] Currency formatting appears correctly
- [ ] Colors match Databricks brand
- [ ] Export to image works (if implemented)

---

## Accessibility

### Keyboard Navigation

```typescript
<button
  onClick={toggleView}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleView();
    }
  }}
  aria-label={`Switch to ${viewMode === 'chart' ? 'table' : 'chart'} view`}
>
  {viewMode === 'chart' ? 'Show Table' : 'Show Chart'}
</button>
```

### Screen Reader Support

```typescript
<div
  role="img"
  aria-label={`${hint.title}. ${hint.reason}. ${data.length} data points.`}
>
  <ResponsiveContainer width="100%" height={400}>
    {/* Chart */}
  </ResponsiveContainer>
</div>

{/* Provide table alternative */}
<details className="mt-2">
  <summary className="text-sm text-blue-600 cursor-pointer">
    View data table (screen reader accessible)
  </summary>
  <DataTable data={data} hint={hint} />
</details>
```

---

## Complete Example Component

```typescript
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AgentVisualization } from './AgentVisualization';

interface AgentMessageProps {
  message: Message;
}

export function AgentMessage({ message }: AgentMessageProps) {
  const { content, customOutputs } = message;
  
  // Error response
  if (customOutputs?.source === 'error') {
    return (
      <div className="agent-message bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">❌</span>
          <div className="flex-1">
            <h3 className="font-semibold text-red-800 mb-1">Query Failed</h3>
            <ReactMarkdown>{content}</ReactMarkdown>
            {customOutputs.error && (
              <p className="text-sm text-red-600 mt-2">
                {customOutputs.error}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }
  
  // Success response
  return (
    <div className="agent-message bg-white border border-gray-200 rounded-lg p-4">
      {/* Natural language response */}
      <div className="prose max-w-none mb-4">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
      
      {/* Visualization (if data present) */}
      {customOutputs?.data && customOutputs?.visualization_hint && (
        <AgentVisualization
          hint={customOutputs.visualization_hint}
          data={customOutputs.data}
          domain={customOutputs.domain}
        />
      )}
      
      {/* Metadata footer */}
      <div className="mt-4 pt-3 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3">
          <span className="px-2 py-1 bg-gray-100 rounded">
            🏷️ {customOutputs?.domain || 'unknown'}
          </span>
          {customOutputs?.memory_status === 'saved' && (
            <span className="text-green-600">
              ✓ Saved to memory
            </span>
          )}
        </div>
        <span>
          ⏱️ {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
```

---

## Styling Guide

### Databricks Brand Colors

```css
/* Custom CSS for Databricks styling */
.visualization-container {
  background: white;
  border: 1px solid #DCE0E2;  /* Gray-lines */
  border-radius: 8px;
  padding: 1rem;
}

.chart-title {
  color: #0B2026;  /* Navy-900 */
  font-weight: 600;
  font-size: 1.125rem;
}

.chart-axis-label {
  color: #5A6F77;  /* Gray-text */
  font-size: 0.75rem;
}

.toggle-button {
  background-color: #2272B4;  /* Blue-600 */
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
}

.toggle-button:hover {
  background-color: #0E538B;  /* Blue-700 */
}

/* Data table */
.data-table thead {
  background-color: #143D4A;  /* Navy-700 */
  color: white;
}

.data-table tbody tr:hover {
  background-color: #F9F7F4;  /* Oat-light */
}
```

---

## Performance Tips

### Lazy Load Charts

```typescript
import { lazy, Suspense } from 'react';

const BarChartViz = lazy(() => import('./charts/BarChart'));
const LineChartViz = lazy(() => import('./charts/LineChart'));
const PieChartViz = lazy(() => import('./charts/PieChart'));

export function AgentVisualization({ hint, data, domain }: Props) {
  return (
    <Suspense fallback={<ChartLoadingSkeleton />}>
      {hint.type === 'bar_chart' && <BarChartViz {...props} />}
      {hint.type === 'line_chart' && <LineChartViz {...props} />}
      {hint.type === 'pie_chart' && <PieChartViz {...props} />}
    </Suspense>
  );
}

function ChartLoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
      <div className="h-80 bg-gray-100 rounded" />
    </div>
  );
}
```

### Memoize Chart Data

```typescript
import { useMemo } from 'react';

export function BarChartViz({ data, hint, domain }: Props) {
  // Only recalculate when data changes
  const chartData = useMemo(() => {
    return data.map(row => ({
      ...row,
      _formatted: formatValue(row[hint.y_axis!], hint.domain_preferences)
    }));
  }, [data, hint]);
  
  return (
    <BarChart data={chartData}>
      {/* ... */}
    </BarChart>
  );
}
```

---

## Checklist: Visualization Implementation

### Setup
- [ ] Recharts installed
- [ ] Databricks colors configured
- [ ] Chart components created (Bar, Line, Pie, Table)

### Functionality
- [ ] Parses `visualization_hint` from response
- [ ] Parses `data` from response
- [ ] Renders appropriate chart based on `hint.type`
- [ ] Toggle button switches between chart and table
- [ ] Currency formatting applied when specified
- [ ] Domain-specific colors applied

### UI/UX
- [ ] Charts are responsive (resize with window)
- [ ] Hover tooltips show formatted values
- [ ] Chart titles display correctly
- [ ] Loading states for lazy-loaded charts
- [ ] Graceful fallback for missing data
- [ ] Error states display helpful messages

### Accessibility
- [ ] Keyboard navigation works
- [ ] ARIA labels on interactive elements
- [ ] Screen reader can access data table
- [ ] High contrast mode compatible

---

## Quick Reference

### Essential Pattern

```typescript
// 1. Extract from response
const { visualization_hint, data } = response.custom_outputs;

// 2. Render based on hint type
switch (hint.type) {
  case 'bar_chart':
    return <BarChart data={data} hint={hint} />;
  case 'line_chart':
    return <LineChart data={data} hint={hint} />;
  case 'pie_chart':
    return <PieChart data={data} hint={hint} />;
  case 'table':
    return <DataTable data={data} hint={hint} />;
  default:
    return <DataTable data={data} hint={hint} />;
}
```

### Chart Type Detection

| Query Pattern | Suggested Chart |
|---|---|
| "top N", "most expensive" | Bar Chart |
| "trend", "over time", "daily" | Line Chart |
| "breakdown", "distribution" | Pie Chart |
| Complex data (many columns) | Table |

---

**Previous Guide**: [05 - Memory Integration](05-memory-integration.md)

**You've completed all guides!** 🎉

**Next Steps**: 
- Review [00-README.md](00-README.md) for the complete checklist
- Check [../14-visualization-hints-backend.md](../14-visualization-hints-backend.md) for backend details
