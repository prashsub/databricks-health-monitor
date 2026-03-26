# Databricks Health Monitor - Figma Design System

> **Note: Outdated Frontend Stack References**
> This document references Next.js 14+ and/or Vercel AI SDK as the frontend stack.
> The actual implementation uses **FastAPI + React/Vite** deployed as a Databricks App.
> Treat frontend-specific sections as superseded design docs; the backend architecture
> and data platform sections remain accurate.


## 🎯 Project Overview

**Product:** Databricks Health Monitoring Platform  
**Type:** Enterprise Platform Observability Dashboard  
**Tech Stack:** Next.js 14, React 18, TypeScript, Databricks Apps  
**Target Users:** Platform Engineers, Data Analysts, Security Teams  

---

## 📋 Build Sequence (22 Total Prompts)

### Phase 1: Foundation (4 prompts, ~30 min)

| Order | File | Scope | Figma Output |
|-------|------|-------|--------------|
| 1 | [01-guidelines-context.md](01-guidelines-context.md) | Guidelines.md + context | Paste into Figma project |
| 2 | [02-tokens-colors.md](02-tokens-colors.md) | 40+ color variables | Color styles/variables |
| 3 | [03-tokens-typography.md](03-tokens-typography.md) | 20+ text styles | Typography styles |
| 4 | [04-tokens-spacing.md](04-tokens-spacing.md) | 15+ spacing variables | Spacing variables + grid |

### Phase 2: Components (7 prompts, ~60 min)

| Order | File | Scope | Components |
|-------|------|-------|------------|
| 5 | [05-primitives-core.md](05-primitives-core.md) | Core primitives | Button, Badge, Card, Input, Chip, Avatar |
| 6 | [06-primitives-data.md](06-primitives-data.md) | Data primitives | Table, Tooltip, Skeleton, Spinner, ProgressBar, StatusIndicator |
| 7 | [07-composed-navigation.md](07-composed-navigation.md) | Navigation | Sidebar, TopBar, Breadcrumb, TabBar |
| 8 | [08-composed-data-display.md](08-composed-data-display.md) | Data display | KPITile, MetricCard, AlertRow, TrendCard |
| 9 | [09-composed-ai.md](09-composed-ai.md) | AI/Chat | ChatBubble, ChatInput, ToolPanel, InsightCard, ActionCard |
| 10 | [10-composed-charts.md](10-composed-charts.md) | Charts | ChartCard (6 chart type variants), ChartLegend, ChartTooltip |
| 18 | [18-overlays-modals.md](18-overlays-modals.md) | **Overlays** | Modal, Drawer, Dropdown, Toast, CommandPalette, DateRangePicker |

### Phase 3: Screens (7 prompts, ~60 min)

| Order | File | Scope | Screen(s) |
|-------|------|-------|-----------|
| 11 | [11-screen-executive-overview.md](11-screen-executive-overview.md) | Executive Overview | 1 screen (4 states) |
| 12 | [12-screen-global-explorer.md](12-screen-global-explorer.md) | Global Explorer | 1 screen (5 states) |
| 13 | [13-screen-domain-pages.md](13-screen-domain-pages.md) | Domain Pages | 5 screens (Cost, Reliability, Performance, Governance, Quality) |
| 14 | [14-screen-signal-detail.md](14-screen-signal-detail.md) | Signal Detail | 1 screen (4 states) |
| 15 | [15-screen-chat-interface.md](15-screen-chat-interface.md) | AI Chat | 1 screen (4 states) |
| 16 | [16-screen-alert-center.md](16-screen-alert-center.md) | Alert Center | 1 screen (3 tabs + modal) |
| 17 | [17-screen-settings.md](17-screen-settings.md) | Settings & Admin | 1 screen (5 sections) |

### Phase 4: Interactivity & Handoff (4 prompts, ~50 min)

| Order | File | Scope | Output |
|-------|------|-------|--------|
| 19 | [19-prototype-flows.md](19-prototype-flows.md) | **Navigation Flows** | All click targets, transitions, user journeys |
| 20 | [20-icons-assets.md](20-icons-assets.md) | **Icons & Assets** | 80+ icons (Lucide), logo variants, illustrations |
| 21 | [21-databricks-template-alignment.md](21-databricks-template-alignment.md) | **Template Alignment** | Code handoff mapping, Tailwind tokens, file structure |
| 22 | [22-figma-to-code-mapping.md](22-figma-to-code-mapping.md) | **Data Mapping** | UI element → data source, TVF, API route, agent tool |

---

## 🏗️ Architecture for MCP Extraction

### Figma Page Structure (Create This First)

```
📄 Databricks Health Monitor
├── 🎨 Tokens
│   ├── Colors
│   ├── Typography  
│   └── Spacing
├── 🧱 Components
│   ├── Primitives/
│   │   ├── Button
│   │   ├── Badge
│   │   ├── Card
│   │   ├── Input
│   │   ├── Chip
│   │   ├── Avatar
│   │   ├── Table
│   │   ├── Tooltip
│   │   ├── Skeleton
│   │   ├── Spinner
│   │   ├── ProgressBar
│   │   └── StatusIndicator
│   ├── Composed/
│   │   ├── Navigation/
│   │   ├── DataDisplay/
│   │   ├── AI/
│   │   └── Charts/
│   └── Overlays/
│       ├── Modal
│       ├── Drawer
│       ├── Dropdown
│       ├── Toast
│       ├── CommandPalette
│       └── DateRangePicker
├── 📄 Screens
│   ├── Overview
│   ├── GlobalExplorer
│   ├── Domains/
│   │   ├── Cost
│   │   ├── Reliability
│   │   ├── Performance
│   │   ├── Governance
│   │   └── DataQuality
│   ├── SignalDetail
│   ├── Chat
│   ├── AlertCenter
│   └── Settings
└── 🎨 Assets
    ├── Icons
    ├── Logos
    └── Illustrations
```

### Component → Code Mapping

| Figma Component | Code Path |
|-----------------|-----------|
| `Button` | `components/primitives/Button.tsx` |
| `Badge` | `components/primitives/Badge.tsx` |
| `Card` | `components/primitives/Card.tsx` |
| `Input` | `components/primitives/Input.tsx` |
| `Table` | `components/primitives/Table.tsx` |
| `Modal` | `components/overlays/Modal.tsx` |
| `Drawer` | `components/overlays/Drawer.tsx` |
| `Dropdown` | `components/overlays/Dropdown.tsx` |
| `Toast` | `components/overlays/Toast.tsx` |
| `KPITile` | `components/composed/DataDisplay/KPITile.tsx` |
| `AlertRow` | `components/composed/DataDisplay/AlertRow.tsx` |
| `ChatBubble` | `components/composed/AI/ChatBubble.tsx` |
| `ToolPanel` | `components/composed/AI/ToolPanel.tsx` |
| `InsightCard` | `components/composed/AI/InsightCard.tsx` |
| `Sidebar` | `components/composed/Navigation/Sidebar.tsx` |
| `ChartCard` | `components/composed/Charts/ChartCard.tsx` |

---

## ✅ Quality Checklist

### Before Starting
- [ ] Guidelines.md is pasted into Figma project
- [ ] Figma page structure is created
- [ ] Lucide Icons plugin installed

### After Each Component Prompt
- [ ] Components use Auto Layout
- [ ] Components have semantic names
- [ ] Variants follow naming conventions (`size=sm|md|lg`, `severity=critical|high|medium|low`)
- [ ] All styling uses variables/tokens (no hardcoded values)
- [ ] States exist: Default, Hover, Loading, Empty, Error (where applicable)

### After All Screens
- [ ] Prototype flows connected (from 19-prototype-flows.md)
- [ ] All click targets have hotspots
- [ ] Transitions are consistent
- [ ] User journeys testable

### Final Check
- [ ] All 22 prompts completed
- [ ] Component library complete (~35 components)
- [ ] All 12+ screens created
- [ ] Prototype is navigable end-to-end
- [ ] Code handoff mapping reviewed (Prompt 21)
- [ ] Data mapping reviewed for implementation (Prompt 22)

---

## 🚀 Quick Start

1. **Create Figma file** with page structure above
2. **Install Lucide Icons** plugin from Figma Community
3. **Paste Guidelines.md** from [01-guidelines-context.md](01-guidelines-context.md) *(includes Databricks Apps alignment)*
4. **Run prompts 2-4** to create tokens (~10 min)
5. **Run prompts 5-10, 18** to create components (~60 min)
6. **Run prompts 11-17** to create screens (~60 min)
7. **Run prompts 19-20** to add interactivity (~30 min)
8. **Review prompt 21** for code handoff preparation (~10 min)
9. **Review prompt 22** for data/API mapping during implementation (~10 min)

**Total time:** ~3 hours for complete design system + 12 screens + prototype flows + code handoff mapping + data source mapping

---

## 📊 Component Count Summary

| Category | Count |
|----------|-------|
| Token sets | 3 (colors, typography, spacing) |
| Primitive components | 12 |
| Composed components | 15 |
| Overlay components | 6 |
| Screen templates | 12 (with states) |
| Icon assets | 80+ |
| **Total components** | **~35** |

---

## 📚 Design Reference

The design specifications in these prompts are based on:
- Production Databricks Lakeview dashboard patterns
- **Official Databricks Design System** (Blue-600 #2272B4, Navy-900 #0B2026, Lava-600 #FF3621, Oat-light #F9F7F4)
- **Official Databricks Typography** (DM Sans, DM Mono)
- Enterprise monitoring UI best practices (Datadog, Grafana, New Relic, Sentry)
- **[Databricks e2e-chatbot-app-next template](https://github.com/databricks/app-templates/tree/main/e2e-chatbot-app-next)** - Official Next.js template for Databricks Apps

See `context/prompts/frontend/figma_frontend_design_prompt.md` for complete design specification.

---

## 🔗 What Happens Next (After Figma)

Once you complete the Figma prototype:

1. **Clone the Databricks template**:
   ```bash
   # Use official Databricks e2e-chatbot-app-next template
   git clone https://github.com/databricks/app-templates.git
   cd app-templates/e2e-chatbot-app-next
   ```

2. **Use Figma MCP** to extract the design into React components

3. **Map Figma components to file structure** (see [21-databricks-template-alignment.md](21-databricks-template-alignment.md)):
   - Primitives → `components/ui/`
   - Layout → `components/layout/`
   - Dashboard → `components/dashboard/`
   - Chat → `components/chat/`

4. **Deploy to Databricks Apps**:
   ```bash
   databricks apps deploy health-monitor --source-code-path /Workspace/...
   ```

The clean component hierarchy (primitives → composed → screens) ensures 1:1 mapping between Figma and the template structure.

---

## ✅ FIGMA MAKE READINESS CHECKLIST

**Status: READY FOR FIGMA MAKE** (January 5, 2026)

All 22 prompt files have been audited and updated to use the **Official Databricks Design System**.

### 🎨 Color System Verification

| Token | Old Value | New Official Value | Status |
|-------|-----------|-------------------|--------|
| Primary Interactive | `#077A9D` (Teal) | `#2272B4` (Blue-600) ✅ | ✅ Updated |
| Primary Text | `#1B3A4B` (Navy) | `#0B2026` (Navy-900) ✅ | ✅ Updated |
| Secondary Emphasis | `#1B3A4B` | `#143D4A` (Navy-700) ✅ | ✅ Updated |
| Background Canvas | `#FAFAFA` | `#F9F7F4` (Oat-light) ✅ | ✅ Updated |
| Success | `#10B981` | `#00A972` (Green-600) ✅ | ✅ Updated |
| Warning | `#F59E0B` | `#FFAB00` (Yellow-600) ✅ | ✅ Updated |
| Critical | `#FF3621` | `#FF3621` (Lava-600) ✅ | ✅ No change needed |
| Info | `#077A9D` | `#2272B4` (Blue-600) ✅ | ✅ Updated |

### 📝 Typography Verification

| Element | Old Value | New Official Value | Status |
|---------|-----------|-------------------|--------|
| UI Font | Inter | DM Sans ✅ | ✅ Updated |
| Code Font | JetBrains Mono | DM Mono ✅ | ✅ Updated |

### 📁 Files Updated (22 Total)

**Phase 1: Foundation**
- [x] `01-guidelines-context.md` - Official colors, typography, iconography ✅
- [x] `02-tokens-colors.md` - 76 color tokens mapped to Databricks CSS classes ✅
- [x] `03-tokens-typography.md` - DM Sans + DM Mono, type scale rules ✅
- [x] `04-tokens-spacing.md` - 8pt grid system ✅

**Phase 2: Components**
- [x] `05-primitives-core.md` - Official button/badge colors ✅
- [x] `06-primitives-data.md` - Updated color references ✅
- [x] `07-composed-navigation.md` - Sidebar/TopBar colors ✅
- [x] `08-composed-data-display.md` - 7 components with official colors ✅
- [x] `09-composed-ai.md` - Tool type colors updated ✅
- [x] `10-composed-charts.md` - Chart series colors updated ✅
- [x] `18-overlays-modals.md` - Modal/Toast severity colors ✅

**Phase 3: Screens**
- [x] `11-screen-executive-overview.md` - All Teal → Blue-600 ✅
- [x] `12-screen-global-explorer.md` - Table-based layout, official colors ✅
- [x] `13-screen-domain-pages.md` - Theme colors updated ✅
- [x] `14-screen-signal-detail.md` - Button/badge colors ✅
- [x] `15-screen-chat-interface.md` - AI chat colors ✅
- [x] `16-screen-alert-center.md` - Alert severity colors ✅
- [x] `17-screen-settings.md` - Form colors ✅

**Phase 4: Interactivity & Handoff**
- [x] `19-prototype-flows.md` - Navigation targets ✅
- [x] `20-icons-assets.md` - Databricks Primary Icons + Lucide ✅
- [x] `21-databricks-template-alignment.md` - Tailwind token mapping ✅
- [x] `22-figma-to-code-mapping.md` - Data source mapping ✅

### 🚀 Build Order Reminder

```
Phase 1 (Foundation):    01 → 02 → 03 → 04
Phase 2 (Components):    05 → 06 → 07 → 08 → 09 → 10 → 18
Phase 3 (Screens):       11 → 12 → 13 → 14 → 15 → 16 → 17
Phase 4 (Handoff):       19 → 20 → 21 → 22
```

**Total Time Estimate:** ~3-4 hours for complete Figma implementation

---

**Last Updated:** January 5, 2026  
**Version:** 3.0 (Official Databricks Design System)
