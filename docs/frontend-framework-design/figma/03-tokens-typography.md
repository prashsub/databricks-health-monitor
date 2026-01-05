# 03 - Typography Tokens

## Overview

Create the complete typography system as Figma text styles. These styles define all text used in the application.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create a comprehensive typography system for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Users: Technical power users reading dense data
- Style: Clean, scannable, enterprise
- Font families: DM Sans (UI) ✅ OFFICIAL, DM Mono (code/numbers) ✅ OFFICIAL

Objective (this run only):
- Create ONLY typography text styles
- No components, no screens
- Organize into logical scale

Follow Guidelines.md for design system alignment.

OFFICIAL Databricks Type Scale Rules (CRITICAL):
- Above 20px: Sizes MUST be divisible by 8 (24, 32, 40, 48, 56, 64, 72, 80)
- Below 20px: Sizes divisible by 4 or 2 (10, 12, 14, 16, 18, 20)
- Body copy line-height: 150% (1.5) ✅
- Headline line-height: 120% (1.2) ✅

Typography Best Practices:
✅ DO: Use hierarchy (size, weight, color) for scannability
✅ DO: Give content space (16px+ between blocks)
✅ DO: Use proper line-height (150% body, 120% headlines)
❌ DON'T: Cram text elements close together
❌ DON'T: Use tight line-height (below 120%)
❌ DON'T: Use right-aligned text

Design system rules:
- Use Figma text styles (not variables for typography)
- Group styles by category (display, heading, body, etc.)
- Include font family, size, weight, line height, letter spacing
- All styles must use the defined fonts only
- ALL sizes must follow type scale rules

---

CREATE THESE TEXT STYLES:

## Group: Display
(Large, impactful text for hero numbers and page titles)

- display/xl
  Font: DM Sans ✅
  Size: 80px
  Weight: 700 (Bold)
  Line Height: 96px (1.2) ✅
  Letter Spacing: -0.02em
  Usage: Billboards, very large hero sections

- display/large
  Font: DM Sans ✅
  Size: 48px
  Weight: 700 (Bold)
  Line Height: 56px (1.17)
  Letter Spacing: -0.02em
  Usage: Very large KPI numbers, dashboard titles

- display/medium
  Font: DM Sans ✅
  Size: 32px
  Weight: 600 (Semibold)
  Line Height: 40px (1.25)
  Letter Spacing: -0.01em
  Usage: Page titles, large section headers

## Group: Heading
(Section and card titles)

- heading/h1
  Font: DM Sans
  Size: 24px
  Weight: 600 (Semibold)
  Line Height: 32px (1.33)
  Letter Spacing: -0.01em
  Usage: Major section titles, modal headers

- heading/h2
  Font: DM Sans
  Size: 18px
  Weight: 600 (Semibold)
  Line Height: 24px (1.33)
  Usage: Card titles, subsection headers

- heading/h3
  Font: DM Sans
  Size: 16px
  Weight: 600 (Semibold)
  Line Height: 22px (1.375)
  Usage: Small section titles, sidebar sections

- heading/h4
  Font: DM Sans
  Size: 14px
  Weight: 600 (Semibold)
  Line Height: 20px (1.43)
  Usage: Table headers, form section labels

## Group: Body
(Primary reading text)

- body/large
  Font: DM Sans
  Size: 16px
  Weight: 400 (Regular)
  Line Height: 24px (1.5)
  Usage: Descriptions, longer text content

- body/default
  Font: DM Sans
  Size: 14px
  Weight: 400 (Regular)
  Line Height: 20px (1.43)
  Usage: Default body text, table cells

- body/small
  Font: DM Sans
  Size: 12px
  Weight: 400 (Regular)
  Line Height: 18px (1.5)
  Usage: Secondary text, metadata, timestamps

- body/small-emphasis
  Font: DM Sans
  Size: 13px
  Weight: 500 (Medium)
  Line Height: 20px (1.54)
  Letter Spacing: 0
  Usage: Action links, metric text in cards (NEW for professional design)

- body/emphasis
  Font: DM Sans
  Size: 14px
  Weight: 500 (Medium)
  Line Height: 20px (1.43)
  Usage: Emphasized body text, important values

## Group: Label
(UI labels and controls)

- label/large
  Font: DM Sans
  Size: 14px
  Weight: 500 (Medium)
  Line Height: 20px (1.43)
  Letter Spacing: 0.01em
  Usage: Button text, form labels

- label/default
  Font: DM Sans
  Size: 12px
  Weight: 500 (Medium)
  Line Height: 16px (1.33)
  Letter Spacing: 0.01em
  Usage: Small buttons, badge text, chip text

- label/badge
  Font: DM Sans
  Size: 11px
  Weight: 500 (Medium)
  Line Height: 16px (1.45)
  Letter Spacing: 0
  Usage: Status badge text, professional chip labels (NEW for professional design)

- label/small
  Font: DM Sans
  Size: 10px
  Weight: 500 (Medium)
  Line Height: 14px (1.4)
  Letter Spacing: 0.02em
  Text Transform: UPPERCASE
  Usage: Overlines, category labels

## Group: Caption
(Smallest text)

- caption/default
  Font: DM Sans
  Size: 10px
  Weight: 400 (Regular)
  Line Height: 14px (1.4)
  Usage: Fine print, chart axis labels

- caption/emphasis
  Font: DM Sans
  Size: 10px
  Weight: 500 (Medium)
  Line Height: 14px (1.4)
  Usage: Emphasized captions, legends

## Group: Code
(Monospace for code, numbers, IDs)

- code/block
  Font: DM Mono
  Size: 14px
  Weight: 400 (Regular)
  Line Height: 22px (1.57)
  Usage: SQL queries, code blocks

- code/inline
  Font: DM Mono
  Size: 13px
  Weight: 400 (Regular)
  Line Height: 20px (1.54)
  Usage: Inline code, table IDs

- code/small
  Font: DM Mono
  Size: 11px
  Weight: 400 (Regular)
  Line Height: 16px (1.45)
  Usage: Small code snippets, timestamps

## Group: Number
(Numeric display - monospace for alignment)

- number/large
  Font: DM Mono
  Size: 32px
  Weight: 600 (Semibold)
  Line Height: 40px (1.25)
  Usage: Large KPI values, cost totals

- number/medium
  Font: DM Mono
  Size: 24px
  Weight: 600 (Semibold)
  Line Height: 32px (1.33)
  Usage: Medium metric values

- number/default
  Font: DM Mono
  Size: 16px
  Weight: 500 (Medium)
  Line Height: 24px (1.5)
  Usage: Standard numeric values

- number/small
  Font: DM Mono
  Size: 12px
  Weight: 500 (Medium)
  Line Height: 18px (1.5)
  Usage: Small numbers, table values

---

ORGANIZATION:
- Add to the "🎨 Tokens" page in Figma
- Create a "Typography" section/frame below Colors
- Display each text style as a sample line showing:
  - The style name
  - A sample text in that style
  - Size/weight annotation

DISPLAY FORMAT FOR EACH STYLE:
┌──────────────────────────────────────────────────┐
│ display/large                     48px / Bold    │
│                                                  │
│ The quick brown fox               ← Sample text  │
│                                   in the style   │
└──────────────────────────────────────────────────┘

Group styles visually by category (Display, Heading, Body, etc.)

Do NOT:
- Create any components
- Create any screens
- Use fonts other than DM Sans ✅ and DM Mono ✅
- Add decorative text effects
- Violate type scale rules (divisible by 8, 4, or 2)
```

---

## 🎯 Expected Output

After running this prompt, you should have:

### Text Styles Created (23 total)

| Group | Count | Styles |
|-------|-------|--------|
| Display | 3 | xl, large, medium |
| Heading | 4 | h1, h2, h3, h4 |
| Body | 4 | large, default, small, emphasis |
| Label | 3 | large, default, small |
| Caption | 2 | default, emphasis |
| Code | 3 | block, inline, small |
| Number | 4 | large, medium, default, small |

### Visual Reference Frame

A "Typography" frame showing all text styles with samples.

---

## ✅ Verification Checklist

After running the prompt:

- [ ] All 23 text styles are created
- [ ] Styles are organized into groups (Display, Heading, Body, Label, Caption, Code, Number)
- [ ] Type scale follows rules: divisible by 8 (above 20px), divisible by 4 or 2 (below 20px)
- [ ] Line heights are 150% for body copy, 120% for headlines
- [ ] Visual sample reference is created
- [ ] DM Sans ✅ font is used for UI text
- [ ] DM Mono ✅ font is used for code/numbers
- [ ] Line heights and letter spacing are correct

---

## 🔗 Typography Usage Reference

| Use Case | Text Style |
|----------|------------|
| KPI large number | number/large |
| Card title | heading/h2 |
| Table cell text | body/default |
| Button label | label/large |
| Badge text | label/default |
| SQL query | code/block |
| Timestamp | body/small |
| Chart axis | caption/default |

---

**Next:** [04-tokens-spacing.md](04-tokens-spacing.md)

