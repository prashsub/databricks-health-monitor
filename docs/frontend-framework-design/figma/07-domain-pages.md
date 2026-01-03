# 07 - Domain Pages (5 Pages)

## Overview

Five domain-specific pages with consistent layout but domain-appropriate content:
- **Cost** - Spend analytics, waste, optimization
- **Reliability** - Jobs, pipelines, SLAs
- **Performance** - Latency, throughput, hotspots
- **Security** - Threats, access, compliance
- **Quality** - Freshness, schema, anomalies

---

## 📋 Template Prompt (Use for All 5)

**Copy and customize the `[DOMAIN]` placeholders:**

```
Design the [DOMAIN] DOMAIN PAGE for Databricks Health Monitor.

This is the domain-specific view for [DESCRIPTION].

=== LAYOUT (1440px wide) ===

┌─────────────────────────────────────────────────────────────────────────────────┐
│ [☰] Databricks Health Monitor    [🕐 Last 24h ▼] [🔔 7] [🤖 Ask AI] [Settings] │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [ICON] [DOMAIN NAME]                              [Export] [Create Alert] [⚙️] │
│  └─ Breadcrumb: Home > [Domain]                                                 │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🤖 [AI DOMAIN SUMMARY]                                              [More] ││
│  │ "[Personalized insight about this domain based on current data]"           ││
│  │ [Primary Action Button] [Secondary Action]                                  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ════════════════════════ KEY METRICS ═══════════════════════════════════════   │
│                                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ [METRIC 1]   │ │ [METRIC 2]   │ │ [METRIC 3]   │ │ [METRIC 4]   │           │
│  │    [VALUE]   │ │    [VALUE]   │ │    [VALUE]   │ │    [VALUE]   │           │
│  │   [CHANGE]   │ │   [CHANGE]   │ │   [CHANGE]   │ │   [CHANGE]   │           │
│  │  ▁▂▃▄▅▆▇▆▅  │ │  ▁▂▃▄▅▆▇▆▅  │ │  ▁▂▃▄▅▆▇▆▅  │ │  ▁▂▃▄▅▆▇▆▅  │           │
│  │ 🤖 [AI tip]  │ │ 🤖 [AI tip]  │ │ 🤖 [AI tip]  │ │ 🤖 [AI tip]  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                                  │
│  ════════════════════════ TREND ANALYSIS ════════════════════════════════════   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ [Main Time Series Chart - 400px height]                                     ││
│  │                                                                             ││
│  │    📈 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~         ││
│  │                                              ▲                              ││
│  │                                              │ 🤖 Anomaly detected:        ││
│  │                                              │    +45% above forecast      ││
│  │    ──────────────────────────────────────────┼───────────────────          ││
│  │                                              │ [Click for details]         ││
│  │                                                                             ││
│  │ Legend: ● Actual  ○ Forecast  --- Threshold                                 ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ════════════════════════ BREAKDOWN ═════════════════════════════════════════   │
│                                                                                  │
│  ┌──────────────────────────────────────┐ ┌────────────────────────────────────┐│
│  │ By [Dimension 1]         [View All]  │ │ By [Dimension 2]        [View All] ││
│  │                                      │ │                                    ││
│  │ ████████████████████  ml-ws   40%   │ │ ████████████████  GPU      35%    ││
│  │ ██████████████        prod    30%   │ │ ████████████      Memory   28%    ││
│  │ ██████████            dev     20%   │ │ ██████████        Compute  22%    ││
│  │ ██████                sandbox 10%   │ │ ████              Storage  15%    ││
│  │                                      │ │                                    ││
│  │ 🤖 ml-ws is 40% of total            │ │ 🤖 GPU up 25% vs last week       ││
│  └──────────────────────────────────────┘ └────────────────────────────────────┘│
│                                                                                  │
│  ════════════════════════ TOP ISSUES ════════════════════════════════════════   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ Severity │ Issue                      │ Impact     │ Status   │ Actions    ││
│  ├──────────┼────────────────────────────┼────────────┼──────────┼────────────┤│
│  │ 🔴 CRIT  │ [Issue 1 title]           │ [Impact]   │ 🔴 Open  │ [Fix]      ││
│  │ 🔴 HIGH  │ [Issue 2 title]           │ [Impact]   │ 🟡 In Prog│ [View]     ││
│  │ 🟡 MED   │ [Issue 3 title]           │ [Impact]   │ 🔴 Open  │ [Fix]      ││
│  │ 🟡 MED   │ [Issue 4 title]           │ [Impact]   │ 🔴 Open  │ [View]     ││
│  │ 🟢 LOW   │ [Issue 5 title]           │ [Impact]   │ 🟢 Muted │ [Unmute]   ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│  [View All Issues →]                                                            │
│                                                                                  │
│  ════════════════════════ AI RECOMMENDATIONS ════════════════════════════════   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🤖 Based on my analysis of your [domain], here are my top recommendations: ││
│  │                                                                             ││
│  │ 1. [Recommendation 1] - Impact: [value] - Confidence: 95%      [Apply]     ││
│  │ 2. [Recommendation 2] - Impact: [value] - Confidence: 90%      [Apply]     ││
│  │ 3. [Recommendation 3] - Impact: [value] - Confidence: 87%      [Apply]     ││
│  │                                                                             ││
│  │ [Show All Recommendations]                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

=== COMPONENT SPECS ===

AI SUMMARY BANNER:
- Same styling as Executive Overview
- Domain-specific personalized insight
- Action buttons based on current state

KPI TILES (4 tiles per domain):
- Same component as home page
- Domain-specific metrics
- Each has AI micro-insight

MAIN CHART:
- Height: 400px
- Shows actual vs forecast (where applicable)
- Clickable annotations for anomalies
- Legend below

BREAKDOWN CHARTS (2 side by side):
- Horizontal bar charts
- Show top 4 items + "Other"
- AI insight below each

ISSUES TABLE:
- Domain-filtered signals
- Same format as Global Explorer
- Quick actions

RECOMMENDATIONS:
- Numbered list
- Confidence percentage
- One-click apply

=== INTERACTIONS ===

- KPI click → Filter issues by that metric
- Chart hover → Show tooltip with details
- Annotation click → Navigate to Signal Detail
- Bar click → Filter by that dimension
- Issue row click → Signal Detail
- Apply button → Execute with confirmation

Provide complete high-fidelity design.
```

---

## 🔷 Cost Domain Specifics

**Replace placeholders with:**

| Placeholder | Cost Domain Value |
|-------------|-------------------|
| `[DOMAIN]` | Cost |
| `[ICON]` | 💰 |
| `[DESCRIPTION]` | Spend analytics, waste identification, and cost optimization |
| `[METRIC 1]` | Total Spend |
| `[METRIC 2]` | DBU Usage |
| `[METRIC 3]` | Waste Detected |
| `[METRIC 4]` | Forecast Delta |
| `[Dimension 1]` | Workspace |
| `[Dimension 2]` | SKU Type |
| `[Issue examples]` | Cost spikes, budget alerts, idle clusters |
| `[Recommendation examples]` | Terminate idle clusters, resize over-provisioned jobs |

---

## 🟠 Reliability Domain Specifics

**Replace placeholders with:**

| Placeholder | Reliability Domain Value |
|-------------|--------------------------|
| `[DOMAIN]` | Reliability |
| `[ICON]` | ⚙️ |
| `[DESCRIPTION]` | Job health, pipeline status, and SLA monitoring |
| `[METRIC 1]` | Success Rate |
| `[METRIC 2]` | Failed Jobs (24h) |
| `[METRIC 3]` | SLA Breaches |
| `[METRIC 4]` | Retry Rate |
| `[Dimension 1]` | Workspace |
| `[Dimension 2]` | Failure Type |
| `[Issue examples]` | Job failures, cascades, timeouts, SLA risks |
| `[Recommendation examples]` | Add retries, increase timeout, fix data dependency |

---

## 🟣 Performance Domain Specifics

**Replace placeholders with:**

| Placeholder | Performance Domain Value |
|-------------|--------------------------|
| `[DOMAIN]` | Performance |
| `[ICON]` | ⚡ |
| `[DESCRIPTION]` | System performance, latency, and resource utilization |
| `[METRIC 1]` | Avg Query Time |
| `[METRIC 2]` | P99 Latency |
| `[METRIC 3]` | Slow Queries |
| `[METRIC 4]` | CPU Utilization |
| `[Dimension 1]` | Warehouse |
| `[Dimension 2]` | Query Type |
| `[Issue examples]` | Slow queries, resource saturation, spills |
| `[Recommendation examples]` | Add clustering, optimize join, scale warehouse |

---

## 🔐 Security Domain Specifics

**Replace placeholders with:**

| Placeholder | Security Domain Value |
|-------------|------------------------|
| `[DOMAIN]` | Security |
| `[ICON]` | 🔒 |
| `[DESCRIPTION]` | Threat detection, access control, and compliance |
| `[METRIC 1]` | Security Score |
| `[METRIC 2]` | Open Findings |
| `[METRIC 3]` | Access Events |
| `[METRIC 4]` | Policy Violations |
| `[Dimension 1]` | Finding Type |
| `[Dimension 2]` | User/Principal |
| `[Issue examples]` | Suspicious access, data exfiltration risk, policy gaps |
| `[Recommendation examples]` | Enable audit logging, restrict public access, rotate secret |

---

## 🟩 Quality Domain Specifics

**Replace placeholders with:**

| Placeholder | Quality Domain Value |
|-------------|----------------------|
| `[DOMAIN]` | Quality |
| `[ICON]` | ✅ |
| `[DESCRIPTION]` | Data quality, freshness, and schema monitoring |
| `[METRIC 1]` | Quality Score |
| `[METRIC 2]` | Stale Tables |
| `[METRIC 3]` | Schema Drifts |
| `[METRIC 4]` | Null Rate |
| `[Dimension 1]` | Catalog |
| `[Dimension 2]` | Anomaly Type |
| `[Issue examples]` | Data staleness, schema drift, null spikes, duplicates |
| `[Recommendation examples]` | Fix pipeline, update schema, add validation |

---

## ✅ Checklist (Per Domain Page)

- [ ] Domain-specific AI summary banner
- [ ] 4 KPI tiles with sparklines and AI tips
- [ ] Main trend chart with annotations
- [ ] 2 breakdown bar charts
- [ ] Issues table (5 rows)
- [ ] AI recommendations section

---

## 📚 PRD References

| Domain | PRD Section |
|--------|-------------|
| Cost | [01-base-prd.md](../prd/01-base-prd.md) - Section 5.3 |
| Reliability | [01-base-prd.md](../prd/01-base-prd.md) - Section 5.4 |
| Performance | [02-ml-enhancements.md](../prd/02-ml-enhancements.md) - Section 3 |
| Security | [01-base-prd.md](../prd/01-base-prd.md) - Section 5.5 |
| Quality | [02-ml-enhancements.md](../prd/02-ml-enhancements.md) - Section 4 |

---

**Next:** [08-signal-detail.md](08-signal-detail.md)

