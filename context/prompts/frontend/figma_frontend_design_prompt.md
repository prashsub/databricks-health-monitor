# Figma Frontend Design Prompt: Databricks Health Monitoring Platform

**Project:** Platform Health Monitor  
**Type:** Enterprise Platform Observability Dashboard  
**Tech Stack:** Next.js 14, React 18, TypeScript, Databricks Apps, Lakeview AI/BI  
**Target Users:** Platform Engineers, Data Analysts, Security Teams, ML Engineers  
**Based On:** Production Databricks Lakeview Dashboard Patterns + Mosaic AI Agent Integration

---

## 🎯 Project Overview

Design a **production-grade Databricks App** for comprehensive platform health monitoring and observability. The app provides real-time analytics, AI-powered insights, and proactive alerting across 5 domains: Cost, Performance, Security, Reliability, and Governance.

**Key Features:**
- **7 Main Pages** - Domain-specific dashboards with 6-column grid layout
- **23 Metric Views** - Semantic layer for natural language queries
- **23 Table-Valued Functions** - Parameterized analytics for complex queries
- **20 Lakehouse Monitoring Tables** - 335 custom metrics with drift detection
- **5 Specialized AI Agents** - Cost, Performance, Security, Reliability, Data Quality
- **Multi-Workspace Scoping** - Filter by workspace, date range, resource type
- **Real-Time Alerting** - Threshold, percentage, anomaly, and trend-based alerts

**Architecture Foundation:**
```
System Tables (35 Bronze) 
       ↓ 
Gold Layer (38 tables: 23 dims + 12 facts + 3 alerts)
       ├── Metric Views (23 views for semantic layer)
       ├── Table-Valued Functions (23 TVFs for parameterized queries)
       ├── Lakehouse Monitoring (335 custom metrics across 20 tables)
       └── ML Models (7 models in UC registry)
       ↓
AI Agents (5 specialized agents) + Dashboards (7 Lakeview AI/BI)
       ↓
Databricks App Frontend (React/Next.js)
```

**Design Philosophy:**
- **Data-Dense but Scannable** - Users monitor 300+ metrics across 5 domains
- **Action-Oriented** - Every insight has a clear next step (Create Alert, Optimize, Investigate)
- **Databricks-Native** - Follows official Lakeview dashboard patterns and color palette
- **AI-First** - Natural language queries via Genie alongside traditional dashboards
- **Production-Ready** - Based on real Databricks dashboard implementations

---

## 👥 User Personas

### 1. Platform Engineer (Primary)
**Goals:** Monitor platform health, detect anomalies, optimize costs  
**Pain Points:** Alert fatigue, context switching, manual troubleshooting  
**Needs:** Quick anomaly detection, root cause analysis, proactive alerts

### 2. Data Analyst (Secondary)
**Goals:** Query platform metrics, understand usage patterns  
**Pain Points:** Complex queries, waiting for data team  
**Needs:** Self-service analytics, natural language queries

### 3. Security Team (Secondary)
**Goals:** Audit access, detect security risks, token management  
**Pain Points:** Manual compliance reporting, delayed anomaly detection  
**Needs:** Real-time security monitoring, automated compliance reports

### 4. ML Engineer (Tertiary)
**Goals:** Monitor model serving, track experiment performance  
**Pain Points:** Fragmented tooling, no unified view  
**Needs:** Centralized ML metrics, serving performance tracking

---

## 🎨 Design System Requirements

### Color Palette

**⚠️ CRITICAL: Use Official Databricks Lakeview Color Palette**

This palette is extracted from production Databricks Lakeview dashboards and ensures consistency with the Databricks platform experience.

**Canvas & Widget Colors:**
```
Canvas Background:
  - Light Mode: #F7F9FA (off-white for reduced eye strain)
  - Dark Mode:  #0B0E11 (deep blue-black)

Widget Background:
  - Light Mode: #FFFFFF (pure white cards)
  - Dark Mode:  #1A1D21 (dark gray cards)

Widget Borders:
  - Light Mode: #E0E4E8 (subtle gray)
  - Dark Mode:  #2A2E33 (medium gray)

Font Colors:
  - Light Mode: #11171C (near-black for readability)
  - Dark Mode:  #E8ECF0 (off-white)

Selection/Highlight:
  - Light Mode: #077A9D (teal blue)
  - Dark Mode:  #8ACAE7 (light teal)
```

**Visualization Colors (10-color palette for charts):**
```
Primary Colors:
  1. #077A9D (Databricks Teal)     - Primary metric, main series
  2. #00A972 (Success Green)        - Positive trends, SLO met
  3. #FFAB00 (Amber Warning)        - Approaching threshold
  4. #FF3621 (Critical Red)         - Alerts, failures, SLO breach
  5. #8BCAE7 (Light Blue)           - Secondary metric

Extended Colors:
  6. #99DDB4 (Light Green)          - Historical baseline
  7. #FCA4A1 (Light Red)            - Anomalies, degradation
  8. #AB4057 (Maroon)               - Severe issues
  9. #6B4FBB (Purple)               - ML predictions, forecasts
  10. #BF7080 (Rose)                - Tertiary metric

Usage Pattern:
  - Use colors 1-5 for primary data series
  - Use colors 6-10 for supporting series
  - Always assign colors consistently (Cost = Teal, Success Rate = Green)
```

**Semantic Status Colors:**
```
Health Scores & SLO Gauges:
  - 90-100: #00A972 (Success Green) - Meeting targets
  - 70-89:  #FFAB00 (Amber)         - At risk
  - 50-69:  #FF9800 (Orange)        - Warning
  - 0-49:   #FF3621 (Critical Red)  - Failing

Alert Severity:
  - Critical: #FF3621 (Red)    - Immediate action required
  - High:     #FF9800 (Orange) - Urgent attention
  - Medium:   #FFAB00 (Amber)  - Monitor closely
  - Low:      #077A9D (Teal)   - Informational
```

### Typography

**Font Family:** Inter (fallback: system-ui, -apple-system)

```
Headings:
  - H1: 32px / 600 weight / 40px line-height (page titles)
  - H2: 24px / 600 weight / 32px line-height (section headers)
  - H3: 18px / 600 weight / 24px line-height (card titles)
  - H4: 16px / 600 weight / 22px line-height (subsection headers)

Body:
  - Large: 16px / 400 weight / 24px line-height (descriptions)
  - Regular: 14px / 400 weight / 20px line-height (default text)
  - Small: 12px / 400 weight / 18px line-height (labels, metadata)
  - Tiny: 10px / 400 weight / 14px line-height (captions)

Monospace:
  - Code: 14px / 400 weight / Fira Code (SQL queries, identifiers)
```

### Spacing Scale

```
4px:  xs  (tight padding, icon spacing)
8px:  sm  (compact spacing)
12px: md  (standard spacing)
16px: lg  (comfortable spacing)
24px: xl  (section spacing)
32px: 2xl (page margins)
48px: 3xl (major sections)
```

### Border Radius

```
2px:  Sharp (data tables)
4px:  Subtle (inputs, cards)
8px:  Standard (buttons, containers)
12px: Rounded (chips, badges)
16px: Soft (modals, major cards)
```

### Shadows

```
Elevation 1: 0 1px 2px rgba(0,0,0,0.05)  (cards)
Elevation 2: 0 4px 6px rgba(0,0,0,0.07)  (hover cards)
Elevation 3: 0 10px 15px rgba(0,0,0,0.1) (modals)
Elevation 4: 0 20px 25px rgba(0,0,0,0.15) (dropdowns)
```

---

## 🏗️ Databricks-Specific Architecture Context

### Data Layer Integration

**The frontend integrates with 4 data layers:**

#### 1. Metric Views (Semantic Layer)
**Purpose:** Simplified queries with business-friendly names  
**Access Pattern:** `MEASURE(\`Total Cost\`)` syntax  
**Example:**
```sql
SELECT 
  workspace_name,
  MEASURE(`Total Cost`) as cost,
  MEASURE(`Success Rate %`) as success_rate
FROM observability.gold.cost_performance_metrics
WHERE date >= CURRENT_DATE() - INTERVAL 30 DAYS;
```

**UI Integration:** Power KPI counters, trend charts, and agent queries

#### 2. Table-Valued Functions (Parameterized Analytics)
**Purpose:** Complex queries with user-provided parameters  
**Access Pattern:** `SELECT * FROM get_function(param1, param2)`  
**Example:**
```sql
SELECT * FROM observability.gold.get_top_workspaces_by_cost(
  '2025-10-01',  -- start_date
  '2025-11-01',  -- end_date
  10             -- top_n
);
```

**UI Integration:** Power drill-down tables, filtered charts, agent deep-dives

#### 3. Lakehouse Monitoring Tables (Time Series Metrics)
**Purpose:** Automatic drift detection, custom business KPIs  
**Access Pattern:** Query `*_profile_metrics` and `*_drift_metrics` tables  
**Example:**
```sql
-- 335 custom metrics across 20 fact tables
SELECT 
  window.start as date,
  total_daily_cost,
  unique_workspaces,
  avg_cost_per_workspace,
  cost_drift_pct  -- Automatic anomaly detection
FROM observability.gold_monitoring.fact_cost_daily_profile_metrics
WHERE window.start >= CURRENT_DATE() - INTERVAL 30 DAYS;
```

**UI Integration:** Anomaly alerts, trend analysis, drift detection charts

#### 4. Direct Gold Table Queries
**Purpose:** Raw dimensional data for custom aggregations  
**Access Pattern:** Traditional SQL with JOINs  
**Example:**
```sql
SELECT 
  w.workspace_name,
  SUM(f.cost_amount) as total_cost
FROM observability.gold.fact_cost_daily f
JOIN observability.gold.dim_workspace w 
  ON f.workspace_key = w.workspace_key 
  AND w.is_current = true  -- SCD Type 2 filter
GROUP BY w.workspace_name;
```

**UI Integration:** Custom aggregations, exploratory analysis

### Dashboard Layout System (Lakeview 6-Column Grid)

**All Databricks Lakeview dashboards use a 6-column grid system:**

```
┌──────┬──────┬──────┬──────┬──────┬──────┐
│  1   │  2   │  3   │  4   │  5   │  6   │  ← Column indices (x: 0-5)
├──────┴──────┴──────┴──────┴──────┴──────┤
│  Widget positions defined by:             │
│  - x (column start: 0-5)                  │
│  - y (row start: 0, 2, 8, 14...)          │
│  - width (columns to span: 1-6)           │
│  - height (rows to span: 2, 4, 6, 8...)   │
└───────────────────────────────────────────┘
```

**Standard Layouts:**

```
KPI Row (6 counters):
┌──────┬──────┬──────┬──────┬──────┬──────┐
│ KPI1 │ KPI2 │ KPI3 │ KPI4 │ KPI5 │ KPI6 │  ← Each: width=1, height=2
└──────┴──────┴──────┴──────┴──────┴──────┘

Two Charts Side-by-Side:
┌─────────────────┬─────────────────┐
│   Chart A       │   Chart B       │  ← Each: width=3, height=6
│   (Trend)       │   (Breakdown)   │
└─────────────────┴─────────────────┘

Full-Width Chart:
┌─────────────────────────────────────────┐
│         Large Trend Chart               │  ← width=6, height=6
└─────────────────────────────────────────┘

Full-Width Table:
┌─────────────────────────────────────────┐
│    Detailed Data Table (50 rows)        │  ← width=6, height=8
└─────────────────────────────────────────┘

Heatmap + Legend:
┌──────────────────────────┬──────────────┐
│   Heatmap                │   Legend     │  ← Heatmap: width=4, Legend: width=2
│   (Hour × Warehouse)     │   (Filters)  │
└──────────────────────────┴──────────────┘
```

**Y-Position Rules:**
- Start at y=0
- Increment by widget height (KPI=2, Chart=6, Table=6-8)
- Example sequence: y=0, y=2, y=8, y=14, y=22...

### Widget Type Specifications (Lakeview Standard)

**Version Requirements (CRITICAL):**
- **KPI Counters:** Version 2 (NO `period` field)
- **Charts:** Version 3 (bar, line, pie, area, scatter)
- **Tables:** Version 1 (with column specifications)
- **Filters:** Version 2 (single-select, multi-select, date range)

**Standard Widget Sizes:**
```
KPI Counter:   width=1, height=2
Small Chart:   width=2, height=4
Medium Chart:  width=3, height=6
Large Chart:   width=4-6, height=6-8
Detail Table:  width=6, height=6-12
Filter Widget: width=2, height=2
Text/Markdown: width=2-6, height=2-4
```

---

## 🎯 Project Overview (Enhanced)

Design a production-grade **Databricks App** for comprehensive platform health monitoring and observability. The app provides real-time analytics, AI-powered insights, and proactive alerting across 5 domains: Cost, Performance, Security, Reliability, and Governance.

**Data Scale:**
- **35 Bronze System Tables** → **38 Gold Tables** (23 dimensions + 12 facts + 3 alerts)
- **23 Metric Views** - Semantic layer with 423 dimensions + measures
- **23 Table-Valued Functions** - Parameterized analytics
- **335 Custom Metrics** - Lakehouse Monitoring across 20 tables
- **7 ML Models** - Forecasting, anomaly detection, risk scoring

**User Workflows:**
1. **Monitor** - Check health scores, active alerts, recent incidents
2. **Investigate** - Drill into cost spikes, runtime anomalies, security risks
3. **Forecast** - ML-powered cost/capacity predictions
4. **Alert** - Configure thresholds, test alerts, manage notifications
5. **Chat** - Natural language queries via AI agents
6. **Optimize** - Right-sizing, query optimization, governance improvements

**Design Philosophy:**
- **Data-Dense but Scannable** - Users need to monitor dozens of metrics quickly
- **Action-Oriented** - Every insight should have a clear next step
- **Databricks-Native** - Follows official Lakeview patterns, color palette, grid system
- **AI-Integrated** - Natural language queries alongside traditional dashboards
- **Production-Ready** - Based on real Databricks dashboard implementations

---

## 📊 Real Dashboard Query Patterns (Production Examples)

**These patterns are extracted from production Databricks Lakeview dashboards and should inform the UI design:**

### Pattern 1: Cost Analysis with Billing Joins
```sql
-- Standard cost calculation pattern (used in 8/8 cost dashboards)
SELECT
  u.workspace_id,
  u.usage_metadata.job_id,
  SUM(u.usage_quantity * lp.pricing.default) as list_cost
FROM system.billing.usage u
INNER JOIN system.billing.list_prices lp 
  ON u.cloud = lp.cloud 
  AND u.sku_name = lp.sku_name
  AND u.usage_start_time >= lp.price_start_time
  AND (u.usage_end_time <= lp.price_end_time OR lp.price_end_time IS NULL)
WHERE u.sku_name LIKE '%JOBS%'
GROUP BY u.workspace_id, u.usage_metadata.job_id;
```

**UI Implication:** KPI counters show "Total Cost" from this pattern

### Pattern 2: Period-over-Period Growth (Week-over-Week)
```sql
-- 7d vs 14d comparison (most common pattern)
SELECT
  workspace_id,
  SUM(CASE WHEN usage_date BETWEEN date_add(current_date(), -8) AND date_add(current_date(), -1) 
      THEN list_cost ELSE 0 END) AS last_7_day,
  SUM(CASE WHEN usage_date BETWEEN date_add(current_date(), -15) AND date_add(current_date(), -8) 
      THEN list_cost ELSE 0 END) AS last_14_day,
  try_divide((last_7_day - last_14_day), last_14_day) * 100 AS growth_pct
FROM billing_usage
GROUP BY workspace_id;
```

**UI Implication:** Trend arrows and percentage badges show growth_pct values

### Pattern 3: Job Retry & Repair Time Analysis
```sql
-- Calculate MTTR for failed jobs (reliability metric)
WITH repaired_runs AS (
  SELECT workspace_id, job_id, run_id, COUNT(*) as retry_count
  FROM system.lakeflow.job_run_timeline
  WHERE result_state IS NOT NULL
  GROUP BY workspace_id, job_id, run_id
  HAVING retry_count > 1
)
SELECT 
  job_id,
  retry_count - 1 as repairs,
  CAST(MAX(period_end_time) - MIN(period_start_time) AS LONG) as repair_time_seconds
FROM repaired_runs
JOIN system.lakeflow.job_run_timeline USING (workspace_id, job_id, run_id)
GROUP BY job_id, retry_count;
```

**UI Implication:** Reliability dashboard shows "Repairs" and "MTTR" columns

### Pattern 4: Cluster Utilization for Right-Sizing
```sql
-- CPU/Memory utilization for savings calculation
SELECT 
  cluster_id,
  AVG(cpu_user_percent + cpu_system_percent) as avg_cpu_pct,
  AVG(mem_used_percent) as avg_mem_pct,
  job_cost * (1 - (avg_cpu_pct / 100)) / 2.0 as potential_savings
FROM system.compute.node_timeline
JOIN billing_usage ON /* cluster join */
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND avg_cpu_pct < 50  -- Underutilized
GROUP BY cluster_id
ORDER BY potential_savings DESC;
```

**UI Implication:** Optimization recommendations show $ savings with utilization %

### Pattern 5: Stale Dataset Detection (Governance)
```sql
-- Jobs producing unused tables (waste detection)
WITH producers AS (
  SELECT 
    entity_id as job_id, 
    target_table_full_name
  FROM system.access.table_lineage
  WHERE entity_type = 'JOB' 
    AND event_date > CURRENT_DATE() - INTERVAL 30 DAYS
),
consumers AS (
  SELECT DISTINCT source_table_full_name
  FROM system.access.table_lineage
  WHERE event_date > CURRENT_DATE() - INTERVAL 30 DAYS
)
SELECT 
  p.job_id,
  COUNT(p.target_table_full_name) as unused_tables,
  SUM(job_cost) as wasted_cost
FROM producers p
LEFT JOIN consumers c ON p.target_table_full_name = c.source_table_full_name
WHERE c.source_table_full_name IS NULL  -- Not consumed
GROUP BY p.job_id
ORDER BY wasted_cost DESC;
```

**UI Implication:** Governance dashboard shows "Unused Tables" and "Wasted Cost"

---

### Global Layout Structure

```
┌─────────────────────────────────────────────┐
│  [Logo] Platform Health Monitor     [User]  │ ← Top Navigation (64px)
├─────────────────────────────────────────────┤
│ Side │                                      │
│ Nav  │     Main Content Area                │
│ 240px│     (Scrollable)                     │
│      │                                      │
│ [≡]  │                                      │
│ Home │                                      │
│ Cost │                                      │
│ Perf │                                      │
│ Sec  │                                      │
│ Rely │                                      │
│ Alert│                                      │
│ Chat │                                      │
└──────┴──────────────────────────────────────┘
```

### Top Navigation Bar (64px height)

**Left Section:**
- Logo + App Name (Platform Health Monitor)
- Workspace Selector (dropdown, current: "Production")

**Right Section:**
- Time Range Picker (Last 7d / 30d / Custom)
- Refresh Button (auto-refresh indicator)
- Notifications (bell icon with badge)
- User Avatar + Dropdown (Settings, Help, Logout)

### Side Navigation (240px width, collapsible to 64px)

**Navigation Items:**
```
Icon  Label                Badge
────  ─────────────────── ─────
📊    Overview            
💰    Cost Monitor        ⚠️ 3
⚡    Performance         
🔒    Security            🔴 5
✅    Reliability         
🔔    Alert Management    
💬    Agent Chat          
```

**Visual States:**
- Default: Gray-500 icon + text
- Hover: Gray-700 with background Gray-100
- Active: Primary-700 with background Primary-50, left border Primary-500 (4px)
- Badge: Red for critical, Orange for warnings, Gray for info

---

## 📄 Page Designs (7 Pages)

## Page 1: Overview Dashboard

**Purpose:** Single-pane-of-glass health summary across all domains

### Layout Grid (3 columns, 24px gutters)

```
┌─────────────────────────────────────────────────────────────┐
│ Health Score Overview                                       │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│ │   85     │ │   92     │ │   78     │ │   88     │      │
│ │  Cost    │ │ Security │ │ Perform. │ │ Reliabil.│      │
│ │  ↑ 5%    │ │  ↓ 2%    │ │  ↑ 12%   │ │  → 0%    │      │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌─────────────────────────────┐  │
│ │ Active Alerts       │  │ Cost Trend (30d)            │  │
│ │ 🔴 5 Critical       │  │ [Line Chart]                │  │
│ │ 🟠 3 High           │  │ $45.2K → $52.8K (+17%)      │  │
│ │ 🟡 12 Medium        │  │                             │  │
│ └─────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ Recent Incidents                                            │
│ [Timeline visualization with MTTR indicators]               │
└─────────────────────────────────────────────────────────────┘
```

### Health Score Card Component

**Design Specs:**
```
Card: 
  - Size: 280px × 180px
  - Background: White
  - Border: 1px solid Gray-200
  - Border Radius: 12px
  - Padding: 24px
  - Shadow: Elevation 1
  - Hover: Shadow Elevation 2 + Border Primary-200

Content:
  - Score Number: 72px / 700 weight / Center aligned
  - Domain Label: 14px / 500 weight / Gray-700
  - Trend Indicator: 
    - Arrow icon (↑↓→) + percentage
    - Green (↑ positive), Red (↓ negative), Gray (→ neutral)
    - 12px / 600 weight
  - Mini Sparkline: 60px width × 30px height (last 7 days)

Color Mapping:
  - 90-100: Success Green
  - 70-89:  Primary Blue
  - 50-69:  Warning Yellow
  - 0-49:   Error Red
```

### Active Alerts Panel

**Design:**
```
Card: 360px × 320px, White background

Header:
  - "Active Alerts" (16px / 600 weight)
  - Filter dropdown (All / Cost / Security / Performance)
  - Time: "Last updated: 2 min ago" (12px / Gray-500)

Alert Items (stacked):
┌──────────────────────────────────────┐
│ 🔴 Workspace X cost spike +42%       │
│    2 min ago • Cost Alert            │
├──────────────────────────────────────┤
│ 🟠 Job runtime anomaly: ETL_daily    │
│    15 min ago • Reliability Alert    │
└──────────────────────────────────────┘

Each Item:
  - Status icon: 16px circle (colored)
  - Title: 14px / 600 weight / 1 line (truncate)
  - Metadata: 12px / Gray-500 / 1 line
  - Hover: Background Gray-50, cursor pointer
  - Click: Navigate to alert detail
```

### Quick Actions (Bottom Right FAB)

```
Floating Action Button:
  - Size: 56px × 56px
  - Background: Primary-500
  - Icon: Plus (white)
  - Shadow: Elevation 3
  - Hover: Background Primary-700 + Scale 1.05

Action Menu (opens on click):
  - Create Alert
  - Chat with Agent
  - Export Report
  - Schedule Review
```

---

## Page 2: Cost Monitor

**Purpose:** Cost analysis, forecasting, spike detection, optimization

**Data Sources:**
- Metric View: `cost_performance_metrics` (23 dimensions, 18 measures)
- TVFs: `get_top_workspaces_by_cost()`, `get_cost_anomalies()`, `get_serverless_vs_provisioned_split()`
- Monitoring: `fact_cost_daily_profile_metrics` (25 custom metrics + drift detection)
- ML Model: `cost_forecasting_model` (30-day horizon predictions)

### Layout (6-Column Grid)

```
Row 1: KPI Row (y=0, height=2)
┌──────┬──────┬──────┬──────┬──────┬──────┐
│Total │Usage │ Work-│ SKUs │ Avg  │WoW   │
│Cost  │(DBUs)│spaces│Active│$/WS  │Change│
│$52.8K│156K  │  12  │  8   │$4.4K │ ↑17% │
└──────┴──────┴──────┴──────┴──────┴──────┘

Row 2: Charts (y=2, height=6)
┌────────────────────────┬───────────────────────┐
│ Cost Trend (30d)       │ SKU Breakdown         │
│ [Line Chart]           │ [Pie Chart]           │
│ - Actual (Teal)        │ - Jobs: 60%           │
│ - Forecast (Purple)    │ - SQL: 25%            │
│ - Budget (Red dashed)  │ - All-Purpose: 10%    │
│ - Anomalies (Red dots) │ - ML: 5%              │
└────────────────────────┴───────────────────────┘

Row 3: Cost Spike Detection (y=8, height=4) - CONDITIONAL
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Cost Spike Detected                                      │
│ Workspace: Production | Date: Nov 22 | Spike: +42% WoW     │
│ Root Cause: Job "ETL_daily" runtime 3.2x normal (data vol) │
│ Potential Savings: Optimize query, add partitioning         │
│ [View Details] [Create Alert] [Optimize Job]                │
└─────────────────────────────────────────────────────────────┘

Row 4: Top Cost Drivers Table (y=12, height=8)
┌─────────────────────────────────────────────────────────────┐
│ Workspace  │ Job/WH    │ SKU      │ Cost   │ Usage │ Growth│
│ Production │ ETL_daily │ Jobs     │ $12.5K │ 450h  │ ↑22% │
│ Production │ Analytics │ SQL WH   │ $8.9K  │ 280h  │ ↓ 5% │
│ Staging    │ ML_train  │ Jobs GPU │ $6.2K  │ 120h  │ ↑89% │
│ ...        │ ...       │ ...      │ ...    │ ...   │ ...  │
└─────────────────────────────────────────────────────────────┘

Row 5: Serverless vs Provisioned Split (y=20, height=4)
┌────────────────────────┬───────────────────────┐
│ Compute Type Split     │ Right-Sizing Opps     │
│ [Gauge Chart]          │ [Bar Chart]           │
│ Serverless: 75%        │ 5 jobs: $8.2K savings │
│ Provisioned: 25%       │ via downsizing        │
└────────────────────────┴───────────────────────┘
```

### Agent Integration Sidebar (Right, 360px)

```
┌─────────────────────────────────┐
│ 💬 Cost Agent                   │
│                                 │
│ Suggested Questions:            │
│ • Why did cost spike this week? │
│ • Forecast next 30 days         │
│ • Compare to last month         │
│ • Show me wasted spend          │
│ • Top 10 expensive jobs         │
│                                 │
│ [Ask a question...]             │
└─────────────────────────────────┘
```

### Cost Trend Chart Specifications

**Chart Type:** Multi-series line chart (Lakeview v3 encoding)

**Data Source:**
```sql
-- From Metric View with MEASURE() function
SELECT 
  date,
  MEASURE(`Total Cost`) as daily_cost,
  MEASURE(`7-Day Moving Avg`) as moving_avg_7d,
  MEASURE(`Forecast (30d)`) as forecast_cost,
  MEASURE(`Budget`) as budget_amount,
  CASE 
    WHEN MEASURE(`Cost Drift %`) > 20 THEN true 
    ELSE false 
  END as is_anomaly
FROM observability.gold.cost_performance_metrics
WHERE date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND (workspace_name = :workspace_filter OR :workspace_filter = 'All')
GROUP BY date
ORDER BY date;
```

**Chart Configuration:**
```
Widget Type: line-chart (version 3)
Size: width=6 (full width), height=6
Position: x=0, y=2

X-Axis (Temporal):
  - Field: date
  - Scale: temporal
  - Format: "MMM d" (Nov 1, Nov 2...)
  - Grid: Dashed lines every 7 days (weekly markers)

Y-Axis (Quantitative):
  - Field: daily_cost
  - Scale: quantitative
  - Format: "$45.2K" (compact abbreviation)
  - Grid: Horizontal lines every $10K
  - Min: 0 (auto)
  - Max: Auto with 10% padding

Series:
  1. Actual Cost (#077A9D Teal, 2px solid, dots on hover)
  2. 7-Day MA (#00A972 Green, 1.5px solid, no dots)
  3. Forecast (#6B4FBB Purple, 2px dashed, confidence band)
  4. Budget (#FF3621 Red, 1px dashed horizontal)

Anomaly Markers:
  - Red dots (8px radius) on anomaly days
  - Label: "↑{drift_pct}%" above dot
  - Click: Show anomaly detail modal
```

**Interactive Elements:**
```
Hover Tooltip:
┌────────────────────────┐
│ Date: Nov 15, 2025     │
│ Actual: $48,234        │
│ 7-Day MA: $45,123      │
│ Forecast: $49,500      │
│ Budget: $50,000        │
│ vs Yesterday: ↑12.3%   │
│ vs Last Week: ↑22.8%   │
│ Status: ⚠️ Warning     │
└────────────────────────┘

Click Data Point:
  → Navigate to daily breakdown page
  → Filter: selected date
  → Show: Job-level cost breakdown

Legend (Right-aligned):
  [x] Actual  [x] Moving Avg  [x] Forecast  [x] Budget
  (Click to toggle series visibility)

Time Range Zoom:
  - Drag horizontal to select range
  - Double-click to reset
  - Buttons: 7d / 30d / 90d / YTD / Custom
```

**Annotations & Alerts:**
```
Anomaly Markers:
  - Position: On anomaly days
  - Icon: ⚠️ warning triangle (16px)
  - Color: #FF9800 (orange for medium severity)
  - Tooltip: "Cost spike: +42% vs baseline"
  - Click: Open anomaly detail panel

Budget Breach Points:
  - Position: Where actual crosses budget line
  - Icon: 🔴 red dot (12px)
  - Label: "Over budget by $X"
  - Click: Show budget alert configuration

Forecast Confidence Band:
  - Area: Semi-transparent purple (#6B4FBB with 0.2 opacity)
  - Represents: 80% confidence interval
  - Hover: Show "Forecast range: $X - $Y"
```

### Cost Breakdown Table

**Columns:**
```
Workspace    | SKU Category | Usage | Cost    | Trend    | Actions
───────────────────────────────────────────────────────────────────
Production   | All-Purpose  | 156h  | $12.5K  | ↑ 22%    | [Optimize]
Production   | Jobs Compute | 89h   | $8.9K   | ↓ 5%     | [→]
Staging      | SQL Warehouse| 45h   | $4.2K   | ↑ 15%    | [Optimize]
```

**Design:**
- Header: 14px / 600 weight / Gray-700
- Cells: 14px / 400 weight / Gray-900
- Trend: Color-coded (green/red) with arrow
- Row hover: Background Gray-50
- Zebra striping: Alternate rows Gray-25
- Actions: Icon buttons (visible on hover)

### Agent Integration Panel (Right Sidebar, 360px)

```
┌─────────────────────────────────┐
│ 💬 Cost Agent                   │
│                                 │
│ Suggested Questions:            │
│ • Why did cost spike this week? │
│ • Forecast next 30 days         │
│ • Compare to last month         │
│                                 │
│ [Ask a question...]             │
└─────────────────────────────────┘
```

---

## Page 3: Performance Hub

**Purpose:** Query performance, warehouse utilization, optimization recommendations

**Data Sources:**
- Metric View: `query_performance_metrics` (15 dimensions, 12 measures)
- TVFs: `get_slow_queries()`, `get_warehouse_utilization()`, `get_query_spill_analysis()`
- Monitoring: `fact_performance_query_daily_profile_metrics` (30 custom metrics)
- System Tables: `system.query.history`, `system.compute.warehouse_events`

### Layout (6-Column Grid)

```
Row 1: Performance KPIs (y=0, height=2)
┌──────┬──────┬──────┬──────┬──────┬──────┐
│Total │P50   │P95   │Failed│Avg   │Spill │
│Quer. │Dur.  │Dur.  │Quer. │Queue │Count │
│45.2K │2.3s  │12.8s │ 145  │0.8s  │  23  │
│↑15%  │↓5%   │↑22%  │↑340% │↑12%  │↓8%   │
└──────┴──────┴──────┴──────┴──────┴──────┘

Row 2: Query Latency Distribution (y=2, height=6, FULL WIDTH)
┌─────────────────────────────────────────────────────────────┐
│ Query Performance (Last 24 Hours) - Percentile Analysis    │
│ [Area Chart with 3 bands]                                   │
│                                                             │
│  P99 Band (Red-100, 0.3 opacity)                           │
│  P95 Band (Yellow-100, 0.3 opacity)                        │
│  P50 Line (Green, 2px solid)                               │
│  Actual Queries (scatter dots, colored by status)          │
│                                                             │
│ X-axis: Hour of Day (0-23) | Y-axis: Duration (seconds)    │
└─────────────────────────────────────────────────────────────┘

Row 3: Warehouse Utilization Heatmap + Slow Queries (y=8)
┌───────────────────────────┬─────────────────────────────────┐
│ Warehouse Utilization     │ Top 50 Slowest Queries          │
│ [Heatmap: Hour × WH]      │ [Table with optimization hints] │
│ (width=3, height=8)       │ (width=3, height=8)             │
│                           │                                 │
│ Color Scale:              │ Columns:                        │
│ 0-20%:  #E8F5E9 (white)   │ - Query ID (link to SQL)        │
│ 21-40%: #A5D6A7 (light)   │ - Duration (P95 comparison)     │
│ 41-60%: #66BB6A (medium)  │ - User                          │
│ 61-80%: #43A047 (dark)    │ - GB Scanned                    │
│ 81-100%:#2E7D32 (darkest) │ - Spill (Y/N)                   │
│                           │ - Optimization Opportunity      │
│ X: 0-23 (hour)            │ - [Optimize] button             │
│ Y: Warehouse names        │                                 │
└───────────────────────────┴─────────────────────────────────┘

Row 4: Right-Sizing Recommendations (y=16, height=6)
┌─────────────────────────────────────────────────────────────┐
│ Warehouse Right-Sizing Opportunities (From TVF)             │
│                                                             │
│ Warehouse  │ Current │ Avg Util │ Recommend │ Est Savings  │
│ Analytics  │ Large   │   12%    │ Medium    │ $1,200/mo   │
│ BI         │ Medium  │   8%     │ Small     │ $800/mo     │
│ ETL        │ X-Large │   45%    │ Large     │ $2,400/mo   │
│                                                             │
│ Total Potential Savings: $4,400/month                      │
│ [Apply All] [Review Individual] [Schedule Optimization]    │
└─────────────────────────────────────────────────────────────┘
```

### Query Latency Distribution Chart Specifications

**Data Source:**
```sql
-- Powered by TVF: get_query_latency_distribution()
SELECT 
  hour_of_day,
  p50_duration_ms,
  p95_duration_ms,
  p99_duration_ms,
  query_count,
  failure_count
FROM observability.gold.get_query_latency_distribution(
  :warehouse_filter,  -- 'All' or specific warehouse
  :start_date,
  :end_date
);
```

**Visualization:**
```
Chart Type: Area chart with scatter overlay

Layers (bottom to top):
  1. P99 Band (background, #FCA4A1 Red-light, 0.2 opacity)
  2. P95 Band (#FFAB00 Amber, 0.3 opacity)
  3. P50 Line (#00A972 Green, 2px solid)
  4. Scatter: Individual queries (colored by status)
     - Success: #077A9D (Teal)
     - Failed: #FF3621 (Red)
     - Timeout: #FF9800 (Orange)

Scatter Point Size:
  - Based on GB scanned (1-10px radius)
  - Hover: Show query details

Hover Tooltip:
┌────────────────────────┐
│ Hour: 14:00 (2 PM)     │
│ P50: 2.3s              │
│ P95: 12.8s             │
│ P99: 45.2s             │
│ Queries: 1,234         │
│ Failed: 12 (0.97%)     │
│ [View Queries]         │
└────────────────────────┘
```

### Warehouse Utilization Heatmap

**Data Source:**
```sql
-- From TVF: get_warehouse_utilization()
SELECT 
  warehouse_name,
  date,
  hour_of_day,
  query_count,
  concurrent_queries_p95,
  utilization_pct,
  CASE 
    WHEN utilization_pct > 80 THEN 'OVER_UTILIZED'
    WHEN utilization_pct < 20 THEN 'UNDER_UTILIZED'
    ELSE 'OPTIMAL'
  END as recommendation
FROM observability.gold.get_warehouse_utilization(
  :warehouse_filter,
  :start_date,
  :end_date
)
ORDER BY date, hour_of_day;
```

**Heatmap Design:**
```
Grid Layout:
  - Columns: 24 (hours 0-23)
  - Rows: N warehouses (dynamic)
  - Cell Size: 32px × 32px (compact for 24 columns)

Color Scale (Sequential Green):
  - 0-20%:   #E8F5E9 (very light - UNDER_UTILIZED)
  - 21-40%:  #A5D6A7 (light)
  - 41-60%:  #66BB6A (medium - OPTIMAL)
  - 61-80%:  #43A047 (dark)
  - 81-100%: #2E7D32 (darkest - OVER_UTILIZED)

Cell Border:
  - Default: 1px #E0E4E8
  - Hover: 2px #077A9D (Teal)
  - Selected: 3px #077A9D

Annotations:
  - UNDER_UTILIZED cells: ↓ icon (consider downsizing)
  - OVER_UTILIZED cells: ↑ icon (consider scaling up)

Hover Tooltip:
┌─────────────────────────┐
│ Warehouse: Analytics    │
│ Date: Nov 15            │
│ Hour: 14:00 (2 PM)      │
│ Utilization: 78%        │
│ Queries: 45             │
│ Concurrent (P95): 3     │
│ Avg Latency: 2.3s       │
│ Status: ⚠️ High Util   │
│ [View Queries] [Resize] │
└─────────────────────────┘

Legend (Below heatmap):
  ┌────────────────────────────────────┐
  │ 0%  ░░░░░░░░░░░░░░░░░░  100%      │
  │ Under  │ Optimal │ Over             │
  │ <20%   │ 40-60%  │ >80%             │
  └────────────────────────────────────┘
```

### Slow Queries Table

**Data Source:**
```sql
-- From TVF: get_slow_queries() - Top 50 slowest queries
SELECT 
  rank,
  query_id,
  LEFT(query_text, 100) as query_snippet,
  execution_duration_ms / 1000.0 as execution_seconds,
  queued_duration_ms / 1000.0 as queue_seconds,
  user_name,
  warehouse_name,
  bytes_scanned / (1024*1024*1024) as gb_scanned,
  CASE 
    WHEN spill_to_disk_bytes > 0 THEN 'YES' 
    ELSE 'NO' 
  END as has_spill,
  optimization_opportunity  -- From analysis
FROM observability.gold.get_slow_queries(
  :warehouse_filter,
  :start_date,
  :end_date,
  50  -- top_n
)
ORDER BY rank;
```

**Table Design:**
```
Columns:
  Rank  │ Query Snippet     │ Duration │ Queue │ User    │ GB   │ Spill │ Optimization        │ Actions
  ──────┼───────────────────┼──────────┼───────┼─────────┼──────┼───────┼─────────────────────┼────────
  1     │ SELECT * FROM...  │  45.2s   │ 0.3s  │ alice@  │ 450  │ YES   │ Add WHERE filter    │ [⚡][📋]
  2     │ MERGE INTO...     │  32.8s   │ 1.2s  │ bob@    │ 280  │ NO    │ Use Z-ORDER         │ [⚡][📋]
  3     │ CREATE TABLE AS...│  28.5s   │ 5.1s  │ charlie │ 890  │ YES   │ Increase WH size    │ [⚡][📋]

Column Specifications:
  - Rank: 60px width, right-aligned, #Gray-600, 12px font
  - Query Snippet: 
    - Min 200px, max 400px, truncated with "..."
    - Monospace font (Fira Code)
    - Click: Expand to show full query in modal
  - Duration: 
    - 80px width, right-aligned
    - Format: "45.2s"
    - Color: 
      - <5s: #00A972 (Green)
      - 5-30s: #FFAB00 (Amber)
      - >30s: #FF3621 (Red)
  - Queue: 
    - 70px width
    - Format: "0.3s"
    - Color if >2s: #FF9800 (Orange, bottleneck indicator)
  - User: 
    - 120px width
    - Truncate email: "alice@..." 
    - Hover: Show full email
  - GB Scanned:
    - 70px width, right-aligned
    - Format: "450 GB"
    - Threshold >100GB: Bold + Orange
  - Spill:
    - 60px width, center-aligned
    - Badge: "YES" (Red) or "NO" (Green)
  - Optimization:
    - 180px width
    - Icon + text suggestion
    - Icons: 🔍 (add filter), 📊 (add index), ⚡ (scale up)
  - Actions:
    - Icon buttons (24px each)
    - ⚡ Optimize: Run auto-optimization
    - 📋 Details: Show execution plan

Row Features:
  - Zebra striping: Alternate #FAFAFA background
  - Hover: #F0F8FF (light blue) + slight elevation
  - Expandable: Click row to show full query text + execution plan
  - Sorting: Click column header (arrow indicators)
  - Filtering: Search box above table

Pagination:
  - 50 items per page (Lakeview standard)
  - "Showing 1-50 of 1,234 queries"
  - [Prev] [1] [2] [3] ... [25] [Next]
```

### Warehouse Right-Sizing Panel

**Data Source:**
```sql
-- Real pattern: Calculate savings from underutilized clusters
WITH cluster_util AS (
  SELECT 
    cluster_id,
    AVG(cpu_user_percent + cpu_system_percent) as avg_cpu_pct,
    AVG(mem_used_percent) as avg_mem_pct
  FROM system.compute.node_timeline
  WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY cluster_id
)
SELECT 
  warehouse_name,
  current_size,
  avg_cpu_pct,
  avg_mem_pct,
  recommended_size,
  monthly_cost * (1 - (avg_cpu_pct / 100)) / 2.0 as monthly_savings
FROM cluster_util u
JOIN warehouses w ON u.cluster_id = w.cluster_id
WHERE avg_cpu_pct < 50  -- Underutilized
ORDER BY monthly_savings DESC;
```

**Recommendation Card Design:**
```
┌────────────────────────────────────────────┐
│ 💡 Warehouse: "Analytics"                  │
│                                            │
│ Current:      Large (4 clusters)           │
│ Avg CPU:      12% ━━░░░░░░░░ (Low)        │
│ Avg Memory:   18% ━━░░░░░░░░ (Low)        │
│                                            │
│ ✅ Recommendation: Downsize to Medium     │
│ 💰 Est. Savings: $1,200/month             │
│ 📊 Impact: Minimal (latency +5%)          │
│                                            │
│ [Apply Now] [Schedule Review] [Dismiss]    │
└────────────────────────────────────────────┘

Card Styling:
  - Background: #F0F8FF (light blue info background)
  - Border: 2px #077A9D (Teal)
  - Border Radius: 12px
  - Padding: 24px
  - Shadow: Elevation 2

Progress Bars:
  - Total width: 200px
  - Height: 8px
  - Fill color: Based on utilization %
    - <30%: #FF9800 (Orange - underutilized)
    - 30-70%: #00A972 (Green - optimal)
    - >70%: #FFAB00 (Amber - high utilization)
  - Background: #E0E4E8 (Gray)
```

---

## Page 4: Security Center

**Purpose:** Access monitoring, anomaly detection, token management

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Security Risk Score Gauge (Center, large)                   │
│        ┌─────────┐                                          │
│        │   78    │   Status: Moderate Risk                  │
│        │  Risk   │   ↑ 5 points since yesterday             │
│        └─────────┘                                          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────┐  ┌───────────────────────────────┐
│ Access Anomalies        │  │ Token Expiration Timeline     │
│ [List with severity]    │  │ [Vertical timeline]           │
│ 🔴 After-hours access   │  │ 🔴 Critical: 2 days           │
│ 🟠 New resource access  │  │ 🟠 High: 7 days               │
│ 🟡 Unusual operation    │  │ 🟡 Medium: 14 days            │
└─────────────────────────┘  └───────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ PII Access Audit Log                                        │
│ [Table: User, Resource, Action, Timestamp]                 │
│ Filter by: User | Resource | Date Range                    │
└─────────────────────────────────────────────────────────────┘
```

### Security Risk Score Gauge

**Design:**
```
Gauge Component:
  - Type: Donut chart (220° arc)
  - Size: 280px diameter
  - Thickness: 32px
  - Center: Score number (72px / 700 weight)
  
Risk Levels:
  - 0-40:   🟢 Low Risk (Green)
  - 41-70:  🟡 Moderate Risk (Yellow)
  - 71-85:  🟠 High Risk (Orange)
  - 86-100: 🔴 Critical Risk (Red)

Below Gauge:
  - Status text: 18px / 600 weight / Colored
  - Trend: Arrow + change (14px / Gray-600)
  - Last updated: 12px / Gray-500
```

### Token Expiration Timeline

**Design:**
```
Vertical Timeline (chronological, nearest first):

┌─────────────────────────────────┐
│ Today                           │
├─────────────────────────────────┤
│ 🔴 2 days                       │
│    SP: data_pipeline_prod       │
│    [Renew Token]                │
├─────────────────────────────────┤
│ 🟠 7 days                       │
│    PAT: alice@company.com       │
│    [Extend Expiry]              │
├─────────────────────────────────┤
│ 🟡 14 days                      │
│    SP: ml_model_serving         │
│    [Set Reminder]               │
└─────────────────────────────────┘

Item Design:
  - Icon: 24px circle (colored)
  - Days until expiry: 16px / 600 weight
  - Token name: 14px / 400 weight / 2 lines max
  - Action button: Secondary (outlined)
  - Connector line: 2px Gray-300
```

### Access Anomaly Card

```
┌────────────────────────────────────────┐
│ 🔴 After-Hours Access Detected         │
│                                        │
│ User: alice@company.com                │
│ Resource: catalog.sensitive.pii_table  │
│ Time: Nov 15, 2:34 AM                  │
│ Location: 192.168.1.*** (masked)       │
│                                        │
│ [Investigate] [Mark as Safe] [Alert]   │
└────────────────────────────────────────┘

Severity Colors:
  - Critical: Error-Red background (light tint)
  - High: Warning-Yellow background
  - Medium: Info-Blue background
  - Low: Gray-100 background
```

---

## Page 5: Reliability Dashboard

**Purpose:** SLO monitoring, runtime anomalies, incident tracking

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ SLO Attainment Overview                                     │
│ [Gauge Chart Row: 4 gauges for key jobs]                   │
│ ETL_daily: 98.5% | ML_train: 99.2% | BI_sync: 95.1% | ...  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────┐  ┌───────────────────────────────┐
│ Job Runtime Trends      │  │ Runtime Anomalies             │
│ [Line chart with bands] │  │ [List with deviation %]       │
│ - Actual runtime        │  │ 🔴 ETL_daily: +340%           │
│ - P50 baseline          │  │ 🟠 ML_train: +89%             │
│ - P95 baseline          │  │                               │
└─────────────────────────┘  └───────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Incident Timeline                                           │
│ [Horizontal timeline with MTTR indicators]                  │
│ Filter: Last 7d / 30d / All                                │
└─────────────────────────────────────────────────────────────┘
```

### SLO Gauge Row

**Design:**
```
4 Gauges in a row, 240px width each

┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   98.5%     │ │   99.2%     │ │   95.1%     │ │   100%      │
│  ETL_daily  │ │  ML_train   │ │  BI_sync    │ │  Reports    │
│ Target: 95% │ │ Target: 99% │ │ Target: 95% │ │ Target: 99% │
│ ✅ Meeting  │ │ ✅ Meeting  │ │ ⚠️ At Risk  │ │ ✅ Meeting  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

Gauge Colors:
  - >= Target: Success Green
  - 95-99% of Target: Warning Yellow
  - < 95% of Target: Error Red
```

### Job Runtime with Baseline Bands

**Chart:**
```
Area Chart with 3 layers:
1. P95 Band (Yellow-100, opacity 0.3)
2. P50 Band (Yellow-200, opacity 0.3)
3. Actual Runtime (Primary-500, 2px line)
4. Anomalies (Error-Red, 8px circles)

Tooltip on Hover:
┌────────────────────────┐
│ Job: ETL_daily         │
│ Date: Nov 15, 2:00 AM  │
│ Runtime: 2h 34m        │
│ P50 Baseline: 45m      │
│ Deviation: +240%       │
│ Status: 🔴 Anomaly     │
└────────────────────────┘
```

### Incident Timeline

**Design:**
```
Horizontal Timeline (newest left):

Today            Yesterday         3 days ago
  |                  |                 |
  🔴──────────────────┤                 |
  │ 45min MTTR        │                 |
  └─────────────────────────────────────┘
           🟠──────┤
           │ 15min │
           └───────┘

Timeline Items:
  - Severity color (red/orange/yellow)
  - Horizontal bar (width = duration)
  - Hover: Show incident details
  - Click: Navigate to incident detail page

Metrics Panel:
  - Total Incidents: 23 (last 30d)
  - Avg MTTR: 28 minutes
  - MTBF: 36 hours
```

---

## Page 6: Alert Management

**Purpose:** Configure, test, and manage all alerts

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Filters:  [All Types ▾] [All Severities ▾] [Search...]     │
│ [+ Create Alert]                                    [Export]│
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Active Alerts Table                                         │
│ Name         | Type    | Status | Severity | Last Fired    │
│ Cost Spike   | Cost    | ✅ On  | High     | 2 hours ago   │
│ Runtime Anom | Runtime | ✅ On  | Critical | 15 min ago    │
│ Token Expiry | Security| ⏸️ Off | Medium   | Never         │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Alert History (Last 7 Days)                                │
│ [Timeline visualization]                                    │
└─────────────────────────────────────────────────────────────┘
```

### Alert Configuration Wizard (Modal)

**Step 1: Alert Type**
```
┌──────────────────────────────────────────┐
│ Create New Alert                         │
│                                          │
│ Select Alert Type:                       │
│                                          │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│ │ 💰 Cost │ │ ⚡ Perf │ │ 🔒 Sec  │    │
│ └─────────┘ └─────────┘ └─────────┘    │
│ ┌─────────┐                             │
│ │ ✅ Rely │                             │
│ └─────────┘                             │
│                                          │
│          [Cancel]  [Next →]              │
└──────────────────────────────────────────┘
```

**Step 2: Resource Selection**
```
┌──────────────────────────────────────────┐
│ Create Cost Alert                        │
│                                          │
│ Select Resource to Monitor:              │
│                                          │
│ Resource Type:                           │
│ ( ) All Workspaces                       │
│ (•) Specific Workspace ▾                 │
│     [Production            ▾]            │
│                                          │
│ Metric:                                  │
│ [Daily Cost              ▾]              │
│                                          │
│         [← Back]  [Next →]               │
└──────────────────────────────────────────┘
```

**Step 3: Threshold Configuration**
```
┌──────────────────────────────────────────┐
│ Create Cost Alert                        │
│                                          │
│ Set Threshold:                           │
│                                          │
│ Threshold Type:                          │
│ (•) Absolute Value                       │
│ ( ) Percentage Change                    │
│ ( ) Anomaly Detection                    │
│                                          │
│ Threshold Value:                         │
│ $ [10000] USD                            │
│                                          │
│ Comparison:                              │
│ [Greater Than              ▾]            │
│                                          │
│ 💡 Preview: Alert fires when daily cost  │
│    exceeds $10,000                       │
│                                          │
│         [← Back]  [Next →]               │
└──────────────────────────────────────────┘
```

**Step 4: Notification Settings**
```
┌──────────────────────────────────────────┐
│ Create Cost Alert                        │
│                                          │
│ Notification Settings:                   │
│                                          │
│ Recipients:                              │
│ ┌────────────────────────────────────┐  │
│ │ alice@company.com                  ✕ │  │
│ │ platform-team@company.com          ✕ │  │
│ └────────────────────────────────────┘  │
│ [+ Add recipient]                        │
│                                          │
│ Channels:                                │
│ ☑ Email                                  │
│ ☑ Slack (#platform-alerts)               │
│ ☐ PagerDuty                              │
│                                          │
│ Severity: [High              ▾]         │
│                                          │
│         [← Back]  [Create Alert]         │
└──────────────────────────────────────────┘
```

**Step 5: Confirmation**
```
┌──────────────────────────────────────────┐
│ Alert Created Successfully! ✅           │
│                                          │
│ Alert Name: Workspace Production Cost   │
│             Threshold                    │
│                                          │
│ ✅ Alert is now active                   │
│ ✅ Monitoring started                    │
│ ✅ Notifications configured              │
│                                          │
│ What's next?                             │
│ • View in Alert Management               │
│ • Test alert notification                │
│ • Configure suppression rules            │
│                                          │
│    [View Alert] [Create Another] [Done]  │
└──────────────────────────────────────────┘
```

---

## Page 7: Agent Chat

**Purpose:** Natural language interaction with Platform Health Copilot

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [Workspace: Production ▾] [Time: Last 7d ▾]        [Clear] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Chat Messages Area (Scrollable)                           │
│                                                             │
│  User Bubble (right-aligned):                              │
│  ┌────────────────────────────────────┐                    │
│  │ Why did cost spike 40% this week?  │                    │
│  └────────────────────────────────────┘                    │
│                                                             │
│  Agent Bubble (left-aligned):                              │
│  ┌────────────────────────────────────────────────┐        │
│  │ Cost in workspace "Production" increased       │        │
│  │ 42% week-over-week. Analysis shows:            │        │
│  │                                                 │        │
│  │ 🔍 Root Cause:                                 │        │
│  │ • Job "ETL_daily" runtime increased 3.2x       │        │
│  │ • Caused by data volume spike (+89%)           │        │
│  │                                                 │        │
│  │ [Inline Cost Chart]                            │        │
│  │                                                 │        │
│  │ 💡 Recommendations:                            │        │
│  │ 1. Optimize query in ETL job                   │        │
│  │ 2. Add partitioning to source table            │        │
│  │                                                 │        │
│  │ [Create Alert] [View Job Details]              │        │
│  └────────────────────────────────────────────────┘        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Suggested Questions:                                        │
│ • What jobs failed today?                                   │
│ • Show me top 10 most expensive queries                     │
│ • Are there any security anomalies?                         │
│ • Compare this week to last week                            │
├─────────────────────────────────────────────────────────────┤
│ [Type your question...]                            [Send →] │
└─────────────────────────────────────────────────────────────┘
```

### Chat Message Bubbles

**User Message:**
```
┌────────────────────────────────────┐
│ Why did cost spike 40% this week?  │ ← User avatar (24px)
└────────────────────────────────────┘
  - Background: Primary-500
  - Text: White
  - Border Radius: 12px (bottom-right: 4px)
  - Max Width: 70% of chat area
  - Padding: 12px 16px
  - Float: Right
```

**Agent Message:**
```
Agent avatar (32px) ↓
┌────────────────────────────────────────────────┐
│ Cost in workspace "Production" increased       │
│ 42% week-over-week. Analysis shows:            │
│                                                 │
│ 🔍 Root Cause:                                 │
│ • Job "ETL_daily" runtime increased 3.2x       │
│ • Caused by data volume spike (+89%)           │
│                                                 │
│ [Inline Cost Chart - 400px × 200px]            │
│                                                 │
│ 💡 Recommendations:                            │
│ 1. Optimize query in ETL job                   │
│ 2. Add partitioning to source table            │
│                                                 │
│ [Create Alert] [View Job Details]              │
└────────────────────────────────────────────────┘
  - Background: Gray-100
  - Text: Gray-900
  - Border Radius: 12px (bottom-left: 4px)
  - Max Width: 85% of chat area
  - Padding: 16px 20px
  - Float: Left
```

**Tool Call Visualization (within Agent bubble):**
```
┌──────────────────────────────────────────┐
│ 🔧 Tools Used:                           │
│                                          │
│ ✅ get_cost_breakdown (0.8s)             │
│ ✅ detect_cost_spike (1.2s)              │
│ ✅ analyze_job_runtime (0.6s)            │
│                                          │
│ [Show Details]                           │
└──────────────────────────────────────────┘
  - Collapsed by default
  - Expand to show SQL queries and results
  - Monospace font for code
```

### Suggested Questions Pills

```
[What jobs failed today?] [Top 10 expensive queries] [Security anomalies?]

Design:
  - Background: White
  - Border: 1px Primary-300
  - Border Radius: 16px
  - Padding: 8px 16px
  - Font: 14px / 500 weight
  - Hover: Background Primary-50
  - Click: Insert into input field
```

### Chat Input Field

```
┌──────────────────────────────────────────────────────────┐
│ [Type your question...]                         [Send →] │
└──────────────────────────────────────────────────────────┘

Design:
  - Height: 56px (auto-expand to 120px max)
  - Background: White
  - Border: 2px Gray-300
  - Focus: Border Primary-500
  - Placeholder: Gray-400
  - Send Button: Primary-500 (disabled if empty)
  
Features:
  - Multiline support (Shift+Enter)
  - Send on Enter
  - Character counter (1000 max)
  - Typing indicator for agent
```

---

## 🧩 Component Library Requirements

### 1. Buttons

**Primary Button:**
```
Default:
  - Background: Primary-500
  - Text: White / 14px / 600 weight
  - Padding: 10px 24px
  - Border Radius: 8px
  - Shadow: None

Hover:
  - Background: Primary-700
  - Shadow: Elevation 1

Pressed:
  - Background: Primary-900
  - Scale: 0.98

Disabled:
  - Background: Gray-200
  - Text: Gray-400
  - Cursor: not-allowed
```

**Secondary Button (Outlined):**
```
Default:
  - Background: White
  - Border: 2px Primary-500
  - Text: Primary-700
  
Hover:
  - Background: Primary-50
```

**Tertiary Button (Ghost):**
```
Default:
  - Background: Transparent
  - Text: Primary-700
  
Hover:
  - Background: Gray-100
```

**Button Sizes:**
- Small: 32px height / 12px font
- Medium: 40px height / 14px font (default)
- Large: 48px height / 16px font

### 2. Cards

**Standard Card:**
```
Background: White
Border: 1px Gray-200
Border Radius: 12px
Padding: 24px
Shadow: Elevation 1

Hover:
  Shadow: Elevation 2
  Border: 1px Primary-200 (if interactive)
```

**Metric Card (Small):**
```
Size: 200px × 120px
Header: Metric name (12px / 500 weight / Gray-600)
Value: Large number (32px / 700 weight / Gray-900)
Trend: Arrow + percentage (14px / colored)
Sparkline: Mini chart (optional)
```

### 3. Badges & Pills

**Status Badge:**
```
Critical:  Red-100 bg / Red-700 text
High:      Orange-100 bg / Orange-700 text
Medium:    Yellow-100 bg / Yellow-800 text
Low:       Gray-100 bg / Gray-700 text
Success:   Green-100 bg / Green-700 text

Size: Height 24px
Border Radius: 12px
Padding: 4px 12px
Font: 12px / 600 weight
```

**Count Badge (on icons):**
```
Size: 18px × 18px (minimum)
Background: Error-Red
Text: White / 10px / 700 weight
Border Radius: 9px
Position: Top-right corner of icon
Border: 2px White (for contrast)
```

### 4. Data Tables

**Header Row:**
```
Background: Gray-50
Border Bottom: 2px Gray-200
Padding: 12px 16px
Font: 14px / 600 weight / Gray-700
Sort Icons: Arrow up/down on hover
```

**Body Rows:**
```
Background: White (alternating Gray-25)
Border Bottom: 1px Gray-100
Padding: 12px 16px
Font: 14px / 400 weight / Gray-900

Hover:
  Background: Primary-50
  Cursor: pointer (if interactive)
```

**Actions Column:**
```
Width: 120px
Alignment: Right
Buttons: Icon buttons (24px)
Visibility: Show on row hover
```

### 5. Tooltips

```
Background: Gray-900
Text: White / 12px / 400 weight
Padding: 8px 12px
Border Radius: 6px
Arrow: 6px triangle
Max Width: 280px
Shadow: Elevation 3

Position: Auto (smart positioning)
Delay: 300ms
```

### 6. Modals

**Small Modal (400px width):**
```
Background: White
Border Radius: 16px
Shadow: Elevation 4
Overlay: Black opacity 0.5

Header:
  Height: 64px
  Padding: 20px 24px
  Border Bottom: 1px Gray-200
  Close Button: Top-right (32px)

Body:
  Padding: 24px
  Max Height: 60vh (scrollable)

Footer:
  Height: 72px
  Padding: 16px 24px
  Border Top: 1px Gray-200
  Buttons: Right-aligned
```

**Large Modal (800px width):**
- Same design, wider content area

### 7. Dropdowns

```
Trigger:
  Height: 40px
  Padding: 8px 16px
  Border: 1px Gray-300
  Border Radius: 8px
  Chevron: Right-aligned

Dropdown Menu:
  Background: White
  Border Radius: 8px
  Shadow: Elevation 2
  Max Height: 320px (scrollable)
  
Menu Item:
  Padding: 10px 16px
  Hover: Background Gray-100
  Selected: Background Primary-50 + Checkmark
  Divider: 1px Gray-200
```

### 8. Charts (Recharts/Chart.js patterns)

**Common Chart Settings:**
```
Grid: Dashed lines (Gray-200)
Axes: Gray-600 text / 12px
Tooltips: Follow tooltip component design
Legend: Bottom or right, 12px / Gray-700
Animation: 300ms ease-in-out
Responsive: Maintain aspect ratio
```

---

## 🎬 Interaction Patterns

### 1. Loading States

**Page Load:**
- Skeleton screens (shimmer effect)
- Gray-100 blocks with shimmer animation
- Maintain layout structure

**Button Load:**
- Spinner icon (16px)
- Text: "Loading..." or keep original text
- Disabled state

**Data Refresh:**
- Subtle spinner in top-right corner
- Toast notification: "Data refreshed"

### 2. Error States

**Error Banner:**
```
┌────────────────────────────────────────────┐
│ ⚠️ Failed to load data. [Retry] [Dismiss] │
└────────────────────────────────────────────┘

Background: Error-Red-50
Border: 1px Error-Red-200
Border Radius: 8px
Padding: 12px 16px
Position: Top of page (below nav)
```

**Empty States:**
```
┌────────────────────────────────┐
│         📊                     │
│                                │
│    No data available           │
│    Try adjusting filters       │
│                                │
│    [Clear Filters]             │
└────────────────────────────────┘

Center-aligned
Icon: 64px / Gray-400
Text: 16px / Gray-600
```

### 3. Notifications (Toasts)

**Position:** Top-right corner, 24px from edge

**Types:**
```
Success:  Green-500 left border + Green-50 bg + ✅ icon
Info:     Primary-500 left border + Primary-50 bg + ℹ️ icon
Warning:  Orange-500 left border + Orange-50 bg + ⚠️ icon
Error:    Red-500 left border + Red-50 bg + ❌ icon

Duration: 
  - Success/Info: 3 seconds
  - Warning: 5 seconds
  - Error: 8 seconds (manual dismiss)

Animation: Slide in from right, fade out
```

### 4. Confirmation Dialogs

```
┌──────────────────────────────────────────┐
│ Delete Alert?                     ✕      │
├──────────────────────────────────────────┤
│ Are you sure you want to delete this     │
│ alert? This action cannot be undone.     │
│                                          │
│              [Cancel] [Delete Alert]     │
└──────────────────────────────────────────┘

Delete Button: Error-Red background
Cancel Button: Secondary style
```

---

## 📐 Responsive Design Requirements

### Breakpoints

```
Mobile:  < 768px
Tablet:  768px - 1024px
Desktop: > 1024px
Large:   > 1440px
```

### Mobile Adaptations

**Navigation:**
- Side nav: Collapsible (hamburger menu)
- Top nav: Stacked dropdowns
- User menu: Full-width modal

**Page Layouts:**
- Single column
- Cards: Full width with 16px margins
- Tables: Horizontal scroll or card view
- Charts: Simplified, touch-optimized

**Chat Interface:**
- Full screen on mobile
- Suggested questions: Horizontal scroll
- Keyboard: Push content up (not fixed)

### Tablet Adaptations

- Side nav: Always visible but narrow (64px icons only)
- 2-column layout for dashboard cards
- Charts: Maintain interactivity

### Touch Targets

- Minimum: 44px × 44px
- Spacing: 8px minimum between targets
- Hover states: Convert to press states

---

## ♿ Accessibility Requirements

### WCAG 2.1 AA Compliance

**Color Contrast:**
- Text: 4.5:1 minimum (normal text)
- Large Text: 3:1 minimum (18px+)
- Interactive: 3:1 for focus indicators

**Keyboard Navigation:**
- Tab order: Logical flow
- Focus indicators: 2px Primary-500 outline
- Shortcuts: Document in help section
- Escape: Close modals/dropdowns

**Screen Readers:**
- ARIA labels: All interactive elements
- Live regions: Dynamic content updates
- Landmark roles: Main, nav, complementary
- Alt text: All icons and charts

**Motion:**
- Respect prefers-reduced-motion
- Disable animations for accessibility mode
- No auto-playing animations

---

## 📦 Deliverables Checklist

### Phase 1: Design System (Week 1)
- [ ] Color palette (Figma color styles)
- [ ] Typography scale (Figma text styles)
- [ ] Spacing tokens
- [ ] Component library (30+ components)
- [ ] Icon library (50+ icons)
- [ ] Design tokens export (JSON)

### Phase 2: Pages (Weeks 2-3)
- [ ] Page 1: Overview Dashboard (desktop + mobile)
- [ ] Page 2: Cost Monitor (desktop + mobile)
- [ ] Page 3: Performance Hub (desktop + mobile)
- [ ] Page 4: Security Center (desktop + mobile)
- [ ] Page 5: Reliability Dashboard (desktop + mobile)
- [ ] Page 6: Alert Management (desktop + mobile)
- [ ] Page 7: Agent Chat (desktop + mobile)

### Phase 3: Interactions (Week 4)
- [ ] Prototype: Navigation flows
- [ ] Prototype: Alert creation wizard
- [ ] Prototype: Chat interactions
- [ ] Loading states for all pages
- [ ] Error states and empty states
- [ ] Hover states and transitions

### Phase 4: Documentation (Week 4)
- [ ] Component usage guide
- [ ] Design system documentation
- [ ] Developer handoff notes
- [ ] Accessibility checklist
- [ ] Responsive breakpoint guide

---

## 🎨 Design Best Practices

1. **Data Visualization:**
   - Use color sparingly (semantic meaning only)
   - Annotate anomalies directly on charts
   - Provide context (previous period, target)
   - Interactive tooltips with rich details

2. **Typography Hierarchy:**
   - Maximum 3 font sizes per page
   - Clear visual hierarchy (headings → body → labels)
   - Adequate line-height (1.5x for body text)

3. **White Space:**
   - Generous padding in cards (24px minimum)
   - Section spacing (48px between major sections)
   - Don't overcrowd dashboards

4. **Status Communication:**
   - Color + icon (don't rely on color alone)
   - Consistent severity mapping across app
   - Clear action items for every alert

5. **Progressive Disclosure:**
   - Summary view by default
   - Drill-down for details
   - Expand/collapse for tables
   - Modal for complex actions

---

## 🚀 Next Steps After Design

1. **Design Review:** Stakeholder feedback on mockups
2. **Usability Testing:** Test with 5 platform engineers
3. **Developer Handoff:** 
   - Export design tokens (JSON)
   - Component specifications
   - Interaction documentation
4. **Implementation:** Next.js components built from Figma
5. **Design QA:** Ensure implementation matches design

---

## 📚 Reference Materials

**Databricks Design:**
- Databricks UI patterns (reference existing apps)
- SQL Analytics dashboard patterns

**Inspiration:**
- Datadog Dashboards (metric density, time range picker)
- New Relic Observability (anomaly detection, MTTR tracking)
- Grafana (chart interactions, drill-down)
- PagerDuty (incident timeline, severity colors)

**Accessibility:**
- WCAG 2.1 Guidelines
- WAI-ARIA Authoring Practices

---

---

## 🎯 ENHANCED SECTION: Real Databricks Dashboard Patterns

### Production Dashboard Widget Specifications

**Based on analysis of 8 production Databricks Lakeview dashboards (Governance Hub, Jobs Dashboard, DBSQL Warehouse Advisor, Account Usage, etc.)**

#### Widget Type 1: KPI Counter (Lakeview v3 Encoding)

```json
{
  "spec": {
    "version": 3,
    "widgetType": "counter",
    "encodings": {
      "value": {
        "fieldName": "total_cost",
        "displayName": "Total Monthly Cost"
      }
    },
    "frame": {
      "showTitle": true,
      "title": "Total Cost"
    }
  },
  "textbox_spec": null
}
```

**Figma Design Requirements:**
- **Number:** 48px / 700 weight / Databricks-900
- **Label:** 14px / 500 weight / Databricks-600
- **Trend Indicator:** Arrow icon + percentage (16px / colored)
- **Background:** White with 1px border Databricks-200
- **Size:** 280px × 160px minimum
- **Hover:** Show tooltip with sparkline (last 7 days)

**Example from Jobs System Tables Dashboard:**
```
┌──────────────────────────┐
│ Total Jobs               │
│                          │
│ 1,247                    │
│ ↑ 12% vs last month      │
└──────────────────────────┘
```

#### Widget Type 2: Multi-Series Line Chart (Time Series)

**Real Pattern from DBSQL Warehouse Advisor (fc2d4844 dataset):**

```json
{
  "spec": {
    "version": 3,
    "widgetType": "line-chart",
    "encodings": {
      "x": {
        "fieldName": "date",
        "scale": {"type": "time"}
      },
      "y": [
        {
          "fieldName": "p50_duration_ms",
          "displayName": "P50 Latency",
          "color": "#1DB954"
        },
        {
          "fieldName": "p95_duration_ms",
          "displayName": "P95 Latency",
          "color": "#FFC107"
        },
        {
          "fieldName": "p99_duration_ms",
          "displayName": "P99 Latency",
          "color": "#F44336"
        }
      ]
    }
  }
}
```

**Figma Specifications:**
- **Width:** Full container width (6 columns in 6-column grid)
- **Height:** 400px
- **X-Axis:** Date labels every 4 hours, format "Nov 1, 2:00 PM"
- **Y-Axis:** Duration in ms, format "125ms" (abbreviated)
- **Grid:** Horizontal lines every 50ms, dashed Databricks-200
- **Legend:** Top-right, horizontal layout
- **Tooltip:** Appears on hover with all series values

**Critical Pattern: Anomaly Annotations**

From Governance Hub Dashboard - mark outliers directly on chart:
```
• Red circle marker (12px) at anomaly point
• Vertical dashed line (Red-500) from marker to X-axis
• Floating annotation box:
  ┌────────────────────────┐
  │ ⚠️ Cost Spike          │
  │ +42% above baseline    │
  │ [Investigate]          │
  └────────────────────────┘
```

#### Widget Type 3: Stacked Bar Chart (SKU Breakdown)

**Real Pattern from Azure Serverless Cost Dashboard (e64c7fb4 dataset):**

```json
{
  "spec": {
    "version": 3,
    "widgetType": "bar-chart",
    "encodings": {
      "x": {"fieldName": "date"},
      "y": {"fieldName": "cost_amount"},
      "color": {
        "fieldName": "sku_name",
        "scale": {
          "domain": ["JOBS_LIGHT_COMPUTE", "ALL_PURPOSE_COMPUTE", "SQL_COMPUTE"],
          "range": ["#1DB954", "#FF6B35", "#2196F3"]
        }
      }
    },
    "stacked": true
  }
}
```

**Figma Design:**
- **Bar Width:** 24px with 8px spacing
- **Colors:** Use distinct Databricks palette colors (avoid similar hues)
- **Stacking Order:** Largest to smallest (top to bottom)
- **Hover:** Highlight segment + show breakdown tooltip
- **Legend:** Below chart, horizontal chips with checkboxes to toggle

#### Widget Type 4: Data Table with Conditional Formatting

**Real Pattern from Governance Hub "Top Queried Tables Without Tags" (98c632da dataset):**

```json
{
  "spec": {
    "version": 3,
    "widgetType": "table",
    "columns": [
      {"fieldName": "table_name", "displayName": "Table"},
      {"fieldName": "query_count", "displayName": "Queries (30d)", "align": "right"},
      {"fieldName": "tag_count", "displayName": "Tags", "align": "center"},
      {"fieldName": "priority_score", "displayName": "Priority", "align": "right"}
    ],
    "conditionalFormatting": [
      {
        "column": "tag_count",
        "rule": "== 0",
        "style": {"backgroundColor": "#FEE", "color": "#C00"}
      },
      {
        "column": "priority_score",
        "rule": ">= 80",
        "style": {"fontWeight": "bold", "color": "#F44336"}
      }
    ]
  }
}
```

**Figma Specifications:**

**Header Row:**
```
Background: Databricks-50
Height: 48px
Padding: 12px 16px
Font: 14px / 600 weight / Databricks-700
Border Bottom: 2px Databricks-200
Sort Icon: Arrow up/down (16px) on hover
```

**Body Rows:**
```
Height: 56px
Padding: 12px 16px
Font: 14px / 400 weight / Databricks-900
Alternating: White / Databricks-25
Hover: Databricks-100 background

Conditional Formatting:
  Zero Tags:    Red-50 background + Red-700 text + ⚠️ icon
  High Priority: Bold font + Red-700 text
```

**Action Column (appears on hover):**
```
Width: 120px
Alignment: Right
Buttons: 
  • View Details (eye icon, 32px)
  • Add Tags (tag icon, 32px)
  • Ignore (x icon, 32px)
```

#### Widget Type 5: Heatmap (Warehouse Utilization)

**Real Pattern from DBSQL Warehouse Advisor (f87c4f02 dataset):**

```json
{
  "spec": {
    "version": 3,
    "widgetType": "heatmap",
    "encodings": {
      "x": {"fieldName": "hour", "scale": {"domain": [0, 23]}},
      "y": {"fieldName": "warehouse_name"},
      "color": {
        "fieldName": "utilization_pct",
        "scale": {
          "type": "sequential",
          "scheme": "greens",
          "domain": [0, 100]
        }
      }
    }
  }
}
```

**Figma Design:**

**Grid Structure:**
```
Columns: 24 (one per hour)
Rows: N warehouses (dynamic)
Cell Size: 48px × 48px
Gap: 2px

Color Scale (5 stops):
  0-20%:   #E8F5E9 (Databricks-Green-50)
  21-40%:  #A5D6A7 (Databricks-Green-200)
  41-60%:  #66BB6A (Databricks-Green-400)
  61-80%:  #43A047 (Databricks-Green-600)
  81-100%: #2E7D32 (Databricks-Green-800)
```

**Hover Tooltip:**
```
┌──────────────────────────┐
│ Warehouse: Analytics     │
│ Time: 2:00 PM - 3:00 PM  │
│ Utilization: 78%         │
│ ─────────────────────    │ ← Progress bar
│ Active Queries: 12       │
│ Avg Latency: 2.3s        │
│                          │
│ [View Queries]           │
└──────────────────────────┘
```

**Legend (horizontal bar):**
```
0%     20%    40%    60%    80%    100%
├──────┼──────┼──────┼──────┼──────┤
└─ Light ──────────────────── Heavy ─┘
```

---

### Data Layer Integration Patterns

#### Pattern 1: Metric View Integration (Semantic Layer)

**Purpose:** Business-friendly query syntax for KPIs

**Backend Query:**
```sql
-- From observability.gold.cost_performance_metrics (Metric View)
SELECT 
  workspace_name,
  MEASURE(`Total Cost`) as total_cost,
  MEASURE(`Cost Per Job`) as cost_per_job,
  MEASURE(`7-Day Moving Avg Cost`) as trend_7d
FROM observability.gold.cost_performance_metrics
WHERE date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY workspace_name
ORDER BY total_cost DESC
LIMIT 10;
```

**Frontend API Call:**
```typescript
// lib/api/metric-views.ts
export async function fetchMetricViewData(
  metricViewName: string,
  measures: string[],
  dimensions: string[],
  filters: Record<string, any>
) {
  const query = `
    SELECT 
      ${dimensions.join(', ')},
      ${measures.map(m => `MEASURE(\`${m}\`) as ${m.toLowerCase().replace(/ /g, '_')}`).join(', ')}
    FROM observability.gold.${metricViewName}
    WHERE ${buildFilterClause(filters)}
    GROUP BY ${dimensions.join(', ')}
  `;
  
  const response = await fetch('/api/databricks/query', {
    method: 'POST',
    body: JSON.stringify({ query, warehouse_id: process.env.WAREHOUSE_ID }),
    headers: { 'Authorization': `Bearer ${getUCToken()}` }
  });
  
  return await response.json();
}

// Usage in React component
const { data, loading, error } = useMetricView({
  metricView: 'cost_performance_metrics',
  measures: ['Total Cost', 'Cost Per Job'],
  dimensions: ['workspace_name', 'date'],
  filters: { date: { gte: 'CURRENT_DATE() - INTERVAL 30 DAYS' } }
});
```

**UI Component Mapping:**
```typescript
// components/KPICounter.tsx
interface KPICounterProps {
  label: string;
  metricView: string;
  measure: string;  // e.g., "Total Cost"
  filters?: Record<string, any>;
  trendPeriod?: '7d' | '30d';
}

export function KPICounter({ label, metricView, measure, filters, trendPeriod = '7d' }: KPICounterProps) {
  const { data } = useMetricView({
    metricView,
    measures: [measure],
    dimensions: ['date'],
    filters
  });
  
  const currentValue = data[data.length - 1]?.[measure];
  const previousValue = data[data.length - 8]?.[measure]; // 7 days ago
  const trendPct = ((currentValue - previousValue) / previousValue) * 100;
  
  return (
    <Card>
      <Label>{label}</Label>
      <Value>{formatCurrency(currentValue)}</Value>
      <Trend direction={trendPct > 0 ? 'up' : 'down'}>
        {formatPercent(Math.abs(trendPct))} vs {trendPeriod}
      </Trend>
    </Card>
  );
}
```

#### Pattern 2: Table-Valued Function (TVF) Integration

**Purpose:** Parameterized complex analytics

**Backend TVF Definition:**
```sql
CREATE OR REPLACE FUNCTION observability.gold.get_top_workspaces_by_cost(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of top workspaces to return'
)
RETURNS TABLE(
  rank INT COMMENT 'Workspace rank by total cost',
  workspace_id STRING,
  workspace_name STRING,
  total_cost DECIMAL(18,2),
  pct_of_total DECIMAL(5,2)
)
COMMENT 'LLM: Returns the top N workspaces ranked by cost for a date range...'
RETURN
  WITH ranked_workspaces AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY SUM(cost_amount) DESC) as rank,
      workspace_id,
      MAX(workspace_name) as workspace_name,
      SUM(cost_amount) as total_cost
    FROM observability.gold.fact_cost_daily
    WHERE date BETWEEN TO_DATE(start_date) AND TO_DATE(end_date)
    GROUP BY workspace_id
  ),
  total_calc AS (
    SELECT SUM(total_cost) as grand_total FROM ranked_workspaces
  )
  SELECT 
    rw.rank,
    rw.workspace_id,
    rw.workspace_name,
    rw.total_cost,
    ROUND((rw.total_cost / tc.grand_total) * 100, 2) as pct_of_total
  FROM ranked_workspaces rw
  CROSS JOIN total_calc tc
  WHERE rw.rank <= top_n
  ORDER BY rw.rank;
```

**Frontend API Call:**
```typescript
// lib/api/table-valued-functions.ts
export async function callTVF(
  functionName: string,
  params: Record<string, any>
) {
  const paramList = Object.entries(params)
    .map(([key, value]) => {
      if (typeof value === 'string') return `'${value}'`;
      return value;
    })
    .join(', ');
  
  const query = `
    SELECT * FROM observability.gold.${functionName}(${paramList})
  `;
  
  const response = await fetch('/api/databricks/query', {
    method: 'POST',
    body: JSON.stringify({ query, warehouse_id: process.env.WAREHOUSE_ID })
  });
  
  return await response.json();
}

// Usage in React component
const { data } = useTVF({
  function: 'get_top_workspaces_by_cost',
  params: {
    start_date: '2024-11-01',
    end_date: '2024-11-30',
    top_n: 10
  }
});
```

**UI Component:**
```typescript
// components/TopWorkspacesTable.tsx
export function TopWorkspacesTable({ startDate, endDate, topN = 10 }) {
  const { data, loading } = useTVF({
    function: 'get_top_workspaces_by_cost',
    params: { start_date: startDate, end_date: endDate, top_n: topN }
  });
  
  return (
    <Table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Workspace</th>
          <th align="right">Total Cost</th>
          <th align="right">% of Total</th>
        </tr>
      </thead>
      <tbody>
        {data?.map(row => (
          <tr key={row.workspace_id}>
            <td>{row.rank}</td>
            <td>{row.workspace_name}</td>
            <td align="right">{formatCurrency(row.total_cost)}</td>
            <td align="right">
              <ProgressBar value={row.pct_of_total} max={100} />
              {row.pct_of_total}%
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
```

#### Pattern 3: Lakehouse Monitoring Integration

**Purpose:** Data quality and drift metrics visualization

**Backend Monitor Output Tables:**
```
observability.gold_monitoring.fact_cost_daily_profile_metrics
  - Contains AGGREGATE custom metrics (e.g., total_daily_cost, avg_cost_per_workspace)
  - Slicing: workspace_id, sku_name
  - Granularity: Daily

observability.gold_monitoring.fact_cost_daily_drift_metrics
  - Contains DRIFT metrics comparing current vs baseline window
  - Metrics: cost_drift_pct, cost_distribution_ks_test
```

**Frontend Query for Drift Chart:**
```sql
-- Drift metrics for last 30 days
SELECT 
  window.end as date,
  CAST(drift_metrics['cost_drift_pct'] AS DOUBLE) as cost_drift_pct,
  CAST(drift_metrics['cost_distribution_ks_test'] AS DOUBLE) as ks_statistic
FROM observability.gold_monitoring.fact_cost_daily_drift_metrics
WHERE window.end >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND column_name = ':table'  -- Table-level drift
ORDER BY window.end;
```

**UI Component:**
```typescript
// components/DriftChart.tsx
export function DriftChart({ tableName, metric, threshold = 0.2 }) {
  const { data } = useLakehouseMonitoring({
    table: tableName,
    metricType: 'drift',
    metric: metric,  // e.g., 'cost_drift_pct'
    days: 30
  });
  
  return (
    <Card>
      <CardHeader>
        <Title>Cost Drift Detection</Title>
        <Subtitle>Threshold: {threshold * 100}%</Subtitle>
      </CardHeader>
      <LineChart
        data={data}
        x="date"
        y="cost_drift_pct"
        threshold={{
          value: threshold,
          color: 'red',
          label: 'Alert Threshold'
        }}
        annotations={data
          .filter(d => d.cost_drift_pct > threshold)
          .map(d => ({
            x: d.date,
            label: '⚠️ Drift Detected'
          }))}
      />
    </Card>
  );
}
```

**Figma Design for Drift Visualization:**
```
┌────────────────────────────────────────────────────────┐
│ Cost Drift Detection                  Threshold: 20%   │
├────────────────────────────────────────────────────────┤
│                                                        │
│   %  │                    ●  ←  Drift spike (Nov 15)  │
│  40  │                   ╱ ╲                           │
│      │                  ╱   ╲                          │
│  20  │ ─ ─ ─ ─ ─ ─ ─ ─●─ ─ ─●─ ← Threshold line       │
│      │      ●     ●   ╱       ╲                        │
│   0  │─────●─────●───●─────────●──────●──────         │
│      └────────────────────────────────────────         │
│       Nov 1        Nov 15          Nov 30              │
│                                                        │
│ 🔍 Analysis:                                           │
│ • 2 drift events detected                              │
│ • Peak drift: +38% on Nov 15                          │
│ • Root cause: Workspace "Prod" cost anomaly           │
│                                                        │
│ [View Detailed Report] [Configure Alert]              │
└────────────────────────────────────────────────────────┘

Design Specs:
  Chart Height: 300px
  Line Color: Databricks-Primary-500 (2px solid)
  Threshold Line: Databricks-Red-500 (2px dashed)
  Breach Points: Red circle marker (16px) + annotation
  Background: White
  Grid: Horizontal lines, Databricks-200
```

#### Pattern 4: ML Model Inference Integration

**Purpose:** Display ML predictions (cost forecasts, anomalies)

**Backend Inference Table:**
```
observability.gold.ml_cost_forecast_inference
  - Model: cost_forecasting_model
  - Predictions: forecasted_cost, confidence_lower, confidence_upper
  - Updated: Daily at 2 AM
```

**Frontend Query:**
```sql
SELECT 
  forecast_date,
  forecasted_cost,
  confidence_lower,
  confidence_upper,
  prediction_timestamp
FROM observability.gold.ml_cost_forecast_inference
WHERE workspace_id = :workspace_id
  AND forecast_date BETWEEN CURRENT_DATE() AND CURRENT_DATE() + INTERVAL 30 DAYS
ORDER BY forecast_date;
```

**UI Component:**
```typescript
// components/CostForecastChart.tsx
export function CostForecastChart({ workspaceId }) {
  const { actual } = useCostHistory({ workspaceId, days: 30 });
  const { forecast } = useCostForecast({ workspaceId, days: 30 });
  
  return (
    <Card>
      <Title>30-Day Cost Forecast</Title>
      <ComboChart
        data={[...actual, ...forecast]}
        series={[
          {
            name: 'Actual Cost',
            type: 'line',
            data: actual,
            color: 'Databricks-Primary-500',
            style: 'solid'
          },
          {
            name: 'Forecast',
            type: 'line',
            data: forecast,
            color: 'Databricks-Orange-500',
            style: 'dashed'
          },
          {
            name: 'Confidence Interval',
            type: 'area',
            data: forecast,
            yMin: 'confidence_lower',
            yMax: 'confidence_upper',
            color: 'Databricks-Orange-200',
            opacity: 0.3
          }
        ]}
        xAxis={{ field: 'date', label: 'Date' }}
        yAxis={{ field: 'cost', label: 'Cost (USD)', format: 'currency' }}
      />
      <Insight>
        📈 Forecast predicts +15% cost increase next week
      </Insight>
    </Card>
  );
}
```

**Figma Forecast Chart Design:**
```
┌────────────────────────────────────────────────────────┐
│ 30-Day Cost Forecast                                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  $  │                           ╱ ╱ ╱  ← Forecast     │
│ 60K │                        ╱ ╱ ╱                     │
│     │                     ╱ ╱ ╱  [Shaded area =        │
│ 40K │────────●────●────● ╱ ╱      confidence interval]│
│     │  Actual ──────────╱                              │
│ 20K │                                                  │
│     │                  │                               │
│   0 └──────────────────┼───────────────────           │
│     Nov 1          Today          Dec 1                │
│                                                        │
│ 📈 Insight: Forecast predicts +15% cost increase      │
│             Budget threshold: $55K (Nov 28)           │
│                                                        │
│ [Set Alert at Threshold] [Export Forecast]            │
└────────────────────────────────────────────────────────┘

Design Specs:
  Actual Line: Databricks-Primary-500, 3px solid
  Forecast Line: Databricks-Orange-500, 3px dashed
  Confidence Area: Databricks-Orange-200, 30% opacity
  Vertical Divider: Today line (Databricks-900, 1px dashed)
  Annotations: Budget threshold (Red dashed horizontal)
```

---

### Advanced Visualization Patterns

#### Pattern 1: Drill-Through Navigation

**Interaction:** Click chart → Navigate to detailed view

**Example: Cost Trend Chart → Daily Breakdown**

**Step 1: Overview Chart (clickable)**
```typescript
<LineChart
  data={monthlyCostData}
  onClick={(dataPoint) => {
    router.push(`/cost/daily?date=${dataPoint.date}&workspace=${dataPoint.workspace_id}`);
  }}
  cursor="pointer"
/>
```

**Step 2: Detail Page (drilled-down view)**
```
URL: /cost/daily?date=2024-11-15&workspace=prod-12345

┌────────────────────────────────────────────────────────┐
│ ← Back to Overview                                     │
│                                                        │
│ Cost Breakdown: Nov 15, 2024 - Workspace "Production" │
├────────────────────────────────────────────────────────┤
│ Total: $42,387 (+38% vs Nov 14)                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│ [Stacked Bar Chart by Hour]                           │
│                                                        │
├────────────────────────────────────────────────────────┤
│ Top Cost Drivers:                                      │
│ 1. Job: ETL_daily         $12,450  (29%)              │
│ 2. Warehouse: BI          $8,200   (19%)              │
│ 3. Job: ML_training       $6,800   (16%)              │
│ ...                                                    │
└────────────────────────────────────────────────────────┘
```

**Figma Breadcrumb Design:**
```
← Back to Overview

Font: 14px / 500 weight / Databricks-Primary-600
Icon: Arrow left (16px)
Hover: Underline + Databricks-Primary-800
Padding: 12px 0
```

#### Pattern 2: Conditional Row Highlighting (Table)

**Real Pattern from Governance Hub "Top Queried Tables":**

**Highlight Rules:**
1. **High Priority:** Row background Red-50 if `priority_score >= 80`
2. **Missing Tags:** Tag count cell Red-700 text + ⚠️ icon if `tag_count = 0`
3. **Recently Accessed:** Green dot indicator if `last_access_date < 24 hours`

**Figma Table Row Design:**
```
Normal Row:
┌──────────────┬──────────┬────────┬──────────┐
│ sales_fact   │ 12,450   │ 0 ⚠️   │ 85       │
└──────────────┴──────────┴────────┴──────────┘
  White background

High Priority Row:
┌──────────────┬──────────┬────────┬──────────┐
│ user_events  │ 45,200   │ 0 ⚠️   │ 92       │
└──────────────┴──────────┴────────┴──────────┘
  Red-50 background, Red-700 text for tag count

Recently Accessed Row:
● ┌──────────────┬──────────┬────────┬──────────┐
  │ orders_dim   │ 8,300    │ 3      │ 65       │
  └──────────────┴──────────┴────────┴──────────┘
    Green dot (8px) in left margin
```

#### Pattern 3: Sparklines in Table Cells

**Real Pattern from Jobs Dashboard (trend mini-charts):**

**Use Case:** Show 7-day cost trend in table cell

**Figma Cell Design:**
```
┌──────────────────────────────────┐
│ $12,450          ╱╲ ╱            │ ← Sparkline (80px × 24px)
│                ╱  ▼╲╱             │   Green if trending down
└──────────────────────────────────┘   Red if trending up

Design Specs:
  Sparkline Height: 24px
  Sparkline Width: 80px
  Line Width: 1.5px
  Color: Green-600 (down trend) / Red-600 (up trend)
  No axes or labels
  Padding: 8px right margin
```

**Implementation:**
```typescript
// components/SparklineCell.tsx
export function SparklineCell({ values, trend }) {
  return (
    <td className="sparkline-cell">
      <Value>{formatCurrency(values[values.length - 1])}</Value>
      <Sparkline
        data={values}
        width={80}
        height={24}
        color={trend === 'up' ? 'red' : 'green'}
      />
    </td>
  );
}
```

#### Pattern 4: Time Range Picker (Global Filter)

**Real Pattern from Account Usage Dashboard:**

**Figma Design:**
```
┌────────────────────────────────────────────────────┐
│ Time Range:  [Last 30 days ▾]  [Custom...]        │
└────────────────────────────────────────────────────┘

Dropdown Options:
  • Today
  • Yesterday
  • Last 7 days
  • Last 30 days ✓ (selected)
  • Last 90 days
  • Month to date
  • Quarter to date
  • Year to date
  ─────────────────
  • Custom range...

Custom Range Modal:
┌──────────────────────────────────┐
│ Custom Date Range         ✕      │
├──────────────────────────────────┤
│                                  │
│ Start Date:                      │
│ [Nov 1, 2024     📅]             │
│                                  │
│ End Date:                        │
│ [Nov 30, 2024    📅]             │
│                                  │
│           [Cancel] [Apply]       │
└──────────────────────────────────┘
```

**Design Specs:**
```
Trigger Button:
  Height: 40px
  Padding: 8px 16px
  Border: 1px Databricks-300
  Border Radius: 8px
  Font: 14px / 500 weight / Databricks-700
  Icon: Chevron down (16px)

Selected State:
  Border: 2px Databricks-Primary-500
  Background: Databricks-Primary-50
```

---

### Agent Integration Patterns

#### Agent Tool Call Visualization

**Real Pattern from Cost Agent (10_cost_agent.md):**

**Agent Available Tools:**
1. `get_cost_breakdown` - Retrieve cost by workspace/SKU
2. `detect_cost_spike` - Identify anomalous cost increases
3. `analyze_job_cost` - Deep dive into specific job costs
4. `forecast_cost` - ML-powered cost prediction
5. `create_cost_alert` - Create threshold-based alert

**Chat Bubble with Tool Execution:**
```
┌────────────────────────────────────────────────────────┐
│ User: Why did cost increase 40% this week?            │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Agent: Analyzing cost spike in Production workspace...│
│                                                        │
│ 🔧 Tools Used:                                         │
│   ✅ get_cost_breakdown (0.8s)                         │
│   ✅ detect_cost_spike (1.2s)                          │
│   ✅ analyze_job_cost (0.6s)                           │
│   [Show SQL Queries ▾]                                 │
│                                                        │
│ 🔍 Analysis Results:                                   │
│                                                        │
│ Cost increased 42% ($18.5K → $26.3K) Nov 8-15.       │
│                                                        │
│ Root Cause:                                            │
│ • Job "ETL_daily" runtime +3.2x (2.1h → 6.8h)        │
│ • Caused by data volume spike (+89%)                  │
│ • No code changes detected                            │
│                                                        │
│ [Cost Breakdown Chart - inline, 400px × 200px]        │
│                                                        │
│ 💡 Recommendations:                                    │
│ 1. Optimize query in ETL job (JOIN on partition key)  │
│ 2. Add Z-ORDER on frequently filtered columns         │
│ 3. Set alert for >20% daily cost increase             │
│                                                        │
│ [Create Alert] [View Job Details] [Export Report]     │
└────────────────────────────────────────────────────────┘
```

**Expandable Tool Details:**
```
┌────────────────────────────────────────────────────────┐
│ 🔧 Tools Used: [Show SQL Queries ▾]                    │
│                                                        │
│ ▼ get_cost_breakdown (0.8s)                            │
│   Query:                                               │
│   ```sql                                               │
│   SELECT workspace_id, sku_name,                       │
│          SUM(cost_amount) as total_cost                │
│   FROM observability.gold.fact_cost_daily              │
│   WHERE date BETWEEN '2024-11-08' AND '2024-11-15'    │
│   GROUP BY 1, 2;                                       │
│   ```                                                  │
│   Results: 127 rows returned                           │
│                                                        │
│ ▼ detect_cost_spike (1.2s)                             │
│   Model: cost_anomaly_detection_rf                     │
│   Threshold: 2.5 std deviations                        │
│   Result: Anomaly score 3.8 (HIGH)                     │
│                                                        │
│ ▼ analyze_job_cost (0.6s)                              │
│   Job ID: job-12345-etl-daily                          │
│   Query: [Metric View] job_performance_metrics         │
│   ...                                                  │
└────────────────────────────────────────────────────────┘

Design Specs:
  Background: Databricks-100
  Border: 1px Databricks-200
  Border Radius: 8px
  Padding: 16px
  Font: Monospace (code blocks), 12px
  Syntax Highlighting: SQL keywords (Databricks-Primary-600)
```

#### Agent Suggested Actions

**Pattern:** Agent provides actionable buttons after analysis

**Figma Button Group:**
```
[Create Alert] [View Job Details] [Export Report]

Button Design:
  Primary Action: Databricks-Primary-500 background (Create Alert)
  Secondary Actions: Outlined Databricks-Primary-500 border
  Height: 36px
  Padding: 8px 16px
  Border Radius: 8px
  Gap: 8px between buttons
  
Hover:
  Primary: Databricks-Primary-700
  Secondary: Databricks-Primary-50 background
```

**Action Outcomes:**

1. **Create Alert:** Opens alert configuration modal (pre-filled)
```
┌──────────────────────────────────────────┐
│ Create Cost Alert                ✕       │
├──────────────────────────────────────────┤
│ Alert Name:                              │
│ [Production Workspace Cost >20%]         │
│                                          │
│ Resource:                                │
│ [Workspace: Production      ▾]           │
│                                          │
│ Metric:                                  │
│ [Daily Cost Increase %      ▾]           │
│                                          │
│ Threshold:                               │
│ [20] % increase                          │
│                                          │
│ Notification:                            │
│ ☑ Email: platform-team@company.com       │
│ ☑ Slack: #cost-alerts                    │
│                                          │
│         [Cancel] [Create Alert]          │
└──────────────────────────────────────────┘
```

2. **View Job Details:** Navigate to job detail page
```
URL: /performance/jobs/job-12345-etl-daily

Breadcrumb: Performance Hub > Jobs > ETL_daily
```

3. **Export Report:** Download PDF with analysis
```
Toast Notification:
┌────────────────────────────────┐
│ ✅ Report exported             │
│ cost-analysis-nov15.pdf        │
│ [Download]                     │
└────────────────────────────────┘
```

---

### Expert SQL Pattern Visualizations

#### Pattern 1: Query Efficiency Ratio (from Cody Austin Davis)

**Concept:** `efficiency_ratio = results_returned / rows_scanned`

**UI Visualization:**
```
┌────────────────────────────────────────────────────────┐
│ Query Efficiency Distribution                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Efficient (>50%)          [████████████░░] 65%        │
│ Moderate (10-50%)         [████░░░░░░░░░░] 25%        │
│ Inefficient (<10%)        [██░░░░░░░░░░░░] 10%        │
│                                                        │
│ Recommendations:                                       │
│ • 47 queries scan >100M rows but return <1K            │
│ • Suggest adding WHERE clauses or materialized views   │
│                                                        │
│ [View Inefficient Queries]                             │
└────────────────────────────────────────────────────────┘

Design:
  Progress Bars: Height 32px, Green/Yellow/Red
  Percentages: 16px / 600 weight / right-aligned
  Recommendations: Bulleted list, 14px / Databricks-700
```

#### Pattern 2: Time-Proportional Cost Allocation

**Concept:** Allocate warehouse cost based on query duration proportion

**UI Card:**
```
┌────────────────────────────────────────────────────────┐
│ Warehouse Cost Allocation                              │
│ Warehouse: Analytics (Nov 15, 2024)                    │
├────────────────────────────────────────────────────────┤
│ Total Warehouse Cost: $1,240                           │
│                                                        │
│ Top Queries by Allocated Cost:                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Query ID     │ Duration │ % of Time │ Alloc Cost │ │
│ ├──────────────┼──────────┼───────────┼────────────┤ │
│ │ abc123       │ 45.2m    │ 18.5%     │ $229       │ │
│ │ def456       │ 32.8m    │ 13.4%     │ $166       │ │
│ │ ghi789       │ 28.1m    │ 11.5%     │ $143       │ │
│ │ ...          │ ...      │ ...       │ ...        │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ 💡 Insight: Top 10 queries account for 68% of cost    │
│                                                        │
│ [Optimize Queries] [Export Full Report]               │
└────────────────────────────────────────────────────────┘

Design:
  Table Font: Monospace for Query ID, 14px
  Duration: Right-aligned
  % of Time: Progress bar + percentage
  Allocated Cost: Right-aligned, bold
```

#### Pattern 3: Governance Prioritization by Query Frequency

**Real Pattern from Governance Hub:**

**Concept:** Prioritize tables for governance based on usage frequency

**UI Table:**
```
┌────────────────────────────────────────────────────────┐
│ Top Queried Tables Without Tags                       │
│ (Governance Priority Score = query_count × age)        │
├────────────────────────────────────────────────────────┤
│ Table Name        │ Queries │ Tags │ Priority │ Action│
│                   │ (30d)   │      │ Score    │       │
├───────────────────┼─────────┼──────┼──────────┼───────┤
│ sales_fact        │ 12,450  │ 0 ⚠️ │ 92       │[Tag]  │
│ user_events       │ 8,320   │ 0 ⚠️ │ 85       │[Tag]  │
│ inventory_snapshot│ 6,780   │ 1    │ 71       │[Tag]  │
│ orders_dim        │ 4,200   │ 0 ⚠️ │ 68       │[Tag]  │
│ ...               │ ...     │ ...  │ ...      │ ...   │
└────────────────────────────────────────────────────────┘

Conditional Formatting:
  • Priority >= 80: Row background Red-50
  • Tags = 0: Red-700 text + ⚠️ icon
  • Queries > 10K: Bold font

Action Button:
  [Tag] → Opens tag editor modal
```

---

### Production-Ready Component Specifications

#### Component 1: Multi-Tab Dashboard

**Use Case:** Switch between Cost / Performance / Security views

**Figma Tab Bar:**
```
┌────────────────────────────────────────────────────────┐
│ [Cost] [Performance] [Security] [Reliability]          │
└────────────────────────────────────────────────────────┘
  Active Tab: Databricks-Primary-500 background
              White text, 3px bottom border
  Inactive Tab: Transparent background
                Databricks-600 text
                1px bottom border Databricks-200
  
  Height: 48px
  Padding: 12px 24px per tab
  Font: 14px / 600 weight
  
  Hover (inactive): Databricks-Primary-50 background
```

**Tab Content Area:**
```
┌────────────────────────────────────────────────────────┐
│ [Tab Bar]                                              │
├────────────────────────────────────────────────────────┤
│                                                        │
│ [Tab Content - changes based on selection]            │
│                                                        │
│                                                        │
└────────────────────────────────────────────────────────┘

Padding: 24px
Background: Databricks-50
Min Height: 600px
```

#### Component 2: Alert History Timeline

**Use Case:** Show alert firing history with context

**Figma Timeline:**
```
┌────────────────────────────────────────────────────────┐
│ Alert History: "Production Workspace Cost >$10K"       │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Nov 15, 2:30 PM  ●  Cost: $12,450 (+24%)              │
│      │               Threshold: $10,000                │
│      │               [View Details]                    │
│      │                                                 │
│ Nov 12, 8:15 AM  ●  Cost: $11,200 (+12%)              │
│      │               Threshold: $10,000                │
│      │               [View Details]                    │
│      │                                                 │
│ Nov 8, 3:00 PM   ○  Alert created                     │
│                                                        │
└────────────────────────────────────────────────────────┘

Design:
  Timeline Line: 2px Databricks-300 vertical line
  
  Fired Event (●):
    Circle: 16px, Red-500 fill
    Label: 14px / 600 weight / Databricks-900
    Details: 12px / 400 weight / Databricks-600
    Button: 12px / Databricks-Primary-600 link
  
  Created Event (○):
    Circle: 16px, Databricks-300 border, white fill
    Label: 14px / 400 weight / Databricks-600
```

#### Component 3: Inline Chart in Agent Chat

**Use Case:** Display chart within agent response bubble

**Figma Design:**
```
Agent Message Bubble:
┌────────────────────────────────────────────────────────┐
│ Cost increased 42% week-over-week.                     │
│                                                        │
│ [Inline Cost Chart - 400px × 200px]                    │
│  $  │                    ╱╲                            │
│ 30K │               ╱╲  ╱  ╲                           │
│     │          ╱╲  ╱  ╲╱    ╲                          │
│ 20K │     ╱╲  ╱  ╲╱            ╲                        │
│     │────╱──╲╱─────────────────╲───                   │
│ 10K │                                                  │
│     └──────────────────────────────                   │
│     Nov 1  Nov 8  Nov 15  Nov 22                       │
│                                                        │
│ Peak: $26.3K on Nov 15 (↑42% vs Nov 8)               │
└────────────────────────────────────────────────────────┘

Chart Specs:
  Width: 400px (max 85% of chat width)
  Height: 200px
  Background: White
  Border: 1px Databricks-200
  Border Radius: 8px
  Padding: 16px
  
  Line: 2px Databricks-Primary-500
  Grid: 1px Databricks-100
  Axes: 12px Databricks-600
  
  Annotations: Red circle marker at peak + label
```

#### Component 4: Global Context Bar (Workspace + Time Filter)

**Use Case:** Persistent filter bar across all pages

**Figma Design:**
```
┌────────────────────────────────────────────────────────┐
│ Workspace: [Production ▾]  Time: [Last 30d ▾]  Apply  │
└────────────────────────────────────────────────────────┘

Position: Sticky top (below main nav)
Background: White
Border Bottom: 1px Databricks-200
Height: 56px
Padding: 8px 24px
Shadow: Elevation 1

Dropdowns: 
  Width: 200px (workspace), 160px (time)
  Height: 40px
  Gap: 16px between dropdowns

Apply Button:
  Primary button style
  Only enabled if filters changed
```

---

## 📚 Complete Component Inventory

### Dashboard Components (25 total)

1. **KPI Counter** - Large number with trend
2. **Sparkline Chart** - Mini trend line (80px × 24px)
3. **Line Chart** - Multi-series time series
4. **Stacked Bar Chart** - Category breakdown
5. **Heatmap** - 2D density visualization
6. **Donut Chart** - Category proportions
7. **Data Table** - Sortable, paginated
8. **Metric Card** - Small KPI (200px × 120px)
9. **Status Badge** - Color-coded severity
10. **Alert Banner** - Page-level notifications
11. **Time Range Picker** - Global date filter
12. **Workspace Selector** - Multi-select dropdown
13. **Breadcrumb Nav** - Drill-down navigation
14. **Tab Bar** - View switcher
15. **Modal Dialog** - Alert wizard, confirmations
16. **Toast Notification** - Success/error messages
17. **Tooltip** - Hover details
18. **Progress Bar** - Linear progress (0-100%)
19. **Loading Skeleton** - Shimmer placeholder
20. **Empty State** - No data placeholder
21. **Error State** - Failed to load
22. **Pagination Controls** - Table navigation
23. **Search Bar** - Filter tables
24. **Action Button Group** - Primary/secondary actions
25. **Inline Chart** - Chart in text (agent chat)

### Agent Components (10 total)

26. **Chat Input Field** - Multiline text input
27. **User Message Bubble** - Right-aligned
28. **Agent Message Bubble** - Left-aligned with tools
29. **Tool Execution Panel** - Expandable SQL/results
30. **Suggested Questions** - Clickable pills
31. **Typing Indicator** - Agent thinking animation
32. **Agent Avatar** - 32px icon
33. **Action Button Row** - Post-analysis actions
34. **Inline Chart in Chat** - 400px × 200px
35. **Insight Callout** - 💡 highlighted message

### Form Components (10 total)

36. **Text Input** - Single line
37. **Text Area** - Multi-line
38. **Dropdown Select** - Single choice
39. **Multi-Select** - Checkboxes
40. **Radio Group** - Exclusive choice
41. **Toggle Switch** - Boolean setting
42. **Date Picker** - Calendar selector
43. **Slider** - Numeric range (threshold)
44. **Tag Input** - Comma-separated values
45. **File Upload** - Import config

### Navigation Components (5 total)

46. **Side Nav** - Persistent left nav
47. **Top Nav** - Logo + user menu
48. **Breadcrumb** - Page hierarchy
49. **Footer** - Links + version
50. **Mobile Menu** - Hamburger collapsible

---

**END OF ENHANCED DESIGN PROMPT**

*This comprehensive prompt integrates real Databricks Lakeview dashboard patterns, metric view semantics, table-valued function parameterization, Lakehouse Monitoring drift visualizations, ML model forecast displays, and expert SQL pattern UI representations. It provides complete specifications for a designer or design AI to generate a production-ready Figma design system for the Databricks Health Monitoring Platform.*

