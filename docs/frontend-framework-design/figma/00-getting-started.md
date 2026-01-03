# 00 - Getting Started with Figma Design

## Overview

This guide explains how to use the Figma design prompts to create the Databricks Health Monitor UI.

> **Approach:** These guides are designed for **AI-assisted Figma design**. Copy prompts into Figma AI or any design AI to generate screens.

---

## 🎯 Before You Start

### Prerequisites

- [ ] Figma account with AI features (or external AI tool)
- [ ] **Inter font** installed ([download](https://fonts.google.com/specimen/Inter))
- [ ] **JetBrains Mono font** installed ([download](https://www.jetbrains.com/lp/mono/))
- [ ] Familiarity with monitoring tools (Datadog, Grafana, New Relic)

### What You'll Build

| Category | Count | Examples |
|----------|-------|----------|
| **Design System** | 3 files | Colors, Typography, Spacing |
| **Screens** | 8 | Executive Overview, Domain Pages, etc. |
| **Components** | 110+ | KPI tiles, charts, tables, AI messages |

### Time Estimate

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | Day 1 | Setup + Design System (01-04) |
| Phase 2 | Week 1-2 | Core Screens (05-06) |
| Phase 3 | Week 3-4 | Domain + Detail Screens (07-08) |
| Phase 4 | Week 5 | Advanced Screens (09-11) |
| Phase 5 | Week 6 | Reference + Polish (12-13) |
| **Total** | **6 weeks** | **13 guides** |

---

## 📋 Design Sequence

**Follow this exact order:**

```
┌─────────────────────────────────────────────────────────────────┐
│             PHASE 1: SETUP + DESIGN SYSTEM (Day 1)              │
│                                                                 │
│  Step 1:  01-context-setup.md        → Product context + tokens │
│  Step 2:  02-design-system-colors.md → Create color styles      │
│  Step 3:  03-design-system-typography.md → Create text styles   │
│  Step 4:  04-design-system-spacing.md    → Configure spacing    │
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2: CORE SCREENS (Week 1-2)                │
│                                                                 │
│  Step 5:  05-executive-overview.md  → Home page with KPIs      │
│  Step 6:  06-global-explorer.md     → Datadog-style signal view│
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               PHASE 3: DOMAIN + DETAIL (Week 3-4)               │
│                                                                 │
│  Step 7:  07-domain-pages.md        → 5 domain pages           │
│  Step 8:  08-signal-detail.md       → Drilldown with timeline  │
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                PHASE 4: ADVANCED SCREENS (Week 5)               │
│                                                                 │
│  Step 9:  09-chat-interface.md      → AI assistant conversation│
│  Step 10: 10-alert-center.md        → Alert management         │
│  Step 11: 11-settings-admin.md      → Settings & configuration │
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               PHASE 5: REFERENCE + POLISH (Week 6)              │
│                                                                 │
│  Step 12: 12-visualizations.md      → All chart patterns       │
│  Step 13: 13-component-library.md   → All component states     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Day 1)

### Step 1: Install Fonts

Download and install:
- [Inter](https://fonts.google.com/specimen/Inter) - UI text
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) - Code/monospace

### Step 2: Create Figma File

1. **File** → **New design file**
2. Rename to "Databricks Health Monitor"

### Step 3: Set Up Context (01)

1. Open [01-context-setup.md](01-context-setup.md)
2. Copy the **entire context prompt**
3. Paste into Figma AI

### Step 4: Create Design System (02-04)

Follow these in order:
1. [02-design-system-colors.md](02-design-system-colors.md) → Create color styles
2. [03-design-system-typography.md](03-design-system-typography.md) → Create text styles
3. [04-design-system-spacing.md](04-design-system-spacing.md) → Configure nudge + grid

### Step 5: Start Designing Screens!

Proceed to [05-executive-overview.md](05-executive-overview.md)

---

## 📁 Complete File Reference

### Setup & Design System (Do First)

| # | File | Content | Time |
|---|------|---------|------|
| 01 | [context-setup.md](01-context-setup.md) | Product context + all tokens | 10 min |
| 02 | [design-system-colors.md](02-design-system-colors.md) | 50+ color styles | 15 min |
| 03 | [design-system-typography.md](03-design-system-typography.md) | 15 text styles | 15 min |
| 04 | [design-system-spacing.md](04-design-system-spacing.md) | Spacing + layouts | 10 min |

### Screen Designs (Follow in Order)

| # | File | Content | Time |
|---|------|---------|------|
| 05 | [executive-overview.md](05-executive-overview.md) | Home page with KPIs | 2-4 hrs |
| 06 | [global-explorer.md](06-global-explorer.md) | Signal table (Datadog-style) | 2-4 hrs |
| 07 | [domain-pages.md](07-domain-pages.md) | 5 domain page templates | 4-8 hrs |
| 08 | [signal-detail.md](08-signal-detail.md) | Drilldown with timeline | 2-4 hrs |
| 09 | [chat-interface.md](09-chat-interface.md) | AI conversation UI | 2-4 hrs |
| 10 | [alert-center.md](10-alert-center.md) | Alert management | 2-4 hrs |
| 11 | [settings-admin.md](11-settings-admin.md) | Settings pages | 2-4 hrs |

### Reference Materials

| # | File | Content | When to Use |
|---|------|---------|-------------|
| 12 | [visualizations.md](12-visualizations.md) | 8 chart patterns | Reference anytime |
| 13 | [component-library.md](13-component-library.md) | All components | Reference anytime |

---

## 🎨 Design System Quick Reference

### Colors (Key Values)

```
Brand:         #FF3621 (Databricks Red)
AI:            #3B82F6 (Blue - ALL AI elements)
Critical:      #DC2626
Warning:       #F59E0B
Success:       #10B981
Background:    #0F0F10 (dark)
Surface:       #1A1A1B (dark)
Text:          #FFFFFF (dark mode)
```

### Typography

```
Display:       32px / Semibold / Inter
H1:            24px / Semibold / Inter
H2:            20px / Semibold / Inter
Body:          14px / Regular / Inter
Label:         12px / Medium / UPPERCASE / Inter
Code:          13px / Regular / JetBrains Mono
```

### Spacing

```
xs:            4px  (icon gaps)
sm:            8px  (item gaps)
md:            16px (card padding)
lg:            24px (page margins)
xl:            32px (section gaps)
```

---

## 🎯 Design Inspiration

| Tool | Patterns Borrowed |
|------|-------------------|
| **Datadog** | Single pane of glass, dense data, filter chips |
| **Grafana** | Time controls, panel layouts, variables |
| **New Relic** | AIOps correlation, root cause analysis |
| **Sentry** | Issue-centric triage, context-rich detail |

**Our differentiator:** Unified AI assistant that proactively helps users.

---

## ✅ Completion Checklist

### Design System Checklist (Phase 1)

- [ ] Inter font installed
- [ ] JetBrains Mono font installed
- [ ] Color styles created (50+)
- [ ] Text styles created (15+)
- [ ] Nudge amount set (4px/16px)
- [ ] Layout grid configured

### Per-Screen Checklist

For each screen, ensure:
- [ ] Desktop layout (1440px)
- [ ] Uses design system styles
- [ ] All component states (default, hover, loading, error, empty)
- [ ] AI integration points (blue styling)

### Final Deliverables

- [ ] 8 high-fidelity screens
- [ ] Design system in Figma
- [ ] Component library
- [ ] Interactive prototype
- [ ] Developer handoff specs

---

## 🚀 Ready?

**Start with:** [01-context-setup.md](01-context-setup.md)
