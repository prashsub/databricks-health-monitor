# Phase 5: Frontend App for Databricks Health Monitor

## Overview

**Status:** 📋 Planned  
**Purpose:** Build a modern web application that provides a unified interface for Databricks platform observability, integrating all agents from Phase 4.

**Template Reference:** Based on [databricks/app-templates/e2e-chatbot-app-next](https://github.com/databricks/app-templates/tree/main/e2e-chatbot-app-next)

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND APP                                    │
│                           (Databricks Apps)                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Next.js 14+ (App Router)                        ││
│  │                         + Vercel AI SDK                                 ││
│  │                                                                         ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      ││
│  │  │Dashboard│  │   Chat  │  │  Alerts │  │ Reports │  │ Settings│      ││
│  │  │   Hub   │  │Interface│  │  Center │  │  Center │  │         │      ││
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API                                     │
│                         (Next.js API Routes)                                 │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │ Agent Gateway  │  │  Dashboard API │  │   Alert API    │                 │
│  │ (AI SDK Chat)  │  │  (Phase 3.5)   │  │                │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER (Databricks)                            │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Model Serving│  │  Gold Layer  │  │Metric Views  │  │     TVFs     │    │
│  │  Endpoints   │  │  (Phase 2)   │  │  (Phase 3.3) │  │  (Phase 3.2) │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies (e2e-chatbot-app-next Pattern)

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Framework** | Next.js 14+ (App Router) | Server components, streaming, native API routes |
| **Language** | TypeScript | Type-safe, better DX, maintainability |
| **AI Integration** | Vercel AI SDK | Streaming chat, tool calling, agent support |
| **Styling** | Tailwind CSS | Utility-first, rapid development |
| **Charts** | Recharts / Tremor | React-native, Tailwind-compatible |
| **State** | React Server Components + SWR | Server-first, minimal client state |
| **Backend** | Next.js API Routes | Unified codebase, automatic code splitting |
| **Databricks SDK** | @databricks/sql | Native SQL connectivity |
| **Deployment** | Databricks Apps | Native integration, SSO, permissions |
| **Auth** | Databricks OAuth | Unified authentication |

### Key Dependencies

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "ai": "^3.0.0",
    "@ai-sdk/openai": "^0.0.40",
    "@databricks/sql": "^1.8.0",
    "recharts": "^2.12.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.4.0",
    "zod": "^3.22.0"
  }
}
```

---

## Project Structure

### Directory Layout (e2e-chatbot-app-next Pattern)

```
src/frontend_app/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout with providers
│   ├── page.tsx                 # Dashboard hub (home)
│   ├── chat/
│   │   └── page.tsx             # Chat interface page
│   ├── cost/
│   │   └── page.tsx             # Cost center page
│   ├── jobs/
│   │   └── page.tsx             # Job operations page
│   ├── security/
│   │   └── page.tsx             # Security center page
│   ├── settings/
│   │   └── page.tsx             # Settings page
│   └── api/
│       ├── chat/
│       │   └── route.ts         # Streaming chat endpoint
│       ├── dashboards/
│       │   ├── overview/
│       │   │   └── route.ts     # Dashboard overview API
│       │   ├── cost/
│       │   │   └── route.ts     # Cost data API
│       │   ├── jobs/
│       │   │   └── route.ts     # Jobs data API
│       │   └── security/
│       │       └── route.ts     # Security data API
│       └── alerts/
│           └── route.ts         # Alerts API
├── components/
│   ├── ui/                      # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── charts/                  # Chart components
│   │   ├── line-chart.tsx
│   │   ├── bar-chart.tsx
│   │   ├── pie-chart.tsx
│   │   └── kpi-card.tsx
│   ├── chat/                    # Chat-specific components
│   │   ├── chat-input.tsx
│   │   ├── chat-message.tsx
│   │   ├── chat-history.tsx
│   │   └── agent-selector.tsx
│   └── layout/                  # Layout components
│       ├── header.tsx
│       ├── sidebar.tsx
│       └── footer.tsx
├── lib/
│   ├── databricks/
│   │   ├── client.ts            # Databricks SDK client
│   │   ├── sql.ts               # SQL query utilities
│   │   └── serving.ts           # Model serving utilities
│   ├── agents/
│   │   ├── cost-agent.ts        # Cost analysis agent
│   │   ├── security-agent.ts    # Security agent
│   │   ├── performance-agent.ts # Performance agent
│   │   └── orchestrator.ts      # Agent orchestrator
│   └── utils/
│       ├── format.ts            # Formatting utilities
│       └── constants.ts         # App constants
├── types/
│   ├── dashboard.ts             # Dashboard type definitions
│   ├── chat.ts                  # Chat type definitions
│   └── api.ts                   # API type definitions
├── public/
│   └── ...                      # Static assets
├── app.yaml                     # Databricks Apps configuration
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .env.example
```

---

## Databricks Apps Configuration

### app.yaml (Required for Databricks Apps)

```yaml
# Databricks Apps Configuration
# Reference: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/app-runtime

command: ['npm', 'run', 'start']

env:
  # Model Serving Endpoint for Agent Chat
  - name: SERVING_ENDPOINT_NAME
    valueFrom: serving-endpoint

  # SQL Warehouse for Data Queries
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom: sql-warehouse

  # Unity Catalog Configuration
  - name: DATABRICKS_CATALOG
    value: 'health_monitor'

  - name: DATABRICKS_SCHEMA_GOLD
    value: 'gold'

  # Application Settings
  - name: NODE_ENV
    value: 'production'

  - name: NEXT_TELEMETRY_DISABLED
    value: '1'
```

### databricks.yml (Asset Bundle Configuration)

```yaml
bundle:
  name: health-monitor-frontend

variables:
  catalog:
    description: Unity Catalog name
    default: health_monitor
  gold_schema:
    description: Gold layer schema
    default: gold
  warehouse_id:
    description: SQL Warehouse ID
    default: "your-warehouse-id"

resources:
  apps:
    health-monitor-app:
      name: "health-monitor-app"
      source_code_path: ../src/frontend_app
      description: "Databricks Health Monitor - Platform observability dashboard with AI-powered chat"
      compute_size: MEDIUM

      resources:
        # Model Serving Endpoint for Agent
        - name: "serving-endpoint"
          description: "Model serving endpoint for AI agents"
          serving_endpoint:
            name: "health-monitor-agent"
            permission: "CAN_QUERY"

        # SQL Warehouse for Data Queries
        - name: "sql-warehouse"
          description: "SQL warehouse for dashboard queries"
          sql_warehouse:
            id: ${var.warehouse_id}
            permission: "CAN_USE"

        # Optional: Genie Space
        - name: "genie-space"
          description: "Genie space for natural language queries"
          genie_space:
            id: "your-genie-space-id"
            permission: "CAN_VIEW"

targets:
  dev:
    mode: development
    default: true
    resources:
      apps:
        health-monitor-app:
          name: "health-monitor-app-dev"

  prod:
    mode: production
    resources:
      apps:
        health-monitor-app:
          name: "health-monitor-app"
```

---

## Core Implementation Patterns

### 1. Vercel AI SDK Chat Integration

**`app/api/chat/route.ts`** - Streaming Chat with Agent Tools

```typescript
import { streamText, tool } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';
import { getDatabricksClient } from '@/lib/databricks/client';

// Define agent tools for cost analysis
const costAnalysisTool = tool({
  description: 'Analyze cost data and identify trends or anomalies',
  parameters: z.object({
    timeRange: z.enum(['7d', '30d', '90d']).describe('Time range for analysis'),
    groupBy: z.enum(['workspace', 'sku', 'user']).optional(),
  }),
  execute: async ({ timeRange, groupBy }) => {
    const client = getDatabricksClient();
    const result = await client.executeStatement({
      statement: `SELECT * FROM ${process.env.DATABRICKS_CATALOG}.${process.env.DATABRICKS_SCHEMA_GOLD}.fact_usage
                  WHERE usage_date >= current_date - interval '${timeRange}'
                  ${groupBy ? `GROUP BY ${groupBy}` : ''}`,
      warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID!,
    });
    return result;
  },
});

const jobStatusTool = tool({
  description: 'Get job execution status and failure analysis',
  parameters: z.object({
    status: z.enum(['all', 'failed', 'running']).optional(),
    limit: z.number().default(10),
  }),
  execute: async ({ status, limit }) => {
    // Implementation using TVFs from Phase 3.2
  },
});

export async function POST(req: Request) {
  const { messages, agent } = await req.json();

  // Select model and tools based on agent type
  const tools = agent === 'cost' 
    ? { costAnalysis: costAnalysisTool }
    : agent === 'performance'
    ? { jobStatus: jobStatusTool }
    : { costAnalysis: costAnalysisTool, jobStatus: jobStatusTool };

  const result = streamText({
    model: openai('gpt-4-turbo'),
    system: getSystemPrompt(agent),
    messages,
    tools,
    maxSteps: 5, // Allow multi-step tool execution
  });

  return result.toDataStreamResponse();
}

function getSystemPrompt(agent: string): string {
  const prompts: Record<string, string> = {
    cost: `You are a Databricks Cost Analysis Agent. Help users understand their 
           DBU usage, identify cost optimization opportunities, and analyze spending trends.`,
    performance: `You are a Databricks Performance Agent. Help users monitor job 
                  executions, identify failures, and optimize workloads.`,
    security: `You are a Databricks Security Agent. Help users monitor audit events,
               identify anomalies, and ensure compliance.`,
    orchestrator: `You are the Databricks Health Monitor Orchestrator. Route queries
                   to specialized agents and provide comprehensive platform insights.`,
  };
  return prompts[agent] || prompts.orchestrator;
}
```

### 2. React Chat Component

**`components/chat/chat-interface.tsx`**

```typescript
'use client';

import { useChat } from 'ai/react';
import { useState } from 'react';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { AgentSelector } from './agent-selector';

type Agent = 'orchestrator' | 'cost' | 'security' | 'performance' | 'reliability' | 'data-quality' | 'mlops';

export function ChatInterface() {
  const [selectedAgent, setSelectedAgent] = useState<Agent>('orchestrator');

  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    body: { agent: selectedAgent },
  });

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4">
      {/* Agent Selector Sidebar */}
      <aside className="w-64 bg-slate-900 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-400 mb-3">Select Agent</h3>
        <AgentSelector
          selected={selectedAgent}
          onSelect={setSelectedAgent}
          agents={[
            { id: 'orchestrator', name: 'All Agents', icon: '🤖', description: 'Orchestrated responses' },
            { id: 'cost', name: 'Cost Agent', icon: '💰', description: 'Cost analysis & optimization' },
            { id: 'security', name: 'Security Agent', icon: '🔒', description: 'Security & compliance' },
            { id: 'performance', name: 'Performance Agent', icon: '⚡', description: 'Job & query performance' },
            { id: 'reliability', name: 'Reliability Agent', icon: '🎯', description: 'SLA & uptime' },
            { id: 'data-quality', name: 'Data Quality Agent', icon: '📊', description: 'DQ monitoring' },
            { id: 'mlops', name: 'MLOps Agent', icon: '🧠', description: 'ML model operations' },
          ]}
        />
        
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-slate-400 mb-3">Suggested Questions</h3>
          <SuggestedQuestions agent={selectedAgent} onSelect={(q) => handleInputChange({ target: { value: q } } as any)} />
        </div>
      </aside>

      {/* Chat Area */}
      <main className="flex-1 flex flex-col bg-slate-800 rounded-lg">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isLoading && <LoadingIndicator />}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-slate-700">
          <ChatInput
            input={input}
            onChange={handleInputChange}
            onSubmit={handleSubmit}
            isLoading={isLoading}
            placeholder={`Ask ${selectedAgent === 'orchestrator' ? 'the Health Monitor' : `the ${selectedAgent} agent`}...`}
          />
        </div>
      </main>
    </div>
  );
}
```

### 3. Dashboard Data Fetching (Server Components)

**`app/page.tsx`** - Dashboard Hub with Server Components

```typescript
import { Suspense } from 'react';
import { KPICard } from '@/components/charts/kpi-card';
import { CostTrendChart } from '@/components/charts/cost-trend-chart';
import { JobStatusChart } from '@/components/charts/job-status-chart';
import { getDashboardOverview } from '@/lib/databricks/sql';

// Server Component - fetches data on server
export default async function DashboardPage() {
  const data = await getDashboardOverview();

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-white">Databricks Health Monitor</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total DBU This Month"
          value={data.totalDbu.toLocaleString()}
          change={data.dbuChangePercent}
          trend={data.dbuTrend}
          icon="💰"
        />
        <KPICard
          title="Job Success Rate (24h)"
          value={`${data.jobSuccessRate.toFixed(1)}%`}
          change={data.jobSuccessChange}
          trend={data.jobSuccessTrend}
          icon="✅"
        />
        <KPICard
          title="Active Workspaces"
          value={data.activeWorkspaces.toString()}
          change={data.workspaceChange}
          trend="flat"
          icon="🏢"
        />
        <KPICard
          title="Security Events (24h)"
          value={data.securityEvents.toString()}
          change={data.securityEventChange}
          trend={data.securityEventTrend}
          icon="🔒"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Suspense fallback={<ChartSkeleton />}>
          <CostTrendChart />
        </Suspense>
        <Suspense fallback={<ChartSkeleton />}>
          <JobStatusChart />
        </Suspense>
      </div>

      {/* Quick Actions */}
      <QuickActions />
    </div>
  );
}
```

### 4. Databricks Client Integration

**`lib/databricks/client.ts`**

```typescript
import { DBSQLClient } from '@databricks/sql';

let client: DBSQLClient | null = null;

export function getDatabricksClient(): DBSQLClient {
  if (!client) {
    client = new DBSQLClient({
      host: process.env.DATABRICKS_HOST!,
      path: `/sql/1.0/warehouses/${process.env.DATABRICKS_WAREHOUSE_ID}`,
      // Auth handled automatically via service principal environment variables
      // DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET are auto-injected
    });
  }
  return client;
}

export async function executeQuery<T>(sql: string): Promise<T[]> {
  const client = getDatabricksClient();
  const session = await client.openSession();

  try {
    const operation = await session.executeStatement(sql, {
      runAsync: true,
      maxRows: 10000,
    });
    const result = await operation.fetchAll();
    await operation.close();
    return result as T[];
  } finally {
    await session.close();
  }
}
```

**`lib/databricks/sql.ts`** - Query Functions

```typescript
import { executeQuery } from './client';

export async function getDashboardOverview() {
  const catalog = process.env.DATABRICKS_CATALOG;
  const schema = process.env.DATABRICKS_SCHEMA_GOLD;

  // Execute multiple queries in parallel
  const [costData, jobData, securityData] = await Promise.all([
    executeQuery<CostSummary>(`
      SELECT * FROM ${catalog}.${schema}.cost_analytics_summary
      WHERE summary_date = current_date()
    `),
    executeQuery<JobSummary>(`
      SELECT * FROM ${catalog}.${schema}.job_performance_summary_24h
    `),
    executeQuery<SecuritySummary>(`
      SELECT * FROM ${catalog}.${schema}.security_events_summary_24h
    `),
  ]);

  return {
    totalDbu: costData[0]?.total_dbu ?? 0,
    dbuChangePercent: costData[0]?.dbu_change_pct ?? 0,
    dbuTrend: costData[0]?.dbu_trend ?? 'flat',
    jobSuccessRate: jobData[0]?.success_rate ?? 0,
    jobSuccessChange: jobData[0]?.success_change ?? 0,
    jobSuccessTrend: jobData[0]?.success_trend ?? 'flat',
    activeWorkspaces: jobData[0]?.active_workspaces ?? 0,
    workspaceChange: 0,
    securityEvents: securityData[0]?.event_count ?? 0,
    securityEventChange: securityData[0]?.event_change ?? 0,
    securityEventTrend: securityData[0]?.event_trend ?? 'flat',
  };
}

export async function getCostTrend(days: number = 30) {
  const catalog = process.env.DATABRICKS_CATALOG;
  const schema = process.env.DATABRICKS_SCHEMA_GOLD;

  return executeQuery<CostTrendPoint>(`
    SELECT 
      usage_date,
      SUM(total_dbu) as total_dbu,
      SUM(total_cost_usd) as total_cost
    FROM ${catalog}.${schema}.fact_usage
    WHERE usage_date >= current_date() - interval '${days}' day
    GROUP BY usage_date
    ORDER BY usage_date
  `);
}
```

---

## Page Specifications

### 1. Dashboard Hub (`app/page.tsx`)

**Purpose:** Central landing page with key metrics and navigation

**Layout:**
```
┌────────────────────────────────────────────────────────────────────────┐
│  DATABRICKS HEALTH MONITOR                            [User] [Settings]│
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Total DBU    │  │ Job Success  │  │ Active       │  │ Security     ││
│  │ This Month   │  │ Rate (24h)   │  │ Workspaces   │  │ Events (24h) ││
│  │              │  │              │  │              │  │              ││
│  │  125,432     │  │   98.5%      │  │     12       │  │     47       ││
│  │  ↑ 15%       │  │   ↓ 0.3%    │  │   ↔ 0       │  │   ↑ 12       ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                                        │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐│
│  │      Cost Trend (30 days)      │  │    Job Status Distribution     ││
│  │   📈 Line Chart                │  │   🥧 Pie Chart                 ││
│  │                                │  │                                ││
│  │                                │  │   ● Success   ● Failed         ││
│  │                                │  │   ● Running   ● Pending        ││
│  └────────────────────────────────┘  └────────────────────────────────┘│
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────│
│  │              Quick Actions                                          │
│  │                                                                     │
│  │  [💰 Cost Analysis]  [⚡ Job Monitor]  [🔒 Security]  [🤖 Ask Agent]│
│  └─────────────────────────────────────────────────────────────────────│
└────────────────────────────────────────────────────────────────────────┘
```

**Data Sources:**
- `cost_analytics` metric view
- `job_performance` metric view
- `security_events` metric view

---

### 2. Chat Interface (`app/chat/page.tsx`)

**Purpose:** Natural language interface to all specialized agents using Vercel AI SDK

**Layout:**
```
┌────────────────────────────────────────────────────────────────────────┐
│  ASK THE HEALTH MONITOR                                                │
├──────────────────────────────────────┬─────────────────────────────────┤
│                                      │                                 │
│  Agent Selection:                    │  Conversation History:          │
│  ┌────────────────────────────────┐  │                                 │
│  │ 🤖 All Agents (Orchestrator)   │  │  [User] Why did costs spike?   │
│  │ 💰 Cost Agent                  │  │                                 │
│  │ 🔒 Security Agent              │  │  [Agent] Based on my analysis...│
│  │ ⚡ Performance Agent           │  │  • DBU usage increased 45%      │
│  │ 🎯 Reliability Agent           │  │  • Jobs Compute SKU: +$2,340    │
│  │ 📊 Data Quality Agent          │  │  • Top contributor: ETL cluster │
│  │ 🧠 ML Ops Agent                │  │                                 │
│  └────────────────────────────────┘  │  [View Details] [Export]        │
│                                      │                                 │
│  Suggested Questions:                │  ─────────────────────────────  │
│  • What are top cost drivers?        │                                 │
│  • Any failed jobs today?            │  [User] Which workspace?        │
│  • Show security anomalies           │                                 │
│  • Check SLA compliance              │  [Agent] The production         │
│                                      │  workspace (ws-123) shows...    │
│                                      │                                 │
├──────────────────────────────────────┴─────────────────────────────────┤
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Ask a question...                                    [Send 📤] │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Streaming responses via Vercel AI SDK
- Agent selector (specific or orchestrator)
- Conversation history with context
- Tool calls for data queries (visible as "thinking" steps)
- Rich responses with charts/tables rendered from tool results
- Export conversation to PDF

---

### 3. Cost Center (`app/cost/page.tsx`)

**Purpose:** Detailed cost analysis and management

**Layout:**
```
┌────────────────────────────────────────────────────────────────────────┐
│  COST CENTER                                    [Export] [Set Budget]  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Filters: [Workspace ▼] [SKU ▼] [Date Range: Last 30 days ▼]          │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                      Cost Overview                                 ││
│  │                                                                    ││
│  │  Total Cost: $45,230    DBU Used: 125,432    Workspaces: 12       ││
│  │  vs Last Period: ↑15%   vs Last Period: ↑18%  Active: 10          ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────┐ │
│  │    Cost Trend                   │  │   Cost by SKU               │ │
│  │    📈 Area Chart               │  │   📊 Bar Chart              │ │
│  │                                 │  │                             │ │
│  │    [Daily] [Weekly] [Monthly]   │  │   Jobs Compute   $15,230    │ │
│  │                                 │  │   SQL Compute    $12,450    │ │
│  │                                 │  │   Storage        $ 8,120    │ │
│  └─────────────────────────────────┘  └─────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                    Cost by Workspace                               ││
│  │                                                                    ││
│  │  Rank  Workspace         DBU        Cost      % of Total  Trend   ││
│  │  ───────────────────────────────────────────────────────────────  ││
│  │   1    Production       45,230    $15,230      33.7%      ↑ 12%   ││
│  │   2    Development      32,100    $10,890      24.1%      ↓ 3%    ││
│  │   3    Analytics        28,450    $ 9,450      20.9%      ↑ 8%    ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  🚨 Cost Anomalies (ML Detection)                     [View All] ││
│  │                                                                    ││
│  │  • Tuesday: $5,230 spike in Jobs Compute (ws-production)          ││
│  │  • Thursday: Unusual ML Serving usage pattern detected            ││
│  └────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

---

### 4. Job Operations Center (`app/jobs/page.tsx`)

**Purpose:** Monitor job executions, failures, and SLA compliance

**Layout:**
```
┌────────────────────────────────────────────────────────────────────────┐
│  JOB OPERATIONS CENTER                         [Create Alert] [Export] │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Total Runs   │  │ Success Rate │  │ Failed Jobs  │  │ SLA Breaches ││
│  │   1,245      │  │   98.2%      │  │     23       │  │      5       ││
│  │   (24h)      │  │   ↓ 0.5%    │  │   ↑ 3       │  │   ↔ 0       ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                                        │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────┐ │
│  │    Job Runs Timeline            │  │   Failure Distribution      │ │
│  │    📈 Stacked Area             │  │   🥧 Pie Chart              │ │
│  │                                 │  │                             │ │
│  │    ■ Success ■ Failed ■ Running │  │   ● Config  ● Data          │ │
│  │                                 │  │   ● Timeout ● Other         │ │
│  └─────────────────────────────────┘  └─────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                    Recent Job Runs                      [Refresh] ││
│  │                                                                    ││
│  │  Status  Job Name          Start Time     Duration   Workspace    ││
│  │  ───────────────────────────────────────────────────────────────  ││
│  │  ✅      daily_etl         10:30 AM       12m 34s    production   ││
│  │  ❌      hourly_sync       10:15 AM       5m 12s     production   ││
│  │  🔄      ml_training       10:00 AM       Running    ml-workspace ││
│  │  ✅      data_quality      09:45 AM       3m 45s     analytics    ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  🔮 At-Risk Jobs (ML Prediction)                       [View All] ││
│  │                                                                    ││
│  │  • nightly_batch: 73% failure probability (historical pattern)    ││
│  │  • weekly_report: 45% failure probability (resource contention)   ││
│  └────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

---

### 5. Security Center (`app/security/page.tsx`)

**Purpose:** Monitor security events, access patterns, and compliance

**Layout:**
```
┌────────────────────────────────────────────────────────────────────────┐
│  SECURITY CENTER                               [Export Report] [Alerts]│
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Total Events │  │ Unique Users │  │ Failed Auth  │  │ Anomalies    ││
│  │   12,456     │  │     234      │  │      12      │  │      3       ││
│  │   (24h)      │  │   Active     │  │   ↑ 4       │  │   🔴 High    ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                                        │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────┐ │
│  │    Events by Service            │  │   Events by Action          │ │
│  │    📊 Horizontal Bar           │  │   🥧 Donut Chart            │ │
│  │                                 │  │                             │ │
│  │    unityCatalog    ████████    │  │   ● Read   ● Write          │ │
│  │    jobs            █████       │  │   ● Admin  ● Other          │ │
│  │    clusters        ███         │  │                             │ │
│  └─────────────────────────────────┘  └─────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  🚨 Security Alerts (ML Anomaly Detection)            [View All] ││
│  │                                                                    ││
│  │  🔴 HIGH: Unusual after-hours access from user@company.com        ││
│  │  🟡 MED:  Multiple failed authentication attempts from IP x.x.x.x ││
│  │  🟡 MED:  New admin privilege granted to service principal        ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                    Recent Audit Events                             ││
│  │                                                                    ││
│  │  Time       User            Service        Action       Status    ││
│  │  ───────────────────────────────────────────────────────────────  ││
│  │  10:32 AM   admin@...       unityCatalog   createTable  Success   ││
│  │  10:30 AM   analyst@...     jobs           runNow       Success   ││
│  │  10:28 AM   unknown         workspace      login        Failed    ││
│  └────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

---

### 6. Settings & Configuration (`app/settings/page.tsx`)

**Purpose:** Configure alerts, budgets, SLAs, and preferences

**Sections:**
- Alert Configuration
- Budget Settings
- SLA Definitions
- User Preferences
- Integration Settings

---

## Component Library

### Reusable Components

| Component | Description |
|-----------|-------------|
| `<KPICard>` | Metric display with trend indicator |
| `<TrendChart>` | Line/area chart for time series |
| `<DataTable>` | Sortable, filterable table with pagination |
| `<PieChart>` | Donut/pie chart for distributions |
| `<AlertBanner>` | Alert notification display |
| `<ChatInterface>` | Full chat interface with AI SDK integration |
| `<ChatMessage>` | Individual message with tool call rendering |
| `<AgentSelector>` | Agent selection panel |
| `<FilterBar>` | Multi-select filter controls |
| `<DateRangePicker>` | Date range selection |

### Design System

```css
/* Color Palette - Dark Theme Optimized */
:root {
  /* Databricks Brand */
  --primary: #FF3621;          /* Databricks Red */
  --primary-dark: #CC2B1A;     /* Darker variant */
  
  /* Semantic Colors */
  --success: #10B981;          /* Green */
  --warning: #F59E0B;          /* Amber */
  --error: #EF4444;            /* Red */
  --info: #3B82F6;             /* Blue */
  
  /* Backgrounds - Slate */
  --bg-primary: #0F172A;       /* slate-900 */
  --bg-secondary: #1E293B;     /* slate-800 */
  --bg-tertiary: #334155;      /* slate-700 */
  
  /* Text */
  --text-primary: #F8FAFC;     /* slate-50 */
  --text-secondary: #94A3B8;   /* slate-400 */
  --text-muted: #64748B;       /* slate-500 */
  
  /* Borders */
  --border: #334155;           /* slate-700 */
}

/* Typography - Using JetBrains Mono for code, Inter for UI */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */

/* Spacing (Tailwind scale) */
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-3: 0.75rem;  /* 12px */
--spacing-4: 1rem;     /* 16px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */

/* Border Radius */
--radius-sm: 0.25rem;
--radius-md: 0.375rem;
--radius-lg: 0.5rem;
--radius-xl: 0.75rem;
```

---

## Environment Variables

### Required Environment Variables

```bash
# Auto-injected by Databricks Apps
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_CLIENT_ID=<service-principal-client-id>
DATABRICKS_CLIENT_SECRET=<service-principal-client-secret>

# Configured via app.yaml valueFrom
DATABRICKS_WAREHOUSE_ID=<warehouse-id>
SERVING_ENDPOINT_NAME=<model-serving-endpoint>

# Application Configuration
DATABRICKS_CATALOG=health_monitor
DATABRICKS_SCHEMA_GOLD=gold

# AI SDK (if using external provider)
OPENAI_API_KEY=<from-secret>
```

---

## Deployment

### Build & Deploy Commands

```bash
# Local Development
cd src/frontend_app
npm install
npm run dev

# Build for Production
npm run build

# Validate Bundle
databricks bundle validate

# Deploy to Dev
databricks bundle deploy -t dev

# Run/Update App
databricks bundle run health-monitor-app -t dev

# Deploy to Production
databricks bundle deploy -t prod
databricks bundle run health-monitor-app -t prod
```

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy Health Monitor App

on:
  push:
    branches: [main]
    paths:
      - 'src/frontend_app/**'
  pull_request:
    paths:
      - 'src/frontend_app/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
        working-directory: src/frontend_app
      - run: npm run lint
        working-directory: src/frontend_app
      - run: npm run test
        working-directory: src/frontend_app

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: npm ci && npm run build
        working-directory: src/frontend_app
      - run: databricks bundle deploy -t prod
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }}
```

---

## Success Criteria

- [ ] All 6 pages implemented and functional
- [ ] Agent chat interface with streaming via Vercel AI SDK
- [ ] All 6+ specialized agents accessible through chat
- [ ] Real-time data updates (< 30s refresh)
- [ ] Mobile-responsive design (Tailwind breakpoints)
- [ ] SSO authentication via Databricks service principal
- [ ] Sub-second page load times (Server Components)
- [ ] Deployed to Databricks Apps
- [ ] CI/CD pipeline with automated tests
- [ ] User documentation complete

---

## References

### Databricks Apps
- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [Configure app.yaml](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/app-runtime)
- [Manage Dependencies](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/dependencies)
- [Add Resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources)
- [App Templates Repository](https://github.com/databricks/app-templates)

### Framework Documentation
- [Next.js App Router](https://nextjs.org/docs/app)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [Tailwind CSS](https://tailwindcss.com/)
- [Recharts](https://recharts.org/)

### Databricks SDK
- [@databricks/sql](https://www.npmjs.com/package/@databricks/sql)
- [Databricks SQL Driver for Node.js](https://docs.databricks.com/en/dev-tools/nodejs-sql-driver.html)
