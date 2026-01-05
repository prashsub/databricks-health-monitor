# 09 - Composed AI Components

## Overview

Create AI interaction components: ChatBubble, ChatInput, ToolPanel, InsightCard, and ActionCard. These power the AI-first experience of the Health Monitor.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create AI interaction components for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- AI Identity: "Health Monitor AI" - unified assistant with memory
- Style: Enterprise conversational UI, data-aware
- Platform: Desktop web, right-side panel layout

Objective (this run only):
- Create 5 AI components
- Use ONLY primitives from previous prompts
- Place in Components/Composed/AI section

Follow Guidelines.md for design system alignment.

Design system rules:
- REUSE existing primitives (Card, Badge, Button, Avatar)
- Use brand/ai-accent (#FFA500) sparingly for AI elements
- Clear visual distinction between user/AI messages
- Support long-form responses and tool outputs

---

## COMPONENT 1: ChatBubble

Purpose: Single message in the chat conversation

### Specifications:
- Max width: 480px (user), 600px (AI)
- Min width: 200px
- Padding: spacing/4 (16px)

### Variants:

**role** (property):
- user: Right-aligned, background/brand-subtle (#EBF8FF), border-radius: 16px 16px 0 16px
- assistant: Left-aligned, background/elevated (#F5F5F5), border-radius: 16px 16px 16px 0

**hasAvatar** (boolean):
- true: Show avatar (User avatar or AI avatar with orange accent)
- false: No avatar (for consecutive messages)

**hasTimestamp** (boolean):
- true: Show timestamp below bubble
- false: No timestamp

### Structure:
```
ChatBubble (Auto Layout, horizontal)
├── [Avatar] (optional, 32px circle)
│   └── For AI: use brand/ai-accent border ring
└── BubbleContent (Auto Layout, vertical, flex-grow)
    ├── Message (body/default, text/primary)
    ├── [ToolReference] (optional, inline code badge)
    └── [Timestamp] (caption/small, text/muted)
```

### User Message Example:
```
                           ┌────────────────────────────────────────┐
                           │ What caused the cost spike yesterday?  │
                           │                                10:42 AM│
                           └────────────────────────────────────────┘
```

### AI Message Example:
```
┌─○──────────────────────────────────────────────────────────────┐
│ ⚡ I analyzed your cost data from yesterday and found 3 main   │
│    drivers for the spike...                                     │
│                                                                  │
│    1. Production cluster scale-up (+$2.4K)                      │
│    2. Unoptimized SQL queries (+$1.8K)                          │
│    3. Development workspace activity (+$0.9K)                   │
│                                                                  │
│    [📊 View Analysis]  [🔧 Open Recommendations]               │
│                                                          10:43 AM│
└────────────────────────────────────────────────────────────────┘
```

---

## COMPONENT 2: ChatInput

Purpose: User input for conversing with AI

### Specifications:
- Height: 52-120px (expands with content)
- Full width within container
- Background: background/default (white)
- Border: 1px border/default, focus: brand/primary

### Variants:

**state** (property):
- default: ready for input
- focused: brand/primary border, subtle shadow
- loading: show spinner, disable input
- disabled: 50% opacity

**hasContext** (boolean):
- true: Show context chip above input (e.g., "Analyzing: workspace-prod")
- false: No context

### Structure:
```
ChatInput (Auto Layout, vertical)
├── [ContextRow] (optional, Auto Layout, horizontal)
│   └── ContextChip (Chip primitive, removable)
├── InputRow (Auto Layout, horizontal)
│   ├── TextArea (multi-line, body/default, flex-grow)
│   │   └── Placeholder: "Ask about costs, performance, jobs..."
│   └── ActionButtons (Auto Layout, horizontal)
│       ├── AttachButton (icon button, 📎)
│       └── SendButton (primary button, → icon)
└── SuggestionRow (Auto Layout, horizontal, wrap)
    ├── SuggestionChip ("What caused the cost spike?")
    ├── SuggestionChip ("Show failed jobs")
    └── SuggestionChip ("Optimize my queries")
```

### Specifications:
- Input padding: spacing/3 (12px)
- Container padding: spacing/4 (16px)
- Border radius: radius/lg (12px)
- Suggestion chips: Chip primitive, ghost variant

### Example Layout:
```
┌──────────────────────────────────────────────────────────────┐
│ 🔖 Analyzing: workspace-prod-001                        ✕    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Ask about costs, performance, jobs...                 📎  → │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ○ What caused the cost spike? ○ Show failed jobs ○ Optimize │
└──────────────────────────────────────────────────────────────┘
```

---

## COMPONENT 3: ToolPanel

Purpose: Show AI tool execution and results

### Specifications:
- Base: Card (elevated variant)
- Full width within chat area
- Collapsible

### Variants:

**toolType** (property):
- query: SQL/data query (blue accent)
- analysis: Data analysis (purple accent)
- action: Execute action (orange accent)
- search: Search operation (teal accent)

**state** (property):
- running: Show spinner, animated border
- success: Green checkmark, collapsed by default
- error: Red exclamation, expanded with error
- expanded: Show full output
- collapsed: Show summary only

### Structure:
```
ToolPanel (Card primitive as base)
├── ToolHeader (Auto Layout, horizontal, clickable to expand)
│   ├── ToolIcon (colored by toolType, 20px)
│   ├── ToolName (body/emphasis, e.g., "Query: Cost by Workspace")
│   ├── StatusBadge (running/success/error)
│   └── ExpandChevron (▼ or ▶)
└── [ToolContent] (collapsible)
    ├── [QueryCode] (code block, JetBrains Mono, dark background)
    ├── [ResultPreview] (truncated output, body/small)
    └── [ActionRow] (Auto Layout, horizontal)
        ├── CopyButton (secondary button, sm)
        └── ViewFullButton (link button)
```

### Tool Type Colors:
- query: brand/primary (#077A9D)
- analysis: #7C3AED (purple)
- action: brand/ai-accent (#FFA500)
- search: #059669 (teal)

### Example - Running:
```
┌────────────────────────────────────────────────────────────────┐
│ 🔍 Query: Cost by Workspace               ◌ Running...    ▼   │
├────────────────────────────────────────────────────────────────┤
│ SELECT workspace, SUM(cost)                                    │
│ FROM gold.fact_usage                                           │
│ WHERE usage_date > '2024-01-01'                               │
│ GROUP BY workspace                                             │
│                                                                │
│ ⏳ Executing query...                                         │
└────────────────────────────────────────────────────────────────┘
```

### Example - Success (Collapsed):
```
┌────────────────────────────────────────────────────────────────┐
│ 🔍 Query: Cost by Workspace               ✓ Complete     ▶   │
│    Retrieved 24 rows • 120ms                                   │
└────────────────────────────────────────────────────────────────┘
```

---

## COMPONENT 4: InsightCard

Purpose: AI-generated proactive insight

### Specifications:
- Base: Card (default variant)
- Left border: 3px brand/ai-accent (#FFA500)
- Max width: 100%

### Variants:

**priority** (property):
- high: brand/ai-accent left border, prominent
- medium: brand/primary left border
- low: border/default left border

**hasTrend** (boolean):
- true: Show mini trend chart
- false: No chart

**hasActions** (boolean):
- true: Show action buttons
- false: No actions

### Structure:
```
InsightCard (Card primitive as base)
├── InsightHeader (Auto Layout, horizontal)
│   ├── AIIcon (✨ sparkle, brand/ai-accent)
│   ├── InsightTitle (body/emphasis, text/primary)
│   └── TimestampBadge (caption/small, "2 hours ago")
├── InsightBody (Auto Layout, horizontal)
│   ├── InsightText (body/default, flex-grow)
│   └── [TrendChart] (optional, 80px × 50px)
├── InsightMeta (Auto Layout, horizontal)
│   ├── ImpactBadge (e.g., "Potential savings: $1.2K/day")
│   ├── ConfidenceBadge (e.g., "High confidence")
│   └── SourceBadge (e.g., "Based on 7 days of data")
└── [ActionRow] (optional, Auto Layout, horizontal)
    ├── PrimaryAction (Button, primary, "Apply fix")
    └── SecondaryAction (Button, secondary, "Learn more")
```

### Example:
```
┌──────────────────────────────────────────────────────────────────┐
│ ✨ Cost Optimization Opportunity                    2 hours ago │
├──────────────────────────────────────────────────────────────────┤
│ I noticed your dev-analytics cluster has been          ▁▂▃▄▅▆▇ │
│ running idle 68% of the time this week.                         │
│ Enabling auto-termination could save ~$1.2K/day.                │
│                                                                  │
│ 💰 Savings: $1.2K/day • High confidence • Based on 7 days      │
│                                                                  │
│ [Apply Auto-termination]   [Dismiss]   [Learn more]             │
└──────────────────────────────────────────────────────────────────┘
```

---

## COMPONENT 5: ActionCard

Purpose: Recommended action from AI with execution capability

### Specifications:
- Base: Card (default variant)
- Similar to InsightCard but action-focused

### Variants:

**actionType** (property):
- config: Configuration change (gear icon)
- notification: Create alert (bell icon)
- runbook: Execute playbook (play icon)
- ticket: Create ticket (ticket icon)

**risk** (property):
- safe: Green badge "Safe", auto-execute available
- review: Yellow badge "Review", needs confirmation
- high: Red badge "High Risk", manual only

**state** (property):
- pending: Ready to execute
- executing: Show progress
- completed: Show success
- failed: Show error

### Structure:
```
ActionCard (Card primitive as base)
├── ActionHeader (Auto Layout, horizontal)
│   ├── ActionIcon (colored by actionType)
│   ├── ActionTitle (body/emphasis)
│   └── RiskBadge (Badge, colored by risk)
├── ActionDescription (body/default, text/secondary)
├── ActionMeta (Auto Layout, vertical)
│   ├── ImpactRow ("Expected impact: Reduce cost by $500/day")
│   ├── TargetRow ("Target: cluster-prod-001")
│   └── ConfidenceRow ("Confidence: 94%")
└── ActionButtons (Auto Layout, horizontal)
    ├── ExecuteButton (Button, primary/destructive based on risk)
    ├── PreviewButton (Button, secondary, "Preview changes")
    └── DismissButton (Button, ghost, "Dismiss")
```

### Example - Config Action:
```
┌──────────────────────────────────────────────────────────────────┐
│ ⚙️ Enable Auto-termination                           Safe ✓    │
├──────────────────────────────────────────────────────────────────┤
│ Configure cluster to terminate after 30 minutes of inactivity.  │
│                                                                  │
│ Expected impact: Reduce cost by $500/day                        │
│ Target: cluster-dev-analytics-001                               │
│ Confidence: 94%                                                  │
│                                                                  │
│ [🔧 Apply Configuration]   [Preview]   [Dismiss]                │
└──────────────────────────────────────────────────────────────────┘
```

### Example - High Risk:
```
┌──────────────────────────────────────────────────────────────────┐
│ ⏸️ Terminate Idle Cluster                         High Risk ⚠️  │
├──────────────────────────────────────────────────────────────────┤
│ This cluster has been idle for 4 hours but may have             │
│ scheduled jobs. Termination requires manual confirmation.       │
│                                                                  │
│ Potential savings: $2.1K/day                                    │
│ Target: cluster-prod-batch-001                                  │
│ Dependencies: 3 scheduled jobs                                   │
│                                                                  │
│ [⚠️ Terminate (Manual)]   [View Dependencies]   [Skip]         │
└──────────────────────────────────────────────────────────────────┘
```

---

## FIGMA ORGANIZATION:

Create in: 🧱 Components > Composed > AI

Page layout:
```
┌─────────────────────────────────────────────────────────────────┐
│ AI Components                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ChatBubble (user vs assistant)                                  │
│                          ┌────────────────────────────────────┐ │
│                          │ What caused the cost spike?        │ │
│                          └────────────────────────────────────┘ │
│ ┌─○──────────────────────────────────────────────────────────┐  │
│ │ ⚡ I analyzed your cost data and found 3 main drivers...   │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ ChatInput (states)                                               │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Ask about costs, performance, jobs...               📎  →  │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ ○ What caused... ○ Show failed... ○ Optimize...           │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ ToolPanel (collapsed vs expanded)                                │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ 🔍 Query: Cost by Workspace           ✓ Complete     ▶   │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ InsightCard                                                      │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ ✨ Cost Optimization Opportunity              2 hours ago   ││
│ │ I noticed your dev-analytics cluster...                     ││
│ │ [Apply Auto-termination]   [Dismiss]                        ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ActionCard (safe vs high-risk)                                   │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ ⚙️ Enable Auto-termination                         Safe ✓  ││
│ │ Expected impact: Reduce cost by $500/day                    ││
│ │ [🔧 Apply Configuration]   [Preview]                        ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PRIMITIVES USED:

- Card (base for panels, insights, actions)
- Badge (for status, risk, confidence)
- Button (actions, execution)
- Avatar (user/AI avatars)
- Chip (context, suggestions)
- Spinner (loading states)

---

## AI DESIGN PRINCIPLES:

1. **Clear attribution** - Always clear if message is from user or AI
2. **Transparency** - Show what tools AI is using and why
3. **Progressive disclosure** - Tool outputs collapsed by default
4. **Action safety** - Color-code risk levels clearly
5. **AI accent** - Use brand/ai-accent (#FFA500) sparingly to highlight AI elements

---

Do NOT:
- Create new primitives
- Add complex animations
- Use hardcoded colors
- Create screens
- Implement actual AI logic
```

---

## 🎯 Expected Output

### Components Created (5)

| Component | Purpose | Built From |
|-----------|---------|------------|
| ChatBubble | Chat message (user/AI) | Card, Avatar |
| ChatInput | User input with suggestions | Input, Chip, Button |
| ToolPanel | AI tool execution display | Card, Badge, Spinner |
| InsightCard | Proactive AI insight | Card, Badge, Button |
| ActionCard | Recommended action | Card, Badge, Button |

### Figma Structure

```
🧱 Components
└── Composed
    └── AI
        ├── ChatBubble (role: user/assistant)
        ├── ChatInput (state: default/focused/loading)
        ├── ToolPanel (toolType, state)
        ├── InsightCard (priority, hasActions)
        └── ActionCard (actionType, risk, state)
```

---

## ✅ Verification Checklist

- [ ] All 5 AI components created
- [ ] ChatBubble has user/assistant variants
- [ ] ToolPanel has 4 tool type variants
- [ ] ActionCard has risk level variants
- [ ] AI accent color (#FFA500) used consistently
- [ ] Components use existing primitives
- [ ] Auto Layout applied to all
- [ ] Collapsed/expanded states work

---

**Next:** [10-composed-charts.md](10-composed-charts.md)

