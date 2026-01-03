# 03 - Future Architecture (Phases 4-5 Planned)

**Roadmap for Agent Framework and Frontend Application implementation.**

---

## Overview

Phases 4-5 represent **40% of the remaining project**:
- **Phase 4**: Agent Framework (Master Orchestrator + 7 Specialized Agents)
- **Phase 5**: Frontend Application (Next.js + Vercel AI SDK + Lakebase)

These phases build upon the deployed foundation (Phases 1-3) to create an **AI-powered conversational interface** with a **modern web application frontend**.

---

## Phase 4: Agent Framework

### Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT LAYER (Phase 4)                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Master Orchestrator Agent                       │  │
│  │                                                            │  │
│  │  Responsibilities:                                        │  │
│  │  • Route queries to specialized agents                    │  │
│  │  • Coordinate multi-agent responses                       │  │
│  │  • Synthesize cross-domain insights                       │  │
│  │  • Manage conversation context                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│           ┌──────────────────┼──────────────────┐               │
│           │                  │                  │               │
│           ▼                  ▼                  ▼               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │ Cost Agent   │   │ Security     │   │ Performance  │       │
│  │              │   │ Agent        │   │ Agent        │       │
│  │ • Cost       │   │              │   │              │       │
│  │   analysis   │   │ • Audit log  │   │ • Job        │       │
│  │ • Budget     │   │   analysis   │   │   monitoring │       │
│  │   tracking   │   │ • Threat     │   │ • Query opt  │       │
│  │ • Forecast   │   │   detection  │   │ • Bottleneck │       │
│  │              │   │ • Compliance │   │   analysis   │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│           │                  │                  │               │
│           ▼                  ▼                  ▼               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │ Reliability  │   │ Quality      │   │ MLOps        │       │
│  │ Agent        │   │ Agent        │   │ Agent        │       │
│  │              │   │              │   │              │       │
│  │ • SLA        │   │ • Data       │   │ • Model      │       │
│  │   tracking   │   │   validation │   │   monitoring │       │
│  │ • Incident   │   │ • Freshness  │   │ • Drift      │       │
│  │   response   │   │ • DQ metrics │   │   detection  │       │
│  │ • Uptime     │   │ • Drift      │   │ • Retraining │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Governance Agent                             │  │
│  │                                                            │  │
│  │  • Lineage tracking                                       │  │
│  │  • Access control recommendations                         │  │
│  │  • Compliance reporting                                   │  │
│  │  • Metadata quality                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Tool Integration:                                               │
│  • 50+ TVFs (parameterized queries)                             │
│  • 30+ Metric Views (semantic metadata)                         │
│  • 15 ML Models (predictions/anomalies)                         │
│  • Gold Layer (direct SQL access)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Specifications

#### 1. Master Orchestrator Agent

**Purpose:** Route queries and coordinate multiple specialized agents.

**Capabilities:**
- Intent classification (which agent(s) to use)
- Multi-agent orchestration
- Response synthesis
- Context management across conversation turns

**Example Interaction:**
```
User: "Show me the top cost drivers and any security issues from yesterday"

Master Orchestrator:
  1. Identifies need for Cost Agent + Security Agent
  2. Calls Cost Agent → get_top_cost_drivers(date='2026-01-14')
  3. Calls Security Agent → get_security_events(date='2026-01-14')
  4. Synthesizes both responses into unified answer
  
Response:
  "Here's what I found for January 14, 2026:
  
  Cost Drivers:
  • ml-workspace: $2,340 (+45% from GPU training)
  • production: $1,850 (steady)
  • analytics: $1,200 (+12%)
  
  Security Events:
  • 3 failed auth attempts from IP 192.168.1.100
  • After-hours access by user@company.com (2-4 AM)
  • No high-severity threats detected
  
  Would you like me to investigate any of these further?"
```

**Implementation:**
- Foundation LLM: GPT-4 Turbo, Claude 3.5 Sonnet, or DBRX
- Deployment: Databricks Model Serving (serverless endpoint)
- Context: 16K token window with conversation history

---

#### 2. Cost Agent

**Domain:** Cost Intelligence & Optimization

**Tools:**
- `get_daily_cost_summary(start_date, end_date)`
- `get_cost_anomalies(lookback_days)`
- `get_top_cost_drivers(date, top_n)`
- `get_workspace_cost_breakdown(workspace_id, start_date, end_date)`
- `get_sku_cost_trend(sku_name, days)`

**ML Models:**
- `cost_anomaly_detector` - Isolation Forest for spike detection
- `dbu_usage_forecaster` - Prophet for 30-day forecast
- `budget_alerter` - XGBoost for budget violation prediction

**Example Queries:**
- "What caused the cost spike yesterday?"
- "Show me the 30-day cost forecast"
- "Which workspaces are over budget?"
- "Compare this month's costs to last month"

---

#### 3. Security Agent

**Domain:** Security & Compliance Monitoring

**Tools:**
- `get_security_events(start_date, end_date, severity)`
- `get_failed_auth_attempts(hours)`
- `get_permission_changes(days)`
- `get_pii_access_logs(user, days)`
- `get_compliance_violations(type)`

**ML Models:**
- `access_anomaly_detector` - Autoencoder for unusual patterns
- `breach_risk_scorer` - Classification for threat scoring
- `user_behavior_analyzer` - LSTM for behavior profiling

**Example Queries:**
- "Show me high-severity security events from today"
- "Has user@company.com accessed PII recently?"
- "Were there any failed auth attempts overnight?"
- "What permission changes happened this week?"

---

#### 4. Performance Agent

**Domain:** Job & Query Performance

**Tools:**
- `get_failed_jobs(hours, workspace)`
- `get_slow_queries(threshold_seconds)`
- `get_job_bottlenecks(job_name)`
- `get_sla_breaches(days)`
- `get_resource_utilization(workspace)`

**ML Models:**
- `job_failure_predictor` - XGBoost for proactive detection
- `job_duration_forecaster` - Gradient Boost for runtime prediction
- `bottleneck_detector` - Isolation Forest for resource constraints

**Example Queries:**
- "Why did nightly_etl fail?"
- "Which jobs are at risk of failure?"
- "Show me the slowest queries today"
- "What's causing the bottleneck in production?"

---

#### 5. Reliability Agent

**Domain:** SLA Tracking & Incident Management

**Tools:**
- `get_sla_breaches(days)`
- `get_uptime_metrics(workspace, days)`
- `get_incident_summary(severity, days)`
- `get_service_health(service_name)`

**ML Models:**
- `uptime_predictor` - Time series forecasting
- `incident_classifier` - Classification for root cause

**Example Queries:**
- "What's our uptime for production this month?"
- "Show me SLA breaches in the past week"
- "Summarize incidents from yesterday"
- "Is there a pattern to our outages?"

---

#### 6. Quality Agent

**Domain:** Data Quality & Freshness

**Tools:**
- `get_dq_summary(schema, days)`
- `get_freshness_violations(hours)`
- `get_expectation_failures(pipeline, days)`
- `get_drift_metrics(table, baseline_date)`

**ML Models:**
- `drift_detector` - Statistical drift detection
- `freshness_predictor` - Time series forecasting

**Example Queries:**
- "What data quality issues exist?"
- "Which tables are stale?"
- "Show me DLT expectation failures"
- "Has the data distribution changed?"

---

#### 7. MLOps Agent

**Domain:** ML Model Monitoring & Operations

**Tools:**
- `get_model_performance(model_name, days)`
- `get_model_drift(model_name)`
- `get_training_history(model_name)`
- `get_inference_metrics(endpoint, days)`

**ML Models:**
- `model_drift_detector` - Distribution comparison
- `retraining_trigger` - Decision classifier

**Example Queries:**
- "How is the job_failure_predictor performing?"
- "Has the cost_anomaly_detector drifted?"
- "When was the last model retraining?"
- "Show me inference latency for all models"

---

#### 8. Governance Agent

**Domain:** Data Governance & Lineage

**Tools:**
- `get_table_lineage(table_name)`
- `get_access_grants(table_name)`
- `get_compliance_report(regulation)`
- `get_metadata_quality(schema)`

**Example Queries:**
- "Show me the lineage for fact_usage"
- "Who has access to sensitive tables?"
- "Generate a GDPR compliance report"
- "Which tables are missing descriptions?"

---

### Agent-to-Agent Communication

**Scenario:** User asks "Why are costs high and jobs failing?"

```
Master Orchestrator:
  ├─► Cost Agent: "Analyze cost spike"
  │   └─► Returns: GPU training job ($2,340)
  │
  └─► Performance Agent: "Check job failures"
      └─► Returns: ml_training job failed 3x
  
Master Orchestrator synthesizes:
  "The cost spike is from ml_training job consuming GPU compute.
   This job also failed 3 times in the past 24 hours.
   
   Recommendation: Investigate job configuration and consider
   smaller GPU instance or incremental training approach."
```

---

## Phase 5: Frontend Application

### Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND APP (Next.js 14+)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Presentation Layer                           │  │
│  │                                                            │  │
│  │  • Dashboard Hub (platform overview)                      │  │
│  │  • Chat Interface (AI agents)                             │  │
│  │  • Cost Center (DBU analysis)                             │  │
│  │  • Job Operations (job monitoring)                        │  │
│  │  • Security Center (audit events)                         │  │
│  │  • Settings (configuration)                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Backend API (Next.js API Routes)             │  │
│  │                                                            │  │
│  │  • /api/chat - Vercel AI SDK chat endpoint                │  │
│  │  • /api/dashboards - Dashboard data                       │  │
│  │  • /api/cost - Cost metrics                               │  │
│  │  • /api/jobs - Job status                                 │  │
│  │  • /api/security - Security events                        │  │
│  │  • /api/alerts - Alert configuration                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                 ┌────────────┴────────────┐                     │
│                 │                         │                     │
│                 ▼                         ▼                     │
│  ┌──────────────────────┐   ┌─────────────────────────┐       │
│  │  Databricks Data     │   │  Lakebase PostgreSQL    │       │
│  │                      │   │                         │       │
│  │  • Gold Layer        │   │  • Chat history         │       │
│  │  • TVFs              │   │  • User preferences     │       │
│  │  • Metric Views      │   │  • Alert rules          │       │
│  │  • Model Endpoints   │   │  • App state            │       │
│  └──────────────────────┘   └─────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- **Next.js 14+**: React framework with App Router
- **TypeScript 5.4+**: Type-safe development
- **Tailwind CSS 3.4+**: Utility-first styling
- **Vercel AI SDK 3.0+**: Streaming chat, tool calling
- **Recharts 2.12+**: Data visualization
- **Lucide Icons**: Icon library
- **Radix UI**: Accessible component primitives

**Backend:**
- **Next.js API Routes**: Serverless functions
- **@databricks/sql 1.8+**: SQL driver for Node.js
- **pg 8.11+**: PostgreSQL client for Lakebase
- **Zod**: Schema validation

**Deployment:**
- **Databricks Apps**: Native platform deployment
- **Docker**: Containerization
- **OAuth 2.0**: Databricks authentication

### Page Architecture

#### 1. Dashboard Hub

**Purpose:** Central landing page with high-level KPIs

**Components:**
- 4 KPI cards (DBU, Job Success, Workspaces, Security Events)
- 2 charts (Cost Trend, Job Status Distribution)
- Active Alerts list
- Quick Actions buttons

**Data Sources:**
- `get_daily_cost_summary()`
- `get_job_success_rate()`
- `get_active_alerts()`
- Gold Layer direct queries

**Update Frequency:** 30 seconds

---

#### 2. Chat Interface

**Purpose:** AI-powered conversational interface with agents

**Components:**
- Agent selector sidebar (8 agents)
- Chat message history (user + agent)
- Tool call indicators (show agent "thinking")
- Input box with send button
- Suggested questions

**Data Sources:**
- `/api/chat` → Vercel AI SDK → Agent endpoints
- Lakebase (chat history persistence)

**Features:**
- Streaming responses
- Multi-turn conversations
- Context retention (16K tokens)
- Tool call transparency
- Export conversation

---

#### 3. Cost Center

**Purpose:** Detailed cost analysis and forecasting

**Components:**
- Cost overview panel (4 metrics)
- Cost trend chart (30 days)
- Cost by SKU chart
- Cost by workspace table
- ML-powered anomaly alerts

**Data Sources:**
- `get_daily_cost_summary()`
- `get_cost_by_sku()`
- `get_workspace_cost_breakdown()`
- `cost_anomaly_detector` model

**Update Frequency:** 5 minutes

---

#### 4. Job Operations Center

**Purpose:** Monitor job executions and failures

**Components:**
- Job KPIs (runs, success rate, failures, SLA breaches)
- Job timeline chart (24h)
- Failure distribution chart
- Recent job runs table
- ML-powered at-risk jobs

**Data Sources:**
- `get_job_runs()`
- `get_failed_jobs()`
- `get_sla_breaches()`
- `job_failure_predictor` model

**Update Frequency:** 1 minute

---

#### 5. Security Center

**Purpose:** Security events and compliance monitoring

**Components:**
- Security KPIs (events, users, failed auth, anomalies)
- Events by service chart
- Events by action chart
- Security alerts (ML-powered)
- Recent audit events table

**Data Sources:**
- `get_security_events()`
- `get_failed_auth_attempts()`
- `access_anomaly_detector` model

**Update Frequency:** 30 seconds

---

#### 6. Settings

**Purpose:** Configure alerts, preferences, integrations

**Components:**
- General settings (name, timezone, theme, refresh rate)
- Alert configuration (create/edit/delete)
- User management (permissions)
- Integration settings (Slack, email, PagerDuty)

**Data Sources:**
- Lakebase (user preferences, alert rules)

---

### Data Flow

**Server Components (Default):**
```typescript
// app/page.tsx - Dashboard Hub (Server Component)
import { getDailyCostSummary } from '@/lib/databricks/tvfs'

export default async function DashboardHub() {
  const costData = await getDailyCostSummary()
  
  return (
    <div>
      <KPICard value={costData.total_cost} label="Total Cost" />
      {/* ... */}
    </div>
  )
}
```

**Client Components (Interactive):**
```typescript
// components/chat/chat-interface.tsx (Client Component)
'use client'

import { useChat } from 'ai/react'

export function ChatInterface() {
  const { messages, input, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    initialMessages: []
  })
  
  return (
    <div>
      {messages.map(msg => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      <ChatInput value={input} onSubmit={handleSubmit} />
    </div>
  )
}
```

**Streaming Chat API:**
```typescript
// app/api/chat/route.ts
import { streamText, tool } from 'ai'
import { openai } from '@ai-sdk/openai'

export async function POST(req: Request) {
  const { messages } = await req.json()
  
  const result = await streamText({
    model: openai('gpt-4-turbo'),
    messages,
    tools: {
      get_daily_cost_summary: tool({
        description: 'Get daily cost summary',
        parameters: z.object({
          start_date: z.string(),
          end_date: z.string()
        }),
        execute: async ({ start_date, end_date }) => {
          return await databricksClient.callTVF(
            'get_daily_cost_summary',
            { start_date, end_date }
          )
        }
      })
    }
  })
  
  return result.toDataStreamResponse()
}
```

---

### Lakebase Integration

**Purpose:** Store transactional app data (chat history, preferences, alert rules)

**Schema:**
```sql
-- Chat history
CREATE TABLE chat_conversations (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE chat_messages (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES chat_conversations(id),
  role VARCHAR(20), -- 'user' or 'assistant'
  content TEXT,
  tool_calls JSONB,
  created_at TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
  user_id VARCHAR(255) PRIMARY KEY,
  display_name VARCHAR(255),
  timezone VARCHAR(100),
  theme VARCHAR(20),
  refresh_rate INTEGER,
  updated_at TIMESTAMP
);

-- Alert rules
CREATE TABLE alert_rules (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255),
  name VARCHAR(255),
  query TEXT,
  threshold DECIMAL,
  enabled BOOLEAN,
  created_at TIMESTAMP
);
```

**Connection Pattern:**
```typescript
// lib/databricks/lakebase.ts
import { Pool } from 'pg'

const pool = new Pool({
  host: process.env.LAKEBASE_HOST,
  port: parseInt(process.env.LAKEBASE_PORT || '5432'),
  database: process.env.LAKEBASE_DATABASE,
  user: process.env.LAKEBASE_USER,
  password: process.env.DATABRICKS_TOKEN, // Token rotation
  ssl: { rejectUnauthorized: false }
})

export async function saveChatMessage(
  conversationId: string,
  role: string,
  content: string
) {
  await pool.query(
    'INSERT INTO chat_messages (id, conversation_id, role, content, created_at) VALUES ($1, $2, $3, $4, NOW())',
    [crypto.randomUUID(), conversationId, role, content]
  )
}
```

---

### Deployment

**Databricks Apps Configuration:**

```yaml
# app.yaml
command:
  - "npm"
  - "run"
  - "start"

env:
  - name: "NODE_ENV"
    value: "production"
  - name: "DATABRICKS_HOST"
    value: "{{ workspace.host }}"
  - name: "DATABRICKS_TOKEN"
    secret: "databricks_token"

resources:
  cpu: "2"
  memory: "4Gi"

port: 3000
```

**Asset Bundle Integration:**
```yaml
# databricks.yml
resources:
  apps:
    health_monitor_frontend:
      name: "health-monitor-frontend"
      description: "Databricks Health Monitor Frontend"
      source_code_path: "./frontend"
      config:
        app_yaml: "app.yaml"
      permissions:
        - level: CAN_USE
          group_name: users
```

---

## Implementation Timeline

### Phase 4: Agent Framework

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | Agent Infrastructure | Tool calling framework, context management |
| 3 | Master Orchestrator | Intent classification, routing |
| 4 | Cost + Security Agents | Domain-specific logic, tool integration |
| 5 | Performance + Reliability Agents | Tool integration, ML model calls |
| 6 | Quality + MLOps + Governance Agents | Complete agent catalog |
| 7 | Integration Testing | Multi-agent flows, response synthesis |
| 8 | Deployment | Model serving endpoints, monitoring |

**Total:** 8 weeks (2 months)

---

### Phase 5: Frontend Application

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | Design (Figma) | Complete UI/UX designs for 6 pages |
| 3-4 | Core Infrastructure | Next.js app, routing, design system |
| 5 | Dashboard Hub + Chat | KPI cards, charts, chat interface |
| 6 | Cost + Job Centers | Detailed cost/job pages |
| 7 | Security Center + Settings | Security page, settings |
| 8 | Lakebase Integration | Chat history, preferences |
| 9 | Agent Integration | Connect frontend to agent endpoints |
| 10 | Testing & Polish | E2E testing, performance optimization |
| 11 | Deployment | Databricks Apps deployment |
| 12 | Documentation & Training | User guides, admin documentation |

**Total:** 12 weeks (3 months)

---

## Success Criteria

### Phase 4: Agent Framework

| Metric | Target |
|--------|--------|
| **Agent Response Time** | < 5s (P95) |
| **Multi-Agent Latency** | < 8s (P95) |
| **Intent Classification Accuracy** | > 95% |
| **Tool Call Success Rate** | > 99% |
| **Context Retention** | 10+ conversation turns |
| **User Satisfaction** | > 4.5/5 rating |

### Phase 5: Frontend App

| Metric | Target |
|--------|--------|
| **Initial Load Time** | < 1.5s |
| **Time to Interactive** | < 2.5s |
| **Dashboard Refresh** | < 30s |
| **Chat Response (streaming)** | < 2s first token |
| **Mobile Responsiveness** | 100% functional |
| **Accessibility** | WCAG 2.1 AA compliant |
| **Uptime** | > 99.5% |

---

## Risk Mitigation

### Phase 4 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM Hallucinations** | High | Use tool calling exclusively, validate all outputs |
| **Agent Latency** | Medium | Optimize tool calls, implement caching |
| **Cost (LLM API)** | Medium | Use efficient prompts, local fallbacks (DBRX) |
| **Multi-Agent Complexity** | Low | Start simple, add agents incrementally |

### Phase 5 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Databricks Apps Limitations** | High | Test early, have fallback deployment (Vercel) |
| **Lakebase Token Rotation** | Medium | Implement robust retry logic |
| **Real-Time Data Sync** | Low | Acceptable 30s lag, use SWR for client updates |
| **Mobile Performance** | Low | Progressive enhancement, skeleton screens |

---

## Next Steps

### Immediate Actions

1. **Finalize Agent Architecture** (Week 1)
   - Select foundation LLM (GPT-4 Turbo vs Claude 3.5 vs DBRX)
   - Design tool calling interface
   - Define context management strategy

2. **Begin Figma Design** (Week 1-2)
   - Use [Frontend PRD](09-frontend-prd.md) as specification
   - Create design system in Figma
   - Design 6 pages (desktop, tablet, mobile)

3. **Prototype Cost Agent** (Week 2-3)
   - Implement single agent with 5 tools
   - Test tool calling and response quality
   - Validate latency and accuracy

4. **Set Up Frontend Scaffold** (Week 3-4)
   - Initialize Next.js 14+ project
   - Configure Tailwind CSS, TypeScript
   - Set up Databricks SQL client

---

## References

### Internal Documentation
- [Frontend PRD](09-frontend-prd.md) - Complete UI/UX specifications
- [Agent Framework Design](../agent-framework-design/) - Detailed agent documentation
- [Phase 4 Plan](../../plans/phase4-agent-framework.md)
- [Phase 5 Plan](../../plans/phase5-frontend-app.md)

### External Documentation
- [Vercel AI SDK](https://sdk.vercel.ai/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [Lakebase](https://docs.databricks.com/en/dev-tools/databricks-apps/lakebase.html)

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Status:** 📋 Planned (14 weeks / 3.5 months)

