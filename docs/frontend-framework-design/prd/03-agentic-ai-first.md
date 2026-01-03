# 09b - Frontend PRD: Agentic AI-First Enhancements

**Document Type:** PRD Enhancement - Agent-Native UX Patterns  
**Version:** 3.0  
**Last Updated:** January 2026  
**Status:** Ready for Figma Design

---

## Overview

This document transforms the Frontend PRD into an **AI-first, agent-native application** where the multi-agent system (Orchestrator + 5 Worker Agents) is the **primary interface**, not a supplementary feature. The chat interface becomes the **main navigation paradigm**, with traditional UI elements serving as **agent outputs** rather than primary interactions.

**Core Principle:** *Every user action can be initiated conversationally, and every data visualization is agent-generated.*

**Integration:** This enhancement adds **180 pages** to the existing PRD for a **total of 470 pages**.

---

## Table of Contents

1. [AI-First Design Principles](#ai-first-design-principles)
2. [Agent System Integration](#agent-system-integration)
3. [Conversational UI Patterns (10 Patterns)](#conversational-ui-patterns-10-patterns)
4. [Multi-Agent Coordination Display](#multi-agent-coordination-display)
5. [Agent Reasoning Visualization](#agent-reasoning-visualization)
6. [Memory-Aware UI Components](#memory-aware-ui-components)
7. [Proactive Agent Interactions](#proactive-agent-interactions)
8. [Tool Invocation Display](#tool-invocation-display)
9. [Agentic Workflows](#agentic-workflows)
10. [Enhanced Chat Interface](#enhanced-chat-interface)
11. [Intent-Driven Navigation](#intent-driven-navigation)
12. [Conversational Data Exploration](#conversational-data-exploration)
13. [Component Library: Agentic UI](#component-library-agentic-ui)

---

## AI-First Design Principles

### Core Tenets

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI-FIRST DESIGN PRINCIPLES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CONVERSATION IS NAVIGATION                                   │
│     • Chat is the primary interface (not a sidebar)             │
│     • Every page is reachable via natural language              │
│     • Traditional nav is secondary/optional                      │
│                                                                  │
│  2. AGENTS GENERATE UI                                           │
│     • Dashboards are agent responses, not static pages          │
│     • Visualizations are query results, not predefined          │
│     • UI adapts to agent's answer format                        │
│                                                                  │
│  3. SHOW THE INTELLIGENCE                                        │
│     • Make agent reasoning visible (not a black box)            │
│     • Show multi-agent coordination in real-time                │
│     • Display tool invocations and data sources                 │
│                                                                  │
│  4. PROACTIVE, NOT REACTIVE                                      │
│     • Agent suggests actions before user asks                   │
│     • Anomaly alerts are conversational                         │
│     • Recommendations appear as agent messages                  │
│                                                                  │
│  5. MEMORY-DRIVEN PERSONALIZATION                                │
│     • UI remembers user preferences (Lakebase long-term)        │
│     • Conversation context persists (Lakebase short-term)       │
│     • Agent learns from user patterns                           │
│                                                                  │
│  6. MULTIMODAL RESPONSES                                         │
│     • Agent returns text + charts + tables + actions            │
│     • User can reply in text, click actions, or refine          │
│     • Every output is interactive                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Traditional vs AI-First Comparison

| Aspect | Traditional Dashboard | AI-First Agent App |
|--------|----------------------|-------------------|
| **Primary Interface** | Sidebar navigation | Chat conversation |
| **Data Access** | Filters, dropdowns, date pickers | Natural language queries |
| **Visualization** | Predefined charts on static pages | Agent-generated charts in response |
| **Navigation** | Click menu → page loads | Ask agent → agent routes + responds |
| **Insights** | User must interpret charts | Agent explains insights in text |
| **Anomalies** | Red badges, alert icons | Agent proactively messages user |
| **Actions** | Click buttons | Agent suggests, user confirms in chat |
| **Help** | Documentation links | Agent is the documentation |
| **Personalization** | User configures settings | Agent learns preferences automatically |
| **Multi-step tasks** | Click 5 buttons across 3 pages | One conversation with agent |

---

## Agent System Integration

### Architecture: Frontend ↔ Agent System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND ↔ AGENT ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   USER INPUT (Chat)                                                          │
│        │                                                                     │
│        ▼                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐         │
│   │  FRONTEND (Next.js + Vercel AI SDK)                          │         │
│   │                                                              │         │
│   │  • Chat component streams messages                           │         │
│   │  • Receives structured responses from agent                  │         │
│   │  • Renders agent-generated UI components                     │         │
│   │  • Shows agent state (thinking, calling tools, synthesizing) │         │
│   └──────────────────────────────────────────────────────────────┘         │
│        │                                                                     │
│        ▼ POST /api/chat                                                     │
│   ┌──────────────────────────────────────────────────────────────┐         │
│   │  API ROUTES (Next.js Backend)                                │         │
│   │                                                              │         │
│   │  • /api/chat → Model Serving endpoint                        │         │
│   │  • Manages conversation_id (Lakebase memory)                 │         │
│   │  • Passes user_token for on-behalf-of-user auth              │         │
│   └──────────────────────────────────────────────────────────────┘         │
│        │                                                                     │
│        ▼ HTTP POST with user context                                        │
│   ┌──────────────────────────────────────────────────────────────┐         │
│   │  MODEL SERVING (health_monitor_orchestrator)                 │         │
│   │                                                              │         │
│   │  • Receives: {messages, user_id, conversation_id}            │         │
│   │  • Returns: {content, sources, confidence, metadata}         │         │
│   └──────────────────────────────────────────────────────────────┘         │
│        │                                                                     │
│        ▼                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐         │
│   │  ORCHESTRATOR AGENT (LangGraph State Machine)                │         │
│   │                                                              │         │
│   │  1. Load context (Lakebase short/long-term memory)           │         │
│   │  2. Classify intent (cost, security, performance, etc.)      │         │
│   │  3. Route to worker agents (parallel if multi-domain)        │         │
│   │  4. Invoke utility tools (web search, dashboards, etc.)      │         │
│   │  5. Synthesize unified response                              │         │
│   │  6. Save conversation turn                                   │         │
│   └──────────────────────────────────────────────────────────────┘         │
│        │                                                                     │
│        ▼                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐         │
│   │  WORKER AGENTS (5 Domain Specialists)                        │         │
│   │                                                              │         │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │         │
│   │  │   Cost   │  │ Security │  │Performance│  │Reliability│   │         │
│   │  │  Agent   │  │  Agent   │  │  Agent    │  │  Agent    │   │         │
│   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │         │
│   │       │              │              │              │          │         │
│   │       ▼              ▼              ▼              ▼          │         │
│   │  ┌──────────────────────────────────────────────────────┐   │         │
│   │  │           GENIE SPACES (6 Total)                     │   │         │
│   │  │  • Cost Intelligence Genie                           │   │         │
│   │  │  • Security Auditor Genie                            │   │         │
│   │  │  • Performance Optimizer Genie                       │   │         │
│   │  │  • Job Health Monitor Genie                          │   │         │
│   │  │  • Data Quality Monitor Genie                        │   │         │
│   │  │  • Unified Health Monitor Genie                      │   │         │
│   │  └──────────────────────────────────────────────────────┘   │         │
│   │       │                                                       │         │
│   │       ▼                                                       │         │
│   │  ┌──────────────────────────────────────────────────────┐   │         │
│   │  │  DATA LAYER (Abstracted by Genie)                    │   │         │
│   │  │  • 60 TVFs                                            │   │         │
│   │  │  • 30 Metric Views                                    │   │         │
│   │  │  • 25 ML Models                                       │   │         │
│   │  │  • 12 Lakehouse Monitors                              │   │         │
│   │  └──────────────────────────────────────────────────────┘   │         │
│   └──────────────────────────────────────────────────────────────┘         │
│        │                                                                     │
│        ▼                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐         │
│   │  UTILITY TOOLS (4 Total)                                      │         │
│   │                                                              │         │
│   │  • Web Search (Databricks status, docs)                      │         │
│   │  • Dashboard Linker (AI/BI dashboard deep links)             │         │
│   │  • Alert Trigger (Proactive notifications)                   │         │
│   │  • Runbook RAG (Remediation steps)                           │         │
│   └──────────────────────────────────────────────────────────────┘         │
│        │                                                                     │
│        ▼                                                                     │
│   STRUCTURED RESPONSE → FRONTEND                                             │
│   {                                                                          │
│     "content": "Costs spiked due to...",                                    │
│     "sources": ["Cost Intelligence Genie", "fact_usage"],                   │
│     "confidence": 0.92,                                                      │
│     "metadata": {                                                            │
│       "agents_invoked": ["cost", "reliability"],                            │
│       "tools_used": ["cost_genie", "dashboard_linker"],                     │
│       "viz_components": ["anomaly_card", "forecast_chart"],                 │
│       "action_buttons": ["view_dashboard", "investigate", "set_alert"]      │
│     }                                                                        │
│   }                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Response Format: Agent → Frontend

**Structured response enables rich UI rendering:**

```typescript
interface AgentResponse {
  // Core response
  content: string;                    // Markdown text response
  sources: string[];                  // Data sources cited
  confidence: number;                 // 0.0-1.0
  
  // Agent metadata (NEW - for UI display)
  metadata: {
    // Which agents were invoked
    agents_invoked: string[];         // ["cost", "reliability"]
    agent_responses: {
      [domain: string]: {
        response: string;
        confidence: number;
        sources: string[];
      }
    };
    
    // Which tools were used
    tools_used: string[];             // ["cost_genie", "web_search"]
    tool_results: {
      [tool: string]: any;
    };
    
    // UI components to render
    viz_components: VizComponent[];   // Agent specifies which charts/cards
    action_buttons: ActionButton[];   // Agent suggests actions
    
    // Intent classification
    intent: {
      domains: string[];              // ["cost", "reliability"]
      confidence: number;
    };
    
    // Conversation state
    conversation_id: string;
    message_id: string;
    
    // MLflow trace
    trace_id: string;
  };
}

interface VizComponent {
  type: "anomaly_card" | "forecast_chart" | "risk_gauge" | "trend_line" | "kpi_card";
  data: any;                          // Data for the component
  props: Record<string, any>;         // Component props
}

interface ActionButton {
  label: string;
  action: "navigate" | "trigger_alert" | "export" | "schedule";
  params: Record<string, any>;
}
```

---

## Conversational UI Patterns (10 Patterns)

### Pattern 1: Agent State Display

**Purpose:** Show what the agent is doing in real-time

```
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Why did costs spike last Tuesday?                     │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 🤖                                       │
│                                                        │
│  🔄 Analyzing your question...                         │
│                                                        │
│  ✓ Classified intent: Cost Analysis (95% confidence)  │
│  ✓ Routing to Cost Agent                              │
│  🔄 Querying Cost Intelligence Genie...                │
│     └─ get_daily_cost_summary(date='2025-01-14')     │
│     └─ get_cost_anomalies(date='2025-01-14')         │
│  ✓ Received data from Genie                           │
│  🔄 Synthesizing response...                           │
│                                                        │
│  [Response appears below after synthesis]              │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Progress Indicator**: Animated dots or spinner
- **Status Icons**: ✓ (done), 🔄 (in progress), ❌ (error)
- **Collapsible Details**: Click to expand/collapse agent steps
- **Color Coding**: Blue for processing, green for success
- **Timing**: Show elapsed time for each step

**States:**
```typescript
type AgentState = 
  | "classifying_intent"
  | "routing_to_agents"
  | "querying_genie"
  | "calling_tools"
  | "synthesizing"
  | "complete"
  | "error";
```

---

### Pattern 2: Multi-Agent Coordination Display

**Purpose:** Show when multiple agents work together

```
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Are expensive jobs also the ones failing?             │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Orchestrator] 🧠                                     │
│                                                        │
│  ✓ Multi-domain query detected                        │
│  ✓ Routing to: Cost Agent + Reliability Agent         │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  PARALLEL EXECUTION                              │ │
│  │                                                  │ │
│  │  💰 Cost Agent         🔄 Reliability Agent      │ │
│  │  ▓▓▓▓▓▓▓▓▓▓░░░ 80%    ▓▓▓▓▓▓▓▓▓▓░░░ 75%       │ │
│  │  Querying costs...     Querying failures...      │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ✓ Both agents completed                              │
│  🔄 Correlating expensive jobs with failures...        │
│                                                        │
│  [Synthesized response appears below]                  │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Parallel Progress Bars**: Show each agent's progress
- **Agent Icons**: Domain-specific icons (💰 Cost, 🔄 Reliability)
- **Correlation Indicator**: Show when orchestrator is correlating
- **Expandable Agent Responses**: Click agent to see individual response
- **Timeline View**: Show execution timeline with overlapping bars

---

### Pattern 3: Tool Invocation Display

**Purpose:** Show when agent calls utility tools

```
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Is Databricks having an outage right now?             │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Orchestrator] 🧠                                     │
│                                                        │
│  ✓ Detected real-time information need                │
│  🔄 Calling Web Search tool...                         │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  🔍 WEB SEARCH TOOL                              │ │
│  │                                                  │ │
│  │  Query: "Databricks service status current"     │ │
│  │  Domain: status.databricks.com                  │ │
│  │                                                  │ │
│  │  ✓ Found 3 results (180ms)                      │ │
│  │                                                  │ │
│  │  📄 Databricks Status                           │ │
│  │     All systems operational                     │ │
│  │     Last updated: 2 minutes ago                 │ │
│  │     [View Status Page →]                        │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ✅ No outages detected. All systems operational.     │
│                                                        │
│  Would you like me to check specific services?         │
│  [SQL Warehouse] [Jobs] [Model Serving] [Notebooks]   │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Tool Card**: Expandable card showing tool invocation
- **Tool Icon**: Specific icon per tool (🔍 search, 📊 dashboard, 🔔 alert)
- **Tool Results**: Formatted results with source attribution
- **Follow-up Actions**: Agent suggests next steps
- **External Links**: Link to external sources (status page, docs)

---

### Pattern 4: Conversational Dashboard Generation

**Purpose:** Agent generates visualizations in response

```
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Show me cost trends for the past month                │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  Here's your cost trend analysis for the last 30 days: │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  📊 DAILY COST TREND                             │ │
│  │                                                  │ │
│  │  $60K ┤                          ╱────────       │ │
│  │       │                    ╱────╱                │ │
│  │  $50K ┤              ╱────╱                      │ │
│  │       │        ╱────╱                            │ │
│  │  $40K ┤  ─────╱                                  │ │
│  │       └────────────────────────────────────────► │ │
│  │        Dec 15    Jan 1     Jan 15   Jan 30      │ │
│  │                                                  │ │
│  │  ⚠️  Anomaly detected on Jan 22 (+45%)          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Key Insights:                                         │
│  • Average daily cost: $45,230                         │
│  • 30-day trend: +18% increase                         │
│  • Spike on Jan 22: GPU training job                   │
│                                                        │
│  Would you like to:                                    │
│  [Investigate Jan 22 Spike] [Set Cost Alert]          │
│  [View Detailed Dashboard] [Export Report]            │
│                                                        │
│  Data source: Cost Intelligence Genie → fact_usage    │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Inline Chart**: Chart rendered within chat message
- **Anomaly Markers**: Highlight anomalies on chart
- **Key Insights**: Bullet points with metrics
- **Action Buttons**: Agent-suggested next steps
- **Data Attribution**: Source citation at bottom

---

### Pattern 5: Memory-Aware Responses

**Purpose:** Show that agent remembers context

```
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  What's my cost summary?                               │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  📝 Based on your preferences:                         │
│  • Workspace: prod (your default)                      │
│  • Time period: Last 7 days (your usual)               │
│  • Alert threshold: $10,000/day                        │
│                                                        │
│  Here's your cost summary for prod workspace:          │
│                                                        │
│  [KPI Cards and charts]                                │
│                                                        │
│  💡 I noticed you ask about costs every Monday morning.│
│     Would you like me to send a weekly cost summary?   │
│     [Yes, schedule it] [No thanks]                     │
│                                                        │
│  Memory: Based on 12 previous conversations            │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Memory Badge**: 📝 indicator showing memory was used
- **Preference Display**: Show which preferences were applied
- **Proactive Suggestion**: Agent suggests automation based on patterns
- **Memory Attribution**: "Based on X previous conversations"

---

### Pattern 6: Proactive Anomaly Notifications

**Purpose:** Agent messages user when anomaly detected

```
┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰  •  Proactive Alert                   │
│  2 minutes ago                                         │
│                                                        │
│  🔴 I detected a cost anomaly that needs your attention│
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  💰 Cost Anomaly Detected                        │ │
│  │                                                  │ │
│  │  Score: -0.78 (HIGH)                             │ │
│  │  ████████████████████░░░ 78% anomalous           │ │
│  │                                                  │ │
│  │  ml-workspace                                    │ │
│  │  $4,890 (baseline: $1,200)                       │ │
│  │  +308% increase                                  │ │
│  │                                                  │ │
│  │  Root Cause (ML Analysis):                      │ │
│  │  • GPU training job on g5.12xlarge              │ │
│  │  • Running for 18 hours (expected: 2 hours)     │ │
│  │  • Job: model_training_pipeline_v3              │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Recommended Actions:                                  │
│  1. Check if training job should still be running     │
│  2. Consider using smaller GPU instance               │
│  3. Enable job timeout alerts                         │
│                                                        │
│  [Investigate Now] [Stop Job] [Dismiss] [Set Alert]   │
│                                                        │
│  Model: cost_anomaly_detector v2.1 (92% confidence)   │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Proactive Badge**: "Proactive Alert" label
- **Timestamp**: "2 minutes ago"
- **Anomaly Card**: Embedded anomaly visualization
- **Action Buttons**: Direct actions (not just "view")
- **Dismissible**: User can dismiss if not relevant

---

### Pattern 7: Conversational Filters

**Purpose:** Replace traditional filters with conversation

```
Traditional Approach:
┌────────────────────────────────────────────────────────┐
│  Cost Dashboard                                        │
│                                                        │
│  Workspace: [All Workspaces ▼]                         │
│  Date Range: [Last 7 Days ▼]                           │
│  SKU: [All SKUs ▼]                                     │
│  Tag: [All Tags ▼]                                     │
│  [Apply Filters]                                       │
└────────────────────────────────────────────────────────┘

AI-First Approach:
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Show costs for prod workspace from last week          │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  ✓ Filters applied:                                    │
│  • Workspace: prod                                     │
│  • Date: Jan 15-22, 2025                               │
│                                                        │
│  [Visualization with filtered data]                    │
│                                                        │
│  Refine: [Different workspace?] [Extend date range?]  │
└────────────────────────────────────────────────────────┘

Follow-up:
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Just show GPU costs                                   │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  ✓ Added filter: SKU contains "GPU"                   │
│                                                        │
│  [Updated visualization]                               │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Filter Display**: Show applied filters as tags
- **Conversational Refinement**: Natural language follow-ups
- **Quick Refine Buttons**: Common filter adjustments as buttons
- **Filter History**: Show conversation thread as filter evolution

---

### Pattern 8: Multi-Step Workflows

**Purpose:** Agent guides user through complex tasks

```
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  I want to optimize costs for my ML workloads          │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  I'll help you optimize ML workload costs. Let's start │
│  by analyzing your current spending.                   │
│                                                        │
│  📋 STEP 1 OF 4: Analyze Current Costs                 │
│                                                        │
│  🔄 Analyzing ML workload costs...                     │
│  ✓ Found: 12 ML jobs, $15,340/month                   │
│                                                        │
│  [Cost breakdown chart]                                │
│                                                        │
│  Key finding: 8 jobs using All-Purpose Compute        │
│  (could save $4,200/month with Jobs Compute)          │
│                                                        │
│  [Next: Identify Opportunities →]                      │
└────────────────────────────────────────────────────────┘

[User clicks "Next"]

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  📋 STEP 2 OF 4: Optimization Opportunities            │
│                                                        │
│  I found 3 optimization opportunities:                 │
│                                                        │
│  1. 💡 Migrate 8 jobs to Jobs Compute                  │
│     Savings: $4,200/month (28%)                        │
│     Effort: Medium (2-3 hours)                         │
│     Risk: Low                                          │
│                                                        │
│  2. 💡 Right-size ml-cluster-01                        │
│     Savings: $1,850/month (12%)                        │
│     Effort: Low (30 minutes)                           │
│     Risk: Low                                          │
│                                                        │
│  3. 💡 Enable auto-scaling on 5 clusters               │
│     Savings: $2,100/month (14%)                        │
│     Effort: Low (1 hour)                               │
│     Risk: Very Low                                     │
│                                                        │
│  Total potential savings: $8,150/month (53%)           │
│                                                        │
│  Which opportunities would you like to implement?      │
│  [All] [Just #1] [#1 + #2] [Custom Selection]         │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Progress Indicator**: "Step X of Y"
- **Step Summary**: What was accomplished in this step
- **Navigation**: Next/Previous buttons
- **Checkpoint Saves**: Can resume workflow later
- **Action Selection**: Multiple choice or custom selection

---

### Pattern 9: Inline Actions

**Purpose:** Actions within chat messages

```
┌────────────────────────────────────────────────────────┐
│  [Reliability Agent] 🔄                                │
│                                                        │
│  I found 3 failed jobs in the last 24 hours:           │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  ❌ nightly_etl                                   │ │
│  │     Failed at: 2:15 AM                           │ │
│  │     Error: Timeout after 2 hours                 │ │
│  │     [View Logs] [Retry Now] [View Run]          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  ❌ data_quality_check                           │ │
│  │     Failed at: 6:45 AM                           │ │
│  │     Error: Schema mismatch                       │ │
│  │     [View Logs] [Retry Now] [View Run]          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  ❌ ml_training_pipeline                         │ │
│  │     Failed at: 10:30 AM                          │ │
│  │     Error: Out of memory                         │ │
│  │     [View Logs] [Retry Now] [View Run]          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Bulk actions:                                         │
│  [Retry All Failed Jobs] [Export Error Report]        │
│  [Set Up Failure Alerts]                              │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Item Cards**: Each result as expandable card
- **Item Actions**: Actions specific to each item
- **Bulk Actions**: Actions across all results
- **Action Feedback**: Inline confirmation when action taken

---

### Pattern 10: Conversational Drill-Down

**Purpose:** Navigate data hierarchy conversationally

```
┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Show me top cost contributors                         │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  Top 5 cost contributors (last 7 days):                │
│                                                        │
│  1. ml-workspace: $12,450 (28%)                        │
│  2. prod-workspace: $9,870 (22%)                       │
│  3. analytics-warehouse: $7,230 (16%)                  │
│  4. dev-workspace: $6,540 (15%)                        │
│  5. staging-workspace: $4,890 (11%)                    │
│                                                        │
│  Tap any workspace to drill down ↓                     │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Tell me more about ml-workspace                       │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  ml-workspace breakdown ($12,450 total):               │
│                                                        │
│  By SKU:                                               │
│  • Jobs Compute GPU: $8,340 (67%)                      │
│  • All-Purpose Compute: $2,890 (23%)                   │
│  • SQL Warehouse: $1,220 (10%)                         │
│                                                        │
│  [Chart: Cost by SKU over time]                        │
│                                                        │
│  Drill deeper?                                         │
│  [By Job] [By User] [By Tag] [By Cluster]             │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Show by job                                           │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  ml-workspace costs by job:                            │
│                                                        │
│  1. model_training_pipeline: $6,780 (54%)              │
│  2. feature_engineering: $2,450 (20%)                  │
│  3. batch_inference: $1,890 (15%)                      │
│  4. hyperparameter_tuning: $1,330 (11%)                │
│                                                        │
│  💡 model_training_pipeline accounts for over half    │
│     the workspace spend. Would you like optimization   │
│     recommendations for this job?                      │
│                                                        │
│  [Yes, show recommendations] [View job details]        │
└────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Breadcrumb Trail**: Show drill-down path (Top → Workspace → Job)
- **Interactive Items**: Each item is clickable to drill down
- **Quick Drill Buttons**: Common drill-down paths as buttons
- **Back Navigation**: "Go back to workspace view" link
- **Smart Suggestions**: Agent suggests next drill-down based on insights

---

## Multi-Agent Coordination Display

### Real-Time Agent Status Dashboard

```
┌────────────────────────────────────────────────────────────────┐
│  AGENT SYSTEM STATUS                          [Expand All ▼]   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  🧠 ORCHESTRATOR AGENT                     ✅ ACTIVE      │ │
│  │  Current query: "Platform health overview"               │ │
│  │  Intent: Multi-domain (5 agents)                         │ │
│  │  Confidence: 88%                                         │ │
│  │  [View Trace →]                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  💰 COST AGENT                             🔄 QUERYING   │ │
│  │  ████████████░░░░░ 75% complete                          │ │
│  │  Genie query: get_daily_cost_summary()                   │ │
│  │  Sources: 3 TVFs, 1 Metric View                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  🔒 SECURITY AGENT                         🔄 QUERYING   │ │
│  │  ████████████████░░ 85% complete                         │ │
│  │  Genie query: get_security_events_summary()              │ │
│  │  Sources: 2 TVFs, 2 ML Models                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  ⚡ PERFORMANCE AGENT                      ⏸️  WAITING    │ │
│  │  Queued (parallel execution limit: 3)                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  🔄 RELIABILITY AGENT                      ⏸️  WAITING    │ │
│  │  Queued (parallel execution limit: 3)                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  📊 QUALITY AGENT                          ⏸️  WAITING    │ │
│  │  Queued (parallel execution limit: 3)                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Estimated completion: 4 seconds                               │
└────────────────────────────────────────────────────────────────┘
```

### Agent Coordination Timeline

```
┌────────────────────────────────────────────────────────────────┐
│  AGENT EXECUTION TIMELINE                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Time (seconds)                                                 │
│  0s ─── 1s ─── 2s ─── 3s ─── 4s ─── 5s                        │
│  │                                                              │
│  🧠 Orchestrator ●═══════════════════════════════●            │
│                  ↓      ↓             ↓                        │
│                  │      │             │                        │
│  💰 Cost         ●══════●              Synthesizing...         │
│                         │                                      │
│  🔒 Security           ●════════●                              │
│                                 │                              │
│  ⚡ Performance                 ●══════●                       │
│                                        │                       │
│  🔄 Reliability                        ●═════●                 │
│                                              │                 │
│  📊 Quality                                  ●════●            │
│                                                                │
│  Legend: ● Start/End   ═ Executing   ─ Waiting                │
└────────────────────────────────────────────────────────────────┘
```

---

## Agent Reasoning Visualization

### Intent Classification Display

```
┌────────────────────────────────────────────────────────┐
│  🧠 INTENT CLASSIFICATION                              │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Query: "Why are my jobs slow and expensive?"          │
│                                                        │
│  Detected Domains:                                     │
│  ████████████████████░ Performance (95% confidence)    │
│  ████████████████░░░░ Cost (85% confidence)            │
│  ████████░░░░░░░░░░░░ Reliability (42% confidence)     │
│                                                        │
│  Keywords matched:                                     │
│  • "slow" → Performance ✓                              │
│  • "expensive" → Cost ✓                                │
│  • "jobs" → Performance + Reliability                  │
│                                                        │
│  Classification Model: DBRX Instruct                   │
│  Classification Time: 120ms                            │
│                                                        │
│  [View Full Prompt] [View Model Response]              │
└────────────────────────────────────────────────────────┘
```

### Response Synthesis Display

```
┌────────────────────────────────────────────────────────┐
│  🧠 RESPONSE SYNTHESIS                                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Combining insights from 2 agents:                     │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  💰 Cost Agent Input:                            │ │
│  │  "Jobs cost $15K/day, 40% above baseline..."     │ │
│  │  Confidence: 92%                                 │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  ⚡ Performance Agent Input:                     │ │
│  │  "Jobs taking 2x longer due to cluster sizing..." │ │
│  │  Confidence: 89%                                 │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  🔄 Synthesizing...                                    │
│                                                        │
│  Correlations found:                                   │
│  ✓ Slow jobs → higher costs (longer runtime)          │
│  ✓ Cluster undersized → spill to disk → slow          │
│  ✓ All-Purpose compute used → expensive                │
│                                                        │
│  Synthesis Model: DBRX Instruct                        │
│  Synthesis Time: 450ms                                 │
│                                                        │
│  [View Synthesized Response ↓]                         │
└────────────────────────────────────────────────────────┘
```

---

## Memory-Aware UI Components

### User Preferences Panel

```
┌────────────────────────────────────────────────────────┐
│  YOUR PREFERENCES                          [Edit ⚙️]   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  🎯 Defaults (Learned from 47 conversations)           │
│  • Workspace: prod (mentioned 85% of time)             │
│  • Time range: Last 7 days (your usual)                │
│  • Cost threshold: $10,000/day                         │
│  • Notification preference: Slack + Email              │
│                                                        │
│  💼 Your Role: Data Engineer                           │
│  Communication style: Technical details + SQL queries  │
│                                                        │
│  📊 Your Patterns                                      │
│  • You check costs every Monday at 9 AM                │
│  • You review failed jobs daily                        │
│  • You ask about GPU costs most often                  │
│                                                        │
│  🔔 Smart Alerts (Agent-suggested)                     │
│  ✅ Weekly cost summary (Mondays at 9 AM)              │
│  ✅ Critical job failures (immediate)                  │
│  ⏸️  GPU cost spikes >$5K (paused - you said "too noisy")│
│                                                        │
│  Last updated: Agent learned from conversation 2m ago  │
└────────────────────────────────────────────────────────┘
```

### Conversation History Sidebar

```
┌────────────────────────────────────────────────────────┐
│  RECENT CONVERSATIONS                      [View All →]│
├────────────────────────────────────────────────────────┤
│                                                        │
│  Today                                                 │
│  ┌──────────────────────────────────────────────────┐ │
│  │  💰 Cost spike investigation                     │ │
│  │  10:15 AM • 12 messages • Cost Agent             │ │
│  │  "Why did costs spike..."                        │ │
│  │  [Continue →]                                    │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  🔄 Failed job analysis                          │ │
│  │  9:30 AM • 8 messages • Reliability Agent        │ │
│  │  "Why is nightly_etl..."                         │ │
│  │  [Continue →]                                    │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Yesterday                                             │
│  ┌──────────────────────────────────────────────────┐ │
│  │  🔒 Security audit                               │ │
│  │  4:45 PM • 15 messages • Security Agent          │ │
│  │  "Show me access events..."                      │ │
│  │  [Continue →]                                    │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  📝 All conversations saved for 24 hours               │
│  💾 Preferences saved for 1 year                       │
└────────────────────────────────────────────────────────┘
```

---

## Proactive Agent Interactions

### Proactive Insight Card (Homepage)

```
┌────────────────────────────────────────────────────────┐
│  💡 INSIGHTS FOR YOU                                   │
│  Based on analysis running in the background           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  🔴 URGENT (2 insights)                                │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  💰 Cost Anomaly Detected                        │ │
│  │  ml-workspace is 308% above baseline             │ │
│  │  [Investigate] [Dismiss]                         │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  🔄 Job Failure Predicted                        │ │
│  │  nightly_etl has 89% failure probability tonight │ │
│  │  [Review] [Take Action]                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  🟡 OPPORTUNITIES (3 insights)                         │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  💡 Optimization Opportunity                     │ │
│  │  Save $4,200/month by migrating 8 jobs           │ │
│  │  [Learn More] [Dismiss]                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  [View All Insights] [Configure Alerts]                │
└────────────────────────────────────────────────────────┘
```

### Agent-Initiated Conversations

```
┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰  •  Started conversation              │
│  5 minutes ago                                         │
│                                                        │
│  Hi! I noticed an unusual pattern I wanted to discuss. │
│                                                        │
│  I've been analyzing your cost data and found that     │
│  12 of your jobs are using All-Purpose Compute, which  │
│  is significantly more expensive than Jobs Compute.    │
│                                                        │
│  Potential savings: $4,200/month (28% reduction)       │
│                                                        │
│  Would you like me to:                                 │
│  1. Show you which jobs can be migrated                │
│  2. Create a migration plan                            │
│  3. Just note this for later                           │
│                                                        │
│  [Show jobs] [Create plan] [Note for later]            │
└────────────────────────────────────────────────────────┘

[If user doesn't respond in 10 minutes]

┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  No problem! I've saved this insight to your inbox.   │
│  You can review it anytime by asking "Show my insights"│
│                                                        │
│  I'll also include it in your Monday morning summary.  │
└────────────────────────────────────────────────────────┘
```

---

## Tool Invocation Display

### Genie Query Visualization

```
┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  🔄 Querying Cost Intelligence Genie...                │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  🧞 GENIE SPACE: Cost Intelligence                │ │
│  │                                                  │ │
│  │  Natural Language Query:                         │ │
│  │  "What are the top 10 cost contributors for     │ │
│  │   prod workspace in the last 7 days?"           │ │
│  │                                                  │ │
│  │  ✓ Query understood (confidence: 95%)           │ │
│  │  🔄 Routing to data sources...                   │ │
│  │                                                  │ │
│  │  Data Sources Used:                              │ │
│  │  ✓ TVF: get_top_cost_contributors()             │ │
│  │  ✓ Metric View: cost_analytics_metrics          │ │
│  │  ✓ ML Model: cost_forecaster                    │ │
│  │                                                  │ │
│  │  ✓ Query complete (1.2s)                        │ │
│  │  📊 15 rows returned                            │ │
│  │                                                  │ │
│  │  [View SQL Generated] [View Raw Data]           │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Here are your top cost contributors:                  │
│  [Visualization with data from Genie]                  │
└────────────────────────────────────────────────────────┘
```

### Dashboard Linker Tool Display

```
┌────────────────────────────────────────────────────────┐
│  [Cost Agent] 💰                                       │
│                                                        │
│  I've prepared a detailed dashboard for deeper analysis│
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  📊 DASHBOARD LINKER TOOL                        │ │
│  │                                                  │ │
│  │  Matched Dashboard: Cost Analysis Dashboard      │ │
│  │  Relevance: 95% (best match for cost queries)   │ │
│  │                                                  │ │
│  │  Pre-applied filters:                            │ │
│  │  • Workspace: prod                               │ │
│  │  • Date range: Last 7 days                       │ │
│  │  • Anomalies: Highlighted                        │ │
│  │                                                  │ │
│  │  [Open Dashboard in New Tab →]                   │ │
│  │  [Embed Dashboard Here]                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Other relevant dashboards:                            │
│  • Warehouse Advisor Dashboard                         │
│  • Serverless Cost Observability                       │
│  • Platform Health Overview                            │
└────────────────────────────────────────────────────────┘
```

---

## Agentic Workflows

### Workflow Template: Incident Investigation

```
┌────────────────────────────────────────────────────────┐
│  AGENT-GUIDED WORKFLOW: Incident Investigation         │
│  Started: 2 minutes ago  •  Progress: 40%              │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ✅ STEP 1: Identify incident                          │
│  Agent detected: Cost spike on Jan 22                  │
│                                                        │
│  🔄 STEP 2: Gather context (IN PROGRESS)               │
│  ▓▓▓▓▓▓▓▓░░░░░░░ 60%                                   │
│  • ✓ Cost data collected                               │
│  • ✓ Job run history retrieved                         │
│  • 🔄 Cluster utilization being analyzed...            │
│  • ⏸️  User activity pending...                         │
│                                                        │
│  ⏸️  STEP 3: Analyze root cause                        │
│  Waiting for Step 2 to complete                        │
│                                                        │
│  ⏸️  STEP 4: Generate recommendations                  │
│  Not started                                           │
│                                                        │
│  ⏸️  STEP 5: Create action plan                        │
│  Not started                                           │
│                                                        │
│  [Pause Workflow] [Skip Step] [View Details]           │
└────────────────────────────────────────────────────────┘

[After workflow completes]

┌────────────────────────────────────────────────────────┐
│  WORKFLOW COMPLETE: Incident Investigation             │
│  Duration: 8 minutes  •  5 agents involved             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  📊 INVESTIGATION SUMMARY                              │
│                                                        │
│  Incident: Cost spike on Jan 22 (+$2,340)             │
│                                                        │
│  Root Cause: GPU training job ran 18h instead of 2h   │
│                                                        │
│  Contributing Factors:                                 │
│  • Job timeout not configured                          │
│  • Auto-termination disabled                           │
│  • No cost alerts set                                  │
│                                                        │
│  Recommendations:                                      │
│  1. Configure 4-hour timeout for this job              │
│  2. Enable auto-termination after 1h idle              │
│  3. Set $2,000/day cost alert                          │
│                                                        │
│  [Apply All Recommendations] [Export Report]           │
│  [Save Workflow as Template]                           │
└────────────────────────────────────────────────────────┘
```

---

## Enhanced Chat Interface

### Main Chat Layout (Full-Screen Priority)

```
┌─────────────────────────────────────────────────────────────────┐
│  HEALTH MONITOR                    [Settings ⚙️] [User Avatar]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  CONVERSATIONS (Left Sidebar - 20% width)                  ││
│  │                                                            ││
│  │  [New Chat +]                                              ││
│  │                                                            ││
│  │  💡 Insights (3 new)                                       ││
│  │  🔔 Alerts (2 new)                                         ││
│  │                                                            ││
│  │  Today                                                     ││
│  │  • Cost spike investigation                                ││
│  │  • Failed job analysis                                     ││
│  │                                                            ││
│  │  Yesterday                                                 ││
│  │  • Security audit                                          ││
│  │                                                            ││
│  │  [View All →]                                              ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  CHAT AREA (Center - 60% width)                           ││
│  │                                                            ││
│  │  [Scrollable message history]                              ││
│  │                                                            ││
│  │  ┌──────────────────────────────────────────────────────┐ ││
│  │  │  [User message]                                      │ ││
│  │  └──────────────────────────────────────────────────────┘ ││
│  │                                                            ││
│  │  ┌──────────────────────────────────────────────────────┐ ││
│  │  │  [Agent response with visualizations]                │ ││
│  │  └──────────────────────────────────────────────────────┘ ││
│  │                                                            ││
│  │  [More messages...]                                        ││
│  │                                                            ││
│  │  ┌──────────────────────────────────────────────────────┐ ││
│  │  │  Type your question...                               │ ││
│  │  │  [Send ↑]                                             │ ││
│  │  └──────────────────────────────────────────────────────┘ ││
│  │                                                            ││
│  │  Suggestions:                                              ││
│  │  [Show cost trends] [Failed jobs today] [Security events] ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  CONTEXT PANEL (Right Sidebar - 20% width, collapsible)   ││
│  │                                                            ││
│  │  🧠 Agent Status                                           ││
│  │  [Current agents working]                                  ││
│  │                                                            ││
│  │  📊 Quick Insights                                         ││
│  │  • Total cost today: $45.2K                                ││
│  │  • Failed jobs: 3                                          ││
│  │  • Security events: 127                                    ││
│  │                                                            ││
│  │  📝 Your Preferences                                       ││
│  │  • Workspace: prod                                         ││
│  │  • Time: Last 7 days                                       ││
│  │                                                            ││
│  │  [View All Preferences →]                                  ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Chat Input Enhancements

**Smart Input with Context Awareness:**

```
┌────────────────────────────────────────────────────────┐
│  Type your question...                                 │
│  💡 Try: "Show me failed jobs for prod workspace"      │
│  [Send ↑]                                              │
├────────────────────────────────────────────────────────┤
│  📎 Attach: [Dashboard] [Report] [Alert]               │
│  🎯 Context: prod workspace, last 7 days (from prefs)  │
│  🧠 Agent: Cost Agent (suggested based on conversation) │
└────────────────────────────────────────────────────────┘

[As user types]

┌────────────────────────────────────────────────────────┐
│  Type: "show cost"                                     │
│                                                        │
│  Suggestions (AI-powered):                             │
│  💰 show cost trends for the last month                │
│  💰 show cost breakdown by workspace                   │
│  💰 show cost anomalies                                │
│  💰 show cost forecast                                 │
└────────────────────────────────────────────────────────┘
```

---

## Intent-Driven Navigation

### Natural Language Navigation

```
Traditional:
User clicks: Dashboard → Cost Center → Date Picker → Filter → Apply

AI-First:
User types: "Show me costs for prod from last week"
Agent: Navigates + filters + displays

┌────────────────────────────────────────────────────────┐
│  [User]                                                │
│  Take me to the security dashboard for last 24 hours  │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  [Orchestrator] 🧠                                     │
│                                                        │
│  ✓ Intent detected: Navigation + Security + Filter    │
│  🔄 Navigating to Security Center...                   │
│  ✓ Applied filter: Last 24 hours                      │
│                                                        │
│  [Page transition animation]                           │
└────────────────────────────────────────────────────────┘

[Security Center page loads with filters pre-applied]

┌────────────────────────────────────────────────────────┐
│  SECURITY CENTER                                       │
│  Showing: Last 24 hours (agent-applied filter)         │
│                                                        │
│  [Dashboard with data]                                 │
│                                                        │
│  💬 Agent: "Here's your security overview. Would you   │
│             like me to highlight any specific events?" │
└────────────────────────────────────────────────────────┘
```

---

## Conversational Data Exploration

### Query → Refine → Drill Pattern

**Step 1: Initial Query**

```
User: "Show me my most expensive jobs"

Agent: [Displays chart with top 10 jobs]
       "Here are your top 10 most expensive jobs..."
       
       Quick actions:
       [Filter by workspace] [Last 30 days instead] [Show details]
```

**Step 2: Conversational Refinement**

```
User: "Just show GPU jobs"

Agent: ✓ Applied filter: SKU contains "GPU"
       [Updated chart with only GPU jobs]
       
       "Refined to GPU jobs only. 6 of your top 10 are GPU jobs,
        accounting for $8,340/day."
```

**Step 3: Drill Down**

```
User: "Tell me more about the top one"

Agent: "model_training_pipeline costs $2,450/day"
       
       [Expanded view with]:
       • Cost breakdown by cluster
       • Runtime history (chart)
       • Optimization recommendations
       
       Would you like to optimize this job?
       [Yes, show recommendations] [No, just monitoring]
```

---

## Component Library: Agentic UI

### Component 1: Agent Status Badge

```
Variants:

🔄 THINKING       (blue, animated dots)
🔍 QUERYING      (purple, animated search)
🧠 SYNTHESIZING  (indigo, animated brain)
✅ COMPLETE      (green, checkmark)
❌ ERROR         (red, exclamation)
⏸️  WAITING       (gray, pause icon)

Props:
- agent: "orchestrator" | "cost" | "security" | etc.
- status: AgentState
- progress?: number (0-100)
- message?: string
```

---

### Component 2: Multi-Agent Progress

```
┌────────────────────────────────────────────────────────┐
│  AGENT COORDINATION                                    │
├────────────────────────────────────────────────────────┤
│  💰 Cost Agent        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░ 85%           │
│  🔒 Security Agent    ▓▓▓▓▓▓▓▓▓▓▓░░░░░ 70%           │
│  ⚡ Performance Agent ▓▓▓▓▓▓░░░░░░░░░░░ 40%           │
│                                                        │
│  Estimated: 3 seconds remaining                        │
└────────────────────────────────────────────────────────┘

Props:
- agents: Array<{domain, status, progress}>
- estimatedTime?: number
```

---

### Component 3: Conversational Card

```
┌────────────────────────────────────────────────────────┐
│  💰 Cost Spike Detected                                │
│  ml-workspace • $4,890 • +308%                         │
├────────────────────────────────────────────────────────┤
│  [Visualization or chart]                              │
│                                                        │
│  Would you like to:                                    │
│  [Investigate] [Set Alert] [Dismiss]                   │
└────────────────────────────────────────────────────────┘

Props:
- title: string
- subtitle?: string
- content: React.ReactNode
- actions: Array<ActionButton>
- dismissible?: boolean
```

---

### Component 4: Genie Query Display

```
┌────────────────────────────────────────────────────────┐
│  🧞 GENIE QUERY                                        │
├────────────────────────────────────────────────────────┤
│  Space: Cost Intelligence                              │
│  Query: "Top 10 cost contributors last 7 days"         │
│                                                        │
│  ✓ Query understood (95% confidence)                   │
│  ✓ Data sources: 3 TVFs, 1 Metric View                │
│  ✓ Complete in 1.2s • 15 rows returned                 │
│                                                        │
│  [View SQL] [View Raw Data]                            │
└────────────────────────────────────────────────────────┘

Props:
- spaceName: string
- query: string
- confidence: number
- sources: string[]
- executionTime: number
- rowCount: number
```

---

### Component 5: Workflow Step

```
┌────────────────────────────────────────────────────────┐
│  ✅ STEP 2 OF 5: Gather Context                        │
├────────────────────────────────────────────────────────┤
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░ 85% complete                        │
│                                                        │
│  • ✓ Cost data collected                               │
│  • ✓ Job history retrieved                             │
│  • 🔄 Analyzing cluster utilization...                 │
│                                                        │
│  [Pause] [Skip Step]                                   │
└────────────────────────────────────────────────────────┘

Props:
- stepNumber: number
- totalSteps: number
- title: string
- status: "pending" | "in_progress" | "complete"
- progress?: number
- substeps: Array<{label, status}>
```

---

## Updated Figma Deliverables

### Pages (10 total - 2 additional)

1. Dashboard Hub (enhanced with proactive agent insights)
2. **Chat Interface (PRIMARY - full-screen priority)**
3. Cost Center (agent-generated visualizations)
4. Job Operations Center (conversational drill-down)
5. Security Center (intent-driven navigation)
6. Data Quality Center (with agent analysis)
7. ML Intelligence (agent reasoning display)
8. Settings & Configuration (memory management)
9. **⭐ NEW: Agent Workflows** (multi-step agent-guided tasks)
10. **⭐ NEW: Conversation History** (memory-aware UI)

### Additional Components (25 new agentic components)

| # | Component | Variants |
|---|-----------|----------|
| 1 | Agent Status Badge | 6 states |
| 2 | Multi-Agent Progress | Parallel + Sequential |
| 3 | Conversational Card | With/without actions |
| 4 | Genie Query Display | Expanded/collapsed |
| 5 | Intent Classification Display | With confidence bars |
| 6 | Response Synthesis Display | Multi-agent inputs |
| 7 | Tool Invocation Card | 4 tools × 2 states |
| 8 | Workflow Step | 3 statuses |
| 9 | Memory Badge | Preferences + History |
| 10 | Proactive Insight Card | 3 severity levels |
| 11 | Agent Reasoning Expansion | Collapsible details |
| 12 | Conversation Timeline | Visual thread |
| 13 | Smart Input Suggestions | Contextual |
| 14 | Agent Avatar | 6 agents + orchestrator |
| 15 | Coordination Timeline | Gantt-style |
| 16 | Filter Tag (Conversational) | Applied filters |
| 17 | Drill-Down Breadcrumb | Hierarchical path |
| 18 | Inline Action Group | Bulk + individual |
| 19 | Agent-Initiated Message | Proactive badge |
| 20 | Workflow Progress | 5-step template |
| 21 | Dashboard Linker Card | Relevance score |
| 22 | Web Search Result Card | Source attribution |
| 23 | Alert Trigger Confirmation | Success/failure states |
| 24 | Runbook Recommendation | Actionable steps |
| 25 | Memory Preferences Panel | Editable settings |

---

## Impact Summary

| Aspect | Before (Base + ML) | After (AI-First) | Change |
|--------|-------------------|------------------|--------|
| **Total Pages** | 290 | 470 | +62% |
| **Primary Interface** | Dashboard navigation | Chat conversation | Paradigm shift |
| **Components** | 40 | 65 | +62% |
| **Pages** | 8 | 10 | +25% |
| **Agent Integration** | None | Complete (6 agents) | New |
| **Conversational Patterns** | 0 | 10 | New |
| **Memory-Aware UI** | No | Yes (Lakebase) | New |
| **Proactive Interactions** | No | Yes | New |
| **Tool Visualization** | No | Yes (4 tools) | New |
| **Multi-Agent Display** | No | Yes | New |

---

## Key Design Principles for Figma

### 1. Conversation-First Layout

- Chat interface occupies **60% of screen** (center)
- Traditional UI elements are **agent outputs**, not primary controls
- Every page is accessible via chat

### 2. Agent Transparency

- **Always show** what agent is doing
- **Never hide** agent reasoning (make it collapsible, not hidden)
- **Visualize** multi-agent coordination

### 3. Proactive Intelligence

- Agent can initiate conversations
- Insights appear without user asking
- Recommendations are conversational

### 4. Memory-Driven Personalization

- UI adapts to learned preferences
- Conversation history is first-class
- Agent references past interactions

### 5. Multimodal Responses

- Agent returns text + visualizations + actions
- All outputs are interactive
- User can refine via text or clicks

---

## Implementation Priority

### Phase 1: Core Agent Integration (Weeks 1-4)
- Agent status display
- Basic conversational UI
- Genie query visualization

### Phase 2: Multi-Agent Coordination (Weeks 5-6)
- Parallel agent progress
- Response synthesis display
- Agent coordination timeline

### Phase 3: Memory & Proactivity (Weeks 7-8)
- Lakebase memory integration
- Proactive insights
- Preferences panel

### Phase 4: Advanced Workflows (Weeks 9-10)
- Multi-step workflows
- Tool invocation display
- Conversational drill-down

### Phase 5: Polish & Refinement (Weeks 11-12)
- Animation and transitions
- Edge cases and errors
- Performance optimization

**Total: 12 weeks** (same timeline, enhanced scope)

---

## References

### Agent Framework
- [Agent Introduction](../../agent-framework-design/01-introduction.md)
- [Agent Architecture](../../agent-framework-design/02-architecture-overview.md)
- [Orchestrator Agent](../../agent-framework-design/03-orchestrator-agent.md)
- [Worker Agents](../../agent-framework-design/04-worker-agents.md)
- [Genie Integration](../../agent-framework-design/05-genie-integration.md)
- [Utility Tools](../../agent-framework-design/06-utility-tools.md)
- [Memory Management](../../agent-framework-design/07-memory-management.md)

### Related
- [Base Frontend PRD](09-frontend-prd.md)
- [ML Enhancement](09a-frontend-prd-ml-enhancements.md)

---

**Document Version:** 3.0  
**Total PRD Pages:** 470 (Base: 150 + ML: 140 + Agentic: 180)  
**Agent Integration:** Complete (Orchestrator + 5 Workers + 4 Tools)  
**Design Paradigm:** AI-First, Conversation-Native  
**Last Updated:** January 2026

