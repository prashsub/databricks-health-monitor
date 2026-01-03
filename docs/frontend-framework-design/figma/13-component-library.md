# 13 - Component Library

## Overview

Complete reference of all UI components with their states and variants.

---

## 📋 Component Categories

### A. Navigation Components

```
Design NAVIGATION COMPONENTS.

=== 1. SIDEBAR ===

┌─────────────┐  ┌────┐
│ 🏠 Home     │  │ 🏠 │  ← Collapsed
│ 🔍 Explorer │  │ 🔍 │
│ 💰 Cost     │  │ 💰 │
│ ⚙️ Reliab.  │  │ ⚙️ │
│ ⚡ Perf.    │  │ ⚡ │
│ 🔒 Security │  │ 🔒 │
│ ✅ Quality  │  │ ✅ │
├─────────────┤  ├────┤
│ 📊 Dashbds  │  │ 📊 │
│ 🔔 Alerts   │  │ 🔔 │
│ 💬 Chat     │  │ 💬 │
├─────────────┤  ├────┤
│ ⚙️ Settings │  │ ⚙️ │
└─────────────┘  └────┘
  240px          64px

States: Default, Hover, Active, Collapsed

=== 2. HEADER BAR ===

┌─────────────────────────────────────────────────────────────────────────────────┐
│ [☰] Databricks Health Monitor    [🕐 Last 24h ▼] [🔔 7] [🤖 Ask AI] [⚙️] [👤]  │
└─────────────────────────────────────────────────────────────────────────────────┘
Height: 64px

Components:
- Logo + App name (left)
- Global time picker (center)
- Notification badge
- AI chat trigger
- Settings
- User avatar

=== 3. BREADCRUMBS ===

Home > Cost > ml-workspace > train-llm-v3

States: Clickable links, Current (non-clickable)
```

---

### B. Data Display Components

```
Design DATA DISPLAY COMPONENTS.

=== 1. KPI TILE ===

┌───────────────────┐
│ 💰 Cost Today     │  ← Icon + Label
│                   │
│    $45,230        │  ← Primary Value (24px bold)
│    ↑12% vs yest   │  ← Comparison (14px)
│                   │
│ ▁▂▃▄▅▆▇▆▅▄▃▂▁   │  ← Sparkline (40px)
│                   │
│ 🤖 Anomaly        │  ← AI Insight (12px, blue)
└───────────────────┘
Size: 200px × 160px

States: Default, Hover, Loading, Error, Empty
Click: Navigate to detail

=== 2. ALERT ROW ===

┌────────────────────────────────────────────────────────────────────────────────┐
│ □ │ 🔴 CRIT │ Cost spike: +308% ($4,890/day) │ ml-ws │ 3h │ [Fix][🔕][✕] │
│   │         │ 🤖 Root cause: train-llm-v3    │       │    │              │
└────────────────────────────────────────────────────────────────────────────────┘
Height: 64px (2 lines)

States: Default, Hover, Selected, Muted, Acknowledged

=== 3. STATUS BADGE ===

[🔴 Critical]  [🟠 High]  [🟡 Medium]  [🟢 Low]  [⚪ Info]

Width: Auto (min 64px)
Height: 24px
Border-radius: 12px

=== 4. METRIC CHANGE ===

↑ 12%    ↓ 5%    → 0%
  🔴       🟢       ⚪

Direction + color indicates good/bad
```

---

### C. Input Components

```
Design INPUT COMPONENTS.

=== 1. SEARCH BAR ===

┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🔎 Search signals, workspaces, jobs...                                   [⌘K] │
└─────────────────────────────────────────────────────────────────────────────────┘
Height: 48px

States: Default, Focused, With results, Empty results

=== 2. FILTER CHIP ===

[Workspace: ml-* ✕]  [Severity: High ▼]  [+ Add Filter]

States: Default, Hover, Active, Removable

=== 3. DROPDOWN ===

┌─────────────────────┐
│ Workspace     ▼     │
├─────────────────────┤
│ □ ml-workspace      │  ← Multi-select
│ ☑ prod-etl          │
│ ☑ analytics         │
│ □ dev-sandbox       │
│─────────────────────│
│ [Clear] [Apply]     │
└─────────────────────┘
Width: 200px min

=== 4. TIME PICKER ===

┌──────────────────────────────────────────┐
│ 🕐 Last 24 hours                    ▼   │
├──────────────────────────────────────────┤
│ Quick ranges:                            │
│ [Last 1h] [Last 24h] [Last 7d] [Last 30d]│
│                                          │
│ Custom range:                            │
│ From: [Jan 1, 2026   ] [09:00 AM]       │
│ To:   [Jan 2, 2026   ] [09:00 AM]       │
│                                          │
│ ☐ Compare to previous period             │
│                                          │
│ [Cancel]                        [Apply]  │
└──────────────────────────────────────────┘
```

---

### D. AI Components

```
Design AI COMPONENTS (critical - consistent styling).

=== 1. AI MESSAGE BUBBLE ===

┌──────────────────────────────────────────────────────────────────────────────────┐
│ 🤖 AI Assistant                                                        3:47 PM │
│                                                                                  │
│ I analyzed your ml-workspace cost and found the root cause:                     │
│                                                                                  │
│ ┌────────────────────────────────────────────────────────────────────────────┐  │
│ │ [Embedded visualization - chart or table]                                  │  │
│ └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│ 💭 This is similar to the Dec 15th issue - you fixed it with a timeout.        │
│                                                                                  │
│ Would you like me to:                                                           │
│ [Stop Job] [Add Timeout] [Alert Owner]                                          │
└──────────────────────────────────────────────────────────────────────────────────┘

Components:
- AI avatar (🤖) + name ("AI Assistant") - ALWAYS consistent
- Accent color: #3B82F6 (blue)
- Memory callout: 💭 with #F5F3FF background
- Action buttons

=== 2. AI INSIGHT BANNER ===

┌──────────────────────────────────────────────────────────────────────────────────┐
│ 🤖 Good morning! Here's what I'm tracking:                           [Dismiss] │
│                                                                                  │
│ • 🔴 3 critical issues need attention                                           │
│ • 🟡 I predict ml-workspace will exceed budget by Thursday                     │
│                                                                                  │
│ [Fix Critical Issues] [See Forecast]                                            │
└──────────────────────────────────────────────────────────────────────────────────┘

Styling:
- Border-left: 4px solid #3B82F6
- Background: Gradient from #3B82F6/10 to transparent
- Dismissible (per session)

=== 3. AI MICRO-INSIGHT ===

🤖 Anomaly detected    🤖 Root cause: config    🤖 Save ~$2K
   (on KPI tile)          (on alert row)            (on action)

Size: Small text (12px)
Color: #3B82F6

=== 4. MEMORY CALLOUT ===

┌──────────────────────────────────────────────────────────────────────────────────┐
│ 💭 I remember: You fixed this same issue on Dec 15th by adding a timeout.       │
└──────────────────────────────────────────────────────────────────────────────────┘

Background: #F5F3FF
Border: 1px solid #E9D5FF
Icon: 💭
```

---

### E. Action Components

```
Design ACTION COMPONENTS.

=== 1. PRIMARY BUTTON ===

[Fix Issue]  [Apply]  [Save Changes]

Background: #3B82F6 (or #FF3621 for destructive)
Text: White
Height: 40px
Border-radius: 8px

States: Default, Hover, Active, Disabled, Loading

=== 2. SECONDARY BUTTON ===

[Cancel]  [View Details]  [Export]

Background: Transparent
Border: 1px solid #E5E7EB
Text: #374151
Height: 40px

=== 3. ICON BUTTON ===

[🔕]  [📌]  [✕]  [⋮]  [⚙️]

Size: 32px × 32px
Border-radius: 8px
Hover: Background highlight

=== 4. ACTION CARD ===

┌────────────────────────────────────────────────────────────────────────────────┐
│ 1. Stop the runaway job                                     [▶️ Execute Now]  │
│    Impact: Save ~$2K immediately • Risk: Low • Confidence: 100%               │
│    🤖 This will terminate train-llm-v3 and alert the owner                    │
└────────────────────────────────────────────────────────────────────────────────┘

Height: ~100px
Border: 1px solid #E5E7EB
Hover: Elevate shadow
```

---

### F. Feedback Components

```
Design FEEDBACK COMPONENTS.

=== 1. TOAST NOTIFICATION ===

┌──────────────────────────────────────┐
│ ✅ Job stopped successfully          │  ← Success
│    train-llm-v3 terminated at 3:48PM │
│                              [Undo]  │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ ❌ Failed to stop job                │  ← Error
│    Permission denied                 │
│                        [Retry] [✕]   │
└──────────────────────────────────────┘

Position: Bottom-right
Duration: 5 seconds (auto-dismiss) or manual
Types: Success, Error, Warning, Info

=== 2. EMPTY STATE ===

┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                           📭                                                     │
│                                                                                  │
│              No alerts match your filters                                        │
│                                                                                  │
│        Try adjusting your filters or time range                                  │
│                                                                                  │
│                    [Clear Filters]                                               │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

=== 3. LOADING STATE ===

┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                         ◐ Loading...                                             │
│                    Analyzing your data                                           │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

Types: Spinner, Skeleton, Progress bar

=== 4. ERROR STATE ===

┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                           ⚠️                                                      │
│                                                                                  │
│                  Failed to load data                                             │
│                                                                                  │
│        There was an error connecting to the workspace.                           │
│                                                                                  │
│                    [Retry]  [Contact Support]                                    │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Design Tokens

### Colors
```
Primary:       #FF3621 (Databricks Red)
AI:            #3B82F6 (Blue)
Success:       #10B981 (Green)
Warning:       #F59E0B (Amber)
Error:         #EF4444 (Red)
Critical:      #DC2626 (Dark Red)

Background:    #0F0F10 (dark) / #FAFAFA (light)
Surface:       #1A1A1B (dark) / #FFFFFF (light)
Border:        #27272A (dark) / #E5E7EB (light)
Text:          #FAFAFA (dark) / #111827 (light)
Text Muted:    #A1A1AA (dark) / #6B7280 (light)
```

### Typography
```
Font Family:   Inter (UI), JetBrains Mono (code/numbers)

Display:       32px / 700 / 1.2
Heading 1:     24px / 600 / 1.3
Heading 2:     20px / 600 / 1.3
Heading 3:     16px / 600 / 1.4
Body:          14px / 400 / 1.5
Small:         12px / 400 / 1.5
Caption:       11px / 400 / 1.4
```

### Spacing
```
4px  - Micro spacing (icon padding)
8px  - Small spacing
12px - Component internal padding
16px - Standard spacing
24px - Section spacing
32px - Large spacing
48px - Section separation
```

### Border Radius
```
4px  - Buttons, inputs
8px  - Cards, panels
12px - Large cards, tiles
16px - Modal corners
Full - Badges, avatars
```

---

## ✅ Component Checklist

### Navigation
- [ ] Sidebar (expanded/collapsed)
- [ ] Header bar
- [ ] Breadcrumbs
- [ ] Tab bar

### Data Display
- [ ] KPI tile
- [ ] Alert row
- [ ] Status badge
- [ ] Metric change

### Inputs
- [ ] Search bar
- [ ] Filter chip
- [ ] Dropdown
- [ ] Time picker

### AI Components
- [ ] AI message bubble
- [ ] AI insight banner
- [ ] AI micro-insight
- [ ] Memory callout

### Actions
- [ ] Primary button
- [ ] Secondary button
- [ ] Icon button
- [ ] Action card

### Feedback
- [ ] Toast notification
- [ ] Empty state
- [ ] Loading state
- [ ] Error state

---

## 📚 PRD Reference

For detailed component specifications, see: [../prd/01-base-prd.md](../prd/01-base-prd.md) - Section 6: Component Library

---

**You've completed all Figma guides! 🎉**

Return to [00-getting-started.md](00-getting-started.md) to review the complete design sequence.

