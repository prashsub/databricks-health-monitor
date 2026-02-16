# Semantic Layer Overview

> **Document Owner:** Analytics Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

The Semantic Layer provides business-friendly interfaces to the Gold layer through Metric Views, TVFs, and Genie Spaces.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 CONSUMPTION LAYER                        │
│   Dashboards  │  Genie Spaces  │  Alerts  │  APIs       │
└─────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────┐
│                  SEMANTIC LAYER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │METRIC VIEWS │  │    TVFs     │  │GENIE SPACES │      │
│  │(KPI Defs)   │  │(Params)     │  │(NL Query)   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────┐
│                    GOLD LAYER                            │
│      Dimension Tables (SCD2)  │  Fact Tables            │
└─────────────────────────────────────────────────────────┘
```

---

## Component Roles

| Component | Purpose | Use When |
|-----------|---------|----------|
| **Metric Views** | Governed KPIs with flexible aggregation | "What is total revenue?" |
| **TVFs** | Parameterized queries with filtering | "Show failed jobs in last 7 days" |
| **Genie Spaces** | Natural language interface | "Why did costs increase?" |

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **SL-01** | Metric Views use v1.1 YAML (no `name` field) | Critical |
| **SL-02** | TVFs use STRING for dates | Critical |
| **SL-03** | Schema validation before SQL | Critical |
| **SL-04** | v3.0 comment format for Genie | Required |
| **SL-05** | No transitive joins in Metric Views | Critical |

---

## When to Use Each

| Question Type | Asset | Why |
|---------------|-------|-----|
| Aggregate KPIs | Metric View | Flexible re-aggregation |
| Filtered results | TVF | Parameter support |
| Complex analysis | TVF | Multi-step logic |
| Business chat | Genie Space | Natural language |

---

## Schema Validation

**Always verify columns against Gold YAML before writing SQL.**

```sql
-- ❌ WRONG: Assumed column
SELECT workspace_owner FROM dim_workspace;  -- Column doesn't exist!

-- ✅ CORRECT: Verified against YAML
SELECT workspace_admin FROM dim_workspace;  -- Actual column name
```

---

## Related Documents

- [Metric View Patterns](30-metric-view-patterns.md)
- [TVF Patterns](31-tvf-patterns.md)
- [Genie Space Patterns](32-genie-space-patterns.md)

---

## References

- [Metric Views](https://docs.databricks.com/metric-views/)
- [TVFs](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-qry-select-tvf)
- [Genie Spaces](https://docs.databricks.com/genie/)
