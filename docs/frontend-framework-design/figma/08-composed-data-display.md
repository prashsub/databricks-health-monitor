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
- Create 7 data display components (4 standard + 3 NEW professional components)
- Use ONLY primitives from previous prompts (Card, Badge, Chip, etc.)
- Place in Components/Composed/DataDisplay section

Follow Guidelines.md for design system alignment.

Design system rules:
- REUSE existing primitive components (Card with accent-top variants, Badge, Chip status variant, ProgressBar, etc.)
- Use Auto Layout for all components
- Support real-world data (short/medium/long values)
- Clear visual hierarchy for fast scanning
- NEW: Use Card accent-top and accent-top-sm variants for professional signal and topology components
- NEW: Use Chip status variant with leading dots for professional status indicators

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

Page layout (show all 7 components):
```
┌─────────────────────────────────────────────────────────────────┐
│ Data Display Components (7 total)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ STANDARD COMPONENTS (4)                                          │
│ ───────────────────────                                          │
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
│ ═════════════════════════════════════════════════════════════   │
│                                                                  │
│ NEW PROFESSIONAL COMPONENTS (3)                                  │
│ ───────────────────────────────                                  │
│                                                                  │
│ SignalCard (show severity variants with 4px top borders)        │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │▀▀▀▀ RED 4px border                                          │  │
│ │ 🔴 Cost spike in Production          ● CRITICAL   5m ago   │  │
│ │ 💰 Impact: $12.5K (+42%)    [View Details] [Acknowledge]  │  │
│ └────────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │▀▀▀▀ CORAL 4px border                                        │  │
│ │ ⚡ Job failure spike                  ● HIGH      15m ago   │  │
│ │ ⚡ 12 failed jobs    [View Details] [Investigate]          │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ TopologyNodeCard (show status variants with 3px top borders)    │
│ ┌───────────────────┐ ┌───────────────────┐                    │
│ │▀▀▀ RED 3px border │ │▀▀▀ GREEN 3px      │                    │
│ │ 🏭 SQL WAREHOUSE  │ │ 🚀 SERVERLESS     │                    │
│ │ prod-analytics-wh │ │ serverless-pool   │                    │
│ │ ● ALERT           │ │ ● HEALTHY         │                    │
│ │ 💰 $42.3K today   │ │ 23 jobs running   │                    │
│ │ Fix Alert →       │ │ View Jobs →       │                    │
│ └───────────────────┘ └───────────────────┘                    │
│                                                                  │
│ LayerHeader (Navy background banner)                            │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ GOVERNANCE LAYER                      [Expand Layer ▼]    │  │
│ │ (Navy-700 #143D4A background, White text, Blue-600 link) ✅│  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PRIMITIVES USED:

- Card (default variant: base for KPITile, MetricCard, TrendCard)
- Card (accent-top variant: base for SignalCard - 4px colored top border)
- Card (accent-top-sm variant: base for TopologyNodeCard - 3px colored top border)
- Badge (for severity, trend indicators, "NEW")
- Chip (status variant: professional status chips with leading dots for SignalCard, TopologyNodeCard)
- ProgressBar (for breakdowns in MetricCard)
- StatusIndicator (for KPITile status)
- Button (primary, gray-outline variants for actions in SignalCard)

---

## STATES TO INCLUDE:

For KPITile: default, hover
For AlertRow: default, hover, selected, muted
For MetricCard: default, loading (skeleton), empty
For TrendCard: default, loading
For SignalCard (NEW): default, hover (Blue-600 border)
For TopologyNodeCard (NEW): default, hover (Blue-600 border + shadow)
For LayerHeader (NEW): default only

---

SUMMARY OF COMPONENTS TO CREATE:

**Standard Components (4):**
1. KPITile - Key metric tile
2. MetricCard - Detailed metric with chart
3. AlertRow - Basic alert list item
4. TrendCard - Trend visualization tile

**NEW Professional Components (3):**
5. SignalCard - Professional alert card with 4px colored top border
6. TopologyNodeCard - Service map node with 3px colored top border
7. LayerHeader - Topology section banner (Navy background)

---

Do NOT:
- Create new primitives (use existing Card, Chip, Badge, Button)
- Implement actual charts (just placeholders)
- Use hardcoded colors (use color tokens)
- Create screens
- Add complex animations
- Mix up the card variants (accent-top for SignalCard, accent-top-sm for TopologyNodeCard)
```

---

## 🎯 Expected Output

### Components Created (7)

| Component | Purpose | Built From |
|-----------|---------|------------|
| KPITile | Key metric with trend | Card (default), Badge, StatusIndicator |
| MetricCard | Detailed metric with chart | Card (default), ProgressBar |
| AlertRow | Alert list item (basic) | Badge, Button |
| TrendCard | Trend visualization | Card (default), Badge |
| SignalCard | **NEW** Professional alert card | Card (accent-top), Chip (status), Button |
| TopologyNodeCard | **NEW** Service map node | Card (accent-top-sm), Chip (status) |
| LayerHeader | **NEW** Topology layer banner | Navy background, typography |

### Figma Structure

```
🧱 Components
└── Composed
    └── DataDisplay
        ├── KPITile (size: sm/md/lg, trend: up/down/neutral)
        ├── MetricCard (hasChart, hasBreakdown)
        ├── AlertRow (severity: critical/high/medium/low)
        ├── TrendCard (trendDirection, chartType)
        ├── SignalCard (NEW - severity: critical/high/medium/low)
        ├── TopologyNodeCard (NEW - resourceType, status: healthy/warning/critical)
        └── LayerHeader (NEW - simple banner component)
```


## COMPONENT 5: SignalCard (NEW - Professional Alert Display)

Purpose: Professional card-based alert/signal display with rich context (replaces basic AlertRow for Executive Overview)

### Specifications:
- Base: Card (accent-top variant, md padding 20px)
- Size: Full width × variable height (min 140px)
- Border-top: 4px solid [severity color]

### Variants:

**severity** (property):
- critical: Lava-600 (#FF3621) ✅ top border, red chip
- high: Lava-500 (#FF5F46) ✅ top border, coral chip
- medium: Yellow-600 (#FFAB00) ✅ top border, amber chip
- low: Blue-600 (#2272B4) ✅ top border, blue chip

### Structure:
```
SignalCard (Card accent-top primitive as base)
├── TitleRow (Auto Layout, horizontal, space-between)
│   ├── SignalIcon (20px, colored by domain: 💰 🛡️ ⚡ 📋)
│   ├── SignalTitle (heading/h2, 18px bold, Navy-900 #0B2026) ✅
│   └── Timestamp (body/small, 12px, Navy-500 #618794) ✅
├── MetadataRow (Auto Layout, horizontal, gap 8px)
│   ├── SeverityChip (Chip status variant with leading dot)
│   └── ResourceDetail (body/default, 14px, Navy-700 #143D4A) ✅
├── ImpactRow (Auto Layout, horizontal, gap 24px)
│   ├── PrimaryImpact (Icon + Text, body/emphasis 14px Navy)
│   └── SecondaryImpact (Icon + Text, body/emphasis 14px Navy)
├── ContextSection (Auto Layout, vertical, gap 6px) - expandable
│   ├── CorrelationText (body/small, 12px, Slate)
│   └── WhatChangedText (body/small, 12px, Slate)
└── ActionFooter (Auto Layout, horizontal, space-between)
    ├── ActionButtons (Auto Layout, horizontal, gap 8px)
    │   ├── PrimaryAction (Button primary or destructive, Blue-600 filled) ✅
    │   └── SecondaryAction (Button gray-outline, Navy-900 text) ✅
    └── AssignmentInfo (body/small, 12px, Navy-500) ✅
```

### Specifications:
- Container padding: 20px 24px
- Title-metadata gap: 8px
- Metadata-impact gap: 12px
- Impact-context gap: 12px
- Context-actions gap: 16px
- Signal icon size: 20px
- Severity chip: status variant, md size (28px height)
- Top border: 4px solid [severity color]
- Box-shadow: 0 2px 4px rgba(27,58,75,0.08)
- Hover: Blue-600 border (#2272B4) ✅, shadow increase

### Typography:
- Signal Title: heading/h2 (18px, bold 600, Navy-900 #0B2026) ✅
- Resource Detail: body/default (14px, regular, Navy-700 #143D4A) ✅
- Impact Metrics: body/emphasis (14px, medium, Navy-900 #0B2026) ✅
- Context Text: body/small (12px, regular, Navy-700 #143D4A) ✅
- Timestamp: body/small (12px, regular, Navy-500 #618794) ✅

### Example Content:
```
┌────────────────────────────────────────────────────────────────────┐
│▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│
│ RED 4px top border                                                 │
│                                                                    │
│ 🔴 Cost spike in Production workspace                  5 min ago  │
│                                                                    │
│ ● CRITICAL    prod-sql-warehouse-001 • Query cost, Warehouse scale│
│                                                                    │
│ 💰 Impact: $12.5K over threshold (+42%)     🎯 Affected: 3 jobs  │
│                                                                    │
│ ↳ 2 correlated signals:                                           │
│   • Query cost anomaly (same WH, started 2m earlier)             │
│                                                                    │
│ [View Details →]  [Acknowledge]  [Mute ▼]          John S.       │
└────────────────────────────────────────────────────────────────────┘
```

---

## COMPONENT 6: TopologyNodeCard (NEW - Professional Service Map Nodes)

Purpose: Professional card node for Resource Topology service map

### Specifications:
- Base: Card (accent-top-sm variant, md padding 16px 20px)
- Size: 240-300px width × 160-180px height
- Border-top: 3px solid [status color]

### Variants:

**resourceType** (property):
- catalog: 🏛️ icon, Navy-700 header
- schema: 📊 icon, Blue-600 header
- warehouse: 🏭 icon, status-colored header
- cluster: 🖥️ icon, status-colored header
- serverless: 🚀 icon, status-colored header
- pipeline: 🔄 icon, status-colored header
- workflow: 📅 icon, status-colored header
- model: 🤖 icon, Green header
- vectorsearch: 🔍 icon, Green header
- genie: 🧞 icon, Green header
- dashboard: 📊 icon, status-colored header
- alerts: 🔔 icon, status-colored header

**status** (property):
- healthy: Green-600 (#00A972) ✅ top border
- warning: Yellow-600 (#FFAB00) ✅ top border
- critical: Lava-600 (#FF3621) ✅ top border
- unknown: Navy-500 (#618794) ✅ top border

### Structure:
```
TopologyNodeCard (Card accent-top-sm primitive as base)
├── HeaderRow (Auto Layout, horizontal, gap 8px)
│   ├── ResourceIcon (20px, colored by type)
│   └── ResourceType (label/small, 10px uppercase, Navy-700 #143D4A) ✅
├── ResourceName (heading/h3, 16px semibold, Navy-900 #0B2026) ✅
├── StatusChip (Chip status variant with leading dot, md size)
├── MetricsSection (Auto Layout, vertical, gap 6px)
│   ├── MetricLine (Icon 14px + Text body/small-emphasis 13px Navy)
│   ├── MetricLine
│   ├── MetricLine
│   └── MetricLine (max 4 metrics)
└── ActionLink (body/small-emphasis, 13px medium, Blue-600 #2272B4) ✅
```

### Specifications:
- Container padding: 16px 20px
- Min-width: 240px, Max-width: 300px
- Min-height: 160px
- Header-title gap: 4px
- Title-status gap: 8px
- Status-metrics gap: 12px
- Metrics-action gap: 12px
- Metric lines gap: 6px
- Top border: 3px solid [status color]
- Box-shadow: 0 2px 4px rgba(27,58,75,0.08)
- Hover: Blue-600 border (#2272B4) ✅, shadow 0 4px 12px rgba(34,114,180,0.15)

### Typography:
- Resource Type: label/small (10px, semibold 600, uppercase, Navy-700 #143D4A) ✅
- Resource Name: heading/h3 (16px, semibold 600, Navy-900 #0B2026) ✅
- Status Chip: label/badge (11px, medium 500)
- Metric Text: body/small-emphasis (13px, medium 500, Navy-900 #0B2026) ✅
- Action Link: body/small-emphasis (13px, medium 500, Blue-600 #2272B4) ✅

### Example Content:
```
┌───────────────────────────────┐
│▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│
│ RED 3px top border            │
│                               │
│ 🏭 SQL WAREHOUSE              │
│ prod-analytics-wh             │
│                               │
│ ● ALERT                       │
│                               │
│ 💰 Cost: $42.3K today         │
│ ⚠️ Cost spike: +42%           │
│ ⚡ 847 queries/hr             │
│ 📊 P95: 4.2s (⚠️ 2s)          │
│                               │
│ Fix Alert →                   │
└───────────────────────────────┘
```

---

## COMPONENT 7: LayerHeader (NEW - Topology Layer Banners)

Purpose: Professional layer header for topology service map

### Specifications:
- Container: Auto Layout, horizontal, space-between
- Background: Navy-700 (#143D4A) ✅ (solid)
- Border-radius: 6px
- Padding: 12px 20px
- Full width

### Structure:
```
LayerHeader (Auto Layout, horizontal, space-between)
├── LayerName (label/small, 11px uppercase bold 700, White #FFFFFF) ✅
└── ExpandLink (body/small-emphasis, 13px, Blue-600 #2272B4) ✅
```

### Specifications:
- Text: label/small (11px, bold 700, uppercase, letter-spacing 0.08em)
- Text color: White (#FFFFFF) ✅
- Link color: Blue-600 (#2272B4) ✅
- Background: Navy-700 (#143D4A) ✅
- Padding: 12px 20px
- Border-radius: 6px

### Example Content:
```
┌────────────────────────────────────────────────┐
│ GOVERNANCE LAYER          [Expand Layer ▼]    │
└────────────────────────────────────────────────┘
```

---

## 📋 Final Pre-Submission Checklist

### Component Count:
- [ ] 7 total components created (4 standard + 3 NEW professional)

### Standard Components Quality:
- [ ] KPITile, MetricCard, AlertRow, TrendCard all present
- [ ] All size/severity variants implemented
- [ ] Loading states (skeleton) included
- [ ] Real-world data scenarios handled (short/long values)

### NEW Professional Components Quality:
- [ ] SignalCard uses Card accent-top variant (4px top border)
- [ ] TopologyNodeCard uses Card accent-top-sm variant (3px top border)
- [ ] LayerHeader uses Navy-700 (#143D4A) ✅ background
- [ ] All typography matches spec (18px bold for SignalCard titles, 16px bold for TopologyNodeCard names)
- [ ] Status chips use leading 6px colored dots (Chip status variant)
- [ ] All text is high contrast (Navy-900 #0B2026, Navy-700 #143D4A) ✅
- [ ] Hover states use Blue-600 (#2272B4) ✅ borders
- [ ] Action buttons use correct colors (Blue-600 filled, Gray outline with Navy-900 text)

### Organization:
- [ ] All components in Components > Composed > DataDisplay
- [ ] Variants properly configured
- [ ] Auto Layout applied consistently

---

**Next:** [09-composed-ai.md](09-composed-ai.md)

