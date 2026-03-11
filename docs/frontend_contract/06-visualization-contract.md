# Visualization Contract

> Extracted from `_suggest_visualization()` at `src/agents/setup/log_agent_model.py` line 1537 and `_get_domain_preferences()` at line 1674.

## Overview

Every response from the agent includes a `visualization_hint` in `custom_outputs`. This tells the frontend what chart type to render and how to configure it. The hint is a **suggestion** -- the frontend decides the final rendering.

The agent also returns parsed `data` (an array of row objects, or `null`) which should be passed directly to the chart renderer.

---

## 7 Visualization Hint Types

### Type 1: `line_chart`

**Triggered by:** Time series data (datetime column + numeric columns), or queries with "over time", "trend" keywords.

```json
{
  "type": "line_chart",
  "x_axis": "usage_date",
  "y_axis": ["total_cost", "total_dbus"],
  "title": "Total Cost, Total Dbus Over Time",
  "reason": "Time series data with numeric metrics",
  "row_count": 30,
  "domain_preferences": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `x_axis` | `string` | Column name for the x-axis (always a datetime column) |
| `y_axis` | `string[]` | Up to 3 numeric columns for y-axis lines |
| `title` | `string` | Auto-generated chart title |
| `reason` | `string` | Why this type was chosen |
| `row_count` | `number` | Number of data rows |
| `domain_preferences` | `object` | Domain-specific rendering preferences (see below) |

### Type 2: `bar_chart`

**Triggered by:** Categorical + numeric data with Top N keywords ("top", "highest", "most", "expensive", "worst") or small comparison datasets (<=15 rows).

```json
{
  "type": "bar_chart",
  "x_axis": "workspace_name",
  "y_axis": "total_cost",
  "title": "Top 10 Workspace Name by Total Cost",
  "reason": "Top N comparison query",
  "row_count": 10,
  "domain_preferences": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `x_axis` | `string` | Categorical column for x-axis |
| `y_axis` | `string` | Single numeric column for y-axis |
| `title` | `string` | Auto-generated chart title |
| `reason` | `string` | `"Top N comparison query"` or `"Comparison across categories"` |
| `row_count` | `number` | Number of data rows |
| `domain_preferences` | `object` | Domain-specific rendering preferences |

### Type 3: `pie_chart`

**Triggered by:** Categorical + numeric data with distribution keywords ("breakdown", "distribution", "percentage", "share", "split") and <=10 rows.

```json
{
  "type": "pie_chart",
  "label": "sku_name",
  "value": "total_cost",
  "title": "Distribution of Total Cost",
  "reason": "Distribution/breakdown query",
  "row_count": 5,
  "domain_preferences": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `label` | `string` | Categorical column for slice labels |
| `value` | `string` | Numeric column for slice values |
| `title` | `string` | Auto-generated chart title |
| `reason` | `string` | `"Distribution/breakdown query"` |
| `row_count` | `number` | Number of data rows |
| `domain_preferences` | `object` | Domain-specific rendering preferences |

### Type 4: `table`

**Triggered by:** Complex or large data (>15 rows or many columns) that doesn't match other patterns.

```json
{
  "type": "table",
  "columns": ["job_name", "workspace_name", "avg_duration_seconds", "success_rate", "total_runs"],
  "reason": "Complex data (50 rows, 5 columns) - table view recommended",
  "row_count": 50,
  "domain_preferences": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `columns` | `string[]` | Column names in order |
| `reason` | `string` | Explains why table was chosen |
| `row_count` | `number` | Number of data rows |
| `domain_preferences` | `object` | Domain-specific rendering preferences |

### Type 5: `text`

**Triggered by:** No tabular data in the response, or visualization hint generation failed (non-fatal).

```json
{
  "type": "text",
  "reason": "Response contains no tabular data",
  "domain_preferences": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `reason` | `string` | Why no chart is shown |
| `domain_preferences` | `object` | Domain-specific rendering preferences |

### Type 6: `multi_domain`

**Triggered by:** Cross-domain queries that span multiple Genie Spaces.

```json
{
  "type": "multi_domain",
  "domains_analyzed": ["cost", "reliability"],
  "reason": "Cross-domain analysis combining multiple data sources"
}
```

| Field | Type | Description |
|---|---|---|
| `domains_analyzed` | `string[]` | List of domains included in the analysis |
| `reason` | `string` | Always `"Cross-domain analysis combining multiple data sources"` |

For `multi_domain`, the `data` field in `custom_outputs` is an **object** keyed by domain (not an array):

```json
{
  "data": {
    "cost": [{ "usage_date": "2026-03-10", "total_cost": 5000 }],
    "reliability": [{ "job_name": "etl_main", "success_rate": 0.95 }]
  }
}
```

### Type 7: `error`

**Triggered by:** Genie query failure or Genie Space not configured.

```json
{
  "type": "error",
  "reason": "Query failed"
}
```

or

```json
{
  "type": "error",
  "reason": "Genie Space not configured"
}
```

| Field | Type | Description |
|---|---|---|
| `reason` | `string` | `"Query failed"` or `"Genie Space not configured"` |

When type is `error`, `data` in `custom_outputs` is always `null`.

---

## 6 Domain Preference Configurations

Each visualization hint includes `domain_preferences` -- a dict of domain-specific rendering guidance. These are extracted from `_get_domain_preferences()` at line 1674.

### `cost`

```json
{
  "prefer_currency_format": true,
  "color_scheme": "red_amber_green",
  "default_sort": "descending",
  "highlight_threshold": "high values",
  "suggested_formats": { "currency": "USD", "decimals": 2 }
}
```

### `performance`

```json
{
  "highlight_outliers": true,
  "color_scheme": "sequential",
  "default_sort": "descending",
  "suggested_formats": { "duration": "seconds", "percentage": true }
}
```

### `security`

```json
{
  "highlight_critical": true,
  "color_scheme": "red_amber_green",
  "default_sort": "severity",
  "severity_levels": ["critical", "high", "medium", "low"]
}
```

### `reliability`

```json
{
  "show_thresholds": true,
  "color_scheme": "red_amber_green",
  "default_sort": "descending",
  "suggested_formats": { "rate": "percentage", "count": true }
}
```

### `quality`

```json
{
  "show_percentages": true,
  "color_scheme": "red_amber_green",
  "default_sort": "quality_score",
  "suggested_formats": { "score": "percentage" }
}
```

### `unified` (default/fallback)

```json
{
  "color_scheme": "categorical",
  "default_sort": "relevance",
  "multi_domain": true
}
```

If the domain is not recognized, the fallback is:

```json
{
  "color_scheme": "default",
  "default_sort": "ascending"
}
```

---

## Data Array Format

The `data` field in `custom_outputs` is the parsed tabular data from the Genie response:

- **Single domain**: `Array<Record<string, any>>` -- array of row objects.
- **Cross domain**: `Record<string, Array<Record<string, any>>>` -- object keyed by domain name, each value is an array of row objects.
- **No data / error**: `null`.

Example (single domain):

```json
{
  "data": [
    { "workspace_name": "prod-analytics", "total_cost": 45000.50, "total_dbus": 12500 },
    { "workspace_name": "prod-ml", "total_cost": 32000.75, "total_dbus": 8900 }
  ]
}
```

Column types are inferred from the Genie response. The agent classifies columns into three categories for hint generation:

- **datetime**: Matches patterns like `YYYY-MM-DD`, `MM/DD/YYYY`, ISO datetime.
- **numeric**: After stripping `$` and `,`, parses as `float`.
- **categorical**: Everything else.

---

## Rendering Decision Flowchart

```
visualization_hint.type
├── "error"      → Show error message, no chart
├── "text"       → Show text response only, no chart
├── "multi_domain" → Show tabbed or side-by-side views per domain
│   └── For each domain in data: render individually
├── "line_chart" → Render line chart with x_axis (datetime) and y_axis (metrics)
├── "bar_chart"  → Render bar chart with x_axis (category) and y_axis (value)
├── "pie_chart"  → Render pie chart with label (category) and value (numeric)
└── "table"      → Render sortable data table with columns
```

For all chart types, check `domain_preferences` for formatting guidance (currency symbols, percentage formatting, severity color coding, etc).
