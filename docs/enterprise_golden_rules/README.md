# Enterprise Data Platform Golden Rules

## Documentation Hub

**Version:** 3.0 | **Last Updated:** January 2026 | **Owner:** Platform Team

This documentation suite provides comprehensive standards, patterns, and governance frameworks for our Databricks-based enterprise data platform.

---

## Documentation Structure

```
enterprise_golden_rules/
│
├── enterprise-architecture/     # 🏢 Governance, Roles, Compliance
│   ├── 01-data-governance.md
│   ├── 02-roles-responsibilities.md
│   └── 03-implementation-workflow.md
│
├── platform-architecture/       # 🔧 Infrastructure, CI/CD, Standards
│   ├── 10-platform-overview.md
│   ├── 11-serverless-compute.md
│   ├── 12-unity-catalog-tables.md
│   ├── 13-cluster-policies.md
│   ├── 14-secrets-workspace-management.md
│   ├── 20-asset-bundle-standards.md
│   └── 21-python-development.md
│
├── solution-architecture/       # 🏗️ Implementation Patterns
│   ├── data-pipelines/
│   │   ├── 10-bronze-layer-patterns.md
│   │   ├── 11-silver-layer-patterns.md
│   │   └── 12-gold-layer-patterns.md
│   ├── semantic-layer/
│   │   ├── 30-metric-view-patterns.md
│   │   ├── 31-tvf-patterns.md
│   │   ├── 32-genie-space-patterns.md
│   │   └── 33-semantic-layer-overview.md
│   ├── monitoring/
│   │   └── 41-lakehouse-monitoring.md
│   ├── dashboards/
│   │   └── 40-aibi-dashboard-patterns.md
│   └── ml-ai/
│       ├── 50-mlflow-model-patterns.md
│       ├── 51-genai-agent-patterns.md
│       └── 52-genai-standards.md
│
├── onboarding/                  # 🎓 New Hire Training
│   ├── 40-new-hire-week1.md
│   └── 41-new-hire-week2.md
│
├── templates/                   # 📝 Reusable Templates
│   ├── architecture-review-checklist.md
│   ├── deployment-checklist.md
│   ├── exception-request-form.md
│   ├── compliance-report-template.md
│   └── verification-checklist.md
│
└── appendix/                    # 📖 Reference Materials
    ├── glossary.md
    └── quick-reference-cards.md
```

---

## Quick Navigation by Role

### Data Engineers
| Priority | Document | Topic |
|----------|----------|-------|
| 🔴 Must Read | [Bronze Layer](solution-architecture/data-pipelines/10-bronze-layer-patterns.md) | CDF, Faker, ingestion |
| 🔴 Must Read | [Silver Layer](solution-architecture/data-pipelines/11-silver-layer-patterns.md) | DLT, expectations, DQX |
| 🔴 Must Read | [Gold Layer](solution-architecture/data-pipelines/12-gold-layer-patterns.md) | YAML schemas, MERGE, SCD2 |
| 🟡 Required | [Asset Bundles](platform-architecture/20-asset-bundle-standards.md) | CI/CD, job configuration |
| 🟡 Required | [Python Standards](platform-architecture/21-python-development.md) | Parameters, imports |

### Analytics Engineers
| Priority | Document | Topic |
|----------|----------|-------|
| 🔴 Must Read | [Metric Views](solution-architecture/semantic-layer/30-metric-view-patterns.md) | v1.1 YAML, no transitive joins |
| 🔴 Must Read | [TVF Patterns](solution-architecture/semantic-layer/31-tvf-patterns.md) | STRING dates, v3.0 comments |
| 🔴 Must Read | [Genie Spaces](solution-architecture/semantic-layer/32-genie-space-patterns.md) | Asset inventory, optimization |
| 🟡 Required | [Dashboards](solution-architecture/dashboards/40-aibi-dashboard-patterns.md) | fieldName, formatting |
| 🟡 Required | [Monitoring](solution-architecture/monitoring/41-lakehouse-monitoring.md) | Custom metrics |

### ML Engineers
| Priority | Document | Topic |
|----------|----------|-------|
| 🔴 Must Read | [MLflow Models](solution-architecture/ml-ai/50-mlflow-model-patterns.md) | Feature tables, inference |
| 🔴 Must Read | [GenAI Agents](solution-architecture/ml-ai/51-genai-agent-patterns.md) | ResponsesAgent, OBO auth |
| 🟡 Required | [GenAI Standards](solution-architecture/ml-ai/52-genai-standards.md) | Evaluation, memory |

### Platform Engineers
| Priority | Document | Topic |
|----------|----------|-------|
| 🔴 Must Read | [Platform Overview](platform-architecture/10-platform-overview.md) | Architecture principles |
| 🔴 Must Read | [Serverless Compute](platform-architecture/11-serverless-compute.md) | SQL Warehouses, Jobs, DLT |
| 🔴 Must Read | [Unity Catalog Tables](platform-architecture/12-unity-catalog-tables.md) | Managed tables, properties, volumes |
| 🔴 Must Read | [Asset Bundles](platform-architecture/20-asset-bundle-standards.md) | CI/CD, hierarchical jobs |
| 🟡 Required | [Cluster Policies](platform-architecture/13-cluster-policies.md) | Compute governance |
| 🟡 Required | [Secrets & Workspaces](platform-architecture/14-secrets-workspace-management.md) | Security, organization |
| 🟡 Required | [Data Governance](enterprise-architecture/01-data-governance.md) | Classification, compliance |

### New Team Members
| Week | Document | Focus |
|------|----------|-------|
| Week 1 | [Onboarding Week 1](onboarding/40-new-hire-week1.md) | Concepts, reading, setup |
| Week 2 | [Onboarding Week 2](onboarding/41-new-hire-week2.md) | Hands-on labs, full pipeline |

---

## Golden Rules Quick Reference

### Critical Rules (🔴 Must Follow)

| ID | Rule | Domain |
|----|------|--------|
| **PA-01** | All tables in Unity Catalog | Platform |
| **PA-02** | Delta Lake format required | Platform |
| **PA-04** | Asset Bundles for deployment | Platform |
| **PA-07** | `dbutils.widgets.get()` for notebook params | Platform |
| **DP-02** | CDF enabled on Bronze tables | Data Pipelines |
| **DP-03** | DLT with expectations for Silver | Data Pipelines |
| **DP-05** | Dedup before MERGE in Gold | Data Pipelines |
| **SL-01** | Metric Views use v1.1 YAML (no name field) | Semantic |
| **SL-02** | STRING type for date parameters in TVFs | Semantic |
| **SL-05** | No transitive joins in Metric Views | Semantic |
| **ML-02** | `output_schema` required for UC models | ML/AI |
| **ML-05** | OBO authentication context detection | ML/AI |
| **ML-06** | Declare Genie Space resources | ML/AI |
| **MO-02** | Dashboard fieldName matches query alias | Monitoring |

### Required Rules (🟡 Should Follow)

| ID | Rule | Domain |
|----|------|--------|
| **EA-01** | All tables must have documentation | Governance |
| **EA-02** | PII columns tagged | Governance |
| **PA-05** | Hierarchical job architecture | Platform |
| **PA-08** | Pure Python files for imports | Platform |
| **DP-04** | Gold tables from YAML schema | Data Pipelines |
| **DP-06** | PK/FK constraints in Gold | Data Pipelines |
| **SL-03** | Schema validation before writing SQL | Semantic |
| **SL-04** | v3.0 comment format for TVFs | Semantic |
| **MO-01** | `input_columns=[":table"]` for KPIs | Monitoring |
| **MO-03** | SQL returns raw numbers (widgets format) | Monitoring |
| **ML-03** | NaN/Inf handling at feature table creation | ML/AI |
| **ML-07** | Evaluation thresholds before production | ML/AI |

---

## Templates

| Template | Purpose | When to Use |
|----------|---------|-------------|
| [Architecture Review](templates/architecture-review-checklist.md) | Pre-implementation review | Before starting new project |
| [Deployment Checklist](templates/deployment-checklist.md) | Pre-deployment validation | Before every deployment |
| [Verification Checklist](templates/verification-checklist.md) | Golden rules compliance | Pre-deployment & audits |
| [Exception Request](templates/exception-request-form.md) | Rule exception approval | When deviating from standards |
| [Compliance Report](templates/compliance-report-template.md) | Periodic compliance review | Monthly/Quarterly audits |

---

## Reference Materials

| Document | Content |
|----------|---------|
| [Glossary](appendix/glossary.md) | 50+ terms, acronyms, rule IDs |
| [Quick Reference Cards](appendix/quick-reference-cards.md) | 10 one-page cheat sheets |

---

## Document Statistics

| Metric | Count |
|--------|-------|
| Total Documents | 32 |
| Architecture Domains | 3 |
| Platform Architecture Docs | 7 |
| Solution Architecture Docs | 12 |
| Golden Rules | 60+ |
| Templates | 5 |
| Onboarding Days | 10 |

---

## Contributing

1. Follow naming convention: `XX-kebab-case-name.md`
2. Include Document Information header
3. Add to appropriate architecture domain
4. Update this README navigation
5. Submit PR for review

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | Jan 2026 | Reorganized into 3-tier architecture |
| 2.1 | Jan 2026 | Added Enterprise/Platform/Solution structure |
| 2.0 | Jan 2026 | Major expansion with 50+ rules |
| 1.0 | Jan 2026 | Initial golden rules documentation |
