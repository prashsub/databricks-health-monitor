# Enterprise Data Platform Golden Rules

## Documentation Hub

**Version:** 4.4 | **Last Updated:** February 2026 | **Owner:** Platform Team

This documentation suite provides comprehensive standards, patterns, and governance frameworks for our Databricks-based enterprise data platform, aligned with the [official Azure Databricks Architecture](https://learn.microsoft.com/en-us/azure/databricks/getting-started/architecture) documentation.

---

## Official Microsoft Learn References

The following official documentation has been incorporated into these golden rules:

| Topic | URL | Key Concepts |
|-------|-----|--------------|
| **Architecture Overview** | [Architecture](https://learn.microsoft.com/en-us/azure/databricks/getting-started/architecture) | Control plane, compute plane, lakehouse |
| **High-Level Architecture** | [High-Level Architecture](https://learn.microsoft.com/en-us/azure/databricks/getting-started/high-level-architecture) | Workspace architecture, serverless vs classic |
| **Medallion Architecture** | [Medallion Architecture](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion) | Bronze, Silver, Gold layers |
| **Unity Catalog** | [What is Unity Catalog?](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/) | Centralized governance, lineage, security |
| **ACID Guarantees** | [ACID on Databricks](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/acid) | Transactions, isolation, durability |
| **Single Source of Truth** | [SSOT](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/ssot) | Data unification, Delta Lake |
| **Governance Best Practices** | [Data Governance](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/data-governance/best-practices) | Lineage, quality, security |
| **Managed Tables** | [Unity Catalog Managed Tables](https://learn.microsoft.com/en-us/azure/databricks/tables/managed) | Default table type, AI optimization |
| **Liquid Clustering** | [Use Liquid Clustering](https://learn.microsoft.com/en-us/azure/databricks/delta/clustering) | CLUSTER BY AUTO, automatic optimization |
| **Performance Efficiency** | [Performance](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/performance-efficiency/best-practices) | Serverless, optimization |
| **Cost Optimization** | [Cost](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/cost-optimization/best-practices) | Serverless pricing, efficiency |
| **Reliability** | [Reliability](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/reliability/best-practices) | HA, DR, autoscaling |
| **Well-Architected Framework** | [Service Guide](https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-databricks) | All 5 pillars, security, network |
| **CI/CD Best Practices** | [CI/CD](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/ci-cd/best-practices) | Asset Bundles, testing, MLOps |
| **AI/BI Genie** | [Genie](https://learn.microsoft.com/en-us/azure/databricks/genie/) | Natural language, trusted assets |
| **Data Engineering Best Practices** | [Data Engineering](https://learn.microsoft.com/en-us/azure/databricks/data-engineering/best-practices) | Streaming, observability, optimization |
| **Delta Lake Best Practices** | [Delta Lake](https://docs.databricks.com/en/delta/best-practices.html) | Clustering, MERGE, caching |
| **Unity Catalog Best Practices** | [Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html) | Identities, privileges, storage |
| **Compute Configuration** | [Compute](https://docs.databricks.com/en/compute/cluster-config-best-practices.html) | Serverless, sizing, Photon |
| **Data Modeling** | [Data Modeling](https://learn.microsoft.com/en-us/azure/databricks/transform/data-modeling) | Star schema, joins, normalization |
| **Table Constraints** | [Constraints](https://learn.microsoft.com/en-us/azure/databricks/tables/constraints) | PK, FK, CHECK, NOT NULL |
| **Data Quality Monitoring** | [Data Quality](https://learn.microsoft.com/en-us/azure/databricks/data-quality-monitoring/) | Anomaly detection, profiling, drift |

---

## Documentation Structure

```
enterprise_golden_rules/
│
├── enterprise-architecture/     # 🏢 Governance, Roles, Compliance
│   ├── 01-data-governance.md
│   ├── 02-roles-responsibilities.md
│   ├── 03-implementation-workflow.md
│   ├── 04-data-modeling.md
│   ├── 05-naming-comment-standards.md
│   ├── 06-tagging-standards.md
│   └── 07-data-quality-standards.md
│
├── platform-architecture/       # 🔧 Infrastructure, CI/CD, Standards
│   ├── 10-platform-overview.md
│   ├── 11-serverless-compute.md
│   ├── 12-unity-catalog-tables.md
│   ├── 13-cluster-policies.md
│   ├── 14-secrets-workspace-management.md
│   ├── 15-unity-catalog-governance.md
│   ├── 16-compute-configuration.md
│   ├── 17-delta-lake-best-practices.md
│   ├── 18-reliability-disaster-recovery.md  # NEW - HA, DR, recovery
│   ├── 19-network-security.md               # NEW - VNet, Private Link, CMK
│   ├── 20-asset-bundle-standards.md
│   └── 21-python-development.md
│
├── solution-architecture/       # 🏗️ Implementation Patterns
│   ├── data-pipelines/
│   │   ├── 10-bronze-layer-patterns.md
│   │   ├── 11-silver-layer-patterns.md
│   │   ├── 12-gold-layer-patterns.md
│   │   └── 14-streaming-production-patterns.md
│   ├── semantic-layer/
│   │   ├── 30-metric-view-patterns.md
│   │   ├── 31-tvf-patterns.md
│   │   ├── 32-genie-space-patterns.md
│   │   └── 33-semantic-layer-overview.md
│   ├── dashboards/
│   │   └── 40-aibi-dashboard-patterns.md
│   ├── monitoring/
│   │   └── 41-lakehouse-monitoring.md
│   ├── ml-ai/
│   │   ├── 50-mlflow-model-patterns.md
│   │   ├── 51-genai-agent-patterns.md
│   │   ├── 52-genai-standards.md
│   │   └── 53-ai-gateway-patterns.md
│   └── data-sharing/
│       └── 60-delta-sharing-patterns.md
│
├── onboarding/                  # 🎓 New Hire Quick Start
│   ├── 40-new-hire-week1.md
│   └── 41-new-hire-week2.md
│
├── training/                    # 📚 Structured Training Curriculum
│   ├── 00-training-curriculum-overview.md
│   ├── 01-module-platform-foundations.md
│   ├── 02-module-data-engineering.md
│   ├── 03-module-gold-layer-semantic.md
│   └── 04-module-operations-deployment.md
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
| 🔴 Must Read | [Delta Lake Best Practices](platform-architecture/17-delta-lake-best-practices.md) | Clustering, MERGE, caching |
| 🔴 Must Read | [Streaming Production](solution-architecture/data-pipelines/14-streaming-production-patterns.md) | Triggers, idempotency, scheduler pools |
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
| 🟡 Required | [AI Gateway](solution-architecture/ml-ai/53-ai-gateway-patterns.md) | Payload logging, guardrails |

### Platform Engineers
| Priority | Document | Topic |
|----------|----------|-------|
| 🔴 Must Read | [Platform Overview](platform-architecture/10-platform-overview.md) | Architecture principles |
| 🔴 Must Read | [Serverless Compute](platform-architecture/11-serverless-compute.md) | SQL Warehouses, Jobs, DLT |
| 🔴 Must Read | [Unity Catalog Tables](platform-architecture/12-unity-catalog-tables.md) | Managed tables, properties, volumes |
| 🔴 Must Read | [Naming & Comment Standards](enterprise-architecture/05-naming-comment-standards.md) | Naming conventions, SQL comments |
| 🔴 Must Read | [Tagging Standards](enterprise-architecture/06-tagging-standards.md) | Table properties, compute tags, governed tags |
| 🔴 Must Read | [Asset Bundles](platform-architecture/20-asset-bundle-standards.md) | CI/CD, hierarchical jobs |
| 🔴 Must Read | [UC Governance](platform-architecture/15-unity-catalog-governance.md) | Identities, privileges, ownership |
| 🔴 Must Read | [Network Security](platform-architecture/19-network-security.md) | VNet, Private Link, CMK |
| 🟡 Required | [Reliability & DR](platform-architecture/18-reliability-disaster-recovery.md) | Time travel, checkpointing, HA |
| 🟡 Required | [Compute Configuration](platform-architecture/16-compute-configuration.md) | Serverless, sizing, Photon |
| 🟡 Required | [Cluster Policies](platform-architecture/13-cluster-policies.md) | Compute governance |
| 🟡 Required | [Secrets & Workspaces](platform-architecture/14-secrets-workspace-management.md) | Security, organization |
| 🟡 Required | [Data Governance](enterprise-architecture/01-data-governance.md) | Classification, compliance |
| 🟡 Required | [Data Modeling](enterprise-architecture/04-data-modeling.md) | Star schema, constraints |
| 🟡 Required | [Data Quality Standards](enterprise-architecture/07-data-quality-standards.md) | DLT Expectations, DQX, Lakehouse Monitor |

### New Team Members

**Quick Start (First Week):**
| Day | Document | Focus |
|-----|----------|-------|
| Day 1-2 | [Onboarding Week 1](onboarding/40-new-hire-week1.md) | Concepts, reading, setup |
| Day 3-5 | [Onboarding Week 2](onboarding/41-new-hire-week2.md) | Hands-on labs, full pipeline |

**Structured Training (40 hours):**
| Module | Duration | Document | Topics |
|--------|----------|----------|--------|
| Overview | - | [Curriculum](training/00-training-curriculum-overview.md) | Learning path, prerequisites |
| Module 1 | 8 hrs | [Platform Foundations](training/01-module-platform-foundations.md) | Unity Catalog, governance, architecture |
| Module 2 | 12 hrs | [Data Engineering](training/02-module-data-engineering.md) | Bronze, Silver, DLT, data quality |
| Module 3 | 12 hrs | [Gold & Semantic](training/03-module-gold-layer-semantic.md) | Dimensional modeling, TVFs, Metric Views |
| Module 4 | 8 hrs | [Operations](training/04-module-operations-deployment.md) | Asset Bundles, deployment, monitoring |

---

## Golden Rules Quick Reference

### Critical Rules (🔴 Must Follow)

| ID | Rule | Domain |
|----|------|--------|
| **NC-01** | Use `snake_case` for all object names | Naming |
| **NC-02** | Use layer-appropriate prefixes for tables | Naming |
| **CM-02** | Use COMMENT ON TABLE with business + technical context | Comments |
| **CM-03** | Use COMMENT ON COLUMN with business + technical context | Comments |
| **CM-04** | Use v3.0 structured comments for TVFs | Comments |
| **TG-01** | All tables require standard TBLPROPERTIES | Tagging |
| **TG-02** | All compute resources require custom tags | Tagging |
| **TG-03** | Use Governed Tags for UC object metadata | Tagging |
| **PA-01** | All tables in Unity Catalog | Platform |
| **PA-02** | Delta Lake format required | Platform |
| **PA-04** | Asset Bundles for deployment | Platform |
| **PA-07** | `dbutils.widgets.get()` for notebook params | Platform |
| **DP-02** | CDF enabled on Bronze tables | Data Pipelines |
| **DP-03** | DLT with expectations for Silver | Data Pipelines |
| **DP-05** | Dedup before MERGE in Gold | Data Pipelines |
| **DM-01** | Dimensional modeling (star/snowflake) in Gold | Data Modeling |
| **DM-02** | PRIMARY KEY constraints on all tables | Data Modeling |
| **SL-01** | Metric Views use v1.1 YAML (no name field) | Semantic |
| **SL-02** | STRING type for date parameters in TVFs | Semantic |
| **SL-05** | No transitive joins in Metric Views | Semantic |
| **ML-02** | `output_schema` required for UC models | ML/AI |
| **ML-05** | OBO authentication context detection | ML/AI |
| **ML-06** | Declare Genie Space resources | ML/AI |
| **MO-02** | Dashboard fieldName matches query alias | Monitoring |
| **BP-01** | Use Unity Catalog managed tables | Best Practices |
| **BP-02** | Enable predictive optimization | Best Practices |
| **BP-03** | Use liquid clustering (CLUSTER BY AUTO) | Best Practices |
| **BP-04** | Use serverless compute when supported | Best Practices |
| **BP-05** | Configure streaming with continuous trigger | Best Practices |
| **BP-07** | Never manually modify Delta data files | Best Practices |
| **REL-01** | Delta Lake time travel ≥7 days retention | Reliability |
| **REL-03** | Streaming checkpoints on ZRS/GRS storage | Reliability |
| **SEC-01** | Production workspaces use VNet injection | Security |
| **SEC-02** | Azure Private Link for control plane access | Security |
| **SEC-07** | Secure cluster connectivity (no public IPs) | Security |

### Required Rules (🟡 Should Follow)

| ID | Rule | Domain |
|----|------|--------|
| **NC-03** | Use approved abbreviations only | Naming |
| **CM-01** | Use SQL block comments for DDL headers | Comments |
| **EA-01** | All tables must have documentation | Governance |
| **EA-02** | PII columns tagged | Governance |
| **PA-05** | Hierarchical job architecture | Platform |
| **PA-08** | Pure Python files for imports | Platform |
| **DP-04** | Gold tables from YAML schema | Data Pipelines |
| **DP-06** | PK/FK constraints in Gold | Data Pipelines |
| **SL-03** | Schema validation before writing SQL | Semantic |
| **DM-03** | FOREIGN KEY constraints for relationships | Data Modeling |
| **DM-04** | Avoid heavy normalization (3NF) in Gold | Data Modeling |
| **SL-04** | v3.0 comment format for TVFs | Semantic |
| **MO-01** | `input_columns=[":table"]` for KPIs | Monitoring |
| **MO-03** | SQL returns raw numbers (widgets format) | Monitoring |
| **ML-03** | NaN/Inf handling at feature table creation | ML/AI |
| **ML-07** | Evaluation thresholds before production | ML/AI |
| **BP-06** | Do not use Spark caching with Delta Lake | Best Practices |
| **BP-08** | Use service principals for production jobs | Best Practices |
| **BP-09** | Assign ownership to groups, not individuals | Best Practices |
| **BP-10** | Remove legacy Delta configurations on upgrade | Best Practices |
| **REL-02** | Configure job retry with exponential backoff | Reliability |
| **REL-04** | Enable cluster autoscaling for variable workloads | Reliability |
| **REL-05** | Configure auto-termination on all clusters | Reliability |
| **REL-08** | Test disaster recovery procedures quarterly | Reliability |
| **SEC-03** | Implement IP access lists | Security |
| **SEC-04** | Customer-managed keys (CMK) for encryption | Security |
| **SEC-05** | Enable diagnostic logging to Azure Monitor | Security |
| **SEC-06** | Configure network egress controls | Security |

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
| [Quick Reference Cards](appendix/quick-reference-cards.md) | 13 one-page cheat sheets |

---

## Document Statistics

| Metric | Count |
|--------|-------|
| Total Documents | 44 |
| Architecture Domains | 3 |
| Enterprise Architecture Docs | 7 |
| Platform Architecture Docs | 12 |
| Solution Architecture Docs | 13 |
| Training Modules | 5 |
| Golden Rules | 110+ |
| Templates | 5 |
| Total Training Hours | 40 |

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
| 4.6 | Feb 2026 | **Data Quality Standards**: Created `07-data-quality-standards.md` covering DLT Expectations (pipeline validation), DQX Library (classic Spark jobs), and Lakehouse Monitoring (time-series trends, drift detection). Added 4 new golden rules (DQ-01 to DQ-04). Updated tagging standards to focus on UC governed tags, workflow tags, and serverless budget policies. |
| 4.5 | Feb 2026 | **Naming, Comments & Tagging Standards**: Created `05-naming-comment-standards.md` (naming conventions, SQL block comments, COMMENT patterns, TVF v3.0 format) and `06-tagging-standards.md` (workflow tags, UC governed tags, serverless budget policies). Added 10 new golden rules (NC-01 to NC-03, CM-01 to CM-04, TG-01 to TG-03). |
| 4.4 | Feb 2026 | **Reorganized for Confluence**: Moved platform-level concerns (`15-unity-catalog-governance.md`, `16-compute-configuration.md`, `17-delta-lake-best-practices.md`) from solution-architecture to platform-architecture. Rewrote all 40 documents to Confluence-friendly format with simplified headers, golden rules summary tables, concise sections, and validation checklists. Added `53-ai-gateway-patterns.md` and `60-delta-sharing-patterns.md`. Removed empty governance/ and compute/ folders from solution-architecture. |
| 4.3 | Feb 2026 | **Added Reliability, Security & CI/CD best practices**: Created `18-reliability-disaster-recovery.md` (HA, DR, time travel, checkpointing), `19-network-security.md` (VNet, Private Link, CMK, IP access lists). Enhanced `20-asset-bundle-standards.md` with CI/CD workflows, branching strategy, and MLOps patterns. Added 15 new golden rules (REL-01 to REL-08, SEC-01 to SEC-07). Based on Microsoft Learn Well-Architected Framework, CI/CD best practices, and notebook engineering documentation. |
| 4.2 | Feb 2026 | **Reorganized best practices into categories**: Split comprehensive best practices into 4 focused documents for better discoverability: `13-delta-lake-best-practices.md` (data-pipelines), `14-streaming-production-patterns.md` (data-pipelines), `20-unity-catalog-governance.md` (new governance folder), `21-compute-configuration.md` (new compute folder). Added 6 additional governance rules (GOV-01 to GOV-05, CMP-01 to CMP-04). |
| 4.1 | Feb 2026 | **New document**: Added comprehensive best practices from official Databricks documentation covering Delta Lake, Structured Streaming production, Unity Catalog governance, and compute configuration. 10 new golden rules (BP-01 through BP-10). |
| 4.0 | Feb 2026 | **Major enhancement** - Integrated official Microsoft Learn documentation (10+ pages) covering: High-level architecture (control plane vs compute plane), Medallion architecture best practices, Unity Catalog governance, ACID guarantees, Single Source of Truth, Performance/Cost/Reliability best practices. Updated 8 core documents. |
| 3.0 | Jan 2026 | Reorganized into 3-tier architecture |
| 2.1 | Jan 2026 | Added Enterprise/Platform/Solution structure |
| 2.0 | Jan 2026 | Major expansion with 50+ rules |
| 1.0 | Jan 2026 | Initial golden rules documentation |
