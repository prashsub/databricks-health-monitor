# 17 - Screen: Settings & Admin (Super Enhanced)

## Overview

Create a comprehensive Settings & Admin interface for platform configuration. This is where administrators manage workspaces, data sources, permissions, team ownership, and system preferences.

---

## 📋 FIGMA MAKE PROMPT

Copy and paste this entire prompt into Figma Make:

```
Create a comprehensive Settings & Admin screen for an enterprise monitoring dashboard.

Context:
- Product: Databricks Health Monitor (platform observability)
- Screen: Admin settings and configuration
- Users: Platform administrators configuring the system
- Mental model: "Configure everything about my Health Monitor"
- Inspiration: Datadog Settings, Grafana Admin, AWS Console Settings
- Platform: Desktop web (1440px primary width)

Quality bar:
- Enterprise-grade admin interface
- Clear navigation between settings
- Professional configuration experience
- Comprehensive but not overwhelming

Objective (this run only):
- Create 1 complete screen with left navigation and content areas
- Use ONLY existing components
- NO new components
- Place in Screens section

Follow Guidelines.md for design system alignment.

---

SCREEN SPECIFICATIONS:

Canvas Size: 1440px x 1600px (scroll)
Background: #FAFAFA

---

LAYOUT STRUCTURE:

Two-column layout:
- Left: Settings Navigation (280px)
- Right: Settings Content (~1096px)

---

LEFT NAVIGATION (280px)

Settings sections with icons:

GENERAL
- Profile & Preferences
- Appearance
- Notifications

PLATFORM
- Workspaces (4 connected)
- Data Sources (2 configured)
- Catalogs & Schemas (18 monitored)

ACCESS CONTROL
- Users & Teams (12 users)
- Roles & Permissions
- API Keys (3 active)

OWNERSHIP
- Team Ownership
- Service Catalog
- Escalation Paths

AI ASSISTANT
- Memory Settings
- Tools & Capabilities
- Response Preferences

INTEGRATIONS
- Slack
- Email
- Ticketing (Jira, ServiceNow)
- Webhooks

SYSTEM
- Audit Logs
- Usage & Billing
- About

---

SECTION 1: WORKSPACES (Default View)

Header:
- Title: "Workspaces"
- Subtitle: "Manage connected Databricks workspaces"
- [+ Connect Workspace]

Connected Workspaces Table:

| Status | Workspace | URL | Region | Environment | Last Sync | Actions |
|--------|-----------|-----|--------|-------------|-----------|---------|
| ✓ Online | Production | prod.cloud.databricks.com | us-west-2 | Production | 2 min ago | Configure/Test/Remove |
| ✓ Online | Staging | staging.cloud.databricks.com | us-west-2 | Staging | 5 min ago | Configure/Test/Remove |
| ✓ Online | Development | dev.cloud.databricks.com | us-east-1 | Development | 10 min ago | Configure/Test/Remove |
| ⚠ Warning | Analytics | analytics.cloud.databricks.com | eu-west-1 | Production | 2 hours ago | Configure/Test/Remove |

Warning detail for Analytics workspace:
"Connection timeout detected. Last successful sync 2 hours ago. [Retry Connection]"

Workspace Configuration Card (expandable):
- Workspace name
- URL
- Authentication method (OAuth/PAT)
- Region
- Environment tag
- Sync frequency
- Monitored catalogs/schemas
- Owner team

---

SECTION 2: USERS & TEAMS

Header:
- Title: "Users & Teams"
- Subtitle: "Manage access and team assignments"
- [+ Invite User] [+ Create Team]

Tab Bar:
[Users (12)] [Teams (4)] [Pending Invites (2)]

Users Table:

| Avatar | Name | Email | Role | Teams | Last Active | Status | Actions |
|--------|------|-------|------|-------|-------------|--------|---------|
| JS | John Smith | john@company.com | Admin | Platform, FinOps | 5 min ago | Active | Edit/Remove |
| MK | Maria Kim | maria@company.com | Editor | Platform | 2 hours ago | Active | Edit/Remove |
| AR | Alex Rivera | alex@company.com | Viewer | Analytics | Yesterday | Active | Edit/Remove |

Teams Table:

| Team | Members | Owned Resources | Role | Actions |
|------|---------|-----------------|------|---------|
| Platform Engineering | 5 | 24 resources | Admin | View/Edit |
| FinOps | 3 | 12 resources | Editor | View/Edit |
| Analytics | 3 | 8 resources | Viewer | View/Edit |
| Security | 1 | 4 resources | Editor | View/Edit |

---

SECTION 3: TEAM OWNERSHIP

Header:
- Title: "Team Ownership"
- Subtitle: "Assign ownership for resources, jobs, and catalogs"
- [+ Add Ownership Rule]

Ownership Rules Table:

| Resource Pattern | Resource Type | Owner Team | Escalation | Actions |
|------------------|---------------|------------|------------|---------|
| prod-* | SQL Warehouse | Platform Engineering | Platform Lead | Edit/Delete |
| analytics.* | Catalog/Schema | Analytics Team | Analytics Lead | Edit/Delete |
| etl-* | Job/Pipeline | Data Engineering | DE Manager | Edit/Delete |
| ml-* | Model Serving | ML Platform | ML Lead | Edit/Delete |

Ownership Coverage Stats:
- Resources with owners: 82% (164/200)
- Unowned resources: 36
- [View Unowned Resources]

---

SECTION 4: AI ASSISTANT SETTINGS

Header:
- Title: "AI Assistant Settings"
- Subtitle: "Configure Health Monitor AI behavior"

Memory Settings:
- Session memory duration: [24 hours ▼]
- Long-term memory enabled: [Toggle ON]
- Memory items limit: [100 ▼]
- [Clear All Memory] [Export Memory]

Tools & Capabilities:
Checkboxes for enabled tools:
- ✓ Cost Analysis (get_daily_cost_summary, get_cost_anomalies)
- ✓ Job Monitoring (get_job_failures, get_job_status)
- ✓ Security Analysis (get_security_findings, get_permission_changes)
- ✓ Performance Analysis (get_query_performance, get_cluster_health)
- ✓ Data Quality (get_freshness_status, get_quality_score)

Action Capabilities:
- ✓ Kill queries (requires approval)
- ✓ Create alerts
- ✓ Send notifications
- ☐ Modify configurations (disabled)
- ☐ Create tickets automatically (disabled)

Response Preferences:
- Verbosity: [Balanced ▼] (Concise / Balanced / Detailed)
- Include charts: [Toggle ON]
- Include recommendations: [Toggle ON]
- Auto-suggest follow-ups: [Toggle ON]

---

SECTION 5: INTEGRATIONS

Header:
- Title: "Integrations"
- Subtitle: "Connect external services"

Integration Cards Grid:

Slack:
- Status: Connected (green)
- Workspace: company.slack.com
- Channels: 3 configured
- [Configure] [Disconnect]

Email:
- Status: Connected (green)
- Provider: SendGrid
- Templates: 5 configured
- [Configure] [Disconnect]

Jira:
- Status: Connected (green)
- Project: PLATFORM
- Issue types: Bug, Task, Incident
- [Configure] [Disconnect]

PagerDuty:
- Status: Connected (green)
- Service: Platform Engineering
- Escalation policy configured
- [Configure] [Disconnect]

Microsoft Teams:
- Status: Not Connected
- [Connect]

ServiceNow:
- Status: Not Connected
- [Connect]

---

SECTION 6: AUDIT LOGS

Header:
- Title: "Audit Logs"
- Subtitle: "Track all administrative actions"
- [Export Logs]

Filter Bar:
- Date range: [Last 7 days ▼]
- User: [All Users ▼]
- Action type: [All Actions ▼]
- Search

Audit Log Table:

| Timestamp | User | Action | Resource | Details | IP Address |
|-----------|------|--------|----------|---------|------------|
| Jan 15, 11:30 AM | John Smith | Updated | Alert Rule | Changed threshold from $25K to $30K | 192.168.1.100 |
| Jan 15, 11:15 AM | System | Executed | Query Kill | Terminated query q-12345 | - |
| Jan 15, 10:42 AM | System | Created | Alert | Cost threshold exceeded | - |
| Jan 15, 09:30 AM | Maria Kim | Created | Team | Created "Security" team | 192.168.1.105 |

---

STATES TO CREATE:

1. Workspaces (default view)
2. Users & Teams
3. Team Ownership
4. AI Assistant Settings
5. Integrations
6. Audit Logs

---

COMPONENTS TO USE:
- Sidebar, TopBar
- Table with sorting
- Card (for integrations)
- Badge (status indicators)
- Button, Toggle, Dropdown
- Chip (for tags)
- Avatar

Do NOT create new components.
Focus on enterprise admin quality.
```

---

## 🎯 Expected Output

### Screen Created (1 with multiple sections)
- Settings & Admin with all configuration sections

### Figma Structure

```
Screens
└── Settings
    └── Settings & Admin
        ├── Workspaces
        ├── Users & Teams
        ├── Team Ownership
        ├── AI Assistant
        ├── Integrations
        └── Audit Logs
```

---

## ✅ Verification Checklist

- [ ] Left navigation with all sections
- [ ] Workspaces management with status
- [ ] Connection warning states
- [ ] Users & Teams tables
- [ ] Team ownership rules
- [ ] Ownership coverage stats
- [ ] AI Assistant configuration
- [ ] Memory settings
- [ ] Tool capabilities toggles
- [ ] Integration cards
- [ ] Connected/disconnected states
- [ ] Audit logs with filtering
- [ ] Professional enterprise admin quality

---

**Previous:** [16-screen-alert-center.md](16-screen-alert-center.md)

