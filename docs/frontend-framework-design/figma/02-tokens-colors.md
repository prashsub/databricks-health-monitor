# 02 - Color Tokens

## Overview

Create the complete color system as Figma variables/styles based on the **official Databricks brand palette** (extracted from authentic Databricks CSS). This is the foundation for all components.

**⚠️ IMPORTANT: Official Databricks Colors**
- **Blue (#2272B4)** = Primary interactive color (buttons, links) - Databricks Blue-600
- **Navy (#143D4A)** = Secondary emphasis (headers, secondary buttons) - Databricks Navy-700
- **Lava Red (#FF3621)** = Critical/destructive ONLY (alerts, delete buttons) - Databricks Lava-600
- **Oat (#F9F7F4)** = Warm background - Databricks Oat-Light

---

## 🎨 Official Databricks Color Palette

Based on **authentic Databricks design system CSS** (bf-color-* classes):

| Role | Color | Hex | Official Class |
|------|-------|-----|----------------|
| **Blue** | 🔵 | `#2272B4` | `blue-600` **PRIMARY** - Buttons, links |
| **Navy** | 🔵 | `#143D4A` | `navy-700` Secondary buttons, headers |
| **Lava Red** | 🔴 | `#FF3621` | `lava-600-primary` Brand, critical alerts |
| **Green** | 🟢 | `#00A972` | `green-600` Success states |
| **Yellow** | 🟡 | `#FFAB00` | `yellow-600` Warning states |
| **Oat Light** | 🟡 | `#F9F7F4` | `oat-light` Page backgrounds |
| **Oat Medium** | 🟡 | `#EEEDE9` | `oat-medium` Card surfaces |
| **Navy Primary** | ⚫ | `#0B2026` | `navy-900-primary` Darkest text |
| **Gray Text** | ⚫ | `#5A6F77` | `gray-text` Secondary text |
| **White** | ⬜ | `#FFFFFF` | `white` Pure white |

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

## Group: interactive/
(Primary interactive colors - buttons, links, focus states - OFFICIAL DATABRICKS)
- interactive/primary: #2272B4 (Blue-600 - PRIMARY interactive color)
- interactive/primary-hover: #0E538B (Blue-700 - darker blue for hover)
- interactive/primary-light: #F0F8FF (Blue-100 - light blue backgrounds)
- interactive/secondary: #143D4A (Navy-700 - secondary buttons, emphasis)
- interactive/secondary-hover: #1B3139 (Navy-800 - darker navy for hover)
- interactive/destructive: #FF3621 (Lava-600 - delete/remove actions ONLY)
- interactive/destructive-hover: #BD2B26 (Lava-700 - darker red for hover)

## Group: brand/
(Databricks brand accent colors - OFFICIAL LAVA & MAROON)
- brand/lava-primary: #FF3621 (Lava-600 - Databricks brand red)
- brand/lava-light: #FAECEB (Lava-100 - light red backgrounds)
- brand/lava-medium: #FF5F46 (Lava-500 - high severity accent)
- brand/lava-soft: #FF9E94 (Lava-400 - softer red)
- brand/maroon: #AB4057 (Maroon-500 - alternate brand accent)
- brand/maroon-light: #F8D5DC (Maroon-100 - light maroon background)

## Group: neutral/
(OFFICIAL Databricks Navy & Gray palette)
- neutral/navy-darkest: #0B2026 (Navy-900-primary - darkest, primary text)
- neutral/navy-dark: #1B3139 (Navy-800 - headers, dark elements)
- neutral/navy: #143D4A (Navy-700 - body text, emphasis)
- neutral/navy-medium: #1B5162 (Navy-600 - medium emphasis)
- neutral/gray-text: #5A6F77 (Gray-text - secondary text)
- neutral/gray-navigation: #303F47 (Gray-navigation - nav elements)
- neutral/navy-muted: #618794 (Navy-500 - muted elements)
- neutral/navy-light: #90A5B1 (Navy-400 - disabled states)
- neutral/navy-subtle: #C4CCD6 (Navy-300 - subtle borders)
- neutral/gray-lines: #DCE0E2 (Gray-lines - dividers)
- neutral/navy-faint: #E5EAF1 (Navy-200 - very light backgrounds)

## Group: semantic/
(OFFICIAL Databricks status colors - EXACT MATCHES!)
- semantic/success: #00A972 (Green-600 - positive, health OK) ✅
- semantic/success-light: #DCF4ED (Green-100 - light green background)
- semantic/warning: #FFAB00 (Yellow-600 - caution) ✅
- semantic/warning-light: #FFF0D3 (Yellow-100 - light yellow background)
- semantic/critical: #FF3621 (Lava-600 - errors, critical) ✅
- semantic/critical-light: #FAECEB (Lava-100 - light red background)
- semantic/info: #2272B4 (Blue-600 - informational)
- semantic/info-light: #F0F8FF (Blue-100 - light blue background)

## Group: severity/
(OFFICIAL Databricks severity - RED RESERVED FOR CRITICAL)
- severity/critical: #FF3621 (Lava-600 - immediate action required) ✅
- severity/high: #FF5F46 (Lava-500 - urgent attention)
- severity/medium: #FFAB00 (Yellow-600 - monitor closely) ✅
- severity/low: #5A6F77 (Gray-text - informational, non-urgent)
- severity/success: #00A972 (Green-600 - resolved/healthy) ✅

## Group: chart/
(OFFICIAL Databricks 10-color palette - Blue first, Lava last)
- chart/1: #2272B4 (Blue-600 - PRIMARY data series) ✅
- chart/2: #143D4A (Navy-700 - secondary series)
- chart/3: #00A972 (Green-600 - positive/success) ✅
- chart/4: #98102A (Maroon-600 - ML/AI features, purple-ish)
- chart/5: #FFAB00 (Yellow-600 - warning/caution) ✅
- chart/6: #FF5F46 (Lava-500 - attention)
- chart/7: #FF3621 (Lava-600 - negative/critical ONLY) ✅
- chart/8: #FF9E94 (Lava-400 - light accent)
- chart/9: #5A6F77 (Gray-text - neutral)
- chart/10: #70C4AB (Green-400 - positive secondary)

## Group: background/
(OFFICIAL Databricks Oat backgrounds & surfaces)
- background/canvas: #F9F7F4 (Oat-light - page background) ✅
- background/canvas-dark: #0B2026 (Navy-900 - dark mode canvas)
- background/surface: #FFFFFF (White - card/widget) ✅
- background/surface-alt: #EEEDE9 (Oat-medium - alternate surface)
- background/surface-dark: #143D4A (Navy-700 - dark mode cards)
- background/elevated: #FFFFFF (White - elevated elements)
- background/overlay: rgba(27,49,57,0.6) (Navy-800 overlay for modals)
- background/highlight: #FAECEB (Lava-100 - highlight rows)

## Group: text/
(OFFICIAL Databricks typography colors)
- text/primary: #0B2026 (Navy-900-primary - main text, darkest) ✅
- text/secondary: #5A6F77 (Gray-text - labels, secondary)
- text/muted: #90A5B1 (Navy-400 - disabled, placeholder)
- text/inverse: #FFFFFF (White - on dark backgrounds) ✅
- text/link: #2272B4 (Blue-600 - links, clickable text)
- text/link-hover: #0E538B (Blue-700 - link hover)
- text/success: #00A972 (Green-600 - positive values) ✅
- text/warning: #BA7B23 (Yellow-700 - warning values, darker for text)
- text/critical: #FF3621 (Lava-600 - critical values ONLY) ✅

## Group: border/
(OFFICIAL Databricks border & divider colors)
- border/default: #DCE0E2 (Gray-lines - standard borders) ✅
- border/strong: #C4CCD6 (Navy-300 - emphasized borders)
- border/subtle: #EDF2F8 (Navy-100 - subtle dividers)
- border/focus: #2272B4 (Blue-600 - focus rings)
- border/error: #FF3621 (Lava-600 - error state) ✅
- border/success: #00A972 (Green-600 - success state) ✅
- border/brand: #FF5F46 (Lava-500 - brand accent borders)

## Group: icon/
(OFFICIAL Databricks iconography colors)
- icon/default: #5A6F77 (Gray-text - default icons)
- icon/interactive: #2272B4 (Blue-600 - clickable icons, primary)
- icon/muted: #90A5B1 (Navy-400 - muted icons)
- icon/inverse: #FFFFFF (White - icons on dark) ✅
- icon/success: #00A972 (Green-600 - success icons) ✅
- icon/warning: #FFAB00 (Yellow-600 - warning icons) ✅
- icon/critical: #FF3621 (Lava-600 - critical icons ONLY) ✅

## Group: table/
(OFFICIAL Databricks table colors)
- table/header-dark: #143D4A (Navy-700 header background)
- table/header-accent: #FF5F46 (Lava-500 header variant)
- table/row-default: #FFFFFF (White row) ✅
- table/row-alt: #EEEDE9 (Oat-medium alternate)
- table/row-hover: #F9F7F4 (Oat-light hover)
- table/row-selected: #FAECEB (Lava-100 selected)
- table/border: #DCE0E2 (Gray-lines borders) ✅

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

### Variables Created (76 total) ✅ OFFICIAL DATABRICKS PALETTE

| Group | Count | Variables |
|-------|-------|-----------|
| interactive/ | 7 | primary (Blue-600), primary-hover, primary-light, secondary (Navy-700), secondary-hover, destructive (Lava-600), destructive-hover |
| brand/ | 6 | lava-primary, lava-light, lava-medium, lava-soft, maroon, maroon-light |
| neutral/ | 11 | navy-darkest (Navy-900), navy-dark (Navy-800), navy (Navy-700), navy-medium, gray-text, gray-navigation, navy-muted, navy-light, navy-subtle, gray-lines, navy-faint |
| semantic/ | 8 | success (Green-600) ✅, success-light, warning (Yellow-600) ✅, warning-light, critical (Lava-600) ✅, critical-light, info (Blue-600), info-light |
| severity/ | 5 | critical (Lava-600) ✅, high (Lava-500), medium (Yellow-600) ✅, low (Gray-text), success (Green-600) ✅ |
| chart/ | 10 | 1-10 (Blue-600 first, Lava-600 last) |
| background/ | 8 | canvas (Oat-light) ✅, canvas-dark, surface (White) ✅, surface-alt (Oat-medium), surface-dark, elevated, overlay, highlight |
| text/ | 9 | primary (Navy-900) ✅, secondary (Gray-text), muted, inverse, link (Blue-600), link-hover, success ✅, warning, critical ✅ |
| border/ | 7 | default (Gray-lines) ✅, strong, subtle, focus (Blue-600), error ✅, success ✅, brand |
| icon/ | 7 | default (Gray-text), interactive (Blue-600), muted, inverse, success ✅, warning ✅, critical ✅ |
| table/ | 7 | header-dark (Navy-700), header-accent (Lava-500), row-default ✅, row-alt (Oat-medium), row-hover (Oat-light), row-selected, border ✅ |

### Visual Reference Frame

A "Colors" frame showing all swatches organized by group with **Blue-600 as primary interactive color** (official Databricks palette).

---

## ✅ Verification Checklist

After running the prompt:

- [ ] All 76 color variables are created (OFFICIAL Databricks palette) ✅
- [ ] Variables are organized into 11 groups
- [ ] **Primary interactive color is Blue-600 (#2272B4)** - official Databricks blue!
- [ ] **Lava-600 Red (#FF3621) is reserved for critical/destructive only** ✅
- [ ] Page background uses Oat-light (#F9F7F4) - official Databricks background
- [ ] Navy-700 (#143D4A) is used for dark elements and headers
- [ ] Lava-500 (#FF5F46) is used for high severity, not primary
- [ ] Visual swatch reference is created
- [ ] No hardcoded colors (all use variables)
- [ ] ✅ markers indicate EXACT matches to Databricks official CSS

---

## 🔗 Color Usage Reference (OFFICIAL DATABRICKS)

| Use Case | Variable | Hex | Official Class | Notes |
|----------|----------|-----|----------------|-------|
| **Primary button** | interactive/primary | #2272B4 | blue-600 | Official Databricks blue ✅ |
| Primary button hover | interactive/primary-hover | #0E538B | blue-700 | Darker blue |
| Secondary button | interactive/secondary | #143D4A | navy-700 | Navy border + navy text |
| **Gray outline button** | border/default + text/primary | #DCE0E2 + #0B2026 | gray-lines + navy-900 | Gray border + DARKEST navy text! |
| Ghost button | text/secondary | #5A6F77 | gray-text | Gray text, no border |
| **Delete/destructive button** | interactive/destructive | #FF3621 | lava-600 | Red - ONLY for destructive ✅ |
| Page background | background/canvas | #F9F7F4 | oat-light | Warm oat ✅ |
| Card background | background/surface | #FFFFFF | white | White ✅ |
| Main body text | text/primary | #0B2026 | navy-900-primary | Darkest navy ✅ |
| Secondary text | text/secondary | #5A6F77 | gray-text | Gray text |
| Links | text/link | #2272B4 | blue-600 | Databricks blue ✅ |
| Standard border | border/default | #DCE0E2 | gray-lines | Gray lines ✅ |
| Table header (dark) | table/header-dark | #143D4A | navy-700 | Dark navy header |
| **Critical alert badge** | severity/critical | #FF3621 | lava-600 | Lava red - alerts ONLY ✅ |
| High alert badge | severity/high | #FF5F46 | lava-500 | High severity lava |
| Success state | semantic/success | #00A972 | green-600 | Green ✅ |
| **Chart primary line** | chart/1 | #2272B4 | blue-600 | Blue - not red! ✅ |

---

## 🎨 Color Philosophy (OFFICIAL DATABRICKS)

| Purpose | Color | Hex | Official Class | Rationale |
|---------|-------|-----|----------------|-----------|
| **Primary interactive** | Blue | #2272B4 | blue-600 ✅ | Official Databricks interactive color |
| **Secondary interactive** | Navy | #143D4A | navy-700 ✅ | Authoritative, secondary actions |
| **Critical/Destructive** | Lava Red | #FF3621 | lava-600 ✅ | Reserved for alerts & delete - Databricks brand |
| **High severity** | Lava Medium | #FF5F46 | lava-500 | Warmer than critical, urgent attention |
| **Warning** | Yellow | #FFAB00 | yellow-600 ✅ | Caution without alarm |
| **Success** | Green | #00A972 | green-600 ✅ | Positive, healthy |
| **Page background** | Oat Light | #F9F7F4 | oat-light ✅ | Warm, approachable, Databricks brand |
| **Text primary** | Navy Darkest | #0B2026 | navy-900 ✅ | Highest contrast, most professional |

### Why Official Databricks Colors Work
- **Brand consistency**: All colors extracted from authentic Databricks CSS
- **Red fatigue avoided**: Lava-600 reserved for critical only
- **Clear hierarchy**: Blue = action, Lava Red = alert, Green = success
- **Professional feel**: Enterprise-grade, matches Databricks products
- **Proven palette**: Used in production Databricks applications

---

**Next:** [03-tokens-typography.md](03-tokens-typography.md)

