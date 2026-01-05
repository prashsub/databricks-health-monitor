# Databricks Health Monitor - Frontend Design Documentation

## Overview

Complete design documentation for the **Databricks Health Monitor** - an enterprise-grade observability platform that rivals Datadog, Grafana, New Relic, and Sentry, enhanced with a unified AI assistant.

> **Core Principle:**
> Users interact with **ONE intelligent AI assistant** that knows everything about their platform, remembers their preferences, proactively surfaces issues, and takes action on their behalf.

---

## 📖 How to Use This Documentation

### Two Paths Based on Your Role

| Path | You Are | Start Here | Purpose |
|------|---------|------------|---------|
| **A. Design Path** | Designer using Figma | [figma/00-getting-started.md](figma/00-getting-started.md) | Step-by-step prompts to create the UI |
| **B. Reference Path** | PM, Engineer, Stakeholder | [prd/README.md](prd/README.md) | Detailed specifications |

---

## 🎯 Quick Start: Design Path (Recommended)

**Follow this sequence to design the complete application:**

```
SETUP & DESIGN SYSTEM (Day 1):
Step 1:  Context Setup          → figma/01-context-setup.md
Step 2:  Colors                 → figma/02-design-system-colors.md
Step 3:  Typography             → figma/03-design-system-typography.md
Step 4:  Spacing                → figma/04-design-system-spacing.md

SCREEN DESIGNS (Weeks 1-5):
Step 5:  Executive Overview     → figma/05-executive-overview.md  
Step 6:  Global Explorer        → figma/06-global-explorer.md
Step 7:  Domain Pages (5)       → figma/07-domain-pages.md
Step 8:  Signal Detail          → figma/08-signal-detail.md
Step 9:  Chat Interface         → figma/09-chat-interface.md
Step 10: Alert Center           → figma/10-alert-center.md
Step 11: Settings               → figma/11-settings-admin.md

REFERENCE MATERIALS:
Step 12: Visualizations         → figma/12-visualizations.md
Step 13: Components             → figma/13-component-library.md
```

**Estimated time:** 6 weeks (1-2 screens per week)

---

## 📁 Folder Structure

```
frontend-framework-design/
│
├── 00-index.md                    ← YOU ARE HERE
│
├── figma/                         # 🎨 DESIGN PROMPTS (Start Here)
│   │
│   │   # SETUP & DESIGN SYSTEM (Do First)
│   ├── 00-getting-started.md      # Prerequisites & workflow
│   ├── 01-context-setup.md        # AI context + all tokens
│   ├── 02-design-system-colors.md # Color palette (50+ colors)
│   ├── 03-design-system-typography.md # Type scale (15 styles)
│   ├── 04-design-system-spacing.md    # Spacing system
│   │
│   │   # SCREEN DESIGNS
│   ├── 05-executive-overview.md   # Home screen
│   ├── 06-global-explorer.md      # Single pane of glass
│   ├── 07-domain-pages.md         # 5 domain pages
│   ├── 08-signal-detail.md        # Drilldown page
│   ├── 09-chat-interface.md       # AI assistant chat
│   ├── 10-alert-center.md         # Alert management
│   ├── 11-settings-admin.md       # Settings & admin
│   │
│   │   # REFERENCE MATERIALS
│   ├── 12-visualizations.md       # Chart patterns
│   └── 13-component-library.md    # All components
│
├── prd/                           # 📋 REFERENCE SPECIFICATIONS
│   ├── README.md                  # PRD navigation
│   ├── 01-base-prd.md             # Foundation (150 pages)
│   ├── 02-ml-enhancements.md      # ML layer (140 pages)
│   ├── 03-agentic-ai-first.md     # Agent layer (180 pages)
│   └── 04-closed-loop-architecture.md # Autonomy (100 pages)
│
├── design-system/                 # 🎨 DESIGN TOKENS (Legacy)
│   └── README.md                  # Points to figma/02-04 for actual tokens
│
└── summaries/                     # 📊 EXECUTIVE SUMMARIES
    └── *.md                       # For stakeholder communication
```

---

## 🖥️ Screens to Design (10 Total)

| # | Screen | Description | Figma Guide | PRD Reference |
|---|--------|-------------|-------------|---------------|
| 1 | **Executive Overview** | KPI tiles, alerts, trends | [05-executive-overview](figma/05-executive-overview.md) | 01-base-prd §5.1 |
| 2 | **Global Explorer** | Single pane of glass | [06-global-explorer](figma/06-global-explorer.md) | 01-base-prd §5.2 |
| 3 | **Cost Domain** | Cost analytics | [07-domain-pages](figma/07-domain-pages.md) | 01-base-prd §5.3 |
| 4 | **Reliability Domain** | Job health | [07-domain-pages](figma/07-domain-pages.md) | 01-base-prd §5.4 |
| 5 | **Performance Domain** | System performance | [07-domain-pages](figma/07-domain-pages.md) | 02-ml §3 |
| 6 | **Security Domain** | Governance & security | [07-domain-pages](figma/07-domain-pages.md) | 01-base-prd §5.5 |
| 7 | **Quality Domain** | Data quality | [07-domain-pages](figma/07-domain-pages.md) | 02-ml §4 |
| 8 | **Signal Detail** | Drilldown view | [08-signal-detail](figma/08-signal-detail.md) | 03-agentic §6 |
| 9 | **Chat Interface** | AI conversation | [09-chat-interface](figma/09-chat-interface.md) | 03-agentic §5 |
| 10 | **Alert Center** | Alert management | [10-alert-center](figma/10-alert-center.md) | 04-closed §4 |

---

## 🤖 Unified AI Assistant

The key differentiator of this application:

| Feature | Implementation |
|---------|----------------|
| **ONE Identity** | "Health Monitor AI" - single name, icon (🤖), color (#3B82F6) |
| **All Domains** | Answers cost, security, performance, reliability, quality questions |
| **Memory** | Remembers preferences, past issues, favorite workspaces |
| **Proactive** | Surfaces issues before users ask |
| **Actions** | Executes fixes with one click |

**Users never see "Cost Agent" or "Security Agent" - just the unified assistant.**

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| **PRD Pages** | 570 |
| **UI Components** | 110 |
| **Application Screens** | 10 |
| **ML Models** | 25 |
| **Custom Metrics** | 155+ |
| **Alert Rules** | 56 |

---

## ✅ Design Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Setup design context
- [ ] Executive Overview
- [ ] Global Explorer
- [ ] Design system tokens

### Phase 2: Domain Pages (Week 3-4)
- [ ] Cost Domain
- [ ] Reliability Domain
- [ ] Performance Domain
- [ ] Security Domain
- [ ] Quality Domain

### Phase 3: Advanced Screens (Week 5)
- [ ] Signal Detail (drilldown)
- [ ] Chat Interface
- [ ] Alert Center

### Phase 4: Completion (Week 6)
- [ ] Settings & Admin
- [ ] Visualizations reference
- [ ] Component states
- [ ] Handoff documentation

---

## 🔗 Related Documentation

| Framework | Path | Description |
|-----------|------|-------------|
| **Agent Framework** | [../agent-framework-design/](../agent-framework-design/) | Agent implementation |
| **ML Framework** | [../ml-framework-design/](../ml-framework-design/) | ML models |
| **Dashboard Framework** | [../dashboard-framework-design/](../dashboard-framework-design/) | AI/BI dashboards |
| **Alerting Framework** | [../alerting-framework-design/](../alerting-framework-design/) | SQL Alerts V2 |

---

## 🚀 Next Steps

1. **Start designing:** [figma/00-getting-started.md](figma/00-getting-started.md)
2. **Review PRDs:** [prd/README.md](prd/README.md)
3. **Share with stakeholders:** [summaries/](summaries/)

---

**Version:** 5.0  
**Last Updated:** January 2026  
**Status:** ✅ Ready for Figma Design

