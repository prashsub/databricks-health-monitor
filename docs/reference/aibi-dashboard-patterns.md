# Databricks AI/BI Dashboard Pattern Reference

Extracted from 9 production dashboards including Account Usage Dashboard v2 - DAIS, Governance Hub, DBSQL Warehouse Advisor, Jobs System Tables Dashboard, and more.

> **Companion to**: `.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc`

## 1. Dataset Structure

Each dataset has:
- `name`: unique identifier (e.g., `"c93a48f4"` or `"ds_kpi_cost"`)
- `displayName`: human-readable name
- `query` OR `queryLines`: SQL query (string or array of strings)
- `parameters`: (OPTIONAL) array of parameter definitions

## 2. Parameter Types

### A) DATE:RANGE (for date range pickers)

**Query uses:** `:time_range.min` and `:time_range.max`

```json
{
  "displayName": "time_range",
  "keyword": "time_range",
  "dataType": "DATE",
  "complexType": "RANGE",
  "defaultSelection": {
    "range": {
      "dataType": "DATE",
      "min": { "value": "now-90d/d" },
      "max": { "value": "now/d" }
    }
  }
}
```

**CRITICAL:** `complexType: "RANGE"` is required for `.min`/`.max` access!

### B) STRING (for single select filters)

**Query uses:** `:param_workspace`

```json
{
  "displayName": "param_workspace",
  "keyword": "param_workspace",
  "dataType": "STRING",
  "defaultSelection": {
    "values": {
      "dataType": "STRING",
      "values": [{ "value": "<ALL WORKSPACES>" }]
    }
  }
}
```

### C) STRING:MULTI (for multi-select filters)

**Query uses:** `array_contains(:param_workspace, column)`

```json
{
  "displayName": "param_workspace",
  "keyword": "param_workspace",
  "dataType": "STRING",
  "complexType": "MULTI",
  "defaultSelection": {
    "values": {
      "dataType": "STRING",
      "values": [{ "value": "all" }]
    }
  }
}
```

### D) INTEGER (for numeric inputs)

**Query uses:** `LIMIT :param_top_n`

```json
{
  "displayName": "param_top_n",
  "keyword": "param_top_n",
  "dataType": "INTEGER",
  "defaultSelection": {
    "values": {
      "dataType": "INTEGER",
      "values": [{ "value": "10" }]
    }
  }
}
```

### E) DECIMAL (for decimal inputs)

```json
{
  "displayName": "units_to_predict",
  "keyword": "units_to_predict",
  "dataType": "DECIMAL",
  "defaultSelection": {
    "values": {
      "dataType": "DECIMAL",
      "values": [{ "value": "3" }]
    }
  }
}
```

### F) DATE (single date, not range)

```json
{
  "displayName": "contract_start_date",
  "keyword": "contract_start_date",
  "dataType": "DATE",
  "defaultSelection": {
    "values": {
      "dataType": "DATE",
      "values": [{ "value": "2024-01-01T00:00:00.000" }]
    }
  }
}
```

## 3. Widget Types

### A) counter - Single metric display

```json
{
  "spec": {
    "version": 2,
    "widgetType": "counter",
    "encodings": {
      "value": {
        "fieldName": "sum(usage_usd)",
        "format": {
          "type": "number-currency",
          "currencyCode": "USD"
        }
      },
      "target": {
        "fieldName": "time_window_string"
      }
    },
    "frame": {
      "showTitle": true,
      "title": "Total Usage"
    }
  }
}
```

### B) bar/line/area - Charts

```json
{
  "spec": {
    "widgetType": "bar",
    "encodings": {
      "x": {
        "fieldName": "time_key",
        "scale": { "type": "temporal" }
      },
      "y": {
        "fieldName": "sum(usage_usd_dynamic)",
        "scale": { "type": "quantitative" }
      },
      "color": {
        "fieldName": "group_key",
        "scale": { "type": "categorical" }
      }
    }
  }
}
```

### C) table - Data grid

```json
{
  "spec": {
    "widgetType": "table",
    "encodings": {
      "columns": [
        {
          "fieldName": "group_key",
          "title": "Key",
          "type": "string",
          "displayAs": "string",
          "visible": true,
          "order": 0
        }
      ]
    }
  }
}
```

**IMPORTANT:** Use `disaggregated: true` in the query for row display!

### D) filter-single-select - Dropdown

```json
{
  "spec": {
    "widgetType": "filter-single-select",
    "encodings": {
      "fields": [
        { "fieldName": "group_key", "queryName": "..." }
      ]
    },
    "selection": {
      "defaultSelection": {
        "values": { "dataType": "STRING", "values": [{"value": "Product"}] }
      }
    }
  }
}
```

### E) filter-date-range-picker - Date range

```json
{
  "spec": {
    "widgetType": "filter-date-range-picker",
    "encodings": {
      "fields": [
        { "parameterName": "time_range", "queryName": "..." }
      ]
    },
    "selection": {
      "defaultSelection": {
        "range": {
          "dataType": "DATE",
          "min": { "value": "now-90d/d" },
          "max": { "value": "now/d" }
        }
      }
    }
  }
}
```

## 4. Widget-Dataset Binding

Widget queries reference datasets:

```json
{
  "queries": [{
    "name": "main_query",
    "query": {
      "datasetName": "ds_kpi_cost",
      "fields": [
        { "name": "total_cost", "expression": "`total_cost`" }
      ],
      "disaggregated": false
    }
  }]
}
```

- `datasetName` must match the dataset's `name` field
- `disaggregated: true` for tables (show rows), `false` for aggregations
- `expression` uses backticks for column names

## 5. Field Expressions

- Simple column: `` `column_name` ``
- Aggregation: `SUM(\`column_name\`)`
- Alias: `name` can be different from actual column

## 6. Default Date Values

Relative date syntax:
- `"now"` - Current date/time
- `"now-90d/d"` - 90 days ago, rounded to day
- `"now-12M/M"` - 12 months ago, rounded to month
- `"now-1M/M"` - 1 month ago
- `"2024-01-01T00:00:00.000"` - Absolute date

## 7. Key Learnings

1. **Always include `complexType: "RANGE"` for date range parameters** - Without this, `:time_range.min` and `:time_range.max` won't work!

2. **Parameters must have `defaultSelection`** - This ensures queries run even without user interaction.

3. **`keyword` must match the parameter name in SQL** - If SQL uses `:time_range`, keyword must be `"time_range"`.

4. **Global Filters page is optional** - Datasets work independently if they have their own parameters with defaults.

5. **Use `disaggregated: true` for tables** - Otherwise, you won't see individual rows.

## 8. Widget Type Distribution (From 9 Dashboards)

| Widget Type | Count | Notes |
|-------------|-------|-------|
| filter-single-select | 105 | Most common filter |
| bar | 90 | Primary chart type |
| table | 73 | Data display |
| counter | 72 | KPIs |
| line | 16 | Trends |
| filter-multi-select | 16 | Multi-selection |
| filter-date-picker | 12 | Single dates |
| pie | 8 | Composition |
| filter-date-range-picker | 4 | Date ranges |
| heatmap | 3 | Matrix visualization |
| area | 2 | Stacked trends |
| pivot | 1 | Cross-tabulation |

## 9. Common Widget Sizes

| Widget Type | Common Widths | Common Heights |
|-------------|---------------|----------------|
| counter | 1, 2 | 2 |
| bar | 3, 2, 6 | 6, 7, 8 |
| line | 6, 2, 4 | 5, 4, 6 |
| table | 6, 3, 2 | 4, 9, 8 |
| pie | 1, 2, 3 | 4, 8, 7 |
| filter-single-select | 2, 1 | 2 |
| filter-date-range-picker | 1, 2, 3 | 2 |

## 10. Encoding Keys by Widget Type

| Widget | Required Encodings | Optional Encodings |
|--------|-------------------|-------------------|
| counter | `value` | `target` |
| bar | `x`, `y` | `color`, `label` |
| line | `x`, `y` | `color`, `label` |
| pie | `angle`, `color` | `label` |
| table | `columns` | - |
| filter-* | `fields` | - |
| heatmap | `x`, `y`, `color` | `label` |
| pivot | `rows`, `columns`, `cell` | - |

## References

### Analyzed Dashboards
1. **Account Usage Dashboard v2 - DAIS** - 28 datasets, 70 widgets
2. **Governance Hub System Dashboard** - 30 datasets, 47 widgets  
3. **Altria Monitoring Dashboard Enhanced** - 11 datasets, 13 widgets
4. **Azure Serverless Jobs Cost Observability** - 13 datasets, 23 widgets
5. **DBR Upgrade Migration** - 20 datasets, 20 widgets
6. **DBSQL Warehouse Advisor** - 19 datasets, 122 widgets
7. **Workflow Advisor Dashboard** - 3 datasets, 61 widgets
8. **Jobs System Tables Dashboard** - 22 datasets, 33 widgets
9. **LakeFlow System Tables Dashboard** - 35 datasets, 75 widgets

### File Locations
- Reference dashboards: `context/dashboards/`
- Cursor rule: `.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc`


---

## 🎯 CRITICAL UPDATE: Global Filters Page Type (Learned Jan 3, 2025)

**The "Global Filters" pane in Databricks AI/BI is NOT a regular page - it uses a special `PAGE_TYPE_GLOBAL_FILTERS`!**

### ❌ WRONG Approach (What I Was Doing)

```json
{
  "pages": [
    {
      "displayName": "Global Filters",
      "pageType": "PAGE_TYPE_CANVAS",  // ❌ Creates a TAB, not a filter pane!
      "layout": [/* filter widgets */]
    }
  ]
}
```

This creates a regular page tab labeled "Global Filters" - NOT the built-in collapsible filter pane.

### ✅ CORRECT Approach (From Gold Standard)

```json
{
  "pages": [
    {
      "displayName": "Global Filters",
      "pageType": "PAGE_TYPE_GLOBAL_FILTERS",  // ✅ Creates the filter PANE!
      "layout": [
        {
          "widget": {
            "name": "filter_time_range",
            "queries": [
              // ONE query per dataset that needs filtering
              {
                "name": "param_ds1_time_range",
                "query": {
                  "datasetName": "ds_dataset_1",
                  "parameters": [{"name": "time_range", "keyword": "time_range"}]
                }
              },
              {
                "name": "param_ds2_time_range", 
                "query": {
                  "datasetName": "ds_dataset_2",
                  "parameters": [{"name": "time_range", "keyword": "time_range"}]
                }
              }
              // ... repeat for ALL 35+ datasets
            ],
            "spec": {
              "widgetType": "filter-date-range-picker",
              "encodings": {
                "fields": [
                  {"parameterName": "time_range", "queryName": "param_ds1_time_range"},
                  {"parameterName": "time_range", "queryName": "param_ds2_time_range"}
                  // ... one field per query
                ]
              }
            }
          }
        }
      ]
    },
    {
      "displayName": "Overview",
      "pageType": "PAGE_TYPE_CANVAS",  // Regular pages use PAGE_TYPE_CANVAS
      "layout": [/* ... */]
    }
  ]
}
```

### Key Differences

| Aspect | WRONG (PAGE_TYPE_CANVAS) | CORRECT (PAGE_TYPE_GLOBAL_FILTERS) |
|--------|--------------------------|-------------------------------------|
| UI Location | Creates a page TAB | Creates collapsible PANE on left |
| Visibility | Shows as regular page | Shows as expandable filter panel |
| Filter Binding | Widget binds to ONE dataset | Widget binds to ALL datasets |
| User Experience | Confusing - filters on separate tab | Intuitive - filters always accessible |

### Checklist for Global Filters

- [ ] Global Filters page uses `pageType: "PAGE_TYPE_GLOBAL_FILTERS"`
- [ ] Filter widget has ONE query per dataset with matching parameter
- [ ] Filter widget `encodings.fields` has ONE entry per query
- [ ] Each dataset defines its own `parameters[]` with `defaultSelection`
- [ ] Parameter keyword matches across all datasets (e.g., `time_range`)
- [ ] Global Filters page is FIRST in `pages[]` array
