# Prompts - Table of Contents

## Overview

This directory contains **production-ready prompts** for building Databricks Medallion Architecture implementations. Prompts are organized by domain/layer to mirror the cursor rules structure.

---

## 📁 Directory Structure

```
context/prompts/
├── 00_TABLE_OF_CONTENTS.md          # This file
├── README.md                         # Framework documentation
│
├── bronze/                           # Bronze layer prompts
│   └── 01-bronze-layer-prompt.md     # Raw data ingestion
│
├── silver/                           # Silver layer prompts
│   ├── 02-silver-layer-prompt.md     # DLT with data quality
│   └── SILVER_LAYER_CREATION_PROMPT.md # Legacy prompt
│
├── gold/                             # Gold layer prompts
│   ├── 03a-gold-layer-design-prompt.md        # ERD & YAML design
│   ├── 03b-gold-layer-implementation-prompt.md # DDL & MERGE scripts
│   └── gold-layer-dimensional-model-design.md  # Dimensional modeling guide
│
├── semantic-layer/                   # Semantic layer prompts
│   ├── 04-metric-views-prompt.md     # Metric views for Genie
│   ├── 06-genie-space-prompt.md      # Genie Space setup
│   ├── 09-table-valued-functions-prompt.md    # TVFs for Genie
│   ├── finops-tvf-business-questions.md       # FinOps TVF questions
│   ├── finops-tvf-sql-examples.sql            # FinOps TVF SQL examples
│   ├── FINOPS_TVF_IMPLEMENTATION_SUMMARY.md   # FinOps TVF summary
│   └── FINOPS_TVF_QUICK_REFERENCE.md          # FinOps TVF quick ref
│
├── monitoring/                       # Observability prompts
│   ├── 05-monitoring-prompt.md       # Lakehouse Monitoring
│   ├── 10-aibi-dashboards-prompt.md  # AI/BI Lakeview dashboards
│   └── 14-sql-alerts-prompt.md       # SQL Alerts V2
│
├── ml/                               # Machine learning prompts
│   └── 12-ml-models-prompt.md        # MLflow + Feature Store
│
├── exploration/                      # Data exploration prompts
│   ├── 07-dqx-integration-prompt.md  # DQX framework integration
│   └── 08-exploration-notebook-prompt.md # Ad-hoc exploration
│
├── planning/                         # Project planning prompts
│   ├── 11-project-plan-prompt.md     # 5-phase project planning
│   ├── 13-agent-architecture-design-prompt.md # Agent design
│   └── 15-documentation-framework-prompt.md   # Documentation generation
│
├── design/                           # UI/UX Design prompts (NEW)
│   ├── README.md                     # Design prompts index
│   ├── 16-capability-audit-prompt.md         # Audit capabilities before design
│   └── 17-figma-interface-design-prompt.md   # Complete Figma guide generation
│
├── frontend/                         # UI/Frontend prompts (legacy)
│   └── figma_frontend_design_prompt.md # Figma design prompt
│
├── reference/                        # Reference materials (empty)
│
└── archive/                          # Deprecated/legacy files
    ├── gold_layer_design.md          # Empty file
    └── system_design.md              # Legacy system design
```

---

## 🎯 Quick Reference

### Core Medallion Architecture (Required)
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| 01 | bronze-layer-prompt.md | `bronze/` | Raw data ingestion | 2-3 hrs |
| 02 | silver-layer-prompt.md | `silver/` | DLT + data quality | 2-4 hrs |
| 03a | gold-layer-design-prompt.md | `gold/` | ERD + YAML schemas | 2-3 hrs |
| 03b | gold-layer-implementation-prompt.md | `gold/` | DDL + MERGE scripts | 3-4 hrs |

### Semantic Layer & BI (Recommended)
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| 04 | metric-views-prompt.md | `semantic-layer/` | Metric views for Genie | 2 hrs |
| 06 | genie-space-prompt.md | `semantic-layer/` | Natural language queries | 1-2 hrs |
| 09 | table-valued-functions-prompt.md | `semantic-layer/` | TVFs for Genie | 2-3 hrs |

### Observability & Alerts
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| 05 | monitoring-prompt.md | `monitoring/` | Lakehouse Monitoring | 2 hrs |
| 10 | aibi-dashboards-prompt.md | `monitoring/` | Lakeview dashboards | 2-4 hrs |
| 14 | sql-alerts-prompt.md | `monitoring/` | SQL Alerts V2 | 1-2 hrs |

### Machine Learning
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| 12 | ml-models-prompt.md | `ml/` | Feature Engineering + MLflow + UC | 10-16 hrs |

### Data Quality & Exploration
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| 07 | dqx-integration-prompt.md | `exploration/` | DQX framework | 3-4 hrs |
| 08 | exploration-notebook-prompt.md | `exploration/` | Ad-hoc analysis | 1 hr |

### Project Planning & Documentation
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| 11 | project-plan-prompt.md | `planning/` | 5-phase planning | 2-4 hrs |
| 13 | agent-architecture-design-prompt.md | `planning/` | Agent design | 2-3 hrs |
| 15 | documentation-framework-prompt.md | `planning/` | Documentation generation | 1-2 hrs |

### UI/UX Design (NEW)
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| 16 | capability-audit-prompt.md | `design/` | Audit capabilities before design | 30 min |
| 17 | figma-interface-design-prompt.md | `design/` | Complete Figma guide generation | 1-2 hrs |

### Frontend (Legacy)
| # | Prompt | Directory | Purpose | Time |
|---|--------|-----------|---------|------|
| - | figma_frontend_design_prompt.md | `frontend/` | Figma UI design (legacy) | 4-8 hrs |

---

## 🔗 Related Resources

- **Cursor Rules:** [../../.cursor/rules/](../../.cursor/rules/) - AI assistant patterns
- **Gold Layer YAML:** [../../gold_layer_design/yaml/](../../gold_layer_design/yaml/) - Schema definitions
- **Plans:** [../../plans/](../../plans/) - Project implementation plans
- **Docs:** [../../docs/](../../docs/) - Reference documentation

---

## 📝 Naming Conventions

Following cursor rules patterns:
- Use numbered prefixes for ordering: `01-`, `02-`, etc.
- Use kebab-case: `bronze-layer-prompt.md`
- Keep prompts in appropriate subdirectory by domain
- Archive deprecated files in `archive/`

