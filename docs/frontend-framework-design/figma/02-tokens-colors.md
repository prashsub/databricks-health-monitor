# 02 - Color Tokens

## Overview

Create the complete color system as Figma variables/styles based on the **official Databricks brand palette** (DATA+AI World Tour 2025). This is the foundation for all components.

---

## 🎨 Databricks Brand Color Reference

Based on official Databricks design system:

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Databricks Red** | 🔴 | `#FF3621` | Primary brand, CTAs, highlights |
| **Coral** | 🟠 | `#E8715E` | Secondary accent, table headers |
| **Salmon** | 🩷 | `#F4A89A` | Tertiary accent, hover states |
| **Blush** | 🩷 | `#F9D4CC` | Light backgrounds, cards |
| **Navy** | 🔵 | `#1B3A4B` | Dark headers, primary text |
| **Charcoal** | ⚫ | `#2D3E4A` | Secondary dark elements |
| **Cream** | 🟡 | `#F5F2ED` | Page backgrounds |
| **Off-white** | ⬜ | `#FAF9F7` | Card surfaces |
| **Teal** | 🔷 | `#077A9D` | Links, informational |
| **Green** | 🟢 | `#00A972` | Success states |

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create a comprehensive color token system for an enterprise monitoring dashboard using the official Databricks brand palette.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users (engineers, FinOps)
- Style: Official Databricks brand (DATA+AI World Tour 2025)
- Platform: Desktop web

Objective (this run only):
- Create ONLY color variables/tokens
- No components, no screens
- Organize into logical groups

Design system rules:
- Use Figma variables for all colors
- Group variables logically by purpose
- Include both light and dark mode values
- Use semantic naming (not "red-500", instead "primary")

---

CREATE THESE COLOR VARIABLES:

## Group: brand/
(Core Databricks brand colors)
- brand/primary: #FF3621 (Databricks Red - signature brand color)
- brand/primary-hover: #E02E1B (Darker red for hover states)
- brand/primary-light: #FFEBE8 (Light red for subtle backgrounds)
- brand/coral: #E8715E (Coral - secondary accent)
- brand/coral-light: #FDF0ED (Light coral background)
- brand/salmon: #F4A89A (Salmon - tertiary accent)
- brand/blush: #F9D4CC (Blush - very light accent)
- brand/teal: #077A9D (Teal - links, informational)
- brand/teal-hover: #065E7A (Darker teal for hover)

## Group: neutral/
(Navy-based neutral palette)
- neutral/navy: #1B3A4B (Dark navy - headers, emphasis)
- neutral/charcoal: #2D3E4A (Charcoal - secondary dark)
- neutral/slate: #4A5D6B (Slate - body text)
- neutral/steel: #6B7D8A (Steel - secondary text)
- neutral/silver: #9DAAB5 (Silver - muted text)
- neutral/ash: #C4CDD5 (Ash - borders, dividers)
- neutral/mist: #E0E6EB (Mist - subtle borders)
- neutral/cloud: #F0F3F5 (Cloud - hover backgrounds)

## Group: semantic/
(Status and feedback colors)
- semantic/success: #00A972 (Green - positive, health OK)
- semantic/success-light: #E6F7F1 (Light green background)
- semantic/warning: #FFAB00 (Amber - caution)
- semantic/warning-light: #FFF8E6 (Light amber background)
- semantic/critical: #FF3621 (Red - errors, critical)
- semantic/critical-light: #FFEBE8 (Light red background)
- semantic/info: #077A9D (Teal - informational)
- semantic/info-light: #E6F4F7 (Light teal background)

## Group: severity/
(Alert severity indicators - monitoring specific)
- severity/critical: #FF3621 (Immediate action required)
- severity/high: #E8715E (Coral - urgent attention)
- severity/medium: #FFAB00 (Amber - monitor closely)
- severity/low: #077A9D (Teal - informational)
- severity/success: #00A972 (Green - resolved/healthy)

## Group: chart/
(10-color palette for data visualization)
- chart/1: #FF3621 (Primary - Databricks Red)
- chart/2: #077A9D (Teal - secondary)
- chart/3: #00A972 (Green - success/positive)
- chart/4: #E8715E (Coral - attention)
- chart/5: #1B3A4B (Navy - dark contrast)
- chart/6: #FFAB00 (Amber - warning)
- chart/7: #F4A89A (Salmon - light accent)
- chart/8: #6B4FBB (Purple - ML/AI features)
- chart/9: #4A5D6B (Slate - neutral)
- chart/10: #99DDB4 (Mint - positive secondary)

## Group: background/
(Surface and canvas colors)
- background/canvas: #F5F2ED (Warm cream - page background)
- background/canvas-dark: #0F1419 (Near black - dark mode)
- background/surface: #FFFFFF (White - card/widget)
- background/surface-alt: #FAF9F7 (Off-white - alternate surface)
- background/surface-dark: #1B3A4B (Navy - dark mode cards)
- background/elevated: #FEFEFE (Pure white - elevated elements)
- background/overlay: rgba(27,58,75,0.6) (Navy overlay for modals)
- background/highlight: #FDF0ED (Light coral - highlight rows)

## Group: text/
(Typography colors)
- text/primary: #1B3A4B (Navy - main text)
- text/secondary: #4A5D6B (Slate - labels, secondary)
- text/muted: #9DAAB5 (Silver - disabled, placeholder)
- text/inverse: #FFFFFF (White - on dark backgrounds)
- text/link: #077A9D (Teal - links)
- text/link-hover: #065E7A (Darker teal - link hover)
- text/brand: #FF3621 (Red - brand emphasis)

## Group: border/
(Border and divider colors)
- border/default: #E0E6EB (Mist - standard borders)
- border/strong: #C4CDD5 (Ash - emphasized borders)
- border/subtle: #F0F3F5 (Cloud - subtle dividers)
- border/focus: #077A9D (Teal - focus rings)
- border/error: #FF3621 (Red - error state)
- border/success: #00A972 (Green - success state)
- border/brand: #E8715E (Coral - brand accent borders)

## Group: icon/
(Iconography colors)
- icon/default: #4A5D6B (Slate - default icons)
- icon/primary: #FF3621 (Red - primary action icons)
- icon/secondary: #077A9D (Teal - secondary icons)
- icon/muted: #9DAAB5 (Silver - muted icons)
- icon/inverse: #FFFFFF (White - icons on dark)
- icon/success: #00A972 (Green - success icons)
- icon/warning: #FFAB00 (Amber - warning icons)
- icon/critical: #FF3621 (Red - critical icons)

## Group: table/
(Table-specific colors from Databricks design)
- table/header-dark: #1B3A4B (Navy header background)
- table/header-accent: #E8715E (Coral header variant)
- table/row-default: #FFFFFF (White row)
- table/row-alt: #FAF9F7 (Off-white alternate)
- table/row-hover: #F5F2ED (Cream hover)
- table/row-selected: #FDF0ED (Light coral selected)
- table/border: #E0E6EB (Mist borders)

---

ORGANIZATION:
- Create a "🎨 Tokens" page in Figma
- Add a "Colors" section/frame
- Display each color group as a row of swatches
- Each swatch: 80px × 80px square with the color
- Label below each swatch with variable name and hex value
- Group swatches by category with section headers

SWATCH DISPLAY FORMAT:
┌────────────┐
│            │  ← 80×80 filled with color
│  #FF3621   │
├────────────┤
│ primary    │  ← 12px label below
└────────────┘

Do NOT:
- Create any components
- Create any screens
- Add gradients or effects
- Use colors outside this defined palette
```

---

## 🎯 Expected Output

After running this prompt, you should have:

### Variables Created (68 total)

| Group | Count | Variables |
|-------|-------|-----------|
| brand/ | 9 | primary, primary-hover, primary-light, coral, coral-light, salmon, blush, teal, teal-hover |
| neutral/ | 8 | navy, charcoal, slate, steel, silver, ash, mist, cloud |
| semantic/ | 8 | success, success-light, warning, warning-light, critical, critical-light, info, info-light |
| severity/ | 5 | critical, high, medium, low, success |
| chart/ | 10 | 1-10 |
| background/ | 8 | canvas, canvas-dark, surface, surface-alt, surface-dark, elevated, overlay, highlight |
| text/ | 7 | primary, secondary, muted, inverse, link, link-hover, brand |
| border/ | 7 | default, strong, subtle, focus, error, success, brand |
| icon/ | 8 | default, primary, secondary, muted, inverse, success, warning, critical |
| table/ | 7 | header-dark, header-accent, row-default, row-alt, row-hover, row-selected, border |

### Visual Reference Frame

A "Colors" frame showing all swatches organized by group with Databricks branding.

---

## ✅ Verification Checklist

After running the prompt:

- [ ] All 68 color variables are created
- [ ] Variables are organized into 10 groups
- [ ] Primary brand color is Databricks Red (#FF3621)
- [ ] Page background uses warm cream (#F5F2ED)
- [ ] Navy (#1B3A4B) is used for dark elements
- [ ] Coral (#E8715E) is used for accent elements
- [ ] Visual swatch reference is created
- [ ] No hardcoded colors (all use variables)

---

## 🔗 Color Usage Reference

| Use Case | Variable | Hex |
|----------|----------|-----|
| Primary button background | brand/primary | #FF3621 |
| Button hover | brand/primary-hover | #E02E1B |
| Page background | background/canvas | #F5F2ED |
| Card background | background/surface | #FFFFFF |
| Main body text | text/primary | #1B3A4B |
| Secondary text | text/secondary | #4A5D6B |
| Links | text/link | #077A9D |
| Standard border | border/default | #E0E6EB |
| Table header (dark) | table/header-dark | #1B3A4B |
| Table header (accent) | table/header-accent | #E8715E |
| Alert critical | severity/critical | #FF3621 |
| Alert high | severity/high | #E8715E |
| Success state | semantic/success | #00A972 |
| Chart primary line | chart/1 | #FF3621 |

---

## 🎨 Theme Comparison

| Element | Old Theme | New Databricks Theme |
|---------|-----------|---------------------|
| Primary color | Teal #077A9D | Red #FF3621 |
| Page background | Cool gray #F7F9FA | Warm cream #F5F2ED |
| Dark elements | Charcoal #11171C | Navy #1B3A4B |
| Accent color | Purple #6B4FBB | Coral #E8715E |
| Text primary | Dark gray #11171C | Navy #1B3A4B |
| Table headers | Dark gray | Navy or Coral |

---

**Next:** [03-tokens-typography.md](03-tokens-typography.md)

