# 15 - Screen: Chat Interface (Super Enhanced)

## Overview

Create a world-class AI chat interface that rivals GitHub Copilot Chat, Notion AI, and enterprise chatbots. This is the unified AI assistant ("Health Monitor AI") that handles all platform questions, analysis, and actions.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create a world-class Chat Interface for an enterprise monitoring AI assistant.

Context:
- Product: Databricks Health Monitor (platform observability)
- Screen: Unified AI assistant chat interface
- Users: Platform engineers asking questions and taking actions
- Mental model: "Ask anything about my platform, get expert answers and actions"
- Inspiration: GitHub Copilot Chat, Notion AI, ChatGPT
- Platform: Desktop web (1440px primary width)

Quality bar:
- GitHub Copilot-level contextual intelligence
- ChatGPT-level conversational fluency
- Enterprise-grade action capabilities
- Professional AI assistant experience

Objective (this run only):
- Create 1 complete screen using ONLY existing components
- Showcase AI with memory, tools, and actions
- NO new components
- Place in Screens section

Follow Guidelines.md for design system alignment.

---

SCREEN SPECIFICATIONS:

Canvas Size: 1440px x 900px (viewport)
Background: #FAFAFA

Layout: Three-panel design
- Left: Chat History (280px)
- Center: Main Chat (680px)
- Right: Context Panel (320px)

---

LEFT PANEL: CHAT HISTORY (280px)

Header: "Chat History" with [+ New] button
Search: "Search conversations..."

Today Section:
- Active conversation (blue dot): "Why is prod-sql-wh expensive?" 11:15 AM, 8 messages
- "Job failure root cause" 9:30 AM, 12 messages

Yesterday Section:
- "Cost forecast next month" 4:15 PM
- "Security audit findings" 2:00 PM

Saved Queries Section:
- "Daily cost summary"
- "Job health check"
- "Security posture"

Quick Actions:
[Cost Summary] [Job Status] [Security Check] [Generate Report]

---

MAIN CHAT AREA (680px)

AI Greeting (New State):
- AI avatar with sparkle icon
- "Hi! I'm your Databricks platform assistant."
- Capabilities list: Memory, Tools, Charts
- 6 suggested question buttons in 2x3 grid

Active Conversation Example:

User Message:
"Why is my cost so high today? I expected around $7K but we're at $12K already."

AI Response with Tool Calls:
Tool Panel showing:
- get_daily_cost_summary (0.8s)
- get_cost_anomalies (1.2s)
- get_top_cost_drivers (0.6s)

Response Content:
- Markdown-formatted analysis
- Inline cost comparison chart
- Table of expensive queries
- Recommendation buttons: [Kill Query] [Email User] [Create Alert]

Input Area (sticky bottom):
- Attachment icon
- Large text input: "Ask me anything..."
- Voice and send buttons
- Suggested follow-ups
- Tools available indicator
- Memory status

---

RIGHT PANEL: CONTEXT (320px)

Active Context:
- Current focus: Cost Analysis, prod-sql-warehouse
- Related alert reference

Referenced Data:
- Cost by SKU breakdown
- Anomalies detected list

Tool Results:
- JSON output panels (collapsible)
- Action confirmations

Memory Panel:
- Session memory (4 items)
- Long-term memory (8 items)
- Edit/view controls

Related Signals:
- 3 related alerts with severity

---

STATES TO CREATE:

1. New Conversation - AI greeting
2. Active Conversation - Full chat
3. AI Thinking - Processing spinner
4. Tool Execution - Action confirmation
5. Error State - Graceful handling

---

COMPONENTS TO USE:
- Sidebar (navigation)
- TopBar
- ChatBubble (user and AI variants)
- ToolPanel
- SuggestedQuestion buttons
- Card, Button, Badge

Do NOT create new components.
Focus on professional AI assistant experience.
```

---

## 🎯 Expected Output

### Screen Created (1)
- Chat Interface - AI Assistant Edition (1440px x 900px)

### Figma Structure

```
Screens
└── Chat
    └── Chat Interface
        ├── New Conversation (greeting)
        ├── Active Conversation
        ├── AI Thinking
        ├── Tool Execution
        └── Error State
```

---

## ✅ Verification Checklist

- [ ] Three-panel layout (history, chat, context)
- [ ] AI greeting with 6 suggested questions
- [ ] Chat history sidebar with search
- [ ] Saved queries and quick actions
- [ ] Tool call visualization
- [ ] Inline charts and tables
- [ ] Action buttons in responses
- [ ] Suggested follow-ups
- [ ] Context panel with active focus
- [ ] Tool results display
- [ ] Memory panel (session + long-term)
- [ ] Related signals
- [ ] Processing/thinking state
- [ ] Error state with alternatives
- [ ] Professional conversational AI quality

---

**Next:** [16-screen-alert-center.md](16-screen-alert-center.md)

