# 01 - Introduction

## Purpose

The **Databricks Health Monitor** addresses a critical gap in platform observability: **unified, AI-powered monitoring across cost, security, performance, reliability, data quality, and MLOps domains**. Built as a comprehensive solution from Bronze layer ingestion through intelligent agent interfaces, the system transforms raw Databricks system tables into actionable insights through a sophisticated semantic layer optimized for both human and AI consumption.

### The Problem

Organizations running Databricks at scale face:
- **Cost Explosion**: DBU costs grow unpredictably without clear attribution
- **Silent Failures**: Jobs fail without proactive alerts or root cause analysis
- **Security Blind Spots**: Audit logs overwhelming, anomalies missed
- **Manual Investigation**: Hours spent querying system tables for answers
- **Fragmented Tools**: Separate dashboards for cost, jobs, security create context switching
- **Reactive Operations**: Issues discovered after impact, not before

### The Solution

A **unified observability platform** that:
1. **Ingests** all Databricks system tables across 7 domains
2. **Validates** data quality through DLT expectations
3. **Transforms** raw data into 41 analytics-ready Gold tables
4. **Enriches** with semantic metadata (50+ TVFs, 30+ Metric Views)
5. **Predicts** issues via 15 ML models for anomaly detection/forecasting
6. **Monitors** data quality with Lakehouse Monitoring (280+ custom metrics)
7. **Alerts** proactively via 56 config-driven SQL alerts
8. **Visualizes** through 12 AI/BI dashboards and 6 Genie Spaces
9. **Converses** via AI agents (Phase 4) for natural language investigation
10. **Presents** through a modern web app (Phase 5) with real-time updates

### Value Proposition

| Stakeholder | Value Delivered |
|-------------|-----------------|
| **Platform Teams** | Proactive incident prevention, faster root cause analysis (2 hours → 5 minutes) |
| **FinOps Teams** | Clear cost attribution, 30-day forecasting, anomaly detection saves 15-20% monthly spend |
| **Security Teams** | Real-time threat detection, ML-powered anomaly alerts reduce investigation time 70% |
| **Data Engineers** | Self-service analytics via Genie, TVFs eliminate 50+ manual queries per week |
| **Executives** | Executive dashboard with KPIs, trend visibility, data-driven decision making |

---

## Scope

### In Scope

**Phase 1: Bronze Layer** ✅ Completed
- Ingest from 7 system table domains (Billing, LakeFlow, Governance, Compute, Serverless, Access, Monitoring)
- Daily scheduled jobs with serverless compute
- CDF-enabled for incremental Silver propagation
- ~30 Bronze tables

**Phase 2: Gold Layer** ✅ Completed
- 41 analytics-ready tables (12 facts, 24 dimensions, 5 summaries)
- YAML-driven schema management for maintainability
- PRIMARY KEY / FOREIGN KEY constraints for relational integrity
- Predictive optimization and liquid clustering
- SCD Type 2 dimensions for historical tracking

**Phase 3: Use Cases** ✅ Completed

**3.1 ML Models (15 models)**
- Cost: Anomaly detection, forecasting, DBU prediction, budget alerting, commitment recommendations
- Performance: Job failure prediction, duration forecasting, bottleneck detection, resource optimization, query optimization
- Security: Access anomaly detection, breach risk scoring, user behavior analysis, threat scoring, compliance prediction

**3.2 Table-Valued Functions (50+ TVFs)**
- Cost domain: 10 TVFs (daily summaries, anomalies, top drivers, trends)
- Security domain: 8 TVFs (events, failed auth, permission changes, compliance)
- Performance domain: 12 TVFs (failed jobs, slow queries, bottlenecks, SLA tracking)
- Reliability domain: 10 TVFs (uptime, incidents, pipeline health)
- Quality domain: 6 TVFs (DQ summaries, freshness violations, expectation failures)
- MLOps domain: 4 TVFs (model performance, drift metrics, training history)

**3.3 Metric Views (30+ views)**
- YAML-defined semantic metadata for Genie natural language queries
- Pre-defined dimensions and measures by domain
- LLM-friendly descriptions with synonyms
- Snowflake schema joins for complex relationships

**3.4 Lakehouse Monitoring (12 monitors)**
- Custom metrics: 150+ business KPIs, 80+ technical metrics, 50+ drift metrics
- Output tables documented for Genie integration
- Automated quality tracking on all Gold tables

**3.5 AI/BI Dashboards (12 dashboards)**
- 200+ visualizations across 6 domains
- Query patterns reference Gold layer only (never system tables directly)
- Real-time refresh via serverless SQL
- Workspace-level permissions

**3.6 Genie Spaces (6 spaces)**
- Domain-specific natural language interfaces
- Comprehensive agent instructions (500-1000 lines each)
- 30-50 benchmark questions per space
- Asset tagging by agent domain

**3.7 SQL Alerting Framework (56 alerts)**
- Config-driven YAML alert definitions
- ML-powered dynamic thresholds
- Multi-channel delivery (Email, Slack, PagerDuty)
- Alert catalog organized by domain

**Phase 4: Agent Framework** 📋 Planned
- Master Orchestrator Agent for multi-domain queries
- 7 Specialized Agents (Cost, Security, Performance, Reliability, Quality, MLOps, Governance)
- Tool integration with semantic layer (TVFs, Metric Views, ML models)
- Multi-agent coordination and response synthesis
- Model serving endpoints (serverless)

**Phase 5: Frontend App** 📋 Planned
- Next.js 14+ with Vercel AI SDK
- 6 specialized pages (Dashboard Hub, Chat, Cost Center, Job Operations, Security Center, Settings)
- Real-time data updates (< 30s refresh)
- Lakebase PostgreSQL for chat history and user preferences
- Databricks Apps deployment with SSO
- Mobile-responsive dark-themed design

### Out of Scope

**Explicitly NOT Included:**
- **Multi-workspace monitoring** (single workspace only in v1.0)
- **Custom data sources** (only Databricks system tables)
- **Advanced ML features** (deep learning, NLP beyond embeddings, reinforcement learning)
- **Real-time streaming** (batch-oriented with daily/hourly refresh)
- **Multi-cloud** (Databricks-specific, not AWS/Azure/GCP native)
- **Third-party integrations** (beyond email/Slack alerts)
- **Mobile native apps** (mobile-responsive web only)
- **On-premise deployment** (cloud-only via Databricks Apps)

---

## Prerequisites

### Completed Components

| Component | Count | Status | Documentation |
|-----------|-------|--------|---------------|
| **Bronze Tables** | 30 | ✅ Required | [Phase 1 Plan](../../plans/phase1-bronze-ingestion.md) |
| **Gold Tables** | 41 | ✅ Required | [Phase 2 Plan](../../plans/phase2-gold-layer-design.md) |
| **Table-Valued Functions** | 50+ | ✅ Required | [Semantic Framework Docs](../semantic-framework/) |
| **Metric Views** | 30+ | ✅ Required | [Semantic Framework Docs](../semantic-framework/) |
| **ML Models** | 15 | ✅ Required | [ML Framework Design](../ml-framework-design/) |
| **Lakehouse Monitors** | 12 | ✅ Required | [Lakehouse Monitoring Design](../lakehouse-monitoring-design/) |
| **SQL Alerts** | 56 | ✅ Required | [Alerting Framework Design](../alerting-framework-design/) |
| **AI/BI Dashboards** | 12 | ✅ Required | [Dashboard Framework Design](../dashboard-framework-design/) |
| **Genie Spaces** | 6 | ✅ Required | [Semantic Framework Docs](../semantic-framework/) |
| **Agent Framework** | 0 | 📋 Optional | [Agent Framework Design](../agent-framework-design/) |
| **Frontend App** | 0 | 📋 Optional | [Frontend PRD](09-frontend-prd.md) |

### Infrastructure Requirements

| Requirement | Specification |
|-------------|---------------|
| **Databricks Workspace** | AWS/Azure/GCP with Unity Catalog enabled |
| **Runtime Version** | Databricks Runtime 15.4+ LTS |
| **Serverless Compute** | SQL Warehouse (Medium or Large), Serverless Jobs, Serverless DLT |
| **Unity Catalog** | Catalog with 3 schemas (bronze, silver, gold) |
| **Model Serving** | Serverless model endpoints enabled |
| **Databricks Apps** | Enabled for Frontend deployment (Phase 5) |
| **System Tables** | Access to `system.billing.*`, `system.lakeflow.*`, `system.access.*`, etc. |
| **Storage** | 1TB+ for Gold layer (scales with usage) |

### Required Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| **CREATE CATALOG** | Account/Workspace | Create Unity Catalog |
| **CREATE SCHEMA** | Catalog | Create bronze/silver/gold schemas |
| **CREATE TABLE** | Schema | Create managed tables |
| **SELECT** | `system.*` | Read system tables |
| **CREATE FUNCTION** | Schema | Deploy TVFs |
| **CREATE MODEL** | Schema | Register ML models |
| **CREATE SERVING ENDPOINT** | Workspace | Deploy model serving |
| **CREATE JOB** | Workspace | Deploy orchestration jobs |
| **CREATE PIPELINE** | Workspace | Deploy DLT pipelines |
| **CREATE DASHBOARD** | Workspace | Deploy AI/BI dashboards |
| **CREATE ALERT** | Workspace | Deploy SQL alerts |
| **CREATE GENIE SPACE** | Workspace | Deploy Genie Spaces |
| **CREATE APP** | Workspace | Deploy Databricks Apps (Phase 5) |

---

## Best Practices Matrix

| # | Best Practice | Implementation | Document |
|---|---------------|----------------|----------|
| 1 | **Medallion Architecture** | Bronze → Silver → Gold with DLT expectations | [02-Current Architecture](02-current-architecture.md) |
| 2 | **Semantic Layer First** | All consumption via TVFs/Metric Views, not direct Gold access | [05-Semantic Layer](05-semantic-layer.md) |
| 3 | **AI-Native Design** | LLM-friendly metadata on all assets (comments, tags, synonyms) | [05-Semantic Layer](05-semantic-layer.md) |
| 4 | **Unity Catalog Governance** | Constraints, lineage, tags on all tables | [11-Security Architecture](11-security-architecture.md) |
| 5 | **Serverless First** | All compute uses serverless (SQL, Jobs, DLT, Serving) | [10-Deployment Architecture](10-deployment-architecture.md) |
| 6 | **Config-Driven Everything** | Databricks Asset Bundles (DABs) for infrastructure as code | [10-Deployment Architecture](10-deployment-architecture.md) |
| 7 | **ML-Powered Insights** | 15 models for anomaly detection, forecasting, prediction | [06-ML Architecture](06-ml-architecture.md) |
| 8 | **Observability by Default** | Lakehouse Monitoring on all Gold tables with custom metrics | [07-Monitoring Architecture](07-monitoring-architecture.md) |
| 9 | **Domain-Driven Design** | 7 domains organize data and agents consistently | [04-Data Architecture](04-data-architecture.md) |
| 10 | **Hierarchical Jobs** | 3-layer job architecture (Atomic → Composite → Orchestrator) | [10-Deployment Architecture](10-deployment-architecture.md) |
| 11 | **YAML-Driven Schemas** | Gold tables created from YAML definitions, not hardcoded DDL | [04-Data Architecture](04-data-architecture.md) |
| 12 | **Pre-Creation Validation** | Schema validation before deployment prevents 100% of schema errors | [05-Semantic Layer](05-semantic-layer.md) |
| 13 | **Agent Domain Framework** | All artifacts tagged by agent domain (Cost, Security, etc.) | [08-Agent Architecture](08-agent-architecture.md) |
| 14 | **Dual-Purpose Comments** | Comments serve both humans and LLMs with structured format | [05-Semantic Layer](05-semantic-layer.md) |
| 15 | **Proactive Alerting** | ML-powered alerts fire before SLA breach, not after | [07-Monitoring Architecture](07-monitoring-architecture.md) |

---

## Development Timeline

### Completed Phases

| Phase | Duration | Deliverables | Status |
|-------|----------|--------------|--------|
| **Phase 1: Bronze Layer** | 2 weeks | 30 Bronze tables, daily ingestion jobs | ✅ Complete |
| **Phase 2: Gold Layer** | 4 weeks | 41 Gold tables with constraints, YAML schemas | ✅ Complete |
| **Phase 3.1: ML Models** | 3 weeks | 15 models trained and served | ✅ Complete |
| **Phase 3.2: TVFs** | 2 weeks | 50+ Table-Valued Functions | ✅ Complete |
| **Phase 3.3: Metric Views** | 2 weeks | 30+ Metric Views with YAML | ✅ Complete |
| **Phase 3.4: Lakehouse Monitoring** | 2 weeks | 12 monitors with 280+ custom metrics | ✅ Complete |
| **Phase 3.5: Dashboards** | 3 weeks | 12 AI/BI dashboards (200+ visualizations) | ✅ Complete |
| **Phase 3.6: Genie Spaces** | 2 weeks | 6 domain-specific spaces | ✅ Complete |
| **Phase 3.7: Alerting** | 2 weeks | 56 SQL alerts deployed | ✅ Complete |
| **Total (Completed)** | **22 weeks** | **Phases 1-3 (60% of project)** | ✅ Complete |

### Planned Phases

| Phase | Duration | Deliverables | Status |
|-------|----------|--------------|--------|
| **Phase 4: Agent Framework** | 6 weeks | Master Orchestrator + 7 agents, tool integration | 📋 Planned |
| **Phase 5: Frontend App** | 8 weeks | Next.js app with 6 pages, chat interface, Lakebase integration | 📋 Planned |
| **Total (Remaining)** | **14 weeks** | **Phases 4-5 (40% of project)** | 📋 Planned |

### Overall Timeline

**Total Project Duration:** 36 weeks (9 months)  
**Completed:** 22 weeks (61%)  
**Remaining:** 14 weeks (39%)

---

## Success Criteria

### Technical Success Metrics

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Data Freshness** | < 24 hours lag | Time from system table update to Gold table availability |
| **Query Performance** | < 3s for 95% of queries | P95 query latency on Gold tables |
| **Model Accuracy** | > 85% precision/recall | ML model performance on hold-out set |
| **Alert Precision** | < 10% false positive rate | False alerts / total alerts |
| **Dashboard Load Time** | < 2s | Time to interactive for dashboards |
| **Agent Response Time** | < 5s | End-to-end chat response time |
| **API Uptime** | > 99.5% | Frontend API availability |
| **Cost Efficiency** | < $2K/month DBU | Total platform DBU cost |

### Business Success Metrics

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **MTTR Reduction** | 70% reduction | Time to resolve incidents (before vs after) |
| **Cost Savings** | 15-20% reduction | Monthly DBU spend reduction from optimization recommendations |
| **Investigation Time** | 90% reduction | Time to diagnose issues (2 hours → 10 minutes) |
| **Proactive Prevention** | 50%+ of issues | Issues caught by alerts before user impact |
| **User Adoption** | 100+ daily active users | Unique users per day after 3 months |
| **Self-Service Queries** | 80% reduction in manual queries | Data team queries eliminated by Genie/TVFs |

### User Satisfaction Metrics

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Net Promoter Score** | > 50 | User survey (0-10 recommendation score) |
| **System Usability Scale** | > 80 | SUS questionnaire score |
| **Agent Helpfulness** | > 4.5/5 | User rating after each agent conversation |
| **Dashboard Usefulness** | > 4/5 | User feedback on dashboard value |

---

## Document Conventions

### Code Examples

All code examples in this documentation are:
- **Production-ready**: No placeholders, fully functional
- **Parameterized**: Use `${catalog}`, `${schema}` for portability
- **Commented**: Explain non-obvious logic
- **Tested**: Validated in dev/prod environments

**Format:**
````python
# Databricks notebook source
# Purpose: Brief description

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp

def main():
    """Main entry point with error handling."""
    spark = SparkSession.builder.getOrCreate()
    
    try:
        # Implementation
        pass
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
````

### Diagrams

**ASCII Art for Architecture:**
- Used for high-level system views
- Easy to version control and diff
- No external dependencies

**Mermaid for Sequences/Flows:**
- Used for data flows and interactions
- Renders in GitHub/Markdown viewers
- Exported to PNG for presentations

### Configuration

**YAML Configuration Files:**
- Stored in `resources/` directory
- Follow DABs patterns
- Include comments for non-obvious settings

**Environment Variables:**
- Always use `${var.variable_name}` in DABs
- Never hardcode values
- Document all required variables

---

## Next Steps

### For Platform Engineers

1. **Read [02-Current Architecture](02-current-architecture.md)** to understand deployed infrastructure
2. **Review [10-Deployment Architecture](10-deployment-architecture.md)** for deployment patterns
3. **Study [07-Monitoring Architecture](07-monitoring-architecture.md)** for operations runbooks

### For ML Engineers

1. **Start with [06-ML Architecture](06-ml-architecture.md)** for model catalog and patterns
2. **Review [04-Data Architecture](04-data-architecture.md)** for feature engineering sources
3. **Understand [05-Semantic Layer](05-semantic-layer.md)** for model consumption patterns

### For Data Engineers

1. **Begin with [04-Data Architecture](04-data-architecture.md)** for data model understanding
2. **Explore [05-Semantic Layer](05-semantic-layer.md)** for TVF and Metric View patterns
3. **Reference [02-Current Architecture](02-current-architecture.md)** for Bronze/Silver/Gold layers

### For Designers/Developers (Frontend)

1. **Start with [09-Frontend PRD](09-frontend-prd.md)** - complete Figma specifications
2. **Review [03-Future Architecture](03-future-architecture.md)** for frontend integration points
3. **Understand [12-Integration Architecture](12-integration-architecture.md)** for API contracts

### For Project Managers

1. **Read [13-Implementation Roadmap](13-implementation-roadmap.md)** for timeline and milestones
2. **Review [01-Introduction](01-introduction.md)** (this document) for scope and success criteria
3. **Track progress via [00-Index](00-index.md)** document index

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Next Review:** March 2026 (or when Phase 4 begins)

