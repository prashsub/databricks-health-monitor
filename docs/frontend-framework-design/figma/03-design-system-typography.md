# Typography - Design System

## Overview

Typography system for Databricks Health Monitor. Optimized for data-dense monitoring interfaces with excellent readability.

---

## 🎨 How to Use in Figma

### Option 1: Create Text Styles (Recommended)

1. **Open Figma** → Your design file
2. **Create a text layer** with sample text
3. **Set the font properties** as specified below
4. **Click the four dots** next to "Text" in right panel
5. **Click "+"** to create a new text style
6. **Name it** exactly as shown (e.g., `Display/Large`)

### Option 2: Use Figma AI Prompt

Copy this prompt to create all text styles:

```
Create text styles for an enterprise monitoring dashboard:

Display/Large: Inter, 32px, Semibold (600), -0.5px letter spacing
Heading/H1: Inter, 24px, Semibold (600), -0.25px letter spacing  
Heading/H2: Inter, 20px, Semibold (600), 0px letter spacing
Heading/H3: Inter, 16px, Semibold (600), 0px letter spacing
Body/Large: Inter, 16px, Regular (400), 0px letter spacing
Body/Default: Inter, 14px, Regular (400), 0px letter spacing
Body/Small: Inter, 12px, Regular (400), 0px letter spacing
Label/Default: Inter, 12px, Medium (500), 0.5px letter spacing, uppercase
Code/Default: JetBrains Mono, 13px, Regular (400), 0px letter spacing
```

### Option 3: Install Fonts First

**Required fonts (free):**
- [Inter](https://fonts.google.com/specimen/Inter) - UI text
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) - Code/monospace

---

## Font Families

| Purpose | Font | Fallback | Notes |
|---------|------|----------|-------|
| **UI** | Inter | system-ui, sans-serif | All interface text |
| **Code** | JetBrains Mono | monospace | SQL, JSON, technical values |
| **Numbers** | Inter (tabular) | - | Use tabular figures for tables |

---

## Type Scale

### Display

For page titles and hero sections.

| Style | Size | Weight | Line Height | Letter Spacing |
|-------|------|--------|-------------|----------------|
| **Display Large** | 32px | Semibold (600) | 40px (1.25) | -0.5px |
| **Display Medium** | 28px | Semibold (600) | 36px (1.29) | -0.25px |

### Headings

For section headers and card titles.

| Style | Size | Weight | Line Height | Letter Spacing |
|-------|------|--------|-------------|----------------|
| **H1** | 24px | Semibold (600) | 32px (1.33) | -0.25px |
| **H2** | 20px | Semibold (600) | 28px (1.4) | 0px |
| **H3** | 16px | Semibold (600) | 24px (1.5) | 0px |
| **H4** | 14px | Semibold (600) | 20px (1.43) | 0px |

### Body

For paragraphs and descriptions.

| Style | Size | Weight | Line Height | Letter Spacing |
|-------|------|--------|-------------|----------------|
| **Body Large** | 16px | Regular (400) | 24px (1.5) | 0px |
| **Body Default** | 14px | Regular (400) | 20px (1.43) | 0px |
| **Body Small** | 12px | Regular (400) | 16px (1.33) | 0px |

### Labels & Captions

For form labels, badges, and metadata.

| Style | Size | Weight | Line Height | Letter Spacing | Case |
|-------|------|--------|-------------|----------------|------|
| **Label Large** | 14px | Medium (500) | 20px | 0.25px | Normal |
| **Label Default** | 12px | Medium (500) | 16px | 0.5px | UPPERCASE |
| **Label Small** | 10px | Medium (500) | 14px | 0.5px | UPPERCASE |
| **Caption** | 11px | Regular (400) | 14px | 0px | Normal |

### Code

For technical content, SQL, values.

| Style | Size | Weight | Line Height | Letter Spacing |
|-------|------|--------|-------------|----------------|
| **Code Large** | 14px | Regular (400) | 20px | 0px |
| **Code Default** | 13px | Regular (400) | 18px | 0px |
| **Code Small** | 12px | Regular (400) | 16px | 0px |

---

## Usage Guidelines

### When to Use Each Style

| Context | Style | Example |
|---------|-------|---------|
| Page title | Display Large | "Executive Overview" |
| Section header | H1 | "Cost by Workspace" |
| Card title | H2 | "Daily Cost Trend" |
| Subsection | H3 | "Top 5 Spenders" |
| Table header | Label Default | "WORKSPACE" |
| Table cell | Body Default | "$12,450.00" |
| Help text | Caption | "Updated 5 minutes ago" |
| KPI value | Display Large | "$42,856" |
| KPI label | Label Default | "TOTAL COST" |
| SQL query | Code Default | `SELECT * FROM...` |
| Badge text | Label Small | "CRITICAL" |

### KPI Cards

```
┌──────────────────────────────┐
│ TOTAL COST (Label Default)   │
│ $42,856 (Display Large)      │
│ ↑ 12.3% vs last week (Body)  │
└──────────────────────────────┘
```

### Table Headers

```
┌──────────────┬───────────┬──────────┐
│ WORKSPACE    │ COST      │ TREND    │  ← Label Default (uppercase)
├──────────────┼───────────┼──────────┤
│ ml-workspace │ $12,450   │ ↑ 8.2%   │  ← Body Default
│ analytics    │ $8,920    │ ↓ 2.1%   │
└──────────────┴───────────┴──────────┘
```

---

## Figma Text Styles Structure

Create these style groups in Figma:

```
📁 Display
   ├── Large (32/600)
   └── Medium (28/600)

📁 Heading
   ├── H1 (24/600)
   ├── H2 (20/600)
   ├── H3 (16/600)
   └── H4 (14/600)

📁 Body
   ├── Large (16/400)
   ├── Default (14/400)
   └── Small (12/400)

📁 Label
   ├── Large (14/500)
   ├── Default (12/500/UPPER)
   └── Small (10/500/UPPER)

📁 Code
   ├── Large (14/400/Mono)
   ├── Default (13/400/Mono)
   └── Small (12/400/Mono)

📁 Caption
   └── Default (11/400)
```

---

## Responsive Adjustments

For different viewport sizes (if needed):

| Style | Desktop (1440px) | Tablet (768px) | Mobile (375px) |
|-------|------------------|----------------|----------------|
| Display Large | 32px | 28px | 24px |
| H1 | 24px | 22px | 20px |
| H2 | 20px | 18px | 16px |
| Body Default | 14px | 14px | 14px |

*Note: Mobile is not a priority for this app, but tokens are provided for completeness.*

---

## Accessibility

### Minimum Sizes

| Context | Minimum Size | Notes |
|---------|--------------|-------|
| Body text | 14px | Never smaller for readability |
| Labels | 10px | Only for badges/tags |
| Interactive | 14px | Buttons, links |

### Contrast Requirements

| Text Color | Background | Contrast Ratio | WCAG |
|------------|------------|----------------|------|
| `#FFFFFF` | `#0F0F10` | 19.4:1 | AAA ✅ |
| `#A1A1AA` | `#0F0F10` | 7.2:1 | AAA ✅ |
| `#71717A` | `#0F0F10` | 4.6:1 | AA ✅ |

---

## Design Tokens JSON

For automated import:

```json
{
  "typography": {
    "fontFamily": {
      "ui": { "value": "Inter" },
      "code": { "value": "JetBrains Mono" }
    },
    "display": {
      "large": {
        "fontSize": { "value": "32px" },
        "fontWeight": { "value": "600" },
        "lineHeight": { "value": "40px" },
        "letterSpacing": { "value": "-0.5px" }
      }
    },
    "heading": {
      "h1": {
        "fontSize": { "value": "24px" },
        "fontWeight": { "value": "600" },
        "lineHeight": { "value": "32px" },
        "letterSpacing": { "value": "-0.25px" }
      },
      "h2": {
        "fontSize": { "value": "20px" },
        "fontWeight": { "value": "600" },
        "lineHeight": { "value": "28px" }
      },
      "h3": {
        "fontSize": { "value": "16px" },
        "fontWeight": { "value": "600" },
        "lineHeight": { "value": "24px" }
      }
    },
    "body": {
      "large": {
        "fontSize": { "value": "16px" },
        "fontWeight": { "value": "400" },
        "lineHeight": { "value": "24px" }
      },
      "default": {
        "fontSize": { "value": "14px" },
        "fontWeight": { "value": "400" },
        "lineHeight": { "value": "20px" }
      },
      "small": {
        "fontSize": { "value": "12px" },
        "fontWeight": { "value": "400" },
        "lineHeight": { "value": "16px" }
      }
    },
    "label": {
      "default": {
        "fontSize": { "value": "12px" },
        "fontWeight": { "value": "500" },
        "lineHeight": { "value": "16px" },
        "letterSpacing": { "value": "0.5px" },
        "textTransform": { "value": "uppercase" }
      }
    },
    "code": {
      "default": {
        "fontFamily": { "value": "JetBrains Mono" },
        "fontSize": { "value": "13px" },
        "fontWeight": { "value": "400" },
        "lineHeight": { "value": "18px" }
      }
    }
  }
}
```

---

**Next:** [04-design-system-spacing.md](04-design-system-spacing.md) | **Prev:** [02-design-system-colors.md](02-design-system-colors.md)

