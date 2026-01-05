# Databricks Health Monitor - Figma Design System

## 🎯 Project Overview

**Product:** Databricks Health Monitoring Platform  
**Type:** Enterprise Platform Observability Dashboard  
**Tech Stack:** Next.js 14, React 18, TypeScript, Databricks Apps  
**Target Users:** Platform Engineers, Data Analysts, Security Teams  

---

## 📋 Build Sequence (21 Total Prompts)

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

### Phase 4: Interactivity & Handoff (3 prompts, ~40 min)

| Order | File | Scope | Output |
|-------|------|-------|--------|
| 19 | [19-prototype-flows.md](19-prototype-flows.md) | **Navigation Flows** | All click targets, transitions, user journeys |
| 20 | [20-icons-assets.md](20-icons-assets.md) | **Icons & Assets** | 80+ icons (Lucide), logo variants, illustrations |
| 21 | [21-databricks-template-alignment.md](21-databricks-template-alignment.md) | **Template Alignment** | Code handoff mapping, Tailwind tokens, file structure |

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
- [ ] All 21 prompts completed
- [ ] Component library complete (~35 components)
- [ ] All 12+ screens created
- [ ] Prototype is navigable end-to-end
- [ ] Code handoff mapping reviewed (Prompt 21)

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

**Total time:** ~3 hours for complete design system + 12 screens + prototype flows + code handoff mapping

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
- Official Databricks color palette (#077A9D, #FF6600)
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
