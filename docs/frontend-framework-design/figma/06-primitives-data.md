# 06 - Data Primitives

## Overview

Create data-focused primitive components: Table, Tooltip, Skeleton, Spinner, ProgressBar, and StatusIndicator. These support data visualization and loading states.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create data-focused primitive UI components for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users viewing large datasets
- Style: Clean enterprise SaaS, data-dense
- Platform: Desktop web

Objective (this run only):
- Create 6 data primitive components with full variants
- No screens, no composed components
- Place in Components/Primitives section

Follow Guidelines.md for design system alignment.

Design system rules:
- Reuse existing tokens (colors, typography, spacing)
- Use Auto Layout on all components
- Create variants for different states and sizes
- Semantic naming for all layers

---

## COMPONENT 1: Table

Purpose: Display tabular data with sorting and selection

### Sub-components to create:

**TableHeader** (single header row):
- Height: 48px
- Background: background/elevated (#FAFBFC)
- Border bottom: 2px border/default
- Cell padding: spacing/4 (16px) horizontal

**TableHeaderCell**:
- Text style: heading/h4 (14px/600)
- Text color: text/secondary
- Align: left (default), right (numbers), center (status)
- Sort indicator: chevron icon (12px) after text
- Variants for sortable (boolean) and sorted (none/asc/desc)

**TableRow**:
- Height: size/row-default (48px)
- Background: background/surface (white)
- Border bottom: 1px border/default
- Hover: background/elevated
- Selected: brand/primary-light background
- Variants: default, hover, selected, disabled

**TableCell**:
- Text style: body/default (14px/400)
- Text color: text/primary
- Padding: spacing/4 (16px) horizontal, spacing/3 (12px) vertical
- Variants for alignment: left, center, right

**TableRowActions** (appears on hover):
- Position: right edge of row
- Background: gradient from transparent to background/surface
- Contains: icon buttons (24px each)

### Complete Table structure:
```
Table (Auto Layout, vertical)
├── TableHeader
│   ├── TableHeaderCell (checkbox, 48px width)
│   ├── TableHeaderCell (name)
│   ├── TableHeaderCell (value, right-aligned)
│   ├── TableHeaderCell (status, center)
│   └── TableHeaderCell (actions, 80px width)
├── TableRow
│   ├── TableCell (checkbox)
│   ├── TableCell (text)
│   ├── TableCell (number, right-aligned)
│   ├── TableCell (badge/status)
│   └── TableRowActions
├── TableRow (alternate background)
└── ...
```

### Specifications:
- Min width: 600px
- Border: 1px border/default around entire table
- Border radius: radius/md (8px)
- Zebra striping: alternate rows use background/elevated

---

## COMPONENT 2: Tooltip

Purpose: Additional information on hover

### Variants:

**position** (property):
- top: arrow points down
- bottom: arrow points up
- left: arrow points right
- right: arrow points left

**size** (property):
- sm: max-width 200px, body/small text (12px)
- md: max-width 280px, body/default text (14px)
- lg: max-width 360px, body/default text (14px)

### Structure:
```
Tooltip (Auto Layout, vertical)
├── Content (text, can include simple formatting)
└── Arrow (6px triangle)
```

### Specifications:
- Background: text/primary (#11171C) - dark tooltip
- Text color: text/inverse (#FFFFFF)
- Padding: spacing/2 (8px) horizontal, spacing/2 (8px) vertical
- Border radius: radius/sm (4px)
- Shadow: elevation/3
- Arrow: 6px equilateral triangle, same color as background

---

## COMPONENT 3: Skeleton

Purpose: Loading placeholder that mimics content shape

### Variants:

**variant** (property):
- text: single line, height 16px, width varies
- title: single line, height 24px, width 60%
- paragraph: 3 lines with varying widths (100%, 100%, 70%)
- avatar: circle, matches avatar sizes
- card: rectangle with header + content areas
- chart: rectangle with chart-like placeholder
- row: horizontal bar for table rows

**size** (property for text/title):
- sm: 60px width
- md: 120px width
- lg: 200px width
- full: 100% width

### Structure:
```
Skeleton (frame)
└── AnimatedBar (rectangle with shimmer gradient)
```

### Specifications:
- Background: linear gradient from #E0E4E8 to #F0F0F0 to #E0E4E8
- Border radius: radius/sm (4px)
- Animation hint: show as gradient (actual animation in code)
- Opacity: subtle pulsing effect representation

---

## COMPONENT 4: Spinner

Purpose: Loading indicator for actions

### Variants:

**size** (property):
- sm: 16px
- md: 24px
- lg: 32px
- xl: 48px

**color** (property):
- primary: brand/primary (#2272B4)
- inverse: text/inverse (#FFFFFF) - for dark backgrounds
- muted: text/muted (#9CA3AF)

### Structure:
```
Spinner (frame)
└── SpinnerCircle (arc shape, 270° stroke)
```

### Specifications:
- Stroke width: 2px (sm), 3px (md/lg), 4px (xl)
- Shape: Circle with 270° arc (gap at top)
- Animation hint: show rotation position
- Background: none (transparent)

---

## COMPONENT 5: ProgressBar

Purpose: Show completion or progress

### Variants:

**variant** (property):
- default: brand/primary fill
- success: semantic/success fill
- warning: semantic/warning fill
- critical: semantic/critical fill

**size** (property):
- sm: 4px height
- md: 8px height
- lg: 12px height

**hasLabel** (boolean):
- true: show percentage label to the right
- false: bar only

**isIndeterminate** (boolean):
- true: show indeterminate animation (moving gradient)
- false: show determinate progress

### Structure:
```
ProgressBar (Auto Layout, horizontal)
├── ProgressTrack (full width, background/elevated)
│   └── ProgressFill (percentage width, colored)
└── [Label] (optional, "75%")
```

### Specifications:
- Track background: background/elevated (#FAFBFC)
- Track border radius: radius/full
- Fill border radius: radius/full
- Label: body/small, text/secondary, spacing/2 gap from bar
- Min width: 100px
- Transition: width changes smoothly

---

## COMPONENT 6: StatusIndicator

Purpose: Show entity status with color and optional label

### Variants:

**status** (property):
- active: semantic/success (#00A972)
- inactive: text/muted (#9CA3AF)
- warning: semantic/warning (#FFAB00)
- critical: semantic/critical (#FF3621)
- pending: brand/secondary (#6B4FBB)

**size** (property):
- sm: 8px dot
- md: 10px dot
- lg: 12px dot

**hasLabel** (boolean):
- true: show status text label
- false: dot only

**hasPulse** (boolean):
- true: show pulse ring animation indicator
- false: static dot

### Structure:
```
StatusIndicator (Auto Layout, horizontal)
├── StatusDot (circle, colored)
│   └── [PulseRing] (optional, larger circle, faded)
└── [Label] (optional, body/small text)
```

### Specifications:
- Dot: solid circle with status color
- Pulse ring: 150% size of dot, 30% opacity, same color
- Label: body/small, text/secondary
- Gap: spacing/2 (8px) between dot and label

---

## FIGMA ORGANIZATION:

Add to: 🧱 Components > Primitives

Page layout:
```
┌─────────────────────────────────────────────────────────────────┐
│ Data Primitives                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Table Components                                                 │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Header │ Name        │ Value    │ Status  │ Actions │       │  │
│ ├────────┼─────────────┼──────────┼─────────┼─────────┤       │  │
│ │ □      │ Item name   │ $1,234   │ ●Active │ ⚙️       │       │  │
│ │ □      │ Another item│ $5,678   │ ●Warning│ ⚙️       │       │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ Tooltip                                                          │
│ ┌──────────────────┐                                            │
│ │ Tooltip content  │                                            │
│ │        ▼        │ ← showing different positions               │
│ └──────────────────┘                                            │
│                                                                  │
│ Skeleton                                                         │
│ ░░░░░░░░░░░░░░░░  (text)                                        │
│ ░░░░░░░░░░░░░░░░░░░░░░░░ (paragraph)                            │
│ ○ (avatar)                                                       │
│                                                                  │
│ Spinner                                                          │
│ ○ ○ ○ ○ ← size variants                                         │
│                                                                  │
│ ProgressBar                                                      │
│ ████████░░░░░░░░ 75%                                            │
│ (show all color variants)                                        │
│                                                                  │
│ StatusIndicator                                                  │
│ ● Active  ● Inactive  ● Warning  ● Critical  ● Pending          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

Do NOT:
- Create composed components (those come later)
- Create screens
- Use hardcoded colors (use variables)
- Create separate components instead of variants
- Add real data (use placeholder content)
- Implement actual animations (just show states)
```

---

## 🎯 Expected Output

### Components Created (6)

| Component | Sub-components | Variants |
|-----------|----------------|----------|
| Table | TableHeader, TableHeaderCell, TableRow, TableCell, TableRowActions | Sorting, selection states |
| Tooltip | - | 4 positions × 3 sizes |
| Skeleton | - | 7 variants × multiple sizes |
| Spinner | - | 4 sizes × 3 colors |
| ProgressBar | - | 4 colors × 3 sizes × label × indeterminate |
| StatusIndicator | - | 5 statuses × 3 sizes × label × pulse |

### Figma Structure

```
🧱 Components
└── Primitives
    ├── Button, Badge, Card, Input, Chip, Avatar (from previous)
    ├── Table (component set)
    │   ├── TableHeader
    │   ├── TableHeaderCell
    │   ├── TableRow
    │   ├── TableCell
    │   └── TableRowActions
    ├── Tooltip (component set)
    ├── Skeleton (component set)
    ├── Spinner (component set)
    ├── ProgressBar (component set)
    └── StatusIndicator (component set)
```

---

## ✅ Verification Checklist

- [ ] All 6 components created
- [ ] Table has all sub-components
- [ ] Auto Layout on all components
- [ ] Variants use properties correctly
- [ ] Colors use token variables
- [ ] Loading states are represented
- [ ] Semantic layer naming

---

**Next:** [07-composed-navigation.md](07-composed-navigation.md)

