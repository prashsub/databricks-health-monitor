# 01 - Context & Design System Setup

## Overview

Copy this prompt into your AI design tool **FIRST** before designing any screens. It establishes the product context, design philosophy, and **complete design system tokens**.

---

## 🎯 Initial Context Prompt

**Copy this entire block:**

```
I'm building DATABRICKS HEALTH MONITOR - an enterprise-grade observability platform
that rivals Datadog, Grafana, New Relic, and Sentry.

=== PRODUCT DEFINITION ===

Goal: Help platform teams DETECT, EXPLAIN, and FIX health issues across Databricks 
workspaces (cost spikes, failures, performance regressions, governance gaps, security risks).

Users: Platform engineers, Data engineering leads, FinOps, Security/Governance admins

Mental model: "What's broken?" → "Why?" → "What do I do now?" → "Did it get better?"

=== THE AI ASSISTANT ===

A SINGLE unified AI assistant that:
- Speaks as "I" (first person)
- Knows everything (cost, security, performance, reliability, quality)
- Remembers user preferences and past issues
- Proactively surfaces insights
- Executes actions on behalf of users

Users NEVER see "Cost Agent" or "Security Agent" - just the AI.

=== DESIGN DNA (Steal from the Best) ===

From DATADOG:
- Single pane of glass with all signals
- Monitor-driven workflows (dashboards → alerts → drilldown)
- Dense but readable data presentation
- Powerful filtering and search

From GRAFANA:
- Strong time controls (sticky global picker, quick ranges, compare)
- Panel interactions (hover, click to drill down)
- Dashboard variables

From NEW RELIC:
- AIOps-style signal correlation
- "What changed?" analysis
- Intelligent noise reduction
- Smarter detection and grouping

From SENTRY:
- Issue-centric triage (not just metrics)
- Context-rich detail pages
- Fast debugging workflows
- Clear severity and status

===============================================================================
                              DESIGN SYSTEM
===============================================================================

=== LAYOUT ===

Page width: 1440px (desktop-first)
Grid: 4px base unit, 12-column layout
Sidebar: 240px (collapsible to 64px)
Content max-width: 1200px
Page margins: 24px
Section gaps: 24px
Card gaps: 16px

=== COLORS ===

// Brand
Primary Brand:        #FF3621 (Databricks Red)
Primary Hover:        #FF6B35

// AI (use for ALL AI elements)
AI Primary:           #3B82F6 (Blue)
AI Light:             #DBEAFE
AI Dark:              #1D4ED8

// Severity
Critical:             #DC2626
High:                 #EF4444
Warning:              #F59E0B
Info:                 #3B82F6
Success:              #10B981

// Severity Backgrounds (for badges/cards)
Critical BG:          #FEF2F2
Warning BG:           #FFFBEB
Success BG:           #ECFDF5
Info BG:              #EFF6FF

// Dark Mode (Primary)
Background:           #0F0F10
Surface:              #1A1A1B
Surface Raised:       #242426
Surface Hover:        #2D2D30
Border:               #333336
Border Subtle:        #27272A

// Dark Mode Text
Text Primary:         #FFFFFF
Text Secondary:       #A1A1AA
Text Tertiary:        #71717A
Text Disabled:        #52525B

// Light Mode (Alternative)
Background Light:     #FAFAFA
Surface Light:        #FFFFFF
Text Primary Light:   #111827
Text Secondary Light: #4B5563

// Chart Palette (6 primary colors)
Chart 1:              #3B82F6 (Blue)
Chart 2:              #10B981 (Green)
Chart 3:              #F59E0B (Amber)
Chart 4:              #EF4444 (Red)
Chart 5:              #8B5CF6 (Purple)
Chart 6:              #EC4899 (Pink)

// Domain Colors
Cost Domain:          #10B981 (Green)
Reliability Domain:   #F59E0B (Amber)
Performance Domain:   #3B82F6 (Blue)
Security Domain:      #EF4444 (Red)
Quality Domain:       #8B5CF6 (Purple)

=== TYPOGRAPHY ===

Font Family UI:       Inter
Font Family Code:     JetBrains Mono

// Display
Display Large:        32px / Semibold (600) / -0.5px tracking / 40px line
Display Medium:       28px / Semibold (600) / -0.25px tracking / 36px line

// Headings
H1:                   24px / Semibold (600) / -0.25px tracking / 32px line
H2:                   20px / Semibold (600) / 0px tracking / 28px line
H3:                   16px / Semibold (600) / 0px tracking / 24px line
H4:                   14px / Semibold (600) / 0px tracking / 20px line

// Body
Body Large:           16px / Regular (400) / 0px tracking / 24px line
Body Default:         14px / Regular (400) / 0px tracking / 20px line
Body Small:           12px / Regular (400) / 0px tracking / 16px line

// Labels
Label Large:          14px / Medium (500) / 0.25px tracking / 20px line
Label Default:        12px / Medium (500) / 0.5px tracking / 16px line / UPPERCASE
Label Small:          10px / Medium (500) / 0.5px tracking / 14px line / UPPERCASE

// Code
Code Default:         13px / Regular (400) / JetBrains Mono / 18px line
Code Small:           12px / Regular (400) / JetBrains Mono / 16px line

=== SPACING SCALE ===

0:                    0px
1 (xs):               4px   (icon gaps, tight)
2 (sm):               8px   (item gaps, default)
3:                    12px
4 (md):               16px  (card padding, standard)
5:                    20px
6 (lg):               24px  (page margins, sections)
8 (xl):               32px  (large sections)
10:                   40px
12:                   48px
16:                   64px

=== COMPONENT SIZES ===

Header Height:        56px
Sidebar Width:        240px (collapsed: 64px)
Button Small:         32px height, 12px padding
Button Default:       40px height, 16px padding
Button Large:         48px height, 20px padding
Input Height:         40px
Table Row Height:     48px
Card Padding:         16px
Card Border Radius:   8px

=== BORDER RADIUS ===

None:                 0px
Small:                4px
Medium:               8px
Large:                12px
XL:                   16px
Full:                 9999px (pills)

=== SHADOWS ===

Shadow SM:            0 1px 2px rgba(0,0,0,0.1)
Shadow MD:            0 4px 6px rgba(0,0,0,0.15)
Shadow LG:            0 10px 15px rgba(0,0,0,0.2)

===============================================================================
                           AI STYLING (CRITICAL)
===============================================================================

All AI elements use consistent styling:
- Name: "Health Monitor AI" or "AI Assistant"
- Icon: 🤖 (or custom AI icon)
- Color: #3B82F6 (blue) - CONSISTENT EVERYWHERE
- Background for AI cards: #EFF6FF (light blue tint)
- Tone: First person ("I found...", "I recommend...")
- Memory callouts: 💭 icon with #F5F3FF background

Users NEVER see agent names like "Cost Agent" or "Security Agent".

===============================================================================
                         INTERACTION PRINCIPLES
===============================================================================

1. Time travel first-class: Sticky global picker + quick ranges + compare
2. Fast triage: Every list has search, filter chips, sort, bulk actions
3. Clear drill path: Overview → Domain → Signal list → Detail → Action
4. Explainability: Every AI insight shows "why" and "evidence"
5. Noise control: Mute/snooze, deduplication, grouping, severity clarity
6. Action orientation: Every detail page ends with "Next best actions"

===============================================================================

Ready to design enterprise-grade monitoring UI with this design system!
```

---

## ✅ What This Establishes

| Category | Details |
|----------|---------|
| **Colors** | 30+ color tokens (brand, severity, backgrounds, charts) |
| **Typography** | 15 text styles (display, heading, body, label, code) |
| **Spacing** | 12-point scale based on 4px unit |
| **Components** | Standard sizes for buttons, inputs, cards |
| **AI Styling** | Consistent blue theme for all AI elements |

---

## 🎨 Create Figma Styles After Setup

After pasting the context, create these in Figma:

### Color Styles (Priority)
```
Primary/Brand, Primary/Hover
AI/Primary, AI/Light, AI/Dark
Severity/Critical, Severity/Warning, Severity/Success, Severity/Info
Background/Dark, Surface/Dark, Surface/Raised
Text/Primary, Text/Secondary, Text/Tertiary
```

### Text Styles (Priority)
```
Display/Large, Display/Medium
Heading/H1, Heading/H2, Heading/H3
Body/Large, Body/Default, Body/Small
Label/Default (uppercase)
Code/Default
```

---

## 📚 Design System Reference

For detailed specifications with examples:
- **Colors:** [02-design-system-colors.md](02-design-system-colors.md)
- **Typography:** [03-design-system-typography.md](03-design-system-typography.md)
- **Spacing:** [04-design-system-spacing.md](04-design-system-spacing.md)

---

## ✅ After Setup

Once you've copied the context, proceed to create your design system styles:

**Next:** [02-design-system-colors.md](02-design-system-colors.md)
