# 07 - Composed Navigation Components

## Overview

Create navigation components built from primitives: Sidebar, TopBar, Breadcrumb, and TabBar. These form the application shell and page navigation.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create navigation components for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users navigating between domains
- Style: Clean enterprise SaaS, persistent navigation
- Platform: Desktop web (1440px primary width)

Objective (this run only):
- Create 4 navigation components
- Use ONLY primitives from previous prompts (Button, Badge, Avatar, etc.)
- Place in Components/Composed/Navigation section

Follow Guidelines.md for design system alignment.

Design system rules:
- REUSE existing primitive components
- Use Auto Layout for all navigation
- Components must be responsive
- Clear visual hierarchy for navigation state

---

## COMPONENT 1: Sidebar

Purpose: Main application navigation (left side)

### Specifications:
- Width: 240px (expanded), 64px (collapsed)
- Height: 100vh (full viewport height)
- Background: background/surface (#FFFFFF)
- Border right: 1px border/default

### Variants:

**collapsed** (boolean property):
- true: 64px width, icons only, tooltips on hover
- false: 240px width, icons + labels

### Structure:
```
Sidebar (Auto Layout, vertical)
├── SidebarHeader (64px height)
│   ├── Logo (32px icon)
│   └── [ProductName] (heading/h3, only when expanded)
├── SidebarNav (Auto Layout, vertical, flex-grow)
│   ├── NavItem (Overview)
│   ├── NavItem (Cost) [with Badge showing alert count]
│   ├── NavItem (Performance)
│   ├── NavItem (Security) [with Badge]
│   ├── NavItem (Reliability)
│   ├── NavDivider (1px line)
│   ├── NavItem (Alerts)
│   └── NavItem (Chat)
└── SidebarFooter (64px height)
    ├── NavItem (Settings)
    └── [CollapseToggle button]
```

### NavItem Sub-component:
```
NavItem (Auto Layout, horizontal)
├── Icon (20px, icon/default color)
├── [Label] (body/default, only when expanded)
└── [Badge] (optional, for alert counts)
```

**NavItem States:**
- default: transparent background, icon/default, text/secondary
- hover: background/elevated, icon/primary, text/primary
- active: brand/primary-light background, brand/primary icon, brand/primary text, 4px left border brand/primary
- disabled: 50% opacity

### Specifications:
- NavItem height: 44px
- NavItem padding: spacing/3 (12px) horizontal
- Icon-label gap: spacing/3 (12px)
- Items gap: spacing/1 (4px)
- Section padding: spacing/4 (16px) top/bottom

---

## COMPONENT 2: TopBar

Purpose: Global controls and user menu (top of page)

### Specifications:
- Width: 100% (full width)
- Height: 64px
- Background: background/surface (#FFFFFF)
- Border bottom: 1px border/default
- Shadow: elevation/1

### Structure:
```
TopBar (Auto Layout, horizontal, space-between)
├── TopBarLeft (Auto Layout, horizontal)
│   ├── [BreadcrumbSlot] (placeholder for breadcrumb)
│   └── PageTitle (heading/h2)
├── TopBarCenter (Auto Layout, horizontal) [optional]
│   └── [Search input or tabs]
└── TopBarRight (Auto Layout, horizontal)
    ├── TimeRangePicker (Button with dropdown icon)
    ├── RefreshButton (icon button)
    ├── NotificationButton (icon button with Badge)
    └── UserMenu (Avatar + dropdown chevron)
```

### TimeRangePicker Sub-component:
- Uses: Button (secondary, md)
- Text: "Last 7d" or selected range
- Icon: calendar + chevron down
- Width: ~140px

### NotificationButton Sub-component:
- Uses: Button (tertiary, icon-only)
- Icon: bell (20px)
- Badge: positioned top-right, shows count if > 0

### UserMenu Sub-component:
```
UserMenu (Auto Layout, horizontal)
├── Avatar (md, 32px)
├── [UserName] (body/default, optional based on width)
└── ChevronDown (12px icon)
```

### Specifications:
- Left/Right padding: spacing/6 (24px)
- Item gap: spacing/4 (16px)
- Right section gap: spacing/3 (12px)

---

## COMPONENT 3: Breadcrumb

Purpose: Show navigation hierarchy and current location

### Specifications:
- Height: auto (based on content)
- Items separated by chevron icons

### Structure:
```
Breadcrumb (Auto Layout, horizontal)
├── BreadcrumbItem (link)
├── Separator (chevron icon, 12px)
├── BreadcrumbItem (link)
├── Separator
└── BreadcrumbItem (current, not a link)
```

### BreadcrumbItem Sub-component:

**Variants:**
- default: text/link color, clickable
- current: text/primary color, not clickable, body/emphasis

**States (for default):**
- default: text/link
- hover: text/link-hover, underline

### Specifications:
- Text style: body/small (12px)
- Separator: chevron-right, icon/muted, 12px
- Item gap: spacing/2 (8px)
- Max items shown: 4 (with ellipsis for longer paths)

---

## COMPONENT 4: TabBar

Purpose: Switch between views within a page

### Specifications:
- Width: 100% or fit-content
- Height: 48px
- Border bottom: 1px border/default

### Variants:

**variant** (property):
- underline: active tab has 2px bottom border (brand/primary)
- pill: active tab has brand/primary-light background, rounded

**size** (property):
- sm: 40px height, body/small text
- md: 48px height, body/default text

### Structure:
```
TabBar (Auto Layout, horizontal)
├── TabItem
├── TabItem (active)
├── TabItem
└── TabItem
```

### TabItem Sub-component:

**States:**
- default: text/secondary, transparent background
- hover: text/primary, background/elevated
- active (underline): text/primary, brand/primary 2px bottom border
- active (pill): brand/primary text, brand/primary-light background

### Specifications:
- Tab padding: spacing/4 (16px) horizontal
- Tab gap: spacing/1 (4px)
- Text style: label/large (14px/500)
- Active indicator: 2px brand/primary (for underline variant)
- Transition: 150ms for state changes

---

## FIGMA ORGANIZATION:

Create in: 🧱 Components > Composed > Navigation

Page layout:
```
┌─────────────────────────────────────────────────────────────────┐
│ Navigation Components                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Sidebar (expanded)           Sidebar (collapsed)                 │
│ ┌────────────────────┐       ┌────┐                             │
│ │ 🔷 Health Monitor  │       │ 🔷 │                             │
│ ├────────────────────┤       ├────┤                             │
│ │ 📊 Overview        │       │ 📊 │                             │
│ │ 💰 Cost        (3) │       │ 💰 │                             │
│ │ ⚡ Performance     │       │ ⚡ │                             │
│ │ 🔒 Security    (5) │       │ 🔒 │                             │
│ │ ✅ Reliability     │       │ ✅ │                             │
│ │ ────────────────── │       │ ── │                             │
│ │ 🔔 Alerts          │       │ 🔔 │                             │
│ │ 💬 Chat            │       │ 💬 │                             │
│ ├────────────────────┤       ├────┤                             │
│ │ ⚙️ Settings        │       │ ⚙️ │                             │
│ └────────────────────┘       └────┘                             │
│                                                                  │
│ TopBar                                                           │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Home > Cost    Cost Monitor    [Last 7d ▾] 🔄 🔔(3) 👤      ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ Breadcrumb                                                       │
│ Home > Cost > Workspace: Production > Alert Detail              │
│                                                                  │
│ TabBar (underline)                                               │
│ [Overview] [Alerts] [Settings] [Analytics]                      │
│  ─────────                                                       │
│                                                                  │
│ TabBar (pill)                                                    │
│ [Overview] [Alerts] [Settings] [Analytics]                      │
│ └────────┘ (filled)                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PRIMITIVES USED:

List of primitives reused in these components:
- Button (for TimeRangePicker, RefreshButton, CollapseToggle)
- Badge (for notification counts, NavItem alerts)
- Avatar (for UserMenu)
- Tooltip (for collapsed Sidebar hover labels)

If a primitive doesn't exist, it should NOT be created here.

---

Do NOT:
- Create new primitive components
- Create screens (just components)
- Use hardcoded colors or typography
- Duplicate existing primitives
- Add complex interactivity or animations
```

---

## 🎯 Expected Output

### Components Created (4)

| Component | Sub-components | Built From |
|-----------|----------------|------------|
| Sidebar | NavItem, NavDivider, SidebarHeader, SidebarFooter | Button, Badge, Tooltip |
| TopBar | TimeRangePicker, NotificationButton, UserMenu | Button, Badge, Avatar |
| Breadcrumb | BreadcrumbItem, Separator | - |
| TabBar | TabItem | - |

### Figma Structure

```
🧱 Components
└── Composed
    └── Navigation
        ├── Sidebar (with collapsed variant)
        │   └── NavItem (sub-component)
        ├── TopBar
        │   ├── TimeRangePicker
        │   ├── NotificationButton
        │   └── UserMenu
        ├── Breadcrumb
        │   └── BreadcrumbItem
        └── TabBar
            └── TabItem
```

---

## ✅ Verification Checklist

- [ ] All 4 navigation components created
- [ ] Sidebar has collapsed variant
- [ ] TopBar contains all required elements
- [ ] Components use existing primitives (Badge, Avatar, Button)
- [ ] Auto Layout applied to all
- [ ] States implemented (hover, active)
- [ ] Responsive constraints set

---

**Next:** [08-composed-data-display.md](08-composed-data-display.md)

