# 04 - Spacing Tokens

## Overview

Create the spacing system, border radius, shadow, and layout grid variables. These ensure consistent spatial rhythm throughout the design.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create a comprehensive spacing and effects token system for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users with data-dense interfaces
- Style: Clean, consistent spacing for scannability
- Grid: 4px base unit system

Objective (this run only):
- Create spacing variables
- Create border radius variables
- Create shadow/elevation effects
- Create layout grid configuration
- No components, no screens

Follow Guidelines.md for design system alignment.

Design system rules:
- Use Figma variables for spacing
- Base unit is 4px (all spacing should be multiples of 4)
- Consistent naming pattern
- Include visual reference for each value

---

CREATE THESE SPACING VARIABLES:

## Group: spacing/
(All based on 4px base unit)

- spacing/0: 0px (none)
- spacing/1: 4px (tight - icon gaps)
- spacing/2: 8px (compact - inline spacing)
- spacing/3: 12px (default - form gaps)
- spacing/4: 16px (comfortable - card padding)
- spacing/5: 20px (relaxed - section gaps)
- spacing/6: 24px (standard card padding)
- spacing/8: 32px (page margins)
- spacing/10: 40px (large gaps)
- spacing/12: 48px (major sections)
- spacing/16: 64px (page sections)
- spacing/20: 80px (hero spacing)
- spacing/24: 96px (large hero)

## Group: radius/
(Border radius values)

- radius/none: 0px (sharp edges)
- radius/sm: 4px (inputs, small elements)
- radius/md: 8px (buttons, cards)
- radius/lg: 12px (modals, large cards)
- radius/xl: 16px (hero cards)
- radius/full: 9999px (pills, avatars, badges)

## Group: size/
(Fixed component sizes)

- size/icon-sm: 16px (small icons)
- size/icon-md: 20px (default icons)
- size/icon-lg: 24px (large icons)
- size/avatar-sm: 24px (small avatar)
- size/avatar-md: 32px (default avatar)
- size/avatar-lg: 40px (large avatar)
- size/avatar-xl: 56px (profile avatar)
- size/button-sm: 32px (small button height)
- size/button-md: 40px (default button height)
- size/button-lg: 48px (large button height)
- size/input-sm: 32px (small input height)
- size/input-md: 40px (default input height)
- size/input-lg: 48px (large input height)
- size/row-compact: 40px (compact table row)
- size/row-default: 48px (default table row)
- size/row-comfortable: 56px (comfortable row)

---

CREATE THESE SHADOW EFFECTS:

## Group: elevation/
(Box shadows for depth)

- elevation/1
  Shadow: 0px 1px 2px rgba(0, 0, 0, 0.05)
  Usage: Cards at rest, subtle depth

- elevation/2
  Shadow: 0px 4px 6px rgba(0, 0, 0, 0.07)
  Usage: Hover states, raised elements

- elevation/3
  Shadow: 0px 10px 15px rgba(0, 0, 0, 0.1)
  Usage: Modals, floating panels

- elevation/4
  Shadow: 0px 20px 25px rgba(0, 0, 0, 0.15)
  Usage: Dropdowns, popovers

- elevation/focus
  Shadow: 0px 0px 0px 2px rgba(7, 122, 157, 0.25)
  Usage: Focus rings on inputs

---

CREATE LAYOUT GRID:

## Desktop Grid (1440px)
- Type: Column grid
- Columns: 12
- Gutter: 24px
- Margin: 32px
- Column width: Auto-fill

## Dashboard Grid (6-column for widgets)
- Type: Column grid
- Columns: 6
- Gutter: 24px
- Margin: 0px
- Usage: Dashboard widget layout

---

ORGANIZATION:
- Add to the "🎨 Tokens" page in Figma
- Create sections: "Spacing", "Radius", "Sizes", "Elevation"

SPACING VISUALIZATION:
For each spacing value, show:
┌──────────────────────────────────────┐
│ spacing/4 = 16px                     │
│ [████████████████]  ← visual bar     │
└──────────────────────────────────────┘

Show bars at proportional widths to visualize the scale.

RADIUS VISUALIZATION:
For each radius value, show:
┌─────────────────────────────┐
│ radius/md = 8px             │
│ ┌────────────────────┐      │
│ │                    │ ← box │
│ └────────────────────┘      │
└─────────────────────────────┘

Show squares with the actual border radius applied.

SHADOW VISUALIZATION:
For each elevation, show:
┌─────────────────────────────┐
│ elevation/2                 │
│ ┌────────────────────┐      │
│ │    Sample Card     │ ← with│
│ └────────────────────┘ shadow│
└─────────────────────────────┘

SIZE VISUALIZATION:
Show component size references:
┌─────────────────────────────┐
│ Button Heights:             │
│ [sm] 32px                   │
│ [md ] 40px                  │
│ [lg  ] 48px                 │
└─────────────────────────────┘

Do NOT:
- Create any components
- Create any screens
- Use spacing values not in this system
- Add complex visual effects beyond defined shadows
```

---

## 🎯 Expected Output

After running this prompt, you should have:

### Variables Created (45+ total)

| Group | Count | Variables |
|-------|-------|-----------|
| spacing/ | 13 | 0-24 scale |
| radius/ | 6 | none through full |
| size/ | 16 | icons, avatars, buttons, inputs, rows |
| elevation/ | 5 | 1-4 plus focus |

### Visual Reference Frames

- Spacing scale visualization
- Border radius samples
- Shadow/elevation samples
- Size reference chart

### Layout Grids

- 12-column desktop grid (1440px)
- 6-column dashboard grid

---

## ✅ Verification Checklist

After running the prompt:

- [ ] All spacing variables created (4px multiples)
- [ ] All radius variables created
- [ ] All size variables created
- [ ] All elevation effects created
- [ ] Layout grids are configured
- [ ] Visual references are created

---

## 🔗 Spacing Usage Reference

| Use Case | Variable |
|----------|----------|
| Icon to text gap | spacing/2 (8px) |
| Input padding | spacing/3 (12px) |
| Card internal padding | spacing/6 (24px) |
| Page margins | spacing/8 (32px) |
| Section separation | spacing/12 (48px) |
| Button corner | radius/md (8px) |
| Badge corner | radius/full |
| Card shadow (rest) | elevation/1 |
| Card shadow (hover) | elevation/2 |
| Modal shadow | elevation/3 |
| Default button height | size/button-md (40px) |

---

## 📐 Component Spacing Presets

For reference when building components:

### Card Padding
```
Outer padding: spacing/6 (24px)
Header to content: spacing/4 (16px)
Content items: spacing/3 (12px)
```

### Button Padding
```
Horizontal: spacing/4 (16px) - spacing/6 (24px)
Vertical: automatic from height
Icon to text: spacing/2 (8px)
```

### Table Spacing
```
Cell padding horizontal: spacing/4 (16px)
Cell padding vertical: spacing/3 (12px)
Header padding: spacing/4 (16px)
Row height: size/row-default (48px)
```

### Form Spacing
```
Label to input: spacing/2 (8px)
Input to input: spacing/4 (16px)
Section to section: spacing/6 (24px)
```

---

**Next:** [05-primitives-core.md](05-primitives-core.md)






