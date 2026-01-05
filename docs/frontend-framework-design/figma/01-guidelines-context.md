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

**Based on OFFICIAL Databricks Design System (extracted from bf-color-* CSS classes)**

### Primary Interactive Colors (for buttons, links, actions)
- **Primary:** #2272B4 (Blue-600) ✅ PRIMARY buttons, links, interactive elements
- **Primary Hover:** #0E538B (Blue-700) ✅ Hover state for primary actions
- **Secondary:** #143D4A (Navy-700) ✅ Secondary buttons, emphasis
- **Secondary Hover:** #1B3139 (Navy-800) ✅ Hover state for secondary

### Brand Accent Colors (OFFICIAL Databricks Lava & Maroon)
- **Brand Lava:** #FF3621 (Lava-600) ✅ Databricks brand red, critical ONLY
- **Lava Medium:** #FF5F46 (Lava-500) ✅ High severity, warm accent
- **Lava Soft:** #FF9E94 (Lava-400) ✅ Subtle highlights, softer red
- **Lava Light:** #FAECEB (Lava-100) ✅ Very light red backgrounds
- **Maroon:** #AB4057 (Maroon-500) - Alternate brand accent

### Semantic Colors (EXACT MATCHES to Databricks palette!)
- **Success:** #00A972 (Green-600) ✅ Positive trends, health OK, SLO met
- **Warning:** #FFAB00 (Yellow-600) ✅ Approaching threshold, at-risk
- **Critical:** #FF3621 (Lava-600) ✅ Alerts, failures, critical issues ONLY
- **Info:** #2272B4 (Blue-600) ✅ Informational, neutral status

### Background Colors (OFFICIAL Oat palette)
- **Canvas:** #F9F7F4 (Oat-light) ✅ Page background
- **Canvas Dark:** #0B2026 (Navy-900) ✅ Dark mode page background
- **Surface:** #FFFFFF (White) ✅ Card/widget background
- **Surface Alt:** #EEEDE9 (Oat-medium) ✅ Alternate surface
- **Surface Dark:** #143D4A (Navy-700) ✅ Dark mode card background
- **Highlight:** #FAECEB (Lava-100) ✅ Highlighted rows, selected items

### Text Colors (OFFICIAL Databricks Navy & Gray)
- **Text Primary:** #0B2026 (Navy-900-primary) ✅ DARKEST - Main text
- **Text Secondary:** #5A6F77 (Gray-text) ✅ Secondary text, labels
- **Text Muted:** #90A5B1 (Navy-400) ✅ Disabled, placeholder
- **Text Inverse:** #FFFFFF (White) ✅ Text on dark backgrounds
- **Text Link:** #2272B4 (Blue-600) ✅ Links
- **Text Brand:** #FF3621 (Lava-600) ✅ Brand emphasis

### Border Colors
- **Border Default:** #DCE0E2 (Gray-lines) ✅ Standard borders
- **Border Strong:** #C4CCD6 (Navy-300) ✅ Emphasized borders
- **Border Focus:** #2272B4 (Blue-600) ✅ Focus states
- **Border Error:** #FF3621 (Lava-600) ✅ Error states
- **Border Brand:** #FF5F46 (Lava-500) ✅ Brand accent borders

## Typography (MANDATORY - Use Text Styles)

**Font Family:** DM Sans ✅ OFFICIAL Databricks (fallback: system-ui)
**Monospace:** DM Mono ✅ OFFICIAL Databricks (for code, numbers, IDs)

### Type Scale Rules (OFFICIAL Databricks)
- **Above 20px:** Sizes MUST be divisible by 8 (24, 32, 40, 48, 56, 64, 72, 80)
- **Below 20px:** Sizes divisible by 4 or 2 (10, 12, 14, 16, 18, 20)
- **Line Height Standards:**
  - **Body copy:** 150% (1.5) line-height ✅
  - **Headlines:** 120% (1.2) line-height ✅

### Scale
- **Display XL:** 80px / 700 weight / 96px line-height (1.2)
- **Display Large:** 48px / 700 weight / 56px line-height (1.17) - Hero numbers
- **Display:** 32px / 600 weight / 40px line-height (1.25) - Page titles
- **H1:** 24px / 600 weight / 32px line-height (1.33) - Major sections
- **H2:** 18px / 600 weight / 24px line-height (1.33) - Card titles
- **H3:** 16px / 600 weight / 22px line-height (1.375) - Subsections
- **H4:** 14px / 600 weight / 20px line-height (1.43) - Table headers
- **Body Large:** 16px / 400 weight / 24px line-height (1.5) ✅
- **Body:** 14px / 400 weight / 20px line-height (1.43)
- **Body Small:** 12px / 400 weight / 18px line-height (1.5) ✅
- **Caption:** 10px / 400 weight / 14px line-height (1.4)
- **Code:** 14px / 400 weight / 20px line-height (1.43) - DM Mono
- **Number Large:** 48px / 700 weight / 56px line-height (1.17) - DM Mono
- **Number Medium:** 24px / 600 weight / 32px line-height (1.33) - DM Mono

### Typography Best Practices (OFFICIAL Databricks)

**✅ DO:**
- Use hierarchy (size, weight, color) for scannable content
- Give content space to breathe (16px+ between text blocks)
- Use 150% line-height for body, 120% for headlines
- Break paragraphs into 3-5 line chunks
- Use clear CTAs separate from body text

**❌ DON'T:**
- Cram text elements too close together
- Use tight line-height (below 120%)
- Use right-aligned text (always left-align)
- Create impenetrable paragraphs with inline links
- Use monospace for UI text (reserve for code/numbers)

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

## Iconography (OFFICIAL Databricks Primary Icons)

**Icon Library:** `context/branding/primary_icons/` (200+ official icons)

### Size Standards
- **icon-sm:** 16px × 16px - Inline text, buttons, chips, table cells
- **icon-md:** 24px × 24px - Cards, list items, navigation
- **icon-lg:** 32px × 32px - Page headers, empty states, feature cards
- **icon-xl:** 48px × 48px - Hero sections, large feature cards, welcome screens

### Color Mapping (Semantic Use)
- **Default:** Navy-900 (#0B2026) or Navy-700 (#143D4A) - Standard icons
- **Interactive:** Blue-600 (#2272B4) - Clickable icons, links
- **Success:** Green-600 (#00A972) - Positive states, health OK
- **Warning:** Yellow-600 (#FFAB00) - Caution, at-risk states
- **Critical:** Lava-600 (#FF3621) - Errors, critical alerts, destructive actions
- **Muted:** Navy-500 (#618794) - Disabled, secondary icons

### Icon Categories for Health Monitor

**Monitoring & Observability:**
- Observable Metrics, Performance, Cost Management
- Data Quality 1, Data Quality 2, Data Quality 3
- Incident Investigation, Help, Runbook Playbook

**Data & Platform:**
- Data Lake, Delta Lake, Unity Catalog, Lakeflow Pipelines
- Databricks Workspace, Serverless, Spark Cluster
- Data Lineage, Data Product, Dashboards

**ML & AI:**
- Machine Learning, MLOps, Feature Store, Model Registry
- Model Training, Model Tuning, Auto Machine Learning

**Security & Governance:**
- Governance, Compliance, Data Security, Privacy
- Enterprise Security, Encryption, Authentication Service

**Status & Actions:**
- Directional Arrows (Up/Down/Left/Right/Curved)
- Deploy, Automation, Scheduled Jobs
- Risk Fraud Detection, Webhook

### Accessibility Rules
- **Icon-only buttons:** MUST have ARIA label (e.g., aria-label="View details")
- **Critical actions:** MUST have icon + visible text label
- **Icon color:** MUST maintain 3:1 contrast ratio against background
- **Hover states:** Change color to Blue-600 (#2272B4) for interactive icons

### Common Icon Mappings
| Feature | Icon Name | Color |
|---------|-----------|-------|
| Health Score | Observable Metrics | Navy-900 |
| Cost Analytics | Cost Management | Navy-900 |
| Failed Jobs | Incident Investigation | Lava-600 |
| ML Models | Machine Learning | Navy-900 |
| Security Findings | Governance | Navy-900 |
| Data Quality | Data Quality 1-3 | Navy-900 |
| Alerts | Help | Lava-600 (critical) |
| Optimize | Deploy | Blue-600 (interactive) |
| Settings | Store Design | Navy-900 |

## Component Rules

### Buttons (OFFICIAL Databricks Colors)
- **Primary:** Blue background (#2272B4 Blue-600) ✅, white text - main actions
- **Secondary:** White background, navy border (#143D4A Navy-700), navy text (#143D4A)
- **Gray Outlined:** White background, gray border (#DCE0E2 Gray-lines), DARKEST navy text (#0B2026 Navy-900) ✅
- **Tertiary:** Transparent background, blue text (#2272B4 Blue-600) ✅ - text link style
- **Ghost:** Transparent background, gray text (#5A6F77 Gray-text) ✅ - dismiss/cancel actions
- **Destructive:** Lava red background (#FF3621 Lava-600) ✅, white text - delete/remove ONLY
- **Sizes:** sm (32px), md (40px), lg (48px)
- **States:** default, hover, pressed, disabled, loading

**Button Contrast Rules (CRITICAL for accessibility):**
- All text on white/light backgrounds must be Navy-900 (#0B2026) or Blue-600 (#2272B4) ✅
- Never use light gray text on white buttons
- Gray outlined buttons use DARKEST Navy text (#0B2026), NOT gray text

### Cards (OFFICIAL Databricks)
- **Background:** Surface (#FFFFFF White) ✅
- **Border:** 1px Border Default (#DCE0E2 Gray-lines) ✅
- **Radius:** radius-md (8px)
- **Padding:** space-6 (24px)
- **Shadow:** elevation-1
- **Hover:** elevation-2 + Border Focus (#2272B4 Blue-600) ✅

### Badges
- **Severity variants:** info, warning, critical, success
- **Size variants:** sm (20px height), md (24px height)
- **Always:** pill shape (radius-full)

### Tables (OFFICIAL Databricks)
- **Header Dark:** Navy background (#143D4A Navy-700) ✅, white text, 600 weight
- **Header Accent:** Lava background (#FF5F46 Lava-500) ✅, white text (alternate)
- **Row height:** 48-56px
- **Zebra striping:** alternate Oat medium (#EEEDE9) ✅
- **Hover:** Oat light (#F9F7F4) ✅ background
- **Selected:** Lava light (#FAECEB Lava-100) ✅ background

### Metric Cards (Primary Metrics) - OFFICIAL Databricks
Simple cards with label, value, status chip, and colored top accent bar:
- **Background:** White #FFFFFF ✅
- **Border:** 1px solid #DCE0E2 (Gray-lines) ✅
- **Border-top:** 4px solid [accent color] - visual differentiation
- **Border-radius:** 8px
- **Padding:** 16px
- **Shadow:** elevation-1
- **Label:** 14px, regular, Gray-text #5A6F77 ✅ (top)
- **Value:** 32px, bold (600), Navy-900 #0B2026 ✅ (center)
- **Status Chip:** Below value, colored background + text
  - Stable/On track: Light green bg #DCF4ED (Green-100) ✅, green text #00A972 (Green-600) ✅
  - Anomaly: Light lava bg #FAECEB (Lava-100) ✅, lava text #FF5F46 (Lava-500) ✅
  - Trending Up: Light blue bg #F0F8FF (Blue-100) ✅, blue text #2272B4 (Blue-600) ✅
  - Warning: Light yellow bg #FFF0D3 (Yellow-100) ✅, yellow text #FFAB00 (Yellow-600) ✅
  - Critical: Light lava bg #FAECEB (Lava-100) ✅, lava text #FF3621 (Lava-600) ✅

**Top Border Accent Colors (per metric type):**
- Health Score: Blue #2272B4 (Blue-600) ✅
- Cost Today: Lava #FF5F46 (Lava-500) ✅
- Active Alerts: Blue #2272B4 (Blue-600) ✅
- SLA Status: Green #00A972 (Green-600) ✅
- Performance: Navy #143D4A (Navy-700) ✅

### Domain Health Cards - OFFICIAL Databricks
Cards with colored top accent bar:
- **Background:** White #FFFFFF ✅
- **Border:** 1px solid #DCE0E2 (Gray-lines) ✅
- **Border-top:** 4px solid [domain color]
- **Border-radius:** 8px
- **Padding:** 16px
- **Header:** Icon + Domain name (14px, Gray-text #5A6F77) ✅
- **Value:** 24px, bold (600), Navy-900 #0B2026 ✅
- **Trend:** Arrow + percentage, colored by direction
  - Good direction: Green #00A972 (Green-600) ✅
  - Bad direction: Lava #FF3621 (Lava-600) ✅
- **Hover:** Blue #2272B4 (Blue-600) ✅ border

### KPI Tiles (Legacy - use Metric Cards instead)
- **Size:** 200-280px width × 120-180px height
- **Large number:** 32-48px font, 700 weight, Navy-900 (#0B2026) ✅
- **Trend indicator:** Arrow + percentage
  - Positive: Green (#00A972 Green-600) ✅
  - Negative: Lava (#FF3621 Lava-600) ✅
  - Neutral: Gray-text (#5A6F77) ✅
- **Sparkline:** Optional, 60-80px × 30px, Blue (#2272B4 Blue-600) ✅ line

### Alert Rows
- **Severity indicator:** 8px colored left border (Critical: #FF3621 Lava-600, High: #FF5F46 Lava-500, Warning: #FFAB00 Yellow-600) ✅
- **Background:** Surface (#FFFFFF) ✅
- **Height:** 64-72px
- **Hover:** Lava-light (#FAECEB Lava-100) ✅ background
- **Actions:** visible on hover

### AI Command Center (Special Pattern) - OFFICIAL Databricks
The AI Command Center is a prominent dashboard section that summarizes issues and recommendations.

**Layout:** Clean, minimal, NO heavy borders around individual metrics
- **Section background:** White (#FFFFFF) ✅ with subtle shadow
- **Header:** "AI Command Center" in Navy-900 (#0B2026) ✅ + sparkle icon
- **Header controls:** Text buttons in Blue (#2272B4 Blue-600) ✅

**Metrics Row (3 columns, no borders between):**
- **Critical count:** Lava dot (#FF3621 Lava-600) ✅ + number + label
- **Savings:** Green dot (#00A972 Green-600) ✅ + amount + label
- **SLOs at Risk:** Yellow dot (#FFAB00 Yellow-600) ✅ + number + label

**Action Buttons (CRITICAL - proper contrast and color hierarchy):**
- **Primary Actions:** "Fix Critical Issues", "Show Analysis", "Optimize Now" → Blue filled (#2272B4 Blue-600) ✅, white text
- **Secondary Actions:** "See Forecast", "Remind Me Later" → Gray outlined (#DCE0E2 Gray-lines border) ✅, Darkest Navy text (#0B2026 Navy-900) ✅
- **Tertiary Actions:** "View Full Report", "View SLOs →" → Blue text link (#2272B4 Blue-600) ✅
- **Dismiss Actions:** "Not Now", "Hide" → Ghost button, Gray-text (#5A6F77) ✅

**Button Contrast (CRITICAL):**
- Gray outlined buttons MUST have DARKEST Navy (#0B2026 Navy-900) ✅ text, NOT gray text
- Ensures accessibility and visibility on white backgrounds

**AI Insight Box:**
- Light oat background (#EEEDE9 Oat-medium) ✅
- Lightbulb icon + natural language text
- Action chips below

**Key Rule:** ❌ Never use Lava red (#FF3621) for action buttons. Lava red = status indicator ONLY. Use Blue (#2272B4) for primary actions.

## Status/Severity Mapping - OFFICIAL Databricks

Use consistently across ALL components:

| Severity | Color | Hex | Official Class | Icon | Usage |
|----------|-------|-----|----------------|------|-------|
| Critical | Lava Red | #FF3621 | lava-600 ✅ | 🔴 | Immediate action required |
| High | Lava Medium | #FF5F46 | lava-500 ✅ | 🟠 | Urgent attention |
| Warning | Yellow | #FFAB00 | yellow-600 ✅ | 🟡 | Monitor closely |
| Info | Blue | #2272B4 | blue-600 ✅ | 🔵 | Informational |
| Success | Green | #00A972 | green-600 ✅ | 🟢 | All OK, targets met |

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

## Accessibility - OFFICIAL Databricks

- Color contrast: 4.5:1 minimum for text
- Focus indicators: 2px ring, Blue (#2272B4 Blue-600) ✅ - high contrast against warm oat backgrounds
- Touch targets: 44px minimum
- Never rely on color alone for status

## Databricks Apps Integration

### Deployment Target
- **Platform:** Databricks Apps
- **Framework:** Next.js 14 with App Router
- **Styling:** Tailwind CSS
- **Icons:** Lucide React (use Lucide icon names)
- **Template:** Based on [e2e-chatbot-app-next](https://github.com/databricks/app-templates/tree/main/e2e-chatbot-app-next)

### Tailwind CSS Mapping (CRITICAL) - OFFICIAL Databricks

All Figma tokens MUST map to Tailwind utilities (with OFFICIAL Databricks theme):

| Figma Token | Hex | Official Class | Tailwind Class | Usage |
|-------------|-----|----------------|----------------|-------|
| **primary (Blue)** ✅ | #2272B4 | blue-600 | `bg-primary` / `text-primary` | Primary buttons, links |
| neutral/navy ✅ | #143D4A | navy-700 | `bg-db-navy` / `text-db-navy` | Headers, secondary buttons |
| neutral/navy-darkest ✅ | #0B2026 | navy-900 | `text-db-navy-900` | Main text (darkest) |
| brand/lava ✅ | #FF3621 | lava-600 | `bg-db-lava` / `text-db-lava` | Critical badges ONLY |
| brand/lava-medium ✅ | #FF5F46 | lava-500 | `bg-db-lava-500` / `text-db-lava-500` | High severity |
| background/canvas ✅ | #F9F7F4 | oat-light | `bg-db-oat` | Page background |
| background/surface ✅ | #FFFFFF | white | `bg-white` | Cards, modals |
| background/surface-alt ✅ | #EEEDE9 | oat-medium | `bg-db-oat-medium` | Zebra stripes |
| text/primary ✅ | #0B2026 | navy-900 | `text-db-navy-900` | Main text |
| text/secondary ✅ | #5A6F77 | gray-text | `text-db-gray` | Labels, secondary |
| border/default ✅ | #DCE0E2 | gray-lines | `border-db-gray-lines` | Card borders |
| severity/critical ✅ | #FF3621 | lava-600 | `text-db-lava` | Critical alerts |
| severity/high ✅ | #FF5F46 | lava-500 | `text-db-lava-500` | High alerts |
| severity/warning ✅ | #FFAB00 | yellow-600 | `text-db-yellow` | Warnings |
| severity/success ✅ | #00A972 | green-600 | `text-db-green` | Success |

**Note:** OFFICIAL Databricks colors in `tailwind.config.js`:
```js
colors: {
  primary: '#2272B4',         // Blue-600 - OFFICIAL primary interactive ✅
  'db-blue': '#2272B4',       // blue-600 ✅
  'db-navy': '#143D4A',       // navy-700 ✅
  'db-navy-900': '#0B2026',   // navy-900-primary - DARKEST ✅
  'db-lava': '#FF3621',       // lava-600 - Brand red - critical/destructive ONLY ✅
  'db-lava-500': '#FF5F46',   // lava-500 - High severity accent ✅
  'db-oat': '#F9F7F4',        // oat-light - Warm page background ✅
  'db-oat-medium': '#EEEDE9', // oat-medium ✅
  'db-gray': '#5A6F77',       // gray-text ✅
  'db-gray-lines': '#DCE0E2', // gray-lines ✅
  'db-green': '#00A972',      // green-600 ✅
  'db-yellow': '#FFAB00',     // yellow-600 ✅
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

