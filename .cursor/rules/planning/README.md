# Planning Cursor Rules

## Overview

This directory contains cursor rules for project planning and framework design documentation for Databricks data platform solutions.

---

## Rules Index

| Rule | File | Description | Lines |
|---|---|---|---|
| **26** | [project-plan-methodology.mdc](26-project-plan-methodology.mdc) | Comprehensive methodology for creating multi-phase project plans | ~800 |
| **27** | [framework-design-methodology.mdc](27-framework-design-methodology.mdc) | Methodology for transforming plans into detailed framework designs | ~1,850 |

---

## Rule Summaries

### Rule 26: Project Plan Methodology

**Purpose:** Standardizes how to create comprehensive, multi-phase project plans for Databricks solutions.

**Key Patterns:**
- 5-phase structure (Prerequisites → Use Cases → Agents → Frontend)
- Agent Domain Framework (Cost, Security, Performance, Reliability, Quality)
- 7 Phase 3 addendums pattern (ML, TVFs, Metrics, Monitoring, Dashboards, Genie, Alerting)
- Artifact count standards (minimum per domain)
- Enrichment methodology (official docs, dashboard JSON, user requirements)
- SQL query standards (Gold layer references, tag patterns)

**When to Use:**
- Planning new Databricks data platform projects
- Building observability/monitoring solutions
- Planning multi-artifact solutions (100+ artifacts)
- Developing agent-based frameworks
- Creating frontend applications

**Output:**
- `plans/README.md` - Project overview
- `plans/phase3-use-cases.md` - Master analytics plan
- `plans/phase3-addendum-3.X-*.md` - Domain-specific plans (7 addendums)
- `plans/phase4-agent-framework.md` - Agent architecture
- `plans/phase5-frontend-app.md` - UI design

---

### Rule 27: Framework Design Methodology ✨ NEW!

**Purpose:** Transforms project plans into comprehensive framework design documentation (3,000-10,000 lines per framework).

**Key Patterns:**
- Standard directory layout (`docs/<framework>-design/`)
- 6 document templates (Index, Introduction, Architecture, Core Chapters, Implementation, Deployment)
- Document naming conventions (00-index, 01-introduction, 02-architecture, etc.)
- Quality standards (completeness checklists, length guidelines, code example standards)
- 10-phase generation workflow (Planning → Structure → Index → Architecture → Chapters → Implementation → Deployment → Appendices → Introduction → Review)
- Framework-specific adaptations (Agent, Alerting, Dashboard, ML, Semantic, Monitoring, Frontend)

**When to Use:**
- Converting Phase 3 addendums into implementation documentation
- Creating agent framework architecture from Phase 4 plans
- Documenting frontend architecture from Phase 5 plans
- Building training/implementation guides
- Establishing reusable patterns

**Output:**
- `docs/<framework>-design/00-index.md` - Navigation hub
- `docs/<framework>-design/01-introduction.md` - Purpose, scope, prerequisites
- `docs/<framework>-design/02-architecture-overview.md` - System architecture
- `docs/<framework>-design/03-XX.md` - Core concept chapters (3-10)
- `docs/<framework>-design/XX-implementation-guide.md` - Step-by-step implementation
- `docs/<framework>-design/YY-deployment-operations.md` - Production operations
- `docs/<framework>-design/appendices/` - Code examples, references, troubleshooting

**Quality Standards:**
- **Total Length:** 3,000-10,000 lines per framework
- **Code Examples:** Complete, tested, with inline comments
- **Diagrams:** ASCII art or Mermaid, clear and labeled
- **Cross-References:** Every document links to 3+ others
- **Best Practices:** Mapped to cursor rules

---

## Related Resources

### Context Prompts

| Prompt | File | Description |
|---|---|---|
| **Framework Design Generation** | [context/prompts/planning/framework-design-generation.md](../../../context/prompts/planning/framework-design-generation.md) | Practical guidance for generating framework designs |

### Example Outputs

**Project Plans:**
- [plans/README.md](../../../plans/README.md) - Databricks Health Monitor project plans
- [plans/phase3-use-cases.md](../../../plans/phase3-use-cases.md) - Analytics artifacts master plan
- [plans/phase3-addendum-3.1-ml-models.md](../../../plans/phase3-addendum-3.1-ml-models.md) - ML models plan (25 models, 5 domains)
- [plans/phase3-addendum-3.6-genie-spaces.md](../../../plans/phase3-addendum-3.6-genie-spaces.md) - Genie Spaces plan
- [plans/phase4-agent-framework.md](../../../plans/phase4-agent-framework.md) - Agent framework plan

**Framework Designs:**
- [docs/agent-framework-design/](../../../docs/agent-framework-design/) - Agent framework (~10,000 lines)
- [docs/alerting-framework-design/](../../../docs/alerting-framework-design/) - Alerting framework (~8,000 lines)
- [docs/dashboard-framework-design/](../../../docs/dashboard-framework-design/) - Dashboard framework (~5,000 lines)
- [docs/lakehouse-monitoring-design/](../../../docs/lakehouse-monitoring-design/) - Monitoring framework (~6,000 lines)
- [docs/ml-framework-design/](../../../docs/ml-framework-design/) - ML framework (~9,000 lines)
- [docs/semantic-framework/](../../../docs/semantic-framework/) - Semantic framework (~7,000 lines)
- [docs/frontend-framework-design/](../../../docs/frontend-framework-design/) - Frontend framework (~12,000 lines)
- [docs/project-architecture-design/](../../../docs/project-architecture-design/) - Complete architecture (~15,000 lines)

---

## Workflow: Plan to Framework

```
┌──────────────────────────────────────────────────────────────┐
│                    RULE 26: PROJECT PLANNING                  │
│                                                               │
│  Input: Requirements, User Stories, Data Sources              │
│  Output: Multi-phase project plan (5-15 documents)            │
│                                                               │
│  Phase 3 Addendum 3.X (Use Case Plan)                        │
│  ├── ML Models Plan (25 models)                              │
│  ├── TVFs Plan (60 functions)                                │
│  ├── Metric Views Plan (10 views)                            │
│  ├── Monitoring Plan (8 monitors)                            │
│  ├── Dashboards Plan (6 dashboards)                          │
│  ├── Genie Spaces Plan (6 spaces)                            │
│  └── Alerting Plan (29 alerts)                               │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Project Plan Complete
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│               RULE 27: FRAMEWORK DESIGN                       │
│                                                               │
│  Input: Phase 3 Addendum, Phase 4 Plan, or Phase 5 Plan      │
│  Output: Complete framework design (3,000-10,000 lines)      │
│                                                               │
│  Framework Design Documents:                                  │
│  ├── 00-index.md (navigation hub)                            │
│  ├── 01-introduction.md (purpose, scope)                     │
│  ├── 02-architecture-overview.md (system design)             │
│  ├── 03-XX.md (core concept chapters × 3-10)                 │
│  ├── XX-implementation-guide.md (step-by-step)               │
│  ├── YY-deployment-operations.md (production)                │
│  └── appendices/ (code examples, references)                 │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Framework Design Complete
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                   IMPLEMENTATION PHASE                        │
│                                                               │
│  Use framework design as implementation guide                 │
│  ├── Architecture patterns                                    │
│  ├── Code examples                                            │
│  ├── Best practices                                           │
│  ├── Testing strategy                                         │
│  └── Deployment procedures                                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Creating a New Project Plan

1. **Review Rule 26:** [project-plan-methodology.mdc](26-project-plan-methodology.mdc)

2. **Gather Inputs:**
   - User requirements
   - Data sources (system tables)
   - Target domains (Cost, Security, Performance, Reliability, Quality)
   - Official Databricks documentation
   - Reference dashboards

3. **Create Plan Structure:**
   ```bash
   mkdir -p plans
   touch plans/README.md
   touch plans/phase3-use-cases.md
   touch plans/phase3-addendum-3.1-ml-models.md
   # ... create other addendums
   touch plans/phase4-agent-framework.md
   touch plans/phase5-frontend-app.md
   ```

4. **Follow Rule 26 patterns for each document**

5. **Validate:**
   - [ ] Agent Domain tags on all artifacts
   - [ ] Minimum artifact counts per domain
   - [ ] SQL queries reference Gold layer
   - [ ] Cross-references complete
   - [ ] User requirements mapped

---

### Creating Framework Design from Plan

1. **Review Rule 27:** [framework-design-methodology.mdc](27-framework-design-methodology.mdc)

2. **Review Context Prompt:** [context/prompts/planning/framework-design-generation.md](../../../context/prompts/planning/framework-design-generation.md)

3. **Identify Framework Scope:**
   - Major components (5-10)
   - Technical challenges (3-5)
   - Best practices (10-15)
   - Target audience
   - Success criteria

4. **Create Directory Structure:**
   ```bash
   mkdir -p docs/<framework>-design
   mkdir -p docs/<framework>-design/appendices
   mkdir -p docs/<framework>-design/actual-implementation  # optional
   ```

5. **Generate Documents in Order:**
   - Phase 1: Planning (scope document)
   - Phase 2: Structure (document outline)
   - Phase 3: Index (00-index.md)
   - Phase 4: Architecture (02-architecture-overview.md)
   - Phase 5: Core Chapters (03-XX.md)
   - Phase 6: Implementation (XX-implementation-guide.md)
   - Phase 7: Deployment (YY-deployment-operations.md)
   - Phase 8: Appendices
   - Phase 9: Introduction (01-introduction.md)
   - Phase 10: Final Review

6. **Quality Check:**
   - [ ] All required documents created
   - [ ] Total length: 3,000-10,000 lines
   - [ ] All code examples tested
   - [ ] All diagrams clear
   - [ ] All links work
   - [ ] Cross-references complete

---

## Best Practices

### Project Planning (Rule 26)

1. **Agent Domain First:**
   - Tag every artifact with its domain
   - Ensure balanced distribution across domains
   - Use domain-specific Gold tables

2. **Enrichment is Key:**
   - Study official Databricks documentation
   - Extract patterns from dashboard JSON files
   - Map user requirements to artifacts

3. **Comprehensive Coverage:**
   - Meet minimum artifact counts per domain
   - Document all edge cases
   - Plan for frontend integration

4. **Cross-Referencing:**
   - Link addendums to master plan
   - Reference Gold layer design
   - Connect agents to Genie Spaces

### Framework Design (Rule 27)

1. **Start with Index:**
   - Forces clear scope definition
   - Creates navigation early
   - Identifies documentation gaps

2. **Architecture Before Details:**
   - Complete architecture overview before core chapters
   - Define all components first
   - Document data flow clearly

3. **Code Examples Must Work:**
   - Test every example
   - Include complete code
   - Show expected output
   - Add inline comments

4. **Write Introduction Last:**
   - You understand the complete framework
   - Can write accurate scope
   - Can identify all prerequisites

5. **Quality Over Speed:**
   - 3,000-10,000 lines is a LOT of content
   - Take time to make examples clear
   - Polish diagrams
   - Verify all links

---

## Common Mistakes to Avoid

### Rule 26: Project Planning

❌ **DON'T:**
- Skip Agent Domain tags
- Plan features without Gold layer design
- Ignore user requirements
- Create plans without studying official docs
- Forget to plan frontend integration

✅ **DO:**
- Tag every artifact with domain
- Reference Gold tables explicitly
- Map requirements to artifacts
- Study dashboard JSON for patterns
- Plan complete end-to-end solution

### Rule 27: Framework Design

❌ **DON'T:**
- Write incomplete code examples
- Skip architecture overview
- Create diagrams without labels
- Write introduction first
- Forget cross-references

✅ **DO:**
- Test all code examples
- Complete architecture before details
- Label all diagram components
- Write introduction last
- Link documents extensively

---

## References

### Official Documentation

- [Databricks Documentation](https://docs.databricks.com/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/)
- [Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/)

### Related Cursor Rules

- [02-databricks-asset-bundles.mdc](../common/02-databricks-asset-bundles.mdc) - Asset Bundle patterns
- [19-sql-alerting-patterns.mdc](../monitoring/19-sql-alerting-patterns.mdc) - Alerting patterns
- [28-mlflow-genai-patterns.mdc](../ml/28-mlflow-genai-patterns.mdc) - MLflow GenAI patterns
- [14-metric-views-patterns.mdc](../semantic-layer/14-metric-views-patterns.mdc) - Metric Views patterns

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-01-14 | Added Rule 27 (Framework Design Methodology), context prompt, examples |
| 1.0 | 2025-12-XX | Initial Rule 26 (Project Plan Methodology) |
