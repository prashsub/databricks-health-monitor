# 01 - Guidelines & Context Setup

## Overview

This file contains the **Guidelines.md** content to paste into your Figma project. This is CRITICAL for Figma Make to understand the design system contract.

---

## Step 1: Create Guidelines.md in Figma

1. Open your Figma project
2. Go to **Project Settings** → **Guidelines** (or create a text frame named "Guidelines")
3. Paste the entire content below

---

## 📋 PASTE THIS INTO FIGMA GUIDELINES

```markdown
# Databricks Health Monitor - Design Guidelines

## Design Philosophy

This is an **enterprise platform observability dashboard** for technical power users who monitor Databricks workspaces daily. The design prioritizes:

- **Data density** - Users scan 300+ metrics across 5 domains
- **Scannability** - Quick visual hierarchy for fast triage
- **Action orientation** - Every insight has a clear next step
- **Databricks-native** - Follows official Lakeview patterns

## Brand Identity

**Product:** Databricks Health Monitor
**Audience:** Platform Engineers, FinOps, Security Teams
**Usage Context:** Desktop web, daily operational monitoring

## Color System (MANDATORY - Use Variables)

**Based on Official Databricks DATA+AI World Tour 2025 Design System**

### Primary Interactive Colors (for buttons, links, actions)
- **Primary:** #077A9D (Teal) - Primary buttons, links, interactive elements
- **Primary Hover:** #065E7A (Dark Teal) - Hover state for primary actions
- **Secondary:** #1B3A4B (Navy) - Secondary buttons, emphasis
- **Secondary Hover:** #142D3A (Dark Navy) - Hover state for secondary

### Brand Accent Colors (use sparingly for identity/highlights)
- **Brand Red:** #FF3621 (Databricks Red) - Logo, brand highlights, critical ONLY
- **Coral:** #E8715E - Warm accent, table header variant
- **Salmon:** #F4A89A - Subtle highlights, hover warmth
- **Blush:** #F9D4CC - Very light accent backgrounds

### Semantic Colors (for status/feedback)
- **Success:** #00A972 (Green) - Positive trends, health OK, SLO met
- **Warning:** #FFAB00 (Amber) - Approaching threshold, at-risk
- **Critical:** #FF3621 (Red) - Alerts, failures, critical issues ONLY
- **Info:** #077A9D (Teal) - Informational, neutral status

### Background Colors
- **Canvas:** #F5F2ED (Warm Cream) - Page background
- **Canvas Dark:** #0F1419 - Dark mode page background
- **Surface:** #FFFFFF - Card/widget background
- **Surface Alt:** #FAF9F7 (Off-white) - Alternate surface
- **Surface Dark:** #1B3A4B (Navy) - Dark mode card background
- **Highlight:** #FDF0ED (Light Coral) - Highlighted rows, selected items

### Text Colors
- **Text Primary:** #1B3A4B (Navy) - Main text
- **Text Secondary:** #4A5D6B (Slate) - Secondary text, labels
- **Text Muted:** #9DAAB5 (Silver) - Disabled, placeholder
- **Text Inverse:** #FFFFFF - Text on dark backgrounds
- **Text Link:** #077A9D (Teal) - Links
- **Text Brand:** #FF3621 (Red) - Brand emphasis

### Border Colors
- **Border Default:** #E0E6EB (Mist) - Standard borders
- **Border Strong:** #C4CDD5 (Ash) - Emphasized borders
- **Border Focus:** #077A9D (Teal) - Focus states
- **Border Error:** #FF3621 (Red) - Error states
- **Border Brand:** #E8715E (Coral) - Brand accent borders

## Typography (MANDATORY - Use Text Styles)

**Font Family:** Inter (fallback: system-ui)
**Monospace:** JetBrains Mono (for code, numbers, IDs)

### Scale
- **Display:** 32px / 600 weight / 40px line-height
- **H1:** 24px / 600 weight / 32px line-height
- **H2:** 18px / 600 weight / 24px line-height
- **H3:** 16px / 600 weight / 22px line-height
- **Body Large:** 16px / 400 weight / 24px line-height
- **Body:** 14px / 400 weight / 20px line-height
- **Body Small:** 12px / 400 weight / 18px line-height
- **Caption:** 10px / 400 weight / 14px line-height
- **Code:** 14px / 400 weight / JetBrains Mono

## Spacing (MANDATORY - Use Variables)

**Base unit:** 4px

- **space-1:** 4px (tight)
- **space-2:** 8px (compact)
- **space-3:** 12px (standard)
- **space-4:** 16px (comfortable)
- **space-5:** 20px (relaxed)
- **space-6:** 24px (section)
- **space-8:** 32px (page margin)
- **space-12:** 48px (major section)

## Border Radius

- **radius-sm:** 4px (inputs, small cards)
- **radius-md:** 8px (buttons, cards)
- **radius-lg:** 12px (modals, large cards)
- **radius-full:** 9999px (pills, avatars)

## Shadows (Elevation)

- **elevation-1:** 0 1px 2px rgba(0,0,0,0.05) - Cards
- **elevation-2:** 0 4px 6px rgba(0,0,0,0.07) - Hover
- **elevation-3:** 0 10px 15px rgba(0,0,0,0.1) - Modals
- **elevation-4:** 0 20px 25px rgba(0,0,0,0.15) - Dropdowns

## Component Rules

### Buttons
- **Primary:** Teal background (#077A9D), white text - main actions
- **Secondary:** White background, navy border (#1B3A4B), navy text
- **Tertiary:** Transparent background, teal text (#077A9D)
- **Destructive:** Red background (#FF3621), white text - delete/remove ONLY
- **Sizes:** sm (32px), md (40px), lg (48px)
- **States:** default, hover, pressed, disabled, loading

### Cards
- **Background:** Surface (#FFFFFF)
- **Border:** 1px Border Default (#E0E6EB)
- **Radius:** radius-md (8px)
- **Padding:** space-6 (24px)
- **Shadow:** elevation-1
- **Hover:** elevation-2 + Border Focus (#077A9D)

### Badges
- **Severity variants:** info, warning, critical, success
- **Size variants:** sm (20px height), md (24px height)
- **Always:** pill shape (radius-full)

### Tables
- **Header Dark:** Navy background (#1B3A4B), white text, 600 weight
- **Header Accent:** Coral background (#E8715E), white text (alternate)
- **Row height:** 48-56px
- **Zebra striping:** alternate Off-white (#FAF9F7)
- **Hover:** Warm Cream (#F5F2ED) background
- **Selected:** Light Coral (#FDF0ED) background

### KPI Tiles
- **Size:** 200-280px width × 120-180px height
- **Large number:** 32-48px font, 700 weight, Navy (#1B3A4B)
- **Trend indicator:** Arrow + percentage
  - Positive: Green (#00A972)
  - Negative: Red (#FF3621)
  - Neutral: Slate (#4A5D6B)
- **Sparkline:** Optional, 60-80px × 30px, Teal (#077A9D) line

### Alert Rows
- **Severity indicator:** 8px colored left border (Critical: #FF3621, High: #E8715E, Warning: #FFAB00)
- **Background:** Surface (#FFFFFF)
- **Height:** 64-72px
- **Hover:** Light Coral (#FDF0ED) background
- **Actions:** visible on hover

## Status/Severity Mapping

Use consistently across ALL components:

| Severity | Color | Hex | Icon | Usage |
|----------|-------|-----|------|-------|
| Critical | Databricks Red | #FF3621 | 🔴 | Immediate action required |
| High | Coral | #E8715E | 🟠 | Urgent attention |
| Warning | Amber | #FFAB00 | 🟡 | Monitor closely |
| Info | Teal | #077A9D | 🔵 | Informational |
| Success | Green | #00A972 | 🟢 | All OK, targets met |

## Layout Grid

**6-column grid** for dashboard layouts:
- Gutters: 24px
- Margins: 32px

Standard widths:
- KPI Counter: 1 column
- Small chart: 2 columns
- Medium chart: 3 columns
- Large chart/table: 6 columns (full width)

## State Requirements

ALL data-driven components MUST have:
1. **Default** - Normal display with data
2. **Loading** - Skeleton placeholder
3. **Empty** - Empty state with guidance
4. **Error** - Error message + retry

## Naming Conventions

Components: PascalCase, semantic names
- ✅ AlertRow, KPITile, StatusBadge
- ❌ Card2, BlueBox, Rectangle12

Variants: lowercase, consistent
- size: sm | md | lg
- severity: info | warning | critical | success
- state: default | hover | pressed | disabled | loading
- density: comfortable | compact

## Accessibility

- Color contrast: 4.5:1 minimum for text
- Focus indicators: 2px ring, Teal (#077A9D) - high contrast against warm backgrounds
- Touch targets: 44px minimum
- Never rely on color alone for status

## Databricks Apps Integration

### Deployment Target
- **Platform:** Databricks Apps
- **Framework:** Next.js 14 with App Router
- **Styling:** Tailwind CSS
- **Icons:** Lucide React (use Lucide icon names)
- **Template:** Based on [e2e-chatbot-app-next](https://github.com/databricks/app-templates/tree/main/e2e-chatbot-app-next)

### Tailwind CSS Mapping (CRITICAL)
All Figma tokens MUST map to Tailwind utilities (with custom Databricks theme):

| Figma Token | Hex | Tailwind Class | Usage |
|-------------|-----|----------------|-------|
| **primary (Teal)** | #077A9D | `bg-primary` / `text-primary` | Primary buttons, links |
| neutral/navy | #1B3A4B | `bg-db-navy` / `text-db-navy` | Headers, secondary buttons |
| brand/red (accent) | #FF3621 | `bg-db-red` / `text-db-red` | Critical badges ONLY |
| brand/coral | #E8715E | `bg-db-coral` / `text-db-coral` | High severity, warm accents |
| background/canvas | #F5F2ED | `bg-db-cream` | Page background |
| background/surface | #FFFFFF | `bg-white` | Cards, modals |
| background/surface-alt | #FAF9F7 | `bg-db-offwhite` | Zebra stripes |
| text/primary | #1B3A4B | `text-db-navy` | Main text |
| text/secondary | #4A5D6B | `text-db-slate` | Labels, secondary |
| border/default | #E0E6EB | `border-db-mist` | Card borders |
| severity/critical | #FF3621 | `text-db-red` | Critical alerts |
| severity/high | #E8715E | `text-db-coral` | High alerts |
| severity/warning | #FFAB00 | `text-amber-500` | Warnings |
| severity/success | #00A972 | `text-emerald-600` | Success |

**Note:** Custom Databricks colors in `tailwind.config.js`:
```js
colors: {
  primary: '#077A9D',      // Teal - main interactive color
  'db-red': '#FF3621',     // Brand red - critical/destructive ONLY
  'db-coral': '#E8715E',   // High severity accent
  'db-navy': '#1B3A4B',    // Dark text, headers
  'db-cream': '#F5F2ED',   // Warm page background
  'db-offwhite': '#FAF9F7',
  'db-slate': '#4A5D6B',
  'db-mist': '#E0E6EB',
}
```

### Component → File Path Mapping

Components follow shadcn/ui patterns:

| Figma Component | Code Path |
|-----------------|-----------|
| Button, Badge, Card, Input | `components/ui/` |
| Sidebar, TopBar, Breadcrumb | `components/layout/` |
| KPITile, MetricCard, AlertRow | `components/dashboard/` |
| ChatBubble, ChatInput, ToolPanel | `components/chat/` |
| ChartCard | `components/charts/` |
| Modal, Drawer, Toast | `components/overlays/` |

### AI Chat Requirements (Vercel AI SDK)
Chat components must support:
- Streaming responses (typing indicator)
- Tool call rendering (collapsible panels)
- Markdown in responses (headings, code, lists)
- Message actions (copy, feedback thumbs)
- Multi-line input with Shift+Enter

### Screen → Route Mapping

| Screen | Next.js Route |
|--------|---------------|
| Executive Overview | `/` |
| Global Explorer | `/explorer` |
| Cost Domain | `/cost` |
| Reliability Domain | `/reliability` |
| Performance Domain | `/performance` |
| Governance Domain | `/governance` |
| Data Quality Domain | `/quality` |
| Signal Detail | `/signals/[id]` |
| AI Chat | `/chat` |
| Alert Center | `/alerts` |
| Settings | `/settings` |
```

---

## Step 2: Context Prompt (Optional)

If you want to set context before creating tokens, paste this into Figma Make:

```
I'm building a design system for "Databricks Health Monitor" - an enterprise platform observability dashboard.

Key context:
- Users: Platform engineers, FinOps, security teams
- Usage: Daily operational monitoring, data-dense dashboards
- Platform: Desktop web (1440px primary width)
- Style: Modern enterprise SaaS, Databricks-native colors

Design philosophy:
- Data density over whitespace
- Scannable hierarchies for fast triage
- Action-oriented (every metric has a next step)
- Consistent severity colors across all components

I've added Guidelines.md to this project. Please follow it strictly for all component creation.

Confirm you understand the context before we proceed.
```

---

## ✅ Verification

Before proceeding to Prompt 02, verify:
- [ ] Guidelines.md content is pasted into Figma
- [ ] You understand the color system
- [ ] You understand the typography scale
- [ ] You understand the spacing system
- [ ] You understand the component naming conventions

---

**Next:** [02-tokens-colors.md](02-tokens-colors.md)

