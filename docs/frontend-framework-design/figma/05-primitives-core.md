# 05 - Core Primitives

## Overview

Create the foundational UI primitives: Button, Badge, Card, Input, Chip, and Avatar. These are the atomic building blocks for all composed components.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create core primitive UI components for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users (engineers, FinOps)
- Style: Clean enterprise SaaS, Databricks-native
- Platform: Desktop web

Objective (this run only):
- Create 6 primitive components with full variants
- No screens, no composed components
- Place in Components/Primitives section

Follow Guidelines.md for design system alignment.

Design system rules:
- Reuse existing tokens (colors, typography, spacing) from previous prompts
- Use Auto Layout on all components
- Create variants for size, emphasis, state
- Semantic naming for all layers
- Support responsive resizing

---

## COMPONENT 1: Button

Purpose: Primary interactive element for actions

### Variants (use Figma component properties):

**emphasis** (property):
- primary: Blue-600 background (#2272B4) ✅, white text
- secondary: White background, Navy-700 border (#143D4A), Navy-700 text
- tertiary: transparent background, no border, Blue-600 text (#2272B4) ✅
- destructive: Lava-600 background (#FF3621) ✅, white text

**size** (property):
- sm: height 32px, padding 12px horizontal, label/default text (12px)
- md: height 40px, padding 16px horizontal, label/large text (14px)
- lg: height 48px, padding 24px horizontal, body/default text (14px)

**state** (property):
- default: normal appearance
- hover: darken background 10%, elevation/2 shadow
- pressed: darken background 15%, scale 0.98
- disabled: 50% opacity, cursor not-allowed
- loading: show spinner icon, text says "Loading..."

**iconPosition** (property):
- none: text only
- leading: icon 16px before text, spacing/2 gap
- trailing: icon 16px after text, spacing/2 gap

### Structure:
```
Button (Auto Layout, horizontal)
├── [Icon] (optional, 16-20px based on size)
├── Label (text style based on size)
└── [Icon] (optional)
```

### Specifications:
- Border radius: radius/md (8px)
- Font weight: 500 (medium)
- Min width: 80px
- Gap between icon and text: spacing/2 (8px)
- Transition: 150ms ease

---

## COMPONENT 2: Badge

Purpose: Status indicators and labels

### Variants:

**severity** (property):
- info: Blue-200 background (#D7EDFE) ✅, Blue-600 text (#2272B4) ✅
- success: Green-100 background (#DCF4ED) ✅, Green-600 text (#00A972) ✅
- warning: Yellow-100 background (#FFF0D3) ✅, Yellow-700 text (#BA7B23) ✅
- critical: Lava-100 background (#FAECEB) ✅, Lava-600 text (#FF3621) ✅
- neutral: Navy-200 background (#E5EAF1) ✅, Navy-900 text (#0B2026) ✅

**size** (property):
- sm: height 20px, padding 6px horizontal, caption/default text (10px)
- md: height 24px, padding 8px horizontal, label/default text (12px)
- lg: height 28px, padding 10px horizontal, label/default text (12px)

**hasIcon** (boolean property):
- true: show 12px icon on left
- false: text only

### Structure:
```
Badge (Auto Layout, horizontal)
├── [Icon] (optional, 12px)
└── Label (text)
```

### Specifications:
- Border radius: radius/full (9999px) - pill shape
- Font weight: 500 (medium)
- Icon-text gap: spacing/1 (4px)
- Text transform: none (sentence case)

---

## COMPONENT 3: Card

Purpose: Container for content groupings

### Variants:

**variant** (property):
- default: background/surface, border/default border, elevation/1 shadow
- elevated: background/surface, no border, elevation/2 shadow
- outlined: background/surface, border/strong border, no shadow
- interactive: same as default, but hover shows elevation/2 + border/focus
- **accent-top**: default + colored 4px top border (NEW for professional signal/metric cards)
- **accent-top-sm**: default + colored 3px top border (NEW for topology nodes)

**accentColor** (property, only for accent-top/accent-top-sm variants):
- blue: border-top Blue-600 (#2272B4) ✅
- green: border-top Green-600 (#00A972) ✅
- maroon: border-top Maroon-500 (#AB4057) ✅
- red: border-top Lava-600 (#FF3621) ✅
- amber: border-top Yellow-600 (#FFAB00) ✅
- navy: border-top Navy-900 (#0B2026) ✅

**padding** (property):
- none: 0px padding
- sm: spacing/4 (16px)
- md: spacing/5 (20px) - NEW for professional card padding
- lg: spacing/6 (24px)
- xl: spacing/8 (32px)

**state** (property):
- default: normal
- hover: elevation-2 shadow (for interactive variant) OR border change to Blue-600 (#2272B4) ✅
- selected: border/focus border (2px brand/primary)

### Structure:
```
Card (Auto Layout, vertical)
├── [Accent Border] (optional, 4px or 3px top border based on variant)
├── [Header Slot] (optional)
├── Content Slot
└── [Footer Slot] (optional)
```

### Specifications:
- Border radius: radius/md (8px)
- Border: 1px Gray-lines (#DCE0E2) ✅
- Border-top (accent variants): 4px or 3px solid [accentColor]
- Min width: 200px
- Background: White (#FFFFFF) ✅
- Header separator: 1px Gray-lines (#DCE0E2) ✅ (optional)
- Box-shadow (default): 0 1px 2px rgba(0,0,0,0.05) - elevation-1 ✅
- Box-shadow (hover): 0 4px 12px rgba(7,122,157,0.15) for interactive

---

## COMPONENT 4: Input

Purpose: Text input field for forms

### Variants:

**size** (property):
- sm: height 32px, body/small text (12px)
- md: height 40px, body/default text (14px)
- lg: height 48px, body/large text (16px)

**state** (property):
- default: border/default border
- hover: border/strong border
- focused: border/focus border (2px), elevation/focus shadow
- error: border/error border, semantic/critical-light background tint
- disabled: 50% opacity, background/elevated background

**hasLabel** (boolean):
- true: show label above input
- false: input only

**hasHelper** (boolean):
- true: show helper text below input
- false: input only

**hasIcon** (boolean):
- true: show icon on left (20px)
- false: no icon

### Structure:
```
InputField (Auto Layout, vertical)
├── [Label] (label/default, text/primary)
├── InputContainer (Auto Layout, horizontal)
│   ├── [Icon] (optional, 20px, icon/muted)
│   ├── Input (text area)
│   └── [Clear Button] (optional, 16px icon)
└── [HelperText] (body/small, text/secondary or semantic/critical)
```

### Specifications:
- Border radius: radius/sm (4px)
- Border: 1px solid
- Padding horizontal: spacing/3 (12px)
- Background: background/surface
- Placeholder color: text/muted
- Icon-text gap: spacing/2 (8px)
- Label-input gap: spacing/2 (8px)
- Input-helper gap: spacing/1 (4px)

---

## COMPONENT 5: Chip

Purpose: Tags, filters, selections, status indicators

### Variants:

**variant** (property):
- default: background/elevated background, text/primary text
- selected: brand/primary-light background, brand/primary text
- outlined: transparent background, border/default border
- **status**: colored background with leading dot indicator (NEW for professional status chips)

**statusSeverity** (property, only for status variant):
- success: Green-100 (#DCF4ED) ✅ background, Green-600 (#00A972) ✅ text, Green dot
- warning: Yellow-100 (#FFF0D3) ✅ background, Yellow-700 (#BA7B23) ✅ text, Amber dot
- critical: Lava-100 (#FAECEB) ✅ background, Lava-600 (#FF3621) ✅ text, Red dot
- info: Blue-200 (#D7EDFE) ✅ background, Blue-600 (#2272B4) ✅ text, Blue dot
- neutral: Navy-200 (#E5EAF1) ✅ background, Navy-900 (#0B2026) ✅ text, Navy dot

**size** (property):
- sm: height 24px, padding 8px, label/badge (11px) - NEW for professional badges
- md: height 28px, padding 10px 12px, label/badge (11px) - NEW default for status chips
- lg: height 32px, padding 12px, label/large (14px)

**hasRemove** (boolean):
- true: show X icon on right (12px)
- false: no remove button

**hasIcon** (boolean):
- true: show icon on left (14px)
- false: no icon

**state** (property):
- default: normal
- hover: slightly darker background
- pressed: even darker background
- disabled: 50% opacity

### Structure:
```
Chip (Auto Layout, horizontal)
├── [LeadingDot] (optional, 6px circle for status variant) - NEW
├── [Icon] (optional, 14px)
├── Label (text)
└── [RemoveIcon] (optional, 12px X icon)
```

### Specifications (default/selected/outlined):
- Border radius: radius/full (9999px)
- Font weight: 500

### Specifications (status variant - NEW):
- Border radius: 4px (NOT full rounded - professional look)
- Border: none
- Leading dot: 6px circle, colored by statusSeverity
- Dot-label gap: spacing/1 (4px)
- Font weight: 500 (medium)
- Font: label/badge (11px)
- Padding: 8px horizontal, 6px vertical
- Icon-text gap: spacing/1 (4px)
- Text-remove gap: spacing/1 (4px)

---

## COMPONENT 6: Avatar

Purpose: User/entity visual identifier

### Variants:

**size** (property):
- sm: 24px × 24px
- md: 32px × 32px
- lg: 40px × 40px
- xl: 56px × 56px

**type** (property):
- image: show image fill
- initials: show 1-2 letter initials on colored background
- icon: show user icon on colored background

**hasStatus** (boolean):
- true: show status indicator dot (8px) at bottom-right
- false: no status indicator

**statusColor** (property, when hasStatus=true):
- online: Green-600 (#00A972) ✅
- offline: Navy-500 (#618794) ✅
- busy: Lava-600 (#FF3621) ✅
- away: Yellow-600 (#FFAB00) ✅

### Structure:
```
Avatar (frame with constraints)
├── AvatarContent (image, initials, or icon)
└── [StatusIndicator] (optional, positioned bottom-right)
```

### Specifications:
- Border radius: radius/full (circle)
- Initials background: brand/primary-light or other pastel
- Initials text: label/default, centered
- Status dot: 8px circle with 2px white border
- Status dot position: offset -2px from bottom-right

---

## FIGMA ORGANIZATION:

Create in: 🧱 Components > Primitives

Page layout:
```
┌─────────────────────────────────────────────────────────────────┐
│ Primitives                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Button                                                           │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ← emphasis variants         │
│ │Primary│ │Second│ │Tertia│ │Destru│                            │
│ └──────┘ └──────┘ └──────┘ └──────┘                             │
│ (show all size and state combinations below)                    │
│                                                                  │
│ Badge                                                            │
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ← severity variants          │
│ │Info│ │Succ│ │Warn│ │Crit│ │Neut│                              │
│ └────┘ └────┘ └────┘ └────┘ └────┘                              │
│                                                                  │
│ Card                                                             │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐                       │
│ │  Default  │ │  Elevated │ │  Outlined │                       │
│ └───────────┘ └───────────┘ └───────────┘                       │
│                                                                  │
│ Input                                                            │
│ (show all state variants)                                        │
│                                                                  │
│ Chip                                                             │
│ (show all variant combinations)                                 │
│                                                                  │
│ Avatar                                                           │
│ ○ ○ ○ ○ ← size variants                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## STATES TO INCLUDE:

For Button: default, hover, pressed, disabled, loading
For Input: default, hover, focused, error, disabled
For Card (interactive): default, hover, selected
For Chip: default, hover, pressed, disabled

---

Do NOT:
- Create composed components (those come later)
- Create screens
- Use hardcoded colors (use variables)
- Create duplicate variants
- Add complex animations
- Use external icon libraries (use simple placeholder shapes)
```

---

## 🎯 Expected Output

### Components Created (6)

| Component | Variants | States | Total Combinations |
|-----------|----------|--------|-------------------|
| Button | 4 emphasis × 3 sizes × 3 icon positions | 5 states | ~180 |
| Badge | 5 severity × 3 sizes × 2 icon options | 1 | 30 |
| Card | 4 variant × 4 padding | 3 states | 48 |
| Input | 3 sizes × 2 label × 2 helper × 2 icon | 5 states | ~240 |
| Chip | 3 variant × 2 sizes × 2 remove × 2 icon | 4 states | ~192 |
| Avatar | 4 sizes × 3 types × 2 status × 4 status colors | 1 | ~96 |

### Figma Structure

```
🧱 Components
└── Primitives
    ├── Button (component set with variants)
    ├── Badge (component set with variants)
    ├── Card (component set with variants)
    ├── Input (component set with variants)
    ├── Chip (component set with variants)
    └── Avatar (component set with variants)
```

---

## ✅ Verification Checklist

- [ ] All 6 components created
- [ ] Auto Layout applied to all components
- [ ] All variants use properties (not separate components)
- [ ] Colors use token variables
- [ ] Typography uses text styles
- [ ] Spacing uses spacing variables
- [ ] States are properly implemented
- [ ] Semantic layer naming (no "Frame 1")
- [ ] Components are in correct Figma location

---

**Next:** [06-primitives-data.md](06-primitives-data.md)

