# 05 - Executive Overview (Home)

## Overview

The first screen users see - provides situational awareness and fast triage.

---

## 📋 Design Prompt

**Copy this prompt:**

```
Design the EXECUTIVE OVERVIEW (Home) page for Databricks Health Monitor.

This is the first thing users see - fast triage and situational awareness.

=== LAYOUT (1440px wide) ===

┌─────────────────────────────────────────────────────────────────────────────────┐
│ [☰] Databricks Health Monitor    [🕐 Last 24h ▼] [🔔 7] [🤖 Ask AI] [Settings] │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🤖 Good morning! Here's what I'm tracking for you:                   [Hide]││
│  │                                                                             ││
│  │ • 🔴 3 critical issues need attention (2 cost spikes, 1 job failure chain)││
│  │ • 🟡 I predict ml-workspace will exceed budget by Thursday               ││
│  │ • ✨ Your job success rate improved 3% this week - nice work!            ││
│  │                                                                             ││
│  │ [Fix Critical Issues] [See Forecast] [View Full Report]                    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ════════════════════════ PRIMARY METRICS ═══════════════════════════════════   │
│                                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ Health Score │ │ Cost Today   │ │ Active Alerts│ │ SLA Status   │           │
│  │     87/100   │ │   $45,230    │ │     7        │ │   98.2%      │           │
│  │   ▁▂▃▄▅▆▇▆▅  │ │   ↑12% 🔴   │ │  3 Critical  │ │   ↑0.5% 🟢   │           │
│  │ 🤖 Stable    │ │ 🤖 Anomaly   │ │ 🤖 Trending ↑│ │ 🤖 On track  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                                  │
│  ════════════════════════ DOMAIN HEALTH ════════════════════════════════════   │
│                                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ 💰 Cost    │ │ ⚡ Reliab. │ │ 🚀 Perf.   │ │ 🔒 Security│ │ 📊 Quality │   │
│  │  $45K/day  │ │  96.2%     │ │  1.2s p95  │ │  5 issues  │ │  94.2%     │   │
│  │  ↑12% 🔴   │ │  ↑0.8% 🟢  │ │  ↓0.3s 🟢  │ │  2 HIGH 🔴 │ │  ↑1.2% 🟢  │   │
│  │  [View →]  │ │  [View →]  │ │  [View →]  │ │  [View →]  │ │  [View →]  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                                  │
│  ════════════════════════ TOP ALERTS ════════════════════════════════════════   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ Severity │ Alert                        │ Domain       │ Started  │ Actions││
│  ├──────────┼──────────────────────────────┼──────────────┼──────────┼────────┤│
│  │ 🔴 CRIT  │ Cost spike: +308% ($4,890)  │ 💰 Cost      │ 3m ago   │ [Fix]  ││
│  │ 🔴 CRIT  │ Job failure cascade (5 jobs)│ ⚡ Reliability│ 12m ago  │ [Fix]  ││
│  │ 🔴 HIGH  │ Suspicious API access       │ 🔒 Security  │ 1h ago   │ [View] ││
│  │ 🟡 MED   │ Query latency p99 > 10s     │ 🚀 Performance│2h ago   │ [View] ││
│  │ 🟡 MED   │ SLA breach risk: etl-daily  │ ⚡ Reliability│ 30m ago  │ [Fix]  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│  [View All 7 Active Alerts →]                                                   │
│                                                                                  │
│  ════════════════════════ TRENDS (7 DAYS) ══════════════════════════════════   │
│                                                                                  │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐│
│  │ Daily Cost          │ │ Job Failures        │ │ Query Latency (p95) │ │ Data Quality        ││
│  │ ▁▂▃▄▅▆▇▆▅▄▃▂▁      │ │ ▇▆▅▄▃▂▁▂▃▄▃▂▁      │ │ ▃▄▅▄▃▂▁▂▃▂▁▂▁      │ │ ▁▂▃▄▅▆▆▆▇▇▇▇▇      ││
│  │ $312K total         │ │ 89 total ↓12% 🟢    │ │ 1.2s avg ↓0.3s 🟢   │ │ 94.2% avg ↑1.2% 🟢 ││
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘│        │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘             │
│                                                                                  │
│  ════════════════════════ AI RECOMMENDED ACTIONS ════════════════════════════   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ # │ Action                          │ Impact   │ Effort │ Confidence │      ││
│  ├───┼─────────────────────────────────┼──────────┼────────┼────────────┼──────┤│
│  │ 1 │ Add timeout to train-llm-v3     │ $2K/mo   │ 5 min  │ 95%        │[Run] ││
│  │ 2 │ Terminate idle clusters (3)     │ $890/mo  │ 1 min  │ 100%       │[Run] ││
│  │ 3 │ Fix missing tags (22 resources) │ Audit    │ 15 min │ 90%        │[Run] ││
│  │ 4 │ Increase memory: etl-daily      │ -3 fails │ 2 min  │ 87%        │[Run] ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│  [View All Recommendations →]                                                   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

=== COMPONENT SPECS ===

AI INSIGHT BANNER:
- Position: Top of content area
- Background: Gradient from #3B82F6/10 to transparent
- Border-left: 4px solid #3B82F6
- Dismissible but persistent per session
- Height: ~100px

PRIMARY METRICS ROW (4 cards):
- Layout: 4 cards in a row (25% width each, with gaps)
- Width: ~270px each
- Height: 140px
- Sparkline: 40px height, 7-day data
- AI insight: Small text at bottom (#3B82F6)
- Border-radius: 12px
- Shadow: subtle elevation

DOMAIN HEALTH ROW (5 cards):
- Layout: 5 cards in a row (20% width each, with gaps)
- Width: ~215px each
- Height: 120px
- Domain icon: 24px emoji or icon
- Domain color accent (top border or left border)
- [View →] link in each card
- Clickable → navigates to domain page

TOP ALERTS TABLE:
- Columns: Severity, Alert, Domain, Started, Actions
- Row height: 48px
- Domain column: Shows domain icon + color
- Severity pill: 64px width, color-coded
- Hover: Highlight row

TRENDS ROW (4 charts):
- Layout: 4 charts in a row (25% width each)
- Width: ~270px each
- Height: 100px
- Sparkline with subtle area fill
- Mini metric + trend indicator below

RECOMMENDED ACTIONS:
- Table format with confidence bars
- "Run" button executes playbook
- Sorted by impact

=== GRID SUMMARY ===

Row 1: AI Insight Banner (full width)
Row 2: Primary Metrics (4 cards) 
Row 3: Domain Health (5 cards)
Row 4: Top Alerts Table (full width)
Row 5: Trends (4 charts)
Row 6: Recommended Actions (full width)

=== INTERACTIONS ===

- Global time picker in header (persists across pages)
- Primary metric tiles: Click → Navigate to relevant page
- Domain cards: Click → Navigate to domain page
- Alert row: Click → Navigate to alert detail
- Trend chart: Hover for tooltip, Click → Navigate to domain
- Action "Run": Executes with confirmation dialog

Provide complete high-fidelity design.
```

---

## 📐 Key Measurements

| Element | Specification |
|---------|---------------|
| Page width | 1440px |
| Sidebar | 240px (not shown in this wireframe) |
| Content area | ~1200px (with 24px margins) |
| Header height | 64px |
| Primary Metric card | ~270px × 140px (4 per row) |
| Domain Health card | ~215px × 120px (5 per row) |
| Trend chart | ~270px × 100px (4 per row) |
| Table row height | 48px |
| Card gap | 16px |
| Section gap | 24px |

---

## ✅ Checklist

- [ ] AI insight banner at top (full width)
- [ ] 4 Primary Metric cards with sparklines (symmetric row)
- [ ] 5 Domain Health cards with domain icons (symmetric row)
- [ ] Top alerts table (5 rows visible, domain column)
- [ ] 4 Trend mini-charts (symmetric row)
- [ ] Recommended actions table
- [ ] All "🤖" AI attribution visible
- [ ] All rows are visually balanced

---

## 📚 PRD Reference

For detailed specifications, see: [../prd/01-base-prd.md](../prd/01-base-prd.md) - Section 5.1: Dashboard Hub

---

**Next:** [06-global-explorer.md](06-global-explorer.md)

