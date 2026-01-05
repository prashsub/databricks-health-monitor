# Planning Rules for Claude Code

This file combines all project planning methodology cursor rules for use by Claude Code.

---

## Project Plan Methodology for Databricks Solutions

### When to Apply

Apply this methodology when:
- Creating architectural plans for Databricks data platform projects
- Building observability/monitoring solutions using system tables
- Planning multi-artifact solutions (TVFs, Metric Views, Dashboards, etc.)
- Developing agent-based frameworks for platform management
- Creating frontend applications for data platform interaction

---

## Plan Structure Framework

### Prerequisites (Not Numbered Phases)

Before planning begins, these must be complete:

| Prerequisite | Description |
|--------------|-------------|
| Bronze Layer | Raw data ingestion from source systems |
| Silver Layer | DLT streaming with data quality |
| Gold Layer | Dimensional model (star schema) |

### Standard Project Phases

```
plans/
├── README.md                              # Index and overview
├── prerequisites.md                       # Bronze/Silver/Gold summary
├── phase1-use-cases.md                    # Analytics artifacts (master)
│   ├── phase1-addendum-1.1-ml-models.md
│   ├── phase1-addendum-1.2-tvfs.md
│   ├── phase1-addendum-1.3-metric-views.md
│   ├── phase1-addendum-1.4-lakehouse-monitoring.md
│   ├── phase1-addendum-1.5-ai-bi-dashboards.md
│   ├── phase1-addendum-1.6-genie-spaces.md
│   └── phase1-addendum-1.7-alerting-framework.md
├── phase2-agent-framework.md              # AI Agents
└── phase3-frontend-app.md                 # User Interface
```

### Phase Dependencies

```
Prerequisites (Bronze → Silver → Gold) → Phase 1 (Use Cases) → Phase 2 (Agents) → Phase 3 (Frontend)
```

---

## Agent Domain Framework

### Core Principle

**ALL artifacts across ALL phases MUST be organized by Agent Domain:**
- Consistent categorization across 100+ artifacts
- Clear ownership by future AI agents
- Easy discoverability for users

### Standard Agent Domains

| Domain | Icon | Focus Area | Key Gold Tables |
|--------|------|------------|-----------------|
| **Cost** | 💰 | FinOps, budgets, chargeback | `fact_usage`, `dim_sku` |
| **Security** | 🔒 | Access audit, compliance | `fact_audit_events` |
| **Performance** | ⚡ | Query optimization, capacity | `fact_query_history` |
| **Reliability** | 🔄 | Job health, SLAs | `fact_job_run_timeline` |
| **Quality** | ✅ | Data quality, governance | `fact_data_quality_*` |

### Agent Domain Application

Every artifact must:
1. Be tagged with its Agent Domain
2. Use the domain's Gold tables
3. Answer domain-specific questions
4. Be grouped with related domain artifacts

**Example:**
```markdown
## 💰 Cost Agent: get_top_cost_contributors

**Agent Domain:** 💰 Cost
**Gold Tables:** `fact_usage`, `dim_workspace`
**Business Questions:** "What are the top cost drivers?"
```

---

## Agent Layer Architecture

### Core Principle

**AI Agents DO NOT query data assets directly.** They use Genie Spaces as their natural language query interface.

```
┌─────────────────────────────────────────────────────────────┐
│                USERS (Natural Language)                      │
│  "Why did costs spike last Tuesday?"                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 2: AI AGENT LAYER                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ORCHESTRATOR AGENT                                   │    │
│  │ • Intent classification → Routes to specialized agents │  │
│  └─────────────────────────────────────────────────────┘    │
│              ▼                ▼                ▼             │
│         Cost Agent    Security Agent    Performance Agent    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Natural Language Queries
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            PHASE 1.6: GENIE SPACES                           │
│  • Translates NL → SQL                                       │
│  • Routes to TVFs, Metric Views, ML                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 1: DATA ASSETS                            │
│  Metric Views | TVFs | ML Predictions | Monitors            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              GOLD LAYER (Foundation)                         │
└─────────────────────────────────────────────────────────────┘
```

### Genie Space → Agent Mapping

| Agent | Genie Space | Tools (via Genie) |
|-------|-------------|-------------------|
| 💰 Cost Agent | Cost Intelligence | 15 TVFs, 2 MVs, 6 ML |
| 🔒 Security Agent | Security Auditor | 10 TVFs, 2 MVs, 4 ML |
| ⚡ Performance Agent | Performance Analyzer | 16 TVFs, 3 MVs, 7 ML |
| 🔄 Reliability Agent | Job Health Monitor | 12 TVFs, 1 MV, 5 ML |
| ✅ Quality Agent | Data Quality Monitor | 7 TVFs, 2 MVs, 3 ML |
| 🤖 Orchestrator | Unified Health Monitor | All tools |

### Why Genie Spaces (Not Direct SQL)?

| Without Genie Spaces | With Genie Spaces |
|---------------------|-------------------|
| Agents must write SQL | Agents use natural language |
| Agents must know schema | Genie understands semantics |
| Hard to maintain | Easy to update instructions |

### Deployment Order (Critical!)

**Genie Spaces MUST be deployed BEFORE agents can use them.**

```
Phase 0: Prerequisites (Complete)
    └── Bronze → Silver → Gold Layer

Phase 1: Data Assets
    ├── 1.1: ML Models
    ├── 1.2: TVFs
    ├── 1.3: Metric Views
    ├── 1.4: Lakehouse Monitors
    ├── 1.5: AI/BI Dashboards
    ├── 1.6: Genie Spaces ← Critical for agents
    └── 1.7: Alerting

Phase 2: Agent Framework (Deploy After Genie Spaces)

Phase 3: Frontend (Deploy Last)
```

---

## Plan Document Template

```markdown
# Phase N: [Phase Name]

## Overview

**Status:** 📋 Planned | 🔧 In Progress | ✅ Complete  
**Dependencies:** [List dependencies]  
**Estimated Effort:** [Duration]  

---

## Purpose

[2-3 sentences explaining why this phase exists]

---

## [Domain-Specific Sections]

### 💰 Cost Agent: [Artifact Name]

[Artifact details organized by agent domain]

---

## Implementation Details

[Code examples, SQL, YAML configurations]

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| [Metric] | [Value] |
```

---

## SQL Query Standards

### Gold Layer Reference Pattern

**ALWAYS use Gold layer tables, NEVER system tables directly:**

```sql
-- ❌ WRONG: Direct system table reference
FROM system.billing.usage

-- ✅ CORRECT: Gold layer reference with variables
FROM ${catalog}.${gold_schema}.fact_usage
```

### Standard Variable References

```sql
-- Catalog and schema
${catalog}.${gold_schema}.table_name

-- Date parameters (STRING for Genie compatibility)
WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)

-- SCD Type 2 dimension joins
LEFT JOIN dim_workspace w 
    ON f.workspace_id = w.workspace_id 
    AND w.is_current = TRUE
```

### Tag Query Patterns

```sql
-- Tag existence check
WHERE custom_tags IS NOT NULL AND cardinality(custom_tags) > 0

-- Tag value extraction
custom_tags['team'] AS team_tag
COALESCE(custom_tags['cost_center'], 'Unassigned') AS cost_center

-- Tag coverage calculation
SUM(CASE WHEN cardinality(custom_tags) > 0 THEN cost ELSE 0 END) / 
    NULLIF(SUM(cost), 0) * 100 AS tag_coverage_pct
```

---

## Artifact Count Standards

### Minimum Artifacts Per Domain

| Artifact Type | Per Domain | Total (5 domains) |
|---------------|------------|-------------------|
| TVFs | 4-8 | 20-40 |
| Metric Views | 1-2 | 5-10 |
| Dashboard Pages | 2-4 | 10-20 |
| Alerts | 4-8 | 20-40 |
| ML Models | 3-5 | 15-25 |
| Lakehouse Monitors | 1-2 | 5-10 |
| Genie Spaces | 1-2 | 5-10 |

### Artifact Naming Conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| TVF | `get_<domain>_<metric>` | `get_cost_by_tag` |
| Metric View | `<domain>_analytics_metrics` | `cost_analytics_metrics` |
| Dashboard | `<Domain> <Purpose> Dashboard` | `Cost Attribution Dashboard` |
| Alert | `<DOMAIN>-NNN` | `COST-001` |
| ML Model | `<Purpose> <Type>` | `Budget Forecaster` |
| Genie Space | `<Domain> <Purpose>` | `Cost Intelligence` |
| AI Agent | `<Domain> Agent` | `Cost Agent` |

---

## Documentation Quality Standards

### LLM-Friendly Comments

All artifacts must have comments that help LLMs understand:

```sql
COMMENT 'LLM: Returns top N cost contributors by workspace and SKU for a date range.
Use this for cost optimization, chargeback analysis, and identifying spending hotspots.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default 10).
Example questions: "What are the top 10 cost drivers?" or "Which workspace spent most?"'
```

### Summary Tables

Every addendum must include:
1. **Overview table** - All artifacts with agent domain, dependencies, status
2. **By-domain sections** - Artifacts grouped by agent domain
3. **Count summary** - Total artifacts by type and domain
4. **Success criteria** - Measurable targets

---

## Enrichment Methodology

### Source Categories (Priority Order)

1. **Official Documentation** - Databricks docs, Microsoft Learn
2. **Reference Dashboards** - Extract SQL from `.lvdash.json` files
3. **Community Resources** - Blog posts, GitHub repos
4. **User Requirements** - Specific use cases provided

### Dashboard Pattern Extraction

1. Read the JSON file to extract datasets, queries, visualizations
2. Categorize patterns by Agent Domain
3. Convert queries to Gold layer references
4. Document with source dashboard name and business question

---

## User Requirement Integration

### Process for Adding Use Cases

1. **Understand the Business Need**
   - What question are they answering?
   - Who is the end user?

2. **Identify Required Artifacts**
   - Configuration tables, TVFs, Metric Views
   - Dashboards, Alerts, ML Models

3. **Update ALL Relevant Addendums**
   - A single use case often spans multiple addendums

4. **Add Cross-References**
   - Link related artifacts
   - Document dependencies

---

## Validation Checklist

### Structure
- [ ] Follows standard template
- [ ] Has Overview with Status, Dependencies, Effort
- [ ] Organized by Agent Domain
- [ ] Includes code examples
- [ ] Has Success Criteria table

### Content Quality
- [ ] All queries use Gold layer tables (not system tables)
- [ ] All artifacts tagged with Agent Domain
- [ ] LLM-friendly comments on all artifacts
- [ ] Uses `${catalog}.${gold_schema}` variables

### Cross-References
- [ ] Main phase document links to addendums
- [ ] Addendums link back to main phase
- [ ] Related artifacts cross-reference each other

### Completeness
- [ ] All 5 agent domains covered
- [ ] Minimum artifact counts met
- [ ] User requirements addressed

---

## Common Mistakes to Avoid

### ❌ DON'T: Mix system tables and Gold tables

```sql
-- BAD: Direct system table
FROM system.billing.usage u
JOIN ${catalog}.${gold_schema}.dim_workspace w ...
```

### ❌ DON'T: Forget Agent Domain classification

```markdown
## get_slow_queries (BAD - no domain)

## ⚡ Performance Agent: get_slow_queries (GOOD)
```

### ❌ DON'T: Create artifacts without cross-addendum updates

When adding a TVF, also consider:
- Does it need a Metric View counterpart?
- Should there be an Alert?
- Is it Dashboard-worthy?

### ❌ DON'T: Use DATE parameters in TVFs (Genie incompatible)

```sql
-- BAD
start_date DATE

-- GOOD
start_date STRING COMMENT 'Format: YYYY-MM-DD'
```

---

## Agent Integration Testing

### Three-Level Testing Strategy

| Level | What to Test | When |
|-------|--------------|------|
| L1: Genie Standalone | Genie returns correct results | After Genie deployment |
| L2: Agent Integration | Agent uses Genie and formats response | After agent deployment |
| L3: Multi-Agent | Orchestrator coordinates agents | After all agents deployed |



