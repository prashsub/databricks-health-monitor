# 16 - Screen: Alert Center (Super Enhanced)

## Overview

Create a world-class Alert Center that rivals PagerDuty's incident dashboard and Grafana's alerting interface. This is where engineers manage alert rules, notification channels, and routing configurations.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create a world-class Alert Center for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Screen: Alert management center (rules, channels, routing)
- Users: Platform engineers configuring and managing alerts
- Mental model: "Control how I get notified about issues"
- Inspiration: PagerDuty, Grafana Alerting, Datadog Monitors
- Platform: Desktop web (1440px primary width)

Quality bar:
- PagerDuty-level incident management
- Grafana-level alerting configuration
- Datadog-level monitor organization
- Professional ops tooling quality

Objective (this run only):
- Create 1 complete screen with 3 tab views
- Use ONLY existing components
- NO new components
- Place in Screens section

Follow Guidelines.md for design system alignment.

---

SCREEN SPECIFICATIONS:

Canvas Size: 1440px x 1400px (scroll)
Background: #FAFAFA

---

LAYOUT STRUCTURE:

Header Section:
- Title: "Alert Center"
- Subtitle: "Configure alerts, notifications, and routing rules"
- Stats bar: 56 active rules, 4 channels, 8 routes
- Actions: [+ Create Alert] [Import] [Export]

Tab Bar:
[Alert Rules (56)] [Notification Channels (4)] [Routing Rules (8)]

---

TAB 1: ALERT RULES

Filter Bar:
- Search: "Search alert rules..."
- Filters: Domain, Severity, Status, Owner
- Active filters as chips
- Sort: Name, Created, Last Triggered

Alert Rules Table:

| Status | Name | Domain | Severity | Condition | Last Triggered | Owner | Actions |
|--------|------|--------|----------|-----------|----------------|-------|---------|
| ✓ | Cost threshold exceeded | Cost | Critical | spend > $30K/day | 2 hours ago | John S. | Edit/Pause/Delete |
| ✓ | Job failure rate spike | Reliability | High | failure_rate > 10% | 5 hours ago | Platform | Edit/Pause/Delete |
| ✓ | SQL Warehouse idle | Cost | Medium | idle > 2 hours | Yesterday | FinOps | Edit/Pause/Delete |
| ⏸ | Query duration anomaly | Performance | High | p95 > 3x baseline | Never | - | Edit/Enable/Delete |

Each row includes:
- Status indicator (green check or yellow pause)
- Alert name (clickable)
- Domain badge (Cost, Reliability, etc.)
- Severity badge (Critical/High/Medium/Low)
- Condition summary
- Last triggered (relative time)
- Owner avatar
- Actions menu

Bulk Actions (when selected):
[✓ Enable] [⏸ Pause] [🗑️ Delete] [📋 Duplicate] [👤 Assign]

---

TAB 2: NOTIFICATION CHANNELS

Channel Cards Grid (2x2):

Card 1: Slack
- Icon: Slack logo
- Status: Connected (green)
- Channel: #platform-alerts
- Last used: 2 hours ago
- Test result: Success
- [Test] [Edit] [Delete]

Card 2: Email
- Icon: Mail icon
- Status: Connected (green)
- Recipients: platform-team@company.com
- Last used: 5 hours ago
- [Test] [Edit] [Delete]

Card 3: PagerDuty
- Icon: PagerDuty logo
- Status: Connected (green)
- Service: Platform Engineering
- Last used: Yesterday
- [Test] [Edit] [Delete]

Card 4: Webhook
- Icon: Code icon
- Status: Warning (yellow)
- URL: https://api.internal.com/alerts
- Last used: 7 days ago
- Error: Timeout on last test
- [Test] [Edit] [Delete]

Add Channel Button:
[+ Add Channel]
Options: Slack, Email, PagerDuty, Webhook, Microsoft Teams, OpsGenie

---

TAB 3: ROUTING RULES

Routing Rules List:

Visual routing diagram at top showing flow:
Alert → Severity Check → Domain Match → Time Window → Channel

Rule 1 (Default - Critical):
- Priority: 1 (highest)
- Condition: severity = Critical
- Channels: Slack + PagerDuty + Email
- Time: 24/7
- Escalation: After 15 min if unacknowledged
- [Edit] [Delete]

Rule 2 (Cost Alerts):
- Priority: 2
- Condition: domain = Cost AND severity >= High
- Channels: Slack (#cost-alerts) + Email (finops@)
- Time: Business hours (9am-6pm Mon-Fri)
- [Edit] [Delete]

Rule 3 (Security Critical):
- Priority: 3
- Condition: domain = Security AND severity = Critical
- Channels: PagerDuty + Slack (#security-incidents)
- Time: 24/7
- Escalation: Immediate
- [Edit] [Delete]

Rule 4 (Default - All Others):
- Priority: 99 (catch-all)
- Condition: All unmatched alerts
- Channels: Slack (#platform-alerts)
- Time: Business hours
- [Edit] [Delete]

Add Rule Button:
[+ Add Routing Rule]

---

ALERT RULE DETAIL DRAWER (slide from right):

Header:
- Name: "Cost threshold exceeded"
- Status: Active (toggle)
- [Save] [Cancel]

Configuration:
- Name input
- Description textarea
- Domain dropdown
- Severity dropdown

Condition Builder:
Visual query builder:
"When [metric] [operator] [value] for [duration]"
- Metric: Daily spend by workspace
- Operator: greater than
- Value: $30,000
- Duration: 5 minutes

Preview:
Live preview of condition with current data

Notification:
- Channels checklist (which channels to notify)
- Message template (customizable)

Schedule:
- Active hours toggle
- Time zone selection
- Days of week checkboxes

Advanced:
- Evaluation interval
- For duration (how long condition must be true)
- No data behavior
- Resolve behavior

---

STATES TO CREATE:

1. Alert Rules Tab (default)
2. Alert Rules Tab (filtered)
3. Alert Rules Tab (bulk selection)
4. Notification Channels Tab
5. Routing Rules Tab
6. Create/Edit Alert Drawer

---

COMPONENTS TO USE:
- Sidebar, TopBar, TabBar
- Table with sorting
- Card (for channels)
- Badge (severity, domain)
- Button, Chip
- Drawer (for edit panel)
- StatusIndicator

Do NOT create new components.
Focus on PagerDuty/Grafana-level quality.
```

---

## 🎯 Expected Output

### Screens Created (1 with 3 tabs)
- Alert Center with Alert Rules, Channels, and Routing tabs

### Figma Structure

```
Screens
└── Alerts
    └── Alert Center
        ├── Alert Rules Tab (default)
        ├── Alert Rules Tab (filtered)
        ├── Alert Rules Tab (selection)
        ├── Notification Channels Tab
        ├── Routing Rules Tab
        └── Create/Edit Drawer
```

---

## ✅ Verification Checklist

- [ ] Header with stats and actions
- [ ] Three-tab navigation
- [ ] Alert rules table with sorting
- [ ] Bulk actions bar
- [ ] Notification channel cards
- [ ] Channel status indicators
- [ ] Routing rules with visual diagram
- [ ] Priority ordering
- [ ] Escalation configuration
- [ ] Create/edit drawer
- [ ] Condition builder UI
- [ ] Schedule configuration
- [ ] Professional ops tooling quality

---

**Next:** [17-screen-settings.md](17-screen-settings.md)

