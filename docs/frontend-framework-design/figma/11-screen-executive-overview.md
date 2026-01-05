# 11 - Screen: Executive Overview (Super Enhanced)

## Overview

Create the main dashboard home page - a world-class command center on par with Datadog, Grafana, and New Relic. This is the nerve center where platform engineers start their day.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create a world-class Executive Overview screen for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Screen: Main command center / home dashboard
- Users: Platform engineers, SREs, FinOps, data engineering leads
- Mental model: "What needs my attention RIGHT NOW?"
- Inspiration: Datadog home, Grafana dashboards, New Relic summary
- Platform: Desktop web (1440px primary width)

Quality bar:
- Must feel as polished as Datadog, Grafana, New Relic
- Dense but scannable - every pixel has purpose
- Real-time feel with live indicators
- Action-oriented - every metric leads somewhere

Objective (this run only):
- Create 1 complete screen using ONLY existing components
- Make it feel ALIVE with status indicators
- NO new components
- Place in 📄 Screens section

Follow Guidelines.md for design system alignment.

---

## DATABRICKS PRIMARY ICONS (Official Brand Assets)

Use official Databricks icons from `context/branding/primary_icons/`:

**Domain Health Icons (24px):**
- Cost Domain → "Cost Management" icon
- Reliability Domain → "Performance" icon  
- Performance Domain → "Photon" icon
- Security Domain → "Governance" icon
- Quality Domain → "Data Quality 1" icon

**Primary Metrics Icons (32px):**
- Health Score → "Observable Metrics" icon
- Cost Today → "Cost" icon
- Active Alerts → "Incident Investigation" icon
- SLA Status → "Performance" icon

**Action Icons (20px):**
- Fix Critical Issues → "Deploy" icon
- Optimize Now → "Automation" icon
- View Details → Lucide "ArrowRight" (implementation)
- Help → "Help" icon

**Resource Topology Icons (24px):**
- Bronze Layer → "Unstructured Bronze" icon
- Silver Layer → "Semi Structured Silver" icon  
- Gold Layer → "Structured Gold" icon
- Unity Catalog → "Unity Catalog" icon
- Databricks Workspace → "Databricks Workspace" icon

**Icon Colors (Semantic):**
- Domain icons: Navy-900 (#0B2026) ✅
- Success metrics: Green-600 (#00A972) ✅
- Warning indicators: Yellow-600 (#FFAB00) ✅
- Critical alerts: Lava-600 (#FF3621) ✅
- Interactive actions: Blue-600 (#2272B4) ✅

---

## SCREEN SPECIFICATIONS:

### Canvas Size:
- Width: 1440px
- Height: Variable (scroll, ~1600px for full experience)
- Background: background/default (#FAFAFA)

### Layout Structure:
```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ SIDEBAR │                              MAIN CONTENT AREA                                   │
│  64px   │  ┌──────────────────────────────────────────────────────────────────────────────┐│
│         │  │ COMMAND BAR (sticky, 56px)                                                   ││
│         │  │ ⌘K Search... │ 🌐 Production ▼ │ 📅 Last 24h ▼ │ ⟳ Live │ 🔔 3 │ 👤      ││
│         │  ├──────────────────────────────────────────────────────────────────────────────┤│
│         │  │                                                                              ││
│         │  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│         │  │ │ AI COMMAND CENTER - Proactive Alert Banner                             │  ││
│         │  │ │ "🔴 3 issues need attention • $4.2K savings available • 2 SLOs at risk"│  ││
│         │  │ └────────────────────────────────────────────────────────────────────────┘  ││
│         │  │                                                                              ││
│         │  │ HERO METRICS (4 large KPIs with real-time updates)                          ││
│         │  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            ││
│         │  │ │ Health Score│ │ Active Spend│ │ Job Success │ │ P95 Latency │            ││
│         │  │ │    87/100   │ │  $52.8K ⚡  │ │   98.2%     │ │   1.24s     │            ││
│         │  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            ││
│         │  │                                                                              ││
│         │  │ DOMAIN HEALTH MATRIX (5 domains with sub-metrics)                           ││
│         │  │ ┌──────────────────────────────────────────────────────────────────────┐   ││
│         │  │ │ Cost │ Reliability │ Performance │ Governance │ Data Quality        │   ││
│         │  │ │ 78   │     92      │     85      │     71     │     89              │   ││
│         │  │ │ ▲$2K │    ▼1%      │    →0%      │    ▲3%     │    ▼2%              │   ││
│         │  │ └──────────────────────────────────────────────────────────────────────┘   ││
│         │  │                                                                              ││
│         │  │ LIVE ACTIVITY FEED           │  TREND HEATMAP                               ││
│         │  │ ┌────────────────────────────┐│ ┌────────────────────────────────────────┐  ││
│         │  │ │ ● Cost spike detected      ││ │ 7-day cost heatmap by hour            │  ││
│         │  │ │ ○ Job completed            ││ │ █▓▒░░▒▓█ (visual heatmap)             │  ││
│         │  │ │ ○ Query optimized          ││ │                                        │  ││
│         │  │ └────────────────────────────┘│ └────────────────────────────────────────┘  ││
│         │  │                                                                              ││
│         │  │ ACTIVE SIGNALS TABLE          │  AI RECOMMENDATIONS                         ││
│         │  │ ┌────────────────────────────┐│ ┌────────────────────────────────────────┐  ││
│         │  │ │ Critical signals requiring ││ │ Smart actions with 1-click apply      │  ││
│         │  │ │ immediate attention        ││ │                                        │  ││
│         │  │ └────────────────────────────┘│ └────────────────────────────────────────┘  ││
│         │  │                                                                              ││
│         │  │ RESOURCE TOPOLOGY (mini service map)                                        ││
│         │  │ ┌──────────────────────────────────────────────────────────────────────┐   ││
│         │  │ │ Visual graph of Databricks resources with health indicators         │   ││
│         │  │ └──────────────────────────────────────────────────────────────────────┘   ││
│         │  │                                                                              ││
│         │  └──────────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## SECTION 1: COMMAND BAR (Sticky Header)

### Purpose: Datadog-style global controls always accessible

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                               │
│  ⌘K  │ Search commands, signals, resources...        │ 🌐 Production ▼ │ 📅 Last 24h ▼ │   │
│                                                                                               │
│  Compare: [vs Yesterday] [vs Last Week] [Custom]     │ ⟳ Auto-refresh: ON │ 🔔 3 │ 👤 PS  │
│                                                                                               │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **Command Palette Trigger:** ⌘K icon + search field (280px), placeholder "Search commands, signals, resources..."
- **Workspace Switcher:** Dropdown showing current workspace with green dot, count of connected workspaces
- **Time Range Picker:** Dropdown with presets + custom range, shows relative time
- **Compare Mode:** Toggle buttons for comparison periods
- **Live Indicator:** Pulsing dot + "Auto-refresh: ON" text, click to pause
- **Notifications:** Bell icon with red badge showing count
- **User Avatar:** Initials in circle, dropdown for profile/logout

**Interaction:**
- ⌘K opens command palette overlay
- Workspace switch updates all data
- Time range affects all metrics
- Compare mode shows delta overlays

---

## SECTION 2: AI COMMAND CENTER (Conversational Style)

### Purpose: Personalized AI greeting with actionable insights (like reference design)

### Design: Card with colored left border, conversational tone, bullet points

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ AI COMMAND CENTER - Conversational Card Design                                               │
│                                                                                              │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │                                                                                         │  │
│ │ ████  ┌─────────────────────────────────────────────────────────────────────────────┐ │  │
│ │ ████  │                                                                             │ │  │
│ │ LEFT  │  [AI Avatar]  Good morning! Here's what I'm tracking for you:      [Hide]  │ │  │
│ │ BORDER│  (Blue-600 bg,                                                                  │ │  │
│ │ 4px   │   sparkle)    ⚠️ 3 critical issues need attention (2 cost, 1 job failure) │ │  │
│ │ TEAL  │                  (Red text for "3 critical issues")                         │ │  │
│ │ #2272B4               📈 I predict ml-workspace will exceed budget by Thursday     │ │  │
│ │       │                                                                             │ │  │
│ │       │               ✅ Your job success rate improved 3% this week - nice work!  │ │  │
│ │       │                  (Green text for "3%")                                      │ │  │
│ │       │                                                                             │ │  │
│ │       │  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐              │ │  │
│ │       │  │Fix Critical     │  │ See Forecast │  │ View Full Report │              │ │  │
│ │       │  │Issues  →        │  │              │  │                  │              │ │  │
│ │       │  └─────────────────┘  └──────────────┘  └──────────────────┘              │ │  │
│ │       │   TEAL filled         Gray outline       Blue-600 text link                    │ │  │
│ │       │   #2272B4             #E0E6EB border     #2272B4                           │ │  │
│ │       │   White text          #0B2026 text                                        │ │  │
│ │       │                                                                             │ │  │
│ │       └─────────────────────────────────────────────────────────────────────────────┘ │  │
│ │                                                                                         │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Card Structure (Conversational Style):**
```
AICommandCard
├── Container
│   ├── Background: White #FFFFFF (or very light blue #F0F8FF)
│   ├── Border: 1px solid #E0E6EB
│   ├── Border-left: 4px solid Blue-600 #2272B4 (accent stripe)
│   ├── Border-radius: 8px
│   ├── Padding: 20px 24px
│   └── Shadow: elevation-1
├── Header Row
│   ├── AI Avatar (40px circle, Blue-600 #2272B4 bg, sparkle icon white)
│   ├── Greeting (H3, Navy #0B2026, "Good morning! Here's what I'm tracking:")
│   └── Hide button (text, Blue-600 #2272B4, right-aligned)
├── Bullet List (insight items)
│   ├── Row 1: ⚠️ icon + text (critical = Red #FF3621 for key words)
│   ├── Row 2: 📈 icon + text (prediction = Navy #0B2026)
│   └── Row 3: ✅ icon + text (positive = Green #00A972 for key words)
└── Action Buttons Row
    ├── Primary: "Fix Critical Issues →" (Blue-600 filled #2272B4)
    ├── Secondary: "See Forecast" (Gray outline, Navy text)
    └── Tertiary: "View Full Report" (Blue-600 text link #2272B4)
```

**Insight Item Format:**
```
┌────────────────────────────────────────────────────────────────────────┐
│ [Icon] [Text with inline colored keywords]                             │
├────────────────────────────────────────────────────────────────────────┤
│ ⚠️     3 critical issues need attention (2 cost spikes, 1 job chain) │
│        ↑ Red #FF3621                                                   │
│                                                                        │
│ 📈     I predict ml-workspace will exceed budget by Thursday          │
│        ↑ Navy (code-style for workspace name)                         │
│                                                                        │
│ ✅     Your job success rate improved 3% this week - nice work!       │
│        ↑ Green #00A972                                                │
└────────────────────────────────────────────────────────────────────────┘
```

**Design Specifications:**

| Element | Style | Color |
|---------|-------|-------|
| Card background | White with left accent | #FFFFFF, 4px left border #2272B4 |
| Card border | Subtle | #E0E6EB |
| AI Avatar | Circle with sparkle | Blue-600 #2272B4 background, white icon |
| Greeting text | H3, friendly tone | Navy #0B2026 |
| Hide button | Text button | Blue-600 #2272B4 |
| Critical keyword | Inline colored text | Red #FF3621 |
| Positive keyword | Inline colored text | Green #00A972 |
| Code/workspace names | Monospace styled | Gray background, Navy text |
| **Primary action** ("Fix Critical Issues") | **Filled button with arrow** | **TEAL #2272B4, white text** |
| Secondary action ("See Forecast") | Outline button | Gray border #E0E6EB, Navy text |
| Tertiary action ("View Full Report") | Text link | Blue-600 #2272B4 |

**Key Design Rules:**
- ✅ LEFT BORDER accent (4px Blue-600) gives the card presence
- ✅ Conversational tone with personalized greeting
- ✅ Bullet points for easy scanning
- ✅ Inline color highlights for critical/positive items
- ✅ Primary action button is TEAL (not red)
- ✅ Clear visual hierarchy: Avatar → Greeting → Bullets → Actions

---

## SECTION 3: PRIMARY METRICS ROW

### Purpose: Contextual headline numbers with colored top accent bars (like reference design)

### Design: Cards with COLORED TOP BORDERS for visual differentiation + status chips

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ PRIMARY METRICS                                                                              │
│ (Section header, Navy #0B2026, caps, small)                                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│ ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│
│ │ GREEN top bar       │ │ TEAL top bar        │ │ CORAL top bar       │ │ NAVY top bar        │
│ │ (Health metric)     │ │ (Cost metric)       │ │ (Alert metric)      │ │ (SLA metric)        │
│ │                     │ │                     │ │                     │ │                     │
│ │ Health Score        │ │ Cost Today          │ │ Active Alerts       │ │ SLA Status          │
│ │ (Label, Slate)      │ │ (Label, Slate)      │ │ (Label, Slate)      │ │ (Label, Slate)      │
│ │                     │ │                     │ │                     │ │                     │
│ │ 87/100              │ │ $45,230             │ │ 7                   │ │ 98.2%               │
│ │ (Large, Navy, bold) │ │ (Large, Navy, bold) │ │ (Large, Navy, bold) │ │ (Large, Navy, bold) │
│ │                     │ │                     │ │                     │ │                     │
│ │ 🟢 Stable           │ │ 🟠 Anomaly detected │ │ 🔵 Trending Up      │ │ 🟢 On track         │
│ │ (Green chip)        │ │ (Coral chip)        │ │ (Blue-600 chip)         │ │ (Green chip)        │
│ │                     │ │                     │ │                     │ │                     │
│ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
│                                                                                               │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Card Structure (With Colored Top Border Accent):**
```
PrimaryMetricCard
├── Card Container
│   ├── Background: White #FFFFFF
│   ├── Border: 1px solid #E0E6EB
│   ├── Border-top: 4px solid [metric accent color] ← KEY DIFFERENTIATOR
│   ├── Border-radius: 8px (with overflow hidden for clean top bar)
│   ├── Padding: 16px
│   └── Shadow: subtle elevation-1
├── Label (top)
│   ├── Font: 14px, regular
│   ├── Color: Slate #4A5D6B (NOT Navy - ensures readable)
│   └── Margin-bottom: 8px
├── Value (center)
│   ├── Font: 32px, bold (600 weight)
│   ├── Color: Navy #0B2026
│   └── Margin-bottom: 12px
└── Status Chip (bottom)
    ├── Font: 12px, medium (500 weight)
    ├── Padding: 4px 10px
    ├── Border-radius: 4px
    ├── Icon: 8px filled circle
    └── Colors by status (see below)
```

**⚠️ ACCENT TOP BORDER COLORS BY METRIC:**
| Metric | Top Border Color | Reason |
|--------|-----------------|--------|
| Health Score | Green #00A972 | Health/wellness indicator |
| Cost Today | Blue-600 #2272B4 | Financial/cost domain |
| Active Alerts | Coral #E8715E | Attention/warning |
| SLA Status | Navy #0B2026 | Reliability/performance |

**Status Chip Colors (High Contrast - Text on Light Background):**
| Status | Background | Text Color | Dot Color |
|--------|------------|------------|-----------|
| Stable / On track | #E6F7F1 (light green) | #00875A (dark green) | #00A972 |
| Anomaly detected | #FDF0ED (light coral) | #C45340 (dark coral) | #E8715E |
| Trending Up | #D7EDFE (Blue-200) | #0E538B (Blue-700) | #2272B4 |
| Warning | #FFF8E6 (light amber) | #B77800 (dark amber) | #FFAB00 |
| Critical | #FFEBE8 (light red) | #CC2A18 (dark red) | #FF3621 |

**Layout:**
- 4 cards in a row (equal width)
- Gap between cards: 16px
- Section aligns with Domain Health cards below
- Cards should be same width as Domain Health cards (responsive grid)

---

## SECTION 4: DOMAIN HEALTH CARDS

### Purpose: 5 domain cards with colored top borders (matching reference design)

### Design: Cards with colored accent bar on top, key metric, and trend

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ DOMAIN HEALTH                                                                                │
│ (Section header, Navy #0B2026, caps, small - matches PRIMARY METRICS header)                │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │
│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │
│ │ TEAL top bar  │ │ GREEN top bar │ │ TEAL top bar  │ │ CORAL top bar │ │ GREEN top bar │   │
│ │               │ │               │ │               │ │               │ │               │   │
│ │ 💰 Cost       │ │ ⚡ Reliability│ │ 📈 Performance│ │ 🛡️ Security   │ │ 📋 Quality    │   │
│ │               │ │               │ │               │ │               │ │               │   │
│ │ $45K/day      │ │ 96.2%         │ │ 1.2s p95      │ │ 5 issues      │ │ 94.2%         │   │
│ │ (Large, bold) │ │ (Large, bold) │ │ (Large, bold) │ │ (Large, bold) │ │ (Large, bold) │   │
│ │               │ │               │ │               │ │               │ │               │   │
│ │ ↑ 12%         │ │ ↑ 0.8%        │ │ ↓ 0.3s        │ │ ↓ 2 HIGH      │ │ ↑ 1.2%        │   │
│ │ (Red - bad)   │ │ (Green - good)│ │ (Green - good)│ │ (Red - bad)   │ │ (Green - good)│   │
│ │               │ │               │ │               │ │               │ │               │   │
│ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘   │
│                                                                                               │
│ All 5 cards are clickable → navigate to domain detail page                                   │
│                                                                                               │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Domain Card Structure (Simplified, like reference):**
```
DomainHealthCard
├── Container
│   ├── Background: White #FFFFFF
│   ├── Border: 1px solid #E0E6EB
│   ├── Border-top: 4px solid [domain color]
│   ├── Border-radius: 8px
│   ├── Padding: 16px
│   └── Hover: Blue-600 border #2272B4
├── Header Row
│   ├── Domain Icon (16px, colored)
│   └── Domain Name (14px, Slate #4A5D6B)
├── Metric Value
│   ├── Font: 24px, bold (600 weight)
│   └── Color: Navy #0B2026
└── Trend Row
    ├── Arrow (↑/↓)
    └── Trend value + label (colored by direction)
```

**Top Border Colors by Domain:**
| Domain | Top Border Color | Icon |
|--------|-----------------|------|
| Cost | Blue-600 #2272B4 | 💰 or $ |
| Reliability | Green #00A972 | ⚡ or ✓ |
| Performance | Blue-600 #2272B4 | 📈 or ↗ |
| Security | Coral #E8715E | 🛡️ or 🔒 |
| Quality | Green #00A972 | 📋 or ✓ |

**Trend Colors (for the ↑/↓ percentage):**
- Cost ↑ = Red (bad - spending more)
- Cost ↓ = Green (good - saving money)
- Reliability ↑ = Green (good - more reliable)
- Reliability ↓ = Red (bad - less reliable)
- Performance ↓ latency = Green (good - faster)
- Performance ↑ latency = Red (bad - slower)
- Security ↓ issues = Green (good - fewer issues)
- Security ↑ issues = Red (bad - more issues)
- Quality ↑ = Green (good - better quality)
- Quality ↓ = Red (bad - worse quality)

**Layout Alignment:**
- 5 cards in a row (equal width)
- Gap between cards: 16px (same as PRIMARY METRICS)
- Cards align horizontally with PRIMARY METRICS row above

**IMPORTANT: Grid Alignment Between Sections**

```
PRIMARY METRICS (4 cards)          DOMAIN HEALTH (5 cards)
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│       │ │       │ │       │ │       │    ← 4 cards, equal width
└───────┘ └───────┘ └───────┘ └───────┘
                                            ← 24px gap
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│     │ │     │ │     │ │     │ │     │    ← 5 cards, equal width
└─────┘ └─────┘ └─────┘ └─────┘ └─────┘

Both rows should:
- Start at the same left margin
- End at the same right margin
- Use consistent 16px gaps between cards
```

**Hover States:**
- Card: Blue-600 #2272B4 border (replaces default gray)
- Cursor: pointer
- Transition: 150ms ease

**Click Action:**
- Each card navigates to its domain detail page

---

## SECTION 5: TWO-COLUMN LAYOUT (Activity + Heatmap)

### Left: Live Activity Feed (Sentry-style)

```
┌────────────────────────────────────────────────────────────────────┐
│ Live Activity                                    [Pause] [Filter]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ● NOW    Cost alert triggered                                      │
│ │        prod-sql-warehouse exceeded $30K threshold                │
│ │        [View Alert →]                                            │
│ │                                                                   │
│ ○ 2m     Job completed successfully                                │
│ │        daily-etl-pipeline • Run #4521 • 12m duration            │
│ │                                                                   │
│ ○ 5m     AI recommendation applied                                 │
│ │        Auto-termination enabled on dev-cluster                   │
│ │        Estimated savings: $1.2K/day                              │
│ │                                                                   │
│ ○ 8m     Query optimized automatically                             │
│ │        analyst@company.com query rewritten                       │
│ │        Improvement: 94% faster                                   │
│ │                                                                   │
│ ○ 12m    Security finding resolved                                 │
│ │        Overly permissive access fixed on analytics.users         │
│ │                                                                   │
│ ○ 15m    SLA warning cleared                                       │
│ │        prod-reporting-job back within SLA                        │
│ │                                                                   │
│ │                                                                   │
│ ▼ Load more activity                                               │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

**Activity Item Structure:**
```
ActivityItem
├── TimeIndicator (● for live, ○ for past)
├── Timestamp (relative)
├── EventType (colored badge)
├── Title (body/emphasis)
├── Description (body/small, text/secondary)
└── [Optional] ActionLink
```

**Event Types & Colors (for the dot indicator):**
- Alert: Red dot #FF3621
- Job: Blue-600 dot #2272B4
- Optimization: Green dot #00A972
- Security: Purple dot #6B4FBB
- SLA: Amber dot #FFAB00

**Text & Link Colors:**
- Title text: Navy #0B2026
- Description: Slate #4A5D6B
- **Action links** ("[View Alert →]"): **Blue-600 #2272B4**
- **Pause/Filter buttons**: Blue-600 outline or text buttons

### Right: Trend Heatmap (Grafana-style)

```
┌────────────────────────────────────────────────────────────────────┐
│ Cost Heatmap • 7 Days × 24 Hours                    [Cost ▼] [⚙]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│        00  03  06  09  12  15  18  21                              │
│        ├───┼───┼───┼───┼───┼───┼───┼───┐                          │
│   Mon  │░░░│░░░│▒▒▒│▓▓▓│███│███│▓▓▓│▒▒▒│                          │
│   Tue  │░░░│░░░│▒▒▒│▓▓▓│███│███│▓▓▓│▒▒▒│                          │
│   Wed  │░░░│░░░│▒▒▒│███│███│███│▓▓▓│▒▒▒│ ← Spike                  │
│   Thu  │░░░│░░░│▒▒▒│▓▓▓│███│███│▓▓▓│▒▒▒│                          │
│   Fri  │░░░│░░░│▒▒▒│▓▓▓│███│███│▓▓▓│▒▒▒│                          │
│   Sat  │░░░│░░░│░░░│▒▒▒│▒▒▒│▒▒▒│░░░│░░░│                          │
│   Sun  │░░░│░░░│░░░│▒▒▒│▒▒▒│▒▒▒│░░░│░░░│                          │
│        └───┴───┴───┴───┴───┴───┴───┴───┘                          │
│                                                                     │
│   Legend: ░ $0-500  ▒ $500-1K  ▓ $1K-2K  █ $2K+                   │
│                                                                     │
│   Anomaly detected: Wed 12:00-15:00 (+42% vs baseline)            │
│   [View Details →]                                                 │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

**Heatmap Colors (using Blue-600 scale for cost, NOT red scale):**
- Low: Light Blue-600 #E6F4F7 to #A8D8E8
- Medium: Blue-600 #2272B4
- High: Dark Blue-600 #065E7A to #043D4F
- Anomaly highlight: Coral border #E8715E (to call attention)

**Link Colors:**
- "View Details →": Blue-600 #2272B4

---

## SECTION 6: ACTIVE SIGNALS (World-Class Card Design)

### Purpose: Sentry/Datadog-style signal triage with rich context and clear visual hierarchy

### Design: Card-based layout (NOT basic table) with severity accents, clear typography, and prominent actions

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Active Signals                                           8 signals • [View All in Explorer →]│
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ Filter: [All Types ▼] [All Domains ▼] [Critical + High ▼]              🔍 Search...   │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│  │
│ │ RED 4px top border (Critical alert)                                                     │  │
│ │                                                                                         │  │
│ │ 🔴 Cost spike in Production workspace                                        5 min ago │  │
│ │    (18px, Navy #0B2026, bold)                                         (12px, Steel)    │  │
│ │                                                                                         │  │
│ │ ┌─────────────┐ ┌───────────────────────────────────────────────────┐                 │  │
│ │ │ ● CRITICAL  │ │ prod-sql-warehouse-001 • Query cost, Warehouse scale│                 │  │
│ │ └─────────────┘ └───────────────────────────────────────────────────┘                 │  │
│ │  (Red chip)     (14px, Slate #4A5D6B - resource detail)                                │  │
│ │                                                                                         │  │
│ │ 💰 Impact: $12.5K over threshold (+42%)     🎯 Affected: 3 jobs, 12 dashboards        │  │
│ │ (14px, Navy #0B2026 - high contrast)                                                   │  │
│ │                                                                                         │  │
│ │ ↳ 2 correlated signals detected:                                                       │  │
│ │   • Query cost anomaly (same WH, started 2m earlier)                                  │  │
│ │   • Warehouse auto-scale event (triggered by query load)                              │  │
│ │   (12px, Slate #4A5D6B)                                                                │  │
│ │                                                                                         │  │
│ │ ┌──────────────────┐  ┌────────────────┐  ┌─────────────┐                            │  │
│ │ │ View Details  →  │  │ Acknowledge    │  │ Mute     ▼  │          John S. assigned  │  │
│ │ └──────────────────┘  └────────────────┘  └─────────────┘          (12px, Steel)     │  │
│ │  TEAL text link       TEAL filled         Gray outline                                 │  │
│ │  #2272B4              #2272B4 white       #E0E6EB/#0B2026                              │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│  │
│ │ CORAL 4px top border (High severity)                                                   │  │
│ │                                                                                         │  │
│ │ ⚡ Job failure rate spike                                                    15 min ago │  │
│ │    (18px, Navy #0B2026, bold)                                         (12px, Steel)    │  │
│ │                                                                                         │  │
│ │ ┌─────────────┐ ┌───────────────────────────────────────────────────┐                 │  │
│ │ │ ● HIGH      │ │ prod-etl-pipeline                                  │                 │  │
│ │ └─────────────┘ └───────────────────────────────────────────────────┘                 │  │
│ │  (Coral chip)   (14px, Slate #4A5D6B)                                                  │  │
│ │                                                                                         │  │
│ │ ⚡ Impact: 12 failed jobs (-3.2% success rate)     🎯 Affected: 5 downstream pipelines│  │
│ │ (14px, Navy #0B2026)                                                                   │  │
│ │                                                                                         │  │
│ │ 📝 What changed: Schema deployment detected 30 min ago                                │  │
│ │   • Table analytics.events: 3 columns added                                           │  │
│ │   • Downstream jobs may be impacted                                                   │  │
│ │   (12px, Slate #4A5D6B)                                                                │  │
│ │                                                                                         │  │
│ │ ┌──────────────────┐  ┌────────────────┐  ┌─────────────┐                            │  │
│ │ │ View Details  →  │  │ Investigate    │  │ Mute     ▼  │          Unassigned        │  │
│ │ └──────────────────┘  └────────────────┘  └─────────────┘                             │  │
│ │  TEAL text link       TEAL filled         Gray outline                                 │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│  │
│ │ AMBER 4px top border (Medium severity)                                                 │  │
│ │                                                                                         │  │
│ │ 🛡️ Security: Overly permissive table access                              1 hour ago   │  │
│ │    (18px, Navy #0B2026, bold)                                         (12px, Steel)    │  │
│ │                                                                                         │  │
│ │ ┌─────────────┐ ┌───────────────────────────────────────────────────┐                 │  │
│ │ │ ● MEDIUM    │ │ analytics.users • No owner assigned                │                 │  │
│ │ └─────────────┘ └───────────────────────────────────────────────────┘                 │  │
│ │  (Amber chip)   (14px, Slate #4A5D6B)                                                  │  │
│ │                                                                                         │  │
│ │ 🛡️ Impact: 45 users with access (HIGH risk)     📋 Contains: email, phone columns    │  │
│ │ (14px, Navy #0B2026)                                                                   │  │
│ │                                                                                         │  │
│ │ 🔍 Evidence: Table contains PII. 45 users have SELECT permission.                     │  │
│ │   (12px, Slate #4A5D6B)                                                                │  │
│ │                                                                                         │  │
│ │ ┌──────────────────┐  ┌────────────────┐  ┌─────────────┐                            │  │
│ │ │ View Details  →  │  │ Fix Access     │  │ Add Owner▼  │                             │  │
│ │ └──────────────────┘  └────────────────┘  └─────────────┘                             │  │
│ │  TEAL text link       RED filled          Gray outline                                 │  │
│ │                       #FF3621 white       #E0E6EB/#0B2026                              │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ 💡 AI Insight: The cost spike and job failures may be related - both started after    │  │
│ │    the schema deployment at 10:15 AM. [Investigate Correlation →]                     │  │
│ │    (Light blue background #D7EDFE, Navy-900 text #0B2026, 14px)                       │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Signal Card Structure (World-Class Design):**
```
SignalCard (Professional Sentry/Datadog-style)
├── Container
│   ├── Background: White #FFFFFF
│   ├── Border: 1px solid #E0E6EB
│   ├── Border-top: 4px solid [severity color]
│   ├── Border-radius: 8px
│   ├── Padding: 20px 24px
│   ├── Margin-bottom: 12px
│   └── Hover: Blue-600 border #2272B4, cursor pointer
│
├── Title Row
│   ├── Severity Badge (left, 8px gap)
│   ├── Signal Title (18px, Navy #0B2026, bold 600)
│   └── Timestamp (12px, Steel #6B7D8A, right-aligned)
│
├── Metadata Row
│   ├── Resource Detail (14px, Slate #4A5D6B)
│   └── Correlation badges (if applicable)
│
├── Impact Row (Key Metrics)
│   ├── Primary Impact (14px, Navy #0B2026, medium 500)
│   ├── Icons: 💰 ⚡ 🛡️ 📋 (colored by domain)
│   └── Secondary Impact (14px, Navy #0B2026)
│
├── Context Section (Expandable)
│   ├── Correlation info (12px, Slate #4A5D6B)
│   └── What Changed info (12px, Slate #4A5D6B)
│
└── Action Footer
    ├── Primary Actions (Blue-600 filled or RED for destructive)
    ├── Secondary Actions (Gray outline, Navy text)
    └── Assignment info (12px, Steel #6B7D8A)
```

**Typography Hierarchy (CRITICAL for readability):**
| Element | Size | Weight | Color | Letter-spacing |
|---------|------|--------|-------|----------------|
| Signal Title | 18px | 600 (semi-bold) | Navy #0B2026 | -0.01em |
| Resource Detail | 14px | 400 (regular) | Slate #4A5D6B | 0 |
| Impact Metrics | 14px | 500 (medium) | Navy #0B2026 | 0 |
| Context/Evidence | 12px | 400 (regular) | Slate #4A5D6B | 0 |
| Timestamp | 12px | 400 (regular) | Steel #6B7D8A | 0 |

**Top Border Colors by Severity:**
| Severity | Border Color | Badge Background | Badge Text |
|----------|-------------|------------------|------------|
| Critical | Red #FF3621 | #FFEBE8 (light red) | #CC2A18 (dark red) |
| High | Coral #E8715E | #FDF0ED (light coral) | #C45340 (dark coral) |
| Medium | Amber #FFAB00 | #FFF8E6 (light amber) | #B77800 (dark amber) |
| Low | Navy-500 #618794 | #EDF2F8 (Navy-100) | #143D4A (Navy-700) |

**Enhanced Features:**
- **4px colored top border** - Immediate severity recognition
- **Clear title hierarchy** - 18px bold makes signals scannable
- **High-contrast text** - Navy #0B2026 for all important text (never gray on white!)
- **Prominent actions** - Blue-600 filled buttons stand out
- **Card-based layout** - Breathing room between signals (not cramped table)
- **Expandable context** - Correlation and "What Changed" with subtle styling

---

## SECTION 7: AI RECOMMENDATIONS (Action-Oriented)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ AI Recommendations                                    5 available • $4.2K potential savings  │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ ┌──────┐                                                                               │  │
│ │ │ 💰   │  Enable auto-termination on dev-analytics-cluster          SAVE $1.2K/day   │  │
│ │ │ $1.2K│                                                                               │  │
│ │ └──────┘  Cluster idle 68% of time. Auto-terminate after 30 min of inactivity.       │  │
│ │                                                                                         │  │
│ │           ████████████████████░░░░░░░░░░  94% confidence │ Based on 7 days data       │  │
│ │                                                                                         │  │
│ │           [✓ Apply Now]  [Preview Changes]  [Schedule]  [Dismiss]          Safe ✓     │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ ┌──────┐                                                                               │  │
│ │ │ ⚡   │  Optimize slow query pattern                                 SAVE 40% time   │  │
│ │ │ Perf │                                                                               │  │
│ │ └──────┘  3 queries missing partition filter. Add date filter to reduce scan.        │  │
│ │                                                                                         │  │
│ │           ████████████████░░░░░░░░░░░░░░  78% confidence │ Affects 12 dashboards      │  │
│ │                                                                                         │  │
│ │           [View Queries]  [Apply Fix]  [Notify Users]  [Dismiss]      Review first ⚠️ │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│ ┌────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ ┌──────┐                                                                               │  │
│ │ │ 🛡️   │  Add owner to 5 unowned tables                              Governance fix   │  │
│ │ │ Gov  │                                                                               │  │
│ │ └──────┘  5 tables in analytics schema have no owner. Assign to analytics team.      │  │
│ │                                                                                         │  │
│ │           [Assign Ownership]  [View Tables]  [Dismiss]                    Safe ✓       │  │
│ └────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│                                                              [View All Recommendations →]    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Recommendation Card Structure:**
```
RecommendationCard
├── ImpactBadge (left, colored by domain)
│   ├── DomainIcon
│   └── SavingsValue (if applicable)
├── Content
│   ├── Title (body/emphasis)
│   ├── Description (body/default)
│   ├── ConfidenceBar (percentage fill)
│   ├── Context (secondary text)
│   └── Actions (buttons)
└── SafetyIndicator (Safe ✓ or Review ⚠️)
```

---

## SECTION 8: RESOURCE TOPOLOGY (Professional Service Map - Datadog/New Relic Style)

### Purpose: Visual dependency graph of Databricks resources showing health, data flow, and relationships

### Design: Professional node-link diagram with polished card-style nodes, clear flow lines, and rich status indicators

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Resource Topology                                    🔴 1 critical  ⚠️ 2 warnings  ✅ 18 healthy          │
│ ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ View: [Data Flow ▼] [Workspace: All ▼] [Status: All ▼]      [Expand ↗] [Refresh ⟳] [Export 📷]  │  │
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                           │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃ GOVERNANCE LAYER                                                            [Expand Layer ▼]    ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                                           │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐     │
│  │ 🏛️ Unity Catalog                                                               ✅ HEALTHY      │     │
│  │ prod_catalog                                                                                    │     │
│  │ ────────────────────────────────────────────────────────────────────────────────────────────── │     │
│  │ 📊 847 tables • 23 schemas                        92% tag coverage • 0 PII exposed              │     │
│  │                                                                                                 │     │
│  │ [View Catalog →]                                                                                │     │
│  └────────────────────────────────────────────────────────────────────────────────────────────────┘     │
│                                              │                                                            │
│                                              │ (Blue-600 flow line 2px)                                      │
│           ┌──────────────────────────────────┼─────────────────────────────────┐                         │
│           │                                  │                                 │                         │
│           │                                  │                                 │                         │
│  ┏━━━━━━━━┷━━━━━━━━━━┓       ┏━━━━━━━━━━━━━━┷━━━━━━━━━┓       ┏━━━━━━━━━━━━━┷━━━━━━━━━━┓               │
│  ┃ DATA LAYER        ┃       ┃ DATA LAYER             ┃       ┃ DATA LAYER            ┃               │
│  ┗━━━━━━━━━━━━━━━━━━━┛       ┗━━━━━━━━━━━━━━━━━━━━━━━━┛       ┗━━━━━━━━━━━━━━━━━━━━━━━┛               │
│                                                                                                           │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐                       │
│  │ 📊 Bronze Schema    │     │ 📊 Silver Schema    │     │ 📊 Gold Schema      │                       │
│  │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│     │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│     │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│                       │
│  │ Blue-600 3px top border │     │ Blue-600 3px top border │     │ Blue-600 3px top border │                       │
│  │                     │     │                     │     │                     │                       │
│  │ system_tables       │ ──▶ │ processed_data      │ ──▶ │ analytics_marts     │                       │
│  │                     │     │                     │     │                     │                       │
│  │ ┌──────────┐        │     │ ┌──────────┐        │     │ ┌──────────┐        │                       │
│  │ │ ● Healthy│        │     │ │ ● Healthy│        │     │ │ ● Healthy│        │                       │
│  │ └──────────┘        │     │ └──────────┘        │     │ └──────────┘        │                       │
│  │ (Green chip)        │     │ (Green chip)        │     │ (Green chip)        │                       │
│  │                     │     │                     │     │                     │                       │
│  │ 156 tables          │     │ 89 tables           │     │ 42 tables           │                       │
│  │ Freshness: <5m      │     │ DQ Score: 94%       │     │ Freshness: <10m     │                       │
│  │                     │     │ Last update: 2m ago │     │ Last update: 5m ago │                       │
│  │                     │     │                     │     │                     │                       │
│  │ [View Schema →]     │     │ [View Schema →]     │     │ [View Schema →]     │                       │
│  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘                       │
│           │                             │                             │                                 │
│           └─────────────────────────────┼─────────────────────────────┘                                 │
│                                         │ (Blue-600 flow line 2px)                                          │
│  ─────────────────────────────────────────────────────────────────────────────────────────────────────  │
│                                         │                                                                │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃ COMPUTE LAYER                                                                                     ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                                           │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐                     │
│  │ 🏭 SQL Warehouse      │   │ 🖥️ All-Purpose        │   │ 🚀 Serverless         │                     │
│  │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│                     │
│  │ RED 3px top border    │   │ AMBER 3px top border  │   │ GREEN 3px top border  │                     │
│  │                       │   │                       │   │                       │                     │
│  │ prod-analytics-wh     │   │ ml-training-cluster   │   │ serverless-pool       │                     │
│  │                       │   │                       │   │                       │                     │
│  │ ┌──────────┐          │   │ ┌──────────┐          │   │ ┌──────────┐          │                     │
│  │ │ ● ALERT  │          │   │ │ ● Warning│          │   │ │ ● Healthy│          │                     │
│  │ └──────────┘          │   │ └──────────┘          │   │ └──────────┘          │                     │
│  │ (Red chip)            │   │ (Amber chip)          │   │ (Green chip)          │                     │
│  │                       │   │                       │   │                       │                     │
│  │ 💰 Cost: $42.3K today │   │ 💰 Cost: $8.2K/day    │   │ 💰 Cost: $12.4K today │                     │
│  │ ⚠️ Cost spike: +42%   │   │ ⚠️ Idle: 68%         │   │ ✅ Healthy            │                     │
│  │ ⚡ 847 queries/hr     │   │ No auto-terminate set │   │ 23 jobs running       │                     │
│  │ 📊 P95: 4.2s (⚠️ 2s)  │   │                       │   │ ⚡ Avg: 1.2s          │                     │
│  │                       │   │                       │   │                       │                     │
│  │ [Fix Alert →]         │   │ [Configure →]         │   │ [View Jobs →]         │                     │
│  └───────────┬───────────┘   └───────────┬───────────┘   └───────────────────────┘                     │
│              │                           │                                                              │
│              │ (Red flow 2px)            │ (Amber flow 2px)                                             │
│  ─────────────┼───────────────────────────┼─────────────────────────────────────────────────────────── │
│              │                           │                                                              │
│  ┏━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃ ORCHESTRATION LAYER                                                                               ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│              │                           │                                                              │
│              ▼                           ▼                                                              │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐                    │
│  │ 🔄 DLT Pipeline       │   │ 📅 Workflow           │   │ 📅 Workflow           │                    │
│  │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│                    │
│  │ GREEN 3px top border  │   │ AMBER 3px top border  │   │ GREEN 3px top border  │                    │
│  │                       │   │                       │   │                       │                    │
│  │ silver_medallion      │   │ daily-etl-pipeline    │   │ hourly-metrics        │                    │
│  │                       │   │                       │   │                       │                    │
│  │ ┌──────────┐          │   │ ┌──────────┐          │   │ ┌──────────┐          │                    │
│  │ │●Streaming│          │   │ │●Degraded │          │   │ │ ●Healthy │          │                    │
│  │ └──────────┘          │   │ └──────────┘          │   │ └──────────┘          │                    │
│  │ (Green chip)          │   │ (Amber chip)          │   │ (Green chip)          │                    │
│  │                       │   │                       │   │                       │                    │
│  │ 🔄 Lag: 2.3s          │   │ ⚠️ 2 retries last run │   │ ✅ Last run: 12m ago  │                    │
│  │ ⚡ 12.4K records/sec  │   │ ⏱️ Duration: 52m      │   │ ⏱️ Duration: 8m       │                    │
│  │ 📊 Quality: 99.2%     │   │ (+12m vs avg)         │   │ 📊 SLA: Met           │                    │
│  │                       │   │ Next: in 15m          │   │                       │                    │
│  │                       │   │                       │   │                       │                    │
│  │ [View Lineage →]      │   │ [View Runs →]         │   │ [View Runs →]         │                    │
│  └───────────────────────┘   └───────────────────────┘   └───────────────────────┘                    │
│                                          │                                                              │
│                                          │ (Blue-600 flow 2px)                                              │
│  ────────────────────────────────────────┼──────────────────────────────────────────────────────────── │
│                                          │                                                              │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃ AI & SERVING LAYER                                                                                ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                          │                                                              │
│                                          ▼                                                              │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐                    │
│  │ 🤖 Model Serving      │   │ 🔍 Vector Search      │   │ 🧞 Genie Space        │                    │
│  │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│                    │
│  │ GREEN 3px top border  │   │ GREEN 3px top border  │   │ GREEN 3px top border  │                    │
│  │                       │   │                       │   │                       │                    │
│  │ cost-anomaly-detector │   │ runbook-embeddings    │   │ cost-intelligence     │                    │
│  │                       │   │                       │   │                       │                    │
│  │ ┌──────────┐          │   │ ┌──────────┐          │   │ ┌──────────┐          │                    │
│  │ │●Serving  │          │   │ │ ●Indexed │          │   │ │ ●Active  │          │                    │
│  │ └──────────┘          │   │ └──────────┘          │   │ └──────────┘          │                    │
│  │ (Green chip)          │   │ (Green chip)          │   │ (Green chip)          │                    │
│  │                       │   │                       │   │                       │                    │
│  │ ⚡ 234 req/min        │   │ 📊 1.2M vectors       │   │ 💬 47 queries today   │                    │
│  │ ⏱️ P95: 120ms         │   │ 🔄 Synced: 2h ago     │   │ 🎯 Accuracy: 94%      │                    │
│  │ 🎯 Accuracy: 96%      │   │ 💾 Size: 4.2GB        │   │                       │                    │
│  │ 💰 $1.2K/day          │   │                       │   │                       │                    │
│  │                       │   │                       │   │                       │                    │
│  │ [View Metrics →]      │   │ [View Index →]        │   │ [View Space →]        │                    │
│  └───────────────────────┘   └───────────────────────┘   └───────────────────────┘                    │
│                                          │                                                              │
│                                          │ (Blue-600 flow 2px)                                              │
│  ────────────────────────────────────────┼──────────────────────────────────────────────────────────── │
│                                          │                                                              │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃ CONSUMPTION LAYER                                                                                 ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                          │                                                              │
│                                          ▼                                                              │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐                    │
│  │ 📊 AI/BI Dashboard    │   │ 📊 AI/BI Dashboard    │   │ 🔔 SQL Alerts         │                    │
│  │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│   │▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀│                    │
│  │ GREEN 3px top border  │   │ AMBER 3px top border  │   │ AMBER 3px top border  │                    │
│  │                       │   │                       │   │                       │                    │
│  │ Executive Summary     │   │ Cost Deep Dive        │   │ Alert Rules           │                    │
│  │                       │   │                       │   │                       │                    │
│  │ ┌──────────┐          │   │ ┌──────────┐          │   │ ┌──────────┐          │                    │
│  │ │ ● Live   │          │   │ │●Stale    │          │   │ │●3 Firing │          │                    │
│  │ └──────────┘          │   │ └──────────┘          │   │ └──────────┘          │                    │
│  │ (Green chip)          │   │ (Amber chip)          │   │ (Amber chip)          │                    │
│  │                       │   │                       │   │                       │                    │
│  │ 👥 12 viewers now     │   │ ⚠️ Last refresh: 4h   │   │ 56 total rules        │                    │
│  │ 🔄 Refresh: 5m        │   │ ❌ Refresh failed     │   │ 🔴 cost_threshold     │                    │
│  │                       │   │                       │   │ 🔴 sla_breach         │                    │
│  │                       │   │                       │   │ 🔴 security_audit     │                    │
│  │                       │   │                       │   │                       │                    │
│  │ [Open Dashboard →]    │   │ [Fix Refresh →]       │   │ [View Alerts →]       │                    │
│  └───────────────────────┘   └───────────────────────┘   └───────────────────────┘                    │
│                                                                                                           │
│  ─────────────────────────────────────────────────────────────────────────────────────────────────────  │
│                                                                                                           │
│  LEGEND & CONTROLS                                                                                        │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Status Indicators:  ●Healthy (Green)  ●Warning (Amber)  ●Critical (Red)  ○Unknown (Gray)          │  │
│  │                                                                                                     │  │
│  │ Flow Lines:  ─▶ Data pipeline (Blue-600)   ─▶ Alert dependency (Red/Amber)   ━━ Layer boundary       │  │
│  │                                                                                                     │  │
│  │ Resource Types:                                                                                     │  │
│  │ 🏛️ Unity Catalog  📊 Schema  🏭 SQL WH  🖥️ Cluster  🚀 Serverless  🔄 DLT  📅 Workflow          │  │
│  │ 🤖 Model Serving  🔍 Vector Search  🧞 Genie  📊 Dashboard  🔔 Alerts                             │  │
│  │                                                                                                     │  │
│  │ Quick Stats:  847 tables • 23 compute • 15 pipelines • 56 alerts • $64.1K today                   │  │
│  │                                                                                                     │  │
│  │ [Click any node for details] [Full Screen ↗] [Export PNG 📷] [Auto-refresh: ON ⟳]                │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Professional Node Card Structure (World-Class Design)

**Resource Node Card (Card-Based, NOT Box Art):**
```
TopologyNodeCard
├── Container
│   ├── Background: White #FFFFFF
│   ├── Border: 1px solid #E0E6EB (Mist)
│   ├── Border-top: 3px solid [status color]
│   ├── Border-radius: 8px
│   ├── Box-shadow: 0 2px 4px rgba(27,58,75,0.08)
│   ├── Padding: 16px 20px
│   ├── Min-width: 240px, Min-height: 160px
│   └── Hover: Subtle Blue-600 border (#2272B4), cursor pointer
│
├── Header Row
│   ├── Icon (20px, colored by resource type)
│   ├── Resource Type (10px, uppercase, letter-spacing 0.05em, Slate #4A5D6B)
│   └── Gap: 8px
│
├── Title
│   ├── Resource Name (16px, semi-bold 600, Navy #0B2026)
│   ├── Margin-top: 4px
│   └── Truncate with ellipsis if too long
│
├── Status Badge
│   ├── Chip style (8px padding, 4px border-radius)
│   ├── Status text (11px, medium 500)
│   ├── Leading dot indicator (colored)
│   └── Margin-top: 8px
│
├── Metrics Section
│   ├── Stack vertically (gap: 6px)
│   ├── Each metric: Icon (14px) + Text (13px, Navy #0B2026)
│   ├── Emphasize critical metrics (cost, errors)
│   └── Max 4 metrics per node
│
└── Action Link
    ├── Blue-600 text (#2272B4), 13px, medium 500
    ├── Right arrow icon (12px)
    ├── Margin-top: 12px
    └── Hover: Darker Blue-700 (#0E538B)
```

**Typography Hierarchy (CRITICAL for Readability):**
| Element | Size | Weight | Color | Letter-spacing |
|---------|------|--------|-------|----------------|
| Resource Type | 10px | 600 (semi-bold) | Slate #4A5D6B | 0.05em (tracked) |
| Resource Name | 16px | 600 (semi-bold) | Navy #0B2026 | 0 |
| Status Badge Text | 11px | 500 (medium) | Varies by status | 0 |
| Metric Text | 13px | 400 (regular) | Navy #0B2026 | 0 |
| Action Link | 13px | 500 (medium) | Blue-600 #2272B4 | 0 |

**Node Sizes (Professional Spacing):**
| Type | Min-Width | Min-Height | Max-Width |
|------|-----------|------------|-----------|
| Unity Catalog (Banner) | 100% | 80px | - |
| Schema Node | 240px | 140px | 280px |
| Compute Resource | 260px | 180px | 300px |
| Pipeline/Workflow | 260px | 180px | 300px |
| AI/Serving | 240px | 160px | 280px |
| Dashboard/Alert | 240px | 160px | 280px |

**Top Border Colors by Status (3px solid):**
| Status | Border Color | Badge Background | Badge Text | Dot Color |
|--------|-------------|------------------|------------|-----------|
| Healthy | Green #00A972 | #E6F7F1 (light green) | #007A54 (dark green) | Green |
| Warning | Amber #FFAB00 | #FFF8E6 (light amber) | #B77800 (dark amber) | Amber |
| Critical | Red #FF3621 | #FFEBE8 (light red) | #CC2A18 (dark red) | Red |
| Unknown | Slate #4A5D6B | #F0F3F5 (cloud) | #4A5D6B (slate) | Slate |

**Status Badge Colors by State:**
| State | Chip Background | Chip Text | Leading Dot |
|-------|----------------|-----------|-------------|
| Streaming/Live/Serving | #E6F7F1 | #007A54 | ● Green |
| Degraded/Stale/Warning | #FFF8E6 | #B77800 | ● Amber |
| Alert/Firing/Critical | #FFEBE8 | #CC2A18 | ● Red |
| Indexed/Active/Healthy | #E6F7F1 | #007A54 | ● Green |

**Flow Line Specifications (Professional):**
| Type | Style | Color | Width | Use Case |
|------|-------|-------|-------|----------|
| Data pipeline | Solid → | Blue-600 #2272B4 | 2px | Normal flow |
| Alert dependency | Solid → | Red #FF3621 | 2px | Critical path |
| Warning dependency | Solid → | Amber #FFAB00 | 2px | Degraded path |
| Layer boundary | Double line ━━ | Navy #0B2026 | 1px | Section separation |

**Layer Header Design (Professional Banner):**
```
LayerHeader
├── Container
│   ├── Background: Navy #0B2026 (solid)
│   ├── Border-radius: 6px
│   ├── Padding: 12px 20px
│   └── Margin-bottom: 16px
│
├── Text
│   ├── Layer Name (11px, uppercase, letter-spacing 0.08em, White #FFFFFF, bold 700)
│   └── Right-aligned: [Expand Layer ▼] link (11px, Blue-600 #2272B4)
│
└── Visual Style
    └── Use for: GOVERNANCE, DATA, COMPUTE, ORCHESTRATION, AI & SERVING, CONSUMPTION
```

**Node Hover State:**
- Border: Blue-600 #2272B4 (1px solid)
- Box-shadow: 0 4px 12px rgba(7,122,157,0.15)
- Action link: Darker Blue-700 (#0E538B)
- Cursor: pointer
- Transition: all 0.2s ease

**Node Colors by Layer (Background Accents):**
| Layer | Header Background | Node Border Accent | Usage |
|-------|-------------------|-------------------|-------|
| Governance | Navy #0B2026 | Blue-600 #2272B4 | Unity Catalog |
| Data | Navy #0B2026 | Blue-600 #2272B4 | Schemas |
| Compute | Navy #0B2026 | Status-based (Red/Amber/Green) | SQL WH, Clusters, Serverless |
| Orchestration | Navy #0B2026 | Status-based (Red/Amber/Green) | DLT, Workflows |
| AI & Serving | Navy #0B2026 | Green #00A972 | Model Serving, Vector Search, Genie |
| Consumption | Navy #0B2026 | Status-based (Red/Amber/Green) | Dashboards, Alerts |

**Interactive Features:**
- **Click any node** → Navigate to detail page for that resource
- **Hover over node** → Show tooltip with full metrics and quick actions
- **Click flow line** → Show data lineage and dependencies
- **Layer header expand** → Collapse/expand entire layer
- **Auto-refresh** → Update status indicators every 30s
- **Full screen** → Expand topology to full browser window
- **Export PNG** → Generate static image of current topology

**Professional Design Principles Applied:**
1. **Card-based nodes** (NOT ASCII box art) with proper shadows and borders
2. **Status-driven top borders** (3px colored accent) for immediate health recognition
3. **High-contrast typography** (Navy #0B2026 for all important text)
4. **Professional status chips** with leading dots and proper color semantics
5. **Clean flow lines** (2px solid, colored by path status)
6. **Layer headers** with proper hierarchy (Navy background, white text)
7. **Generous spacing** between layers (24px) and nodes (16px)
8. **Consistent sizing** (min-width 240px, max 300px for uniformity)
9. **Icon + label pattern** for metrics (improved scannability)
10. **Hover states** with subtle Blue-600 accent (interactive affordance)

---

## SECTION 9: COMPONENT SPECIFICATIONS (For Figma Implementation)

### Executive Overview Component Hierarchy

```
ExecutiveOverviewPage
├── AICommandCenter (conversational style with 4px Blue-600 left border)
├── PrimaryMetrics (grid 4-col, colored top borders)
├── DomainHealth (grid 5-col, colored top borders)
├── TrendAnalysis (grid 4-col)
├── ActiveSignals (card-based table, NOT basic rows)
├── AIRecommendations (card list)
└── ResourceTopology (professional service map)
```

## STATES TO INCLUDE:

1. **Default State** - Full dashboard with live data
2. **Loading State** - Skeleton placeholders
3. **Empty State** - New user, no data yet
4. **Alert State** - Multiple critical alerts (red accent)
5. **Comparison Mode** - Showing delta overlays
6. **Command Palette Open** - Modal overlay

---

## KEYBOARD SHORTCUTS (document for devs):

| Shortcut | Action |
|----------|--------|
| `⌘K` / `Ctrl+K` | Open command palette |
| `g h` | Go to home |
| `g e` | Go to explorer |
| `g c` | Go to cost domain |
| `r` | Refresh data |
| `?` | Show shortcuts |

---

## COMPONENTS USED:

| Component | Source | Count |
|-----------|--------|-------|
| Sidebar | 07-composed-navigation | 1 |
| TopBar (enhanced) | 07-composed-navigation | 1 |
| KPITile (lg) | 08-composed-data-display | 4 |
| DomainHealthCard | Custom (Card base) | 5 |
| AlertRow | 08-composed-data-display | 5 |
| InsightCard | 09-composed-ai | 4 |
| Card | 05-primitives-core | Multiple |
| Badge | 05-primitives-core | Multiple |
| Button | 05-primitives-core | Multiple |
| Chip | 05-primitives-core | Multiple |

---

Do NOT:
- Create new components
- Use hardcoded colors
- Add real chart implementations
- Create mobile variants

Focus on:
- Making it feel ALIVE and real-time
- Dense but scannable information hierarchy
- Clear call-to-action for every element
- Professional, enterprise-grade polish
```

---

## 🎯 Expected Output

### Screen Created (1)
- Executive Overview - Command Center Edition (1440px × ~1600px)

### Figma Structure

```
📄 Screens
└── Home
    └── Executive Overview
        ├── Default (live data)
        ├── Loading (skeletons)
        ├── Empty (onboarding)
        ├── Alert State (critical issues)
        └── Comparison Mode
```

---

## ✅ Verification Checklist

- [ ] Command bar with ⌘K, workspace switcher, time picker
- [ ] AI Command Center with proactive insights
- [ ] 4 Hero KPIs with sparklines and live indicators
- [ ] 5 Domain Health Cards with scores and top issues
- [ ] Live Activity Feed with event types
- [ ] Cost Heatmap visualization
- [ ] Enhanced Signals table with correlation
- [ ] AI Recommendations with apply buttons
- [ ] Resource Topology mini-map
- [ ] Real-time feel throughout
- [ ] Professional Datadog/Grafana quality level

---

**Next:** [12-screen-global-explorer.md](12-screen-global-explorer.md)

