# Colors - Design System

## Overview

Complete color palette for Databricks Health Monitor. Optimized for enterprise monitoring with excellent contrast and accessibility.

---

## 🎨 How to Use in Figma

### Option 1: Create Color Styles (Recommended)

1. **Open Figma** → Create a new file or your design file
2. **Go to** Local Styles panel (right sidebar)
3. **Click** the "+" next to "Color Styles"
4. **For each color below:**
   - Name it exactly as shown (e.g., `Primary/Brand`)
   - Enter the hex value
   - Add the description as the style description

### Option 2: Use Figma AI Prompt

Copy this prompt to Figma AI:
```
Create color styles with these exact values:
- Primary/Brand: #FF3621 (Databricks brand red)
- AI/Primary: #3B82F6 (All AI elements)
- Severity/Critical: #DC2626
- Severity/Warning: #F59E0B
- Severity/Success: #10B981
- Severity/Info: #3B82F6
- Background/Dark: #0F0F10
- Surface/Dark: #1A1A1B
- Text/Primary: #FFFFFF (dark mode), #111827 (light mode)
```

### Option 3: Import from Tokens

Use [Tokens Studio for Figma](https://tokens.studio/) plugin and import `design-tokens.json` (at bottom of this file).

---

## Primary Colors

### Brand Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Brand Red** | `#FF3621` | `rgb(255, 54, 33)` | Databricks logo, primary CTAs |
| **Brand Orange** | `#FF6B35` | `rgb(255, 107, 53)` | Hover states, accents |

### AI Colors (Unified Assistant)

**All AI elements use the same blue color for consistency.**

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **AI Blue** | `#3B82F6` | `rgb(59, 130, 246)` | AI icon, AI messages, AI badges |
| **AI Blue Light** | `#DBEAFE` | `rgb(219, 234, 254)` | AI message backgrounds |
| **AI Blue Dark** | `#1D4ED8` | `rgb(29, 78, 216)` | AI hover states |

---

## Severity Colors

Used for alerts, status indicators, and health scores.

| Severity | Hex | RGB | When to Use |
|----------|-----|-----|-------------|
| **Critical** | `#DC2626` | `rgb(220, 38, 38)` | System down, data loss risk, P1 |
| **High** | `#EF4444` | `rgb(239, 68, 68)` | Major issues, P2 |
| **Warning** | `#F59E0B` | `rgb(245, 158, 11)` | Degradation, threshold breached |
| **Info** | `#3B82F6` | `rgb(59, 130, 246)` | Informational, low priority |
| **Success** | `#10B981` | `rgb(16, 185, 129)` | Healthy, resolved, completed |

### Severity Backgrounds (for cards, badges)

| Severity | Background | Border | Text |
|----------|------------|--------|------|
| Critical | `#FEF2F2` | `#FECACA` | `#991B1B` |
| High | `#FEF2F2` | `#FECACA` | `#B91C1C` |
| Warning | `#FFFBEB` | `#FDE68A` | `#92400E` |
| Info | `#EFF6FF` | `#BFDBFE` | `#1E40AF` |
| Success | `#ECFDF5` | `#A7F3D0` | `#065F46` |

---

## Dark Mode (Primary)

Our default mode, optimized for monitoring dashboards.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Background** | `#0F0F10` | `rgb(15, 15, 16)` | Page background |
| **Surface** | `#1A1A1B` | `rgb(26, 26, 27)` | Cards, panels |
| **Surface Raised** | `#242426` | `rgb(36, 36, 38)` | Modals, dropdowns |
| **Surface Hover** | `#2D2D30` | `rgb(45, 45, 48)` | Interactive hover |
| **Border** | `#333336` | `rgb(51, 51, 54)` | Dividers, borders |
| **Border Subtle** | `#27272A` | `rgb(39, 39, 42)` | Subtle separators |

### Dark Mode Text

| Name | Hex | Opacity | Usage |
|------|-----|---------|-------|
| **Text Primary** | `#FFFFFF` | 100% | Headlines, important text |
| **Text Secondary** | `#A1A1AA` | - | Body text, descriptions |
| **Text Tertiary** | `#71717A` | - | Captions, hints |
| **Text Disabled** | `#52525B` | - | Disabled states |

---

## Light Mode

For users who prefer light interfaces.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Background** | `#FAFAFA` | `rgb(250, 250, 250)` | Page background |
| **Surface** | `#FFFFFF` | `rgb(255, 255, 255)` | Cards, panels |
| **Surface Raised** | `#FFFFFF` | `rgb(255, 255, 255)` | Modals, dropdowns |
| **Surface Hover** | `#F4F4F5` | `rgb(244, 244, 245)` | Interactive hover |
| **Border** | `#E4E4E7` | `rgb(228, 228, 231)` | Dividers, borders |
| **Border Subtle** | `#F4F4F5` | `rgb(244, 244, 245)` | Subtle separators |

### Light Mode Text

| Name | Hex | Usage |
|------|-----|-------|
| **Text Primary** | `#111827` | Headlines, important text |
| **Text Secondary** | `#4B5563` | Body text, descriptions |
| **Text Tertiary** | `#9CA3AF` | Captions, hints |
| **Text Disabled** | `#D1D5DB` | Disabled states |

---

## Chart Colors

For data visualizations. Colors are selected for distinguishability.

### Primary Palette (6 colors)

| # | Hex | Name | RGB |
|---|-----|------|-----|
| 1 | `#3B82F6` | Blue | `rgb(59, 130, 246)` |
| 2 | `#10B981` | Green | `rgb(16, 185, 129)` |
| 3 | `#F59E0B` | Amber | `rgb(245, 158, 11)` |
| 4 | `#EF4444` | Red | `rgb(239, 68, 68)` |
| 5 | `#8B5CF6` | Purple | `rgb(139, 92, 246)` |
| 6 | `#EC4899` | Pink | `rgb(236, 72, 153)` |

### Extended Palette (12 colors)

| # | Hex | Name |
|---|-----|------|
| 7 | `#06B6D4` | Cyan |
| 8 | `#84CC16` | Lime |
| 9 | `#F97316` | Orange |
| 10 | `#6366F1` | Indigo |
| 11 | `#14B8A6` | Teal |
| 12 | `#A855F7` | Violet |

---

## Domain Colors

Each monitoring domain has an associated color for quick identification.

| Domain | Hex | Icon | Usage |
|--------|-----|------|-------|
| **Cost** | `#10B981` | 💰 | Cost analytics, billing |
| **Reliability** | `#F59E0B` | ⚙️ | Job health, uptime |
| **Performance** | `#3B82F6` | ⚡ | Query speed, latency |
| **Security** | `#EF4444` | 🔒 | Access, audit, compliance |
| **Quality** | `#8B5CF6` | ✅ | Data quality, freshness |

---

## Special States

| State | Background | Border | Icon |
|-------|------------|--------|------|
| **Selected** | `#1D4ED8` | `#3B82F6` | `#FFFFFF` |
| **Focused** | transparent | `#3B82F6` (2px) | - |
| **Disabled** | `#27272A` | `#333336` | `#52525B` |
| **Error** | `#FEF2F2` | `#EF4444` | `#DC2626` |

---

## Figma Color Styles Structure

Create these style groups in Figma:

```
📁 Primary
   ├── Brand
   └── Brand Hover

📁 AI
   ├── Primary
   ├── Light
   └── Dark

📁 Severity
   ├── Critical
   ├── High
   ├── Warning
   ├── Info
   └── Success

📁 Background
   ├── Dark/Default
   ├── Dark/Surface
   ├── Dark/Raised
   └── Dark/Hover

📁 Text
   ├── Dark/Primary
   ├── Dark/Secondary
   ├── Dark/Tertiary
   └── Dark/Disabled

📁 Chart
   ├── 1-Blue
   ├── 2-Green
   ├── 3-Amber
   ├── ...
```

---

## Design Tokens JSON

For automated import via Tokens Studio plugin:

```json
{
  "color": {
    "primary": {
      "brand": { "value": "#FF3621" },
      "brandHover": { "value": "#FF6B35" }
    },
    "ai": {
      "primary": { "value": "#3B82F6" },
      "light": { "value": "#DBEAFE" },
      "dark": { "value": "#1D4ED8" }
    },
    "severity": {
      "critical": { "value": "#DC2626" },
      "high": { "value": "#EF4444" },
      "warning": { "value": "#F59E0B" },
      "info": { "value": "#3B82F6" },
      "success": { "value": "#10B981" }
    },
    "background": {
      "dark": { "value": "#0F0F10" },
      "surface": { "value": "#1A1A1B" },
      "raised": { "value": "#242426" },
      "hover": { "value": "#2D2D30" }
    },
    "text": {
      "primary": { "value": "#FFFFFF" },
      "secondary": { "value": "#A1A1AA" },
      "tertiary": { "value": "#71717A" },
      "disabled": { "value": "#52525B" }
    },
    "border": {
      "default": { "value": "#333336" },
      "subtle": { "value": "#27272A" }
    }
  }
}
```

---

**Next:** [typography.md](typography.md) | **Back:** [README.md](README.md)








