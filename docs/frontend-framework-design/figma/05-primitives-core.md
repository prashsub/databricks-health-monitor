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
- primary: brand/primary background (#077A9D), text/inverse text
- secondary: transparent background, brand/primary border, brand/primary text
- tertiary: transparent background, no border, brand/primary text
- destructive: semantic/critical background (#FF3621), text/inverse text

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
- info: semantic/info-light background (#E8F5FA), brand/primary text
- success: semantic/success-light background (#E6F7F1), semantic/success text
- warning: semantic/warning-light background (#FFF8E6), text/primary text
- critical: semantic/critical-light background (#FFEBE8), semantic/critical text
- neutral: background/elevated (#FAFBFC), text/secondary

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

**padding** (property):
- none: 0px padding
- sm: spacing/4 (16px)
- md: spacing/6 (24px)
- lg: spacing/8 (32px)

**state** (property):
- default: normal
- hover: elevation/2 shadow (for interactive variant)
- selected: border/focus border (2px brand/primary)

### Structure:
```
Card (Auto Layout, vertical)
├── [Header Slot] (optional)
├── Content Slot
└── [Footer Slot] (optional)
```

### Specifications:
- Border radius: radius/md (8px)
- Border: 1px border/default
- Min width: 200px
- Background: background/surface (#FFFFFF)
- Header separator: 1px border/default (optional)

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

Purpose: Tags, filters, selections

### Variants:

**variant** (property):
- default: background/elevated background, text/primary text
- selected: brand/primary-light background, brand/primary text
- outlined: transparent background, border/default border

**size** (property):
- sm: height 24px, padding 8px, label/default (12px)
- md: height 32px, padding 12px, label/large (14px)

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
├── [Icon] (optional, 14px)
├── Label (text)
└── [RemoveIcon] (optional, 12px X icon)
```

### Specifications:
- Border radius: radius/full (9999px)
- Font weight: 500
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
- online: semantic/success (#00A972)
- offline: text/muted (#9CA3AF)
- busy: semantic/critical (#FF3621)
- away: semantic/warning (#FFAB00)

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

