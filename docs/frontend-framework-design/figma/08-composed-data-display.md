# 08 - Composed Data Display Components

## Overview

Create data display components: KPITile, MetricCard, AlertRow, and TrendCard. These are the core components for showing metrics, alerts, and trends on dashboards.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create data display components for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users scanning metrics quickly
- Style: Data-dense, scannable, enterprise
- Platform: Desktop web

Objective (this run only):
- Create 4 data display components
- Use ONLY primitives from previous prompts (Card, Badge, StatusIndicator, etc.)
- Place in Components/Composed/DataDisplay section

Follow Guidelines.md for design system alignment.

Design system rules:
- REUSE existing primitive components (Card, Badge, ProgressBar, etc.)
- Use Auto Layout for all components
- Support real-world data (short/medium/long values)
- Clear visual hierarchy for fast scanning

---

## COMPONENT 1: KPITile

Purpose: Display key metrics with trend indication (used in dashboard headers)

### Specifications:
- Base: Card (default variant, md padding)
- Size: 200-280px width × 120-160px height
- Hover: Card hover state (elevation/2)

### Variants:

**size** (property):
- sm: 200px × 120px, smaller typography
- md: 240px × 140px (default)
- lg: 280px × 160px, larger typography

**trend** (property):
- up: green arrow up, semantic/success color
- down: red arrow down, semantic/critical color
- neutral: gray dash, text/muted color
- none: no trend indicator

**hasSparkline** (boolean):
- true: show mini sparkline chart (60px × 30px)
- false: no sparkline

### Structure:
```
KPITile (Card primitive as base)
├── Header (Auto Layout, horizontal, space-between)
│   ├── Label (body/small, text/secondary)
│   └── [StatusIndicator] (optional)
├── ValueRow (Auto Layout, horizontal)
│   ├── Value (number/large or number/medium based on size)
│   └── TrendIndicator (Auto Layout, horizontal)
│       ├── TrendArrow (12px icon, colored)
│       └── TrendPercent (body/small, colored)
├── [Sparkline] (optional, 60px × 30px placeholder)
└── [CompareText] (optional, body/small, text/muted, "vs $45K last week")
```

### Specifications:
- Value font: number/large (32px) for md size
- Trend percent: body/small (12px), colored by direction
- Label-value gap: spacing/2 (8px)
- Value-sparkline gap: spacing/3 (12px)
- Internal padding: spacing/4 (16px)

### Example Content:
```
┌────────────────────────────────┐
│ Total Cost           ● Active  │
│                                │
│ $52.8K              ↑ 17%     │
│ ▁▂▃▄▅▆▇ (sparkline)           │
│                                │
│ vs $45.2K last week           │
└────────────────────────────────┘
```

---

## COMPONENT 2: MetricCard

Purpose: Detailed metric with context (chart + breakdown)

### Specifications:
- Base: Card (default variant, md padding)
- Size: min 320px width, flexible height

### Variants:

**hasChart** (boolean):
- true: includes chart placeholder area (200px height)
- false: metrics only

**hasBreakdown** (boolean):
- true: shows breakdown list below main value
- false: main value only

### Structure:
```
MetricCard (Card primitive as base)
├── CardHeader (Auto Layout, horizontal, space-between)
│   ├── Title (heading/h3)
│   └── ActionMenu (icon button, ⋮)
├── CardContent (Auto Layout, vertical)
│   ├── [ChartArea] (optional, 200px height placeholder)
│   ├── MetricRow (Auto Layout, horizontal, space-between)
│   │   ├── MetricLabel (body/default, text/secondary)
│   │   └── MetricValue (number/default, text/primary)
│   └── [BreakdownList] (optional)
│       ├── BreakdownItem (label + value + bar)
│       ├── BreakdownItem
│       └── BreakdownItem
└── [CardFooter] (optional, AI insight or link)
```

### BreakdownItem Sub-component:
```
BreakdownItem (Auto Layout, horizontal)
├── Label (body/small, text/secondary, 120px width)
├── ProgressBar (sm size, flex-grow)
└── Value (number/small, 60px width, right-aligned)
```

### Specifications:
- Header-content gap: spacing/4 (16px)
- Content item gap: spacing/3 (12px)
- Breakdown item gap: spacing/2 (8px)

---

## COMPONENT 3: AlertRow

Purpose: Single alert item in a list

### Specifications:
- Height: 64-72px
- Width: 100% (fills container)
- Hover: background/elevated, show actions

### Variants:

**severity** (property):
- critical: 4px left border severity/critical, severity/critical-light background tint
- high: 4px left border severity/high
- medium: 4px left border severity/medium
- low: 4px left border severity/low

**state** (property):
- default: normal
- hover: background/elevated, show actions
- selected: brand/primary-light background
- muted: 50% opacity (snoozed/acknowledged)

**isNew** (boolean):
- true: show "NEW" badge
- false: no badge

### Structure:
```
AlertRow (Auto Layout, horizontal)
├── SeverityIndicator (4px width, full height, colored)
├── AlertContent (Auto Layout, vertical, flex-grow)
│   ├── TitleRow (Auto Layout, horizontal)
│   │   ├── AlertTitle (body/emphasis, text/primary, truncate)
│   │   └── [Badge "NEW"] (optional)
│   └── MetaRow (Auto Layout, horizontal)
│       ├── AlertType (Badge, severity variant)
│       ├── Resource (body/small, text/secondary)
│       └── Timestamp (body/small, text/muted)
├── AlertValue (Auto Layout, vertical, right-aligned)
│   ├── Value (number/default, colored by severity)
│   └── Threshold (body/small, text/muted, "Threshold: $10K")
└── AlertActions (Auto Layout, horizontal, visible on hover)
    ├── IconButton (View)
    ├── IconButton (Snooze)
    └── IconButton (More)
```

### Specifications:
- Row padding: spacing/4 (16px) horizontal
- Content gap: spacing/3 (12px)
- Title max-width: 400px with truncation
- Actions gap: spacing/2 (8px)
- Border bottom: 1px border/default

### Example Content:
```
┌────────────────────────────────────────────────────────────────────┐
│█│ Cost spike detected in Production workspace      NEW            │
│█│ 🏷️ Cost Alert  • workspace-prod-001 • 5 min ago    $42.5K ↑42% │
│█│                                                  Threshold: $30K│
└────────────────────────────────────────────────────────────────────┘
```

---

## COMPONENT 4: TrendCard

Purpose: Show metric trend over time (mini dashboard tile)

### Specifications:
- Base: Card (default variant, md padding)
- Size: 300-360px width × 180-240px height

### Variants:

**trendDirection** (property):
- positive: semantic/success color, upward indication
- negative: semantic/critical color, downward indication
- neutral: text/muted color

**chartType** (property):
- line: line chart placeholder
- bar: bar chart placeholder
- area: area chart placeholder

### Structure:
```
TrendCard (Card primitive as base)
├── CardHeader (Auto Layout, horizontal, space-between)
│   ├── TitleGroup (Auto Layout, vertical)
│   │   ├── Title (heading/h3)
│   │   └── Subtitle (body/small, text/secondary)
│   └── TrendBadge (Badge with trend value, e.g., "+17%")
├── ChartArea (placeholder, 120px height)
│   └── [Chart placeholder lines/bars]
├── StatsRow (Auto Layout, horizontal, space-between)
│   ├── StatItem (label + value, e.g., "Avg: $1.2K")
│   ├── StatItem (e.g., "Peak: $2.5K")
│   └── StatItem (e.g., "Min: $0.8K")
└── TimeRange (body/small, text/muted, "Last 30 days")
```

### StatItem Sub-component:
```
StatItem (Auto Layout, vertical)
├── Label (caption/default, text/muted)
└── Value (number/small, text/primary)
```

### Specifications:
- Chart area background: background/elevated (subtle)
- Stats gap: spacing/4 (16px)
- Stat label-value gap: spacing/1 (4px)

---

## FIGMA ORGANIZATION:

Create in: 🧱 Components > Composed > DataDisplay

Page layout:
```
┌─────────────────────────────────────────────────────────────────┐
│ Data Display Components                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ KPITile (show size variants)                                    │
│ ┌────────────┐ ┌──────────────┐ ┌────────────────┐             │
│ │ Total Cost │ │ Total Cost   │ │ Total Cost     │             │
│ │ $52.8K ↑17%│ │ $52.8K  ↑17% │ │ $52.8K    ↑17% │             │
│ └────────────┘ └──────────────┘ └────────────────┘             │
│   (sm)           (md)              (lg)                         │
│                                                                  │
│ MetricCard                                                       │
│ ┌─────────────────────────────────────┐                         │
│ │ Cost Breakdown                    ⋮ │                         │
│ │ ┌─────────────────────────────────┐ │                         │
│ │ │ [Chart placeholder]             │ │                         │
│ │ └─────────────────────────────────┘ │                         │
│ │ Jobs      ████████████ 60%  $6.2K  │                         │
│ │ SQL       █████████    40%  $4.1K  │                         │
│ └─────────────────────────────────────┘                         │
│                                                                  │
│ AlertRow (show severity variants)                                │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │█│ Critical: Cost spike in Production        $42K  Thresh:$30K│  │
│ └────────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │▒│ High: Job failure rate increasing         98%  Target:99% │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ TrendCard                                                        │
│ ┌───────────────────────────────────┐                           │
│ │ Daily Cost Trend          +17%    │                           │
│ │ Last 30 days                      │                           │
│ │ ┌───────────────────────────────┐ │                           │
│ │ │ ╱╲  ╱╲                        │ │                           │
│ │ │╱  ╲╱  ╲_____╱╲               │ │                           │
│ │ └───────────────────────────────┘ │                           │
│ │ Avg: $1.2K  Peak: $2.5K  Min: $0.8│                           │
│ └───────────────────────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PRIMITIVES USED:

- Card (base for KPITile, MetricCard, TrendCard)
- Badge (for severity, trend indicators, "NEW")
- ProgressBar (for breakdowns in MetricCard)
- StatusIndicator (for KPITile status)
- Button (icon buttons for actions)

---

## STATES TO INCLUDE:

For KPITile: default, hover
For AlertRow: default, hover, selected, muted
For MetricCard: default, loading (skeleton), empty
For TrendCard: default, loading

---

Do NOT:
- Create new primitives
- Implement actual charts (just placeholders)
- Use hardcoded colors
- Create screens
- Add complex animations
```

---

## 🎯 Expected Output

### Components Created (4)

| Component | Purpose | Built From |
|-----------|---------|------------|
| KPITile | Key metric with trend | Card, Badge, StatusIndicator |
| MetricCard | Detailed metric with chart | Card, ProgressBar |
| AlertRow | Alert list item | Badge, Button |
| TrendCard | Trend visualization | Card, Badge |

### Figma Structure

```
🧱 Components
└── Composed
    └── DataDisplay
        ├── KPITile (size: sm/md/lg, trend: up/down/neutral)
        ├── MetricCard (hasChart, hasBreakdown)
        ├── AlertRow (severity: critical/high/medium/low)
        └── TrendCard (trendDirection, chartType)
```

---

## ✅ Verification Checklist

- [ ] All 4 components created
- [ ] KPITile has 3 size variants
- [ ] AlertRow has 4 severity variants
- [ ] Components use existing primitives
- [ ] Auto Layout applied to all
- [ ] Hover states implemented
- [ ] Loading states (skeleton) included
- [ ] Real-world data scenarios handled (short/long values)

---

**Next:** [09-composed-ai.md](09-composed-ai.md)

