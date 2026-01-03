# 09 - Chat Interface (AI Assistant)

## Overview

The unified AI assistant chat interface - the primary way users interact with the platform through natural language.

---

## 📋 Design Prompt

**Copy this prompt:**

```
Design the CHAT INTERFACE page for Databricks Health Monitor.

This is the primary AI assistant conversation interface - users can ask anything.
The AI is a UNIFIED assistant (not multiple agents).

=== LAYOUT (1440px wide) ===

┌─────────────────────────────────────────────────────────────────────────────────┐
│ [☰] Databricks Health Monitor    [🕐 Last 24h ▼] [🔔 7] [🤖 Ask AI] [Settings] │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────┐ ┌──────────────────────────────┐│
│  │ 💬 Conversations                           │ │ 🤖 AI Assistant              ││
│  │                                            │ │                              ││
│  │ [+ New Conversation]                       │ │ ┌──────────────────────────┐││
│  │                                            │ │ │ 💭 I remember:           │││
│  │ Today                                      │ │ │ • You focus on ml-ws     │││
│  │ ├─ Cost spike investigation      3:47 PM  │ │ │ • You prefer detail view │││
│  │ └─ Job failure analysis          11:20 AM │ │ │ • Alert threshold: $1K   │││
│  │                                            │ │ └──────────────────────────┘││
│  │ Yesterday                                  │ │                              ││
│  │ ├─ Weekly cost review            4:15 PM  │ │                              ││
│  │ └─ Security audit findings       9:30 AM  │ │                              ││
│  │                                            │ │                              ││
│  │ Last 7 days                                │ │                              ││
│  │ ├─ Performance optimization      Mon      │ │                              ││
│  │ └─ Security audit review         Sun      │ │                              ││
│  │                                            │ │                              ││
│  │ [View All History]                         │ │                              ││
│  └────────────────────────────────────────────┘ │                              ││
│                                                 │                              ││
│  ────────────────────────────────────────────── │                              ││
│                                                 │                              ││
│  CONVERSATION AREA (scrollable)                 │ ┌──────────────────────────┐││
│                                                 │ │ 🔥 Suggested Questions   │││
│  ┌──────────────────────────────────────────┐  │ │                          │││
│  │ 👤 You                           3:47 PM │  │ │ • Why did cost spike?    │││
│  │                                          │  │ │ • Show failed jobs       │││
│  │ "Why did cost spike 300% in ml-workspace │  │ │ • Security findings      │││
│  │  today?"                                 │  │ │ • Budget forecast        │││
│  └──────────────────────────────────────────┘  │ └──────────────────────────┘││
│                                                 │                              ││
│  ┌──────────────────────────────────────────┐  │ ┌──────────────────────────┐││
│  │ 🤖 AI Assistant                  3:47 PM │  │ │ 🛠️ Actions Available    │││
│  │                                          │  │ │                          │││
│  │ I analyzed your ml-workspace cost and    │  │ │ • Stop runaway job       │││
│  │ found the root cause:                    │  │ │ • Add timeout            │││
│  │                                          │  │ │ • Create alert           │││
│  │ ┌────────────────────────────────────┐   │  │ │ • Export report          │││
│  │ │ 📊 Cost Spike Analysis             │   │  │ └──────────────────────────┘││
│  │ │                                    │   │  │                              ││
│  │ │ Root Cause: train-llm-v3 job ran  │   │  │ ┌──────────────────────────┐││
│  │ │ 6x longer than expected           │   │  │ │ 📋 Quick Actions         │││
│  │ │                                    │   │  │ │                          │││
│  │ │ $4,890 ────────────────▲          │   │  │ │ [📊 View Dashboard]      │││
│  │ │ $1,200 ──────────────────────     │   │  │ │ [🔔 Create Alert]        │││
│  │ │        6AM  9AM  12PM  3PM  Now   │   │  │ │ [📑 Export Report]       │││
│  │ │                                    │   │  │ └──────────────────────────┘││
│  │ │ Config change at 9:45 AM triggered│   │  └──────────────────────────────┘│
│  │ │ autoscaling from 4 → 20 nodes.   │   │                                  │
│  │ └────────────────────────────────────┘   │                                  │
│  │                                          │                                  │
│  │ 💭 This is similar to the Dec 15th      │                                  │
│  │    issue - you fixed it with a timeout. │                                  │
│  │                                          │                                  │
│  │ Would you like me to:                    │                                  │
│  │ 1. Stop the runaway job now ($2K saved) │                                  │
│  │ 2. Add a 2-hour timeout for future runs │                                  │
│  │ 3. Alert the job owner (@jane.doe)      │                                  │
│  │                                          │                                  │
│  │ [Stop Job] [Add Timeout] [Alert Owner]  │                                  │
│  │ [Show More Options]                      │                                  │
│  └──────────────────────────────────────────┘                                  │
│                                                                                  │
│  ┌──────────────────────────────────────────┐                                  │
│  │ 👤 You                           3:48 PM │                                  │
│  │                                          │                                  │
│  │ "Stop the job and add a timeout"         │                                  │
│  └──────────────────────────────────────────┘                                  │
│                                                                                  │
│  ┌──────────────────────────────────────────┐                                  │
│  │ 🤖 AI Assistant                  3:48 PM │                                  │
│  │                                          │                                  │
│  │ ✅ Done! I've:                           │                                  │
│  │                                          │                                  │
│  │ 1. ✅ Stopped train-llm-v3 (saved ~$2K) │                                  │
│  │ 2. ✅ Added 2-hour timeout to job config│                                  │
│  │ 3. ✅ Notified @jane.doe via Slack      │                                  │
│  │                                          │                                  │
│  │ ┌────────────────────────────────────┐   │                                  │
│  │ │ 📋 Action Summary                  │   │                                  │
│  │ │ ├─ Job stopped at 3:48 PM         │   │                                  │
│  │ │ ├─ Timeout: 2 hours (was: none)   │   │                                  │
│  │ │ └─ Notification sent to @jane.doe │   │                                  │
│  │ └────────────────────────────────────┘   │                                  │
│  │                                          │                                  │
│  │ Would you like me to set up an alert    │                                  │
│  │ for future cost spikes in ml-workspace? │                                  │
│  │                                          │                                  │
│  │ [Yes, Create Alert] [No Thanks]          │                                  │
│  └──────────────────────────────────────────┘                                  │
│                                                                                  │
│  ════════════════════════════════════════════════════════════════════════════   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────┐│
│  │ 💬 Ask me anything...                                           [🎤] [Send] ││
│  │                                                                              ││
│  │ Examples: "Why did cost spike?" • "Show failed jobs" • "Create an alert"    ││
│  └──────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

=== COMPONENT SPECS ===

CONVERSATION SIDEBAR:
- Width: 280px (collapsible)
- Grouped by time (Today, Yesterday, etc.)
- Hover: Show delete/rename options
- Click: Load conversation

MEMORY PANEL:
- Shows what AI remembers about user
- Preferences, past issues, favorite workspaces
- Editable by user

USER MESSAGE:
- Right-aligned bubble
- Avatar: User initial or photo
- Timestamp

AI MESSAGE:
- Left-aligned
- AI icon (🤖) + "AI Assistant"
- Can include:
  - Text explanation
  - Embedded visualization (chart, table)
  - Memory callout (💭 purple background)
  - Action buttons
  - Code blocks (syntax highlighted)

EMBEDDED VISUALIZATION:
- Full width within message
- Same styling as dashboard panels
- Interactive (hover for details)

MEMORY CALLOUT:
- Purple background (#F5F3FF)
- 💭 icon
- References past interactions

ACTION BUTTONS:
- Primary actions as buttons
- Secondary as text links
- Execute inline with progress indicator

INPUT BAR:
- Sticky at bottom
- Placeholder with examples
- Voice input button
- Send button

=== INTERACTIONS ===

- Send message: Natural language query
- Action button: Execute with confirmation
- Embedded chart: Hover for details, click to expand
- Memory edit: Click to modify preferences
- New conversation: Fresh context
- Load history: Restore past conversation

=== AI STYLING (CRITICAL) ===

- Name: Always "AI Assistant" (never "Cost Agent", etc.)
- Icon: 🤖 (consistent everywhere)
- Color: #3B82F6 (blue accent)
- Tone: First person ("I found...", "I recommend...")
- Memory: 💭 with purple background (#F5F3FF)

Provide complete high-fidelity design.
```

---

## 📐 Key Measurements

| Element | Specification |
|---------|---------------|
| Sidebar width | 280px (collapsible) |
| Conversation area | Remaining width |
| Message bubble | Max 80% width |
| Input bar height | 72px (sticky) |
| Embedded chart | 100% of message width |

---

## ✅ Checklist

- [ ] Conversation sidebar with history
- [ ] Memory panel ("I remember")
- [ ] Suggested questions
- [ ] User message bubbles (right-aligned)
- [ ] AI message bubbles (left-aligned)
- [ ] Embedded visualizations in messages
- [ ] Memory callouts (💭)
- [ ] Action buttons with confirmation
- [ ] Action summary blocks
- [ ] Input bar with examples

---

## 📚 PRD Reference

For detailed specifications, see: [../prd/03-agentic-ai-first.md](../prd/03-agentic-ai-first.md) - Section 5: Conversational UI Patterns

---

**Next:** [10-alert-center.md](10-alert-center.md)

