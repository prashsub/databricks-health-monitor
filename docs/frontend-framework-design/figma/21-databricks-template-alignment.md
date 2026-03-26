# Prompt 21: Databricks Template Alignment Guide

> **Note: Outdated Frontend Stack References**
> This document references Next.js 14+ and/or Vercel AI SDK as the frontend stack.
> The actual implementation uses **FastAPI + React/Vite** deployed as a Databricks App.
> Treat frontend-specific sections as superseded design docs; the backend architecture
> and data platform sections remain accurate.


## 🎯 Purpose
Ensure Figma designs align with the official [Databricks e2e-chatbot-app-next template](https://github.com/databricks/app-templates/tree/main/e2e-chatbot-app-next) for seamless deployment to Databricks Apps.

---

## 📦 Template Tech Stack

Based on official Databricks app template patterns:

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.x | React framework with App Router |
| **React** | 18.x | UI library |
| **TypeScript** | 5.x | Type safety |
| **Tailwind CSS** | 3.x | Utility-first styling |
| **Vercel AI SDK** | Latest | Streaming chat, AI responses |
| **Lucide React** | Latest | Icon library |

### Deployment Configuration
- **`app.yaml`** - Databricks app runtime config
- **`package.json`** - Node.js dependencies
- **Port**: 8000 (Databricks Apps default)
- **Build command**: `npm run build`
- **Start command**: `npm run start`

---

## 🔧 Figma-to-Code Alignment Requirements

### 1. Tailwind CSS Token Mapping (Updated Color System)

**Aligned with Databricks Color Themes (02-tokens-colors.md):**

| Figma Token | Hex Value | Tailwind Class | CSS Variable |
|-------------|-----------|----------------|--------------|
| `interactive/primary` | #2272B4 (Blue-600) ✅ | `text-blue-600` / `bg-blue-600` | `--color-primary` |
| `brand/secondary` | #143D4A (Navy-700) ✅ | `text-db-navy` / `bg-db-navy` | `--color-secondary` |
| `brand/lava` | #FF3621 (Lava-600) ✅ | `text-db-lava` | `--color-accent` |
| `background/canvas` | #F5F2ED | `bg-db-cream` | `--color-bg-canvas` |
| `background/surface` | #FFFFFF | `bg-white` | `--color-bg-surface` |
| `background/surface-alt` | #EEEDE9 (Oat-medium) ✅ | `bg-db-oat-medium` | `--color-bg-subtle` |
| `text/primary` | #0B2026 (Navy-900) ✅ | `text-db-navy-900` | `--color-text-primary` |
| `neutral/slate` | #4A5D6B | `text-db-slate` | `--color-text-secondary` |
| `neutral/steel` | #6B7D8A | `text-db-steel` | `--color-text-muted` |
| `border/default` | #E0E6EB | `border-db-mist` | `--color-border-default` |
| `semantic/critical` | #FF3621 | `text-db-red` / `bg-red-500` | `--color-critical` |
| `semantic/warning` | #FFAB00 | `text-db-amber` / `bg-amber-500` | `--color-warning` |
| `semantic/success` | #00A972 | `text-db-green` / `bg-emerald-500` | `--color-success` |
| `semantic/info` | #2272B4 (Blue-600) ✅ | `text-blue-600` / `bg-blue-600` | `--color-info` |

**Custom Tailwind Config (tailwind.config.js):**

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        // Official Databricks colors ✅
        'db-blue': '#2272B4',        // Blue-600 - PRIMARY interactive
        'db-navy': '#143D4A',        // Navy-700
        'db-navy-900': '#0B2026',    // Navy-900 - PRIMARY text
        'db-coral': '#E8715E',
        'db-red': '#FF3621',
        'db-green': '#00A972',
        'db-amber': '#FFAB00',
        'db-cream': '#F5F2ED',
        'db-offwhite': '#FAF9F7',
        'db-slate': '#4A5D6B',
        'db-steel': '#6B7D8A',
        'db-mist': '#E0E6EB',
      }
    }
  }
}
```

### 2. Component Naming Conventions

**Figma component names must map to file paths:**

#### Primitives (`components/ui/`)

| Figma Component | File Path | Export |
|-----------------|-----------|--------|
| `Button` | `components/ui/button.tsx` | `Button` |

**Button Variants (CRITICAL for Contrast):**

| Variant | Background | Border | Text | Tailwind Classes |
|---------|------------|--------|------|------------------|
| `primary` | `#2272B4` (Blue-600) ✅ | None | `#FFFFFF` (White) | `bg-blue-600 text-white` |
| `secondary` | Transparent | `#143D4A` (Navy-700) ✅ | `#0B2026` (Navy-900) ✅ | `border-db-navy text-db-navy-900` |
| `gray-outline` | Transparent | `#DCE0E2` (Gray-lines) ✅ | `#0B2026` (Navy-900) ✅ | `border-gray-300 text-db-navy-900` |
| `ghost` | Transparent | None | `#618794` (Navy-500) ✅ | `text-db-navy-500 hover:bg-gray-100` |
| `destructive` | `#FF3621` (Lava-600) ✅ | None | `#FFFFFF` (White) | `bg-db-lava text-white` |
| `link` | Transparent | None | `#2272B4` (Blue-600) ✅ | `text-blue-600 underline-offset-4` |

**Note:** Gray-outline buttons use Navy-900 text (`#0B2026`) for WCAG AA contrast compliance on white backgrounds. Never use gray text on gray-bordered buttons.

| `Badge` | `components/ui/badge.tsx` | `Badge` |
| `Card` | `components/ui/card.tsx` | `Card` |
| `Input` | `components/ui/input.tsx` | `Input` |
| `Table` | `components/ui/table.tsx` | `Table` |
| `Chip` | `components/ui/chip.tsx` | `Chip` |
| `Avatar` | `components/ui/avatar.tsx` | `Avatar` |
| `Tooltip` | `components/ui/tooltip.tsx` | `Tooltip` |
| `Skeleton` | `components/ui/skeleton.tsx` | `Skeleton` |
| `Spinner` | `components/ui/spinner.tsx` | `Spinner` |
| `ProgressBar` | `components/ui/progress-bar.tsx` | `ProgressBar` |
| `StatusIndicator` | `components/ui/status-indicator.tsx` | `StatusIndicator` |

#### Layout (`components/layout/`)

| Figma Component | File Path | Export |
|-----------------|-----------|--------|
| `Sidebar` | `components/layout/sidebar.tsx` | `Sidebar` |
| `TopBar` | `components/layout/top-bar.tsx` | `TopBar` |
| `Breadcrumb` | `components/layout/breadcrumb.tsx` | `Breadcrumb` |
| `TabBar` | `components/layout/tab-bar.tsx` | `TabBar` |
| `ThreePanelLayout` | `components/layout/three-panel-layout.tsx` | `ThreePanelLayout` |

#### Dashboard (`components/dashboard/`)

| Figma Component | File Path | Export |
|-----------------|-----------|--------|
| `KPITile` | `components/dashboard/kpi-tile.tsx` | `KPITile` |
| `MetricCard` | `components/dashboard/metric-card.tsx` | `MetricCard` |
| `AlertRow` | `components/dashboard/alert-row.tsx` | `AlertRow` |
| `TrendCard` | `components/dashboard/trend-card.tsx` | `TrendCard` |
| `DomainCard` | `components/dashboard/domain-card.tsx` | `DomainCard` |
| `ActivityFeed` | `components/dashboard/activity-feed.tsx` | `ActivityFeed` |
| `ProactiveActionCard` | `components/dashboard/proactive-action-card.tsx` | `ProactiveActionCard` |

#### Chat/AI (`components/chat/`)

| Figma Component | File Path | Export |
|-----------------|-----------|--------|
| `ChatBubble` | `components/chat/chat-bubble.tsx` | `ChatBubble` |
| `ChatInput` | `components/chat/chat-input.tsx` | `ChatInput` |
| `ToolCallPanel` | `components/chat/tool-call-panel.tsx` | `ToolCallPanel` |
| `InsightCallout` | `components/chat/insight-callout.tsx` | `InsightCallout` |
| `SuggestedQuestion` | `components/chat/suggested-question.tsx` | `SuggestedQuestion` |
| `MemoryPanel` | `components/chat/memory-panel.tsx` | `MemoryPanel` |
| `ContextPanel` | `components/chat/context-panel.tsx` | `ContextPanel` |
| `AICommandCenter` | `components/chat/ai-command-center.tsx` | `AICommandCenter` |

#### Charts (`components/charts/`)

| Figma Component | File Path | Export |
|-----------------|-----------|--------|
| `ChartCard` | `components/charts/chart-card.tsx` | `ChartCard` |
| `TimelineChart` | `components/charts/timeline-chart.tsx` | `TimelineChart` |
| `BlastRadiusGraph` | `components/charts/blast-radius-graph.tsx` | `BlastRadiusGraph` |

#### Signals (`components/signals/`) - NEW

| Figma Component | File Path | Export |
|-----------------|-----------|--------|
| `SignalRow` | `components/signals/signal-row.tsx` | `SignalRow` |
| `StatusTimeline` | `components/signals/status-timeline.tsx` | `StatusTimeline` |
| `EventTimeline` | `components/signals/event-timeline.tsx` | `EventTimeline` |
| `HypothesisCard` | `components/signals/hypothesis-card.tsx` | `HypothesisCard` |
| `EvidenceSection` | `components/signals/evidence-section.tsx` | `EvidenceSection` |
| `WhatChanged` | `components/signals/what-changed.tsx` | `WhatChanged` |
| `ResolutionPath` | `components/signals/resolution-path.tsx` | `ResolutionPath` |
| `ActivityComments` | `components/signals/activity-comments.tsx` | `ActivityComments` |

#### Overlays (`components/overlays/`)

| Figma Component | File Path | Export |
|-----------------|-----------|--------|
| `Modal` | `components/overlays/modal.tsx` | `Modal` |
| `Drawer` | `components/overlays/drawer.tsx` | `Drawer` |
| `Dropdown` | `components/overlays/dropdown.tsx` | `Dropdown` |
| `Toast` | `components/overlays/toast.tsx` | `Toast` |
| `CommandPalette` | `components/overlays/command-palette.tsx` | `CommandPalette` |
| `DateRangePicker` | `components/overlays/date-range-picker.tsx` | `DateRangePicker` |
| `AssigneePicker` | `components/overlays/assignee-picker.tsx` | `AssigneePicker` |
| `SnoozePicker` | `components/overlays/snooze-picker.tsx` | `SnoozePicker` |
| `MultiStepModal` | `components/overlays/multi-step-modal.tsx` | `MultiStepModal` |
| `QueryProfileDrawer` | `components/overlays/query-profile-drawer.tsx` | `QueryProfileDrawer` |
| `ComparePeriodPicker` | `components/overlays/compare-period-picker.tsx` | `ComparePeriodPicker` |
| `AIFeedbackModal` | `components/overlays/ai-feedback-modal.tsx` | `AIFeedbackModal` |

### 3. File Structure Alignment (Super-Enhanced)

```
app/                          # Next.js 14 App Router
├── (dashboard)/              # Dashboard route group
│   ├── page.tsx              # Executive Overview (Screen 11)
│   ├── explorer/
│   │   └── page.tsx          # Global Explorer (Screen 12)
│   ├── cost/
│   │   └── page.tsx          # Cost Domain (Screen 13)
│   ├── reliability/
│   │   └── page.tsx          # Reliability Domain (Screen 13)
│   ├── performance/
│   │   └── page.tsx          # Performance Domain (Screen 13)
│   ├── governance/
│   │   └── page.tsx          # Governance Domain (Screen 13)
│   ├── quality/
│   │   └── page.tsx          # Data Quality Domain (Screen 13)
│   ├── signals/
│   │   └── [id]/
│   │       └── page.tsx      # Signal Detail (Screen 14)
│   ├── chat/
│   │   └── page.tsx          # AI Chat Interface (Screen 15)
│   ├── alerts/
│   │   ├── page.tsx          # Alert Center (Screen 16)
│   │   ├── rules/
│   │   │   └── page.tsx      # Alert Rules Tab
│   │   ├── channels/
│   │   │   └── page.tsx      # Notification Channels Tab
│   │   └── routing/
│   │       └── page.tsx      # Routing Rules Tab
│   └── settings/
│       ├── page.tsx          # Settings Hub (Screen 17)
│       ├── workspaces/
│       │   └── page.tsx      # Workspaces Management
│       ├── users/
│       │   └── page.tsx      # Users & Teams
│       ├── ai/
│       │   └── page.tsx      # AI Assistant Settings
│       ├── integrations/
│       │   └── page.tsx      # Integrations
│       └── audit/
│           └── page.tsx      # Audit Logs
├── api/                      # API routes
│   ├── chat/
│   │   └── route.ts          # AI chat endpoint (Vercel AI SDK)
│   ├── signals/
│   │   ├── route.ts          # Signals list API
│   │   └── [id]/
│   │       ├── route.ts      # Signal detail API
│   │       ├── actions/
│   │       │   └── route.ts  # Execute actions
│   │       └── comments/
│   │           └── route.ts  # Activity comments
│   ├── alerts/
│   │   ├── route.ts          # Alerts API
│   │   └── rules/
│   │       └── route.ts      # Alert rules CRUD
│   ├── metrics/
│   │   └── route.ts          # Dashboard metrics
│   ├── memory/
│   │   └── route.ts          # AI memory CRUD
│   └── feedback/
│       └── route.ts          # AI feedback endpoint
├── layout.tsx                # Root layout with Sidebar
└── globals.css               # Global styles + Tailwind

components/
├── ui/                       # Primitives (Figma: Components/Primitives)
│   ├── button.tsx
│   ├── badge.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── table.tsx
│   ├── chip.tsx
│   ├── avatar.tsx
│   ├── tooltip.tsx
│   ├── skeleton.tsx
│   ├── spinner.tsx
│   ├── progress-bar.tsx
│   └── status-indicator.tsx
├── layout/                   # Navigation (Figma: Components/Composed/Navigation)
│   ├── sidebar.tsx
│   ├── top-bar.tsx
│   ├── breadcrumb.tsx
│   ├── tab-bar.tsx
│   └── three-panel-layout.tsx  # NEW: Chat interface layout
├── dashboard/                # Data Display (Figma: Components/Composed/DataDisplay)
│   ├── kpi-tile.tsx
│   ├── metric-card.tsx
│   ├── alert-row.tsx
│   ├── trend-card.tsx
│   ├── domain-card.tsx         # NEW: Domain health cards
│   ├── activity-feed.tsx       # NEW: Recent activity
│   └── proactive-action-card.tsx # NEW: AI recommendations
├── chat/                     # AI Components (Figma: Components/Composed/AI)
│   ├── chat-bubble.tsx
│   ├── chat-input.tsx
│   ├── tool-call-panel.tsx     # Renamed from tool-panel
│   ├── insight-callout.tsx     # Renamed from insight-card
│   ├── suggested-question.tsx
│   ├── memory-panel.tsx        # NEW: Memory management
│   ├── context-panel.tsx       # NEW: Context display
│   └── ai-command-center.tsx   # NEW: AI input banner
├── signals/                  # Signal Components (NEW)
│   ├── signal-row.tsx          # Rich signal row
│   ├── status-timeline.tsx     # Status progression
│   ├── event-timeline.tsx      # Detailed events
│   ├── hypothesis-card.tsx     # Root cause hypotheses
│   ├── evidence-section.tsx    # Query profile, metrics, logs
│   ├── what-changed.tsx        # Correlation panel
│   ├── resolution-path.tsx     # Step-by-step resolution
│   └── activity-comments.tsx   # Comments feed
├── charts/                   # Charts (Figma: Components/Composed/Charts)
│   ├── chart-card.tsx
│   ├── timeline-chart.tsx      # NEW: Event timeline visualization
│   └── blast-radius-graph.tsx  # NEW: Impact visualization
└── overlays/                 # Overlays (Figma: Components/Overlays)
    ├── modal.tsx
    ├── drawer.tsx
    ├── dropdown.tsx
    ├── toast.tsx
    ├── command-palette.tsx
    ├── date-range-picker.tsx
    ├── assignee-picker.tsx       # NEW: User/team picker
    ├── snooze-picker.tsx         # NEW: Duration presets
    ├── multi-step-modal.tsx      # NEW: Resolution execution
    ├── query-profile-drawer.tsx  # NEW: Query analysis
    ├── compare-period-picker.tsx # NEW: Time comparison
    └── ai-feedback-modal.tsx     # NEW: Feedback collection

lib/
├── databricks.ts             # Databricks SDK client
├── api.ts                    # API utilities
├── utils.ts                  # General utilities
├── memory.ts                 # AI memory utilities (NEW)
└── actions.ts                # Action execution utilities (NEW)

hooks/
├── use-signals.ts            # Signals data hook
├── use-metrics.ts            # Metrics data hook
├── use-chat.ts               # Chat state hook
├── use-memory.ts             # Memory state hook (NEW)
└── use-compare.ts            # Compare mode hook (NEW)

types/
├── signal.ts                 # Signal types
├── metric.ts                 # Metric types
├── alert.ts                  # Alert types
├── chat.ts                   # Chat message types
├── memory.ts                 # Memory types (NEW)
└── action.ts                 # Action types (NEW)
```

---

## 🎨 Figma Make Adjustments

### Update Prompt 01 (Guidelines Context)

Add these Databricks-specific guidelines to your `Guidelines.md`:

```markdown
## Databricks Apps Integration

### Deployment Target
- Platform: Databricks Apps
- Framework: Next.js 14 with App Router
- Styling: Tailwind CSS
- Icons: Lucide React (NOT custom icons)

### Component Architecture
Components follow shadcn/ui patterns:
- Primitives in `components/ui/`
- Composed components in feature folders
- Server Components by default, "use client" where needed

### Tailwind Mapping
All Figma tokens MUST map to Tailwind utilities:
- Colors: Use Tailwind color palette (gray-50, gray-100, etc.)
- Spacing: 4px = 1 unit (p-1, m-1, gap-1)
- Typography: text-sm, text-base, text-lg, font-medium, etc.
- Shadows: shadow-sm, shadow-md, shadow-lg

### AI Chat Integration
Chat components must support:
- Streaming responses (Vercel AI SDK)
- Tool call rendering (expandable panels)
- Message actions (copy, feedback)
- Markdown rendering in responses
```

### Update Prompt 09 (AI Components)

Ensure chat components match Vercel AI SDK patterns:

```
ChatBubble must support:
- User messages (right-aligned)
- Assistant messages (left-aligned, with avatar)
- Streaming state (typing indicator with animated dots)
- Tool calls (collapsible panel showing: name, status, result)
- Actions (copy, thumbs up/down, regenerate)
- Markdown rendering (headings, lists, code blocks, tables)

ChatInput must support:
- Multi-line textarea with auto-resize
- Send button (disabled when empty)
- Attachment button (optional)
- "Shift+Enter for new line" hint
- Character count (optional)
```

---

## 📝 Additional Figma Pages to Create

### Page: Code Handoff

Create a Figma page specifically for developer handoff:

```
📄 Code Handoff
├── Tailwind Mapping Reference
│   ├── Colors → Tailwind classes
│   ├── Typography → Tailwind classes
│   ├── Spacing → Tailwind classes
│   └── Shadows → Tailwind classes
│
├── Component → File Mapping
│   ├── Primitives → components/ui/
│   ├── Layout → components/layout/
│   ├── Dashboard → components/dashboard/
│   ├── Chat → components/chat/
│   └── Overlays → components/overlays/
│
└── Screen → Route Mapping
    ├── Executive Overview → /
    ├── Global Explorer → /explorer
    ├── Cost Domain → /cost
    ├── Signal Detail → /signals/[id]
    ├── AI Chat → /chat
    ├── Alert Center → /alerts
    └── Settings → /settings
```

---

## 🔌 API Endpoints to Design For (Super-Enhanced)

Your UI should be designed with these endpoints in mind:

### Core Endpoints

| Endpoint | Method | Purpose | UI Component |
|----------|--------|---------|--------------|
| `/api/chat` | POST | AI conversation | ChatInput → ChatBubble |
| `/api/signals` | GET | List signals | Global Explorer table |
| `/api/signals/[id]` | GET | Signal detail | Signal Detail page |
| `/api/alerts` | GET/POST | Alert rules | Alert Center |
| `/api/metrics` | GET | Dashboard metrics | KPITile, ChartCard |
| `/api/workspaces` | GET | Workspace list | Settings, filters |

### Super-Enhanced Endpoints (NEW)

| Endpoint | Method | Purpose | UI Component |
|----------|--------|---------|--------------|
| `/api/signals/[id]/actions` | POST | Execute action step | ResolutionPath, MultiStepModal |
| `/api/signals/[id]/actions/bulk` | POST | Execute all steps | MultiStepModal |
| `/api/signals/[id]/assign` | PATCH | Assign signal | AssigneePicker |
| `/api/signals/[id]/snooze` | PATCH | Snooze signal | SnoozePicker |
| `/api/signals/[id]/status` | PATCH | Update status | StatusTimeline |
| `/api/signals/[id]/comments` | GET/POST | Activity comments | ActivityComments |
| `/api/signals/[id]/hypotheses` | GET | Root cause analysis | HypothesisCard |
| `/api/signals/[id]/evidence` | GET | Evidence data | EvidenceSection |
| `/api/signals/[id]/correlation` | GET | What changed data | WhatChanged |
| `/api/signals/[id]/blast-radius` | GET | Impact graph | BlastRadiusGraph |
| `/api/memory` | GET/POST/DELETE | AI memory CRUD | MemoryPanel |
| `/api/feedback` | POST | AI feedback | AIFeedbackModal |
| `/api/chat/regenerate` | POST | Regenerate response | ChatBubble |
| `/api/metrics/compare` | GET | Compare periods | ComparePeriodPicker |
| `/api/users/search` | GET | Search users | AssigneePicker |
| `/api/teams` | GET | Team list | AssigneePicker |
| `/api/views` | GET/POST/DELETE | Saved views | Global Explorer |
| `/api/alerts/rules` | GET/POST/PUT/DELETE | Alert rules CRUD | Alert Center |
| `/api/alerts/channels` | GET/POST/PUT/DELETE | Notification channels | Alert Center |
| `/api/alerts/routing` | GET/POST/PUT/DELETE | Routing rules | Alert Center |
| `/api/audit` | GET | Audit logs | Settings Audit page |

### WebSocket Endpoints (Real-time updates)

| Endpoint | Purpose | UI Component |
|----------|---------|--------------|
| `ws://api/signals/stream` | Real-time signal updates | Global Explorer |
| `ws://api/chat/stream` | Streaming AI responses | ChatBubble |
| `ws://api/metrics/stream` | Real-time metric updates | KPITile, ChartCard |

---

## ✅ Pre-Development Checklist (Super-Enhanced)

Before starting code implementation from Figma:

### Figma Preparation
- [ ] All tokens exported as CSS variables
- [ ] Component names match file paths (see Section 2)
- [ ] Variants documented with TypeScript props
- [ ] Responsive breakpoints noted (1440px, 1024px, 768px)
- [ ] Icons are Lucide names (not custom) - see 132 icons in Prompt 20

### Super-Enhanced Components Verified
- [ ] AI Command Center component exists
- [ ] Signal components (8 total) created
- [ ] New overlay components (6 total) created
- [ ] Three-panel layout for Chat verified
- [ ] Resolution Path with step states exists
- [ ] Compare Period Picker with presets exists

### Databricks Setup
- [ ] Workspace with Apps enabled
- [ ] SQL Warehouse for queries
- [ ] Model Serving endpoint for AI (unified agent)
- [ ] Unity Catalog tables configured
- [ ] Service principal with permissions
- [ ] Lakebase tables for memory (short-term, long-term)
- [ ] Vector Search index for Runbook RAG

### Backend Integrations
- [ ] 60+ TVFs available for AI tools
- [ ] 155+ custom metrics configured
- [ ] 56 SQL Alert V2 rules deployed
- [ ] 25 ML models in Unity Catalog
- [ ] Tavily API key for web search

### Development Environment
- [ ] Node.js 18+ installed
- [ ] Databricks CLI configured
- [ ] Environment variables set:
  - `DATABRICKS_HOST`
  - `DATABRICKS_TOKEN`
  - `DATABRICKS_WAREHOUSE_ID`
  - `DATABRICKS_SERVING_ENDPOINT`
  - `TAVILY_API_KEY`
  - `LAKEBASE_MEMORY_TABLE`

---

## 🚀 Deployment Validation

### app.yaml Configuration

```yaml
# Databricks Apps configuration
command:
  - "npm"
  - "run"
  - "start"

env:
  - name: DATABRICKS_HOST
    valueFrom:
      secret: databricks-host
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom:
      secret: warehouse-id
  - name: MODEL_SERVING_ENDPOINT
    valueFrom:
      secret: model-endpoint
```

### package.json Scripts

```json
{
  "scripts": {
    "dev": "next dev -p 8000",
    "build": "next build",
    "start": "next start -p 8000",
    "lint": "next lint"
  }
}
```

---

---

## 🆕 Super-Enhanced Feature Summary

### New Component Categories Added

| Category | Count | Key Components |
|----------|-------|----------------|
| **Signals** | 8 | StatusTimeline, EventTimeline, HypothesisCard, EvidenceSection, WhatChanged, ResolutionPath |
| **Overlays (New)** | 6 | AssigneePicker, SnoozePicker, MultiStepModal, QueryProfileDrawer, ComparePeriodPicker, AIFeedbackModal |
| **Dashboard (New)** | 3 | DomainCard, ActivityFeed, ProactiveActionCard |
| **Chat (New)** | 3 | MemoryPanel, ContextPanel, AICommandCenter |
| **Charts (New)** | 2 | TimelineChart, BlastRadiusGraph |
| **Layout (New)** | 1 | ThreePanelLayout |

### New Icon Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Resolution | 12 | Multi-step workflows |
| Evidence | 10 | Analysis and correlation |
| Time | 8 | Scheduling and comparison |
| View | 10 | View mode toggles |
| Interaction | 8 | Save, pin, voice features |

**Total Icons:** 132 (was 89, +43 new)

### New API Endpoints

- **Signal Actions:** 10 endpoints for actions, assignment, status, comments
- **AI Features:** 3 endpoints for memory, feedback, regeneration
- **Comparison:** 1 endpoint for period comparison
- **Search:** 2 endpoints for user and team search
- **Alert Management:** 9 endpoints for rules, channels, routing

### Key Architectural Changes

1. **Three-Panel Layout** - Chat interface with history, chat, and context panels
2. **Resolution Path** - Step-by-step execution with progress tracking
3. **Compare Mode** - Time period comparison across all metrics
4. **Memory System** - AI short-term and long-term memory management
5. **Evidence Section** - Query profile, metrics, logs in signal detail

---

## 📚 References

- [Databricks Apps Documentation](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/)
- [e2e-chatbot-app-next Template](https://github.com/databricks/app-templates/tree/main/e2e-chatbot-app-next)
- [Vercel AI SDK Documentation](https://sdk.vercel.ai/docs)
- [Next.js 14 App Router](https://nextjs.org/docs/app)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev/icons)
- [shadcn/ui Components](https://ui.shadcn.com/)

---

## 🔗 Related Documents

- [11-screen-executive-overview.md](11-screen-executive-overview.md) - AI Command Center, Compare Mode
- [12-screen-global-explorer.md](12-screen-global-explorer.md) - Smart tabs, Saved views, Facets
- [13-screen-domain-pages.md](13-screen-domain-pages.md) - Domain AI, ML Insights
- [14-screen-signal-detail.md](14-screen-signal-detail.md) - Resolution Path, Evidence
- [15-screen-chat-interface.md](15-screen-chat-interface.md) - Memory Panel, Context Panel
- [18-overlays-modals.md](18-overlays-modals.md) - 6 new overlay components
- [19-prototype-flows.md](19-prototype-flows.md) - 10 user journey scenarios
- [20-icons-assets.md](20-icons-assets.md) - 132 icons organized in 13 categories
