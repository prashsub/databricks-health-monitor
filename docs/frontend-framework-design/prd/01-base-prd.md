# 09 - Frontend Product Requirements Document (PRD)

> **Note: Outdated Frontend Stack References**
> This document references Next.js 14+ and/or Vercel AI SDK as the frontend stack.
> The actual implementation uses **FastAPI + React/Vite** deployed as a Databricks App.
> Treat frontend-specific sections as superseded design docs; the backend architecture
> and data platform sections remain accurate.


**Document Type:** Product Requirements Document for UI/UX Design  
**Target:** Figma Design Team  
**Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Ready for Design

---

## Executive Summary

This PRD specifies the complete UI/UX requirements for the **Databricks Health Monitor Frontend Application** - a modern, AI-powered platform observability dashboard. The application provides real-time monitoring, analytics, and conversational AI interface for Databricks workspaces across cost, security, performance, reliability, data quality, and MLOps domains.

**Target Users:** Platform Engineers, Data Engineers, Security Teams, FinOps Teams, Executives

**Key Features:**
- AI-powered chat interface with 7 specialized agents
- Real-time dashboards with 200+ visualizations
- Domain-specific operational centers (Cost, Jobs, Security)
- Mobile-responsive dark-themed design
- Sub-2-second page load times

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Target Users & Personas](#target-users--personas)
3. [User Journeys](#user-journeys)
4. [Information Architecture](#information-architecture)
5. [Design System](#design-system)
6. [Page Specifications](#page-specifications)
7. [Component Library](#component-library)
8. [Interactions & Animations](#interactions--animations)
9. [Responsive Design](#responsive-design)
10. [Accessibility Requirements](#accessibility-requirements)
11. [Technical Constraints](#technical-constraints)
12. [Figma Deliverables](#figma-deliverables)

---

## Design Philosophy

### Core Principles

1. **Data Density with Clarity**
   - Display maximum information without overwhelming users
   - Progressive disclosure: summary → details on demand
   - Visual hierarchy guides attention to critical metrics

2. **AI-First Interaction**
   - Chat as primary interface for complex queries
   - Natural language over complex filters
   - Agents proactively surface insights

3. **Dark Theme Optimization**
   - Professional, eye-friendly for long sessions
   - High contrast for data visualization
   - Databricks brand alignment (red accent)

4. **Speed & Responsiveness**
   - Instant feedback on all interactions
   - Skeleton screens during loading
   - Real-time updates without page refresh

5. **Enterprise Professionalism**
   - Clean, modern aesthetic
   - Data-driven visual style
   - Trust-building through design consistency

### Design Inspiration

**Style References:**
- **Databricks SQL UI** - Enterprise data platform aesthetic
- **Linear** - Clean, fast, keyboard-friendly
- **Vercel Dashboard** - Modern metrics visualization
- **Grafana** - Data density and chart sophistication
- **Notion AI** - Conversational interface patterns

---

## Target Users & Personas

### Primary Personas

#### 1. **Platform Engineer - "Sam"**

**Profile:**
- Age: 28-40
- Role: Databricks Platform Administrator
- Goals: Keep platform healthy, optimize costs, prevent incidents
- Pain Points: Too many dashboards, reactive not proactive
- Tech Savvy: High

**Use Cases:**
- Monitor job failures and investigate root cause
- Identify cost spikes and optimize spending
- Set up alerts for critical metrics
- Track SLA compliance

**Key Screens:** Dashboard Hub, Job Operations, Chat Interface

---

#### 2. **FinOps Analyst - "Taylor"**

**Profile:**
- Age: 25-35
- Role: Cloud Cost Optimization
- Goals: Reduce DBU spend, forecast budgets, chargeback reporting
- Pain Points: Complex cost attribution, manual reporting
- Tech Savvy: Medium

**Use Cases:**
- Analyze cost trends by workspace/SKU
- Identify top cost drivers
- Generate executive cost reports
- Set budget alerts

**Key Screens:** Cost Center, Dashboard Hub, Chat Interface

---

#### 3. **Security Engineer - "Alex"**

**Profile:**
- Age: 30-45
- Role: Data Platform Security
- Goals: Monitor access patterns, detect anomalies, ensure compliance
- Pain Points: Audit log noise, delayed threat detection
- Tech Savvy: High

**Use Cases:**
- Review security events and failed auth attempts
- Investigate unusual access patterns
- Track permission changes
- Generate compliance reports

**Key Screens:** Security Center, Chat Interface, Dashboard Hub

---

#### 4. **Executive - "Morgan"**

**Profile:**
- Age: 40-60
- Role: VP Data/CTO
- Goals: High-level platform health visibility, cost control
- Pain Points: No executive summary view, too detailed
- Tech Savvy: Medium

**Use Cases:**
- View platform health at a glance
- Track month-over-month costs
- Understand major incidents
- Share metrics with leadership

**Key Screens:** Dashboard Hub, Cost Center (summary view)

---

## User Journeys

### Journey 1: Investigating Job Failures

```
Sam (Platform Engineer) receives alert: "3 critical jobs failed in production"

1. Opens Health Monitor → Dashboard Hub
   - Sees "Job Success Rate (24h): 96.2% ↓ 1.8%" KPI card in RED
   - Click: "Job Operations Center"

2. Job Operations Page
   - Scans "Recent Job Runs" table
   - Filters: Status = Failed, Workspace = production
   - Identifies 3 failed jobs: nightly_etl, hourly_sync, data_quality

3. Clicks "Ask Agent" button
   - Opens Chat Interface
   - Types: "Why did nightly_etl fail?"
   
4. Agent Response (with tool calls visible):
   - Queries job_run_timeline table
   - Shows: "Failed at Task 3: data_validation"
   - Error: "SchemaException: Column revenue_usd not found"
   - Recommendation: "Check upstream table schema changes"
   
5. Sam investigates upstream changes
   - Finds recent schema migration
   - Creates fix and re-runs job
   
6. Returns to Dashboard Hub
   - Confirms job success rate recovers
```

**Design Requirements:**
- KPI cards must show trend indicators (arrows, colors)
- Job table must support inline filtering
- Chat must show "thinking" indicators for tool calls
- Agent responses must include actionable recommendations

---

### Journey 2: Cost Spike Investigation

```
Taylor (FinOps) reviews weekly cost report: +35% DBU increase

1. Opens Health Monitor → Cost Center
   - Sees "Total DBU This Month: 145K ↑ 35%" KPI
   - Views "Cost Trend (30 days)" chart - spike visible on Day 22

2. Filters cost data
   - Date Range: Day 20-24
   - Groups by: Workspace
   - Sees: "ML Workspace" shows 3x increase
   
3. Drills into ML Workspace
   - Views "Cost by SKU" breakdown
   - Identifies: Jobs Compute GPU increased 400%
   
4. Opens Chat Interface
   - Types: "What caused the GPU compute spike in ml-workspace on March 22?"
   
5. Agent Response:
   - Queries usage and job tables
   - Shows: "New model training pipeline deployed"
   - Job: "train_llm_model" ran 12 hours on g5.12xlarge cluster
   - Cost impact: $2,340 for single job
   
6. Taylor creates budget alert
   - Settings → Alerts
   - Configures: "GPU spend > $500/day" → Notify FinOps team
```

**Design Requirements:**
- Cost charts must support date range selection
- Drill-down from chart → table → details
- Chat must correlate cost spikes with job executions
- Alert configuration must be intuitive

---

### Journey 3: Security Anomaly Detection

```
Alex (Security) sees ML alert: "Unusual access pattern detected"

1. Opens Health Monitor → Security Center
   - Sees "Anomalies: 3 🔴 High" KPI card
   - Views "Security Alerts" section
   
2. Reviews alerts:
   - Alert 1: "After-hours database access from user@company.com"
   - Alert 2: "Multiple failed auth attempts from IP x.x.x.x"
   - Alert 3: "New admin privilege granted to service principal"
   
3. Clicks Alert 1 for details
   - Shows timeline of access events
   - User accessed 5 tables between 2 AM - 4 AM
   - Tables contain PII (marked with 🔒 icon)
   
4. Opens Chat Interface
   - Types: "Show all after-hours access by user@company.com in the past 30 days"
   
5. Agent Response (with table):
   - Queries audit logs with time filters
   - Shows 12 after-hours access events
   - Pattern: Every Friday night, same tables
   - Insight: "Appears to be scheduled ETL job, not manual access"
   
6. Alex verifies with user
   - Confirms legitimate scheduled job
   - Adds exception to anomaly detection
   - Alert cleared
```

**Design Requirements:**
- Security alerts must show severity (color-coded)
- Timeline visualization for event sequences
- PII indicators on sensitive data
- Chat must support temporal queries

---

## Information Architecture

### Site Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         Health Monitor                           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Dashboard Hub│      │ Chat Interface│      │   Settings   │
└──────────────┘      └──────────────┘      └──────────────┘
        │                                           │
        │                                           ├─ User Preferences
        ├─ Cost Center                              ├─ Alert Configuration
        ├─ Job Operations                           ├─ Integration Settings
        ├─ Security Center                          └─ Team Management
        ├─ Reliability Center
        ├─ Data Quality Center
        └─ ML Ops Center
```

### Navigation Structure

**Top-Level Navigation** (Persistent across all pages):
1. Dashboard Hub (home icon)
2. Chat Interface (chat icon)
3. Domain Centers (dropdown menu)
4. Settings (gear icon)
5. User Menu (avatar)

**Domain Centers Dropdown:**
- Cost Intelligence 💰
- Job Operations ⚡
- Security & Compliance 🔒
- Reliability Management 🎯
- Data Quality 📊
- ML Operations 🧠

---

## Design System

### Color Palette

#### Brand Colors

```
Primary (Databricks Red):
  - primary-500: #FF3621
  - primary-600: #E62F1D
  - primary-700: #CC2B1A
  - primary-800: #B32717
  
Semantic Colors:
  - success-500: #10B981  (Green)
  - warning-500: #F59E0B  (Amber)
  - error-500:   #EF4444  (Red)
  - info-500:    #3B82F6  (Blue)
```

#### Dark Theme Palette

```
Backgrounds:
  - bg-primary:    #0F172A  (slate-900) - Page background
  - bg-secondary:  #1E293B  (slate-800) - Card background
  - bg-tertiary:   #334155  (slate-700) - Nested card, hover states
  - bg-quaternary: #475569  (slate-600) - Active states

Text:
  - text-primary:   #F8FAFC  (slate-50)  - Main text
  - text-secondary: #CBD5E1  (slate-300) - Secondary text
  - text-tertiary:  #94A3B8  (slate-400) - Muted text
  - text-disabled:  #64748B  (slate-500) - Disabled text

Borders:
  - border-primary:   #334155  (slate-700)
  - border-secondary: #475569  (slate-600)
  - border-focus:     #3B82F6  (blue-500)
```

#### Data Visualization Colors

```
Chart Palette (Sequential):
  - chart-1: #3B82F6  (Blue)
  - chart-2: #8B5CF6  (Purple)
  - chart-3: #EC4899  (Pink)
  - chart-4: #F59E0B  (Amber)
  - chart-5: #10B981  (Green)
  - chart-6: #06B6D4  (Cyan)
  
Gradient (for area charts):
  - gradient-start: rgba(59, 130, 246, 0.8)
  - gradient-end:   rgba(59, 130, 246, 0.1)
```

---

### Typography

#### Font Families

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

**Usage:**
- **Inter**: All UI text (headings, body, labels)
- **JetBrains Mono**: Code snippets, SQL queries, JSON, logs

#### Font Scale

```
Headings:
  - h1: 2rem (32px) / font-semibold / line-height: 1.2
  - h2: 1.5rem (24px) / font-semibold / line-height: 1.3
  - h3: 1.25rem (20px) / font-semibold / line-height: 1.4
  - h4: 1.125rem (18px) / font-medium / line-height: 1.4

Body:
  - body-large: 1rem (16px) / font-normal / line-height: 1.5
  - body: 0.875rem (14px) / font-normal / line-height: 1.5
  - body-small: 0.75rem (12px) / font-normal / line-height: 1.5

Special:
  - label: 0.875rem (14px) / font-medium / line-height: 1.4
  - caption: 0.75rem (12px) / font-normal / line-height: 1.4
  - code: 0.875rem (14px) / font-mono / line-height: 1.6
```

---

### Spacing System

**Based on 4px grid:**

```
spacing-1:  4px   (0.25rem)
spacing-2:  8px   (0.5rem)
spacing-3:  12px  (0.75rem)
spacing-4:  16px  (1rem)
spacing-5:  20px  (1.25rem)
spacing-6:  24px  (1.5rem)
spacing-8:  32px  (2rem)
spacing-10: 40px  (2.5rem)
spacing-12: 48px  (3rem)
spacing-16: 64px  (4rem)
```

**Usage Guidelines:**
- **Between sections**: spacing-8 to spacing-12
- **Between cards**: spacing-6
- **Card padding**: spacing-6
- **Form field gaps**: spacing-4
- **Icon-text gap**: spacing-2

---

### Border Radius

```
radius-sm:  0.25rem (4px)  - Pills, small badges
radius-md:  0.375rem (6px) - Buttons, inputs
radius-lg:  0.5rem (8px)   - Cards, modals
radius-xl:  0.75rem (12px) - Large cards
radius-2xl: 1rem (16px)    - Hero sections
```

---

### Elevation (Shadows)

```css
/* Subtle elevation for cards */
shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.25);

/* Card hover state */
shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3),
           0 2px 4px -1px rgba(0, 0, 0, 0.2);

/* Modal, dropdown */
shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4),
           0 4px 6px -2px rgba(0, 0, 0, 0.3);

/* Popover, tooltip */
shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.5),
           0 10px 10px -5px rgba(0, 0, 0, 0.4);
```

---

### Iconography

**Icon Library:** [Lucide Icons](https://lucide.dev/) (React-friendly, consistent style)

**Icon Sizes:**
- Small: 16px (inline with text)
- Medium: 20px (buttons, labels)
- Large: 24px (page headings)
- X-Large: 32px (empty states)

**Usage Examples:**
- `Home` - Dashboard Hub
- `MessageSquare` - Chat Interface
- `DollarSign` - Cost metrics
- `Activity` - Performance metrics
- `Shield` - Security features
- `AlertTriangle` - Warnings
- `TrendingUp` / `TrendingDown` - Trends
- `ChevronRight` - Navigation
- `X` - Close actions

---

## Page Specifications

### Global Layout

All pages share this structure:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Top Navigation                           │ 64px
│  [Logo] [Dashboard] [Chat] [Centers ▼] [Search]   [User] [⚙️]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                        Page Content Area                         │
│                     (Variable height)                            │
│                                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Top Navigation Specs:**
- Height: 64px
- Background: `bg-secondary` (#1E293B)
- Border bottom: 1px solid `border-primary` (#334155)
- Padding: 0 spacing-6 (24px)
- Sticky: Fixed at top
- Z-index: 1000

---

### Page 1: Dashboard Hub

**Purpose:** Central landing page with high-level platform health metrics

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  DATABRICKS HEALTH MONITOR                         [User] [Settings]│
├─────────────────────────────────────────────────────────────────────┤
│  Platform Health Overview                        Last updated: 2:45 PM │
│                                                                      │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────┐
│  │ 💰 Total DBU  │ │ ✅ Job Success│ │ 🏢 Active     │ │ 🔒 Security  │
│  │  This Month   │ │  Rate (24h)   │ │  Workspaces   │ │  Events (24h)│
│  │               │ │               │ │               │ │              │
│  │  125,432      │ │    98.2%      │ │      12       │ │     47       │
│  │  ↑ +15%       │ │    ↓ -0.5%   │ │    ↔ 0        │ │   ↑ +12      │
│  │  vs last month│ │    vs yesterday│ │   no change   │ │   vs yesterday
│  └───────────────┘ └───────────────┘ └───────────────┘ └──────────────┘
│                                                                      │
│  ┌────────────────────────────────────┐ ┌────────────────────────────┐
│  │     Cost Trend (Last 30 Days)      │ │   Job Status Distribution  │
│  │                                    │ │                            │
│  │     📈 Area Chart                 │ │      🥧 Donut Chart        │
│  │     Shows daily DBU consumption   │ │      Success: 1,245        │
│  │     with trend line               │ │      Failed: 23            │
│  │                                    │ │      Running: 8            │
│  │     [Daily] [Weekly] [Monthly]    │ │      Pending: 4            │
│  │                                    │ │                            │
│  └────────────────────────────────────┘ └────────────────────────────┘
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐
│  │              🚨 Active Alerts                      [View All →]  │
│  │                                                                  │
│  │  🔴 HIGH    Cost spike in production workspace (+45% vs avg)    │
│  │  🟡 MED     Job 'nightly_etl' failed 3 times in past 24h        │
│  │  🟢 INFO    New user granted admin permissions                  │
│  └─────────────────────────────────────────────────────────────────┘
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐
│  │              Quick Actions                                       │
│  │                                                                  │
│  │  [💰 Analyze Costs] [⚡ Monitor Jobs] [🔒 Review Security]      │
│  │                                                                  │
│  │  [🤖 Ask the Health Monitor]                                    │
│  └─────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────┘
```

**Component Specifications:**

#### KPI Card
```
Dimensions: 
  - Width: 280px (min), flexible
  - Height: 140px
  - Grid: 1-4 cards per row (responsive)

Structure:
  ┌─────────────────────────────┐
  │ 💰 Title                    │  12px caption, text-secondary
  │                             │  
  │ 125,432                     │  32px h1, text-primary
  │                             │
  │ ↑ +15% vs last month        │  14px body, color based on trend
  └─────────────────────────────┘
  
Background: bg-secondary (#1E293B)
Border: 1px solid border-primary (#334155)
Radius: radius-lg (8px)
Padding: spacing-6 (24px)
Shadow: shadow-sm (subtle)
Hover: shadow-md + translate-y(-2px)

Trend Indicators:
  - ↑ Green (#10B981) for positive trends (revenue, success rate)
  - ↓ Red (#EF4444) for negative trends
  - ↔ Gray (#64748B) for no change
```

#### Chart Card
```
Dimensions:
  - Width: 50% of container (2 charts per row on desktop)
  - Height: 320px
  - Min-width: 480px

Structure:
  ┌──────────────────────────────────┐
  │ Chart Title                      │  20px h3, text-primary
  │ [Filter buttons if applicable]   │  
  │                                  │
  │     [Chart visualization]        │  260px chart area
  │                                  │
  │                                  │
  │  Legend (if multi-series)        │  12px caption
  └──────────────────────────────────┘

Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-lg
Padding: spacing-6
Shadow: shadow-sm
```

#### Alert List
```
Structure:
  ┌─────────────────────────────────────────────┐
  │ 🚨 Active Alerts             [View All →]  │
  ├─────────────────────────────────────────────┤
  │                                             │
  │ 🔴 HIGH   Alert message text here...       │  Each alert: 48px height
  │ 🟡 MED    Alert message text here...       │  Hover: bg-tertiary
  │ 🟢 INFO   Alert message text here...       │  Click: Navigate to details
  └─────────────────────────────────────────────┘

Severity Icons:
  - 🔴 Critical/High: error-500 (#EF4444)
  - 🟡 Medium: warning-500 (#F59E0B)
  - 🟢 Low/Info: info-500 (#3B82F6)
```

---

### Page 2: Chat Interface

**Purpose:** AI-powered conversational interface with specialized agents

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  ASK THE HEALTH MONITOR                                 [Settings]  │
├─────────────────────┬───────────────────────────────────────────────┤
│                     │                                               │
│  Agent Selection:   │         Conversation History                  │
│                     │                                               │
│  ┌─────────────────┐│  ┌─────────────────────────────────────────┐ │
│  │ 🤖 Orchestrator ││  │ [User]                                  │ │
│  │  (All Agents)   ││  │ Why did costs spike yesterday?          │ │
│  ├─────────────────┤│  └─────────────────────────────────────────┘ │
│  │                 ││                                               │
│  │ 💰 Cost Agent   ││  ┌─────────────────────────────────────────┐ │
│  │                 ││  │ [Cost Agent] 🤖                         │ │
│  │ 🔒 Security     ││  │                                         │ │
│  │                 ││  │ I analyzed your cost data...            │ │
│  │ ⚡ Performance  ││  │                                         │ │
│  │                 ││  │ Key Findings:                           │ │
│  │ 🎯 Reliability  ││  │ • DBU usage increased 45%               │ │
│  │                 ││  │ • Jobs Compute SKU: +$2,340             │ │
│  │ 📊 Quality      ││  │ • Top contributor: ETL cluster         │ │
│  │                 ││  │                                         │ │
│  │ 🧠 ML Ops       ││  │ [View Details] [Export]                 │ │
│  └─────────────────┘│  └─────────────────────────────────────────┘ │
│                     │                                               │
│  Suggested:         │  ⏱️ Thinking... [Progress indicator]         │
│  • Top cost drivers?│                                               │
│  • Failed jobs?     │  ┌─────────────────────────────────────────┐ │
│  • Security events? │  │ [User]                                  │ │
│                     │  │ Which workspace?                        │ │
│                     │  └─────────────────────────────────────────┘ │
│                     │                                               │
├─────────────────────┴───────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Ask a question...                              [Send 📤]      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Component Specifications:**

#### Agent Selector Sidebar
```
Dimensions:
  - Width: 280px (fixed)
  - Height: 100vh - 64px (full height minus top nav)
  - Position: Fixed left

Structure:
  ┌──────────────────────┐
  │ Select Agent:        │  14px label, text-secondary
  │                      │
  │ [Agent Button 1]     │  Each: 48px height
  │ [Agent Button 2]     │  Hover: bg-tertiary
  │ [Agent Button 3]     │  Active: bg-primary-700
  │ [Agent Button 4]     │
  │ [Agent Button 5]     │
  │ [Agent Button 6]     │
  │ [Agent Button 7]     │
  │                      │
  │ ────────────────     │  Divider
  │                      │
  │ Suggested Questions: │
  │ • Question 1         │  Each: clickable, text-info
  │ • Question 2         │  Click: Populate input
  │ • Question 3         │
  └──────────────────────┘

Background: bg-secondary
Border-right: 1px solid border-primary
Padding: spacing-6
```

#### Agent Button
```
Structure:
  ┌────────────────────────────┐
  │ 💰  Cost Agent             │  Icon + Label
  │     Cost analysis & opt... │  Description (muted)
  └────────────────────────────┘

States:
  - Default: bg-secondary, text-primary
  - Hover: bg-tertiary, cursor-pointer
  - Active: bg-primary-700, text-white, border-primary-500
  - Disabled: opacity-50, cursor-not-allowed

Height: 64px
Padding: spacing-4
Radius: radius-md
Transition: all 200ms
```

#### Chat Message (User)
```
Structure:
  ┌───────────────────────────────┐
  │ [User Avatar] User            │  12px caption
  │ Why did costs spike?          │  14px body
  │                               │
  │ 2:45 PM                       │  10px timestamp, text-tertiary
  └───────────────────────────────┘

Alignment: Right
Background: bg-tertiary (#334155)
Max-width: 80%
Padding: spacing-4
Radius: radius-lg
Margin-bottom: spacing-4
```

#### Chat Message (Agent)
```
Structure:
  ┌────────────────────────────────────┐
  │ [Agent Icon] Cost Agent 🤖         │  12px caption + emoji
  │                                    │
  │ I analyzed your cost data...       │  14px body
  │                                    │
  │ Key Findings:                      │  Formatted content:
  │ • DBU usage increased 45%          │  - Bullet lists
  │ • Jobs Compute: +$2,340            │  - Inline code
  │ • Top: ETL cluster                 │  - Tables
  │                                    │  - Charts (if applicable)
  │ [View Details] [Export]            │  Action buttons
  │                                    │
  │ 2:46 PM                            │  10px timestamp
  └────────────────────────────────────┘

Alignment: Left
Background: bg-secondary (#1E293B)
Border: 1px solid border-primary
Max-width: 80%
Padding: spacing-6
Radius: radius-lg
Margin-bottom: spacing-4
Shadow: shadow-sm
```

#### Tool Call Indicator (Agent "thinking")
```
Structure:
  ┌────────────────────────────────────┐
  │ [Agent Icon] Cost Agent 🤖         │
  │                                    │
  │ ⏱️ Analyzing cost data...          │  Animated dots
  │                                    │
  │ 🔍 Querying fact_usage table       │  Step-by-step indicators
  │ ✓  Found 1,234 records             │  Show completed steps
  │ 🔍 Calculating trends...           │  Current step
  └────────────────────────────────────┘

Background: bg-secondary
Border: 1px solid info-500 (blue, animated pulse)
Opacity: 0.9
Animation: Pulse border every 2s
```

#### Chat Input Box
```
Structure:
  ┌────────────────────────────────────────────┐
  │ Ask a question...                  [📤]    │
  └────────────────────────────────────────────┘

Dimensions:
  - Height: 56px (comfortable typing)
  - Width: 100% of chat area
  - Position: Fixed at bottom

States:
  - Default: border-primary, bg-secondary
  - Focus: border-info-500, shadow-md
  - Disabled: opacity-50 (while agent responding)

Features:
  - Auto-resize textarea (up to 200px height)
  - Keyboard shortcut: Cmd/Ctrl + Enter to send
  - Character count if > 80% of limit
  - Send button disabled if empty
```

---

### Page 3: Cost Center

**Purpose:** Detailed cost analysis and management

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  COST CENTER                                [Export] [Set Budget]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Filters: [Workspace ▼] [SKU ▼] [Date Range: Last 30 days ▼]      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Cost Overview                               │ │
│  │                                                                │ │
│  │  Total Cost     DBU Used      Workspaces   Avg Daily Cost     │ │
│  │  $45,230        125,432       12           $1,508             │ │
│  │  ↑ +15%         ↑ +18%        → 0          ↑ +14%            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐│
│  │   Cost Trend (30 days)       │  │   Cost by SKU                ││
│  │                              │  │                              ││
│  │   📈 Area Chart             │  │   📊 Horizontal Bar Chart    ││
│  │                              │  │                              ││
│  │   [Daily] [Weekly] [Monthly] │  │   Jobs Compute  ████ $15.2K ││
│  │                              │  │   SQL Compute   ███  $12.5K ││
│  │   Legend:                    │  │   Storage       ██   $8.1K  ││
│  │   ── DBU Used                │  │   ML Serving    █    $5.4K  ││
│  │   ── Target Budget           │  │   Data Transfer █    $4.0K  ││
│  └──────────────────────────────┘  └──────────────────────────────┘│
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │               Cost by Workspace                    [Export CSV]│ │
│  │                                                                │ │
│  │  Rank  Workspace      DBU       Cost      % Total    Trend    │ │
│  │  ──────────────────────────────────────────────────────────   │ │
│  │   1    production    45,230   $15,230     33.7%    ↑ +12%    │ │
│  │   2    development   32,100   $10,890     24.1%    ↓ -3%     │ │
│  │   3    analytics     28,450   $ 9,450     20.9%    ↑ +8%     │ │
│  │   4    ml-workspace  15,670   $ 5,340     11.8%    ↑ +35%    │ │
│  │   5    staging       12,340   $ 4,200      9.3%    → 0%      │ │
│  │   ...                                                         │ │
│  │                                                                │ │
│  │  [< Previous] Page 1 of 3 [Next >]                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  🚨 Cost Anomalies (ML Detection)                 [View All →]│ │
│  │                                                                │ │
│  │  • Tuesday: $5,230 spike in Jobs Compute (production)         │ │
│  │  • Thursday: Unusual ML Serving pattern detected              │ │
│  │  • Budget alert: On track to exceed $50K monthly target       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Component Specifications:**

#### Filter Bar
```
Structure:
  ┌──────────────────────────────────────────────────────────────┐
  │ Filters: [Dropdown 1 ▼] [Dropdown 2 ▼] [Date Range ▼] [🔍]  │
  └──────────────────────────────────────────────────────────────┘

Height: 56px
Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-lg
Padding: spacing-4
Gap between filters: spacing-3

Each Dropdown:
  - Height: 40px
  - Min-width: 180px
  - Background: bg-tertiary
  - Hover: bg-quaternary
  - Active: border-info-500
```

#### Cost Overview Panel
```
Structure:
  ┌────────────────────────────────────────────────────┐
  │  Total Cost    DBU Used    Workspaces   Avg Daily │
  │  $45,230       125,432     12           $1,508    │
  │  ↑ +15%        ↑ +18%      → 0          ↑ +14%   │
  └────────────────────────────────────────────────────┘

Layout: 4 columns, equal width
Each metric:
  - Label: 12px caption, text-secondary
  - Value: 24px h2, text-primary
  - Trend: 14px body, color-coded

Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-lg
Padding: spacing-6
Height: 120px
```

#### Data Table
```
Structure:
  ┌────────────────────────────────────────────────────────┐
  │  Column 1  Column 2  Column 3  Column 4  Column 5     │  Header
  │  ───────────────────────────────────────────────────   │  Divider
  │  Row 1 data...                                         │  48px height
  │  Row 2 data...                                         │  Hover: bg-tertiary
  │  Row 3 data...                                         │  Click: Drill-down
  │  ...                                                   │
  │                                                        │
  │  [< Previous] Page 1 of 3 [Next >]                    │  Pagination
  └────────────────────────────────────────────────────────┘

Header:
  - Background: bg-tertiary
  - Text: 12px caption, text-secondary, font-medium
  - Height: 40px
  - Padding: spacing-4
  - Sortable columns: Show sort icon on hover

Row:
  - Height: 48px
  - Padding: spacing-4
  - Border-bottom: 1px solid border-primary
  - Hover: bg-tertiary, cursor-pointer
  - Selected: border-left: 3px solid info-500

Cell alignment:
  - Text: Left
  - Numbers: Right
  - Icons/Status: Center
```

---

### Page 4: Job Operations Center

**Purpose:** Monitor job executions, failures, and performance

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  JOB OPERATIONS CENTER                     [Create Alert] [Export]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Runs(24h)│  │ Success  │  │ Failed   │  │ SLA      │            │
│  │  1,245   │  │  98.2%   │  │   23     │  │ Breaches │            │
│  │  ↑ +120  │  │  ↓ -0.5% │  │  ↑ +3   │  │    5     │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐│
│  │  Job Runs Timeline (24h)     │  │  Failure Distribution        ││
│  │                              │  │                              ││
│  │  📈 Stacked Area Chart      │  │  🥧 Donut Chart              ││
│  │                              │  │                              ││
│  │  ■ Success ■ Failed ■ Running│  │  • Config Error    35%      ││
│  │                              │  │  • Data Issue      28%      ││
│  │  Hourly breakdown showing    │  │  • Timeout         20%      ││
│  │  job execution patterns      │  │  • Resource        12%      ││
│  │                              │  │  • Other            5%      ││
│  └──────────────────────────────┘  └──────────────────────────────┘│
│                                                                      │
│  Filters: [Status: All ▼] [Workspace ▼] [Date Range ▼] [🔍 Search] │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Recent Job Runs                        [Refresh]  │ │
│  │                                                                │ │
│  │  Status  Job Name        Start Time  Duration  Workspace      │ │
│  │  ─────────────────────────────────────────────────────────    │ │
│  │  ✅      daily_etl       10:30 AM    12m 34s   production    │ │
│  │  ❌      hourly_sync     10:15 AM    5m 12s    production    │ │
│  │  🔄      ml_training     10:00 AM    Running   ml-workspace  │ │
│  │  ✅      data_quality    09:45 AM    3m 45s    analytics     │ │
│  │  ⏸️      weekly_report   09:30 AM    Pending   production    │ │
│  │  ...                                                          │ │
│  │                                                                │ │
│  │  [< Previous] Page 1 of 24 [Next >]                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  🔮 At-Risk Jobs (ML Prediction)                  [View All →]│ │
│  │                                                                │ │
│  │  • nightly_batch: 73% failure probability (historical pattern)│ │
│  │  • weekly_report: 45% failure probability (resource conflict) │ │
│  │  • data_sync: 38% failure probability (data quality issues)   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Component Specifications:**

#### Status Icon + Text
```
Status Mapping:
  - ✅ Success:  success-500 (#10B981)
  - ❌ Failed:   error-500 (#EF4444)
  - 🔄 Running:  info-500 (#3B82F6) + spin animation
  - ⏸️ Pending:  warning-500 (#F59E0B)
  - ⏹️ Cancelled: text-tertiary (#94A3B8)

Display:
  - Icon size: 20px
  - Icon + Text gap: spacing-2
  - Text: 14px body, color matches icon
```

#### Duration Display
```
Format:
  - < 1 min: "34s"
  - < 1 hour: "12m 34s"
  - ≥ 1 hour: "2h 15m"
  - Running: "Running" (with animated dots)

Color coding (for duration column):
  - < Expected: text-success
  - Within 10% of expected: text-primary
  - > 110% of expected: text-warning
  - > 150% of expected: text-error
```

---

### Page 5: Security Center

**Purpose:** Monitor security events, access patterns, compliance

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  SECURITY CENTER                           [Export Report] [Alerts] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Events   │  │ Users    │  │ Failed   │  │ Anomalies│            │
│  │ (24h)    │  │ Active   │  │ Auth     │  │          │            │
│  │ 12,456   │  │  234     │  │   12     │  │  🔴 3    │            │
│  │ ↑ +1.2K  │  │  → 0     │  │  ↑ +4   │  │  High    │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐│
│  │  Events by Service           │  │  Events by Action            ││
│  │                              │  │                              ││
│  │  📊 Horizontal Bar Chart    │  │  🥧 Donut Chart              ││
│  │                              │  │                              ││
│  │  unityCatalog   ████████    │  │  • Read        45%          ││
│  │  jobs           █████       │  │  • Write       28%          ││
│  │  clusters       ███         │  │  • Admin       15%          ││
│  │  notebooks      ██          │  │  • Delete       8%          ││
│  │  sql            █           │  │  • Other        4%          ││
│  └──────────────────────────────┘  └──────────────────────────────┘│
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  🚨 Security Alerts (ML Anomaly Detection)        [View All →]│ │
│  │                                                                │ │
│  │  🔴 HIGH  After-hours access from user@company.com (2-4 AM)   │ │
│  │  🟡 MED   Multiple failed auth from IP 192.168.1.100 (x12)    │ │
│  │  🟡 MED   New admin privilege granted to service principal    │ │
│  │  🟢 INFO  Unusual query pattern detected in production        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  Filters: [Service ▼] [Action ▼] [User ▼] [Date Range ▼] [🔍]     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Recent Audit Events                               │ │
│  │                                                                │ │
│  │  Time     User           Service        Action      Status    │ │
│  │  ───────────────────────────────────────────────────────────  │ │
│  │  10:32 AM admin@co.com   unityCatalog   createTable Success  │ │
│  │  10:30 AM analyst@co.com jobs           runNow      Success  │ │
│  │  10:28 AM unknown        workspace      login       Failed   │ │
│  │  10:25 AM user@co.com    notebooks      read        Success  │ │
│  │  ...                                                          │ │
│  │                                                                │ │
│  │  [< Previous] Page 1 of 156 [Next >]                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Component Specifications:**

#### Alert Card
```
Structure:
  ┌──────────────────────────────────────────────────────────────┐
  │ 🔴 HIGH  Alert message text here...               [View →]   │
  └──────────────────────────────────────────────────────────────┘

Severity Badge:
  - 🔴 Critical/High: bg-error-500, text-white
  - 🟡 Medium: bg-warning-500, text-slate-900
  - 🟢 Low/Info: bg-info-500, text-white
  - Badge size: 64px width, 24px height
  - Font: 10px caption, font-semibold

Alert States:
  - New: border-left: 4px solid severity-color
  - Acknowledged: opacity-70
  - Resolved: strikethrough text
```

---

### Page 6: Settings

**Purpose:** Configure alerts, preferences, integrations

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  SETTINGS                                           [Save] [Cancel] │
├───────────────┬─────────────────────────────────────────────────────┤
│               │                                                     │
│  [General]    │  General Settings                                   │
│  [Alerts]     │                                                     │
│  [Users]      │  ┌─────────────────────────────────────────────┐   │
│  [Integrations│  │ Display Name                                │   │
│  [About]      │  │ [Health Monitor Dashboard______________]    │   │
│               │  │                                             │   │
│               │  │ Time Zone                                   │   │
│               │  │ [America/New_York ▼]                        │   │
│               │  │                                             │   │
│               │  │ Theme                                       │   │
│               │  │ ● Dark  ○ Light  ○ Auto                    │   │
│               │  │                                             │   │
│               │  │ Dashboard Refresh Rate                      │   │
│               │  │ [30 seconds ▼]                              │   │
│               │  └─────────────────────────────────────────────┘   │
│               │                                                     │
└───────────────┴─────────────────────────────────────────────────────┘
```

**Component Specifications:**

#### Settings Sidebar
```
Structure:
  ┌──────────────┐
  │ [General]    │  Each: 48px height
  │ [Alerts]     │  Active: bg-primary-700
  │ [Users]      │  Hover: bg-tertiary
  │ [Integrations│
  │ [About]      │
  └──────────────┘

Width: 200px (fixed)
Background: bg-secondary
Border-right: 1px solid border-primary
```

#### Form Field
```
Structure:
  ┌────────────────────────────────┐
  │ Label                          │  12px caption, text-secondary
  │ [Input field_______________]   │  40px height
  │ Help text if applicable        │  11px caption, text-tertiary
  └────────────────────────────────┘

Input States:
  - Default: border-primary, bg-secondary
  - Hover: border-secondary
  - Focus: border-info-500, shadow-md
  - Error: border-error-500, text-error below
  - Disabled: opacity-50
```

---

## Component Library

### Buttons

#### Primary Button
```css
Background: primary-500 (#FF3621)
Text: white
Hover: primary-600, scale(1.02)
Active: primary-700, scale(0.98)
Disabled: opacity-50

Sizes:
  - Small: height 32px, padding 0 12px, font 14px
  - Medium: height 40px, padding 0 16px, font 14px
  - Large: height 48px, padding 0 24px, font 16px

Radius: radius-md (6px)
Transition: all 200ms
```

#### Secondary Button
```css
Background: transparent
Border: 1px solid border-primary
Text: text-primary
Hover: bg-tertiary
Active: bg-quaternary

(Same sizes as Primary)
```

#### Ghost Button
```css
Background: transparent
Border: none
Text: text-secondary
Hover: text-primary, bg-tertiary
Active: bg-quaternary

(Same sizes as Primary)
```

#### Icon Button
```css
Size: 40px × 40px square
Background: transparent
Icon: 20px, text-secondary
Hover: bg-tertiary, icon text-primary
Active: bg-quaternary
Radius: radius-md

With tooltip on hover (200ms delay)
```

---

### Inputs

#### Text Input
```css
Height: 40px
Padding: 0 spacing-4
Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-md

States:
  - Placeholder: text-tertiary
  - Focus: border-info-500, shadow-md
  - Error: border-error-500
  - Disabled: opacity-50, cursor-not-allowed

Font: 14px body
```

#### Select Dropdown
```css
Height: 40px
Padding: 0 spacing-4
Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-md

Dropdown Menu:
  - Background: bg-secondary
  - Shadow: shadow-xl
  - Max-height: 320px (scrollable)
  - Option height: 40px
  - Option hover: bg-tertiary
  - Option selected: bg-primary-700

Icon: ChevronDown (16px, text-secondary)
```

#### Search Input
```css
Height: 40px
Padding-left: 40px (space for icon)
Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-md

Icon: Search (20px) at left, text-tertiary
Clear button: X icon at right (when text present)

Focus: border-info-500
```

---

### Cards

#### Standard Card
```css
Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-lg (8px)
Padding: spacing-6 (24px)
Shadow: shadow-sm

Hover (if interactive):
  - Shadow: shadow-md
  - Transform: translateY(-2px)
  - Cursor: pointer

Transition: all 200ms
```

#### Outlined Card
```css
Background: transparent
Border: 2px solid border-primary
Radius: radius-lg
Padding: spacing-6

(No hover effects unless interactive)
```

---

### Charts

#### Color Scheme
```css
chart-colors: [
  '#3B82F6',  // Blue
  '#8B5CF6',  // Purple
  '#EC4899',  // Pink
  '#F59E0B',  // Amber
  '#10B981',  // Green
  '#06B6D4',  // Cyan
  '#F43F5E',  // Rose
  '#8B5CF6',  // Violet
]

Use sequentially for multi-series charts
```

#### Chart Container
```css
Background: bg-secondary
Border: 1px solid border-primary
Radius: radius-lg
Padding: spacing-6
Min-height: 320px

Title: 20px h3, text-primary
Legend: 12px caption, text-secondary
Axis labels: 11px caption, text-tertiary
Grid lines: border-primary, 1px dashed
```

#### Tooltip
```css
Background: bg-tertiary
Border: 1px solid border-secondary
Radius: radius-md
Padding: spacing-3
Shadow: shadow-lg

Font: 12px caption
Max-width: 240px
Animation: Fade in 100ms
```

---

### Modals

```css
Overlay:
  - Background: rgba(15, 23, 42, 0.8)  // bg-primary with 80% opacity
  - Z-index: 2000
  - Animation: Fade in 200ms

Modal:
  - Background: bg-secondary
  - Border: 1px solid border-primary
  - Radius: radius-xl (12px)
  - Shadow: shadow-xl
  - Max-width: 640px (medium), 896px (large)
  - Animation: Scale in + fade in 200ms

Header:
  - Padding: spacing-6
  - Border-bottom: 1px solid border-primary
  - Title: 20px h3, text-primary
  - Close button: Top-right, icon-button

Body:
  - Padding: spacing-6
  - Max-height: 60vh (scrollable if needed)

Footer:
  - Padding: spacing-6
  - Border-top: 1px solid border-primary
  - Buttons: Right-aligned, gap spacing-3
```

---

## Interactions & Animations

### Hover States

All interactive elements:
```css
transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);

Buttons:
  - Scale: 1.02
  - Background: Darker shade
  - Cursor: pointer

Cards (clickable):
  - Transform: translateY(-2px)
  - Shadow: Increase by one level
  - Cursor: pointer

Links:
  - Color: info-500
  - Text-decoration: underline
  - Cursor: pointer
```

### Loading States

#### Skeleton Screens
```
Replace content with skeleton placeholders during load:

Card skeleton:
  ┌────────────────────────────┐
  │ ████████ (title)           │
  │ ████ (subtitle)            │
  │                            │
  │ ██████████████ (content)   │
  │ ████████ (content)         │
  │ ████████████ (content)     │
  └────────────────────────────┘

Animation: Shimmer effect (pulse 2s infinite)
Background: Linear gradient with lighter stripe moving left to right
```

#### Spinner
```
Icon: Loader2 (lucide)
Size: 24px (inline), 48px (full-page)
Color: primary-500
Animation: Spin 1s linear infinite
```

#### Progress Bar
```css
Height: 4px
Background: bg-tertiary
Fill: primary-500 (animated left to right)
Radius: 2px

Indeterminate: Animated stripe moving infinitely
Determinate: Fill width based on percentage
```

### Page Transitions

```css
Enter:
  - Opacity: 0 → 1
  - Transform: translateY(10px) → translateY(0)
  - Duration: 300ms
  - Easing: ease-out

Exit:
  - Opacity: 1 → 0
  - Duration: 200ms
  - Easing: ease-in

(Use Framer Motion or CSS transitions)
```

### Micro-interactions

#### KPI Card Trend Animation
```
When KPI updates:
  1. Number: Count-up animation from old to new (500ms)
  2. Trend indicator: Scale up from 0.8 to 1 with bounce (300ms)
  3. Background: Subtle flash of success/error color (500ms fade out)
```

#### Button Click Ripple
```
Material design ripple effect:
  1. Create circle at click point
  2. Expand from 0 to button size (400ms)
  3. Fade out (opacity 1 → 0)
  4. Color: white with 20% opacity
```

#### Toast Notifications
```
Position: Top-right, 24px from edges
Stack: Multiple toasts stack vertically

Animation:
  - Enter: Slide in from right + fade in (300ms)
  - Exit: Slide out to right + fade out (200ms)
  - Auto-dismiss: After 5s (or on click)

Types:
  - Success: border-left success-500, icon CheckCircle
  - Error: border-left error-500, icon XCircle
  - Warning: border-left warning-500, icon AlertTriangle
  - Info: border-left info-500, icon Info
```

---

## Responsive Design

### Breakpoints

```css
xs: 0px      // Mobile portrait
sm: 640px    // Mobile landscape
md: 768px    // Tablet portrait
lg: 1024px   // Tablet landscape / Small laptop
xl: 1280px   // Desktop
2xl: 1536px  // Large desktop
```

### Layout Adaptations

#### Dashboard Hub

**Desktop (≥ 1024px):**
- KPI Cards: 4 per row
- Charts: 2 per row
- Sidebars: Visible

**Tablet (768px - 1023px):**
- KPI Cards: 2 per row
- Charts: 1 per row (full width)
- Sidebars: Collapsible

**Mobile (< 768px):**
- KPI Cards: 1 per row
- Charts: 1 per row
- Navigation: Bottom tab bar
- Sidebars: Hidden (drawer on demand)

#### Chat Interface

**Desktop:**
- Sidebar: 280px fixed left
- Chat: Remaining width

**Tablet:**
- Sidebar: Collapsible drawer (slide in from left)
- Chat: Full width when sidebar hidden

**Mobile:**
- Sidebar: Full-screen overlay (slide in from bottom)
- Chat: Full width
- Input: Fixed at bottom with safe area inset

#### Data Tables

**Desktop:**
- All columns visible
- Horizontal scroll if needed

**Tablet:**
- Hide less important columns
- Show full table in landscape
- Show summary cards in portrait

**Mobile:**
- Card-based layout (not table)
- Each row becomes a card
- Stack vertically
- Swipe actions (left: delete, right: details)

### Touch Optimization

```css
Mobile adjustments:
  - Minimum tap target: 44px × 44px
  - Button height: 48px (vs 40px desktop)
  - Increased padding: spacing-5 (vs spacing-4)
  - Larger font: 16px base (vs 14px)
  - Remove hover states, use active states
  - Add haptic feedback (via navigator.vibrate)
```

---

## Accessibility Requirements

### WCAG 2.1 Level AA Compliance

#### Color Contrast

All text must meet contrast ratios:
- **Normal text (< 18px)**: 4.5:1 minimum
- **Large text (≥ 18px)**: 3:1 minimum
- **UI components**: 3:1 minimum

Verified combinations:
- `text-primary` (#F8FAFC) on `bg-primary` (#0F172A): **15.3:1** ✅
- `primary-500` (#FF3621) on `bg-secondary` (#1E293B): **5.2:1** ✅
- `success-500` (#10B981) on `bg-secondary`: **4.8:1** ✅

#### Keyboard Navigation

All interactive elements must be keyboard accessible:

**Tab Order:**
1. Top navigation (left to right)
2. Main content (top to bottom, left to right)
3. Sidebars (if present)
4. Footer

**Keyboard Shortcuts:**
- `Tab`: Next element
- `Shift + Tab`: Previous element
- `Enter`: Activate button/link
- `Space`: Toggle checkbox/radio, activate button
- `Escape`: Close modal/dropdown
- `Arrow keys`: Navigate within dropdown/menu
- `Cmd/Ctrl + K`: Open global search
- `Cmd/Ctrl + /`: Open chat interface

**Focus Indicators:**
```css
:focus-visible {
  outline: 2px solid info-500;
  outline-offset: 2px;
}
```

#### Screen Reader Support

**ARIA Labels:**
- All icons: `aria-label` or `aria-labelledby`
- All form inputs: Associated `<label>` with `for` attribute
- All charts: `aria-label` describing the chart
- All interactive elements: Descriptive `aria-label`

**ARIA Live Regions:**
```html
<!-- Toast notifications -->
<div role="status" aria-live="polite" aria-atomic="true">
  Cost spike detected in production workspace
</div>

<!-- Loading states -->
<div role="status" aria-live="polite">
  Loading dashboard data...
</div>

<!-- Agent responses -->
<div role="log" aria-live="polite" aria-atomic="false">
  <!-- Chat messages appear here -->
</div>
```

**Landmark Regions:**
- `<header role="banner">` - Top navigation
- `<main role="main">` - Primary content
- `<aside role="complementary">` - Sidebars
- `<nav role="navigation">` - Navigation menus
- `<footer role="contentinfo">` - Footer

#### Alternative Text

All images and icons:
```html
<!-- Decorative icons -->
<svg aria-hidden="true">...</svg>

<!-- Informative icons -->
<svg aria-label="Cost trending upward">...</svg>

<!-- Images -->
<img src="..." alt="Descriptive text explaining the image content">

<!-- Charts (use figcaption) -->
<figure role="img" aria-labelledby="chart-title">
  <figcaption id="chart-title">
    Cost trend for the past 30 days showing a 15% increase
  </figcaption>
  <!-- Chart visualization -->
</figure>
```

---

## Technical Constraints

### Performance Budgets

| Metric | Target | Maximum |
|--------|--------|---------|
| **Initial Load** | < 1.5s | 2s |
| **Time to Interactive** | < 2.5s | 3s |
| **First Contentful Paint** | < 1s | 1.5s |
| **Largest Contentful Paint** | < 1.5s | 2s |
| **Bundle Size** | < 250KB | 300KB (gzipped) |
| **API Response Time** | < 500ms | 1s |
| **Chart Render Time** | < 300ms | 500ms |

### Browser Support

| Browser | Version |
|---------|---------|
| Chrome | Last 2 versions |
| Firefox | Last 2 versions |
| Safari | Last 2 versions |
| Edge | Last 2 versions |

**No support for:**
- Internet Explorer
- Opera Mini
- UC Browser

### Framework Constraints

**Next.js 14+ Patterns:**
- Use Server Components by default
- Client Components only when needed (interactivity)
- Parallel data fetching with `Promise.all()`
- Streaming with React Suspense
- Route Groups for layout organization

**Vercel AI SDK:**
- `useChat` hook for chat interface
- Streaming responses with `streamText`
- Tool calling for agent actions
- Conversation history management

**React Patterns:**
- Functional components only (no classes)
- Custom hooks for reusable logic
- Context API for global state (minimal)
- SWR for client-side data fetching

---

## Figma Deliverables

### Required Figma Files

#### 1. Design System File
**Content:**
- Color palette (all variants)
- Typography scale with examples
- Spacing system documentation
- Component library (all components)
- Icon library (all used icons)
- Chart templates
- Animation documentation

**Organization:**
- Page 1: Brand & Colors
- Page 2: Typography
- Page 3: Components (Atoms)
- Page 4: Components (Molecules)
- Page 5: Components (Organisms)
- Page 6: Charts & Data Viz
- Page 7: Patterns & Templates

---

#### 2. Desktop Designs (1920×1080)
**Pages:**
- Dashboard Hub
- Chat Interface
- Cost Center
- Job Operations Center
- Security Center
- Data Quality Center (if needed)
- ML Ops Center (if needed)
- Settings

**States per page:**
- Empty state
- Loading state (with skeletons)
- Populated state (happy path)
- Error state
- Hover states (for interactive elements)
- Modal overlays (if applicable)

---

#### 3. Tablet Designs (768×1024)
**Pages:**
- Dashboard Hub
- Chat Interface
- Cost Center
- Job Operations Center
- Security Center

**Show:**
- Responsive layout adaptations
- Collapsible sidebars
- Touch-optimized spacing

---

#### 4. Mobile Designs (375×812 iPhone)
**Pages:**
- Dashboard Hub
- Chat Interface
- Cost Center (summary view)
- Job Operations (summary view)

**Show:**
- Bottom tab navigation
- Card-based layouts
- Drawer navigations
- Mobile-optimized charts

---

#### 5. Interaction Prototypes
**Required Flows:**
1. **Cost Spike Investigation**
   - Dashboard Hub → Cost Center
   - Filter selection
   - Drill-down into anomaly
   - Open chat for analysis

2. **Job Failure Investigation**
   - Dashboard Hub → Job Operations
   - Filter failed jobs
   - Click job for details
   - Ask agent for root cause

3. **Security Alert Review**
   - Dashboard Hub (see alert)
   - Security Center
   - Review event details
   - Acknowledge alert

4. **Agent Chat Interaction**
   - Open chat interface
   - Select agent
   - Type question
   - See streaming response with tool calls
   - View results (table/chart)

**Prototype Features:**
- Click interactions
- Page transitions
- Modal open/close
- Dropdown menus
- Hover states
- Loading states

---

### Component Specifications

Each component in Figma should include:

**Variants:**
- Default state
- Hover state
- Active/Pressed state
- Focus state (with visible outline)
- Disabled state
- Error state (if applicable)

**Properties:**
- Size variants (Small, Medium, Large where applicable)
- Type variants (Primary, Secondary, Ghost for buttons)
- Content variants (With icon, Without icon, Icon only)

**Documentation:**
- Component name
- Usage guidelines
- Props/variants explanation
- Do's and Don'ts

**Auto Layout:**
- All components use Auto Layout
- Proper padding and gap values
- Responsive sizing (hug/fill)
- Min/max constraints

---

### Export Specifications

**Assets to Export:**

1. **Icons** (as SVG)
   - 16px, 20px, 24px, 32px sizes
   - Monochrome (inherits color)
   - Optimized paths

2. **Illustrations** (as SVG/PNG)
   - Empty states
   - Error states
   - Loading states

3. **Logos** (as SVG/PNG)
   - Databricks logo
   - Health Monitor wordmark
   - Favicon variants

**Export Settings:**
- SVG: Outline stroke, simplify paths
- PNG: 1x, 2x, 3x (for retina)
- Format: RGB color space

---

### Handoff Requirements

**Developer Handoff Package:**

1. **Figma Link** with view access
2. **Design Specs** (this document)
3. **Asset Export** (zipped folder)
4. **Prototype Links** (for each flow)
5. **Design Tokens** (JSON format):
   ```json
   {
     "colors": {
       "primary-500": "#FF3621",
       "bg-primary": "#0F172A",
       ...
     },
     "typography": {
       "h1": {
         "size": "32px",
         "weight": 600,
         "lineHeight": 1.2
       },
       ...
     },
     "spacing": {
       "1": "4px",
       "2": "8px",
       ...
     }
   }
   ```

---

## Success Criteria

### Design Quality Metrics

- [ ] All pages designed for 3 breakpoints (desktop, tablet, mobile)
- [ ] All interactive states documented (hover, active, focus, disabled)
- [ ] All components use Auto Layout with proper constraints
- [ ] Color contrast verified for WCAG AA compliance
- [ ] Typography scale consistently applied
- [ ] Spacing system used throughout (no arbitrary values)
- [ ] Interaction prototypes demonstrate key user flows
- [ ] Empty, loading, and error states designed
- [ ] Mobile designs optimized for touch (44px min tap targets)
- [ ] Dark theme optimized for readability

### User Experience Metrics

- [ ] < 3 clicks to reach any page from Dashboard
- [ ] < 2 seconds perceived load time (with skeletons)
- [ ] All critical information visible without scrolling (above fold)
- [ ] Clear visual hierarchy guides attention
- [ ] Consistent navigation patterns across pages
- [ ] Intuitive filter and search mechanisms
- [ ] Obvious call-to-action buttons
- [ ] Helpful empty states with actions
- [ ] Informative error messages with solutions

---

## References

### Design Inspiration
- [Databricks SQL UI](https://docs.databricks.com/sql/)
- [Linear](https://linear.app/)
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Grafana](https://grafana.com/)

### Design Systems
- [Tailwind CSS](https://tailwindcss.com/)
- [Radix UI](https://www.radix-ui.com/)
- [Shadcn/ui](https://ui.shadcn.com/)

### Icon Libraries
- [Lucide Icons](https://lucide.dev/)

### Typography
- [Inter Font](https://rsms.me/inter/)
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/)

### Accessibility
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

---

**Document Version:** 1.0  
**For Figma Design Team**  
**Questions?** Contact: Engineering Team

---

## Appendix: Quick Reference

### Color Quick Reference
```
Backgrounds: #0F172A → #1E293B → #334155 → #475569
Text: #F8FAFC → #CBD5E1 → #94A3B8 → #64748B
Primary: #FF3621
Success: #10B981
Warning: #F59E0B
Error: #EF4444
Info: #3B82F6
```

### Spacing Quick Reference
```
XS: 4px    SM: 8px    MD: 12px   LG: 16px
XL: 24px   2XL: 32px  3XL: 48px  4XL: 64px
```

### Component Sizes Quick Reference
```
Buttons:   SM: 32px   MD: 40px   LG: 48px
Icons:     SM: 16px   MD: 20px   LG: 24px   XL: 32px
Inputs:    Height: 40px
Cards:     Min-height: 140px (KPI), 320px (Charts)
```
