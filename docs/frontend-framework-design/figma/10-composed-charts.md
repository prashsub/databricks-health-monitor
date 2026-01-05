# 10 - Composed Chart Components

## Overview

Create chart container components: ChartCard (various types), ChartLegend, and ChartTooltip. These are placeholders for charts that will be rendered via Recharts/Tremor in code.

**Note:** Figma doesn't render actual charts - we create structured containers that developers will populate with chart libraries.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create chart container components for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users analyzing metrics
- Style: Clean data visualization containers
- Platform: Desktop web
- Note: Actual charts rendered via Recharts/Tremor in code

Objective (this run only):
- Create chart container components (NOT actual charts)
- Create supporting legend and tooltip components
- Use ONLY primitives from previous prompts
- Place in Components/Composed/Charts section

Follow Guidelines.md for design system alignment.

Design system rules:
- REUSE existing primitives (Card, Badge, Button)
- Charts are PLACEHOLDERS (simple lines/shapes)
- Focus on container structure, headers, legends
- Support standard chart sizes (sm/md/lg)

---

## COMPONENT 1: ChartCard

Purpose: Container for various chart types with header, legend, and AI insights

### Specifications:
- Base: Card (default variant)
- Configurable chart area placeholder

### Variants:

**chartType** (property):
- timeseries: Line chart placeholder with x/y axis lines
- bar: Horizontal bar chart placeholder
- donut: Donut/pie chart placeholder (circular)
- heatmap: Grid-based heatmap placeholder
- sparkline: Mini inline chart (no container)
- stacked: Stacked bar chart placeholder

**size** (property):
- sm: 320px × 200px (for grid layouts)
- md: 480px × 280px (default)
- lg: 640px × 360px (full-width)
- xl: 100% width × 480px (hero charts)

**hasHeader** (boolean):
- true: Show header with title, actions
- false: Chart only (for embedding)

**hasLegend** (boolean):
- true: Show legend component
- false: No legend

**hasAIInsight** (boolean):
- true: Show AI insight footer
- false: No insight

### Structure:
```
ChartCard (Card primitive as base)
├── [ChartHeader] (optional, Auto Layout, horizontal, space-between)
│   ├── HeaderLeft (Auto Layout, vertical)
│   │   ├── Title (heading/h3)
│   │   └── Subtitle (body/small, text/secondary)
│   └── HeaderRight (Auto Layout, horizontal)
│       ├── TimeRangeBadge (Badge, "Last 7 days")
│       └── ActionMenu (IconButton, ⋮)
├── ChartArea (Auto Layout, vertical)
│   ├── ChartPlaceholder (flex, based on chartType)
│   │   └── [Placeholder graphics - simple shapes]
│   └── [ChartLegend] (optional)
└── [AIInsightFooter] (optional)
    ├── SparkleIcon (✨, brand/ai-accent)
    └── InsightText (body/small, text/secondary)
```

### ChartPlaceholder by Type:

**timeseries:**
```
┌─────────────────────────────────────┐
│ 100 ─┼                              │
│      │   ╱╲  ╱╲╱╲                   │
│  50 ─┼──╱──╲╱    ╲                 │
│      │╱            ╲___╱╲_         │
│   0 ─┼───────────────────────────── │
│      Jan  Feb  Mar  Apr  May        │
└─────────────────────────────────────┘
```

**bar:**
```
┌─────────────────────────────────────┐
│ Production  ████████████████  85%   │
│ Staging     █████████████     68%   │
│ Development ████████          42%   │
│ Sandbox     ██████            32%   │
└─────────────────────────────────────┘
```

**donut:**
```
┌─────────────────────────────────────┐
│       ┌──────┐                      │
│      ╱   42%  ╲    ● Jobs (42%)    │
│     │         │    ● SQL (33%)     │
│     │  $52K   │    ● DLT (18%)     │
│      ╲       ╱     ● Other (7%)    │
│       └──────┘                      │
└─────────────────────────────────────┘
```

**heatmap:**
```
┌─────────────────────────────────────┐
│     Mon Tue Wed Thu Fri Sat Sun     │
│ 0h  ░░░ ▒▒▒ ░░░ ░░░ ░░░ ░░░ ░░░     │
│ 6h  ▓▓▓ ███ ▓▓▓ ▓▓▓ ▓▓▓ ░░░ ░░░     │
│ 12h ███ ███ ███ ███ ▓▓▓ ▒▒▒ ░░░     │
│ 18h ▓▓▓ ▓▓▓ ▓▓▓ ▓▓▓ ▒▒▒ ░░░ ░░░     │
└─────────────────────────────────────┘
```

**sparkline:**
```
▁▂▃▄▅▆▇█▇▆▅▄▃▂▁ (40px × 20px, inline)
```

### Specifications:
- Chart area aspect ratios: 16:9 (timeseries), 4:3 (bar, donut), 1:1 (heatmap)
- Internal padding: spacing/4 (16px)
- Header-chart gap: spacing/4 (16px)
- Chart-legend gap: spacing/3 (12px)

### Example - Full ChartCard:
```
┌────────────────────────────────────────────────────────────────┐
│ Daily Cost Trend                              Last 7 days   ⋮  │
│ Production workspace spending                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  $60K ─┼                                                       │
│        │        ╱╲                                             │
│  $40K ─┼───────╱──╲─────╱╲────────────────────────────────    │
│        │      ╱    ╲___╱  ╲___________╱╲__                    │
│  $20K ─┼─────╱                            ╲___                 │
│        │                                                        │
│    $0 ─┼──────────────────────────────────────────────────────  │
│        Mon    Tue    Wed    Thu    Fri    Sat    Sun           │
│                                                                 │
│  ● Jobs  ● SQL Warehouse  ● DLT Pipelines  ● Other            │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│ ✨ Peak cost detected on Wednesday - 42% above baseline        │
└────────────────────────────────────────────────────────────────┘
```

---

## COMPONENT 2: ChartLegend

Purpose: Legend for chart color coding

### Specifications:
- Auto Layout: horizontal (wrap) or vertical
- Gap: spacing/3 (12px) between items

### Variants:

**layout** (property):
- horizontal: Items in a row (wraps)
- vertical: Items stacked

**interactive** (boolean):
- true: Items are clickable (toggle series)
- false: Display only

### Structure:
```
ChartLegend (Auto Layout)
├── LegendItem
│   ├── ColorIndicator (12px circle or square)
│   └── Label (body/small, text/secondary)
├── LegendItem
├── LegendItem
└── ...
```

### LegendItem Sub-component:
```
LegendItem (Auto Layout, horizontal, 4px gap)
├── ColorIndicator (12px × 12px, circle or square, colored)
└── Label (body/small, "Jobs ($21K)")
```

### Color Palette for Charts:
```
Series colors (Official Databricks - in order):
- chart/series-1: #2272B4 (Blue-600 - PRIMARY) ✅
- chart/series-2: #1B3139 (Navy-800 - secondary)
- chart/series-3: #059669 (emerald)
- chart/series-4: #F59E0B (amber)
- chart/series-5: #EF4444 (red)
- chart/series-6: #6366F1 (indigo)
```

---

## COMPONENT 3: ChartTooltip

Purpose: Hover tooltip showing data point details

### Specifications:
- Background: background/elevated (white)
- Shadow: shadow/lg
- Border radius: radius/md (8px)
- Max width: 280px

### Variants:

**style** (property):
- default: Standard tooltip with value
- comparison: Shows current vs previous
- multi: Shows multiple series values

### Structure:
```
ChartTooltip (Card-like container)
├── TooltipHeader (optional)
│   └── DateLabel (body/small, text/secondary, "Wed, Jan 15")
├── TooltipContent (Auto Layout, vertical)
│   ├── TooltipRow
│   │   ├── ColorDot (8px, colored)
│   │   ├── Label (body/small, "Jobs")
│   │   └── Value (number/small, "$21.4K")
│   └── TooltipRow...
└── [TooltipFooter] (optional, comparison)
    └── ChangeText (body/small, "vs $18.2K last week (+17%)")
```

### Example - Default:
```
┌─────────────────────┐
│ Wed, Jan 15         │
│ ● Jobs     $21.4K   │
│ ● SQL       $8.2K   │
│ ● DLT       $3.1K   │
│─────────────────────│
│ Total: $32.7K       │
└─────────────────────┘
```

### Example - Comparison:
```
┌─────────────────────────┐
│ Wed, Jan 15             │
│                         │
│ $32.7K                  │
│ vs $28.1K last week     │
│ ↑ +$4.6K (+16%)        │
└─────────────────────────┘
```

---

## COMPONENT 4: ChartAxisLabel

Purpose: Axis labels for charts

### Structure:
```
ChartAxisLabel (Auto Layout, horizontal or vertical)
├── AxisLine (1px, border/default)
├── TickMarks (Auto Layout)
│   ├── Tick ("$0")
│   ├── Tick ("$20K")
│   ├── Tick ("$40K")
│   └── Tick ("$60K")
└── [AxisTitle] (optional, body/small, "Cost (USD)")
```

---

## FIGMA ORGANIZATION:

Create in: 🧱 Components > Composed > Charts

Page layout:
```
┌─────────────────────────────────────────────────────────────────┐
│ Chart Components                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ChartCard - Timeseries (sizes)                                  │
│ ┌─────────────┐ ┌───────────────────┐ ┌─────────────────────────│
│ │ Daily Cost  │ │ Daily Cost Trend  │ │ Daily Cost Trend       ││
│ │ ___╱╲___╱╲_ │ │    ╱╲  ╱╲         │ │     ╱╲  ╱╲            ││
│ └─────────────┘ │___╱  ╲╱  ╲___     │ │____╱  ╲╱  ╲_____     ││
│     (sm)        └───────────────────┘ └─────────────────────────│
│                       (md)                    (lg)              │
│                                                                  │
│ ChartCard - Bar                                                  │
│ ┌───────────────────────────────────────┐                       │
│ │ Cost by Workspace                     │                       │
│ │ Production  █████████████████  85%    │                       │
│ │ Staging     ████████████       68%    │                       │
│ │ Development ████████           42%    │                       │
│ └───────────────────────────────────────┘                       │
│                                                                  │
│ ChartCard - Donut                                                │
│ ┌───────────────────────────────────────┐                       │
│ │ Cost Distribution                     │                       │
│ │      ╭──────╮     ● Jobs (42%)       │                       │
│ │     │ $52K │     ● SQL (33%)         │                       │
│ │      ╰──────╯     ● DLT (18%)        │                       │
│ └───────────────────────────────────────┘                       │
│                                                                  │
│ ChartCard - Heatmap                                              │
│ ┌───────────────────────────────────────┐                       │
│ │ Query Activity Heatmap                │                       │
│ │    Mon Tue Wed Thu Fri Sat Sun        │                       │
│ │ 0h ░░░ ▒▒▒ ░░░ ░░░ ░░░ ░░░ ░░░        │                       │
│ │ 6h ▓▓▓ ███ ▓▓▓ ▓▓▓ ▓▓▓ ░░░ ░░░        │                       │
│ │12h ███ ███ ███ ███ ▓▓▓ ▒▒▒ ░░░        │                       │
│ └───────────────────────────────────────┘                       │
│                                                                  │
│ ChartLegend (horizontal/vertical)                                │
│ ● Jobs  ● SQL  ● DLT  ● Other                                   │
│                                                                  │
│ ChartTooltip (default/comparison)                                │
│ ┌─────────────────────┐                                         │
│ │ Wed, Jan 15         │                                         │
│ │ ● Jobs     $21.4K   │                                         │
│ │ Total: $32.7K       │                                         │
│ └─────────────────────┘                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PRIMITIVES USED:

- Card (base for ChartCard)
- Badge (time range badges)
- Button (action menus)

---

## SIZE REFERENCE TABLE:

| Size | Width | Height | Use Case |
|------|-------|--------|----------|
| sm | 320px | 200px | Grid layouts, 3-4 per row |
| md | 480px | 280px | Default, 2 per row |
| lg | 640px | 360px | Featured charts, 1-2 per row |
| xl | 100% | 480px | Hero charts, full width |
| sparkline | 40-80px | 20-30px | Inline in KPITile |

---

## CHART COLOR TOKENS TO CREATE:

```
chart/series-1: #2272B4 (Blue-600 - PRIMARY) ✅
chart/series-2: #1B3139 (Navy-800 - secondary)
chart/series-3: #059669 (emerald)
chart/series-4: #F59E0B (amber)
chart/series-5: #EF4444 (red)
chart/series-6: #6366F1 (indigo)
chart/series-7: #EC4899 (pink)
chart/series-8: #8ACAFF (Blue-400 - light accent) ✅

chart/axis: text/muted (#6B7280)
chart/grid: border/default (#E5E7EB)
chart/threshold: semantic/warning (#F59E0B)
chart/anomaly: semantic/critical (#DC2626)
```

---

Do NOT:
- Render actual dynamic charts
- Create complex SVG paths
- Add interactivity
- Create screens
- Use hardcoded colors
```

---

## 🎯 Expected Output

### Components Created (4)

| Component | Purpose | Built From |
|-----------|---------|------------|
| ChartCard | Container for charts | Card, Badge, Button |
| ChartLegend | Color legend | Custom |
| ChartTooltip | Hover details | Card-like |
| ChartAxisLabel | Axis formatting | Custom |

### Figma Structure

```
🧱 Components
└── Composed
    └── Charts
        ├── ChartCard (chartType, size, hasHeader, hasLegend)
        ├── ChartLegend (layout, interactive)
        ├── ChartTooltip (style)
        └── ChartAxisLabel
```

---

## ✅ Verification Checklist

- [ ] ChartCard has all 6 chartType variants
- [ ] ChartCard has all 4 size variants
- [ ] ChartLegend horizontal and vertical layouts
- [ ] ChartTooltip default and comparison styles
- [ ] Chart series colors defined as tokens
- [ ] All components use Auto Layout
- [ ] Placeholder graphics are simple (not complex SVGs)

---

**Next:** [11-screen-executive-overview.md](11-screen-executive-overview.md)

